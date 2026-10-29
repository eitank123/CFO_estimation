"""
Blind CFO, idea 3: an NN posterior over the 4th-power frequency bins, used to RANK the candidate peaks instead of the
raw periodogram height. Input: log |FFT_4096(-r^4)|^2 of the 1024-symbol packet (normalised to zero mean) and the SNR,
as two channels of a circular 1-D conv net (translation-equivariant along frequency, like the split-NN coarse stage).
Output: one logit per bin of 4f mod 1; trained with cross-entropy on the bin of the true 4f.

    python blind_nn.py --epochs 60          # -> blind/models/blind_nn.pth, blind/logs/blind_nn_train.json
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

SNR_CENTER, SNR_SCALE = 2.5, 7.5
MODEL = "blind_nn.pth"


class PeakNet(nn.Module):
    def __init__(self, ch=16, k=9, dil=(1, 2, 4, 8)):
        super().__init__()
        layers, c = [], 2
        for d in dil:
            layers += [nn.Conv1d(c, ch, k, padding=d * (k // 2), dilation=d, padding_mode="circular"), nn.GELU()]
            c = ch
        layers.append(nn.Conv1d(c, 1, k, padding=k // 2, padding_mode="circular"))
        self.net = nn.Sequential(*layers)

    def forward(self, logp, snr_db):
        s = ((snr_db - SNR_CENTER) / SNR_SCALE).float()[:, None, None].expand(-1, 1, logp.shape[1])
        return self.net(torch.cat([logp[:, None].float(), s], 1))[:, 0]


def features(r):
    p = np.log(np.abs(np.fft.fft(-(r ** 4), bc.NFFT4)) ** 2 + 1e-12)
    return torch.from_numpy(p - p.mean(1, keepdims=True))


def target(f):
    nu = (4 * f + 0.5) % 1.0 - 0.5
    return torch.from_numpy(np.round(nu * bc.NFFT4).astype(int) % bc.NFFT4)


def batch(B, rng, lo=-6.0, hi=11.0, fixed=None):
    from txrx_chain import qpsk, transmit
    snr = np.full(B, float(fixed)) if fixed is not None else rng.uniform(lo, hi, B)
    f = rng.uniform(-bc.MAX_CFO, bc.MAX_CFO, B)
    r = transmit(qpsk(rng, (B, bc.N_SYM)), f, rng.uniform(0, 2 * np.pi, B), snr, rng)
    return features(r), torch.from_numpy(snr), target(f)


def _producer(seed, q, B):
    """Batches as numpy arrays (pickled through the queue pipe: torch tensors would go through /dev/shm)."""
    torch.set_num_threads(1)
    rng = np.random.default_rng(seed)
    while True:
        q.put(tuple(v.numpy() for v in batch(B, rng)))


_model = None


def load():
    global _model
    if _model is None:
        ck = torch.load(bc.path("models", MODEL), map_location="cpu", weights_only=False)
        _model = PeakNet(**ck["config"])
        _model.load_state_dict(ck["state_dict"])
        _model.eval()
    return _model


def peak_bins(model, r, snr_db, P):
    """The P best bins (B, P) by NN logit, local maxima suppressed within +-8 bins (as the periodogram peaks)."""
    with torch.no_grad():
        lg = model(features(r), torch.full((len(r),), float(snr_db), dtype=torch.float64)).numpy()
    return bc.top_peaks(lg, P, radius=bc.NFFT4 // bc.N_SYM * 2)


def train(a):
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)
    cfg = {"ch": a.ch}
    model = PeakNet(**cfg)
    print(f"PeakNet params {sum(p.numel() for p in model.parameters())}", flush=True)
    vrng = np.random.default_rng(a.seed + 1)
    val = {s: batch(2000, vrng, fixed=s) for s in (-3, 0, 2, 5)}
    q = mp.Queue(maxsize=32)
    procs = [mp.Process(target=_producer, daemon=True, args=(a.seed + 1000 * (i + 1), q, a.batch))
             for i in range(a.producers)]
    for p in procs:
        p.start()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=a.epochs * a.steps, eta_min=a.lr * 1e-2)
    best, hist = -1.0, []
    for ep in range(1, a.epochs + 1):
        model.train()
        t0, tot = time.time(), 0.0
        for _ in range(a.steps):
            x, s, y = (torch.from_numpy(v) for v in q.get())
            loss = nn.functional.cross_entropy(model(x, s), y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item()
        model.eval()
        acc = {}
        with torch.no_grad():
            for sn, (x, s, y) in val.items():
                lg = model(x, s)
                d = (lg.argmax(1) - y).abs()
                acc[sn] = float(((d <= 1) | (d >= bc.NFFT4 - 1)).double().mean())     # top-1 within +-1 bin
        score = float(np.mean(list(acc.values())))
        mark = ""
        if score > best:
            best = score
            torch.save({"state_dict": model.state_dict(), "config": cfg}, bc.path("models", MODEL))
            mark = " [BEST]"
        hist.append({"epoch": ep, "loss": tot / a.steps, "top1": acc})
        print(f"Epoch {ep:3d}/{a.epochs} | CE {tot / a.steps:.4f} | top-1 (+-1 bin) "
              + " ".join(f"{k}:{v:.3f}" for k, v in acc.items()) + f" | {time.time() - t0:.0f}s{mark}", flush=True)
    json.dump(hist, open(bc.path("logs", "blind_nn_train.json"), "w"), indent=1)
    for p in procs:
        p.terminate()
    print("TRAIN DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--ch", type=int, default=16)
    ap.add_argument("--producers", type=int, default=13)
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--seed", type=int, default=2026)
    train(ap.parse_args())
