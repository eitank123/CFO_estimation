"""
Progress bars for the local BER jobs, written to progress.txt (open it in VS Code;
it refreshes every --interval seconds).

    polar_ebn0 / polar_error - polar_ber_experiment.py --mode ebn0 / error
        phase 1: estimator error distributions  ("estimator errors i/n" lines in the log)
        phase 2: Monte Carlo points             (per-batch progress in polar_<mode>.progress)
    ber_*.log - ber_experiment.py runs          (one "SNR ... dB |" line per SNR)

A Monte Carlo point is done when it has --min-errors frame errors or --max-frames frames,
so the per-point fraction is max(frame_err / min_errors, frames / max_frames).

    train_fft_nn_long.log - train_fft_nn_long.py   ("Epoch i/N ... | t s" lines, then "EVAL DONE")

Usage:
    py job_progress.py                                  # every job whose log exists, until all are done
    py job_progress.py --jobs train_long polar_ebn0     # a queued chain (later jobs show "waiting")
    py job_progress.py --once
"""

import argparse
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def where(rel):
    """A bare file name is in logs/ (paths.py); a path with a folder (multipath/...) is kept."""
    return os.path.join(HERE, rel if os.path.dirname(rel) else os.path.join("logs", rel))

BAR = 40
EST_LINE = re.compile(r"^estimator errors (\d+)/(\d+)")
SNR_LINE = re.compile(r"^SNR\s+-?[\d.]+ dB \|")

EPOCH_LINE = re.compile(r"^Epoch\s+(\d+)/(\d+) .*\|\s*(\d+)s")

# key: (display name, kind, arguments)
JOBS = {
    "train_long": ("FFT-NN training, L=512", "train", ("train_fft_nn_long.log",)),
    "multipath": ("Multipath FFT-NN (L=128, 512)", "train", (os.path.join("multipath", "results_multipath", "run.log"),)),
    "zo_awgn": ("Zero-overhead Rx, AWGN (stage 1)", "polar",
                ("zo", os.path.join("multipath", "results_zo_awgn", "run.log"),
                 os.path.join("multipath", "results_zo_awgn", "run.progress"))),
    "polar_ebn0": ("Polar BER/BLER vs Eb/N0", "polar", ("ebn0",)),
    "polar_error": ("Polar BER/BLER vs CFO error", "polar", ("error",)),
    # same experiment run on Run:ai: stdout goes to run_<job>.out (synced back by multipath/cluster.py)
    "polar_error_b": ("Polar BER/BLER vs CFO error (Run:ai)", "polar", ("error", "run_polar-err-b.out", "polar_error.progress")),
    "ber_P1024": ("Uncoded BER vs SNR, P=1024", "uncoded", ("ber_P1024.log", 16)),
    "ber_P256": ("Uncoded BER vs SNR, P=256", "uncoded", ("ber_P256.log", 16)),
    "ber_err": ("Uncoded BER vs CFO error", "uncoded", ("ber_err.log", 4)),
}
for _L in (128, 512):   # channel-aware MP-NN training (multipath/mp_cfo_v2.py), one Run:ai job per length
    JOBS[f"mp_v2_L{_L}"] = (f"MP-NN training, L={_L}", "train",
                            (os.path.join("multipath", "results_multipath", f"run_v2_L{_L}.log"),))
JOBS["coarse_nn_train"] = ("Stage 3 coarse NN training", "train",
                           (os.path.join("multipath", "results_coarse_nn", "train.log"),))
JOBS["coarse_nn_eval"] = ("Stage 3 coarse NN evaluation", "count",
                          (os.path.join("multipath", "results_coarse_nn", "eval.log"),
                           os.path.join("multipath", "results_coarse_nn", "eval.progress")))
for _k, _log in (("nofft_plain", "nofft_nn_plain.log"), ("nofft_unwrap", "nofft_nn_unwrap.log"),
                 ("nofft_unwrap_wide", "nofft_nn_unwrap_wide.log")):   # train_nofft_nn.py (FFT-free FFT-NN)
    JOBS[_k] = (f"FFT-free NN: {_k[6:]}", "train", (_log,))
JOBS["polar_error_c"] = ("Polar BLER vs CFO error (full chain, Run:ai)", "polar",
                         ("error", "run_polar-err-c.out", "polar_error.progress"))
JOBS["polar_ebn0_c"] = ("Polar BLER vs Eb/N0 (full chain, Run:ai)", "polar",
                        ("ebn0", "run_polar-ebn0-c.out", "polar_ebn0.progress"))
JOBS["snr_chain_b"] = ("SNR-aware NN, 150 more epochs (full chain)", "train", ("run_snr-chain-b.out",))
JOBS["polar_ebn0_r01"] = ("Polar BLER vs Eb/N0, R=1/10 (full chain, Run:ai)", "polar",
                          ("ebn0", "run_polar-ebn0-r01.out", "polar_ebn0.progress"))
for _r in ("r05", "r025", "r01"):      # L=128 Eb/N0 run split over 9 Run:ai jobs (polar_ber_experiment.py --tag)
    for _s in ("genie", "nn", "mm"):
        JOBS[f"p128_{_r}_{_s}"] = (f"L=128 Eb/N0 {_r} {_s}", "polar",
                                   ("ebn0", f"run_p128-{_r}-{_s}.out", f"polar_ebn0_L128_{_r}-{_s}.progress"))
for _L in (512, 128):                  # Es/N0 -5..10 dB extension, 12 Run:ai jobs (--missing-only --tag x<L>-<r>-<s>)
    for _r in ("r05", "r025"):
        for _s in ("genie", "nn", "mm"):
            _sfx = "" if _L == 512 else f"_L{_L}"
            JOBS[f"x{_L}_{_r}_{_s}"] = (f"Eb/N0 to 10 dB, L={_L} {_r} {_s}", "polar",
                                        ("ebn0", f"run_x{_L}-{_r}-{_s}.out", f"polar_ebn0{_sfx}_x{_L}-{_r}-{_s}.progress"))
JOBS["train_est256"] = ("SNR-aware NN, 256 symbols (est256)", "train",
                        (os.path.join("est256", "logs", "run_train-est256.out"),))
for _st in ("est256", "packet256"):    # 256-symbol studies: own folders <study>/logs (cluster.py --study)
    _lg = lambda f: os.path.join(_st, "logs", f)
    _sfx = "_L256" if _st == "packet256" else ""
    for _p in range(4):
        JOBS[f"{_st}_out{_p}"] = (f"{_st}: outage part {_p + 1}", "count",
                                  (_lg(f"run_{_st}-out{_p}.out"), _lg(f"{_st}_out{_p}.progress")))
    for _r in ("r05", "r025"):
        for _s in ("genie", "nn", "mm"):
            JOBS[f"{_st}_eb_{_r}_{_s}"] = (f"{_st}: Eb/N0 {_r} {_s}", "polar",
                                           ("ebn0", _lg(f"run_{_st}-eb-{_r}-{_s}.out"),
                                            _lg(f"polar_ebn0{_sfx}_{_st}-eb-{_r}-{_s}.progress")))
        JOBS[f"{_st}_err_{_r}"] = (f"{_st}: CFO error {_r}", "polar",
                                   ("error", _lg(f"run_{_st}-err-{_r}.out"), _lg(f"polar_error{_sfx}_{_st}-err-{_r}.progress")))
for _r in ("r0025", "r005", "r0075", "r01", "r015", "r02", "r033", "r075"):   # low-rate study (CFO_STUDY=lowrate)
    for _s in ("genie", "nn", "mm"):
        JOBS[f"lr_{_r}_{_s}"] = (f"lowrate: BLER vs SNR {_r} {_s}", "polar",
                                 ("ebn0", os.path.join("lowrate", "logs", f"run_lr-{_r}-{_s}.out"),
                                  os.path.join("lowrate", "logs", f"polar_ebn0_lr-{_r}-{_s}.progress")))
for _r in ("r0025", "r005", "r0075", "r01", "r015", "r02", "r025", "r033", "r05", "r075"):   # lowrate: CRB + CRC search
    for _s in ("crb", "srch"):
        JOBS[f"lr2_{_r}_{_s}"] = (f"lowrate: {_r} {'CRB bound' if _s == 'crb' else 'NN + CRC search'}", "polar",
                                  ("ebn0", os.path.join("lowrate", "logs", f"run_lr2-{_r}-{_s}.out"),
                                   os.path.join("lowrate", "logs", f"polar_ebn0_lr2-{_r}-{_s}.progress")))
