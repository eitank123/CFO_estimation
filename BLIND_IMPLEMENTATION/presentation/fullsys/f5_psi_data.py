"""ψ (psn_min) of right vs wrong CA-SCL decodes per frozen-bit checkpoint q, from the full-system decode dumps of the
F5 calibration parts (fullsys/results/blind_fs_<part>_dump, rows_*.npz as read by fullsys/tune_blind_fs.load_part).
right = accepted right decode, wrong = decode that failed its CRC. Writes data/f5_psi_fullsys.json.
    py BLIND_IMPLEMENTATION/presentation/fullsys/f5_psi_data.py"""
import glob, json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "..", "..", "fullsys", "results")
FZ_Q = (0.25, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
PARTS = {"ID 13": ["fs-k13m02", "fs-k13m04", "fs-k13m06", "fs-k13m08"], "ID 42": ["fs-k42"], "ID 14": ["fs-k14"]}
out = {}
for name, parts in PARTS.items():
    W, Rt = [], []
    for part in parts:
        for fn in glob.glob(os.path.join(R, f"blind_fs_{part}_dump", "rows_*.npz")):
            r = np.load(fn)
            G = [g for g in ("f", "j") if f"{g}_pk" in r.files]
            cat = lambda k: np.concatenate([r[f"{g}_{k}"] for g in G])
            rp, rs, rl = cat("pk"), cat("seq"), cat("slot")
            o = np.lexsort((rl, rs, rp)); od = np.lexsort((r["d_att"], r["d_pk"]))
            if len(o) != len(od): continue
            psn = cat("psn_min")[o].astype(np.float64)
            acc, drt = r["d_acc"][od].astype(bool), r["d_right"][od].astype(bool)
            Rt.append(psn[acc & drt]); W.append(psn[~acc])
    W, Rt = np.concatenate(W), np.concatenate(Rt)
    med = lambda X, c: float(np.nanmedian(np.where(np.isfinite(X[:, c]), X[:, c], np.nan)))
    out[name] = dict(q=list(FZ_Q), med_right=[med(Rt, c) for c in range(len(FZ_Q))],
                     med_wrong=[med(W, c) for c in range(len(FZ_Q))], n_right=int(len(Rt)), n_wrong=int(len(W)), parts=parts)
    print(name, out[name])
json.dump(out, open(os.path.join(HERE, "data", "f5_psi_fullsys.json"), "w"), indent=1)
