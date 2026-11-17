"""Burst layouts of the compared real systems for the slides (2026-11-18): where the known symbols sit.
Positions are read from the implementation (fullsys/rcs2.py Waveform.known_idx, fullsys/vde.py VDELink sync_pos /
pilot_pos) and saved to data/layouts_fullsys.json.

    py BLIND_IMPLEMENTATION/presentation/fullsys/plot_layouts.py

fs_rcs2_layout.png  DVB-RCS2 IDs 3, 13, 14, 42: preamble, pilots, postamble along the burst (to scale), + zoom
fs_vde_layout.png   VDE-SAT Link 32: 4 syncwords and the pilots along the 1641-symbol burst (to scale), + zoom
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "fullsys"))
from fullsys import rcs2, vde   # noqa: E402

plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
DATA, KNOWN, SYNC = "#d9e2ec", "#E07B39", "#8c564b"
lay = {}
for k in (3, 13, 14, 42):
    wf = rcs2.Waveform(k)
    lay[f"rcs2_{k}"] = dict(L=int(wf.L), known=[int(x) for x in wf.known_idx])
v = vde.VDELink(32)
lay["vde32"] = dict(L=int(v.n_sym), sync=[int(x) for x in v.sync_pos], pilot=[int(x) for x in v.pilot_pos])
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(lay, open(os.path.join(HERE, "data", "layouts_fullsys.json"), "w"))


def strip(a, L, kinds, y=0, h=0.6, thin=False):
    """thin: the full-burst view; isolated symbols are drawn as fixed-width lines so none drops below a pixel."""
    a.add_patch(Rectangle((0, y), L, h, color=DATA, lw=0))
    for pos, col in kinds:
        pos = np.asarray(pos)
        if thin:
            iso = np.array([p for p in pos if (p - 1 not in pos) and (p + 1 not in pos)])
            run = np.array([p for p in pos if p not in set(iso)])
            if len(iso):
                a.vlines(iso + 0.5, y, y + h, color=col, lw=1.6)
            pos = run
        for p in pos:
            a.add_patch(Rectangle((p, y), 1, h, color=col, lw=0))


# DVB-RCS2
INFO = {3: "ID 3: QPSK 1/3, 272-bit payload", 13: "ID 13: QPSK 1/3, 952-bit payload",
        14: "ID 14: QPSK 1/2, 1472-bit payload", 42: "ID 42: pi/2-BPSK 1/3, 952-bit payload"}
f, ax = plt.subplots(1, 2, figsize=(17, 5.2), gridspec_kw=dict(width_ratios=[3, 1.2]))
for i, k in enumerate((3, 13, 14, 42)):
    d = lay[f"rcs2_{k}"]; y = 3 - i
    strip(ax[0], d["L"], [(d["known"], KNOWN)], y=y, thin=True)
    ax[0].text(0, y + 0.72, f"{INFO[k]}: {d['L']} symbols, {len(d['known'])} known ({100 * len(d['known']) / d['L']:.1f} %)", fontsize=12)
    strip(ax[1], 120, [([p for p in d["known"] if p < 120], KNOWN)], y=y)
ax[0].set_xlim(-20, 3300); ax[0].set_ylim(-0.2, 4); ax[0].set_yticks([]); ax[0].set_xlabel("symbol index in the burst")
ax[0].set_title("Burst layout (to scale)", fontweight="bold")
ax[1].set_xlim(0, 120); ax[1].set_ylim(-0.2, 4); ax[1].set_yticks([]); ax[1].set_xlabel("first 120 symbols")
ax[1].set_title("Zoom: preamble, then 1 pilot every P", fontweight="bold")
for a in ax:
    for s in ("left", "right", "top"): a.spines[s].set_visible(False)
h = [Rectangle((0, 0), 1, 1, color=DATA), Rectangle((0, 0), 1, 1, color=KNOWN)]
f.legend(h, ["data symbols", "known symbols (preamble, pilots, postamble)"], loc="lower center", ncol=2, frameon=False)
f.tight_layout(rect=(0, 0.08, 1, 1)); f.savefig(os.path.join(HERE, "fs_rcs2_layout.png"), dpi=200); plt.close(f)

# VDE-SAT Link 32
d = lay["vde32"]
f, ax = plt.subplots(2, 1, figsize=(15, 4.4))
strip(ax[0], d["L"], [(d["pilot"], KNOWN), (d["sync"], SYNC)], h=0.8, thin=True)
ax[0].set_xlim(-10, d["L"] + 10); ax[0].set_ylim(0, 1); ax[0].set_yticks([])
ax[0].set_title(f"VDE-SAT Link 32: {d['L']} symbols = 1269 data + {len(d['sync'])} syncword + {len(d['pilot'])} pilot "
                f"({100 * (len(d['sync']) + len(d['pilot'])) / d['L']:.0f} % known)", fontweight="bold")
strip(ax[1], 140, [([p for p in d["pilot"] if p < 140], KNOWN), ([p for p in d["sync"] if p < 140], SYNC)], h=0.8)
ax[1].set_xlim(0, 140); ax[1].set_ylim(0, 1); ax[1].set_yticks([]); ax[1].set_xlabel("symbol index (zoom: first 140 symbols)")
for a in ax:
    for s in ("left", "right", "top"): a.spines[s].set_visible(False)
h = [Rectangle((0, 0), 1, 1, color=DATA), Rectangle((0, 0), 1, 1, color=SYNC), Rectangle((0, 0), 1, 1, color=KNOWN)]
f.legend(h, ["data symbols", "48-symbol syncword (x4)", "single pilot (every 8 symbols)"], loc="lower center", ncol=3, frameon=False)
f.tight_layout(rect=(0, 0.1, 1, 1)); f.savefig(os.path.join(HERE, "fs_vde_layout.png"), dpi=200); plt.close(f)
print("ok")
