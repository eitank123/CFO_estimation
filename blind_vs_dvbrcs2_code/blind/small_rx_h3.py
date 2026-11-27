"""H3 (2026-11-25, CHATGPT-0015; sync_cfo/expected_fs.md "H3 (ID 13, ID 2)"): code-aided partial-path-metric (PM)
evidence on the H1 candidates of small_rx (h1 dict key "h3"; None = off = H1 unchanged, bit-identical).

Inside small_rx's 1b (h1) block, on the packets the fast path did not accept, the H1 hypotheses HY1 (cells f_k + m STEP
of the combined Y2 + Y4 + LS top-K peaks, + f0's cell with its other phases) are re-ordered (never re-scored, never
dropped unless nmax / jgap say so) by
    J = alpha S_norm - beta PM_norm,   S_norm = S - max S,   PM_norm = PM_c - min PM_c   (over the ranked set),
S = the combined score at the cell's bin (nats), PM_c = sum_{i <= leaf(c)} ln(1 + exp(-(1 - 2 u_i) lambda_i)) = the
list-1 Fast-SSC metric of small_rx (fsn.metric_nodes, cumulated up to the checkpoint c; ck useful: c of the not
pre-frozen positions, as the search), at the hypothesis' own (f, theta): theta = H1's combined Y4 + twin phase of the
cell (_ph1 on the pre-MF of the raw SPS at the cell's peak, lazily, cached in H1's own PH1 / RP1: never paid twice).
rank "J" / "pm" (PM only) / "spec" (H1's own combined-score order; PMs still computed and charged). CRC + rho stay the
only acceptance (decode() unchanged); E-style fallback, f0's alternate phases, PiCode, exact-repeat reuse unchanged.

Arms (keys of H3_DEF):
  H3a  c (one checkpoint): PM of EVERY remaining hypothesis, J order (matched decode budget: the same hypotheses);
  H3b  + expand: the 3-point stencil P(f_k - h), P(f_k), P(f_k + h) (h = STEP, phase re-estimated at each CFO); an edge
       minimum with PM decreasing -> one more point f_k +- s h (s = 2 .. xmax + 1) while PM keeps decreasing, each a
       new hypothesis (never widened for a large PM);
  H3c  + vertex: f_v = f_k + (h/2)(P- - P+)/(P- - 2 P0 + P+) only if the curvature > 0 and |f_v - f_k| <= h, checked by
       ONE real evaluation: a new hypothesis only if PM(f_v) < min(P-, P0, P+);
  H3d  prog: PMs at the peaks' representative hypotheses at cks[0], the best keep[l] extended to cks[l + 1] (prefix
       reused: only the extra share charged); peaks in (deepest level, J) order, each peak's hypotheses together;
       stencil: the 3-point PMs (all of the peak's hypotheses) at cks[-1] for the deepest peaks.
  lazy True: the PMs only after H1's first decode round of the packet failed (easy packets pay none); False: before it.
Cost (standard scheduled crit path, small_rx crit_par / c_d4a): each PM stage of a packet is ONE parallel launch on
KP = 32 cores (per hypothesis: the de-rotation derot when new + m_met x the extra Fast-SSC tree share; LPT busiest
core into crit, the work into macs / pmac); phases (_ph1, charged as H1's), pre-MF (PREMF_FAIR, serial -> / KP).
Measurement (finish, NOT charged, no decision): the PM landscape at the K combined peaks f_k and f_k +- STEP at every
H3_LCK checkpoint with the phase used (h3_src: 0 the arm's charged PM, 1 the arm's phase / PM measured here, 2 both
measured here: _ph1 charge False = the twin branch), the truth's rank under J / PM only / spectrum, per-packet ops.

python small_rx_h3.py --fit <dump dir> [...] --out <json>: alpha = 1, beta per checkpoint fitted on CALIBRATION dumps
only (the h3_* landscape of a "rank": "spec" run): the beta minimising the truth's mean rank among the 3K points.
"""
import numpy as np

import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp

H3_DEF = dict(c=0.25, rank="J", alpha=1.0, beta=1.0, lazy=False, prog=False, cks=(0.0625, 0.125, 0.25), keep=(4, 2),
              stencil=False, expand=False, xmax=2, vertex=False, vtol=0.1, nmax=None, jgap=None, log=True)