for _n, _sfx in (   # lowrate: CRC length and packet length (polar_ber_experiment.py --tag <name>)
    ("lr3-p512-r0025-c11-srch", ""),
    ("lr3-p512-r005-c11-srch", ""),
    ("lr3-p512-r0075-c11-srch", ""),
    ("lr3-p512-r01-c11-srch", ""),
    ("lr3-p512-r0025-c16-srch", ""),
    ("lr3-p512-r0025-c16-genie", ""),
    ("lr3-p512-r005-c16-srch", ""),
    ("lr3-p512-r005-c16-genie", ""),
    ("lr3-p512-r0075-c16-srch", ""),
    ("lr3-p512-r0075-c16-genie", ""),
    ("lr3-p512-r01-c16-srch", ""),
    ("lr3-p512-r01-c16-genie", ""),
    ("lr3-p512-r0025-c24-srch", ""),
    ("lr3-p512-r0025-c24-genie", ""),
    ("lr3-p512-r005-c24-srch", ""),
    ("lr3-p512-r005-c24-genie", ""),
    ("lr3-p512-r0075-c24-srch", ""),
    ("lr3-p512-r0075-c24-genie", ""),
    ("lr3-p512-r01-c24-srch", ""),
    ("lr3-p512-r01-c24-genie", ""),
    ("lr7-p1024-nnsrch-m5", "_L1024"),
    ("lr7-p1024-nnsrch-m4", "_L1024"),
    ("lr7-p1024-nnsrch-m3", "_L1024"),
    ("lr7-p1024-nnsrch-m2", "_L1024"),
    ("lr7-p1024-nnsrch-m1", "_L1024"),
    ("lr7-p1024-nnsrch-p0", "_L1024"),
    ("lr7-p1024-mmsrch-m5", "_L1024"),
    ("lr7-p1024-mmsrch-m4", "_L1024"),
    ("lr7-p1024-mmsrch-m3", "_L1024"),
    ("lr7-p1024-mmsrch-m2", "_L1024"),
    ("lr7-p1024-mmsrch-m1", "_L1024"),
    ("lr7-p1024-mmsrch-p0", "_L1024"),
    ("lr7-p1024-mm-m5", "_L1024"),
    ("lr7-p1024-mm-m2", "_L1024"),
    ("add1-r005-mm-m2-m1", ""),
    ("add1-r005-nns-m5-m4", ""),
    ("add1-r005-nns-m3p5-m2p5", ""),
    ("add1-r005-nns-m2-m1", ""),
    ("add1-r01-mms-m3p5-m2p75", ""),
    ("add1-r01-mms-m2p5-m1p75", ""),
    ("add1-r01-mms-m1p5-m0p75", ""),
    ("add1-r01-mms-m0p5-0", ""),
    ("add1-r01-nns-m3-m2p25", ""),
    ("add1-r01-nns-m2-m1p25", ""),
    ("add1-r01-nns-m1-m0p5", ""),
    ("add1-r01-nns-m0p25-0", ""),
    ("add1-p1024-nns-m4p5-m4p5", "_L1024"),
    ("add1-p1024-nns-m4-m4", "_L1024"),
    ("add1-p1024-nns-m3p5-m3p5", "_L1024"),
    ("add1-p1024-nns-m3-m3", "_L1024"),
    ("add1-p1024-nns-m2p5-m2p5", "_L1024"),
    ("add1-p1024-nns-m2-m2", "_L1024"),
    ("add1-p1024-nns-m1p5-m1p5", "_L1024"),
    ("add1-p1024-nns-m1-m1", "_L1024"),
    ("add1-p1024-nns-m0p5-m0p5", "_L1024"),
    ("add1-p1024-nns-0-0", "_L1024"),
    ("lr11-p1024-r02-a", "_L1024"),
    ("lr11-p1024-r02-b", "_L1024"),
    ("lr11-p1024-r025-a", "_L1024"),
    ("lr11-p1024-r025-b", "_L1024"),
    ("lr11-p1024-r033-a", "_L1024"),
    ("lr11-p1024-r033-b", "_L1024"),
    ("lr11-p1024-r05-a", "_L1024"),
    ("lr11-p1024-r05-b", "_L1024"),
    ("lr11-p1024-r075-a", "_L1024"),
    ("lr11-p1024-r075-b", "_L1024"),
    ("add2-r01-mms-m1p75-m1p5", ""),
    ("add2-r01-mms-m1p25-m1", ""),
    ("add2-r01-mms-m0p75-m0p5", ""),
    ("add2-r01-mms-m0p25-0", ""),
    ("add2-r01-nns-m2-m1p75", ""),
    ("add2-r01-nns-m1p5-m1p25", ""),
    ("add2-r01-nns-m1-m0p75", ""),
    ("add2-r01-nns-m0p5-m0p25", ""),
    ("add2-r01-nns-0", ""),
    ("add2-p1024-nns-m4", "_L1024"),
    ("add2-p1024-nns-m3p5", "_L1024"),
    ("add2-p1024-nns-m3", "_L1024"),
    ("add2-p1024-nns-m2p5", "_L1024"),
    ("add2-p1024-nns-m2", "_L1024"),
    ("add2-p1024-nns-m1p5", "_L1024"),
    ("add2-p1024-nns-m1", "_L1024"),
    ("add2-p1024-nns-m0p5", "_L1024"),
    ("add2-p1024-nns-0", "_L1024"),
    ("add2-p1024-mms-m2p5", "_L1024"),
    ("add2-p1024-mms-m2", "_L1024"),
    ("add2-p1024-mms-m1p5", "_L1024"),
    ("add2-p1024-mms-m1", "_L1024"),
    ("add2-p1024-mms-m0p5", "_L1024"),
    ("add2-p1024-mms-0", "_L1024"),
    ("lr12-r01c16-mm-a", ""),
    ("lr12-r01c16-mm-b", ""),
    ("lr12-r01c16-mms-a", ""),
    ("lr12-r01c16-mms-b", ""),
    ("lr12-r01c16-mms-c", ""),
    ("add2-r01c16-nns-m4", ""),
    ("add2-r01c16-nns-m3p5", ""),
    ("add2-r01c16-nns-m3", ""),
    ("add2-r01c16-nns-m2p5", ""),
    ("add2-r01c16-nns-m2", ""),
    ("add2-r01c16-nns-m1p5-m1", ""),
    ("add2-r01c16-nns-m0p5-0", ""),
    ("lr3-p1024-r0025-c11-srch", "_L1024"),
    ("lr3-p1024-r0025-c11-genie", "_L1024"),
    ("lr3-p1024-r0025-c11-nn", "_L1024"),
    ("lr3-p1024-r0025-c16-srch", "_L1024"),
    ("lr3-p1024-r0025-c16-genie", "_L1024"),
    ("lr3-p1024-r0025-c24-srch", "_L1024"),
    ("lr3-p1024-r0025-c24-genie", "_L1024"),
    ("lr3-p1024-r005-c11-srch", "_L1024"),
    ("lr3-p1024-r005-c11-genie", "_L1024"),
    ("lr3-p1024-r005-c11-nn", "_L1024"),
    ("lr3-p1024-r005-c16-srch", "_L1024"),
    ("lr3-p1024-r005-c16-genie", "_L1024"),
    ("lr3-p1024-r005-c24-srch", "_L1024"),
    ("lr3-p1024-r005-c24-genie", "_L1024"),
    ("lr3-p1024-r0075-c11-srch", "_L1024"),
    ("lr3-p1024-r0075-c11-genie", "_L1024"),
    ("lr3-p1024-r0075-c11-nn", "_L1024"),
    ("lr3-p1024-r0075-c16-srch", "_L1024"),
    ("lr3-p1024-r0075-c16-genie", "_L1024"),
    ("lr3-p1024-r0075-c24-srch", "_L1024"),
    ("lr3-p1024-r0075-c24-genie", "_L1024"),
    ("lr3-p1024-r01-c11-srch", "_L1024"),
    ("lr3-p1024-r01-c11-genie", "_L1024"),
    ("lr3-p1024-r01-c11-nn", "_L1024"),
    ("lr3-p1024-r01-c16-srch", "_L1024"),
    ("lr3-p1024-r01-c16-genie", "_L1024"),
    ("lr3-p1024-r01-c24-srch", "_L1024"),
    ("lr3-p1024-r01-c24-genie", "_L1024"),
    ("lr3-p1024-r015-c11-srch", "_L1024"),
    ("lr3-p1024-r015-c11-genie", "_L1024"),
    ("lr3-p1024-r015-c11-nn", "_L1024"),
    ("lr3-p1024-r015-c16-srch", "_L1024"),
    ("lr3-p1024-r015-c16-genie", "_L1024"),
    ("lr3-p1024-r015-c24-srch", "_L1024"),
    ("lr3-p1024-r015-c24-genie", "_L1024"),
):
    JOBS[_n.replace("-", "_")] = (f"lowrate: {_n[4:]}", "polar", ("ebn0", os.path.join("lowrate", "logs", f"run_{_n}.out"), os.path.join("lowrate", "logs", f"polar_ebn0{_sfx}_{_n}.progress")))
