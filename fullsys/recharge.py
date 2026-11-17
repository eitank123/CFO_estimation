"""
Offline bound on the MACs the checkpoint NN used but did not charge in run_blind_fs runs WITHOUT --charge-all
(small_rx ck_charge_all False). Decisions / BLER of those runs stay; only the MACs per core are bracketed.

    The NN at CK_FR[ck_nn] (small_rx ck_features: robust z, softmax, cumulative-mass shortlist over EVERY cell) runs in
    round 0 of the grid search on every packet that reaches it (fast path failed), but round 0 charges only its alive
    cells (2/5: first_k = 32 of G; 0.15 --cknn fmt: one batch block of ~32). The missing charge of a packet is exactly 0
    when it leaves the search after its LAST round (its last round charges every cell up to the NN checkpoint), so
        stage 1 (fast path) and stage >= 3 (final / rescue, all rounds done): 0
        stage 2 (accepted in the grid search): 0 if it ended in the last round, else <= the round-0 charge D below
    D (one round-0 packet, n0 alive cells charged with nph phases to share sh0, nU = G - n0 others, Kc cores):
        macs    nU (join + met),                 join = cmul (1 + n_sym), met = m_met nph sh0
        c_d4a   (ceil((n0 + nU) / Kc) - ceil(n0 / Kc)) met + ceil(nU / Kc) join            (crit; small_rx _par LPT)
        c_hd4a  (ceil((n0 + nU) nph / Kc) - ceil(n0 nph / Kc)) met / nph + ceil(nU nph / Kc) join   (crit_gh)
    (= what ck_charge_all adds in round 0; the round is not logged, so this is an UPPER bound: every stage-2 packet in
    round 0). With the part's --dump: a packet with a decode row n_alive > n0 was in a later round (first_k: then 0;
    batch: nU <= G - max n_alive), and the max per packet is bounded per packet instead of max + D.

Prints per part and point: frames, stage-2 accepted, the reported mean / max MACs per core (STD_CORE of the profile)
and the upper bounds. The exact values: the --charge-all reruns (jobs/fs-q*.sh, parts <part>ca, same seeds).

    BLIND_STUDY=small_cfo python fullsys/recharge.py fs-g13m08 fs-g13m06 ...        (parts; results in fullsys/results)

Builds the formats' codes (blind_fmt) to get m_met / sh0: run on the cluster (a Run:ai job), not on the login node.
"""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import run_blind_fs as rbf             # noqa: E402


def opts(a):
    """run_blind_fs's o dict from a part's meta args (older parts: missing keys at their defaults)."""
    return dict(crc=a.get("crc", 32), beta=a["beta"], cfo_max=a["cfo_max"], extra_in_fz=a.get("extra_in_fz", False),
                rho=a.get("rho", "scaled"), fzstop=a.get("fzstop", "off"), spec=a.get("spec", "off"),
                cknn=a.get("cknn", "keep"), ck=a.get("ck", "useful"), bpsk_phase=a.get("bpsk_phase", "sq"),
                sub=a.get("sub", 50), rx=a.get("rx"), dump=None, chan=not a.get("no_chan_intlv", False),
                design=a.get("design", "pw"), design_snr=a.get("design_snr"), cap_core=a.get("cap_core"),
                cknn_name=a.get("cknn_name"), ck_c=a.get("ck_c"),
                sps=rbf.sps_json(a["sps"]) if a.get("sps") else None)


