"""
Live progress bars for the Run:ai training jobs in ~/CFO_estimation on bhn20.

Jobs are discovered from the run_*.sh scripts (job name after "-n", log after "> ").
Progress and ETA come from the "Epoch i/N | ... | <sec>s" lines in each log.

Usage (VS Code terminal):
    py watch_jobs.py            # refresh every 20 s, Ctrl+C to stop
    py watch_jobs.py --once
"""

import argparse
import os
import re
import subprocess
import time

SSH_DIR = os.path.join(os.path.expanduser("~"), ".ssh")
SSH = ["ssh", "-F", os.path.join(SSH_DIR, "config"),
       "-o", "UserKnownHostsFile=" + os.path.join(SSH_DIR, "known_hosts"),
       "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "bhn20"]

REMOTE = r"""
cd ~/CFO_estimation
echo @@LIST; runai training list 2>/dev/null
for s in run_*.sh; do
  n=$(grep -oE 'submit python -n [^ ]+' "$s" | head -1 | awk '{print $4}')
  l=$(grep -oE '> [^ ]+\.log' "$s" | tail -1 | awk '{print $2}')
  echo "@@JOB $n $l"
  [ -f "$l" ] && grep -E '^Epoch|Fusion total|TEST DONE|Traceback|Error' "$l" | tail -8
done
"""

EPOCH_RE = re.compile(r"^Epoch\s+(\d+)/(\d+).*?val MSE/CRB mean\s+([\d.]+).*?\|\s*(\d+)s")
FINAL_TEST_SEC = 90
BAR_WIDTH = 40


def fetch():
    out = subprocess.run(SSH + [REMOTE], capture_output=True, text=True, timeout=90).stdout
    status, jobs, cur = {}, [], None
    section = None
    for line in out.splitlines():
        if line.startswith("@@LIST"):
            section = "list"
        elif line.startswith("@@JOB"):
            section = "job"
            parts = line.split()
            cur = {"name": parts[1] if len(parts) > 1 else "?", "log": parts[2] if len(parts) > 2 else "?",
                   "epochs": [], "done": False, "error": False}
            jobs.append(cur)
        elif section == "list":
            cols = line.split()
            if len(cols) >= 4 and cols[1] == "Training":
                status[cols[0]] = cols[3]
        elif section == "job" and cur is not None:
            m = EPOCH_RE.search(line)
            if m:
                cur["epochs"].append(tuple(float(x) for x in m.groups()))
            elif "Fusion total" in line or "TEST DONE" in line:
                cur["done"] = True
            elif "Traceback" in line or "Error" in line:
                cur["error"] = True
    for j in jobs:
        j["status"] = status.get(j["name"], "Deleted")
    return jobs


def fmt_time(sec):
    sec = int(max(0, sec))
    return f"{sec // 3600}h{sec % 3600 // 60:02d}m" if sec >= 3600 else f"{sec // 60}m{sec % 60:02d}s"


def render(jobs):
    lines = [f"Run:ai jobs on bhn20  ({time.strftime('%H:%M:%S')})", ""]
    for j in jobs:
        if j["status"] == "Deleted" and not j["epochs"]:
            continue
        if j["epochs"]:
            ep, total, best_val, _ = j["epochs"][-1]
            secs = [e[3] for e in j["epochs"][-5:]]
            frac = ep / total
            if j["done"]:
                frac, eta = 1.0, "done"
            else:
                eta = fmt_time((total - ep) * sum(secs) / len(secs) + FINAL_TEST_SEC)
            val = f"last val MSE/CRB {best_val:.3f}"
            prog = f"epoch {int(ep)}/{int(total)}"
        else:
            frac, eta, val, prog = 0.0, "-", "", "starting"
        if j["error"]:
            eta = "ERROR - check log"
        filled = int(round(frac * BAR_WIDTH))
        bar = "#" * filled + "-" * (BAR_WIDTH - filled)
        lines.append(f"{j['name']:<22} [{bar}] {frac * 100:5.1f}%  {prog:<14} ETA {eta:<10} {j['status']:<10} {val}")
    return "\n".join(lines)


HERE = os.path.dirname(os.path.abspath(__file__))
SYNC_EXT = (".png", ".log", ".pth", ".npy")
SYNC_SINCE = time.mktime((2026, 10, 18, 0, 0, 0, 0, 0, -1))  # skip the original Aug checkpoints


def sync_outputs():
    """Download result files that are new or changed on the server. Never touches .py/.sh."""
    listing = subprocess.run(SSH + ["cd ~/CFO_estimation && find . -maxdepth 1 -type f -printf '%f\\t%s\\t%T@\\n'"],
                             capture_output=True, text=True, timeout=90).stdout
    wanted = []
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) != 3 or not parts[0].endswith(SYNC_EXT):
            continue
        name, size, mtime = parts[0], int(parts[1]), float(parts[2])
        if mtime < SYNC_SINCE:
            continue
        local = os.path.join(HERE, name)
        if not os.path.exists(local) or os.path.getsize(local) != size or os.path.getmtime(local) < mtime - 1:
            wanted.append(name)
    if wanted:
        tar = subprocess.run(SSH + ["cd ~/CFO_estimation && tar cf - " + " ".join(f"'{w}'" for w in wanted)],
                             capture_output=True, timeout=300).stdout
        subprocess.run(["tar", "xf", "-", "-C", HERE], input=tar, check=True)
    return wanted


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=20)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--sync", action="store_true",
                    help="write progress.txt and download new results into this folder")
    args = ap.parse_args()
    os.system("")  # enable ANSI escapes in the Windows console
    synced = []
    while True:
        try:
            text = render(fetch())
            if args.sync:
                new = sync_outputs()
                if new:
                    synced = (new + synced)[:15]
                text += "\n\nRecently downloaded:\n" + ("\n".join("  " + s for s in synced) or "  (nothing yet)")
        except Exception as e:  # keep watching through transient SSH failures
            text = f"fetch failed at {time.strftime('%H:%M:%S')}: {e}"
        if args.sync:
            with open(os.path.join(HERE, "progress.txt"), "w", encoding="utf-8") as f:
                f.write(text + f"\n\n(updates every {args.interval}s)\n")
        if args.once:
            print(text)
            break
        if not args.sync:
            print("\033[H\033[J" + text + "\n\nCtrl+C to stop", flush=True)
        time.sleep(args.interval)
