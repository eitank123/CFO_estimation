"""
Slide figure: the deck's blind receiver with a per-packet MACs cap of 2 / 1 / 0.5 M (a packet that would exceed C MACs
per core is stopped and counted as an error; stopped packets charged C), against no cap and DVB-RCS2.
ID 13 / ID 3: offline cap tables BLIND_IMPLEMENTATION/testing/results/cap_e2l.json; ID 2: computed the same way from
the e2 parts' core_hist (plot_id2_slides.capped). No simulation.
Writes figs/cap_e2l.png (2 x 3: BLER (top) and mean MACs (bottom) vs Es/N0 for ID 13, ID 3, ID 2).

    py BLIND_IMPLEMENTATION/presentation/latex/plot_cap_slide.py
"""
import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plot_best_fs as B  # noqa: E402
import plot_twin_fs as T  # noqa: E402
import plot_id2_slides as I2  # noqa: E402

SRC = os.path.join(HERE, "data", "cap_e2l.json")
OUT = os.path.join(HERE, "figs", "cap_e2l.png")
XL = {"id13": (-1.1, -0.3), "id3": (-0.6, 0.2), "id2": I2.XL}
CAPS = [("nocap", None, "blind, no cap", "#2ca02c", "-D"),
        ("2000000.0", 2e6, "blind, cap 2 M", "#d95f02", "-v"),
        ("1000000.0", 1e6, "blind, cap 1 M", "#d62728", "-<"),
        ("500000.0", 5e5, "blind, cap 0.5 M", "#7570b3", "->")]


def series(fmt, d):
    """{cap key: (snr, bler, mean)}."""
    out = {}
    if fmt == "id2":
        P = {s: I2.load(t) for s, t in I2.PTS.items()}
        P = {s: v for s, v in P.items() if v is not None}
        snr = np.array(sorted(P))
        for key, C, *_ in CAPS:
            em = [I2.capped(P[s], C) for s in snr]
            fr = np.array([P[s]["frames"] for s in snr], float)
            out[key] = (snr, np.array([e for e, _ in em]) / fr, np.array([m for _, m in em]))
    else:
        for key, *_ in CAPS:
            a = np.array(d[fmt][key], float)
            out[key] = (a[:, 0], a[:, 2] / a[:, 1], a[:, 4])
    return out


def main():
    d = json.load(open(SRC))
    plt.rcParams.update({"xtick.labelsize": 12, "ytick.labelsize": 12})
    fig, axs = plt.subplots(2, 3, figsize=(16, 7.4))
    for col, fmt in enumerate(("id13", "id3", "id2")):
        dd, ce, cp, cm = B.comp_points(fmt)
        xx, yy = T._nz(ce, cp)
        axs[0, col].semilogy(xx, yy, "--s", color=T.ORANGE, lw=2.2, ms=6, label="DVB-RCS2")
        axs[1, col].semilogy(ce, np.asarray(cm) / 1e6, "--s", color=T.ORANGE, lw=2.2, ms=6, label="DVB-RCS2")
        S = series(fmt, d)
        for key, C, lab, colr, mk in CAPS:
            snr, bl, mean = S[key]
            axs[0, col].semilogy(snr, bl, mk, color=colr, lw=2.2, ms=7, label=lab)
            axs[1, col].semilogy(snr, mean / 1e6, mk, color=colr, lw=2.2, ms=7, label=lab)
        name = {"id13": "ID 13", "id3": "ID 3", "id2": "ID 2"}[fmt]
        axs[0, col].set_title(f"{name}: BLER", fontsize=16, fontweight="bold")
        axs[1, col].set_title(f"{name}: mean MACs per core", fontsize=16, fontweight="bold")
        for row in (0, 1):
            ax = axs[row, col]
            ax.set_xlim(XL[fmt])
            ax.grid(True, which="both", ls=":", color="#cccccc")
            ax.set_xlabel("$E_s/N_0$ [dB]", fontsize=14)
        axs[0, col].set_ylabel("BLER", fontsize=14)
        axs[1, col].set_ylabel("MACs per core [M]", fontsize=14)
    h, l_ = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l_, loc="lower center", ncol=len(h), frameon=False, fontsize=14)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT, dpi=150)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
