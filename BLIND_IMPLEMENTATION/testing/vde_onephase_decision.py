"""VDE one-phase-guess decision (2026-11-18): paired comparison jointly tuned (2 phase guesses) vs + one phase guess
(nph 2) on every paired run: fresh seeds 7032/7033 (fs-gv32k vs fs-gv32o), 7033 (fs-jv32x1 vs x2), 7034 (x3/x5 vs
x4/x6); calibration seed 8032 (fs-jv32u / fs-jv32c0 vs fs-jv32w1 / w6). Per point: errors, packets lost / gained
(paired per chunk), mean MACs per core, change. Verdict: pooled over the fresh runs at -5.0 and -4.6 dB, extra errors
vs floor(0.02 x tuned errors) (the 2 % rule)."""
import json, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, "fullsys", "results", "blind_fs_")
PAIRS = [("fresh 7032", "fs-gv32k", "fs-gv32o", ["m66", "m62", "m58", "m54", "m50", "m46", "m42", "m38", "m38s2"]),
         ("fresh 7033", "fs-jv32x1", "fs-jv32x2", ["m50", "m46"]),
         ("fresh 7034 -5.0", "fs-jv32x3", "fs-jv32x4", ["m50"]),
         ("fresh 7034 -4.6", "fs-jv32x5", "fs-jv32x6", ["m46"]),
         ("calib 8032 (20k)", "fs-jv32u", "fs-jv32w1", ["am62", "bm54", "cm46"]),
         ("calib 8032 (60k)", "fs-jv32c0", "fs-jv32w6", ["m50", "m46"])]


def load(part):
    f = R + part + ".json"
    return json.load(open(f))["points"][0] if os.path.exists(f) else None


pool = {}
print("| run | Es/N0 | errors tuned | errors 1 phase | lost / gained | MACs tuned [M] | MACs 1 phase [M] | change |")
print("|---|---|---|---|---|---|---|---|")
for lab, a_, b_, pts in PAIRS:
    for pt in pts:
        A, B = load(a_ + pt), load(b_ + pt.replace("am", "m").replace("bm", "m").replace("cm", "m") if b_ == "fs-jv32w1" else b_ + pt)
        if A is None or B is None:
            print(f"| {lab} | {pt} | (missing) | | | | | |")
            continue
        cc = {c["c"] for c in A["chunks"]} & {c["c"] for c in B["chunks"]}
        sa = {(c["c"], i) for c in A["chunks"] for i in c["fe_idx"] if c["c"] in cc}
        sb = {(c["c"], i) for c in B["chunks"] for i in c["fe_idx"] if c["c"] in cc}
        ma, mb = A["sum_c_hd4a"] / A["frames"] / 1e6, B["sum_c_hd4a"] / B["frames"] / 1e6
        e = round(A["esn0"], 1)
        print(f"| {lab} | {e:+.1f} | {A['frame_err']}/{A['frames']} | {B['frame_err']}/{B['frames']} | {len(sb - sa)} / {len(sa - sb)} "
              f"| {ma:.3f} | {mb:.3f} | {(mb / ma - 1) * 100:+.0f} % |")
        if lab.startswith("fresh") and e in (-5.0, -4.6):
            p = pool.setdefault(e, [0, 0, 0, 0]); p[0] += len(sa); p[1] += len(sb); p[2] += len(sb - sa); p[3] += len(sa - sb)
print()
ok = True
for e, (ea, eb, lost, gained) in sorted(pool.items()):
    allow = int(np.floor(0.02 * ea))
    v = eb - ea <= allow
    ok &= v
    print(f"pooled fresh {e:+.1f} dB: tuned {ea} errors, one phase {eb} (lost {lost}, gained {gained}); extra {eb - ea:+d}, "
          f"allowed {allow} -> {'PASS' if v else 'FAIL'}")
print("VERDICT:", "ADOPT one phase guess" if ok and pool else "KEEP the jointly tuned receiver (2 phase guesses)" if pool else "no data yet")
