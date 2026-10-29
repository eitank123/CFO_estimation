"""Smoke: per-packet MAC distribution of a receiver, by outcome, plus decodes / metric evaluations per packet.
    python blind/smoke/profile_pp.py --points 1/10:-3 --frames 2000 --rx "v3 eco + CRC" """
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
import blind_ber as bb


def run(job):
    rate, snr, nm, n = job
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    rng = np.random.default_rng(7)
    spec = {**bb.RX[nm]}
    spec["sps"] = {**spec["sps"], "rate": rate}
    st = dict(decodes=0, metric_evals=0, macs_pp=[])
    OK, BAD = [], []
    for _ in range(n // 250):
        data, cw, r, rx, f, th = bc.frames(250, code, snr, rng)
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        dec, ok, ff, ftop = bf.sps3_receive(r, rx, snr, code, sigma2, st, spec, sym)
        OK.append(ok)
        BAD.append((dec != data).any(1))
    M = np.concatenate(st["macs_pp"]) / 1e6
    OK, BAD = np.concatenate(OK), np.concatenate(BAD)
    tot = M.sum()
    q = np.quantile(M, [0.1, 0.5, 0.9, 0.99])
    out = [f"R={rate} {snr} dB {nm}: mean {M.mean():.2f} M (p10 {q[0]:.2f}, median {q[1]:.2f}, p90 {q[2]:.2f}, "
           f"p99 {q[3]:.2f}, max {M.max():.1f}); decodes {st['decodes'] / n:.2f}, metric evals {st['metric_evals'] / n:.1f}"]
    for lab, m in (("CRC pass, correct", OK & ~BAD), ("CRC pass, wrong", OK & BAD), ("no CRC pass", ~OK)):
        out.append(f"    {lab:18s} {m.sum():5d} packets, mean {M[m].mean() if m.any() else 0:.2f} M, "
                   f"{M[m].sum() / tot:.1%} of the MACs")
    edges = [0, 1, 2, 4, 8, 16, 32, 1e9]
    h = np.histogram(M, edges)[0]
    out.append("    MACs histogram (M): " + ", ".join(f"[{edges[i]},{edges[i + 1]}) {h[i] / n:.1%}"
                                                   for i in range(len(h)) if h[i]))
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True)
    ap.add_argument("--rx", nargs="+", required=True)
    ap.add_argument("--frames", type=int, default=2000)
    a = ap.parse_args()
    jobs = [(pt.split(":")[0], float(pt.split(":")[1]), nm, a.frames) for pt in a.points for nm in a.rx]
    with Pool(min(16, len(jobs))) as pool:
        for line in pool.imap(run, jobs):
            print(line, flush=True)
    print("SMOKE DONE", flush=True)
