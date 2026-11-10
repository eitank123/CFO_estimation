"""
est3: CFO-estimation accuracy on AWGN, every estimator of a pilot layout on IDENTICAL bursts (full chain).

    python est3/run_est.py validate                        # smoke checks (chain, references, CRBs), printed
    python est3/run_est.py run --layout contig --part a     # -> est3/results/est_a.json
    python est3/run_est.py merge                            # -> est3/results/est.json

Per (layout, SNR, estimator): bias, RMSE, |error| histogram (log bins) and signed histogram, P(|e| > thresholds),
P(|e| > the CRC search half-width), MACs, measured wall time per burst (vectorised batches of 1000, one thread), and
the CRB of the layout (known pilots, unknown phase); Method 1 rows also carry the CRB with its Lh taps unknown.
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from est3 import common as C
from est3 import estimators as E

SNRS = list(range(-12, 17))
CHUNK, CHUNKS = 1000, 100
THR = (1e-4, 3e-4, 1e-3, 1 / (2 * C.L_P), 1 / C.L_P)
LOGB = np.logspace(-8, -1, 71)                    # |e| histogram edges
LINB = np.linspace(-2e-3, 2e-3, 81)               # signed e histogram edges (+ under / overflow)
SEARCH_STEP = 1.5e-4 * 512 / C.N_SYM              # the existing CRC search (polar_ber_experiment)
LAYOUT_ORDER = ("contig", "periodic", "split2x64", "dist4x32", "dist8x16")

# Method 3 grid / refinement variants: (grid, refine, iters)
ML_VARIANTS = [("fft128", "parabolic", 0), ("fft256", "none", 0), ("fft256", "parabolic", 0),
               ("fft1024", "none", 0), ("fft1024", "parabolic", 0), ("fft1024", "am", 2),
               ("fft128", "newton", 2), ("fft512", "newton", 1), ("fft512", "newton", 2),
               ("step1e-4", "parabolic", 0), ("step1e-4", "newton", 2), ("fft4096", "golden", 0)]
JOINT_SUPPORTS = [(0, 1), (0, 2), (1, 3), (1, 5), (1, 8), (2, 12)]
NN_KINDS = ("cluster", "cnn-cr", "cnn-reg")


def ml_name(g, rf, it):
    return f"ML direct {g} + {rf}" + (f" x{it}" if rf in ("newton", "am") else "")


def joint_name(P, Lh):
    return f"Joint ML Lh={Lh} (taps {-P}..{Lh - 1 - P})"


def estimators(layout):
    """(name, function(r, s, snr) -> f, MACs per burst, (P, Lh) for Method 1 rows) of a pilot layout."""
    pos = C.LAYOUTS[layout]
    if layout == "contig":
        out = [("M&M", lambda r, s, snr: E.mm(r, s, snr), E.MM_MACS, None),
               ("Jacobsen-Candan (FFT 128)", lambda r, s, snr: E.candan(r, s), E.CANDAN_MACS, None)]
        for g, rf, it in ML_VARIANTS:
            out.append((ml_name(g, rf, it), lambda r, s, snr, g=g, rf=rf, it=it: E.ml_direct(r, s, g, rf, it),
                        E.ml_direct_macs(g, rf, it), None))
        for P, Lh in JOINT_SUPPORTS:
            out.append((joint_name(P, Lh), lambda r, s, snr, P=P, Lh=Lh: E.joint_ml(r, s, P, Lh), E.joint_macs(P, Lh),
                        (P, Lh)))
        from est3 import nn as N
        for k in NN_KINDS:
            if os.path.exists(C.path("models", "cluster.pth" if k == "cluster" else f"{k}.pth")):
                out.append((N.NAMES[k], lambda r, s, snr, k=k: N.estimate(k, r, s), N.macs(k), None))
        return out
    if layout == "periodic":
        return [("Schmidl-Cox / Moose [periodic]", lambda r, s, snr: E.moose(r, C.REP_Q), E.MOOSE_MACS, None),
                ("BLUE, Morelli-Mengali 1999 [periodic]", lambda r, s, snr: E.blue_mm99(r, C.REP_Q), E.BLUE_MACS,
                 None),
                ("M&M [periodic]", lambda r, s, snr: E.mm(r, s, snr), E.MM_MACS, None),
                ("ML direct fft512 + newton x2 [periodic]", lambda r, s, snr: E.ml_direct(r, s),
                 E.ml_direct_macs(), None)]
    nb = C.BLOCKS[layout]
    return [(f"Distributed ML [{layout}]", lambda r, s, snr: E.dist_ml(r, s, pos), E.dist_ml_macs(len(pos)), None),
            (f"DVB-S2 block phase-difference [{layout}]", lambda r, s, snr: E.dvbs2_blocks(r, s, pos, nb),
             E.dvbs2_macs(len(pos), nb), None)]


def search_halfwidth(snr):
    m = int(np.ceil(4.0 * 1.3 * np.sqrt(C.crb_awgn(snr)) / SEARCH_STEP))
    return m * SEARCH_STEP


def work(task):
    layout, snr, chunk, only = task
    seed = 1_000_000 * (1 + LAYOUT_ORDER.index(layout)) + 1000 * (snr + 20) + chunk     # < 1e7: evaluation seeds
    rng = np.random.default_rng(seed)
    r, s, f, ph = C.bursts(CHUNK, snr, rng, layout)
    out = {}
    hw = search_halfwidth(snr)
    for name, fn, macs, ml in estimators(layout):
        if only and not any(o in name for o in only):         # (a later part on the same seeds = same bursts)
            continue
        t0 = time.perf_counter()
        fh = fn(r, s, snr)
        dt = time.perf_counter() - t0
        e = fh - f
        a = np.abs(e)
        out[name] = dict(n=len(e), se=float(np.sum(e ** 2)), sum=float(np.sum(e)), time=dt, macs=macs,
                         thr=[int(np.sum(a > t)) for t in THR], beyond_search=int(np.sum(a > hw)),
                         loghist=np.histogram(np.clip(a, 1.01e-8, 0.099), LOGB)[0].tolist(),
                         linhist=np.histogram(np.clip(e, LINB[0] + 1e-12, LINB[-1] - 1e-12), LINB)[0].tolist(),
                         under=int(np.sum(e < LINB[0])), over=int(np.sum(e > LINB[-1])),
                         crb_lh=float(np.sum(C.crb_unknown_taps(s, *ml, snr))) if ml else None)
    return layout, snr, out


def run(a):
    tasks = [(lay, s, c, a.only) for lay in a.layout for s in a.snrs for c in range(a.chunks)]
    acc = {}
    t0 = time.time()
    prog = C.path("logs", f"est_{a.part}.progress")
    with mp.Pool(a.workers) as pool:
        for i, (lay, snr, o) in enumerate(pool.imap_unordered(work, tasks)):
            A = acc.setdefault((lay, snr), {})
            for nm, v in o.items():
                if nm not in A:
                    A[nm] = v
                    continue
                w = A[nm]
                for f_ in ("n", "se", "sum", "time", "beyond_search", "under", "over"):
                    w[f_] += v[f_]
                for f_ in ("thr", "loghist", "linhist"):
                    w[f_] = (np.array(w[f_]) + v[f_]).tolist()
                if v["crb_lh"] is not None:
                    w["crb_lh"] += v["crb_lh"]
            with open(prog, "w") as fp:
                fp.write(f"{i + 1} {len(tasks)} {time.time() - t0:.0f}\n")    # job_progress.py: done total seconds
            if (i + 1) % 100 == 0:
                print(f"{i + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
    res = []
    for (lay, snr), A in sorted(acc.items()):
        for nm, w in A.items():
            res.append(dict(layout=lay, snr=snr, est=nm, n=w["n"], bias=w["sum"] / w["n"],
                            rmse=float(np.sqrt(w["se"] / w["n"])), p_thr=[c / w["n"] for c in w["thr"]],
                            p_beyond_search=w["beyond_search"] / w["n"], loghist=w["loghist"],
                            linhist=w["linhist"], under=w["under"], over=w["over"], macs=w["macs"],
                            us_per_burst=1e6 * w["time"] / w["n"], crb=float(C.crb_layout(snr, lay)),
                            crb_lh=w["crb_lh"] / w["n"] if w["crb_lh"] is not None else None))
    from est3.nn import TRAIN_SNRS
    json.dump(dict(thr=THR, logb=LOGB.tolist(), linb=LINB.tolist(), train_snrs=list(TRAIN_SNRS), results=res),
              open(C.path("results", f"est_{a.part}.json"), "w"))
    print("saved", C.path("results", f"est_{a.part}.json"), f"{time.time() - t0:.0f}s")
    print("EVAL DONE")


def merge(a):
    allr, meta = [], None
    for p in sorted(glob.glob(C.path("results", "est_*.json"))):
        d = json.load(open(p))
        meta = {k: v for k, v in d.items() if k != "results"}
        allr += d["results"]
    keys = {}
    for r in allr:                                 # a later part replaces the same (layout, snr, estimator)
        keys[(r["layout"], r["snr"], r["est"])] = r
    json.dump({**meta, "results": list(keys.values())}, open(C.path("results", "est.json"), "w"))
    print(len(keys), "rows ->", C.path("results", "est.json"))


# =====================================================================
# Smoke checks
# =====================================================================

def validate(a):
    import blind_cfo as bc
    rng1, rng2 = np.random.default_rng(5), np.random.default_rng(5)
    sym = C.qpsk(np.random.default_rng(1), (64, C.N_SYM))
    f = np.random.default_rng(2).uniform(-0.03, 0.03, 64)
    ph = np.random.default_rng(3).uniform(0, 6.28, 64)
    r1, rx1 = C.transmit(sym, f, ph, -3.0, rng1)
    r2, rx2 = bc.transmit_full(sym, f, ph, -3.0, rng2)
    print(f"[1] AWGN chain == blind_cfo.transmit_full: max |diff| r {np.abs(r1 - r2).max():.2e}, "
          f"rx {np.abs(rx1 - rx2).max():.2e}")
    from train_cfo_v3 import positions
    print(f"[2] split2x64 layout == train_cfo_v3 'quarter' positions: "
          f"{np.array_equal(np.asarray(positions(C.N_SYM, 'quarter')), C.LAYOUTS['split2x64'])}; layouts "
          + ", ".join(f"{k}: {len(v)} pilots {v.min()}..{v.max()}" for k, v in C.LAYOUTS.items()))

    # noiseless: every estimator returns the CFO (within its approximation)
    for lay in LAYOUT_ORDER:
        r, s, f, _ = C.bursts(200, 200.0, np.random.default_rng(6), lay)
        for name, fn, _, _ in estimators(lay):
            if "NN" in name:
                continue
            print(f"[3] noiseless {lay:9s} {name:45s} max |e| {np.abs(fn(r, s, 200.0) - f).max():.2e}")

    rng = np.random.default_rng(7)
    for snr in (-8, 0, 10):
        r, s, f, _ = C.bursts(200, snr, rng, "contig")
        ref = E.ml_direct(r, s, "fft4096", "golden", 0)
        br = E.ml_brute(r, s, 1e-6)
        d = np.abs(ref - br)
        print(f"[4] {snr:+d} dB ML reference vs dense brute grid 1e-6: max |diff| {d.max():.2e}; default "
              f"{np.abs(E.ml_direct(r, s) - ref).max():.2e}; Candan RMSE {np.sqrt(np.mean((E.candan(r, s) - f) ** 2)):.2e}"
              f" vs ref {np.sqrt(np.mean((ref - f) ** 2)):.2e} (sqrt CRB {np.sqrt(C.crb_awgn(snr)):.2e})")
        print(f"[5] joint ML Lh=1 == ML direct: max |diff| "
              f"{np.abs(E.joint_ml(r, s, 0, 1, 'fft4096', 'golden', 0) - ref).max():.2e}; Lh=3 fast vs dense lstsq: "
              f"{np.abs(E.joint_ml(r[:10], s[:10], 1, 3, 'fft4096', 'golden', 0) - E.joint_ref(r[:10], s[:10], 1, 3, 2e-5)).max():.2e}")
        print(f"[6] CRB Lh=1 unknown taps / closed form {np.mean(C.crb_unknown_taps(s, 0, 1, snr)) / C.crb_awgn(snr):.6f}"
              f"; Lh=3 {np.mean(C.crb_unknown_taps(s, 1, 3, snr)) / C.crb_awgn(snr):.3f}"
              f"; Lh=8 {np.mean(C.crb_unknown_taps(s, 1, 8, snr)) / C.crb_awgn(snr):.3f}")
    for lay in LAYOUT_ORDER:
        print(f"[7] sqrt CRB at 0 dB, {lay}: {np.sqrt(C.crb_layout(0, lay)):.3e}")
    for lay in LAYOUT_ORDER:
        for name, fn, macs, _ in estimators(lay):
            r, s, f, _ = C.bursts(1000, 0, np.random.default_rng(11), lay)
            t0 = time.perf_counter()
            fn(r, s, 0)
            print(f"[8] {name:48s} {macs:>10,} MACs  {1e6 * (time.perf_counter() - t0) / 1000:8.1f} us/burst")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "merge", "validate"])
    ap.add_argument("--layout", nargs="+", default=list(LAYOUT_ORDER))
    ap.add_argument("--snrs", type=int, nargs="+", default=SNRS)
    ap.add_argument("--chunks", type=int, default=CHUNKS)
    ap.add_argument("--part", default="a")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--only", nargs="*", default=[], help="estimators whose name contains one of these")
    a = ap.parse_args()
    {"run": run, "merge": merge, "validate": validate}[a.cmd](a)


if __name__ == "__main__":
    main()
