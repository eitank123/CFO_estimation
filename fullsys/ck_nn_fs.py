"""
The checkpoint NN of the blind receiver (small_ck_nn.py CkNet, one model per checkpoint CKS) retrained on ONE
full-system format's own packets, instead of the 1/10, 2/5, 1/2 models of the 1024-symbol N = 2048 packets.

    data  the search packets (those the fast path fails) of the format, exactly as run_blind_fs sends and receives them:
          tx run_blind_fs.tx_packets (RMPolarCode.encode_rm -> [:, F.chan] -> modulate -> txrx_chain._transmit at
          --beta, f ~ U[-cfo_max, cfo_max], phase ~ U[0, 2 pi)), rx = the blind_fmt.BlindFormat context + rx_spec of the
          adopted receiver (BL: base25_qfix_fzs at 2/5, base2_qfix_fzs at 1/2, testing_s11g at 0.15 (vde32), with the
          format hooks nopi / bpsk_sq /
          ck_useful and the provisional options) + small_rx spec dump_pm: the cell-prior features and the partial path
          metrics (total, rate-0 part) at CK_FR of every cell x phase (CK_FR on the useful positions under ck_useful,
          the phases of nopi / bpsk_sq, as the search uses them); the true cell = the grid cell nearest to f
    SNR   training Es/N0 ~ U[lo, hi] per batch (CFG[fmt]["snr"]: the format's waterfall); validation at CFG[fmt]["val"]
    seeds SeedSequence([--seed, tag + TRAIN_TAG, kind, ...]): kind 0 training [producer, batch] (+ [2] its SNR), kind 1
          validation [Es/N0 code, chunk]; TRAIN_TAG = 900000 is disjoint from every reported run (tag) and from
          run_blind_fs --calib (tag + CALIB_TAG 500000)
    train streaming (each batch used once, as small_ck_nn): --producers processes fill a queue, the main process steps
          all CKS models on minibatches of --mb packets (AdamW, cross-entropy over the cells); the lr follows a cosine
          over max(step / (epochs x steps), elapsed / training budget), so the run always ends annealed inside --budget
          minutes; after every epoch (--steps steps) the mean true-cell rank on the validation set, the best model per
          checkpoint (mean log(1 + rank) over the validation points) saved to <models>/<name>_c<c>.npz
    eval  at the end, the saved models (read back through small_rx.ck_logp, the receiver's numpy path) vs the z-test on
          the validation set: true-cell rank mean / tails / quantiles per checkpoint, the full-decode metric rank, the
          NN shortlists (cumulative probability 1 - eps, >= nmin cells; the receiver: ck_keep 1e-3, ck_min 8)

    BLIND_STUDY=small_cfo python fullsys/ck_nn_fs.py --fmt id13 --design ga --part fs-cktr13
    -> small_cfo/blind/models/ck_nn_fs_id13_c{1..6}.npz, used by run_blind_fs.py --cknn fmt (the profile's checkpoint:
       c 3 = 1/4 at 2/5, c 2 = 3/16 at 1/2; 0.15 (vde32) run_blind_fs.CK_C c 3 = 1/4 or --ck-c)

Writes fullsys/results/ck_nn_fs_<part>.json (meta, data counts per SNR bin, per-epoch history, final eval; rewritten
after every epoch; refuses an existing part or existing models) and .prog ("done total elapsed_s"). Cluster only.
"""

import argparse
import itertools
import json
import multiprocessing as mp
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import run_blind_fs as rbf             # noqa: E402  (get_fmt, rx_spec, tx_packets: the run's own tx / rx)
from fullsys import run_polar_genie as pg           # noqa: E402

TRAIN_TAG = 900000                                  # training / validation seed tag offset (test: tag, calib: + 500000)
# per format: training Es/N0 range (dB), validation points, frames per producer batch (more where the fast path
# rarely fails), steps per epoch (sized for ~25 min on 16 cores, see the planning note in main)
CFG = {"id3": dict(snr=(-1.2, 0.8), val=(-1.0, -0.4, 0.4), batch=40, steps=150),
       "id13": dict(snr=(-1.0, 0.0), val=(-0.8, -0.4, 0.0), batch=40, steps=50),
       "id14s": dict(snr=(1.2, 2.2), val=(1.3, 1.6, 1.9), batch=200, steps=25),
       "id42b": dict(snr=(-4.4, -3.0), val=(-4.3, -4.0, -3.7), batch=200, steps=25),
       # vde32 (0.15 profile, testing_s11g: fast path off below 0.5 dB, every packet a search packet; BPSK bpsk_sq: 2
       # phases; N 2048, ~249 cells of 4 STEP): the dump costs ~1/10 of an id13 packet -> ~100-300 packets / s, the
       # trainer the limit; 250 steps x 30 epochs x 24 = 180000 planned (the time cosine anneals it if fewer arrive).
       # Below -5 dB allowed for VDE only (user)
       "vde32": dict(snr=(-6.6, -3.8), val=(-6.2, -5.4, -4.6), batch=40, steps=250)}
