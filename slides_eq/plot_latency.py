"""MACs per packet of the blind receiver: total work vs critical path on 32 cores (README A.17.2 tables).

Run: python slides_eq/plot_latency.py  (writes slides_eq/latency.png)
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

OUT = os.path.dirname(os.path.abspath(__file__))
NAVY, ORANGE, MUTED = "#003366", "#E07B39", "#5B6573"

# SNR: (total M MACs, per-core M MACs), blind final receivers
BLIND = {
    "R = 1/10": [(-5, 4.16, .77), (-4.5, 3.41, .72), (-4, 2.99, .70), (-3, 2.67, .68), (-2, 2.52, .66), (-1, 1.94, .62), (0, 1.44, .54)],
    "R = 2/5": [(.5, 3.65, 1.72), (1, 1.26, .73), (1.5, .77, .53), (2, .60, .44), (2.5, .56, .42), (3, .55, .42)],
    "R = 1/2": [(2, .74, .47), (2.5, .58, .43), (3, .55, .43), (3.5, .55, .43), (4, .55, .43), (5, .55, .43)],
}
# ML direct + re-encoding check, 128 pilots: (SNR, total, per core) at the operating point
ML = {"R = 1/10": (-5, .52, .16), "R = 2/5": (.5, .30, .17), "R = 1/2": (2, .27, .17)}
DEC = 0.186  # one CA-SCL-8 decode on one core (M MACs)

fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.9), sharey=True)
for ax, (rate, pts) in zip(axs, BLIND.items()):
    s = [p[0] for p in pts]
    ax.plot(s, [p[1] for p in pts], color=NAVY, ls="--", lw=2, marker="o", ms=6, mfc="white", label="blind: total MACs")
    ax.plot(s, [p[2] for p in pts], color=NAVY, ls="-", lw=2, marker="o", ms=6, label="blind: per core (latency)")
    m = ML[rate]
    ax.plot([m[0]], [m[2]], color=ORANGE, marker="^", ms=9, ls="none", label="ML + re-enc., 128 pilots: per core")
    ax.axhline(DEC, color=MUTED, ls=":", lw=1.5, label="one CA-SCL-8 decode on 1 core")
    ax.set_yscale("log")
    ax.set_ylim(0.1, 6)
    ax.set_title(rate, fontsize=13, fontweight="bold")
    ax.set_xlabel("SNR (Es/N0) [dB]", fontsize=11)
    ax.grid(True, which="both", color="#e5e7eb", lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axs[0].set_ylabel("M MACs per packet", fontsize=11)
axs[0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
axs[0].set_yticks([0.1, 0.2, 0.5, 1, 2, 5])
axs[0].set_yticklabels(["0.1", "0.2", "0.5", "1", "2", "5"])
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, fontsize=10, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(os.path.join(OUT, "latency.png"), dpi=200, facecolor="white")
