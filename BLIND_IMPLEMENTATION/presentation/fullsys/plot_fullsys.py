"""Full-system slides (2026-11-18): the blind receiver (jointly tuned, no known symbols) vs the deployed systems
DVB-RCS2 (waveform IDs 13, 42, 3, 14; own data-aided CFO estimate, turbo max-log 8 it., CRC early stop) and VDE-SAT Link 32 (own
data-aided CFO estimate, turbo log-MAP 8 it., CRC early stop), same payload, CFO range +-0.03. Data:
data/fullsys_fastvde_es.json (2026-11-23: as fullsys_fastvde.json but the DVB-RCS2 competitor with turbo CRC early
stop, the da_fs-esd-* re-runs: export_fullsys_slides.py --comp-es; same decisions, only its MACs change) /
data/fullsys_fastvde.json (2026-11-19, BLIND_IMPLEMENTATION/testing/export_fullsys_slides.py): as fullsys_6350b72.json
(full-chain-cfo 6350b72) but VDE "final" = blind with the fast path on at every SNR (fs-i9q-m*, -5.8 ... -3.8 dB); the
previous final (fs-gv32om*) is kept as "before_fast" and not drawn.

    python slides_eq/plot_fullsys.py

fs_dvb_bler.png    BLER vs Eb/N0 per payload bit (known symbols charged), one panel per DVB-RCS2 ID
fs_dvb_macs.png    mean MACs per core vs Eb/N0, same panels
fs_vde.png         VDE-SAT: BLER vs Eb/N0 and mean MACs per core vs Eb/N0 (blind before / after joint tuning)
fs_vde_cap.png     VDE-SAT, blind with a per-packet MAC cap (2 / 1 / 0.5 M per core); STALE receiver: the cap curves
                   are of before_fast (fast path off), marked in the figure until a fast-path cap curve exists
fs_scoreboard.png  lead of blind at BLER 1e-3 (dB) and the MAC ratio blind / competitor near that point, all 5 systems
Zero-error points are not drawn; MACs = mean per core per packet on the 32-core scheduled model.
"""
import json
import os

import numpy as np
import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "data", "fullsys_fastvde_es.json")))
NAVY, LIGHT, ORANGE, BROWN = "#003366", "#7f9fbf", "#E07B39", "#8c564b"
CAPC = {"2.0": "#4a6f99", "1.0": "#7f9fbf", "0.5": "#b8c9db"}
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
DVB = ("id3", "id13", "id14s", "id42b")              # by burst length (536, 1616, 1616, 3236 symbols)
XL = "SNR [dB], known-symbol energy charged"   # blind Es/N0; competitor Es/N0 + its known-symbol energy (same Eb/N0 per payload bit)
MT = [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5]


def mticks(a, vals):
    """MAC axes in M with plain ticks, no minor ticks (deck style)."""
    lo, hi = min(vals) / 1.3, max(vals) * 1.3
    t = [x for x in MT if lo <= x <= hi]
    a.set_yscale("log"); a.set_ylim(lo, hi); a.set_yticks(t); a.set_yticklabels([f"{x:g}" for x in t])
    a.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())


def cross(es, p, target=1e-3):
    pts = [(e, q) for e, q in zip(es, p) if q > 0]
    for (e0, p0), (e1, p1) in zip(pts, pts[1:]):
        if p0 >= target >= p1:
            t = (np.log10(p0) - np.log10(target)) / (np.log10(p0) - np.log10(p1))
            return e0 + t * (e1 - e0)
    return None


