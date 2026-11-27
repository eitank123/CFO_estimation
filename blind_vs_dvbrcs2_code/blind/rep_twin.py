"""Repetition twins (2026-11-23, literature-scout idea): a twin made by REPEATING a coded bit, not by moving info bits into
frozen positions (twin_design k<m>). Code = the rate-matched (E - t, K) polar code (fullsys/polar_rm.rm_plan, 38.212
puncture / shorten rule, same K = A + crc) plus t of its coded bits sent twice; the copy goes on the Q bit of the symbol
whose I bit carries the original, i.e. t DIAGONAL symbols (I = Q up to the scrambler: the twin_design 'same' / rd
semi-pilot, s^2 known). The receiver MRC-adds the two LLRs (the copy's energy is kept); each twin costs one degree of
freedom. The placement of the t diagonal symbols is free (no Plotkin structure). Imported read-only: twin_design,
fullsys/polar_rm.py, polar_design.py, run_polar_genie.py; nothing there is changed.

    code     e1 (B, E - t) = RMPolarCode(A, E - t).encode_rm, extended e = [e1, e1[:, rep]] (E bits; e index E - t + k =
             the copy of e1[rep[k]]); rx: l1 = le[:, :E - t], l1[:, rep] += le[:, E - t:] (MRC), then the (E - t) rate
             recovery + CA-SCL-L. The (E - t) plan keeps N, the mode is asserted equal to the format's (id13 / id3:
             puncture, N 4096 / 1024)
    channel  GA (fullsys/polar_design) at Es/N0 s: m_x = rm_channel_means(N, E - t, ...) (mu = 4 Es / (bps N0) per sent
             bit) + mu at the mother positions pos0[rep] of the repeated bits (MRC: mean 2 mu); UB = sum_info Q(sqrt(m_u / 2))
    info     aware (default): the K most reliable u outside pre under that channel (GA at GA_REF = DESIGN_SNR); plain ('p'
             suffix): the (E - t) uniform-channel design (rm_plan's info set), repetition ignored
    rules    which coded bits of e1 to repeat (rep = e1 indices):
               gr   greedy on the GA union bound: GR_BLOCK bits per round with the largest first-order gain -dUB/dm_x mu
                    (forward GA with the stage inputs kept, backward chain rule; f by one-sided secants, GR_H), the aware
                    info set re-designed every round
               pnc  e1[0 .. t - 1] = y[U' .. U' + t - 1]: the bits the puncturer would drop next (low sub-blocks)
               rnd  default_rng([REP_SEED, tag, t]).choice(E - t, t)
               wst  the t smallest first-order gains (one shot, plain info set): the bad reference
    loss     dB shift d with UB_design(s0 + d) = UB_base(s0), s0 = GA_REF (bisection on the Es/N0 axis, every design's info
             set fixed); also the k<m> moved-bit designs (twin_design.design_info, orders greedy / search) on the base
             channel, with their clean twin count (= the rd diagonal symbols P); resolution ~0.01 dB (k0 gives -0.005 /
             -0.010: the 2 % jump of the two-piece phi at 10 makes UB(Es/N0) locally non-monotone)
    place    the t diagonal symbols out of n = E / 2 (sorted): rd = default_rng([REP_SEED + 1, tag, t]).choice(n, t);
             us / ea / ex = stratified Beta(a, a) quantiles floor(n I^-1_{a,a}((k + u_k) / t)), u_k ~ U(0, 1) from
             default_rng([REP_SEED + 2, tag, t, round(100 a)]), a = 1 (uniform), 0.5 (arcsine: ends-weighted), 0.3
             (stronger ends); collisions moved to the nearest free symbol. Irregular (jittered): no grating lobes
    tx map   repeated unit k (e1 index rep[k], copy E - t + k) -> (I, Q) of symbol pos[perm[k]] (perm =
             default_rng(PAIR_SEED).permutation(t)); the other bits in the base order rng(CHAN_SEED).permutation(E)
             (twin_design._fill); scrambler pn = the symbol sign q (both bits), axis hop on the diagonal symbols (I bit
             only): s^2 = j (1 - 2 q), w2 = conj(s0^2) (s0 = the symbols of x = 0), w2 s^2 = 1 (twin_design rd)

    py sync_cfo/fs/rep_twin.py --table          # offline GA / UB cost table -> results/rep_twin_cost.json (seconds)"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.special import betaincinv

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import twin_design as td  # noqa: E402  (puts the project root on the path)
import polar_design as pd  # noqa: E402
import polar_rm as rm  # noqa: E402
import run_polar_genie as rpg  # noqa: E402
from polar import PolarCode  # noqa: E402

FMTS = ("id13", "id3")
# (2026-11-24) formats the full blind receiver may build a repetition twin on (blind_fmt rep; QPSK, the (E - t) plan keeps
# N and the mode: puncture, or shorten with its own J[E - t:] shortened set): FMTS + id14s / id5 (shorten), id2 (t <= 47:
# E - t <= 288 drops N to 256, repetition); FMTS (the --table default) unchanged
RX_FMTS = FMTS + ("id14s", "id5", "id2")
TS = (32, 48, 64, 96, 128)                                 # repeated bits = diagonal symbols
RULES = ("gr", "pnc", "rnd", "wst")
PLACES = ("rd", "us", "ea", "ex")
PLACE_A = {"us": 1.0, "ea": 0.5, "ex": 0.3}                # Beta(a, a) density of the stratified placements
REP_SEED = 4520                                            # rnd rule / rd, us, ea, ex positions (+1, +2)
GR_BLOCK = 4                                               # gr: bits added per gradient round
GR_H = 0.3                                                 # gr: relative secant step of the f nodes (1e-4 / 1e-2: the
                                                           # piece-split jump of phi at 10 spoils it; 0.3: corr 0.98-0.998)
K_ORDERS = {"greedy": None, "search": (6, 9, 12, 18, 24, 30, 36)}   # k<m> comparison: greedy every 2nd (id3) / 3rd m, search these m
CRC = td.CRC
_D = {}


def _plan(fmt, t, crc=CRC):
    """The rate-matched (E - t, K) plan with the format's adopted design keywords (twin_design.plan_kw: GA at GA_REF)."""
    f = rpg.FMTS[fmt]
    p = rm.rm_plan(f["A"] + crc, f["E"] - t, **td.plan_kw(fmt))
    assert p["mode"] == f["mode"], (fmt, t, p["mode"])
    return p


