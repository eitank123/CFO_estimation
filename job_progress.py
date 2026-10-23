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
    if log is not None and any(l.startswith(("EVAL DONE", "TRAIN DONE")) for l in log):
        return f"{name:<30} {bar(1.0)}  done", True
    prog = read_lines(where(prog_name))
    if not prog:
        return f"{name:<30} {bar(0)}  {'starting' if log is not None else 'waiting'}", False
    d, n, sec = (float(v) for v in prog[-1].split())
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
