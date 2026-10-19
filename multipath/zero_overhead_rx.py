"""
Zero-overhead single-carrier burst receiver, Stage 1: AWGN, blind + code-aided CFO, no equalizer.

Packet : 512 QPSK symbols = one polar codeword (N = 1024 bits, R = 1/2 or 1/4, CRC-11, CA-SCL L = 8),
         same interleaver and mapping as polar_ber_experiment.py. No preamble, no CP; the 2-symbol
         guard gap between bursts only matters for multipath (Stage 2). Perfect timing and frame
         sync are assumed, and the receiver knows Es/N0 (LLR scaling).
Channel: y[n] = s[n] exp(j(2 pi f n + phi)) + w[n],  f ~ U[-0.2, 0.2], phi ~ U[0, 2 pi).

Receivers, all on the same packets:
    Genie          true f and phi
    Known 512      data-aided ML (FFT 1024 + 2 Newton) on the true 512 symbols: the known-symbol bound
    Blind + CRC    Algorithm 1: 4th-power estimator (FFT of y^4, K = 2048, + 2 Newton), f0 = nu/4, phase
                   from the same line. Ambiguities: CFO modulo 1/4 (candidates f0 + k/4, k in {-1,0,1},
                   kept if inside the +-0.2 prior) and phase modulo pi/2 (4 candidates). Every candidate
                   is decoded; the CRC-passing one with the best path metric wins, else the best metric.
    Code-aided i   Algorithm 2: re-encode the decision, data-aided ML of f and phi on it (as Known 512),
                   re-decode; i = 1, 2, 3 iterations.
Also measured (no decoding): the oversampled RRC chain (SPS = 8, matched filter), where the 4th-power
line is searched over +-4*0.2 symbol rates, so the CFO cell k is chosen from the spectrum.

Outputs (multipath/results_zo_<channel>/): run.log, run.progress (job_progress.py), zo_results.npy,
zo_cfo_metrics_R0p5.png / _R0p25.png (vs. Es/N0), zo_bler_vs_ebn0.png, zo_ber_vs_ebn0.png.

Usage (project folder):
    python multipath/zero_overhead_rx.py --channel awgn
    python multipath/zero_overhead_rx.py --channel awgn --plot-only
"""

import argparse
import multiprocessing as mp
import os
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from polar import PolarCode

N_SYM, N_BITS, MAX_CFO = 512, 1024, 0.2
CODES = {"R=0.5": (512, 11), "R=0.25": (256, 11)}
SHORT = {"R=0.5": "R=1/2", "R=0.25": "R=1/4"}
ES_GRID = list(range(-5, 11))
RX = ["Genie", "Known 512", "Blind + CRC", "Code-aided 1", "Code-aided 2", "Code-aided 3"]
CFO_EST = ["Blind coarse (k=0)", "Blind + CRC", "Code-aided 1", "Code-aided 2", "Code-aided 3", "Known 512"]
OUTAGE = 1e-4
SPS = 8


# =====================================================================
# Building blocks
# =====================================================================

def interleaver():
    return np.random.default_rng(12345).permutation(N_BITS)     # same as polar_ber_experiment.py


def qpsk(cw):
    return ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)


def decode(code, y, sigma2, inter, chunk=1000):
    """Derotated symbols y (R, 512) -> data (R, A), CRC passed (R,), path metric (R,)."""
    out_d, out_ok, out_pm = [], [], []
    for i in range(0, len(y), chunk):
        yy = y[i:i + chunk]
        llr = np.empty((len(yy), N_BITS))
        llr[:, 0::2] = np.sqrt(2) * yy.real / sigma2
        llr[:, 1::2] = np.sqrt(2) * yy.imag / sigma2
        deint = np.empty_like(llr)
        deint[:, inter] = llr
        d, ok, pm = code.decode(deint, return_info=True)
        out_d.append(d), out_ok.append(ok), out_pm.append(pm)
    return np.concatenate(out_d), np.concatenate(out_ok), np.concatenate(out_pm)


