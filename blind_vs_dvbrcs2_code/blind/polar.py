"""
Polar code with CRC-aided successive-cancellation list (CA-SCL) decoding.

    Encoder : x = u F^{(x)n},  F = [[1, 0], [1, 1]]  (natural order, no bit reversal)
    Frozen  : polarization-weight (PW) reliability order, beta = 2^(1/4)
              (the SNR-independent construction 5G NR's sequence is derived from)
    CRC     : 5G NR polynomials, data bits first, CRC bits last
    Decoder : LLR-based SCL (min-sum f, exact path metric), batched over frames,
              with the Fast-SSCL rate-0 node shortcut (all-frozen sub-trees).
              The surviving path with the best metric that passes the CRC is
              chosen; if no path passes, the best-metric path is returned.

LLR convention: LLR = log P(bit = 0) / P(bit = 1).
"""

import numpy as np

CRC_POLYS = {               # exponents of the generator polynomial (5G NR, TS 38.212)
    6: (6, 5, 0),
    11: (11, 10, 9, 5, 0),
    16: (16, 12, 5, 0),
    24: (24, 23, 21, 20, 17, 15, 13, 12, 8, 4, 2, 1, 0),   # CRC24C
    32: (32, 26, 23, 22, 16, 12, 11, 10, 8, 7, 5, 4, 2, 1, 0),   # 0x04C11DB7 (fullsys: the competitors' CRC-32;
}                                                              # here init 0, no reflection, no final XOR)


def pw_reliability(N, beta=2 ** 0.25):
    """Bit-channel indices sorted from least to most reliable."""
    n = int(np.log2(N))
    idx = np.arange(N)
    w = sum(((idx >> j) & 1) * beta ** j for j in range(n))
    return np.argsort(w, kind="stable")


def crc_remainder(bits, crc_len):
    """CRC of a single bit vector: remainder of bits(x) * x^C mod g(x)."""
    g = np.zeros(crc_len + 1, dtype=np.uint8)
    for e in CRC_POLYS[crc_len]:
        g[crc_len - e] = 1
    reg = np.concatenate([np.asarray(bits, dtype=np.uint8), np.zeros(crc_len, dtype=np.uint8)])
    for i in range(len(bits)):
        if reg[i]:
            reg[i:i + crc_len + 1] ^= g
    return reg[-crc_len:]


