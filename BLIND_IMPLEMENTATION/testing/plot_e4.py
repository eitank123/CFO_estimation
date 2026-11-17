"""est4 vs blind, energy charged (pilots outside the packet): BLER and MACs per core vs the plotted SNR
(burst energy per data symbol, est4 snr_plot), one figure per rate, plus a text table.
usage: py plot_e4.py   (reads est4/results/bler_e4-{10,15,25,2,pp*}.json and the blind parts via agg_cmp)
       py plot_e4.py --e5   (+ the est5 deployed competitors, bler_e5-{10,15,25,2,pp*}.json -> e5_{bler,macs}_R*.png;
                             the est5 parts' own Genie is not drawn: est4's genie stays the reference)
       py plot_e4.py --ars  (+ the ARS 2021 variants on rcs13, bler_ars-{10,15,25,2}.json -> ars_{bler,macs}_R*.png;
                             their RCS2-13 rows are the e4 packets again and are not drawn twice; combinable with --e5)
       py plot_e4.py --e5 --var   (+ the faithful variants, bler_v-{10,15,25,2}{,h,p,w,s}.json -> e5var_*.png; their
                             parent rows are other seeds and pool with the e4 / e5 rows)"""
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
MAIN5 = {"1/10": "e5-10", "0.15": "e5-15", "2/5": "e5-25", "1/2": "e5-2"}
PP5 = {"1/10": "e5-pp10", "0.15": "e5-pp15", "2/5": "e5-pp25", "1/2": "e5-pp2"}
EXT5 = {"1/10": ["e5-10lo-a", "e5-10lo-b", "e5-10lo-c"]}        # low-SNR extensions (expected_e5lo.md, 2026-11-15)
STY5 = {"VDE-SAT": ("VDE-SAT: 27 syncword + 1 pilot per 27, 66 known", "#17becf", "P", "-"),
        "DVB-S2 style": ("DVB-S2-inspired: 90 PL header + 36 pilot block, M&M + joint ML", "#8c564b", "h", "-"),
        "CCSDS style": ("CCSDS-inspired: 8 x 16 pilot blocks, Rife-Boorstyn", "#d62728", "*", "-"),
        "CCSDS style blocks": ("CCSDS-inspired, per-block ML phase + linear interp.", "#ff9896", "*", "--"),
        "ViaSat UW": ("ViaSat: 16 midamble UW, 4th-power top-32", "#7f7f7f", "1", "--"),
        "DMRS 1/7": ("NB-IoT DMRS style: 1 pilot per 7, 171 known", "#393b79", "p", "-."),
        "Sparse pilots 1/32": ("Sparse pilots 1/32 (400ZR-inspired), 4th-power coarse", "#e7ba52", "<", "-."),
        "WiFi pre128": ("Wi-Fi-inspired: 8 x 16 preamble, lag 16 / 64", "#637939", ">", "-."),
        "MIL-110 HF": ("MIL-STD-188-110C App C: 184 + 4 x 31 probes, 308 known", "#843c39", "X", ":"),
        "hyb3": ("16 + 16, hybrid DA + 4th power, 3 candidates (US7590199)", "#ce6dbd", "d", ":"),
        # faithful variants (expected_variants.md; their parts with --var)
        "hyb3-pre48": ("Advantech US7590199 layout: 48 preamble, hybrid DA + 4th power, 3 candidates", "#a55194", "d", "-"),
        "ViaSat 7653150": ("ViaSat US7653150: 16 UW, single 4th-power peak, 4th-power phase", "#525252", "1", "-"),
        "ViaSat top32 X4phase": ("ViaSat top-32 (US8243859) + 4th-power phase", "#969696", "2", "-."),
        "DVB-S2 header90": ("DVB-S2 PL header only (90, CCM), M&M + ML", "#c49c94", "h", "--"),
        "DVB-S2 SOF26": ("DVB-S2 SOF only (26, ACM), M&M + ML", "#e7969c", "h", ":"),
        "MIL-110 full": ("MIL-STD-188-110C App C full: 287 + 4 x 31 probes, 411 known", "#ad494a", "X", "-"),
        "CCSDS 131.2 real": ("CCSDS 131.2 density: 16 pilots per 540 data, +-17 lobes", "#e7298a", "*", ":"),
        "CCSDS 131.0 ASM": ("CCSDS 131.0: 32-symbol ASM before + after, joint ML", "#fd8d3c", "o", "--"),
        "WiFi real320": ("Wi-Fi legacy L-STF + L-LTF (320), lag 16 / 64, no lobe search", "#8ca252", ">", "-"),
        "WiFi real320 lobes": ("Wi-Fi legacy L-STF + L-LTF (320) + the +-4 fine-lobe search", "#b5cf6b", ">", ":"),
        "hyb3-pre48 wide": ("Advantech 48 preamble, hybrid, window from the 48-symbol DA CRB", "#7b4173", "d", "--"),
        "split64 ML L4": ("64 pre + 64 post, joint ML, +-4 lobes", "#e6550d", "o", ":")}