def newton(x, f, iters=2):
    """Refine the peak f (R,) of |sum_n x[n] exp(-j 2 pi f n)|^2 with Newton steps."""
    n = np.arange(x.shape[1])
    for _ in range(iters):
        e = x * np.exp(-2j * np.pi * f[:, None] * n)
        A, A1, A2 = e.sum(1), (e * (-2j * np.pi * n)).sum(1), (e * (-(2 * np.pi * n) ** 2)).sum(1)
        f = f - 2 * (A1 * A.conj()).real / (2 * ((A2 * A.conj()).real + np.abs(A1) ** 2))
    return f


def tone(x, K, f_max):
    """Strongest tone of x (R, L): coarse FFT peak with |f| <= f_max, 2 Newton steps, and its phase."""
    X = np.abs(np.fft.fft(x, n=K, axis=1))
    fr = np.fft.fftfreq(K)
    X[:, np.abs(fr) > f_max + 1.0 / K] = -1
    f = newton(x, fr[X.argmax(1)])
    ph = np.angle((x * np.exp(-2j * np.pi * f[:, None] * np.arange(x.shape[1]))).sum(1))
    return f, ph


def data_aided(y, s):
    """Data-aided ML CFO and phase from y and (estimated or true) symbols s: FFT 1024 + 2 Newton."""
    return tone(y * s.conj(), 2 * N_SYM, MAX_CFO)


def fourth_power(y):
    """Blind 4th-power estimate: f0 in [-1/8, 1/8) (ambiguous mod 1/4) and phase phi0 (ambiguous mod pi/2)."""
    nu, th = tone(y ** 4, 4 * N_SYM, 0.5)
    nu = (nu + 0.5) % 1.0 - 0.5
    return nu / 4, (th - np.pi) / 4                 # s^4 = -1 for every QPSK symbol


def derotate(y, f, ph):
    return y * np.exp(-1j * (2 * np.pi * f[:, None] * np.arange(y.shape[1]) + ph[:, None]))


def oversampled_cell(sym, f, ph, snr, rng, rrc):
    """Oversampled RRC chain: k chosen from the 4th-power line searched over +-4*MAX_CFO symbol rates."""
    from scipy.signal import fftconvolve
    B = len(sym)
    up = np.zeros((B, N_SYM * SPS), complex)
    up[:, ::SPS] = sym
    tx = fftconvolve(up, rrc[None], axes=1)
    n = np.arange(tx.shape[1])
    rx = tx * np.exp(1j * (2 * np.pi * f[:, None] * n / SPS + ph[:, None]))
    rx = rx + np.sqrt(1 / snr / 2) * (rng.standard_normal(rx.shape) + 1j * rng.standard_normal(rx.shape))
    D = (len(rrc) - 1)
    mf = fftconvolve(rx, rrc[None], axes=1)[:, D:D + N_SYM * SPS]
    f0, _ = fourth_power(mf[:, ::SPS])                               # fine value, symbol rate
    K = 4 * N_SYM * SPS
    X = np.abs(np.fft.fft(mf ** 4, n=K, axis=1))
    fr = np.fft.fftfreq(K) * SPS                                      # cycles/symbol
    X[:, np.abs(fr) > 4 * MAX_CFO + SPS / K] = -1
    f_spec = fr[X.argmax(1)] / 4
    ks = np.array([-1, 0, 1])
    cand = f0[:, None] + ks / 4
    cand_ok = np.abs(cand) <= MAX_CFO + 0.005
    k_os = ks[np.where(cand_ok, np.abs(cand - f_spec[:, None]), np.inf).argmin(1)]
    k_true = ks[np.abs(cand - f[:, None]).argmin(1)]
    return k_os != k_true


# =====================================================================
# Monte Carlo point
# =====================================================================

