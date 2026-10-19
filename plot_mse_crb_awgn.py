"""
AWGN, 128-symbol known sequence: MSE / CRB (or MSE) vs. Es/N0 (-5 .. 10 dB) of selected estimators,
always through the full Tx/Rx chain of main.py (vectorised):

    QPSK preamble -> upsample x8 -> RRC (beta, span 10) -> CFO per sample (before the matched filter)
    -> AWGN (Es/N0 per symbol, Es measured per frame as main.apply_awgn) -> matched RRC -> remove delay
    -> downsample -> z = r s*

CFO ~ U[-0.2, 0.2], random carrier phase. All estimators see the same frames; the NNs are the trained models
fft_nn_residual_cfo_model_L64.pth (train_fft_nn.py) and snr_aware_cfo_model_L64.pth (train_snr_nn.py), both
given the true SNR.

Usage:
    python plot_mse_crb_awgn.py                 # FFT-aided NN, ML, M&M: MSE/CRB, beta = config.BETA
    python plot_mse_crb_awgn.py --est "SNR-aware NN" "M&M" --metric mse --out mse_snr_aware_vs_mm_awgn.png
    python plot_mse_crb_awgn.py --est "SNR-aware NN" "M&M" --metric mse --beta 0.5 --out mse_snr_aware_vs_mm_awgn_beta0p5.png
    python plot_mse_crb_awgn.py --est "SNR-aware NN" "M&M" --metric outage --out cfo_outage_snr_aware_vs_mm_awgn.png
    python plot_mse_crb_awgn.py --from-npz cfo_outage_snr_aware_vs_mm_awgn.npz --thresholds 1e-3 1e-2 \
        --out cfo_outage_snr_aware_vs_mm_awgn.png       # redraw with other thresholds, no simulation

--metric outage plots P(|CFO error| > threshold) for each --thresholds value; the exceedance counts over a fine
threshold grid are saved next to the plot (.npz) so other thresholds can be drawn without rerunning.
"""

import argparse
import paths
import os
import sys
import time

if "--length" in sys.argv:          # known-sequence length, read by train_snr_nn at import (CRB, lags = L/2)
    os.environ["CFO_EST_LEN"] = sys.argv[sys.argv.index("--length") + 1]

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

import config as cfg
from train_fft_nn import FFTAidedCFOEstimator, fft_features, ml_estimate
from train_snr_nn import EVAL_SNRS, MAX_CFO, PREAMBLE_LENGTH, SNRAwareCFOEstimator, crb, lag_features, mm_estimate

SPS, SPAN = cfg.SPS, cfg.FILTER_SPAN


def chain_batch(B, snr_db, rng, beta, fft=True):
    """B known PREAMBLE_LENGTH-symbol frames through the full Tx/Rx chain (txrx_chain.py), as estimator inputs."""
    from txrx_chain import known_sequence
    z, f = known_sequence(B, PREAMBLE_LENGTH, snr_db, rng, max_cfo=MAX_CFO, beta=beta)
    z = torch.from_numpy(z)
    feats, R = lag_features(z)
    aux, fc = fft_features(z) if fft else (None, None)     # FFT-NN / ML inputs (128-symbol models only)
    return {"feats": feats, "R": R, "aux": aux, "fc": fc, "z": z, "y": torch.from_numpy(f / MAX_CFO)[:, None].float(),
            "snr": torch.full((B,), float(snr_db))}


MODEL = paths.model("fft_nn_residual_cfo_model_L64.pth")
SNR_AWARE = paths.model({128: "snr_aware_cfo_model_L64_chain150.pth",    # full chain (40 + 150 epochs)
                         256: "snr_aware_cfo_model_L128_est256.pth"}.get(PREAMBLE_LENGTH, ""))
STYLE = {"FFT-aided NN": ("#d62728", "o"), "ML (FFT + 2 Newton)": ("#1f77b4", "s"), "M&M": ("#2ca02c", "^"),
         "SNR-aware NN": ("#9467bd", "D")}


