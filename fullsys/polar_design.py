"""
Gaussian-approximation (GA, density-evolution) polar construction over the RATE-MATCHED channel, for
fullsys/polar_rm.py (rm_plan / RMPolarCode design='ga'): the info set designed for the bits actually sent, instead of
the rate-matching-blind PW order (design='pw', the default there, unchanged).

    Channel : per mother x position the LLR mean m (LLR ~ N(m, 2m), symmetric-consistent):
                sent        4 Es / (bps N0) per coded bit (QPSK Gray bps = 2: LLR 2 sqrt2 Re y / N0, mean 2 Es/N0;
                            (pi/2-)BPSK bps = 1: mean 4 Es/N0), times the number of copies under repetition (MRC)
                shortened   MU_BIG (known zero: rate_recover's +LLR_BIG)
                punctured   0
              mapped through the sub-block interleaver as rate_recover: x_{J(n)} <- y_n
    Transf. : natural order as polar.py (x = u F^{(x)n}; the decoder's f on the low half, g on the high half): per
              stage, for each pair (a, b) = (m_i, m_{i + s}) of a 2s block
                u low   f(a, b) = phi^-1(1 - (1 - phi(a)) (1 - phi(b)))
                u high  g(a, b) = a + b
              (per-position GA: non-identical channels, as needed for puncturing / shortening)
    phi     : the two-piece Chung-Richardson-Urbanke approximation used by Trifonov (IEEE TCOM 2012):
                phi(x) = exp(-0.4527 x^0.86 + 0.0218)               0 <= x < 10   (clipped to <= 1: phi(0) = 1)
                         sqrt(pi / x) exp(-x / 4) (1 - 10 / (7 x))      x >= 10
              in the log domain (no underflow up to MU_BIG); phi^-1 closed form on piece 1, bisection on piece 2
    Ranking : u means ascending; ties (equal means, e.g. the zero-capacity punctured channels) broken by the PW
              order; the info set = the K largest outside the pre-frozen set (rm_plan)

No CRC-aware tweak: plain GA at the design SNR is the standard CA-SCL construction (NR's sequence has none either).
The NR sequence (TS 38.212 Table 5.3.1.2-1) is not offered: no local source (sionna, which ships it, is cluster-only),
and it covers only N <= 1024 (id3; id13 / id14 run at N = 4096).
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:                                       # polar.py lives at the project root
    sys.path.insert(0, _ROOT)
from polar import pw_reliability  # noqa: E402

A1, B1, C1 = 0.4527, 0.86, 0.0218  # phi piece 1: exp(-A1 x^B1 + C1)
X_SPLIT = 10.0                     # piece 1 below, piece 2 (asymptotic) above
MU_BIG = 1e8                       # LLR mean of a shortened (known) bit: phi = e^-2.5e7, exact enough as +inf
_Y1 = -A1 * X_SPLIT ** B1 + C1     # log phi piece 1 at the split (-3.257; piece 2 there -3.233: a 2 % jump)


def _log_phi2(x):
    """log of phi piece 2 (x >= 10): 0.5 log(pi / x) - x / 4 + log(1 - 10 / (7 x)); decreasing."""
    return 0.5 * np.log(np.pi / x) - x / 4 + np.log1p(-10 / (7 * x))


def log_phi(x):
    """log phi(x) (any shape), <= 0, = 0 at x <= 0 (and x < 0.029, where piece 1 exceeds 1)."""
    x = np.asarray(x, dtype=np.float64)
    out = np.zeros_like(x)
    p1, p2 = (x > 0) & (x < X_SPLIT), x >= X_SPLIT
    out[p1] = np.minimum(-A1 * x[p1] ** B1 + C1, 0.0)
    out[p2] = _log_phi2(x[p2])
    return out


def phi_inv_log(ly, iters=100):
    """x with log phi(x) = ly (any shape): 0 at ly >= 0; piece 1 closed form for ly >= _Y1; piece 2 by bisection on
    log x in [log 10, log(10 - 4 ly)] (piece 2 < -x / 4 for x >= 10 brackets the root)."""
    ly = np.minimum(np.asarray(ly, dtype=np.float64), 0.0)
    x = np.zeros_like(ly)
    p1, p2 = (ly < 0) & (ly >= _Y1), ly < _Y1
    x[p1] = ((C1 - ly[p1]) / A1) ** (1 / B1)
    if p2.any():
        t = ly[p2]
        lo, hi = np.full_like(t, np.log(X_SPLIT)), np.log(X_SPLIT - 4 * t)
        for _ in range(iters):
            mid = 0.5 * (lo + hi)
            up = _log_phi2(np.exp(mid)) > t                    # root above mid
            lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
        x[p2] = np.exp(0.5 * (lo + hi))
    return x


def ga_f(a, b):
    """Check-node mean phi^-1(1 - (1 - phi(a))(1 - phi(b))), in logs: log(pa + pb - pa pb) =
    logaddexp(la, lb) + log1p(-exp(la + lb - logaddexp(la, lb)))."""
    la, lb = log_phi(a), log_phi(b)
    ls = np.logaddexp(la, lb)
    return phi_inv_log(ls + np.log1p(-np.exp(la + lb - ls)))


def ga_bit_means(m_x):
    """Channel LLR means m_x (N,) per x position -> GA bit-channel means (N,) per u position (polar.py order)."""
    m = np.asarray(m_x, dtype=np.float64).copy()
    N = len(m)
    s = N // 2
    while s >= 1:                                               # top stage first: (u low, u high) of each 2s block
        v = m.reshape(N // (2 * s), 2, s)
        a, b = v[:, 0, :].copy(), v[:, 1, :].copy()
        v[:, 0, :], v[:, 1, :] = ga_f(a, b), a + b
        s //= 2
    return m


def design_mu(esn0_db, bps=2):
    """LLR mean of a sent coded bit: 4 Es / (bps N0) (QPSK Gray bps 2 -> 2 Es/N0, BPSK bps 1 -> 4 Es/N0)."""
    return 4.0 * 10 ** (esn0_db / 10) / bps


def rm_channel_means(N, E, mode, J, mu):
    """Per mother x position LLR mean (N,) after rate recovery: punctured y[:U] 0, shortened y[E:] MU_BIG, sent mu
    (repeat / none: mu times the copies), then x_{J(n)} = y_n (polar_rm.RMPolarCode.rate_recover)."""
    U = max(N - E, 0)
    y = np.zeros(N)
    if mode == "puncture":
        y[U:] = mu
    elif mode == "shorten":
        y[:E], y[E:] = mu, MU_BIG
    else:
        y += mu * np.bincount(np.arange(E) % N, minlength=N)
    m = np.empty(N)
    m[J] = y
    return m


def ga_order(m_u):
    """u indices least -> most reliable by GA mean; ties broken by the PW order (polar.pw_reliability)."""
    N = len(m_u)
    pw_rank = np.empty(N, np.int64)
    pw_rank[pw_reliability(N)] = np.arange(N)
    return np.lexsort((pw_rank, m_u))


def ga_design(N, E, mode, J, esn0_db, bps=2):
    """GA over the rate-matched channel: dict m_x (N,), m_u (N,), order (N,) least -> most reliable, mu."""
    mu = design_mu(esn0_db, bps)
    m_x = rm_channel_means(N, E, mode, J, mu)
    m_u = ga_bit_means(m_x)
    return dict(m_x=m_x, m_u=m_u, order=ga_order(m_u), mu=mu)


def q_func(x):
    """Gaussian tail Q(x) = erfc(x / sqrt2) / 2 (any shape)."""
    from math import erfc
    return 0.5 * np.vectorize(erfc, otypes=[np.float64])(np.asarray(x, dtype=np.float64) / np.sqrt(2))


def union_bound(m_u, info_pos):
    """GA SC BLER union bound sum_{i in info} Q(sqrt(m_i / 2)) (LLR ~ N(m, 2m): P(sign error) = Q(m / sqrt(2m)))."""
    return float(q_func(np.sqrt(np.asarray(m_u)[np.asarray(info_pos)] / 2)).sum())