def simulate_point(task):
    code_name, es_db, batch, min_errors, min_frames, max_frames, n_os, seed, task_id, progress_file = task
    A, C = CODES[code_name]
    code = PolarCode(N_BITS, A, C, 8)
    inter = interleaver()
    rng = np.random.default_rng(seed)
    snr = 10 ** (es_db / 10)
    sigma2 = 1 / (2 * snr)
    n = np.arange(N_SYM)
    import channel
    import config as cfg
    rrc = np.asarray(channel.rrc_design(cfg.BETA, SPS, cfg.FILTER_SPAN))

    acc = {"frames": 0, "bit_err": {r: 0 for r in RX}, "frame_err": {r: 0 for r in RX},
           "cfo_err": {e: [] for e in CFO_EST}, "amb_present": 0, "amb_err": 0, "hyp_err": 0,
           "decodes_blind": 0, "os_err": 0, "os_n": 0}
    while (acc["frame_err"]["Code-aided 3"] < min_errors or acc["frames"] < min_frames) and acc["frames"] < max_frames:
        B = batch
        data = rng.integers(0, 2, (B, A), dtype=np.uint8)
        sym = qpsk(code.encode(data)[:, inter])
        f = rng.uniform(-MAX_CFO, MAX_CFO, B)
        ph = rng.uniform(0, 2 * np.pi, B)
        y = sym * np.exp(1j * (2 * np.pi * f[:, None] * n + ph[:, None])) + np.sqrt(sigma2) * (
            rng.standard_normal((B, N_SYM)) + 1j * rng.standard_normal((B, N_SYM)))

        def score(name, d):
            e = d != data
            acc["bit_err"][name] += int(e.sum())
            acc["frame_err"][name] += int(e.any(1).sum())

        # Genie and the known-symbol bound
        score("Genie", decode(code, derotate(y, f, ph), sigma2, inter)[0])
        fk, phk = data_aided(y, sym)
        acc["cfo_err"]["Known 512"].append(fk - f)
        score("Known 512", decode(code, derotate(y, fk, phk), sigma2, inter)[0])

        # Algorithm 1: blind 4th power, ambiguity resolved by the CRC over all valid hypotheses
        f0, ph0 = fourth_power(y)
        acc["cfo_err"]["Blind coarse (k=0)"].append(f0 - f)
        ks = np.array([-1, 0, 1])
        k_true = ks[np.abs(f0[:, None] + ks / 4 - f[:, None]).argmin(1)]
        acc["amb_present"] += int((k_true != 0).sum())
        rows = [(p, k, m) for p in range(B) for k in ks for m in range(4) if abs(f0[p] + k / 4) <= MAX_CFO + 0.005]
        rp, rk, rm = (np.array(v) for v in zip(*rows))
        acc["decodes_blind"] += len(rows)
        d_r, ok_r, pm_r = decode(code, derotate(y[rp], f0[rp] + rk / 4, ph0[rp] + rm * np.pi / 2), sigma2, inter)
        pick = np.empty(B, int)
        for p in range(B):
            idx = np.where(rp == p)[0]
            good = idx[ok_r[idx]]
            pick[p] = good[pm_r[good].argmin()] if len(good) else idx[pm_r[idx].argmin()]
        d_sel, k_sel = d_r[pick], rk[pick]
        f_sel = f0 + k_sel / 4
        # phase hypothesis m that matches the true phase (for the hypothesis-error rate)
        m_true = np.round(((ph - ph0) % (2 * np.pi)) / (np.pi / 2)) % 4
        acc["amb_err"] += int((k_sel != k_true).sum())
        acc["hyp_err"] += int(((k_sel != k_true) | (rm[pick] != m_true)).sum())
        acc["cfo_err"]["Blind + CRC"].append(f_sel - f)
        score("Blind + CRC", d_sel)

        # Algorithm 2: code-aided refinement on the decisions
        for it in (1, 2, 3):
            s_hat = qpsk(code.encode(d_sel)[:, inter])
            fi, phi_ = data_aided(y, s_hat)
            acc["cfo_err"][f"Code-aided {it}"].append(fi - f)
            d_sel = decode(code, derotate(y, fi, phi_), sigma2, inter)[0]
            score(f"Code-aided {it}", d_sel)

        # Oversampled spectral ambiguity resolution (subset, no decoding)
        if acc["os_n"] < n_os:
            m_os = min(B, n_os - acc["os_n"])
            acc["os_err"] += int(oversampled_cell(sym[:m_os], f[:m_os], ph[:m_os], snr, rng, rrc).sum())
            acc["os_n"] += m_os

        acc["frames"] += B
        done = min(1.0, max(min(acc["frame_err"]["Code-aided 3"] / min_errors, 1.0) * min(acc["frames"] / min_frames, 1.0),
                            acc["frames"] / max_frames))
        with open(progress_file, "a") as fp:
            fp.write(f"{task_id} {done:.4f}\n")

    acc["cfo_err"] = {k: np.concatenate(v) for k, v in acc["cfo_err"].items()}
    return {"code": code_name, "es": es_db, "ebn0": es_db - 10 * np.log10(A / N_SYM), **acc}


