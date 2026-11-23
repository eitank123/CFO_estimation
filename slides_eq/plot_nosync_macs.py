"""Blind vs the real systems' receivers WITHOUT their synchroniser (decoder only, turbo with CRC early stop)
-> slides_eq/fs_macs_nosync_es.png (vs Es/N0 per symbol), fs_macs_nosync_ebn0.png (vs Eb/N0 per payload bit,
known symbols charged).

    python slides_eq/plot_nosync_macs.py

Competitors: data/comp_nosync_ae351ac.json = full-chain-cfo ae351ac DA runs with CRC early stop (DVB-RCS2 da_fs-esd-*,
VDE-SAT da_fs-vda32*), MACs per core = crit_mean minus stage 0 (the CFO / phase estimation); the decodes of the
candidates stay in. Blind: full receiver (its search is its synchronisation), data/fullsys_6350b72.json (DVB 'tuned',
VDE 'final'). MACs per core on the 32-core model.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(os.path.join(HERE, "data", "fullsys_6350b72.json")))
C = json.load(open(os.path.join(HERE, "data", "comp_nosync_ae351ac.json")))["sys"]
NAVY, ORANGE, BROWN = "#003366", "#E07B39", "#8c564b"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
SYS = ("id3", "id13", "id14s", "id42b", "vde")


def blind(k):
    if k == "vde":
        V = B["vde"]
        return "VDE-SAT Link 32 (BPSK 1/4)", [x["es"] for x in V["final"]], [x["macs"] / 1e6 for x in V["final"]], V["off_blind"], V["off_comp"]
    d = B["dvb"][k]
    return (f"DVB-RCS2 {d['name']} ({d['desc'].replace('pi/2', 'π/2')})", d["tuned"]["es"], list(d["tuned"]["mean"]),
            d["off_blind"], d["off_comp"])


def figure(ebn0, fname):
    f, ax = plt.subplots(1, 5, figsize=(21, 5.0))
    for a, k in zip(ax, SYS):
        title, be, bm, ob, oc = blind(k)
        c = C[k]
        ce = np.array([x["es"] for x in c]) + (oc if ebn0 else 0)
        cm = [x["dec"] / 1e6 for x in c]
        be = np.asarray(be, float) + (ob if ebn0 else 0)
        col, mk = (BROWN, "P") if k == "vde" else (ORANGE, "s")
        a.plot(be, bm, "-o", color=NAVY, lw=3, ms=7)
        a.plot(ce, cm, "--" + mk, color=col, lw=2, ms=7)
        v = list(bm) + cm
        lo, hi = min(v) / 1.4, max(v) * 1.4
        a.set_yscale("log")
        a.set_ylim(lo, hi)
        t = [x for x in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2) if lo <= x <= hi]
        a.minorticks_off()
        a.set_yticks(t)
        a.set_yticklabels([f"{x:g}" for x in t])
        a.set_title(title, fontweight="bold", fontsize=12)
        a.set_xlabel("Eb/N0 per payload bit [dB]" if ebn0 else "Es/N0 per symbol [dB]")
        a.grid(True, which="major", ls=":", color="#cccccc")
    ax[0].set_ylabel("mean MACs per core [M] (32 cores)")
    h = [plt.Line2D([], [], color=NAVY, marker="o", lw=3), plt.Line2D([], [], color=ORANGE, marker="s", ls="--", lw=2),
         plt.Line2D([], [], color=BROWN, marker="P", ls="--", lw=2)]
    f.legend(h, ["blind, full receiver (0 known symbols)", "DVB-RCS2",
                 "VDE-SAT"], loc="lower center", ncol=3,
             frameon=False, fontsize=12)
    f.tight_layout(rect=(0, 0.1, 1, 1))
    f.savefig(os.path.join(HERE, fname), dpi=200, facecolor="white")


figure(False, "fs_macs_nosync_es.png")
figure(True, "fs_macs_nosync_ebn0.png")
