"""
Cut-size NN for the small-CFO search (blind): at one checkpoint, how many cells must survive so that the true cell does
with probability TAU. The checkpoint NN (small_ck_nn.py) orders the cells; this small MLP predicts, per packet, the
TAU-quantile of the true cell's rank in that order (pinball loss on log(1 + rank)), from packet-level features: SNR,
grid step, the checkpoint NN's top probability, top-2 log-probability gap, entropy, its cumulative-probability
shortlist sizes at 1e-2 .. 1e-6, and the z-test's best / 2nd / 16th z. Compared offline against the z-test and the
checkpoint NN's fixed-threshold shortlist: misses of the true cell (and of the cell and both neighbours) and the work
(share of decoding every cell x phase in full, Fast-SSC cost), on fresh packets.

    BLIND_STUDY=small_cfo python small_cut_nn.py --rate 2/5 --train 150000 --test 100000
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

CK = {"1/10": 6, "2/5": 3, "1/2": 2}                   # checkpoint per rate (CK_FR: 1/2, 1/4, 3/16)
REG = {"1/10": (-5.5, -3.5), "2/5": (-0.5, 2.0), "1/2": (1.0, 3.0)}
TEST = {"1/10": (-5.0, -4.5, -4.0), "2/5": (0.5, 1.0), "1/2": (2.0,)}
EPS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6)
TAU = 0.9999
CK_S = {"1/10": (0.5,), "2/5": (0.25, 0.375, 0.5, 0.75), "1/2": (0.125, 0.25, 0.5)}
TAU_S = {"1/10": 1.0, "2/5": -1.0, "1/2": -1.0}


def _feats(rate, x, pm, snr):
    """Per packet: features (n, NFE), the true-cell rank in the NN order needs t; also the NN order and z (n, G)."""
    c = CK[rate]
    X = sr.ck_features(x, pm, c)
    lp = sr.ck_logp("blind", c, X)
    o = np.argsort(-lp, 1)
    sl = np.take_along_axis(lp, o, 1)
    cp = np.cumsum(np.exp(sl), 1)
    sizes = [np.log1p((cp < 1 - e).sum(1) + 1) for e in EPS]
    ent = -(np.exp(lp) * lp).sum(1)
    z = X[..., sr.NF] * 5
    zs = -np.sort(-z, 1)
    F = np.stack([np.full(len(x), snr / 10), x[:, 0, 9], sl[:, 0], sl[:, 0] - sl[:, 1], ent / 5, *sizes,
                  zs[:, 0] / 10, zs[:, 1] / 10, zs[:, 15] / 10], 1).astype(np.float32)
    return F, lp, z


def _gen(task):
    rate, lo, hi, n, seed = task
    rng = np.random.default_rng(seed)
    out = {k: [] for k in ("F", "rank", "zrank", "nb", "work_ok")}
    W = sr.cost_share(bf.fast_sc(bc.CODES[rate]).plan, np.array(sr.CK_FR))
    got = 0
    while got < n:
        snr = float(rng.uniform(lo, hi))
        b = _batch(50, rng, "blind", rate, snr)
        if b is None:
            continue
        x, pm, t = b
        F, lp, z = _feats(rate, x, pm, snr)
        idx = np.arange(len(t))
        rk = (lp > lp[idx, t][:, None]).sum(1)                       # rank of the true cell in the NN order
        nb = np.minimum.reduce([(lp > lp[idx, np.clip(t + d, 0, lp.shape[1] - 1)][:, None]).sum(1) for d in (-1, 0, 1)])
        # the z-test as in the receiver at its checkpoints (replay, cell level, every phase continues)
        zr = np.array([_zreplay(rate, pm[i, :, :, :, 0], int(t[i]), W) for i in range(len(t))])
        out["F"].append(F)
        out["rank"].append(rk)
        out["nb"].append(nb)
        out["zrank"].append(zr)
        got += len(t)
    return rate, {k: np.concatenate(v)[:n] for k, v in out.items() if v}


def _zreplay(rate, P, t, W):
    """(true cell lost, true cell and neighbours lost, work) of the receiver's z-test."""
    G, Q, _ = P.shape
    A = np.ones(G, bool)
    work, prev = 0.0, 0.0
    cks = {sr.CK_FR.index(c) for c in CK_S[rate]}
    for j in range(len(sr.CK_FR)):
        work += (W[j] - prev) * A.sum() * Q
        prev = W[j]
        if j == len(sr.CK_FR) - 1:
            break
        if j in cks:
            cell = P[:, :, j].min(1)
            s = cell[A]
            med = np.median(s)
            zz = np.full(G, -np.inf)
            zz[A] = (med - s) / (1.4826 * np.median(np.abs(s - med)) + 1e-6)
            keep = zz > TAU_S[rate]
            keep[np.argsort(-zz)[:16]] = True
            A &= keep
    return (not A[t], not A[max(t - 1, 0):t + 2].any(), work / (G * Q))


