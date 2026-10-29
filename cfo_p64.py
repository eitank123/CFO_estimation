"""
64-symbol preamble (lowrate study, 1024-symbol packet, full Tx/Rx chain): CFO MSE, outage P(|e| > 1.0e-4) and the
split wrong-lobe rate of the four estimators on 64 known symbols, on the SAME frames:

    M&M          64 contiguous symbols (lags 1..32)
    SNR-aware NN 64 contiguous symbols (lowrate/models/snr_aware_cfo_model_L32_chain.pth)
    split ML     2 x 32 symbols centred at N/4 and 3N/4
    split NN     2 x 32 (lowrate/models/cfo_split_nn_L1024_B32.pth)

and, as the 128-symbol reference on the same frames, M&M and the SNR-aware NN on 128 contiguous symbols (the split
NN on 2 x 64 comes from logs/cfo_split_nn_L1024.json and logs/cfo_outage_split.json).
Per SNR: 1e6 frames at <= -3 dB, 1e5 above.

    CFO_STUDY=lowrate python cfo_p64.py --snrs -5 --part a     # -> lowrate/logs/cfo_p64_a.json (one part per job)
    CFO_STUDY=lowrate python cfo_p64.py --merge --plot         # -> lowrate/logs/cfo_p64.json, lowrate/plots/{mse,outage}
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import time

os.environ.setdefault("CFO_STUDY", "lowrate")
os.environ["CFO_BLOCK"] = "32"                 # train_cfo_v3 reads the block size at import
os.environ["CFO_PILOTS"] = "quarter"

import numpy as np

import paths

SNRS = [-5, -4, -3, -2, -1, 0, 2, 5, 10]
N_SYM = 1024
TOL = 1.0e-4                                   # the 1024-symbol R = 1/10 CRC-16 code's CFO tolerance (A.15.1)
CHUNK, BATCH = 10000, 500
EST = ("M&M 64", "NN 64", "split ML 2x32", "split NN 2x32", "M&M 128", "NN 128")
OUT = "cfo_p64.json"


def _snr_nn(name, max_lag):
    import torch
    from train_snr_nn import SNRAwareCFOEstimator
    ck = torch.load(paths.model(name), map_location="cpu", weights_only=False)
    assert ck["config"]["max_lag"] == max_lag, (name, ck["config"]["max_lag"])
    m = SNRAwareCFOEstimator(max_lag=max_lag, hidden=tuple(ck["config"]["hidden"]))
    m.load_state_dict(ck["state_dict"])
    return m.eval()


def _work(task):
    snr, seed = task
    import torch
    torch.set_num_threads(1)
    from train_cfo_split_nn import load_best
    from train_cfo_v3 import positions, spacing, split_ml
    from train_snr_nn import MAX_CFO, lag_features, mm_estimate
    from txrx_chain import qpsk, transmit
    nn64, nn128 = _snr_nn("snr_aware_cfo_model_L32_chain.pth", 32), _snr_nn("snr_aware_cfo_model_L64_chain150.pth", 64)
    snn = load_best(N_SYM)
    kp, d = positions(N_SYM, "quarter"), spacing(N_SYM, "quarter")
    rng = np.random.default_rng(seed)
    acc = {k: np.zeros(4) for k in EST}          # sum e^2, outage count, wrong-lobe count, frames
    s = torch.full((BATCH,), float(snr), dtype=torch.float64)
    with torch.no_grad():
        for _ in range(CHUNK // BATCH):
            sym = qpsk(rng, (BATCH, N_SYM))
            f = rng.uniform(-MAX_CFO, MAX_CFO, BATCH)
            z = transmit(sym, f, rng.uniform(0, 2 * np.pi, BATCH), snr, rng) * np.conj(sym)
            est = {}
            for L, nn, tag in ((64, nn64, "64"), (128, nn128, "128")):
                feats, R = lag_features(torch.from_numpy(z[:, :L]))
                est[f"M&M {tag}"] = mm_estimate(R).double().numpy()[:, 0] * MAX_CFO
                est[f"NN {tag}"] = nn(feats, s.float()).double().numpy()[:, 0] * MAX_CFO
            zp = z[:, kp]
            est["split ML 2x32"] = split_ml(zp, N_SYM, "quarter")[0].numpy()
            est["split NN 2x32"] = snn(torch.from_numpy(zp), s)[0].numpy()
            for k, fh in est.items():
                e = fh - f
                acc[k] += [np.sum(e ** 2), np.sum(np.abs(e) > TOL), np.sum(np.round(e / d) != 0), BATCH]
    return snr, acc


def run(workers, snrs, part):
    tasks = [(s, 700000 + 1000 * (s + 10) + i) for s in snrs for i in range((1000000 if s <= -3 else 100000) // CHUNK)]
    acc = {s: {k: np.zeros(4) for k in EST} for s in snrs}
    t0 = time.time()
    with mp.Pool(workers) as pool:
        for i, (s, a) in enumerate(pool.imap_unordered(_work, tasks), 1):
            for k in EST:
                acc[s][k] += a[k]
            with open(os.path.join(paths.ROOT, "logs", f"p64out-{part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} {time.time() - t0:.0f}\n")
    out = {"snr": snrs, "tol": TOL, "est": {k: {"mse": [acc[s][k][0] / acc[s][k][3] for s in snrs],
                                                "outage": [acc[s][k][1] / acc[s][k][3] for s in snrs],
                                                "wrong_lobe": [acc[s][k][2] / acc[s][k][3] for s in snrs],
                                                "n": [int(acc[s][k][3]) for s in snrs]} for k in EST}}
    json.dump(out, open(paths.log(f"cfo_p64_{part}.json"), "w"), indent=1)
    for k in EST:
        print(f"{k:14s} MSE " + " ".join(f"{v:.2e}" for v in out["est"][k]["mse"]) + " | outage "
              + " ".join(f"{v:.3f}" for v in out["est"][k]["outage"]), flush=True)
    print("EVAL DONE", flush=True)


def merge():
    parts = [json.load(open(p)) for p in sorted(glob.glob(paths.log("cfo_p64_*.json")))]
    rows = sorted((s, p, i) for p in parts for i, s in enumerate(p["snr"]))
    out = {"snr": [s for s, _, _ in rows], "tol": TOL,
           "est": {k: {q: [p["est"][k][q][i] for _, p, i in rows] for q in ("mse", "outage", "wrong_lobe", "n")}
                   for k in EST}}
    json.dump(out, open(paths.log(OUT), "w"), indent=1)
    print(f"merged {len(parts)} parts: SNRs {out['snr']}")


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import config as cfg
    from train_cfo_v3 import crb_split
    from train_snr_nn import crb
    d = json.load(open(paths.log(OUT)))
    snr = np.array(d["snr"], float)
    root = os.path.join(paths.ROOT, "logs")      # the 128-pilot split NN (main study logs)
    s128 = json.load(open(os.path.join(root, "cfo_split_nn_L1024.json")))
    o128 = json.load(open(os.path.join(root, "cfo_outage_split.json")))
    styles = {"M&M 64": ("#ff7f0e", "-.", "d", "M&M, 64 contiguous"),
              "NN 64": ("#9467bd", "-", "s", "SNR-aware NN, 64 contiguous"),
              "split ML 2x32": ("#e377c2", ":", "x", "Split ML, 2 × 32"),
              "split NN 2x32": ("#17becf", "-", "h", "Split NN, 2 × 32"),
              "M&M 128": ("#ff7f0e", "-.", "d", "M&M, 128 contiguous"),
              "NN 128": ("#9467bd", "-", "s", "SNR-aware NN, 128 contiguous")}

    fig, ax = plt.subplots(figsize=(11, 6.5))
    for k, (c, ls, mk, lab) in styles.items():
        ref = "128" in k
        ax.semilogy(snr, d["est"][k]["mse"], ls=ls, color=c, marker=mk, lw=1.4 if ref else 2.2, ms=5,
                    alpha=0.45 if ref else 1, markerfacecolor="none" if ref else c, label=lab)
    ax.semilogy(s128["snr"], s128["est"]["nn"]["mse"], "-", color="#17becf", marker="h", lw=1.4, alpha=0.45,
                markerfacecolor="none", label="Split NN, 2 × 64")
    ax.semilogy(snr, [crb(s, 64) for s in snr], ":", color="0.25", lw=1.5, label="CRB, 64 contiguous")
    ax.semilogy(snr, crb_split(snr, N_SYM, "quarter"), "--", color="0.25", lw=1.2, label="CRB, 2 × 32 split")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO MSE [(cycles/symbol)²]")
    fig.suptitle("CFO MSE vs SNR", fontsize=15, fontweight="bold")
    ax.set_title(f"{N_SYM}-symbol packet, 64 known symbols (bold) vs 128 (faded); roll-off = {cfg.BETA:g}",
                 fontsize=10.5, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(paths.plot("cfo_mse_vs_snr_preamble64_L1024.png"), dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    floor = 1.0 / np.array(d["est"]["M&M 64"]["n"], float)
    for k, (c, ls, mk, lab) in styles.items():
        ref = "128" in k
        y = np.array(d["est"][k]["outage"])
        ax.semilogy(snr, np.where(y > 0, y, np.nan), ls=ls, color=c, marker=mk, lw=1.4 if ref else 2.2, ms=5,
                    alpha=0.45 if ref else 1, markerfacecolor="none" if ref else c, label=lab)
        if (y == 0).any() and not ref:
            ax.semilogy(snr[y == 0], floor[y == 0], "v", color=c, markerfacecolor="none", ms=6)
    j = [abs(t - TOL) < 1e-12 for t in o128["thresholds"]].index(True)
    y = np.array(o128["outage"]["split NN"][j])
    ax.semilogy(o128["snr"], np.where(y > 0, y, np.nan), "-", color="#17becf", marker="h", lw=1.4, alpha=0.45,
                markerfacecolor="none", label="Split NN, 2 × 64")
    ax.set_xlabel("SNR (Es/N0) [dB]")
    ax.set_ylabel("CFO outage probability")
    ax.set_title(f"CFO outage probability vs. SNR (64 known symbols, roll-off = {cfg.BETA:g})", fontsize=13)
    ax.text(0.99, 0.97, f"outage: |CFO error| > {TOL:.1e}; faded: 128 known symbols", transform=ax.transAxes,
            ha="right", va="top", fontsize=10, color="0.3")
    ax.grid(True, which="both", linestyle=":", alpha=0.6)
    ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(paths.plot("cfo_outage_preamble64_L1024.png"), dpi=300)
    plt.close(fig)
    print("saved", paths.plot("cfo_mse_vs_snr_preamble64_L1024.png"), paths.plot("cfo_outage_preamble64_L1024.png"))


def plot_bler():
    """BLER vs SNR with a 64-symbol preamble (lowrate/results/polar_results_ebn0_chain_L1024_P64.npy), the same
    receivers with 128 pilots faded (polar_results_ebn0_chain_L1024.npy): R = 1/10 (-5..0 dB), R = 1/4 (0..10 dB)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    load = lambda f: list(np.load(paths.result(f), allow_pickle=True)) if os.path.exists(paths.result(f)) else []
    r64, r128 = load("polar_results_ebn0_chain_L1024_P64.npy"), load("polar_results_ebn0_chain_L1024.npy")
    rx = (("Genie (known CFO)", "Genie (no CFO error)", "k", ":", ""),
          ("M&M", "M&M", "#ff7f0e", "-.", "d"),
          ("M&M + CRC search (first pass)", "M&M + CRC search (first pass)", "#9467bd", "--", "v"),
          ("SNR-aware NN + CRC search (first pass)", "SNR-aware NN + CRC search (first pass)", "#1f77b4", "--", "o"),
          ("Split pilots NN, quarter", "Split pilots NN (no CRC search)", "#17becf", ":", "X"),
          ("Split pilots NN, quarter + CRC search (first pass)", "Split pilots NN + CRC search (first pass)", "#17becf",
           "-", "h"))
    for code, lo, hi, tag in (("R=0.1,C16", -5.0, 0.0, "R0p1"), ("R=1/4,C16", 0.0, 10.0, "R1_4")):
        fig, ax = plt.subplots(figsize=(11, 6.5))
        for res, faded in ((r128, True), (r64, False)):
            for src, lab, c, ls, mk in rx:
                if faded and src == "Genie (known CFO)":
                    continue
                pts = sorted((q["esn0"], q["bler"]) for q in res if q["code"] == code and q["src"] == src
                             and lo - 0.01 <= q["esn0"] <= hi + 0.01 and np.isclose(q["esn0"] * 2, round(q["esn0"] * 2)))
                pts = [p for p in pts if p[1] > 0]
                if len(pts) < 2:
                    continue
                x, y = map(np.array, zip(*pts))
                ax.semilogy(x, y, ls=ls, color=c, marker=mk, lw=1.3 if faded else 2.2, ms=4 if faded else 5,
                            alpha=0.35 if faded else 1, markerfacecolor="none" if faded else c,
                            label=None if faded else lab)
        ax.plot([], [], color="0.5", alpha=0.35, lw=1.3, label="faded: the same receiver with 128 pilots")
        ax.set_xlabel("SNR (Es/N0) [dB]")
        ax.set_ylabel("BLER")
        ax.set_xlim(lo - 0.25, hi + 0.25)
        ax.set_ylim(top=1.5)
        fig.suptitle("BLER vs SNR, 64-symbol preamble", fontsize=15, fontweight="bold")
        A = {"R=0.1,C16": 205, "R=1/4,C16": 512}[code]
        ax.set_title(f"{N_SYM}-symbol packet, R = {'1/10' if tag == 'R0p1' else '1/4'}, CRC-16 ({A} data bits); "
                     "64 known symbols (split: 2 × 32 centred at N/4, 3N/4)", fontsize=10.5, color="0.3")
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        ax.legend(fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
        fig.tight_layout()
        out = paths.plot(f"polar_bler_vs_snr_preamble64_{tag}_C16_L1024.png")
        fig.savefig(out, dpi=300)
        plt.close(fig)
        print("saved", out)


def plot_bler_crc():
    """64-symbol preamble, CRC-24 against CRC-16 (same data bits A): the CRC search receivers and the genie; 128 pilots
    with CRC-16 faded. R = 1/10 (-5..0 dB), R = 1/4 (0..10 dB)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    load = lambda f: list(np.load(paths.result(f), allow_pickle=True)) if os.path.exists(paths.result(f)) else []
    r64, r128 = load("polar_results_ebn0_chain_L1024_P64.npy"), load("polar_results_ebn0_chain_L1024.npy")
    rx = (("Genie (known CFO)", "Genie", "k", ""),
          ("M&M + CRC search (first pass)", "M&M + CRC search", "#9467bd", "v"),
          ("SNR-aware NN + CRC search (first pass)", "SNR-aware NN + CRC search", "#1f77b4", "o"),
          ("Split pilots NN, quarter + CRC search (first pass)", "Split NN + CRC search", "#17becf", "h"))
    for rate, lo, hi, tag in (("R=0.1", -5.0, 0.0, "R0p1"), ("R=1/4", 0.0, 10.0, "R1_4")):
        fig, ax = plt.subplots(figsize=(11, 6.5))
        for res, crc, ls, lw, alpha, suffix in ((r128, 16, "-", 1.2, 0.3, None), (r64, 16, "--", 1.6, 0.9, "CRC-16"),
                                                (r64, 24, "-", 2.3, 1.0, "CRC-24")):
            for src, lab, c, mk in rx:
                if src.startswith("Genie") and res is r128:
                    continue
                pts = sorted((q["esn0"], q["bler"]) for q in res if q["code"] == f"{rate},C{crc}" and q["src"] == src
                             and lo - 0.01 <= q["esn0"] <= hi + 0.01 and np.isclose(q["esn0"] * 2, round(q["esn0"] * 2))
                             and q["bler"] > 0)
                if len(pts) < 2:
                    continue
                x, y = map(np.array, zip(*pts))
                ax.semilogy(x, y, ls=":" if src.startswith("Genie") else ls, color=c, marker=mk, lw=lw, ms=4,
                            alpha=alpha, markerfacecolor=c if suffix == "CRC-24" else "none",
                            label=None if suffix is None else f"64 pilots, {suffix}: {lab}")
        ax.plot([], [], color="0.5", alpha=0.3, lw=1.2, label="faded: 128 pilots, CRC-16")
        ax.set_xlabel("SNR (Es/N0) [dB]")
        ax.set_ylabel("BLER")
        ax.set_xlim(lo - 0.25, hi + 0.25)
        fig.suptitle("BLER vs SNR, 64-symbol preamble: CRC-24 vs CRC-16", fontsize=15, fontweight="bold")
        A = {"R=0.1": 205, "R=1/4": 512}[rate]
        ax.set_title(f"{N_SYM}-symbol packet, R = {'1/10' if tag == 'R0p1' else '1/4'} ({A} data bits); first-pass CRC "
                     "search; split pilots 2 × 32", fontsize=10.5, color="0.3")
        ax.grid(True, which="both", linestyle=":", alpha=0.6)
        ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False)
        fig.tight_layout()
        out = paths.plot(f"polar_bler_vs_snr_preamble64_crc24_vs_crc16_{tag}_L1024.png")
        fig.savefig(out, dpi=300)
        plt.close(fig)
        print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot-bler", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--snrs", type=int, nargs="+", default=SNRS)
    ap.add_argument("--part", default="all")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--plot", action="store_true")
    a = ap.parse_args()
    if a.plot_bler:
        plot_bler()
        plot_bler_crc()
        raise SystemExit
    if a.merge:
        merge()
    if a.plot:
        plot()
    if not (a.merge or a.plot):
        run(a.workers, a.snrs, a.part)
