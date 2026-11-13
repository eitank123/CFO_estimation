"""Plots of the S experiments -> BLIND_IMPLEMENTATION/testing/results/plots/s_*.png (one figure per code rate).
Run from anywhere: py BLIND_IMPLEMENTATION/testing/plot_S.py   (no simulation; 0-error points are not drawn, the
legend gives errors / packets per SNR). Pilot receivers: est3/plots.pilot_macs on the 4-decodes-at-once model."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, PROJ)
import agg_S as A                      # noqa: E402
from est3 import plots as EP           # noqa: E402  (pilot_macs, bler_rows)

OUT = os.path.join(HERE, "results", "plots")
os.makedirs(OUT, exist_ok=True)
STY = {"S blind final v2": ("baseline (S blind final v2)", "#d62728", "o"),
       "T nofast": ("nofast (no fast-path decode)", "#1f77b4", "s"),
       "T nofast_spec": ("nofast_spec (+ speculative decode, z > 4)", "#2ca02c", "^"),
       "T nph4": ("nph4 (4 phases at every SNR)", "#9467bd", "D"),
       "T nofast_nph4": ("nofast_nph4", "#ff7f0e", "v"),
       "T nph15": ("nph15 (4 phases at R = 0.15)", "#8c564b", "P")}
MS = {"S blind final v2": 13, "T nofast": 9, "T nofast_spec": 6, "T nph4": 12, "T nofast_nph4": 8, "T nph15": 7}
PILOT = (("ML direct", "ML direct, 128 pilots (4 decodes at once)", "#555555", "x"),
         ("Joint ML Lh=3", "joint ML, 128 pilots (4 decodes at once)", "#17becf", "+"))


def gaps(x, y, max_gap=2.0):
    """Break the line where two measured SNRs are more than max_gap dB apart (no interpolation over unmeasured SNRs)."""
    xo, yo = [x[0]], [y[0]]
    for i in range(1, len(x)):
        if x[i] - x[i - 1] > max_gap:
            xo.append(np.nan)
            yo.append(np.nan)
        xo.append(x[i])
        yo.append(y[i])
    return np.array(xo), np.array(yo)


def by_rx(res, rate):
    d = {}
    for part, r, snr, rx, s, rows, b in res:
        if r == rate:
            d.setdefault(rx, {})[snr] = s
    return {k: d[k] for k in STY if k in d}


def tag(rate):
    return rate.replace("/", "_")


def bler_fig(rate, d, lim):
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for rx, pts in d.items():
        lab, c, m = STY[rx]
        x = np.array(sorted(pts))
        e = np.array([pts[s]["err"] for s in x])
        n = np.array([pts[s]["n"] for s in x])
        lab += "  (" + ", ".join(f"{a}/{b // 1000}k at {s:g}" for a, b, s in zip(e, n, x)) + ")"
        y = np.where(e > 0, e / n, np.nan)
        lo = np.array([A.cp(a, b)[0] for a, b in zip(e, n)])
        hi = np.array([A.cp(a, b)[1] for a, b in zip(e, n)])
        ax.errorbar(x, y, yerr=[np.where(e > 0, y - lo, np.nan), np.where(e > 0, hi - y, np.nan)], color=c, marker=m,
                    ms=MS[rx], lw=2, capsize=4, label=lab)
    ax.set_yscale("log")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER", title=f"BLER vs SNR, R = {rate}")
    ax.set_xlim(lim)
    ax.title.set_fontsize(14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False)
    fig.tight_layout()
    p = os.path.join(OUT, f"s_bler_R{tag(rate)}.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(p)


def pilot_lines(ax, rate, lim, col):
    rows = [r for r in EP.bler_rows() if r["rate"] == rate and lim[0] <= r["snr"] <= lim[1]]
    for src, lab, c, m in PILOT:
        pts = sorted((r["snr"], EP.pilot_macs(rate, src, r["extra_decodes_per_frame"])[col] / 1e6) for r in rows if r["src"] == src)
        if pts:
            ax.plot(*zip(*pts), color=c, marker=m, ls=":", lw=2, ms=7, label=lab)


def macs_fig(rate, d, lim, total):
    fig, ax = plt.subplots(figsize=(9, 6.8))
    for rx, pts in d.items():
        lab, c, m = STY[rx]
        x = np.array(sorted(pts))
        if total:
            ax.plot(*gaps(x, np.array([pts[s]["macs"] for s in x]) / 1e6), color=c, marker=m, lw=2.2, ms=MS[rx], label=lab)
        else:
            ax.plot(*gaps(x, np.array([pts[s]["core"] for s in x]) / 1e6), color=c, marker=m, lw=2.2, ms=MS[rx], label=lab)
            ax.plot(*gaps(x, np.array([pts[s]["core_h"] for s in x]) / 1e6), color=c, marker=m, lw=1.6, ms=6, ls="--", mfc="white")
    pilot_lines(ax, rate, lim, 0 if total else 1)
    if not total:
        ax.plot([], [], color="k", lw=1.6, ls="--", marker="o", mfc="white", ms=6,
                label="dashed: crit_par_h (one core per (cell, phase) hypothesis)")
    ax.set_yscale("log")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="mean total MACs per packet [M]" if total else "mean MACs per core [M] (32 cores)",
           title=f"Total MACs vs SNR, R = {rate}" if total else f"MACs per core vs SNR, R = {rate}")
    ax.set_xlim(lim)
    ax.title.set_fontsize(14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    fig.tight_layout()
    p = os.path.join(OUT, f"s_macs{'_total' if total else ''}_R{tag(rate)}.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(p)


def noise_fig():
    ns = A.noise()
    fig, (a0, a1, a2) = plt.subplots(1, 3, figsize=(17, 6.3))
    for key, (lab, c, m) in (("S blind final v2 [noise only]", STY["S blind final v2"]), ("T nph15 [noise only]", STY["T nph15"])):
        r = sorted((x for x in ns if x["rx"] == key), key=lambda x: x["snr"])
        x = np.array([q["snr"] for q in r])
        cnt = ", ".join(f"{q['fa_pk']}/{q['n']} at {q['snr']:g} dB" for q in r)
        ub = max(q["ub"] for q in r)
        # 0 false alarms: no point drawn (counts and the 95 % upper bound of the rate in the legend)
        a0.plot(x, [q["crc_pass"] / q["n"] for q in r], color=c, marker=m, lw=2.2, ms=MS[key.split(" [")[0]],
                label=f"{lab}: false alarms (accepted decodes) {cnt}, each < {ub:.1e} (95 %)")
        a1.plot(x, [q["macs"] / 1e6 for q in r], color=c, marker=m, lw=2.2, ms=MS[key.split(" [")[0]])
        a2.plot(x, [q["core"] / 1e6 for q in r], color=c, marker=m, lw=2.2, ms=MS[key.split(" [")[0]])
        a2.plot(x, [q["core_h"] / 1e6 for q in r], color=c, marker=m, lw=1.6, ms=6, ls="--", mfc="white")
    a0.set_yscale("log")
    a0.set_ylim(1e-2, 1)
    a0.set(xlabel="SNR (Es/N0) [dB]", ylabel="CRC passes per noise-only packet (all rejected by the re-encoding check)", title="Noise-only false alarms vs SNR, R = 0.15")
    a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="mean total MACs per noise-only packet [M]", title="Total MACs vs SNR, noise only, R = 0.15")
    a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="mean MACs per core [M] (32 cores; dashed: crit_par_h)",
           title="MACs per core vs SNR, noise only, R = 0.15")
    a1.set_ylim(0, 320)
    a2.set_ylim(0, 40)
    for a in (a0, a1, a2):
        a.set_xlim(-1.3, 0.3)
        a.set_xticks([-1, 0])
        a.title.set_fontsize(12)
        a.grid(True, which="both", ls=":", alpha=0.6)
    h, l = a0.get_legend_handles_labels()
    fig.legend(h, l, fontsize=9.5, loc="lower center", ncol=1, frameon=False)
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    p = os.path.join(OUT, "s_noise_R0.15.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(p)


if __name__ == "__main__":
    res = A.collect()
    for rate in ("1/10", "0.15"):                      # one figure per code rate (2/5 and 1/2 are not part of S)
        d = by_rx(res, rate)
        snrs = sorted({s for v in d.values() for s in v})
        lim = (snrs[0] - 0.3, snrs[-1] + 0.3)
        bler_fig(rate, d, lim)
        macs_fig(rate, d, lim, total=False)
        macs_fig(rate, d, lim, total=True)
    noise_fig()