for _n in ("lr4-r01-mmsrch", "lr4-r015-mmsrch", "lr5-r01-first", "lr5-r01-half",
           "lr10-r015-fine", "lr10-r02-fine", "lr10-r033-fine", "lr10-r075-fine",
           "lr9-r01-mmsrch-m5", "lr9-r01-mmsrch-m375", "lr9-r01-mmsrch-m25", "lr9-r01-mmsrch-m125",
           "lr8-r005-mmsrch-m5", "lr8-r005-mmsrch-m3", "lr8-r005-nnsrch-m5", "lr8-r005-nnsrch-m3", "lr8-r005-mm-m5", "lr8-r005-mm-m3", "lr8-r005-genie-m5", "lr8-r005-genie-m3",
           "lr6-full-m5", "lr6-full-m375", "lr6-full-m25", "lr6-full-m125", "lr6-first-m5", "lr6-first-m375", "lr6-first-m25", "lr6-first-m125", "lr6-half-m5", "lr6-half-m375", "lr6-half-m25", "lr6-half-m125", "lr6-mm-m5", "lr6-mm-m25", "lr6-genie-m5", "lr6-genie-m25"):   # lowrate: search variants
    JOBS[_n.replace("-", "_")] = (f"lowrate: {_n[4:]}", "polar", ("ebn0", os.path.join("lowrate", "logs", f"run_{_n}.out"), os.path.join("lowrate", "logs", f"polar_ebn0_{_n}.progress")))
for _n, _sfx in (("fp-p512c11-v2", ""), ("fp-p512c11-mm", ""), ("fp-p512c16-v2", ""), ("fp-p512c16-nn", ""),
                 ("fp-p512c16-mm", ""), ("fp-p1024c16-v2", "_L1024"), ("fp-p1024c16-nn", "_L1024"),
                 ("fp-p1024c16-mm", "_L1024")):   # lowrate: first-pass CRC search, NN v2 vs previous NN vs M&M
    JOBS[_n.replace("-", "_")] = (f"lowrate: {_n[3:]} first pass", "polar", ("ebn0", os.path.join("lowrate", "logs", f"run_{_n}.out"), os.path.join("lowrate", "logs", f"polar_ebn0{_sfx}_{_n}.progress")))
for _j in "abcdefgh":   # lowrate: extra frames for jittery BLER points (jobs/add3-<j>.sh, 16 lanes each)
    JOBS[f"add3_{_j}"] = (f"Add-trials job {_j} (16 lanes)", "count", (f"run_add3-{_j}.out", f"add3-{_j}.progress"))
for _j in "abcdefg":   # lowrate: NN v2 + CRC search (full search) BLER points (jobs/add4-<j>.sh, 16 lanes each)
    JOBS[f"add4_{_j}"] = (f"NN v2 full search, job {_j} (16 lanes)", "count", (f"run_add4-{_j}.out", f"add4-{_j}.progress"))
for _n, _sfx in (("sp1-p512c11", ""), ("sp1-p512c16", ""), ("sp1-p1024c16", "_L1024")):   # lowrate: split pilots, quick
    JOBS[_n.replace("-", "_")] = (f"lowrate: split pilots {_n[4:]} (quick)", "polar", ("ebn0", os.path.join("lowrate", "logs", f"run_{_n}.out"), os.path.join("lowrate", "logs", f"polar_ebn0{_sfx}_{_n}.progress")))
for _j in "abcdefgh":   # lowrate: split pilots (quarter) full search / first pass, NN v2 full search (jobs/add5-<j>.sh)
    JOBS[f"add5_{_j}"] = (f"Split full / first + NN v2 full, job {_j}", "count", (f"run_add5-{_j}.out", f"add5-{_j}.progress"))
for _j in "abcd":
    JOBS[f"add8_{_j}"] = (f"Split-pilot NN full search, job {_j}", "count", (f"run_add8-{_j}.out", f"add8-{_j}.progress"))
for _j in "abcde":
    JOBS[f"add9_{_j}"] = (f"R=1/4 CRC-16, M&M / split NN, 0..10 dB, job {_j}", "count", (f"run_add9-{_j}.out", f"add9-{_j}.progress"))
for _j in "abcdefgh":
    JOBS[f"add10_{_j}"] = (f"R=1/4 CRC-16 top-up, job {_j}", "count", (f"run_add10-{_j}.out", f"add10-{_j}.progress"))
for _j in "abcdefgh":
    JOBS[f"add11_{_j}"] = (f"R=1/3 CRC-16, M&M / split NN, 0..10 dB, job {_j}", "count", (f"run_add11-{_j}.out", f"add11-{_j}.progress"))
for _j in "abcdefgh":
    JOBS[f"add12_{_j}"] = (f"R=1/2 CRC-16, M&M / split NN, 2..10 dB, job {_j}", "count", (f"run_add12-{_j}.out", f"add12-{_j}.progress"))
JOBS["bt_nn"] = ("Blind NN posterior training", "train", ("run_bt-nn.out",))
JOBS["bt_coarse"] = ("Blind T1 coarse estimators", "count", ("run_bt-coarse.out", os.path.join("blind", "logs", "blind_coarse_a.progress")))
for _r in ("r10", "r4", "r2"):
    JOBS[f"bt_metric_{_r}"] = (f"Blind T2 metrics {_r}", "count", (f"run_bt-metric-{_r}.out", os.path.join("blind", "logs", "blind_metric_a.progress")))
for _r in ("r4", "r2"):
    JOBS[f"bt_sub_{_r}"] = (f"Blind T3 sub-code {_r}", "train", (f"run_bt-sub-{_r}.out",))
JOBS["bt_dd"] = ("Blind T4 decision-directed", "train", ("run_bt-dd.out",))
JOBS["bt_sub2_r4"] = ("Blind T3 sub-code basin r4", "train", ("run_bt-sub2-r4.out",))
JOBS["bt_sub2_r2"] = ("Blind T3 sub-code basin r2", "train", ("run_bt-sub2-r2.out",))
for _j in "abcdefghijklmno":
    JOBS[f"blb_{_j}"] = (f"Blind BLER, job {_j}", "count", (f"run_blb-{_j}.out", os.path.join("blind", "logs", f"blind_ber_{_j}.progress")))
for _j in range(1, 6):
    JOBS[f"blb_t{_j}"] = (f"Blind wall time, receiver {_j}", "count", ("run_blb-t.out", os.path.join("blind", "logs", f"blind_ber_t{_j}.progress")))
JOBS["fe_3"] = ("Blind round 2, E3 weighted metric", "count", ("run_fe-3.out", os.path.join("blind", "logs", "fast_e3_a.progress")))
JOBS["fe_1"] = ("Blind round 2, E1 coarse ranks", "count", ("run_fe-1.out", os.path.join("blind", "logs", "fast_e1_a.progress")))
for _p in ("r10", "r4", "r2"):
    JOBS[f"fe_2_{_p}"] = (f"Blind round 2, E2 metrics {_p}", "count", ("run_fe-2.out", os.path.join("blind", "logs", f"fast_e2_{_p}.progress")))
for _j in "abcdefghijk":
    JOBS[f"bf_{_j}"] = (f"Blind best-first search, job {_j}", "count", (f"run_bf-{_j}.out", os.path.join("blind", "logs", f"blind_ber_bf-{_j}.progress")))
for _j in "abcdefghi":
    JOBS[f"bv_{_j}"] = (f"Blind best-first search v3, job {_j}", "count", (f"run_bv-{_j}.out", os.path.join("blind", "logs", f"blind_ber_bv-{_j}.progress")))
for _g in ("vpa", "vpb", "vpc", "mv", "es", "nn"):
    for _r in ("r10", "r4", "r3", "r2"):
        JOBS[f"{_g}_{_r}"] = (f"Blind round 3, {_g}-{_r}", "count", (f"run_{_g}-{_r}.out", os.path.join("blind", "logs", f"blind_ber_{_g}-{_r}.progress")))
for _j in "abcdefgh":
    JOBS[f"b25_{_j}"] = (f"R=2/5 blind / few pilots, job {_j}", "count", (f"run_b25-{_j}.out", os.path.join("blind", "logs", f"blind_ber_b25-{_j}.progress")))
JOBS["sn25_a"] = ("R=2/5 split NN 128 pilots + CRC search", "count", ("run_sn25-a.out", "sn25-a.progress"))
for _j in ("r10a", "r10b", "r3a", "r3b", "r25a", "r25b", "r2a", "r2b"):
    JOBS[f"pv_{_j}"] = (f"Pilots + v3, {_j}", "count", (f"run_pv-{_j}.out", os.path.join("blind", "logs", f"blind_ber_pv-{_j}.progress")))
for _j in ("r10", "r25", "r2"):
    JOBS[f"pm_{_j}"] = (f"Split NN 128 + pre-MF correction, {_j}", "count", (f"run_pm-{_j}.out", f"pm-{_j}.progress"))
for _j in ("r10a", "r10b", "r10c", "r25a", "r25b", "r25c", "r2a", "r2b", "r2c"):
    JOBS[f"ec_{_j}"] = (f"v3 eco vs v3 fast, {_j}", "count", (f"run_ec-{_j}.out", os.path.join("blind", "logs", f"blind_ber_ec-{_j}.progress")))
