"""S experiments (nofast, nofast_spec, nofast_nph4, nph15, noise-only): tables for report_S.md.
Usage (from anywhere): py BLIND_IMPLEMENTATION/testing/agg_S.py            (prints markdown tables; no simulation)

Rows of a part are one per (chunk, receiver); the receivers of a job see the same packets chunk by chunk, so the
chunks are paired (checked here with out_coarse_1e3, which depends on the packets only). Per-packet outcomes are not
stored, so paired BLER is per chunk (errors of the same 4000 packets), not per packet.

Two error counts:
  frame_err  = delivered data != true data (blind_ber). A packet without an accepted decode delivers its FIRST
               decode ("out" in small_rx.decode): the fast-path decode in the baseline, the first search decode under
               nofast. Such a packet is no frame error if that unaccepted decode happens to be right, so the rule is
               not the same in the two arms.
  miss       = frames - n_dd = packets without an accepted AND right decode: the same rule in every arm.
"""
import collections
import json
import os
import sys

import numpy as np
from scipy.stats import beta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "small_cfo", "blind", "results")
SIG = ["nf10a", "nf10b", "nf15a", "nf15b", "nf15c", "nn15c"]          # signal-present parts
NOISE = ["nn15a", "nn15b"]                                              # noise-only parts
REF = {"1/10": "srch10", "0.15": "srch15"}                            # the R runs (same seeds / chunking)
BASE = {"nf10a": "S blind final v2", "nf10b": "S blind final v2", "nf15a": "S blind final v2",
        "nf15b": "S blind final v2", "nf15c": "T nph4", "nn15c": "S blind final v2",
        "nn15a": "S blind final v2 [noise only]", "nn15b": "S blind final v2 [noise only]"}
PH_EDGES = 10 ** (4 + np.arange(101) / 20)                            # small_rx "ph_" bins (per core, all packets)


def cp(k, n):
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1)
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return lo, hi


def load(part):
    """{(rate, snr, rx): [chunk rows in file order]} without the genie."""
    t = collections.defaultdict(list)
    for r in json.load(open(os.path.join(ROOT, f"blind_ber_{part}.json"))):
        if "Genie" not in r["rx"]:
            t[(r["rate"], r["snr"], r["rx"])].append(r)
    return t


def tot(rows, f):
    return sum(r.get(f, 0) or 0 for r in rows)


def tail(rows, q):
    h = np.array([tot(rows, f"ph_{b:02d}") for b in range(100)], float)
    if h.sum() == 0:
        return np.nan
    c = np.cumsum(h) / h.sum()
    return PH_EDGES[1:][np.searchsorted(c, q - 1e-12)]                 # upper edge of the bin holding the quantile


def summary(rows):
    n, m = tot(rows, "frames"), tot(rows, "mac_frames")
    k = tot(rows, "frame_err")
    return dict(n=n, err=k, ci=cp(k, n), miss=n - tot(rows, "n_dd"), und=tot(rows, "undetected"),
                macs=tot(rows, "macs") / m, core=tot(rows, "crit_par_macs") / m,
                core_h=tot(rows, "crit_par_h_macs") / m, grid=tot(rows, "crit_grid") / m,
                fast=tot(rows, "macs_fast") / m, dec=tot(rows, "decodes") / n,
                spec=tot(rows, "spec_decodes") if any("spec_decodes" in r for r in rows) else None,
                spec_pass=tot(rows, "spec_pass") if any("spec_decodes" in r for r in rows) else None,
                lost=tot(rows, "check_lost"), caught=tot(rows, "check_caught"), crc_wrong=tot(rows, "crc_pass_wrong"),
                crc_pass=tot(rows, "crc_pass"), st=[tot(rows, f"stage_{s}") / max(tot(rows, "stage_frames"), 1) for s in range(1, 6)],
                p99=tail(rows, 0.99), p999=tail(rows, 0.999), pmax=tail(rows, 1.0), chunks=len(rows))


def rel(a_rows, b_rows, f):
    """Relative difference of the per-packet mean of f, a vs b (%), with a 95 % interval from the paired chunks
    (t, n - 1 d.o.f., delta method on the chunk ratios)."""
    from scipy.stats import t as tdist
    a = np.array([r.get(f, 0) / r["mac_frames"] for r in a_rows])
    b = np.array([r.get(f, 0) / r["mac_frames"] for r in b_rows])
    d = a.sum() / b.sum() - 1
    q = a / b - 1
    h = tdist.ppf(0.975, len(q) - 1) * q.std(ddof=1) / np.sqrt(len(q)) if len(q) > 1 else np.nan
    return 100 * d, 100 * h


