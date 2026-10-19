"""
SNR-aware CFO NN with FFT periodogram-peak information.

The expert features fail in the threshold region (low SNR) because they are
built from lag correlations. The periodogram peak (the ML coarse estimate) is
what keeps the ML estimator at the CRB down to about -6 dB, so it is given to
the network:

    aux = [ f_c / MAX_CFO,                         coarse FFT-peak frequency
            |X[k-1]|, |X[k]|, |X[k+1]|  (/ L),      peak and neighbour magnitudes
            Re/Im( X[k-1] X*[k] / |X[k]|^2 ),       neighbour-to-peak complex ratios
            Re/Im( X[k+1] X*[k] / |X[k]|^2 ) ]      (what bin interpolators use)

    X = FFT_K-point FFT of z[n] = r[n] conj(s[n])

Modes:
    residual  f_hat = f_c + bin * MLP([lag feats, snr, aux])     (last layer zero-init)
    input     f_hat = MLP([lag feats, snr, aux])                   (init from SNR-aware MLP)

Usage:
    python train_fft_nn.py --mode residual --epochs 150
"""

import argparse
import paths
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

from Hybrid import FusionNetwork, DenseCFOEstimator
from train_snr_nn import (EVAL_SNRS, EXPERT_PATH, FUSION_PATH, MAX_CFO, MAX_LAG, PREAMBLE_LENGTH,
                          SNR_CENTER, SNR_SCALE, SNRAwareCFOEstimator, count_params, crb, lag_features,
                          make_z, mm_estimate, print_table)

FFT_K = 256
N_AUX = 8
BIN = 1.0 / (FFT_K * MAX_CFO)          # one FFT bin in normalized-CFO units
SNR_AWARE_PATH = paths.model("snr_aware_cfo_model_L64.pth")


# =====================================================================
# Features
# =====================================================================

def fft_features(z, K=FFT_K):
    """aux (B, N_AUX) float32 and coarse frequency f_c (B,) in cycles/symbol."""
    L = z.shape[1]
    X = torch.fft.fft(z, n=K)
    mag = X.abs()
    freqs = torch.fft.fftfreq(K, dtype=torch.float64)
    masked = mag.masked_fill((freqs.abs() > MAX_CFO + 1.0 / K).unsqueeze(0), -1.0)
    k = masked.argmax(1)
    idx = torch.stack([(k - 1) % K, k, (k + 1) % K], dim=1)
    Xn = X.gather(1, idx)
    peak = Xn[:, 1:2]
    ratios = Xn[:, [0, 2]] * peak.conj() / (peak.abs() ** 2)
    fc = freqs[k]
    aux = torch.cat([
        (fc / MAX_CFO).unsqueeze(1),
        Xn.abs() / L,
        ratios.real, ratios.imag,
    ], dim=1).float()
    return aux, fc


def ml_estimate(z, fc, iters=2):
    """Classical ML reference: FFT coarse + Newton steps on the periodogram. Normalized CFO."""
    n = torch.arange(z.shape[1], dtype=torch.float64)
    f = fc.clone()
    for _ in range(iters):
        e = torch.exp(-1j * 2 * np.pi * f[:, None] * n)
        A = (z * e).sum(1)
        A1 = (z * e * (-1j * 2 * np.pi * n)).sum(1)
        A2 = (z * e * (-(2 * np.pi * n) ** 2)).sum(1)
        f = f - 2 * (A1 * A.conj()).real / (2 * ((A2 * A.conj()).real + A1.abs() ** 2))
    return (f / MAX_CFO).float().unsqueeze(1)


def make_fft_batch(batch_size, snr_low, snr_high, gen, device, fixed_snr=None, keep_z=False):
    z, y, snr_db = make_z(batch_size, snr_low, snr_high, gen, fixed_snr)
    feats, R = lag_features(z)
    aux, fc = fft_features(z)
    out = {"feats": feats.to(device), "R": R, "aux": aux.to(device), "fc": fc,
           "y": y.float().to(device), "snr": snr_db.float().to(device)}
    if keep_z:
        out["z"] = z
    return out


