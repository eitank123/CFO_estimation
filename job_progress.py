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
JOBS["cfo_outage"] =("CFO outage, SNR-aware NN vs M&M", "count", ("run_cfo-outage.out", "cfo_outage.progress"))
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
