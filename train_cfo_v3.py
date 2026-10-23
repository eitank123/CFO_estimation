"""
CFO NN v3: split pilots. The same 128 known symbols as before, but as two 64-symbol blocks at the two ends of the
packet (positions 0..63 and N-64..N-1) instead of one block at the start. The CRB falls with the spread of the
known positions, sum (n - n_mean)^2: 37x (512 symbols) and 169x (1024 symbols) below the contiguous 128 block,
i.e. a 6x / 13x smaller CFO standard deviation for the same overhead.

The price is ambiguity: the pilot likelihood |sum_n z[n] exp(-j 2 pi f n)|^2 has near-equal lobes every 1/D
cycles/symbol (D = N - 64, the distance between the block centres); the adjacent lobe is 97 % (512) / 99 % (1024)
of the main one. The estimator therefore works in three steps (split-pilot ML):
    1. coarse: the mean of the two per-block ML estimates (FFT-256 peak + 2 Newton steps on each 64-block)
    2. lobe:   the lobe nearest the coarse estimate, refined by 2 Newton steps on the full (gapped) likelihood;
               the lobe with the largest likelihood among the nearest +-2 is kept (the joint ML lobe)
    3. fine:   v3 = f_ML + (1/D) * MLP(inputs), last layer zero-initialised (an untrained v3 IS the split ML)
A wrong lobe is not something a regression can fix (any value between lobes decodes badly), so the loss clips the
error at half a lobe spacing: v3 learns the fine correction, and the CRC search covers the neighbouring lobes.

Inputs (9): SNR, (f_ML - f_coarse) * D, (f_block1 - f_ML) * D, (f_block2 - f_ML) * D, likelihood ratios of the
lobes j = -2, -1, +1, +2 to the chosen one, peak magnitude |A(f_ML)| / 128.

    python train_cfo_v3.py --packet 512 --epochs 60      # -> models/cfo_v3_L512.pth, logs/cfo_v3_L512_test.json
    python train_cfo_v3.py --packet 1024 --eval-only
"""
import argparse
import json
import time

import numpy as np
import torch
import torch.nn as nn

import os

import paths
from train_snr_nn import MAX_CFO, SNR_CENTER, SNR_SCALE, count_params, crb

BLOCK = 64
TEST_SNRS = [-5, -4, -3, -2, -1, 0, 2, 5, 10]
N_IN = 9
# "ends": blocks at 0..63 and N-64..N-1 (D = N - 64); "quarter": blocks centred at N/4 and 3N/4 (D = N/2)
LAYOUT = os.environ.get("CFO_PILOTS", "ends")


def positions(n_sym, layout=None):
    """Known-symbol positions (128,) of an n_sym packet: two BLOCK-symbol blocks (LAYOUT)."""
    if (layout or LAYOUT) == "ends":
        return np.concatenate([np.arange(BLOCK), np.arange(n_sym - BLOCK, n_sym)])
    a, b = n_sym // 4 - BLOCK // 2, 3 * n_sym // 4 - BLOCK // 2
    return np.concatenate([np.arange(a, a + BLOCK), np.arange(b, b + BLOCK)])


def spacing(n_sym, layout=None):
    """Lobe spacing of the split-pilot likelihood (cycles/symbol): 1 / distance between the block centres."""
    p = positions(n_sym, layout)
    return 1.0 / (p[BLOCK:].mean() - p[:BLOCK].mean())


def crb_split(snr_db, n_sym, layout=None):
    """Data-aided CFO CRB 1 / (8 pi^2 SNR sum (n - n_mean)^2) over the split positions (cycles^2/symbol^2)."""
    n = positions(n_sym, layout).astype(float)
    return 1.0 / (8 * np.pi ** 2 * 10 ** (np.asarray(snr_db, float) / 10) * np.sum((n - n.mean()) ** 2))


