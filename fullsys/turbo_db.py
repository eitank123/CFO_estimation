"""
DVB-RCS2 TC-LM turbo code: 16-state duo-binary circular RSC ("Turbo-Phi"), EN 301 545-2 V1.3.1 cl. 7.3.5.1.

    encoder   cl. 7.3.5.1.0 (taps of AFF3CT Encoder_RSC_DB: A 1000, B 1101, Y 11101, W 10111, feedback 0011)
    circular  cl. 7.3.5.1.2: pre-encode from 0 -> S_N^0, Sc = CIRC[N mod 15 - 1][S_N^0], encode again from Sc
    interleaver cl. 7.3.5.1.1: level 1 swap (A, B) -> (B, A) (which couples: INTERLEAVER_DIR), level 2
              Pi(j) = (P j + Q(j mod 4) + 3) mod N, Q = 0, 4 Q1, 4 Q0 P + 4 Q2, 4 Q0 P + 4 Q3
    puncture  cl. 7.3.5.1.3: per-couple Y / W keep patterns, same pattern on both constituents
    decoder   TR 101 545-4 cl. 6.3.2: BCJR in the log domain on 4-ary couple symbols (max-log-MAP or exact
              log-MAP), extrinsic scaling, circular trellis by state-metric passing between iterations

Conventions (see ASSUMPTIONS): state S = 8 S1 + 4 S2 + 2 S3 + S4 (S1 = MSB); couple symbol u = 2 A + B;
LLR L = ln P(b = 0) / P(b = 1) (positive = bit 0, AFF3CT); symbol metric of a bit value x = -x L.
Arrays inside the decoder are laid out (N couples, B frames, ...); a Python loop runs over trellis steps only.
"""

import numpy as np

ASSUMPTIONS = [
    "Constituent encoder update (AFF3CT vectors): f = S3^S4^A^B; S1' = f; S2' = S1^B; S3' = S2; S4' = S3^B; "
    "Y = f^S1^S2^S4; W = f^S2^S3^S4; state integer S = 8 S1 + 4 S2 + 2 S3 + S4 (S1 = MSB).",
    "Couple bit order: A_j = bit 2j, B_j = bit 2j+1 of the encoder input (MSB of the first byte = A_0).",
    "Circulation table = AFF3CT circ_states (EN Table 7-13 garbled); row = (N mod 15) - 1, column = S_N^0; "
    "the self-test rebuilds all 14 x 16 entries from (I + G^n) Sc = S_N^0.",
    "Interleaver INTERLEAVER_DIR (three readings, the swap always follows its own reading): "
    "'aff3ct' (default) = natural couple k written to interleaved position Pi(k), natural even couples swapped "
    "(AFF3CT lut_inv gather; its published curves and, per the coordinator, the TR values); "
    "'en' = EN 301 545-2 V1.3.1 cl. 7.3.5.1.0-1 read literally: Pi(j) gives the natural index i of interleaved "
    "couple j, and the j-th OUTPUT couple is (B, A) when j mod 2 = 0 (Eq. 7-2 / 7-4 sentence) = natural odd "
    "couples swapped (the IEEE 802.16 CTC structure); 'en-natswap' = read form with natural even couples swapped "
    "(the lit_rcs2_fullsystem.md reading, the earlier 'std'). MATLAB dvbrcs2TurboEncode would be the arbiter.",
    "Puncturing: keep masks indexed by the couple index of each constituent (natural for Y1/W1, interleaved for "
    "Y2/W2); Z_i = kept Y_i followed by kept W_i.",
    "LLR sign: L = ln P(0)/P(1) (AFF3CT); symbol metric -(a La + b Lb) (= AFF3CT's halved form up to a constant).",
    "Circular trellis: alpha_0 / beta_N uniform in iteration 1, then the previous iteration's alpha_N / beta_0 "
    "(metric passing, AFF3CT; no prologue).",
    "Extrinsic scaling applied to both SISO outputs every half-iteration; the decision uses the unscaled APP of "
    "SISO 2 (TR: 0.7 except the last iteration). Default sf = 'adaptive' = AFF3CT ADAPTIVE: 0.5 in iteration 1, "
    "then 0.85 (coordinator, 2026-11-17; lit_turbo_db.md 4.1 says iterations 1-2: ADAPTIVE_LOW_ITERS sets it). "
    "sf = 0.7 gives the TR 101 545-4 cl. 6.3.2 setting.",
    "Bit decision: L(A) = red(L10, L11) - red(L00, L01), L(B) = red(L01, L11) - red(L00, L10), red = max (max-log) "
    "or exact log-sum (log-MAP); bit = 1 if L > 0 here (metrics are log-probabilities).",
]

