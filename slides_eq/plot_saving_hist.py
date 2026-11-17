"""Slide 19: MACs per core saved by the adopted testing receiver vs the presentation receiver, per SNR
-> slides_eq/saving_hist.png

    python slides_eq/plot_saving_hist.py

Data: data/testing_vs_pres_17b16ea.json (full-chain-cfo 17b16ea, agg_cmp: presentation = pres_fix_macs with the fixed
accounting only; testing = adopted (1/10, 0.15) / testing_hi (2/5, 1/2)); MACs per core = the scheduled count. Only SNRs
where both receivers have fixed-accounting runs; the two receivers ran on different packets.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "testing_vs_pres_17b16ea.json")))
plt.rcParams.update({"font.size": 14, "font.family": "DejaVu Sans"})
COL = {"1/10": "#003366", "0.15": "#6f9bd1", "2/5": "#E07B39", "1/2": "#f2b98c"}

fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [2.2, 1]})
for ax, rates in zip(axs, (("1/10", "0.15"), ("2/5", "1/2"))):
    snrs = sorted({float(s) for r in rates for s in D[r]})
    x = np.arange(len(snrs))
    w = 0.4
    for i, r in enumerate(rates):
        for j, s in enumerate(snrs):
            v = D[r].get(str(s)) or D[r].get(f"{s:.1f}")
            if not v:
                continue
            y = 100 * (1 - v["test"] / v["pres"])
            xx = j + (i - 0.5) * w
            ax.bar(xx, y, w, color=COL[r], label=f"R = {r}" if j == min(k for k, t in enumerate(snrs) if str(t) in D[r] or f"{t:.1f}" in D[r]) else None)
            ax.text(xx, y + 0.8, f"{y:.0f}", ha="center", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s:g}" for s in snrs])
    ax.set_xlabel("SNR [dB]")
    ax.set_ylim(0, 50)
    ax.grid(True, axis="y", ls=":", alpha=0.5)
    ax.legend(fontsize=13, loc="upper right")
axs[0].set_ylabel("MACs per core saved [%]")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "saving_hist.png"), dpi=200, facecolor="white")
