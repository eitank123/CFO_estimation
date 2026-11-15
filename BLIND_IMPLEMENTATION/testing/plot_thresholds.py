"""BLIND_IMPLEMENTATION/testing/: why each threshold has its value, one plain figure per decision.

    py BLIND_IMPLEMENTATION/testing/plot_thresholds.py

results/plots/thresholds/
  thr_gate_<point>.png   retry gate: x = share of the code-aided retries the gate skips, left = MACs per core saved,
                         right = BLER (with the gate vs without); the two chosen settings marked and explained.
                         Offline replay on the test packets of the decode dumps.
  thr_spec_rho.png       speculative decode: rho / threshold of right and wrong speculative CRC passes, the three
                         regions (rejected anyway / rejected only by the 1.1 factor / accepted) labelled with counts.
  thr_fastpath_R*.png    fast-path switch: change in MACs per core when the fast path is off, per SNR, and the switch.
"""
import collections
import glob
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(ROOT, "small_cfo", "blind", "results")
PL = os.path.join(HERE, "results", "plots", "thresholds")
os.makedirs(PL, exist_ok=True)
BLUE, ORANGE, GREY, GREEN, RED = "#2a78b8", "#e07b28", "#5a5a5a", "#2e9e4f", "#c8423b"
plt.rcParams.update({"font.size": 11})


def gate():
    import nn_offline as no
    import nn_b_export as nx
    G = json.load(open(os.path.join(HERE, "results", "nn_b_gate.json")))
    for name, rate, snr, part, pat in no.POINTS:
        D, P, meta = no.load(part, pat)
        D = no.prep(D, P)
        C = no.costs(rate)
        md = no.measured_dec(D)
        if md is not None:
            C["retry"] += md - C["dec"]
            C["dec"] = md
        D["rem"] = no.rem_after(D, P, C)
        nch = int(P["chunk"].max()) + 1
        test_pk = P["chunk"] >= nch - 2
        g = G[rate]
        rr = np.where(D["retry"])[0]
        Z = np.clip(np.nan_to_num((nx.X_of(D, rr) - np.array(g["mu"])) / np.array(g["sd"]), nan=0.0), -20, 20)
        sB = np.full(len(D["pk"]), np.inf)
        sB[rr] = Z @ np.array(g["w"]) + g["b"]
        sc = sB[rr]
        npk = int(test_pk.sum())
        e0 = int((~P["right"][test_pk]).sum())
        tt = np.unique(np.r_[np.percentile(sc, np.linspace(0, 99.95, 40)), g["thr"]["0.001"], g["thr"]["0.01"], sc.max() + 1])
        rows = []
        for t in tt:
            r = no.replay(D, P, C, test_pk, sB=sB, tB=t, nn_macs=nx.GATE_MACS)
            rows.append((100 * r["skipped"] / max(r["retries"], 1), r["saved_pct"], (e0 + r["lost"]) / npk, t))
        rows.sort()
        x, sv, bl, th = map(np.array, zip(*rows))
        b0 = e0 / npk
        fig, ax = plt.subplots(figsize=(10, 6))
        ax2 = ax.twinx()
        ax.plot(x, sv, color=BLUE, lw=2.5, label="MACs per core saved [%] (left axis)")
        ax2.semilogy(x, np.maximum(bl, 1e-6), color=ORANGE, lw=2.5, label="BLER with the gate (right axis)")
        ax2.axhline(b0, color=ORANGE, ls="--", lw=1.5, label=f"BLER without the gate: {b0:.1e}")
        worse = bl > b0 * 1.0001
        if worse.any():
            x0 = x[np.argmax(worse)]
            ax.axvspan(x0, 100, color=RED, alpha=0.08)
            ax.text(x0 - 0.5, 0.02, "BLER rises here ->", color=RED, fontsize=10, ha="right",
                    transform=ax.get_xaxis_transform())
        for f, lab, mk in (("0.01", "chosen setting A (1 % point)", "o"), ("0.001", "safer setting B (0.1 % point)", "s")):
            j = int(np.argmin(np.abs(th - g["thr"][f])))
            ax.plot(x[j], sv[j], mk, color="k", ms=10, zorder=5)
            ax.annotate(f"{lab}\nskips {x[j]:.1f} % of retries\nsaves {sv[j]:.1f} % MACs per core\n"
                        f"BLER {bl[j]:.1e} ({'unchanged' if bl[j] <= b0 * 1.0001 else 'higher'})",
                        (x[j], sv[j]), xytext=(0.03, 0.95 if f == "0.01" else 0.62), va="top",
                        textcoords="axes fraction", fontsize=9.5,
                        arrowprops=dict(arrowstyle="->", color="k"), bbox=dict(fc="white", ec=GREY, alpha=0.9))
        lo = max(0, x[sv > 0.2].min() - 5) if (sv > 0.2).any() else 0
        ax.set_xlim(lo, 100.5)
        ax.set_ylim(0, max(5, sv.max() * 1.25))
        ax.set_xlabel("share of the code-aided retries skipped by the gate [%]")
        ax.set_ylabel("MACs per core saved [%]", color=BLUE)
        ax2.set_ylabel("BLER", color=ORANGE)
        ax.set_title(f"Retry gate: MAC saving and BLER vs retries skipped, R = {rate}, SNR = {snr:g} dB")
        ax.grid(alpha=0.3)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9.5)
        fig.tight_layout()
        fn = f"thr_gate_R{rate.replace('/', '_')}_{snr:g}dB.png"
        fig.savefig(os.path.join(PL, fn), dpi=130)
        plt.close(fig)
        print("gate", name, flush=True)
    for old in glob.glob(os.path.join(PL, "thr_gate_R*.png")):          # the earlier two-panel figures
        if "dB" not in old:
            os.remove(old)


