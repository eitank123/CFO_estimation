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
        ax.plot(*FP[r], "o-", color=NAVY, lw=2.5, ms=8, label="Stage 1 (fast path) switched off")
        ax.plot(*SP[r], "s-", color=ORANGE, lw=2.5, ms=8, label="speculative decode (spec11) switched on")
        ax.axvline(0.5, color=NAVY, ls=":", lw=2)
        ax.axvline(GATE_S[r], color=ORANGE, ls=":", lw=2)
        ax.text(0.45, 9, "fast path off\nbelow 0.5 dB ", ha="right", va="top", color=NAVY, fontsize=11)
        ax.text(GATE_S[r] - 0.05, 9, f"spec11 below\n{GATE_S[r]:g} dB ".replace("-", "−"), ha="right", va="top",
                color=ORANGE, fontsize=11)
        ax.set_title(f"R = {r}", fontweight="bold")
        ax.set_xlabel("SNR [dB]")
        ax.set_ylim(-45, 12)
        ax.grid(True, ls=":", alpha=0.5)
    axs[0].set_ylabel("MACs per core change [%]\n(paired packets)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=12, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "tr_gates.png"), dpi=200, facecolor="white")


def f5_thr():
    R = {r["point"]: r for r in json.load(open(os.path.join(HERE, "data", "fz_f5_17b16ea.json")))}
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.8))
    ck = R["2/5 0.5 dB"]["groups"]["f"]["m"]["psn"]["ck"]
    q = [c["q"] for c in ck]
    a.plot(q, [c["med_wrong"] for c in ck], "s-", color=RED, lw=2.5, ms=7, label="wrong decodes (median)")
    a.plot(q, [c["med_right"] for c in ck], "o-", color=NAVY, lw=2.5, ms=7, label="right decodes (median)")
    a.plot(q, [c["th"][0]["t"] for c in ck], "--", color=ORANGE, lw=2.5, label="threshold t: 0 right lost")
    a.set_xlabel("share q of the frozen bits seen")
    a.set_ylabel("ψ: mean frozen-bit penalty")
    a.set_title("R = 2/5, 0.5 dB: ψ separates", fontweight="bold")
    a.grid(True, ls=":", alpha=0.5)
    a.legend(fontsize=11)
    for pt, col, mk in (("2/5 0.5 dB", NAVY, "o"), ("1/2 2 dB", GREEN, "^"), ("0.15 -4 dB", GREY, "s"), ("1/10 -5 dB", ORANGE, "v")):
        c = R[pt]["groups"]["f"]["m"]["psn"]["ck"]
        lab = pt.replace("-", "−")
        b.plot([x["q"] for x in c], [100 * x["th"][0]["save_core"] for x in c], marker=mk, color=col, lw=2.3, ms=7,
               label=f"R = {lab}")
    b.axvline(0.7, color="k", ls=":", lw=1.5)
    b.text(0.71, 9.5, "chosen q = 0.7\n(R = 2/5, 1/2)", fontsize=11, va="bottom")
    b.set_xlabel("share q of the frozen bits seen")
    b.set_ylabel("MACs per core saved [%]")
    b.set_title("Saving at the 0-loss threshold", fontweight="bold")
    b.set_ylim(bottom=0)
    b.grid(True, ls=":", alpha=0.5)
    b.legend(fontsize=11, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "f5_thr.png"), dpi=200, facecolor="white")


def f5_save():
    D = json.load(open(os.path.join(HERE, "data", "f5_paired_17b16ea.json")))
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    for ax, r in zip(axs, ("2/5", "1/2")):
        pts = sorted((float(s), v) for s, v in D[r].items())
        x = [s for s, _ in pts]
        ax.plot(x, [v["base"] / 1e6 for _, v in pts], "--", color=GREY, lw=2, label="without early stop")
        ax.plot(x, [v["fzs"] / 1e6 for _, v in pts], "-", color=NAVY, lw=2.8, label="with F5 early stop")
        for s, v in pts:
            pr = v["paired"]
            ax.plot(s, v["base"] / 1e6, "o", color=GREY, ms=8, mfc=GREY if pr else "white")
            ax.plot(s, v["fzs"] / 1e6, "o", color=NAVY, ms=8, mfc=NAVY if pr else "white")
            ch = 100 * (v["fzs"] / v["base"] - 1)
            if abs(ch) >= 1:
                ax.annotate(f"{ch:+.0f} %".replace("-", "−"), (s, v["base"] / 1e6), textcoords="offset points",
                            xytext=(8, 6), fontsize=12, color=NAVY, fontweight="bold")
        ax.set_yscale("log")
        ax.minorticks_off()
        t = [0.05, 0.1, 0.2, 0.5, 1, 2]
        ax.set_yticks(t)
        ax.set_yticklabels([f"{v:g}" for v in t])
        ax.set_ylim(0.05, 2.5)
        ax.set_xlim(min(x) - 0.15, max(x) + 0.25)
        ax.set_title(f"R = {r}", fontweight="bold")
        ax.set_xlabel("SNR [dB]")
        ax.grid(True, ls=":", alpha=0.5)
    axs[0].set_ylabel("MACs per core [M]")
    h = [plt.Line2D([], [], color=GREY, ls="--", lw=2), plt.Line2D([], [], color=NAVY, lw=2.8),
         plt.Line2D([], [], color="k", marker="o", ls="none", ms=8), plt.Line2D([], [], color="k", marker="o", ls="none", ms=8, mfc="white")]
    fig.legend(h, ["without early stop", "with F5 early stop", "same packets (paired)", "different packets"],
               loc="lower center", ncol=4, fontsize=12, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "f5_save.png"), dpi=200, facecolor="white")


tr_gates()
f5_thr()
f5_save()
