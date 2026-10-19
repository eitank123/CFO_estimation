"""
Run a job of this project on the BGU Run:ai cluster (bhn20) and keep its results in sync locally.

    push       copy source files / inputs to the cluster project folder
    submit     write run_<job>.sh there and submit it with runai-bgu (CPU job)
    sync       while the job runs, copy its result folder back every --interval s, so the local
               job_progress.py / progress.txt keeps working; one last copy when it ends

Needs the university VPN when off campus (bhn20 is resolved through it).

Usage (project folder):
    py multipath/cluster.py run --job zo-awgn --cpu 16 --mem 24Gi \
        --push polar.py channel.py config.py polar_results_ebn0.npy multipath/zero_overhead_rx.py \
        --results multipath/results_zo_awgn \
        --cmd "multipath/zero_overhead_rx.py --channel awgn --workers 16"
    py multipath/cluster.py status --job zo-awgn
"""

import argparse
import io
import os
import re
import subprocess
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REMOTE = "/gpfs0/bgu-haimp/users/karpei/CFO_estimation"
PYTHON = "/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python"
SSH_DIR = "/c/Users/eitan/.ssh"
SSH = ["ssh", "-F", f"{SSH_DIR}/config", "-o", f"UserKnownHostsFile={SSH_DIR}/known_hosts",
       "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=30", "bhn20"]


# bhn20 is a LOGIN node: HPC policy allows only data transfer and runai commands there. Any user code
# (python, even "python -c 'import torch'" for a version check) must run inside a Run:ai job.
# Every command sent over ssh is checked; "runai-bgu submit python" is the Run:ai job type, not an interpreter.
_INTERPRETER = re.compile(r"(?:^|[\s;&|(`$/'\"])(?:python[\d.]*|ipython|py|pip[\d.]*|conda|mamba|jupyter|"
                          r"torchrun|perl|ruby|node|Rscript|julia|matlab)(?=$|[\s;&|)`'\"])")


def check_login_command(cmd):
    if _INTERPRETER.search(cmd.replace("runai-bgu submit python", "runai-bgu submit JOB")):
        raise RuntimeError("refusing to run an interpreter on the login node bhn20 "
                           f"(submit it as a Run:ai job instead): {cmd[:200]}")


def ssh(cmd, data=None, timeout=300):
    check_login_command(cmd)
    r = subprocess.run(SSH + [cmd], input=data, capture_output=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"ssh failed ({r.returncode}): {r.stderr.decode(errors='replace')[-500:]}")
    return r.stdout


def push(paths):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for p in paths:
            tar.add(os.path.join(ROOT, p), arcname=p.replace("\\", "/"))
    ssh(f"cd {REMOTE} && tar xf -", data=buf.getvalue())
    print(f"pushed {len(paths)} files")


def submit(job, cmd, cpu, mem, study=""):
    logs = f"{study}/logs" if study else "logs"                # a study keeps its job output too (paths.py)
    script = (f"#!/bin/bash\n# Submitted by multipath/cluster.py\ncd {REMOTE}\n"
              f"export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg\n"
              + (f"export CFO_STUDY={study}\n" if study else "") +
              f"{PYTHON} -u {cmd} > {logs}/run_{job}.out 2>&1\n")
    sh = f"{REMOTE}/jobs/run_{job}.sh"
    ssh(f"mkdir -p {REMOTE}/jobs {REMOTE}/{logs} && cat > {sh} && chmod +x {sh}", data=script.encode())
    if status(job) != "not found":
        raise RuntimeError(f"a Run:ai job named {job} already exists; use a new name")
    out = ssh(f'runai-bgu submit python -n {job} -c {cpu} -m {mem} -- "bash {sh}" 2>&1')
    text = out.decode(errors="replace").strip()
    print(text[-800:])
    if "Creating" not in text:                  # runai-bgu prints "Creating training <name>..."
        raise RuntimeError(f"submit of {job} failed")


def statuses(jobs):
    """Status of several jobs from ONE `runai training list` call (keeps the login node load minimal)."""
    out = ssh("runai training list 2>/dev/null").decode(errors="replace")
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if parts and parts[0] in jobs:
            found[parts[0]] = parts[3] if len(parts) > 3 else "?"
    return {j: found.get(j, "not found") for j in jobs}


def status(job):
    return statuses([job])[job]


def pull(results):
    """Copy result folders and/or files (list of paths relative to the project) back; missing ones are skipped."""
    paths = " ".join(results) if isinstance(results, (list, tuple)) else results
    data = ssh(f"cd {REMOTE} && p=$(ls -d {paths} 2>/dev/null); [ -n \"$p\" ] && tar cf - $p || true")
    if data:
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(ROOT, filter="data")
    return bool(data)


FINAL = ("Completed", "Failed", "Succeeded", "Error", "not found")


def sync(jobs, results, interval):
    """Copy the result folder back until none of the jobs is pending/running."""
    seen, tries = set(), 0
    while True:
        tries += 1
        try:
            st = statuses(jobs)
            pull(results)
        except Exception as e:      # VPN hiccups: keep trying
            st = {j: f"sync error: {e}" for j in jobs}
        seen |= {j for j, s in st.items() if s not in FINAL and not s.startswith("sync error")}
        print(f"{time.strftime('%H:%M:%S')} " + " | ".join(f"{j}: {s}" for j, s in st.items()), flush=True)
        # a just-submitted job is "not found" for a while: only final once it was seen (or after 10 tries)
        if all(s in FINAL and (s != "not found" or j in seen or tries > 10) for j, s in st.items()):
            pull(results)
            for j in jobs:
                print(f"--- {j}\n" + ssh(f"tail -5 {REMOTE}/logs/run_{j}.out {REMOTE}/*/logs/run_{j}.out 2>/dev/null || true").decode(errors="replace"))
            return st
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["run", "push", "submit", "sync", "status"])
    ap.add_argument("--job", required=True, nargs="+", help="job name(s); sync/status accept several")
    ap.add_argument("--cpu", type=int, default=16)
    ap.add_argument("--mem", default="24Gi")
    ap.add_argument("--push", nargs="*", default=[])
    ap.add_argument("--results", nargs="*", default=[], help="folders and/or files to sync back")
    ap.add_argument("--cmd", default="")
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--study", default="", help="CFO_STUDY of the job (outputs and job log in <study>/)")
    a = ap.parse_args()
    if a.action in ("run", "push") and a.push:
        push(a.push)
    if a.action in ("run", "submit"):
        submit(a.job[0], a.cmd, a.cpu, a.mem, a.study)
    if a.action in ("run", "sync"):
        sync(a.job, a.results, a.interval)
    if a.action == "status":
        for j in a.job:
            print(j, status(j))
