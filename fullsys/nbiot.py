"""
3GPP IoT-NTN NB-IoT NPUSCH format 1, single tone, 3.75 kHz subcarrier spacing (Rel-17+), for the full-system competitor
study (BLIND_IMPLEMENTATION/testing/results/lit_widecfo_competitor.md, rank 1): AWGN, timing known, M_rep = 1, one HARQ
transmission (RV 0), the DM-RS used only for CFO, phase, gain and N0.

Tx per transmission (TS 36.212 6.3.2, 5.1.1, 5.1.3.2, 5.1.4.1; TS 36.211 10.1.3, 10.1.4, 10.1.5; TS 36.213 16.5.1.2):
    TB (A = TBS bits, Table 16.5.1.2-2 at (I_TBS, I_RU)) -> CRC-24A (0x864CFB, init 0, MSB first) -> K = A + 24 (a
    Table 5.1.3-3 size for every NPUSCH TBS: one code block, no filler) -> LTE turbo 1/3 + rate matching to
    E = G = N_RU 16 slots 6 data symbols Q_m, RV 0 (turbo_lte.py) -> [per-RU channel interleaver 5.2.2.8: identity
    for one subcarrier] -> scrambling c(n), c_init = n_RNTI 2^14 + (n_f mod 2) 2^13 + floor(n_s / 2) 2^9 + N_ID^cell
    -> QPSK (Q_m 2, 36.211 Table 7.1.2-1) or BPSK (Q_m 1, Table 7.1.1-1) -> time-first mapping onto the data symbols of
    7-symbol 2 ms slots, DM-RS at slot symbol 4 (Table 10.1.4.2-1), r(n) = (1+j)/sqrt2 (1 - 2 c_35(n)) w_u(n mod 16)
    (10.1.4.1.1, Table 10.1.4.1.1-1 Hadamard row u = N_ID^cell mod 16) -> phase rotation of every SC-FDMA symbol
    exp(j rho (l~ mod 2)), rho = pi/4 (QPSK) / pi/2 (BPSK), l~ = symbol counter of the transmission (10.1.5)
Timing (10.1.5, Table 10.1.5-1): T_s = 1 / 30.72 MHz, symbol N + N_CP = 8192 + 256 = 8448 T_s = 275 us, slot 61440 T_s
= 7 symbols + a 2304 T_s (3/11 symbol) guard period that is not transmitted. Burst symbol n (slot s = n // 7) sits at
    t_n = n mod 7 + (80 / 11) (s + 20 floor(s / 128))    (symbol durations; 80/11 = slot / symbol)
the 20-slot term = the 40 ms uplink gap after every 256 ms of transmission (10.1.3.6) [mem], only for N_RU = 10.
The CFO f is in cycles per symbol DURATION (275 us): 128 Hz = 0.0352. The DM-RS comb is uniform in t (period 80/11
symbols, aliases at +-11/80 = +-0.1375), so the DA estimator runs on the comb index (no alias search inside +-0.069).

Model (run_fullsys_da.py --sys nbiot): symbol-rate waveform through txrx_chain.transmit (RRC ROLLOFF, the project's
full-chain rule; NB-IoT has no RRC, its single tone uses a rectangular symbol + CP); the guard / gap phase is applied
as a per-symbol rotation exp(j 2 pi f (t_n - n)) before the chain (exact at the symbol instants). The CP is not
simulated (it is discarded by the receiver): Es is per useful symbol; ebn0_db(cp=True) charges the CP energy
(+10 log10(8448/8192) = +0.134 dB). Eb/N0 per payload bit charges every transmitted symbol (data + DM-RS).
LLR convention as polar.py: LLR = log P(bit = 0) / P(bit = 1).
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from fullsys import turbo_lte as tl                                  # noqa: E402
from fullsys.vde import CRC, crc_register                            # noqa: E402

ASSUMPTIONS = list(tl.ASSUMPTIONS) + [
    "TBS / MCS: TS 36.213 Table 16.5.1.2-2 and the single-tone Table 16.5.1.2-1 read from the itecspec Rel-19 mirror "
    "(2026-11-17; TBS_TABLE / MCS_SINGLE_TONE below). UE category NB1 (max UL TBS 1000). Single tone: I_TBS 0 and 2 "
    "are pi/2-BPSK (I_MCS 0, 1), the rest pi/4-QPSK; N_RU = {1, 2, 3, 4, 5, 6, 8, 10}[I_RU].",
    "Format choice (FORMATS): for each target payload the closest TBS, then the most robust single-tone format "
    "(lowest code rate on pi/4-QPSK) within 256 ms (N_RU <= 8): 205 -> 208 (nb208, I_MCS 2 / I_TBS 1 / I_RU 5); "
    "307 -> 296 is the closest TBS but exists only at I_RU 1 (2 RUs, rate 0.83: nb296), so nb328 (I_TBS 3, I_RU 5, "
    "rate 0.31) is the strong format near 307; 819 -> 808 (nb808, I_TBS 6, I_RU 6); 1000 -> 1000 (nb1000, I_TBS 7, "
    "I_RU 6, rate 0.67). Variants: nb208b (pi/2-BPSK, I_TBS 0, I_RU 6), nb1000r10 (I_TBS 6, I_RU 7: 10 RUs, rate 0.53, "
    "320 ms + the 40 ms uplink gap).",
    "Resource unit (36.211 Table 10.1.2.3-1): 3.75 kHz, 1 subcarrier -> 16 slots of 2 ms (32 ms); 1 DM-RS + 6 data "
    "symbols per slot -> 96 data symbols per RU, G = 96 N_RU Q_m coded bits.",
    "UL-SCH coding (36.212 6.3.2): CRC attachment (5.2.2.1), channel coding (5.2.2.3), rate matching (5.2.2.4) with "
    "rv_idx 0 (M_rep 1, first transmission); the per-RU channel interleaver (5.2.2.7-8) has one row for a single "
    "subcarrier and is the identity. TBS + 24 is a QPP size for every NPUSCH TBS: one code block, no filler.",
    "Scrambling: 36.211 5.3.1 Gold sequence (7.2: x1 init 1, x2 init c_init, N_C = 1600), c_init per 10.1.3.1 with "
    "n_RNTI = 1, n_f = 0, n_s = 0, N_ID^cell = 0 (no effect on AWGN performance).",
    "DM-RS (10.1.4.1.1): r(n) = (1+j)/sqrt2 (1 - 2 c(n)) w(n mod 16), c with c_init = 35 [mem: the mirror drops the "
    "equation], w = Table 10.1.4.1.1-1 row u = N_ID^cell mod 16 = 0 (read from the mirror: Sylvester Hadamard rows), "
    "no group hopping; one DM-RS per slot at symbol 4 (Table 10.1.4.2-1, read). Its values are known to the receiver, "
    "so the sign convention does not affect performance.",
    "Phase rotation (10.1.5, read): phi(l~) = rho (l~ mod 2) + phi_k(l~), rho = pi/2 BPSK / pi/4 QPSK, l~ counts every "
    "SC-FDMA symbol (DM-RS included) from 0 at the start of the codeword. The continuous-phase term phi_k(l~) (tone at "
    "(k + 1/2) 3.75 kHz, guard not included) is deterministic and removed by the tone demodulator: not modelled.",
    "Timing: 3.75 kHz symbol 8448 T_s, slot 61440 T_s, guard 2304 T_s = 3/11 symbol (Table 10.1.5-1 + the slot length; "
    "the guard value is derived). Uplink gap (10.1.3.6): 40 ms after every 256 ms of transmission [mem: the mirror "
    "drops the numbers]; affects only N_RU = 10 (nb1000r10). NTN segmented pre-compensation gaps (UE capability "
    "ntn-SegmentedPrecompensationGaps-r17) and NPRACH / reserved-subframe postponements are not configured.",
    "Waveform: symbol-rate single carrier through txrx_chain.transmit (RRC ROLLOFF = 0.20, the polar genie default; "
    "NB-IoT has no RRC). The guard / gap delay enters only as the CFO phase at t_n (pre-rotation at the symbol "
    "instants); the RRC ISI across the phase step at a slot boundary (<= 2 pi 0.055 3/11 = 0.09 rad) is not exact.",
    "CP: not simulated; Es/N0 per useful (8192 T_s) symbol; the CP energy (256 / 8192) is charged in ebn0_*_cp.",
    "CFO: f per 275 us symbol duration; the SAN conformance offset 128 Hz = 0.0352, the S-band +-0.1 ppm budget "
    "(+-200 Hz) = 0.055; the run draws f ~ U(-cfo_max, cfo_max) per packet (3GPP: a static offset).",
    "Receiver: DA CFO / phase / gain / N0 from the DM-RS only (fullsys/da_sync.py on the DM-RS comb index), "
    "decision on the data with the turbo decoder; no decision-directed refinement, no repetition combining.",
    "Code-only validation format 'aff3ct-K2048' (not an NPUSCH format): K 2048 = 2024 + CRC-24A, AFF3CT puncturing "
    "'11,10,01' (all systematic, parity 1 at even k, parity 2 at odd k, the 12 tail bits sent) = (4108, 2048), plain "
    "BPSK, no scrambling / DM-RS, crc_start 2; = the AFF3CT reference Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt "
    "(MAX, LTE_VEC 0.75, 8 it, 24-LTEA CRC).",
]

# ---- 36.211 / 36.213 constants ------------------------------------------------------------------------------------
TS_SYM, TS_SLOT, TS_N, TS_CP = 8448, 61440, 8192, 256          # 3.75 kHz: symbol, slot, useful part, CP (T_s units)
SYM_PER_SLOT, SLOTS_PER_RU, DMRS_SYM = 7, 16, 4                 # Table 10.1.2.3-1, Table 10.1.4.2-1 (format 1, 3.75 kHz)
SLOT_T = TS_SLOT / TS_SYM                                       # 80 / 11 symbol durations per slot (guard included)
GAP_AFTER_SLOTS, GAP_SLOTS = 128, 20                            # 256 ms of transmission, then a 40 ms gap [mem]
T_SYM_S = TS_SYM / 30.72e6                                      # 275 us
CP_DB = 10 * np.log10(TS_SYM / TS_N)                            # CP energy charge, +0.134 dB
N_RU_OF = (1, 2, 3, 4, 5, 6, 8, 10)                             # I_RU -> N_RU (36.213 Table 16.5.1.1-2) [mem]
ROLLOFF = 0.20
CRC24A = dict(nbits=24, poly=0x864CFB, init=0)                  # 36.212 5.1.1 g_CRC24A
MCS_SINGLE_TONE = {0: (1, 0), 1: (1, 2), 2: (2, 1), 3: (2, 3), 4: (2, 4), 5: (2, 5), 6: (2, 6), 7: (2, 7),
                   8: (2, 8), 9: (2, 9), 10: (2, 10)}           # Table 16.5.1.2-1 (N_sc^RU = 1): I_MCS -> (Q_m, I_TBS)
TBS_TABLE = (                                                   # Table 16.5.1.2-2 rows I_TBS 0..13, columns I_RU 0..7
    (16, 32, 56, 88, 120, 152, 208, 256), (24, 56, 88, 144, 176, 208, 256, 344),
    (32, 72, 144, 176, 208, 256, 328, 424), (40, 104, 176, 208, 256, 328, 440, 568),
    (56, 120, 208, 256, 328, 408, 552, 680), (72, 144, 224, 328, 424, 504, 680, 872),
    (88, 176, 256, 392, 504, 600, 808, 1000), (104, 224, 328, 472, 584, 712, 1000, 1224),
    (120, 256, 392, 536, 680, 808, 1096, 1384), (136, 296, 456, 616, 776, 936, 1256, 1544),
    (144, 328, 504, 680, 872, 1000, 1384, 1736), (176, 376, 584, 776, 1000, 1192, 1608, 2024),
    (208, 440, 680, 1000, 1128, 1352, 1800, 2280), (224, 488, 744, 1032, 1256, 1544, 2024, 2536))
TBS_MAX_NB1 = 1000

# ---- formats: (I_MCS, I_RU) single tone; tag = seed tag shared with run_polar_genie's nb* formats (payload pairing)
FORMATS = {
    "nb208": dict(i_mcs=2, i_ru=5, tag=5208, target=205, note="R 1/10 payload: TBS 208, pi/4-QPSK, 6 RUs, rate 0.20"),
    "nb208b": dict(i_mcs=0, i_ru=6, tag=5209, target=205, note="TBS 208 on pi/2-BPSK, 8 RUs, rate 0.30 (variant)"),
    "nb296": dict(i_mcs=9, i_ru=1, tag=5296, target=307, note="closest TBS to 307 (only at 2 RUs), rate 0.83"),
    "nb328": dict(i_mcs=3, i_ru=5, tag=5328, target=307, note="R 0.15 payload: TBS 328, 6 RUs, rate 0.31"),
    "nb808": dict(i_mcs=6, i_ru=6, tag=5808, target=819, note="R 2/5 payload: TBS 808, 8 RUs, rate 0.54"),
    "nb1000": dict(i_mcs=7, i_ru=6, tag=6000, target=1000, note="max NB1 TBS 1000, 8 RUs, rate 0.67"),
    "nb1000r10": dict(i_mcs=6, i_ru=7, tag=6010, target=1000, note="TBS 1000, 10 RUs (320 ms + 40 ms gap), rate 0.53"),
    "aff3ct-K2048": dict(code_only=True, A=2024, K=2048, tag=7048, crc_start=2,
                         note="code-only validation = AFF3CT Turbo_N4096_K2048_BCJR_i8_ref_LTE (4108, 2048) BPSK"),
}
MAIN_FORMATS = ("nb208", "nb328", "nb808", "nb1000")

# AFF3CT error_rate_references (master) TURBO/AWGN/BPSK/RSC_RSC/BCJR/LTE/Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt
# (local copy: BLIND_IMPLEMENTATION/testing/results/standards/aff3ct_refs/): K_info 2024 + CRC 24-LTEA, puncturing
# 11,10,01 (N 4108), BPSK AWGN, MAX + LTE_VEC 0.75, 8 it, 100 frame errors per point. {AFF3CT Eb/N0: FER}
REF_AFF3CT = {0.5: 1.00, 0.6: 9.46e-1, 0.7: 9.09e-1, 0.8: 6.84e-1, 0.9: 5.83e-1, 1.0: 3.16e-1, 1.1: 1.57e-1,
              1.2: 6.74e-2, 1.3: 1.58e-2, 1.4: 4.21e-3, 1.5: 6.88e-4, 1.6: 8.03e-5, 1.7: 1.66e-5, 1.8: 6.87e-6,
              1.9: 4.13e-6, 2.0: 2.21e-6}


def gold(c_init, n, Nc=1600):
    """36.211 7.2 pseudo-random sequence c(0..n-1): x1(0) = 1, x2 = c_init bits, c(m) = x1(m + Nc) ^ x2(m + Nc)."""
    L = n + Nc + 31
    x1 = np.zeros(L, np.int8)
    x2 = np.zeros(L, np.int8)
    x1[0] = 1
    x2[:31] = [(c_init >> i) & 1 for i in range(31)]
    for m in range(L - 31):
        x1[m + 31] = x1[m + 3] ^ x1[m]
        x2[m + 31] = x2[m + 3] ^ x2[m + 2] ^ x2[m + 1] ^ x2[m]
    return (x1[Nc:Nc + n] ^ x2[Nc:Nc + n]).astype(np.int8)


def hadamard_row(u, n=16):
    """Table 10.1.4.1.1-1 row u (Sylvester order, entries +-1)."""
    H = np.array([[1]])
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H[u]


def fmt_params(name):
    """Resolved format: A, K, E, Q_m, N_RU, I_TBS, ... (FORMATS entry + Tables 16.5.1.2-1 / -2)."""
    f = dict(FORMATS[name])
    if f.get("code_only"):
        f.update(qm=1, n_ru=0, i_tbs=None, i_ru=None, E=2 * f["K"] + 12, mod="bpsk")
        return f
    qm, i_tbs = MCS_SINGLE_TONE[f["i_mcs"]]
    A = TBS_TABLE[i_tbs][f["i_ru"]]
    assert A <= TBS_MAX_NB1, f"{name}: TBS {A} > {TBS_MAX_NB1} (UE category NB1)"
    n_ru = N_RU_OF[f["i_ru"]]
    f.update(qm=qm, i_tbs=i_tbs, A=A, K=A + 24, n_ru=n_ru, E=SLOTS_PER_RU * (SYM_PER_SLOT - 1) * n_ru * qm,
             mod="qpsk" if qm == 2 else "bpsk", crc_start=f.get("crc_start", 1))
    return f


def burst_times(n_slots):
    """t_n (symbol durations) of the n_slots 7-symbol slots: guard 3/11 per slot, 20-slot gap after every 128 slots
    of transmission (only if more slots follow)."""
    n = np.arange(SYM_PER_SLOT * n_slots)
    s = n // SYM_PER_SLOT
    gaps = (s // GAP_AFTER_SLOTS) if n_slots > GAP_AFTER_SLOTS else np.zeros_like(s)
    return n % SYM_PER_SLOT + SLOT_T * (s + GAP_SLOTS * gaps)


class NPUSCH:
    """One NPUSCH format 1 transmission format (FORMATS key) with its encoder, layout and ideal-sync receiver."""

    def __init__(self, fmt, rnti=1, n_f=0, n_s=0, cell_id=0, rv=0):
        p = fmt_params(fmt)
        self.fmt, self.p = fmt, p
        self.A, self.K, self.E, self.qm, self.mod = p["A"], p["K"], p["E"], p["qm"], p["mod"]
        self.code_only = bool(p.get("code_only"))
        self.crc_start = p["crc_start"]
        self.kpay = self.A
        self.crc = CRC(self.A, **CRC24A)
        self.crc_chk = CRC(self.K, **CRC24A)
        if self.code_only:                                     # AFF3CT puncturing 11,10,01 + the 12 tail bits
            K, D = self.K, self.K + 4
            k = np.arange(K)
            tail = [i * D + K + j for j in range(4) for i in range(3)]
            idx = np.concatenate([k, D + k[k % 2 == 0], 2 * D + k[k % 2 == 1], tail])
            self.code = tl.TurboLTE(K, idx=idx)
            self.n_slots, self.n_sym = 0, self.E
            self.t = np.arange(self.E, dtype=float)
            self.data_pos = np.arange(self.E)
            self.dmrs_pos = np.zeros(0, np.int64)
            self.scr = np.zeros(self.E, np.int8)
            self.rot = np.ones(self.E, complex)
            self.dmrs = np.zeros(0, complex)
            self.n_valid = self.E
        else:
            self.code = tl.TurboLTE(self.K, self.E, rv)
            self.n_valid = self.code.rm["n_valid"]
            self.n_slots = SLOTS_PER_RU * p["n_ru"]
            self.n_sym = SYM_PER_SLOT * self.n_slots
            self.t = burst_times(self.n_slots)
            n = np.arange(self.n_sym)
            self.dmrs_pos = SYM_PER_SLOT * np.arange(self.n_slots) + DMRS_SYM
            self.data_pos = n[n % SYM_PER_SLOT != DMRS_SYM]
            self.c_init = rnti * 2 ** 14 + (n_f % 2) * 2 ** 13 + (n_s // 2) * 2 ** 9 + cell_id
            self.scr = gold(self.c_init, self.E)
            rho = np.pi / 4 if self.qm == 2 else np.pi / 2
            self.rot = np.exp(1j * rho * (n % 2))                # l~ = n: every SC-FDMA symbol of the codeword
            s = np.arange(self.n_slots)
            w = hadamard_row(cell_id % 16)
            self.dmrs = (1 + 1j) / np.sqrt(2) * (1 - 2 * gold(35, self.n_slots)) * w[s % 16] * self.rot[self.dmrs_pos]
        assert len(self.data_pos) * self.qm == self.E, (fmt, len(self.data_pos), self.qm, self.E)
        self.n_data = len(self.data_pos)
        n_gap = (self.n_slots - 1) // GAP_AFTER_SLOTS if self.n_slots > GAP_AFTER_SLOTS else 0
        self.duration_ms = 2.0 * (self.n_slots + GAP_SLOTS * n_gap) if not self.code_only else None   # incl. gaps

    # ---- Tx ----
    def encode_bits(self, pay):
        """pay (B, A) -> dict(c (B, K) TB | CRC-24A, d (B, 3, K + 4), e (B, E), b (B, E) scrambled)."""
        pay = np.asarray(pay, np.int8)
        c = np.concatenate([pay, self.crc.register(pay)], 1)
        d = self.code.encode(c)
        e = self.code.rate_match(d)
        return dict(c=c, d=d, e=e, b=e ^ self.scr[None])

    def map_bits(self, b):
        """Scrambled bits (B, E) -> burst symbols (B, n_sym) incl. the DM-RS, unit energy, phase-rotated."""
        B = b.shape[0]
        if self.code_only:
            return (1.0 - 2.0 * b).astype(complex)
        if self.qm == 2:
            z = ((1 - 2.0 * b[:, 0::2]) + 1j * (1 - 2.0 * b[:, 1::2])) / np.sqrt(2)
        else:
            z = (1 - 2.0 * b) * (1 + 1j) / np.sqrt(2)
        x = np.empty((B, self.n_sym), complex)
        x[:, self.data_pos] = z * self.rot[self.data_pos][None]
        x[:, self.dmrs_pos] = self.dmrs[None]
        return x

    def tx(self, pay):
        st = self.encode_bits(pay)
        return self.map_bits(st["b"]), st

    # ---- Rx ----
    def data_llr(self, y, n0):
        """y (B, n_sym) unit gain, complex noise variance n0 (scalar or (B, 1)) -> descrambled LLRs (B, E)."""
        yd = y[:, self.data_pos] * np.conj(self.rot[self.data_pos])[None]
        if self.code_only:
            L = 4.0 * yd.real / n0
        elif self.qm == 2:
            L = np.empty((y.shape[0], self.E))
            L[:, 0::2], L[:, 1::2] = 2 * np.sqrt(2) * yd.real / n0, 2 * np.sqrt(2) * yd.imag / n0
        else:
            L = 4.0 * (yd * (1 - 1j) / np.sqrt(2)).real / n0
        return L * (1 - 2.0 * self.scr[None])

    def decode_llr(self, llr, iters=8, algo="maxlog", scale=None, early=True):
        """Channel LLRs (B, E) -> dict(payload (B, A), crc_ok (B,), iters (B,), first (B,), ops (B,), ops_crit (B,))."""
        Ld = self.code.rate_recover(llr)
        stop = lambda bits, rows: ~self.crc_chk.register(bits).any(1)
        bits, used, first, _ = self.code.decode(Ld, iters, algo, scale, stop, self.crc_start, freeze=early)
        ok = ~self.crc_chk.register(bits).any(1)
        sc = None if scale is None else (scale != 1.0)
        return dict(payload=bits[:, :self.A], crc_ok=ok, iters=used, first=first,
                    ops=np.asarray(tl.macs(self.K, used, algo, early, sc), float),
                    ops_crit=np.asarray(tl.crit(self.K, used, algo, early, sc), float))

    def rx(self, y, n0, iters=8, algo="maxlog", scale=None, early=True):
        """Ideal-sync receiver: unit-gain symbols y (B, n_sym), noise variance n0."""
        return self.decode_llr(self.data_llr(y, n0), iters, algo, scale, early)

    # ---- bookkeeping ----
    def llr_ops(self):
        """LLR scaling 1 / channel bit + the repetition sums of the rate recovery (descrambling = sign, free)."""
        return float(self.E + max(self.E - self.n_valid, 0))

    def ebn0_db(self, esn0_db, cp=False, charge="burst"):
        """Eb/N0 per payload bit: Es/N0 + 10 log10(symbols / A); charge 'burst' (data + DM-RS) or 'data'; cp: + CP."""
        n = self.n_sym if charge == "burst" else self.n_data
        return esn0_db + 10 * np.log10(n / self.A) + (CP_DB if cp and not self.code_only else 0.0)

    def summary(self):
        p = self.p
        return dict(fmt=self.fmt, A=self.A, K=self.K, E=self.E, qm=self.qm, mod=self.mod, i_mcs=p.get("i_mcs"),
                    i_tbs=p.get("i_tbs"), i_ru=p.get("i_ru"), n_ru=p.get("n_ru"), n_slots=self.n_slots,
                    n_sym=self.n_sym, n_data=self.n_data, n_dmrs=len(self.dmrs_pos), rate=self.K / self.E,
                    duration_ms=self.duration_ms, n_valid=self.n_valid, crc_start=self.crc_start,
                    k0=None if self.code.rm is None else self.code.rm["k0"], note=p.get("note"),
                    ebn0_offset_burst=float(self.ebn0_db(0.0)), ebn0_offset_burst_cp=float(self.ebn0_db(0.0, True)),
                    ebn0_offset_data=float(self.ebn0_db(0.0, charge="data")))


def crc24a_check(data=b"123456789", init=0):
    """CRC-24A register over the bytes (MSB first, no reflection / final XOR): 0xCDE703 (CRC-24/LTE-A); with
    init 0xB704CE the same polynomial gives the OpenPGP check 0x21CF02."""
    bits = np.unpackbits(np.frombuffer(data, np.uint8))
    return crc_register(bits, 24, CRC24A["poly"], init)