def plot_outage(path, thresholds, out, beta, labels=None):
    """Outage P(|error| > threshold) vs. Es/N0 from the saved exceedance counts of a --metric outage run.
    path: one .npz, or a list of them (parts of a run split over Es/N0, merged here)."""
    parts = [np.load(paths.result(p)) for p in ([path] if isinstance(path, str) else path)]
    names = [n for n in STYLE if all(n in q.files for q in parts)]
    order = np.argsort(np.concatenate([q["snr"] for q in parts]))
    d = {"snr": np.concatenate([q["snr"] for q in parts])[order], "grid": parts[0]["grid"],
         "trials": np.concatenate([q["trials"] for q in parts])[order]}
    d.update({n: np.concatenate([q[n] for q in parts])[order] for n in names})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for n in names:
        c, m = STYLE[n]
        for k, (th, ls) in enumerate(zip(thresholds, ["-", "--", ":", "-."])):
            extra = f" ({labels[k]})" if labels and k < len(labels) and labels[k] else ""
            j = int(np.argmin(np.abs(np.log(d["grid"] / th))))
            p = d[n][:, j] / d["trials"]
            ax.semilogy(d["snr"], np.where(p > 0, p, np.nan), color=c, marker=m, markersize=5, linestyle=ls,
                        label=f"{n}, |error| > {th:.1e}{extra}")       # no exceedance observed: point left out
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO outage probability")
    ax.set_xticks(d["snr"])
    ax.set_title(f"CFO outage probability vs. SNR ({PREAMBLE_LENGTH} known symbols, roll-off = {beta:g})")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=8)   # below: off the curves
    fig.tight_layout()
    fig.savefig(paths.plot(out), dpi=300, bbox_inches="tight")
    print(f"saved {out}")


