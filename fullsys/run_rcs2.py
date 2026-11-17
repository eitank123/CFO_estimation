"""
Monte-Carlo PER of the DVB-RCS2 TC-LM bursts (fullsys/rcs2.py) through the full chain: burst at symbol rate ->
upsample + RRC (roll-off 0.20) -> AWGN (Es/N0 per symbol) -> matched RRC -> downsample (txrx_chain.transmit) ->
rx(sync) -> turbo decode -> CRC. Ideal sync = true timing, zero CFO, true phase, known N0 (TR 101 545-4 10.2.1).

Frame error = CRC fail OR PDU mismatch; undetected = CRC pass AND PDU mismatch (counted separately).
Packets are paired by (--seed, waveform, Es/N0, chunk index): decoder variants run with the same seed see the same
bursts. Run on the cluster only (Run:ai job), never locally.

    python fullsys/run_rcs2.py --wf 13 --snrs -1.4 -1.2 -1.0 --frames 1000000 --max-err 300 --seed 1 --part fs-x
    python fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.4 1.6 --part fs-y   # AFF3CT config + Eb/N0 axis
"""

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import rcs2, turbo_db as tdb          # noqa: E402
import txrx_chain                                   # noqa: E402

RESULTS = os.path.join(ROOT, "fullsys", "results")
_WF = {}


def _init():
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[v] = "1"


def _wf(key, itl):
    if (key, itl) not in _WF:
        _WF[(key, itl)] = rcs2.Waveform(key, direction=itl)
    return _WF[(key, itl)]


def wf_code(key):
    """Integer tag of a waveform for the seed sequence (13 -> 13, 'A13' -> 1013)."""
    return key if isinstance(key, int) else 1000 + int(key[1:])


def run_chunk(task):
    key, esn0, entropy, batch, opt = task
    wf = _wf(key, opt["itl"])
    rng = np.random.default_rng(np.random.SeedSequence(entropy))
    pdu = rng.integers(0, 2, (batch, wf.k)).astype(np.int8)
    s, _ = rcs2.tx(pdu, wf)
    z = np.zeros(batch)
    r = txrx_chain.transmit(s, z, z, esn0, rng, beta=rcs2.ROLLOFF)   # f = 0, phase = 0: ideal sync
    out = rcs2.rx(r, wf, 10 ** (-esn0 / 10), sync=opt["sync"], algo=opt["algo"], iters=opt["iters"],
                  sf=opt["sf"], early_stop=opt["early_stop"], exact_demap=opt["exact_demap"],
                  sf_low_iters=opt.get("sf_low_iters"))
    nbe = np.sum(out["pdu"] != pdu, axis=1)
    mism = nbe > 0
    fe = ~out["crc"] | mism
    return dict(frames=batch, frame_err=int(fe.sum()), err_idx=np.flatnonzero(fe).tolist(),
                crc_fail=int(np.sum(~out["crc"])),
                undetected=int(np.sum(out["crc"] & mism)), mismatch=int(mism.sum()), bit_err=int(nbe.sum()),
                iters_sum=int(out["iters"].sum()),
                first_pass=np.bincount(out["first_pass"], minlength=opt["iters"] + 1).tolist())


