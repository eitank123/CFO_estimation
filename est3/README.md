# est3: modern pilot-based CFO estimators vs the blind receiver (AWGN)

This study adds the CFO estimators used in practice and in recent papers to the project's comparison: the 128-pilot ML family, joint CFO/channel ML, interpolated-DFT, periodic-preamble (Schmidl-Cox / Moose, BLUE), distributed-pilot (ML, DVB-S2 phase-difference) and three NNs (Clustering-NN, CNN classification + refinement, CNN regression). All of them run on identical packets through the full Tx/Rx chain. They are scored on CFO accuracy against the CRB of their own pilot layout and on BLER with one shared receiver back-end. The blind receiver ([BLIND_IMPLEMENTATION/](../BLIND_IMPLEMENTATION/)) is the reference.

**Channel: AWGN only.** The Rician (NTN-TDL-D) part was removed on request. Its code, results and plots are gone, and the NNs were retrained on AWGN only.

| File | Content |
|---|---|
| `est3/common.py` | Full chain (bit-identical to `blind_cfo.transmit_full`), pilot layouts, CRBs, the gain/phase + LLR back-end |
| `est3/estimators.py` | Classical estimators and their analytic MAC counts |
| `est3/nn.py` | Clustering-NN, CNN classification + refinement, CNN regression: data, training, inference, MACs |
| `est3/run_est.py` | CFO accuracy sweep (−12…16 dB, 10⁵ bursts per point); `validate` holds the smoke checks |
| `est3/run_bler.py` | BLER with the same back-end for every estimator |
| `est3/plots.py` | All figures in `est3/plots/` |

Results are in `est3/results/` (`est.json`, `bler_k*.json`), models in `est3/models/` and logs in `est3/logs/`. Files named `superseded_*` are earlier runs that are kept but no longer used.

## 1. Conventions

