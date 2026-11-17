"""Testing model vs presentation model vs the 128-pilot receivers -> BLIND_IMPLEMENTATION/testing/results/plots/cmp_*.png
(one figure per code rate; no simulation). Run from anywhere: py BLIND_IMPLEMENTATION/testing/plot_cmp.py
Data and receiver definitions: agg_cmp.py. 0-error points are not drawn (the legend gives the 0-error SNRs).
Fixed phase accounting (2026-11-13 runs) in every blind curve:
  testing model   "T nofast15", all packets of t-cnf10a/b/c (1/10) and t-cnf15a...e (0.15): BLER and MACs.
  presentation    MACs: "T base10" in t-cnf10d (1/10), t-cnf15d + t-cnf15f (0.15); 2/5, 1/2: the base arms of t-qfx25 +
                  t-cnf25 / t-qfx2 + t-cnf2 at their SNRs, the pre-fix parts elsewhere (2 phases: the fix changes nothing).
                  BLER: the merged big-sample blind_ber.json (BLER does not depend on the accounting).
  q_fix           "T base25_qfix" (t-qfx25 + t-ddq25), "T base2_qfix" (t-qfx2 + t-ddq2): BLER and MACs; at 1/10 and 0.15
                  "T base10_qfix" (t-qfx10 + t-ddq10) as a thin dashed line (BLER only where it has errors).
Pilot receivers and the genie curves are as before (est3)."""
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

OUT = os.path.join(HERE, "results", "plots", "original_study")
os.makedirs(OUT, exist_ok=True)
SNR_MIN = -5.5                          # as est3/plots.BLER_SNR_MIN
TEST = ("testing model", "#1f77b4", "s")
TEST_LAB = {"1/10": "testing model (T nofast15: fast path off at <= 0 dB)",
            "0.15": "testing model (fast path off at <= 0 dB; 4 phases below 0.5 dB, 2 above)"}
ADOPT = ("adopted testing model", "#e377c2", "d")
ADOPT_LAB = {"1/10": "adopted testing model (testing + spec11 below -3.5 dB; 64k paired per SNR)",
             "0.15": "adopted testing model (testing + spec11 below -2.5 dB; 64k paired per SNR)"}
PRES = ("presentation model (S blind final v2)", "#d62728", "o")
PRES25 = {"2/5": "presentation model (S blind final 2/5, 1/2, best-first 32)", "1/2": "presentation model (S blind final 2/5, 1/2)"}
QFX = ("presentation model + q_fix (phase-index fix)", "#8c564b", "h")
# Pilot receivers: the FAIR CRC search (" PM+all": decode at f_hat, then every neighbour in list-1 metric order;
# expected_fair.md) is the reference; the fixed-order search (|k| order, undetected floor) is drawn thin.
PIL = {"ML direct PM+all": ("ML direct, 128 pilots, fair CRC search (metric order)", "#2ca02c", "^"),
       "M&M PM+all": ("M&M, 128 pilots, fair CRC search (metric order)", "#ff7f0e", "v"),
       "ML direct": ("ML direct, 128 pilots, fixed-order CRC search", "#2ca02c", ""),
       "Joint ML Lh=3": ("joint CFO / channel ML (Lh = 3), 128 pilots, fixed-order CRC search", "#9467bd", ""),
       "cnn-cr": ("CNN classification + refinement, 128 pilots, fixed-order CRC search", "#17becf", ""),
       "M&M": ("M&M, 128 pilots, fixed-order CRC search", "#ff7f0e", "")}
THIN = dict(ls=":", lw=0.9, ms=0)
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
    T = C.testing_fix(rate)
    if T:
        bler_curve(ax, {s: (v["err"], v["n"]) for s, v in T.items()}, TEST_LAB[rate], TEST[1], TEST[2], lw=2.6, ms=9)
    pm = {s: v for s, v in C.merged(rate, C.EP.BLIND_RX[rate]).items() if s > SNR_MIN}
    bler_curve(ax, pm, PRES[0] if rate in ("1/10", "0.15") else PRES25[rate], PRES[1], PRES[2], lw=2.6, ms=7)
    Q = {s: (v["err"], v["n"]) for s, v in C.qfix(rate).items()}
    if rate in ("2/5", "1/2"):
        bler_curve(ax, Q, QFX[0], QFX[1], QFX[2], lw=2.2, ms=8)
    elif any(k for k, n in Q.values()):                    # 1/10, 0.15: thin dashed, only if it has errors
        bler_curve(ax, Q, QFX[0], QFX[1], QFX[2], ls="--", lw=1.2, ms=5)
    for src, (lab, c, m) in PIL.items():
        pts = {s: (v["err"], v["n"]) for s, v in P.get(src, {}).items() if s > SNR_MIN}
        if pts:
            bler_curve(ax, pts, lab, c, m, **(THIN if not m else dict(ls="--", lw=1.8, ms=6)))
    xr = set(pm) | {s for src in PIL for s in P.get(src, {}) if s > SNR_MIN}
    g = {s: v for s, v in C.merged(rate, C.GENIE_BLIND).items() if min(xr) <= s <= max(xr)}
    if g:
        bler_curve(ax, g, GEN[0][1], GEN[0][2], GEN[0][3], ls=":", lw=1.6, ms=8)
    ge = {s: (v["err"], v["n"]) for s, v in P.get("Genie CFO", {}).items() if s > SNR_MIN}
    if ge:
        bler_curve(ax, ge, GEN[1][1], GEN[1][2], GEN[1][3], ls=":", lw=1.6, ms=7)
    finish(ax, fig, f"BLER vs SNR, R = {rate}", "BLER", f"cmp_bler_R{tag(rate)}.png", ncol=1)


