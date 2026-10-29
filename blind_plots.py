"""Figures of the blind-CFO study, all in "Blind CFO estimation/<kind>/" (data from blind/logs and blind/results).

    py blind_plots.py
"""
import glob
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import blind_cfo as bc
import config as cfg

RATE_LABEL = {"1/10": "R = 1/10", "1/4": "R = 1/4", "1/3": "R = 1/3", "2/5": "R = 2/5", "1/2": "R = 1/2", "3/5": "R = 3/5", "2/3": "R = 2/3", "3/4": "R = 3/4"}
POLAR_CODE = {"1/10": "R=0.1,C16", "1/4": "R=1/4,C16", "1/3": "R=1/3,C16", "2/5": "R=2/5,C16", "1/2": "R=1/2,C16", "3/5": "R=3/5,C16", "2/3": "R=2/3,C16", "3/4": "R=3/4,C16"}
PLOT_RATES = ("1/10", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4")             # R = 1/4 dropped (BLER already at the CRC floor): R = 1/3 instead


def _save(fig, kind, name):
    out = bc.path(kind, name)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print("saved", out)


def _legend(ax, ncol=2):
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=ncol, frameon=False)


def _est_stats():
    p = bc.path("results", "est_stats.json")
    return sorted(json.load(open(p)), key=lambda r: r["snr"]) if os.path.exists(p) else None


def _split128():
    """128-pilot split NN: MSE (A.15 evaluation) and outage |error| > TOL."""
    s128 = json.load(open(os.path.join(bc.ROOT, "logs", "cfo_split_nn_L1024.json")))
    o128 = json.load(open(os.path.join(bc.ROOT, "logs", "cfo_outage_split.json")))
    j = [abs(t - bc.TOL) < 1e-12 for t in o128["thresholds"]].index(True)
    return (np.array(s128["snr"]), np.array(s128["est"]["nn"]["mse"]),
            np.array(o128["snr"]), np.array(o128["outage"]["split NN"][j]))


FAST = (("strongest", "#7f7f7f", ":", "x", "strongest 4th-power peak"),
        ("metric", "#d62728", "-", "o", "blind: best of the top 4 (>= 0.85 x max) by the left code metric"),
        ("nn_blind", "#ff7f0e", "-", "D", "blind: peak NN (heights, distance to the coarse CFO, SNR)"),
        ("pilots", "#000000", "--", "s", "24 pilots: best of the top 16 (>= 0.7 x max) by the pilot sum"),
        ("nn_pilots", "#1f77b4", "--", "^", "24 pilots: peak NN (+ pilot sum)"))


def coarse():
    """coarse/: the receivers' first stage, the 4th-power fast path (pre-MF at the autocorrelation CFO, 4th power,
    2 Newton steps, the peak picked among the top ones): CFO MSE, outage, and P(true CFO among the top peaks)."""
    E = _est_stats()
    if not E:
        return
    snr = np.array([r["snr"] for r in E])
    s1, m1, s2, o2 = _split128()
    for q, ylab, fname, title in (
            ("mse", "CFO MSE [(cycles/symbol)$^2$]", "blind_cfo_mse_vs_snr.png", "Fast-path CFO: MSE vs SNR"),
            ("outage", f"P(|CFO error| > {bc.TOL:.0e})", "blind_cfo_outage_vs_snr.png",
             "Fast-path CFO: outage vs SNR (an outage sends the packet to the search)")):
        fig, ax = plt.subplots(figsize=(11, 6.5))
        for k, c, ls, mk, lab in FAST:
            if k in E[0]["est"]:
                y = np.array([r["est"][k][q] for r in E])
                ax.semilogy(snr, np.where(y > 0, y, np.nan), ls=ls, color=c, marker=mk, lw=2.2, ms=5, label=lab)
        if q == "mse":
            ax.semilogy(s1, m1, "-.", color="#17becf", marker="h", lw=1.8, ms=5, label="128 pilots (12.5 %): split NN")
            ax.semilogy(snr, bc.crb_da(snr), "k:", lw=1.3, label="CRB, 1024 known symbols")
        else:
            y = 1 - np.array([r["inclusion"]["16"] for r in E])
            ax.semilogy(snr, y, ":", color="0.4", lw=1.6, label="true CFO not among the top 16 peaks (best possible)")
            ax.semilogy(s2, np.where(o2 > 0, o2, np.nan), "-.", color="#17becf", marker="h", lw=1.8, ms=5,
                        label="128 pilots (12.5 %): split NN")
        ax.set(xlabel="SNR (Es/N0) [dB]", ylabel=ylab, xlim=(snr.min() - 0.3, snr.max() + 0.3))
        fig.suptitle(title, fontsize=14, fontweight="bold")
        ax.set_title(f"{bc.N_SYM}-symbol packet, CFO ~ U[-0.2, 0.2], {E[0]['frames']} packets per SNR", fontsize=10.5,
                     color="0.3")
        _legend(ax, 1)
        fig.tight_layout()
        _save(fig, "coarse", fname)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for K, c in (("1", "#d62728"), ("4", "#ff7f0e"), ("16", "#2ca02c")):
        ax.plot(snr, [r["inclusion"][K] for r in E], "-", color=c, marker="o", lw=2.2, ms=5,
                label=f"true CFO among the top {K} peak" + ("s" if K != "1" else ""))
    for k, c, ls, mk, lab in FAST[1:]:
        if k in E[0]["est"]:
            ax.plot(snr, [1 - r["est"][k]["outage"] for r in E], ls=ls, color=c, marker=mk, lw=1.6, ms=4,
                    label=f"picked right: {lab}")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="probability", ylim=(0, 1.02))
    ax.grid(True, ls=":", alpha=0.6)
    fig.suptitle("Fast path: is the true CFO among the top 4th-power peaks, and is it picked?", fontsize=14,
                 fontweight="bold")
    _legend(ax, 1)
    fig.tight_layout()
    _save(fig, "coarse", "blind_peak_inclusion_vs_snr.png")


