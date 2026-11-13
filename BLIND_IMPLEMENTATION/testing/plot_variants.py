"""Plots of the R experiments (srch*) and experiment K (nph15*) -> BLIND_IMPLEMENTATION/testing/results/plots/.
Run from anywhere: py BLIND_IMPLEMENTATION/testing/plot_variants.py   (0-error points are not drawn; the legend
gives errors / packets per SNR)."""
import os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); import agg_variants as agg
OUT = os.path.join(HERE, "results", "plots")
os.makedirs(OUT, exist_ok=True)
STY = {"base": ("#d62728", "o", "-", 3.0), "dd": ("#1f77b4", "s", "--", 2), "win4": ("#2ca02c", "^", "--", 2),
       "dd_win4": ("#9467bd", "D", "--", 2), "dd_k": ("#7f7f7f", "v", ":", 2), "nph4": ("#1f77b4", "s", "--", 2)}
def key(rx):
    if rx.startswith("S "): return "base"
    v = rx[2:]
    for s in ("_25", "_2"):
        if v.endswith(s): v = v[: -len(s)]
    return "dd_k" if v.startswith("dd_k") else v
LAB = {"base": "baseline", "dd": "R1 dd (code-aided refinement)", "win4": "R3 win4 (early win z > 4)",
       "dd_win4": "R1 + R3 dd_win4", "dd_k": "R2 dd + coarser grid", "nph4": "K nph4 (4 phases at every SNR)"}
def fig_for(rate, t, tag, base_t=None):
    rows = {}
    for (r, s, rx), c in t.items():
        if r == rate: rows.setdefault(key(rx), {})[s] = c
    common = set.intersection(*(set(v) for v in rows.values()))   # paired points only (every variant ran them)
    rows = {k: {s: c for s, c in v.items() if s in common} for k, v in rows.items()}
    lim = (min(common) - 0.1, max(common) + 0.1)                   # x range = all simulated SNRs, even 0-error ones
    if base_t is not None:                     # MACs of the baseline from other parts (b15c has no crit_par_macs)
        bm = {s: c for (r, s, rx), c in base_t.items() if r == rate and rx.startswith("S ")}
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for k in [k for k in STY if k in rows]:
        x = np.array(sorted(rows[k])); n = np.array([rows[k][s]["frames"] for s in x]); e = np.array([rows[k][s]["frame_err"] for s in x])
        y = e / n
        c, m, ls, lw = STY[k]
        lab = LAB[k] + "  (" + ", ".join(f"{int(a)}/{int(b)//1000}k" for a, b in zip(e, n)) + ")"
        ax.semilogy(x, np.where(e > 0, y, np.nan), color=c, marker=m, ls=ls, lw=lw, ms=8, label=lab)
    ax.set(xlabel="SNR (Es/N0) [dB]", ylabel="BLER", title=f"BLER vs SNR, R = {rate}")
    ax.set_xlim(lim); ax.title.set_fontsize(14); ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False)
    fig.tight_layout(); p = f"{OUT}/{tag}_bler_R{rate.replace('/', '_')}.png"; fig.savefig(p, dpi=150); plt.close(fig); print(p)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.5))
    for k in [k for k in STY if k in rows]:
        src = bm if (k == "base" and base_t is not None) else rows[k]
        x = np.array(sorted(s for s in src if s in rows[k]))
        mf = np.array([src[s]["mac_frames"] for s in x])
        c, m, ls, lw = STY[k]
        a1.plot(x, [src[s]["macs"] / f / 1e6 for s, f in zip(x, mf)], color=c, marker=m, ls=ls, lw=lw, ms=8, label=LAB[k])
        a2.plot(x, [src[s]["crit_par_macs"] / f / 1e6 for s, f in zip(x, mf)], color=c, marker=m, ls=ls, lw=lw, ms=8)
    a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per packet [M]", title=f"Total MACs per packet vs SNR, R = {rate}")
    a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="MACs per core [M]", title=f"MACs per core (32 cores) vs SNR, R = {rate}")
    for a in (a1, a2):
        a.set_xlim(lim); a.title.set_fontsize(13); a.grid(True, which="both", ls=":", alpha=0.6); a.set_yscale("log")
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, fontsize=10, loc="lower center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1)); p = f"{OUT}/{tag}_macs_R{rate.replace('/', '_')}.png"; fig.savefig(p, dpi=150); plt.close(fig); print(p)
t = agg.agg(["srch10", "srch15", "srch25", "srch2"])
for rate in ("1/10", "0.15", "2/5", "1/2"):
    fig_for(rate, t, "srch")
fig_for("0.15", agg.agg(["b15c", "nph15a", "nph15b"]), "k_nph4", base_t=agg.agg(["bm15b"]))
