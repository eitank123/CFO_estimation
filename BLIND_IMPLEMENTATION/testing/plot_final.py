"""Final comparison figures and table from EXISTING results only (est4 parts + the blind parts; no simulation).
Outputs (results/plots/ unless stated):
  bler_raw_R*.png   BLER vs the raw Es/N0 of the data symbols (pilot energy NOT charged): blind, genie, RCS2-13, 128 ML
  bler_norm_R*.png  BLER vs the charged SNR (est4 snr_plot = Es/N0 + 10 log10((1024 + Nk) / 1024)), Clopper-Pearson 95 %
  pareto_R*.png     required (charged) SNR at the target BLER vs MACs per core (scheduled, log x)
  results/final_table.md  required SNR per receiver / rate (+ CI), MACs per core there, pilot overhead [dB]
Required SNR = plot_e4.gap_db (log-linear interpolation) on plot_e4.e4 / plot_e4.blind: these reproduce 08, 8.2a.
CI = the crossings of the per-point Clopper-Pearson 95 % upper / lower BLER curves (statistics of the two bracketing
points only; no interpolation-model error). Curves: blind = plot_pres.blind (every same-BLER run pooled), pilots =
plot_pres.smooth (raw axis) or the raw counts (normalised axis, with the error bars). No point below -5 dB is drawn.
usage: py plot_final.py"""
import os, sys
import numpy as np
from scipy.stats import beta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plot_e4 as P4
import plot_pres as PP

OUT = os.path.join(HERE, "results", "plots")
TAB = os.path.join(HERE, "results", "final_table.md")
RATES = ("1/10", "0.15", "2/5", "1/2")
TARGET = {"1/10": [1e-4], "0.15": [1e-3, 1e-4], "2/5": [1e-3], "1/2": [1e-3]}
XMIN = -5.0                                            # no points below -5 dB (user, 2026-11-15)
NK = {"Genie": 0, "RCS2-13": 116, "pre128 ML": 128, "pre128 M&M": 128, "split64 ML": 128, "RCS2 pre/post": 32}
RAW = ("RCS2-13", "pre128 ML")   # genie not drawn (user 2026-11-15)                # receivers of bler_raw_R*
PAR = ("RCS2-13", "pre128 ML", "pre128 M&M", "split64 ML", "RCS2 pre/post")   # pilot receivers of pareto_R*
STY = {s: (lab, c, m, ls) for s, lab, c, m, ls in PP.STY}


def cp(k, n, a=0.05):
    """Clopper-Pearson (lo, hi) for k errors in n"""
    lo = beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi


def req(pts, t):
    """(SNR at BLER t, CI lo, CI hi) from {snr: dict(err, n)}; CI from the CP bound curves (lo bound 0 -> 1e-12)"""
    g = P4.gap_db(pts, t)
    b = {s: cp(v["err"], v["n"]) for s, v in pts.items()}
    lo = P4.gap_db({s: dict(err=max(b[s][0], 1e-12), n=1) for s in pts}, t)   # optimistic curve -> lower SNR
    hi = P4.gap_db({s: dict(err=b[s][1], n=1) for s in pts}, t)                # pessimistic curve -> higher SNR
    return g, lo, hi


def core_at(pts, x):
    """MACs per core at SNR x: linear interpolation between the bracketing points with a count, else the nearest one;
    returns (core, note)"""
    xs = sorted(s for s in pts if pts[s].get("core"))
    if not xs or x is None:
        return None, ""
    for a, b in zip(xs, xs[1:]):
        if a <= x <= b:
            return pts[a]["core"] + (x - a) / (b - a) * (pts[b]["core"] - pts[a]["core"]), ""
    s = min(xs, key=lambda q: abs(q - x))
    return pts[s]["core"], f" (nearest count, {s:g} dB)"


def rawmap(rate):
    """{src: {snr_plot: raw Es/N0 of the data symbols}} from plot_e4.e4"""
    return {src: {s: v["snr"] for s, v in d.items()} for src, d in P4.e4(rate).items()}


def save(f, ax, name, rate):
    ax.set_xlabel("SNR (Es/N0) [dB]", fontsize=13)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=1, frameon=False)
    f.tight_layout()
    p = os.path.join(OUT, f"{name}_R{P4.tag(rate)}.png")
    f.savefig(p, dpi=160, bbox_inches="tight")
    plt.close(f)
    print(p)


