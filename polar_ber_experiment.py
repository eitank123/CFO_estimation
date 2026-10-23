"""
Coded BER / BLER with CFO estimation: polar code + CA-SCL, 512-symbol packet, FULL Tx/Rx chain.

Frame  : 512 QPSK symbols = one polar codeword (N = 1024 coded bits). Coded bits are interleaved with a fixed
         random permutation before QPSK mapping.
Codes  : R = 0.5 (512 data + CRC-11), R = 0.25 (256 data + CRC-11), R = 0.1 (102 + CRC-11). R = 0.1 is
         simulated over the same Es/N0 range as R = 0.25 (-5 .. 0 dB) and in the CFO-error sweep at
         Es/N0 = -5 / -4 dB, where the higher rates fail even without CFO error.
Channel: the full chain of main.py (txrx_chain.py): upsample x8 -> RRC (config.BETA) -> CFO ~ U[-0.2, 0.2]
         per sample, before the matched filter -> AWGN (Es/N0) -> matched RRC -> downsample. A large CFO
         therefore also costs matched-filter loss + ISI, for every receiver including the Genie.
Rx     : CFO estimate f_hat (per source, below) -> de-rotate; the phase reference is exact at the packet
         centre, so the residual phase is 2 pi (f - f_hat)(n - 255.5) -> LLRs -> de-interleave ->
         CA-SCL (L = 8).
Sources: Genie         f_hat = f (true CFO)
         SNR-aware NN  estimated on the first 128 received symbols, treated as known (a 128-symbol
         M&M           training sequence), same chain and noise as the data
         error mode    f_hat = f + eps, fixed |eps| in [0, 0.2], random sign

Axis   : Eb/N0 = energy per data bit (CRC counted as overhead): Es/N0 = Eb/N0 + 10 log10(A / 512)

Monte Carlo per point: batches until --min-errors frame errors or --max-frames frames. All sources of one
(code, Eb/N0) see the same data, CFO, phase and noise (common random numbers).

Usage:
    python polar_ber_experiment.py --mode ebn0        # -> polar_results_ebn0_chain.npy, polar_{ber,bler}_vs_ebn0.png
    python polar_ber_experiment.py --mode error       # -> polar_results_error_chain.npy, polar_{ber,bler}_vs_cfo_error_*.png
    python polar_ber_experiment.py --mode error --plot-only
    python polar_ber_experiment.py --mode ebn0 --packet 128   # 128-symbol packet (N = 256; A = 128 / 64 / 25),
                                                              # -> *_L128 files; the CFO is estimated on the whole packet
"""

import argparse
import paths
import multiprocessing as mp
import os
import re
import sys
import time
import zlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from polar import PolarCode

if "--packet" in sys.argv:        # read before the tables below; the environment carries it to spawned workers
    os.environ["POLAR_NSYM"] = sys.argv[sys.argv.index("--packet") + 1]
N_SYM = int(os.environ.get("POLAR_NSYM", "512"))   # packet length (symbols)
N_BITS = 2 * N_SYM
if "--est-len" in sys.argv:
    os.environ["POLAR_LEST"] = sys.argv[sys.argv.index("--est-len") + 1]
L_EST = int(os.environ.get("POLAR_LEST", "128"))  # symbols the estimators see (start of the packet, treated as known)
MAX_CFO = 0.2
LINE_SNR = -4.0                   # Es/N0 of the estimator-RMSE lines in the CFO-error plots
SUFFIX = "" if N_SYM == 512 else f"_L{N_SYM}"      # file names of other packet lengths

# name: (data bits A, CRC length, Eb/N0 grid for --mode ebn0, Eb/N0 points for --mode error)
# R=1/2 and R=1/4 (both packet lengths): Es/N0 -5 .. 10 dB in 0.25 dB steps (R=1/4: Es/N0 = Eb/N0 - 3.01 dB)
EBN0_R05 = list(np.arange(-5.0, 10.01, 0.25))
EBN0_R025 = list(np.arange(-2.0, 13.01, 0.25))
if N_SYM == 512:
    CODES = {
        "R=0.5": (512, 11, EBN0_R05, [1.5, 2.0, 2.5, 3.0]),
        "R=0.25": (256, 11, EBN0_R025, [0.5, 1.0, 1.5, 2.0]),
        "R=0.1": (102, 11, list(np.round(np.arange(0.0, 5.01, 0.25) + 2.0067, 4)),    # Es/N0 -5 .. 0 dB
                  [2.0067, 3.0067]),                                                   # Es/N0 = -5 and -4 dB
    }
    # Low-rate study (CFO_STUDY=lowrate): codes on an SNR (Es/N0) grid in 0.5 dB steps, A = round(R * 1024)
    for _name, _a, _lo, _hi in (("R=0.025", 26, -12, -2), ("R=0.05", 51, -11, -1), ("R=0.075", 77, -10, 0),
                                ("R=0.15", 154, -8, 2), ("R=0.2", 205, -7, 3), ("R=1/3", 341, -5, 5),
                                ("R=0.75", 768, 0, 10)):
        CODES[_name] = (_a, 11, list(np.round(np.arange(_lo, _hi + 0.01, 0.5) - 10 * np.log10(_a / 512), 4)), [])
    if os.environ.get("CFO_STUDY") == "lowrate":   # R=1/10 also below Es/N0 = -5 dB (its estimator curves start there)
        CODES["R=0.1"] = (102, 11, list(np.round(np.arange(-9.0, -5.1, 0.5) + 7.0067, 4)) + CODES["R=0.1"][2],
                          CODES["R=0.1"][3])
    # Longer CRCs at the same data rate (same A, K = A + C): "R=0.05,C16" etc., SNR -5 .. 0 dB
    for _name in ("R=0.025", "R=0.05", "R=0.075", "R=0.1"):
        for _c in (16, 24):
            _a = CODES[_name][0]
            CODES[f"{_name},C{_c}"] = (_a, _c, list(np.round(np.arange(-5, 0.01, 0.5) - 10 * np.log10(_a / 512), 4)), [])
elif N_SYM == 256:                # N = 512; CFO-error points ~0.5 dB above the 512-symbol ones (shorter code)
    CODES = {
        "R=0.5": (256, 11, EBN0_R05, [2.0, 2.5, 3.0, 3.5]),
        "R=0.25": (128, 11, EBN0_R025, [1.0, 1.5, 2.0, 2.5]),
    }
elif N_SYM == 128:                # N = 256
    CODES = {
        "R=0.5": (128, 11, EBN0_R05, []),
        "R=0.25": (64, 11, EBN0_R025, []),
        "R=0.1": (25, 11, list(np.round(np.arange(0.0, 6.51, 0.25) + 2.0927, 4)), []),  # Es/N0 -5 .. 1.5 dB
    }
elif N_SYM == 1024:               # N = 2048, low-rate study: same data rates, half the CRC share; SNR -6 .. 0 dB
    CODES = {}
    for _name, _a in (("R=0.025", 51), ("R=0.05", 102), ("R=0.075", 154), ("R=0.1", 205), ("R=0.15", 307)):
        for _c in (11, 16, 24):
            CODES[_name if _c == 11 else f"{_name},C{_c}"] = (
                _a, _c, list(np.round(np.arange(-6, 0.01, 0.5) - 10 * np.log10(_a / N_SYM), 4)), [])
    # adaptive-rate study: higher rates with CRC-16, each around the SNR region where it is the best rate
    for _name, _a, _lo, _hi in (("R=0.2", 410, -4.5, 0), ("R=1/4", 512, -3.5, 1.5), ("R=1/3", 683, -2.5, 4),
                                ("R=1/2", 1024, 0, 7.5), ("R=3/4", 1536, 3.5, 10)):
        CODES[f"{_name},C16"] = (_a, 16, list(np.round(np.arange(_lo, _hi + 0.01, 0.5) - 10 * np.log10(_a / N_SYM), 4)), [])
else:
    raise ValueError(f"no code table for a {N_SYM}-symbol packet")