def metric():
    fs = sorted(glob.glob(bc.path("logs", "blind_metric_*_a.json")))
    if not fs:
        return
    data = [json.load(open(f)) for f in fs]
    data.sort(key=lambda d: bc.CODES[d["rate"]])
    colors = {"SC": "#d62728", "syndrome hard": "#8c564b", "syndrome soft w<=16": "#ff7f0e",
              "syndrome soft w<=32": "#2ca02c"}
    # rank-1 probability vs SNR
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for d, ls in zip(data, ("-", "--", ":")):
        for m, c in colors.items():
            ax.plot(d["snr"], d["metric"][m]["rank1"], ls=ls, color=c, marker="o", lw=2, ms=4,
                    label=f"{m}, {RATE_LABEL[d['rate']]}")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="P(true hypothesis ranked first)", ylim=(-0.02, 1.02))
    fig.suptitle("Decoder metrics: ranking the true (CFO, phase) first", fontsize=15, fontweight="bold")
    ax.set_title(f"among CFO offsets −{data[0]['G']}…{data[0]['G']} grid steps (7.5e-5) × 2 phase hypotheses (mod π)",
                 fontsize=10.5, color="0.3")
    _legend(ax, 3)
    fig.tight_layout()
    _save(fig, "metric", "blind_metric_rank1_vs_snr.png")
    # AUC vs CFO offset, one panel per rate
    fig, axs = plt.subplots(1, len(data), figsize=(6 * len(data), 5.5), squeeze=False)
    for ax, d in zip(axs[0], data):
        offs = [o for o in d["offsets"] if o > 0]
        for i, s in enumerate(d["snr"]):
            if i % 2:
                continue
            for m, c in (("SC", "#d62728"), ("syndrome soft w<=16", "#ff7f0e")):
                y = [d["metric"][m]["auc"][i][str(float(o))] for o in offs]
                ax.semilogx(np.array(offs) * d["step"], y, "-" if m == "SC" else "--", color=c,
                            alpha=0.35 + 0.65 * i / max(len(d["snr"]) - 1, 1), marker="o", ms=3, lw=1.8,
                            label=f"{'SC' if m == 'SC' else 'syndrome'} {s:g} dB")
        ax.axvline(bc.TOL, color="0.3", ls="-.", lw=1)
        ax.set(xlabel="|CFO error| of the competing hypothesis", ylabel="P(true scores better)", ylim=(0.4, 1.02))
        ax.set_title(RATE_LABEL[d["rate"]], fontsize=12)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        ax.legend(fontsize=8, ncol=2)
    fig.suptitle("Metric discrimination vs CFO error (dash-dot: code tolerance 1e-4)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, "metric", "blind_metric_auc_vs_cfo_error.png")


def subcode():
    fs = sorted(glob.glob(bc.path("logs", "blind_subcode_*_a.json")))
    if not fs:
        return
    data = sorted((json.load(open(f)) for f in fs), key=lambda d: bc.CODES[d["rate"]])
    fig, axs = plt.subplots(1, len(data), figsize=(7 * len(data), 5.5), squeeze=False)
    cols = {"2048": "#d62728", "1024": "#ff7f0e", "512": "#2ca02c"}
    for ax, d in zip(axs[0], data):
        offs = [o for o in d["offsets"] if o > 0]
        for i, s in enumerate(d["snr"]):
            for M in map(str, d["M"]):
                y = [d["auc"][M][i][str(float(o))] for o in offs]
                ax.semilogx(np.array(offs) * d["step"], y, color=cols[M], marker="o", ms=3, lw=1.8,
                            alpha=0.35 + 0.65 * i / max(len(d["snr"]) - 1, 1),
                            label=f"last {int(M) // 2} symbols ({d['frozen'][M]} frozen), {s:g} dB")
        ax.axvline(bc.TOL, color="0.3", ls="-.", lw=1)
        ax.set(xlabel="|CFO error| of the competing hypothesis", ylabel="P(true scores better)", ylim=(0.4, 1.02))
        ax.set_title(f"{RATE_LABEL[d['rate']]}, no interleaver", fontsize=12)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        ax.legend(fontsize=7.5, ncol=2)
    fig.suptitle("Sub-code SC metric: does a shorter sub-code tolerate a larger CFO error?", fontsize=14,
                 fontweight="bold")
    fig.tight_layout()
    _save(fig, "metric", "blind_subcode_auc_vs_cfo_error.png")


def _pilot_results():
    p = os.path.join(bc.ROOT, "lowrate", "results", "polar_results_ebn0_chain_L1024.npy")
    return list(np.load(p, allow_pickle=True)) if os.path.exists(p) else []


def dd_mse(res):
    """mse/: decision-directed CFO re-estimation after the CRC pass."""
    # decision-directed re-estimation after the CRC pass
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for rate, c in zip(PLOT_RATES, ("#1f77b4", "#2ca02c", "#9467bd", "#d62728", "#ff7f0e", "#8c564b", "#e377c2")):
        pts = sorted((x["snr"], x["rmse_final"], x["rmse_dd"]) for x in res
                     if x["rate"] == rate and x["rx"] == "4th power + SC search + CRC" and x["n_dd"] > 0)
        if pts:
            x, fi, dd = map(np.array, zip(*pts))
            ax.semilogy(x, fi ** 2, "--", color=c, marker="o", lw=1.6, ms=4,
                        label=f"{RATE_LABEL[rate]}: CFO used for the passing decode")
            ax.semilogy(x, dd ** 2, "-", color=c, marker="s", lw=2.2, ms=4,
                        label=f"{RATE_LABEL[rate]}: decision-directed, 1024 symbols")
    s = np.linspace(-2, 10, 50)
    ax.semilogy(s, bc.crb_da(s), "k:", lw=1.5, label="CRB, 1024 known symbols")
    ax.semilogy(s, bc.crb_da(s, 128), ":", color="0.5", lw=1.5, label="CRB, 128 contiguous pilots")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="CFO MSE [(cycles/symbol)²] (correctly decoded packets)")
    fig.suptitle("Decision-directed CFO re-estimation after the CRC pass", fontsize=15, fontweight="bold")
    ax.set_title("blind receiver: 4th power + SC-metric search + CRC", fontsize=10.5, color="0.3")
    _legend(ax)
    fig.tight_layout()
    _save(fig, "mse", "blind_dd_refinement_mse_vs_snr.png")




