"""Twin-preserving polar designs (sync_cfo/IDEAS_fable.md I2 / I4-I7, the user's 2026-11-19 idea): the Plotkin twins
x_k = x_{k+N/2} of the rate-matched codes as a zero-energy "pilot" made of code redundancy. Counting only (no channel):
designs, clean relations, transmit lags, the pi/2-rotation rank test. Imported read-only: fullsys/polar_rm.py,
fullsys/run_polar_genie.py (FMTS, DESIGN_SNR), fullsys/polar_design.py; nothing there is changed.

    Plotkin  x = u G_N, G_N = F^{(x)n}, natural order (polar.polar_transform): G[i, j] = 1 iff j subset-of i (bitwise),
             x_j = XOR_{i superset-of j} u_i. For k < N/2: x_k XOR x_{k+N/2} = XOR_{i < N/2, i superset-of k} u_i, so the
             twin k is CLEAN (equal in every codeword) iff no first-half info index i covers k; a first-half info bit i
             breaks the 2^{wt(i)} twins k subset-of i (the second-half info rows never break a twin)
    exact    columns of the K x N info-row generator G_info: x_p XOR x_q = 0 for every codeword iff column p == column q
             (linear code: otherwise the XOR is uniform); a class = the sent positions with one column (a relation =
             a pair inside a class, sum (m - 1) independent ones); an all-zero column = a known (0) sent bit. Clean twins
             are checked both ways (cover count == column test, asserted)
    designs  base = the adopted code (rm_plan with run_polar_genie's settings: GA at DESIGN_SNR for DVB-RCS2, PW for
             vde32), K = A + 32, E, rate matching (J, mode, pre-frozen set) unchanged in every design:
               k<m>  m of the F1 first-half info bits moved (order 'weight', default: highest Hamming weight first =
                     the most twins broken, 2^wt; ties: more reliable first; 'greedy': most twins freed per move, then
                     the fractional cover sum 1 / cnt; 'search': greedy + swap local search, removed_set; 'low': least
                     reliable first) to the m most reliable frozen
                     second-half positions outside pre (design order: GA mean / PW); nested in m
               f<x>  m = round(x F1) (f0.25, f0.5, f1)
               p<F>  aligned prefix: u_0 .. u_{N - N/F - 1} frozen, the K info bits = the most reliable of the last N/F
                     outside pre (feasible iff K <= that count): x_k = x_{k + j N/F}, j = 0 .. F - 1 (F-fold repetition,
                     relations at x lags multiples of N/F); p2 is the all-twin design
    tx map   sent bit e_k = x[pos0[k]] (pos0 = J[U:] puncture, J[:E] shorten), tx bit m = e[chan[m]] XOR pn_m, P[m] =
             pos0[chan[m]]; QPSK symbol m // 2 (I even, Q odd), BPSK / pi/2-BPSK symbol m. intlv:
               none  chan = identity (run_polar_genie's default)
               base  the blind system's: QPSK rng(12345).permutation(E) (blind_fmt chan), BPSK identity  [today]
               adj   (I2) the bits of each relation class in consecutive symbols: BPSK one bit per symbol; QPSK two
                     classes of one size side by side (symbol t = (A_t, B_t): equal symbols, mu = 1); blocks spread
                     evenly over the burst, the other bits in base order in between
               same  (QPSK) a class's bits on I / Q of the same symbols (twin pair -> one diagonal symbol, lag 0: a
                     squared-signal line, not a product)
             scr: a known PN scrambler pn = default_rng([PN_SEED, tag]) bits (zero energy; makes wrong starts incoherent)
    symbol relations  from the relation pairs (p, q) of a class: symbols (i, j); i != j -> mu = E[s_i s_j^*]
             (QPSK (d_II + d_QQ + j d_QI - j d_IQ) / 2, d_pq = sgn_p sgn_q [cls_p == cls_q]; BPSK d; pi/2-BPSK
             d e^{j pi (i - j) / 2}), lag n_j - n_i; i == j (QPSK) -> mu2 = E[s_i^2] = j d_IQ (lag 0); mu = 0 dropped
    rotation  QPSK pi/2 linear part = the I / Q swap of every symbol: rank_GF2([G_tx; G_tx swapped]) > K required
             (BLIND_IMPLEMENTATION/01_signal_model.md; = K: the rotated code is the code)
    cost     per move: GA mean m_u (design Es/N0) of the moved source minus the replacement, and the GA SC union bound
             UB = sum_{info} Q(sqrt(m_u / 2)) (fullsys/polar_design.union_bound); a prediction, the BLER is measured
             by run_twin_genie.py

    py sync_cfo/fs/twin_design.py --table            # counting table (all formats, levels, intlv) -> results json
    py sync_cfo/fs/twin_design.py --curve id13       # clean twins / reliability lost per moved bit"""