VARP = {r: tuple(f"v-{t}{s}" for s in ("", "h", "h2", "p", "p2", "w", "w2", "s", "s2",
                                         "ma", "mb", "mc", "ha", "hb", "hc", "pa", "pb", "wa", "wb", "sa", "sb", "sc", "s2a", "s2b", "hla", "hlb"))
        for r, t in (("1/10", "10"), ("0.15", "15"), ("2/5", "25"), ("1/2", "2"))}
                                                     # --var: the variant parts (absent parts, e.g. v-10w2, load empty;
                                                     # *a/*b/*c: the re-split after v-smoke, 2026-11-15; never submit a
                                                     # replaced job with its split, or its rows pool twice)
ARSP = {"1/10": "ars-10", "0.15": "ars-15", "2/5": "ars-25", "1/2": "ars-2"}
STYA = {"G4096": ("RCS2-13, FFT 4096 + parabolic (ARS 2021)", "#aec7e8", "s", ":"),
        "G2048": ("RCS2-13, FFT 2048 + parabolic (ARS 2021)", "#6baed6", "s", "-."),
        "G2048N": ("RCS2-13, FFT 2048 + parabolic + 1 Newton", "#3182bd", "s", ":"),
        "Griebel faithful": ("Griebel et al. 2021 as published: FFT 2048, full band, Eq. 17 phase, 1 decode", "#08306b", "v", "--"),
        "RCS2-13 lobes": ("RCS2-13 + the +-1/20 alias lobes in the CRC search", "#17becf", "o", "-")}
BLIND =("blind (testing receiver, no pilots)", "#e377c2", "d")


def tag(r):
    return {"1/10": "10", "0.15": "15", "2/5": "25", "1/2": "2"}[r]


def load(part):
    p = os.path.join(RES, f"bler_{part}.json")
    return json.load(open(p))["results"] if os.path.exists(p) else []


def e4(rate, e5=False, ars=False, var=False):
    """{src: {snr_plot: dict(err, n, und, core, est_core, snr)}}; e5: + the est5 parts (without their Genie); ars: + the
    ARS parts (without their RCS2-13); var: + the variant parts v-* (their parents pool with the e4 / e5 rows: other
    seeds); a (src, snr_plot) in several parts is pooled (pool)"""
    out = defaultdict(dict)
    rows = load(MAIN[rate]) + load(PP[rate])
    if e5:
        rows += [r for r in load(MAIN5[rate]) + load(PP5[rate]) if r["src"] != "Genie"]
        rows += [r for p in EXT5.get(rate, []) for r in load(p) if r["src"] != "Genie"]
    if ars:
        rows += [r for r in load(ARSP[rate]) if r["src"] != "RCS2-13"]
    if var:
        rows += [r for p in VARP[rate] for r in load(p) if r["src"] != "Genie"]
    for r in rows:
        if r["rate"] != rate or r["pn"] != 0:
            continue
        n = r["frames"]
        x = r["extra_decodes_per_frame"]
        tot, core = E4E.pilot_macs(rate, r["src"], x, par=True, m_evals=r.get("metric_evals", 0) / n,
                                   m_rounds=r["metric_rounds"] / n if r.get("metric_rounds") else None,
                                   mode=r["track"], pn=r["pn"])
        lay, est, model = E4C.SOURCES[r["src"]]
        ec = E4E.est_macs(est, E4C.layout(lay)) / E4E.KP if r["src"] != "Genie" else 0.0
        d = dict(err=r["frame_err"], n=n, und=r["undetected"], core=core, tot=tot, est_core=ec, snr=r["snr"], x=x)
        k = round(r["snr_plot"], 3)
        if k in out[r["src"]]:                             # same receiver, same SNR in another part (e.g. e5-pp* re-runs
            d = pool(out[r["src"]][k], d)                  # "RCS2 pre/post" of e4-pp*, other seeds): pool the packets
        out[r["src"]][k] = d
    return out


