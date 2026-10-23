"""
CFO NN v2: a light correction network on top of the ML estimate (full Tx/Rx chain, 128 known symbols).

The current SNR-aware NN (lag correlations + SNR -> MLP) is 4x the CRB at Es/N0 = -5 dB and 2-4 % worse than M&M
from -2 dB up. The ML estimate (FFT-256 peak + 2 Newton steps) is 1.4x the CRB at -5 dB, because the periodogram
peak does not break down where the lag correlations do. So v2 starts from ML and learns only a small correction:

    f_hat = f_ML + BIN * MLP(inputs),   last layer zero-initialised (an untrained v2 IS the ML estimator)

Inputs ("light", 12 values): SNR, (f_ML - f_FFT)/BIN, (f_MM - f_ML)/BIN, and the 8 FFT-peak features of
train_fft_nn.fft_features (coarse frequency, peak and neighbour magnitudes, neighbour/peak ratios), plus a
constant-free bias. With (f_MM - f_ML) the network can lean on M&M where M&M is better (high SNR).
"lag" models add the 64 x 4 lag-correlation features of the current NN.

Loss = squared error / CRB(SNR), Es/N0 ~ U[-6, 11] dB, CFO ~ U[-0.2, 0.2], as the current NN.

    python train_cfo_v2.py --name light32 --arch light --hidden 32 16 --epochs 80 --producers 15
    python train_cfo_v2.py --name light32 --eval-only        # the large test (1e6 frames at -5..-3 dB)
Checkpoint: models/cfo_v2_<name>.pth; test table: logs/cfo_v2_<name>_test.json
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn

import paths
from train_fft_nn import BIN, N_AUX, fft_features, ml_estimate
from train_snr_nn import (MAX_CFO, MAX_LAG, SNR_CENTER, SNR_SCALE, SNRAwareCFOEstimator, count_params, crb,
                          lag_features, make_z, mm_estimate)

CURRENT_PATH = paths.model("snr_aware_cfo_model_L64_chain150.pth")     # the NN used in polar_ber_experiment
TEST_SNRS = [-5, -4, -3, -2, -1, 0, 2, 5, 10]
N_LIGHT = 3 + N_AUX                                                      # snr, ml-fc, mm-ml, aux


def features(z, snr_db):
    """All inputs from z (B, L) complex128 and SNR (B,) dB: dict of float32 tensors + the ML estimate."""
    lag, R = lag_features(z)
    aux, fc = fft_features(z)
    ml = ml_estimate(z, fc).double()[:, 0]                 # normalised CFO
    mm = mm_estimate(R).double()[:, 0]
    s = ((torch.as_tensor(snr_db, dtype=torch.float64) - SNR_CENTER) / SNR_SCALE)
    light = torch.stack([s, (ml - fc / MAX_CFO) / BIN, ((mm - ml) / BIN).clamp(-20, 20)], dim=1)
    return {"light": torch.cat([light.float(), aux], dim=1), "lag": lag.flatten(1), "ml": ml.float(),
            "mm": mm.float()}


class CFOv2(nn.Module):
    def __init__(self, arch="light", hidden=(32, 16)):
        super().__init__()
        self.arch = arch
        d = N_LIGHT + (MAX_LAG * 4 if arch == "lag" else 0)
        layers = []
        for h in hidden:
            layers += [nn.Linear(d, h), nn.GELU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, f):
        x = f["light"] if self.arch == "light" else torch.cat([f["light"], f["lag"]], dim=1)
        return f["ml"] + BIN * self.net(x)[:, 0]               # normalised CFO


def macs(model):
    return sum(m.in_features * m.out_features for m in model.modules() if isinstance(m, nn.Linear))


def batch(B, lo, hi, gen, fixed=None):
    z, y, snr = make_z(B, lo, hi, gen, fixed)
    return features(z, snr), y[:, 0].float(), snr.float()


def _producer(seed, q, B, lo, hi):
    torch.set_num_threads(1)
    gen = torch.Generator().manual_seed(seed)
    while True:
        f, y, s = batch(B, lo, hi, gen)
        q.put(({k: v.numpy() for k, v in f.items()}, y.numpy(), s.numpy()))


def loss_fn(pred, y, snr):
    c = torch.as_tensor(crb(snr.double().numpy()), dtype=torch.float32)
    return (((pred - y) * MAX_CFO) ** 2 / c).mean()


def train(args):
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    model = CFOv2(args.arch, tuple(args.hidden))
    print(f"{args.name}: arch {args.arch} hidden {args.hidden} params {count_params(model)} MLP MACs {macs(model)}",
          flush=True)
    vgen = torch.Generator().manual_seed(args.seed + 1)
    val = {s: batch(args.val_per_snr, s, s, vgen, s) for s in TEST_SNRS}
    import multiprocessing as mp
    q = mp.Queue(maxsize=64)
    for i in range(args.producers):
        mp.Process(target=_producer, daemon=True, args=(args.seed + 1000 * (i + 1), q, args.batch, -6.0, 11.0)).start()
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    best = float("inf")
    for ep in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            f, y, s = q.get()
            f = {k: torch.from_numpy(v) for k, v in f.items()}
            loss = loss_fn(model(f), torch.from_numpy(y), torch.from_numpy(s))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += loss.item()
        model.eval()
        with torch.no_grad():
            r = np.array([float(((model(f) - y) * MAX_CFO).pow(2).mean()) / crb(sn) for sn, (f, y, _) in val.items()])
        score = r.mean()
        mark = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict(), "config": {"arch": args.arch, "hidden": list(args.hidden)}},
                       paths.model(f"cfo_v2_{args.name}.pth"))
            mark = " [BEST]"
        print(f"Epoch {ep:3d}/{args.epochs} | train {run / args.steps:7.3f} | val MSE/CRB mean {score:6.3f} | "
              + " ".join(f"{sn}:{v:.2f}" for sn, v in zip(TEST_SNRS, r)) + f" | {time.time() - t0:.0f}s{mark}",
              flush=True)


def load_v2(name):
    ck = torch.load(paths.model(f"cfo_v2_{name}.pth"), map_location="cpu", weights_only=False)
    m = CFOv2(ck["config"]["arch"], tuple(ck["config"]["hidden"]))
    m.load_state_dict(ck["state_dict"])
    return m.eval()


def load_current():
    ck = torch.load(CURRENT_PATH, map_location="cpu", weights_only=False)
    m = SNRAwareCFOEstimator(max_lag=ck["config"]["max_lag"], hidden=tuple(ck["config"]["hidden"]))
    m.load_state_dict(ck["state_dict"])
    return m.eval()


@torch.no_grad()
def big_test(name, seed=7, chunk=50000):
    """MSE/CRB and outlier rate (|error| > the CRC-search half-width 4 * 1.3 * sqrt(CRB)) on the full chain:
    1e6 frames per SNR at <= -3 dB, 1e5 above, for v2 <name>, the current NN, M&M and ML (same frames)."""
    torch.set_num_threads(16)
    import txrx_chain
    txrx_chain.FFT_WORKERS = 16                      # multi-threaded chain convolutions for the test frames
    v2, cur = load_v2(name), load_current()
    gen = torch.Generator().manual_seed(seed)
    out = {"name": name, "params": count_params(v2), "mlp_macs": macs(v2), "snr": TEST_SNRS, "est": {}}
    ests = ("v2", "current NN", "M&M", "ML")
    acc = {e: {s: [0.0, 0, 0] for s in TEST_SNRS} for e in ests}          # sum sq err, outliers, n
    for s in TEST_SNRS:
        n_tot = 1000000 if s <= -3 else 100000
        win = 4 * 1.3 * np.sqrt(crb(s))
        for _ in range(n_tot // chunk):
            z, y, snr = make_z(chunk, s, s, gen, s)
            f = features(z, snr)
            preds = {"v2": v2(f), "current NN": cur(f["lag"], snr.float())[:, 0], "M&M": f["mm"], "ML": f["ml"]}
            for e, p in preds.items():
                err = ((p.double() - y[:, 0]) * MAX_CFO).numpy()
                a = acc[e][s]
                a[0] += float((err ** 2).sum())
                a[1] += int((np.abs(err) > win).sum())
                a[2] += len(err)
        print(f"{s:4d} dB: " + "  ".join(f"{e} {acc[e][s][0] / acc[e][s][2] / crb(s):6.3f} "
                                          f"(out {acc[e][s][1] / acc[e][s][2]:.1e})" for e in ests), flush=True)
    for e in ests:
        out["est"][e] = {"mse_over_crb": [acc[e][s][0] / acc[e][s][2] / crb(s) for s in TEST_SNRS],
                         "outlier_rate": [acc[e][s][1] / acc[e][s][2] for s in TEST_SNRS],
                         "n": [acc[e][s][2] for s in TEST_SNRS]}
    json.dump(out, open(paths.log(f"cfo_v2_{name}_test.json"), "w"), indent=1)
    print("DONE", flush=True)


def plot_compare(name):
    """The chosen v2 against the current NN (and M&M for reference): MSE/CRB and outlier rate vs SNR."""
    import matplotlib.pyplot as plt
    d = json.load(open(paths.log(f"cfo_v2_{name}_test.json")))
    snr = np.array(d["snr"])
    rx = ((f"NN v2 ({d['params']} params)", "v2", "tab:blue", "-", "o"),
          ("Current SNR-aware NN", "current NN", "tab:orange", "-", "s"),
          ("M&M", "M&M", "tab:gray", "--", "^"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6))
    for label, key, c, ls, mk in rx:
        e = d["est"][key]
        a1.semilogy(snr, e["mse_over_crb"], ls, color=c, marker=mk, label=label)
        out, n = np.array(e["outlier_rate"]), np.array(e["n"])
        nz = out > 0                                            # 0 outliers cannot be drawn on a log axis
        a2.semilogy(snr[nz], out[nz], ls, color=c, marker=mk, label=label)
    a1.axhline(1.0, color="k", lw=0.8, ls=":", label="CRB")
    a1.set(xlabel="SNR (Es/N0) [dB]", ylabel="MSE / CRB", title="CFO MSE relative to the CRB")
    a2.set(xlabel="SNR (Es/N0) [dB]", ylabel="P(|error| > 4·1.3·√CRB)",
           title="Outlier rate (outside the CRC-search window)")
    for a in (a1, a2):
        a.grid(True, which="both", alpha=0.3)
        a.legend()
    fig.suptitle("New NN v2 vs current SNR-aware NN (128 known symbols, full Tx/Rx chain)")
    fig.text(0.5, 0.005, "1e6 frames per SNR at ≤ −3 dB, 1e5 above; points with 0 outliers are not drawn",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = paths.plot("cfo_v2_vs_current_nn_mse_over_crb.png")
    fig.savefig(out, dpi=150)
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--arch", choices=["light", "lag"], default="light")
    ap.add_argument("--hidden", type=int, nargs="+", default=[32, 16])
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-per-snr", type=int, default=20000)
    ap.add_argument("--producers", type=int, default=15)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--eval-only", action="store_true")
    ap.add_argument("--plot", action="store_true", help="only draw the comparison from the saved test table")
    a = ap.parse_args()
    if a.plot:
        plot_compare(a.name)
        raise SystemExit
    if not a.eval_only:
        train(a)
    big_test(a.name)
