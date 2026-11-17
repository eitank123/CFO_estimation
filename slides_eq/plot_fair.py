"""Blind (adopted testing receiver) vs the most relevant deployed pilot / preamble systems, full curves on the fair
SNR axis (known symbols outside the packet, their energy charged), from slides_eq/data/curves_17b16ea.json
(full-chain-cfo 17b16ea, testing/plot_curves.data + the est4 genie).

    python slides_eq/plot_fair.py

fair_bler.png   BLER vs SNR, R = 1/10, 0.15, 2/5, 1/2
fair_macs.png   MACs per core (32 cores, scheduled count) vs SNR, same receivers
Lines join runs of >= 2 adjacent simulated SNRs with errors; 0-error and isolated points are not drawn.
"""
import json
import os

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "curves_17b16ea.json")))
RATES = ("1/10", "0.15", "2/5", "1/2")
NAVY = "#003366"
COMP = (("RCS2-13", "DVB-RCS2 ID 13 (116 known, +0.47 dB)", "#E07B39", "s"),
        ("pre128 ML", "128-symbol preamble, ML (+0.51 dB)", "#777777", "^"),
        ("DVB-S2 style", "DVB-S2-inspired: header + pilot block (126, +0.50 dB)", "#2ca02c", "v"),
        ("CCSDS 131.0 ASM", "CCSDS 131.0 ASM (64, +0.26 dB)", "#9467bd", "D"),
        ("VDE-SAT", "VDE-SAT (66, +0.27 dB)", "#8c564b", "P"),
        ("DMRS 1/7", "5G-NR-like DMRS 1/7 (171, +0.67 dB)", "#17becf", "X"),
        ("hyb3-pre48 wide", "Advantech 48 preamble, wide DA window (+0.20 dB)", "#c8423b", "h"))
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})


def pts(d, key):
    out = []
    for s in sorted(d, key=float):
        v = d[s]
        if key == "bler":
            out.append((float(s), v["err"] / v["n"] if v["n"] else 0))
        elif v.get("core"):
            out.append((float(s), v["core"] / 1e6))
    return out


def runs(p):
    out, run = [], []
    for s, y in p + [(None, 0)]:
        if y > 0:
            run.append((s, y))
            continue
        if len(run) > 1:
            out.append(run)
        run = []
    return out


def draw(ax, p, **kw):
    for r in runs(p):
        ax.plot(*zip(*r), **kw)


def figure(key, fname):
    fig, axs = plt.subplots(1, 4, figsize=(17, 5.4))
    for ax, rate in zip(axs, RATES):
        o = D[rate]
        xs = []
        if key == "bler":
            g = pts(o["genie"], key)
            draw(ax, g, color="k", ls=":", lw=1.6)
            xs += [s for r in runs(g) for s, _ in r]
        for src, _, c, m in COMP[::-1]:
            p = pts(o["comp"][src], key)
            draw(ax, p, color=c, marker=m, ms=6, lw=1.7, ls="--")
            xs += [s for r in runs(p) for s, _ in r]
        b = pts(o["blind"], key)
        draw(ax, b, color=NAVY, marker="o", ms=8, lw=3)
        xs += [s for r in runs(b) for s, _ in r]
        ax.set_xlim(min(xs) - 0.15, max(xs) + 0.15)
        ax.set_yscale("log")
        ax.set_title(f"R = {rate}", fontweight="bold")
        if key == "macs":
            lo, hi = ax.get_ylim()
            t = [v for v in (0.03, 0.05, 0.1, 0.2, 0.4, 1, 2, 4) if lo <= v <= hi]
            ax.minorticks_off()
            ax.set_yticks(t)
            ax.set_yticklabels([f"{v:g}" for v in t])
        ax.set_xlabel("SNR [dB], pilot energy charged")
        ax.grid(True, which="both", ls=":", alpha=0.45)
    axs[0].set_ylabel("BLER" if key == "bler" else "MACs per core [M]")
    h = [plt.Line2D([], [], color=NAVY, marker="o", ms=8, lw=3)] + \
        [plt.Line2D([], [], color=c, marker=m, ms=6, lw=1.7, ls="--") for _, _, c, m in COMP]
    lab = ["blind, 0 known symbols (testing receiver)"] + [l for _, l, _, _ in COMP]
    if key == "bler":
        h.append(plt.Line2D([], [], color="k", ls=":", lw=1.6))
        lab.append("genie*: known CFO and phase, no pilots, one decode")
    fig.legend(h, lab, loc="lower center", ncol=3, fontsize=11.5, frameon=False)
    fig.tight_layout(rect=(0, 0.2, 1, 1))
    fig.savefig(os.path.join(HERE, fname), dpi=200, facecolor="white")


figure("bler", "fair_bler.png")
figure("macs", "fair_macs.png")
