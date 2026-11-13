"""Confirmation runs (t-cnf*): measured columns for results/expected_cnf.md (analysis only, no simulation).
Usage (from anywhere): py BLIND_IMPLEMENTATION/testing/agg_cnf.py

Parts (jobs/cnf*.sh): testing "T nofast15" in t-cnf10a/b/c (1/10) and t-cnf15a/b/c/d/e (0.15); presentation with the
fixed phase accounting ("T base10" = rx "S blind final v2") in t-cnf10d (1/10, 16 chunks per point), t-cnf15d (0.15 -4)
and t-cnf15f (0.15 -3.5 ... +1); side arms nofast_spec_t (t-cnf10a), nofast_nph4 (t-cnf15e), base/nofast at 2/5 (t-cnf25)
and 1/2 (t-cnf2). Pairing: rows with the same (rate, snr, chunk_seed) carry the same packets; per-packet frame errors
are fe_idx (index inside the chunk), so paired errors are matched on (chunk_seed, index).
MACs: mean per packet over mac_frames; per core = crit_par_macs, total = macs, d4a / d4b = crit_par_d4a/_d4b_macs.
"""
import collections
import json
import os
import sys

import numpy as np
from scipy.stats import beta, binomtest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "small_cfo", "blind", "results")
PH_EDGES = 10 ** (4 + np.arange(101) / 20)        # small_rx "ph_" bins (per core, all packets)
PRES = "S blind final v2"
TEST = "T nofast15"
TEST_PARTS = {"1/10": ["t-cnf10a", "t-cnf10b", "t-cnf10c"], "0.15": ["t-cnf15a", "t-cnf15b", "t-cnf15c", "t-cnf15d", "t-cnf15e"]}
PRES_PARTS = {"1/10": ["t-cnf10d"], "0.15": ["t-cnf15d", "t-cnf15f"]}
# pre-registered values of expected_cnf.md: snr: (pres merged err, pres merged n, BLER-test expectation,
#   per core pre-fix, per core expected fixed, per core test exp, change %, total pres exp, total test exp, change %)
EXP = {"1/10": {-5: (88, 424e3, "same", .314, .377, .279, -26, 5.00, 4.40, -12),
                -4.5: (19, 560e3, "same", .276, .328, .233, -29, 4.10, 3.48, -15),
                -4: (1, 624e3, "same", .258, .304, .210, -31, 3.59, 2.98, -17),
                -3: (0, 260e3, "same", .243, .284, .193, -32, 3.20, 2.63, -18),
                -2: (0, 160e3, "same", .232, .271, .185, -32, 3.03, 2.49, -18),
                -1: (0, 160e3, "same", .202, .202, .127, -37, 1.94, 1.59, -18),
                0: (0, 160e3, "same", .154, .154, .108, -30, 1.44, 1.31, -9)},
       "0.15": {-4: (2175, 524e3, "same", .640, .726, .639, -12, 8.72, 8.19, -6),
                -3.5: (230, 340e3, "same", .349, .405, .316, -22, 5.07, 4.51, -11),
                -3: (93, 844e3, "same", .282, .337, .239, -29, 3.97, 3.37, -15),
                -2.5: (6, 660e3, "same", .261, .311, .221, -29, 3.48, 2.96, -15),
                -2: (0, 780e3, "same", .250, .297, .211, -29, 3.24, 2.76, -15),
                -1: (143, 880e3, ("lt", 1e-5), .236, .236, .179, -24, 2.35, 2.61, 11),
                0: (14, 780e3, ("about", 3e-6), .169, .169, .149, -12, 1.59, 2.13, 34),
                1: (0, 780e3, ("lt", 1e-5), .099, .099, .108, 9, .88, .97, 10)}}


def cp(k, n):
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1)
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return lo, hi


def load(part):
    t = collections.defaultdict(list)
    for r in json.load(open(os.path.join(ROOT, f"blind_ber_{part}.json"))):
        if "Genie" not in r["rx"]:
            t[(r["rate"], r["snr"], r["rx"])].append(r)
    return t


def rows_of(parts, rate, snr, rx):
    out = []
    for p in parts:
        out += load(p).get((rate, float(snr), rx), [])
    seeds = [r["chunk_seed"] for r in out]
    assert len(seeds) == len(set(seeds)), f"duplicated chunk {rate} {snr} {rx}"
    return out


