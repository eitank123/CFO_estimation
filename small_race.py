"""
Replay of pruning rules for the small-CFO search (small_rx.py, BLIND_STUDY=small_cfo) on real search packets: every
(cell, phase) hypothesis is a list-1 Fast-SSC decode running in parallel; the rules drop hypotheses at checkpoints
along the decode by their path metrics (PM), as an SCL decoder drops paths. Per rule: the work (fraction of decoding
every cell x phase in full) and how often the true hypothesis is lost (true cell = nearest to the CFO; its phase =
the one with the best full-codeword PM), strict (that phase) and per cell (every phase of the true cell lost).

Rules (checkpoints CK_FR = 1/16, 1/8, 3/16, 1/4, 5/16, 3/8, 1/2, 3/4, 1):
    z            the receiver's z-test (robust z of the cells' best-phase PM among the alive cells; z <= tau dropped,
                 the best 16 kept; every phase of a kept cell continues), per-rate checkpoints as blind_ber CK_S
    phase        at one checkpoint each cell keeps only its phases within dp nats of its best phase, then z
    gap          from checkpoint j0 on, hypotheses with PM > best PM + delta are dropped (at every checkpoint)
    beam         at j0 the best K hypotheses are kept, half as many at each later checkpoint (>= 4)
    phase+gap    phase racing, then gap

    BLIND_STUDY=small_cfo python small_race.py --points 1/10:-5 1/10:-4.5 --packets 30000 --workers 16
"""
import argparse
import json
import multiprocessing as mp
import time

import numpy as np

import blind_cfo as bc
import blind_fast as bf
import small_rx as sr
from small_ck_nn import _batch

F = np.array(sr.CK_FR)
J = {f: i for i, f in enumerate(sr.CK_FR)}
CK_S = {"1/10": (0.5,), "2/5": (0.25, 0.375, 0.5, 0.75), "1/2": (0.125, 0.25, 0.5)}   # blind_ber CK_S / TAU_S
TAU_S = {"1/10": 1.0, "2/5": -1.0, "1/2": -1.0}
DELTAS = (5, 10, 15, 20, 30, 40, 60, 80)
DPS = (2, 5, 10, 20)
KS = (8, 16, 32, 64, 128, 256)
KEEP = (0.75, 0.5)                       # early checkpoint: the best share of the hypotheses kept


def _zkeep(P, A, j, tau, kmin=16):
    cell = np.where(A, P[:, :, j], np.inf).min(1)
    alive = A.any(1)
    s = cell[alive]
    med = np.median(s)
    z = np.full(len(cell), -np.inf)
    z[alive] = (med - s) / (1.4826 * np.median(np.abs(s - med)) + 1e-6)
    keep = z > tau
    keep[np.argsort(-z)[:kmin]] = True
    return A & (keep & alive)[:, None]


def rules(rate):
    """name -> {checkpoint index: [actions]}; action = (kind, parameter)."""
    zs = {J[c]: [("z", TAU_S[rate])] for c in CK_S[rate]}
    out = {"z (receiver)": zs}
    for fp in (1 / 8, 1 / 4, 1 / 2):
        for dp in DPS:
            r = {j: list(a) for j, a in zs.items()}
            r.setdefault(J[fp], []).insert(0, ("phase", dp))
            out[f"phase {dp} @{fp:g} + z"] = r
    for f0 in (1 / 4, 3 / 8, 1 / 2):
        for d in DELTAS:
            out[f"gap {d} from {f0:g}"] = {j: [("gap", d)] for j in range(J[f0], len(F) - 1)}
            out[f"phase 5 @{f0:g} + gap {d}"] = {j: ([("phase", 5)] if j == J[f0] else []) + [("gap", d)]
                                                 for j in range(J[f0], len(F) - 1)}
        for K in KS:
            out[f"beam {K} from {f0:g}"] = {j: [("beam", max(4, K >> (j - J[f0])))] for j in range(J[f0], len(F) - 1)}
    # an extra lenient checkpoint before the receiver's first one: keep the best share p of the hypotheses there,
    # then the z-test, or a beam from 1/2
    first = min(CK_S[rate])
    for f1 in (1 / 8, 1 / 4, 5 / 16, 3 / 8):
        for p in KEEP:
            pre = {J[f1]: [("share", p)]}
            if f1 < first:
                out[f"keep {p:g} @{f1:g} + z"] = {**{j: list(a) for j, a in zs.items()}, **pre}
            for K in (16, 32, 64, 128):
                out[f"keep {p:g} @{f1:g} + beam {K} from 0.5"] = {
                    **pre, **{j: [("beam", max(4, K >> (j - J[0.5])))] for j in range(J[0.5], len(F) - 1)}}
    return out


