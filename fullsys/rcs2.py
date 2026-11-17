"""
DVB-RCS2 TC-LM return-link burst (EN 301 545-2 V1.3.1 cl. 7.3, Annex A Table A-1): transmitter and receiver helpers.

    tx  cl. 7.3.2 order: energy dispersal of the Frame PDU (7.3.3) -> CRC (7.3.4) -> turbo code (7.3.5.1, turbo_db)
        -> bit-to-symbol map (7.3.7.1.4) -> unique word: preamble | data with one pilot symbol every pilot period |
        postamble (7.3.6.1, 7.3.7.1.2-3)
    rx  synchronise (hook: 'ideal' | 'da') -> strip the known symbols -> demap to LLRs -> turbo decode -> CRC on the
        scrambled bits -> descramble

Symbols are unit energy at symbol rate; the RRC (roll-off 0.20, cl. 7.3.7.1.1) is applied by the channel chain
(run_rcs2.py, txrx_chain.transmit with beta = ROLLOFF). Es/N0 is per transmitted symbol (TR 10.2.1 convention).
"""

import numpy as np

from fullsys import turbo_db as tdb

ROLLOFF = 0.20                           # cl. 7.3.7.1.1 (V1.3.1)
SCR_INIT = "100101010000000"             # SR1 ... SR15, Table 7-11; PRBS 1 + x^14 + x^15 (Eq. 7-1)
CRC_POLY = {16: 0x8005, 32: 0x04C11DB7}  # Table 7-12: CRC16 x^16+x^15+x^2+1 (init 0), CRC32 ISO 13818-1 Annex B
CRC_INIT = {16: 0x0000, 32: 0xFFFFFFFF}

ASSUMPTIONS = list(tdb.ASSUMPTIONS) + [
    "Table A-1 payload bytes = Frame PDU + CRC = turbo input K = 8 x bytes; traffic bursts carry CRC32 (k = K - 32).",
    "Energy dispersal: output = SR14 ^ SR15 fed back into SR1 (DVB-S randomiser form), XOR on every Frame PDU bit, "
    "reset per burst; the CRC and the UW are not scrambled; CRC computed over the scrambled PDU.",
    "CRC16 = poly 0x8005, init 0, no reflection, no final XOR (CRC-16/UMTS); CRC32 = CRC-32/MPEG-2 (init all 1, no "
    "reflection, no final XOR); bits fed MSB first, register appended MSB first.",
    "QPSK map (Fig. 7-20 not legible): Gray, I = (1 - 2 u0)/sqrt2, Q = (1 - 2 u1)/sqrt2; symbol k < N carries "
    "(A_k, B_k), symbol N + k carries (Z1_k, Z2_k).",
    "pi/2-BPSK (EN 7.3.7.1.4.1, read from the local EN text): bits A0 B0 A1 B1 ... Z1_0 Z2_0 Z1_1 ..., bit 0 -> +1, "
    "s(n) = u(n) exp(j (pi n / 2 + pi / 4)); 'the integer n for the very first symbol in the burst is arbitrary': "
    "we use n = burst index from the first preamble symbol (UW symbols mapped the same way, EN 7.3.7.1.2-3).",
    "UW (EN 6.4.6.1 UW_symbol: m bits per symbol of the concatenated preamble | one pilot block | postamble; hex "
    "strings re-read from the local EN Table A-1 for IDs 3, 13, 14, 42, identical): read MSB first, trailing pad "
    "bits dropped (pilot = (0,0) for the QPSK IDs, bit 0 for ID 42); every pilot block repeats the same symbols.",
    "Pilot layout (EN 6.4.6.1 pilot_period, 7.3.6.1): the last symbol of the first pilot block lies one pilot period "
    "after the last preamble symbol, period = distance between block starts, blocks inserted while P - 1 payload "
    "symbols remain to sustain the period (zero or more payload after the last block); block length 1: "
    "l = Lpre - 1 + k P, k = 1 ... min(pilot sum, n_data // (P - 1)); postamble = the last Lpost symbols.",
    "Eb/N0 per information bit: EbN0 = EsN0 + 10 log10(L_burst / k), k = K - CRC bits, every burst symbol charged "
    "(lit_rcs2_fullsystem.md 0). AFF3CT convention: EsN0 = EbN0 + 10 log10(m k / n_coded) (no UW).",
    "Demapper: QPSK Gray and BPSK per-dimension LLRs, where max-log and exact are identical (both implemented "
    "generically over the constellation); N0 = Es / SNR is known (ideal sync).",
    "Waveforms 'A12' / 'A13' / 'A23' (= --fmt aff3ct-N3008 / N4512 / N2256) are code-only (no UW / pilots) K = 1504 "
    "QPSK rate 1/2 / 1/3 / 2/3 with the N = 752 P/Q (A12 = the ID 14 code), as the AFF3CT reference curves "
    "(K_info 1472 + CRC32, PSK 2 bps, MAX, ADAPTIVE, 8 it); not Table A-1 waveforms. AFF3CT runs a symbol-rate "
    "channel; we keep the RRC chain (identical in AWGN up to the truncated-filter ISI). AFF3CT FER = any K_info bit "
    "wrong (our 'mismatch'); its turbo decoder stops on the CRC from iteration 2 (--dec-crc-start), so the fmt "
    "runs use early stop.",
]