SNR_BIN = 0.1                                       # data counts per Es/N0 bin (frames, search packets)
KS = (1, 4, 16, 32, 64, 128)                        # true-cell rank tail fractions (rank >= K)
QS = (0.99, 0.999)
SHORT = ((1e-2, 8), (1e-3, 8), (1e-4, 8), (1e-3, 16))   # NN shortlists (eps, nmin); the receiver: (1e-3, 8)


def gen(fmt, F, sps, o, esn0, ent, batch, sub):
    """One batch of the format's packets through the receiver up to the search: (frames, x, pm, t) of its search
    packets (x None if the fast path delivered all)."""
    import small_rx
    _, f, _, v, rx = rbf.tx_packets(fmt, F, esn0, ent, batch, o)
    sigma2 = 1.0 / (2.0 * 10 ** (esn0 / 10))
    st = dict(decodes=0, metric_evals=0)
    xs, ps, ts = [], [], []
    with F:
        for a in range(0, batch, sub):
            sl = slice(a, min(a + sub, batch))
            d = {}
            small_rx.small_receive(v[sl], rx[sl], esn0, F.code, sigma2, st, {"sps": {**sps, "dump_pm": d}})
            if "x" in d:
                xs.append(d["x"])
                ps.append(d["pm"])
                ts.append(np.abs(d["g"][None] - f[sl][d["rem"], None]).argmin(1))
    if not xs:
        return batch, None, None, None
    return batch, np.concatenate(xs), np.concatenate(ps), np.concatenate(ts)


def _ctx(fmt, o):
    F = rbf.get_fmt(fmt, o)
    sps, _ = rbf.rx_spec(fmt, F, o, o["rx"])
    return F, sps


def _val_task(task):
    fmt, o, esn0, ent, batch, sub = task
    F, sps = _ctx(fmt, o)
    return gen(fmt, F, sps, o, esn0, ent, batch, sub)


def _producer(i, q, fmt, o, a):
    rbf._init()
    F, sps = _ctx(fmt, o)
    tag = pg.FMTS[fmt]["tag"] + TRAIN_TAG
    lo, hi = a.snr
    for j in itertools.count():
        ent = [a.seed, tag, 0, i, j]
        snr = float(np.random.default_rng(np.random.SeedSequence(ent + [2])).uniform(lo, hi))
        q.put((snr,) + gen(fmt, F, sps, o, snr, ent, a.batch, a.sub))


