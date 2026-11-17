"""
VDE-SAT / VDE (ITU-R M.2092-2, 02/2026) burst chain, bit-exact where the standard defines it, for the full-system
competitor study (BLIND_IMPLEMENTATION/testing/results/lit_vde_fec.md, lit_vdesat_fullsystem.md).

Tx per burst (A2-1.2.3.5, A2-1.2.5, A2-1.2.6, A5-2.13, A5-2.5.2, A5-2.10):
    payload (+ zero padding) -> CRC-32 (0x04C11DB7, init 0xFFFFFFFF, MSB first, no reflection / final XOR)
    -> turbo encode per FEC sub-block (turbo_vde.py, Table 4 k1 k2 primes, Table 5 / 6 puncturing and tail)
    -> [+ zero padding per sub-block, Table 10 "Padding + FEC tail"] -> scrambler 1 + x^-14 + x^-15, seed
    100101010000000 (Fig. 9), re-initialised per burst -> DL block channel interleaver (Table 63, IB blocks)
    -> burst stuffing bits -> map (BPSK 1 -> +1 Fig. 10; pi/4-QPSK absolute, Fig. 11; QPSK = its even set)
    -> insert syncwords (Table 1, every d_s symbols), Link ID (TER / ASM), single pilots (every d_p, A5-2.10)
    -> DS spreading of every burst bit by 8 Gold chips (Links 25, 32; Table 62 SS0 / SS1, periodic over 2047 chips)
Rx (ideal sync): matched-filter samples -> despread -> per-bit LLR -> strip stuffing -> deinterleave -> descramble
    -> drop padding -> turbo decode (CRC early stop) -> CRC.

Es/N0 is per data-modulation symbol (despread symbol for the CDMA links: Table 11 C/(N0+I0) - 10 log10(4200) =
-4.63 dB for Link 32), Eb/N0 charges every burst symbol (syncwords, pilots, Link ID) to the payload bits.
LLR convention as polar.py: LLR = log P(bit = 0) / P(bit = 1).
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:                                       # `fullsys` importable when run as a script
    sys.path.insert(0, _ROOT)
from fullsys.turbo_vde import TurboVDE, DEFAULT_PRIMES, macs, crit, srandom_interleaver, qpp_interleaver  # noqa: E402
from fullsys import costmodel  # noqa: E402

ASSUMPTIONS = [
    "A1 Table 63 (DL channel interleaver) read from the PDF layout (Rec. p. 122, PDF p. 124): Link 32 M 27 N 47 "
    "Ar 13 Br 17 Ac 23 Bc 13; = lit_vde_fec.md 0.3, NOT lit_vdesat_fullsystem.md 1.5 (its Ac / Bc are wrong).",
    "A2 Channel interleaver law applied literally: write rows (bit (m, n) = (m-1) N + n-1), row step new[m, n] = "
    "old[pr(m, n), n] with Cr(n) depending on the column, then column step new2[m, n] = new[m, pc(n, m)] with m the row "
    "index after the row step, read by columns. No test vector exists; AWGN PER does not depend on it.",
    "A3 CRC: one CRC-32 per burst, at the end of the last FEC sub-block, over all sub-blocks' payload (A2-1.2.5 'over "
    "all fragments ... appended to the last segment', A4-4.6 'The CRC is always at the end of the packet'). "
    "crc_mode='block' (one CRC-32 per sub-block) is kept as the alternative. Single-block links (5, 11, 17, 32, 33) "
    "are not affected. Payload = k - 32 per burst (Link 32: 280 bits).",
    "A4 Multi-block bursts (26, 34): sub-blocks concatenated in order, each followed by its zero padding (Link 26: 3 "
    "bits after its 18 tail bits), ONE scrambler run over all channel bits (re-initialised per packet), then the "
    "channel interleaver in IB consecutive blocks of L, then the burst stuffing bits (zeros, not scrambled) at the end.",
    "A5 DS spreading (Link 32): burst bit i (syncword, pilot and data bits alike, counted from the first syncword bit) "
    "is XORed with Gold chips (8 i .. 8 i + 7) mod 2047 of SS0 (MSB of each byte first); chip 1 -> +1, 0 -> -1 "
    "('ordinary BPSK', Fig. 10). SS0 by default (SS1 = the second satellite).",
    "A6 Pilot grid: pilots at Ns + floor((dp - 1)/2) + i dp after each syncword start, up to (<=) the next syncword "
    "start (or the burst end) - floor((1 + dp)/2), i.e. A5-2.10's 'last pilot at d_s - (1 + d_p)/2' read as an upper "
    "bound. Reproduces the A5-2.10 Link 26 example (40, 67, ..., 2254; 31 symbols after the last pilot) and the pilot "
    "totals 180 / 2940 / 480 of Tables 10-11. For Link 32 the last pilot of a segment is at 523 (527 is off the "
    "d_p = 8 grid; an exact 527 would break the 180 total), so 7 data symbols precede each repeated syncword.",
    "A7 Pilot value: bit 1 (BPSK / CDMA: spread like data); pi/4-QPSK: dibit 11 with the alternating map ((1+j)/sqrt2 "
    "at even, 1 at odd positions). pi/4-QPSK symbol index runs over the whole burst from the first syncword symbol.",
    "A8 Link 32 burst = 4 syncwords x 48 at 0, 531, 1062, 1593 (the last one ends the burst) + 3 x 60 pilots + 1269 "
    "data = 1641 symbols (Table 11 'burst symbol duration'; the 1645 'symbols/burst' adds the 14 + 14 ramp chips).",
    "A9 Eb/N0 helper: info bits = payload (k - 32 per burst), every burst symbol charged: Link 32 at Es/N0 -4.5 dB -> "
    "-4.5 + 10 log10(1641/280) = 3.18 dB (lit table); with 312 (CRC counted as info) it would be 2.71 dB.",
    "A10 Ramps (14/14 chips, modulation 'not specified') and guard time are not transmitted; the waveform is "
    "the 1641-symbol burst through RRC (roll-off 0.25 SAT, 0.3 TER, 0.35 ASM per Tables 7-11).",
    "A11 Pseudo-link 'M2435' (Report M.2435 4.3.1): k = 88 info bits, no CRC (frame error by genie), plain QPSK "
    "(A5-2.4 Gray quadrants, = the even pi/4-QPSK set), turbo rate 1/4 (punct 2 / tail 2 of the DVB-SH 1/4 code: "
    "XXY0Y1 tail, 24 tail bits), interleaver: the M.2092 CCSDS law with 2 x 44 and the default primes, since the "
    "DVB-SH / 3GPP2 interleaver is defined for other lengths only (L = 1146 / 12282) and its tables are not in the "
    "specs we hold; payload-only frame (no syncword / pilots). Bracketing options (M.2435 does not state its "
    "interleaver): interleaver='srandom' (S = floor(sqrt(k/2)) = 6 at k 88, seeded), 'qpp' (LTE QPP, default "
    "f1 5 f2 22 = TS 36.212 Table 5.1.3-3 row K 88 as recalled, no local copy of the table), 'random' (seeded).",
    "A12 Links 33 (BPSK) and 26 / 34 (pi/4-QPSK) built from Tables 4, 10, 11, 63 with the same rules; Link 34 has no "
    "tail (decoder: unterminated trellis). Link 25 (SF 8, rate 1/2) and Links 27-31 not built.",
    "A13 Ideal sync: known timing, CFO = 0, phase 0, unit gain, noise variance from the nominal Es/N0 (genie). The "
    "data-aided synchroniser (sync='da') is the next step and raises NotImplementedError.",
]

# ---- Table 1 syncwords; Table 2 Reed-Muller (32, 6) generator + scrambling word (Link ID, D0 = MSB) ----
SYNC = {
    "TER27": "111111001101010000011001010",                      # 1 + Barker13 + inverted Barker13 (ASM / VDE-TER)
    "SAT27": "010001010010010000000110011",                      # ASM-SAT / VDE-SAT 27
    "SAT48": "000100011110011011000001010111011010110111101000",  # VDE-SAT 48
}
RM_G = ["10000010111010011110100110010110", "01000001110101011101010101010101",
        "00100011101100110011001100110011", "00010011000011111000111100001111",
        "00001000011111110000000011111111", "00000100000000000111111111111111"]
RM_SCR = "11000010111000101000111001001111"

GOLD_HEX = {                                                     # Table 62 (256 bytes; only 7 MSBs of the last byte used)
    "SS0": ("04614F298EA36313B481443D35C9BCDF0605D33EA313DEDAC937F6C02D5A81B7ED4B4377310DDF991C49E17131C11230"
            "589E809EACE783ABD89AAD245689BBC237EADB49F84D80B92CE3F1981C8606454C3125686A3F1F9B62CC2D424BE19F2C"
            "0FF0844F313CB44005B6FDD2D4E863A95662B60880DADD07AA3776C78A8181BD953179E40DEB928CA4D1A6FF4547C7F9"
            "09D1D22C4602B1B5B2836B57D0BFC34CD62A260AEBC1D858490AFBCFDA62FD4160FDF70FA28EA490B0AD37FD2EE42B75"
            "E64663ABFA55243D93CF4E72CE0238B777959730867E242E8081C29726322A7190CB367917A5D4493604215F1E54A288"
            "D662ADE04761A789ED8134881AD0BE5A"),
    "SS1": ("410B5766A0D19436C2948C6010FF81065184E380EBFEB5C2265DAEA71222D29418CF31C03C6AC0F547EF46F602BEC222"
            "53DA4A628D737B48B541FBE5EE62D31B407FE372E2A3AA691EFCBDD7B2A4D3757229EA163ADD72E0702705B32D7E0311"
            "968F14752B72DABAA7B3BFDB916217DDE2AE49E88CDD5E3654F7CE8CA6726632A34C88A2867F2A47D80054387E3D15CA"
            "5615C8A250CB0C5CFB0E9C129AB384E7F6DE42B4237C9155EE6DA48B90CEFEC0D0139DF7819B4CD99D1E582738ADC6BE"
            "BA8399E9932CB7C6117E40D44991034DF584DDBC91F71192E938295FBB6F2F53A59733FB66D341D149345F6FC020566C"
            "388805E147C1E3A37D9B3ACEF1781F1E"),
}

SCR_SEED = "100101010000000"                                     # Fig. 9, register cells 1..15
CRC32 = dict(nbits=32, poly=0x04C11DB7, init=0xFFFFFFFF)

# ---- link table (Tables 4, 7, 8, 10, 11, 63). ileave = (M, N, Ar, Br, Ac, Bc, IB) ----
LINKS = {
    5: dict(name="ASM-MCS-1.16-5", k=288, nblk=1, k1=2, k2=144, primes=(47, 17, 233, 127, 239, 139, 199, 163),
            punct="8", tail="8b", crc=32, mod="pi4qpsk", sf=1, sync="TER27", n_sync=1, ds=None, dp=None,
            linkid=True, ileave=None, pad=0, stuff=0, n_sym=240, beta=0.35, esn0_ref=5.3),
    11: dict(name="TER-MCS-1.25", k=432, nblk=1, k1=2, k2=216, primes=(127, 191, 241, 5, 83, 109, 107, 179),
             punct="6", tail="6a", crc=32, mod="pi4qpsk", sf=1, sync="TER27", n_sync=1, ds=None, dp=None,
             linkid=True, ileave=None, pad=0, stuff=0, n_sym=480, beta=0.3, esn0_ref=1.0),
    17: dict(name="TER-MCS-1.100", k=1872, nblk=1, k1=6, k2=312, primes=(211, 61, 227, 239, 181, 79, 73, 193),
             punct="6", tail="6a", crc=32, mod="pi4qpsk", sf=1, sync="TER27", n_sync=1, ds=None, dp=None,
             linkid=True, ileave=None, pad=0, stuff=0, n_sym=1920, beta=0.3, esn0_ref=1.0),
    26: dict(name="SAT-MCS-1.50-1", k=5456, nblk=7, k1=16, k2=341, primes=(37, 41, 43, 47, 53, 59, 61, 67),
             punct="2", tail="2a", crc=32, mod="pi4qpsk", sf=1, sync="SAT27", n_sync=35, ds=2268, dp=27,
             linkid=False, ileave=(257, 119, 127, 107, 59, 41, 5), pad=3, stuff=1, n_sym=80343, beta=0.25,
             esn0_ref=-2.4),
    32: dict(name="SAT-MCS-0.50-2", k=312, nblk=1, k1=2, k2=156, primes=(37, 79, 29, 139, 151, 97, 181, 157),
             punct="2", tail="2e", crc=32, mod="bpsk", sf=8, sync="SAT48", n_sync=4, ds=531, dp=8,
             linkid=False, ileave=(27, 47, 13, 17, 23, 13, 1), pad=0, stuff=0, n_sym=1641, beta=0.25, esn0_ref=-4.5),
    33: dict(name="SAT-MCS-0.50-3", k=4280, nblk=1, k1=8, k2=535, primes=(59, 37, 157, 167, 239, 83, 163, 29),
             punct="4", tail="4a", crc=32, mod="bpsk", sf=1, sync="SAT48", n_sync=6, ds=2619, dp=None,
             linkid=False, ileave=(857, 15, 421, 367, 7, 3, 1), pad=0, stuff=0, n_sym=13143, beta=0.25, esn0_ref=-3.6),
    34: dict(name="SAT-MCS-1.50-2", k=4160, nblk=2, k1=16, k2=260, primes=(163, 157, 149, 137, 197, 47, 241, 251),
             punct="4", tail=None, crc=32, mod="pi4qpsk", sf=1, sync="SAT27", n_sync=6, ds=2619, dp=27,
             linkid=False, ileave=(128, 195, 51, 89, 97, 19, 1), pad=0, stuff=0, n_sym=13122, beta=0.25,
             esn0_ref=-0.6),
    "M2435": dict(name="M.2435 4.3.1 88-bit QPSK 1/4", k=88, nblk=1, k1=2, k2=44, primes=DEFAULT_PRIMES,
                  punct="2", tail="2", crc=None, mod="qpsk", sf=1, sync=None, n_sync=0, ds=None, dp=None,
                  linkid=False, ileave=None, pad=0, stuff=0, n_sym=188, beta=0.25, esn0_ref=-1.5),
}

REF = {                                                          # validation targets (AWGN, Es/N0 per data symbol)
    "M2435_PER": dict(link="M2435", esn0_db=-1.5, per=1e-2,
                      src="ITU-R M.2435 4.3.1 Fig. 11 (PDF p. 25): AWGN, 88 info bits, QPSK, turbo 1/4 per ETSI EN 302 583 "
                          "(DVB-SH), Es/N0 after de-spreading; 'conservative design point'; interleaver, decoder and "
                          "iterations not stated",
                      pass_rule=dict(algo="logmap", esn0_db=-1.5, tol_db=0.3, per=1e-2, slope_db_per_decade=0.9),
                      fig_esn0=[-3.29, -3.04, -2.79, -2.54, -2.29, -2.04, -1.79, -1.54, -1.29, -1.04, -0.79, -0.54, -0.29],
                      fig_per=[0.5, 0.39, 0.25, 0.17, 0.11, 0.048, 0.028, 0.012, 0.0047, 0.0022, 0.00105, 0.00036, 0.00018],
                      fig_note="read off the figure image by eye (+-10 % in PER, +-0.02 dB); slope there ~0.75 dB "
                               "per decade between PER 1e-1 and 1e-3"),
    "M2435_BER": dict(link="M2435", esn0_db=-0.3, ber=1e-5, src="ITU-R M.2435 4.3.1 Fig. 12 (PDF p. 26)",
                      fig_esn0=[-3.29, -3.04, -2.79, -2.54, -2.29, -2.04, -1.79, -1.54, -1.29, -1.04, -0.79, -0.54, -0.29],
                      fig_ber=[0.08, 0.063, 0.04, 0.024, 0.015, 0.0058, 0.0037, 0.0016, 0.00052, 0.00022, 0.00011,
                               3.0e-5, 1.1e-5]),
    "Kim_L11": dict(link=11, esn0_db=2.1, per=1e-2, algo="logmap", iters=6,
                    src="Kim, J. KICS 50(3) 2025: Link 11, 432 bits, 1/2, pi/4-QPSK; axis Es/N0 per symbol"),
    "Kim_L17": dict(link=17, esn0_db=1.5, per=1e-2, algo="logmap", iters=6,
                    src="Kim 2025: Link 17, 1872 bits, 1/2, pi/4-QPSK; axis Es/N0 per symbol"),
    "M2092_thresholds": {5: 5.3, 11: 1.0, 17: 1.0, 26: -2.4, 32: -4.5, 33: -3.6, 34: -0.6},   # Tables 7-11, PER unstated
}


def bits_of(s):
    return np.array([int(c) for c in s], np.int8)


# ---- CRC (A2-1.2.5) ----
def _crc_step0(reg, nbits, poly):
    fb = (reg >> (nbits - 1)) & 1
    reg = (reg << 1) & ((1 << nbits) - 1)
    return reg ^ poly if fb else reg


def crc_register(bits, nbits=32, poly=0x04C11DB7, init=0xFFFFFFFF):
    """LFSR register after the bits (MSB-first, non-reflected): the CRC to append, or 0 over data + CRC."""
    reg, mask = init, (1 << nbits) - 1
    for b in bits:
        fb = ((reg >> (nbits - 1)) & 1) ^ int(b)
        reg = (reg << 1) & mask
        if fb:
            reg ^= poly
    return reg


def _reg_bits(reg, nbits):
    return np.array([(reg >> (nbits - 1 - i)) & 1 for i in range(nbits)], np.int8)


class CRC:
    """Vectorised affine CRC: register(bits) = bits @ M + c0 (mod 2), MSB first. n = number of input bits."""

    def __init__(self, n, nbits=32, poly=0x04C11DB7, init=0xFFFFFFFF):
        self.n, self.nbits = n, nbits
        cols = np.empty((n, nbits), np.int8)
        reg = poly                                              # a single 1 as the last bit (zero init)
        for j in range(n - 1, -1, -1):
            cols[j] = _reg_bits(reg, nbits)
            reg = _crc_step0(reg, nbits, poly)
        self.M = cols.astype(np.int32)
        r0 = init
        for _ in range(n):
            r0 = _crc_step0(r0, nbits, poly)
        self.c0 = _reg_bits(r0, nbits).astype(np.int32)

    def register(self, bits):
        return ((np.asarray(bits, np.int32) @ self.M + self.c0) & 1).astype(np.int8)


def scrambler_seq(n, seed=SCR_SEED):
    """A2-1.2.6 / Fig. 9: 1 + x^-14 + x^-15, cells 1..15 = seed; out = in XOR (cell 14 XOR cell 15)."""
    r = [int(c) for c in seed]
    out = np.empty(n, np.int8)
    for i in range(n):
        fb = r[13] ^ r[14]
        out[i] = fb
        r = [fb] + r[:14]
    return out


def chan_interleaver(M, N, Ar, Br, Ac, Bc):
    """A5-2.13: perm (M N,) 0-based, out = in[perm] (rows written, row then column permutation, read by columns)."""
    idx = np.arange(M * N).reshape(M, N)
    m = np.arange(1, M + 1)[:, None]
    n = np.arange(1, N + 1)[None, :]
    pr = 1 + (Ar * m + (Br * n - 1) % M) % M                    # (M, N): row pr(m) -> row m, per column n
    R = idx[pr - 1, np.broadcast_to(n - 1, (M, N))]
    pc = 1 + (Ac * n + (Bc * m - 1) % N) % N                    # (M, N): column pc(n) -> column n, per row m
    C = R[np.broadcast_to(m - 1, (M, N)), pc - 1]
    return C.T.ravel()


def gold_chips(name="SS0"):
    """Table 62 sequence as 2047 chips (MSB of each byte first; the last byte's LSB dropped)."""
    by = bytes.fromhex(GOLD_HEX[name])
    return np.unpackbits(np.frombuffer(by, np.uint8))[:2047].astype(np.int8)


def linkid_bits(lid):
    """(32, 6) Reed-Muller code word of Link ID lid (D0 = MSB, Table 2) XOR the scrambling word (Table 3)."""
    D = np.array([(lid >> (5 - i)) & 1 for i in range(6)])
    G = np.array([[int(c) for c in r] for r in RM_G])
    return ((D @ G) % 2 ^ bits_of(RM_SCR)).astype(np.int8)


# ---- mapping (A2-1.2.9, Figs 10, 11) ----
ROT = np.exp(-1j * np.pi / 4)                                   # odd pi/4-QPSK index: even point rotated by -45 deg


def map_dibits(b0, b1, idx, mod):
    """Gray: 11 -> (+,+), 01 -> (-,+), 00 -> (-,-), 10 -> (+,-) at even idx; pi/4-QPSK rotates odd idx by -45 deg."""
    s = ((2 * b0 - 1) + 1j * (2 * b1 - 1)) / np.sqrt(2)
    if mod == "pi4qpsk":
        s = np.where(np.asarray(idx) % 2 == 1, s * ROT, s)
    return s


def demap_dibits(y, idx, N0, mod):
    """y (B, n) unit-gain symbols, complex noise variance N0 -> LLR (B, 2 n) [b0, b1] per symbol (log P0 / P1)."""
    if mod == "pi4qpsk":
        y = np.where(np.asarray(idx) % 2 == 1, y / ROT, y)
    c = 2 * np.sqrt(2) / N0
    out = np.empty(y.shape[:-1] + (2 * y.shape[-1],))
    out[..., 0::2] = -c * y.real
    out[..., 1::2] = -c * y.imag
    return out


class VDELink:
    """One VDE burst format (LINKS entry) with its encoder, layout, interleavers and ideal-sync receiver."""

    def __init__(self, lid, interleaver="ccsds", gold="SS0", crc_mode="burst", beta=None, perm_seed=0,
                 s_spread=None, qpp=(5, 22)):
        p = dict(LINKS[lid])
        self.lid, self.p = lid, p
        self.mod, self.sf, self.beta = p["mod"], p["sf"], (p["beta"] if beta is None else beta)
        self.k, self.nblk = p["k"], p["nblk"]
        perm = None
        if interleaver == "random":                             # sensitivity options (not the VDE interleaver)
            perm = np.random.default_rng(perm_seed).permutation(self.k)
        elif interleaver == "srandom":
            perm = srandom_interleaver(self.k, s_spread, perm_seed)
        elif interleaver == "qpp":
            perm = qpp_interleaver(self.k, *qpp)
        else:
            assert interleaver == "ccsds", interleaver
        self.code = TurboVDE(self.k, p["k1"], p["k2"], p["primes"], p["punct"], p["tail"], perm=perm)
        self.crc_mode = crc_mode if p["crc"] else None
        if self.crc_mode == "burst":
            self.kpay = self.nblk * self.k - p["crc"]
            self.crc = CRC(self.kpay, **CRC32)
            self.crc_chk = CRC(self.nblk * self.k, **CRC32)
        elif self.crc_mode == "block":
            self.kpay = self.nblk * (self.k - p["crc"])
            self.crc = CRC(self.k - p["crc"], **CRC32)
            self.crc_chk = CRC(self.k, **CRC32)
        else:
            self.kpay = self.nblk * self.k
        self.n_blk = self.code.n + p["pad"]                     # channel bits per sub-block (coded + tail + pad)
        self.n_chan = self.nblk * self.n_blk
        self.scr = scrambler_seq(self.n_chan)
        if p["ileave"] is not None:
            M, N, Ar, Br, Ac, Bc, IB = p["ileave"]
            assert M * N * IB == self.n_chan, f"Table 63: {M} x {N} x {IB} != {self.n_chan} channel bits"
            one = chan_interleaver(M, N, Ar, Br, Ac, Bc)
            self.ileave = np.concatenate([one + b * M * N for b in range(IB)])
        else:
            self.ileave = np.arange(self.n_chan)
        self.ideint = np.argsort(self.ileave)
        self.bps = 1 if self.mod == "bpsk" else 2
        self.n_data_bits = self.n_chan + p["stuff"]
        assert self.n_data_bits % self.bps == 0
        self.n_data_sym = self.n_data_bits // self.bps
        self._layout()
        if self.sf > 1:
            g = gold_chips(gold)
            ci = (np.arange(self.n_sym * self.sf)) % 2047
            self.chips = g[ci].reshape(self.n_sym, self.sf)     # chip bits per burst symbol (bit)
            self.csign = (1 - 2 * self.chips).astype(float)     # chip = (2 b - 1) (1 - 2 g)
        self.n_el = self.n_sym * self.sf                        # transmitted elements (chips or symbols)

    # ---- burst layout (A5-2.10) ----
    def _layout(self):
        p = self.p
        n = p["n_sym"]
        kind = np.zeros(n, np.int8)                             # 0 data, 1 syncword, 2 pilot, 3 Link ID
        sw = bits_of(SYNC[p["sync"]]) if p["sync"] else np.zeros(0, np.int8)
        Ns = len(sw)
        starts = [j * p["ds"] for j in range(p["n_sync"])] if p["ds"] else ([0] if p["n_sync"] else [])
        swbit = np.zeros(n, np.int8)
        for s0 in starts:
            kind[s0:s0 + Ns], swbit[s0:s0 + Ns] = 1, sw
        if p["linkid"]:
            kind[Ns:Ns + 16] = 3
        if p["dp"]:
            dp = p["dp"]
            for j, s0 in enumerate(starts):
                end = starts[j + 1] if j + 1 < len(starts) else n
                pos = np.arange(s0 + Ns + (dp - 1) // 2, end - (1 + dp) // 2 + 1, dp)   # last <= end - (1 + dp)/2
                kind[pos] = 2
        self.kind, self.swbit = kind, swbit
        self.n_sym = n
        self.data_pos = np.flatnonzero(kind == 0)
        self.pilot_pos = np.flatnonzero(kind == 2)
        self.sync_pos = np.flatnonzero(kind == 1)
        assert len(self.data_pos) == self.n_data_sym, \
            f"Link {self.lid}: {len(self.data_pos)} data symbols in the layout, {self.n_data_sym} needed"

    # ---- Tx ----
    def encode_bits(self, payload):
        """payload (B, kpay) -> dict(info (B, nblk, k), coded (B, nblk, n), chan (B, n_data_bits))."""
        payload = np.asarray(payload, np.int8)
        B = payload.shape[0]
        k, nb = self.k, self.nblk
        if self.crc_mode == "burst":
            info = np.concatenate([payload, self.crc.register(payload)], 1).reshape(B, nb, k)
        elif self.crc_mode == "block":
            pb = payload.reshape(B * nb, -1)
            info = np.concatenate([pb, self.crc.register(pb)], 1).reshape(B, nb, k)
        else:
            info = payload.reshape(B, nb, k)
        coded = self.code.encode(info.reshape(B * nb, k)).reshape(B, nb, -1)
        blk = np.concatenate([coded, np.zeros((B, nb, self.p["pad"]), np.int8)], 2).reshape(B, -1)
        scr = blk ^ self.scr[None]
        chan = np.concatenate([scr[:, self.ileave], np.zeros((B, self.p["stuff"]), np.int8)], 1)
        return dict(info=info, coded=coded, scrambled=scr, chan=chan)

    def burst_bits(self, chan):
        """Data bits (B, n_data_bits) -> burst symbols (B, n_sym) complex (or the burst bits for CDMA)."""
        B = chan.shape[0]
        idx = np.arange(self.n_sym)
        if self.mod == "bpsk":
            bits = np.zeros((B, self.n_sym), np.int8)
            bits[:, self.sync_pos] = self.swbit[self.sync_pos]
            bits[:, self.pilot_pos] = 1
            bits[:, self.data_pos] = chan
            return bits
        b0 = np.zeros((B, self.n_sym), np.int8)
        b1 = np.zeros((B, self.n_sym), np.int8)
        b0[:, self.sync_pos] = b1[:, self.sync_pos] = self.swbit[self.sync_pos]   # 1 -> 11, 0 -> 00
        b0[:, self.pilot_pos] = b1[:, self.pilot_pos] = 1
        if self.p["linkid"]:
            lb = linkid_bits(self.lid)
            pos = np.flatnonzero(self.kind == 3)
            b0[:, pos], b1[:, pos] = lb[0::2], lb[1::2]
        b0[:, self.data_pos], b1[:, self.data_pos] = chan[:, 0::2], chan[:, 1::2]
        return map_dibits(b0, b1, idx[None], self.mod)

    def tx(self, payload):
        """payload (B, kpay) -> (elements (B, n_el) complex unit energy: chips for CDMA, else symbols; stages)."""
        st = self.encode_bits(payload)
        x = self.burst_bits(st["chan"])
        if self.mod == "bpsk":
            if self.sf > 1:
                x = ((2 * x[:, :, None] - 1) * self.csign[None]).reshape(len(x), -1)
            else:
                x = 2.0 * x - 1
            x = x.astype(complex)
        return x, st

    # ---- Rx ----
    def despread(self, r):
        """(B, n_el) unit-gain chips -> (B, n_sym) symbols (mean over SF: amplitude 1, noise variance / SF)."""
        if self.sf == 1:
            return r
        return np.einsum("bnc,nc->bn", r.reshape(len(r), self.n_sym, self.sf), self.csign) / self.sf

    def data_llr(self, y, N0):
        """Burst symbols y (B, n_sym), unit gain, complex noise var N0 per symbol -> channel-bit LLRs (B, n_chan)."""
        yd = y[:, self.data_pos]
        if self.mod == "bpsk":
            llr = -4.0 * yd.real / N0
        else:
            llr = demap_dibits(yd, self.data_pos[None], N0, self.mod)
        llr = llr[:, :self.n_chan]                              # drop the burst stuffing bits
        llr = llr[:, self.ideint]                               # channel deinterleaver
        return llr * (1 - 2 * self.scr[None].astype(float))     # descramble: a 1 flips the bit

    def rx(self, r, N0_el, sync="ideal", iters=8, algo="maxlog", scale=None, early=True):
        """
        r (B, n_el) matched-filter samples at unit gain (ideal timing), N0_el complex noise variance per element.
        Returns dict(payload (B, kpay), crc_ok (B,), iters (B, nblk), ops (B,)).
        """
        if sync == "da":
            raise NotImplementedError("data-aided synchroniser (CFO from syncwords + pilots): next step")
        assert sync == "ideal"
        y = self.despread(r)
        return self.decode_llr(self.data_llr(y, N0_el / self.sf), iters, algo, scale, early)

    def decode_llr(self, llr, iters=8, algo="maxlog", scale=None, early=True):
        B = llr.shape[0]
        nb, k = self.nblk, self.k
        L = llr.reshape(B, nb, self.n_blk)[:, :, :self.code.n].reshape(B * nb, -1)
        stop = None
        if early and self.crc_mode == "burst":
            stop = lambda bits, rows: np.repeat(~self.crc_chk.register(bits.reshape(-1, nb * k)).any(1), nb)
        elif early and self.crc_mode == "block":
            stop = lambda bits, rows: ~self.crc_chk.register(bits).any(1)
        bits, used, _ = self.code.decode(L, iters, algo, scale, stop)
        info = bits.reshape(B, nb * k)
        if self.crc_mode == "burst":
            ok = ~self.crc_chk.register(info).any(1)
            pay = info[:, :self.kpay]
        elif self.crc_mode == "block":
            ok = ~self.crc_chk.register(bits).any(1).reshape(B, nb).any(1)
            pay = bits.reshape(B, nb, k)[:, :, :k - self.p["crc"]].reshape(B, -1)
        else:
            ok = np.ones(B, bool)
            pay = info
        used = used.reshape(B, nb)
        ts = 3 if self.code.terminated else 0
        es = stop is not None
        return dict(payload=pay, crc_ok=ok, iters=used, ops=macs(k, used, algo, es, ts).sum(1),
                    ops_crit=crit(k, used, algo, es, ts).sum(1))           # sub-blocks decoded one after another

    # ---- bookkeeping ----
    def ebn0_db(self, esn0_db, info="payload"):
        """Eb/N0 per info bit charging every burst symbol: Es/N0 + 10 log10(n_sym / bits), bits = payload or k."""
        bits = self.kpay if info == "payload" else self.nblk * self.k
        return esn0_db + 10 * np.log10(self.n_sym / bits)

    def despread_ops(self):
        """Despreader ops per burst (costmodel: 2 per chip when sf > 1, else 0)."""
        return 2 * self.n_el if self.sf > 1 else 0

    def frontend_ops(self):
        """costmodel.frontend_ops: de-rotation (chip rate) + despreading + LLR scaling of the channel bits."""
        return costmodel.frontend_ops(self.n_sym, self.sf, self.n_chan, self.mod)

    def frontend_crit(self):
        return costmodel.frontend_crit(self.n_sym, self.sf, self.n_chan, self.mod)
