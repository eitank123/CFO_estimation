"""BLER plots for the slides: the blind receiver vs the single best 128-pilot benchmark.

Benchmark: ML direct (FFT 512 + 2 Newton) on 128 contiguous pilots, with the same CRC-16
search and the same re-encoding check as blind (study est3/).  Blind: the final receivers of
the |f| <= 0.03 study (small_cfo/).  Points with 0 errors are drawn hollow at 1/frames
(an upper bound).

Usage:  python slides_eq/plot_bler.py <dir with est3 bler_k*.json and blind_ber.json>
"""
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(__file__))
BLIND_RX = {"1/10": "S blind final v2", "2/5": "S blind final 2/5, 1/2, best-first 32", "1/2": "S blind final 2/5, 1/2"}
RANGE = {"1/10": (-5, 0), "2/5": (0.5, 3), "1/2": (1.5, 5)}

rows = []
for p in glob.glob(os.path.join(SRC, "bler_k*.json")):
    rows += json.load(open(p))["results"]
blind = json.load(open(os.path.join(SRC, "blind_ber.json")))

plt.rcParams.update({"font.size": 14, "font.family": "DejaVu Sans"})
for rate, (lo, hi) in RANGE.items():
    ml = sorted((r["snr"], r["frame_err"], r["frames"]) for r in rows
                if r["rate"] == rate and r["src"] == "ML direct" and lo <= r["snr"] <= hi)
    bl = sorted((x["snr"], x["frame_err"], x["frames"]) for x in blind
                if x["rate"] == rate and x["rx"] == BLIND_RX[rate] and lo <= x["snr"] <= hi)
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for pts, lab, c, mk, ls in ((bl, "blind, 0 pilots", "#003366", "o", "-"),
                                (ml, "ML + re-encoding check, 128 pilots", "#E07B39", "^", "--")):
        x = [p[0] for p in pts]
        y = [p[1] / p[2] if p[1] else None for p in pts]
        ax.semilogy([a for a, b in zip(x, y) if b], [b for b in y if b], color=c, ls=ls, lw=2.6, marker=mk, ms=8, label=lab)
        zx = [p[0] for p in pts if p[1] == 0]
        zy = [1 / p[2] for p in pts if p[1] == 0]
        if zx:
            ax.semilogy(zx, zy, ls="none", marker=mk, ms=8, mfc="white", mec=c, mew=2)
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("BLER")
    ax.set_title(f"R = {rate}", fontweight="bold")
    ax.grid(True, which="both", ls=":", alpha=0.5)
    ax.legend(fontsize=12, loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"bler_R{rate.replace('/', '_')}.png"), dpi=200)
    plt.close(fig)
    print(rate, "blind", bl, "\n     ML", ml)