def nz(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = y > 0
    return x[m], y[m]


def legend_below(f, handles, labels, ncol):
    f.legend(handles, labels, loc="lower center", ncol=ncol, frameon=False, fontsize=13)


def style(a, xl, yl=None):
    a.grid(True, which="both", ls=":", color="#cccccc"); a.set_xlabel(xl)
    if yl:
        a.set_ylabel(yl)


def dvb_series(fmt):
    d = D["dvb"][fmt]
    c = d["comp"]; t = d["tuned"]
    ce = np.array([x["es"] for x in c]) + d["off_comp"] - d["off_blind"]
    cp = [x["err"] / x["n"] for x in c]
    cm = [x["macs"] for x in c]
    te = np.array(t["es"])
    tp = [e / n for e, n in zip(t["err"], t["n"])]
    return d, ce, cp, cm, te, tp, np.array(t["mean"]) * 1e6        # summary MACs are in M


# 1) DVB-RCS2 BLER
f, ax = plt.subplots(1, 4, figsize=(17, 5.2))
for a, fmt in zip(ax, DVB):
    d, ce, cp, cm, te, tp, tm = dvb_series(fmt)
    hb, = a.semilogy(*nz(te, tp), "-o", color=NAVY, lw=3, ms=8)
    hc, = a.semilogy(*nz(ce, cp), "--s", color=ORANGE, lw=2, ms=7)
    a.set_title(f"{d['name']} ({d['desc'].replace('pi/2', 'π/2')})", fontweight="bold")
    style(a, XL, "BLER" if a is ax[0] else None)
legend_below(f, [hb, hc], ["blind, 0 known symbols", "DVB-RCS2, known symbols + own data-aided CFO estimate"], 2)
f.tight_layout(rect=(0, 0.1, 1, 1)); f.savefig(os.path.join(HERE, "fs_dvb_bler.png"), dpi=200); plt.close(f)

# 2) DVB-RCS2 MACs
f, ax = plt.subplots(1, 4, figsize=(17, 5.2))
for a, fmt in zip(ax, DVB):
    d, ce, cp, cm, te, tp, tm = dvb_series(fmt)
    hb, = a.plot(te, np.array(tm) / 1e6, "-o", color=NAVY, lw=3, ms=8)
    hc, = a.plot(ce, np.array(cm) / 1e6, "--s", color=ORANGE, lw=2, ms=7)
    mticks(a, list(np.array(tm) / 1e6) + list(np.array(cm) / 1e6))
    a.set_title(f"{d['name']} ({d['desc'].replace('pi/2', 'π/2')})", fontweight="bold")
    style(a, XL, "mean MACs per core [M] (32 cores)" if a is ax[0] else None)
legend_below(f, [hb, hc], ["blind, 0 known symbols", "DVB-RCS2 (synchroniser + turbo decoder, CRC early stop)"], 2)
f.tight_layout(rect=(0, 0.1, 1, 1)); f.savefig(os.path.join(HERE, "fs_dvb_macs.png"), dpi=200); plt.close(f)

# 3) VDE-SAT: BLER and MACs vs Eb/N0
V = D["vde"]
ce = np.array([x["es"] for x in V["comp"]]) + V["off_comp"] - V["off_blind"]; cp = [x["p"] for x in V["comp"]]; cm = [x["macs"] for x in V["comp"]]
fe = np.array([x["es"] for x in V["final"]]); fp = [x["err"] / x["n"] for x in V["final"]]; fm = [x["macs"] for x in V["final"]]
be = np.array([x["es"] for x in V["before"]]); bm = [x["macs"] for x in V["before"]]
f, ax = plt.subplots(1, 2, figsize=(14, 5.4))
hb, = ax[0].semilogy(*nz(fe, fp), "-o", color=NAVY, lw=3, ms=8)
hc, = ax[0].semilogy(*nz(ce, cp), "--P", color=BROWN, lw=2, ms=8)
xb, xc = cross(fe, fp), cross(ce, cp)
ax[0].set_title("BLER", fontweight="bold"); style(ax[0], XL, "BLER")
ax[1].plot(fe, np.array(fm) / 1e6, "-o", color=NAVY, lw=3, ms=8)
ax[1].plot(ce, np.array(cm) / 1e6, "--P", color=BROWN, lw=2, ms=8)
mticks(ax[1], list(np.array(fm) / 1e6) + list(np.array(cm) / 1e6))
ax[1].set_title("mean MACs per core [M] (32 cores)", fontweight="bold"); style(ax[1], XL)
legend_below(f, [hb, hc], ["blind, 0 known symbols",
                           f"VDE-SAT ({V['known']} known: syncwords + pilots)"], 2)
f.tight_layout(rect=(0, 0.1, 1, 1)); f.savefig(os.path.join(HERE, "fs_vde.png"), dpi=200); plt.close(f)

# 4) VDE-SAT, final blind with a MAC cap
cap = V["cap"]
f, ax = plt.subplots(1, 2, figsize=(14, 5.4)); H = []; MV = []
for c, col, lab in (("None", NAVY, "blind, no cap"), ("2.0", CAPC["2.0"], "cap 2 M per core"),
                    ("1.0", CAPC["1.0"], "cap 1 M per core"), ("0.5", CAPC["0.5"], "cap 0.5 M per core")):
    rows = cap[c]; es = np.array(sorted(float(k) for k in rows))
    p = [rows[str(e)]["err"] / rows[str(e)]["n"] for e in es]; m = [rows[str(e)]["mean"] * 1e6 for e in es]       # cap curve MACs are in M
    h, = ax[0].semilogy(*nz(es, p), "-o", color=col, lw=3 if c == "None" else 2, ms=7)
    ax[1].plot(es, np.array(m) / 1e6, "-o", color=col, lw=3 if c == "None" else 2, ms=7); H.append((h, lab)); MV += list(np.array(m) / 1e6)
hc, = ax[0].semilogy(*nz(ce, cp), "--P", color=BROWN, lw=2, ms=8); H.append((hc, "VDE-SAT"))
ax[1].plot(ce, np.array(cm) / 1e6, "--P", color=BROWN, lw=2, ms=8); mticks(ax[1], MV + list(np.array(cm) / 1e6))
ax[0].set_title("BLER", fontweight="bold"); style(ax[0], XL, "BLER")
ax[1].set_title("mean MACs per core [M] (32 cores)", fontweight="bold"); style(ax[1], XL)
legend_below(f, [h for h, _ in H], [l for _, l in H], 5)
if "cap_rx" in V:                                     # cap curves not of the final receiver: say so in the figure
    f.suptitle("MAC cap on the receiver before the fast-path change (fast path off below 0.5 dB); fast-path cap curve pending",
               fontsize=12, color=BROWN)
f.tight_layout(rect=(0, 0.1, 1, 0.95 if "cap_rx" in V else 1)); f.savefig(os.path.join(HERE, "fs_vde_cap.png"), dpi=200); plt.close(f)

# 5) scoreboard: lead at BLER 1e-3 and MAC ratio near it
names, lead, ratio = [], [], []
for fmt in DVB:
    d, ce_, cp_, cm_, te_, tp_, tm_ = dvb_series(fmt)
    xb_, xc_ = cross(te_, tp_), cross(ce_, cp_)
    names.append(f"DVB-RCS2\n{d['name']}"); lead.append(xc_ - xb_)
    ratio.append(np.interp(xb_, te_, tm_) / np.interp(xc_, ce_, cm_))
names.append("VDE-SAT\nLink 32"); lead.append(xc - xb); ratio.append(np.interp(xb, fe, fm) / np.interp(xc, ce, cm))
f, ax = plt.subplots(1, 2, figsize=(14, 5.4))
b = ax[0].bar(names, lead, color=NAVY)
for r, v in zip(b, lead):
    ax[0].text(r.get_x() + r.get_width() / 2, v + 0.02, f"+{v:.2f} dB", ha="center", fontsize=13, fontweight="bold")
ax[0].set_ylabel("blind lead at BLER 10$^{-3}$ [dB]"); ax[0].set_ylim(0, max(lead) * 1.2)
ax[0].set_title("SNR saved by sending no known symbols", fontweight="bold"); ax[0].grid(True, axis="y", ls=":", color="#cccccc")
b = ax[1].bar(names, ratio, color=[NAVY if r > 1 else "#3a7d44" for r in ratio])
for r, v in zip(b, ratio):
    ax[1].text(r.get_x() + r.get_width() / 2, v * 1.08, f"{v:.1f}x", ha="center", fontsize=13, fontweight="bold")
ax[1].axhline(1, color="#555555", lw=1); ax[1].set_yscale("log"); ax[1].set_ylim(0.3, max(ratio) * 2.5)
ax[1].set_ylabel("MACs per core: blind / real system"); ax[1].set_title("compute, each at its own BLER 10$^{-3}$ SNR\n(< 1: blind cheaper)", fontweight="bold")
ax[1].grid(True, axis="y", which="both", ls=":", color="#cccccc")
f.tight_layout(); f.savefig(os.path.join(HERE, "fs_scoreboard.png"), dpi=200); plt.close(f)
print("leads", [round(x, 2) for x in lead], "ratios", [round(x, 2) for x in ratio])
