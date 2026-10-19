"""
FFT-free version of the FFT-aided NN (train_fft_nn.py): the 8 FFT-peak features are removed, so the
network sees only the 64 lag correlations R(m) (computed directly, no FFT anywhere) and the SNR.

Variants (--variant):
    plain    exactly the FFT-aided NN minus its 8 FFT features: MLP([lag feats, SNR]) -> f directly.
             This is the SNR-aware NN's input; initialised from snr_aware_cfo_model_L64.pth.
    unwrap   FFT-free coarse estimate from the same lags, by lag-doubling phase unwrapping:
                 f_1 = arg R(1) / 2pi                      (unambiguous for |f| < 0.5)
                 f_m = f_{m/2} + arg(R(m) e^{-j 2 pi m f_{m/2}}) / (2 pi m),   m = 2, 4, ..., 64
             The lag features are de-rotated by f_64 (R(m) e^{-j 2 pi m f_64}), and the MLP outputs a
             residual on f_64 (last layer zero-initialised, as the FFT-aided NN's residual on the FFT
             peak). Inputs: 64 x 4 de-rotated lag features + SNR + f_64 = 258.

Same training as the FFT-aided NN: on the fly, AWGN symbol-rate model, CFO ~ U[-0.2, 0.2],
Es/N0 ~ U[-6, 11] dB, loss = error^2 / CRB, AdamW + cosine decay, best mean val MSE/CRB kept.

Usage:
    python train_nofft_nn.py --variant unwrap --epochs 150     # -> nofft_nn_unwrap.pth, nofft_nn_unwrap.log
"""

import argparse
import paths
import os
import time

import numpy as np
import torch
import torch.nn as nn

from train_snr_nn import (EVAL_SNRS, MAX_CFO, MAX_LAG, PREAMBLE_LENGTH, SNR_CENTER, SNR_SCALE, crb,
                          lag_features, make_z)

UNWRAP_LAGS = (2, 4, 8, 16, 32, 64)
RES_SCALE = 1.0 / 256                       # residual unit (cycles/symbol), = one bin of the old FFT 256
SNR_AWARE_PATH = paths.model("snr_aware_cfo_model_L64.pth")


# =====================================================================
# Features (no FFT: R(m) is defined as the direct lag correlation; torch computes it via FFT only for speed)
# =====================================================================

def unwrap_coarse(R):
    """Lag-doubling phase unwrapping on R (B, 64) complex -> f (B,) cycles/symbol."""
    f = R[:, 0].angle() / (2 * np.pi)
    for m in UNWRAP_LAGS:
        f = f + (R[:, m - 1] * torch.exp(-2j * np.pi * m * f)).angle() / (2 * np.pi * m)
    return f


def features(z, variant):
    feats, R = lag_features(z)
    if variant == "plain":
        return feats, None
    f_c = unwrap_coarse(R)
    m = torch.arange(1, MAX_LAG + 1, dtype=torch.float64)
    Rd = R * torch.exp(-2j * np.pi * m * f_c[:, None])
    feats = torch.stack([Rd.real, Rd.imag, Rd.abs(), Rd.angle()], dim=2).float()
    return feats, f_c


def make_batch(B, lo, hi, gen, fixed_snr=None, variant="unwrap"):
    z, y, snr = make_z(B, lo, hi, gen, fixed_snr)
    feats, f_c = features(z, variant)
    return {"feats": feats, "fc": None if f_c is None else f_c.float(), "y": y.float(), "snr": snr.float()}


# =====================================================================
# Model
# =====================================================================

class NoFFTCFOEstimator(nn.Module):
    def __init__(self, variant="unwrap", hidden=(128, 64, 32)):
        super().__init__()
        self.variant = variant
        layers, d = [], MAX_LAG * 4 + 1 + (variant != "plain")
        for h in hidden:
            layers += [nn.Linear(d, h), nn.GELU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)
        if variant != "plain":
            nn.init.zeros_(self.net[-1].weight)
            nn.init.zeros_(self.net[-1].bias)

    def forward(self, b):
        s = (b["snr"].view(-1, 1) - SNR_CENTER) / SNR_SCALE
        if self.variant == "plain":                             # normalised CFO f / MAX_CFO
            return self.net(torch.cat([b["feats"].flatten(1), s], 1))
        fc = b["fc"].view(-1, 1)
        out = self.net(torch.cat([b["feats"].flatten(1), s, fc / MAX_CFO], 1))
        return (fc + RES_SCALE * out) / MAX_CFO