ERRORS = np.concatenate([[0.0], np.logspace(-5, np.log10(0.2), 18)])
GENIE = "Genie (known CFO)"
ESTIMATORS = ["SNR-aware NN", "M&M"]
CRB_SRC = "CRB (ideal 128-symbol estimator)"   # f_hat = f + N(0, CRB): the bound for any estimator on L_EST symbols
SEARCH = "SNR-aware NN + CRC search"            # NN estimate, then a CRC-aided CFO search when its decode fails
DEFAULT_SOURCES = [GENIE] + ESTIMATORS
SEARCH_MM = "M&M + CRC search"                  # the same search around the M&M estimate
SEARCH_FIRST = "SNR-aware NN + CRC search (first pass)"   # nearest hypotheses first, stop at the first CRC pass
SEARCH_HALF = "SNR-aware NN + CRC search (M/2)"          # full search over half the grid width
V2 = "NN v2"                                     # ML + light correction MLP (train_cfo_v2.py, V2_NAME)
V2_NAME = "light32"
SEARCH_MM_FIRST = "M&M + CRC search (first pass)"
SEARCH_V2_FIRST = "NN v2 + CRC search (first pass)"
SEARCH_V2 = "NN v2 + CRC search"                  # full search around the NN v2 estimate
# Split pilots (train_cfo_v3.py): the same 128 known symbols as two 64-symbol blocks, "ends" (first / last 64 symbols)
# or "quarter" (centred at N/4 and 3N/4); split-pilot ML estimate; the CRC search covers +-J likelihood lobes x a fine
# grid around each, tried in order of the pilot likelihood
SPLIT_ENDS, SPLIT_QUARTER = "Split pilots, ends (ML)", "Split pilots, quarter (ML)"
SPLIT_NN = "Split pilots NN, quarter"     # train_cfo_split_nn.py model (1024 symbols: conv soft-argmax + lobe classifier)
SPLIT = {SPLIT_ENDS: "ends", SPLIT_QUARTER: "quarter", SPLIT_NN: "quarter"}
SEARCH_SPLIT_ENDS = SPLIT_ENDS + " + CRC search (first pass)"
SEARCH_SPLIT_QUARTER = SPLIT_QUARTER + " + CRC search (first pass)"
SEARCH_SPLIT_QUARTER_FULL = SPLIT_QUARTER + " + CRC search"          # full search over the same lobes x fine grid
SEARCH_SPLIT_NN = SPLIT_NN + " + CRC search (first pass)"             # the split ML's search, around the NN estimate
SEARCH_SPLIT_NN_FULL = SPLIT_NN + " + CRC search"                     # ... full search (every hypothesis, best metric)
FIRST_PASS = {SEARCH_FIRST, SEARCH_MM_FIRST, SEARCH_V2_FIRST, SEARCH_SPLIT_ENDS, SEARCH_SPLIT_QUARTER, SEARCH_SPLIT_NN}
SEARCH_BASE = {SEARCH: "SNR-aware NN", SEARCH_MM: "M&M", SEARCH_FIRST: "SNR-aware NN", SEARCH_HALF: "SNR-aware NN",
               SEARCH_MM_FIRST: "M&M", SEARCH_V2_FIRST: V2, SEARCH_V2: V2, SEARCH_SPLIT_ENDS: SPLIT_ENDS,
               SEARCH_SPLIT_QUARTER: SPLIT_QUARTER, SEARCH_SPLIT_QUARTER_FULL: SPLIT_QUARTER, SEARCH_SPLIT_NN: SPLIT_NN,
               SEARCH_SPLIT_NN_FULL: SPLIT_NN}
SOURCES = DEFAULT_SOURCES + [CRB_SRC, SEARCH, SEARCH_MM, SEARCH_FIRST, SEARCH_HALF, SEARCH_MM_FIRST, SEARCH_V2_FIRST,
                             SEARCH_V2, V2, SPLIT_ENDS, SPLIT_QUARTER, SEARCH_SPLIT_ENDS, SEARCH_SPLIT_QUARTER,
                             SEARCH_SPLIT_QUARTER_FULL, SPLIT_NN, SEARCH_SPLIT_NN, SEARCH_SPLIT_NN_FULL]
COLORS = {GENIE: "k", "SNR-aware NN": "#9467bd", "M&M": "#ff7f0e", CRB_SRC: "#7f7f7f", SEARCH: "#2ca02c",
          SEARCH_MM: "#d62728", SEARCH_FIRST: "#1f77b4", SEARCH_HALF: "#8c564b", SEARCH_MM_FIRST: "#d62728",
          SEARCH_V2_FIRST: "#2ca02c", SEARCH_V2: "#17becf", V2: "#8c564b", SPLIT_ENDS: "#e377c2",
          SPLIT_QUARTER: "#e377c2", SEARCH_SPLIT_ENDS: "#d62728", SEARCH_SPLIT_QUARTER: "#d62728",
          SEARCH_SPLIT_QUARTER_FULL: "#d62728", SPLIT_NN: "#17becf", SEARCH_SPLIT_NN: "#17becf",
          SEARCH_SPLIT_NN_FULL: "#17becf"}
MARKERS = {GENIE: "", "SNR-aware NN": "s", "M&M": "d", CRB_SRC: "", SEARCH: "^", SEARCH_MM: "v", SEARCH_FIRST: "o",
           SEARCH_HALF: "P", SEARCH_MM_FIRST: "v", SEARCH_V2_FIRST: "^", SEARCH_V2: "D", V2: "s", SPLIT_ENDS: "x",
           SPLIT_QUARTER: "x", SEARCH_SPLIT_ENDS: "*", SEARCH_SPLIT_QUARTER: "*",
           SEARCH_SPLIT_QUARTER_FULL: "P", SPLIT_NN: "X", SEARCH_SPLIT_NN: "h", SEARCH_SPLIT_NN_FULL: "H"}
# CFO grid step (cycles/symbol): 1.5e-4 for 512 symbols (residual <= 7.5e-5, below the code's tolerance); the tolerance
# scales with 1 / packet length (the phase drift 2 pi e n grows along the packet), so the step does too
SEARCH_STEP = 1.5e-4 * 512 / N_SYM
SEARCH_SIGMAS = 4.0           # grid half-width = SEARCH_SIGMAS * 1.3 * sqrt(CRB) (the NN is ~1.2x the CRB)


def crb_std(snr_db, n=None):
    """sqrt of the data-aided CFO CRB 3 / (2 pi^2 SNR L (L^2 - 1)) for L known symbols (cycles/symbol)."""
    n = n or L_EST
    return float(np.sqrt(3.0 / (2 * np.pi ** 2 * 10 ** (snr_db / 10) * n * (n ** 2 - 1))))


def search_m(snr_db, src=SEARCH):
    """Grid half-width M of the CRC search (hypotheses f_hat + k * SEARCH_STEP, 0 < |k| <= M); halved for SEARCH_HALF."""
    m = int(np.ceil(SEARCH_SIGMAS * 1.3 * crb_std(snr_db) / SEARCH_STEP))
    return max(1, int(np.ceil(m / 2))) if src == SEARCH_HALF else m


SPLIT_STEP = SEARCH_STEP * 2 / 3      # finer grid: the split-pilot estimate is 3.5-13x tighter than the contiguous one
SPLIT_LOBES = {("ends", 512): 2, ("ends", 1024): 3, ("quarter", 512): 1, ("quarter", 1024): 2}   # +-J lobes searched


_split_nn = None


def split_nn(zp, snr_db):
    """CFO estimate (B,) of the split-pilot NN (models/cfo_split_nn_L<N>.pth) from z = r s* at the quarter positions."""
    global _split_nn
    import torch
    if _split_nn is None:
        import train_cfo_split_nn
        _split_nn = _load_split_nn(train_cfo_split_nn)
    with torch.no_grad():
        return _split_nn(torch.from_numpy(zp), torch.full((len(zp),), float(snr_db), dtype=torch.float64))[0].numpy()


def _load_split_nn(mod):
    import torch
    ck = torch.load(paths.model(f"cfo_split_nn_L{N_SYM}.pth"), map_location="cpu", weights_only=False)
    m = mod.build(ck["config"])
    m.load_state_dict(ck["state_dict"])
    return m.eval()


def split_offsets(layout, snr_db):
    """Search offsets (T,) around the split-pilot estimate: lobes j / D (|j| <= J) x fine grid k * SPLIT_STEP
    (|k| <= M_f = ceil(4 * 1.06 * sqrt(CRB_split) / SPLIT_STEP)); (0, 0) first."""
    from train_cfo_v3 import crb_split, spacing
    m = int(np.ceil(SEARCH_SIGMAS * 1.06 * np.sqrt(crb_split(snr_db, N_SYM, layout)) / SPLIT_STEP))
    J = SPLIT_LOBES[(layout, N_SYM)]
    off = [j * spacing(N_SYM, layout) + k * SPLIT_STEP for j in range(-J, J + 1) for k in range(-m, m + 1)]
    return np.array(sorted(off, key=lambda o: abs(o) > 1e-15))
