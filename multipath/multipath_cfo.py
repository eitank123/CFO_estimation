"""
CFO estimation under multipath vs. AWGN, for a 128-symbol and a 512-symbol known sequence.

Channel (symbol-spaced, block fading: one channel realisation per sequence):

    r[n] = exp(j(2 pi f n + phi)) * sum_k h_k s[n-k] + w[n],   n = 0 .. L-1

    --channel awgn       h = [1]                       (exactly the model of the main AWGN study)
    --channel multipath  3 taps, power-delay profile 0 / -3 / -6 dB, Rayleigh taps,
                         E[sum |h_k|^2] = 1, so Es/N0 is the average received SNR

The estimators use z[n] = r[n] s*[n] with the known sequence s, as in the AWGN study, so the
delayed taps act as interference (ISI) and the channel gain h_0 fades.

Estimators:
    M&M                       M = L/2 lags
    ML                        FFT (K = 2L) peak + 2 Newton steps
    FFT-NN (AWGN-trained)     the models of the main study (L=128: fft_nn_residual_cfo_model_L64.pth,
                              L=512: fft_nn_residual_cfo_model_seq512.pth)
    FFT-NN (channel-trained)  same architecture, fine-tuned on this channel (initialised from the AWGN model)

Everything is written to multipath/results_<channel>/; the AWGN study in the main folder is not
touched. Switching back to AWGN is just --channel awgn (or running the main-folder scripts).

Usage (from the project folder):
    python multipath/multipath_cfo.py --channel multipath            # train both lengths + evaluate
    python multipath/multipath_cfo.py --channel multipath --eval-only
    python multipath/multipath_cfo.py --channel awgn --eval-only     # same evaluation on AWGN
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from train_fft_nn import ml_estimate
from train_fft_nn_long import FFTAidedCFOEstimatorK, crb, features, load_fft_nn, mm_cfo
from train_snr_nn import MAX_CFO

CHANNELS = {
    "awgn": {"taps_db": [0.0], "fading": False},
    "multipath": {"taps_db": [0.0, -3.0, -6.0], "fading": True},
}
LENGTHS = (128, 512)
AWGN_MODELS = {128: os.path.join(ROOT, "models", "fft_nn_residual_cfo_model_L64.pth"),
               512: os.path.join(ROOT, "models", "fft_nn_residual_cfo_model_seq512.pth")}
EVAL_SNRS = list(range(-5, 11))
OUTAGE = 1e-4      # |CFO error| above which a 512-symbol coded packet starts to fail (main study)


# =====================================================================
# Channel
# =====================================================================

def make_batch(batch, L, snr_low, snr_high, gen, channel, fixed_snr=None, return_rs=False):
    """
    Returns z = r * conj(s) (B, L) complex128, normalised CFO y (B, 1) and SNR in dB (B,).
    return_rs: return the received r (B, L) and the known symbols s (B, L) instead of z.
    """
    cfg = CHANNELS[channel]
    p = 10.0 ** (np.asarray(cfg["taps_db"]) / 10.0)
    p = torch.as_tensor(p / p.sum(), dtype=torch.float64)
    n_taps = len(p)

    bits = torch.randint(0, 2, (batch, L + n_taps - 1, 2), generator=gen).double()
    s = ((1 - 2 * bits[..., 0]) + 1j * (1 - 2 * bits[..., 1])) / np.sqrt(2)     # leading symbols = previous data
    if cfg["fading"]:
        h = torch.complex(torch.randn(batch, n_taps, generator=gen, dtype=torch.float64),
                          torch.randn(batch, n_taps, generator=gen, dtype=torch.float64)) * torch.sqrt(p / 2)
    else:
        h = torch.sqrt(p).to(torch.complex128).expand(batch, n_taps)
    rx = sum(h[:, k:k + 1] * s[:, n_taps - 1 - k: n_taps - 1 - k + L] for k in range(n_taps))
    known = s[:, n_taps - 1:]                                                    # the L known symbols

    y = torch.rand(batch, 1, generator=gen, dtype=torch.float64) * 2 - 1
    snr = (torch.full((batch,), float(fixed_snr), dtype=torch.float64) if fixed_snr is not None else
           torch.rand(batch, generator=gen, dtype=torch.float64) * (snr_high - snr_low) + snr_low)
    n = torch.arange(L, dtype=torch.float64)
    phase = torch.rand(batch, 1, generator=gen, dtype=torch.float64) * 2 * np.pi
    std = torch.sqrt(1.0 / (2.0 * 10.0 ** (snr / 10.0))).unsqueeze(1)
    r = rx * torch.exp(1j * (2 * np.pi * y * MAX_CFO * n + phase)) + std * torch.complex(
        torch.randn(batch, L, generator=gen, dtype=torch.float64),
        torch.randn(batch, L, generator=gen, dtype=torch.float64))
    if return_rs:
        return r, known, y, snr
    return r * known.conj(), y, snr


# =====================================================================
# Training (fine-tune the AWGN FFT-NN on this channel)
# =====================================================================

def train(args, L, epoch_offset, total_epochs, out_path, log):
    torch.manual_seed(args.seed + L)
    model, k = load_fft_nn(AWGN_MODELS[L])
    model.train()
    vgen = torch.Generator().manual_seed(args.seed + 1)
    val = {s: make_batch(args.val_per_snr, L, s, s, vgen, args.channel, fixed_snr=s) for s in (-5, 0, 5, 10)}
    val = {s: (*features(z, k), y.float(), snr.float()) for s, (z, y, snr) in val.items()}
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-2)
    gen = torch.Generator().manual_seed(args.seed + 10 * L)
    best = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            z, y, snr = make_batch(args.batch, L, args.train_snr[0], args.train_snr[1], gen, args.channel)
            f, a, _ = features(z, k)
            pred = model(f, snr.float(), a)
            c = torch.as_tensor(crb(snr.numpy(), L), dtype=torch.float32)
            # log-compressed loss: deep fades give errors >> CRB that would otherwise dominate the gradient
            loss = torch.log1p((((pred - y.float()).squeeze(1) * MAX_CFO) ** 2 / c)).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += loss.item()
        model.eval()
        with torch.no_grad():
            # median |error|: the RMSE is dominated by deep-fade outliers that no estimator can fix
            rm = [float(((model(f, s, a) - y) * MAX_CFO).abs().median()) for f, a, _, y, s in val.values()]
        score = float(np.mean(np.log(rm)))
        mark = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict(),
                        "config": {"mode": "residual", "hidden": [128, 64, 32], "fft_k": k, "length": L,
                                   "channel": args.channel, "max_cfo": MAX_CFO}}, out_path)
            mark = " [BEST]"
        log(f"Epoch {epoch_offset + epoch:3d}/{total_epochs} | L={L} | train loss {run / args.steps:.3f} | "
            f"val median |err| @-5/0/5/10 dB " + " ".join(f"{v:.2e}" for v in rm) + f" | {time.time() - t0:.0f}s{mark}")


# =====================================================================
# Evaluation
# =====================================================================

@torch.no_grad()
def evaluate(args, out_dir, log):
    names = ["M&M", "ML", "FFT-NN (AWGN-trained)", "FFT-NN (channel-trained)"]
    res = {}   # (name, L) -> {"rmse": [...], "outage": [...]}
    gen = torch.Generator().manual_seed(args.seed + 2)
    for L in LENGTHS:
        awgn_nn, k = load_fft_nn(AWGN_MODELS[L])
        ch_path = os.path.join(out_dir, f"fft_nn_{args.channel}_seq{L}.pth")
        ch_nn = load_fft_nn(ch_path)[0] if os.path.exists(ch_path) else None
        for nm in names:
            res[(nm, L)] = {"rmse": [], "median": [], "outage": []}
        for s in EVAL_SNRS:
            z, y, snr = make_batch(args.test_per_snr, L, s, s, gen, args.channel, fixed_snr=s)
            f, a, fc = features(z, k)
            est = {"M&M": mm_cfo(z).float(), "ML": ml_estimate(z, fc),
                   "FFT-NN (AWGN-trained)": awgn_nn(f, snr.float(), a)}
            if ch_nn is not None:
                est["FFT-NN (channel-trained)"] = ch_nn(f, snr.float(), a)
            for nm in names:
                if nm not in est:
                    continue
                e = ((est[nm] - y.float()) * MAX_CFO).squeeze(1).double().numpy()
                res[(nm, L)]["rmse"].append(float(np.sqrt(np.mean(e ** 2))))
                res[(nm, L)]["median"].append(float(np.median(np.abs(e))))
                res[(nm, L)]["outage"].append(float(np.mean(np.abs(e) > OUTAGE)))
        log(f"evaluated L={L}")

    log(f"\nChannel: {args.channel} {CHANNELS[args.channel]}, {args.test_per_snr} sequences per Es/N0")
    for L in LENGTHS:
        log(f"\nL = {L}: CFO RMSE | median |error| | P(|error| > {OUTAGE:g})   (cycles/symbol)")
        cols = [nm for nm in names if res[(nm, L)]["rmse"]]
        log(f"{'Es/N0':>5} | " + " | ".join(f"{nm:>34}" for nm in cols) + f" | {'sqrt(CRB)':>9}")
        for i, s in enumerate(EVAL_SNRS):
            log(f"{s:5d} | " + " | ".join(
                f"{res[(nm, L)]['rmse'][i]:.2e} | {res[(nm, L)]['median'][i]:.2e} | {res[(nm, L)]['outage'][i]:5.3f}".rjust(34)
                for nm in cols) + f" | {np.sqrt(crb(s, L)):.2e}")
    np.save(os.path.join(out_dir, "cfo_results.npy"), {"res": res, "snrs": EVAL_SNRS, "channel": args.channel},
            allow_pickle=True)
    plot(res, args.channel, out_dir)
    log("EVAL DONE")


def plot(res, channel, out_dir):
    style = {"M&M": ("#ff7f0e", "d"), "ML": ("#2ca02c", "o"),
             "FFT-NN (AWGN-trained)": ("#9467bd", "s"), "FFT-NN (channel-trained)": ("#d62728", "^")}
    for metric, ylabel, fname in (("rmse", "CFO RMSE (cycles/symbol)", "cfo_rmse"),
                                  ("median", "Median |CFO error| (cycles/symbol)", "cfo_median"),
                                  ("outage", f"P(|CFO error| > {OUTAGE:g})", "cfo_outage")):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
        for ax, L in zip(axes, LENGTHS):
            for nm, (c, m) in style.items():
                v = res[(nm, L)][metric]
                if v:
                    ax.semilogy(EVAL_SNRS, v, "-", color=c, marker=m, markersize=4, label=nm)
            if metric in ("rmse", "median"):
                ax.semilogy(EVAL_SNRS, np.sqrt(crb(EVAL_SNRS, L)), "k--", linewidth=1, label="sqrt(CRB), AWGN")
            ax.set_title(f"{L}-symbol sequence")
            ax.set_xlabel("Es/N0 [dB] (average)")
            ax.grid(True, which="both", linestyle=":", alpha=0.6)
        axes[0].set_ylabel(ylabel)
        axes[0].legend(fontsize=9)
        fig.suptitle(f"CFO estimation, {channel} channel")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"{fname}_{channel}.png"), dpi=300, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", choices=list(CHANNELS), default="multipath")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--steps", type=int, default=150)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=4000)
    ap.add_argument("--test-per-snr", type=int, default=20000)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--eval-only", action="store_true")
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    out_dir = os.path.join(HERE, f"results_{args.channel}")
    os.makedirs(out_dir, exist_ok=True)
    log_file = open(os.path.join(out_dir, "run.log"), "a" if args.eval_only else "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        log_file.write(msg + "\n")
        log_file.flush()

    if not args.eval_only and args.channel != "awgn":
        total = args.epochs * len(LENGTHS)
        for i, L in enumerate(LENGTHS):
            train(args, L, i * args.epochs, total, os.path.join(out_dir, f"fft_nn_{args.channel}_seq{L}.pth"), log)
    evaluate(args, out_dir, log)
