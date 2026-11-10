"""
est3 Method 2: neural CFO estimators on the 128-symbol preamble, trained on bursts from the full Tx/Rx chain.

    clustering NN   Li Zhen et al., "Clustering-NN based CFO estimation using random access preambles for 5G NTN",
                    IEEE WCL 13(3), 2024, adapted. The paper's input is the PDP of a Zadoff-Chu preamble,
                    p(m) = |(1/N) sum_n s*(n) y[(n + m) mod N]|^2; for a ZC sequence a CFO of eps subcarriers moves the
                    peak to lag (-eps_I / u) mod N, i.e. the PDP is a permuted periodogram of y s*. Our preamble is
                    random QPSK (the packet's own codeword symbols), so the same quantity is the periodogram of
                    z = r s*: P(k) = |(1/L) sum_n z[n] e^{-j 2 pi k n / L}|^2, k = 0 .. L-1 (L = 128 bins, no zero
                    padding, as the paper's N_ZC lags); eps = f L, eps_I = round(eps) in -4 .. 4 (K = 9 clusters).
                    As in the paper:
                      - samples scaled to [0, 1] (divided by their maximum)
                      - SSKC: K-means with K = the integer CFOs, initialised with the integer-CFO PDPs (here the
                        noiseless one: a delta at bin eps_I), Lloyd iterations on the training set; a cluster is
                        labelled by its initial integer CFO
                      - online cluster = the one whose centre's maximum peak is nearest to the sample's maximum peak
                        (eq. 7, circular distance in bins)
                      - SMDR: only the PDP values at the cluster's peak and its neighbours (the Dirichlet side lobes,
                        the paper's "multiples of (-1/u) mod N_ZC" positions): 2 W + 1 = 9 features
                      - one BPNN per cluster: 9 -> H = 5 tanh -> 1 tanh, MSE on the residual eps - eps_I(cluster),
                        trained on that cluster's K-means members
                    Differences (stated in the report): Adam instead of the paper's BP solver; SNR varied in training
                    (the paper trains at 20 dB only); random QPSK preamble instead of ZC.
    cnn-cr          CNN, classification + refinement (the task's primary candidate): z / rms(r) as 2 x 128 real
                    channels, 6 residual dilated conv blocks (32 channels), FC 256, heads: logits over NB = 24 CFO bins
                    of width 2.5e-3 and a residual per bin (in bin widths); loss CE + 10 MSE(residual of the true bin);
                    f_hat = centre(argmax) + width x residual(argmax)
    cnn-reg         the same backbone, one output f / MAX_CFO, MSE (direct regression)

Training data: generated on the fly (fresh bursts every step, never stored), random CFO over the whole range, random
phase, random preamble, SNR drawn from TRAIN_SNRS only (9 values; the evaluation grid is every integer -12 .. 16 dB,
so 20 of its 29 SNRs are never seen), AWGN.
Seeds: training streams 10_000_000 + ..., validation 20_000_000, evaluation (run_est / run_bler) < 10_000_000:
no burst or noise realisation is shared between training, validation and test.

    python est3/nn.py train --what cnn-cr cnn-reg cluster --device cuda
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn

from est3.common import L_P, MAX_CFO, TAIL, path, preamble_bursts, qpsk, transmit

TRAIN_SNRS = (-10.0, -7.0, -4.0, -1.0, 2.0, 5.0, 8.0, 11.0, 14.0)
NB = 24
BIN_W = 2 * MAX_CFO / NB
K_CL = 9                     # integer CFOs eps_I = -4 .. 4 (eps = f L, |eps| <= 3.84)
W_SM = 4                     # SMDR: bins eps_I - 4 .. eps_I + 4
H_BP = 5
TRAIN_SEED, VAL_SEED = 10_000_000, 20_000_000


def make_batch(B, rng, snrs=TRAIN_SNRS):
    """B training bursts (AWGN, full chain): z (B, L) complex, f (B,), snr (B,)."""
    snr = rng.choice(np.asarray(snrs, float), B)
    r, s, f, _ = preamble_bursts(B, snr, rng)
    return r * np.conj(s), f, snr


def nn_input(z):
    """2 x L float32 channels: z / rms(z) (scale-free: the network sees no SNR)."""
    zn = z / np.sqrt(np.mean(np.abs(z) ** 2, 1, keepdims=True))
    return np.stack([zn.real, zn.imag], 1).astype(np.float32)


# =====================================================================
# CNNs
# =====================================================================

class Block(nn.Module):
    def __init__(self, c, dil):
        super().__init__()
        self.c1 = nn.Conv1d(c, c, 5, padding=2 * dil, dilation=dil)
        self.c2 = nn.Conv1d(c, c, 5, padding=2 * dil, dilation=dil)
        self.b1, self.b2 = nn.BatchNorm1d(c), nn.BatchNorm1d(c)

    def forward(self, x):
        y = torch.relu(self.b1(self.c1(x)))
        return torch.relu(x + self.b2(self.c2(y)))


class CNN(nn.Module):
    def __init__(self, kind, c=32, fc=256):
        super().__init__()
        self.kind = kind
        self.stem = nn.Sequential(nn.Conv1d(2, c, 7, padding=3), nn.BatchNorm1d(c), nn.ReLU())
        self.blocks = nn.Sequential(*[Block(c, d) for d in (1, 2, 4, 8, 16, 32)])
        self.fc = nn.Sequential(nn.Flatten(), nn.Linear(c * L_P, fc), nn.ReLU())
        self.head = nn.Linear(fc, 2 * NB if kind == "cnn-cr" else 1)

    def forward(self, x):
        return self.head(self.fc(self.blocks(self.stem(x))))


CENTRES = -MAX_CFO + BIN_W * (np.arange(NB) + 0.5)


def cnn_decode(kind, out):
    """CFO (B,) from the network output (numpy)."""
    if kind == "cnn-reg":
        return out[:, 0] * MAX_CFO
    b = out[:, :NB].argmax(1)
    return CENTRES[b] + BIN_W * out[np.arange(len(out)), NB + b]


def cnn_loss(kind, out, f):
    if kind == "cnn-reg":
        return torch.mean((out[:, 0] - f / MAX_CFO) ** 2)
    b = torch.clamp(((f + MAX_CFO) / BIN_W).long(), 0, NB - 1)
    res = (f - torch.as_tensor(CENTRES, device=f.device, dtype=f.dtype)[b]) / BIN_W
    ce = nn.functional.cross_entropy(out[:, :NB], b)
    return ce + 10 * torch.mean((out[torch.arange(len(f)), NB + b] - res) ** 2)


def cnn_macs(c=32, fc=256, kind="cnn-cr"):
    conv = 2 * c * 7 * L_P + 12 * c * c * 5 * L_P
    return conv + c * L_P * fc + fc * (2 * NB if kind == "cnn-cr" else 1)


def n_params(m):
    return sum(p.numel() for p in m.parameters())


class Stream(torch.utils.data.IterableDataset):
    """Fresh bursts from the full chain, each worker its own seed stream (no repeats, no overlap)."""

    def __init__(self, B, seed):
        self.B, self.seed = B, seed

    def __iter__(self):
        wi = torch.utils.data.get_worker_info()
        rng = np.random.default_rng([self.seed, wi.id if wi else 0])
        while True:
            z, f, _ = make_batch(self.B, rng)
            yield torch.from_numpy(nn_input(z)), torch.from_numpy(f)


def val_set(n=40_000):
    rng = np.random.default_rng(VAL_SEED)
    z, f, snr = make_batch(n, rng)
    return nn_input(z), f, snr, None


def train_cnn(kind, device, epochs, steps, B, workers, log):
    torch.manual_seed(1)
    m = CNN(kind).to(device)
    opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, 2e-3, total_steps=epochs * steps)
    ld = torch.utils.data.DataLoader(Stream(B, TRAIN_SEED + (0 if kind == "cnn-cr" else 1_000_000)), batch_size=None,
                                     num_workers=workers, prefetch_factor=4, persistent_workers=True)
    xv, fv, sv, _ = val_set()
    xv_t = torch.from_numpy(xv).to(device)
    best, hist, t0 = np.inf, [], time.time()
    ck = path("models", f"{kind}.pth")
    it = iter(ld)
    for ep in range(epochs):
        m.train()
        tl = 0.0
        for _ in range(steps):
            x, f = next(it)
            x, f = x.to(device), f.to(device).float()
            loss = cnn_loss(kind, m(x), f)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tl += loss.item()
        m.eval()
        with torch.no_grad():
            out = torch.cat([m(xv_t[a:a + 4096]) for a in range(0, len(xv_t), 4096)]).cpu().numpy()
        e = cnn_decode(kind, out) - fv
        rm = {int(s): float(np.sqrt(np.mean(e[sv == s] ** 2))) for s in TRAIN_SNRS}
        v = float(np.mean(np.log10(list(rm.values()))))         # mean log-RMSE over the SNRs: every SNR counts
        hist.append(dict(epoch=ep + 1, train_loss=tl / steps, val_log_rmse=v, val_rmse=rm, time=time.time() - t0))
        log(f"{kind} epoch {ep + 1}/{epochs} loss {tl / steps:.4f} val log-RMSE {v:.3f} "
            f"(-10 dB {rm[-10]:.2e}, 2 dB {rm[2]:.2e}, 14 dB {rm[14]:.2e}) {time.time() - t0:.0f}s")
        with open(path("logs", f"train_{kind}.progress"), "w") as fp:
            fp.write(f"{ep + 1} {epochs} {time.time() - t0:.0f}\n")      # job_progress.py: done total seconds
        if v < best:
            best = v
            torch.save({"kind": kind, "state_dict": m.state_dict(), "epoch": ep + 1, "params": n_params(m),
                        "macs": cnn_macs(kind=kind), "train_snrs": TRAIN_SNRS, "hist": hist}, ck)
    ckd = torch.load(ck, map_location="cpu", weights_only=False)
    ckd["hist"], ckd["train_time_s"], ckd["samples"] = hist, time.time() - t0, epochs * steps * B
    torch.save(ckd, ck)


# =====================================================================
# Clustering NN (SSKC + SMDR-BPNN)
# =====================================================================

def pdp(z):
    """Normalised periodogram (B, L) of z, scaled to [0, 1] (the paper's PDP, see the module doc)."""
    P = np.abs(np.fft.fft(z, axis=1)) ** 2
    return (P / P.max(1, keepdims=True)).astype(np.float32)


def eps_bins(k):
    """FFT bin index of integer CFO k (eps_I = k cycles per L symbols)."""
    return np.asarray(k) % L_P


INT_CFO = np.arange(-(K_CL // 2), K_CL // 2 + 1)


def sm_features(p, k):
    """SMDR features (B, 2W+1): PDP at the bins of eps_I = k - W .. k + W."""
    idx = eps_bins(k[:, None] + np.arange(-W_SM, W_SM + 1)[None])
    return np.take_along_axis(p, idx, 1)


def cluster_online(p, centre_peaks):
    """eq. (7): the cluster whose centre's maximum peak is nearest (circular, in bins) to the sample's peak."""
    pk = p.argmax(1)
    d = np.abs(pk[:, None] - centre_peaks[None])
    d = np.minimum(d, L_P - d)
    return d.argmin(1)


class BPNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.l1, self.l2 = nn.Linear(2 * W_SM + 1, H_BP), nn.Linear(H_BP, 1)

    def forward(self, x):
        return torch.tanh(self.l2(torch.tanh(self.l1(x))))[:, 0]


def cluster_dataset(rng, per_value, step=0.001):
    """The paper's dataset: eps on a grid of step 0.001 over the whole range, per_value bursts per value (AWGN);
    SNR from TRAIN_SNRS (the paper: 20 dB only)."""
    eps = np.arange(-MAX_CFO * L_P, MAX_CFO * L_P + step / 2, step)
    P_, F_ = [], []
    chunk = max(1, 4000 // per_value)
    for a in range(0, len(eps), chunk):
        e = np.repeat(eps[a:a + chunk], per_value)
        snr = rng.choice(np.asarray(TRAIN_SNRS), len(e))
        sym = qpsk(rng, (len(e), L_P + TAIL))
        f = e / L_P
        r, _ = transmit(sym, f, rng.uniform(0, 2 * np.pi, len(e)), snr, rng)
        P_.append(pdp(r[:, :L_P] * np.conj(sym[:, :L_P])))
        F_.append(f)
    return np.concatenate(P_), np.concatenate(F_)


def train_cluster(device, per_value, epochs, log):
    t0 = time.time()
    rng = np.random.default_rng(TRAIN_SEED + 2_000_000)
    P, F = cluster_dataset(rng, per_value)
    log(f"cluster dataset {P.shape} in {time.time() - t0:.0f}s")
    # SSKC: K-means with the integer-CFO prior as seeds (semi-supervised clustering by seeding, Basu et al. 2002):
    # the PDP samples at (or, for the partial edge clusters +-4, nearest to) an integer CFO are labelled, initialise
    # their cluster's centre (the paper: "take their PDP samples as the initial clustering centers") and keep their
    # label in every Lloyd iteration; the unlabelled samples are assigned freely. (Unconstrained K-means let a centre
    # drift onto its neighbour's peak in the smoke test, which breaks the peak-position assignment of eq. 7.)
    eps = F * L_P
    seed = np.full(len(F), -1)
    for k, kv in enumerate(INT_CFO):
        sel = np.abs(eps - kv) < 0.1 if abs(kv) < K_CL // 2 else np.sign(kv) * eps > K_CL // 2 - 0.26
        seed[sel & (seed < 0)] = k
    Pt = torch.from_numpy(P).to(device)
    st = torch.from_numpy(seed).to(device)
    Ct = torch.stack([Pt[st == k].mean(0) for k in range(K_CL)])
    log(f"SSKC seeds per cluster {np.bincount(seed[seed >= 0], minlength=K_CL).tolist()}, initial centre peaks "
        f"{Ct.argmax(1).cpu().tolist()}")
    for it in range(50):
        a = torch.cdist(Pt, Ct).argmin(1)
        a = torch.where(st >= 0, st, a)
        newC = torch.stack([Pt[a == k].mean(0) if (a == k).any() else Ct[k] for k in range(K_CL)])
        moved = float((newC - Ct).abs().max())
        Ct = newC
        if moved < 1e-6:
            break
    a = torch.where(st >= 0, st, torch.cdist(Pt, Ct).argmin(1)).cpu().numpy()
    centres = Ct.cpu().numpy()
    centre_peaks = centres.argmax(1)
    log(f"K-means {it + 1} iterations, centre peaks {centre_peaks.tolist()} (bins of eps_I {INT_CFO.tolist()})")
    nets, hist = [], []
    for k in range(K_CL):
        i = np.where(a == k)[0]
        X = torch.from_numpy(sm_features(P[i], np.full(len(i), INT_CFO[k]))).to(device)
        y = torch.from_numpy((F[i] * L_P - INT_CFO[k]).astype(np.float32)).to(device)
        torch.manual_seed(k)
        net = BPNN().to(device)
        opt = torch.optim.Adam(net.parameters(), 1e-2)
        sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
        for ep in range(epochs):
            perm = torch.randperm(len(i), device=device)
            for b in range(0, len(i), 4096):
                j = perm[b:b + 4096]
                loss = torch.mean((net(X[j]) - y[j]) ** 2)
                opt.zero_grad()
                loss.backward()
                opt.step()
            sch.step()
        with torch.no_grad():
            mse = float(torch.mean((net(X) - y) ** 2))
        hist.append(dict(cluster=int(INT_CFO[k]), members=int(len(i)), train_mse_eps=mse))
        with open(path("logs", "train_cluster.progress"), "w") as fp:
            fp.write(f"{k + 1} {K_CL} {time.time() - t0:.0f}\n")
        log(f"  cluster eps_I={INT_CFO[k]:+d}: {len(i)} samples, train MSE {mse:.4f} (eps units)")
        nets.append({kk: v.cpu() for kk, v in net.state_dict().items()})
    torch.save({"centres": centres, "centre_peaks": centre_peaks, "nets": nets, "hist": hist,
                "samples": int(len(P)), "train_time_s": time.time() - t0, "train_snrs": TRAIN_SNRS,
                "params": K_CL * ((2 * W_SM + 1) * H_BP + H_BP + H_BP + 1)}, path("models", "cluster.pth"))


CLUSTER_MACS = 2 * L_P * 7 + 4 * L_P + 2 * L_P + L_P + K_CL + ((2 * W_SM + 1) * H_BP + H_BP) + 2 * 20   # FFT,
# z, |.|^2, max-normalise, peak search, cluster pick, BPNN (2 tanh ~ 20 each)


# =====================================================================
# Inference (CPU, used by run_est / run_bler)
# =====================================================================

NAMES = {"cluster": "Clustering NN (SSKC + SMDR-BPNN)", "cnn-cr": "CNN classification + refinement",
         "cnn-reg": "CNN direct regression"}
_models = {}


def load(kind):
    if kind not in _models:
        ck = torch.load(path("models", "cluster.pth" if kind == "cluster" else f"{kind}.pth"), map_location="cpu",
                        weights_only=False)
        if kind == "cluster":
            nets = []
            for sd in ck["nets"]:
                n_ = BPNN()
                n_.load_state_dict(sd)
                nets.append(n_.eval())
            _models[kind] = (ck, nets)
        else:
            m = CNN(kind)
            m.load_state_dict(ck["state_dict"])
            _models[kind] = (ck, m.eval())
    return _models[kind]


def estimate(kind, r, s):
    """CFO (B,) of a trained estimator from the preamble (no SNR, no channel knowledge)."""
    torch.set_num_threads(1)
    z = r * np.conj(s)
    ck, m = load(kind)
    with torch.no_grad():
        if kind == "cluster":
            p = pdp(z)
            k = cluster_online(p, ck["centre_peaks"])
            eps = np.empty(len(z))
            for c in np.unique(k):
                i = np.where(k == c)[0]
                eps[i] = INT_CFO[c] + m[c](torch.from_numpy(sm_features(p[i], np.full(len(i), INT_CFO[c])))).numpy()
            return np.clip(eps / L_P, -MAX_CFO, MAX_CFO)
        out = torch.cat([m(torch.from_numpy(nn_input(z[a:a + 2048]))) for a in range(0, len(z), 2048)]).numpy()
        return np.clip(cnn_decode(kind, out), -MAX_CFO, MAX_CFO)


def macs(kind):
    return CLUSTER_MACS if kind == "cluster" else cnn_macs(kind=kind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["train"])
    ap.add_argument("--what", nargs="+", default=["cluster", "cnn-cr", "cnn-reg"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--threads", type=int, default=0, help="torch threads of the training process (CPU)")
    ap.add_argument("--cluster-per-value", type=int, default=100)
    ap.add_argument("--cluster-epochs", type=int, default=30)
    a = ap.parse_args()
    if a.threads:
        torch.set_num_threads(a.threads)
    logf = open(path("logs", f"train_{'_'.join(a.what)}.log"), "a")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()
    log(f"device {a.device} ({torch.cuda.get_device_name(0) if a.device == 'cuda' else 'cpu'}), torch "
        f"{torch.__version__}, args {vars(a)}")
    for w in a.what:
        if w == "cluster":
            train_cluster(a.device, a.cluster_per_value, a.cluster_epochs, log)
        else:
            train_cnn(w, a.device, a.epochs, a.steps, a.batch, a.workers, log)
    log("TRAIN DONE")


if __name__ == "__main__":
    main()
