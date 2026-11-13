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

import part_filter  # noqa: E402
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
          "CRB 128 pilots": ("CFO error at the CRB (ideal estimator)", "0.4", "x", ":"),
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
STD_RATES = ("0.15", "2/5", "1/2")                   # the main rates (R = 0.15 replaces 1/10 at low SNR, user)
PLOT_RATES = ("1/10",) + STD_RATES                  # the presentation figures also keep R = 1/10 (user)
BLIND_DIR = os.path.join(C.ROOT, "small_cfo", "blind", "results")
BLIND_JSON = os.path.join(BLIND_DIR, "blind_ber.json")
BLIND_RX = {"1/10": "S blind final v2", "0.15": "S blind final v2", "2/5": "S blind final 2/5, 1/2, best-first 32",
            "1/2": "S blind final 2/5, 1/2"}
BLIND_LAB = "blind, 0 pilots (proposed)"
# the secondary BLER figure: blind, ML, M&M and two more modern estimators (same back-end)
MORE_SRC = (("ML direct", "ML (FFT 512 + 2 Newton), 128 pilots", "#2ca02c", "^"),
            ("M&M", "M&M, 128 pilots", "#ff7f0e", "v"),
            ("Joint ML Lh=3", "joint CFO / channel ML (Morelli-Mengali 2000), 128 pilots", "#9467bd", "s"),
            ("cnn-cr", "CNN classification + refinement, 128 pilots", "#1f77b4", "D"))
# the CRB-limited 128-pilot receiver: CFO error N(0, CRB), the rest as the ML receiver (run_bler "CRB 128 pilots")
CRB_SRC = ("CRB 128 pilots", "CFO error at the CRB (ideal 128-pilot estimator)", "k", "x")
EST_NAME = {"ML direct": "ML direct fft512 + newton x2", "M&M": "M&M", "Joint ML Lh=3": "Joint ML Lh=3 (taps -1..1)",
            "cnn-cr": "CNN classification + refinement"}
KP = 32                                              # decoder cores (the standard MACs-per-core model)
_SUM = ("frames", "frame_err", "undetected", "extra_decodes", "se_first", "se_final", "crc_pass", "crc_pass_wrong",
        "re_caught", "re_lost", "time_est")


def bler_rows():
    """est3 BLER parts (not smoke / superseded) summed per (rate, SNR, source): extra runs add packets."""
    tot = {}
    for p in glob.glob(C.path("results", "bler_*.json")):
        if "smoke" in os.path.basename(p):
            continue
        for r in json.load(open(p))["results"]:
            k = (r["rate"], r["snr"], r["src"])
            t = tot.setdefault(k, {"rate": r["rate"], "snr": r["snr"], "src": r["src"], **{f: 0 for f in _SUM}})
            for f in _SUM:
                t[f] += r.get(f, 0)
    for t in tot.values():
        n = t["frames"]
        t.update(bler=t["frame_err"] / n, rmse_final=float(np.sqrt(t["se_final"] / n)),
                 extra_decodes_per_frame=t["extra_decodes"] / n)
    return list(tot.values())


def blind_bler(rate, lo=-99, hi=99):
    """(snr, bler, frames) of the final blind receiver (merged blind_ber.json)."""
    blind = json.load(open(BLIND_JSON)) if os.path.exists(BLIND_JSON) else []
    return sorted((x["snr"], x["bler"], x["frames"]) for x in blind
                  if x["rate"] == rate and x["rx"] == BLIND_RX[rate] and lo <= x["snr"] <= hi)


def blind_parts(rate, need):
    """Rows of the final blind receiver at rate from the part files that carry the field `need` (prefix)."""
    rows = []
    for p in glob.glob(os.path.join(BLIND_DIR, "blind_ber_*.json")):
        if os.path.basename(p) == "blind_ber.json" or part_filter.test_part(os.path.basename(p)[len("blind_ber_"):-len(".json")]):
            continue                                      # smoke / testing parts (part_filter.py)
        rows += [r for r in json.load(open(p)) if r["rate"] == rate and r["rx"] == BLIND_RX[rate]
                 and any(k.startswith(need) for k in r)]
    return rows


