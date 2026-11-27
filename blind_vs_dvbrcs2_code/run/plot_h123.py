"""
ID 13 (twc-id13-ph moved-bit twins, known timing): previous blind receiver vs the new architectures, same packets
(seed 9913). H1 = combined CFO spectrum (4th power + twins + 4-symbol parity) top-8 local decode after the fast path,
old search as fallback (arm E); H2 = the same on every packet, cell-sized parity FFT (arm E2, "l"); H3 = H1 + partial-
decoder ranking of the candidates (H3d, progressive). DVB-RCS2 for reference. 2 x 2: BLER and MACs per core vs Es/N0 and
Eb/N0.

    py fullsys/plot_h123_id13.py   -> BLIND_IMPLEMENTATION/testing/results/h123_id13.png
"""
import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_best_fs as B  # noqa: E402
import plot_twin_fs as T  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
CFG = {"id13": dict(snrs={-1.0: ["m10"], -0.9: ["m09"], -0.8: ["m08"], -0.7: ["m07"], -0.6: ["m06"],
                          -0.4: ["m04a", "m04b"]}, A=952, xl=(-1.1, -0.3)),
       "id3": dict(snrs={-0.5: ["m05a", "m05b", "m05c", "m05d"], -0.4: ["m04"], -0.2: ["m02"], 0.0: ["p00"],
                         0.1: ["p01a", "p01b", "p01c", "p01d"]}, A=272, xl=(-0.6, 0.2))}
LAB = [("a", "previous blind receiver", "#003366", "-o"),
       ("e", "H1: combined CFO spectrum, top-8 + fallback", "#d62728", "-*"),
       ("ed", "H1 + phase diversity at the top candidate", "#e377c2", "-^"),
       ("e2l", "H2: combined spectrum on every packet", "#2ca02c", "--D"),
       ("h3d", "H3: H1 + partial-decode ranking", "#9467bd", ":s")]


def point(pre, tags):
    e = f = c = 0.0
    for t in tags:
        fn = os.path.join(RES, f"blind_fs_{pre}{t}.json")
        if not os.path.exists(fn):
            return None
        p = json.load(open(fn))["points"]
        p = p[0] if isinstance(p, list) else list(p.values())[0]
        e += p["frame_err"]
        f += p["frames"]
        c += p["crit_par_d4a_per_frame"] * p["frames"]
    return e, f, c / f


def main(fmt="id13", only=None, tag="h123", title="new blind architectures vs previous"):
    """only: arm keys of LAB to draw (None = all); tag: output name prefix."""
    cf = CFG[fmt]
    SNRS = cf["snrs"]
    ARMS = [((f"h3-{fmt}-" if k == "h3d" else f"h1-{fmt}-") + k + "-", nm, col, mk) for k, nm, col, mk in LAB if only is None or k in only]
    fig, axs = plt.subplots(2, 2, figsize=(16, 11))
    ax = [axs[0, 0], axs[0, 1], axs[1, 0], axs[1, 1]]   # BLER Es, BLER Eb, MACs Es, MACs Eb
    d, ce, cp, cm = B.comp_points(fmt)
    ob, oc = d["off_blind"], d["off_comp"]
    ov = 100.0 * d["known"] / (cf["A"] * 10 ** (oc / 10))
    ax[0].semilogy(*T._nz(ce, cp), "--s", color=T.ORANGE, lw=2, ms=5, label="DVB-RCS2")
    ax[1].semilogy(*T._nz(ce + oc, cp), "--s", color=T.ORANGE, lw=2, ms=5)
    ax[2].semilogy(ce, cm / 1e6, "--s", color=T.ORANGE, lw=2, ms=5)
    ax[3].semilogy(ce + oc, cm / 1e6, "--s", color=T.ORANGE, lw=2, ms=5)
    for pre, nm, col, mk in ARMS:
        pts = {s: point(pre, t) for s, t in SNRS.items()}
        s = np.array(sorted(x for x in pts if pts[x] is not None))
        if not len(s):
            continue
        e = np.array([pts[x][0] for x in s])
        f = np.array([pts[x][1] for x in s])
        c = np.array([pts[x][2] for x in s])
        ax[0].semilogy(s, e / f, mk, color=col, lw=2, ms=7, label=nm)
        ax[1].semilogy(s + ob, e / f, mk, color=col, lw=2, ms=7)
        ax[2].semilogy(s, c / 1e6, mk, color=col, lw=2, ms=7)
        ax[3].semilogy(s + ob, c / 1e6, mk, color=col, lw=2, ms=7)
    ax[0].set_title("BLER vs Es/N0", fontweight="bold")
    ax[1].set_title(f"BLER vs Eb/N0 (DVB-RCS2 pilots {ov:.1f} %)", fontweight="bold")
    ax[2].set_title("MACs vs Es/N0", fontweight="bold")
    ax[3].set_title("MACs vs Eb/N0", fontweight="bold")
    for i, a_ in enumerate(ax):
        a_.grid(True, which="both", ls=":", color="#cccccc")
        eb = i in (1, 3)
        a_.set_xlabel("Eb/N0 per payload bit [dB]" if eb else "SNR Es/N0 [dB]")
        a_.set_ylabel("BLER" if i < 2 else "mean MACs per core [M]")
        a_.set_xlim((cf["xl"][0] + ob, cf["xl"][1] + 0.25 + ob) if eb else cf["xl"])
    fig.suptitle(f"{fmt.upper().replace('ID', 'ID ')}: {title}", fontsize=14, fontweight="bold")
    h, l_ = ax[0].get_legend_handles_labels()
    fig.legend(h, l_, loc="lower center", ncol=3, frameon=False, fontsize=11)
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    out = os.path.join(T.OUT, f"{tag}_{fmt}.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    fm = sys.argv[1] if len(sys.argv) > 1 else "id13"
    if len(sys.argv) > 2 and sys.argv[2] == "h2":       # py fullsys/plot_h123.py id13 h2 -> h2_vs_prev_id13.png
        main(fm, only=("a", "e2l"), tag="h2_vs_prev", title="H2 vs previous blind receiver")
    else:
        main(fm)
