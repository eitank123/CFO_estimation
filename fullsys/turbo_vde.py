"""
VDE turbo code (ITU-R M.2092-2 A2-1.2.4, = the 3GPP2 / DVB-SH 8-state two-parity turbo code with the CCSDS-law
interleaver and VDE's k1, k2, primes per Link ID), encoder + batch BCJR decoder.

    RSC     : G(D) = [1, n0/d, n1/d], d = 1 + D^2 + D^3, n0 = 1 + D + D^3, n1 = 1 + D + D^2 + D^3 (Fig. 8)
              a_t = u_t + a_{t-2} + a_{t-3};  y0 = a_t + a_{t-1} + a_{t-3};  y1 = a_t + a_{t-1} + a_{t-2} + a_{t-3}
    Tail    : 6 clocks, switch (b): input = feedback a_{t-2} + a_{t-3} (register -> 0); clocks 1-3 RSC1 (X Y0 Y1),
              clocks 4-6 RSC2 (X' Y'0 Y'1), "X output first"; copies per Table 6 (2 = sent twice, consecutive)
    Interl. : k = k1 k2, s = 1..k: m = (s-1) mod 2, i = floor((s-1)/(2 k2)), j = floor((s-1)/2) - i k2,
              t = (19 i + 1) mod (k1/2), q = t mod 8 + 1, c = (p_q j + 21 m) mod k2, pi(s) = 2 (t + c k1/2 + 1) - m;
              u'_s = u_{pi(s)}  (A2-1.2.4.3)
    Order   : per data clock X Y0 Y1 X' Y'0 Y'1 masked by Table 5 (period = clock mod Lp), then the 6 tail clocks
    Decoder : BCJR on both RSCs (data + 3 tail steps each, terminated), max-log-MAP (extrinsic x scale, default 0.75)
              or exact log-MAP (Jacobian log, scale 1); a priori exchange through pi; optional early stop by a callable
              (CRC) after each full iteration. Punctured -> LLR 0, repeated copies -> LLR sum.

LLR convention as polar.py: LLR = log P(bit = 0) / P(bit = 1); branch metric of bit b = -b L.
Tables 5 / 6 below are the PDF layout reading (Rec. pp. 18-19, PDF pp. 20-21); the .txt Table 6 is shifted one row.
"""

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from fullsys import costmodel  # noqa: E402

DEFAULT_PRIMES = (31, 37, 43, 47, 53, 59, 61, 67)              # Table 4 "default" (CCSDS 131.0-B-2 set)

PUNCT = {                                                       # Table 5: one 6-digit group per data clock (X Y0 Y1 X' Y'0 Y'1)
    "0": ["111011"],
    "1": ["101011", "111011", "111001", "111011"],
    "2": ["111001", "110011"],
    "3": ["101001", "101011", "101001", "111001"],
    "4": ["110010"],
    "5": ["100000", "101001", "001001", "101001", "101001", "001001",
          "101001", "101001", "001001", "101001", "101001", "001001"],
    "6": ["110000", "100010"],
    "7": ["100000", "100000", "100000", "101001"],
    "7a": ["100000", "100000", "100000", "110010"],
    "7b": ["100000", "110000", "100000", "100010"],
    "8": ["101000", "100000", "100000", "100000", "100000", "100001"],
    "9": ["100000", "110000", "100010", "100000", "100000", "100000", "100000", "100000", "100000", "100000"],
}

TAIL = {                                                        # Table 6: copies per tail clock 1..6 (X Y0 Y1 X' Y'0 Y'1)
    "0": ["311000", "311000", "311000", "000311", "000311", "000311"],
    "1": ["311000", "311000", "211000", "000211", "000211", "000311"],
    "2": ["211000", "211000", "211000", "000211", "000211", "000211"],
    "2a": ["111000", "111000", "111000", "000111", "000111", "000111"],
    "2b": ["111000", "111000", "110000", "000111", "000111", "000110"],
    "2c": ["110000", "110000", "110000", "000110", "000110", "000110"],
    "2d": ["110000", "100000", "100000", "000110", "000100", "000100"],
    "2e": ["211000", "211000", "210000", "000211", "000211", "000200"],
    "3": ["111000", "211000", "211000", "000211", "000111", "000111"],
    "4": ["210000", "210000", "210000", "000210", "000210", "000210"],
    "4a": ["210000", "210000", "200000", "000210", "000210", "000010"],
    "5": ["111000", "111000", "101000", "000111", "000111", "000101"],
    "6": ["110000", "110000", "110000", "000110", "000110", "000110"],
    "6a": ["110000", "110000", "100000", "000110", "000110", "000100"],
    "6b": ["110000", "100000", "100000", "000110", "000100", "000100"],
    "7": ["100000", "101000", "101000", "000100", "000101", "000100"],
    "7a": ["110000", "100000", "100000", "000110", "000100", "000100"],
    "7b": ["110000", "110000", "110000", "000110", "000110", "000110"],
    "8": ["101000", "101000", "101000", "000101", "000101", "000101"],
    "8a": ["101000", "101000", "101000", "000101", "000101", "000100"],
    "8b": ["101000", "101000", "100000", "000101", "000101", "000100"],
    "9": ["110000", "100000", "100000", "000110", "000100", "000100"],
}