def bblind(rate):
    """pooled blind curve {snr: (err, n)}, >= -5 dB, no 0-error points"""
    return {s: v for s, v in PP.blind(rate).items() if v[0] > 0 and s >= XMIN}


def fig_raw(rate):
    f, ax = plt.subplots(figsize=(10, 7.6))
    B = bblind(rate)
    xb = sorted(B)
    ax.plot(xb, [B[s][0] / B[s][1] for s in xb], color=PP.BLIND[1], marker=PP.BLIND[2], lw=3, ms=10,
            label=PP.BLIND[0], zorder=5)
    PL, RM = PP.pilots(rate), rawmap(rate)
    for src in RAW:
        if src not in PL:
            continue
        lab, c, m, ls = STY[src]
        x, y, f0, uf, nf = PP.smooth(PL[src])
        xr = np.array([RM[src][round(s, 3)] for s in x])
        keep = (xr >= XMIN) & (y > 0)
        if f0 is not None:
            lab += f"\n   (floor = wrong CRC passes, pooled: {uf} in {nf / 1e6:.1f}M packets)"
        if keep.any():
            ax.plot(xr[keep], y[keep], color=c, marker=m, ls=ls, lw=1.4 if src == "Genie" else 2.0, ms=6,
                    label=lab + ("" if src == "Genie" else " - pilot energy NOT charged"))
    ax.set_yscale("log")
    ax.set_ylim(top=1.2)
    ax.set_ylabel("BLER", fontsize=13)
    ax.set_title(f"BLER vs SNR, R = {rate}", fontsize=15)
    ax.text(0.99, 0.99, "x = Es/N0 of the data symbols; the pilot symbols' energy is not counted", fontsize=8.5,
            transform=ax.transAxes, color="#555555", ha="right", va="top")
    save(f, ax, "bler_raw", rate)


def fig_norm(rate):
    f, ax = plt.subplots(figsize=(10, 7.6))
    B = bblind(rate)
    xb = sorted(B)
    yb = np.array([B[s][0] / B[s][1] for s in xb])
    ci = np.array([cp(*B[s]) for s in xb]).T
    ax.errorbar(xb, yb, yerr=[yb - ci[0], ci[1] - yb], color=PP.BLIND[1], marker=PP.BLIND[2], lw=3, ms=10, capsize=4,
                label=PP.BLIND[0], zorder=5)
    E = P4.e4(rate)
    for src, (lab, c, m, ls) in STY.items():
        if src == "Genie":                            # genie not drawn (user 2026-11-15)
            continue
        d = {s: v for s, v in E.get(src, {}).items() if v["err"] > 0 and s >= XMIN}
        if not d:
            continue
        xs = sorted(d)
        y = np.array([d[s]["err"] / d[s]["n"] for s in xs])
        ci = np.array([cp(d[s]["err"], d[s]["n"]) for s in xs]).T
        ax.errorbar(xs, y, yerr=[y - ci[0], ci[1] - y], color=c, marker=m, ls=ls, lw=1.4 if src == "Genie" else 2.0,
                    ms=6, capsize=3, label=lab + (f" (+{10 * np.log10((1024 + NK[src]) / 1024):.2f} dB charged)"
                                                  if NK[src] else ""))
    ax.set_yscale("log")
    ax.set_ylim(top=1.2)
    ax.set_ylabel("BLER (Clopper-Pearson 95 % bars)", fontsize=13)
    ax.set_title(f"BLER vs SNR, R = {rate}", fontsize=15)
    ax.text(0.99, 0.99, "x = burst energy per data symbol (pilot energy charged); 0-error points not drawn",
            fontsize=8.5, transform=ax.transAxes, color="#555555", ha="right", va="top")
    save(f, ax, "bler_norm", rate)


def rows(rate):
    """[(receiver, target, snr, lo, hi, core, note, overhead dB, pooled-blind snr)]"""
    E, B, out = P4.e4(rate), P4.blind(rate), []
    Bp = {s: dict(err=k, n=n) for s, (k, n) in PP.blind(rate).items()}
    for t in TARGET[rate]:
        g, lo, hi = req(B, t)
        c, nt = core_at(B, g)
        out.append(("Blind", t, g, lo, hi, c, nt, 0.0, P4.gap_db(Bp, t)))
        for src in STY:
            if src not in E:
                continue
            g, lo, hi = req(E[src], t)
            c, nt = core_at(E[src], g)
            ov = float(np.mean([s - v["snr"] for s, v in E[src].items()]))
            out.append((src, t, g, lo, hi, c, nt, ov, None))
    return out


