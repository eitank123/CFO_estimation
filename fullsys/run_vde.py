"""
Monte-Carlo PER of a VDE burst format (fullsys/vde.py) vs Es/N0 through the full Tx/Rx chain (txrx_chain.py:
upsample x SPS -> RRC (the link's roll-off) -> AWGN -> matched RRC -> downsample), ideal sync (sync='ideal'; the
data-aided synchroniser 'da' is the next step). Es/N0 is per data-modulation symbol (despread symbol for CDMA: the
chips go through the chain at Ec/N0 = Es/N0 - 10 log10 SF).

Pairing: chunk c of the point Es/N0 = x uses rng = default_rng([seed, round(100 (x + 50)), c]) whatever the SNR list
or the worker count, so two runs with the same --seed at the same point duplicate packets; use new seeds to pool.
Output: fullsys/results/vde_<part>.json (rewritten after every point), progress fullsys/results/vde_<part>.prog
("done total elapsed_s" in points, job_progress.count_row format).
Frame error = payload wrong or CRC failed; undetected = payload wrong and CRC passed. Ops by fullsys/costmodel.py:
ops = turbo decoder ops (iterations actually used, + APP / CRC per iteration with early stop), ops_crit = its 32-core
critical path (state-parallel model), frontend_ops / frontend_crit = de-rotation + despreading + LLR scaling.
Per point "chunk_err" = [[chunk index, frames in chunk, [in-chunk indices of the frames in error]], ...] for the
chunks with errors (all chunks hold `batch` frames except possibly the last, "n_chunks" in total), so two variants
run with the same --seed and batch can be paired frame by frame.
"""

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import txrx_chain  # noqa: E402
from fullsys.vde import VDELink, LINKS, REF, ASSUMPTIONS  # noqa: E402
from fullsys import costmodel  # noqa: E402

_W = {}


def link_key(s):
    return int(s) if str(s).isdigit() else s


def _init(link, interleaver, gold, crc_mode, beta, perm_seed=0, s_spread=None, qpp=(5, 22)):
    L = VDELink(link_key(link), interleaver=interleaver, gold=gold, crc_mode=crc_mode, beta=beta,
                perm_seed=perm_seed, s_spread=s_spread, qpp=tuple(qpp))
    h = txrx_chain.rrc(L.beta)
    _W.update(L=L, g=float(np.sum(h ** 2)))                     # matched-filter peak gain (unit-gain normalisation)


