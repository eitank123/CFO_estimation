"""
Checkpoint NN for the small-CFO search (small_rx.py, BLIND_STUDY=small_cfo): at a checkpoint along the list-1
Fast-SSC decode of every cell, P(cell holds the CFO) from what the search has already paid for, to replace the
median/MAD z-test there (which cells continue, in which order the candidates are decoded).

Per cell (small_rx.ck_features): the cell-prior features (4th power, lag-4 ACF, pilots' log-likelihood, SNR, grid
step), the robust z of the partial path metric at 1/16, 1/8, ... up to the checkpoint (best phase), the same for the
rate-0 (frozen) nodes alone, the phase contrast. Net as small_prior_nn (conv(3) -> FiLM(SNR) -> ReLU -> conv(3) ->
FiLM(SNR) -> ReLU -> 1x1 across the cells: it sees the neighbouring cells, i.e. the shape of the metric's basin) +
(w0 + w1 SNR) x the z-test (skip, so training starts from the z-test order). One model per checkpoint (CKS), all
trained on the same packets (those the fast path fails, small_receive with spec "dump_pm").

    BLIND_STUDY=small_cfo python small_ck_nn.py train --mode blind    # -> small_cfo/blind/models/ck_nn_blind_c*.npz
    BLIND_STUDY=small_cfo python small_ck_nn.py eval --mode blind     # z-test vs NN: true-cell rank, shortlists
"""
import argparse
import json
import multiprocessing as mp
import time

import numpy as np

import blind_cfo as bc
import small_rx as sr
from small_prior_nn import _ranks

REGIMES = (("1/10", -5.5, -3.5), ("2/5", -0.5, 2.0), ("1/2", 1.0, 3.0))
VAL = (("1/10", -5.0), ("1/10", -4.5), ("1/10", -4.0), ("2/5", 0.5), ("2/5", 1.0), ("1/2", 2.0))
CKS = (1, 2, 3, 4, 5, 6)                # checkpoints CK_FR[c]: 1/8, 3/16, 1/4, 5/16, 3/8, 1/2
KS = (1, 4, 16, 32, 64, 128)
QS = (0.99, 0.999)


def _batch(B, rng, mode, rate, snr):
    """Cell-prior features (n, G, NF), partial metrics (n, G, phases, len(CK_FR), 2), true cells (n,), snr."""
    from blind_ber import RHO_N
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    _, cw, r, rx, f, _ = bc.frames(B, code, snr, rng)
    sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    d = {}
    spec = {"sps": {"rate": rate, "rho_n": RHO_N, "pilots": "N3x8" if mode == "pilots" else None,
                    "premf_dec": True, "ca_retry": True, "dump_pm": d}}
    st = {"decodes": 0, "metric_evals": 0}
    sr.small_receive(r, rx, snr, code, sigma2, st, spec, sym if mode == "pilots" else None)
    if "x" not in d:
        return None
    t = np.abs(d["g"][None] - f[d["rem"], None]).argmin(1)
    return d["x"], d["pm"], t


def _producer(seed, q, B, mode):
    rng = np.random.default_rng(seed)
    while True:
        rate, lo, hi = REGIMES[rng.integers(len(REGIMES))]
        b = _batch(B, rng, mode, rate, float(rng.uniform(lo, hi)))
        if b is not None:
            q.put(b)


def _collect(n, rng, mode, rate, snr):
    xs, ps, ts = [], [], []
    while sum(len(t) for t in ts) < n:
        b = _batch(50, rng, mode, rate, snr)
        if b is not None:
            xs.append(b[0])
            ps.append(b[1])
            ts.append(b[2])
    return np.concatenate(xs)[:n], np.concatenate(ps)[:n], np.concatenate(ts)[:n]


def save(model, path):
    sd = {k: v.numpy() for k, v in model.state_dict().items()}
    np.savez(path, c1=sd["c1.weight"].transpose(2, 1, 0), b1=sd["c1.bias"],
             c2=sd["c2.weight"].transpose(2, 1, 0), b2=sd["c2.bias"],
             c3=sd["c3.weight"][:, :, 0].T, b3=sd["c3.bias"], w0=sd["w0"], w1=sd["w1"],
             a1=sd["a1"][:, 0], f1=sd["f1"][:, 0], a2=sd["a2"][:, 0], f2=sd["f2"][:, 0])


