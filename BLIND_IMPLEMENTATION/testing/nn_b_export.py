"""BLIND_IMPLEMENTATION/testing/: the deployable retry gate (head B) for the online test.

    py BLIND_IMPLEMENTATION/testing/nn_b_export.py

One logistic model per code rate (the rate's dump points pooled; train = the first 6 of 8 chunks per point), on
features of the failed main decode that the receiver has at the retry decision without the grid state or a
re-encoding (computed online by small_rx._gate_feats from the decoder list and the LLRs):
    pm0, pm_gap, pm_spread, pm_meanex   sorted path metrics of the list
    syn_w, n_rem, n_agree, agree_bits   CRC syndromes / agreement of the list paths
    l_sum, l_mean, l_lt1, pm_norm       channel LLR magnitudes
    sgn_agree                           sign agreement of the LLRs with the best path's codeword
The retry is skipped when the score < thr; thr keeps all but floor(frac * n) of the train successful retries
(frac = 0.001 and 0.01). Writes results/nn_b_gate.json (weights, thresholds) and results/nn_b_export.json
(AUC + replay per point on the test chunks, vs the full-feature per-point gate of nn_offline.json).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nn_offline as no  # noqa: E402

GF = ["pm0", "pm_gap", "pm_spread", "pm_meanex", "syn_w", "n_rem", "n_agree", "agree_bits",
      "l_sum", "l_mean", "l_lt1", "pm_norm", "sgn_agree"]
FRACS = (0.001, 0.01)
GATE_MACS = 50          # the logistic score; the feature work is charged online by small_rx (see _gate_feats)


def X_of(D, rows):
    i = D["par_row"][rows]
    X = np.stack([D[k][i].astype(np.float64) for k in GF], 1)
    X[~np.isfinite(X)] = np.nan
    return X


def main():
    data = {}
    for name, rate, snr, part, pat in no.POINTS:
        D, P, meta = no.load(part, pat)
        D = no.prep(D, P)
        C = no.costs(rate)
        md = no.measured_dec(D)
        if md is not None:
            C["retry"] += md - C["dec"]
            C["dec"] = md
        D["rem"] = no.rem_after(D, P, C)
        nch = int(P["chunk"].max()) + 1
        data[name] = (D, P, C, P["chunk"] >= nch - 2, rate)
        print(name, len(D["pk"]), flush=True)
    full = json.load(open(os.path.join(no.OUT, "nn_offline.json")))
    gate, rep = {}, {}
    for rate in dict.fromkeys(r for _, r, *_ in no.POINTS):
        names = [n for n, (_, _, _, _, r) in data.items() if r == rate]
        Xs, ys = [], []
        for n in names:
            D, P, C, test_pk, _ = data[n]
            rr = np.where(D["retry"] & ~test_pk[D["gid"]])[0]
            Xs.append(X_of(D, rr))
            ys.append(D["acc"][rr])
        Xtr, ytr = np.concatenate(Xs), np.concatenate(ys)
        rng = np.random.default_rng(0)
        pos, neg = np.where(ytr)[0], np.where(~ytr)[0]
        neg = rng.choice(neg, min(len(neg), 40000), replace=False)
        s = np.r_[pos, neg]
        mu, sd = np.nanmean(Xtr[s], 0), np.nanstd(Xtr[s], 0) + 1e-9
        mu = np.where(np.isfinite(mu), mu, 0.0)

        def tr(A):
            return np.clip(np.nan_to_num((A - mu) / sd, nan=0.0), -20, 20)
        from sklearn.linear_model import LogisticRegression
        clf = LogisticRegression(max_iter=2000, C=1.0).fit(tr(Xtr[s]), ytr[s])
        w, b = clf.coef_[0], float(clf.intercept_[0])

        def score(A):                                     # the linear score (monotone in the probability)
            return tr(A) @ w + b
        str_ = score(Xtr)
        thr = {str(f): float(no.thr_for_loss(np.sort(str_[ytr]), f)) for f in FRACS}
        gate[rate] = dict(features=GF, mu=mu.tolist(), sd=sd.tolist(), w=w.tolist(), b=b, thr=thr,
                          train_pos=int(ytr.sum()), train_n=int(len(ytr)))
        for n in names:
            D, P, C, test_pk, _ = data[n]
            sB = np.full(len(D["pk"]), np.inf)
            rr = np.where(D["retry"])[0]
            sB[rr] = score(X_of(D, rr))
            te = rr[test_pk[D["gid"][rr]]]
            a = no.auc(D["acc"][te], sB[te])
            r = dict(auc=a[0], auc_se=a[1], pos=a[2], neg=a[3])
            for f in FRACS:
                r[f"B {f}"] = no.replay(D, P, C, test_pk, sB=sB, tB=thr[str(f)], nn_macs=GATE_MACS)
                fo = full["ops"][n].get(f"B|logistic|{f}", {})
                r[f"full {f}"] = dict(saved_pct=fo.get("saved_pct"), lost=fo.get("lost"))
            rep[n] = r
            print(n, f"AUC {a[0]:.3f}", *(f"{f}: {r[f'B {f}']['saved_pct']:+.1f} % lost {r[f'B {f}']['lost']} "
                                         f"(full {r[f'full {f}']['saved_pct']:+.1f} % lost {r[f'full {f}']['lost']})"
                                         for f in FRACS), flush=True)
    json.dump(gate, open(os.path.join(no.OUT, "nn_b_gate.json"), "w"), indent=1)
    json.dump(rep, open(os.path.join(no.OUT, "nn_b_export.json"), "w"), indent=1,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


if __name__ == "__main__":
    main()
