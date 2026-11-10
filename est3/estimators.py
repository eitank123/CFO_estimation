"""
est3 estimators. All take the preamble's MF output r (B, L_P) and its known symbols s (B, L_P) (and the true SNR only
where noted) and return the CFO estimate f_hat (B,) in cycles/symbol; *_macs give the real multiply-adds per burst
(conventions of polar_ber_experiment: complex multiply = 4, FFT = 2 NFFT log2 NFFT, an exponential = 8).

    ml_direct     Method 3: ML for the AWGN matched-preamble model r[n] = A s[n] e^{j 2 pi f n} + w[n]:
                  f_hat = argmax_f |sum_n r[n] s*[n] e^{-j 2 pi f n}|^2 over |f| <= MAX_CFO. Coarse grid (zero-padded
                  FFT restricted to the range, or a direct DFT on a uniform grid), then a refinement: none, parabolic
                  (on |Z|), Aboutanios-Mulgrew, Newton, or golden-section (the accurate reference). No M&M, no other
                  coarse estimator.
    joint_ml      Method 1: Morelli & Mengali (2000) scheme 1 (arbitrary training sequence): r = D(f) S h + w with an
                  unknown Lh-tap channel h (support -P .. Lh-1-P), h_hat(f) = LS, f_hat = argmin ||r - D S h_hat||^2
                  = argmax ||Q^H D^H(f) r||^2 (S = Q R): Lh FFTs of conj(q_j) r give the profile likelihood on the
                  grid, Newton refines it, h_hat = R^-1 Q^H D^H(f_hat) r. Lh = 1, P = 0 is exactly ml_direct.
                  Schemes 2 and 3 of the paper need a periodic training sequence and are NOT implemented.
    mm            the existing Mengali & Morelli 1997 estimator (polar_ber_experiment, unchanged): the baseline
    nn            Method 2 (est3/nn.py): the clustering NN and the CNNs
"""
import numpy as np

from est3.common import DELAY_SYM, L_P, MAX_CFO, conv_matrix

FFT_MACS = lambda n: 2 * n * int(np.log2(n))


# =====================================================================
# Profile likelihood of a (B, R, J) set of sequences x: Lambda(f) = sum_j |sum_n x[n, j] e^{-j 2 pi f n}|^2
# (ml_direct: J = 1, x = z = r s*; joint_ml: x[:, :, j] = conj(q_j) r)
# =====================================================================

def _grid_fft(x, nfft):
    """Peak of Lambda on the zero-padded FFT grid inside |f| <= MAX_CFO (+ one bin): f (B,), Lambda there,
    the neighbouring values (for interpolation) and the bin spacing."""
    X = np.fft.fft(x, nfft, axis=1)
    lam = np.sum(np.abs(X) ** 2, axis=2)                         # (B, nfft)
    nu = np.fft.fftfreq(nfft)
    ins = np.abs(nu) <= MAX_CFO + 1.0 / nfft
    k = np.where(ins[None], lam, -1.0).argmax(1)
    rows = np.arange(len(x))
    nb = np.sqrt(lam[rows[:, None], (k[:, None] + np.array([-1, 0, 1])[None]) % nfft])   # |Z| at k-1, k, k+1
    return nu[k], nb, 1.0 / nfft


def _grid_direct(x, step):
    """Peak of Lambda on the uniform grid -MAX_CFO .. MAX_CFO (step) by a direct DFT: f (B,), |Z| neighbours."""
    g = np.arange(-MAX_CFO, MAX_CFO + step / 2, step)
    n = np.arange(x.shape[1])
    E = np.exp(-2j * np.pi * g[:, None] * n[None])               # (G, R) twiddles: fixed, precomputed in hardware
    lam = np.sum(np.abs(np.einsum("gn,bnj->bgj", E, x)) ** 2, axis=2)
    k = lam.argmax(1)
    rows = np.arange(len(x))
    nb = np.sqrt(lam[rows[:, None], np.clip(k[:, None] + np.array([-1, 0, 1])[None], 0, len(g) - 1)])
    return g[k], nb, step