def train(a):
    import torch
    import torch.nn as nn
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)
    SK = sr.NF                                               # index of the z-test feature (skip input)

    class CkNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.c1 = nn.Conv1d(sr.NF_CK, sr.NH, sr.KS, padding=sr.KS // 2)
            self.c2 = nn.Conv1d(sr.NH, sr.NH, sr.KS, padding=sr.KS // 2)
            self.c3 = nn.Conv1d(sr.NH, 1, 1)
            self.w0 = nn.Parameter(torch.tensor([5.0]))      # z-test (feature z / 5) as the starting order
            self.w1 = nn.Parameter(torch.zeros(1))
            self.a1, self.f1, self.a2, self.f2 = (nn.Parameter(torch.zeros(sr.NH, 1)) for _ in range(4))
            nn.init.zeros_(self.c3.weight)

        def forward(self, x):
            s = x[:, :1, 8:9].transpose(1, 2)
            h = torch.relu(self.c1(x.transpose(1, 2)) * (1 + self.a1 * s) + self.f1 * s)
            h = torch.relu(self.c2(h) * (1 + self.a2 * s) + self.f2 * s)
            return self.c3(h)[:, 0] + (self.w0 + self.w1 * s[:, 0]) * x[..., SK]

    models = {c: CkNet() for c in CKS}
    print(f"CkNet ({a.mode}) params {sum(p.numel() for p in models[CKS[0]].parameters())}, "
          f"{sr.ck_macs(201) / 1e3:.0f}k MACs at 201 cells, {sr.ck_macs(401) / 1e3:.0f}k at 401", flush=True)
    vrng = np.random.default_rng(a.seed + 1)
    val = {v: _collect(a.val, vrng, a.mode, *v) for v in VAL}
    for (rate, s), (x, pm, t) in val.items():
        print(f"z-test {rate} {s:+.1f}: mean rank " + " ".join(
            f"[{sr.CK_FR[c]:.4g}] {_ranks(sr.ck_features(x, pm, c)[..., SK], t).mean():.1f}"
            for c in CKS + (len(sr.CK_FR) - 1,)), flush=True)
    q = mp.Queue(maxsize=64)
    procs = [mp.Process(target=_producer, daemon=True, args=(a.seed + 1000 * (i + 1), q, a.batch, a.mode))
             for i in range(a.producers)]
    for p in procs:
        p.start()
    opts = {c: torch.optim.AdamW(models[c].parameters(), lr=a.lr, weight_decay=1e-5) for c in CKS}
    scheds = {c: torch.optim.lr_scheduler.CosineAnnealingLR(opts[c], T_max=a.epochs * a.steps, eta_min=a.lr * 1e-2)
              for c in CKS}
    best = {c: np.inf for c in CKS}
    hist = []
    for ep in range(1, a.epochs + 1):
        t0, tot = time.time(), {c: 0.0 for c in CKS}
        for m in models.values():
            m.train()
        for _ in range(a.steps):
            x, pm, t = q.get()
            tt = torch.from_numpy(t).long()
            for c in CKS:
                loss = nn.functional.cross_entropy(models[c](torch.from_numpy(sr.ck_features(x, pm, c))), tt)
                opts[c].zero_grad(set_to_none=True)
                loss.backward()
                opts[c].step()
                scheds[c].step()
                tot[c] += loss.item()
        row = {"epoch": ep}
        line = f"Epoch {ep:3d}/{a.epochs}"
        for c in CKS:
            models[c].eval()
            res = {}
            with torch.no_grad():
                for (rate, s), (x, pm, t) in val.items():
                    lg = models[c](torch.from_numpy(sr.ck_features(x, pm, c))).numpy()
                    res[f"{rate} {s:+.1f}"] = float(_ranks(lg, t).mean())
            sc = float(np.mean([np.log1p(v) for v in res.values()]))
            mark = ""
            if sc < best[c]:
                best[c] = sc
                save(models[c], bc.path("models", f"ck_nn_{a.mode}_c{c}.npz"))
                mark = "*"
            row[str(c)] = {"loss": tot[c] / a.steps, "mean_rank": res}
            line += f" | c{c} CE {tot[c] / a.steps:.3f} " + " ".join(f"{v:.1f}" for v in res.values()) + mark
        hist.append(row)
        print(line + f" | {time.time() - t0:.0f}s", flush=True)
    json.dump(hist, open(bc.path("logs", f"ck_nn_{a.mode}_train.json"), "w"), indent=1)
    for p in procs:
        p.terminate()
    print("TRAIN DONE", flush=True)


def _short(lp, t, eps, nmin):
    o = np.argsort(-lp, 1)
    cp = np.cumsum(np.exp(np.take_along_axis(lp, o, 1)), 1)
    n = np.maximum(nmin, (cp < 1 - eps).sum(1) + 1)
    return n, _ranks(lp, t) < n


def evaluate(a):
    """Fresh search packets per VAL point: rank of the true cell by the z-test vs the NN at each checkpoint (mean,
    tail fractions, 99 / 99.9 % quantiles = the top-K that holds the true cell), and the NN's adaptive shortlist
    (cumulative probability 1 - eps, >= nmin cells). Work estimate: the checkpoint's fraction for every cell + the
    rest of the codeword for the shortlist (fraction of a full decode of the whole grid)."""
    rng = np.random.default_rng(a.seed + 7)
    out = []
    for rate, s in VAL:
        x, pm, t = _collect(a.frames, rng, a.mode, rate, s)
        G = x.shape[1]
        row = {"rate": rate, "snr": s, "cells": G, "packets": len(t)}
        zf = _ranks(sr.ck_features(x, pm, len(sr.CK_FR) - 1)[..., sr.NF], t)
        print(f"{rate} {s:+.1f} ({len(t)} packets, {G} cells): full-decode metric rank mean {zf.mean():.1f}, "
              f"q99 {np.quantile(zf, 0.99):.0f}, q99.9 {np.quantile(zf, 0.999):.0f}", flush=True)
        row["full"] = {"mean": float(zf.mean()), **{str(qq): float(np.quantile(zf, qq)) for qq in QS}}
        for c in CKS:
            X = sr.ck_features(x, pm, c)
            lp = sr.ck_logp(a.mode, c, X)
            fr = sr.CK_FR[c]
            for nm, sc in (("z", X[..., sr.NF]), ("nn", lp)):
                rk = _ranks(sc, t)
                row[f"{nm} c{c}"] = {"mean": float(rk.mean()), **{str(K): float(np.mean(rk >= K)) for K in KS},
                                     **{str(qq): float(np.quantile(rk, qq)) for qq in QS}}
                print(f"  ck {fr:.4g} {nm:2s}: mean rank {rk.mean():6.1f}  q99 {np.quantile(rk, .99):5.0f}  "
                      f"q99.9 {np.quantile(rk, .999):5.0f}  " + " ".join(f">={K} {np.mean(rk >= K):.4f}" for K in KS),
                      flush=True)
            for eps in (1e-2, 1e-3, 1e-4):
                for nmin in (8, 16):
                    n, hit = _short(lp, t, eps, nmin)
                    w = fr + (1 - fr) * n.mean() / G
                    row[f"short c{c} {eps:g} {nmin}"] = {"size": float(n.mean()), "miss": float(1 - hit.mean()),
                                                         "work": float(w)}
                    print(f"    NN shortlist 1-{eps:g}, >= {nmin}: {n.mean():6.1f} cells, missed {1 - hit.mean():.4f}, "
                          f"work {w:.3f} of the full grid", flush=True)
        out.append(row)
        json.dump(out, open(bc.path("results", f"ck_nn_{a.mode}_eval.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["train", "eval"])
    ap.add_argument("--mode", choices=["blind", "pilots"], default="blind")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--val", type=int, default=800)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--producers", type=int, default=15)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--frames", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=41)
    a = ap.parse_args()
    {"train": train, "eval": evaluate}[a.action](a)
