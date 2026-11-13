"""BLIND_IMPLEMENTATION/testing/: offline analysis of the Stage 3 dumps (BLIND_IMPLEMENTATION/testing/run.py --dump).

    python BLIND_IMPLEMENTATION/testing/analyze.py t-dump10a [t-dump10b ...]      -> BLIND_IMPLEMENTATION/testing/results/report_<first part>.md + plots

Step 1  where the MACs go (fast path / decodes / rest) and why packets fail (failure types).
Step 2  counterfactual policies on the recorded hypotheses: within one Stage 3 candidate the receiver decodes the
        hypotheses in some order and stops at the first accepted decode (CRC + re-encoding check), so the outcome
        of any ordering / screening / adaptive-T policy follows from the per-hypothesis outcomes: decodes used and
        whether the accepted packet is right.
"""
import glob
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = 7.5e-5
COLS = ("uid", "row", "rank", "M", "Mbest", "rho_sc", "dF", "dT", "crc", "acc", "corr", "in_list", "nok", "rho",
        "c1", "c2", "dphi", "thr", "snr")
DEC = 180224 + 6144                                  # one CA-SCL-8 decode + LLRs (blind_vp.MAC)
CORR = 4 * 1024 + 2 * 1024                           # SC-codeword correlation: de-rotation / product + sum (MACs)


def load(parts):
    rows, pk = [], []
    for spec in parts:                               # "part" or "part@snr" (only that SNR of the part)
        part, _, only = spec.partition("@")
        for p in glob.glob(os.path.join(HERE, "results", "dumps", part, "s3_*.npz")):
            d = np.load(p)
            if only and float(d["snr"]) != float(only):
                continue
            if len(d["rows"]):
                rows.append(d["rows"])
            pk.append(np.stack([d["uid"], d["passed"], d["good"], d["fast"], d["macs"], d["cpar"], d["m_fast"],
                                d["dmac"], np.full(len(d["uid"]), float(d["snr"]))], 1))
    R = np.concatenate(rows) if rows else np.zeros((0, len(COLS)))
    P = np.concatenate(pk)
    return {c: R[:, i] for i, c in enumerate(COLS)}, P


def candidates(R):
    """Split the rows into Stage 3 candidates (a new candidate starts at rank 0): list of index arrays."""
    starts = np.nonzero(R["rank"] == 0)[0]
    return [np.arange(a, b) for a, b in zip(starts, list(starts[1:]) + [len(R["rank"])])]


def ub(n):
    return 3.0 / n if n else np.nan                  # 95 % upper bound with 0 events


def policy(R, cands, order_key, T, screen=None):
    """Decodes used and outcome per candidate when the hypotheses are tried in order_key order (ascending), at most
    T of them, optionally skipping those with screen(idx) False: (decodes, accepted, right)."""
    dec = acc = right = 0
    for idx in cands:
        o = idx[np.argsort(order_key(idx), kind="stable")]
        if screen is not None:
            o = o[screen(o)]
        for j in o[:T]:
            dec += 1
            if R["acc"][j]:
                acc += 1
                right += int(R["corr"][j])
                break
    return dec, acc, right


def zs(x):
    return (x - np.nanmean(x)) / (np.nanstd(x) + 1e-12)


