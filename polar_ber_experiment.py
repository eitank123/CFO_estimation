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
else:
    raise ValueError(f"no code table for a {N_SYM}-symbol packet")
ERRORS = np.concatenate([[0.0], np.logspace(-5, np.log10(0.2), 18)])
GENIE = "Genie (known CFO)"
ESTIMATORS = ["SNR-aware NN", "M&M"]
SOURCES = [GENIE] + ESTIMATORS
COLORS = {GENIE: "k", "SNR-aware NN": "#9467bd", "M&M": "#ff7f0e"}
MARKERS = {GENIE: "", "SNR-aware NN": "s", "M&M": "d"}
LINES = {"R=0.5": "-", "R=0.25": "--", "R=0.1": ":"}
NOT_PLOTTED = {"R=0.1"}           # results kept, but no R=1/10 plots (vs Eb/N0 or vs CFO error)
SNR_AWARE_PATH = paths.model({128: "snr_aware_cfo_model_L64_chain150.pth",   # full chain, 40 + 150 epochs
                              256: "snr_aware_cfo_model_L128_est256.pth"}[L_EST])   # full chain, 256 symbols
RMSE_FILE = paths.result("cfo_rmse_chain.npz")
_snr_nn = None


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
    """One point. src is a float (fixed |eps|, random sign), GENIE, or an estimator name."""
    code_name, ebn0_db, src, list_size, batch, min_errors, max_frames, seed, task_id, progress_file = task
    from txrx_chain import DELAY_SYM, transmit
    A, C = CODES[code_name][:2]
    snr_db = esn0(code_name, ebn0_db)
    code = PolarCode(N_BITS, A, C, list_size)
    rng = np.random.default_rng(seed)                     # data, CFO, phase, noise: identical for every source
    rng_e = np.random.default_rng(seed + 1)               # sign of the fixed CFO error
    interleaver = np.random.default_rng(12345).permutation(N_BITS)    # fixed, shared by Tx and Rx
    sigma2 = 1.0 / (2.0 * 10 ** (snr_db / 10))                         # noise variance per real dimension
    n = np.arange(N_SYM)
    centre = (N_SYM - 1) / 2

    frames = frame_err = bit_err = raw_err = 0
    while frame_err < min_errors and frames < max_frames:
        data = rng.integers(0, 2, (batch, A), dtype=np.uint8)
        cw = code.encode(data)[:, interleaver]
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        f = rng.uniform(-MAX_CFO, MAX_CFO, batch)
        ph = rng.uniform(0, 2 * np.pi, batch)
        r = transmit(sym, f, ph, snr_db, rng)             # full Tx/Rx chain

        if src == GENIE:
            f_hat = f
        elif isinstance(src, str):
            f_hat = estimate(src, r[:, :L_EST] * np.conj(sym[:, :L_EST]), snr_db)
        else:
            f_hat = f + src * rng_e.choice([-1.0, 1.0], batch)
        # de-rotate by f_hat; phase of r[n] is 2 pi f (n + DELAY_SYM) + ph, reference exact at the centre
        rot = 2 * np.pi * f_hat[:, None] * (n + DELAY_SYM) + (ph + 2 * np.pi * (f - f_hat) * (centre + DELAY_SYM))[:, None]
        y = r * np.exp(-1j * rot)

        llr = np.empty((batch, N_BITS))
        llr[:, 0::2] = np.sqrt(2) * y.real / sigma2
        llr[:, 1::2] = np.sqrt(2) * y.imag / sigma2
        raw_err += int(np.sum((llr < 0) != cw))

        deint = np.empty_like(llr)
        deint[:, interleaver] = llr
        errs = code.decode(deint) != data
        bit_err += int(errs.sum())
        frame_err += int(errs.any(1).sum())
        frames += batch
        done = min(1.0, max(frame_err / min_errors, frames / max_frames))
        with open(progress_file, "a") as fp:     # per-batch progress, read by job_progress.py
            fp.write(f"{task_id} {done:.4f}\n")

    return {"code": code_name, "ebn0": ebn0_db, "esn0": snr_db, "src": src, "frames": frames,
            "frame_err": frame_err, "ber": bit_err / (frames * A), "bler": frame_err / frames,
            "raw_ber": raw_err / (frames * N_BITS)}


def run(args):
    tasks = []
    for name in args.codes:
        _, _, grid, err_points = CODES[name]
        points = grid if args.mode == "ebn0" else err_points
        sources = args.sources if args.mode == "ebn0" else [float(e) for e in ERRORS]
        for ebn0 in points:
            seed = zlib.crc32(repr((name, round(float(ebn0), 3), args.seed)).encode())
            for src in sources:
                if (name, round(float(ebn0), 3), src) in args.skip:      # --missing-only: already saved
                    continue
                tasks.append((name, float(ebn0), src, args.list_size, args.batch, args.min_errors,
                              args.max_frames, seed, len(tasks), args.progress_file))
    # Expensive points (low error rate: high Eb/N0, small eps) first so the pool stays busy
    tasks.sort(key=lambda t: (not isinstance(t[2], str) and t[2] > 1e-3, -t[1]))
    with open(args.progress_file, "w") as fp:
        fp.write(f"start {time.time():.0f} tasks {len(tasks)}\n")
    t0 = time.time()
    results = []
    with mp.Pool(args.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(simulate_point, tasks), 1):
            results.append(r)
            print(f"{i}/{len(tasks)} points | {time.time() - t0:.0f}s", flush=True)
    return results


# =====================================================================
# Report / plots
# =====================================================================

SHORT = {"R=0.5": "R=1/2", "R=0.25": "R=1/4", "R=0.1": "R=1/10"}


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
    parser.add_argument("--plot-only", action="store_true", help="redraw plots from polar_results_<mode>_chain.npy")
    parser.add_argument("--est-len", type=int, choices=[128, 256], default=128,
                        help="known symbols the CFO estimators use (start of the packet); 256 uses the 128-lag "
                             "SNR-aware NN. Run with CFO_STUDY=est256 to keep its files apart")
    parser.add_argument("--packet", type=int, choices=[128, 256, 512], default=512,
                        help="packet length in symbols (codeword N = 2x); 128 writes *_L128 files")
    parser.add_argument("--codes", nargs="+", choices=list(CODES), default=None,
                        help="simulate only these codes; results of the others are kept from the saved file")
    parser.add_argument("--sources", nargs="+", choices=SOURCES, default=SOURCES,
                        help="--mode ebn0: CFO sources to simulate; other saved sources are kept")
    parser.add_argument("--tag", default="",
                        help="one of several parallel Run:ai jobs: write results/progress to *_<tag> files only "
                             "(no shared file is touched); --merge collects them afterwards")
    parser.add_argument("--merge", action="store_true",
                        help="merge every polar_results_<mode>_chain[_L*]_<tag>.npy into the main file, then plot")
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
        for p in parts:
            merged.update({key(r): r for r in np.load(p, allow_pickle=True)})
        np.save(results_file, list(merged.values()), allow_pickle=True)
        print(f"merged {len(parts)} part files into {results_file}")
        args.plot_only = True
    if args.plot_only:   # redraw from the saved results
        results = list(np.load(results_file, allow_pickle=True))
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
    (plot_ebn0 if args.mode == "ebn0" else plot_error)(results)
    print("=====\nDONE", flush=True)