JOBS["bs_e6"] = ("Basin E6: segment phase tracking", "count", ("run_bs-e6.out", os.path.join("blind", "logs", "basin_e6_a.progress")))
for _j in ("35a", "35b", "23a", "23b", "34a", "34b"):
    JOBS[f"hr_{_j}"] = (f"High rate blind, {_j}", "count", (f"run_hr-{_j}.out", os.path.join("blind", "logs", f"blind_ber_hr-{_j}.progress")))
JOBS["pm_hr"] = ("Split NN 128 +- pre-MF, R = 3/5, 2/3, 3/4", "count", ("run_pm-hr.out", "pm-hr.progress"))
JOBS["bs_e6b"] = ("Basin E6 b: high rates", "count", ("run_bs-e6b.out", os.path.join("blind", "logs", "basin_e6_b.progress")))
for _j in ("r10", "r25", "r2"):
    JOBS[f"ep_{_j}"] = (f"v3 eco + CA retry + posterior final, {_j}", "count", (f"run_ep-{_j}.out", os.path.join("blind", "logs", f"blind_ber_ep-{_j}.progress")))
for _j in ("r10", "r25", "r2"):
    JOBS[f"pe_{_j}"] = (f"Pilots + v3 eco+, {_j}", "count", (f"run_pe-{_j}.out", os.path.join("blind", "logs", f"blind_ber_pe-{_j}.progress")))
for _j in ("r10", "r25", "r2"):
    JOBS[f"ev_{_j}"] = (f"v3 eco+ verified, {_j}", "count", (f"run_ev-{_j}.out", os.path.join("blind", "logs", f"blind_ber_ev-{_j}.progress")))
for _j, _d in (("r25a", "R=2/5 blind"), ("r25b", "R=2/5 pilots N3x8"), ("r2", "R=1/2"), ("r10", "R=1/10 grid 6")):
    JOBS[f"e3_{_j}"] = (f"v3 eco3+ (cheap fast path), {_d}", "count", (f"run_e3-{_j}.out", os.path.join("blind", "logs", f"blind_ber_e3-{_j}.progress")))
for _j in ("r25", "r2"):
    JOBS[f"f7_{_j}"] = (f"eco3+ peak-picked fast path, {_j}", "count", (f"run_f7-{_j}.out", os.path.join("blind", "logs", f"blind_ber_f7-{_j}.progress")))
for _j in ("r25", "r2", "r10"):
    JOBS[f"g8_{_j}"] = (f"blind eco3+ gated, {_j}", "count", (f"run_g8-{_j}.out", os.path.join("blind", "logs", f"blind_ber_g8-{_j}.progress")))
for _j in ("r25a", "r25b", "r2"):
    JOBS[f"h9_{_j}"] = (f"eco4, {_j}", "count", (f"run_h9-{_j}.out", os.path.join("blind", "logs", f"blind_ber_h9-{_j}.progress")))
for _j in ("r25", "r2", "r10"):
    JOBS[f"i5_{_j}"] = (f"eco5 (best), {_j}", "count", (f"run_i5-{_j}.out", os.path.join("blind", "logs", f"blind_ber_i5-{_j}.progress")))
for _j in ("r10a", "r10b", "r25", "r2"):
    JOBS[f"j6_{_j}"] = (f"eco6, {_j}", "count", (f"run_j6-{_j}.out", os.path.join("blind", "logs", f"blind_ber_j6-{_j}.progress")))
for _j in ("r10a", "r10b"):
    JOBS[f"k7_{_j}"] = (f"eco7, {_j}", "count", (f"run_k7-{_j}.out", os.path.join("blind", "logs", f"blind_ber_k7-{_j}.progress")))
for _j in ("r10a", "r10b", "r10c", "r25", "r2"):
    JOBS[f"l8_{_j}"] = (f"eco8 candidates, {_j}", "count", (f"run_l8-{_j}.out", os.path.join("blind", "logs", f"blind_ber_l8-{_j}.progress")))
for _j in ("r25a", "r25b", "r2"):
    JOBS[f"nn_{_j}"] = (f"NN peak grader, {_j}", "count", (f"run_nn-{_j}.out", os.path.join("blind", "logs", f"blind_ber_nn-{_j}.progress")))
