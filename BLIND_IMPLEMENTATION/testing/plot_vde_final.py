"""VDE-SAT Link 32 vs blind (2026-11-17): BLER and MACs per core vs Eb/N0 (syncword + pilots charged) and vs SNR.
Blind baseline = 0.15 receiver without NN (coarse start); blind final = with the VDE-trained checkpoint NN (coarse off,
honest --charge-all accounting). VDE: log-MAP 8 it. with CRC early stop, own DA CFO estimate (syncword 192 + pilots 180)."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
OV, OB = 7.68, 6.56          # Eb/N0 per payload bit = Es/N0 + offset (VDE 1641 symbols, blind 1269 symbols, 280-bit payload)
vi = dict(es=[-7.0,-6.5,-6.0,-5.5,-5.0,-4.5,-4.0], p=[931/960,732/960,318/960,100/1920,105/24000,49/300000,2/300000])
vd = dict(es=[-7.0,-6.5,-6.0,-5.5,-5.0,-4.5,-4.0], p=[1.0,119/150,105/270,104/1530,100/19950,63/300000,7/300000],
          m=[.1965,.1664,.1019,.0459,.0291,.0250,.0222])
import glob, json, os
_R = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fullsys", "results")
def _pool(pat, excl=()):
    """Pool every part matching blind_fs_<pat>*.json per Es/N0 (32-core models only: parts with batch null and no
    cores are skipped, their per-core cost uses one core per grid cell)."""
    B = {}
    for fn in glob.glob(os.path.join(_R, f"blind_fs_{pat}*.json")):
        part = os.path.basename(fn)[9:-5]
        if part.endswith("smoke") or any(x in part for x in excl): continue
        d = json.load(open(fn)); s = d["meta"].get("sps") or {}
        if s.get("batch") is None and s.get("cores") is None and "v32" in part and "bv32" not in part and "gv32m" not in part: continue
        for q in d["points"]:
            r = B.setdefault(round(q["esn0"], 2), [0, 0, 0.0, 0.0]); r[0] += q["frames"]; r[1] += q["frame_err"]
            r[2] += q["sum_c_hd4a"]; r[3] = max(r[3], q["max_c_hd4a"])
    e = sorted(B)
    return dict(es=e, p=[B[x][1] / B[x][0] if B[x][1] else float("nan") for x in e], m=[B[x][2] / B[x][0] / 1e6 for x in e], mx=[B[x][3] / 1e6 for x in e],
                n=[B[x][0] for x in e], err=[B[x][1] for x in e])
b0 = _pool("fs-bv32m")                      # no NN (coarse start), seeds 32 / 3232
b1 = _pool("fs-gv32m")                      # previous final: VDE-trained NN, batch (32, 5.0) on 32 cores, seeds 7032 / 7033
import sys as _s
_TUNED = _s.argv[1] if len(_s.argv) > 1 else "fs-gv32km"   # jointly tuned final (joint_v32jr.json pick; r3 = fs-gv32qm)
b2 = _pool(_TUNED)
C = dict(vi="#b5651d", vd="#eb6834", b0="#9a9a9a", b1="#8fcfb4", b2="#1f9e6e")
L = dict(vi="VDE-SAT, ideal sync", vd="VDE-SAT",
         b0="Blind, no NN", b1="Blind, before tuning", b2="Blind, jointly tuned")
f, ax = plt.subplots(2, 2, figsize=(15, 10))
for (a, xl, ov, ob) in ((ax[0, 0], "Eb/N0 per payload bit [dB] (syncword + pilots charged)", OV, OB), (ax[0, 1], "SNR (Es/N0 per symbol) [dB]", 0, 0)):
    a.semilogy(np.array(vi["es"]) + ov, vi["p"], "--o", color=C["vi"], ms=4, lw=1.5, label=L["vi"])
    a.semilogy(np.array(vd["es"]) + ov, vd["p"], "-o", color=C["vd"], ms=5, lw=2, label=L["vd"])
    a.semilogy(np.array(b1["es"]) + ob, b1["p"], "--s", color=C["b1"], ms=5, lw=1.5, label=L["b1"])
    a.semilogy(np.array(b2["es"]) + ob, b2["p"], "-D", color=C["b2"], ms=6, lw=2, label=L["b2"])
    a.set_xlabel(xl); a.set_ylabel("BLER"); a.set_ylim(1e-6, 1.1); a.grid(True, which="both", ls=":", color="#c3c2b7"); a.legend(fontsize=7.5, loc="lower left")
for (a, xl, ov, ob) in ((ax[1, 0], "Eb/N0 per payload bit [dB] (syncword + pilots charged)", OV, OB), (ax[1, 1], "SNR (Es/N0 per symbol) [dB]", 0, 0)):
    for k, d in (("vd", vd), ("b1", b1), ("b2", b2)):
        x = np.array(d["es"]) + (ov if k == "vd" else ob)
        a.semilogy(x, d["m"], "-o" if k == "vd" else "-s", color=C[k], lw=2, ms=5, label=L[k])
        for xx, v in zip(x, d["m"]): a.annotate(f"{v:.3g}", (xx, v), textcoords="offset points", xytext=(4, 4), fontsize=7, color=C[k])
    a.set_xlabel(xl); a.set_ylabel("mean MACs per core per packet [M]"); a.grid(True, which="both", ls=":", color="#c3c2b7"); a.legend(fontsize=7.5)
ax[0, 0].set_title("VDE-SAT Link 32: BLER vs Eb/N0", fontsize=10); ax[0, 1].set_title("VDE-SAT Link 32: BLER vs SNR", fontsize=10)
ax[1, 0].set_title("VDE-SAT Link 32: MACs per core vs Eb/N0", fontsize=10); ax[1, 1].set_title("VDE-SAT Link 32: MACs per core vs SNR", fontsize=10)
f.text(0.01, -0.03, "VDE-SAT: own data-aided CFO estimate (sync word + pilots), turbo log-MAP 8 it., CRC early stop; SNR per despread symbol. "
       "Blind jointly tuned: VDE-trained NN, batch null (32 cores), final 4, win 4.0, shortlist 99.7 %/4" + (", one phase guess" if "gv32o" in _TUNED else "") + ". MACs: mean per core per packet.", fontsize=8)
f.tight_layout(); f.savefig("BLIND_IMPLEMENTATION/testing/results/plots/VDE-SAT/overview/fs_vde32_final.png", dpi=105, bbox_inches="tight"); print("ok")
