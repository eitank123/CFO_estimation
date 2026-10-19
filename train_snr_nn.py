"""
Single NN CFO estimator (no fusion) that also receives the SNR as an input.

Goal: replace Phase-1 expert + M&M + fusion net with ONE network that
reaches the CRB at every SNR in [-5, 10] dB.

Input : lag-correlation features (max_lag, 4) [same as the Phase-1 expert]
        + SNR in dB (scaled)
Loss  : squared CFO error / CRB(SNR) -> every SNR point is pushed toward 1
Init  : Phase-1 expert weights (best_cfo_model_crb_L64.pth); the SNR input
        column starts at zero, so training starts from expert performance.
Data  : generated on the fly, batched in torch. Symbol-rate AWGN model, same
        as NN_model.py / Hybrid.py training.

Usage:
    python train_snr_nn.py --epochs 80 --steps 500
"""

import argparse
import os
import paths
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

from Hybrid import FusionNetwork, DenseCFOEstimator

if __name__ == "__main__" and "--length" in sys.argv:   # the environment carries it to the producer processes
    os.environ["CFO_EST_LEN"] = sys.argv[sys.argv.index("--length") + 1]
PREAMBLE_LENGTH = int(os.environ.get("CFO_EST_LEN", "128"))   # known symbols per estimate (training/evaluation)
MAX_CFO = 0.2
MAX_LAG = PREAMBLE_LENGTH // 2    # lags m = 1..L/2, as M&M's N = L0/2 (64 for L = 128)
EVAL_SNRS = list(range(-5, 11))
SNR_CENTER = 2.5   # (snr_db - center) / scale maps [-5, 10] dB to [-1, 1]
SNR_SCALE = 7.5

EXPERT_PATH = paths.model("best_cfo_model_crb_L64.pth")
FUSION_PATH = paths.model("unified_hybrid_cfo_model.pth")
OUT_PATH = paths.model("snr_aware_cfo_model_L64.pth")


# =====================================================================
# Model
# =====================================================================

class SNRAwareCFOEstimator(nn.Module):
    """Phase-1 expert MLP with the SNR (dB) appended to the flattened features."""

    def __init__(self, max_lag=MAX_LAG, hidden=(128, 64, 32), in_channels=4, use_snr=True):
        super().__init__()
        self.use_snr = use_snr
        layers = []
        d = max_lag * in_channels + 1
        for h in hidden:
            layers += [nn.Linear(d, h), nn.GELU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x, snr_db):
        s = (snr_db.view(-1, 1) - SNR_CENTER) / SNR_SCALE
        if not self.use_snr:   # ablation: SNR input held at 0
            s = torch.zeros_like(s)
        return self.net(torch.cat([x.flatten(1), s], dim=1))


def init_from_shorter(model, state):
    """
    Warm start from an SNR-aware NN trained on fewer lags: lags 1..M_old keep their first-layer weights, the
    extra lags start at 0, the SNR column moves to the new last input; deeper layers are copied as they are.
    """
    lins = [m for m in model.net if isinstance(m, nn.Linear)]
    keys = [k for k in state if k.endswith(".weight")]
    with torch.no_grad():
        for i, (lin, wk) in enumerate(zip(lins, keys)):
            w, b = state[wk], state[wk.replace(".weight", ".bias")]
            if i == 0:
                lin.weight.zero_()
                lin.weight[:, :w.shape[1] - 1] = w[:, :-1]         # lag features (lag-major, 4 channels)
                lin.weight[:, -1] = w[:, -1]                       # SNR input
            else:
                lin.weight.copy_(w)
            lin.bias.copy_(b)


def init_from_expert(model, expert_state):
    """Copy expert weights; the extra SNR column of the first layer starts at 0."""
    expert_layers = [k for k in expert_state if k.endswith(".weight")]
    model_linears = [m for m in model.net if isinstance(m, nn.Linear)]
    if len(expert_layers) != len(model_linears):
        raise ValueError("Expert and model have different depth; use --no-expert-init")
    with torch.no_grad():
        for lin, wkey in zip(model_linears, expert_layers):
            w = expert_state[wkey]
            b = expert_state[wkey.replace(".weight", ".bias")]
            if lin.weight.shape[0] != w.shape[0]:
                raise ValueError("Expert and model have different widths; use --no-expert-init")
            lin.weight.zero_()
            lin.weight[:, :w.shape[1]] = w
            lin.bias.copy_(b)


# =====================================================================
# Data (batched, torch)
# =====================================================================

