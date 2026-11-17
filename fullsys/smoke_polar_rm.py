"""
Cluster smoke of the rate recovery under shortening (fullsys/polar_rm.py; Run:ai job only, NEVER on the local PC or
bhn20): RCS2 ID 14 (A = 1472 + CRC-32 = K 1504, E = 3008, standard rule -> shorten, N = 4096), genie sync (f = 0,
phase 0, full Tx/Rx chain txrx_chain.transmit, RRC roll-off 0.20), QPSK 1504 symbols, CA-SCL-8. Every packet is
decoded three times with the SAME channel LLRs, only the shortened LLRs differ:

    big  : +LLR_BIG (known zero; the implementation)     zero : 0 (as if punctured)     neg : -LLR_BIG (control)

Expect BLER(big) <= BLER(zero) (McNemar on the discordant pairs) and BLER(neg) ~ 1 with no correct accept.
Default Es/N0 0.5 / 1.0 / 1.5 dB brackets BLER ~0.1 (TR 101 545-4 turbo PER 1e-3 at 1.49 dB).

    python fullsys/smoke_polar_rm.py --part smk_prm_a --packets 300 --seed 1 [--snr 0.5 1.0 1.5]

Writes fullsys/results/smoke_polar_rm_<part>.json. Packets pair by (seed, SNR, chunk).
"""

import argparse
import json
import os
import sys
from math import comb

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import txrx_chain  # noqa: E402
from fullsys import polar_rm as rm  # noqa: E402

A, E = 1472, 3008
ROLLOFF = 0.20                     # DVB-RCS2 return link (EN 301 545-2 cl. 7.3.7.1.1)
CHUNK = 50
ARMS = {"big": rm.LLR_BIG, "zero": 0.0, "neg": -rm.LLR_BIG}


def mcnemar(a, b):
    """Discordant counts n10 (a right, b wrong), n01 and the exact two-sided binomial p (p = 1/2)."""
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    n, k = n10 + n01, min(n10, n01)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return dict(n10=n10, n01=n01, p=p)


def run_point(code, snr, packets, seed):
    right = {k: [] for k in ARMS}
    crc = {k: [] for k in ARMS}
    for c in range(0, packets, CHUNK):
        B = min(CHUNK, packets - c)
        rng = np.random.default_rng([seed, int(round(100 * snr)) + 1000, c])
        d = rng.integers(0, 2, (B, A), dtype=np.uint8)
        e = code.encode_rm(d)
        sym = ((1 - 2 * e[:, 0::2].astype(float)) + 1j * (1 - 2 * e[:, 1::2].astype(float))) / np.sqrt(2)
        r = txrx_chain.transmit(sym, np.zeros(B), np.zeros(B), snr, rng, beta=ROLLOFF)
        g = np.sum(r * np.conj(sym), 1, keepdims=True) / sym.shape[1]   # genie gain (MF loss, no phase)
        z = r / g
        s2 = np.mean(np.abs(z - sym) ** 2, 1, keepdims=True)              # genie noise variance per symbol
        llr = np.empty((B, E))
        llr[:, 0::2] = 2 * np.sqrt(2) * z.real / s2                       # bit 0 -> +1/sqrt2
        llr[:, 1::2] = 2 * np.sqrt(2) * z.imag / s2
        lx = code.rate_recover(llr)
        short = code.J[E:]
        for k, val in ARMS.items():
            lk = lx.copy()
            lk[:, short] = val
            dh, ok, _ = code.code.decode(lk, return_info=True)
            crc[k].append(ok)
            right[k].append(ok & np.all(dh == d, axis=1))
    right = {k: np.concatenate(v) for k, v in right.items()}
    crc = {k: np.concatenate(v) for k, v in crc.items()}
    return dict(snr=snr, packets=packets,
                bler={k: float(1 - v.mean()) for k, v in right.items()},
                crc_pass={k: int(v.sum()) for k, v in crc.items()},
                false_accept={k: int((crc[k] & ~right[k]).sum()) for k in ARMS},
                mcnemar_big_zero=mcnemar(right["big"], right["zero"]),
                mcnemar_big_neg=mcnemar(right["big"], right["neg"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True)
    ap.add_argument("--packets", type=int, default=300)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--snr", type=float, nargs="+", default=[0.5, 1.0, 1.5])   # Es/N0 dB
    a = ap.parse_args()
    code = rm.RMPolarCode(A, E)
    assert code.mode == "shorten" and code.N == 4096 and code.K == 1504
    out = dict(format="RCS2 ID 14", A=A, K=code.K, E=E, N=code.N, mode=code.mode, crc=32, L=8, seed=a.seed,
               points=[])
    path = os.path.join(_ROOT, "fullsys", "results", f"smoke_polar_rm_{a.part}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for snr in a.snr:
        pt = run_point(code, snr, a.packets, a.seed)
        out["points"].append(pt)
        print(json.dumps(pt), flush=True)
        with open(path, "w") as f:                               # rewritten after every point (partial results)
            json.dump(out, f, indent=1)
    print("DONE", path)


if __name__ == "__main__":
    main()
