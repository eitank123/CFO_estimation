"""BLER vs SNR of the TESTING blind receiver under a hard cap on the MACs per core, next to the est4 pilot competitors
(fair axis, pilot energy charged). Existing results only (2026-11-15).

    py BLIND_IMPLEMENTATION/testing/plot_cap_fair.py

Cap emulation (as plot_cap_snr.py): the blind search stops at its first accepted decode, so a cap C on a packet's MACs
per core turns exactly the right decodes that needed more than C into errors ("no packet"):
    BLER(C) = (errors without a cap + right decodes with MACs per core >= C) / packets,
exact at the histogram bin edges (small_rx pg_XX: right decodes, 0.05-decade bins from 1e4). The histogram is on
crit_par (critical path, 32 cores), which per packet is >= the scheduled count used everywhere else
(crit_par_h_d4a / crit_par_d4a), so these caps are conservative for blind (it would lose fewer packets under the
same cap on the scheduled count).
Testing model = 1/10, 0.15: `testing_s11g` (= T testing_spec11 below -3.5 / -2.5 dB and T testing above, in the s11
sweep, as agg_cmp.adopted) + every non-smoke run of `T testing_s11g`; 2/5, 1/2: every non-smoke run of base25_qfix /
base2_qfix. The pilot competitors spend 0.03-0.045 M per core on average (one decode + a few lobe decodes); their
per-packet maximum is not recorded, so they are drawn uncapped.
Outputs: results/plots/capf_bler_R*.png, results/cap_fair.md.
"""
import glob
import json
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import agg_cmp as C
import plot_e4 as P

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(os.path.dirname(HERE)), "small_cfo", "blind", "results")
CAPS = {"0.3 M": 30, "0.5 M": 34, "1 M": 40, "2 M": 46}          # bin k: cap = 10^(4 + k/20) MACs per core
CAP_COL = {"0.3 M": "#7b2d6b", "0.5 M": "#b04a94", "1 M": "#d77fbf", "2 M": "#f0b6dd"}
TARGETS = {"1/10": [1e-4], "0.15": [1e-3, 1e-4], "2/5": [1e-3], "1/2": [1e-3]}
REFS = ["RCS2-13", "pre128 ML"]


def modified_parts():
    """Parts run with a channel / code override (phase noise BLIND_PN, no interleaver BLIND_NOINT, rotation bits
    BLIND_ROTBITS): the env var is set in the job script, not stored in the result rows, so read the scripts."""
    import re
    bad, pat = set(), re.compile(r"\bBLIND_(PN|NOINT|ROTBITS)=")
    jobs = os.path.join(os.path.dirname(os.path.dirname(HERE)), "jobs")
    for f in glob.glob(os.path.join(jobs, "**", "*.sh"), recursive=True):
        txt = open(f, encoding="utf-8", errors="replace").read().splitlines()
        glob_ = any(l.lstrip().startswith("export") and pat.search(l) for l in txt)
        for l in txt:
            m = re.search(r"--part\s+(\S+)", l)
            if m and (glob_ or pat.search(l)):
                bad.add(m.group(1))
    return bad


def load():
    """{rate: {snr: [packets, errors, pg histogram (100 bins)]}} for the testing model, AWGN runs only."""
    acc = defaultdict(lambda: defaultdict(lambda: [0, 0, np.zeros(100)]))
    skip = modified_parts()

    def add(rate, r):
        a = acc[rate][r["snr"]]
        a[0] += r["frames"]
        a[1] += r["frame_err"]
        for b in range(100):
            a[2][b] += r.get(f"pg_{b:02d}", 0)
    for f in glob.glob(os.path.join(RES, "blind_ber_*.json")):
        part = os.path.basename(f)[len("blind_ber_"):-5]
        if part == "" or "smoke" in part or "dump" in part or part in skip:
            continue
        try:
            rows = json.load(open(f))
        except Exception:
            continue
        rows = rows["results"] if isinstance(rows, dict) and "results" in rows else rows
        for r in rows if isinstance(rows, list) else []:
            if not any(k.startswith("pg_") for k in r):
                continue
            rate, rx, s = r.get("rate"), r.get("rx"), r.get("snr")
            if rate in C.S11_SNR:
                if part in C.S11_PARTS:
                    want = "T testing_spec11" if s < C.S11_SNR[rate] else "T testing"
                    if rx == want:
                        add(rate, r)
                elif rx == "T testing_s11g":
                    add(rate, r)
            elif (rate, rx) in (("2/5", "T base25_qfix"), ("1/2", "T base2_qfix")):
                add(rate, r)
    return acc