def _val(d, k):
    v = d.get(k)
    return np.nan if v is None else v / 1e6


def macs_fig(rate, total):
    """total: mean total MACs; else the STANDARD per-core count (scheduled, agg_cmp.SCHED), with the earlier count
    (crit_par: one core per cell, decodes one at a time) as thin dotted lines of the same colour for comparison."""
    k = "macs" if total else "core_s"
    fig, ax = plt.subplots(figsize=(10, 8.0))
    T = C.testing_fix(rate)
    Pr = {s: v for s, v in C.pres_fix_macs(rate).items() if s > SNR_MIN}
    if T:
        x = np.array(sorted(T))
        ax.plot(*gaps(x, np.array([_val(T[s], k) for s in x])), color=TEST[1], marker=TEST[2], lw=2.6, ms=9,
                label=TEST_LAB[rate])
    Ad = C.adopted(rate)                                  # 2026-11-14: + spec11 in the waterfall (testing_s11g)
    if Ad:
        xa = np.array(sorted(Ad))
        ax.plot(*gaps(xa, np.array([_val(Ad[s], k) for s in xa])), color=ADOPT[1], marker=ADOPT[2], lw=2.4, ms=7,
                label=ADOPT_LAB[rate])
    x = np.array(sorted(Pr))
    lab = PRES[0] if rate in ("1/10", "0.15") else PRES25[rate]
    ax.plot(*gaps(x, np.array([_val(Pr[s], k) for s in x])), color=PRES[1], marker=PRES[2], lw=2.6, ms=7, label=lab)
    Q = C.qfix(rate)
    xq = np.array(sorted(Q))
    sty = dict(lw=2.2, ms=8) if rate in ("2/5", "1/2") else dict(ls="--", lw=1.2, ms=5)
    ax.plot(*gaps(xq, np.array([_val(Q[s], k) for s in xq])), color=QFX[1], marker=QFX[2], label=QFX[0], **sty)
    if not total:                                        # the earlier count, for this round only
        for D_, c in ((T, TEST[1]), (Pr, PRES[1])):
            if D_:
                xs = np.array(sorted(D_))
                ax.plot(*gaps(xs, np.array([_val(D_[s], "core") for s in xs])), color=c, ls=":", lw=1.3,
                        label="same receiver, earlier count (one core per cell, decodes one at a time)"
                        if c == TEST[1] else None)
    P = C.pilots(rate)
    lo, hi = min(min(x), min(xq)), max(max(x), max(xq))
    if T:
        lo, hi = min(lo, min(T)), max(hi, max(T))
    for src, (lab, c, m) in PIL.items():
        kp = "core" if k == "core_s" else k              # the pilot receivers' count is already 4 decodes at once
        pts = sorted((s, v[kp]) for s, v in P.get(src, {}).items() if lo - 0.01 <= s <= hi + 0.01)
        if pts:
            sty = dict(marker=m, ls="--", lw=1.8, ms=6) if m else dict(ls=":", lw=0.9)
            ax.plot([p[0] for p in pts], [p[1] / 1e6 for p in pts], color=c, label=lab + " (4 decodes at once)", **sty)
    if total:
        finish(ax, fig, f"Total MACs vs SNR, R = {rate}", "mean total MACs per packet [M]", f"cmp_macs_total_R{tag(rate)}.png", ncol=1)
    else:
        sch = "per-hypothesis grid + 4 decodes at once" if rate in ("1/10", "0.15") else "4 decodes at once"
        finish(ax, fig, f"MACs per core vs SNR, R = {rate}", f"mean MACs per core [M] (32 cores, {sch})",
               f"cmp_macs_R{tag(rate)}.png", ncol=1)


if __name__ == "__main__":
    for rate in C.RATES:
        bler_fig(rate)
        macs_fig(rate, total=False)
        macs_fig(rate, total=True)
