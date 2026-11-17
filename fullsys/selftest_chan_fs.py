"""
Noiseless checks of the blind format's channel interleaver (fullsys/blind_fmt chan), no BLER (< 1 min, cluster only:
it runs receiver code). Per QPSK format (id13 / id3 / id14p, GA and PW designs), with and without chan:
    tx == rx map   e = encode_rm(d)[:, chan] -> modulate == F.modulate_virtual(e); inside the context the re-encoding
                   code.encode(d)[:, bc.INTERLEAVER] == e; bc.llrs(s, f 0, phase 0) signs == e on F.pos, 0 on the
                   punctured x; reencode_rho(d) ~ 1
    pi/2 branch    the list-1 metric (bf.fast_sc, the receiver's) of the pi/2-rotated packet vs the right phase:
                   no chan = the tie (metric(pi/2) == metric(0) = the root cause of the 37 % floor), chan = metric(pi/2)
                   >> metric(0) (asserted); CA-SCL at pi/2 must not return the sent data

    BLIND_STUDY=small_cfo python fullsys/selftest_chan_fs.py
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import run_polar_genie as pg          # noqa: E402
from fullsys.blind_fmt import BlindFormat           # noqa: E402
import blind_cfo as bc                              # noqa: E402
import blind_fast as bf                             # noqa: E402


def check(fmt, design, chan, B=4, sigma2=0.05):
    f = pg.FMTS[fmt]
    F = BlindFormat(fmt, f["A"], f["E"], f["mod"], mode=f["mode"] if f["force"] else None, crc=32, L=pg.L_LIST,
                    chan_intlv=chan, design=design, design_snr=pg.DESIGN_SNR[fmt] if design == "ga" else None)
    d = np.random.default_rng(7).integers(0, 2, (B, F.A)).astype(np.uint8)
    e = F.rmc.encode_rm(d)[:, F.chan]
    s = pg.modulate(e, fmt)
    assert np.allclose(F.virtual(s), F.modulate_virtual(e)), "tx map != the receiver's virtual map"
    z = np.zeros(B)
    with F:
        assert np.array_equal(F.code.encode(d)[:, bc.INTERLEAVER], e), "re-encoding map != tx"
        llr = bc.llrs(s, z, z, sigma2)
        assert np.array_equal((llr[:, F.pos] < 0).astype(np.uint8), e), "LLR signs != the sent bits"
        sent = np.zeros(F.N, bool)
        sent[F.pos] = True
        assert np.all(llr[:, ~sent] == F.base[~sent]), "rate recovery of the unsent x"
        rho = bf.reencode_rho(F.code, s, d, z)
        assert np.all(rho > 0.999), rho
        fs = bf.fast_sc(F.A)
        m0 = fs.metric(llr)
        l90 = bc.llrs(s * np.exp(1j * np.pi / 2), z, z, sigma2)
        m90 = fs.metric(l90)
        dh, ok, _ = F.code.decode(l90, return_info=True)
        right90 = ok & (dh == d).all(1)
    tie = bool(np.allclose(m90, m0, rtol=1e-4, atol=1e-2))
    print(f"  {fmt:5s} {design} chan {str(F.chan_intlv):5s} N {F.N} E {F.E}: tx == rx ok, rho min {rho.min():.6f} | "
          f"metric 0 {np.round(m0, 2).tolist()} pi/2 {np.round(m90, 1).tolist()} tie {tie} | CA-SCL at pi/2: CRC pass "
          f"{int(ok.sum())}/{B}, = sent data {int(right90.sum())}", flush=True)
    if chan:
        assert not tie and np.all(m90 > m0 + 100), "chan on: the pi/2 branch still ties"
        assert not right90.any()
    return tie


def main():
    assert bc.STUDY == "small_cfo", "run with BLIND_STUDY=small_cfo"
    t0 = time.time()
    ties = {}
    for fmt in ("id13", "id3", "id14p"):
        for design in ("ga", "pw"):
            for chan in (False, True):
                ties[(fmt, design, chan)] = check(fmt, design, chan)
    nt = [k for k, v in ties.items() if not k[2] and not v]
    print(("  note: no tie WITHOUT chan for " + str(nt)) if nt else "  without chan: every format ties (root cause seen)")
    print(f"SELFTEST CHAN OK ({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
