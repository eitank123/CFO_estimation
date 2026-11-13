"""Testing model vs presentation model vs the 128-pilot receivers -> BLIND_IMPLEMENTATION/testing/results/plots/cmp_*.png
(one figure per code rate; no simulation). Run from anywhere: py BLIND_IMPLEMENTATION/testing/plot_cmp.py
Data and receiver definitions: agg_cmp.py. 0-error points are not drawn (the legend gives the 0-error SNRs); every
blind MAC curve is pre-fix accounting (phase_keep undercount, report_cmp.md)."""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker  # noqa: E402,F401

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agg_cmp as C                     # noqa: E402
import agg_S as A                       # noqa: E402

OUT = os.path.join(HERE, "results", "plots")
os.makedirs(OUT, exist_ok=True)
SNR_MIN = -5.5                          # as est3/plots.BLER_SNR_MIN
TEST = ("testing model", "#1f77b4", "s")
TEST_LAB = {"1/10": "testing model (fast path off at <= 0 dB)",
            "0.15": "testing model (fast path off at <= 0 dB, 4 phases: nofast / nofast_nph4 / nph15)"}
PRES = ("presentation model (S blind final v2)", "#d62728", "o")
PRES25 = {"2/5": "presentation model (S blind final 2/5, 1/2, best-first 32)", "1/2": "presentation model (S blind final 2/5, 1/2)"}
PIL = {"ML direct": ("ML direct, 128 pilots", "#2ca02c", "^"),
       "Joint ML Lh=3": ("joint CFO / channel ML (Lh = 3), 128 pilots", "#9467bd", "D"),
       "cnn-cr": ("CNN classification + refinement, 128 pilots", "#17becf", "P"),
       "M&M": ("M&M, 128 pilots", "#ff7f0e", "v")}
GEN = (("blind", "genie: known CFO and phase (blind packet)", "k", "*"),
       ("est3", "genie CFO, 128 pilots (est3 back-end)", "0.45", "x"))


def tag(rate):
    return rate.replace("/", "_")


def gaps(x, y, max_gap=2.0):
    """NaN between two measured SNRs more than max_gap dB apart (no line over unmeasured SNRs)."""
    xo, yo = [], []
    for i in range(len(x)):
        if i and x[i] - x[i - 1] > max_gap:
            xo.append(np.nan)
            yo.append(np.nan)
        xo.append(x[i])
        yo.append(y[i])
    return np.array(xo, float), np.array(yo, float)


def zero_note(pts):
    z = [f"{s:g}" for s, (k, n) in sorted(pts.items()) if k == 0]
    if not z:
        return ""
    ns = sorted({n for s, (k, n) in pts.items() if k == 0})
    nn = f"{ns[0] // 1000}k" if len(ns) == 1 else f"{ns[0] // 1000}-{ns[-1] // 1000}k"
    return f"; 0 errors in {nn} at {', '.join(z)} dB"


def bler_curve(ax, pts, lab, c, m, ls="-", lw=2.2, ms=7):
    """pts {snr: (errors, packets)}: points with errors and 95 % intervals; 0-error points left out."""
    x = np.array(sorted(pts))
    e = np.array([pts[s][0] for s in x], float)
    n = np.array([pts[s][1] for s in x], float)
    keep = e > 0
    y = np.where(keep, e / n, np.nan)
    lo = np.array([A.cp(int(a), int(b))[0] for a, b in zip(e, n)])
    hi = np.array([A.cp(int(a), int(b))[1] for a, b in zip(e, n)])
    xx, yy = gaps(x[keep], y[keep]) if keep.any() else (np.array([]), np.array([]))
    ax.plot(xx, yy, color=c, ls=ls, lw=lw, marker=m, ms=ms, label=lab + zero_note(pts))
    if keep.any():
        ax.errorbar(x[keep], y[keep], yerr=[y[keep] - lo[keep], hi[keep] - y[keep]], fmt="none", ecolor=c, elinewidth=1.0,
                    capsize=3, alpha=0.8)


def finish(ax, fig, title, ylabel, name, ncol=2):
    ax.set_yscale("log")
    lo, hi = ax.get_ylim()
    if hi / lo < 30:                                      # short log range: label the 2x, 3x, 5x ticks too
        f = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}" if round(v / 10 ** np.floor(np.log10(v)), 6) in (1, 2, 3, 5) else "")
        ax.yaxis.set_minor_formatter(f)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel=ylabel, title=title)
    ax.title.set_fontsize(14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=ncol, frameon=False)
    fig.tight_layout()
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print(p)


