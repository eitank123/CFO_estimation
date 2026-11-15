"""
est4: BLER of the fair pilot-aided receivers (pilots OUTSIDE the 1024-symbol packet, energy charged; DVB-RCS2-style
layouts; Wiener phase noise) with est3's back-end, BLIND_IMPLEMENTATION/testing/results/expected_est4.md:

    f_hat from the receiver's own known symbols (est4/estimators.py), on its own burst (est4/common.py layouts)
    -> pre-MF correction at f_hat over the whole burst (est4.common.premf)
    -> per CFO hypothesis f_h: the receiver's phase model (const / interp2 / track / genie) on its known symbols at f_h,
       LLRs of the 1024 data symbols, CA-SCL-8 (N = 2048, CRC-16), CRC + re-encoding check (blind_fast.rho_min and the
       blind receivers' per-rate RHO_N table, at the simulated per-symbol Es/N0)
    -> est3's fair "PM+all" CRC search: decode at f_hat first; for the packets not accepted, score every neighbour
       hypothesis by the list-1 Fast-SSC metric (KP = 32 at a time: metric_rounds) and decode all of them in metric
       order, stopping at the first accepted pass. Neighbours: f_hat + k STEP (0 < |k| <= M), M = max(1, ceil(4 x 1.3
       sqrt(CRB_own) / STEP)) with the CRB of the receiver's own known positions in its burst (unknown phase); the
       genie has no search (M = 0). 2-field layouts (split64, prepost16; 2026-11-15 after e4-smoke: split64 491/800
       errors from lobe jumps of 1/1088): the union over lobes m = -LOBES .. LOBES of f_hat + m / D_lobe + k STEP,
       |k| <= M, without (0, 0), so the decoder chooses the lobe (Barbieri-Colavolpe 2007): (2 LOBES + 1)(2M + 1) - 1
       metric passes per failing packet (split64 at M = 3: 48 = 2 rounds (LOBES = 3) instead of 6 = 1 round)
    -> phase model of the receiver at each hypothesis: --track kalman (default; RTS smoother with q = 2 pi pn, est4/
       estimators.py) or sw (the first sliding-window version, --track-w)
Measurement only (no effect on decisions or MACs): in_window / in_search = packets with |f_hat - f| <= M STEP / with
some lobe hypothesis f_hat + m / D_lobe within M STEP of f; for 2-field layouts lobe_err (|f_hat - f| > 1 / (2 D_lobe)),
nc_lobe_err (the per-block noncoherent estimate off by more than half a lobe) and nc_pick_err (the lobe of the
joint-ML candidate set nearest the noncoherent estimate is wrong).

Packets: IDENTICAL data, CFO, phase (and Wiener phase-noise process) for every receiver. The bursts of the different
layouts have different lengths, so each layout gets its own known symbols and noise from a dedicated rng stream (seeded
from (seed, rate, SNR, chunk, layout)): the noise differs BETWEEN layouts (it cannot be the same: the bursts differ),
the sources of one layout share one burst. The phase-noise path is drawn once per batch for the longest burst and each
layout takes its centred piece (the same process at the same time from the burst centre, zero at every burst centre).
pn is not in the seed: runs at different pn with the same seed have the same packets and the same (scaled) path.
Results are independent of which other sources run.

    python est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --chunks 2 --pn 1e-4 --part e4-smoke-b
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                                   # noqa: E402

from est4 import common as C                                         # noqa: E402
from est4 import estimators as E                                     # noqa: E402

SEARCH_STEP = 1.5e-4 * 512 / C.N_SYM                                 # = est3.run_bler.SEARCH_STEP (7.5e-5)
KP = E.KP
RATE_IDX = {"1/10": 0, "0.15": 1, "2/5": 1, "1/2": 2}               # est3.run_bler.RATE_IDX (0.15 and 2/5 share 1:
                                                                     # use different --seed per rate)
_FIELDS = ("frames", "frame_err", "undetected", "extra_decodes", "se_first", "se_final", "crc_pass", "crc_pass_wrong",
           "re_caught", "re_lost", "time_est", "metric_evals", "metric_rounds", "in_window", "in_search", "lobe_err",
           "nc_lobe_err", "nc_pick_err")
LOBES = 3                                                            # lobe hypotheses m = -LOBES .. LOBES (2-field)


def window(src, snr):
    """CRC-search half-width M (steps) of a source: from the CRB of its own known positions, at least 1; genie 0."""
    lay = C.SOURCES[src][0]
    if lay == "none":
        return 0
    crb = C.crb_known(snr, C.layout(lay)["known_idx"])
    return max(1, int(np.ceil(4.0 * 1.3 * np.sqrt(crb) / SEARCH_STEP)))


def hypotheses(src, snr, lobes):
    """CFO offsets from f_hat of the search (without 0), in (|m|, m, |k|, k) order (the metric decides the order of
    the decodes; this order only breaks ties): k STEP, |k| <= M, and for 2-field layouts m / D_lobe + k STEP,
    0 < |m| <= lobes. Returns (offsets, M, D_lobe)."""
    M = window(src, snr)
    D = C.lobe_D(C.SOURCES[src][0]) if lobes else 0.0
    ms = range(-lobes, lobes + 1) if D else (0,)
    hyp = sorted([(m, k) for m in ms for k in range(-M, M + 1) if (m, k) != (0, 0)],
                 key=lambda t: (abs(t[0]), t[0], abs(t[1]), t[1]))
    return np.array([(m / D if m else 0.0) + k * SEARCH_STEP for m, k in hyp]), M, D


def work(task):
    rate, snr, chunk, frames, min_err, sources, seed, pn, track_w, track, lobes = task
    q = 2 * np.pi * pn                                     # Wiener phase variance per symbol (kalman: true linewidth)
    from blind_fast import fast_sc, rho_min
    from blind_ber import RHO_N                            # the blind receivers' per-rate threshold (same check)
    from polar import PolarCode
    key = [seed, RATE_IDX[rate], int(round(10 * snr)) + 1000, chunk]
    rng = np.random.default_rng([40] + key)                # data, CFO, phase
    rpn = np.random.default_rng([41] + key)                # the phase-noise path (drawn only if pn > 0)
    lays = [l for l in C.LAYOUTS if any(C.SOURCES[s][0] == l for s in sources)]
    rlay = {l: np.random.default_rng([42] + key + [C.LAYOUT_ID[l]]) for l in lays}   # known symbols + noise
    A = C.CODES[rate]
    code = PolarCode(C.N_BITS, A, 16, 8)
    fsc = fast_sc(A)
    s2 = 10 ** (-snr / 10)                                 # complex noise variance at the MF output
    sl = 10 ** (snr / 10)
    thr = max(rho_min(snr), float(np.interp(snr, *zip(*RHO_N[rate]))) * np.sqrt(sl / (1 + sl)))
    st = {s: {k: (0.0 if k in ("se_first", "se_final", "time_est") else 0) for k in _FIELDS} for s in sources}
    B = 100
    while st[sources[0]]["frames"] < frames and min(v["frame_err"] for v in st.values()) < min_err:
        data = rng.integers(0, 2, (B, A), dtype=np.uint8)
        cw = code.encode(data)[:, C.INTERLEAVER]
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        f = rng.uniform(-C.MAX_CFO, C.MAX_CFO, B)
        ph = rng.uniform(0, 2 * np.pi, B)
        phi = C.wiener(B, C.KMAX, pn, rpn) if pn > 0 else None
        bur = {}
        for l in lays:
            bs, _, _, ks = C.make_burst(l, sym, rlay[l])
            r, rx, phs = C.transmit(bs, f, ph, snr, rlay[l], pn, None if phi is None else C.slice_path(phi, bs.shape[1]))
            bur[l] = (r, rx, phs, ks)
        fcache = {}
        for src in sources:
            S = st[src]
            lay, est, model = C.SOURCES[src]
            L = C.layout(lay)
            didx = L["data_idx"]
            r, rx, phs, ks = bur[lay]
            if (lay, est) not in fcache:                   # sources of one layout and estimator share f_hat, premf
                t0 = time.perf_counter()
                fh_ = E.estimate(est, r, ks, L, snr, f)
                dt = time.perf_counter() - t0
                fcache[(lay, est)] = (fh_, dt, C.premf(r, rx, fh_))
            fh, dt, rp = fcache[(lay, est)]
            S["time_est"] += dt
            off, M, D = hypotheses(src, snr, lobes)
            tol = M * SEARCH_STEP + 1e-12                  # measurement only from here to attempt()
            S["in_window"] += int(np.sum(np.abs(fh - f) <= tol))
            ms = np.arange(-lobes, lobes + 1) / D if D else np.zeros(1)
            S["in_search"] += int(np.sum(np.min(np.abs(fh[:, None] + ms[None] - f[:, None]), 1) <= tol))
            if C.lobe_D(lay):
                D_ = C.lobe_D(lay)
                fnc = E.noncoherent(r, ks, L)
                S["lobe_err"] += int(np.sum(np.abs(fh - f) > 0.5 / D_))
                S["nc_lobe_err"] += int(np.sum(np.abs(fnc - f) > 0.5 / D_))
                fpk = fh + np.round((fnc - fh) * D_) / D_
                S["nc_pick_err"] += int(np.sum(np.abs(fpk - f) > 0.5 / D_))

            def attempt(idx, fhyp):
                g = E.gain(model, rp[idx], ks[idx], L, fhyp, ph[idx], phs[idx], track_w, track, q, s2)
                llr, sh = C.llrs(rp[idx], didx, fhyp, g, s2)
                d, ok, _ = code.decode(llr, return_info=True)
                j = np.where(ok)[0]
                if len(j):                                 # re-encoding check on the de-rotated, gain-corrected symbols
                    c_ = code.encode(d[j])[:, C.INTERLEAVER]
                    sr = ((1 - 2.0 * c_[:, 0::2]) + 1j * (1 - 2.0 * c_[:, 1::2])) / np.sqrt(2)
                    rho = np.abs(np.sum(sh[j] * np.conj(sr), 1)) / np.sqrt(C.N_SYM * np.sum(np.abs(sh[j]) ** 2, 1))
                    acc = rho > thr
                    wrong = (d[j] != data[idx[j]]).any(1)
                    S["crc_pass"] += len(j)
                    S["crc_pass_wrong"] += int(wrong.sum())
                    S["re_caught"] += int((wrong & ~acc).sum())
                    S["re_lost"] += int((~wrong & ~acc).sum())
                    ok = ok.copy()
                    ok[j] = acc
                return d, ok

            dec, ok = attempt(np.arange(B), fh)
            ffin = fh.copy()
            bad = np.where(~ok)[0]
            if len(off) and len(bad):                      # PM+all: metric-ordered neighbours after the decode at f_hat
                Mt = np.empty((len(bad), len(off)))
                for i_, o in enumerate(off):
                    fq = fh[bad] + o
                    g = E.gain(model, rp[bad], ks[bad], L, fq, ph[bad], phs[bad], track_w, track, q, s2)
                    llr, _ = C.llrs(rp[bad], didx, fq, g, s2)
                    Mt[:, i_] = fsc.metric(llr)
                S["metric_evals"] += len(bad) * len(off)
                S["metric_rounds"] += len(bad) * int(np.ceil(len(off) / KP))
                order = np.argsort(Mt, 1, kind="stable")
                for t in range(order.shape[1]):
                    sub = np.where(~ok[bad])[0]
                    if not len(sub):
                        break
                    idx = bad[sub]
                    fk = fh[idx] + off[order[sub, t]]
                    d, okk = attempt(idx, fk)
                    S["extra_decodes"] += len(idx)
                    w = idx[okk]
                    dec[w], ok[w], ffin[w] = d[okk], True, fk[okk]
            errs = (dec != data).any(1)
            S["frames"] += B
            S["frame_err"] += int(errs.sum())
            S["undetected"] += int((errs & ok).sum())
            S["se_first"] += float(np.sum((fh - f) ** 2))
            S["se_final"] += float(np.sum((ffin - f) ** 2))
    return rate, snr, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", required=True, choices=list(C.CODES))
    ap.add_argument("--snrs", type=float, nargs="+", required=True, help="per-symbol Es/N0 (dB)")
    ap.add_argument("--sources", nargs="+", default=list(C.SOURCES))
    ap.add_argument("--frames", "--max-frames", dest="frames", type=int, default=60_000, help="packets per SNR")
    ap.add_argument("--min-err", "--min-errors", dest="min_err", type=int, default=150)
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--part", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pn", type=float, default=0.0, help="Wiener phase noise, linewidth x symbol time")
    ap.add_argument("--track", choices=("kalman", "sw"), default=E.TRACK_MODE,
                    help="interp2 / track phase model: RTS smoother (q = 2 pi pn) or the sliding window (--track-w)")
    ap.add_argument("--track-w", type=int, default=E.TRACK_W, help="--track sw: sliding window in fields (odd)")
    ap.add_argument("--lobes", type=int, default=LOBES, help="2-field layouts: lobe hypotheses m = -L .. L (0: none)")
    a = ap.parse_args()
    assert all(s in C.SOURCES for s in a.sources), a.sources
    assert a.track_w % 2 == 1, a.track_w
    tasks = [(a.rate, s, c, a.frames // a.chunks, -(-a.min_err // a.chunks), a.sources, a.seed, a.pn, a.track_w,
              a.track, a.lobes) for s in a.snrs for c in range(a.chunks)]
    acc = {}
    t0 = time.time()
    prog = C.path("logs", f"bler_{a.part}.progress")
    with mp.Pool(a.workers) as pool:
        for i, (rt, snr, st) in enumerate(pool.imap_unordered(work, tasks)):
            for src, v in st.items():
                w = acc.setdefault((snr, src), {k: 0 for k in v})
                for k, x in v.items():
                    w[k] += x
            with open(prog, "w") as fp:
                fp.write(f"{i + 1} {len(tasks)} {time.time() - t0:.0f}\n")    # job_progress.py: done total seconds
            print(f"{i + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
    res = []
    for (snr, src), v in sorted(acc.items()):
        lay = C.SOURCES[src][0]
        L = C.layout(lay)
        res.append(dict(rate=a.rate, snr=snr, src=src, layout=lay, pn=a.pn, nk=L["nk"], energy_db=L["energy_db"],
                        snr_plot=snr + L["energy_db"], window=window(src, snr), track=a.track, track_w=a.track_w,
                        lobes=a.lobes if C.lobe_D(lay) else 0, n_hyp=len(hypotheses(src, snr, a.lobes)[0]),
                        seed=a.seed, bler=v["frame_err"] / v["frames"], undetected_bler=v["undetected"] / v["frames"],
                        frac_in_window=v["in_window"] / v["frames"], frac_in_search=v["in_search"] / v["frames"],
                        rmse_first=float(np.sqrt(v["se_first"] / v["frames"])),
                        rmse_final=float(np.sqrt(v["se_final"] / v["frames"])),
                        extra_decodes_per_frame=v["extra_decodes"] / v["frames"],
                        us_est_per_frame=1e6 * v["time_est"] / v["frames"], **v))
    json.dump(dict(results=res), open(C.path("results", f"bler_{a.part}.json"), "w"))
    for r_ in res:
        print(f"{r_['snr']:5.1f} ({r_['snr_plot']:5.2f}) {r_['src']:18s} BLER {r_['bler']:.2e} "
              f"({r_['frame_err']}/{r_['frames']}) und {r_['undetected']} extra {r_['extra_decodes_per_frame']:.2f} "
              f"M {r_['window']} hyp {r_['n_hyp']} in-win {r_['frac_in_window']:.4f} in-search "
              f"{r_['frac_in_search']:.4f} lobe-err {r_['lobe_err']} (nc {r_['nc_lobe_err']}, nc-pick {r_['nc_pick_err']}) "
              f"rmse {r_['rmse_first']:.2e} -> {r_['rmse_final']:.2e}")
    print("saved", C.path("results", f"bler_{a.part}.json"), f"{time.time() - t0:.0f}s")
    print("EVAL DONE")


if __name__ == "__main__":
    main()
