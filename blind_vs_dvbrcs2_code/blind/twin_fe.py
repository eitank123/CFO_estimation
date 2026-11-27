"""
Twin-aided stage-1 CFO line statistic of small_rx (tw_fe, sync_cfo/PLAN_twin_receiver.md sec. 2; the receiver form of
sync_cfo/fs/mod_cfo_fe.py e6_jt, which stays the reference and is only imported by the selfcheck).

    QPSK (pw 4)  Y4 = |FFT_nf(y4)| the receiver's 4th-power line (vv_p None: -r^4; vv_p 2: V&V r^4 / |r|^2), Y2 =
                 |FFT_2nf(y2)| of the square on the diagonal twin symbols only, y2_d = -j v_d^2 = e^{j 2 theta_d} (v the
                 unscrambled virtual symbols, blind_fmt twin), 0 elsewhere; over the 4th-power band bins kk:
                 LL(k) = ln I0(2 mu4 Y4(k) / v4) + ln I0(2 Y2(k2) / v2), k2 = round(nu_k nf) mod 2 nf (f = nu / 4 =
                 k2 / (2 nf) / 2: the same f), v2 = 4 N0 + 2 N0^2; vv_p None: mu4 = 1, v4 = v_line(4, N0) = 16 N0 +
                 72 N0^2 + 96 N0^3 + 24 N0^4; vv_p 2: (mu4, v4) = mu4_of(N0) (fixed-seed Monte Carlo, = mod_cfo_fe)
    BPSK         not implemented (PLAN 2: lag products; small_rx refuses tw_fe on pw 2)
    ops          pow_macs(n_diag, 2) + 2 n_diag (the -j: sign / swap) + fft_macs(2 nf) + n_band (3 + 3 + 8 + 8 + 2)
    tw_ph        S = sum_d -j v_d^2 e^{-j 2 pi 2 f0 nc_d} at the stage-1 f0 (post-premf v): theta_tw = arg(S) / 2 the centre
                 phase mod pi (phase4: mod pi / 2), z = |S|^2 / (n_d v2); ops ph_ops = pow_macs(n_diag, 2) + 2 n_diag +
                 PH4_C n_diag + PH_FIX; tw_prior PRIOR_OPS per cell

    py twin_fe.py --selfcheck          # equivalence vs mod_cfo_fe's e6_jt formula on synthetic lines (no receiver)
"""
import argparse

import numpy as np
from scipy.special import i0e

TW_MC = (4305, 400000)                              # = mod_cfo_fe.TW_MC (mu4 Monte Carlo: seed, samples)
LL_OPS = 3 + 3 + 8 + 8 + 2                          # per band bin: 2 scalings, 2 ln I0, the sum + the argmax compare
_MU = {}


def lni0(x):
    """ln I0(x) (x >= 0), overflow-free."""
    return np.log(i0e(x)) + x


def v_line(pw, N0):
    """var(y) per symbol of the power-law line of unit symbols in CN(0, N0): E|r|^(2 pw) - 1 (mod_cfo_fe.v_line)."""
    return (16 * N0 + 72 * N0 ** 2 + 96 * N0 ** 3 + 24 * N0 ** 4) if pw == 4 else (4 * N0 + 2 * N0 ** 2)


def mu4_of(N0):
    """(mu4, v4) of y = -v^4 / |v|^2 for a unit QPSK symbol in CN(0, N0) (fixed-seed Monte Carlo, = mod_cfo_fe.mu4_of)."""
    if N0 not in _MU:
        g = np.random.default_rng(TW_MC[0])
        w = np.sqrt(N0 / 2) * (g.standard_normal(TW_MC[1]) + 1j * g.standard_normal(TW_MC[1]))
        x = np.exp(1j * np.pi / 4) + w
        mu = float(np.mean(-(x ** 4) / np.abs(x) ** 2).real)
        _MU[N0] = (mu, float(1 + 4 * N0 + 2 * N0 ** 2 - mu ** 2))
    return _MU[N0]


def mu_v4(N0, vv_p):
    """(mu4, v4) of the receiver's 4th-power line: vv_p None (or 4) -r^4: (1, v_line(4, N0)); vv_p 2: mu4_of."""
    if vv_p is None or vv_p == 4:
        return 1.0, v_line(4, N0)
    assert vv_p == 2, "tw_fe: vv_p None / 2"
    return mu4_of(N0)