def main(parts):
    R, P = load(parts)
    out = [f"# Stage 3 dump analysis: {', '.join(parts)}", ""]
    for snr in sorted(set(P[:, 8])):
        pk = P[P[:, 8] == snr]
        m = R["snr"] == snr
        Rs = {c: v[m] for c, v in R.items()}
        n = len(pk)
        good = pk[:, 2] > 0
        fast = pk[:, 3] > 0
        out += [f"## SNR {snr:g} dB: {n} packets, {int((~good).sum())} not decoded right "
                f"(BLER {(~good).mean():.2e}), {int(fast.sum())} by the fast path", ""]
        tot, mf, md = pk[:, 4].mean(), pk[:, 6].mean(), pk[:, 7].mean()
        out += ["**Where the MACs go (mean per packet)**", "",
                "| part | MACs | share |", "|---|---|---|",
                f"| fast path | {mf / 1e6:.3f} M | {mf / tot:.0%} |",
                f"| CA-SCL decodes (search + retries) | {md / 1e6:.3f} M | {md / tot:.0%} |",
                f"| rest (search metrics, refinement scoring, checks) | {(tot - mf - md) / 1e6:.3f} M | "
                f"{(tot - mf - md) / tot:.0%} |",
                f"| total | {tot / 1e6:.3f} M | per core {pk[:, 5].mean() / 1e6:.3f} M |", ""]
        # ---- failure classification
        fails = pk[~good, 0]
        kinds = {"Stage 2: true CFO region not among the Stage 3 candidates": 0,
                 "sync / list: true region reached but no CA-SCL-8 decode of it is right": 0,
                 "selection: true packet in a final list but another path chosen": 0,
                 "order / budget: a right decode exists among the top 6 but was not reached": 0}
        for u in fails:
            k = Rs["uid"] == u
            if not k.any():
                kinds["Stage 2: true CFO region not among the Stage 3 candidates"] += 1
            elif not (np.abs(Rs["dF"][k]) < 2 * STEP).any():
                kinds["Stage 2: true CFO region not among the Stage 3 candidates"] += 1
            elif (Rs["corr"][k] * Rs["acc"][k]).any():
                kinds["order / budget: a right decode exists among the top 6 but was not reached"] += 1
            elif Rs["in_list"][k].any():
                kinds["selection: true packet in a final list but another path chosen"] += 1
            else:
                kinds["sync / list: true region reached but no CA-SCL-8 decode of it is right"] += 1
        out += ["**Failure types** (packets not decoded right)", "", "| type | packets |", "|---|---|"]
        out += [f"| {k} | {v} |" for k, v in kinds.items()] + [""]
        if not len(Rs["uid"]):
            continue
        cands = candidates(Rs)
        good_h = (Rs["acc"] > 0) & (Rs["corr"] > 0)
        wrong_h = (Rs["acc"] > 0) & (Rs["corr"] == 0)
        out += [f"**Stage 3 hypotheses** {len(Rs['uid'])} in {len(cands)} candidates; accepted right "
                f"{int(good_h.sum())}, accepted wrong {int(wrong_h.sum())}", ""]
        # ---- A / C: rankings
        T0 = 2
        zJ = zs(Rs["M"]) - zs(Rs["rho_sc"])          # once per SNR (inside the lambda it was O(rows^2))
        pols = {
            "path metric (baseline)": lambda i: Rs["M"][i],
            "SC-codeword correlation": lambda i: -Rs["rho_sc"][i],
            "metric, correlation as tie-break (|dM| < 1)": lambda i: np.round(Rs["M"][i]) - 1e-3 * Rs["rho_sc"][i],
            "joint z(metric) - z(correlation)": lambda i: zJ[i],
        }
        out += ["**A / C: ranking inside a candidate** (decodes stop at the first acceptance)", "",
                "| ranking | budget T | CA-SCL decodes | accepted right | accepted wrong | extra MACs (corr.) |",
                "|---|---|---|---|---|---|"]
        for nm, key in pols.items():
            for T in (1, 2, 3, 6):
                d, a, r = policy(Rs, cands, key, T)
                extra = "0" if "baseline" in nm else f"{len(Rs['uid']) * CORR / 1e6:.2f} M"
                out.append(f"| {nm} | {T} | {d} | {r} | {a - r} | {extra} |")
        out.append("")
        # ---- B: screening on the SC-codeword correlation (normalised by the expected right value)
        s_lin = 10 ** (snr / 10)
        e_r = np.sqrt(s_lin / (1 + s_lin))
        out += ["**B: screening** (skip hypotheses with rho_sc < t x sqrt(s / (1 + s)), metric order, T = 2)", "",
                "| t | decodes | accepted right | accepted wrong | right hypotheses screened out |", "|---|---|---|---|---|"]
        for t in (0.0, 0.2, 0.3, 0.4, 0.5):
            d, a, r = policy(Rs, cands, pols["path metric (baseline)"], T0, screen=lambda o: Rs["rho_sc"][o] >= t * e_r)
            lost = int((good_h & (Rs["rho_sc"] < t * e_r)).sum())
            out.append(f"| {t} | {d} | {r} | {a - r} | {lost} of {int(good_h.sum())} |")
        out.append("")
        # predictive power: rho_sc of decodable vs not
        if good_h.any() and (~good_h).any():
            from itertools import product
            g, b = Rs["rho_sc"][good_h], Rs["rho_sc"][~good_h]
            auc = np.mean([float(x > y) for x, y in product(g[:400], b[:400])])
            gm, bm = -Rs["M"][good_h], -Rs["M"][~good_h]
            aucm = np.mean([float(x > y) for x, y in product(gm[:400], bm[:400])])
            out += [f"Predictive power (AUC, right-and-accepted vs other hypotheses): SC-codeword correlation "
                    f"{auc:.3f}, path metric {aucm:.3f}.", ""]
        # ---- F: selection inside the final list
        sel_fail = (Rs["in_list"] > 0) & (Rs["corr"] == 0)
        out += [f"**F: list re-ranking potential** hypotheses whose CA-SCL list holds the true packet but chose "
                f"another path: {int(sel_fail.sum())} (of which CRC-passing chosen path: "
                f"{int((sel_fail & (Rs['crc'] > 0)).sum())}); hypotheses with the true packet in the list: "
                f"{int(Rs['in_list'].sum())}.", ""]
        # ---- J: half-packet statistics on accepted decodes
        if wrong_h.any():
            out += ["**J: half-packet consistency on accepted decodes** (wrong accepted vs right)", "",
                    "| statistic | right: 0.1 % quantile | wrong: max |", "|---|---|---|"]
            for nm, v in (("rho", Rs["rho"]), ("min(|C1|, |C2|)", np.minimum(Rs["c1"], Rs["c2"])),
                          ("|phase(C1 C2*)|", -np.abs(Rs["dphi"]))):
                out.append(f"| {nm} | {np.quantile(v[good_h], 0.001):.3f} | {v[wrong_h].max():.3f} |")
            out.append("")
        else:
            out += [f"**J:** no wrong accepted decode among {int((Rs['acc'] > 0).sum())} accepted "
                    f"(upper bound {ub(int((Rs['acc'] > 0).sum())):.1e}); nothing for a second check to catch.", ""]
    rep = os.path.join(HERE, "results", f"report_{parts[0]}.md")
    open(rep, "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out))
    print("saved", rep)


if __name__ == "__main__":
    main(sys.argv[1:])