def likelihood(z, n, f):
    """A(f) = sum_k z[k] exp(-j 2 pi f n[k]) for z (B, K), centred positions n (K,), f (B,) or (B, H) -> same shape."""
    if f.dim() == 1:
        return (z * torch.exp(-2j * np.pi * f[:, None] * n)).sum(1)
    return torch.einsum("bk,bhk->bh", z, torch.exp(-2j * np.pi * f[:, :, None] * n))


def newton(z, n, f, iters=2, blocks=1):
    """Newton steps on the likelihood over the positions n; f in cycles/symbol. blocks=1: |A(f)|^2 (coherent over
    all of n); blocks=2: |A_1(f)|^2 + |A_2(f)|^2 (the two halves of n combined non-coherently)."""
    for _ in range(iters):
        g = h = 0.0
        for zb, nb in zip(z.chunk(blocks, 1), n.chunk(blocks)):
            e = torch.exp(-2j * np.pi * f[:, None] * nb)
            A = (zb * e).sum(1)
            A1 = (zb * e * (-2j * np.pi * nb)).sum(1)
            A2 = (zb * e * (-(2 * np.pi * nb) ** 2)).sum(1)
            g = g + 2 * (A1 * A.conj()).real
            h = h + 2 * ((A2 * A.conj()).real + A1.abs() ** 2)
        f = f - g / h
    return f


def coarse(z, K=256):
    """Coarse CFO from the two blocks combined non-coherently: peak of |FFT_K(block 1)|^2 + |FFT_K(block 2)|^2
    within +-MAX_CFO, then 2 Newton steps on |A_1|^2 + |A_2|^2 (block-local positions)."""
    P = (torch.fft.fft(z[:, :BLOCK], n=K).abs() ** 2 + torch.fft.fft(z[:, BLOCK:], n=K).abs() ** 2)
    freqs = torch.fft.fftfreq(K, dtype=torch.float64)
    P = P.masked_fill((freqs.abs() > MAX_CFO + 1.0 / K).unsqueeze(0), -1.0)
    nb = torch.arange(BLOCK, dtype=torch.float64) - (BLOCK - 1) / 2
    return newton(z, torch.cat([nb, nb]), freqs[P.argmax(1)], iters=2, blocks=2)


def split_ml(z, n_sym, layout=None):
    """Split-pilot ML estimate (B,) cycles/symbol and the v3 inputs, from z = r s* at positions(n_sym), (B, 128)."""
    z = torch.as_tensor(z, dtype=torch.complex128)
    n = torch.as_tensor(positions(n_sym, layout) - (n_sym - 1) / 2.0, dtype=torch.float64)   # centred positions
    d = spacing(n_sym, layout)
    f_coarse = coarse(z)
    nb = n[:BLOCK] - n[:BLOCK].mean()
    fb = [newton(z[:, sl], nb, f_coarse, iters=1) for sl in (slice(0, BLOCK), slice(BLOCK, None))]  # per block
    A1 = (z[:, :BLOCK] * torch.exp(-2j * np.pi * f_coarse[:, None] * n[:BLOCK])).sum(1)
    A2 = (z[:, BLOCK:] * torch.exp(-2j * np.pi * f_coarse[:, None] * n[BLOCK:])).sum(1)
    f0 = newton(z, n, f_coarse + torch.angle(A2 * A1.conj()) / (2 * np.pi) * d)          # nearest lobe
    js = torch.arange(-2, 3, dtype=torch.float64)
    cand = newton(z.repeat_interleave(5, 0), n, (f0[:, None] + js * d).reshape(-1), iters=1).reshape(-1, 5)
    lik = likelihood(z, n, cand).abs() ** 2
    f_ml = cand.gather(1, lik.argmax(1, keepdim=True))[:, 0]                               # joint ML lobe
    lj = likelihood(z, n, f_ml[:, None] + js * d).abs() ** 2
    ratios = lj[:, [0, 1, 3, 4]] / lj[:, 2:3]
    peak = lj[:, 2].sqrt() / z.shape[1]
    return f_ml, {"coarse": f_coarse, "b1": fb[0], "b2": fb[1], "ratios": ratios, "peak": peak}


