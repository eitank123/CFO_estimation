"""
A small NN that grades the search cells of blind_fast.sps3_receive (cell_nn): P(this cell holds the true CFO).

The best-first search scores cells in posterior order and sends a cell to refinement + CA-SCL when its robust z
(metric vs the packet's wrong cells) exceeds z0 = 4. The z-test ignores where the cell sits in the posterior. The
network sees, per scored cell:
    z, log2(1 + its position in the search order), its posterior score relative to the packet's top cell, SNR,
    search round
and replaces the z-test (trigger: P > cell_tau). A grader that detects the true cell earlier at the same
false-trigger rate stops the search earlier: fewer metric evaluations, mainly at R = 1/10 (where the fast path
never works). ~0.6k MACs per scored cell (MACS).

    python blind_cell_nn.py data --mode blind --rate 1/10     # dump cells of the real receiver (eco7)
    python blind_cell_nn.py train --mode blind --rate 1/10    # -> blind/models/cell_nn_<mode>_<rate>.npz
"""
import argparse
import multiprocessing as mp
import os
import time

import numpy as np

import blind_cfo as bc

NF = 5
H = 16
MACS = NF * H + H * H + H
_W = {}
_MODE = {"blind": "v3 eco7 + CRC", "pilots": "Pilots N3x8 + v3 eco7 + CRC"}
_CUR = {"mode": "blind", "rate": "1/10"}


def _fname(mode, rate):
    return bc.path("models", f"cell_nn_{mode}_{rate.replace('/', '_')}.npz")


def set_model(mode, rate):
    _CUR.update(mode=mode, rate=rate)


def grade(F):
    """P(true cell) for features F (..., NF)."""
    key = (_CUR["mode"], _CUR["rate"])
    if key not in _W:
        z = np.load(_fname(*key))
        _W[key] = {k: z[k] for k in z.files}
    W = _W[key]
    h = np.maximum(F @ W["w1"] + W["b1"], 0)
    h = np.maximum(h @ W["w2"] + W["b2"], 0)
    return 1.0 / (1.0 + np.exp(-(h @ W["w3"] + W["b3"])[..., 0]))


def _gen(task):
    import blind_ber as bb
    import blind_fast as bf
    mode, rate, snr, seed, n = task
    code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    rng = np.random.default_rng(seed)
    spec = {**bb.RX[_MODE[mode]]}
    spec["sps"] = {**spec["sps"], "rate": rate}
    out = []
    for _ in range(n // 100):
        _, cw, r, rx, f, _ = bc.frames(100, code, snr, rng)
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        st = dict(decodes=0, metric_evals=0, dump=[], truth=f)
        bf.sps3_receive(r, rx, snr, code, sigma2, st, spec, sym)
        out += st["dump"]
    return np.concatenate(out) if out else np.zeros((0, NF + 1), np.float32)


def data(a):
    snrs = [float(s) for s in a.snrs.split(",")]
    tasks = [(a.mode, a.rate, s, a.seed + 100 * i + j, a.frames) for i, s in enumerate(snrs) for j in range(a.workers // len(snrs) or 1)]
    t0 = time.time()
    with mp.Pool(min(a.workers, len(tasks))) as pool:
        parts = pool.map(_gen, tasks)
    D = np.concatenate(parts).astype(np.float32)
    np.save(bc.path("results", f"cell_data_{a.mode}_{a.rate.replace('/', '_')}.npy"), D)
    print(f"{len(D)} cells, {int(D[:, -1].sum())} true ({time.time() - t0:.0f}s)", flush=True)
    print("DATA DONE", flush=True)


def train(a):
    import torch
    import torch.nn as nn
    torch.manual_seed(a.seed)
    D = np.load(bc.path("results", f"cell_data_{a.mode}_{a.rate.replace('/', '_')}.npy"))
    rng = np.random.default_rng(a.seed)
    i = rng.permutation(len(D))
    nv = len(D) // 5
    V, T = D[i[:nv]], D[i[nv:]]
    model = nn.Sequential(nn.Linear(NF, H), nn.ReLU(), nn.Linear(H, H), nn.ReLU(), nn.Linear(H, 1))
    pw = torch.tensor((1 - T[:, -1].mean()) / max(T[:, -1].mean(), 1e-6))
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-5)
    Xt, Yt = torch.from_numpy(T[:, :NF]), torch.from_numpy(T[:, -1])
    for ep in range(a.epochs):
        perm = torch.randperm(len(Xt))
        tot = 0.0
        for b in range(0, len(Xt), 4096):
            j = perm[b:b + 4096]
            loss = nn.functional.binary_cross_entropy_with_logits(model(Xt[j])[:, 0], Yt[j], pos_weight=pw ** 0.5)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            tot += loss.item() * len(j)
        if (ep + 1) % 5 == 0:
            print(f"epoch {ep + 1} loss {tot / len(Xt):.4f}", flush=True)
    sd = model.state_dict()
    np.savez(_fname(a.mode, a.rate), w1=sd["0.weight"].numpy().T, b1=sd["0.bias"].numpy(),
             w2=sd["2.weight"].numpy().T, b2=sd["2.bias"].numpy(), w3=sd["4.weight"].numpy().T, b3=sd["4.bias"].numpy())
    # held-out: detection of the true cells at the z-test's false-trigger rate, per SNR
    set_model(a.mode, a.rate)
    pv = grade(V[:, :NF])
    zv, yv, sv = V[:, 0], V[:, -1] > 0.5, np.round(V[:, 3] * 10, 1)
    for s in sorted(set(sv)):
        m = sv == s
        fpr_z = np.mean(zv[m & ~yv] > 4.0)
        tpr_z = np.mean(zv[m & yv] > 4.0)
        tau = np.quantile(pv[m & ~yv], 1 - max(fpr_z, 1e-6))
        print(f"{s:+.1f} dB: true cells {int((m & yv).sum())}, wrong {int((m & ~yv).sum())} | z>4: detect {tpr_z:.3f} at "
              f"false {fpr_z:.2e} | NN at the same false rate (tau {tau:.3f}): detect {np.mean(pv[m & yv] > tau):.3f}",
              flush=True)
    print("TRAIN DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["data", "train"])
    ap.add_argument("--mode", choices=["blind", "pilots"], default="blind")
    ap.add_argument("--rate", default="1/10")
    ap.add_argument("--snrs", default="-5,-4,-3,-2,-1,0")
    ap.add_argument("--frames", type=int, default=1200)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--seed", type=int, default=21)
    a = ap.parse_args()
    {"data": data, "train": train}[a.action](a)