INTERLEAVER_DIRS = ("aff3ct", "en", "en-natswap")
INTERLEAVER_DIR = "aff3ct"               # 'aff3ct' (write, AFF3CT lut_inv) | 'en' (EN literal) | 'en-natswap'
ADAPTIVE_SF = (0.5, 0.85)                # AFF3CT ADAPTIVE scaling: low value, then high value
ADAPTIVE_LOW_ITERS = 1                   # iterations that use the low value (coordinator; lit_turbo_db.md says 2)
SF_DEFAULT = "adaptive"                  # extrinsic scaling default (AFF3CT reference curves)

# ---- trellis (cl. 7.3.5.1.0) ------------------------------------------------------------------------------------
NEXT = np.zeros((16, 4), np.int64)       # next state [s, u]
YOUT = np.zeros((16, 4), np.int64)       # parity Y [s, u]
WOUT = np.zeros((16, 4), np.int64)       # parity W [s, u]
for _s in range(16):
    _S1, _S2, _S3, _S4 = (_s >> 3) & 1, (_s >> 2) & 1, (_s >> 1) & 1, _s & 1
    for _u in range(4):
        _a, _b = _u >> 1, _u & 1
        _f = _S3 ^ _S4 ^ _a ^ _b
        NEXT[_s, _u] = (_f << 3) | ((_S1 ^ _b) << 2) | (_S2 << 1) | (_S3 ^ _b)
        YOUT[_s, _u] = _f ^ _S1 ^ _S2 ^ _S4
        WOUT[_s, _u] = _f ^ _S2 ^ _S3 ^ _S4
PREV = np.zeros((16, 4), np.int64)       # previous state [s', u]: NEXT[PREV[s', u], u] = s'
for _s in range(16):
    for _u in range(4):
        PREV[NEXT[_s, _u], _u] = _s
assert all(len(set(NEXT[:, u])) == 16 for u in range(4))
PAR = 2 * YOUT + WOUT                    # parity combination c = 2 y + w of branch [s, u]
UIDX = np.tile(np.arange(4), (16, 1))    # u of branch [s, u]
IDXF = PREV * 4 + UIDX                   # flat (s, u) index of the branches entering s' [s', u]
NEXTF = NEXT.reshape(-1)                 # next state of flat branch s * 4 + u
SWP = np.array([0, 2, 1, 3])             # level-1 swap on a couple symbol: 01 <-> 10

