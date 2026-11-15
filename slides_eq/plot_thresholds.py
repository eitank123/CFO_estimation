"""Thresholds slide: why each threshold of the presentation receiver has its value, as plots.

    python slides_eq/plot_thresholds.py   -> slides_eq/thresholds.png

Numbers are the measured ones quoted in BLIND_IMPLEMENTATION (full-chain-cfo c90c5b7 and the 2026-11-16 docs):
08 §8.1a (variant runs), 06 §6.2 (re-encoding calibration table), 04 §4.6. No other data is used.
(a) each alternative to a chosen threshold: MAC change vs error ratio, relative to the chosen setting (R = 1/10, -5 dB)
(b) re-encoding calibration: per calibrated point, the highest false CRC pass, the lowest right pass, and c_R
(c) checkpoint NN cut: true cells missed and cells kept per cumulative-probability cut
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, ORANGE, RED, GREY = "#003366", "#E07B39", "#c8423b", "#777777"
plt.rcParams.update({"font.size": 12, "font.family": "DejaVu Sans"})

fig, (a, b, c) = plt.subplots(1, 3, figsize=(15, 5.2), gridspec_kw={"width_ratios": [1.25, 1.1, 0.9]})

# (a) alternatives, R = 1/10 -5 dB: x = MAC change vs the chosen setting [%], y = errors (alternative / chosen)
alts = [  # label, x, y, x-range or None, metric, packets
    ("early win at z > 4\ninstead of z > 6", 6, 9 / 8, None, "per core", "64k paired"),
    ("keep all phases\ninstead of the best 2", 100 * (5.99 / 4.15 - 1), 9 / 10, None, "total", "40k"),
    ("no batches of 32 cells", 62, 47 / 47, (43, 82), "total", "40k"),
    ("one checkpoint, τ = +1\ninstead of ½ + ¾, τ = −0.5", 100 * (10.5 / 8.6 - 1), 6.7 / 3.9, None, "total", ""),
]
a.axhline(1, color=GREY, lw=1, ls=":")
a.axvline(0, color=GREY, lw=1, ls=":")
a.plot(0, 1, marker="*", ms=20, color=NAVY, ls="none", zorder=5)
a.annotate("chosen thresholds", (0, 1), xytext=(2, 0.76), fontsize=11, color=NAVY,
           arrowprops=dict(arrowstyle="-", color=NAVY, lw=1))
offs = [(8, 1.40), (50, 0.76), (50, 1.13), (30, 1.95)]
for (lab, x, y, rng, met, pk), (tx, ty) in zip(alts, offs):
    if rng:
        a.plot(rng, [y, y], color=ORANGE, lw=4, alpha=0.6, solid_capstyle="round")
    a.plot(x, y, "o", color=ORANGE, ms=9, zorder=4)
    a.annotate(f"{lab}\n({met} MACs{', ' + pk if pk else ''})", (x, y), xytext=(tx, ty), fontsize=9.5,
               arrowprops=dict(arrowstyle="-", color=GREY, lw=0.8))
a.set_yscale("log")
a.set_ylim(0.7, 2.6)
a.set_yticks([0.8, 1, 1.25, 1.5, 2, 2.5])
a.set_yticklabels(["0.8", "1", "1.25", "1.5", "2", "2.5"])
a.set_xlim(-8, 95)
a.set_xlabel("MACs vs the chosen setting [%]")
a.set_ylabel("errors: alternative / chosen")
a.set_title("(a) every alternative costs MACs or BLER\nR = 1/10, −5 dB", fontsize=12, fontweight="bold")
a.grid(True, which="both", ls=":", alpha=0.5)

# (b) re-encoding calibration (06 §6.2): normalised rho of the highest false and the lowest right CRC pass
cal = [("1/10\n−5 dB", 0.7945, 0.7519, 0.775), ("1/10\n−3 dB", 0.690, 0.633, 0.66), ("0.15\n−4.5 dB", 0.8926, 0.8525, 0.873),
       ("0.15\n−1 dB", 0.7337, 0.6545, 0.694), ("0.15\n0 dB", 0.7663, 0.6189, 0.693), ("0.15\n+1 dB", 0.7217, 0.5881, 0.655),
       ("2/5\n0.5 dB", 0.9503, 0.9052, 0.928)]
for i, (lab, right, false, rho) in enumerate(cal):
    b.plot([i, i], [false, right], color=GREY, lw=1.2)
    b.plot(i, right, "o", color=NAVY, ms=8)
    b.plot(i, false, "x", color=RED, ms=9, mew=2.2)
    b.plot([i - 0.28, i + 0.28], [rho, rho], color=ORANGE, lw=3)
b.set_xticks(range(len(cal)))
b.set_xticklabels([c_[0] for c_ in cal], fontsize=9.5)
b.set_ylabel("ρ / √(s/(1+s))")
b.set_title("(b) re-encoding threshold c_R: midway\nbetween false and right CRC passes", fontsize=12, fontweight="bold")
b.legend([plt.Line2D([], [], color=NAVY, marker="o", ls="none"), plt.Line2D([], [], color=RED, marker="x", ls="none", mew=2),
          plt.Line2D([], [], color=ORANGE, lw=3)], ["lowest right pass", "highest false pass", "chosen c_R"],
         fontsize=9.5, loc="upper center", bbox_to_anchor=(0.6, 1.0))
b.grid(True, axis="y", ls=":", alpha=0.5)

# (c) checkpoint NN cut (08 §8.1a): true cells missed [%], cells kept
cuts = ["1 − 10⁻²", "1 − 10⁻³\n(chosen)", "1 − 10⁻⁴"]
miss25, miss2 = [0.17, 0.0, None], [0.07, 0.0, None]
kept = ["27.5 cells", "69 cells", "133 cells"]
w = 0.36
for i in range(3):
    for dx, m, col, lab in ((-w / 2, miss25[i], NAVY, "R = 2/5"), (w / 2, miss2[i], ORANGE, "R = 1/2")):
        if m is not None:
            c.bar(i + dx, m, w, color=col, label=lab if i == 0 else None)
            c.text(i + dx, m + 0.004, f"{m:g} %", ha="center", fontsize=9.5)
    c.text(i, 0.205, kept[i], ha="center", fontsize=10, color=GREY)
c.text(2, 0.03, "misses not\nreported;\nwork 0.499\nvs 0.379", ha="center", fontsize=9.5, color=GREY)
c.set_xticks(range(3))
c.set_xticklabels(cuts)
c.set_ylim(0, 0.23)
c.set_ylabel("true cells missed [%]")
c.set_xlabel("cumulative probability kept by the NN")
c.set_title("(c) checkpoint NN cut\n(3000 packets per point)", fontsize=12, fontweight="bold")
c.legend(fontsize=9.5, loc="center right")
c.grid(True, axis="y", ls=":", alpha=0.5)

fig.tight_layout()
fig.savefig(os.path.join(HERE, "thresholds.png"), dpi=200, facecolor="white")
