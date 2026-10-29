"""
SNR-aware cell-prior NN for the small-CFO search (small_rx.py, BLIND_STUDY=small_cfo): P(cell holds the CFO) for the
packets the 4th-power fast path does not deliver, to order the search best-first instead of the spectral prior of the
+-0.2 receivers (no spectral / cyclic statistics here).

Per cell (small_rx.nn_features): 4th-power periodogram of the packet and of each half, the halves' phase agreement at
the cell, the periodogram's peak-to-mean, distance to the fast-path estimate, the pre-MF lag-4 autocorrelation
estimate, the pilots' log-likelihood (pilots mode), SNR, grid step. Net: conv(3) -> ReLU -> conv(3) -> ReLU -> 1x1
across the cells (it sees the neighbouring cells, i.e. the peak's shape) + w0 x periodogram (skip, so training starts
from the periodogram order). Loss: softmax over the grid, cross-entropy on the cell nearest to the true CFO.
Training packets = those the receiver's own fast path fails (small_receive with spec "dump").

    BLIND_STUDY=small_cfo python small_prior_nn.py train --mode blind     # -> small_cfo/blind/models/prior_nn_blind.npz
    BLIND_STUDY=small_cfo python small_prior_nn.py eval --mode blind      # true-cell rank and shortlist sizes
"""
import argparse
import json
import multiprocessing as mp
import os
import time

import numpy as np

import blind_cfo as bc
import small_rx as sr

REGIMES = (("1/10", -6.5, -3.5), ("2/5", -0.5, 2.0), ("1/2", 1.0, 3.0))   # (rate, SNR range) of the search
VAL = (("1/10", -6.0), ("1/10", -5.0), ("1/10", -4.0), ("2/5", 0.5), ("2/5", 1.0), ("1/2", 2.0))
KS = (1, 4, 16, 32, 64, 128)
EPS = (1e-2, 1e-3, 1e-4)


def _batch(B, rng, mode, rate, snr):
    """Features (n, G, NF) and true cells (n,) of the packets of a batch that reach the search."""
    from blind_ber import RHO_N
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    _, cw, r, rx, f, _ = bc.frames(B, code, snr, rng)
    sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    d = {}
    spec = {"sps": {"rate": rate, "rho_n": RHO_N, "pilots": "N3x8" if mode == "pilots" else None,
                    "premf_dec": True, "ca_retry": True, "dump": d}}
    st = {"decodes": 0, "metric_evals": 0}
    sr.small_receive(r, rx, snr, code, sigma2, st, spec, sym if mode == "pilots" else None)
    if "x" not in d:
        return None
    t = np.abs(d["g"][None] - f[d["rem"], None]).argmin(1)
    return d["x"], t


def _producer(seed, q, B, mode):
    rng = np.random.default_rng(seed)
    while True:
        rate, lo, hi = REGIMES[rng.integers(len(REGIMES))]
        b = _batch(B, rng, mode, rate, float(rng.uniform(lo, hi)))
        if b is not None:
            q.put(b)


def _val(n, rng, mode, rate, snr):
    xs, ts = [], []
    while sum(len(t) for t in ts) < n:
        b = _batch(100, rng, mode, rate, snr)
        if b is not None:
            xs.append(b[0])
            ts.append(b[1])
    return np.concatenate(xs)[:n], np.concatenate(ts)[:n]


def _ranks(s, t):
    return (s > s[np.arange(len(t)), t][:, None]).sum(1)


def _short(lp, t, eps, nmin):
    """Shortlist size (cumulative probability 1 - eps, >= nmin cells) and whether the true cell is in it."""
    o = np.argsort(-lp, 1)
    cp = np.cumsum(np.exp(np.take_along_axis(lp, o, 1)), 1)
    n = np.maximum(nmin, (cp < 1 - eps).sum(1) + 1)
    return n, _ranks(lp, t) < n


def _report(lab, s, t, G, f=None):
    rk = _ranks(s, t)
    line = (f"{lab:9s}: mean rank {rk.mean():6.1f} of {G}  "
            + " ".join(f">={K} {np.mean(rk >= K):.4f}" for K in KS))
    print(line, flush=True)
    return {"mean": float(rk.mean()), **{str(K): float(np.mean(rk >= K)) for K in KS}}


