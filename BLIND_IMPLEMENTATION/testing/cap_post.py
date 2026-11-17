"""BLIND_IMPLEMENTATION/testing/: a MACs-per-core cap applied after the run, on the per-packet MACs logs (read-only, no
simulation).

    py cap_post.py                          # every part; caps 0.2 0.3 0.5 1 2 M
    py cap_post.py --caps 0.25 1 --parts "t-maclog*" "ml-*"   # fnmatch patterns on the part names
    -> results/cap_post.md + results/cap_post.json

Inputs. Blind: <study data>/dumps/<part>/macs_<rx>_R<rate>_<snr>_<seed>.npz (blind_ber.simulate + small_rx mac_acc, one
file per chunk and receiver; on by default, BLIND_NO_MACLOG=1 off). est4: est4/dumps/<part>/macs_R<rate>_<snr>_c<chunk>
.npz (est4/run_bler.py, one file per chunk with every source; EST4_NO_MACLOG=1 off): per source i x_dec_i (int16),
m_evals_i (int16), m_rounds_i (uint8), the flags passed_i / right_i / fe_i / ud_i (np.packbits), n[i], pkt0[i] (packets
pkt0 .. pkt0 + n - 1 of the chunk), coef[i] = (c0, cx, ce, cm), par_dec. Packets are deduplicated per point by (chunk,
packet index) with int64 keys (smoke and main parts on the same seed hold the same packets).

Cost. The standard MACs per core: blind c_hd4a (crit_par_h_d4a) at R = 1/10, 0.15 and c_d4a (crit_par_d4a) at 2/5, 1/2;
est4 core = c0 + cx x + ce e + cm m (plot_e4's E.pilot_macs per core: its mean = plot_e4's figure), and the "ceil"
variant core_ceil = c0 + cx P ceil(x / P) + ce e + cm m (P = par_dec = 4 decodes at once: x extra decodes really take
ceil(x / P) rounds, the fractional x / P understates the tail). The search stops at its first accepted call, so a right
decode's cost is its cost up to acceptance. Per cap C:
    BLER_strict(C) = 1 - #(right & cost <= C) / n   only an accepted right decode within C is delivered, else no packet
                                                     (THE column for plots)
    BLER(C)        = (fe + #(right & cost > C)) / n  (fe: dec != data as counted by blind_ber / run_bler)
    BLER_era(C)    = #(fe | cost > C) / n            every packet over C an erasure (small_rx cap_core)
    cut(C) = #(cost > C) / n,  UD(C) = #(ud & cost <= C) (undetected errors delivered within C)
BLER and BLER_era differ from BLER_strict by the unaccepted packets whose delivered decode is right: run_bler keeps the
decode at f_hat when nothing is accepted, and blind_ber (small_rx: the first decode is delivered when nothing passes)
does the same, and both count dec == data as correct; n_unacc_right = #(~fe & ~passed) per point.
Capped runs (small_rx cap_core; npz cap_core, or "_cap" in the rx name / cap_hit in the part JSON): valid only for
C <= that cap; larger caps are "n/a" (cap unknown: every cap flagged). Non-finite costs / coefficients: a warning and
MISMATCH in the check. Check section: per-chunk dump sums vs the part JSONs' counters (blind: crit_par_h_d4a_macs,
crit_par_d4a_macs, crit_par_macs, macs, frame_err, undetected, frames; est4: frames, frame_err, undetected,
extra_decodes, metric_evals, metric_rounds and the mean core vs pilot_macs of the JSON's per-frame means)."""
import argparse
import fnmatch
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "results")
STD = {"1/10": "c_hd4a", "0.15": "c_hd4a", "2/5": "c_d4a", "1/2": "c_d4a"}   # the standard per-core metric per rate
PCT = (50, 90, 99, 99.9)
WARN = []


def warn(msg):
    WARN.append(msg)
    print("WARNING " + msg, flush=True)


def part_of(p):
    return os.path.basename(os.path.dirname(p))


