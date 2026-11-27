"""
Best-so-far comparison, known timing, one 2x2 figure per format: BLER and mean MACs per core vs Es/N0 (pilots not charged)
and vs Eb/N0 per payload bit (competitor's known symbols charged). Lines: DVB-RCS2 competitor, blind today (a0),
18 moved bits (tb), 18 moved + CRC-24 + list 16 (twl-*-c24l16), the combined receiver (+ twin phase, twc-*-ph),
the z arrangements (tz0 / tz2 / tz4) and repetition twins (rpz-*-gr96ea / gr128ea; only arms with parts for the format).
(2026-11-24) id14s / id5 / id2: FMT_ARMS (baseline, no-twin CRC-24 control, twin arms); id5 / id2 competitor from the
da_da-f5-nda-* / da_da-f2-std parts (DA_COMP).

    py fullsys/plot_best_fs.py [fmt ...]   -> BLIND_IMPLEMENTATION/testing/results/best_<fmt>.png (default id13 id3)
"""
import glob
import json
import os
import re
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_twin_fs as T  # noqa: E402

ARMS = [("blind today", "fs-tw-full-{f}-a0-*", "#003366", "-o"),
        ("18 moved bits (twins)", "fs-tw-full-{f}-tb-*", "#17becf", "-v"),
        ("18 moved bits + CRC-24 + list 16", "twl-{f}-c24l16-*", "#9467bd", "-D"),
        ("18 moved + CRC-24 + list 16 + twin phase", "twc-{f}-ph-*", "#d62728", "-*"),
        ("... + 2 extra frozen bits (z2; ID 3: on top of z0)","tz2-{f}-*", "#2ca02c", "-P"),
        ("... + 4 extra frozen bits (z4)", "tz4-{f}-*", "#8c564b", ":X"),
        ("... with the z0 arrangement", "tz0-{f}-*", "#ff7f0e", "-p"),
        ("repeated twins 96 (rpz)", "rpz-{f}-gr96ea-*", "#e377c2", "-h"),
        ("repeated twins 128 (rpz)", "rpz-{f}-gr128ea-*", "#bcbd22", "--d"),
        ("48 pilots, equal overhead (pil)", "pil-{f}-48ea-*", "#000000", "-.s")]   # (2026-11-24) pilot arm
# (2026-11-24) twin family on the other formats: own line sets (baseline, no-twin CRC-24 control, twin arms); id13 / id3
# keep ARMS above unchanged
FMT_ARMS = {"id14s": [("blind best: CRC-24 + list 16 (no twin)", "fs-lc-id14s-c24l16-*", "#003366", "-o"),
                      ("repeated twins 96 (rpz, CRC-24, L16)", "rpz-id14s-gr96ea-*", "#e377c2", "-h")],
            "id5": [("blind today: CRC-32 + list 16 (no twin)", "fs-f5-l16-*", "#003366", "-o"),
                    ("control: CRC-24 + list 16, no twin", "c24-id5-*", "#7f7f7f", "--x"),
                    ("18 moved bits, z0 (twc, CRC-24, L16)", "twc-id5-z0-*", "#d62728", "-*"),
                    ("repeated twins 32 (rpz, CRC-24, L16)", "rpz-id5-gr32ea-*", "#e377c2", "-h")],
            "id2": [("blind today: CRC-16 + list 16 (no twin)", "fs-f2-l16-*", "#003366", "-o"),
                    ("control: CRC-24 + list 16, no twin", "c24-id2-*", "#7f7f7f", "--x"),
                    ("12 moved bits + twin phase (twc, CRC-24, L16)", "twc-id2-ph-*", "#d62728", "-*"),
                    ("repeated twins 32 + twin phase (rpz, CRC-24, L16)", "rpz-id2-gr32ea-*", "#e377c2", "-h"),
                    # (2026-11-24) final fresh-seed sweep of the adopted receiver: warm NN + joint-tuned c19
                    ("12 moved + CRC-24 + twin phase, retuned (final)", "fin-id2-twc-*", "#2ca02c", "-P")]}
# competitor parts for formats not in fullsys_fastvde_es.json (as BLIND_IMPLEMENTATION/testing/analyze_id2_id5_full.py)
DA_COMP = {"id5": ("da_da-f5-nda-*", "ID 5", "648 bits, QPSK 2/3", 26),
           "id2": ("da_da-f2-std", "ID 2", "96 bits, QPSK 1/3", 94)}

