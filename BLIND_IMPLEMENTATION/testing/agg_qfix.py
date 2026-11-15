"""q_fix and dd-with-q_fix paired runs (t-qfx10 / t-qfx25 / t-qfx2, t-ddq10 / t-ddq25 / t-ddq2): analysis only.
Usage (from anywhere): py BLIND_IMPLEMENTATION/testing/agg_qfix.py

Jobs: jobs/qfx10.sh, jobs/qfx25.sh (base* vs base*_qfix, same packets), jobs/ddq10.sh, jobs/ddq25.sh (base*_qfix vs
dd_qfix* / dd_win4_qfix*, same packets). Pairing as in agg_cnf.py: rows of one point with the same chunk_seed carry
the same packets, errors are matched on (chunk_seed, fe_idx). Smoke parts (t-ddq-smoke-*) are not used.
MACs: mean per packet over mac_frames; per core = crit_par_macs, total = macs. Tails from the ph_ histogram (per core).
"""
import collections
import json
import os
import sys

import numpy as np

from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agg_cnf import ROOT, S, bler_s, cp, load, paired, rows_of  # noqa: E402

BASE = {"1/10": "S blind final v2", "0.15": "S blind final v2",
        "2/5": "S blind final 2/5, 1/2, best-first 32", "1/2": "S blind final 2/5, 1/2"}
QFX = [("t-qfx10", "1/10", -1), ("t-qfx10", "1/10", 0), ("t-qfx10", "0.15", -1), ("t-qfx10", "0.15", 0),
       ("t-qfx10", "0.15", 1), ("t-qfx25", "2/5", .5), ("t-qfx25", "2/5", 1), ("t-qfx2", "1/2", 2), ("t-qfx2", "1/2", 2.5)]
DDQ = [("t-ddq10", "1/10", -1, "T base10_qfix", ["T dd_qfix", "T dd_win4_qfix"]),
       ("t-ddq10", "0.15", -1, "T base10_qfix", ["T dd_qfix", "T dd_win4_qfix"]),
       ("t-ddq10", "0.15", 0, "T base10_qfix", ["T dd_qfix", "T dd_win4_qfix"]),
       ("t-ddq25", "2/5", .5, "T base25_qfix", ["T dd_qfix_25", "T dd_win4_qfix_25"]),
       ("t-ddq25", "2/5", 1, "T base25_qfix", ["T dd_qfix_25", "T dd_win4_qfix_25"]),
       ("t-ddq2", "1/2", 2, "T base2_qfix", ["T dd_qfix_2", "T dd_win4_qfix_2"]),
       ("t-ddq2", "1/2", 2.5, "T base2_qfix", ["T dd_qfix_2", "T dd_win4_qfix_2"])]
QRX = {"1/10": "T base10_qfix", "0.15": "T base10_qfix", "2/5": "T base25_qfix", "1/2": "T base2_qfix"}
# testing nofast15 (expected_cnf.md "Measured"; parts t-cnf15a..e) for the 0.15 comparison
NF15_PARTS = ["t-cnf15a", "t-cnf15b", "t-cnf15c", "t-cnf15d", "t-cnf15e"]


def ci(k, n):
    lo, hi = cp(k, n)
    return f"[{lo:.1e}, {hi:.1e}]"


def jk(A, B, f):
    """Paired % change of sum(f)/sum(mac_frames) B vs A, with a delete-one-chunk jackknife standard error."""
    a = np.array([r.get(f, 0) or 0 for r in A], float) / 1.0
    b = np.array([r.get(f, 0) or 0 for r in B], float)
    m = np.array([r["mac_frames"] for r in A], float)
    assert all(r["mac_frames"] == q["mac_frames"] for r, q in zip(A, B))
    full = 100 * (b.sum() / a.sum() - 1)
    loo = np.array([100 * ((b.sum() - b[i]) / (a.sum() - a[i]) - 1) for i in range(len(a))])
    n = len(a)
    se = np.sqrt((n - 1) / n * ((loo - loo.mean()) ** 2).sum())
    return full, se, m.sum()


def pc(a, b):
    return f"{100 * (a / b - 1):+.1f} %"


def acc_s(s):
    return ", ".join(f"{k[4:-6]} {v}" for k, v in sorted(s["acc"].items()) if v) or "-"


def row(label, s, sb=None, mc=None, AB=None):
    """Markdown row: arm, errors (BLER, CI), McNemar vs base, core, total, changes (+- jackknife SE over chunks),
    dec/pk, und, acc wrong, tails."""
    if AB:
        c, cs, _ = jk(*AB, "crit_par_macs")
        t, ts, _ = jk(*AB, "macs")
        chg = f"{c:+.1f} +- {cs:.1f} % | {t:+.1f} +- {ts:.1f} %"
    else:
        chg = "- | -"
    m = f"{mc[0]} / {mc[1]} (p = {mc[2]:.2g})" if mc else "-"
    return (f"| {label} | {bler_s(s['err'], s['n'])} {ci(s['err'], s['n'])} | {m} | {s['core']:.4f} | {s['macs']:.3f} | "
            f"{chg} | {s['dec']:.3f} | {s['und']} | {acc_s(s)} | {s['t99']:.2f} / {s['t999']:.2f} / {s['tmax']:.2f} |")