def bler_plots():
    rows = bler_rows()
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
        bp = blind_bler(rate, min(r["snr"] for r in sel), max(r["snr"] for r in sel))
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


def _bler_fig(rate, srcs, name, save=None):
    """One BLER vs SNR figure: blind and the est3 sources srcs (label, colour, marker); 0-error points not drawn."""
    sel = [r for r in bler_rows() if r["rate"] == rate and r["snr"] > BLER_SNR_MIN]
    if not sel:
        return
    fig, ax = plt.subplots(figsize=(9, 6.5))
    bp = blind_bler(rate, min(r["snr"] for r in sel), max(r["snr"] for r in sel))
    if bp:
        x, y, _ = map(np.array, zip(*bp))
        ax.semilogy(x, np.where(y > 0, y, np.nan), color="#d62728", lw=3.0, marker="o", ms=7, label=BLIND_LAB)
    for src, lab, c, mk in srcs + (CRB_SRC,):
        pts = sorted((r["snr"], r["bler"]) for r in sel if r["src"] == src)
        if pts:
            x, y = map(np.array, zip(*pts))
            ls = ":" if src == CRB_SRC[0] else "--"
            ax.semilogy(x, np.where(y > 0, y, np.nan), color=c, ls=ls, lw=2.0, marker=mk, ms=7, label=lab)
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER", title=f"BLER vs SNR, R = {rate}")
    ax.title.set_fontsize(14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    if save:                                              # another folder's saver (blind_plots.modern)
        fig.tight_layout()
        save(fig)
    else:
        _save(fig, name)


def bler_best():
    """plots/bler_best_R*.png: blind, the best modern estimator (ML direct) and M&M."""
    for rate in PLOT_RATES:
        _bler_fig(rate, MORE_SRC[:2], f"bler_best_R{rate.replace('/', '_')}.png")


def bler_more():
    """plots/bler_more_R*.png (secondary): blind, ML, M&M, joint CFO / channel ML and the CNN."""
    for rate in PLOT_RATES:
        _bler_fig(rate, MORE_SRC, f"bler_more_R{rate.replace('/', '_')}.png")


PAR_DEC = KP // 8                                    # CA-SCL-8 decodes that fit on the cores at once


def pilot_macs(rate, src, x_dec, par=True):
    """(total MACs, MACs per core) per packet of a 128-pilot receiver: estimator, pre-MF correction, LS gain / phase
    on the pilots, (1 + x_dec) CA-SCL-8 decodes (each with LLRs and the gain / phase at its hypothesis) and one
    re-encoding check; per core the standard model: every sample-wise step / KP, one list path per core, bitonic
    2L -> L sort (10 stages for L = 8) at each information bit.
    Parallel CRC search (PAR_DEC = 32 cores / 8 list paths = 4 decodes at once, user 2026-11-12): the decode at the
    estimate first, then the extra decodes at the neighbouring CFOs 4 at a time -> per core 1 + x_dec / 4 decode
    rounds (from the mean extra decodes; per-packet counts are not stored, so the rounding up of a packet's last round
    is not modelled). Running 4 at once also decodes up to 3 hypotheses beyond the accepted one in the last round:
    total + min(x_dec, 1.5) decodes (an approximation: 1.5 = the mean waste of a round of 4, at most x_dec).
    par=False: the one-at-a-time model."""
    import blind_vp as vp
    d = json.load(open(C.path("results", "est.json")))
    rows = d["results"] if isinstance(d, dict) else d
    est = next(r["macs"] for r in rows if r["est"] == EST_NAME[src] and r["layout"] == "contig")
    K = C.CODES[rate] + 16
    gain = vp.MAC["cmul"] * C.L_P
    dec_t = vp.MAC["decode"] + vp.MAC["llr"] + gain
    dec_c = vp.MAC["decode"] / 8 + (vp.MAC["llr"] + gain) / KP + K * 10
    rounds, n_dec = (1 + x_dec / PAR_DEC, 1 + x_dec + min(x_dec, 1.5)) if par else (1 + x_dec, 1 + x_dec)
    total = est + vp.PREMF_FAIR_MACS + n_dec * dec_t + vp.MAC["reencode"]
    core = (est + vp.PREMF_FAIR_MACS + vp.MAC["reencode"]) / KP + rounds * dec_c
    return total, core


def macs_plot():
    """plots/macs_R*.png: total MACs per packet and MACs per core (critical path, the standard model) vs SNR."""
    rows = bler_rows()
    for rate in PLOT_RATES:
        sel = [r for r in rows if r["rate"] == rate and r["snr"] > BLER_SNR_MIN]
        bl = {}
        for r in blind_parts(rate, "crit_par_macs"):
            a = bl.setdefault(r["snr"], [0.0, 0.0, 0.0])
            a[0] += r["mac_frames"]
            a[1] += r["macs"]
            a[2] += r["crit_par_macs"]
        if not sel and not bl:
            continue
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.5))
        if bl:
            x = np.array(sorted(bl))
            n, t, cp = (np.array([bl[s][i] for s in x]) for i in range(3))
            for ax, y in ((a1, t / n), (a2, cp / n)):
                ax.semilogy(x, y, color="#d62728", lw=3.0, marker="o", ms=7, label=BLIND_LAB)
        for src, lab, c, mk in MORE_SRC:
            pts = sorted((r["snr"],) + pilot_macs(rate, src, r["extra_decodes_per_frame"]) for r in sel
                         if r["src"] == src)
            if pts:
                x, t, cp = map(np.array, zip(*pts))
                for ax, y in ((a1, t), (a2, cp)):
                    ax.semilogy(x, y, color=c, ls="--", lw=2.0, marker=mk, ms=6, label=lab + ", 4 decodes at once")
        a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per packet", title=f"Total MACs per packet, R = {rate}")
        a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per core",
               title=f"MACs per core (critical path, {KP} cores), R = {rate}")
        for ax in (a1, a2):
            ax.title.set_fontsize(13)
            ax.grid(True, which="both", ls=":", alpha=0.6)
        h, l = a1.get_legend_handles_labels()
        fig.legend(h, l, fontsize=9.5, loc="lower center", ncol=3, frameon=False)
        fig.tight_layout(rect=(0, 0.1, 1, 1))
        _save_raw(fig, f"macs_R{rate.replace('/', '_')}.png")


