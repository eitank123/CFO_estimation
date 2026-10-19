"""
Zero-overhead single-carrier burst receiver, Stage 2: multipath, equalization without CP.

Packet : as in Stage 1 (zero_overhead_rx.py): 512 QPSK symbols = one polar codeword (R = 1/2 or 1/4,
         CRC-11, CA-SCL L = 8), no preamble, no CP, 2 zero symbols of guard between bursts.
Channel: --channel multipath  3 symbol-spaced taps, 0/-3/-6 dB, Rayleigh, one realisation per burst,
                              E[sum |h|^2] = 1 (Es/N0 = average received SNR)
         --channel awgn       1 tap h = 1: every block below reduces to the Stage 1 receiver
         r[n] = exp(j(2 pi f n + phi)) sum_k h_k s[n-k] + w[n],  n = 0 .. 513  (burst + 2-sample tail;
         the guard makes the burst free of inter-burst interference), f ~ U[-0.2, 0.2].
         Perfect timing; Es/N0 known (noise variance for the equalizers and the LLRs).

Blocks
    coarse CFO      4th power of r (FFT 2048 + 2 Newton): f0, ambiguous mod 1/4 (cells k = -1, 0, 1 inside
                    the +-0.2 prior). With multipath the line has amplitude |sum h_k^4| instead of 1.
    channel init    (a) blind CMA: 9-tap FIR, 5 passes, decisions -> least-squares taps (delay searched)
                    (b) strongest-tap bootstrap: no equalizer, single-tap LLRs (4th-power phase and gain,
                        interference counted as noise), decode, then LS taps on the decisions
                    The phase is ambiguous mod pi/2: the 4 hypotheses are LLR relabellings of one
                    equalizer output (one equalization per CFO cell).
    equalizers      MLSE: BCJR over 5^M states (M = taps - 1; QPSK + the zero guard symbol, so the burst
                    edges are exact; 25 states for 3 taps), bit LLRs from the symbol APPs
                    MMSE: block (H^H H + N0 I)^-1 H^H r on the 514 x 512 convolution matrix (banded
                    Toeplitz, solved per burst), LLRs from the unbiased output and its average SINR
    selection       CRC-passing hypothesis with the best path metric, else the best metric
    code-aided      re-encode the decision, joint ML of CFO and taps on it (sum over taps of the
                    periodograms of r[n] s*[n-k], FFT 2048 + Newton, then LS taps) -> re-equalize ->
                    re-decode, 3 iterations

Receivers (all on the same bursts)
    Genie MLSE / MMSE            true CFO, phase and taps
    Known 512 MLSE / MMSE        joint ML of CFO + taps on the true symbols
    Known CFO, est. ch. MLSE     true CFO; channel from CMA + 3 code-aided tap updates (channel loss only)
    Blind CMA + CRC MLSE         coarse CFO + CMA init + MLSE, CRC selection
    Code-aided 1/2/3 MLSE        + code-aided loop
    Blind ST + CRC / CA-3 ST     same with the strongest-tap bootstrap instead of CMA
    Blind CMA + CRC / CA-3 MMSE  block MMSE instead of MLSE

Usage (project folder):
    python multipath/zero_overhead_mp.py --channel multipath --parts 4 --part 0   (one Run:ai job per part)
    python multipath/zero_overhead_mp.py --channel multipath --merge
    python multipath/zero_overhead_mp.py --channel awgn ...                        (instant AWGN check)
"""

import argparse
import glob
import itertools
import multiprocessing as mp
import os
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solveh_banded
from scipy.special import logsumexp

from polar import PolarCode
from zero_overhead_rx import (CODES, ES_GRID, MAX_CFO, N_BITS, N_SYM, OUTAGE, SHORT, fourth_power, interleaver,
                              newton, qpsk)

CHANNELS = {"multipath": [0.0, -3.0, -6.0], "awgn": [0.0]}
N_RX = N_SYM + 2                     # received samples: burst + 2-sample channel tail (guard)
QP = np.array([1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j]) / np.sqrt(2)      # index u = 2 b0 + b1 (as qpsk())
ALPH = np.concatenate([QP, [0]])                                     # + the zero (guard) symbol, index 4
RX = ["Genie MLSE", "Genie MMSE", "Known 512 MLSE", "Known 512 MMSE", "Known CFO, est. ch. MLSE",
      "Blind CMA + CRC MLSE", "Code-aided 1 MLSE", "Code-aided 2 MLSE", "Code-aided 3 MLSE",
      "Blind ST + CRC MLSE", "Code-aided 3 ST MLSE", "Blind CMA + CRC MMSE", "Code-aided 3 MMSE"]
CFO_EST = ["Blind coarse (k=0)", "Blind CMA + CRC", "Code-aided 1", "Code-aided 3", "Known 512"]
MAIN = "Code-aided 3 MLSE"
# Stage 3 (--nn): bursts generated at 8 SPS (coarse_nn.waveform, every 8th sample = the symbol-rate r above),
# the neural coarse estimator on z8 replaces the 4th power; the ST and MMSE variants are skipped
RX_NN = ["NN + CRC MLSE", "NN code-aided 3 MLSE"]
CFO_NN = ["NN coarse", "NN + CRC", "NN code-aided 3"]