LINES = {"R=0.5": "-", "R=0.25": "--", "R=0.1": ":"}
NOT_PLOTTED = set() if paths.STUDY == "lowrate" else {"R=0.1"}   # main: results kept, no R=1/10 plots
LOWRATE = paths.STUDY == "lowrate"   # plots vs SNR (Es/N0), every rate, operating points
BLER_TARGET = 1e-2                   # operating points: highest rate with BLER below this
SNR_MIN = -5.0                       # low-rate study plots: SNR (Es/N0) from -5 dB up

SNR_AWARE_PATH = paths.model({128: "snr_aware_cfo_model_L64_chain150.pth",   # full chain, 40 + 150 epochs
                              256: "snr_aware_cfo_model_L128_est256.pth"}[L_EST])   # full chain, 256 symbols
RMSE_FILE = paths.result("cfo_rmse_chain.npz")
_snr_nn = _v2 = None


def esn0(code_name, ebn0_db):
    """Es/N0 of a QPSK symbol: N_SYM symbols carry A data bits, so Es = Eb * A / N_SYM."""
    return round(ebn0_db + 10 * np.log10(CODES[code_name][0] / N_SYM), 4)


def load_snr_nn(path=SNR_AWARE_PATH):
    global _snr_nn
    if _snr_nn is None:
        import torch
        from train_snr_nn import SNRAwareCFOEstimator
        ck = torch.load(path, map_location="cpu", weights_only=False)
        _snr_nn = SNRAwareCFOEstimator(max_lag=ck["config"]["max_lag"], hidden=tuple(ck["config"]["hidden"]),
                                       use_snr=ck["config"].get("use_snr", True))
        assert ck["config"]["max_lag"] == L_EST // 2, (path, ck["config"]["max_lag"], L_EST)
        _snr_nn.load_state_dict(ck["state_dict"])
        _snr_nn.eval()
    return _snr_nn


def estimate(src, z, snr_db):
    """CFO estimate (cycles/symbol, (B,)) of an estimator from z = r s* of the known symbols."""
    import torch
    from train_snr_nn import lag_features, mm_estimate
    torch.set_num_threads(1)
    with torch.no_grad():
        if src == V2:
            from train_cfo_v2 import features, load_v2
            global _v2
            if _v2 is None:
                _v2 = load_v2(V2_NAME)
            f = _v2(features(torch.from_numpy(z), np.full(len(z), float(snr_db))))[:, None]
            return f.double().numpy()[:, 0] * MAX_CFO
        feats, R = lag_features(torch.from_numpy(z))
        if src == "M&M":
            f = mm_estimate(R)
        else:
            f = load_snr_nn()(feats, torch.full((len(z),), float(snr_db)))
    return f.double().numpy()[:, 0] * MAX_CFO


# =====================================================================
# Monte Carlo
# =====================================================================

def simulate_point(task):
    """One point. src is a float (fixed |eps|, random sign), GENIE, an estimator name, or a tuple of those: then all
    the sources are simulated on the SAME frames (one Tx/Rx chain per batch, shared), each with its own stopping rule
    and statistics, and a list of results is returned. Every source of a point already uses the same seed, so a
    shared run gives exactly the results of the separate runs, with the chain computed once."""
    code_name, ebn0_db, src_arg, list_size, batch, min_errors, max_frames, seed, task_id, progress_file = task
    srcs = list(src_arg) if isinstance(src_arg, tuple) else [src_arg]
    from txrx_chain import DELAY_SYM, transmit
    A, C = CODES[code_name][:2]
    snr_db = esn0(code_name, ebn0_db)
    code = PolarCode(N_BITS, A, C, list_size)
    rng = np.random.default_rng(seed)                     # data, CFO, phase, noise: identical for every source
    rng_es = {s: np.random.default_rng(seed + 1) for s in srcs}   # sign of the fixed CFO error, per source
    interleaver = np.random.default_rng(12345).permutation(N_BITS)    # fixed, shared by Tx and Rx
    sigma2 = 1.0 / (2.0 * 10 ** (snr_db / 10))                         # noise variance per real dimension
    n = np.arange(N_SYM)
    centre = (N_SYM - 1) / 2

    stats = {s: dict(frames=0, frame_err=0, bit_err=0, raw_err=0, searched=0, undetected=0, se_first=0.0,
                     se_final=0.0) for s in srcs}
    running = lambda s: stats[s]["frame_err"] < min_errors and stats[s]["frames"] < max_frames
    while any(running(s) for s in srcs):
        data = rng.integers(0, 2, (batch, A), dtype=np.uint8)
        cw = code.encode(data)[:, interleaver]
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        f = rng.uniform(-MAX_CFO, MAX_CFO, batch)
        ph = rng.uniform(0, 2 * np.pi, batch)
        r = transmit(sym, f, ph, snr_db, rng)             # full Tx/Rx chain, shared by every source
        for src in srcs:
            if running(src):
                _receive(src, stats[src], rng_es[src], code, data, cw, sym, f, ph, r, snr_db, sigma2, interleaver,
                         n, centre, batch)
        done = min(min(1.0, max(stats[s]["frame_err"] / min_errors, stats[s]["frames"] / max_frames)) for s in srcs)
        with open(progress_file, "a") as fp:     # per-batch progress, read by job_progress.py
            fp.write(f"{task_id} {done:.4f}\n")

    out =[{"code": code_name, "ebn0": ebn0_db, "esn0": snr_db, "src": s, "frames": st["frames"],
            "frame_err": st["frame_err"], "ber": st["bit_err"] / (st["frames"] * A), "bler": st["frame_err"] / st["frames"],
            "raw_ber": st["raw_err"] / (st["frames"] * N_BITS), "extra_decodes_per_frame": st["searched"] / st["frames"],
            "undetected_bler": st["undetected"] / st["frames"], "rmse_cfo_first": np.sqrt(st["se_first"] / st["frames"]),
            "rmse_cfo_final": np.sqrt(st["se_final"] / st["frames"])} for s, st in stats.items()]
    return out if isinstance(src_arg, tuple) else out[0]


