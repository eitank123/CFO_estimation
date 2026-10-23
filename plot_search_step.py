"""
Why the CRC-search grid step is 1.5e-4 * 512 / N cycles/symbol: BLER vs. CFO error.

The search decodes on f_hat + k * step, so the hypothesis nearest the true CFO is at most step / 2 off. The step is
the largest one whose worst residual (step / 2) costs little BLER against no CFO error, because the number of
hypotheses (decodes in the worst case) grows as 1 / step.

Data (polar_ber_experiment.py --mode error, full Tx/Rx chain, R = 1/10, fixed |CFO error| with random sign):
    512 symbols, CRC-11, Es/N0 -5 / -4 dB:        results/polar_results_error_chain.npy
    1024 symbols, CRC-16, Es/N0 -5.5 / -5 / -4.5: lowrate/results/polar_results_error_chain_L1024_err1024.npy

    python plot_search_step.py --packet 1024   # -> lowrate/plots/bler/polar_bler_vs_cfo_error_search_step[_L1024].png
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import paths
from train_snr_nn import crb

HERE = os.path.dirname(os.path.abspath(__file__))
SIGMAS, NN_FACTOR = 4.0, 1.3            # grid half-width = 4 * 1.3 * sqrt(CRB) (polar_ber_experiment.SEARCH_SIGMAS)
CONFIG = {   # packet: (results file, code, CRC, SNRs and colours)
    512: (os.path.join("results", "polar_results_error_chain.npy"), "R=0.1", 11,
          ((-5.0, "#1f77b4"), (-4.0, "#d62728"))),
    1024: (os.path.join("lowrate", "results", "polar_results_error_chain_L1024_err1024.npy"), "R=0.1,C16", 16,
           ((-5.0, "#1f77b4"), (-4.5, "#d62728"))),
}


def load(packet):
    f, code, _, snrs = CONFIG[packet]
    r = [x for x in np.load(os.path.join(HERE, f), allow_pickle=True) if x["code"] == code]
    out = {}
    for s, _ in snrs:
        pts = sorted((float(x["src"]), x["bler"], x["frame_err"], x["frames"]) for x in r if abs(x["esn0"] - s) < 0.01)
        if pts:
            out[s] = tuple(np.array(v, float) for v in zip(*pts))
    return out


def sci(x):
    m, e = f"{x:.2e}".split("e")
    return f"{float(m):g}e{int(e)}"


def interp_loglog(x, xs, ys):
    return np.exp(np.interp(np.log(x), np.log(xs), np.log(ys)))


def main(packet):
    step = 1.5e-4 * 512 / packet                    # polar_ber_experiment.SEARCH_STEP
    data = load(packet)
    _, _, crc, snrs = CONFIG[packet]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    lo, base = 1e-5, []
    for s, c in snrs:
        if s not in data:
            continue
        eps, bler, err, n = data[s]
        b0 = bler[eps == 0][0]
        base.append(b0)
        pos = (eps > 0) & (eps <= 1.2e-3)
        lo = min(lo, eps[pos].min())
        ci = 1.96 / np.sqrt(np.maximum(err[pos], 1))                     # relative 95 % half-width (Poisson)
        lab = f"SNR = {s:g} dB"
        ax.errorbar(eps[pos], bler[pos], yerr=bler[pos] * ci, fmt="-o", color=c, ms=5, lw=2, capsize=3, label=lab)
        ax.axhline(b0, color=c, ls=":", lw=1.4, label=f"{lab}, no CFO error ({b0:.1e}, {int(err[eps == 0][0])} errors)")
    ax.axvspan(lo * 0.8, step / 2, color="0.85", alpha=0.6, lw=0)
    ax.axvline(step / 2, color="0.2", ls="--", lw=1.4)
    ax.axvline(step, color="0.2", ls="-.", lw=1.4)
    ax.set(xscale="log", yscale="log", xlabel="|CFO error| (cycles/symbol)", ylabel="BLER")
    base = sorted(base)
    ty = np.sqrt(base[-2] * base[-1]) if len(base) > 1 else base[0] * 5    # between the curves
    ax.text(step / 2 * 0.95, ty, f"Δ/2 = {sci(step / 2)}:\nlargest error left\nby the grid", fontsize=9.5, color="0.2",
            ha="right")
    ax.text(step * 1.06, ty * 1.6, f"Δ = {sci(step)}:\nthe chosen\nsearch step", fontsize=9.5, color="0.2")
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper left")
    fig.suptitle("BLER vs. CFO error", fontsize=15, fontweight="bold")
    ax.set_title(f"{packet}-symbol packet, R = 1/10, CRC-{crc}, CA-SCL L = 8; the search grid f̂ + k·Δ leaves at most "
                 "Δ/2 (shaded)", fontsize=10.5, color="0.3")
    fig.tight_layout()
    out = paths.plot("polar_bler_vs_cfo_error_search_step" + ("" if packet == 512 else f"_L{packet}") + ".png")
    fig.savefig(out, dpi=300)
    print("saved", out)
    for s in data:
        eps, bler, err, n = data[s]
        b0 = bler[eps == 0][0]
        xs, ys = np.concatenate([[1e-8], eps[eps > 0]]), np.concatenate([[b0], bler[eps > 0]])
        for d in np.array([1 / 3, 2 / 3, 1, 4 / 3, 2, 8 / 3]) * step:
            print(f"{s:g} dB  step {d:.2e}: BLER(step/2)/BLER(0) = {interp_loglog(d / 2, xs, ys) / b0:.3f}  "
                  f"grid {2 * int(np.ceil(SIGMAS * NN_FACTOR * np.sqrt(crb(s)) / d)) + 1} hypotheses")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", type=int, choices=sorted(CONFIG), default=512)
    main(ap.parse_args().packet)