OPS_PER_STEP = {a: costmodel.siso_step_ops(a)["total"] for a in ("maxlog", "logmap")}   # costmodel.py: 118 / 177
NEG = -1e9                                    # log-domain "minus infinity" (finite: no inf - inf)

# ---- trellis: state s = 4 a_{t-1} + 2 a_{t-2} + a_{t-3} ----
_S = np.arange(8)
_A1, _A2, _A3 = (_S >> 2) & 1, (_S >> 1) & 1, _S & 1
_U = np.array([0, 1])
_A = _U[None, :] ^ (_A2 ^ _A3)[:, None]                         # a_t (8, 2)
NEXT = (_A << 2) | (_S[:, None] >> 1)                           # next state (8, 2)
Y0 = _A ^ _A1[:, None] ^ _A3[:, None]                           # n0 = 1 + D + D^3
Y1 = _A ^ _A1[:, None] ^ _A2[:, None] ^ _A3[:, None]            # n1 = 1 + D + D^2 + D^3
FB = _A2 ^ _A3                                                  # tail input (switch (b)): makes a_t = 0
PREV_S = np.zeros((8, 2), int)                                  # the two (state, input) pairs entering each state
PREV_U = np.zeros((8, 2), int)
_cnt = np.zeros(8, int)
for _s in range(8):
    for _u in range(2):
        _n = NEXT[_s, _u]
        PREV_S[_n, _cnt[_n]], PREV_U[_n, _cnt[_n]] = _s, _u
        _cnt[_n] += 1
assert (_cnt == 2).all()