def paired(a_rows, b_rows):
    """Chunk-level pairing of frame errors (a = variant, b = baseline): chunks where the variant has fewer / more
    errors, and the lower bounds on packets fixed / broken that follow."""
    assert len(a_rows) == len(b_rows)
    same = all(x["out_coarse_1e3"] == y["out_coarse_1e3"] and x["frames"] == y["frames"] for x, y in zip(a_rows, b_rows))
    d = np.array([x["frame_err"] - y["frame_err"] for x, y in zip(a_rows, b_rows)])
    dm = np.array([(x["frames"] - x["n_dd"]) - (y["frames"] - y["n_dd"]) for x, y in zip(a_rows, b_rows)])
    return dict(same=same, fixed=int(-d[d < 0].sum()), broken=int(d[d > 0].sum()),
                fixed_m=int(-dm[dm < 0].sum()), broken_m=int(dm[dm > 0].sum()))


def collect():
    """[(part, rate, snr, rx, summary, rows, base rows)] of the signal-present parts."""
    out = []
    for part in SIG:
        t = load(part)
        for (rate, snr, rx), rows in sorted(t.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] != BASE[part], kv[0][2])):
            out.append((part, rate, snr, rx, summary(rows), rows, t[(rate, snr, BASE[part])]))
    return out


def noise():
    out = []
    for part in NOISE:
        t = load(part)
        for (rate, snr, rx), rows in sorted(t.items(), key=lambda kv: kv[0][2] != BASE[part]):
            n, m = tot(rows, "frames"), tot(rows, "mac_frames")
            acc_dec = tot(rows, "crc_pass") - tot(rows, "check_caught") - tot(rows, "check_lost")
            out.append(dict(part=part, rate=rate, snr=snr, rx=rx, n=n, frame_err=tot(rows, "frame_err"),
                            fa_pk=tot(rows, "undetected"), acc_dec=acc_dec, right=tot(rows, "n_dd"),
                            crc_pass=tot(rows, "crc_pass"), caught=tot(rows, "check_caught"),
                            ub=1 - 0.05 ** (1 / n), macs=tot(rows, "macs") / m, core=tot(rows, "crit_par_macs") / m,
                            core_h=tot(rows, "crit_par_h_macs") / m, dec=tot(rows, "decodes") / n,
                            p99=tail(rows, 0.99), pmax=tail(rows, 1.0), rows=rows, base=t[(rate, snr, BASE[part])]))
    return out


def M(v):
    return f"{v / 1e6:.3f}"