def sq_line(v, diag, nf):
    """Y2 (B, 2 nf) = |FFT_2nf(-j v^2 on the diagonal symbols, 0 elsewhere)|."""
    y2 = np.zeros_like(v)
    y2[:, diag] = -1j * v[:, diag] ** 2
    return np.abs(np.fft.fft(y2, 2 * nf, axis=1))


def jt_qpsk(Y4, Y2, kk, nu_b, N0, vv_p=None):
    """LL (B, len(kk)) of the joint line (module docstring) and kb (B,) = kk[argmax]."""
    nf = Y4.shape[1]
    mu4, v4 = mu_v4(N0, vv_p)
    k2 = np.round(nu_b[kk] * nf).astype(np.int64) % (2 * nf)
    LL = lni0(2 * mu4 * Y4[:, kk] / v4) + lni0(2 * Y2[:, k2] / v_line(2, N0))
    return LL, kk[LL.argmax(1)]


def ops_qpsk(n_diag, nband, nf, vp):
    """Ops of the twin term per packet (vp = blind_vp: the receiver's unit)."""
    return vp.pow_macs(n_diag, 2) + 2 * n_diag + vp.fft_macs(2 * nf) + nband * LL_OPS


def prior_term(Y2, g, nf, N0):
    """(tw_prior 'pre') the twin term at the grid cells g (B, len(g)): ln I0(2 Y2(round(4 g nf) mod 2 nf) / v2)."""
    b2 = np.round(4 * np.asarray(g) * nf).astype(np.int64) % (2 * nf)
    return lni0(2 * Y2[:, b2] / v_line(2, N0))


PRIOR_OPS = 3 + 8 + 2                               # (tw_prior) per cell: the scaling, ln I0, the tw_w weight + the add
PH_FIX = 3 + 8 + 1 + 1 + 4 + 3                      # (tw_ph) per packet: |S|^2, the angle, the z scaling, the z test,
#                                                     the branch test (rel, its 3 compares), the wrap + weighted add


def ph_twin(v, diag, f, nc, N0):
    """(tw_ph) the twin square line's phase at CFO f (B,): S = sum_d -j v_d^2 e^{-j 2 pi 2 f nc_d} (nc the centred index,
    as bc.phase4) = n_d e^{j 2 theta_c} + noise, so theta_tw = arg(S) / 2 = the centre phase mod pi (the 4th-power line:
    mod pi / 2); z = |S|^2 / (n_d v2) the line SNR at f (noise only: mean 1; clean twins ~ n_d / v2). -> (theta_tw, z)."""
    S = np.einsum("bn,bn->b", -1j * v[:, diag] ** 2, np.exp(-4j * np.pi * f[:, None] * nc[diag][None]))
    return np.angle(S) / 2, np.abs(S) ** 2 / (diag.size * v_line(2, N0))


def ph_weight(N0, n_sym, n_diag):
    """(tw_ph 'iv') inverse-variance weight of theta_tw against bc.phase4's theta_4 (-r^4 at mu 1: arg noise v / (2 N
    mu^2)): var4 = v_line(4) / (32 n_sym), var2 = v_line(2) / (8 n_diag); th = th4 + w wrap(theta_tw - th4), w = var4 /
    (var4 + var2)."""
    var4, var2 = v_line(4, N0) / (32 * n_sym), v_line(2, N0) / (8 * n_diag)
    return var4 / (var4 + var2)


def ph_ops(n_diag, vp):
    """Ops of tw_ph per packet: the square + -j of the diagonal twin symbols (as ops_qpsk), their phasor CMAC (vp.PH4_C
    per symbol, as bc.phase4) and PH_FIX."""
    return vp.pow_macs(n_diag, 2) + 2 * n_diag + vp.PH4_C * n_diag + PH_FIX


