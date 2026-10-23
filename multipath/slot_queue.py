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


def active_jobs():
    out = cluster.ssh("runai training list 2>/dev/null").decode(errors="replace")
    rows = [l.split() for l in out.splitlines()[1:] if l.strip()]
    return [r[0] for r in rows if len(r) > 3 and r[3] in ACTIVE], {r[0] for r in rows if r}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--interval", type=int, default=120)
    ap.add_argument("--cpu", type=int, default=16)
    ap.add_argument("--mem", default="24Gi")
    a = ap.parse_args()
    todo = [l.strip().split("|", 2) for l in open(a.queue, encoding="utf-8") if l.strip() and not l.startswith("#")]
    while todo:
        try:
            act, known = active_jobs()
            todo = [t for t in todo if t[0] not in known]          # already submitted (e.g. a restarted queue)
            while todo and len(act) < MAX_ACTIVE:
                job, study, cmd = todo.pop(0)
                cluster.submit(job, cmd, a.cpu, a.mem, "" if study == "-" else study)
                act.append(job)
                print(f"{time.strftime('%H:%M:%S')} submitted {job} ({len(act)} active, {len(todo)} queued)", flush=True)
        except Exception as e:                                   # VPN hiccups: try again next poll
            print(f"{time.strftime('%H:%M:%S')} queue error: {e}", flush=True)
        if todo:
            time.sleep(a.interval)
    print("queue empty", flush=True)
