"""Replays decode rules on the CA-SCL-8 hypotheses saved by scl_traj.py (analysis only). Per search packet:
    current        cells in z order; per cell the best T=2 hypotheses by the list-1 metric decoded one at a time,
                   the first CRC pass accepted
    parallel       every hypothesis decoded with CA-SCL-8 in lockstep, no pruning; the CRC pass with the lowest
                   final path metric accepted (the best this stage can do)
    pruned         as parallel, but at each checkpoint a hypothesis whose best path metric exceeds the best alive one
                   by more than delta is dropped (the best kmin always survive)
Prints the share of packets with a right decode accepted, wrong CRC passes accepted (before rho_n), and the SCL work
in full CA-SCL-8 decodes per packet.
    BLIND_STUDY=small_cfo python blind/smoke/scl_traj_report.py --tag a"""
import argparse
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc


def current(D, T=2):
    right, wrong, dec = [], [], []
    for i in range(len(D["ok"])):
        n, got = 0, None
        for c in range(D["zc"].shape[1]):
            h = np.where(D["cand"] == c)[0]
            for j in h[np.argsort(D["m1"][i, h])][:T]:
                n += 1
                if D["ok"][i, j]:
                    got = j
                    break
            if got is not None:
                break
        right.append(got is not None and D["right"][i, got])
        wrong.append(got is not None and not D["right"][i, got])
        dec.append(n)
    return np.array(right), np.array(wrong), np.array(dec, float)


def pruned(D, delta=None, kmin=1):
    tr, ok, rt, ck = D["tr"], D["ok"], D["right"], D["ck"]
    P, H, C = tr.shape
    alive = np.ones((P, H), bool)
    work = np.zeros(P)
    prev = 0.0
    for j in range(C):
        work += alive.sum(1) * (ck[j] - prev)
        prev = ck[j]
        if delta is None or j == C - 1:
            continue
        x = np.where(alive, tr[:, :, j], np.inf)
        best = x.min(1, keepdims=True)
        keep = x <= best + delta
        top = np.argsort(x, 1)[:, :kmin]
        keep[np.arange(P)[:, None], top] = True
        alive &= keep
    fin = np.where(alive & ok, tr[:, :, -1], np.inf)
    j = fin.argmin(1)
    got = np.isfinite(fin[np.arange(P), j])
    return got & rt[np.arange(P), j], got & ~rt[np.arange(P), j], work


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="a")
    a = ap.parse_args()
    for fn in sorted(glob.glob(bc.path("results", f"scl_traj_{a.tag}_*.npz"))):
        D = dict(np.load(fn))
        P, H = D["ok"].shape
        print(f"\n== {os.path.basename(fn)}: {int(D['reached'])} of {int(D['packets'])} packets reach the search, "
              f"{H} hypotheses each; a right decode exists for {D['right'].any(1).mean():.4f}")
        r, w, d = current(D)
        print(f"  current (z order, 2 per cell by list-1):  right {r.mean():.4f}, wrong passes {w.mean():.4f}, "
              f"SCL decodes {d.mean():.2f}")
        r, w, d = pruned(D)
        print(f"  parallel, no pruning:                     right {r.mean():.4f}, wrong passes {w.mean():.4f}, "
              f"SCL decodes {d.mean():.2f}")
        for kmin in (1, 2, 4):
            for delta in (2, 5, 10, 20, 40, 80):
                r, w, d = pruned(D, delta, kmin)
                print(f"  pruned delta {delta:3d} kmin {kmin}:                right {r.mean():.4f}, "
                      f"wrong passes {w.mean():.4f}, SCL decodes {d.mean():.2f}")
