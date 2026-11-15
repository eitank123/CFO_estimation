# Literature survey: blind CFO + phase acquisition for short polar packets (2026-11-13)

Scope: the four focus questions of the main session (search ranking, retry gating / early termination, false-alarm
control, deployment). Our receiver as read from `BLIND_IMPLEMENTATION/README.md`, `03_path_metric.md`, `04_search.md`,
`05_decoding.md`, `06_acceptance.md`, the 2026-11-13 section of `testing/README.md` and `results/report_t-dump15a.md`
(R = 0.15, -4 dB: 199 failures in 50k packets, of which 117 are "true CFO region not among the Stage 3 candidates",
65 "sync / list", 17 "order / budget"; search metrics + refinement scoring = 64 % of the 7.32 M MACs per packet).

Reading depth: "full" = full text read (arXiv HTML / ar5iv); "abstract" = abstract page only; "snippet" = only search
result text or an index page could be read (PDF not parseable or paywalled). Several key PDFs (Herzet et al. 2007,
Wymeersch & Moeneclaey 2005 full text, Strodthoff et al. Globecom 2018, Giard 2017 PDF, Qualcomm patent PDF) could not be
read in full; this is marked per source.

**Main comparability caveat.** No paper found does what we do: blind *frequency* offset over a wide range (|f| <= 0.03
cycles/symbol, i.e. 3 % of the symbol rate) with a polar code of N = 2048. The closest works handle an unknown *phase*
(or block-fading gain) only, at N = 128 ... 512, BPSK / QPSK, AWGN. Numbers below are not directly comparable to ours.
Several searches for "polar + SC/SCL path metric + CFO search" returned nothing beyond those phase-only papers; as far
as this survey can tell, the joint CFO-grid x SC-metric search with checkpoints is not published.

---

## 1. Ranked actionable findings (at most 5)

