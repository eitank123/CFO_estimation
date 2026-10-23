# CFO Estimation: Classical vs. Neural Estimators and Their Impact on BER

Carrier frequency offset (CFO) estimation for QPSK bursts. The project compares classical
estimators (Mengali & Morelli, ML, 4th power) with neural ones (expert MLP, fusion network,
SNR-aware MLP, FFT-aided MLP, channel-aware NN, 8-SPS coarse NN), and measures what the residual
CFO error costs in **uncoded** and **polar-coded (CA-SCL)** BER / BLER. It finishes with a
**zero-overhead burst receiver**: no preamble and no CP, with the CFO estimated blind and from the code.

The README has two parts that use **different channels**. Numbers from one part cannot be compared with the other:

| | Channel | Where the code and results live |
|---|---|---|
| **[Part A: AWGN](#part-a-awgn-channel)** | full Tx/Rx chain (RRC, CFO before the matched filter, AWGN), [A.1](#a1-signal-model-the-full-txrx-chain-txrx_chainpy); legacy sections symbol-rate ([A.0](#a0-status-full-txrx-chain-vs-legacy-results)) | main folder, plus `multipath/results_zo_awgn/`, `multipath/results_zo2_awgn*` (the `--channel awgn` runs) |
| **[Part B: Multipath](#part-b-multipath-channel-3-tap-rayleigh)** | 3 symbol-spaced Rayleigh taps (0 / −3 / −6 dB), block fading | `multipath/`, results in `multipath/results_*multipath*` |
| **[Part C: Conclusions](#part-c-conclusions-stage-4)** | both, side by side | |

Every multipath script takes `--channel awgn` and then reduces exactly to the AWGN model of
Part A, so the switch back is instant. Those AWGN runs are reported in Part A and validated against it.

**Bottom line**
* **AWGN, full Tx/Rx chain (A.1–A.5, verified).** A CFO of up to 0.2 Rs before the matched filter costs every
  receiver, even a Genie, up to 1.25 dB plus ISI, so all estimators sit at ≈ 1.12–1.17× the ideal CRB. ML is the
  best and cheapest estimator. The chain-retrained SNR-aware NN is 27× better than M&M at −5 dB but 2–8 % worse
  from −2 dB up, and in BLER the two are equal (R = 1/2) or M&M is 0.1 dB better (R = 1/4). A 128-symbol estimate
  leaves an error floor (BLER cliff at |e| ≈ 1e-4). Only a low-rate code at Es/N0 ≈ −4 dB would profit from the
  NN (its RMSE 5.3e-4 vs M&M 1.75e-3).
* **AWGN, zero-overhead receiver (A.7–A.8).** Blind 4th-power CFO estimation plus CRC selection of
  the ambiguity works, but only above the estimator's threshold (Es/N0 ≈ 3–4 dB). That costs 1.9 dB
  (R = 1/2) and 5.5 dB (R = 1/4) against a known CFO at BLER 1e-2.
* **Multipath (Part B).** Data-aided estimators that ignore the channel lose a lot; the joint CFO + taps
  ML (MP-ML) restores them at 3× the cost of ML, and an NN adds nothing over it. The blind
  zero-overhead receiver hits a **BLER floor of ≈ 0.45**, because the 4th-power estimate fails under ISI.
* **Low rates, SNR axis (A.9, study `lowrate/`).** With the CFO estimated on 128 known symbols, NN and M&M cannot
  reach BLER 1e-2 below −3.7 dB at any rate: the 128-symbol CRB itself is too large there. An **NN + CRC search**
  (re-decode on a CFO grid around the NN estimate when the CRC fails) reaches the known-CFO curve at every rate: BLER
  < 1e-2 with R = 0.1 from −5 dB, 1/4 from −1.1 dB, 1/2 from 2.8 dB.
* **Stage 3 neural coarse estimator (8 SPS).** It learns the CFO cell, which is impossible at symbol rate.
  But as the first block of the receiver it is **worse than the classical 4th power + CRC in both channels**:
  +1.2 dB at BLER 1e-2 in AWGN and a higher floor in multipath, at ≈ 500× the MACs of the 4th-power stage
  ([A.8](#a8-stage-3-neural-coarse-cfo-estimator-8-sps), [B.5](#b5-stage-3-neural-coarse-estimator-in-multipath),
  [Part C](#part-c-conclusions-stage-4)).

---

## Repository layout

The Python code, `README.md` and `progress.txt` are in the project root. Every other file is in a folder by type,
and the scripts write there automatically (`paths.py`):

| Folder | Contents |
|---|---|
| `models/` | trained networks (`.pth`) |
| `results/` | simulation results and caches (`.npy`, `.npz`) |
| `logs/` | run logs, Run:ai job output `run_<job>.out`, progress files |
| `jobs/` | Run:ai job scripts (`.sh`) |
| `docs/` | the M&M paper |
| `plots/bler/`, `plots/ber/` | BLER and BER plots (vs Eb/N0, vs CFO error, uncoded BER) |
| `plots/mse/` | CFO MSE and MSE/CRB plots |
| `plots/outage/` | CFO outage probability |
| `plots/training/` | training curves |
| `plots/operating_points/` | highest code rate with BLER < 1e-2 vs SNR |
| `tests/` | `python -m pytest tests -q` (run as a Run:ai job): low-rate study tests |
| `lowrate/` | study A.9 (`CFO_STUDY=lowrate`): `results/`, `logs/`, `plots/bler/`, `plots/operating_points/`, `verification.txt` |
| `est256/`, `packet256/` | the 256-symbol studies (same layout) |
| `multipath/` | Part B, with its own `results_*` folders (unchanged) |

| File | What it does |
|---|---|
| `paths.py` | Folder of every file type; `paths.plot(name)` picks the plot sub-folder from the file name |
| `verify_lowrate.py` | Consistency / theory checks of the low-rate study → `lowrate/verification.txt` |
| `config.py` | Global parameters (SPS = 8, RRC β = 0.25 / span 10, preamble L = 128, `MAX_CFO` = 0.2, SNR grid, run flags) |
| `channel.py` | Root-raised-cosine filter design |
| `main.py`, `plots.py` | Original Tx/Rx chain (upsample → RRC → CFO → AWGN → matched filter → downsample), MSE-vs-SNR / CFO-sweep / histogram experiments |
| `NN_model.py` | Training of the Phase-1 expert MLP (`best_cfo_model_L64.pth`) |
| `Hybrid.py` | Expert MLP, M&M, fusion network ("Model A"), `UnifiedHybridCFOEstimator` (`unified_hybrid_cfo_model.pth`) |
| `txrx_chain.py` | **The full Tx/Rx chain of `main.py`, vectorised**: used by every AWGN simulation and training set |
| `train_snr_nn.py` | SNR-aware MLP, CRB-normalised loss; data from the full chain (`snr_aware_cfo_model_L64_chain150.pth`; symbol-rate legacy `snr_aware_cfo_model_L64.pth`) |
| `train_nofft_nn.py` | FFT-free variants of the FFT-aided NN (`plain`, `unwrap`) |
| `train_fft_nn.py` | FFT-aided MLP (residual on the FFT bin), the ML estimator, complexity table (`fft_nn_residual_cfo_model_L64.pth`) |
| `plot_mse_crb_awgn.py` | MSE/CRB or MSE vs Es/N0 of selected estimators on the full chain (`--est`, `--metric`, `--beta`) |
| `train_fft_nn_long.py` | FFT-aided MLP, M&M and ML on a 512-symbol known sequence (`fft_nn_residual_cfo_model_seq512.pth`) |
| `train_cfo_v2.py` | NN v2: ML estimate + light correction MLP (A.10, `cfo_v2_light32.pth`) |
| `train_cfo_v3.py` | Split pilots: positions, split CRB, lobe spacing, split-pilot ML estimator, `make_z` (A.13) |
| `cfo_split_mse.py` | CFO MSE of the split-pilot ML, 512 / 1024 symbols, and the CFO MSE vs SNR figure (A.13) |
| `train_cfo_split_nn.py` | Split-pilot NN without an ML front end: architectures, training, paired evaluation (A.15, A.15.1; `cfo_split_nn_L{512,1024}.pth`) |
| `plot_search_step.py` | BLER vs CFO error at 512 / 1024 symbols: why the CRC-search step is 1.5e-4 · 512/N (A.9) |
| `adaptive_rate.py` | Adaptive-rate switch points (A.12) |
| `ber_experiment.py` | Uncoded BER: 128-symbol preamble + payload through the full RRC chain |
| `polar.py` | Polar encoder + CRC-aided SCL decoder (batched NumPy, `decode(..., return_info=True)` also returns CRC flag and path metric) |
| `polar_ber_experiment.py` | Coded BER/BLER of a 512-symbol polar packet through the full chain: per estimator (Genie, SNR-aware NN, M&M) vs Eb/N0, and vs fixed CFO error |
| `job_progress.py` | Progress bars of every run (local or Run:ai) → `progress.txt` (replaces the removed `watch_jobs.py`) |
| **`multipath/`** | **Everything in Part B and the zero-overhead receiver (Stages 1–3)** |
| `multipath/multipath_cfo.py` | Data-aided M&M / ML / FFT-NN under multipath, L = 128 and 512 (`--channel awgn` / `multipath`) |
| `multipath/mp_cfo_v2.py` | Channel-aware estimators: MP-ML (joint CFO + taps) and MP-NN |
| `multipath/zero_overhead_rx.py` | Stage 1: zero-overhead receiver on AWGN (blind 4th power + CRC, code-aided refinement) |
| `multipath/zero_overhead_mp.py` | Stage 2: the same receiver with equalization (BCJR-MLSE / block MMSE, CMA or strongest-tap init, joint CFO + taps loop). `--channel awgn` reduces it to Stage 1. `--nn` adds the Stage 3 receivers |
| `multipath/coarse_nn.py` | Stage 3: 8-SPS neural coarse CFO estimator (front end, model, training, stand-alone evaluation) |
| `multipath/cluster.py` | Push / submit / sync helper for the Run:ai cluster (`bhn20`) |

---

# Part A: AWGN channel

## A.0 Status: full Tx/Rx chain vs. legacy results

**Every AWGN simulation now runs through the full Tx/Rx chain of `main.py`** (`txrx_chain.py`, A.1). There
is no symbol-rate shortcut. Sections not yet redone in the chain are marked **legacy (symbol-rate model)**.
Their *relative* conclusions still hold, but their absolute numbers are optimistic: the matched-filter loss of a
large CFO is missing.

| Section | Channel model | Status |
|---|---|---|
| A.3 estimators: MSE plots, SNR-aware NN | full chain | verified, retrained (A.3.2) |
| A.4 uncoded BER | full chain (`main.py` functions) | unchanged, estimators trained on the symbol-rate model |
| A.5 polar BER/BLER vs Eb/N0 and vs CFO error | full chain | verified, rerun |
| A.6 512-symbol estimation | symbol-rate | legacy |
| A.7–A.8 zero-overhead receiver, 8-SPS coarse NN | symbol-rate (A.8: idealised 8-SPS front end) | legacy |

## A.1 Signal model: the full Tx/Rx chain (`txrx_chain.py`)

QPSK symbols → upsample ×8 → RRC (β = `config.BETA` = 0.25 unless stated, span 10) → **CFO per sample, before
the matched filter**, ε ~ U[−0.2, 0.2] cycles/symbol, random carrier phase → AWGN with Es/N0 per symbol
(Es measured per frame as `main.apply_awgn`) → matched RRC → remove the filter delay → downsample.
The CRB is the data-aided bound var(ε̂) ≥ 3 / (2π² · SNR · L(L²−1)) (= `main.compute_cfo_crlb`).

**Verification of the chain** (independent checks, all passed):

| Check | Result |
|---|---|
| Vectorised chain vs `main.py` per-frame functions, same noise samples (ε = 0.137, 3 dB) | max difference 1.6e-15 |
| RRC: unit energy, Nyquist | energy 1.000000, raised cosine 1 at 0, ≤ 6.7e-3 at kT |
| Noise at the symbol instants (−5 and +10 dB) | variance 3.165 vs 1/SNR = 3.162; 0.10005 vs 0.1; lag-1 correlation ≤ 6e-3 |
| CFO phase reference of r[n] = 2πε(n + 5) + φ, matched-filter gain G(ε) = Σ h²[k] cos(2πεk/8) | measured 1.0000 / 0.9584 / 0.8686 vs theory 1.0000 / 0.9588 / 0.8684 at ε = 0 / 0.1 / 0.2, no phase error |
| Polar Genie with the CFO forced to 0 vs the old pure-AWGN Genie | 2.25e-3 vs 2.08e-3 (R=1/2, 2 dB), 2.48e-2 vs 2.42e-2 (R=1/4, 1 dB), within Monte-Carlo noise |
| BLER-vs-CFO-error run at e = 0 vs BLER-vs-Eb/N0 Genie (same seeds), 8 points | agree within Monte-Carlo noise (e.g. 5.57e-3 vs 5.65e-3, R=1/2, 3 dB) |
| ML vs brute-force periodogram (1e-5 grid); M&M vectorised vs `main.py` | median 3.1e-6; 5.9e-9 (float32 rounding) |
| Bias of M&M and SNR-aware NN across the CFO range (5 dB) | ≤ 4e-6, i.e. ≤ 3 % of √CRB |

**Consequence of the chain**: a CFO of up to 0.2 Rs shifts the signal partly out of the matched filter:
amplitude G(0.2) = 0.87 (−1.25 dB) plus ISI. Every receiver pays this, including a Genie that knows the CFO.
Genie BLER, R = 1/2 at Eb/N0 = 2.5 dB, at a fixed CFO: 0 (ε = 0 and 0.05), 1e-3 (0.1), 2.9e-2 (0.15),
0.37 (0.2). Averaged over ε ~ U[−0.2, 0.2] this gives 4.3e-2, against 3e-5 without the filter loss.

## A.2 How to run

```bash
python train_snr_nn.py --init snr_aware_cfo_model_L64.pth --tag _chain --epochs 40 --threads 8 --producers 7   # retrain on the chain
python plot_mse_crb_awgn.py                                                   # MSE/CRB: FFT-NN vs ML vs M&M
python plot_mse_crb_awgn.py --est "SNR-aware NN" "M&M" --metric mse --out mse_snr_aware_vs_mm_awgn.png
python plot_mse_crb_awgn.py --est "SNR-aware NN" "M&M" --metric mse --beta 0.5 --out mse_snr_aware_vs_mm_awgn_beta0p5.png
python polar_ber_experiment.py --mode ebn0  --workers 16 --min-errors 500 --max-frames 100000
python polar_ber_experiment.py --mode error --workers 16 --min-errors 1000 --max-frames 200000
python polar_ber_experiment.py --mode error --plot-only                       # redraw (RMSE lines cached in cfo_rmse_chain.npz)
python ber_experiment.py --frames 4000 --payload 1024                         # uncoded BER (A.4)
python job_progress.py                                                        # progress bars → progress.txt
```

Long runs go to Run:ai (16 cores) with `multipath/cluster.py`. `OMP_NUM_THREADS=1` in multi-process scripts.

## A.3 CFO estimators (known 128-symbol sequence)

| Estimator | How it works | Real MACs / estimate | Params |
|---|---|---|---|
| **M&M** (Mengali & Morelli) | Lag correlations R(m), m = 1..64; weighted sum of the phase increments arg(R(m)R*(m−1)) | 24,704 | 0 |
| **ML** | 256-point FFT periodogram peak + 2 Newton steps | **7,168** | 0 |
| **Expert NN** | MLP 256→128→64→32→1 (GELU) on [Re, Im, \|·\|, arg] of R(m) | 67,488 | 43,265 |
| **Fusion** ("Hybrid") | Expert NN + M&M; a small net outputs w, estimate = w·NN + (1−w)·M&M | 70,448 | 46,086 |
| **SNR-aware NN** | Expert MLP + true SNR input, loss = error² / CRB(SNR); **retrained on the full chain** (A.3.2) | 67,616 | 43,393 |
| **FFT-aided NN** | SNR-aware MLP + 8 periodogram-peak features; residual on the FFT bin | 72,736 | 44,417 |

**M&M is implemented exactly as in the paper** (Mengali & Morelli 1997, eqs. (3), (8), (9); N = L₀/2 = 64). All
four copies in the repo agree, and the vectorised version equals `main.py`'s to 6e-9 (float32 rounding).
The only difference: the paper's own simulations use the multiplication-free R̄(m) of its eq. (10); we use the
exact R(m) of eq. (3), which is better, e.g. MSE/CRB 15 vs 114 at Es/N0 = −5 dB (symbol-rate check). The paper's
axis is Eb/N0 = Es/N0 − 3 dB; it shows results only from Eb/N0 = 0 dB (Es/N0 = 3 dB) up.

**MSE/CRB on the full chain** (β = 0.25). M&M, ML, FFT-aided NN: 1,000,000 frames per point at ≤ −3 dB and
100,000 above ([`mse_over_crb_awgn.png`](plots/mse/mse_over_crb_awgn.png)). SNR-aware NN: the same frame counts
(`mse_snr_aware_vs_mm_awgn.png`). Expert and Fusion: the 20,000-frame test of `train_snr_nn.py`.

| Es/N0 (dB) | −5 | −4 | −3 | −2 | 0 | 5 | 10 |
|---|---|---|---|---|---|---|---|
| ML | **1.39** | **1.15** | **1.15** | **1.14** | **1.13** | 1.14 | 1.17 |
| FFT-aided NN (symbol-rate trained) | 1.40 | 1.19 | 1.18 | 1.17 | 1.15 | 1.14 | 1.14 |
| SNR-aware NN (retrained on the chain) | 4.08 | 1.70 | 1.36 | 1.28 | 1.20 | 1.16 | 1.16 |
| Fusion | 7.7 | 1.40 | 1.28 | 1.20 | 1.18 | 1.12 | 1.13 |
| Expert NN | 7.3 | 1.71 | 1.52 | 1.41 | 1.34 | 1.32 | 1.66 |
| M&M | 109 | 16.3 | 2.55 | 1.26 | 1.15 | **1.13** | **1.12** |

* **In the full chain no estimator reaches the CRB**: all sit at ≈ 1.12–1.17 × CRB from −2 dB up. That is the
  matched-filter loss of A.1, and the CRB here is the ideal one, without filter loss.
* **ML is the best estimator at every SNR up to ≈ 3 dB** and the cheapest (7.2k MACs). M&M is marginally best from
  4 dB (1–3 %, invisible in BER/BLER). **M&M breaks down below −3 dB** (×109 the CRB at −5 dB).
* **The MSE at −5 / −4 dB is outlier-dominated**: the 20 worst of 100,000 trials carry 45–80 % of the MSE, and a
  100,000-trial MSE varies ×2.5 between seeds. Hence 10⁶ trials there. The "1e-5" M&M MSE at −5 dB of the original
  `main.py` plots is this full-chain regime: 2.5e-5 at β = 0.25, 1.1e-5 at β = 0.5.

### A.3.1 The FFT-aided NN in detail (`train_fft_nn.py`, checkpoint `fft_nn_residual_cfo_model_L64.pth`)

**Idea.** The lag-correlation features the earlier NNs use break down at low SNR, the same threshold as
M&M. The periodogram peak (the ML coarse estimate) does not. So the network gets the FFT peak and its
neighbourhood, and only learns a **residual inside the peak bin**.

**Inputs** (computed from z[n] = r[n]·s*[n], n = 0..127, which removes the known QPSK symbols): **265 values**
| Group | Size | What |
|---|---|---|
| Lag features | 64 × 4 = 256 | R(m) = (1/(L−m)) Σ_n z[n]·z*[n−m], m = 1..64 (M = L/2 lags, as M&M); for each lag [Re R(m), Im R(m), \|R(m)\|, arg R(m)] |
| SNR | 1 | true Es/N0 in dB, scaled as (SNR − 2.5)/7.5, so [−5, 10] dB maps to [−1, 1] |
| FFT features | 8 | X = FFT₂₅₆(z), peak bin k searched over \|f\| ≤ 0.2: [f_c/0.2, \|X[k−1]\|/L, \|X[k]\|/L, \|X[k+1]\|/L, Re/Im(X[k−1]X*[k]/\|X[k]\|²), Re/Im(X[k+1]X*[k]/\|X[k]\|²)]: the coarse frequency, the peak and neighbour magnitudes, and the neighbour-to-peak complex ratios that bin interpolators use |

**Architecture.** MLP 265 → 128 → 64 → 32 → 1, GELU activations, **44,417 parameters**.
**Output**: ε̂ = f_c + (1 bin) · MLP(·), with one bin = 1/256 cycles/symbol. The last layer is zero-initialised,
so training starts exactly at the FFT-peak estimate.

**Training** (legacy: symbol-rate model, not retrained). ε ~ U[−0.2, 0.2], Es/N0 ~ U[−6, 11] dB, batch 1024 ×
500 steps × 150 epochs, AdamW (3e-4, cosine decay), loss = mean(error² / CRB(Es/N0, 128)). It still transfers
to the full chain (table above: within 1–3 % of ML).

**Complexity per estimate** (real multiply-accumulates; 1 complex MAC = 4 real):
| Part | real MACs |
|---|---|
| 64 lag correlations (direct, Σ_{m=1..64}(128−m) = 6,112 complex MACs) | 24,448 |
| FFT 256 (radix-2, 1,024 complex MACs) | 4,096 |
| MLP (265·128 + 128·64 + 64·32 + 32·1) | 44,192 |
| **Total FFT-aided NN** | **72,736** |
| ML (FFT 256 + 2 Newton steps × 3 sums over 128) for comparison | 7,168 |
| M&M (64 lag correlations + weighted phase sum) for comparison | 24,704 |

So the FFT-aided NN costs **10× ML** and **2.9× M&M**, plus 44k stored weights, and needs the SNR.
Removing its 8 FFT features gives exactly the SNR-aware NN's input. An FFT-free variant that replaces the
FFT peak by a lag-doubling phase-unwrapping coarse estimate (`train_nofft_nn.py`, `unwrap`) matched the
FFT-aided NN in validation (mean MSE/CRB 1.022 vs 1.035; legacy symbol-rate, 5,000 trials per point).

![MSE/CRB, AWGN, full chain](plots/mse/mse_over_crb_awgn.png)

### A.3.2 SNR-aware NN, retrained on the full chain (`train_snr_nn.py`)

* **Input**: the 64 × 4 lag features + SNR (257 values). **Architecture**: MLP 257 → 128 → 64 → 32 → 1 (GELU),
  43,393 parameters, 67,616 real MACs per estimate (lags 24,448 + MLP 43,168).
* **Training data**: `make_z` now draws every batch from the full chain (`txrx_chain.known_sequence`), ε ~ U[−0.2, 0.2],
  Es/N0 ~ U[−6, 11] dB, loss = error²/CRB. Fine-tuned from the symbol-rate model: 40 epochs, then 150 more
  (500 × 1024 frames per epoch, AdamW 3e-4 cosine; Run:ai, 16 cores, 7 data-producer processes, ≈ 25 min).
  Checkpoint `snr_aware_cfo_model_L64_chain150.pth`; the symbol-rate one is kept as `snr_aware_cfo_model_L64.pth`.
* Effect of retraining (MSE/CRB on the chain, β = 0.25): **≈ 12 → 4.1 at −5 dB**, ≈ 2.7 → 1.70 at −4 dB,
  1.26 → 1.20 at 0 dB.

**MSE vs SNR, SNR-aware NN vs M&M, with the CRB** ([`mse_snr_aware_vs_mm_awgn.png`](plots/mse/mse_snr_aware_vs_mm_awgn.png)
roll-off 0.25, [`mse_snr_aware_vs_mm_awgn_beta0p5.png`](plots/mse/mse_snr_aware_vs_mm_awgn_beta0p5.png) roll-off 0.5;
10⁶ frames per point at ≤ −3 dB, 10⁵ above; × = MSE/CRB):

| Es/N0 | −5 | −4 | −3 | −2 | 0 | 10 dB |
|---|---|---|---|---|---|---|
| SNR-aware NN, β = 0.25 | **9.3e-7** (4.1×) | **3.1e-7** (1.7×) | **2.0e-7** (1.36×) | 1.47e-7 | 8.7e-8 (1.20×) | 8.4e-9 (1.16×) |
| M&M, β = 0.25 | 2.5e-5 (109×) | 3.0e-6 (16×) | 3.7e-7 (2.6×) | **1.45e-7** | **8.3e-8** (1.15×) | **8.1e-9** (1.12×) |
| SNR-aware NN, β = 0.5 | **5.8e-7** (2.5×) | **2.6e-7** (1.45×) | **1.85e-7** (1.28×) | 1.40e-7 | 8.3e-8 (1.15×) | 8.1e-9 (1.12×) |
| M&M, β = 0.5 | 1.1e-5 (48×) | 1.1e-6 (6.2×) | 2.0e-7 (1.40×) | **1.29e-7** | **7.9e-8** (1.10×) | **7.8e-9** (1.07×) |
| CRB | 2.3e-7 | 1.8e-7 | 1.45e-7 | 1.15e-7 | 7.2e-8 | 7.2e-9 |

* The SNR-aware NN is **27× (β = 0.25) / 19× (β = 0.5) better than M&M at −5 dB** and ≈ 10× / 4× at −4 dB.
  From −2 dB up M&M is 2–8 % better.
* β = 0.5 widens the matched filter, so less of the frequency-shifted signal is lost: every estimator moves
  closer to the CRB (M&M 1.07–1.10× from 0 dB up, vs 1.12–1.15× at β = 0.25), and M&M's breakdown is ≈ 2.5× milder.

## A.4 Uncoded BER (`ber_experiment.py`)

128-symbol preamble + 1024 (or 256) payload symbols through the full RRC chain, random phase;
de-rotate with the CFO estimate, phase from the preamble, hard QPSK decisions. (Estimators here are the
symbol-rate-trained versions.)

| Es/N0 | QPSK theory | Genie | Known CFO | Hybrid | ML | FFT-aided NN |
|---|---|---|---|---|---|---|
| 0 dB, P=1024 | 0.159 | 0.160 | 0.174 | 0.313 | 0.311 | 0.314 |
| 10 dB, P=1024 | 7.8e-4 | 8.0e-4 | 3.0e-3 | 4.2e-2 | 4.4e-2 | 4.3e-2 |
| 10 dB, P=256 | 7.8e-4 | 8.2e-4 | 3.0e-3 | 4.8e-3 | 4.9e-3 | 4.8e-3 |

With a long payload all estimators give the same BER, far above Known CFO: over 1024 symbols even a
CRB-level error rotates the phase by ~0.6 rad at 10 dB. The payload length, not the estimator, sets the BER.

## A.5 Polar-coded BER / BLER, full chain (`polar.py`, `polar_ber_experiment.py`)

**Code and decoder.** 512 QPSK symbols = one polar codeword, N = 1024 coded bits. R = 1/2 (512 data bits +
CRC-11) and R = 1/4 (256 + CRC-11); R = 1/10 (102 + CRC-11) only in the CFO-error sweep. 5G NR CRC, PW
construction, fixed random interleaver. CA-SCL, list 8, min-sum, rate-0 shortcut, batched float32.
**Eb/N0** counts the CRC as overhead: Es/N0 = Eb/N0 + 10·log10(A/512) (R = 1/2: equal; R = 1/4: −3.01 dB;
R = 1/10: −7.01 dB).

**Channel and receiver.** Every packet goes through the full chain (A.1) with its own random ε ~ U[−0.2, 0.2] and
phase. The CFO estimate ε̂ comes from the source:
* **Genie**: ε̂ = ε (true CFO; still pays the matched-filter loss).
* **SNR-aware NN** (chain-trained) and **M&M**: estimated on the packet's first 128 received symbols, treated as
  known (a 128-symbol training sequence), same chain and noise as the data.
* **CFO-error sweep**: ε̂ = ε + e for a fixed |e| with random sign.

The packet is de-rotated by ε̂ with the phase reference exact at the packet centre, so the residual phase is
2π(ε − ε̂)(n − 255.5). Then LLRs → de-interleave → CA-SCL. All sources see the same data, CFO, phase and noise.

**BLER vs Eb/N0** ([`polar_bler_vs_ebn0_R0p5.png`](plots/bler/polar_bler_vs_ebn0_R0p5.png), [`_R0p25.png`](plots/bler/polar_bler_vs_ebn0_R0p25.png), [`polar_ber_vs_ebn0.png`](plots/ber/polar_ber_vs_ebn0.png);
up to 100,000 frames and ≥ 500 errors per point; `polar_results_ebn0_chain.npy`):

| Eb/N0 for BLER | 0.3 | 0.1 | 0.03 | 0.01 | 1e-3 |
|---|---|---|---|---|---|
| R=1/2 Genie | 1.62 dB | 2.18 dB | 2.59 dB | 2.86 dB | 3.33 dB |
| R=1/2 SNR-aware NN | 2.08 | 2.83 | 3.52 | 4.09 | 5.16 |
| R=1/2 M&M | 2.08 | 2.82 | 3.49 | 4.06 | 5.12 |
| R=1/4 Genie | 0.82 | 1.31 | 1.74 | 2.03 | 2.56 |
| R=1/4 SNR-aware NN | 1.51 | 2.45 | 3.26 | 4.03 | 5.13 |
| R=1/4 M&M | 1.44 | 2.37 | 3.20 | 3.94 | 5.10 |

Both rates are simulated over Es/N0 −5 … 10 dB (both packet lengths). Points with no error in 30,000 frames
(BLER < 3.3e-5) are left out of the plots: the Genie from Es/N0 ≈ 3.75 dB (R = 1/2) and ≈ 0.5 dB (R = 1/4), the
estimators from ≈ 7.5 / 4 dB.

* **SNR-aware NN ≈ M&M**: within 0.03 dB for R = 1/2, M&M ≈ 0.05–0.1 dB better for R = 1/4 (Es/N0 −2 … 1 dB, where
  M&M's MSE is 2–8 % lower). The NN's low-SNR advantage (−5/−4 dB) is below where these codes work.
* **Both lose ≈ 0.65 dB to the Genie at BLER 0.1, growing to ≈ 1.8 dB (R = 1/2) and 2.5 dB (R = 1/4) at 1e-3.**
  The cause is the 128-symbol estimate's error, as in the legacy study. It is not the estimator: see the CFO-error sweep.
* **L = 128 packet** ([`polar_bler_vs_ebn0_R0p5_L128.png`](plots/bler/polar_bler_vs_ebn0_R0p5_L128.png),
  [`_R0p25_L128.png`](plots/bler/polar_bler_vs_ebn0_R0p25_L128.png); N = 256, A = 128 / 64, CFO estimated on the
  whole packet): both estimators lie on the Genie curve. Across 128 symbols the phase drift of the residual CFO
  is too small to matter.

**BLER vs fixed CFO error** (`polar_{ber,bler}_vs_cfo_error_R0p5.png`, `_R0p25.png`; R = 1/10 only in the table below, no plot; up to 200,000
frames and ≥ 1,000 errors per point; `polar_results_error_chain.npy`). Dotted lines: the RMSE of M&M (1.75e-3) and of
the SNR-aware NN (5.27e-4) at **SNR = Es/N0 = −4 dB**, 10⁶ frames (`cfo_rmse_chain.npz`):

| \|e\| (cycles/symbol) | 0 | 5.7e-5 | 1.0e-4 | 1.8e-4 | 3.3e-4 | 5.9e-4 | ≥ 1.1e-3 |
|---|---|---|---|---|---|---|---|
| R=1/2, Eb/N0 2.5 dB | 4.3e-2 | 4.7e-2 | 5.7e-2 | 9.9e-2 | 0.38 | 1.0 | 1.0 |
| R=1/2, Eb/N0 3.0 dB | 5.6e-3 | 6.6e-3 | 8.8e-3 | 2.2e-2 | 0.17 | 1.0 | 1.0 |
| R=1/4, Eb/N0 2.0 dB | 1.2e-2 | 1.3e-2 | 1.5e-2 | 2.5e-2 | 0.10 | 0.80 | 1.0 |
| R=1/10, Es/N0 −5 dB | 9.8e-3 | 1.0e-2 | 1.2e-2 | 1.6e-2 | 4.3e-2 | 0.35 | 1.0 |
| R=1/10, **Es/N0 −4 dB** | 1.8e-4 | 1.8e-4 | 2.2e-4 | 3.5e-4 | 1.8e-3 | 6.5e-2 | 1.0 |

* The coded BLER is flat up to |e| ≈ 5e-5 … 1e-4 and collapses within less than a factor of 10 in e; it is
  1.0 from ≈ 6e-4 (R = 1/2) to ≈ 1.1e-3 (R = 1/10). **|e| ≈ 1e-4 stays the outage threshold.**
* **At SNR −4 dB the SNR-aware NN's RMSE (5.3e-4) sits at the knee** of the R = 1/10 curve (BLER ≈ 6e-2 at
  5.9e-4). **M&M's RMSE (1.75e-3) is far past the cliff**: BLER 1. This is the one place where the NN's low-SNR
  advantage would matter, for a low-rate code operated at Es/N0 ≈ −4 dB.

## A.6 Estimating the CFO on the whole 512-symbol packet (`train_fft_nn_long.py`)

> **Legacy (symbol-rate model)**: not yet redone in the full chain; absolute numbers are optimistic (A.0).

Same packets, but the estimators see the 512 packet symbols as known (the upper bound of
decision-directed estimation). M&M with M = 256 lags; FFT-aided NN fine-tuned for L = 512 (1.03×CRB).

| Es/N0 | M&M L=128 | FFT-NN L=128 | M&M L=512 | ML L=512 | FFT-NN L=512 |
|---|---|---|---|---|---|
| −5 dB | 1.6e-3 (11.6×CRB) | 5.0e-4 (1.09) | 6.1e-5 (1.03) | 6.0e-5 (1.02) | 6.1e-5 (1.05) |
| 0 dB | 2.7e-4 (1.04) | 2.7e-4 (1.04) | 3.4e-5 (1.01) | 3.4e-5 (1.03) | 3.4e-5 (1.04) |
| 10 dB | 8.5e-5 (1.00) | 8.6e-5 (1.02) | 1.1e-5 (1.02) | 1.2e-5 (1.22) | 1.1e-5 (1.05) |

Complexity (real MACs): M&M 24,704 / 393,728 (direct) or 8,448 / 41,984 (FFT autocorrelation);
ML 7,168 / 32,768; FFT-aided NN 72,736 / 187,424 (L = 128 / 512).

Eb/N0 for a target BLER ([`polar_bler_vs_ebn0_L128_vs_L512_R0p5.png`](plots/bler/polar_bler_vs_ebn0_L128_vs_L512_R0p5.png), `_R0p25.png`):

| Code | CFO source | BLER 1e-1 | BLER 1e-2 | BLER 1e-3 |
|---|---|---|---|---|
| R=1/2 | Genie | 1.32 dB | 1.77 dB | 2.11 dB |
| R=1/2 | M&M / FFT-NN, 128 symbols | 2.06 / 2.08 | 3.30 / 3.32 | > 3.5 |
| R=1/2 | M&M / FFT-NN, 512 symbols | 1.33 / 1.33 | 1.76 / 1.76 | 2.10 / 2.10 |
| R=1/4 | Genie | 0.61 | 1.20 | 1.63 |
| R=1/4 | M&M / FFT-NN, 128 symbols | 1.80 / 1.81 | > 3.0 | > 3.0 |
| R=1/4 | M&M / FFT-NN, 512 symbols | 0.61 / 0.61 | 1.17 / 1.17 | 1.55 / 1.56 |

**With a 512-symbol estimate the error floor disappears**, with either estimator. But the receiver
does not know the 512 symbols, which is what the zero-overhead receiver below has to solve.

## A.7 Zero-overhead receiver, Stage 1: AWGN (`multipath/zero_overhead_rx.py`)

> **Legacy (symbol-rate model)**: not yet redone in the full chain (A.0).

**Packet**: the polar packet of A.5 (512 QPSK symbols, R = 1/2 or 1/4, CA-SCL L = 8), **no preamble,
no CP**, 2-symbol guard. ε ~ U[−0.2, 0.2], random phase. The receiver knows Es/N0 and has perfect timing.

**Receivers (same packets, common random numbers)**
| Receiver | What it does |
|---|---|
| Genie | true ε and φ |
| Known 512 | data-aided ML (FFT 1024 + 2 Newton) on the true 512 symbols (the known-symbol bound) |
| **Blind + CRC** (Algorithm 1) | 4th power: FFT of y⁴ (K = 2048) + 2 Newton → f0 = ν/4, φ0 from the same line. Ambiguities: CFO mod 1/4 (cells k = −1, 0, 1 inside the ±0.2 prior) and phase mod π/2. **Every (k, phase) hypothesis is decoded** (≈7.1 decodes/packet); the CRC-passing one with the best path metric wins |
| Code-aided 1/2/3 (Algorithm 2) | re-encode the decision → data-aided ML of ε, φ on it → decode again; 1–3 iterations |
| Oversampled cell (no decoding) | RRC chain at 8 SPS, cell k from the 4th-power line searched over ±0.8 Rs |

Monte Carlo: 0.5 dB Es/N0 grid, 10,000 packets per point (100,000 where BLER < 1e-2), ≥ 200 errors.
Plots: [`zo_bler_vs_ebn0.png`](multipath/results_zo_awgn/zo_bler_vs_ebn0.png),
[`zo_ber_vs_ebn0.png`](multipath/results_zo_awgn/zo_ber_vs_ebn0.png),
[`zo_cfo_metrics_R0p5.png`](multipath/results_zo_awgn/zo_cfo_metrics_R0p5.png), `zo_cfo_metrics_R0p25.png`.

**Eb/N0 for a target BLER (AWGN)**

| Code | Genie | Known 512 | Blind + CRC = Code-aided 3 | Loss vs Genie |
|---|---|---|---|---|
| R=1/2, BLER 1e-2 | 1.77 dB | 1.75 dB | 3.62 dB | 1.85 dB |
| R=1/2, BLER 1e-3 | 2.11 dB | 2.10 dB | 4.15 dB | 2.0 dB |
| R=1/4, BLER 1e-2 | 1.19 dB | 1.17 dB | 6.65 dB | 5.5 dB |
| R=1/4, BLER 1e-3 | 1.63 dB | 1.55 dB | 7.16 dB | 5.5 dB |

**CFO and ambiguity statistics (R = 1/2; R = 1/4 identical at the same Es/N0)**

| Es/N0 | 4th power (k = 0): median / P(>1e-4) | Blind + CRC | Code-aided 3 | Known 512 median | cell k wrong (CRC) | cell k wrong (oversampled spectrum) |
|---|---|---|---|---|---|---|
| 1 dB | 8.9e-2 / 0.85 | 6.6e-2 / 0.77 | 8.0e-2 / 0.80 | 2.1e-5 | 0.34 | 0.33 |
| 2 dB | 4.9e-2 / 0.65 | 8.0e-5 / 0.44 | 3.3e-5 / 0.36 | 1.8e-5 | 0.16 | 0.28 |
| 3 dB | 8.0e-5 / 0.46 | 3.8e-5 / 0.13 | 1.8e-5 / 0.06 | 1.6e-5 | 0.028 | 0.22 |
| 4 dB | 5.4e-5 / 0.39 | 2.8e-5 / 0.022 | 1.5e-5 / 0.002 | 1.5e-5 | 0.001 | 0.15 |
| 6 dB | 3.4e-5 / 0.37 | 1.8e-5 / 0.000 | 1.2e-5 / 0.000 | 1.2e-5 | 0 | 0.05 |
| 10 dB | 1.7e-5 / 0.38 | 8.8e-6 / 0.000 | 7.6e-6 / 0.000 | 7.6e-6 | 0 | 0.012 |

(The "k = 0" column stays at P ≈ 0.37 at high SNR simply because 37 % of the CFOs are in another cell.)

**Observations**
* The blind receiver is limited by the **4th-power threshold at Es/N0 ≈ 3–4 dB**, not by the code: below
  it the r⁴ line is buried (the 4th power raises the noise to the 4th order). Hence the loss is small for
  R = 1/2 (its own threshold is at ≈1.8 dB) and large for R = 1/4 (the code works from Es/N0 ≈ −2 dB).
* **CRC selection resolves the ambiguity essentially perfectly** above the threshold (cell error 1e-3 at
  4 dB, 0 above). The oversampled-spectrum cell decision is far worse (15 % wrong at 4 dB), because the
  line's symbol-rate harmonic at 4ε ± 1 is also inside the ±0.8 search window.
* **Code-aided refinement brings the CFO to the known-symbol bound** (median equal to Known 512 from
  4 dB), but gives **no BLER gain**: when the first decode succeeds the CFO is already good enough, and
  when it fails the re-encoded decision is wrong.
* **Complexity**: 4th-power stage ≈ 64k real MACs (y⁴, FFT 2048, 2 Newton); ≈7.1 CA-SCL decodes per
  packet for the hypotheses + 1 per code-aided iteration (vs. 1 for a known CFO). The decodes dominate.

## A.8 Stage 3: neural coarse CFO estimator (8 SPS)

> **Legacy**: idealised 8-SPS front end (CFO applied after the matched filter), not the `main.py` chain (A.0).

Code: `multipath/coarse_nn.py`.

The NN replaces Algorithm 1 (the 4th-power stage) as the first block of the receiver. It is trained on
AWGN and multipath together (p = 0.5); the AWGN results are here, the multipath results in [B.5](#b5-stage-3-neural-coarse-estimator-in-multipath).

**Why 8 SPS (first attempt at symbol rate failed).** The first network took the symbol-rate burst
(2 × 512) and |FFT(r⁴)|. Its cell error stayed at the prior P(k ≠ 0) = 0.37 for 40 epochs
(`results_coarse_nn/train_symrate.log`). A CFO shift of 1/4 multiplies symbol n by jⁿ, which maps a random
QPSK burst onto another equally likely QPSK burst. **At symbol rate the cell is unidentifiable: no network
can learn it.** It is the same ambiguity the 4th power has. Between the symbol instants the shift also
moves the pulse spectrum by Rs/4, so the **oversampled** matched-filter output resolves it: the 4th-power line
at 4ε is unambiguous over ±4 Rs at 8 SPS.

**Front end (`waveform`).** Symbols → symbol-spaced channel → RRC (β 0.25, span 10, 8 SPS) → + white noise →
matched RRC. The CFO rotation is applied to the signal after the matched filter (CFO small against the
filter bandwidth). The noise is the matched-filtered white noise, not rotated, so its spectrum stays at 0.
Every 8th sample is then exactly the symbol-rate burst of Stages 1–2 (checked: noise variance 0.1001 for
0.1, lag-1 correlation 1e-4), so the decoding receivers are unchanged and the NN additionally sees z8.
(Rotating the noise too would have centred the noise hump on the CFO and let the NN cheat at low SNR.)

**Inputs** (z8: 514 × 8 = 4112 samples, unit RMS)
* z8 real / imag (2 × 4112)
* |FFT₁₆₃₈₄(z8⁴)| cropped to |4ε| ≤ 0.81 (3317 bins of 1/2048 cycles/symbol), unit energy, log-compressed
* a zoom: |DTFT(z8⁴)| at the spectrum peak ν_pk ± 4 bins in quarter-bin steps (33 values), and ν_pk itself

**Architecture** (974,820 parameters)
* CNN on z8: 4 × [Conv1d(kernel 7, stride 2) + GELU], 32/32/64/64 channels, global average pooling → 64
* MLP on the spectrum 3317 → 256 → 128; MLP on the zoom 33 → 64 → 32
* head: concat(64 + 128 + 32 + 1) → 128 → 64 → 4 = 3 logits for the cell k + a residual ρ (|ρ| ≤ 4 bins)
* output: 4ε̂ = ν_pk + ρ/2048, ε_fine = 4ε̂/4 wrapped to [−1/8, 1/8), ε̂ = k/4 + ε_fine; optional
  **polish** = 2 Newton steps on the symbol-rate r⁴ periodogram from ε_fine

**Training** (on the fly, Run:ai, 16 cores, ≈25 min): polar-coded bursts (R = 1/2 or 1/4), AWGN or 3-tap
Rayleigh (p = 0.5), ε ~ U[−0.2, 0.2], φ ~ U[0, 2π), Es/N0 ~ U[−6, 11] dB; 40 epochs × 400 batches × 256.
Loss = CE(k) + 0.3 · log(1 + e²/CRB(Es/N0, 512)), with e the fine error, counted only where the peak is within
4 bins of the true line (elsewhere no residual can fix it). AdamW + OneCycle (1e-3).

**Receiver with the NN** (`zero_overhead_mp.py --nn`): hypotheses = the 2 most probable cells (inside the
prior) × 4 phase relabellings, then the same equalizer, CRC selection and code-aided loop as Algorithm 1.

**Training curve** (`results_coarse_nn/train.log`, validation 1,000 bursts per point): the cell error of the
k head fell from the prior 0.37 to **0.026 / 0.014 / 0.001 / 0.002 at Es/N0 = −5 / 0 / 5 / 10 dB (AWGN)**. The
classical oversampled-peak cell decision gets 0.28 / 0.21 / 0.002 / 0. So 8 SPS makes the cell learnable,
and the NN finds it far below the 4th-power threshold.

**Stand-alone CFO accuracy, AWGN** (`coarse_nn.py --eval`, 20,000 bursts per point,
[`coarse_nn_vs_4th_power.png`](multipath/results_coarse_nn/coarse_nn_vs_4th_power.png); P(|err| > 1e-4)):

| Es/N0 | 4th power, k = 0 | 4th power + oversampled cell | 4th power, oracle k | NN | NN + polish |
|---|---|---|---|---|---|
| 0 dB | 0.952 | 0.934 | 0.923 | 0.964 | 0.962 |
| 2 dB | 0.653 | 0.486 | 0.437 | 0.719 | 0.695 |
| 3 dB | 0.456 | 0.170 | 0.131 | 0.416 | 0.376 |
| 4 dB | 0.385 | 0.032 | 0.022 | 0.156 | 0.106 |
| 5 dB | 0.380 | 0.004 | 0.004 | 0.041 | 0.016 |
| 10 dB | 0.382 | 0.000 | 0.000 | 0.002 | 0.002 |

The NN gets the cell right, but its **fine** estimate is worse than the plain symbol-rate 4th power. At low
SNR the fine part is random inside the cell (median 0.07), because nothing can beat the r⁴ threshold. Around
the threshold, the peak of the oversampled spectrum (weaker line, plus harmonics) is a worse starting point than the
symbol-rate FFT peak, and the Newton polish only climbs to the nearest local maximum. Its 0.2 % high-SNR floor
is k-head mistakes.

**In the receiver, AWGN** (`zero_overhead_mp.py --channel awgn --nn`, 4,000–20,000 packets per point, all
receivers on the same 8-SPS packets; [`zo_bler_vs_ebn0.png`](multipath/results_zo2_awgn_nn/zo_bler_vs_ebn0.png)):

| Eb/N0 for BLER | Genie | 4th power + CRC, code-aided 3 | NN + CRC, code-aided 3 | NN loss |
|---|---|---|---|---|
| R=1/2, 1e-1 | 1.24 dB | 2.77 dB | 3.85 dB | +1.1 dB |
| R=1/2, 1e-2 | 1.73 dB | 3.56 dB | 4.81 dB | +1.25 dB |
| R=1/4, 1e-1 | 0.51 dB | 5.75 dB | 6.84 dB | +1.1 dB |
| R=1/4, 1e-2 | 1.19 dB | 6.54 dB | 7.78 dB | +1.25 dB |

Hypothesis decodes per packet: NN 5.8 (top-2 cells inside the prior × 4 phases) vs 4th power 6.9 (every valid
cell × 4 phases), both + 3 code-aided decodes. The classical numbers reproduce Stage 1 (3.56 vs 3.62 dB at
1e-2 for R = 1/2), which confirms the 8-SPS front end.

## A.9 Low code rates, SNR axis and operating points (study `lowrate/`)

**Question.** Which code rate keeps the BLER below 1e-2 at each SNR from −5 dB up, and can the NN-based receiver
decode at −5 dB? Same chain and packet as A.5 (512 QPSK symbols, N = 1024, CRC-11, CA-SCL L = 8, CFO estimated on
the first 128 symbols, treated as known). Every result is in `lowrate/` (`CFO_STUDY=lowrate`); the x axis of every
BLER plot is the **SNR = Es/N0**.

- **Rates:** R = A/1024 = 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 1/4, 1/3, 1/2, 3/4 (A = 26 … 768 data bits). The
  R = 1/4 and 1/2 points are those of A.5; R = 0.1 was extended below −5 dB.
- **Receivers:** Genie (known CFO), M&M, SNR-aware NN, plus two new ones (`polar_ber_experiment.py --sources`):
  - **CRB (ideal 128-symbol estimator):** f̂ = f + N(0, CRB), with CRB = 3 / (2π² · SNR · L(L²−1)) for L = 128. It is
    what any unbiased estimator on the 128 known symbols could do at best.
  - **SNR-aware NN + CRC search:** decode with the NN estimate; if the CRC fails, decode again on a CFO grid
    f̂ + k · 1.5e-4 (|k| ≤ 4 · 1.3 · √CRB / 1.5e-4) and keep the hypothesis that passes the CRC with the best path
    metric. The code checks the CFO on all 512 symbols, so the 128-symbol CRB no longer limits the receiver.
- **Runs:** 44 Run:ai jobs (16 cores), 300 frame errors or 30 000 frames per point, 0.5 dB steps. Figures:
  `lowrate/plots/bler/polar_bler_vs_snr_<receiver>.png`, `polar_bler_vs_snr_3rates.png`,
  `polar_bler_operating_points.png`.

**How the NN + CRC search works** (`simulate_point`, source `SEARCH`):
1. The SNR-aware NN estimates f̂ from the 128 known symbols, exactly as before. The packet is de-rotated by f̂ and
   decoded with CA-SCL (L = 8). If a list path passes the CRC-11, that decode is delivered: no extra cost.
2. If no path passes, the receiver tries the hypotheses f̂ + k·Δ, Δ = 1.5e-4 cycles/symbol, k = ±1 … ±M with
   M = ⌈4 · 1.3 · √CRB(SNR) / Δ⌉ (±4 standard deviations of the NN error; M = 17 at −5 dB, 14 at −3 dB, 3 at 10 dB).
   Each hypothesis is a de-rotation of the stored samples plus one CA-SCL decode.
   **Why Δ = 1.5e-4** (`plot_search_step.py` → `lowrate/plots/bler/polar_bler_vs_cfo_error_search_step.png`, from
   the BLER-vs-CFO-error runs, 512 symbols, CRC-11): the true CFO is at most Δ/2 = 7.5e-5 from the nearest
   hypothesis, and a CFO error of 7.5e-5 raises the BLER by only ≈ 11 % (−5 dB) / 8 % (−4 dB) over no CFO error.
   A finer step barely helps (Δ = 1e-4: +4 %) but needs 46 % more hypotheses (51 vs 35 at −5 dB); a coarser one
   loses quickly (Δ = 2e-4: +19 %; 3e-4: +48–64 %; 4e-4: ×1.9–2.4), because the BLER rises steeply above an error of
   ≈ 1e-4. The tolerance scales with 1 / packet length (the phase drift 2π·e·n grows along the packet), so the step
   is 1.5e-4 · 512/N. **Measured at 1024 symbols** (CRC-16, −5 / −4.5 dB, 450–500 errors per point,
   `lowrate/plots/bler/polar_bler_vs_cfo_error_search_step_L1024.png`): with Δ = 7.5e-5 the worst residual 3.75e-5
   costs +12 / +15 %; keeping the 512-symbol step 1.5e-4 would cost +52 / +71 %, so halving it was right.
3. Among the hypotheses whose decode passes the CRC, the one with the best (lowest) path metric is delivered. If
   none passes, the first decode stays (a block error).

**Why it "beats the CRB" (it does not really).** The CRB line is the bound for an estimator that sees only the
**128 known symbols**: √CRB = 4.8e-4 at −5 dB. The search uses the decoder as a test on **all 512 symbols**: a
hypothesis passes the CRC only if its residual CFO is within the code's tolerance (≈ 2e-4 at −5 dB). This is a
code-aided (decision-directed) estimate, and its bound is the CRB of 512 symbols, √CRB₅₁₂ = 6.0e-5 at −5 dB,
8× smaller in standard deviation (the CRB scales with 1/L³). The search does not aim at that bound either: it
only needs to land within the code's tolerance, with a grid residual of at most Δ/2 = 7.5e-5. Measured at −5 dB
(R = 1/10, 3000 frames): CFO RMSE of the NN 7.1e-4 → 4.5e-4 after the search. The overall RMSE stays large because
frames where no hypothesis passes keep the NN estimate; what matters is that the decoded frames are correct.

**Compute cost:**

| | Decodes per packet | Other |
|---|---|---|
| NN alone | 1 CA-SCL (O(L·N log N) ≈ 8 · 1024 · 10 ≈ 8·10⁴ list-node operations) | NN: 64 lag features + a small MLP |
| NN + CRC search, CRC passes | 1 | same |
| NN + CRC search, CRC fails | 1 + 2M (35 at −5 dB, 29 at −3 dB) | 2M de-rotations (O(N) each) |
| Average, measured | 1 + 10.0 (R=1/10, −5 dB), 1 + 4.2 (−4 dB), 1 + 1.6 (−3 dB); ≈ 1 at the operating points of R ≥ 1/4 | |

The average cost is 1 + 2M · BLER(NN alone): high only where the NN alone fails often. The worst-case latency is
2M + 1 decodes, so a hardware receiver must budget for 35 decodes per failing packet, or stop at the first CRC
pass (cheaper, but more undetected errors, see below).

**Undetected errors (wrong data with a passing CRC).** Every extra hypothesis is another chance for a wrong
decode to pass the 11-bit CRC. Measured at −5 dB, R = 1/10, on the same 3000 frames: Genie 0, NN alone 1.3e-3,
**NN + CRC search 2.3e-3** (of its BLER of 1.1e-2). The search therefore adds about 1e-3 undetected errors per
packet at the lowest SNR. A longer CRC (CRC-16/24) or a path-metric acceptance threshold would reduce that; CRC-16
and CRC-24 were simulated later (A.11).

**Verification.** `py verify_lowrate.py` → `lowrate/verification.txt`: **6 PASS, 0 WARN, 0 FAIL**:
- the search's BLER is never above the NN's on the same frames (243 points);
- the CRB source matches the BLER predicted from the BLER-vs-CFO-error curve: 0.212 vs 0.199 at −5 dB, 0.086 vs
  0.081 at −4 dB;
- every curve falls with SNR, and the 429 points copied from the main results are unchanged;
- required SNRs are ordered Genie ≤ CRB bound ≤ NN, M&M, with the search within 0.2 dB of the Genie.

Tests: `python -m pytest tests -q` as a Run:ai job, **6 passed** (`tests/test_lowrate.py`). They cover:
- the code grid and the CRB formula;
- the decoder's CRC flag and path metric;
- that the search beats the NN on common frames at −4 dB;
- the CRB source's error spread;
- the required-SNR interpolation.

**Why the NN alone cannot decode at −5 dB.** At −5 dB the R = 1/10 code tolerates a residual CFO of about 2e-4
(BLER 1.6e-2 at |e| = 1.84e-4, 4.3e-2 at 3.3e-4, 0.35 at 5.9e-4, A.5 sweep), but the CRB of 128 known symbols is
√CRB = 4.8e-4. Even the ideal estimator therefore gives BLER 0.21 there, and the NN (≈ 1.2× the CRB in RMSE) gives
0.30. Retraining the NN cannot close that gap; more symbols must enter the estimate, which is what the CRC search
does.

**BLER at SNR = −5 / −4 / −3 dB:**

| R | Genie | M&M | SNR-aware NN | CRB bound | **NN + CRC search** (extra decodes / frame) |
|---|---|---|---|---|---|
| 0.025 | 0 / 0 / 0 | 6.3e-2 / 1.7e-2 / 3.1e-3 | 4.6e-2 / 1.7e-2 / 4.6e-3 | 1.3e-2 / 2.9e-3 / 6.3e-4 | **1.1e-3 / 1.0e-4 / 1.0e-4** (1.7 / 0.5 / 0.1) |
| 0.05 | 0 / 0 / 0 | 9.1e-2 / 3.3e-2 / 8.6e-3 | 9.3e-2 / 3.6e-2 / 1.3e-2 | 4.3e-2 / 1.3e-2 / 3.1e-3 | **1.4e-3 / 3.0e-4 / 3.3e-5** (3.5 / 1.1 / 0.4) |
| 0.075 | 2.3e-4 / 0 / 0 | 0.16 / 6.2e-2 / 1.9e-2 | 0.18 / 7.3e-2 / 2.9e-2 | 0.11 / 3.5e-2 / 1.2e-2 | **2.3e-3 / 6.0e-4 / 1.3e-4** (6.0 / 2.3 / 0.8) |
| 0.1 | 9.4e-3 / 2.0e-4 / 0 | 0.27 / 0.12 / 4.5e-2 | 0.30 / 0.14 / 5.6e-2 | 0.21 / 8.6e-2 / 2.5e-2 | **9.4e-3 / 1.0e-3 / 3.0e-4** (10 / 4.2 / 1.6) |
| 0.15 | 0.45 / 8.8e-2 / 4.1e-3 | 0.75 / 0.40 / 0.15 | 0.76 / 0.41 / 0.17 | 0.76 / 0.35 / 0.14 | **0.41 / 6.8e-2 / 3.4e-3** (25 / 13 / 5.0) |
| 0.2 | 0.98 / 0.70 / 0.18 | 0.99 / 0.86 / 0.47 | 0.99 / 0.87 / 0.49 | 1.0 / 0.88 / 0.47 | **0.98 / 0.67 / 0.16** (34 / 26 / 14) |

(0 = no error in 30 000 frames, i.e. < 1e-4 at 95 %.)

**Required SNR for BLER < 1e-2** [dB] (the operating points; "≤ −5" = already below 1e-2 at −5 dB):

| R | Genie | **NN + CRC search** | CRB bound | M&M | SNR-aware NN |
|---|---|---|---|---|---|
| 0.025 | ≤ −5 | **≤ −5** | −4.88 | −3.68 | −3.62 |
| 0.05 | ≤ −5 | **≤ −5** | −3.82 | −3.10 | −2.82 |
| 0.075 | ≤ −5 | **≤ −5** | −2.89 | −2.45 | −2.22 |
| 0.1 | ≤ −5 | **≤ −5** | −2.34 | −1.85 | −1.53 |
| 0.15 | −3.28 | **−3.35** | −1.16 | −0.65 | −0.55 |
| 0.2 | −1.98 | **−2.07** | −0.18 | 0.14 | 0.21 |
| 1/4 | −0.98 | **−1.06** | 0.59 | 0.93 | 1.02 |
| 1/3 | 0.46 | **0.39** | 1.81 | 2.07 | 2.12 |
| 1/2 | 2.86 | **2.80** | 3.82 | 4.06 | 4.09 |
| 3/4 | 6.19 | **6.18** | 6.81 | 6.96 | 6.99 |

So, at BLER < 1e-2 with the NN + CRC search: R = 0.1 from −5 dB, 0.15 from −3.4 dB, 0.2 from −2.1 dB,
1/4 from −1.1 dB, 1/3 from 0.4 dB, 1/2 from 2.8 dB, 3/4 from 6.2 dB.

**Interpretation:**
- **The 128-symbol estimate is the bottleneck, not the estimator.** Without the search neither NN nor M&M gets
  below 1e-2 under −3.7 dB at any rate, and even the CRB-limited estimator only reaches −4.9 dB at R = 0.025. NN and
  M&M are 0.15–1.3 dB behind the CRB bound (most at the lowest rates) and close to each other (M&M 0.03–0.3 dB
  better).
- **The CRC search reaches the Genie at every rate** (within 0.1 dB, on the operating-point plot the curves
  coincide). At −5 dB it makes R = 0.1 work (BLER 9.4e-3, same as the Genie), against 0.30 for the NN alone. From
  R = 0.15 up it is even 0.01–0.09 dB *better* than the Genie: the extra decodes at nearby CFO values act as
  additional decoding attempts. An undetected wrong pass still counts as an error, so that gain is real.
- **Cost:** the search runs only when the first decode fails, so the extra decodes per frame scale with the BLER of
  the NN alone: 10 at R = 0.1 and −5 dB, below 2 once that BLER is under ~5 %, and ≈ 0 at the operating points of the
  higher rates.
- **Choice of rate:** below −3.4 dB only R ≤ 0.1 works; the step from R = 0.1 to 0.15 costs 1.7 dB, and the
  rate doubles roughly every 2–3 dB above that.

## A.10 NN v2: an ML estimator with a learned correction (`train_cfo_v2.py`, checkpoint `cfo_v2_light32.pth`)

**Why a new NN.** The SNR-aware NN of A.3.2 was 4× the CRB at −5 dB, and 2–4 % *worse* than M&M from −2 dB up. Both
problems have the same root: its only inputs are the 64 lag correlations R(m) = Σ z[n] z*[n−m] — the same
information M&M uses. Every R(m) multiplies two noisy samples *before* anything is averaged, so at low SNR the
noise × noise terms dominate, the phases of R(m) wrap, and that information is gone; a network on top cannot get it
back (threshold effect: 3e-3 of the frames outside the CRC-search window at −5 dB). And because it learns the whole
frequency mapping from scratch, it ends up slightly worse than the closed-form M&M at high SNR.

**The idea: start from the right estimator, learn only what it misses.** For one tone in white noise —
z[n] = r[n]·s*[n] = e^{j(2πfn+φ)} + noise once the known symbols are stripped — the maximum-likelihood estimator is
the peak of the periodogram |Σ z[n] e^{−j2πfn}|². The FFT adds all 128 samples *coherently* (≈ 21 dB of gain)
before the single nonlinearity (the peak search), so its threshold sits far below that of the lag products: plain
ML is already 1.8× the CRB at −5 dB with 2e-5 outliers. What ML does not capture are small effects of the real
chain (matched-filter loss and ISI at a large CFO, the finite number of Newton steps), which show up at high SNR,
where M&M is slightly better (1.12 vs 1.17 × CRB at 10 dB). So NN v2 is ML plus a small learned correction:

    f̂ = f_ML + BIN · MLP(x),        BIN = one FFT-256 bin = 1/256 cycles/symbol

- **f_ML:** FFT-256 of the 128 de-modulated pilots, peak within ±0.2 cycles/symbol, 2 Newton steps on the
  periodogram (`train_fft_nn.ml_estimate`).
- **Inputs x (11):** the SNR (as the SNR-aware NN; needed because the right correction depends on the noise level);
  (f_ML − f_FFT)/BIN, how far Newton moved from the FFT bin; **(f_M&M − f_ML)/BIN**, which lets the network lean on
  M&M where M&M is the better estimator (high SNR); and the 8 FFT-peak features of A.3.1 (coarse frequency, peak and
  neighbour magnitudes, neighbour/peak ratios), which describe how well-defined the peak is.
- **MLP:** 11 → 32 → 16 → 1, GELU; **929 parameters, 880 MACs**. The last layer is initialised to zero, so an
  untrained NN v2 *is* the ML estimator: training can only move it away from ML where that lowers the loss.
- **Loss:** squared error / CRB(SNR), so every SNR counts equally (as A.3.2). Training on the full chain: Es/N0 ~
  U[−6, 11] dB, CFO ~ U[−0.2, 0.2], 80 epochs × 500 steps × 1024 frames (41M frames), AdamW 1e-3, cosine decay.

**Architecture at a glance** (per packet; z[n] = r[n]·s*[n], n = 0..127, the 128 de-modulated pilots):

```
 z[0..127] ──► FFT-256, peak in ±0.2 ──► f_FFT ──► 2 Newton steps on |Σ z[n]e^{-j2πfn}|² ──► f_ML ───────────┐
     │                    │                                                                     │             │
     │                    └─► 8 peak features (coarse f, |peak|, |neighbours|, ratios) ─┐       │             │
     └─► M&M (lag correlations R(m), m = 1..64) ──► f_M&M                           │       │             │
                                                                                    ▼       ▼             │
   input x (11) = [ SNR, (f_ML − f_FFT)/BIN, (f_M&M − f_ML)/BIN, 8 peak features ]                        │
                                                                                                          │
   Linear 11→32 + GELU ──► Linear 32→16 + GELU ──► Linear 16→1 (zero-init) ──► Δ  (in FFT bins)           │
                                                                                                          ▼
                                                                         f̂ = f_ML + BIN · Δ,  BIN = 1/256
```

| Part | Size | Parameters | Real ops / estimate |
|---|---|---|---|
| FFT-256 of the 128 pilots + peak search | — | 0 | ≈ 10,000 |
| 2 Newton steps (1st/2nd derivative of the periodogram) | — | 0 | ≈ 4,000 |
| M&M (lag correlations, shared with the M&M estimate) | — | 0 | 24,704 |
| Layer 1 | 11 → 32, GELU | 384 | 352 |
| Layer 2 | 32 → 16, GELU | 528 | 512 |
| Layer 3 (output, zero-initialised) | 16 → 1 | 17 | 16 |
| **Total** | | **929** | **≈ 40,000** (MLP 880) |

The same NN v2 (contiguous 128 pilots at the start of the packet) is the "NN v2 + CRC search" receiver in every
BLER figure; the CRC search around f̂ is the contiguous grid (step 1.5e-4 · 512/N, nearest hypothesis first).

**Model size.** Five sizes were trained, from 209 parameters (one hidden layer of 16) to 44,673 (with the 256 lag
features as extra inputs): all five came within **0.01 × CRB** of each other at every SNR. The correction ML needs
is small and simple; the lag features add nothing once ML is the starting point. The second-smallest (929
parameters) was chosen: the smallest (209) is 0.01 worse than M&M at 10 dB.

**Result** (full chain, 1e6 frames per SNR at ≤ −3 dB, 1e5 above; `logs/cfo_v2_light32_test.json`,
`plots/mse/cfo_v2_vs_current_nn_mse_over_crb.png`):

| MSE / CRB | −5 dB | −4 | −3 | −2 | −1 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| **NN v2** | **1.80** | **1.15** | **1.14** | **1.14** | **1.13** | **1.14** | **1.12** | **1.13** | **1.12** |
| SNR-aware NN (A.3.2) | 3.90 | 1.58 | 1.39 | 1.28 | 1.24 | 1.22 | 1.18 | 1.16 | 1.16 |
| M&M | 108 | 16.6 | 2.71 | 1.28 | 1.17 | 1.16 | 1.14 | 1.13 | 1.12 |
| ML alone | 1.80 | 1.16 | 1.15 | 1.14 | 1.14 | 1.14 | 1.13 | 1.14 | 1.17 |
| Outliers (outside the CRC-search window), NN v2 / SNR-aware NN | 2e-5 / 3e-3 | 1e-5 / 8e-4 | 7e-6 / 3e-4 | 0 / 5e-5 | | | | | |

NN v2 is equal to or better than M&M at every SNR and 2.2× better than the old NN at −5 dB, with 150× fewer
outliers. **Most of the gain comes from the ML front end, not from the network**: up to 5 dB NN v2 and plain ML are
the same; the network's contribution is to bring ML down to M&M at high SNR. The ≈ 1.13 × CRB floor is the full
chain (matched-filter loss / ISI at a large CFO), which every estimator pays. Cost: ≈ 40,000 real operations per
estimate (M&M's lag correlations, as an input, 24.7k; FFT-256 ≈ 10k; Newton ≈ 4k; MLP 0.9k), against 67.6k for the
old NN, and below one CA-SCL decode (82k at 512 symbols).

## A.11 CRC search: first pass vs full search, CRC length and packet length (study `lowrate/`)

**The two search variants** (both start only when the first decode fails its CRC; grid f̂ + k·Δ as in A.9):
- **Full search:** decode every hypothesis and deliver the CRC pass with the best path metric. Worst case
  1 + 2M decodes per packet.
- **First pass:** try the hypotheses nearest-first (±1, ±2, …) and deliver the first one that passes the CRC.
  Much cheaper on average, but a wrong codeword that passes the CRC is delivered as soon as it is met, so it has more
  undetected errors (wrong data with a passing CRC). With a 11-bit CRC and list size 8 a wrong decode passes with
  probability ≈ 8 · 2⁻¹¹ ≈ 4e-3, with CRC-16 ≈ 1.2e-4.
- **M/2** (half the grid width) was also tested and dropped: it loses BLER without saving much over first pass.

**Receivers and configurations.** Standard set: R = 1/10, 512-symbol packet with CRC-11 and CRC-16, 1024-symbol
packet with CRC-16 (same data rate: A = 102 / 205 data bits). The CRC bits are carried by the polar code (K = A + C),
so a longer CRC makes the code itself slightly weaker. Each point has ≥ 30–100 frame errors (except where noted).

| BLER (decodes / packet) | M&M + CRC, first pass | NN v2 + CRC, first pass | NN v2 + CRC, full search |
|---|---|---|---|
| 512, CRC-11, −5 dB | 5.7e-2 (3.7) | 9.3e-3 (2.2) | 7.9e-3 (9.3) |
| 512, CRC-11, −3 dB | 1.4e-3 (1.1) | 4.6e-4 (1.1) | 1.5e-4 (2.1) |
| 512, CRC-11, −1 dB | 2.5e-5 (1.0) | 2.1e-5 (1.0) | 8.7e-6 (1.1) |
| 512, CRC-16, −5 dB | 4.4e-2 (3.6) | 1.5e-2 (2.7) | 1.3e-2 (10.1) |
| 512, CRC-16, −3 dB | 8.8e-4 (1.2) | 2.3e-5 (1.1) | 9.2e-6 (2.2) |
| 512, CRC-16, −1 dB | 2.6e-6 (1.0) | 8.3e-7 (1.0) | 4.8e-7 (1.1) |
| 1024, CRC-16, −5 dB | 3.5e-2 (8.7) | 3.3e-3 (6.2) | 2.7e-3 (38.4) |
| 1024, CRC-16, −3 dB | 1.0e-3 (3.0) | 2.6e-4 (2.8) | 5.3e-5 (16.7) |
| 1024, CRC-16, −1 dB | 1.0e-4 (1.6) | 1.0e-4 (1.5) | 1.6e-5 (6.0) |

**What this shows:**
- **The CRC search is the big gain.** At −4 dB (512, CRC-11): M&M alone 0.12 → M&M + CRC 8.1e-3; NN v2 alone 0.11 →
  NN v2 + CRC 1.6e-3. At −5 dB the NN receivers are at the known-CFO BLER (9.3e-3 vs 9.8e-3): the code, not the CFO,
  limits them there.
- **Above ≈ −4 dB almost all remaining errors are undetected** (85–100 % of the BLER with first pass). The first
  decode fails because the 128-pilot estimate misses the code's CFO tolerance; each extra hypothesis is another
  chance for a wrong codeword to pass the CRC. Full search removes part of them by keeping the best path metric:
  2–3× lower BLER from −3.5 dB up at 512, 3–6× at 1024, at 2–9× the decodes (1024: 17 decodes at −3 dB).
- **For M&M, full and first pass give the same BLER with CRC-16** (curves coincide in
  `polar_bler_vs_snr_full_vs_first_pass_R0p1_C16.png`): with a 16-bit CRC there is rarely more than one pass to
  choose from, so full search only adds decodes (11.7 vs 3.6 at −5 dB).
- **CRC-16 vs CRC-11 (512).** CRC-16 is worse at −5 dB even with a known CFO (2.0e-2 vs 9.8e-3: 5 more bits under
  the same codeword, ≈ 0.2 dB) and better from ≈ −4 dB up, where CRC-11's false passes dominate (NN v2 first pass
  at −3 dB: 2.3e-5 vs 4.6e-4). CRC-24 (previous NN, full search, fewer frames) had **0 undetected errors** in every
  run but costs another ≈ 0.3 dB at −5 dB (3.5e-2 vs 1.7e-2 at 512); it wins only from ≈ −3 dB (512) / −4 dB (1024).
- **1024 vs 512 symbols.** At −5 dB the 1024-symbol packet is 3–5× better (known CFO: 4.5e-3 vs 2.0e-2 with CRC-16):
  a 2048-bit polar code polarises better (fewer partly-polarised bit channels), and the CRC is a smaller share of K.
  At high SNR it is worse (first pass floors at ≈ 1e-4 … 4e-5): the CFO tolerance halves (the residual phase drifts
  over twice as many symbols) while the 128-pilot estimate does not improve, so the first decode fails more often
  (57 % vs 26 % at −5 dB) and the grid is twice as wide (M = 34 vs 17) — hence 6.2 vs 2.7 decodes per packet.

Figures (`lowrate/plots/bler/`): `polar_bler_vs_snr_R0p1.png`, `polar_bler_vs_snr_R0p1_C16.png`,
`polar_bler_vs_snr_best_option_L1024.png` (first pass), `polar_bler_vs_snr_full_vs_first_pass_*.png` (512: BLER and
decodes per packet, full vs first pass, for NN v2, M&M and the split pilots of A.13; 1024 (`_L1024`): decodes per
packet only, full vs first pass, for M&M and the split-pilot NN of A.15.1, whose BLERs are in the split-pilot
figure); compute vs SNR in
`lowrate/plots/complexity/`.

## A.12 Adaptive rate (`adaptive_rate.py`, `lowrate/plots/adaptive_rate/`)

Highest rate with measured BLER < 1e-2 at each 0.5 dB point from −5 to 10 dB (switching only on measured points,
no interpolation); throughput = A·(1 − BLER) / N_sym bits per symbol. Receiver: SNR-aware NN + CRC search (full
search). Since 1 − BLER > 0.99 at every chosen point and consecutive rates differ by ≥ 1.33×, the highest rate under
the target is always the best throughput.

| Rate | 1/10 | 0.15 | 0.2 | 1/4 | 1/3 | 1/2 | 3/4 |
|---|---|---|---|---|---|---|---|
| Switch at (512 symbols, CRC-11) | −5 | −3 | −2 | −1 | 0.5 | 3 | 6.5 dB |
| Switch at (1024 symbols, CRC-16) | −5 | **−3.5** | −2 | −1 | 0.5 | 3 | 6.5 dB |

Switching to R = 0.15 already at −3.5 dB breaks the target at 512 (BLER 1.55e-2) but works at 1024 (7.7e-3): +0.1
b/symbol there. Elsewhere both packet lengths give the same throughput (within 0.003 b/symbol), the 1024-symbol one
at 4–8× the decodes.

## A.13 Split pilots: why the "quarter" layout (`train_cfo_v3.py`, study `lowrate/`)

**Idea.** Keep the same 128 known symbols, but place them as **two 64-symbol blocks** instead of one block at the
start of the packet. Two layouts were tested:

| Layout | Blocks | Block distance D | Wrong-lobe rate (512 / 1024 symbols) | CFO std vs. contiguous 128 (512 / 1024) |
|---|---|---|---|---|
| Ends | 0..63 and N−64..N−1 | N − 64 | 27 % → 5.2 % (−5 → 0 dB) / 61 % → 35 % | 6.1× / 13× smaller |
| **Quarter** | centred at N/4 and 3N/4 | N/2 | **6.5 % → 0.08 %** / 34 % → 9.2 % | 3.5× / 6.9× smaller |

**Why spreading the pilots helps.** The CFO CRB is 1 / (8π² · SNR · Σ(n − n̄)²): it falls with the *spread* of the
known positions in time, not only with their number. A residual CFO e rotates the phase by 2π·e·Δn, so two blocks
far apart measure that rotation over a long baseline. With the same 128 symbols, Σ(n − n̄)² grows 12× (quarter, 512)
to 169× (ends, 1024) compared with one contiguous block.

**Why the widest spread is not the best: lobe ambiguity.** Two separated blocks only measure the phase difference
between them, which is known modulo 2π. Every CFO f + j/D (j = ±1, ±2, …) fits the pilots almost equally well: the
likelihood has near-equal lobes spaced 1/D apart (the adjacent lobe is 97 % (ends, 512) to 99 % (ends, 1024) of
the main one). Which lobe is right can only be decided *inside* each 64-symbol block, whose own CFO precision is
fixed (σ₆₄ ≈ 1.4e-3 cycles/symbol at −5 dB). The wrong-lobe probability therefore depends on σ₆₄ relative to the
lobe spacing 1/D:
- **ends:** 1/D = 2.2e-3 (512) or 1.0e-3 (1024), comparable to σ₆₄ → the lobe is often wrong (27 % at −5 dB, 512;
  still 35 % at 0 dB, 1024);
- **quarter:** 1/D = 3.9e-3 (512), about 3σ₆₄ → wrong lobes are rare (6.5 % at −5 dB, 0.08 % at 0 dB).

A wrong lobe is a CFO error of a full 1/D, far beyond what the code tolerates, so that first decode fails. The CRC
search must then try the neighbouring lobes, and every extra decode is another chance for a wrong codeword to pass
the CRC (an undetected error). **The ends layout trades more precision on the right lobe for many more wrong
lobes; the quarter layout gives up some precision (3.5× instead of 6×) to make wrong lobes rare.** On the right lobe
both are equally good relative to their own CRB (fine RMSE 1.05–1.08 × √CRB).

**Estimator** (split-pilot ML, no NN): coarse CFO from both blocks combined non-coherently (peak of
|FFT₂₅₆(block 1)|² + |FFT₂₅₆(block 2)|², 2 Newton steps); the lobe nearest to it from the phase difference of the two
blocks; the lobe with the highest likelihood among the nearest ±2 (the joint ML lobe); 2 Newton steps on the full
likelihood. A light correction MLP on top was not trained: on the right lobe the ML is already at 1.06× the CRB,
and picking the most likely lobe is already the optimal choice.

**CRC search for split pilots** (a tighter, finer grid than the contiguous one, because the estimate is 3.5–7×
more precise): ±J lobes (J = 1 for quarter/512, 2 for quarter/1024) × a fine grid of step 1.0e-4 · 512/N (2/3 of the
contiguous step), half-width 4 · 1.06 · √CRB_split around each lobe. The hypotheses are tried **in order of the
pilot likelihood** |Σ z[n] e^{−j2πfn}|² (computed for every hypothesis from the 128 pilots, cheap next to a decode),
so a wrong-lobe frame usually reaches the right lobe at the second or third decode. First pass stops at the first
CRC pass; full search decodes every hypothesis and keeps the best path metric.

**Result** (R = 1/10; ≥ 30–50 errors per point, except where marked; ends layout from the quick round only):

| BLER (decodes / packet) | 512, CRC-11, −4 dB | 512, CRC-16, −3 dB | 1024, CRC-16, −3 dB |
|---|---|---|---|
| NN v2, no CRC search | 0.11 | 4.6e-2 | 0.26 |
| Quarter, no CRC search | 3.5e-2 | 1.7e-2 | 0.24 |
| NN v2 + CRC search, first pass | 1.6e-3 (1.4) | 2.3e-5 (1.1) | 2.6e-4 (2.8) |
| Ends + CRC search, first pass | 3.2e-3 (1.5) | 2.8e-5 (1.4) | 2.1e-4 (2.2) |
| **Quarter + CRC search, first pass** | **5.8e-4 (1.2)** | **8.5e-6 (1.1)** | **8.7e-5 (1.8)** |
| NN v2 + CRC search, full search | 4.4e-4 (4.1) | 9.2e-6 (2.2) | 5.3e-5 (16.7) |
| **Quarter + CRC search, full search** | **2.7e-4 (2.4)** | **3.2e-6 (1.6)**, 17 errors | **3.5e-5 (13.4)**, 18 errors |

- **Without the CRC search** the quarter layout is 2–3× better than NN v2 at low SNR (−5 to −3 dB), but slightly
  worse from ≈ −1 dB at 512 (wrong-lobe frames, 0.3 % at −1 dB, are lost without a search). Split pilots therefore
  pay off together with the lobe search.
- **With the CRC search** the quarter layout is the best receiver up to ≈ −2 dB in every configuration, for both
  search variants, with fewer decodes than NN v2: first pass 1.5–3× lower BLER; full search the lowest BLER (or tied
  with NN v2's full search within the statistics, e.g. 512 / CRC-16 at −4 dB), at 25–60 % fewer decodes than NN
  v2's full search at 512 (1024: 13–23 decodes per packet at −5 to −3 dB, so first pass is the efficient choice
  there).
- **Above ≈ −1 dB at 512 / CRC-11** the CRC-11 false-pass floor dominates every receiver (≈ 100 % undetected
  errors), and the quarter layout is no better (0 dB: 7.8e-6 first pass vs 2.5e-6 for NN v2).

Figures: `lowrate/plots/bler/polar_bler_vs_snr_split_pilots_*.png` (the genie = one CA-SCL decode with the true CFO and
phase; M&M with / without the CRC search, NN v1 (the SNR-aware NN of A.3.2) and NN v2 (A.10) + CRC search (first
pass); the 1024 figure instead shows only the genie, M&M with / without the search and the split-pilot NN of
A.15.1 (no search, first pass, full search), whose curves are statistically the same as the split ML's against the quarter layout without the search, first pass and full search), `polar_bler_vs_snr_full_vs_first_pass_*.png`, and
the quarter curve in `polar_bler_vs_snr_R0p1*.png` / `polar_bler_vs_snr_best_option_L1024.png`.

**Why the CRC-search receivers can be below the genie.** The genie decodes each packet *once*, with the exact CFO.
A CRC-search receiver whose first decode fails decodes the same packet again under other CFO hypotheses. A
hypothesis a little off the true CFO perturbs the LLRs slightly, and the CA-SCL list of the perturbed packet is
different, so a packet the exact-CFO decode loses can still be recovered (the effect behind "perturbation" /
re-decoding schemes for SCL). The genie is therefore the bound for a *single* decode, not for a receiver that is
allowed several. The price is more decodes and more chances for a false CRC pass (undetected errors). This only
pays at the lowest SNRs: with more genie frames (jobs `add6-a/b`, 10–518 errors per point; the last points 2–16) the
genie waterfall is much steeper than the search receivers' curves. At 512 / CRC-16 it is below the first-pass
receivers from −3 dB (genie 4.0e-6 vs 8.5e-6 for split pilots + first pass) and below the full search from −2.5 dB
(1.3e-7 vs 1.5e-6; at −3 dB the two are level, 4.0e-6 vs 3.2e-6 on 10 genie errors), where the search receivers
flatten out on their undetected-error floor.

**CFO MSE** (`cfo_split_mse.py` → `logs/cfo_split_mse.json`, `plots/mse/cfo_mse_vs_snr_split_pilots.png`; full
chain, 1e6 frames per SNR at ≤ −3 dB, 1e5 above; NN v2 and M&M from `logs/cfo_v2_light32_test.json`):

| SNR | −5 dB | −3 | −1 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|---|
| M&M, MSE | 2.5e-5 | 4.0e-7 | 1.1e-7 | 8.5e-8 | 5.2e-8 | 2.6e-8 | 8.2e-9 |
| NN v2, MSE | 4.1e-7 | 1.7e-7 | 1.0e-7 | 8.3e-8 | 5.1e-8 | 2.6e-8 | 8.2e-9 |
| Split 512, MSE (all frames) | 1.3e-6 | 2.9e-7 | 5.6e-8 | 2.2e-8 | 5.0e-9 | 2.1e-9 | 6.5e-10 |
| Split 512, wrong-lobe rate | 6.4 % | 1.9 % | 0.33 % | 0.11 % | 6e-5 | 0 | 0 |
| Split 1024, MSE (all frames) | 1.5e-6 | 8.8e-7 | 4.9e-7 | 3.4e-7 | 1.3e-7 | 1.1e-8 | 1.7e-10 |
| Split 1024, wrong-lobe rate | 34 % | 23 % | 13 % | 8.9 % | 3.4 % | 0.27 % | 0 |

On the right lobe the split-pilot ML is at **1.11–1.14 × its own CRB** at every SNR and both packet lengths
(the same full-chain floor as NN v2's 1.12–1.15 × the contiguous CRB), i.e. 12× (512) / 48× (1024) lower MSE than
NN v2. The MSE over *all* frames is dominated by the wrong-lobe frames (each a full lobe spacing off): it is
**worse than NN v2 up to ≈ −2 dB (512) / ≈ 4 dB (1024)** and much better above, approaching the split CRB once
wrong lobes vanish (512 from ≈ 2 dB, 1024 at 10 dB). This is why the split pilots need the lobe search: the MSE
alone understates them at low SNR — the wrong lobe is almost always a *neighbouring* lobe, which the CRC search
recovers in one or two extra decodes, whereas NN v2's error is spread continuously.

## A.14 Simulation speed (same results, less time)

Profile of one BLER point: the CA-SCL decoder is 55 % (512 symbols) / 72 % (1024) of the time, the full Tx/Rx chain
38 % / 24 %. Two changes give **exactly the same results** (checked bit for bit), so new runs pool with old ones:
- **Decoder** (`polar.py`): the list paths are re-ordered at every information bit; `np.take_along_axis` was
  replaced by plain fancy indexing (same values, less overhead): **1.3× faster decoding, 1.25–1.3× per point**
  (512: 652 → 816 frames/s; 1024: 202 → 264 frames/s, one core).
- **Shared frames** (`polar_ber_experiment.py --shared-frames`): every receiver of a point already uses the same
  seed, i.e. the same data, CFO, phase and noise. All receivers of a point now run in one task on one Tx/Rx chain
  per batch: **1.3–1.6× faster with 5 receivers**, results identical to separate runs.

Not adopted: computing only the needed samples of the pulse shaping / matched filter (identical output, but 2.5×
slower than the FFT convolution; the chain's time is the noise and CFO rotation at 8 samples per symbol, which the
full chain requires). Larger batches gain < 10 %. Possible next step: a compiled (numba) decoder, ≈ 2× more overall,
statistically identical but not bit-identical (float sums in a different order).

---

## A.15 Split pilots with a pure NN estimator (`train_cfo_split_nn.py`, `models/cfo_split_nn_L{512,1024}.pth`)

**Question.** Can a network that does *not* start from ML (no FFT peak search, no Newton steps, no likelihood lobe
choice) match the split-pilot ML of A.13? Same pilots (quarter layout, 2 × 64 symbols centred at N/4 and 3N/4), full
Tx/Rx chain, AWGN, one model per packet length.

**Why try it without ML.** NN v2 (A.10) showed that almost all of its gain came from the ML front end. This
experiment asks the opposite question: whether the expensive, hand-designed parts (FFT, Newton, lobe search) can
be learned, and if so what they cost. Only the lobe step is kept analytic: given a coarse CFO, the phase difference
of the two blocks determines the lobe exactly, and the smoke test showed that this step, fed the true coarse CFO,
is already at 1.10–1.15 × CRB_split. So the whole question is whether a learned coarse stage can be accurate
enough to pick the right lobe.

**Architecture** (z[n] = r[n]·s*[n] at the 128 pilot positions; D = N/2 = distance of the block centres):

```
 block 1: z[0..63] ──► [Re, Im] (128) ──► bank: Linear 128→256, no bias ──► |·|² of 128 complex filters ─┐
 block 2: z[64..127] ─► [Re, Im] (128) ──► same bank ──────────────────────► |·|² ─────────────────────── + ─┐
                                                                (non-coherent sum of the 2 blocks)            │
        log(E) − log(mean E)  (128)  +  SNR  ──► MLP 129→256→128→1 (GELU) ──► f_c = 0.2·tanh(·)   COARSE  │
                                                                                                    │
        de-rotate both blocks by f_c ──► b1 = Σ block 1, b2 = Σ block 2                            LOBE (analytic)
        φ = angle(b2·b1*) / 2π,   f_lobe = f_c + φ / D                                              │
                                                                                                    │
        [SNR, frac(f_c·D), cos 2πφ, sin 2πφ, log(1 + |b2·b1*|/64)] ──► MLP 5→32→1 (GELU,           FINE
                                                                        last layer zero-init) ──► Δ │
                                                                                                    ▼
                                                                              f̂ = f_lobe + Δ / D
```

- **Filter bank** initialised either with DFT rows (128 frequencies evenly over ±0.21 cycles/symbol, i.e. a zoomed
  DFT of each block) or randomly. Both were trained; **DFT initialisation was better at both lengths** and is the
  saved 512 model. (At 1024 a better architecture replaced it, A.15.1.)
- **Loss** = ((f_c − f)·D)² + min((f̂ − f)², (1/2D)²) / CRB_split. f_c is detached in the lobe and fine stages,
  so the first term trains the coarse branch and the second only the fine MLP. A wrong lobe is clipped at half a
  lobe, as in A.13, because the CRC search handles it, not the regression.
- **Training:** Es/N0 ~ U[−6, 11] dB, CFO ~ U[−0.2, 0.2], 80 epochs × 500 steps × 1024 frames (41M frames, as NN
  v2), AdamW 1e-3, cosine decay; best epoch by validation loss.
- **Size / cost:** 99,298 parameters; **132,932 real MACs per estimate** (filter bank 65,536, energies 512, coarse
  MLP 65,920, de-rotation and sums 772, fine MLP 192). The split ML costs ≈ 35,000 and NN v2 ≈ 40,000.

**Result** (full chain, 1e6 frames per SNR at ≤ −3 dB, 1e5 above; the split ML evaluated *on the same frames*;
`logs/cfo_split_nn_L{512,1024}.json`, `plots/mse/cfo_mse_vs_snr_split_pilots_nn.png`):

| Wrong-lobe rate | −5 dB | −4 | −3 | −2 | −1 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| 512, split ML | **6.4 %** | **3.7 %** | **1.9 %** | **0.86 %** | **0.34 %** | **0.12 %** | **7e-5** | 0 | 0 |
| 512, split NN (DFT init) | 11.9 % | 7.2 % | 4.0 % | 2.1 % | 0.90 % | 0.34 % | 2.5e-4 | 0 | 7e-5 |
| 512, split NN (random init) | 19.4 % | 12.7 % | 7.7 % | 4.2 % | 2.1 % | 0.97 % | 1.3e-3 | 1e-5 | 5e-5 |
| 1024, split ML | **34 %** | **29 %** | **23 %** | **18 %** | **13 %** | **9.0 %** | **3.3 %** | **0.28 %** | 0 |
| 1024, split NN (DFT init) | 41 % | 35 % | 28 % | 23 % | 17 % | 12 % | 5.4 % | 0.83 % | 0.09 % |
| 1024, split NN (random init) | 49 % | 42 % | 35 % | 29 % | 22 % | 17 % | 8.2 % | 1.8 % | 0.26 % |

| Right-lobe MSE / CRB_split | −5 dB | −3 | 0 | 2 | 10 |
|---|---|---|---|---|---|
| 512, split ML / split NN | 1.14 / 1.16 | 1.13 / 1.15 | 1.12 / 1.13 | 1.12 / 1.13 | 1.12 / 1.14 |
| 1024, split ML / split NN | 1.13 / 1.13 | 1.13 / 1.13 | 1.13 / 1.13 | 1.12 / 1.12 | 1.11 / 1.12 |

- **On the right lobe the NN matches the ML** (within 0–2 %): the analytic lobe step does the precise work, and the
  fine MLP has nothing left to correct.
- **The NN picks the wrong lobe 1.9–2.9× (512) and 1.2–3× (1024) as often as the ML**, and still a few frames in 1e5 at
  10 dB, where the ML never errs. Every wrong-lobe error comes from the coarse stage (the coarse-only wrong-lobe
  rate is the same to within 2 %). The coarse MLP has to place the peak of 128 filter energies to ≈ 1/400 of the
  ±0.2 range, i.e. a learned arg-max with interpolation; the ML gets this from 2 Newton steps on the exact
  likelihood, and then picks the lobe by the full likelihood. The NN's coarse MSE stays 2.4–3× above the bound of a
  non-coherent two-block estimate (512: 2.8e-6 vs 9.2e-7 at −5 dB, 6.9e-8 vs 2.9e-8 at 10 dB): the learned arg-max
  loses a constant factor of precision, and the wrong-lobe rate is very sensitive to it.
- **MSE over all frames** (dominated by the wrong lobes): the NN is 1.0–2.7× worse than the ML at 512 and 1.25–24×
  worse at 1024 (the largest gap at high SNR, where the ML has no wrong lobes left).
- **Cost:** 3.8× the split ML and 3.3× NN v2 per estimate.
- **Against NN v2** (contiguous pilots): the split NN is better than NN v2 only where the split ML is too, but by
  less (512: from 0 dB instead of ≈ −2 dB; 1024: only at 10 dB).

**Conclusion of the first design.** This MLP-coarse NN is not competitive with the split-pilot ML: twice the wrong
lobes at 512, more at 1024, and 3.8× the cost. The bottleneck is the learned coarse arg-max. **No BLER runs were
made for it** (BLER was planned only if the NN was competitive). It appears in the complexity figure's footer only
(estimator cost), because the plotted curves need the decode counts of a BLER run.

### A.15.1 Architecture search at 1024 symbols: a pure NN that matches the split ML

Five more 1024-symbol models (same pilots, chain, frames per epoch, fine stage and evaluation frames), aimed at the
two weaknesses found above: the coarse arg-max and the lobe choice.

| Tag | Coarse stage | Lobe choice | Epochs | Params | MACs |
|---|---|---|---|---|---|
| `wide` | MLP 257 → 512 → 256 → 1 on 256 filters (2× wider) | analytic (nearest lobe) | 120 | 329k | 396k |
| `conv` | **1-D conv over the filter energies + soft-argmax** | analytic | 80 | 34k | 153k |
| `mlplobe` | the original MLP | **learned lobe classifier** | 80 | 105k | 143k |
| `convlobe` | conv + soft-argmax | learned lobe classifier | 80 | 40k | 163k |
| **`convlobe-long`** | conv + soft-argmax | learned lobe classifier | **160** | **40k** | **163k** |

- **Conv soft-argmax coarse stage.** The log energies of the 128 DFT-initialised filters (one value per frequency)
  go through three 1-D convolutions along frequency (2 → 8 → 8 → 2 channels, kernel 7; the SNR is the second input
  channel). Output channel 1 is a logit per filter, channel 2 an offset within the filter spacing; f_c = Σ softmax
  · (f_k + offset_k). Because a convolution does the same thing at every frequency, the network learns *one* peak
  finder instead of a separate mapping for each of the 128 positions (the MLP's problem). Trained with an extra
  cross-entropy on the filter nearest the true CFO.
- **Learned lobe classifier.** For the 7 candidate lobes f_lobe + j/D (|j| ≤ 3) around the analytic lobe, the
  inputs are the coherent pilot likelihood |B₁ + B₂|², the per-block energy |B₁|² + |B₂|² (both as log ratios to
  the best candidate) and the distance to f_c in lobes, plus the SNR (22 values) → MLP 22 → 64 → 64 → 7, trained
  with cross-entropy on the true lobe. It replaces the ML's "best of the ±2 lobes by likelihood" with a learned
  decision that can also use the coarse estimate. (It uses the pilot likelihood at 7 candidates as *features*; there
  is still no FFT peak search and no Newton step.)

```
 z (2 × 64) ─► DFT-init bank ─► log energies (128) ─► conv1d ×3 ─► softmax + offsets ─► f_c          COARSE
                                     (+ SNR channel)
 f_c ─► de-rotate, b1, b2 ─► φ ─► f_lobe = f_c + φ/D                                                  LOBE
 7 candidates f_lobe + j/D ─► [log|B1+B2|², log(|B1|²+|B2|²), (cand − f_c)·D, SNR] ─► MLP 22→64→64→7 ─► j*
 f̂ = f_lobe + j*/D + (1/D)·MLP 5→32→1                                                                FINE
```

Block diagram: [`plots/split_nn_architecture.png`](plots/split_nn_architecture.png) (`py plot_split_nn_arch.py`).

**Result** (1024 symbols, the same 1e6 / 1e5 frames per SNR as the split ML):

| Wrong-lobe rate | −5 dB | −4 | −3 | −2 | −1 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| Split ML | 34.28 % | 28.59 % | 23.00 % | 17.63 % | 13.06 % | 8.98 % | 3.26 % | 0.28 % | 0 |
| **`convlobe-long`** | **34.18 %** | **28.48 %** | **22.93 %** | **17.61 %** | **13.00 %** | **8.96 %** | **3.23 %** | **0.28 %** | **0** |
| `convlobe` | 34.32 % | 28.61 % | 23.02 % | 17.64 % | 13.06 % | 9.02 % | 3.28 % | 0.29 % | 0 |
| `mlplobe` | 34.45 % | 28.66 % | 23.05 % | 17.61 % | 13.08 % | 9.04 % | 3.27 % | 0.28 % | 0 |
| `conv` | 34.80 % | 29.08 % | 23.44 % | 18.08 % | 13.37 % | 9.19 % | 3.35 % | 0.31 % | 0 |
| `wide` | 38.83 % | 32.59 % | 26.65 % | 20.99 % | 15.76 % | 11.47 % | 4.90 % | 0.73 % | 0.01 % |
| first design (A.15) | 41.26 % | 34.59 % | 28.30 % | 22.53 % | 16.92 % | 12.39 % | 5.35 % | 0.83 % | 0.09 % |

| | −5 dB | −3 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|
| MSE, split ML | 1.96e-6 | 8.79e-7 | 3.41e-7 | 1.24e-7 | 1.10e-8 | 1.67e-10 |
| MSE, **`convlobe-long`** | **1.63e-6** | **8.77e-7** | **3.41e-7** | **1.23e-7** | **1.10e-8** | **1.67e-10** |
| Right-lobe MSE / CRB_split, split ML / `convlobe-long` | 1.132 / 1.137 | 1.126 / 1.131 | 1.125 / 1.129 | 1.117 / 1.120 | 1.116 / 1.117 | 1.112 / 1.113 |

- **`convlobe-long` is the chosen 1024 model** (`models/cfo_split_nn_L1024.pth`). It picks the wrong lobe as often
  as the split ML or slightly less (−0.1 points at −5 dB), and its MSE over all frames is equal or lower at every
  SNR (17 % lower at −5 dB). On the right lobe it is 0.1–0.5 % above the ML.
- **What made the difference:** the translation-equivariant coarse stage (`conv` alone cuts the gap to the ML from
  7 to 0.5 points at −5 dB), then the learned lobe choice (closes the rest; with it even the poor MLP coarse stage
  reaches the ML, `mlplobe`). Capacity does not help (`wide`, 3× the cost, is still 4.5 points behind). Doubling the
  training gave a small further gain.
- **Against the CRB:** at 10 dB the all-frames MSE is 1.11 × the CRB, the full-chain floor (matched-filter loss at a
  large CFO) that every estimator in this study pays. At low SNR no estimator can approach the CRB at 1024: the
  lobes are 99 % equal, so a third of the frames sit on the wrong lobe at −5 dB, for the ML as well.
- **Cost:** 163,004 real MACs per estimate (filter bank 65.5k, conv 86.4k, lobe classifier 9.6k, rest 1.5k), 4.7×
  the split ML. It matches the ML; it is not cheaper.
- **512 symbols:** still the first design (`cfo_split_nn_L512.pth`); the new architecture was trained only at 1024.

**BLER of the chosen 1024 model** (R = 1/10, CRC-16, full chain; sources `Split pilots NN, quarter` with and without
`+ CRC search (first pass)` in `polar_ber_experiment.py`; the CRC search is the split ML's own: ±2 lobes × the fine
grid, tried in order of the pilot likelihood, around the NN estimate; job `add7-a`, the same number of frames per SNR
as the split-ML curve, at least 2000 without the search; figure
`lowrate/plots/bler/polar_bler_vs_snr_split_pilots_R0p1_C16_L1024.png`, cyan):

| SNR | −5 dB | −4.5 | −4 | −3.5 | −3 | −2.5 | −2 | −1.5 | −1 | −0.5 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Split ML, no search | 3.2e-1 | 3.2e-1 | 2.6e-1 | 2.3e-1 | 2.4e-1 | 1.9e-1 | 1.7e-1 | 1.6e-1 | 1.3e-1 | 1.3e-1 | 8.3e-2 |
| Split NN, no search | 3.4e-1 | 3.1e-1 | 3.0e-1 | 2.4e-1 | 2.3e-1 | 2.2e-1 | 1.8e-1 | 1.4e-1 | 1.2e-1 | 1.1e-1 | 8.3e-2 |
| Split ML + CRC (first pass) | 2.9e-3 | 4.0e-4 | 2.1e-4 | 1.2e-4 | 8.7e-5 | 1.0e-4 | 6.4e-5 | 5.3e-5 | 5.2e-5 | 3.9e-5 | 3.4e-5 |
| Split NN + CRC (first pass) | 2.7e-3 | 3.4e-4 | 1.2e-4 | 1.3e-4 | 8.2e-5 | 8.7e-5 | 6.7e-5 | 6.6e-5 | 4.0e-5 | 4.2e-5 | 2.7e-5 |
| Decodes / packet, ML / NN | 2.83 / 2.84 | 2.42 / 2.41 | 2.18 / 2.18 | 2.00 / 1.99 | 1.84 / 1.83 | 1.69 / 1.69 | 1.57 / 1.56 | 1.46 / 1.46 | 1.37 / 1.37 | 1.30 / 1.29 | 1.23 / 1.23 |
| Split ML + CRC (full search) | 2.8e-3 | 2.0e-4 | 7.3e-5 | 2.8e-5 | 3.5e-5 | 2.3e-5 | 3.9e-5 | 2.2e-5 | 2.7e-5 | 1.5e-5 | 9.8e-6 |
| Split NN + CRC (full search) | 2.4e-3 | 2.2e-4 | 5.3e-5 | 4.7e-5 | 2.7e-5 | 3.7e-5 | 2.5e-5 | 1.2e-5 | 2.2e-5 | 1.7e-5 | 1.7e-5 |
| Full-search decodes / packet, ML / NN | 23.2 / 23.3 | 21.1 / 21.3 | 19.4 / 19.2 | 14.9 / 14.9 | 13.4 / 13.4 | 12.0 / 11.9 | 10.6 / 10.6 | 7.7 / 7.7 | 6.7 / 6.7 | 5.8 / 5.8 | 4.9 / 4.9 |

(28–124 errors per point with the first-pass search; 10–140 with the full search, the same frame counts as the split
ML's full-search curve, job `add8-a…d`; without the search 166–687 for the NN, 66–160 for the ML.) Pooled over the
11 SNRs (inverse-variance weighted log ratio), **NN / ML BLER = 1.01 (95 %: 0.95–1.08) without the search, 0.93
(0.84–1.03) with the first-pass search and 0.93 (0.79–1.09) with the full search**, χ²/dof = 0.7, 1.3 and 1.35: the point-to-point differences are Monte-Carlo noise, and the NN receiver is statistically the same as the
split-ML receiver, at the same number of decodes. With the search, most remaining errors are undetected (a wrong
codeword passes CRC-16: 621 of 691 NN errors, 672 of 744 ML errors), the CRC floor of A.11.

**The same comparison at R = 1/4, SNR 0 … 10 dB** (`lowrate/plots/bler/polar_bler_vs_snr_split_pilots_R1_4_C16_L1024.png`;
jobs `add9-a…e` (≤ 200k frames or 300 errors per point) and the top-up `add10-a…h`). **R = 1/4 (512 data bits,
CRC-16) is the highest rate with BLER < 1e-2 at 0 dB:** R = 1/3 fails there even with the true CFO (genie 4.8e-2;
M&M + CRC 3.8e-2, split NN + CRC 3.8e-2), while at R = 1/4 the genie has 1.2e-5 (27 errors in 2.2M) and no error
in 200k frames from 0.5 dB up. (No rate between 1/4 and 1/3 was simulated.)

| SNR | 0 dB | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M&M, no search | 2.8e-1 | 1.9e-1 | 9.0e-2 | 4.5e-2 | 1.8e-2 | 5.5e-3 | 1.6e-3 | 3.4e-4 | 5.1e-5 | 2.3e-6 (5) | 4.5e-7 (1) |
| **Split NN, no search** | **8.6e-2** | **5.7e-2** | **3.2e-2** | **1.5e-2** | **7.0e-3** | **2.6e-3** | **8.4e-4** | **1.6e-4** | **2.6e-5** | 4.1e-6 (9) | 4.5e-7 (1) |
| M&M + CRC (first pass) | 2.6e-4 | 1.2e-4 | 6.3e-5 | 1.9e-5 | 9.5e-6 (21) | 8.3e-7 (1) | 0 in 1.2M | | | | |
| **Split NN + CRC (first pass)** | **4.2e-5** | **2.0e-5** | **1.3e-5** | **3.4e-6** (11) | **2.8e-6** (9) | 0 in 200k | | | | | |
| Decodes / packet, M&M / NN | 2.36 / 1.23 | 1.67 / 1.13 | 1.30 / 1.07 | 1.12 / 1.03 | 1.04 / 1.01 | 1.01 / 1.00 | | | | | |

(Error counts in brackets where < 25; the other points have 40–577 errors. Up to 2.2M frames per point without the
search, 3.2M (NN) / 2.2M (M&M) with it.)
- **Without the search, every error is a CFO-estimate error**, since the code itself is error-free from 0.5 dB.
  The split NN is 2.5–3.3× below M&M up to 4 dB and ≈ 2× at 5–6 dB (at 0 dB its 8.6 % ≈ its 9 % wrong-lobe rate); the two meet near
  8–9 dB, where both are at ≈ 1e-5 … 1e-6 and only a handful of errors were counted.
- **With the first-pass search, the split NN is 3–6× below M&M at 0–4 dB with fewer decodes** (1.23 vs 2.36 per
  packet at 0 dB). Practically all remaining errors are undetected (a wrong codeword passing CRC-16), so the BLER
  follows the number of extra decodes, which falls to ≈ 1 by 4–5 dB; above that neither receiver had an error in
  the frames simulated (no point drawn).

**And at R = 1/3** (683 data bits, CRC-16; `polar_bler_vs_snr_split_pilots_R1_3_C16_L1024.png`, jobs `add11-a…h`,
≤ 100 errors or 500k frames per run, up to 4 runs per point). Here the code itself still fails at low SNR: the genie
falls from 4.8e-2 at 0 dB to 1.9e-4 at 1 dB and 3.3e-6 (5 errors) at 1.5 dB, with no errors in 1.5M frames from 2 dB.

| SNR | 0 dB | 0.5 | 1 | 1.5 | 2 | 3 | 4 | 5 | 6 | 8 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Genie | 4.8e-2 | 5.0e-3 | 1.9e-4 | 3.3e-6 (5) | 0 in 1.5M | | | | | | |
| M&M, no search | 5.4e-1 | 3.9e-1 | 2.9e-1 | 2.4e-1 | 2.1e-1 | 9.5e-2 | 4.1e-2 | 1.6e-2 | 5.9e-3 | 3.4e-4 | 1.3e-6 (2) |
| **Split NN, no search** | **1.4e-1** | **8.1e-2** | **5.5e-2** | **4.2e-2** | **2.9e-2** | **2.0e-2** | **7.5e-3** | **2.7e-3** | **7.7e-4** | **3.3e-5** | 0 in 1.5M |
| M&M + CRC (first pass) | 3.8e-2 | 3.6e-3 | 4.5e-4 | 1.8e-4 | 1.3e-4 | 4.8e-5 | 2.1e-5 | 6.0e-6 (3) | 2.0e-6 (1) | | |
| **Split NN + CRC (first pass)** | **3.7e-2** | **2.9e-3** | **1.3e-4** | **2.5e-5** | **1.1e-5** (21) | **5.5e-6** (11) | **2.5e-6** (5) | 0 in 500k | | | |
| Decodes / packet, M&M / NN | 5.09 / 2.88 | 3.09 / 1.31 | 2.39 / 1.14 | 1.96 / 1.10 | 1.66 / 1.07 | 1.29 / 1.03 | 1.12 / 1.01 | | | | |

(Error counts in brackets where < 25; the other points have 42–409 errors.)
- **Up to 1 dB both search receivers follow the genie** (the code's own errors dominate). From 1 dB the split NN
  stays on the waterfall longer: 1.3e-4 vs 4.5e-4 at 1 dB, then 7–12× below M&M at 1.5–2 dB, with 1.1 vs 2.0 decodes.
  Both then flatten on the undetected-error floor (a wrong codeword passing CRC-16), M&M's ≈ 8–15× higher (2.5–4 dB) because it
  needs more decodes.
- **Without the search** the split NN is 4–10× below M&M at every SNR from 0 to 9 dB; above the genie's waterfall
  every remaining error is a CFO error (the split NN's wrong lobe, M&M's spread error).
- **BLER < 1e-2:** first pass from ≈ 0.3 dB for both; without the search from ≈ 3.7 dB (split NN) and ≈ 5.4 dB
  (M&M).

**And at R = 1/2** (1024 data bits, CRC-16, SNR 2 … 10 dB; `polar_bler_vs_snr_split_pilots_R1_2_C16_L1024.png`, jobs
`add12-a…h`, same stopping rule). The genie's waterfall is at 2–4 dB (1.4e-1 at 2 dB, 2.2e-3 at 3 dB, 7.4e-5 at
3.5 dB, 1.3e-6 (2 errors) at 4 dB).

| SNR | 2 dB | 2.5 | 3 | 3.5 | 4 | 4.5 | 5 | 6 | 7 | 8 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Genie | 1.4e-1 | 3.3e-2 | 2.2e-3 | 7.4e-5 | 1.3e-6 (2) | | | | | | |
| M&M, no search | 5.8e-1 | 4.7e-1 | 3.2e-1 | 2.6e-1 | 1.9e-1 | 1.3e-1 | 8.7e-2 | 3.7e-2 | 1.5e-2 | 4.7e-3 | 2.2e-4 |
| **Split NN, no search** | **2.0e-1** | **6.2e-2** | **1.8e-2** | **1.1e-2** | **7.4e-3** | **4.9e-3** | **3.0e-3** | **7.8e-4** | **1.9e-4** | **4.1e-5** | 6.7e-7 (1) |
| M&M + CRC (first pass) | 1.6e-1 | 2.8e-2 | 2.1e-3 | 2.0e-4 | 1.1e-4 | 6.3e-5 | 5.3e-5 | 2.0e-5 | 1.0e-5 (5) | 0 in 500k | |
| **Split NN + CRC (first pass)** | **1.5e-1** | **2.6e-2** | **1.4e-3** | **4.1e-5** | **3.5e-6** (7) | **3.5e-6** (7) | 0 in 2M | 5e-7 (1) | 0 in 500k | | |
| Decodes / packet, M&M / NN | 7.76 / 6.02 | 3.48 / 1.96 | 2.23 / 1.08 | 1.79 / 1.02 | 1.52 / 1.01 | 1.34 / 1.01 | 1.22 / 1.00 | 1.09 / 1.00 | | | |

(Error counts in brackets where < 25; the other points have 39–423 errors.)
- **Without the search the gap is largest at this rate:** the split NN is 3× below M&M at 2 dB and 18–115× at
  3–8 dB. R = 1/2 tolerates the least CFO error, and M&M's spread error (RMS ≈ 1e-4 even at 10 dB) keeps failing
  it, while the split NN's right-lobe error is ≈ 7× smaller; its remaining no-search errors are wrong-lobe frames.
- **With the first-pass search, the split NN follows the genie** down to 3.5 dB (slightly below it at 3 and 3.5 dB,
  the re-decoding effect of A.13) and then has only 7 errors in 2M frames at 4 and 4.5 dB; M&M + search leaves the
  waterfall at 3.5 dB and flattens at 1e-4 … 2e-5 (undetected errors from its extra decodes): 5× higher at 3.5 dB,
  ≈ 20–30× at 4–4.5 dB.
- **BLER < 1e-2:** with the search from ≈ 2.7 dB for both; without it from ≈ 3.7 dB (split NN) and ≈ 7.4 dB (M&M).

**CFO MSE against M&M** (`train_cfo_split_nn.plot_vs_mm()` → `plots/mse/cfo_mse_vs_snr_split_nn_vs_mm_L1024.png`;
the split NN over all frames, M&M on 128 contiguous pilots from `logs/cfo_v2_light32_test.json`, and both CRBs):

| SNR | −5 dB | −4 | −3 | −2 | −1 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| M&M, MSE | 2.5e-5 | 3.0e-6 | 3.9e-7 | 1.5e-7 | 1.1e-7 | 8.4e-8 | 5.2e-8 | 2.6e-8 | 8.1e-9 |
| Split NN, MSE (all frames) | **1.6e-6** | **1.1e-6** | 8.8e-7 | 6.7e-7 | 4.9e-7 | 3.4e-7 | 1.2e-7 | **1.1e-8** | **1.7e-10** |
| CRB, contiguous / split | 2.3e-7 / 4.8e-9 | 1.8e-7 / 3.8e-9 | 1.5e-7 / 3.0e-9 | 1.2e-7 / 2.4e-9 | 9.1e-8 / 1.9e-9 | 7.3e-8 / 1.5e-9 | 4.6e-8 / 9.5e-10 | 2.3e-8 / 4.8e-10 | 7.3e-9 / 1.5e-10 |

The split NN has the lower MSE at −5 and −4 dB (M&M's own threshold region) and from ≈ 3.5 dB up (49× lower at
10 dB, at 1.11 × its CRB). From ≈ −3.5 to 3.5 dB M&M has the lower MSE, yet the split NN + CRC search has the lower
BLER there (first pass, −2 … 0 dB: 6.7e-5 … 2.7e-5 vs M&M's 2.2e-4 … 4.1e-5). The split NN's MSE in this range is
the wrong-lobe frames (13 % at −1 dB, each ≈ 2e-3 off), which the lobe-ordered search fixes in one or two decodes;
M&M's error is spread continuously (RMS ≈ 3–4e-4 at −2 … 0 dB), so its search scans more hypotheses (2.09 vs 1.56 decodes per
packet at −2 dB, 1.26 vs 1.23 at 0 dB), and almost all remaining errors of both are undetected CRC passes, which grow
with the number of decodes.

**CFO outage** (`cfo_outage_split.py` → `logs/cfo_outage_split.json`, `plots/outage/cfo_outage_split_nn_vs_mm_L1024.png`;
P(|CFO error| > 1.0e-4), 1e6 frames at ≤ −3 dB, 1e5 above).

**Why the threshold is 1.0e-4** (`python cfo_outage_split.py --plot-tolerance` →
`plots/outage/cfo_outage_threshold_tolerance_L1024.png`): an outage threshold should be the CFO error the *code*
cannot tolerate, not a round number. From the BLER-vs-CFO-error run of this code (1024 symbols, R = 1/10, CRC-16,
450–500 errors per point), the error at which the BLER doubles relative to no CFO error is 1.07e-4 at −5.5 dB
(BLER(0) = 2.7e-2), 0.98e-4 at −5 dB (4.3e-3) and 0.83e-4 at −4.5 dB (3.7e-4); at BLER(0) ≈ 1e-2 (the operating point
used for the tolerance throughout this study) it is **1.0e-4**. The figure shows the absolute BLER at −5.5 and
−4.5 dB (the two SNRs on either side of the threshold; −5 dB is left out to keep it readable): dotted line = BLER with
no CFO error, dashed = twice that, ◆ = where each curve doubles, dash-dot = 1.0e-4. Below it the BLER is nearly flat (+12–15 % at 3.75e-5),
above it it rises steeply (×5 at 1.5e-4, ×15 at 2e-4 at −5 dB). The other thresholds (3e-4, 1e-3) were dropped:
both lie on the steep part, where any estimator error is already a decoding failure.

| Outage, \|error\| > 1.0e-4 | −5 dB | −4 | −3 | −2 | −1 | 0 | 2 | 5 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| M&M (128 contiguous pilots) | 0.86 | 0.83 | 0.81 | 0.78 | 0.76 | 0.73 | 0.66 | 0.53 | 0.27 |
| **Split pilots NN** | **0.46** | **0.38** | **0.30** | **0.22** | **0.16** | **0.10** | **0.035** | **3.1e-3** | **0** |
| Split ML (same frames) | 0.46 | 0.38 | 0.30 | 0.22 | 0.16 | 0.10 | 0.034 | 3.0e-3 | 0 |

The split NN has lower outage than M&M at every SNR: 1.9× at −5 dB, 7× at 0 dB, and none in 1e5 frames at 10 dB,
where 27 % of M&M frames still exceed the tolerance (M&M's RMS error is ≈ 9e-5 even at 10 dB). Most of the NN's
outage frames are wrong-lobe frames (a lobe is 1.95e-3 off: 34 % of frames at −5 dB, 9 % at 0 dB), which the
lobe-ordered CRC search recovers in 1–2 extra decodes; M&M's are spread errors around its RMS. The split ML on the
same frames has the same outage as the NN within ±0.001 everywhere.

**Would an estimator built to minimise outage do better? No, not with these pilots.** Both outages are close to
what the pilots allow:
- **Split pilots, −5 dB:** a wrong lobe is always an outage (34.2 %). On the right lobe, even an estimator at the
  CRB (σ = 6.9e-5) exceeds 1.0e-4 in 2Q(1.46) = 15 % of frames, i.e. 0.66 × 0.15 ≈ 0.10. Together ≈ 0.44 of the
  measured 0.455. The lobe choice by maximum pilot likelihood is already near the best possible: an estimator
  trained on the outage itself would pick the lobe with the most probability within ±τ, which for lobes of equal
  width is almost always the same lobe (expected gain ≤ 1–2 points; not trained).
- **M&M, contiguous pilots:** the CRB alone gives an outage of 0.84 at −5 dB (σ = 4.8e-4) and 0.24 at 10 dB
  (σ = 8.5e-5, almost the threshold); M&M measures 0.855 and 0.266. No estimator on 128 contiguous pilots can get
  much lower.

The outage is set by the pilot layout and the SNR, not by the estimator. What would lower it: a layout that trades
less fine accuracy for fewer lobe ambiguities (three blocks with unequal gaps, unequal block sizes; the bound per
layout can be computed with the split ML), decision-directed re-estimation over all 1024 symbols after a decode, and,
for the receiver, the CRC search, which already turns most outage frames into extra decodes (the BLER table above).

**Checks made before these results were written down:**
- **Paired CFO evaluation:** every 1024 / 512 test file contains the split-ML statistics of its own run, and their
  wrong-lobe counts are identical across all 7 (1024) / 2 (512) runs (the MSE sums differ only at 1e-16, summation
  order), so every model was scored on exactly the same frames. They also agree with the independent split-ML run
  `cfo_split_mse.json` (other seeds) within 2σ.
- **No leakage:** training producers, validation and evaluation use disjoint seeds; the best epoch's validation
  (10k frames per SNR: 34.0 % wrong lobe at −5 dB) matches the 1e6-frame evaluation (34.2 %), so no over-fit.
- **Formulas:** the split CRB reduces to the contiguous CRB 3 / (2π² SNR L(L² − 1)) for one block; the quarter
  positions (224–287 and 736–799 at 1024) and the lobe spacing 2/N are as designed; the DFT-initialised bank rows
  are Re / Im of Σ z e^{−j2πfm}; the operation count adds up (conv 14,336 + 57,344 + 14,336 + 384).
- **Simulator:** the NN receives z = r·s* at the same quarter positions as the split ML and, like NN v1 / v2, the
  true SNR; its search reuses the split ML's offsets and likelihood ordering; on 2000 shared frames (−3 dB) it gave
  460 vs 462 errors without the search and 1.83 vs 1.84 decodes with it.
- **All BLER results of the study** (512: CRC-11 / CRC-16, 1024: CRC-16, every receiver, −5 … 0 dB): consistent
  counts, ≥ 1 decode per packet, undetected ≤ BLER, no SNR step where the BLER rises by more than 3σ, and no
  estimator whose CRC search is worse than the same estimator without it.

# Part B: Multipath channel (3-tap Rayleigh)

> **Everything in this part uses the multipath channel.** r[n] = e^{j(2πεn+φ)} Σ_k h_k s[n−k] + w[n],
> 3 symbol-spaced taps with power-delay profile 0 / −3 / −6 dB, independent Rayleigh taps,
> **one realisation per burst** (block fading), E[Σ|h_k|²] = 1, so **Es/N0 is the average received SNR**.
> Numbers here are not comparable with Part A, except where a table explicitly shows both.
> All scripts accept `--channel awgn`, which makes h = [1] and reproduces Part A.

## B.1 How to run

```bash
python multipath/multipath_cfo.py --channel multipath          # M&M / ML / FFT-NN, L = 128 and 512
python multipath/mp_cfo_v2.py ...                              # MP-ML and MP-NN (train + evaluate)
python multipath/zero_overhead_mp.py --channel multipath --parts 4 --part 0      # Stage 2, one job per part
python multipath/zero_overhead_mp.py --channel multipath --refs-only --parts 4 --part 0   # high-trial references
python multipath/zero_overhead_mp.py --channel multipath --merge
python multipath/coarse_nn.py --train ; python multipath/coarse_nn.py --eval          # Stage 3 NN
python multipath/zero_overhead_mp.py --channel multipath --nn multipath/results_coarse_nn/coarse_nn.pth --parts 8 --part 0
```
Results: `multipath/results_multipath/` (B.2–B.3), `multipath/results_zo2_multipath/` (Stage 2),
`multipath/results_coarse_nn/` and `multipath/results_zo2_multipath_nn/` (Stage 3).

## B.2 How much multipath degrades known-sequence CFO estimation (`multipath_cfo.py`)

Same estimators as Part A, on z[n] = r[n]·s*[n] with a known sequence. The delayed taps now act as
interference (ISI) and the main tap fades. "Channel-trained" FFT-NN = fine-tuned on this channel.
20,000 sequences per point. [`cfo_outage_multipath.png`](multipath/results_multipath/cfo_outage_multipath.png),
`cfo_rmse_multipath.png`, `cfo_median_multipath.png`.

**P(|CFO error| > 1e-4), multipath**

| Es/N0 | M&M L=128 | ML L=128 | M&M L=512 | ML L=512 | FFT-NN L=512 (AWGN-trained) | FFT-NN L=512 (channel-trained) |
|---|---|---|---|---|---|---|
| −5 dB | 0.94 | 0.91 | 0.53 | 0.38 | 0.40 | 0.39 |
| 0 dB | 0.86 | 0.84 | 0.29 | 0.21 | 0.26 | 0.22 |
| 5 dB | 0.78 | 0.77 | 0.17 | 0.13 | 0.22 | 0.13 |
| 10 dB | 0.72 | 0.71 | 0.13 | 0.09 | 0.21 | 0.10 |

For comparison, in AWGN at L = 512 the outage is ≈0 from −5 dB up (A.6). The RMSE is dominated by gross
errors (≈2e-2 at L = 512, 3e-2 at L = 128, independent of SNR): in deep fades of the main tap the ISI
terms produce spurious periodogram peaks. **Training the NN on the channel only brings it back to ML; it
cannot do better than ML, because ML is the wrong model here.**

## B.3 Channel-aware estimators: MP-ML and MP-NN (`mp_cfo_v2.py`)

**Why equalization / channel knowledge is needed for the CFO.** With taps, r[n]·s*[n−k] contains the
CFO tone with amplitude h_k for every k, plus interference from the other taps. A single-tap estimator
uses only k = 0 and treats the rest as noise, so it fails whenever h_0 fades.

* **MP-ML** (joint ML of CFO + taps): maximise Σ_k |FFT(r[n]·s*[n−k])|² over ε (FFT K = 2L + 2 Newton steps),
  then least-squares taps. It is the exact joint ML when the shifted sequences are orthogonal (random QPSK:
  nearly). In AWGN (1 tap) it **is** the ML estimator. Cost: 3 FFTs instead of 1 → **3.0× ML**.
* **MP-NN**: FFT-aided network given the same per-tap periodogram features, trained on the channel.

200,000 sequences per point ([`cfo_v2_outage_multipath.png`](multipath/results_multipath/cfo_v2_outage_multipath.png), `cfo_v2_rmse_multipath.png`, `cfo_v2_median_multipath.png`):

| Es/N0 | P(>1e-4), L=512: ML | MP-ML | MP-NN | median, L=512: ML | MP-ML | MP-NN |
|---|---|---|---|---|---|---|
| −5 dB | 0.374 | **0.166** | 0.179 | 7.1e-5 | **4.4e-5** | 4.6e-5 |
| 0 dB | 0.209 | **0.033** | 0.038 | 4.4e-5 | **2.5e-5** | 2.6e-5 |
| 5 dB | 0.123 | **0.003** | 0.004 | 3.1e-5 | **1.4e-5** | 1.6e-5 |
| 10 dB | 0.092 | **0.000** | 0.000 | 2.5e-5 | **8.4e-6** | 9.9e-6 |

| Complexity (real MACs) | ML | MP-ML | MP-NN |
|---|---|---|---|
| L = 128 | 7,680 | 23,040 (3.0×) | 280,640 (36.5×, 242,689 params) |
| L = 512 | 34,816 | 104,448 (3.0×) | 432,704 (12.4×) |

* **MP-ML is the estimator to use in multipath**: 6–∞× lower outage than ML for 3× its cost, and it
  costs nothing in AWGN (it reduces to ML).
* **MP-NN matches MP-ML but never beats it** (slightly worse median and outage everywhere), at 4–12× the
  cost of MP-ML. Several architecture / input variants were tried; none gained an edge.
* At L = 128 even MP-ML has outage 0.34 at 10 dB: 128 symbols are too short for a multipath channel.

## B.4 Zero-overhead receiver, Stage 2: multipath (`multipath/zero_overhead_mp.py`)

Same packet as A.7 (no preamble, no CP, 2-symbol guard so the burst is free of inter-burst
interference; 514 received samples). Es/N0 known (noise variance for equalizers and LLRs).

**Blocks**
| Block | Implementation |
|---|---|
| coarse CFO | 4th power of r (FFT 2048 + 2 Newton), cells k inside the prior; the line amplitude is \|Σh_k⁴\| instead of 1 |
| channel init (a) | blind **CMA** (9 taps, 5 passes, 4th-power phase fix) → decisions → LS taps, delay searched |
| channel init (b) | **strongest-tap (ST) bootstrap**: no equalizer, single-tap LLRs (ISI counted as noise), decode, LS taps on the decisions |
| equalizers | **MLSE** = BCJR over 25 states (QPSK + the zero guard symbol, so the burst edges are exact), bit LLRs from symbol APPs; **block MMSE** (banded Toeplitz, solved per burst) |
| phase ambiguity | the 4 π/2 hypotheses are LLR relabellings of one equalizer output (one equalization per cell) |
| selection | CRC-passing hypothesis with the best path metric, else the best metric |
| code-aided loop | re-encode → **joint ML of CFO + taps** (MP-ML of B.3) on the decisions → re-equalize → re-decode, 3 iterations |

**Receivers**: Genie MLSE / MMSE (true CFO, phase, taps); Known 512 MLSE / MMSE (MP-ML on the true symbols);
Known CFO, est. channel (true CFO, CMA init + 3 code-aided tap updates); Blind CMA + CRC and Code-aided 1/2/3
(MLSE); Blind ST + CRC / Code-aided 3 ST (MLSE); Blind CMA + CRC / Code-aided 3 (MMSE).

Monte Carlo: 6,000 bursts per point for every receiver; the Genie and Known-512 references rerun with up to
200,000 bursts and ≥ 200 errors (`--refs-only`). Plots: [`zo_bler_vs_ebn0.png`](multipath/results_zo2_multipath/zo_bler_vs_ebn0.png),
[`zo_ber_vs_ebn0.png`](multipath/results_zo2_multipath/zo_ber_vs_ebn0.png),
[`zo_cfo_channel_metrics.png`](multipath/results_zo2_multipath/zo_cfo_channel_metrics.png).

**BLER, multipath, selected points (average Eb/N0)**

| Code | Eb/N0 | Genie MLSE | Genie MMSE | Known 512 MLSE | Known CFO, est. ch. | Blind CMA + CRC | Code-aided 3 MLSE | Code-aided 3 ST | Code-aided 3 MMSE |
|---|---|---|---|---|---|---|---|---|---|
| R=1/2 | 5 | 0.24 | 0.27 | 0.24 | 0.44 | 0.75 | 0.75 | 0.80 | 0.75 |
| R=1/2 | 10 | 2.2e-2 | 2.8e-2 | 2.1e-2 | 0.11 | 0.47 | 0.47 | 0.65 | 0.47 |
| R=1/4 | 5 | 0.14 | 0.14 | 0.13 | 0.50 | 0.89 | 0.89 | 0.88 | 0.89 |
| R=1/4 | 10 | 9.0e-3 | 9.2e-3 | 8.8e-3 | 0.12 | 0.62 | 0.62 | 0.69 | 0.62 |
| R=1/4 | 13 | 1.5e-3 | 1.6e-3 | 1.4e-3 | 3.8e-2 | 0.45 | 0.45 | 0.59 | 0.45 |

**Eb/N0 for a target BLER, multipath**: R = 1/2 at BLER 0.1: Genie MLSE 7.11 dB, MMSE 7.46 dB, Known 512 7.08 dB.
R = 1/4: Genie MLSE 5.77 / 7.86 / 9.87 dB at BLER 0.1 / 0.03 / 0.01 (MMSE 5.83 / 7.95 / 9.91; Known 512 5.67 at 0.1);
Known CFO with estimated channel 10.4 dB at 0.1. **The blind receivers never reach 0.1 (floor ≈ 0.45–0.47 at 10 dB Es/N0).**

**CFO statistics, multipath (R = 1/4, median / P(>1e-4))**

| Es/N0 | 4th power (k = 0) | Blind CMA + CRC | Code-aided 3 | Known 512 (MP-ML) | cell k wrong (CRC) |
|---|---|---|---|---|---|
| 0 dB | 0.10 / 0.97 | 0.10 / 0.96 | 0.10 / 0.96 | 2e-5 / 0.030 | 0.45 |
| 5 dB | 0.10 / 0.84 | 6e-2 / 0.75 | 7e-2 / 0.73 | 1e-5 / 0.003 | 0.33 |
| 10 dB | 7e-2 / 0.67 | 8e-5 / 0.48 | 2e-5 / 0.45 | 8e-6 / 0.000 | 0.20 |

**Observations (multipath)**
* **Equalization itself is not the problem**: Known 512 (CFO + taps estimated from known symbols) is on
  the Genie curve, and MMSE costs only 0.05–0.35 dB against MLSE. A known CFO with a blindly initialised
  channel loses ≈ 4.5 dB at BLER 0.1 (R = 1/4); the channel bootstrap is the second problem.
* **The CFO bootstrap is the first problem.** The 4th-power line has amplitude |Σh_k⁴|, which the ISI
  terms swamp; at 10 dB it is in the wrong cell 22 % of the time, and even with the oracle cell its
  fine error exceeds 1e-4 in ≈ 49 % of bursts. The CRC cannot fix a wrong fine estimate.
* **Whenever the first decode succeeds, the code-aided loop reaches the known-symbol bound** (CA-3 median
  2e-5 at 10 dB vs 8e-6), but it cannot rescue bursts whose first decode failed, so the BLER floor stays.
* CMA vs ST init: CMA is better (ST floor 0.59–0.65). MLSE vs MMSE: identical in the blind receivers.
* **Complexity** (blind CMA + MLSE receiver): ≈ 6.9 hypothesis decodes + 1.7 equalizations (25-state BCJR), then
  3 code-aided decodes and equalizations: ≈ 10 decodes and 4.7 equalizations per burst. The `.log` tables of this
  run count the code-aided steps once per batch (a bookkeeping bug, fixed since), and their "decodes" column sums
  the CMA, ST and MMSE chains.
* **AWGN check**: `--channel awgn` reproduces Stage 1 (e.g. R = 1/2 at Es/N0 = 4 dB: BLER 2.4e-3 vs 2.1e-3;
  R = 1/4 at 4 dB: 1.7e-3 vs 2.4e-3, within Monte-Carlo noise of 10,000 packets).

## B.5 Stage 3: neural coarse estimator in multipath

Same network as [A.8](#a8-stage-3-neural-coarse-cfo-estimator-8-sps): one model trained on both channels.
In the receiver it replaces the 4th power; CMA init, MLSE, CRC selection and the joint CFO + taps loop are
unchanged (`zero_overhead_mp.py --channel multipath --nn`, 20,000 bursts per point for every receiver,
[`zo_bler_vs_ebn0.png`](multipath/results_zo2_multipath_nn/zo_bler_vs_ebn0.png),
[`zo_cfo_channel_metrics.png`](multipath/results_zo2_multipath_nn/zo_cfo_channel_metrics.png)).

**Stand-alone, multipath: P(|err| > 1e-4)** (20,000 bursts per point)

| Es/N0 | 4th power, k = 0 | 4th power + oversampled cell | 4th power, oracle k | NN | NN + polish |
|---|---|---|---|---|---|
| 0 dB | 0.973 | 0.961 | 0.957 | 0.969 | 0.968 |
| 5 dB | 0.842 | 0.762 | 0.745 | 0.786 | 0.784 |
| 10 dB | 0.674 | 0.514 | 0.485 | 0.527 | 0.530 |

(Validation cell error of the k head in multipath: 0.031 / 0.023 / 0.007 / 0.009 at −5 / 0 / 5 / 10 dB.)

**BLER, multipath** (same bursts for all receivers)

| Code | Eb/N0 | Genie MLSE | Known 512 MLSE | 4th power + CRC, CA-3 | NN + CRC | NN, CA-3 |
|---|---|---|---|---|---|---|
| R=1/2 | 5 | 0.24 | 0.24 | 0.74 | 0.78 | 0.78 |
| R=1/2 | 10 | 2.2e-2 | 2.1e-2 | 0.46 | 0.51 | 0.51 |
| R=1/4 | 8 | 2.8e-2 | 2.7e-2 | 0.74 | 0.78 | 0.77 |
| R=1/4 | 13 | 1.5e-3 | 1.5e-3 | 0.46 | 0.50 | 0.50 |

At BLER 0.6 the NN receiver needs +0.75 dB (R = 1/2: 7.38 → 8.13 dB; R = 1/4: 10.25 → 11.00 dB), and its floor
is ≈ 0.04 higher. Hypothesis decodes: 5.8 (NN) vs 6.9 (4th power) per burst.

**Why it doesn't help in multipath either**: knowing the right cell is not the bottleneck. Even the
4th power with an **oracle** cell has P(|err| > 1e-4) = 0.49 at 10 dB, because under ISI the r⁴ line
(amplitude |Σh_k⁴|) is too weak and biased for a fine estimate. The NN's fine output is anchored to that same
r⁴ peak, so it inherits the failure.

---

# Part C: Conclusions (Stage 4)

**Where the receivers stand (Eb/N0 at the target BLER; same packet, no preamble)**

| | AWGN R=1/2, BLER 1e-2 | AWGN R=1/4, BLER 1e-2 | Multipath R=1/2, BLER 0.1 | Multipath R=1/4, BLER 0.01 |
|---|---|---|---|---|
| Genie (true CFO, phase, channel) | 1.77 dB | 1.19 dB | 7.11 dB | 9.87 dB |
| Known-symbol bound (512 known symbols) | 1.75 dB | 1.17 dB | 7.08 dB | ≈ 9.85 dB |
| Blind 4th power + CRC + code-aided (Algorithm 1 + 2) | 3.62 dB | 6.65 dB | floor 0.46 | floor 0.45 |
| Blind NN (8 SPS) + CRC + code-aided | 4.81 dB | 7.78 dB | floor 0.51 | floor 0.50 |

1. **Does the NN improve anything? No.** The 8-SPS NN does something no symbol-rate estimator can: it
   picks the CFO cell from the waveform, even at −5 dB. But that only matters where the classical receiver
   fails, and the classical receiver never fails on the cell: it decodes every cell hypothesis and lets the
   CRC choose (cell error 1e-3 at 4 dB, 0 above). Where the classical receiver does fail, the cause is the fine
   CFO (the r⁴ threshold in AWGN, ISI in multipath), and the NN's fine estimate is no better there, and
   slightly worse. Net result: **+1.1–1.25 dB in AWGN, +0.75 dB and a higher floor in multipath.**
2. **Cost.** The NN needs ≈ 24.6M real MACs per burst (975k parameters) against ≈ 50–64k for the 4th-power
   stage: ≈ 400–500×. It saves ≈ 1.1 of ≈ 10 CA-SCL decodes per burst, worth well under 1M operations. It
   does not pay for itself in any regime simulated. The same pattern held for every NN in this project: the
   FFT-aided NN learned the ML estimator (A.3), and MP-NN learned MP-ML (B.3), always at higher cost.
3. **How close is the zero-overhead receiver to the known-symbol bound?**
   * AWGN, R = 1/2: **1.85 dB** away at BLER 1e-2. R = 1/4: **5.5 dB** away. The gap is the 4th-power
     threshold (Es/N0 ≈ 3–4 dB), so it is small for codes that need Es/N0 above it and large for low-rate codes.
     Once the first decode succeeds, the code-aided loop reaches the bound on the CFO itself (median equal to Known 512).
   * Multipath: **no usable operating point**. The blind receiver floors at BLER ≈ 0.45, while the
     known-symbol receiver (= Genie, within 0.05 dB) reaches 1e-2 at 9.9 dB. Even a known CFO with a blindly
     initialised channel loses ≈ 4.5 dB at BLER 0.1.
4. **What would close the gap** (where effort should go instead of a bigger NN):
   * **A few known symbols.** The code-aided loop already reaches the bound when it gets a correct first
     decode; a short pilot block or preamble would provide that bootstrap. Even a 32-symbol (6 %) preamble
     gives a cell- and phase-unambiguous coarse CFO, and in multipath a first channel estimate. This is the
     real trade-off for a "zero-overhead" design.
   * **A blind CFO estimator that survives ISI**, e.g. channel-agnostic cyclostationary / blind joint CFO +
     channel estimation, or iterating CMA ↔ CFO before the first decode. The r⁴ line is the weak link.
   * **More hypotheses instead of a better estimator.** Decoding is what resolves the ambiguities, so
     spending decodes on a few fine-CFO candidates (several r⁴ peaks) attacks the actual failure mode.
5. **Overall**: for CFO in this system the classical estimators (ML in AWGN, MP-ML in multipath, the 4th power
   + CRC for blind operation) are at or near the relevant bound, and no neural estimator built here beat them.
   The neural approach would only pay off for an impairment without a tractable model-based estimator.

### Conclusions on AWGN known-sequence estimation (full chain, A.3–A.5)

1. **Above ≈ −3 dB Es/N0 the choice of estimator doesn't matter.** SNR-aware NN and M&M give the same BLER
   (R = 1/2) or M&M is 0.1 dB better (R = 1/4); all estimators are within 1–4 % of each other in MSE.
2. **So the cheapest estimator is the best one**: ML (7.2k MACs, 1.13–1.39× the ideal CRB from −5 to 10 dB on the
   full chain). The neural estimators cost 67–73k MACs, need training (and the SNR), and give no BER/BLER benefit,
   except for a low-rate code near Es/N0 = −4 dB, where the SNR-aware NN (or ML) avoids M&M's breakdown.
3. **The residual CFO error matters a lot for long packets**: a 128-symbol estimate creates an error floor
   on a 512-symbol coded packet (full chain: ≈ 0.65 dB loss at BLER 0.1, BLER 1e-2 not reached by 3.5 dB, vs the
   Genie at 2.86 dB for R = 1/2); the flat region ends at |e| ≈ 1e-4.
4. **Optimising the estimator at −5 … −3 dB only pays for low-rate codes**: R = 1/2 and 1/4 fail there even with a
   Genie; R = 1/10 at Es/N0 = −4 dB is where the NN's RMSE (5.3e-4) is usable and M&M's (1.75e-3) is not.
5. **What helps is a lower CRB, not a better estimator**: a 512-symbol estimate removed the floor completely
   (A.6, legacy symbol-rate). In the full chain, a CFO correction before the matched filter (or a larger roll-off,
   A.3.2) would also remove the Genie's matched-filter loss.

---

## Verification

* **Full Tx/Rx chain and AWGN results (A.1)**: chain = `main.py` to 1.6e-15 with the same noise; noise variance 1/SNR
  and white after the matched filter; matched-filter gain and phase reference = theory; polar Genie at CFO = 0 =
  the pure-AWGN result; the two polar runs agree at e = 0; ML = brute-force periodogram; M&M = `main.py` and the paper
  (eqs. (3), (8), (9)); M&M and SNR-aware NN unbiased.
* Vectorised Tx/Rx chain in `ber_experiment.py` vs. a per-frame chain built from `main.py`: max difference 4e-15.
* Batched hybrid estimate vs. `UnifiedHybridCFOEstimator.estimate`: max difference 2e-8.
* ML estimator vs. brute-force fine-grid periodogram search: median difference 3e-8.
* Uncoded BER vs. fixed CFO error vs. the closed form: agree to 3 digits.
* Polar decoder: CRC self-check, F^⊗n involution, noiseless decoding, SC > SCL > CA-SCL ordering.
* Stage 1 Genie / Known-512 curves vs. the main polar study (`polar_results_ebn0.npy`): same BLER at the same Eb/N0.
* Stage 2 with `--channel awgn` vs. Stage 1: same BLER within Monte-Carlo noise (B.4).
* 8-SPS front end: every 8th sample has noise variance 1/SNR and no correlation (A.8).

## Bugs fixed

| Where | Problem | Fix |
|---|---|---|
| `main.apply_awgn`, `ber_experiment.transmit` | Signal power averaged over the filter tails (+0.32 dB real SNR) | Es = total energy / number of symbols |
| `main.py` main loop | Estimator and checkpoint reloaded in each of 150,000 iterations | Loaded once |
| `main.snr_sweep_nn`, `cfo_sweep_nn` | `device` defined only under `__main__` | Module level |
| `plots.plot_cfo_sweep` | Wrong title / legend | Corrected |
| `zero_overhead_mp.cma_taps` | Equalizer delay search never reached the right alignment; phase-blind decisions | Offset search over −(E−1)..T; 4th-power phase fix before deciding |
| `zero_overhead_mp` decode counter | Code-aided decodes/equalizations counted once per batch instead of per burst | Counted per burst (B.4 gives corrected totals) |

## Assumptions and limitations

* Perfect timing and frame synchronisation everywhere; Es/N0 known to the receiver (LLR scaling, equalizers).
* Part A (A.1–A.5) uses the full chain: the matched filter is fixed at 0 Hz, so a large CFO costs signal and adds ISI.
  A.6–A.8 and Part B are still on the symbol-rate model, which omits that loss.
* The 128-symbol estimators in A.5 use the packet's first 128 symbols as known (a training sequence); its overhead
  is not charged in Eb/N0.
* MSE near and below the estimators' threshold (≤ −4 dB) is dominated by rare outliers; 10⁶ trials per point there.
* Stage 3 front end: the CFO is applied after the matched filter (same idealisation), the noise is real
  matched-filtered white noise. The un-truncated shifted signal spectrum slightly favours spectral (cell)
  detection, i.e. the NN's cell accuracy is if anything optimistic. It still did not help.
* Multipath: symbol-spaced taps, block fading (static over a burst), no Doppler, guard ≥ channel memory.
* Monte-Carlo resolution: points with no errors are not plotted (BLER < 1/frames).