def main():
    if bc.STUDY == "small_cfo":                               # the small-CFO study has its own figures only
        small()
        bench()
        return
    coarse()
    metric()
    subcode()
    bler()
    macs_towers()
    estimation()




def estimation():
    """estimation/: the coarse CFO estimators (MSE) and the search stage (rank of the true cell in the receiver's
    posterior, blind vs 24 pilots), against the 128-pilot split NN."""
    E = _est_stats()
    if not E:
        return
    snr = np.array([r["snr"] for r in E])
    s1, m1, s2, o2 = _split128()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for k, c, mk, lab in (("acf", "#d62728", "o", "lag-4 autocorrelation of the 8-SPS samples (33k MACs, fast path)"),
                          ("spec2", "#ff7f0e", "s", "2-SPS spectral template (0.27 M MACs)"),
                          ("spec8", "#2ca02c", "^", "8-SPS spectral template (1.41 M MACs)")):
        ax.semilogy(snr, [r["est"][k]["mse"] for r in E], "-", color=c, marker=mk, lw=2.2, ms=5, label=lab)
    ax.semilogy(s1, m1, "-.", color="#17becf", marker="h", lw=1.8, ms=5, label="128 pilots (12.5 %): split NN")
    ax.axhline((1 / 24) ** 2, color="0.5", ls="--", lw=1)
    ax.text(snr.max(), (1 / 24) ** 2 * 1.5, "sigma = 1/24: the +-1/8 ambiguity of the 4th power at 3 sigma",
            ha="right", va="bottom", fontsize=9, color="0.4")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="CFO MSE [(cycles/symbol)$^2$]", xlim=(snr.min() - 0.3, snr.max() + 0.3))
    fig.suptitle("Coarse CFO estimators (no pilots): MSE vs SNR", fontsize=14, fontweight="bold")
    ax.set_title("they resolve the 1/4 ambiguity of the 4th power and centre the pre-MF correction / the search prior",
                 fontsize=10.5, color="0.3")
    _legend(ax, 1)
    fig.tight_layout()
    _save(fig, "estimation", "cfo_coarse_mse_vs_snr.png")
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for mode, c, mk in (("blind", "#d62728", "o"), ("pilots", "#000000", "s")):
        for K, ls in (("1", "-"), ("16", "--"), ("128", ":")):
            y = np.array([r["search"][f"{mode} 1/10"]["P_ge"][K] for r in E])
            who = "blind" if mode == "blind" else "24 pilots"
            ax.semilogy(snr, np.where(y > 0, y, np.nan), ls=ls, color=c, marker=mk, lw=2.0, ms=4,
                        label=f"{who}: true cell not among the first {K}")
    ax.semilogy(s2, np.where(o2 > 0, o2, np.nan), "-.", color="#17becf", marker="h", lw=1.8, ms=5,
                label=f"128 pilots: split NN, |error| > {bc.TOL:.0e}")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="probability", xlim=(snr.min() - 0.3, snr.max() + 0.3))
    fig.suptitle("Search stage: is the true cell among the first K cells of the posterior?", fontsize=14,
                 fontweight="bold")
    ax.set_title("R = 1/10 grid; the posterior of the packets the fast path does not deliver (2-SPS statistics)",
                 fontsize=10.5, color="0.3")
    _legend(ax, 2)
    fig.tight_layout()
    _save(fig, "estimation", "cfo_coarse_outage_vs_snr.png")
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for mode, c, mk in (("blind", "#d62728", "o"), ("pilots", "#000000", "s")):
        for rate, ls in (("1/10", "-"), ("2/5", "--")):
            who = "blind" if mode == "blind" else "24 pilots"
            ax.semilogy(snr, [r["search"][f"{mode} {rate}"]["mean"] + 1 for r in E], ls=ls, color=c, marker=mk,
                        lw=2.2, ms=5, label=f"{who}, R = {rate} grid")
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="mean number of cells scored until the true cell")
    fig.suptitle("Search size: mean rank of the true cell in the posterior", fontsize=14, fontweight="bold")
    ax.set_title("grid step from the code metric's basin (finer at R = 2/5); the mean is set by the rare far-off packets",
                 fontsize=10.5, color="0.3")
    _legend(ax, 2)
    fig.tight_layout()
    _save(fig, "estimation", "cfo_search_size_vs_snr.png")


