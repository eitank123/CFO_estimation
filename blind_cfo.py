"""
Blind CFO estimation (no pilots) for the 1024-symbol polar-coded packet, full Tx/Rx chain: library + tests.

Without pilots the receiver knows neither the CFO (U[-0.2, 0.2] cycles/symbol) nor the carrier phase; QPSK leaves a
4-fold phase ambiguity (rotations q pi/2) that only the code / CRC can resolve. Pieces (README "Blind CFO"):

  coarse, no decoding
    fourth_power   peaks of |FFT(-r^4)| (the modulation removed: a tone at 4f), Newton-refined; 4f is known mod 1, so
                   f mod 1/4; the phase at the packet centre theta_c = angle / 4 (mod pi/2)
    spectral       band-edge / spectral-template estimator on the 8x-oversampled samples BEFORE the matched filter:
                   argmax of the correlation of the periodogram with the raised-cosine |H|^2; coarse, but it resolves
                   the 1/4 ambiguity of the 4th power
    (blind_nn.py   an NN posterior over the 4th-power bins, used to rank the peaks)
  decoder metrics, per hypothesis (f, theta)
    sc_metric      path metric of a plain SC decode (list 1) with the frozen bits forced to 0
    syndrome_hard  number of frozen u-bits = 1 after the polar transform of the hard decisions (u = x G, G G = I)
    syndrome_soft  -sum log P(check satisfied) over the frozen parity checks of weight <= W (u_i = XOR_{j >= i} x_j)
  sub-codes        x[N - M:] = u[N - M:] G_M is itself a polar codeword (only without the interleaver)
  decision-directed re-estimation over all 1024 symbols (dd_refine), used after a CRC pass and for turbo iterations

Tests (cluster jobs; results in blind/logs, figures in "Blind CFO estimation/"):
    python blind_cfo.py coarse  --snrs -5 -4 ... --part a      # T1: coarse estimators (MSE, outage, peak inclusion)
    python blind_cfo.py metric  --rate 1/4 --snrs 0 2 --part a  # T2: metric vs CFO / phase error, ranking
    python blind_cfo.py subcode --rate 1/4 --snrs 2 --part a    # T3: sub-code metric capture width (no interleaver)
    python blind_cfo.py plot                                    # all test figures
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import time

import numpy as np

import config as cfg
from polar import PolarCode, polar_transform

ROOT = os.path.dirname(os.path.abspath(__file__))
# a study (environment variable BLIND_STUDY) has its own CFO range and keeps all its results / logs / models / figures
# in its own folder; trained models fall back to the main blind/models
STUDIES = {"small_cfo": {"max_cfo": 0.03, "folder": "small_cfo"}}
STUDY = os.environ.get("BLIND_STUDY", "")
MAIN_DATA = os.path.join(ROOT, "blind")
if STUDY:
    DATA = os.path.join(ROOT, STUDIES[STUDY]["folder"], "blind")
    PLOTS = os.path.join(ROOT, STUDIES[STUDY]["folder"], "Blind CFO estimation")
else:
    DATA = MAIN_DATA                                       # results / logs / models (synced from the cluster)
    PLOTS = os.path.join(ROOT, "Blind CFO estimation")     # every blind figure
N_SYM, N_BITS = 1024, 2048
MAX_CFO = STUDIES[STUDY]["max_cfo"] if STUDY else cfg.MAX_CFO
SPS, SPAN = cfg.SPS, cfg.FILTER_SPAN
DELAY_SYM = SPAN / 2
CENTRE = (N_SYM - 1) / 2
NC = np.arange(N_SYM) - CENTRE                             # centred symbol index
STEP = 1.5e-4 * 512 / N_SYM                                # CFO grid step = the pilot receivers' search step (7.5e-5)
NFFT4 = 4096                                               # 4th-power FFT: 4x zero padding of the 1024 symbols
NFFT_S = 16384                                             # spectral estimator FFT (8192 + 80 samples, 2x padding)
TOL = 1.0e-4
CODES = {"1/10": 205, "1/4": 512, "1/3": 683, "2/5": 819, "1/2": 1024, "3/5": 1229, "2/3": 1365, "3/4": 1536}   # data bits A, CRC-16, N = 2048 (as polar_ber_experiment)
INTERLEAVER = np.random.default_rng(12345).permutation(N_BITS)  # the same fixed interleaver as polar_ber_experiment


def path(kind, name):
    d = os.path.join(DATA, kind) if kind in ("results", "logs", "models") else os.path.join(PLOTS, kind)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    if kind == "models" and STUDY and not os.path.exists(p) and os.path.exists(os.path.join(MAIN_DATA, kind, name)):
        return os.path.join(MAIN_DATA, kind, name)        # a study reads the main trained models until it has its own
    return p


# =====================================================================
# Transmitter (full chain, also returning the pre-matched-filter samples)
# =====================================================================

def transmit_full(sym, f, phase, snr_db, rng, beta=cfg.BETA, noise_only=False):
    """txrx_chain.transmit, also returning the noisy 8x-oversampled samples before the matched filter. noise_only:
    the noise of the same SNR, without the signal (false-alarm tests)."""
    from scipy.signal import fftconvolve
    from txrx_chain import rrc
    B, K = sym.shape
    h = rrc(beta)
    up = np.zeros((B, K * SPS), complex)
    up[:, ::SPS] = sym
    tx = fftconvolve(up, h[None], axes=1)
    m = np.arange(tx.shape[1])
    rx = tx * np.exp(1j * (2 * np.pi * np.asarray(f, float).reshape(-1, 1) * m / SPS
                           + np.asarray(phase, float).reshape(-1, 1)))
    es = np.sum(np.abs(tx) ** 2, axis=1, keepdims=True) / K
    sigma = np.sqrt(es / (10 ** (np.asarray(snr_db, float).reshape(-1, 1) / 10)) / 2)
    if noise_only:
        rx = np.zeros_like(rx)
    rx = rx + sigma * (rng.standard_normal(rx.shape) + 1j * rng.standard_normal(rx.shape))
    D = SPAN * SPS
    return fftconvolve(rx, h[None], axes=1)[:, D:D + K * SPS:SPS], rx


def frames(B, code, snr_db, rng, interleave=True, noise_only=False):
    """B random coded packets through the chain: data, codeword (Tx order), r, pre-MF samples, f, centre phase."""
    data = rng.integers(0, 2, (B, code.A), dtype=np.uint8)
    cw = code.encode(data)
    if interleave:
        cw = cw[:, INTERLEAVER]
    sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    f = rng.uniform(-MAX_CFO, MAX_CFO, B)
    ph = rng.uniform(0, 2 * np.pi, B)
    r, rx = transmit_full(sym, f, ph, snr_db, rng, noise_only=noise_only)
    theta = ph + 2 * np.pi * f * (CENTRE + DELAY_SYM)       # carrier phase at the packet centre
    return data, cw, r, rx, f, theta


# =====================================================================
# Coarse blind estimators
# =====================================================================

def _newton_tone(y, nu, iters=3):
    """Newton steps on |A(nu)|^2, A(nu) = sum_n y[n] exp(-j 2 pi nu nc[n]); y (B, N), nu (B, P). Returns nu, A."""
    w = -2j * np.pi * NC
    for _ in range(iters):
        e = np.exp(np.einsum("bp,n->bpn", -2j * np.pi * nu, NC))
        A = np.einsum("bn,bpn->bp", y, e)
        A1 = np.einsum("bn,bpn->bp", y * w, e)
        A2 = np.einsum("bn,bpn->bp", y * w ** 2, e)
        g = 2 * (A1 * A.conj()).real
        h = 2 * ((A2 * A.conj()).real + np.abs(A1) ** 2)
        step = np.where(h < 0, -g / np.where(h < 0, h, -1.0), 0.0)
        nu = nu + np.clip(step, -1.0 / N_SYM, 1.0 / N_SYM)
    e = np.exp(np.einsum("bp,n->bpn", -2j * np.pi * nu, NC))
    return nu, np.einsum("bn,bpn->bp", y, e)


def top_peaks(score, P, radius):
    """Indices (B, P) of the P largest local maxima of score (B, M), circular, each suppressing +-radius bins."""
    s = score.copy()
    M = s.shape[1]
    out = np.empty((len(s), P), int)
    rows = np.arange(len(s))
    for p in range(P):
        k = s.argmax(1)
        out[:, p] = k
        for d in range(-radius, radius + 1):
            s[rows, (k + d) % M] = -np.inf
    return out


def fourth_power(r, P=1, bins=None):
    """Blind 4th-power estimator. r (B, N). Returns nu = 4f mod 1 in [-0.5, 0.5) (B, P) and the peak heights
    |A| / N (B, P), peaks ordered by height (or the given bins (B, P) of an NFFT4 grid, e.g. from the NN posterior).
    The phase comes from phase4 at the resolved CFO."""
    y = -(r ** 4)
    if bins is None:
        bins = top_peaks(np.abs(np.fft.fft(y, NFFT4)), P, radius=NFFT4 // N_SYM * 2)
    nu0 = np.fft.fftfreq(NFFT4)[bins]
    nu, A = _newton_tone(y, nu0)
    nu = (nu + 0.5) % 1.0 - 0.5
    h = np.abs(A) / N_SYM
    order = np.argsort(-h, 1)
    return np.take_along_axis(nu, order, 1), np.take_along_axis(h, order, 1)


def phase4(r, f):
    """Carrier phase at the packet centre (mod pi/2) from the 4th power at CFO f (B,) or (B, P):
    -r^4 = g^4 exp(j (2 pi 4f nc + 4 theta_c)). Computed at 4f itself, not 4f mod 1: the centre nc is a half
    integer, so a wrap of 4f by an odd integer would flip the sign of the sum."""
    f2 = f if f.ndim == 2 else f[:, None]
    A = np.einsum("bn,bpn->bp", -(r ** 4), np.exp(np.einsum("bp,n->bpn", -2j * np.pi * 4 * f2, NC)))
    th = np.angle(A) / 4
    return th if f.ndim == 2 else th[:, 0]


_tmpl = None


def spectral(rx):
    """Spectral-template (band-edge) CFO estimate (B,) cycles/symbol from the pre-MF samples rx (B, M): argmax over
    shifts of sum_F P(F) |H(F - shift)|^2 (circular correlation by FFT), parabolic interpolation."""
    global _tmpl
    from txrx_chain import rrc
    if _tmpl is None:
        _tmpl = np.conj(np.fft.fft(np.abs(np.fft.fft(rrc(cfg.BETA), NFFT_S)) ** 2))
    Pw = np.abs(np.fft.fft(rx, NFFT_S, axis=1)) ** 2
    C = np.fft.ifft(np.fft.fft(Pw, axis=1) * _tmpl, axis=1).real
    k = np.fft.fftfreq(NFFT_S) * NFFT_S
    i = np.where(np.abs(k) / NFFT_S * SPS > MAX_CFO + 0.01, -np.inf, C).argmax(1)
    rows = np.arange(len(C))
    c0, cm, cp = C[rows, i], C[rows, (i - 1) % NFFT_S], C[rows, (i + 1) % NFFT_S]
    den = cm - 2 * c0 + cp
    d = np.clip(0.5 * (cm - cp) / np.where(den < 0, den, -1e-30), -0.5, 0.5)
    return (k[i] + d) / NFFT_S * SPS


def resolve(nu, f_ref):
    """f = nu / 4 + k / 4 with the k that puts f nearest the reference (spectral) estimate; nu (B, P), f_ref (B,)."""
    k = np.round((f_ref[:, None] - nu / 4) * 4)
    return nu / 4 + k / 4


# =====================================================================
# Decoder metrics
# =====================================================================

def llrs(r, fh, th, sigma2, interleave=True):
    """De-interleaved channel LLRs (B, N_BITS) of r (B, N) de-rotated by CFO fh (B,) and centre phase th (B,)."""
    y = r * np.exp(-1j * (2 * np.pi * fh[:, None] * NC + th[:, None]))
    llr = np.empty((len(r), N_BITS))
    llr[:, 0::2] = np.sqrt(2) * y.real / sigma2
    llr[:, 1::2] = np.sqrt(2) * y.imag / sigma2
    if not interleave:
        return llr
    out = np.empty_like(llr)
    out[:, INTERLEAVER] = llr
    return out


_sc = {}


def sc_code(A, crc=16):
    if (A, crc) not in _sc:
        _sc[(A, crc)] = PolarCode(N_BITS, A, crc, list_size=1)
    return _sc[(A, crc)]


def sc_metric(llr, code):
    """SC path metric (list 1, frozen bits = 0): sum of the bit penalties log(1 + exp(-+L)) along the SC path."""
    return code.decode(llr, return_info=True)[2].astype(float)


def syndrome_hard(llr, frozen):
    """Unsatisfied frozen checks of the hard decisions: popcount of (x_hat G)[frozen] (G is its own inverse)."""
    return polar_transform((llr < 0).astype(np.uint8))[:, frozen].sum(1).astype(float)


_checks = {}


def checks(frozen, wmax):
    """Frozen parity checks of weight <= wmax: u_i = XOR of x_j over j whose bits contain i's bits, w = 2^(n - |i|)."""
    key = (frozen.tobytes(), wmax)
    if key not in _checks:
        N = len(frozen)
        n = int(np.log2(N))
        groups = {}
        for i in np.where(frozen)[0]:
            w = 2 ** (n - bin(i).count("1"))
            if w <= wmax:
                groups.setdefault(w, []).append([j for j in range(N) if (j & i) == i])
        _checks[key] = [np.array(v) for v in groups.values()]
    return _checks[key]


