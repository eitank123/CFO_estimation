"""Competitor algorithm slides -> slides_eq/rcs_alg.png, vde_alg.png

    python slides_eq/plot_competitor_algos.py

Layouts from est4/common.py (data/layouts_est4.json: known-symbol burst positions of rcs13 and vde27). (Earlier versions also drew the noiseless known-symbol pattern |sum_k exp(-j 2 pi nu n_k)| / Nk (true CFO 0): where the estimator's spectrum
X(nu) peaks, including its alias lobes. Deterministic from the layout, no simulation.
"""
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, "data", "layouts_est4.json")))
NAVY, ORANGE, GREY, RED = "#003366", "#E07B39", "#999999", "#c8423b"
plt.rcParams.update({"font.size": 13, "font.family": "DejaVu Sans"})
NU = np.linspace(-0.08, 0.08, 4001)


def pattern(idx):
    idx = np.asarray(idx, float)
    return np.abs(np.exp(-2j * np.pi * NU[:, None] * idx[None]).sum(1)) / len(idx)


def strip(ax, lay, title):
    K, k = lay["K"], np.asarray(lay["known_idx"])
    ax.add_patch(plt.Rectangle((0, 0), K, 1, color="#e6ecf3"))
    for n in k:
        ax.add_patch(plt.Rectangle((n, 0), 1.6, 1, color=ORANGE))
    ax.set_xlim(0, K)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("symbol index in the burst")
    ax.set_title(title, fontsize=13)


def spectrum(ax, curves, win=None):
    if win:
        ax.axvspan(-win, win, color="#d8e4f0", label="step 2 search window: f_c ± 1/54")
    for y, lab, col, lw in curves:
        ax.plot(NU, y, color=col, lw=lw, label=lab)
    ax.set_xlim(NU[0], NU[-1])
    ax.set_ylim(0, 1.5)
    ax.set_xlabel("ν − f  [cycles/symbol]")
    ax.set_ylabel("|X(ν)| (noiseless, normalised)")
    ax.grid(True, ls=":", alpha=0.5)
    ax.legend(fontsize=11, loc="upper right")


def fig(name, lay, title, curves=None, win=None, marks=()):
    f = plt.figure(figsize=(9.5, 2.3))
    a = f.add_axes([0.04, 0.30, 0.93, 0.48])
    strip(a, lay, title)
    f.savefig(os.path.join(HERE, name), dpi=200, facecolor="white")


r, v = L["rcs13"], L["vde27"]
fig("rcs_alg.png", r, "known symbols (orange): 32 + 53 single pilots every 20 + 31 = 116",
    [(pattern(r["known_idx"]), "all 116 known symbols", NAVY, 2.2)], marks=((-0.05, "alias\n−1/20"), (0.05, "alias\n+1/20")))
fig("vde_alg.png", v, "known symbols (orange): 27-symbol syncword + 39 single pilots every 27 = 66",
    [(pattern(v["known_idx"][:27]), "step 1: syncword only (27): wide, no aliases", ORANGE, 2.2),
     (pattern(v["known_idx"]), "step 2: all 66 known", NAVY, 2.2)], win=1 / 54,
    marks=((-1 / 27, "alias\n−1/27"), (1 / 27, "alias\n+1/27")))
