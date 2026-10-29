"""False CRC passes ("staircase" codewords of a wrong CFO): can a data-aided consistency check separate them from the
right decodes? Every packet is decoded at its top 8 4th-power peaks (pre-MF at the lag-4 autocorrelation CFO, 2 Newton
steps), both pi/2 branches; every CRC pass with rho > rho_min is kept with
    rho / sqrt(s / (1 + s)), the PiCode path metric, |f - f_acf| / sigma, peak rank / height ratio, and the data-aided
    residual z = r s_dec* e^{-j 2 pi f nc}: angle of its lag-1 and lag-4 autocorrelation (a staircase decode turns by
    2 pi Delta per symbol inside its pi/2 steps; a right decode does not), circular spread of angle(z)
and labelled right / false. Prints the separation per feature (false passes caught when the threshold keeps 99.9 % of
the right passes) and saves the rows for an NN (blind/results/fp_rows_<tag>.npz).
    python blind/smoke/fp_check.py --points 2/5:1:24000 --tag r25"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
from polar import PolarCode

K = 8
FEATS = ("rho_n", "pm", "dist_acf", "rank", "hratio", "a1", "a4", "spread", "snr")


def run(job):
    rate, snr, n, seed = job
    code = PolarCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    pi = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    s_lin = 10 ** (snr / 10)
    sig = float(np.interp(snr, *zip(*bf.ACF_SIGMA)))
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n // 100):
        data, cw, r, rx, f, th = bc.frames(100, code, snr, rng)
        B = len(f)
        fa = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
        r1 = bf.premf(r, rx, fa)
        y4 = -(r1 ** 4)
        Y4a = np.abs(np.fft.fft(y4, bc.NFFT4))
        pk = bc.top_peaks(Y4a, K, 2)
        hp = np.take_along_axis(Y4a, pk, 1)
        fc = bc.resolve(np.fft.fftfreq(bc.NFFT4)[pk], fa)
        nu, _ = bc._newton_tone(y4, np.fft.fftfreq(bc.NFFT4)[pk], 2)
        nu = (nu + 0.5) % 1.0 - 0.5
        F = nu / 4 + np.round((fc - nu / 4) * 4) / 4           # each peak resolved against its own coarse CFO
        for j in range(K):
            f0 = F[:, j]
            t0 = bc.phase4(r1, f0)
            for q in (0, 1):
                d, ok, pm = pi.decode(bc.llrs(r1, f0, t0 + q * np.pi / 2, sigma2), return_info=True)
                w = np.where(ok)[0]
                if not len(w):
                    continue
                rho = bf.reencode_rho(pi, r1[w], d[w], f0[w])
                keep = rho > bf.rho_min(snr)
                w, rho = w[keep], rho[keep]
                if not len(w):
                    continue
                c = pi.encode(d[w])[:, bc.INTERLEAVER]
                s = ((1 - 2.0 * c[:, 0::2]) + 1j * (1 - 2.0 * c[:, 1::2])) / np.sqrt(2)
                z = r1[w] * np.conj(s) * np.exp(-2j * np.pi * f0[w][:, None] * bc.NC[None])
                a1 = np.angle(np.sum(z[:, 1:] * np.conj(z[:, :-1]), 1))
                a4 = np.angle(np.sum(z[:, 4:] * np.conj(z[:, :-4]), 1)) / 4
                u = z / np.maximum(np.abs(z), 1e-12)
                spread = 1 - np.abs(u.mean(1))
                right = (d[w] == data[w]).all(1)
                for k, i in enumerate(w):
                    rows.append((rho[k] / np.sqrt(s_lin / (1 + s_lin)), pm[i] / bc.N_BITS, abs(f0[i] - fa[i]) / sig,
                                 j / K, hp[i, j] / hp[i, 0], a1[k], a4[k], spread[k], snr / 10, float(right[k])))
    return rate, snr, np.array(rows, np.float32).reshape(-1, len(FEATS) + 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True)          # rate:snr:packets
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--tag", default="x")
    a = ap.parse_args()
    jobs = []
    for pt in a.points:
        rate, snr, n = pt.split(":")
        jobs += [(rate, float(snr), int(n) // a.chunks, 9100 + c) for c in range(a.chunks)]
    agg = {}
    with Pool(16) as pool:
        for rate, snr, rows in pool.imap_unordered(run, jobs):
            agg.setdefault((rate, snr), []).append(rows)
    allrows = []
    for (rate, snr), parts in sorted(agg.items()):
        X = np.concatenate(parts)
        allrows.append(X)
        y = X[:, -1] > 0.5
        print(f"R={rate} {snr:+.1f} dB: {y.sum()} right passes, {(~y).sum()} false passes (rho above rho_min)", flush=True)
        if (~y).sum() == 0 or y.sum() == 0:
            continue
        for k, nm in enumerate(FEATS[:-1]):
            v = X[:, k]
            for sign, lab in ((1, ">"), (-1, "<")):
                # threshold keeping 99.9 % of the right passes; the share of false passes beyond it
                t = np.quantile(sign * v[y], 0.999)
                caught = np.mean(sign * v[~y] > t)
                if caught > 0.3:
                    print(f"    {nm:8s} {lab} {sign * t:+.4f}: catches {caught:.2f} of the false passes "
                          f"(right: median {np.median(v[y]):+.4f}, false: median {np.median(v[~y]):+.4f})", flush=True)
            if nm in ("rho_n", "a1", "a4"):
                print(f"    {nm:8s} quantiles right {np.round(np.quantile(v[y], [0.001, 0.5, 0.999]), 4)} "
                      f"false {np.round(np.quantile(v[~y], [0.0, 0.5, 1.0]), 4)}", flush=True)
    np.savez(bc.path("results", f"fp_rows_{a.tag}.npz"), X=np.concatenate(allrows), feats=np.array(FEATS))
    print("SMOKE DONE", flush=True)