def syndrome_soft(llr, frozen, wmax=16):
    """-sum log P(check satisfied), P = (1 + prod tanh(L_j / 2)) / 2, over the frozen checks of weight <= wmax."""
    t = np.tanh(np.clip(llr, -30, 30) / 2)
    s = np.zeros(len(llr))
    for idx in checks(frozen, wmax):
        s -= np.log(np.clip((1 + t[:, idx].prod(2)) / 2, 1e-12, None)).sum(1)
    return s


def subcode(A, M, crc=16):
    """The polar sub-code of the last M codeword bits: x[N-M:] = u[N-M:] G_M, frozen = frozen[N-M:] (no CRC)."""
    full = PolarCode(N_BITS, A, crc, list_size=1)
    c = PolarCode(M, 1, 0, list_size=1)
    c.frozen = full.frozen[N_BITS - M:].copy()
    c.info_pos = np.where(~c.frozen)[0]
    c.K = c.A = len(c.info_pos)
    c.C = 0
    c.crc_G = np.zeros((c.A, 0), dtype=np.uint8)
    return c


DD_SCAN = np.arange(-8, 9) * 1.25e-4                       # +-1e-3: a passing decode can be ~5e-4 off (low rate)


def dd_refine(r, data, code, f0, iters=3):
    """Decision-directed CFO / centre phase from all N_SYM symbols re-encoded from data (B, A): the best of a +-1e-3
    scan of |sum z e^(-j 2 pi f nc)| around f0 (B,) (Newton alone converges only within ~2e-4), then Newton."""
    cw = code.encode(data)[:, INTERLEAVER]
    sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    z = r * np.conj(sym)
    cand = f0[:, None] + DD_SCAN[None, :]
    A = np.abs(np.einsum("bn,bkn->bk", z, np.exp(np.einsum("bk,n->bkn", -2j * np.pi * cand, NC))))
    nu, A = _newton_tone(z, cand[np.arange(len(z)), A.argmax(1)][:, None], iters)
    return nu[:, 0], np.angle(A[:, 0])


