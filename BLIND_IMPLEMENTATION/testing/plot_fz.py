"""BLIND_IMPLEMENTATION/testing/: F5 plots from results/fz_f5.json (fz_analyze.py): ROC of the frozen-bit abort per
checkpoint, and MACs saved vs the right-packet loss (95 % upper bound). No simulation.

    py plot_fz.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.stats import beta  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(RES, "plots")
SHOW = ("0.15 -4 dB", "2/5 0.5 dB")
LBL = {"psn": "free (decoder's frozen PM)", "pn": "hard penalty / frozen bits", "pl": "hard penalty / sum |LLR|"}


def ub95(k, n):
    return float(beta.ppf(0.95, k + 1, n - k))


def main():
    R = {r["point"]: r for r in json.load(open(os.path.join(RES, "fz_f5.json")))}
    os.makedirs(OUT, exist_ok=True)
    cm = plt.get_cmap("viridis")

    # 1: ROC per checkpoint (free metric), CA-SCL-8 rows
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.4))
    for ax, pt in zip(axs, SHOW):
        r = R[pt]
        g = r["groups"]["f"]
        for i, ck in enumerate(g["m"]["psn"]["ck"]):
            n = ck["th"][0]["n"]
            pts = sorted({(l / n, w) for l, w, _, _ in ck["curve"] if l > 0})      # lost > 0 only (log axis)
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", ms=3, color=cm(i / 7),
                        label=f"{ck['q']:.2f} of frozen set (nb {ck['nb']}), AUC {ck['auc']:.3f}")
        ax.axvline(1e-4, color="r", ls="--", lw=1, label="1e-4 right-packet loss")
        ax.set_xscale("log")
        ax.set_xlabel(f"Right packets lost (fraction of {g['delivered_packets']})")
        ax.set_ylabel("Wrong CA-SCL-8 decodes stopped (free metric)")
        ax.set_title(f"Wrong decodes stopped vs right packets lost, R = {r['rate']} ({r['snr']:+g} dB)")
        ax.grid(True, which="both", alpha=0.3)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=7)
    fig.tight_layout()
    p1 = os.path.join(OUT, "fz_roc.png")
    fig.savefig(p1, dpi=130)
    plt.close(fig)

    # 2: total MACs saved vs right-packet loss (95 % upper bound), every metric at its best checkpoints
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.6))
    for ax, pt in zip(axs, SHOW):
        r = R[pt]
        g = r["groups"]["f"]
        n = g["delivered_packets"]
        for m, ls in (("psn", "-"), ("pn", "--"), ("pl", ":")):
            cks = g["m"][m]["ck"]
            best = sorted(range(len(cks)), key=lambda c: -cks[c]["th"][1]["save_tot"])[:2]
            for c in sorted(best):
                ck = cks[c]
                pts = sorted({(ub95(l, n), 100 * s) for l, _, s, _ in ck["curve"]})
                ax.plot([p[0] for p in pts], [p[1] for p in pts], ls, marker="o", ms=3, color=plt.get_cmap("tab10")(c),
                        label=f"{LBL[m]}, {ck['q']:.2f} of frozen set")
        u = g["m"]["psn"]["union0"]
        ax.plot([u["ub95"]], [100 * u["save_tot"]], "k*", ms=12, label="free, union of 7 checkpoints (in-sample, 0 lost)")
        if "cv" in r:
            v = r["cv"]["psn"]["union"]
            ax.plot([v["ub95"]], [100 * v["save_tot"]], "kD", ms=7,
                    label=f"free, union, thresholds from the other half ({v['lost']} lost)")
        ax.set_ylim(bottom=0)
        ax.axvline(1e-4, color="r", ls="--", lw=1, label="1e-4 right-packet loss")
        ax.axhline(5, color="k", ls="-.", lw=1, label="gate: 5 % of total MACs")
        ax.set_xscale("log")
        ax.set_xlabel("Right-packet loss, 95 % upper bound")
        ax.set_ylabel("Total MACs saved [%]")
        ax.set_title(f"MACs saved vs right-packet loss, R = {r['rate']} ({r['snr']:+g} dB)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=7)
    fig.tight_layout()
    p2 = os.path.join(OUT, "fz_saving_vs_loss.png")
    fig.savefig(p2, dpi=130)
    plt.close(fig)
    print(p1, p2)


if __name__ == "__main__":
    main()