# Annex A Table A-1 rows (lit_rcs2_fullsystem.md 0, 1.6). Q = (Q0, Q1, Q2, Q3); pre / post / pilot in symbols.
WAVEFORMS = {
    3: dict(mod="qpsk", rate="1/3", bytes=38, N=152, P=17, Q=(9, 5, 14, 1), ypat="1", wpat="1", burst=536,
            pre=27, post=27, pilot_period=18, pilot_sum=26, uw="F030F330CFFF00F030F330CFFF00", crc=32),
    13: dict(mod="qpsk", rate="1/3", bytes=123, N=492, P=31, Q=(0, 3, 1, 0), ypat="1", wpat="1", burst=1616,
             pre=32, post=31, pilot_period=20, pilot_sum=77, uw="3F00C30F3F3FCCC03CC0F03F3F00333C", crc=32),
    14: dict(mod="qpsk", rate="1/2", bytes=188, N=752, P=37, Q=(1, 3, 4, 2), ypat="1", wpat="0", burst=1616,
             pre=25, post=25, pilot_period=25, pilot_sum=62, uw="FC033FCC3030CFC033FCC30303", crc=32),
    42: dict(mod="pi2bpsk", rate="1/3", bytes=123, N=492, P=31, Q=(0, 3, 1, 0), ypat="1", wpat="1", burst=3236,
             pre=65, post=64, pilot_period=20, pilot_sum=155, uw="C7B6676A0A09D0B7B17D422B7B8E48E44", crc=32),
    "A12": dict(mod="qpsk", rate="1/2", bytes=188, N=752, P=37, Q=(1, 3, 4, 2), ypat="1", wpat="0", burst=1504,
                pre=0, post=0, pilot_period=0, pilot_sum=0, uw="", crc=32),
    "A13": dict(mod="qpsk", rate="1/3", bytes=188, N=752, P=37, Q=(1, 3, 4, 2), ypat="1", wpat="1", burst=2256,
                pre=0, post=0, pilot_period=0, pilot_sum=0, uw="", crc=32),
    "A23": dict(mod="qpsk", rate="2/3", bytes=188, N=752, P=37, Q=(1, 3, 4, 2), ypat="10", wpat="0", burst=1128,
                pre=0, post=0, pilot_period=0, pilot_sum=0, uw="", crc=32),
}

# TR 101 545-4 cl. 10.2.1 (Tables 10.4-10.8): Es/N0 (dB) per transmitted symbol at PER, ideal sync, AWGN
REF_PER = {
    2: {"table": "10.4", 1e-1: -0.53, 1e-2: 0.06, 1e-3: 0.50, 1e-4: 0.87, 1e-5: 1.29},
    41: {"table": "10.4 (row printed '41 | 3 236', burst-length misprint)", 1e-1: -4.00, 1e-2: -3.65, 1e-3: -3.38,
         1e-4: -3.17, 1e-5: -2.98},
    3: {"table": "10.5", 1e-3: -0.27, 1e-5: 0.22},
    4: {"table": "10.5", 1e-3: 1.92, 1e-5: 2.34},
    5: {"table": "10.5", 1e-3: 3.90, 1e-5: 4.29},
    13: {"table": "10.6", 1e-3: -0.80, 1e-5: -0.51},
    14: {"table": "10.6", 1e-3: 1.49, 1e-5: 1.71},
    15: {"table": "10.6", 1e-3: 3.46, 1e-5: 3.69},
    42: {"table": "10.8", 1e-3: -3.81, 1e-5: -3.52},
    43: {"table": "10.8", 1e-3: -1.53, 1e-5: -1.30},
}