class PiCode(PolarCode):
    """CA-SCL that also accepts the pi-rotated codeword. A rotation of QPSK by pi complements every coded bit; the
    all-ones word is a polar codeword (u = e_{N-1}, the last, always-information bit), so the complement is decoded
    as the same data with u_{N-1}, the last CRC bit, flipped. A path whose CRC fails ONLY in its last bit is therefore
    the transmitted packet received with a pi phase error: accepted (the data are unchanged). The phase is then
    needed only mod pi: 2 hypotheses instead of 4."""

    def decode(self, llr, return_info=False):
        B, Ls = llr.shape[0], self.list_size
        self._pm = np.full((B, Ls), np.inf, dtype=np.float32)
        self._pm[:, 0] = 0.0
        self._bits, self._parents = [], []
        alpha = np.repeat(llr[:, None, :].astype(np.float32), Ls, axis=1)
        self._rec(alpha, 0, self.N)
        info = np.empty((B, Ls, self.K), dtype=np.uint8)
        path = np.broadcast_to(np.arange(Ls), (B, Ls))
        rows = np.arange(B)[:, None]
        for k in range(self.K - 1, -1, -1):
            info[:, :, k] = self._bits[k][rows, path]
            path = self._parents[k][rows, path]
        data, crc = info[..., :self.A], info[..., self.A:]
        calc = self.crc(data.reshape(-1, self.A)).reshape(B, Ls, self.C)
        flip = np.zeros(self.C, np.uint8)
        flip[-1] = 1
        ok = np.all(calc == crc, axis=2) | np.all(calc == crc ^ flip, axis=2)
        score = np.where(ok, self._pm, np.inf)
        best = np.where(ok.any(1), score.argmin(1), self._pm.argmin(1))
        if return_info:
            return data[np.arange(B), best], ok.any(1), self._pm[np.arange(B), best]
        return data[np.arange(B), best]

    def decode_joint(self, llr_h, Ls):
        """One packet's H hypotheses (H, N) (CFO / phase) in ONE list decode of Ls >= H paths: path h starts on
        hypothesis h's channel LLRs, and the list is pruned over all of them (path metrics of the same received
        samples are comparable: a wrong hypothesis loses its paths to the right one). -> data (A,), CRC passed,
        path metric, the chosen path's hypothesis."""
        H = len(llr_h)
        assert H <= Ls
        L0, self.list_size = self.list_size, Ls
        try:
            self._pm = np.full((1, Ls), np.inf, dtype=np.float32)
            self._pm[0, :H] = 0.0
            self._bits, self._parents = [], []
            alpha = np.repeat(llr_h[:1, None, :].astype(np.float32), Ls, axis=1)
            alpha[0, :H] = llr_h
            self._rec(alpha, 0, self.N)
            info = np.empty((1, Ls, self.K), dtype=np.uint8)
            path = np.arange(Ls)[None]
            for k in range(self.K - 1, -1, -1):
                info[:, :, k] = self._bits[k][0, path]
                path = self._parents[k][0, path]
            data, crc = info[0, :, :self.A], info[0, :, self.A:]
            calc = self.crc(data)
            flip = np.zeros(self.C, np.uint8)
            flip[-1] = 1
            ok = np.all(calc == crc, axis=1) | np.all(calc == crc ^ flip, axis=1)
            pm = self._pm[0]
            best = np.where(ok, pm, np.inf).argmin() if ok.any() else pm.argmin()
            return data[best], bool(ok.any()), pm[best], int(path[0, best])   # path: the starting path = hypothesis
        finally:
            self.list_size = L0


