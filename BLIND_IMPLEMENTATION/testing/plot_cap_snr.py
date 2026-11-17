"""BLIND_IMPLEMENTATION/testing/: BLER vs SNR under a hard cap on the MACs per core, one figure per (cap, rate).

    py BLIND_IMPLEMENTATION/testing/plot_cap_snr.py

The search stops at its first accepted decode, so a cap C on a packet's MACs per core (crit_par, 32 cores) turns
exactly the right decodes that needed more than C into errors. small_rx stores the per-core MACs of the right decodes
as a histogram (pg_XX, 0.05-decade bins from 1e4), so the BLER under a cap at a bin edge is exact:
    BLER(C) = (errors without a cap + right decodes in bins >= C) / packets.
Each figure: the presentation receiver (fixed phase accounting at 1/10 and 0.15) and the testing receiver (1/10, 0.15:
nofast15; 2/5, 1/2: presentation + q_fix), each with and without the cap, and the 128-pilot references (est3: ML,
M&M; genie CFO), which need 0.03-0.07 M MACs per core and so are never cut by these caps. Zero-error points are not
drawn. Numbers: results/cap_snr.json.
"""
import glob
import json
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(ROOT, "small_cfo", "blind", "results")
EST3 = os.path.join(ROOT, "est3", "results")
OUT = os.path.join(HERE, "results", "plots", "original_study", "cap")
CAPS = {"0.5 M": 34, "1 M": 40, "2 M": 46, "5 M": 54, "10 M": 60}   # bin index k: cap = 10^(4 + k/20)
PRES = {"1/10": "S blind final v2", "0.15": "S blind final v2", "2/5": "S blind final 2/5, 1/2, best-first 32",
        "1/2": "S blind final 2/5, 1/2"}
TEST = {"1/10": ["T nofast15"], "0.15": ["T nofast15"], "2/5": ["T base25_qfix"], "1/2": ["T base2_qfix"]}
FIXED_PRES_PARTS = ("t-cnf10d", "t-cnf15d", "t-cnf15f", "t-qfx10")   # presentation runs after the accounting fix
REFS = (("ML direct PM+all", "128 pilots: ML (FFT + Newton), fair CRC search (metric order)", "#2ca02c", "^"),
        ("M&M PM+all", "128 pilots: M&M (existing baseline), fair CRC search (metric order)", "#8c564b", "v"),
        ("ML direct", "128 pilots: ML, fixed-order CRC search", "#2ca02c", ""),
        ("M&M", "128 pilots: M&M, fixed-order CRC search", "#8c564b", ""),
        ("Genie CFO", "genie CFO (known CFO)", "k", ""))
ARMS = (("presentation", "#2a78b8", "o"), ("testing", "#e07b28", "s"))


def load():
    acc = defaultdict(lambda: [0, 0, np.zeros(100)])          # (arm, rate, snr) -> frames, errors, pg histogram
    for f in glob.glob(os.path.join(RES, "blind_ber_*.json")):
        part = os.path.basename(f)[len("blind_ber_"):-5]
        if part == "" or "smoke" in part or "dump" in part or part.startswith("t-dec"):
            continue
        try:
            rows = json.load(open(f))
        except Exception:
            continue
        for r in rows if isinstance(rows, list) else []:
            if not any(k.startswith("pg_") for k in r):
                continue
            rate, rx = r["rate"], r["rx"]
            arm = None
            if rx == PRES.get(rate):
                if rate in ("1/10", "0.15") and part not in FIXED_PRES_PARTS:
                    continue                                    # pre-fix accounting undercounts at these rates
                arm = "presentation"
            elif rx in TEST.get(rate, ()):
                arm = "testing"
            if arm is None:
                continue
            a = acc[(arm, rate, r["snr"])]
            a[0] += r["frames"]
            a[1] += r["frame_err"]
            for b in range(100):
                a[2][b] += r.get(f"pg_{b:02d}", 0)
    return acc


def refs():
    tot = defaultdict(lambda: [0, 0])
    for p in glob.glob(os.path.join(EST3, "bler_*.json")):
        if "smoke" in os.path.basename(p):
            continue
        for r in json.load(open(p))["results"]:
            t = tot[(r["src"], r["rate"], r["snr"])]
            t[0] += r["frames"]
            t[1] += r["frame_err"]
    return tot


def main():
    os.makedirs(OUT, exist_ok=True)
    acc, R = load(), refs()
    table = {}
    for rate in PRES:
        lo_s = min(s for (a, r, s) in acc if r == rate) - 0.25
        hi_s = max(s for (a, r, s) in acc if r == rate) + 0.25
        for cap, k in CAPS.items():
            fig, ax = plt.subplots(figsize=(9, 6.2))
            for arm, c, mk in ARMS:
                pts = sorted((s, *v) for (a, r, s), v in acc.items() if a == arm and r == rate)
                if not pts:
                    continue
                x = np.array([p[0] for p in pts])
                n = np.array([p[1] for p in pts], float)
                e = np.array([p[2] for p in pts], float)
                lost = np.array([p[3][k:].sum() for p in pts], float)
                b0, b1 = e / n, (e + lost) / n
                for s_, n_, e_, l_ in zip(x, n, e, lost):
                    table[f"{rate} | {cap} | {arm} | {s_:g}"] = dict(packets=int(n_), bler_no_cap=e_ / n_,
                                                                     bler_cap=(e_ + l_) / n_)
                m1, m0 = b1 > 0, b0 > 0
                ax.semilogy(x[m1], b1[m1], color=c, marker=mk, lw=2.4, label=f"{arm} receiver, cap {cap}")
                ax.semilogy(x[m0], b0[m0], color=c, marker=mk, mfc="none", ls="--", lw=1.4,
                            label=f"{arm} receiver, no cap")
            for src, lab, c, mk in REFS:
                pts = sorted((s, v[1] / v[0]) for (sr, r, s), v in R.items()
                             if sr == src and r == rate and lo_s <= s <= hi_s and v[1] > 0)
                if pts:
                    x, y = zip(*pts)
                    thin = "fixed-order" in lab                  # the pre-2026-11-13 search (undetected floor): thin
                    ax.semilogy(x, y, color=c, marker=mk, ls=":", lw=0.9 if thin else 1.8, alpha=0.6 if thin else 1.0,
                                label=f"{lab} (within any cap)")
            ax.set_xlim(lo_s, hi_s)
            ax.set_xlabel("SNR (Es/N0) [dB]")
            ax.set_ylabel("BLER")
            ax.set_title(f"BLER vs SNR with a cap of {cap} MACs per core, R = {rate}")
            ax.grid(True, which="both", ls=":", alpha=0.5)
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
            fig.tight_layout()
            fn = os.path.join(OUT, f"cap_{cap.replace(' ', '').replace('.', 'p')}_R{rate.replace('/', '_')}.png")
            fig.savefig(fn, dpi=130)
            plt.close(fig)
    json.dump(table, open(os.path.join(HERE, "results", "cap_snr.json"), "w"), indent=1)
    print("written", OUT)


if __name__ == "__main__":
    main()