JOBS["pk_blind"] = ("Peak-grader NN training, blind", "train", ("run_pk-train-blind.out",))
JOBS["pk_pilots"] = ("Peak-grader NN training, 24 pilots", "train", ("run_pk-train-pilots.out",))
JOBS["snn_s1"] = ("Split NN retrained, CFO +-0.03 (small_cfo)", "train", ("run_snn-s1.out",))
JOBS["sx_b10"] = ("small CFO, sx-b10", "count", ("run_sx-b10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-b10.progress")))
JOBS["sx_p10"] = ("small CFO, sx-p10", "count", ("run_sx-p10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-p10.progress")))
JOBS["sx_b25"] = ("small CFO, sx-b25", "count", ("run_sx-b25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-b25.progress")))
JOBS["sx_p25"] = ("small CFO, sx-p25", "count", ("run_sx-p25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-p25.progress")))
JOBS["sx_r2"] = ("small CFO, sx-r2", "count", ("run_sx-r2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-r2.progress")))
JOBS["sx_ref"] = ("small CFO, sx-ref", "count", ("run_sx-ref.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-ref1.progress")))
JOBS["sx_f"] = ("small CFO, sx-f (phase sub-offsets)", "count", ("run_sx-f.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sx-f1.progress")))
JOBS["st_a"] = ("small CFO: split NN / M&M + pre-MF, part a", "count", ("run_st-a.out", "st-a.progress"))
JOBS["st_b"] = ("small CFO: split NN / M&M + pre-MF, part b", "count", ("run_st-b.out", "st-b.progress"))
JOBS["sw10b_a"] = ("small CFO sweep, sw10b-a", "count", ("run_sw10b-a.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sw10b-a0.progress")))
JOBS["sw10b_b"] = ("small CFO sweep, sw10b-b", "count", ("run_sw10b-b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sw10b-b0.progress")))
JOBS["sw10p"] = ("small CFO sweep, sw10p", "count", ("run_sw10p.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sw10p0.progress")))
JOBS["sw25b"] = ("small CFO sweep, sw25b", "count", ("run_sw25b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sw25b0.progress")))
JOBS["sw25p"] = ("small CFO sweep, sw25p", "count", ("run_sw25p.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sw25p0.progress")))
JOBS["sw2"] = ("small CFO sweep, sw2", "count", ("run_sw2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_sw20.progress")))
JOBS["st_c"] = ("small CFO: split NN / M&M + pre-MF, part c", "count", ("run_st-c.out", "st-c.progress"))
JOBS["gh_b10"] = ("small CFO G / H, gh-b10", "count", ("run_gh-b10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_gh-b100.progress")))
JOBS["gh_p10"] = ("small CFO G / H, gh-p10", "count", ("run_gh-p10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_gh-p100.progress")))
JOBS["gh_25"] = ("small CFO G / H, gh-25", "count", ("run_gh-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_gh-250.progress")))
JOBS["gh_2"] = ("small CFO G / H, gh-2", "count", ("run_gh-2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_gh-20.progress")))
JOBS["rs_b10a"] = ("small CFO rescue, rs-b10a", "count", ("run_rs-b10a.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_rs-b10a0.progress")))
JOBS["rs_b10b"] = ("small CFO rescue, rs-b10b", "count", ("run_rs-b10b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_rs-b10b0.progress")))
JOBS["rs_p10"] = ("small CFO rescue, rs-p10", "count", ("run_rs-p10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_rs-p100.progress")))
JOBS["rs_25"] = ("small CFO rescue, rs-25", "count", ("run_rs-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_rs-250.progress")))
JOBS["rs_2"] = ("small CFO rescue, rs-2", "count", ("run_rs-2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_rs-20.progress")))
JOBS["spn_blind"] = ("Cell-prior NN, blind (small_cfo)", "train", ("run_spn-blind.out",))
JOBS["spn_pilots"] = ("Cell-prior NN, pilots 3x8 (small_cfo)", "train", ("run_spn-pilots.out",))
JOBS["ck_smoke"] = ("Checkpoint NN smoke (small_cfo)", "train", ("run_ck-smoke.out",))
JOBS["ck_blind"] = ("Checkpoint NN, blind (small_cfo)", "train", ("run_ck-blind.out",))
JOBS["ck_pilots"] = ("Checkpoint NN, pilots 3x8 (small_cfo)", "train", ("run_ck-pilots.out",))
JOBS["bm_smoke"] = ("CFO literature benchmarks smoke", "count", ("run_bm-smoke.out", "bm-smoke.progress"))
JOBS["bm_a"] = ("CFO literature benchmarks, R=1/10", "count", ("run_bm-a.out", "bm-a.progress"))
JOBS["bm_b"] = ("CFO literature benchmarks, R=2/5", "count", ("run_bm-b.out", "bm-b.progress"))
JOBS["bm_c"] = ("CFO literature benchmarks, R=1/2", "count", ("run_bm-c.out", "bm-c.progress"))
JOBS["bm2_a"] = ("Fine estimators + split est. phase, R=1/10", "count", ("run_bm2-a.out", "bm2-a.progress"))
JOBS["bm2_b"] = ("Fine estimators + split est. phase, R=2/5, 1/2", "count", ("run_bm2-b.out", "bm2-b.progress"))
JOBS["re_a"] = ("Benchmarks + re-encode check", "count", ("run_re-a2.out", "re-a2.progress"))
JOBS["re_b"] = ("Split ML + re-encode, R=1/10 (more)", "count", ("run_re-b.out", "re-b.progress"))
JOBS["bm_em_smoke"] = ("EM benchmarks smoke (fix)", "count", ("run_bm-em-smoke.out", "bm-em-smoke.progress"))
JOBS["bm_em_a"] = ("EM benchmarks, R=1/10", "count", ("run_bm-em-a.out", "bm-em-a.progress"))
JOBS["bm_em_b"] = ("EM benchmarks, R=2/5", "count", ("run_bm-em-b.out", "bm-em-b.progress"))
JOBS["bm_em_c"] = ("EM benchmarks, R=1/2", "count", ("run_bm-em-c.out", "bm-em-c.progress"))
JOBS["ckr_smoke"] = ("Checkpoint NN in the receiver, smoke", "train", ("run_ckr-smoke.out",))
JOBS["ckr_p10"] = ("NN receiver BLER, ckr-p10", "count", ("run_ckr-p10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-p10.progress")))
JOBS["ckr_p10b"] = ("NN receiver BLER, ckr-p10b", "count", ("run_ckr-p10b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-p10b.progress")))
JOBS["ckr_b25"] = ("NN receiver BLER, ckr-b25", "count", ("run_ckr-b25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-b25.progress")))
JOBS["ckr_b2"] = ("NN receiver BLER, ckr-b2", "count", ("run_ckr-b2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-b2.progress")))
JOBS["ckr_pn25"] = ("NN receiver BLER, ckr-pn25", "count", ("run_ckr-pn25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-pn25.progress")))
JOBS["ckr_pn2"] = ("NN receiver BLER, ckr-pn2", "count", ("run_ckr-pn2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-pn2.progress")))
JOBS["ckr_pnsmoke"] = ("NN receiver BLER, ckr-pnsmoke", "count", ("run_ckr-pnsmoke.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_ckr-pnsmoke.progress")))
JOBS["race_10"] = ("PM racing replay, R=1/10", "train", ("run_race-10.out",))
JOBS["race_25"] = ("PM racing replay, R=2/5", "train", ("run_race-25.out",))
JOBS["race_2"] = ("PM racing replay, R=1/2", "train", ("run_race-2.out",))
JOBS["race2_10"] = ("PM racing replay v2, R=1/10", "train", ("run_race2-10.out",))
JOBS["race2_25"] = ("PM racing replay v2, R=2/5", "train", ("run_race2-25.out",))
JOBS["race2_2"] = ("PM racing replay v2, R=1/2", "train", ("run_race2-2.out",))
JOBS["pmr_smoke"] = ("PM racing receiver smoke", "count", ("run_pmr-smoke.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-pmr10.progress")))
JOBS["bmc_smoke"] = ("Blind MAC cuts smoke", "count", ("run_bmc-smoke.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-bmc25.progress")))
JOBS["tr10_smoke"] = ("Blind R=1/10 trade-off smoke", "count", ("run_tr10-smoke.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-tr10.progress")))
JOBS["bf_25"] = ("Blind best-first R=2/5", "count", ("run_bf-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_bf-25.progress")))
JOBS["join_smoke"] = ("Cheaper neighbour join smoke", "count", ("run_join-smoke.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-join-b.progress")))
JOBS["jt_10"] = ("R=1/10 MAC cuts, full stats", "count", ("run_jt-10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_jt-10.progress")))
JOBS["cap_b10a"] = ("Parallel cap smoke, blind 1/10 a", "count", ("run_cap-b10a.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-cap-b10a.progress")))
JOBS["cap_b10b"] = ("Parallel cap smoke, blind 1/10 b", "count", ("run_cap-b10b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-cap-b10b.progress")))
JOBS["cap_p10"] = ("Parallel cap smoke, pilots 1/10", "count", ("run_cap-p10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-cap-p10.progress")))
JOBS["cap_25"] = ("Parallel cap smoke, R=2/5 (then 1/2)", "count", ("run_cap-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-cap-25.progress")))
JOBS["cap_2"] = ("Parallel cap smoke, R=1/2", "count", ("run_cap-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-cap-2.progress")))
JOBS["mux"] = ("Fixed cores in passes smoke", "count", ("run_mux.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-mux10.progress")))
JOBS["crit_10"] = ("Critical-path MACs, R=1/10", "count", ("run_crit-10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-crit-10.progress")))
JOBS["crit_25"] = ("Critical-path MACs, R=2/5 (then 1/2)", "count", ("run_crit-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-crit-25.progress")))
JOBS["joint_b10"] = ("Joint CA-SCL smoke, blind 1/10", "count", ("run_joint-b10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-joint-b10.progress")))
JOBS["joint_p10"] = ("Joint CA-SCL smoke, pilots 1/10", "count", ("run_joint-p10.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-joint-p10.progress")))
JOBS["joint_25"] = ("Joint CA-SCL smoke, R=2/5 (then 1/2)", "count", ("run_joint-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-joint-25.progress")))
JOBS["fin_10a"] = ("Final receivers, R=1/10 -5/-4.5", "count", ("run_fin-10a.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-10a.progress")))
JOBS["fin_10b"] = ("Final receivers, R=1/10 -4..0", "count", ("run_fin-10b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-10b.progress")))
JOBS["fin_25"] = ("Final receivers, R=2/5 (0.5, 1 dB)", "count", ("run_fin-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-25a.progress")))
JOBS["fin_25b"] = ("Final receivers, R=2/5 (other SNRs)", "count", ("run_fin-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-25b.progress")))
JOBS["fin_2"] = ("Final receivers, R=1/2 (2, 2.5 dB)", "count", ("run_fin-2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-2a.progress")))
JOBS["fin_2b"] = ("Final receivers, R=1/2 (other SNRs)", "count", ("run_fin-2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-2b.progress")))
JOBS["reoff"] = ("Final receivers, CRC only (R=1/10)", "count", ("run_reoff.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_reoff-10.progress")))
JOBS["rob_snr"] = ("Robustness: SNR error (R=1/10)", "count", ("run_rob-snr.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-rob-snr10.progress")))
JOBS["rob_noise"] = ("Robustness: noise only (R=1/10)", "count", ("run_rob-noise.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_noise-10.progress")))
JOBS["rob_margin"] = ("Robustness: check margin (R=1/10)", "count", ("run_rob-margin.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_smoke-rob-margin10.progress")))
JOBS["fin_10c"] = ("Blind final v2, R=1/10 -5/-4.5", "count", ("run_fin-10c.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-10c.progress")))
JOBS["fin_10d"] = ("Blind final v2, R=1/10 -4..0", "count", ("run_fin-10d.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fin-10d.progress")))
JOBS["fill_10b"] = ("fill-in points, fill-10b", "count", ("run_fill-10b.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fill-10b.progress")))
JOBS["fill_10p"] = ("fill-in points, fill-10p", "count", ("run_fill-10p.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fill-10p.progress")))
JOBS["fill_25"] = ("fill-in points, fill-25", "count", ("run_fill-25.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fill-25.progress")))
JOBS["fill_2"] = ("fill-in points, fill-2", "count", ("run_fill-2.out", os.path.join("small_cfo", "blind", "logs", "blind_ber_fill-2.progress")))
JOBS["rk_blind"] = ("Cell-ranking NN training, blind", "train", ("run_rk-train-blind.out",))
JOBS["rk_pilots"] = ("Cell-ranking NN training, 24 pilots", "train", ("run_rk-train-pilots.out",))
JOBS["m9_r10"] = ("24 pilots eco7, default grid, r10", "count", ("run_m9-r10.out", os.path.join("blind", "logs", "blind_ber_m9-r10.progress")))
JOBS["pb_r25"] = ("parabolic fast path, r25", "count", ("run_pb-r25.out", os.path.join("blind", "logs", "blind_ber_pb-r25.progress")))
JOBS["pb_r2"] = ("parabolic fast path, r2", "count", ("run_pb-r2.out", os.path.join("blind", "logs", "blind_ber_pb-r2.progress")))
JOBS["rn_r10a"] = ("rank NN search order, r10a", "count", ("run_rn-r10a.out", os.path.join("blind", "logs", "blind_ber_rn-r10a.progress")))
JOBS["rn_r10b"] = ("rank NN search order, r10b", "count", ("run_rn-r10b.out", os.path.join("blind", "logs", "blind_ber_rn-r10b.progress")))
JOBS["rn_r25"] = ("rank NN search order, r25", "count", ("run_rn-r25.out", os.path.join("blind", "logs", "blind_ber_rn-r25.progress")))
JOBS["rn2_r10"] = ("rank NN, default grid, r10", "count", ("run_rn2-r10.out", os.path.join("blind", "logs", "blind_ber_rn2-r10.progress")))
JOBS["rm_b25"] = ("blind rescue mid + rho_n, r25", "count", ("run_rm-b25.out", os.path.join("blind", "logs", "blind_ber_rm-b25.progress")))
JOBS["ff_p10"] = ("final fill pilots R=1/10 -3 dB", "count", ("run_ff-p10.out", os.path.join("blind", "logs", "blind_ber_ff-p10.progress")))
JOBS["ff_p25"] = ("final fill pilots R=2/5 2-4 dB", "count", ("run_ff-p25.out", os.path.join("blind", "logs", "blind_ber_ff-p25.progress")))
JOBS["ff_p2a"] = ("final fill pilots R=1/2 2-3 dB", "count", ("run_ff-p2a.out", os.path.join("blind", "logs", "blind_ber_ff-p2a.progress")))
JOBS["ff_p2b"] = ("final fill pilots R=1/2 3.5-5 dB", "count", ("run_ff-p2b.out", os.path.join("blind", "logs", "blind_ber_ff-p2b.progress")))
JOBS["ff_b25"] = ("final fill blind R=2/5 2.5-4 dB", "count", ("run_ff-b25.out", os.path.join("blind", "logs", "blind_ber_ff-b25.progress")))
JOBS["ff_b2"] = ("final fill blind R=1/2 3.5-5 dB", "count", ("run_ff-b2.out", os.path.join("blind", "logs", "blind_ber_ff-b2.progress")))
JOBS["sg_b1"] = ("in-cell grid -5 dB, sg-b1", "count", ("run_sg-b1.out", os.path.join("blind", "logs", "blind_ber_sg-b1.progress")))
JOBS["sg_b2"] = ("in-cell grid -5 dB, sg-b2", "count", ("run_sg-b2.out", os.path.join("blind", "logs", "blind_ber_sg-b2.progress")))
JOBS["sg_p1"] = ("in-cell grid -5 dB, sg-p1", "count", ("run_sg-p1.out", os.path.join("blind", "logs", "blind_ber_sg-p1.progress")))
JOBS["sg_p2"] = ("in-cell grid -5 dB, sg-p2", "count", ("run_sg-p2.out", os.path.join("blind", "logs", "blind_ber_sg-p2.progress")))
JOBS["sg_smoke"] = ("in-cell grid smoke", "count", ("run_sg-smoke2.out", os.path.join("blind", "logs", "blind_ber_sg-smoke2.progress")))
JOBS["sw_b10a"] = ("in-cell grid sweep, sw-b10a", "count", ("run_sw-b10a.out", os.path.join("blind", "logs", "blind_ber_sw-b10a.progress")))
JOBS["sw_b10b"] = ("in-cell grid sweep, sw-b10b", "count", ("run_sw-b10b.out", os.path.join("blind", "logs", "blind_ber_sw-b10b.progress")))
JOBS["sw_b10c"] = ("in-cell grid sweep, sw-b10c", "count", ("run_sw-b10c.out", os.path.join("blind", "logs", "blind_ber_sw-b10c.progress")))
JOBS["sw_b10d"] = ("in-cell grid sweep, sw-b10d", "count", ("run_sw-b10d.out", os.path.join("blind", "logs", "blind_ber_sw-b10d.progress")))
JOBS["sw_p10"] = ("in-cell grid sweep, sw-p10", "count", ("run_sw-p10.out", os.path.join("blind", "logs", "blind_ber_sw-p10.progress")))
JOBS["sw_b25a"] = ("in-cell grid sweep, sw-b25a", "count", ("run_sw-b25a.out", os.path.join("blind", "logs", "blind_ber_sw-b25a.progress")))
JOBS["sw_b25b"] = ("in-cell grid sweep, sw-b25b", "count", ("run_sw-b25b.out", os.path.join("blind", "logs", "blind_ber_sw-b25b.progress")))
JOBS["sw_p25"] = ("in-cell grid sweep, sw-p25", "count", ("run_sw-p25.out", os.path.join("blind", "logs", "blind_ber_sw-p25.progress")))
JOBS["sw_b2"] = ("in-cell grid sweep, sw-b2", "count", ("run_sw-b2.out", os.path.join("blind", "logs", "blind_ber_sw-b2.progress")))
JOBS["sw_p2"] = ("in-cell grid sweep, sw-p2", "count", ("run_sw-p2.out", os.path.join("blind", "logs", "blind_ber_sw-p2.progress")))
JOBS["pf3_r10"] = ("pilot fast path R=1/10 from -4/-3 dB", "count", ("run_pf3-r10.out", os.path.join("blind", "logs", "blind_ber_pf3-r10.progress")))
JOBS["rl_b25"] = ("blind rescue lite + rho_n, r25", "count", ("run_rl-b25.out", os.path.join("blind", "logs", "blind_ber_rl-b25.progress")))
JOBS["pf2_r10"] = ("pilot fast path R=1/10 + rho_n", "count", ("run_pf2-r10.out", os.path.join("blind", "logs", "blind_ber_pf2-r10.progress")))
JOBS["rh_p25"] = ("rescue + rho_n check, p25", "count", ("run_rh-p25.out", os.path.join("blind", "logs", "blind_ber_rh-p25.progress")))
JOBS["rh_p10"] = ("rescue + rho_n check, p10", "count", ("run_rh-p10.out", os.path.join("blind", "logs", "blind_ber_rh-p10.progress")))
JOBS["rh_b2"] = ("rescue + rho_n check, b2", "count", ("run_rh-b2.out", os.path.join("blind", "logs", "blind_ber_rh-b2.progress")))
JOBS["rh_b25"] = ("rescue + rho_n check, b25", "count", ("run_rh-b25.out", os.path.join("blind", "logs", "blind_ber_rh-b25.progress")))
JOBS["rh_b10b"] = ("rescue + rho_n check, b10b", "count", ("run_rh-b10b.out", os.path.join("blind", "logs", "blind_ber_rh-b10b.progress")))
JOBS["rh_b10a"] = ("rescue + rho_n check, b10a", "count", ("run_rh-b10a.out", os.path.join("blind", "logs", "blind_ber_rh-b10a.progress")))
JOBS["bx_r10b"] = ("blind cheaper search + rescue, r10b", "count", ("run_bx-r10b.out", os.path.join("blind", "logs", "blind_ber_bx-r10b.progress")))
JOBS["bx_r10a"] = ("blind cheaper search + rescue, r10a", "count", ("run_bx-r10a.out", os.path.join("blind", "logs", "blind_ber_bx-r10a.progress")))
JOBS["pf_r10b"] = ("pilot fast path R=1/10, r10b", "count", ("run_pf-r10b.out", os.path.join("blind", "logs", "blind_ber_pf-r10b.progress")))
JOBS["pf_r10a"] = ("pilot fast path R=1/10, r10a", "count", ("run_pf-r10a.out", os.path.join("blind", "logs", "blind_ber_pf-r10a.progress")))
JOBS["fx3_r10b"] = ("rescue, rest of R=1/10, r10b", "count", ("run_fx3-r10b.out", os.path.join("blind", "logs", "blind_ber_fx3-r10b.progress")))
JOBS["fx3_r10p"] = ("rescue, rest of R=1/10, r10p", "count", ("run_fx3-r10p.out", os.path.join("blind", "logs", "blind_ber_fx3-r10p.progress")))
JOBS["fx2_r25p"] = ("rescue + pilot check 3 sigma, r25p", "count", ("run_fx2-r25p.out", os.path.join("blind", "logs", "blind_ber_fx2-r25p.progress")))
JOBS["fx2_r10p"] = ("rescue + pilot check 3 sigma, r10p", "count", ("run_fx2-r10p.out", os.path.join("blind", "logs", "blind_ber_fx2-r10p.progress")))
JOBS["fx_r25b"] = ("last-stage rescue, r25b", "count", ("run_fx-r25b.out", os.path.join("blind", "logs", "blind_ber_fx-r25b.progress")))
JOBS["fx_r10b4"] = ("last-stage rescue, r10b4", "count", ("run_fx-r10b4.out", os.path.join("blind", "logs", "blind_ber_fx-r10b4.progress")))
JOBS["fx_r10b5"] = ("last-stage rescue, r10b5", "count", ("run_fx-r10b5.out", os.path.join("blind", "logs", "blind_ber_fx-r10b5.progress")))
JOBS["fx_r10p"] = ("last-stage rescue, r10p", "count", ("run_fx-r10p.out", os.path.join("blind", "logs", "blind_ber_fx-r10p.progress")))
JOBS["vp_e4"] = ("Few-pilot comb ranks (E4)", "count", ("run_vp-e4.out", os.path.join("blind", "logs", "vp_e4_a.progress")))
JOBS["pnn_train"] = ("NN posterior training", "train", ("run_pnn-train.out",))
JOBS["pnn_e5"] = ("NN posterior ranks (E5)", "count", ("run_pnn-e5.out", os.path.join("blind", "logs", "post_e5_a.progress")))
JOBS["pt_a"] = ("Pilot receivers wall time", "count", ("run_pt-a.out", os.path.join("blind", "logs", "pilot_time_a.progress")))
for _j in ("p64r10-a", "p64r10s-a", "p64r4-a", "p64r4-b", "p64r4s-a", "p64out-a", "p64c24r10-a", "p64c24r4-a",
           "p64c24r4-b"):
    JOBS[_j.replace("-", "_")] = (f"64-symbol preamble {_j}", "count", (f"run_{_j}.out", f"{_j}.progress"))
