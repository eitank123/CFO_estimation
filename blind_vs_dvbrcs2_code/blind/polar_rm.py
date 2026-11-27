"""
5G-NR-style polar rate matching (TS 38.212 5.3.1, 5.4.1.1, 5.4.1.2) around polar.PolarCode, for the full-system
comparison at the competitors' native (K, E) (BLIND_IMPLEMENTATION/testing/results/lit_polar_ratematch.md, sec. 1).

Fairness labels (state them with every result): "NR-style rate matching on an N <= 4096 PW mother code"; the
reliability order is our PW (beta = 2^(1/4)), NOT the NR sequence (NR has none beyond N = 1024); the
full-length CA-SCL decode is charged (decode_macs; no Fast-SSC rate-0 discount of the pre-frozen block).

    Mother N : N = 2^n, n = max(min(n1, n2, n_max), n_min), n_max = 12 (ours; NR 9 / 10), n_min = 5
               n1 = ceil(log2 E) - 1 if E <= (9/8) 2^(ceil(log2 E) - 1) and K/E < 9/16, else ceil(log2 E)
               n2 = ceil(log2 8K)                                             (mother rate >= 1/8)
    Interl.  : y_n = x_{J(n)}, J(n) = P(floor(32 n / N)) N/32 + n mod N/32   (32 sub-blocks, Table 5.4.1.1-1)
    Select   : U = N - E; E > N repeat e_k = y_{k mod N}; E == N none; else K/E <= 7/16 puncture e = y[U:]
               (drop the first U), otherwise shorten e = y[:E] (drop the last U, known zeros); mode= forces
               puncture / shorten (e.g. RCS2 ID 14 punctured so that PiCode stays valid)
    Pre-frz  : puncture: rm = u_{J(0..U-1)} + extra = the low block u_0..u_{t-1} beyond them (EXTRA_STD below);
               shorten: rm = u_{J(E..N-1)}
    Info set : the K most reliable of the rest by OUR PW order (polar.pw_reliability), not the NR sequence
               (design='pw', default); design='ga': by GA over the rate-matched channel (fullsys/polar_design.py)
    Encoder  : polar.PolarCode (natural order, no bit reversal: the NR convention, so J indexes u / x directly)
    Rx       : rate recovery to N LLRs (punctured 0, shortened +LLR_BIG = known zero, repeated: sum of the copies),
               then the unchanged PolarCode decoder (CA-SCL-L, CRC; K = A + crc_len, CRC-32 0x04C11DB7 by default,
               init 0 / no reflection / no final XOR: our own system's check, CRC-16 by crc_len=16).

LLR convention as polar.py: LLR = log P(bit = 0) / P(bit = 1).
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [_p for _p in (os.path.join(_ROOT, "blind"), os.path.join(_ROOT, "dvbrcs2")) if _p not in sys.path]   # (package)
from polar import CRC_POLYS, PolarCode, pw_reliability  # noqa: E402

SUBBLOCK_P = np.array([0, 1, 2, 4, 3, 5, 6, 7, 8, 16, 9, 17, 10, 18, 11, 19,
                       12, 20, 13, 21, 14, 22, 15, 23, 24, 25, 26, 28, 27, 29, 30, 31])   # TS 38.212 Table 5.4.1.1-1
N_MAX, N_MIN = 12, 5           # log2 mother length bounds (NR: n_max 9 DL / 10 UL; ours 12 -> N <= 4096)
LLR_BIG = 1e4                  # LLR of a shortened (known-zero) bit; float32-safe through the 12 g stages
EXTRA_STD = True               # puncturing low block u_0..u_{t-1}: True = the 38.212 text / Bioglio-Condo-Land Q2,
                               # t = ceil(.) bits (u_0..u_T, T = ceil(.) - 1); False = Sionna Polar5GEncoder,
                               # t = ceil(.) - 1 bits (`for i in range(ceil(.) - 1)`), one frozen bit fewer
NO_RM = ("PiCode4", "PiCodeRB", "RBCode")   # blind_cfo codes whose un-rotation map is built for the native N = 2048
                                            # no-interleaver packet: rejected (by class name: no blind_cfo import
                                            # here). NOT because rate matching breaks the pi/2 symmetry: J keeps the
                                            # mother pairs (x_2m, x_2m+1) together, so on QPSK (e_2k -> I, e_2k+1 -> Q)
                                            # a pi/2 rotation stays a code automorphism (i -> i xor 1) + a codeword
                                            # after sub-block interleaving and puncturing; only a channel interleaver
                                            # over the E bits (fullsys/blind_fmt chan) breaks it


def crc_matrix(A, C):
    """The CRC generator matrix (A, C) of polar.PolarCode (row i = crc_remainder(e_i)), by the LFSR: row i is
    x^(A - 1 - i + C) mod g(x), MSB first; O(A C) instead of O(A^2)."""
    if C == 0:
        return np.zeros((A, 0), np.uint8)
    g = np.zeros(C + 1, np.uint8)
    for e in CRC_POLYS[C]:
        g[C - e] = 1
    G, r = np.empty((A, C), np.uint8), g[1:].copy()            # r = x^C mod g
    for j in range(A):                                          # r = x^(j + C) mod g -> row A - 1 - j
        G[A - 1 - j] = r
        top = r[0]
        r = np.concatenate([r[1:], np.zeros(1, np.uint8)])
        if top:
            r ^= g[1:]
    return G


def mother_n(K, E, n_max=N_MAX, n_min=N_MIN):
    """log2 of the mother code length (38.212 5.3.1, the 9/8 rule; n_max raised to 12)."""
    ce = int(np.ceil(np.log2(E)))
    n1 = ce - 1 if (E <= 9 / 8 * 2 ** (ce - 1) and K / E < 9 / 16) else ce
    n2 = int(np.ceil(np.log2(8 * K)))
    return max(min(n1, n2, n_max), n_min)


def subblock_interleaver(N):
    """J (N,): y_n = x_{J(n)} (38.212 5.4.1.1, 32 sub-blocks of N/32 bits)."""
    n, B = np.arange(N), N // 32
    return SUBBLOCK_P[(32 * n) // N] * B + n % B


def rm_mode(K, E, N):
    """'repeat' (E > N), 'none' (E == N), 'puncture' (K/E <= 7/16) or 'shorten' (38.212 5.4.1.2)."""
    if E > N:
        return "repeat"
    if E == N:
        return "none"
    return "puncture" if K / E <= 7 / 16 else "shorten"


def extra_count(E, N, std=EXTRA_STD):
    """Puncturing: number of low-index u's u_0.. frozen on top of J(0..U-1): ceil(3N/4 - E/2) if E >= 3N/4 else
    ceil(9N/16 - E/4) (std True: 38.212 / Bioglio), one fewer for Sionna (std False)."""
    c = int(np.ceil(3 * N / 4 - E / 2)) if E >= 3 * N / 4 else int(np.ceil(9 * N / 16 - E / 4))
    return max(c if std else c - 1, 0)


def rm_plan(K, E, n_max=N_MAX, n_min=N_MIN, extra_std=EXTRA_STD, N=None, mode=None, design="pw", design_snr_db=None,
            bps=2):
    """The rate-matched code of K info bits (data + CRC) in E coded bits: dict N, mode, U, J, the u masks (N,)
    rm (frozen because their x positions are removed: punctured-incapable / shortened, no information), extra (the
    puncturing low block beyond rm; disjoint from rm), pre = rm | extra, frozen, rel (frozen by reliability =
    frozen & ~pre), info_pos (K,), and sent_x (N,): the x positions transmitted. N given = override of the mother
    length rule (an A/B, e.g. N = 2048 + repetition); mode 'puncture' / 'shorten' given (E < N) = override of the
    7/16 rule. design 'pw' (default: the rate-matching-blind PW order) or 'ga' (fullsys/polar_design.py: Gaussian
    approximation over the rate-matched channel at Es/N0 design_snr_db, bps coded bits per symbol: QPSK 2, BPSK 1;
    adds ga = its dict m_x, m_u, order, mu); either way the top K outside pre."""
    assert design in ("pw", "ga"), design
    N = 2 ** mother_n(K, E, n_max, n_min) if N is None else int(N)
    U, J = max(N - E, 0), subblock_interleaver(N)
    if mode is None:
        mode = rm_mode(K, E, N)
    else:
        assert mode in ("puncture", "shorten") and E < N, f"mode {mode} needs E < N (E = {E}, N = {N})"
    rm, extra, sent_x = np.zeros(N, bool), np.zeros(N, bool), np.ones(N, bool)
    if mode == "puncture":
        rm[J[:U]] = True
        extra[:extra_count(E, N, extra_std)] = True
        extra &= ~rm
        sent_x[J[:U]] = False
    elif mode == "shorten":
        rm[J[E:]] = True
        sent_x[J[E:]] = False
    pre = rm | extra
    ga = None
    if design == "pw":
        order = pw_reliability(N)                               # least -> most reliable
    else:                                                       # GA over the rate-matched channel (ties: PW)
        assert design_snr_db is not None, "design='ga' needs design_snr_db (Es/N0, dB)"
        from polar_design import ga_design
        ga = ga_design(N, E, mode, J, design_snr_db, bps)
        order = ga["order"]
    rest = order[~pre[order]]
    assert K <= len(rest), f"K = {K} > {len(rest)} positions left after rate-matching pre-freezing (N = {N})"
    info_pos = np.sort(rest[-K:])
    frozen = np.ones(N, bool)
    frozen[info_pos] = False
    return dict(N=N, mode=mode, U=U, J=J, rm=rm, extra=extra, pre=pre, frozen=frozen, rel=frozen & ~pre,
                info_pos=info_pos, sent_x=sent_x, design=design, design_snr_db=design_snr_db, bps=bps, ga=ga)


def _finfo(p):
    return dict(rm=p["rm"], extra=p["extra"], pre=p["pre"], rel=p["rel"], frozen=p["frozen"], mode=p["mode"],
                N=p["N"], n_rm=int(p["rm"].sum()), n_extra=int(p["extra"].sum()), n_pre=int(p["pre"].sum()),
                n_rel=int(p["rel"].sum()))


def frozen_info(K, E, **kw):
    """Frozen u positions (N,) masks for the blind receiver's frozen-penalty early stop (F5 / fz_stop): rm (removed
    x positions: punctured-incapable LLR ~0 / shortened LLR +inf, truly zero CFO information), extra (the puncturing
    low block beyond rm: weak channels, little information), pre = rm | extra, rel (frozen by reliability);
    frozen = pre | rel, mode, N and the counts n_rm, n_extra, n_pre, n_rel. kw as rm_plan."""
    return _finfo(rm_plan(K, E, **kw))


def decode_macs(N, K, E, n_sym, L=8, sf=1, cores=32):
    """MAC model of one rate-matched CA-SCL-L decode (as small_rx _dec_cost / dp8 and blind_vp.MAC, N generalised).
    n_sym (required): channel symbols carrying the E bits (QPSK E / 2, BPSK / pi/2-BPSK E); sf: spreading factor
    (VDE-SAT SF 8: the de-rotation runs on the n_sym sf chips and despreading costs 2 per chip, complex adds).
    Unit costmodel.MAC_UNIT (env BLIND_MAC_UNIT, as blind_vp): ops (default) / legacy (before 2026-11-19).
    llr = D n_sym sf (de-rotation, D = costmodel.DEROT: CMUL 6, legacy 4) + 2 n_sym sf [sf > 1] (despreading) + E
    (scaling) (legacy 6,144 at 1024 QPSK symbols) + max(E - N, 0) (repetition sums);
    path = L (2 N log2 N + N) (ops: f / g 2 per node output as the Fast-SSC metric + 1 per leaf, the decision / PM
    update; partial sums not charged), legacy L N log2 N;
    total = path + llr;  crit (MACs per core, one list path per core, sample-wise steps over `cores`)
    = path / L + K lg (lg + 1) / 2 (bitonic 2L -> L sort per info bit, lg = log2 2L) + llr / cores;
    reencode (the acceptance check: polar transform N/2 log2 N XORs + correlation over the E sent bits 2E, legacy 4E),
    reencode_crit = reencode / cores (charged once per accepted / checked decode, apart from total)."""
    import costmodel as cm
    ops = cm.MAC_UNIT == "ops"
    n_chip = n_sym * sf
    lg = np.log2(2 * L)
    llr = cm.DEROT * n_chip + (2 * n_chip if sf > 1 else 0) + E + max(E - N, 0)
    dec = L * (2 * N * np.log2(N) + N) if ops else L * N * np.log2(N)
    re = N / 2 * np.log2(N) + (2 if ops else 4) * E
    return dict(total=float(dec + llr), crit=float(dec / L + K * lg * (lg + 1) / 2 + llr / cores),
                reencode=float(re), reencode_crit=float(re / cores))


class RMPolarCode:
    """PolarCode, or blind_cfo.PiCode (its pi trick needs the all-ones codeword: puncture / repeat / none only,
    never shorten), on the rate-matched info set; encode / rate_match / rate_recover / decode on E coded bits.
    PiCode4 / PiCodeRB / RBCode are rejected (their un-rotation map is the native packet's; see NO_RM).
    self.code is the N-length code; crc_len 32 (default, 0x04C11DB7) or 16 / 11 / 24 / 6; mode and plan_kw (design
    'pw' default / 'ga', design_snr_db, bps, ...) as rm_plan."""

    def __init__(self, A, E, crc_len=32, list_size=8, code_cls=PolarCode, mode=None, **plan_kw):
        names = [c.__name__ for c in code_cls.__mro__]
        assert not set(names) & set(NO_RM), f"{code_cls.__name__}: rotation automorphism broken by rate matching"
        self.A, self.E, self.C = A, E, crc_len
        self.K = A + crc_len
        self.plan = rm_plan(self.K, E, mode=mode, **plan_kw)
        self.N, self.mode, self.U, self.J = self.plan["N"], self.plan["mode"], self.plan["U"], self.plan["J"]
        assert not ("PiCode" in names and self.mode == "shorten"), \
            f"{code_cls.__name__} under shortening: no all-ones codeword, the pi trick would accept wrong words"
        self.code = code_cls(self.N, A, crc_len, list_size, info_pos=self.plan["info_pos"],
                             crc_G=crc_matrix(A, crc_len))
        assert np.array_equal(self.code.frozen, self.plan["frozen"])

    def frozen_info(self):
        """As the module's frozen_info for this code."""
        return _finfo(self.plan)

    def encode(self, data):
        """data (B, A) -> mother codewords x (B, N)."""
        return self.code.encode(data)

    def rate_match(self, x):
        """x (B, N) -> e (B, E): interleave y = x[J], then puncture (y[U:]) / shorten (y[:E]) / repeat (y[k mod N])."""
        y = x[..., self.J]
        if self.mode == "puncture":
            return y[..., self.U:]
        if self.mode == "shorten":
            return y[..., :self.E]
        return y[..., np.arange(self.E) % self.N]               # repeat / none

    def encode_rm(self, data):
        """data (B, A) -> transmitted coded bits e (B, E)."""
        return self.rate_match(self.encode(data))

    def rate_recover(self, llr_e):
        """llr_e (B, E) -> mother LLRs (B, N): punctured 0, shortened +LLR_BIG (known zero), repeated summed."""
        B = llr_e.shape[0]
        y = np.zeros((B, self.N), dtype=np.float64)
        if self.mode == "puncture":
            y[:, self.U:] = llr_e
        elif self.mode == "shorten":
            y[:, :self.E] = llr_e
            y[:, self.E:] = LLR_BIG
        else:
            for s in range(0, self.E, self.N):                  # MRC of the copies (none: one copy)
                m = min(self.N, self.E - s)
                y[:, :m] += llr_e[:, s:s + m]
        x = np.empty_like(y)
        x[:, self.J] = y
        return x

    def decode(self, llr_e, return_info=False):
        """llr_e (B, E) channel LLRs -> self.code.decode on the recovered N LLRs."""
        return self.code.decode(self.rate_recover(llr_e), return_info=return_info)

    def macs(self, n_sym, L=None, sf=1, cores=32):
        """decode_macs of this code (n_sym required: E / 2 QPSK, E BPSK)."""
        return decode_macs(self.N, self.K, self.E, n_sym, L or self.code.list_size, sf, cores)
