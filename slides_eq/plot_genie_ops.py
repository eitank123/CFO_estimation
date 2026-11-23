"""Code-only decoder cost with perfect sync (true CFO, phase, N0): polar CA-SCL-8 (blind's code, rate-matched) vs the
real systems' turbo decoders -> slides_eq/genie_ops.png

    python slides_eq/plot_genie_ops.py

Data: data/genie_ops_ae351ac.json (full-chain-cfo ae351ac fullsys/results, the genie files of
presentation/fullsys/plot_genie.py). Unit: total ops per packet (all cores, the simulator's 'ops' count).
Polar: ops_per_frame (one CA-SCL-8 decode, fixed). Turbo DVB-RCS2: ops_per_frame (8 iterations) and ops_es_equiv
(the same packets with CRC early stop; not in the ID 13 genie file). VDE-SAT: ops_mean (log-MAP with CRC early stop,
its 80 k front end included). Points with BLER 1 at the left edge are kept for the cost.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "genie_ops_ae351ac.json")))["sys"]
NAVY, ORANGE, BROWN = "#003366", "#E07B39", "#8c564b"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})

f, ax = plt.subplots(1, 5, figsize=(21, 5.0))
for a, k in zip(ax, ("id3", "id13", "id14s", "id42b", "vde")):
    s = D[k]
    col = BROWN if k == "vde" else ORANGE
    P = s["polar"]
    a.plot([p["es"] for p in P], [p["ops"] / 1e6 for p in P], "-o", color=NAVY, lw=3, ms=7)
    T8 = [t for t in s["turbo"] if t["ops8"]]
    if T8:
        a.plot([t["es"] for t in T8], [t["ops8"] / 1e6 for t in T8], "--s", color=col, lw=2, ms=6, mfc="white")
    TE = [t for t in s["turbo"] if t["ops_es"]]
    if TE:
        a.plot([t["es"] for t in TE], [t["ops_es"] / 1e6 for t in TE], "-s", color=col, lw=2.4, ms=7)
    a.set_yscale("log")
    v = [p["ops"] / 1e6 for p in P] + [t["ops8"] / 1e6 for t in T8] + [t["ops_es"] / 1e6 for t in TE]
    lo, hi = min(v) / 1.6, max(v) * 1.6
    a.set_ylim(lo, hi)
    tk = [x for x in (0.05, 0.1, 0.2, 0.5, 1, 2, 5) if lo <= x <= hi]
    a.minorticks_off()
    a.set_yticks(tk)
    a.set_yticklabels([f"{x:g}" for x in tk])
    a.set_title(s["name"], fontweight="bold", fontsize=12)
    a.set_xlabel("Es/N0 per symbol [dB] (perfect sync)")
    a.grid(True, which="major", ls=":", color="#cccccc")
    if k == "id13":
        a.text(0.5, 0.62, "early-stop cost not in\nthe ID 13 genie run", transform=a.transAxes, ha="center", fontsize=11,
               color="#555555")
ax[0].set_ylabel("decoder ops per packet [M] (all cores)")
h = [plt.Line2D([], [], color=NAVY, marker="o", lw=3),
     plt.Line2D([], [], color=ORANGE, marker="s", ls="--", lw=2, mfc="white"),
     plt.Line2D([], [], color=ORANGE, marker="s", lw=2.4),
     plt.Line2D([], [], color=BROWN, marker="s", lw=2.4)]
f.legend(h, ["polar CA-SCL-8 (blind's code)", "DVB-RCS2 turbo, 8 iterations", "DVB-RCS2 turbo, CRC early stop",
             "VDE-SAT turbo, CRC early stop"], loc="lower center", ncol=4, frameon=False, fontsize=13)
f.tight_layout(rect=(0, 0.1, 1, 1))
f.savefig(os.path.join(HERE, "genie_ops.png"), dpi=200, facecolor="white")