def _save_raw(fig, name):
    fig.savefig(C.path("plots", name), dpi=200)
    plt.close(fig)
    print("saved", C.path("plots", name))


PG_EDGES = 10 ** (4 + np.arange(101) / 20)           # small_rx "pg_" / "ph_" bins (0.05 decade from 1e4)
MG_EDGES = 10 ** (5 + np.arange(41) / 10)            # small_rx "mg_" / "mh_" bins (0.1 decade from 1e5)
CAP_REF = {"ML direct": "ML direct, 128 pilots", "Joint ML Lh=3": "joint CFO / channel ML, 128 pilots"}
PRES = os.path.join(C.ROOT, "BLIND_IMPLEMENTATION", "presentation")   # the presentation figures (user)
PRES_FIGS = [f"{k}_R{r.replace('/', '_')}.png" for k in ("bler_best", "bler_more", "macs", "bler_vs_cap", "stages", "stage_pass")
             for r in PLOT_RATES]


def _cap_curve(ax, h, n, edges, c, label):
    """BLER under a hard cap at each bin's upper edge: right decodes above the cap become misses."""
    miss = 1 - np.cumsum(h) / n
    m = np.nonzero(h)[0]
    lo = max(m.min() - 2, 0)
    miss = np.where(miss > 0.5 / n, miss, np.nan)        # 0 errors: not drawn (the curve ends at its last miss)
    ax.loglog(edges[1:][lo:], miss[lo:], color=c, lw=2.2, label=label)


