"""Slide 19: MACs per core saved by the adopted testing receiver vs the presentation receiver, per SNR, R = 1/10 and 0.15
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

GREEN, RED = "#2e8b3d", "#c8423b"
fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
for ax, r in zip(axs, ("1/10", "0.15")):
    pts = sorted((float(k), v) for k, v in D[r].items())
    for j, (snr, v) in enumerate(pts):
        y = 100 * (1 - v["test"] / v["pres"])
        ax.bar(j, y, 0.7, color=GREEN if y >= 0 else RED)
        ax.text(j, y + (0.8 if y >= 0 else -2.5), f"{y:.0f} %", ha="center", fontsize=12)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels([f"{snr:g}".replace("-", "−") for snr, _ in pts])
    ax.set_xlabel("SNR [dB]")
    ax.set_title(f"R = {r}", fontweight="bold")
    ax.set_ylim(min(-5, ax.get_ylim()[0]), 50)
    ax.grid(True, axis="y", ls=":", alpha=0.5)
axs[0].set_ylabel("MACs per core saved [%]")
handles = [plt.Rectangle((0, 0), 1, 1, color=GREEN), plt.Rectangle((0, 0), 1, 1, color=RED)]
fig.legend(handles, ["fewer MACs (saving)", "more MACs"], loc="lower center", ncol=2, fontsize=13, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(os.path.join(HERE, "saving_hist.png"), dpi=200, facecolor="white")