def _receive(src, st, rng_e, code, data, cw, sym, f, ph, r, snr_db, sigma2, interleaver, n, centre, batch):
    """Receiver `src` on one batch of frames (estimate, de-rotate, decode, CRC search); accumulates into st."""
    from txrx_chain import DELAY_SYM
    if True:                                              # (the body of the former per-source loop)
        if src == GENIE:
            f_hat = f
        elif src == CRB_SRC:
            f_hat = f + crb_std(snr_db) * rng_e.standard_normal(batch)
        elif SEARCH_BASE.get(src, src) in SPLIT:
            from train_cfo_v3 import positions, split_ml
            layout = SPLIT[SEARCH_BASE.get(src, src)]
            kp = positions(N_SYM, layout)
            zp = r[:, kp] * np.conj(sym[:, kp])
            if SEARCH_BASE.get(src, src) == SPLIT_NN:
                f_hat = split_nn(zp, snr_db)
            else:
                f_hat = split_ml(zp, N_SYM, layout)[0].numpy()
        elif isinstance(src, str):
            nn = SEARCH_BASE.get(src, src)
            f_hat = estimate(nn, r[:, :L_EST] * np.conj(sym[:, :L_EST]), snr_db)
        else:
            f_hat = f + src * rng_e.choice([-1.0, 1.0], batch)

        def llrs(fh, idx):
            """De-interleaved LLRs of frames idx de-rotated by fh; the phase of r[n] is 2 pi f (n + DELAY_SYM) + ph,
            the reference is exact at the packet centre."""
            rot = (2 * np.pi * fh[:, None] * (n + DELAY_SYM)
                   + (ph[idx] + 2 * np.pi * (f[idx] - fh) * (centre + DELAY_SYM))[:, None])
            y = r[idx] * np.exp(-1j * rot)
            llr = np.empty((len(idx), N_BITS))
            llr[:, 0::2] = np.sqrt(2) * y.real / sigma2
            llr[:, 1::2] = np.sqrt(2) * y.imag / sigma2
            deint = np.empty_like(llr)
            deint[:, interleaver] = llr
            return llr, deint

        allf = np.arange(batch)
        llr, deint = llrs(f_hat, allf)
        st["raw_err"] += int(np.sum((llr < 0) != cw))
        dec, ok, pm = code.decode(deint, return_info=True)
        f_final = f_hat.copy()                            # the CFO the delivered decode used
        if src in SEARCH_BASE and not ok.all():
            # CRC-aided CFO search: frames whose CRC failed are decoded on a grid around the NN estimate; the
            # hypothesis that passes the CRC with the best path metric wins (none passes: the first decode stays)
            bad = np.where(~ok)[0]
            best_pm = np.full(len(bad), np.inf)
            first = src in FIRST_PASS            # nearest first (+-1, +-2, ...), a frame stops at its first CRC pass
            if SEARCH_BASE[src] in SPLIT:        # split pilots: lobes x fine grid, in order of the pilot likelihood
                import torch
                from train_cfo_v3 import likelihood
                o = split_offsets(SPLIT[SEARCH_BASE[src]], snr_db)[1:]
                hyp = f_hat[bad][:, None] + o
                nc = torch.as_tensor(kp - (N_SYM - 1) / 2.0, dtype=torch.float64)
                lik = likelihood(torch.from_numpy(zp[bad]), nc, torch.from_numpy(hyp)).abs().numpy()
                off = np.take_along_axis(np.broadcast_to(o, hyp.shape), np.argsort(-lik, 1), 1)
            else:                                # contiguous pilots: the same grid k * SEARCH_STEP for every frame
                m = search_m(snr_db, src)
                ks = [k for k in range(-m, m + 1) if k]
                ks = sorted(ks, key=lambda k: (abs(k), k)) if first else ks
                off = np.broadcast_to(np.array(ks, float) * SEARCH_STEP, (len(bad), len(ks)))
            active = np.ones(len(bad), bool)
            for t in range(off.shape[1]):
                idx = np.where(active)[0]
                if not len(idx):
                    break
                fh = f_hat[bad[idx]] + off[idx, t]
                d_k, ok_k, pm_k = code.decode(llrs(fh, bad[idx])[1], return_info=True)
                st["searched"] += len(idx)
                win = ok_k & (pm_k < best_pm[idx])
                w = idx[win]
                dec[bad[w]], best_pm[w] = d_k[win], pm_k[win]
                f_final[bad[w]] = fh[win]
                if first:
                    active[w] = False
        errs = dec != data
        crc_ok = ok.copy()
        if src in SEARCH_BASE and len(bad := np.where(~ok)[0]):
            crc_ok[bad] = np.isfinite(best_pm)
        st["undetected"] += int((errs.any(1) & crc_ok).sum())  # delivered with a passing CRC but wrong
        st["se_first"] += float(np.sum((f_hat - f) ** 2))
        st["se_final"] += float(np.sum((f_final - f) ** 2))
        st["bit_err"] += int(errs.sum())
        st["frame_err"] += int(errs.any(1).sum())
        st["frames"] += batch


def pool_points(a, b, tag):
    """Point a with the extra frames of point b (same code, SNR and source, independent seed) added in."""
    if tag in a.get("added", []):
        return a
    fa, fb = a["frames"], b["frames"]
    out = {**a, "frames": fa + fb, "frame_err": a["frame_err"] + b["frame_err"], "added": a.get("added", []) + [tag]}
    for f in ("ber", "bler", "raw_ber", "extra_decodes_per_frame", "undetected_bler"):
        if a.get(f) is not None and b.get(f) is not None:
            out[f] = (a[f] * fa + b[f] * fb) / (fa + fb)
    for f in ("rmse_cfo_first", "rmse_cfo_final"):
        if a.get(f) is not None and b.get(f) is not None:
            out[f] = float(np.sqrt((a[f] ** 2 * fa + b[f] ** 2 * fb) / (fa + fb)))
    return out


def run(args):
    tasks = []
    for name in args.codes:
        _, _, grid, err_points = CODES[name]
        points = grid if args.mode == "ebn0" else err_points
        if args.extra_esn0:                     # SNR points off the code's grid (e.g. finer steps near a threshold)
            points = [round(e - 10 * np.log10(CODES[name][0] / N_SYM), 4) for e in args.extra_esn0]
        if args.snr_min is not None:            # SNR (Es/N0) from snr_min up
            points = [e for e in points if esn0(name, e) >= args.snr_min - 1e-6]
        if args.snr_max is not None:            # ... up to snr_max (a split run: one SNR range per job)
            points = [e for e in points if esn0(name, e) <= args.snr_max + 1e-6]
        sources = args.sources if args.mode == "ebn0" else [float(e) for e in (args.errors or ERRORS)]
        for ebn0 in points:
            seed = zlib.crc32(repr((name, round(float(ebn0), 3), args.seed)).encode())
            todo = [src for src in sources if (name, round(float(ebn0), 3), src) not in args.skip]  # --missing-only
            groups = [tuple(todo)] if args.shared_frames and args.mode == "ebn0" and len(todo) > 1 else todo
            for src in groups:
                tasks.append((name, float(ebn0), src, args.list_size, args.batch, args.min_errors,
                              args.max_frames, seed, len(tasks), args.progress_file))
    # Expensive points (low error rate: high Eb/N0, small eps) first so the pool stays busy
    tasks.sort(key=lambda t: (isinstance(t[2], float) and t[2] > 1e-3, -t[1]))
    with open(args.progress_file, "w") as fp:
        fp.write(f"start {time.time():.0f} tasks {len(tasks)}\n")
    t0 = time.time()
    results = []
    with mp.Pool(args.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(simulate_point, tasks), 1):
            results.extend(r if isinstance(r, list) else [r])
            print(f"{i}/{len(tasks)} points | {time.time() - t0:.0f}s", flush=True)
    return results


# =====================================================================
# Report / plots
# =====================================================================

SHORT = {"R=0.5": "R=1/2", "R=0.25": "R=1/4", "R=0.1": "R=1/10", "R=1/3": "R=1/3", "R=0.75": "R=3/4"}


def short(name):
    return SHORT.get(name, name)


def rate(name):
    return CODES[name][0] / N_BITS


def codes_in(results):
    return [n for n in CODES if any(r["code"] == n for r in results)]


def report_ebn0(results, list_size):
    for name in codes_in(results):
        rs = [r for r in results if r["code"] == name]
        get = {(r["ebn0"], r["src"]): r for r in rs}
        srcs = [s for s in SOURCES if any(r["src"] == s for r in rs)]
        print("\n" + "=" * 110)
        print(f"Polar {name} (N={N_BITS}, A={CODES[name][0]}, CRC-{CODES[name][1]}), CA-SCL L={list_size}, full chain")
        print("=" * 110)
        print(f"{'Eb/N0':>5} {'Es/N0':>6} | " + " | ".join(f"{s[:21]:>21}" for s in srcs) + " | frames")
        print(f"{'':>12} | " + " | ".join(f"{'BER':>10} {'BLER':>10}" for _ in srcs))
        for eb in sorted({r["ebn0"] for r in rs}):
            cells = [f"{get[(eb, s)]['ber']:10.3e} {get[(eb, s)]['bler']:10.3e}" for s in srcs]
            print(f"{eb:5.2f} {esn0(name, eb):6.2f} | " + " | ".join(cells) + f" | {get[(eb, srcs[0])]['frames']}")


def informative_range(results, codes, metric, flat=0.98):
    """
    Eb/N0 axis limits without the repetitive ends: start at the last point where every curve is still ~1
    (BLER >= 0.98, or the BER equivalent: within 2 % of that curve's first value), end at the first point after
    which no curve has any error. Both rounded outward to whole dB.
    """
    rs = [r for r in results if r["code"] in codes]
    ebs = sorted({r["ebn0"] for r in rs})
    curves = {}
    for r in rs:
        curves.setdefault((r["code"], r["src"]), {})[r["ebn0"]] = r[metric]
    def all_flat(e):
        return all(c.get(e, 1.0) >= flat * max(c.values()) for c in curves.values() if min(c) <= e)
    def all_zero(e):
        return all(c.get(e, 0.0) == 0 for c in curves.values())
    lo = next((ebs[i] for i in range(len(ebs)) if not all_flat(ebs[i])), ebs[0])
    lo = ebs[max(ebs.index(lo) - 1, 0)]                         # keep the last flat point
    hi = next((e for e in ebs if all(all_zero(x) for x in ebs if x >= e)), ebs[-1])
    return np.floor(lo), np.ceil(hi)


