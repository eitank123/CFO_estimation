"""
BER vs. SNR: impact of CFO estimation error on the payload.

Frame = known QPSK preamble (cfg.PREAMBLE_LENGTH) + random QPSK payload,
sent through the same Tx/Rx chain as main.py (upsample, RRC, CFO, AWGN,
matched filter, downsample) plus a random carrier phase.

Receiver, for every CFO source:
    1. de-rotate the whole frame with the CFO estimate
    2. estimate the common phase from the preamble (data-aided)
    3. hard-decide the payload QPSK symbols

CFO sources, all evaluated on the SAME received frames:
    Genie         - the same frame and noise received with zero CFO
    Known CFO     - the real frame de-rotated with the true CFO (zero estimation error;
                    still pays the RRC mismatch loss of the frequency-shifted signal)
    CRB-limited   - true CFO + N(0, CRB) error: an ideal efficient estimator (reference, not real)
    Hybrid        - Phase-1 expert + M&M + fusion net (unified_hybrid_cfo_model.pth)
    ML            - FFT periodogram peak + Newton refinement
    SNR-aware NN  - single NN fed with the true SNR (snr_aware_cfo_model_L64.pth)
    FFT-aided NN  - SNR-aware NN with periodogram-peak inputs (fft_nn_residual_cfo_model_L64.pth),
                    only if the checkpoint exists

Usage:
    python ber_experiment.py --frames 4000 --payload 1024
"""

import argparse
import paths
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from scipy.signal import fftconvolve
from scipy.special import erfc

import channel
import config as cfg
from Hybrid import DenseCFOEstimator, FusionNetwork
from train_fft_nn import FFTAidedCFOEstimator, fft_features, ml_estimate
from train_snr_nn import SNRAwareCFOEstimator, lag_features, mm_estimate

HYBRID_PATH = paths.model("unified_hybrid_cfo_model.pth")
SNR_AWARE_PATH = paths.model("snr_aware_cfo_model_L64.pth")
FFT_PATH = paths.model("fft_nn_residual_cfo_model_L64.pth")

COLORS = {"Genie": "k", "Known CFO": "#7f7f7f", "CRB-limited": "#2ca02c", "Hybrid": "#1f77b4", "ML": "#ff7f0e",
          "SNR-aware NN": "#d62728", "FFT-aided NN": "#9467bd"}
REFERENCES = ("Genie", "Known CFO", "CRB-limited")
MARKERS = {"Genie": "", "Known CFO": "", "CRB-limited": "*", "Hybrid": "^", "ML": "d", "SNR-aware NN": "o", "FFT-aided NN": "s"}


# =====================================================================
# Estimators (batched, return CFO in cycles/symbol)
# =====================================================================

def load_estimators(use_fft=True):
    dev = torch.device("cpu")

    ck = torch.load(HYBRID_PATH, map_location=dev, weights_only=False)
    max_lag, max_cfo = ck["config"]["max_lag"], ck["config"]["max_cfo"]
    expert = DenseCFOEstimator(max_lag, 4)
    expert.load_state_dict(ck["phase1_state"])
    fusion = FusionNetwork(in_features=2)
    fusion.load_state_dict(ck["phase2_state"])

    sck = torch.load(SNR_AWARE_PATH, map_location=dev, weights_only=False)
    snr_nn = SNRAwareCFOEstimator(hidden=tuple(sck["config"]["hidden"]),
                                  use_snr=sck["config"].get("use_snr", True))
    snr_nn.load_state_dict(sck["state_dict"])

    def hybrid(b):
        nn_est, mm_est = expert(b["feats"]), mm_estimate(b["R"])
        return fusion(torch.cat([nn_est, mm_est], 1), nn_est, mm_est)[0]

    est = {
        "Hybrid": hybrid,
        "ML": lambda b: ml_estimate(b["z"], b["fc"]),
        "SNR-aware NN": lambda b: snr_nn(b["feats"], b["snr"]),
    }

    if use_fft and os.path.exists(FFT_PATH):
        fck = torch.load(FFT_PATH, map_location=dev, weights_only=False)
        fft_nn = FFTAidedCFOEstimator(hidden=tuple(fck["config"]["hidden"]),
                                      residual=(fck["config"]["mode"] == "residual"))
        fft_nn.load_state_dict(fck["state_dict"])
        est["FFT-aided NN"] = lambda b: fft_nn(b["feats"], b["snr"], b["aux"])

    for m in (expert, fusion, snr_nn):
        m.eval()
    if "FFT-aided NN" in est:
        fft_nn.eval()

    @torch.no_grad()
    def estimate_all(rx_preamble, preamble, snr_db):
        z = torch.from_numpy(rx_preamble * np.conj(preamble))
        feats, R = lag_features(z)
        aux, fc = fft_features(z)
        b = {"z": z, "feats": feats, "R": R, "aux": aux, "fc": fc,
             "snr": torch.full((z.shape[0],), float(snr_db))}
        return {name: f(b).double().squeeze(1).numpy() * max_cfo for name, f in est.items()}

    return estimate_all, list(est)


