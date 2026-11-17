"""Full curves, not crossings: BLER vs SNR and MACs per core vs SNR of blind (adopted testing receiver) and every
compared receiver (est4 + est5 + ARS + faithful variants), on the fair axis (pilot energy charged). Existing results only.

    py BLIND_IMPLEMENTATION/testing/plot_curves.py

Outputs:
  results/curves.md                            every point: errors / packets, BLER, MACs per core, per rate and receiver
  results/plots/curves_bler_R*.png             BLER vs SNR, one panel per system family (blind in every panel)
  results/plots/curves_macs_R*.png             MACs per core vs SNR, same panels
Rules: x axis = SNR (Es/N0) [dB] on the fair axis, nothing below -5 dB, 0-error points are not drawn (they are in the
table as '< 3/n'), no genie, 1/10 and 0.15 in separate figures, legends below the panels.
"""
import os
from collections import OrderedDict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

import plot_e4 as P

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(HERE, "results", "curves.md")
RATES = ("1/10", "0.15", "2/5", "1/2")

# System families (one panel each). Labels follow scoreboard.md.
FAMILIES = OrderedDict([
    ("DVB-RCS2 and Griebel 2021", OrderedDict([
        ("RCS2-13", "DVB-RCS2 ID 13 (116 known)"), ("RCS2-13 lobes", "DVB-RCS2 ID 13 + lobes"),
        ("G4096", "Griebel 2021 FFT 4096"), ("G2048", "Griebel 2021 FFT 2048"),
        ("Griebel faithful", "Griebel 2021 as published"), ("RCS2 pre/post", "DVB-RCS2 16 + 16, 4th power")])),
    ("Preambles (generic and Wi-Fi)", OrderedDict([
        ("pre128 ML", "128 preamble, ML"), ("pre128 M&M", "128 preamble, M&M"),
        ("split64 ML", "64 + 64, joint ML (+-3 lobes)"), ("split64 ML L4", "64 + 64, joint ML (+-4 lobes)"),
        ("WiFi pre128", "Wi-Fi-like 128 preamble"), ("WiFi real320", "Wi-Fi 802.11 real 320"),
        ("WiFi real320 lobes", "Wi-Fi 802.11 real 320 + lobes")])),
    ("Satellite and space standards", OrderedDict([
        ("VDE-SAT", "VDE-SAT (66 known)"), ("DVB-S2 style", "DVB-S2-inspired (126)"),
        ("DVB-S2 header90", "DVB-S2 PL header (90, scan)"), ("DVB-S2 SOF26", "DVB-S2 SOF (26, scan)"),
        ("CCSDS style", "CCSDS-inspired (8 x 16)"), ("CCSDS 131.2 real", "CCSDS 131.2 real (32)"),
        ("CCSDS 131.0 ASM", "CCSDS 131.0 ASM (64)")])),
    ("Terrestrial and military", OrderedDict([
        ("DMRS 1/7", "5G-NR-like DMRS 1/7"), ("Sparse pilots 1/32", "Sparse pilots 1/32"),
        ("MIL-110 HF", "MIL-STD-188-110 HF"), ("MIL-110 full", "MIL-STD-188-110 full (411)")])),
    ("Burst modems (ViaSat, Advantech patents)", OrderedDict([
        ("ViaSat UW", "ViaSat 16-symbol UW"), ("ViaSat 7653150", "ViaSat US 7653150"),
        ("ViaSat top32 X4phase", "ViaSat top-32 + 4th-power phase"), ("hyb3", "Advantech hybrid DA + NDA"),
        ("hyb3-pre48", "Advantech 48 preamble"), ("hyb3-pre48 wide", "Advantech 48, wide window")])),
])
# Fixed categorical order (validated reference palette, light mode); the slot follows the position in the family.
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARKS = ["o", "s", "^", "D", "v", "P", "X", "*"]
BLIND_STYLE = dict(color="#1a1a19", lw=2.8, marker="o", ms=7, label="blind (0 known symbols), adopted testing receiver")


def data(rate):
    """(blind {snr: dict}, competitors {src: {snr_fair: dict}}) with snr >= -5 dB."""
    E = P.e4(rate, e5=True, ars=True, var=True)
    B = {s: v for s, v in P.blind(rate).items() if s >= -5.0}
    return B, {k: {s: v for s, v in pts.items() if s >= -5.0} for k, pts in E.items() if k != "Genie"}


def draw(ax, pts, key, **kw):
    xs = [s for s in sorted(pts) if pts[s]["n"] > 0 and (pts[s]["err"] > 0 if key == "bler" else pts[s].get("core"))]
    if not xs:
        return False
    ys = [pts[s]["err"] / pts[s]["n"] if key == "bler" else pts[s]["core"] / 1e6 for s in xs]
    ax.plot(xs, ys, **kw)
    return True


