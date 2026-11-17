"""Testing-receiver changes -> slides_eq/tr_gates.png, f5_thr.png, f5_save.png

    python slides_eq/plot_testing_changes.py

tr_gates.png  per-core MACs change of two switches vs SNR, paired measurements quoted in
              BLIND_IMPLEMENTATION/08_parameters_results.md 8.1a (fast path off: 1/10, 0.15; spec11 sweep: 1/10, 0.15),
              with the adopted gates (fast path off at SNR <= 0 dB; spec11 below -3.5 dB / -2.5 dB)
f5_thr.png    F5 threshold study (data/fz_f5_17b16ea.json = testing/results/fz_f5.json, decode dumps): per checkpoint q
              (share of the frozen bits seen) the median psn of right and wrong CA-SCL-8 decodes and the 0-loss threshold
              t, and at that t the wrong decodes stopped and the MACs per core saved
f5_save.png   MACs per core with and without F5 (data/f5_paired_17b16ea.json from agg_cmp FZS parts): paired where both
              arms ran on the same packets (filled), otherwise vs the q_fix receiver on other packets (open)
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, ORANGE, RED, GREY, GREEN = "#003366", "#E07B39", "#c8423b", "#777777", "#2ca02c"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})


def tr_gates():
    FP = {"1/10": ([-5, -4, -3, -1, 0], [-30, -37, -38, -37, -30]), "0.15": ([-4, -3, -1, 0, 1], [-15, -35, -35, -26, 6])}
    SP = {"1/10": ([-5, -4.5, -4, -3], [-14.6, -10.1, -3.6, 3.7]), "0.15": ([-4, -3.5, -3, -2.5], [-7.0, -8.1, -4.1, 0.5])}
    GATE_S = {"1/10": -3.5, "0.15": -2.5}
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for ax, r in zip(axs, ("1/10", "0.15")):
        ax.axhline(0, color="k", lw=1)
        ax.plot(FP[r][0], [-v for v in FP[r][1]], "o-", color=NAVY, lw=3, ms=9, label="Stage 1 off (used at SNR ≤ 0 dB)")
        ax.plot(SP[r][0], [-v for v in SP[r][1]], "s-", color=ORANGE, lw=3, ms=9,
                label="speculative decode (used below −3.5 / −2.5 dB)")
        ax.set_xlim(-5.3, 1.3)
        ax.set_title(f"R = {r}", fontweight="bold")
        ax.set_xlabel("SNR [dB]")
        ax.set_ylim(-10, 42)
        ax.grid(True, ls=":", alpha=0.5)
    axs[0].set_ylabel("MACs per core saved [%]")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=13, frameon=False)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(os.path.join(HERE, "tr_gates.png"), dpi=200, facecolor="white")


def f5_thr():
    R = {r["point"]: r for r in json.load(open(os.path.join(HERE, "data", "fz_f5_17b16ea.json")))}
    fig, a = plt.subplots(figsize=(9, 4.8))
    ck = R["2/5 0.5 dB"]["groups"]["f"]["m"]["psn"]["ck"]
    q = [c["q"] for c in ck]
    a.plot(q, [c["med_wrong"] for c in ck], "s-", color=RED, lw=3, ms=8, label="decodes at a wrong hypothesis (median ψ)")
    a.plot(q, [c["med_right"] for c in ck], "o-", color=NAVY, lw=3, ms=8, label="decodes at the right hypothesis (median ψ)")
    c7 = [c for c in ck if abs(c["q"] - 0.7) < 1e-9][0]
    a.plot([0.7], [c7["th"][0]["t"]], "*", color=ORANGE, ms=22, label="chosen: q = 0.7, t = 0.774 (run.py FZS_T)")
    a.axvline(0.7, color=ORANGE, ls=":", lw=2)
    a.set_xlabel("share q of the frozen bits seen when ψ is checked")
    a.set_ylabel("ψ: mean frozen-bit penalty")
    a.set_title("R = 2/5, 0.5 dB (decode dumps)", fontweight="bold")
    a.grid(True, ls=":", alpha=0.5)
    a.legend(fontsize=12, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "f5_thr.png"), dpi=200, facecolor="white")


def f5_save():
    D = json.load(open(os.path.join(HERE, "data", "f5_paired_17b16ea.json")))
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for ax, r in zip(axs, ("2/5", "1/2")):
        pts = sorted((float(s), v) for s, v in D[r].items())
        x = list(range(len(pts)))
        y = [100 * (1 - v["fzs"] / v["base"]) for _, v in pts]
        for i, ((s, v), yy) in enumerate(zip(pts, y)):
            ax.bar(i, yy, color=NAVY if v["paired"] else "white", edgecolor=NAVY, lw=2, hatch=None if v["paired"] else "//")
            ax.text(i, yy + 0.6, f"{yy:.0f} %", ha="center", fontsize=13, color=NAVY, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{s:g}" for s, _ in pts])
        ax.set_title(f"R = {r}", fontweight="bold")
        ax.set_xlabel("SNR [dB]")
        ax.set_ylim(0, 25)
        ax.grid(True, axis="y", ls=":", alpha=0.5)
    axs[0].set_ylabel("MACs per core saved [%]")
    h = [plt.Rectangle((0, 0), 1, 1, color=NAVY), plt.Rectangle((0, 0), 1, 1, fc="white", ec=NAVY, hatch="//")]
    fig.legend(h, ["same packets with and without F5", "different packets"], loc="lower center", ncol=2, fontsize=13,
               frameon=False)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(os.path.join(HERE, "f5_save.png"), dpi=200, facecolor="white")


tr_gates()
f5_thr()
f5_save()