def tot(rows, f):
    return sum(r.get(f, 0) or 0 for r in rows)


def tail(rows, q):
    h = np.array([tot(rows, f"ph_{b:02d}") for b in range(100)], float)
    if h.sum() == 0:
        return np.nan
    if q >= 1:
        return PH_EDGES[1:][np.nonzero(h)[0][-1]]
    c = np.cumsum(h) / h.sum()
    return PH_EDGES[1:][np.searchsorted(c, q - 1e-12)]


def S(rows):
    n, m = tot(rows, "frames"), tot(rows, "mac_frames")
    acc = collections.Counter()
    for r in rows:
        for k, v in r.items():
            if k.startswith("acc_") and k.endswith("_wrong"):
                acc[k] += v
    return dict(n=n, err=tot(rows, "frame_err"), und=tot(rows, "undetected"), core=tot(rows, "crit_par_macs") / m / 1e6,
                macs=tot(rows, "macs") / m / 1e6, d4a=tot(rows, "crit_par_d4a_macs") / m / 1e6,
                d4b=tot(rows, "crit_par_d4b_macs") / m / 1e6, dec=tot(rows, "decodes") / n,
                t99=tail(rows, .99) / 1e6, t999=tail(rows, .999) / 1e6, tmax=tail(rows, 1) / 1e6, acc=dict(acc),
                ud=sorted((r["chunk_seed"], i) for r in rows for i in r["ud_idx"]))


def errset(rows):
    return {(r["chunk_seed"], i) for r in rows for i in r["fe_idx"]}


def paired(ra, rb):
    """Common chunks of two arms: (subset a, subset b, a-only errors, b-only errors, both, McNemar exact p)."""
    a = {r["chunk_seed"]: r for r in ra}
    b = {r["chunk_seed"]: r for r in rb}
    com = sorted(set(a) & set(b))
    for s in com:      # packet-only signature must agree
        assert a[s]["frames"] == b[s]["frames"]
    A, B = [a[s] for s in com], [b[s] for s in com]
    ea, eb = errset(A), errset(B)
    na, nb = len(ea - eb), len(eb - ea)
    p = binomtest(na, na + nb, .5).pvalue if na + nb else 1.0
    return A, B, na, nb, len(ea & eb), p


def bler_s(k, n):
    if k == 0:
        return f"< {3 / n:.1e} (0/{n / 1e3:.0f}k)"
    return f"{k / n:.2e} ({k}/{n / 1e3:.0f}k)"


def bler_hit(exp, k, n, k0, n0):
    lo, hi = cp(k, n)
    if exp == "same":
        if k + k0 == 0:
            return True, "0 and 0"
        p = binomtest(k, k + k0, n / (n + n0)).pvalue
        return p > .05, f"p = {p:.2f} vs merged presentation"
    kind, v = exp
    if kind == "lt":
        return lo < v, f"CI [{lo:.1e}, {hi:.1e}]"
    return lo <= v <= hi, f"CI [{lo:.1e}, {hi:.1e}]"


def H(meas, exp):
    return "hit" if abs(meas / exp - 1) <= .10 else "miss"


def pct(a, b):
    return f"{100 * (a / b - 1):+.0f} %"


