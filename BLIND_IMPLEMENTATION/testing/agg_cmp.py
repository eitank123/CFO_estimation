"""Testing model vs presentation model vs the 128-pilot receivers: tables for report_cmp.md (analysis only, no simulation).
Usage (from anywhere): py BLIND_IMPLEMENTATION/testing/agg_cmp.py

Receivers
  testing model      fast path off at SNR <= 0 dB (nofast), 4 phases at R = 0.15 (nph15); fast path on above 0 dB.
                     Arms of the S runs (TESTING below): 1/10 -5 ... 0 dB "T nofast"; 0.15 -4, -3 dB "T nofast", -1, 0 dB
                     "T nofast_nph4", +1 dB "T nph15". No 1/10 point above 0 dB exists in any part.
  presentation model "S blind final v2" (1/10, 0.15), "S blind final 2/5, 1/2[, best-first 32]" (2/5, 1/2), est3/plots.BLIND_RX.
                     BLER: the merged blind_ber.json (as est3/plots.blind_bler; merged 2026-11-12 19:40, before the S runs).
                     MACs: the part files carrying crit_par_macs (as est3/plots.blind_parts) WITHOUT nf10a, nf15a, nf15b:
                     their baseline arms are the srch10 / srch15 packets again (same seed and chunking, report_S note 4).
  pilot receivers    est3/plots.bler_rows (BLER) and est3/plots.pilot_macs(par=True) (4 decodes at once).

Phase-accounting undercount (small_rx, phase_keep at 1/2): after the 1/2 checkpoint of round 1 every cell keeps 2 of its
4 phases, so every cell decoded from 0 to 1/2 AFTER that point (the joining neighbours of round 1, the coarse cells of
rounds >= 2 and their neighbours) is charged 2 phases instead of 4: 2 * m_met * sh(1/2) too little per such cell, per
core the same amount per such pass (one cell per core). Only with 4 phases (nph = 4: SNR < -1 dB, or nph4 / nph15 arms).
bound_undercount() brackets it from the stored counters (passes, crit_grid, macs_par - macs_score), see its docstring.
"""
import collections
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, PROJ)
import agg_S as A                      # noqa: E402  (load, summary, tot, cp, tail, rel)
from est3 import plots as EP           # noqa: E402  (bler_rows, pilot_macs, BLIND_RX, BLIND_DIR, BLIND_JSON)

RATES = ("1/10", "0.15", "2/5", "1/2")
# testing model: (snr, part, receiver, paired arm of the same job)
TESTING = {"1/10": [(-5.0, "nf10a", "T nofast", "S blind final v2"), (-4.0, "nf10a", "T nofast", "S blind final v2"),
                    (-3.0, "nf10b", "T nofast", "S blind final v2"), (-1.0, "nf10b", "T nofast", "S blind final v2"),
                    (0.0, "nf10b", "T nofast", "S blind final v2")],
           "0.15": [(-4.0, "nf15a", "T nofast", "S blind final v2"), (-3.0, "nf15b", "T nofast", "S blind final v2"),
                    (-1.0, "nf15c", "T nofast_nph4", "T nph4"), (0.0, "nf15c", "T nofast_nph4", "T nph4"),
                    (1.0, "nn15c", "T nph15", "S blind final v2")]}
DUP = ("nf10a", "nf15a", "nf15b")      # baseline arms = srch10 / srch15 packets: left out of the presentation MACs
PILOTS = ("ML direct", "Joint ML Lh=3", "cnn-cr")   # the 3 best 128-pilot receivers by BLER (rank_pilots)
MM = "M&M"
GENIE_BLIND = "Genie (known CFO and phase)"
PILOT_NAME = {"ML direct": "ML direct", "Joint ML Lh=3": "joint ML (Lh = 3)", "cnn-cr": "CNN class. + refinement",
              "M&M": "M&M"}

