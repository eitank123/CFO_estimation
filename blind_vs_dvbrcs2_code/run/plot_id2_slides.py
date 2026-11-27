"""
ID 2 (k12 moved-bit twins, no weight-4 checks): the deck's blind receiver (H2 arm e2, combined spectrum on every packet,
top-K M = 1 + fallback) vs DVB-RCS2, from the existing part JSONs (fullsys/results/blind_fs_h1-id2-e2-p*-m1.json).
Also the per-packet MACs cap (a packet whose scheduled 32-core crit passes C is stopped and counted as an error; charged C),
computed offline from each part's core_hist (per-outcome c_d4a histograms, 0.05-decade bins from 1e4): capped BLER exact
when C is a bin edge; capped mean with the no-cap cost at the bin's geometric midpoint. No simulation.

Writes figs/h2_id2_4.png (BLER / MACs vs Es/N0 and Eb/N0) and figs/cap_id2.png (BLER / MACs vs Es/N0 with caps).

    py BLIND_IMPLEMENTATION/presentation/latex/plot_id2_slides.py
"""
import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FS = HERE                                          # (package) the plot helpers and results/ live in run/
sys.path.insert(0, FS)
import plot_best_fs as B  # noqa: E402
import plot_twin_fs as T  # noqa: E402

RES = os.path.join(FS, "results")
OUT = os.path.join(HERE, "figs")
PTS = {0.4: ["p040a", "p040b", "p040c", "p040d"], 0.5: ["p050"], 0.75: ["p075"], 1.0: ["p100"],
       1.2: ["p120a", "p120b", "p120c", "p120d"]}
B0, BPD, NB = 4.0, 20, 100                       # run_blind_fs.CORE_B
CAPS = [(None, "blind, no cap", "#2ca02c", "-D"), (2e6, "blind, cap 2 M", "#d95f02", "-v"),
        (1e6, "blind, cap 1 M", "#d62728", "-<"), (5e5, "blind, cap 0.5 M", "#7570b3", "->")]
XL = (0.1, 1.4)


def load(tags):
    """Merge the parts of one point (frames, errors, mean crit, core_hist); None if any part is missing."""
    out = None
    for tag in tags:
        fn = os.path.join(RES, f"blind_fs_h1-id2-e2-{tag}-m1.json")
        if not os.path.exists(fn):
            return None
        p = json.load(open(fn))["points"]
        p = p[0] if isinstance(p, list) else list(p.values())[0]
        if out is None:
            out = dict(frames=0, frame_err=0, csum=0.0,
                       core_hist={k: {"c_d4a": np.zeros(NB)} for k in ("right", "wrong", "failed")})
        out["frames"] += p["frames"]
        out["frame_err"] += p["frame_err"]
        out["csum"] += p["crit_par_d4a_per_frame"] * p["frames"]
        for k in ("right", "wrong", "failed"):
            out["core_hist"][k]["c_d4a"] += np.asarray(p["core_hist"][k]["c_d4a"], float)
    out["crit_par_d4a_per_frame"] = out["csum"] / out["frames"]
    return out


def capped(p, C):
    """(errors, mean crit) with cap C (None = no cap)."""
    fr, er = p["frames"], p["frame_err"]
    mean0 = p["crit_par_d4a_per_frame"]
    if C is None:
        return er, mean0
    h = {k: np.asarray(p["core_hist"][k]["c_d4a"], float) for k in ("right", "wrong", "failed")}
    kc = int(round((np.log10(C) - B0) * BPD))     # bins >= kc are above the cap
    mid = 10 ** (B0 + (np.arange(NB) + 0.5) / BPD)
    allh = h["right"] + h["wrong"] + h["failed"]
    stopped_right = h["right"][kc:].sum()
    over = allh[kc:]
    mean = mean0 - (over * mid[kc:]).sum() / fr + over.sum() * C / fr
    return er + stopped_right, mean