import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                               # (package) blind/ -> the package root
for _p in (os.path.join(ROOT, "dvbrcs2"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import polar_design as pd  # noqa: E402
import polar_rm as rm  # noqa: E402
import run_polar_genie as rpg  # noqa: E402
from polar import PolarCode, pw_reliability  # noqa: E402

RES = os.path.join(ROOT, "run", "data")
FORMATS = ("id3", "id13", "id42b", "id14s", "vde32")
ADOPTED = {f: ("ga", rpg.DESIGN_SNR[f]) for f in ("id3", "id13", "id42b", "id14s")}
ADOPTED["vde32"] = ("pw", None)                            # VDE: the PW design of the blind receiver (fs-pgv2a)
ADOPTED.update({f: ("ga", rpg.DESIGN_SNR[f]) for f in ("id2", "id5")})   # (2026-11-24) the fs-f2 / fs-f5 blind codes
#                                                            (GA at DESIGN_SNR); not in FORMATS: the tables are unchanged
ADOPTED["pc1024"] = ("ga", rpg.DESIGN_SNR["pc1024"])       # (2026-11-26) N 1024, E = N (mode 'none': pos0 = J, no pre);
#                                                            GA at 0.0 dB; not in FORMATS (tables unchanged)
GA_REF = dict(rpg.DESIGN_SNR)                              # GA means for the cost columns (vde32 -4.2 dB too)
LEVELS = {f: (0.0, 0.25, 0.5, 1.0) for f in FORMATS}
LEVELS["id14s"] = (0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0)   # 803 to move: intermediate counts
PREFIX = (4, 8)                                            # p4 / p8 designs where feasible
CHAN_SEED, PAIR_SEED, PN_SEED = 12345, 4202, 4203
INTLVS = ("none", "base", "adj", "same")
CRC = 32


def bps(fmt):
    return rpg.bps(fmt)


def popcount(a):
    a = np.asarray(a, np.int64)
    return np.array([bin(int(v)).count("1") for v in a.ravel()]).reshape(a.shape)


def plan_kw(fmt):
    """rm_plan / RMPolarCode keywords of the adopted design (as run_polar_genie.get_code)."""
    d, s = ADOPTED[fmt]
    f = rpg.FMTS[fmt]
    kw = dict(design="ga", design_snr_db=s, bps=bps(fmt)) if d == "ga" else {}
    return dict(mode=f["mode"] if f["force"] else None, **kw)


_PLAN = {}


def base_plan(fmt, crc=CRC):
    """The adopted rate-matched plan (cached) + order (least -> most reliable), relrank (N,) and m_u (GA means at
    GA_REF[fmt], for the cost columns)."""
    if (fmt, crc) not in _PLAN:
        f = rpg.FMTS[fmt]
        p = rm.rm_plan(f["A"] + crc, f["E"], **plan_kw(fmt))
        assert p["mode"] == f["mode"], (fmt, p["mode"])
        order = p["ga"]["order"] if p["ga"] is not None else pw_reliability(p["N"])
        rr = np.empty(p["N"], int)
        rr[order] = np.arange(p["N"])
        p = dict(p, order=order, relrank=rr,
                 m_u=pd.ga_design(p["N"], f["E"], p["mode"], p["J"], GA_REF[fmt], bps(fmt))["m_u"])
        _PLAN[(fmt, crc)] = p
    return _PLAN[(fmt, crc)]


def move_lists(p, order="weight"):
    """(src, dst): the first-half info bits in move order and the frozen second-half positions outside pre, most
    reliable first (moving m bits = src[:m] -> dst[:m]; m <= min(len(src), len(dst))). 'search': the greedy list (its
    start point; the moved SETS are not prefixes, see removed_set)."""
    N, info = p["N"], p["info_pos"]
    src = info[info < N // 2]
    rr = p["relrank"]
    if order == "weight":
        src = src[np.lexsort((-rr[src], -popcount(src)))]
    elif order == "low":
        src = src[np.argsort(rr[src], kind="stable")]
    elif order in ("greedy", "search"):
        src = _greedy(p, src)
    else:
        raise ValueError(order)
    cand = np.flatnonzero(p["rel"] & (np.arange(N) >= N // 2))
    dst = cand[np.argsort(-rr[cand], kind="stable")]
    return src, dst


def _twin_cands(p):
    h = p["N"] // 2
    return np.flatnonzero(p["sent_x"][:h] & p["sent_x"][h:])


def _cover(rows, ks):
    """(len(rows), len(ks)) bool: k subset-of i."""
    return (ks[None, :] & ~rows[:, None]) == 0


def _greedy(p, src):
    ks = _twin_cands(p)
    M = _cover(src, ks)
    cnt = M.sum(0).astype(float)
    left, out = list(range(len(src))), []
    rr = p["relrank"][src]
    while left:
        Ml = M[left]
        gain = (Ml & (cnt == 1)[None]).sum(1)
        soft = (Ml / np.maximum(cnt, 1)[None]).sum(1)
        j = int(np.lexsort((rr[left], -soft, -gain))[0])
        r = left.pop(j)
        out.append(src[r])
        cnt -= M[r]
    return np.array(out, int)


_SEARCH = {}


def removed_set(p, order, m):
    """The m first-half info bits moved by a design: src[:m] of move_lists (weight / greedy / low: nested in m);
    'search' (IDEAS_fable2.md 1.3 item 2): the greedy prefix, then best-improvement swaps (one bit in / one out of the
    removed set) while the clean twin count rises (ties: the removed sources' summed Q(sqrt(m_u / 2)) rises = lower
    union bound); not nested in m."""
    src, _ = move_lists(p, order)
    if order != "search" or m == 0 or m >= len(src):
        return src[:m]
    k = (id(p), m)
    if k not in _SEARCH:
        M = _cover(src, _twin_cands(p))                    # (F1, twins): k subset-of i
        q = pd.q_func(np.sqrt(np.maximum(p["m_u"][src], 0) / 2))
        inS = np.zeros(len(src), bool)
        inS[:m] = True
        while True:
            cnt = M[~inS].sum(0)                           # cover count by the bits that stay
            c0, c1 = cnt == 0, cnt == 1
            I, J = np.flatnonzero(inS), np.flatnonzero(~inS)
            nM = ~M[I]
            new = (nM & c0[None]).sum(1)[:, None] + (nM & c1[None]).astype(np.int32) @ (M[J] & c1[None]).T.astype(np.int32)
            dq = q[J][None] - q[I][:, None]                # i back to info, j removed: summed removed Q + q_j - q_i
            cur = int(c0.sum())
            ok = (new > cur) | ((new == cur) & (dq > 1e-15))
            if not ok.any():
                break
            sc = np.where(ok, new, -1)
            a, b = np.unravel_index(np.lexsort((-np.where(ok, dq, -np.inf).ravel(), -sc.ravel()))[0], sc.shape)
            inS[I[a]], inS[J[b]] = False, True
        _SEARCH[k] = src[inS]
    return _SEARCH[k]


# ---- pure freezes (2026-11-23, user idea; sync_cfo/fs/twin_freeze.py): k<m> moves + p first-half info bits FROZEN -------
#   universe U = the k<m> design (order) of the CRC-FREEZE_FROM plan (K_U = A + 32, today's adopted CRC-32 code); a spec
#   at crc c keeps K = A + c (equal payload A; the p <= 32 - c info slots come from the shorter CRC):
#     k<m>z<p>    joint: removed_set(U plan, order, m + p) leaves the first half, only dst[:m] get info (= k<m + p> with
#                 p destinations dropped), then the 32 - c - p least reliable info bits (GA mean m_u) frozen to reach K
#     k<m>z<p>l   the p LEAST reliable staying first-half info bits of U frozen (the cheap reference), then the trim
#     k<m>x<u1>.<u2>...  the listed staying first-half info bits u of U frozen (twin_freeze.py's combination search),
#                 then the trim
#   z0 at crc c = U minus its 32 - c least reliable info bits (not always = k<m> searched on the CRC-c plan: id3)
FREEZE_FROM = 32
_FZ = re.compile(r"^k(\d+)(?:z(\d+)(l?)|x(\d+(?:\.\d+)*))$")
_CRCSUF = re.compile(r"^(.+?)c(\d+)$")


def split_crc(spec):
    """(spec, crc) of a spec with an optional CRC suffix 'c<crc>' ('k18z8c24' -> ('k18z8', 24); none: crc = CRC)."""
    m = _CRCSUF.match(spec)
    return (m.group(1), int(m.group(2))) if m else (spec, CRC)


def _freeze_info(fmt, spec, mz, order, crc):
    """design_info of a pure-freeze spec (block comment above)."""
    f = rpg.FMTS[fmt]
    pu, pc = base_plan(fmt, FREEZE_FROM), base_plan(fmt, crc)
    N, h, K = pu["N"], pu["N"] // 2, f["A"] + crc
    assert pc["N"] == N and np.array_equal(pc["J"], pu["J"]) and np.array_equal(pc["pre"], pu["pre"]), (fmt, crc)
    m = int(mz.group(1))
    lst = [int(v) for v in mz.group(4).split(".")] if mz.group(4) else None
    pz = len(lst) if lst is not None else int(mz.group(2))
    rule = "list" if lst is not None else ("low" if mz.group(3) else "joint")
    src, dst = move_lists(pu, order)
    ntrim = FREEZE_FROM - crc - pz
    meta = dict(spec=spec, kind="freeze", order=order, m=m, z=pz, rule=rule, crc=crc, F1=int(len(src)),
                n_dst=int(len(dst)), trim=int(ntrim), feasible=bool(ntrim >= 0 and m + pz <= len(src) and m <= len(dst)))
    if not meta["feasible"]:
        return None, meta
    if rule == "joint":
        rem = removed_set(pu, order, m + pz)
    else:
        rem = removed_set(pu, order, m)
        stay = np.setdiff1d(src, rem)
        if rule == "low":
            frz = stay[np.argsort(pu["relrank"][stay], kind="stable")[:pz]]
        else:
            frz = np.array(lst, int)
            if not (np.isin(frz, stay).all() and np.unique(frz).size == pz):
                return None, dict(meta, feasible=False, why="listed bits not all staying first-half info bits of U")
        rem = np.concatenate([rem, frz])
    info = np.sort(np.concatenate([np.setdiff1d(pu["info_pos"], rem), dst[:m]]))
    if ntrim:
        info = np.sort(info[np.argsort(-pu["m_u"][info], kind="stable")[:K]])   # the trim: least reliable frozen
    assert info.size == K and not pu["pre"][info].any()
    return info, meta


def design_info(fmt, spec, order="weight", crc=CRC):
    """info_pos (K,) of a design spec ('k<m>', 'f<x>', 'p<F>', 'k0' = base; 'k<m>z<p>[l]' / 'k<m>x<u>...' pure
    freezes, block comment above) + meta; None info if infeasible."""
    mz = _FZ.match(spec)
    if mz:                                                 # (2026-11-23 pure freezes; the older specs never match)
        return _freeze_info(fmt, spec, mz, order, crc)
    p = base_plan(fmt, crc)
    N, K = p["N"], p["info_pos"].size
    src, dst = move_lists(p, order)
    if spec.startswith("p"):
        F = int(spec[1:])
        ok = (np.arange(N) >= N - N // F) & ~p["pre"]
        avail = int(ok.sum())
        meta = dict(spec=spec, kind="prefix", F=F, avail=avail, K=K, feasible=K <= avail)
        if K > avail:
            return None, meta
        c = np.flatnonzero(ok)
        info = np.sort(c[np.argsort(-p["relrank"][c], kind="stable")[:K]])
        return info, dict(meta, moved=int(K - np.isin(info, p["info_pos"]).sum()))
    m = int(round(float(spec[1:]) * len(src))) if spec.startswith("f") else int(spec[1:])
    mmax = min(len(src), len(dst))
    meta = dict(spec=spec, kind="move", order=order, m=m, F1=int(len(src)), n_dst=int(len(dst)), feasible=m <= mmax)
    if m > mmax:
        return None, meta
    info = np.setdiff1d(p["info_pos"], removed_set(p, order, m))
    info = np.sort(np.concatenate([info, dst[:m]]))
    assert info.size == K
    return info, meta


def levels(fmt, order="weight"):
    """Design specs of the default grid: k<m> per LEVELS fraction (+ p4 / p8 where feasible)."""
    src, dst = move_lists(base_plan(fmt), order)
    mm = []
    for x in LEVELS[fmt]:
        m = min(int(round(x * len(src))), len(dst))
        if m not in mm:
            mm.append(m)
    out = [f"k{m}" for m in mm]
    for F in PREFIX:
        if design_info(fmt, f"p{F}", order)[0] is not None:
            out.append(f"p{F}")
    return out


def gen_info(N, info):
    """K x N bool info-row generator: G[r, j] = j subset-of info[r]."""
    j = np.arange(N)
    return (j[None, :] & ~np.asarray(info)[:, None]) == 0


def classes(G, sent):
    """Column classes: cls (N,) int (-1 not sent), 0 = the all-zero column (known 0 bit), ids >= 1 otherwise; equal ids
    = x equal in every codeword."""
    N = G.shape[1]
    cls = np.full(N, -1, int)
    pk = np.packbits(G[:, sent].T, axis=1)
    idx = np.flatnonzero(sent)
    _, inv = np.unique(pk, axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    zero = np.flatnonzero(~pk.any(1))
    zid = inv[zero[0]] if zero.size else -5
    cls[idx] = np.where(inv == zid, 0, inv + 1)
    return cls


def clean_twins(p, info, G=None):
    """Clean twin mask (N/2,) by the cover count, asserted equal to the column test."""
    N = p["N"]
    h = N // 2
    ks = _twin_cands(p)
    f1 = np.asarray(info)[np.asarray(info) < h]
    cov = _cover(f1, ks).any(0) if f1.size else np.zeros(ks.size, bool)
    m = np.zeros(h, bool)
    m[ks[~cov]] = True
    G = gen_info(N, info) if G is None else G
    col = np.zeros(h, bool)
    col[ks] = np.all(G[:, ks] == G[:, ks + h], axis=0)
    assert np.array_equal(m, col), "twin cover count != column test"
    return m


def _pos0(p):
    J, U = p["J"], p["U"]
    if p["mode"] == "puncture":
        return J[U:]
    if p["mode"] == "shorten":
        return J[:p["N"] - U]
    return J.copy()


def tx_map(fmt, p, cls, intlv="base", scr=False, which="all"):
    """chan (E,) (tx bit m = e[chan[m]]), pn (E,) scrambler bits, P (E,) mother x position of tx bit m."""
    E, b = rpg.FMTS[fmt]["E"], bps(fmt)
    pos0 = _pos0(p)
    assert pos0.size == E
    base = np.random.default_rng(CHAN_SEED).permutation(E) if b == 2 else np.arange(E)
    if intlv == "none":
        chan = np.arange(E)
    elif intlv == "base":
        chan = base
    else:
        assert intlv in ("adj", "same") and not (intlv == "same" and b == 1), (intlv, fmt)
        chan = _group_intlv(fmt, p, cls, pos0, base, intlv, which)
    q = np.random.default_rng([PN_SEED, rpg.FMTS[fmt]["tag"]]).integers(0, 2, E // b)
    if not scr:
        pn = np.zeros(E, int)
    elif b == 1:
        pn = q
    elif intlv == "same":                                  # axis hop: the diagonal twin symbol -> +-j (I bit only)
        pn = np.stack([q, np.zeros_like(q)], 1).ravel()
    else:                                                  # symbol sign (both bits): mu = +-1, never (s_I + s_Q) / 2 = 0
        pn = np.repeat(q, 2)
    return chan, pn.astype(np.uint8), pos0[chan]


def _units(p, cls, pos0, which):
    """Relation classes as lists of e indices (size >= 2): 'all' = column classes (no zero class), 'twin' = the clean
    twin pairs (k, k + N/2) only."""
    inv = np.full(p["N"], -1, int)
    inv[pos0] = np.arange(pos0.size)
    if which == "twin":
        h = p["N"] // 2
        k = np.flatnonzero((cls[:h] >= 1) & (cls[:h] == cls[h:]))
        return [[int(inv[a]), int(inv[a + h])] for a in k]
    c = cls[pos0]
    out = {}
    for e, v in enumerate(c):
        if v >= 1:
            out.setdefault(int(v), []).append(e)
    return [u for u in out.values() if len(u) >= 2]


def _group_intlv(fmt, p, cls, pos0, base, intlv, which, units=None):
    """The adj / same channel interleaver (module docstring): blocks of whole symbols, spread evenly."""
    E, b = rpg.FMTS[fmt]["E"], bps(fmt)
    units = _units(p, cls, pos0, which) if units is None else list(units)   # (units: given e-index lists, guess_build)
    rng = np.random.default_rng(PAIR_SEED)
    units = [units[i] for i in rng.permutation(len(units))]
    used = set(e for u in units for e in u)
    rest = [int(e) for e in base if int(e) not in used]
    blocks = []                                            # each: list of e indices or None (filled from rest), len % b == 0
    if b == 1:
        blocks = [list(u) for u in units]
    elif intlv == "adj":
        by = {}
        for u in units:
            by.setdefault(len(u), []).append(u)
        loose = []                                         # an unpaired unit of a size: back among the other bits
        for m, us in sorted(by.items()):
            for i in range(0, len(us) - 1, 2):
                blocks.append([v for t in range(m) for v in (us[i][t], us[i + 1][t])])
            if len(us) % 2:
                loose += us[-1]
        rest = loose + rest
    else:                                                  # same: I / Q of the same symbols; odd tails paired up
        tails = []
        for u in units:
            blocks.append(list(u[:len(u) - len(u) % 2]))
            if len(u) % 2:
                tails.append(u[-1])
        tails += [None] * (len(tails) % 2)
        blocks += [tails[i:i + 2] for i in range(0, len(tails), 2)]
    nb = sum(len(B_) for B_ in blocks) // b               # block symbols
    n = E // b
    F = n - nb
    assert F >= 0, "blocks exceed the burst"
    it = iter(rest)
    out = []
    gaps = np.diff(np.floor(np.arange(len(blocks) + 2) * F / (len(blocks) + 1)).astype(int))
    for j, B_ in enumerate(blocks):
        out += [next(it) for _ in range(gaps[j] * b)]
        out += [next(it) if v is None else v for v in B_]
    out += list(it)
    assert len(out) == E and len(set(out)) == E
    return np.array(out, int)


def sym_relations(fmt, cls, P, pn, which="all", h=None):
    """Symbol relations of the tx map: dict i, j (pairs, i < j), mu (complex), lag = j - i; s0, mu2 (same-symbol,
    QPSK). which 'all' = every pair inside a column class (zero class excluded), 'twin' = (k, k + N/2) pairs only."""
    b, mod = bps(fmt), rpg.FMTS[fmt]["mod"]
    E = P.size
    c = cls[P]                                             # class of tx bit m
    sg = 1 - 2.0 * pn
    sym = np.arange(E) // b
    groups = {}
    if which == "twin":
        inv = np.full(cls.size, -1, int)
        inv[P] = np.arange(E)
        for a in np.flatnonzero((cls[:h] >= 1) & (cls[:h] == cls[h:])):
            groups[a] = [inv[a], inv[a + h]]
    else:
        for m, v in enumerate(c):
            if v >= 1:
                groups.setdefault(int(v), []).append(m)
    sp, ss = set(), set()
    for g in groups.values():
        for x_ in range(len(g)):
            for y_ in range(x_ + 1, len(g)):
                i, j = sym[g[x_]], sym[g[y_]]
                (ss.add(i) if i == j else sp.add((min(i, j), max(i, j))))

    def d(p_, q_):
        return sg[p_] * sg[q_] * float(c[p_] == c[q_] and c[p_] >= 0)

    I, Jj, MU = [], [], []
    for i, j in sorted(sp):
        if b == 2:
            mu = (d(2 * i, 2 * j) + d(2 * i + 1, 2 * j + 1) + 1j * d(2 * i + 1, 2 * j) - 1j * d(2 * i, 2 * j + 1)) / 2
        else:
            mu = d(i, j) * (np.exp(1j * np.pi * (i - j) / 2) if mod == "pi2bpsk" else 1.0)
        if abs(mu) > 1e-12:
            I.append(i), Jj.append(j), MU.append(mu)
    S0, MU2 = [], []
    for i in sorted(ss):
        mu2 = 1j * d(2 * i, 2 * i + 1)
        if abs(mu2) > 1e-12:
            S0.append(i), MU2.append(mu2)
    I, Jj = np.array(I, int), np.array(Jj, int)
    return dict(i=I, j=Jj, mu=np.array(MU, complex), lag=Jj - I, s0=np.array(S0, int), mu2=np.array(MU2, complex))


def gf2_rank(M):
    """Rank over GF(2) of a bool matrix (packed rows, elimination column by column)."""
    A = np.packbits(np.asarray(M, bool), axis=1)
    R, C = M.shape
    r = 0
    for col in range(C):
        if r == R:
            break
        by, bit = col >> 3, np.uint8(1 << (7 - (col & 7)))
        nz = np.flatnonzero(A[r:, by] & bit)
        if not nz.size:
            continue
        pr = r + nz[0]
        if pr != r:
            A[[r, pr]] = A[[pr, r]]
        sel = r + 1 + np.flatnonzero(A[r + 1:, by] & bit)
        if sel.size:
            A[sel, by:] ^= A[r, by:]
        r += 1
    return r


def rotation_rank(G, P):
    """QPSK: rank_GF2([G_tx; G_tx with I / Q swapped per symbol]) (G_tx = G[:, P])."""
    Gt = G[:, P]
    sw = np.arange(P.size).reshape(-1, 2)[:, ::-1].ravel()
    return gf2_rank(np.concatenate([Gt, Gt[:, sw]], 0))


class TwinCode(rm.RMPolarCode):
    """RMPolarCode of a format with the adopted rate matching and an injected info set (design spec)."""

    def __init__(self, fmt, spec="k0", crc=CRC, L=8, order="weight", code_cls=PolarCode):
        f = rpg.FMTS[fmt]
        super().__init__(f["A"], f["E"], crc_len=crc, list_size=L, code_cls=code_cls, **plan_kw(fmt))
        info, meta = design_info(fmt, spec, order, crc)
        assert info is not None, f"{fmt} {spec}: infeasible ({meta})"
        self.spec, self.meta = spec, meta
        if not np.array_equal(info, self.plan["info_pos"]):
            fz = np.ones(self.N, bool)
            fz[info] = False
            assert not (self.plan["pre"] & ~fz).any(), "an info bit on a pre-frozen position"
            self.plan = dict(self.plan, info_pos=info, frozen=fz, rel=fz & ~self.plan["pre"])
            self.code = code_cls(self.N, f["A"], crc, L, info_pos=info, crc_G=rm.crc_matrix(f["A"], crc))
            assert np.array_equal(self.code.frozen, fz)


_BUILD = {}


def build(fmt, spec="k0", intlv="base", scr=False, order="weight", which="all", crc=CRC):
    """Everything a runner needs (cached per process): info, G, cls, chan, pn, P, rel (sym_relations), twins."""
    key = (fmt, spec, intlv, scr, order, which, crc)
    if key not in _BUILD:
        p = base_plan(fmt, crc)
        info, meta = design_info(fmt, spec, order, crc)
        assert info is not None, f"{fmt} {spec}: infeasible ({meta})"
        G = gen_info(p["N"], info)
        cls = classes(G, p["sent_x"])
        tw = clean_twins(p, info, G)
        chan, pn, P = tx_map(fmt, p, cls, intlv, scr, which)
        rel = sym_relations(fmt, cls, P, pn, which, p["N"] // 2)
        _BUILD[key] = dict(fmt=fmt, spec=spec, intlv=intlv, scr=scr, order=order, which=which, info=info, meta=meta,
                           G=G, cls=cls, twins=tw, chan=chan, pn=pn, P=P, rel=rel, N=p["N"], plan=p)
    return _BUILD[key]


def count_row(fmt, spec, intlv, scr=False, order="weight", which="all", rank=True):
    """One counting row (json-safe)."""
    B = build(fmt, spec, intlv, scr, order, which)
    p, info, cls, rel = B["plan"], B["info"], B["cls"], B["rel"]
    N = p["N"]
    sc = cls[cls >= 0]
    _, cnt = np.unique(sc[sc >= 1], return_counts=True)
    lag = rel["lag"]
    full = np.isclose(np.abs(rel["mu"]), 1.0)
    ub = pd.union_bound(p["m_u"], info)
    row = dict(fmt=fmt, spec=spec, intlv=intlv, scr=scr, order=order, which=which, N=N, K=int(info.size),
               E=rpg.FMTS[fmt]["E"], mode=p["mode"], f1_info=int(np.sum(info < N // 2)),
               twin_cands=int(_twin_cands(p).size), clean_twins=int(B["twins"].sum()),
               classes_ge2=int(np.sum(cnt >= 2)), rel_pairs=int(np.sum(cnt * (cnt - 1) // 2)),
               rel_indep=int(np.sum(cnt - 1)), class_sizes={int(k): int(v) for k, v in
                                                            zip(*np.unique(cnt[cnt >= 2], return_counts=True))},
               known_zero_sent=int(np.sum(sc == 0)), sym_pairs=int(lag.size), sym_pairs_full=int(full.sum()),
               same_sym=int(rel["s0"].size), distinct_lags=int(np.unique(lag).size),
               lag_min=int(np.abs(lag).min()) if lag.size else None, lag_med=float(np.median(np.abs(lag))) if lag.size else None,
               lag_max=int(np.abs(lag).max()) if lag.size else None,
               lag_top=[[int(a), int(b)] for a, b in sorted(zip(*np.unique(lag, return_counts=True)),
                                                           key=lambda t: -t[1])[:6]] if lag.size else [],
               ub=ub, ub_base=pd.union_bound(p["m_u"], p["info_pos"]),
               dm_u=float(p["m_u"][p["info_pos"]].sum() - p["m_u"][info].sum()), meta=B["meta"])
    if rank and bps(fmt) == 2:
        row["rot_rank"] = int(rotation_rank(B["G"], B["P"]))
        row["rot_ok"] = row["rot_rank"] > row["K"]
    return row


def curve(fmt, order="weight"):
    """Per moved bit m = 0 .. min(F1, dst): clean twins, the moved source / destination, its weight, GA mean lost
    m_u(src) - m_u(dst), cumulative, union bound (json-safe list)."""
    p = base_plan(fmt)
    src, dst = move_lists(p, order)
    ks = _twin_cands(p)
    M = _cover(src, ks)
    cnt = M.sum(0)
    mu = p["m_u"]
    info = p["info_pos"].copy()
    q = pd.q_func(np.sqrt(np.maximum(mu, 0) / 2))
    ub = float(q[info].sum())
    out = [dict(m=0, clean=int(np.sum(cnt == 0)), ub=ub, dmu=0.0, cum_dmu=0.0)]
    cum = 0.0
    if order == "search":                                  # sets not nested: one search per m
        for m in range(1, min(len(src), len(dst)) + 1):
            rm_ = removed_set(p, order, m)
            st = ~np.isin(src, rm_)
            out.append(dict(m=m, clean=int(np.sum(~M[st].any(0))), removed=rm_.tolist(),
                            cum_dmu=float(mu[rm_].sum() - mu[dst[:m]].sum()),
                            ub=float(q[info].sum() - q[rm_].sum() + q[dst[:m]].sum())))
        return out
    for m in range(min(len(src), len(dst))):
        cnt = cnt - M[m]
        dmu = float(mu[src[m]] - mu[dst[m]])
        cum += dmu
        ub += float(q[dst[m]] - q[src[m]])
        out.append(dict(m=m + 1, clean=int(np.sum(cnt == 0)), src=int(src[m]), wt=int(popcount(src[m])),
                        dst=int(dst[m]), dmu=dmu, cum_dmu=cum, ub=ub,
                        pw_rank_lost=int(p["relrank"][src[m]] - p["relrank"][dst[m]])))
    return out


# ---- move + GUESS (sync_cfo/IDEAS_fable2.md 1.1-1.3, 1.7) and the B2 cluster comb (2.3), 2026-11-19 -------------------
#   twin vector  a_k[r] = 1 iff the r-th staying first-half info bit i covers k (x_k XOR x_{k+N/2} = a_k . v)
#   guess space  W = span of a basis of twin vectors chosen greedily in PAIRS (largest coset of the reduced a_k first,
#                look-ahead: the pair (g1, g2) of the GUESS_TOP largest cosets maximising |g1| + |g2| + |g1 + g2|);
#                U_m = the twins with a_k in the first-m-vector span (U_0 = clean twins), bin = coordinates of a_k in
#                that basis (an m-bit integer); the guessed bits y_c = x_{b_c} XOR x_{b_c + N/2} of the basis twins b_c
#   maps         adj   every twin of U_mmax as a unit in the I2 pair interleaver (_group_intlv: BPSK 2 consecutive
#                      symbols; QPSK two twins side by side on I / Q of 2 consecutive symbols), symbol-sign scrambler
#                cl<L> (QPSK, B2) the clean twins on I / Q of one symbol (diagonal), C = ceil(P / L) clusters of L
#                      consecutive symbols at o + c Delta (Delta = n // C), axis-hop scrambler (I bit) on them
#                sp<L> cl<L> + the guessed twins (U_mmax minus U_0) adj in the gaps (symbol-sign scrambler there)
#                ad<p>c<L> (QPSK, IDEAS_combo.md C13, 2026-11-19) the CLEAN twins split: 2 round(p C / 200) of the C (a
#                      fixed rng(PAIR_SEED + 1) choice) adj in the gaps, the rest diagonal as cl<L>; no guessed twins
#                      (ad0c<L> = cl<L> exactly)
#                rd    (QPSK, 2026-11-23, mod_cfo_fe E6) the clean twins diagonal as cl<L> but at P pseudo-random symbols
#                      default_rng([RD_SEED, tag]).choice(n, P) (no clusters / comb), axis hop on them; no guessed twins
GUESS_LEVELS = (0, 2, 4, 6, 8, 10, 12, 16)
GUESS_TOP = 128
SWEEP_N = (0, 3, 6, 9, 12, 18, 24)
GMAPS = ("adj", "cl4", "cl8", "sp4", "sp8")               # (+ 'rd', 2026-11-23: diagonal at random symbols, _rand_intlv)
RD_SEED = 4304                                             # rd positions default_rng([RD_SEED, tag])
_GS, _GB = {}, {}


def sweep_ns(fmt):
    """Moved n of the A-fe / A-ber sweep (IDEAS_fable2.md 1.7): SWEEP_N capped at min(F1, dst) (+ the cap itself,
    VDE 25); id14s 0 / 12 / 24 (the expected null)."""
    if fmt == "id14s":
        return [0, 12, 24]
    src, dst = move_lists(base_plan(fmt))
    cap = min(len(src), len(dst))
    ns = sorted(set(min(n, cap) for n in SWEEP_N))
    return ns + ([cap] if max(SWEEP_N) < cap <= max(SWEEP_N) + 3 else [])


def same_design(fmt, spec, order_a, order_b, crc=CRC):
    """True iff the two orders give the same info set for spec (e.g. search = greedy at some n: one case suffices)."""
    a, b = design_info(fmt, spec, order_a, crc)[0], design_info(fmt, spec, order_b, crc)[0]
    return a is not None and b is not None and np.array_equal(a, b)


def split_of(gmap):
    """(adjacent share p / 100, cluster L) of a split map ad<p>c<L>; None for any other map (adj included)."""
    if not gmap.startswith("ad") or gmap == "adj":
        return None
    p, L = gmap[2:].split("c")
    return int(p) / 100.0, int(L)


def _bitints(M):
    """(F, K) bool -> K Python ints (bit r = row r)."""
    if M.shape[0] == 0:
        return [0] * M.shape[1]
    pk = np.packbits(M.T, axis=1, bitorder="little")
    return [int.from_bytes(r.tobytes(), "little") for r in pk]


def guess_space(fmt, spec, order="greedy", mmax=16, crc=CRC):
    """Guess subspace of a moved design (block comment above): ks (twin candidates k < N/2), level (K,) = the guess
    level at which twin k enters U (0 = clean, -1 = never up to mmax), coords (K,) its Walsh bin, basis (dims,) the
    basis twins k, dims, used {m: |U_m|} for GUESS_LEVELS (m > dims: = dims)."""
    key = (fmt, spec, order, mmax, crc)
    if key in _GS:
        return _GS[key]
    p = base_plan(fmt, crc)
    info, meta = design_info(fmt, spec, order, crc)
    assert info is not None, f"{fmt} {spec}: infeasible ({meta})"
    h = p["N"] // 2
    ks = _twin_cands(p)
    f1 = info[info < h]
    av = _bitints(_cover(f1, ks))
    rows = []                                              # Gauss-Jordan rows [pivot, vec, combo]: vec = XOR_{c in combo} w_c

    def red(v):
        c = 0
        for pv, w, cb in rows:
            if v >> pv & 1:
                v ^= w
                c ^= cb
        return v, c

    def insert(v, ci):
        v, c = red(v)
        assert v, "dependent basis vector"
        c ^= 1 << ci
        pv = v.bit_length() - 1
        for r in rows:
            if r[1] >> pv & 1:
                r[1] ^= v
                r[2] ^= c
        rows.append([pv, v, c])

    K = ks.size
    level = np.where(np.array([a == 0 for a in av], bool), 0, -1)
    coords = np.zeros(K, np.int64)
    basis, dim = [], 0
    while dim < mmax:
        left = np.flatnonzero(level < 0)
        if not left.size:
            break
        R = {}
        for t in left:
            R.setdefault(red(av[t])[0], []).append(int(t))
        top = sorted(R, key=lambda g: (-len(R[g]), R[g][0]))[:GUESS_TOP]
        pick = [top[0]]
        if mmax - dim >= 2 and len(top) >= 2:
            best = (-1, 0, 1)
            for x in range(len(top)):
                for y in range(x + 1, len(top)):
                    s = len(R[top[x]]) + len(R[top[y]]) + len(R.get(top[x] ^ top[y], ()))
                    if s > best[0]:
                        best = (s, x, y)
            pick = [top[best[1]], top[best[2]]]
        for g in pick:
            t = R[g][0]
            insert(av[t], dim)
            basis.append(t)
            dim += 1
        for t in left:
            v, c = red(av[t])
            if v == 0:
                level[t], coords[t] = dim, c
    used = {m: int(np.sum((level >= 0) & (level <= m))) for m in GUESS_LEVELS if m <= mmax}
    out = dict(ks=ks, f1=f1, level=level, coords=coords, basis=ks[np.array(basis, int)], dims=dim, used=used,
               meta=meta)
    _GS[key] = out
    return out


def _comb_intlv(fmt, base, dunits, aunits, L):
    """cl<L> / sp<L> channel interleaver (QPSK): chan (E,), the diagonal symbols (P,), geometry dict(L, C, P, delta,
    o). dunits: clean twin units -> one diagonal symbol each (I, Q), clusters of L at o + c delta; aunits: adj twin
    units, two side by side on 2 consecutive free symbols, spread evenly over the free symbols; the rest in base
    order."""
    E = rpg.FMTS[fmt]["E"]
    n = E // 2
    rng = np.random.default_rng(PAIR_SEED)
    dunits = [dunits[i] for i in rng.permutation(len(dunits))]
    aunits = [aunits[i] for i in rng.permutation(len(aunits))]
    Pd = len(dunits)
    C = -(-Pd // L) if Pd else 0
    content = [None] * n
    geo = dict(L=L, C=C, P=Pd, delta=0, o=0)
    dsym = []
    if C:
        dl = n // C
        assert dl >= L, (fmt, Pd, L)
        o = (n - (C - 1) * dl - L) // 2
        for idx, u in enumerate(dunits):
            c, i = divmod(idx, L)
            content[o + c * dl + i] = (u[0], u[1])
            dsym.append(o + c * dl + i)
        geo.update(delta=dl, o=o)
    blocks = [[(aunits[x][0], aunits[x + 1][0]), (aunits[x][1], aunits[x + 1][1])] for x in range(0, len(aunits) - 1, 2)]
    loose = list(aunits[-1]) if len(aunits) % 2 else []
    used = set(e for u in dunits + aunits for e in u)
    rest = loose + [int(e) for e in base if int(e) not in used]
    free = [s for s in range(n) if content[s] is None]
    nb, nf = len(blocks), len(free)
    tgt = [(j + 1) * (nf - 2 * nb) // (nb + 1) + 2 * j for j in range(nb)]
    it = iter(rest)
    bj = f = 0
    while f < nf:
        if bj < nb and f >= tgt[bj] and f + 1 < nf and free[f + 1] == free[f] + 1:
            content[free[f]], content[free[f + 1]] = blocks[bj]
            bj, f = bj + 1, f + 2
        else:
            content[free[f]] = (next(it), next(it))
            f += 1
    assert bj == nb, "adj blocks left over"
    chan = np.array([e for c_ in content for e in c_], int)
    assert len(chan) == E and len(set(chan.tolist())) == E
    return chan, np.array(sorted(dsym), int), geo


def _rand_intlv(fmt, base, dunits):
    """rd channel interleaver (QPSK, 2026-11-23, mod_cfo_fe E6): the clean twin units -> one diagonal symbol each (I, Q)
    at P pseudo-random symbols default_rng([RD_SEED, tag]).choice(n, P) (no clusters, no comb), the rest in base order;
    chan (E,), the diagonal symbols (sorted), geo dict(kind 'rd', P, seed) (no L / C / delta: not a twin_sweep dg map)."""
    E = rpg.FMTS[fmt]["E"]
    n = E // 2
    Pd = len(dunits)
    dunits = [dunits[i] for i in np.random.default_rng(PAIR_SEED).permutation(Pd)]
    pos = np.random.default_rng([RD_SEED, rpg.FMTS[fmt]["tag"]]).choice(n, Pd, replace=False) if Pd else np.zeros(0, int)
    content = [None] * n
    for s_, u in zip(pos, dunits):
        content[int(s_)] = (u[0], u[1])
    used = set(e for u in dunits for e in u)
    it = iter([int(e) for e in base if int(e) not in used])
    for s_ in range(n):
        if content[s_] is None:
            content[s_] = (next(it), next(it))
    chan = np.array([e for c_ in content for e in c_], int)
    assert len(chan) == E and len(set(chan.tolist())) == E
    return chan, np.sort(pos).astype(int), dict(kind="rd", P=Pd, seed=RD_SEED)


# ---- more twin layouts (2026-11-23, mod_cfo_fe E6g / E8; QPSK, CLEAN twins unless guessed): guess_build gmap ------------
#   cb<D>   diagonal (I / Q of one symbol, axis hop) on a regular comb of spacing D symbols: Tu = min(n // D, P) teeth, W =
#           ceil(P / Tu) consecutive symbols per tooth (twin c -> tooth c % Tu, offset c // Tu), centred; W <= D - 2 (D // 4)
#           (else infeasible). The squared line has grating lobes at 2 f = j / D
#   cj<D>   cb<D> with every tooth moved by a fixed integer U[-D // 4, D // 4] (default_rng([RD_SEED + 2, tag, D])): mixed
#   rdg<g>  rd with the GUESSED twins in the span of the first g basis twins (coords < 2^g; = guess level <= g for even g,
#           guess_space mmax 16; odd g allowed) diagonal too (rd positions for the clean +
#           guessed units): w2 s^2 = (-1)^{popcount(dco & y)}, dco = the twin's Walsh coords, y = the g basis twins' XORs
#           (e[be1] ^ e[be2], bit c = basis c): 2^g receiver hypotheses
#   hd<D>   half-symbol twins: one twin on the I bits of symbols i and j = i + D (Q bits = other bits), i pseudo-random with
#           both I slots free (default_rng([RD_SEED + 3, tag, D])); E[s_i s_j^*] = E[s_i s_j] = sg_i sg_j / 2
#   hr      half-symbol twins at 2 P pseudo-random I slots (pair k = (pos_k, pos_{P+k}), random lags; RD_SEED + 4)
#   fd<D>   full-symbol lag pairs: two twins on (I, Q) of symbol i and (I, Q) of symbol i + D (s_j = sg_i sg_j s_i, mu =
#           1), i pseudo-random with both symbols free (RD_SEED + 5); an odd last twin stays in base order
#   pairs: (pi, pj) symbols, lag pi - pj, pw = sg_i sg_j (symbol-sign scrambler on every symbol), amp = |mu| (1/2 / 1):
#   z = pw r_i r_j^* has mean amp e^{j 2 pi f (i - j)}; kind 'diag' / 'half' / 'full'
class Infeasible(ValueError):
    """A layout that does not fit the burst (guess_build raises it; mod_cfo_fe skips the wave)."""


def layout_of(gmap):
    """(kind, D / g) of a 2026-11-23 layout gmap (block comment above); None for the older maps (adj, rd, cl / sp / ad)."""
    for pre in ("rdg", "cb", "cj", "hd", "fd"):
        if gmap.startswith(pre) and gmap[len(pre):].isdigit() and int(gmap[len(pre):]) >= 1:
            return pre, int(gmap[len(pre):])
    return ("hr", 0) if gmap == "hr" else None


def _comb_pos(n, P, D, rng=None):
    """cb / cj diagonal symbols (P,) (index c = twin c) or None if infeasible (rng: the cj tooth jitter)."""
    J = D // 4
    Tu = min(n // D, P)
    if Tu < 1:
        return None
    W = -(-P // Tu)
    if W > D - 2 * J:
        return None
    c = np.arange(P)
    tooth, off = c % Tu, c // Tu
    jit = rng.integers(-J, J + 1, Tu) if rng is not None else np.zeros(Tu, int)
    o = (n - ((Tu - 1) * D + W)) // 2
    pos = o + tooth * D + jit[tooth] + off
    if pos.min() < 0 or pos.max() >= n or np.unique(pos).size != P:
        return None
    return pos.astype(int)


def _fill(fmt, base, I, Q):
    """chan (E,) from per-symbol I / Q e indices (-1 = free): the free slots in symbol order (I, Q) get the unused e
    indices in base order."""
    E = rpg.FMTS[fmt]["E"]
    content = np.stack([I, Q], 1).ravel().copy()
    used = set(int(e) for e in content if e >= 0)
    rest = [int(e) for e in base if int(e) not in used]
    free = np.flatnonzero(content < 0)
    assert len(rest) == free.size, (fmt, len(rest), free.size)
    content[free] = rest
    assert len(content) == E and len(set(content.tolist())) == E
    return content.astype(int)


def _layout_build(fmt, spec, order, gmap, mmax, crc):
    """guess_build of a 2026-11-23 layout (block comment above); raises Infeasible."""
    kind, D = layout_of(gmap)
    p = base_plan(fmt, crc)
    N, h, E, b = p["N"], p["N"] // 2, rpg.FMTS[fmt]["E"], bps(fmt)
    assert b == 2, (fmt, gmap)
    n = E // 2
    tag = rpg.FMTS[fmt]["tag"]
    gs = guess_space(fmt, spec, order, mmax, crc)
    info = design_info(fmt, spec, order, crc)[0]
    pos0 = _pos0(p)
    inv = np.full(N, -1, int)
    inv[pos0] = np.arange(E)
    ks, lev = gs["ks"], gs["level"]
    ng = D if kind == "rdg" else 0
    if kind == "rdg" and D > gs["dims"]:
        raise Infeasible(f"{fmt} {spec} {gmap}: {gs['dims']} guess dims")
    sel = np.flatnonzero((lev >= 0) & ((gs["coords"] >> ng) == 0))   # clean (+ the twins in the span of the first g
    sel = sel[lev[sel] >= 0]                                 # basis twins: = level <= g for even g; odd g works too as
    sel = sel[np.random.default_rng(PAIR_SEED).permutation(sel.size)]   # the basis is built in pairs), PAIR_SEED order
    units =[(int(inv[ks[t]]), int(inv[ks[t] + h])) for t in sel]
    base = np.random.default_rng(CHAN_SEED).permutation(E)
    q = np.random.default_rng([PN_SEED, tag]).integers(0, 2, n)
    pn = np.repeat(q, 2)
    I, Q = np.full(n, -1, int), np.full(n, -1, int)
    P = len(units)
    dsym, dco = np.zeros(0, int), np.zeros(0, np.int64)
    pi, pj = np.zeros(0, int), np.zeros(0, int)
    geo = dict(kind=kind, D=D, P=P)
    if kind in ("rdg", "cb", "cj"):
        if kind == "rdg":
            pos = np.random.default_rng([RD_SEED, tag]).choice(n, P, replace=False) if P else np.zeros(0, int)
        else:
            pos = _comb_pos(n, P, D, np.random.default_rng([RD_SEED + 2, tag, D]) if kind == "cj" else None)
            if pos is None:
                raise Infeasible(f"{fmt} {spec} {gmap}: {P} twins do not fit a spacing-{D} comb of {n} symbols")
            geo.update(Tu=min(n // D, P), W=-(-P // min(n // D, P)))
        for s_, u in zip(pos, units):
            I[s_], Q[s_] = u
        o_ = np.argsort(pos)
        dsym = np.asarray(pos, int)[o_]
        dco = gs["coords"][sel][o_].astype(np.int64)
        pn[2 * dsym + 1] = 0                                   # axis hop on the diagonal symbols (I bit only)
    elif kind in ("hd", "hr"):
        if kind == "hd":
            fr, a_, c_ = np.ones(n, bool), [], []
            for i in np.random.default_rng([RD_SEED + 3, tag, D]).permutation(max(n - D, 0)):
                if len(a_) == P:
                    break
                if fr[i] and fr[i + D]:
                    fr[i] = fr[i + D] = False
                    a_.append(int(i)), c_.append(int(i + D))
            if len(a_) < P:
                raise Infeasible(f"{fmt} {spec} {gmap}: {len(a_)} of {P} lag-{D} I-slot pairs")
            pi, pj = np.array(a_, int), np.array(c_, int)
        else:
            if 2 * P > n:
                raise Infeasible(f"{fmt} {spec} {gmap}: {2 * P} I slots > {n}")
            pos = np.random.default_rng([RD_SEED + 4, tag]).choice(n, 2 * P, replace=False)
            pi, pj = pos[:P].astype(int), pos[P:].astype(int)
        for k_, u in enumerate(units):
            I[pi[k_]], I[pj[k_]] = u
    else:                                                      # fd<D>: two twins per symbol pair
        fr, a_, c_ = np.ones(n, bool), [], []
        npr = P // 2
        for i in np.random.default_rng([RD_SEED + 5, tag, D]).permutation(max(n - D, 0)):
            if len(a_) == npr:
                break
            if fr[i] and fr[i + D]:
                fr[i] = fr[i + D] = False
                a_.append(int(i)), c_.append(int(i + D))
        if len(a_) < npr:
            raise Infeasible(f"{fmt} {spec} {gmap}: {len(a_)} of {npr} lag-{D} symbol pairs")
        pi, pj = np.array(a_, int), np.array(c_, int)
        for k_ in range(npr):
            ua, ub = units[2 * k_], units[2 * k_ + 1]
            I[pi[k_]], Q[pi[k_]], I[pj[k_]], Q[pj[k_]] = ua[0], ub[0], ua[1], ub[1]
    chan = _fill(fmt, base, I, Q)
    pn = pn.astype(np.uint8)
    s0 = rpg.modulate(pn[None], fmt)[0]                    # the symbols of x = 0 (scrambler / rotation only)
    sg = 1.0 - 2.0 * pn[0::2]                              # I-bit scrambler sign per symbol (= Q's off the diagonal)
    amp = 0.5 if kind in ("hd", "hr") else 1.0
    o_ = np.argsort(pi, kind="stable")
    pi, pj = pi[o_], pj[o_]
    return dict(fmt=fmt, spec=spec, order=order, gmap=gmap, info=info, G=gen_info(N, info), gs=gs, chan=chan, pn=pn,
                P=pos0[chan], geo=geo, kind=("diag" if kind in ("rdg", "cb", "cj") else "half" if amp < 1 else "full"),
                pi=pi, pj=pj, pw=sg[pi] * sg[pj], amp=amp, ep=np.zeros(0, int), ecoord=np.zeros(0, np.int64),
                elev=np.zeros(0, int), ewt=np.zeros(0), s0=dsym, w2=np.conj(s0[dsym] ** 2), dco=dco, ng=ng,
                be1=inv[gs["basis"]], be2=inv[gs["basis"] + h], N=N, plan=p)


def guess_build(fmt, spec, order="greedy", gmap="adj", mmax=16, crc=CRC):
    """Tx map + receiver relations of a move + guess design (cached per process): info, G, gs (guess_space), chan, pn,
    P, geo (cl / sp), pairs (pi, pj, pw: Re(pw r_i r_j^*) has mean sum over its twins of wt (-1)^{a_k . v}), entries
    (ep pair, ecoord bin, elev level, ewt = 1 / bps: QPSK one product feeds two twins' bins), diag (s0 symbols, w2 =
    conj(E s^2)), be1 / be2 (e indices of the basis twins: y_c = e[be1] XOR e[be2])."""
    key = (fmt, spec, order, gmap, mmax, crc)
    if key in _GB:
        return _GB[key]
    if layout_of(gmap) is not None:                        # cb / cj / rdg / hd / hr / fd (2026-11-23): own builder
        _GB[key] = _layout_build(fmt, spec, order, gmap, mmax, crc)
        return _GB[key]
    p = base_plan(fmt, crc)
    N, h, E, b = p["N"], p["N"] // 2, rpg.FMTS[fmt]["E"], bps(fmt)
    gs = guess_space(fmt, spec, order, mmax, crc)
    info = design_info(fmt, spec, order, crc)[0]
    G = gen_info(N, info)
    pos0 = _pos0(p)
    inv = np.full(N, -1, int)
    inv[pos0] = np.arange(E)
    ks, lev = gs["ks"], gs["level"]
    use, clean = lev >= 0, lev == 0
    base = np.random.default_rng(CHAN_SEED).permutation(E) if b == 2 else np.arange(E)
    q = np.random.default_rng([PN_SEED, rpg.FMTS[fmt]["tag"]]).integers(0, 2, E // b)
    unit = lambda k: [int(inv[k]), int(inv[k + h])]  # noqa: E731
    geo = None
    if gmap == "adj":
        chan = _group_intlv(fmt, p, None, pos0, base, "adj", None, units=[unit(k) for k in ks[use]])
        pn = q.copy() if b == 1 else np.repeat(q, 2)
    elif gmap == "rd":                                     # rd: every clean twin diagonal at pseudo-random symbols
        assert b == 2, (fmt, gmap)
        chan, dsym, geo = _rand_intlv(fmt, base, [unit(k) for k in ks[clean]])
        pn = np.repeat(q, 2)
        pn[2 * dsym + 1] = 0                               # axis hop on the diagonal symbols (I bit only)
    elif split_of(gmap) is not None:                       # ad<p>c<L>: the clean twins split adj / diagonal (C13)
        assert b == 2, (fmt, gmap)
        sh, Lc = split_of(gmap)
        cu = [unit(k) for k in ks[clean]]
        na = 2 * int(round(sh * len(cu) / 2))
        sel = np.zeros(len(cu), bool)
        sel[np.random.default_rng(PAIR_SEED + 1).permutation(len(cu))[:na]] = True
        chan, dsym, geo = _comb_intlv(fmt, base, [u for u, s_ in zip(cu, sel) if not s_],
                                      [u for u, s_ in zip(cu, sel) if s_], Lc)
        pn = np.repeat(q, 2)
        pn[2 * dsym + 1] = 0                               # axis hop on the diagonal symbols (I bit only)
    else:
        assert b == 2 and gmap[:2] in ("cl", "sp"), (fmt, gmap)
        au = [unit(k) for k in ks[use & ~clean]] if gmap.startswith("sp") else []
        chan, dsym, geo = _comb_intlv(fmt, base, [unit(k) for k in ks[clean]], au, int(gmap[2:]))
        pn = np.repeat(q, 2)
        pn[2 * dsym + 1] = 0                               # axis hop on the diagonal symbols (I bit only)
    pn = pn.astype(np.uint8)
    P = pos0[chan]
    tinv = np.empty(E, int)
    tinv[chan] = np.arange(E)                              # tx bit index of e index
    s0 = rpg.modulate(pn[None], fmt)[0]                    # the symbols of x = 0 (scrambler / rotation only)
    prs, dg = {}, []
    for t in np.flatnonzero(use):
        m1, m2 = tinv[inv[ks[t]]], tinv[inv[ks[t] + h]]
        i, j = m1 // b, m2 // b
        if i == j:
            if clean[t] and geo is not None:               # (adj: a twin that falls on I / Q of one symbol by chance
                dg.append(i)                               # is not a diagonal line: no comb geometry, no axis hop)
            continue
        if b == 2 and m1 % 2 != m2 % 2:                    # I with Q: not a Walsh term (not built by these maps)
            continue
        if gmap.startswith("cl") or gmap == "rd" or abs(j - i) != 1:   # only the map's adjacent units (cl / rd: none;
            continue                                       # the twins left in base order are dropped)
        if split_of(gmap) is not None and not clean[t]:    # ad: only the placed clean units (no guessed twins)
            continue
        prs.setdefault((min(i, j), max(i, j)), []).append(int(t))
    kp = sorted(prs)
    pi = np.array([a for a, _ in kp], int)
    pj = np.array([c for _, c in kp], int)
    et = [t for k_ in kp for t in prs[k_]]
    ep = np.array([x for x, k_ in enumerate(kp) for _ in prs[k_]], int)
    dg = np.array(sorted(dg), int)
    out = dict(fmt=fmt, spec=spec, order=order, gmap=gmap, info=info, G=G, gs=gs, chan=chan, pn=pn, P=P, geo=geo,
               pi=pi, pj=pj, pw=np.conj(s0[pi]) * s0[pj], ep=ep, ecoord=gs["coords"][et], elev=lev[et],
               ewt=np.full(len(et), 1.0 / b), s0=dg, w2=np.conj(s0[dg] ** 2),
               be1=inv[gs["basis"]], be2=inv[gs["basis"] + h], N=N, plan=p)
    _GB[key] = out
    return out


def guess_rows(fmts, orders=("greedy", "search")):
    """Counting rows of the sweep designs: used twins per guess level (json-safe)."""
    out = []
    for fmt in fmts:
        p = base_plan(fmt)
        for order in orders:
            for n in sweep_ns(fmt):
                gs = guess_space(fmt, f"k{n}", order)
                info = design_info(fmt, f"k{n}", order)[0]
                out.append(dict(fmt=fmt, order=order, n=n, dims=gs["dims"], used=gs["used"],
                                ub=pd.union_bound(p["m_u"], info), ub_base=pd.union_bound(p["m_u"], p["info_pos"])))
                print(f"{fmt:6s} {order:6s} k{n:<3d} dims {gs['dims']:2d} used " + " ".join(
                    f"{m}:{u}" for m, u in gs["used"].items()) + f" | UB x{out[-1]['ub'] / out[-1]['ub_base']:.2f}",
                      flush=True)
    return out


def _fmt_row(r):
    rk = f"{r['rot_rank']:5d}{' ok' if r['rot_ok'] else ' NO'}" if "rot_rank" in r else "    -   "
    lg = f"{r['lag_min']}/{r['lag_med']:.0f}/{r['lag_max']}" if r["lag_min"] is not None else "-"
    return (f"{r['fmt']:6s} {r['spec']:6s} {r['intlv']:4s}{'+s' if r['scr'] else '  '} F1 {r['f1_info']:4d} twins "
            f"{r['clean_twins']:4d}/{r['twin_cands']:4d} rel {r['rel_indep']:4d} ({r['rel_pairs']:5d} pairs) "
            f"zero {r['known_zero_sent']:3d} | sym pairs {r['sym_pairs']:5d} (mu=1 {r['sym_pairs_full']:5d}) same "
            f"{r['same_sym']:4d} lags {r['distinct_lags']:4d} |lag| min/med/max {lg:14s} top {r['lag_top'][:3]} | "
            f"rot {rk} | UB {r['ub']:.2e} (base {r['ub_base']:.2e}) dm_u {r['dm_u']:+.1f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", action="store_true", help="the counting table (all formats / levels / intlv)")
    ap.add_argument("--curve", nargs="*", default=None, help="per-move curves of these formats (none: all)")
    ap.add_argument("--fmts", nargs="+", default=list(FORMATS))
    ap.add_argument("--order", default="weight", choices=["weight", "greedy", "search", "low"])
    ap.add_argument("--guess", action="store_true", help="used twins per (moved n, guessed m) of the orders greedy / "
                    "search (guess_space; counting only) -> results/<--out>")
    ap.add_argument("--no-rank", action="store_true", help="skip the GF(2) rotation rank (seconds per row)")
    ap.add_argument("--out", default="twin_design_count.json")
    a = ap.parse_args()
    doc = dict(order=a.order, rows=[], curves={})
    if a.guess:
        doc["guess"] = guess_rows(a.fmts)
    if a.table:
        for fmt in a.fmts:
            for spec in levels(fmt, a.order):
                for il, sc in (("base", False), ("adj", True)) + ((("same", True),) if bps(fmt) == 2 else ()):
                    r = count_row(fmt, spec, il, sc, a.order, rank=not a.no_rank)
                    doc["rows"].append(r)
                    print(_fmt_row(r), flush=True)
            for F in PREFIX:
                _, mt = design_info(fmt, f"p{F}", a.order)
                if not mt["feasible"]:
                    print(f"{fmt:6s} p{F}: infeasible (K {mt['K']} > {mt['avail']} positions in the last N/{F} "
                          f"outside pre)", flush=True)
    if a.curve is not None:
        for fmt in (a.curve or a.fmts):
            c = curve(fmt, a.order)
            doc["curves"][fmt] = c
            step = max(1, len(c) // 12)
            print(f"{fmt}: m clean ub cum_dmu | " + " | ".join(
                f"{r['m']} {r['clean']} {r['ub']:.1e} {r['cum_dmu']:.0f}" for r in c[::step] + [c[-1]]), flush=True)
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, a.out), "w") as fh:
        json.dump(doc, fh, indent=1)


if __name__ == "__main__":
    main()
