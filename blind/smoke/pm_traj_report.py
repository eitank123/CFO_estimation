"""Replays CFO-cell pruning / early-stop rules on the partial path metrics saved by pm_traj.py (analysis only, no
simulation). A rule sees only what a real decoder would: at checkpoint j the alive cells' cumulative path metric
PM_j; their robust z is computed among the ALIVE cells (median / MAD); cells with z <= tau are dropped (the best kmin
always survive, so the z keeps a population); a dropped cell costs only the part of the codeword decoded so far.
    no checkpoints   every cell scored to the end (the current search over the whole small range)
    prune            drop the losers at the checkpoints; the survivors are scored to the end
    early stop       at a checkpoint, a cell with z > T_win ends the CFO search: it is decoded, the rest is dropped
Prints, per rate / SNR and rule: P(true cell lost), the true cell's final rank among the survivors, the work in
full-metric units per cell (1.0 = no checkpoints), and for early stop how often it stops and how often wrongly.
    BLIND_STUDY=small_cfo python blind/smoke/pm_traj_report.py --tag b"""
import argparse
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import blind_cfo as bc


def rz(x):
    """Robust z of the rows of x (P, cells) with NaN = not alive: (median - x) / (1.4826 MAD)."""
    med = np.nanmedian(x, 1, keepdims=True)
    mad = 1.4826 * np.nanmedian(np.abs(x - med), 1, keepdims=True) + 1e-6
    return (med - x) / mad


def replay(PM, true, frac, cks, tau, kmin, win=None):
    """PM (P, C, cells) at the saved checkpoints frac; cks = indices of the checkpoints used (distinct fractions, the
    last = the full metric). The true CFO counts as found when its nearest cell or a neighbour (+-1) is decoded.
    Early stop: the best alive cell with z > win is decoded at once; if it is the true one (or a neighbour) the search
    ends, otherwise it cost one decode and the pruning goes on. Returns lost (P,): the true and both neighbours dropped
    and no early stop on them; rank of the best true / neighbour cell among the final survivors (P,); work (P,) in
    full-metric units per cell; stop (P,) the checkpoint index of a right early stop or -1; wrong (P,) early-stop
    decodes on wrong cells."""
    P, _, n = PM.shape
    rows = np.arange(P)
    tn = np.clip(true[:, None] + np.array([-1, 0, 1])[None], 0, n - 1)      # the true cell and its neighbours
    alive = np.ones((P, n), bool)
    work = np.zeros(P)
    prev = 0.0
    stop = np.full(P, -1)
    wrong = np.zeros(P, int)
    tried = np.zeros((P, n), bool)
    for j in cks:
        act = stop < 0
        work[act] += alive[act].sum(1) * (frac[j] - prev)    # the alive cells decoded from prev to frac[j]
        prev = frac[j]
        z = np.where(alive, rz(np.where(alive, PM[:, j], np.nan)), -np.inf)
        if j == cks[-1]:
            break
        if win is not None:
            zb = np.where(tried, -np.inf, z)
            b = zb.argmax(1)
            s = act & (zb[rows, b] > win)
            ok = (np.abs(b - true) <= 1) & s
            stop[ok] = j
            wrong[s & ~ok] += 1
            tried[rows[s], b[s]] = True
        keep = z > tau
        top = np.argsort(-z, 1)[:, :kmin]
        keep[rows[:, None], top] = True
        alive &= keep
    found = alive[rows[:, None], tn].any(1)
    lost = ~found & (stop < 0)
    zt = np.where(alive[rows[:, None], tn], z[rows[:, None], tn], -np.inf).max(1)
    rank = (z > zt[:, None]).sum(1)
    return lost, rank, work / n, stop, wrong


