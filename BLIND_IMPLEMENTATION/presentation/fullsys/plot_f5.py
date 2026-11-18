"""Frozen-bit early stop (F5) on the full-system DVB-RCS2 waveforms (2026-11-18): median psi of the right (accepted)
and wrong (CRC-failed) CA-SCL decodes vs the share q of the frozen bits seen, with the adopted (q, t) per waveform.
Data: data/f5_psi_fullsys.json (f5_psi_data.py, the F5 calibration decode dumps fs-k13m*, fs-k42, fs-k14).

    py BLIND_IMPLEMENTATION/presentation/fullsys/plot_f5.py      -> fs_f5.png
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "f5_psi_fullsys.json")))
NAVY, RED, ORANGE = "#003366", "#c8423b", "#E07B39"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
QT = {"ID 13": (0.6, 0.80), "ID 14": (0.7, 0.78), "ID 42": (0.9, 0.75)}
f, ax = plt.subplots(1, 3, figsize=(15, 5.0), sharey=True)
for a, name in zip(ax, ("ID 13", "ID 14", "ID 42")):
    d = D[name]; q, t = QT[name]
    hw, = a.plot(d["q"], d["med_wrong"], "s-", color=RED, lw=3, ms=8)
    hr, = a.plot(d["q"], d["med_right"], "o-", color=NAVY, lw=3, ms=8)
    hq = a.axvline(q, color=ORANGE, ls="--", lw=2.5)
    ht = a.axhline(t, color="#555555", ls=":", lw=2)
    a.set_title(f"DVB-RCS2 {name}  (q = {q:g}, t = {t:.2f})", fontweight="bold")
    a.set_xlabel("share q of the frozen bits seen"); a.grid(True, ls=":", color="#cccccc"); a.set_xlim(0.2, 1.02)
ax[0].set_ylabel("ψ: mean frozen-bit penalty (median)")
f.legend([hw, hr, hq, ht], ["decodes at a wrong hypothesis", "decodes at the right hypothesis", "the check (q)",
                            "stop threshold t"], loc="lower center", ncol=4, frameon=False, fontsize=13)
f.tight_layout(rect=(0, 0.09, 1, 1)); f.savefig(os.path.join(HERE, "fs_f5.png"), dpi=200); plt.close(f)
print("ok")