def features(z, snr_db, n_sym):
    f_ml, aux = split_ml(z, n_sym)
    D = 1.0 / spacing(n_sym)
    s = (torch.as_tensor(snr_db, dtype=torch.float64) - SNR_CENTER) / SNR_SCALE
    x = torch.cat([torch.stack([s, (f_ml - aux["coarse"]) * D, ((aux["b1"] - f_ml) * D).clamp(-20, 20),
                                ((aux["b2"] - f_ml) * D).clamp(-20, 20)], 1), aux["ratios"], aux["peak"][:, None]], 1)
    return {"x": x.float(), "ml": f_ml}


class CFOv3(nn.Module):
    def __init__(self, n_sym, hidden=(32, 16)):
        super().__init__()
        self.n_sym = n_sym
        layers, d = [], N_IN
        for h in hidden:
            layers += [nn.Linear(d, h), nn.GELU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, f):
        """CFO in cycles/symbol (float64)."""
        return f["ml"] + spacing(self.n_sym) * self.net(f["x"])[:, 0].double()


def make_z(B, n_sym, lo, hi, rng, fixed=None):
    """Random n_sym-symbol QPSK packets through the full chain; z = r s* at the split positions (B, 128)."""
    from txrx_chain import qpsk, transmit
    snr = np.full(B, float(fixed)) if fixed is not None else rng.uniform(lo, hi, B)
    sym = qpsk(rng, (B, n_sym))
    f = rng.uniform(-MAX_CFO, MAX_CFO, B)
    r = transmit(sym, f, rng.uniform(0, 2 * np.pi, B), snr, rng)
    idx = positions(n_sym)
    return r[:, idx] * np.conj(sym[:, idx]), f, snr


def batch(B, n_sym, lo, hi, rng, fixed=None):
    z, f, snr = make_z(B, n_sym, lo, hi, rng, fixed)
    return features(z, snr, n_sym), torch.from_numpy(f), torch.from_numpy(snr)


def _producer(seed, q, B, n_sym, lo, hi):
    torch.set_num_threads(1)
    rng = np.random.default_rng(seed)
    while True:
        f, y, s = batch(B, n_sym, lo, hi, rng)
        q.put(({k: v.numpy() for k, v in f.items()}, y.numpy(), s.numpy()))


def loss_fn(pred, y, snr, n_sym):
    """Squared error / CRB, the error clipped at half a lobe spacing (no gradient for lobe errors)."""
    c = torch.as_tensor(crb_split(snr.numpy(), n_sym))
    e = (pred - y).clamp(-spacing(n_sym) / 2, spacing(n_sym) / 2)
    return (e ** 2 / c).mean()


def model_path(n_sym):
    return paths.model(f"cfo_v3_L{n_sym}.pth")


def train(args):
    torch.manual_seed(args.seed)
    torch.set_num_threads(1)
    model = CFOv3(args.packet, tuple(args.hidden))
    print(f"v3 L{args.packet}: hidden {args.hidden} params {count_params(model)}", flush=True)
    vrng = np.random.default_rng(args.seed + 1)
    val = {s: batch(args.val_per_snr, args.packet, s, s, vrng, s) for s in TEST_SNRS}
    import multiprocessing as mp
    q = mp.Queue(maxsize=64)
    for i in range(args.producers):
        mp.Process(target=_producer, daemon=True,
                   args=(args.seed + 1000 * (i + 1), q, args.batch, args.packet, -6.0, 11.0)).start()
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    best = float("inf")
    for ep in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            f, y, s = q.get()
            f = {k: torch.from_numpy(v) for k, v in f.items()}
            loss = loss_fn(model(f), torch.from_numpy(y), torch.from_numpy(s), args.packet)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += loss.item()
        model.eval()
        with torch.no_grad():
            r = np.array([float(loss_fn(model(f), y, s, args.packet)) for f, y, s in val.values()])
        mark = ""
        if r.mean() < best:
            best = r.mean()
            torch.save({"state_dict": model.state_dict(), "config": {"n_sym": args.packet, "hidden": list(args.hidden)}},
                       model_path(args.packet))
            mark = " [BEST]"
        print(f"Epoch {ep:3d}/{args.epochs} | train {run / args.steps:7.3f} | val (clipped MSE/CRB) "
              + " ".join(f"{sn}:{v:.2f}" for sn, v in zip(TEST_SNRS, r)) + f" | {time.time() - t0:.0f}s{mark}", flush=True)


