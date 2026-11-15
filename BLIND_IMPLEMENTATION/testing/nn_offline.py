"""BLIND_IMPLEMENTATION/testing/: offline stage of the decode-feedback NN plan (results/plan_nn_feedback.md).

    py BLIND_IMPLEMENTATION/testing/nn_offline.py [--quick]

Reads the decode dumps (small_rx.py dec_dump: d_* one row per decode attempt, p_* one row per packet) in
small_cfo/blind/dumps/{t-deca, t-decb25, t-decb2, t-decbn} and writes
    results/nn_offline.json           every number of the report (tables P0..P3)
    results/plots/nn_auc_head{A,B,C}.png, results/plots/nn_pm_vs_rho.png
No receiver simulation: only numpy / sklearn fits on the logged rows.

Labels (truth only in the labels, never in the features):
    A  failed main decode (not retry, not accepted): |f_err| <= 0.5 STEP (d_in_cell)
    B  CA retry row (features of its parent main decode): the retry was accepted (all accepted retries are right)
    C  failed main decode: some failed main decode of the packet so far (this one included) had |f_err| <= 0.5 STEP
    D  failed main decode: the frame is noise only (t-decbn) vs a 0.15 signal packet (-4 / -3 dB)
    A2 / C2 the same with |f_err| <= 2 STEP (sensitivity)
Train / test split by chunk: per point the chunks sorted by chunk seed, the last 2 of 8 (25 %) are the test set.

Cost model (MACs per core = crit_par, the standard 32-core model; small_rx._dec_cost and the CA retry):
    main decode   decode / 8 + llr / 32 + K * 10                 (K = A + 16 CRC bits)
    CA retry      m_met (sequential SC metric) + (llr + CA_MACS(2)) / 32 + one main decode
Replay (approximate): a packet's logged trajectory is cut / edited by the gate; rem_after(r) = the packet's final
crit_par - the cost before row r's decode call - the decodes (and retries) of that call up to r. A refinement
fired by head A or C costs C_REF = 2 main decodes and is assumed to SUCCEED when the label is true and the packet
was decoded right in the log (an optimistic assumption); a C stop at a false row loses the packet (if it was right);
a skipped successful retry is counted as a lost packet (conservative: the search might have found it later).
"""
import glob
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
DUMPS = os.path.join(ROOT, "small_cfo", "blind", "dumps")
RES = os.path.join(ROOT, "small_cfo", "blind", "results")
OUT = os.path.join(HERE, "results")
PLOTS = os.path.join(OUT, "plots")

POINTS = [  # name, code rate key, SNR, part, glob
    ("1/10 -5", "1/10", -5.0, "t-deca", "*R1_10_-5.0_*"),
    ("0.15 -4", "0.15", -4.0, "t-deca", "*R0.15_-4.0_*"),
    ("0.15 -3", "0.15", -3.0, "t-deca", "*R0.15_-3.0_*"),
    ("2/5 0.5", "2/5", 0.5, "t-decb25", "*"),
    ("1/2 2", "1/2", 2.0, "t-decb2", "*"),
]
NOISE = ("0.15 -1 noise", "0.15", -1.0, "t-decbn", "*_noise.npz")
MODELS = {"logistic": None, "MLP 1x32": (32,), "MLP 2x32": (32, 32), "MLP 2x64": (64, 64)}
NN_MACS = {"logistic": 50, "MLP 1x32": 1000, "MLP 2x32": 2000, "MLP 2x64": 6000}
FSETS = ["F0", "F0+F1", "F0+F2", "F0+F1+F2", "F0+F1+F2+F3"]
TRAIN_CAP = 20000          # training rows per fit (subsample; all positives kept up to half of it)
QUICK = "--quick" in sys.argv


def measured_dec(D):
    """Per-core cost of one main decode as logged: (retry rows' cpar0 - their call's cpar0) / main rows of the call."""
    r = np.where(D["retry"])[0]
    if not len(r):
        return None
    pr = D["par_row"][r]
    c0, c1 = D["cpar0"][pr].astype(np.float64), D["cpar0"][r].astype(np.float64)
    key = D["gid"] * 1e12 + D["cpar0"].astype(np.float64)
    m = ~D["retry"]
    u, cnt = np.unique(key[m], return_counts=True)
    n = cnt[np.searchsorted(u, key[pr])]
    return float(np.median((c1 - c0) / n))


def costs(rate):
    import blind_cfo as bc
    import blind_fast as bf
    import blind_vp as vp
    K = bc.CODES[rate] + 16
    dec = vp.MAC["decode"] / 8 + vp.MAC["llr"] / 32 + K * 10
    ret = vp.metric_macs(bc.CODES[rate]) + (vp.MAC["llr"] + bf.CA_MACS(2)) / 32 + dec
    return dict(dec=float(dec), retry=float(ret), reenc_total=float(vp.MAC["reencode"]),
                reenc_core=float(vp.MAC["reencode"] / 32))


# ----------------------------------------------------------------------------------------------------------- load
DKEYS = ["pk", "att", "tag", "retry", "parent", "cell", "q", "off", "sub", "hrank", "m_hyp", "pm_cell", "z",
         "zrank", "z1", "z2", "ck", "paid", "n_alive", "n_tried", "cpar0", "rho_min", "acc", "f_err", "pm_list",
         "pm_crc", "crc", "syn_w", "n_agree", "agree_bits", "n_rem", "l_sum", "l_mean", "l_lt1", "sgn_agree",
         "rho_best", "rho_crc", "right", "in_cell"]
PKEYS = ["pkt", "f0_err", "y4_ratio", "y4_coh", "m_br0", "m_br1", "p_r", "snr_m2m4", "truth_f", "true_cell",
         "passed", "right", "n_dec", "first_cell", "cpar", "snr_rx", "stage"]