# AFF3CT circ_states, row = (N mod 15) - 1, column = S_N^0 (cl. 7.3.5.1.2, Table 7-13)
CIRC = np.array([
    [0, 14, 3, 13, 7, 9, 4, 10, 15, 1, 12, 2, 8, 6, 11, 5],
    [0, 11, 13, 6, 10, 1, 7, 12, 5, 14, 8, 3, 15, 4, 2, 9],
    [0, 8, 9, 1, 2, 10, 11, 3, 4, 12, 13, 5, 6, 14, 15, 7],
    [0, 3, 4, 7, 8, 11, 12, 15, 1, 2, 5, 6, 9, 10, 13, 14],
    [0, 12, 5, 9, 11, 7, 14, 2, 6, 10, 3, 15, 13, 1, 8, 4],
    [0, 4, 12, 8, 9, 13, 5, 1, 2, 6, 14, 10, 11, 15, 7, 3],
    [0, 6, 10, 12, 5, 3, 15, 9, 11, 13, 1, 7, 14, 8, 4, 2],
    [0, 7, 8, 15, 1, 6, 9, 14, 3, 4, 11, 12, 2, 5, 10, 13],
    [0, 5, 14, 11, 13, 8, 3, 6, 10, 15, 4, 1, 7, 2, 9, 12],
    [0, 13, 7, 10, 15, 2, 8, 5, 14, 3, 9, 4, 1, 12, 6, 11],
    [0, 2, 6, 4, 12, 14, 10, 8, 9, 11, 15, 13, 5, 7, 3, 1],
    [0, 9, 11, 2, 6, 15, 13, 4, 12, 5, 7, 14, 10, 3, 1, 8],
    [0, 10, 15, 5, 14, 4, 1, 11, 13, 7, 2, 8, 3, 9, 12, 6],
    [0, 15, 1, 14, 3, 12, 2, 13, 7, 8, 6, 9, 4, 11, 5, 10]])


def circ_table_gf2():
    """Rebuild CIRC from the zero-input map G: Sc ^ G^n(Sc) = S_N^0, n = N mod 15 = 1..14 (cl. 7.3.5.1.2)."""
    T = np.full((14, 16), -1)
    for n in range(1, 15):
        for sc in range(16):
            g = sc
            for _ in range(n):
                g = NEXT[g, 0]
            T[n - 1, sc ^ g] = sc
    return T


# ---- interleaver (cl. 7.3.5.1.1) --------------------------------------------------------------------------------
def arp(N, P, Q):
    """Level 2: Pi(j) = (P j + Q(j mod 4) + 3) mod N; Q = (Q0, Q1, Q2, Q3)."""
    Q0, Q1, Q2, Q3 = Q
    q = np.array([0, 4 * Q1, 4 * Q0 * P + 4 * Q2, 4 * Q0 * P + 4 * Q3])
    j = np.arange(N)
    return (P * j + q[j % 4] + 3) % N


def interleaver(N, P, Q, direction=None):
    """(src, swap): interleaved couple j = natural couple src[j], with (A, B) swapped if swap[j]."""
    direction = direction or INTERLEAVER_DIR
    assert N % 4 == 0 and N % 15 != 0 and np.gcd(P, N) == 1, "TR 6.3.1: 4 | N, 15 does not divide N, gcd(P, N) = 1"
    pi = arp(N, P, Q)
    if direction == "aff3ct":                       # V[Pi(k)] = S'[k], S' = natural with even couples swapped
        src = np.empty(N, np.int64)
        src[pi] = np.arange(N)
        return src, src % 2 == 0
    if direction == "en":                           # EN Eq. 7-2 / 7-4: V[j] = S[Pi(j)], swapped if j even
        return pi, np.arange(N) % 2 == 0
    if direction == "en-natswap":                   # V[j] = S'[Pi(j)], S' = natural with even couples swapped
        return pi, pi % 2 == 0
    raise ValueError(f"interleaver direction {direction!r} not in {INTERLEAVER_DIRS}")


def pattern_mask(pat, N):
    """Per-couple keep mask from a Table A-1 pattern string (period = len(pat))."""
    p = np.array([c == "1" for c in pat])
    return p[np.arange(N) % len(p)]


# ---- encoder ----------------------------------------------------------------------------------------------------
def rsc_encode(u, s0):
    """u (B, N) couple symbols, s0 (B,) start states -> Y, W (B, N) and the end state (B,)."""
    B, N = u.shape
    Y = np.empty((B, N), np.int8)
    W = np.empty((B, N), np.int8)
    s = s0.copy()
    for k in range(N):
        uk = u[:, k]
        Y[:, k] = YOUT[s, uk]
        W[:, k] = WOUT[s, uk]
        s = NEXT[s, uk]
    return Y, W, s


