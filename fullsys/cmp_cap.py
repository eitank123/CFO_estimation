"""
Paired comparison of two run_blind_fs runs on the SAME packets (same --fmt / --seed / --batch / --frames / design), one
without and one with --cap-core: per Es/N0 the errors of each, the packets failing only with the cap (= the BLER cost
of the cap), only without it (must be 0: the cap is emulated after the search), the cap hits and their verdict without
the cap, mean / max MACs per core (the profile's standard model and crit_par, the capped quantity). Pairing per chunk
c by chunks[].fe_idx / cap_idx; with --dump on the no-cap run also the packets whose crit_par passes the cap (pk npz).

    python fullsys/cmp_cap.py fullsys/results/blind_fs_<nocap>.json fullsys/results/blind_fs_<cap>.json
Exit 0 if no packet fails only with the cap, else 1.
"""

import glob
import json
import os
import sys

import numpy as np


def _load(p):
    with open(p) as fh:
        return json.load(fh)


def _sets(pt, key):
    return {(ch["c"], int(i)) for ch in pt["chunks"] for i in ch.get(key, [])}


def main(p0, p1):
    a, b = _load(p0), _load(p1)
    ma, mb = a["meta"], b["meta"]
    for k in ("fmt", "seed", "batch", "frames", "design", "design_snr", "cfo_max", "calib", "no_chan_intlv"):
        va, vb = ma["args"].get(k), mb["args"].get(k)
        assert va == vb, f"not paired: {k} {va} vs {vb}"
    cap = mb["args"].get("cap_core")
    assert ma["args"].get("cap_core") is None and cap, "give the no-cap run first, the cap run second"
    std = ma["std_core"]
    pb = {round(p["esn0"], 3): p for p in b["points"]}
    bad = 0
    print(f"{ma['fmt']} design {ma['args'].get('design')} seed {ma['args']['seed']} | cap {cap:.3g} MACs per core "
          f"(crit_par) | std model {std}")
    for pa in a["points"]:
        x = round(pa["esn0"], 3)
        if x not in pb:
            print(f"  Es/N0 {x:+.2f}: missing in the cap run")
            continue
        q = pb[x]
        n = min(pa["frames"], q["frames"])
        ca = {ch["c"] for ch in pa["chunks"]} & {ch["c"] for ch in q["chunks"]}
        ea = {k for k in _sets(pa, "fe_idx") if k[0] in ca}
        eb = {k for k in _sets(q, "fe_idx") if k[0] in ca}
        hb = {k for k in _sets(q, "cap_idx") if k[0] in ca}
        only_cap, only_nocap = eb - ea, ea - eb
        hit_ok = hb - ea                                              # capped, right (or at least not failed) uncapped
        bad += len(only_cap)
        line = (f"  Es/N0 {x:+.2f}: frames {pa['frames']} / {q['frames']} (paired chunks {len(ca)}) | errors no cap "
                f"{len(ea)} cap {len(eb)} | fail only with cap {len(only_cap)} only without {len(only_nocap)} | cap "
                f"hits {len(hb)} (of them fine without the cap {len(hit_ok)}; logged cap_hit {q.get('cap_hit')} right "
                f"{q.get('cap_hit_right')}) | per core {std} mean {pa['macs_per_core_std'] / 1e6:.3f} M -> "
                f"{q['macs_per_core_std'] / 1e6:.3f} M, max {pa.get('max_macs_per_core_std', float('nan')) / 1e6:.3f} M "
                f"-> {q.get('max_macs_per_core_std', float('nan')) / 1e6:.3f} M | crit_par mean "
                f"{pa['sum_cpar'] / pa['frames'] / 1e6:.3f} -> {q['sum_cpar'] / q['frames'] / 1e6:.3f} M, max "
                f"{pa.get('max_cpar', float('nan')) / 1e6:.3f} -> {q.get('max_cpar', float('nan')) / 1e6:.3f} M")
        print(line)
        dd = os.path.splitext(p0)[0] + "_dump"
        fl = sorted(glob.glob(os.path.join(dd, f"pk_{ma['fmt']}_{x:+.2f}_c*.npz")))
        if fl:                                                        # the no-cap run's per-packet crit_par
            cp = np.concatenate([np.load(f_)["cpar"] for f_ in fl])
            rt = np.concatenate([np.load(f_)["right"] for f_ in fl])
            ov = cp > cap
            print(f"      no-cap dump: {len(cp)} packets, crit_par > cap {int(ov.sum())} (right {int((ov & rt).sum())}), "
                  f"crit_par of the right ones: p99 {np.percentile(cp[rt], 99) / 1e6 if rt.any() else 0:.3f} M, max "
                  f"{cp[rt].max() / 1e6 if rt.any() else 0:.3f} M")
    print(f"CAP CHECK: {'NO BLER LOSS' if not bad else f'{bad} packets fail only with the cap'}")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
