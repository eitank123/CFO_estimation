"""Result figures for the slides, from slides_eq/data/results_c90c5b7.json (full-chain-cfo c90c5b7).

    python slides_eq/plot_results.py

bler_all.png   measured BLER vs SNR: blind (0 pilots) vs ML on 128 pilots with the metric-ordered ("fair") CRC search
bler_cap.png   blind BLER with and without a hard cap on the MACs per core (2 M at R = 1/10, 1 M at R = 2/5, 1/2),
               same packets (cap_snr.json, presentation arm); the pilot receiver needs < 0.1 M per core, so no cap cuts it
macs_snr.png   total MACs per packet and MACs per core (32 cores) vs SNR; pilot MACs are the est3 model estimate
macs_cap.png   mean MACs per core with and without the cap. The capped mean is computed from the measured per-packet
               histogram of MACs per core (small_rx "ph_", 0.05-decade bins): mean - sum over bins above the cap of
               (bin centre - cap), not from separate capped runs.
Points with 0 errors are not drawn (log axis); lines join adjacent simulated SNRs that both had errors, and an isolated
point (an SNR with errors whose neighbouring simulated SNRs had none) is not drawn.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "results_c90c5b7.json")))
RATES = ("1/10", "2/5", "1/2")
NAVY, ORANGE, GREY = "#003366", "#E07B39", "#777777"
PILOT = "ML, 128 pilots, metric-ordered CRC search"
# 128-pilot receivers (est3, same back-end as blind). ML and M&M use the metric-ordered ("fair") CRC search; the joint
# ML and CNN runs exist only with the fixed |k|-order search. CRB: CFO error drawn at the CRB (ideal estimator). Genie:
# known CFO and phase, one decode (no MACs curve).
MODELS = (("ML direct PM+all", "ML (FFT + 2 Newton), metric-ordered search", ORANGE, "^", "--"),
          ("M&M PM+all", "Mengali & Morelli, metric-ordered search", "#8c564b", "v", "--"),
          ("Joint ML Lh=3", "joint CFO / channel ML (Morelli-Mengali 2000)", "#9467bd", "s", "--"),
          ("cnn-cr", "CNN classification + refinement", "#1f9e89", "D", "--"),
          ("CRB 128 pilots", "CFO error at the CRB (ideal 128-pilot estimator)", GREY, "x", ":"),
          ("Genie CFO", "genie: known CFO and phase, one decode", "k", "", ":"))
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})


def runs(pts):
    """pts: (snr, y) with y = 0 for no errors -> runs of >= 2 adjacent nonzero points."""
    out, run = [], []
    for s, y in pts + [(None, 0)]:
        if y > 0:
            run.append((s, y))
            continue
        if len(run) > 1:
            out.append(run)
        run = []
    return out


def draw(ax, pts, **kw):
    first = True
    for r in runs(pts):
        ax.plot(*zip(*r), **kw, **({} if first else {"label": None}))
        first = False


def finish(fig, axs, handles, labels, ncol=2):
    for ax in axs:
        ax.set_yscale("log")
        ax.grid(True, which="both", ls=":", alpha=0.5)
        ax.set_xlabel("SNR (Es/N0) [dB]")
    fig.legend(handles, labels, loc="lower center", ncol=ncol, fontsize=12, frameon=False)


def line(c, ls, mk, mfc=None):
    return plt.Line2D([], [], color=c, ls=ls, lw=2.2, marker=mk, ms=7, mfc=mfc or c)


def xlim(ax, rate):
    s = [p[0] for p in D[rate]["blind_cnt"] if p[2] >= 10000]
    pad = 0.05 * (max(s) - min(s))
    ax.set_xlim(min(s) - pad, max(s) + pad)


def in_range(rate, pts):
    s = [p[0] for p in D[rate]["blind_cnt"] if p[2] >= 10000]
    return [p for p in pts if min(s) - 1e-9 <= p[0] <= max(s) + 1e-9]


def bler_all():
    fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.7))
    for ax, rate in zip(axs, RATES):
        o = D[rate]
        for src, lab, c, mk, ls in MODELS[::-1]:
            pts = in_range(rate, [(s_, e / n) for s_, e, n, *_ in o[src]])
            draw(ax, pts, color=c, ls=ls, lw=1.8, marker=mk, ms=6)
        bl = [(s_, e / n) for s_, e, n, u in o["blind_cnt"] if n >= 10000]
        draw(ax, bl, color=NAVY, ls="-", lw=2.8, marker="o", ms=7)
        ax.set_title(f"R = {rate}", fontweight="bold")
        xlim(ax, rate)
    axs[0].set_ylabel("BLER")
    finish(fig, axs, [line(NAVY, "-", "o")] + [line(c, ls, mk) for _, _, c, mk, ls in MODELS],
           ["blind, 0 pilots"] + [lab for _, lab, *_ in MODELS], ncol=3)
    for lg in fig.legends:
        for t in lg.get_texts():
            t.set_fontsize(10.5)
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    fig.savefig(os.path.join(HERE, "bler_all.png"), dpi=200, facecolor="white")


def bler_cap():
    fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.7))
    for ax, rate in zip(axs, RATES):
        o, c = D[rate], D[rate]["cap"]
        draw(ax, [(s, b0) for s, n, b0, b1 in c["rows"]], color=NAVY, ls="--", lw=1.8, marker="o", ms=7, mfc="white")
        draw(ax, [(s, b1) for s, n, b0, b1 in c["rows"]], color=NAVY, ls="-", lw=2.4, marker="o", ms=7)
        ml = [(s, e / n) for s, e, n, *_ in o["ML direct PM+all"]]
        draw(ax, ml, color=ORANGE, ls=":", lw=2.0, marker="^", ms=6)
        ax.set_title(f"R = {rate}: cap {c['label']} MACs per core", fontweight="bold", fontsize=13)
        xlim(ax, rate)
    axs[0].set_ylabel("BLER")
    finish(fig, axs, [line(NAVY, "--", "o", "white"), line(NAVY, "-", "o"), line(ORANGE, ":", "^")],
           ["blind, no cap", "blind, hard cap on MACs per core (same packets)", PILOT + " (never reaches the cap)"],
           ncol=3)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "bler_cap.png"), dpi=200, facecolor="white")


def macs_snr():
    fig, axs = plt.subplots(2, 3, figsize=(13.2, 7.4))
    models = [m for m in MODELS if m[0] + " macs" in D["1/10"]]
    for j, rate in enumerate(RATES):
        o = D[rate]
        bm = o["blind_macs"]
        for i, (k, lab) in enumerate(((1, "total MACs per packet"), (2, "MACs per core (32 cores)"))):
            ax = axs[i, j]
            for src, _, c, mk, ls in models[::-1]:
                pm = in_range(rate, o[src + " macs"])
                ax.plot([p[0] for p in pm], [p[k] for p in pm], color=c, ls=ls, lw=1.8, marker=mk, ms=6)
            ax.plot([p[0] for p in bm], [p[k] for p in bm], color=NAVY, lw=2.8, marker="o", ms=7)
            ax.set_yscale("log")
            ax.grid(True, which="both", ls=":", alpha=0.5)
            if j == 0:
                ax.set_ylabel(lab)
            if i == 0:
                ax.set_title(f"R = {rate}", fontweight="bold")
            else:
                ax.set_xlabel("SNR (Es/N0) [dB]")
            xlim(ax, rate)
    fig.legend([line(NAVY, "-", "o")] + [line(c, ls, mk) for _, _, c, mk, ls in models],
               ["blind, 0 pilots"] + [lab for _, lab, *_ in models],
               loc="lower center", ncol=3, fontsize=10.5, frameon=False)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(os.path.join(HERE, "macs_snr.png"), dpi=200, facecolor="white")


CAPK = {"1/10": 46, "2/5": 40, "1/2": 40}         # histogram bin of the cap: cap = 10^(4 + k/20) = 2 M, 1 M, 1 M


def capped_means(rate):
    k = CAPK[rate]
    cap = 10 ** (4 + k / 20)
    mid = 10 ** (4 + (np.arange(100) + 0.5) / 20)
    out = []
    for s, h in sorted(D[rate]["hist"].items(), key=lambda x: float(x[0])):
        ph = np.array(h["ph"])
        excess = (ph[k:] * (mid[k:] - cap)).sum() / h["n"]
        out.append((float(s), h["crit_mean"], h["crit_mean"] - excess, int(ph[k:].sum()), h["n"]))
    return cap, out


def macs_cap():
    fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.7))
    for ax, rate in zip(axs, RATES):
        cap, rows = capped_means(rate)
        x = [r[0] for r in rows]
        ax.plot(x, [r[1] for r in rows], color=NAVY, ls="--", lw=1.8, marker="o", ms=7, mfc="white")
        ax.plot(x, [r[2] for r in rows], color=NAVY, ls="-", lw=2.4, marker="o", ms=7)
        pm = D[rate]["ML direct PM+all macs"]
        ax.plot([p[0] for p in pm], [p[2] for p in pm], color=ORANGE, ls="--", lw=2.0, marker="^", ms=6)
        ax.axhline(cap, color=GREY, ls="-.", lw=1.6)
        ax.text(0.03, 0.94, f"cap = {cap / 1e6:.0f} M per core", transform=ax.transAxes, color=GREY, fontsize=11, va="top")
        ax.set_title(f"R = {rate}", fontweight="bold")
        xlim(ax, rate)
        print(rate, [(r[0], round(r[1] / 1e6, 3), round(r[2] / 1e6, 3), r[3], r[4]) for r in rows])
    axs[0].set_ylabel("mean MACs per core (32 cores)")
    finish(fig, axs, [line(NAVY, "--", "o", "white"), line(NAVY, "-", "o"), line(ORANGE, "--", "^")],
           ["blind, no cap", "blind with the cap",
            PILOT], ncol=3)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "macs_cap.png"), dpi=200, facecolor="white")


if __name__ == "__main__":
    bler_all()
    bler_cap()
    macs_snr()
    macs_cap()