def rx_list(results):
    return [x for x in RX + RX_NN if x in results[0]["frame_err"]]


def cfo_list(results):
    return [x for x in CFO_EST + CFO_NN if x in results[0]["cfo_err"]]


# =====================================================================
# Channel
# =====================================================================

def make_channel(rng, B, taps_db):
    p = 10 ** (np.asarray(taps_db) / 10)
    p = p / p.sum()
    if len(p) == 1:
        return np.ones((B, 1), complex)
    return (rng.standard_normal((B, len(p))) + 1j * rng.standard_normal((B, len(p)))) * np.sqrt(p / 2)


def convolve(sym, h):
    """x[n] = sum_k h_k s[n-k], n = 0 .. N_RX-1 (zeros outside the burst)."""
    B, T = h.shape
    x = np.zeros((B, N_RX), complex)
    for k in range(T):
        x[:, k:k + N_SYM] += h[:, k:k + 1] * sym
    return x


def rot(r, f):
    return r * np.exp(-2j * np.pi * f[:, None] * np.arange(r.shape[1]))


# =====================================================================
# Equalizers -> bit LLRs (R, 1024) in transmitted (interleaved) bit order
# =====================================================================

def bcjr(r, h, n0):
    """Symbol-APP MLSE over the states (s[n-1] .. s[n-M]) in {QPSK, 0}; r (R, N_RX), h (R, T)."""
    R, T = h.shape
    M = T - 1
    if M == 0:                                                   # AWGN: per-symbol metrics
        lg = -np.abs(r[:, :N_SYM, None] - h[:, :1, None] * QP) ** 2 / n0
        return app_to_llr(lg)
    states = list(itertools.product(range(5), repeat=M))         # (a_1 .. a_M) = (s[n-1] .. s[n-M])
    S = len(states)
    mean = h[:, 0, None, None] * ALPH[None, None, :]              # (R, S, 5) for input u
    for i in range(M):
        mean = mean + (h[:, i + 1, None] * ALPH[[st[i] for st in states]])[:, :, None]
    shape = (R,) + (5,) * M
    alpha = np.full((N_RX + 1,) + shape, -np.inf)
    alpha[(0, slice(None)) + (4,) * M] = 0.0                      # starts in the guard (all-zero) state
    gam = np.empty((N_RX, R, S, 5))
    for n in range(N_RX):
        g = -np.abs(r[:, n, None, None] - mean) ** 2 / n0
        if n < N_SYM:
            g[:, :, 4] = -np.inf                                 # data symbols are QPSK
        else:
            g[:, :, :4] = -np.inf                                # tail: the guard symbols are zero
        gam[n] = g
        # alpha_{n+1}[u, a_1 .. a_{M-1}] = lse_{a_M} alpha_n[a_1 .. a_M] + gamma[(a_1 .. a_M), u]
        t = alpha[n].reshape(R, S, 1) + g
        t = logsumexp(t.reshape((R,) + (5,) * M + (5,)), axis=M)  # sum out a_M -> (R, a_1..a_{M-1}, u)
        alpha[n + 1] = np.moveaxis(t, -1, 1)
    beta = np.full(shape, -np.inf)
    beta[(slice(None),) + (4,) * M] = 0.0                         # ends in the all-zero state
    app = np.empty((R, N_SYM, 4))
    for n in range(N_RX - 1, -1, -1):
        # beta_n[a_1 .. a_M] = lse_u gamma[(a_1..a_M), u] + beta_{n+1}[u, a_1 .. a_{M-1}]
        bn = np.moveaxis(beta, 1, -1)                             # (R, a_1..a_{M-1}, u)
        bn = np.expand_dims(bn, M)                                # broadcast over a_M
        g = gam[n].reshape((R,) + (5,) * M + (5,))
        tot = g + bn
        if n < N_SYM:
            a = alpha[n].reshape((R,) + (5,) * M + (1,))
            app[:, n] = logsumexp((a + tot).reshape(R, -1, 5), axis=1)[:, :4]
        beta = logsumexp(tot, axis=-1)
    return app_to_llr(app)


def app_to_llr(lg):
    """Symbol log-APPs (R, 512, 4) -> bit LLRs (R, 1024): b0 from u in {0,1} vs {2,3}, b1 from {0,2} vs {1,3}."""
    llr = np.empty((lg.shape[0], N_BITS))
    llr[:, 0::2] = logsumexp(lg[..., [0, 1]], -1) - logsumexp(lg[..., [2, 3]], -1)
    llr[:, 1::2] = logsumexp(lg[..., [0, 2]], -1) - logsumexp(lg[..., [1, 3]], -1)
    return llr


