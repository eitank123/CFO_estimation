"""BLER plot for the slides: the blind receiver vs the single best 128-pilot benchmark, with statistics.

Benchmark: ML direct (FFT 512 + 2 Newton) on 128 contiguous pilots, with the same CRC-16 search and the same
re-encoding check as blind (study est3/).  Blind: the final receivers of the |f| <= 0.03 study.
Points with errors: BLER = errors / packets with the exact (Clopper-Pearson) 95 % interval.
Points with 0 errors: not a measured BLER; drawn as an open marker with a downward arrow at the one-sided
95 % upper bound 3/n (n = packets simulated at that point).

Usage:  python slides_eq/plot_bler.py <dir with est3 bler_k*.json and blind_ber.json>
"""
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import beta

SRC = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(__file__))
BLIND_RX = {"1/10": "S blind final v2", "2/5": "S blind final 2/5, 1/2, best-first 32", "1/2": "S blind final 2/5, 1/2"}
RANGE = {"1/10": (-5, 0), "2/5": (0.5, 3), "1/2": (1.5, 5)}
NAVY, ORANGE = "#003366", "#E07B39"

rows = []
for p in glob.glob(os.path.join(SRC, "bler_k*.json")):
    rows += json.load(open(p))["results"]
blind = json.load(open(os.path.join(SRC, "blind_ber.json")))


def cp(k, n):
    return (beta.ppf(0.025, k, n - k + 1) if k else 0.0), beta.ppf(0.975, k + 1, n - k)


plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.7))
for ax, (rate, (lo, hi)) in zip(axs, RANGE.items()):
    ml = sorted((r["snr"], r["frame_err"], r["frames"]) for r in rows
                if r["rate"] == rate and r["src"] == "ML direct" and lo <= r["snr"] <= hi)
    bl = sorted((x["snr"], x["frame_err"], x["frames"]) for x in blind
                if x["rate"] == rate and x["rx"] == BLIND_RX[rate] and lo <= x["snr"] <= hi)
    for pts, lab, c, mk, ls, dx in ((bl, "blind, 0 pilots", NAVY, "o", "-", -0.04),
                                    (ml, "ML + same search/check, 128 pilots", ORANGE, "^", "--", 0.04)):
        e = [p for p in pts if p[1]]
        x = [p[0] + dx for p in e]
        y = [p[1] / p[2] for p in e]
        ci = [cp(p[1], p[2]) for p in e]
        ax.errorbar(x, y, yerr=[[b - a[0] for a, b in zip(ci, y)], [a[1] - b for a, b in zip(ci, y)]],
                    color=c, ls="none", lw=2.2, marker=mk, ms=7, capsize=3, label=lab)
        run = []                                      # lines only between adjacent SNRs that both had errors
        for p in pts + [(None, 0, 1)]:
            if p[1]:
                run.append((p[0] + dx, p[1] / p[2]))
                continue
            if len(run) > 1:
                ax.plot(*zip(*run), color=c, ls=ls, lw=2.2)
            run = []
        z = [p for p in pts if p[1] == 0]
        for p in z:
            ub = 3.0 / p[2]
            ax.annotate("", xy=(p[0] + dx, ub / 2.2), xytext=(p[0] + dx, ub),
                        arrowprops=dict(arrowstyle="-|>", color=c, lw=1.6, mutation_scale=11))
        if z:
            ax.plot([p[0] + dx for p in z], [3.0 / p[2] for p in z], ls="none", marker=mk, ms=7, mfc="white", mec=c, mew=1.8)
        print(rate, lab, [(p[0], p[1], p[2]) for p in pts])
    ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_title(f"R = {rate}", fontweight="bold")
    ax.grid(True, which="both", ls=":", alpha=0.5)
axs[0].set_ylabel("BLER")
h, l = axs[0].get_legend_handles_labels()
h = [plt.Line2D([], [], color=NAVY, ls="-", lw=2.2, marker="o", ms=7), plt.Line2D([], [], color=ORANGE, ls="--", lw=2.2, marker="^", ms=7)]
l = ["blind, 0 pilots (95 % CI)", "ML + same search/check, 128 pilots (95 % CI)"]
h.append(plt.Line2D([], [], ls="none", marker="o", mfc="white", mec="#555555", mew=1.8, ms=7))
l.append("0 errors: one-sided 95 % upper bound 3/n (arrow)")
fig.legend(h, l, loc="lower center", ncol=3, fontsize=12, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(os.path.join(OUT, "bler_all.png"), dpi=200, facecolor="white")