def _lam(x, f, t):
    e = np.exp(-2j * np.pi * f[:, None] * t[None])
    return np.sum(np.abs(np.einsum("bnj,bn->bj", x, e)) ** 2, axis=1)


def newton(x, f, iters=2, t=None):
    """Newton steps on Lambda(f) from f (B,) (centred time index t, default 0 .. R-1; steps clipped to half a bin
    1 / (2 span)). J = 1 is polar_ber_experiment.ml_newton."""
    R = x.shape[1]
    t = np.arange(R) - (R - 1) / 2 if t is None else t - t.mean()
    R = t.max() - t.min() + 1
    w = -2j * np.pi * t
    for _ in range(iters):
        e = np.exp(-2j * np.pi * f[:, None] * t[None])
        A = np.einsum("bnj,bn->bj", x, e)
        A1 = np.einsum("bnj,bn->bj", x, w[None] * e)
        A2 = np.einsum("bnj,bn->bj", x, (w ** 2)[None] * e)
        g = 2 * np.sum((A1 * A.conj()).real, 1)
        h = 2 * np.sum((A2 * A.conj()).real + np.abs(A1) ** 2, 1)
        step = np.where(h < 0, -g / np.where(h < 0, h, -1.0), 0.0)
        f = f + np.clip(step, -0.5 / R, 0.5 / R)
    return f


def golden(x, f, half, tol=1e-11):
    """Golden-section maximisation of Lambda on [f - half, f + half] (the reference refinement)."""
    R = x.shape[1]
    t = np.arange(R) - (R - 1) / 2
    a, b = f - half, f + half
    gr = (np.sqrt(5) - 1) / 2
    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = _lam(x, c, t), _lam(x, d, t)
    while np.max(b - a) > tol:
        left = fc > fd                                           # the maximum is in [a, d]: drop (d, b]
        a, b = np.where(left, a, c), np.where(left, d, b)
        nc, nd = b - gr * (b - a), a + gr * (b - a)
        fnc, fnd = _lam(x, nc, t), _lam(x, nd, t)
        c, d, fc, fd = (np.where(left, nc, d), np.where(left, c, nd),
                        np.where(left, fnc, fd), np.where(left, fc, fnd))
    return (a + b) / 2


