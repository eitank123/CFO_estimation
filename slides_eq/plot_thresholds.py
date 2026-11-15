"""Thresholds slide: three simple panels -> slides_eq/thresholds.png

    python slides_eq/plot_thresholds.py

Numbers are the measured ones quoted in BLIND_IMPLEMENTATION (08 §8.1a, 06 §6.2, 04 §4.6); R = 1/10 at -5 dB unless noted.
(a) BLER vs a hard cap on the MACs per core, from the measured per-packet histograms (chosen caps marked)
(b) rho: highest false and lowest right CRC pass at the calibrated points of R = 1/10 and 2/5, and the chosen c_R
(c) z-test: Gaussian tail of a wrong cell's z (idealised) with the thresholds used
"""
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, ORANGE, RED, GREY = "#003366", "#E07B39", "#c8423b", "#777777"
plt.rcParams.update({"font.size": 14, "font.family": "DejaVu Sans"})
fig, (a, b, c) = plt.subplots(1, 3, figsize=(15, 5.0))

# (a) BLER vs a hard cap on the MACs per core (measured per-packet histograms of the right decodes, small_rx "pg_";
#     the search stops at its first accepted decode, so a cap C turns the right decodes that needed more than C into errors)
import json
D = json.load(open(os.path.join(HERE, "data", "results_c90c5b7.json")))
edges = 10 ** (4 + np.arange(1, 101) / 20)                    # upper edge of each 0.05-decade bin from 1e4
for rate, snr, col, cap in (("1/10", "-5.0", NAVY, 2e6), ("2/5", "1.0", ORANGE, 1e6), ("1/2", "2.0", GREY, 1e6)):
    h = D[rate]["hist"][snr]
    miss = 1 - np.cumsum(h["pg"]) / h["n"]
    m = miss > 0.5 / h["n"]
    a.loglog(edges[m], miss[m], color=col, lw=2.5, label=f"R = {rate}, {float(snr):g} dB".replace("-", "−"))
    k = int(round(20 * np.log10(cap / 1e4))) - 1
    a.plot(cap, miss[k], "o", color=col, ms=9)
a.axvline(1e6, color=GREY, ls=":", lw=1.5)
a.axvline(2e6, color=GREY, ls=":", lw=1.5)
a.text(1e6, 5e-5, "1 M ", ha="right", color=GREY, fontsize=12)
a.text(2e6, 5e-5, " 2 M", ha="left", color=GREY, fontsize=12)
a.set_ylim(3e-5, 1.6)
a.set_xlim(5e4, 3e7)
a.set_xlabel("cap on MACs per core")
a.set_ylabel("BLER")
a.set_title("MAC cap", fontweight="bold")
a.legend(fontsize=12, loc="upper right")
a.grid(True, which="major", ls=":", alpha=0.5)

# (b) re-encoding calibration at R = 1/10 and 2/5 (normalised rho)
cal = [("1/10\n−5 dB", 0.7945, 0.7519, 0.775), ("1/10\n−3 dB", 0.690, 0.633, 0.66), ("2/5\n0.5 dB", 0.9503, 0.9052, 0.928)]
for i, (lab, right, false, rho) in enumerate(cal):
    b.plot(i, right, "o", color=NAVY, ms=12)
    b.plot(i, false, "x", color=RED, ms=12, mew=3)
    b.plot([i - 0.25, i + 0.25], [rho, rho], color=ORANGE, lw=4)
b.set_xticks(range(len(cal)))
b.set_xticklabels([x[0] for x in cal])
b.set_xlim(-0.5, 2.5)
b.set_ylabel("normalised ρ")
b.set_title("Re-encoding threshold ρ", fontweight="bold")
b.legend([plt.Line2D([], [], color=NAVY, marker="o", ls="none", ms=10),
          plt.Line2D([], [], color=ORANGE, lw=4),
          plt.Line2D([], [], color=RED, marker="x", ls="none", mew=3, ms=10)],
         ["lowest right pass", "threshold c_R", "highest false pass"], fontsize=12, loc="upper left")
b.grid(True, axis="y", ls=":", alpha=0.5)

# (c) z-test: tail probability of a wrong cell (idealised Gaussian) and the thresholds
z = np.linspace(0, 11, 400)
c.semilogy(z, norm.sf(z), color=GREY, lw=2.5)
for t, lab, col, yy in ((4, "candidate\nz > 4", ORANGE, 1e-11), (6, "decode\nat once\nz > 6", NAVY, 3e-4)):
    c.axvline(t, color=col, lw=2.5)
    c.text(t - 0.2 if t == 4 else t + 0.2, yy, lab, color=col, fontsize=12, ha="right" if t == 4 else "left")
c.set_ylim(1e-12, 1)
c.set_xlim(0, 11)
c.set_xlabel("z of a cell")
c.set_ylabel("P(wrong cell above z)")
c.set_title("z-test thresholds", fontweight="bold")
c.grid(True, which="major", ls=":", alpha=0.5)

fig.tight_layout()
fig.savefig(os.path.join(HERE, "thresholds.png"), dpi=200, facecolor="white")