def unit(fmt, F, o, snr):
    """Round-0 constants of the receiver at snr, as small_rx sets them up (lines: the setup of _small_receive and the
    rounds of the grid search): None if it has no checkpoint NN. Asserts the cases this bound does not model."""
    import blind_cfo as bc
    import blind_fast as bf
    import blind_vp as vp
    import small_rx as sr
    sps, prof = rbf.rx_spec(fmt, F, o, o.get("rx"))
    p = {**sr.DEFAULT, **sps}
    snr = snr + p["snr_err"]                                          # (every SNR-dependent setting sees it)
    p["code_rate"] = p["rate"]
    p["rate"] = bc.PROFILE.get(p["rate"], p["rate"])
    for key in sr.PER_RATE:
        if isinstance(p[key], dict):
            p[key] = p[key].get(p["rate"])
    if isinstance(p["nph"], dict):
        p["nph"] = p["nph"].get(p["code_rate"])
        if isinstance(p["nph"], tuple):
            p["nph"] = p["nph"][0] if snr < p["nph"][1] else None
    cnn = p["ck_nn"]
    if cnn is None:
        return None, prof
    assert not (p["equiv"] or p["pilots"] or p["coarse"] or p["pre_keep"] or p["top_k"] or p["nn_keep"]), \
        "recharge: equiv / pilots / coarse / pre_keep / top_k / nn_keep not modelled"
    ckf = sr.CK_FR[cnn]
    for pr_ in (p["phase_keep"], p["race_phase"], p["beam"], p["keep_early"]):
        assert pr_ is None or pr_[0] > ckf, "recharge: a phase / beam pruning before the NN checkpoint"
    with F:
        k = p["kstep"] or bf.grid_step(p["rate"], snr)
        G = len(bf.grid(k)["f"])
        nph = p["nph"] or (4 if snr < -1 else 2)
        qs = np.arange(nph) * (2 if nph == 2 else 1)
        if p["nopi"]:
            qs = np.concatenate([qs, qs + 4])
        elif p["bpsk_sq"]:
            qs = 2 * qs[qs < 2]
        nph = len(qs)
        code = F.code
        fsn = bf.FastSC(bf.fast_sc(code.A).frozen)
        fsn.split = sr.SPLIT
        lv = np.array([h for _, h in sr.leaves(fsn.plan, 0, bc.N_BITS, [], sr.SPLIT)])
        cks = [1.0] if not p["ck"] else sorted(set(p["ck"]) | {1.0})
        cks = sorted({c for c in cks if c > ckf} | {ckf, 1.0})
        if p["beam"] is not None:
            cks = sorted(set(cks) | {p["beam"][0], 0.75})
            if p["keep_early"] is not None:
                cks = sorted(set(cks) | {p["keep_early"][0]})
        if p["phase_keep"] is not None:
            cks = sorted(set(cks) | {p["phase_keep"][0]})
        if p["race_phase"] is not None:
            cks = sorted(set(cks) | {p["race_phase"][0], 1.0})
        if p["ck_useful"]:
            ul_ = np.cumsum(~bc.FMT.pre)[lv - 1]
            nl = [max(1, int((ul_ <= c * ul_[-1] + 1e-9).sum())) for c in cks]
            fr = lv[np.array(nl) - 1] / bc.N_BITS
        else:
            nl = [max(1, int((lv <= c * bc.N_BITS).sum())) for c in cks]
            fr = lv[np.array(nl) - 1] / bc.N_BITS
        sh = sr.cost_share(fsn.plan, fr) if p["cost"] == "tree" else fr
        sh0 = float(np.atleast_1d(sh)[cks.index(ckf)])
        m_met = float(vp.metric_macs(code.A))
        join = float(vp.MAC["cmul"] * (1 + bc.N_SYM))
    ncore = p["cores"] or (p["batch"][0] if p["batch"] else None)
    Kc = ncore or G
    if p["first_k"]:
        n0, kind = min(int(p["first_k"]), G), "first_k"
    elif p["batch"]:
        n0, kind = min(len(b) for b in np.array_split(np.arange(G), -(-G // p["batch"][0]))), "batch"
    else:
        n0, kind = G, "all"
    return dict(G=G, nph=nph, n0=n0, kind=kind, Kc=Kc, sh0=sh0, m_met=m_met, join=join, met=m_met * nph * sh0), prof


def delta(u, nU, n0=None):
    """(macs, c_d4a, c_hd4a) added by ck_charge_all for nU extra cells next to n0 charged ones (arrays ok)."""
    n0 = u["n0"] if n0 is None else n0
    nU = np.asarray(nU, float)
    Kc, nph, met, join = u["Kc"], u["nph"], u["met"], u["join"]
    c = lambda x: np.ceil(x / Kc)
    dm = nU * (met + join)
    dd = (c(n0 + nU) - c(n0)) * met + c(nU) * join
    dh = (c((n0 + nU) * nph) - c(n0 * nph)) * met / nph + c(nU * nph) * join
    return dm, dd, dh


def dump_bound(part, pt, u, std):
    """Per-packet upper bound from the part's dump (None if absent): (mean, max) of the std MACs per core."""
    dd = os.path.join(rbf.RESULTS, f"blind_fs_{part}_dump")
    if not os.path.isdir(dd):
        return None
    vals = []
    for ch in pt["chunks"]:
        tag = f"{pt['fmt']}_{pt['esn0']:+.2f}_c{ch['c']:05d}"
        fp, fr = os.path.join(dd, f"pk_{tag}.npz"), os.path.join(dd, f"rows_{tag}.npz")
        if not os.path.exists(fp):
            return None
        P = np.load(fp)
        n = len(P["pk"])
        nal = np.full(n, -1)
        if os.path.exists(fr):
            R = np.load(fr)
            if "d_pk" in R.files:
                np.maximum.at(nal, R["d_pk"].astype(int), R["d_n_alive"].astype(int))
        s2 = P["stage"] == 2
        if u["kind"] == "first_k":
            nU = np.where(s2 & (nal <= u["n0"]), u["G"] - u["n0"], 0)
        else:
            nU = np.where(s2, u["G"] - np.maximum(nal, u["n0"]), 0)
        dm, d4, dh = delta(u, np.maximum(nU, 0))
        vals.append(P[std].astype(float) + (d4 if std == "c_d4a" else dh))
    v = np.concatenate(vals)
    return float(v.mean()), float(v.max())


def main():
    import blind_cfo as bc
    assert bc.STUDY == "small_cfo", "run with BLIND_STUDY=small_cfo"
    parts = sys.argv[1:]
    if not parts:
        sys.exit(__doc__)
    print(f"{'part':16s} {'Es/N0':>6s} {'frames':>7s} {'s2acc':>6s} | {'std':6s} {'mean':>8s} {'up':>8s} {'up_d':>8s} "
          f"| {'max':>8s} {'up':>8s} {'up_d':>8s} | D/core (M)  G nph n0 Kc sh0")
    for part in parts:
        fj = os.path.join(rbf.RESULTS, f"blind_fs_{part}.json")
        if not os.path.exists(fj):
            print(f"{part:16s} missing ({fj})")
            continue
        doc = json.load(open(fj))
        m = doc["meta"]
        if m.get("charge_all"):
            print(f"{part:16s} already --charge-all (honest)")
            continue
        o = opts(m["args"])
        fmt = m["fmt"]
        F = rbf.get_fmt(fmt, o)
        for pt in doc["points"]:
            u, prof = unit(fmt, F, o, pt["esn0"])
            std = rbf.STD_CORE[prof]
            n = pt["frames"]
            mean, mx = pt["sum_" + std] / n, pt["max_" + std]
            if u is None:
                print(f"{part:16s} {pt['esn0']:+6.2f} {n:7d}      - | {std:6s} {mean / 1e6:8.4f} (no checkpoint NN)")
                continue
            s2 = pt["stages"][1]["right"] + pt["stages"][1]["wrong"]
            _, d4, dh = delta(u, u["G"] - u["n0"])
            D = float(d4 if std == "c_d4a" else dh)
            db = dump_bound(part, pt, u, std)
            ud = f"{db[0] / 1e6:8.4f}" if db else "       -"
            xd = f"{db[1] / 1e6:8.3f}" if db else "       -"
            print(f"{part:16s} {pt['esn0']:+6.2f} {n:7d} {s2:6d} | {std:6s} {mean / 1e6:8.4f} "
                  f"{(mean + s2 * D / n) / 1e6:8.4f} {ud} | {mx / 1e6:8.3f} {(mx + D) / 1e6:8.3f} {xd} | "
                  f"{D / 1e6:.4f} {u['G']} {u['nph']} {u['n0']} {u['Kc']} {u['sh0']:.3f}", flush=True)
    print("mean / max: reported MACs per core (M); up: + every stage-2 packet charged D (JSON only); up_d: per packet "
          "from the dump (later rounds by n_alive). Exact: the --charge-all rerun.")


if __name__ == "__main__":
    main()
