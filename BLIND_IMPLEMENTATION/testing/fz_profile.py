"""BLIND_IMPLEMENTATION/testing/: cost profile of a CA-SCL decode in decoding order (F5 of results/expected_f3f5.md, the
offline saving of a frozen-bit abort; pure, no simulation).

The receiver charges a CA-SCL-L decode L/8 MAC["decode"] MACs (blind_vp, flat: 8 N log2 N) and, on the per-core
critical path (small_rx _dec_cost, dcritp), MAC["decode"]/8 ceil(L/Kc) + n_dec lg (lg + 1)/2 (lg = log2 2L: the
bitonic 2L -> L sort at each information bit; the LLR part is paid before the decode and never saved). The flat
decode MACs are spread over the decoding order by the work of the decoder that runs (polar.PolarCode: Fast-SSCL with
rate-0 nodes): per path f and g n/2 each at an internal node of n leaves, n at a rate-0 node (its PM sum), 1 at a
frozen leaf, 2 at an information leaf (both candidates). A decode stopped once the leaves [0, pos) are decided
(the f_pos / f_pos_s fields of the fz_diag dump) saves the rest:

    from fz_profile import saved
    tot, crit = saved("0.15", pos)              # MACs, crit-path MACs saved per stopped CA-SCL-8 decode
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import blind_cfo as bc  # noqa: E402
import blind_vp as vp  # noqa: E402
from polar import PolarCode  # noqa: E402

_P = {}


def profile(rate):
    """Code rate key ("0.15", "1/10", "2/5", "1/2") -> dict(pos (P,) leaf ends of every leaf / rate-0 node in decoding
    order, tree (P,) the share of the decode's work done once [0, pos) is decided, nb (P,) information bits decided,
    n_dec the information bits of a decode)."""
    if rate not in _P:
        fz = PolarCode(bc.N_BITS, bc.CODES[rate], 16).frozen
        out, acc = [], [0.0, 0]

        def walk(lo, hi):
            n = hi - lo
            if n == 1:
                acc[0] += 1 if fz[lo] else 2
                acc[1] += 0 if fz[lo] else 1
                out.append((hi, acc[0], acc[1]))
                return
            if fz[lo:hi].all():
                acc[0] += n
                out.append((hi, acc[0], acc[1]))
                return
            acc[0] += n / 2                                   # f
            walk(lo, lo + n // 2)
            acc[0] += n / 2                                   # g
            walk(lo + n // 2, hi)

        walk(0, bc.N_BITS)
        a = np.array(out, float)
        _P[rate] = dict(pos=np.r_[0, a[:, 0]].astype(int), tree=np.r_[0, a[:, 1] / a[-1, 1]],
                        nb=np.r_[0, a[:, 2]].astype(int), n_dec=int((~fz).sum()))
    return _P[rate]


def share(rate, pos):
    """Share of the decode's work and information bits decided once the leaves [0, pos) are decided (pos array; at a
    leaf / node boundary, else the last boundary before it)."""
    P = profile(rate)
    j = np.searchsorted(P["pos"], np.asarray(pos), side="right") - 1
    return P["tree"][j], P["nb"][j]


def saved(rate, pos, L=8, Kc=32):
    """MACs and per-core critical-path MACs (small_rx dcritp) NOT spent by a CA-SCL-L decode stopped at leaf pos."""
    P = profile(rate)
    tr, nb = share(rate, pos)
    lg = np.log2(2 * L)
    tot = (1 - tr) * L / 8 * vp.MAC["decode"]
    crit = (1 - tr) * vp.MAC["decode"] / 8 * np.ceil(L / Kc) + (P["n_dec"] - nb) * lg * (lg + 1) / 2
    return tot, crit


if __name__ == "__main__":
    for r in ("1/10", "0.15", "2/5", "1/2"):
        P = profile(r)
        F = bc.N_BITS - P["n_dec"]
        print(r, "frozen", F, "info", P["n_dec"], "work share at leaf 512 / 1024 / 1536:",
              np.round(share(r, [512, 1024, 1536])[0], 3))