JOBS["bt_nn2"] = ("Blind NN posterior training (retry)", "train", ("run_bt-nn2.out",))
JOBS["bt_coarse2"] = ("Blind T1 coarse + NN", "count", ("run_bt-coarse2.out", os.path.join("blind", "logs", "blind_coarse_b.progress")))
JOBS["p64_nn"] = ("SNR-aware NN, 64-symbol preamble", "train", ("run_p64-nn.out",))
JOBS["p64_snn"] = ("Split NN 2 x 32, 64-symbol preamble", "train", ("run_p64-snn.out",))
for _j in "abc":
    JOBS[f"outs_{_j}"] = (f"CFO outage, split NN vs M&M, part {_j}", "count", (f"run_outs-{_j}.out", f"cfo_outage_split_{_j}.progress"))
JOBS["add7_a"] =("Split-pilot NN BLER, 1024 CRC-16 (16 lanes)", "count", ("run_add7-a.out", "add7-a.progress"))
JOBS["err1024"] =("BLER vs CFO error, 1024 symbols, CRC-16", "polar", ("error", os.path.join("lowrate", "logs", "run_err1024.out"), os.path.join("lowrate", "logs", "polar_error_L1024_err1024.progress")))
for _j in "ab":
    JOBS[f"add6_{_j}"] =(f"Genie top-up, job {_j} (16 lanes)", "count", (f"run_add6-{_j}.out", f"add6-{_j}.progress"))
