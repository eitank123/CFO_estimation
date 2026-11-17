"""Histograms of MACs per core per packet with and without Stage 1 (the fast path) at R = 1/10 and 0.15, from the paired
confirmation runs (expected_cnf.md, fixed phase accounting): presentation receiver "S blind final v2" (fast path on,
parts t-cnf10d, t-cnf15d, t-cnf15f) vs "T nofast15" (fast path off at <= 0 dB; at 0.15 also 4 phase hypotheses;
parts t-cnf10a/b/c, t-cnf15a-e). Existing results only.

    py BLIND_IMPLEMENTATION/testing/plot_fastpath_hist.py

Data: small_rx pg_XX = right decodes per 0.05-decade bin of the critical-path MACs per core (crit_par, bin k covers
10^(4 + k/20) ... 10^(4 + (k+1)/20)); the mean in the legend is the standard scheduled count of ALL packets
(crit_par_h_d4a), the number quoted in the docs. Outputs: results/plots/original_study/fastpath_hist_R10.png, _R15.png.
"""
import glob
import json
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(os.path.dirname(HERE)), "small_cfo", "blind", "results")
OUT = os.path.join(HERE, "results", "plots", "original_study")
ON, OFF = "S blind final v2", "T nofast15"
PARTS = {"1/10": ["t-cnf10a", "t-cnf10b", "t-cnf10c", "t-cnf10d"],
         "0.15": ["t-cnf15a", "t-cnf15b", "t-cnf15c", "t-cnf15d", "t-cnf15e", "t-cnf15f"]}
SNRS = {"1/10": [-5.0, -4.0, -3.0, -1.0, 0.0], "0.15": [-4.0, -3.0, -1.0, 0.0, 1.0]}
COL = {ON: "#2a78d6", OFF: "#eb6834"}
LAB = {ON: "Stage 1 on (presentation receiver)", OFF: "Stage 1 skipped at <= 0 dB (testing receiver)"}


def load(rate):
    acc = defaultdict(lambda: dict(h=np.zeros(100), right=0, n=0, sched=0.0, mf=0))
    for p in PARTS[rate]:
        rows = json.load(open(os.path.join(RES, f"blind_ber_{p}.json")))
        rows = rows["results"] if isinstance(rows, dict) else rows
        for r in rows:
            if r["rate"] != rate or r["rx"] not in (ON, OFF) or not any(k.startswith("pg_") for k in r):
                continue
            a = acc[(r["rx"], r["snr"])]
            for b in range(100):
                a["h"][b] += r.get(f"pg_{b:02d}", 0)
            a["n"] += r["frames"]
            a["right"] += r["frames"] - r["frame_err"]
            if "crit_par_h_d4a_macs" in r:
                a["sched"] += r["crit_par_h_d4a_macs"]
                a["mf"] += r["mac_frames"]
    return acc


def fig(rate):
    acc = load(rate)
    snrs = [s for s in SNRS[rate] if (ON, s) in acc and (OFF, s) in acc]
    f, axs = plt.subplots(1, len(snrs), figsize=(4.1 * len(snrs), 4.6), sharey=False)
    edges = 10 ** (4 + np.arange(101) / 20) / 1e6                     # M MACs per core
    for ax, s in zip(np.atleast_1d(axs), snrs):
        means = {}
        for rx in (ON, OFF):
            a = acc[(rx, s)]
            frac = a["h"] / max(a["h"].sum(), 1)
            ax.stairs(frac, edges, color=COL[rx], lw=2, label=LAB[rx])
            means[rx] = a["sched"] / a["mf"] / 1e6 if a["mf"] else None
            if means[rx]:
                ax.axvline(means[rx], color=COL[rx], ls="--", lw=1.4)
        lo = edges[max(np.nonzero(acc[(ON, s)]["h"] + acc[(OFF, s)]["h"])[0].min() - 2, 0)]
        hi = edges[min(np.nonzero(acc[(ON, s)]["h"] + acc[(OFF, s)]["h"])[0].max() + 3, 100)]
        ax.set_xscale("log")
        ax.set_xlim(lo, hi)
        d = (means[OFF] / means[ON] - 1) * 100 if means[ON] and means[OFF] else None
        ax.set_title(f"SNR {s:+g} dB" + (f": mean {means[ON]:.3f} -> {means[OFF]:.3f} M ({d:+.0f} %)" if d is not None else ""),
                     fontsize=9.5)
        ax.set_xlabel("MACs per core per packet [M] (log)", fontsize=9.5)
        ax.grid(True, which="both", ls=":", color="#c3c2b7", alpha=0.7)
        n_on, n_off = acc[(ON, s)]["n"], acc[(OFF, s)]["n"]
        ax.text(0.98, 0.97, f"{n_on // 1000}k / {n_off // 1000}k packets", transform=ax.transAxes, ha="right",
                va="top", fontsize=8, color="#3d3d3a")
    np.atleast_1d(axs)[0].set_ylabel("share of right decodes per bin", fontsize=9.5)
    h, l = np.atleast_1d(axs)[0].get_legend_handles_labels()
    f.legend(h + [plt.Line2D([], [], color="#3d3d3a", ls="--")], l + ["mean MACs per core (scheduled count, all packets)"],
             loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.08))
    f.suptitle(f"MACs per core per packet with and without Stage 1, R = {rate}  (packets on vs off in each panel; histogram = critical-path "
               f"count of right decodes, dashed = scheduled mean)", fontsize=11.5)
    f.tight_layout(rect=(0, 0.03, 1, 0.95))
    p = os.path.join(OUT, f"fastpath_hist_R{ {'1/10': '10', '0.15': '15'}[rate]}.png")
    f.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(f)
    print(p)


if __name__ == "__main__":
    for r in ("1/10", "0.15"):
        fig(r)
