"""Published reference curves of the full-system competitors (ideal sync, AWGN), the targets our implementations must
reproduce before any comparison. Existing data only.

    py BLIND_IMPLEMENTATION/testing/plot_fullsys_refs.py

Sources (results/standards/):
- DVB-RCS2, ETSI TR 101 545-4 V1.1.1 Tables 10.5, 10.6, 10.8 (PER 1e-3 and 1e-5 per waveform ID; normalized max-log-MAP,
  up to 8 iterations, ideal sync).
- DVB-RCS2 turbo code, AFF3CT reference curves (aff3ct_refs/*.txt; K = 1504 incl. CRC-32, QPSK, BCJR 8 it., ADAPTIVE
  scaling; full FER curves; ISTC 2016 Fig. 7). N = 3008 is the ID 14 code.
- VDE-SAT, ITU-R M.2435 Fig. 11 (88 info bits, QPSK, turbo 1/4), digitized by eye from the figure (+-0.02 dB).
Output: results/plots/DVB-RCS2/BLER/fullsys_refs.png
"""
import glob
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STD = os.path.join(HERE, "results", "standards")
OUT = os.path.join(HERE, "results", "plots", "DVB-RCS2", "BLER", "fullsys_refs.png")

TR = {  # waveform ID: (label, Es/N0 @1e-3, @1e-5)
    3: ("ID 3: QPSK 1/3, 536 sym", -0.27, 0.22),
    13: ("ID 13: QPSK 1/3, 1616 sym", -0.80, -0.51),
    14: ("ID 14: QPSK 1/2, 1616 sym", 1.49, 1.71),
    42: ("ID 42: pi/2-BPSK 1/3, 3236 sym", -3.81, -3.52),
}
M2435 = [(-3.30, 0.52), (-3.05, 0.40), (-2.80, 0.26), (-2.55, 0.17), (-2.30, 0.11), (-2.05, 0.048), (-1.80, 0.028),
         (-1.55, 0.012), (-1.30, 0.0047), (-1.05, 0.0022), (-0.80, 0.00105), (-0.55, 0.00037), (-0.30, 0.00018)]
COL = ["#2a78d6", "#eb6834", "#1f9e6e", "#9b59b6"]


def aff3ct(path):
    rows = []
    for line in open(path):
        m = re.match(r"\s*(-?[\d.]+)\s*\|\s*(-?[\d.]+)\s*\|.*?\|\s*([\d.e+-]+)\s*\|\s*([\d.e+-]+)\s*\|\|", line)
        if m:
            es, eb, ber, fer = map(float, m.groups())
            if 0 < fer < 1:
                rows.append((es, fer))
    return np.array(rows)


def main():
    f, (a, b) = plt.subplots(1, 2, figsize=(13, 5.6))
    for c, (wid, (lab, p3, p5)) in zip(COL, TR.items()):
        a.semilogy([p3, p5], [1e-3, 1e-5], "o--", color=c, lw=1.6, ms=8, label=f"TR 101 545-4 {lab}")
    for c, (n, rate) in zip((COL[2], "#7a7a74", "#b5a46a"), (("N3008", "1/2 (= ID 14 code)"), ("N4512", "1/3"), ("N2256", "2/3"))):
        d = aff3ct(glob.glob(os.path.join(STD, "aff3ct_refs", f"Turbo_DB_{n}_K1504*.txt"))[0])
        a.semilogy(d[:, 0], d[:, 1], "-", color=c, lw=2, alpha=0.75, label=f"AFF3CT K = 1504, rate {rate}, full curve")
    a.set_title("DVB-RCS2 published PER vs SNR (ideal sync, AWGN)", fontsize=11)
    d = np.array(M2435)
    b.semilogy(d[:, 0], d[:, 1], "o-", color=COL[0], lw=2, ms=7, label="ITU-R M.2435 Fig. 11: 88 info bits, QPSK, turbo 1/4")
    b.set_title("VDE-SAT published PER vs SNR (AWGN)", fontsize=11)
    for ax in (a, b):
        ax.set_xlabel("SNR (Es/N0) [dB]")
        ax.set_ylabel("PER")
        ax.set_ylim(1e-6, 1)
        ax.grid(True, which="both", ls=":", color="#c3c2b7")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1, frameon=False, fontsize=8.5)
    a.set_xlim(-4.5, 4)
    b.set_xlim(-4, 0.5)
    f.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    f.savefig(OUT, dpi=140, bbox_inches="tight")
    print(OUT)


if __name__ == "__main__":
    main()
