"""Presentation BLER figures: blind vs ALL pilot competitors (est4: pilots outside the packet, pilot energy charged),
one figure per rate -> results/plots/pres_bler_R*.png.

Smoothing (statistics only, no model of the waterfall):
- blind: every run of the same-BLER testing receiver pooled per SNR (more packets per point).
- pilot receivers: errors split into detected (CRC / re-encoding failure) and undetected (wrong CRC pass). The undetected
  errors above the waterfall are an SNR-flat floor (CRC-16 false passes), so they are pooled over the floor region
  (SNRs where the receiver has <= 2 detected errors) and that pooled rate replaces the 0-6-count per-SNR values there.
  BLER drawn = detected / n + undetected rate (per SNR in the waterfall, pooled in the floor region).
usage: py plot_pres.py"""
import os, sys
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agg_cmp as C
import plot_e4 as P4

OUT = os.path.join(HERE, "results", "plots")
XLIM = {"1/10": (-5.1, -1.8), "0.15": (-4.7, -1.3), "2/5": (-0.1, 2.6), "1/2": (1.4, 3.6)}
LOW10 = []          # the 1/10 low-SNR extension was cancelled 2026-11-15: the user does not care below -5 dB
BL10 = []
STY = [("Genie", "genie: true CFO and phase (no pilots, lower bound)", "#7f7f7f", "x", ":"),
       ("RCS2-13", "DVB-RCS2 pilots (ID 13 layout, 116 known symbols), Rife-Boorstyn FFT", "#1f77b4", "s", "-"),
       ("pre128 ML", "128-symbol preamble, ML", "#2ca02c", "^", "-"),
       ("pre128 M&M", "128-symbol preamble, Mengali-Morelli", "#bcbd22", "v", "--"),
       ("split64 ML", "64 + 64 symbols (pre + post), joint ML", "#ff7f0e", "o", "-"),
       ("RCS2 pre/post", "DVB-RCS2 16 + 16 pre/post, 4th-power NDA", "#9467bd", "D", "--")]
BLIND = ("blind CFO (proposed, no pilots)", "#e377c2", "d")


def pilots(rate):
    """{src: {snr_plot: [n, det, und]}}"""
    out = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    parts = [P4.MAIN[rate], P4.PP[rate]] + (LOW10 if rate == "1/10" else [])
    for r in sum((P4.load(p) for p in parts), []):
        if r["rate"] != rate or r["pn"] != 0 or r["src"] not in dict((s[0], 1) for s in STY):
            continue
        d = out[r["src"]][round(r["snr_plot"], 3)]
        d[0] += r["frames"]
        d[1] += r["frame_err"] - r["undetected"]
        d[2] += r["undetected"]
    return out


def smooth(pts):
    """{snr: [n, det, und]} -> (x, bler, floor_from or None)"""
    xs = sorted(pts)
    fl = [s for s in xs if pts[s][1] <= 2 and s >= min(xs, key=lambda q: pts[q][1])]   # floor region: tail only
    fl = [s for s in fl if all(pts[q][1] <= 2 for q in xs if q >= s)]
    nf, uf = sum(pts[s][0] for s in fl), sum(pts[s][2] for s in fl)
    u_pool = uf / nf if nf else 0.0
    y = []
    for s in xs:
        n, d, u = pts[s]
        y.append(d / n + (u_pool if s in fl else u / n))
    return np.array(xs), np.array(y), (min(fl) if fl and u_pool > 0 else None), uf, nf


def blind(rate):
    """{snr: (err, n)} pooled over the same-BLER testing-receiver runs."""
    acc = defaultdict(lambda: [0, 0])

    def add(d):
        for s, v in d.items():
            acc[s][0] += v["err"]
            acc[s][1] += v["n"]
    if rate in ("1/10", "0.15"):
        add(C.testing_fix(rate))
        add(C.adopted(rate))
        if rate == "0.15":                                 # -4.5 dB only in the presentation runs (same BLER)
            k, n = C.merged(rate, C.EP.BLIND_RX[rate])[-4.5]
            acc[-4.5] = [k, n]
        if rate == "1/10":
            for p in BL10:
                try:
                    for (r_, s, x), rows in C.A.load(p).items():
                        if r_ == rate and x == "T testing_s11g":
                            acc[s][0] += sum(r["frame_err"] for r in rows)
                            acc[s][1] += sum(r["frames"] for r in rows)
                except Exception:
                    pass
    else:
        for s, (k, n) in C.merged(rate, C.EP.BLIND_RX[rate]).items():
            acc[s] = [k, n]
    return {s: tuple(v) for s, v in acc.items() if v[1] >= 1000}


def fig(rate):
    f, ax = plt.subplots(figsize=(10, 7.6))
    lo, hi = XLIM[rate]
    B = blind(rate)
    have = [s for s in B if B[s][0] > 0] + [s for d in pilots(rate).values() for s in d]
    lo = max(lo, min(have) - 0.2)                       # until the low-SNR extension is in
    xb = np.array([s for s in sorted(B) if B[s][0] > 0 and lo <= s <= hi])
    ax.plot(xb, [B[s][0] / B[s][1] for s in xb], color=BLIND[1], marker=BLIND[2], lw=3, ms=10, label=BLIND[0], zorder=5)
    notes = []
    for src, lab, c, m, ls in STY:
        pts = pilots(rate).get(src)
        if not pts:
            continue
        x, y, f0, uf, nf = smooth(pts)
        keep = (x >= lo) & (x <= hi) & (y > 0)
        if not keep.any():
            continue
        if f0 is not None:
            lab += f"\n   (floor = wrong CRC passes, pooled from {f0:+.1f} dB: {uf} in {nf / 1e6:.1f}M packets)"
        ax.plot(x[keep], y[keep], color=c, marker=m, ls=ls, lw=1.4 if src == "Genie" else 2.0, ms=6, label=lab)
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(top=1.2)
    ax.set_xlabel("SNR (Es/N0) [dB]", fontsize=13)
    ax.set_ylabel("BLER", fontsize=13)
    ax.set_title(f"BLER vs SNR, R = {rate}", fontsize=15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=1, frameon=False)
    f.tight_layout()
    p = os.path.join(OUT, f"pres_bler_R{P4.tag(rate)}.png")
    f.savefig(p, dpi=160)
    plt.close(f)
    print(p)


PRES = os.path.join(HERE, "..", "presentation")        # the slide figures (presentation/README.md)


def tag2(rate):
    return rate.replace("/", "_")


if __name__ == "__main__":
    import shutil
    for rate in ("1/10", "0.15", "2/5", "1/2"):
        fig(rate)
        P4.fig(rate, "core")
        shutil.copy(os.path.join(OUT, f"pres_bler_R{P4.tag(rate)}.png"), os.path.join(PRES, f"bler_fair_R{tag2(rate)}.png"))
        shutil.copy(os.path.join(OUT, f"e4_macs_R{P4.tag(rate)}.png"), os.path.join(PRES, f"macs_fair_R{tag2(rate)}.png"))
    print("copied to", os.path.abspath(PRES))
