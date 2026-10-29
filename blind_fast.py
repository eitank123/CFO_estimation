"""
Blind CFO, round 2: cheaper code-aided metrics, a better coarse posterior and a best-first search.

Metrics (score of one (CFO, phase) hypothesis: lower = more likely; all vectorised over hypotheses)
    fast_metric   Fast-SSC path metric (list 1): rate-0, rate-1, repetition and single-parity-check nodes in closed
                  form (ML inside the node) instead of descending to every leaf; min-sum f (or the exact box-plus).
                  The SC path metric = -log P(frozen bits = 0 | r) along the SC path, i.e. an approximation of the
                  code-aided log-likelihood of the hypothesis.

Coarse posterior over the CFO grid G (step 4 x STEP = 3e-4, the SC metric's basin, over the whole +-0.2 range)
    log post(f) = w4 * S4(f) + log prior_spec(f) [+ wc * cyclic(f)]
    S4       4th-power periodogram |FFT(-r^4)|^2 at 4f (max over the bins of the grid cell), normalised by its mean
    prior    Student-t (3 dof) around the spectral (band-edge PSD template) estimate, scale = its measured RMSE
    cyclic   band-edge cyclic correlation sum_nu X(nu + 1/2) X*(nu - 1/2) W(nu - f): a second-order statistic of the
             pre-MF samples with a known (timing) phase, independent of the PSD template's noise

    python blind_fast.py bench                    # metric time per hypothesis, local
    python blind_fast.py coarse --part a          # E1: rank of the true grid cell under each posterior
    python blind_fast.py metric --rate 1/10 ...   # E2: metric separation (true vs wrong), basin, time
"""
import argparse
import json
import multiprocessing as mp
import os
import time

import numpy as np

import blind_cfo as bc

GSTEP = 4 * bc.STEP                                               # grid step of the searches (3e-4)
GRID = np.arange(-bc.MAX_CFO, bc.MAX_CFO + GSTEP / 2, GSTEP)      # 1335 cells over the whole CFO range
SPEC_SIGMA = ((-6, 5.0e-2), (-5, 4.0e-2), (-4, 3.1e-2), (-3, 2.45e-2), (-2, 2.02e-2), (-1, 1.7e-2), (0, 1.45e-2),
              (2, 1.03e-2), (5, 7.3e-3), (10, 4.4e-3))           # measured RMSE of bc.spectral (local, 4000 frames)


def spec_sigma(snr):
    return float(np.interp(snr, *zip(*SPEC_SIGMA)))


# =====================================================================
# Fast-SSC metric
# =====================================================================

def _softplus(x):
    return np.logaddexp(np.float32(0), x)


class FastSC:
    """List-1 Fast-SSC path metric of a polar code (frozen mask (N,)). metric(llr (H, N)) -> (H,)."""

    def __init__(self, frozen, exact=False):
        self.frozen = np.asarray(frozen, bool)
        self.exact = exact
        self.plan = self._plan(0, len(self.frozen))

    def _plan(self, lo, hi):
        fr = self.frozen[lo:hi]
        n = hi - lo
        if fr.all():
            return ("R0",)
        if not fr.any():
            return ("R1",)
        if n > 1 and fr[:-1].all() and not fr[-1]:
            return ("REP",)
        if n > 1 and fr[0] and not fr[1:].any():
            return ("SPC",)
        mid = lo + n // 2
        return ("N", self._plan(lo, mid), self._plan(mid, hi))

    def _f(self, a, b):
        m = np.copysign(np.minimum(np.abs(a), np.abs(b)), a * b)
        if self.exact:          # box-plus = min-sum + log(1 + e^-|a+b|) - log(1 + e^-|a-b|)
            m = m + np.log1p(np.exp(-np.abs(a + b))) - np.log1p(np.exp(-np.abs(a - b)))
        return m

    split = None            # metric_nodes: rate-0 nodes reported in chunks of `split` bits (earlier checkpoints)

    def _node(self, plan, a, pm):
        t = plan[0]
        if t == "R0":
            v = _softplus(-a)
            if self._parts is not None and self.split and v.shape[1] > self.split:
                for c in range(0, v.shape[1], self.split):
                    self._acc(pm, v[:, c:c + self.split].sum(1))
            else:
                self._acc(pm, v.sum(1))
            return np.zeros(a.shape, bool)
        if t == "R1":
            self._acc(pm, _softplus(-np.abs(a)).sum(1))
            return a < 0
        if t == "REP":
            c0, c1 = _softplus(-a).sum(1), _softplus(a).sum(1)
            self._acc(pm, np.minimum(c0, c1))
            return np.broadcast_to((c1 < c0)[:, None], a.shape).copy()
        if t == "SPC":
            h = a < 0
            par = h.sum(1) % 2 == 1
            aa = np.abs(a)
            j = aa.argmin(1)
            self._acc(pm, _softplus(-aa).sum(1) + np.where(par, aa[np.arange(len(a)), j], 0.0))
            h[np.where(par)[0], j[par]] ^= True
            return h
        n = a.shape[1] // 2
        x, y = a[:, :n], a[:, n:]
        bl = self._node(plan[1], self._f(x, y), pm)
        br = self._node(plan[2], y + np.where(bl, -x, x), pm)
        return np.concatenate([bl ^ br, br], 1)

    _parts = None

    def _acc(self, pm, v):
        if self._parts is not None:
            self._parts.append(v)
        else:
            pm += v

    def metric_nodes(self, llr):
        """Penalty of every leaf node (rate-0 / rate-1 / REP / SPC), in decoding order: (H, nodes)."""
        self._parts = []
        try:
            self._node(self.plan, np.asarray(llr, np.float32), np.zeros(len(llr), np.float32))
            return np.stack(self._parts, 1)
        finally:
            self._parts = None

    def metric(self, llr):
        pm = np.zeros(len(llr), np.float32)
        self._node(self.plan, np.asarray(llr, np.float32), pm)
        return pm

    def metric_cw(self, llr):
        """Path metric and the SC hard-decision codeword (H, N) in the LLR (de-interleaved) order."""
        pm = np.zeros(len(llr), np.float32)
        cw = self._node(self.plan, np.asarray(llr, np.float32), pm)
        return pm, cw

    def metric_left(self, llr, depth=1):
        """Partial metric: only the leftmost sub-tree of 1/2^depth of the bits (the least reliable, mostly frozen
        ones), reached by depth f-steps; the rest of the tree is skipped (about 1/2^depth of the cost)."""
        a = np.asarray(llr, np.float32)
        plan = self.plan
        for _ in range(depth):
            if plan[0] != "N":
                break
            n = a.shape[1] // 2
            a = self._f(a[:, :n], a[:, n:])
            plan = plan[1]
        pm = np.zeros(len(a), np.float32)
        self._node(plan, a, pm)
        return pm


_fast = {}


def fast_sc(A, exact=False, crc=16):
    if (A, exact) not in _fast:
        _fast[(A, exact)] = FastSC(bc.sc_code(A, crc).frozen, exact)
    return _fast[(A, exact)]


# =====================================================================
# Coarse posterior
# =====================================================================

_cyc = None


def _cyc_template():
    """Band-edge cyclic template W(nu) = H(nu + 1/2) H*(nu - 1/2) on the NFFT_S grid of the 8-SPS samples, with the
    phase of the known timing (matched-filter delay) folded in by calibration on noiseless frames."""
    from txrx_chain import rrc
    import config as cfg
    h = rrc(cfg.BETA)
    H = np.fft.fft(h, bc.NFFT_S)
    half = bc.NFFT_S // (2 * bc.SPS)                           # 1/2 cycle/symbol in bins
    return np.roll(H, -half) * np.conj(np.roll(H, half)), half


def cyclic(rx):
    """Cyclic statistic Re{C(shift)} (B, NFFT_S) over CFO shifts (bins of NFFT_S, f = k / NFFT_S * SPS):
    C(k) = sum_nu X(nu + k + 1/2) X*(nu + k - 1/2) W*(nu), by circular correlation."""
    global _cyc
    if _cyc is None:
        _cyc = _cyc_template()
    W, half = _cyc
    X = np.fft.fft(rx, bc.NFFT_S, axis=1)
    P = np.roll(X, -half, axis=1) * np.conj(np.roll(X, half, axis=1))      # X(nu + 1/2) X*(nu - 1/2)
    C = np.fft.ifft(np.fft.fft(P, axis=1) * np.conj(np.fft.fft(W))[None], axis=1)
    return C


def coarse_features(r, rx, need_cyc=True):
    """Per-frame coarse features on GRID: S4 (B, G), spectral estimate fs (B,), PSD-template and cyclic curves on
    GRID (B, G)."""
    Y = np.abs(np.fft.fft(-(r ** 4), bc.NFFT4)) ** 2
    Y /= Y.mean(1, keepdims=True)
    nu = (4 * GRID) % 1.0
    w = int(np.ceil(4 * GSTEP * bc.NFFT4)) + 1
    b0 = np.floor((nu - 2 * GSTEP) * bc.NFFT4).astype(int)
    S4 = Y[:, (b0[:, None] + np.arange(w)[None]) % bc.NFFT4].max(2)
    fs = bc.spectral(rx)
    k = np.round(GRID / bc.SPS * bc.NFFT_S).astype(int) % bc.NFFT_S
    if not need_cyc:
        return S4, fs, None
    C = cyclic(rx)
    return S4, fs, C[:, k]


def posterior(S4, fs, Cg, snr, w4=1 / 3, wc=0.0, phi=0.0):
    """Log posterior score (B, G) on GRID (higher = more likely)."""
    d = (GRID[None] - fs[:, None]) / spec_sigma(snr)
    lp = -2.0 * np.log1p(d ** 2 / 3)                             # Student-t, 3 dof
    lp = lp + w4 * S4
    if wc:
        c = (Cg * np.exp(-1j * phi)).real
        lp = lp + wc * c / np.std(c, axis=1, keepdims=True)
    return lp


# =====================================================================
# Best-first receiver: posterior-ordered sequential search (SPS)
# =====================================================================

_E = {}


def _rot(cells, power=1):
    """exp(-j 2 pi power GRID[cells] nc) (len, N), from a cached table of the whole grid (complex64)."""
    if power not in _E:
        _E[power] = np.exp(-2j * np.pi * power * GRID[:, None] * bc.NC[None]).astype(np.complex64)
    return _E[power][cells]


def _llr_pair(y, sigma2):
    """De-interleaved LLRs of y (H, N) and of y rotated by -pi/2 (the second phase hypothesis): (2H, N_BITS)."""
    out = np.empty((2 * len(y), bc.N_BITS), np.float32)
    for q, z in enumerate((y, -1j * y)):
        llr = np.empty((len(y), bc.N_BITS), np.float32)
        llr[:, 0::2] = np.sqrt(2) * z.real / sigma2
        llr[:, 1::2] = np.sqrt(2) * z.imag / sigma2
        out[q * len(y):(q + 1) * len(y)][:, bc.INTERLEAVER] = llr
    return out


SPS_DEFAULT = dict(w4=1 / 3, wc=0.0, z0=4.0, rounds=(8, 8, 16, 32, 64, 128, 256, 512, 1024), budget=len(GRID),
                   s0_snr=1.0, T=2, final=3, exact=False)