def mu_of(fmt, esn0):
    return pd.design_mu(esn0, td.bps(fmt))


def chan_means(p, E1, rep_x, mu):
    """m_x (N,): the (E1) rate-matched channel + mu at the repeated mother positions rep_x (MRC)."""
    m = pd.rm_channel_means(p["N"], E1, p["mode"], p["J"], mu)
    m[np.asarray(rep_x, int)] += mu
    return m


def info_of(p, m_x, K):
    """(info (K,) sorted, m_u): the K most reliable u outside pre under m_x (ties: PW, polar_design.ga_order)."""
    m_u = pd.ga_bit_means(m_x)
    o = pd.ga_order(m_u)
    rest = o[~p["pre"][o]]
    return np.sort(rest[-K:]), m_u


def ub_grad(m_x, info):
    """(UB, dUB / dm_x (N,)): forward GA (polar_design.ga_bit_means) keeping the stage inputs, backward chain rule (g
    node d/da = d/db = 1; f node one-sided secants, step GR_H a + 1e-9); dQ(sqrt(m / 2)) / dm = -phi(x) / (4 x)."""
    m = np.asarray(m_x, np.float64).copy()
    N = m.size
    s, st = N // 2, []
    while s >= 1:
        v = m.reshape(N // (2 * s), 2, s)
        a, b = v[:, 0, :].copy(), v[:, 1, :].copy()
        st.append((s, a, b))
        v[:, 0, :], v[:, 1, :] = pd.ga_f(a, b), a + b
        s //= 2
    x = np.sqrt(np.maximum(m[info], 0) / 2)
    ub = float(pd.q_func(x).sum())
    g = np.zeros(N)
    g[info] = -np.exp(-x ** 2 / 2) / np.sqrt(2 * np.pi) / (4 * np.maximum(x, 1e-12))
    for s, a, b in reversed(st):
        gv = g.reshape(N // (2 * s), 2, s)
        gl, gh = gv[:, 0, :].copy(), gv[:, 1, :].copy()
        f0 = pd.ga_f(a, b)
        ha, hb = GR_H * a + 1e-9, GR_H * b + 1e-9
        gv[:, 0, :] = gl * (pd.ga_f(a + ha, b) - f0) / ha + gh
        gv[:, 1, :] = gl * (pd.ga_f(a, b + hb) - f0) / hb + gh
    return ub, g


def design(fmt, t, rule, crc=CRC):
    """The repetition design (cached): plan p of (E - t), pos0, rep (t,) e1 indices, rep_x mother positions, info (aware),
    info_plain (rm_plan's), K, E, E1."""
    key = (fmt, t, rule, crc)
    if key in _D:
        return _D[key]
    f = rpg.FMTS[fmt]
    E, K, tag = f["E"], f["A"] + crc, f["tag"]
    E1 = E - t
    p = _plan(fmt, t, crc)
    pos0 = td._pos0(p)
    assert pos0.size == E1
    mu = mu_of(fmt, td.GA_REF[fmt])
    if rule == "rnd":
        rep = np.random.default_rng([REP_SEED, tag, t]).choice(E1, t, replace=False)
    elif rule == "pnc":
        assert p["mode"] == "puncture", (fmt, p["mode"])
        rep = np.arange(t)
    elif rule == "wst":
        _, g = ub_grad(chan_means(p, E1, [], mu), p["info_pos"])
        rep = np.argsort(-g[pos0] * mu, kind="stable")[:t]
    elif rule == "gr":
        chosen = []
        while len(chosen) < t:
            mx = chan_means(p, E1, pos0[chosen], mu)
            info, _ = info_of(p, mx, K)
            _, g = ub_grad(mx, info)
            gain = -g[pos0] * mu
            gain[chosen] = -np.inf
            chosen += [int(i) for i in np.argsort(-gain, kind="stable")[:min(GR_BLOCK, t - len(chosen))]]
        rep = np.array(chosen, int)
    else:
        raise ValueError(rule)
    rep = np.asarray(rep, int)
    assert np.unique(rep).size == t
    rep_x = pos0[rep]
    info, _ = info_of(p, chan_means(p, E1, rep_x, mu), K)
    _D[key] = dict(fmt=fmt, t=t, rule=rule, plan=p, pos0=pos0, rep=rep, rep_x=rep_x, info=info,
                   info_plain=p["info_pos"], K=K, E=E, E1=E1)
    return _D[key]


def ub_at(fmt, esn0, p, E1, rep_x, info):
    return pd.union_bound(pd.ga_bit_means(chan_means(p, E1, rep_x, mu_of(fmt, esn0))), info)


def loss_db(fmt, p, E1, rep_x, info, s0=None, lo=-0.5, hi=1.5, it=12):
    """d (dB) with UB(s0 + d) = UB_base(s0) (bisection; UB decreasing in Es/N0), s0 = GA_REF."""
    s0 = td.GA_REF[fmt] if s0 is None else s0
    b = td.base_plan(fmt)
    tgt = ub_at(fmt, s0, b, rpg.FMTS[fmt]["E"], [], b["info_pos"])
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        if ub_at(fmt, s0 + mid, p, E1, rep_x, info) > tgt:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def rep_row(fmt, t, rule, aware=True):
    D = design(fmt, t, rule)
    info = D["info"] if aware else D["info_plain"]
    s0 = td.GA_REF[fmt]
    b = td.base_plan(fmt)
    E = D["E"]
    return dict(fmt=fmt, kind="rep", t=t, rule=rule, aware=aware, twins=t, E1=D["E1"], N=D["plan"]["N"],
                ub=ub_at(fmt, s0, D["plan"], D["E1"], D["rep_x"], info),
                ub_norep=ub_at(fmt, s0, D["plan"], D["E1"], [], info),
                ub_base=ub_at(fmt, s0, b, E, [], b["info_pos"]),
                loss_db=loss_db(fmt, D["plan"], D["E1"], D["rep_x"], info),
                info_moved=int(np.setdiff1d(info, D["info_plain"]).size),
                rep_x_wt_mean=float(td.popcount(D["rep_x"]).mean()),
                rep_x_lowhalf=int(np.sum(D["rep_x"] < D["plan"]["N"] // 2)))


def k_row(fmt, m, order):
    info, meta = td.design_info(fmt, f"k{m}", order)
    if info is None:
        return None
    b = td.base_plan(fmt)
    E, s0 = rpg.FMTS[fmt]["E"], td.GA_REF[fmt]
    return dict(fmt=fmt, kind="move", m=m, order=order, twins=int(td.clean_twins(b, info).sum()),
                ub=ub_at(fmt, s0, b, E, [], info), ub_base=ub_at(fmt, s0, b, E, [], b["info_pos"]),
                loss_db=loss_db(fmt, b, E, [], info))


def k_rows(fmt, mmax=48):
    out = []
    src, dst = td.move_lists(td.base_plan(fmt), "greedy")
    for m in range(0, min(mmax, len(src), len(dst)) + 1, 2 if fmt == "id3" else 3):
        r = k_row(fmt, m, "greedy")
        if r:
            out.append(r)
    for m in K_ORDERS["search"]:
        r = k_row(fmt, m, "search")
        if r:
            out.append(r)
    return out


class RepCode:
    """The repetition-twin code of a format (module docstring): RMPolarCode(A, E - t) with the design's info set + t
    repeated bits; encode_rm -> the extended E bits, decode = MRC + the (E - t) decoder; A, K, N, E, code, rep."""

    def __init__(self, fmt, t, rule="gr", crc=CRC, L=8, aware=True, code_cls=PolarCode):
        D = design(fmt, t, rule, crc)
        f = rpg.FMTS[fmt]
        self.fmt, self.t, self.rule, self.aware = fmt, t, rule, aware
        self.E, self.E1, self.rep = D["E"], D["E1"], D["rep"]
        r = rm.RMPolarCode(f["A"], self.E1, crc_len=crc, list_size=L, code_cls=code_cls, **td.plan_kw(fmt))
        assert r.mode == f["mode"], (fmt, t, r.mode)
        info = D["info"] if aware else D["info_plain"]
        if not np.array_equal(info, r.plan["info_pos"]):
            fz = np.ones(r.N, bool)
            fz[info] = False
            assert not (r.plan["pre"] & ~fz).any(), "an info bit on a pre-frozen position"
            r.plan = dict(r.plan, info_pos=info, frozen=fz, rel=fz & ~r.plan["pre"])
            r.code = code_cls(r.N, f["A"], crc, L, info_pos=info, crc_G=rm.crc_matrix(f["A"], crc))
            assert np.array_equal(r.code.frozen, fz)
        self.rmc, self.code = r, r.code
        self.A, self.C, self.K, self.N, self.mode = r.A, r.C, r.K, r.N, r.mode

    def encode_rm(self, data):
        """data (B, A) -> extended e (B, E) = [e1, e1[:, rep]]."""
        e1 = self.rmc.encode_rm(data)
        return np.concatenate([e1, e1[:, self.rep]], 1)

    def mrc(self, llr_e):
        """llr_e (B, E) extended order -> (B, E - t): the copies added onto their originals."""
        l1 = np.array(llr_e[:, :self.E1], dtype=np.float64)
        l1[:, self.rep] += llr_e[:, self.E1:]
        return l1

    def decode(self, llr_e, return_info=False):
        return self.rmc.decode(self.mrc(llr_e), return_info=return_info)

    def macs(self, n_sym, L=None, sf=1, cores=32):
        """decode_macs of the (E - t) code (n_sym the E / 2 symbols) + t MRC adds (llr; crit / 32)."""
        c = rm.decode_macs(self.N, self.K, self.E1, n_sym, L or self.code.list_size, sf, cores)
        return dict(c, total=c["total"] + self.t, crit=c["crit"] + self.t / cores)


def _dedup(pos, n):
    """Integer positions with collisions moved to the nearest free symbol (in order; ties: the lower one)."""
    used, out = np.zeros(n, bool), []
    for x in pos:
        x = int(x)
        for d in range(n):
            c = [y for y in (x - d, x + d) if 0 <= y < n and not used[y]]
            if c:
                used[c[0]] = True
                out.append(c[0])
                break
    return np.array(out, int)


def place(fmt, t, kind):
    """The t diagonal symbols (sorted) of a placement (module docstring)."""
    n, tag = rpg.FMTS[fmt]["E"] // 2, rpg.FMTS[fmt]["tag"]
    if kind == "rd":
        pos = np.random.default_rng([REP_SEED + 1, tag, t]).choice(n, t, replace=False)
    else:
        a = PLACE_A[kind]
        u = (np.arange(t) + np.random.default_rng([REP_SEED + 2, tag, t, int(round(100 * a))]).uniform(size=t)) / t
        pos = _dedup(np.clip(np.floor(n * betaincinv(a, a, u)), 0, n - 1), n)
    pos = np.sort(np.asarray(pos, int))
    assert pos.size == t and np.unique(pos).size == t
    return pos


def tx_map(fmt, t, kind, rep):
    """chan (E,) (tx bit m = e[chan[m]], e extended), pn (E,) uint8, s0 (t,) diagonal symbols (sorted), w2 (t,), geo."""
    f = rpg.FMTS[fmt]
    E, n, tag = f["E"], f["E"] // 2, f["tag"]
    assert td.bps(fmt) == 2, fmt
    E1 = E - t
    pos = place(fmt, t, kind)
    perm = np.random.default_rng(td.PAIR_SEED).permutation(t)
    I, Q = np.full(n, -1, int), np.full(n, -1, int)
    for k in range(t):
        s_ = pos[perm[k]]
        I[s_], Q[s_] = int(rep[k]), E1 + k
    chan = td._fill(fmt, np.random.default_rng(td.CHAN_SEED).permutation(E), I, Q)
    q = np.random.default_rng([td.PN_SEED, tag]).integers(0, 2, n)
    pn = np.repeat(q, 2)
    pn[2 * pos + 1] = 0                                    # axis hop on the diagonal symbols (I bit only)
    pn = pn.astype(np.uint8)
    s0 = rpg.modulate(pn[None], fmt)[0]
    return dict(chan=chan, pn=pn, s0=pos, w2=np.conj(s0[pos] ** 2), geo=dict(kind=kind, t=t, a=PLACE_A.get(kind)))


def table(fmts=FMTS, ts=TS, rules=RULES):
    doc = dict(ga_ref={f: td.GA_REF[f] for f in fmts}, ts=list(ts), rules=list(rules), rows=[], k=[])
    for fmt in fmts:
        kr = k_rows(fmt)
        doc["k"] += kr
        for r in kr:
            print(f"{fmt:5s} k{r['m']:<3d} {r['order']:6s} twins {r['twins']:4d} UB {r['ub']:.3e} (base "
                  f"{r['ub_base']:.3e}) loss {r['loss_db']:+.3f} dB", flush=True)
        for t in ts:
            for rule in rules:
                for aw in ((True, False) if rule == "gr" else (True,)):
                    r = rep_row(fmt, t, rule, aw)
                    doc["rows"].append(r)
                    kk = [x for x in kr if x["twins"] >= t]
                    best = min(kk, key=lambda x: x["loss_db"]) if kk else None
                    print(f"{fmt:5s} t {t:3d} {rule:3s}{'' if aw else 'p'} E1 {r['E1']} UB {r['ub']:.3e} (no rep "
                          f"{r['ub_norep']:.3e}, base {r['ub_base']:.3e}) loss {r['loss_db']:+.3f} dB | info moved "
                          f"{r['info_moved']} | rep wt {r['rep_x_wt_mean']:.1f} low-half {r['rep_x_lowhalf']} | k with "
                          f">= {t} twins: " + (f"k{best['m']} {best['order']} ({best['twins']}) {best['loss_db']:+.3f} dB"
                                               if best else "none"), flush=True)
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--fmts", nargs="+", default=list(FMTS))
    ap.add_argument("--ts", nargs="+", type=int, default=list(TS))
    ap.add_argument("--rules", nargs="+", default=list(RULES), choices=list(RULES))
    ap.add_argument("--out", default="rep_twin_cost.json")
    a = ap.parse_args()
    if a.table:
        doc = table(a.fmts, a.ts, a.rules)
        os.makedirs(td.RES, exist_ok=True)
        with open(os.path.join(td.RES, a.out), "w") as fh:
            json.dump(doc, fh, indent=1)


if __name__ == "__main__":
    main()