# small_rx cost constants (vp.metric_macs(A), small_rx.cost_share at the checkpoints 1/2, 3/4 of the R = 1/10 profile,
# vp.MAC["cmul"] * (1 + N_SYM)); computed with BLIND_STUDY=small_cfo from blind_vp / small_rx, see report_cmp.md
COST = {"1/10": dict(m=20188, s=0.36041213, s34=0.65761839), "0.15": dict(m=22252, s=0.35861945, s34=0.69836419)}
JOIN = 4 + 4 * 1024                   # a cell's phase + de-rotation (cmul + derot)
COARSE1 = 14.5                         # coarse cells of the first block (blocks of 29 / 28 of the 201 cells, stride 2)


def nph_of(rate, snr, rx):
    if rx in ("T nofast_nph4", "T nph4") or (rx == "T nph15" and rate == "0.15"):
        return 4
    return 4 if snr < -1 else 2


# ---------------------------------------------------------------------------------------------------------- loaders
def merged(rate, rx):
    """{snr: (errors, packets)} from the merged blind_ber.json."""
    out = {}
    for x in json.load(open(EP.BLIND_JSON)):
        if x["rate"] == rate and x["rx"] == rx:
            out[x["snr"]] = (x["frame_err"], x["frames"])
    return out


def pres_rows(rate, exclude=DUP):
    """{snr: [rows]} of the presentation receiver from the non-smoke part files with crit_par_macs."""
    out = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(EP.BLIND_DIR, "blind_ber_*.json"))):
        b = os.path.basename(p)[len("blind_ber_"):-len(".json")]
        if b == "" or os.path.basename(p) == "blind_ber.json" or "smoke" in b or b in exclude:
            continue
        for r in json.load(open(p)):
            if r["rate"] == rate and r["rx"] == EP.BLIND_RX[rate] and "crit_par_macs" in r:
                out[r["snr"]].append({**r, "_part": b})
    return out


def pres_macs(rate, exclude=DUP):
    """{snr: dict(n, macs, core, core_h or None, parts)} per packet means."""
    out = {}
    for s, rows in pres_rows(rate, exclude).items():
        m = A.tot(rows, "mac_frames")
        hr = [r for r in rows if "crit_par_h_macs" in r]
        out[s] = dict(n=m, macs=A.tot(rows, "macs") / m, core=A.tot(rows, "crit_par_macs") / m,
                      core_h=A.tot(hr, "crit_par_h_macs") / A.tot(hr, "mac_frames") if hr else None,
                      parts=sorted({r["_part"] for r in rows}), rows=rows)
    return out


def testing(rate):
    """{snr: (summary, rows, paired rows, part, rx, paired rx)} of the testing model."""
    out = {}
    for snr, part, rx, base in TESTING.get(rate, []):
        t = A.load(part)
        rows = t[(rate, snr, rx)]
        out[snr] = (A.summary(rows), rows, t[(rate, snr, base)], part, rx, base)
    return out


def pilots(rate):
    """{src: {snr: dict(err, n, bler, x, macs, core)}} of the est3 128-pilot receivers."""
    out = collections.defaultdict(dict)
    for r in EP.bler_rows():
        if r["rate"] != rate:
            continue
        d = dict(err=r["frame_err"], n=r["frames"], bler=r["bler"], x=r["extra_decodes_per_frame"])
        if r["src"] in PILOTS + (MM,):
            d["macs"], d["core"] = EP.pilot_macs(rate, r["src"], r["extra_decodes_per_frame"], par=True)
        out[r["src"]][r["snr"]] = d
    return out