def spec():
    c = collections.Counter()
    for f in glob.glob(os.path.join(RES, "blind_ber_t-cnf*.json")):
        for r in json.load(open(f)):
            if r["rx"] == "T nofast_spec_t":
                for k, v in r.items():
                    if k.startswith("rho_spec_"):
                        c[k] += v
    right = np.array([c.get(f"rho_spec_right_{b:02d}", 0) for b in range(30)], float)
    wrong = np.array([c.get(f"rho_spec_wrong_{b:02d}", 0) for b in range(30)], float)
    x = np.arange(30) * 0.1
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axvspan(0.6, 1.0, color=GREY, alpha=0.10)
    ax.axvspan(1.0, 1.1, color=RED, alpha=0.12)
    ax.axvspan(1.1, 1.6, color=GREEN, alpha=0.08)
    ax.bar(x + 0.03, np.where(right > 0, right, np.nan), 0.045, color=ORANGE, label=f"right decodes ({int(right.sum())})")
    ax.bar(x + 0.07, np.where(wrong > 0, wrong, np.nan), 0.045, color="k", label=f"wrong decodes ({int(wrong.sum())})")
    ax.set_yscale("log")
    ax.set_ylim(0.5, 3e5)
    ax.set_xlim(0.6, 1.6)
    rej = int(wrong[:10].sum())
    bb = dict(fc="white", ec=GREY, alpha=0.95)
    ax.text(0.63, 2e4, f"rho < 1.0: rejected by the\nnormal check (wrong: {rej})", fontsize=10, bbox=bb)
    ax.annotate(f"1.0 - 1.1: rejected only by the 1.1 factor\nwrong {int(wrong[10])} (these were the 2 undetected errors)"
                f"\nright {int(right[10])} ({100 * right[10] / right.sum():.1f} %; the search decodes them later)",
                (1.05, 30), xytext=(0.63, 150), fontsize=10, bbox=bb, arrowprops=dict(arrowstyle="->", color=RED))
    ax.text(1.37, 2e3, f"rho > 1.1: accepted\nright {int(right[11:].sum())}\nwrong {int(wrong[11:].sum())}",
            fontsize=10, bbox=bb)
    ax.set_xlabel("re-encoding correlation rho / its threshold")
    ax.set_ylabel("speculative decodes that pass the CRC")
    ax.set_title("Speculative decode: why accept only above 1.1 x the threshold, R = 1/10, -5 dB")
    ax.grid(alpha=0.3, axis="y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(PL, "thr_spec_rho.png"), dpi=130)
    plt.close(fig)


def fastpath():
    # MACs per core [M]: (SNR, fast path off, on), paired runs nf10a/b, nf15a/b/c, t-cnf15e, t-cnf25, t-cnf2
    D = {"1/10": [(-5, .2156, .3102), (-4, .1635, .2577), (-3, .1505, .2428), (-1, .1268, .2017), (0, .1077, .1532)],
         "0.15": [(-4, .5512, .6497), (-3, .1834, .2817), (-1, .1450, .2238), (0, .1268, .1713), (1, .1128, .1063)],
         "2/5": [(0.5, .4655, .3819), (1.0, .1495, .1303)],
         "1/2": [(2.0, .3221, .0852), (2.5, .3130, .0752)]}
    for rates, fn in ((["1/10"], "thr_fastpath_R1_10.png"), (["0.15"], "thr_fastpath_R0.15.png"),
                      (["2/5", "1/2"], "thr_fastpath_R2_5_R1_2.png")):
        fig, ax = plt.subplots(figsize=(10, 5.8))
        xs, ys, labs = [], [], []
        for rate in rates:
            for s, off, on in D[rate]:
                xs.append(f"{s:g} dB" + (f"\nR = {rate}" if len(rates) > 1 else ""))
                ys.append(100 * (off / on - 1))
        cols = [GREEN if y < 0 else RED for y in ys]
        b = ax.bar(range(len(ys)), ys, color=cols, width=0.6)
        for i, y in enumerate(ys):
            ax.text(i, y + (2 if y >= 0 else -2), f"{y:+.0f} %", ha="center", va="bottom" if y >= 0 else "top",
                    fontsize=10)
        ax.axhline(0, color="k", lw=1)
        ax.set_xticks(range(len(ys)), xs)
        if rates == ["0.15"] or rates == ["1/10"]:
            k = sum(1 for s, *_ in D[rates[0]] if s <= 0)
            if k < len(ys):
                ax.axvline(k - 0.5, color=BLUE, ls="--", lw=2)
            top = max(0, max(ys)) * 1.25 + 6
            ax.text(k - 0.6, top, "fast path OFF (SNR <= 0 dB)", ha="right", va="top", color=BLUE, fontsize=10)
            if k < len(ys):
                ax.text(k - 0.4, top, "ON", ha="left", va="top", color=BLUE, fontsize=10)
        else:
            ax.text(len(ys) / 2 - 0.5, max(ys) * 0.8, "fast path stays ON at every SNR", ha="center", color=BLUE,
                    fontsize=11)
        ax.set_ylim(min(0, min(ys)) * 1.3 - 5, max(0, max(ys)) * 1.25 + 8)
        ax.set_xlabel("SNR (Es/N0)")
        ax.set_ylabel("MACs per core with the fast path OFF vs ON [%]")
        ax.set_title("Fast path switch: green = turning it off saves, red = it costs, R = " + ", ".join(rates))
        ax.grid(alpha=0.3, axis="y")
        fig.tight_layout()
        fig.savefig(os.path.join(PL, fn), dpi=130)
        plt.close(fig)
    for old in ("thr_fastpath_main.png",):
        if os.path.exists(os.path.join(PL, old)):
            os.remove(os.path.join(PL, old))


if __name__ == "__main__":
    spec()
    fastpath()
    gate()
    print("written", PL)