def plot_ebn0(results):
    """
    BER: all rates in one figure (colour = CFO source, line style = rate, top axis = Es/N0 of R=1/4).
    BLER: one figure per rate (polar_bler_vs_ebn0_R0p5.png, ...), top axis = Es/N0 of that rate.
    """
    from matplotlib.lines import Line2D
    shown = [c for c in codes_in(results) if c in LINES and c not in NOT_PLOTTED]
    figures = [("ber", "BER", shown, "R=0.25", "")]
    figures += [("bler", "BLER", [c], c, "_" + c.replace("=", "").replace(".", "p")) for c in shown]
    for metric, ylabel, codes, top_code, tag in figures:
        shift = esn0(top_code, 0.0)                              # Es/N0 - Eb/N0 of the top-axis code
        fig, ax = plt.subplots(figsize=(11, 6.5))
        for name in codes:
            rs = [r for r in results if r["code"] == name]
            for src in SOURCES:
                pts = sorted((r["ebn0"], r[metric]) for r in rs if r["src"] == src)
                if not pts:
                    continue
                x, y = np.array(pts).T
                ax.semilogy(x, np.where(y > 0, y, np.nan), LINES[name] if len(codes) > 1 else "-",
                            color=COLORS[src], marker=MARKERS[src], markersize=5,
                            linewidth=2 if src == GENIE else 1.3)
        src_handles = [Line2D([], [], color=COLORS[s], marker=MARKERS[s], label=s) for s in SOURCES]
        leg = ax.legend(handles=src_handles, loc="lower left", fontsize=9)
        if len(codes) > 1:
            ax.add_artist(leg)
            ax.legend(handles=[Line2D([], [], color="k", linestyle=LINES[n], label=SHORT[n]) for n in codes],
                      loc="lower center", fontsize=9)
        ax.set_ylim(top=3)
        ax.set_xlim(*informative_range(results, codes, metric, flat=0.98 if metric == "bler" else 0.9))
        ax.set_xlabel("Eb/N0 [dB]   (R=1/2: Es/N0 = Eb/N0)" if len(codes) > 1 else "Eb/N0 [dB]")
        ax.set_ylabel(ylabel)
        top = ax.secondary_xaxis("top", functions=(lambda e, s=shift: e + s, lambda v, s=shift: v - s))
        top.set_xlabel(f"Es/N0 [dB] for {SHORT[top_code]}" if len(codes) > 1 else "SNR (Es/N0) [dB]")
        title = f"{ylabel} vs. Eb/N0" + (f", {SHORT[codes[0]]}" if len(codes) == 1 else "")
        ax.set_title(title + (f", L={N_SYM}" if SUFFIX else "") + (f", CFO from {L_EST} symbols" if L_EST != 128 else ""),
                     pad=10)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        fig.tight_layout()
        fig.savefig(paths.plot(f"polar_{metric}_vs_ebn0{tag}{SUFFIX}.png"), dpi=300, bbox_inches="tight")
        plt.close(fig)


def bler_curve(results, name, src):
    """(SNR, BLER, frames) of one code and CFO source, sorted by SNR."""
    pts = sorted((r["esn0"], r["bler"], r["frames"]) for r in results
                 if r["code"] == name and r["src"] == src and r["esn0"] >= SNR_MIN - 1e-6)
    return [np.array(v, dtype=float) for v in zip(*pts)] if pts else (np.array([]),) * 3


def required_snr(snr, bler, target=BLER_TARGET):
    """SNR where a BLER curve first falls below `target` and stays there (log-linear interpolation); None if never."""
    below = bler < target
    if not below.any() or not below[-1]:
        return None
    i = len(below) - np.argmax(~below[::-1]) if (~below).any() else 0   # first index of the final run below target
    if i == 0:
        return float(snr[0])
    b0, b1 = bler[i - 1], max(bler[i], 1e-12)
    f = (np.log10(b0) - np.log10(target)) / (np.log10(b0) - np.log10(b1))
    return float(snr[i - 1] + f * (snr[i] - snr[i - 1]))


def plot_snr(results):
    """Low-rate study: BLER vs SNR (Es/N0), one figure per CFO source with every rate, and the operating points
    (highest rate with BLER < BLER_TARGET at each SNR) per source; tables printed for the README."""
    codes = sorted(codes_in(results), key=rate)
    # BLER figures: at most two rates each, receivers M&M, M&M + CRC search, NN + CRC search (plot_search_compare)
    if N_SYM == 512 and all(n in CODES for n in BLER_FIG_CODES):
        plot_search_compare(results, BLER_FIG_CODES, "polar_bler_vs_snr_R0p1.png", x_max=0.0)
    if N_SYM == 512 and "R=0.1,C16" in CODES:     # the same code with CRC-16
        plot_search_compare(results, ("R=0.1,C16",), "polar_bler_vs_snr_R0p1_C16.png", x_max=0.0)
    if N_SYM == 1024 and "R=0.1,C16" in CODES:    # the best option: 1024 symbols, R = 0.1, CRC-16
        plot_search_compare(results, ("R=0.1,C16",), "polar_bler_vs_snr_best_option_L1024.png", x_max=0.0)
    for name in ("R=0.1", "R=0.1,C16"):        # split pilots vs the contiguous pilots (bler/)
        if name in CODES and (N_SYM == 512 or name.endswith("C16")):
            plot_split_compare(results, name)
    for name, lo in (("R=1/4,C16", 0.0), ("R=1/3,C16", 0.0), ("R=1/2,C16", 2.0)):   # R = 1/4: the highest rate
        if N_SYM == 1024 and name in CODES:                                       # with BLER < 1e-2 at 0 dB
            plot_split_compare(results, name, xlim=(lo, 10.0))
    for name in ("R=0.1", "R=0.1,C16"):        # NN v2: full search vs first pass (bler/)
        if name in CODES and (N_SYM == 512 or name.endswith("C16")):
            plot_full_vs_first(results, name)
    if N_SYM == 512 and all(n in CODES for n in SEARCH_FIG_CODES):  # compute vs SNR (complexity/)
        plot_complexity(results)
    if N_SYM == 1024 and "R=0.1,C16" in CODES:
        plot_complexity(results, "R=0.1,C16", "polar_complexity_vs_snr_best_option_L1024.png")
    # BLER at SNR = -4 dB per rate, and the operating points
    print("\nBLER at SNR = -4 dB:")
    for name in codes:
        cells = []
        for src in SOURCES:
            x, y, n = bler_curve(results, name, src)
            k = np.where(np.isclose(x, -4, atol=0.02))[0]
            cells.append(f"{src[:12]} {y[k[0]]:.2e} ({int(n[k[0]])})" if len(k) else f"{src[:12]} -")
        print(f"  {short(name):8s} " + " | ".join(cells))
    fig, ax = plt.subplots(figsize=(11, 6.5))
    print(f"\nRequired SNR for BLER < {BLER_TARGET:g}:")
    req = {src: {} for src in SOURCES}
    for src in SOURCES:
        for name in codes:
            x, y, _ = bler_curve(results, name, src)
            if len(x):
                req[src][name] = required_snr(x, y)
        print(f"  {src}: " + ", ".join(f"{short(n)} {v:.2f}" if v is not None else f"{short(n)} -"
                                        for n, v in req[src].items()))
        pts = sorted((v, rate(n)) for n, v in req[src].items() if v is not None)
        best, stair = 0.0, []
        for v, r in pts:            # achievable rate = best rate whose required SNR is below the SNR
            if r > best:
                best = r
                stair.append((v, r))
        if stair:
            sx = [p[0] for p in stair] + [12]
            sy = [p[1] for p in stair] + [stair[-1][1]]
            ax.step(sx, sy, where="post", color=COLORS[src], lw=2.2, label=src)
            ax.plot([p[0] for p in stair], [p[1] for p in stair], MARKERS[src] or "o", color=COLORS[src], ms=7)
    ax.axvline(-4, color="0.5", ls=":", lw=1.2)
    ax.set_xlim(SNR_MIN - 0.25, 10)
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("Highest code rate R (data bits / coded bit)")
    ax.set_title(f"Operating points: highest rate with BLER < {BLER_TARGET:g}", pad=10)
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(paths.plot("polar_bler_operating_points.png"), dpi=300)
    plt.close(fig)


SEARCH_FIG_CODES = ("R=0.1",)
BLER_FIG_CODES = ("R=0.1",)   # the rate of polar_bler_vs_snr_R0p1.png


