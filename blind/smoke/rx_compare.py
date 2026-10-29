"""Smoke: BLER / false passes / MACs / decodes of receiver variants on the same frames, one worker per
(point, receiver). Receiver names from blind_ber.RX, optionally with ";key=value" overrides of its sps spec.
    python blind/smoke/rx_compare.py --points 2/5:0.5 2/5:1 --frames 2000 --rx "v3 eco + CRC" "v3 eco + CRC;newton=2" """
import argparse
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc
import blind_fast as bf
import blind_ber as bb


def run(job):
    rate, snr, nm, n = job
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    rng = np.random.default_rng(7)                            # the same frames for every receiver
    base, *kv = nm.split(";")
    spec = {**bb.RX[base]}
    spec["sps"] = {**spec["sps"], "rate": rate, **{k: eval(v) for k, v in (x.split("=", 1) for x in kv)}}
    err = fp = 0
    st = dict(decodes=0, metric_evals=0)
    for _ in range(n // 500):
        data, cw, r, rx, f, th = bc.frames(500, code, snr, rng)
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        dec, ok, ff, ftop = bf.sps3_receive(r, rx, snr, code, sigma2, st, spec, sym)
        bad = (dec != data).any(1)
        err += int(bad.sum())
        fp += int((bad & ok).sum())
    return (f"R={rate} {snr:5} dB {nm[:60]:60s} err {err:4d} (false pass {fp:3d}) / {n}  MACs {st['macs'] / n / 1e6:.3f} M"
            f"  decodes {st['decodes'] / n:.2f}  metric evals {st['metric_evals'] / n:.1f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True)
    ap.add_argument("--rx", nargs="+", required=True)
    ap.add_argument("--frames", type=int, default=2000)
    a = ap.parse_args()
    jobs = [(pt.split(":")[0], float(pt.split(":")[1]), nm, a.frames) for pt in a.points for nm in a.rx]
    with Pool(min(16, len(jobs))) as pool:
        for line in pool.imap(run, jobs):
            print(line, flush=True)
    print("SMOKE DONE", flush=True)