def _chunk(a):
    esn0, ci, n, seed, iters, algo, scale, early, sync = a
    L, g = _W["L"], _W["g"]
    rng = np.random.default_rng([seed, int(round(100 * (esn0 + 50))), ci])
    pay = rng.integers(0, 2, (n, L.kpay), dtype=np.int8)
    x, _ = L.tx(pay)
    snr_el = esn0 - 10 * np.log10(L.sf)                         # per transmitted element (chip or symbol)
    r = txrx_chain.transmit(x, np.zeros(n), np.zeros(n), snr_el, rng, beta=L.beta) / g
    out = L.rx(r, 10 ** (-snr_el / 10), sync=sync, iters=iters, algo=algo, scale=scale, early=early)
    wrong = (out["payload"] != pay)
    err = wrong.any(1)
    ok = out["crc_ok"]
    it = out["iters"].max(1)
    fe = err | ~ok
    return dict(frames=n, frame_err=int(fe.sum()), crc_fail=int((~ok).sum()), undetected=int((err & ok).sum()),
                bit_err=int(wrong.sum()), bits=int(wrong.size), ops=float(out["ops"].sum()),
                ops_crit=float(out["ops_crit"].sum()), iters_hist=np.bincount(it, minlength=iters + 1).tolist(),
                ci=ci, err_idx=np.flatnonzero(fe).tolist())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--link", default="32", help="LINKS key: 32 33 34 26 5 11 17 M2435")
    ap.add_argument("--snrs", type=float, nargs="+", required=True, help="Es/N0 per data symbol (dB)")
    ap.add_argument("--frames", type=int, default=100000, help="max frames per point")
    ap.add_argument("--max-err", type=int, default=200, help="stop a point at this many frame errors")
    ap.add_argument("--min-frames", type=int, default=0, help="run at least this many frames per point")
    ap.add_argument("--batch", type=int, default=0, help="frames per chunk (0 = auto from the burst length)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--part", required=True)
    ap.add_argument("--algo", choices=["maxlog", "logmap"], default="maxlog")
    ap.add_argument("--iters", type=int, default=8)
    ap.add_argument("--scale", type=float, default=None, help="extrinsic scale (default 0.75 max-log, 1.0 log-MAP)")
    ap.add_argument("--no-early", action="store_true", help="no CRC early stop")
    ap.add_argument("--sync", choices=["ideal", "da"], default="ideal")
    ap.add_argument("--interleaver", choices=["ccsds", "random", "srandom", "qpp"], default="ccsds")
    ap.add_argument("--perm-seed", type=int, default=0, help="seed of the random / S-random interleaver")
    ap.add_argument("--s-spread", type=int, default=None, help="S-random spread (default floor(sqrt(k/2)))")
    ap.add_argument("--qpp", type=int, nargs=2, default=[5, 22], metavar=("F1", "F2"), help="QPP f1 f2")
    ap.add_argument("--gold", choices=["SS0", "SS1"], default="SS0")
    ap.add_argument("--crc-mode", choices=["burst", "block"], default="burst")
    ap.add_argument("--beta", type=float, default=None, help="RRC roll-off override (default: the standard's)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    print(f"run_vde {vars(a)}", flush=True)

    out_dir = os.path.join(_ROOT, "fullsys", "results")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"vde_{a.part}.json")
    prog = os.path.join(out_dir, f"vde_{a.part}.prog")
    if os.path.exists(path) and not a.overwrite:
        raise SystemExit(f"{path} exists: use a new --part (or --overwrite)")

    iargs = (a.link, a.interleaver, a.gold, a.crc_mode, a.beta, a.perm_seed, a.s_spread, a.qpp)
    _init(*iargs)
    L = _W["L"]
    batch = a.batch or int(np.clip(4e5 // L.n_el, 1, 64))
    meta = dict(args=vars(a), link=str(a.link), params={k: (list(v) if isinstance(v, tuple) else v)
                                                         for k, v in LINKS[L.lid].items()},
                kpay=L.kpay, k=L.k, nblk=L.nblk, n_sym=L.n_sym, n_el=L.n_el, sf=L.sf, beta=L.beta,
                n_coded=L.code.n, n_chan=L.n_chan, batch=batch, despread_ops=L.despread_ops(),
                ebn0_offset_payload=L.ebn0_db(0.0), ebn0_offset_k=L.ebn0_db(0.0, info="k"),
                axis="Es/N0 per data-modulation symbol (despread for CDMA)", sync=a.sync,
                ref=REF, assumptions=ASSUMPTIONS, interleaver_perm=L.code.pi.tolist(),
                frontend_ops=L.frontend_ops(), frontend_crit=L.frontend_crit(),
                costmodel=dict(maxstar_extra=costmodel.MAXSTAR_EXTRA, cores=costmodel.CORES,
                               reduction=costmodel.REDUCTION, app_ops=costmodel.APP_OPS, crc_ops=costmodel.CRC_OPS,
                               step_ops={x: costmodel.siso_step_ops(x) for x in ("maxlog", "logmap")},
                               crit_model="state"))
    res = dict(meta=meta, points=[])
    t0 = time.time()
    with Pool(a.workers, initializer=_init, initargs=iargs) as pool:
        for pi, esn0 in enumerate(a.snrs):
            acc = dict(frames=0, frame_err=0, crc_fail=0, undetected=0, bit_err=0, bits=0, ops=0.0, ops_crit=0.0,
                       iters_hist=np.zeros(a.iters + 1, int))
            chunk_err = []
            ci, tp = 0, time.time()
            while acc["frames"] < a.frames and (acc["frame_err"] < a.max_err or acc["frames"] < a.min_frames):
                wave = []
                for _ in range(2 * a.workers):
                    n = min(batch, a.frames - acc["frames"] - batch * len(wave))
                    if n <= 0:
                        break
                    wave.append((esn0, ci, n, a.seed, a.iters, a.algo, a.scale, not a.no_early, a.sync))
                    ci += 1
                for r in pool.imap(_chunk, wave):
                    for key in ("frames", "frame_err", "crc_fail", "undetected", "bit_err", "bits", "ops", "ops_crit"):
                        acc[key] += r[key]
                    if r["err_idx"]:
                        chunk_err.append([r["ci"], r["frames"], r["err_idx"]])
                    acc["iters_hist"] += np.array(r["iters_hist"])
                f = acc["frames"]
                print(f"  progress link {a.link} Es/N0 {esn0:+.2f}: frames {f} err {acc['frame_err']} "
                      f"und {acc['undetected']} ({time.time() - tp:.0f}s)", flush=True)
                with open(prog, "w") as fh:
                    fh.write(f"{pi + min(f / a.frames, 1.0):.4f} {len(a.snrs)} {time.time() - t0:.0f}\n")
            f = acc["frames"]
            h = acc["iters_hist"]
            p = dict(esn0=esn0, ebn0_payload=L.ebn0_db(esn0), ebn0_k=L.ebn0_db(esn0, info="k"),
                     frames=f, frame_err=acc["frame_err"], per=acc["frame_err"] / f, crc_fail=acc["crc_fail"],
                     undetected=acc["undetected"], bit_err=acc["bit_err"], ber=acc["bit_err"] / acc["bits"],
                     iters_hist=h.tolist(), iters_mean=float((h * np.arange(len(h))).sum() / f),
                     ops_mean=acc["ops"] / f, ops_per_payload_bit=acc["ops"] / f / L.kpay,
                     despread_ops=L.despread_ops(), ops_crit_mean=acc["ops_crit"] / f,
                     frontend_ops=L.frontend_ops(), frontend_crit=L.frontend_crit(),
                     n_chunks=ci, batch=batch, chunk_err=chunk_err, seconds=time.time() - tp)
            res["points"].append(p)
            with open(path, "w") as fh:
                json.dump(res, fh, indent=1)
            print(f"SNR {esn0:+.2f} dB | link {a.link} | Eb/N0 payload {p['ebn0_payload']:+.2f} | frames {f} | "
                  f"err {p['frame_err']} | PER {p['per']:.3e} | BER {p['ber']:.3e} | und {p['undetected']} | "
                  f"iters {p['iters_mean']:.2f} | ops {p['ops_mean']:.3g}", flush=True)
            with open(prog, "w") as fh:
                fh.write(f"{pi + 1} {len(a.snrs)} {time.time() - t0:.0f}\n")
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