def crb(snr_db, L=PREAMBLE_LENGTH):
    snr = 10.0 ** (snr_db / 10.0)
    return 3.0 / (2.0 * np.pi ** 2 * snr * L * (L ** 2 - 1))


def make_batch(batch_size, snr_low, snr_high, gen, device, fixed_snr=None):
    """
    Returns lag features (B, MAX_LAG, 4), M&M-ready correlations R (B, MAX_LAG),
    normalized CFO target (B, 1) and SNR in dB (B,).
    """
    z, y, snr_db = make_z(batch_size, snr_low, snr_high, gen, fixed_snr)
    feats, R = lag_features(z)
    return feats.to(device), R, y.float().to(device), snr_db.float().to(device)


def make_z(batch_size, snr_low, snr_high, gen, fixed_snr=None):
    """
    Known 128-symbol QPSK sequences through the FULL Tx/Rx chain (txrx_chain.py = main.py: upsample, RRC,
    CFO before the matched filter, AWGN, matched RRC, downsample); z[n] = r[n] * conj(s[n]).
    CFO ~ U[-MAX_CFO, MAX_CFO], random carrier phase, Es/N0 ~ U[snr_low, snr_high] (or fixed_snr).

    Returns z (B, L) complex128, normalized CFO y (B, 1) and SNR in dB (B,), float64 tensors.
    """
    from txrx_chain import known_sequence
    rng = np.random.default_rng(int(torch.randint(0, 2 ** 62, (1,), generator=gen)))   # reproducible from gen
    if fixed_snr is None:
        snr_db = rng.uniform(snr_low, snr_high, batch_size)
    else:
        snr_db = np.full(batch_size, float(fixed_snr))
    z, f = known_sequence(batch_size, PREAMBLE_LENGTH, snr_db, rng, max_cfo=MAX_CFO)
    return (torch.from_numpy(z), torch.from_numpy(f / MAX_CFO).unsqueeze(1), torch.from_numpy(snr_db))


def lag_features(z, max_lag=None):
    """Expert features (B, M, 4) float32 and complex correlations R (B, M); M = max_lag or L/2 of z (B, L)."""
    L = z.shape[1]
    M = max_lag or L // 2
    # C_m = mean_n z[n] conj(z[n-m]),  m = 1..M  (via FFT autocorrelation)
    Z = torch.fft.fft(z, n=2 * L)
    acf = torch.fft.ifft(Z * Z.conj())[:, 1:M + 1]
    R = acf / torch.arange(L - 1, L - M - 1, -1, dtype=torch.float64)

    feats = torch.stack([R.real, R.imag, R.abs(), R.angle()], dim=2).float()
    return feats, R


def mm_estimate(R, L=None):
    """Batched Mengali & Morelli, same as Hybrid.mm_cfo_estimate. Returns normalized CFO.
    R (B, M) from lag_features; L = sequence length, default 2 M (the paper's N = L0/2)."""
    M = R.shape[1]
    L = L or 2 * M
    dphi = torch.empty(R.shape, dtype=torch.float64)
    dphi[:, 0] = R[:, 0].angle()
    dphi[:, 1:] = (R[:, 1:] * R[:, :-1].conj()).angle()
    m = torch.arange(1, M + 1, dtype=torch.float64)
    w = 3 * ((L - m) * (L - m + 1) - M * (L - M)) / (M * (4 * M ** 2 - 6 * M * L + 3 * L ** 2 - 1))
    return ((dphi * w).sum(1) / (2 * np.pi) / MAX_CFO).float().unsqueeze(1)


def make_eval_sets(n_per_snr, seed, device):
    gen = torch.Generator().manual_seed(seed)
    return {s: make_batch(n_per_snr, s, s, gen, device, fixed_snr=s) for s in EVAL_SNRS}


# =====================================================================
# Evaluation
# =====================================================================

@torch.no_grad()
def mse_per_snr(predict, eval_sets):
    """predict(feats, R, snr_db) -> normalized CFO estimate (B, 1)."""
    out = {}
    for s, (feats, R, y, snr_db) in eval_sets.items():
        pred = predict(feats, R, snr_db)
        out[s] = float((((pred - y) * MAX_CFO) ** 2).mean())
    return out


def print_table(title, columns, mses):
    print("\n" + title)
    print(f"{'SNR':>5} | " + " | ".join(f"{c:>20}" for c in columns) + f" | {'CRB':>10}")
    for s in EVAL_SNRS:
        cells = []
        for c in columns:
            v = mses[c][s]
            cells.append(f"{v:.3e} (x{v / crb(s):5.2f})")
        print(f"{s:>5} | " + " | ".join(f"{x:>20}" for x in cells) + f" | {crb(s):.3e}")


