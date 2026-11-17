"""
Offline tuning and validation-by-replay of the BLIND receiver's early stops on the full-system formats: the decode rows
of run_blind_fs runs with the stops OFF and --dump are replayed under a stop setting (F5 (q, t), a stage cut-off, a
MAC-per-core cap), tuned on the --calib parts, validated on the test parts (the same packets: paired). Local analysis
of existing dumps only: no receiver or simulation code is imported or run.

Inputs per part P (run_blind_fs --part P --dump):
    fullsys/results/blind_fs_<P>.json        meta (MAC model mac.decode, K, N, sps cores, std_core, cap_core) and per
                                             point frame_err / cap_hit_right / frames (no JSON: the first part's meta)
    fullsys/results/blind_fs_<P>_dump/       pk_<fmt>_<snr>_c<chunk>.npz + rows_<...>.npz (the puller skips *_dump:
                                             fetch them with cluster.pull, e.g. fullsys/results/blind_fs_fs-k13m08_dump)
    --frozen F.npy (optional)                the code's frozen set (N,) bool (BlindFormat.code.frozen), for the exact
                                             tree share of a stopped decode (default: the pos / N approximation)

Replay (one packet: its CA-SCL calls in the receiver's order, the fz rows f / j sorted by (seq, slot); they map 1:1 onto
the decode rows d sorted by att, whose d_acc / d_right mark the accepted decode; the stops never change the order, only
turn decodes into CRC failures):
  F5 (q, t)  q in FZ_Q only (the logged checkpoints: f_psn_min at the first node boundary with >= ceil(q F) masked frozen
             leaves = the quantity polar.PolarCode fz_stop tests); a decode stops if psn_min > t (nan: never).
             LOST: a right packet whose accepted right decode(s) stop (conservative: the CA retry of a stopped main
             decode and the cells after it are not logged, no rescue is counted). Cost as small_rx _fzs: a stopped
             decode gives back cr = (1 - share(pos_s)) MAC_dec / 8 ceil(L / Kc) + (K - nb_s) lg (lg + 1) / 2 (lg = log2
             2L; L 8 CA-SCL, 16 joint) of crit_par; the std model (d4a) gets cr back once per 4-decode round (rows of
             one call, slot // 4) all of whose decodes stop, a joint decode alone. share = small_rx.fz_share(frozen,
             pos_s) with --frozen (exact), else pos_s / N (no Fast-SSC rate-0 discount of the early leaves: the saving
             is underestimated, conservative). A lost packet (or a wrongly accepted one whose accepted decode stops)
             searches on: charged max(its own replayed cost, the mean replayed cost of the point's failed searches).
  stage s    stages 1 fast, 2 grid, 3 final, 4 final_post, 5 fine_last (decode tags small_rx.DEC_TAGS -> TAG_STAGE);
             s < 5: the receiver ends after stage s; cost = the stage_acc snapshot pk cost[:, s - 1] (exact), packets
             accepted later fail, stop savings of the stages <= s only.
  cap C      on crit_par as small_rx cap_core (emulated after the search): crit_par after the stops > C -> no packet
             (a right one is lost), its costs scaled to C. A logged cap (--cap-core runs) is undone first: crit_par_true =
             crit_par_log x cost[last stage] / std_log (the stage snapshots precede the cap scaling: exact); under a
             stage cut crit_par = crit_par_true x std_cut / std_true (approximate; enters the cap check only).
  not replayable: spec11 (win_spec off in the runs: its speculative decodes are not logged), the checkpoint kept
             fraction / z-test (it changes which cells are decoded and their order), the re-encoding threshold.
  MACs per core = the meta std_core model (c_d4a at 2/5, 1/2; c_hd4a at 0.15), mean and p99 over the packets.

Tuning (--calib parts only): grid q x t x stage x cap (setting "off" = no F5); per setting the errors at every
calibration point (part, Es/N0) and the pooled mean / p99 MACs per core; the Pareto front (total errors vs mean); the
chosen setting = the cheapest one whose errors exceed the no-stop errors by <= floor(--rel x no-stop errors) (default
0.02) at EVERY calibration point. Validation (--test parts): no stops vs the chosen setting on the same packets
(packets lost = right without the stops, wrong with them), mean / p99 MACs per core before / after, both without a cap
and with the run's own cap (min with the setting's); the cap effect from the JSON: no-cap errors = frame_err -
cap_hit_right (cross-checked with the dump's no-cap replay when the dump holds every chunk).

    py fullsys/tune_blind_fs.py --calib fs-k13m08 fs-k13m06 fs-k13m04 --test fs-c13m08 fs-c13m06 fs-c13m04 \
        fs-c13m02 fs-c13p00 --name k13 [--frozen id13_frozen.npy]
    py fullsys/tune_blind_fs.py --test fs-b13cap-nc --setting 0.5,0.6,5,none --name b13chk      # one setting only

Writes fullsys/results/tune_<name>.json (--out: another path) and prints the tables.
"""

