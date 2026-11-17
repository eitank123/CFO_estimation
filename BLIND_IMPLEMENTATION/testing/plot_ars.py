"""Focused figures for the Griebel / ARS 2021 study (ars-10/15/25/2, 2026-11-15): blind vs DVB-RCS2 ID 13 and the
paper's FFT-interpolation variants, on the est4 fair axis (pilot energy charged). Existing results only.
Outputs (testing/results/plots/): arsf_bler_R*.png, arsf_macs_R*.png and ars_gap_summary.png."""
import os
import numpy as np
import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plot_e4 as P

KEEP = ["RCS2-13", "G4096", "G2048", "G2048N", "Griebel faithful", "RCS2-13 lobes"]
TARGETS = [("1/10", 1e-4), ("0.15", 1e-3), ("0.15", 1e-4), ("2/5", 1e-3), ("1/2", 1e-3)]


def bler_fig(rate):
    E, B = P.e4(rate, ars=True), P.blind(rate)
    sty = P.styles(ars=True)
    allx = [s for k in KEEP if k in E for s in E[k]]
    lo, hi = max(min(allx) - 0.25, -5.0), max(allx) + 0.25          # never below -5 dB
    B = {s: v for s, v in B.items() if lo <= s <= hi}
    f, ax = plt.subplots(figsize=(10, 7.4))
    P.curve(ax, B, "bler", P.BLIND[0], P.BLIND[1], P.BLIND[2], lw=2.8, ms=9)
    for k in KEEP:
        if k in E:
            lab, c, m, ls = sty[k]
            P.curve(ax, {s: v for s, v in E[k].items() if s >= -5.0}, "bler", lab, c, m, ls=ls,
                    lw=1.4 if k == "Genie" else 1.9)
    ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]  (burst energy per data symbol: pilot energy charged)", fontsize=12)
    ax.set_ylabel("BLER", fontsize=12)
    ax.set_title(f"BLER vs SNR, R = {rate}  (blind vs DVB-RCS2 and Griebel 2021 variants)", fontsize=13)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    p = os.path.join(P.OUT, f"arsf_bler_R{P.tag(rate)}.png")
    f.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(f)
    print(p)


def macs_fig(rate):
    """MACs per core per packet (scheduled count) vs SNR: blind vs RCS2-13 and the variants (Genie left out)."""
    E, B = P.e4(rate, ars=True), P.blind(rate)
    sty = P.styles(ars=True)
    allx = [s for k in KEEP if k in E for s in E[k]]
    lo, hi = max(min(allx) - 0.25, -5.0), max(allx) + 0.25
    B = {s: v for s, v in B.items() if lo <= s <= hi and v.get("core")}
    f, ax = plt.subplots(figsize=(10, 7.4))
    P.curve(ax, B, "core", P.BLIND[0], P.BLIND[1], P.BLIND[2], lw=2.8, ms=9)
    for k in KEEP:
        if k in E:
            lab, c, m, ls = sty[k]
            P.curve(ax, {s: v for s, v in E[k].items() if s >= -5.0}, "core", lab, c, m, ls=ls, lw=1.9)
    ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]  (burst energy per data symbol: pilot energy charged)", fontsize=12)
    ax.set_ylabel("MACs per core per packet [M]  (scheduled count, log scale)", fontsize=12)
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}" if v >= 0.1 else f"{v:.3f}")
    ax.yaxis.set_major_formatter(fmt)
    ax.yaxis.set_minor_formatter(fmt)
    ax.tick_params(axis="y", which="minor", labelsize=8)
    ax.set_title(f"MACs per core vs SNR, R = {rate}  (blind vs DVB-RCS2 and Griebel 2021 variants)", fontsize=13)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    p = os.path.join(P.OUT, f"arsf_macs_R{P.tag(rate)}.png")
    f.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(f)
    print(p)


def gap_fig():
    """Required SNR minus blind's, per variant and target (+ = blind needs less SNR)."""
    rows = {}
    for rate, t in TARGETS:
        E, b = P.e4(rate, ars=True), P.gap_db(P.blind(rate), t)
        for k in KEEP:
            g = P.gap_db(E[k], t) if k in E else None
            rows.setdefault(k, []).append(None if (g is None or b is None) else g - b)
    labels = [f"R = {r}\nBLER {t:.0e}" for r, t in TARGETS]
    sty = P.styles(ars=True)
    f, ax = plt.subplots(figsize=(11, 6.4))
    n, w = len(rows), 0.8 / len(rows)
    x = np.arange(len(TARGETS))
    for i, (k, v) in enumerate(rows.items()):
        vals = [np.nan if g is None else g for g in v]
        ax.bar(x + (i - (n - 1) / 2) * w, vals, w * 0.92, color=sty[k][1], label=sty[k][0], edgecolor="white")
        for xi, g in zip(x + (i - (n - 1) / 2) * w, v):
            if g is not None:
                ax.text(xi, g + (0.04 if g >= 0 else -0.04), f"{g:+.2f}", ha="center", rotation=90,
                        va="bottom" if g >= 0 else "top", fontsize=7.5)
    ax.margins(y=0.12)
    ax.axhline(0, color="#e377c2", lw=2.4, label="blind (0 = same required SNR as blind)")
    ax.set_xticks(x, labels)
    ax.set_ylabel("required SNR minus blind's [dB]  (+ = blind better)", fontsize=11)
    ax.set_title("Gap to blind vs target, DVB-RCS2 ID 13 and Griebel 2021 variants (pilot energy charged)", fontsize=12)
    ax.grid(True, axis="y", ls=":", alpha=0.6)
    ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    p = os.path.join(P.OUT, "ars_gap_summary.png")
    f.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(f)
    print(p)


if __name__ == "__main__":
    for r in ("1/10", "0.15", "2/5", "1/2"):
        bler_fig(r)
        macs_fig(r)
    gap_fig()