# =====================================================================
# Tx / channel / Rx (batched over frames, same chain as main.py)
# =====================================================================

def random_qpsk(n_frames, n_sym):
    bits = np.random.randint(0, 2, size=(n_frames, n_sym, 2))
    # Same mapping as cfg.BIT_MAPPING_QPSK: bit0 -> sign of I, bit1 -> sign of Q
    sym = (1 - 2 * bits[..., 0] + 1j * (1 - 2 * bits[..., 1])) / np.sqrt(2)
    return bits, sym


def transmit(frames, cfo, snr_db, phase, rrc):
    """
    frames (N, K) symbols -> matched-filtered symbol-rate samples (N, K), received
    with the given CFO and, with the same noise realisation, with zero CFO (genie).
    """
    N, K = frames.shape
    up = np.zeros((N, K * cfg.SPS), dtype=np.complex128)
    up[:, ::cfg.SPS] = frames
    tx = fftconvolve(up, rrc[None, :], axes=1) * np.exp(1j * phase[:, None])

    # AWGN as main.apply_awgn: Es/N0 with Es measured per frame over the K symbols (unchanged by the CFO)
    es = np.sum(np.abs(tx) ** 2, axis=1, keepdims=True) / K
    noise_power = es / 10 ** (snr_db / 10)
    noise = np.sqrt(noise_power / 2) * (np.random.randn(*tx.shape) + 1j * np.random.randn(*tx.shape))

    n = np.arange(tx.shape[1])
    delay = cfg.FILTER_SPAN * cfg.SPS
    out = []
    for f in (cfo, np.zeros_like(cfo)):
        rx = fftconvolve(tx * np.exp(1j * 2 * np.pi * f[:, None] * n / cfg.SPS) + noise, rrc[None, :], axes=1)
        out.append(rx[:, delay: delay + K * cfg.SPS: cfg.SPS])
    return out


def demodulate(rx, preamble, cfo_hat):
    k = np.arange(rx.shape[1])
    derotated = rx * np.exp(-1j * 2 * np.pi * cfo_hat[:, None] * k)
    L = preamble.shape[1]
    phase_hat = np.angle(np.sum(derotated[:, :L] * np.conj(preamble), axis=1, keepdims=True))
    payload = derotated[:, L:] * np.exp(-1j * phase_hat)
    return np.stack([payload.real < 0, payload.imag < 0], axis=-1).astype(int)


def qpsk_ber_theory(snr_db):
    # Es/N0 -> Eb/N0 = Es/N0 / 2, BER = Q(sqrt(2 Eb/N0)) = 0.5 erfc(sqrt(Es/N0 / 2))
    return 0.5 * erfc(np.sqrt(10 ** (np.asarray(snr_db) / 10) / 2))


def crb(snr_db):
    snr = 10 ** (np.asarray(snr_db) / 10)
    L = cfg.PREAMBLE_LENGTH
    return 3.0 / (2.0 * np.pi ** 2 * snr * L * (L ** 2 - 1))


# =====================================================================
# Experiment
# =====================================================================