def run(args, log):
    tasks = []
    points = [(name, es) for name in CODES for es in ES_GRID]
    for i, (name, es) in enumerate(points):
        if i % args.parts != args.part:          # --parts P: this job takes every P-th point
            continue
        seed = zlib.crc32(repr(("zo", args.channel, name, es, args.seed)).encode())
        tasks.append((name, float(es), args.batch, args.min_errors, args.min_frames, args.max_frames,
                      args.os_packets, seed, len(tasks), args.progress))
    tasks.sort(key=lambda t: -t[1])                   # high SNR (most frames) first
    with open(args.progress, "w") as fp:
        fp.write(f"start {time.time():.0f} tasks {len(tasks)}\n")
    t0, results = time.time(), []
    with mp.Pool(args.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(simulate_point, tasks), 1):
            results.append(r)
            log(f"{i}/{len(tasks)} points | {time.time() - t0:.0f}s")
    return results


# =====================================================================
# Report and plots
# =====================================================================

def metrics(r):
    out = {}
    for e, v in r["cfo_err"].items():
        out[e] = (np.sqrt(np.mean(v ** 2)), np.median(np.abs(v)), np.mean(np.abs(v) > OUTAGE))
    return out


def report(results, log):
    for name in CODES:
        rs = sorted((r for r in results if r["code"] == name), key=lambda r: r["es"])
        log(f"\n{'=' * 110}\n{SHORT[name]}: BLER (BER)\n{'=' * 110}")
        rxs, cfos = RX, CFO_EST
        log(f"{'Es/N0':>5} {'Eb/N0':>6} | " + " | ".join(f"{x:>21}" for x in rxs) + " | frames | decodes/packet (blind)")
        for r in rs:
            cells = [f"{r['frame_err'][x] / r['frames']:.2e} ({r['bit_err'][x] / (r['frames'] * CODES[name][0]):.1e})" for x in rxs]
            log(f"{r['es']:5.1f} {r['ebn0']:6.2f} | " + " | ".join(f"{c:>21}" for c in cells) +
                f" | {r['frames']:6d} | {r['decodes_blind'] / r['frames'] + 3:.2f} (+ Genie/bound)")
        log(f"\n{SHORT[name]}: CFO RMSE / median |err| / P(|err| > {OUTAGE:g}); ambiguity error rates")
        log(f"{'Es/N0':>5} | " + " | ".join(f"{e:>30}" for e in cfos) + " | k-err CRC | (k,phi)-err | k-err oversampled | k != 0")
        for r in rs:
            m = metrics(r)
            cells = [f"{m[e][0]:.1e} / {m[e][1]:.1e} / {m[e][2]:.3f}" for e in cfos]
            log(f"{r['es']:5.1f} | " + " | ".join(f"{c:>30}" for c in cells) +
                f" | {r['amb_err'] / r['frames']:.4f} | {r['hyp_err'] / r['frames']:.4f} | "
                f"{r['os_err'] / max(r['os_n'], 1):.4f} | {r['amb_present'] / r['frames']:.3f}")


