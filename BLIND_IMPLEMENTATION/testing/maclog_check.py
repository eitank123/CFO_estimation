"""BLIND_IMPLEMENTATION/testing/: pass criteria (b)-(f) of jobs/maclog-smoke.sh on the synced files (read-only, no
simulation). (a) (EVAL DONE / ALL DONE / no Traceback in logs/run_maclog-smoke.out) is checked too if the log is there.

    py maclog_check.py      # after syncing small_cfo/blind/results, small_cfo/blind/dumps/t-maclog-smoke-{a,b},
                            # est4/results, est4/dumps/maclog-smoke-c and logs/run_maclog-smoke.out

(b) one npz per (chunk, rx) for blind (every small-receiver row of the part JSON), one per (part, chunk) for est4
    holding every source of the JSON; no macs_*.npz in the opt-out parts (-a0, -b0, -c0)
(c) cap_post's dump vs JSON check: MATCH on every row (and at least one row per logging part)
(d) no NaN / inf in the blind costs and the est4 coef
(e) logging vs opt-out JSONs identical except time / timed_frames (blind) and time_est / us_est_per_frame (est4)
    (blind per chunk exactly; est4 floats to rtol 1e-12: its chunks are summed in completion order)
(f) blind pkt = 0 .. n - 1 in every file; est4 pkt0 = 0, contiguous batches, the chunks' n summing to the JSON frames"""
import glob
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import cap_post as CP  # noqa: E402

BL = os.path.join(PROJ, "small_cfo", "blind")
BLIND = {"t-maclog-smoke-a": "t-maclog-smoke-a0", "t-maclog-smoke-b": "t-maclog-smoke-b0"}   # logging: opt-out
EST4 = {"maclog-smoke-c": "maclog-smoke-c0"}
GENIE = "Genie (known CFO and phase)"
slug = lambda x: re.sub(r"[^0-9A-Za-z.+-]+", "_", str(x)).strip("_")


def bjson(part):
    p = os.path.join(BL, "results", f"blind_ber_{part}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def ejson(part):
    p = os.path.join(PROJ, "est4", "results", f"bler_{part}.json")
    return json.load(open(p))["results"] if os.path.exists(p) else None


def macs_files(root, part):
    return sorted(glob.glob(os.path.join(root, "dumps", part, "macs_*.npz")))


def same(a, b, skip, rtol):
    """field-wise equality of two row dicts except skip (floats to rtol)."""
    bad = []
    for k in sorted(set(a) | set(b)):
        if k in skip:
            continue
        x, y = a.get(k), b.get(k)
        if isinstance(x, float) or isinstance(y, float):
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))
                    and (x == y or np.isclose(x, y, rtol=rtol, atol=0))):
                bad.append(k)
        elif x != y:
            bad.append(k)
    return bad