# =====================================================================
# Model
# =====================================================================

class FFTAidedCFOEstimator(nn.Module):

    def __init__(self, hidden=(128, 64, 32), residual=True, max_lag=MAX_LAG, in_channels=4):
        super().__init__()
        self.residual = residual
        layers, d = [], max_lag * in_channels + 1 + N_AUX
        for h in hidden:
            layers += [nn.Linear(d, h), nn.GELU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)
        if residual:
            nn.init.zeros_(self.net[-1].weight)
            nn.init.zeros_(self.net[-1].bias)

    def forward(self, x, snr_db, aux):
        s = (snr_db.view(-1, 1) - SNR_CENTER) / SNR_SCALE
        out = self.net(torch.cat([x.flatten(1), s, aux], dim=1))
        return aux[:, :1] + BIN * out if self.residual else out


def init_from_snr_aware(model, path=SNR_AWARE_PATH):
    """Copy SNR-aware MLP weights; the new aux input columns start at zero."""
    state = torch.load(path, map_location="cpu", weights_only=False)["state_dict"]
    lins = [m for m in model.net if isinstance(m, nn.Linear)]
    keys = [k for k in state if k.endswith(".weight")]
    with torch.no_grad():
        for lin, wk in zip(lins, keys):
            w, b = state[wk], state[wk.replace(".weight", ".bias")]
            lin.weight.zero_()
            lin.weight[:, :w.shape[1]] = w
            lin.bias.copy_(b)


# =====================================================================
# Complexity (per estimate, multiply-accumulates; 1 complex MAC = 4 real MACs)
# =====================================================================

def mlp_macs(module):
    return sum(m.in_features * m.out_features for m in module.modules() if isinstance(m, nn.Linear))