def mmse(r, h, n0):
    """Block MMSE on the convolution matrix; A = H^H H + N0 I is banded Toeplitz (the tail is observed)."""
    R, T = h.shape
    rho = np.array([[np.sum(h[i, :T - d].conj() * h[i, d:]) for d in range(T)] for i in range(R)])  # rho[d]
    b = np.zeros((R, N_SYM), complex)
    for k in range(T):
        b += h[:, k:k + 1].conj() * r[:, k:k + N_SYM]
    x = np.empty((R, N_SYM), complex)
    for i in range(R):
        ab = np.zeros((T, N_SYM), complex)                        # upper banded form for solveh_banded
        for d in range(T):
            ab[T - 1 - d, d:] = rho[i, d].conj()
        ab[T - 1] += n0
        x[i] = solveh_banded(ab, b[i])
    Hw = np.fft.fft(h, n=N_SYM, axis=1)
    mu = 1 - n0 * np.mean(1 / (np.abs(Hw) ** 2 + n0), axis=1)     # average bias (interior symbols)
    xt = x / mu[:, None]
    var = np.maximum((1 - mu) / (2 * mu), 1e-6)                    # per real dimension
    llr = np.empty((R, N_BITS))
    llr[:, 0::2] = np.sqrt(2) * xt.real / var[:, None]
    llr[:, 1::2] = np.sqrt(2) * xt.imag / var[:, None]
    return llr


def rotate_llr(llr, m):
    """LLRs of the symbols multiplied by j^m: one step maps (L0, L1) -> (-L1, L0)."""
    out = llr.copy()
    for _ in range(m % 4):
        l0, l1 = out[:, 0::2].copy(), out[:, 1::2].copy()
        out[:, 0::2], out[:, 1::2] = -l1, l0
    return out


# =====================================================================
# Estimators
# =====================================================================

def ls_taps(r, s, T):
    """Least-squares taps from (estimated) symbols: min || r - conv(s, h) ||."""
    S = np.zeros((len(r), N_RX, T), complex)
    for k in range(T):
        S[:, k:k + N_SYM, k] = s
    G = np.einsum("bnk,bnl->bkl", S.conj(), S) + 1e-9 * np.eye(T)
    c = np.einsum("bnk,bn->bk", S.conj(), r)
    return np.linalg.solve(G, c[..., None])[..., 0]


def joint_ml(r, s, T, K=2048):
    """Joint ML of CFO and taps on symbols s: max_f sum_k |FFT(r[n] s*[n-k])|^2 (+ Newton), then LS taps."""
    z = np.zeros((len(r), T, N_RX), complex)
    for k in range(T):
        z[:, k, k:k + N_SYM] = r[:, k:k + N_SYM] * s.conj()
    Z = np.fft.fft(z, n=K, axis=2)
    P = (np.abs(Z) ** 2).sum(1)
    fr = np.fft.fftfreq(K)
    P[:, np.abs(fr) > MAX_CFO + 1.0 / K] = -1
    f = fr[P.argmax(1)]
    n = np.arange(N_RX)
    for _ in range(2):
        e = z * np.exp(-2j * np.pi * f[:, None, None] * n)
        A, A1, A2 = e.sum(2), (e * (-2j * np.pi * n)).sum(2), (e * (-(2 * np.pi * n) ** 2)).sum(2)
        f = f - (2 * (A1 * A.conj()).real).sum(1) / (2 * ((A2 * A.conj()).real + np.abs(A1) ** 2)).sum(1)
    return f, ls_taps(rot(r, f), s, T)


