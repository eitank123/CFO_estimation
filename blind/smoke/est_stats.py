"""Estimation statistics of the current receiver stages (for blind_plots.coarse / estimation), per SNR:
    coarse CFO: lag-4 autocorrelation, 2-SPS spectral, 8-SPS spectral -> MSE, P(|error| > 1/8) (the 1/4 ambiguity of
        the 4th power resolved wrongly)
    fast path (pre-MF at the autocorrelation CFO, 4th power, 2 Newton steps) with the peak picked by: the strongest,
        the left code metric (top 4, >= 0.85 x max, blind), the 24 pilots (top 16, >= 0.7 x max), the peak NN (blind /
        pilots) -> MSE, outage P(|error| > 1e-4); P(true CFO among the top 1 / 4 / 16 peaks)
    search: rank of the true cell in the receiver's posterior (2-SPS statistics; + pilot ruler), grids of R = 1/10
        and 2/5 -> mean, P(rank >= K)
    python blind/smoke/est_stats.py --frames 4000          -> blind/results/est_stats.json"""
import argparse
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp

SNRS = (-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0)
KS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
POS = np.array(vp.PATTERNS["N3x8"])


def run(task):
    snr, n, seed = task
    code = bc.PiCode(bc.N_BITS, bc.CODES["2/5"], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    left = bf.fast_sc(code.A).metric_left
    try:
        import blind_peak_nn as pknn
        pknn.load("blind"), pknn.load("pilots")
        have_nn = True
    except Exception:
        have_nn = False
    rng = np.random.default_rng(seed)
    E = {k: [] for k in ("acf", "spec2", "spec8", "strongest", "metric", "pilots", "nn_blind", "nn_pilots")}
    inc = {1: 0, 4: 0, 16: 0}
    ranks = {"blind 1/10": [], "pilots 1/10": [], "blind 2/5": [], "pilots 2/5": []}
    tot = 0
    for _ in range(n // 200):
        _, cw, r, rx, f, _ = bc.frames(200, code, snr, rng)
        B = len(f)
        tot += B
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        fa = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
        E["acf"].append(fa - f)
        E["spec2"].append(vp.spectral_small(vp.decimate(rx)) - f)
        E["spec8"].append(bc.spectral(rx) - f)
        r1 = bf.premf(r, rx, fa)
        y4 = -(r1 ** 4)
        Y4a = np.abs(np.fft.fft(y4, bc.NFFT4))
        pk = bc.top_peaks(Y4a, 16, 2)
        fc = bc.resolve(np.fft.fftfreq(bc.NFFT4)[pk], fa)
        hp = np.take_along_axis(Y4a, pk, 1)
        hit = np.abs(fc - f[:, None]) < 1.5e-4
        for K in inc:
            inc[K] += int(hit[:, :K].any(1).sum())
        zp = r1[:, POS] * np.conj(sym[:, POS])
        rows = np.arange(B)

        def final(jb):
            nu, _ = bc._newton_tone(y4, np.fft.fftfreq(bc.NFFT4)[pk[rows, jb]][:, None], 2)
            return bc.resolve((nu + 0.5) % 1.0 - 0.5, fc[rows, jb])[:, 0] - f

        E["strongest"].append(final(np.zeros(B, int)))
        sp = np.abs(np.einsum("bk,bpk->bp", zp, np.exp(-2j * np.pi * fc[:, :, None] * (POS - bc.CENTRE)[None, None])))
        E["pilots"].append(final(np.where(hp >= 0.7 * hp[:, :1], sp, -1).argmax(1)))
        sc = np.full((B, 4), np.inf)
        for j in range(4):
            live = hp[:, j] >= 0.85 * hp[:, 0]
            if j == 0:
                live[:] = True
            w = np.where(live)[0]
            if len(w):
                t = bc.phase4(r1[w], fc[w, j])
                sc[w, j] = np.minimum(*[left(bc.llrs(r1[w], fc[w, j], t + q * np.pi / 2, sigma2), 1) for q in range(2)])
        E["metric"].append(final(sc.argmin(1)))
        if have_nn:
            for mode, z in (("blind", None), ("pilots", zp)):
                x, _, _ = pknn.features(r1, Y4a, fa, snr, z, POS if z is not None else None)
                E[f"nn_{mode}"].append(final(pknn.grade(mode, x)[:, :16].argmax(1)))
        # the receiver's posterior for the search (2-SPS statistics, pre-MF at their spectral estimate)
        for rate in ("1/10", "2/5"):
            k = bf.grid_step(rate, snr)
            g = bf.grid(k)["f"]
            _, fs, C = vp.features_lite(r, rx, k)
            r2 = bf.premf(r, rx, fs)
            post = bf.posterior2(vp.s4_grid(r2, k), fs, C, snr, k)
            t = np.abs(g[None] - f[:, None]).argmin(1)
            for mode in ("blind", "pilots"):
                pp = post
                if mode == "pilots":
                    pp = post + vp.pilot_loglik(vp.pilot_A(r2[:, POS] * np.conj(sym[:, POS]), POS, g), snr)
                ranks[f"{mode} {rate}"].append((pp > pp[rows, t][:, None]).sum(1))
    out = {"snr": snr, "frames": tot, "est": {}, "inclusion": {str(K): v / tot for K, v in inc.items()}, "search": {}}
    for k, v in E.items():
        if v:
            e = np.concatenate(v)
            out["est"][k] = {"mse": float(np.mean(e ** 2)), "outage": float(np.mean(np.abs(e) > bc.TOL)),
                             "wrong_quarter": float(np.mean(np.abs(e) > 0.125))}
    for k, v in ranks.items():
        rk = np.concatenate(v)
        out["search"][k] = {"mean": float(rk.mean()), "P_ge": {str(K): float(np.mean(rk >= K)) for K in KS}}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=4000)
    a = ap.parse_args()
    with Pool(len(SNRS)) as pool:
        res = pool.map(run, [(s, a.frames, 900 + i) for i, s in enumerate(SNRS)])
    json.dump(res, open(bc.path("results", "est_stats.json"), "w"), indent=1)
    for r in res:
        print(r["snr"], {k: round(v["outage"], 4) for k, v in r["est"].items()}, flush=True)
    print("SMOKE DONE", flush=True)