### 1. Rank the Stage 2 cells with a frozen-only detection metric (drop rate-1 and SPC penalties) - zero extra MACs
- Source: Giard, Balatsoukas-Stimming, Burg, "Blind Detection of Polar Codes", SiPS 2017
  ([arXiv 1705.02111](https://ar5iv.arxiv.org/html/1705.02111), full) and the follow-up "On the Tradeoff Between Accuracy
  and Complexity in Blind Detection of Polar Codes", ISTC 2018 ([arXiv 1807.00655](https://ar5iv.arxiv.org/html/1807.00655), full).
- What they do: to tell a polar codeword from noise they do **not** use the path metric. Their Fast-SSC detection metric
  is D += (1/n) sum(a_i) at rate-0 nodes, (1/n)|sum a_i| at REP nodes, (-1)^parity min|a| at SPC nodes, and **rate-1
  nodes are ignored** ("no redundancy useful for detection"). They state that the list path metric measures the
  likelihood of a candidate *given* that a codeword was sent, while detection needs the likelihood that the observation
  is a codeword at all. In the 2018 paper the **SPC updates hurt accuracy at high BLER** (crossover at t = 5 -> 6 visited
  nodes); without SPC updates, 40 of 44 candidates are dismissed at MDR 1e-2 (N = 256, K = 24 + CRC-16, BPSK).
- Why it matters here: a wrong CFO cell is, for the decoder, close to "not a codeword". Our ranking (z-test on the
  list-1 metric M of `03_path_metric.md`) adds rate-1 penalties sum ln(1+e^-|a|) and SPC penalties, which carry no
  CFO information and add variance; at R = 0.15 there are more information nodes than at R = 1/10, and the R = 0.15 -4 dB
  error mode is exactly a ranking failure (117 / 199).
- Cost: none in MACs (same pass, different accumulation; the leaf penalties are already returned by `metric_nodes`).
- How to test: offline first, if the t-dump15a / decode dumps keep per-cell partial metrics split by node type (the
  checkpoint NN already uses a "rate-0 part" z-trajectory, so the split exists in code). Rank of the true cell under
  (a) total M, (b) rate-0 + REP only, (c) Giard's linear form, at 0.15 -4 / -3 dB and 1/10 -5 dB. If (b) or (c) lifts the
  true cell into the candidate set for a large share of the 117, add a flag (e.g. `rank_metric`) for the checkpoint
  z-tests and run 64k paired packets at 0.15 -4 dB, 1/10 -5 dB, 2/5 0.5 dB.
- Expected gain: unknown in numbers (their setting is detection, not CFO ranking); possible effect is fewer Stage 2
  failures at the same MACs, or a tighter tau at the same BLER.

### 2. Phase-equivariant code design: remove the pi/2 phase hypotheses from the search
- Source: Geiselhart, Gauger, Krieg, Clausius, ten Brink, "Phase-Equivariant Polar Coded Modulation", 2023
  ([arXiv 2305.01972](https://arxiv.org/html/2305.01972), full).
- What they do: with Gray QPSK, a pi/2 rotation of the received block equals a bit permutation (an automorphism of the
  polar code) plus a bit flip on one row; freezing 2 extra "rotation bits" makes the SC decoder equivariant, so **one
  decode at theta returns the same metric as at theta + pi/2** and the rotation count is read from 2 decoded bits.
  Cost: 2 bits of rate. Gain vs pilot-assisted: 0.8 dB (QPSK) and up to 2 dB (16-QAM), N = 128 ... 256, SC / L = 8.
  Their list variant starts the L paths on different phase hypotheses and keeps the best metric, which is our joint list
  decoding (05, 5.3).
- Why it matters here: we score q in {0, 2} (2 phases) per cell from -1 dB up and q in {0,1,2,3} (4) at R = 0.15; with an
  equivariant code half of these are redundant (2 -> 1, 4 -> 2). Search metrics + refinement scoring are 64 % of the MACs
  at 0.15 -4 dB, so the search part could drop by up to ~half (my estimate, not measured). The project memory notes
  that the present code is "NOT closed under pi/2 (rot_test)": that is exactly what this construction fixes.
- Cost and risks: a change of the transmitted code (2 frozen bits + the symbol-to-bit mapping that matches the
  automorphism), RHO_N recalibration, and the 128-pilot reference should be rerun on the same code for a fair comparison.
  A 2026 paper ([arXiv 2602.17979](https://arxiv.org/html/2602.17979)) notes the construction is fragile under rate
  matching (puncturing / shortening); our N = 2048 mother code fills 1024 QPSK symbols exactly, so that concern should not
  apply.
- How to test: a unit check first (metric(theta) == metric(theta + pi/2) on noisy packets, cluster job), then paired
  BLER at 0.15 -4 / -1 dB and 2/5 0.5 dB with q in {0} (or {0, 1}).

### 3. Score the last-checkpoint survivors with a small-list (marginalised) metric before cutting to candidates
- Source: Yuan, Coskun, Kramer, "Polar-Coded Non-Coherent Communication", 2021
  ([arXiv 2102.10719](https://ar5iv.arxiv.org/html/2102.10719), full).
- What they do: estimate the unknown phase by maximising p(y | theta, u_F = 0), which sums over the information bits;
  the sum is approximated by an SCL pass with list L_e up to bit beta, followed by a coarse-fine search over theta and
  a second-stage SCL-8 decode. This is our Stage 2 + Stage 3 structure, for phase only (N = 128, K = 32 + CRC-6, QPSK).
  Results: within 0.3 dB of coherent and ~1.5 dB better than 14-pilot PAT at FER 1e-4 with L_e = 8, beta = 113 of 128;
  L_e = 1 gives FER 3.5e-4 vs 2.4e-5 for perfect CSI at 1 dB; stopping at beta = 47 (before the first information bit)
  is **worse than PAT**.
- Why it matters here: our ranking uses a list-1 (max) metric; the list-1 hard decisions on information bits are what
  becomes unreliable at -4 dB. A list-L_e metric log-sum-exp over the list paths is a better approximation of the CFO
  likelihood. Applied only to the ~32-64 survivors of the last checkpoint, the extra cost is about L_e times the
  remaining partial pass for those cells.
- How to test: flag for the last checkpoint (L_e = 2 or 4, LSE of the L_e PMs); 64k paired at 0.15 -4 dB and 1/10 -5 dB;
  measure the "true region not among candidates" count from the dump report and MACs per core.
- Note: the earlier "in-cell retry / near-miss rescoring" (project memory) re-scored cells at new CFO offsets with the
  same list-1 metric; this is a different metric, so it is not a repeat of that dead end.

### 4. Retry gating is established practice; extend it to an in-decode abort of the main CA-SCL-8 decode
- Sources: Strodthoff et al., "Enhanced Machine Learning Techniques for Early HARQ Feedback Prediction in 5G", IEEE JSAC
  2019 ([arXiv 1807.10495](https://ar5iv.arxiv.org/html/1807.10495), full); Sarkis, Jiang, Lin, Yang (Qualcomm),
  "Early-termination techniques for polar list decoders", US 10615825 B2, 2020
  ([Google Patents](https://patents.google.com/patent/US10615825B2/en), description read); Yao & Ma, "Low-Complexity PSCL
  Decoding of Polar Codes", 2024 ([arXiv 2405.13255](https://arxiv.org/abs/2405.13255), abstract).
- What they do: Strodthoff et al. predict decoding failure from decoder reliability features (VNR from the first 5 of
  50 LDPC iterations, rate-1/5 LDPC, 360-bit TB) with logistic regression, random forest and a supervised autoencoder,
  threshold moved on an imbalanced problem: LR ~ RF ~ SAE (AUC-PR 0.905 / 0.907 / 0.908 at 4 dB, subcode 5/6), all only
  slightly above a hard threshold on the best single feature (0.902). The Qualcomm patent stops a polar list decode
  when the **spread of the list path metrics** (max - min, normalised; or std / percentiles) falls below a threshold
  after a minimum number of bits, aimed at PDCCH blind decoding of noise / wrong candidates. Yao & Ma prune with two
  SNR-dependent thresholds (one on path reliability, one on the probability that the correct path is in the list).
- Comparison with ours: our logistic gate on 13 failed-decode features (pm_gap, pm_spread, syndromes, LLR stats) is the
  same family; our "logistic = MLP" finding matches Strodthoff et al. (LR as good as the more complex models). Our gate
  acts only *after* a failed decode; the patent acts *during* the decode.
- What to borrow: an in-decode abort on PM spread / PM-vs-expected at fixed points (e.g. bit 1/4 and 1/2 of the
  information set). CA-SCL decodes are 25 % of MACs at 0.15 -4 dB (1.87 M of 7.32 M); failed main decodes are the target.
- How to test: a decode dump that records the list PMs at 2-3 intermediate points (the present dump has end-of-decode
  features only); fit the same logistic + threshold-moving offline at 0.15 -4 dB and 2/5 0.5 dB (skip <= 0.1 % of the
  decodes that end accepted); then an online flag.

### 5. Add a Forney / soft-output (blockwise probability) test to CRC + rho for analytic undetected-error control
- Sources: Yuan, Duffy, Medard, "Near-Optimal Generalized Decoding of Polar-like Codes", 2024
  ([arXiv 2402.05004](https://arxiv.org/html/2402.05004), full); Yuan, Duffy, Medard, "Soft-Output Successive Cancellation
  List Decoding", IEEE T-IT 2025 ([arXiv 2412.03623](https://arxiv.org/abs/2412.03623), abstract); Feng, Yuan, Duffy,
  Medard, "Improving the decoding performance of CA-polar codes", 2025 ([arXiv 2512.10223](https://arxiv.org/html/2512.10223v1), full).
- What they do: accept a decode only if P(c | y) / sum over the codebook >= 2^{NT}/(1+2^{NT}) (Forney); the codebook
  sum is approximated from the list plus an SC-based term for unvisited subtrees. The misdetection rate (UER / BLER) is
  then bounded by a chosen epsilon (shown for eps = 0.1 and 0.005, N = 64 ... 128); with CA-polar codes, candidates
  failing the CRC are removed and the unvisited term is scaled by 2^(M-K); simulated UER stays below the target line.
- Comparison with ours: the rho re-encoding check is a non-coherent re-score of the list output, the same idea as
  Coskun, Liva, Ostman, Durisi 2019 ([arXiv 1901.05409](https://arxiv.org/abs/1901.05409)); our finding that the raw path
  metric cannot replace rho (accepts 12 / 47 wrong CRC passes, 1046 / 1046 noise passes) is consistent with Giard 2017:
  the CA-SCL-8 ROC is *worse* than the SC ROC because list decoding makes non-codewords decodable. The raw PM is not
  normalised; the Forney ratio is.
- What to borrow: a list-normalised score P_list = 1 / (1 + sum_{l>0} exp(-(pm_l - pm_0))) (computable from the sorted
  list PMs already in the dump) and, if it separates, the full SO-SCL term. It would not replace rho, but it gives an
  epsilon-bounded misdetection rate per decode, which helps with the open item "noise-only false alarms at 1e6 scale"
  (RHO_N is calibrated empirically per rate).
- How to test: offline on the existing dumps (wrong CRC passes, noise-only 5600 frames): ROC of P_list alone and of
  (rho, P_list) jointly. Cheap; no new run needed if the dumps store all 8 list PMs.

---

## 2. Per-source table

| # | Title (authors), year | Link | Read | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|
| 1 | Polar-Coded Non-Coherent Communication (Yuan, Coskun, Kramer), 2021 | [2102.10719](https://ar5iv.arxiv.org/html/2102.10719) | full | **high**: same structure as our search, phase only | phase by max p(y \| theta, u_F = 0) via SCL(L_e) up to bit beta, coarse-fine search, then SCL-8 + CRC; pi ambiguity by flipping u_N | (128, 32) + CRC-6, QPSK, AWGN phase / block fading, no pilots, no CFO | within 0.3 dB of coherent, ~1.5 dB over 14-pilot PAT at FER 1e-4; beta = 47 worse than PAT; L_e = 1: FER 3.5e-4 at 1 dB |
| 2 | Phase-Equivariant Polar Coded Modulation (Geiselhart et al.), 2023 | [2305.01972](https://arxiv.org/html/2305.01972) | full | **high**: removes pi/2 hypotheses | rotation = automorphism + bit flip; 2 frozen rotation bits; V&V phase first; list paths start at different phases | K = 64 ... 192, N ~ 128 ... 256, QPSK / 16-QAM, SC, L = 8, phase only | +0.8 dB (QPSK), up to +2 dB (16-QAM) vs PAT; cost 2 bits |
| 3 | Blind Detection of Polar Codes (Giard, Balatsoukas-Stimming, Burg), 2017 | [1705.02111](https://ar5iv.arxiv.org/html/1705.02111) | full (ar5iv) | **high**: frozen-only detection metric | Fast-SSC metric from rate-0 / REP / SPC nodes, rate-1 ignored | (512, 80) incl. CRC-16, BPSK, AWGN | P_miss 1e-5 at P_fa 1e-3 (3 dB, SC); CA-SCL-8 ROC worse than SC |
| 4 | Accuracy vs Complexity in Blind Detection of Polar Codes (same group), 2018 | [1807.00655](https://ar5iv.arxiv.org/html/1807.00655) | full | **high**: partial-decode pruning of candidates | Fast-SSC metric after t nodes; 3 BP metrics; prune M = 44 to B for SCL | N = 256, K = 24 + CRC-16, BPSK, BLER 1e-2 point | 40 / 44 dismissed at MDR 1e-2 without SPC updates; SPC updates hurt at high BLER |
| 5 | Blind Detection with Polar Codes (Condo, Hashemi, Gross), 2017 | [1705.01864](https://ar5iv.arxiv.org/html/1705.01864) | full | medium: two-phase SC -> SCL candidate search (PDCCH) | 44 SC decodes ranked by PM, C2 best (plus low-PM ones) to SCL; RNTI in frozen bits; early stop when all paths mismatch RNTI | N = 128 ... 512, K = 8 ... 57, L = 2 ... 8 | FAR < 1e-3 (sequential RNTIs), ~1e-4 bound (random, 1e6 trials); 4 us budget met with 22 SC + C2 SCL decoders at 800 MHz |
| 6 | Design and Implementation of a Polar Codes Blind Detection Scheme (Condo et al.), 2018 | [1801.01820](https://arxiv.org/abs/1801.01820) | abstract | medium: hardware for #5 | two-phase + early stop; 65 nm | 5G PDCCH | "substantial" latency gain, no numbers in abstract |
| 7 | Code-Aided Turbo Synchronization (Herzet, Noels, Lottici, et al.), Proc. IEEE 2007 | [ResearchGate PDF](https://www.researchgate.net/profile/Nele-Noels/publication/2998277_Code-Aided_Turbo_Synchronization/links/09e415077d6120c438000000/Code-Aided-Turbo-Synchronization.pdf) | snippet only (403) | medium: classic baseline | EM / gradient / sum-product code-aided sync | turbo / LDPC, long frames | not read |
| 8 | Iterative Code-Aided ML Phase Estimation and Phase Ambiguity Resolution (Wymeersch, Moeneclaey), EURASIP JASP 2005 | [index page](https://portal.mardi4nfdi.de/wiki/Item:Q2570528) | abstract | medium: pilot-free ambiguity resolution | EM with MAP-decoder soft info; ambiguity resolved without pilots | turbo codes | lower MSE and BER loss than conventional; no numbers read |
| 9 | Code-aided CFOs and CPOs Estimation in Cooperative Satellite Communication (Yue et al.), 2023 | [2309.12828](https://arxiv.org/html/2309.12828) | full | medium: code-aided CFO with polar code, coarse search + EM | cross-entropy search over 6-bit quantised CFO (120 candidates, 24 elites, 4-8 iterations) + EM with soft symbols from BP LLRs | polar (1024, 512), BP, BPSK, \|f\| <= 7.8e-3, Es/N0 ~ -3 dB, 2-4 satellites | 0.3-0.4 dB BER loss at 1e-4; no complexity numbers |
| 10 | Low-Complexity Joint Channel Estimation and List Decoding of Short Codes (Coskun, Liva, Ostman, Durisi), 2019 | [1901.05409](https://arxiv.org/abs/1901.05409) | abstract | medium: list candidates re-scored by a non-coherent metric (= our rho idea) | few pilots for a first estimate, OSD list, final choice by non-coherent metric | short codes, QPSK, block fading | up to 1.2 dB over PAT |
| 11 | Near-Optimal Generalized Decoding of Polar-like Codes (Yuan, Duffy, Medard), 2024 | [2402.05004](https://arxiv.org/html/2402.05004) | full | **high** for acceptance | Forney threshold on list-approximated codebook probability | (64, 42) dRM vs 5G polar + CRC-6 / CRC-11, L = 4 / 8 | MDR <= eps (0.1, 0.005); beats CA-SCL in BLER and UER |
| 12 | Soft-Output SCL Decoding (Yuan, Duffy, Medard), IEEE T-IT 2025 | [2412.03623](https://arxiv.org/abs/2412.03623) | abstract | medium-high | codebook-probability estimate for SC-type decoders; blockwise / bitwise SO | dRM, 5G polar | qualitative only in abstract |
| 13 | Improving the decoding performance of CA-polar codes (Feng, Yuan, Duffy, Medard), 2025 | [2512.10223](https://arxiv.org/html/2512.10223v1) | full | medium | SO for CA-polar, erase when SO < 1 - eps; outer GRAND / GCD on CA-SCL failure | [64, 48, 24], [64, 43, 32] etc., L = 4 ... 16 | +0.2 dB (non-sys.), +0.2-1 dB (sys.); UER below target line |
| 14 | Soft-Output Fast SCL Decoder (Shen et al.), WCNC 2025 | [2410.15071](https://arxiv.org/abs/2410.15071) | abstract | low-medium | SO-SCL with Fast-SSC nodes | polar | "significant" latency cut, no numbers |
| 15 | Enhanced ML Techniques for Early HARQ Feedback Prediction in 5G (Strodthoff et al.), JSAC 2019 | [1807.10495](https://ar5iv.arxiv.org/html/1807.10495) | full | **high** for the retry gate | failure prediction from decoder reliability (VNR iters 0-5); LR, RF, isolation forest, SAE; threshold moving | LDPC BG2 rate 1/5, 360 bits, QPSK, TDL-C, 3-4 dB | AUC-PR 0.902 (threshold) vs 0.905 (LR) vs 0.908 (SAE) at 4 dB, 5/6 subcode |
| 16 | Early-termination techniques for polar list decoders (Sarkis et al., Qualcomm), US 10615825 B2, 2020 | [Google Patents](https://patents.google.com/patent/US10615825B2/en) | description (first 100k chars) | medium-high | stop SCL when normalised PM spread < threshold after a minimum number of bits; PDCCH blind decoding | 5G control | example spread 1.75 vs threshold 2.0; no BLER numbers |
| 17 | Low-Complexity PSCL Decoding of Polar Codes (Yao, Ma), 2024 | [2405.13255](https://arxiv.org/abs/2405.13255) | abstract | low-medium | double threshold: path reliability + P(correct path in list) | polar, CRC-polar, PAC | savings grow with SNR; no numbers in abstract |
| 18 | On List Decoding of 5G-NR Polar Codes (Pillet, Bioglio, Condo), WCNC 2020 | [1907.00784](https://arxiv.org/abs/1907.00784) | abstract | low: distributed CRC early stop | path pruning and early termination with distributed CRC | 5G DCI | trade-off curves only |
| 19 | Design, Performance, and Complexity of CRC-Aided List Decoding ... Short Messages (King, Yao, Ryan, Wesel), 2023 | [2302.07513](https://ar5iv.labs.arxiv.org/html/2302.07513) | full | medium: UER vs list size / CRC length | CRC-polar and CRC-TBCC list decoding | (512, 43), CRC-11 / CRC-24, L up to 1024 | CRC-24: 0 undetected errors up to L = 1024; CRC-11: > 80 % of failures undetected at high SNR; L ~ 2^m conjecture |
| 20 | LLR-Based SCL Decoding of Polar Codes (Balatsoukas-Stimming, Bastani Parizi, Burg), IEEE TSP 2015 | [1401.3753](https://ar5iv.arxiv.org/html/1401.3753) | full | medium: our PM formula and a cycle model | LLR-domain PM; hardware SCL | N = 1024, R = 1/2, 90 nm | latency 2N + (N/P)log2(N/4P) + K cycles (2592 for N = 1024, K = 512, P = 64), independent of L; L = 8: 637 MHz, 246 Mb/s, 3.6-3.9 mm^2 |
| 21 | Fast and Flexible SCL Decoders (Hashemi, Condo, Gross), 2017 | [1703.08208](https://arxiv.org/abs/1703.08208) | abstract | low-medium | Fast-SSCL, Fast-SSCL-SPC | polar | 1.86 Gb/s |
| 22 | LLR-based SCL with Multi-bit Decision (Yuan, Parhi), 2016 | [1603.07055](https://arxiv.org/pdf/1603.07055) | snippet | low-medium: fixed point | quantisation study | N = 1024, R = 1/2 | 6-bit LLRs sufficient; PMs need more bits; 7-bit sorting ~ no loss |
| 23 | Interpolation Techniques for FFT-Based Carrier Synchronization, DVB-RCS2 (Griebel, Wasenmuller, Wehn), Adv. Radio Sci. 2021 | [ars-19-59-2021](https://ars.copernicus.org/articles/19/59/2021/) | full | medium: deployment of NDA FFT CFO | DA / NDA Rife-Boorstyn FFT + parabolic / energy interpolation | 40 DVB-RCS2 burst types (~536-1616 symbols), CFO up to 1.5 % (tolerance 0.5-3 %) of Rs | interpolation cuts FFT 8192 -> 2048 with no FER loss; throughput x2-4 for < 20 % more FPGA resources |
| 24 | Feedforward frequency estimation for PSK: a tutorial review (Morelli, Mengali), ETT 1998 | [index](https://www.bohrium.com/paper-details/feedforward-frequency-estimation-for-psk-a-tutorial-review/811904108263899138-14477) | abstract | medium: classic NDA baseline | DA vs NDA (M-th power) feedforward estimators | PSK | NDA non-linearity raises the threshold; R&B best at low SNR |
| 25 | Learning While Transmitting: Pilotless Polar Coded Modulation (2026) | [2602.17979](https://arxiv.org/html/2602.17979) | abstract + snippet | medium: pilot-free polar, implicit pilots | QPSK segment decoded first (frozen bits + rotation invariance) gives CSI for a QAM segment | block fading, short packets | up to 1.5 dB over PAT; notes phase-equivariant designs break under rate matching |
| 26 | Hybrid Polar Encoding with Applications in Non-Coherent Channels, 2023 | [2308.08201](https://arxiv.org/pdf/2308.08201) | snippet | low | joint estimation + decoding, L = 16, CRC-16 | block fading | approaches perfect-CSI at high SNR |
| 27 | Deep Learning-Based Frequency Offset Estimation (Chen et al.), 2023 | [2311.16155](https://ar5iv.labs.arxiv.org/html/2311.16155) | full | low: NN CFO regressor | IQ-ResNet regression | BPSK / FSK / QAM, 512-2048 samples, \|f\| <= 0.2, -20 ... 30 dB | beats Kay; no CRB, no complexity numbers |
| 28 | LR-FHSS Transceiver for Direct-to-Satellite IoT (Jung et al.), 2024 | [2403.14154](https://arxiv.org/abs/2403.14154) | abstract (+ snippet) | low-medium: deployed candidate-Doppler search | Doppler-robust sync; candidate Doppler values tested, tracking in header decoding (snippet) | LEO IoT, ASIC + FPGA | no numbers in abstract |
| 29 | Doppler Shift Estimation in 5G NR NTN (Lin et al., Ericsson), Globecom 2021 | [2108.07757](https://arxiv.org/abs/2108.07757) | abstract | low: NTN relies on GNSS / reference signals | Doppler from reference signals at several frequencies, UL pre-compensation | 5G NR NTN | no numbers in abstract |
| 30 | Almost Optimal Exploration in Multi-Armed Bandits (Karnin, Koren, Somekh), ICML 2013 | [PDF](https://labs.yahoo.com/mobstor/publication_attachments/Almost%20Optimal%20Exploration%20in%20Multi-Armed%20Bandits.pdf) | snippet (via citing papers) | low-medium: theory for our checkpoints | sequential halving, fixed-budget best-arm identification | generic | near-optimal for equal variances (per [2306.07549](https://arxiv.org/pdf/2306.07549)) |

Not found or not readable: an open full text of Herzet et al. 2007; any paper on SC/SCL-metric search over a *frequency*
grid; 3GPP TS 38.212 / 38.213 tables (PDCCH blind-decode limits) - only patent snippets, so no numbers are quoted here;
a peer-reviewed in-decode early-termination paper with false-alarm numbers (only the Qualcomm patent was read).

---

## 3. State of the art per receiver component

| Component | Our version | Literature state of the art | Verdict |
|---|---|---|---|
| Coarse CFO | 4th-power FFT (R&B on r^4), lag-4 autocorrelation, peak picking, parabolic / Newton refinement (fast path) | NDA R&B FFT + interpolation is the deployed baseline (DVB-RCS2, #23); the NDA threshold is fundamental (#24); NN regressors (#27) are not shown to beat it at low SNR | **we already use it**. Nothing to switch to |
| Fine CFO / phase | refinement offsets + full list-1 metric; DD Newton on the hard SC codeword (CA retry); DD final estimate | code-aided EM with soft symbol expectations from decoder LLRs (#7, #8, #9) | **slightly behind** (hard vs soft symbols), but `s3_dd` gave no gain and the main failure is the search, not the fine stage. Soft EM would need soft output (SO-SCL, #12). Low priority |
| Phase ambiguity | PiCode (two CRC patterns) for pi; pi/2 branch by extra phase hypotheses | phase-equivariant code (#2); outer code with d_min >= 2 + last-bit flip (#1); code-aided ML ambiguity resolution (#8) | **behind** for pi/2: finding 2 |
| Hypothesis search | CFO grid x phases, partial list-1 Fast-SSC metric, robust z-test checkpoints, prior-ordered batches, checkpoint NN (2/5, 1/2) | same two-phase structure in PDCCH blind detection (#4, #5) and in non-coherent polar (#1); detection metric that ignores rate-1 / SPC (#3, #4); list-marginalised metric L_e = 8 (#1); checkpoints = successive halving (#30) | structure: **we already use it** (and go further: CFO grid, robust z, 32-core batches). Metric: **behind** on two points (findings 1, 3) |
| Joint list decoding over hypotheses | 16-path list over 8 hypotheses with global pruning (2/5, 1/2) | list paths started on different phase hypotheses (#2) | **we already use it** |
| Acceptance / false alarms | CRC-16 (PiCode) + rho re-encoding check with per-rate RHO_N | non-coherent re-scoring of list output (#10); Forney / SO-SCL thresholds with bounded misdetection (#11-#13); PDCCH: RNTI in frozen bits / CRC-24, FAR target < 1e-4 checked over 1e6 trials (#5) | rho: **we already use it**. Forney / SO bound: **behind** (finding 5). Noise-only FAR: ours is 0 / 9600 so far; the PDCCH practice is 1e6 trials, already our open item 4 |
| Complexity reduction | Fast-SSC nodes, checkpoints + early win, fast path, prior ordering, retry gate (offline) | Fast-SSCL (#21); PM-spread in-decode early termination (#16); double-threshold pruning (#17); distributed CRC early stop (#18) | **mostly in use**; in-decode abort **behind** (finding 4); distributed CRC **not applicable** without changing the code / CRC placement (possible, but a code change like finding 2) |
| ML gates | logistic retry gate on 13 failed-decode features; checkpoint NN; logistic = MLP | LR / RF / SAE for failure prediction, LR as good as the complex models (#15) | **we already use it**; consistent with the literature |
| Cost model | MACs per core (crit_par on 32 cores) | hardware SCL latency 2N + (N/P)log2(N/4P) + K cycles, independent of L when the L SC units run in parallel (#20) | **not the same quantity**: see 4.4 |

---

## 4. Answers to the focus questions

### 4.1 Search ranking (main error mode at 0.15 -4 dB)
- Published blind / non-coherent polar receivers use the same idea: frozen bits as implicit pilots, a partial SC/SCL
  metric to score hypotheses, coarse-to-fine, then SCL on the best few (#1, #4, #5, #25). None searches a CFO grid of
  201-401 cells; the largest candidate sets are the 44 PDCCH candidates (#4, #5) and 120 cross-entropy samples (#9).
- What differs from ours, and might help the 117 / 199 "true region missed" cases:
  1. the detection metric ignores rate-1 nodes and treats SPC updates as harmful at high BLER (#3, #4) -> finding 1;
  2. the phase estimator marginalises over information bits with L_e = 8 and runs to 88 % of the code (#1) -> finding 3;
  3. the pi/2 hypotheses can be removed by the code design (#2) -> finding 2; at the same MACs the freed budget could
     go into denser CFO cells or lower tau at the low-SNR points.
- Successive halving theory (#30) supports our checkpoint scheme for equal variances. Our robust median / MAD z already
  normalises per packet. The variance-aware variants in [2306.07549](https://arxiv.org/pdf/2306.07549) are a hint that
  cells near the true CFO (partially coherent, higher metric variance) deserve a looser cut; the "neighbours join"
  rule at R = 1/10 already does something similar. No concrete method to borrow beyond findings 1-3.
- Cross-entropy search (#9) replaces the grid with adaptive sampling. It needs several full scoring rounds and gave
  4 dB SNR loss with 5-bit quantisation in their setting, so it is not a clear win for a 32-core MAC budget. Not
  recommended.

### 4.2 Retry gating / stopping rules
- Known: failure prediction from decoder reliability features with logistic regression (#15); PM-spread early
  termination for polar list decoders in PDCCH blind decoding (#16); SNR-dependent PM thresholds (#17); distributed CRC
  early stop (#18); RNTI-in-frozen-bits early stop (#5). Our gate's features (pm_gap, pm_spread, syndrome agreement,
  LLR magnitudes) are the same kind as #15 and #16.
- New for us: acting *during* the main decode (finding 4) and using a normalised probability (P_list or SO-SCL) as a
  feature (finding 5).
- The literature found no gain from complex models over LR (#15), which matches our logistic = MLP.

### 4.3 False-alarm / undetected-error control
- Two published lines: (a) re-score list candidates with a non-coherent or re-encoding metric (#10); this is our rho;
  (b) Forney-style thresholds on a normalised likelihood, with SO-SCL giving a bounded misdetection rate (#11-#13).
- Raw path-metric detection gets worse under list decoding (#3: CA-SCL-8 ROC worse than SC), which agrees with our
  measurement (PM accepts 1046 / 1046 noise passes).
- CRC length: with CRC-24, 0 undetected errors were seen up to L = 1024; with CRC-11, more than 80 % of failures were
  undetected at high SNR (#19). The CRC budget seen by our search is much more than 1 decode: about (number of CA-SCL
  decodes per packet) x 8 paths x 2 PiCode patterns x 2^-16. That is why rho is needed, and why a 1e6-trial noise-only
  test (PDCCH practice, #5) is the right next check.

### 4.4 Deployment and practical concerns
- **5G NR PDCCH** (polar, short DCI): two-phase blind detection of about 44 candidates in a 4-16 us budget, FAR target
  < 1e-4 (#5, #6). This is the closest deployed analogue of our Stage 2 -> Stage 3, but it searches over candidate
  positions / RNTIs, not CFO (CFO is removed by SSB-based sync).
- **DVB-RCS2 return link**: bursts of ~536-1616 symbols, CFO up to 0.5-3 % of the symbol rate (ours: 3 %), NDA / DA R&B
  FFT with interpolation on FPGAs; known symbols (preamble / pilots) are still present (#23). Our blind receiver
  removes them; the 128-pilot NN is the DVB-RCS2-like reference.
- **LEO IoT / NTN**: deployed systems test several Doppler candidates in the header (LR-FHSS, #28) or pre-compensate
  with GNSS / reference signals (#29). Neither is pilot-free in our sense.
- **Latency**: with the cycle model of #20 (P = 64 processing elements per SC core), one SCL decode of N = 2048 takes
  about 2·2048 + 32·3 + K cycles = 4515 cycles at R = 0.15 (K = 323) and 5232 at R = 1/2 (K = 1040), about 7-8 us at
  the 637 MHz of their 90 nm L = 8 design (my calculation from their formula; their design is for N = 1024). The cycle
  count does not grow with L, because the L SC units run in parallel, while our MAC model charges L times the work.
  So "MACs per core" and hardware latency rank designs differently: list decodes look relatively cheaper in cycles,
  metric passes relatively dearer. Worth stating in `07_complexity.md`. Fast-SSC node scheduling (#21) reduces the
  cycle count further.
- **Fixed point**: 6-bit LLRs are typical; path metrics need more bits (#22, #20). Our z-test uses median and MAD of
  *wrong-cell* metrics, which grow by about (N - K) ln 2 ~ 1200 nats. A saturating PM register would compress exactly
  those values and change z. This should be tested before any hardware claim (open item 4).
- **Phase noise and timing**: none of the polar papers read models phase noise or timing error. The cell width rests
  on a 0.48 rad edge drift (04, 4.1); phase noise adds a random walk on top. Timing / burst detection without a
  preamble is the PDCCH / Giard detection problem (#3), which our noise-only test only partly covers. Still open.

---

## 5. Sources
- https://ar5iv.arxiv.org/html/2102.10719
- https://arxiv.org/html/2305.01972
- https://ar5iv.arxiv.org/html/1705.02111
- https://ar5iv.arxiv.org/html/1807.00655
- https://ar5iv.arxiv.org/html/1705.01864
- https://arxiv.org/abs/1801.01820
- https://www.researchgate.net/profile/Nele-Noels/publication/2998277_Code-Aided_Turbo_Synchronization/links/09e415077d6120c438000000/Code-Aided-Turbo-Synchronization.pdf
- https://portal.mardi4nfdi.de/wiki/Item:Q2570528
- https://arxiv.org/html/2309.12828
- https://arxiv.org/abs/1901.05409
- https://arxiv.org/html/2402.05004
- https://arxiv.org/abs/2412.03623
- https://arxiv.org/html/2512.10223v1
- https://arxiv.org/abs/2410.15071
- https://ar5iv.arxiv.org/html/1807.10495
- https://patents.google.com/patent/US10615825B2/en
- https://arxiv.org/abs/2405.13255
- https://arxiv.org/abs/1907.00784
- https://ar5iv.labs.arxiv.org/html/2302.07513
- https://ar5iv.arxiv.org/html/1401.3753
- https://arxiv.org/abs/1703.08208
- https://arxiv.org/pdf/1603.07055
- https://ars.copernicus.org/articles/19/59/2021/
- https://www.bohrium.com/paper-details/feedforward-frequency-estimation-for-psk-a-tutorial-review/811904108263899138-14477
- https://arxiv.org/html/2602.17979
- https://arxiv.org/pdf/2308.08201
- https://ar5iv.labs.arxiv.org/html/2311.16155
- https://arxiv.org/abs/2403.14154
- https://arxiv.org/abs/2108.07757
- https://labs.yahoo.com/mobstor/publication_attachments/Almost%20Optimal%20Exploration%20in%20Multi-Armed%20Bandits.pdf
- https://arxiv.org/pdf/2306.07549
