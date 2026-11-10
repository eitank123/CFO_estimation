"""
est3: BLER of the 1024-symbol polar packet (N = 2048, CRC-16, CA-SCL-8) on AWGN with each CFO estimator, on IDENTICAL
packets (data, CFO, phase, noise), full chain, and the SAME receiver back-end:

    f_hat from the receiver's 128 pilots (inside the packet: known codeword symbols, the existing convention), in its
    layout (contiguous preamble, or distributed blocks)
    -> pre-MF correction at f_hat (blind_fast.premf, as the existing benchmarks)
    -> per CFO hypothesis f_h: complex gain (amplitude + phase) by LS on the receiver's own pilots at f_h, LLRs,
       CA-SCL-8, CRC-16 + re-encoding check (blind_fast.rho_min and the blind receivers' per-rate RHO_N table)
    -> CRC search as polar_ber_experiment's "first pass": f_hat + k STEP, k = +-1, +-2, ..., |k| <= M =
       ceil(4 x 1.3 sqrt(CRB_contiguous) / STEP), STEP = 7.5e-5; a packet stops at its first accepted pass

Periodic-preamble estimators (Schmidl-Cox / Moose, BLUE): a codeword cannot be periodic, so they estimate from a
periodic 128-symbol preamble with the packet's CFO and phase and independent noise of the same SNR (drawn for every
batch, whichever sources run, so the packets stay identical); the gain / phase come from the packet's first 128 known
symbols, as for the contiguous receivers. Statistically this is a packet whose first 128 symbols are periodic pilots.

    python est3/run_bler.py --rate 1/10 --snrs -6 -5 -4 --part a10
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from est3 import common as C
from est3 import estimators as E

SEARCH_STEP = 1.5e-4 * 512 / C.N_SYM
# source: (pilot layout used by the receiver, estimator)
SOURCES = {
    "Genie CFO": "contig", "M&M": "contig", "ML direct": "contig", "Joint ML Lh=3": "contig",
    "Jacobsen-Candan": "contig", "cluster": "contig", "cnn-cr": "contig", "cnn-reg": "contig",
    "Schmidl-Cox / Moose": "periodic", "BLUE MM99": "periodic",
    "Distributed ML 2x64": "split2x64", "Distributed ML 4x32": "dist4x32", "DVB-S2 blocks 4x32": "dist4x32",
    "DVB-S2 blocks 8x16": "dist8x16"}


def estimate(src, r, s, rp, snr, f):
    """CFO (B,) of a source: r, s at its pilot positions; rp the periodic preamble burst (periodic sources)."""
    lay = SOURCES[src]
    pos = C.LAYOUTS[lay]
    if src == "Genie CFO":
        return f.copy()
    if src == "M&M":
        return E.mm(r, s, snr)
    if src == "ML direct":
        return E.ml_direct(r, s)
    if src == "Joint ML Lh=3":
        return E.joint_ml(r, s, 1, 3)
    if src == "Jacobsen-Candan":
        return E.candan(r, s)
    if src == "Schmidl-Cox / Moose":
        return E.moose(rp, C.REP_Q)
    if src == "BLUE MM99":
        return E.blue_mm99(rp, C.REP_Q)
    if src.startswith("Distributed ML"):
        return E.dist_ml(r, s, pos)
    if src.startswith("DVB-S2"):
        return E.dvbs2_blocks(r, s, pos, C.BLOCKS[lay])
    from est3 import nn as N
    return N.estimate(src, r, s)


def work(task):
    rate, snr, chunk, frames, min_err, sources, seed = task
    from blind_fast import premf, rho_min
    from polar import PolarCode
    rng = np.random.default_rng([5, seed, list(C.CODES).index(rate), int(round(10 * snr)) + 1000, chunk])
    A = C.CODES[rate]
    code = PolarCode(C.N_BITS, A, 16, 8)
    s2 = 10 ** (-snr / 10)                                 # complex noise variance at the MF output
    from blind_ber import RHO_N                            # the blind receivers' per-rate threshold (same check)
    sl = 10 ** (snr / 10)
    thr = max(rho_min(snr), float(np.interp(snr, *zip(*RHO_N[rate]))) * np.sqrt(sl / (1 + sl)))
    M =int(np.ceil(4.0 * 1.3 * np.sqrt(C.crb_awgn(snr)) / SEARCH_STEP))
    ks = sorted([k for k in range(-M, M + 1) if k], key=lambda k: (abs(k), k))
    st = {s: dict(frames=0, frame_err=0, undetected=0, extra_decodes=0, se_first=0.0, se_final=0.0, crc_pass=0,
                  crc_pass_wrong=0, re_caught=0, re_lost=0, time_est=0.0) for s in sources}
    B = 100
    while st[sources[0]]["frames"] < frames and min(v["frame_err"] for v in st.values()) < min_err:
        data = rng.integers(0, 2, (B, A), dtype=np.uint8)
        cw = code.encode(data)[:, C.INTERLEAVER]
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        f = rng.uniform(-C.MAX_CFO, C.MAX_CFO, B)
        ph = rng.uniform(0, 2 * np.pi, B)
        r, rx = C.transmit(sym, f, ph, snr, rng)
        rper, _, _, _ = C.bursts(B, snr, rng, "periodic", f=f, ph=ph)     # always drawn (identical packets)
        for src in sources:
            S = st[src]
            pos = C.LAYOUTS[SOURCES[src]] if SOURCES[src] != "periodic" else C.LAYOUTS["contig"]
            sp = sym[:, pos]
            t0 = time.perf_counter()
            fh = estimate(src, r[:, pos], sp, rper, snr, f)
            S["time_est"] += time.perf_counter() - t0
            rp = premf(r, rx, fh)

            def attempt(idx, fhyp):
                g = C.gain_phase(rp[idx], sp[idx], pos, fhyp)
                llr, sh = C.llrs(rp[idx], fhyp, g, s2)
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
            for k in ks:
                bad = np.where(~ok)[0]
                if not len(bad):
                    break
                fk = fh[bad] + k * SEARCH_STEP
                d, okk = attempt(bad, fk)
                S["extra_decodes"] += len(bad)
                w = bad[okk]
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
    ap.add_argument("--snrs", type=float, nargs="+", required=True)
    ap.add_argument("--sources", nargs="+", default=list(SOURCES))
    ap.add_argument("--max-frames", type=int, default=60_000)
    ap.add_argument("--min-errors", type=int, default=150)
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--part", required=True)
    ap.add_argument("--seed", type=int, default=0, help="0 = the original runs; others add independent packets")
    a = ap.parse_args()
    assert all(s in SOURCES for s in a.sources), a.sources
    tasks = [(a.rate, s, c, a.max_frames // a.chunks, -(-a.min_errors // a.chunks), a.sources, a.seed)
             for s in a.snrs for c in range(a.chunks)]
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
    res = [dict(rate=a.rate, snr=snr, src=src, layout=SOURCES[src], bler=v["frame_err"] / v["frames"],
                undetected_bler=v["undetected"] / v["frames"], rmse_first=float(np.sqrt(v["se_first"] / v["frames"])),
                rmse_final=float(np.sqrt(v["se_final"] / v["frames"])),
                extra_decodes_per_frame=v["extra_decodes"] / v["frames"],
                us_est_per_frame=1e6 * v["time_est"] / v["frames"], **v) for (snr, src), v in sorted(acc.items())]
    json.dump(dict(results=res), open(C.path("results", f"bler_{a.part}.json"), "w"))
    for r_ in res:
        print(f"{r_['snr']:5.1f} {r_['src']:22s} BLER {r_['bler']:.2e} ({r_['frame_err']}/{r_['frames']}) "
              f"und {r_['undetected']} extra {r_['extra_decodes_per_frame']:.2f} rmse {r_['rmse_first']:.2e} "
              f"-> {r_['rmse_final']:.2e}")
    print("saved", C.path("results", f"bler_{a.part}.json"), f"{time.time() - t0:.0f}s")
    print("EVAL DONE")


if __name__ == "__main__":
    main()
