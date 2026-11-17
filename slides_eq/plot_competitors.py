"""Blind (adopted testing receiver) vs the most relevant deployed pilot / preamble systems -> slides_eq/competitors.png

    python slides_eq/plot_competitors.py

Numbers copied verbatim from slides_eq/data/scoreboard_2026-11-17.md (BLIND_IMPLEMENTATION/testing/results/scoreboard.md):
required SNR on the fair axis (pilots outside the packet, their energy charged) and MACs per core at the crossing.
Only measured crossings are plotted; 'fails' / 'not bracketed' entries are listed in the panel, never placed.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY = "#003366"
# name, known symbols Nk, energy charged [dB], colour, marker
COMP = (("DVB-RCS2 ID 13", 116, 0.47, "#E07B39", "o"),
        ("128-symbol preamble, ML", 128, 0.51, "#777777", "s"),
        ("DVB-S2-inspired", 126, 0.50, "#2ca02c", "^"),
        ("CCSDS 131.0 ASM", 64, 0.26, "#9467bd", "D"),
        ("VDE-SAT", 66, 0.27, "#8c564b", "v"),
        ("5G-NR-like DMRS 1/7", 171, 0.67, "#17becf", "P"),
        ("Advantech 48, wide DA", 48, 0.20, "#c8423b", "X"),
        ("Wi-Fi 802.11 320 + lobes", 320, 1.18, "#bcbd22", "h"))
# per target: blind (SNR, M MACs per core), then per competitor (SNR, M) or a string (not placed)
T = {
    "R = 1/10, BLER 10⁻⁴": ((-4.78, 0.194), {
        "DVB-RCS2 ID 13": (-4.09, 0.034), "128-symbol preamble, ML": (-4.68, 0.090),
        "DVB-S2-inspired": (-2.32, 0.041), "CCSDS 131.0 ASM": (-3.89, 0.167), "VDE-SAT": "fails",
        "5G-NR-like DMRS 1/7": (-4.58, 0.034), "Advantech 48, wide DA": "fails",
        "Wi-Fi 802.11 320 + lobes": (-2.46, 0.343)}),
    "R = 0.15, BLER 10⁻³": ((-3.60, 0.262), {
        "DVB-RCS2 ID 13": (-3.45, 0.035), "128-symbol preamble, ML": (-3.44, 0.078),
        "DVB-S2-inspired": (-3.12, 0.048), "CCSDS 131.0 ASM": (-3.44, 0.172), "VDE-SAT": (-2.92, 0.035),
        "5G-NR-like DMRS 1/7": (-3.27, 0.035), "Advantech 48, wide DA": (-3.63, 0.363),
        "Wi-Fi 802.11 320 + lobes": (-2.72, 0.442)}),
    "R = 0.15, BLER 10⁻⁴": ((-2.93, 0.180), {
        "DVB-RCS2 ID 13": (-3.12, 0.035), "128-symbol preamble, ML": (-3.12, 0.076),
        "DVB-S2-inspired": (-2.28, 0.042), "CCSDS 131.0 ASM": (-2.98, 0.167), "VDE-SAT": (-1.77, 0.035),
        "5G-NR-like DMRS 1/7": (-2.92, 0.035), "Advantech 48, wide DA": "fails",
        "Wi-Fi 802.11 320 + lobes": (-2.26, 0.359)}),
    "R = 2/5, BLER 10⁻³": ((0.58, 0.183), {
        "DVB-RCS2 ID 13": (1.10, 0.040), "128-symbol preamble, ML": (1.16, 0.085),
        "DVB-S2-inspired": (1.12, 0.042), "CCSDS 131.0 ASM": (0.95, 0.142), "VDE-SAT": (0.92, 0.041),
        "5G-NR-like DMRS 1/7": (1.28, 0.040), "Advantech 48, wide DA": (0.91, 0.101),
        "Wi-Fi 802.11 320 + lobes": (1.84, 0.238)}),
    "R = 1/2, BLER 10⁻³": ((1.73, 0.139), {
        "DVB-RCS2 ID 13": (2.33, 0.043), "128-symbol preamble, ML": (2.41, 0.068),
        "DVB-S2-inspired": (2.39, 0.044), "CCSDS 131.0 ASM": (2.19, 0.144), "VDE-SAT": (2.16, 0.043),
        "5G-NR-like DMRS 1/7": (2.53, 0.043), "Advantech 48, wide DA": (2.11, 0.070),
        "Wi-Fi 802.11 320 + lobes": (3.11, 0.218)}),
}

plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
fig, axs = plt.subplots(2, 3, figsize=(15, 8.4))
for ax, (title, (blind, comp)) in zip(axs.flat, T.items()):
    ax.axvline(blind[0], color=NAVY, lw=1, ls=":")
    ax.axhline(blind[1], color=NAVY, lw=1, ls=":")
    ax.plot(*blind, marker="*", ms=22, color=NAVY, ls="none", zorder=5)
    fails = []
    for name, nk, db, col, mk in COMP:
        v = comp[name]
        if isinstance(v, str):
            fails.append(name)
            continue
        ax.plot(*v, marker=mk, ms=11, color=col, ls="none", mec="k", mew=0.6)
    ax.set_yscale("log")
    ax.set_ylim(0.02, 0.8)
    ax.set_yticks([0.03, 0.05, 0.1, 0.2, 0.4])
    ax.set_yticklabels(["0.03", "0.05", "0.1", "0.2", "0.4"])
    ax.minorticks_off()
    xs = [blind[0]] + [v[0] for v in comp.values() if not isinstance(v, str)]
    ax.set_xlim(min(xs) - 0.25, max(xs) + 0.25)
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("required SNR [dB], pilot energy charged")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    if fails:
        ax.text(0.97, 0.97, "fails the target:\n" + "\n".join(fails), transform=ax.transAxes, ha="right",
                va="top", fontsize=10.5, color="#444444")
for ax in axs[:, 0]:
    ax.set_ylabel("MACs per core [M]")
lg = axs[1, 2]
lg.axis("off")
h = [plt.Line2D([], [], marker="*", ms=18, color=NAVY, ls="none")] + \
    [plt.Line2D([], [], marker=mk, ms=10, color=c, ls="none", mec="k", mew=0.6) for _, _, _, c, mk in COMP]
lab = ["blind, 0 known symbols"] + [f"{n} ({nk}, +{db:.2f} dB)" for n, nk, db, _, _ in COMP]
lg.legend(h, lab, loc="center", fontsize=12, frameon=False, title="receiver (known symbols, energy)",
          title_fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "competitors.png"), dpi=200, facecolor="white")