def refine(x, f, nb, step, how, iters):
    """Refinement of the grid peak f: 'none', 'parabolic' (on |Z| at the grid neighbours), 'am' (Aboutanios &
    Mulgrew: |Z| half a 1/R bin either side, iterated), 'newton', 'golden' (to 1e-11, the reference)."""
    R = x.shape[1]
    if how == "none":
        return f
    if how == "parabolic":
        den = nb[:, 0] - 2 * nb[:, 1] + nb[:, 2]
        off = np.clip(np.where(den < 0, 0.5 * (nb[:, 0] - nb[:, 2]) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
        return f + off * step
    if how == "am":
        t = np.arange(R) - (R - 1) / 2
        for _ in range(iters):
            Xp = np.sqrt(_lam(x, f + 0.5 / R, t))
            Xm = np.sqrt(_lam(x, f - 0.5 / R, t))
            f = f + 0.5 * (Xp - Xm) / (Xp + Xm + 1e-30) / R
        return f
    if how == "newton":
        return newton(x, f, iters)
    if how == "golden":
        return golden(x, f, step)
    raise ValueError(how)


def peak(x, grid, refine_how="newton", iters=2):
    """Grid search ('fft<NFFT>' or 'step<value>') of Lambda over the whole range + refinement. 'golden' (the
    reference) refines the 3 highest local maxima of the grid and keeps the best, so two nearly equal lobes at low
    SNR cannot make it miss the global maximum."""
    if refine_how == "golden":
        n = int(grid[3:])
        lam = np.sum(np.abs(np.fft.fft(x, n, axis=1)) ** 2, axis=2)
        nu = np.fft.fftfreq(n)
        lam = np.where(np.abs(nu)[None] <= MAX_CFO + 1.0 / n, lam, -1.0)
        loc = (lam >= np.roll(lam, 1, 1)) & (lam >= np.roll(lam, -1, 1))
        top = np.argsort(-np.where(loc, lam, -1.0), 1)[:, :3]
        t = np.arange(x.shape[1]) - (x.shape[1] - 1) / 2
        cand = np.stack([golden(x, nu[top[:, i]], 1.0 / n) for i in range(3)], 1)
        val = np.stack([_lam(x, cand[:, i], t) for i in range(3)], 1)
        return cand[np.arange(len(x)), val.argmax(1)]
    if grid.startswith("fft"):
        f, nb, st = _grid_fft(x, int(grid[3:]))
    else:
        f, nb, st = _grid_direct(x, float(grid[4:]))
    return refine(x, f, nb, st, refine_how, iters)


def peak_macs(R, J, grid, refine_how, iters):
    """Real MACs of peak() per burst (J sequences of length R)."""
    if grid.startswith("fft"):
        n = int(grid[3:])
        m = J * FFT_MACS(n) + J * 2 * n
    else:
        G = int(round(2 * MAX_CFO / float(grid[4:]))) + 1
        m = G * J * 4 * R + G * J * 2
    per = J * 4 * R + 8 * R                                      # one evaluation of Lambda (sums + exponentials)
    m += {"none": 0, "parabolic": 10, "am": iters * 2 * per, "newton": iters * (3 * J * 4 * R + 8 * R),
          "golden": 3 * 55 * per}[refine_how]
    return m


# =====================================================================
# Method 3: direct ML (AWGN matched-preamble likelihood)
# =====================================================================

ML_DEFAULT = ("fft512", "newton", 2)


def ml_direct(r, s, grid=ML_DEFAULT[0], refine_how=ML_DEFAULT[1], iters=ML_DEFAULT[2]):
    z = r * np.conj(s)
    return peak(z[:, :, None], grid, refine_how, iters)


def ml_direct_macs(grid=ML_DEFAULT[0], refine_how=ML_DEFAULT[1], iters=ML_DEFAULT[2]):
    return 4 * L_P + peak_macs(L_P, 1, grid, refine_how, iters)


def ml_brute(r, s, step=1e-6, chunk=2000):
    """Dense-grid reference: |A(f)| on a uniform grid of the whole range (step), no interpolation."""
    z = r * np.conj(s)
    g = np.arange(-MAX_CFO, MAX_CFO + step / 2, step)
    n = np.arange(z.shape[1]) - (z.shape[1] - 1) / 2
    best = np.full(len(z), -1.0)
    fb = np.zeros(len(z))
    for a in range(0, len(g), chunk):
        gg = g[a:a + chunk]
        A = np.abs(z @ np.exp(-2j * np.pi * gg[:, None] * n[None]).T)
        k = A.argmax(1)
        v = A[np.arange(len(z)), k]
        up = v > best
        best[up], fb[up] = v[up], gg[k[up]]
    return fb


# =====================================================================
# Method 1: joint CFO / channel ML (Morelli & Mengali 2000, scheme 1)
# =====================================================================

JOINT_DEFAULT = ("fft512", "newton", 2)


def joint_ml(r, s, P, Lh, grid=JOINT_DEFAULT[0], refine_how=JOINT_DEFAULT[1], iters=JOINT_DEFAULT[2],
             return_h=False):
    """f_hat (B,) (and the LS channel at it, taps -P .. Lh-1-P, phase referenced as common.ls_channel)."""
    S = conv_matrix(s, P, Lh)                                    # (B, R, Lh), R = L - P
    Q, Rm = np.linalg.qr(S)
    R = S.shape[1]
    x = Q.conj() * r[:, :R, None]                                # x[n, j] = conj(q_j[n]) r[n]
    f = peak(x, grid, refine_how, iters)
    if not return_h:
        return f
    y = r[:, :R] * np.exp(-2j * np.pi * f[:, None] * (np.arange(R) + DELAY_SYM)[None])
    h = np.linalg.solve(Rm, np.einsum("brl,br->bl", Q.conj(), y)[..., None])[..., 0]
    return f, h


def joint_macs(P, Lh, grid=JOINT_DEFAULT[0], refine_how=JOINT_DEFAULT[1], iters=JOINT_DEFAULT[2]):
    R = L_P - P
    qr = 4 * 2 * R * Lh ** 2                                     # Householder QR of the R x Lh training matrix
    return qr + 4 * R * Lh + peak_macs(R, Lh, grid, refine_how, iters)   # (the training matrix is known in advance:
                                                                         # Q can be precomputed for a fixed preamble)


def joint_ref(r, s, P, Lh, step=1e-5):
    """Dense-grid reference of joint_ml straight from the definition: the LS residual ||r - D(f) S h_hat(f)||^2
    (np.linalg.lstsq at every grid point) minimised over the whole range, then golden-section on the residual."""
    S = conv_matrix(s, P, Lh)
    R = S.shape[1]
    n = np.arange(R)
    out = np.empty(len(r))
    for b in range(len(r)):
        def res(f):
            y = r[b, :R] * np.exp(-2j * np.pi * f * n)
            h, *_ = np.linalg.lstsq(S[b], y, rcond=None)
            return np.sum(np.abs(y - S[b] @ h) ** 2)
        g = np.arange(-MAX_CFO, MAX_CFO + step / 2, step)
        v = np.array([res(f) for f in g])
        k = int(v.argmin())
        a, c = g[max(k - 1, 0)], g[min(k + 1, len(g) - 1)]
        gr = (np.sqrt(5) - 1) / 2
        while c - a > 1e-11:
            u, w = c - gr * (c - a), a + gr * (c - a)
            if res(u) < res(w):
                c = w
            else:
                a = u
        out[b] = (a + c) / 2
    return out


# =====================================================================
# Baseline: the existing M&M (polar_ber_experiment.bench_estimate("mm"), unchanged)
# =====================================================================

def mm(r, s, snr_db):
    import polar_ber_experiment as pbe
    assert pbe.MAX_CFO == MAX_CFO and pbe.L_EST == L_P
    return pbe.bench_estimate("mm", r * np.conj(s), snr_db)


MM_MACS = 24_704 + 4 * L_P


# =====================================================================
# More estimators in use (contiguous / periodic / distributed pilots)
# =====================================================================

def candan(r, s):
    """Jacobsen's three-DFT-bin interpolator with Candan's bias correction (IEEE SPL 2011) on the UNPADDED L-point FFT
    of z = r s* (the cheap hardware variant of the ML periodogram): k = peak bin inside the range,
    delta = tan(pi/L)/(pi/L) Re{(X[k-1] - X[k+1]) / (2 X[k] - X[k-1] - X[k+1])}, f = (k + delta) / L."""
    z = r * np.conj(s)
    L = z.shape[1]
    X = np.fft.fft(z, axis=1)
    nu = np.fft.fftfreq(L)
    k = np.where(np.abs(nu)[None] <= MAX_CFO + 1.0 / L, np.abs(X), -1.0).argmax(1)
    rows = np.arange(len(z))
    Xm, X0, Xp = X[rows, (k - 1) % L], X[rows, k], X[rows, (k + 1) % L]
    d = np.tan(np.pi / L) / (np.pi / L) * np.real((Xm - Xp) / (2 * X0 - Xm - Xp))
    return nu[k] + np.clip(d, -0.5, 0.5) / L


CANDAN_MACS = 4 * L_P + FFT_MACS(L_P) + L_P + 40


def moose(r, Q=16):
    """Schmidl & Cox / Moose on a periodic preamble (period Q symbols; needs no knowledge of the symbols):
    f = arg(sum_n r[n] r*[n - Q]) / (2 pi Q), range |f| < 1 / (2Q) = 0.031 for Q = 16."""
    return np.angle(np.sum(r[:, Q:] * np.conj(r[:, :-Q]), 1)) / (2 * np.pi * Q)


MOOSE_MACS = 4 * (L_P - 16) + 20


def blue_mm99(r, Q=16):
    """Morelli & Mengali, "An improved frequency offset estimator for OFDM applications", IEEE Commun. Lett. 3(3),
    1999 (BLUE): U = L / Q periods, R(m) = 1/(L - mQ) sum_{k=mQ}^{L-1} r[k] r*[k - mQ], m = 0 .. H = U/2,
    phi(m) = [arg R(m) - arg R(m-1)]_2pi, f = sum_m w(m) phi(m) / (2 pi Q),
    w(m) = 3 ((U-m)(U-m+1) - H(U-H)) / (H (4H^2 - 6UH + 3U^2 - 1)) (sum w = 1). Range |f| < 1 / (2Q)."""
    L = r.shape[1]
    U = L // Q
    H = U // 2
    R = [np.ones(len(r), complex)] + [np.sum(r[:, m * Q:] * np.conj(r[:, :L - m * Q]), 1) / (L - m * Q)
                                      for m in range(1, H + 1)]
    ph = np.stack([np.angle(R[m] * np.conj(R[m - 1])) for m in range(1, H + 1)], 1)
    m = np.arange(1, H + 1)
    w = 3 * ((U - m) * (U - m + 1) - H * (U - H)) / (H * (4 * H ** 2 - 6 * U * H + 3 * U ** 2 - 1))
    return ph @ w / (2 * np.pi * Q)


BLUE_MACS = 4 * 4 * L_P + 4 * 20


def dist_ml(r, s, pos, nfft=8192, iters=3):
    """ML for pilots at arbitrary positions pos (K,): argmax_f |sum_k z_k e^{-j 2 pi f n_k}|^2 over the whole range
    (z placed on the 1024-symbol time axis, zero-padded FFT, then Newton on the exact positions)."""
    z = r * np.conj(s)
    x = np.zeros((len(z), pos.max() + 1), complex)
    x[:, pos] = z
    f, _, _ = _grid_fft(x[:, :, None], nfft)
    return newton(z[:, :, None], f, iters, t=pos.astype(float))


def dist_ml_macs(K, nfft=8192, iters=3):
    return 4 * K + FFT_MACS(nfft) + 2 * nfft + iters * (3 * 4 * K + 8 * K)


def dvbs2_blocks(r, s, pos, nb):
    """The DVB-S2 pilot-aided practice (Casini, De Gaudenzi & Ginesi, IJSCN 2004) on nb equal pilot blocks: coarse
    f_c = peak of the non-coherently combined block periodograms sum_b |Z_b(f)|^2 (512-point FFT per block,
    parabolic interpolation), then the block phasors B_b = sum_{n in b} z_n e^{-j 2 pi f_c n} and
    f = f_c + arg(sum_b B_{b+1} B_b*) / (2 pi D) (D = block spacing; unambiguous for |f - f_c| < 1 / (2D))."""
    z = r * np.conj(s)
    Kb = len(pos) // nb
    zb = z.reshape(len(z), nb, Kb)
    P = np.sum(np.abs(np.fft.fft(zb, 512, axis=2)) ** 2, axis=1)    # (B, 512)
    nu = np.fft.fftfreq(512)
    k = np.where(np.abs(nu)[None] <= MAX_CFO + 1 / 512, P, -1.0).argmax(1)
    rows = np.arange(len(z))
    V = np.sqrt(P[rows[:, None], (k[:, None] + np.array([-1, 0, 1])[None]) % 512])
    den = V[:, 0] - 2 * V[:, 1] + V[:, 2]
    off = np.clip(np.where(den < 0, 0.5 * (V[:, 0] - V[:, 2]) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
    fc = nu[k] + off / 512
    Bb = np.sum(z.reshape(len(z), nb, Kb) * np.exp(-2j * np.pi * fc[:, None, None] *
                                                   pos.reshape(nb, Kb)[None]), axis=2)
    D = (pos.reshape(nb, Kb)[:, 0][1:] - pos.reshape(nb, Kb)[:, 0][:-1]).mean()
    return fc + np.angle(np.sum(Bb[:, 1:] * np.conj(Bb[:, :-1]), 1)) / (2 * np.pi * D)


def dvbs2_macs(K, nb):
    return 4 * K + nb * (FFT_MACS(512) + 2 * 512) + 20 + 4 * K + 8 * K + 4 * nb + 20