def load(part, pat, keep_rows=None, seed=0):
    """Concatenate a point's chunks (sorted by chunk seed). keep_rows(z) -> bool mask of the rows to keep."""
    fs = glob.glob(os.path.join(DUMPS, part, f"dec_*{pat}" if pat != "*" else "dec_*.npz"))
    fs = sorted(fs, key=lambda f: int(np.load(f)["chunk_seed"]))
    D, P, meta = {k: [] for k in DKEYS + ["chunk", "gid"]}, {k: [] for k in PKEYS + ["chunk", "gid"]}, []
    off = 0
    for c, f in enumerate(fs):
        z = np.load(f)
        npk = len(z["p_pkt"])
        m = keep_rows(z) if keep_rows is not None else slice(None)
        for k in DKEYS:
            D[k].append(z["d_" + k][m])
        n = len(D["pk"][-1])
        D["chunk"].append(np.full(n, c, np.int8))
        D["gid"].append(off + D["pk"][-1].astype(np.int64))
        for k in PKEYS:
            P[k].append(z["p_" + k])
        P["chunk"].append(np.full(npk, c, np.int8))
        P["gid"].append(off + np.arange(npk))
        meta.append(dict(file=os.path.basename(f), chunk_seed=int(z["chunk_seed"]), rows=int(len(z["d_pk"])),
                         packets=int(npk), rx=str(z["rx"]), rate=str(z["rate"]), snr=float(z["snr"])))
        off += npk
    D = {k: np.concatenate(v) for k, v in D.items()}
    P = {k: np.concatenate(v) for k, v in P.items()}
    return D, P, meta


def validate(part, meta):
    """Rows per chunk = decodes - joint decodes of the result part (a joint decode counts 2 CA-SCL-8 equivalents
    in 'decodes' and gives one dump row), packets = frames."""
    J = json.load(open(os.path.join(RES, f"blind_ber_{part}.json")))
    T = {(r["rate"], r["snr"], r["chunk_seed"]): r for r in J if r["rx"].startswith("T")}
    out = []
    for m in meta:
        r = T.get((m["rate"], m["snr"], m["chunk_seed"]))
        exp = None if r is None else r["decodes"] - r.get("joint_decodes", 0)
        out.append(dict(**m, json_decodes=None if r is None else r["decodes"],
                        joint=None if r is None else r.get("joint_decodes", 0),
                        rows_ok=r is not None and abs(m["rows"] - exp) < 0.5,
                        frames_ok=r is not None and r["frames"] == m["packets"],
                        cpar_json=None if r is None else r["crit_par_macs"] / r["frames"]))
    return out


# ------------------------------------------------------------------------------------------------------ features
def prep(D, P):
    """Derived per-row quantities: packet index, parent row of a retry, per-packet history, rem_after."""
    n = len(D["pk"])
    g = D["gid"]
    key = g * 65536 + D["att"].astype(np.int64)
    o = np.argsort(key, kind="stable")
    ks = key[o]
    par = np.full(n, -1)
    r = np.where(D["retry"])[0]
    pk_ = g[r] * 65536 + D["parent"][r].astype(np.int64)
    j = np.searchsorted(ks, pk_)
    assert (ks[np.minimum(j, n - 1)] == pk_).all(), "retry parent not found"
    par[r] = o[j]
    D["par_row"] = par
    pm = D["pm_list"].astype(np.float64)
    fin = np.isfinite(pm)
    pm0 = pm[:, 0]
    pmf = np.where(fin, pm, np.nan)
    D["pm0"] = pm0
    D["pm_gap"] = np.where(fin[:, 1], pm[:, 1] - pm0, 0.0)
    D["pm_spread"] = np.nanmax(pmf, 1) - pm0
    D["pm_meanex"] = np.nanmean(pmf, 1) - pm0
    D["pm_norm"] = pm0 / D["l_sum"]
    D["pmcrc_norm"] = D["pm_crc"] / D["l_sum"]
    D["f0_dist"] = np.abs(D["f_err"] - P["f0_err"][g])               # |f_hyp - f0| / STEP (truth cancels)
    # per-packet history in attempt order (main rows only)
    cm_pm = np.full(n, np.nan)
    cm_rho = np.full(n, np.nan)
    cumA = np.zeros(n, bool)
    cumA2 = np.zeros(n, bool)
    main_o = o[~D["retry"][o]]
    gm = g[main_o]
    starts = np.r_[0, np.where(np.diff(gm) != 0)[0] + 1]
    seg = np.repeat(np.arange(len(starts)), np.diff(np.r_[starts, len(gm)]))
    pmn = D["pm_norm"][main_o]
    rho = D["rho_best"][main_o].astype(np.float64)
    failA = (D["in_cell"] & ~D["acc"])[main_o]
    failA2 = ((np.abs(D["f_err"]) <= 2) & ~D["acc"])[main_o]
    # segmented cumulative min / max / or via a loop over segments with >1 row (fast enough)
    cpm, crh, cA, cA2 = pmn.copy(), rho.copy(), failA.copy(), failA2.copy()
    lens = np.diff(np.r_[starts, len(gm)])
    for s, L in zip(starts[lens > 1], lens[lens > 1]):
        sl = slice(s, s + L)
        cpm[sl] = np.minimum.accumulate(pmn[sl])
        crh[sl] = np.maximum.accumulate(rho[sl])
        cA[sl] = np.logical_or.accumulate(failA[sl])
        cA2[sl] = np.logical_or.accumulate(failA2[sl])
    cm_pm[main_o], cm_rho[main_o], cumA[main_o], cumA2[main_o] = cpm, crh, cA, cA2
    D["cum_pm"], D["cum_rho"], D["labC"], D["labC2"] = cm_pm, cm_rho, cumA, cumA2
    # rem_after for main rows: final cpar - cpar0 - the call's decodes up to this row (and their retries)
    has_ret = np.zeros(n, bool)
    has_ret[par[r]] = True
    D["has_ret"] = has_ret
    return D