def figure(rate, key, B, E):
    fams = list(FAMILIES.items())
    f, axs = plt.subplots(2, 3, figsize=(19, 12.5))
    axs = axs.ravel()
    allx = [s for s in B] + [s for d in E.values() for s in d]
    lo, hi = max(min(allx) - 0.2, -5.0), max(allx) + 0.2
    for ax, (fam, members) in zip(axs, fams):
        draw(ax, B, key, **BLIND_STYLE)
        for i, (src, lab) in enumerate(members.items()):
            if src in E:
                draw(ax, E[src], key, color=SLOTS[i], marker=MARKS[i], lw=1.8, ms=7, label=lab,
                     ls="-" if i < 4 else "--", markeredgecolor="white", markeredgewidth=0.8)
        ax.set_yscale("log")
        ax.set_xlim(lo, hi)
        ax.set_title(fam, fontsize=12)
        ax.set_xlabel("SNR (Es/N0) [dB]  (pilot energy charged)", fontsize=10.5)
        ax.set_ylabel("BLER" if key == "bler" else "MACs per core per packet [M]", fontsize=10.5)
        ax.grid(True, which="both", ls=":", color="#c3c2b7", alpha=0.7)
        if key == "core":
            fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}" if v >= 0.1 else f"{v:.3f}")
            ax.yaxis.set_major_formatter(fmt)
            ax.yaxis.set_minor_formatter(fmt)
            ax.tick_params(axis="y", which="minor", labelsize=7.5)
        ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False)
    axs[-1].axis("off")
    axs[-1].text(0.02, 0.95, "\n".join([
        f"R = {rate}. Fair axis: SNR = data Es/N0 + 10 log10((1024 + Nk) / 1024).",
        "Same code (polar N = 2048, CRC-16), CA-SCL-8, re-encoding",
        "check and metric-ordered CRC search for every receiver.",
        "0-error points are not drawn (see results/curves.md).",
        "Blind (black) is the same curve in every panel.",
        "MACs per core = scheduled 32-core count."]), va="top", fontsize=10.5, color="#3d3d3a", transform=axs[-1].transAxes)
    what = "BLER" if key == "bler" else "MACs per core"
    f.suptitle(f"{what} vs SNR, R = {rate}  (blind vs every compared receiver, by system family)", fontsize=15)
    f.tight_layout(rect=(0, 0, 1, 0.97))
    p = os.path.join(P.OUT, f"curves_{'bler' if key == 'bler' else 'macs'}_R{P.tag(rate)}.png")
    f.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(f)
    print(p)


def cell(v):
    n, e = v["n"], v["err"]
    b = f"{e / n:.1e}" if e else f"< {3 / n:.0e}"
    return f"{b} ({e}/{n // 1000}k)"


def tables(rate, B, E):
    L = [f"## R = {rate}", ""]
    rows = [("Blind (0 known symbols, adopted testing receiver)", B)]
    for fam, members in FAMILIES.items():
        rows += [(f"{lab} [{fam}]", E[src]) for src, lab in members.items() if src in E]
    L += ["### BLER vs SNR (fair axis)", "",
          "Each cell: SNR [dB]: BLER (errors / packets). 0 errors: 95 % upper bound '< 3/n'.", ""]
    L += ["| Receiver | points |", "|---|---|"]
    for lab, pts in rows:
        L.append(f"| {lab} | " + "; ".join(f"{s:.2f}: {cell(pts[s])}" for s in sorted(pts)) + " |")
    L += ["", "### MACs per core vs SNR (fair axis, M MACs per core per packet, scheduled count)", "",
          "| Receiver | points |", "|---|---|"]
    for lab, pts in rows:
        L.append(f"| {lab} | " + "; ".join(f"{s:.2f}: {pts[s]['core'] / 1e6:.3f}" for s in sorted(pts)
                                           if pts[s].get("core")) + " |")
    return L + [""]


if __name__ == "__main__":
    md = ["# Blind vs every compared receiver: full BLER and MACs curves (generated by plot_curves.py)", "",
          "Every simulated point, from existing results only: blind = adopted testing receiver (`plot_e4.blind`), the others",
          "= est4 / est5 / ARS / faithful-variant parts (`plot_e4.e4(rate, e5, ars, var)`, same receiver at the same SNR in",
          "several parts is pooled). SNR = the fair axis (burst energy per data symbol, pilot energy charged), nothing below",
          "-5 dB, genie left out. Figures: `results/plots/curves_bler_R*.png`, `curves_macs_R*.png`. Crossings at target BLERs:",
          "`scoreboard.md`. Receiver layouts: `competitors.md`, `expected_variants.md`.", ""]
    for r in RATES:
        B, E = data(r)
        figure(r, "bler", B, E)
        figure(r, "core", B, E)
        md += tables(r, B, E)
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print(OUT_MD)
