"""
CFO outage probability P(|CFO error| > threshold) of the split-pilot NN (models/cfo_split_nn_L1024.pth, quarter
layout, 1024-symbol packet) against M&M on 128 contiguous pilots, full Tx/Rx chain. The split-pilot ML is evaluated
on the NN's frames as a reference.

Thresholds: 3e-4 and 1e-3 (the standard outage plot) and 1.0e-4, the CFO-error tolerance of the 1024-symbol
R = 1/10 CRC-16 code (the error where its BLER doubles, at BLER(0) ~ 1e-2; polar_bler_vs_cfo_error_search_step_L1024).
Per SNR: 1e6 frames at <= -3 dB, 1e5 above (as the MSE runs).

    python cfo_outage_split.py --snrs -5 --part a      # -> logs/cfo_outage_split_a.json (one part per job)
    python cfo_outage_split.py --merge                 # parts -> logs/cfo_outage_split.json
    python cfo_outage_split.py --plot           # -> plots/outage/cfo_outage_split_nn_vs_mm_L1024.png
"""
import argparse
import json
import multiprocessing as mp
import os
import time

os.environ["CFO_PILOTS"] = "quarter"          # train_cfo_v3 reads the pilot layout at import

import numpy as np

import paths

SNRS = [-5, -4, -3, -2, -1, 0, 2, 5, 10]
N_SYM = 1024
THRESHOLDS = [1.0e-4, 3e-4, 1e-3]
TOLERANCE = 1.0e-4                            # the R = 1/10 CRC-16 code's tolerance at 1024 symbols
CHUNK, BATCH = 10000, 500
OUT = "cfo_outage_split.json"
EST = ("split NN", "split ML", "M&M")


