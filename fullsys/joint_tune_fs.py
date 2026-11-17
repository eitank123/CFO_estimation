"""
Joint offline tuning of the BLIND receiver's search settings from the full-search log (run_blind_fs --fulllog, small_rx
fulllog): a setting combination is replayed on every logged packet (its grid search re-run from the logged list-1 PMs,
checkpoint-NN log P(cell) and spectral prior; every decode looked up in the logged decode attempts) -> per packet
passed / right / stage and the cost counters of small_rx (macs, pmac, dmac, seqm, crit, crit_g, crit_gh, dcritp, seqc,
d4a from the logged state at the search start) -> MACs per core in the profile's standard model (c_hd4a at 0.15,
c_d4a at 2/5, 1/2), exactly as the receiver counts them. Local analysis of the logs only: no receiver code imported.

Scope: the non-joint receivers small_rx fulllog accepts (vde32 = testing_s11g at the 0.15 profile with the format NN);
the DVB formats (joint list decodes) are not modelled.

Replay exactness. A decode of a hypothesis (cell, phase offset, kind) the log holds is exact (the search's own rows
src 0; the side rows src 1: the cells within `near` of the true cell, every phase some logged checkpoint's best-phase
choice gives). A decode of a hypothesis NOT in the log is counted as failed (CRC fail of main and retry, full cost) and
reported (n_unl, split near / far): conservative for a right packet (no rescue counted), optimistic only if a far cell
would have passed wrongly (an undetected error; the far-cell CRC passes of the search's own rows are reported as a check).
  exact (no unlogged decode possible beyond the above): ck_keep, ck_min, tau, kmin, win, ncand, z0, final, final_post,
      fine_last, T (<= the logged run's), ck (fractions among the logged ones), phase_keep (fraction among the logged),
      first_k, batch (K, z) / null, cores
  F5 fzstop (q, t): psn_min of every logged attempt; a stopped main whose retry was not logged (main CRC pass in the
      search's rows) -> retry counted failed; cost back as small_rx _fzs (fz_share at the logged node, d4a rounds)
  Kc: small_rx grid cores = cores or batch[0] or len(grid): batch null without cores schedules the grid on one core per
      cell (248 at vde32), not 32; --honest-kc (default on) replays every candidate with cores 32 (cost-neutral for a
      batch (32, z) receiver), the self-check uses the logged run's own value.

    py fullsys/joint_tune_fs.py --calib fs-flv32a fs-flv32b fs-flv32c --name v32j          # self-check + tuning
    py fullsys/joint_tune_fs.py --calib ... --check-only --name v32chk                     # self-check only
    py fullsys/joint_tune_fs.py --test fs-flv32t --setting '{"final": 8, "ck_keep": 0.01}' --name v32val

Selection: the cheapest (mean MACs per core over all calibration packets) setting whose errors exceed the replayed
baseline's by <= floor(--rel x baseline errors) at EVERY calibration point (part, Es/N0). Search: coordinate descent
over the knob grids (GRID, --grid JSON) from the baseline + --restarts random starts; every evaluated setting kept for
the Pareto front (total errors vs mean). Writes fullsys/results/joint_<name>.json.
"""

import argparse
import glob
import json
import math
import os
import random
import time
from multiprocessing import Process, Queue

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "fullsys", "results")
CK_FR = (1 / 16, 1 / 8, 3 / 16, 1 / 4, 5 / 16, 3 / 8, 1 / 2, 3 / 4, 1.0)   # small_rx.CK_FR
STD = {"1/10": "c_hd4a"}                            # profile (small_rx rate after PROFILE) -> std model; else c_d4a
COSTS = ("macs", "cpar", "c_d4a", "c_hd4a")
GRID = dict(ck_keep=[1e-3, 3e-3, 1e-2, 3e-2, 1e-1], ck_min=[8, 6, 4, 2], tau=[-0.5, -0.25, 0.0, 0.25, 0.5, 1.0],
            kmin=[16, 12, 8, 6, 4], win=[6.0, 5.5, 5.0, 4.5, 4.0], final=[32, 24, 16, 12, 8, 4, 0],
            final_post=[256, 128, 64, 32, 16, 0], fine_last=[4, 2, 0], ncand=[4, 3, 2, 1], z0=[4.0, 4.5, 5.0, 6.0],
            T=[2, 1])   # fzstop / batch / first_k: replay paths not covered by the self-check (verifier 2026-11-17):
                        # only via --grid after a cross-check against a real run
KNOBS = ("ck_keep", "ck_min", "tau", "kmin", "win", "ncand", "z0", "final", "final_post", "fine_last", "T", "ck",
         "phase_keep", "first_k", "batch", "cores", "fzstop", "ck_win")


