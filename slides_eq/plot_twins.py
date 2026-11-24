"""Slides on the blind receiver's two "twin" techniques (zero-energy semi-pilots): 18 moved bits vs repeated twin bits.
Rendered as full 16:9 slide images in the deck style (navy title + rule, Calibri-like body):
  twin_common.png  twin_moved.png  twin_repeat.png  twin_diff.png  twin_data.png

    python slides_eq/plot_twins.py

All numbers come from the local CFO_esitimation session's message of 2026-11-24: known timing, BLER 1e-3, base NN, before
the joint retune (final numbers pending). Negative dB = blind needs less SNR.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle

matplotlib.rcParams["mathtext.fontset"] = "cm"
HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, ORANGE, GREEN, RED, TXT, GREY = "#003366", "#E07B39", "#2e8b3d", "#c8423b", "#1f2937", "#5b6573"
LIGHT = "#e8eef5"
TITLE_F, BODY_F = "Liberation Sans", "Carlito"
PRE = "Pre-retune numbers: known timing, BLER 1e-3, base NN, thresholds not yet retuned; final numbers pending."


def slide(title, n):
    f = plt.figure(figsize=(13.333, 7.5))
    a = f.add_axes((0, 0, 1, 1))
    a.set_xlim(0, 13.333)
    a.set_ylim(7.5, 0)
    a.axis("off")
    a.text(0.73, 0.88, title, fontsize=28, fontweight="bold", color=NAVY, family=TITLE_F, va="center")
    a.add_patch(Rectangle((0.83, 1.215), 11.67, 0.03, color=NAVY, lw=0))
    a.text(12.6, 7.17, n, fontsize=10, color=GREY, family=BODY_F, ha="right")
    return f, a


def bullets(a, x, y, items, size=16, dy=0.42, width=None):
    for it in items:
        sub = it.startswith("-")
        t = it.lstrip("- ")
        a.text(x + (0.35 if sub else 0), y, "–" if sub else "•", fontsize=size, color=TXT, family=BODY_F, va="top")
        a.text(x + (0.6 if sub else 0.25), y, t, fontsize=size - (1 if sub else 0), color=TXT, family=BODY_F, va="top")
        y += dy
    return y


def eq(a, x, y, s, size=17, color=TXT, ha="left"):
    a.text(x, y, s, fontsize=size, color=color, va="center", ha=ha)


def box(a, x, y, w, h, fc=LIGHT, ec=NAVY, lw=1.4):
    a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=lw))


def arrow(a, p, q, col=NAVY, lw=1.8):
    a.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=col, lw=lw))


def save(f, name):
    f.savefig(os.path.join(HERE, name), dpi=150, facecolor="white")
    plt.close(f)


# 1) common idea ---------------------------------------------------------------------------------------------------
f, a = slide("Twin symbols: a zero-energy semi-pilot", "1/5")
bullets(a, 0.83, 1.55, ["Twin = QPSK symbol whose two coded bits are always equal ($b_I = b_Q$)",
                        "It is then a diagonal symbol: its square is known (up to the known scrambler sign)",
                        "Receiver squares the twins: CFO line at 2f, coherent over all twins",
                        "2nd power instead of the 4th power blind QPSK needs: much smaller squaring loss",
                        "No pilot symbol sent, no energy spent: the twins only constrain the code",
                        "Also gives the carrier phase (twin phase)"], size=17, dy=0.46)
eq(a, 0.95, 4.65, r"$s=\frac{b_I+j\,b_Q}{\sqrt{2}},\quad b_I=b_Q\ \Rightarrow\ s\in\{\pm\frac{1+j}{\sqrt{2}}\}\ \Rightarrow\ s^2=j\ \ (\pm j\ \mathrm{scrambled})$")
eq(a, 0.95, 5.35, r"$r_n=s_n\,e^{\,j(2\pi f n+\theta)}+w_n$")
eq(a, 0.95, 6.05, r"$\omega_n\,r_n^2=e^{\,j(4\pi f n+2\theta)}+\mathrm{noise}\quad(\omega_n:\ \mathrm{known\ scrambler\ term})$")
eq(a, 0.95, 6.7, r"$\mathrm{FFT\ over\ the\ twins}\ \Rightarrow\ \mathrm{line\ at}\ 2f\qquad(\mathrm{blind\ QPSK}:\ r_n^4,\ \mathrm{line\ at}\ 4f)$")
# constellation
cx, cy, R = 10.9, 4.1, 1.35
a.plot([cx - 1.9, cx + 1.9], [cy, cy], color=GREY, lw=1)
a.plot([cx, cx], [cy - 1.9, cy + 1.9], color=GREY, lw=1)
a.text(cx + 1.95, cy + 0.05, "I", fontsize=15, color=GREY, family=BODY_F, va="center")
a.text(cx + 0.08, cy - 1.95, "Q", fontsize=15, color=GREY, family=BODY_F)
d = R / 2 ** 0.5
for sx, sy in ((1, -1), (-1, 1)):            # y axis is flipped: (1,-1) is the +I +Q corner
    a.plot([cx, cx + sx * d * 1.25], [cy, cy + sy * d * 1.25], color=NAVY, ls=":", lw=1.4)
for sx, sy, twin in ((1, -1, True), (-1, 1, True), (1, 1, False), (-1, -1, False)):
    a.add_patch(Circle((cx + sx * d, cy + sy * d), 0.17, fc=NAVY if twin else "white", ec=NAVY, lw=2))
a.text(cx + d + 0.25, cy - d - 0.2, r"$b_I = b_Q$", fontsize=16, color=NAVY, family=BODY_F)
a.text(cx - d - 1.25, cy + d + 0.35, r"$b_I = b_Q$", fontsize=16, color=NAVY, family=BODY_F)
a.text(cx, cy + 2.3, "filled: twin (diagonal) symbols, b_I = b_Q\nhollow: b_I ≠ b_Q (before scrambling)", fontsize=13, color=GREY,
       family=BODY_F, ha="center", va="top")
save(f, "twin_common.png")

# 2) moved bits -----------------------------------------------------------------------------------------------------
f, a = slide("Twins from the code: 18 moved bits", "2/5")
eq(a, 0.95, 1.65, r"$x=u\,G_N,\ \ G_N=F^{\otimes n}\ \Rightarrow\ x_j=\bigoplus_{i\,\supseteq\,j}u_i$", 18)
eq(a, 0.95, 2.4, r"$k<N/2:\quad x_k\oplus x_{k+N/2}=\bigoplus_{i<N/2,\ i\,\supseteq\,k}u_i$", 18)
bullets(a, 0.83, 2.95, [r"Pair $(x_k,\ x_{k+N/2})$ is equal in every codeword iff no first-half info bit covers k",
                        r"Each first-half info bit $i$ breaks $2^{\mathrm{wt}(i)}$ twins",
                        "Move m of them (highest weight first, greedy / swap search) to the most",
                        "- reliable frozen second-half positions: those twins are freed",
                        "Same payload, same frame, same E, zero extra bits",
                        "Cost: info bits on less reliable bit-channels (small coding loss)"], size=16, dy=0.43)
eq(a, 0.95, 5.75, r"$\mathrm{UB}=\sum_{u\,\in\,\mathrm{info}} Q\!\left(\sqrt{m_u/2}\right)$  (GA union bound)", 17)
bullets(a, 0.83, 6.2, ["Twins set by the code: ID 13 (N 4096, 1476 sym) 73; ID 3 (N 1024, 456 sym) 100;",
                       "- shortened ID 14 only ~6 (does not work); ID 2 can move only 12 bits"], size=15, dy=0.4)
# mapping diagram
X0, Y0 = 8.2, 1.65
a.text(X0 + 2.3, Y0, "polar codeword x (length N):  first half | second half", fontsize=14, color=GREY, family=BODY_F, ha="center")
for i in range(8):
    c = NAVY if i in (2,) else ("#7f9fbf" if i in (6,) else LIGHT)
    a.add_patch(Rectangle((X0 + i * 0.58, Y0 + 0.25), 0.55, 0.5, fc=LIGHT, ec=NAVY, lw=1))
a.add_patch(Rectangle((X0 + 2 * 0.58, Y0 + 0.25), 0.55, 0.5, fc=NAVY, ec=NAVY))
a.add_patch(Rectangle((X0 + 6 * 0.58, Y0 + 0.25), 0.55, 0.5, fc=NAVY, ec=NAVY))
a.plot([X0 + 4 * 0.58 - 0.015] * 2, [Y0 + 0.15, Y0 + 0.85], color=RED, lw=2)
a.text(X0 + 2 * 0.58 + 0.27, Y0 + 1.05, r"$x_k$", fontsize=17, color=NAVY, family=BODY_F, ha="center")
a.text(X0 + 6 * 0.58 + 0.27, Y0 + 1.05, r"$x_{k+N/2}$", fontsize=17, color=NAVY, family=BODY_F, ha="center")
sx, sy = X0 + 2.3, Y0 + 3.35
box(a, sx - 1.0, sy - 0.55, 2.0, 1.1)
a.text(sx - 0.5, sy - 0.15, "I", fontsize=16, color=NAVY, family=BODY_F, ha="center", fontweight="bold")
a.text(sx + 0.5, sy - 0.15, "Q", fontsize=16, color=NAVY, family=BODY_F, ha="center", fontweight="bold")
a.text(sx, sy + 0.3, "one QPSK symbol", fontsize=12, color=GREY, family=BODY_F, ha="center")
arrow(a, (X0 + 2 * 0.58 + 0.27, Y0 + 1.25), (sx - 0.5, sy - 0.6))
arrow(a, (X0 + 6 * 0.58 + 0.27, Y0 + 1.25), (sx + 0.5, sy - 0.6))
a.text(sx, sy + 0.95, r"$x_k = x_{k+N/2}$ in every codeword" + "\n=> diagonal (twin) symbol", fontsize=14, color=NAVY,
       family=BODY_F, ha="center", va="top")
save(f, "twin_moved.png")

# 3) repeated bits --------------------------------------------------------------------------------------------------
f, a = slide("Twins by repetition: repeated twin bits (t = 96)", "3/5")
bullets(a, 0.83, 1.55, ["Encode the rate-matched (E − t, K) polar code: same K, optimal info set kept",
                        "Send t of its coded bits twice; the copy rides on the Q bit of the symbol",
                        "- whose I bit carries the original: t diagonal symbols by construction",
                        "Rx: add the two LLRs (MRC), the copy's energy is not wasted",
                        "Which bits: greedy on the union bound (largest −dUB/dm per round)",
                        "Placement: arcsine (ends-weighted) stratified jitter over the burst:",
                        "- better CFO estimate, no grating lobes",
                        "Cost: t fewer parity bits (rate up), partly paid back by the MRC",
                        "Twin count free (= t), placement free, works on shortened codes",
                        "ID 13 and ID 3: t = 96 (96 twins); ID 5 and ID 2: t = 32"], size=16, dy=0.42)
eq(a, 0.95, 6.05, r"$e=[\,e_1,\ e_1[\mathrm{rep}]\,],\quad |\mathrm{rep}|=t$", 18)
eq(a, 0.95, 6.7, r"$\ell_1[\mathrm{rep}]\ {+}{=}\ \ell_{\mathrm{copy}}\quad\Rightarrow\quad \mathrm{GA\ mean}\ 2\mu\ \mathrm{on\ the\ repeated\ bits}$", 18)
# chain diagram
X, Y = 8.0, 1.75
steps = [("polar (E − t, K)", "encode"), ("e1 (E − t bits)", ""), ("+ copies of t bits", "repeat"),
         ("copy on Q of the\noriginal's symbol", "map"), ("channel", ""), (r"$\ell_1[\mathrm{rep}]\ {+}{=}\ \ell_{\mathrm{copy}}$", "MRC"),
         ("CA-SCL decode", "")]
for i, (t, lab) in enumerate(steps):
    y = Y + i * 0.72
    box(a, X, y, 3.6, 0.5, fc=NAVY if t == "channel" else LIGHT)
    a.text(X + 1.8, y + 0.25, t, fontsize=13.5, color="white" if t == "channel" else NAVY, family=BODY_F, ha="center",
           va="center")
    if i:
        arrow(a, (X + 1.8, y - 0.21), (X + 1.8, y - 0.02))
    if lab:
        a.text(X + 3.75, y + 0.25, lab, fontsize=12, color=GREY, family=BODY_F, va="center")
save(f, "twin_repeat.png")

# 4) the difference ------------------------------------------------------------------------------------------------
f, a = slide("Moved bits vs repeated bits: the difference", "4/5")
rows = [("", "Moved bits (18)", "Repeated bits (t = 96)"),
        ("Where twins come from", "Code's own structure (Plotkin pairs\nfreed by moving info bits)", "Explicit repetition of coded bits"),
        ("What it costs", "Info set moved to worse bit-channels", "Fewer parity bits (rate up),\nMRC gain on the repeated bits"),
        ("Number of twins", "Limited by the code\n(73 on ID 13, ~6 on ID 14)", "Any t"),
        ("Placement over the burst", "Fixed by the code", "Free (ends-weighted)"),
        ("Extra receiver work", "None", "t LLR additions (MRC)"),
        ("Shortened codes", "Does not work", "Works")]
x0, cw, y = 0.83, (3.2, 4.25, 4.25), 1.5
for r, row in enumerate(rows):
    h = 0.55 if r == 0 else 0.68
    x = x0
    for c, t in enumerate(row):
        fc = NAVY if r == 0 else ("#f4f6f9" if r % 2 else "white")
        a.add_patch(Rectangle((x, y), cw[c], h, fc=fc, ec="#c3c9d2", lw=0.8))
        a.text(x + 0.15, y + h / 2, t, fontsize=15, va="center", family=BODY_F,
               color="white" if r == 0 else (NAVY if c == 0 else TXT), fontweight="bold" if (r == 0 or c == 0) else "normal")
        x += cw[c]
    y += h
a.text(x0, y + 0.45, "Both: zero pilots, same payload, same frame length. "
       "Both lose a little coding gain to buy twins; they differ in how the twins are made.",
       fontsize=15, color=NAVY, family=BODY_F, va="top")
save(f, "twin_diff.png")

# 5) data -----------------------------------------------------------------------------------------------------------
f, a = slide("Twins: results so far (before retune)", "5/5")
rows = [("", "ID 13 (QPSK 1/3, 1476 sym)", "ID 3 (QPSK 1/3, 456 sym)"),
        ("Repeated 96 vs moved\n(combined receiver)", "−0.026 dB, MACs per core x0.88", "−0.153 dB"),
        ("Repeated 96 vs other\nmoved arrangement", "−0.046 dB (moved + 2 extra frozen)", "−0.062 dB vs z0 (p = 0.014)"),
        ("Repeated 96 vs DVB-RCS2", "+0.02 dB Es/N0, −0.38 dB Eb/N0\nMACs ~x3.8 the competitor's",
         "−0.21 dB Es/N0, −0.92 dB Eb/N0\nMACs ~x3.6 the competitor's"),
        ("Other", "Twin-phase fallbacks 4-8x fewer\nwith repeated twins", "Repeated 128 no better than z0\n(dropped)")]
x0, cw, y = 0.83, (3.3, 4.2, 4.2), 1.5
for r, row in enumerate(rows):
    h = 0.55 if r == 0 else 0.78
    x = x0
    for c, t in enumerate(row):
        fc = NAVY if r == 0 else ("#f4f6f9" if r % 2 else "white")
        a.add_patch(Rectangle((x, y), cw[c], h, fc=fc, ec="#c3c9d2", lw=0.8))
        a.text(x + 0.15, y + h / 2, t, fontsize=15, va="center", family=BODY_F,
               color="white" if r == 0 else (NAVY if c == 0 else TXT), fontweight="bold" if (r == 0 or c == 0) else "normal")
        x += cw[c]
    y += h
bullets(a, 0.83, y + 0.3, ["All twin receivers vs blind without twins (ID 13): MACs per core ~3-4x lower (~0.2-0.3 M vs 0.8-1.8 M)",
                           "Undetected errors: 0 in all twin runs",
                           "In progress: NN retrain + joint threshold retune (ID 13, ID 3); twins on ID 14 (repeated only), ID 5, ID 2",
                           "VDE-SAT and ID 42 (BPSK) cannot use twins: every BPSK symbol already has I = Q"], size=15, dy=0.4)
a.text(0.83, 7.17, PRE + " Negative dB = the repeated-twin receiver needs less SNR (Eb/N0: DVB-RCS2 pilots charged).", fontsize=11,
       color=GREY, family=BODY_F)
save(f, "twin_data.png")
