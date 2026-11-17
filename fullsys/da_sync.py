"""
Data-aided (DA) CFO / phase / noise synchroniser for the full-system competitors (DVB-RCS2 TC-LM bursts, rcs2.py;
VDE-SAT Link 32, vde.py), timing known. The strongest reasonable DA receiver for |f| <= CFO_MAX = 0.03 cycles per
symbol and a uniform phase; reuses est3 / est4 code (newton, _parab, _top_in, nfft_for, crb_known) by import.

Model at the known burst positions n_k (absolute burst index, known unit-modulus symbols s_k):
    z_k = r[n_k] conj(s_k) = g e^{j 2 pi f n_k} + w_k,   g complex (amplitude + phase), w_k ~ CN(0, N0)
ML (g, N0 unknown): f_hat = argmax Lambda(f), Lambda(f) = |sum_k z_k e^{-j 2 pi f n_k}|^2   (the masked periodogram)
    1  z placed at n_k - n_0 on the burst span (zeros at the data), |FFT| of size nfft_for(span) (power of 2 >= 4 x span:
       the FFT covers the whole [-1/2, 1/2), no FFT aliasing; the layout's own lobes / aliases stay as candidates)
    2  local maxima inside |nu| <= CFO_MAX + MARGIN / span (+ 1 bin); the REFINE highest are refined: parabolic
       interpolation on |X| (est4 _parab), then NEWTON Newton steps on the exact Lambda (est3.newton, centred t)
    3  candidates ranked by the exact Lambda, duplicates (|f_i - f_j| < DEDUP / span) dropped, the best n_cand kept
    4  per candidate: g_hat = sum_k z_k e^{-j 2 pi f n_k} / Nk (ML gain: |g| and phase arg g at n = 0),
       N0_hat = sum_k |z_k - g_hat e^{j 2 pi f n_k}|^2 / (Nk - 1.5) (residual, 3 real parameters fitted of 2 Nk)
    5  y_n = r_n e^{-j 2 pi f n} / g_hat (unit gain), LLR noise N0_eff = N0_hat / |g_hat|^2 (or genie N0 / |g_hat|^2)
Optional (DD_ITERS > 0, off: not specified for either system): decision-directed refinement, hard decisions on the
data symbols + the known symbols, DD_ITERS Newton steps on Lambda over the whole burst, g_hat re-fitted on all.
CRB (unknown phase and amplitude): 1 / (2 SNR (2 pi)^2 sum_k (n_k - mean n)^2) (est4.common.crb_known).
Ops in fullsys/costmodel.py units (da_ops / da_crit: FFT 5 n log2 n, phasor recursion, 32-core critical path) via
cost(): 'lean' (1 maximum refined, nfft >= 2 span) = the competitor cost reported, 'upper' (this module's REFINE
maxima, nfft >= 4 span) = the upper bracket.
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from est3 import estimators as E3            # noqa: E402  newton, FFT_MACS
from est4 import estimators as E4            # noqa: E402  _parab, _top_in, nfft_for
from est4 import common as C4                # noqa: E402  crb_known
from fullsys import costmodel                # noqa: E402  da_ops / da_crit

CFO_MAX = 0.03                               # |f| range (cycles / symbol)
MARGIN = 2.0                                 # search beyond CFO_MAX by MARGIN / span (the main lobe of an edge CFO)
REFINE = 6                                   # local maxima refined (parabolic + Newton) before the ranking
NEWTON = 3                                   # Newton steps on the exact Lambda per refined maximum
DEDUP = 0.5                                  # refined maxima closer than DEDUP / span are one candidate
TOP_M = 3                                    # 'strong' receiver: candidates decoded in metric order until the CRC
DD_ITERS = 0                                 # decision-directed Newton steps on the whole burst (0 = off, the default)
KP = 32                                      # cores of the MACs-per-core model (est4.estimators.KP)


class Layout:
    """Known-symbol layout: positions pos (Nk,) in the burst, symbols ks (Nk,), FFT size, search mask."""

    def __init__(self, pos, ks, L, cfo_max=CFO_MAX, margin=MARGIN, nfft=None, name=""):
        self.pos = np.asarray(pos, np.int64)
        self.ks = np.asarray(ks, complex)
        self.L, self.name, self.Nk = int(L), name, len(self.pos)
        self.n0 = int(self.pos.min())
        self.span = int(self.pos.max()) - self.n0 + 1
        self.nfft = nfft or E4.nfft_for(self.span)
        self.fwin = cfo_max + margin / self.span                         # searched |f|
        self.mask = np.abs(np.fft.fftfreq(self.nfft)) <= self.fwin + 1.0 / self.nfft
        self.n_win = int(self.mask.sum())
        self.t = self.pos.astype(float)

    def crb(self, snr_db):
        """CRB of f (cycles / symbol)^2 at Es/N0 snr_db per known symbol."""
        return C4.crb_known(snr_db, self.pos)

    def outlier_thr(self):
        """|f_err| above which a packet counts as an outlier: 1 / (2 L)."""
        return 0.5 / self.L


def _gain(z, f, t):
    """ML complex gain and Lambda at f (B,): A = sum_k z_k e^{-j 2 pi f t_k} (absolute t), g = A / Nk."""
    A = np.einsum("bk,bk->b", z, np.exp(-2j * np.pi * f[:, None] * t[None]))
    return A / z.shape[1], np.abs(A) ** 2


def _n0(z, f, g, t):
    """Residual noise variance on the known symbols, Nk - 1.5 complex degrees of freedom."""
    res = z - g[:, None] * np.exp(2j * np.pi * f[:, None] * t[None])
    return np.sum(np.abs(res) ** 2, 1) / (z.shape[1] - 1.5)


def estimate(r, lay, n_cand=1, refine=REFINE, iters=NEWTON, dedup=DEDUP):
    """
    r (B, L) symbol-rate samples (MF output, despread for CDMA) -> dict of (B, n_cand) arrays ranked by Lambda:
    f, lam, g (complex gain at n = 0), n0 (noise variance in r units), valid; and peak_bins (B,) local maxima found.
    """
    B = len(r)
    z = r[:, lay.pos] * np.conj(lay.ks)[None]
    x = np.zeros((B, lay.span), complex)
    x[:, lay.pos - lay.n0] = z
    X = np.abs(np.fft.fft(x, lay.nfft, axis=1))
    nref = max(refine, n_cand)
    top = E4._top_in(X, lay.mask[None], nref)                          # (B, nref) bins, descending |X|
    rows = np.arange(B)[:, None]
    loc = (X >= np.roll(X, 1, 1)) & (X >= np.roll(X, -1, 1)) & lay.mask[None]
    ok = loc[rows, top]                                                # fewer maxima than nref: the rest invalid
    f0 = np.fft.fftfreq(lay.nfft)[top] + E4._parab(X, top) / lay.nfft
    zz = z[:, :, None]
    f = np.stack([E3.newton(zz, f0[:, i], iters, t=lay.t) for i in range(nref)], 1)
    lam = np.stack([_gain(z, f[:, i], lay.t)[1] for i in range(nref)], 1)
    lam = np.where(ok, lam, -np.inf)
    order = np.argsort(-lam, 1, kind="stable")
    f, lam = np.take_along_axis(f, order, 1), np.take_along_axis(lam, order, 1)
    keep = np.isfinite(lam)
    for i in range(1, nref):                                           # drop a maximum that refined onto a better one
        near = (np.abs(f[:, :i] - f[:, i:i + 1]) < dedup / lay.span) & keep[:, :i]
        keep[:, i] &= ~near.any(1)
    order = np.argsort(~keep, 1, kind="stable")[:, :n_cand]            # kept ones first, metric order preserved
    f, lam, valid = (np.take_along_axis(a, order, 1) for a in (f, lam, keep))
    g = np.zeros((B, n_cand), complex)
    n0 = np.full((B, n_cand), np.nan)
    for i in range(n_cand):
        g[:, i], _ = _gain(z, f[:, i], lay.t)
        n0[:, i] = _n0(z, f[:, i], g[:, i], lay.t)
    return dict(f=f, lam=lam, g=g, n0=n0, valid=valid, peaks=loc.sum(1))


def correct(r, f, g):
    """y_n = r_n e^{-j 2 pi f n} / g over the whole burst (f, g (B,)): unit gain, zero CFO / phase."""
    n = np.arange(r.shape[1])
    return r * np.exp(-2j * np.pi * f[:, None] * n[None]) / g[:, None]


def dd_refine(r, f, g, decide, lay, iters=DD_ITERS):
    """Decision-directed refinement (option, off by default): symbols d = known at lay.pos, decide(y) elsewhere,
    iters Newton steps on Lambda over the whole burst from f, then g re-fitted on all symbols. Returns (f, g)."""
    if iters <= 0:
        return f, g
    y = correct(r, f, g)
    d = decide(y)                                                      # (B, L) unit-modulus decisions
    d[:, lay.pos] = lay.ks[None]
    z = r * np.conj(d)
    t = np.arange(r.shape[1], dtype=float)
    f = E3.newton(z[:, :, None], f, iters, t=t)
    g, _ = _gain(z, f, t)
    return f, g


def phase_err(f_hat, g_hat, f, g_true, n_c):
    """Phase error (rad, wrapped) of the estimated vs the true gain trajectory at the known-symbol centre n_c."""
    return np.angle(g_hat * np.exp(2j * np.pi * f_hat * n_c) * np.conj(g_true * np.exp(2j * np.pi * f * n_c)))


# ---- ops (fullsys/costmodel.py units) ----------------------------------------------------------------------------
def cost(lay, n_data, kind="lean", refine=REFINE, newton=NEWTON):
    """costmodel.da_ops / da_crit of the synchroniser on layout lay. kind 'lean' = the competitor cost (1 maximum
    refined, nfft = power of 2 >= 2 span; a further candidate costs refine_one + per_cand); 'upper' = what this
    module runs (refine maxima, nfft = lay.nfft >= 4 span): the upper bracket. Returns dict(ops, crit, nfft, n_win,
    refine) with ops / crit = dict(first, per_cand, refine_one, breakdown)."""
    if kind == "lean":
        nfft, refine = costmodel.pow2_at_least(2 * lay.span), 1
    else:
        nfft = lay.nfft
    n_win = int(np.sum(np.abs(np.fft.fftfreq(nfft)) <= lay.fwin + 1.0 / nfft))
    a = (lay.Nk, n_data, nfft, n_win, refine, newton)
    return dict(ops=costmodel.da_ops(*a), crit=costmodel.da_crit(*a), nfft=nfft, n_win=n_win, refine=refine)


def attempt_cost(c, m, key="ops"):
    """Extra synchroniser cost of decode attempt m (0-based) beyond the first: per_cand, + refine_one when the
    candidate was not among the refined maxima (m >= refine)."""
    if m == 0:
        return 0.0
    d = c[key]
    return d["per_cand"] + (d["refine_one"] if m >= c["refine"] else 0.0)


# ---- hooks for rcs2.synchronise / vde.VDELink.rx (not wired in: see the run_fullsys_da.py docstring) -------------
def rcs2_layout(wf, cfo_max=CFO_MAX):
    return Layout(wf.known_idx, wf.known_sym, wf.L, cfo_max=cfo_max, name=f"rcs2-{wf.key}")


def vde_layout(link, cfo_max=CFO_MAX):
    """Known symbols of a VDE burst after despreading: syncwords (bit b -> 2 b - 1) and pilots (+1), BPSK."""
    pos = np.concatenate([link.sync_pos, link.pilot_pos])
    sym = np.concatenate([2.0 * link.swbit[link.sync_pos] - 1, np.ones(len(link.pilot_pos))]).astype(complex)
    o = np.argsort(pos)
    return Layout(pos[o], sym[o], link.n_sym, cfo_max=cfo_max, name=f"vde-{link.lid}")


def rcs2_hook(r, wf, n0=None, genie_n0=False, **kw):
    """rcs2.synchronise(sync='da'): rank-1 DA estimate -> (y unit gain, N0 (B, 1, 1) for rcs2.demap)."""
    lay = rcs2_layout(wf)
    e = estimate(r, lay)
    f, g = e["f"][:, 0], e["g"][:, 0]
    n = (n0 if genie_n0 else e["n0"][:, 0]) / np.abs(g) ** 2
    return correct(r, f, g), np.broadcast_to(n, (len(r),))[:, None, None]


def vde_hook(link, r, N0_el=None, genie_n0=False):
    """VDELink.rx(sync='da'): despread, rank-1 DA estimate -> (y unit gain (B, n_sym), N0 per symbol (B, 1))."""
    y = link.despread(r)
    lay = vde_layout(link)
    e = estimate(y, lay)
    f, g = e["f"][:, 0], e["g"][:, 0]
    n = (N0_el / link.sf if genie_n0 else e["n0"][:, 0]) / np.abs(g) ** 2
    return correct(y, f, g), np.broadcast_to(n, (len(r),))[:, None]


def despread_loss_db(f_sym, sf):
    """Coherent-despreading loss (dB, <= 0) at a per-symbol CFO f_sym: |sum_c e^{j 2 pi (f_sym / sf) c}| / sf."""
    fc = f_sym / sf
    a = np.sin(np.pi * fc * sf) / (sf * np.sin(np.pi * fc)) if fc else 1.0
    return 20 * np.log10(abs(a))
