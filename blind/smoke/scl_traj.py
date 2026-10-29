"""Can the CA-SCL-8 decodes of the refinement hypotheses also run in parallel and be pruned by their path metric?
For every packet the fast path does not deliver (small-CFO study, as small_rx: 4th-power fast path, pre-MF at it),
the whole grid is scored with the list-1 metric, the top NC cells by z are refined as in blind_fast._refine2
(+-k/2 STEP x phase sub-offsets, the cell's pi/2 branch) and EVERY refinement hypothesis is decoded with CA-SCL-8
(PiCode.decode_traced): the list's best path metric at checkpoints CK, the final CRC pass, right / wrong, its list-1
metric (the current rule decodes the best T of a cell by it) are saved for the offline replay (scl_traj_report.py).
    BLIND_STUDY=small_cfo python blind/smoke/scl_traj.py --points 1/10:-5:2000 2/5:0.5:4000 1/2:2:6000 --tag a"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
from polar import PolarCode

CK = (1 / 8, 1 / 4, 3 / 8, 1 / 2, 5 / 8, 3 / 4, 7 / 8, 1.0)
NC = 4


def run(job):
    rate, snr, n, seed = job
    code = PolarCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    pi = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    fs_ = bf.fast_sc(code.A)
    ends = [int(c * bc.N_BITS) for c in CK]
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    k = bf.grid_step(rate, snr)
    g = bf.grid(k)["f"]
    nph = 4 if snr < -1 else 2
    qs = np.arange(nph) * (2 if nph == 2 else 1)
    roffs = np.arange(-(k // 2), k // 2 + 1)
    sub = (-np.pi / 12, 0.0, np.pi / 12) if nph == 4 else (0.0,)
    H = NC * len(roffs) * len(sub)
    rng = np.random.default_rng(seed)
    rows = []                                                 # per search packet
    reached = 0
    for _ in range(n // 50):
        data, cw, r_mf, rx, f, th_true = bc.frames(50, code, snr, rng)
        nf = bc.NFFT4
        nu_b = np.fft.fftfreq(nf)
        Y4 = np.abs(np.fft.fft(-(r_mf ** 4), nf, axis=1))
        Y4 = np.where(np.abs(nu_b)[None] <= 4 * bc.MAX_CFO + 2.0 / nf, Y4, 0.0)
        kb = Y4.argmax(1)
        V = Y4[np.arange(len(f))[:, None], (kb[:, None] + np.array([-1, 0, 1])[None]) % nf]
        den = V[:, 0] - 2 * V[:, 1] + V[:, 2]
        off = np.clip(np.where(den < 0, 0.5 * (V[:, 0] - V[:, 2]) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
        f0 = np.clip((nu_b[kb] + off / nf) / 4, -bc.MAX_CFO, bc.MAX_CFO)
        r = bf.premf(r_mf, rx, f0)
        th0 = bc.phase4(r, f0)
        M2 = np.stack([fs_.metric(bc.llrs(r, f0, th0 + q * np.pi / 2, sigma2)) for q in range(2)])
        d, ok, _ = pi.decode(bc.llrs(r, f0, th0 + M2.argmin(0) * np.pi / 2, sigma2), return_info=True)
        fast_ok = ok & (d == data).all(1)
        for b in np.where(~fast_ok)[0]:
            reached += 1
            rb = np.repeat(r[b:b + 1], len(g), 0)
            t4 = bc.phase4(rb, g)
            P = np.stack([fs_.metric(bc.llrs(rb, g, t4 + q * np.pi / 4, sigma2)) for q in qs])
            pm, qb = P.min(0), P.argmin(0)
            med = np.median(pm)
            z = (med - pm) / (1.4826 * np.median(np.abs(pm - med)) + 1e-6)
            top = np.argsort(-z)[:NC]
            tcell = int(np.abs(g - f[b]).argmin())
            F = (g[top][:, None] + roffs[None] * bc.STEP)                       # (NC, offsets)
            TH = bc.phase4(np.repeat(r[b:b + 1], NC, 0), F)
            tc = t4[top] + qb[top] * np.pi / 4
            TH = TH + np.round((tc[:, None] - TH) / (np.pi / 2)) * (np.pi / 2)
            F = np.repeat(F, len(sub), 1).ravel()
            TH = (TH[:, :, None] + np.array(sub)[None, None]).ravel()
            rh = np.repeat(r[b:b + 1], H, 0)
            L = bc.llrs(rh, F, TH, sigma2)
            m1 = fs_.metric(L)                                                  # list-1 metric (current ranking)
            dd, okh, pmh, tr = pi.decode_traced(L, ends)
            right = okh & (dd == data[b]).all(1)
            rows.append(dict(tr=tr, m1=m1, ok=okh, right=right, cand=np.repeat(np.arange(NC), len(roffs) * len(sub)),
                             zc=z[top], true_rank=int((z > z[tcell]).sum()), ferr=np.abs(F - f[b])))
    return rate, snr, reached, n, rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True)          # rate:snr:packets
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--tag", default="a")
    a = ap.parse_args()
    jobs = []
    for pt in a.points:
        rate, snr, n = pt.split(":")
        jobs += [(rate, float(snr), int(n) // a.chunks, 9500 + c) for c in range(a.chunks)]
    agg = {}
    with Pool(16) as pool:
        for rate, snr, reached, n, rows in pool.imap_unordered(run, jobs):
            e = agg.setdefault((rate, snr), {"reached": 0, "n": 0, "rows": []})
            e["reached"] += reached
            e["n"] += n
            e["rows"] += rows
            print(f"chunk done R={rate} {snr:+.1f} dB", flush=True)
    for (rate, snr), e in agg.items():
        R = e["rows"]
        tag = f"{rate.replace('/', '_')}_{snr:g}".replace("-", "m").replace(".", "p")
        np.savez_compressed(bc.path("results", f"scl_traj_{a.tag}_{tag}.npz"),
                            tr=np.stack([x["tr"] for x in R]), m1=np.stack([x["m1"] for x in R]),
                            ok=np.stack([x["ok"] for x in R]), right=np.stack([x["right"] for x in R]),
                            cand=R[0]["cand"] if R else np.zeros(0), zc=np.stack([x["zc"] for x in R]),
                            true_rank=np.array([x["true_rank"] for x in R]), ferr=np.stack([x["ferr"] for x in R]),
                            ck=np.array(CK), reached=e["reached"], packets=e["n"])
        rt = np.stack([x["right"] for x in R])
        print(f"R={rate} {snr:+.1f} dB: {e['reached']} of {e['n']} packets reach the search; a right decode among the "
              f"hypotheses for {rt.any(1).mean():.4f} of them", flush=True)
    print("SMOKE DONE", flush=True)