def run_point(pool_n, key, esn0, args, opt):
    nch = -(-args.frames // args.batch)
    tasks = ((key, esn0, [args.seed, wf_code(key), int(round(esn0 * 1000)) + 100000, c], args.batch, opt)
             for c in range(nch))
    acc = dict(frames=0, frame_err=0, crc_fail=0, undetected=0, mismatch=0, bit_err=0, iters_sum=0,
               first_pass=[0] * (opt["iters"] + 1))
    chunks = dict(batch=args.batch, frame_err=[], err_idx=[])     # per chunk c (seed index): paired McNemar tests
    t0 = tlast = time.time()
    with Pool(pool_n, initializer=_init) as pool:
        for res in pool.imap(run_chunk, tasks):
            chunks["err_idx"].append(res.pop("err_idx"))
            chunks["frame_err"].append(res["frame_err"])
            for k, v in res.items():
                acc[k] = [a + b for a, b in zip(acc[k], v)] if k == "first_pass" else acc[k] + v
            if time.time() - tlast > 60:
                tlast = time.time()
                print(f"  progress wf {key} Es/N0 {esn0:+.2f}: frames {acc['frames']} err {acc['frame_err']} "
                      f"({time.time() - t0:.0f} s)", flush=True)
            if acc["frame_err"] >= args.max_err or acc["frames"] >= args.frames:
                break
        pool.terminate()
    acc["time_s"] = round(time.time() - t0, 1)
    acc["chunks"] = chunks
    return acc


def iters_es_equiv(first_pass, iters, crc_start=2):
    """Mean early-stop-equivalent iterations from the first-pass histogram: max(first pass, crc_start), or iters
    when the CRC never passes (bin 0) - the fair early-stop cost of a fixed-iteration run."""
    h = np.asarray(first_pass, float)
    it = np.array([iters] + [max(i, crc_start) for i in range(1, len(h))], float)
    return float((h * it).sum() / max(h.sum(), 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wf", nargs="+", help="waveform IDs: 3 13 14 42 A12 A13 A23")
    ap.add_argument("--fmt", choices=sorted(rcs2.FMT), help="AFF3CT reference configuration (code only, no UW): "
                    "K 1504, PSK 2 bps, MAX, ADAPTIVE, 8 it, CRC early stop, 'aff3ct' interleaver; overrides --wf")
    ap.add_argument("--snrs", nargs="+", type=float, help="Es/N0 per transmitted symbol (dB)")
    ap.add_argument("--ebn0-aff3ct", nargs="+", type=float, help="AFF3CT Eb/N0 (code rate only), converted per wf")
    ap.add_argument("--frames", type=int, default=100000, help="max frames per point")
    ap.add_argument("--max-err", type=int, default=200, help="stop a point at this many frame errors")
    ap.add_argument("--batch", type=int, default=200, help="frames per chunk (one task)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--part", required=True, help="results file fullsys/results/rcs2_<part>.json")
    ap.add_argument("--algo", default=None, choices=["maxlog", "logmap"], help="default maxlog")
    ap.add_argument("--iters", type=int, default=None, help="default 8")
    ap.add_argument("--sf", default=None, help="extrinsic scaling: float (TR: 0.7) or 'adaptive' (AFF3CT 0.5 in "
                    "iteration 1, then 0.85; the default)")
    ap.add_argument("--early-stop", dest="early_stop", action="store_const", const=True, default=None,
                    help="CRC early stop from iteration 2 (default off, on with --fmt)")
    ap.add_argument("--no-early-stop", dest="early_stop", action="store_const", const=False)
    ap.add_argument("--sf-low-iters", type=int, default=None,
                    help=f"ADAPTIVE: iterations at 0.5 before 0.85 (default {tdb.ADAPTIVE_LOW_ITERS})")
    ap.add_argument("--itl", default=None, choices=list(tdb.INTERLEAVER_DIRS), help=f"default {tdb.INTERLEAVER_DIR}")
    ap.add_argument("--sync", default="ideal", choices=["ideal", "da"])
    ap.add_argument("--exact-demap", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()
    if bool(args.snrs) == bool(args.ebn0_aff3ct):
        ap.error("give exactly one of --snrs / --ebn0-aff3ct")
    if args.fmt:                                   # AFF3CT configuration; explicit flags still override (variants)
        args.wf = [rcs2.FMT[args.fmt]]
        dflt = dict(algo="maxlog", iters=8, sf="adaptive", early_stop=True, itl="aff3ct")
    elif args.wf:
        dflt = dict(algo="maxlog", iters=8, sf=tdb.SF_DEFAULT, early_stop=False, itl=tdb.INTERLEAVER_DIR)
    else:
        ap.error("give --wf or --fmt")
    for k, v in dflt.items():
        if getattr(args, k) is None:
            setattr(args, k, v)
    sf = args.sf if args.sf == "adaptive" else float(args.sf)
    opt = dict(itl=args.itl, sync=args.sync, algo=args.algo, iters=args.iters, sf=sf, early_stop=args.early_stop,
               exact_demap=args.exact_demap, sf_low_iters=args.sf_low_iters)
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, f"rcs2_{args.part}.json")
    if os.path.exists(path):
        sys.exit(f"{path} exists: use a new --part")
    doc = dict(meta=dict(args=vars(args), rolloff=rcs2.ROLLOFF, chain="txrx_chain.transmit (SPS %d, span %d)"
                         % (txrx_chain.SPS, txrx_chain.SPAN), assumptions=rcs2.ASSUMPTIONS), points=[])
    print(f"run_rcs2 {vars(args)}", flush=True)
    for w in args.wf:
        key = rcs2.wf_key(w)
        wf = rcs2.Waveform(key, direction=args.itl)
        rate = wf.w["rate"]
        aff = rcs2.REF_AFF3CT.get(rate, {}) if args.ebn0_aff3ct else {}
        pts = ([(round(wf.esn0_from_aff3ct(e), 4), e) for e in args.ebn0_aff3ct] if args.ebn0_aff3ct
               else [(e, None) for e in args.snrs])
        for esn0, eb_aff in pts:
            acc = run_point(args.workers, key, esn0, args, opt)
            n = acc["frames"]
            it_mean = acc["iters_sum"] / n
            mk = dict(n_sym=wf.n_data, bps=wf.m, crc=wf.crc)
            ops = tdb.macs(wf.code.N, it_mean, args.algo, args.early_stop, **mk)
            it_es = iters_es_equiv(acc["first_pass"], args.iters)
            ops_es = tdb.macs(wf.code.N, it_es, args.algo, True, **mk)
            p = dict(wf=w, esn0=esn0, ebn0_burst=round(float(wf.ebn0(esn0)), 4),
                     ebn0_aff3ct=round(float(esn0 - 10 * np.log10(wf.m * wf.k / wf.n_coded)), 4),
                     L_burst=wf.L, k=wf.k, N=wf.code.N, **acc, per=acc["frame_err"] / n,
                     fer_aff3ct=acc["mismatch"] / n,                # AFF3CT FER: any information bit wrong
                     iters_mean=it_mean, ops_per_frame=ops["total"], ops_crit_per_frame=ops["crit"], ops=ops,
                     iters_es_equiv=it_es, ops_es_equiv=ops_es["total"], crit_es_equiv=ops_es["crit"],
                     ref_tr=rcs2.REF_PER.get(key) and {str(k): v for k, v in rcs2.REF_PER[key].items()},
                     ref_aff3ct_fer=aff.get(eb_aff) if aff.get("wf") == key or key == 14 else None)  # 14 = A12 code
            doc["points"].append(p)
            with open(path + ".tmp", "w") as f:
                json.dump(doc, f, indent=1)
            os.replace(path + ".tmp", path)
            print(f"SNR {esn0:+.2f} dB | wf {w} | Eb/N0 burst {p['ebn0_burst']:+.2f} | frames {n} | err "
                  f"{acc['frame_err']} (undetected {acc['undetected']}) | PER {p['per']:.3e} | FER(info) "
                  f"{p['fer_aff3ct']:.3e} (ref {p['ref_aff3ct_fer']}) | it {it_mean:.2f} | "
                  f"ops {ops['total'] / 1e6:.2f} M (crit {ops['crit'] / 1e3:.1f} k) | it_es {it_es:.2f} | "
                  f"{acc['time_s']:.0f} s", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
