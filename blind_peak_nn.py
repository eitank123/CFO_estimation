"""
A small NN that grades the fast path's 4th-power peaks (blind_fast.sps3_receive, fast_nn).

The fast path takes one of the top P = 16 peaks of the 4th-power periodogram (pre-MF at the lag-4 autocorrelation
CFO fa). The hand rules use only the peak heights (blind) or the 24-pilot coherent sum (pilots). The network sees,
per peak:
    log height / mean, height / strongest, rank, distance to fa in units of the autocorrelation std at this SNR
    (prior information the rules ignore), the pilot coherent sum / K (pilots model), SNR
and scores every peak with a shared MLP; a "none" logit from the pooled hidden features says that no peak is the
right one, so the fast-path decode can be skipped (the packet goes to the search directly).
Label: the peak whose resolved CFO is within 1.5e-4 of the true CFO (bins are 6.1e-5 in f), else "none".
~25k MACs per packet (MACS).

    python blind_peak_nn.py train --mode blind      # -> blind/models/peak_nn_blind.pth
    python blind_peak_nn.py train --mode pilots     # -> blind/models/peak_nn_pilots.pth (24 pilots, N3x8)
    python blind_peak_nn.py eval --mode pilots      # pick accuracy vs the hand rules, per SNR
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

P = 16                                            # peaks graded
NF = 6                                            # features per peak
H = 32                                            # hidden width
TOL = 1.5e-4                                      # label: resolved peak CFO within TOL of the true CFO
MACS = P * (NF * H + H * H + H) + H * H + H + P * 8 * 24   # per-peak MLP + none head + pilot sums


def features(r1, Y4a, fa, snr, zp=None, pos=None):
    """Per-peak features (B, P, NF), candidate CFOs (B, P), peak bins (B, P) from the 4th-power magnitude Y4a
    (B, NFFT4) of the MF output r1 pre-MF corrected at fa."""
    nf = Y4a.shape[1]
    pk = bc.top_peaks(Y4a, P, 2)
    fc = bc.resolve(np.fft.fftfreq(nf)[pk], fa)
    hp = np.take_along_axis(Y4a, pk, 1)
    sig = float(np.interp(snr, *zip(*bf.ACF_SIGMA)))
    x = np.empty((len(fc), P, NF), np.float32)
    x[..., 0] = np.log(hp / Y4a.mean(1, keepdims=True))
    x[..., 1] = hp / hp[:, :1]
    x[..., 2] = np.arange(P)[None] / P
    x[..., 3] = np.clip(np.abs(fc - fa[:, None]) / sig, 0, 8)
    if zp is not None:
        nc = np.asarray(pos, float) - bc.CENTRE
        x[..., 4] = np.abs(np.einsum("bk,bpk->bp", zp, np.exp(-2j * np.pi * fc[:, :, None] * nc[None, None]))) / len(pos)
    else:
        x[..., 4] = 0.0
    x[..., 5] = snr / 10.0
    return x, fc, pk


def _np_forward(W, x):
    """Numpy inference: logits (B, P + 1) (last = none)."""
    h = np.maximum(x @ W["w1"] + W["b1"], 0)
    h = np.maximum(h @ W["w2"] + W["b2"], 0)
    s = (h @ W["w3"] + W["b3"])[..., 0]
    g = np.maximum(h.max(1) @ W["wn1"] + W["bn1"], 0)
    n = (g @ W["wn2"] + W["bn2"])[:, :1]
    return np.concatenate([s, n], 1)


_W = {}


def load(mode):
    if mode not in _W:
        z = np.load(bc.path("models", f"peak_nn_{mode}.npz"))
        _W[mode] = {k: z[k] for k in z.files}
    return _W[mode]


def grade(mode, x):
    """Softmax over the P peaks + none (B, P + 1)."""
    lg = _np_forward(load(mode), x)
    lg -= lg.max(1, keepdims=True)
    e = np.exp(lg)
    return e / e.sum(1, keepdims=True)


# ------------------------------------------------------------------ training data (the receiver's own fast-path chain)
def _batch(B, rng, mode, lo=-6.0, hi=5.0, snr=None):
    from polar import PolarCode
    code = PolarCode(bc.N_BITS, 205, 16, 8)
    snr = float(rng.uniform(lo, hi)) if snr is None else snr
    _, cw, r, rx, f, _ = bc.frames(B, code, snr, rng)
    fa = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
    r1 = bf.premf(r, rx, fa)
    Y4a = np.abs(np.fft.fft(-(r1 ** 4), bc.NFFT4))
    zp = pos = None
    if mode == "pilots":
        pos = np.array(vp.PATTERNS["N3x8"])
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        zp = r1[:, pos] * np.conj(sym[:, pos])
    x, fc, _ = features(r1, Y4a, fa, snr, zp, pos)
    err = np.abs(fc - f[:, None])
    y = np.where(err.min(1) < TOL, err.argmin(1), P)
    return x, y


def _producer(seed, q, B, mode):
    rng = np.random.default_rng(seed)
    while True:
        q.put(_batch(B, rng, mode))


def train(a):
    import torch
    import torch.nn as nn
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)

    class PeakNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.peak = nn.Sequential(nn.Linear(NF, H), nn.ReLU(), nn.Linear(H, H), nn.ReLU())
            self.out = nn.Linear(H, 1)
            self.none = nn.Sequential(nn.Linear(H, H), nn.ReLU(), nn.Linear(H, 1))

        def forward(self, x):
            h = self.peak(x)
            return torch.cat([self.out(h)[..., 0], self.none(h.max(1).values)], 1)

    model = PeakNet()
    print(f"PeakNet ({a.mode}) params {sum(p.numel() for p in model.parameters())}, ~{MACS / 1e3:.0f}k MACs / packet",
          flush=True)
    vrng = np.random.default_rng(a.seed + 1)
    val = {s: _batch(2000, vrng, a.mode, snr=s) for s in (-3.0, -1.0, 0.5, 1.0, 2.0)}
    q = mp.Queue(maxsize=64)
    procs = [mp.Process(target=_producer, daemon=True, args=(a.seed + 1000 * (i + 1), q, 256, a.mode))
             for i in range(a.producers)]
    for p in procs:
        p.start()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr * 1e-2)
    best, hist = -1.0, []
    for ep in range(1, a.epochs + 1):
        model.train()
        t0, tot = time.time(), 0.0
        for _ in range(a.steps):
            xs, ys = zip(*[q.get() for _ in range(2)])
            x = torch.from_numpy(np.concatenate(xs))
            y = torch.from_numpy(np.concatenate(ys)).long()
            loss = nn.functional.cross_entropy(model(x), y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item()
        model.eval()
        acc = {}
        with torch.no_grad():
            for s, (x, y) in val.items():
                lg = model(torch.from_numpy(x)).numpy()
                hit = y < P
                acc[s] = float(np.mean((lg[:, :P].argmax(1) == y) & hit))
        score = float(np.mean(list(acc.values())))
        mark = ""
        if score > best:
            best = score
            sd = model.state_dict()
            np.savez(bc.path("models", f"peak_nn_{a.mode}.npz"),
                     w1=sd["peak.0.weight"].numpy().T, b1=sd["peak.0.bias"].numpy(),
                     w2=sd["peak.2.weight"].numpy().T, b2=sd["peak.2.bias"].numpy(),
                     w3=sd["out.weight"].numpy().T, b3=sd["out.bias"].numpy(),
                     wn1=sd["none.0.weight"].numpy().T, bn1=sd["none.0.bias"].numpy(),
                     wn2=sd["none.2.weight"].numpy().T, bn2=sd["none.2.bias"].numpy())
            mark = " [BEST]"
        hist.append({"epoch": ep, "loss": tot / a.steps, "acc": acc})
        print(f"Epoch {ep:3d}/{a.epochs} | CE {tot / a.steps:.4f} | right peak picked "
              + " ".join(f"{k:+.1f}dB {v:.3f}" for k, v in acc.items()) + f" | {time.time() - t0:.0f}s{mark}",
              flush=True)
    json.dump(hist, open(bc.path("logs", f"peak_nn_{a.mode}_train.json"), "w"), indent=1)
    for p in procs:
        p.terminate()
    print("TRAIN DONE", flush=True)


def evaluate(a):
    """Pick accuracy per SNR: NN vs the strongest peak and (pilots) the pilot rule with the 0.7 height gate; the
    best possible (true CFO among the P peaks); the none head at a few thresholds."""
    rng = np.random.default_rng(a.seed + 7)
    for s in (-3.0, -2.0, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 3.0):
        x, y = _batch(a.frames, rng, a.mode, snr=s)
        hit = y < P
        pr = grade(a.mode, x)
        nn_pick = pr[:, :P].argmax(1)
        line = (f"{s:+.1f} dB: in top {P} {hit.mean():.3f} | strongest {np.mean(hit & (y == 0)):.3f} | "
                f"NN {np.mean(hit & (nn_pick == y)):.3f}")
        if a.mode == "pilots":
            live = x[..., 1] >= 0.7
            rule = np.where(live, x[..., 4], -1).argmax(1)
            line += f" | pilot rule {np.mean(hit & (rule == y)):.3f}"
        for tau in (0.5, 0.8, 0.9):
            skip = pr[:, P] > tau
            line += f" | none>{tau}: skip {skip.mean():.2f} (wrongly {np.mean(skip & hit & (nn_pick == y)):.3f})"
        print(line, flush=True)
    print("EVAL DONE", flush=True)


def retry(a):
    """Stage 2 candidate: when the fast-path pick is wrong, is the NN's 2nd / 3rd choice right? A retry decode costs
    ~0.19 M MACs against ~0.9 M for the search statistics, so it pays off if P(right | 1st wrong) is high enough.
    Also P(1st right) at a few NN-confidence levels (a confident pick that fails the CRC = noise, not a wrong CFO)."""
    rng = np.random.default_rng(a.seed + 9)
    for s in (-1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5):
        x, y = _batch(a.frames, rng, a.mode, snr=s)
        pr = grade(a.mode, x)[:, :P]
        o = np.argsort(-pr, 1)
        wrong1 = o[:, 0] != y
        line = f"{s:+.1f} dB: 1st wrong {wrong1.mean():.3f}"
        for j in (1, 2, 3):
            line += f" | P(choice {j + 1} right | earlier wrong) {np.mean(o[wrong1, j] == y[wrong1]):.3f}"
            wrong1 = wrong1 & (o[:, j] != y)
        line += f" | truth not in top {P} {np.mean(y == P):.3f}"
        p1 = pr.max(1)
        for tau in (0.5, 0.9, 0.99):
            m = p1 > tau
            line += f" | p1>{tau}: {m.mean():.2f} of packets, right {np.mean(o[m, 0] == y[m]) if m.any() else 0:.4f}"
        print(line, flush=True)
    print("RETRY DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["train", "eval", "retry"])
    ap.add_argument("--mode", choices=["blind", "pilots"], default="blind")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--producers", type=int, default=6)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--frames", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    {"train": train, "eval": evaluate, "retry": retry}[a.action](a)
