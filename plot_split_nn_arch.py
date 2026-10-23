"""Block diagram of the split-pilot NN (models/cfo_split_nn_L1024.pth, `convlobe-long`, README A.15.1).
    py plot_split_nn_arch.py   -> plots/split_nn_architecture.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BOX = dict(fc="white", ec="0.15", lw=1.4)
STAGE = {"coarse": "#e8f4fa", "lobe": "#fdf1e3", "cls": "#eef7ec", "fine": "#f3eefa"}


def box(ax, x, y, w, h, text, fc="white", fs=11):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.012",
                                fc=fc, ec="0.15", lw=1.4))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, linespacing=1.35)
    return x, y, w, h


def arrow(ax, p, q, label=None, dashed=False, lx=0.0, ly=0.012):
    ax.annotate("", q, p, arrowprops=dict(arrowstyle="-|>", lw=1.4, color="0.15", mutation_scale=14,
                                          ls="--" if dashed else "-", shrinkA=0, shrinkB=0))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, ha="center", va="bottom", fontsize=11)


def main():
    fig = plt.figure(figsize=(17, 10))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")

    # stage bands
    ax.add_patch(FancyBboxPatch((0.01, 0.74), 0.98, 0.215, boxstyle="round,pad=0,rounding_size=0.01",
                                fc=STAGE["coarse"], ec="none"))
    ax.add_patch(FancyBboxPatch((0.01, 0.53), 0.98, 0.18, boxstyle="round,pad=0,rounding_size=0.01",
                                fc=STAGE["lobe"], ec="none"))
    ax.add_patch(FancyBboxPatch((0.01, 0.27), 0.98, 0.23, boxstyle="round,pad=0,rounding_size=0.01",
                                fc=STAGE["cls"], ec="none"))
    ax.add_patch(FancyBboxPatch((0.50, 0.02), 0.49, 0.235, boxstyle="round,pad=0,rounding_size=0.01",
                                fc=STAGE["fine"], ec="none"))
    for x, y, t in ((0.018, 0.945, "COARSE"), (0.018, 0.70, "LOBE (analytic)"), (0.018, 0.49, "LOBE CLASSIFIER"),
                    (0.508, 0.245, "FINE")):
        ax.text(x, y, t, fontsize=10, fontweight="bold", color="0.35", va="top")

    # ---- coarse row
    y1 = 0.82
    z = box(ax, 0.075, y1, 0.10, 0.075, "$z[n]=r[n]\\,s^*[n]$\n2 blocks × 64")
    fb = box(ax, 0.235, y1, 0.17, 0.10, "Filter bank, per block\nLinear 128 → 256\n(DFT-initialised, learned;\n"
             "128 filters over ±0.21)", fs=10.5)
    en = box(ax, 0.415, y1, 0.15, 0.10, "$E_k=\\sum_{blocks}|y_k|^2$\n(non-coherent sum)\n"
             "$\\log E_k-\\log\\,\\overline{E}$", fs=10.5)
    cv = box(ax, 0.585, y1, 0.15, 0.10, "Conv1d × 3 along $k$\n2 → 8 → 8 → 2 ch,\nkernel 7 (GELU)", fs=10.5)
    sa = box(ax, 0.79, y1, 0.20, 0.10, "Soft-argmax\n$f_c=\\sum_k \\mathrm{softmax}(\\ell)_k$\n"
             "$\\cdot\\,(f_k+\\Delta f\\,\\tanh o_k)$", fs=10.5)
    snr1 = box(ax, 0.585, 0.915, 0.07, 0.04, "SNR", fs=10.5)
    for a, b in ((z, fb), (fb, en), (en, cv), (cv, sa)):
        arrow(ax, (a[0] + a[2] / 2, y1), (b[0] - b[2] / 2, y1))
    arrow(ax, (0.585, 0.895), (0.585, y1 + 0.05), )
    ax.text(0.63, 0.915, "(2nd input channel)", fontsize=9, color="0.35", va="center")
    ax.text(0.6775, y1 + 0.008, "$\\ell_k,o_k$", fontsize=10, ha="center", va="bottom")

    # ---- lobe row (right to left)
    y2 = 0.615
    dr = box(ax, 0.83, y2, 0.20, 0.085, "De-rotate both blocks by $f_c$\n"
             "$b_1=\\sum_{blk\\,1},\\;b_2=\\sum_{blk\\,2}$", fs=10.5)
    ph = box(ax, 0.60, y2, 0.15, 0.085, "$\\phi=\\dfrac{\\angle(b_2\\,b_1^*)}{2\\pi}$", fs=12)
    fl = box(ax, 0.41, y2, 0.15, 0.085, "$f_{lobe}=f_c+\\phi/D$\n($D=N/2=512$)", fs=11)
    ca = box(ax, 0.19, y2, 0.20, 0.085, "7 candidates\n$f_j=f_{lobe}+j/D,\\;j=-3\\ldots3$", fs=10.5)
    arrow(ax, (0.89, y1 - 0.05), (0.89, y2 + 0.0425), "$f_c$", lx=0.018, ly=-0.01)
    for a, b in ((dr, ph), (ph, fl), (fl, ca)):
        arrow(ax, (a[0] - a[2] / 2, y2), (b[0] + b[2] / 2, y2))

    # ---- lobe classifier row
    y3 = 0.38
    ft = box(ax, 0.19, y3, 0.24, 0.15, "from $z$, per candidate (7 each):\n"
             "$\\log|B_1+B_2|^2$  − best\n$\\log(|B_1|^2+|B_2|^2)$  − best\n"
             "$(f_j-f_c)\\,D$, clamped ±6\n+ SNR  → 22 inputs", fs=10.5)
    ml = box(ax, 0.445, y3, 0.15, 0.085, "MLP\n22 → 64 → 64 → 7", fs=11)
    js = box(ax, 0.63, y3, 0.12, 0.085, "$j^*=\\arg\\max-3$\n$\\in\\{-3\\ldots3\\}$", fs=10.5)
    fh = box(ax, 0.81, y3, 0.18, 0.085, "$\\hat f=f_{lobe}+\\dfrac{j^*}{D}+\\dfrac{\\Delta}{D}$", fs=12)
    snr2 = box(ax, 0.445, 0.30, 0.07, 0.04, "SNR", fs=10.5)
    arrow(ax, (0.19, y2 - 0.0425), (0.19, y3 + 0.075))
    arrow(ax, (ft[0] + ft[2] / 2, y3), (ml[0] - ml[2] / 2, y3))
    arrow(ax, (ml[0] + ml[2] / 2, y3), (js[0] - js[2] / 2, y3), "logits", ly=0.008)
    arrow(ax, (js[0] + js[2] / 2, y3), (fh[0] - fh[2] / 2, y3))
    arrow(ax, (0.445, 0.32), (0.445, y3 - 0.0425))
    arrow(ax, (fh[0] + fh[2] / 2, y3), (0.995, y3))
    ax.text(0.95, y3 + 0.012, "CFO\nestimate", fontsize=10.5, fontweight="bold", ha="center", va="bottom")
    # z feeds the candidate likelihoods B1, B2 (dashed, along the left edge)
    ax.annotate("", (0.07, y3), (0.035, y1 - 0.0375), arrowprops=dict(arrowstyle="-|>", lw=1.2, color="0.35",
                ls="--", connectionstyle="angle,angleA=-90,angleB=180,rad=0", mutation_scale=12))
    ax.annotate("", (ft[0] - ft[2] / 2, y3), (0.035, y1 - 0.0375), arrowprops=dict(arrowstyle="-|>", lw=1.2,
                color="0.35", ls="--", connectionstyle="angle,angleA=-90,angleB=180,rad=0", mutation_scale=12))

    # ---- fine stage
    y4 = 0.12
    fi = box(ax, 0.62, y4, 0.16, 0.17, "SNR\n$f_cD-\\mathrm{round}(f_cD)$\n$\\cos 2\\pi\\phi$\n$\\sin 2\\pi\\phi$\n"
             "$\\log(1+|b_2 b_1^*|/64)$", fs=10.5)
    mf = box(ax, 0.81, y4, 0.15, 0.085, "MLP\n5 → 32 → 1\n(last layer zero-init)", fs=10.5)
    arrow(ax, (fi[0] + fi[2] / 2, y4), (mf[0] - mf[2] / 2, y4))
    arrow(ax, (0.81, y4 + 0.0425), (0.81, y3 - 0.0425), "Δ", lx=0.012, ly=-0.012)
    # f_c, phi, b1, b2 of the analytic stage feed the fine features (dashed)
    ax.annotate("", (0.555, y4 + 0.085), (0.555, y2 - 0.0425), arrowprops=dict(arrowstyle="-|>", lw=1.2,
                color="0.35", ls="--", mutation_scale=12))
    ax.text(0.562, 0.235, "$f_c,\\ \\phi,\\ b_1,b_2$", fontsize=10, color="0.35", ha="left")

    ax.text(0.5, 0.985, "Split-pilot NN CFO estimator (1024-symbol packet, quarter layout)", ha="center",
            va="top", fontsize=15, fontweight="bold")
    ax.text(0.25, 0.04, "39,770 parameters · 163,004 real MACs per estimate\n"
            "$f_c$ is detached (no gradient) in the lobe and fine stages", ha="center", fontsize=10.5, color="0.3")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots", "split_nn_architecture.png")
    fig.savefig(out, dpi=200)
    print("saved", out)


if __name__ == "__main__":
    main()