# ------------------------------------------------------------------ data
def load_chunk(fn):
    z = np.load(fn)
    C = json.loads(str(z["flc_js"][0]))
    for s_ in z["flc_js"][1:]:
        c2 = json.loads(str(s_))
        assert c2["rx"] == C["rx"] and c2["G"] == C["G"] and c2["FLF"] == C["FLF"], f"{fn}: calls differ"
    b = {k: z[f"flb_{k}"] for k in ("pk", "search", "passed", "right", "stage") + COSTS}
    P = {}
    if "flp_pk" in z.files:
        for n, pk in enumerate(z["flp_pk"]):
            P[int(pk)] = dict(pq=z["flp_pq"][n], lp=z["flp_lp"][n], lpr=z["flp_lpr"][n], ct=int(z["flp_ct"][n]),
                              snap=z["flp_snap"][n].astype(np.float64), H={})
    mism, side_n, far_pass = 0, 0, 0
    if "flh_pk" in z.files:
        h = {k[4:]: z[k] for k in z.files if k.startswith("flh_")}
        o = np.lexsort((h["t"], -h["src"].astype(int), h["pk"]))       # src 0 (the search's own) last: preferred
        for q in o:
            pk = int(h["pk"][q])
            if pk not in P:
                continue
            key = (int(h["cell"][q]), int(h["po"][q]), int(h["kind"][q]))
            rec = (bool(h["crc_m"][q]), int(h["crc_r"][q]), bool(h["acc_m"][q]), bool(h["right_m"][q]),
                   bool(h["acc_r"][q]), bool(h["right_r"][q]), h["psn_m"][q].astype(np.float32),
                   h["psn_r"][q].astype(np.float32))
            L = P[pk]["H"].setdefault(key, {})
            t = int(h["t"][q])
            if t in L and int(h["src"][q]) == 0:                       # both logged: must agree
                a = L[t]
                if a[:3] != rec[:3] or a[3] != rec[3]:
                    mism += 1
            if int(h["src"][q]) == 1:
                side_n += 1
            if int(h["src"][q]) == 0 and abs(key[0] - P[pk]["ct"]) > C["fl"]["near"] and (rec[0] or rec[1] == 1):
                far_pass += 1
            L[t] = rec if (t not in L or int(h["src"][q]) == 0) else L[t]
    return dict(C=C, b=b, P=P, mism=mism, side=side_n, far_pass=far_pass, snr=float(z["snr"]))


def load_part(part):
    d = os.path.join(RESULTS, f"blind_fs_{part}_dump")
    fs = sorted(glob.glob(os.path.join(d, "fl_*.npz")))
    assert fs, f"{part}: no {d}/fl_*.npz (run_blind_fs --fulllog; fetch the _dump folder)"
    return fs