def fig_pareto(rate, R):
    f, ax = plt.subplots(figsize=(10, 7.6))
    sty = dict(STY, Blind=(PP.BLIND[0], PP.BLIND[1], PP.BLIND[2], "-"))
    seen = set()
    for src, t, g, lo, hi, c, nt, ov, _ in R:
        if g is None or c is None or src not in ("Blind",) + PAR:
            continue
        lab, col, m, _ = sty[src]
        first = t == TARGET[rate][0]
        yerr = [[g - lo if lo is not None else 0], [hi - g if hi is not None else 0]]
        lab = f"{lab}, BLER {t:.0e}" if len(TARGET[rate]) > 1 else lab
        ax.errorbar([c / 1e6], [g], yerr=yerr, color=col, marker=m, ms=12 if src == "Blind" else 9, capsize=4, ls="none",
                    mfc=col if first else "white", mew=2, label=lab)
        seen.add(src)
    ax.set_xscale("log")
    ax.set_xlabel("MACs per core per packet [M] (scheduled, at the required SNR)", fontsize=13)
    ax.set_ylabel("required SNR (Es/N0) [dB] (pilot energy charged)", fontsize=13)
    tt = ", ".join(f"{t:.0e}" for t in TARGET[rate])
    ax.set_title(f"Required SNR vs MACs per core, R = {rate} (BLER {tt})", fontsize=14)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=1 if len(TARGET[rate]) == 1 else 2,
              frameon=False)
    f.tight_layout()
    p = os.path.join(OUT, f"pareto_R{P4.tag(rate)}.png")
    f.savefig(p, dpi=160, bbox_inches="tight")
    plt.close(f)
    print(p)


def fmt(v, d=2):
    return "-" if v is None else f"{v:.{d}f}"


def table(allrows):
    L = ["# Final comparison: required SNR, MACs per core, pilot overhead",
         "",
         "Generated by `testing/plot_final.py` from existing results only (est4 `bler_e4-*.json` + the blind parts via",
         "`agg_cmp`). SNR = est4 axis: burst energy per data symbol, pilot energy charged",
         "(Es/N0 + overhead). Required SNR = log-linear interpolation (`plot_e4.gap_db`) on `plot_e4.e4` / `plot_e4.blind`,",
         "the same as 08, 8.2a. CI = crossing of the per-point Clopper-Pearson 95 % lower / upper BLER curves (statistics",
         "of the bracketing points only, no interpolation-model error; '-' = that bound curve does not cross in the",
         "simulated range). MACs per core = scheduled count, linearly interpolated at the required SNR. Blind (pooled) =",
         "the same crossing on `plot_pres.blind` (every same-BLER run pooled; the curves of the figures).",
         "'fails' = no crossing in the simulated range.", ""]
    for rate, R in allrows:
        L += [f"## R = {rate}", "",
              "| Receiver | BLER | required SNR [dB] | 95 % CI [dB] | M MACs per core | pilot overhead [dB] |",
              "|---|---|---|---|---|---|"]
        for src, t, g, lo, hi, c, nt, ov, gp in R:
            name = src + (f" (pooled: {fmt(gp)})" if src == "Blind" else "")
            if g is None:
                L.append(f"| {name} | {t:.0e} | fails | - | - | {ov:.2f} |")
                continue
            note = " (crossing uses the -5.5 dB point)" if g < XMIN else ""
            L.append(f"| {name} | {t:.0e} | {g:.2f}{note} | [{fmt(lo)}, {fmt(hi)}] | "
                     f"{'-' if c is None else f'{c / 1e6:.3f}'}{nt} | {ov:.2f} |")
        L.append("")
    open(TAB, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print(TAB)


if __name__ == "__main__":
    allrows = []
    for rate in RATES:
        fig_raw(rate)
        fig_norm(rate)
        R = rows(rate)
        fig_pareto(rate, R)
        allrows.append((rate, R))
    table(allrows)