def run(snr_list, n_frames, payload_len, seed, chunk=500, use_fft=True):
    np.random.seed(seed)
    torch.manual_seed(seed)
    estimate_all, est_names = load_estimators(use_fft)
    sources = ["Genie", "Known CFO", "CRB-limited"] + est_names
    rrc = np.asarray(channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN))
    L = cfg.PREAMBLE_LENGTH

    results = {"sources": sources, "snr": list(snr_list), "payload": payload_len, "frames": n_frames,
               "ber": {s: [] for s in sources}, "cfo_mse": {s: [] for s in est_names}}
    for snr_db in snr_list:
        errors = {s: 0 for s in sources}
        sq_err = {s: 0.0 for s in est_names}
        t0 = time.time()
        for start in range(0, n_frames, chunk):
            n = min(chunk, n_frames - start)
            _, preamble = random_qpsk(n, L)
            payload_bits, payload = random_qpsk(n, payload_len)
            cfo = np.random.uniform(-cfg.MAX_CFO, cfg.MAX_CFO, n)
            phase = np.random.uniform(-np.pi, np.pi, n)
            rx, rx_genie = transmit(np.concatenate([preamble, payload], axis=1), cfo, snr_db, phase, rrc)

            estimates = estimate_all(rx[:, :L], preamble, snr_db)
            estimates["Known CFO"] = cfo
            estimates["CRB-limited"] = cfo + np.sqrt(crb(snr_db)) * np.random.randn(n)
            for src in sources:
                if src == "Genie":
                    decided = demodulate(rx_genie, preamble, np.zeros(n))
                else:
                    decided = demodulate(rx, preamble, estimates[src])
                errors[src] += int(np.sum(decided != payload_bits))
                if src in est_names:
                    sq_err[src] += float(np.sum((estimates[src] - cfo) ** 2))

        n_bits = 2 * n_frames * payload_len
        for src in sources:
            results["ber"][src].append(errors[src] / n_bits)
        for src in est_names:
            results["cfo_mse"][src].append(sq_err[src] / n_frames)
        print(f"SNR {snr_db:5.1f} dB | " + " | ".join(f"{s} {results['ber'][s][-1]:.3e}" for s in sources)
              + f" | {time.time() - t0:.0f}s", flush=True)
    return results


def report(res):
    est_names = [s for s in res["sources"] if s not in REFERENCES]
    print("\n" + "=" * 100)
    print(f"BER over {res['payload']}-symbol payload, {res['frames']} frames per SNR "
          f"(CFO ~ U[-{cfg.MAX_CFO}, {cfg.MAX_CFO}] cycles/symbol)")
    print("=" * 100)
    print(f"{'SNR':>5} | {'theory':>9} | " + " | ".join(f"{s:>12}" for s in res["sources"]))
    for i, snr_db in enumerate(res["snr"]):
        print(f"{snr_db:5.1f} | {qpsk_ber_theory(snr_db):9.3e} | "
              + " | ".join(f"{res['ber'][s][i]:12.3e}" for s in res["sources"]))
    print("\nCFO MSE / CRB on the same frames:")
    print(f"{'SNR':>5} | " + " | ".join(f"{s:>12}" for s in est_names))
    for i, snr_db in enumerate(res["snr"]):
        print(f"{snr_db:5.1f} | " + " | ".join(f"{res['cfo_mse'][s][i] / crb(snr_db):12.2f}" for s in est_names))


def plot(res):
    snrs = np.asarray(res["snr"])
    est_names = [s for s in res["sources"] if s not in REFERENCES]

    plt.figure(figsize=(10, 6))
    plt.semilogy(snrs, qpsk_ber_theory(snrs), "r:", linewidth=2, label="QPSK theory (perfect sync)")
    for src in res["sources"]:
        if src == "CRB-limited":   # kept in the printed table only
            continue
        style = "--" if src in REFERENCES else "-"
        label = {"Genie": "Genie (0 CFO)", "Known CFO": "Known CFO (perfect estimate)"}.get(src, src)
        plt.semilogy(snrs, res["ber"][src], style, color=COLORS[src], marker=MARKERS[src],
                     markersize=5, label=label)
    plt.xlabel("SNR (Es/N0) [dB]")
    plt.ylabel("BER")
    plt.title(f"Payload BER vs. SNR ({res['payload']} QPSK symbols after a {cfg.PREAMBLE_LENGTH}-symbol preamble)")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"ber_vs_snr_P{res['payload']}.png"), dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 6))
    for src in est_names:
        plt.semilogy(snrs, np.asarray(res["cfo_mse"][src]) / crb(snrs), color=COLORS[src],
                     marker=MARKERS[src], markersize=5, label=src)
    plt.axhline(1.0, color="r", linestyle="--", linewidth=2, label="CRB")
    plt.xlabel("SNR (Es/N0) [dB]")
    plt.ylabel("CFO MSE / CRB")
    plt.title("CFO estimation efficiency on the BER frames (RRC chain)")
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.plot(f"ber_cfo_mse_over_crb_P{res['payload']}.png"), dpi=300, bbox_inches="tight")
    plt.close()


# =====================================================================
# BER vs. residual CFO error
# =====================================================================

