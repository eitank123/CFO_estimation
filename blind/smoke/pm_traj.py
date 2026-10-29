"""Partial path metrics along the decode: can wrong CFO cells be dropped (or the whole CFO search ended) before the
list-1 Fast-SSC metric is complete? For every packet, every cell of the CFO grid (all phases; the cell's 4th-power
phase + q pi/4) is scored with FastSC.metric_nodes; the cumulative path metric at checkpoints (leaf boundaries
nearest CK of the codeword, in decoding order) is turned into the packet's robust z per checkpoint
    z_c = (median_cells(PM_c) - PM_c(cell)) / (1.4826 MAD_cells(PM_c)),   PM_c(cell) = min over the phases,
and saved (float16) with the true cell and the raw partial path metrics PM_c (float32: any pruning rule, e.g. z among
the cells still alive, can then be replayed exactly offline) for the pruning / early-stop analysis.
Run in the small-CFO study (BLIND_STUDY=small_cfo):
    python blind/smoke/pm_traj.py --points 1/10:-5:4000 2/5:0.5:4000 1/2:2:4000 --tag a"""
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp
from polar import PolarCode

CK = (1 / 32, 1 / 16, 3 / 32, 1 / 8, 3 / 16, 1 / 4, 3 / 8, 1 / 2, 5 / 8, 3 / 4, 1.0)    # fractions of the codeword
SPLIT = 64                     # rate-0 nodes reported in chunks of 64 bits (checkpoints inside a long frozen block)


def leaves(plan, lo, hi, out, split=None):
    """(lo, hi) of every leaf node of a FastSC plan, in decoding order (rate-0 nodes in chunks of `split` bits, as
    FastSC.metric_nodes with FastSC.split)."""
    if plan[0] == "R0" and split and hi - lo > split:
        out += [(c, c + split) for c in range(lo, hi, split)]
        return out
    if plan[0] != "N":
        out.append((lo, hi))
        return out
    mid = (lo + hi) // 2
    leaves(plan[1], lo, mid, out, split)
    leaves(plan[2], mid, hi, out, split)
    return out


def run(job):
    rate, snr, n, seed = job
    code = PolarCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    fs_ = bf.FastSC(bf.fast_sc(code.A).frozen)
    fs_.split = SPLIT
    lv = leaves(fs_.plan, 0, bc.N_BITS, [], SPLIT)
    ends = np.array([h for _, h in lv])
    # checkpoint = number of leaves whose end is <= the target bit position (at least one leaf)
    nl = np.array([max(1, int((ends <= c * bc.N_BITS).sum())) for c in CK])
    frac = ends[nl - 1] / bc.N_BITS                            # the exact fraction of the codeword at each checkpoint
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    k = bf.grid_step(rate, snr)
    g = bf.grid(k)["f"]
    nph = 4 if snr < -1 else 2
    qs = np.arange(nph) * (2 if nph == 2 else 1)              # phase offsets in pi/4 units
    rng = np.random.default_rng(seed)
    Z = np.zeros((n, len(CK), len(g)), np.float16)
    PMs = np.zeros((n, len(CK), len(g)), np.float32)
    LLP = np.zeros((n, len(g)), np.float32)                   # the 24 pilots' (N3x8) log-likelihood of each cell
    pos = np.array(vp.PATTERNS["N3x8"])
    true = np.zeros(n, np.int32)
    for i0 in range(0, n, 50):
        data, cw, r, rx, f, th = bc.frames(min(50, n - i0), code, snr, rng)
        for b in range(len(f)):
            i = i0 + b
            true[i] = int(np.abs(g - f[b]).argmin())
            sym = ((1 - 2.0 * cw[b, 0::2]) + 1j * (1 - 2.0 * cw[b, 1::2])) / np.sqrt(2)
            LLP[i] = vp.pilot_loglik(vp.pilot_A((r[b, pos] * np.conj(sym[pos]))[None], pos, g), snr)[0]
            t4 = bc.phase4(np.repeat(r[b:b + 1], len(g), 0), g)               # the cells' 4th-power phases
            P = np.full((nph, len(g), len(CK)), np.inf, np.float32)
            for jq, q in enumerate(qs):
                llr = bc.llrs(np.repeat(r[b:b + 1], len(g), 0), g, t4 + q * np.pi / 4, sigma2)
                C = np.cumsum(fs_.metric_nodes(llr), 1)                       # (cells, leaves)
                P[jq] = C[:, nl - 1]
            pm = P.min(0)                                                     # (cells, checkpoints)
            med = np.median(pm, 0)
            mad = 1.4826 * np.median(np.abs(pm - med[None]), 0) + 1e-6
            Z[i] = ((med[None] - pm) / mad[None]).T.astype(np.float16)
            PMs[i] = pm.T
    return rate, snr, k, frac, Z, PMs, LLP, true


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True)          # rate:snr:packets
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--tag", default="a")
    a = ap.parse_args()
    jobs = []
    for pt in a.points:
        rate, snr, n = pt.split(":")
        jobs += [(rate, float(snr), int(n) // a.chunks, 9300 + c) for c in range(a.chunks)]
    agg = {}
    with Pool(16) as pool:
        for rate, snr, k, frac, Z, PMs, LLP, true in pool.imap_unordered(run, jobs):
            e = agg.setdefault((rate, snr), {"k": k, "frac": frac, "Z": [], "PM": [], "LLP": [], "true": []})
            e["LLP"].append(LLP)
            e["Z"].append(Z)
            e["PM"].append(PMs)
            e["true"].append(true)
            print(f"chunk done R={rate} {snr:+.1f} dB ({len(true)} packets)", flush=True)
    for (rate, snr), e in agg.items():
        Z, true = np.concatenate(e["Z"]), np.concatenate(e["true"])
        tag = f"{rate.replace('/', '_')}_{snr:g}".replace("-", "m").replace(".", "p")
        np.savez_compressed(bc.path("results", f"pm_traj_{a.tag}_{tag}.npz"), Z=Z, PM=np.concatenate(e["PM"]),
                            LLP=np.concatenate(e["LLP"]),
                            true=true, frac=e["frac"],
                            k=e["k"], ck=np.array(CK), max_cfo=bc.MAX_CFO)
        zt = Z[np.arange(len(true)), :, true].astype(np.float32)               # (packets, checkpoints)
        print(f"R={rate} {snr:+.1f} dB, {len(true)} packets, {Z.shape[2]} cells (k={e['k']}): true-cell z per "
              f"checkpoint (0.1 % / median): " + ", ".join(f"{fr:.3f}: {np.quantile(zt[:, j], 0.001):.1f} / "
                                                          f"{np.median(zt[:, j]):.1f}" for j, fr in enumerate(e["frac"])),
              flush=True)
    print("SMOKE DONE", flush=True)
