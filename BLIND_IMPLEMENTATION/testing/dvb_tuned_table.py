"""Markdown tables for the jointly tuned DVB-RCS2 results (2026-11-18), from fullsys/results/fs_tuned_summary.json
(written by plot_fs_tuned.py) and the DVB-RCS2 DA parts. Prints:
  1. per ID: Eb/N0 at BLER 1e-3 (known symbols charged) for DVB-RCS2, blind before tuning, blind jointly tuned, the gap
     (+ = blind better) and the mean MACs per core near the crossing;
  2. per ID and Es/N0: errors / frames and mean MACs before -> after, change in %.
Crossings: log-linear interpolation between the two bracketing points (blank if not bracketed)."""
import json, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, "fullsys", "results")
OFF = {"id13": (2.298, 1.904, ["da_fs-q13da.json"]), "id42b": (5.311, 4.915, ["da_fs-q42td.json"]),
       "id3": (2.95, 2.24, ["da_fs-q3td.json", "da_fs-q3deep.json"]), "id14s": (0.41, 0.09, ["da_fs-q14td.json"])}
NAME = {"id13": "ID 13", "id42b": "ID 42", "id3": "ID 3", "id14s": "ID 14"}


def cross(es, p, target=1e-3):
    pts = [(e, q) for e, q in zip(es, p) if q and q > 0]
    for (e0, p0), (e1, p1) in zip(pts, pts[1:]):
        if p0 >= target >= p1:
            t = (np.log10(p0) - np.log10(target)) / (np.log10(p0) - np.log10(p1))
            return e0 + t * (e1 - e0)
    return None


def macs_at(es, m, e):
    if e is None or not len(es):
        return None
    return float(np.interp(e, es, m))


S = json.load(open(os.path.join(R, "fs_tuned_summary.json")))
print("| Waveform | DVB-RCS2 [dB] | Blind before [dB] | Blind tuned [dB] | Gap tuned (+ = blind better) | MACs/core before | MACs/core tuned | DVB-RCS2 MACs/core |")
print("|---|---|---|---|---|---|---|---|")
for fmt, (OT, OP, das) in OFF.items():
    D = []
    for fn in das:
        if os.path.exists(os.path.join(R, fn)):
            D += [(q["esn0"], q["frame_err"] / q["frames"], q["crit_mean"] / 1e6) for q in json.load(open(os.path.join(R, fn)))["points"]]
    D.sort()
    cd = cross([d[0] for d in D], [d[1] for d in D])
    md = macs_at([d[0] for d in D], [d[2] for d in D], cd)
    row = [NAME[fmt], f"{cd + OT:.2f}" if cd is not None else "-"]
    cs = {}
    for k in ("before", "tuned"):
        b = S[fmt][k]
        p = [er / n for er, n in zip(b["err"], b["n"])]
        cs[k] = cross(b["es"], p)
        row.append(f"{cs[k] + OP:.2f}" if cs[k] is not None else "-")
    row.append(f"**{(cd + OT) - (cs['tuned'] + OP):+.2f}**" if cd is not None and cs["tuned"] is not None else "-")
    for k in ("before", "tuned"):
        b = S[fmt][k]; v = macs_at(b["es"], b["mean"], cs[k])
        row.append(f"{v:.3f} M" if v is not None else "-")
    row.append(f"{md:.3f} M" if md is not None else "-")
    print("| " + " | ".join(row) + " |")
print()
for fmt in OFF:
    b0, b1 = S[fmt]["before"], S[fmt]["tuned"]
    print(f"**{NAME[fmt]}**\n\n| Es/N0 [dB] | errors before | errors tuned | MACs/core before [M] | MACs/core tuned [M] | change |")
    print("|---|---|---|---|---|---|")
    m0 = {e: (er, n, m) for e, er, n, m in zip(b0["es"], b0["err"], b0["n"], b0["mean"])}
    for e, er, n, m in zip(b1["es"], b1["err"], b1["n"], b1["mean"]):
        o = m0.get(e)
        print(f"| {e:+.1f} | {f'{o[0]}/{o[1]}' if o else '-'} | {er}/{n} | {f'{o[2]:.3f}' if o else '-'} | {m:.3f} | "
              f"{f'{(m / o[2] - 1) * 100:+.0f} %' if o else '-'} |")
    print()
