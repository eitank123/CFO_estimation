"""
Submit queued Run:ai jobs as soon as a slot is free (at most MAX_ACTIVE of the user's jobs Pending/Running), never
waiting for a whole batch. One `runai training list` per poll keeps the login-node load minimal.

    py multipath/slot_queue.py --queue jobs/queue_split1.txt --interval 120
Queue file: one job per line, "<job name>|<study or ->|<cmd for cluster.py submit>"; '#' lines are skipped.
"""
import argparse
import time

import cluster

MAX_ACTIVE = 8
ACTIVE = ("Pending", "Running", "Creating", "Initializing", "ContainerCreating")


RETRY_WINDOW = 600        # a job that is Failed within 10 min of its submission never started (Run:ai webhook
RETRIES = 20              # timeouts): it is resubmitted under <name>-r<k>


def active_jobs():
    out = cluster.ssh("runai training list 2>/dev/null").decode(errors="replace")
    rows = [l.split() for l in out.splitlines()[1:] if l.strip()]
    status = {r[0]: r[3] for r in rows if len(r) > 3}
    return [r[0] for r in rows if len(r) > 3 and r[3] in ACTIVE], {r[0] for r in rows if r}, status


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--interval", type=int, default=120)
    ap.add_argument("--cpu", type=int, default=16)
    ap.add_argument("--mem", default="24Gi")
    ap.add_argument("--max-active", type=int, default=MAX_ACTIVE, help="7 keeps one slot free for smoke tests")
    a = ap.parse_args()
    todo = [l.strip().split("|", 2) for l in open(a.queue, encoding="utf-8") if l.strip() and not l.startswith("#")]
    recent = {}                                                  # job -> (submit time, study, cmd, retry count)
    while todo or recent:
        try:
            act, known, status = active_jobs()
            for job, (t0, study, cmd, k) in list(recent.items()):
                if status.get(job) == "Failed" and time.time() - t0 < RETRY_WINDOW and k < RETRIES:
                    base = job.rsplit("-r", 1)[0] if k else job
                    todo.insert(0, [f"{base}-r{k + 1}", study, cmd])
                    recent.pop(job)
                    print(f"{time.strftime('%H:%M:%S')} {job} failed at start, resubmitting as {base}-r{k + 1}",
                          flush=True)
                elif time.time() - t0 >= RETRY_WINDOW or status.get(job) in ("Running", "Completed"):
                    recent.pop(job)
            todo = [t for t in todo if t[0] not in known]          # already submitted (e.g. a restarted queue)
            while todo and len(act) < a.max_active:
                job, study, cmd = todo.pop(0)
                k = int(job.rsplit("-r", 1)[1]) if "-r" in job and job.rsplit("-r", 1)[1].isdigit() else 0
                cluster.submit(job, cmd, a.cpu, a.mem, "" if study == "-" else study)
                recent[job] = (time.time(), study, cmd, k)
                act.append(job)
                print(f"{time.strftime('%H:%M:%S')} submitted {job} ({len(act)} active, {len(todo)} queued)", flush=True)
        except Exception as e:                                   # VPN hiccups: try again next poll
            print(f"{time.strftime('%H:%M:%S')} queue error: {e}", flush=True)
        if todo or recent:
            time.sleep(a.interval)
    print("queue empty", flush=True)