# (h3) c: H3a's checkpoint (fraction; ck useful: of the not pre-frozen positions); rank J / pm / spec; alpha, beta: J
# (beta a float, or with prog one per cks); lazy: PMs after the first failed H1 round; prog (H3d): cks the progressive
# checkpoints, keep[l] peaks extended from cks[l] to cks[l + 1] (last value repeats); stencil: the 3-point PMs (prog:
# at the deepest peaks; non-prog: every peak, exact f_k +- STEP points charged when not cells); expand (H3b, implies
# stencil): xmax extra steps in the decreasing direction; vertex (H3c, implies stencil): the guarded parabola (vtol STEP:
# a vertex closer to f_k is not evaluated); nmax / jgap (None = off: matched budget, never pruned): keep the first nmax
# remaining / drop J < max J - jgap (non-prog), the dropped true hypotheses logged (h3_lost); log: the landscape logs
H3_LCK = (0.0625, 0.125, 0.25, 0.5, 1.0)       # (h3, measurement) checkpoints of the logged landscape
H3_KEYS = ("h3_on", "h3_npm", "h3_next", "h3_nst", "h3_ops", "h3_crit", "h3_ckf", "h3_nx", "h3_vtry", "h3_vok",
           "h3_ndrop", "h3_lost", "h3_nhyp", "h3_rkJ", "h3_rkP", "h3_rkS", "h3_pm", "h3_th", "h3_s", "h3_src", "h3_dt",
           "h3_e")


def log_init(B, H1):
    """(h3) the per-packet h3_* fields (in small_rx's h1l, dumped through H1_KEYS); K = H1's K."""
    K, nl = int(H1["K"]), len(H3_LCK)
    return dict(h3_on=np.zeros(B, bool), h3_npm=np.zeros(B, np.int16), h3_next=np.zeros(B, np.int16),
                h3_nst=np.zeros(B, np.int8), h3_ops=np.zeros(B, np.float32), h3_crit=np.zeros(B, np.float32),
                h3_ckf=np.full(B, np.nan, np.float32), h3_nx=np.zeros(B, np.int8), h3_vtry=np.zeros(B, np.int8),
                h3_vok=np.zeros(B, np.int8), h3_ndrop=np.zeros(B, np.int16), h3_lost=np.zeros(B, bool),
                h3_nhyp=np.zeros(B, np.int16), **{k_: np.full(B, -2, np.int16) for k_ in ("h3_rkJ", "h3_rkP", "h3_rkS")},
                h3_pm=np.full((B, K, 3, nl), np.nan, np.float32), h3_th=np.full((B, K, 3), np.nan, np.float32),
                h3_s=np.full((B, K, 3), np.nan, np.float32), h3_src=np.full((B, K, 3), -1, np.int8),
                h3_dt=np.full((B, K), np.nan, np.float32), h3_e=np.full((B, K, 3), np.nan, np.float16))


