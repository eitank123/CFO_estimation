"""
FFT-aided NN and M&M on a longer known sequence (default L = 512: the whole polar packet).

Same estimator structure as train_fft_nn.py, generalised to any L:
    FFT-aided NN : 64 lag correlations over L symbols + SNR + 8 periodogram-peak features
                   (FFT K = 2L), output = FFT-peak frequency + bin * MLP(...).
                   Initialised from the L = 128 model: with K = 2L the bin-relative features
                   have the same meaning, so training starts close to a good solution.
    M&M          : M = L/2 lag correlations (the optimum in Mengali & Morelli).
    ML           : FFT (K = 2L) peak + 2 Newton steps (reference).
Loss = squared CFO error / CRB(SNR, L), CFO ~ U[-0.2, 0.2], symbol-rate AWGN model.

Outputs: fft_nn_residual_cfo_model_seq<L>.pth, cfo_accuracy_L128_vs_L<L>.png (CFO RMSE vs. Es/N0
for both lengths), training log and a complexity table.

Usage:
    python train_fft_nn_long.py --length 512 --epochs 60
"""

import argparse
import paths
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from train_fft_nn import FFTAidedCFOEstimator, N_AUX, fft_features, ml_estimate
from train_snr_nn import MAX_CFO, MAX_LAG, lag_features, mm_estimate

EVAL_SNRS = list(range(-5, 11))
SHORT_PATH = paths.model("fft_nn_residual_cfo_model_L64.pth")    # L = 128 model (64 lags)


def crb(snr_db, L):
    snr = 10.0 ** (np.asarray(snr_db, dtype=float) / 10.0)
    return 3.0 / (2.0 * np.pi ** 2 * snr * L * (L ** 2 - 1))


class FFTAidedCFOEstimatorK(FFTAidedCFOEstimator):
    """FFTAidedCFOEstimator with the FFT size as a parameter (the parent uses K = 256)."""

    def __init__(self, fft_k, **kw):
        super().__init__(**kw)
        self.bin = 1.0 / (fft_k * MAX_CFO)              # one FFT bin in normalised-CFO units

    def forward(self, x, snr_db, aux):
        from train_snr_nn import SNR_CENTER, SNR_SCALE
        s = (snr_db.view(-1, 1) - SNR_CENTER) / SNR_SCALE
        out = self.net(torch.cat([x.flatten(1), s, aux], dim=1))
        return aux[:, :1] + self.bin * out if self.residual else out


