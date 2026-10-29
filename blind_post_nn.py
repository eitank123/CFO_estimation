"""
Blind CFO, idea 2: a neural network that fuses every blind statistic into a posterior over CFO cells (no pilots).

Input (4 channels over a coarse grid of 334 cells, 16 STEP = 1.2e-3 each, covering +-0.2), from the MAC-light (2-SPS)
features of blind_vp.features_lite:
    PSD-template correlation curve, band-edge cyclic curve, 4th-power periodogram (max-pooled per cell), SNR
Network: dilated 1-D convolutions (zero padding: the range has edges), 8 channels; output one logit per coarse cell,
cross-entropy on the cell of the true CFO. It replaces the hand-made posterior (Student-t prior + weighted terms): it
can learn the heavy tails of the spectral estimate and how the three statistics interact. The fine cells inside a
coarse cell are ordered by the analytic posterior. ~0.9 M MACs per packet (MACS).

    python blind_post_nn.py train --epochs 40      # -> blind/models/post_nn.pth
    python blind_post_nn.py ranks --part a         # E5: rank of the true cell, NN vs analytic posterior
"""
import argparse
import json
import multiprocessing as mp
import os
import time

import numpy as np
import torch
import torch.nn as nn

import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp

CSTEP = 16                                         # coarse cell = 16 STEP
GC = np.arange(-bc.MAX_CFO, bc.MAX_CFO + CSTEP * bc.STEP / 2, CSTEP * bc.STEP)
NC_ = len(GC)
MODEL = "post_nn.pth"
CH, LAYERS, KS = 8, 4, 9
MACS = (4 * CH * KS + LAYERS * CH * CH * KS + CH) * NC_


class PostNet(nn.Module):
    def __init__(self, ch=CH, layers=LAYERS, k=KS):
        super().__init__()
        mods, c = [], 4
        for d in [1] + [2 ** (i + 1) for i in range(layers)]:
            mods += [nn.Conv1d(c, ch, k, padding=d * (k // 2), dilation=d), nn.GELU()]
            c = ch
        mods.append(nn.Conv1d(ch, 1, 1))
        self.net = nn.Sequential(*mods)

    def forward(self, x):
        return self.net(x)[:, 0]


def coarse_inputs(r, rx, snr):
    """(B, 4, NC_) network input, and the lite fine-grid features (S4, fs, C on grid(4)) for the tie-break."""
    S4, fs, C, Cp, Cc, Y = vp.features_lite(r, rx, 4, curves=True)
    sps_l = bc.SPS / vp.DEC
    kb = np.round(GC / sps_l * vp.NFFT_L).astype(int) % vp.NFFT_L
    w = CSTEP // 2                                 # PSD / cyclic bins per half coarse cell (bin = 1/2048 = 0.65 STEP)
    idx = (kb[:, None] + np.arange(-w, w + 1)[None]) % vp.NFFT_L
    cp = Cp[:, idx].max(2)
    cc = Cc[:, idx].max(2)
    nu = (4 * GC) % 1.0
    span = int(np.ceil(4 * CSTEP * bc.STEP * bc.NFFT4)) + 1
    b0 = np.floor((nu - 2 * CSTEP * bc.STEP) * bc.NFFT4).astype(int)
    s4 = Y[:, (b0[:, None] + np.arange(span)[None]) % bc.NFFT4].max(2)
    norm = lambda a: (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-9)
    x = np.stack([norm(cp), norm(cc), norm(np.log(s4)), np.full(cp.shape, (snr - 0.0) / 5.0)], 1).astype(np.float32)
    return x, (S4, fs, C)


_model = None


def load():
    global _model
    if _model is None:
        ck = torch.load(bc.path("models", MODEL), map_location="cpu", weights_only=False)
        _model = PostNet(**ck["config"])
        _model.load_state_dict(ck["state_dict"])
        _model.eval()
    return _model


def posterior(r, rx, snr, k):
    """Score (B, G) on grid(k): NN log-posterior of the coarse cell + 0.1 x the analytic posterior (tie-break)."""
    x, (S4, fs, C) = coarse_inputs(r, rx, snr)
    torch.set_num_threads(1)
    with torch.no_grad():
        lg = torch.log_softmax(load()(torch.from_numpy(x)), 1).numpy()
    g = bf.grid(k)["f"]
    cidx = np.clip(np.round((g + bc.MAX_CFO) / (CSTEP * bc.STEP)).astype(int), 0, NC_ - 1)
    if k == 4:
        S4k, Ck = S4, C
    else:
        S4k, fs2, Ck = vp.features_lite(r, rx, k)
    return lg[:, cidx] + 0.1 * bf.posterior2(S4k, fs, Ck, snr, k), fs


def _batch(B, rng, lo=-6.0, hi=4.0):
    from polar import PolarCode
    code = PolarCode(bc.N_BITS, 205, 16, 8)
    snr = float(rng.uniform(lo, hi))
    _, _, r, rx, f, _ = bc.frames(B, code, snr, rng)
    x, _ = coarse_inputs(r, rx, snr)
    y = np.clip(np.round((f + bc.MAX_CFO) / (CSTEP * bc.STEP)).astype(int), 0, NC_ - 1)
    return x, y


def _producer(seed, q, B):
    torch.set_num_threads(1)
    rng = np.random.default_rng(seed)
    while True:
        q.put(_batch(B, rng))


def train(a):
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)
    cfg = {"ch": CH, "layers": LAYERS, "k": KS}
    model = PostNet(**cfg)
    print(f"PostNet params {sum(p.numel() for p in model.parameters())}, ~{MACS / 1e6:.2f} M MACs / packet", flush=True)
    vrng = np.random.default_rng(a.seed + 1)
    val = {}
    for s in (-5.0, -3.0, -1.0, 1.0):
        xs, ys = zip(*[_batch(50, vrng, s, s) for _ in range(20)])
        val[s] = (torch.from_numpy(np.concatenate(xs)), np.concatenate(ys))
    q = mp.Queue(maxsize=64)
    procs = [mp.Process(target=_producer, daemon=True, args=(a.seed + 1000 * (i + 1), q, 32)) for i in range(a.producers)]
    for p in procs:
        p.start()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr * 1e-2)
    best, hist = np.inf, []
    for ep in range(1, a.epochs + 1):
        model.train()
        t0, tot = time.time(), 0.0
        for _ in range(a.steps):
            xs, ys = zip(*[q.get() for _ in range(4)])
            x = torch.from_numpy(np.concatenate(xs))
            y = torch.from_numpy(np.concatenate(ys)).long()
            loss = nn.functional.cross_entropy(model(x), y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item()
        model.eval()
        ranks = {}
        with torch.no_grad():
            for s, (x, y) in val.items():
                lg = model(x).numpy()
                ranks[s] = float(np.mean((lg > lg[np.arange(len(y)), y][:, None]).sum(1)))
        score = np.mean([ranks[-5.0], ranks[-3.0], ranks[-1.0]])
        mark = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict(), "config": cfg}, bc.path("models", MODEL))
            mark = " [BEST]"
        hist.append({"epoch": ep, "loss": tot / a.steps, "rank": ranks})
        print(f"Epoch {ep:3d}/{a.epochs} | CE {tot / a.steps:.4f} | mean coarse rank "
              + " ".join(f"{k:+.0f}dB {v:.2f}" for k, v in ranks.items()) + f" | {time.time() - t0:.0f}s{mark}",
              flush=True)
    json.dump(hist, open(bc.path("logs", "post_nn_train.json"), "w"), indent=1)
    for p in procs:
        p.terminate()
    print("TRAIN DONE", flush=True)