def count_params(module):
    return sum(p.numel() for p in module.parameters())


# =====================================================================
# Training
# =====================================================================

def _producer(seed, q, B, lo, hi):
    """Worker process: full-chain training batches (feats, y, snr as numpy) into the bounded queue q."""
    torch.set_num_threads(1)
    gen = torch.Generator().manual_seed(seed)
    while True:
        f, _, y, s = make_batch(B, lo, hi, gen, "cpu")
        q.put((f.numpy(), y.numpy(), s.numpy()))


def train(args):
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    import txrx_chain
    txrx_chain.FFT_WORKERS = args.threads           # multi-threaded chain convolutions for the training data
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} | threads: {torch.get_num_threads()}", flush=True)

    expert_state = torch.load(EXPERT_PATH, map_location="cpu", weights_only=True) if MAX_LAG == 64 else None
    model = SNRAwareCFOEstimator(hidden=tuple(args.hidden), use_snr=not args.no_snr).to(device)
    if args.init_short:                             # longer sequence: start from the shorter-sequence model
        init_from_shorter(model, torch.load(args.init_short, map_location="cpu", weights_only=False)["state_dict"])
        print(f"Initialized from {args.init_short} (lags 1..{args.short_lags} copied, the rest 0)")
    elif args.init:                                 # fine-tune an existing SNR-aware checkpoint
        model.load_state_dict(torch.load(args.init, map_location="cpu", weights_only=False)["state_dict"])
        print(f"Initialized from {args.init}")
    elif not args.no_expert_init:
        init_from_expert(model, expert_state)
        print(f"Initialized from {EXPERT_PATH}")
    print(f"SNR-aware model: hidden={args.hidden}, params={count_params(model)}")

    val_sets = make_eval_sets(args.val_per_snr, args.seed + 1, device)
    crb_t = lambda snr_db: torch.as_tensor(crb(snr_db.double().cpu().numpy()), dtype=torch.float32, device=device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-6)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs * args.steps, eta_min=args.lr * 1e-3)
    gen = torch.Generator().manual_seed(args.seed)
    if args.producers:                               # the chain is costly: generate batches in parallel
        import multiprocessing as mp
        q = mp.Queue(maxsize=64)
        for i in range(args.producers):
            mp.Process(target=_producer, daemon=True,
                       args=(args.seed + 1000 * (i + 1), q, args.batch, *args.train_snr)).start()

        def next_batch():
            f, y, s = q.get()
            return torch.from_numpy(f).to(device), None, torch.from_numpy(y).to(device), torch.from_numpy(s).to(device)
    else:
        next_batch = lambda: make_batch(args.batch, args.train_snr[0], args.train_snr[1], gen, device)

    best_score, history = float("inf"), []
    predict = lambda f, R, s: model(f, s)

    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run_loss = time.time(), 0.0
        for _ in range(args.steps):
            feats, _, y, snr_db = next_batch()
            pred = model(feats, snr_db)
            loss = (((pred - y).squeeze(1) * MAX_CFO) ** 2 / crb_t(snr_db)).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            scheduler.step()
            run_loss += loss.item()

        model.eval()
        val = mse_per_snr(predict, val_sets)
        ratios = np.array([val[s] / crb(s) for s in EVAL_SNRS])
        score = ratios.mean()
        history.append((run_loss / args.steps, score))
        marker = ""
        if score < best_score:
            best_score = score
            torch.save({
                "state_dict": model.state_dict(),
                "config": {"max_lag": MAX_LAG, "max_cfo": MAX_CFO, "hidden": list(args.hidden),
                           "snr_center": SNR_CENTER, "snr_scale": SNR_SCALE,
                           "preamble_length": PREAMBLE_LENGTH, "train_snr": list(args.train_snr),
                           "use_snr": not args.no_snr},
            }, OUT_PATH)
            marker = " [BEST]"
        print(f"Epoch {epoch:3d}/{args.epochs} | train MSE/CRB {run_loss / args.steps:8.3f} | "
              f"val MSE/CRB mean {score:6.3f} max {ratios.max():6.3f} (@{EVAL_SNRS[ratios.argmax()]} dB) | "
              f"lr {scheduler.get_last_lr()[0]:.2e} | {time.time() - t0:.0f}s{marker}", flush=True)
        if epoch % 10 == 0 or epoch == args.epochs:
            print("   " + " ".join(f"{s}:{r:.2f}" for s, r in zip(EVAL_SNRS, ratios)), flush=True)

    return model, expert_state, history, device


