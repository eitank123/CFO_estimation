"""BLIND_IMPLEMENTATION/testing/: F5 offline analysis (results/expected_f3f5.md): the frozen-bit abort "stop a CA-SCL
decode at checkpoint c when ALL alive paths have metric > t" on the fz_diag dumps (read-only, no simulation).

    py fz_analyze.py            # tables to stdout, results/fz_f5.json (plots: plot_fz.py)

Labels. Right rows = out 0. The DELIVERED decode of a right packet = its out-0 row(s) (f or j) of the latest call that
has an out-0 row (later calls of the same packet are only the CA retries of the same batch); the packet is lost when
every one of them is stopped. A stopped decode = a CRC failure, so every other row's flow is unchanged (the CA retry
takes its CFO from the SC pass, not from the list; the retry gate is off; no pns rows in these dumps). Wrong rows =
out 1 or 2 (wrong cell, or failed true-cell decodes). Thresholds: t = the (k+1)-th largest delivered-packet score
(score = min over the packet's delivered rows of the abort statistic min_paths metric) -> k lost packets
(k = 0, floor(1e-4 n), floor(1e-3 n)), in-sample; cross-check: threshold from part a applied to part b and back.
Saving: fz_profile.saved per stopped non-delivered row at the checkpoint's leaf position rounded UP to the next leaf /
rate-0 node end (total); per core the d4a rounds (rnd): a round's critical path shortens by the min of its rows' crit
savings (0 unless every row of the round stops). Denominators: the parts' JSON mean total MACs and the standard per
core (crit_par_h_d4a at 1/10, 0.15; crit_par_d4a at 2/5, 1/2).
"""
import json
import os
import sys

import numpy as np
from scipy.stats import beta, rankdata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fz_load import load, ROOT  # noqa: E402
from fz_profile import saved, profile  # noqa: E402