def run_error_sweep(snr_list, errors, n_frames, payload_len, seed, chunk=500, use_fft=True):
    """
    Same frames as run(), but de-rotated with (true CFO + eps) for a fixed residual
    error eps (cycles/symbol). The RMSE of every estimator on the same frames is
    also recorded, so it can be placed on the curve.
    """
    np.random.seed(seed)
    torch.manual_seed(seed)
    estimate_all, est_names = load_estimators(use_fft)
    rrc = np.asarray(channel.rrc_design(cfg.BETA, cfg.SPS, cfg.FILTER_SPAN))
    L = cfg.PREAMBLE_LENGTH

    res = {"snr": list(snr_list), "errors": np.asarray(errors), "payload": payload_len, "frames": n_frames,
           "est_names": est_names, "ber": {}, "ber_crb": {}, "rmse": {}}
    for snr_db in snr_list:
        bit_err = np.zeros(len(errors))
        crb_err = 0
        sq_err = {s: 0.0 for s in est_names}
        for start in range(0, n_frames, chunk):
            n = min(chunk, n_frames - start)
            _, preamble = random_qpsk(n, L)
            payload_bits, payload = random_qpsk(n, payload_len)
            cfo = np.random.uniform(-cfg.MAX_CFO, cfg.MAX_CFO, n)
            phase = np.random.uniform(-np.pi, np.pi, n)
            rx, _ = transmit(np.concatenate([preamble, payload], axis=1), cfo, snr_db, phase, rrc)
            sign = np.random.choice([-1.0, 1.0], n)
            for j, eps in enumerate(errors):
                bit_err[j] += np.sum(demodulate(rx, preamble, cfo + sign * eps) != payload_bits)
            crb_err += np.sum(demodulate(rx, preamble, cfo + np.sqrt(crb(snr_db)) * np.random.randn(n))
                              != payload_bits)
            for src, e in estimate_all(rx[:, :L], preamble, snr_db).items():
                sq_err[src] += float(np.sum((e - cfo) ** 2))
        res["ber"][snr_db] = bit_err / (2 * n_frames * payload_len)
        res["ber_crb"][snr_db] = crb_err / (2 * n_frames * payload_len)
        res["rmse"][snr_db] = {s: np.sqrt(v / n_frames) for s, v in sq_err.items()}
        print(f"SNR {snr_db:5.1f} dB | BER(eps=0) {res['ber'][snr_db][0]:.3e} | "
              + " | ".join(f"{s} RMSE {r:.2e}" for s, r in res["rmse"][snr_db].items()), flush=True)
    return res


def plot_error_sweep(res):
    eps = res["errors"]
    x = np.where(eps > 0, eps, eps[eps > 0].min() / 3)   # draw eps = 0 at the left edge of the log axis
    snr_colors = plt.cm.viridis(np.linspace(0, 0.9, len(res["snr"])))

    plt.figure(figsize=(11, 6.5))
    for c, snr_db in zip(snr_colors, res["snr"]):
        plt.loglog(x, res["ber"][snr_db], "-", color=c, label=f"SNR = {snr_db:g} dB")
    plt.xlabel("Residual CFO error |eps| (cycles/symbol, normalized to the symbol rate)")
    plt.ylabel("BER")
    plt.title(f"Payload BER vs. residual CFO error ({res['payload']}-symbol payload, "
              f"leftmost point = zero error)")
    plt.ylim(top=0.9)
    plt.grid(True, which="both", linestyle=":", alpha=0.6)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(paths.plot(f"ber_vs_cfo_error_P{res['payload']}.png"), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snrs", type=float, nargs="+", default=[float(s) for s in cfg.SNR])
    parser.add_argument("--frames", type=int, default=4000)
    parser.add_argument("--payload", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--no-fft", action="store_true", help="skip the FFT-aided NN")
    parser.add_argument("--error-sweep", action="store_true",
                        help="BER vs. fixed residual CFO error in [0, 0.2] cycles/symbol instead of BER vs. SNR")
    args = parser.parse_args()

    if args.error_sweep:
        snrs = args.snrs if args.snrs != [float(s) for s in cfg.SNR] else [-5.0, 0.0, 5.0, 10.0]
        errors = np.concatenate([[0.0], np.logspace(-6, np.log10(0.2), 40)])
        res = run_error_sweep(snrs, errors, args.frames, args.payload, args.seed, use_fft=not args.no_fft)
        plot_error_sweep(res)
        np.save(paths.result(f"ber_vs_cfo_error_P{args.payload}.npy"), res, allow_pickle=True)
        raise SystemExit

    res = run(args.snrs, args.frames, args.payload, args.seed, use_fft=not args.no_fft)
    report(res)
    plot(res)
    np.save(paths.result(f"ber_results_P{args.payload}.npy"), res, allow_pickle=True)
