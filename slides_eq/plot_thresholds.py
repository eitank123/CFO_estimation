"""Thresholds slide: three simple panels -> slides_eq/thresholds.png

    python slides_eq/plot_thresholds.py

Numbers are the measured ones quoted in BLIND_IMPLEMENTATION (08 §8.1a, 06 §6.2, 04 §4.6); R = 1/10 at -5 dB unless noted.
(a) MACs: extra MACs of each alternative to the chosen setting, with its errors (alternative vs chosen)
(b) rho: highest false and lowest right CRC pass at the calibrated points of R = 1/10 and 2/5, and the chosen c_R
(c) z-test: Gaussian tail of a wrong cell's z (idealised) with the thresholds used and where the true cell sits
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

# (a) extra MACs of each alternative (bar) and its errors vs the chosen setting (label)
alts = [("early win z > 4", 6, "9 vs 8 errors"),
        ("one checkpoint", 22, "BLER ×1.7"),
        ("keep all phases", 44, "10 vs 9 errors"),
        ("no batches", 62, "47 vs 47 errors")]
y = np.arange(len(alts))[::-1]
a.barh(y, [m for _, m, _ in alts], color=ORANGE, height=0.55)
for yi, (_, m, e) in zip(y, alts):
    a.text(m + 2, yi, ("+43–82 %" if m == 62 else f"+{m} %") + f"\n{e}", va="center", fontsize=12)
a.set_yticks(y)
a.set_yticklabels([n for n, _, _ in alts])
a.set_xlim(0, 100)
a.set_xlabel("extra MACs vs the chosen setting [%]")
a.set_title("MACs of the alternatives", fontweight="bold")
a.grid(True, axis="x", ls=":", alpha=0.5)

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
    c.text(t + 0.2, yy, lab, color=col, fontsize=12)
c.axvspan(8, 11, color=NAVY, alpha=0.12)
c.text(9.5, 1e-6, "true cell\nz ≈ 10", ha="center", color=NAVY, fontsize=12)
c.set_ylim(1e-12, 1)
c.set_xlim(0, 11)
c.set_xlabel("z of a cell")
c.set_ylabel("P(wrong cell above z)")
c.set_title("z-test thresholds", fontweight="bold")
c.grid(True, which="major", ls=":", alpha=0.5)

fig.tight_layout()
fig.savefig(os.path.join(HERE, "thresholds.png"), dpi=200, facecolor="white")