def main():
    for rate in ("1/10", "0.15"):
        print(f"\n### R = {rate}\n")
        print("| SNR [dB] | BLER pres (64k fixed; merged) | BLER test | paired errors pres / test (fixed / broken, p) | "
              "per core pres fixed [M] | per core test [M] | change (paired) | total pres fixed [M] | total test [M] | "
              "change (paired) | d4a test [M] | d4b test [M] | fixed / pre-fix | hit / miss |")
        print("|" + "---|" * 14)
        notes = []
        for snr, e in EXP[rate].items():
            k0, n0, bexp, pre, efix, etest, echg, etp, ett, etchg = e
            P = rows_of(PRES_PARTS[rate], rate, snr, PRES)
            T = rows_of(TEST_PARTS[rate], rate, snr, TEST)
            sp, st = S(P), S(T)
            Ap, At, fixed, broken, both, p = paired(P, T)
            pp, pt = S(Ap), S(At)
            bh, bnote = bler_hit(bexp, st["err"], st["n"], k0, n0)
            marks = [("BLER", "hit" if bh else "miss"), ("core pres", H(sp["core"], efix)), ("core test", H(st["core"], etest)),
                     ("total pres", H(sp["macs"], etp)), ("total test", H(st["macs"], ett))]
            ok = sum(m == "hit" for _, m in marks)
            mk = ", ".join(f"{a} {m}" for a, m in marks if m == "miss") or "all hit"
            print(f"| {snr:g} | {bler_s(sp['err'], sp['n'])}; {bler_s(k0, n0)} | {bler_s(st['err'], st['n'])} | "
                  f"{pp['err']} / {pt['err']} ({fixed} / {broken}, p = {p:.2f}) | {sp['core']:.3f} | {st['core']:.3f} | "
                  f"{pct(pt['core'], pp['core'])} | {sp['macs']:.2f} | {st['macs']:.2f} | {pct(pt['macs'], pp['macs'])} | "
                  f"{st['d4a']:.3f} ({pct(st['d4a'], st['core'])}) | {st['d4b']:.3f} ({pct(st['d4b'], st['core'])}) | "
                  f"{pct(sp['core'], pre)} | {ok}/5 hit{'' if ok == 5 else ': ' + mk} |")
            notes.append(f"  {rate} {snr:g}: BLER check {bnote}; change exp {echg:+d} % core / {etchg:+d} % total; "
                         f"und pres {sp['und']} test {st['und']}; tails test core 99/99.9/max {st['t99']:.2f}/{st['t999']:.2f}/"
                         f"{st['tmax']:.2f}, pres {sp['t99']:.2f}/{sp['t999']:.2f}/{sp['tmax']:.2f}; test unpaired-vs-paired core "
                         f"{st['core']:.3f}/{pt['core']:.3f}; dec/pk pres {sp['dec']:.3f} test {st['dec']:.3f}; acc_wrong test {st['acc']}")
        print("\n".join(notes))

    print("\n## side arms\n")
    for part, rate, snr, rxs in [("t-cnf10a", "1/10", -5, ["T nofast15", "T nofast_spec_t"]),
                                 ("t-cnf15e", "0.15", 1, ["T nofast15", "T nofast_nph4"]),
                                 ("t-cnf25", "2/5", .5, ["S blind final 2/5, 1/2, best-first 32", "T nofast_25"]),
                                 ("t-cnf25", "2/5", 1, ["S blind final 2/5, 1/2, best-first 32", "T nofast_25"]),
                                 ("t-cnf2", "1/2", 2, ["S blind final 2/5, 1/2", "T nofast_2"]),
                                 ("t-cnf2", "1/2", 2.5, ["S blind final 2/5, 1/2", "T nofast_2"])]:
        t = load(part)
        a, b = t[(rate, float(snr), rxs[0])], t[(rate, float(snr), rxs[1])]
        sa, sb = S(a), S(b)
        _, _, oa, ob, both, p = paired(a, b)
        for rx, s in zip(rxs, (sa, sb)):
            print(f"{part} {rate} {snr:g} {rx}: err {s['err']}/{s['n']} und {s['und']} ud {s['ud']} core {s['core']:.4f} "
                  f"total {s['macs']:.3f} d4a {s['d4a']:.4f} dec/pk {s['dec']:.3f} tails {s['t99']:.3f}/{s['t999']:.3f}/{s['tmax']:.3f} "
                  f"acc_wrong {s['acc']}")
        print(f"   paired: {rxs[0]}-only {oa}, {rxs[1]}-only {ob}, both {both}, p = {p:.2f}; core {pct(sb['core'], sa['core'])}, "
              f"total {pct(sb['macs'], sa['macs'])}")
    # 0.15 +1 dB vs base10 (t-cnf15f, same seed 7702 / chunks)
    P = rows_of(["t-cnf15f"], "0.15", 1, PRES)
    for rx in ("T nofast15", "T nofast_nph4"):
        T = load("t-cnf15e")[("0.15", 1.0, rx)]
        A, B, oa, ob, both, p = paired(P, T)
        sa, sb = S(A), S(B)
        print(f"0.15 +1 base10 vs {rx} on {sa['n']} common packets: base err {sa['err']} / {sb['err']}, base-only {oa}, "
              f"{rx}-only {ob}; core {sa['core']:.4f} -> {sb['core']:.4f} ({pct(sb['core'], sa['core'])}), total {sa['macs']:.3f} -> "
              f"{sb['macs']:.3f} ({pct(sb['macs'], sa['macs'])})")


if __name__ == "__main__":
    sys.exit(main())