def cap_plot():
    """plots/bler_vs_cap_R*.png: BLER of the blind receiver vs a hard cap on the MACs of each packet, left on the MACs
    per core (critical path, 32 cores), right on the total MACs. The search stops at its first accepted pass, so a cap
    C keeps exactly the right decodes that needed <= C (small_rx histograms of the right decodes: "pg_" per core,
    "mg_" total) and turns the rest into misses; the curves flatten at the BLER without a cap."""
    for rate in PLOT_RATES:
        per = {}
        for r in blind_parts(rate, "pg_"):
            a = per.setdefault(r["snr"], [0, np.zeros(100), np.zeros(40)])
            a[0] += r["frames"]
            for b in range(100):
                a[1][b] += r.get(f"pg_{b:02d}", 0)
            for b in range(40):
                a[2][b] += r.get(f"mg_{b:02d}", 0)
        if not per:
            continue
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.5))
        cols = plt.cm.viridis(np.linspace(0, 0.85, len(per)))
        for (snr, (n, hp, hm)), c in zip(sorted(per.items()), cols):
            lab = f"SNR = {snr:g} dB (no cap: BLER {1 - hp.sum() / n:.1e}, {n} packets)"
            _cap_curve(a1, hp, n, PG_EDGES, c, lab)
            _cap_curve(a2, hm, n, MG_EDGES, c, lab)
        # the 2 best pilot receivers (lowest BLER at a pilot-receiver cost): their mean MACs at the lowest cap SNR
        rows = [r for r in bler_rows() if r["rate"] == rate]
        s0 = min(per)
        for src, nm, c, _ in (s for s in MORE_SRC if s[0] in CAP_REF):
            xd = [r["extra_decodes_per_frame"] for r in rows if r["src"] == src and r["snr"] == s0]
            if not xd:
                continue
            t, cp = pilot_macs(rate, src, xd[0])
            for ax, v in ((a1, cp), (a2, t)):
                ax.axvline(v, color=c, ls=":", lw=2.2,
                           label=f"{CAP_REF[src]}: {v / 1e6:.2g} M (mean at {s0:g} dB)")
        a1.set(xlabel=f"hard cap on MACs per core (critical path, {KP} cores)", ylabel="BLER",
               title=f"BLER vs per-core MAC cap, R = {rate}")
        a2.set(xlabel="hard cap on total MACs per packet", ylabel="BLER", title=f"BLER vs total MAC cap, R = {rate}")
        for ax in (a1, a2):
            ax.title.set_fontsize(13)
            ax.grid(True, which="both", ls=":", alpha=0.6)
        for ax in (a1, a2):                              # each panel: its own reference values in its legend
            hh, ll = ax.get_legend_handles_labels()
            k = [i for i, x in enumerate(hh) if isinstance(x, plt.Line2D) and x.get_linestyle() == ":"]
            if k:
                ax.legend([hh[i] for i in k], [ll[i] for i in k], fontsize=9, loc="lower left", framealpha=0.9)
        h, l = a1.get_legend_handles_labels()
        k = [i for i, x in enumerate(h) if x.get_linestyle() != ":"]
        fig.legend([h[i] for i in k], [l[i] for i in k], fontsize=9.5, loc="lower center", ncol=2, frameon=False)
        fig.tight_layout(rect=(0, 0.12, 1, 1))
        _save_raw(fig, f"bler_vs_cap_R{rate.replace('/', '_')}.png")


STAGE_LAB = ("after Stage 1 (fast path)", "after Stage 2 (grid search, incl. its early decodes)",
             "after Stage 3 (final candidate decodes)", "after the rescue (= final BLER)")


