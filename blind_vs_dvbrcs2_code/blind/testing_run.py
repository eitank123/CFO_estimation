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

<key>_rd (testing_s11g_rd, base25_qfix_rd, base2_qfix_rd) runs that receiver with the Stage 3 refinement diagnostic
(small_rx ref_diag, D0 of results/expected_ref.md; decisions and MACs unchanged): rd_*.npz per chunk in the same
<study data>/dumps/<part>/ (r_* one row per refined candidate cell, q_* one per packet) + rd_* counters in the json.

<key>_fz (testing_s11g_fz, base25_qfix_fz, base2_qfix_fz) runs that receiver with the frozen-bit diagnostic (small_rx
fz_diag, F5 of results/expected_f3f5.md; decisions and MACs unchanged): fz_*.npz per chunk in the same directory (f_* one
row per CA-SCL-8 decode, j_* per joint list: every path's frozen-only metrics at small_rx FZ_Q of the frozen set; g_* per packet).

testing_s11g_lm2 / _lm4 / _lm2z (small_rx lmarg = 2 / 4, lazy 2) and testing_s11g_ddref / _ddref_s2 (small_rx ddref): the
online tests of results/expected_online_f3dd.md, decisions changed (lm_* / ddref_* counters in the json); base25_qfix_fzs /
base2_qfix_fzs / testing_s11g_fzs (small_rx fzstop, F5 online of results/expected_f3f5.md; fz_* / fzs_* counters). Run
each with its baseline (testing_s11g / base25_qfix / base2_qfix) on the same --seed and points (paired packets).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                             # (package) blind/ -> the package root
sys.path.insert(0, HERE)

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

# 2026-11-13: the retry gate (head B, nn_b_export.py): the CA retry of a failed main decode runs only if its logistic
# score >= thr[frac]; nnb1 = the 1 % point, nnb01 = the 0.1 % point; paired with the q_fix baselines (q_fix adopted)
NNB_JSON = os.path.join(HERE, "results", "nn_b_gate.json")
for _k in ("nofast15_qfix", "base25_qfix", "base2_qfix"):
    for _t, _f in (("nnb1", 0.01), ("nnb01", 0.001)):
        VARIANTS[f"{_k}_{_t}"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], "nn_b": (NNB_JSON, _f)})

# 2026-11-13: speculative early decode on the testing receiver (+ q_fix): win_spec = 4 (one CA-SCL decode, no retry, for
# 4 < z <= 6), and with the speculative acceptance at 1.1 x the re-encoding threshold (nofast_spec_t: 2 undetected / 400k
# at 1/10 -5 dB, both with rho / thr in [1.0, 1.1))
VARIANTS["nofast15_qfix_spec"] = ("base10", {**VARIANTS["nofast15_qfix"][1], "win_spec": 4.0})
VARIANTS["nofast15_qfix_spec11"] = ("base10", {**VARIANTS["nofast15_qfix"][1], "win_spec": 4.0, "spec_rho": 1.1})

# 2026-11-13: hard cap on the MACs per core (small_rx cap_core, "no packet" at the cap); caps from the cap plots
# (1/10, 0.15: 2 M; 2/5, 1/2: 1 M)
VARIANTS["nofast15_qfix_cap2"] = ("base10", {**VARIANTS["nofast15_qfix"][1], "cap_core": 2e6})
VARIANTS["base25_qfix_cap1"] = ("base25", {**VARIANTS["base25_qfix"][1], "cap_core": 1e6})
VARIANTS["base2_qfix_cap1"] = ("base2", {**VARIANTS["base2_qfix"][1], "cap_core": 1e6})
# 2026-11-13: the retry gate (1 % point) + the stricter speculative decode together
VARIANTS["nofast15_qfix_nnb1_spec11"] = ("base10", {**VARIANTS["nofast15_qfix_nnb1"][1], "win_spec": 4.0,
                                                    "spec_rho": 1.1})

# 2026-11-13: phase-equivariant receiver (small_rx equiv, bc.PiCode4; lit_checks equiv): without the bit interleaver a pi/2
# rotation is a polar automorphism + a codeword, so the cells keep their phases mod pi/2 (half the metric passes) and
# CA-SCL accepts the packet at any pi/2 branch. These MUST run with BLIND_NOINT=1 (asserted); their packets are then NOT
# paired with any interleaved run (another bit mapping, other noise realisations): the comparison arm is the same
# receiver without equiv in the same BLIND_NOINT=1 job (nofast15_qfix / base25_qfix / base2_qfix there; in AWGN with
# Gray QPSK the interleaver itself does not change the BLER)
for _k in ("nofast15_qfix", "base25_qfix", "base2_qfix"):
    VARIANTS[f"{_k}_eq"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], "equiv": True})