if __name__ == "__main__":
    res = collect()
    print("### Results (signal present)\n")
    print("| R | SNR | receiver | errors / packets | BLER (95 % CI) | miss | undetected | total [M] | per core [M] | crit_par_h [M] | "
          "per core 99 % / 99.9 % / max [M] | dec/pk | spec dec / pass | check_lost | part |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for part, rate, snr, rx, s, rows, b in res:
        bl = f"{s['err'] / s['n']:.2e} [{s['ci'][0]:.1e}, {s['ci'][1]:.1e}]" if s["err"] else f"< {3 / s['n']:.1e}"
        sp = "-" if s["spec"] is None else f"{s['spec']} / {s['spec_pass']}"
        print(f"| {rate} | {snr:g} | {rx} | {s['err']} / {s['n']} | {bl} | {s['miss']} | {s['und']} | {M(s['macs'])} | {M(s['core'])} | "
              f"{M(s['core_h'])} | {s['p99'] / 1e6:.2f} / {s['p999'] / 1e6:.2f} / {s['pmax'] / 1e6:.2f} | {s['dec']:.2f} | {sp} | {s['lost']} | {part} |")
    print("\n### Paired differences vs the job's baseline arm (same packets; +- = 95 % from the 16 paired chunks)\n")
    print("| R | SNR | receiver vs baseline | errors (var vs base) | chunk-paired fixed / broken | miss (var vs base) | "
          "total | per core | crit_par_h vs base crit_par | grid crit | stage 1 share of base | pairing ok |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for part, rate, snr, rx, s, rows, b in res:
        if rx == BASE[part]:
            continue
        sb, pr = summary(b), paired(rows, b)
        dt, dc = rel(rows, b, "macs"), rel(rows, b, "crit_par_macs")
        dh = 100 * (s["core_h"] / sb["core"] - 1)
        dg = 100 * (s["grid"] / sb["grid"] - 1)
        print(f"| {rate} | {snr:g} | {rx} vs {BASE[part]} | {s['err']} vs {sb['err']} | {pr['fixed']} / {pr['broken']} | "
              f"{s['miss']} vs {sb['miss']} | {dt[0]:+.1f} +- {dt[1]:.1f} % | {dc[0]:+.1f} +- {dc[1]:.1f} % | {dh:+.1f} % | {dg:+.1f} % | "
              f"{100 * sb['st'][0]:.1f} % | {pr['same']} |")
    print("\n### S2: nofast_spec vs nofast\n")
    print("| R | SNR | errors (spec vs nofast) | total | per core | dec/pk | spec decodes / pk | spec pass share |")
    print("|---|---|---|---|---|---|---|---|")
    d = {(p, r, s, x): (sm, rows) for p, r, s, x, sm, rows, b in res}
    for (p, r, s, x), (sm, rows) in d.items():
        if x == "T nofast_spec":
            nb, nrows = d[(p, r, s, "T nofast")]
            dt, dc = rel(rows, nrows, "macs"), rel(rows, nrows, "crit_par_macs")
            print(f"| {r} | {s:g} | {sm['err']} vs {nb['err']} | {dt[0]:+.1f} +- {dt[1]:.1f} % | {dc[0]:+.1f} +- {dc[1]:.1f} % | "
                  f"{sm['dec']:.2f} vs {nb['dec']:.2f} ({sm['dec'] - nb['dec']:+.2f}) | {sm['spec'] / sm['n']:.3f} | {sm['spec_pass'] / max(sm['spec'], 1):.1%} |")
    print("\n### S1b: crit_par_h vs crit_par within each receiver\n")
    print("| R | SNR | receiver | crit_par [M] | crit_par_h [M] | change | grid part: crit_grid -> per-hypothesis |")
    print("|---|---|---|---|---|---|---|")
    for part, rate, snr, rx, s, rows, b in res:
        gh = s["grid"] + s["core_h"] - s["core"]
        print(f"| {rate} | {snr:g} | {rx} | {M(s['core'])} | {M(s['core_h'])} | {100 * (s['core_h'] / s['core'] - 1):+.1f} % | "
              f"{M(s['grid'])} -> {M(gh)} ({100 * (gh / s['grid'] - 1):+.1f} %) |")
    print("\n### Baseline arm vs the R runs (same seed and chunking)\n")
    print("| R | SNR | S baseline errors / packets | R run errors / packets | chunks identical (errors and MACs) | total S / R [M] | per core S / R [M] |")
    print("|---|---|---|---|---|---|---|")
    for part, rate, snr, rx, s, rows, b in res:
        if rx != "S blind final v2":
            continue
        ref = load(REF[rate]).get((rate, snr, rx)) if rate in REF else None
        if not ref:
            print(f"| {rate} | {snr:g} | {s['err']} / {s['n']} | not in {REF.get(rate)} | - | - | - |")
            continue
        sr = summary(ref)
        # the chunks finish in a different order in the two jobs: compare them as sorted (packets, errors, MACs) tuples
        sig = lambda r: (r["frames"], r["out_coarse"], r["out_coarse_1e3"], r["frame_err"], r["macs"], r["crit_par_macs"])
        ident = sorted(map(sig, rows)) == sorted(map(sig, ref))
        print(f"| {rate} | {snr:g} | {s['err']} / {s['n']} | {sr['err']} / {sr['n']} | {ident} | {M(s['macs'])} / {M(sr['macs'])} | {M(s['core'])} / {M(sr['core'])} |")
    print("\n### Noise-only packets (R = 0.15)\n")
    print("| SNR | receiver | packets | accepted packets (false alarms) | accepted decodes | 95 % upper bound | CRC passes / caught by re-encoding | "
          "total [M] | per core [M] | crit_par_h [M] | per core 99 % / max [M] | dec/pk |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    ns = noise()
    for r in ns:
        print(f"| {r['snr']:g} | {r['rx']} | {r['n']} | {r['fa_pk']} | {r['acc_dec']} | < {r['ub']:.1e} | {r['crc_pass']} / {r['caught']} | "
              f"{M(r['macs'])} | {M(r['core'])} | {M(r['core_h'])} | {r['p99'] / 1e6:.1f} / {r['pmax'] / 1e6:.1f} | {r['dec']:.1f} |")
    for r in ns:
        if r["rx"] != BASE[r["part"]]:
            dt, dc = rel(r["rows"], r["base"], "macs"), rel(r["rows"], r["base"], "crit_par_macs")
            print(f"\nnoise-only {r['snr']:g} dB, {r['rx']} vs base: total {dt[0]:+.1f} +- {dt[1]:.1f} %, per core {dc[0]:+.1f} +- {dc[1]:.1f} %")