- **CFO:** f is in cycles per symbol, applied per 8-SPS sample as e^{j2πf·m/8} before the matched filter, with |f| ≤ 0.03. Every estimator works on the symbol-rate MF output.
- **SNR:** Es/N0 at the MF output (unit-energy RRC, β = 0.25, span 10). There is no Eb/N0 anywhere.
- **Pilots inside the packet:** the 128 pilots are known symbols of the 1024-symbol packet, so they add no energy and the SNR does not drop. They do carry no data, which costs **12.5 % of throughput**: (1024 − 128)/1024 = 0.875. The simulation keeps the code at N = 2048 and the pilot symbols are codeword symbols the receiver knows (the existing benchmarks' convention). This slightly *favours* the pilot receivers, because they keep the full code length.
- **Identical packets and seeds:** all estimators see the same data, CFO, phase and noise, and no estimator draws random numbers. Evaluation seeds are below 10⁷, NN training uses 10⁷+ and validation 2·10⁷, so they share no realisation. The true CFO is used only for scoring.

## 2. Pilot layouts (128 pilots each)

| Layout | Positions | Used by |
|---|---|---|
| `contig` | symbols 0…127 (preamble) | M&M, ML direct, Jacobsen-Candan, joint ML, NNs |
| `periodic` | 8 repetitions of 16 symbols | Schmidl-Cox / Moose, BLUE (MM99) |
| `split2x64` | 2 blocks of 64 (the project's split-pilot positions) | distributed ML, DVB-S2 |
| `dist4x32`, `dist8x16` | 4 × 32 / 8 × 16 blocks centred at (b + ½)·1024/blocks | distributed ML, DVB-S2 |

A codeword cannot be periodic. So the periodic sources estimate from a separate periodic burst with the packet's CFO and phase and independent noise of the same SNR (drawn for every batch). Statistically this is a packet whose first 128 symbols are periodic pilots.

Spreading the pilots lowers the CRB by up to about 8× (dist8x16), because the CRB scales with the spread Σ(n − n̄)². The cost is lobe ambiguity at low SNR: the likelihood has side lobes 1/D apart, where D is the block spacing.

## 3. Estimators

**Contiguous preamble (z_n = r_n·s_n\*, n = 0…127)**
- **M&M** (Mengali & Morelli 1997): the project's existing baseline (`polar_ber_experiment.bench_estimate("mm")`).
- **ML direct:** f̂ = argmax_{|f|≤0.03} |Σ z_n e^{−j2πfn}|², the exact ML with unknown gain and phase, with no coarse stage. Variants: a zero-padded FFT of 128…4096 points, or a direct grid with a 10⁻⁴ step, refined by parabolic interpolation, Aboutanios-Mulgrew, Newton or golden-section. The reference is FFT 4096 + golden-section on the 3 highest peaks (the single-peak version missed the global maximum in 0.5 % of bursts at −8 dB). The default is **FFT 512 + 2 Newton steps** (15,872 MACs).
- **Jacobsen-Candan** (Candan 2013): an unpadded 128-point FFT, then δ = tan(π/L)/(π/L)·Re{(X₋ − X₊)/(2X₀ − X₋ − X₊)}.
- **Joint CFO/channel ML** (Morelli & Mengali 2000): r = D(f)·S·h + w with an Lh-tap channel. Profile likelihood ||Qᴴ D(f)ᴴ r||² with S = QR, Lh FFTs plus Newton. The fast form matches a dense-grid lstsq reference to 10⁻¹⁰, and Lh = 1 equals ML direct exactly. On AWGN the extra taps only cost accuracy (the unknown-tap CRB is 1.04× at Lh = 3 and 1.08× at Lh = 8).

**Periodic preamble (8 × 16)**
- **Schmidl-Cox / Moose:** f̂ = arg(Σ r_n r\*_{n−Q})/(2πQ), Q = 16.
- **BLUE** (Morelli & Mengali 1999): weighted increments of the autocorrelation phase, U = 8, H = 4, w(m) = 3[(U−m)(U−m+1) − H(U−H)] / [H(4H² − 6UH + 3U² − 1)].

**Distributed pilots**
- **Distributed ML:** the same likelihood on the block positions (FFT 8192 + 3 Newton steps).
- **DVB-S2 block phase-difference** (Casini et al. 2004): non-coherent block periodograms give f_c, then f̂ = f_c + arg(Σ B_{b+1} B_b\*)/(2πD).

**Neural networks** (trained on AWGN, SNR ∈ {−10, −7, …, 14} dB only, so 20 of the 29 test SNRs are unseen)
- **Clustering-NN** (Li Zhen et al., IEEE WCL 2024), adapted to a random QPSK preamble:
  - the input is the 128-bin periodogram of z (the PDP of a ZC preamble is a permuted version of it);
  - 9 integer clusters (ε = 128f ∈ [−3.84, 3.84]) from a seeded semi-supervised K-means;
  - the online cluster is chosen by peak position (eq. 7);
  - SMDR keeps the ±4 bins around the cluster;
  - one BPNN 9 → 5 tanh → 1 tanh per cluster.
- **CNN classification + refinement:**
  - input z/rms(z) as 2 × 128;
  - backbone: a 7-tap conv stem, 6 dilated residual blocks with 32 channels, FC 256;
  - head: 24 CFO bins of width 2.5·10⁻³ plus a residual per bin;
  - trained on a GPU (RTX 6000 Ada), 60 epochs × 2000 steps × 512 bursts, all fresh.
- **CNN direct regression:** the same backbone with one output.

## 4. Bounds

- **Own-layout CRB** (known symbols, unknown phase): CRB = 1/(2·SNR·(2π)²·Σ_n (n − n̄)²), with n the pilot positions. For `contig` this is 3/(2π²·SNR·L(L² − 1)).
- **Joint ML** is also shown against the unknown-tap CRB with Lh taps as nuisance parameters.

## 5. BLER back-end (identical for every estimator)

1. Estimate f̂ from the receiver's own pilots.
2. Apply the pre-MF correction at f̂ (`blind_fast.premf`, as all existing benchmarks do).
3. For each CFO hypothesis f_h:
   1. LS complex gain (amplitude + phase) on the receiver's own pilots at f_h;
   2. LLRs;
   3. CA-SCL-8 (N = 2048, CRC-16);
   4. the **same acceptance as the blind receiver**: re-encoding check ρ > max(0.12, ½√(s/(1+s)), RHO_N(rate, SNR)·√(s/(1+s))).
4. Run the CRC search "first pass": f̂ + k·7.5·10⁻⁵, k = ±1, ±2, …, |k| ≤ ⌈4·1.3·√CRB_contig / step⌉, stopping at the first accepted pass.

**Genie CFO** uses the true CFO with the same estimated gain and phase.

**Correction made during this study.** The first BLER run accepted a CRC pass with only the loose threshold, max(0.12, ½√(s/(1+s))). A wrong list path close to the true codeword passes that check, and every pilot receiver then showed a floor of about 10⁻⁴–10⁻³ in which **all** errors were undetected. Those results are kept as `results/superseded_loose_bler_*.json`. The final run uses the blind receiver's per-rate RHO_N table, so both sides have the same acceptance rule.

## 6. Results: CFO accuracy (10⁵ bursts per point)

RMSE / √CRB of each estimator's **own** layout (1.00 = efficient); in brackets, the fraction of bursts outside the CRC-search window.

| Estimator | MACs | −6 dB | −2 dB | 0 dB | 4 dB | 10 dB | 16 dB |
|---|---|---|---|---|---|---|---|
| M&M | 25,216 | 5.18 (2·10⁻²) | 1.03 | 1.02 | 1.01 | 1.00 | 1.00 |
| ML direct FFT 512 + Newton ×2 (default) | 15,872 | 1.02 (2·10⁻⁵) | 1.01 | 1.01 | 1.00 | 1.00 | 1.00 |
| ML direct FFT 256 + parabolic | 5,130 | 1.04 | 1.04 | 1.05 | 1.09 | 1.30 | 1.93 |
| ML direct FFT 4096 + golden (reference) | 360,448 | 1.02 | 1.01 | 1.01 | 1.00 | 1.00 | 1.00 |
| Jacobsen-Candan (FFT 128) | 2,472 | 1.61 (10⁻³) | 1.49 | 1.50 | 1.51 | 1.52 | 1.53 |
| Joint ML Lh = 3 | 52,564 | 1.09 (10⁻⁴) | 1.04 | 1.04 | 1.03 | 1.02 | 1.02 |
| Joint ML Lh = 8 | 177,424 | 1.65 (9·10⁻⁴) | 1.09 | 1.07 | 1.05 | 1.04 | 1.04 |
| Schmidl-Cox / Moose [periodic] | 468 | 17.3 (0.3) | 10.3 (0.1) | 6.5 (0.07) | 2.06 (10⁻²) | 1.54 | 1.38 |
| BLUE MM99 [periodic] | 2,128 | 13.4 (0.1) | 8.2 (0.03) | 5.3 (10⁻²) | 1.29 | 1.03 | 1.01 |
| Distributed ML [2×64] | 237,568 | 15.8 | 15.5 (0.1) | 13.6 (0.07) | 5.2 | 1.01 | 1.00 |
| Distributed ML [4×32] | 237,568 | 34.6 (0.4) | 33.9 (0.1) | 29.6 (0.07) | 11.3 | 1.00 | 1.00 |
| Distributed ML [8×16] | 237,568 | 68.5 (0.3) | 67.8 (0.1) | 57.8 (0.06) | 21.7 | 1.00 | 1.00 |
| DVB-S2 phase-difference [4×32] | 43,064 | 37.0 (0.4) | 35.8 (0.2) | 30.9 (0.08) | 11.8 | 1.06 | 1.06 |
| DVB-S2 phase-difference [8×16] | 84,040 | 78.4 (0.4) | 75.0 (0.2) | 64.3 (0.08) | 24.5 | 1.32 | 1.32 |
| Clustering-NN | 2,787 | 2.92 (0.05) | 3.07 (0.08) | 3.56 (0.1) | 5.16 (0.4) | 9.8 (0.7) | 19.4 (0.8) |
| CNN classification + refinement | 8.98 M | 1.11 (7·10⁻⁵) | 1.06 | 1.05 | 1.03 | 1.04 | 1.12 |
| CNN regression | 8.97 M | 1.06 (4·10⁻⁵) | 1.07 | 1.09 | 1.12 | 1.22 | 1.61 |

**Accuracy findings**
- **ML direct is efficient everywhere with no coarse stage.** From −6 dB on it is within 2 % of the CRB, at 15.9 k MACs.
  - It is cheaper than M&M (25 k MACs), which loses 2 % of bursts to outliers at −6 dB.
  - Grids coarser than FFT 512, or without refinement, have a precision floor at high SNR.
- **The CNN classification + refinement network reaches the CRB to within 3–12 %,** but costs 9 M MACs, 570× the ML. It brings no gain on AWGN, where ML is already optimal.
- **The CNN regression network** drifts to 1.6× the CRB at 16 dB, the usual regression-head precision floor.
- **The Clustering-NN does not reach the CRB in this setting.** Its fractional regression on 9 features has a precision floor, at 19× the CRB at 16 dB. With a random preamble, its periodogram input carries less than a ZC PDP does.
- **Jacobsen-Candan** sits at a constant 1.5× the CRB, the known efficiency loss of an unpadded 3-bin interpolator.
- **Periodic preambles** (Moose, BLUE) are very cheap, but need about 4 dB (BLUE) or 10 dB (Moose) more SNR before they are efficient. At the SNRs of the low-rate codes they are far from the CRB.
- **Distributed pilots** have a CRB up to 8× lower, but they only reach it from about 10 dB. Below that, lobe ambiguity dominates. The 2-block layout is the least affected.

## 7. Results: BLER

Figures: `plots/bler_R1_10.png`, `bler_R2_5.png`, `bler_R1_2.png`, each with BLER, throughput and residual CFO. Points have 60,800 packets each (fewer at the lowest SNR), so one error is a BLER of 1.6·10⁻⁵. The blind points are the final blind receivers (`small_cfo/blind/results/blind_ber.json`), with 10⁵–4·10⁵ packets per point.

**R = 1/10 (A = 205)**

| Receiver | −5 dB | −4.5 dB | −4 dB | −3 dB | −2 dB | −1 dB | 0 dB |
|---|---|---|---|---|---|---|---|
| **Blind, 0 pilots** | 1.75·10⁻⁴ | 3.5·10⁻⁵ | 5·10⁻⁶ | 0 | 0 | 0 | 0 |
| Genie CFO | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ML direct | 4.9·10⁻⁵ | 8.2·10⁻⁵ | 1.6·10⁻⁵ | 0 | 1.6·10⁻⁵ | 0 | 3.3·10⁻⁵ |
| Joint ML Lh = 3 | 1.6·10⁻⁵ | 3.3·10⁻⁵ | 0 | 0 | 4.9·10⁻⁵ | 1.6·10⁻⁵ | 3.3·10⁻⁵ |
| CNN classification + refinement | 6.6·10⁻⁵ | 6.6·10⁻⁵ | 1.6·10⁻⁵ | 3.3·10⁻⁵ | 0 | 3.3·10⁻⁵ | 4.9·10⁻⁵ |
| CNN regression | 3.3·10⁻⁵ | 4.9·10⁻⁵ | 0 | 0 | 8.2·10⁻⁵ | 3.3·10⁻⁵ | 0 |
| M&M | 3.4·10⁻³ | 1.4·10⁻³ | 3.9·10⁻⁴ | 0 | 1.2·10⁻⁴ | 3.3·10⁻⁵ | 0 |
| Jacobsen-Candan | 3.6·10⁻⁴ | 3.3·10⁻⁴ | 2.5·10⁻⁴ | 2.3·10⁻⁴ | 1.6·10⁻⁴ | 1.6·10⁻⁴ | 8.2·10⁻⁵ |
| Distributed ML 2 × 64 | 3.5·10⁻³ | 2.1·10⁻³ | 1.1·10⁻³ | 2.3·10⁻⁴ | 1.6·10⁻⁵ | 6.6·10⁻⁵ | 2.1·10⁻² |
| BLUE (periodic) | 9.0·10⁻² | 7.4·10⁻² | 6.6·10⁻² | 4.2·10⁻² | 2.9·10⁻² | 1.7·10⁻² | 1.0·10⁻² |
| Clustering-NN | 3.4·10⁻² | 3.4·10⁻² | 3.7·10⁻² | 3.8·10⁻² | 4.1·10⁻² | 5.4·10⁻² | 5.9·10⁻² |
| Moose, DVB-S2, distributed 4 × 32 / 8 × 16 | 0.24–0.34 | | | 0.13–0.22 | | | 0.03–0.08 |

**R = 2/5 (A = 819)**

| Receiver | 0.5 dB | 1.0 dB | 1.5 dB | 2.0 dB | 3.0 dB |
|---|---|---|---|---|---|
| **Blind, 0 pilots** | 2.1·10⁻³ | 8·10⁻⁵ | 0 | 0 | 0 |
| Genie CFO | 2.6·10⁻³ | 8.2·10⁻⁵ | 0 | 0 | 0 |
| ML direct | 2.8·10⁻³ | 8.2·10⁻⁵ | 3.3·10⁻⁵ | 1.6·10⁻⁵ | 0 |
| M&M | 2.6·10⁻³ | 9.9·10⁻⁵ | 3.3·10⁻⁵ | 0 | 1.6·10⁻⁵ |
| CNN classification + refinement | 2.7·10⁻³ | 8.2·10⁻⁵ | 0 | 0 | 0 |
| CNN regression | 2.8·10⁻³ | 1.2·10⁻⁴ | 3.3·10⁻⁵ | 1.6·10⁻⁵ | 1.6·10⁻⁵ |
| Joint ML Lh = 3 | 2.6·10⁻³ | 1.3·10⁻⁴ | 6.6·10⁻⁵ | 1.6·10⁻⁵ | 3.3·10⁻⁵ |
| Jacobsen-Candan | 3.0·10⁻³ | 3.3·10⁻⁴ | 3.8·10⁻⁴ | 1.6·10⁻⁴ | 1.3·10⁻⁴ |
| BLUE (periodic) | 9.5·10⁻³ | 5.0·10⁻³ | 3.8·10⁻³ | 2.8·10⁻³ | 8.7·10⁻⁴ |
| Distributed / DVB-S2 (all layouts) | 0.055–0.065 | 0.042–0.048 | 0.03 | 0.022–0.025 | 0.011–0.012 |
| Moose | 4.3·10⁻² | 2.9·10⁻² | 2.1·10⁻² | 1.5·10⁻² | 5.1·10⁻³ |
| Clustering-NN | 0.13 | 0.13 | 0.15 | 0.17 | 0.18 |

**R = 1/2 (A = 1024)**

| Receiver | 2.0 dB | 2.5 dB | 3.0 dB | 4.0 dB | 5.0 dB |
|---|---|---|---|---|---|
| **Blind, 0 pilots** | 1.4·10⁻⁴ | 0 | 0 | 0 | 0 |
| Genie CFO | 3.3·10⁻⁴ | 0 | 0 | 0 | 0 |
| ML direct | 3.5·10⁻⁴ | 0 | 0 | 0 | 1.6·10⁻⁵ |
| M&M | 3.1·10⁻⁴ | 0 | 1.6·10⁻⁵ | 0 | 1.6·10⁻⁵ |
| CNN classification + refinement | 3.6·10⁻⁴ | 3.3·10⁻⁵ | 0 | 1.6·10⁻⁵ | 0 |
| CNN regression | 3.3·10⁻⁴ | 1.6·10⁻⁵ | 0 | 0 | 0 |
| Joint ML Lh = 3 | 2.6·10⁻⁴ | 4.9·10⁻⁵ | 1.6·10⁻⁵ | 3.3·10⁻⁵ | 0 |
| Jacobsen-Candan | 7.7·10⁻⁴ | 3.6·10⁻⁴ | 9.9·10⁻⁵ | 3.0·10⁻⁴ | 3.3·10⁻⁵ |
| BLUE (periodic) | 3.0·10⁻³ | 1.6·10⁻³ | 1.0·10⁻³ | 3.3·10⁻⁴ | 1.5·10⁻⁴ |
| Distributed / DVB-S2 (all layouts) | 0.023–0.025 | 0.015–0.018 | 0.010–0.012 | 0.004–0.005 | 1.4·10⁻³ |
| Moose | 1.9·10⁻² | 1.4·10⁻² | 6.3·10⁻³ | 3.0·10⁻³ | 1.1·10⁻³ |
| Clustering-NN | 0.20 | 0.22 | 0.21 | 0.28 | 0.32 |

**BLER findings**
- **The best pilot receivers are at the genie, so the CFO is no longer their bottleneck.**
  - These are ML direct, joint ML, the two CNNs, and M&M from −4 dB on.
  - Their remaining errors in the waterfall are the code's own errors.
  - Above it, a few residual undetected errors remain: CRC passes on a wrong codeword that also clear the tight re-encoding check, about 1–5 per 60,800 packets. For example, ML direct at R = 1/10 had 12 errors in 425,600 packets from −5 to 0 dB, all undetected. Blind had 0 undetected in 1.4 M packets.
- **Blind vs the best pilot receivers, on BLER alone:**
  - **R = 1/10, −5 dB:** pilots are better (1.6–6.6·10⁻⁵ vs 1.75·10⁻⁴).
  - **R = 1/10, −4.5 dB:** about equal.
  - **R = 1/10, ≥ −4 dB:** blind is equal or better.
  - **R = 2/5:** equal (8·10⁻⁵ vs 8.2·10⁻⁵ at 1 dB).
  - **R = 1/2, 2 dB:** blind is better (1.4·10⁻⁴ vs 2.6–3.6·10⁻⁴), from its extra decoding diversity (joint list, retries).
- **ML direct beats M&M at R = 1/10 below −4 dB** (4.9·10⁻⁵ vs 3.4·10⁻³ at −5 dB), because M&M has outliers there. At R = 2/5 and 1/2 the two are equal.
- **Jacobsen-Candan, the periodic preambles, the distributed / DVB-S2 layouts and the Clustering-NN are not competitive at these SNRs.**
  - Jacobsen-Candan's 1.5× CRB leaves residuals the CRC search does not always fix.
  - The periodic estimators have outliers.
  - Distributed pilots have lobe ambiguity. The CRC search window recovers a lobe jump only at low SNR, where it is wide. That is why distributed 2 × 64 at R = 1/10 jumps from 6.6·10⁻⁵ at −1 dB to 2.1·10⁻² at 0 dB.
  - The Clustering-NN has a precision floor.

**Throughput.** Delivered data per packet is A·(1 − BLER)·(1024 − n_pilots)/1024.
- Every 128-pilot receiver is capped at 0.875·A.
- Blind delivers 0.9998·A at R = 1/10 −5 dB and 0.998·A at R = 2/5 0.5 dB.
- So blind delivers **12.5–14 % more data per packet** than the best pilot receiver at every operating point here. The pilots' BLER advantage at R = 1/10 −5 dB (about 1.5·10⁻⁴) is worth 0.015 % of throughput.

**Cost per packet**

| | MACs |
|---|---|
| ML direct | 15.9 k |
| M&M | 25 k |
| CNNs | 9.0 M |
| Pilot back-end (each CA-SCL-8 decode) | 0.19 M, ×(1 + extra decodes) |
| Blind (mean total) | 0.55–4.2 M |
| Blind (critical path on 32 cores) | 0.43–1.7 M |

Blind costs more in total. Its latency on 32 cores is comparable to a pilot receiver that runs a few CRC-search decodes.

## 8. Limitations

- AWGN only, with a static CFO over the packet and ideal timing and SNR knowledge.
- The pilot receivers use the same N = 2048 code as blind. A real pilot system with 896 data symbols would need a higher code rate (or a punctured code) for the same data bits, which this simulation does not charge.
- The MAC counts are analytic for the classical estimators and per layer for the NNs. The BLER back-end's decodes are not part of the estimator MACs.

## 9. Reproduce

```bash
python est3/nn.py --kind cnn-cr --device cuda --epochs 60 --steps 2000 --batch 512 --workers 14   # and cnn-reg, cluster
python est3/run_est.py --part base ; python est3/run_est.py --part nn ; python est3/run_est.py merge
python est3/run_bler.py --rate 1/10 --snrs -6 -5.5 -5 -4.5 -4 -3 -2 -1 0 --part kb10              # etc., see jobs/
python est3/plots.py
```