def selfcheck():
    """jt_qpsk == mod_cfo_fe's e6_jt formula (its _lni0 / v_line / mu4_of / _band, w2 v_base^2 on the scrambled-domain
    symbols) on synthetic noisy QPSK lines with diagonal twins and the j^q axis hop."""
    import os
    import sys
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_cfo", "fs")
    sys.path.insert(0, here)
    import mod_cfo_fe as mcf
    rng = np.random.default_rng(1)
    B, n, nf, cm = 6, 456, 2048, 0.03
    diag = np.sort(rng.choice(n, 24, replace=False))
    for N0 in (0.5, 1.0, 1.25):
        assert v_line(4, N0) == mcf.v_line(4, N0) and v_line(2, N0) == mcf.v_line(2, N0)
        assert mu4_of(N0) == mcf.mu4_of(N0), "mu4_of != mod_cfo_fe.mu4_of"
        for vv_p in (None, 2):
            b = 1 - 2.0 * rng.integers(0, 2, (B, n, 2))
            b[:, diag, 1] = b[:, diag, 0]                             # clean twins on the diagonal symbols
            clean = (b[..., 0] + 1j * b[..., 1]) / np.sqrt(2)
            q = rng.integers(0, 2, n)
            hop = np.where(np.isin(np.arange(n), diag) & (q == 1), 1j, np.where(q == 1, -1.0, 1.0))
            f = rng.uniform(-cm, cm, B)
            ph = rng.uniform(0, 2 * np.pi, B)
            w = np.sqrt(N0 / 2) * (rng.standard_normal((B, n)) + 1j * rng.standard_normal((B, n)))
            rot = np.exp(1j * (2 * np.pi * f[:, None] * np.arange(n)[None] + ph[:, None]))
            vb = clean * hop[None] * rot + w                          # scrambled domain (mod_cfo_fe's v)
            v = vb * np.conj(hop)[None]                               # derot-folded (ours)
            s0 = np.where(np.isin(np.arange(n), diag) & (q == 1), (-1 + 1j) / np.sqrt(2), (1 + 1j) / np.sqrt(2) * np.where(q == 1, -1, 1))
            w2 = np.conj(s0[diag] ** 2)
            nu, bm = mcf._band(nf, 4, cm)
            kk = np.where(bm)[0]
            y4 = -(v ** 4) / (1.0 if vv_p is None else np.abs(v) ** 2)          # small_rx vv_line (-r^4 [/ |r|^2])
            y4b = -(vb ** 4) / (1.0 if vv_p is None else np.abs(vb) ** 2)
            Y4, Y4b = np.abs(np.fft.fft(y4, nf, axis=1)), np.abs(np.fft.fft(y4b, nf, axis=1))
            assert np.allclose(Y4, Y4b, rtol=1e-10, atol=1e-9), "4th-power line changed by the fold"
            Y2 = sq_line(v, diag, nf)
            y2b = np.zeros_like(vb)
            y2b[:, diag] = w2[None] * vb[:, diag] ** 2
            Y2b = np.abs(np.fft.fft(y2b, 2 * nf, axis=1))
            assert np.allclose(Y2, Y2b, rtol=1e-10, atol=1e-9), "-j v^2 != w2 v_base^2"
            LL, kb = jt_qpsk(Y4, Y2, kk, nu, N0, vv_p)
            mu4, v4 = (mcf.mu4_of(N0) if vv_p == 2 else (1.0, mcf.v_line(4, N0)))
            k2 = np.round(nu[kk] * nf).astype(np.int64) % (2 * nf)
            LLr = mcf._lni0(2 * mu4 * Y4b[:, kk] / v4) + mcf._lni0(2 * Y2b[:, k2] / mcf.v_line(2, N0))
            assert np.allclose(LL, LLr, rtol=1e-9, atol=1e-9) and np.array_equal(kb, kk[LLr.argmax(1)]), (N0, vv_p)
    for N0 in (0.0, 0.01):                                            # (tw_ph) theta_tw = the centre phase mod pi
        b = 1 - 2.0 * rng.integers(0, 2, (B, n, 2))
        b[:, diag, 1] = b[:, diag, 0]
        nc = np.arange(n) - (n - 1) / 2
        f, thc = rng.uniform(-cm, cm, B), rng.uniform(-np.pi, np.pi, B)
        w = np.sqrt(N0 / 2) * (rng.standard_normal((B, n)) + 1j * rng.standard_normal((B, n)))
        v = (b[..., 0] + 1j * b[..., 1]) / np.sqrt(2) * np.exp(1j * (2 * np.pi * f[:, None] * nc[None] + thc[:, None])) + w
        tw, z = ph_twin(v, diag, f, nc, max(N0, 1e-3))
        e = (tw - thc + np.pi / 2) % np.pi - np.pi / 2
        assert np.abs(e).max() < (1e-9 if N0 == 0 else 0.05) and (z > 0.5 * diag.size / v_line(2, max(N0, 1e-3))).all(), (N0, e, z)
    assert 0 < ph_weight(1.0, 456, 100) < 1 and abs(ph_weight(1.0, 456, 0.0 + 1e9) - 1) < 1e-6
    print("TWIN_FE SELFCHECK OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selfcheck", action="store_true")
    if ap.parse_args().selfcheck:
        selfcheck()