def main(args):
    if args.from_npz:
        return plot_outage(args.from_npz if len(args.from_npz) > 1 else args.from_npz[0], args.thresholds, args.out,
                           args.beta, args.labels)
    torch.manual_seed(args.seed)
    use_fft = any(n in args.est for n in ("FFT-aided NN", "ML (FFT + 2 Newton)"))
    if use_fft and PREAMBLE_LENGTH != 128:
        raise SystemExit("FFT-aided NN / ML are set up for 128 symbols only")
    if PREAMBLE_LENGTH != 128 and not paths.STUDY:
        raise SystemExit("--length != 128: set CFO_STUDY (e.g. est256) so the results stay apart")
    if use_fft:
        ck = torch.load(MODEL, map_location="cpu", weights_only=False)
        model = FFTAidedCFOEstimator(hidden=tuple(ck["config"]["hidden"]), residual=ck["config"]["mode"] == "residual")
        model.load_state_dict(ck["state_dict"])
        model.eval()
    if "SNR-aware NN" in args.est:
        sck = torch.load(args.snr_aware, map_location="cpu", weights_only=False)
        assert sck["config"]["max_lag"] == PREAMBLE_LENGTH // 2, (args.snr_aware, sck["config"]["max_lag"])
        snr_nn = SNRAwareCFOEstimator(max_lag=sck["config"]["max_lag"], hidden=tuple(sck["config"]["hidden"]),
                                      use_snr=sck["config"].get("use_snr", True))
        snr_nn.load_state_dict(sck["state_dict"])
        snr_nn.eval()
    every = {
        "FFT-aided NN": lambda b: model(b["feats"], b["snr"], b["aux"]),
        "ML (FFT + 2 Newton)": lambda b: ml_estimate(b["z"], b["fc"]),
        "M&M": lambda b: mm_estimate(b["R"]),
        "SNR-aware NN": lambda b: snr_nn(b["feats"], b["snr"]),
    }
    predictors = {n: every[n] for n in args.est}
    rng = np.random.default_rng(args.seed)
    ratio = {n: [] for n in predictors}
    grid = np.logspace(-6, -1, 201)                                    # outage thresholds (normalised CFO)
    snrs = args.snrs or EVAL_SNRS                                     # a subset: one part of a split outage run
    if args.metric != "outage" and snrs != EVAL_SNRS:
        raise SystemExit("--snrs only with --metric outage")
    exceed = {n: np.zeros((len(snrs), len(grid))) for n in predictors}
    n_trials = []
    trials_at = [args.trials_low if s <= -3 else args.trials for s in snrs]   # heavy tail below threshold
    total, done, t0 = sum(t // args.chunk for t in trials_at), 0, time.time()
    with torch.no_grad():
        for i, s in enumerate(snrs):
            se = {n: 0.0 for n in predictors}
            nc = trials_at[i] // args.chunk
            for _ in range(nc):
                b = chain_batch(args.chunk, s, rng, args.beta, fft=use_fft)
                for n, p in predictors.items():
                    e = ((p(b) - b["y"]).double() * MAX_CFO).numpy().ravel()
                    se[n] += float((e ** 2).sum())
                    exceed[n][i] += len(e) - np.searchsorted(np.sort(np.abs(e)), grid, side="right")
                done += 1
                if args.progress:
                    with open(paths.log(args.progress), "a") as fp:
                        fp.write(f"{done} {total} {time.time() - t0:.0f}\n")
            n_trials.append(nc * args.chunk)
            for n in predictors:
                mse = se[n] / n_trials[-1]
                ratio[n].append(mse / crb(s) if args.metric == "ratio" else mse)
            print(f"Es/N0 {s:3d} dB | " + " | ".join(f"{n} {ratio[n][-1]:.4g}" for n in predictors), flush=True)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    if args.metric == "outage":
        npz = paths.result(os.path.splitext(os.path.basename(args.out))[0] + ".npz")
        np.savez(npz, snr=snrs, grid=grid, trials=n_trials, **{n: exceed[n] for n in predictors})
        plt.close(fig)
        plot_outage(npz, args.thresholds, args.out, args.beta)
        print("EVAL DONE", flush=True)
        return
    else:
        for n in predictors:
            c, m = STYLE[n]
            ax.semilogy(EVAL_SNRS, ratio[n], color=c, marker=m, markersize=5, label=n)
        if args.metric == "mse":                  # CRB only on the MSE plot (on MSE/CRB it would be the line at 1)
            ax.semilogy(EVAL_SNRS, [crb(s) for s in EVAL_SNRS], "k:", linewidth=1.8, label="CRB")
        ax.set_ylabel("CFO MSE / CRB" if args.metric == "ratio" else "CFO MSE")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_xticks(EVAL_SNRS)
    ax.set_title(f"CFO estimation (roll-off = {args.beta:g})")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(paths.plot(args.out), dpi=300, bbox_inches="tight")
    print(f"saved {args.out}")
    print("EVAL DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=100000, help="sequences per Es/N0")
    ap.add_argument("--trials-low", type=int, default=1000000,
                    help="sequences per Es/N0 at <= -3 dB (rare outliers dominate the MSE there)")
    ap.add_argument("--chunk", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="mse_over_crb_awgn.png")
    ap.add_argument("--est", nargs="+", default=["FFT-aided NN", "ML (FFT + 2 Newton)", "M&M"],
                    choices=["FFT-aided NN", "ML (FFT + 2 Newton)", "M&M", "SNR-aware NN"])
    ap.add_argument("--metric", choices=["ratio", "mse", "outage"], default="ratio",
                    help="MSE/CRB, plain MSE, or outage probability P(|error| > threshold)")
    ap.add_argument("--thresholds", type=float, nargs="+", default=[3e-4, 1e-3],
                    help="--metric outage: CFO error thresholds (normalised to the symbol rate); below ~1e-3 "
                         "the outage is just the Gaussian spread (CRB std ~5e-4 at -5 dB), not breakdown")
    ap.add_argument("--length", type=int, default=128,
                    help="known symbols per estimate (SNR-aware NN and M&M only for != 128; needs CFO_STUDY)")
    ap.add_argument("--labels", nargs="+", default=None,
                    help="--metric outage: legend note per threshold, e.g. 'R=1/2 tolerance' ('' for none)")
    ap.add_argument("--snrs", type=int, nargs="+", default=None, help="--metric outage: only these Es/N0 (split runs)")
    ap.add_argument("--from-npz", nargs="+", default=None, help="redraw an outage plot from saved counts (no simulation)")
    ap.add_argument("--progress", default=None, help="append 'done total elapsed_s' per chunk (job_progress.py)")
    ap.add_argument("--beta", type=float, default=cfg.BETA, help="RRC roll-off of the Tx/Rx chain")
    ap.add_argument("--snr-aware", default=SNR_AWARE, help="SNR-aware NN checkpoint")
    main(ap.parse_args())
