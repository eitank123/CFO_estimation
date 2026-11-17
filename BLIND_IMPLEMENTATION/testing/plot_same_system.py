"""Blind vs ONLY the competitors designed for the same kind of system as ours (2026-11-15, user request): short
single-carrier bursts on a return link / uplink, operating below ~3 dB Es/N0, designed for a CFO of >= ~1 % of the
symbol rate. Existing results only; rerun as the est5 parts land (ViaSat, Advantech and NB-IoT appear then).

    py BLIND_IMPLEMENTATION/testing/plot_same_system.py

Included: DVB-RCS2 return-link bursts (RCS2-13 = ID 13 + Rife-Boorstyn; G4096 = Griebel 2021 at the paper's
zero-padding; Griebel faithful = the paper's one-decode chain; RCS2 pre/post = 16 + 16; pre128 ML = the preamble-only
receiver TR 101 545-4 assumes), ViaSat burst modems (C9, US 7653150 / US 8243859), Advantech burst modems (C14 hyb3,
US 7590199), NB-IoT single-tone NPUSCH DMRS (C10). Excluded: DVB-S2 / CCSDS (continuous long frames), Wi-Fi and
MIL-STD-188-110 (designed for high SNR), VDE-SAT (80k-symbol bursts), 400ZR (optical). Cards: comparison_full.md.
Outputs: results/plots/same_bler_R*.png, same_macs_R*.png.
"""
import os
import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plot_e4 as P

SAME = ["RCS2-13", "G4096", "Griebel faithful", "RCS2 pre/post", "pre128 ML", "ViaSat UW", "hyb3", "DMRS 1/7"]
RENAME = {"pre128 ML": "128-symbol preamble, ML (the DVB-RCS2 guideline's preamble-only receiver, TR 101 545-4)",
          "RCS2 pre/post": "DVB-RCS2 16 pre + 16 post, 4th-power NDA"}


def fig(rate, key):
    E, B = P.e4(rate, e5=True, ars=True), P.blind(rate)
    sty = P.styles(e5=True, ars=True)
    srcs = [k for k in SAME if k in E and (key == "bler" or k != "Genie")]
    allx = [s for k in srcs for s in E[k]] + list(B)
    lo, hi = max(min(allx) - 0.25, -5.0), max(allx) + 0.25
    Bk = {s: v for s, v in B.items() if lo <= s <= hi and (key == "bler" or v.get("core"))}
    f, ax = plt.subplots(figsize=(10, 7.4))
    P.curve(ax, Bk, key, P.BLIND[0], P.BLIND[1], P.BLIND[2], lw=2.8, ms=9)
    for k in srcs:
        lab, c, m, ls = sty[k]
        P.curve(ax, {s: v for s, v in E[k].items() if s >= -5.0}, key, RENAME.get(k, lab), c, m, ls=ls,
                lw=1.4 if k == "Genie" else 1.9)
    ax.set_yscale("log")
    ax.set_xlabel("SNR (Es/N0) [dB]  (burst energy per data symbol: pilot energy charged)", fontsize=12)
    if key == "bler":
        ax.set_ylabel("BLER", fontsize=12)
        ax.set_title(f"BLER vs SNR, R = {rate}  (blind vs same-system burst receivers)", fontsize=13)
    else:
        ax.set_ylabel("MACs per core per packet [M]  (scheduled count, log scale)", fontsize=12)
        ax.set_title(f"MACs per core vs SNR, R = {rate}  (blind vs same-system burst receivers)", fontsize=13)
        fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.2f}" if v >= 0.1 else f"{v:.3f}")
        ax.yaxis.set_major_formatter(fmt)
        ax.yaxis.set_minor_formatter(fmt)
        ax.tick_params(axis="y", which="minor", labelsize=8)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=1, frameon=False)
    p = os.path.join(P.OUT, f"same_{'bler' if key == 'bler' else 'macs'}_R{P.tag(rate)}.png")
    f.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(f)
    missing = [k for k in SAME if k not in E]
    print(p, "| not measured yet:", ", ".join(missing) if missing else "-")


if __name__ == "__main__":
    for r in ("1/10", "0.15", "2/5", "1/2"):
        fig(r, "bler")
        fig(r, "core")
