"""
Stage 3: neural coarse CFO estimator for the zero-overhead burst receiver, on the 8-SPS matched-filter output.

Why 8 SPS: at symbol rate the CFO cell cannot be learned. A CFO shift of 1/4 multiplies symbol n by j^n,
which maps a random QPSK burst onto another equally likely QPSK burst, so the symbol-rate samples carry
no information about the cell k (first attempt: k-error stayed at the prior P(k != 0) = 0.37, see
results_coarse_nn/train_symrate.log). Between the symbol instants the shift also moves the pulse
spectrum by Rs/4, which the oversampled signal shows: the 4th-power line at 4f is unambiguous over +-4 Rs.

Front end (waveform): symbols -> symbol-spaced channel (AWGN: 1 tap; multipath: 3 taps) -> RRC (beta 0.25,
span 10, 8 SPS) -> + white noise -> matched RRC -> CFO and phase rotation exp(j(2 pi f m / 8 + phi)).
The signal CFO is applied after the matched filter (CFO small against the filter bandwidth), the noise is
the matched-filtered white noise (not rotated, its spectrum stays centred at 0), so
every 8th sample z8[8n] is exactly the symbol-rate burst r[n] of Stages 1-2 (signal x[n] e^{j..}, white
noise of variance N0): the decoding receivers run on it unchanged, the NN additionally sees z8.

Inputs (from z8, 514 x 8 = 4112 samples, unit RMS)
    z8       real/imag -> (2, 4112)
    spec     |FFT_16384(z8^4)| cropped to |4f| <= 4 * 0.2 (+ margin): 3317 bins of 1/2048 cycles/symbol,
             unit energy, log-compressed. The line at 4f is unambiguous; its symbol-rate harmonics at
             4f -+ 1 also fall inside the crop, which is what makes the classical peak pick fail.
    zoom     |DTFT(z8^4)| at the spectrum peak nu_pk + (-16..16)/4 bins (quarter-bin steps), max-normalised
    nu_pk    the peak position itself (4f in cycles/symbol)

Architecture
    CNN on z8    4 x [Conv1d(kernel 7, stride 2) + GELU], channels 32, 32, 64, 64, global average pool -> 64
    MLP on spec  3317 -> 256 -> 128;   MLP on zoom  33 -> 64 -> 32
    head         concat(64 + 128 + 32 + 1) -> 128 -> 64 -> 4 = 3 logits for k + residual rho
Outputs
    k        CFO cell, f = k/4 + f_fine, k in {-1, 0, 1}
    rho      fine residual in FFT bins (|rho| <= 4): 4 f_hat = nu_pk + rho / 2048, f_fine = that / 4
             wrapped to [-1/8, 1/8)
Training (on the fly): polar-coded bursts (R = 1/2 or 1/4), AWGN or 3-tap Rayleigh (p = 0.5),
    CFO ~ U[-0.2, 0.2], phase ~ U[0, 2 pi), Es/N0 ~ U[-6, 11] dB.
    loss = CE(k) + lam * log(1 + e^2 / CRB(Es/N0, 512)),  e = f error of the fine part, counted only
    where the peak is within 4 bins of the true line (elsewhere no residual can fix it).

Usage (project folder):
    python multipath/coarse_nn.py --train      # -> multipath/results_coarse_nn/coarse_nn.pth, train.log
    python multipath/coarse_nn.py --eval       # stand-alone CFO metrics vs. Es/N0 (AWGN, multipath), eval.log
"""

import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.signal import fftconvolve

import channel
import config as cfg

N_SYM, N_RX, MAX_CFO, SPS = 512, 514, 0.2, 8
M8 = N_RX * SPS                                      # 4112 oversampled samples
K_OS = 16384                                         # FFT of z8^4: bin = 8 / 16384 = 1/2048 cycles/symbol
BIN = SPS / K_OS
FR = np.fft.fftshift(np.fft.fftfreq(K_OS)) * SPS     # cycles/symbol (of the 4th power, i.e. 4f)
CROP = np.abs(FR) <= 4 * MAX_CFO + 0.01
N_SPEC = int(CROP.sum())
ZOOM = np.arange(-16, 17) / 4 * BIN                  # +-4 bins, quarter-bin steps
_EZ = np.exp(-2j * np.pi * np.outer(np.arange(M8), ZOOM) / SPS)   # (M8, 33)
RRC = np.asarray(channel.rrc_design(cfg.BETA, SPS, cfg.FILTER_SPAN))
OUT = os.path.join(HERE, "results_coarse_nn")
MODEL_PATH = os.path.join(OUT, "coarse_nn.pth")
TAPS_DB = {"awgn": [0.0], "multipath": [0.0, -3.0, -6.0]}