# ------------------------------------------------------------------ replay
class Replay:
    """One chunk's constants and a setting -> the replay of one packet (small_rx._small_receive's search loop for the
    modelled receivers, its cost counters)."""

    def __init__(self, C, s):
        self.C, M = C, C["mac"]
        rx = C["rx"]
        self.s = s = {**{k: rx.get(k) for k in KNOBS}, **s}
        self.G, self.nph, self.KP = C["G"], C["nph"], C["KP"]
        ncore = s["cores"] or (s["batch"][0] if s["batch"] else None)
        self.Kc = ncore or self.G
        self.m, self.dr, self.cm = M["m_met"], M["derot"], M["cmul"]
        self.dec, self.llr, self.ren, self.pre, self.ca2, self.ckm = (M[k] for k in ("dec", "llr", "reenc", "premf",
                                                                                      "ca2", "ckm"))
        self.ndec = M["n_dec"]
        self.dp8 = self.dec / 8 * math.ceil(8 / self.Kc) + self.ndec * 10.0   # lg 4: 4 x 5 / 2 sort stages
        self.dcp = self.dec / 8 * math.ceil(8 / self.Kc) + self.llr / self.KP + self.ndec * 10.0
        cnn = C["cnn"]
        self.cnn = cnn
        ck = s["ck"]
        cks = [1.0] if not ck else sorted(set(float(x) for x in ck) | {1.0})
        if cnn is not None:
            cf = CK_FR[cnn]
            cks = sorted({c for c in cks if c > cf} | {cf, 1.0})
        pk = s["phase_keep"]
        if pk is not None:
            cks = sorted(set(cks) | {float(pk[0])})
        FLF = C["FLF"]
        miss = [c for c in cks if not any(abs(c - f) < 1e-12 for f in FLF)]
        assert not miss, f"checkpoints {miss} not logged (logged {FLF})"
        self.cols = [min(range(len(FLF)), key=lambda q: abs(FLF[q] - c)) for c in cks]
        self.frac = [C["frL"][q] for q in self.cols]
        self.sh = np.array([C["shL"][q] for q in self.cols])
        self.jnn = cks.index(CK_FR[cnn]) if cnn is not None else -1
        rxv = C["rx"]
        self.nk = None
        if pk is not None:
            self.nk = (max(1, pk[1] // 2) if (rxv["equiv"] or rxv["bpsk_sq"]) else 2 * pk[1] if rxv["nopi"] else pk[1])
        self.qph = C["qph"]
        self.fz = None
        if s["fzstop"] is not None:
            q, t = s["fzstop"]
            c = int(np.argmin(np.abs(np.array(C["fz_q"]) - q)))
            assert abs(C["fz_q"][c] - q) < 1e-9 and C["fz_tr"] is not None, "fzstop: q must be a logged FZ_Q"
            tr, nb = C["fz_tr"][c], C["fz_nb"][c]
            self.fz = (c, float(t), (1 - tr) * self.dec,
                       (1 - tr) * self.dec / 8 * math.ceil(8 / self.Kc) + (self.ndec - nb) * 10.0)

    # small_rx _par / _segs (verbatim semantics)
    def _par(self, v, cost, nh=None, join=None, hyp=None):
        keep_ = cost > 0
        cost = cost[keep_]
        if len(cost):
            Kc = self.Kc
            v[1] += cost.sum()
            lp = np.sort(cost)[::-1][::Kc].sum()
            v[4] += lp
            v[5] += lp
            j_ = np.zeros(len(cost)) if join is None else np.broadcast_to(join, keep_.shape)[keep_]
            if hyp is None:
                h_ = np.ones(len(cost), int) if nh is None else np.maximum(np.broadcast_to(nh, keep_.shape)[keep_], 1)
                hc = np.repeat((cost - j_) / h_ + j_, h_)
            else:
                L_, C_ = hyp[0][keep_], hyp[1][keep_]
                n_h = np.maximum((C_ * (L_ > 0)).max(1), 1)
                hc = np.concatenate([(self.m * (L_ * (C_ > h)).sum(1) + j_)[n_h > h] for h in range(int(n_h.max()))])
            v[6] += np.sort(hc)[::-1][::Kc].sum()

    @staticmethod
    def _segs(qcut, qal, paid, c, hi):
        S = sorted(qcut)
        e = [0.0] + S + [np.inf]
        L = np.stack([np.clip(np.minimum(hi, e[k + 1]) - np.maximum(paid[c], e[k]), 0, None)
                      for k in range(len(S) + 1)], 1)
        C = np.stack([qcut[s][c] for s in S] + [qal[c].sum(1)], 1)
        return L, C

    def _call(self, v, H, ct, rows, kind, t, st):
        """One decode() call of refine2 round t: rows = hypothesis keys; returns (accepted any, right of the delivered
        = last accepted row)."""
        n = len(rows)
        near = self.C["fl"]["near"]
        v[0] += n * (self.pre * bool(self.C["rx"]["premf_dec"]) + self.dec + self.llr)
        v[2] += n * (self.dec + self.llr)
        v[7] += n * self.dcp
        v[9] += (math.ceil(n / 4) - n) * self.dp8
        recs = []
        for key in rows:
            r_ = H.get(key, {}).get(t)
            if r_ is None:
                st["unl_near" if abs(key[0] - ct) <= near else "unl_far"] += 1
            recs.append(r_)
        crc = [bool(r_ is not None and r_[0]) for r_ in recs]
        fz = self.fz
        if fz is not None:                                         # F5 on the main decodes
            stp = [bool(r_ is not None and r_[6][fz[0]] > fz[1]) for r_ in recs]
            self._fzcost(v, stp)
            crc = [c and not s_ for c, s_ in zip(crc, stp)]
        src = ["m" if c else None for c in crc]
        jr = [q for q in range(n) if not crc[q]] if self.C["rx"]["ca_retry"] else []
        if jr:
            nr = len(jr)
            v[9] += (math.ceil(nr / 4) - nr) * self.dp8 + (math.ceil(nr / self.KP) - nr) * self.m
            v[0] += nr * (self.m + self.llr + self.ca2 + self.dec + self.llr)
            v[3] += nr * self.m
            v[8] += nr * self.m
            v[2] += nr * (self.dec + self.llr)
            v[7] += nr * self.dcp
            cr = []
            for q in jr:
                r_ = recs[q]
                if r_ is not None and r_[1] == -1:                 # (a stopped main whose retry is not logged)
                    st["unl_retry"] += 1
                cr.append(bool(r_ is not None and r_[1] == 1))
            if fz is not None:
                stp = [bool(recs[q] is not None and recs[q][7][fz[0]] > fz[1]) for q in jr]
                self._fzcost(v, stp)
                cr = [c and not s_ for c, s_ in zip(cr, stp)]
            for q, c in zip(jr, cr):
                if c:
                    src[q] = "r"
        nok = sum(x is not None for x in src)
        v[0] += nok * self.ren
        acc_any, right = False, False
        for q in range(n):
            r_ = recs[q]
            if src[q] == "m" and r_[2]:
                acc_any, right = True, r_[3]
            elif src[q] == "r" and r_[4]:
                acc_any, right = True, r_[5]
        st["dec"] += n + len(jr)
        return acc_any, right

    def _fzcost(self, v, stp):
        if not any(stp):
            return
        c, t, tot, cr = self.fz
        w = sum(stp)
        v[0] -= w * tot
        v[2] -= w * tot
        v[7] -= w * cr
        n_all = sum(all(stp[a:a + 4]) for a in range(0, len(stp), 4))
        v[9] += (w - n_all) * cr

    def refine(self, v, H, ct, cands, kind, st):
        """refine2 of cands (keys (cell, po, kind)) in one call: scoring, then T rounds until an accept."""
        Hh = self.C["H_std"] if kind == 0 else self.C["H_fine"]
        T = self.s["T"] if kind == 0 else self.C["rx"]["T_fine"]
        n = len(cands)
        cs = self.m + self.dr
        v[0] += n * Hh * cs
        v[1] += n * Hh * cs
        v[4] += math.ceil(n * Hh / self.Kc) * cs
        for t in range(T):
            ok, rt = self._call(v, H, ct, cands, kind, t, st)
            if ok:
                return True, rt
        return False, False

    def packet(self, P):
        """(passed, right, stage, cost vector (10,), stats) of one search packet."""
        s, C, G = self.s, self.C, self.G
        st = dict(unl_near=0, unl_far=0, unl_retry=0, dec=0)
        v = P["snap"].copy()
        H, ct = P["H"], P["ct"]
        Pq = P["pq"][:, :, self.cols]
        frac, sh, jnn = self.frac, self.sh, self.jnn
        cm_d = self.cm + self.dr
        pm = Pq.min(0)
        qb = Pq.argmin(0)
        adj = pm - pm
        LP = P["lpr"]
        base = np.ones(G, bool)
        rounds = [base]
        if s["first_k"]:
            short = np.zeros(G, bool)
            short[np.argsort(-LP)[:s["first_k"]]] = True
            rounds = [short & base, base]
        if s["batch"]:
            blk = np.array_split(np.arange(G), -(-G // s["batch"][0]))
            blk.sort(key=lambda b_: -np.logaddexp.reduce(LP[b_]))
            acc = np.zeros(G, bool)
            rounds = []
            for b_ in blk:
                acc = acc.copy()
                acc[b_] = True
                rounds.append(acc & base)
        qal = np.ones((G, self.nph), bool)
        paid = np.zeros(G)
        joined = np.zeros(G, bool)
        tried = set()
        qcut = {}
        new_acct = not C["rx"]["old_acct"]
        charge_all = bool(C["rx"]["ck_charge_all"])
        po = lambda c, q: (c, int(self.qph[q]) % 8, 0)
        passed = right = False
        stage = 0
        z = zf = alive = None

        def ref(cands, kind=0):
            nonlocal passed, right
            ok, rt = self.refine(v, H, ct, cands, kind, st)
            if ok:
                passed, right = True, rt
            return ok

        for rnd, alive0 in enumerate(rounds):
            if rnd and not (alive0 & ~rounds[rnd - 1]).any():
                break
            alive = alive0.copy()
            skip = False
            jn_ = alive & ~joined
            v[0] += jn_.sum() * cm_d
            self._par(v, np.full(jn_.sum(), cm_d),
                      self._segs(qcut, qal, paid, jn_, 0.0)[1][:, 0] if (new_acct and qcut) else qal[jn_].sum(1), cm_d)
            joined |= alive
            for j, f_ in enumerate(frac):
                chg = alive
                if charge_all and self.cnn is not None and j == jnn:
                    chg = alive | (paid < sh[j])
                    jx_ = chg & ~alive & ~joined
                    if jx_.any():
                        v[0] += jx_.sum() * cm_d
                        self._par(v, np.full(jx_.sum(), cm_d), self._segs(qcut, qal, paid, jx_, 0.0)[1][:, 0]
                                  if (new_acct and qcut) else qal[jx_].sum(1), cm_d)
                        joined |= jx_
                if new_acct and qcut:
                    L_, C_ = self._segs(qcut, qal, paid, chg, sh[j])
                    w_ = self.m * (L_ * C_).sum(1)
                    v[0] += w_.sum()
                    self._par(v, w_, hyp=(L_, C_))
                else:
                    v[0] += self.m * (qal[chg].sum(1) * np.clip(sh[j] - paid[chg], 0, None)).sum()
                    self._par(v, self.m * qal[chg].sum(1) * np.clip(sh[j] - paid[chg], 0, None), qal[chg].sum(1))
                paid[chg] = np.maximum(paid[chg], sh[j])
                z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                if j == len(frac) - 1:
                    break
                if self.cnn is not None and j == jnn:
                    lp = P["lp"]
                    v[0] += self.ckm
                    o = np.argsort(-lp)
                    o = o[alive[o]]
                    if s["ck_win"] is not None and np.exp(lp[o[0]]) > s["ck_win"] and o[0] not in tried:
                        c = int(o[0])
                        tried.add(c)
                        if ref([po(c, qb[c, j])]):
                            stage = 2
                            break
                    n_ = max(s["ck_min"], int(np.searchsorted(np.cumsum(np.exp(lp[o])), 1 - s["ck_keep"])) + 1)
                    keep = np.zeros(G, bool)
                    keep[o[:n_]] = True
                    alive &= keep
                    continue
                pk_ = s["phase_keep"]
                if pk_ is not None and f_ == pk_[0]:
                    sc_ = np.where(qal, Pq[:, :, j].T, np.inf)
                    if new_acct:
                        qcut.setdefault(sh[j], qal.sum(1))
                    qal &= np.argsort(np.argsort(sc_, 1), 1) < self.nk
                    P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                    pm, qb = P_.min(0) + adj, P_.argmin(0)
                    z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                if s["win"] is not None:
                    zt = z.copy()
                    zt[list(tried)] = -np.inf
                    c = int(zt.argmax())
                    if zt[c] > s["win"]:
                        tried.add(c)
                        if ref([po(c, qb[c, j])]):
                            break
                if s["batch"] and rnd < len(rounds) - 1 and z.max() < s["batch"][1]:
                    skip = True
                    break
                keep = z > s["tau"]
                keep[np.argsort(-z)[:s["kmin"]]] = True
                alive &= keep
            if passed:
                break
            zf = z
            if skip:
                continue
            qc_ = qb[:, -1]
            cs = [c for c in np.argsort(-zf)[:s["ncand"]] if zf[c] > s["z0"] and c not in tried]
            for c in cs:
                tried.add(c)
                if ref([po(c, qc_[c])]):
                    break
            if passed:
                break
        if passed:
            return True, right, 2, v, st
        cs = [c for c in np.argsort(np.where(alive, pm[:, -1], np.inf))[:s["final"]] if c not in tried]
        for c in cs:
            tried.add(c)
            if ref([po(c, qb[c, -1])]):
                return True, right, 3, v, st
        if s["final_post"]:
            cs = [c for c in np.argsort(-zf) if np.isfinite(zf[c]) and c not in tried][:s["final_post"]]
            tried.update(cs)
            cand = [(c, (int(self.qph[qb[c, -1]]) + 2 * b) % 8, 0) for c in cs for b in C["bs"]]
            for a in range(0, len(cand), 8):
                if ref(cand[a:a + 8]):
                    return True, right, 4, v, st
        if s["fine_last"]:
            cs = np.argsort(np.where(alive, pm[:, -1], np.inf))[:s["fine_last"]]
            for c in cs:
                if ref([(int(c), int(self.qph[qb[c, -1]]) % 8, 1)], 1):
                    return True, right, 5, v, st
        return False, False, 0, v, st


def _rz(x):
    med = np.nanmedian(x)
    return (med - x) / (1.4826 * np.nanmedian(np.abs(x - med)) + 1e-6)


def _final(v, KP):
    cpar = v[4] + v[7] + v[8] + (v[0] - v[1] - v[2] - v[3]) / KP
    return dict(macs=v[0], cpar=cpar, c_d4a=cpar + v[9], c_hd4a=cpar - v[5] + v[6] + v[9])


def replay_chunk(D, s):
    """Every packet of a loaded chunk under setting s: arrays passed, right, stage, costs, unlogged counts."""
    b = D["b"]
    n = len(b["pk"])
    R = dict(passed=b["passed"].copy(), right=b["right"].copy(), stage=b["stage"].astype(int).copy(),
             **{k: b[k].astype(np.float64).copy() for k in COSTS}, unl_near=np.zeros(n, int), unl_far=np.zeros(n, int),
             unl_retry=np.zeros(n, int), dec=np.zeros(n, int))
    rp = Replay(D["C"], s)
    for q in range(n):
        pk = int(b["pk"][q])
        if not b["search"][q] or pk not in D["P"]:
            continue
        ps, rt, stg, v, st = rp.packet(D["P"][pk])
        R["passed"][q], R["right"][q], R["stage"][q] = ps, rt, stg
        for k, x in _final(v, rp.KP).items():
            R[k][q] = x
        for k in ("unl_near", "unl_far", "unl_retry", "dec"):
            R[k][q] = st[k]
    return R


# ------------------------------------------------------------------ workers (each owns its chunk files)
def _worker(files, qin, qout):
    data = [load_chunk(f) for f in files]
    qout.put(("loaded", [(D["snr"], len(D["b"]["pk"]), D["mism"], D["side"], D["far_pass"],
                          json.dumps(D["C"]["rx"]), D["C"]["Kc"], D["C"]["numpy"]) for D in data]))
    while True:
        s = qin.get()
        if s is None:
            return
        try:
            out = [replay_chunk(D, s) for D in data]
            qout.put(("ok", out))
        except Exception as e:                                            # noqa: BLE001
            import traceback
            qout.put(("err", f"{e!r}\n{traceback.format_exc()}"))


class Pool_:
    def __init__(self, files, n):
        n = max(1, min(n, len(files)))
        shards = [files[k::n] for k in range(n)]
        self.files = [f for sh in shards for f in sh]
        self.P = []
        self.meta = []
        for sh in shards:
            qi, qo = Queue(), Queue()
            pr = Process(target=_worker, args=(sh, qi, qo), daemon=True)
            pr.start()
            self.P.append((pr, qi, qo))
        for _, _, qo in self.P:
            tag, m = qo.get()
            self.meta += m
        self.cache = {}

    def run(self, s):
        key = json.dumps(s, sort_keys=True)
        if key in self.cache:
            return self.cache[key]
        for _, qi, _ in self.P:
            qi.put(s)
        out = []
        for _, _, qo in self.P:
            tag, x = qo.get()
            if tag == "err":
                raise RuntimeError(x)
            out += x
        R = {k: np.concatenate([o[k] for o in out]) for k in out[0]}
        self.cache[key] = R
        return R

    def close(self):
        for pr, qi, _ in self.P:
            qi.put(None)
        for pr, _, _ in self.P:
            pr.join(5)


# ------------------------------------------------------------------ evaluation / search
class Eval:
    def __init__(self, parts, workers):
        self.files, self.ptag = [], []
        for pa in parts:
            for f in load_part(pa):
                self.files.append(f)
                self.ptag.append(pa)
        self.pool = Pool_(self.files, workers)
        order = {f: i for i, f in enumerate(self.files)}
        tagof = {f: t for f, t in zip(self.files, self.ptag)}
        pts, self.keys = [], []
        for f, m in zip(self.pool.files, self.pool.meta):
            k = (tagof[f], round(m[0], 3))
            if k not in self.keys:
                self.keys.append(k)
            pts.append(np.full(m[1], self.keys.index(k)))
        self.pt = np.concatenate(pts)
        self.npt = len(self.keys)
        self.frames = np.bincount(self.pt, minlength=self.npt)
        self.mism = sum(m[2] for m in self.pool.meta)
        self.side = sum(m[3] for m in self.pool.meta)
        self.far_pass = sum(m[4] for m in self.pool.meta)
        rxs = {m[5] for m in self.pool.meta}
        assert len(rxs) == 1, f"parts mix receivers: {rxs}"
        self.rx = json.loads(rxs.pop())
        self.std = STD.get(self.rx["rate"], "c_d4a")
        self.kc_log = {m[6] for m in self.pool.meta}
        self.np_log = {m[7] for m in self.pool.meta}
        self.base = None

    def stats(self, R):
        err = np.bincount(self.pt, ~R["right"], minlength=self.npt).astype(int)
        c = R[self.std]
        mpt = np.bincount(self.pt, c, minlength=self.npt) / self.frames
        # objective (lead, 2026-11-17, verifier note 4): the mean of the per-point means, not the frame-weighted pool
        # (the frame counts were chosen for error statistics); the pooled mean is kept as mean_pooled
        bm = getattr(self, "base_mpt", None)
        # --objective rel (default, lead 2026-11-17 22:50): every point counts by its RELATIVE cost (mean over points of
        # cost / baseline cost, scaled by the baseline's mean so it reads in MACs); abs = the plain mean of the per-point
        # means (lets the expensive low-SNR points dominate: the first run traded +18 % at -4.6 dB for -48 % at -6.2)
        obj = float((mpt / bm).mean() * bm.mean()) if (bm is not None and getattr(self, "objective", "rel") == "rel")             else float(mpt.mean())
        return dict(err=err.tolist(), err_tot=int(err.sum()), mean=obj, mean_abs=float(mpt.mean()), mean_pooled=float(c.mean()),
                    p99=float(np.percentile(c, 99)), max=float(c.max()), mean_pt=mpt.tolist(),
                    unl_near=int(R["unl_near"].sum()), unl_far=int(R["unl_far"].sum()),
                    unl_retry=int(R["unl_retry"].sum()))


def selfcheck(E, rtol=1e-6):
    """The receiver's own settings (cores as logged) must give the logged result: passed / right / stage per packet,
    every cost within rtol, no unlogged decode."""
    R = E.pool.run({})
    B = {k: np.concatenate([np.load(f)[f"flb_{k}"] for f in E.pool.files])
         for k in ("passed", "right", "stage") + COSTS}
    bad = {k: int((R[k] != B[k]).sum()) for k in ("passed", "right", "stage")}
    rel = {k: float(np.max(np.abs(R[k] - B[k]) / np.maximum(np.abs(B[k]), 1.0))) for k in COSTS}
    unl = int(R["unl_near"].sum() + R["unl_far"].sum())
    ok = all(v == 0 for v in bad.values()) and all(v <= rtol for v in rel.values()) and unl == 0 and E.mism == 0
    return ok, dict(mismatch=bad, max_rel_cost_err=rel, unlogged=unl, side_vs_own_mismatch=E.mism,
                    packets=int(len(R["right"])), errors=int((~B["right"]).sum())), R


def feasible(E, st, allow, base_err):
    return bool((np.array(st["err"]) - base_err <= allow).all())


def search(E, grid, base_set, rel, restarts, seed, log):
    """Coordinate descent over the knob grids from the baseline (+ random restarts): minimise the mean std MACs per core
    subject to the 2 % rule at every point; every evaluation recorded."""
    recs = {}

    def ev(s):
        key = json.dumps(s, sort_keys=True)
        if key not in recs:
            t0 = time.time()
            st = E.stats(E.pool.run(s))
            st["ok"] = feasible(E, st, E.allow, E.base_err)
            st["extra"] = (np.array(st["err"]) - E.base_err).tolist()
            recs[key] = dict(setting=s, **st)
            log(f"  {'*' if st['ok'] else ' '} mean {st['mean'] / 1e6:7.4f} M  err {st['err_tot']:5d} "
                f"extra {st['extra']}  unl {st['unl_near']}/{st['unl_far']}  {json.dumps(s)}  ({time.time() - t0:.1f} s)")
        return recs[key]

    def descend(s):
        best = ev(s)
        changed = True
        while changed:
            changed = False
            for kn, vals in grid.items():
                for x in vals:
                    s2 = {**best["setting"], kn: x}
                    r = ev(s2)
                    if r["ok"] and (r["mean"] < best["mean"] - 1e-9 or not best["ok"]):
                        best, changed = r, True
        return best

    out = [descend(dict(base_set))]
    rng = random.Random(seed)
    for _ in range(restarts):
        s = {**base_set, **{kn: rng.choice(v) for kn, v in grid.items()}}
        out.append(descend(s))
    feas = [r for r in recs.values() if r["ok"]]
    chosen = min(feas, key=lambda r: (r["mean"], r["err_tot"])) if feas else None
    return list(recs.values()), chosen


def pareto(recs):
    front, best = [], np.inf
    for x in sorted(recs, key=lambda x: (x["mean"], x["err_tot"])):
        if x["err_tot"] < best:
            front.append(x)
            best = x["err_tot"]
    return front


def validate(E, s, base_set):
    R0, R1 = E.pool.run(base_set), E.pool.run(s)
    rows = []
    for k, (part, esn0) in enumerate(E.keys):
        m = E.pt == k
        c0, c1 = R0[E.std][m], R1[E.std][m]
        rows.append(dict(part=part, esn0=esn0, n=int(m.sum()), err_base=int((~R0["right"][m]).sum()),
                         err=int((~R1["right"][m]).sum()), lost=int((R0["right"][m] & ~R1["right"][m]).sum()),
                         gained=int((~R0["right"][m] & R1["right"][m]).sum()), mean_base=float(c0.mean()),
                         mean=float(c1.mean()), p99_base=float(np.percentile(c0, 99)),
                         p99=float(np.percentile(c1, 99)), max_base=float(c0.max()), max=float(c1.max()),
                         unl_near=int(R1["unl_near"][m].sum()), unl_far=int(R1["unl_far"][m].sum())))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calib", nargs="*", default=[])
    ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--name", required=True)
    ap.add_argument("--setting", default=None, help="JSON knob dict (skip the search; validate it)")
    ap.add_argument("--grid", default=None, help="JSON {knob: [values]} replacing GRID (knobs: %s)" % ", ".join(KNOBS))
    ap.add_argument("--rel", type=float, default=0.02)
    ap.add_argument("--restarts", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--no-honest-kc", action="store_true", help="replay candidates with the logged cores (batch "
                    "null: one grid core per cell) instead of cores 32")
    ap.add_argument("--objective", default="rel", choices=["rel", "abs"], help="rel: mean over points of cost / "
                    "baseline cost (each SNR counts equally); abs: mean of the per-point mean MACs")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--no-strict", action="store_true", help="continue after a failed self-check")
    a = ap.parse_args()
    out = os.path.join(RESULTS, f"joint_{a.name}.json")
    assert not os.path.exists(out), f"{out} exists: use a new --name"
    assert a.calib or a.test, "give --calib and / or --test parts"
    lines = []

    def log(x):
        print(x, flush=True)
        lines.append(x)

    res = dict(meta=dict(args=vars(a), approx="unlogged decodes counted failed (n_unl per setting)"))
    grid = json.loads(a.grid) if a.grid else GRID
    bad = sorted(set(grid) - set(KNOBS))
    assert not bad, f"unknown knobs {bad}"
    chosen = json.loads(a.setting) if a.setting else None
    honest = {} if a.no_honest_kc else {"cores": 32}
    if a.calib:
        t0 = time.time()
        E = Eval(a.calib, a.workers)
        log(f"calibration: {len(E.files)} chunks, {len(E.pt)} packets, {E.npt} points, std {E.std}, logged Kc "
            f"{E.kc_log}, numpy (log) {E.np_log} / here {np.__version__}, side rows {E.side}, far-cell CRC passes in "
            f"the search's own rows {E.far_pass} ({time.time() - t0:.0f} s)")
        ok, chk, R0 = selfcheck(E)
        log(f"SELF-CHECK {'OK' if ok else 'FAILED'}: {chk}")
        res["selfcheck"] = dict(ok=ok, **chk)
        if not ok and not a.no_strict:
            E.pool.close()
            with open(out, "w") as fh:
                json.dump(res, fh, indent=1)
            raise SystemExit("self-check failed (see above); --no-strict to continue")
        st0 = E.stats(R0)
        E.base_err = np.array(st0["err"])
        E.allow = np.floor(a.rel * E.base_err + 1e-9)
        base_set = dict(honest)
        stb = E.stats(E.pool.run(base_set))
        E.objective = a.objective
        E.base_mpt = np.array(stb["mean_pt"])
        stb = E.stats(E.pool.run(base_set))
        log(f"baseline (logged settings{', cores 32' if honest else ''}): errors {st0['err']} mean "
            f"{stb['mean'] / 1e6:.4f} M (logged cores {st0['mean'] / 1e6:.4f} M) max {stb['max'] / 1e6:.3f} M; "
            f"allowed extra {E.allow.astype(int).tolist()}")
        res["calib"] = dict(parts=a.calib, points=[list(k) for k in E.keys], frames=E.frames.tolist(),
                            err_base=st0["err"], allowed=E.allow.astype(int).tolist(), base_logged=st0,
                            base_replay=stb, receiver=E.rx)
        if not a.check_only:
            if chosen is None:
                recs, best = search(E, grid, base_set, a.rel, a.restarts, a.seed, log)
                res["calib"].update(n_settings=len(recs), front=pareto(recs),
                                    feasible_top=sorted([r for r in recs if r["ok"]], key=lambda r: r["mean"])[:50])
                chosen = best["setting"] if best else None
                if best:
                    log(f"CHOSEN {json.dumps(chosen)}: mean {best['mean'] / 1e6:.4f} M (baseline "
                        f"{stb['mean'] / 1e6:.4f}) err {best['err']} max {best['max'] / 1e6:.3f} M")
            if chosen is not None:
                res["calib"]["per_point"] = validate(E, chosen, base_set)
        E.pool.close()
    res["chosen"] = chosen
    if a.test and chosen is not None:
        T = Eval(a.test, a.workers)
        okT, chkT, _ = selfcheck(T)
        log(f"TEST self-check {'OK' if okT else 'FAILED'}: {chkT}")
        rows = validate(T, {**honest, **chosen}, dict(honest))
        for x in rows:
            log(f"  {x['part']:>14s} {x['esn0']:+6.2f} n {x['n']:6d} err {x['err_base']:5d} -> {x['err']:5d} (lost "
                f"{x['lost']}, gained {x['gained']}) mean {x['mean_base'] / 1e6:.4f} -> {x['mean'] / 1e6:.4f} M max "
                f"{x['max_base'] / 1e6:.3f} -> {x['max'] / 1e6:.3f} M unl {x['unl_near']}/{x['unl_far']}")
        res["test"] = dict(parts=a.test, selfcheck=dict(ok=okT, **chkT), rows=rows)
        T.pool.close()
    res["log"] = lines
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