class H3:
    """(h3) one small_rx h1 block's PM ranking: E = the block's state (dict, see h3_hook.patch); step(ptr1) at the top of
    every H1 decode round, finish(h1l) after the last."""

    def __init__(self, cfg, E):
        self.c = {**H3_DEF, **(cfg or {})}
        assert set(self.c) == set(H3_DEF), f"h3 keys: {tuple(H3_DEF)}"
        c = self.c
        assert c["rank"] in ("J", "pm", "spec") and E["Du1"] is None, "h3: rank J / pm / spec; not with ls_L + ls_rs"
        assert not (c["prog"] and c["jgap"] is not None), "h3: jgap only without prog"
        self.E = E
        self.cks = tuple(float(x) for x in c["cks"]) if c["prog"] else (float(c["c"]),)
        self.beta = (tuple(float(x) for x in c["beta"]) if isinstance(c["beta"], (list, tuple))
                     else (float(c["beta"]),) * len(self.cks))
        assert len(self.beta) == len(self.cks), "h3: one beta per checkpoint"
        self.keep = tuple(int(x) for x in c["keep"])
        self.sten = bool(c["stencil"] or c["expand"] or c["vertex"])
        self.LCK = tuple(sorted(set(H3_LCK) | set(self.cks)))
        lv, N = E["lv"], bc.N_BITS
        self.nl, self.sh = {}, {}
        for ck in self.LCK:                                   # leaf index / tree share per checkpoint (as the search)
            n_ = E["nlf"](ck) if E["nlf"] is not None else max(1, int((lv <= ck * N).sum()))
            fr_ = lv[n_ - 1] / N
            self.nl[ck] = n_
            self.sh[ck] = float(E["cost_share"](E["fsn"].plan, fr_)) if E["tree"] else float(fr_)
        self.jl = np.array([self.nl[ck] for ck in self.LCK]) - 1
        self.q = {int(i_): q_ for q_, i_ in enumerate(E["R1"])}
        self.pmv, self.paid, self.chg = {}, {}, set()         # (i, f, th) -> PMs at LCK / paid share; charged keys
        self.rpm = {}                                         # (measurement) uncharged pre-MF symbols
        self.done = set()
        B = E["B"]
        self.a = dict(npm=np.zeros(B, int), next=np.zeros(B, int), nst=np.zeros(B, int), ops=np.zeros(B),
                      crit=np.zeros(B), ckf=np.full(B, np.nan), nx=np.zeros(B, int), vtry=np.zeros(B, int),
                      vok=np.zeros(B, int), ndrop=np.zeros(B, int), lost=np.zeros(B, bool), nhyp=np.zeros(B, int),
                      rkJ=np.full(B, -2), rkP=np.full(B, -2), rkS=np.full(B, -2))

    # ------------------------------------------------------------------ state shared with the H1 loop (PH1 / RP1)
    def _rr(self, i, pf, charge=True):
        """pre-MF symbols at the peak pf (H1's RP1: f0's = r itself; else PREMF_FAIR charged once)."""
        E = self.E
        if (i, pf) in E["RP1"]:
            return E["RP1"][(i, pf)]
        if pf == float(E["f0g"][i]):
            x_ = E["r"][i]
        elif not charge and (i, pf) in self.rpm:
            return self.rpm[(i, pf)]
        else:
            x_ = bf.premf(E["r_mf"][i:i + 1], E["rx"][i:i + 1], np.array([pf]))[0]
            if charge:
                E["macs"][i] += vp.PREMF_FAIR_MACS
                E["cco"]["t_premf"][i] += vp.PREMF_FAIR_MACS
        if charge:
            E["RP1"][(i, pf)] = x_
        else:
            self.rpm[(i, pf)] = x_
        return x_

    def _c0(self, i):
        """the f0 cell's phase = the fast path's own theta0 (as the H1 loop sets it): before any new phase there."""
        E = self.E
        for h_ in E["HY1"][i]:
            if h_[1] and (i, h_[4]) not in E["PH1"]:
                E["PH1"][(i, h_[4])] = (float(E["h1f"][1][i]), -1, False, 0.0)

    def _phases(self, i, items):
        """H1's combined phase (charged _ph1) of the cells f (items (f, peak)) not in PH1, on the peak's pre-MF."""
        E = self.E
        nw_ = [x_ for x_ in dict.fromkeys(items) if (i, x_[0]) not in E["PH1"]]
        if not nw_:
            return
        rr_ = np.stack([self._rr(i, pf_) for _, pf_ in nw_])
        a_, b_, c_, d_ = E["ph1"](np.full(len(nw_), i), np.array([f_ for f_, _ in nw_]), rr_=rr_)
        for q_, (f_, _) in enumerate(nw_):
            E["PH1"][(i, f_)] = (a_[q_], int(b_[q_]), bool(c_[q_]), d_[q_])

    def _key(self, i, h_):                                    # hypothesis -> (PM key, peak)
        return (i, float(h_[0]), float(self.E["PH1"][(i, h_[4])][0] + h_[2])), float(h_[3])

    def _vals(self, keys, pfs, charge=True):
        """PM numerics (cumulated list-1 Fast-SSC metric at every LCK checkpoint) of new keys, one metric pass each."""
        nw_ = [(k_, pf_) for k_, pf_ in dict.fromkeys(zip(keys, pfs)) if k_ not in self.pmv]
        if nw_:
            E = self.E
            i_ = nw_[0][0][0]
            rr_ = np.stack([self._rr(i_, pf_, charge) for _, pf_ in nw_])
            L_ = bc.llrs(rr_, np.array([k_[1] for k_, _ in nw_]), np.array([k_[2] for k_, _ in nw_]), E["sigma2"])
            v_ = np.cumsum(E["fsn"].metric_nodes(L_), 1)[:, self.jl]
            for q_, (k_, _) in enumerate(nw_):
                self.pmv[k_] = v_[q_].astype(float)

    def _pay(self, i, keys, pfs, ck):
        """ONE parallel PM stage of packet i: each key decoded from its paid share up to ck's (prefix reused)."""
        E = self.E
        self._vals(keys, pfs)
        s_ = self.sh[ck]
        cs_, nw_ = [], []
        for k_ in dict.fromkeys(keys):
            pd_ = self.paid.get(k_, -1.0)
            if pd_ >= s_:
                continue
            cs_.append((E["derot"] if pd_ < 0 else 0.0) + E["m_met"] * (s_ - max(pd_, 0.0)))
            nw_.append(pd_ < 0)
            self.paid[k_] = s_
            self.chg.add(k_)
        if not cs_:
            return
        cs_, nw_ = np.array(cs_), np.array(nw_)
        E["macs"][i] += cs_.sum()
        E["pmac"][i] += cs_.sum()
        o_ = np.argsort(-cs_, kind="stable")[::E["KP"]]       # LPT over the KP cores: each pass its busiest core
        E["crit"][i] += cs_[o_].sum()
        E["cco"]["c_cmul"][i] += E["derot"] * nw_[o_].sum()   # (cco) the de-rotation share
        self.a["npm"][i] += int(nw_.sum())
        self.a["next"][i] += int((~nw_).sum())
        self.a["nst"][i] += 1
        E["st"]["h3_pm"] = E["st"].get("h3_pm", 0) + int(nw_.sum())
        E["st"]["h3_stages"] = E["st"].get("h3_stages", 0) + 1

    def _pm(self, k_, ck):
        return self.pmv[k_][self.LCK.index(ck)]

    def _S(self, i, f_):                                      # the combined score at f's bin (as H1's cell order)
        E = self.E
        return float(E["CB"][self.q[i], E["bix1"][int(np.round(E["pw"] * f_ * E["nf"])) % E["nf"]]])

    @staticmethod
    def _J(S_, P_, al, be, mode):
        S_, P_ = np.asarray(S_, float), np.asarray(P_, float)
        if mode == "pm":
            return -(P_ - P_.min())
        return al * (S_ - S_.max()) - be * (P_ - P_.min())

    # ------------------------------------------------------------------ the stencil / expansion / vertex of a peak
    def _point(self, i, pf, f_):
        """(f, theta) key of a stencil point of peak pf: theta = the cell's phase (PH1, re-estimated at f if new)."""
        self._phases(i, [(f_, pf)])
        return (i, float(f_), float(self.E["PH1"][(i, f_)][0]))

    def _stencil(self, i, peaks, ck, add):
        """3-point PMs of the peaks at ck (one stage), then expand / vertex (H3b / H3c); new hypotheses -> add."""
        c, ST, MX = self.c, bc.STEP, bc.MAX_CFO
        P3 = {}
        ks_, ps_ = [], []
        for pf in peaks:
            P3[pf] = [self._point(i, pf, float(np.clip(pf + m_ * ST, -MX, MX))) for m_ in (-1, 0, 1)]
            ks_ += P3[pf]
            ps_ += [pf] * 3
        self._pay(i, ks_, ps_, ck)
        have = {(round(k_[1], 12), round(k_[2], 12)) for k_ in self.hk}   # exact identity only (dedup rule)
        def new(pf, k_, kind):
            if (round(k_[1], 12), round(k_[2], 12)) not in have:
                have.add((round(k_[1], 12), round(k_[2], 12)))
                add.append(((k_[1], False, 0.0, pf, k_[1], kind), k_))
        if c["expand"]:
            run = {}
            for pf in peaks:
                Pm, P0, Pp = (self._pm(k_, ck) for k_ in P3[pf])
                d_ = 1 if (Pp < P0 and Pp <= Pm) else -1 if (Pm < P0 and Pm < Pp) else 0
                if d_:
                    new(pf, P3[pf][1 + d_], 4)                # the edge point itself (a cell already when M >= 1)
                    run[pf] = (d_, min(Pm, Pp))
            for s_ in range(2, int(c["xmax"]) + 2):           # one stage per step, every running peak at once
                if not run:
                    break
                pt_ = {pf: self._point(i, pf, float(np.clip(pf + d_ * s_ * ST, -MX, MX))) for pf, (d_, _) in run.items()}
                self._pay(i, list(pt_.values()), list(pt_), ck)
                nr_ = {}
                for pf, k_ in pt_.items():
                    if self._pm(k_, ck) < run[pf][1]:
                        new(pf, k_, 4)
                        self.a["nx"][i] += 1
                        nr_[pf] = (run[pf][0], self._pm(k_, ck))
                run = nr_
        if c["vertex"]:
            vt_ = {}
            for pf in peaks:
                Pm, P0, Pp = (self._pm(k_, ck) for k_ in P3[pf])
                ku_ = Pm - 2 * P0 + Pp
                if ku_ > 0:
                    dl_ = 0.5 * ST * (Pm - Pp) / ku_
                    if c["vtol"] * ST < abs(dl_) <= ST:
                        vt_[pf] = (self._point(i, pf, float(np.clip(pf + dl_, -MX, MX))), min(Pm, P0, Pp))
            if vt_:
                self._pay(i, [v_[0] for v_ in vt_.values()], list(vt_), ck)
                for pf, (k_, pb_) in vt_.items():
                    self.a["vtry"][i] += 1
                    if self._pm(k_, ck) < pb_:
                        self.a["vok"][i] += 1
                        new(pf, k_, 5)

    # ------------------------------------------------------------------ the ranking of one packet
    def _rank(self, i, ptr):
        E, c = self.E, self.c
        m0_, p0_, c0_ = E["macs"][i], E["pmac"][i], E["crit"][i]
        self._c0(i)
        rem = list(E["HY1"][i][ptr:])
        self._phases(i, [(h_[4], float(h_[3])) for h_ in rem if not h_[1]])
        KH = [self._key(i, h_) for h_ in rem]
        self.hk = [k_ for k_, _ in KH]
        add = []                                              # (hypothesis, key) added by expand / vertex
        al = float(c["alpha"])
        if not c["prog"]:
            ck = self.cks[0]
            self._pay(i, [k_ for k_, _ in KH], [p_ for _, p_ in KH], ck)
            if self.sten:
                self._stencil(i, list(dict.fromkeys(p_ for _, p_ in KH)), ck, add)
            H = [(h_, k_) for h_, (k_, _) in zip(rem, KH)] + add
            S_ = [self._S(i, h_[0]) for h_, _ in H]
            P_ = [self._pm(k_, ck) for _, k_ in H]
            ords = {}
            for md_ in ("J", "pm", "spec"):
                if md_ == "spec":
                    ords[md_] = list(range(len(H)))
                else:
                    J_ = self._J(S_, P_, al, self.beta[0], md_)
                    ords[md_] = sorted(range(len(H)), key=lambda x_: (-J_[x_], x_))
            Jm_ = self._J(S_, P_, al, self.beta[0], c["rank"]) if c["rank"] != "spec" else None
            self.a["ckf"][i] = ck
        else:
            pk_ = list(dict.fromkeys(p_ for _, p_ in KH))     # the peaks in H1's order
            rep = {}
            for x_, (h_, (k_, p_)) in enumerate(zip(rem, KH)):   # representative: the hypothesis nearest its peak
                if p_ not in rep or (abs(h_[0] - p_), h_[2] != 0.0) < (abs(rem[rep[p_]][0] - p_), rem[rep[p_]][2] != 0.0):
                    rep[p_] = x_
            lvl, Jl = {}, {}
            sel = list(pk_)
            for l_, ck in enumerate(self.cks):
                if l_:
                    n_ = self.keep[min(l_ - 1, len(self.keep) - 1)]
                    sel = sorted(sel, key=lambda p_: (-Jl[p_], pk_.index(p_)))[:n_]
                if not sel:
                    break
                self._pay(i, [KH[rep[p_]][0] for p_ in sel], sel, ck)
                S_ = [self._S(i, rem[rep[p_]][0]) for p_ in sel]
                P_ = [self._pm(KH[rep[p_]][0], ck) for p_ in sel]
                J_ = self._J(S_, P_, al, self.beta[l_], c["rank"] if c["rank"] != "spec" else "J")
                for p_, j_ in zip(sel, J_):
                    lvl[p_], Jl[p_] = l_, float(j_)
                self.a["ckf"][i] = ck
            ckL = self.cks[max(lvl.values())] if lvl else self.cks[0]
            deep = [p_ for p_ in pk_ if lvl.get(p_, -1) == max(lvl.values(), default=0)]
            if self.sten and deep:                            # the deepest peaks' 3 points and own hypotheses at ckL
                self._pay(i, [KH[x_][0] for x_ in range(len(rem)) if KH[x_][1] in deep],
                          [KH[x_][1] for x_ in range(len(rem)) if KH[x_][1] in deep], ckL)
                self._stencil(i, deep, ckL, add)
            H = [(h_, k_) for h_, (k_, _) in zip(rem, KH)] + add
            ev_ = [x_ for x_, (h_, k_) in enumerate(H) if h_[3] in deep and self.paid.get(k_, -1) >= self.sh[ckL]] \
                if self.sten else []
            ords = {}
            for md_ in ("J", "pm", "spec"):
                if md_ == "spec":
                    ords[md_] = list(range(len(H)))
                    continue
                Jp_ = dict(Jl)                                # peak order: deepest level first, then J there
                if md_ != c["rank"] and lvl:                  # (measurement) the other mode on the same PMs
                    for l_ in set(lvl.values()):
                        ps_ = [p_ for p_ in lvl if lvl[p_] == l_]
                        J_ = self._J([self._S(i, rem[rep[p_]][0]) for p_ in ps_],
                                     [self._pm(KH[rep[p_]][0], self.cks[l_]) for p_ in ps_], al, self.beta[l_], md_)
                        Jp_.update({p_: float(j_) for p_, j_ in zip(ps_, J_)})
                po_ = sorted(pk_, key=lambda p_: (-lvl.get(p_, -1), -Jp_.get(p_, 0.0), pk_.index(p_)))
                Jh_ = {}
                if ev_:                                       # the deepest peaks' hypotheses by J at ckL
                    J_ = self._J([self._S(i, H[x_][0][0]) for x_ in ev_], [self._pm(H[x_][1], ckL) for x_ in ev_],
                                 al, self.beta[self.cks.index(ckL)], md_)
                    Jh_ = {x_: float(j_) for x_, j_ in zip(ev_, J_)}
                o_ = []
                for p_ in po_:
                    xs_ = [x_ for x_, (h_, _) in enumerate(H) if h_[3] == p_]
                    xs_.sort(key=lambda x_: (0, -Jh_[x_], x_) if x_ in Jh_ else
                             (1, 0 if x_ == rep.get(p_) else 1, x_))
                    o_ += xs_
                ords[md_] = o_
            Jm_ = None
        o_ = ords["J" if c["rank"] == "J" else c["rank"]]
        if Jm_ is not None and c["jgap"] is not None:         # (pruning, default off) J below the best - jgap
            o_ = [x_ for x_ in o_ if Jm_[x_] >= Jm_.max() - float(c["jgap"])]
        if c["nmax"] is not None:
            o_ = o_[:int(c["nmax"])]
        tf_ = E["truth_f"]
        if tf_ is not None:                                   # (measurement) the true hypothesis (within 0.5 STEP):
            on_ = [abs(h_[0] - float(tf_[i])) <= 0.5 * bc.STEP for h_, _ in H]   # its rank in each order, lost by
            for md_, kk_ in (("J", "rkJ"), ("pm", "rkP"), ("spec", "rkS")):     # pruning
                r_ = [n_ for n_, x_ in enumerate(ords[md_]) if on_[x_]]
                self.a[kk_][i] = r_[0] if r_ else -1
            self.a["lost"][i] = any(on_) and not any(on_[x_] for x_ in o_)
        self.a["ndrop"][i] = len(H) - len(o_)
        E["HY1"][i] = list(E["HY1"][i][:ptr]) + [H[x_][0] for x_ in o_]
        self.a["nhyp"][i] = len(E["HY1"][i])
        dm_ = E["macs"][i] - m0_
        self.a["ops"][i] += dm_
        self.a["crit"][i] += (E["crit"][i] - c0_) + (dm_ - (E["pmac"][i] - p0_)) / E["KP"]
        E["st"]["h3_rank"] = E["st"].get("h3_rank", 0) + 1

    def step(self, ptr1):
        """(hook, top of every H1 round) rank each packet still decoding: at once (lazy False) or after its first round."""
        E = self.E
        for i_ in E["R1"]:
            i_ = int(i_)
            if i_ in self.done or E["passed"][i_] or ptr1[i_] >= len(E["HY1"][i_]):
                continue
            if self.c["lazy"] and ptr1[i_] == 0:
                continue
            self.done.add(i_)
            self._rank(i_, ptr1[i_])

    # ------------------------------------------------------------------ (measurement) logs
    def finish(self, h1l):
        """(hook, after the H1 loop; measurement only: no charge, no decision) the h3_* fields."""
        E, a = self.E, self.a
        for k_ in ("npm", "next", "nst", "ops", "crit", "ckf", "nx", "vtry", "vok", "ndrop", "lost", "nhyp", "rkJ",
                   "rkP", "rkS"):
            h1l["h3_" + k_][:] = a[k_].astype(h1l["h3_" + k_].dtype)
        for i_ in self.done:
            h1l["h3_on"][i_] = True
        if not self.c["log"]:
            return
        ST, MX, PK = bc.STEP, bc.MAX_CFO, E["PK1"]["cb"][0]
        K = h1l["h3_pm"].shape[1]
        jx_ = [self.LCK.index(c_) for c_ in H3_LCK]
        tf_, tt_ = E["truth_f"], E["truth_th"]
        for q_, i_ in enumerate(E["R1"]):
            i_ = int(i_)
            pts = []
            for k in range(min(K, PK.shape[1])):
                pf = float(PK[q_, k])
                if tf_ is not None:
                    h1l["h3_dt"][i_, k] = (pf - float(tf_[i_])) / ST
                for j_, m_ in enumerate((-1, 0, 1)):
                    f_ = float(np.clip(pf + m_ * ST, -MX, MX))
                    if (i_, f_) in E["PH1"]:
                        th_, s0_ = float(E["PH1"][(i_, f_)][0]), 1
                    else:
                        rr_ = self._rr(i_, pf, charge=False)
                        th_ = float(E["ph1"](np.array([i_]), np.array([f_]), charge=False, rr_=rr_[None])[0][0])
                        if not np.isfinite(th_):                  # (no twin: the Y4 phase, branch 0)
                            th_ = float(bc.phase4(rr_[None], np.array([f_]))[0])
                        s0_ = 2
                    k3_ = (i_, f_, th_)
                    pts.append((k, j_, k3_, pf, s0_))
            ks_ = [x_[2] for x_ in pts]
            if not ks_:
                continue
            self._vals(ks_, [x_[3] for x_ in pts], charge=False)
            for k, j_, k3_, pf, s0_ in pts:
                h1l["h3_pm"][i_, k, j_] = self.pmv[k3_][jx_]
                h1l["h3_th"][i_, k, j_] = k3_[2]
                h1l["h3_s"][i_, k, j_] = self._S(i_, k3_[1])
                h1l["h3_src"][i_, k, j_] = 0 if k3_ in self.chg else s0_
                if tt_ is not None:
                    h1l["h3_e"][i_, k, j_] = (k3_[2] - float(tt_[i_]) + np.pi / 2) % np.pi - np.pi / 2