def plot_search_compare(results, codes=SEARCH_FIG_CODES, fname=None, x_max=None):
    """BLER vs SNR of M&M, M&M + CRC search and NN + CRC search at `codes` (colour = receiver, line style = rate when
    there are several); title "BLER vs SNR", subtitle packet length, rate and CRC length."""
    from matplotlib.lines import Line2D
    style = {"M&M": "-.", SEARCH_MM_FIRST: "--", SEARCH_V2_FIRST: "-", SEARCH_SPLIT_QUARTER: "-"}   # first pass only
    rate_ls = dict(zip(codes, ("-", "--", ":")))
    fig, ax = plt.subplots(figsize=(11, 6.5))
    x_last = SNR_MIN
    for name in codes:
        for src, ls in style.items():
            x, y, _ = bler_curve(results, name, src)
            on_grid = np.isclose(x * 2, np.round(x * 2))          # the common 0.5 dB grid of every receiver
            x, y = x[on_grid], y[on_grid]
            if len(x):
                ax.semilogy(x, np.where(y > 0, y, np.nan), ls=ls if len(codes) == 1 else rate_ls[name],
                            color=PLOT_COLORS.get(src, COLORS[src]), lw=2.2, marker=MARKERS[src], markersize=5)
                if (y > 0).any():
                    x_last = max(x_last, x[y > 0].max())
    handles = [Line2D([], [], color=PLOT_COLORS.get(s, COLORS[s]), lw=2.2, ls=ls if len(codes) == 1 else "-",
                      marker=MARKERS[s], label=LABELS.get(s, s)) for s, ls in style.items()
               if any(r["code"] in codes and r["src"] == s for r in results)]
    if len(codes) > 1:
        handles += [Line2D([], [], color="0.3", ls=rate_ls[n], label=short(n.split(",")[0])) for n in codes]
    ax.legend(handles=handles, fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    ax.set_xlim(SNR_MIN - 0.25, (x_max if x_max is not None else x_last + 0.5) + (0.25 if x_max is not None else 0))
    ax.set_ylim(top=1.5)
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("BLER")
    sub = "; ".join(f"{N_SYM}-symbol packet, R = {short(n.split(',')[0]).replace('R=', '')}, CRC-{CODES[n][1]} "
                    f"({CODES[n][0]} data bits)" for n in codes)
    fig.suptitle("BLER vs SNR", fontsize=15, fontweight="bold")
    ax.set_title(sub, fontsize=11, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(paths.plot(fname or f"polar_bler_vs_snr_crc_search{SUFFIX}.png"), dpi=300)
    plt.close(fig)


def plot_split_compare(results, name, xlim=None):
    """BLER vs SNR at code `name`: M&M (contiguous pilots, with and without the CRC search) against the split pilots
    (quarter layout) without the CRC search and with it (first pass and full search). xlim: SNR range [dB]
    (default SNR_MIN .. 0)."""
    split = ((SPLIT_QUARTER, SEARCH_SPLIT_QUARTER, "Split pilots: two 64-symbol blocks centred at N/4 and 3N/4"),)
    if not any(r["code"] == name and r["src"] in SPLIT for r in results):
        return
    fig, ax = plt.subplots(figsize=(11, 6.5))
    axes = [ax]
    for ax, (plain, srch, title) in zip(axes, split):
        rx = ((GENIE, "Genie (no CFO error)", "k", ":"),
              ("M&M", "M&M", "#ff7f0e", "-."),
              (SEARCH_MM_FIRST, "M&M + CRC search (first pass)", "#9467bd", "--"),
              (SEARCH_FIRST, "NN v1 + CRC search (first pass)", "#1f77b4", "--"),
              (SEARCH_V2_FIRST, "NN v2 + CRC search (first pass)", "#2ca02c", "-"),
              (plain, "Split pilots (no CRC search)", "#e377c2", ":"),
              (srch, "Split pilots + CRC search (first pass)", "#d62728", "-"),
              (SPLIT_NN, "Split pilots NN (no CRC search)", "#17becf", ":"),
              (SEARCH_SPLIT_NN, "Split pilots NN + CRC search (first pass)", "#17becf", "-"),
              (SEARCH_SPLIT_NN_FULL, "Split pilots NN + CRC search (full search)", "#17becf", (0, (6, 2))),
              (SEARCH_SPLIT_QUARTER_FULL, "Split pilots + CRC search (full search)", "#d62728", (0, (6, 2))))
        if any(r["code"] == name and r["src"] == SPLIT_NN for r in results):    # with the split NN (1024): only it,
            drop = {SEARCH_FIRST, SEARCH_V2_FIRST, plain, srch, SEARCH_SPLIT_QUARTER_FULL}   # the genie and M&M
            rx = tuple(r for r in rx if r[0] not in drop)
        for src, label, c, ls in rx:
            x, y, _ = bler_curve(results, name, src)
            on = np.isclose(x * 2, np.round(x * 2))
            x, y = x[on], y[on]
            if (y > 0).sum() >= 2:              # a curve with errors at fewer than 2 SNRs is not drawn
                ax.semilogy(x, np.where(y > 0, y, np.nan), ls=ls, color=c, lw=2.2, marker=MARKERS.get(src, "o"),
                            markersize=5, label=label)
        ax.set_xlabel("SNR (Es/N0) [dB]")
        lo, hi = xlim or (SNR_MIN, 0.0)
        ax.set_xlim(lo - 0.25, hi + 0.25)
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        ax.legend(fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    axes[0].set_ylabel("BLER")
    axes[0].set_ylim(top=1.5)
    fig.suptitle("BLER vs SNR", fontsize=15, fontweight="bold")
    axes[0].set_title(f"{N_SYM}-symbol packet, R = {short(name.split(',')[0]).replace('R=', '')}, "
                      f"CRC-{CODES[name][1]} ({CODES[name][0]} data bits); 128 known symbols in every receiver",
                      fontsize=11, color="0.3")
    fig.tight_layout()
    tag = name.replace("R=0.1", "R0p1").replace("R=", "R").replace("/", "_").replace(",", "_")
    fig.savefig(paths.plot(f"polar_bler_vs_snr_split_pilots_{tag}{SUFFIX}.png"), dpi=300)
    plt.close(fig)


def plot_full_vs_first(results, name):
    """CRC search, full search against first pass, for M&M and the split-pilot NN at code `name`: average CA-SCL
    decodes per packet vs SNR (the BLERs are in plot_split_compare). Colour = estimator, line style = search (dashed
    full, solid first pass). Drawn only where the split NN's full search was simulated (1024 symbols)."""
    rx = ((SEARCH_MM, "M&M + CRC search (full search)", "#9467bd", "--", "s"),
          (SEARCH_MM_FIRST, "M&M + CRC search (first pass)", "#9467bd", "-", "v"),
          (SEARCH_SPLIT_NN_FULL, "Split pilots NN + CRC search (full search)", "#17becf", "--", "h"),
          (SEARCH_SPLIT_NN, "Split pilots NN + CRC search (first pass)", "#17becf", "-", "h"))
    if not any(r["code"] == name and r["src"] == SEARCH_SPLIT_NN_FULL for r in results):
        return
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for src, label, c, ls, mk in rx:
        pts = sorted((r["esn0"], 1 + (r.get("extra_decodes_per_frame") or 0.0)) for r in results
                     if r["code"] == name and r["src"] == src and r["esn0"] >= SNR_MIN - 1e-6 and r["esn0"] <= 1e-6
                     and np.isclose(r["esn0"] * 2, round(r["esn0"] * 2)))
        if not pts:
            continue
        x, dec = (np.array(v, dtype=float) for v in zip(*pts))
        ax.plot(x, dec, ls=ls, color=c, marker=mk, markersize=5, lw=2.2, label=label,
                markerfacecolor="none" if ls == "--" else c)
    ax.set_ylabel("Average CA-SCL decodes per packet")
    ax.set_ylim(bottom=0)
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_xlim(SNR_MIN - 0.25, 0.25)
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
    fig.suptitle("CRC search: full search vs first pass", fontsize=15, fontweight="bold")
    ax.set_title(f"{N_SYM}-symbol packet, R = {short(name.split(',')[0]).replace('R=', '')}, "
                 f"CRC-{CODES[name][1]} ({CODES[name][0]} data bits)", fontsize=11, color="0.3")
    fig.tight_layout()
    tag = name.replace("R=0.1", "R0p1").replace(",", "_")
    fig.savefig(paths.plot(f"polar_bler_vs_snr_full_vs_first_pass_{tag}{SUFFIX}.png"), dpi=300)
    plt.close(fig)


# Cost model of the complexity figure (real operations per packet, approximate): CA-SCL L = 8 on N = 1024 is
# L * N * log2(N) node operations; each search hypothesis also de-rotates the N_SYM symbols and recomputes the LLRs.
# NN v2: M&M lags (its input) 24,704 + FFT-256 ~10,240 + 2 Newton steps ~4,000 + MLP 880 MACs ~ 40,000
# split-pilot ML: 2 FFT-256 ~20,500 + coarse Newton ~5,000 + 5 lobe candidates and likelihoods ~9,500 ~ 35,000
EST_MACS = {"M&M": 24_704, "SNR-aware NN": 67_616, V2: 40_000, SPLIT_QUARTER: 35_000,
            "Split pilots NN": 132_932}     # per estimate, README A.3 / A.15
LABELS = {SEARCH_MM_FIRST: "M&M + CRC search (first pass)", SEARCH_FIRST: "Previous NN + CRC search (first pass)",
          SEARCH: "Previous NN + CRC search (full search)", SEARCH_V2: "NN v2 + CRC search (full search)",
          SEARCH_SPLIT_QUARTER: "Split pilots (quarter) + CRC search (first pass)",
          SEARCH_SPLIT_QUARTER_FULL: "Split pilots (quarter) + CRC search (full search)",
          SEARCH_V2_FIRST: "NN v2 + CRC search (first pass)"}
PLOT_COLORS = {SEARCH_FIRST: "#9467bd", SEARCH: "#1f77b4", SEARCH_MM_FIRST: "#9467bd"}   # M&M + CRC: purple, the
#                                                                  split pilots red


def decode_ops():
    return 8 * N_BITS * int(np.log2(N_BITS))


def plot_complexity(results, name="R=0.1", fname=None):
    """Average compute per packet vs SNR at code `name`: CA-SCL decodes (left) and estimated real operations
    (right) for the CRC-search receivers."""
    rx = ((SEARCH_MM_FIRST, "M&M", "--"), (SEARCH_V2_FIRST, V2, "-"), (SEARCH_SPLIT_QUARTER, SPLIT_QUARTER, "-"))
    hyp_ops = decode_ops() + 6 * N_SYM + N_BITS          # decode + de-rotation (complex exp + multiply) + LLRs
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6))
    for src, est, ls in rx:
        pts = sorted((r["esn0"], r.get("extra_decodes_per_frame") or 0.0) for r in results
                     if r["code"] == name and r["src"] == src and r["esn0"] >= SNR_MIN - 1e-6
                     and np.isclose(r["esn0"] * 2, round(r["esn0"] * 2)))
        if not pts:
            continue
        x, extra = (np.array(v, dtype=float) for v in zip(*pts))
        ops = EST_MACS[est] + decode_ops() + 6 * N_SYM + N_BITS + extra * hyp_ops
        kw = dict(ls=ls, color=PLOT_COLORS.get(src, COLORS[src]), marker=MARKERS[src], markersize=5, lw=2.2,
                  label=LABELS.get(src, src))
        a1.plot(x, 1 + extra, **kw)
        a2.semilogy(x, ops, **kw)
    a1.set_ylabel("Average CA-SCL decodes per packet")
    a1.set_ylim(bottom=0)
    a2.set_ylabel("Estimated real operations per packet")
    for a, t in ((a1, "CA-SCL decodes"), (a2, "Real operations (estimator + decodes + de-rotations)")):
        a.set_xlabel("SNR (Es/N0) [dB]")
        a.set_title(t, fontsize=12)
        a.grid(True, which="both", linestyle=":", alpha=0.6)
        a.legend(fontsize=9.5)
    fig.suptitle(f"Average compute vs. SNR, {short(name)} ({N_SYM}-symbol packet, CA-SCL L = 8, N = {N_BITS})",
                 fontsize=14)
    fig.text(0.5, 0.005, f"One CA-SCL decode ≈ L·N·log2 N = {decode_ops():,} operations; "
             f"estimators: M&M {EST_MACS['M&M']:,}, NN v2 ~{EST_MACS[V2]:,}, "
             f"split-pilot ML ~{EST_MACS[SPLIT_QUARTER]:,}, split-pilot NN {EST_MACS['Split pilots NN']:,} "
             "real operations (no BLER run for the split NN). "
             "The search runs only when the first decode fails.", ha="center", fontsize=9, color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(paths.plot(fname or f"polar_complexity_vs_snr_crc_search{SUFFIX}.png"), dpi=300)
    plt.close(fig)


def plot_search_variants(results, name="R=0.1", fname=None):
    """The CRC-search variants at code `name`: BLER vs SNR (left) and CA-SCL decodes per packet, average (markers)
    vs SNR (right)."""
    rx = (("M&M", "-."), (SEARCH, "-"), (SEARCH_FIRST, "-"), (GENIE, ":"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6))
    x_last = SNR_MIN
    for src, ls in rx:
        x, y, _ = bler_curve(results, name, src)
        if not len(x):
            continue
        kw = dict(ls=ls, color=COLORS[src], marker=MARKERS[src] or None, markersize=5, lw=2.2)
        a1.semilogy(x, np.where(y > 0, y, np.nan), label=src, **kw)
        if (y > 0).any():
            x_last = max(x_last, x[y > 0].max())
        if src == GENIE:
            continue
        pts = sorted((r["esn0"], r.get("extra_decodes_per_frame") or 0.0) for r in results
                     if r["code"] == name and r["src"] == src and r["esn0"] >= SNR_MIN - 1e-6)
        xe, extra = (np.array(v, dtype=float) for v in zip(*pts))
        a2.semilogy(xe, 1 + extra, label=src, **kw)
    a1.set_ylabel("BLER")
    a1.set_ylim(top=1.5)
    a2.set_ylabel("CA-SCL decodes per packet")
    a1.set_xlim(SNR_MIN - 0.25, x_last + 0.5)
    a2.set_xlim(SNR_MIN - 0.25, x_last + 0.5)
    for a, t in ((a1, "BLER"), (a2, "Average CA-SCL decodes per packet")):
        a.set_xlabel("SNR (Es/N0) [dB]")
        a.set_title(t, fontsize=12)
        a.grid(True, which="both", linestyle=":", alpha=0.6)
        a.legend(fontsize=8.5, loc="lower left" if a is a1 else "center right")
    fig.suptitle(f"CRC-search variants, {short(name)} ({N_SYM}-symbol packet, step {SEARCH_STEP:.2e} cycles/symbol)",
                 fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(paths.plot(fname or f"polar_complexity_search_variants{SUFFIX}.png"), dpi=300)
    plt.close(fig)


def estimator_rmse(es_db=LINE_SNR, n=1000000, seed=7):
    """RMSE of M&M and the SNR-aware NN at Es/N0 = es_db on 128 known symbols, full chain (cached)."""
    key = f"{es_db:g}"
    if os.path.exists(RMSE_FILE):
        cache = dict(np.load(RMSE_FILE))
        if f"M&M@{key}" in cache and f"SNR-aware NN@{key}" in cache:
            return {s: float(cache[f"{s}@{key}"]) for s in ESTIMATORS}
    from txrx_chain import known_sequence
    rng = np.random.default_rng(seed)
    se = {s: 0.0 for s in ESTIMATORS}
    for _ in range(n // 10000):
        z, f = known_sequence(10000, L_EST, es_db, rng)
        for s in ESTIMATORS:
            se[s] += float(np.sum((estimate(s, z, es_db) - f) ** 2))
    out = {s: np.sqrt(se[s] / (n // 10000 * 10000)) for s in ESTIMATORS}
    cache = dict(np.load(RMSE_FILE)) if os.path.exists(RMSE_FILE) else {}
    cache.update({f"{s}@{key}": v for s, v in out.items()})
    np.savez(RMSE_FILE, **cache)
    return out


def report_error(results, list_size):
    for name in codes_in(results):
        rs = [r for r in results if r["code"] == name]
        print("\n" + "=" * 90)
        print(f"Polar {name}, CA-SCL L={list_size}: fixed CFO error (full chain)")
        print("=" * 90)
        for eb in sorted({r["ebn0"] for r in rs}):
            print(f"\nEb/N0 {eb:g} dB (Es/N0 {esn0(name, eb):g} dB)")
            print(f"  {'eps':>9} | {'coded BER':>10} | {'BLER':>10} | {'uncoded BER':>11} | {'frames':>8}")
            for r in sorted((r for r in rs if r["ebn0"] == eb), key=lambda r: r["src"]):
                print(f"  {r['src']:9.2e} | {r['ber']:10.3e} | {r['bler']:10.3e} | {r['raw_ber']:11.3e} | "
                      f"{r['frames']:8d}")


def plot_error(results):
    rmse = estimator_rmse() if os.path.exists(SNR_AWARE_PATH) else {}
    for name in [c for c in codes_in(results) if c not in NOT_PLOTTED]:
        rs = [r for r in results if r["code"] == name]
        ebs = sorted({r["ebn0"] for r in rs})
        colors = plt.cm.viridis(np.linspace(0, 0.9, len(ebs)))
        for metric, ylabel in (("ber", "BER"), ("bler", "BLER")):
            bits = 1 if metric == "bler" else CODES[name][0]
            plt.figure(figsize=(11, 6.5))
            for c, eb in zip(colors, ebs):
                pts = sorted((r for r in rs if r["ebn0"] == eb), key=lambda r: r["src"])
                eps = np.array([r["src"] for r in pts])
                y = np.array([r[metric] for r in pts])
                frames = np.array([r["frames"] for r in pts])
                x = np.where(eps > 0, eps, eps[eps > 0].min() / 3)   # eps = 0 at the left edge
                plt.loglog(x, np.where(y > 0, y, np.nan), "-o", color=c, markersize=3,
                           label=f"Eb/N0 = {eb:.1f} dB (SNR = {esn0(name, eb):.1f} dB)")
                zero = y == 0
                if zero.any():   # no errors observed: Monte-Carlo resolution as an upper bound (not in legend)
                    plt.loglog(x[zero], 1.0 / (frames[zero] * bits), "v", color=c, markerfacecolor="none")
            for s, lw in (("M&M", 2.0), ("SNR-aware NN", 2.0)):
                if s in rmse:
                    plt.axvline(rmse[s], color=COLORS[s], linestyle=":", linewidth=lw,
                                label=f"{s} RMSE at SNR = {LINE_SNR:g} dB ({rmse[s]:.1e})")
            plt.xlabel("CFO error (cycles/symbol)   [leftmost point = 0]")
            plt.ylabel(ylabel)
            plt.title(f"{ylabel} vs. CFO error, polar {SHORT[name]}, {N_SYM}-symbol packet")
            plt.grid(True, which="both", linestyle=":", alpha=0.6)
            plt.legend(fontsize=8, loc="lower right")
            plt.tight_layout()
            plt.savefig(paths.plot(f"polar_{metric}_vs_cfo_error_{name.replace('=', '').replace('.', 'p')}{SUFFIX}.png"),
                        dpi=300, bbox_inches="tight")
            plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["ebn0", "error"], default="ebn0")
    parser.add_argument("--list-size", type=int, default=8)
    parser.add_argument("--batch", type=int, default=500)
    parser.add_argument("--min-errors", type=int, default=300, help="frame errors per Monte Carlo point")
    parser.add_argument("--max-frames", type=int, default=30000)
    parser.add_argument("--workers", type=int, default=mp.cpu_count())
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--snr-min", type=float, default=None, help="simulate only SNR (Es/N0) >= this [dB]")
    parser.add_argument("--errors", type=float, nargs="+", default=None,
                        help="--mode error: the |CFO error| grid (cycles/symbol), instead of ERRORS")
    parser.add_argument("--extra-esn0", type=float, nargs="+", default=None,
                        help="simulate only these SNR (Es/N0) points [dB] instead of the code's grid")
    parser.add_argument("--snr-max", type=float, default=None, help="simulate only SNR (Es/N0) <= this [dB]")
    parser.add_argument("--plot-only", action="store_true", help="redraw plots from polar_results_<mode>_chain.npy")
    parser.add_argument("--est-len", type=int, choices=[128, 256], default=128,
                        help="known symbols the CFO estimators use (start of the packet); 256 uses the 128-lag "
                             "SNR-aware NN. Run with CFO_STUDY=est256 to keep its files apart")
    parser.add_argument("--packet", type=int, choices=[128, 256, 512, 1024], default=512,
                        help="packet length in symbols (codeword N = 2x); 128 writes *_L128 files")
    parser.add_argument("--codes", nargs="+", choices=list(CODES), default=None,
                        help="simulate only these codes; results of the others are kept from the saved file")
    parser.add_argument("--sources", nargs="+", choices=SOURCES, default=DEFAULT_SOURCES,
                        help="--mode ebn0: CFO sources to simulate; other saved sources are kept")
    parser.add_argument("--tag", default="",
                        help="one of several parallel Run:ai jobs: write results/progress to *_<tag> files only "
                             "(no shared file is touched); --merge collects them afterwards")
    parser.add_argument("--merge", action="store_true",
                        help="merge every polar_results_<mode>_chain[_L*]_<tag>.npy into the main file, then plot")
    parser.add_argument("--shared-frames", action="store_true",
                        help="--mode ebn0: simulate all --sources of a point in one task on the same frames (one Tx/Rx "
                             "chain per batch); results identical to separate tasks, the chain computed once")
    parser.add_argument("--missing-only", action="store_true",
                        help="simulate only the (code, Eb/N0, source) points not yet in the main results file")
    args = parser.parse_args()
    if L_EST != 128 and not paths.STUDY:
        raise SystemExit("--est-len != 128 writes over the main results: set CFO_STUDY (e.g. est256)")
    if args.codes is None:
        args.codes = [c for c in CODES if (CODES[c][2] if args.mode == "ebn0" else CODES[c][3])]
    tag = f"_{args.tag}" if args.tag else ""
    args.progress_file = paths.log(f"polar_{args.mode}{SUFFIX}{tag}.progress")
    results_file = paths.result(f"polar_results_{args.mode}_chain{SUFFIX}.npy")
    key = lambda r: (r["code"], round(r["ebn0"], 3), r["src"])
    if not args.plot_only and not args.merge and os.path.exists(args.progress_file):
        os.remove(args.progress_file)    # a stale file would show the previous run's progress

    if args.merge:       # parts of a split run override the saved points they re-simulated
        import glob
        merged = {key(r): r for r in (np.load(results_file, allow_pickle=True) if os.path.exists(results_file) else [])}
        base = f"polar_results_{args.mode}_chain{SUFFIX}_"
        parts = sorted(p for p in glob.glob(paths.result(base + "*.npy"))   # not another packet length's files
                       if not re.match(r"L\d+(_|\.npy)", os.path.basename(p)[len(base):]))
        # "add*" parts are extra frames of saved points (another seed): pooled into the saved point, never replacing
        # it; each record lists the add tags it already contains, so merging again does not count them twice
        is_add = lambda p: os.path.basename(p)[len(base):].startswith("add")
        for p in [p for p in parts if not is_add(p)]:
            merged.update({key(r): r for r in np.load(p, allow_pickle=True)})
        for p in [p for p in parts if is_add(p)]:
            add_tag = os.path.basename(p)[len(base):-4]
            for r in np.load(p, allow_pickle=True):
                k = key(r)
                merged[k] = pool_points(merged[k], r, add_tag) if k in merged else {**r, "added": [add_tag]}
        np.save(results_file, list(merged.values()), allow_pickle=True)
        print(f"merged {len(parts)} part files into {results_file}")
        args.plot_only = True
    if args.plot_only:   # redraw from the saved results
        results = list(np.load(results_file, allow_pickle=True))
        if LOWRATE and args.mode == "ebn0":     # low-rate study: SNR-axis plots only
            plot_snr(results)
        else:
            (plot_ebn0 if args.mode == "ebn0" else plot_error)(results)
        raise SystemExit

    args.skip = ({key(r) for r in np.load(results_file, allow_pickle=True)}
                 if args.missing_only and os.path.exists(results_file) else set())
    new = run(args)
    (report_ebn0 if args.mode == "ebn0" else report_error)(new, args.list_size)

    if tag:              # a part of a split run: its own file only, merged later with --merge
        np.save(paths.result(f"polar_results_{args.mode}_chain{SUFFIX}{tag}.npy"), new, allow_pickle=True)
        print("=====\nDONE", flush=True)
        raise SystemExit
    # Merge with the saved points not simulated now (every (code, Eb/N0) has its own fixed seed)
    new_keys = {key(r) for r in new}
    old = list(np.load(results_file, allow_pickle=True)) if os.path.exists(results_file) else []
    results = [r for r in old if key(r) not in new_keys] + new
    np.save(results_file, results, allow_pickle=True)
    if LOWRATE and args.mode == "ebn0":
        plot_snr(results)
    else:
        (plot_ebn0 if args.mode == "ebn0" else plot_error)(results)
    print("=====\nDONE", flush=True)