def sps_receive(r, rx, snr, code, sigma2, st, spec):
    """Posterior-ordered sequential search. Returns decoded data (B, A), CRC passed (B,), final CFO (B,), the top
    posterior cell's CFO (B,)."""
    p = {**SPS_DEFAULT, **spec.get("sps", {})}
    B = len(r)
    fast = fast_sc(code.A, p["exact"])
    out = np.zeros((B, code.A), np.uint8)
    have = np.zeros(B, bool)
    passed = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
    y4 = -(r ** 4)

    def decode(fr, fh, th):
        d, ok, _ = code.decode(bc.llrs(r[fr], fh, th, sigma2), return_info=True)
        st["decodes"] += len(fr)
        first = ~have[fr]
        out[fr[first]], have[fr[first]], f_fin[fr[first]] = d[first], True, fh[first]
        w = fr[ok]
        out[w], passed[w], f_fin[w] = d[ok], True, fh[ok]
        return ok

    def score(fr, fh, th):
        """Fast-SSC metric of hypotheses (frames fr, CFO fh, phase th): (H,)"""
        M = np.empty(len(fr), np.float32)
        for a in range(0, len(fr), 2048):
            sl = slice(a, a + 2048)
            M[sl] = fast.metric(bc.llrs(r[fr[sl]], fh[sl], th[sl], sigma2))
        st["metric_evals"] += len(fr)
        return M

    # stage 0 (high SNR): the 4th-power peak, Newton-refined, 1/4 ambiguity resolved by the spectral estimate
    S4, fs, Cg = coarse_features(r, rx, need_cyc=bool(p["wc"]))
    if snr >= p["s0_snr"]:
        nu, _ = bc._newton_tone(y4, np.fft.fftfreq(bc.NFFT4)[np.abs(np.fft.fft(y4, bc.NFFT4)).argmax(1)][:, None])
        f0 = bc.resolve((nu + 0.5) % 1.0 - 0.5, fs)[:, 0]
        th0 = bc.phase4(r, f0)
        fr = np.arange(B)
        M = score(np.tile(fr, 2), np.tile(f0, 2), np.concatenate([th0, th0 + np.pi / 2])).reshape(2, B)
        q = M.argmin(0)
        decode(fr, f0, th0 + q * np.pi / 2)
    post = posterior(S4, fs, Cg, snr, w4=p["w4"], wc=p["wc"])
    order = np.argsort(-post, 1)
    f_top = GRID[order[:, 0]]
    seen = {i: [] for i in range(B)}                         # per frame: (metric, cell, q) of every scored cell
    stats = {i: [] for i in range(B)}
    tried = {i: set() for i in range(B)}
    ptr = 0
    phase_sub = (-np.pi / 10, 0.0, np.pi / 10) if snr < -3.5 else (0.0,)
    for K in p["rounds"]:
        idx = np.where(~passed)[0]
        if not len(idx) or ptr >= p["budget"]:
            break
        K = min(K, p["budget"] - ptr)
        cells = order[idx, ptr:ptr + K]                         # (n, K)
        ptr += K
        fr = np.repeat(idx, cells.shape[1])
        c = cells.ravel()
        A4 = np.einsum("hn,hn->h", y4[fr], _rot(c, 4))
        th = np.angle(A4) / 4
        y = r[fr] * _rot(c) * np.exp(-1j * th)[:, None]
        M = np.empty(2 * len(fr), np.float32)
        llr = _llr_pair(y, sigma2)
        for a in range(0, len(llr), 2048):
            M[a:a + 2048] = fast.metric(llr[a:a + 2048])
        st["metric_evals"] += len(llr)
        M = M.reshape(2, -1)
        q = M.argmin(0)
        Mb = M.min(0)
        cand_fr, cand_f, cand_th = [], [], []
        for j, i in enumerate(idx):
            sl = slice(j * cells.shape[1], (j + 1) * cells.shape[1])
            stats[i] += list(M[:, sl].ravel())
            v = np.array(stats[i])
            med = np.median(v)
            mad = 1.4826 * np.median(np.abs(v - med)) + 1e-6
            z = (med - Mb[sl]) / mad
            seen[i] += list(zip(Mb[sl], c[sl], q[sl], th[sl]))
            for k in np.argsort(-z)[:2]:                       # at most 2 detections per frame and round
                if z[k] > p["z0"] and c[sl][k] not in tried[i]:
                    tried[i].add(c[sl][k])
                    cand_fr.append(i)
                    cand_f.append(GRID[c[sl][k]])
                    cand_th.append(th[sl][k] + q[sl][k] * np.pi / 2)
        if cand_fr:
            _refine_decode(np.array(cand_fr), np.array(cand_f), np.array(cand_th), phase_sub, p["T"], r, y4, score,
                           decode, passed)
    # budget exhausted without a CRC pass: the best-metric cells overall, refined and decoded
    idx = np.where(~passed)[0]
    cand_fr, cand_f, cand_th = [], [], []
    for i in idx:
        best = sorted(seen[i], key=lambda t: t[0])
        n_take = 0
        for m, cc, qq, tt in best:
            if n_take >= p["final"]:
                break
            if cc in tried[i]:
                continue
            tried[i].add(cc)
            n_take += 1
            cand_fr.append(i)
            cand_f.append(GRID[cc])
            cand_th.append(tt + qq * np.pi / 2)
    if cand_fr:
        _refine_decode(np.array(cand_fr), np.array(cand_f), np.array(cand_th), phase_sub, p["T"], r, y4, score,
                       decode, passed)
    return out, passed, f_fin, f_top


def _refine_decode(fr, f, th, phase_sub, T, r, y4, score, decode, passed):
    """Each candidate cell: CFO offsets 0, +-1, +-2 steps (the 4th-power phase recomputed there, mod pi/2 kept near
    the cell's phase), x phase sub-offsets; CA-SCL on the best T in metric order, stopping at a CRC pass."""
    offs = np.array([0.0, -1.0, 1.0, -2.0, 2.0]) * bc.STEP
    F = f[:, None] + offs[None]                                       # (n, 5)
    TH = bc.phase4(r[fr], F)
    TH = TH + np.round((th[:, None] - TH) / (np.pi / 2)) * (np.pi / 2)  # the same phase hypothesis as the cell
    F = np.repeat(F, len(phase_sub), 1)
    TH = (TH[:, :, None] + np.array(phase_sub)[None, None]).reshape(len(fr), -1)
    H = F.shape[1]
    rows = np.repeat(fr, H)
    M = score(rows, F.ravel(), TH.ravel()).reshape(len(fr), H)
    o = np.argsort(M, 1)
    act = np.ones(len(fr), bool)
    for t in range(T):
        j = np.where(act & ~passed[fr])[0]
        if not len(j):
            break
        ok = decode(fr[j], F[j, o[j, t]], TH[j, o[j, t]])
        act[j[ok]] = False


# =====================================================================
# Best-first receiver v2 (after E1 / E2)
#   - 4 phase hypotheses per cell (theta4 + k pi/4) below -1 dB: the 4th-power phase is > 22.5 deg off for 30 % of
#     the packets at -5 dB and the metric fails beyond ~20 deg (E2 lower tail)
#   - grid step from the measured basin of the metric (rate and SNR dependent, E2)
#   - posterior with the cyclic band-edge term (E1: P(rank >= 300) at -3 dB 0.060 -> 0.021) and an SNR-scheduled
#     4th-power weight
#   - optional reliability-weighted metric (weights per Fast-SSC node, fast_weights / E3)
# =====================================================================

def grid_step(rate, snr):
    """Grid step in STEP units: about twice the CFO offset at which the metric's z still clears z0 for 99 % of the
    packets (E2)."""
    if rate == "1/10":
        return 8 if snr >= 0 else (6 if snr >= -2 else 4)
    if rate == "1/4":
        return 4 if snr >= 2 else 3
    if rate == "1/3":
        return 3
    if rate == "2/5":                                      # between 1/3 and 1/2: the narrower basin of 1/2
        return 2
    if rate in ("3/5", "2/3", "3/4"):                      # high rates: narrow basin (E6 b)
        return 2
    return 4 if snr >= 4 else 2


_G = {}


def grid(k):
    if k not in _G:
        _G[k] = {"f": np.arange(-bc.MAX_CFO, bc.MAX_CFO + k * bc.STEP / 2, k * bc.STEP), 1: None, 4: None}
    return _G[k]


def _rot2(k, cells, power):
    G = grid(k)
    if G[power] is None:
        G[power] = np.exp(-2j * np.pi * power * G["f"][:, None] * bc.NC[None]).astype(np.complex64)
    return G[power][cells]


_SUB = {}


def _subrot(k, d):
    """De-rotation by d cells (d x k x STEP) around the cell centre, (N,) complex64."""
    if (k, d) not in _SUB:
        _SUB[(k, d)] = np.exp(-2j * np.pi * d * k * bc.STEP * bc.NC).astype(np.complex64)
    return _SUB[(k, d)]


def features2(r, rx, k, fs=None):
    """S4, spectral estimate, cyclic statistic (real part, phase 0 measured in E1) on grid(k)."""
    g = grid(k)["f"]
    step = k * bc.STEP
    Y = np.abs(np.fft.fft(-(r ** 4), bc.NFFT4)) ** 2
    Y /= Y.mean(1, keepdims=True)
    nu = (4 * g) % 1.0
    w = int(np.ceil(4 * step * bc.NFFT4)) + 1
    b0 = np.floor((nu - 2 * step) * bc.NFFT4).astype(int)
    S4 = Y[:, (b0[:, None] + np.arange(w)[None]) % bc.NFFT4].max(2)
    fs = bc.spectral(rx) if fs is None else fs
    C = cyclic(rx)[:, np.round(g / bc.SPS * bc.NFFT_S).astype(int) % bc.NFFT_S].real
    return S4, fs, C


def w4_of(snr):
    return float(np.interp(snr, (-5.0, -2.0, 1.0), (0.1, 1 / 3, 1.0)))


ACF_SIGMA = ((-5.0, 0.11), (-2.0, 0.056), (0.5, 0.032), (2.0, 0.026), (6.0, 0.02))   # lag-4 autocorrelation CFO std


def posterior2(S4, fs, C, snr, k, w4=None, wc=2.0, sig=None):
    g = grid(k)["f"]
    d = (g[None] - fs[:, None]) / (sig or spec_sigma(snr))
    lp = -2.0 * np.log1p(d ** 2 / 3) + (w4_of(snr) if w4 is None else w4) * S4
    if wc:
        lp = lp + wc * C / np.std(C, axis=1, keepdims=True)
    return lp


SPS2_DEFAULT = dict(z0=4.0, rounds=(8, 8, 16, 32, 64, 128, 256, 512, 1024, 2048), s0_snr=1.0, T=2, final=3,
                    nph=None, wc=2.0, w4=None, step=None, rate=None, weighted=False, exact=False, verify=False,
                    premf=False)