def ccsds_interleaver(k1, k2, primes=DEFAULT_PRIMES):
    """pi (k,) 0-based: u' = u[pi] (A2-1.2.4.3; the s-th bit read out is the pi(s)-th input bit)."""
    assert k1 % 2 == 0, "k1 must be even"
    s = np.arange(1, k1 * k2 + 1)
    m = (s - 1) % 2
    i = (s - 1) // (2 * k2)
    j = (s - 1) // 2 - i * k2
    t = (19 * i + 1) % (k1 // 2)
    q = t % 8 + 1
    p = np.asarray(primes)[q - 1]
    c = (p * j + 21 * m) % k2
    return 2 * (t + c * (k1 // 2) + 1) - m - 1


def srandom_interleaver(k, S=None, seed=0, tries=1000):
    """S-random (spread) permutation: |pi(i) - pi(j)| > S whenever 0 < i - j <= S; S default floor(sqrt(k/2))."""
    S = int(np.floor(np.sqrt(k / 2))) if S is None else S
    rng = np.random.default_rng(seed)
    for _ in range(tries):
        left, pi = list(rng.permutation(k)), []
        for i in range(k):
            for c, v in enumerate(left):
                if all(abs(v - w) > S for w in pi[-S:]):
                    pi.append(left.pop(c))
                    break
            else:
                break
        if len(pi) == k:
            return np.array(pi)
    raise RuntimeError(f"no S-random permutation, k {k} S {S}")


def qpp_interleaver(k, f1, f2):
    """LTE QPP (TS 36.212 5.1.3.2.3): pi(i) = (f1 i + f2 i^2) mod k, u' = u[pi]."""
    i = np.arange(k, dtype=np.int64)
    return (f1 * i + f2 * i * i) % k


def rsc_encode(u):
    """u (B, k) {0,1} -> y0, y1 (B, k), tail x, y0, y1 (B, 3) (switch (b) for 3 clocks: register ends in 0)."""
    B, k = u.shape
    a1 = np.zeros(B, np.int8); a2 = np.zeros(B, np.int8); a3 = np.zeros(B, np.int8)
    y0 = np.empty((B, k), np.int8); y1 = np.empty((B, k), np.int8)
    for t in range(k):
        a = u[:, t] ^ a2 ^ a3
        y0[:, t] = a ^ a1 ^ a3
        y1[:, t] = a ^ a1 ^ a2 ^ a3
        a1, a2, a3 = a, a1, a2
    tx, ty0, ty1 = (np.empty((B, 3), np.int8) for _ in range(3))
    for t in range(3):
        x = a2 ^ a3                                             # feedback value fed in -> a = 0
        tx[:, t], ty0[:, t], ty1[:, t] = x, a1 ^ a3, a1 ^ a2 ^ a3
        a1, a2, a3 = np.zeros_like(a1), a1, a2
    assert not (a1 | a2 | a3).any()
    return y0, y1, tx, ty0, ty1


class TurboVDE:
    """
    k info bits (incl. CRC), interleaver law k1 x k2 / primes (or an explicit permutation `perm`), puncturing ID
    `punct` (Table 5), tail ID `tail` (Table 6; None = no tail bits, Link 34: the trellis is then not terminated).
    n = coded bits (data + tail). Row layout of the 6-stream array: k data clocks, then tail clocks 1..6.
    """

    def __init__(self, k, k1=None, k2=None, primes=DEFAULT_PRIMES, punct="2", tail="2e", perm=None):
        self.k, self.punct, self.tail = k, punct, tail
        if perm is None:
            assert k1 * k2 == k, f"k1 k2 = {k1} x {k2} != k = {k}"
            perm = ccsds_interleaver(k1, k2, primes)
        self.pi = np.asarray(perm, int)
        assert np.array_equal(np.sort(self.pi), np.arange(k)), "interleaver is not a permutation"
        self.ipi = np.argsort(self.pi)                          # deinterleave: x = x'[ipi]
        pat = PUNCT[punct]
        Lp = len(pat)
        cnt = np.zeros((k + 6, 6), int)
        cnt[:k] = np.array([[int(c) for c in pat[t % Lp]] for t in range(k)])
        if tail is not None:
            cnt[k:] = np.array([[int(c) for c in g] for g in TAIL[tail]])
        self.cnt = cnt
        self.src = np.repeat(np.arange((k + 6) * 6), cnt.ravel())   # output bit n = stream array flat index src[n]
        self.n = len(self.src)
        self.n_data = int(cnt[:k].sum())                        # A2-1.2.4.5: floor(k/Lp) Lp/r + ones of first R groups
        self.terminated = tail is not None

    def streams(self, u):
        """(B, k + 6, 6) bit array of all encoder outputs (X Y0 Y1 X' Y'0 Y'1 per clock)."""
        u = np.asarray(u, np.int8)
        B, k = u.shape
        y0, y1, tx, ty0, ty1 = rsc_encode(u)
        up = u[:, self.pi]
        z0, z1, sx, sy0, sy1 = rsc_encode(up)
        st = np.zeros((B, k + 6, 6), np.int8)
        st[:, :k] = np.stack([u, y0, y1, up, z0, z1], axis=2)
        st[:, k:k + 3, 0], st[:, k:k + 3, 1], st[:, k:k + 3, 2] = tx, ty0, ty1
        st[:, k + 3:, 3], st[:, k + 3:, 4], st[:, k + 3:, 5] = sx, sy0, sy1
        return st

    def encode(self, u):
        """u (B, k) -> codeword (B, n)."""
        return self.streams(u).reshape(len(u), -1)[:, self.src]

    def _derate(self, llr):
        """(B, n) channel LLRs -> (B, k + 6, 6) stream LLRs (punctured 0, repeated copies summed)."""
        B = llr.shape[0]
        full = np.zeros(((self.k + 6) * 6, B))
        np.add.at(full, self.src, llr.T)
        return full.T.reshape(B, self.k + 6, 6)

    def decode(self, llr, iters=8, algo="maxlog", scale=None, stop=None):
        """
        llr (B, n) -> (bits (B, k) int8, iterations used (B,) int, app LLR (B, k)).
        stop(bits_active (A, k), rows (A,)) -> bool (A,): freeze those rows after the current iteration (CRC early
        stop). scale: extrinsic scaling (default 0.75 max-log, 1.0 log-MAP).
        """
        if scale is None:
            scale = 0.75 if algo == "maxlog" else 1.0
        k = self.k
        L = self._derate(np.asarray(llr, float))
        B = L.shape[0]
        Ls = L[:, :k, 0]
        Ls2 = Ls[:, self.pi] + L[:, :k, 3]                      # RSC2 systematic: interleaved X (+ X' if ever sent)
        T = k + 3
        p1 = (np.concatenate([L[:, :k, 1], L[:, k:k + 3, 1]], 1), np.concatenate([L[:, :k, 2], L[:, k:k + 3, 2]], 1))
        p2 = (np.concatenate([L[:, :k, 4], L[:, k + 3:, 4]], 1), np.concatenate([L[:, :k, 5], L[:, k + 3:, 5]], 1))
        t1, t2 = L[:, k:k + 3, 0], L[:, k + 3:, 3]              # tail systematic LLRs (RSC1, RSC2)
        bits = np.zeros((B, k), np.int8)
        app = np.zeros((B, k))
        used = np.full(B, iters, int)
        act = np.arange(B)
        La1 = np.zeros((B, k))
        for it in range(1, iters + 1):
            a = act
            Le1 = self._siso(Ls[a] + La1[a], (p1[0][a], p1[1][a]), t1[a], algo)
            La2 = scale * Le1[:, self.pi]
            Le2 = self._siso(Ls2[a] + La2, (p2[0][a], p2[1][a]), t2[a], algo)
            Le2d = Le2[:, self.ipi]
            La1[a] = scale * Le2d
            Lapp = Ls[a] + Le1 + Le2d
            hb = (Lapp < 0).astype(np.int8)
            bits[a], app[a] = hb, Lapp
            if stop is not None and it < iters:
                done = np.asarray(stop(hb, a), bool)
                used[a[done]] = it
                act = a[~done]
                if len(act) == 0:
                    break
        return bits, used, app

    def _siso(self, Lsys, par, Ltail, algo):
        """One BCJR pass: Lsys (A, k) systematic + a priori, par = (Lp0, Lp1) (A, k + 3), Ltail (A, 3) -> Le (A, k)."""
        k = self.k
        A = Lsys.shape[0]
        T = k + 3
        gp = -(Y0[None, None] * par[0][:, :, None, None] + Y1[None, None] * par[1][:, :, None, None])  # (A, T, 8, 2)
        sysl = np.concatenate([Lsys, Ltail], 1)                 # tail steps: their own X LLR, no a priori
        g = gp - _U[None, None, None, :] * sysl[:, :, None, None]
        tailmask = np.where(_U[None, :] == FB[:, None], 0.0, NEG)   # tail: only the feedback input is allowed
        g[:, k:] += tailmask
        if algo == "maxlog":
            red2 = lambda x, y: np.maximum(x, y)
            redn = lambda x, ax: x.max(axis=ax)
        else:
            red2 = np.logaddexp
            redn = lambda x, ax: np.logaddexp.reduce(x, axis=ax)
        alpha = np.empty((A, T + 1, 8))
        alpha[:, 0] = NEG
        alpha[:, 0, 0] = 0.0
        for t in range(T):
            c = alpha[:, t, :, None] + g[:, t]                  # (A, 8, 2)
            nx = red2(c[:, PREV_S[:, 0], PREV_U[:, 0]], c[:, PREV_S[:, 1], PREV_U[:, 1]])
            alpha[:, t + 1] = nx - nx.max(1, keepdims=True)
        beta = np.empty((A, T + 1, 8))
        if self.terminated:
            beta[:, T] = NEG
            beta[:, T, 0] = 0.0
        else:
            beta[:, T] = 0.0
        for t in range(T - 1, -1, -1):
            c = g[:, t] + beta[:, t + 1][:, NEXT]               # (A, 8, 2)
            b = red2(c[:, :, 0], c[:, :, 1])
            beta[:, t] = b - b.max(1, keepdims=True)
        m = alpha[:, :k, :, None] + gp[:, :k] + beta[:, 1:k + 1][:, :, NEXT]   # (A, k, 8, 2), no systematic term
        return redn(m[..., 0], 2) - redn(m[..., 1], 2)          # extrinsic, log P0 / P1


def macs(k, iters, algo="maxlog", early=False, tail_steps=3):
    """
    Decoder ops per block (costmodel.turbo_ops): iters x 2 SISOs x (k + tail_steps) x OPS_PER_STEP[algo]
    + APP decision (+ CRC per iteration when early). `iters` may be an array (iterations used, early stop).
    """
    return costmodel.turbo_ops(k, iters, algo, tail_steps=tail_steps, early=early)


def crit(k, iters, algo="maxlog", early=False, tail_steps=3, model="state"):
    """32-core critical path of one block decode (costmodel.crit_turbo, state-parallel by default)."""
    return costmodel.crit_turbo(k, iters, algo, tail_steps=tail_steps, early=early, model=model)