import argparse
import glob
import json
import os
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "fullsys", "results")
FZ_Q = (0.25, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)        # small_rx.FZ_Q: the logged psn checkpoints (fractions of F)
TAG_STAGE = {0: 1, 1: 2, 2: 2, 3: 2, 7: 2, 4: 3, 5: 4, 6: 5}   # small_rx.DEC_TAGS (fast, win, spec, s2cand, early_z,
                                                    # final32, post, fine_last) -> stage 1 .. 5 (unknown tag: 2)
STD_COL = {"c_d4a": 1, "c_hd4a": 2}                 # pk cost[:, :, k]: [macs, crit_par_d4a, crit_par_h_d4a]
T_GRID = (0.30, 1.20, 0.01)                         # default t grid (lo, hi, step)
CAPS = ("none", "1e6", "1.5e6", "2e6", "3e6", "5e6", "8e6")   # default cap grid (MACs per core on crit_par)
STAGES = (5, 4, 3, 2)                               # default stage cut-offs (5 = no cut)


def fz_share(frozen, pos):
    """Share of a CA-SCL decode's work done once leaves [0, pos) are decided (a copy of small_rx.fz_share: per path f
    and g n/2 each at an internal node, n at a rate-0 node, 1 at a frozen leaf, 2 at an information leaf)."""
    fz, out, acc = np.asarray(frozen, bool), [], [0.0]

    def walk(lo, hi):
        n = hi - lo
        if n == 1 or fz[lo:hi].all():
            acc[0] += n if fz[lo:hi].all() else 2
            out.append((hi, acc[0]))
            return
        acc[0] += n / 2
        walk(lo, lo + n // 2)
        acc[0] += n / 2
        walk(lo + n // 2, hi)

    walk(0, len(fz))
    a = np.array(out, float)
    P, T = np.r_[0, a[:, 0]].astype(int), np.r_[0, a[:, 1] / a[-1, 1]]
    return T[np.searchsorted(P, np.asarray(pos), side="right") - 1]


def _json(part):
    p = os.path.join(RESULTS, f"blind_fs_{part}.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def load_part(part, frozen=None, doc_fb=None):
    """One part's dump: per-packet arrays (P), fz rows (R: one per CA-SCL decode) and 4-decode rounds (U)."""
    doc = _json(part)
    d_ = doc or doc_fb
    assert d_ is not None, f"{part}: no blind_fs_{part}.json and no fallback meta"
    m = d_["meta"]
    fm = m["format"]
    N, K, mdec = int(fm["N"]), int(fm["K"]), float(fm["mac"]["decode"])
    Kc = int(m["sps"].get("cores") or 32)
    std = m.get("std_core", "c_d4a")
    col = STD_COL[std]
    cap_log = (m.get("cap_core") or m["args"].get("cap_core")) if doc is not None else None
    files = sorted(glob.glob(os.path.join(RESULTS, f"blind_fs_{part}_dump", "pk_*.npz")))
    assert files, f"{part}: no dump (fullsys/results/blind_fs_{part}_dump/pk_*.npz; fetch with cluster.pull)"
    if frozen is not None:
        assert len(frozen) == N, f"--frozen: {len(frozen)} leaves, the code has N = {N}"
    lut = np.full(256, 2, np.int8)
    for k, v in TAG_STAGE.items():
        lut[k] = v
    P, R, U, warn = [], [], [], []
    for fn in files:
        z = np.load(fn)
        r = np.load(os.path.join(os.path.dirname(fn), "rows_" + os.path.basename(fn)[3:]))
        B = len(z["right"])
        ar = np.arange(B)
        cost = z["cost"].astype(np.float64)
        lr = np.where(z["reach"], np.arange(5), -1).max(1)               # last stage reached (0 .. 4)
        cs = cost[:, :5, col]                                             # std cost at the end of each stage
        cd_true = cs[ar, lr]                                              # before any cap scaling
        cd_log = z[std].astype(np.float64)
        cp_true = z["cpar"].astype(np.float64) * cd_true / np.maximum(cd_log, 1.0)   # (logged cap undone)
        G = [g for g in ("f", "j") if f"{g}_pk" in r.files]
        cat = lambda k: np.concatenate([r[f"{g}_{k}"] for g in G])
        rp, rs, rl, rt, rL = cat("pk"), cat("seq"), cat("slot"), cat("tag"), cat("L")
        o = np.lexsort((rl, rs, rp))                                      # decode order per packet
        od = np.lexsort((r["d_att"], r["d_pk"]))
        assert len(o) == len(od) and (rp[o] == r["d_pk"][od]).all(), f"{fn}: fz rows do not map onto the d rows"
        rp, rs, rl, rt, rL = rp[o], rs[o], rl[o], rt[o], rL[o].astype(np.float64)
        psn = cat("psn_min")[o].astype(np.float32)
        psn[~np.isfinite(psn)] = -np.inf                                  # not reached: never stops
        pos, nb = cat("pos_s")[o].astype(np.float64), cat("nb_s")[o].astype(np.float64)
        acc, drt = r["d_acc"][od].astype(bool), r["d_right"][od].astype(bool)
        passed0 = np.zeros(B, bool)
        right0 = np.zeros(B, bool)
        passed0[rp[acc]] = True
        right0[rp[acc & drt]] = True
        if (z["right"] & ~right0).any():
            warn.append(f"{os.path.basename(fn)}: {int((z['right'] & ~right0).sum())} right packets without an "
                        f"accepted right d row")
        sel = acc & np.where(right0[rp], drt, True)                       # the accepted decode(s) of the packet
        ap = np.full((B, len(FZ_Q)), np.inf, np.float32)
        np.minimum.at(ap, rp[sel], psn[sel])
        ap[np.isposinf(ap)] = -np.inf                                     # no accepted decode: nothing to lose
        share = fz_share(frozen, pos) if frozen is not None else pos / N
        lg = np.log2(2 * rL)[:, None]
        cr = ((1 - share) * mdec / 8 * np.ceil(rL / Kc)[:, None] + (K - nb) * lg * (lg + 1) / 2).astype(np.float32)
        stg = lut[rt.astype(np.int64) & 0xFF]
        new = np.r_[True, (rp[1:] != rp[:-1]) | (rs[1:] != rs[:-1]) | (rl[1:] // 4 != rl[:-1] // 4)]
        st_ = np.flatnonzero(new)                                         # 4-decode rounds (joint: own call, slot 0)
        esn0 = float(z["esn0"])
        P.append(dict(esn0=np.full(B, esn0), lr=lr, cs=cs, cd_true=cd_true, cp_true=cp_true, cd_log=cd_log,
                      right_log=z["right"].astype(bool), right0=right0, passed0=passed0,
                      st0=np.where(passed0, z["stage"].astype(int), 0), accpsn=ap))
        R.append(dict(pk=rp, stg=stg, psn=psn, cr=cr))
        U.append(dict(pk=rp[st_], stg=stg[st_], psn=np.minimum.reduceat(psn, st_, axis=0), cr=cr[st_]))
    return dict(part=part, doc=doc, meta=m, std=std, cap_log=cap_log, P=P, R=R, U=U, warn=warn,
                share="fz_share(--frozen)" if frozen is not None else "pos/N")


class Set:
    """Parts concatenated: packets (global index), points (part, Es/N0), rows and rounds keyed (packet, stage)."""

    def __init__(self, parts):
        self.parts = parts
        Ps, Rs, Us, pts, off = [], [], [], [], 0
        self.pt_key, self.pt_part = [], []
        for pa in parts:
            for p, r, u in zip(pa["P"], pa["R"], pa["U"]):
                k = (pa["part"], round(float(p["esn0"][0]), 3))
                if k not in self.pt_key:
                    self.pt_key.append(k)
                    self.pt_part.append(pa)
                pts.append(np.full(len(p["lr"]), self.pt_key.index(k)))
                Ps.append(p)
                Rs.append(dict(r, pk=r["pk"] + off))
                Us.append(dict(u, pk=u["pk"] + off))
                off += len(p["lr"])
        c = lambda L, k: np.concatenate([x[k] for x in L])
        for k in Ps[0]:
            setattr(self, k, c(Ps, k))
        self.pt = np.concatenate(pts)
        self.n, self.npt = off, len(self.pt_key)
        self.ar = np.arange(off)
        self.r_key, self.r_psn, self.r_cr = c(Rs, "pk") * 5 + c(Rs, "stg") - 1, c(Rs, "psn"), c(Rs, "cr")
        self.u_key, self.u_psn, self.u_cr = c(Us, "pk") * 5 + c(Us, "stg") - 1, c(Us, "psn"), c(Us, "cr")
        self.frames = np.bincount(self.pt, minlength=self.npt)

    def savings(self, c, ts):
        """F5 at checkpoint c for the thresholds ts (descending): yields t, the cumulative-over-stages savings of the
        std model (rounds all stopped) and of crit_par (every stopped decode), (n, 5) each."""
        out = []
        for key, psn, cr in ((self.r_key, self.r_psn, self.r_cr), (self.u_key, self.u_psn, self.u_cr)):
            o = np.argsort(-psn[:, c], kind="stable")
            out.append((key[o], -psn[o, c], cr[o, c].astype(np.float64)))
        Sp, Sd = np.zeros(self.n * 5), np.zeros(self.n * 5)
        ip = iu = 0
        for t in ts:
            for nm, (k, v, w) in zip(("p", "d"), out):
                j = int(np.searchsorted(v, -t, side="left"))             # decodes with psn > t
                i0 = ip if nm == "p" else iu
                if j > i0:
                    (Sp if nm == "p" else Sd)[:] += np.bincount(k[i0:j], w[i0:j], minlength=self.n * 5)
                if nm == "p":
                    ip = j
                else:
                    iu = j
            yield t, np.cumsum(Sd.reshape(self.n, 5), 1), np.cumsum(Sp.reshape(self.n, 5), 1)

    def evaluate(self, SdC=None, SpC=None, stop_acc=None, scut=5, cap=None):
        """One setting: right (n,), std MACs per core (n,), crit_par (n,)."""
        e = np.minimum(self.lr, scut - 1)
        cut = self.lr > scut - 1
        cd = np.where(cut, self.cs[self.ar, scut - 1], self.cd_true)
        cp = self.cp_true * cd / np.maximum(self.cd_true, 1.0)
        if SdC is not None:
            cd = cd - SdC[self.ar, e]
            cp = cp - SpC[self.ar, e]
        late = self.st0 > scut
        right = self.right0 & ~late
        acc_ok = self.passed0 & ~late
        if stop_acc is not None and stop_acc.any():
            lost = acc_ok & stop_acc                                      # the accepted decode stopped: search on
            right = right & ~lost
            fail = ~acc_ok
            nf = np.bincount(self.pt[fail], minlength=self.npt)
            Fd = np.bincount(self.pt[fail], cd[fail], minlength=self.npt) / np.maximum(nf, 1)
            Fp = np.bincount(self.pt[fail], cp[fail], minlength=self.npt) / np.maximum(nf, 1)
            ls = lost & (nf[self.pt] > 0)
            cd = np.where(ls, np.maximum(cd, Fd[self.pt]), cd)
            cp = np.where(ls, np.maximum(cp, Fp[self.pt]), cp)
        if cap is not None:
            over = cp > cap
            right = right & ~over
            cd = np.where(over, cd * cap / np.maximum(cp, 1.0), cd)
            cp = np.minimum(cp, cap)
        return right, cd, cp

    def stats(self, right, cd):
        err = np.bincount(self.pt, ~right, minlength=self.npt).astype(int)
        mean_pt = np.bincount(self.pt, cd, minlength=self.npt) / np.maximum(self.frames, 1)
        return err, float(cd.mean()), float(np.percentile(cd, 99)), mean_pt


def _cap(x):
    return None if str(x).lower() in ("none", "off", "inf") else float(x)


def _fmt_set(s):
    q = "off" if s["q"] is None else f"{s['q']:g}"
    t = "-" if s["t"] is None else f"{s['t']:.2f}"
    cap = "none" if s["cap"] is None else f"{s['cap'] / 1e6:g}M"
    return f"F5 q {q:>4s} t {t:>4s} | stage <= {s['stage']} | cap {cap:>5s}"


def parse_setting(txt):
    q, t, s, c = (txt.split(",") + ["5", "none"])[:4]
    q = None if q.lower() == "off" else float(q)
    assert q is None or any(abs(q - x) < 1e-9 for x in FZ_Q), f"q must be one of FZ_Q {FZ_Q} (or off)"
    return dict(q=q, t=None if q is None else float(t), stage=int(s), cap=_cap(c))


def apply(S, s):
    """right, std cost, crit_par of a setting dict (q, t, stage, cap)."""
    if s["q"] is None:
        return S.evaluate(scut=s["stage"], cap=s["cap"])
    c = int(np.argmin(np.abs(np.array(FZ_Q) - s["q"])))
    _, SdC, SpC = next(S.savings(c, [s["t"]]))
    return S.evaluate(SdC, SpC, S.accpsn[:, c] > s["t"], s["stage"], s["cap"])


def tune(S, ts, stages, caps, rel):
    """Grid search on the calibration set: every setting's errors per point, pooled mean / p99."""
    recs = []

    def rec(q, t, scut, cap, right, cd):
        err, mu, p99, _ = S.stats(right, cd)
        recs.append(dict(q=q, t=t, stage=scut, cap=cap, err=err.tolist(), err_tot=int(err.sum()), mean=mu, p99=p99))

    for scut in stages:
        for cap in caps:
            r_, cd, _ = S.evaluate(scut=scut, cap=cap)
            rec(None, None, scut, cap, r_, cd)
    base = S.stats(*S.evaluate()[:2])[0]                                 # no stops, no cut, no cap
    for c, q in enumerate(FZ_Q):
        for t, SdC, SpC in S.savings(c, ts):
            sa = S.accpsn[:, c] > t
            for scut in stages:
                for cap in caps:
                    r_, cd, _ = S.evaluate(SdC, SpC, sa, scut, cap)
                    rec(q, float(t), scut, cap, r_, cd)
    allow = np.floor(rel * base + 1e-9)
    for x in recs:
        x["extra"] = (np.array(x["err"]) - base).tolist()
        x["ok"] = bool((np.array(x["err"]) - base <= allow).all())
    return recs, base, allow


def pareto(recs):
    front, best = [], np.inf
    for x in sorted(recs, key=lambda x: (x["mean"], x["err_tot"])):
        if x["err_tot"] < best:
            front.append(x)
            best = x["err_tot"]
    return front


def psn_diag(S):
    """psn_min of the accepted right decodes per checkpoint: t below their low quantiles loses packets."""
    m = S.right0
    out = {}
    for c, q in enumerate(FZ_Q):
        v = S.accpsn[m, c]
        v = v[np.isfinite(v)]
        out[f"{q:g}"] = [float(x) for x in np.percentile(v, [0, 0.5, 1, 5, 50])] if len(v) else []
    return out


def validate(T, s):
    """Test set: no stops vs the setting s on the same packets, without a cap and with each point's run cap."""
    rows = []
    r0, c0, _ = T.evaluate()
    r1, c1, _ = apply(T, s)
    for k, (part, esn0) in enumerate(T.pt_key):
        pa = T.pt_part[k]
        m = T.pt == k
        capr = pa["cap_log"]
        rc0, cc0, _ = T.evaluate(cap=capr) if capr else (r0, c0, None)
        s2 = dict(s, cap=min(x for x in (s["cap"], capr) if x is not None) if (s["cap"] or capr) else None)
        rc1, cc1, _ = apply(T, s2) if capr else (r1, c1, None)
        jp = None
        if pa["doc"] is not None:
            jp = next((p for p in pa["doc"]["points"] if abs(p["esn0"] - esn0) < 1e-6), None)
        n = int(m.sum())
        row = dict(part=part, esn0=esn0, frames_dump=n, err_nostop=int((~r0[m]).sum()),
                   err_stop=int((~r1[m]).sum()), lost=int((r0[m] & ~r1[m]).sum()), gained=int((~r0[m] & r1[m]).sum()),
                   mean_nostop=float(c0[m].mean()), p99_nostop=float(np.percentile(c0[m], 99)),
                   mean_stop=float(c1[m].mean()), p99_stop=float(np.percentile(c1[m], 99)),
                   max_nostop=float(c0[m].max()), max_stop=float(c1[m].max()), run_cap=capr,
                   err_log=int((~T.right_log[m]).sum()))
        if capr:
            row.update(err_nostop_cap=int((~rc0[m]).sum()), err_stop_cap=int((~rc1[m]).sum()),
                       lost_cap=int((rc0[m] & ~rc1[m]).sum()), mean_nostop_cap=float(cc0[m].mean()),
                       mean_stop_cap=float(cc1[m].mean()), p99_stop_cap=float(np.percentile(cc1[m], 99)))
        if jp is not None:
            row.update(json_frames=int(jp["frames"]), json_err=int(jp["frame_err"]),
                       json_cap_hit=int(jp.get("cap_hit", 0) or 0), json_cap_hit_right=int(jp.get("cap_hit_right", 0)
                                                                                         or 0))
            row["json_err_nocap"] = row["json_err"] - row["json_cap_hit_right"]
            row["json_bler"] = row["json_err"] / max(row["json_frames"], 1)
            row["json_bler_nocap"] = row["json_err_nocap"] / max(row["json_frames"], 1)
            row["dump_complete"] = row["json_frames"] == n
        rows.append(row)
    return rows


def _pr_val(rows, s):
    print(f"\nVALIDATION (test parts, paired packets) | setting {_fmt_set(s)}")
    print(f"{'part':>14s} {'Es/N0':>6s} {'n':>6s} | {'err0':>5s} {'err':>5s} {'lost':>4s} {'BLER0':>9s} {'BLER':>9s} | "
          f"{'mean0':>7s} {'mean':>7s} {'p99_0':>7s} {'p99':>7s} [M/core]")
    for x in rows:
        n = x["frames_dump"]
        print(f"{x['part']:>14s} {x['esn0']:+6.2f} {n:6d} | {x['err_nostop']:5d} {x['err_stop']:5d} {x['lost']:4d} "
              f"{x['err_nostop'] / n:9.3e} {x['err_stop'] / n:9.3e} | {x['mean_nostop'] / 1e6:7.3f} "
              f"{x['mean_stop'] / 1e6:7.3f} {x['p99_nostop'] / 1e6:7.3f} {x['p99_stop'] / 1e6:7.3f}")
    if any(x["run_cap"] for x in rows) or any("json_err" in x for x in rows):
        print(f"\nCAP EFFECT (the runs' own --cap-core; JSON: no-cap errors = frame_err - cap_hit_right)")
        print(f"{'part':>14s} {'Es/N0':>6s} {'cap':>5s} | {'JSON n':>7s} {'err':>5s} {'hitR':>4s} {'err_nc':>6s} "
              f"{'BLER':>9s} {'BLER_nc':>9s} | dump: {'err_cap':>7s} {'err_nc':>6s} {'stop+cap':>8s} {'lost':>4s} "
              f"{'mean':>7s}")
        for x in rows:
            cap = f"{x['run_cap'] / 1e6:g}M" if x["run_cap"] else "none"
            js = (f"{x['json_frames']:7d} {x['json_err']:5d} {x['json_cap_hit_right']:4d} {x['json_err_nocap']:6d} "
                  f"{x['json_bler']:9.3e} {x['json_bler_nocap']:9.3e}" if "json_err" in x else f"{'(no JSON)':>45s}")
            dc = (f"{x['err_nostop_cap']:7d} {x['err_nostop']:6d} {x['err_stop_cap']:8d} {x['lost_cap']:4d} "
                  f"{x['mean_stop_cap'] / 1e6:7.3f}" if x["run_cap"] else
                  f"{x['err_nostop']:7d} {x['err_nostop']:6d} {x['err_stop']:8d} {x['lost']:4d} "
                  f"{x['mean_stop'] / 1e6:7.3f}")
            inc = "" if x.get("dump_complete", True) else "  (dump holds fewer chunks than the JSON)"
            print(f"{x['part']:>14s} {x['esn0']:+6.2f} {cap:>5s} | {js} | {dc}{inc}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calib", nargs="*", default=[], help="calibration parts (run_blind_fs --calib --dump)")
    ap.add_argument("--test", nargs="*", default=[], help="test parts (validation, paired)")
    ap.add_argument("--name", required=True, help="fullsys/results/tune_<name>.json")
    ap.add_argument("--out", default=None, help="output path instead of fullsys/results/tune_<name>.json")
    ap.add_argument("--setting", default=None, help="q,t[,stage[,cap]] (q off = no F5): skip the tuning")
    ap.add_argument("--frozen", default=None, help=".npy (N,) bool frozen set: exact fz_share (default pos / N)")
    ap.add_argument("--rel", type=float, default=0.02, help="allowed extra errors / no-stop errors per point")
    ap.add_argument("--t-grid", nargs=3, type=float, default=T_GRID, metavar=("LO", "HI", "STEP"))
    ap.add_argument("--stages", nargs="+", type=int, default=STAGES)
    ap.add_argument("--caps", nargs="+", default=CAPS, help="MACs per core on crit_par ('none' = no cap)")
    ap.add_argument("--front", type=int, default=25, help="Pareto points printed (the low-error end)")
    args = ap.parse_args()
    assert args.calib or (args.test and args.setting), "give --calib (tuning) or --test with --setting"
    out = args.out or os.path.join(RESULTS, f"tune_{args.name}.json")
    assert not os.path.exists(out), f"{out} exists: use a new --name"
    t0 = time.time()
    frozen = np.load(args.frozen).astype(bool) if args.frozen else None
    fb = next((d for d in (_json(p) for p in args.calib + args.test) if d is not None), None)
    load = lambda ps: [load_part(p, frozen, fb) for p in ps]
    C, Tp = load(args.calib), load(args.test)
    for pa in C + Tp:
        for w in pa["warn"]:
            print("WARNING", pa["part"], w)
        if pa["doc"] is None:
            print(f"WARNING {pa['part']}: no JSON, meta from another part (cap / JSON counts unknown)")
        if pa["doc"] is not None and pa["meta"]["args"].get("fzstop", "off") != "off":
            print(f"WARNING {pa['part']}: run with fzstop {pa['meta']['args']['fzstop']} (replay assumes stops off)")
    for pa in C:
        if not pa["meta"].get("calib"):
            print(f"WARNING {pa['part']}: not a --calib run (seeds may overlap the test parts)")
        if pa["cap_log"]:
            print(f"WARNING {pa['part']}: calibration run with --cap-core {pa['cap_log']:g} (undone in the replay)")
    stds = {pa["std"] for pa in C + Tp}
    assert len(stds) == 1, f"parts mix MAC models {stds}"
    std = stds.pop()
    print(f"loaded {len(C)} calibration / {len(Tp)} test parts in {time.time() - t0:.1f} s | MACs per core = {std} | "
          f"stopped-decode share: {(C + Tp)[0]['share']}")
    res = dict(meta=dict(args=vars(args), std_core=std, share=(C + Tp)[0]["share"], fz_q=FZ_Q, tag_stage=TAG_STAGE,
                         approx=["F5: a right packet is lost if its accepted right decode stops (no CA-retry / later "
                                 "rescue), charged max(own, mean failed-search cost of the point)",
                                 "stopped decode: (1 - share) of the tree + the remaining sorts back, d4a once per "
                                 "all-stopped 4-decode round; share = pos/N unless --frozen (conservative)",
                                 "stage cut: crit_par scaled by the std ratio (cap check only)",
                                 "not replayable: spec11, checkpoint kept fraction, rho threshold"]))
    chosen = parse_setting(args.setting) if args.setting else None
    if C:
        S = Set(C)
        ts = np.round(np.arange(args.t_grid[1], args.t_grid[0] - 1e-9, -args.t_grid[2]), 6)
        caps = [_cap(c) for c in args.caps]
        t1 = time.time()
        recs, base, allow = tune(S, ts, args.stages, caps, args.rel)
        print(f"grid: {len(recs)} settings on {S.n} calibration packets, {S.npt} points ({time.time() - t1:.1f} s)")
        print("\nCALIBRATION points (no stops, no cut, no cap):")
        b0 = S.stats(*S.evaluate()[:2])
        for k, (part, esn0) in enumerate(S.pt_key):
            print(f"  {part:>14s} {esn0:+6.2f} dB: n {S.frames[k]:6d}  err {base[k]:5d}  BLER {base[k] / S.frames[k]:9.3e}"
                  f"  allowed extra {int(allow[k])}  mean {b0[3][k] / 1e6:7.3f} M/core")
        print(f"  pooled mean {b0[1] / 1e6:.3f}  p99 {b0[2] / 1e6:.3f} M/core")
        dg = psn_diag(S)
        print("\npsn_min of the accepted right decodes (min, 0.5 %, 1 %, 5 %, median) per q:")
        for q, v in dg.items():
            print(f"  q {q:>4s}: " + " ".join(f"{x:6.3f}" for x in v))
        front = pareto(recs)
        print(f"\nPARETO front, its low-error end ({len(front)} points; total errors vs pooled mean MACs per core; "
              f"no-stop total {int(base.sum())}; * = within --rel at every point):")
        print(f"  {'setting':48s} {'err':>5s} {'extra/pt':>14s} {'mean':>7s} {'p99':>7s} ok")
        for x in front[-args.front:]:
            print(f"  {_fmt_set(x):48s} {x['err_tot']:5d} {str(x['extra']):>14s} {x['mean'] / 1e6:7.3f} "
                  f"{x['p99'] / 1e6:7.3f} {'*' if x['ok'] else ''}")
        ok = [x for x in recs if x["ok"]]
        fam = {"F5 only": lambda x: x["q"] is not None and x["stage"] == 5 and x["cap"] is None,
               "stage cut only": lambda x: x["q"] is None and x["cap"] is None,
               "cap only": lambda x: x["q"] is None and x["stage"] == 5,
               "any": lambda x: True}
        best = {}
        print(f"\nCHEAPEST setting with extra errors <= floor({args.rel:g} x no-stop errors) at every point:")
        for nm, f in fam.items():
            cand = sorted([x for x in ok if f(x)], key=lambda x: (x["mean"], x["err_tot"], -(x["t"] or 9)))
            if cand:
                best[nm] = cand[0]
                x = cand[0]
                print(f"  {nm:15s} {_fmt_set(x):48s} err {x['err_tot']:5d} extra {x['extra']} mean "
                      f"{x['mean'] / 1e6:7.3f} (no-stop {b0[1] / 1e6:.3f}) p99 {x['p99'] / 1e6:7.3f} M/core")
        if chosen is None:
            chosen = {k: best["any"][k] for k in ("q", "t", "stage", "cap")}
        res["calib"] = dict(parts=[pa["part"] for pa in C], points=[list(k) for k in S.pt_key],
                            frames=S.frames.tolist(), err_base=base.tolist(), allowed=allow.tolist(),
                            mean_base=b0[1], p99_base=b0[2], psn_acc_right=dg, n_settings=len(recs),
                            front=front, best=best,
                            feasible_top=sorted(ok, key=lambda x: (x["mean"], x["err_tot"]))[:50])
    res["chosen"] = chosen
    print(f"\nCHOSEN: {_fmt_set(chosen)}")
    if Tp:
        T = Set(Tp)
        rows = validate(T, chosen)
        _pr_val(rows, chosen)
        res["test"] = rows
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    print(f"\nwrote {out} ({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