def sps2_receive(r, rx, snr, code, sigma2, st, spec):
    """Best-first search v2. Returns decoded data (B, A), CRC passed (B,), final CFO (B,), top posterior CFO (B,)."""
    p = {**SPS2_DEFAULT, **spec.get("sps", {})}
    k = p["step"] or grid_step(p["rate"], snr)
    g = grid(k)["f"]
    nph = p["nph"] or (4 if snr < -1 else 2)
    kq = np.arange(nph) * (2 if nph == 2 else 1)              # phase offsets in units of pi/4
    B = len(r)
    fast = fast_sc(code.A, p["exact"])
    wts = node_weights(p["rate"], snr) if p["weighted"] else None
    metric = (lambda llr: fast.metric_nodes(llr) @ wts) if wts is not None else fast.metric
    out = np.zeros((B, code.A), np.uint8)
    have = np.zeros(B, bool)
    passed = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
    y4 = -(r ** 4)

    def decode(fr, fh, th):
        d, ok, _ = code.decode(bc.llrs(r[fr], fh, th, sigma2), return_info=True)
        st["decodes"] += len(fr)
        if p["verify"] and ok.any():
            j = np.where(ok)[0]
            ok[j] = reencode_rho(code, r[fr[j]], d[j], fh[j]) > rho_min(snr)
            st["rejected"] = st.get("rejected", 0) + int(len(j) - ok[j].sum())
        first = ~have[fr]
        out[fr[first]], have[fr[first]], f_fin[fr[first]] = d[first], True, fh[first]
        w = fr[ok]
        out[w], passed[w], f_fin[w] = d[ok], True, fh[ok]
        return ok

    def score(fr, fh, th):
        M = np.empty(len(fr), np.float32)
        for a in range(0, len(fr), 2048):
            sl = slice(a, a + 2048)
            M[sl] = metric(bc.llrs(r[fr[sl]], fh[sl], th[sl], sigma2))
        st["metric_evals"] += len(fr)
        return M

    fs = bc.spectral(rx)
    if p["premf"]:
        r = premf(r, rx, fs)
        y4 = -(r ** 4)
    if snr >= p["s0_snr"]:                                     # stage 0: the 4th-power peak itself
        nu, _ = bc._newton_tone(y4, np.fft.fftfreq(bc.NFFT4)[np.abs(np.fft.fft(y4, bc.NFFT4)).argmax(1)][:, None])
        f0 = bc.resolve((nu + 0.5) % 1.0 - 0.5, fs)[:, 0]
        th0 = bc.phase4(r, f0)
        fr = np.arange(B)
        M = score(np.tile(fr, 2), np.tile(f0, 2), np.concatenate([th0, th0 + np.pi / 2])).reshape(2, B)
        decode(fr, f0, th0 + M.argmin(0) * np.pi / 2)
    order = np.zeros((B, len(g)), int)                         # the posterior only for the undecoded packets
    rem = np.where(~passed)[0]
    if len(rem):
        S4, _, C = features2(r[rem], rx[rem], k, fs[rem])
        order[rem] = np.argsort(-posterior2(S4, fs[rem], C, snr, k, p["w4"], p["wc"]), 1)
    f_top = np.where(passed, f_fin, g[order[:, 0]])
    stats = {i: [] for i in range(B)}
    seen = {i: [] for i in range(B)}
    tried = {i: set() for i in range(B)}
    ptr = 0
    sub = (-np.pi / 12, 0.0, np.pi / 12) if nph == 4 else (0.0,)
    roffs = np.arange(-(k // 2), k // 2 + 1)                   # refinement offsets (STEP units) around a cell
    for K in p["rounds"]:
        idx = np.where(~passed)[0]
        if not len(idx) or ptr >= len(g):
            break
        cells = order[idx, ptr:ptr + K]
        ptr += cells.shape[1]
        nK = cells.shape[1]
        fr = np.repeat(idx, nK)
        c = cells.ravel()
        th = np.angle(np.einsum("hn,hn->h", y4[fr], _rot2(k, c, 4))) / 4
        y = r[fr] * _rot2(k, c, 1) * np.exp(-1j * th)[:, None]
        M = np.empty((nph, len(y)), np.float32)
        for qi, q in enumerate(kq):
            for a in range(0, len(y), 2048):
                z = y[a:a + 2048] * np.exp(-1j * q * np.pi / 4)
                l2 = np.empty((len(z), bc.N_BITS), np.float32)
                l2[:, 0::2] = np.sqrt(2) * z.real / sigma2
                l2[:, 1::2] = np.sqrt(2) * z.imag / sigma2
                llr = np.empty_like(l2)
                llr[:, bc.INTERLEAVER] = l2
                M[qi, a:a + 2048] = metric(llr)
        st["metric_evals"] += nph * len(y)
        qb = kq[M.argmin(0)]
        Mb = M.min(0)
        cand = []
        for j, i in enumerate(idx):
            sl = slice(j * nK, (j + 1) * nK)
            stats[i] += list(M[:, sl].ravel())
            v = np.array(stats[i])
            med = np.median(v)
            mad = 1.4826 * np.median(np.abs(v - med)) + 1e-6
            z = (med - Mb[sl]) / mad
            seen[i] += list(zip(Mb[sl], c[sl], th[sl] + qb[sl] * np.pi / 4))
            for kk in np.argsort(-z)[:2]:
                if z[kk] > p["z0"] and c[sl][kk] not in tried[i]:
                    tried[i].add(c[sl][kk])
                    cand.append((i, g[c[sl][kk]], th[sl][kk] + qb[sl][kk] * np.pi / 4))
        if cand:
            _refine2(cand, roffs, sub, p["T"], r, score, decode, passed)
    cand = []
    for i in np.where(~passed)[0]:
        n_take = 0
        for m, cc, tt in sorted(seen[i], key=lambda t: t[0]):
            if n_take >= p["final"]:
                break
            if cc in tried[i]:
                continue
            tried[i].add(cc)
            n_take += 1
            cand.append((i, g[cc], tt))
    if cand:
        _refine2(cand, roffs, sub, p["T"], r, score, decode, passed)
    return out, passed, f_fin, f_top


def _refine2(cand, roffs, sub, T, r, score, decode, passed):
    """Candidates (frame, cell CFO, phase): offsets roffs x STEP (4th-power phase recomputed, kept on the cell's
    branch mod pi/2) x phase sub-offsets, scored; CA-SCL on the best T, stopping at a CRC pass."""
    fr = np.array([c[0] for c in cand])
    f = np.array([c[1] for c in cand])
    th = np.array([c[2] for c in cand])
    F = f[:, None] + roffs[None] * bc.STEP
    TH = bc.phase4(r[fr], F)
    TH = TH + np.round((th[:, None] - TH) / (np.pi / 2)) * (np.pi / 2)
    F = np.repeat(F, len(sub), 1)
    TH = (TH[:, :, None] + np.array(sub)[None, None]).reshape(len(fr), -1)
    H = F.shape[1]
    M = score(np.repeat(fr, H), F.ravel(), TH.ravel()).reshape(len(fr), H)
    o = np.argsort(M, 1)
    act = np.ones(len(fr), bool)
    for t in range(T):
        j = np.where(act & ~passed[fr])[0]
        if not len(j):
            break
        ok = decode(fr[j], F[j, o[j, t]], TH[j, o[j, t]])
        act[j[ok]] = False


# =====================================================================
# v3 additions
#   re-encoding check: a CRC pass of a wrong-CFO hypothesis (false alarm) is a codeword unrelated to r; the
#     normalised correlation of r with the re-encoded symbols at the hypothesis CFO is ~ sqrt(SNR / (1 + SNR))
#     (>= 0.45 at -5 dB) for the right packet and ~ 1 / sqrt(N) = 0.03 for an unrelated one: it removes the
#     undetected errors of CRC-16 (x2 for the pi-accepting PiCode) without extra parity bits
#   pre-MF correction: the CFO is applied before the receiver's fixed matched filter, so at |f| -> 0.2 part of the
#     signal falls outside the RRC passband (energy loss + ISI). De-rotating the 8-SPS samples by the spectral
#     estimate before the MF and putting the same CFO back at symbol rate keeps the model of r (CFO f, phase
#     convention of the chain) but with the MF matched to a residual of ~ +-0.02 instead of up to +-0.2.
# =====================================================================

def rho_min(snr):
    """Acceptance threshold: half the expected correlation of the right packet, at least 0.12 (P(random > 0.12)
    ~ exp(-N 0.12^2) = 4e-7)."""
    s = 10 ** (snr / 10)
    return max(0.12, 0.5 * np.sqrt(s / (1 + s)))


def reencode_rho(code, r, data, fh):
    """|sum_n r_n s_n* exp(-j 2 pi fh nc)| / sqrt(N sum |r|^2) of the re-encoded packet (phase-free, so the pi
    complement of PiCode counts too)."""
    cw = code.encode(data)[:, bc.INTERLEAVER]
    s = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    A = np.abs(np.sum(r * np.conj(s) * np.exp(-2j * np.pi * fh[:, None] * bc.NC[None]), 1))
    return A / np.sqrt(bc.N_SYM * np.sum(np.abs(r) ** 2, 1))


_h = None


def premf(r, rx, fs):
    """MF output with the pre-MF samples de-rotated by fs (B,), the CFO fs put back at symbol rate:
    r'[n] = MF(rx e^{-j 2 pi fs m / SPS})[n] e^{j 2 pi fs (n + DELAY_SYM)}."""
    global _h
    from scipy.signal import fftconvolve
    if _h is None:
        from txrx_chain import rrc
        import config as cfg
        _h = rrc(cfg.BETA)
    m = np.arange(rx.shape[1])
    rx2 = rx * np.exp(-2j * np.pi * fs[:, None] * m[None] / bc.SPS)
    D = bc.SPAN * bc.SPS
    r2 = fftconvolve(rx2, _h[None], axes=1)[:, D:D + bc.N_SYM * bc.SPS:bc.SPS]
    return r2 * np.exp(2j * np.pi * fs[:, None] * (np.arange(bc.N_SYM)[None] + bc.DELAY_SYM))


# =====================================================================
# v3, optimised implementation (same algorithm as sps2_receive with verify + premf)
#   - the robust z statistics of all active packets at once: every packet still searching has scored the same cells
#     count, so the scores form a (packets, scores) array (no per-packet Python lists)
#   - only the best `final` cells per packet are kept for the fallback (not every scored cell)
#   - complex64 de-rotation / LLRs
#   - optional hard path metric (max(0, -L) instead of log(1 + e^-L): the usual SC approximation, ~5x cheaper)
# =====================================================================

class FastSCHard(FastSC):
    """Fast-SSC path metric with the hard penalties: rate-0 sum max(0, -a), rate-1 0, REP min of the two hard sums,
    SPC |a_min| on a parity failure."""

    def _node(self, plan, a, pm):
        t = plan[0]
        if t == "R0":
            self._acc(pm, np.maximum(-a, 0).sum(1))
            return np.zeros(a.shape, bool)
        if t == "R1":
            return a < 0
        if t == "REP":
            c0, c1 = np.maximum(-a, 0).sum(1), np.maximum(a, 0).sum(1)
            self._acc(pm, np.minimum(c0, c1))
            return np.broadcast_to((c1 < c0)[:, None], a.shape).copy()
        if t == "SPC":
            h = a < 0
            par = h.sum(1) % 2 == 1
            aa = np.abs(a)
            j = aa.argmin(1)
            self._acc(pm, np.where(par, aa[np.arange(len(a)), j], 0.0))
            h[np.where(par)[0], j[par]] ^= True
            return h
        n = a.shape[1] // 2
        x, y = a[:, :n], a[:, n:]
        bl = self._node(plan[1], self._f(x, y), pm)
        br = self._node(plan[2], y + np.where(bl, -x, x), pm)
        return np.concatenate([bl ^ br, br], 1)


_fast_hard = {}


def fast_sc_hard(A):
    if A not in _fast_hard:
        _fast_hard[A] = FastSCHard(bc.sc_code(A).frozen)
    return _fast_hard[A]


def sps3_receive(r, rx, snr, code, sigma2, st, spec, sym=None):
    """v3 (pre-MF correction + re-encoding check), optimised, with real-MAC counting (blind_vp.MAC model) and the
    MAC-saving options:
        adaptive  score phases {0, pi/2} for every cell; the other two (pi/4, 3pi/4) only for the cells whose 2-phase
                  z is promising (> z_adapt, or the best 2 of the round)
        abort     screen every cell with the left half of the decoding tree (~45 % of the metric's operations);
                  the full metric only for the cells whose screening z > z_screen (and the best 2 of the round).
                  The first two rounds are scored in full (calibration of the z statistics).
        posterior "analytic" (spectral + cyclic + 4th power) or "nn" (blind_post_nn.py)
    and the few-pilot combination (pilots = a blind_vp.PATTERNS name; sym (B, N_SYM) the transmitted symbols):
        pilot_order  the pilot non-coherent log-likelihood log I0(2|A(f)|/N0) is added to the posterior (search order)
        pilot_check  every CRC pass must also agree with the pilots: at the code-aided phase of the re-encoded packet
                     the coherent pilot sum Re(sum_k r_k s_k* e^{-j(2 pi f nc_k + theta)}) ~ N(K, K / (2 snr)) for
                     the right packet and ~ 0 for a wrong one; accepted above K - pc_sigmas std (5 std: 3e-7 of the
                     right packets lost)
        The v3 phase search (4th power, 4 hypotheses) is kept: the pilot phase, extrapolated from the start of the
        packet to its centre, is too noisy across a grid cell.
    eco: the same decisions for fewer MACs ("v3 eco")
        - fast path (snr >= s0_snr) on a small spectral estimate (2-SPS, 2048-point FFT); the packets it does not
          deliver get the full statistics (eco_feat "lite": 2-SPS, or "8sps": v3's) and a new pre-MF correction, so
          their search is the one of the full receiver; the cyclic statistic only for those packets
        - pre-MF correction counted as its de-rotation (its matched filter replaces the chain's)
        - search: one de-rotation per cell (phase pi/2 = swap of I/Q, free), one more for the pi/4 pair, no LLR
          scaling (the min-sum metric and the per-packet z-test are scale-invariant): metric MACs only per phase
        - adaptive phases / early abort only where they were lossless (eco_gate: SNR from which they are used)
    redecode: after a CRC pass, CFO / phase decision-directed from the decoded packet (bc.dd_refine, all N symbols);
        if the CFO moved by more than rd_tol, decode again there: a false pass of a near-correct codeword (decoded at
        a hypothesis a cell or two off) gives an accurate DD estimate, so the re-decode corrects it (CRC pass) or
        rejects it (CRC fail, the search goes on). rd_where "all" or "search" (not the fast path)
    branch2: a decode whose CRC fails is repeated on the other pi/2 branch (phase + pi/2): the code metric picks the
        wrong pi/2 branch of the 4th-power phase for ~1.3 % of the packets at the waterfall (blind_diag.py: R = 2/5,
        0.5 dB, true CFO: 2942 / 3000 decoded with the metric's branch, 2982 with either branch, 2988 true phase)
    redecode scopes: rd_where "extra" re-decodes only the passes of the code-aided retries and of the posterior final
        cells (always, rd_tol 0); rd_keep: a failed re-decode keeps the first pass instead of rejecting it
    ca_retry: a decode whose CRC fails is repeated at the code-aided CFO / phase (2 Newton steps on r s*, s the SC
        hard decisions of the code metric at the hypothesis): blind_diag at R = 2/5, 0.5 dB, the true grid cell:
        2972 / 3000 decoded with v3's refine, 2984 with the code-aided step (genie 2988)
    phase_fft: the cells' 4th-power phase read from the 4th-power FFT (bins 1/4096, already computed for S4) instead
        of one correlation per cell
    fast-path cost (eco3): coarse "acf" = lag-4 autocorrelation of the 8-SPS samples (one cmul per sample, std ~0.03:
        enough to resolve the 4th-power ambiguity, +-1/8), then premf2 = the pre-MF correction redone at the resolved
        4th-power estimate; nfft4 / newton = FFT size / Newton steps of the 4th-power estimate; pi2 "left" = the pi/2
        branch chosen by the left-half metric. A wrong fast-path decision only fails CRC and goes to the search."""
    import blind_vp as vp
    p = {**SPS2_DEFAULT, "verify": True, "premf": True, "hard": False, "adaptive": False, "z_adapt": 2.0,
         "abort": False, "z_screen": 2.5, "posterior": "analytic", "lite": False,
         "pilots": None, "pilot_order": True, "pilot_check": True, "pc_sigmas": 5.0, "eco": False, "eco_feat": "lite",
         "eco_gate": None, "redecode": False, "rd_tol": 5e-5, "rd_where": "all", "phase_fft": False,
         "branch2": False, "ca_retry": False, "final_post": 0, "rd_keep": False, "coarse": "small",
         "premf2": False, "nfft4": bc.NFFT4, "newton": 3, "pi2": "full", "step_from": None, "fast_peaks": 0, "fast_ratio": 0.0, "pilot_phase": False, "plus_below": None, "s4_interp": 0, "pilot_pi2": False, "hi_snr": None, "pilot_direct": 0, "no_stats": False, "ca_fast": True, "z_screen_low": None, "z_screen_vlow": None, "screen_rnd": 2,
         "share_reencode": False, "fast_nn": False, "fast_skip": None, "cell_nn": False,
         "cell_tau": 0.5, "parab": False, "rank_nn": False, "fine_last": 0, "T_fine": 6, "adapt_gate": None, "screen_from": -4.0, "rho_n": None,
         "sub_all": None, "sub_z": None, "sub_below": None,
         **spec.get("sps", {})}
    if p["sub_below"] is not None and snr >= p["sub_below"].get(p["rate"], -np.inf):
        p["sub_all"] = p["sub_z"] = None                      # the in-cell CFO grid only on the waterfall
    if p["hi_snr"] is not None and snr >= p["hi_snr"].get(p["rate"], np.inf):
        p.update(nfft4=1024, s4_interp=4, premf2=False)       # above the waterfall: the cheapest fast path
    if isinstance(p["pilot_phase"], (int, float)) and not isinstance(p["pilot_phase"], bool):
        p["pilot_phase"] = snr >= p["pilot_phase"]           # pilot-chosen search phases from this SNR (smoke-10)
    if p["z_screen_low"] is not None and snr < -2.5:          # looser left-metric screening at low SNR (smoke-11)
        p["z_screen"] = p["z_screen_low"]
    if p["z_screen_vlow"] is not None and snr < -3.5:
        p["z_screen"] = p["z_screen_vlow"]
    if isinstance(p["s0_snr"], dict):                         # per-rate fast-path threshold
        p["s0_snr"] = p["s0_snr"].get(p["rate"], 1.0)
    if p["plus_below"] is not None and snr >= p["plus_below"].get(p["rate"], np.inf):
        p["ca_retry"], p["final_post"] = False, 0             # eco+ extras only on the waterfall (CRC false passes)
    eco = p["eco"]
    if eco:
        gate = p["eco_gate"] if p["eco_gate"] is not None else {"1/10": -2.0}
        gate = {"1/10": -2.0, **gate}.get(p["rate"], -np.inf) if isinstance(gate, dict) else gate
        p["adaptive"] = p["abort"] = snr >= gate
        if p["adapt_gate"] is not None:                   # adaptive phases alone from their own SNR (per rate)
            ag = p["adapt_gate"].get(p["rate"], gate) if isinstance(p["adapt_gate"], dict) else p["adapt_gate"]
            p["adaptive"] = snr >= ag
        p["lite"] = p["eco_feat"] == "lite"
    if p["posterior"] == "nn":
        p["lite"] = True
    k = p["step"] or grid_step(p["rate"], snr)
    sf = p["step_from"].get(p["rate"]) if isinstance(p["step_from"], dict) else p["step_from"]
    if sf is not None and snr >= sf[1]:                       # coarser grid from that SNR (basin E6)
        k = sf[0]
    g = grid(k)["f"]
    nph = p["nph"] or (4 if snr < -1 else 2)
    B = len(r)
    fs_ = fast_sc_hard(code.A) if p["hard"] else fast_sc(code.A)
    metric = fs_.metric
    m_full = vp.metric_macs(code.A) + vp.MAC["llr"]
    m_left = _left_macs(code.A) + vp.MAC["llr"]
    m_met, m_lmet = vp.metric_macs(code.A), _left_macs(code.A)
    derot = vp.MAC["cmul"] * bc.N_SYM
    macs = np.zeros(B)
    out = np.zeros((B, code.A), np.uint8)
    have = np.zeros(B, bool)
    passed = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
    scale = np.float32(np.sqrt(2) / sigma2)

    in_search = [False]
    in_post = [False]
    dd_macs = 4 * bc.N_SYM + len(bc.DD_SCAN) * bc.N_SYM * 8 + 3 * 20 * bc.N_SYM + vp.MAC["reencode"]

    def decode(fr, fh, th):
        fh = np.array(fh, float)
        th = np.array(th, float)
        d, ok, _ = code.decode(bc.llrs(r[fr], fh, th, sigma2), return_info=True)
        xm = np.full(len(fr), in_post[0])                    # passes of the extra decodes
        if p["branch2"] and not ok.all():                     # the other pi/2 branch of the failed decodes
            j = np.where(~ok)[0]
            d2, ok2, _ = code.decode(bc.llrs(r[fr[j]], fh[j], th[j] + np.pi / 2, sigma2), return_info=True)
            st["decodes"] += len(j)
            np.add.at(macs, fr[j], vp.MAC["decode"] + vp.MAC["llr"])
            st["branch2_used"] = st.get("branch2_used", 0) + int(ok2.sum())
            d[j[ok2]], ok[j[ok2]], th[j[ok2]] = d2[ok2], True, th[j[ok2]] + np.pi / 2
        if p["ca_retry"] and (in_search[0] or p["ca_fast"]) and not ok.all():   # code-aided CFO / phase, failed decodes
            j = np.where(~ok)[0]
            _, cwh = fs_.metric_cw(bc.llrs(r[fr[j]], fh[j], th[j], sigma2))
            fca, tca = code_aided(r[fr[j]], fh[j], cwh, 2)
            d2, ok2, _ = code.decode(bc.llrs(r[fr[j]], fca, tca, sigma2), return_info=True)
            st["decodes"] += len(j)
            np.add.at(macs, fr[j], m_full + CA_MACS(2) + vp.MAC["decode"] + vp.MAC["llr"])
            st["ca_used"] = st.get("ca_used", 0) + int(ok2.sum())
            d[j[ok2]], ok[j[ok2]], fh[j[ok2]], th[j[ok2]] = d2[ok2], True, fca[ok2], tca[ok2]
            xm[j[ok2]] = True
        st["decodes"] += len(fr)
        np.add.at(macs, fr, vp.MAC["decode"] + vp.MAC["llr"])
        if p["verify"] and ok.any():
            j = np.where(ok)[0]
            np.add.at(macs, fr[j], vp.MAC["reencode"])
            rho = reencode_rho(code, r[fr[j]], d[j], fh[j])
            thr = rho_min(snr)
            tab = p["rho_n"].get(p["rate"]) if isinstance(p["rho_n"], dict) else p["rho_n"]
            if tab:                                           # normalised threshold: rho / sqrt(s / (1 + s)) of a
                s_ = 10 ** (snr / 10)                         # right decode ~ 1; a staircase false pass ~ 0.5-0.92
                thr = max(thr, float(np.interp(snr, *zip(*tab))) * np.sqrt(s_ / (1 + s_)))
            ok[j] = rho > thr
            st["rejected"] = st.get("rejected", 0) + int(len(j) - ok[j].sum())
            if "diag" in st:                                  # accepted decodes: rho, stage (0 fast, 1 search, 2 final)
                w = j[ok[j]]
                st["diag"]["rho"][fr[w]] = rho[ok[j]]
                st["diag"]["stage"][fr[w]] = 2 if in_post[0] else int(in_search[0])
                st["diag"]["ca"][fr[w]] = xm[w]
        if pos is not None and p["pilot_check"] and ok.any():
            j = np.where(ok)[0]
            np.add.at(macs, fr[j], (0 if p["verify"] and p["share_reencode"] else vp.MAC["reencode"])
                      + 2 * vp.MAC["cmul"] * len(pos))            # (the re-encoded packet of the rho check, if shared)
            c = pilot_coherent(code, r[fr[j]], d[j], fh[j], zp[fr[j]], pos)
            ok[j] = c > len(pos) - p["pc_sigmas"] * np.sqrt(len(pos) / (2 * 10 ** (snr / 10)))
            st["pilot_rejected"] = st.get("pilot_rejected", 0) + int(len(j) - ok[j].sum())
        sel = ok & xm if p["rd_where"] == "extra" else ok
        if p["redecode"] and sel.any() and (p["rd_where"] != "search" or in_search[0]):
            j = np.where(sel)[0]
            fd, thd = bc.dd_refine(r[fr[j]], d[j], code, fh[j])
            np.add.at(macs, fr[j], dd_macs)
            far = np.abs(fd - fh[j]) > (0.0 if p["rd_where"] == "extra" else p["rd_tol"])
            if far.any():
                jj = j[far]
                d2, ok2, _ = code.decode(bc.llrs(r[fr[jj]], fd[far], thd[far], sigma2), return_info=True)
                st["decodes"] += len(jj)
                np.add.at(macs, fr[jj], vp.MAC["decode"] + vp.MAC["llr"])
                st["redecoded"] = st.get("redecoded", 0) + len(jj)
                st["rd_changed"] = st.get("rd_changed", 0) + int((ok2 & (d2 != d[jj]).any(1)).sum())
                st["rd_rejected"] = st.get("rd_rejected", 0) + int((~ok2).sum())
                d[jj[ok2]] = d2[ok2]
                fh[jj[ok2]] = fd[far][ok2]
                if not p["rd_keep"]:
                    ok[jj[~ok2]] = False
        first = ~have[fr]
        out[fr[first]], have[fr[first]], f_fin[fr[first]] = d[first], True, fh[first]
        w = fr[ok]
        out[w], passed[w], f_fin[w] = d[ok], True, fh[ok]
        return ok

    def score(fr, fh, th):
        M = np.empty(len(fr), np.float32)
        for a in range(0, len(fr), 2048):
            sl = slice(a, a + 2048)
            M[sl] = metric(bc.llrs(r[fr[sl]], fh[sl], th[sl], sigma2))
        st["metric_evals"] += len(fr)
        np.add.at(macs, fr, (m_met + derot) if eco else (m_full + vp.MAC["phase4"] / 4))
        return M

    def score_cells(y, fr, q, left=False):
        """Metric of de-rotated cells y (H, N) at phase offset q (units of pi/4)."""
        M = np.empty(len(y), np.float32)
        rq = np.complex64(np.exp(-1j * q * np.pi / 4))
        for a in range(0, len(y), 2048):
            z = y[a:a + 2048] * rq
            n = len(z)
            l2 = np.empty((n, bc.N_BITS), np.float32)
            l2[:, 0::2] = z.real
            l2[:, 1::2] = z.imag
            l2 *= scale
            llr = np.empty_like(l2)
            llr[:, bc.INTERLEAVER] = l2
            M[a:a + n] = fs_.metric_left(llr, 1) if left else metric(llr)
        st["metric_evals"] += len(y)
        if eco:                                     # metric only; the pi/4 pair needs one more de-rotation
            np.add.at(macs, fr, (m_lmet if left else m_met) + (derot if q == 1 else 0))
        else:
            np.add.at(macs, fr, m_left if left else m_full)
        return M

    r_mf = r
    small = eco and snr >= p["s0_snr"]
    if small and p["coarse"] == "acf":                        # eco3: lag-4 autocorrelation of the 8-SPS samples
        fs = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
        macs += vp.MAC["cmul"] * rx.shape[1]
    elif small:                                               # eco fast path: small spectral estimate only
        fs = vp.spectral_small(vp.decimate(rx))
        macs += vp.DECIM_MACS + vp.SMALL_SPEC_MACS
    elif p["lite"]:                                           # 2-SPS PSD-template + cyclic statistics
        _, fs, C_lite = vp.features_lite(r, rx, k)
        macs += 2 * vp.LITE_MACS - (vp.DECIM_MACS if eco else 0)
    else:
        fs = bc.spectral(rx)
        macs += vp.SPECTRAL_MACS
    if p["premf"]:
        r = premf(r, rx, fs)
        macs += vp.PREMF_FAIR_MACS if eco else vp.PREMF_MACS
    pos = zp = None
    if p["pilots"]:
        pos = np.array(vp.PATTERNS[p["pilots"]])
        zp = r[:, pos] * np.conj(sym[:, pos])
    y4 = -(r ** 4)
    r64 = r.astype(np.complex64)
    if snr >= p["s0_snr"]:
        nf = p["nfft4"]
        Y4a = np.abs(np.fft.fft(y4, nf))
        fref = fs
        skip = np.zeros(B, bool)
        if p["fast_nn"] and nf == bc.NFFT4:                   # the peak graded by the small NN (blind_peak_nn)
            import blind_peak_nn as pknn
            xf, fc, pk = pknn.features(r, Y4a, fs, snr, zp, pos)
            pr = pknn.grade("pilots" if pos is not None else "blind", xf)
            jb = pr[:, :pknn.P].argmax(1)
            if p["fast_skip"] is not None:                    # "no peak is right": skip the fast-path decode
                skip = pr[:, pknn.P] > p["fast_skip"]
            macs += pknn.MACS
            fref = fc[np.arange(B), jb]
            nu0 = np.fft.fftfreq(nf)[pk[np.arange(B), jb]][:, None]
        elif p["fast_peaks"]:                                 # the fast-path peak chosen among the top P peaks
            P = p["fast_peaks"]
            pk = bc.top_peaks(Y4a, P, 2)
            fc = bc.resolve(np.fft.fftfreq(nf)[pk], fs)       # (B, P) candidate CFOs (bin accuracy)
            hp = np.take_along_axis(Y4a, pk, 1)
            live = hp >= p["fast_ratio"] * hp[:, :1]          # only peaks nearly as high as the strongest compete
            live[:, 0] = True
            sc = np.full((B, P), np.inf)
            if pos is not None:                               # by the pilots' coherent sum (~100 MACs a peak)
                spl = -np.abs(np.einsum("bk,bpk->bp", zp, np.exp(-2j * np.pi * fc[:, :, None]
                                                               * (pos - bc.CENTRE)[None, None])))
                sc[live] = spl[live]
                macs += live.sum(1) * (vp.MAC["cmul"] * len(pos) + 8 * len(pos))
            else:                                             # by the left-half metric, both pi/2 branches
                for j in range(P):
                    rw = np.where(live[:, j])[0]
                    if not len(rw):
                        continue
                    t = bc.phase4(r[rw], fc[rw, j])
                    sc[rw, j] = np.minimum(*[fs_.metric_left(bc.llrs(r[rw], fc[rw, j], t + q * np.pi / 2, sigma2), 1)
                                             for q in range(2)])
                    st["metric_evals"] += 2 * len(rw)
                    macs[rw] += vp.MAC["phase4"] + 2 * (m_lmet + derot)
                one = live.sum(1) == 1                        # a single live peak needs no metric
                macs[one] -= vp.MAC["phase4"] + 2 * (m_lmet + derot)
            jb = sc.argmin(1)
            fref = fc[np.arange(B), jb]
            nu0 = np.fft.fftfreq(nf)[pk[np.arange(B), jb]][:, None]
        else:
            nu0 = np.fft.fftfreq(nf)[Y4a.argmax(1)][:, None]
        kb = np.rint(nu0[:, 0] * nf).astype(int) % nf          # FFT bin of the chosen peak
        V = Y4a[np.arange(B)[:, None], (kb[:, None] + np.array([-1, 0, 1])[None]) % nf]   # bin -1, 0, +1
        if p["s4_interp"]:                                    # off-bin points around the peak of a short FFT
            m = p["s4_interp"]                                # (the zero padding of the 4096 FFT, for this bin only)
            dn = np.arange(-(m - 1), m) / (m * nf)
            dn = dn[dn != 0]
            cand = nu0 + dn[None]
            A = np.abs(np.einsum("bn,bpn->bp", y4, np.exp(-2j * np.pi * cand[:, :, None] * bc.NC[None, None])))
            A0 = Y4a.max(1) if not p["fast_peaks"] else np.take_along_axis(Y4a, pk[np.arange(B), jb][:, None], 1)[:, 0]
            better = A.max(1) > A0
            if p["parab"]:                                    # the sub-grid -m..m: FFT bins at -m, 0, m
                V = np.concatenate([V[:, :1], A[:, :m - 1], V[:, 1:2], A[:, m - 1:], V[:, 2:]], 1)
            nu0 = np.where(better[:, None], cand[np.arange(B), A.argmax(1)][:, None], nu0)
            macs += len(dn) * vp.MAC["cmul"] * bc.N_SYM
        if p["parab"]:                                        # parabolic fit through the 3 points around the
            m = V.shape[1] // 2                               # largest one (spacing 1 / (m nf)) instead of Newton
            ip = 1 + V[:, 1:-1].argmax(1)
            rw = np.arange(B)
            va, vb, vc = V[rw, ip - 1], V[rw, ip], V[rw, ip + 1]
            den = va - 2 * vb + vc
            off = np.clip(np.where(den < 0, 0.5 * (va - vc) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
            nu = (np.fft.fftfreq(nf)[kb] + (ip - m + off) / (m * nf))[:, None]
            macs += 2 * 4 * bc.N_SYM + vp.fft_macs(nf) + 8
        else:
            nu, _ = bc._newton_tone(y4, nu0, p["newton"])
            macs += 2 * 4 * bc.N_SYM + vp.fft_macs(nf) + vp.NEWTON_MACS * (p["newton"] + 1) / 4
        f0 = bc.resolve((nu + 0.5) % 1.0 - 0.5, fref)[:, 0]
        if small and p["premf2"]:                             # pre-MF again at the resolved 4th-power estimate
            r = premf(r_mf, rx, f0)
            macs += vp.PREMF_FAIR_MACS
        th0 = bc.phase4(r, f0)
        macs += vp.MAC["phase4"]
        fr = np.arange(B)
        if (p["pilot_phase"] or p["pilot_pi2"]) and pos is not None:    # pi/2 branch by the pilots' phase
            zp0 = r[:, pos] * np.conj(sym[:, pos])
            zz = np.sum(zp0 * np.exp(-2j * np.pi * f0[:, None] * (pos - bc.CENTRE)[None]), 1)
            rel = ((np.angle(zz) - th0) / (np.pi / 2)) % 2      # pi/2 units; PiCode makes pi free
            M = np.stack([np.minimum(rel, 2 - rel), np.abs(rel - 1)])
            macs += vp.MAC["cmul"] * 3 * len(pos)
        elif p["pi2"] == "left":                              # pi/2 branch by the left-half metric
            M = np.empty((2, B), np.float32)
            for qq in range(2):
                M[qq] = fs_.metric_left(bc.llrs(r, f0, th0 + qq * np.pi / 2, sigma2), 1)
            st["metric_evals"] += 2 * B
            macs += 2 * (m_lmet + derot)
        else:
            M = score(np.tile(fr, 2), np.tile(f0, 2), np.concatenate([th0, th0 + np.pi / 2])).reshape(2, B)
        keep = ~skip
        decode(fr[keep], f0[keep], (th0 + M.argmin(0) * np.pi / 2)[keep])
    in_search[0] = True
    order = np.zeros((B, len(g)), int)
    post_rel = np.zeros((B, len(g)), np.float32)
    rem = np.where(~passed)[0]
    if small and len(rem):                                    # eco: full statistics + pre-MF for the rest
        fs = fs.copy()
        nost = p["no_stats"] and pos is not None              # pilots: no spectral / cyclic statistics, the ruler
        if nost:                                              # + 4th power + the autocorrelation prior rank the cells
            C_lite = np.zeros((B, len(g)))
        elif p["lite"]:
            C_lite = np.zeros((B, len(g)))
            _, fs[rem], C_lite[rem] = vp.features_lite(r_mf[rem], rx[rem], k)
            macs[rem] += 2 * vp.LITE_MACS - 2 * vp.DECIM_MACS
        else:
            fs[rem] = bc.spectral(rx[rem])
            macs[rem] += vp.SPECTRAL_MACS
        r = r.copy()
        r[rem] = premf(r_mf[rem], rx[rem], fs[rem])
        macs[rem] += vp.PREMF_FAIR_MACS
        y4 = -(r ** 4)
        r64 = r.astype(np.complex64)
        if pos is not None:
            zp = r[:, pos] * np.conj(sym[:, pos])
    if len(rem):
        if p["posterior"] == "nn":
            import blind_post_nn as pnn
            post, _ = pnn.posterior(r[rem], rx[rem], snr, k)
            macs[rem] += pnn.MACS + vp.S4_MACS
        elif small and p["no_stats"] and pos is not None:
            post = posterior2(vp.s4_grid(r[rem], k), fs[rem], C_lite[rem], snr, k, p["w4"], 0.0,
                              float(np.interp(snr, *zip(*ACF_SIGMA))))
            macs[rem] += vp.S4_MACS
        elif p["lite"]:
            S4r = vp.s4_grid(r[rem], k)
            post = posterior2(S4r, fs[rem], C_lite[rem], snr, k, p["w4"], p["wc"])
            macs[rem] += vp.S4_MACS
        else:
            S4, _, C = features2(r[rem], rx[rem], k, fs[rem])
            post = posterior2(S4, fs[rem], C, snr, k, p["w4"], p["wc"])
            macs[rem] += vp.CYCLIC_MACS + vp.S4_MACS
        pl = None
        if pos is not None and p["pilot_order"]:               # + the pilot ruler
            pl = vp.pilot_loglik(vp.pilot_A(zp[rem], pos, g), snr)
            post = post + pl
            macs[rem] += vp.MAC["cmul"] * len(pos) * len(g)
        if p["rank_nn"] and p["lite"] and p["posterior"] != "nn":   # the order re-scored by the cell-ranking NN
            import blind_rank_nn as rnn
            M = min(int(p["rank_nn"]), len(g))                # re-score only the top M analytic cells
            top = np.argsort(-post, 1)[:, :M]
            rw = np.arange(len(rem))[:, None]
            x = rnn.features(post, S4r, fs[rem], C_lite[rem], pl, snr, k)[rw, top]
            sc = 10 * rnn.score("pilots" if pos is not None else "blind", x)
            lo = post.min(1, keepdims=True)
            post = post - (post.max(1, keepdims=True) - lo + 1.0)   # the rest: same order, below lo
            post[rw, top] = sc - sc.min(1, keepdims=True) + lo      # the top M in the NN's order
            macs[rem] += rnn.macs(M)
        order[rem] = np.argsort(-post, 1)
        if "diag" in st:                                      # failure diagnostics: posterior rank of the true cell
            tcell = np.abs(g[None] - st["truth"][rem][:, None]).argmin(1)
            st["diag"]["prank"][rem] = np.argmax(order[rem] == tcell[:, None], 1)
        post_rel[rem] = post - post.max(1, keepdims=True)    # (cell-grader input)
        macs[rem] += len(g) * int(np.log2(len(g)))
    f_top = np.where(passed, f_fin, g[order[:, 0]])
    nF = p["final"]
    bestM = np.full((B, nF), np.inf, np.float32)
    bestC = np.zeros((B, nF), int)
    bestT = np.zeros((B, nF))
    stats = np.zeros((B, 0), np.float32)
    tried = [set() for _ in range(B)]
    sub = (-np.pi / 12, 0.0, np.pi / 12) if nph == 4 else (0.0,)
    roffs = np.arange(-(k // 2), k // 2 + 1)
    ptr = 0
    y4_64 = y4.astype(np.complex64)
    Y4c = np.fft.fft(y4, bc.NFFT4, axis=1) if p["phase_fft"] else None    # (its cost is in S4_MACS)
    base_q = (0, 2)                                            # phases scored for every cell (units of pi/4)
    extra_q = (1, 3) if nph == 4 else ()
    idx = np.where(~passed)[0]
    if p["pilot_direct"] and pos is not None and len(idx):      # pilots: refine + decode the top posterior cells first
        cand = []
        for j in range(p["pilot_direct"]):
            c = order[idx, j]
            t4 = bc.phase4(r[idx], g[c])
            zz = np.sum(zp[idx] * np.exp(-2j * np.pi * g[c][:, None] * (pos - bc.CENTRE)[None]), 1)
            q = np.round(((np.angle(zz) - t4) / (np.pi / 4)) % 4) % 4   # the pilots' phase, on the pi/4 lattice
            macs[idx] += vp.MAC["phase4"] + vp.MAC["cmul"] * 2 * len(pos)
            for i, cc, t in zip(idx, c, t4 + q * np.pi / 4):
                tried[i].add(cc)
                cand.append((i, g[cc], t))
        _refine2(cand, roffs, sub, p["T"], r, score, decode, passed)
    for rnd, K in enumerate(p["rounds"]):
        idx = np.where(~passed)[0]
        if not len(idx) or ptr >= len(g):
            break
        cells = order[idx, ptr:ptr + K]
        ptr += cells.shape[1]
        nK = cells.shape[1]
        fr = np.repeat(idx, nK)
        c = cells.ravel()
        if p["phase_fft"]:                                    # 4th-power FFT bin of 4 f, centre-referenced
            nu = 4 * g[c]
            b = np.round((nu % 1.0) * bc.NFFT4).astype(int) % bc.NFFT4
            nus = nu + ((b / bc.NFFT4 - nu % 1.0 + 0.5) % 1.0 - 0.5)
            th = np.angle(Y4c[fr, b] * np.exp(2j * np.pi * nus * bc.CENTRE)) / 4
            np.add.at(macs, fr, vp.MAC["cmul"])
        else:
            th = np.angle(np.einsum("hn,hn->h", y4_64[fr], _rot2(k, c, 4))) / 4
            np.add.at(macs, fr, vp.MAC["phase4"])
        y = r64[fr] * _rot2(k, c, 1) * np.exp(-1j * th).astype(np.complex64)[:, None]
        if eco:                                                   # the cell's de-rotation, shared by its phases
            np.add.at(macs, fr, derot)
        pph = p["pilot_phase"] and pos is not None and bool(extra_q)   # 2 of 4 phases (1 of 2 starves the z-test)
        screen = p["abort"] and rnd >= p["screen_rnd"] and snr >= p["screen_from"] and not pph
        if pph:                                                   # the pilots pick the cell's phase branch(es)
            zz = np.einsum("hk,hk->h", zp[fr], np.exp(-2j * np.pi * g[c][:, None] * (pos - bc.CENTRE)[None]))
            rel = ((np.angle(zz) - th) / (np.pi / 4)) % 4          # pilot phase - 4th-power phase, pi/4 units
            qs = base_q + extra_q
            d = np.stack([np.minimum((rel - q) % 4, (q - rel) % 4) for q in qs])
            keep = np.zeros_like(d, bool)
            np.put_along_axis(keep, np.argsort(d, 0)[:2 if extra_q else 1], True, 0)
            M = np.full((len(qs), len(y)), np.inf, np.float32)
            for qi, q in enumerate(qs):
                M[qi, keep[qi]] = score_cells(y[keep[qi]], fr[keep[qi]], q)
            np.add.at(macs, fr, vp.MAC["cmul"] * 2 * len(pos))
        elif p["sub_all"] and not screen and not (p["adaptive"] and extra_q):
            # in-cell CFO grid: every cell scored at a few CFOs inside it (fractions of the cell) instead of its
            # centre, so an off-centre true CFO is still inside the metric's basin; the reference population of the
            # z-test is scored the same way (min over the same offsets), so its z stays unbiased
            qs = base_q + extra_q
            M = np.min([np.stack([score_cells(y * _subrot(k, d), fr, q) for q in qs]) for d in p["sub_all"]], 0)
            np.add.at(macs, fr, derot * len(p["sub_all"]))
        else:
            qs = base_q if (p["adaptive"] or screen) else base_q + extra_q
            M = np.stack([score_cells(y, fr, q, left=screen) for q in qs])          # (len(qs), H)
        if not pph and (screen or (p["adaptive"] and extra_q)):
            Mq = M.min(0).reshape(len(idx), nK)
            # screening / adaptive statistics from this round's own scores (almost all of them wrong cells)
            ref = M.reshape(len(qs), len(idx), nK).transpose(1, 0, 2).reshape(len(idx), -1)
            med = np.median(ref, 1)
            mad = 1.4826 * np.median(np.abs(ref - med[:, None]), 1) + 1e-6
            zq = (med[:, None] - Mq) / mad[:, None]
            thr = p["z_screen"] if screen else p["z_adapt"]
            sel = zq > thr
            sel[np.arange(len(idx))[:, None], np.argsort(-zq, 1)[:, :2]] = True
            sel = sel.ravel()
            # full metric (screen) / the remaining phases (adaptive) for the selected cells only
            if screen:
                Mf = np.full((len(base_q + extra_q), len(y)), np.inf, np.float32)
                for qi, q in enumerate(base_q + extra_q):
                    Mf[qi, sel] = score_cells(y[sel], fr[sel], q)
                M = Mf
                qs = base_q + extra_q
            else:
                Mx = np.full((len(extra_q), len(y)), np.inf, np.float32)
                for qi, q in enumerate(extra_q):
                    Mx[qi, sel] = score_cells(y[sel], fr[sel], q)
                M = np.concatenate([M, Mx])
                qs = base_q + extra_q
        qarr = np.array(qs)
        qb = qarr[M.argmin(0)].reshape(len(idx), nK)
        Mb = M.min(0).reshape(len(idx), nK)
        thc = th.reshape(len(idx), nK) + qb * np.pi / 4
        # robust z against this packet's finite full-metric scores so far (base phases; screened-out cells excluded)
        new = M[:len(base_q)].reshape(len(base_q), len(idx), nK).transpose(1, 0, 2).reshape(len(idx), -1)
        if screen or pph:
            new = np.where(np.isfinite(new), new, np.nan)
        full = np.full((B, stats.shape[1] + new.shape[1]), np.nan, np.float32)
        full[:, :stats.shape[1]] = stats
        full[idx, stats.shape[1]:] = new
        stats = full
        v = stats[idx]
        med = np.nanmedian(v, 1)
        mad = 1.4826 * np.nanmedian(np.abs(v - med[:, None]), 1) + 1e-6
        z = (med[:, None] - Mb) / mad[:, None]
        z = np.where(np.isfinite(z), z, -np.inf)
        if p["sub_z"]:
            # near misses (z_lo < z <= z0, the best `top` of the round): scored again at CFOs inside the cell and
            # z recomputed with the best of them against the same (centre-scored) reference
            zl, ntop, offs = p["sub_z"]
            zs = np.where((z > zl) & (z <= p["z0"]), z, -np.inf)
            o_ = np.argsort(-zs, 1)[:, :ntop]
            jj, t_ = np.where(np.take_along_axis(zs, o_, 1) > -np.inf)
            if len(jj):
                kk = o_[jj, t_]
                h = jj * nK + kk                                  # flat (packet, cell) index of fr / y
                qa = base_q + extra_q
                Ms = np.stack([np.stack([score_cells(y[h] * _subrot(k, d), fr[h], q) for q in qa]) for d in offs])
                np.add.at(macs, fr[h], derot * len(offs))
                Ms = Ms.reshape(-1, len(h))                       # (offs x phases, H)
                b_ = Ms.argmin(0)
                mn = Ms[b_, np.arange(len(h))]
                better = mn < Mb[jj, kk]
                jj, kk, mn, qn = jj[better], kk[better], mn[better], np.array(qa)[b_[better] % len(qa)]
                Mb[jj, kk] = mn
                thc[jj, kk] = th.reshape(len(idx), nK)[jj, kk] + qn * np.pi / 4
                z[jj, kk] = (med[jj] - mn) / mad[jj]
        allM = np.concatenate([bestM[idx], Mb], 1)
        allC = np.concatenate([bestC[idx], cells], 1)
        allT = np.concatenate([bestT[idx], thc], 1)
        o = np.argsort(allM, 1)[:, :nF]
        bestM[idx] = np.take_along_axis(allM, o, 1)
        bestC[idx] = np.take_along_axis(allC, o, 1)
        bestT[idx] = np.take_along_axis(allT, o, 1)
        cand = []
        if p["cell_nn"] or "dump" in st:                      # cell grader: z, posterior rank / score, SNR
            pos_c = np.arange(ptr - nK, ptr)[None].repeat(len(idx), 0)
            Fc = np.stack([np.clip(z, -10, 30), np.log2(1 + pos_c), np.clip(post_rel[idx[:, None], cells], -30, 0),
                           np.full(z.shape, snr / 10.0), np.full(z.shape, rnd / 10.0)], -1).astype(np.float32)
            if "dump" in st:
                lab = np.abs(g[cells] - st["truth"][idx][:, None]) < k * bc.STEP
                st["dump"].append(np.concatenate([Fc.reshape(-1, Fc.shape[-1]), lab.reshape(-1, 1)], 1))
            if p["cell_nn"]:
                import blind_cell_nn as cnn
                cnn.set_model("pilots" if pos is not None else "blind", p["rate"])
                z = np.where(np.isfinite(z), cnn.grade(Fc), -np.inf)   # P(true cell): replaces the z-test
                np.add.at(macs, np.repeat(idx, nK), cnn.MACS)
        thr = p["cell_tau"] if p["cell_nn"] else p["z0"]
        if "diag" in st:                                      # the true (nearest) cell, if scored in this round
            D = st["diag"]
            tc = np.abs(g[None] - st["truth"][idx][:, None]).argmin(1)
            hit = cells == tc[:, None]
            for j, kk in zip(*np.where(hit)):
                i = idx[j]
                D["z"][i], D["rnd"][i] = z[j, kk], rnd
                D["zrank"][i] = int((z[j] > z[j, kk]).sum())
                D["Mrank"][i] = int((Mb[j] < Mb[j, kk]).sum())
        top = np.argsort(-z, 1)[:, :2]
        for j, kk in zip(*np.where(np.take_along_axis(z, top, 1) > thr)):
            kk = top[j, kk]
            i, cc = idx[j], cells[j, kk]
            if cc not in tried[i]:
                tried[i].add(cc)
                cand.append((i, g[cc], thc[j, kk]))
        if cand:
            _refine2(cand, roffs, sub, p["T"], r, score, decode, passed)
    cand = []
    for i in np.where(~passed)[0]:
        for m, cc, tt in zip(bestM[i], bestC[i], bestT[i]):
            if np.isfinite(m) and cc not in tried[i]:
                tried[i].add(cc)
                cand.append((i, g[cc], tt))
    if cand:
        _refine2(cand, roffs, sub, p["T"], r, score, decode, passed)
    if p["final_post"]:          # still no pass: the top posterior cells, both pi/2 branches, decoded with CA-SCL
        cand = []
        for i in np.where(~passed)[0]:
            cs = [cc for cc in order[i, :p["final_post"]] if cc not in tried[i]]
            if cs:
                tried[i].update(cs)
                t0 = bc.phase4(r[i:i + 1], g[cs][None])[0]
                macs[i] += vp.MAC["phase4"] * len(cs)
                cand += [(i, g[cc], t) for cc, t in zip(cs, t0)] + [(i, g[cc], t + np.pi / 2) for cc, t in zip(cs, t0)]
        if cand:
            in_post[0] = True
            _refine2(cand, roffs, sub, p["T"], r, score, decode, passed)
            st["post_final_rescued"] = st.get("post_final_rescued", 0) + int(passed[[c[0] for c in cand]].sum())
    if p["fine_last"]:           # still no pass: the best-metric cells again (tried or not) on a finer grid, more decodes
        cand = [(i, g[cc], tt) for i in np.where(~passed)[0]
                for m, cc, tt in list(zip(bestM[i], bestC[i], bestT[i]))[:p["fine_last"]] if np.isfinite(m)]
        if cand:
            fine = np.arange(-k, k + 1) * 0.5                 # half-STEP offsets over the cell and its edges
            subf = tuple(np.arange(-2, 3) * np.pi / 16)
            n0 = int((~passed).sum())
            _refine2(cand, fine, subf, p["T_fine"], r, score, decode, passed)
            st["fine_rescued"] = st.get("fine_rescued", 0) + n0 - int((~passed).sum())
    if "diag" in st:
        tc = np.abs(g[None] - st["truth"][:, None]).argmin(1)
        st["diag"]["tried"][:] = [tc[i] in tried[i] for i in range(B)]
        st["diag"]["tried_nb"][:] = [any(abs(c - tc[i]) <= 1 for c in tried[i]) for i in range(B)]
    st["macs"] = st.get("macs", 0.0) + float(macs.sum())
    if "macs_pp" in st:                                       # per-packet MACs (profiling)
        st["macs_pp"].append(macs.copy())
    return out, passed, f_fin, f_top


def pilot_coherent(code, r, data, fh, zp, pos):
    """Coherent pilot sum at the code-aided phase of the re-encoded packet (CFO fh): ~K for the right packet."""
    cw = code.encode(data)[:, bc.INTERLEAVER]
    s = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    th = np.angle(np.sum(r * np.conj(s) * np.exp(-2j * np.pi * fh[:, None] * bc.NC[None]), 1))
    nc = np.asarray(pos, float) - bc.CENTRE
    return np.real(np.sum(zp * np.exp(-1j * (2 * np.pi * fh[:, None] * nc[None] + th[:, None])), 1))


def code_aided(r, fh, cw, newton=2):
    """Code-aided CFO / centre phase from the SC hard-decision codeword cw (H, N_BITS, de-interleaved order) at CFO
    fh: z = r s*, Newton steps on |sum z e^{-j 2 pi f nc}| (as bc.dd_refine without its scan), phase of the sum."""
    c = cw[:, bc.INTERLEAVER]
    s = ((1 - 2.0 * c[:, 0::2]) + 1j * (1 - 2.0 * c[:, 1::2])) / np.sqrt(2)
    z = r * np.conj(s)
    if newton:
        nu, A = bc._newton_tone(z, fh[:, None], newton)
        return nu[:, 0], np.angle(A[:, 0])
    return fh, np.angle(np.sum(z * np.exp(-2j * np.pi * fh[:, None] * bc.NC[None]), 1))


CA_MACS = lambda newton: 4 * bc.N_SYM + newton * 20 * bc.N_SYM + 8 * bc.N_SYM   # z, Newton sums, final sum


def _left_macs(A):
    """Real ops of the left-half partial metric (one f-step over N + the left sub-tree)."""
    def walk(q, n):
        if q[0] == "N":
            return 2 * n + walk(q[1], n // 2) + walk(q[2], n // 2)
        return 2 * n if q[0] in ("REP", "SPC") else n
    plan = fast_sc(A).plan
    return bc.N_BITS + (walk(plan[1], bc.N_BITS // 2) if plan[0] == "N" else 0)


# =====================================================================
# E3: reliability-weighted metric (per Fast-SSC node). Under the right CFO a reliable frozen node's penalty is small,
# an unreliable one's is ~log 2 either way (noise only). The optimal linear test weights each node by its
# discrimination: LDA w = (Sigma + lambda I)^-1 (mu_wrong - mu_true) (full) or (mu_wrong - mu_true) / var (diagonal).
# =====================================================================

E3_OFFSETS = (0.0, 1.0, 2.0, 3.0, 4.0)
_W = None


def node_weights(rate, snr, kind="h0full"):
    """Learned node weights (float32) at the nearest trained SNR, or None when no weights file exists."""
    global _W
    if _W is None:
        p = bc.path("models", "fast_node_weights.json")
        _W = json.load(open(p)) if os.path.exists(p) else {}
    if rate not in _W:
        return None
    snrs = np.array([float(s) for s in _W[rate]])
    s = list(_W[rate])[int(np.abs(snrs - snr).argmin())]
    return np.array(_W[rate][s][kind], np.float32)


def _e3_feats(fast, r, F, TH, sigma2, nph=4):
    """Node penalties (n, H, nodes) of hypotheses (n, H), best of nph phases by the plain metric."""
    n, H = F.shape
    rows = np.repeat(np.arange(n), H)
    best, bestM = None, None
    for q in range(nph):
        P = fast.metric_nodes(bc.llrs(r[rows], F.ravel(), TH.ravel() + q * np.pi / 4 * (2 if nph == 2 else 1),
                                      sigma2))
        M = P.sum(1)
        if best is None:
            best, bestM = P, M
        else:
            sel = M < bestM
            best[sel], bestM[sel] = P[sel], M[sel]
    return best.reshape(n, H, -1)


def _e3_work(task):
    rate, snr, seed, n = task
    from polar import PolarCode
    A = bc.CODES[rate]
    code = PolarCode(bc.N_BITS, A, 16, 8)
    fast = fast_sc(A)
    rng = np.random.default_rng(seed)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    T, W = [], []
    B = 20
    for _ in range(n // B):
        _, _, r, _, f, _ = bc.frames(B, code, snr, rng)
        Ft = f[:, None] + np.array(E3_OFFSETS)[None] * bc.STEP * rng.choice([-1, 1], (B, len(E3_OFFSETS)))
        Fw = f[:, None] + rng.uniform(20, 600, (B, 48)) * GSTEP * rng.choice([-1, 1], (B, 48))
        T.append(_e3_feats(fast, r, Ft, bc.phase4(r, Ft), sigma2))
        W.append(_e3_feats(fast, r, Fw, bc.phase4(r, Fw), sigma2))
    return rate, snr, np.concatenate(T), np.concatenate(W)


def _train_mlp(Xt, Xw, epochs=300):
    """Small MLP (nodes -> 64 -> 64 -> 1) on log node penalties, logistic loss, true vs wrong (balanced). Returns a
    scorer X (..., nodes) -> metric (lower = more likely true), like the path metric."""
    import torch
    torch.manual_seed(0)
    X = np.log(np.concatenate([Xt, Xw]) + 1e-3)
    y = np.concatenate([np.ones(len(Xt)), np.zeros(len(Xw))])
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Xn = torch.tensor((X - mu) / sd, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32)
    wpos = torch.tensor(len(Xw) / len(Xt))
    net = torch.nn.Sequential(torch.nn.Linear(X.shape[1], 64), torch.nn.GELU(), torch.nn.Linear(64, 64),
                              torch.nn.GELU(), torch.nn.Linear(64, 1))
    opt = torch.optim.Adam(net.parameters(), lr=2e-3, weight_decay=1e-5)
    for _ in range(epochs):
        perm = torch.randperm(len(Xn))
        for a in range(0, len(Xn), 4096):
            i = perm[a:a + 4096]
            loss = torch.nn.functional.binary_cross_entropy_with_logits(net(Xn[i])[:, 0], yt[i], pos_weight=wpos)
            opt.zero_grad()
            loss.backward()
            opt.step()

    def score(Z):
        sh = Z.shape[:-1]
        z = torch.tensor((np.log(Z.reshape(-1, Z.shape[-1]) + 1e-3) - mu) / sd, dtype=torch.float32)
        with torch.no_grad():
            return -net(z)[:, 0].numpy().reshape(sh)
    return score


def _zs(Mt, Mw):
    med = np.median(Mw, 1)
    mad = 1.4826 * np.median(np.abs(Mw - med[:, None]), 1) + 1e-9
    return (med[:, None] - Mt) / mad[:, None], (med[:, None] - Mw) / mad[:, None]


def run_e3(rates_snrs, part, workers, n, chunks):
    tasks = [(rt, s, 6100 + 17 * i + int(10 * s + 100), n) for rt, s in rates_snrs for i in range(chunks)]
    acc = {}
    with mp.Pool(workers) as pool:
        for i, (rate, snr, T, W) in enumerate(pool.imap_unordered(_e3_work, tasks), 1):
            a = acc.setdefault((rate, snr), ([], []))
            a[0].append(T)
            a[1].append(W)
            with open(bc.path("logs", f"fast_e3_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} 0\n")
    weights, res = {}, []
    for (rate, snr), (T, W) in sorted(acc.items()):
        T, W = np.concatenate(T), np.concatenate(W)               # (frames, offsets, nodes), (frames, 48, nodes)
        h = len(T) // 2                                           # train on the first half, test on the second
        Xt = T[:h, :3].reshape(-1, T.shape[2])                    # true: offsets 0..2 (inside a grid cell)
        Xw = W[:h].reshape(-1, W.shape[2])
        d = Xw.mean(0) - Xt.mean(0)
        var = 0.5 * (Xt.var(0) + Xw.var(0)) + 1e-6
        w_diag = d / var
        S = 0.5 * (np.cov(Xt.T) + np.cov(Xw.T))
        w_full = np.linalg.solve(S + 1e-3 * np.trace(S) / len(S) * np.eye(len(S)), d)
        # the detector's own objective: separation in units of the WRONG hypotheses' spread (robust z)
        w_h0diag = d / (Xw.var(0) + 1e-6)
        Sw = np.cov(Xw.T)
        w_h0full = np.linalg.solve(Sw + 1e-3 * np.trace(Sw) / len(Sw) * np.eye(len(Sw)), d)
        for w in (w_diag, w_full, w_h0diag, w_h0full):
            w *= len(w) / np.abs(w).sum()
        weights.setdefault(rate, {})[str(snr)] = {k: [float(x) for x in v] for k, v in (
            ("diag", w_diag), ("full", w_full), ("h0diag", w_h0diag), ("h0full", w_h0full))}
        mlp = _train_mlp(Xt, Xw)
        row = {"rate": rate, "snr": snr, "frames_test": len(T) - h, "nodes": int(T.shape[2])}
        for name, w in (("plain", np.ones(T.shape[2])), ("diag", w_diag), ("full", w_full), ("h0diag", w_h0diag),
                        ("h0full", w_h0full), ("mlp", None)):
            if w is None:
                zt, zw = _zs(mlp(T[h:]), mlp(W[h:]))
            else:
                zt, zw = _zs(T[h:] @ w, W[h:] @ w)
            row[name] = {"z_wrong_9999": float(np.quantile(zw, 0.9999)),
                         **{f"off{o}": {"z50": float(np.median(zt[:, j])), "z1": float(np.quantile(zt[:, j], 0.01)),
                                        "P_lt4": float(np.mean(zt[:, j] < 4))} for j, o in enumerate(E3_OFFSETS)}}
        res.append(row)
        print(f"{rate} {snr:5.1f} " + " | ".join(
            f"{nm}: wrong99.99 {row[nm]['z_wrong_9999']:.1f} " + " ".join(
                f"o{int(o)} z50 {row[nm][f'off{o}']['z50']:.1f} P<4 {row[nm][f'off{o}']['P_lt4']:.3f}"
                for o in (0.0, 2.0, 3.0, 4.0)) for nm in ("plain", "diag", "full", "h0diag", "h0full", "mlp")), flush=True)
    json.dump(weights, open(bc.path("models", "fast_node_weights.json"), "w"))
    json.dump(res, open(bc.path("results", f"fast_e3_{part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


E3_SNRS = {"1/10": (-5.0, -4.0, -3.0, -2.0, -1.0, 0.0), "1/4": (0.0, 1.0, 2.0, 3.0), "1/2": (2.0, 3.0, 4.0)}


# =====================================================================
# E1: coarse ranks
# =====================================================================

E1_SNRS = (-6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0)
E1_VARIANTS = {"spectral": dict(w4=0.0), "4th power": None, "spectral + 4th (w=1/3)": dict(w4=1 / 3),
               "spectral + 4th (w=1/10)": dict(w4=0.1), "spectral + 4th (w=1)": dict(w4=1.0),
               "cyclic": "cyc", "spectral + cyclic + 4th": dict(w4=1 / 3, wc=1.0),
               "spectral + cyclic(2) + 4th": dict(w4=1 / 3, wc=2.0)}
RANK_K = (1, 3, 10, 30, 100, 300, 1000)


def _e1_work(task):
    snr, seed, n = task
    from polar import PolarCode
    code = PolarCode(bc.N_BITS, 205, 16, 8)
    rng = np.random.default_rng(seed)
    out = {k: [] for k in E1_VARIANTS}
    out["cyclic phase"] = []
    se = {"spectral": 0.0, "cyclic": 0.0}
    for _ in range(n // 100):
        _, _, r, rx, f, _ = bc.frames(100, code, snr, rng)
        S4, fs, Cg = coarse_features(r, rx)
        true = np.abs(GRID[None] - f[:, None]).argmin(1)
        rows = np.arange(len(f))
        # the cyclic statistic's phase at the true CFO (calibrates phi) and its own argmax estimate
        out["cyclic phase"] += list(np.angle(Cg[rows, true]))
        fc = GRID[np.abs(Cg).argmax(1)]
        se["spectral"] += float(np.sum((fs - f) ** 2))
        se["cyclic"] += float(np.sum((fc - f) ** 2))
        for k, v in E1_VARIANTS.items():
            if v is None:
                sc = S4
            elif v == "cyc":
                sc = np.abs(Cg)
            else:
                sc = posterior(S4, fs, Cg, snr, phi=_PHI, **v)
            out[k] += list((sc > sc[rows, true][:, None]).sum(1).astype(int))
    return snr, out, se, n


_PHI = 0.0


def run_e1(part, workers, n, chunks):
    tasks = [(s, 9000 + 100 * i + int(10 * s + 100), n) for s in E1_SNRS for i in range(chunks)]
    acc = {}
    with mp.Pool(workers) as pool:
        for i, (snr, out, se, m) in enumerate(pool.imap_unordered(_e1_work, tasks), 1):
            a = acc.setdefault(snr, {"n": 0, "ranks": {k: [] for k in out}, "se": {k: 0.0 for k in se}})
            a["n"] += m
            for k, v in out.items():
                a["ranks"][k] += [float(x) for x in v]
            for k, v in se.items():
                a["se"][k] += v
            with open(bc.path("logs", f"fast_e1_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} 0\n")
    res = []
    for snr in sorted(acc):
        a = acc[snr]
        row = {"snr": snr, "n": a["n"], "rmse": {k: float(np.sqrt(v / a["n"])) for k, v in a["se"].items()},
               "cyclic_phase_mean": float(np.angle(np.mean(np.exp(1j * np.array(a["ranks"]["cyclic phase"]))))),
               "cyclic_phase_R": float(np.abs(np.mean(np.exp(1j * np.array(a["ranks"]["cyclic phase"])))))}
        for k, v in a["ranks"].items():
            if k == "cyclic phase":
                continue
            v = np.array(v)
            row[k] = {"mean": float(v.mean()), "median": float(np.median(v)),
                      "P_gt": {str(K): float(np.mean(v >= K)) for K in RANK_K}}
        res.append(row)
        print(f"{snr:5.1f} dB  rmse spectral {row['rmse']['spectral']:.2e} cyclic {row['rmse']['cyclic']:.2e}  "
              f"cyc phase {row['cyclic_phase_mean']:+.2f} (R {row['cyclic_phase_R']:.2f}) | "
              + " | ".join(f"{k}: {row[k]['mean']:.1f}" for k in E1_VARIANTS), flush=True)
    json.dump(res, open(bc.path("results", f"fast_e1_{part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


# =====================================================================
# E2: metric separation
# =====================================================================

E2_METRICS = ("SC (CA-SCL list 1)", "Fast-SSC min-sum", "Fast-SSC exact", "Fast-SSC left 1/2", "Fast-SSC left 1/4")
E2_OFFSETS = (0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0)                   # in STEP: 2 = the worst case of the 4-step grid
E2_WRONG = 64                                                     # far-off (wrong) CFO hypotheses per frame


def _metric_fn(name, A):
    if name == "SC (CA-SCL list 1)":
        c = bc.sc_code(A)
        return lambda llr: bc.sc_metric(llr, c)
    if "left" in name:
        fs = fast_sc(A)
        d = 1 if name.endswith("1/2") else 2
        return lambda llr: fs.metric_left(llr, d)
    return fast_sc(A, exact=name.endswith("exact")).metric


def _e2_work(task):
    rate, snr, seed, n = task
    from polar import PolarCode
    A = bc.CODES[rate]
    code = PolarCode(bc.N_BITS, A, 16, 8)
    rng = np.random.default_rng(seed)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    fns = {m: _metric_fn(m, A) for m in E2_METRICS}
    out = {m: {"true": {str(o): [] for o in E2_OFFSETS}, "wrong": [], "time": 0.0, "evals": 0} for m in E2_METRICS}
    B = 25
    for _ in range(n // B):
        _, _, r, _, f, th = bc.frames(B, code, snr, rng)
        rows_t, F, TH = [], [], []
        for o in E2_OFFSETS:                                       # true CFO + offset, the 4th-power phase there
            fo = f + o * bc.STEP * rng.choice([-1, 1], B)
            F.append(fo)
            TH.append(bc.phase4(r, fo))
        fw = f[:, None] + rng.uniform(20, 600, (B, E2_WRONG)) * GSTEP * rng.choice([-1, 1], (B, E2_WRONG))
        thw = bc.phase4(r, fw)
        Fall = np.concatenate([np.stack(F, 1), fw], 1)
        THall = np.concatenate([np.stack(TH, 1), thw], 1)
        H = Fall.shape[1]
        rr = np.repeat(np.arange(B), H)
        # both phase hypotheses (0, pi/2): the metric of a cell is the better one
        best = {}
        for m, fn in fns.items():
            Ms = []
            t0 = time.perf_counter()
            for q in (0, 1):
                llr = bc.llrs(r[rr], Fall.ravel(), THall.ravel() + q * np.pi / 2, sigma2)
                Ms.append(fn(llr).reshape(B, H))
            out[m]["time"] += time.perf_counter() - t0
            out[m]["evals"] += 2 * B * H
            M = np.minimum(*Ms)
            for i, o in enumerate(E2_OFFSETS):
                out[m]["true"][str(o)] += list(M[:, i].astype(float))
            out[m]["wrong"] += [list(row) for row in M[:, len(E2_OFFSETS):].astype(float)]
    return rate, snr, out, n


def run_e2(rates, snrs, part, workers, n, chunks):
    tasks = [(rt, s, 7000 + 13 * i + int(10 * s + 100), n) for rt in rates for s in snrs for i in range(chunks)]
    acc = {}
    with mp.Pool(workers) as pool:
        for i, (rate, snr, out, m) in enumerate(pool.imap_unordered(_e2_work, tasks), 1):
            a = acc.setdefault((rate, snr), {k: {"true": {o: [] for o in v["true"]}, "wrong": [], "time": 0.0,
                                                 "evals": 0} for k, v in out.items()})
            for k, v in out.items():
                for o, x in v["true"].items():
                    a[k]["true"][o] += x
                a[k]["wrong"] += v["wrong"]
                a[k]["time"] += v["time"]
                a[k]["evals"] += v["evals"]
            with open(bc.path("logs", f"fast_e2_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} 0\n")
    res = []
    for (rate, snr), a in sorted(acc.items()):
        for k, v in a.items():
            W = np.array(v["wrong"])                                # (frames, E2_WRONG)
            med = np.median(W, 1)
            mad = 1.4826 * np.median(np.abs(W - med[:, None]), 1)
            zw = (med[:, None] - W) / mad[:, None]                  # z of the wrong cells (higher = more likely)
            row = {"rate": rate, "snr": snr, "metric": k, "frames": len(W), "time_per_eval": v["time"] / v["evals"],
                   "z_wrong_q": {str(q): float(np.quantile(zw, q)) for q in (0.5, 0.99, 0.999, 0.9999)},
                   "z_wrong_max_mean": float(zw.max(1).mean())}
            for o, x in v["true"].items():
                zt = (med - np.array(x)) / mad
                row[f"off{o}"] = {"z_median": float(np.median(zt)), "z_q01": float(np.quantile(zt, 0.01)),
                                  "z_q001": float(np.quantile(zt, 0.001)),
                                  "auc": float(np.mean(np.array(x)[:, None] < W)),
                                  "P_best_of_64": float(np.mean(np.array(x) < W.min(1))),
                                  "P_z": {str(z): float(np.mean(zt > z)) for z in (3, 4, 5, 6, 8)}}
            res.append(row)
            print(f"{rate} {snr:5.1f} {k:20s} {1e6 * row['time_per_eval']:7.1f} us/eval  wrong z99.99 "
                  f"{row['z_wrong_q']['0.9999']:5.2f}  " + "  ".join(
                      f"off{o}: z {row[f'off{o}']['z_median']:5.1f} auc {row[f'off{o}']['auc']:.4f}"
                      for o in ("0.0", "2.0", "4.0")), flush=True)
    json.dump(res, open(bc.path("results", f"fast_e2_{part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


def bench():
    from polar import PolarCode
    rng = np.random.default_rng(1)
    for rate in ("1/10", "1/4", "1/2"):
        A = bc.CODES[rate]
        code = PolarCode(bc.N_BITS, A, 16, 8)
        _, _, r, _, f, th = bc.frames(64, code, 0.0, rng)
        llr = bc.llrs(np.repeat(r, 16, 0), np.repeat(f, 16), np.repeat(th, 16), 1.0)
        for m in E2_METRICS:
            fn = _metric_fn(m, A)
            fn(llr[:64])
            t0 = time.perf_counter()
            M = fn(llr)
            dt = (time.perf_counter() - t0) / len(llr)
            print(f"{rate} {m:22s} {1e6 * dt:7.1f} us/hypothesis  mean metric {M.mean():.1f}")
        p = fast_sc(A).plan
        cnt = {}

        def walk(q):
            cnt[q[0]] = cnt.get(q[0], 0) + 1
            if q[0] == "N":
                walk(q[1]), walk(q[2])
        walk(p)
        print("   nodes", cnt)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["bench", "coarse", "metric", "weights"])
    ap.add_argument("--part", default="a")
    ap.add_argument("--rates", nargs="+", default=["1/10"])
    ap.add_argument("--snrs", type=float, nargs="+", default=[-5.0, -3.0, 0.0])
    ap.add_argument("--frames", type=int, default=2000, help="per chunk")
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--phi", type=float, default=0.0, help="cyclic statistic phase (from a calibration run)")
    a = ap.parse_args()
    _PHI = a.phi
    if a.what == "bench":
        bench()
    elif a.what == "coarse":
        run_e1(a.part, a.workers, a.frames, a.chunks)
    elif a.what == "weights":
        run_e3([(rt, s) for rt in a.rates for s in E3_SNRS[rt]], a.part, a.workers, a.frames, a.chunks)
    else:
        run_e2(a.rates, a.snrs, a.part, a.workers, a.frames, a.chunks)
