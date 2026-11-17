"""
LTE turbo code (3GPP TS 36.212 5.1.3.2) with LTE circular-buffer rate matching (5.1.4.1): the UL-SCH channel code of
NB-IoT NPUSCH format 1 (36.212 6.3.2), encoder + rate matcher + batch BCJR decoder.

    PCCC    : 2 identical 8-state RSCs, G(D) = [1, g1(D)/g0(D)], g0 = 1 + D^2 + D^3 (feedback), g1 = 1 + D + D^3,
              initial state 0. = the turbo_vde trellis (d = g0, n0 = g1; its second parity n1 unused here)
    QPP     : c'_i = c_{Pi(i)}, Pi(i) = (f1 i + f2 i^2) mod K, (f1, f2) of Table 5.1.3-3 (QPP_TABLE, 188 sizes)
    Tail    : 3 clocks per RSC, input = feedback (register -> 0): x_K.. x_K+2 / z_K.. z_K+2 (RSC 1), x'_K.. / z'_K..
              (RSC 2); d(0)_K.. = x_K z_K+1 x'_K z'_K+1, d(1) = z_K x_K+2 z'_K x'_K+2, d(2) = x_K+1 z_K+2 x'_K+1 z'_K+2
    Streams : d(0) = x (systematic), d(1) = z, d(2) = z', D = K + 4 each: the rate-1/3 mother code, 3K + 12 bits
    RM      : sub-block interleaver, 32 columns, R = ceil(D / 32) rows, N_D = 32 R - D leading NULLs, column pattern
              SUBBLOCK_P (Table 5.1.4-1), read by columns: v_k = y_{P(k // R) + 32 (k mod R)} (d(0), d(1)),
              v(2)_k = y_{(P(k // R) + 32 (k mod R) + 1) mod K_Pi}; buffer w = v(0) | v(1)_0 v(2)_0 v(1)_1 ...,
              K_w = 3 K_Pi, N_cb = K_w (UL-SCH), k0 = R (2 ceil(N_cb / 8R) rv + 2), E bits read circularly from k0,
              NULLs skipped (5.1.4.1.2). Filler bits (F > 0): d(0), d(1) NULL at k < F (5.1.3.2.1)
    Decoder : BCJR on both RSCs (K data + 3 tail steps, terminated at both ends), max-log-MAP with the extrinsic
              scaled by `scale` (default 0.75 = AFF3CT LTE / LTE_VEC) or exact log-MAP (scale 1); a priori exchange
              through Pi; optional early stop by a callable (CRC) after each full iteration from `crc_start`.
              Rate recovery: LLRs of repeated bits summed, punctured (unsent) bits 0, filler systematic +LLR_BIG.

LLR convention as polar.py: LLR = log P(bit = 0) / P(bit = 1); branch metric of bit b = -b L.
Ops by fullsys/costmodel.py (binary 8-state trellis, 2 soft inputs per step: systematic + a priori, parity).
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from fullsys import costmodel                                                        # noqa: E402
from fullsys.turbo_vde import NEXT, Y0, FB, PREV_S, PREV_U, NEG, rsc_encode, qpp_interleaver   # noqa: E402

ASSUMPTIONS = [
    "QPP (f1, f2) = TS 36.212 Table 5.1.3-3 as copied in NVIDIA Sionna src/sionna/phy/fec/turbo/coeffs/"
    "turbo_coeffs.csv (188 rows, fetched 2026-11-17); the self-test checks the encoder bit-exactly against Sionna's "
    "reference codewords (test/codes/turbo/ref_k{40,112,168,432}, 'pre-encoded codewords from a reference "
    "implementation'), which exercises those 4 rows; the other rows are checked to be permutations.",
    "Constituent RSC = turbo_vde trellis (state 4 a_{t-1} + 2 a_{t-2} + a_{t-3}, a_t = u_t + a_{t-2} + a_{t-3}, "
    "z_t = a_t + a_{t-1} + a_{t-3}); tail input = feedback a_{t-2} + a_{t-3}.",
    "Rate matching formulas (sub-block interleaver incl. the d(2) +1 shift, k0, N_cb = K_w for UL-SCH) from TS 36.212 "
    "5.1.4.1.1-2: the itecspec mirror shows the text and Table 5.1.4-1 but drops the equations, so the equations are "
    "as recalled [mem]; the self-test checks the structural properties (E = 3K + 12 at rv 0 is a permutation of the "
    "mother codeword, NULLs never sent, k0 = 2R).",
    "Max-log extrinsic scaling 0.75 in every half iteration (AFF3CT --dec-sf-type LTE / LTE_VEC: 'Select a 0.75 SF'); "
    "log-MAP unscaled. The decision is the unscaled APP L_s + L_e1 + L_e2.",
    "Early stop: CRC checked after every full iteration from crc_start (NB-IoT formats 1, AFF3CT validation 2 = its "
    "--dec-crc-start default); a passing block is frozen, the rest continue up to `iters`.",
]

# TS 36.212 Table 5.1.3-3 (K, f1, f2), i = 1..188 (Sionna turbo_coeffs.csv)
QPP_TABLE = (
    (40, 3, 10), (48, 7, 12), (56, 19, 42), (64, 7, 16), (72, 7, 18), (80, 11, 20), (88, 5, 22), (96, 11, 24),
    (104, 7, 26), (112, 41, 84), (120, 103, 90), (128, 15, 32), (136, 9, 34), (144, 17, 108), (152, 9, 38),
    (160, 21, 120), (168, 101, 84), (176, 21, 44), (184, 57, 46), (192, 23, 48), (200, 13, 50), (208, 27, 52),
    (216, 11, 36), (224, 27, 56), (232, 85, 58), (240, 29, 60), (248, 33, 62), (256, 15, 32), (264, 17, 198),
    (272, 33, 68), (280, 103, 210), (288, 19, 36), (296, 19, 74), (304, 37, 76), (312, 19, 78), (320, 21, 120),
    (328, 21, 82), (336, 115, 84), (344, 193, 86), (352, 21, 44), (360, 133, 90), (368, 81, 46), (376, 45, 94),
    (384, 23, 48), (392, 243, 98), (400, 151, 40), (408, 155, 102), (416, 25, 52), (424, 51, 106), (432, 47, 72),
    (440, 91, 110), (448, 29, 168), (456, 29, 114), (464, 247, 58), (472, 29, 118), (480, 89, 180), (488, 91, 122),
    (496, 157, 62), (504, 55, 84), (512, 31, 64), (528, 17, 66), (544, 35, 68), (560, 227, 420), (576, 65, 96),
    (592, 19, 74), (608, 37, 76), (624, 41, 234), (640, 39, 80), (656, 185, 82), (672, 43, 252), (688, 21, 86),
    (704, 155, 44), (720, 79, 120), (736, 139, 92), (752, 23, 94), (768, 217, 48), (784, 25, 98), (800, 17, 80),
    (816, 127, 102), (832, 25, 52), (848, 239, 106), (864, 17, 48), (880, 137, 110), (896, 215, 112),
    (912, 29, 114), (928, 15, 58), (944, 147, 118), (960, 29, 60), (976, 59, 122), (992, 65, 124), (1008, 55, 84),
    (1024, 31, 64), (1056, 17, 66), (1088, 171, 204), (1120, 67, 140), (1152, 35, 72), (1184, 19, 74),
    (1216, 39, 76), (1248, 19, 78), (1280, 199, 240), (1312, 21, 82), (1344, 211, 252), (1376, 21, 86),
    (1408, 43, 88), (1440, 149, 60), (1472, 45, 92), (1504, 49, 846), (1536, 71, 48), (1568, 13, 28),
    (1600, 17, 80), (1632, 25, 102), (1664, 183, 104), (1696, 55, 954), (1728, 127, 96), (1760, 27, 110),
    (1792, 29, 112), (1824, 29, 114), (1856, 57, 116), (1888, 45, 354), (1920, 31, 120), (1952, 59, 610),
    (1984, 185, 124), (2016, 113, 420), (2048, 31, 64), (2112, 17, 66), (2176, 171, 136), (2240, 209, 420),
    (2304, 253, 216), (2368, 367, 444), (2432, 265, 456), (2496, 181, 468), (2560, 39, 80), (2624, 27, 164),
    (2688, 127, 504), (2752, 143, 172), (2816, 43, 88), (2880, 29, 300), (2944, 45, 92), (3008, 157, 188),
    (3072, 47, 96), (3136, 13, 28), (3200, 111, 240), (3264, 443, 204), (3328, 51, 104), (3392, 51, 212),
    (3456, 451, 192), (3520, 257, 220), (3584, 57, 336), (3648, 313, 228), (3712, 271, 232), (3776, 179, 236),
    (3840, 331, 120), (3904, 363, 244), (3968, 375, 248), (4032, 127, 168), (4096, 31, 64), (4160, 33, 130),
    (4224, 43, 264), (4288, 33, 134), (4352, 477, 408), (4416, 35, 138), (4480, 233, 280), (4544, 357, 142),
    (4608, 337, 480), (4672, 37, 146), (4736, 71, 444), (4800, 71, 120), (4864, 37, 152), (4928, 39, 462),
    (4992, 127, 234), (5056, 39, 158), (5120, 39, 80), (5184, 31, 96), (5248, 113, 902), (5312, 41, 166),
    (5376, 251, 336), (5440, 43, 170), (5504, 21, 86), (5568, 43, 174), (5632, 45, 176), (5696, 45, 178),
    (5760, 161, 120), (5824, 89, 182), (5888, 323, 184), (5952, 47, 186), (6016, 23, 94), (6080, 47, 190),
    (6144, 263, 480))
QPP = {k: (f1, f2) for k, f1, f2 in QPP_TABLE}
SUBBLOCK_P = np.array([0, 16, 8, 24, 4, 20, 12, 28, 2, 18, 10, 26, 6, 22, 14, 30,
                       1, 17, 9, 25, 5, 21, 13, 29, 3, 19, 11, 27, 7, 23, 15, 31])   # Table 5.1.4-1
C_TC = 32                                      # sub-block interleaver columns
NULL = -1                                      # dummy / filler marker in the index maps
LLR_BIG = 1e4                                  # LLR of a known-zero (filler) systematic bit
SCALE_MAXLOG = 0.75                            # AFF3CT LTE / LTE_VEC extrinsic scaling
_U = np.array([0, 1])


def tail_map():
    """(3, 4) index into the 12 tail bits T = x_K z_K x_K+1 z_K+1 x_K+2 z_K+2 x'_K z'_K x'_K+1 z'_K+1 x'_K+2 z'_K+2:
    d(i)_{K+j} = T[3 j + i] (5.1.3.2.2)."""
    return 3 * np.arange(4)[None] + np.arange(3)[:, None]


def subblock_perm(D):
    """(perm01, perm2, R): v_k = y[perm[k]] for the 32-column interleaver of D bits; y = (N_D NULLs, d)."""
    R = -(-D // C_TC)
    KP = R * C_TC
    k = np.arange(KP)
    p01 = SUBBLOCK_P[k // R] + C_TC * (k % R)
    return p01, (p01 + 1) % KP, R


def rm_index(K, E, rv=0, F=0):
    """
    Rate-matching index map (E,): e_k = d_flat[idx[k]], d_flat = (d(0) | d(1) | d(2)) of length 3 (K + 4).
    Returns dict(idx, R, K_Pi, K_w, N_cb, k0, n_valid, w (K_w,) flat index or NULL).
    """
    D = K + 4
    p01, p2, R = subblock_perm(D)
    KP = R * C_TC
    ND = KP - D
    y = np.full((3, KP), NULL, np.int64)
    for i in range(3):
        y[i, ND:] = i * D + np.arange(D)
    if F:                                                      # filler: d(0), d(1) NULL at k < F
        y[0, ND:ND + F] = NULL
        y[1, ND:ND + F] = NULL
    v0, v1, v2 = y[0, p01], y[1, p01], y[2, p2]
    w = np.concatenate([v0, np.stack([v1, v2], 1).ravel()])
    Kw = 3 * KP
    Ncb = Kw                                                   # UL-SCH (5.1.4.1.2)
    k0 = R * (2 * int(np.ceil(Ncb / (8 * R))) * rv + 2)
    order = np.roll(w, -k0)                                    # circular read from k0 (N_cb = K_w)
    valid = order[order != NULL]
    idx = valid[np.arange(E) % len(valid)]                     # E > valid: wrap around (repetition)
    return dict(idx=idx, R=R, K_Pi=KP, K_w=Kw, N_cb=Ncb, k0=k0, n_valid=int(len(valid)), w=w)


class TurboLTE:
    """LTE turbo code of K bits (Table 5.1.3-3 size, F leading filler bits) with RV `rv` rate matching to E bits;
    E = None: no rate matching (the 3 streams d (B, 3, K + 4) in and out); idx = an explicit selection map into
    d_flat (e.g. the AFF3CT puncturing pattern) instead of the LTE rate matcher."""

    def __init__(self, K, E=None, rv=0, F=0, idx=None):
        assert K in QPP, f"K = {K} is not a Table 5.1.3-3 size"
        self.K, self.F, self.rv = K, F, rv
        self.f1, self.f2 = QPP[K]
        self.pi = qpp_interleaver(K, self.f1, self.f2)
        assert np.array_equal(np.sort(self.pi), np.arange(K)), f"QPP K {K} not a permutation"
        self.ipi = np.argsort(self.pi)
        self.D = K + 4
        self.E, self.rm, self.idx = E, None, None
        if idx is not None:
            self.idx = np.asarray(idx, np.int64)
            self.E = len(self.idx)
        elif E is not None:
            self.rm = rm_index(K, E, rv, F)
            self.idx = self.rm["idx"]

    # ---- encoder (5.1.3.2) ----
    def encode(self, c):
        """c (B, K) {0,1} (filler = 0 at k < F) -> d (B, 3, K + 4) int8."""
        c = np.asarray(c, np.int8)
        B, K = c.shape
        z1, _, tx1, tz1, _ = rsc_encode(c)
        z2, _, tx2, tz2, _ = rsc_encode(c[:, self.pi])
        T = np.stack([tx1[:, 0], tz1[:, 0], tx1[:, 1], tz1[:, 1], tx1[:, 2], tz1[:, 2],
                      tx2[:, 0], tz2[:, 0], tx2[:, 1], tz2[:, 1], tx2[:, 2], tz2[:, 2]], 1)
        d = np.empty((B, 3, K + 4), np.int8)
        d[:, 0, :K], d[:, 1, :K], d[:, 2, :K] = c, z1, z2
        d[:, :, K:] = T[:, tail_map()]
        return d

    def rate_match(self, d):
        """d (B, 3, K + 4) -> e (B, E) (5.1.4.1)."""
        return d.reshape(len(d), -1)[:, self.idx]

    def encode_rm(self, c):
        return self.rate_match(self.encode(c))

    def rate_recover(self, llr):
        """llr (B, E) -> stream LLRs (B, 3, K + 4): repeated copies summed, unsent 0, filler systematic +LLR_BIG."""
        B = llr.shape[0]
        full = np.zeros((3 * self.D, B))
        np.add.at(full, self.idx, np.asarray(llr, float).T)
        L = full.T.reshape(B, 3, self.D)
        if self.F:
            L[:, 0, :self.F] = LLR_BIG
        return L

    # ---- decoder ----
    def decode(self, Ld, iters=8, algo="maxlog", scale=None, stop=None, crc_start=1, freeze=True):
        """
        Ld (B, 3, K + 4) stream LLRs -> (bits (B, K) int8, iterations used (B,), first pass (B,) (first iteration whose
        decision passed `stop`, 0 = never; = used with early stop), app LLR (B, K)).
        stop(bits_active (A, K), rows (A,)) -> bool (A,), checked from iteration crc_start: freeze those rows (CRC
        early stop) if freeze, else only record the first pass (all blocks run `iters`).
        scale: extrinsic scaling (default 0.75 max-log, 1.0 log-MAP).
        """
        if scale is None:
            scale = SCALE_MAXLOG if algo == "maxlog" else 1.0
        K = self.K
        Ld = np.asarray(Ld, float)
        B = Ld.shape[0]
        tm = tail_map()
        T = np.empty((B, 12))
        T[:, tm.ravel()] = Ld[:, :, K:].reshape(B, 12)
        Ls = Ld[:, 0, :K]
        Ls2 = Ls[:, self.pi]
        p1 = np.concatenate([Ld[:, 1, :K], T[:, [1, 3, 5]]], 1)            # z_0..z_K+2
        p2 = np.concatenate([Ld[:, 2, :K], T[:, [7, 9, 11]]], 1)           # z'_0..z'_K+2
        t1, t2 = T[:, [0, 2, 4]], T[:, [6, 8, 10]]                          # tail systematic x, x'
        bits = np.zeros((B, K), np.int8)
        app = np.zeros((B, K))
        used = np.full(B, iters, int)
        first = np.zeros(B, int)
        act = np.arange(B)
        La1 = np.zeros((B, K))
        for it in range(1, iters + 1):
            a = act
            Le1 = self._siso(Ls[a] + La1[a], p1[a], t1[a], algo)
            Le2 = self._siso(Ls2[a] + scale * Le1[:, self.pi], p2[a], t2[a], algo)
            Le2d = Le2[:, self.ipi]
            La1[a] = scale * Le2d
            Lapp = Ls[a] + Le1 + Le2d
            hb = (Lapp < 0).astype(np.int8)
            bits[a], app[a] = hb, Lapp
            if stop is not None and it >= crc_start:
                done = np.asarray(stop(hb, a), bool)
                first[a[done & (first[a] == 0)]] = it
                if freeze and it < iters:
                    used[a[done]] = it
                    act = a[~done]
                    if len(act) == 0:
                        break
        return bits, used, first, app

    def _siso(self, Lsys, Lpar, Ltail, algo):
        """One BCJR pass: Lsys (A, K) systematic + a priori, Lpar (A, K + 3), Ltail (A, 3) -> extrinsic (A, K)."""
        K = self.K
        A = Lsys.shape[0]
        T = K + 3
        gp = -(Y0[None, None] * Lpar[:, :, None, None])                    # (A, T, 8, 2)
        sysl = np.concatenate([Lsys, Ltail], 1)                             # tail steps: their own x LLR
        g = gp - _U[None, None, None, :] * sysl[:, :, None, None]
        g[:, K:] += np.where(_U[None, :] == FB[:, None], 0.0, NEG)          # tail: only the feedback input
        if algo == "maxlog":
            red2 = np.maximum
            redn = lambda x, ax: x.max(axis=ax)
        else:
            red2 = np.logaddexp
            redn = lambda x, ax: np.logaddexp.reduce(x, axis=ax)
        alpha = np.empty((A, T + 1, 8))
        alpha[:, 0] = NEG
        alpha[:, 0, 0] = 0.0
        for t in range(T):
            c = alpha[:, t, :, None] + g[:, t]
            nx = red2(c[:, PREV_S[:, 0], PREV_U[:, 0]], c[:, PREV_S[:, 1], PREV_U[:, 1]])
            alpha[:, t + 1] = nx - nx.max(1, keepdims=True)
        beta = np.empty((A, T + 1, 8))
        beta[:, T] = NEG
        beta[:, T, 0] = 0.0                                                 # terminated (state 0 after the tail)
        for t in range(T - 1, -1, -1):
            c = g[:, t] + beta[:, t + 1][:, NEXT]
            b = red2(c[:, :, 0], c[:, :, 1])
            beta[:, t] = b - b.max(1, keepdims=True)
        m = alpha[:, :K, :, None] + gp[:, :K] + beta[:, 1:K + 1][:, :, NEXT]
        return redn(m[..., 0], 2) - redn(m[..., 1], 2)


def macs(K, iters, algo="maxlog", early=True, scaled=None):
    """Decoder ops per block (costmodel.turbo_ops, 8 states, 2 soft inputs per step, 3 tail steps per SISO);
    iters may be an array (iterations used)."""
    return costmodel.turbo_ops(K, iters, algo, n_states=8, n_soft=2, tail_steps=3, early=early, scaled=scaled)


def crit(K, iters, algo="maxlog", early=True, scaled=None, model="state"):
    """32-core critical path of one block decode (costmodel.crit_turbo, state-parallel by default)."""
    return costmodel.crit_turbo(K, iters, algo, n_states=8, n_soft=2, tail_steps=3, early=early, scaled=scaled,
                                model=model)