def complexity_table(models):
    L, M, K = PREAMBLE_LENGTH, MAX_LAG, FFT_K
    lag_cmacs = sum(L - m for m in range(1, M + 1))          # direct C_m for m = 1..M
    fft_cmacs = (K // 2) * int(np.log2(K))                     # radix-2 FFT
    newton_cmacs = 2 * 3 * L                                  # 2 iterations x 3 sums over L
    rows = [
        ("M&M", lag_cmacs * 4 + M * 4, 0, f"O(M*L) lag correlations, M={M}"),
        ("ML (FFT256 + 2 Newton)", (fft_cmacs + newton_cmacs) * 4, 0, "O(K log K + I*L)"),
        ("Expert NN", lag_cmacs * 4 + mlp_macs(models["Expert NN"]), count_params(models["Expert NN"]),
         "O(M*L) features + MLP"),
        ("Fusion", lag_cmacs * 4 + M * 4 + mlp_macs(models["Expert NN"]) + mlp_macs(models["fusion net"]),
         count_params(models["Expert NN"]) + count_params(models["fusion net"]), "expert + M&M + fusion net"),
        ("SNR-aware MLP", lag_cmacs * 4 + mlp_macs(models["SNR-aware MLP"]), count_params(models["SNR-aware MLP"]),
         "O(M*L) features + MLP"),
        ("FFT-aided NN", lag_cmacs * 4 + fft_cmacs * 4 + mlp_macs(models["FFT-aided NN"]),
         count_params(models["FFT-aided NN"]), "O(M*L + K log K) features + MLP"),
    ]
    print("\nComplexity per CFO estimate (real multiply-accumulates; 1 complex MAC = 4 real):")
    print(f"  {'Estimator':<24} {'real MACs':>10} {'params':>8}   notes")
    for name, macs, params, note in rows:
        print(f"  {name:<24} {macs:>10,} {params:>8,}   {note}")
    print(f"  (lag correlations: {lag_cmacs} complex MACs; FFT{K}: {fft_cmacs} complex MACs)")


# =====================================================================
# Train / evaluate
# =====================================================================

@torch.no_grad()
def eval_mse(predict, sets):
    out = {}
    for s, b in sets.items():
        out[s] = float((((predict(b) - b["y"]) * MAX_CFO) ** 2).mean())
    return out


def train(args, device):
    torch.manual_seed(args.seed)
    model = FFTAidedCFOEstimator(hidden=tuple(args.hidden), residual=(args.mode == "residual")).to(device)
    if args.mode == "input":
        init_from_snr_aware(model)
        print(f"Initialized from {SNR_AWARE_PATH}")
    print(f"Mode {args.mode} | hidden {args.hidden} | params {count_params(model)} | FFT K={FFT_K}", flush=True)

    vgen = torch.Generator().manual_seed(args.seed + 1)
    val_sets = {s: make_fft_batch(args.val_per_snr, s, s, vgen, device, fixed_snr=s) for s in EVAL_SNRS}
    predict = lambda b: model(b["feats"], b["snr"], b["aux"])

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs * args.steps,
                                                           eta_min=args.lr * 1e-3)
    gen = torch.Generator().manual_seed(args.seed)
    best, history = float("inf"), []

    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            b = make_fft_batch(args.batch, args.train_snr[0], args.train_snr[1], gen, device)
            pred = predict(b)
            c = torch.as_tensor(crb(b["snr"].double().cpu().numpy()), dtype=torch.float32, device=device)
            loss = (((pred - b["y"]).squeeze(1) * MAX_CFO) ** 2 / c).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            scheduler.step()
            run += loss.item()

        model.eval()
        val = eval_mse(predict, val_sets)
        ratios = np.array([val[s] / crb(s) for s in EVAL_SNRS])
        score = ratios.mean()
        history.append((run / args.steps, score))
        marker = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict(),
                        "config": {"mode": args.mode, "hidden": list(args.hidden), "fft_k": FFT_K,
                                   "max_lag": MAX_LAG, "max_cfo": MAX_CFO, "snr_center": SNR_CENTER,
                                   "snr_scale": SNR_SCALE, "train_snr": list(args.train_snr)}}, args.out)
            marker = " [BEST]"
        print(f"Epoch {epoch:3d}/{args.epochs} | train MSE/CRB {run / args.steps:8.3f} | "
              f"val MSE/CRB mean {score:6.3f} max {ratios.max():6.3f} (@{EVAL_SNRS[ratios.argmax()]} dB) | "
              f"lr {scheduler.get_last_lr()[0]:.2e} | {time.time() - t0:.0f}s{marker}", flush=True)
        if epoch % 10 == 0 or epoch == args.epochs:
            print("   " + " ".join(f"{s}:{r:.2f}" for s, r in zip(EVAL_SNRS, ratios)), flush=True)
    return history