def pool(a, b):
    """a + b of one receiver at one SNR (independent packets): counts summed, per-packet means weighted by n"""
    n = a["n"] + b["n"]
    w = {k: (a[k] * a["n"] + b[k] * b["n"]) / n for k in ("core", "tot", "est_core", "x")}
    return dict(a, err=a["err"] + b["err"], n=n, und=a["und"] + b["und"], **w)


def blind(rate):
    """{snr: dict(err, n, und, core)}: adopted testing receiver (1/10, 0.15); 2/5, 1/2: presentation receiver BLER
    over the whole waterfall, q_fix testing receiver where it was run (its MACs; BLER the same within noise)."""
    if rate in ("1/10", "0.15"):
        return {s: dict(err=v["err"], n=v["n"], und=v["und"], core=v["core_s"]) for s, v in C.adopted(rate).items()}
    out = {s: dict(err=k, n=n, und=None, core=None) for s, (k, n) in C.merged(rate, C.EP.BLIND_RX[rate]).items()}
    for s, v in C.testing_hi(rate).items():               # q_fix + early stop (adopted 2026-11-15)
        out[s] = dict(err=v["err"], n=v["n"], und=v["und"], core=v["core_s"])
    return out


def curve(ax, pts, key, lab, c, m, ls="-", lw=1.8, ms=6):
    xs = sorted(pts)
    y = [(pts[s]["err"] / pts[s]["n"] if key == "bler" else (pts[s][key] or np.nan) / 1e6) for s in xs]
    if key == "bler":
        xs, y = zip(*[(s, v) for s, v in zip(xs, y) if v > 0]) if any(v > 0 for v in y) else ([], [])
    if len(xs):
        ax.plot(xs, y, color=c, marker=m, ls=ls, lw=lw, ms=ms, label=lab)


def styles(e5=False, ars=False, var=False):
    return dict(STY, **(STY5 if e5 or var else {}), **(STYA if ars else {}))


def fig(rate, key, e5=False, ars=False, var=False):
    P, B = e4(rate, e5, ars, var), blind(rate)
    allx = [s for d in P.values() for s in d]
    lo, hi = min(allx) - 0.25, max(allx) + 0.25
    B = {s: v for s, v in B.items() if lo <= s <= hi}
    f, ax = plt.subplots(figsize=(10, 7.8))
    curve(ax, B, key, BLIND[0], BLIND[1], BLIND[2], lw=2.8, ms=9)
    for src, (lab, c, m, ls) in styles(e5, ars, var).items():
        if src in P and src != "Genie":   # genie not drawn (user 2026-11-15)
            curve(ax, P[src], key, lab, c, m, ls=ls, lw=1.4 if src == "Genie" else 1.9)
    if key == "bler":
        ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]  (burst energy per data symbol: pilot energy charged)", fontsize=12)
    ax.set_ylabel("BLER" if key == "bler" else "MACs per core per packet [M] (scheduled)", fontsize=12)
    ax.set_title(("BLER" if key == "bler" else "MACs per core") + f" vs SNR, R = {rate}", fontsize=14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    f.tight_layout()
    pre = ("e5" if e5 else "") + ("ars" if ars else "") + ("var" if var else "") or "e4"
    p = os.path.join(OUT, f"{pre}_{'bler' if key == 'bler' else 'macs'}_R{tag(rate)}.png")
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


def table(rate, e5=False, ars=False, var=False):
    P, B = e4(rate, e5, ars, var), blind(rate)
    print(f"\n### R = {rate}  (SNR = plotted, energy charged; errors / packets (undetected); core = M MACs per core)")
    print("| receiver | " + " | ".join(f"{s:g}" for s in sorted(B)) + " |")
    print("| blind | " + " | ".join(f"{B[s]['err']}/{B[s]['n']//1000}k" + (f" {B[s]['core']/1e6:.3f}" if B[s]['core'] else "")
                                  for s in sorted(B)) + " |")
    for src in styles(e5, ars, var):
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
    E5, AR, VA = "--e5" in sys.argv, "--ars" in sys.argv, "--var" in sys.argv
    for rate in ("1/10", "0.15", "2/5", "1/2"):
        table(rate, E5, AR, VA)
        fig(rate, "bler", E5, AR, VA)
        fig(rate, "core", E5, AR, VA)
