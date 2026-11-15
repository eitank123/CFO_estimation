"""est4 vs blind, energy charged (pilots outside the packet): BLER and MACs per core vs the plotted SNR
(burst energy per data symbol, est4 snr_plot), one figure per rate, plus a text table.
usage: py plot_e4.py   (reads est4/results/bler_e4-{10,15,25,2,pp*}.json and the blind parts via agg_cmp)"""
import json, os, sys
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [HERE, PROJ, os.path.join(PROJ, "est4")]
import agg_cmp as C
import common as E4C
import estimators as E4E

OUT = os.path.join(HERE, "results", "plots")
RES = os.path.join(PROJ, "est4", "results")
MAIN = {"1/10": "e4-10", "0.15": "e4-15", "2/5": "e4-25", "1/2": "e4-2"}
PP = {"1/10": "e4-pp10", "0.15": "e4-pp15", "2/5": "e4-pp25", "1/2": "e4-pp2"}
STY = {"Genie": ("est4 genie (true CFO + phase, no pilots)", "#7f7f7f", "x", ":"),
       "RCS2-13": ("DVB-RCS2 ID13 layout, 116 known symbols (tracking = constant here: no phase noise)", "#1f77b4", "s", "--"),
       "pre128 ML": ("128 preamble, ML", "#2ca02c", "^", "-"),
       "pre128 M&M": ("128 preamble, M&M", "#bcbd22", "v", "--"),
       "split64 ML": ("64 pre + 64 post, joint ML (interp. = constant here)", "#ff7f0e", "o", "-"),
       "RCS2 pre/post": ("16 pre + 16 post, 4th-power NDA", "#9467bd", "D", "--")}
BLIND = ("blind (testing receiver, no pilots)", "#e377c2", "d")


def tag(r):
    return {"1/10": "10", "0.15": "15", "2/5": "25", "1/2": "2"}[r]


def load(part):
    p = os.path.join(RES, f"bler_{part}.json")
    return json.load(open(p))["results"] if os.path.exists(p) else []


def e4(rate):
    """{src: {snr_plot: dict(err, n, und, core, est_core, snr)}}"""
    out = defaultdict(dict)
    for r in load(MAIN[rate]) + load(PP[rate]):
        if r["rate"] != rate or r["pn"] != 0:
            continue
        n = r["frames"]
        x = r["extra_decodes_per_frame"]
        tot, core = E4E.pilot_macs(rate, r["src"], x, par=True, m_evals=r.get("metric_evals", 0) / n,
                                   m_rounds=r["metric_rounds"] / n if r.get("metric_rounds") else None,
                                   mode=r["track"], pn=r["pn"])
        lay, est, model = E4C.SOURCES[r["src"]]
        ec = E4E.est_macs(est, E4C.layout(lay)) / E4E.KP if r["src"] != "Genie" else 0.0
        out[r["src"]][round(r["snr_plot"], 3)] = dict(err=r["frame_err"], n=n, und=r["undetected"], core=core,
                                                      tot=tot, est_core=ec, snr=r["snr"], x=x)
    return out


def blind(rate):
    """{snr: dict(err, n, und, core)}: adopted testing receiver (1/10, 0.15); 2/5, 1/2: presentation receiver BLER
    over the whole waterfall, q_fix testing receiver where it was run (its MACs; BLER the same within noise)."""
    if rate in ("1/10", "0.15"):
        return {s: dict(err=v["err"], n=v["n"], und=v["und"], core=v["core_s"]) for s, v in C.adopted(rate).items()}
    out = {s: dict(err=k, n=n, und=None, core=None) for s, (k, n) in C.merged(rate, C.EP.BLIND_RX[rate]).items()}
    for s, v in C.qfix(rate).items():
        out[s] = dict(err=v["err"], n=v["n"], und=v["und"], core=v["core_s"])
    return out


def curve(ax, pts, key, lab, c, m, ls="-", lw=1.8, ms=6):
    xs = sorted(pts)
    y = [(pts[s]["err"] / pts[s]["n"] if key == "bler" else (pts[s][key] or np.nan) / 1e6) for s in xs]
    if key == "bler":
        xs, y = zip(*[(s, v) for s, v in zip(xs, y) if v > 0]) if any(v > 0 for v in y) else ([], [])
    if len(xs):
        ax.plot(xs, y, color=c, marker=m, ls=ls, lw=lw, ms=ms, label=lab)


def fig(rate, key):
    P, B = e4(rate), blind(rate)
    allx = [s for d in P.values() for s in d]
    lo, hi = min(allx) - 0.25, max(allx) + 0.25
    B = {s: v for s, v in B.items() if lo <= s <= hi}
    f, ax = plt.subplots(figsize=(10, 7.8))
    curve(ax, B, key, BLIND[0], BLIND[1], BLIND[2], lw=2.8, ms=9)
    for src, (lab, c, m, ls) in STY.items():
        if src in P and not (key != "bler" and src == "Genie"):
            curve(ax, P[src], key, lab, c, m, ls=ls, lw=1.4 if src == "Genie" else 1.9)
    if key == "bler":
        ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]  (burst energy per data symbol: pilot energy charged)", fontsize=12)
    ax.set_ylabel("BLER" if key == "bler" else "MACs per core per packet [M] (scheduled)", fontsize=12)
    ax.set_title(("BLER" if key == "bler" else "MACs per core") + f" vs SNR, R = {rate}", fontsize=14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    f.tight_layout()
    p = os.path.join(OUT, f"e4_{'bler' if key == 'bler' else 'macs'}_R{tag(rate)}.png")
    f.savefig(p, dpi=150)
    plt.close(f)
    print(p)


def gap_db(pts, target):
    """SNR where BLER crosses target (log-linear interpolation), None if not crossed."""
    xs = sorted(s for s in pts if pts[s]["err"] > 0 or True)
    for a, b in zip(xs, xs[1:]):
        ya, yb = pts[a]["err"] / pts[a]["n"], pts[b]["err"] / pts[b]["n"]
        if ya >= target > yb and yb > 0:
            return a + (np.log(ya) - np.log(target)) / (np.log(ya) - np.log(yb)) * (b - a)
        if ya >= target and yb == 0:
            return None
    return None


def table(rate):
    P, B = e4(rate), blind(rate)
    print(f"\n### R = {rate}  (SNR = plotted, energy charged; errors / packets (undetected); core = M MACs per core)")
    print("| receiver | " + " | ".join(f"{s:g}" for s in sorted(B)) + " |")
    print("| blind | " + " | ".join(f"{B[s]['err']}/{B[s]['n']//1000}k" + (f" {B[s]['core']/1e6:.3f}" if B[s]['core'] else "")
                                  for s in sorted(B)) + " |")
    for src in STY:
        if src not in P:
            continue
        d = P[src]
        print(f"| {src} | " + " | ".join(f"@{s:g}: {d[s]['err']}/{d[s]['n']//1000}k ({d[s]['und']}) {d[s]['core']/1e6:.3f}"
                                        f" [est {100*d[s]['est_core']/d[s]['core']:.0f}%]" for s in sorted(d)) + " |")
    for t in (1e-2, 1e-3, 1e-4):
        g = {src: gap_db(d, t) for src, d in P.items()}
        gb = gap_db(B, t)
        print(f"SNR at BLER {t:g}: blind {gb if gb is None else round(gb, 2)}; " +
              ", ".join(f"{k} {v if v is None else round(v, 2)}" for k, v in g.items()))


if __name__ == "__main__":
    for rate in ("1/10", "0.15", "2/5", "1/2"):
        table(rate)
        fig(rate, "bler")
        fig(rate, "core")
