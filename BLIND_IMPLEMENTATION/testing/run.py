"""BLIND_IMPLEMENTATION/testing/: run the final blind receivers (baselines) or an experiment variant on paired packets.

A variant is the baseline receiver's spec with extra small_rx flags (VARIANTS below); every flag defaults to the
baseline behaviour, so the baselines stay reproducible. Packets are paired: the same --seed and points give the
same packets (data, CFO, phase, noise) to every receiver of a run (blind_ber.simulate draws them once per batch).

    BLIND_STUDY=small_cfo python BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-5:16 --rx base10 --dump --part t-dump10a

--dump writes the Stage 3 dump (small_rx s3dump: every refined hypothesis' list-1 metric, SC-codeword correlation,
distance to the true CFO and its CA-SCL-8 outcome with all list paths, plus one row per packet) to
BLIND_IMPLEMENTATION/testing/results/dumps/<part>/ for the offline policy evaluation in BLIND_IMPLEMENTATION/testing/analyze.py.

<key>_dump (any baseline or variant key, e.g. nofast15_dump, base25_dump, base2_dump) runs that receiver with the decode
dump (small_rx dec_dump: one row per decode attempt, every call path and the CA retries, + one row per packet; decisions
and MACs unchanged), one file per chunk in <study data>/dumps/<part>/ (small_cfo/blind/dumps/<part>/ with
BLIND_STUDY=small_cfo; sync it back with cluster.py --results small_cfo/blind/dumps/<part>):

    BLIND_STUDY=small_cfo python BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-4:4 --rx nofast15_dump --part t-dec15a
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))            # BLIND_IMPLEMENTATION/testing -> the project root
sys.path.insert(0, ROOT)

import blind_ber as bb  # noqa: E402

BASE = {"base10": "S blind final v2",                      # R = 1/10 and 0.15 (blind_cfo.PROFILE)
        "base25": "S blind final 2/5, 1/2, best-first 32",
        "base2": "S blind final 2/5, 1/2"}
# experiment variants: (baseline, extra small_rx flags); filled in as the experiments are implemented
VARIANTS = {
    # R = 0.15 -1 dB failures (96 / 520k vs 0 / 740k at -2 dB, wrong final CFO): small_rx switches from 4 phase
    # hypotheses per cell (+ the +-pi/12 sub-offsets) to 2 at snr >= -1 (nph default). Keep 4 at every SNR.
    "nph4": ("base10", {"nph": 4}),
    # search-metric experiments with the re-encoded codeword (2026-11-12, predictions in README "R experiments")
    "dd": ("base10", {"s3_dd": True}),                                  # R1: code-aided refinement, no offset grid
    "win4": ("base10", {"win": {"1/10": 4.0}}),                         # R3: early win at z > 4 (re-encoding guards)
    "dd_win4": ("base10", {"s3_dd": True, "win": {"1/10": 4.0}}),       # R1 + R3
    "dd_k6": ("base10", {"s3_dd": True, "kstep": {"1/10": 6}}),         # R2: coarser grid (6 STEP) + R1
    # strategist actions (2026-11-12): fast path off, per-code-rate phases, speculative early decode
    "nofast": ("base10", {"s0_snr": 99.0}),            # fast path decode (+ retry) skipped (its FFT stays: the cells' phases need it)
    "nofast_nph4": ("base10", {"s0_snr": 99.0, "nph": 4}),
    "nofast_spec": ("base10", {"s0_snr": 99.0, "win_spec": 4.0}),      # action 2: z > 4 decoded at once (T = 1, no retry)
    "nph15": ("base10", {"nph": {"0.15": 4}}),          # the R = 0.15 setting candidate (code-rate keyed)
    # 2026-11-13: the testing receiver candidate: fast path off at SNR <= 0 dB (small_rx runs it at snr >= s0_snr) + 4
    # phases at R = 0.15; the origin tags / rho histograms / d4 counters are always on, so nofast_spec_t = nofast_spec
    "nofast15": ("base10", {"s0_snr": 0.5, "nph": {"0.15": 4}}),
    "nofast_spec_t": ("base10", {"s0_snr": 99.0, "win_spec": 4.0}),
    # the old phase_keep accounting (cells joining after the keep charged 2 phases from 0) on the same packets
    "base10_oldacct": ("base10", {"old_acct": True}),
    "nofast15_oldacct": ("base10", {"s0_snr": 0.5, "nph": {"0.15": 4}, "old_acct": True}),
    "base25_oldacct": ("base25", {"old_acct": True}),   # no phase pruning at 2/5: every count must equal base25's
    # 2026-11-13: q_fix, a candidate's phase th + qs[qb] pi/4 (the scored phase offset) instead of th + qb pi/4 (with
    # nph = 2, qs = [0, 2]: index 1 gave pi/4, on the rounding edge of the pi/2 branch in the refinement)
    "base10_qfix": ("base10", {"q_fix": True}),
    "nofast_qfix": ("base10", {"s0_snr": 0.5, "q_fix": True}),        # fast path off at <= 0 dB, default phases
    "nofast15_qfix": ("base10", {"s0_snr": 0.5, "nph": {"0.15": 4}, "q_fix": True}),
    "base25_qfix": ("base25", {"q_fix": True}),
    "base2_qfix": ("base2", {"q_fix": True}),
}
for _b, _s in (("base25", "25"), ("base2", "2")):                      # the same at R = 2/5 and 1/2 (joint list
    VARIANTS[f"dd_{_s}"] = (_b, {"s3_dd": True})                        # decode: R1 there replaces the 3 scored
    VARIANTS[f"win4_{_s}"] = (_b, {"win": 4.0})                         # offsets per cell; the grid is 2 STEP,
    VARIANTS[f"dd_win4_{_s}"] = (_b, {"s3_dd": True, "win": 4.0})       # R2 = 3 STEP)
    VARIANTS[f"dd_k3_{_s}"] = (_b, {"s3_dd": True, "kstep": {"2/5": 3, "1/2": 3}})
    VARIANTS[f"nofast_{_s}"] = (_b, {"s0_snr": 99.0})                   # fast path off (s0_snr is not per rate)
    # 2026-11-13: the R experiments again with q_fix (the phase-index bug biased them at the 2-phase points);
    # compare against base25_qfix / base2_qfix
    VARIANTS[f"dd_qfix_{_s}"] = (_b, {"s3_dd": True, "q_fix": True})
    VARIANTS[f"dd_win4_qfix_{_s}"] = (_b, {"s3_dd": True, "win": 4.0, "q_fix": True})
for _k in ("dd", "dd_win4"):                                            # R = 1/10 / 0.15 at >= -1 dB (2 phases)
    VARIANTS[f"{_k}_qfix"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], "q_fix": True})

DEC_DUMP = ("nofast15", "base25", "base2", "nofast15_qfix", "base25_qfix")   # decode dump receivers registered by
                                                                              # default (<key>_dump; any key on request)


def register(dump_dir=None, dec_dir=None, keys=()):
    names = {}
    for k, base in BASE.items():
        names[k] = base
        if dump_dir:
            nm = f"T {k} dump"
            bb.RX[nm] = {**bb.RX[base], "sps": {**bb.RX[base]["sps"], "s3dump": dump_dir}}
            names[k] = nm
    for k, (base, flags) in VARIANTS.items():
        nm = f"T {k}"
        bb.RX[nm] = {**bb.RX[BASE[base]], "sps": {**bb.RX[BASE[base]]["sps"], **flags}}
        names[k] = nm
    if dec_dir:                                            # (measurement) <key>_dump: the receiver + the decode dump
        for k in dict.fromkeys(list(DEC_DUMP) + [x[:-5] for x in keys if x.endswith("_dump")]):
            src = BASE[k] if k in BASE else names[k]       # (the baselines without the Stage 3 dump)
            bb.RX[f"T {k}_dump"] = {**bb.RX[src], "sps": {**bb.RX[src]["sps"], "dec_dump": dec_dir}}
            names[f"{k}_dump"] = f"T {k}_dump"
    return names


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", nargs="+", required=True, help='"rate:snr:chunks"')
    ap.add_argument("--rx", nargs="+", required=True, help="baseline keys (base10, base25, base2) and/or variants")
    ap.add_argument("--max-frames", type=int, default=2500, help="per chunk")
    ap.add_argument("--min-errors", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=8001)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--noise-only", action="store_true")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--part", required=True)
    a = ap.parse_args()
    dump = os.path.join(HERE, "results", "dumps", a.part) if a.dump else None
    names = register(dump, os.path.join(bb.bc.DATA, "dumps", a.part), a.rx)
    run_args = argparse.Namespace(points=a.points, rate=None, snrs=None, chunks=1, max_frames=a.max_frames,
                                  min_errors=a.min_errors, rx=[names[k] for k in a.rx], noise_only=a.noise_only,
                                  seed=a.seed, part=a.part, workers=a.workers)
    bb.run(run_args)