def stage_plot():
    """plots/stages_R*.png: share of packets NOT yet decoded (right) after each stage of the blind receiver vs SNR
    (small_rx stage_1..5: the stage that accepted each right decode; rescue = final_post + fine_last)."""
    for rate in PLOT_RATES:
        acc = {}
        for r in blind_parts(rate, "stage_"):
            a = acc.setdefault(r["snr"], np.zeros(6))
            a[0] += r["stage_frames"]
            for s in range(1, 6):
                a[s] += r[f"stage_{s}"]
        if not acc:
            continue
        x = np.array(sorted(acc))
        A = np.array([acc[s] for s in x])
        n = A[:, 0]
        left = [1 - A[:, 1] / n, 1 - A[:, 1:3].sum(1) / n, 1 - A[:, 1:4].sum(1) / n, 1 - A[:, 1:6].sum(1) / n]
        fig, ax = plt.subplots(figsize=(9, 6.5))
        for y, lab, c, mk in zip(left, STAGE_LAB, ("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"), ("o", "s", "^", "D")):
            ax.semilogy(x, np.where(y > 0, y, np.nan), color=c, marker=mk, ms=7, lw=2.2, label=lab)
        ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="share of packets not decoded yet",
               title=f"Packets not decoded after each stage vs SNR, R = {rate}")
        ax.title.set_fontsize(14)
        ax.grid(True, which="both", ls=":", alpha=0.6)
        ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
        fig.tight_layout()
        _save_raw(fig, f"stages_R{rate.replace('/', '_')}.png")
        print(rate, "packets per SNR:", dict(zip(x.tolist(), n.astype(int).tolist())))


PASS_LAB = ("Stage 1 (fast path)", "Stage 2 (grid search, incl. its early decodes)",
            "Stage 3 (final candidate decodes)", "rescue (next 256 cells + fine grid)")


def stage_pass_plot():
    """plots/stage_pass_R*.png: probability that a packet which REACHES a stage is not decoded there (small_rx
    stage_1..5; rescue = stage 4 + 5): 1 - decoded at the stage / packets entering it. A decoded packet stops, so the
    packets entering stage k are the ones no earlier stage decoded; BLER = the product of the four."""
    for rate in PLOT_RATES:
        acc = {}
        for r in blind_parts(rate, "stage_"):
            a = acc.setdefault(r["snr"], np.zeros(6))
            a[0] += r["stage_frames"]
            for s in range(1, 6):
                a[s] += r[f"stage_{s}"]
        if not acc:
            continue
        x = np.array(sorted(acc))
        A = np.array([acc[s] for s in x])
        n = A[:, 0]
        dec = [A[:, 1], A[:, 2], A[:, 3], A[:, 4:6].sum(1)]
        miss = []
        ent = n.copy()                                        # packets entering the stage
        for d in dec:
            with np.errstate(invalid="ignore", divide="ignore"):
                miss.append(np.where(ent >= 20, 1 - d / ent, np.nan))   # < 20 packets reach it: not drawn
            ent = ent - d
        fig, ax = plt.subplots(figsize=(9, 6.5))
        for y, lab, c, mk in zip(miss, PASS_LAB, ("#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"), ("o", "s", "^", "v")):
            ax.semilogy(x, np.where(y > 0, y, np.nan), color=c, marker=mk, ms=7, lw=2.2, label=lab)
        ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="P(not decoded at the stage | packet reached it)", ylim=(None, 1.5),
               title=f"Probability of not decoding at each stage vs SNR, R = {rate}")
        ax.title.set_fontsize(14)
        ax.grid(True, which="both", ls=":", alpha=0.6)
        ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
        fig.tight_layout()
        _save_raw(fig, f"stage_pass_R{rate.replace('/', '_')}.png")


def presentation():
    """Copy the presentation figures into BLIND_IMPLEMENTATION/presentation/ (est3/plots keeps the originals)."""
    import shutil
    os.makedirs(PRES, exist_ok=True)
    for f in PRES_FIGS:
        src = C.path("plots", f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(PRES, f))
            print("copied", f)


if __name__ == "__main__":
    p = C.path("results", "est.json")
    if os.path.exists(p):
        est_plots(json.load(open(p)))
    training_plot()
    bler_plots()
    bler_best()
    bler_more()
    macs_plot()
    cap_plot()
    stage_plot()
    stage_pass_plot()
    presentation()
