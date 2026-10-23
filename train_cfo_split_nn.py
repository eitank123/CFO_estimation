"""
Pure-NN CFO estimator for split pilots (quarter layout: two 64-symbol blocks centred at N/4 and 3N/4), with no ML
front end: no FFT peak search, no Newton steps, no likelihood lobe search. Full Tx/Rx chain, AWGN, one model per
packet length (512, 1024).

    1. coarse: a learned linear filter bank (bias-free Linear 128 -> 2K on [Re, Im] of each 64-symbol block, i.e.
               K complex filters), the two blocks' energies added non-coherently and log-normalised, then
               MLP([log-energies, SNR]) -> f_c = 0.2 tanh(.). Filter bank initialised randomly or with DFT rows
               (K frequencies evenly over +-0.21 cycles/symbol).
    2. lobe:   analytic. Both blocks de-rotated by f_c, one coherent sum per block b1, b2;
               phi = angle(b2 conj(b1)) / 2 pi, f_lobe = f_c + phi / D (D = distance of the block centres)
    3. fine:   MLP 5 -> 32 -> 1 (GELU, last layer zero-initialised) on [SNR, frac(f_c D), cos 2 pi phi,
               sin 2 pi phi, log(1 + |b2 conj(b1)| / 64)];  f_hat = f_lobe + (1/D) MLP
Loss = ((f_c - f) D)^2 + min((f_hat - f)^2, (1/2D)^2) / CRB_split  (f_c is detached in the lobe/fine stages, so
the fine term trains only the fine MLP and the coarse term only the coarse branch).

    python train_cfo_split_nn.py --packet 512 --init dft       # -> models/cfo_split_nn_L512_dft.pth,
                                                               #    logs/cfo_split_nn_L512_dft_test.json
    python train_cfo_split_nn.py --packet 512 --init dft --eval-only
    python train_cfo_split_nn.py --plot                        # -> plots/mse/cfo_mse_vs_snr_split_pilots_nn.png
"""
import argparse
import json
import multiprocessing as mp
import os
import time

os.environ["CFO_PILOTS"] = "quarter"          # train_cfo_v3 reads the pilot layout at import (make_z, positions)

import numpy as np
import torch
import torch.nn as nn

import paths
from train_cfo_v3 import BLOCK, crb_split, likelihood, make_z, positions, spacing, split_ml
from train_snr_nn import MAX_CFO, SNR_CENTER, SNR_SCALE, count_params

LAYOUT = "quarter"
TEST_SNRS = [-5, -4, -3, -2, -1, 0, 2, 5, 10]
SUB = 256                    # frames per chain call (memory of the 8-SPS chain at 1024 symbols)


