"""Smoke: can a failed 4th-power fast path be rescued from the other 4th-power peaks? For the top P peaks of the
4th-power FFT (after the autocorrelation pre-MF), Newton-refined and resolved: rank of the peak at the true CFO, by
peak height and by the 24-pilot (N3x8) coherent sum.
    python blind/smoke/s4_rank.py --points 2/5:0.5 2/5:1 1/10:-3 1/10:-1 --frames 4000"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp

ap = argparse.ArgumentParser()
ap.add_argument("--points", nargs="+", default=["2/5:0.5", "2/5:1"])
ap.add_argument("--frames", type=int, default=4000)
ap.add_argument("--P", type=int, default=16)
a = ap.parse_args()
pos = np.array(vp.PATTERNS["N3x8"])
nc = pos - bc.CENTRE
for pt in a.points:
    rate, snr = pt.split(":")
    snr = float(snr)
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    rng = np.random.default_rng(11)
    rk_h, rk_p = [], []
    for _ in range(a.frames // 500):
        data, cw, r, rx, f, th = bc.frames(500, code, snr, rng)
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        fa = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
        r1 = bf.premf(r, rx, fa)
        nu, _ = bc.fourth_power(r1, P=a.P)
        nu, _ = bc._newton_tone(-(r1 ** 4), nu, 2)
        fc = bc.resolve((nu + 0.5) % 1.0 - 0.5, fa)                       # (B, P), ordered by peak height
        hit = np.abs(fc - f[:, None]) < 1e-4
        zp = r1[:, pos] * np.conj(sym[:, pos])
        sp = np.abs(np.einsum("bk,bpk->bp", zp, np.exp(-2j * np.pi * fc[:, :, None] * nc[None, None])))
        op = np.argsort(-sp, 1)
        rk_h.append(np.where(hit.any(1), hit.argmax(1), a.P))
        rk_p.append(np.where(hit.any(1), np.take_along_axis(hit, op, 1).argmax(1), a.P))
    rk_h, rk_p = np.concatenate(rk_h), np.concatenate(rk_p)
    print(f"R={rate} {snr} dB, {len(rk_h)} packets: true CFO among the top {a.P} peaks {np.mean(rk_h < a.P):.3f}", flush=True)
    for K in (1, 2, 4, 8, 16):
        print(f"   within top {K:2d}: by height {np.mean(rk_h < K):.3f}   by 24 pilots {np.mean(rk_p < K):.3f}", flush=True)
print("SMOKE DONE", flush=True)