def _premf_split():
    """Split-NN (and M&M) results with the pre-MF correction: the premf_split study, or in the small-CFO study its own
    runs (CFO_STUDY=small_cfo, merged)."""
    f = os.path.join(bc.ROOT, "small_cfo" if bc.STUDY == "small_cfo" else "premf_split", "results",
                     "polar_results_ebn0_chain_L1024.npy")
    return list(np.load(f, allow_pickle=True)) if os.path.exists(f) else []


TP_RX = (  # (label, source, receiver name, pilots, colour, style)
    ("Genie, pre-MF (known CFO, 0 pilots)", "blind", "Genie (known CFO, pre-MF correction)", 0, "0.4", ":"),
    ("Blind v3 (0 pilots)", "blind", "Best-first search v3 + CRC", 0, "#d62728", "-"),
    ("Blind v3 eco (0 pilots)", "blind", "v3 eco + CRC", 0, "#2ca02c", "-"),
    ("24 pilots + v3 (2.3 %)", "blind", "Pilots N3x8 + v3 + CRC", 24, "#ff7f0e", "--"),
    ("128 pilots: split NN (11 %)", "split", "Split pilots NN, quarter + CRC search (first pass)", 128, "#17becf", "--"),
    ("128 pilots: split NN + pre-MF (11 %)", "premf",
     "Split pilots NN, quarter, pre-MF correction + CRC search (first pass)", 128, "#1f77b4", "--"))
TP_RATES = ("1/10", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4")


def _bler_table(src, name):
    """{rate: {snr: (bler, frames, macs)}} of one receiver; blind-v3 rows without MACs take v3 fast's."""
    out = {}
    if src == "blind":
        res = json.load(open(bc.path("results", "blind_ber.json")))
        fast = {(x["rate"], x["snr"]): x.get("macs_per_frame") for x in res if x["rx"] == "Best-first search v3 fast + CRC"}
        for x in res:
            if x["rx"] == name and x["rate"] in TP_RATES:
                m = x.get("macs_per_frame") or (fast.get((x["rate"], x["snr"])) if "v3" in name else None)
                out.setdefault(x["rate"], {})[round(x["snr"], 2)] = (x["bler"], x["frames"], m)
    else:
        rows = _pilot_results() if src == "split" else _premf_split()
        inv = {v: k for k, v in POLAR_CODE.items()}
        for d in rows:
            if d["src"] == name and d["code"] in inv:
                ex = d.get("extra_decodes_per_frame") or 0.0
                m = 132_932 + (1 + ex) * (180_224 + 6_144) + (vp_premf() if src == "premf" else 0)
                out.setdefault(inv[d["code"]], {})[round(float(d["esn0"]), 2)] = (d["bler"], d["frames"], m)
    return out


def vp_premf():
    import blind_vp as vp
    return vp.PREMF_FAIR_MACS


def throughput(target=None):
    """Throughput vs SNR with the best rate per SNR: max_R R (1 - BLER_R) x 1024 / (1024 + pilots), information bits per
    transmitted symbol over QPSK (x2 bits per symbol), and the MACs per packet at the chosen rate. A rate counts at an
    SNR only where it was measured with >= 1e4 frames (BLER 0 there taken as 0)."""
    snrs = np.arange(-5.0, 8.01, 0.5)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6.5))
    rows = []
    for lab, src, name, K, c, ls in TP_RX:
        t = _bler_table(src, name)
        if not t:
            continue
        xs, tp, mc, rs = [], [], [], []
        for s in snrs:
            best = None
            for rate, pts in t.items():
                v = pts.get(round(s, 2))
                if v is None or v[1] < 1e4:
                    continue
                R = 1.0 / float(eval(rate)) if False else float(eval(rate))
                T = 2 * R * (1 - v[0]) * 1024 / (1024 + K)
                if best is None or T > best[0]:
                    best = (T, v[2], rate, v[0])
            if best:
                xs.append(s), tp.append(best[0]), mc.append(best[1]), rs.append(best[2])
                rows.append({"rx": lab, "snr": float(s), "rate": best[2], "bler": best[3], "throughput": best[0],
                             "macs": best[1]})
        if xs:
            a1.plot(xs, tp, ls=ls, color=c, marker="o", ms=3.5, lw=2.0, label=lab)
            m = [(x, y) for x, y in zip(xs, mc) if y]
            if m and "Genie" not in lab:
                a2.semilogy(*zip(*m), ls=ls, color=c, marker="o", ms=3.5, lw=2.0, label=lab)
    a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="throughput [information bits / symbol]", title="best rate per SNR")
    a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per packet at that rate", title="receiver cost")
    for ax in (a1, a2):
        ax.grid(True, which="both", ls=":", alpha=0.6)
        _legend(ax, 2)
    fig.suptitle("Throughput: blind CFO (v3) vs pilots, rate chosen per SNR", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, "throughput", "throughput_vs_snr.png")
    json.dump(rows, open(bc.path("results", "throughput.json"), "w"), indent=1)