RATE = {"id13": "1/3", "id3": "1/3", "id14s": "1/2", "id5": "2/3", "id2": "1/3"}


def points(pat):
    P = {}
    for p in glob.glob(os.path.join(T.RES, "blind_fs_" + pat + ".json")):
        if not re.search(r"-[mp]\d+\.json$", p):
            continue
        for q in json.load(open(p))["points"]:
            r = P.setdefault(round(q["esn0"], 2), [0, 0, 0.0])
            r[0] += q["frame_err"]
            r[1] += q["frames"]
            r[2] += q["macs_per_core_std"] * q["frames"]
    return {e: v for e, v in sorted(P.items()) if e >= T.ES_MIN}


def comp_points(fmt):
    """(meta dict with name / desc / off_blind / off_comp, es, BLER, MACs per core) of the DVB-RCS2 competitor."""
    if fmt not in DA_COMP:
        return T.comp_points(fmt)
    pat, name, desc, known = DA_COMP[fmt]
    P, oc = {}, None
    for p in sorted(glob.glob(os.path.join(T.RES, pat + ".json"))):
        for q in json.load(open(p))["points"]:
            e = round(q["esn0"], 2)
            assert e not in P, f"duplicate comp point {e} in {p}"
            P[e] = (q["frame_err"] / q["frames"], q["crit_mean"])
            oc = q["ebn0_burst"] - q["esn0"]
    ob = json.load(open(glob.glob(os.path.join(T.RES, "blind_fs_" + FMT_ARMS[fmt][0][1] + ".json"))[0]))["meta"]["ebn0_offset"]
    es = np.array([e for e in sorted(P) if e >= T.ES_MIN])
    return (dict(name=name, desc=desc, known=known, off_blind=ob, off_comp=oc), es,
            np.array([P[e][0] for e in es]), np.array([P[e][1] for e in es]))


def main(fmt):
    d, ce, cp, cm = comp_points(fmt)
    f, ax = plt.subplots(2, 2, figsize=(14, 10))
    hs = ls = None
    for c, eb in enumerate((False, True)):
        ob, oc = (d["off_blind"], d["off_comp"]) if eb else (0.0, 0.0)
        for r, kind in enumerate(("bler", "macs")):
            a = ax[r, c]
            if kind == "bler":
                h, = a.semilogy(*T._nz(ce + oc, cp), "--s", color=T.ORANGE, lw=2, ms=7)
            else:
                h, = a.semilogy(ce + oc, cm / 1e6, "--s", color=T.ORANGE, lw=2, ms=7)
            hh, ll = [h], ["DVB-RCS2 competitor (known symbols, turbo, CRC early stop)"]
            for nm, pat, col, mk in FMT_ARMS.get(fmt, ARMS):
                P = points(pat.format(f=fmt))
                if not P:
                    continue
                e = np.array(list(P)) + ob
                v = np.array(list(P.values()))
                y = v[:, 0] / v[:, 1] if kind == "bler" else v[:, 2] / v[:, 1] / 1e6
                h, = (a.semilogy(*T._nz(e, y), mk, color=col, lw=2.5, ms=8) if kind == "bler"
                      else a.semilogy(e, y, mk, color=col, lw=2.5, ms=8))
                hh.append(h)
                ll.append(nm)
            hs, ls = hh, ll
            a.grid(True, which="both", ls=":", color="#cccccc")
            a.set_xlabel("Eb/N0 per payload bit [dB], known-symbol energy charged" if eb
                         else "SNR (Es/N0) [dB], known symbols not charged")
            a.set_ylabel("BLER" if kind == "bler" else "mean MACs per core [M] (32 cores)")
            a.set_title(("BLER" if kind == "bler" else "MACs per core") + (" vs Eb/N0" if eb else " vs SNR")
                        + f", R = {RATE.get(fmt, '?')}", fontweight="bold")
    f.suptitle(f"{d['name']} ({d['desc']}), known timing: best blind receivers vs competitor", fontsize=15,
               fontweight="bold")
    f.legend(hs, ls, loc="lower center", ncol=2, frameon=False, fontsize=11)
    f.tight_layout(rect=(0, 0.02 + 0.024 * int(np.ceil(len(ls) / 2)), 1, 0.96))   # room for every legend row
    p = os.path.join(T.OUT, f"best_{fmt}.png")
    f.savefig(p, dpi=160)
    plt.close(f)
    print("wrote", p)


if __name__ == "__main__":
    for fm in (sys.argv[1:] or ["id13", "id3"]):
        main(fm)