E5_SNRS = (-6.0, -5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0)


def _e5_work(task):
    snr, seed, n = task
    from polar import PolarCode
    torch.set_num_threads(1)
    code = PolarCode(bc.N_BITS, 205, 16, 8)
    rng = np.random.default_rng(seed)
    g = bf.grid(4)["f"]
    out = {"NN posterior (2-SPS features)": [], "analytic posterior (8-SPS features)": [],
           "analytic posterior (2-SPS features)": []}
    for _ in range(n // 50):
        _, _, r, rx, f, _ = bc.frames(50, code, snr, rng)
        t = np.abs(g[None] - f[:, None]).argmin(1)
        rows = np.arange(len(f))
        P, fs = posterior(r, rx, snr, 4)
        S4, fs8, C = bf.features2(r, rx, 4)
        S4l, fsl, Cl = vp.features_lite(r, rx, 4)
        for kname, sc in (("NN posterior (2-SPS features)", P),
                          ("analytic posterior (8-SPS features)", bf.posterior2(S4, fs8, C, snr, 4)),
                          ("analytic posterior (2-SPS features)", bf.posterior2(S4l, fsl, Cl, snr, 4))):
            out[kname] += list((sc > sc[rows, t][:, None]).sum(1).astype(int))
    return snr, out


def run_e5(part, workers, n, chunks):
    tasks = [(s, 7700 + 29 * i + int(10 * s + 100), n) for s in E5_SNRS for i in range(chunks)]
    acc = {}
    with mp.Pool(workers) as pool:
        for i, (snr, out) in enumerate(pool.imap_unordered(_e5_work, tasks), 1):
            a = acc.setdefault(snr, {})
            for k, v in out.items():
                a.setdefault(k, []).extend(v)
            with open(bc.path("logs", f"post_e5_{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} 0\n")
    res = []
    for snr in sorted(acc):
        for k, v in acc[snr].items():
            v = np.array(v)
            res.append({"snr": snr, "posterior": k, "frames": len(v), "rank_mean": float(v.mean()),
                        "rank_median": float(np.median(v)),
                        "P_rank_ge": {str(K): float(np.mean(v >= K)) for K in (1, 3, 10, 30, 100, 300, 1000)}})
        print(f"{snr:5.1f} dB " + " | ".join(f"{r['posterior']}: {r['rank_mean']:.1f}" for r in res if r["snr"] == snr),
              flush=True)
    json.dump(res, open(bc.path("results", f"post_e5_{part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["train", "ranks"])
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--producers", type=int, default=14)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--seed", type=int, default=2027)
    ap.add_argument("--part", default="a")
    ap.add_argument("--frames", type=int, default=2000)
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    train(a) if a.what == "train" else run_e5(a.part, a.workers, a.frames, a.chunks)