# the final receivers, as (receiver, lowest SNR, highest SNR) segments of one receiver: the 24-pilot fast path at
# R = 1/10 is gated by snr >= -2 dB (s0_snr) and the runs are paired (same seeds), so below -2 dB it is exactly
# "rescue, rho_n" and the two runs join without approximation
_P = "Pilots N3x8 + v3 eco7, rescue, rho_n + CRC"
FINAL = {"blind": ("blind", {r: [("v3 eco7, rescue, rho_n + CRC", -99, 99)]
                                                                  for r in ("1/10", "2/5", "1/2")}),
         "pilots": ("pilots 3x8 (24 pilots, 2.3 %)",
                    {"1/10": [(_P, -99, -2.5), ("Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB + CRC", -2.5, 99)],
                     "2/5": [(_P, -99, 99)], "1/2": [(_P, -99, 99)]})}
TARGET = "Split pilots NN, quarter, pre-MF correction + CRC search (first pass)"
SPLIT = "Split pilots NN, quarter + CRC search (first pass)"
GENIE_P = "Genie (known CFO), pre-MF correction"
BEST_RATES = ("1/10", "2/5", "1/2")          # the rates of the current receivers (R = 1/3 was stopped before them)
NN_MACS, DEC_MACS, PREMF_DEROT = 132_932, 186_368, 33_792    # split NN; CA-SCL decode + LLRs; pre-MF de-rotation


def final_points(res, rate, mode):
    """(snr, bler, macs per packet, block errors, packets, undetected errors) of the final receiver of this mode at this rate."""
    return sorted((x["snr"], x["bler"], x.get("macs_per_frame"), x["frame_err"], x["frames"], x["undetected"]) for x in res
                  for rx, lo, hi in FINAL[mode][1][rate] if x["rate"] == rate and x["rx"] == rx and lo < x["snr"] < hi)


def bler():
    """bler/bler_vs_snr_R*.png and bler/macs_vs_snr_R*.png: BLER / MACs per packet vs SNR (separate figures), the 128-pilot split NN with the pre-MF correction
    (the target; without pre-MF where that study has no results) against the best blind and the best 24-pilot
    receivers, and the known-CFO bound."""
    p = bc.path("results", "blind_ber.json")
    if not os.path.exists(p):
        return
    res = json.load(open(p))
    P = _premf_split()
    for rate in BEST_RATES:
        code = POLAR_CODE[rate]
        tgt = [d for d in P if d["code"] == code and d["src"] == TARGET]
        premf = bool(tgt)
        if not premf:                                         # no pre-MF split-NN run at this rate: the plain one
            tgt = [d for d in _pilot_results() if d["code"] == code and d["src"] == SPLIT]
        F = {m: final_points(res, rate, m) for m in FINAL}
        if not tgt or not any(F.values()):
            continue
        snrs = sorted({p_[0] for v in F.values() for p_ in v})
        lo, hi = min(snrs) - 0.01, max(snrs) + 0.01
        f1, a1 = plt.subplots(figsize=(10, 6.5))
        f2, a2 = plt.subplots(figsize=(10, 6.5))
        pts = sorted((float(d["esn0"]), d["bler"], NN_MACS + (1 + (d.get("extra_decodes_per_frame") or 0)) * DEC_MACS
                      + (PREMF_DEROT if premf else 0)) for d in tgt if lo <= float(d["esn0"]) <= hi)
        lab = f"128 pilots (12.5 %): split NN{' + pre-MF' if premf else ''} (target)"
        if pts:
            x, y, m = map(np.array, zip(*pts))
            a1.semilogy(x, np.where(y > 0, y, np.nan), "-", color="#1f77b4", marker="D", ms=5, lw=2.2, label=lab)
            a2.semilogy(x, m, "-", color="#1f77b4", marker="D", ms=5, lw=2.2, label=lab)
        if premf:                                             # the same split NN without the pre-MF correction
            pts = sorted((float(d["esn0"]), d["bler"], NN_MACS + (1 + (d.get("extra_decodes_per_frame") or 0)) * DEC_MACS)
                         for d in _pilot_results() if d["code"] == code and d["src"] == SPLIT
                         and lo <= float(d["esn0"]) <= hi)
            if pts:
                x, y, m = map(np.array, zip(*pts))
                lab = "128 pilots (12.5 %): split NN, no pre-MF"
                a1.semilogy(x, np.where(y > 0, y, np.nan), ":", color="#17becf", marker="D", ms=4, lw=2.0, label=lab)
                a2.semilogy(x, m, ":", color="#17becf", marker="D", ms=4, lw=2.0, label=lab)
        for mode, c, ls, mk in (("blind", "#d62728", "-", "o"), ("pilots", "#000000", "--", "s")):
            lab = FINAL[mode][0]
            sty = dict(ls=ls, color=c, marker=mk, ms=5, lw=2.2, label=lab)
            pts = F[mode]
            q = [p_ for p_ in pts if p_[1] > 0]
            if q:
                a1.semilogy(*zip(*[(p_[0], p_[1]) for p_ in q]), **sty)
            q = [p_ for p_ in pts if p_[2]]
            if q:
                a2.semilogy(*zip(*[(p_[0], p_[2]) for p_ in q]), **sty)
        a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER")
        a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per packet (CFO estimation + decoding)")
        tail = f"{RATE_LABEL[rate]}, CRC-16, {bc.N_SYM}-symbol packet"
        for fig, ax, what, fn in ((f1, a1, "BLER", "bler_vs_snr"), (f2, a2, "Receiver cost", "macs_vs_snr")):
            ax.grid(True, which="both", ls=":", alpha=0.6)
            _legend(ax, 1)
            fig.suptitle(f"{what}, {tail}", fontsize=14, fontweight="bold")
            fig.tight_layout()
            _save(fig, "bler" if fn.startswith("bler") else "macs", f"{fn}_R{rate.replace('/', '_')}.png")
    dd_mse(res)


