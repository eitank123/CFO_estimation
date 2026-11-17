"""Slide 19: MACs per core with the fast path (Stage 1) OFF vs ON, paired packets -> slides_eq/fastpath_switch.png

    python slides_eq/plot_fastpath_switch.py

Values from the user's fast-path-switch histograms (2026-11-17), which match BLIND_IMPLEMENTATION/08_parameters_results.md
8.1a ("Fast path off"): 1/10 -30/-37/-38/-37/-30 % at -5/-4/-3/-1/0 dB; 0.15 -15/-35/-35/-26 % at -4/-3/-1/0 dB, +6 % at
+1 dB; 2/5 +22 % at 0.5 dB (+15 % at 1 dB: user figure); 1/2 +278 / +316 % at 2 / 2.5 dB.
Green = turning the fast path off saves MACs, red = it costs.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
GREEN, RED, BLUE = "#2e8b3d", "#c8423b", "#2b6cb0"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
P = (("R = 1/10", [("−5", -30), ("−4", -37), ("−3", -38), ("−1", -37), ("0", -30)], None),
     ("R = 0.15", [("−4", -15), ("−3", -35), ("−1", -35), ("0", -26), ("+1", 6)], 3.5),
     ("R = 2/5, 1/2", [("0.5\nR = 2/5", 22), ("1\nR = 2/5", 15), ("2\nR = 1/2", 278), ("2.5\nR = 1/2", 316)], None))

fig, axs = plt.subplots(1, 3, figsize=(16, 5.0), gridspec_kw={"width_ratios": [1, 1, 0.9]})
for k, (ax, (title, pts, cut)) in enumerate(zip(axs, P)):
    for j, (lab, y) in enumerate(pts):
        ax.bar(j, y, 0.62, color=GREEN if y < 0 else RED)
        big = k == 2
        off = (8 if big else 1.2) if y >= 0 else (-(8 if big else 1.2))
        ax.text(j, y + off, f"{y:+d} %".replace("-", "−"), ha="center", va="bottom" if y >= 0 else "top", fontsize=12)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels([p[0] for p in pts])
    ax.set_xlabel("SNR [dB]")
    ax.set_title(title, fontweight="bold")
    ax.grid(True, axis="y", ls=":", alpha=0.5)
    if k < 2:
        ax.set_ylim(-48, 14)
    else:
        ax.set_ylim(0, 380)
    if cut:
        ax.axvline(cut, color=BLUE, ls="--", lw=2)
        ax.text(cut - 0.1, 11, "OFF", ha="right", va="center", color=BLUE, fontsize=12)
        ax.text(cut + 0.1, 11, "ON", ha="left", va="center", color=BLUE, fontsize=12)
axs[0].set_ylabel("MACs per core, fast path OFF vs ON [%]")
axs[2].text(1.5, 340, "fast path stays ON", ha="center", color=BLUE, fontsize=12)
h = [plt.Rectangle((0, 0), 1, 1, color=GREEN), plt.Rectangle((0, 0), 1, 1, color=RED)]
fig.legend(h, ["turning it off saves MACs", "turning it off costs MACs"], loc="lower center", ncol=2, fontsize=13,
           frameon=False)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(os.path.join(HERE, "fastpath_switch.png"), dpi=200, facecolor="white")