def validate(results, log):
    """The AWGN Genie and Known-512 curves must reproduce the main study (polar_results_ebn0.npy)."""
    f = os.path.join(ROOT, "results", "polar_results_ebn0.npy")
    if not os.path.exists(f):
        return
    ref = list(np.load(f, allow_pickle=True))
    log("\nValidation against the main AWGN study (BLER at the closest Eb/N0 point):")
    for r in sorted(results, key=lambda r: (r["code"], r["es"])):
        for mine, theirs in (("Genie", "Genie (0 CFO error)"), ("Known 512", "M&M (L=512)")):
            cand = [x for x in ref if x["code"] == r["code"] and x["src"] == theirs and abs(x["ebn0"] - r["ebn0"]) < 0.02]
            if cand and (cand[0]["bler"] > 0 or r["frame_err"][mine] > 0):
                log(f"  {SHORT[r['code']]} Eb/N0 {r['ebn0']:5.2f}: {mine:<9} {r['frame_err'][mine] / r['frames']:.2e}"
                    f"  vs main study {theirs:<20} {cand[0]['bler']:.2e} (Eb/N0 {cand[0]['ebn0']:.2f})")


def plot(results, out_dir):
    colors = {"Genie": "k", "Known 512": "#2ca02c", "Blind + CRC": "#ff7f0e", "Code-aided 1": "#9ecae1",
              "Code-aided 2": "#4292c6", "Code-aided 3": "#08519c", "Blind coarse (k=0)": "#bbbbbb"}
    for metric, ylabel, fname in (("bler", "BLER", "zo_bler_vs_ebn0"), ("ber", "BER", "zo_ber_vs_ebn0")):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
        for ax, name in zip(axes, CODES):
            rs = sorted((r for r in results if r["code"] == name), key=lambda r: r["es"])
            x = [r["ebn0"] for r in rs]
            for rx in RX:
                v = np.array([(r["frame_err"][rx] / r["frames"]) if metric == "bler" else
                              r["bit_err"][rx] / (r["frames"] * CODES[name][0]) for r in rs])
                ax.semilogy(x, np.where(v > 0, v, np.nan), "--" if rx in ("Genie", "Known 512") else "-",
                            color=colors[rx], marker="o", markersize=3, label=rx)
            ax.set_title(SHORT[name])
            ax.set_xlabel("Eb/N0 [dB]")
            ax.grid(True, which="both", linestyle=":", alpha=0.6)
        axes[0].set_ylabel(ylabel)
        axes[0].legend(fontsize=9)
        fig.suptitle(f"Zero-overhead receiver, AWGN: {ylabel} vs. Eb/N0 (512-symbol packet, no preamble)")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, fname + ".png"), dpi=300, bbox_inches="tight")
        plt.close(fig)

    for name in CODES:
        rs = sorted((r for r in results if r["code"] == name), key=lambda r: r["es"])
        es = [r["es"] for r in rs]
        ms = [metrics(r) for r in rs]
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        for ax, (i, ylabel) in zip(axes.flat[:3], enumerate(["CFO RMSE", "Median |CFO error|", f"P(|CFO error| > {OUTAGE:g})"])):
            for e in CFO_EST:
                ax.semilogy(es, [m[e][i] for m in ms], "--" if e == "Known 512" else "-", color=colors[e],
                            marker="o", markersize=3, label=e)
            if i < 2:
                crb = 3 / (2 * np.pi ** 2 * 10 ** (np.array(es) / 10) * N_SYM * (N_SYM ** 2 - 1))
                ax.semilogy(es, np.sqrt(crb), "k:", label="sqrt(CRB), 512 symbols")
            ax.set_ylabel(ylabel + (" (cycles/symbol)" if i < 2 else ""))
        ax = axes.flat[3]
        for key, label, c in (("amb_err", "CFO cell k wrong, CRC selection", "#ff7f0e"),
                              ("hyp_err", "(k, phase) hypothesis wrong, CRC selection", "#d62728"),
                              ("os_err", "CFO cell k wrong, oversampled spectrum", "#9467bd"),
                              ("amb_present", "Packets with an ambiguity (k != 0)", "#bbbbbb")):
            den = [max(r["os_n"], 1) if key == "os_err" else r["frames"] for r in rs]
            v = np.array([r[key] for r in rs]) / np.array(den)
            ax.semilogy(es, np.where(v > 0, v, np.nan), color=c, marker="o", markersize=3, label=label)
        ax.set_ylabel("Rate")
        for ax in axes.flat:
            ax.set_xlabel("Es/N0 [dB]")
            ax.grid(True, which="both", linestyle=":", alpha=0.6)
            ax.legend(fontsize=8)
        fig.suptitle(f"Zero-overhead receiver, AWGN, {SHORT[name]}: CFO estimation")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"zo_cfo_metrics_{name.replace('=', '').replace('.', 'p')}.png"),
                    dpi=300, bbox_inches="tight")
        plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", choices=["awgn", "multipath"], default="awgn")
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--min-errors", type=int, default=200, help="frame errors of the final receiver per point")
    ap.add_argument("--min-frames", type=int, default=2000, help="for the CFO statistics")
    ap.add_argument("--max-frames", type=int, default=10000)
    ap.add_argument("--os-packets", type=int, default=2000, help="packets per point for the oversampled chain")
    ap.add_argument("--workers", type=int, default=mp.cpu_count())
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--plot-only", action="store_true")
    ap.add_argument("--parts", type=int, default=1, help="split the points over this many jobs")
    ap.add_argument("--part", type=int, default=0, help="which part this job runs (0 .. parts-1)")
    ap.add_argument("--merge", action="store_true", help="combine zo_results_p*.npy, then report and plot")
    ap.add_argument("--es-step", type=float, default=1.0, help="Es/N0 grid step over -5 .. 10 dB")
    args = ap.parse_args()
    ES_GRID = [round(float(x), 2) for x in np.arange(-5.0, 10.0 + 1e-9, args.es_step)]
    if args.channel != "awgn":
        raise SystemExit("Stage 2 (multipath equalization) is not implemented yet")

    out_dir = os.path.join(HERE, f"results_zo_{args.channel}")
    os.makedirs(out_dir, exist_ok=True)
    tag = f"_p{args.part}" if args.parts > 1 else ""
    args.progress = os.path.join(out_dir, f"run{tag}.progress")
    res_file = os.path.join(out_dir, "zo_results.npy")
    if args.plot_only:
        plot(list(np.load(res_file, allow_pickle=True)), out_dir)
        raise SystemExit
    log_f = open(os.path.join(out_dir, "run.log" if args.merge else f"run{tag}.log"), "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True)
        log_f.write(msg + "\n")
        log_f.flush()

    if args.merge:
        import glob
        results = [r for f in sorted(glob.glob(os.path.join(out_dir, "zo_results_p*.npy")))
                   for r in np.load(f, allow_pickle=True)]
        log(f"merged {len(results)} points")
    else:
        if os.path.exists(args.progress):
            os.remove(args.progress)
        results = run(args, log)
        if args.parts > 1:
            np.save(os.path.join(out_dir, f"zo_results{tag}.npy"), results, allow_pickle=True)
            log("=====\nPART DONE")
            raise SystemExit
    np.save(res_file, results, allow_pickle=True)
    report(results, log)
    validate(results, log)
    plot(results, out_dir)
    log("=====\nDONE")
