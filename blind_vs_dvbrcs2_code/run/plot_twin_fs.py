"""
Twin-design blind receiver vs today's blind receiver vs the DVB-RCS2 competitor (sync_cfo/PLAN_twin_receiver.md, known
timing), one panel per format (id13, id3, id14s: ID 14 has no twin arms):

    competitor  DVB-RCS2 with its known-symbol data-aided sync and turbo WITH CRC early stop: the da_fs-esd points of
                BLIND_IMPLEMENTATION/presentation/fullsys/data/fullsys_fastvde_es.json dvb/<fmt>/comp (es, err, n, macs =
                mean MACs per core)
    blind       run_blind_fs parts: a0 (today, no twin), ta / tb / tc (search:k12 / k18 / k24:rd, --twin-fe jt), d (search:k18:rd,
                twin FE off); the full parts fs-tw-full-<fmt>-<arm>-<snr> where present, else the small fs-tw-s-<fmt>-<arm>
                (never both: same seed = the same packets); BLER = frame_err / frames, MACs = macs_per_core_std (c_d4a, 32
                cores, frames-weighted)
    axes        Es/N0 per transmitted symbol (both systems as run); *_ebn0: Eb/N0 per payload bit, blind es + off_blind,
                competitor es + off_comp (its known-symbol energy charged, as plot_fullsys.py's off_comp / off_blind)

    py fullsys/plot_twin_fs.py     -> BLIND_IMPLEMENTATION/testing/results/twin_fs_{bler,macs}{,_ebn0}.png
Zero-error points are not drawn on BLER; nothing below Es/N0 -5 dB.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "run", "results")
OUT = os.path.join(ROOT, "run", "figs")
COMP = os.path.join(ROOT, "run", "data", "fullsys_fastvde_es.json")
FMTS = ("id13", "id3", "id14s")
SNR_TAGS = {"id13": ("m12", "m10", "m08", "m06", "m04", "m02", "p00"), "id3": ("m06", "m04", "m02", "p00", "p02", "p04", "p06"),
            "id14s": ("p12", "p14", "p20")}
# ID 14 (no twins possible, <= 6 pairs): a0 / av at 1.6 / 1.8 dB are the existing ops-unit parts (same args, seed 7014)
EXTRA = {("id14s", "a0"): ("fs-ops-g14p16", "fs-ops-g14p18"), ("id14s", "av"): ("fs-vvp-v-g14p16", "fs-vvp-v-g14p18")}
ARMS = [("a0", "blind today (r^4 CFO line, no twins)", "#003366", "-o"),
        ("av", "blind today + r^4/|r|^2 CFO line (no twins)", "#7f9fbf", "--o"),
        ("ta", "blind, 12 moved bits (twins) + twin CFO", "#2ca02c", "-^"),
        ("tb", "blind, 18 moved bits (twins) + twin CFO", "#17becf", "-v"),
        ("tc", "blind, 24 moved bits (twins) + twin CFO", "#9467bd", "-D"),
        ("d", "blind, 18 moved bits, twin CFO off", "#7f7f7f", ":x")]
ORANGE = "#E07B39"
ES_MIN = -5.0
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})


def _load(name):
    p = os.path.join(RES, f"blind_fs_{name}.json")
    return json.load(open(p))["points"] if os.path.exists(p) else None


def arm_points(fmt, arm):
    """{esn0: [err, frames, sum macs per core]}: the full parts if any exist, else the small part."""
    full = [q for t in SNR_TAGS[fmt] for q in (_load(f"fs-tw-full-{fmt}-{arm}-{t}") or [])]
    full += [q for n in EXTRA.get((fmt, arm), ()) for q in (_load(n) or [])]
    pts = full or (_load(f"fs-tw-s-{fmt}-{arm}") or [])
    P = {}
    for q in pts:
        r = P.setdefault(round(q["esn0"], 2), [0, 0, 0.0])
        r[0] += q["frame_err"]
        r[1] += q["frames"]
        r[2] += q["macs_per_core_std"] * q["frames"]
    src = "full" if full else ("small" if pts else "missing")
    return {e: v for e, v in sorted(P.items()) if e >= ES_MIN}, src


def comp_points(fmt):
    d = json.load(open(COMP))["dvb"][fmt]
    c = [x for x in d["comp"] if x["es"] >= ES_MIN]
    return d, np.array([x["es"] for x in c]), np.array([x["err"] / x["n"] for x in c]), np.array([x["macs"] for x in c])


def _nz(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    return x[y > 0], y[y > 0]


def plot(kind, ebn0):
    f, ax = plt.subplots(1, len(FMTS), figsize=(6.5 * len(FMTS), 5.6))
    hs, ls = [], []
    for a, fmt in zip(np.atleast_1d(ax), FMTS):
        d, ce, cp, cm = comp_points(fmt)
        ob, oc = (d["off_blind"], d["off_comp"]) if ebn0 else (0.0, 0.0)
        if kind == "bler":
            h, = a.semilogy(*_nz(ce + oc, cp), "--s", color=ORANGE, lw=2, ms=7)
        else:
            h, = a.semilogy(ce + oc, cm / 1e6, "--s", color=ORANGE, lw=2, ms=7)
        lab = ["DVB-RCS2 (known symbols + own DA sync, turbo, CRC early stop)"]
        hh = [h]
        for arm, nm, col, mk in ARMS:
            P, src = arm_points(fmt, arm)
            if not P:
                print(f"  {fmt} {arm}: no parts")
                continue
            e = np.array(list(P)) + ob
            v = np.array(list(P.values()))
            y = v[:, 0] / v[:, 1] if kind == "bler" else v[:, 2] / v[:, 1] / 1e6
            h, = (a.semilogy(*_nz(e, y), mk, color=col, lw=2.5, ms=7) if kind == "bler"
                  else a.semilogy(e, y, mk, color=col, lw=2.5, ms=7))
            hh.append(h)
            lab.append(nm)
            print(f"  {fmt} {arm} ({src}): " + ", ".join(f"{k:+.2f} dB {int(r[0])}/{int(r[1])} {r[2] / r[1] / 1e6:.3f} M"
                                                       for k, r in P.items()))
        a.set_title(f"{d['name']} ({d['desc']})", fontweight="bold")
        a.grid(True, which="both", ls=":", color="#cccccc")
        a.set_xlabel("Eb/N0 per payload bit [dB], known-symbol energy charged" if ebn0 else "SNR (Es/N0) [dB]")
        if a is np.atleast_1d(ax)[0]:
            a.set_ylabel("BLER" if kind == "bler" else "mean MACs per core [M] (32 cores)")
        if len(hh) > len(hs):
            hs, ls = hh, lab
    f.legend(hs, ls, loc="lower center", ncol=3, frameon=False, fontsize=11)
    f.tight_layout(rect=(0, 0.14, 1, 1))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"twin_fs_{kind}{'_ebn0' if ebn0 else ''}.png")
    f.savefig(p, dpi=200)
    plt.close(f)
    print("wrote", p)


if __name__ == "__main__":
    for kind in ("bler", "macs"):
        for eb in (False, True):
            plot(kind, eb)