def macs_towers(rate="2/5", snrs=(0.5, 2.5)):
    """bler/macs_towers_R*.png: total MACs per packet of the split NN + pre-MF, blind and 24-pilot receivers, one bar
    per SNR side by side for every receiver."""
    res = json.load(open(bc.path("results", "blind_ber.json")))
    P = _premf_split()
    labs = ["128-pilot split NN\n+ pre-MF", "blind", "pilots 3x8"]
    V = np.full((len(labs), len(snrs)), np.nan)
    for j, s in enumerate(snrs):
        t = [d for d in P if d["code"] == POLAR_CODE[rate] and d["src"] == TARGET and abs(float(d["esn0"]) - s) < 1e-6]
        if t:
            V[0, j] = NN_MACS + PREMF_DEROT + (1 + (t[0].get("extra_decodes_per_frame") or 0)) * DEC_MACS
        for i, mode in ((1, "blind"), (2, "pilots")):
            pt = [p_ for p_ in final_points(res, rate, mode) if abs(p_[0] - s) < 1e-6]
            if pt:
                V[i, j] = pt[0][2]
    if np.isnan(V).all():
        return
    V /= 1e6
    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = np.arange(len(labs))
    w = 0.8 / len(snrs)
    for j, (s, c) in enumerate(zip(snrs, ("#1f77b4", "#ff7f0e", "#2ca02c"))):
        xs = x + (j - (len(snrs) - 1) / 2) * w
        ax.bar(xs, V[:, j], w * 0.94, color=c, edgecolor="white", lw=1.5, label=f"SNR (Es/N0) = {s:g} dB")
        for xi, v in zip(xs, V[:, j]):
            if np.isfinite(v):
                ax.text(xi, v + 0.012 * np.nanmax(V), f"{v:.2f} M", ha="center", va="bottom", fontsize=10.5)
    ax.set_xticks(x, labs, fontsize=12)
    ax.set_ylim(0, np.nanmax(V) * 1.12)
    ax.set(ylabel="MACs per packet [M]")
    ax.grid(True, axis="y", ls=":", alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=11, loc="upper right", frameon=False)
    fig.suptitle(f"Receiver cost per packet, {RATE_LABEL[rate]}, CRC-16, {bc.N_SYM}-symbol packet",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, "macs", f"macs_towers_R{rate.replace('/', '_')}.png")


# small-CFO study (BLIND_STUDY=small_cfo): (label, preference list of receivers, colour, style, marker); per rate the
# first receiver of the list with results there is drawn
# small-CFO study (BLIND_STUDY=small_cfo), user 2026-10-29: only the split NN, M&M, the best 24-pilot and the best
# blind receiver. Best = the cheapest one at about the split NN's BLER, per rate: (label, {rate: (what, receivers in
# order of preference)}, colour, style, marker); the first receiver with results there is drawn
_BL, _PL = "S blind, checkpoints", "S pilots N3x8, checkpoints, pilot score"
_J8 = ", coarse start, join top 16, phase hand-off, keep 2 phases, join top 8, rescue, tree cost + CRC"
# per rate: (description, receiver) in order of preference, newest first; the first with full-statistics results is
# drawn (smoke tests are never merged)
SMALL_RX = (("best blind (0 pilots)", 0, {
                "1/10": (("32 cores, batches of 32, coarse start + keep 2 phases", "S blind final v2"),
                         # "S blind final" (+ join top 8 / hand-off) held back: 1.0e-3 at -5 dB vs 1.8e-4 (diag-b, -c)
                         ("coarse start + join top 8 + phase hand-off + rescue", _BL + _J8),
                         ("coarse start + checkpoints + rescue", "S blind, checkpoints, coarse start, rescue + CRC")),
                "2/5": (("32 cores, checkpoint NN + best-first 32 + joint list", "S blind final 2/5, 1/2, best-first 32"),
                        ("32 cores, checkpoint NN + joint list", "S blind final 2/5, 1/2"),
                        ("checkpoint NN + best-first 32 + rescue", _BL + ", checkpoint NN, best-first 32, rescue, tree cost + CRC"),
                        ("checkpoint NN + rescue", _BL + ", checkpoint NN, rescue + CRC")),
                "1/2": (("32 cores, checkpoint NN + joint list", "S blind final 2/5, 1/2"),
                        ("checkpoint NN + rescue", _BL + ", checkpoint NN, rescue + CRC"))}, "#d62728", "-", "o"),
            ("best 3x8 (24 pilots, 2.3 %)", 24, {
                "1/10": (("32 cores, batches of 32, coarse start + join + pilot score", "S pilots final"),
                         ("coarse start + join top 8 + pilot score + rescue", _PL + _J8),
                         ("pilot score + rescue", _PL + ", rescue + CRC")),
                "2/5": (("32 cores, prior NN + pilot score + joint list", "S pilots final 2/5, 1/2"),
                        ("prior NN + pilot score + rescue", _PL + ", NN per rate, rescue + CRC")),
                "1/2": (("32 cores, prior NN + pilot score + joint list", "S pilots final 2/5, 1/2"),
                        ("prior NN + pilot score + rescue", _PL + ", NN per rate, rescue + CRC"))}, "#000000", "--", "s"))