def init_plain_from_snr_aware(model):
    st = torch.load(SNR_AWARE_PATH, map_location="cpu", weights_only=False)["state_dict"]
    lins = [m for m in model.net if isinstance(m, nn.Linear)]
    keys = [k for k in st if k.endswith(".weight")]
    with torch.no_grad():
        for lin, k in zip(lins, keys):
            lin.weight.copy_(st[k])
            lin.bias.copy_(st[k.replace(".weight", ".bias")])


def macs(model):
    lag = sum(PREAMBLE_LENGTH - m for m in range(1, MAX_LAG + 1)) * 4            # direct lag correlations
    mlp = sum(l.in_features * l.out_features for l in model.modules() if isinstance(l, nn.Linear))
    extra = 0 if model.variant == "plain" else (len(UNWRAP_LAGS) * 4 + MAX_LAG * 4)  # unwrap + de-rotation
    return lag + mlp + extra, lag, mlp, extra


# =====================================================================
# Train
# =====================================================================

def train(args, log):
    torch.manual_seed(args.seed)
    model = NoFFTCFOEstimator(args.variant, tuple(args.hidden))
    if args.variant == "plain":
        init_plain_from_snr_aware(model)
        log(f"initialised from {SNR_AWARE_PATH}")
    total, lag, mlp, extra = macs(model)
    log(f"variant {args.variant} | hidden {args.hidden} | params {sum(p.numel() for p in model.parameters()):,} | "
        f"real MACs {total:,} (lags {lag:,} + MLP {mlp:,} + unwrap/de-rotation {extra:,})")
    vgen = torch.Generator().manual_seed(args.seed + 1)
    val = {s: make_batch(args.val_per_snr, s, s, vgen, s, args.variant) for s in EVAL_SNRS}
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    gen = torch.Generator().manual_seed(args.seed)
    if args.variant != "plain":
        with torch.no_grad():
            r = [float((((val[s]["fc"] / MAX_CFO - val[s]["y"][:, 0]) * MAX_CFO) ** 2).mean()) / crb(s) for s in EVAL_SNRS]
        log("coarse (unwrap only) MSE/CRB: " + " ".join(f"{s}:{x:.2f}" for s, x in zip(EVAL_SNRS, r)))
    best = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            b = make_batch(args.batch, *args.train_snr, gen, variant=args.variant)
            c = torch.as_tensor(crb(b["snr"].double().numpy()), dtype=torch.float32)
            loss = (((model(b) - b["y"]).squeeze(1) * MAX_CFO) ** 2 / c).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += loss.item()
        model.eval()
        with torch.no_grad():
            ratios = np.array([float((((model(val[s]) - val[s]["y"]) * MAX_CFO) ** 2).mean()) / crb(s) for s in EVAL_SNRS])
        mark = ""
        if ratios.mean() < best:
            best = ratios.mean()
            torch.save({"state_dict": model.state_dict(), "config": {"variant": args.variant, "hidden": list(args.hidden)}},
                       args.out)
            mark = " [BEST]"
        log(f"Epoch {epoch:3d}/{args.epochs} | train MSE/CRB {run / args.steps:8.3f} | val MSE/CRB mean "
            f"{ratios.mean():6.3f} max {ratios.max():6.3f} (@{EVAL_SNRS[ratios.argmax()]} dB) | "
            f"{time.time() - t0:.0f}s{mark}")
        if epoch % 10 == 0 or epoch == args.epochs:
            log("   " + " ".join(f"{s}:{r:.2f}" for s, r in zip(EVAL_SNRS, ratios)))
    log("TRAIN DONE")


def load(path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    m = NoFFTCFOEstimator(ck["config"]["variant"], tuple(ck["config"]["hidden"]))
    m.load_state_dict(ck["state_dict"])
    m.eval()
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["plain", "unwrap"], default="unwrap")
    ap.add_argument("--hidden", type=int, nargs="+", default=[128, 64, 32])
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=5000)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--tag", default="", help="suffix of the output files")
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    name = f"nofft_nn_{args.variant}{args.tag}"
    args.out = paths.model(name + ".pth")
    log_f = open(paths.log(name + ".log"), "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    train(args, log)