FZ_Q = (0.25, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
METRICS = {"psn": "pos_s", "pn": "pos", "pl": "pos"}       # metric -> its checkpoint leaf positions
POINTS = [  # name, parts, rate key, SNR, per-core (standard) field of the JSON parts
    ("0.15 -4 dB", ["t-fz1a", "t-fz1b"], "0.15", -4.0, "crit_par_h_d4a_macs"),
    ("2/5 0.5 dB", ["t-fz2a", "t-fz2b"], "2/5", 0.5, "crit_par_d4a_macs"),
    ("1/10 -5 dB", ["t-fz3a"], "1/10", -5.0, "crit_par_h_d4a_macs"),
    ("1/2 2 dB", ["t-fz3b"], "1/2", 2.0, "crit_par_d4a_macs"),
]
RES = os.path.join(HERE, "results")


def ub95(k, n):
    """One-sided 95 % upper bound of a rate with k events in n (Clopper-Pearson; k = 0 -> ~3 / n)."""
    return float(beta.ppf(0.95, k + 1, n - k)) if k < n else 1.0


def auc(x_pos, x_neg):
    """P(score of an x_pos row > score of an x_neg row) (ties 1/2); called (wrong, right)."""
    x = np.concatenate([x_neg, x_pos])
    r = rankdata(x)
    n1, n0 = len(x_pos), len(x_neg)
    return float((r[n0:].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def cost_pos(rate, pos):
    """Leaf position a stop at checkpoint pos is costed at: the first leaf / rate-0 node END >= pos (a pn / pl
    checkpoint inside a rate-0 node is reached once that node is processed; fz_profile.share rounds down)."""
    P = profile(rate)["pos"]
    return int(P[np.searchsorted(P, pos, side="left")])


def json_den(parts, field):
    tot = cp = fr = 0.0
    for p in parts:
        d = json.load(open(os.path.join(ROOT, "small_cfo", "blind", "results", f"blind_ber_{p}.json")))
        for x in d:
            if x["rx"].startswith("T "):
                tot += x["macs"]
                cp += x[field]
                fr += x["frames"]
    return tot / fr, cp / fr, int(fr)


def delivered(F, J, G):
    """Boolean arrays for F and J rows: the delivered decode(s) of each right packet (module doc)."""
    groups = [D for D in (F, J) if D is not None]
    mc = {}
    for D in groups:
        r0 = np.where(D["out"] == 0)[0]
        for u, c in zip(D["uid"][r0].tolist(), D["call"][r0].tolist()):
            mc[u] = max(mc.get(u, -1), c)
    right = set(G["uid"][G["right"]].tolist())
    res = []
    for D in (F, J):
        if D is None:
            res.append(None)
            continue
        dl = np.array([o == 0 and u in right and mc[u] == c for u, c, o in
                       zip(D["uid"].tolist(), D["call"].tolist(), D["out"].tolist())], bool)
        res.append(dl)
    return res


class Group:
    """One row group (f: CA-SCL-8, j: joint list) of a point with its labels, rounds and packet index."""

    def __init__(self, D, dl, rate, L, npk, mtot, mcp):
        self.D, self.dl, self.rate, self.L = D, dl, rate, L
        self.npk, self.mtot, self.mcp = npk, mtot, mcp
        self.wrong = D["out"] != 0
        self.right = D["out"] == 0
        self.wc = self.wrong & ~D["true_cell"]
        _, self.rinv = np.unique(D["uid"].astype(np.int64) * 4096 + D["rnd"].astype(np.int64), return_inverse=True)
        self.rsize = np.bincount(self.rinv)
        du, self.dinv = np.unique(D["uid"][dl], return_inverse=True)
        self.n = len(du)

    def scores(self, x):
        """Per delivered packet: min over its delivered rows of x (NaN -> -inf: never stopped)."""
        s = np.full(self.n, np.inf)
        np.minimum.at(s, self.dinv, np.nan_to_num(x[self.dl], nan=-np.inf))
        return s

    def evaluate(self, stop, pos_row):
        """stop (rows,) bool, pos_row (rows,) cost position of each row's stop -> lost packets, fractions, savings."""
        lost = int(self.n - np.bincount(self.dinv, weights=(~stop[self.dl]).astype(float),
                                        minlength=self.n).astype(bool).sum())
        tot, crit = saved(self.rate, pos_row, L=self.L)
        use = stop & ~self.dl
        tot, crit = np.where(use, tot, 0.0), np.where(use, crit, 0.0)
        mn = np.full(len(self.rsize), np.inf)
        np.minimum.at(mn, self.rinv, crit)
        return dict(lost=lost, n=self.n, ub95=ub95(lost, self.n), right_rows_stopped=int((stop & self.right).sum()),
                    wrong_stopped=float((stop & self.wrong).sum() / max(1, self.wrong.sum())),
                    wrong_cell_stopped=float((stop & self.wc).sum() / max(1, self.wc.sum())),
                    tc_fail_stopped=float((stop & self.wrong & self.D["true_cell"]).sum()
                                          / max(1, (self.wrong & self.D["true_cell"]).sum())),
                    save_tot=float(tot.sum()) / self.npk / self.mtot, save_core=float(mn.sum()) / self.npk / self.mcp,
                    save_tot_abs=float(tot.sum()) / self.npk, save_core_abs=float(mn.sum()) / self.npk)


def stop_single(x, t):
    return np.nan_to_num(x, nan=-np.inf) > t


def stop_union(X, ts, cpos):
    """Stop at the first checkpoint c with x_c > t_c -> (stop, cost position per row)."""
    first = np.full(X.shape[0], -1)
    for c in range(len(ts) - 1, -1, -1):
        first = np.where(np.nan_to_num(X[:, c], nan=-np.inf) > ts[c], c, first)
    stop = first >= 0
    return stop, np.where(stop, np.asarray(cpos)[np.maximum(first, 0)], 2048)


def load_point(parts, rate, cpf):
    F, J, G = load(parts)
    mtot, mcp, nfr = json_den(parts, cpf)
    assert nfr == len(G["uid"]), (nfr, len(G["uid"]))
    dF, dJ = delivered(F, J, G)
    out = {}
    for grp, D, dl, L in (("f", F, dF, 8), ("j", J, dJ, 16)):
        if D is not None:
            out[grp] = Group(D, dl, rate, L, len(G["uid"]), mtot, mcp)
    return out, G, mtot, mcp


def analyse(name, parts, rate, snr, cpf):
    gs, G, mtot, mcp = load_point(parts, rate, cpf)
    npk = len(G["uid"])
    res = dict(point=name, rate=rate, snr=snr, parts=parts, packets=npk, right_packets=int(G["right"].sum()),
               bler=float(1 - G["right"].mean()), macs_total=mtot, macs_core=mcp, groups={})
    for grp, g in gs.items():
        D = g.D
        full = saved(rate, 0, L=g.L)
        gres = dict(rows=len(D["uid"]), right_rows=int(g.right.sum()), wrong_rows=int(g.wrong.sum()),
                    wrong_cell_rows=int(g.wc.sum()), delivered_rows=int(g.dl.sum()), delivered_packets=g.n,
                    decode_share_tot=float(len(D["uid"]) * full[0] / npk / mtot),
                    nb=D["nb"][0].tolist(), nb_s=D["nb_s"][0].tolist(), pos=D["pos"][0].tolist(),
                    pos_s=D["pos_s"][0].tolist(), cnt=D["cnt"][0].tolist(), cnt_s=D["cnt_s"][0].tolist(),
                    full_tot=float(full[0]), full_crit=float(full[1]), m={})
        for m, pk in METRICS.items():
            X = D[m + "_min"].astype(float)
            cpos = [cost_pos(rate, int(v)) for v in D[pk][0]]
            rows = []
            for c in range(len(FZ_Q)):
                x = X[:, c]
                ok = np.isfinite(x)
                a = auc(x[ok & g.wrong], x[ok & g.right])
                a_wc = auc(x[ok & g.wc], x[ok & g.right]) if (ok & g.wc).any() else float("nan")
                s = np.sort(g.scores(x))[::-1]
                prow = np.full(len(x), cpos[c])
                ths = []
                for lab, k in (("0", 0), ("1e-4", int(np.floor(1e-4 * g.n))), ("1e-3", int(np.floor(1e-3 * g.n)))):
                    t = float(s[k]) if k < len(s) else -np.inf
                    ths.append(dict(target=lab, t=t, **g.evaluate(stop_single(x, t), prow)))
                ks = np.unique(np.r_[np.arange(0, min(len(s), 40)),
                                     np.geomspace(1, max(2, len(s) - 1), 60).astype(int)])
                curve = []
                for k in ks:
                    t = float(s[k]) if k < len(s) else -np.inf
                    e = g.evaluate(stop_single(x, t), prow)
                    curve.append((e["lost"], e["wrong_stopped"], e["save_tot"], e["save_core"]))
                rows.append(dict(q=FZ_Q[c], pos=int(D[pk][0, c]), cost_pos=cpos[c], nb=int(D["nb" + pk[3:]][0, c]),
                                 auc=a, auc_wrong_cell=a_wc, med_right=float(np.nanmedian(x[g.right])),
                                 med_wrong=float(np.nanmedian(x[g.wrong])), th=ths, curve=curve))
            ts = [r["th"][0]["t"] for r in rows]
            stop, prow = stop_union(X, ts, cpos)
            gres["m"][m] = dict(ck=rows, union0=g.evaluate(stop, prow))
        res["groups"][grp] = gres
    if len(parts) == 2:
        res["cv"] = crossval(parts, rate, cpf)
    return res


def crossval(parts, rate, cpf):
    """0-loss thresholds of one part applied to the other (f rows): lost, ub95, W, savings; single checkpoints and
    the union of the 7 checkpoints."""
    P = [load_point([p], rate, cpf)[0]["f"] for p in parts]
    out = {}
    for m, pk in METRICS.items():
        rr = {}
        for i, (tr, te) in enumerate(((P[0], P[1]), (P[1], P[0]))):
            Xtr, Xte = tr.D[m + "_min"].astype(float), te.D[m + "_min"].astype(float)
            cpos = [cost_pos(rate, int(v)) for v in te.D[pk][0]]
            ts = [float(tr.scores(Xtr[:, c]).max()) for c in range(len(FZ_Q))]
            for c in range(len(FZ_Q)):
                e = te.evaluate(stop_single(Xte[:, c], ts[c]), np.full(Xte.shape[0], cpos[c]))
                rr.setdefault(str(FZ_Q[c]), []).append(e)
            stop, prow = stop_union(Xte, ts, cpos)
            rr.setdefault("union", []).append(te.evaluate(stop, prow))
        out[m] = {k: dict(lost=sum(e["lost"] for e in v), n=sum(e["n"] for e in v),
                          ub95=ub95(sum(e["lost"] for e in v), sum(e["n"] for e in v)),
                          wrong_stopped=float(np.mean([e["wrong_stopped"] for e in v])),
                          save_tot=float(np.mean([e["save_tot"] for e in v])),
                          save_core=float(np.mean([e["save_core"] for e in v]))) for k, v in rr.items()}
    return out


def main():
    allres = [analyse(*p) for p in POINTS]
    with open(os.path.join(RES, "fz_f5.json"), "w") as f:
        json.dump(allres, f, indent=1)
    for r in allres:
        print(f"\n=== {r['point']}: {r['packets']} packets, BLER {r['bler']:.2e} ({r['packets'] - r['right_packets']}), "
              f"MACs total {r['macs_total']:.4g}, per core {r['macs_core']:.4g}")
        for grp, g in r["groups"].items():
            print(f" [{grp}] rows {g['rows']} right {g['right_rows']} wrong {g['wrong_rows']} (wrong cell "
                  f"{g['wrong_cell_rows']}) delivered rows {g['delivered_rows']} / packets {g['delivered_packets']}; "
                  f"decodes = {100 * g['decode_share_tot']:.1f} % of total MACs; full decode {g['full_tot']:.4g} / "
                  f"crit {g['full_crit']:.4g}")
            print("   nb", g["nb"], "pos", g["pos"], "| nb_s", g["nb_s"], "pos_s", g["pos_s"])
            for m, mm in g["m"].items():
                print(f"  metric {m}")
                for row in mm["ck"]:
                    s = f"   q {row['q']:.2f} pos {row['pos']:4d}->{row['cost_pos']:4d} nb {row['nb']:3d} AUC " \
                        f"{row['auc']:.4f} (wc {row['auc_wrong_cell']:.4f}) med R/W {row['med_right']:.3f}/" \
                        f"{row['med_wrong']:.3f} |"
                    for th in row["th"]:
                        s += (f" [{th['target']}: lost {th['lost']}/{th['n']} (rows {th['right_rows_stopped']}) "
                              f"ub {th['ub95']:.1e} W {th['wrong_stopped']:.3f} tot {100 * th['save_tot']:.2f}% "
                              f"core {100 * th['save_core']:.2f}%]")
                    print(s)
                u = mm["union0"]
                print(f"   union of 0-loss thresholds: lost {u['lost']}/{u['n']} ub {u['ub95']:.1e} W "
                      f"{u['wrong_stopped']:.3f} tot {100 * u['save_tot']:.2f}% core {100 * u['save_core']:.2f}%")
        if "cv" in r:
            print(" cross-validation (0-loss threshold of one part on the other, f rows, pooled):")
            for m, mm in r["cv"].items():
                print("  ", m, " ".join(f"{k}: lost {v['lost']}/{v['n']} W {v['wrong_stopped']:.3f} tot "
                                         f"{100 * v['save_tot']:.2f}% core {100 * v['save_core']:.2f}% |"
                                         for k, v in mm.items()))


if __name__ == "__main__":
    main()