# 2026-11-13 (user decision): R = 0.15 back to 2 phases from +1 dB; 4 phases only below 0.5 dB. THE TESTING RECEIVER
# from now on (at +1 dB it equals base10_qfix: fast path on, 2 phases; at <= 0 dB it equals nofast15_qfix)
VARIANTS["testing"] = ("base10", {"s0_snr": 0.5, "nph": {"0.15": (4, 0.5)}, "q_fix": True})
# 2026-11-13: spec11 adopted (expected_spec1m.md: 1e6 paired at 1/10 -5 dB, 0 discordant, undetected = base, 0 noise false
# alarms). THE TESTING RECEIVER at 1/10 and 0.15 from now on. Measured only at <= -3 dB (fast path off); at +1 dB, with the
# fast path on, not run yet.
VARIANTS["testing_spec11"] = ("base10", {**VARIANTS["testing"][1], "win_spec": 4.0, "spec_rho": 1.1})
# 2026-11-14 (expected_s11.md): spec11 costs +3 ... +4 % per core above the waterfall (1/10 from -3 dB, 0.15 from -2 dB), so it
# runs only below 1/10 -3.5 dB, 0.15 -2.5 dB. At each SNR this receiver is exactly `testing_spec11` or `testing`.
VARIANTS["testing_s11g"] = ("base10", {**VARIANTS["testing_spec11"][1], "spec_snr": {"1/10": -3.5, "0.15": -2.5}})
# 2026-11-15 (expected_eqrb.md): the faithful phase-equivariant code, 2 rotation bits (Geiselhart et al. 2023; bc.PiCodeRB):
# the `*_eq` receivers with each list path un-rotated by the rotation read from (u_{N-2}, u_{N-1}) and ONE CRC test. MUST
# run with BLIND_NOINT=1 BLIND_ROTBITS=1 (asserted below; the whole chain then sends u_{N-2} = u_{N-1} = 0), and that
# job runs only eqrb receivers; the comparison arm is the interleaved receiver on the same seed in another part
for _k in ("nofast15_qfix", "base25_qfix", "base2_qfix", "testing"):
    VARIANTS[f"{_k}_eqrb"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], "equiv": True, "eqrb": True})
# 2026-11-15 (expected_pns.md): phase tracking for Wiener phase noise. _pns: after a CA-SCL-8 decode that fails CRC or the
# re-encoding check, the list-weighted re-encoded symbols drive an RTS phase smoother, the samples are de-rotated by it and
# decoded once more (small_rx pns). The smoother's linewidth = small_rx pns_lw, default None = BLIND_PN of the run when
# > 0, else 1e-4 (the AWGN runs: an assumed 1e-4). _rhosl: the segment re-encoding check measured only (small_rx rhos_log,
# S = 32 / 64 / 128; decisions unchanged) -> st["rhos_rows"] for the offline calibration of rhos_k.
# TODO after that calibration: testing_s11g_rhos / base25_qfix_rhos / base2_qfix_rhos ({"rhos": 64, "rhos_k": ...})
PNS = {"pns": {"iters": 1, "soft": True, "max_calls": 2}, "pns_lw": None}   # at most 2 pns retries per packet (cost cap)
RHOS_LOG = {"rhos_log": (32, 64, 128)}
for _k in ("testing_s11g", "base25_qfix", "base2_qfix"):
    VARIANTS[f"{_k}_pns"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], **PNS})
    VARIANTS[f"{_k}_rhosl"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], **RHOS_LOG})
    VARIANTS[f"{_k}_pns_rhosl"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], **PNS, **RHOS_LOG})

# 2026-11-15 (expected_ref.md, D0): the refinement diagnostic, log-only (small_rx ref_diag: decisions and MACs = the
# receiver's): every candidate cell refined in Stage 3 -> one row (truth residual, grid scores, 4th-power Newton,
# checkpoint-PM / grid parabolas, DD Newton, their MACs) in <study data>/dumps/<part>/rd_*.npz (sync it back with
# cluster.py --results small_cfo/blind/dumps/<part>) + rd_* counters in the part's json
for _k in ("testing_s11g", "base25_qfix", "base2_qfix"):
    VARIANTS[f"{_k}_rd"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], "ref_diag": True})   # True -> the part's dump dir