def files(kind, pats):
    if kind == "blind":
        fs = glob.glob(os.path.join(PROJ, "blind", "dumps", "*", "macs_*.npz")) + \
             glob.glob(os.path.join(PROJ, "*", "blind", "dumps", "*", "macs_*.npz"))
    else:
        fs = glob.glob(os.path.join(PROJ, "est4", "dumps", "*", "macs_*.npz"))
    return sorted(f for f in fs if not pats or any(fnmatch.fnmatch(part_of(f), q) for q in pats))


def blind_json(f):
    """the part JSON rows of a blind dump file (list; [] if missing)."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(f))), "results", f"blind_ber_{part_of(f)}.json")
    return json.load(open(p)) if os.path.exists(p) else []


def est4_cost(z, i):
    """(cost, cost_ceil) per packet of source i of an est4 file."""
    x, e, m = (z[f"{q}_{i}"].astype(np.float64) for q in ("x_dec", "m_evals", "m_rounds"))
    c0, cx, ce, cm = z["coef"][i]
    P = float(z["par_dec"])
    return c0 + cx * x + ce * e + cm * m, c0 + cx * P * np.ceil(x / P) + ce * e + cm * m


def bits(z, q, i, n):
    return np.unpackbits(z[f"{q}_{i}"])[:n].astype(bool)


def records(kind, pats):
    """one dict per (file, rx): key (rate, snr, rx), cid, pkt, cost, cost_ceil, fe, right, passed, ud, cap, part."""
    jc = {}
    for f in files(kind, pats):
        z = np.load(f, allow_pickle=False)
        rate, snr = str(z["rate"]), float(z["snr"])
        if kind == "blind":
            rx = str(z["rx"])
            if part_of(f) not in jc:
                jc[part_of(f)] = blind_json(f)
            cap = float(z["cap_core"]) if "cap_core" in z.files else np.nan
            sus = "_cap" in rx or any(r.get("rx") == rx and "cap_hit" in r for r in jc[part_of(f)])
            c = z[STD.get(rate, "c_hd4a")].astype(np.float64)
            yield dict(key=(rate, snr, rx), cid=("b", int(z["chunk_seed"])), pkt=z["pkt"].astype(np.int64), cost=c,
                       cost_ceil=c, fe=z["fe"].astype(bool), right=z["right"].astype(bool),
                       passed=z["passed"].astype(bool), ud=z["ud"].astype(bool), cap=cap, cap_sus=sus,
                       part=part_of(f), file=os.path.basename(f))
        else:
            for i, src in enumerate(z["src"]):
                n = int(z["n"][i])
                c, cc = est4_cost(z, i)
                yield dict(key=(rate, snr, str(src)), cid=("e",) + tuple(int(v) for v in z["rng_key"]),
                           pkt=int(z["pkt0"][i]) + np.arange(n, dtype=np.int64), cost=c, cost_ceil=cc,
                           fe=bits(z, "fe", i, n), right=bits(z, "right", i, n), passed=bits(z, "passed", i, n),
                           ud=bits(z, "ud", i, n), cap=np.nan, cap_sus=False, part=part_of(f),
                           file=os.path.basename(f))


def load(kind, pats):
    """{(rate, snr, rx): arrays + parts, n_dup, cap, cap_sus}, packets deduplicated by int64 (chunk index << 32 | pkt)
    keys (np.unique, first occurrence kept)."""
    G = defaultdict(list)
    for r in records(kind, pats):
        G[r["key"]].append(r)
    out = {}
    for k, rs in G.items():
        cidx = {}
        keys = np.concatenate([np.int64(cidx.setdefault(r["cid"], len(cidx))) << 32 | r["pkt"] for r in rs])
        _, first = np.unique(keys, return_index=True)
        first = np.sort(first)
        cat = lambda q: np.concatenate([r[q] for r in rs])[first]
        v = {q: cat(q) for q in ("cost", "cost_ceil", "fe", "right", "passed", "ud")}
        caps = [r["cap"] for r in rs if np.isfinite(r["cap"])]
        v.update(parts=sorted({r["part"] for r in rs}), n_dup=int(len(keys) - len(first)),
                 cap=min(caps) if caps else np.nan, cap_sus=any(r["cap_sus"] for r in rs))
        nb = int((~np.isfinite(v["cost"])).sum())
        if nb:
            warn(f"{kind} {k}: {nb} non-finite per-packet costs (cost model failed: coef nan?)")
        v["n_bad"] = nb
        out[k] = v
    return out


def capstats(c, v, C):
    over, n = c > C, len(c)
    return dict(cap=C, bler_strict=float(1 - (v["right"] & ~over).sum() / n),
                bler=float((v["fe"].sum() + (v["right"] & over).sum()) / n), bler_era=float((v["fe"] | over).mean()),
                cut=float(over.mean()), cut_right=int((v["right"] & over).sum()), ud=int((v["ud"] & ~over).sum()))


def point(v, caps, kind):
    c, n = v["cost"], len(v["cost"])
    r = dict(n=n, fe=int(v["fe"].sum()), bler=float(v["fe"].mean()), right=int(v["right"].sum()),
             ud=int(v["ud"].sum()), n_unacc_right=int((~v["fe"] & ~v["passed"]).sum()), parts=v["parts"],
             n_dup=v["n_dup"], n_bad=v["n_bad"], cap_core=None if np.isnan(v["cap"]) else v["cap"],
             cap_suspect=bool(v["cap_sus"]), pct={str(q): float(np.percentile(c, q)) for q in PCT},
             max=float(c.max()), mean=float(c.mean()), caps={})
    for C in caps:
        ok = (np.isnan(v["cap"]) and not v["cap_sus"]) or (np.isfinite(v["cap"]) and C <= v["cap"])
        s = capstats(c, v, C)
        s["valid"] = bool(ok)
        if kind == "est4":                                   # the ceil-rounds variant of the competitors
            s["ceil"] = capstats(v["cost_ceil"], v, C)
        r["caps"][str(C)] = s
    if kind == "est4":
        cc = v["cost_ceil"]
        r.update(pct_ceil={str(q): float(np.percentile(cc, q)) for q in PCT}, max_ceil=float(cc.max()),
                 mean_ceil=float(cc.mean()))
    if v["cap_sus"] and np.isnan(v["cap"]):
        warn(f"{v['parts']}: a capped run (rx name _cap / cap_hit in the JSON) with unknown cap: every cap flagged")
    return r


def check_blind(pats):
    """per-chunk dump sums vs the part JSON rows (blind_ber_<part>.json in the study's results)."""
    rows = []
    for f in files("blind", pats):
        z = np.load(f, allow_pickle=False)
        js = [r for r in blind_json(f) if r["rx"] == str(z["rx"]) and r["rate"] == str(z["rate"])
              and abs(r["snr"] - float(z["snr"])) < 1e-9 and r.get("chunk_seed") == int(z["chunk_seed"])]
        name = f"{part_of(f)}/{os.path.basename(f)}"
        if len(js) != 1:
            rows.append((name, f"{len(js)} json rows", None))
            continue
        j = js[0]
        d = {"frames": (len(z["pkt"]), j["frames"]), "frame_err": (int(z["fe"].sum()), j["frame_err"]),
             "undetected": (int(z["ud"].sum()), j["undetected"])}
        for q, key in (("c_hd4a", "crit_par_h_d4a_macs"), ("c_d4a", "crit_par_d4a_macs"), ("cpar", "crit_par_macs"),
                       ("macs", "macs")):
            d[key] = (float(z[q].astype(np.float64).sum()), float(j.get(key, np.nan)))
        d["finite"] = (int(sum((~np.isfinite(z[q])).sum() for q in ("c_hd4a", "c_d4a", "cpar", "macs"))), 0)
        rows.append((name, "ok", d))
    return rows


def check_est4(pats):
    """per (part, snr, src): dump sums vs bler_<part>.json; mean core vs pilot_macs of the JSON's per-frame means;
    non-finite coef, clipped counts (ovf) or non-contiguous batches -> MISMATCH."""
    grp = defaultdict(list)
    for f in files("est4", pats):
        z = np.load(f, allow_pickle=False)
        for i, src in enumerate(z["src"]):
            grp[(part_of(f), str(z["rate"]), float(z["snr"]), str(src))].append((z, i))
    rows = []
    if not grp:
        return rows
    sys.path[:0] = [PROJ, os.path.join(PROJ, "est4")]
    import estimators as E4E
    for (part, rate, snr, src), zs in sorted(grp.items()):
        name = f"{part} {rate} {snr:+.1f} {src}"
        res = os.path.join(PROJ, "est4", "results", f"bler_{part}.json")
        js = [r for r in json.load(open(res))["results"] if r["src"] == src and abs(r["snr"] - snr) < 1e-9] \
            if os.path.exists(res) else []
        if len(js) != 1:
            rows.append((name, f"{len(js)} json rows", None))
            continue
        j, n = js[0], js[0]["frames"]
        core = E4E.pilot_macs(rate, src, j["extra_decodes"] / n, par=True, m_evals=j.get("metric_evals", 0) / n,
                              m_rounds=j["metric_rounds"] / n if j.get("metric_rounds") else None, mode=j["track"],
                              pn=j["pn"])[1]
        s = lambda q: int(sum(z[f"{q}_{i}"].astype(np.int64).sum() for z, i in zs))
        sb = lambda q: int(sum(bits(z, q, i, int(z["n"][i])).sum() for z, i in zs))
        cost = np.concatenate([est4_cost(z, i)[0] for z, i in zs])
        d = {"frames": (int(sum(int(z["n"][i]) for z, i in zs)), n), "frame_err": (sb("fe"), j["frame_err"]),
             "undetected": (sb("ud"), j["undetected"]), "extra_decodes": (s("x_dec"), j["extra_decodes"]),
             "metric_evals": (s("m_evals"), j["metric_evals"]), "metric_rounds": (s("m_rounds"), j["metric_rounds"]),
             "mean_core": (float(cost.mean()), float(core)),
             "finite_coef": (int(sum((~np.isfinite(z["coef"][i])).sum() for z, i in zs)), 0),
             "ovf": (int(sum(int(z["ovf"][i]) for z, i in zs)), 0),
             "contig": (int(sum(not bool(z["contig"][i]) for z, i in zs)), 0)}
        if d["finite_coef"][0]:
            warn(f"est4 {name}: non-finite cost coefficients (mac_coef failed: see the job log)")
        rows.append((name, "ok", d))
    return rows


def mismatches(d):
    return [k for k, (a, b) in d.items() if not (np.isfinite(a) and np.isfinite(b) and np.isclose(a, b, rtol=1e-5, atol=1e-6))]


def fmt_check(rows):
    L = []
    for name, s, d in rows:
        if d is None:
            L.append(f"- {name}: {s}")
            continue
        bad = mismatches(d)
        L.append(f"- {name}: {'MATCH' if not bad else 'MISMATCH ' + ', '.join(f'{k} {d[k][0]:.6g} vs {d[k][1]:.6g}' for k in bad)}")
    return L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--caps", type=float, nargs="+", default=[0.2, 0.3, 0.5, 1.0, 2.0], help="MACs per core [M]")
    ap.add_argument("--parts", nargs="*", default=None, help="fnmatch patterns on the part names (default all)")
    ap.add_argument("--no-check", action="store_true", help="skip the dump vs JSON consistency check")
    a = ap.parse_args(argv)
    caps = [c * 1e6 for c in a.caps]
    res = {"caps_M": a.caps, "blind": {}, "est4": {}}
    md = ["# MACs-per-core cap applied after the run (cap_post.py)", "",
          "Standard per-core metric: crit_par_h_d4a at R = 1/10, 0.15, crit_par_d4a at 2/5, 1/2 (blind); "
          "plot_e4's pilot_macs per core (est4; + the ceil-rounds variant). BLER_strict(C) = 1 - #(right & cost <= C)"
          " / n (the plotted one); BLER(C) = (errors + right decodes over C) / n; BLER_era(C): every packet over C an "
          "erasure; cut = share over C; UD(C) = undetected errors within C. n/a: C above the run's own cap_core.", ""]
    for kind in ("blind", "est4"):
        P = load(kind, a.parts)
        md += [f"## {kind}", ""]
        if not P:
            md += ["no dumps yet", ""]
            continue
        R = {}
        for (rate, snr, rx), v in sorted(P.items(), key=lambda t: t[0]):
            R[(rate, snr, rx)] = r = point(v, caps, kind)
            res[kind][f"{rate}|{snr:+.1f}|{rx}"] = dict(rate=rate, snr=snr, rx=rx, **r)
        f_ = lambda s, key="bler_strict": f"{s[key]:.2e}" if s["valid"] else "n/a"
        md += ["BLER_strict(C):", "", "| rate | snr | rx | n | BLER | n_unacc_right | p50 | p90 | p99 | p99.9 | max | "
               + " | ".join(f"{c:g}M" for c in a.caps) + " |", "|" + "---|" * (11 + len(caps))]
        for (rate, snr, rx), r in R.items():
            md.append(f"| {rate} | {snr:+.1f} | {rx} | {r['n']} | {r['bler']:.2e} | {r['n_unacc_right']} | "
                      + " | ".join(f"{r['pct'][str(q)] / 1e6:.3f}" for q in PCT) + f" | {r['max'] / 1e6:.3f} | "
                      + " | ".join(f_(s) for s in r["caps"].values()) + " |")
        md += ["", "Details per cap: BLER / BLER_era / cut / UD:", "",
               "| rate | snr | rx | " + " | ".join(f"{c:g}M" for c in a.caps) + " |", "|" + "---|" * (3 + len(caps))]
        for (rate, snr, rx), r in R.items():
            md.append(f"| {rate} | {snr:+.1f} | {rx} | " + " | ".join(
                (f"{s['bler']:.2e} / {s['bler_era']:.2e} / {s['cut']:.1e} / {s['ud']}" if s["valid"] else "n/a")
                for s in r["caps"].values()) + " |")
        md.append("")
        if kind == "est4":
            md += ["Ceil-rounds variant (x extra decodes = ceil(x / 4) rounds): BLER_strict / cut per cap, max:", "",
                   "| rate | snr | rx | mean | mean ceil | p99.9 ceil | max ceil | "
                   + " | ".join(f"{c:g}M" for c in a.caps) + " |", "|" + "---|" * (7 + len(caps))]
            for (rate, snr, rx), r in R.items():
                md.append(f"| {rate} | {snr:+.1f} | {rx} | {r['mean'] / 1e6:.3f} | {r['mean_ceil'] / 1e6:.3f} | "
                          f"{r['pct_ceil']['99.9'] / 1e6:.3f} | {r['max_ceil'] / 1e6:.3f} | "
                          + " | ".join(f"{s['ceil']['bler_strict']:.2e} / {s['ceil']['cut']:.1e}"
                                       for s in r["caps"].values()) + " |")
            md += ["", "Max per-packet MACs per core of each competitor (a cap below it would cut some packet):", ""]
            md += [f"- R {rate} {snr:+.1f} dB {rx}: max {r['max'] / 1e6:.3f} M (ceil {r['max_ceil'] / 1e6:.3f} M), "
                   f"p99.9 {r['pct']['99.9'] / 1e6:.3f} M" for (rate, snr, rx), r in R.items()] + [""]
        dup = [(k, v["n_dup"]) for k, v in P.items() if v["n_dup"]]
        if dup:
            md += ["Duplicate packets dropped (same chunk + index in several parts): "
                   + ", ".join(f"{k[0]} {k[1]:+.1f} {k[2]}: {n}" for k, n in dup), ""]
    if not a.no_check:
        md += ["## check: dumps vs part JSON counters", ""]
        cb, ce = check_blind(a.parts), check_est4(a.parts)
        res["check"] = dict(blind=[(n, s, d) for n, s, d in cb], est4=[(n, s, d) for n, s, d in ce])
        md += (["blind:"] + fmt_check(cb) if cb else ["blind: no dumps yet"]) + [""]
        md += (["est4:"] + fmt_check(ce) if ce else ["est4: no dumps yet"]) + [""]
    if WARN:
        md += ["## WARNINGS", ""] + [f"- {w}" for w in WARN] + [""]
    res["warnings"] = WARN
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "cap_post.md"), "w", newline="\n").write("\n".join(md) + "\n")
    json.dump(res, open(os.path.join(OUT, "cap_post.json"), "w"), indent=1)
    print("\n".join(md))
    return res


if __name__ == "__main__":
    main()