# =====================================================================
# Front end
# =====================================================================

def waveform(x, f, ph, snr, rng):
    """Symbol-rate channel output x (B, 514) -> 8-SPS matched-filter output z8 (B, 4112) and r = z8[:, ::8]."""
    B = len(x)
    up = np.zeros((B, M8), complex)
    up[:, ::SPS] = x
    tx = fftconvolve(up, RRC[None], axes=1)
    w = np.sqrt(1 / (2 * np.asarray(snr, float)))
    w = (np.broadcast_to(w, (B,))[:, None]) * (rng.standard_normal(tx.shape) + 1j * rng.standard_normal(tx.shape))
    D = len(RRC) - 1
    sig = fftconvolve(tx, RRC[None], axes=1)[:, D:D + M8]
    noise = fftconvolve(w, RRC[None], axes=1)[:, D:D + M8]      # not rotated: its spectrum stays at 0
    m = np.arange(M8)
    z8 = sig * np.exp(1j * (2 * np.pi * f[:, None] * m / SPS + ph[:, None])) + noise
    return z8, z8[:, ::SPS]


# =====================================================================
# Model
# =====================================================================

class CoarseCFONet(nn.Module):
    def __init__(self, ch=(32, 32, 64, 64), k=7, spec_hidden=(256, 128), zoom_hidden=(64, 32), head=(128, 64)):
        super().__init__()
        convs, c_in = [], 2
        for c in ch:
            convs += [nn.Conv1d(c_in, c, k, stride=2, padding=k // 2), nn.GELU()]
            c_in = c
        self.cnn = nn.Sequential(*convs)

        def mlp(d, hidden):
            layers = []
            for h in hidden:
                layers += [nn.Linear(d, h), nn.GELU()]
                d = h
            return nn.Sequential(*layers), d
        self.spec, d_s = mlp(N_SPEC, spec_hidden)
        self.zoom, d_z = mlp(len(ZOOM), zoom_hidden)
        self.head, d = mlp(c_in + d_s + d_z + 1, head)
        self.out = nn.Linear(d, 4)

    def forward(self, z_iq, spec, zoom, nu_pk):
        a = self.cnn(z_iq).mean(2)                  # global average pooling
        o = self.out(self.head(torch.cat([a, self.spec(spec), self.zoom(zoom), nu_pk[:, None]], 1)))
        return o[:, :3], 4 * torch.tanh(o[:, 3])    # k logits, residual in bins


def features(z8):
    """z8 (B, 4112) complex numpy -> float32 arrays (z_iq, spec, zoom, nu_pk)."""
    x = z8 / np.sqrt(np.mean(np.abs(z8) ** 2, axis=1, keepdims=True))
    x4 = x ** 4
    S = np.abs(np.fft.fftshift(np.fft.fft(x4, n=K_OS, axis=1), axes=1))[:, CROP]
    nu_pk = FR[CROP][S.argmax(1)]
    S = S / np.sqrt(np.sum(S ** 2, axis=1, keepdims=True))
    Z = np.abs((x4 * np.exp(-2j * np.pi * nu_pk[:, None] * np.arange(M8) / SPS)) @ _EZ)
    Z = Z / Z.max(1, keepdims=True)
    return tuple(np.ascontiguousarray(a, dtype=np.float32)
                 for a in (np.stack([x.real, x.imag], 1), np.log1p(64 * S), Z, nu_pk))


def inputs(z8):
    """z8 (B, 4112) complex numpy -> float32 tensors (z_iq, spec, zoom, nu_pk)."""
    return tuple(torch.from_numpy(a) for a in features(z8))


def fine_from(nu_pk, rho):
    """f_fine in [-1/8, 1/8) from the peak and the residual (bins)."""
    return ((nu_pk + rho * BIN) / 4 + 0.125) % 0.25 - 0.125


def decode_outputs(logits, rho, nu_pk):
    """-> f_hat (B,), k_hat (B,) in {-1,0,1}, class probabilities (B, 3), f_fine (B,)."""
    p = F.softmax(logits, 1).numpy()
    k = p.argmax(1) - 1
    f_fine = fine_from(nu_pk.numpy().astype(float), rho.numpy().astype(float))
    return f_fine + k / 4, k, p, f_fine


_cache = {}


def load(path=MODEL_PATH):
    if path not in _cache:
        m = CoarseCFONet()
        m.load_state_dict(torch.load(path, map_location="cpu")["state_dict"])
        m.eval()
        _cache[path] = m
    return _cache[path]


def estimate(z8, path=MODEL_PATH, polish=True, chunk=500):
    """
    Coarse CFO of 8-SPS bursts z8 (numpy, (B, 4112)): returns f_hat, k_hat, class probabilities, f_fine.
    polish: 2 Newton steps on the symbol-rate r^4 periodogram from the NN fine estimate.
    """
    model = load(path)
    out = []
    with torch.no_grad():
        for i in range(0, len(z8), chunk):
            zi, sp, zo, nu = inputs(z8[i:i + chunk])
            out.append(decode_outputs(*model(zi, sp, zo, nu), nu))
    f, k, p, f_fine = (np.concatenate(v) for v in zip(*out))
    if polish:
        from zero_overhead_rx import newton
        r = z8[:, ::SPS][:, :N_SYM]
        nu = newton(r ** 4, 4 * f_fine)                         # r^4 tone at 4 f (mod 1)
        delta = ((nu / 4 - f_fine) + 0.125) % 0.25 - 0.125      # correction, wrapped so k stays valid
        f_fine = f_fine + delta
        f = f + delta
    return f, k, p, f_fine


def macs():
    """Multiply-accumulates of one forward pass (convolutions + linear layers) and of the input features."""
    m, L = 0, M8
    for layer in load().cnn:
        if isinstance(layer, nn.Conv1d):
            L = (L + 2 * layer.padding[0] - layer.kernel_size[0]) // layer.stride[0] + 1
            m += L * layer.in_channels * layer.out_channels * layer.kernel_size[0]
    m += sum(l.in_features * l.out_features for l in load().modules() if isinstance(l, nn.Linear))
    feats = 3 * M8 + 2 * K_OS * np.log2(K_OS) + M8 * (len(ZOOM) + 1)      # z^4, FFT, zoom DTFT
    return m, int(feats)


# =====================================================================
# Data
# =====================================================================

class BurstGenerator:
    """Random polar-coded QPSK bursts through AWGN or 3-tap Rayleigh, with CFO and phase, at 8 SPS."""

    def __init__(self, seed):
        from polar import PolarCode
        from zero_overhead_rx import CODES, interleaver
        self.rng = np.random.default_rng(seed)
        self.codes = [PolarCode(1024, A, C, 8) for A, C in CODES.values()]
        self.inter = interleaver()

    def batch(self, B, snr_lo, snr_hi, p_multipath=0.5, fixed_snr=None, channel=None):
        rng = self.rng
        code = self.codes[rng.integers(len(self.codes))]
        cw = code.encode(rng.integers(0, 2, (B, code.A), dtype=np.uint8))[:, self.inter]
        s = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        mp = (rng.random(B) < p_multipath) if channel is None else np.full(B, channel == "multipath")
        p = 10 ** (np.asarray(TAPS_DB["multipath"]) / 10)
        p = p / p.sum()
        h = (rng.standard_normal((B, 3)) + 1j * rng.standard_normal((B, 3))) * np.sqrt(p / 2)
        h[~mp] = [1, 0, 0]
        x = np.zeros((B, N_RX), complex)
        for t in range(3):
            x[:, t:t + N_SYM] += h[:, t:t + 1] * s
        f = rng.uniform(-MAX_CFO, MAX_CFO, B)
        ph = rng.uniform(0, 2 * np.pi, B)
        snr_db = np.full(B, fixed_snr, float) if fixed_snr is not None else rng.uniform(snr_lo, snr_hi, B)
        z8, _ = waveform(x, f, ph, 10 ** (snr_db / 10), rng)
        return z8, f, snr_db


def labels(f):
    k = np.clip(np.round(4 * f), -1, 1)
    return k.astype(int), f - k / 4


def crb(snr_db, L=N_SYM):
    return 3.0 / (2.0 * np.pi ** 2 * 10 ** (np.asarray(snr_db) / 10) * L * (L ** 2 - 1))


def residual_target(f, nu_pk):
    """True residual 4f - nu_pk in bins, modulo one cell (the k head picks the cell)."""
    return (((4 * f - nu_pk) + 0.5) % 1.0 - 0.5) / BIN


# =====================================================================
# Train
# =====================================================================

def _producer(seed, q, B, snr_lo, snr_hi, p_mp):
    """Worker process: training batches (features, f, Es/N0) into the bounded queue q, forever."""
    torch.set_num_threads(1)
    gen = BurstGenerator(seed)
    while True:
        z8, f, snr = gen.batch(B, snr_lo, snr_hi, p_multipath=p_mp)
        q.put((features(z8), f, snr))


def train(args, log):
    import multiprocessing as mp
    torch.manual_seed(args.seed)
    q = mp.Queue(maxsize=32)
    procs = [mp.Process(target=_producer, daemon=True,
                        args=(args.seed + 1000 * (i + 1), q, args.batch, *args.train_snr, args.p_multipath))
             for i in range(args.producers)]
    for p in procs:
        p.start()
    model = CoarseCFONet()
    log(f"CoarseCFONet (8 SPS): {sum(p.numel() for p in model.parameters()):,} parameters")
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=args.epochs * args.steps)
    vgen = BurstGenerator(args.seed + 1)
    val = {}
    for ch in ("awgn", "multipath"):
        for s in (-5, 0, 5, 10):
            z8, f, _ = vgen.batch(args.val_per_snr, s, s, fixed_snr=s, channel=ch)
            val[(ch, s)] = (inputs(z8), f)
    best = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train()
        t0, run_ce, run_f = time.time(), 0.0, 0.0
        for _ in range(args.steps):
            feats, f, snr = q.get()
            k, _ = labels(f)
            x = tuple(torch.from_numpy(a) for a in feats)
            logits, rho = model(*x)
            ce = F.cross_entropy(logits, torch.from_numpy(k + 1))
            t = torch.from_numpy(residual_target(f, x[3].numpy().astype(float))).float()
            ok = (t.abs() <= 4).float()
            e = (rho - t) * BIN / 4                                          # error of f (cycles/symbol)
            lf = (torch.log1p(e ** 2 / torch.from_numpy(crb(snr)).float()) * ok).sum() / ok.sum().clamp(min=1)
            loss = ce + args.lam * lf
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            run_ce += ce.item()
            run_f += lf.item()
        model.eval()
        msg, score = [], 0.0
        with torch.no_grad():
            for (ch, s), (x, f) in val.items():
                fh, kh, _, _ = decode_outputs(*model(*x), x[3])
                err = np.abs(fh - f)
                kerr = np.mean(kh != labels(f)[0])
                score += kerr + np.mean(err > 1e-3)
                msg.append(f"{ch[:2]}{s:+d}: k-err {kerr:.3f} med {np.median(err):.1e}")
        mark = ""
        if score < best:
            best = score
            torch.save({"state_dict": model.state_dict()}, MODEL_PATH)
            mark = " [BEST]"
        log(f"Epoch {epoch:3d}/{args.epochs} | CE {run_ce / args.steps:.3f} | fine {run_f / args.steps:.2f} | "
            + " | ".join(msg) + f" | {time.time() - t0:.0f}s{mark}")
    log("TRAIN DONE")


# =====================================================================
# Stand-alone evaluation against Algorithm 1 (4th power)
# =====================================================================

NAMES = ["4th power, k = 0", "4th power + OS cell", "4th power, oracle k", "NN", "NN + polish"]


def evaluate(args, log):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from zero_overhead_rx import fourth_power
    snrs = list(range(-5, 11))
    res = {}
    gen = BurstGenerator(args.seed + 2)
    n_chunks = args.test_per_snr // 2000
    total, done, t0 = 2 * len(snrs) * n_chunks, 0, time.time()
    prog = os.path.join(OUT, "eval.progress")                       # job_progress.py ("count" kind)
    for ch in ("awgn", "multipath"):
        for nm in NAMES:
            res[(ch, nm)] = {"median": [], "p1e4": [], "p1e3": [], "kerr": []}
        for s in snrs:
            errs, kerr = {nm: [] for nm in NAMES}, {nm: [] for nm in NAMES}
            for _ in range(n_chunks):
                z8, f, _ = gen.batch(2000, s, s, fixed_snr=s, channel=ch)
                kt, _ = labels(f)
                f0, _ = fourth_power(z8[:, ::SPS][:, :N_SYM])
                ks = np.array([-1, 0, 1])
                cand = f0[:, None] + ks / 4
                valid = np.abs(cand) <= MAX_CFO + 0.005
                nu_pk = inputs(z8)[3].numpy().astype(float)
                k_os = ks[np.where(valid, np.abs(cand - nu_pk[:, None] / 4), np.inf).argmin(1)]
                k_or = ks[np.abs(cand - f[:, None]).argmin(1)]
                fn, kn, _, _ = estimate(z8, polish=False)
                fp, _, _, _ = estimate(z8, polish=True)
                for nm, fh, kh in (("4th power, k = 0", f0, np.zeros_like(kt)), ("4th power + OS cell", f0 + k_os / 4, k_os),
                                   ("4th power, oracle k", f0 + k_or / 4, k_or), ("NN", fn, kn), ("NN + polish", fp, kn)):
                    errs[nm].append(fh - f)
                    kerr[nm].append(np.round(4 * (fh - f)) != 0)      # landed in the wrong cell
                done += 1
                with open(prog, "w") as fp:
                    fp.write(f"{done} {total} {time.time() - t0:.0f}\n")
            for nm in NAMES:
                e = np.abs(np.concatenate(errs[nm]))
                res[(ch, nm)]["median"].append(np.median(e))
                res[(ch, nm)]["p1e4"].append(np.mean(e > 1e-4))
                res[(ch, nm)]["p1e3"].append(np.mean(e > 1e-3))
                res[(ch, nm)]["kerr"].append(np.mean(np.concatenate(kerr[nm])))
        log(f"\n{ch}: median |err| / P(|err| > 1e-4) / P(|err| > 1e-3) / P(wrong cell)   ({args.test_per_snr} bursts per point)")
        log(f"{'Es/N0':>5} | " + " | ".join(f"{nm:>36}" for nm in NAMES))
        for i, s in enumerate(snrs):
            log(f"{s:5d} | " + " | ".join(
                f"{res[(ch, nm)]['median'][i]:.1e} / {res[(ch, nm)]['p1e4'][i]:.3f} / {res[(ch, nm)]['p1e3'][i]:.3f} / "
                f"{res[(ch, nm)]['kerr'][i]:.4f}".rjust(36) for nm in NAMES))
    m, feats = macs()
    log(f"\nNN complexity per burst: {m:,} MACs (network) + ~{feats:,} (z^4, FFT 16384, zoom); "
        f"{sum(p.numel() for p in load().parameters()):,} parameters. "
        f"4th power (FFT 2048 + 2 Newton): ~{int(2 * 2048 * 11 + 3 * 512 + 2 * 3 * 512):,}")
    np.save(os.path.join(OUT, "coarse_eval.npy"), {"res": res, "snrs": snrs}, allow_pickle=True)
    colors = {"4th power, k = 0": "#bbbbbb", "4th power + OS cell": "#2ca02c", "4th power, oracle k": "#ff7f0e",
              "NN": "#9467bd", "NN + polish": "#d62728"}
    fig, axes = plt.subplots(2, 3, figsize=(19, 10))
    for row, ch in enumerate(("awgn", "multipath")):
        for col, (metric, yl) in enumerate((("median", "Median |CFO error|"), ("p1e4", "P(|CFO error| > 1e-4)"),
                                            ("kerr", "P(wrong CFO cell)"))):
            ax = axes[row, col]
            for nm in NAMES:
                if metric == "kerr" and nm in ("4th power, k = 0", "4th power, oracle k", "NN + polish"):
                    continue
                ax.semilogy(snrs, np.maximum(res[(ch, nm)][metric], 1e-6), color=colors[nm], marker="o", markersize=3, label=nm)
            ax.set_title(f"{'AWGN' if ch == 'awgn' else '3-tap Rayleigh'}: {yl}")
            ax.set_xlabel("Es/N0 [dB]")
            ax.grid(True, which="both", linestyle=":", alpha=0.6)
            ax.legend(fontsize=8)
    fig.suptitle("Blind coarse CFO, 512-symbol burst, no preamble: 8-SPS neural estimator vs. 4th power")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "coarse_nn_vs_4th_power.png"), dpi=300, bbox_inches="tight")
    log("EVAL DONE")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam", type=float, default=0.3, help="weight of the fine-CFO loss")
    ap.add_argument("--p-multipath", type=float, default=0.5)
    ap.add_argument("--train-snr", type=float, nargs=2, default=[-6.0, 11.0])
    ap.add_argument("--val-per-snr", type=int, default=1000)
    ap.add_argument("--test-per-snr", type=int, default=20000)
    ap.add_argument("--threads", type=int, default=12, help="torch threads (training / evaluation)")
    ap.add_argument("--producers", type=int, default=4, help="data-generation processes while training")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    os.makedirs(OUT, exist_ok=True)
    log_f = open(os.path.join(OUT, "train.log" if args.train else "eval.log"), "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    if args.train:
        train(args, log)
    if args.eval:
        evaluate(args, log)
