"""
The full Tx/Rx chain of main.py, vectorised over frames. Every simulation, training set and evaluation in
this project goes through it (no symbol-rate shortcut):

    QPSK symbols -> upsample x SPS -> RRC (beta, span) -> CFO per sample (before the matched filter)
    -> AWGN (Es/N0 per symbol; Es measured per frame as main.apply_awgn) -> matched RRC
    -> remove the filter delay (main.remove_filter_delay) -> downsample (main.downsample)

Checked against main.py's per-frame functions: identical to ~1e-15 (noiseless).

Timing of the symbol-rate output r[n]: the pulse of symbol n peaks at Tx sample SPS*n + SPAN*SPS/2, so the CFO
phase of r[n] is 2 pi f (n + SPAN/2) + phase; the matched filter adds no phase (symmetric real RRC), only an
amplitude loss G(f) = sum_k h[k]^2 cos(2 pi f k / SPS) < 1 and some ISI for a large CFO.
"""

import numpy as np

import channel
import config as cfg

SPS, SPAN = cfg.SPS, cfg.FILTER_SPAN
DELAY_SYM = SPAN / 2                     # CFO phase reference offset of r[n] (symbols)
FFT_WORKERS = 1                          # threads for the convolutions (raise in single-process training jobs)
_rrc = {}


def rrc(beta):
    if beta not in _rrc:
        _rrc[beta] = np.asarray(channel.rrc_design(beta, SPS, SPAN))
    return _rrc[beta]


def qpsk(rng, shape):
    return ((2 * rng.integers(0, 2, shape) - 1) + 1j * (2 * rng.integers(0, 2, shape) - 1)) / np.sqrt(2)


def transmit(sym, f, phase, snr_db, rng, beta=cfg.BETA):
    """
    sym (B, K) complex unit-energy symbols, f (B,) normalised CFO, phase (B,), snr_db scalar or (B,).
    Returns the matched-filter output at the symbol instants, r (B, K).
    """
    import scipy.fft
    from scipy.signal import fftconvolve
    with scipy.fft.set_workers(FFT_WORKERS):
        return _transmit(sym, f, phase, snr_db, rng, beta, fftconvolve)


def _transmit(sym, f, phase, snr_db, rng, beta, fftconvolve):
    B, K = sym.shape
    h = rrc(beta)
    up = np.zeros((B, K * SPS), complex)
    up[:, ::SPS] = sym
    tx = fftconvolve(up, h[None], axes=1)                                   # 'full', as np.convolve
    m = np.arange(tx.shape[1])
    rx = tx * np.exp(1j * (2 * np.pi * np.asarray(f, float).reshape(-1, 1) * m / SPS
                           + np.asarray(phase, float).reshape(-1, 1)))
    es = np.sum(np.abs(tx) ** 2, axis=1, keepdims=True) / K                # main.apply_awgn
    snr = 10 ** (np.asarray(snr_db, float).reshape(-1, 1) / 10)
    sigma = np.sqrt(es / snr / 2)
    rx = rx + sigma * (rng.standard_normal(rx.shape) + 1j * rng.standard_normal(rx.shape))
    D = SPAN * SPS
    return fftconvolve(rx, h[None], axes=1)[:, D:D + K * SPS:SPS]


def known_sequence(B, K, snr_db, rng, max_cfo=cfg.MAX_CFO, beta=cfg.BETA):
    """Random K-symbol known sequences through the chain: z = r s* (B, K), true CFO f (B,)."""
    sym = qpsk(rng, (B, K))
    f = rng.uniform(-max_cfo, max_cfo, B)
    r = transmit(sym, f, rng.uniform(0, 2 * np.pi, B), snr_db, rng, beta)
    return r * np.conj(sym), f
