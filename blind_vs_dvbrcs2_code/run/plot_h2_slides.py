"""
Slide figures for the H2 receiver (combined CFO spectrum on every packet, top-K direct decode, old search as fallback;
arm E2 with the cell-sized parity FFT, "e2l") vs the previous blind receiver (arm A) and DVB-RCS2, same packets.
Reads the existing part JSONs only (no simulation). Writes figs/h2_<fmt>_{bler,macs,legend}.png for \\resultpanels.

    py BLIND_IMPLEMENTATION/presentation/latex/plot_h2_slides.py
"""
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FS = HERE                                          # (package) the plot helpers live in run/
sys.path.insert(0, FS)
import plot_h123 as H  # noqa: E402
import plot_best_fs as B  # noqa: E402
import plot_twin_fs as T  # noqa: E402

OUT = os.path.join(HERE, "figs")
ARMS = [("e2l", "blind receiver: combined CFO spectrum, top-K + fallback", "#2ca02c", "-D")]


def curves(fmt):
    cf = H.CFG[fmt]
    res = []
    for k, nm, col, mk in ARMS:
        pts = {s: H.point(f"h1-{fmt}-{k}-", t) for s, t in cf["snrs"].items()}
        s = np.array(sorted(x for x in pts if pts[x] is not None))
        e = np.array([pts[x][0] for x in s])
        f = np.array([pts[x][1] for x in s])
        c = np.array([pts[x][2] for x in s])
        res.append((nm, col, mk, s, e / f, c))
    return res


def main():
    hs = None
    for fmt in ("id13", "id3"):
        cf = H.CFG[fmt]
        d, ce, cp, cm = B.comp_points(fmt)
        cs = curves(fmt)
        for kind in ("bler", "macs"):
            fig, ax = plt.subplots(figsize=(7.6, 4.1))
            if kind == "bler":
                ax.semilogy(*T._nz(ce, cp), "--s", color=T.ORANGE, lw=2, ms=5, label="DVB-RCS2")
            else:
                ax.semilogy(ce, cm / 1e6, "--s", color=T.ORANGE, lw=2, ms=5, label="DVB-RCS2")
            for nm, col, mk, s, b, c in cs:
                y = b if kind == "bler" else c / 1e6
                ax.semilogy(s, y, mk, color=col, lw=2, ms=7, label=nm)
            ax.set_xlim(cf["xl"])
            ax.grid(True, which="both", ls=":", color="#cccccc")
            ax.set_xlabel("SNR $E_s/N_0$ [dB]", fontsize=12)
            ax.set_ylabel("BLER" if kind == "bler" else "mean MACs per core [M]", fontsize=12)
            ax.set_title(("BLER" if kind == "bler" else "MACs per core") + f" vs $E_s/N_0$, {fmt.upper().replace('ID', 'ID ')}",
                         fontsize=13, fontweight="bold")
            fig.tight_layout()
            fig.savefig(os.path.join(OUT, f"h2_{fmt}_{kind}.png"), dpi=150)
            hs = ax.get_legend_handles_labels()
            plt.close(fig)
        # 2 x 2: BLER / MACs vs Es/N0 and vs Eb/N0 per payload bit (competitor's known symbols charged)
        ob, oc = d["off_blind"], d["off_comp"]
        plt.rcParams.update({"xtick.labelsize": 14, "ytick.labelsize": 14})
        fig, axs = plt.subplots(2, 2, figsize=(14, 7.0))
        for row, kind in enumerate(("bler", "macs")):
            for col_, eb in enumerate((False, True)):
                ax = axs[row, col_]
                xo_c, xo_b = (oc, ob) if eb else (0.0, 0.0)
                if kind == "bler":
                    xx, yy = T._nz(ce, cp)
                    ax.semilogy(np.asarray(xx) + xo_c, yy, "--s", color=T.ORANGE, lw=2, ms=5, label="DVB-RCS2")
                else:
                    ax.semilogy(np.asarray(ce) + xo_c, cm / 1e6, "--s", color=T.ORANGE, lw=2, ms=5, label="DVB-RCS2")
                for nm, colr, mk, s, b, c in cs:
                    ax.semilogy(s + xo_b, b if kind == "bler" else c / 1e6, mk, color=colr, lw=2.5, ms=9, label=nm)
                xl = cf["xl"]
                ax.set_xlim((xl[0] + ob, xl[1] + 0.25 + ob) if eb else xl)
                ax.grid(True, which="both", ls=":", color="#cccccc")
                ax.set_xlabel("$E_b/N_0$ per payload bit [dB]" if eb else "$E_s/N_0$ [dB]", fontsize=16)
                ax.set_ylabel("BLER" if kind == "bler" else "MACs per core [M]", fontsize=16)
                ax.set_title(("BLER" if kind == "bler" else "MACs per core") + (" vs $E_b/N_0$" if eb else " vs $E_s/N_0$"),
                             fontsize=17, fontweight="bold")
        h_, l_ = axs[0, 0].get_legend_handles_labels()
        fig.legend(h_, l_, loc="lower center", ncol=2, frameon=False, fontsize=16)
        fig.tight_layout(rect=(0, 0.06, 1, 1))
        fig.savefig(os.path.join(OUT, f"h2_{fmt}_4.png"), dpi=150)
        plt.close(fig)
        fig = plt.figure(figsize=(15, 0.6))
        fig.legend(*hs, loc="center", ncol=3, frameon=False, fontsize=12)
        fig.savefig(os.path.join(OUT, f"h2_{fmt}_legend.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)
        for nm, col, mk, s, b, c in cs:
            print(fmt, nm[:22], " ".join(f"{x:+.1f}:{bb:.2e}/{cc/1e3:.0f}k" for x, bb, cc in zip(s, b, c)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