# 2026-11-15 (expected_f3f5.md, F5 offline): the frozen-bit diagnostic, log-only (small_rx fz_diag: decisions and MACs = the
# receiver's): every CA-SCL decode (main, CA retry, joint list, pns) -> one row with every list path's frozen-only metric
# at small_rx FZ_Q (1/4 ... 1) of the frozen set (polar.PolarCode fz_q), its outcome and true-cell label, in
# <study data>/dumps/<part>/fz_*.npz (groups f / j / g)
for _k in ("testing_s11g", "base25_qfix", "base2_qfix"):
    VARIANTS[f"{_k}_fz"] = (VARIANTS[_k][0], {**VARIANTS[_k][1], "fz_diag": True})    # True -> the part's dump dir
# 2026-11-15 (expected_online_f3dd.md, online at 1/10, 0.15): A (F3) _lm2 / _lm4: the candidates after the last checkpoint
# ordered by the list-marginalised metric of a Fast-SSC list decode (L_e = 2 / 4 paths, fastscl) of every surviving (cell,
# phase) hypothesis up to c = 3/4 (small_rx lmarg); B (TODO 3) _ddref: each candidate cell refined first at its DD-Newton
# estimate from the list-1 SC codeword at the cell centre, the 5-offset grid only as the fallback (small_rx ddref)
for _t, _f in (("lm2", {"lmarg": 2}), ("lm4", {"lmarg": 4}), ("ddref", {"ddref": True}),
               # verifier fixes (2026-11-15): _lm2z lazy lmarg (the first s2cand candidate in list-1 order first, the
               # list decode only if it fails); _ddref_s2: ddref only for win / spec / s2cand, one DD decode per cell
               ("lm2z", {"lmarg": 2, "lmarg_lazy": True}),
               ("ddref_s2", {"ddref": True, "ddref_tags": ("win", "spec", "s2cand"), "ddref_T": 1})):
    VARIANTS[f"testing_s11g_{_t}"] = ("base10", {**VARIANTS["testing_s11g"][1], **_f})
# 2026-11-15 (expected_f3f5.md "F5 online"): the frozen-metric stop inside every CA-SCL decode (small_rx fzstop = (q, t),
# the offline 0-loss thresholds of results/fz_f5.json): 2/5 q = 0.7, t = 0.774; 0.15 q = 0.9, t = 0.763
# review fix (2026-11-15): keyed by CODE rate (small_rx resolves p["code_rate"]; a missing rate = off), the 0-loss points
# of expected_f3f5.md / fz_f5.json: 1/10 (0.8, 0.751), 0.15 (0.9, 0.763), 2/5 (0.7, 0.774), 1/2 (0.7, 0.776)
FZS_T = {"1/10": (0.8, 0.751), "0.15": (0.9, 0.763), "2/5": (0.7, 0.774), "1/2": (0.7, 0.776)}
VARIANTS["base25_qfix_fzs"] = ("base25", {**VARIANTS["base25_qfix"][1], "fzstop": FZS_T})
VARIANTS["base2_qfix_fzs"] = ("base2", {**VARIANTS["base2_qfix"][1], "fzstop": FZS_T})
VARIANTS["testing_s11g_fzs"] = ("base10", {**VARIANTS["testing_s11g"][1], "fzstop": FZS_T})

DEC_DUMP = ("nofast15","base25", "base2", "nofast15_qfix", "base25_qfix")   # decode dump receivers registered by
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
        if flags.get("ref_diag") is True:                  # (measurement) ref_diag rows into the decode dump dir
            flags = {**flags, "ref_diag": dec_dir}
        if flags.get("fz_diag") is True:                   # (measurement) fz_diag rows: the same dir
            flags = {**flags, "fz_diag": dec_dir}
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
    _rb = [k.endswith("_eqrb") or k.endswith("_eqrb_dump") for k in a.rx]
    if any(_rb) or bb.bc.ROTBITS:                          # eqrb: only with BLIND_NOINT=1 BLIND_ROTBITS=1, and alone
        assert all(_rb) and bb.bc.NOINT and bb.bc.ROTBITS, "eqrb receivers need BLIND_NOINT=1 BLIND_ROTBITS=1 (and only them)"
    dump = os.path.join(HERE, "results", "dumps", a.part) if a.dump else None
    names = register(dump, os.path.join(bb.bc.DATA, "dumps", a.part), a.rx)
    run_args = argparse.Namespace(points=a.points, rate=None, snrs=None, chunks=1, max_frames=a.max_frames,
                                  min_errors=a.min_errors, rx=[names[k] for k in a.rx], noise_only=a.noise_only,
                                  seed=a.seed, part=a.part, workers=a.workers)
    bb.run(run_args)
