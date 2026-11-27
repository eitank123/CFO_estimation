"""
est3: more preamble CFO estimators on AWGN, common parts.

Conventions (the project's, see txrx_chain.py / blind_cfo.py):
    f       normalised CFO in cycles per SYMBOL (eps of the task); the chain applies it per 8-SPS sample as
            exp(j 2 pi f m / SPS), so the MF output r[n] carries 2 pi f (n + DELAY_SYM) + phase. |f| <= MAX_CFO = 0.03
    SNR     Es/N0 at the MF output (unit-energy RRC, Es measured per frame from the Tx samples, as main.apply_awgn)
    pilots  128 known symbols INSIDE the 1024-symbol packet (the existing benchmarks' convention: they are codeword
            symbols, no overhead), in one of the LAYOUTS:
              contig     the first 128 symbols (the existing preamble; random QPSK)
              periodic   the first 128 symbols = 8 repetitions of a random 16-symbol QPSK block (repeated-preamble
                         estimators: Schmidl & Cox / Moose, Morelli & Mengali's BLUE)
              split2x64  2 blocks of 64 centred at N/4, 3N/4 (as train_cfo_v3's "quarter" layout)
              dist4x32   4 blocks of 32, dist8x16   8 blocks of 16, centred at (b + 1/2) N / blocks (DVB-S2-like
                         distributed pilot blocks)
Channel: AWGN only (the chain is exactly blind_cfo.transmit_full).
"""
import os

os.environ.setdefault("CFO_MAX", "0.03")       # the benchmark modules read these at import
os.environ.setdefault("POLAR_NSYM", "1024")

import numpy as np
from scipy.signal import fftconvolve

import config as cfg
from txrx_chain import rrc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS, MODELS, LOGS, PLOTS = (os.path.join(HERE, d) for d in ("results", "models", "logs", "plots"))

N_SYM, N_BITS, L_P = 1024, 2048, 128
SPS, SPAN, BETA = cfg.SPS, cfg.FILTER_SPAN, cfg.BETA
DELAY_SYM = SPAN / 2
MAX_CFO = 0.03
TAIL = 24                                      # data symbols after a contiguous preamble in preamble-only bursts (> RRC
                                               # span: the preamble's MF outputs are exactly as in a packet)
INTERLEAVER = np.random.default_rng(12345).permutation(N_BITS)   # as polar_ber_experiment / blind_cfo
CODES = {"1/10": 205, "0.15": 307, "2/5": 819, "1/2": 1024}                    # data bits A, CRC-16, N = 2048
CHANNELS = ("awgn",)
REP_Q = 16                                     # periodic preamble: 8 repetitions of 16 symbols


def _blocks(nb, size):
    c = (np.arange(nb) + 0.5) * N_SYM / nb
    return np.concatenate([np.arange(int(round(x - size / 2)), int(round(x - size / 2)) + size) for x in c])


LAYOUTS = {"contig": np.arange(L_P), "periodic": np.arange(L_P), "split2x64": _blocks(2, 64),
           "dist4x32": _blocks(4, 32), "dist8x16": _blocks(8, 16)}
BLOCKS = {"split2x64": 2, "dist4x32": 4, "dist8x16": 8}


def transmit(sym, f, ph, snr_db, rng, noise_only=False):
    """The full AWGN chain (identical to blind_cfo.transmit_full). sym (B, K) unit-energy symbols. Returns the MF
    output r (B, K) and the noisy 8-SPS samples rx (for the pre-MF correction)."""
    B, K = sym.shape
    h = rrc(BETA)
    up = np.zeros((B, K * SPS), complex)
    up[:, ::SPS] = sym
    tx = fftconvolve(up, h[None], axes=1)
    es = np.sum(np.abs(tx) ** 2, axis=1, keepdims=True) / K          # main.apply_awgn
    m = np.arange(tx.shape[1])
    rx = tx * np.exp(1j * (2 * np.pi * np.asarray(f, float).reshape(-1, 1) * m / SPS
                           + np.asarray(ph, float).reshape(-1, 1)))
    sigma = np.sqrt(es / (10 ** (np.asarray(snr_db, float).reshape(-1, 1) / 10)) / 2)
    if noise_only:
        rx = np.zeros_like(rx)
    rx = rx + sigma * (rng.standard_normal(rx.shape) + 1j * rng.standard_normal(rx.shape))
    D = SPAN * SPS
    return fftconvolve(rx, h[None], axes=1)[:, D:D + K * SPS:SPS], rx


def qpsk(rng, shape):
    b = rng.integers(0, 2, shape + (2,))
    return ((1 - 2.0 * b[..., 0]) + 1j * (1 - 2.0 * b[..., 1])) / np.sqrt(2)