# ---------------------------------------------------------------------- offline fit of beta (calibration dumps only)
def fit(dirs, out=None, grid=None, par=2):
    """alpha = 1, beta per H3_LCK checkpoint: the beta minimising the true point's mean rank among the 3K landscape
    points (truth = the point within 0.5 STEP; packets without one are coverage misses, reported apart), on every H1
    packet ("all", for lazy False) and on those whose first H1 round failed ("fail1", h1_acc >= par or none: lazy)."""
    import glob
    import json
    import os
    grid = np.concatenate([[0.0], np.logspace(-3, 1, 41)]) if grid is None else np.asarray(grid, float)
    F = {k_: [] for k_ in ("h3_pm", "h3_s", "h3_dt", "h1_on", "h1_acc")}
    for d_ in dirs:
        for f_ in sorted(glob.glob(os.path.join(d_, "pk_*.npz"))):
            z_ = np.load(f_)
            if "h3_pm" not in z_:
                continue
            for k_ in F:
                F[k_].append(z_[k_])
    F = {k_: np.concatenate(v_) for k_, v_ in F.items()}
    on_ = F["h1_on"] & np.isfinite(F["h3_pm"][:, 0, 1, 0])
    PM, S, dt = F["h3_pm"][on_], F["h3_s"][on_], F["h3_dt"][on_]
    n, K = dt.shape
    D = dt[:, :, None] + np.array([-1.0, 0.0, 1.0])[None, None]
    tr = np.abs(D) <= 0.5
    tr &= np.isfinite(S)
    has = tr.reshape(n, -1).any(1)
    f1 = ~((F["h1_acc"][on_] >= 0) & (F["h1_acc"][on_] < par))
    res = dict(n=int(n), covered=float(has.mean()), n_fail1=int(f1.sum()), lck=list(H3_LCK), grid=grid.tolist(), fits={})
    for jc_, ck in enumerate(H3_LCK):
        P = PM[..., jc_].reshape(n, -1).astype(float)
        Sx = S.reshape(n, -1).astype(float)
        ok_ = np.isfinite(P) & np.isfinite(Sx)
        P, Sx = np.where(ok_, P, np.inf), np.where(ok_, Sx, -np.inf)
        T = tr.reshape(n, -1)
        def ranks(be):
            J = (Sx - np.max(Sx, 1, keepdims=True)) - be * (P - np.min(P, 1, keepdims=True))
            J = np.where(ok_, J, -np.inf)
            jt = np.where(T, J, -np.inf).max(1)
            return (J > jt[:, None]).sum(1)
        R = {}
        for pop, m_ in (("all", has), ("fail1", has & f1)):
            mr = [float(ranks(b_)[m_].mean()) if m_.any() else np.nan for b_ in grid]
            t1 = [float((ranks(b_)[m_] == 0).mean()) if m_.any() else np.nan for b_ in grid]
            bi = int(np.nanargmin(mr)) if np.isfinite(mr).any() else 0
            Jpm = (-(P - np.min(P, 1, keepdims=True)))
            Jpm = np.where(ok_, Jpm, -np.inf)
            rp = (Jpm > np.where(T, Jpm, -np.inf).max(1)[:, None]).sum(1)
            R[pop] = dict(beta=float(grid[bi]), mean_rank=mr[bi], top1=t1[bi], spec_mean_rank=mr[0], spec_top1=t1[0],
                          pm_mean_rank=float(rp[m_].mean()) if m_.any() else np.nan,
                          pm_top1=float((rp[m_] == 0).mean()) if m_.any() else np.nan, n=int(m_.sum()))
        res["fits"][str(ck)] = R
    if out:
        with open(out, "w") as fh_:
            json.dump(res, fh_, indent=1)
    return res


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="small_rx_h3: offline fit of the H3 J weights on CALIBRATION dumps")
    ap.add_argument("--fit", nargs="+", required=True, help="dump dirs (fullsys/results/blind_fs_<part>_dump)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--par", type=int, default=2, help="H1 hypotheses per round (fail1 = first round failed)")
    a_ = ap.parse_args()
    r_ = fit(a_.fit, a_.out, par=a_.par)
    for ck_, R_ in r_["fits"].items():
        print(ck_, {p_: {k_: (round(v_, 4) if isinstance(v_, float) else v_) for k_, v_ in x_.items()} for p_, x_ in R_.items()})