def load_fft_nn(path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    k = ck["config"].get("fft_k", 256)
    model = FFTAidedCFOEstimatorK(k, hidden=tuple(ck["config"]["hidden"]),
                                  residual=(ck["config"]["mode"] == "residual"))
    model.load_state_dict(ck["state_dict"])
    model.eval()
    return model, k


# =====================================================================
# Data and estimators for any L
# =====================================================================

def make_z(batch, L, snr_low, snr_high, gen, fixed_snr=None):
    """z[n] = exp(j(2 pi f n + phi)) + w[n]  (r[n] s*[n] with the symbols removed)."""
    y = torch.rand(batch, 1, generator=gen, dtype=torch.float64) * 2 - 1
    snr = (torch.full((batch,), float(fixed_snr), dtype=torch.float64) if fixed_snr is not None else
           torch.rand(batch, generator=gen, dtype=torch.float64) * (snr_high - snr_low) + snr_low)
    std = torch.sqrt(1.0 / (2.0 * 10.0 ** (snr / 10.0))).unsqueeze(1)
    n = torch.arange(L, dtype=torch.float64)
    phase = torch.rand(batch, 1, generator=gen, dtype=torch.float64) * 2 * np.pi
    z = torch.exp(1j * (2 * np.pi * y * MAX_CFO * n + phase)) + std * torch.complex(
        torch.randn(batch, L, generator=gen, dtype=torch.float64),
        torch.randn(batch, L, generator=gen, dtype=torch.float64))
    return z, y, snr


def lag_corr(z, M):
    """R(m) = mean_n z[n] z*[n-m], m = 1..M, via an FFT autocorrelation. (B, M) complex."""
    L = z.shape[1]
    Z = torch.fft.fft(z, n=2 * L)
    acf = torch.fft.ifft(Z * Z.conj())[:, 1:M + 1]
    return acf / torch.arange(L - 1, L - M - 1, -1, dtype=torch.float64)


def mm_cfo(z):
    """M&M with M = L/2, normalised CFO (B, 1)."""
    L = z.shape[1]
    return mm_estimate(lag_corr(z, L // 2), L=L)


def features(z, k):
    feats, _ = lag_features(z)            # 64 lags, any L
    aux, fc = fft_features(z, K=k)
    return feats, aux, fc


# =====================================================================
# Complexity (real MACs per estimate, direct lag correlations as in train_fft_nn.py)
# =====================================================================

def complexity(L, model):
    k = 2 * L
    mlp = sum(m.in_features * m.out_features for m in model.modules() if isinstance(m, torch.nn.Linear))
    fft = (k // 2) * int(np.log2(k))
    lag64 = sum(L - m for m in range(1, MAX_LAG + 1))
    lag_mm = sum(L - m for m in range(1, L // 2 + 1))
    return {
        "M&M": 4 * lag_mm + 4 * (L // 2),
        "M&M (FFT autocorr.)": 4 * 2 * fft + 4 * (L // 2),
        "ML": 4 * (fft + 6 * L),
        "FFT-aided NN": 4 * (lag64 + fft) + mlp,
    }


# =====================================================================
# Train
# =====================================================================

def train(args):
    torch.manual_seed(args.seed)
    k = 2 * args.length
    model = FFTAidedCFOEstimatorK(k, residual=True)
    model.load_state_dict(torch.load(SHORT_PATH, map_location="cpu", weights_only=False)["state_dict"])
    print(f"L = {args.length}, FFT K = {k}, initialised from {SHORT_PATH}", flush=True)

    vgen = torch.Generator().manual_seed(args.seed + 1)
    val = {}
    for s in EVAL_SNRS:
        z, y, snr = make_z(args.val_per_snr, args.length, s, s, vgen, fixed_snr=s)
        val[s] = (*features(z, k), y.float(), snr.float())

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    gen = torch.Generator().manual_seed(args.seed)
    best = float("inf")

    def val_ratios():
        model.eval()
        with torch.no_grad():
            r = [float((((model(f, s, a) - y) * MAX_CFO) ** 2).mean()) / crb(snr_db, args.length)
                 for snr_db, (f, a, _, y, s) in val.items()]
        return np.array(r)

    r0 = val_ratios()
    print(f"Epoch   0 | val MSE/CRB mean {r0.mean():6.3f} (L=128 weights, no training)", flush=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            z, y, snr = make_z(args.batch, args.length, args.train_snr[0], args.train_snr[1], gen)
            f, a, _ = features(z, k)
            pred = model(f, snr.float(), a)
            c = torch.as_tensor(crb(snr.numpy(), args.length), dtype=torch.float32)
            loss = (((pred - y.float()).squeeze(1) * MAX_CFO) ** 2 / c).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += loss.item()
        r = val_ratios()
        mark = ""
        if r.mean() < best:
            best = r.mean()
            torch.save({"state_dict": model.state_dict(),
                        "config": {"mode": "residual", "hidden": [128, 64, 32], "fft_k": k, "length": args.length,
                                   "max_lag": MAX_LAG, "max_cfo": MAX_CFO, "train_snr": list(args.train_snr)}},
                       args.out)
            mark = " [BEST]"
        print(f"Epoch {epoch:3d}/{args.epochs} | train MSE/CRB {run / args.steps:7.3f} | val MSE/CRB mean "
              f"{r.mean():6.3f} max {r.max():6.3f} (@{EVAL_SNRS[r.argmax()]} dB) | {time.time() - t0:.0f}s{mark}",
              flush=True)


# =====================================================================
# Evaluate: CFO accuracy at L = 128 and L = 512, complexity
# =====================================================================

@torch.no_grad()
def evaluate(args):
    long_nn, k_long = load_fft_nn(args.out)
    short_nn, k_short = load_fft_nn(SHORT_PATH)
    gen = torch.Generator().manual_seed(args.seed + 2)
    rmse = {}
    for L, nn_model, k in ((128, short_nn, k_short), (args.length, long_nn, k_long)):
        for name in ("M&M", "ML", "FFT-aided NN"):
            rmse[(name, L)] = []
        for s in EVAL_SNRS:
            z, y, snr = make_z(args.test_per_snr, L, s, s, gen, fixed_snr=s)
            f, a, fc = features(z, k)
            est = {"M&M": mm_cfo(z).float(), "ML": ml_estimate(z, fc), "FFT-aided NN": nn_model(f, snr.float(), a)}
            for name, e in est.items():
                rmse[(name, L)].append(float(torch.sqrt((((e - y.float()) * MAX_CFO) ** 2).mean())))

    print("\nCFO RMSE (cycles/symbol), MSE/CRB in brackets, "
          f"{args.test_per_snr} sequences per Es/N0")
    cols = [(n, L) for L in (128, args.length) for n in ("M&M", "ML", "FFT-aided NN")]
    print(f"{'Es/N0':>5} | " + " | ".join(f"{n + ' L=' + str(L):>22}" for n, L in cols))
    for i, s in enumerate(EVAL_SNRS):
        print(f"{s:5d} | " + " | ".join(
            f"{rmse[c][i]:.2e} ({rmse[c][i] ** 2 / crb(s, c[1]):5.2f})".rjust(22) for c in cols))

    print("\nComplexity (real MACs per estimate; lag correlations computed directly, as in train_fft_nn.py)")
    for L, m in ((128, short_nn), (args.length, long_nn)):
        print(f"  L = {L}: " + " | ".join(f"{n} {v:,}" for n, v in complexity(L, m).items()))

    colors = {"M&M": "#ff7f0e", "ML": "#2ca02c", "FFT-aided NN": "#9467bd"}
    markers = {"M&M": "d", "ML": "o", "FFT-aided NN": "s"}
    plt.figure(figsize=(10, 6))
    for (name, L), v in rmse.items():
        plt.semilogy(EVAL_SNRS, v, "-" if L == args.length else "--", color=colors[name], marker=markers[name],
                     markersize=4, label=f"{name}, L={L}")
    for L, ls in ((128, "--"), (args.length, "-")):
        plt.semilogy(EVAL_SNRS, np.sqrt(crb(EVAL_SNRS, L)), ls, color="k", linewidth=1, label=f"sqrt(CRB), L={L}")
    plt.xlabel("Es/N0 [dB]")
    plt.ylabel("CFO RMSE (cycles/symbol)")
    plt.title(f"CFO estimation error: 128-symbol sequence vs. whole {args.length}-symbol packet")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(paths.plot(f"cfo_accuracy_L128_vs_L{args.length}.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--length", type=int, default=512)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=4000)
    ap.add_argument("--test-per-snr", type=int, default=20000)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--eval-only", action="store_true")
    args = ap.parse_args()
    args.out = paths.model(f"fft_nn_residual_cfo_model_seq{args.length}.pth")
    torch.set_num_threads(args.threads)
    if not args.eval_only:
        train(args)
    evaluate(args)
