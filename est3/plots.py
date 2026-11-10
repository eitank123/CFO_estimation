"""
est3 figures (est3/plots/), AWGN: py est3/plots.py

    rmse_contig.png        RMSE vs SNR, the estimators on the contiguous 128-symbol preamble + its CRB
    rmse_families.png      RMSE vs SNR of every family on its own 128-pilot layout + the CRB of each layout
    rmse_crb.png           RMSE / sqrt(CRB of the estimator's own layout) vs SNR
    bias.png               bias vs SNR
    outlier.png            P(|e| > 1/(2L)) and P(|e| > CRC search half-width) vs SNR
    errdist.png            CCDF of |e| at three SNRs
    ml_grid.png            Method 3 grid / interpolation variants (+ Jacobsen-Candan): RMSE / reference
    chanlen.png            Method 1 with Lh assumed taps: RMSE / its own CRB (Lh unknown taps), RMSE vs Lh
    nn_generalisation.png  the NNs' RMSE / CRB with the training SNRs marked
    training.png           CNN validation curves
    bler_R<rate>.png       BLER and residual CFO vs SNR (identical packets and back-end for every estimator)
    complexity.png         MACs and measured time per burst
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from est3 import common as C

TRAIN_SNRS = (-10.0, -7.0, -4.0, -1.0, 2.0, 5.0, 8.0, 11.0, 14.0)
TAIL = "AWGN, 128 pilot symbols inside the 1024-symbol packet, |f| <= 0.03"
# (estimator name in est.json, label, colour, marker, line style)
CONTIG = [("M&M", "M&M (existing baseline)", "#ff7f0e", "v", "-"),
          ("ML direct fft512 + newton x2", "Method 3: direct ML (FFT 512 + 2 Newton)", "#2ca02c", "^", "-"),
          ("Jacobsen-Candan (FFT 128)", "Jacobsen-Candan (FFT 128, 3-bin)", "#8c564b", "<", "--"),
          ("Joint ML Lh=3 (taps -1..1)", "Method 1: joint CFO/channel ML, Lh = 3", "#d62728", "o", "-"),
          ("Joint ML Lh=8 (taps -1..6)", "Method 1: joint CFO/channel ML, Lh = 8", "#e377c2", "o", "--"),
          ("Clustering NN (SSKC + SMDR-BPNN)", "Method 2: clustering NN (Li Zhen et al.)", "#9467bd", "s", "-"),
          ("CNN classification + refinement", "Method 2: CNN classification + refinement", "#1f77b4", "D", "-"),
          ("CNN direct regression", "Method 2: CNN direct regression", "#17becf", "D", "--")]
FAMILIES = [("ML direct fft512 + newton x2", "contiguous preamble: direct ML", "#2ca02c", "^", "-"),
            ("Schmidl-Cox / Moose [periodic]", "periodic preamble 8x16: Schmidl-Cox / Moose", "#bcbd22", "x", "-"),
            ("BLUE, Morelli-Mengali 1999 [periodic]", "periodic preamble 8x16: BLUE (Morelli-Mengali 1999)",
             "#7f7f7f", "P", "-"),
            ("Distributed ML [split2x64]", "2 x 64 pilot blocks: ML", "#1f77b4", "s", "-"),
            ("Distributed ML [dist4x32]", "4 x 32 pilot blocks: ML", "#9467bd", "s", "-"),
            ("DVB-S2 block phase-difference [dist4x32]", "4 x 32 pilot blocks: DVB-S2 phase-difference",
             "#9467bd", "D", "--"),
            ("Distributed ML [dist8x16]", "8 x 16 pilot blocks: ML", "#d62728", "s", "-"),
            ("DVB-S2 block phase-difference [dist8x16]", "8 x 16 pilot blocks: DVB-S2 phase-difference",
             "#d62728", "D", "--")]
CRB_LINES = [("contig", "contiguous / periodic", ":"), ("split2x64", "2 x 64", "-."), ("dist4x32", "4 x 32", "--"),
             ("dist8x16", "8 x 16", "-")]


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(C.path("plots", name), dpi=200)
    plt.close(fig)
    print("saved", C.path("plots", name))


def _rows(R, est):
    return sorted((r for r in R if r["est"] == est), key=lambda r: r["snr"])


def _grid(ax, legend=True, fs=8):
    ax.grid(True, which="both", ls=":", alpha=0.6)
    if legend:
        ax.legend(fontsize=fs)


def est_plots(d):
    R = d["results"]
    ref = _rows(R, "M&M")
    x0 = np.array([r["snr"] for r in ref])
    crb = {lay: np.sqrt([C.crb_layout(s, lay) for s in x0]) for lay, *_ in CRB_LINES}

    for fname, sets, lines in (("rmse_contig.png", CONTIG, CRB_LINES[:1]), ("rmse_families.png", FAMILIES, CRB_LINES)):
        fig, ax = plt.subplots(figsize=(10.5, 7.5))
        for est, lab, c, mk, ls in sets:
            rows = _rows(R, est)
            if rows:
                ax.semilogy([r["snr"] for r in rows], [r["rmse"] for r in rows], color=c, marker=mk, ls=ls, ms=4,
                            lw=1.8, label=lab)
        for lay, lab, ls in lines:
            ax.semilogy(x0, crb[lay], color="k", ls=ls, lw=1.2, label=f"sqrt CRB, {lab}")
        ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="CFO RMSE [cycles / symbol]", title=f"CFO RMSE, {TAIL}")
        _grid(ax)
        _save(fig, fname)

    allsets = CONTIG + FAMILIES[1:]
    lay_of = lambda est: next((r["layout"] for r in R if r["est"] == est), "contig")
    f2, a2 = plt.subplots(figsize=(10.5, 7.5))
    f3, a3 = plt.subplots(figsize=(10.5, 7.5))
    f4, (a4, a5) = plt.subplots(1, 2, figsize=(18, 7.5))
    for est, lab, c, mk, ls in allsets:
        rows = _rows(R, est)
        if not rows:
            continue
        xs = np.array([r["snr"] for r in rows])
        sty = dict(color=c, marker=mk, ls=ls, ms=4, lw=1.6, label=lab)
        a2.semilogy(xs, np.array([r["rmse"] for r in rows]) / np.sqrt([r["crb"] for r in rows]), **sty)
        a3.plot(xs, [r["bias"] for r in rows], **sty)
        a4.semilogy(xs, np.maximum([r["p_thr"][3] for r in rows], 1e-6), **sty)
        a5.semilogy(xs, np.maximum([r["p_beyond_search"] for r in rows], 1e-6), **sty)
    a2.axhline(1.0, color="k", lw=1)
    a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="RMSE / sqrt(CRB of its own pilot layout)", ylim=(0.8, 1e3),
           title=f"Efficiency relative to the CRB, {TAIL}")
    a3.axhline(0, color="k", lw=0.8)
    a3.set(xlabel="SNR (Es/N0) [dB]", ylabel="bias [cycles / symbol]", title=f"CFO bias, {TAIL}")
    a4.set(xlabel="SNR (Es/N0) [dB]", ylabel="P(|e| > 1/(2L) = 3.9e-3)", title="outliers: wrong lobe / cluster")
    a5.set(xlabel="SNR (Es/N0) [dB]", ylabel="P(|e| > CRC search half-width)",
           title="errors the CRC search cannot recover (4 x 1.3 sqrt CRB, contiguous)")
    for ax in (a2, a3, a4, a5):
        _grid(ax, fs=7.5)
    f4.suptitle(f"Outlier probability, {TAIL}", fontweight="bold")
    _save(f2, "rmse_crb.png"), _save(f3, "bias.png"), _save(f4, "outlier.png")

    edges = np.array(d["logb"])
    fig, axs = plt.subplots(1, 3, figsize=(21, 7), sharey=True)
    for ax, s in zip(axs, (-6, 0, 10)):
        for est, lab, c, mk, ls in allsets:
            rr = [r for r in _rows(R, est) if r["snr"] == s]
            if rr:
                ccdf = 1 - np.cumsum(np.array(rr[0]["loghist"], float)) / rr[0]["n"]
                ax.loglog(edges[1:], np.maximum(ccdf, 1e-6), color=c, ls=ls, lw=1.6, label=lab)
        ax.axvline(np.sqrt(C.crb_layout(s, "contig")), color="k", ls=":", label="sqrt CRB, contiguous")
        ax.set(xlabel="|CFO error| [cycles / symbol]", title=f"{s} dB", xlim=(1e-7, 1e-1))
        _grid(ax, legend=False)
    axs[0].set_ylabel("P(|e| > x)")
    axs[0].legend(fontsize=7)
    fig.suptitle(f"CFO error distribution (CCDF), {TAIL}", fontweight="bold")
    _save(fig, "errdist.png")

    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    refr = {r["snr"]: r["rmse"] for r in _rows(R, "ML direct fft4096 + golden")}
    names = sorted({r["est"] for r in R if r["est"].startswith("ML direct") and r["layout"] == "contig"})
    names.append("Jacobsen-Candan (FFT 128)")
    for i, nm in enumerate(names):
        rows = _rows(R, nm)
        if rows:
            ax.semilogy([r["snr"] for r in rows], [r["rmse"] / refr[r["snr"]] for r in rows], marker=".",
                        color=plt.cm.tab20(i % 20), label=f"{nm.replace('ML direct ', '')} ({rows[0]['macs']:,} MACs)")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="RMSE / RMSE of the reference (FFT 4096 + golden, 3 peaks)",
           title="Method 3: grid resolution and interpolation")
    _grid(ax)
    _save(fig, "ml_grid.png")

    fig, (b1, b2) = plt.subplots(1, 2, figsize=(18, 7.5))
    jn = sorted({r["est"] for r in R if r["est"].startswith("Joint ML")}, key=lambda s: int(s.split("Lh=")[1].split()[0]))
    for i, nm in enumerate(jn):
        rows = _rows(R, nm)
        b1.semilogy([r["snr"] for r in rows], [r["rmse"] / np.sqrt(r["crb_lh"]) for r in rows], marker="o", ms=3,
                    color=plt.cm.viridis(i / max(1, len(jn) - 1)), label=nm[9:])
    for s, c in zip((-6, 0, 6, 14), ("#1f77b4", "#2ca02c", "#d62728", "#9467bd")):
        pts = sorted((int(nm.split("Lh=")[1].split()[0]), r["rmse"], np.sqrt(r["crb_lh"])) for nm in jn
                     for r in _rows(R, nm) if r["snr"] == s)
        if pts:
            L_, rm, cb = zip(*pts)
            b2.semilogy(L_, rm, marker="o", color=c, label=f"{s} dB: RMSE")
            b2.semilogy(L_, cb, ls=":", color=c, label=f"{s} dB: sqrt CRB with Lh unknown taps")
    b1.axhline(1.0, color="k", lw=1)
    b1.set(xlabel="SNR (Es/N0) [dB]", ylabel="RMSE / sqrt(CRB with Lh unknown taps)", title="each assumed length")
    b2.set(xlabel="assumed channel length Lh [symbols]", ylabel="CFO RMSE", title="cost of the unneeded taps (AWGN)")
    _grid(b1), _grid(b2)
    fig.suptitle("Method 1: joint CFO / channel ML on AWGN with Lh assumed taps", fontweight="bold")
    _save(fig, "chanlen.png")

    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    for est, lab, c, mk, ls in CONTIG:
        if "NN" not in est:
            continue
        rows = _rows(R, est)
        if not rows:
            continue
        xs = np.array([r["snr"] for r in rows])
        y = np.array([r["rmse"] for r in rows]) / np.sqrt([r["crb"] for r in rows])
        ax.semilogy(xs, y, color=c, ls=ls, lw=1.5, label=lab)
        tr = np.isin(xs, TRAIN_SNRS)
        ax.semilogy(xs[tr], y[tr], "o", color=c, ms=7)
        ax.semilogy(xs[~tr], y[~tr], "x", color=c, ms=6)
    ax.axhline(1.0, color="k", lw=1)
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="RMSE / sqrt(CRB)",
           title="Method 2: generalisation to unseen SNRs (o: SNR used in training, x: never seen)")
    _grid(ax)
    _save(fig, "nn_generalisation.png")

    fig, (c1, c2) = plt.subplots(1, 2, figsize=(19, 8))
    names = [e for e, *_ in CONTIG + FAMILIES[1:]] + ["ML direct fft4096 + golden"]
    rr = [(nm, next((r for r in R if r["est"] == nm and r["snr"] == 0), None)) for nm in names]
    rr = [(nm, r) for nm, r in rr if r]
    c1.barh([nm for nm, _ in rr], [r["macs"] for _, r in rr], color="#4c72b0")
    c1.set(xscale="log", xlabel="real MACs per burst (analytic)", title="computational cost")
    c2.barh([nm for nm, _ in rr], [np.mean([x["us_per_burst"] for x in R if x["est"] == nm]) for nm, _ in rr],
            color="#dd8452")
    c2.set(xscale="log", xlabel="measured time per burst [us] (numpy / torch CPU, 1 thread, batches of 1000)",
           title="measured runtime")
    _grid(c1, False), _grid(c2, False)
    _save(fig, "complexity.png")


def training_plot():
    import torch
    fig, ax = plt.subplots(figsize=(10, 6.5))
    for k, c in (("cnn-cr", "#1f77b4"), ("cnn-reg", "#17becf")):
        p = C.path("models", f"{k}.pth")
        if os.path.exists(p):
            h = torch.load(p, map_location="cpu", weights_only=False)["hist"]
            ax.plot([x["epoch"] for x in h], [x["val_log_rmse"] for x in h], color=c, label=f"{k} (validation)")
    ax.set(xlabel="epoch", ylabel="mean over the training SNRs of log10 RMSE", title="Method 2 CNN training (AWGN)")
    _grid(ax)
    _save(fig, "training.png")


BL_SRC = {"Genie CFO": ("genie CFO (gain / phase still estimated)", "k", "", "-"),
          "M&M": ("M&M (existing baseline)", "#ff7f0e", "v", "-"),
          "ML direct": ("Method 3: direct ML", "#2ca02c", "^", "-"),
          "Joint ML Lh=3": ("Method 1: joint ML, Lh = 3", "#e377c2", "o", "-"),
          "Jacobsen-Candan": ("Jacobsen-Candan", "#8c564b", "<", "--"),
          "cluster": ("Method 2: clustering NN", "#9467bd", "s", "-"),
          "cnn-cr": ("Method 2: CNN classification + refinement", "#1f77b4", "D", "-"),
          "cnn-reg": ("Method 2: CNN regression", "#17becf", "D", "--"),
          "Schmidl-Cox / Moose": ("periodic 8x16: Schmidl-Cox / Moose", "#bcbd22", "x", "-"),
          "BLUE MM99": ("periodic 8x16: BLUE (Morelli-Mengali 1999)", "#7f7f7f", "P", "-"),
          "Distributed ML 2x64": ("2 x 64 blocks: ML", "#1f77b4", "s", ":"),
          "Distributed ML 4x32": ("4 x 32 blocks: ML", "#9467bd", "s", ":"),
          "DVB-S2 blocks 4x32": ("4 x 32 blocks: DVB-S2 phase-difference", "#9467bd", "D", "-."),
          "DVB-S2 blocks 8x16": ("8 x 16 blocks: DVB-S2 phase-difference", "#d62728", "D", "-.")}


# the final blind receivers (small_cfo study, 0 pilots), as in blind_plots.SMALL_RX
BLER_SNR_MIN = -5.5                                  # BLER plots start above -5.5 dB (user)
BLIND_JSON = os.path.join(C.ROOT, "small_cfo", "blind", "results", "blind_ber.json")
BLIND_RX = {"1/10": "S blind final v2", "2/5": "S blind final 2/5, 1/2, best-first 32", "1/2": "S blind final 2/5, 1/2"}


def bler_plots():
    rows = []
    for p in glob.glob(C.path("results", "bler_*.json")):
        if "smoke" not in os.path.basename(p):
            rows += json.load(open(p))["results"]
    blind = json.load(open(BLIND_JSON)) if os.path.exists(BLIND_JSON) else []
    keep = (1024 - C.L_P) / 1024                          # data share of a packet with 128 pilots inside it
    for rate in C.CODES:
        sel = [r for r in rows if r["rate"] == rate and r["snr"] > BLER_SNR_MIN]
        if not sel:
            continue
        fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(24, 8.5))
        for src, (lab, c, mk, ls) in BL_SRC.items():
            pts = sorted((r["snr"], r["bler"], r["rmse_final"], r["frames"]) for r in sel if r["src"] == src)
            if not pts:
                continue
            x, y, rf, n = map(np.array, zip(*pts))
            lab = "128 pilots: " + lab
            a1.semilogy(x, np.where(y > 0, y, np.nan), color=c, marker=mk, ls=ls, lw=1.6, label=lab)
            a2.plot(x, keep * (1 - y), color=c, marker=mk, ls=ls, lw=1.6, label=lab)
            a3.semilogy(x, rf, color=c, marker=mk, ls=ls, lw=1.6, label=lab)
        lo, hi = min(r["snr"] for r in sel), max(r["snr"] for r in sel)
        bp = sorted((x["snr"], x["bler"], x["frames"]) for x in blind
                    if x["rate"] == rate and x["rx"] == BLIND_RX[rate] and lo <= x["snr"] <= hi)
        if bp:
            x, y, n = map(np.array, zip(*bp))
            sty = dict(color="#d62728", lw=3, marker="o", ms=7)
            a1.semilogy(x, np.where(y > 0, y, np.nan), label="blind, 0 pilots (final receiver)", **sty)
            a2.plot(x, 1 - y, label="blind, 0 pilots (final receiver)", **sty)
        a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER", title="BLER (points with 0 errors are not drawn)")
        a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="delivered data per packet / A",
               title=f"throughput: (1 - BLER) x (1024 - pilots) / 1024  (128 pilots: x {keep:.3f})",
               ylim=(min(0.8, a2.get_ylim()[0]), 1.01))
        a3.set(xlabel="SNR (Es/N0) [dB]", ylabel="RMS residual CFO after the receiver [cycles / symbol]",
               title="residual CFO after compensation (estimate + CRC search)")
        a1.grid(True, which="both", ls=":", alpha=0.6), a2.grid(True, ls=":", alpha=0.6)
        a3.grid(True, which="both", ls=":", alpha=0.6)
        h, l = a1.get_legend_handles_labels()
        fig.legend(h, l, fontsize=10, loc="lower center", ncol=4, frameon=False)
        fig.suptitle(f"R = {rate} (A = {C.CODES[rate]} data bits), 1024-symbol polar packet, CRC-16, CA-SCL-8, same "
                     f"re-encoding check as blind\n{TAIL}", fontweight="bold", fontsize=13)
        fig.tight_layout(rect=(0, 0.13, 1, 1))
        fig.savefig(C.path("plots", f"bler_R{rate.replace('/', '_')}.png"), dpi=200)
        plt.close(fig)
        print("saved", C.path("plots", f"bler_R{rate.replace('/', '_')}.png"))


def bler_best():
    """plots/bler_best_R*.png: only blind, the best modern estimator (ML direct) and M&M, BLER vs SNR."""
    rows = []
    for p in glob.glob(C.path("results", "bler_*.json")):
        if "smoke" not in os.path.basename(p):
            rows += json.load(open(p))["results"]
    blind = json.load(open(BLIND_JSON)) if os.path.exists(BLIND_JSON) else []
    for rate in C.CODES:
        sel = [r for r in rows if r["rate"] == rate and r["snr"] > BLER_SNR_MIN]
        if not sel:
            continue
        lo, hi = min(r["snr"] for r in sel), max(r["snr"] for r in sel)
        curves = [("blind, 0 pilots (proposed)", "#d62728", "o", "-", 3.0,
                   sorted((x["snr"], x["bler"], x["frames"]) for x in blind
                          if x["rate"] == rate and x["rx"] == BLIND_RX[rate] and lo <= x["snr"] <= hi))]
        for src, lab, c, mk in (("ML direct", "ML (FFT 512 + 2 Newton), 128 pilots", "#2ca02c", "^"),
                                ("M&M", "M&M, 128 pilots", "#ff7f0e", "v")):
            curves.append((lab, c, mk, "--", 2.0, sorted((r["snr"], r["bler"], r["frames"]) for r in sel
                                                         if r["src"] == src)))
        fig, ax = plt.subplots(figsize=(9, 6.5))
        for lab, c, mk, ls, lw, pts in curves:
            if not pts:
                continue
            x, y, n = map(np.array, zip(*pts))
            ax.semilogy(x, np.where(y > 0, y, np.nan), color=c, ls=ls, lw=lw, marker=mk, ms=7, label=lab)  # 0: not drawn
        ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER", title=f"BLER vs. SNR, R={rate}")
        ax.grid(True, which="both", ls=":", alpha=0.6)
        ax.legend(fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
        ax.text(0.99, 0.99, "points with 0 errors are not drawn\nsame CRC-16 + re-encoding check for all",
                transform=ax.transAxes, ha="right", va="top", fontsize=8.5, color="0.35")
        _save(fig, f"bler_best_R{rate.replace('/', '_')}.png")


if __name__ == "__main__":
    p = C.path("results", "est.json")
    if os.path.exists(p):
        est_plots(json.load(open(p)))
    training_plot()
    bler_plots()
    bler_best()
