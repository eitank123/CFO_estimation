"""Genie vs genie (2026-11-18): how much the turbo code itself is worth, and that blind still wins.
Per system, BLER vs SNR of
  - the real system's turbo code with perfect sync (true CFO, phase, N0; code only, no known symbols needed),
  - our rate-matched polar code with perfect sync (CA-SCL-8, CRC-32; same payload and data symbols),
  - the real system with its known symbols and its own data-aided CFO estimate (known-symbol energy charged),
  - blind with 0 known symbols (jointly tuned).
Sources (fullsys/results): turbo ideal-sync rcs2_fs-{q3ti, rcs2v13, rcs2v14, q42ti}.json, vde_fs-{v32a, v32lo}.json;
polar genie polar_genie_fs-{q3pg8, pgga-13, pgga-14s, q42pg8, pgv2a, pgv2b}.json (GA design for DVB-RCS2 and PW for
VDE-SAT, as the blind receivers); real curves from data/fullsys_6350b72.json. Snapshot: data/genie_fullsys.json.

    py BLIND_IMPLEMENTATION/presentation/fullsys/plot_genie.py      -> fs_genie.png
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "..", "..", "fullsys", "results")
D = json.load(open(os.path.join(HERE, "data", "fullsys_6350b72.json")))
NAVY, ORANGE, BROWN = "#003366", "#E07B39", "#8c564b"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
XL = "SNR [dB] (perfect sync, code only)"
SYS = [("id3", "DVB-RCS2 ID 3", ["rcs2_fs-q3ti"], ["polar_genie_fs-q3pg8"], ORANGE),
       ("id13", "DVB-RCS2 ID 13", ["rcs2_fs-rcs2v13"], ["polar_genie_fs-pgga-13"], ORANGE),
       ("id14s", "DVB-RCS2 ID 14", ["rcs2_fs-rcs2v14"], ["polar_genie_fs-pgga-14s"], ORANGE),
       ("id42b", "DVB-RCS2 ID 42", ["rcs2_fs-q42ti"], ["polar_genie_fs-q42pg8"], ORANGE),
       ("vde", "VDE-SAT Link 32", ["vde_fs-v32a", "vde_fs-v32lo"], ["polar_genie_fs-pgv2a", "polar_genie_fs-pgv2b"], BROWN)]


def pool(names):
    P = {}
    for n in names:
        for q in json.load(open(os.path.join(RES, n + ".json")))["points"]:
            r = P.setdefault(round(q["esn0"], 2), [0, 0]); r[0] += q["frame_err"]; r[1] += q["frames"]
    return [dict(es=e, err=P[e][0], n=P[e][1]) for e in sorted(P)]


def cross(pts, t=1e-3):
    pts = [(p["es"], p["err"] / p["n"]) for p in pts if p["err"] > 0]
    for (x0, p0), (x1, p1) in zip(pts, pts[1:]):
        if p0 >= t >= p1:
            return x0 + (np.log(t) - np.log(p0)) / (np.log(p1) - np.log(p0)) * (x1 - x0)
    return None


snap = {}
for key, name, tu, po, col in SYS:
    if key == "vde":
        V = D["vde"]; sh = V["off_comp"] - V["off_blind"]
        real = [dict(es=c["es"] + sh, err=c["p"] * 1e6, n=1e6) for c in V["comp"]]
        blind = [dict(es=x["es"], err=x["err"], n=x["n"]) for x in V["final"]]
    else:
        d = D["dvb"][key]; sh = d["off_comp"] - d["off_blind"]
        real = [dict(es=c["es"] + sh, err=c["err"], n=c["n"]) for c in d["comp"]]
        t = d["tuned"]; blind = [dict(es=e, err=r, n=n) for e, r, n in zip(t["es"], t["err"], t["n"])]
    snap[key] = dict(name=name, turbo_genie=pool(tu), polar_genie=pool(po), real=real, blind=blind, shift_db=sh)
json.dump(snap, open(os.path.join(HERE, "data", "genie_fullsys.json"), "w"), indent=1)

f, ax = plt.subplots(1, 5, figsize=(22, 5.4))
for a, (key, name, tu, po, col) in zip(ax, SYS):
    s = snap[key]
    for k, sty, c in (("turbo_genie", "-s", col), ("polar_genie", "-o", NAVY)):
        x = [p["es"] for p in s[k] if p["err"] > 0]; y = [p["err"] / p["n"] for p in s[k] if p["err"] > 0]
        a.semilogy(x, y, sty, color=c, lw=3, ms=8)
    xt, xp, xr, xb = (cross(s[k]) for k in ("turbo_genie", "polar_genie", "real", "blind"))
    s["x1e-3"] = dict(turbo_genie=xt, polar_genie=xp, real=xr, blind=xb)
    a.set_xlim(min(xt, xp) - 0.7, max(xt, xp) + 0.6); a.set_ylim(1e-5, 1)
    a.set_title(name, fontweight="bold"); a.grid(True, which="both", ls=":", color="#cccccc"); a.set_xlabel(XL)
    if a is ax[0]:
        a.set_ylabel("BLER")
H = [plt.Line2D([], [], ls="-", marker="s", color=ORANGE, lw=3, ms=8), plt.Line2D([], [], ls="-", marker="o", color=NAVY, lw=3, ms=8)]
f.legend(H, ["turbo code of the real system (VDE-SAT: brown)", "our polar code, CA-SCL-8"], loc="lower center", ncol=2,
         frameon=False, fontsize=14)
f.tight_layout(rect=(0, 0.09, 1, 1)); f.savefig(os.path.join(HERE, "fs_genie.png"), dpi=200); plt.close(f)
json.dump(snap, open(os.path.join(HERE, "data", "genie_fullsys.json"), "w"), indent=1)
for k, s in snap.items():
    print(k, {a: round(b, 3) for a, b in s["x1e-3"].items()})