# AFF3CT error_rate_references Turbo_DB_N{3008,4512,2256}_K1504_BCJR_i8_ref_DVB-RCS2.txt (local copies in
# BLIND_IMPLEMENTATION/testing/results/standards/aff3ct_refs; uncommented rows): K = 1504 (K_info 1472 + CRC32),
# PSK 2 bps AWGN, MAX + ADAPTIVE, 8 it. {AFF3CT Eb/N0 (per K_info, code rate only): FER}
REF_AFF3CT = {
    "1/2": {"wf": "A12", "fmt": "aff3ct-N3008", "n_coded": 3008,
            0.0: 1.00, 0.2: 1.00, 0.4: 9.92e-1, 0.6: 9.33e-1, 0.8: 7.56e-1, 1.0: 4.00e-1, 1.2: 1.07e-1,
            1.4: 1.22e-2, 1.6: 5.91e-4, 1.8: 9.22e-6, 2.0: 9.31e-8, 2.2: 1.29e-8, 2.4: 3.57e-9},
    "1/3": {"wf": "A13", "fmt": "aff3ct-N4512", "n_coded": 4512,
            0.0: 9.62e-1, 0.2: 7.76e-1, 0.4: 3.87e-1, 0.6: 8.01e-2, 0.8: 6.49e-3, 1.0: 2.37e-4, 1.2: 2.64e-6,
            1.4: 8.15e-8, 1.6: 2.00e-8, 1.8: 5.37e-9},
    "2/3": {"wf": "A23", "fmt": "aff3ct-N2256", "n_coded": 2256,
            0.0: 1.00, 0.2: 1.00, 0.4: 1.00, 0.6: 1.00, 0.8: 1.00, 1.0: 1.00, 1.2: 9.92e-1, 1.4: 9.47e-1,
            1.6: 6.98e-1, 1.8: 4.75e-1, 2.0: 1.44e-1, 2.2: 2.17e-2, 2.4: 1.31e-3, 2.6: 4.86e-5, 2.8: 1.10e-6,
            3.0: 1.00e-7, 3.2: 2.63e-8, 3.4: 8.96e-9, 3.6: 2.61e-9},
}
FMT = {v["fmt"]: v["wf"] for v in REF_AFF3CT.values()}   # run_rcs2 --fmt -> code-only waveform

BITS_PER_SYM = {"qpsk": 2, "pi2bpsk": 1}


def wf_key(s):
    """CLI waveform name -> WAVEFORMS key ('13' -> 13, 'A13' -> 'A13')."""
    return int(s) if str(s).isdigit() else str(s)


# ---- energy dispersal (cl. 7.3.3) --------------------------------------------------------------------------------
def prbs(n):
    """First n bits of the 1 + x^14 + x^15 PRBS from SCR_INIT."""
    sr = [int(c) for c in SCR_INIT]
    out = np.empty(n, np.int8)
    for i in range(n):
        b = sr[13] ^ sr[14]
        out[i] = b
        sr = [b] + sr[:14]
    return out


# ---- CRC (cl. 7.3.4) ---------------------------------------------------------------------------------------------
def crc_bits_serial(bits, r):
    """Bitwise CRC, MSB first, batched: bits (B, n) -> register (B, r), column 0 = MSB."""
    poly = np.array([(CRC_POLY[r] >> (r - 1 - i)) & 1 for i in range(r)], np.int8)
    B = bits.shape[0]
    reg = np.array([(CRC_INIT[r] >> (r - 1 - i)) & 1 for i in range(r)], np.int8)[None].repeat(B, 0)
    for k in range(bits.shape[1]):
        fb = reg[:, 0] ^ bits[:, k]
        reg = np.concatenate([reg[:, 1:], np.zeros((B, 1), np.int8)], axis=1)
        reg ^= fb[:, None] * poly[None]
    return reg


_crc_lin = {}