for _L in (512, 1024):
    for _i in ("dft", "rand"):
        JOBS[f"snn_{_L}_{_i}"] = (f"Split-pilot NN L={_L} {_i} (train + test)", "train", (f"run_snn-{_L}-{_i}.out",))
for _t in ("wide", "conv", "convlobe", "mlplobe", "convlobe-long"):
    JOBS["snn2_" + _t.replace("-", "_")] = (f"Split-pilot NN L=1024 {_t}", "train", (f"run_snn2-{_t}.out",))
JOBS["cfo_split_mse"] =("CFO MSE of the split pilots (512 / 1024)", "train", ("run_cfo-split-mse.out",))
JOBS["cfo_outage"] =("CFO outage, SNR-aware NN vs M&M", "count", ("run_cfo-outage.out", "cfo_outage.progress"))
JOBS["nn2_lag128"] = ("CFO NN v2 lag128 (train + test)", "train", ("run_nn2-lag128.out",))
JOBS["nn2_lag64"] = ("CFO NN v2 lag64 (train + test)", "train", ("run_nn2-lag64.out",))
JOBS["nn2_light64"] = ("CFO NN v2 light64 (train + test)", "train", ("run_nn2-light64.out",))
JOBS["nn2_light32"] = ("CFO NN v2 light32 (train + test)", "train", ("run_nn2-light32.out",))
JOBS["nn2_light16"] = ("CFO NN v2 light16 (train + test)", "train", ("run_nn2-light16.out",))
JOBS["chain_a"] = ("Chain A on the cluster (12 x 1024-symbol points + CRC-16 M&M search)", "count", ("run_chain-a.out", "chain-a.progress"))
JOBS["chain_b"] = ("Chain B on the cluster (CRC-16 NN-search extra frames)", "count", ("run_chain-b.out", "chain-b.progress"))
JOBS["chain_c"] = ("Chain C on the cluster (NN v2 light64/32/16 training)", "count", ("run_chain-c.out", "chain-c.progress"))
# est3: three extra preamble CFO estimators (joint CFO / channel ML, clustering NN + CNNs, direct ML)
_E3 = os.path.join("est3", "logs")
JOBS["est3_smoke"] = ("est3 smoke test (AWGN validation)", "count",
                      ("run_est3-smoke2.out", os.path.join(_E3, "bler_smoke3.progress")))
for _k in ("cnn-cr", "cnn-reg", "cluster"):
    JOBS[f"est3_train_{_k}"] = (f"est3 training {_k} (AWGN)", "count",
                                (f"run_est3-awtrain-{_k}.out", os.path.join(_E3, f"train_{_k}.progress")))
for _p in ("base", "nn"):
    JOBS[f"est3_est_{_p}"] = (f"est3 CFO accuracy sweep ({_p})", "count",
                              (f"run_est3-est-{_p}.out", os.path.join(_E3, f"est_{_p}.progress")))
for _p in ("kb10", "kb25", "kb2", "kn10", "kn25", "kn2", "m10", "m25", "m2", "m15", "j15", "c15", "x10"):
    JOBS[f"est3_bler_{_p}"] = (f"est3 BLER {_p}", "count",
                               (f"run_est3-bler-{_p}.out", os.path.join(_E3, f"bler_{_p}.progress")))
for _p in ("y10a", "y10b", "y15a", "y15b"):              # more packets for bler_more R = 1/10, 0.15 (2026-11-11)
    JOBS[f"est3_bler_{_p}"] = (f"est3 BLER {_p}", "count",
                               (f"run_est3-{_p}.out", os.path.join(_E3, f"bler_{_p}.progress")))
for _j, _p in (("est3-crb15", "crb15"), ("est3-crbhi", "crb25"), ("est3-crbhi", "crb2")):   # CRB-limited receiver
    JOBS[f"est3_{_p}"] = (f"est3 BLER {_p}", "count", (f"run_{_j}.out", os.path.join(_E3, f"bler_{_p}.progress")))
for _j, _p in (("more-10a", "more-10a"), ("more-10b", "more-10b"), ("more-10c", "more-10c"), ("more-hi", "more-25"),
               ("more-hi", "more-2"), ("cap-25", "cap-25"), ("b15a", "b15a"), ("b15b", "b15b"), ("b15c", "b15c"), ("cpar", "cpar-15"), ("cpar", "cpar-25"),
               ("cpar", "cpar-2"), ("cpar10", "cpar-10"),
               ("miss15a", "miss-15a"), ("miss15b", "miss-15b"), ("miss-hi", "miss-25"), ("miss-hi", "miss-2"),
               ("miss10a", "miss-10a"), ("miss10b", "miss-10b"), ("t-dump10", "t-dump10"), ("t-dump15a", "t-dump15a"),
               ("t-dump15b", "t-dump15b"), ("bm15a", "bm15a"), ("bm15b", "bm15b"), ("bm10", "bm10"),
               ("stg10", "stg10"), ("stg15", "stg15"), ("stg25", "stg25"), ("stg2", "stg2"), ("nph15a", "nph15a"), ("nph15b", "nph15b"), ("srch10", "srch10"), ("srch15", "srch15"), ("srch25", "srch25"), ("srch2", "srch2"),
               ("nf10a", "nf10a"), ("nf10b", "nf10b"), ("nf15a", "nf15a"), ("nf15b", "nf15b"), ("nf15b", "nf15c"),
               ("nn15a", "nn15a"), ("nn15b", "nn15b"), ("nn15b", "nn15c"),
               ("acct-smoke", "t-acct-smoke-a"), ("acct-smoke", "t-acct-smoke-b"),
               ("cnf10a", "t-cnf10a"), ("cnf10b", "t-cnf10b"), ("cnf10c", "t-cnf10c"), ("cnf10c", "t-cnf10d"), ("cnf15a", "t-cnf15a"),
               ("cnf15b", "t-cnf15b"), ("cnf15c", "t-cnf15c"), ("cnf15c", "t-cnf15e"), ("cnf15d", "t-cnf15d"), ("cnf15d", "t-cnf15f"),
               ("cnf15d", "t-cnf25"), ("cnf15d", "t-cnf2"),
               ("dec-smoke", "t-dec-smoke-a"), ("dec-smoke", "t-dec-smoke-b"), ("dec-smoke", "t-dec-smoke-c"), ("ddq-smoke", "t-ddq-smoke-a"), ("ddq-smoke", "t-ddq-smoke-b"), ("ddq-smoke", "t-ddq-smoke-c"), ("ddq25", "t-ddq25"), ("ddq25", "t-ddq2"), ("ddq10", "t-ddq10"),
               ("qfx10", "t-qfx10"), ("qfx25", "t-qfx25"), ("qfx25", "t-qfx2"), ("dec-a", "t-deca"), ("dec-b", "t-decb25"), ("dec-b", "t-decb2"), ("dec-b", "t-decbn")):              # more blind statistics for the est3 comparison (small_cfo study)
    JOBS[f"blind_{_p}"] = (f"blind more packets {_p}", "count",
                           (f"run_{_j}.out", os.path.join("small_cfo", "blind", "logs", f"blind_ber_{_p}.progress")))
