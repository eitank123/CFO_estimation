"""
est4 CFO estimators and phase models on a burst's MF output r (B, K) with its known symbols ks (B, Nk) at the burst
positions kidx (layout(...)["known_idx"]); z_k = r[kidx_k] conj(ks_k). f in cycles/symbol, |f| <= MAX_CFO. MACs are
analytic, in est3's conventions (complex multiply 4, FFT 2 n log2 n, exponential 8, |X|^2 2 per bin, a full FFT is
charged even when most inputs are zeros).

CFO estimators
    ml128   est3 ML direct (FFT 512 + 2 Newton) on the 128-symbol preamble (pre128)
    mm128   est3 M&M (polar_ber_experiment.bench_estimate("mm")) on the preamble
    ml      ML over arbitrary known positions: Lambda(f) = |sum_k z_k e^{-j 2 pi f n_k}|^2; zero-filled z on the span of
            kidx, FFT (power of 2 >= 4 x span), the ML_CAND highest local maxima inside |f| <= MAX_CFO (the coarse lobes
            1/D apart for split64), 2 Newton steps on each (est3.newton on the exact positions), keep the largest Lambda
    rb      Rife-Boorstyn (Griebel et al. 2021, DA-KS, Eqs. 2-5, 15-16): FFT (power of 2 >= 4 x K) of z placed at the
            known burst positions, zeros at the data, peak inside |f| <= MAX_CFO (+ 1 bin), parabolic interpolation on
            |X|, then RB_NEWTON Newton steps (0 = the faithful DVB-RCS2 chain)
    nda4    4th-power NDA over the whole burst (Griebel Eqs. 11-12): FFT (power of 2 >= 4 x K) of r^4, peak inside
            |4f| <= 4 MAX_CFO (+ 1 bin), parabolic interpolation, f0 = nu / 4; refined by ML on the known symbols
            restricted to f0 +- NDA_WIN / D (D = distance of the first and last field centres, the known-symbol lobe
            spacing 1/D): NDA_GRID-point grid, 2 Newton steps, clipped to the window. The 4-fold phase ambiguity
            (Eq. 13-14) needs no step: the LS gain on the known symbols absorbs any phase
  est5 (deployed systems, expected_est5.md; "in its lobe" = the peak of the zero-filled known-symbol FFT restricted to
  f_c +- 1 / (2 D_lobe) and |f| <= MAX_CFO (+ 1 bin), parabolic interpolation, as rb)
    vde     VDE-SAT: ML (ml, 1 candidate) on the 27-symbol syncword -> f_c, then rb over all 66 known in its lobe
            (D_lobe = 27)
    mmml    DVB-S2 style: M&M (Mengali-Morelli 1997, est3's weights, M = N / 2, numpy) on the 90-symbol PL header -> f_c,
            then joint ML over header + pilot block (zero-filled FFT on the span, nfft_for(span)) in its lobe
            (D_lobe = 575), ML_ITERS Newton steps
    nda4uw  ViaSat (US 7653150 + US 8243859): FFT (nfft_for(K)) of r^4 over the burst, the UW_TOP largest local maxima
            inside |4f| <= 4 MAX_CFO (+ 1 bin), parabolic interpolation, f_i = nu_i / 4; each candidate checked on the
            16-symbol UW: pick argmax_i |U(f_i)|^2 / (Nk s2) + UW_W |X4_i|^2 / mean_in-range |X4|^2 (U(f) = sum_k z_k
            e^{-j 2 pi f n_k}; the two noise-normalised energies: the patent's weighted joint frequency + UW metric);
            the pi/2 ambiguity is absorbed by the LS gain on the UW
    nda4rb  sparse pilots 1/32 (400ZR-inspired): 4th-power coarse f_c (the nda4 FFT step), then rb on the 33 pilots
            in its lobe (D_lobe = 32)
    lag     Wi-Fi style: coarse f_c = arg(sum_n r[n + 16] r*[n]) / (2 pi 16) over the 8 x 16 repeated preamble (range
            1/32), fine f_f = arg(sum_{n < 64} r[n + 64] r*[n]) / (2 pi 64) (range 1/128), f = f_f + round((f_c - f_f)
            64) / 64 (the deployed coarse / fine pair; the repeats make r[n + D] r*[n] = z[n + D] z*[n])
    hyb3    US 7590199 on prepost16: S(nu) = log|FFT(z zero-filled)|(nu) + HYB_W log|FFT(r^4)|(4 nu) (both nfft_for(K)),
            the HYB_TOP largest local maxima inside |nu| <= MAX_CFO (+ 1 bin), parabolic interpolation on S: f_hat =
            the best, the other 2 are extra hypotheses of the CRC search (run_bler, with their own lobes)
    rb is also the estimator of ccsds8, dmrs7 and mil110 (R-B over all known symbols, full range)
  faithful variants (expected_variants.md; hyb3 on pre48, mmml on dvbh90 / sof26 (M&M on the header, ML in f_c +-
  1 / (2 Nh)), rb on mil110f / cc131, ml on asm32 are the generic chains above)
    nda4pk  ViaSat US 7653150: FFT of r^4 over the burst with the patent's 2x zero padding (power of 2 >= 2 K), the
            single largest bin k inside |4f| <= 4 MAX_CFO (+ 1 bin), nu = the |X|-weighted mean of bins k-1, k, k+1,
            f = nu / 4 (phase: model x4)
    lag320  Wi-Fi legacy (wifi320): coarse f_c = arg(sum r[n + 16] r*[n]) / (2 pi 16) over the 160-symbol L-STF (144
            products), fine f_f = arg(sum_{n < 64} r[n + 64] r*[n]) / (2 pi 64) over the 2 x 64 L-LTF symbols after
            its 32 guard, f = f_f + round((f_c - f_f) 64) / 64 (the real chip's coarse / fine pair)
  ARS 2021 (Griebel et al., lit_ars2021.md section 6) on rcs13
    rb4096, rb2048, rb2048n   rb with the FFT size 4096 / 2048 (+ 1 Newton step: rb2048n), peak inside |nu| <= MAX_CFO
            + 1/N
    rb2048f the paper's DA-KS as published: FFT 2048, peak over ALL bins (Eq. 4: |nu| <= 1/2), parabolic Eq. 15
Phase models (complex gain per data symbol at a CFO hypothesis fh, from y_k = r[n_k] e^{-j 2 pi fh (n_k + D)} ks_k*)
    const   est3.gain_phase: g = sum_k y_k / sum_k |ks_k|^2 on all known symbols (one gain per burst)
    interp2, track   the phase-tracking models (split64: 2 fields; rcs13: 55 fields), in one of two modes:
      kalman (default, 2026-11-15 after e4-smoke: W = 9 single pilots left ~0.37 rad at -4 dB, 113/800 vs 1/800):
            field phasors P_j = sum_{k in field j} y_k, energies E_j = sum |ks|^2; random-walk phase theta_j at the field
            centres c_j, process noise q (c_{j+1} - c_j), q = 2 pi pn per symbol (the TRUE linewidth: a best-tuned
            competitor), linearised about the constant LS phase phi0 = arg sum_j P_j (one pass, KALMAN_ITERS = 1):
            measurement u_j = Im(P_j e^{-j phi0}) / (a0 E_j), a0 = |sum_j P_j| / sum_j E_j, variance
            sigma^2 / (2 a0^2 E_j) (KALMAN_MEAS 'im'; 'angle': u_j = arg(P_j e^{-j phi0}), variance sigma^2 / (2 E_j));
            diffuse prior; Kalman filter + Rauch-Tung-Striebel smoother, phi = phi0 + theta_s; linear interpolation of
            phi between the field centres to every data symbol, amplitude a = |Re(sum_j P_j e^{-j phi_j})| / sum_j E_j.
            q = 0 (pn = 0) returns the constant LS gain exactly; with 'im' the q -> 0 limit of the smoother is the same
            (sum_j Im(P_j e^{-j phi0}) = 0). Check at -4 dB (rcs13, 400 noisy symbol-rate bursts, rms phase error):
            pn 1e-5 / 1e-4 / 3e-4: const 0.155 / 0.371 / 0.657, im 0.143 / 0.249 / 0.423, angle 0.158 / 0.279 / 0.424;
            the first sliding window W = 9: 0.395 / 0.406 / 0.418 and 0.380 at pn = 0 (const 0.104)
      sw (the first version, --track sw): interp2 = per-block LS gains g_1, g_2, phase(n) = arg g_1 + angle(g_2 g_1*)
            (n - c_1) / (c_2 - c_1), amplitude (|g_1| + |g_2|) / 2; track = sliding window of W fields
            S_j = sum_{|i - j| <= W // 2} P_i (truncated at the ends), phi_j = unwrap_j(arg S_j), linear interpolation,
            a = Re(sum_j P_j e^{-j phi_j}) / sum |ks|^2 (phasors smoothed BEFORE arg, the ESA PA-SWI form)
    blocks  per-field LS phase arg P_j, unwrapped, linear interpolation between the field centres, amplitude
            |Re(sum_j P_j e^{-j phi_j})| / sum |ks|^2 (= track mode sw with W = 1; CCSDS 130.11 5.6 / DVB-S2 TR C.6.1;
            independent of --track)
    eq17    Griebel Eq. 17 / 20 (sign-corrected): k = round(fh N), Delta = fh N - k (N = EQ17_NFFT; the estimator's
            bin and parabolic offset), X_j = sum_k z_k e^{-j 2 pi j n_k / N} at the bins k-1, k, k+1 (the estimator's
            FFT bins; recomputed here as 3 DFT bins), phi = arg X_k + |Delta| wrap(arg X_nb - arg X_k) (nb = k - 1 if
            Delta < 0 else k + 1; the printed Eq. 17 has the opposite sign), referred to l = 0 and converted to ours by
            - 2 pi fh DELAY_SYM; amplitude |X(k~)| / sum |ks|^2 with Eq. 20 X(k~) = X_k + |Delta| (X_nb - X_k);
            one gain per burst
    x4      ViaSat US 7653150: phase from the 4th power over the whole burst, theta = arg(-Y4) / 4 with Y4 = sum_n (r[n]
            e^{-j 2 pi fh (n + D)})^4 (QPSK s^4 = -1: the 4th-power bin at 4 fh, referred to our time origin), the
            pi/2 quadrant q maximising Re(U e^{-j (theta + q pi/2)}) on the UW (U = sum_k y_k), amplitude
            |Re(U e^{-j phi})| / sum |ks|^2; one gain per burst
    genie   g_n = e^{j (ph + phs_n)} (the true phase incl. the phase-noise path, the true gain 1), at the true f
Lobes (2-field layouts split64, prepost16): the known-symbol likelihood has lobes 1/D_lobe apart (D_lobe = distance of
the two block centres: 1088, 1040); the receiver's CRC search lets the decoder choose among them (run_bler --lobes).
noncoherent(): the per-block noncoherent estimate argmax sum_b |Z_b(f)|^2 (measurement only: lobe-pick comparison)
"""
import numpy as np

