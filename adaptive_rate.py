"""Adaptive code rate vs SNR for the low-rate study (512-symbol packet, CRC-11, SNR-aware NN + CRC search).

Measured points only, no interpolation: the SNR grid is -5, -4.5, ..., 10 dB (0.5 dB steps), and at each grid point
the receiver uses the highest code rate whose MEASURED BLER at that point is below BLER_TARGET. A rate switch can
therefore only happen at a grid point. Throughput = delivered data bits per packet symbol, A * (1 - BLER) / N_SYM.

Why this gives the best throughput under BLER < 1e-2: every allowed rate has 1 - BLER > 0.99 and consecutive rates
differ by >= 1.33x in A, so A_hi * (1 - BLER_hi) > 0.99 * A_hi > A_lo >= A_lo * (1 - BLER_lo): at each grid point the
highest allowed rate delivers the most data. Switching one point earlier breaks the BLER target, switching later
loses throughput; the figures show both sides at every switch.

Run: CFO_STUDY=lowrate py adaptive_rate.py   (after polar_ber_experiment.py --mode ebn0 --merge)
Figures in lowrate/plots/adaptive_rate/, table printed for the README.
"""
import json
import os
import sys

os.environ.setdefault("CFO_STUDY", "lowrate")
PACKET = int(sys.argv[sys.argv.index("--packet") + 1]) if "--packet" in sys.argv else 512   # read by p as well
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import paths
import polar_ber_experiment as p

SRC = p.SEARCH
TARGET = p.BLER_TARGET
GRID = np.round(np.arange(-5.0, 10.0 + 1e-9, 0.5), 2)   # SNR (Es/N0) points where the rate may change [dB]
TOL = 0.02                  # a measured point within 0.02 dB of a grid point is that grid point (R = 1/4: -1.0103 dB)
USER_SWITCH = -3.5          # the proposed scheme: the same policy, but R = 0.15 from -3.5 dB (512 symbols)
CRC = {512: 11, 1024: 16}[PACKET]      # 512 symbols: CRC-11 codes; 1024 symbols: CRC-16 codes ("R=x,C16")
SFX = "" if PACKET == 512 else f"_L{PACKET}"
FIXED = "R=0.1" if PACKET == 512 else "R=0.1,C16"
REF_512 = "adaptive_rate_throughput_512.json"   # the 512-symbol optimum, saved by the 512 run, drawn by the 1024 run
COL = {"opt": "#1b7837", "user": "#c51b7d", "fixed": "#2166ac", "lo": "#2166ac", "hi": "#d6604d", "target": "0.45"}


def load():
    r = list(np.load(paths.result(f"polar_results_ebn0_chain{SFX}.npy"), allow_pickle=True))
    mine = (lambda c: "," not in c) if PACKET == 512 else (lambda c: c.endswith(f",C{CRC}"))
    codes = sorted([c for c in p.codes_in(r) if mine(c) and len(p.bler_curve(r, c, SRC)[0])], key=p.rate)
    return {c: p.bler_curve(r, c, SRC)[:2] for c in codes}


def meas(curves, c, s):
    """Measured BLER of code c at grid point s, or None if c was not simulated there."""
    x, y = curves[c]
    k = np.where(np.abs(x - s) < TOL)[0]
    return float(y[k[0]]) if len(k) else None


def ok(curves, c, s):
    b = meas(curves, c, s)
    return b is not None and b < TARGET


def choose(curves, s, force=None):
    """Highest rate with measured BLER < TARGET at grid point s (force: {code: first SNR it is used})."""
    if force:
        for c, s0 in sorted(force.items(), key=lambda kv: -p.rate(kv[0])):
            better = [d for d in curves if p.rate(d) > p.rate(c) and ok(curves, d, s)]
            if s >= s0 and not better:
                return c
    good = [c for c in curves if ok(curves, c, s)]
    return max(good, key=p.rate) if good else None


def tput(c, b):
    return p.CODES[c][0] * (1 - b) / p.N_SYM


def lab(c):
    return f"R = {name(c)} ({p.CODES[c][0]} data bits)"


def name(c):
    return p.short(c.split(",")[0]).replace("R=", "")


def schedule(curves):
    plan = [(s, choose(curves, s)) for s in GRID]
    switches = [(plan[i - 1][1], c, s) for i, (s, c) in enumerate(plan) if i and c != plan[i - 1][1]]
    switches = [w for w in switches if w[0] and w[1]]          # no rate yet (data still missing): no switch
    return plan, switches


