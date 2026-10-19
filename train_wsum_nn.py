"""
Low-complexity CFO estimator: learned, input/SNR-adaptive weighting of the
M&M phase increments.

    dphi_1 = angle(R_1),  dphi_m = angle(R_m conj(R_{m-1}))     (no wrapping for |f| < 0.5)
    w      = w_MM + g(x)                                         (g last layer zero-init)
    f_hat  = sum_m w_m dphi_m / (2 pi)

At high SNR the CRB-achieving estimator is (close to) a fixed linear
combination of the dphi_m, which this structure represents exactly (it starts
as M&M). The small gate network g only has to learn how to re-weight lags when
noise makes some increments unreliable (low SNR / threshold region).

Archs:
    wsum      g([|R_m|, dphi_m/pi, snr])  -> 2M+1 -> hidden -> M
    wsum-snr  g(snr)                      -> 1    -> hidden -> M   (weights depend on SNR only)

Usage:
    python train_wsum_nn.py --arch wsum --epochs 150
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
                          SNR_CENTER, SNR_SCALE, SNRAwareCFOEstimator, count_params, crb, make_batch,
                          make_eval_sets, mm_estimate, mse_per_snr, print_table)


def mm_weights(M=MAX_LAG, L=PREAMBLE_LENGTH):
    m = np.arange(1, M + 1)
    return 3 * ((L - m) * (L - m + 1) - M * (L - M)) / (M * (4 * M ** 2 - 6 * M * L + 3 * L ** 2 - 1))


def phase_increments(R):
    dphi = torch.empty(R.shape, dtype=torch.float32, device=R.device)
    dphi[:, 0] = R[:, 0].angle()
    dphi[:, 1:] = (R[:, 1:] * R[:, :-1].conj()).angle()
    return dphi


class WeightedPhaseCFOEstimator(nn.Module):

    def __init__(self, max_lag=MAX_LAG, hidden=32, use_features=True):
        super().__init__()
        self.use_features = use_features
        in_dim = 2 * max_lag + 1 if use_features else 1
        self.gate = nn.Sequential(nn.Linear(in_dim, hidden), nn.GELU(), nn.Linear(hidden, max_lag))
        nn.init.zeros_(self.gate[-1].weight)
        nn.init.zeros_(self.gate[-1].bias)
        self.register_buffer("w_mm", torch.tensor(mm_weights(max_lag), dtype=torch.float32))

    def forward(self, R, snr_db):
        """R: complex lag correlations (B, M). Returns normalized CFO (B, 1)."""
        dphi = phase_increments(R)
        s = ((snr_db.view(-1, 1) - SNR_CENTER) / SNR_SCALE).float()
        x = torch.cat([R.abs().float(), dphi / np.pi, s], dim=1) if self.use_features else s
        w = self.w_mm + self.gate(x) * 1e-2   # small scale keeps early updates gentle
        return ((w * dphi).sum(1, keepdim=True) / (2 * np.pi)) / MAX_CFO


def train(args, device):
    torch.manual_seed(args.seed)
    model = WeightedPhaseCFOEstimator(hidden=args.hidden, use_features=(args.arch == "wsum")).to(device)
    print(f"Arch {args.arch} | hidden {args.hidden} | params {count_params(model)}", flush=True)

    val_sets = make_eval_sets(args.val_per_snr, args.seed + 1, device)
    predict = lambda f, R, s: model(R.to(device).to(torch.complex64), s)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    gen = torch.Generator().manual_seed(args.seed)

    model.eval()
    init = mse_per_snr(predict, val_sets)
    print("Init (= M&M) val MSE/CRB: " + " ".join(f"{s}:{init[s] / crb(s):.2f}" for s in EVAL_SNRS), flush=True)

    best, history = float("inf"), []
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            _, R, y, snr_db = make_batch(args.batch, args.train_snr[0], args.train_snr[1], gen, device)
            pred = model(R.to(device).to(torch.complex64), snr_db)
            c = torch.as_tensor(crb(snr_db.double().cpu().numpy()), dtype=torch.float32, device=device)
            loss = (((pred - y).squeeze(1) * MAX_CFO) ** 2 / c).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            scheduler.step()
            run += loss.item()

        model.eval()
        val = mse_per_snr(predict, val_sets)
        ratios = np.array([val[s] / crb(s) for s in EVAL_SNRS])
        score = ratios.mean()
        history.append((run / args.steps, score))
        marker = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict(),
                        "config": {"arch": args.arch, "hidden": args.hidden, "max_lag": MAX_LAG,
                                   "max_cfo": MAX_CFO, "snr_center": SNR_CENTER, "snr_scale": SNR_SCALE}},
                       args.out)
            marker = " [BEST]"
        print(f"Epoch {epoch:3d}/{args.epochs} | train MSE/CRB {run / args.steps:8.3f} | "
              f"val MSE/CRB mean {score:6.3f} max {ratios.max():6.3f} (@{EVAL_SNRS[ratios.argmax()]} dB) | "
              f"lr {scheduler.get_last_lr()[0]:.2e} | {time.time() - t0:.0f}s{marker}", flush=True)
        if epoch % 10 == 0 or epoch == args.epochs:
            print("   " + " ".join(f"{s}:{r:.2f}" for s, r in zip(EVAL_SNRS, ratios)), flush=True)
    return history


def final_comparison(args, history, device):
    ckpt = torch.load(args.out, map_location=device, weights_only=False)
    model = WeightedPhaseCFOEstimator(hidden=ckpt["config"]["hidden"],
                                      use_features=(ckpt["config"]["arch"] == "wsum")).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

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

    def fusion_predict(f, R, s):
        nn_est, mm_est = f_exp(f), mm_estimate(R).to(device)
        return fusion(torch.cat([nn_est, mm_est], 1), nn_est, mm_est)[0]

    name = f"W-sum ({args.arch})"
    predictors = {
        name: lambda f, R, s: model(R.to(device).to(torch.complex64), s),
        "Expert NN": lambda f, R, s: expert(f),
        "Fusion": fusion_predict,
        "M&M": lambda f, R, s: mm_estimate(R).to(device),
    }
    params = {name: count_params(model), "Expert NN": count_params(expert),
              "Fusion": count_params(f_exp) + count_params(fusion), "M&M": 0}

    # Include the SNR-aware MLP runs if their checkpoints exist
    for tag in args.compare_tags:
        try:
            sck = torch.load(paths.model(f"snr_aware_cfo_model_L64{tag}.pth"), map_location=device, weights_only=False)
        except FileNotFoundError:
            continue
        m = SNRAwareCFOEstimator(hidden=tuple(sck["config"]["hidden"])).to(device)
        m.load_state_dict(sck["state_dict"])
        m.eval()
        predictors[f"SNR-aware MLP{tag}"] = (lambda mm: (lambda f, R, s: mm(f, s)))(m)
        params[f"SNR-aware MLP{tag}"] = count_params(m)

    test_sets = make_eval_sets(args.test_per_snr, args.seed + 2, device)
    mses = {n: mse_per_snr(p, test_sets) for n, p in predictors.items()}

    print("\n" + "=" * 130)
    print(f"TEST: MSE (xCRB), {args.test_per_snr} samples per SNR (true SNR given to SNR-aware models)")
    print("=" * 130)
    print_table("", list(predictors), mses)
    print("\nMean MSE/CRB over SNR and trainable parameters:")
    for n in predictors:
        print(f"  {n:<26} mean {np.mean([mses[n][s] / crb(s) for s in EVAL_SNRS]):6.3f} | params {params[n]:>6}")
    print("TEST DONE", flush=True)

    plt.figure(figsize=(10, 6))
    for n in predictors:
        plt.plot(EVAL_SNRS, [mses[n][s] / crb(s) for s in EVAL_SNRS], marker="o", markersize=4,
                 label=f"{n} ({params[n]} params)")
    plt.axhline(1.0, color="r", linestyle="--", linewidth=2, label="CRB")
    plt.yscale("log")
    plt.xlabel("SNR (dB)")
    plt.ylabel("MSE / CRB")
    plt.title("CFO estimator efficiency: MSE / CRB vs. SNR")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"wsum_{args.arch}_mse_over_crb.png"), dpi=300, bbox_inches="tight")
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
    plt.savefig(paths.plot(f"wsum_{args.arch}_mse_vs_snr.png"), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", choices=["wsum", "wsum-snr"], default="wsum")
    ap.add_argument("--hidden", type=int, default=32)
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=5000)
    ap.add_argument("--test-per-snr", type=int, default=20000)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--compare-tags", nargs="*", default=["", "_lr3e-5"])
    ap.add_argument("--eval-only", action="store_true")
    args = ap.parse_args()
    args.out = paths.model(f"wsum_{args.arch}_cfo_model_L64.pth")
    torch.set_num_threads(args.threads)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    hist = [] if args.eval_only else train(args, device)
    final_comparison(args, hist, device)
