"""
Eb/N0-only slide figures (user 2026-11-25: drop the Es/N0 plots). Eb/N0 = energy per PAYLOAD bit:
    Eb/N0 [dB] = Es/N0 [dB] + 10 log10(transmitted symbols / payload bits)
(all transmitted symbols counted, known symbols included; equal-energy symbols). Blind sends only data symbols, so its
shift is smaller than DVB-RCS2's (offsets from fullsys/plot_best_fs.comp_points).

Writes figs/h2_<fmt>_eb.png (BLER and MACs per core vs Eb/N0, blind vs DVB-RCS2) for id13 / id3 / id2 and
figs/cap_eb.png (2 x 3: BLER / MACs vs Eb/N0 with per-packet caps 2 / 1 / 0.5 M). Existing results only.

    py BLIND_IMPLEMENTATION/presentation/latex/plot_eb_slides.py
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
import plot_h2_slides as H2  # noqa: E402
import plot_id2_slides as I2  # noqa: E402
import plot_cap_slide as CP  # noqa: E402

OUT = os.path.join(HERE, "figs")
GREEN = "#2ca02c"
NAME = {"id13": "ID 13", "id3": "ID 3", "id2": "ID 2"}
XL_ES = {"id13": (-1.1, -0.3), "id3": (-0.6, 0.2), "id2": (0.1, 1.4)}


def blind_curve(fmt):
    """(snr, bler, mean crit) of the presented receiver."""
    if fmt == "id2":
        P = {s: I2.load(t) for s, t in I2.PTS.items()}
        P = {s: v for s, v in P.items() if v is not None}
        s = np.array(sorted(P))
        return (s, np.array([P[x]["frame_err"] / P[x]["frames"] for x in s]),
                np.array([P[x]["crit_par_d4a_per_frame"] for x in s]))
    nm, col, mk, s, b, c = H2.curves(fmt)[0]
    return s, b, c


def xlim(fmt, ob, oc):
    lo, hi = XL_ES[fmt]
    return (lo + min(ob, oc), hi + max(ob, oc))


def main():
    plt.rcParams.update({"xtick.labelsize": 14, "ytick.labelsize": 14})
    for fmt in ("id13", "id3", "id2"):
        d, ce, cp, cm = B.comp_points(fmt)
        ob, oc = d["off_blind"], d["off_comp"]
        s, b, c = blind_curve(fmt)
        fig, axs = plt.subplots(1, 2, figsize=(14, 4.9))
        xx, yy = T._nz(ce, cp)
        axs[0].semilogy(np.asarray(xx) + oc, yy, "--s", color=T.ORANGE, lw=2.5, ms=6, label="DVB-RCS2 (known symbols)")
        axs[1].semilogy(np.asarray(ce) + oc, np.asarray(cm) / 1e6, "--s", color=T.ORANGE, lw=2.5, ms=6)
        axs[0].semilogy(s + ob, b, "-D", color=GREEN, lw=2.5, ms=9, label="blind receiver (no known symbols)")
        axs[1].semilogy(s + ob, c / 1e6, "-D", color=GREEN, lw=2.5, ms=9)
        for i, ax in enumerate(axs):
            ax.set_xlim(xlim(fmt, ob, oc))
            ax.grid(True, which="both", ls=":", color="#cccccc")
            ax.set_xlabel("$E_b/N_0$ per data bit [dB]", fontsize=16)
            ax.set_ylabel("BLER" if i == 0 else "MACs per core [M]", fontsize=16)
            ax.set_title("BLER vs $E_b/N_0$" if i == 0 else "Complexity", fontsize=17, fontweight="bold")
        h, l_ = axs[0].get_legend_handles_labels()
        fig.legend(h, l_, loc="lower center", ncol=2, frameon=False, fontsize=15)
        fig.tight_layout(rect=(0, 0.1, 1, 1))
        fig.savefig(os.path.join(OUT, f"h2_{fmt}_eb.png"), dpi=150)
        plt.close(fig)
        print(fmt, "offsets blind", round(ob, 3), "dvb", round(oc, 3))

    # caps
    dcap = json.load(open(CP.SRC))
    plt.rcParams.update({"xtick.labelsize": 12, "ytick.labelsize": 12})
    fig, axs = plt.subplots(2, 3, figsize=(16, 7.4))
    for col, fmt in enumerate(("id13", "id3", "id2")):
        d, ce, cp, cm = B.comp_points(fmt)
        ob, oc = d["off_blind"], d["off_comp"]
        xx, yy = T._nz(ce, cp)
        axs[0, col].semilogy(np.asarray(xx) + oc, yy, "--s", color=T.ORANGE, lw=2.2, ms=6, label="DVB-RCS2")
        axs[1, col].semilogy(np.asarray(ce) + oc, np.asarray(cm) / 1e6, "--s", color=T.ORANGE, lw=2.2, ms=6, label="DVB-RCS2")
        S = CP.series(fmt, dcap)
        for key, C, lab, colr, mk in CP.CAPS:
            sn, bl, mean = S[key]
            axs[0, col].semilogy(sn + ob, bl, mk, color=colr, lw=2.2, ms=7, label=lab)
            axs[1, col].semilogy(sn + ob, mean / 1e6, mk, color=colr, lw=2.2, ms=7, label=lab)
        axs[0, col].set_title(f"{NAME[fmt]}: BLER", fontsize=16, fontweight="bold")
        axs[1, col].set_title(f"{NAME[fmt]}: Complexity", fontsize=16, fontweight="bold")
        for row in (0, 1):
            ax = axs[row, col]
            ax.set_xlim(xlim(fmt, ob, oc))
            ax.grid(True, which="both", ls=":", color="#cccccc")
            ax.set_xlabel("$E_b/N_0$ per data bit [dB]", fontsize=13)
        axs[0, col].set_ylabel("BLER", fontsize=14)
        axs[1, col].set_ylabel("MACs per core [M]", fontsize=14)
    h, l_ = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l_, loc="lower center", ncol=len(h), frameon=False, fontsize=14)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(OUT, "cap_eb.png"), dpi=150)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