SMALL_PILOTS = 128                                            # the references' known symbols (split NN, M&M)
SMALL_REF = ((TARGET, "128 pilots (12.5 %): split NN + pre-MF", "#1f77b4", "-", "D"),
             ("M&M, pre-MF correction + CRC search (first pass)", "128 pilots (12.5 %): M&M + pre-MF", "#ff7f0e", "-",
              "v"),
             ("Split pilots ML, est. phase, pre-MF + CRC search (first pass)",   # the satcom practice (DVB-RCS2-like
              "128 pilots (12.5 %): split ML, estimated phase", "#2ca02c", "-.", "^"),   # distributed known symbols)
             ("Split pilots ML, est. phase, pre-MF + CRC search (first pass) + re-encode check",   # + the blind
              "128 pilots (12.5 %): split ML + re-encoding check", "#006400", "-", "^"))           # receivers' check
SPLIT_ML_MACS = 35_000                                        # split-pilot ML (polar_ber_experiment EST_MACS)
SMALL_SNR_MIN = {"1/10": -5.0}                                # user: R = 1/10 only from -5 dB
MM_MACS = 24_704                                              # M&M on 128 known symbols (polar_ber_experiment EST_MACS)
PG_MACS = 2 * 1024 * 10 + 4 * 128 + 2 * 2 * 12 * 128 + 4 * 128   # FFT-1024 + 2 AM iterations + phase (BENCH_EST_MACS)


# preamble / pilot benchmarks (polar_ber_experiment BENCH, 128 known symbols, phase estimated from them unless noted):
# (source, label, colour, style, marker)
BENCH_SRC = (
    ("M&M, est. phase, pre-MF + CRC search (first pass)", "M&M (coarse)", "#ff7f0e", "-", "v"),
    ("M&M + L&R, est. phase, pre-MF + CRC search (first pass)", "M&M + Luise-Reggiannini (fine)", "#bcbd22", "-", "<"),
    ("M&M + Fitz, est. phase, pre-MF + CRC search (first pass)", "M&M + Fitz (fine)", "#8c564b", "-", ">"),
    ("ML periodogram (FFT + AM), est. phase, pre-MF + CRC search (first pass)", "ML periodogram + Aboutanios-Mulgrew",
     "#9467bd", "-", "P"),
    ("M&M + ML Newton, est. phase, pre-MF + code-aided EM + CRC search (first pass)", "M&M + Newton + code-aided EM",
     "#e377c2", "-", "X"),
    ("Split pilots ML, est. phase, pre-MF + CRC search (first pass)", "split pilots 2x64: ML", "#2ca02c", "-", "^"),
    ("Split pilots ML, est. phase, pre-MF + CRC search (first pass) + re-encode check",
     "split pilots 2x64: ML + re-encoding check", "#006400", "-", "^"),
    ("ML periodogram (FFT + AM), est. phase, pre-MF + CRC search (first pass) + re-encode check",
     "ML periodogram + AM + re-encoding check", "#9467bd", "--", "P"),
    ("Split pilots NN, est. phase, pre-MF + CRC search (first pass)", "split pilots 2x64: NN", "#17becf", "--", "o"),
    (TARGET, "split pilots 2x64: NN, genie phase (reference)", "#1f77b4", ":", "D"))


def bench():
    """bench/bench_R*.png: every 128-symbol preamble / pilot benchmark against the best blind and 3x8 receivers, BLER vs
    SNR as simulated (the known symbols are codeword symbols: no overhead) and vs Eb/N0 with the pilots' energy counted
    (128 extra symbols: +0.51 dB). Kay (below its threshold, BLER > 0.4 at every point) is left out."""
    p = bc.path("results", "blind_ber.json")
    res = json.load(open(p)) if os.path.exists(p) else []
    P = _premf_split()
    for rate in BEST_RATES:
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(17, 7), sharey=True)
        ebn0 = lambda x, n_p: np.asarray(x) + 10 * np.log10((bc.N_SYM + n_p) / bc.CODES[rate])
        lo = SMALL_SNR_MIN.get(rate, -99)
        for src, lab, c, ls, mk in BENCH_SRC:
            pts = sorted((float(d["esn0"]), d["bler"]) for d in P if d["code"] == POLAR_CODE[rate] and d["src"] == src
                         and float(d["esn0"]) >= lo and d["bler"] > 0)
            if pts:
                x, y = map(np.array, zip(*pts))
                sty = dict(ls=ls, color=c, marker=mk, ms=5, lw=2.0, label=f"128 pilots: {lab}")
                a1.semilogy(x, y, **sty)
                a2.semilogy(ebn0(x, SMALL_PILOTS), y, **sty)
        for lab, n_p, per, c, ls, mk in SMALL_RX:
            for what, rx in per.get(rate, ()):
                pts = sorted((x["snr"], x["bler"]) for x in res if x["rate"] == rate and x["rx"] == rx
                             and x["snr"] >= lo and x["bler"] > 0)
                if pts:
                    x, y = map(np.array, zip(*pts))
                    sty = dict(ls=ls, color=c, marker=mk, ms=6, lw=2.8, label=f"{lab}: {what}")
                    a1.semilogy(x, y, **sty)
                    a2.semilogy(ebn0(x, n_p), y, **sty)
                    break
        a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER", title="as simulated (known symbols inside the packet, no overhead)")
        a2.set(xlabel="Eb/N0 [dB] (the pilots' energy counted: 128 pilots +0.51 dB, 24 pilots +0.10 dB)",
               title="pilots sent as extra symbols (1024 + pilots)")
        for ax in (a1, a2):
            ax.grid(True, which="both", ls=":", alpha=0.6)
        a2.legend(fontsize=8.5, loc="lower left")
        fig.suptitle(f"Blind vs preamble / pilot CFO estimators, {RATE_LABEL[rate]}, CFO in [-{bc.MAX_CFO:g}, "
                     f"{bc.MAX_CFO:g}], CRC-16, {bc.N_SYM}-symbol packet", fontsize=13, fontweight="bold")
        fig.tight_layout()
        _save(fig, "bench", f"bench_R{rate.replace('/', '_')}.png")