def crc_bits(bits, r):
    """CRC as an affine GF(2) map (cached per length): register bits (B, r) = (bits M + c) mod 2."""
    n = bits.shape[1]
    if (n, r) not in _crc_lin:
        c = crc_bits_serial(np.zeros((1, n), np.int8), r)[0]
        M = crc_bits_serial(np.eye(n, dtype=np.int8), r) ^ c[None]
        _crc_lin[(n, r)] = (M.astype(np.float32), c)
    M, c = _crc_lin[(n, r)]
    return ((bits.astype(np.float32) @ M).astype(np.int64) % 2).astype(np.int8) ^ c[None]


def bytes_to_bits(b):
    return np.unpackbits(np.frombuffer(bytes(b), np.uint8))[None].astype(np.int8)


def bits_to_int(bits):
    return int("".join(str(int(x)) for x in bits), 2)


# ---- waveform layout (cl. 7.3.6.1, 7.3.7.1) ---------------------------------------------------------------------
class Waveform:
    """A Table A-1 burst: code, layout (data / pilot / UW positions), known symbols."""

    def __init__(self, key, direction=None):
        w = WAVEFORMS[key]
        self.key, self.w = key, w
        self.mod, self.m = w["mod"], BITS_PER_SYM[w["mod"]]
        self.K, self.crc = 8 * w["bytes"], w["crc"]
        self.k = self.K - self.crc                                     # Frame PDU bits (information bits)
        self.code = tdb.TurboDB(w["N"], w["P"], w["Q"], w["ypat"], w["wpat"], direction)
        assert 2 * w["N"] == self.K
        self.n_coded = self.K + 2 * self.code.M
        self.n_data = -(-self.n_coded // self.m)
        pre, post, P, ps = w["pre"], w["post"], w["pilot_period"], w["pilot_sum"]
        self.L = pre + self.n_data + ps + post
        assert self.L == w["burst"], (key, self.L, w["burst"])
        n_pil = min(ps, self.n_data // (P - 1)) if P else 0           # EN 7.3.6.1 insertion rule (block length 1)
        assert n_pil == ps, (key, n_pil, ps)                           # Table A-1 pilot sums obey the rule
        pil = np.array([pre - 1 + k * P for k in range(1, ps + 1)], np.int64)
        assert ps == 0 or pil[-1] < self.L - post
        kind = np.zeros(self.L, np.int8)                               # 0 data, 1 preamble, 2 pilot, 3 postamble
        kind[:pre], kind[pil], kind[self.L - post:] = 1, 2, 3
        self.data_idx = np.flatnonzero(kind == 0)
        self.known_idx = np.flatnonzero(kind != 0)
        assert len(self.data_idx) == self.n_data
        nk = pre + 1 + post if (pre + post) else 0                     # UW = preamble | one pilot | postamble
        uwb = np.array([int(c) for h in w["uw"] for c in format(int(h, 16), "04b")], np.int8)[:nk * self.m]
        assert len(uwb) == nk * self.m and len(w["uw"]) == -(-nk * self.m // 4)
        kb = np.zeros((self.L, self.m), np.int8)                       # known bits per burst symbol
        if nk:
            u = uwb.reshape(nk, self.m)
            kb[:pre], kb[pil], kb[self.L - post:] = u[:pre], u[pre], u[pre + 1:]
        self.pilot_bits = u[pre] if nk else None
        self.known_sym = self.map(kb[None], np.arange(self.L))[0][self.known_idx]

    def map(self, b, n):
        """b (B, S, m) bits at burst indices n (S,) -> symbols (B, S) (cl. 7.3.7.1.4)."""
        if self.mod == "qpsk":
            return ((1 - 2 * b[..., 0]) + 1j * (1 - 2 * b[..., 1])) / np.sqrt(2)
        return (1 - 2 * b[..., 0]) * np.exp(1j * (np.pi * n / 2 + np.pi / 4))

    # Eb/N0 helpers
    def ebn0(self, esn0):
        """Eb/N0 per information bit, all burst symbols charged: EsN0 + 10 log10(L / k)."""
        return esn0 + 10 * np.log10(self.L / self.k)

    def esn0_from_aff3ct(self, ebn0):
        """AFF3CT convention (code rate only, no UW): EsN0 = EbN0 + 10 log10(m k / n_coded)."""
        return ebn0 + 10 * np.log10(self.m * self.k / self.n_coded)


def tx(pdu, wf):
    """pdu (B, k) Frame PDU bits -> burst symbols (B, L) and the encoder input (B, K) (scrambled PDU | CRC)."""
    B = pdu.shape[0]
    scr = pdu ^ prbs(wf.k)[None]                                       # 7.3.3
    u = np.concatenate([scr, crc_bits(scr, wf.crc)], axis=1)          # 7.3.4
    Z1, Z2 = wf.code.encode(u)                                         # 7.3.5.1
    par = np.empty((B, 2 * wf.code.M), np.int8)
    par[:, 0::2], par[:, 1::2] = Z1, Z2
    stream = np.concatenate([u, par], axis=1)                          # A0 B0 ... | Z1_0 Z2_0 Z1_1 Z2_1 ...
    pad = wf.n_data * wf.m - stream.shape[1]
    if pad:
        stream = np.concatenate([stream, np.zeros((B, pad), np.int8)], axis=1)
    s = np.empty((B, wf.L), complex)
    s[:, wf.data_idx] = wf.map(stream.reshape(B, wf.n_data, wf.m), wf.data_idx)
    s[:, wf.known_idx] = wf.known_sym[None]
    return s, u


# ---- receiver ----------------------------------------------------------------------------------------------------
def synchronise(r, wf, sync="ideal", n0=None, **kw):
    """Hook: returns (r corrected, N0). 'ideal' = true timing, zero CFO, true phase, known N0.
    'da' (NEXT step): CFO (+-0.03) and phase from the UW / pilots at wf.known_idx with wf.known_sym."""
    if sync == "ideal":
        return r, n0
    if sync == "da":
        raise NotImplementedError("DA synchroniser (UW / pilots) is the next step")
    raise ValueError(sync)


def demap(y, wf, n0, exact=False):
    """Data symbols y (B, n_data) -> bit LLRs (B, n_data m), L = ln P(0)/P(1)."""
    if wf.mod == "pi2bpsk":
        y = y * np.exp(-1j * (np.pi * wf.data_idx / 2 + np.pi / 4))[None]   # derotate -> real +-1
        pts = np.array([[0], [1]], np.int8)
        const = 1.0 - 2.0 * pts[:, 0]
    else:
        pts = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], np.int8)
        const = wf.map(pts[None], np.zeros(len(pts)))[0]               # (P,) Gray QPSK points
    d = -np.abs(y[..., None] - const) ** 2 / n0                        # (B, S, P)
    red = (lambda x: np.logaddexp.reduce(x, axis=-1)) if exact else (lambda x: x.max(axis=-1))
    L = np.empty(y.shape + (wf.m,))
    for i in range(wf.m):
        L[..., i] = red(d[..., pts[:, i] == 0]) - red(d[..., pts[:, i] == 1])
    return L.reshape(y.shape[0], -1)


def crc_ok(u, wf):
    """u (B, K) decoded encoder input (scrambled PDU | CRC) -> CRC pass (B,)."""
    return np.all(crc_bits(u[:, :wf.k], wf.crc) == u[:, wf.k:], axis=1)


def rx(r, wf, n0, sync="ideal", algo="maxlog", iters=8, sf=tdb.SF_DEFAULT, early_stop=False, exact_demap=False,
       sf_low_iters=None):
    """Burst samples at symbol rate (B, L) -> dict(pdu (B, k), u (B, K), crc (B,), iters, first_pass)."""
    y, n0 = synchronise(r, wf, sync, n0)
    L = demap(y[:, wf.data_idx], wf, n0, exact=exact_demap)[:, :wf.n_coded]
    Ls, par = L[:, :wf.K], L[:, wf.K:]
    u, info = wf.code.decode(Ls, par[:, 0::2], par[:, 1::2], iters=iters, algo=algo, sf=sf,
                             crc_check=lambda b: crc_ok(b, wf), early_stop=early_stop,
                             sf_low_iters=sf_low_iters)
    ok = crc_ok(u, wf)
    pdu = u[:, :wf.k] ^ prbs(wf.k)[None]                               # descramble after the CRC check
    return dict(pdu=pdu, u=u, crc=ok, **info)