def crb_da(snr_db, L=N_SYM):
    return 3.0 / (2 * np.pi ** 2 * 10 ** (snr_db / 10) * L * (L ** 2 - 1))


# =====================================================================
# T1: coarse estimators
# =====================================================================

PEAKS = (1, 2, 4, 8)
WINDOWS = (STEP / 2, 3.5 * STEP, 8.5 * STEP)               # peak within +-W of f: grid offset 0 / +-3 / +-8 steps


def _coarse_work(task):
    snr, seed, n = task
    rng = np.random.default_rng(seed)
    code = PolarCode(N_BITS, CODES["1/4"], 16, 1)          # the data only feed the chain; any code will do
    nn = None
    try:
        import blind_nn
        nn = blind_nn.load()
    except Exception:
        pass
    est = ["4th power", "spectral", "4th power + spectral"] + (["NN + spectral"] if nn else [])
    acc = {k: np.zeros(4) for k in est}                    # sum e^2, outage, gross (> 1e-3), frames
    inc = {k: np.zeros((len(PEAKS), len(WINDOWS))) for k in (["fft"] + (["nn"] if nn else []))}
    ph_se = 0.0
    for _ in range(n // 250):
        _, _, r, rx, f, th = frames(250, code, snr, rng)
        nu, _ = fourth_power(r, P=max(PEAKS))
        fs = spectral(rx)
        f4 = resolve(nu, fs)
        phs = phase4(r, f4[:, :1])
        out = {"4th power": resolve(nu[:, :1], f)[:, 0],   # the 1/4 ambiguity resolved by the true CFO
               "spectral": fs, "4th power + spectral": f4[:, 0]}
        dq = np.angle(np.exp(1j * 4 * (phs[:, 0] - th))) / 4  # phase error mod pi/2 (at the main peak)
        ph_se += float(np.sum(np.where(np.abs(f4[:, 0] - f) < TOL, dq, 0) ** 2))
        cands = {"fft": f4}
        if nn:
            nun, _ = fourth_power(r, bins=blind_nn.peak_bins(nn, r, snr, max(PEAKS)))
            fn = resolve(nun, fs)
            out["NN + spectral"] = fn[:, 0]
            cands["nn"] = fn
        for k, fh in out.items():
            e = fh - f
            acc[k] += [np.sum(e ** 2), np.sum(np.abs(e) > TOL), np.sum(np.abs(e) > 1e-3), len(e)]
        for k, fc in cands.items():
            d = np.abs(fc - f[:, None])
            for a, P in enumerate(PEAKS):
                for b, W in enumerate(WINDOWS):
                    inc[k][a, b] += np.sum((d[:, :P] <= W).any(1))
    return snr, acc, inc, ph_se


def run_coarse(snrs, part, workers, n):
    tasks = [(s, 500000 + 1000 * (s + 10) + i, n // 16) for s in snrs for i in range(16)]
    res = {}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for i, (s, acc, inc, ph) in enumerate(pool.imap_unordered(_coarse_work, tasks), 1):
            if s not in res:
                res[s] = (acc, inc, [ph])
            else:
                for k in acc:
                    res[s][0][k] += acc[k]
                for k in inc:
                    res[s][1][k] += inc[k]
                res[s][2][0] += ph
            with open(path("logs", f"blind_coarse_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} {time.time() - t0:.0f}\n")
    out = {"snr": snrs, "peaks": PEAKS, "windows": WINDOWS, "est": {}, "inclusion": {}, "phase_rmse": []}
    for s in snrs:
        acc, inc, ph = res[s]
        for k, a in acc.items():
            d = out["est"].setdefault(k, {"mse": [], "outage": [], "gross": [], "n": []})
            d["mse"].append(a[0] / a[3]); d["outage"].append(a[1] / a[3]); d["gross"].append(a[2] / a[3])
            d["n"].append(int(a[3]))
        for k, v in inc.items():
            out["inclusion"].setdefault(k, []).append((v / acc["spectral"][3]).tolist())
        good = acc["4th power + spectral"][3] * (1 - acc["4th power + spectral"][1] / acc["4th power + spectral"][3])
        out["phase_rmse"].append(float(np.sqrt(ph[0] / max(good, 1))))
    json.dump(out, open(path("logs", f"blind_coarse_{part}.json"), "w"), indent=1)
    for k, d in out["est"].items():
        print(f"{k:22s} MSE " + " ".join(f"{v:.1e}" for v in d["mse"]) + " | outage "
              + " ".join(f"{v:.3f}" for v in d["outage"]), flush=True)
    print("EVAL DONE", flush=True)


# =====================================================================
# T2: decoder metrics vs CFO / phase error
# =====================================================================

OFFSETS = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)       # CFO error in grid steps (x STEP)
METRICS = ("SC", "syndrome hard", "syndrome soft w<=16", "syndrome soft w<=32")


def _metrics(llr, code):
    return {"SC": sc_metric(llr, code), "syndrome hard": syndrome_hard(llr, code.frozen),
            "syndrome soft w<=16": syndrome_soft(llr, code.frozen, 16),
            "syndrome soft w<=32": syndrome_soft(llr, code.frozen, 32)}


def _metric_work(task):
    rate, snr, seed, n, G = task
    rng = np.random.default_rng(seed)
    A = CODES[rate]
    code, sc = PolarCode(N_BITS, A, 16, 8), sc_code(A)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    B = 100
    vals = {m: {e: [] for e in OFFSETS + ("phase",)} for m in METRICS}
    rank1 = {m: 0 for m in METRICS}
    for _ in range(n // B):
        _, _, r, _, f, th = frames(B, code, snr, rng)
        sgn = rng.choice([-1.0, 1.0], B)
        for e in OFFSETS:
            mt = _metrics(llrs(r, f + sgn * e * STEP, th, sigma2), sc)
            for m in METRICS:
                vals[m][e].append(mt[m])
        q = rng.choice([1, 3], B)                            # a +-pi/2 phase error (a pi error is the CRC's job)
        mt = _metrics(llrs(r, f, th + q * np.pi / 2, sigma2), sc)
        for m in METRICS:
            vals[m]["phase"].append(mt[m])
        # ranking: is the true hypothesis (offset 0, true phase) the best of offsets -G..G x 2 phases (mod pi)?
        best = {m: np.full(B, np.inf) for m in METRICS}
        true = {}
        for k in range(-G, G + 1):
            for q in range(2):
                mt = _metrics(llrs(r, f + k * STEP + sgn * 0.0, th + q * np.pi / 2, sigma2), sc)
                for m in METRICS:
                    if k == 0 and q == 0:
                        true[m] = mt[m]
                    else:
                        best[m] = np.minimum(best[m], mt[m])
        for m in METRICS:
            rank1[m] += int(np.sum(true[m] < best[m]))
    return rate, snr, {m: {str(e): np.concatenate(v).tolist() for e, v in d.items()} for m, d in vals.items()}, rank1


def run_metric(rate, snrs, part, workers, n, G=3):
    tasks = [(rate, s, 600000 + 1000 * (s + 10) + i, n // 16, G) for s in snrs for i in range(16)]
    res = {}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for i, (_, s, vals, rank1) in enumerate(pool.imap_unordered(_metric_work, tasks), 1):
            d = res.setdefault(s, ({m: {e: [] for e in vals[m]} for m in METRICS}, {m: 0 for m in METRICS}))
            for m in METRICS:
                for e, v in vals[m].items():
                    d[0][m][e] += v
                d[1][m] += rank1[m]
            with open(path("logs", f"blind_metric_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} {time.time() - t0:.0f}\n")
    out = {"rate": rate, "snr": snrs, "offsets": OFFSETS, "step": STEP, "G": G, "n": n, "metric": {}}
    for s in snrs:
        vals, rank1 = res[s]
        for m in METRICS:
            v0 = np.array(vals[m]["0.0"])
            d = out["metric"].setdefault(m, {"mean": [], "auc": [], "rank1": []})
            d["mean"].append({e: float(np.mean(v)) for e, v in vals[m].items()})
            # AUC: P(metric of the true hypothesis < metric of the hypothesis off by e), the same frames
            d["auc"].append({e: float(np.mean(v0 < np.array(v)) + 0.5 * np.mean(v0 == np.array(v)))
                             for e, v in vals[m].items() if e != "0.0"})
            d["rank1"].append(rank1[m] / len(v0))           # the frames actually run (n rounded to batches)
    json.dump(out, open(path("logs", f"blind_metric_{rate.replace('/', '_')}_{part}.json"), "w"), indent=1)
    for m in METRICS:
        print(f"{m:22s} rank-1 " + " ".join(f"{v:.3f}" for v in out["metric"][m]["rank1"]), flush=True)
    print("EVAL DONE", flush=True)


# =====================================================================
# T3: sub-code metric (no interleaver)
# =====================================================================

SUB_M = (2048, 1024, 512)
SUB_OFFSETS = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0)


def _subcode_work(task):
    rate, snr, seed, n = task
    rng = np.random.default_rng(seed)
    A = CODES[rate]
    code = PolarCode(N_BITS, A, 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    subs = {M: subcode(A, M) for M in SUB_M}
    vals = {M: {e: [] for e in SUB_OFFSETS} for M in SUB_M}
    B = 100
    for _ in range(n // B):
        _, _, r, _, f, th = frames(B, code, snr, rng, interleave=False)
        sgn = rng.choice([-1.0, 1.0], B)
        for e in SUB_OFFSETS:
            llr = llrs(r, f + sgn * e * STEP, th, sigma2, interleave=False)
            for M, c in subs.items():
                vals[M][e].append(sc_metric(llr[:, N_BITS - M:], c))
    return rate, snr, {M: {str(e): np.concatenate(v).tolist() for e, v in d.items()} for M, d in vals.items()}


def run_subcode(rate, snrs, part, workers, n):
    tasks = [(rate, s, 800000 + 1000 * (s + 10) + i, n // 16) for s in snrs for i in range(16)]
    res = {}
    with mp.Pool(workers) as pool:
        for _, s, vals in pool.imap_unordered(_subcode_work, tasks):
            d = res.setdefault(s, {M: {e: [] for e in vals[M]} for M in vals})
            for M in vals:
                for e, v in vals[M].items():
                    d[M][e] += v
    out = {"rate": rate, "snr": snrs, "offsets": SUB_OFFSETS, "step": STEP, "M": SUB_M,
           "frozen": {str(M): int(subcode(CODES[rate], M).frozen.sum()) for M in SUB_M}, "auc": {}, "mean": {}}
    for s in snrs:
        for M in SUB_M:
            v0 = np.array(res[s][M]["0.0"])
            out["mean"].setdefault(str(M), []).append({e: float(np.mean(v)) for e, v in res[s][M].items()})
            out["auc"].setdefault(str(M), []).append(
                {e: float(np.mean(v0 < np.array(v)) + 0.5 * np.mean(v0 == np.array(v)))
                 for e, v in res[s][M].items() if e != "0.0"})
    json.dump(out, open(path("logs", f"blind_subcode_{rate.replace('/', '_')}_{part}.json"), "w"), indent=1)
    print(json.dumps(out["auc"])[:2000])
    print("EVAL DONE", flush=True)


# =====================================================================
# T4: decision-directed re-estimation (correct data, start error U[-5e-4, 5e-4], the range of passing decodes)
# =====================================================================

def _dd_work(task):
    rate, snr, seed, n = task
    rng = np.random.default_rng(seed)
    code = PolarCode(N_BITS, CODES[rate], 16, 8)
    se, cnt = 0.0, 0
    for _ in range(n // 200):
        data, _, r, _, f, _ = frames(200, code, snr, rng)
        fd, _ = dd_refine(r, data, code, f + rng.uniform(-5e-4, 5e-4, 200))
        se += float(np.sum((fd - f) ** 2))
        cnt += 200
    return rate, snr, se, cnt


def run_dd(rates, snrs, part, workers, n):
    tasks = [(rt, s, 900000 + 1000 * (s + 10) + 10 * i + j, n // 8) for j, rt in enumerate(rates) for s in snrs
             for i in range(8)]
    acc = {}
    with mp.Pool(workers) as pool:
        for rt, s, se, c in pool.imap_unordered(_dd_work, tasks):
            a = acc.setdefault((rt, s), [0.0, 0])
            a[0] += se
            a[1] += c
    out = {"snr": snrs, "mse": {rt: [acc[(rt, s)][0] / acc[(rt, s)][1] for s in snrs] for rt in rates},
           "crb1024": [crb_da(s) for s in snrs], "crb128": [crb_da(s, 128) for s in snrs]}
    json.dump(out, open(path("logs", f"blind_dd_{part}.json"), "w"), indent=1)
    for rt in rates:
        print(rt, " ".join(f"{m / c:.2f}" for m, c in zip(out["mse"][rt], out["crb1024"])), "x CRB1024", flush=True)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("test", choices=["coarse", "metric", "subcode", "dd", "plot"])
    ap.add_argument("--snrs", type=float, nargs="+", default=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8, 10])
    ap.add_argument("--rate", default="1/4", choices=list(CODES))
    ap.add_argument("--part", default="a")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--frames", type=int, default=20000)
    ap.add_argument("--G", type=int, default=3)
    a = ap.parse_args()
    snrs = [int(s) if float(s).is_integer() else s for s in a.snrs]
    if a.test == "coarse":
        run_coarse(snrs, a.part, a.workers, a.frames)
    elif a.test == "metric":
        run_metric(a.rate, snrs, a.part, a.workers, a.frames, a.G)
    elif a.test == "dd":
        run_dd(["1/10", "1/4", "1/2"], snrs, a.part, a.workers, a.frames)
    elif a.test == "subcode":
        run_subcode(a.rate, snrs, a.part, a.workers, a.frames)
    else:
        import blind_plots
        blind_plots.main()