class SplitNN(nn.Module):
    """arch "mlp": coarse = MLP on the log filter energies; "conv": coarse = a small 1-D conv over the filter energies
    (translation-equivariant along frequency), soft-argmax over the filter frequencies plus a per-filter offset.
    lobe > 0: a learned lobe classifier over the 2 lobe + 1 candidates around the analytic lobe (instead of taking the
    analytic lobe as it is)."""

    def __init__(self, n_sym, init="dft", K=128, hidden=(256, 128), fine_hidden=32, arch="mlp", lobe=0, conv_ch=8,
                 lobe_hidden=(64, 64)):
        super().__init__()
        self.n_sym, self.K, self.arch, self.L = n_sym, K, arch, lobe
        self.D = 1.0 / spacing(n_sym, LAYOUT)
        self.register_buffer("n", torch.as_tensor(positions(n_sym, LAYOUT) - (n_sym - 1) / 2.0, dtype=torch.float64))
        fk = np.linspace(-MAX_CFO - 0.01, MAX_CFO + 0.01, K)
        self.register_buffer("fk", torch.as_tensor(fk, dtype=torch.float64), persistent=False)
        self.bank = nn.Linear(2 * BLOCK, 2 * K, bias=False)
        if init == "dft":     # rows: Re / Im of sum_m z[m] exp(-j 2 pi f_k m), z = a + jb -> [cos, sin] / [-sin, cos]
            th = 2 * np.pi * np.outer(fk, np.arange(BLOCK) - (BLOCK - 1) / 2)
            c, s = np.cos(th), np.sin(th)
            w = np.concatenate([np.concatenate([c, s], 1), np.concatenate([-s, c], 1)]) / np.sqrt(BLOCK)
            with torch.no_grad():
                self.bank.weight.copy_(torch.as_tensor(w, dtype=torch.float32))
        if arch == "mlp":
            layers, d = [], K + 1
            for h in hidden:
                layers += [nn.Linear(d, h), nn.GELU()]
                d = h
            self.coarse = nn.Sequential(*layers, nn.Linear(d, 1))
        else:                 # channels: log energy, SNR -> conv_ch -> conv_ch -> (logit, offset)
            self.coarse = nn.Sequential(nn.Conv1d(2, conv_ch, 7, padding=3), nn.GELU(),
                                        nn.Conv1d(conv_ch, conv_ch, 7, padding=3), nn.GELU(),
                                        nn.Conv1d(conv_ch, 2, 7, padding=3))
        if lobe:              # inputs per candidate: coherent and per-block log likelihood, distance to f_c (+ SNR)
            layers, d = [], 3 * (2 * lobe + 1) + 1
            for h in lobe_hidden:
                layers += [nn.Linear(d, h), nn.GELU()]
                d = h
            self.lobe = nn.Sequential(*layers, nn.Linear(d, 2 * lobe + 1))
        self.fine = nn.Sequential(nn.Linear(5, fine_hidden), nn.GELU(), nn.Linear(fine_hidden, 1))
        nn.init.zeros_(self.fine[-1].weight)
        nn.init.zeros_(self.fine[-1].bias)

    def forward(self, z, snr_db):
        """z (B, 128) complex (r s* at the split positions), SNR (B,) dB -> (f_hat, f_c, aux), cycles/symbol float64."""
        z = torch.as_tensor(z).to(torch.complex128)
        s = ((torch.as_tensor(snr_db, dtype=torch.float64) - SNR_CENTER) / SNR_SCALE).float()[:, None]
        zf = z.to(torch.complex64)
        E = 0.0
        for blk in (zf[:, :BLOCK], zf[:, BLOCK:]):
            y = self.bank(torch.cat([blk.real, blk.imag], 1))
            E = E + y[:, :self.K] ** 2 + y[:, self.K:] ** 2                   # non-coherent over the two blocks
        E = torch.log(E + 1e-6) - torch.log(E.mean(1, keepdim=True) + 1e-6)    # log-normalised
        aux = {}
        if self.arch == "mlp":
            f_c = MAX_CFO * torch.tanh(self.coarse(torch.cat([E, s], 1))[:, 0]).double()
        else:
            o = self.coarse(torch.stack([E, s.expand(-1, self.K)], 1)).double()
            aux["bin_logits"] = o[:, 0]
            df = float(self.fk[1] - self.fk[0])
            f_c = (torch.softmax(o[:, 0], 1) * (self.fk + df * torch.tanh(o[:, 1]))).sum(1)
        fc = f_c.detach()
        e = torch.exp(-2j * np.pi * fc[:, None] * self.n)
        b1, b2 = (z[:, :BLOCK] * e[:, :BLOCK]).sum(1), (z[:, BLOCK:] * e[:, BLOCK:]).sum(1)
        p = b2 * b1.conj()
        phi = torch.angle(p) / (2 * np.pi)
        f_lobe = fc + phi / self.D
        if self.L:
            js = torch.arange(-self.L, self.L + 1, dtype=torch.float64)
            cand = f_lobe[:, None] + js / self.D
            B1 = likelihood(z[:, :BLOCK], self.n[:BLOCK], cand)
            B2 = likelihood(z[:, BLOCK:], self.n[BLOCK:], cand)
            la = torch.log((B1 + B2).abs() ** 2 + 1e-9)
            lb = torch.log(B1.abs() ** 2 + B2.abs() ** 2 + 1e-9)
            x = torch.cat([la - la.max(1, keepdim=True)[0], lb - lb.max(1, keepdim=True)[0],
                           ((cand - fc[:, None]) * self.D).clamp(-2 * self.L, 2 * self.L), s.double()], 1).float()
            logits = self.lobe(x).double()
            aux["lobe_logits"], aux["f_lobe0"] = logits, f_lobe
            f_lobe = f_lobe + (logits.argmax(1) - self.L).double() / self.D
        x = torch.stack([s[:, 0].double(), fc * self.D - torch.round(fc * self.D), torch.cos(2 * np.pi * phi),
                         torch.sin(2 * np.pi * phi), torch.log1p(p.abs() / BLOCK)], 1).float()
        return f_lobe + self.fine(x)[:, 0].double() / self.D, f_c, aux