HDR = ("| arm | BLER (err/n) [95 % CI] | fixed / broken vs base (McNemar p) | per core [M] | total [M] | per core change | "
       "total change (paired, +- jackknife SE) | dec / pk | undetected | acc_*_wrong | per core 99 / 99.9 % / max [M] |\n|" + "---|" * 11)


def check_part(part):
    t = collections.defaultdict(list)
    for r in json.load(open(os.path.join(ROOT, f"blind_ber_{part}.json"))):
        t[(r["rate"], r["snr"], r["rx"])].append(r)
    for (rate, snr, rx), rs in sorted(t.items()):
        seeds = [r["chunk_seed"] for r in rs]
        dup = len(seeds) - len(set(seeds))
        cpm = sum("crit_par_macs" in r for r in rs)
        print(f"  {part} {rate} {snr:g} {rx}: chunks {len(rs)}, packets {sum(r['frames'] for r in rs)}, "
              f"dup seeds {dup}, rows with crit_par {cpm}, errors {sum(r['frame_err'] for r in rs)}")


def main():
    print("## Completeness\n")
    for p in ("t-qfx10", "t-qfx25", "t-qfx2", "t-ddq10", "t-ddq25", "t-ddq2"):
        check_part(p)

    print("\n## q_fix: base vs base_qfix (paired, same packets)\n")
    for part, rate, snr in QFX:
        t = load(part)
        a, b = t[(rate, float(snr), BASE[rate])], t[(rate, float(snr), QRX[rate])]
        A, B, fx, br, both, p = paired(a, b)          # a-only = base errors fixed by q_fix, b-only = broken
        sa, sb = S(A), S(B)
        print(f"\n### R = {rate}, {snr:g} dB ({part}, {sa['n']} packets)\n\n{HDR}")
        print(row("base", sa))
        print(row("q_fix", sb, sa, (fx, br, p), (A, B)))
        print(f"\nboth wrong {both}; undetected idx base {sa['ud']} qfix {sb['ud']}")

    print("\n## 0.15: q_fix (2 phases) pooled vs testing nofast15 (4 phases, other packets)\n")
    for snr in (-1, 0):
        q = rows_of(["t-qfx10", "t-ddq10"], "0.15", snr, "T base10_qfix")
        nf = rows_of(NF15_PARTS, "0.15", snr, "T nofast15")
        pres = rows_of(["t-qfx10"], "0.15", snr, "S blind final v2")
        sq, sn, sp = S(q), S(nf), S(pres)
        k = sq["err"] + sn["err"]
        p = binomtest(sq["err"], k, sq["n"] / (sq["n"] + sn["n"])).pvalue if k else 1.0
        print(f"0.15 {snr:g}: base10_qfix {bler_s(sq['err'], sq['n'])} {ci(sq['err'], sq['n'])} core {sq['core']:.4f} "
              f"total {sq['macs']:.3f} | nofast15 {bler_s(sn['err'], sn['n'])} {ci(sn['err'], sn['n'])} core {sn['core']:.4f} "
              f"total {sn['macs']:.3f} | conditional binomial p = {p:.2g} | nofast15 vs qfix core {pc(sn['core'], sq['core'])} "
              f"total {pc(sn['macs'], sq['macs'])} | base10 (qfx10 only) {bler_s(sp['err'], sp['n'])}")

    print("\n## dd_qfix / dd_win4_qfix vs base_qfix (paired, same packets)\n")
    for part, rate, snr, base, arms in DDQ:
        t = load(part)
        rb = t[(rate, float(snr), base)]
        sb = S(rb)
        print(f"\n### R = {rate}, {snr:g} dB ({part}, {sb['n']} packets)\n\n{HDR}")
        print(row(base[2:], sb))
        for rx in arms:
            A, B, fx, br, both, p = paired(rb, t[(rate, float(snr), rx)])
            print(row(rx[2:], S(B), S(A), (fx, br, p), (A, B)))
        _, _, o1, o2, both, _ = paired(t[(rate, float(snr), arms[0])], t[(rate, float(snr), arms[1])])
        print(f"\n{arms[0][2:]} vs {arms[1][2:]}: only-first {o1}, only-second {o2}, both {both}")
        g = [r for r in json.load(open(os.path.join(ROOT, f"blind_ber_{part}.json")))
             if r["rate"] == rate and r["snr"] == float(snr) and "Genie" in r["rx"]]
        print(f"\ngenie (one decode) {sum(r['frame_err'] for r in g)}/{sum(r['frames'] for r in g)}")


if __name__ == "__main__":
    sys.exit(main())