from est3 import estimators as E3
from est4 import common as C

FFT_MACS = E3.FFT_MACS
ML_CAND, ML_ITERS = 3, 2                       # ml: lobes refined, Newton steps per lobe
RB_NEWTON = 0                                  # rb: Newton steps after the parabolic interpolation (0 = faithful)
NDA_WIN, NDA_GRID, NDA_ITERS = 0.25, 17, 2     # nda4: refinement window (x 1/D), its grid points, Newton steps
TRACK_W = 9                                    # track, mode sw: sliding window in fields (odd)
TRACK_MODE = "kalman"                          # interp2 / track: 'kalman' (RTS smoother) or 'sw' (the first version)
KALMAN_ITERS = 1                               # linearisations about the constant phase (more passes re-smooth noise:
                                               # rms phase error up at every pn in the 400-burst -4 dB check)
KALMAN_MEAS = "im"                             # field measurement: 'im' (linearised) or 'angle' (arg of the residual)
NC_NFFT = 512                                  # noncoherent per-block estimate (measurement only)
UW_TOP, UW_W = 32, 1.0                         # nda4uw: 4th-power peaks checked on the UW, weight of the 4th-power term
HYB_TOP, HYB_W = 3, 1.0                        # hyb3: CFO candidates, weight of the 4th-power log spectrum
RB_ARS = {"rb4096": (4096, 0, C.MAX_CFO), "rb2048": (2048, 0, C.MAX_CFO), "rb2048n": (2048, 1, C.MAX_CFO),
          "rb2048f": (2048, 0, 0.5)}           # ARS variants: (nfft, Newton steps, peak range |nu| <=)