def main():
    d, ce, cp, cm = B.comp_points("id2")
    ob, oc = d["off_blind"], d["off_comp"]
    P = {s: load(t) for s, t in PTS.items()}
    P = {s: v for s, v in P.items() if v is not None}
    snr = np.array(sorted(P))
    rows = []
    for C, lab, *_ in CAPS:
        e_m = [capped(P[s], C) for s in snr]
        rows.append((C, [P[s]["frames"] for s in snr], [x[0] for x in e_m], [x[1] for x in e_m]))
        print(lab, [(s, int(P[s]["frames"]), int(e), round(m / 1e3, 1)) for s, (e, m) in zip(snr, e_m)])

    plt.rcParams.update({"xtick.labelsize": 14, "ytick.labelsize": 14})
    # 2 x 2, Es and Eb
    fig, axs = plt.subplots(2, 2, figsize=(14, 7.0))
    _, fr, er, mm = rows[0]
    bl = np.array(er) / np.array(fr)
    for col, eb in enumerate((False, True)):
        xc, xb = (oc, ob) if eb else (0.0, 0.0)
        xx, yy = T._nz(ce, cp)
        axs[0, col].semilogy(np.asarray(xx) + xc, yy, "--s", color=T.ORANGE, lw=2.5, ms=6, label="DVB-RCS2")
        axs[1, col].semilogy(np.asarray(ce) + xc, np.asarray(cm) / 1e6, "--s", color=T.ORANGE, lw=2.5, ms=6, label="DVB-RCS2")
        axs[0, col].semilogy(snr + xb, bl, "-D", color="#2ca02c", lw=2.5, ms=9,
                             label="blind receiver: combined CFO spectrum, top-K + fallback")
        axs[1, col].semilogy(snr + xb, np.array(mm) / 1e6, "-D", color="#2ca02c", lw=2.5, ms=9,
                             label="blind receiver: combined CFO spectrum, top-K + fallback")
        for row in (0, 1):
            ax = axs[row, col]
            ax.set_xlim((XL[0] + ob, XL[1] - 0.2 + oc) if eb else XL)
            ax.grid(True, which="both", ls=":", color="#cccccc")
            ax.set_xlabel("$E_b/N_0$ per payload bit [dB]" if eb else "$E_s/N_0$ [dB]", fontsize=16)
            ax.set_ylabel("BLER" if row == 0 else "MACs per core [M]", fontsize=16)
            ax.set_title(("BLER" if row == 0 else "MACs per core") + (" vs $E_b/N_0$" if eb else " vs $E_s/N_0$"),
                         fontsize=17, fontweight="bold")
    h, l_ = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l_, loc="lower center", ncol=2, frameon=False, fontsize=14)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(OUT, "h2_id2_4.png"), dpi=150)
    plt.close(fig)

    # caps
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.6))
    xx, yy = T._nz(ce, cp)
    axs[0].semilogy(xx, yy, "--s", color=T.ORANGE, lw=2.2, ms=6, label="DVB-RCS2")
    axs[1].semilogy(ce, np.asarray(cm) / 1e6, "--s", color=T.ORANGE, lw=2.2, ms=6, label="DVB-RCS2")
    for (C, fr, er, mm), (_, lab, colr, mk) in zip(rows, CAPS):
        axs[0].semilogy(snr, np.array(er) / np.array(fr), mk, color=colr, lw=2.2, ms=7, label=lab)
        axs[1].semilogy(snr, np.array(mm) / 1e6, mk, color=colr, lw=2.2, ms=7, label=lab)
    axs[0].set_title("ID 2: BLER vs $E_s/N_0$", fontsize=16, fontweight="bold")
    axs[1].set_title("ID 2: mean MACs per core vs $E_s/N_0$", fontsize=16, fontweight="bold")
    axs[0].set_ylabel("BLER", fontsize=15)
    axs[1].set_ylabel("MACs per core [M]", fontsize=15)
    for ax in axs:
        ax.set_xlim(XL)
        ax.grid(True, which="both", ls=":", color="#cccccc")
        ax.set_xlabel("$E_s/N_0$ [dB]", fontsize=15)
    h, l_ = axs[0].get_legend_handles_labels()
    fig.legend(h, l_, loc="lower center", ncol=len(h), frameon=False, fontsize=13)
    fig.tight_layout(rect=(0, 0.11, 1, 1))
    fig.savefig(os.path.join(OUT, "cap_id2.png"), dpi=150)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
