"""
A small per-cell NN that re-scores the search's posterior (blind_fast.sps3_receive, rank_nn).

The search decodes the CFO cells best-first in the order of a hand-weighted posterior,
    Student-t prior around the 2-SPS spectral estimate + w4(snr) S4 + 2 C / std(C) [+ pilot log-likelihood],
so the MACs of a searched packet grow with the rank of the true cell. The network sees, per cell:
    the analytic posterior (relative to its max), the prior term, |distance to the estimate| / sigma, S4, C / std(C),
    the pilot log-likelihood (relative to its max; 0 blind), SNR, grid step
and adds a shared MLP (NF -> H -> 1) to the analytic posterior (skip connection, so training starts from it).
Loss: softmax over all cells of the grid, cross-entropy on the cell nearest to the true CFO.
One model per mode (blind / 24 pilots N3x8) covering the receivers' grids: step 4 (R = 1/10 below -3 dB), step 6
(R = 1/10 from -3 dB), step 2 (R = 2/5, 1/2).  ~G (NF H + 2 H) MACs per searched packet (macs(G)).

    python blind_rank_nn.py train --mode blind      # -> blind/models/rank_nn_blind.npz
    python blind_rank_nn.py eval --mode blind       # rank of the true cell: NN vs the analytic posterior
"""
import argparse
import json
import multiprocessing as mp
import os
import time

import numpy as np

import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp

NF = 8                                            # features per cell
H = 16                                            # hidden width
POS = np.array(vp.PATTERNS["N3x8"])
REGIMES = ((4, -6.0, -3.0), (6, -3.5, 0.5), (2, -0.5, 3.5))   # (grid step, SNR range) the receivers use
KS = (1, 4, 16, 64, 128, 256, 512)


def macs(G):
    return G * (NF * H + 2 * H + 2)


def features(post, S4, fs, C, pl, snr, k):
    """Per-cell features (B, G, NF) from the receiver's posterior parts."""
    g = bf.grid(k)["f"]
    d = (g[None] - fs[:, None]) / bf.spec_sigma(snr)
    x = np.empty(post.shape + (NF,), np.float32)
    x[..., 0] = np.clip(post - post.max(1, keepdims=True), -50, 0) / 10
    x[..., 1] = -2.0 * np.log1p(d ** 2 / 3) / 10
    x[..., 2] = np.clip(np.abs(d), 0, 10) / 10
    x[..., 3] = np.clip(S4, 0, 50) / 10
    x[..., 4] = C / np.std(C, axis=1, keepdims=True) / 3
    x[..., 5] = 0.0 if pl is None else np.clip(pl - pl.max(1, keepdims=True), -50, 0) / 10
    x[..., 6] = snr / 10.0
    x[..., 7] = k / 6.0
    return x


_W = {}


def load(mode):
    if mode not in _W:
        z = np.load(bc.path("models", f"rank_nn_{mode}.npz"))
        _W[mode] = {k: z[k] for k in z.files}
    return _W[mode]


def score(mode, x):
    """New posterior (B, G): w0 x0 + MLP(x) (in units of the analytic posterior / 10)."""
    W = load(mode)
    h = np.maximum(x @ W["w1"] + W["b1"], 0)
    return (h @ W["w2"])[..., 0] + W["b2"][0] + W["w0"][0] * x[..., 0]


# ------------------------------------------------------------------ data: the receiver's own search statistics
def _batch(B, rng, mode, k, snr):
    from polar import PolarCode
    code = PolarCode(bc.N_BITS, 205, 16, 8)
    _, cw, r, rx, f, _ = bc.frames(B, code, snr, rng)
    g = bf.grid(k)["f"]
    _, fs, C = vp.features_lite(r, rx, k)
    r2 = bf.premf(r, rx, fs)
    S4 = vp.s4_grid(r2, k)
    post = bf.posterior2(S4, fs, C, snr, k)
    pl = None
    if mode == "pilots":
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        pl = vp.pilot_loglik(vp.pilot_A(r2[:, POS] * np.conj(sym[:, POS]), POS, g), snr)
        post = post + pl
    t = np.abs(g[None] - f[:, None]).argmin(1)
    return features(post, S4, fs, C, pl, snr, k), t


def _producer(seed, q, B, mode):
    rng = np.random.default_rng(seed)
    while True:
        k, lo, hi = REGIMES[rng.integers(len(REGIMES))]
        q.put(_batch(B, rng, mode, k, float(rng.uniform(lo, hi))))


def _ranks(s, t):
    return (s > s[np.arange(len(t)), t][:, None]).sum(1)