def collect(rate, n, workers, seed, snr=None):
    lo, hi = (snr, snr) if snr is not None else REG[rate]
    per = -(-n // workers)
    with mp.Pool(workers) as pool:
        parts = pool.map(_gen, [(rate, lo, hi, per, seed + i) for i in range(workers)])
    return {k: np.concatenate([p[1][k] for p in parts]) for k in parts[0][1]}


def train_mlp(F, y, tau, epochs=60, seed=0):
    import torch
    torch.manual_seed(seed)
    torch.set_num_threads(16)
    m = torch.nn.Sequential(torch.nn.Linear(F.shape[1], 32), torch.nn.ReLU(), torch.nn.Linear(32, 32),
                            torch.nn.ReLU(), torch.nn.Linear(32, 1))
    opt = torch.optim.Adam(m.parameters(), lr=3e-3)
    Ft, yt = torch.from_numpy(F), torch.from_numpy(np.log1p(y).astype(np.float32))
    for ep in range(epochs):
        perm = torch.randperm(len(Ft))
        for b in range(0, len(Ft), 1024):
            i = perm[b:b + 1024]
            e = yt[i] - m(Ft[i])[:, 0]
            loss = torch.maximum(tau * e, (tau - 1) * e).mean()      # pinball: the tau-quantile of log(1 + rank)
            opt.zero_grad()
            loss.backward()
            opt.step()
    m.eval()
    return lambda X: np.expm1(m(torch.from_numpy(X)).detach().numpy()[:, 0])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", required=True)
    ap.add_argument("--train", type=int, default=150000)
    ap.add_argument("--test", type=int, default=100000)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=81)
    a = ap.parse_args()
    t0 = time.time()
    rate = a.rate
    G = len(bf.grid(bf.grid_step(rate, REG[rate][0]))["f"])
    Q = 4 if REG[rate][0] < -1 else 2
    W = sr.cost_share(bf.fast_sc(bc.CODES[rate]).plan, np.array(sr.CK_FR))
    wc = W[CK[rate]]
    tr = collect(rate, a.train, a.workers, a.seed)
    print(f"{rate}: {len(tr['rank'])} training packets ({time.time() - t0:.0f}s)", flush=True)
    out = []
    models = {tau: train_mlp(tr["F"], tr["rank"], tau) for tau in (0.999, 0.9999)}
    print(f"trained ({time.time() - t0:.0f}s)", flush=True)
    for s in TEST[rate]:
        te = collect(rate, a.test, a.workers, a.seed + 1000 + int(10 * s), snr=s)
        n = len(te["rank"])
        zl, znb, zw = te["zrank"][:, 0].mean(), te["zrank"][:, 1].mean(), te["zrank"][:, 2].mean()
        print(f"\n== {rate} {s:+.1f} dB, {n} search packets; checkpoint {sr.CK_FR[CK[rate]]:g} (Fast-SSC cost "
              f"{wc:.3f} of a pass)\n  z-test (receiver): lost {zl:.1e}, cell+nb {znb:.1e}, work {zw:.3f}", flush=True)
        row = {"rate": rate, "snr": s, "packets": n, "z": [float(zl), float(znb), float(zw)]}
        # work after the checkpoint: only the kept cells (every phase) continue to the end (an upper bound: the
        # receiver's later checkpoints prune further)
        for e_i, e in enumerate(EPS):
            k = np.maximum(8, np.ceil(np.expm1(te["F"][:, 5 + e_i])))
            lost, lnb = (te["rank"] >= k).mean(), (te["nb"] >= k).mean()
            w = wc + (1 - wc) * (k / G).mean()
            print(f"  NN shortlist 1-{e:g}: {k.mean():6.1f} cells, lost {lost:.1e}, cell+nb {lnb:.1e}, work <= {w:.3f}")
            row[f"short {e:g}"] = [float(k.mean()), float(lost), float(lnb), float(w)]
        for tau, f in models.items():
            for mg in (1.0, 1.5, 2.0, 3.0):
                k = np.clip(np.ceil(mg * (f(te["F"]) + 1)), 8, G)
                lost, lnb = (te["rank"] >= k).mean(), (te["nb"] >= k).mean()
                w = wc + (1 - wc) * (k / G).mean()
                print(f"  cut NN q{tau:g} x{mg:g}: {k.mean():6.1f} cells, lost {lost:.1e}, cell+nb {lnb:.1e}, "
                      f"work <= {w:.3f}")
                row[f"cut {tau:g} x{mg:g}"] = [float(k.mean()), float(lost), float(lnb), float(w)]
        out.append(row)
        json.dump(out, open(bc.path("results", f"cut_nn_{rate.replace('/', '_')}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)
