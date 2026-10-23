"""
CFO MSE of the split-pilot ML estimator (quarter layout, train_cfo_v3.py) on the full Tx/Rx chain, 512- and
1024-symbol packets, for the CFO MSE vs SNR figure next to NN v2 and M&M (contiguous 128 pilots, from
logs/cfo_v2_light32_test.json).

Per SNR: 1e6 frames at <= -3 dB, 1e5 above (as the NN v2 test). Statistics: MSE over all frames, the wrong-lobe
rate (|error| > half a lobe spacing) and the fine MSE over the frames on the right lobe.

    CFO_PILOTS=quarter python cfo_split_mse.py --workers 16      # -> logs/cfo_split_mse.json
    python cfo_split_mse.py --plot                                # -> plots/mse/cfo_mse_vs_snr_split_pilots.png
"""
import argparse
import json
import multiprocessing as mp
import os

import numpy as np

import paths

SNRS = [-5, -4, -3, -2, -1, 0, 2, 5, 10]
PACKETS = (512, 1024)
LAYOUT = "quarter"
CHUNK = 10000                # frames per work unit
BATCH = 500                  # frames per chain call (memory: 16 workers x a few 500 x 8272 complex arrays)
OUT = "cfo_split_mse.json"


def _work(task):
    n_sym, snr, seed = task
    import torch
    torch.set_num_threads(1)
    from train_cfo_v3 import make_z, spacing, split_ml
    rng = np.random.default_rng(seed)
    errs = []
    for _ in range(CHUNK // BATCH):          # the chain at 8 SPS: ~16 MB per frame-batch of 1024 symbols
        z, f, s = make_z(BATCH, n_sym, snr, snr, rng, snr)
        errs.append(split_ml(z, n_sym, LAYOUT)[0].numpy() - f)
    err = np.concatenate(errs)
    ok = np.rint(err / spacing(n_sym, LAYOUT)) == 0
    return n_sym, snr, float((err ** 2).sum()), int((~ok).sum()), float((err[ok] ** 2).sum()), int(ok.sum()), len(err)


def run(workers):
    assert os.environ.get("CFO_PILOTS") == LAYOUT, "run with CFO_PILOTS=quarter (positions used by make_z)"
    tasks = [(n, s, 1000 * n + 17 * i + 100 * (s + 10)) for n in PACKETS for s in SNRS
             for i in range((1000000 if s <= -3 else 100000) // CHUNK)]
    acc = {}
    with mp.Pool(workers) as pool:
        for k, (n, s, se, wrong, se_ok, n_ok, cnt) in enumerate(pool.imap_unordered(_work, tasks), 1):
            a = acc.setdefault((n, s), [0.0, 0, 0.0, 0, 0])
            a[0] += se; a[1] += wrong; a[2] += se_ok; a[3] += n_ok; a[4] += cnt
            if k % 50 == 0 or k == len(tasks):
                print(f"{k}/{len(tasks)} chunks", flush=True)
    from train_cfo_v3 import crb_split
    out = {"layout": LAYOUT, "snr": SNRS, "packets": {}}
    for n in PACKETS:
        rows = [acc[(n, s)] for s in SNRS]
        out["packets"][str(n)] = {
            "mse": [r[0] / r[4] for r in rows],
            "wrong_lobe_rate": [r[1] / r[4] for r in rows],
            "fine_mse": [r[2] / max(r[3], 1) for r in rows],
            "crb": [float(crb_split(s, n, LAYOUT)) for s in SNRS],
            "n": [r[4] for r in rows]}
        for s, r in zip(SNRS, rows):
            print(f"N={n} {s:4d} dB: MSE {r[0] / r[4]:.2e}  wrong lobe {r[1] / r[4]:.2e}  "
                  f"fine MSE/CRB {r[2] / max(r[3], 1) / crb_split(s, n, LAYOUT):.3f}  ({r[4]} frames)", flush=True)
    json.dump(out, open(paths.log(OUT), "w"), indent=1)
    print("DONE", flush=True)


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from train_snr_nn import crb
    sp = json.load(open(paths.log(OUT)))
    v2 = json.load(open(paths.log("cfo_v2_light32_test.json")))
    snr = np.array(sp["snr"], float)
    c128 = np.array([crb(s) for s in v2["snr"]])
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.semilogy(v2["snr"], np.array(v2["est"]["M&M"]["mse_over_crb"]) * c128, "-.", color="#ff7f0e", marker="d",
                lw=2.2, label="M&M (contiguous 128 pilots)")
    ax.semilogy(v2["snr"], np.array(v2["est"]["v2"]["mse_over_crb"]) * c128, "-", color="#2ca02c", marker="^",
                lw=2.2, label="NN v2 (contiguous 128 pilots)")
    ax.semilogy(v2["snr"], c128, ":", color="0.4", lw=1.6, label="CRB, contiguous 128 pilots")
    for n, c, mk in (("512", "#d62728", "*"), ("1024", "#8c1a1a", "P")):
        p = sp["packets"][n]
        ax.semilogy(snr, p["mse"], "-", color=c, marker=mk, lw=2.2,
                    label=f"Split pilots, {n}-symbol packet (all frames)")
        ax.semilogy(snr, p["fine_mse"], "--", color=c, marker=mk, lw=1.6, markerfacecolor="none",
                    label=f"Split pilots, {n}-symbol packet (right lobe only)")
        ax.semilogy(snr, p["crb"], ":", color=c, lw=1.4, label=f"CRB, split pilots, {n} symbols")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO MSE [(cycles/symbol)²]")
    fig.suptitle("CFO MSE vs SNR", fontsize=15, fontweight="bold")
    ax.set_title("128 known symbols in every estimator; split pilots: two 64-symbol blocks centred at N/4 and 3N/4 "
                 "(ML estimator)", fontsize=10, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=3, frameon=False)
    fig.tight_layout()
    out = paths.plot("cfo_mse_vs_snr_split_pilots.png")
    fig.savefig(out, dpi=300)
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--plot", action="store_true")
    a = ap.parse_args()
    plot() if a.plot else run(a.workers)