def feats(D, P, rows, fset, rate_in=None, use_par=False, drop=()):
    """Feature matrix of the rows (use_par: the parent main row's features, for the retry gate)."""
    i = D["par_row"][rows] if use_par else rows
    g = D["gid"][i]
    cols = {}
    grid = D["cell"][i] >= 0
    if "F0" in fset:
        for k in ["z", "zrank", "ck", "n_alive", "n_tried", "paid", "hrank", "sub", "off", "q", "tag", "att"]:
            cols[k] = D[k][i].astype(np.float64)
        cols["zgap1"] = (D["z1"][i] - D["z"][i]).astype(np.float64)
        cols["zgap12"] = (D["z1"][i] - D["z2"][i]).astype(np.float64)
        cols["m_hyp"] = D["m_hyp"][i].astype(np.float64)
        cols["pm_cell"] = D["pm_cell"][i].astype(np.float64)
        cols["f0_dist"] = D["f0_dist"][i]
        cols["nogrid"] = (~grid).astype(np.float64)
    if "F1" in fset:
        for k in ["pm0", "pm_gap", "pm_spread", "pm_meanex", "syn_w", "n_rem", "n_agree", "agree_bits"]:
            cols[k] = D[k][i].astype(np.float64)
    if "F2" in fset:
        cols["rho_best"] = D["rho_best"][i].astype(np.float64)
        cols["rho_rel"] = (D["rho_best"][i] / D["rho_min"][i]).astype(np.float64)
        cols["sgn_agree"] = D["sgn_agree"][i].astype(np.float64)
        cols["cum_rho"] = D["cum_rho"][i]
    if "F3" in fset:
        for k in ["l_sum", "l_mean", "l_lt1", "pm_norm", "cum_pm"]:
            cols[k] = D[k][i].astype(np.float64)
        for k in ["y4_ratio", "y4_coh", "m_br0", "m_br1", "p_r", "snr_m2m4", "snr_rx"]:
            cols[k] = P[k][g].astype(np.float64)
        cols["snr_m2m4"] = np.clip(cols["snr_m2m4"], -30, 30)
        cols["m_br_d"] = cols["m_br0"] - cols["m_br1"]
    if rate_in is not None:
        cols["rate"] = rate_in[i] if np.ndim(rate_in) else np.full(len(i), rate_in)
    for k in drop:
        cols.pop(k, None)
    X = np.stack([cols[k] for k in cols], 1)
    X[~np.isfinite(X)] = np.nan
    return X, list(cols)


