"""Blind with a hard per-packet MAC cap (a packet needing more MACs per core than the cap is an error) vs DVB-RCS2 and
VDE-SAT. Four figures:
  fs_cap_bler_es.png / fs_cap_bler_ebn0.png  BLER vs Es/N0 per symbol / Eb/N0 per payload bit (known symbols charged)
  fs_cap_macs_es.png / fs_cap_macs_ebn0.png  mean MACs per core vs the same axes

    python slides_eq/plot_cap_fullsys.py

Data (full-chain-cfo ae351ac, nothing extrapolated):
  DVB-RCS2 IDs 3/13/42 cap curves: data/capcurve_dvb_ae351ac.json (= fullsys/results/capcurve_id13_3_42.json), the
    blind receiver BEFORE joint tuning (tuning_fullsys.md, "MAC cap / stage cut-off"); no cap curve exists for the tuned one.
  DVB-RCS2 ID 14: no cap data at all; the tuned blind (data/fullsys_6350b72.json) is drawn uncapped only.
  VDE-SAT cap curves: data/fullsys_6350b72.json vde.cap, the blind before the fast-path change (fs-gv32om); no cap
    curve exists for the fast-path receiver.
  Competitors: data/comp_nosync_ae351ac.json (DA runs with turbo CRC early stop); BLER of the real receiver, MACs of the
    decoder only (synchroniser stage 0 removed), as in plot_nosync_macs.py.
MACs per core on the 32-core model; cap values in M MACs per core.
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
K = json.load(open(os.path.join(HERE, "data", "capcurve_dvb_ae351ac.json")))
KEY = {"id13": "ID 13 (QPSK 1/3)", "id3": "ID 3 (QPSK 1/3, short)", "id42b": "ID 42 (pi/2-BPSK 1/3)"}
NAVY, ORANGE, BROWN = "#003366", "#E07B39", "#8c564b"
CAPS = ((None, NAVY, "o", "blind, no cap"), (2.0, "#3f78b5", "v", "blind, cap 2 M"),
        (1.0, "#6aa6d8", "^", "blind, cap 1 M"), (0.5, "#a9cbe8", "D", "blind, cap 0.5 M"))
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
SYS = ("id3", "id13", "id14s", "id42b", "vde")


def blind_curves(k):
    """{cap: (es, bler, mean MACs [M])} for the caps that have data."""
    out = {}
    if k == "vde":
        for c, *_ in CAPS:
            rows = B["vde"]["cap"]["None" if c is None else f"{c:.1f}"]
            es = sorted(float(e) for e in rows)
            out[c] = (es, [rows[f"{e}"]["err"] / rows[f"{e}"]["n"] for e in es], [rows[f"{e}"]["mean"] for e in es])
    elif k in KEY:
        d = K[KEY[k]]
        caps = [None if x is None else x / 1e6 for x in d["caps"]]
        es = sorted(float(e) for e in d["rows"])
        for c, *_ in CAPS:
            i = caps.index(c)
            out[c] = (es, [d["rows"][f"{e}"]["err"][i] / d["rows"][f"{e}"]["n"] for e in es],
                      [d["rows"][f"{e}"]["mac"][i] for e in es])
    else:
        t = B["dvb"][k]["tuned"]
        out[None] = (t["es"], [e / n for e, n in zip(t["err"], t["n"])], list(t["mean"]))
    return out


def meta(k):
    if k == "vde":
        V = B["vde"]
        return "VDE-SAT Link 32 (BPSK 1/4)", V["off_blind"], V["off_comp"]
    d = B["dvb"][k]
    return f"DVB-RCS2 {d['name']} ({d['desc'].replace('pi/2', 'π/2')})", d["off_blind"], d["off_comp"]


def figure(ebn0, what, fname):
    f, ax = plt.subplots(1, 5, figsize=(21, 5.4))
    for a, k in zip(ax, SYS):
        title, ob, oc = meta(k)
        bc = blind_curves(k)
        c = C[k]
        ce = np.array([x["es"] for x in c]) + (oc if ebn0 else 0)
        col, mk = (BROWN, "P") if k == "vde" else (ORANGE, "s")
        vals = []
        for cap, cc, m, _ in CAPS:
            if cap not in bc:
                continue
            es, p, mm = bc[cap]
            x = np.asarray(es, float) + (ob if ebn0 else 0)
            y = np.asarray(p if what == "bler" else mm, float)
            keep = y > 0
            a.plot(x[keep], y[keep], "-" + m, color=cc, lw=3 if cap is None else 2, ms=7 if cap is None else 6)
            vals += list(y[keep])
        if what == "bler":
            cy = np.array([x["err"] / x["n"] for x in c])
        else:
            cy = np.array([x["dec"] / 1e6 for x in c])
        keep = cy > 0
        a.plot(ce[keep], cy[keep], "--" + mk, color=col, lw=2, ms=7)
        a.set_yscale("log")
        if what == "bler":
            a.set_ylim(1e-6, 1)
        else:
            vals += list(cy[keep])
            lo, hi = min(vals) / 1.4, max(vals) * 1.4
            a.set_ylim(lo, hi)
            t = [x for x in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5) if lo <= x <= hi]
            a.minorticks_off()
            a.set_yticks(t)
            a.set_yticklabels([f"{x:g}" for x in t])
        if k == "id14s":
            a.text(0.04, 0.05, "no cap data", transform=a.transAxes, fontsize=11, color="#555555")
        a.set_title(title, fontweight="bold", fontsize=12)
        a.set_xlabel("Eb/N0 per payload bit [dB]" if ebn0 else "Es/N0 per symbol [dB]")
        a.grid(True, which="major", ls=":", color="#cccccc")
    ax[0].set_ylabel("BLER" if what == "bler" else "mean MACs per core [M] (32 cores)")
    h = [plt.Line2D([], [], color=cc, marker=m, lw=3 if cap is None else 2) for cap, cc, m, _ in CAPS]
    h += [plt.Line2D([], [], color=ORANGE, marker="s", ls="--", lw=2), plt.Line2D([], [], color=BROWN, marker="P", ls="--", lw=2)]
    f.legend(h, [l for *_, l in CAPS] + ["DVB-RCS2", "VDE-SAT"], loc="lower center", ncol=6, frameon=False, fontsize=12,
             bbox_to_anchor=(0.5, 0.05))
    f.text(0.5, 0.01, "Cap = MACs per core per packet; a packet needing more is an error. Cap curves: DVB-RCS2 blind before "
           "joint tuning, VDE-SAT blind before the fast-path change. ID 14: tuned blind, no cap.",
           ha="center", fontsize=10.5, color="#555555")
    f.tight_layout(rect=(0, 0.14, 1, 1))
    f.savefig(os.path.join(HERE, fname), dpi=200, facecolor="white")
    plt.close(f)


for ebn0, ax_ in ((False, "es"), (True, "ebn0")):
    figure(ebn0, "bler", f"fs_cap_bler_{ax_}.png")
    figure(ebn0, "macs", f"fs_cap_macs_{ax_}.png")