# ------------------------------------------------------------------------------------------------ pilot ranking
def rank_pilots(rate, ref="ML direct", min_n=500000):
    """Relative BLER of each est3 source vs ref, pooled over the SNRs both have: sum(errors) / sum(n * BLER_ref)
    (1 = as good as ref). Only sources with >= min_n packets at every common SNR with >= 20 ref errors."""
    P = pilots(rate)
    rf = P[ref]
    res = []
    for src, pts in P.items():
        if src in ("CRB 128 pilots", "Genie CFO"):
            continue
        common = [s for s in pts if s in rf and rf[s]["err"] >= 20]
        if not common:
            continue
        e = sum(pts[s]["err"] for s in common)
        x = sum(pts[s]["n"] * rf[s]["bler"] for s in common)
        nmin = min(pts[s]["n"] for s in common)
        res.append((e / x, src, e, x, nmin, len(common)))
    return sorted(res)


# --------------------------------------------------------------------------------------- undercount bound
def bound_undercount(rows, rate, snr, rx):
    """Bracket of the phase_keep undercount from the stored counters (per packet means).

    Per-core model (crit_grid = the grid part of crit_par, one cell per core, passes of <= 32 cells, LPT): a searched
    packet's grid passes are (a) the round-1 coarse pass to 1/2 at 4 phases (cost 4 m s, + one join item JOIN for its
    cells), (b) undercharged 0 -> 1/2 passes, X of them: the coarse pass of every later round (2 m s + its join item) and
    every neighbour-join pass (JOIN + 2 m s), each 2 m s + JOIN, (c) Y = passes 1/2 -> 3/4 and 3/4 -> 1 at 2 phases
    (2 m (s34 - s) and 2 m (1 - s34)). Two counters: stage passes per searched packet S = passes / searched - 1... (the
    passes counter starts at 1 per packet) = 1 + X + Y and crit_grid per searched packet G = 4 m s + JOIN + (2 m s + JOIN) X
    + c Y with c between the two continuation costs. Solving for X with c at both ends brackets X; the per-core
    undercount is 2 m s X per searched packet (the max cell of each such pass should cost 4 m s). The fixed code also
    charges these passes' cells 4 phases in crit_par_h (there 2 hypotheses per cell become 4; not bracketed here).

    Total MACs: the undercount is 2 m s per late cell. Late cells per undercharged pass: 14-15 for a later coarse pass,
    1..32 for a join pass (14-15 for the round-1 join). Bracket: N_late in [X, 32 X], cut by the grid MACs
    (macs_par - macs_score = round-1 coarse cells (4 m s + JOIN) + (2 m s + JOIN) N_late + continuation >= 0) and by
    the 201 - 14.5 cells that can be late; the nominal value uses 14.5 cells per undercharged pass."""
    c = COST[rate]
    m, s, s34 = c["m"], c["s"], c["s34"]
    n = A.tot(rows, "frames")
    mf = A.tot(rows, "mac_frames")
    ok = bool(rows) and all(f in r for r in rows for f in NEED)
    if nph_of(rate, snr, rx) == 2:                         # 2 phases: phase_keep keeps both, nothing undercounted
        return dict(nph=2, core=(0.0, 0.0), tot=(0.0, 0.0, 0.0), X=(0.0, 0.0), ns=None,
                    check=check2(rows, rate) if ok else None)
    if not ok:
        return None
    st1 = A.tot(rows, "stage_1")
    ns = n - st1                                            # searched packets (fast-path accepted: stage 1, all right)
    if ns <= 0:
        return dict(nph=4, core=(0.0, 0.0), tot=(0.0, 0.0, 0.0), X=(0.0, 0.0), ns=0)
    S = (A.tot(rows, "passes") - n) / ns                    # stage passes per searched packet
    G = A.tot(rows, "crit_grid") / ns
    a1, aL = 4 * m * s + JOIN, 2 * m * s + JOIN
    xs = []
    for cc in (2 * m * (s34 - s), 2 * m * (1 - s34)):
        xs.append((G - a1 - cc * (S - 1)) / (aL - cc))
    X = (max(0.0, min(xs)), min(S - 1, max(xs)))
    per = 2 * m * s
    core = (per * X[0] * ns / mf, per * X[1] * ns / mf)
    grid_tot = (A.tot(rows, "macs_par") - A.tot(rows, "macs_score")) / ns
    nl_max_grid = max(0.0, (grid_tot - COARSE1 * a1) / aL)
    nl_lo, nl_hi = X[0], min(32 * X[1], nl_max_grid, 201 - COARSE1)
    nl_nom = min(14.5 * 0.5 * (X[0] + X[1]), nl_hi)
    tot = tuple(per * v * ns / mf for v in (nl_lo, nl_nom, nl_hi))
    return dict(nph=4, core=core, tot=tot, X=X, ns=ns / n, S=S, G=G, nl=(nl_lo, nl_nom, nl_hi))