VAL = ((4, -5.0), (4, -4.0), (6, -3.0), (6, -2.0), (6, -1.0), (2, 0.5), (2, 1.0), (2, 2.0))


def train(a):
    import torch
    import torch.nn as nn
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)

    class RankNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.mlp = nn.Sequential(nn.Linear(NF, H), nn.ReLU(), nn.Linear(H, 1))
            self.w0 = nn.Parameter(torch.tensor([10.0]))       # x0 = post / 10: start from the analytic order
            nn.init.zeros_(self.mlp[2].weight)

        def forward(self, x):
            return self.mlp(x)[..., 0] + self.w0 * x[..., 0]

    model = RankNet()
    print(f"RankNet ({a.mode}) params {sum(p.numel() for p in model.parameters())}, "
          f"{macs(1)} MACs a cell (~{macs(1334) / 1e3:.0f}k at 1334 cells)", flush=True)
    vrng = np.random.default_rng(a.seed + 1)
    val = {(k, s): _batch(a.val, vrng, a.mode, k, s) for k, s in VAL}
    for (k, s), (x, t) in val.items():
        rk = _ranks(x[..., 0], t)
        print(f"analytic  step {k} {s:+.1f} dB: mean rank {rk.mean():7.1f}  "
              + " ".join(f">={K} {np.mean(rk >= K):.4f}" for K in KS), flush=True)
    q = mp.Queue(maxsize=64)
    procs = [mp.Process(target=_producer, daemon=True, args=(a.seed + 1000 * (i + 1), q, a.batch, a.mode))
             for i in range(a.producers)]
    for p in procs:
        p.start()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr * 1e-2)
    best, hist = np.inf, []
    for ep in range(1, a.epochs + 1):
        model.train()
        t0, tot = time.time(), 0.0
        for _ in range(a.steps):
            x, t = q.get()
            loss = nn.functional.cross_entropy(model(torch.from_numpy(x)), torch.from_numpy(t).long())
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item()
        model.eval()
        res = {}
        with torch.no_grad():
            for (k, s), (x, t) in val.items():
                rk = _ranks(model(torch.from_numpy(x)).numpy(), t)
                res[f"{k} {s:+.1f}"] = float(rk.mean())
        sc = float(np.mean([np.log1p(v) for v in res.values()]))
        mark = ""
        if sc < best:
            best = sc
            sd = model.state_dict()
            np.savez(bc.path("models", f"rank_nn_{a.mode}.npz"),
                     w1=sd["mlp.0.weight"].numpy().T, b1=sd["mlp.0.bias"].numpy(),
                     w2=sd["mlp.2.weight"].numpy().T, b2=sd["mlp.2.bias"].numpy(), w0=sd["w0"].numpy())
            mark = " [BEST]"
        hist.append({"epoch": ep, "loss": tot / a.steps, "mean_rank": res})
        print(f"Epoch {ep:3d}/{a.epochs} | CE {tot / a.steps:.4f} | mean rank "
              + " ".join(f"[{k}] {v:.1f}" for k, v in res.items()) + f" | {time.time() - t0:.0f}s{mark}", flush=True)
    json.dump(hist, open(bc.path("logs", f"rank_nn_{a.mode}_train.json"), "w"), indent=1)
    for p in procs:
        p.terminate()
    print("TRAIN DONE", flush=True)


def evaluate(a):
    """Rank of the true cell per (grid step, SNR): analytic posterior vs the NN, on fresh packets."""
    rng = np.random.default_rng(a.seed + 7)
    out = []
    for k, s in VAL:
        x, t = _batch(a.frames, rng, a.mode, k, s)
        ra, rn = _ranks(x[..., 0], t), _ranks(score(a.mode, x), t)
        out.append({"step": k, "snr": s, "analytic": {"mean": float(ra.mean()), **{str(K): float(np.mean(ra >= K))
                                                                                     for K in KS}},
                    "nn": {"mean": float(rn.mean()), **{str(K): float(np.mean(rn >= K)) for K in KS}}})
        for lab, rk in (("analytic", ra), ("NN", rn)):
            print(f"{lab:8s} step {k} {s:+.1f} dB: mean rank {rk.mean():7.1f}  "
                  + " ".join(f">={K} {np.mean(rk >= K):.4f}" for K in KS), flush=True)
    json.dump(out, open(bc.path("results", f"rank_nn_{a.mode}_eval.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["train", "eval"])
    ap.add_argument("--mode", choices=["blind", "pilots"], default="blind")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=150)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--val", type=int, default=1000)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--producers", type=int, default=7)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--frames", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=21)
    a = ap.parse_args()
    {"train": train, "eval": evaluate}[a.action](a)