def main():
    R = {}
    log = os.path.join(PROJ, "logs", "run_maclog-smoke.out")
    if os.path.exists(log):
        t = open(log, errors="replace").read()
        R["a"] = (t.count("EVAL DONE") == 6 and "ALL DONE" in t and "Traceback" not in t,
                  f"EVAL DONE x{t.count('EVAL DONE')} (want 6), ALL DONE {'ALL DONE' in t}, Traceback {'Traceback' in t}")
    else:
        R["a"] = (False, "logs/run_maclog-smoke.out not synced")
    msg = {q: [] for q in "bcdef"}
    for part, off in BLIND.items():                        # blind (b) (d) (e) (f)
        js, jo = bjson(part), bjson(off)
        if js is None:
            msg["b"].append(f"{part}: no JSON")
            continue
        rows = [r for r in js if r["rx"] != GENIE]
        fs = macs_files(BL, part)
        want = {f"macs_{slug(r['rx'])}_R{slug(r['rate'])}_{r['snr']:+.1f}_{r['chunk_seed']}.npz" for r in rows}
        have = {os.path.basename(f) for f in fs}
        if want != have:
            msg["b"].append(f"{part}: missing {sorted(want - have)}, extra {sorted(have - want)}")
        if macs_files(BL, off):
            msg["b"].append(f"{off}: opt-out part has macs files")
        for f in fs:
            z = np.load(f)
            if not all(np.isfinite(z[q]).all() for q in ("c_hd4a", "c_d4a", "cpar", "macs")):
                msg["d"].append(f"{part}/{os.path.basename(f)}: non-finite cost")
            if not np.array_equal(z["pkt"], np.arange(len(z["pkt"]))):
                msg["f"].append(f"{part}/{os.path.basename(f)}: pkt not 0..n-1")
        if jo is None:
            msg["e"].append(f"{off}: no JSON")
        else:
            key = lambda r: (r["rate"], r["snr"], r["rx"], r["chunk_seed"])
            A, B = {key(r): r for r in js}, {key(r): r for r in jo}
            if set(A) != set(B):
                msg["e"].append(f"{part} vs {off}: different rows")
            for k in set(A) & set(B):
                b_ = same(A[k], B[k], {"time", "timed_frames"}, 0.0)
                if b_:
                    msg["e"].append(f"{part} vs {off} {k}: {b_}")
    for part, off in EST4.items():                         # est4 (b) (d) (e) (f)
        js, jo = ejson(part), ejson(off)
        if js is None:
            msg["b"].append(f"{part}: no JSON")
            continue
        fs = macs_files(os.path.join(PROJ, "est4"), part)
        srcs = {r["src"] for r in js}
        nsum = {}
        for f in fs:
            z = np.load(f)
            if set(map(str, z["src"])) != srcs:
                msg["b"].append(f"{part}/{os.path.basename(f)}: sources {sorted(map(str, z['src']))} != JSON {sorted(srcs)}")
            if not np.isfinite(z["coef"]).all():
                msg["d"].append(f"{part}/{os.path.basename(f)}: non-finite coef "
                                f"{[str(s) for s, c in zip(z['src'], z['coef']) if not np.isfinite(c).all()]}")
            if (z["pkt0"] != 0).any() or not z["contig"].all() or (z["ovf"] != 0).any():
                msg["f"].append(f"{part}/{os.path.basename(f)}: pkt0 {z['pkt0'].tolist()}, contig "
                                f"{z['contig'].tolist()}, ovf {z['ovf'].tolist()}")
            for s, n in zip(z["src"], z["n"]):
                k = (float(z["snr"]), str(s))
                nsum[k] = nsum.get(k, 0) + int(n)
        snrs = {r["snr"] for r in js}
        if len(fs) != 4 * len(snrs):
            msg["b"].append(f"{part}: {len(fs)} files, want 4 chunks x {len(snrs)} SNRs")
        for r in js:
            if nsum.get((r["snr"], r["src"])) != r["frames"]:
                msg["f"].append(f"{part} {r['snr']} {r['src']}: dump n {nsum.get((r['snr'], r['src']))} != frames {r['frames']}")
        if macs_files(os.path.join(PROJ, "est4"), off):
            msg["b"].append(f"{off}: opt-out part has macs files")
        if jo is None:
            msg["e"].append(f"{off}: no JSON")
        else:
            key = lambda r: (r["snr"], r["src"])
            A, B = {key(r): r for r in js}, {key(r): r for r in jo}
            if set(A) != set(B):
                msg["e"].append(f"{part} vs {off}: different rows")
            for k in set(A) & set(B):
                b_ = same(A[k], B[k], {"time_est", "us_est_per_frame"}, 1e-12)
                if b_:
                    msg["e"].append(f"{part} vs {off} {k}: {b_}")
    pats = list(BLIND) + list(EST4)                        # (c) cap_post's check on the logging parts
    cb, ce = CP.check_blind(pats), CP.check_est4(pats)
    for name, s, d in cb + ce:
        if d is None or CP.mismatches(d):
            msg["c"].append(f"{name}: {s if d is None else CP.mismatches(d)}")
    for p in pats:
        if not any(n.startswith(p + "/") or n.startswith(p + " ") for n, _, _ in cb + ce):
            msg["c"].append(f"{p}: no checked rows")
    for q in "bcdef":
        R[q] = (not msg[q], "; ".join(msg[q]) or "ok")
    for q in "abcdef":
        print(f"({q}) {'PASS' if R[q][0] else 'FAIL'}  {R[q][1]}")
    print("ALL PASS" if all(v[0] for v in R.values()) else "SOME FAIL")


if __name__ == "__main__":
    main()