NEED = ("passes", "crit_grid", "macs_par", "macs_score", "stage_1", "crit_par_macs")


def check2(rows, rate):
    """Consistency check of the pass model at 2 phases (no undercount there): every 0 -> 1/2 pass costs 2 m s + JOIN,
    so X + 1 = (G - c Y) / (2 m s + JOIN) with S = 1 + X + Y; returns the X range (must lie in [0, S - 1])."""
    c = COST[rate]
    m, s, s34 = c["m"], c["s"], c["s34"]
    n = A.tot(rows, "frames")
    ns = n - A.tot(rows, "stage_1")
    if ns <= 0:
        return None
    S = (A.tot(rows, "passes") - n) / ns
    G = A.tot(rows, "crit_grid") / ns
    aL = 2 * m * s + JOIN
    xs = [(G - aL - cc * (S - 1)) / (aL - cc) for cc in (2 * m * (s34 - s), 2 * m * (1 - s34))]
    return dict(S=S, X=(min(xs), max(xs)), ns=ns / n)


def bound_rows(rows):
    return [r for r in rows if all(f in r for f in NEED)]


# --------------------------------------------------------------------------------------------- step 0 helpers
def share_above(rows, thr_bin=40):
    """Share of the mean crit_par carried by packets with crit_par >= 1e6 (bins >= 40 of the 0.05-decade ph_ / pg_
    histograms), split into right-decoded (pg_) and the rest (ph_ - pg_: no accepted right decode). Sums from the bin
    geometric centres, bracketed by the bin edges. Returns dict with counts and shares (lo, mid, hi)."""
    E = A.PH_EDGES
    ph = np.array([A.tot(rows, f"ph_{b:02d}") for b in range(100)], float)
    pg = np.array([A.tot(rows, f"pg_{b:02d}") for b in range(100)], float)
    fl = ph - pg
    total = A.tot(rows, "crit_par_macs")
    lo_e, hi_e = E[:-1], E[1:]
    mid = np.sqrt(lo_e * hi_e)
    sel = np.arange(100) >= thr_bin
    out = dict(n=ph.sum(), total=total, mean=total / ph.sum())
    for k, h in (("all", ph), ("right", pg), ("failed", fl)):
        out[k] = dict(count=int(h[sel].sum()), share=tuple(float((h[sel] * e[sel]).sum() / total) for e in (lo_e, mid, hi_e)))
    out["ph_sum_mid"] = float((ph * mid).sum() / total)     # check: the histogram-centre sum vs the exact sum
    return out


def four_at_once(rows):
    """Per-core gain of decoding blind's CA-SCL decodes 4 at a time (as est3 pilot_macs): per decode critical path
    c_d = crit_par_dec / decodes. Upper bound 0.75 * crit_par_dec / packet (every decode in a full group of 4);
    pilot-model analog 0.75 c_d (d - 1) (the first decode alone, then the rest 4 at a time, rounding not modelled,
    as pilot_macs); with the rounding the gain is at least 0.75 c_d (d - 1) - 0.75 c_d min(1, d - 1).
    Total-MAC cost of the same (pilot_macs rule): + min(d - 1, 1.5) decodes of macs_dec / decodes."""
    n, mf = A.tot(rows, "frames"), A.tot(rows, "mac_frames")
    d = A.tot(rows, "decodes") / n
    cd = A.tot(rows, "crit_par_dec") / A.tot(rows, "decodes")
    dec_tot = A.tot(rows, "macs_dec") / A.tot(rows, "decodes")
    core = A.tot(rows, "crit_par_macs") / mf
    return dict(d=d, cd=cd, core=core, dec_share=A.tot(rows, "crit_par_dec") / A.tot(rows, "crit_par_macs"),
                ub=0.75 * cd * d, analog=0.75 * cd * (d - 1), lb=max(0.0, 0.75 * cd * (d - 1) - 0.75 * cd * min(1.0, d - 1)),
                tot_cost=min(d - 1, 1.5) * dec_tot, macs=A.tot(rows, "macs") / mf)