def replay(P, t, R, W):
    """P (G, Q, len(F)) PMs of one packet, t its true cell, W (len(F),) the share of a full Fast-SSC pass spent up to
    each checkpoint. Returns {rule: (lost strict, lost cell, lost cell and both neighbours, work)}."""
    G, Q, _ = P.shape
    qt = int(P[t, :, -1].argmin())
    res = {}
    for name, acts in R.items():
        A = np.ones((G, Q), bool)
        work, prev = 0.0, 0.0
        for j, f in enumerate(F):
            work += (W[j] - prev) * A.sum()
            prev = W[j]
            if j == len(F) - 1:
                break
            for kind, v in acts.get(j, ()):
                if kind == "z":
                    A = _zkeep(P, A, j, v)
                elif kind == "phase":
                    best = np.where(A, P[:, :, j], np.inf).min(1, keepdims=True)
                    A &= P[:, :, j] <= best + v
                elif kind == "gap":
                    A &= P[:, :, j] <= np.where(A, P[:, :, j], np.inf).min() + v
                elif kind in ("beam", "share"):
                    if kind == "share":
                        v = int(np.ceil(v * A.sum()))
                    s = np.where(A, P[:, :, j], np.inf).ravel()
                    if np.isfinite(s).sum() > v:
                        k = np.zeros(s.size, bool)
                        k[np.argpartition(s, v)[:v]] = True
                        A &= k.reshape(G, Q)
        res[name] = (not A[t, qt], not A[t].any(), not A[max(t - 1, 0):t + 2].any(), work / (G * Q))
    return res


def _work(task):
    rate, snr, n, seed = task
    rng = np.random.default_rng(seed)
    R = rules(rate)
    W = sr.cost_share(bf.fast_sc(bc.CODES[rate]).plan, F)
    acc = {k: np.zeros(4) for k in R}
    done = 0
    while done < n:
        b = _batch(50, rng, "blind", rate, snr)
        if b is None:
            continue
        _, pm, t = b
        for i in range(min(len(t), n - done)):
            for k, v in replay(pm[i, :, :, :, 0], int(t[i]), R, W).items():
                acc[k] += v
        done += min(len(t), n - done)
    return rate, snr, n, {k: v.tolist() for k, v in acc.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True, help="rate:snr")
    ap.add_argument("--packets", type=int, default=30000, help="search packets per point")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=61)
    ap.add_argument("--part", required=True)
    a = ap.parse_args()
    pts = [(p.split(":")[0], float(p.split(":")[1])) for p in a.points]
    per = -(-a.packets // a.workers)
    tasks = [(r, s, per, a.seed + 1000 * k + i) for k, (r, s) in enumerate(pts) for i in range(a.workers)]
    t0 = time.time()
    tot = {}
    with mp.Pool(a.workers) as pool:
        for rate, snr, n, acc in pool.imap_unordered(_work, tasks):
            T = tot.setdefault((rate, snr), {"n": 0, "acc": {}})
            T["n"] += n
            for k, v in acc.items():
                T["acc"][k] = (np.array(T["acc"].get(k, 0)) + np.array(v)).tolist()
            print(f"{rate} {snr:+.1f}: {T['n']} packets ({time.time() - t0:.0f}s)", flush=True)
    out = []
    for (rate, snr), T in tot.items():
        n = T["n"]
        print(f"\n== {rate} {snr:+.1f} dB, {n} search packets: rule | lost: true phase, true cell, cell and "
              f"neighbours | work (share of every cell x phase decoded in full, Fast-SSC cost)")
        rows = sorted(((k, *(np.array(v) / n)) for k, v in T["acc"].items()), key=lambda r: r[4])
        for k, ls, lc, ln, w in rows:
            print(f"  {k:36s} {ls:.2e} {lc:.2e} {ln:.2e} {w:.3f}")
            out.append({"rate": rate, "snr": snr, "packets": n, "rule": k, "lost_phase": ls, "lost_cell": lc,
                        "lost_nb": ln, "work": w})
    json.dump(out, open(bc.path("results", f"race_{a.part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)