def load_v3(n_sym):
    ck = torch.load(model_path(n_sym), map_location="cpu", weights_only=False)
    m = CFOv3(ck["config"]["n_sym"], tuple(ck["config"]["hidden"]))
    m.load_state_dict(ck["state_dict"])
    return m.eval()


@torch.no_grad()
def big_test(n_sym, n_low=300000, n_high=100000, chunk=20000, seed=7):
    """Per SNR: lobe-error rate (|e| > half a lobe spacing), fine RMSE / sqrt(CRB_split) over the frames on the right
    lobe, and the lobe-error distribution |j|, for v3 and the split ML (same frames)."""
    torch.set_num_threads(16)
    import txrx_chain
    txrx_chain.FFT_WORKERS = 16
    v3 = load_v3(n_sym)
    rng = np.random.default_rng(seed)
    d = spacing(n_sym)
    out = {"n_sym": n_sym, "params": count_params(v3), "snr": TEST_SNRS, "est": {"v3": {}, "split ML": {}}}
    for e in out["est"].values():
        e.update(lobe_err=[], fine_rmse_over_crb=[], lobe_hist=[], n=[])
    for s in TEST_SNRS:
        n_tot = n_low if s <= -3 else n_high
        acc = {k: [0, 0.0, 0, np.zeros(6)] for k in out["est"]}         # lobe errors, sum sq fine, n fine, |j| hist
        for _ in range(n_tot // chunk):
            z, f, snr = make_z(chunk, n_sym, s, s, rng, s)
            ft = features(z, snr, n_sym)
            for k, p in (("v3", v3(ft)), ("split ML", ft["ml"])):
                err = p.numpy() - f
                j = np.rint(err / d)
                ok = j == 0
                a = acc[k]
                a[0] += int((~ok).sum())
                a[1] += float((err[ok] ** 2).sum())
                a[2] += int(ok.sum())
                a[3] += np.bincount(np.minimum(np.abs(j).astype(int), 5), minlength=6)
        for k, a in acc.items():
            e = out["est"][k]
            e["lobe_err"].append(a[0] / n_tot)
            e["fine_rmse_over_crb"].append(float(np.sqrt(a[1] / max(a[2], 1) / crb_split(s, n_sym))))
            e["lobe_hist"].append(a[3].tolist())
            e["n"].append(n_tot)
        print(f"{s:4d} dB: " + "  ".join(f"{k}: lobe err {out['est'][k]['lobe_err'][-1]:.2e} fine rmse/sqrtCRB "
                                          f"{out['est'][k]['fine_rmse_over_crb'][-1]:.3f} |j| {acc[k][3].astype(int).tolist()}"
                                          for k in out["est"]), flush=True)
    json.dump(out, open(paths.log(f"cfo_v3_L{n_sym}_test.json"), "w"), indent=1)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", type=int, choices=[512, 1024], required=True)
    ap.add_argument("--hidden", type=int, nargs="+", default=[32, 16])
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-per-snr", type=int, default=20000)
    ap.add_argument("--producers", type=int, default=15)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--eval-only", action="store_true")
    a = ap.parse_args()
    if not a.eval_only:
        train(a)
    big_test(a.packet)