def bler_fig(rate):
    fig, ax = plt.subplots(figsize=(10, 7.6))
    P = C.pilots(rate)
    T = C.testing(rate)
    if T:
        bler_curve(ax, {s: (v[0]["err"], v[0]["n"]) for s, v in T.items()}, TEST_LAB[rate], TEST[1], TEST[2], lw=2.6, ms=9)
    pm = {s: v for s, v in C.merged(rate, C.EP.BLIND_RX[rate]).items() if s > SNR_MIN}
    bler_curve(ax, pm, PRES[0] if rate in ("1/10", "0.15") else PRES25[rate], PRES[1], PRES[2], lw=2.6, ms=7)
    for src, (lab, c, m) in PIL.items():
        pts = {s: (v["err"], v["n"]) for s, v in P.get(src, {}).items() if s > SNR_MIN}
        if pts:
            bler_curve(ax, pts, lab, c, m, ls="--", lw=1.8, ms=6)
    xr = set(pm) | {s for src in PIL for s in P.get(src, {}) if s > SNR_MIN}
    g = {s: v for s, v in C.merged(rate, C.GENIE_BLIND).items() if min(xr) <= s <= max(xr)}
    if g:
        bler_curve(ax, g, GEN[0][1], GEN[0][2], GEN[0][3], ls=":", lw=1.6, ms=8)
    ge = {s: (v["err"], v["n"]) for s, v in P.get("Genie CFO", {}).items() if s > SNR_MIN}
    if ge:
        bler_curve(ax, ge, GEN[1][1], GEN[1][2], GEN[1][3], ls=":", lw=1.6, ms=7)
    finish(ax, fig, f"BLER vs SNR, R = {rate}", "BLER", f"cmp_bler_R{tag(rate)}.png", ncol=1)


def macs_fig(rate, total):
    k = "macs" if total else "core"
    fig, ax = plt.subplots(figsize=(10, 7.2))
    T = C.testing(rate)
    if T:
        x = np.array(sorted(T))
        ax.plot(*gaps(x, np.array([T[s][0][k] for s in x]) / 1e6), color=TEST[1], marker=TEST[2], lw=2.6, ms=9,
                label=TEST_LAB[rate] + " (pre-fix accounting)")
        if not total:
            ax.plot(*gaps(x, np.array([T[s][0]["core_h"] for s in x]) / 1e6), color=TEST[1], marker=TEST[2], lw=1.6, ms=6,
                    ls="--", label="testing model, crit_par_h: one core per (cell, phase) hypothesis (pre-fix accounting)")
    Pr = {s: v for s, v in C.pres_macs(rate).items() if s > SNR_MIN}
    x = np.array(sorted(Pr))
    lab = PRES[0] if rate in ("1/10", "0.15") else PRES25[rate]
    ax.plot(*gaps(x, np.array([Pr[s][k] for s in x]) / 1e6), color=PRES[1], marker=PRES[2], lw=2.6, ms=7,
            label=lab + (" (pre-fix accounting)" if rate in ("1/10", "0.15") else ""))
    P = C.pilots(rate)
    lo, hi = min(x), max(x)
    if T:
        lo, hi = min(lo, min(T)), max(hi, max(T))
    for src, (lab, c, m) in PIL.items():
        pts = sorted((s, v[k]) for s, v in P.get(src, {}).items() if lo - 0.01 <= s <= hi + 0.01)
        if pts:
            ax.plot([p[0] for p in pts], [p[1] / 1e6 for p in pts], color=c, marker=m, ls="--", lw=1.8, ms=6,
                    label=lab + " (4 decodes at once)")
    if total:
        finish(ax, fig, f"Total MACs vs SNR, R = {rate}", "mean total MACs per packet [M]", f"cmp_macs_total_R{tag(rate)}.png")
    else:
        finish(ax, fig, f"MACs per core vs SNR, R = {rate}", "mean MACs per core [M] (32 cores, crit_par)", f"cmp_macs_R{tag(rate)}.png")


if __name__ == "__main__":
    for rate in C.RATES:
        bler_fig(rate)
        macs_fig(rate, total=False)
        macs_fig(rate, total=True)
