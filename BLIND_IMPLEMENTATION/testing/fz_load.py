"""BLIND_IMPLEMENTATION/testing/: load the fz_diag dumps (F5 of results/expected_f3f5.md; read-only, no simulation).

    from fz_load import load
    F, J, G = load(["t-fz1a", "t-fz1b"])      # dicts of arrays: f_ / j_ rows, g_ packets, + "chunk" (chunk index)
"""
import glob
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DUMPS = os.path.join(ROOT, "small_cfo", "blind", "dumps")


def load(parts, rx_prefix="fz_T_"):
    """Concatenate the f / j / g groups of every chunk file of the parts; 'chunk' = a unique chunk index, 'uid' =
    chunk * 100000 + packet (the packet key). Duplicate chunk seeds across parts are an error."""
    out = {"f": [], "j": [], "g": []}
    seeds = set()
    ci = 0
    for part in parts:
        for fn in sorted(glob.glob(os.path.join(DUMPS, part, rx_prefix + "*.npz"))):
            z = np.load(fn, allow_pickle=False)
            s = (str(z["rate"]), float(z["snr"]), int(z["chunk_seed"]))
            assert s not in seeds, f"duplicate chunk {s} in {fn}"
            seeds.add(s)
            for g in out:
                ks = [k for k in z.files if k.startswith(g + "_")]
                if not ks:
                    continue
                d = {k[2:]: z[k] for k in ks}
                n = len(d["pkt" if g == "g" else "pk"])
                d["chunk"] = np.full(n, ci, np.int32)
                out[g].append(d)
            ci += 1
    res = []
    for g in ("f", "j", "g"):
        if not out[g]:
            res.append(None)
            continue
        d = {k: np.concatenate([x[k] for x in out[g]]) for k in out[g][0]}
        d["uid"] = d["chunk"].astype(np.int64) * 100000 + d["pkt" if g == "g" else "pk"]
        res.append(d)
    return tuple(res)