def rsc_encode_circular(u):
    """Circular encoding (cl. 7.3.5.1.2): returns Y, W, Sc; the encoder ends in Sc."""
    B, N = u.shape
    _, _, sN0 = rsc_encode(u, np.zeros(B, np.int64))
    sc = CIRC[N % 15 - 1][sN0]
    Y, W, s_end = rsc_encode(u, sc)
    assert np.array_equal(s_end, sc), "circulation state failed"
    return Y, W, sc


def _red_max(x, axis):
    return x.max(axis=axis)


def _red_exact(x, axis):
    m = x.max(axis=axis, keepdims=True)
    return np.squeeze(m, axis) + np.log(np.exp(x - m).sum(axis=axis))


class TurboDB:
    """One DVB-RCS2 turbo code: N couples, ARP (P, Q), puncturing (ypat, wpat), interleaver direction."""

    def __init__(self, N, P, Q, ypat="1", wpat="1", direction=None):
        self.N, self.P, self.Q = N, P, tuple(Q)
        self.direction = direction or INTERLEAVER_DIR
        self.src, self.swap = interleaver(N, P, Q, self.direction)
        self.ymask, self.wmask = pattern_mask(ypat, N), pattern_mask(wpat, N)
        self.ny, self.nw = int(self.ymask.sum()), int(self.wmask.sum())
        self.M = self.ny + self.nw                                   # length of Z1 (= Z2)

    # couple-symbol interleaving, any array with the couple index on `axis` (symbols 0..3 or metrics [..., 4])
    def itl_sym(self, u):
        v = u[:, self.src]
        v[:, self.swap] = SWP[v[:, self.swap]]
        return v

    def itl_met(self, m):
        """(N, B, 4) metrics natural -> interleaved."""
        v = m[self.src]
        v[self.swap] = v[self.swap][..., SWP]
        return v

    def deitl_met(self, v):
        """(N, B, 4) metrics interleaved -> natural."""
        t = v.copy()
        t[self.swap] = t[self.swap][..., SWP]
        m = np.empty_like(v)
        m[self.src] = t
        return m

    def encode(self, bits):
        """bits (B, 2N) {0,1} -> Z1, Z2 (B, M) punctured parity streams (systematic bits = the input)."""
        u = 2 * bits[:, 0::2].astype(np.int64) + bits[:, 1::2]
        Y1, W1, _ = rsc_encode_circular(u)
        Y2, W2, _ = rsc_encode_circular(self.itl_sym(u))
        Z1 = np.concatenate([Y1[:, self.ymask], W1[:, self.wmask]], axis=1)
        Z2 = np.concatenate([Y2[:, self.ymask], W2[:, self.wmask]], axis=1)
        return Z1, Z2

    def _depuncture(self, Lz):
        B = Lz.shape[0]
        Ly, Lw = np.zeros((B, self.N)), np.zeros((B, self.N))
        Ly[:, self.ymask] = Lz[:, :self.ny]
        Lw[:, self.wmask] = Lz[:, self.ny:]
        return Ly, Lw

    @staticmethod
    def _pair_metric(L0, L1):
        """(N, B, 4) metric of the 4 values of a bit pair (x0, x1): -(x0 L0 + x1 L1)."""
        return np.stack([np.zeros_like(L0), -L1, -L0, -L0 - L1], axis=-1)

    @staticmethod
    def _siso(gfix, ap, a0, bN, red):
        """One BCJR pass: gfix (N, B, 16, 4) channel branch metrics, ap (N, B, 4) a priori -> APP (N, B, 4)."""
        N, B = ap.shape[:2]
        g = (gfix + ap[:, :, None, :]).reshape(N, B, 64)
        alpha = np.empty((N + 1, B, 16))
        alpha[0] = a0
        for k in range(N):                                           # forward
            t = (alpha[k][:, :, None] + g[k].reshape(B, 16, 4)).reshape(B, 64)[:, IDXF]
            a = red(t, 2)
            alpha[k + 1] = a - a[:, :1]
        app = np.empty((N, B, 4))
        beta = bN
        for k in range(N - 1, -1, -1):                               # backward + APP
            t = (g[k] + beta[:, NEXTF]).reshape(B, 16, 4)
            app[k] = red(alpha[k][:, :, None] + t, 1)
            b = red(t, 2)
            beta = b - b[:, :1]
        return app - app[..., :1], alpha[N], beta

    def decode(self, Ls, Lz1, Lz2, iters=8, algo="maxlog", sf=SF_DEFAULT, crc_check=None, early_stop=False,
               crc_start=2, sf_low_iters=None):
        """
        Ls (B, 2N) systematic LLRs (A0 B0 A1 B1 ...), Lz1 / Lz2 (B, M) parity LLRs (L = ln P0/P1).
        sf: float (TR: not applied in the last iteration) or 'adaptive' (sf_low_iters iterations at 0.5, default
        ADAPTIVE_LOW_ITERS, then 0.85). crc_check(bits (B, 2N)) -> bool (B,), used for early stop / first-pass record.
        Returns bits (B, 2N) and info: iters (B,) used, first_pass (B,) first iteration with CRC ok (0 = never).
        """
        red = {"maxlog": _red_max, "logmap": _red_exact}[algo]
        B, N = Ls.shape[0], self.N
        La, Lb = Ls[:, 0::2].T, Ls[:, 1::2].T                         # (N, B)
        sys1 = self._pair_metric(La, Lb)
        sys2 = self.itl_met(sys1)
        Ly1, Lw1 = self._depuncture(Lz1)
        Ly2, Lw2 = self._depuncture(Lz2)
        par1, par2 = self._pair_metric(Ly1.T, Lw1.T), self._pair_metric(Ly2.T, Lw2.T)
        g1 = sys1[:, :, UIDX] + par1[:, :, PAR]                       # (N, B, 16, 4)
        g2 = sys2[:, :, UIDX] + par2[:, :, PAR]
        z16 = np.zeros((B, 16))
        a1, b1, a2, b2 = z16, z16, z16, z16
        ap1 = np.zeros((N, B, 4))
        bits = np.zeros((B, 2 * N), np.int8)
        done = np.zeros(B, bool)
        used = np.full(B, iters)
        first = np.zeros(B, np.int64)
        for it in range(1, iters + 1):
            if sf == "adaptive":
                nlow = ADAPTIVE_LOW_ITERS if sf_low_iters is None else sf_low_iters
                s = ADAPTIVE_SF[0] if it <= nlow else ADAPTIVE_SF[1]
            else:
                s = 1.0 if it == iters else float(sf)              # TR 6.3.2: "0.7 except for the last iteration"
            app1, a1, b1 = self._siso(g1, ap1, a1, b1, red)
            e1 = app1 - ap1 - sys1
            ap2 = self.itl_met(s * (e1 - e1[..., :1]))
            app2, a2, b2 = self._siso(g2, ap2, a2, b2, red)
            e2 = app2 - ap2 - sys2
            ap1 = self.deitl_met(s * (e2 - e2[..., :1]))
            tot = self.deitl_met(app2)                               # (N, B, 4): log APP of 00, 01, 10, 11
            LA = red(tot[..., [2, 3]], 2) - red(tot[..., [0, 1]], 2)
            LB = red(tot[..., [1, 3]], 2) - red(tot[..., [0, 2]], 2)
            hard = np.empty((B, 2 * N), np.int8)
            hard[:, 0::2] = (LA > 0).T
            hard[:, 1::2] = (LB > 0).T
            upd = ~done
            bits[upd] = hard[upd]
            if crc_check is not None:
                ok = crc_check(hard)
                first[(first == 0) & ok] = it
                if early_stop and it >= crc_start:
                    new = upd & ok
                    used[new] = it
                    done |= new
                    if done.all():
                        break
        return bits, {"iters": used, "first_pass": first}