def _work(task):
    snr, seed = task
    import torch
    torch.set_num_threads(1)
    from train_cfo_split_nn import gen, load_best
    from train_cfo_v3 import split_ml
    from train_snr_nn import MAX_CFO, lag_features, make_z, mm_estimate
    model = load_best(N_SYM)
    rng = np.random.default_rng(seed)
    g = torch.Generator().manual_seed(seed)
    cnt = {k: np.zeros(len(THRESHOLDS), int) for k in EST}
    with torch.no_grad():
        for _ in range(CHUNK // BATCH):
            z, f, s = gen(BATCH, N_SYM, snr, snr, rng, snr)                      # split pilots, 1024 symbols
            e_nn = model(torch.from_numpy(z), torch.from_numpy(s))[0].numpy() - f
            e_ml = split_ml(z.astype(np.complex128), N_SYM, "quarter")[0].numpy() - f
            zc, y, _ = make_z(BATCH, snr, snr, g, snr)                          # 128 contiguous pilots
            e_mm = ((mm_estimate(lag_features(zc)[1]).double()[:, 0] - y[:, 0]) * MAX_CFO).numpy()
            for k, e in (("split NN", e_nn), ("split ML", e_ml), ("M&M", e_mm)):
                cnt[k] += (np.abs(e)[:, None] > np.array(THRESHOLDS)).sum(0)
    return snr, cnt


def run(workers, snrs, part):
    tasks = [(s, 900000 + 1000 * (s + 10) + i) for s in snrs for i in range((1000000 if s <= -3 else 100000) // CHUNK)]
    acc = {s: {k: np.zeros(len(THRESHOLDS), int) for k in EST} for s in snrs}
    n = {s: 0 for s in snrs}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for k, (s, cnt) in enumerate(pool.imap_unordered(_work, tasks), 1):
            for e in EST:
                acc[s][e] += cnt[e]
            n[s] += CHUNK
            with open(paths.log(f"cfo_outage_split_{part}.progress"), "a") as fh:
                fh.write(f"{k} {len(tasks)} {time.time() - t0:.0f}\n")
    out = {"snr": snrs, "thresholds": THRESHOLDS, "n": [n[s] for s in snrs],
           "count": {e: [[int(acc[s][e][j]) for s in snrs] for j in range(len(THRESHOLDS))] for e in EST}}
    out["outage"] = {e: [[c / m for c, m in zip(row, out["n"])] for row in out["count"][e]] for e in EST}
    json.dump(out, open(paths.log(f"cfo_outage_split_{part}.json"), "w"), indent=1)
    for e in EST:
        for j, t in enumerate(THRESHOLDS):
            print(f"{e:9s} P(|e| > {t:.1e}): " + " ".join(f"{v:.2e}" for v in out["outage"][e][j]), flush=True)
    print("EVAL DONE", flush=True)


def merge():
    """The part files -> logs/cfo_outage_split.json, SNRs in order."""
    import glob
    parts = [json.load(open(f)) for f in sorted(glob.glob(paths.log("cfo_outage_split_*.json")))]
    rows = sorted((s, p, i) for p in parts for i, s in enumerate(p["snr"]))
    out = {"snr": [s for s, _, _ in rows], "thresholds": THRESHOLDS, "n": [p["n"][i] for _, p, i in rows],
           "outage": {e: [[p["outage"][e][j][i] for _, p, i in rows] for j in range(len(THRESHOLDS))] for e in EST}}
    json.dump(out, open(paths.log(OUT), "w"), indent=1)
    print(f"merged {len(parts)} parts: SNRs {out['snr']}")


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import config as cfg
    d = json.load(open(paths.log(OUT)))
    snr = np.array(d["snr"], float)
    floor = 1.0 / np.array(d["n"], float)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    j = [abs(t - TOLERANCE) < 1e-12 for t in d["thresholds"]].index(True)   # only the code's tolerance
    for e, c, mk, ls, lab in (("M&M", "#ff7f0e", "d", "-.", "M&M (128 contiguous pilots)"),
                              ("split NN", "#17becf", "h", "-", "Split pilots NN")):
        y = np.array(d["outage"][e][j])
        ax.semilogy(snr, np.where(y > 0, y, np.nan), ls=ls, color=c, marker=mk, lw=2.2, ms=5, label=lab)
        zero = y == 0                           # no outage observed: Monte-Carlo resolution (not in the legend)
        if zero.any():
            ax.semilogy(snr[zero], floor[zero], "v", color=c, markerfacecolor="none", ms=6)
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO outage probability")
    ax.set_title(f"CFO outage probability vs. SNR (128 known symbols, roll-off = {cfg.BETA:g})", fontsize=13)
    ax.text(0.99, 0.97, f"outage: |CFO error| > {TOLERANCE:.1e} (R=1/10 tolerance)", transform=ax.transAxes,
            ha="right", va="top", fontsize=10, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    fig.text(0.5, 0.005, f"{N_SYM}-symbol packet; split pilots: two 64-symbol blocks centred at N/4 and 3N/4. "
             "Open triangles: no outage in the frames simulated (upper bound 1/frames).", ha="center", fontsize=9,
             color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = paths.plot("cfo_outage_split_nn_vs_mm_L1024.png")
    fig.savefig(out, dpi=300)
    print("saved", out)


def plot_tolerance():
    """Why the threshold is 1.0e-4: BLER vs CFO error of the 1024-symbol R = 1/10 CRC-16 code
    (lowrate/results/polar_results_error_chain_L1024_err1024.npy); the tolerance is the error where the BLER doubles."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = list(np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lowrate", "results",
                                  "polar_results_error_chain_L1024_err1024.npy"), allow_pickle=True))
    fig, ax = plt.subplots(figsize=(11, 6.5))
    tols = []
    for s, c in ((-5.5, "#2ca02c"), (-4.5, "#d62728")):
        p = sorted((float(x["src"]), x["bler"], x["frame_err"]) for x in r if abs(x["esn0"] - s) < 0.01)
        e, b, k = (np.array(v, float) for v in zip(*p))
        b0, pos = b[e == 0][0], e > 0
        tol = float(np.exp(np.interp(np.log(2), np.log(b[pos] / b0), np.log(e[pos]))))
        tols.append(tol)
        ax.errorbar(e[pos], b[pos], yerr=b[pos] * 1.96 / np.sqrt(np.maximum(k[pos], 1)), fmt="-o", color=c, ms=5,
                    lw=2, capsize=3, label=f"SNR = {s:g} dB: BLER doubles at {tol:.2e}")
        ax.axhline(b0, color=c, ls=":", lw=1.3, label=f"SNR = {s:g} dB, no CFO error ({b0:.1e})")
        ax.axhline(2 * b0, color=c, ls="--", lw=1.0, alpha=0.6)
        ax.plot([tol], [2 * b0], "D", color=c, ms=8, markeredgecolor="k")
    ax.axvline(TOLERANCE, color="0.2", ls="-.", lw=1.4)
    ax.text(TOLERANCE * 0.95, 0.3, f"tolerance {TOLERANCE:.1e}\n(BLER × 2 at BLER(0) ≈ 1e-2)", fontsize=10,
            color="0.2", ha="right")
    ax.set(xscale="log", yscale="log", xlabel="|CFO error| (cycles/symbol)", ylabel="BLER")
    fig.suptitle("Why the outage threshold is 1.0e-4", fontsize=15, fontweight="bold")
    ax.set_title(f"{N_SYM}-symbol packet, R = 1/10, CRC-16, CA-SCL L = 8; dotted: no CFO error, dashed: twice that, "
                 "◆: BLER doubles", fontsize=10.5, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    fig.tight_layout()
    out = paths.plot("cfo_outage_threshold_tolerance_L1024.png")
    fig.savefig(out, dpi=300)
    print("saved", out, "tolerances", [f"{t:.2e}" for t in tols])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--snrs", type=int, nargs="+", default=SNRS)
    ap.add_argument("--part", default="all")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--plot-tolerance", action="store_true")
    a = ap.parse_args()
    if a.plot_tolerance:
        plot_tolerance()
        raise SystemExit
    if a.merge:
        merge()
    plot() if a.plot or a.merge else run(a.workers, a.snrs, a.part)