def final_comparison(args, history, device):
    ck = torch.load(args.out, map_location=device, weights_only=False)
    model = FFTAidedCFOEstimator(hidden=tuple(ck["config"]["hidden"]),
                                 residual=(ck["config"]["mode"] == "residual")).to(device)
    model.load_state_dict(ck["state_dict"])
    model.eval()

    sck = torch.load(SNR_AWARE_PATH, map_location=device, weights_only=False)
    snr_mlp = SNRAwareCFOEstimator(hidden=tuple(sck["config"]["hidden"]),
                                   use_snr=sck["config"].get("use_snr", True)).to(device)
    snr_mlp.load_state_dict(sck["state_dict"])
    snr_mlp.eval()

    expert = DenseCFOEstimator(MAX_LAG, 4).to(device)
    expert.load_state_dict(torch.load(EXPERT_PATH, map_location=device, weights_only=True))
    expert.eval()

    fck = torch.load(FUSION_PATH, map_location=device, weights_only=False)
    f_exp = DenseCFOEstimator(MAX_LAG, 4).to(device)
    f_exp.load_state_dict(fck["phase1_state"])
    f_exp.eval()
    fusion = FusionNetwork(in_features=2).to(device)
    fusion.load_state_dict(fck["phase2_state"])
    fusion.eval()

    def fusion_predict(b):
        nn_est, mm_est = f_exp(b["feats"]), mm_estimate(b["R"]).to(device)
        return fusion(torch.cat([nn_est, mm_est], 1), nn_est, mm_est)[0]

    name = f"FFT-aided NN ({args.mode})"
    predictors = {
        name: lambda b: model(b["feats"], b["snr"], b["aux"]),
        "SNR-aware MLP": lambda b: snr_mlp(b["feats"], b["snr"]),
        "Expert NN": lambda b: expert(b["feats"]),
        "Fusion": fusion_predict,
        "M&M": lambda b: mm_estimate(b["R"]).to(device),
        "ML (FFT+Newton)": lambda b: ml_estimate(b["z"], b["fc"]).to(device),
    }

    # Generate the test set one SNR at a time to keep memory small
    tgen = torch.Generator().manual_seed(args.seed + 2)
    mses = {n: {} for n in predictors}
    with torch.no_grad():
        for s in EVAL_SNRS:
            b = make_fft_batch(args.test_per_snr, s, s, tgen, device, fixed_snr=s, keep_z=True)
            for n, p in predictors.items():
                mses[n][s] = float((((p(b) - b["y"]) * MAX_CFO) ** 2).mean())

    print("\n" + "=" * 150)
    print(f"TEST: MSE (xCRB), {args.test_per_snr} samples per SNR (true SNR given to SNR-aware models)")
    print("=" * 150)
    print_table("", list(predictors), mses)
    print("\nMean MSE/CRB over SNR -5..10 dB:")
    for n in predictors:
        print(f"  {n:<26} {np.mean([mses[n][s] / crb(s) for s in EVAL_SNRS]):6.3f}")
    complexity_table({"Expert NN": expert, "fusion net": fusion, "SNR-aware MLP": snr_mlp, "FFT-aided NN": model})
    print("TEST DONE", flush=True)

    plt.figure(figsize=(10, 6))
    for n in predictors:
        plt.plot(EVAL_SNRS, [mses[n][s] / crb(s) for s in EVAL_SNRS], marker="o", markersize=4, label=n)
    plt.axhline(1.0, color="r", linestyle="--", linewidth=2, label="CRB")
    plt.yscale("log")
    plt.xlabel("SNR (dB)")
    plt.ylabel("MSE / CRB")
    plt.title("CFO estimator efficiency: MSE / CRB vs. SNR")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"fft_nn_{args.mode}_mse_over_crb.png"), dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    for n in predictors:
        plt.semilogy(EVAL_SNRS, [mses[n][s] for s in EVAL_SNRS], marker="o", markersize=4, label=n)
    plt.semilogy(EVAL_SNRS, [crb(s) for s in EVAL_SNRS], "r--", linewidth=2, label="CRB")
    plt.xlabel("SNR (dB)")
    plt.ylabel("CFO MSE")
    plt.title("CFO estimation MSE vs. SNR")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"fft_nn_{args.mode}_mse_vs_snr.png"), dpi=300, bbox_inches="tight")
    plt.close()

    if history:
        tr, va = zip(*history)
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(tr) + 1), tr, label="Train MSE/CRB")
        plt.plot(range(1, len(va) + 1), va, "--", label="Val mean MSE/CRB")
        plt.yscale("log")
        plt.xlabel("Epoch")
        plt.ylabel("MSE / CRB")
        plt.title(f"FFT-aided NN training ({args.mode})")
        plt.grid(True, which="both", linestyle=":", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(paths.plot(f"fft_nn_{args.mode}_training.png"), dpi=300, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["residual", "input"], default="residual")
    ap.add_argument("--hidden", type=int, nargs="+", default=[128, 64, 32])
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=5000)
    ap.add_argument("--test-per-snr", type=int, default=20000)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--eval-only", action="store_true")
    args = ap.parse_args()
    args.out = paths.model(f"fft_nn_{args.mode}_cfo_model_L64.pth")
    torch.set_num_threads(args.threads)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    hist = [] if args.eval_only else train(args, device)
    final_comparison(args, hist, device)
