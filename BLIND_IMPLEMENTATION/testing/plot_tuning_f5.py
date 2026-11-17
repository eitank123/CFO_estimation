"""Tuning evidence for the F5 early stop of the full-system blind receiver (2026-11-17).
Per format: sweep the F5 threshold t at the chosen checkpoint q, replayed on the logged packets
(fullsys/tune_blind_fs.py), and show (top) extra errors on CALIBRATION packets and lost packets on TEST
packets, (bottom) mean MACs per core saved. Vertical lines: the setting picked on calibration and the adopted one.
Writes testing/results/plots/DVB-RCS2/tuning/fs_tuning_f5.png and fullsys/results/tuning_f5_sweep.json."""
import json, os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, "fullsys"); sys.argv = sys.argv[:1]
import tune_blind_fs as tb
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
F = {"ID 13": (["fs-k13m08", "fs-k13m06", "fs-k13m04", "fs-k13m02"], ["fs-c13m08n", "fs-c13m06", "fs-c13m04", "fs-c13m02", "fs-c13p00"], 0.6, 0.78, 0.80),
     "ID 3": (["fs-k3", "fs-k3b"], ["fs-c3m10", "fs-c3m08", "fs-c3m06", "fs-c3m04", "fs-c3m02", "fs-c3p00", "fs-d3p02", "fs-d3p04", "fs-e3p06"], 0.8, 0.86, None),
     "ID 42": (["fs-k42"], ["fs-c42m42", "fs-c42m40", "fs-c42m38", "fs-c42m36", "fs-d42m36", "fs-d42m34", "fs-d42m32"], 0.9, 0.75, 0.75),
     "ID 14": (["fs-k14"], ["fs-c14p14", "fs-c14p16", "fs-c14p18", "fs-c14p20"], 0.7, 0.78, 0.78),
     "VDE 32": (["fs-kv32"], ["fs-bv32m58", "fs-bv32m54", "fs-bv32m50", "fs-bv32m48", "fs-bv32m46", "fs-bv32m44", "fs-bv32m42"], 1.0, 0.75, None)}
TS = np.round(np.arange(0.70, 1.001, 0.01), 2)
f, ax = plt.subplots(2, len(F), figsize=(4.2 * len(F), 8)); out = {}
for j, (name, (cal, tst, q, tc, ta)) in enumerate(F.items()):
    C, T = tb.Set([tb.load_part(p) for p in cal]), tb.Set([tb.load_part(p) for p in tst])
    rc0, cc0, _ = C.evaluate(); rt0, ct0, _ = T.evaluate()
    ex, lo, sv = [], [], []
    for t in TS:
        s = dict(q=q, t=float(t), stage=5, cap=None)
        rc, cc, _ = tb.apply(C, s); rt, ct, _ = tb.apply(T, s)
        ex.append(int((rc0 & ~rc).sum())); lo.append(int((rt0 & ~rt).sum())); sv.append(100 * (1 - ct.mean() / ct0.mean()))
    out[name] = dict(q=q, t=TS.tolist(), calib_extra=ex, test_lost=lo, test_mac_saving_pct=sv, calib_err=int((~rc0).sum()),
                     test_err=int((~rt0).sum()), picked_on_calib=tc, adopted=ta, calib_parts=cal, test_parts=tst)
    a, b = ax[0, j], ax[1, j]
    a.plot(TS, ex, "-o", ms=3, color="#7b3fb5", label=f"extra errors, calibration ({int((~rc0).sum())} without stop)")
    a.plot(TS, lo, "-s", ms=3, color="#eb6834", label=f"lost packets, test ({int((~rt0).sum())} errors without stop)")
    a.axhline(np.floor(0.02 * (~rc0).sum()), color="#7b3fb5", ls=":", lw=1, label="2 % rule (calibration)")
    b.plot(TS, sv, "-o", ms=3, color="#1f9e6e", label="mean MACs per core saved on test packets")
    for z in (a, b):
        z.axvline(tc, color="#555", ls="--", lw=1, label=f"picked on calibration t={tc}")
        if ta is not None and ta != tc: z.axvline(ta, color="#000", lw=1.5, label=f"adopted t={ta} (live-checked)")
        z.grid(True, ls=":", color="#c3c2b7"); z.set_xlabel(f"F5 threshold t (checkpoint q={q})")
    a.set_yscale("symlog", linthresh=1); a.set_ylabel("packets (symlog)"); b.set_ylabel("MACs saved [%]"); b.set_ylim(-15, max(5, max(sv) + 3))
    verdict = f"adopted t={ta}" if ta is not None else "F5 NOT adopted (saving too small / packets lost)"
    a.set_title(f"{name}: F5 early stop, {verdict}", fontsize=9.5); a.legend(fontsize=6.5); b.legend(fontsize=6.5)
f.suptitle("Why each F5 threshold: calibration extra errors / test lost packets (top) vs MACs saved (bottom); replayed from logged packets", fontsize=11)
f.tight_layout()
f.savefig("BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/tuning/fs_tuning_f5.png", dpi=105, bbox_inches="tight")
json.dump(out, open("fullsys/results/tuning_f5_sweep.json", "w"), indent=1)
print("ok")