def fig_bler(curves, plan, switches):
    """Measured BLER and chosen rate of the adaptive receiver at every grid point, -5 .. 10 dB."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True, gridspec_kw={"height_ratios": [3, 1.6]})
    xs = np.array([s for s, c in plan if c])
    ys = np.array([meas(curves, c, s) for s, c in plan if c])
    a1.semilogy(xs, np.where(ys > 0, ys, np.nan), "-o", color=COL["opt"], lw=2.2, ms=5,
                label="Adaptive rate, measured BLER at each 0.5 dB point")
    a1.axhline(TARGET, color=COL["target"], ls="--", lw=1.4, label=f"Target BLER = {TARGET:g}")
    zero = xs[ys == 0]
    if len(zero):
        a1.plot(zero, np.full(len(zero), 2e-5), "v", color=COL["opt"], ms=6, mfc="none",
                label="No error in the simulated frames")
    a1.set_ylim(1e-5, 0.1)
    a1.set_ylabel("BLER")
    a1.set_title(f"Adaptive code rate ({PACKET}-symbol packet, CRC-{CRC}): measured BLER below $10^{{-2}}$ "
                 f"from −5 to 10 dB", fontsize=13)
    a1.legend(fontsize=9.5, loc="lower left")
    a1.grid(True, which="both", ls=":", alpha=0.6)
    a2.step(xs, [p.rate(c) for s, c in plan if c], where="post", color=COL["opt"], lw=2.2)
    for lo, hi, s in switches:
        a2.annotate(f"{s:g} dB", (s, p.rate(hi)), xytext=(3, 4), textcoords="offset points", fontsize=8.5)
    a2.set_ylabel("Code rate R")
    a2.set_xlabel("SNR (Es/N0) [dB]")
    a2.set_title("Chosen rate: the highest rate with measured BLER < $10^{-2}$ at that point", fontsize=11)
    a2.grid(True, ls=":", alpha=0.6)
    a2.set_xlim(GRID[0] - 0.25, GRID[-1] + 0.25)
    fig.tight_layout()
    fig.savefig(paths.plot(f"polar_adaptive_rate_bler_vs_snr{SFX}.png"), dpi=300)
    plt.close(fig)


def fig_switches(curves, switches, kind):
    """One panel per switch R_lo -> R_hi at grid point s0, grid points within 1.5 dB. kind 'bler': both BLERs and the
    target (one point earlier the higher rate breaks the target); kind 'tput': both throughputs, filled markers where
    the rate meets the target (after the switch the higher rate delivers more)."""
    n, cols = len(switches), 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(5.2 * cols, 4.3 * rows), squeeze=False)
    for ax, (lo, hi, s0) in zip(axes.flat, switches):
        pts = GRID[(GRID >= s0 - 1.5) & (GRID <= s0 + 1.5)]
        for c, col in ((lo, COL["lo"]), (hi, COL["hi"])):
            x = np.array([s for s in pts if meas(curves, c, s) is not None])
            y = np.array([meas(curves, c, s) for s in x])
            if not len(x):
                continue
            if kind == "bler":
                ax.semilogy(x, np.where(y > 0, y, np.nan), "-o", color=col, lw=2, ms=5, label=lab(c))
            else:
                t = np.array([tput(c, b) for b in y])
                good = y < TARGET
                ax.plot(x, t, "-", color=col, lw=2.0, label=lab(c))
                ax.plot(x[good], t[good], "o", color=col, ms=6)
                ax.plot(x[~good], t[~good], "o", color=col, ms=6, mfc="white")
        ax.axvspan(s0 - 0.25, pts[-1] + 0.25, color=COL["hi"], alpha=0.07)
        if kind == "bler":
            ax.axhline(TARGET, color=COL["target"], ls="--", lw=1.3, label=f"Target {TARGET:g}")
            ax.set_ylim(1e-4, 1)
            ax.set_ylabel("BLER (measured)")
        else:
            ax.set_ylabel("Throughput [data bits / symbol]")
        ax.set_xlim(pts[0] - 0.25, pts[-1] + 0.25)
        ax.set_xticks(pts)
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(f"R = {name(lo)} → {name(hi)}: switch at {s0:g} dB", fontsize=11.5)
        ax.set_xlabel("SNR (Es/N0) [dB]")
        ax.grid(True, which="both", ls=":", alpha=0.6)
        ax.legend(fontsize=8.5, loc="lower left" if kind == "bler" else "center left")
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    if kind == "bler":
        sup = "Why not switch earlier: one point before each switch (unshaded) the higher rate's BLER is above $10^{-2}$"
        fname = f"polar_adaptive_rate_switch_bler{SFX}.png"
    else:
        sup = ("Why not switch later: from each switch on (shaded) the higher rate delivers more data "
               "(hollow marker = BLER above $10^{-2}$, not allowed)")
        fname = f"polar_adaptive_rate_switch_throughput{SFX}.png"
    fig.suptitle(sup, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(paths.plot(fname), dpi=300)
    plt.close(fig)


def fig_throughput(curves, plan):
    """Throughput vs SNR at the grid points: optimal adaptive rate, the proposed switch to R = 0.15 at -3.5 dB,
    fixed R = 0.1 (simulated up to 0 dB)."""
    def series(pick):
        x, t, bad = [], [], []
        for s in GRID:
            c = pick(s)
            b = meas(curves, c, s) if c else None
            if b is None:
                continue
            x.append(s)
            t.append(tput(c, b))
            bad.append(b >= TARGET)
        return np.array(x), np.array(t), np.array(bad)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    xo, to, _ = series(lambda s: dict(plan)[s])
    xf, tf, _ = series(lambda s: FIXED)
    if PACKET == 512:
        xu, tu, bu = series(lambda s: choose(curves, s, force={"R=0.15": USER_SWITCH}))
        ulab = f"Adaptive rate, R = 0.15 already from {USER_SWITCH:g} dB (proposed)"
    else:
        ref = json.load(open(paths.result(REF_512)))
        xu, tu = np.array(ref["snr"]), np.array(ref["tput"])
        bu = np.zeros(len(xu), bool)
        ulab = "512-symbol packet, CRC-11, adaptive rate (optimal)"
    ax.step(xo, to, where="post", color=COL["opt"], lw=2.6,
            label="Adaptive rate, optimal switching" + ("" if PACKET == 512 else f" ({PACKET} symbols, CRC-{CRC})"))
    ax.step(xu, tu, where="post", color=COL["user"], lw=2.0, ls="--",
            label=ulab)
    ax.step(xf, tf, where="post", color=COL["fixed"], lw=2.0, ls=":", label=f"Fixed R = 0.1 (simulated up to {xf[-1]:g} dB)")
    ax.plot(xo, to, "o", color=COL["opt"], ms=4)
    if bu.any():
        k = np.where(bu)[0][0]
        b = meas(curves, "R=0.15", xu[k])   # 512 only (bu is all False for 1024)
        ax.plot(xu[k], tu[k], "x", color=COL["user"], ms=10, mew=2.5)
        ax.annotate(f"Proposed at {xu[k]:g} dB: BLER = {b:.1e}\nabove the $10^{{-2}}$ target", (xu[k], tu[k]),
                    xytext=(25, 45), textcoords="offset points", fontsize=9.5, color=COL["user"],
                    arrowprops=dict(arrowstyle="->", color=COL["user"]))
    ax.set_xlim(GRID[0] - 0.25, GRID[-1] + 0.25)
    ax.set_ylim(0, None)
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel(f"Throughput [data bits per symbol] = A(1 − BLER) / {p.N_SYM}")
    ax.set_title(f"Throughput vs SNR ({PACKET}-symbol packet, CRC-{CRC}, NN + CRC search, measured points)", fontsize=13)
    ax.grid(True, ls=":", alpha=0.6)
    ax.legend(fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(paths.plot(f"polar_adaptive_rate_throughput{SFX}.png"), dpi=300)
    plt.close(fig)
    if PACKET == 512:
        json.dump({"snr": [float(v) for v in xo], "tput": [float(v) for v in to]}, open(paths.result(REF_512), "w"))
    return dict(zip(xo, to)), dict(zip(xu, tu))


def main():
    curves = load()
    plan, switches = schedule(curves)
    print("Chosen rate per SNR region (switch only at measured 0.5 dB points):")
    edges = [plan[0][0]] + [s for _, _, s in switches] + [GRID[-1] + 0.5]
    rates = [plan[0][1]] + [hi for _, hi, _ in switches]
    for c, a, b in zip(rates, edges[:-1], edges[1:]):
        if c is None:
            print(f"  {a:5g} .. {b - 0.5:5g} dB: no simulated rate with BLER < {TARGET:g}")
            continue
        print(f"  {a:5g} .. {b - 0.5:5g} dB: R={name(c):6s} A={p.CODES[c][0]:4d}  "
              f"BLER at {a:g} dB {meas(curves, c, a):.2e}  throughput {tput(c, meas(curves, c, a)):.3f} b/sym")
    for lo, hi, s in switches:
        print(f"  switch {name(lo)} -> {name(hi)} at {s:g} dB: {name(hi)} BLER at {s - 0.5:g} dB = "
              f"{meas(curves, hi, s - 0.5)}, at {s:g} dB = {meas(curves, hi, s):.2e}")
    if PACKET == 512:
        b15 = meas(curves, "R=0.15", USER_SWITCH)
        print(f"Proposed switch to R=0.15 at {USER_SWITCH} dB: measured BLER {b15:.2e} "
              f"({'meets' if b15 < TARGET else 'breaks'} the target)")
    fig_bler(curves, plan, switches)
    fig_switches(curves, switches, "bler")
    fig_switches(curves, switches, "tput")
    opt, user = fig_throughput(curves, plan)
    for s in (-5, -3.5, -3, -2, -1, 0, 1, 3, 6.5, 10):
        print(f"  SNR {s:5g}: optimal {opt.get(s, float('nan')):.3f}  "
              f"{'proposed' if PACKET == 512 else '512-symbol'} {user.get(s, float('nan')):.3f} b/sym")


if __name__ == "__main__":
    main()
