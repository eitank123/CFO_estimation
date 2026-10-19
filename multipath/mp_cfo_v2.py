"""
Channel-aware CFO estimation on the multipath channel (3-tap Rayleigh, 0/-3/-6 dB, block fading),
known sequence of L = 128 or 512 symbols. Companion of multipath_cfo.py (same channel generator).

The single-path estimators (M&M, ML, FFT-NN) all work on z[n] = r[n] s*[n], which assumes one path:
the delayed taps leave interference that does not fall with SNR, and a fade of the first tap removes
the tone. Here every tap gets its own correlation

    z_k[n] = r[n] s*[n-k],   k = 0 .. T-1  (T = 3),   Z_k(f) = FFT of z_k

    MP-ML  (classical, channel-aware)  maximise P(f) = sum_k |Z_k(f)|^2  (FFT K = 2L + 2 Newton steps)
           For random (white) symbols S^H S ~ L*I, so P(f)/L is the least-squares-taps ML cost
           Z^H (S^H S)^-1 Z: the joint ML of CFO and taps, without an equalizer.
    MP-NN  (channel-aware NN)  residual MLP on
           [64 lag correlations x 4 features of every z_k (T*256), SNR, 17 peak features of P(f)]
           output = peak frequency of P(f) + bin * MLP(...), last layer zero-initialised.

Training: on-the-fly multipath sequences, CFO ~ U[-0.2, 0.2], Es/N0 ~ U[-6, 11] dB,
loss log(1 + error^2 / CRB(Es/N0, L)) (log-compressed against deep-fade outliers).

Usage (project folder):
    python multipath/mp_cfo_v2.py --train --length 128      # one job per length
    python multipath/mp_cfo_v2.py --train --length 512
    python multipath/mp_cfo_v2.py --eval                    # both lengths, all estimators
Outputs: multipath/results_multipath/ (mp_nn_v2_seq<L>.pth, run_v2_L<L>.log, run_v2_eval.log,
cfo_v2_{rmse,median,outage}_multipath.png).
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

from multipath_cfo import AWGN_MODELS, CHANNELS, EVAL_SNRS, LENGTHS, OUTAGE, make_batch
from train_fft_nn import ml_estimate
from train_fft_nn_long import crb, features, load_fft_nn, mm_cfo
from train_snr_nn import MAX_CFO, SNR_CENTER, SNR_SCALE, lag_features

OUT = os.path.join(HERE, "results_multipath")
N_TAPS = len(CHANNELS["multipath"]["taps_db"])
N_AUX = 2 + 5 * N_TAPS


# =====================================================================
# Channel-aware features and the classical MP-ML estimator
# =====================================================================

def tap_correlations(r, s, T=N_TAPS):
    """z (B, T, L): z_k[n] = r[n] s*[n-k] for n >= k (zero for n < k)."""
    B, L = r.shape
    z = torch.zeros(B, T, L, dtype=torch.complex128)
    for k in range(T):
        z[:, k, k:] = r[:, k:] * s[:, :L - k].conj()
    return z


def mp_peak(z, K):
    """Peak of P(f) = sum_k |Z_k(f)|^2 over |f| <= MAX_CFO: bin index, frequency, Z (B, T, K), P (B, K)."""
    Z = torch.fft.fft(z, n=K, dim=2)
    P = (Z.abs() ** 2).sum(1)
    fr = torch.fft.fftfreq(K, dtype=torch.float64)
    idx = P.masked_fill((fr.abs() > MAX_CFO + 1.0 / K).unsqueeze(0), -1.0).argmax(1)
    return idx, fr[idx], Z, P


def mp_newton(z, f, iters=2):
    """Newton steps on P(f) = sum_k |A_k(f)|^2 (gradient and Hessian add over the taps)."""
    n = torch.arange(z.shape[2], dtype=torch.float64)
    for _ in range(iters):
        e = z * torch.exp(-2j * np.pi * f[:, None, None] * n)
        A, A1, A2 = e.sum(2), (e * (-2j * np.pi * n)).sum(2), (e * (-(2 * np.pi * n) ** 2)).sum(2)
        g = (2 * (A1 * A.conj()).real).sum(1)
        h = (2 * ((A2 * A.conj()).real + A1.abs() ** 2)).sum(1)
        f = f - g / h
    return f


def mp_ml(r, s):
    z = tap_correlations(r, s)
    _, fc, _, _ = mp_peak(z, 2 * r.shape[1])
    return (mp_newton(z, fc) / MAX_CFO).float().unsqueeze(1)


def mp_features(r, s):
    """NN inputs: lag features of every z_k (B, T*64*4), peak features of P(f) (B, N_AUX), coarse freq (B,)."""
    z = tap_correlations(r, s)
    B, T, L = z.shape
    K = 2 * L
    idx, fc, Z, P = mp_peak(z, K)
    ii = torch.stack([(idx - 1) % K, idx, (idx + 1) % K], 1)                       # (B, 3)
    Zn = torch.gather(Z, 2, ii.unsqueeze(1).expand(B, T, 3))                       # (B, T, 3)
    peak = P.gather(1, idx[:, None]).clamp_min(1e-12)                              # (B, 1)
    pk = Zn[:, :, 1]
    ratios = Zn[:, :, [0, 2]] * pk.conj().unsqueeze(2) / peak.unsqueeze(2)         # (B, T, 2) complex
    aux = torch.cat([(fc / MAX_CFO).unsqueeze(1), torch.sqrt(peak) / L,
                     (pk.abs() ** 2 / peak),                                        # tap energy shares
                     ratios.real.flatten(1), ratios.imag.flatten(1)], 1).float()
    lags = torch.cat([lag_features(z[:, k])[0].flatten(1) for k in range(T)], 1)  # 64 lags x 4 per tap
    return lags, aux, fc


class MPNN(nn.Module):
    def __init__(self, L, hidden=(256, 128, 64)):
        super().__init__()
        d = N_TAPS * 64 * 4 + 1 + N_AUX
        layers = []
        for h in hidden:
            layers += [nn.Linear(d, h), nn.GELU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)
        self.bin = 1.0 / (2 * L * MAX_CFO)

    def forward(self, lags, snr_db, aux):
        s = (snr_db.view(-1, 1) - SNR_CENTER) / SNR_SCALE
        return aux[:, :1] + self.bin * self.net(torch.cat([lags, s, aux], 1))


# =====================================================================
# Train / evaluate
# =====================================================================

def train(args, log):
    L = args.length
    torch.manual_seed(args.seed + L)
    model = MPNN(L)
    vgen = torch.Generator().manual_seed(args.seed + 1)
    val = []
    for s in (-5, 0, 5, 10):
        r, sym, y, snr = make_batch(args.val_per_snr, L, s, s, vgen, "multipath", fixed_snr=s, return_rs=True)
        lg, aux, _ = mp_features(r, sym)
        val.append((lg, aux, y.float(), snr.float()))
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-2)
    gen = torch.Generator().manual_seed(args.seed + 10 * L)
    best = float("inf")
    path = os.path.join(OUT, f"mp_nn_v2_seq{L}.pth")
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run = time.time(), 0.0
        for _ in range(args.steps):
            r, sym, y, snr = make_batch(args.batch, L, args.train_snr[0], args.train_snr[1], gen, "multipath",
                                        return_rs=True)
            lg, aux, _ = mp_features(r, sym)
            pred = model(lg, snr.float(), aux)
            c = torch.as_tensor(crb(snr.numpy(), L), dtype=torch.float32)
            loss = torch.log1p((((pred - y.float()).squeeze(1) * MAX_CFO) ** 2 / c)).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run += loss.item()
        model.eval()
        with torch.no_grad():
            med = [float(((model(lg, s, a) - y) * MAX_CFO).abs().median()) for lg, a, y, s in val]
        score = float(np.mean(np.log(med)))
        mark = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict(), "length": L}, path)
            mark = " [BEST]"
        log(f"Epoch {epoch:3d}/{args.epochs} | L={L} | train loss {run / args.steps:.3f} | val median |err| "
            f"@-5/0/5/10 dB " + " ".join(f"{v:.2e}" for v in med) + f" | {time.time() - t0:.0f}s{mark}")
    log("TRAIN DONE")


@torch.no_grad()
def evaluate(args, log):
    names = ["M&M", "ML", "FFT-NN (channel-trained)", "MP-ML (channel-aware)", "MP-NN (channel-aware)"]
    res = {}
    gen = torch.Generator().manual_seed(args.seed + 2)
    for L in LENGTHS:
        fft_nn, k = load_fft_nn(os.path.join(OUT, f"fft_nn_multipath_seq{L}.pth"))
        mp = MPNN(L)
        mp.load_state_dict(torch.load(os.path.join(OUT, f"mp_nn_v2_seq{L}.pth"), map_location="cpu")["state_dict"])
        mp.eval()
        for nm in names:
            res[(nm, L)] = {"rmse": [], "median": [], "outage": []}
        for s in EVAL_SNRS:
            errs = {nm: [] for nm in names}
            for start in range(0, args.test_per_snr, 20000):          # chunks keep the memory bounded
                nb = min(20000, args.test_per_snr - start)
                r, sym, y, snr = make_batch(nb, L, s, s, gen, "multipath", fixed_snr=s, return_rs=True)
                z0 = r * sym.conj()
                f, a, fc = features(z0, k)
                lg, aux, _ = mp_features(r, sym)
                est = {"M&M": mm_cfo(z0).float(), "ML": ml_estimate(z0, fc),
                       "FFT-NN (channel-trained)": fft_nn(f, snr.float(), a),
                       "MP-ML (channel-aware)": mp_ml(r, sym), "MP-NN (channel-aware)": mp(lg, snr.float(), aux)}
                for nm, e in est.items():
                    errs[nm].append(((e - y.float()) * MAX_CFO).squeeze(1).double().numpy())
            for nm in names:
                err = np.concatenate(errs[nm])
                res[(nm, L)]["rmse"].append(float(np.sqrt(np.mean(err ** 2))))
                res[(nm, L)]["median"].append(float(np.median(np.abs(err))))
                res[(nm, L)]["outage"].append(float(np.mean(np.abs(err) > OUTAGE)))
        log(f"evaluated L={L}")
    for L in LENGTHS:
        log(f"\nL = {L}: RMSE | median |error| | P(|error| > {OUTAGE:g})")
        log(f"{'Es/N0':>5} | " + " | ".join(f"{nm:>34}" for nm in names))
        for i, s in enumerate(EVAL_SNRS):
            log(f"{s:5d} | " + " | ".join(
                f"{res[(nm, L)]['rmse'][i]:.2e} | {res[(nm, L)]['median'][i]:.2e} | {res[(nm, L)]['outage'][i]:5.3f}".rjust(34)
                for nm in names))
    np.save(os.path.join(OUT, "cfo_v2_results.npy"), {"res": res, "snrs": EVAL_SNRS}, allow_pickle=True)
    log("\nComplexity per estimate, real MACs (1 complex MAC = 4), FFT K = 2L, 2 Newton steps:")
    for L in LENGTHS:
        K = 2 * L
        fft = (K // 2) * int(np.log2(K))
        mlp = sum(m.in_features * m.out_features for m in MPNN(L).modules() if isinstance(m, nn.Linear))
        ml = 4 * (L + fft + 6 * L)
        mpml = 4 * (N_TAPS * L + N_TAPS * fft + N_TAPS * 6 * L)
        mpnn = 4 * (N_TAPS * L + N_TAPS * fft + 2 * N_TAPS * fft) + mlp      # per-tap peak FFT + lag-correlation FFT/IFFT
        log(f"  L = {L}: ML {ml:,} | MP-ML {mpml:,} ({mpml / ml:.1f}x) | MP-NN {mpnn:,} ({mpnn / ml:.1f}x, "
            f"{sum(p.numel() for p in MPNN(L).parameters()):,} parameters)")

    style = {"M&M": ("#ff7f0e", "d", "--"), "ML": ("#2ca02c", "o", "--"),
             "FFT-NN (channel-trained)": ("#9467bd", "s", "--"),
             "MP-ML (channel-aware)": ("#1f77b4", "o", "-"), "MP-NN (channel-aware)": ("#d62728", "^", "-")}
    for metric, ylabel in (("rmse", "CFO RMSE (cycles/symbol)"), ("median", "Median |CFO error| (cycles/symbol)"),
                           ("outage", f"P(|CFO error| > {OUTAGE:g})")):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
        for ax, L in zip(axes, LENGTHS):
            for nm, (c, m, ls) in style.items():
                ax.semilogy(EVAL_SNRS, res[(nm, L)][metric], ls, color=c, marker=m, markersize=4, label=nm)
            if metric != "outage":
                ax.semilogy(EVAL_SNRS, np.sqrt(crb(EVAL_SNRS, L)), "k:", linewidth=1, label="sqrt(CRB), AWGN")
            ax.set_title(f"{L}-symbol sequence")
            ax.set_xlabel("Es/N0 [dB] (average)")
            ax.grid(True, which="both", linestyle=":", alpha=0.6)
        axes[0].set_ylabel(ylabel)
        axes[0].legend(fontsize=8)
        fig.suptitle("CFO estimation on the 3-tap Rayleigh channel: single-path (dashed) vs. channel-aware (solid)")
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, f"cfo_v2_{metric}_multipath.png"), dpi=300, bbox_inches="tight")
        plt.close(fig)
    log("EVAL DONE")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--length", type=int, default=128, choices=list(LENGTHS))
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--steps", type=int, default=250)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=4000)
    ap.add_argument("--test-per-snr", type=int, default=200000)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    os.makedirs(OUT, exist_ok=True)
    name = f"run_v2_L{args.length}.log" if args.train else "run_v2_eval.log"
    log_f = open(os.path.join(OUT, name), "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    if args.train:
        train(args, log)
    if args.eval:
        evaluate(args, log)