# ---- operation count ---------------------------------------------------------------------------------------------
OPS_STAGE = {"adds": 252, "cs": 156, "muls": 3}     # per couple per SISO pass, max-log-MAP, this implementation
OPS_TR = {"adds": 267, "cs": 159, "muls": 0}       # TR 101 545-4 cl. 6.3.2.3 per trellis stage (per SISO)


CRIT_CORES = 32                                    # state-parallel model: cores sharing one trellis stage
CRIT_SYNC = 8                                      # per stage: 16 -> 1 APP / normalisation reduction tree + sync


def macs(N_couples, iters, algo="maxlog", early_stop=False, model="impl", n_sym=0, bps=2, crc=32,
         cores=CRIT_CORES):
    """
    Decoder operations per frame, iters may be a mean (early stop).
    Counting convention: every add, compare-select (CS), multiply and LUT read = 1 op (as a MAC in the polar
    model); all 64 branches counted, normalisation counted.
    Per couple per SISO pass (model 'impl', max-log-MAP):
        branch  2 (La+Lb, Ly+Lw) + 3 (a priori + systematic, u != 00) + 16 (distinct gamma of 4 u x 4 parity) = 21 add
        forward 64 add + 16 x 3 = 48 CS + 15 normalisation add;  backward the same (its gamma+beta sums reused)
        APP     64 add + 4 x 15 = 60 CS;  extrinsic 9 add (normalise, - a priori, - systematic) + 3 mul (scaling)
        -> 252 add + 156 CS + 3 mul = 411 ops counted (a lean design without the 2 x 15 normalisation
        subtractions, e.g. modulo metric arithmetic, needs ~381).
    log-MAP: every 2-input CS becomes max* = CS + |difference| / LUT / add -> + 2 add + 1 LUT per CS (+468 ops).
    Decision: 4 CS + 2 add per couple, once (every iteration with early stop). CRC not counted.
    Demapper LLR scaling (as polar_rm.decode_macs): llr = 4 per QPSK / 2 per BPSK symbol (n_sym data symbols, bps).
    total = 2 N iters ops_couple + 6 N (iters if early_stop else 1) + llr.
    crit (MACs per core, state-parallel on `cores` = 32: the 64 branches of a stage split over the cores, stages
    serial, 2 SISO passes per iteration) = 2 iters N (ceil(ops_couple / cores) + CRIT_SYNC) + decision / cores
    + llr / cores; CRIT_SYNC = 8 for the 16 -> 1 APP reduction and the core sync per stage.
    per_info_bit = total / k, k = 2 N - crc (information bits).
    model 'tr': the TR's 267 add + 159 CS per stage per SISO instead.
    """
    st = dict(OPS_TR if model == "tr" else OPS_STAGE)
    st["lut"] = 0
    if algo == "logmap":
        st["adds"] += 2 * st["cs"]
        st["lut"] = st["cs"]
    ops_couple = st["adds"] + st["cs"] + st["muls"] + st["lut"]
    n = 2 * N_couples * iters
    out = {k: n * v for k, v in st.items()}
    nd = N_couples * (iters if early_stop else 1)
    out["cs"] += 4 * nd
    out["adds"] += 2 * nd
    out["llr"] = (4 if bps == 2 else 2) * n_sym
    out["total"] = sum(out[k] for k in ("adds", "cs", "muls", "lut", "llr"))
    out["ops_couple"] = ops_couple
    out["crit"] = (n * (int(np.ceil(ops_couple / cores)) + CRIT_SYNC) + 6 * nd / cores + out["llr"] / cores)
    out["per_info_bit"] = out["total"] / (2 * N_couples - crc)
    return out
