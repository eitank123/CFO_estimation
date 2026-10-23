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
}


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

    def __init__(self, N, A, crc_len=11, list_size=8):
        """N code length, A data bits, crc_len CRC bits, K = A + crc_len info bits."""
        self.N, self.A, self.C, self.list_size = N, A, crc_len, list_size
        self.K = A + crc_len
        self.n = int(np.log2(N))
        assert 2 ** self.n == N and self.K <= N
        self.info_pos = np.sort(pw_reliability(N)[-self.K:])
        self.frozen = np.ones(N, dtype=bool)
        self.frozen[self.info_pos] = False
        # CRC is linear (zero initial state): crc(d) = d @ G mod 2
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
        if return_info:   # also: did a list path pass the CRC, and the chosen path's metric
            return data[np.arange(B), best], ok.any(1), self._pm[np.arange(B), best]
        return data[np.arange(B), best]

    def _rec(self, alpha, lo, hi):
        """Decode leaves [lo, hi). Returns (re-encoded bits (B, Ls, n), path permutation or None)."""
        n = hi - lo
        if n == 1:
            return self._leaf(alpha[..., 0], lo)
        if self.frozen[lo:hi].all():
            # Rate-0 node (Fast-SSCL): all-zero sub-codeword, metric of every node LLR being 0
            self._pm += np.logaddexp(np.float32(0), -alpha).sum(axis=2)
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
            self._pm += np.logaddexp(np.float32(0), -llr)       # cost of u_i = 0
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


def _gather(arr, perm):
    """arr (B, Ls, ...) re-ordered along the path axis by perm (B, Ls). Plain fancy indexing: the same values as
    np.take_along_axis, with less overhead."""
    return arr[np.arange(perm.shape[0])[:, None], perm]