def collect_val(fmt, o, a, log):
    """Validation search packets per point: up to --val packets or --val-frames frames (16 workers, then closed)."""
    tag = pg.FMTS[fmt]["tag"] + TRAIN_TAG
    val, cnt = {}, {}
    for s in a.val_snrs:
        t0 = time.time()
        nch = -(-a.val_frames // a.batch)
        tasks = ((fmt, o, s, [a.seed, tag, 1, int(round(s * 1000)) + 100000, c], a.batch, a.sub) for c in range(nch))
        xs, ps, ts, fr = [], [], [], 0
        with Pool(a.workers, initializer=rbf._init) as pool:
            for n_, x, pm, t in pool.imap(_val_task, tasks):
                fr += n_
                if x is not None:
                    xs.append(x)
                    ps.append(pm)
                    ts.append(t)
                if sum(len(t_) for t_ in ts) >= a.val or time.time() - t0 > 60 * a.val_time:
                    break
            pool.terminate()
        n = sum(len(t_) for t_ in ts)
        cnt[f"{s:+.2f}"] = dict(frames=fr, search=n, time_s=round(time.time() - t0, 1))
        log(f"val {fmt} {s:+.2f} dB: {n} search packets of {fr} frames (search fraction {n / max(fr, 1):.4f}), "
            f"{time.time() - t0:.0f} s")
        if n:
            val[s] = (np.concatenate(xs)[:a.val], np.concatenate(ps)[:a.val], np.concatenate(ts)[:a.val])
    return val, cnt


def _ranks(s, t):
    return (s > s[np.arange(len(t)), t][:, None]).sum(1)


def _short(lp, t, eps, nmin):
    o = np.argsort(-lp, 1)
    cp = np.cumsum(np.exp(np.take_along_axis(lp, o, 1)), 1)
    n = np.maximum(nmin, (cp < 1 - eps).sum(1) + 1)
    return n, _ranks(lp, t) < n


def final_eval(val, name, CKS, log):
    """The saved models (small_rx.ck_logp, numpy) vs the z-test on the validation set."""
    import small_rx as sr
    out = []
    for s, (x, pm, t) in val.items():
        G = x.shape[1]
        row = {"snr": s, "cells": G, "packets": len(t), "phases": int(pm.shape[2])}
        zf = _ranks(sr.ck_features(x, pm, len(sr.CK_FR) - 1)[..., sr.NF], t)
        row["full"] = {"mean": float(zf.mean()), **{str(q): float(np.quantile(zf, q)) for q in QS}}
        log(f"eval {s:+.2f} dB ({len(t)} packets, {G} cells, {pm.shape[2]} phases): full-decode metric rank mean "
            f"{zf.mean():.1f}, q99 {np.quantile(zf, .99):.0f}, q99.9 {np.quantile(zf, .999):.0f}")
        for c in CKS:
            X = sr.ck_features(x, pm, c)
            lp = sr.ck_logp("blind", c, X, name)
            fr = sr.CK_FR[c]
            for nm, sc in (("z", X[..., sr.NF]), ("nn", lp)):
                rk = _ranks(sc, t)
                row[f"{nm} c{c}"] = {"mean": float(rk.mean()), **{str(K): float(np.mean(rk >= K)) for K in KS},
                                     **{str(q): float(np.quantile(rk, q)) for q in QS}}
                log(f"  ck {fr:.4g} {nm:2s}: mean rank {rk.mean():6.1f}  q99 {np.quantile(rk, .99):5.0f}  "
                    f"q99.9 {np.quantile(rk, .999):5.0f}  " + " ".join(f">={K} {np.mean(rk >= K):.4f}" for K in KS))
            for eps, nmin in SHORT:
                n, hit = _short(lp, t, eps, nmin)
                w = fr + (1 - fr) * n.mean() / G
                row[f"short c{c} {eps:g} {nmin}"] = {"size": float(n.mean()), "miss": float(1 - hit.mean()),
                                                     "work": float(w)}
                log(f"    NN shortlist 1-{eps:g}, >= {nmin}: {n.mean():6.1f} cells, missed {1 - hit.mean():.4f}, "
                    f"work {w:.3f} of the full grid")
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fmt", required=True, choices=list(CFG))
    ap.add_argument("--part", required=True, help="results fullsys/results/ck_nn_fs_<part>.json / .prog")
    ap.add_argument("--name", default=None, help="model prefix (default ck_nn_fs_<fmt>): <models>/<name>_c<c>.npz")
    ap.add_argument("--snr", nargs=2, type=float, default=None, help="training Es/N0 range (default CFG[fmt])")
    ap.add_argument("--val-snrs", nargs="+", type=float, default=None, help="validation Es/N0 (default CFG[fmt])")
    ap.add_argument("--val", type=int, default=400, help="validation search packets per point")
    ap.add_argument("--val-frames", type=int, default=60000, help="max frames per validation point")
    ap.add_argument("--val-time", type=float, default=2.0, help="max minutes per validation point")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=None, help="steps per epoch (default CFG[fmt])")
    ap.add_argument("--mb", type=int, default=24, help="search packets per training step")
    ap.add_argument("--batch", type=int, default=None, help="frames per producer batch (default CFG[fmt])")
    ap.add_argument("--sub", type=int, default=50, help="packets per small_receive call (run_blind_fs --sub)")
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--budget", type=float, default=25.0, help="wall-clock minutes of the whole run (training stops, "
                    "annealed, in time for the final eval)")
    ap.add_argument("--producers", type=int, default=15)
    ap.add_argument("--workers", type=int, default=16, help="validation collection pool")
    ap.add_argument("--seed", type=int, default=41)
    # the run_blind_fs receiver / format options (defaults = run_blind_fs's; the full-system runs use --design ga)
    ap.add_argument("--crc", type=int, default=32, choices=[32, 16])
    ap.add_argument("--beta", type=float, default=pg.ROLLOFF)
    ap.add_argument("--cfo-max", type=float, default=0.03)
    ap.add_argument("--rx", default=None)
    ap.add_argument("--rho", default="scaled", choices=["scaled", "table", "min"])
    ap.add_argument("--fzstop", default="off")
    ap.add_argument("--spec", default="off", choices=["off", "adopted"])
    ap.add_argument("--ck", default="useful", choices=["useful", "codeword"])
    ap.add_argument("--bpsk-phase", default="sq", choices=["sq", "4th"])
    ap.add_argument("--extra-in-fz", action="store_true")
    ap.add_argument("--no-chan-intlv", action="store_true")
    ap.add_argument("--design", default="pw", choices=["pw", "ga"])
    ap.add_argument("--design-snr", type=float, default=None)
    a = ap.parse_args()
    import blind_cfo as bc
    import small_rx as sr
    from small_ck_nn import CKS, ck_net, save
    assert bc.STUDY == "small_cfo", "run with BLIND_STUDY=small_cfo"
    t_start = time.time()
    fmt = a.fmt
    cf = CFG[fmt]
    a.snr = tuple(a.snr or cf["snr"])
    a.val_snrs = tuple(a.val_snrs or cf["val"])
    a.steps = a.steps or cf["steps"]
    a.batch = a.batch or cf["batch"]
    name = a.name or f"ck_nn_fs_{fmt}"
    if a.design == "ga" and a.design_snr is None:
        a.design_snr = pg.DESIGN_SNR[fmt]
    o = dict(crc=a.crc, beta=a.beta, cfo_max=a.cfo_max, extra_in_fz=a.extra_in_fz, rho=a.rho, fzstop=a.fzstop,
             spec=a.spec, cknn="keep", ck=a.ck, bpsk_phase=a.bpsk_phase, sub=a.sub, rx=a.rx, dump=None,
             chan=not a.no_chan_intlv, design=a.design, design_snr=a.design_snr, cap_core=None, cknn_name=None,
             ck_c=None)
    os.makedirs(rbf.RESULTS, exist_ok=True)
    path = os.path.join(rbf.RESULTS, f"ck_nn_fs_{a.part}.json")
    prog_path = os.path.join(rbf.RESULTS, f"ck_nn_fs_{a.part}.prog")
    if os.path.exists(path):
        sys.exit(f"{path} exists: use a new --part")
    mpaths = {c: bc.path("models", f"{name}_c{c}.npz") for c in CKS}
    if any(os.path.exists(p) for p in mpaths.values()):
        sys.exit(f"models {name}_c*.npz exist: use a new --name")
    F, sps = _ctx(fmt, o)
    budget = a.budget * 60.0

    def log(s):
        print(s, flush=True)

    def prog(done):
        with open(prog_path, "w") as fh:
            fh.write(f"{min(done, 1.0):.4f} 1 {time.time() - t_start:.0f}\n")

    log(f"ck_nn_fs {vars(a)} | model {name} | {F.info()} | profile {rbf.BL[fmt]} | ck_nn {sps.get('ck_nn')}")
    doc = dict(meta=dict(args=vars(a), fmt=fmt, name=name, models={str(c): mpaths[c] for c in CKS},
                         format=F.info(), profile=rbf.BL[fmt][0], rx=a.rx or rbf.BL[fmt][1],
                         seed_tag=pg.FMTS[fmt]["tag"] + TRAIN_TAG, train_tag=TRAIN_TAG, calib_tag=rbf.CALIB_TAG,
                         ck_fr={str(c): sr.CK_FR[c] for c in CKS},
                         sps={k: (repr(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                              for k, v in sps.items()}),
               val_counts=None, data=None, history=[], eval=None)

    def dump():
        with open(path + ".tmp", "w") as fh:
            json.dump(doc, fh, indent=1)
        os.replace(path + ".tmp", path)

    prog(0.0)
    val, doc["val_counts"] = collect_val(fmt, o, a, log)
    assert val, "no validation search packets at any point: move --val-snrs down"
    dump()
    XV = {c: {s: sr.ck_features(x, pm, c) for s, (x, pm, t) in val.items()} for c in CKS}   # (once: every epoch)
    for s, (x, pm, t) in val.items():
        log(f"z-test {s:+.2f}: mean rank " + " ".join(
            f"[{sr.CK_FR[c]:.4g}] {_ranks(sr.ck_features(x, pm, c)[..., sr.NF], t).mean():.1f}"
            for c in CKS + (len(sr.CK_FR) - 1,)))
    q = mp.Queue(maxsize=64)
    procs = [mp.Process(target=_producer, daemon=True, args=(i, q, fmt, o, a)) for i in range(a.producers)]
    for p in procs:
        p.start()
    import torch
    import torch.nn as nn
    torch.manual_seed(a.seed)
    torch.set_num_threads(1)
    CkNet = ck_net()
    models = {c: CkNet() for c in CKS}
    opts = {c: torch.optim.AdamW(models[c].parameters(), lr=a.lr, weight_decay=1e-5) for c in CKS}
    total = a.epochs * a.steps
    t_tr0 = time.time()
    t_tr = max(budget - (t_tr0 - t_start) - 90.0, 60.0)      # training seconds (90 s kept for the final eval)
    log(f"training: {a.epochs} epochs x {a.steps} steps x {a.mb} packets = {total * a.mb} search packets planned, "
        f"{t_tr / 60:.1f} min left in the budget")
    nb = int(round((a.snr[1] - a.snr[0]) / SNR_BIN)) + 1
    d_fr, d_se = np.zeros(nb, int), np.zeros(nb, int)
    pend = {c: [] for c in CKS}
    pend_t = []
    best = {c: np.inf for c in CKS}
    step, stop = 0, False

    def lr_at():
        pr = min(1.0, max(step / total, (time.time() - t_tr0) / t_tr))
        return a.lr * (1e-2 + (1 - 1e-2) * 0.5 * (1 + np.cos(np.pi * pr))), pr

    for ep in range(1, a.epochs + 1):
        t0, tot, ns = time.time(), {c: 0.0 for c in CKS}, 0
        for m in models.values():
            m.train()
        while ns < a.steps:
            snr, n_, x, pm, t = q.get(timeout=900)               # (a dead producer pool: queue.Empty, not a hang)
            b_ = int(np.clip(round((snr - a.snr[0]) / SNR_BIN), 0, nb - 1))
            d_fr[b_] += n_
            if x is None:
                continue
            d_se[b_] += len(t)
            for c in CKS:
                pend[c].append(sr.ck_features(x, pm, c))
            pend_t.append(t)
            if sum(len(t_) for t_ in pend_t) < a.mb:
                continue
            tt = torch.from_numpy(np.concatenate(pend_t)).long()
            lr, pr = lr_at()
            for c in CKS:
                X = torch.from_numpy(np.concatenate(pend[c]))
                for g_ in opts[c].param_groups:
                    g_["lr"] = lr
                loss = nn.functional.cross_entropy(models[c](X), tt)
                opts[c].zero_grad(set_to_none=True)
                loss.backward()
                opts[c].step()
                tot[c] += loss.item()
                pend[c] = []
            pend_t = []
            step += 1
            ns += 1
            if pr >= 1.0:
                stop = True
                break
        row = {"epoch": ep, "steps": ns, "step": step, "lr": float(lr_at()[0]), "time_s": round(time.time() - t0, 1),
               "packets": int(d_se.sum()), "frames": int(d_fr.sum())}
        line = f"Epoch {ep:3d}/{a.epochs}"
        for c in CKS:
            models[c].eval()
            res = {}
            with torch.no_grad():
                for s, (x, pm, t) in val.items():
                    lg = models[c](torch.from_numpy(XV[c][s])).numpy()
                    res[f"{s:+.2f}"] = float(_ranks(lg, t).mean())
            sc = float(np.mean([np.log1p(v) for v in res.values()]))
            mark = ""
            if sc < best[c]:
                best[c] = sc
                save(models[c], mpaths[c])
                mark = "*"
            row[str(c)] = {"loss": tot[c] / max(ns, 1), "mean_rank": res, "score": sc, "saved": bool(mark)}
            line += f" | c{c} CE {tot[c] / max(ns, 1):.3f} " + " ".join(f"{v:.1f}" for v in res.values()) + mark
        doc["history"].append(row)
        el = time.time() - t_start
        log(line + f" | {row['time_s']:.0f}s | packets {row['packets']} of {row['frames']} frames "
                   f"({row['packets'] / max(el, 1):.1f}/s) | {el / 60:.1f} min")
        doc["data"] = dict(snr_bin=SNR_BIN, snr_lo=a.snr[0], frames=d_fr.tolist(), search=d_se.tolist())
        dump()
        prog(0.95 * min(1.0, max(step / total, (time.time() - t_tr0) / t_tr)))
        if stop:
            log(f"  training budget reached after {step} of {total} steps: stopping (lr annealed)")
            break
    for p in procs:
        p.terminate()
    doc["meta"]["steps_done"], doc["meta"]["train_s"] = step, round(time.time() - t_tr0, 1)
    log("TRAIN DONE")
    doc["eval"] = final_eval(val, name, CKS, log)
    doc["meta"]["total_s"] = round(time.time() - t_start, 1)
    dump()
    prog(1.0)
    log(f"EVAL DONE ({doc['meta']['total_s'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
