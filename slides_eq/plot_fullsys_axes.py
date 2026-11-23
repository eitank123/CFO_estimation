"""Full-system BLER (blind vs DVB-RCS2 IDs 3/13/14/42 and VDE-SAT Link 32) on two x axes -> slides_eq/
    fs_bler_es.png    BLER vs Es/N0 per transmitted symbol: known-symbol (preamble, pilot, syncword) energy NOT charged
    fs_bler_ebn0.png  BLER vs Eb/N0 per payload bit: Es/N0 + 10 log10(burst symbols / payload bits) (known symbols charged)
    fs_macs_{es,ebn0}_before.png  mean MACs per core vs the same two axes, competitors BEFORE their turbo early stop
                      (DVB-RCS2 8 iterations; VDE-SAT already with CRC early stop) 
    fs_macs_{es,ebn0}_after.png   the same with DVB-RCS2's turbo CRC early stop (data/fullsys_es_ae351ac.json,
                      full-chain-cfo ae351ac fullsys/results/da_fs-esd-*.json, crit_mean); VDE-SAT unchanged

    python slides_eq/plot_fullsys_axes.py

Data: slides_eq/data/fullsys_6350b72.json (= full-chain-cfo 1a0daa4 BLIND_IMPLEMENTATION/presentation/fullsys/data/,
made by testing/export_fullsys_slides.py). 'es' is each system's own Es/N0 per burst symbol; off_blind / off_comp =
10 log10(n_sym / payload bits). Blind = jointly tuned receiver (DVB 'tuned', VDE 'final'). Zero-error points not drawn.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "fullsys_6350b72.json")))
NAVY, ORANGE, BROWN = "#003366", "#E07B39", "#8c564b"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
DVB = ("id3", "id13", "id14s", "id42b")


def nz(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return x[y > 0], y[y > 0]


def series(key):
    """(title, blind x Es/N0, blind BLER, comp x Es/N0, comp BLER, off_blind, off_comp, comp colour, comp label)"""
    if key == "vde":
        V = D["vde"]
        return ("VDE-SAT Link 32 (BPSK 1/4)", [x["es"] for x in V["final"]], [x["err"] / x["n"] for x in V["final"]],
                [x["es"] for x in V["comp"]], [x["p"] for x in V["comp"]], V["off_blind"], V["off_comp"], BROWN, "P")
    d = D["dvb"][key]
    t = d["tuned"]
    return (f"DVB-RCS2 {d['name']} ({d['desc'].replace('pi/2', 'π/2')})", t["es"], [e / n for e, n in zip(t["err"], t["n"])],
            [x["es"] for x in d["comp"]], [x["err"] / x["n"] for x in d["comp"]], d["off_blind"], d["off_comp"], ORANGE, "s")


def figure(ebn0, fname):
    f, ax = plt.subplots(1, 5, figsize=(21, 5.0))
    for a, key in zip(ax, DVB + ("vde",)):
        title, be, bp, ce, cp, ob, oc, col, mk = series(key)
        be, ce = np.asarray(be, float) + (ob if ebn0 else 0), np.asarray(ce, float) + (oc if ebn0 else 0)
        a.semilogy(*nz(be, bp), "-o", color=NAVY, lw=3, ms=7)
        a.semilogy(*nz(ce, cp), "--" + mk, color=col, lw=2, ms=7)
        a.set_title(title, fontweight="bold", fontsize=12)
        a.set_xlabel("Eb/N0 per payload bit [dB]" if ebn0 else "Es/N0 per symbol [dB]")
        a.grid(True, which="both", ls=":", color="#cccccc")
    ax[0].set_ylabel("BLER")
    h = [plt.Line2D([], [], color=NAVY, marker="o", lw=3), plt.Line2D([], [], color=ORANGE, marker="s", ls="--", lw=2),
         plt.Line2D([], [], color=BROWN, marker="P", ls="--", lw=2)]
    f.legend(h, ["blind, 0 known symbols", "DVB-RCS2 (known symbols + own data-aided CFO estimate)",
                 "VDE-SAT (syncwords + pilots + own data-aided CFO estimate)"], loc="lower center", ncol=3, frameon=False,
             fontsize=13)
    f.tight_layout(rect=(0, 0.1, 1, 1))
    f.savefig(os.path.join(HERE, fname), dpi=200, facecolor="white")


ES = json.load(open(os.path.join(HERE, "data", "fullsys_es_ae351ac.json")))     # DVB-RCS2 with turbo CRC early stop


def macs_series(key, after=False):
    """MACs per core (M): (blind x, blind MACs, comp x, comp MACs, off_blind, off_comp, colour, marker, title)"""
    if key == "vde":
        V = D["vde"]
        return ([x["es"] for x in V["final"]], [x["macs"] / 1e6 for x in V["final"]], [x["es"] for x in V["comp"]],
                [x["macs"] / 1e6 for x in V["comp"]], V["off_blind"], V["off_comp"], BROWN, "P", "VDE-SAT Link 32 (BPSK 1/4)")
    d = D["dvb"][key]
    t = d["tuned"]
    comp = ES["dvb"][key] if after else d["comp"]
    return (t["es"], list(t["mean"]), [x["es"] for x in comp], [x["macs"] / 1e6 for x in comp],
            d["off_blind"], d["off_comp"], ORANGE, "s", f"DVB-RCS2 {d['name']} ({d['desc'].replace('pi/2', 'π/2')})")


def macs_figure(ebn0, fname, after=False):
    f, ax = plt.subplots(1, 5, figsize=(21, 5.0))
    for a, key in zip(ax, DVB + ("vde",)):
        be, bm, ce, cm, ob, oc, col, mk, title = macs_series(key, after)
        be, ce = np.asarray(be, float) + (ob if ebn0 else 0), np.asarray(ce, float) + (oc if ebn0 else 0)
        a.plot(be, bm, "-o", color=NAVY, lw=3, ms=7)
        a.plot(ce, cm, "--" + mk, color=col, lw=2, ms=7)
        v = list(bm) + list(cm)
        lo, hi = min(v) / 1.4, max(v) * 1.4
        a.set_yscale("log")
        a.set_ylim(lo, hi)
        t = [x for x in (0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5) if lo <= x <= hi]
        a.minorticks_off()
        a.set_yticks(t)
        a.set_yticklabels([f"{x:g}" for x in t])
        a.set_title(title, fontweight="bold", fontsize=12)
        a.set_xlabel("Eb/N0 per payload bit [dB]" if ebn0 else "Es/N0 per symbol [dB]")
        a.grid(True, which="major", ls=":", color="#cccccc")
    ax[0].set_ylabel("mean MACs per core [M] (32 cores)")
    h = [plt.Line2D([], [], color=NAVY, marker="o", lw=3), plt.Line2D([], [], color=ORANGE, marker="s", ls="--", lw=2),
         plt.Line2D([], [], color=BROWN, marker="P", ls="--", lw=2)]
    f.legend(h, ["blind, 0 known symbols", "DVB-RCS2 (synchroniser + turbo with CRC early stop)" if after else
                 "DVB-RCS2 (synchroniser + turbo, 8 iterations, no early stop)",
                 "VDE-SAT (synchroniser + turbo with CRC early stop)"], loc="lower center", ncol=3, frameon=False,
             fontsize=13)
    f.tight_layout(rect=(0, 0.1, 1, 1))
    f.savefig(os.path.join(HERE, fname), dpi=200, facecolor="white")


macs_figure(False, "fs_macs_es_before.png")
macs_figure(True, "fs_macs_ebn0_before.png")
macs_figure(False, "fs_macs_es_after.png", after=True)
macs_figure(True, "fs_macs_ebn0_after.png", after=True)
figure(False, "fs_bler_es.png")
figure(True, "fs_bler_ebn0.png")
