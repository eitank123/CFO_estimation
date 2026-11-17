"""
Paired comparison of the z-test live-tuning runs (run_blind_fs --calib --sps, jobs fs-zt<fmt>k<k>, parts fs-zt<fmt>k<k>
<point>): every setting k vs the control (k 0, the final receiver) on the SAME calibration packets (same --fmt / --seed /
--batch / --frames / design / fzstop / cknn; checked). Per format and Es/N0: frames, errors (undetected), BLER, the
packets failing only with the setting (new) / only with the control (fixed), extra = errors - control errors, flagged
when extra > floor(0.02 x control errors); MACs per core (the profile's standard model) mean and max, MACs per frame,
each as a ratio to the control. Pairing per chunk c by chunks[].fe_idx (only the chunks both runs finished).

    python fullsys/zt_compare.py                       # every fullsys/results/blind_fs_fs-zt*.json
    python fullsys/zt_compare.py --prefix fs-zt13      # one format; --control 0 (default) the reference setting
Offline only (reads the part files); exit 0.
"""

import argparse
import glob
import json
import math
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "fullsys", "results")
PAIR = ("fmt", "seed", "charge_all", "sub", "batch", "frames", "design", "design_snr", "cfo_max", "calib", "cknn", "cknn_name", "ck_c",
        "fzstop", "spec", "rho", "ck", "bpsk_phase", "crc", "beta", "rx", "no_chan_intlv", "cap_core")
NAME = re.compile(r"^blind_fs_(fs-zt[a-z0-9]+?)k(\d+)([mp]\d+)\.json$")   # group, setting k, point tag
TOL = 0.02                                                               # extra errors allowed: floor(TOL x control)


def _sets(pt, chunks):
    return {(ch["c"], int(i)) for ch in pt["chunks"] if ch["c"] in chunks for i in ch.get("fe_idx", [])}


def _sps(meta):
    s = meta.get("sps_override")
    return "control" if not s else json.dumps(s, separators=(",", ":"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prefix", default="fs-zt", help="part-name prefix (default every fs-zt group)")
    ap.add_argument("--control", type=int, default=0, help="the reference setting k (default 0)")
    ap.add_argument("--results", default=RESULTS)
    a = ap.parse_args()
    runs = defaultdict(dict)                                             # (group, point tag) -> k -> (meta, point)
    for p in sorted(glob.glob(os.path.join(a.results, f"blind_fs_{a.prefix}*.json"))):
        m = NAME.match(os.path.basename(p))
        if not m:
            continue
        with open(p) as fh:
            d = json.load(fh)
        if not d["points"]:
            print(f"(no finished point yet: {os.path.basename(p)})")
            continue
        runs[(m.group(1), m.group(3))][int(m.group(2))] = (d["meta"], d["points"][0])
    if not runs:
        print("no z-test parts found")
        return 0
    flagged = []
    for (grp, tag), ks in sorted(runs.items()):
        if a.control not in ks:
            print(f"\n{grp} {tag}: no control (k {a.control}) yet; settings {sorted(ks)}")
            continue
        mc, pc = ks[a.control]
        std = mc["std_core"]
        print(f"\n{grp} {tag}: {mc['fmt']} Es/N0 {pc['esn0']:+.2f} dB | seed {mc['args']['seed']} calib "
              f"{mc['args']['calib']} | MACs per core = {std} | allowed extra errors floor({TOL:g} x control)")
        print(f"  {'k':>2} {'frames':>7} {'err':>5} {'ud':>3} {'BLER':>9} {'new':>4} {'fixed':>5} {'extra':>5} "
              f"{'allow':>5} {'core mean M':>11} {'ratio':>6} {'core max M':>10} {'ratio':>6} {'MACs/fr M':>9} "
              f"{'ratio':>6}  setting")
        for k in sorted(ks):
            m, p = ks[k]
            bad = [x for x in PAIR if m["args"].get(x) != mc["args"].get(x)]
            ch = {c["c"] for c in p["chunks"]} & {c["c"] for c in pc["chunks"]}
            es, ec = _sets(p, ch), _sets(pc, ch)
            n_s = sum(c["frames"] for c in p["chunks"] if c["c"] in ch)
            extra, allow = len(es) - len(ec), math.floor(TOL * len(ec))
            flag = k != a.control and extra > allow
            cm, cx, mf = p["macs_per_core_std"], p["max_macs_per_core_std"], p["macs_per_frame"]
            r = lambda x, y: x / y if y else float("nan")
            print(f"  {k:>2} {n_s:>7} {len(es):>5} {p['undetected']:>3} {len(es) / max(n_s, 1):>9.3e} "
                  f"{len(es - ec):>4} {len(ec - es):>5} {extra:>+5} {allow:>5} {cm / 1e6:>11.4f} "
                  f"{r(cm, pc['macs_per_core_std']):>6.3f} {cx / 1e6:>10.3f} {r(cx, pc['max_macs_per_core_std']):>6.3f} "
                  f"{mf / 1e6:>9.3f} {r(mf, pc['macs_per_frame']):>6.3f}  {_sps(m)}"
                  + ("  FLAG extra errors" if flag else "")
                  + (f"  NOT PAIRED ({', '.join(bad)})" if bad else "")
                  + (f"  (partial: {p['frames']} vs control {pc['frames']} frames)" if p["frames"] != pc["frames"] else ""))
            if flag or bad:
                flagged.append((grp, tag, k))
    print("\nflagged (extra errors above the allowance, or not paired):",
          ", ".join(f"{g}k{k}{t}" for g, t, k in flagged) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