def train(a):
    import torch
    import torch.nn as nn
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)

    class PriorNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.c1 = nn.Conv1d(sr.NF, sr.NH, sr.KS, padding=sr.KS // 2)
            self.c2 = nn.Conv1d(sr.NH, sr.NH, sr.KS, padding=sr.KS // 2)
            self.c3 = nn.Conv1d(sr.NH, 1, 1)
            self.w0 = nn.Parameter(torch.tensor([5.0]))
            self.w1 = nn.Parameter(torch.zeros(1))            # SNR-dependent weight of the periodogram skip
            self.a1, self.f1, self.a2, self.f2 = (nn.Parameter(torch.zeros(sr.NH, 1)) for _ in range(4))   # FiLM(SNR)
            nn.init.zeros_(self.c3.weight)

        def forward(self, x):                                # x (B, G, NF)
            s = x[:, :1, 8:9].transpose(1, 2)                # SNR / 10 (B, 1, 1)
            h = torch.relu(self.c1(x.transpose(1, 2)) * (1 + self.a1 * s) + self.f1 * s)
            h = torch.relu(self.c2(h) * (1 + self.a2 * s) + self.f2 * s)
            return self.c3(h)[:, 0] + (self.w0 + self.w1 * s[:, 0]) * x[..., 0]

    model = PriorNet()
    print(f"PriorNet ({a.mode}) params {sum(p.numel() for p in model.parameters())}, "
          f"{sr.nn_macs(201) / 1e3:.0f}k MACs at 201 cells, {sr.nn_macs(401) / 1e3:.0f}k at 401", flush=True)
    vrng = np.random.default_rng(a.seed + 1)
    val = {v: _val(a.val, vrng, a.mode, *v) for v in VAL}
    for (rate, s), (x, t) in val.items():
        _report(f"S4 {rate} {s:+.1f}", x[..., 0], t, x.shape[1])
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
            for (rate, s), (x, t) in val.items():
                res[f"{rate} {s:+.1f}"] = float(_ranks(model(torch.from_numpy(x)).numpy(), t).mean())
        sc = float(np.mean([np.log1p(v) for v in res.values()]))
        mark = ""
        if sc < best:
            best = sc
            sd = {k: v.numpy() for k, v in model.state_dict().items()}
            np.savez(bc.path("models", f"prior_nn_{a.mode}.npz"),
                     c1=sd["c1.weight"].transpose(2, 1, 0), b1=sd["c1.bias"],
                     c2=sd["c2.weight"].transpose(2, 1, 0), b2=sd["c2.bias"],
                     c3=sd["c3.weight"][:, :, 0].T, b3=sd["c3.bias"], w0=sd["w0"], w1=sd["w1"],
                     a1=sd["a1"][:, 0], f1=sd["f1"][:, 0], a2=sd["a2"][:, 0], f2=sd["f2"][:, 0])
            mark = " [BEST]"
        hist.append({"epoch": ep, "loss": tot / a.steps, "mean_rank": res})
        print(f"Epoch {ep:3d}/{a.epochs} | CE {tot / a.steps:.4f} | mean rank "
              + " ".join(f"[{k}] {v:.1f}" for k, v in res.items()) + f" | {time.time() - t0:.0f}s{mark}", flush=True)
    json.dump(hist, open(bc.path("logs", f"prior_nn_{a.mode}_train.json"), "w"), indent=1)
    for p in procs:
        p.terminate()
    print("TRAIN DONE", flush=True)


def evaluate(a):
    """On fresh search packets: rank of the true cell by the periodogram alone vs the NN (numpy forward, as in the
    receiver), and the NN shortlist (cumulative probability 1 - eps, >= nmin cells): mean size vs the grid, misses."""
    rng = np.random.default_rng(a.seed + 7)
    out = []
    for rate, s in VAL:
        x, t = _val(a.frames, rng, a.mode, rate, s)
        G = x.shape[1]
        lp = sr.nn_logp(a.mode, x)
        row = {"rate": rate, "snr": s, "cells": G, "packets": len(t),
               "s4": _report(f"S4 {rate} {s:+.1f}", x[..., 0], t, G), "nn": _report(f"NN {rate} {s:+.1f}", lp, t, G)}
        for eps in EPS:
            for nmin in (16, 48):
                n, hit = _short(lp, t, eps, nmin)
                row[f"short {eps:g} {nmin}"] = {"size": float(n.mean()), "miss": float(1 - hit.mean())}
                print(f"    shortlist 1-{eps:g}, >= {nmin}: mean {n.mean():6.1f} cells ({n.mean() / G:.3f} of the grid), "
                      f"true cell missed {1 - hit.mean():.4f}", flush=True)
        out.append(row)
    json.dump(out, open(bc.path("results", f"prior_nn_{a.mode}_eval.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["train", "eval"])
    ap.add_argument("--mode", choices=["blind", "pilots"], default="blind")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--steps", type=int, default=150)
    ap.add_argument("--batch", type=int, default=100)
    ap.add_argument("--val", type=int, default=2000)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--producers", type=int, default=14)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--frames", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=31)
    a = ap.parse_args()
    {"train": train, "eval": evaluate}[a.action](a)