def curves(acc, rate):
    """{label: {snr: dict(err, n)}}: uncapped and each cap."""
    out = {"none": {}}
    out.update({c: {} for c in CAPS})
    for s, (n, e, h) in acc[rate].items():
        if s < -5.0:
            continue
        out["none"][s] = dict(err=e, n=n)
        for c, k in CAPS.items():
            out[c][s] = dict(err=e + h[k:].sum(), n=n)
    return out


def fig(rate, cv):
    E = P.e4(rate)
    sty = P.styles()
    f, ax = plt.subplots(figsize=(10, 7.4))
    P.curve(ax, cv["none"], "bler", "blind, testing receiver, no cap", P.BLIND[1], P.BLIND[2], lw=2.8, ms=9)
    for c in CAPS:
        P.curve(ax, cv[c], "bler", f"blind, testing receiver, cap {c} MACs per core", CAP_COL[c], "o", ls="--", lw=1.8,
                ms=5)
    for k in REFS:
        if k in E:
            lab, c, m, ls = sty[k]
            P.curve(ax, {s: v for s, v in E[k].items() if s >= -5.0}, "bler", lab + " (no cap needed)", c, m, ls=ls,
                    lw=1.4 if k == "Genie" else 1.9)
    ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]  (burst energy per data symbol: pilot energy charged)", fontsize=12)
    ax.set_ylabel("BLER", fontsize=12)
    ax.set_title(f"BLER vs SNR with a MACs-per-core cap, R = {rate}", fontsize=13)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    p = os.path.join(P.OUT, f"capf_bler_R{P.tag(rate)}.png")
    f.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(f)
    print(p)


def table(acc):
    lines = ["# Testing blind receiver under a MACs-per-core cap vs the pilot competitors (generated by plot_cap_fair.py)",
             "", "Required SNR [dB] at the target BLER on the fair axis (log-linear interpolation; 'fails' = not crossed "
             "in the simulated range). Cap = hard limit on crit_par MACs per core (conservative, see the script "
             "docstring). Gap = blind - RCS2-13 (negative = blind better).", "",
             "| Rate, BLER | no cap | cap 2 M | cap 1 M | cap 0.5 M | cap 0.3 M | RCS2-13 | 128 ML | packets per blind point |",
             "|---|---|---|---|---|---|---|---|---|"]
    for rate, ts in TARGETS.items():
        cv, E = curves(acc, rate), P.e4(rate)
        npk = ", ".join(f"{s:g}: {v['n'] // 1000}k" for s, v in sorted(cv["none"].items()))
        for t in ts:
            ref = P.gap_db(E["RCS2-13"], t)
            cells = []
            for key in ("none", "2 M", "1 M", "0.5 M", "0.3 M"):
                g = P.gap_db(cv[key], t)
                cells.append("fails" if g is None else f"{g:.2f} ({g - ref:+.2f})")
            ml = P.gap_db(E["pre128 ML"], t)
            lines.append(f"| {rate}, {t:.0e} | " + " | ".join(cells) + f" | {ref:.2f} | "
                         + ("fails" if ml is None else f"{ml:.2f}") + f" | {npk} |")
    lines += ["", "Fraction of packets stopped by the cap (right decodes lost), per SNR:", "",
              "| Rate | SNR | packets | cap 2 M | cap 1 M | cap 0.5 M | cap 0.3 M |", "|---|---|---|---|---|---|---|"]
    for rate in TARGETS:
        for s, (n, e, h) in sorted(acc[rate].items()):
            if s >= -5.0:
                lines.append(f"| {rate} | {s:g} | {n} | " + " | ".join(f"{h[CAPS[c]:].sum() / n:.1e}"
                                                                    for c in ("2 M", "1 M", "0.5 M", "0.3 M")) + " |")
    p = os.path.join(HERE, "results", "cap_fair.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(p)


if __name__ == "__main__":
    A = load()
    for r in ("1/10", "0.15", "2/5", "1/2"):
        fig(r, curves(A, r))
    table(A)
