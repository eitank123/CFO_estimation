"""
Wall time per packet of the pilot receivers (lowrate study, 1024 symbols), measured the same way as the blind receivers
in blind_ber.py: one thread per process, the Tx/Rx chain excluded (estimate + de-rotation + LLRs + decodes + CRC search).
Runs polar_ber_experiment.simulate_point with _receive timed; nothing is written to the BLER results.

    python pilot_time.py --est-len 128 --frames 4000 --part a     # -> blind/results/pilot_time_<part>.json
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import zlib

ap = argparse.ArgumentParser()
ap.add_argument("--est-len", type=int, default=128, choices=[64, 128])
ap.add_argument("--frames", type=int, default=4000)
ap.add_argument("--workers", type=int, default=16)
ap.add_argument("--part", default="a")
args = ap.parse_args()
os.environ.update(CFO_STUDY="lowrate", POLAR_NSYM="1024", POLAR_LEST=str(args.est_len))
os.environ.setdefault("CFO_BLOCK", str(min(args.est_len, 128) // 2))
sys.argv = sys.argv[:1]

import numpy as np                                   # noqa: E402
import blind_cfo as bc                               # noqa: E402
import polar_ber_experiment as pe                    # noqa: E402

SOURCES = (pe.GENIE, pe.SEARCH_MM_FIRST, pe.SEARCH_FIRST, pe.SEARCH_SPLIT_NN)
POINTS = {"R=0.1,C16": (-5.0, -4.0, -3.0, -2.0, -1.0, 0.0), "R=1/4,C16": (0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0),
          "R=1/2,C16": (2.0, 3.0, 4.0, 6.0, 8.0, 10.0)}
_t = {"time": 0.0}
_receive = pe._receive


def _timed(*a):
    t0 = time.perf_counter()
    _receive(*a)
    _t["time"] += time.perf_counter() - t0


def point(task):
    code, snr, src = task
    pe._receive = _timed
    _t["time"] = 0.0
    ebn0 = round(snr - 10 * np.log10(pe.CODES[code][0] / pe.N_SYM), 4)
    seed = zlib.crc32(repr((code, snr, src, "time")).encode())
    r = pe.simulate_point((code, ebn0, src, 8, 100, 10 ** 9, args.frames, seed, 0, os.devnull))
    return {"code": code, "esn0": snr, "src": src, "est_len": args.est_len, "frames": r["frames"],
            "bler": r["bler"], "extra_decodes_per_frame": r["extra_decodes_per_frame"],
            "time_per_frame": _t["time"] / r["frames"]}


if __name__ == "__main__":
    tasks = [(c, s, src) for c, ss in POINTS.items() if c in pe.CODES for s in ss for src in SOURCES]
    tasks.sort(key=lambda t: t[1])                   # the slow low-SNR searches first
    out, t0 = [], time.time()
    with mp.Pool(args.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(point, tasks), 1):
            out.append(r)
            print(f"{i}/{len(tasks)} {r['code']} {r['esn0']:5.1f} {r['src'][:48]:48s} "
                  f"{1e3 * r['time_per_frame']:.2f} ms/packet, {1 + r['extra_decodes_per_frame']:.2f} decodes", flush=True)
            with open(bc.path("logs", f"pilot_time_{args.part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} {time.time() - t0:.0f}\n")
    json.dump(out, open(bc.path("results", f"pilot_time_{args.part}.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)