def cma_taps(r, T, E=9, passes=5, mu=5e-3):
    """Blind CMA equalizer -> hard decisions -> LS taps, with the equalizer delay searched."""
    R = len(r)
    w = np.zeros((R, E), complex)
    w[:, E // 2] = 1.0
    scale = 1 / np.sqrt(np.mean(np.abs(r) ** 2, axis=1, keepdims=True))
    x = r * scale
    win = np.lib.stride_tricks.sliding_window_view(x, E, axis=1)[:, :, ::-1]     # (R, N_RX-E+1, E)
    for _ in range(passes):
        for n in range(win.shape[1]):
            v = win[:, n]
            y = np.einsum("re,re->r", w.conj(), v)
            w = w - mu * ((np.abs(y) ** 2 - 1) * y.conj())[:, None] * v
    y = np.einsum("re,rne->rn", w.conj(), win)                     # output n corresponds to r[n + E - 1]
    # CMA is phase-blind: remove the rotation (mod pi/2) with the 4th-power phase before deciding
    y = y * np.exp(-1j * (np.angle(np.sum(y ** 4, axis=1)) - np.pi) / 4)[:, None]
    d = QP[(2 * (y.real < 0) + (y.imag < 0)).astype(int)]
    # Output y[j] is a delayed symbol: y[j] ~ s[j - o] for an unknown offset o (equalizer + channel
    # delay); with the centre-spike start o = -(E // 2). Search every offset, keep the best LS fit.
    best, best_res = None, None
    J = d.shape[1]
    for o in range(-(E - 1), T):
        s = np.zeros((R, N_SYM), complex)
        i_lo, i_hi = max(0, -o), min(N_SYM, J - o)                  # need 0 <= i + o < J
        s[:, i_lo:i_hi] = d[:, i_lo + o:i_hi + o]
        h = ls_taps(r, s, T)
        res = np.sum(np.abs(r - convolve(s, h)) ** 2, axis=1)
        if best is None:
            best, best_res = h, res
        else:
            upd = res < best_res
            best[upd], best_res[upd] = h[upd], res[upd]
    return best


# =====================================================================
# Monte Carlo point
# =====================================================================

def decode_llr(code, llr, inter, chunk=1000):
    out_d, out_ok, out_pm = [], [], []
    for i in range(0, len(llr), chunk):
        deint = np.empty_like(llr[i:i + chunk])
        deint[:, inter] = llr[i:i + chunk]
        d, ok, pm = code.decode(deint, return_info=True)
        out_d.append(d), out_ok.append(ok), out_pm.append(pm)
    return np.concatenate(out_d), np.concatenate(out_ok), np.concatenate(out_pm)


def select(p_of_row, ok, pm, B):
    """Per packet: CRC-passing row with the best metric, else the best metric. Returns row indices."""
    pick = np.empty(B, int)
    for p in range(B):
        idx = np.where(p_of_row == p)[0]
        good = idx[ok[idx]]
        pick[p] = good[pm[good].argmin()] if len(good) else idx[pm[idx].argmin()]
    return pick


def simulate_point(task):
    (code_name, es_db, channel, batch, min_errors, min_frames, max_frames, seed, task_id, progress_file, refs_only,
     nn_path, nn_polish) = task
    main = "Genie MLSE" if refs_only else MAIN       # receiver whose errors stop the point
    A, C = CODES[code_name]
    code = PolarCode(N_BITS, A, C, 8)
    inter = interleaver()
    rng = np.random.default_rng(seed)
    taps_db = CHANNELS[channel]
    T = len(taps_db)
    snr = 10 ** (es_db / 10)
    n0 = 1 / snr                                                   # complex noise variance
    sigma2 = n0 / 2
    ks = np.array([-1, 0, 1])

    acc = {"frames": 0, "bit_err": {r: 0 for r in RX}, "frame_err": {r: 0 for r in RX},
           "cfo_err": {e: [] for e in CFO_EST}, "amb_present": 0, "amb_err": 0,
           "decodes": 0, "equalizations": 0, "tap_nmse": {"Known 512": [], "Code-aided 3": []}}
    rx_skip = ("Blind ST + CRC MLSE", "Code-aided 3 ST MLSE", "Blind CMA + CRC MMSE", "Code-aided 3 MMSE")
    if nn_path:
        import torch
        from coarse_nn import estimate as nn_estimate, waveform
        torch.set_num_threads(1)                                   # one core per Monte-Carlo worker
        for x in rx_skip:
            del acc["bit_err"][x], acc["frame_err"][x]
        for x in RX_NN:
            acc["bit_err"][x] = acc["frame_err"][x] = 0
        for e in CFO_NN:
            acc["cfo_err"][e] = []
        acc["amb_err_nn"] = acc["decodes_nn"] = acc["equalizations_nn"] = 0

    def tick(B):
        acc["frames"] += B
        done = min(1.0, max(min(acc["frame_err"][main] / min_errors, 1.0) * min(acc["frames"] / min_frames, 1.0),
                            acc["frames"] / max_frames))
        with open(progress_file, "a") as fp:
            fp.write(f"{task_id} {done:.4f}\n")

    while (acc["frame_err"][main] < min_errors or acc["frames"] < min_frames) and acc["frames"] < max_frames:
        B = batch
        data = rng.integers(0, 2, (B, A), dtype=np.uint8)
        sym = qpsk(code.encode(data)[:, inter])
        h = make_channel(rng, B, taps_db)
        f = rng.uniform(-MAX_CFO, MAX_CFO, B)
        ph = rng.uniform(0, 2 * np.pi, B)
        n = np.arange(N_RX)
        if nn_path:
            z8, r = waveform(convolve(sym, h), f, ph, snr, rng)
        else:
            r = convolve(sym, h) * np.exp(1j * (2 * np.pi * f[:, None] * n + ph[:, None])) + np.sqrt(sigma2) * (
                rng.standard_normal((B, N_RX)) + 1j * rng.standard_normal((B, N_RX)))
        h_eff = h * np.exp(1j * ph[:, None])                       # taps seen after removing the true CFO

        def score(name, d):
            e = d != data
            acc["bit_err"][name] += int(e.sum())
            acc["frame_err"][name] += int(e.any(1).sum())

        def count(decodes, eqs):
            acc["decodes"] += decodes
            acc["equalizations"] += eqs

        # --- references
        rg = rot(r, f)
        score("Genie MLSE", decode_llr(code, bcjr(rg, h_eff, n0), inter)[0])
        score("Genie MMSE", decode_llr(code, mmse(rg, h_eff, n0), inter)[0])
        fk, hk = joint_ml(r, sym, T)
        acc["cfo_err"]["Known 512"].append(fk - f)
        acc["tap_nmse"]["Known 512"].append(np.sum(np.abs(hk - h_eff) ** 2, 1) / np.sum(np.abs(h) ** 2, 1))
        rk = rot(r, fk)
        score("Known 512 MLSE", decode_llr(code, bcjr(rk, hk, n0), inter)[0])
        score("Known 512 MMSE", decode_llr(code, mmse(rk, hk, n0), inter)[0])
        if refs_only:                     # high-trial run of the reference receivers only
            tick(B)
            continue

        # --- known CFO, estimated channel (CMA init, 4 phase hypotheses, 3 code-aided tap updates)
        hc = cma_taps(rg, T)
        llr = bcjr(rg, hc, n0)
        rows_p = np.repeat(np.arange(B), 4)
        d_r, ok_r, pm_r = decode_llr(code, np.concatenate([rotate_llr(llr, m) for m in range(4)])
                                     .reshape(4, B, -1).transpose(1, 0, 2).reshape(4 * B, -1), inter)
        d_sel = d_r[select(rows_p, ok_r, pm_r, B)]
        for _ in range(3):
            hc = ls_taps(rg, qpsk(code.encode(d_sel)[:, inter]), T)
            d_sel = decode_llr(code, bcjr(rg, hc, n0), inter)[0]
        score("Known CFO, est. ch. MLSE", d_sel)

        # --- blind coarse CFO: hypotheses (packet, k) inside the prior
        f0, ph0 = fourth_power(r)
        acc["cfo_err"]["Blind coarse (k=0)"].append(f0 - f)
        k_true = ks[np.abs(f0[:, None] + ks / 4 - f[:, None]).argmin(1)]
        acc["amb_present"] += int((k_true != 0).sum())
        hyp = [(p, k) for p in range(B) for k in ks if abs(f0[p] + k / 4) <= MAX_CFO + 0.005]
        hp, hk_ = (np.array(v) for v in zip(*hyp))
        f_h = f0[hp] + hk_ / 4
        r_h = rot(r[hp], f_h)
        h_cma = cma_taps(r_h, T)

        def blind_select(llr_h):
            """4 phase relabellings of every (packet, k) hypothesis, CRC selection."""
            Hn = len(hp)
            stacked = np.stack([rotate_llr(llr_h, m) for m in range(4)], 1).reshape(4 * Hn, -1)
            d_r, ok_r, pm_r = decode_llr(code, stacked, inter)
            count(4 * Hn, 0)
            pick = select(np.repeat(hp, 4), ok_r, pm_r, B)
            return d_r[pick], np.repeat(np.arange(Hn), 4)[pick]

        def code_aided(d_sel, equalize, iters, record):
            for it in range(1, iters + 1):
                s_hat = qpsk(code.encode(d_sel)[:, inter])
                fi, hi = joint_ml(r, s_hat, T)
                if record:
                    acc["cfo_err"].setdefault(f"Code-aided {it}", []).append(fi - f) if it in (1, 3) else None
                    if it == 3:
                        acc["tap_nmse"]["Code-aided 3"].append(np.sum(np.abs(hi - h_eff) ** 2, 1) / np.sum(np.abs(h) ** 2, 1))
                ri = rot(r, fi)
                d_sel = decode_llr(code, equalize(ri, hi, n0), inter)[0]
                count(len(d_sel), len(d_sel))           # one decode + one equalization per burst
                yield it, d_sel

        # MLSE, CMA init
        d_sel, hsel = blind_select(bcjr(r_h, h_cma, n0))
        count(0, len(hp))
        acc["amb_err"] += int((hk_[hsel] != k_true).sum())
        acc["cfo_err"]["Blind CMA + CRC"].append(f_h[hsel] - f)
        score("Blind CMA + CRC MLSE", d_sel)
        for it, d_it in code_aided(d_sel, bcjr, 3, True):
            score(f"Code-aided {it} MLSE", d_it)

        if nn_path:
            # Stage 3: neural coarse CFO on the 8-SPS burst; hypotheses = 2 most probable cells (inside the
            # prior) x 4 phase relabellings, then the same CMA init, MLSE, CRC selection and code-aided loop
            fn, kn, pn, ffn = nn_estimate(z8, nn_path, polish=nn_polish)
            acc["cfo_err"]["NN coarse"].append(fn - f)
            top2 = np.argsort(-pn, axis=1)[:, :2] - 1
            hyp = []
            for p in range(B):
                cand = [k for k in top2[p] if abs(ffn[p] + k / 4) <= MAX_CFO + 0.005] or [int(kn[p])]
                hyp += [(p, k) for k in cand]
            hp_n, hk_n = (np.array(v) for v in zip(*hyp))
            f_n = ffn[hp_n] + hk_n / 4
            r_n = rot(r[hp_n], f_n)
            llr_n = bcjr(r_n, cma_taps(r_n, T), n0)
            stacked = np.stack([rotate_llr(llr_n, m) for m in range(4)], 1).reshape(4 * len(hp_n), -1)
            d_r, ok_r, pm_r = decode_llr(code, stacked, inter)
            pick = select(np.repeat(hp_n, 4), ok_r, pm_r, B)
            sel = np.repeat(np.arange(len(hp_n)), 4)[pick]
            acc["decodes_nn"] += 4 * len(hp_n) + 3 * B
            acc["equalizations_nn"] += len(hp_n) + 3 * B
            acc["amb_err_nn"] += int((np.abs(f_n[sel] - f) > 0.125).sum())
            acc["cfo_err"]["NN + CRC"].append(f_n[sel] - f)
            score("NN + CRC MLSE", d_r[pick])
            d_it = d_r[pick]
            for it in (1, 2, 3):
                fi, hi = joint_ml(r, qpsk(code.encode(d_it)[:, inter]), T)
                d_it = decode_llr(code, bcjr(rot(r, fi), hi, n0), inter)[0]
            acc["cfo_err"]["NN code-aided 3"].append(fi - f)
            score("NN code-aided 3 MLSE", d_it)
            tick(B)
            continue

        # MLSE, strongest-tap bootstrap: no equalizer for the first decode
        y4 = r_h ** 4
        A4 = np.abs((y4 * np.exp(-2j * np.pi * 4 * 0 * n)).mean(1))       # |sum h^4| (CFO already removed)
        g = np.maximum(A4, 1e-6) ** 0.25
        ph_h = ph0[hp] + 2 * np.pi * (hk_ / 4) * 0
        y1 = r_h[:, :N_SYM] * np.exp(-1j * ph_h)[:, None] / g[:, None]
        var = np.maximum((np.mean(np.abs(r_h) ** 2, 1) - g ** 2) / (2 * g ** 2), 1e-3)
        llr1 = np.empty((len(hp), N_BITS))
        llr1[:, 0::2] = np.sqrt(2) * y1.real / var[:, None]
        llr1[:, 1::2] = np.sqrt(2) * y1.imag / var[:, None]
        d_st, _ = blind_select(llr1)
        score("Blind ST + CRC MLSE", d_st)
        for it, d_it in code_aided(d_st, bcjr, 3, False):
            if it == 3:
                score("Code-aided 3 ST MLSE", d_it)

        # MMSE, CMA init
        d_mm, _ = blind_select(mmse(r_h, h_cma, n0))
        count(0, len(hp))
        score("Blind CMA + CRC MMSE", d_mm)
        for it, d_it in code_aided(d_mm, mmse, 3, False):
            if it == 3:
                score("Code-aided 3 MMSE", d_it)

        tick(B)

    acc["cfo_err"] = {k: np.concatenate(v) for k, v in acc["cfo_err"].items() if v}
    acc["tap_nmse"] = {k: np.concatenate(v) for k, v in acc["tap_nmse"].items() if v}
    return {"code": code_name, "es": es_db, "ebn0": es_db - 10 * np.log10(A / N_SYM), "channel": channel, **acc}


def run(args, log):
    points = [(name, es) for name in CODES for es in ES_GRID]
    tasks = []
    for i, (name, es) in enumerate(points):
        if i % args.parts != args.part:
            continue
        seed = zlib.crc32(repr(("zo-mp", args.channel, name, es, args.seed)).encode())
        tasks.append((name, float(es), args.channel, args.batch, args.min_errors, args.min_frames, args.max_frames,
                      seed + (7 if args.refs_only else 0), len(tasks), args.progress, args.refs_only,
                      args.nn, not args.nn_no_polish))
    tasks.sort(key=lambda t: -t[1])
    with open(args.progress, "w") as fp:
        fp.write(f"start {time.time():.0f} tasks {len(tasks)}\n")
    t0, results = time.time(), []
    with mp.Pool(args.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(simulate_point, tasks), 1):
            results.append(r)
            log(f"{i}/{len(tasks)} points | {time.time() - t0:.0f}s")
    return results


# =====================================================================
# Report and plots
# =====================================================================

REF_RX = ["Genie MLSE", "Genie MMSE", "Known 512 MLSE", "Known 512 MMSE"]


def counts(r, rx):
    """(frames, bit errors, frame errors) of a receiver; references from the high-trial run when merged."""
    if rx in r.get("refs", {}):
        return r["refs"][rx]
    return r["frames"], r["bit_err"][rx], r["frame_err"][rx]


def bler(r, rx):
    n, _, fe = counts(r, rx)
    return fe / n


def report(results, log):
    for name in CODES:
        rs = sorted((r for r in results if r["code"] == name), key=lambda r: r["es"])
        log(f"\n{'=' * 120}\n{SHORT[name]}: BLER\n{'=' * 120}")
        rxs = rx_list(results)
        log(f"{'Es/N0':>5} {'Eb/N0':>6} | " + " | ".join(f"{x[:16]:>16}" for x in rxs) + " | frames | decodes, eq./packet")
        for r in rs:
            nn = (f" | NN: {r['decodes_nn'] / r['frames']:.1f}, {r['equalizations_nn'] / r['frames']:.1f}"
                  if "decodes_nn" in r else "")
            log(f"{r['es']:5.0f} {r['ebn0']:6.2f} | " + " | ".join(f"{bler(r, x):16.2e}" for x in rxs)
                + f" | {r['frames']:6d} | {r['decodes'] / r['frames']:.1f}, {r['equalizations'] / r['frames']:.1f}" + nn)
        log(f"\n{SHORT[name]}: CFO median |err| / P(|err| > {OUTAGE:g}); k-error rate; tap NMSE (median)")
        cfos = cfo_list(results)
        log(f"{'Es/N0':>5} | " + " | ".join(f"{e:>22}" for e in cfos) + " | k-err CRC | k != 0 | NMSE known512 / CA-3"
            + (" | k-err NN + CRC" if "amb_err_nn" in rs[0] else ""))
        for r in rs:
            cells = [f"{np.median(np.abs(r['cfo_err'][e])):.1e} / {np.mean(np.abs(r['cfo_err'][e]) > OUTAGE):.3f}"
                     if e in r["cfo_err"] else "-" for e in cfos]
            nm = r["tap_nmse"]
            log(f"{r['es']:5.0f} | " + " | ".join(f"{c:>22}" for c in cells) +
                f" | {r['amb_err'] / r['frames']:.4f} | {r['amb_present'] / r['frames']:.3f} | "
                f"{np.median(nm['Known 512']):.1e} / {np.median(nm['Code-aided 3']):.1e}"
                + (f" | {r['amb_err_nn'] / r['frames']:.4f}" if "amb_err_nn" in r else ""))


def validate(results, log):
    """--channel awgn must reproduce Stage 1 (results_zo_awgn/zo_results.npy)."""
    f = os.path.join(HERE, "results_zo_awgn", "zo_results.npy")
    if results[0]["channel"] != "awgn" or not os.path.exists(f) or "Blind ST + CRC MLSE" not in results[0]["frame_err"]:
        return
    ref = {(r["code"], r["es"]): r for r in np.load(f, allow_pickle=True)}
    log("\nValidation against Stage 1 (AWGN), BLER:")
    pairs = (("Genie MLSE", "Genie"), ("Known 512 MLSE", "Known 512"), ("Blind ST + CRC MLSE", "Blind + CRC"),
             ("Code-aided 3 ST MLSE", "Code-aided 3"))
    for r in sorted(results, key=lambda r: (r["code"], r["es"])):
        s1 = ref.get((r["code"], r["es"]))
        if s1 is None or s1["frame_err"]["Code-aided 3"] == 0 and r["frame_err"][MAIN] == 0:
            continue
        log(f"  {SHORT[r['code']]} Es/N0 {r['es']:3.0f}: " + " | ".join(
            f"{a} {r['frame_err'][a] / r['frames']:.2e} vs {s1['frame_err'][b] / s1['frames']:.2e}" for a, b in pairs))


def plot(results, out_dir):
    channel = results[0]["channel"]
    style = {"Genie MLSE": ("k", "-"), "Genie MMSE": ("k", ":"), "Known 512 MLSE": ("#2ca02c", "--"),
             "Known CFO, est. ch. MLSE": ("#9467bd", "--"), "Blind CMA + CRC MLSE": ("#ff7f0e", "-"),
             "Code-aided 3 MLSE": ("#08519c", "-"), "Blind ST + CRC MLSE": ("#8c564b", ":"),
             "Code-aided 3 ST MLSE": ("#8c564b", "-"), "Code-aided 3 MMSE": ("#08519c", ":"),
             "NN + CRC MLSE": ("#d62728", ":"), "NN code-aided 3 MLSE": ("#d62728", "-")}
    style = {k: v for k, v in style.items() if k in rx_list(results)}
    for metric, ylabel in (("bler", "BLER"), ("ber", "BER")):
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        for ax, name in zip(axes, CODES):
            rs = sorted((r for r in results if r["code"] == name), key=lambda r: r["es"])
            x = [r["ebn0"] for r in rs]
            for rx, (c, ls) in style.items():
                v = np.array([bler(r, rx) if metric == "bler" else
                              counts(r, rx)[1] / (counts(r, rx)[0] * CODES[name][0]) for r in rs])
                ax.semilogy(x, np.where(v > 0, v, np.nan), ls, color=c, marker="o", markersize=3, label=rx)
            ax.set_title(SHORT[name])
            ax.set_xlabel("Eb/N0 [dB] (average)")
            ax.grid(True, which="both", linestyle=":", alpha=0.6)
        axes[0].set_ylabel(ylabel)
        axes[0].legend(fontsize=8)
        fig.suptitle(f"Zero-overhead receiver, {channel}: {ylabel} vs. Eb/N0 (512-symbol burst, no preamble, no CP)")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"zo_{metric}_vs_ebn0.png"), dpi=300, bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    for name, ls in zip(CODES, ("-", "--")):
        rs = sorted((r for r in results if r["code"] == name), key=lambda r: r["es"])
        es = [r["es"] for r in rs]
        for e, c in zip(cfo_list(results), ("#bbbbbb", "#ff7f0e", "#9ecae1", "#08519c", "#2ca02c", "#f4a6a6", "#d62728", "#67000d")):
            axes[0].semilogy(es, [np.median(np.abs(r["cfo_err"][e])) for r in rs], ls, color=c, label=f"{SHORT[name]}: {e}")
            axes[1].semilogy(es, [max(np.mean(np.abs(r["cfo_err"][e]) > OUTAGE), 1e-5) for r in rs], ls, color=c)
        axes[2].semilogy(es, [max(r["amb_err"] / r["frames"], 1e-5) for r in rs], ls, color="#ff7f0e",
                         label=f"{SHORT[name]}: CFO cell k wrong (CRC)")
        if "amb_err_nn" in rs[0]:
            axes[2].semilogy(es, [max(r["amb_err_nn"] / r["frames"], 1e-5) for r in rs], ls, color="#d62728",
                             label=f"{SHORT[name]}: CFO cell k wrong (NN + CRC)")
        axes[2].semilogy(es, [np.median(r["tap_nmse"]["Code-aided 3"]) for r in rs], ls, color="#08519c",
                         label=f"{SHORT[name]}: tap NMSE, code-aided 3 (median)")
        axes[2].semilogy(es, [np.median(r["tap_nmse"]["Known 512"]) for r in rs], ls, color="#2ca02c",
                         label=f"{SHORT[name]}: tap NMSE, known 512 (median)")
    for ax, yl in zip(axes, ("Median |CFO error| (cycles/symbol)", f"P(|CFO error| > {OUTAGE:g})", "Rate / NMSE")):
        ax.set_xlabel("Es/N0 [dB] (average)")
        ax.set_ylabel(yl)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
    axes[0].legend(fontsize=7)
    axes[2].legend(fontsize=7)
    fig.suptitle(f"Zero-overhead receiver, {channel}: CFO and channel estimation")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "zo_cfo_channel_metrics.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", choices=list(CHANNELS), default="multipath")
    ap.add_argument("--batch", type=int, default=100)
    ap.add_argument("--min-errors", type=int, default=200, help="frame errors of the main receiver per point")
    ap.add_argument("--min-frames", type=int, default=2000)
    ap.add_argument("--max-frames", type=int, default=10000)
    ap.add_argument("--workers", type=int, default=mp.cpu_count())
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--parts", type=int, default=1)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--plot-only", action="store_true")
    ap.add_argument("--refs-only", action="store_true", help="only Genie / Known 512 (MLSE, MMSE), many trials")
    ap.add_argument("--nn", default="", help="Stage 3: coarse NN model (coarse_nn.py); 8-SPS bursts, own folder")
    ap.add_argument("--nn-no-polish", action="store_true", help="NN estimate without the r^4 Newton polish")
    args = ap.parse_args()

    out_dir = os.path.join(HERE, f"results_zo2_{args.channel}" + ("_nn" if args.nn else ""))
    os.makedirs(out_dir, exist_ok=True)
    tag = ("_refs" if args.refs_only else "") + (f"_p{args.part}" if args.parts > 1 else "")
    args.progress = os.path.join(out_dir, f"run{tag}.progress")
    res_file = os.path.join(out_dir, "zo_results.npy")
    if args.plot_only:
        plot(list(np.load(res_file, allow_pickle=True)), out_dir)
        raise SystemExit
    log_f = open(os.path.join(out_dir, "run.log" if args.merge else f"run{tag}.log"), "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    if args.merge:
        results = [r for f in sorted(glob.glob(os.path.join(out_dir, "zo_results_p*.npy")))
                   for r in np.load(f, allow_pickle=True)]
        ref_dir = os.path.join(HERE, f"results_zo2_{args.channel}")    # same reference receivers, same statistics
        refs = {(r["code"], r["es"]): r for f in sorted(glob.glob(os.path.join(ref_dir, "zo_results_refs_p*.npy")))
                for r in np.load(f, allow_pickle=True)}
        for r in results:
            ref = refs.get((r["code"], r["es"]))
            if ref is not None:
                r["refs"] = {rx: (ref["frames"], ref["bit_err"][rx], ref["frame_err"][rx]) for rx in REF_RX}
        log(f"merged {len(results)} points, {len(refs)} with high-trial references")
    else:
        if os.path.exists(args.progress):
            os.remove(args.progress)
        results = run(args, log)
        if args.parts > 1:
            np.save(os.path.join(out_dir, f"zo_results{tag}.npy"), results, allow_pickle=True)
            log("=====\nPART DONE")
            raise SystemExit
    np.save(res_file, results, allow_pickle=True)
    report(results, log)
    validate(results, log)
    plot(results, out_dir)
    log("=====\nDONE")