def macs(model):
    """Real multiply-accumulates per estimate: filter bank + energies + coarse stage + de-rotation/sums + lobe
    classifier + fine MLP."""
    lin = lambda seq: sum(m.in_features * m.out_features for m in seq if isinstance(m, nn.Linear))
    if model.arch == "mlp":
        coarse = lin(model.coarse)
    else:
        coarse = sum(m.in_channels * m.out_channels * m.kernel_size[0] * model.K for m in model.coarse
                     if isinstance(m, nn.Conv1d)) + 3 * model.K          # + softmax and weighted sum
    bank = 2 * (2 * BLOCK) * (2 * model.K)
    energy = 2 * 2 * model.K
    lobe = 2 * BLOCK * 4 + 2 * BLOCK * 2 + 4          # 128 complex rotations (4 real mults) + 2 sums + b2 b1*
    cls = (2 * model.L + 1) * (2 * BLOCK * 4 + 8) + lin(model.lobe) if model.L else 0   # candidate likelihoods + MLP
    fine = lin(model.fine)
    return {"bank": bank, "energy": energy, "coarse": coarse, "lobe": lobe, "lobe_classifier": cls, "fine_mlp": fine,
            "total": bank + energy + coarse + lobe + cls + fine}


def gen(B, n_sym, lo, hi, rng, fixed=None):
    zs, fs, ss = [], [], []
    for i in range(0, B, SUB):
        z, f, s = make_z(min(SUB, B - i), n_sym, lo, hi, rng, fixed)
        zs.append(z.astype(np.complex64)); fs.append(f); ss.append(s)
    return np.concatenate(zs), np.concatenate(fs), np.concatenate(ss)


def _producer(seed, q, B, n_sym):
    torch.set_num_threads(1)
    rng = np.random.default_rng(seed)
    while True:
        q.put(gen(B, n_sym, -6.0, 11.0, rng))


def loss_fn(model, z, f, snr):
    """Total loss, coarse term, fine term (clipped error^2 / CRB: the selection metric), wrong-lobe rate.
    conv coarse: + cross-entropy of the filter nearest the true CFO; lobe classifier: + cross-entropy of the true lobe
    (frames whose true lobe is outside the candidates are left out of that term)."""
    f_hat, f_c, aux = model(torch.from_numpy(z), torch.from_numpy(snr))
    f = torch.from_numpy(f)
    c = torch.as_tensor(crb_split(snr, model.n_sym, LAYOUT))
    lc = ((f_c - f) * model.D) ** 2
    lf = torch.minimum((f_hat - f) ** 2, torch.full_like(f, (0.5 / model.D) ** 2)) / c
    loss = (lc + lf).mean()
    if "bin_logits" in aux:
        df = float(model.fk[1] - model.fk[0])
        t = torch.round((f - model.fk[0]) / df).long().clamp(0, model.K - 1)
        loss = loss + nn.functional.cross_entropy(aux["bin_logits"], t)
    if "lobe_logits" in aux:
        t = torch.round((f - aux["f_lobe0"]) * model.D).long() + model.L
        ok = (t >= 0) & (t <= 2 * model.L)
        if ok.any():
            loss = loss + nn.functional.cross_entropy(aux["lobe_logits"][ok], t[ok]) * ok.double().mean()
    return loss, lc.mean(), lf.mean(), (torch.round((f_hat - f) * model.D) != 0).double().mean()