class PolarCode:

    def __init__(self, N, A, crc_len=11, list_size=8, info_pos=None, crc_G=None):
        """N code length, A data bits, crc_len CRC bits, K = A + crc_len info bits. info_pos (optional, K indices):
        an explicit information set (fullsys/polar_rm.py rate matching); None = the top K of the PW order. crc_G
        (optional, (A, crc_len)): the CRC generator matrix precomputed (fullsys/polar_rm.crc_matrix, the same
        matrix, fast); None = computed here as before."""
        self.N, self.A, self.C, self.list_size = N, A, crc_len, list_size
        self.K = A + crc_len
        self.n = int(np.log2(N))
        assert 2 ** self.n == N and self.K <= N
        if info_pos is None:
            self.info_pos = np.sort(pw_reliability(N)[-self.K:])
        else:
            self.info_pos = np.sort(np.asarray(info_pos, dtype=np.int64))
            assert len(self.info_pos) == self.K and len(np.unique(self.info_pos)) == self.K \
                and self.info_pos[0] >= 0 and self.info_pos[-1] < N
        self.frozen = np.ones(N, dtype=bool)
        self.frozen[self.info_pos] = False
        # CRC is linear (zero initial state): crc(d) = d @ G mod 2
        if crc_G is not None:
            self.crc_G = np.asarray(crc_G, dtype=np.uint8)
            assert self.crc_G.shape == (A, crc_len)
        else:
            self.crc_G = np.stack([crc_remainder(np.eye(A, dtype=np.uint8)[i], crc_len) for i in range(A)]) \
                if crc_len else np.zeros((A, 0), dtype=np.uint8)

    @property
    def rate(self):
        return self.A / self.N

    # ----------------------------------------------------------------- encode

    def crc(self, data):
        return (data.astype(np.int64) @ self.crc_G) % 2

    def encode(self, data):
        """data (B, A) bits -> codewords (B, N) bits."""
        B = data.shape[0]
        u = np.zeros((B, self.N), dtype=np.uint8)
        u[:, self.info_pos] = np.concatenate([data, self.crc(data)], axis=1)
        return polar_transform(u)

    # ----------------------------------------------------------------- decode

    def decode(self, llr, return_info=False):
        """llr (B, N) channel LLRs -> decoded data bits (B, A) [, CRC passed (B,), path metric (B,)]."""
        B, Ls = llr.shape[0], self.list_size
        self._pm = np.full((B, Ls), np.inf, dtype=np.float32)
        self._pm[:, 0] = 0.0
        self._bits, self._parents = [], []                      # per info bit, for the traceback
        alpha = np.repeat(llr[:, None, :].astype(np.float32), Ls, axis=1)   # float32: half the memory traffic
        self._rec(alpha, 0, self.N)

        # Trace every surviving path back through the parent pointers
        info = np.empty((B, Ls, self.K), dtype=np.uint8)
        path = np.broadcast_to(np.arange(Ls), (B, Ls))
        rows = np.arange(B)[:, None]
        for k in range(self.K - 1, -1, -1):
            info[:, :, k] = self._bits[k][rows, path]
            path = self._parents[k][rows, path]
        data, crc = info[..., :self.A], info[..., self.A:]
        ok = np.all(self.crc(data.reshape(-1, self.A)).reshape(B, Ls, self.C) == crc, axis=2)
        score = np.where(ok, self._pm, np.inf)
        best = np.where(ok.any(1), score.argmin(1), self._pm.argmin(1))
        self.last_info = info[np.arange(B), best]        # the chosen paths' info bits incl. their CRC (re-encoding)
        if return_info:   # also: did a list path pass the CRC, and the chosen path's metric
            return data[np.arange(B), best], ok.any(1), self._pm[np.arange(B), best]
        return data[np.arange(B), best]

    def decode_traced(self, llr, ends):
        """decode(llr, return_info=True) that also records the best path metric of the list after the bits [0, e)
        for every e in ends (ascending bit counts): (data, CRC passed, path metric, trace (B, len(ends)))."""
        self._ends, self._ci = list(ends), 0
        self._tr = np.full((len(llr), len(ends)), np.nan, np.float32)
        try:
            out = self.decode(llr, return_info=True)
            return (*out, self._tr)
        finally:
            self._ends = None

    _ends = None
    fz_q = None     # (measurement, small_rx fz_diag) None = off; fractions of the frozen set (decoding order) at which
                    # every list path's frozen-only metrics are recorded in fz_rec (decisions / PMs unchanged)
    fz_stop = None  # F5 online (small_rx fzstop): None = off; (q, t): at the first node boundary with >= ceil(q F) frozen
                    # leaves seen, a row whose min over its alive paths of psn = (the decoder's own frozen PM increment
                    # summed over the frozen leaves / rate-0 nodes seen) / (frozen leaves seen) is > t is marked stopped
                    # (fzs_stop (B,), fzs_pos the check's leaf end, fzs_nb information bits decided); the decode itself
                    # runs on unchanged (the caller treats a stopped row as a CRC failure and charges the work up to
                    # fzs_pos); the fz_diag `ps` checkpoint rule
    fz_mask = None  # (fullsys/blind_fmt.py) None = every frozen leaf counts (the baseline); bool (N,): only the frozen
                    # leaves in the mask enter the fz_stop sums / count and the fz_q `ps` / cnt_s rule (rate matching:
                    # the pre-frozen rm / extra leaves carry no CFO information); a rate-0 node with m of its n leaves
                    # in the mask adds m leaves and m / n of its increment

    def _fzm(self, lo, n):
        """(fz_mask) leaves of [lo, lo + n) in the mask."""
        return int(self.fz_mask[lo:lo + n].sum())

    def _fzs_start(self, shape):
        """(fz_stop) a decode starts: per path (B, Ls) the frozen PM increment sum, the check's frozen-leaf count."""
        F = int(self.frozen.sum()) if self.fz_mask is None else int((self.frozen & self.fz_mask).sum())
        self._fzs_t = max(int(np.ceil(float(self.fz_stop[0]) * F - 1e-9)), 1)
        self._fzs_n, self._fzs_ps, self._fzs_done = 0, np.zeros(shape), False
        self.fzs_stop, self.fzs_pos, self.fzs_nb = np.zeros(shape[0], bool), -1, -1
        self.fzs_psn = np.full(shape[0], np.nan)                # (measurement) the check's psn (B,); nan: not reached

    def _fzs_add(self, inc, n, hi):
        """(fz_stop) n frozen leaves ending at leaf hi added inc (B, Ls) to the PMs (already in _pm): the check."""
        if self._fzs_done:
            return
        self._fzs_ps += inc
        self._fzs_n += n
        if self._fzs_n >= self._fzs_t:                          # the first node boundary at >= ceil(q F) frozen leaves
            psn = np.where(np.isfinite(self._pm), self._fzs_ps, np.inf).min(1) / self._fzs_n
            self.fzs_stop, self.fzs_pos, self.fzs_nb = psn > float(self.fz_stop[1]), int(hi), len(self._bits)
            self.fzs_psn = psn
            self._fzs_done = True

    def _fz_start(self, shape):
        """(fz_q) a decode starts: per path (B, Ls) running sums of the frozen-bit hard penalty |LLR| [LLR < 0] and
        of |LLR| over the frozen leaves seen (leaf LLRs, also inside rate-0 nodes), checkpoint c at the
        ceil(fz_q[c] F)-th frozen leaf (F frozen bits); and of the decoder's own frozen PM increment ps (log(1 + e^-a)
        summed over a rate-0 node's / frozen leaf's LLRs, the _pm terms recomputed apart), at the first node boundary
        with >= ceil(fz_q[c] F) frozen leaves. fz_rec: pen, mag, alive (B, Ls, C) finite PM, cnt / pos / nb (C,)
        frozen leaves, leaves (bits) and information bits decided; ps, alive_s (B, Ls, C), cnt_s / pos_s / nb_s (C,)."""
        F = int(self.frozen.sum())
        t = np.maximum(np.ceil(np.asarray(self.fz_q, float) * F - 1e-9).astype(int), 1)
        C = len(t)
        self._fz_t, self._fz_c, self._fz_cs, self._fz_n = t, 0, 0, 0
        if self.fz_mask is not None:                            # (fz_mask) the ps rule on the masked leaves only
            Fm = int((self.frozen & self.fz_mask).sum())
            self._fz_tm, self._fz_nm = np.maximum(np.ceil(np.asarray(self.fz_q, float) * Fm - 1e-9).astype(int), 1), 0
        self._fz_s = np.zeros(shape + (3,))
        z = lambda: np.zeros(C, int)
        self.fz_rec = dict(pen=np.full(shape + (C,), np.nan, np.float32), mag=np.full(shape + (C,), np.nan, np.float32),
                           alive=np.zeros(shape + (C,), bool), cnt=t.copy(), pos=z(), nb=z(),
                           ps=np.full(shape + (C,), np.nan, np.float32), alive_s=np.zeros(shape + (C,), bool),
                           cnt_s=z(), pos_s=z(), nb_s=z())

    def _fz_add(self, a, lo, node):
        """(fz_q) frozen leaves lo, lo + 1, ... with leaf LLRs a (B, Ls, n), node LLRs node (B, Ls, n) (a frozen leaf:
        node = a): accumulate, record crossed checkpoints."""
        pen, mag = np.where(a < 0, -a, 0).astype(np.float64), np.abs(a).astype(np.float64)
        n, R = a.shape[2], self.fz_rec
        while self._fz_c < len(self._fz_t) and self._fz_t[self._fz_c] <= self._fz_n + n:
            c, m = self._fz_c, self._fz_t[self._fz_c] - self._fz_n      # m leaves of this node up to checkpoint c
            R["pen"][..., c] = self._fz_s[..., 0] + pen[..., :m].sum(2)
            R["mag"][..., c] = self._fz_s[..., 1] + mag[..., :m].sum(2)
            R["alive"][..., c] = np.isfinite(self._pm)
            R["pos"][c], R["nb"][c] = lo + m, len(self._bits)
            self._fz_c += 1
        self._fz_s[..., 0] += pen.sum(2)
        self._fz_s[..., 1] += mag.sum(2)
        if self.fz_mask is not None:                            # (fz_mask) masked leaves, m / n of the increment
            m = self._fzm(lo, n)
            self._fz_n += n
            if not m:
                return
            self._fz_s[..., 2] += np.logaddexp(np.float32(0), -node).sum(axis=2) * (m / n)
            self._fz_nm += m
            while self._fz_cs < len(self._fz_tm) and self._fz_tm[self._fz_cs] <= self._fz_nm:
                c = self._fz_cs
                R["ps"][..., c], R["alive_s"][..., c] = self._fz_s[..., 2], np.isfinite(self._pm)
                R["cnt_s"][c], R["pos_s"][c], R["nb_s"][c] = self._fz_nm, lo + n, len(self._bits)
                self._fz_cs += 1
            return
        self._fz_s[..., 2] += np.logaddexp(np.float32(0), -node).sum(axis=2)   # = the _pm term, computed apart
        self._fz_n += n
        while self._fz_cs < len(self._fz_t) and self._fz_t[self._fz_cs] <= self._fz_n:   # node boundary checkpoints
            c = self._fz_cs
            R["ps"][..., c], R["alive_s"][..., c] = self._fz_s[..., 2], np.isfinite(self._pm)
            R["cnt_s"][c], R["pos_s"][c], R["nb_s"][c] = self._fz_n, lo + n, len(self._bits)
            self._fz_cs += 1

    def _mark(self, end):
        """(decode_traced) the list's best path metric once the first `end` bits are decided."""
        while self._ci < len(self._ends) and self._ends[self._ci] <= end:
            self._tr[:, self._ci] = self._pm.min(1)
            self._ci += 1

    def _rec(self, alpha, lo, hi):
        """Decode leaves [lo, hi). Returns (re-encoded bits (B, Ls, n), path permutation or None)."""
        n = hi - lo
        if n == self.N and self.fz_q is not None:               # (measurement) a decode starts
            self._fz_start(alpha.shape[:2])
        if n == self.N and self.fz_stop is not None:            # (fz_stop) a decode starts
            self._fzs_start(alpha.shape[:2])
        if n == 1:
            out = self._leaf(alpha[..., 0], lo)
            if self._ends is not None:
                self._mark(lo + 1)
            return out
        if self.frozen[lo:hi].all():
            # Rate-0 node (Fast-SSCL): all-zero sub-codeword, metric of every node LLR being 0
            if self.fz_stop is None:
                self._pm += np.logaddexp(np.float32(0), -alpha).sum(axis=2)
            else:                                               # (fz_stop) the same increment, also summed apart
                inc = np.logaddexp(np.float32(0), -alpha).sum(axis=2)
                self._pm += inc
                if self.fz_mask is None:
                    self._fzs_add(inc, n, hi)
                elif self._fzm(lo, n):                          # (fz_mask) m of the n leaves, m / n of the increment
                    m = self._fzm(lo, n)
                    self._fzs_add(inc * (m / n), m, hi)
            if self._ends is not None:
                self._mark(hi)
            if self.fz_q is not None:                           # (measurement) its leaves' LLRs, as SC would see them
                self._fz_add(_rate0_leaves(alpha), lo, alpha)
            return np.zeros(alpha.shape, dtype=np.uint8), None
        mid = lo + n // 2
        a, b = alpha[..., :n // 2], alpha[..., n // 2:]
        left = np.copysign(np.minimum(np.abs(a), np.abs(b)), a * b)              # min-sum f
        beta_l, p1 = self._rec(left, lo, mid)
        if p1 is not None:
            a, b = _gather(a, p1), _gather(b, p1)
        beta_r, p2 = self._rec(b + np.where(beta_l, -a, a), mid, hi)             # g
        if p2 is not None:
            beta_l = _gather(beta_l, p2)
        perm = p1 if p2 is None else (p2 if p1 is None else _gather(p1, p2))
        return np.concatenate([beta_l ^ beta_r, beta_r], axis=2), perm

    def _leaf(self, llr, i):
        if self.frozen[i]:
            if self.fz_stop is None:
                self._pm += np.logaddexp(np.float32(0), -llr)   # cost of u_i = 0
            else:                                               # (fz_stop) the same increment, also summed apart
                inc = np.logaddexp(np.float32(0), -llr)
                self._pm += inc
                if self.fz_mask is None or self.fz_mask[i]:     # (fz_mask) a masked-out leaf is not counted
                    self._fzs_add(inc, 1, i + 1)
            if self.fz_q is not None:                           # (measurement) frozen-only metrics
                self._fz_add(llr[..., None], i, llr[..., None])
            return np.zeros(llr.shape + (1,), dtype=np.uint8), None
        Ls = self.list_size
        zero = np.float32(0)
        cand = np.concatenate([self._pm + np.logaddexp(zero, -llr),    # u_i = 0
                               self._pm + np.logaddexp(zero, llr)], 1)  # u_i = 1
        keep = np.argpartition(cand, Ls - 1, axis=1)[:, :Ls]
        parent, bit = keep % Ls, (keep // Ls).astype(np.uint8)
        self._pm = cand[np.arange(len(cand))[:, None], keep]
        self._bits.append(bit)
        self._parents.append(parent)
        if self.fz_q is not None:                               # (measurement) the sums follow their paths
            self._fz_s = self._fz_s[np.arange(len(cand))[:, None], parent]
        if self.fz_stop is not None and not self._fzs_done:     # (fz_stop) the sums follow their paths
            self._fzs_ps = self._fzs_ps[np.arange(len(cand))[:, None], parent]
        return bit[..., None], parent


def polar_transform(u):
    """x = u F^{(x)n} over the last axis (works for any leading shape)."""
    x = u.copy()
    N = x.shape[-1]
    step = 1
    while step < N:
        v = x.reshape(x.shape[:-1] + (N // (2 * step), 2, step))
        v[..., 0, :] ^= v[..., 1, :]
        step *= 2
    return x


def _rate0_leaves(a):
    """(measurement, fz_q) leaf LLRs (..., n) of an all-frozen sub-tree from its node LLRs a (..., n), leaf order: the
    decoder's min-sum f and g with zero partial sums (g = a + b)."""
    n = a.shape[-1]
    if n == 1:
        return a
    x, y = a[..., :n // 2], a[..., n // 2:]
    return np.concatenate([_rate0_leaves(np.copysign(np.minimum(np.abs(x), np.abs(y)), x * y)),
                           _rate0_leaves(x + y)], -1)


def _gather(arr, perm):
    """arr (B, Ls, ...) re-ordered along the path axis by perm (B, Ls). Plain fancy indexing: the same values as
    np.take_along_axis, with less overhead."""
    return arr[np.arange(perm.shape[0])[:, None], perm]