def chunk_match():
    """The undetected errors of T win4 (srch10) and T nofast_spec (nf10a) at 1/10 -5 dB: their chunk, identified by the
    baseline arm of the same chunk (rows are written chunk by chunk: Genie, baseline, variants)."""
    res = {}
    for part, rx in (("srch10", "T win4"), ("nf10a", "T nofast_spec")):
        rows = [r for r in json.load(open(os.path.join(A.ROOT, f"blind_ber_{part}.json"))) if r["rate"] == "1/10" and r["snr"] == -5.0]
        blocks, cur = [], []
        for r in rows:
            if "Genie" in r["rx"] and cur:
                blocks.append(cur)
                cur = []
            cur.append(r)
        blocks.append(cur)
        hits = []
        for k, b in enumerate(blocks):
            v = next(r for r in b if r["rx"] == rx)
            if v["undetected"]:
                base = next(r for r in b if r["rx"] == "S blind final v2")
                hits.append(dict(block=k, und=v["undetected"], err=v["frame_err"],
                                 sig=(base["frames"], base["out_coarse"], base["out_coarse_1e3"], round(base["se_coarse"], 6),
                                      base["frame_err"], base["macs"], base["crit_par_macs"])))
        res[(part, rx)] = dict(hits=hits, nblocks=len(blocks))
    return res


def M(v, d=3):
    return "-" if v is None else f"{v / 1e6:.{d}f}"


def pct(a, b):
    return 100 * (a / b - 1)


def bler_txt(k, n):
    if k == 0:
        return f"0 / {n} (< {3 / n:.1e})"
    lo, hi = A.cp(k, n)
    return f"{k} / {n} = {k / n:.2e} [{lo:.1e}, {hi:.1e}]"