def name(n_sym, tag):
    return f"cfo_split_nn_L{n_sym}_{tag}"


def build(c):
    return SplitNN(c["n_sym"], c["init"], c["K"], tuple(c["hidden"]), arch=c.get("arch", "mlp"), lobe=c.get("lobe", 0),
                   conv_ch=c.get("conv_ch", 8))


def train(args):
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    tag = args.tag or args.init
    cfg = {"n_sym": args.packet, "init": args.init, "K": args.K, "hidden": list(args.hidden), "arch": args.arch,
           "lobe": args.lobe, "conv_ch": args.conv_ch}
    model = build(cfg)
    print(f"{name(args.packet, tag)}: {cfg} params {count_params(model)} MACs {macs(model)}", flush=True)
    vrng = np.random.default_rng(args.seed + 1)
    val = {s: gen(args.val_per_snr, args.packet, s, s, vrng, s) for s in TEST_SNRS}
    q = mp.Queue(maxsize=48)
    procs = [mp.Process(target=_producer, daemon=True, args=(args.seed + 1000 * (i + 1), q, args.batch, args.packet))
             for i in range(args.producers)]
    for p in procs:
        p.start()
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    best = float("inf")
    for ep in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), np.zeros(2)
        for _ in range(args.steps):
            loss, lc, lf, _ = loss_fn(model, *q.get())
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += [lc.item(), lf.item()]
        model.eval()
        with torch.no_grad():
            r = [loss_fn(model, *v) for v in val.values()]
        tot = float(np.mean([float(x[2]) for x in r]))         # clipped fine MSE / CRB, mean over the SNRs
        mark = ""
        if tot < best:
            best = tot
            torch.save({"state_dict": model.state_dict(), "config": cfg}, paths.model(name(args.packet, tag) + ".pth"))
            mark = " [BEST]"
        print(f"Epoch {ep:3d}/{args.epochs} | train coarse {run[0] / args.steps:.4f} fine {run[1] / args.steps:.3f} | "
              f"val wrong lobe " + " ".join(f"{sn}:{float(x[3]):.4f}" for sn, x in zip(TEST_SNRS, r))
              + f" | fine " + " ".join(f"{float(x[2]):.2f}" for x in r) + f" | {time.time() - t0:.0f}s{mark}",
              flush=True)
    for p in procs:
        p.terminate()


def load(n_sym, tag):
    ck = torch.load(paths.model(name(n_sym, tag) + ".pth"), map_location="cpu", weights_only=False)
    m = build(ck["config"])
    m.load_state_dict(ck["state_dict"])
    return m.eval()


def load_best(n_sym):
    """The chosen model models/cfo_split_nn_L<n_sym>.pth (a copy of the best tagged checkpoint)."""
    ck = torch.load(paths.model(f"cfo_split_nn_L{n_sym}.pth"), map_location="cpu", weights_only=False)
    m = build(ck["config"])
    m.load_state_dict(ck["state_dict"])
    return m.eval()


CHUNK, BATCH = 10000, 500