def replay2(PM, true, frac, cks, tau, kmin, win=None, coarse=False):
    """replay() with an optional coarse-to-fine start: up to the first checkpoint only every other cell is decoded;
    there the neighbours of the surviving cells join (their decode up to that checkpoint is charged then) and the
    pruning goes on over all alive cells. Returns lost, work, right early stops, wrong early-stop decodes."""
    P, _, n = PM.shape
    rows = np.arange(P)
    tn = np.clip(true[:, None] + np.array([-1, 0, 1])[None], 0, n - 1)
    alive = np.ones((P, n), bool)
    if coarse:
        alive[:, 1::2] = False
    work = np.zeros(P)
    prev = 0.0
    stop = np.full(P, -1)
    wrong = np.zeros(P, int)
    tried = np.zeros((P, n), bool)
    for jj, j in enumerate(cks):
        act = stop < 0
        work[act] += alive[act].sum(1) * (frac[j] - prev)
        prev = frac[j]
        z = np.where(alive, rz(np.where(alive, PM[:, j], np.nan)), -np.inf)
        if j == cks[-1]:
            break
        if win is not None:
            zb = np.where(tried, -np.inf, z)
            b = zb.argmax(1)
            s = act & (zb[rows, b] > win)
            ok = (np.abs(b - true) <= 1) & s
            stop[ok] = j
            wrong[s & ~ok] += 1
            tried[rows[s], b[s]] = True
        keep = z > tau
        top = np.argsort(-z, 1)[:, :kmin]
        keep[rows[:, None], top] = True
        alive &= keep
        if coarse and jj == 0:                                # the neighbours of the surviving coarse cells join
            nb = np.zeros_like(alive)
            nb[:, 1:] |= alive[:, :-1]
            nb[:, :-1] |= alive[:, 1:]
            new = nb & ~alive
            new[:, 0::2] = False
            work[stop < 0] += new[stop < 0].sum(1) * frac[j]
            alive |= new
    found = alive[rows[:, None], tn].any(1)
    return ~found & (stop < 0), work / n, stop, wrong


def cks_of(frac, targets):
    """Indices of the distinct saved checkpoints nearest the target fractions (always ending at the full metric)."""
    idx = sorted({int(np.argmin(np.abs(frac - t))) for t in targets} | {len(frac) - 1})
    out = []
    for i in idx:                                             # one index per distinct fraction
        if not out or frac[i] > frac[out[-1]] + 1e-9:
            out.append(i)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="b")
    a = ap.parse_args()
    for fn in sorted(glob.glob(bc.path("results", f"pm_traj_{a.tag}_*.npz"))):
        D = np.load(fn)
        PM, true, frac = D["PM"], D["true"], D["frac"]
        P, C, n = PM.shape
        print(f"\n== {os.path.basename(fn)}: {P} packets, {n} cells, checkpoints {np.round(frac, 3).tolist()}")
        full = [C - 1]
        lost, rank, work, *_ = replay(PM, true, frac, full, 0, n)
        print(f"  no checkpoints: true cell (or a neighbour) best {np.mean(rank == 0):.4f}, in top 2 {np.mean(rank < 2):.4f}, "
              f"top 4 {np.mean(rank < 4):.4f}; work 1.000")
        for name, tg in (("1/8,1/4,1/2,1", (1 / 8, 1 / 4, 1 / 2)), ("1/4,1/2,1", (1 / 4, 1 / 2)), ("1/2,1", (1 / 2,)),
                         ("1/4,3/8,1/2,3/4,1", (1 / 4, 3 / 8, 1 / 2, 3 / 4))):
            cks = cks_of(frac, tg)
            for tau in (-1.0, -0.5, 0.0, 0.5, 1.0):
                for kmin in (8, 16, 32):
                    lost, rank, work, *_ = replay(PM, true, frac, cks, tau, kmin)
                    print(f"  prune at {name:18s} tau {tau:+.1f} kmin {kmin:2d}: lost {lost.mean():.4f} ({lost.sum():3d}), "
                          f"true in top 2 {np.mean(~lost & (rank < 2)):.4f}, work {work.mean():.3f}")
        for name, tg in (("1/8,1/4,1/2,1", (1 / 8, 1 / 4, 1 / 2)), ("1/4,1/2,1", (1 / 4, 1 / 2))):
            cks = cks_of(frac, tg)
            for win in (6, 8, 10, 12, 15, 20):
                lost, rank, work, stop, wrong = replay(PM, true, frac, cks, -0.5, 16, win)
                print(f"  early stop z > {win:2d} at {name} (prune tau -0.5, kmin 16): right stops {np.mean(stop >= 0):.3f}, "
                      f"wrong-stop decodes {wrong.mean():.3f}/packet, lost {lost.mean():.4f}, work {work.mean():.3f}")
