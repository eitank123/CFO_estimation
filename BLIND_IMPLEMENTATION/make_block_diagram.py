"""Black-and-white block diagram of the blind CFO receiver (BLIND_IMPLEMENTATION/block_diagram.{png,pdf,svg}).

    python BLIND_IMPLEMENTATION/make_block_diagram.py
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})

X, W = 5.05, 7.0                    # main column centre and box width
XR, WR = 11.5, 3.3                  # right column (output, re-encoding check)
XL = 1.2                            # left bypass line (early win)
XB = X + W / 2 + 0.45               # right loop line (retry)
XO = 13.5                           # far-right return line to the output box
FS = 9.5
LINE, TALL = 0.44, 0.34             # height of a text line, extra for a line with a fraction / sum
GAP = 0.5                           # vertical gap between blocks (arrow length)


def _height(title, body):
    lines = body.split("\n") if body else []
    tall = sum(any(t in l for t in ("dfrac", "sum", "frac", "sqrt")) for l in lines)
    return 0.62 + (0.42 if body else 0.0) + LINE * len(lines) + TALL * tall


def box(ax, y_top, title, body="", bold=False, x=X, w=W):
    """A box whose top is at y_top; returns its bottom."""
    h = _height(title, body)
    ax.add_patch(FancyBboxPatch((x - w / 2, y_top - h), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="white", ec="black", lw=1.7 if bold else 1.2))
    if body:
        ax.text(x, y_top - 0.25, title, ha="center", va="top", fontsize=FS + 0.5, fontweight="bold")
        ax.text(x, y_top - 0.25 - 0.47, body, ha="center", va="top", fontsize=FS, linespacing=1.55)
    else:
        ax.text(x, y_top - h / 2, title, ha="center", va="center", fontsize=FS + 0.5,
                fontweight="bold" if bold else "normal")
    return y_top - h


def diamond(ax, y_top, text, w=5.4, h=2.0):
    """A decision whose top vertex is at y_top; returns (centre y, bottom y)."""
    y = y_top - h / 2
    ax.add_patch(Polygon([(X, y_top), (X + w / 2, y), (X, y_top - h), (X - w / 2, y)], closed=True,
                         fc="white", ec="black", lw=1.3))
    ax.text(X, y, text, ha="center", va="center", fontsize=FS, linespacing=1.35)
    return y, y_top - h


def arrow(ax, pts, label="", lpos=None, ha="left"):
    """A polyline arrow through pts (the last segment carries the head)."""
    for (x0, y0), (x1, y1) in zip(pts[:-2], pts[1:-1]):
        ax.plot([x0, x1], [y0, y1], color="black", lw=1.2, solid_capstyle="butt")
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, mutation_scale=14, shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lpos
        ax.text(lx, ly, label, fontsize=FS, ha=ha, va="center", fontstyle="italic")


def down(ax, y0, label=""):
    """An arrow from y0 down by GAP on the main column; returns the new top."""
    arrow(ax, [(X, y0), (X, y0 - GAP)], label, (X + 0.15, y0 - GAP / 2))
    return y0 - GAP


def stage(ax, y0, y1, name):
    ax.add_patch(Rectangle((0.55, y1), X + W / 2 + 0.75 - 0.55, y0 - y1, fc="none", ec="black", lw=1.0, ls=(0, (5, 4))))
    ax.text(0.85, (y0 + y1) / 2, name, rotation=90, ha="center", va="center", fontsize=FS + 1.5, fontweight="bold")


fig, ax = plt.subplots(figsize=(13.5, 24))
ax.axis("off")

y = 40.0
ax.text(7.0, y, "Blind (zero-pilot) CFO receiver", ha="center", va="center", fontsize=18, fontweight="bold")
ax.text(7.0, y - 0.55, "1024-symbol QPSK packet, polar code N = 2048 with CRC-16, CFO |f| ≤ 0.03 cycles / symbol",
        ha="center", va="center", fontsize=FS + 1)
y -= 1.2
y = box(ax, y, "Received samples $r_x(m)$, 8 samples / symbol", bold=True)
y = down(ax, y)
y = box(ax, y, "Matched filter (RRC, β = 0.25) and downsampling  →  $r_n$,  n = 0 … 1023")
y = down(ax, y)

# ---------------- stage 1
s1 = y + 0.2
y -= 0.1
y = box(ax, y, "4th-power CFO estimate",
        "$y_n = -r_n^{\\,4}$   (removes QPSK: a pure tone at $4f$)\n"
        "$Y[k]$ = FFT of $y_n$ (4096 points),  peak in $|\\nu| \\leq 4 \\times 0.03$\n"
        "parabolic interpolation  →  $\\hat\\nu$,   $f_0 = \\hat\\nu / 4$")
y = down(ax, y)
y = box(ax, y, "Pre-MF correction", "$r_x(m)\\, e^{-j 2\\pi f_0 m / 8}$  →  matched filter again  →  $r'_n$")
y = down(ax, y)
y = box(ax, y, "Carrier phase and the π ambiguity",
        "$\\theta_0 = \\frac{1}{4}\\arg \\sum_n y'_n\\, e^{-j 2\\pi\\, 4 f_0 n}$    (known modulo π/2)\n"
        "π/2 branch: the smaller list-1 path metric of $\\theta_0$ and $\\theta_0 + \\pi/2$\n"
        "π branch: PiCode (the complement codeword is also accepted)")
y = down(ax, y)
y = box(ax, y, "CA-SCL-8 decode", "LLR$_n = \\sqrt{2}\\, y_n / \\sigma^2$   on   $r'_n\\, e^{-j(2\\pi f_0 n + \\theta_0)}$")
y = down(ax, y)
yd1, y = diamond(ax, y, "CRC-16 (PiCode) passes\nand  $\\rho > \\rho_{\\mathrm{th}}(\\mathrm{SNR})$ ?")
stage(ax, s1, y - 0.25, "STAGE 1:  FAST PATH")

# output box (right), level with the first decision
out_body = "deliver the data bits\nand the CFO (decision-\ndirected refinement\nover the 1024 symbols)"
oh = _height("Packet accepted", out_body)
box(ax, yd1 + oh / 2, "Packet accepted", out_body, bold=True, x=XR, w=WR)
arrow(ax, [(X + 2.7, yd1), (XR - WR / 2, yd1)], "yes", (X + 2.85, yd1 + 0.25))

# ---------------- stage 2
y -= 0.5
s2 = y
y -= 0.35
arrow(ax, [(X, y + 0.85), (X, y)], "no", (X + 0.15, y + 0.98))
y = box(ax, y, "Grid of hypotheses (cells)",
        "$f_c = -0.03 + c\\,k\\,\\mathrm{STEP}$,   STEP = $7.5 \\times 10^{-5}$   (k = 4 at R = 1/10 and 0.15)\n"
        "phases $\\theta_c + q\\,\\pi/4$   ($\\theta_c$ from the 4th-power FFT at $4 f_c$)")
ygrid = y
y = down(ax, y)
y = box(ax, y, "Partial decodes as a CFO detector",
        "list-1 Fast-SSC path metric $M_c$ up to a checkpoint (½ of the code)\n"
        "the frozen bits act as implicit pilots: $M_c$ is small only near the true (f, θ)\n"
        "R = 1/10, 0.15: coarse start + batches of 32 cells;   R = 2/5, 1/2: checkpoint NN")
y = down(ax, y)
y = box(ax, y, "Robust z-test",
        "$z_c = \\dfrac{\\mathrm{median}(M) - M_c}{1.4826\\ \\mathrm{MAD}(M)}$\n"
        "drop the cells with $z_c \\leq \\tau$ (keep the best 16); their neighbours join")
y = down(ax, y)
yd2, y = diamond(ax, y, "early win:\n$z_c > 6$ ?", w=4.0, h=1.6)
y = down(ax, y, "no")
y = box(ax, y, "Later checkpoints (¾, 1)",
        "repeat the path metric and the z-test\n"
        "candidates: $z > 4$ (at most 4), then the best 32 by path metric")
stage(ax, s2, y - 0.25, "STAGE 2:  SEARCH")

# ---------------- stage 3
y -= 0.5
s3 = y
y -= 0.35
arrow(ax, [(X, y + 0.85), (X, y)])
y_ref_top = y
y = box(ax, y, "Refinement of each candidate",
        "CFO offsets $\\pm k/2$ STEP,   phase offsets $\\{-\\pi/12,\\ 0,\\ +\\pi/12\\}$\n"
        "scored with the full path metric  →  the best T = 2 hypotheses")
y_ref = (y_ref_top + y) / 2
arrow(ax, [(X - 2.0, yd2), (XL, yd2), (XL, y_ref), (X - W / 2, y_ref)], "yes", (X - 2.6, yd2 + 0.25))
y = down(ax, y)
y = box(ax, y, "List decoding",
        "R = 1/10, 0.15: CA-SCL-8 per hypothesis\n"
        "R = 2/5, 1/2: one joint list of 16 paths over 4 cells × 2 hypotheses")
y = down(ax, y)
y = box(ax, y, "Code-aided retry (when the CRC fails)",
        "SC hard decisions $\\hat s_n$:   $z_n = r'_n\\, \\hat s_n^{*}$,   2 Newton steps on $|\\sum_n z_n e^{-j2\\pi f n}|^2$\n"
        "$\\theta = \\arg \\sum_n z_n e^{-j2\\pi f n}$,   then one more CA-SCL-8 decode")
y = down(ax, y)
yd3, y = diamond(ax, y, "CRC-16 (PiCode) passes\nand  $\\rho > \\rho_{\\mathrm{th}}(\\mathrm{SNR})$ ?")
arrow(ax, [(X + 2.7, yd3), (XO, yd3), (XO, yd1), (XR + WR / 2, yd1)], "yes", (X + 2.85, yd3 + 0.25))
y = down(ax, y, "no")
y_res_top = y
y = box(ax, y, "Next candidate, then rescue",
        "next 256 cells on both π/2 branches;   half-STEP grid × π/16 phases on the best 4")
y_res = (y_res_top + y) / 2
arrow(ax, [(X + W / 2, y_res), (XB, y_res), (XB, y_ref), (X + W / 2, y_ref)], "retry", (XB + 0.1, (y_res + y_ref) / 2))
stage(ax, s3, y - 0.25, "STAGE 3:  DECODE")
y -= 0.25
arrow(ax, [(X, y + 0.25), (X, y - 0.75)], "search exhausted", (X + 0.15, y - 0.3))
y = box(ax, y - 0.75, "Nothing accepted  →  block error", bold=True)

# ---------------- the acceptance check (right column)
ytxt = ygrid + 0.6
ax.add_patch(Rectangle((XR - WR / 2 - 0.1, ytxt - 7.35), WR + 0.2, 7.65, fc="white", ec="black", lw=0.8))
ax.text(XR - WR / 2 + 0.1, ytxt, "Re-encoding check", fontsize=FS + 0.5, fontweight="bold", va="top")
ax.text(XR - WR / 2 + 0.1, ytxt - 0.55,
        "$\\rho = \\dfrac{|\\sum_n r'_n\\, \\tilde s_n^{*}\\, e^{-j 2\\pi \\hat f n}|}{\\sqrt{N \\sum_n |r'_n|^2}}$\n"
        "$\\tilde s_n$: the re-encoded decision\n\n"
        "right packet:\n   $\\rho \\approx \\sqrt{\\mathrm{SNR} / (1 + \\mathrm{SNR})}$\n"
        "unrelated codeword:\n   $P(\\rho > t) \\approx e^{-N t^2}$\n\n"
        "$\\rho_{\\mathrm{th}} = \\max\\left(0.12,\\ c(\\mathrm{SNR})\\sqrt{s/(1+s)}\\right)$\n"
        "c: the per-rate table RHO_N",
        fontsize=FS, va="top", linespacing=1.5)

ax.set_xlim(0.3, 13.9)
ax.set_ylim(y - 0.3, 40.5)
for ext in ("png", "pdf", "svg"):
    fig.savefig(os.path.join(HERE, f"block_diagram.{ext}"), dpi=200, bbox_inches="tight", facecolor="white")
print("saved", os.path.join(HERE, "block_diagram.png"))