# =====================================================================
# Final comparison
# =====================================================================

def final_comparison(args, expert_state, history, device):
    ckpt = torch.load(OUT_PATH, map_location=device, weights_only=False)
    model = SNRAwareCFOEstimator(hidden=tuple(ckpt["config"]["hidden"]),
                                 use_snr=ckpt["config"].get("use_snr", True)).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    if MAX_LAG != 64:                # the expert / fusion networks exist only for 64 lags (L = 128)
        return final_comparison_long(args, model, history, device)

    expert = DenseCFOEstimator(MAX_LAG, 4).to(device)
    expert.load_state_dict(expert_state)
    expert.eval()

    fusion_ckpt = torch.load(FUSION_PATH, map_location=device, weights_only=False)
    fusion_expert = DenseCFOEstimator(MAX_LAG, 4).to(device)
    fusion_expert.load_state_dict(fusion_ckpt["phase1_state"])
    fusion_expert.eval()
    fusion = FusionNetwork(in_features=2).to(device)
    fusion.load_state_dict(fusion_ckpt["phase2_state"])
    fusion.eval()

    def fusion_predict(f, R, s):
        nn_est = fusion_expert(f)
        mm_est = mm_estimate(R).to(device)
        est, _ = fusion(torch.cat([nn_est, mm_est], 1), nn_est, mm_est)
        return est

    predictors = {
        "SNR-aware NN": lambda f, R, s: model(f, s),
        "Expert NN": lambda f, R, s: expert(f),
        "Fusion": fusion_predict,
        "M&M": lambda f, R, s: mm_estimate(R).to(device),
    }

    test_sets = make_eval_sets(args.test_per_snr, args.seed + 2, device)
    mses = {name: mse_per_snr(p, test_sets) for name, p in predictors.items()}

    print("\n" + "=" * 110)
    print(f"TEST: MSE (xCRB), {args.test_per_snr} samples per SNR, true SNR given to the SNR-aware NN")
    print("=" * 110)
    print_table("", list(predictors), mses)

    print("\nComplexity (trainable parameters):")
    print(f"  SNR-aware NN : {count_params(model):>7}")
    print(f"  Expert NN    : {count_params(expert):>7}")
    print(f"  Fusion total : {count_params(fusion_expert) + count_params(fusion):>7}  "
          f"(expert {count_params(fusion_expert)} + fusion net {count_params(fusion)} + M&M)")

    # ---- plots ----
    colors = {"SNR-aware NN": "#d62728", "Expert NN": "#2ca02c", "Fusion": "#1f77b4", "M&M": "#ff7f0e"}
    markers = {"SNR-aware NN": "o", "Expert NN": "s", "Fusion": "^", "M&M": "d"}

    plt.figure(figsize=(10, 6))
    for name in predictors:
        plt.semilogy(EVAL_SNRS, [mses[name][s] for s in EVAL_SNRS], marker=markers[name],
                     color=colors[name], label=name)
    plt.semilogy(EVAL_SNRS, [crb(s) for s in EVAL_SNRS], "r--", linewidth=2, label="CRB")
    plt.xlabel("SNR (dB)")
    plt.ylabel("CFO MSE")
    plt.title("CFO estimation MSE vs. SNR (SNR-aware single NN vs. fusion)")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"snr_aware_mse_vs_snr{args.tag}.png"), dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    for name in predictors:
        plt.plot(EVAL_SNRS, [mses[name][s] / crb(s) for s in EVAL_SNRS], marker=markers[name],
                 color=colors[name], label=name)
    plt.axhline(1.0, color="r", linestyle="--", linewidth=2, label="CRB")
    plt.yscale("log")
    plt.xlabel("SNR (dB)")
    plt.ylabel("MSE / CRB")
    plt.title("Efficiency: MSE / CRB vs. SNR")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"snr_aware_mse_over_crb{args.tag}.png"), dpi=300, bbox_inches="tight")
    plt.close()

    if history:
        tr, va = zip(*history)
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(tr) + 1), tr, label="Train MSE/CRB")
        plt.plot(range(1, len(va) + 1), va, "--", label="Val mean MSE/CRB")
        plt.yscale("log")
        plt.xlabel("Epoch")
        plt.ylabel("MSE / CRB")
        plt.title("SNR-aware NN training")
        plt.grid(True, which="both", linestyle=":", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(paths.plot(f"snr_aware_training{args.tag}.png"), dpi=300, bbox_inches="tight")
        plt.close()


def final_comparison_long(args, model, history, device):
    """L != 128: SNR-aware NN vs M&M (N = L/2) on the test sets, MSE and MSE/CRB plots, training curve."""
    test_sets = make_eval_sets(args.test_per_snr, args.seed + 2, device)
    predictors = {"SNR-aware NN": lambda f, R, s: model(f, s), "M&M": lambda f, R, s: mm_estimate(R).to(device)}
    mses = {name: mse_per_snr(p, test_sets) for name, p in predictors.items()}
    print("\n" + "=" * 80)
    print(f"TEST (L = {PREAMBLE_LENGTH}, {MAX_LAG} lags): MSE (xCRB), {args.test_per_snr} samples per SNR")
    print("=" * 80)
    print_table("", list(predictors), mses)
    print(f"\nSNR-aware NN parameters: {count_params(model)}")
    colors, markers = {"SNR-aware NN": "#9467bd", "M&M": "#2ca02c"}, {"SNR-aware NN": "D", "M&M": "^"}
    for ratio in (False, True):
        plt.figure(figsize=(9, 5.5))
        for n in predictors:
            plt.semilogy(EVAL_SNRS, [mses[n][s] / (crb(s) if ratio else 1) for s in EVAL_SNRS],
                         marker=markers[n], color=colors[n], label=n)
        if not ratio:
            plt.semilogy(EVAL_SNRS, [crb(s) for s in EVAL_SNRS], "k:", linewidth=1.8, label="CRB")
        plt.xlabel("SNR (Es/N0) [dB]")
        plt.ylabel("CFO MSE / CRB" if ratio else "CFO MSE")
        plt.title(f"CFO estimation, L = {PREAMBLE_LENGTH} (test set)")
        plt.grid(True, which="both", linestyle=":", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(paths.plot(f"snr_aware_mse_{'over_crb' if ratio else 'vs_snr'}{args.tag}.png"), dpi=300,
                    bbox_inches="tight")
        plt.close()
    if history:
        tr, va = zip(*history)
        plt.figure(figsize=(9, 5.5))
        plt.plot(range(1, len(tr) + 1), tr, label="Train MSE/CRB")
        plt.plot(range(1, len(va) + 1), va, "--", label="Val mean MSE/CRB")
        plt.yscale("log")
        plt.xlabel("Epoch")
        plt.ylabel("MSE / CRB")
        plt.title(f"SNR-aware NN training, L = {PREAMBLE_LENGTH}")
        plt.grid(True, which="both", linestyle=":", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(paths.plot(f"snr_aware_training{args.tag}.png"), dpi=300, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=int, default=128,
                        help="known symbols per estimate (lags = length/2); != 128 needs --init-short or "
                             "--no-expert-init. Set CFO_STUDY to keep the outputs in their own folder")
    parser.add_argument("--init-short", default="", help="warm start from a shorter-sequence SNR-aware model")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--steps", type=int, default=500, help="batches per epoch")
    parser.add_argument("--batch", type=int, default=1024)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--hidden", type=int, nargs="+", default=[128, 64, 32])
    parser.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    parser.add_argument("--val-per-snr", type=int, default=5000)
    parser.add_argument("--test-per-snr", type=int, default=20000)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--no-snr", action="store_true", help="ablation: SNR input held at 0")
    parser.add_argument("--no-expert-init", action="store_true")
    parser.add_argument("--tag", default="", help="suffix for output files, e.g. _lr3e-5")
    parser.add_argument("--eval-only", action="store_true", help="skip training, evaluate saved model")
    parser.add_argument("--init", default="", help="start from this SNR-aware checkpoint instead of the expert")
    parser.add_argument("--producers", type=int, default=0, help="data-generation processes (0: inline)")
    args = parser.parse_args()
    OUT_PATH = paths.model(f"snr_aware_cfo_model_L{MAX_LAG}{args.tag}.pth")
    if args.init_short:
        args.short_lags = torch.load(args.init_short, map_location="cpu", weights_only=False)["config"]["max_lag"]

    if args.eval_only:
        final_comparison(args, torch.load(EXPERT_PATH, map_location="cpu", weights_only=True) if MAX_LAG == 64
                         else None, [], torch.device("cpu"))
    else:
        _, expert_state, history, device = train(args)
        final_comparison(args, expert_state, history, device)
    print("TRAIN DONE", flush=True)