if __name__ == "__main__":
    print("## Pilot ranking (pooled BLER relative to ML direct over the SNRs where ML direct has >= 20 errors)\n")
    print("| R | source | rel. BLER vs ML direct | errors / expected at ML BLER | min packets per SNR | SNRs |")
    print("|---|---|---|---|---|---|")
    for rate in RATES:
        for q, src, e, x, nmin, ns in rank_pilots(rate)[:8]:
            print(f"| {rate} | {src} | {q:.2f} | {e} / {x:.0f} | {nmin} | {ns} |")

    print("\n## BLER table\n")
    print("| R | SNR | testing model | presentation model | ML direct | joint ML | CNN-cr | M&M | genie (blind) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for rate in RATES:
        T = testing(rate)
        Pm = merged(rate, EP.BLIND_RX[rate])
        G = merged(rate, GENIE_BLIND)
        P = pilots(rate)
        for s in sorted(set(T) | set(Pm)):
            t = bler_txt(T[s][0]["err"], T[s][0]["n"]) + f" ({T[s][4][2:]})" if s in T else "-"
            pm = bler_txt(*Pm[s]) if s in Pm else "-"
            ps = [bler_txt(P[src][s]["err"], P[src][s]["n"]) if s in P.get(src, {}) else "-" for src in PILOTS + (MM,)]
            g = bler_txt(*G[s]) if s in G else "-"
            print(f"| {rate} | {s:g} | {t} | {pm} | " + " | ".join(ps) + f" | {g} |")

    print("\n## MAC summary: testing vs presentation (per packet means, M; pre-fix accounting for every blind number)\n")
    print("| R | SNR | testing per core | testing crit_par_h | presentation per core | per core change | testing total | "
          "presentation total | total change | paired (same packets) per core / total | ML direct per core | best pilot per core | "
          "testing / ML | testing / best pilot | testing packets | presentation packets (parts) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for rate in ("1/10", "0.15"):
        T = testing(rate)
        Pr = pres_macs(rate)
        P = pilots(rate)
        for s in sorted(set(T) | set(Pr)):
            pr = Pr.get(s)
            ml = P["ML direct"].get(s, {}).get("core")
            best = min(((P[src][s]["core"], src) for src in PILOTS + (MM,) if s in P.get(src, {})), default=(None, None))
            if s in T:
                sm, rows, brows, part, rx, base = T[s]
                dc, dt = A.rel(rows, brows, "crit_par_macs"), A.rel(rows, brows, "macs")
                pair = f"{dc[0]:+.1f} / {dt[0]:+.1f} % (vs {base[2:] if base.startswith('T ') else 'S blind final v2'})"
                cc = f"{pct(sm['core'], pr['core']):+.1f} %" if pr else "-"
                ct = f"{pct(sm['macs'], pr['macs']):+.1f} %" if pr else "-"
                r1 = f"{sm['core'] / ml:.2f}" if ml else "-"
                r2 = f"{sm['core'] / best[0]:.2f} ({PILOT_NAME[best[1]]})" if best[0] else "-"
                print(f"| {rate} | {s:g} | {M(sm['core'])} | {M(sm['core_h'])} | {M(pr['core']) if pr else '-'} | {cc} | {M(sm['macs'])} | "
                      f"{M(pr['macs']) if pr else '-'} | {ct} | {pair} | {M(ml)} | {M(best[0])} | {r1} | {r2} | {sm['n']} ({rx[2:]}) | "
                      f"{pr['n'] if pr else '-'} ({', '.join(pr['parts']) if pr else ''}) |")
            else:
                r1 = f"{pr['core'] / ml:.2f}" if ml else "-"
                print(f"| {rate} | {s:g} | - | - | {M(pr['core'])} | - | - | {M(pr['macs'])} | - | - | {M(ml)} | {M(best[0])} | "
                      f"(presentation / ML {r1}) | - | - | {pr['n']} ({', '.join(pr['parts'])}) |")

    print("\n## Per-core change with the undercount bracket added to both sides (testing vs presentation)\n")
    print("| R | SNR | testing per core pre-fix -> bracket [M] | presentation per core pre-fix -> bracket [M] | change pre-fix | change with the bracket |")
    print("|---|---|---|---|---|---|")
    for rate in ("1/10", "0.15"):
        T, Pr = testing(rate), pres_macs(rate)
        for s in sorted(T):
            if s not in Pr:
                continue
            sm, rows = T[s][0], T[s][1]
            bt = bound_undercount(rows, rate, s, T[s][4])
            pb = bound_rows(Pr[s]["rows"])
            bp = bound_undercount(pb, rate, s, "S blind final v2")
            if bt is None or bp is None:
                continue
            pc = Pr[s]["core"]                                  # bracket from the rows with the counters, added
            t_lo, t_hi = sm["core"] + bt["core"][0], sm["core"] + bt["core"][1]
            p_lo, p_hi = pc + bp["core"][0], pc + bp["core"][1]
            ch = sorted((pct(t_lo, p_hi), pct(t_hi, p_lo)))
            print(f"| {rate} | {s:g} | {M(sm['core'])} -> {M(t_lo)} - {M(t_hi)} | {M(pc)} -> {M(p_lo)} - {M(p_hi)} | "
                  f"{pct(sm['core'], pc):+.1f} % | {ch[0]:+.1f} to {ch[1]:+.1f} % |")

    print("\n## Presentation MACs as est3/plots.macs_plot draws them (all parts) vs without the duplicated parts\n")
    print("| R | SNR | per core all parts | per core without nf10a/nf15a/nf15b | total all parts | total without |")
    print("|---|---|---|---|---|---|")
    for rate in RATES:
        a, b = pres_macs(rate, exclude=()), pres_macs(rate)
        for s in sorted(a):
            if a[s]["n"] != b[s]["n"]:
                print(f"| {rate} | {s:g} | {M(a[s]['core'])} | {M(b[s]['core'])} | {M(a[s]['macs'])} | {M(b[s]['macs'])} |")

    print("\n## MACs of the presentation model at 2/5 and 1/2 and the pilots (testing = presentation there)\n")
    print("| R | SNR | presentation per core | presentation total | ML direct per core / total | best pilot per core | presentation / ML per core |")
    print("|---|---|---|---|---|---|---|")
    for rate in ("2/5", "1/2"):
        Pr, P = pres_macs(rate), pilots(rate)
        for s in sorted(Pr):
            ml = P["ML direct"].get(s, {})
            best = min(((P[src][s]["core"], src) for src in PILOTS + (MM,) if s in P.get(src, {})), default=(None, None))
            print(f"| {rate} | {s:g} | {M(Pr[s]['core'])} | {M(Pr[s]['macs'])} | {M(ml.get('core'))} / {M(ml.get('macs'))} | "
                  f"{M(best[0])} ({PILOT_NAME.get(best[1], '-')}) | {Pr[s]['core'] / ml['core']:.2f} |" if ml else
                  f"| {rate} | {s:g} | {M(Pr[s]['core'])} | {M(Pr[s]['macs'])} | - | - | - |")

    print("\n## Phase-accounting undercount bracket (per packet means)\n")
    print("| R | SNR | receiver | nph | searched share | stage passes / searched | X (undercharged passes / searched) | "
          "per core undercount [M] | per core % of crit_par | total undercount lo / nominal / hi [M] | total % (lo / nom / hi) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for rate in ("1/10", "0.15"):
        T, Pr = testing(rate), pres_macs(rate)
        items = [(s, "testing " + T[s][4][2:], T[s][1]) for s in T]
        items += [(s, "presentation", bound_rows(Pr[s]["rows"])) for s in Pr]
        for s, lab, rows in sorted(items, key=lambda x: (x[0], x[1])):
            rx = "T " + lab.split(" ", 1)[1] if lab.startswith("testing") else "S blind final v2"
            b = bound_undercount(rows, rate, s, rx)
            if b is None:
                print(f"| {rate} | {s:g} | {lab} | 4 | no rows with passes / crit_grid / macs_par / macs_score | | | | | | |")
                continue
            mf = A.tot(rows, "mac_frames") if rows else 1
            core, tot = (A.tot(rows, "crit_par_macs") / mf, A.tot(rows, "macs") / mf) if rows else (1, 1)
            if b is None:
                print(f"| {rate} | {s:g} | {lab} | - | counters missing | | | | | | |")
                continue
            if b["nph"] == 2:
                k = b["check"]
                ck = f"model check: S {k['S']:.2f}, X {k['X'][0]:.2f} - {k['X'][1]:.2f} (must be in [0, S - 1])" if k else "- (no counters)"
                print(f"| {rate} | {s:g} | {lab} | 2 | {k['ns'] if k else 0:.3f} | {ck} | - | 0 (2 phases: phase_keep keeps both) | 0 % | 0 | 0 % |")
                continue
            print(f"| {rate} | {s:g} | {lab} | 4 | {b['ns']:.3f} | {b['S']:.2f} | {b['X'][0]:.2f} - {b['X'][1]:.2f} | "
                  f"{M(b['core'][0], 4)} - {M(b['core'][1], 4)} | +{100 * b['core'][0] / core:.1f} to +{100 * b['core'][1] / core:.1f} % | "
                  f"{M(b['tot'][0])} / {M(b['tot'][1])} / {M(b['tot'][2])} | +{100 * b['tot'][0] / tot:.1f} / +{100 * b['tot'][1] / tot:.1f} / "
                  f"+{100 * b['tot'][2] / tot:.1f} % |")

    print("\n## Step 0a: share of the mean crit_par carried by packets >= 1 M per core (bin centres [edges])\n")
    print("| R | SNR | receiver | part | packets | mean per core [M] | packets >= 1 M (right / failed) | share of mean: all | right-decoded | failed | hist check |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for rate, snr, items in (("0.15", -4.0, (("srch15", "S blind final v2"), ("srch15", "T win4"), ("nf15a", "T nofast"), ("nf15a", "T nofast_spec"))),
                             ("1/10", -5.0, (("srch10", "S blind final v2"), ("srch10", "T win4"), ("nf10a", "T nofast"), ("nf10a", "T nofast_spec")))):
        for part, rx in items:
            rows = A.load(part)[(rate, snr, rx)]
            q = share_above(rows)
            f = lambda d: f"{100 * d['share'][1]:.1f} % [{100 * d['share'][0]:.1f}, {100 * d['share'][2]:.1f}]"
            print(f"| {rate} | {snr:g} | {rx} | {part} | {int(q['n'])} | {M(q['mean'])} | {q['all']['count']} ({q['right']['count']} / "
                  f"{q['failed']['count']}) | {f(q['all'])} | {f(q['right'])} | {f(q['failed'])} | {q['ph_sum_mid']:.3f} |")

    print("\n## Step 0b: blind decodes 4 at once (offline bound from crit_par_dec)\n")
    print("| R | SNR | receiver | dec / pk | decode share of crit_par | per core now [M] | gain: upper bound 0.75 crit_par_dec | "
          "pilot-model analog 0.75 c_d (d - 1) | with rounding at least | per core after (analog) | total + min(d-1, 1.5) decodes |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    pts = [("1/10", s, T_[1], T_[4]) for s, T_ in testing("1/10").items()] + [("0.15", s, T_[1], T_[4]) for s, T_ in testing("0.15").items()]
    pts += [("1/10", -5.0, A.load("srch10")[("1/10", -5.0, "S blind final v2")], "S blind final v2"),
            ("0.15", -4.0, A.load("srch15")[("0.15", -4.0, "S blind final v2")], "S blind final v2"),
            ("0.15", -3.0, A.load("srch15")[("0.15", -3.0, "S blind final v2")], "S blind final v2")]
    for rate, s, rows, rx in pts:
        q = four_at_once(rows)
        print(f"| {rate} | {s:g} | {rx} | {q['d']:.2f} | {100 * q['dec_share']:.0f} % | {M(q['core'])} | -{M(q['ub'])} ({-100 * q['ub'] / q['core']:.0f} %) | "
              f"-{M(q['analog'])} ({-100 * q['analog'] / q['core']:.1f} %) | -{M(q['lb'])} | {M(q['core'] - q['analog'])} | "
              f"+{M(q['tot_cost'])} (+{100 * q['tot_cost'] / q['macs']:.1f} %) |")

    print("\n## Step 0c: chunk of the undetected errors (1/10 -5 dB, seed 7701)\n")
    for (part, rx), v in chunk_match().items():
        for h in v["hits"]:
            print(f"- {part} {rx}: block {h['block']} of {v['nblocks']} (file order), undetected {h['und']}, frame errors {h['err']}; "
                  f"baseline arm of that chunk: frames {h['sig'][0]}, out_coarse {h['sig'][1]}, out_coarse_1e3 {h['sig'][2]}, "
                  f"se_coarse {h['sig'][3]}, errors {h['sig'][4]}, macs {h['sig'][5]:.6e}, crit_par {h['sig'][6]:.6e}")
