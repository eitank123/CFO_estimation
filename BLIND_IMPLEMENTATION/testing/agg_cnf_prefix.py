"""Pre-fix vs fixed phase accounting of the presentation receiver on the SAME packets (analysis only, no simulation).
Usage: py BLIND_IMPLEMENTATION/testing/agg_cnf_prefix.py

The old S parts (nf10a, nf15a, nf15b) carry no chunk_seed; their chunks are matched to the t-cnf presentation chunks
(t-cnf10d, t-cnf15d, t-cnf15f: same seeds 7701 / 7702) by the packet-only signature (out_coarse, out_coarse_1e3,
se_coarse). The receiver is the same ("S blind final v2"); only the phase accounting differs, so errors must agree.
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "small_cfo", "blind", "results")
RX = "S blind final v2"


def rows(part, rate, snr):
    return [r for r in json.load(open(os.path.join(ROOT, f"blind_ber_{part}.json")))
            if r["rx"] == RX and r["rate"] == rate and r["snr"] == snr]


def sig(r):
    return (r["out_coarse"], r["out_coarse_1e3"], round(r["se_coarse"], 9))


for old, new, rate, snr in [("nf10a", "t-cnf10d", "1/10", -5.0), ("nf10a", "t-cnf10d", "1/10", -4.0),
                            ("nf15a", "t-cnf15d", "0.15", -4.0), ("nf15b", "t-cnf15f", "0.15", -3.0)]:
    O, N = rows(old, rate, snr), rows(new, rate, snr)
    so = collections.Counter(sig(r) for r in O)
    assert max(so.values()) == 1
    o = {sig(r): r for r in O}
    pairs = [(o[sig(r)], r) for r in N if sig(r) in o]
    if not pairs:
        print(f"{rate} {snr:g}: {old} vs {new}: no matching chunks ({len(O)} / {len(N)})")
        continue
    f = lambda P, i, k: sum(p[i][k] for p in P)
    m = f(pairs, 1, "mac_frames")
    assert m == f(pairs, 0, "mac_frames")
    c0, c1 = f(pairs, 0, "crit_par_macs") / m / 1e6, f(pairs, 1, "crit_par_macs") / m / 1e6
    t0, t1 = f(pairs, 0, "macs") / m / 1e6, f(pairs, 1, "macs") / m / 1e6
    print(f"{rate} {snr:g}: {len(pairs)} of {len(N)} chunks matched ({old} -> {new}); errors {f(pairs, 0, 'frame_err')} / "
          f"{f(pairs, 1, 'frame_err')}; decodes {f(pairs, 0, 'decodes')} / {f(pairs, 1, 'decodes')}; per core {c0:.4f} -> {c1:.4f} "
          f"({100 * (c1 / c0 - 1):+.1f} %); total {t0:.3f} -> {t1:.3f} ({100 * (t1 / t0 - 1):+.1f} %)")