EQ17_NFFT = 2048                               # eq17: the FFT of Griebel faithful
KP = 32                                        # decoder cores (est3.plots.KP: the standard MACs-per-core model)
PAR_DEC = KP // 8                              # CA-SCL-8 decodes that fit on the cores at once


def nfft_for(n):
    """Smallest power of 2 >= 4 n."""
    return 1 << int(np.ceil(np.log2(4 * n)))


def _fft_peak(x, nfft, fmax):
    """Peak of |FFT_nfft(x)| inside |nu| <= fmax + 1/nfft, parabolic interpolation on |X| (Griebel Eq. 15): nu (B,)."""
    X = np.abs(np.fft.fft(x, nfft, axis=1))
    nu = np.fft.fftfreq(nfft)
    k = np.where((np.abs(nu) <= fmax + 1.0 / nfft)[None], X, -1.0).argmax(1)
    rows = np.arange(len(x))
    nb = X[rows[:, None], (k[:, None] + np.array([-1, 0, 1])[None]) % nfft]
    den = nb[:, 0] - 2 * nb[:, 1] + nb[:, 2]                          # as est3.estimators.refine("parabolic")
    off = np.clip(np.where(den < 0, 0.5 * (nb[:, 0] - nb[:, 2]) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
    return nu[k] + off / nfft


def _parab(X, k):
    """Parabolic-interpolation offset (bins, clipped to +-0.5) of X (B, nfft) at the peak bins k (B,) or (B, n), as
    _fft_peak (also on a log spectrum)."""
    nfft = X.shape[1]
    rows = np.arange(len(X)).reshape((-1,) + (1,) * (k.ndim - 1))
    a, b, c = X[rows, (k - 1) % nfft], X[rows, k], X[rows, (k + 1) % nfft]
    den = a - 2 * b + c
    return np.clip(np.where(den < 0, 0.5 * (a - c) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)


def _win_mask(nfft, fc, half):
    """Bins (B, nfft) inside fc +- (half + 1/nfft) and |nu| <= MAX_CFO + 1/nfft (fc (B,) clipped to the range first)."""
    nu = np.fft.fftfreq(nfft)
    fc = np.clip(fc, -C.MAX_CFO, C.MAX_CFO)
    return (np.abs(nu[None] - fc[:, None]) <= half + 1.0 / nfft) & (np.abs(nu) <= C.MAX_CFO + 1.0 / nfft)[None]


def _peak_in(X, mask):
    """Peak of X (B, nfft) inside mask (B, nfft) + parabolic interpolation: nu (B,)."""
    k = np.where(mask, X, -np.inf).argmax(1)
    return np.fft.fftfreq(X.shape[1])[k] + _parab(X, k) / X.shape[1]


def _top_in(X, mask, n):
    """Bins (B, n) of the n largest local maxima of X inside mask, in descending order."""
    loc = (X >= np.roll(X, 1, 1)) & (X >= np.roll(X, -1, 1)) & mask
    return np.argsort(-np.where(loc, X, -np.inf), 1, kind="stable")[:, :n]


def _rb_win(r, ks, kidx, fc, half, nfft=None):
    """rb restricted to the lobe fc +- half: |FFT| of z placed at the known burst positions, peak in _win_mask."""
    K = r.shape[1]
    nfft = nfft or nfft_for(K)
    x = np.zeros((len(r), K), complex)
    x[:, kidx] = r[:, kidx] * np.conj(ks)
    return _peak_in(np.abs(np.fft.fft(x, nfft, axis=1)), _win_mask(nfft, fc, half))


# =====================================================================
# CFO estimators
# =====================================================================

def ml128(r, ks, kidx):
    return E3.ml_direct(r[:, kidx], ks)


def mm128(r, ks, kidx, snr_db):
    return E3.mm(r[:, kidx], ks, snr_db)


def ml_known(r, ks, kidx, nfft=None, cand=ML_CAND, iters=ML_ITERS):
    z = r[:, kidx] * np.conj(ks)
    n0, span = kidx.min(), kidx.max() - kidx.min() + 1
    nfft = nfft or nfft_for(span)
    x = np.zeros((len(z), span), complex)
    x[:, kidx - n0] = z
    lam = np.abs(np.fft.fft(x, nfft, axis=1)) ** 2
    nu = np.fft.fftfreq(nfft)
    lam = np.where((np.abs(nu) <= C.MAX_CFO + 1.0 / nfft)[None], lam, -1.0)
    loc = (lam >= np.roll(lam, 1, 1)) & (lam >= np.roll(lam, -1, 1))
    top = np.argsort(-np.where(loc, lam, -1.0), 1)[:, :cand]
    t = kidx.astype(float)
    fc = np.stack([E3.newton(z[:, :, None], nu[top[:, i]], iters, t=t) for i in range(cand)], 1)
    val = np.stack([E3._lam(z[:, :, None], fc[:, i], t - t.mean()) for i in range(cand)], 1)
    return fc[np.arange(len(z)), val.argmax(1)]


def rife_boorstyn(r, ks, kidx, nfft=None, iters=RB_NEWTON, fmax=None):
    K = r.shape[1]
    nfft = nfft or nfft_for(K)
    z = r[:, kidx] * np.conj(ks)
    x = np.zeros((len(z), K), complex)
    x[:, kidx] = z
    f = _fft_peak(x, nfft, C.MAX_CFO if fmax is None else fmax)
    return E3.newton(z[:, :, None], f, iters, t=kidx.astype(float)) if iters else f


def nda4(r, ks, L, nfft=None, win=NDA_WIN, grid=NDA_GRID, iters=NDA_ITERS):
    K = r.shape[1]
    nfft = nfft or nfft_for(K)
    f0 = _fft_peak(r ** 4, nfft, 4 * C.MAX_CFO) / 4
    kidx = L["known_idx"]
    D = L["centres"][-1] - L["centres"][0]
    W = win / D
    z = r[:, kidx] * np.conj(ks)
    t = kidx - kidx.mean()
    g = f0[:, None] + np.linspace(-W, W, grid)[None]                  # (B, G)
    lam = np.abs(np.einsum("bk,bgk->bg", z, np.exp(-2j * np.pi * g[:, :, None] * t[None, None]))) ** 2
    f1 = g[np.arange(len(z)), lam.argmax(1)]
    f1 = E3.newton(z[:, :, None], f1, iters, t=kidx.astype(float))
    return np.clip(f1, f0 - W, f0 + W)


def vde(r, ks, L):
    kidx, ns = L["known_idx"], L["fsize"][0]                         # field 0 = the syncword
    f0 = ml_known(r, ks[:, :ns], kidx[:ns], cand=1)
    return _rb_win(r, ks, kidx, f0, 0.5 / C.lobe_D(L["name"]))


def mm_known(z):
    """Mengali-Morelli 1997 on contiguous z (B, N), M = N // 2 (est3 / train_snr_nn.mm_estimate weights, float64):
    R(m) = mean_n z[n] z*[n - m], f = sum_m w_m arg(R(m) R*(m - 1)) / (2 pi)."""
    N = z.shape[1]
    M = N // 2
    R = np.stack([np.sum(z[:, m:] * np.conj(z[:, :N - m]), 1) / (N - m) for m in range(1, M + 1)], 1)
    dphi = np.angle(np.concatenate([R[:, :1], R[:, 1:] * np.conj(R[:, :-1])], 1))
    m = np.arange(1, M + 1)
    w = 3 * ((N - m) * (N - m + 1) - M * (N - M)) / (M * (4 * M ** 2 - 6 * M * N + 3 * N ** 2 - 1))
    return dphi @ w / (2 * np.pi)


def mmml(r, ks, L, iters=ML_ITERS):
    kidx, nh = L["known_idx"], L["fsize"][0]                         # field 0 = the PL header
    z = r[:, kidx] * np.conj(ks)
    f0 = mm_known(z[:, :nh])
    n0, span = kidx.min(), kidx.max() - kidx.min() + 1
    nfft = nfft_for(span)
    x = np.zeros((len(z), span), complex)
    x[:, kidx - n0] = z
    lam = np.abs(np.fft.fft(x, nfft, axis=1)) ** 2
    k = np.where(_win_mask(nfft, f0, 0.5 / C.lobe_D(L["name"])), lam, -np.inf).argmax(1)
    return E3.newton(z[:, :, None], np.fft.fftfreq(nfft)[k], iters, t=kidx.astype(float))


def nda4uw(r, ks, L, snr_db, top=UW_TOP, w=UW_W):
    K, kidx = r.shape[1], L["known_idx"]
    nfft = nfft_for(K)
    X = np.abs(np.fft.fft(r ** 4, nfft, axis=1))
    nu = np.fft.fftfreq(nfft)
    ins = (np.abs(nu) <= 4 * C.MAX_CFO + 1.0 / nfft)[None]
    k = _top_in(X, ins, top)                                          # (B, top)
    rows = np.arange(len(r))[:, None]
    fc = (nu[k] + _parab(X, k) / nfft) / 4
    z = r[:, kidx] * np.conj(ks)
    t = kidx - kidx.mean()
    U = np.abs(np.einsum("bk,bnk->bn", z, np.exp(-2j * np.pi * fc[:, :, None] * t[None, None]))) ** 2
    met = U / (L["nk"] * 10 ** (-snr_db / 10)) + w * X[rows, k] ** 2 / np.mean(X[:, ins[0]] ** 2, 1)[:, None]
    return fc[rows[:, 0], met.argmax(1)]


def nda4rb(r, ks, L):
    K = r.shape[1]
    f0 = _fft_peak(r ** 4, nfft_for(K), 4 * C.MAX_CFO) / 4
    return _rb_win(r, ks, L["known_idx"], f0, 0.5 / C.lobe_D(L["name"]))


def lag(r, L, rep=C.WIFI_REP, fine=C.WIFI_FINE):
    k0 = L["known_idx"][0]
    p = r[:, k0:k0 + L["nk"]]                                         # the contiguous repeated preamble
    fc = np.angle(np.sum(p[:, rep:] * np.conj(p[:, :-rep]), 1)) / (2 * np.pi * rep)
    ff = np.angle(np.sum(p[:, fine:2 * fine] * np.conj(p[:, :fine]), 1)) / (2 * np.pi * fine)
    return ff + np.round((fc - ff) * fine) / fine


def nda4pk(r):
    K = r.shape[1]
    nfft = 1 << int(np.ceil(np.log2(2 * K)))                          # the patent's 2x zero padding (512 -> 1024)
    X = np.abs(np.fft.fft(r ** 4, nfft, axis=1))
    nu = np.fft.fftfreq(nfft)
    k = np.where((np.abs(nu) <= 4 * C.MAX_CFO + 1.0 / nfft)[None], X, -1.0).argmax(1)
    d = np.arange(-1, 2)
    w = X[np.arange(len(r))[:, None], (k[:, None] + d[None]) % nfft]  # |X| of bins k-1, k, k+1
    return (nu[k] + np.sum(w * d[None], 1) / np.sum(w, 1) / nfft) / 4


def lag320(r, L, rep=C.WIFI_REP, fine=C.WIFI_FINE):
    k0 = L["known_idx"][0]
    s = r[:, k0:k0 + C.WIFI_STF]                                      # L-STF (10 x 16)
    a = k0 + C.WIFI_STF + C.WIFI_GI
    lt = r[:, a:a + 2 * fine]                                         # the 2 L-LTF symbols after the guard
    fc = np.angle(np.sum(s[:, rep:] * np.conj(s[:, :-rep]), 1)) / (2 * np.pi * rep)
    ff = np.angle(np.sum(lt[:, fine:] * np.conj(lt[:, :fine]), 1)) / (2 * np.pi * fine)
    return ff + np.round((fc - ff) * fine) / fine


def hyb3(r, ks, L, top=HYB_TOP, w=HYB_W):
    """(B, top) CFO candidates, best first."""
    K = r.shape[1]
    nfft = nfft_for(K)
    x = np.zeros((len(r), K), complex)
    x[:, L["known_idx"]] = r[:, L["known_idx"]] * np.conj(ks)
    tiny = 1e-300
    S = np.log(np.abs(np.fft.fft(x, nfft, axis=1)) + tiny)
    S = S + w * np.log(np.abs(np.fft.fft(r ** 4, nfft, axis=1))[:, (4 * np.arange(nfft)) % nfft] + tiny)
    nu = np.fft.fftfreq(nfft)
    k = _top_in(S, (np.abs(nu) <= C.MAX_CFO + 1.0 / nfft)[None], top)
    return nu[k] + _parab(S, k) / nfft


def candidates(est, r, ks, L, snr_db, f):
    """(f_hat (B,), extra CFO candidates (B, n) or None): hyb3 returns its 2 other candidates, the rest None."""
    if est == "hyb3":
        c = hyb3(r, ks, L)
        return c[:, 0], c[:, 1:]
    return estimate(est, r, ks, L, snr_db, f), None


def estimate(est, r, ks, L, snr_db, f):
    """CFO (B,) of estimator est on the burst MF output r (B, K); f (the true CFO) only for the genie."""
    kidx = L["known_idx"]
    if est == "genie":
        return f.copy()
    if est == "vde":
        return vde(r, ks, L)
    if est == "mmml":
        return mmml(r, ks, L)
    if est == "nda4uw":
        return nda4uw(r, ks, L, snr_db)
    if est == "nda4rb":
        return nda4rb(r, ks, L)
    if est == "lag":
        return lag(r, L)
    if est == "hyb3":
        return hyb3(r, ks, L)[:, 0]
    if est == "nda4pk":
        return nda4pk(r)
    if est == "lag320":
        return lag320(r, L)
    if est in RB_ARS:
        n, it, fm = RB_ARS[est]
        return rife_boorstyn(r, ks, kidx, nfft=n, iters=it, fmax=fm)
    if est == "ml128":
        return ml128(r, ks, kidx)
    if est == "mm128":
        return mm128(r, ks, kidx, snr_db)
    if est == "ml":
        return ml_known(r, ks, kidx)
    if est == "rb":
        return rife_boorstyn(r, ks, kidx)
    if est == "nda4":
        return nda4(r, ks, L)
    raise ValueError(est)


def noncoherent(r, ks, L, nfft=NC_NFFT):
    """Per-block noncoherent CFO estimate (measurement only): argmax_f sum_b |FFT_nfft(z_b)|^2 inside |f| <= MAX_CFO
    (+ 1 bin), parabolic interpolation on sqrt (as est3.dvbs2_blocks' coarse stage). Phase-free across the blocks, so
    it has no 1/D_lobe ambiguity, but only the resolution of one block."""
    z = r[:, L["known_idx"]] * np.conj(ks)
    lam = 0.0
    for a, n in zip(L["fstart"], L["fsize"]):
        lam = lam + np.abs(np.fft.fft(z[:, a:a + n], nfft, axis=1)) ** 2
    X = np.sqrt(lam)
    nu = np.fft.fftfreq(nfft)
    k = np.where((np.abs(nu) <= C.MAX_CFO + 1.0 / nfft)[None], X, -1.0).argmax(1)
    rows = np.arange(len(z))
    nb = X[rows[:, None], (k[:, None] + np.array([-1, 0, 1])[None]) % nfft]
    den = nb[:, 0] - 2 * nb[:, 1] + nb[:, 2]
    off = np.clip(np.where(den < 0, 0.5 * (nb[:, 0] - nb[:, 2]) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
    return nu[k] + off / nfft


def est_macs(est, L):
    """Real MACs of the CFO estimator per burst.
    ml128  est3.ml_direct_macs() = 4 x 128 + FFT 512 + |X|^2 + 2 Newton x (3 sums x 4 x 128 + 8 x 128 exponentials)
    mm128  est3.MM_MACS
    ml     4 Nk (z) + FFT(nfft) + 2 nfft (|X|^2) + cand x [iters x (12 Nk + 8 Nk) + (4 Nk + 8 Nk) (final Lambda)]
    rb     4 Nk + FFT(nfft) + 2 nfft + 10 (parabolic) + RB_NEWTON x 20 Nk
    nda4   8 K (r^4: 2 complex squarings) + FFT(nfft) + 2 nfft + 10 + 4 Nk (z) + 8 Nk (twiddles at f0; the grid offsets
           e^{-j 2 pi delta_g n_k} are fixed) + G (4 Nk + 2) (grid) + iters x 20 Nk
    vde    4 Nk (z, once) + syncword ml with 1 candidate: FFT(nfft_for(Ns)) + 2 nfft + ML_ITERS x 20 Ns + 12 Ns
           + rb over all known: FFT(nfft_for(K)) + 2 nfft + 10                       (Ns = 27)
    mmml   4 Nk + M&M on the Nh-symbol header: 4 sum_{m=1..M} (Nh - m) (lags) + 4 M (R(m) R*(m-1)), as est3's
           MM_MACS = 24,704 at N = 128 + joint ML: FFT(nfft_for(span)) + 2 nfft + ML_ITERS x 20 Nk   (Nh = 90, M = 45)
    nda4uw 8 K (r^4) + FFT(nfft) + 2 nfft (|X|^2) + nb (floor mean over the nb in-range bins) + UW_TOP x 10 (parabolic)
           + 4 Nk (z) + UW_TOP x (8 Nk (twiddles) + 4 Nk (correlation) + 2 (|U|^2) + 4 (metric))
    nda4rb 8 K + FFT(nfft) + 2 nfft + 10 (4th-power coarse) + 4 Nk + FFT(nfft) + 2 nfft + 10 (rb in the lobe)
    lag    4 (Nk - 16) (coarse lag products) + 4 x 64 (fine) + 2 x 20 (two arguments) + 4 (lobe pick)
    hyb3   4 Nk + FFT(nfft) + 2 nfft (DA) + 8 K + FFT(nfft) + 2 nfft (4th power) + nb x (2 x 8 (two logs, charged as
           exponentials) + 2 (weight, add)) + HYB_TOP x 10 (parabolic)      (nb = in-range bins, nfft = nfft_for(K))
    nda4pk 8 K (r^4) + FFT(n) + 2 n (|X|) + 10 (3-bin weighted mean)    (n = power of 2 >= 2 K: 4096 on viasat16)
    lag320 4 (160 - 16) (coarse lag products on the L-STF) + 4 x 64 (fine, L-LTF) + 2 x 20 (two arguments) + 4
    rb4096 / rb2048 / rb2048f / rb2048n   4 Nk + FFT(N) + 2 N + 10 (+ 20 Nk for the Newton step): rcs13 106,970 /
           49,626 / 49,626 / 51,946 (lit_ars2021.md section 6)
    genie  0"""
    nk, K, kidx = L["nk"], L["K"], L["known_idx"]
    if est in RB_ARS:
        n, it, _ = RB_ARS[est]
        return 4 * nk + FFT_MACS(n) + 2 * n + 10 + it * 20 * nk
    nb = lambda n, fmax: 2 * int(np.ceil(fmax * n)) + 3                # in-range bins (+ 1 bin each side)
    if est == "genie":
        return 0
    if est == "vde":
        ns, n, n1 = L["fsize"][0], nfft_for(L["fsize"][0]), nfft_for(K)
        return 4 * nk + FFT_MACS(n) + 2 * n + ML_ITERS * 20 * ns + 12 * ns + FFT_MACS(n1) + 2 * n1 + 10
    if est == "mmml":
        nh = L["fsize"][0]
        M = nh // 2
        n = nfft_for(kidx.max() - kidx.min() + 1)
        return 4 * nk + 4 * sum(nh - m for m in range(1, M + 1)) + 4 * M + FFT_MACS(n) + 2 * n + ML_ITERS * 20 * nk
    if est == "nda4uw":
        n = nfft_for(K)
        return (8 * K + FFT_MACS(n) + 2 * n + nb(n, 4 * C.MAX_CFO) + UW_TOP * 10 + 4 * nk
                + UW_TOP * (12 * nk + 6))
    if est == "nda4rb":
        n = nfft_for(K)
        return 8 * K + 4 * nk + 2 * (FFT_MACS(n) + 2 * n + 10)
    if est == "lag":
        return 4 * (nk - C.WIFI_REP) + 4 * C.WIFI_FINE + 2 * 20 + 4
    if est == "hyb3":
        n = nfft_for(K)
        return 4 * nk + 8 * K + 2 * (FFT_MACS(n) + 2 * n) + nb(n, C.MAX_CFO) * 18 + HYB_TOP * 10
    if est == "nda4pk":
        n = 1 << int(np.ceil(np.log2(2 * K)))
        return 8 * K + FFT_MACS(n) + 2 * n + 10
    if est == "lag320":
        return 4 * (C.WIFI_STF - C.WIFI_REP) + 4 * C.WIFI_FINE + 2 * 20 + 4
    if est == "ml128":
        return E3.ml_direct_macs()
    if est == "mm128":
        return E3.MM_MACS
    if est == "ml":
        n = nfft_for(kidx.max() - kidx.min() + 1)
        return 4 * nk + FFT_MACS(n) + 2 * n + ML_CAND * (ML_ITERS * 20 * nk + 12 * nk)
    if est == "rb":
        n = nfft_for(K)
        return 4 * nk + FFT_MACS(n) + 2 * n + 10 + RB_NEWTON * 20 * nk
    if est == "nda4":
        n = nfft_for(K)
        return 8 * K + FFT_MACS(n) + 2 * n + 10 + 12 * nk + NDA_GRID * (4 * nk + 2) + NDA_ITERS * 20 * nk
    raise ValueError(est)


# =====================================================================
# Phase models: complex gain (B,) or (B, 1024) at the data symbols for the hypothesis fh (B,)
# =====================================================================

def _y(r, ks, L, fh):
    """De-rotated known symbols times conj(ks): (B, Nk)."""
    kidx = L["known_idx"]
    return r[:, kidx] * np.exp(-2j * np.pi * fh[:, None] * (kidx + C.DELAY_SYM)[None]) * np.conj(ks)


def gain_const(r, ks, L, fh):
    return np.sum(_y(r, ks, L, fh), 1) / np.sum(np.abs(ks) ** 2, 1)


def _fields(y, ks, L):
    """Field phasors P (B, F) and field energies (B, F)."""
    return np.add.reduceat(y, L["fstart"], axis=1), np.add.reduceat(np.abs(ks) ** 2, L["fstart"], axis=1)


def _interp(phi, L):
    j, w = L["ij"], L["iw"]
    return (1 - w)[None] * phi[:, j] + w[None] * phi[:, j + 1]


def gain_interp2(r, ks, L, fh):
    assert len(L["fstart"]) == 2, L["name"]
    P, e = _fields(_y(r, ks, L, fh), ks, L)
    g = P / e
    phi = np.stack([np.angle(g[:, 0]), np.angle(g[:, 0]) + np.angle(g[:, 1] * np.conj(g[:, 0]))], 1)
    a = 0.5 * (np.abs(g[:, 0]) + np.abs(g[:, 1]))
    return a[:, None] * np.exp(1j * _interp(phi, L))


def gain_track(r, ks, L, fh, W=TRACK_W):
    assert W % 2 == 1 and len(L["fstart"]) >= 2, (W, L["name"])
    P, e = _fields(_y(r, ks, L, fh), ks, L)
    F, h = P.shape[1], W // 2
    cs = np.concatenate([np.zeros((len(P), 1), complex), np.cumsum(P, 1)], 1)
    j = np.arange(F)
    S = cs[:, np.minimum(j + h + 1, F)] - cs[:, np.maximum(j - h, 0)]
    phi = np.unwrap(np.angle(S), axis=1)
    a = np.real(np.sum(P * np.exp(-1j * phi), 1)) / np.sum(e, 1)
    return np.abs(a)[:, None] * np.exp(1j * _interp(phi, L))


def rts(u, R, dc, q):
    """Kalman filter + Rauch-Tung-Striebel smoother of a scalar random walk theta_{j+1} = theta_j + w_j,
    var w_j = q dc_j, from measurements u_j = theta_j + v_j, var v_j = R_j (u, R: (B, F); dc: (F - 1,)); diffuse prior.
    Returns the smoothed theta (B, F)."""
    B, F = u.shape
    xp, Pp, xf, Pf = (np.empty((B, F)) for _ in range(4))
    x, P = np.zeros(B), np.full(B, 1e12)
    for j in range(F):
        if j:
            P = P + q * dc[j - 1]
        xp[:, j], Pp[:, j] = x, P
        K = P / (P + R[:, j])
        x, P = x + K * (u[:, j] - x), K * R[:, j]                     # = (1 - K) P without the diffuse cancellation
        xf[:, j], Pf[:, j] = x, P
    xs = xf.copy()
    for j in range(F - 2, -1, -1):
        xs[:, j] = xf[:, j] + Pf[:, j] / Pp[:, j + 1] * (xs[:, j + 1] - xp[:, j + 1])
    return xs


def gain_kalman(r, ks, L, fh, q, s2, iters=KALMAN_ITERS, meas=None):
    """Phase tracking by the RTS smoother on the field phases (module docstring, mode kalman); q = 2 pi pn per symbol,
    s2 the complex noise variance at the MF output. q = 0: the constant LS gain (exact). meas 'angle':
    u_j = arg(P_j e^{-j phi_j}); 'im': u_j = Im(P_j e^{-j phi_j}) / (a E_j), a = |sum P| / sum E (the linearised,
    Gaussian measurement: its q -> 0 limit is the constant LS phase exactly)."""
    meas = meas or KALMAN_MEAS
    if q <= 0:
        return gain_const(r, ks, L, fh)[:, None]
    assert len(L["fstart"]) >= 2, L["name"]
    P, e = _fields(_y(r, ks, L, fh), ks, L)
    phi = np.repeat(np.angle(np.sum(P, 1))[:, None], P.shape[1], 1)
    a0 = np.abs(np.sum(P, 1)) / np.sum(e, 1)
    R = s2 / (2 * e) / a0[:, None] ** 2                                 # both forms: var of arg / Im-scaled = s2 / (2 a^2 E)
    dc = np.diff(L["centres"])
    for _ in range(iters):
        v = P * np.exp(-1j * phi)
        u = np.angle(v) if meas == "angle" else v.imag / (a0[:, None] * e)
        phi = phi + rts(u, R, dc, q)
    a = np.abs(np.real(np.sum(P * np.exp(-1j * phi), 1))) / np.sum(e, 1)
    return a[:, None] * np.exp(1j * _interp(phi, L))


def gain_eq17(r, ks, L, fh, nfft=EQ17_NFFT):
    kidx = L["known_idx"]
    z = r[:, kidx] * np.conj(ks)
    k = np.round(fh * nfft)
    dl = fh * nfft - k
    nb = np.where(dl < 0, k - 1, k + 1)
    X = lambda j: np.sum(z * np.exp(-2j * np.pi * j[:, None] * kidx[None] / nfft), 1)
    Xk, Xn = X(k), X(nb)
    a = np.abs(dl)
    phi = np.angle(Xk) + a * np.angle(Xn * np.conj(Xk)) - 2 * np.pi * fh * C.DELAY_SYM
    amp = np.abs(Xk + a * (Xn - Xk)) / np.sum(np.abs(ks) ** 2, 1)
    return amp * np.exp(1j * phi)


def gain_x4(r, ks, L, fh):
    n = np.arange(r.shape[1])
    y4 = np.sum((r * np.exp(-2j * np.pi * fh[:, None] * (n + C.DELAY_SYM)[None])) ** 4, 1)
    phi = np.angle(-y4) / 4                                           # QPSK: s^4 = -1
    U = np.sum(_y(r, ks, L, fh), 1)                                   # the UW: quadrant only
    phi = phi + np.round(np.angle(U * np.exp(-1j * phi)) / (np.pi / 2)) * (np.pi / 2)
    return np.abs(np.real(U * np.exp(-1j * phi))) / np.sum(np.abs(ks) ** 2, 1) * np.exp(1j * phi)


def gain_genie(ph, phs, L):
    return np.exp(1j * (ph[:, None] + phs[:, L["data_idx"]]))


def gain(model, r, ks, L, fh, ph=None, phs=None, W=TRACK_W, mode=TRACK_MODE, q=0.0, s2=1.0):
    """Complex gain at the data symbols; mode 'kalman' (q = 2 pi pn, s2 noise variance) or 'sw' for interp2 / track."""
    if model == "const":
        return gain_const(r, ks, L, fh)
    if model in ("interp2", "track") and mode == "kalman":
        return gain_kalman(r, ks, L, fh, q, s2)
    if model == "interp2":
        return gain_interp2(r, ks, L, fh)
    if model == "track":
        return gain_track(r, ks, L, fh, W)
    if model == "blocks":
        return gain_track(r, ks, L, fh, 1)
    if model == "eq17":
        return gain_eq17(r, ks, L, fh)
    if model == "x4":
        return gain_x4(r, ks, L, fh)
    if model == "genie":
        return gain_genie(ph, phs, L)
    raise ValueError(model)


def phase_macs(model, L, mode=TRACK_MODE, pn=None):
    """Real MACs of a phase model per CFO hypothesis (on top of the LLRs of the 1024 data symbols, blind_vp
    MAC['llr']; est3 charges cmul x 128 for its LS gain):
    const              4 Nk
    interp2 / track, mode kalman: 4 Nk + KALMAN_ITERS x 40 F (per field and pass: residual rotation 4 + measurement
             20 (angle; Im + scaling is less, charged the same) + filter 10 + smoother 6) + 14 x 1024 (per data symbol: phase lerp 2, exponential 8, the extra complex
             multiply by the per-symbol gain 4); at pn = 0 it IS the constant gain and is charged as const (pass pn;
             pn = None keeps the conservative kalman charge)
    interp2, mode sw   4 Nk + 40 (2 gains, 2 angles) + 14 x 1024
    track, mode sw     4 Nk + 32 F (sliding sums 8, arg + unwrap 20, amplitude projection 4 per field) + 14 x 1024
    blocks             4 Nk + 24 F (arg + unwrap 20, amplitude projection 4 per field) + 14 x 1024
    eq17               40 (3 CORDIC angles / interpolation on the estimator's FFT bins, lit_ars2021.md 6.2; the
                       3-bin DFT recomputed in the simulation is not charged: the bins exist in the receiver)
    x4                 12 K (the 4th-power bin at 4 fh: twiddle 8 + complex multiply 4 per burst symbol on the
                       estimator's r^4) + 4 Nk (UW correlation) + 44 (angle 20, 4 quadrant projections 16, e^{j phi} 8);
                       charged as computed (the patent reads it off its 3 FFT bins, ~0 MACs)
    genie              12 x 1024 (exponential + complex multiply per data symbol)"""
    nk, F = L["nk"], len(L["fstart"])
    if model == "eq17":
        return 40
    if model == "x4":
        return 12 * L["K"] + 4 * nk + 44
    if model == "blocks":
        return 4 * nk + 24 * F + 14 * C.N_SYM
    if model in ("interp2", "track") and mode == "kalman" and pn is not None and pn <= 0:
        return 4 * nk
    if model in ("interp2", "track") and mode == "kalman":
        return 4 * nk + KALMAN_ITERS * 40 * F + 14 * C.N_SYM
    return {"const": 4 * nk, "interp2": 4 * nk + 40 + 14 * C.N_SYM, "track": 4 * nk + 32 * F + 14 * C.N_SYM,
            "genie": 12 * C.N_SYM}[model]


def pilot_macs(rate, src, x_dec, par=True, m_evals=0.0, m_rounds=None, mode=TRACK_MODE, pn=None):
    """(total MACs, MACs per core) per packet of an est4 receiver: est3.plots.pilot_macs with the receiver's own
    estimator (est_macs), the pre-MF correction over its whole burst (4 x (K + 2 SPAN) x SPS, de-rotation only, as
    blind_vp.PREMF_FAIR_MACS for K = 1024), the phase model (phase_macs) at every hypothesis, the LLRs of the 1024 data
    symbols, (1 + x_dec) CA-SCL-8 decodes (per core: 1 + x_dec / PAR_DEC rounds, 4 decodes at once; total + min(x_dec,
    1.5) wasted decodes of the last round), one re-encoding check, and the metric passes (m_evals, m_rounds as est3:
    each pass with its LLRs and phase model; per core m_rounds metric passes + the sample-wise work / KP; the lobe
    hypotheses of run_bler --lobes are inside m_evals / m_rounds / x_dec). par=False: one decode at a time."""
    import blind_vp as vp
    lay, est, model = C.SOURCES[src]
    L = C.layout(lay)
    e = est_macs(est, L)
    K = C.CODES[rate] + 16
    g = phase_macs(model, L, mode, pn)
    pre = vp.MAC["cmul"] * (L["K"] + 2 * C.SPAN) * C.SPS
    dec_t = vp.MAC["decode"] + vp.MAC["llr"] + g
    dec_c = vp.MAC["decode"] / 8 + (vp.MAC["llr"] + g) / KP + K * 10
    rounds, n_dec = (1 + x_dec / PAR_DEC, 1 + x_dec + min(x_dec, 1.5)) if par else (1 + x_dec, 1 + x_dec)
    total = e + pre + n_dec * dec_t + vp.MAC["reencode"]
    core = (e + pre + vp.MAC["reencode"]) / KP + rounds * dec_c
    if m_evals:
        m_met = vp.metric_macs(C.CODES[rate])
        total += m_evals * (m_met + vp.MAC["llr"] + g)
        core += (np.ceil(m_evals / KP) if m_rounds is None else m_rounds) * m_met + m_evals * (vp.MAC["llr"] + g) / KP
    return total, core