def periodic_symbols(rng, B):
    return np.tile(qpsk(rng, (B, REP_Q)), (1, L_P // REP_Q))


def bursts(B, snr_db, rng, layout="contig", f=None, ph=None):
    """Bursts for a pilot layout: r (B, K) MF output at the pilot positions, s (B, K) the known symbols, f, phase.
    contig / periodic: the first L_P + TAIL symbols of a packet (cheaper, identical MF outputs); distributed layouts:
    whole 1024-symbol packets. f / ph can be given (the same CFO and phase on another burst)."""
    pos = LAYOUTS[layout]
    K = L_P + TAIL if layout in ("contig", "periodic") else N_SYM
    sym = qpsk(rng, (B, K))
    if layout == "periodic":
        sym[:, :L_P] = periodic_symbols(rng, B)
    f = rng.uniform(-MAX_CFO, MAX_CFO, B) if f is None else f
    ph = rng.uniform(0, 2 * np.pi, B) if ph is None else ph
    snr = np.broadcast_to(np.asarray(snr_db, float), (B,))
    r, _ = transmit(sym, f, ph, snr, rng)
    return r[:, pos], sym[:, pos], f, ph


def preamble_bursts(B, snr_db, rng):
    """The contiguous 128-symbol preamble (NN training / evaluation): r, s, f, phase."""
    return bursts(B, snr_db, rng, "contig")


# =====================================================================
# Cramer-Rao bounds (AWGN, known pilot symbols, unknown phase)
# =====================================================================

def crb_awgn(snr_db, L=L_P):
    """Contiguous L known symbols: 3 / (2 pi^2 SNR L (L^2 - 1)) (cycles/symbol)^2."""
    return 3.0 / (2 * np.pi ** 2 * 10 ** (np.asarray(snr_db) / 10) * L * (L ** 2 - 1))


def crb_layout(snr_db, layout):
    """Any pilot positions n_k: 1 / (2 SNR (2 pi)^2 sum (n_k - mean n)^2) (unknown phase and amplitude)."""
    n = LAYOUTS[layout].astype(float)
    return 1.0 / (2 * 10 ** (np.asarray(snr_db) / 10) * (2 * np.pi) ** 2 * np.sum((n - n.mean()) ** 2))


def conv_matrix(s, P, Lh):
    """Training matrix (B, R, Lh) of y[n] = sum_{k=-P}^{Lh-1-P} h_k s[n-k], rows n = 0 .. L-1-P; s[n] = 0 before
    the burst (Method 1's channel model; on AWGN the true channel is the single tap k = 0)."""
    B, L = s.shape
    R = L - P
    S = np.zeros((B, R, Lh), complex)
    for j in range(Lh):
        k = j - P
        n = np.arange(R)
        idx = n - k
        ok = (idx >= 0) & (idx < L)
        S[:, ok, j] = s[:, idx[ok]]
    return S


def crb_unknown_taps(s, P, Lh, snr_db):
    """CRB (B,) of f when the estimator treats Lh taps (support -P ..) as unknown and the true channel is the single
    tap 1 at k = 0 (AWGN): J = 2 SNR (2 pi)^2 ||Proj_perp(S) N S h||^2: the bound of Method 1 with Lh assumed taps."""
    S = conv_matrix(s, P, Lh)
    h = np.zeros(Lh, complex)
    h[P] = 1.0
    n = np.arange(S.shape[1], dtype=float)
    v = n[None] * np.einsum("brl,l->br", S, h)
    Q, _ = np.linalg.qr(S)
    proj = v - np.einsum("brl,bl->br", Q, np.einsum("brl,br->bl", Q.conj(), v))
    return 1.0 / (2 * 10 ** (snr_db / 10) * (2 * np.pi) ** 2 * np.real(np.sum(v.conj() * proj, 1)))


# =====================================================================
# Receiver back-end shared by every estimator (BLER)
# =====================================================================

def gain_phase(r, s, pos, f):
    """Complex gain (B,) from the known symbols at CFO hypothesis f (B,): LS of r[pos] e^{-j 2 pi f (pos + D)} on s."""
    y = r[:, pos] * np.exp(-2j * np.pi * f[:, None] * (pos + DELAY_SYM)[None])
    return np.sum(y * np.conj(s), 1) / np.sum(np.abs(s) ** 2, 1)


def llrs(r, f, g, sigma2c):
    """De-interleaved channel LLRs (B, N_BITS) of the packet r de-rotated by f and divided by the gain g
    (complex noise variance sigma2c / |g|^2)."""
    sh = r * np.exp(-2j * np.pi * f[:, None] * (np.arange(r.shape[1]) + DELAY_SYM)[None]) / g[:, None]
    var = sigma2c / np.abs(g) ** 2
    llr = np.empty((len(r), N_BITS))
    llr[:, 0::2] = 2 * np.sqrt(2) * sh.real / var[:, None]
    llr[:, 1::2] = 2 * np.sqrt(2) * sh.imag / var[:, None]
    out = np.empty_like(llr)
    out[:, INTERLEAVER] = llr
    return out, sh


def path(kind, name):
    d = {"results": RESULTS, "models": MODELS, "logs": LOGS, "plots": PLOTS}[kind]
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)
