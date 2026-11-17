"""Fast-SSC list decoder of the path metric only (F3 of BLIND_IMPLEMENTATION/testing/results/expected_f3f5.md; Yuan,
Coskun, Kramer 2021): the list-marginalised SC metric -log sum_l exp(-PM_l) over the L_e surviving paths. Used by the
offline rank harness (BLIND_IMPLEMENTATION/testing/lit_checks.py lmarg) and by small_rx's `lmarg` re-ranking of the
last-checkpoint survivors. Moved here from lit_checks.py (2026-11-15), unchanged except the optional early stop and
the L = 1 REP rule (review fix 2026-11-15: bf.FastSC's arithmetic)."""
import numpy as np

import blind_fast as bf

SPLIT = 64                      # rate-0 nodes in 64-bit chunks for the checkpoint (small_rx.SPLIT)


def leaf_ends(plan, lo, hi, out, split=None):
    """End bit of every leaf in decoding order, rate-0 nodes in split-bit chunks (as small_rx.leaves)."""
    if plan[0] == "R0" and split and hi - lo > split:
        out += list(range(lo + split, hi + 1, split))
    elif plan[0] != "N":
        out.append(hi)
    else:
        leaf_ends(plan[1], lo, (lo + hi) // 2, out, split)
        leaf_ends(plan[2], (lo + hi) // 2, hi, out, split)
    return out


class FastSCL:
    """Fast-SSC list decoder of the path metric only (no CRC: every non-frozen bit is information), node rules of
    bf.FastSC (min-sum f, closed-form rate-0 / rate-1 / REP / SPC penalties) with the Fast-SSCL splits of Hashemi et al.
    2017: rate-1 the min(L - 1, n) least reliable bits one by one, SPC min(L, n) (pair flips with the least reliable
    bit, which fixes the parity), REP both repetitions; the L best paths by PM kept per hypothesis (the list grows
    1, 2, 4, ... to L). PM_l = sum over the node bits of softplus(-(1 - 2 b) a) (a flip costs +|a|), so L = 1 is
    bf.FastSC.metric (REP at L = 1 in FastSC's arithmetic, pm + min(c0, c1); L >= 2 unchanged). decode(llr (H, N),
    cut) -> PM (H, L) at the end and after the last leaf ending <= cut bits; stop=True skips every node starting at or beyond the cut
    (the end PM is then partial: only the checkpoint PM is valid)."""

    def __init__(self, fs, L):
        self.plan, self.L, self._f = fs.plan, L, fs._f
        self._stop = False

    def _sel(self, cand, cur):
        """Keep the min(L, C) best of the candidates (H, C = k cur), candidate c from path c % cur."""
        if cand.shape[1] <= self.L:
            o = np.broadcast_to(np.arange(cand.shape[1]), cand.shape)
        else:
            o = np.argsort(cand, 1, kind="stable")[:, :self.L]
        src = o % cur
        return o, cand[self._h, o], (None if cur == 1 and o.shape[1] == 1 else src)

    def _mark(self, end, pm):
        if end <= self._cut:
            self._ck = pm

    def _flip(self, h, idx, fl):
        hb = np.zeros(h.shape, bool)
        np.put_along_axis(hb, idx, fl, -1)
        return h ^ hb

    def _node(self, plan, a, pm, lo):
        t, n, hh = plan[0], a.shape[2], self._h
        if self._stop and lo >= self._cut:                            # beyond the checkpoint: not decoded
            return np.zeros(a.shape, bool), pm, None
        if t == "R0":
            v = bf._softplus(-a)
            k = (self._cut - lo) // SPLIT * SPLIT                     # rate-0 node across the checkpoint: its
            if 0 < k < n:                                             # chunks up to the cut
                self._mark(lo + k, pm + v[..., :k].sum(-1))
            pm = pm + v.sum(-1)
            self._mark(lo + n, pm)
            return np.zeros(a.shape, bool), pm, None
        if t == "N":
            x, y = a[..., :n // 2], a[..., n // 2:]
            bl, pm, p1 = self._node(plan[1], self._f(x, y), pm, lo)
            if p1 is not None:
                x, y = x[hh, p1], y[hh, p1]
            br, pm, p2 = self._node(plan[2], y + np.where(bl, -x, x), pm, lo + n // 2)
            if p2 is not None:
                bl = bl[hh, p2]
                p1 = p2 if p1 is None else p1[hh, p2]
            return np.concatenate([bl ^ br, br], -1), pm, p1
        if t == "REP":
            c0, c1 = bf._softplus(-a).sum(-1), bf._softplus(a).sum(-1)
            if self.L == 1:                                           # L = 1: bf.FastSC's own arithmetic (b = c1 < c0,
                pm = pm + np.minimum(c0, c1)                          # pm + min): no near-tie flips; c0 (H, 1)
                self._mark(lo + n, pm)
                return np.broadcast_to((c1 < c0)[..., None], a.shape).copy(), pm, None
            cur = pm.shape[1]
            o, pm, p = self._sel(np.concatenate([pm + c0, pm + c1], 1), cur)
            self._mark(lo + n, pm)
            return np.broadcast_to((o >= cur)[..., None], o.shape + (n,)).copy(), pm, p
        h, aa = a < 0, np.abs(a)
        spc = t == "SPC"
        m = min(self.L if spc else self.L - 1, n)
        if m == 1 and spc:
            idx = aa.argmin(-1)[..., None]                            # = bf.FastSC (first minimum)
        elif m:
            idx = np.argsort(aa, -1, kind="stable")[..., :m]
        if spc:
            av = np.take_along_axis(aa, idx, -1)
            par = h.sum(-1) % 2 == 1
            pm = pm + (bf._softplus(-aa).sum(-1) + np.where(par, av[..., 0], 0.0))
            fl = np.zeros(idx.shape, bool)
            fl[..., 0] = par                                          # the least reliable bit fixes the parity
        else:
            pm = pm + bf._softplus(-aa).sum(-1)
            if not m:
                self._mark(lo + n, pm)
                return h, pm, None
            av = np.take_along_axis(aa, idx, -1)
            fl = np.zeros(idx.shape, bool)
        p = None
        for j in range(1 if spc else 0, m):                           # split on the j-th least reliable bit
            cur = pm.shape[1]
            dj = av[..., j] + (np.where(fl[..., 0], -av[..., 0], av[..., 0]) if spc else 0.0)
            o, pm, s = self._sel(np.concatenate([pm, pm + dj], 1), cur)
            src = o % cur
            idx, av, fl = idx[hh, src], av[hh, src], fl[hh, src]
            f_ = o >= cur
            fl[..., j] ^= f_
            if spc:
                fl[..., 0] ^= f_                                      # pair flip: toggles the parity bit
            p = src if p is None else p[hh, src]
        if p is not None:
            h = h[hh, p]
        self._mark(lo + n, pm)
        return self._flip(h, idx, fl), pm, p

    def decode(self, llr, cut, stop=False):
        a = np.asarray(llr, np.float32)[:, None, :]
        self._h, self._cut, self._ck, self._stop = np.arange(len(a))[:, None], int(cut), None, bool(stop)
        _, pm, _ = self._node(self.plan, a, np.zeros((len(a), 1), np.float32), 0)
        return pm, self._ck


def lse_metric(pm):
    """-log sum_l exp(-PM_l) over the surviving paths (H, L) -> (H,)."""
    pm = pm.astype(np.float64)
    mn = pm.min(1)
    return mn - np.log(np.exp(mn[:, None] - pm).sum(1))