JOBS["snr_chain"] =("SNR-aware NN retraining (full chain)", "train", ("run_snr-chain.out",))
JOBS["mp_v2_eval"] =("MP-NN evaluation", "train", (os.path.join("multipath", "results_multipath", "run_v2_eval.log"),))
for _i in range(8):   # Stage 1 split over up to 8 Run:ai jobs (zero_overhead_rx.py --parts N --part i)
    _d = os.path.join("multipath", "results_zo_awgn")
    JOBS[f"zo_awgn_p{_i}"] = (f"Stage 1 AWGN, job {_i + 1}", "polar",
                              ("zo", os.path.join(_d, f"run_p{_i}.log"), os.path.join(_d, f"run_p{_i}.progress")))
for _ch, _n in (("multipath", 8), ("awgn", 8)):   # Stage 2 (zero_overhead_mp.py --parts N --part i)
    _d = os.path.join("multipath", f"results_zo2_{_ch}")
    for _i in range(_n):
        JOBS[f"zo2_{_ch}_p{_i}"] = (f"Stage 2 {_ch}, job {_i + 1}", "polar",
                                    ("zo", os.path.join(_d, f"run_p{_i}.log"), os.path.join(_d, f"run_p{_i}.progress")))
        JOBS[f"zo2ref_{_ch}_p{_i}"] = (f"Stage 2 {_ch} references, job {_i + 1}", "polar",
                                       ("zo", os.path.join(_d, f"run_refs_p{_i}.log"),
                                        os.path.join(_d, f"run_refs_p{_i}.progress")))
for _ch in ("multipath", "awgn"):   # Stage 3: NN receivers (zero_overhead_mp.py --nn ... --parts N --part i)
    _d = os.path.join("multipath", f"results_zo2_{_ch}_nn")
    for _i in range(8):
        JOBS[f"zo2nn_{_ch}_p{_i}"] = (f"Stage 3 NN receiver, {_ch}, job {_i + 1}", "polar",
                                      ("zo", os.path.join(_d, f"run_p{_i}.log"), os.path.join(_d, f"run_p{_i}.progress")))
LOGS = {"train": lambda a: a[0], "count": lambda a: a[0], "polar": lambda a: a[1] if len(a) > 1 else f"polar_{a[0]}.log",
        "uncoded": lambda a: a[0]}


def fmt(sec):
    sec = int(sec)
    return f"{sec // 3600}h{sec % 3600 // 60:02d}m" if sec >= 3600 else f"{sec // 60}m{sec % 60:02d}s"


def bar(frac):
    fill = int(round(min(max(frac, 0.0), 1.0) * BAR))
    return f"[{'#' * fill}{'-' * (BAR - fill)}] {frac * 100:5.1f}%"


def read_lines(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def polar_rows(name, mode, log_rel=None, prog_rel=None):
    log_rel = log_rel or f"polar_{mode}.log"
    prog_rel = prog_rel or f"polar_{mode}.progress"
    log = read_lines(where(log_rel))
    if log is None:
        return [f"{name:<30} {bar(0)}  waiting"], False
    if any(l.startswith("Traceback") for l in log):
        return [f"{name:<30} {bar(0)}  FAILED (see {log_rel})"], True
    finished = any(l.startswith("=====") for l in log)

    rows = []
    prog = read_lines(where(prog_rel))
    est = [m for m in (EST_LINE.match(l) for l in log) if m]
    if mode == "ebn0" and (est or not prog):     # phase 1 only runs when 128-symbol estimators are simulated
        d, n = (int(est[-1].group(1)), int(est[-1].group(2))) if est else (0, 1)
        rows.append(f"  {'1. estimator error samples':<28} {bar(d / n)}  {d}/{n} Es/N0 points")

    frac, n_done, n_tasks, extra = 0.0, 0, 0, ""
    if prog and prog[0].startswith("start"):
        head = prog[0].split()
        start, n_tasks = float(head[1]), int(head[3])
        last = {}
        for l in prog[1:]:
            parts = l.split()
            if len(parts) == 2:
                last[parts[0]] = float(parts[1])
        n_done = sum(v >= 1.0 for v in last.values())
        frac = sum(last.values()) / n_tasks
        end = os.path.getmtime(where(prog_rel)) if finished else time.time()
        elapsed = end - start                     # frozen at the last update once the job is done
        extra = f"elapsed {fmt(elapsed)}"
        if 0 < frac < 1:
            extra += f", ETA ~{fmt(elapsed * (1 - frac) / frac)}"
    if finished:
        frac, n_done = 1.0, n_tasks
    label = "2. Monte Carlo points" if len(rows) else "Monte Carlo points"
    rows.append(f"  {label:<28} {bar(frac)}  {n_done}/{n_tasks or '?'} points  {extra}")
    return [f"{name}  ({'done' if finished else 'running'})"] + rows, finished


def uncoded_row(name, log_name, total):
    log = read_lines(where(log_name))
    if log is None:
        return f"{name:<30} {bar(0)}  waiting", False
    if any(l.startswith("Traceback") for l in log):
        return f"{name:<30} {bar(0)}  FAILED (see {log_name})", True
    done = sum(bool(SNR_LINE.match(l)) for l in log)
    return f"{name:<30} {bar(done / total)}  {done}/{total} SNRs", done >= total


def train_row(name, log_name):
    log = read_lines(where(log_name))
    if log is None:
        return f"{name:<30} {bar(0)}  waiting", False
    if any(l.startswith("Traceback") for l in log):
        return f"{name:<30} {bar(0)}  FAILED (see {log_name})", True
    if any(l.startswith(("EVAL DONE", "TRAIN DONE")) for l in log):
        return f"{name:<30} {bar(1.0)}  done", True
    ep = [m for m in (EPOCH_LINE.match(l) for l in log) if m]
    if not ep:
        return f"{name:<30} {bar(0)}  starting", False
    k, n = int(ep[-1].group(1)), int(ep[-1].group(2))
    if k >= n:
        return f"{name:<30} {bar(1.0)}  {k}/{n} epochs, final evaluation running", False
    sec = sum(int(m.group(3)) for m in ep) / len(ep)
    return f"{name:<30} {bar(k / n)}  {k}/{n} epochs  ETA ~{fmt(sec * (n - k))}", False


def count_row(name, log_name, prog_name):
    """Jobs that write "done total elapsed_s" into a progress file (coarse_nn.py --eval)."""
    log = read_lines(where(log_name))
    if log is not None and any(l.startswith("Traceback") for l in log):
        return f"{name:<30} {bar(0)}  FAILED (see {log_name})", True
    prog = read_lines(where(prog_name))
    if log is not None and any(l.startswith("ALL DONE") for l in log):
        return f"{name:<30} {bar(1.0)}  done", True
    if prog:                                              # several parts can share one log: a part is done when its
        v = [float(x) for x in prog[-1].split()]          # own progress file says so, not at the log's first EVAL DONE
        if len(v) == 3 and v[1] and v[0] >= v[1]:
            return f"{name:<30} {bar(1.0)}  done", True
    elif "blind_ber_" not in prog_name and log is not None and any(l.startswith(("EVAL DONE", "TRAIN DONE")) for l in log):
        return f"{name:<30} {bar(1.0)}  done", True
    if not prog:
        return f"{name:<30} {bar(0)}  {'starting' if log is not None else 'waiting'}", False
    v = [float(x) for x in prog[-1].split()]
    if len(v) == 1:                                       # a bare fraction (no counts / time)
        return f"{name:<30} {bar(min(v[0], 1.0))}  {100 * v[0]:.0f}%", False
    d, n, sec = v
    eta = f"  ETA ~{fmt(sec * (n - d) / d)}" if d else ""
    return f"{name:<30} {bar(d / n)}  {int(d)}/{int(n)} chunks{eta}", False


def render(keys):
    out = [f"Local jobs  ({time.strftime('%H:%M:%S')})", ""]
    all_done = True
    for key in keys:
        name, kind, a = JOBS[key]
        if kind == "polar":
            rows, done = polar_rows(name, *a)
            out += rows + [""]
        else:
            row, done = {"train": train_row, "count": count_row, "uncoded": uncoded_row}[kind](name, *a)
            out.append(row)
        all_done &= done
    return "\n".join(out), all_done


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=10)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--jobs", nargs="+", choices=list(JOBS),
                    help="jobs to show, in order (default: every job whose log exists)")
    args = ap.parse_args()
    keys = args.jobs or [k for k, (_, kind, a) in JOBS.items() if os.path.exists(where(LOGS[kind](a)))]
    while True:
        text, all_done = render(keys)
        with open(os.path.join(HERE, "progress.txt"), "w", encoding="utf-8") as f:
            f.write(text + f"\n\n(updates every {args.interval}s; ETA assumes the remaining points are "
                           f"as slow as the finished ones)\n")
        if args.once or all_done:
            print(text)
            break
        time.sleep(args.interval)