def fit_score(Xtr, ytr, Xall, model, seed=0):
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    rng = np.random.default_rng(seed)
    pos, neg = np.where(ytr)[0], np.where(~ytr)[0]
    if len(pos) + len(neg) > TRAIN_CAP:                       # subsample: positives up to half, negatives the rest
        pos = rng.choice(pos, min(len(pos), TRAIN_CAP // 2), replace=False)
        neg = rng.choice(neg, min(len(neg), TRAIN_CAP - len(pos)), replace=False)
    s = np.r_[pos, neg]
    if MODELS[model] is not None and 0 < len(pos) < 0.2 * len(s):   # MLP: positives replicated to >= 20 %
        s = np.r_[np.tile(pos, int(np.ceil(0.25 * len(neg) / len(pos)))), neg]
    X = Xtr[s]
    mu, sd = np.nanmean(X, 0), np.nanstd(X, 0) + 1e-9
    mu = np.where(np.isfinite(mu), mu, 0)

    def tr(A):
        Z = (A - mu) / sd
        return np.clip(np.nan_to_num(Z, nan=0.0), -20, 20)
    if MODELS[model] is None:
        clf = LogisticRegression(max_iter=1000, C=1.0)
    else:
        clf = MLPClassifier(MODELS[model], alpha=1e-3, max_iter=150, early_stopping=len(pos) >= 300,
                            n_iter_no_change=8, random_state=seed)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clf.fit(tr(X), ytr[s])
    return clf.predict_proba(tr(Xall))[:, 1], len(np.unique(s))


def auc(y, s):
    """AUC (ties half) and the Hanley-McNeil standard error."""
    y = np.asarray(y, bool)
    n1, n0 = int(y.sum()), int((~y).sum())
    if n1 == 0 or n0 == 0:
        return np.nan, np.nan, n1, n0
    from scipy.stats import rankdata
    r = rankdata(s)
    a = (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
    se = np.sqrt(max(a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n0 - 1) * (q2 - a * a), 0) / (n1 * n0))
    return float(a), float(se), n1, n0


def cp(k, n, a=0.05):
    from scipy.stats import beta
    if n == 0:
        return (np.nan, np.nan)
    lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
    return (float(lo), float(hi))


# --------------------------------------------------------------------------------------------------------- replay
def rem_after(D, P, C):
    """Per main row: the packet's crit_par after this row's decode (and its retry) within the logged trajectory."""
    n = len(D["pk"])
    out = np.zeros(n)
    m = ~D["retry"]
    idx = np.where(m)[0]
    key = D["gid"][idx] * 1e12 + D["cpar0"][idx].astype(np.float64)
    o = idx[np.lexsort((D["att"][idx], key))]
    g = D["gid"][o]
    c0 = D["cpar0"][o].astype(np.float64)
    same = np.r_[False, (g[1:] == g[:-1]) & (c0[1:] == c0[:-1])]
    # position within the call and the retries of the call's rows so far
    pos = np.zeros(len(o))
    nret = D["has_ret"][o].astype(float)
    cum_r = nret.copy()
    for t in range(1, len(o)):
        if same[t]:
            pos[t] = pos[t - 1] + 1
            cum_r[t] = cum_r[t - 1] + nret[t]
    out[o] = np.maximum(P["cpar"][g].astype(np.float64) - c0 - (pos + 1) * C["dec"] - cum_r * C["retry"], 0.0)
    return out


def replay(D, P, C, test_pk, sA=None, tA=None, sB=None, tB=None, sC=None, tC=None, labA="in_cell", labC="labC",
           nn_macs=0.0):
    """Approximate per-core MACs saved / packets lost on the test packets by gates A (refine), B (retry skip),
    C (grid stop) at thresholds t (fire when the score >= t for A, C; skip the retry when the score < t for B)."""
    C_REF = 2 * C["dec"]
    pk_test = np.where(test_pk)[0]
    npk = len(pk_test)
    tot = P["cpar"][pk_test].astype(np.float64).sum()
    fm = (~D["retry"]) & (~D["acc"]) & test_pk[D["gid"]]
    rows = np.where(fm)[0]
    rows = rows[np.lexsort((D["att"][rows], D["gid"][rows]))]
    g = D["gid"][rows]
    right = P["right"][g]
    rem = D["rem"][rows]
    fireA = np.zeros(len(rows), bool) if sA is None else sA[rows] >= tA
    fireC = np.zeros(len(rows), bool) if sC is None else sC[rows] >= tC
    LA = D[labA][rows] if labA != "in_cell2" else ((np.abs(D["f_err"][rows]) <= 2) & ~D["acc"][rows])
    LC = D[labC][rows]
    # per packet: the first row where A fires with a true label (success by refinement) or C fires (stop)
    starts = np.r_[0, np.where(np.diff(g) != 0)[0] + 1]
    ends = np.r_[starts[1:], len(g)]
    saved, lost, calls, extra = 0.0, 0, 0, 0.0
    cut = np.full(len(rows), False)                        # rows after the cut (no B decision for them)
    for s, e in zip(starts, ends):
        for t in range(s, e):
            calls += (sA is not None) + (sC is not None)
            if fireC[t]:
                if LC[t] and right[t]:
                    saved += rem[t] - C_REF
                else:
                    saved += rem[t]
                    lost += int(right[t])
                cut[t + 1:e] = True
                break
            if fireA[t]:
                if LA[t] and right[t]:
                    saved += rem[t] - C_REF
                    cut[t + 1:e] = True
                    break
                extra += C_REF
    nB = skipped = lostB = 0
    if sB is not None:
        rr = np.where(D["retry"] & test_pk[D["gid"]])[0]
        par = D["par_row"][rr]
        # retries of rows after a cut are already in rem_after
        cut_rows = set(rows[cut].tolist())
        keep = np.array([p_ not in cut_rows for p_ in par], bool) if len(cut_rows) else np.ones(len(rr), bool)
        rr = rr[keep]
        sk = sB[rr] < tB
        nB, skipped = len(rr), int(sk.sum())
        lostB = int((sk & D["acc"][rr]).sum())
        saved += skipped * C["retry"]
        calls += len(rr)
    net = saved - extra - calls * nn_macs
    return dict(saved_per_pk=net / npk, saved_pct=100 * net / tot, lost=lost + lostB, lost_C=lost, lost_B=lostB,
                packets=npk, cpar_mean=tot / npk, retries=nB, skipped=skipped, refine_waste=extra / npk)


def thr_for_loss(scores_pos, frac):
    """Highest threshold that keeps all but floor(frac * n) of the positive scores at or above it."""
    s = np.sort(scores_pos)
    k = int(np.floor(frac * len(s)))
    return s[k] if len(s) else np.inf


def thr_C(D, P, rows_tr, sC, frac, labC="labC"):
    """Lowest threshold whose first firing loses <= frac of the train 'would-succeed' packets (right, >= 1 failed
    main decode). A packet is lost when its first firing row has a false label: max score over its false rows."""
    g = D["gid"][rows_tr]
    lab = D[labC][rows_tr]
    sc = sC[rows_tr]
    ug, inv = np.unique(g, return_inverse=True)
    mfalse = np.full(len(ug), -np.inf)
    np.maximum.at(mfalse, inv[~lab], sc[~lab])
    # first true row comes after all false rows (label is cumulative): lost iff max false score >= t
    rp = P["right"][ug]
    base = int(rp.sum())
    v = np.sort(mfalse[rp & np.isfinite(mfalse)])[::-1]
    k = int(np.floor(frac * base))
    return (v[k] + 1e-12 if k < len(v) else -np.inf), base


# ------------------------------------------------------------------------------------------------------------ main
def main():
    t0 = time.time()
    os.makedirs(PLOTS, exist_ok=True)
    R = dict(validation={}, base={}, p1={}, auc={}, ops={}, oracle={}, combos={}, cost={}, d={})
    data = {}
    for name, rate, snr, part, pat in POINTS:
        D, P, meta = load(part, pat)
        R["validation"][name] = validate(part, meta)
        D = prep(D, P)
        C = costs(rate)
        md = measured_dec(D)
        C["dec_model"] = C["dec"]
        if md is not None:                                    # the logged step (model + a constant ~1k: LLR / check)
            C["retry"] += md - C["dec"]
            C["dec"] = md
        D["rem"] = rem_after(D, P, C)
        R["cost"][name] = C
        nch = int(P["chunk"].max()) + 1
        test_pk = P["chunk"] >= nch - 2
        data[name] = (D, P, C, test_pk, rate, snr)
        print(f"{name}: {len(D['pk'])} rows, {len(P['pkt'])} packets, {time.time() - t0:.0f} s", flush=True)

    # noise only: the failed main rows (subsampled to 40k per chunk... all CRC passes kept) and a 20k scatter sample
    rng = np.random.default_rng(1)

    def keep_noise(z):
        m = ~z["d_retry"]
        k = np.zeros(len(m), bool)
        idx = np.where(m)[0]
        k[rng.choice(idx, min(len(idx), 25000), replace=False)] = True
        k |= z["d_crc"]
        return k
    Dn, Pn, metan = load(NOISE[3], NOISE[4], keep_rows=keep_noise)
    R["validation"][NOISE[0]] = validate(NOISE[3], metan)
    Dn["pm0"] = Dn["pm_list"][:, 0].astype(np.float64)
    Dn["pm_norm"] = Dn["pm0"] / Dn["l_sum"]
    Dn["pmcrc_norm"] = Dn["pm_crc"] / Dn["l_sum"]
    print(f"noise: {len(Dn['pk'])} rows kept, {time.time() - t0:.0f} s", flush=True)

    # ---------------------------------------------------------------------------------------------- P0 base rates
    for name, (D, P, C, test_pk, rate, snr) in data.items():
        mr, rr = ~D["retry"], D["retry"]
        fm = mr & ~D["acc"]
        R["base"][name] = dict(
            packets=int(len(P["pkt"])), rows=int(len(D["pk"])), main=int(mr.sum()), retries=int(rr.sum()),
            errors=int((~P["right"]).sum()), cpar_mean=float(P["cpar"].mean()),
            cpar_before_first=float(D["cpar0"][D["att"] == 0].mean()),
            failed_main=int(fm.sum()), A_pos=int((fm & D["in_cell"]).sum()),
            A2_pos=int((fm & (np.abs(D["f_err"]) <= 2)).sum()), A_cell=int((fm & (D["cell"] ==
                                                                                   P["true_cell"][D["gid"]])).sum()),
            B_pos=int((rr & D["acc"]).sum()), B_pos_parent_in_cell=int((rr & D["acc"] & D["in_cell"][
                np.maximum(D["par_row"], 0)]).sum()), B_parent_in_cell=int((rr & D["in_cell"][np.maximum(
                    D["par_row"], 0)]).sum()),
            C_pos=int((fm & D["labC"]).sum()), C2_pos=int((fm & D["labC2"]).sum()),
            crc_right=int((D["crc"] & D["right"]).sum()), crc_wrong=int((D["crc"] & ~D["right"]).sum()),
            acc_wrong=int((D["acc"] & ~D["right"]).sum()), first_cell_none=int((P["first_cell"] < 0).sum()),
            retry_cost_share=float(rr.sum() * C["retry"] / P["cpar"].sum()),
            test_packets=int(test_pk.sum()))
    R["base"][NOISE[0]] = dict(frames=int(len(Pn["pkt"])), rows_total=int(sum(m["rows"] for m in metan)),
                               rows_kept=int(len(Dn["pk"])), crc_pass=int(Dn["crc"].sum()),
                               accepted=int(Dn["acc"].sum()), cpar_mean=float(Pn["cpar"].mean()))

    # ---------------------------------------------------------------------------------------------- P1 PM vs rho
    from scipy.stats import pearsonr, spearmanr
    by_rate = {}
    for name, (D, P, C, test_pk, rate, snr) in data.items():
        by_rate.setdefault(rate, []).append(name)
    for rate, names in by_rate.items():
        res = dict(points=names)
        Ds = [data[n][0] for n in names]
        cat = lambda k: np.concatenate([d[k] for d in Ds])
        pmn, rho, crc, right = cat("pm_norm"), cat("rho_best").astype(float), cat("crc"), cat("right")
        pcn, rcr, rmin, acc = cat("pmcrc_norm"), cat("rho_crc").astype(float), cat("rho_min").astype(float), \
            cat("acc")
        ok = np.isfinite(pmn) & np.isfinite(rho)
        res["pearson_all"] = float(pearsonr(pmn[ok], rho[ok])[0])
        res["spearman_all"] = float(spearmanr(pmn[ok], rho[ok])[0])
        cr = crc & np.isfinite(pcn)
        res["spearman_crc"] = float(spearmanr(pcn[cr], rcr[cr])[0]) if cr.sum() > 2 else np.nan
        good = crc & right
        bad = crc & ~right
        res["crc_right"], res["crc_wrong"] = int(good.sum()), int(bad.sum())
        res["wrong_rho_above_thr"] = int((bad & (rcr > rmin)).sum())
        res["right_rho_below_thr"] = int((good & (rcr <= rmin)).sum())
        res["wrong_rho_over_thr_max"] = float(np.nanmax(rcr[bad] / rmin[bad])) if bad.any() else None
        res["right_rho_over_thr_min_acc"] = float(np.nanmin((rcr / rmin)[good & acc]))
        res["right_rho_over_thr_p001"] = float(np.nanpercentile((rcr / rmin)[good & acc], 0.1))
        # PM alone: threshold per point = the largest normalised PM of an ACCEPTED right CRC pass
        fa, nb, per = 0, 0, {}
        for n_, d in zip(names, Ds):
            g_ = d["crc"] & d["right"] & d["acc"]
            b_ = d["crc"] & ~d["right"]
            thr = float(np.nanmax(d["pmcrc_norm"][g_]))
            k = int((d["pmcrc_norm"][b_] <= thr).sum())
            per[n_] = dict(thr=thr, wrong=int(b_.sum()), wrong_accepted_by_pm=k,
                           wrong_rho_rej=int((b_ & ~(d["rho_crc"] > d["rho_min"])).sum()),
                           auc_pm=auc(~d["right"][d["crc"]], d["pmcrc_norm"][d["crc"]])[:2],
                           auc_rho=auc(~d["right"][d["crc"]], -d["rho_crc"][d["crc"]].astype(float))[:2],
                           pm_right_max=thr, pm_wrong_min=float(np.nanmin(d["pmcrc_norm"][b_])) if b_.any() else None)
            fa += k
            nb += int(b_.sum())
        res["per_point"] = per
        res["pm_false_accept"] = (fa, nb, cp(fa, nb))
        if rate == "0.15":                                    # noise-only CRC passes against the 0.15 thresholds
            ncr = Dn["crc"]
            for n_ in names:
                thr = per[n_]["thr"]
                k = int((Dn["pmcrc_norm"][ncr] <= thr).sum())
                per[n_]["noise_crc"] = int(ncr.sum())
                per[n_]["noise_accepted_by_pm"] = (k, cp(k, int(ncr.sum())))
            res["noise_rho_above_thr"] = int((ncr & (Dn["rho_crc"] > Dn["rho_min"])).sum())
            res["noise_pm_min"] = float(np.nanmin(Dn["pmcrc_norm"][ncr]))
            res["noise_rho_max"] = float(np.nanmax(Dn["rho_crc"][ncr].astype(float)))
            res["noise_rho_over_thr_max"] = float(np.nanmax(Dn["rho_crc"][ncr].astype(float) /
                                                            Dn["rho_min"][ncr].astype(float)))
        R["p1"][rate] = res
    plot_pm_rho(data, Dn)

    # --------------------------------------------------------------------------------------------- P2/P3 models
    heads = {
        "A": dict(rows=lambda D: (~D["retry"]) & (~D["acc"]), lab=lambda D: D["in_cell"], par=False),
        "B": dict(rows=lambda D: D["retry"], lab=lambda D: D["acc"], par=True),
        "C": dict(rows=lambda D: (~D["retry"]) & (~D["acc"]), lab=lambda D: D["labC"], par=False),
        "A2": dict(rows=lambda D: (~D["retry"]) & (~D["acc"]), lab=lambda D: np.abs(D["f_err"]) <= 2, par=False),
        "C2": dict(rows=lambda D: (~D["retry"]) & (~D["acc"]), lab=lambda D: D["labC2"], par=False),
    }
    RATEV = {"1/10": 0.1, "0.15": 0.15, "2/5": 0.4, "1/2": 0.5}
    scores = {}                                              # (head, point, fset, model) -> score per row (all rows)
    for h, H in heads.items():
        fsets = FSETS if h in ("A", "B", "C") else ["F0+F1+F2+F3"]
        models = list(MODELS) if h in ("A", "B", "C") else ["logistic", "MLP 2x32"]
        if QUICK:
            fsets, models = ["F0", "F0+F1+F2+F3"], ["logistic", "MLP 2x32"]
        for fs in fsets:
            # pooled: every point, the code rate as an input
            Xs, ys, trm, tem, srcs = [], [], [], [], []
            for name, (D, P, C, test_pk, rate, snr) in data.items():
                rows = np.where(H["rows"](D))[0]
                X, cols = feats(D, P, rows, fs, use_par=H["par"])
                y = H["lab"](D)[rows]
                te = test_pk[D["gid"][rows]]
                Xs.append(np.c_[X, np.full(len(rows), RATEV[rate])])
                ys.append(y)
                tem.append(te)
                srcs.append((name, rows))
                for model in models:
                    s, ntr = fit_score(X[~te], y[~te], X, model)
                    a = auc(y[te], s[te])
                    full = np.full(len(D["pk"]), np.nan)
                    full[rows] = s
                    scores[(h, name, fs, model)] = full
                    R["auc"][f"{h}|{name}|{fs}|{model}"] = dict(auc=a[0], se=a[1], n_pos=a[2], n_neg=a[3],
                                                               n_train=ntr, n_train_pos=int(y[~te].sum()))
                if fs == "F0+F1+F2+F3":                       # best single feature (chosen on train) as a baseline
                    best = (0.5, None, 1)
                    for j, c in enumerate(cols):
                        xj = np.nan_to_num(X[:, j], nan=np.nanmedian(X[:, j]) if np.isfinite(X[:, j]).any() else 0)
                        at = auc(y[~te], xj[~te])[0]
                        if np.isfinite(at) and abs(at - 0.5) > abs(best[0] - 0.5):
                            best = (at, j, 1 if at >= 0.5 else -1)
                    if best[1] is not None:
                        xj = np.nan_to_num(X[:, best[1]], nan=np.nanmedian(X[:, best[1]]))
                        a = auc(y[te], best[2] * xj[te])
                        R["auc"][f"{h}|{name}|single|{cols[best[1]]}"] = dict(auc=a[0], se=a[1], n_pos=a[2],
                                                                            n_neg=a[3])
            X = np.concatenate(Xs)
            y = np.concatenate(ys)
            te = np.concatenate(tem)
            for model in models:
                s, ntr = fit_score(X[~te], y[~te], X, model)
                a = auc(y[te], s[te])
                R["auc"][f"{h}|pooled|{fs}|{model}"] = dict(auc=a[0], se=a[1], n_pos=a[2], n_neg=a[3],
                                                           n_train=ntr, n_train_pos=int(y[~te].sum()))
                o = 0
                for (name, rows) in srcs:                     # the pooled model's AUC per point
                    ss = s[o:o + len(rows)]
                    yy, tt = y[o:o + len(rows)], te[o:o + len(rows)]
                    a2 = auc(yy[tt], ss[tt])
                    R["auc"][f"{h}|pooled@{name}|{fs}|{model}"] = dict(auc=a2[0], se=a2[1], n_pos=a2[2],
                                                                      n_neg=a2[3])
                    o += len(rows)
            print(f"head {h} {fs}: {time.time() - t0:.0f} s", flush=True)

    # head D: noise-only vs 0.15 signal, failed main decodes; snr_rx dropped (it is -1 vs -4 / -3 by construction)
    SCALE = ("snr_rx", "cum_pm", "cum_rho", "m_hyp", "pm_cell", "pm0", "pm_gap", "pm_spread", "pm_meanex",
             "l_sum", "l_mean", "l_lt1", "pm_norm", "m_br0", "m_br1", "m_br_d", "p_r", "snr_m2m4")
    for fs in (["F0", "F0+F1+F2", "F0+F1+F2+F3", "scale-free"] if not QUICK else ["F0+F1+F2+F3", "scale-free"]):
        drop = ("snr_rx", "cum_pm", "cum_rho") if fs != "scale-free" else SCALE
        fsx = fs if fs != "scale-free" else "F0+F1+F2+F3"
        Xs, ys, tes = [], [], []
        for name in ("0.15 -4", "0.15 -3"):
            D, P, C, test_pk, rate, snr = data[name]
            rows = np.where((~D["retry"]) & (~D["acc"]))[0]
            X, cols = feats(D, P, rows, fsx, drop=drop)
            Xs.append(X)
            ys.append(np.zeros(len(rows), bool))
            tes.append(test_pk[D["gid"]][rows])
        Dn2 = dict(Dn)
        Dn2["f0_dist"] = np.abs(Dn["f_err"] - Pn["f0_err"][Dn["gid"]])
        pm = Dn["pm_list"].astype(np.float64)
        fin = np.isfinite(pm)
        pmf = np.where(fin, pm, np.nan)
        Dn2["pm_gap"] = np.where(fin[:, 1], pm[:, 1] - pm[:, 0], 0.0)
        Dn2["pm_spread"] = np.nanmax(pmf, 1) - pm[:, 0]
        Dn2["pm_meanex"] = np.nanmean(pmf, 1) - pm[:, 0]
        Dn2["cum_pm"] = Dn2["cum_rho"] = np.full(len(Dn["pk"]), np.nan)
        rows = np.where((~Dn["retry"]) & (~Dn["acc"]))[0]
        X, cols = feats(Dn2, Pn, rows, fsx, drop=drop)
        Xs.append(X)
        ys.append(np.ones(len(rows), bool))
        tes.append(Pn["chunk"][Dn["gid"][rows]] >= 6)
        X, y, te = np.concatenate(Xs), np.concatenate(ys), np.concatenate(tes)
        for model in ["logistic", "MLP 2x32"]:
            s, ntr = fit_score(X[~te], y[~te], X, model)
            a = auc(y[te], s[te])
            R["d"][f"{fs}|{model}"] = dict(auc=a[0], se=a[1], n_pos=a[2], n_neg=a[3], n_train=ntr)
        # one-feature AUCs (which single feature separates noise; scale leaks)
        if fs in ("F0+F1+F2+F3", "scale-free"):
            R["d"]["single " + fs] = {c: auc(y[te], np.nan_to_num(X[te, j], nan=np.nanmedian(X[:, j])))[0]
                                for j, c in enumerate(cols)}
    print(f"head D: {time.time() - t0:.0f} s", flush=True)

    # ----------------------------------------------------------------------------- operating points and replay
    full = "F0+F1+F2+F3"
    for name, (D, P, C, test_pk, rate, snr) in data.items():
        trm = ~test_pk
        rowsF = np.where((~D["retry"]) & (~D["acc"]))[0]
        rowsR = np.where(D["retry"])[0]
        ops = {}
        for model in (["logistic", "MLP 2x32"] if QUICK else list(MODELS)):
            nnm = NN_MACS[model]
            sB = scores.get(("B", name, full, model))
            sA = scores.get(("A", name, full, model))
            sC = scores.get(("C", name, full, model))
            for frac in (0.01, 0.001):
                # B: threshold on the train successful retries
                rtr = rowsR[trm[D["gid"][rowsR]]]
                tB = thr_for_loss(sB[rtr][D["acc"][rtr]], frac)
                ops[f"B|{model}|{frac}"] = dict(thr=float(tB), **replay(D, P, C, test_pk, sB=sB, tB=tB,
                                                                       nn_macs=nnm))
                # A: false-positive rate <= frac on the train negatives
                ftr = rowsF[trm[D["gid"][rowsF]]]
                neg = sA[ftr][~D["in_cell"][ftr]]
                tA = float(np.quantile(neg, 1 - frac)) if len(neg) else np.inf
                ops[f"A|{model}|{frac}"] = dict(thr=tA, **replay(D, P, C, test_pk, sA=sA, tA=tA, nn_macs=nnm))
                # C: <= frac of the train would-succeed packets lost
                tC, base = thr_C(D, P, ftr, sC, frac)
                ops[f"C|{model}|{frac}"] = dict(thr=float(tC), base_train=base,
                                                **replay(D, P, C, test_pk, sC=sC, tC=tC, nn_macs=nnm))
                # combinations at the same per-head thresholds
                for combo in ("A+B", "A+C", "B+C", "A+B+C"):
                    kw = {}
                    if "A" in combo:
                        kw.update(sA=sA, tA=tA)
                    if "B" in combo:
                        kw.update(sB=sB, tB=tB)
                    if "C" in combo:
                        kw.update(sC=sC, tC=tC)
                    ops[f"{combo}|{model}|{frac}"] = replay(D, P, C, test_pk, nn_macs=nnm, **kw)
            # sensitivity labels A2 / C2 (|f_err| <= 2 STEP), logistic and MLP 2x32 only
        for model in ["logistic", "MLP 2x32"]:
            s2A, s2C = scores.get(("A2", name, full, model)), scores.get(("C2", name, full, model))
            ftr = rowsF[trm[D["gid"][rowsF]]]
            lab2 = (np.abs(D["f_err"]) <= 2)
            for frac in (0.01, 0.001):
                neg = s2A[ftr][~lab2[ftr]]
                tA = float(np.quantile(neg, 1 - frac))
                ops[f"A2|{model}|{frac}"] = dict(thr=tA, **replay(D, P, C, test_pk, sA=s2A, tA=tA, labA="in_cell2",
                                                                  nn_macs=NN_MACS[model]))
                tC, base = thr_C(D, P, ftr, s2C, frac, labC="labC2")
                ops[f"C2|{model}|{frac}"] = dict(thr=float(tC), **replay(D, P, C, test_pk, sC=s2C, tC=tC,
                                                                         labC="labC2", nn_macs=NN_MACS[model]))
        R["ops"][name] = ops
        # oracle gates (perfect labels, no NN cost)
        orc = {}
        lA = np.where(D["in_cell"], 1.0, 0.0)
        orc["A"] = replay(D, P, C, test_pk, sA=lA, tA=0.5)
        orc["B"] = replay(D, P, C, test_pk, sB=np.where(D["acc"], 1.0, 0.0), tB=0.5)
        orc["C"] = replay(D, P, C, test_pk, sC=np.where(D["labC"], 1.0, 0.0), tC=0.5)
        orc["B_skip_all"] = replay(D, P, C, test_pk, sB=np.zeros(len(D["pk"])), tB=0.5)
        orc["A+B"] = replay(D, P, C, test_pk, sA=lA, tA=0.5, sB=np.where(D["acc"], 1.0, 0.0), tB=0.5)
        orc["A2"] = replay(D, P, C, test_pk, sA=(np.abs(D["f_err"]) <= 2).astype(float), tA=0.5, labA="in_cell2")
        orc["C2"] = replay(D, P, C, test_pk, sC=D["labC2"].astype(float), tC=0.5, labC="labC2")
        orc["A2+B"] = replay(D, P, C, test_pk, sA=(np.abs(D["f_err"]) <= 2).astype(float), tA=0.5,
                             labA="in_cell2", sB=np.where(D["acc"], 1.0, 0.0), tB=0.5)
        R["oracle"][name] = orc
        # diagnostic: retry success when the parent main decode was in the right cell
        rr = D["retry"]
        pin = D["in_cell"][np.maximum(D["par_row"], 0)] & rr
        R["oracle"][name]["retry_success_parent_in_cell"] = (int((pin & D["acc"]).sum()), int(pin.sum()))
        print(f"ops {name}: {time.time() - t0:.0f} s", flush=True)

    plot_auc(R)
    with open(os.path.join(OUT, "nn_offline.json"), "w") as f:
        json.dump(R, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    print(f"done {time.time() - t0:.0f} s")


# ------------------------------------------------------------------------------------------------------------ plots
def plot_pm_rho(data, Dn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rng = np.random.default_rng(0)
    fig, axs = plt.subplots(2, 2, figsize=(10, 8.5))
    panels = [("1/10", ["1/10 -5"]), ("0.15", ["0.15 -4", "0.15 -3"]), ("2/5", ["2/5 0.5"]), ("1/2", ["1/2 2"])]
    for ax, (rate, names) in zip(axs.ravel(), panels):
        D = {k: np.concatenate([data[n][0][k] for n in names]) for k in ("pm_norm", "rho_best", "crc", "right",
                                                                         "pmcrc_norm", "rho_crc")}
        fail = ~D["crc"]
        sel = np.where(fail)[0]
        sel = rng.choice(sel, min(len(sel), 6000), replace=False)
        ax.scatter(D["pm_norm"][sel], D["rho_best"][sel].astype(float), s=2, c="0.65", label="CRC fail: best-PM path (sample)")
        g = np.where(D["crc"] & D["right"])[0]
        g = rng.choice(g, min(len(g), 6000), replace=False)
        ax.scatter(D["pmcrc_norm"][g], D["rho_crc"][g].astype(float), s=2, c="tab:blue", label="CRC pass, right: CRC path")
        b = D["crc"] & ~D["right"]
        ax.scatter(D["pmcrc_norm"][b], D["rho_crc"][b].astype(float), s=14, c="tab:red", marker="x",
                   label="CRC pass, wrong: CRC path")
        if rate == "0.15":
            ax.scatter(Dn["pmcrc_norm"][Dn["crc"]], Dn["rho_crc"][Dn["crc"]].astype(float), s=14, c="k", marker="+",
                       label="CRC pass, noise only")
        thr = np.unique(np.concatenate([data[n][0]["rho_min"] for n in names]).astype(float))
        for t in thr:
            ax.axhline(t, color="tab:green", lw=1, ls="--")
        ax.set_xlabel("path metric / sum |L|")
        ax.set_ylabel("re-encoding rho of that path")
        ax.set_title(f"R = {rate} ({', '.join(n.split()[1] + ' dB' for n in names)})", fontsize=10)
        ax.grid(alpha=.3)
    h, l = axs[0, 1].get_legend_handles_labels()
    h.append(plt.Line2D([], [], color="tab:green", ls="--"))
    l.append("re-encoding threshold rho_min")
    fig.legend(h, l, loc="lower center", ncol=3, markerscale=3, fontsize=9)
    fig.suptitle("Normalised path metric vs re-encoding rho per decode attempt")
    fig.tight_layout(rect=(0, 0.07, 1, 0.97))
    fig.savefig(os.path.join(PLOTS, "nn_pm_vs_rho.png"), dpi=130)
    plt.close(fig)


def plot_auc(R):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = [p[0] for p in POINTS] + ["pooled"]
    for h, title in (("A", "Head A (local refine): AUC per feature set"),
                     ("B", "Head B (retry gate): AUC per feature set"),
                     ("C", "Head C (grid stop): AUC per feature set")):
        fig, ax = plt.subplots(figsize=(8, 5.2))
        x = np.arange(len(FSETS))
        for j, n in enumerate(names):
            for model, ls in (("logistic", "--"), ("MLP 2x32", "-")):
                v = [R["auc"].get(f"{h}|{n}|{fs}|{model}", {}).get("auc", np.nan) for fs in FSETS]
                e = [R["auc"].get(f"{h}|{n}|{fs}|{model}", {}).get("se", np.nan) for fs in FSETS]
                npos = R["auc"].get(f"{h}|{n}|{FSETS[-1]}|{model}", {}).get("n_pos", 0)
                ax.errorbar(x + (j - 2.5) * 0.04, v, yerr=e, ls=ls, marker="o", ms=4, color=f"C{j}", capsize=2,
                            label=f"{n} ({model}, {npos} test pos.)")
        ax.set_xticks(x)
        ax.set_xticklabels(FSETS)
        ax.set_xlabel("feature set")
        ax.set_ylabel("test AUC (+- 1 s.e.)")
        ax.set_title(title)
        ax.grid(alpha=.3)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(PLOTS, f"nn_auc_head{h}.png"), dpi=130)
        plt.close(fig)


if __name__ == "__main__":
    main()