def small():
    """Small-CFO study figures: bler/bler_vs_snr_R*.png and macs/macs_vs_snr_R*.png (CFO in [-0.03, 0.03])."""
    p = bc.path("results", "blind_ber.json")
    res = json.load(open(p)) if os.path.exists(p) else []
    P = _premf_split()
    tail = f"CFO in [-{bc.MAX_CFO:g}, {bc.MAX_CFO:g}], CRC-16, {bc.N_SYM}-symbol packet"
    for rate in BEST_RATES:
        f1, a1 = plt.subplots(figsize=(10, 6.5))
        f2, a2 = plt.subplots(figsize=(10, 6.5))
        f3, a3 = plt.subplots(figsize=(10, 6.5))
        f4, a4 = plt.subplots(figsize=(10, 6.5))
        ebn0 = lambda x, n_p: np.asarray(x) + 10 * np.log10((bc.N_SYM + n_p) / bc.CODES[rate])   # pilots' energy counted
        K = bc.CODES[rate] + 16
        lp_dec = DEC_MACS / 8 + 6144 / 8 + K * 16 * 4         # a CA-SCL-8 decode with its 8 paths on 8 cores (+ sort)
        drawn = False
        for src, lab, c, ls, mk in SMALL_REF:
            est = (NN_MACS if "NN" in src else PG_MACS if "periodogram" in src
                   else SPLIT_ML_MACS if "Split pilots ML" in src else MM_MACS)
            pts = sorted((float(d["esn0"]), d["bler"], est + PREMF_DEROT + (1 + (d.get("extra_decodes_per_frame") or 0))
                          * DEC_MACS) for d in P if d["code"] == POLAR_CODE[rate] and d["src"] == src
                         and float(d["esn0"]) >= SMALL_SNR_MIN.get(rate, -99))
            if pts:
                x, y, m = map(np.array, zip(*pts))
                sty = dict(ls=ls, color=c, marker=mk, ms=5, lw=2.2, label=lab)
                a1.semilogy(x, np.where(y > 0, y, np.nan), **sty)
                a2.semilogy(x, m, **sty)
                a3.semilogy(x, est + PREMF_DEROT + (m - est - PREMF_DEROT) / DEC_MACS * lp_dec, **sty)
                a4.semilogy(ebn0(x, SMALL_PILOTS), np.where(y > 0, y, np.nan), **sty)
                drawn = True
        for lab, n_p, per, c, ls, mk in SMALL_RX:
            pts = []
            for what, rx in per.get(rate, ()):
                pts = sorted((x["snr"], x["bler"], x.get("macs_per_frame"), x.get("crit_lp_macs_per_frame")) for x in res
                             if x["rate"] == rate and x["rx"] == rx and x["snr"] >= SMALL_SNR_MIN.get(rate, -99))
                if pts:
                    lab = f"{lab}: {what}"
                    break
            if not pts:
                continue
            sty = dict(ls=ls, color=c, marker=mk, ms=5, lw=2.2, label=lab)
            q = [p_ for p_ in pts if p_[1] > 0]
            if q:
                a1.semilogy(*zip(*[(p_[0], p_[1]) for p_ in q]), **sty)
                a4.semilogy(ebn0([p_[0] for p_ in q], n_p), [p_[1] for p_ in q], **sty)
            q = [p_ for p_ in pts if p_[2]]
            if q:
                a2.semilogy(*zip(*[(p_[0], p_[2]) for p_ in q]), **sty)
            q = [p_ for p_ in pts if p_[3]]
            if q:
                a3.semilogy(*zip(*[(p_[0], p_[3]) for p_ in q]), **sty)
            drawn = True
        if not drawn:
            plt.close(f1), plt.close(f2), plt.close(f3), plt.close(f4)
            continue
        a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER")
        a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per packet (CFO estimation + decoding)")
        a3.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per core (critical path, list paths of a decode in parallel)")
        a4.set(xlabel="Eb/N0 [dB] (energy of the pilot symbols included)", ylabel="BLER")
        for fig, ax, what, kind, fn in ((f1, a1, "BLER", "bler", "bler_vs_snr"), (f2, a2, "Receiver cost", "macs", "macs_vs_snr"),
                                        (f3, a3, "Receiver latency (critical path)", "macs", "macs_per_core_vs_snr"),
                                        (f4, a4, "BLER with the pilot overhead", "bler", "bler_vs_ebn0")):
            ax.grid(True, which="both", ls=":", alpha=0.6)
            _legend(ax, 1)
            fig.suptitle(f"{what}, {RATE_LABEL[rate]}, {tail}", fontsize=13, fontweight="bold")
            fig.tight_layout()
            _save(fig, kind, f"{fn}_R{rate.replace('/', '_')}.png")


if __name__ == "__main__":
    main()