def _eval(task):
    n_sym, tag, snr, seed = task
    torch.set_num_threads(1)
    model = load(n_sym, tag)
    rng = np.random.default_rng(seed)
    d = spacing(n_sym, LAYOUT)
    acc = {k: [0.0, 0, 0.0, 0] for k in ("nn", "ml", "coarse")}       # sum sq, wrong lobes, sum sq right lobe, n right
    with torch.no_grad():
        for _ in range(CHUNK // BATCH):
            z, f, s = gen(BATCH, n_sym, snr, snr, rng, snr)
            f_hat, f_c, _ = model(torch.from_numpy(z), torch.from_numpy(s))
            ml = split_ml(z.astype(np.complex128), n_sym, LAYOUT)[0]
            for k, p in (("nn", f_hat), ("ml", ml), ("coarse", f_c)):
                err = p.numpy() - f
                ok = np.rint(err / d) == 0 if k != "coarse" else np.abs(err) < d / 2
                a = acc[k]
                a[0] += float((err ** 2).sum()); a[1] += int((~ok).sum())
                a[2] += float((err[ok] ** 2).sum()); a[3] += int(ok.sum())
    return snr, acc


def big_test(n_sym, tag, workers):
    tasks = [(n_sym, tag, s, 7000 * n_sym + 31 * i + 1000 * (s + 10)) for s in TEST_SNRS
             for i in range((1000000 if s <= -3 else 100000) // CHUNK)]
    tot = {}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for k, (s, acc) in enumerate(pool.imap_unordered(_eval, tasks), 1):
            t = tot.setdefault(s, {kk: [0.0, 0, 0.0, 0] for kk in acc})
            for kk, a in acc.items():
                t[kk] = [x + y for x, y in zip(t[kk], a)]
            with open(paths.log(name(n_sym, tag) + "_test.progress"), "a") as fh:
                fh.write(f"{k} {len(tasks)} {time.time() - t0:.0f}\n")
    model = load(n_sym, tag)
    out = {"n_sym": n_sym, "tag": tag, "config": torch.load(paths.model(name(n_sym, tag) + ".pth"), map_location="cpu",
                                                         weights_only=False)["config"], "layout": LAYOUT, "params": count_params(model), "macs": macs(model),
           "snr": TEST_SNRS, "crb": [float(crb_split(s, n_sym, LAYOUT)) for s in TEST_SNRS], "est": {}}
    for kk in ("nn", "ml", "coarse"):
        rows = [tot[s][kk] for s in TEST_SNRS]
        n = [r[1] + r[3] for r in rows]
        out["est"][kk] = {"mse": [r[0] / m for r, m in zip(rows, n)], "wrong_lobe_rate": [r[1] / m for r, m in zip(rows, n)],
                          "fine_mse": [r[2] / max(r[3], 1) for r in rows], "n": n}
    for i, s in enumerate(TEST_SNRS):
        print(f"{s:4d} dB: " + "  ".join(
            f"{kk}: MSE {out['est'][kk]['mse'][i]:.2e} wrong {out['est'][kk]['wrong_lobe_rate'][i]:.2e} "
            f"fine/CRB {out['est'][kk]['fine_mse'][i] / out['crb'][i]:.3f}" for kk in ("nn", "ml", "coarse")), flush=True)
    json.dump(out, open(paths.log(name(n_sym, tag) + "_test.json"), "w"), indent=1)
    print("EVAL DONE", flush=True)


def plot():
    """CFO MSE vs SNR: M&M, NN v2 (contiguous), split ML (cfo_split_mse.json) and the split NN (both packets)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from train_snr_nn import crb
    sp = json.load(open(paths.log("cfo_split_mse.json")))
    v2 = json.load(open(paths.log("cfo_v2_light32_test.json")))
    snr = np.array(sp["snr"], float)
    c128 = np.array([crb(s) for s in v2["snr"]])
    fig, ax = plt.subplots(figsize=(11, 6.8))
    ax.semilogy(v2["snr"], np.array(v2["est"]["M&M"]["mse_over_crb"]) * c128, "-.", color="#ff7f0e", marker="d",
                lw=2.2, label="M&M (contiguous 128 pilots)")
    ax.semilogy(v2["snr"], np.array(v2["est"]["v2"]["mse_over_crb"]) * c128, "-", color="#2ca02c", marker="^",
                lw=2.2, label="NN v2 (contiguous 128 pilots)")
    ax.semilogy(v2["snr"], c128, ":", color="0.4", lw=1.6, label="CRB, contiguous 128 pilots")
    for n, c, cn, mk in (("512", "#d62728", "#1f77b4", "*"), ("1024", "#8c1a1a", "#17becf", "P")):
        p = sp["packets"][n]
        ax.semilogy(snr, p["mse"], "-", color=c, marker=mk, lw=2.2, label=f"Split pilots ML, {n} symbols")
        f = paths.log(f"cfo_split_nn_L{n}.json")
        if os.path.exists(f):
            nn_ = json.load(open(f))["est"]["nn"]
            ax.semilogy(nn_["snr"] if "snr" in nn_ else snr, nn_["mse"], "--", color=cn, marker=mk, lw=2.2,
                        label=f"Split pilots NN, {n} symbols")
        ax.semilogy(snr, p["crb"], ":", color=c, lw=1.4, label=f"CRB, split pilots, {n} symbols")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO MSE [(cycles/symbol)²]")
    fig.suptitle("CFO MSE vs SNR", fontsize=15, fontweight="bold")
    ax.set_title("128 known symbols in every estimator; split pilots: two 64-symbol blocks centred at N/4 and 3N/4 "
                 "(all frames)", fontsize=10, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=3, frameon=False)
    fig.tight_layout()
    out = paths.plot("cfo_mse_vs_snr_split_pilots_nn.png")
    fig.savefig(out, dpi=300)
    print("saved", out)


def plot_vs_mm(n_sym=1024):
    """CFO MSE vs SNR: the split-pilot NN (models/cfo_split_nn_L<n_sym>.pth, all frames) against
    M&M on 128 contiguous pilots (logs/cfo_v2_light32_test.json), with both CRBs."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from train_snr_nn import crb
    d = json.load(open(paths.log(f"cfo_split_nn_L{n_sym}.json")))
    v2 = json.load(open(paths.log("cfo_v2_light32_test.json")))
    snr, nn_ = np.array(d["snr"], float), d["est"]["nn"]
    c128 = np.array([crb(s) for s in v2["snr"]])
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.semilogy(v2["snr"], np.array(v2["est"]["M&M"]["mse_over_crb"]) * c128, "-.", color="#ff7f0e", marker="d",
                lw=2.2, label="M&M (128 contiguous pilots)")
    ax.semilogy(v2["snr"], c128, ":", color="#ff7f0e", lw=1.5, label="CRB, 128 contiguous pilots")
    ax.semilogy(snr, nn_["mse"], "-", color="#17becf", marker="h", lw=2.2, label="Split pilots NN")
    ax.semilogy(snr, d["crb"], ":", color="#17becf", lw=1.5, label="CRB, split pilots")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO MSE [(cycles/symbol)²]")
    fig.suptitle("CFO MSE vs SNR", fontsize=15, fontweight="bold")
    ax.set_title(f"{n_sym}-symbol packet; 128 known symbols in both; split pilots: two 64-symbol blocks centred at N/4 "
                 "and 3N/4", fontsize=10.5, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    fig.tight_layout()
    out = paths.plot(f"cfo_mse_vs_snr_split_nn_vs_mm_L{n_sym}.png")
    fig.savefig(out, dpi=300)
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", type=int, choices=[512, 1024])
    ap.add_argument("--init", choices=["dft", "rand"], default="dft")
    ap.add_argument("--tag", default="", help="model name suffix (default: the init)")
    ap.add_argument("--arch", choices=["mlp", "conv"], default="mlp")
    ap.add_argument("--lobe", type=int, default=0, help="learned lobe classifier over 2 lobe + 1 candidates (0: off)")
    ap.add_argument("--conv-ch", type=int, default=8)
    ap.add_argument("--threads", type=int, default=1, help="trainer threads (producers + threads <= 16)")
    ap.add_argument("--K", type=int, default=128)
    ap.add_argument("--hidden", type=int, nargs="+", default=[256, 128])
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-per-snr", type=int, default=10000)
    ap.add_argument("--producers", type=int, default=15)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--eval-only", action="store_true")
    ap.add_argument("--plot", action="store_true")
    a = ap.parse_args()
    if a.plot:
        plot()
    else:
        if not a.eval_only:
            train(a)
        big_test(a.packet, a.tag or a.init, a.workers)
