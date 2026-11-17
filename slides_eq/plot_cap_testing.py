"""Hard cap on the MACs per core, adopted testing receiver -> slides_eq/cap_bler.png, cap_macs.png

    python slides_eq/plot_cap_testing.py

Data: slides_eq/data/cap_testing_17b16ea.json = the packet pool of BLIND_IMPLEMENTATION/testing/plot_cap_fair.py
(full-chain-cfo 17b16ea): per SNR, packets, errors, and the small_rx histograms pg_ (right decodes) and ph_ (all
packets) of the critical-path MACs per core (crit_par, 32 cores; 0.05-decade bins from 1e4).
- capped BLER = (errors + right decodes with crit_par >= cap) / packets (the search stops at its first accepted decode),
  exact at the bin edge: caps 2 M (bin 46) at R = 1/10, 0.15 and 1 M (bin 40) at 2/5, 1/2;
- mean MACs per core, uncapped and capped, from the ph_ histogram at the bin centres (capped: min(centre, cap)).
crit_par is >= the scheduled count of fair_macs.png per packet, so these caps are conservative for blind.
Pilot receivers (uncapped) from data/curves_17b16ea.json.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "data", "cap_testing_17b16ea.json")))
V = json.load(open(os.path.join(HERE, "data", "curves_17b16ea.json")))
RATES = ("1/10", "0.15", "2/5", "1/2")
CAPK = {"1/10": 46, "0.15": 46, "2/5": 40, "1/2": 40}
MID = 10 ** (4 + (np.arange(100) + 0.5) / 20)
NAVY = "#003366"
REF = (("RCS2-13", "DVB-RCS2 ID 13", "#E07B39", "s"),
       ("VDE-SAT", "VDE-SAT", "#8c564b", "P"),
       ("CCSDS 131.0 ASM", "CCSDS 131.0 ASM", "#9467bd", "D"),
       ("CCSDS 131.2 real", "CCSDS 131.2 real", "#c8423b", "X"),
       ("DVB-S2 header90", "DVB-S2 PL header", "#2ca02c", "v"))
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})


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


def capname(rate):
    return f"{10 ** (4 + CAPK[rate] / 20) / 1e6:.0f} M"


def rows(rate):
    return sorted(((float(s), v) for s, v in C[rate].items()), key=lambda x: x[0])


def bler():
    fig, axs = plt.subplots(1, 4, figsize=(17, 5.2))
    for ax, rate in zip(axs, RATES):
        k = CAPK[rate]
        R = rows(rate)
        xs = []
        for src, _, c, m in REF:
            p = [(float(s), v["err"] / v["n"]) for s, v in sorted(V[rate]["comp"][src].items(), key=lambda x: float(x[0]))]
            draw(ax, p, color=c, marker=m, ms=5, lw=1.3, ls="--", alpha=0.8)
            xs += [s for r in runs(p) for s, _ in r]
        p0 = [(s, v["err"] / v["n"]) for s, v in R]
        p1 = [(s, (v["err"] + sum(v["pg"][k:])) / v["n"]) for s, v in R]
        draw(ax, p0, color=NAVY, marker="o", ms=7, lw=1.8, ls="--", mfc="white")
        draw(ax, p1, color=NAVY, marker="o", ms=8, lw=3)
        xs += [s for r in runs(p0) + runs(p1) for s, _ in r]
        ax.set_xlim(min(xs) - 0.15, max(xs) + 0.15)
        ax.set_yscale("log")
        ax.set_title(f"R = {rate}: cap {capname(rate)}", fontweight="bold")
        ax.set_xlabel("SNR [dB], pilot energy charged")
        ax.grid(True, which="both", ls=":", alpha=0.45)
        print(rate, [(s, round(a, 7), round(b, 7)) for (s, a), (_, b) in zip(p0, p1)])
    axs[0].set_ylabel("BLER")
    h = [plt.Line2D([], [], color=NAVY, marker="o", ms=7, lw=1.8, ls="--", mfc="white"),
         plt.Line2D([], [], color=NAVY, marker="o", ms=8, lw=3)] + \
        [plt.Line2D([], [], color=c, marker=m, ms=6, lw=1.7, ls="--") for _, _, c, m in REF]
    fig.legend(h, ["blind (testing receiver), no cap", "blind with the hard cap on MACs per core (same packets)"]
               + [l + " (no cap)" for _, l, _, _ in REF], loc="lower center", ncol=4, fontsize=12, frameon=False)
    fig.tight_layout(rect=(0, 0.15, 1, 1))
    fig.savefig(os.path.join(HERE, "cap_bler.png"), dpi=200, facecolor="white")


def macs():
    fig, axs = plt.subplots(1, 4, figsize=(17, 5.2))
    for ax, rate in zip(axs, RATES):
        k = CAPK[rate]
        cap = 10 ** (4 + k / 20)
        R = rows(rate)
        x = [s for s, _ in R]
        m0 = [float((np.array(v["ph"]) * MID).sum() / sum(v["ph"])) / 1e6 for _, v in R]
        m1 = [float((np.array(v["ph"]) * np.minimum(MID, cap)).sum() / sum(v["ph"])) / 1e6 for _, v in R]
        ax.plot(x, m0, color=NAVY, marker="o", ms=7, lw=1.8, ls="--", mfc="white")
        ax.plot(x, m1, color=NAVY, marker="o", ms=8, lw=3)
        ax.axhline(cap / 1e6, color="#777777", ls="-.", lw=1.5)
        ax.text(0.97, 0.95, f"cap = {capname(rate)} per core", transform=ax.transAxes, ha="right", va="top",
                color="#555555", fontsize=11)
        ax.set_yscale("log")
        lo, hi = min(m1) * 0.7, max(max(m0), cap / 1e6) * 1.6
        ax.set_ylim(lo, hi)
        t = [v for v in (0.05, 0.1, 0.2, 0.5, 1, 2, 5) if lo <= v <= hi]
        ax.minorticks_off()
        ax.set_yticks(t)
        ax.set_yticklabels([f"{v:g}" for v in t])
        ax.set_title(f"R = {rate}", fontweight="bold")
        ax.set_xlabel("SNR [dB]")
        ax.grid(True, which="major", ls=":", alpha=0.45)
        print(rate, [(s, round(a, 3), round(b, 3)) for s, a, b in zip(x, m0, m1)])
    axs[0].set_ylabel("mean MACs per core [M]\n(critical path, 32 cores)")
    fig.legend([plt.Line2D([], [], color=NAVY, marker="o", ms=7, lw=1.8, ls="--", mfc="white"),
                plt.Line2D([], [], color=NAVY, marker="o", ms=8, lw=3)],
               ["blind (testing receiver), no cap", "blind with the hard cap"], loc="lower center", ncol=2,
               fontsize=12, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "cap_macs.png"), dpi=200, facecolor="white")


bler()
macs()
