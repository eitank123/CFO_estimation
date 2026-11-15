# Literature survey 3: academic state of the art for CFO estimation in SINGLE-CARRIER PSK bursts (2026-11-15)

Scope (main session, refocused by the user: "SC" = single-carrier): CFO estimators for single-carrier PSK burst /
short-packet receivers, 2015-2026, plus the classic baselines they build on: data-aided (DA) and non-data-aided (NDA)
feedforward estimators, code-aided (EM / turbo / LDPC / polar), deep-learning estimators, and short-packet pilot
designs vs blind designs; low SNR (Es/N0 -5 ... +3 dB) and large CFO (~0.03 cycles/symbol). OFDM skipped.

Read before searching and NOT repeated: `lit_blind_cfo.md` (survey 1: Yuan-Coskun-Kramer 2021, Geiselhart 2023, Giard,
Condo, Yue 2023, Chen 2023, Griebel 2021, Morelli-Mengali 1998, ...), `lit_polar_sync.md` (survey 2: Choi-Lee 2026,
Colavolpe 2005, CN110519200B, Wu 2025, ...), `lit_dvbrcs2.md` (DVB-RCS2, ESA patent, Barbieri-Colavolpe 2007 T-BC,
Ying-Ghogho 2005). Those sources are cited here only where a new comparison is made. One reference entry per source
cited is in the last section ("Reference entries").

Our system for comparison: 1024 QPSK symbols, polar N = 2048 + CRC-16, R = 1/10, 0.15, 2/5, 1/2, Es/N0 -5 ... +3 dB,
CFO uniform |f| <= 0.03 cycles/symbol, no pilots; grid over CFO x phase scored by the list-1 Fast-SSC metric with
checkpoints, CA-SCL-8 + CRC + re-encoding check. Measured (08, 8.2a; 07, 7.5b): with pilot energy charged blind is the
best receiver at 1/10 (BLER 1e-4 at -4.9 dB vs -4.68 dB for 128-preamble ML), ties at 0.15, is ~0.5 dB better at 2/5 and
1/2, at 2-12x the MACs per core. Final CFO RMSE of accepted packets (testing/README.md, R1 dd): 4.9e-5 ... 7.1e-5
cycles/symbol at 1/10 -5 dB, 5.2e-5 ... 5.9e-5 at 0.15 -4 dB, 3.9e-5 ... 4.3e-5 at 2/5 0.5 dB.

Reading depth: "full" = full text (often via the r.jina.ai text reader, tables / figures may be lost); "abstract";
"snippet" = search-result text only. **[derived]** = my arithmetic. No simulations were run.

**Main comparability caveat.** The search again found NO single-carrier paper with BLER / FER results for a blind CFO
search over |f| <= 0.03 at Es/N0 <= -3 dB. The only blind code-aided CFO search over a range as wide as ours (wider:
+-0.1) is Imad, Houcke, Ghogho 2010 (LDPC (512, 256), BPSK, MSE only, Es/N0 >= about -0.5 dB [derived]). The classic
code-aided turbo synchronizer study with our burst size (Noels, Steendam, Moeneclaey 2005: 1001 QPSK symbols, |fT| <=
0.1) needs a 128-symbol preamble and works above ~2 dB Es/N0. Deep-learning CFO estimators report RMSE / MAE only, at
>= 0 dB, with no BLER and usually no CRB. Nothing found beats our receiver at a comparable point; nothing found is at a
comparable point.

---

## 1. Ranked takeaways

### T1. Our operating region is outside the published one; say so, with the two closest anchors
- Blind, wide range: Imad et al. 2010 ([EURASIP JASP 2010:293572](https://link.springer.com/article/10.1155/2010/293572),
  full via text reader): syndrome-LLR cost over CFO, exhaustive search or simulated annealing, |f| <= 0.1 cycles/symbol,
  LDPC (512, 256), BPSK. MSE ~5e-8 at Eb/N0 2.5 dB (RMSE ~2.2e-4 cycles/symbol [derived], Es/N0 ~ -0.5 dB [derived]);
  NLLS (an NDA estimator) is BETTER than it for BPSK; it wins only for 16-QAM. No BER / FER for the CFO part, no CRB.
  [derived] MCRB for 512 BPSK symbols at -0.5 dB is ~3.6e-5, so their RMSE is ~6x the MCRB. Ours is 2.3-3.8x the MCRB
  of 1024 symbols (T2) at Es/N0 4.5 dB lower, and delivers BLER.
- Pilot + code-aided, same burst size: Noels et al. 2005 ([EURASIP JASP 2005:6, 972](https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972),
  full via text reader): rate-1/2 turbo, 1001 QPSK symbols, |fT| <= 0.1. The coded CRB equals the MCRB at the
  operating SNR. A code-aided soft-decision-directed (SDD) synchronizer reaches it only with a good start: DA preamble
  512 symbols (34 % overhead) -> at the CRB; 256 -> "degrades seriously" for DA-SDD, DA-NDA-SDD at the CRB above 1.5 dB;
  128 (11 %) -> DA-NDA-SDD at the CRB above ~2 dB. Code-unaware NDA has a threshold at ~3.5 dB Es/N0.
- Meaning: the literature's code-aided synchronizers need pilots for pull-in and >= ~2 dB; ours acquires +-0.03 with
  no pilots down to -5 dB Es/N0 at the cost of a full-range hypothesis search. This is the claim to make, with these two
  papers as the nearest published points.

### T2. Fine CFO: we are 2.3-3.8x the MCRB in RMSE, but the BLER headroom from closing that is <= ~0.04 dB [derived]
- MCRB (1024 symbols, var = 3 / (2 pi^2 rho N^3) cycles^2/symbol^2) [derived]: RMSE 2.1e-5 at -5 dB, 1.9e-5 at -4 dB,
  1.8e-5 at -3.5 dB, 1.1e-5 at 0.5 dB, 9.4e-6 at 2 dB. Noels 2005: the coded CRB ~ MCRB, reachable by code-aided SDD.
- Ours: 4.9e-5 ... 7.1e-5 (1/10 -5 dB), 3.9e-5 ... 4.3e-5 (2/5 0.5 dB) -> 2.3-3.4x and 3.5-3.8x the MCRB.
- Effect on BLER [derived]: a 5e-5 residual gives at most 2 pi x 5e-5 x 512 = 0.16 rad at the packet edges, RMS 0.093 rad
  over the packet, a coherent loss of ~0.04 dB; at the MCRB level ~0.006 dB. So EM / SDD fine estimation (the
  "state of the art" for fine CFO) is worth <= ~0.04 dB to us. This agrees with the dead end `dd` (no packet fixed).
- Verdict: fine CFO = **we are behind in RMSE, not in BLER**; do not invest; plot RMSE vs the MCRB line in the
  presentation so the gap is shown honestly.

### T3. Acquisition: the literature's remedies for the NDA threshold are pilots (DA-NDA) or code-aided candidate selection; ours is the latter at full range
- DA-NDA combination (Noels 2005): NDA search restricted to the neighbourhood of a DA peak; softens the threshold.
- Code-aided candidate selection: Barbieri-Colavolpe 2007 T-BC (3-7 frequency candidates chosen by the LDPC syndrome,
  in `lit_dvbrcs2.md`); Barbieri, Colavolpe, Caire 2007 T-COM ([j31.pdf](https://www.tlc.unipr.it/colavolpe/papers/j31.pdf),
  full via text reader: 11 quantised frequency levels in the first iteration, 3 after, inside the sum-product
  factor graph; pilots every 20 symbols bootstrap it, so the range is |f| < 1/40 = 0.025 [derived]; no measurable BER
  loss vs known frequency offset with the forward-backward schedule; long LDPC codes 4000 and 64800 bits);
  Wang, Jiang, Kuang, Guo 2020 GP-MASO-MLE ([PolyU record](https://research.polyu.edu.hk/en/publications/iterative-doppler-frequency-offset-estimation-in-low-snr-satellit/),
  abstract; [IEEE 9148098](https://ieeexplore.ieee.org/document/9148098/)): NDA, short bursts, Gaussian-process
  (Bayesian-optimisation) search of a decoder-based objective for coarse CFO, then MLE with turbo iterations; within
  0.1 dB of ideal-correction BER; RMSE near the MCRB for Eb/N0 >= 2 dB (as cited by Diniz 2024); range and code not read.
- Ours = code-aided candidate selection over the full range with a parallel grid and early-stop checkpoints: **we
  already use it**, and at a lower SNR than any of these. GP / Bayesian-optimisation search samples sequentially, which
  works against our per-core critical path on 32 cores; the cross-entropy variant (Yue 2023, survey 1) was already
  judged not worth it. **Not recommended.**

### T4. Deep-learning CFO estimators are not ahead at our block length and SNR
- O'Shea, Karra, Clancy 2017 ([ar5iv 1707.06260](https://ar5iv.labs.arxiv.org/html/1707.06260), full): CNN regressor,
  QPSK, RRC 0.25, 4 samples/symbol, CFO up to +-0.5 cycles/symbol, SNR 0 / 5 / 10 dB, baseline 4th-power periodogram.
  The 4th-power baseline wins in AWGN for blocks > 1024 samples at >= 5 dB; the CNN wins for short blocks and under
  fading. Cost: CNN 23.7 MFLOP at 1024 samples vs 5.4 MFLOP for the FFT baseline (4.4x). No CRB, no BER.
- Chen et al. 2023 (survey 1 #27): ResNet, beats Kay, no CRB, no complexity. Jung et al. 2026 SAFE
  ([2609.07034](https://arxiv.org/abs/2609.07034), abstract): multi-tone sinusoid estimation, -10 ... 0 dB, no CRB.
- No DL paper found reports BLER after decoding for single-carrier CFO, or works at -5 dB with a 1024-symbol burst.
  Our own CNN estimator (07: ~9 M MACs) is already the DL competitor. Verdict: **we already use it**; nothing to switch to.

### T5. Short-packet theory and pilot-free designs: supporting context, no competitor to build
- Kislal, Rajiv, Durisi, Strom, Mitra 2024 ([2401.09089](https://arxiv.org/abs/2401.09089), abstract): finite-blocklength
  RCUs bound with pilot-based joint synchronisation (delay) and channel estimation; with independent delays per block
  "synchronization becomes the bottleneck". Supports adding timing uncertainty to our open items; no CFO numbers read.
- Walk, Jung, Hassibi, Jafarkhani 2019 MOCZ ([1902.02928](https://arxiv.org/abs/1902.02928), abstract): pilot-free
  short packets where CFO is a common rotation of zeros, resolved by a cyclically permutable code; a different
  modulation, no numbers read. Not applicable to QPSK + polar.
- Bodet, Medard, Rangaswamy, Duffy 2026 ([2605.00761](https://arxiv.org/abs/2605.00761), abstract): decoded codewords as
  pilots, non-iterative; the same idea as our `pns` code-aided phase tracking. **We already use it.**
- Sy, Knopp 2024 ([2404.09943](https://arxiv.org/abs/2404.09943), abstract): joint estimation-detection BICM metrics with
  low-density DMRS, polar / LDPC in a 5G (OFDM) chain; not single-carrier CFO.

---

## 2. Per-source table (new sources of this survey)

| # | Source | Link | Read | Relevance | Method | Code, N | CFO range (cycles/symbol) | SNR (Es/N0) | Pilots | Numbers | Comparability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Noels, Steendam, Moeneclaey, "Carrier and clock recovery in (turbo-)coded systems: CRB and synchronizer performance", EURASIP JASP 2005 | [springeropen](https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972) | full (reader) | **high**: same burst size, code-aided bound | coded CRB via BCJR marginals; DA, NDA, DA-SDD, DA-NDA-SDD (EM) synchronizers | turbo R = 1/2, 1001 QPSK symbols | <= 0.1 | about -1 ... 3 dB | DA preamble 128 / 256 / 512 | coded CRB ~ MCRB at operating SNR; DA-NDA-SDD at CRB above ~2 dB (128 pilots), ~1.5 dB (256); NDA threshold ~3.5 dB | 2-7 dB above our SNRs; pilots needed |
| 2 | Imad, Houcke, Ghogho, "Blind estimation of the phase and carrier frequency offsets for LDPC-coded systems", EURASIP JASP 2010 | [springer](https://link.springer.com/article/10.1155/2010/293572) | full (reader) | **high**: the only blind code-aided CFO search as wide as ours | minimise syndrome-LLR cost over CFO: exhaustive or simulated annealing; optional interval f_est +- 3 sigma from a classical estimator | LDPC (512, 256), d_c = 4; BPSK (16-QAM for comparison) | <= 0.1 | Eb/N0 ~2.5-3 dB = Es/N0 ~ -0.5 ... 0 dB [derived] | none | MSE ~5e-8 (exhaustive, 2.5 dB), ~7e-8 (narrowed + 700 SA iterations, 3 dB); NLLS better for BPSK; cost O(n_r d_c n_iter); no BER for CFO | BPSK, LDPC, MSE only, no BLER |
| 3 | Barbieri, Colavolpe, Caire, "Joint iterative detection and decoding in the presence of phase noise and frequency offset", IEEE T-COM 2007 | [j31.pdf](https://www.tlc.unipr.it/colavolpe/papers/j31.pdf) | full (reader; numbers in figures lost) | medium-high: quantised-frequency hypotheses inside the decoder | sum-product over code + phase + quantised FO (11 levels, then 3) | (3,6) LDPC 4000; DVB-S2 64800 | set by pilot spacing: < 0.025 for P = 20 [derived] | not legible (3.9 dB Eb/N0 in one test) | 1 per 20 (QPSK, 8PSK), 1 per 40 (32APSK) | no measurable loss vs Tikhonov with known FO; mixed schedule ~0.3 dB | long codes, pilots, iterative BP |
| 4 | Wang, Jiang, Kuang, Guo, "Iterative Doppler frequency offset estimation in low SNR satellite communications", IWCMC 2020 | [PolyU](https://research.polyu.edu.hk/en/publications/iterative-doppler-frequency-offset-estimation-in-low-snr-satellit/), [IEEE](https://ieeexplore.ieee.org/document/9148098/) | abstract (+ citation in #6) | medium: NDA code-aided search for short bursts | GP (Bayesian) search of a decoder objective + MLE with turbo iterations | turbo; length not read | not read | not read; RMSE ~MCRB for Eb/N0 >= 2 dB (per #6) | none | within 0.1 dB of ideal-correction BER; "lower complexity than multi-step search" (no number) | settings unknown |
| 5 | O'Shea, Karra, Clancy, "Learning approximate neural estimators for wireless channel state information", 2017 | [ar5iv 1707.06260](https://ar5iv.labs.arxiv.org/html/1707.06260) | full | medium: the single-carrier DL-vs-4th-power reference | 1-D CNN regressor vs 4th-power periodogram | uncoded QPSK, RRC 0.25, 4 sps, 32 ... 1e5 samples | <= 0.5 | 0, 5, 10 dB (per sample, definition not read) | none (CFO task) | CNN better below ~1024 samples; FFT better above at >= 5 dB (AWGN); CNN 23.7 vs 5.4 MFLOP at 1024 samples | uncoded, no BLER, >= 0 dB |
| 6 | Diniz, Eriksson, Gustavsson, "Doppler shift estimation for satellite communications using linear estimators", SPAWC 2024 | [Chalmers PDF](https://research.chalmers.se/publication/543507/file/543507_Fulltext.pdf) | full (reader) | low-medium: modern DA tone estimator | multi-step linearised LS (Taylor) after phase from N1 pilots | 500-sample all-ones pilot, no code | ~0.0044 cycles/sample [derived from 0.0275 rad/sample] | -10 ... 15 dB | 500 known | near CRLB to about -6 dB; Tretter fails at ~10 dB | pure pilot tone, not a data burst |
| 7 | Rodrigues, Dias, Fraidenraich, de Lima, "Study of a pilotless fine frequency estimator in burst-mode PSK", SBrT 2019 | [SBrT PDF](https://biblioteca.sbrt.org.br/articlefile/2063.pdf) | full (reader) | low | L&R / Jiang-type fine estimator with complex accumulation, vector projection | DVB-S2, 21690-symbol window | residual after coarse 4e-3 | down to -2 dB (residual below target); "close to MCRB down to 0 dB" | header only | Kay, Tretter fail below ~9 dB | long frames, fine stage only |
| 8 | Kislal, Rajiv, Durisi, Strom, Mitra, "Is synchronization a bottleneck for pilot-assisted URLLC links?", IEEE TWC 2024 | [2401.09089](https://arxiv.org/abs/2401.09089) | abstract | low-medium: short-packet sync theory | RCUs + saddlepoint with joint delay / channel estimation from pilots | Gaussian codebooks, block fading | delay, not CFO | not read | pilots | qualitative: sync is the bottleneck when delays are independent | no CFO |
| 9 | Walk, Jung, Hassibi, Jafarkhani, "MOCZ for blind short-packet communication: some practical aspects", 2019 | [1902.02928](https://arxiv.org/abs/1902.02928) | abstract | low | zero-modulation; CFO = rotation of zeros, CPC resolves integer rotations | MOCZ + cyclic code | not read | not read | none | none in abstract | different modulation |
| 10 | Bodet, Medard, Rangaswamy, Duffy, "The benefit of decoder-provided pilots in highly dynamic channels", 2026 | [2605.00761](https://arxiv.org/abs/2605.00761) | abstract | low-medium: same idea as `pns` | decoded codewords as non-iterative pilots | code-agnostic | fast fading, no CFO | not read | decoded data | qualitative only | fading, no CFO |
| 11 | Sy, Knopp, "Novel joint estimation and decoding metrics for short-blocklength transmission systems", 2024 | [2404.09943](https://arxiv.org/abs/2404.09943) | abstract | low | joint estimation-detection BICM metrics, low-density DMRS | polar, LDPC, 5G chain | none | not read | DMRS | "close to coherent" with ~4-symbol windows | OFDM / 5G |
| 12 | Serbes, "Fast and efficient sinusoidal frequency estimation by using the DFT coefficients", IEEE T-COM 2019 | [record](https://www.bohrium.com/paper-details/fast-and-efficient-sinusoidal-frequency-estimation-by-using-the-dft-coefficients/812821168208740353-105711) | snippet | low-medium: modern DFT interpolation | iterative interpolation on shifted DFT coefficients | single tone | any (FFT) | not read | DA (tone) | not read | could replace parabolic interpolation in pilot receivers; tiny gain expected |
| 13 | Jung, Paek, Jung, Kong, "SAFE: SNR-adaptive frequency estimator", 2026 | [2609.07034](https://arxiv.org/abs/2609.07034) | abstract | low | NN time-frequency enhancement + SNR-based estimator selection | multi-tone, no code | not read | -10 ... 0 dB | n/a | FNR 13.0 %, NN-RMSE -56.7 % vs prior | radar-style multi-tone |
| 14 | Vieira, Serra, Colares, Mello, "Spectral segmented linear regression for coarse CFO estimation in optical LEO", Opt. Express 2026 | [2603.28262](https://arxiv.org/abs/2603.28262) | abstract | low | NDA coarse CFO by segmented regression on the spectrum | optical coherent | up to ~+-0.5 (per snippet) | "low SNR" | none | none in abstract | optical, continuous |
| 15 | Baldi et al., "State-of-the-art space mission telecommand receivers", IEEE AES Mag. 2017 | [polito PDF](https://iris.polito.it/bitstream/11583/2651421/3/29017%20j1%20nexcode%20journal_x.pdf) | full (reader, OCR noise) | low | PLL + FFT-aided acquisition, LDPC (128,64), (512,256) | CCSDS TC | Hz only | Es/N0 for CER 1e-5: (128,64) 0.55 dB (hybrid) ... 2.4 dB; (512,256) 0.43 ... 1.85 dB | acquisition sequence | no sync loss numbers | loop-based, long acquisition |
| 16 | Vila-Valls, Navarro, Closas, Bertinelli, "Synchronization challenges in deep space communications", ~2018 | [zenodo PDF](https://zenodo.org/records/3471450/files/Synchronization%20Challenges%20in%20Deep%20Space.pdf) | full (reader) | low | FFT acquisition, Kalman PLL, NC-DTTL | uncoded sims; LDPC (128,64) targeted | Hz only | target 2 dB | 128-bit acquisition | 8192-pt FFT x10 blocks: 0 / 50 misacquisitions at 10 dB | loop-based |

Cross-referenced from earlier surveys (entries 17-19 below): Yue et al. 2023 code-aided polar CFO, |f| <= 7.8e-3,
cross-entropy search + EM, 0.3-0.4 dB BER loss ([2309.12828](https://arxiv.org/html/2309.12828)); Chen et al. 2023 DL
CFO ([2311.16155](https://ar5iv.labs.arxiv.org/html/2311.16155)); Yuan, Coskun, Kramer 2021 non-coherent polar
([2102.10719](https://ar5iv.arxiv.org/html/2102.10719)).

Searched for but NOT found / not readable: any 2019-2026 single-carrier paper with BLER after a blind CFO search
at |f| ~ 0.03 and Es/N0 < 0 dB; any transformer CFO estimator for single-carrier bursts with a CRB comparison; any
2020-2026 LDPC / polar syndrome-based CFO paper newer than Imad 2010 (only a 2023 Imad-Houcke phase-only follow-up was
listed); the full texts of Wang 2020 (IEEE, paywalled), Man et al. 2013 code-aided large-CFO LDPC (IEEE CL, page blocked),
the DVB-S2X VL-SNR acquisition paper (core.ac.uk blocked), Serbes 2019 (paywalled).

---

## 3. State of the art per receiver component

| Component | Ours | Best published (single-carrier) | Verdict |
|---|---|---|---|
| Coarse CFO (fast path) | 4th-power FFT + lag-4 autocorrelation + peak picking + Newton | NDA M-th power periodogram (R&B) + interpolation (Griebel 2021); DL regressors only better for < 1024 samples (O'Shea 2017) | **we already use it** |
| Acquisition below the NDA threshold | full-range CFO x phase grid, list-1 SC metric, checkpoints | pilots + DA-NDA (Noels 2005); code-aided candidate selection among 3-11 levels with pilots (Barbieri-Colavolpe 2007 x2); blind syndrome search (Imad 2010); GP search (Wang 2020) | **we already use it, and at lower SNR than any published one**; GP / SA search not recommended (sequential) |
| Fine CFO / phase | DD refinement on re-encoded symbols (hard), `pns` tracking | code-aided SDD / EM with soft symbols reaches coded CRB ~ MCRB (Noels 2005) | **behind in RMSE (2.3-3.8x MCRB), not in BLER** (<= 0.04 dB [derived]); no action |
| Pilot competitor quality | DVB-RCS2 ID 13, 128-preamble ML, 64+64 joint ML, all with code-aided CRC search | DA-KS (Griebel 2021), split placement optimal (Ying-Ghogho 2005), DA-NDA-SDD (Noels 2005) | **fair**; pilot receivers already reach the genie once the energy is removed [derived from 8.2a]; add C-1 for completeness |
| DL estimators | CNN estimator (9 M MACs) | CNN / ResNet regressors without BLER or CRB | **we already use it**; literature not ahead |
| Short-packet design | pilot-free + CRC + re-encoding | pilot-assisted finite-blocklength analysis (Kislal 2024), MOCZ, decoder-provided pilots | context only; **not applicable** as receivers |

---

## 4. Which competitors to implement (at most 2)

### C-1 (recommended): Noels-style DA-NDA-SDD code-aided turbo synchronizer on our pilot layouts
- What: DA estimate on the known symbols (128 preamble or DVB-RCS2 ID 13), NDA 4th-power search restricted to +-3 sigma
  around the DA peak, then 2-3 soft-decision-directed EM refinements of f and phase using the list-weighted soft symbols
  of CA-SCL-8, each followed by a decode. This is the classic published code-aided synchronizer for ~1000-symbol QPSK
  turbo bursts (Noels 2005), the reference a reviewer will ask for.
- Expected at our points [derived, not measured]: CFO RMSE close to the MCRB of the known + data symbols (~2e-5 at -5 dB,
  ~1e-5 at 0.5 dB), but BLER ~ unchanged vs our current pilot receivers, because they already sit at the genie once the
  pilot energy is removed (8.2a: 128-preamble ML -4.68 - 0.51 = -5.19 dB vs genie -5.19 dB at 1/10, 1e-4; DVB-RCS2 ID 13
  1.10 - 0.47 = 0.63 dB vs genie 0.64 dB at 2/5, 1e-3). So blind should stay ahead by about the energy charge: ~0.2 dB at
  1/10, ~0 at 0.15, ~0.5 dB at 2/5 and 1/2. The NDA stage is useless at -5 ... -3 dB (4th-power RMSE 2.4e-2 at -4 dB in
  est4) and only matters at 2/5, 1/2. Exception: DVB-RCS2 ID 13 at 1/10 -5 dB loses 0.2 % of packets outside |f| < 0.025
  (881 / 480k); EM cannot fix those (no pull-in); only a wider code-aided search can.
- Cost: our pilot receiver + 2-3 x ~1024 complex MACs for the soft EM + 1-2 decodes for failing packets.
- Test: 480k paired at 1/10 -5 dB, 0.15 -3.5 dB, 2/5 0.5 dB, 1/2 2 dB; report BLER, RMSE vs MCRB, MACs per core.

### C-2 (optional, cheap): Imad-style literature-faithful blind baseline
- What: 4th-power estimate -> search interval f_est +- 3 sigma_est (clipped to +-0.03) -> rank CFO candidates by the
  syndrome / frozen-only metric (for a polar code this is the rate-0-node part of our SC metric) -> CA-SCL-8 + CRC on the
  best few. It is the only published blind code-aided CFO search over a wide range, so it is the natural "published
  blind baseline".
- Expected [derived]: at 1/10 and 0.15 the 4th-power sigma is the whole range, so it reduces to our full grid with a
  frozen-only ranking, which our own test found equal to the full metric (P(rank <= 4) 0.9725 vs 0.9735 at 0.15 -4 dB,
  DEAD_ENDS): BLER ~ ours, MACs ~ ours without checkpoint savings unless they are added. At 2/5, 1/2 it equals our fast
  path. It cannot beat ours; it shows that the published blind idea, implemented on our code, lands where we are.
- Run only if the presentation needs a "published blind method" line; 64k at 0.15 -4 dB and 2/5 0.5 dB is enough.

Not recommended as competitors: GP / Bayesian-optimisation or cross-entropy searches (sequential, hurt MACs per core),
Barbieri-Colavolpe-Caire factor graph (needs an iterative SISO decoder; polar SCL is not), DL regressors (no BLER-level
evidence; ours exists).

---

## 5. Sources
- https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972 (via https://r.jina.ai/)
- https://link.springer.com/article/10.1155/2010/293572 and https://link.springer.com/content/pdf/10.1155/2010/293572.pdf (via https://r.jina.ai/)
- https://www.tlc.unipr.it/colavolpe/papers/j31.pdf (via https://r.jina.ai/)
- https://research.polyu.edu.hk/en/publications/iterative-doppler-frequency-offset-estimation-in-low-snr-satellit/ ; https://ieeexplore.ieee.org/document/9148098/ (empty page)
- https://ar5iv.labs.arxiv.org/html/1707.06260
- https://research.chalmers.se/publication/543507/file/543507_Fulltext.pdf (via https://r.jina.ai/)
- https://biblioteca.sbrt.org.br/articlefile/2063.pdf (via https://r.jina.ai/)
- https://arxiv.org/abs/2401.09089
- https://arxiv.org/abs/1902.02928
- https://arxiv.org/abs/2605.00761
- https://arxiv.org/abs/2404.09943
- https://www.bohrium.com/paper-details/fast-and-efficient-sinusoidal-frequency-estimation-by-using-the-dft-coefficients/812821168208740353-105711
- https://arxiv.org/abs/2609.07034
- https://arxiv.org/abs/2603.28262
- https://iris.polito.it/bitstream/11583/2651421/3/29017%20j1%20nexcode%20journal_x.pdf (via https://r.jina.ai/)
- https://zenodo.org/records/3471450/files/Synchronization%20Challenges%20in%20Deep%20Space.pdf (via https://r.jina.ai/)
- Cross-references: https://arxiv.org/html/2309.12828 ; https://ar5iv.labs.arxiv.org/html/2311.16155 ; https://ar5iv.arxiv.org/html/2102.10719

---

## Reference entries

### 1. N. Noels, H. Steendam, M. Moeneclaey, "Carrier and clock recovery in (turbo-)coded systems: Cramer-Rao bound and synchronizer performance", EURASIP J. Applied Signal Processing, 2005:6, pp. 972-980
- Link: https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972   - Type: paper   - Read depth: full (text reader)
#### What it does
Coded CRB for carrier phase / frequency / timing from BCJR marginals; compares DA, NDA, DA-SDD and DA-NDA-SDD (code-aided
EM) synchronizers. Rate-1/2 turbo, Gray QPSK, 1001 symbols, |fT| <= 0.1 cycles/symbol, Es/N0 about -1 ... 3 dB. Coded CRB
~ MCRB at the operating SNR; diverges below the SNR where BER is ~1e-2 ... 1e-3. DA-SDD at the CRB with a 512-symbol
preamble (34 %); with 256 DA-SDD degrades, DA-NDA-SDD at the CRB above ~1.5 dB; with 128 (11 %) above ~2 dB. Code-unaware
NDA threshold ~3.5 dB.
#### What we took / could take
Fine-CFO bound for our RMSE plot (coded CRB ~ MCRB of 1024 symbols: 2.1e-5 at -5 dB [derived]); competitor C-1
(DA-NDA-SDD on our pilot layouts). Shows that published code-aided sync needs pilots and >= ~2 dB.
#### Used in
-

### 2. R. Imad, S. Houcke, M. Ghogho, "Blind estimation of the phase and carrier frequency offsets for LDPC-coded systems", EURASIP J. Advances in Signal Processing, 2010, 293572
- Link: https://link.springer.com/article/10.1155/2010/293572   - Type: paper   - Read depth: full (text reader of the PDF)
#### What it does
Blind phase and CFO estimation by minimising a cost built from the LLRs of the LDPC syndrome elements. CFO: LDPC (512, 256),
d_c = 4, BPSK, CFO uniform in +-0.1 cycles/symbol, search by exhaustive grid or simulated annealing (the cost has many
local minima), optional narrowing to f_est +- 3 sigma from a classical estimator. MSE ~5e-8 at Eb/N0 2.5 dB (exhaustive),
~7e-8 at 3 dB with narrowing + 700 SA iterations; NLLS better for BPSK, the proposed method better for 16-QAM. Cost
O(n_r d_c n_iter). No CRB, no BER for the CFO part. Phase part: within ~0.2 dB of coherent at BER 1e-3 (8-iteration BP).
#### What we took / could take
The only published blind code-aided CFO search over a range as wide as ours; nearest published anchor for our claim.
Competitor C-2 (4th power -> +-3 sigma -> frozen-only ranking); for polar codes the syndrome metric corresponds to our
rate-0-node metric, already tested (DEAD_ENDS: frozen-only ranking = full metric).
#### Used in
-

### 3. A. Barbieri, G. Colavolpe, G. Caire, "Joint iterative detection and decoding in the presence of phase noise and frequency offset", IEEE Trans. Commun., 55(1), 2007
- Link: https://www.tlc.unipr.it/colavolpe/papers/j31.pdf   - Type: paper   - Read depth: full (text reader; figure numbers lost)
#### What it does
Sum-product over the joint posterior of data, Wiener phase and a constant frequency offset; frequency quantised to 11 levels
in the first iteration and 3 after; implicit frequency estimate = mean of its pdf. Pilots every 20 symbols (QPSK, 8PSK) or
40 (32APSK) bootstrap it; range limited by the pilot spacing (|f| < 0.025 for P = 20 [derived]). (3,6) LDPC 4000 bits,
DVB-S2 LDPC 64800. No measurable BER loss vs Tikhonov with known FO (forward-backward schedule); mixed schedule ~0.3 dB.
Complexity linear in the number of frequency levels.
#### What we took / could take
Supports our "frequency hypotheses scored by the decoder" design. Not used: needs an iterative SISO decoder (polar SCL is
not) and pilots; long codes.
#### Used in
-

### 4. J. Wang, C. Jiang, L. Kuang, S. Guo, "Iterative Doppler frequency offset estimation in low SNR satellite communications", IWCMC 2020, pp. 36-41
- Link: https://research.polyu.edu.hk/en/publications/iterative-doppler-frequency-offset-estimation-in-low-snr-satellit/ (IEEE: https://ieeexplore.ieee.org/document/9148098/)   - Type: paper   - Read depth: abstract
#### What it does
GP-MASO-MLE: non-data-aided coarse correction by Gaussian-process (Bayesian-optimisation) search of a decoder-based objective,
fine correction by MLE jointly with turbo iterations, for short bursts at low SNR. Within 0.1 dB of the ideal-correction BER;
RMSE near the MCRB for Eb/N0 >= 2 dB (as cited by Diniz et al. 2024). CFO range, code length, complexity not read.
#### What we took / could take
Not used: sequential sampling lengthens the per-core critical path; our parallel grid with checkpoints is the same idea.
#### Used in
-

### 5. T. J. O'Shea, K. Karra, T. C. Clancy, "Learning approximate neural estimators for wireless channel state information", arXiv 1707.06260, 2017
- Link: https://ar5iv.labs.arxiv.org/html/1707.06260   - Type: paper   - Read depth: full
#### What it does
1-D CNN regressors for CFO and timing of single-carrier QPSK bursts (RRC 0.25, 4 samples/symbol, CFO up to +-0.5
cycles/symbol, SNR 0 / 5 / 10 dB, AWGN and Rayleigh with delay spread). Baseline: 4th-power periodogram. The baseline wins
for blocks > 1024 samples at >= 5 dB (AWGN); the CNN wins for short blocks and under fading. CNN 23.7 MFLOP vs 5.4 MFLOP
for the baseline at 1024 samples. No CRB, no BER.
#### What we took / could take
Evidence that DL CFO estimators do not beat the 4th-power / search approach at our burst length in AWGN; our CNN estimator
is already the DL competitor. Not used.
#### Used in
-

### 6. A. B. de F. Diniz, T. Eriksson, U. Gustavsson, "Doppler shift estimation for satellite communications using linear estimators", IEEE SPAWC 2024
- Link: https://research.chalmers.se/publication/543507/file/543507_Fulltext.pdf   - Type: paper   - Read depth: full (text reader)
#### What it does
Multi-step DA estimator: phase from N1 pilot samples, then least squares on a third-order Taylor linearisation, N per step
chosen for minimum worst-case MSE. 500-sample all-ones pilot, AWGN, Doppler ~0.0275 rad/sample (~0.0044 cycles/sample
[derived]). Variance close to the CRLB down to about -6 dB; Tretter diverges at ~10 dB.
#### What we took / could take
Not used: a pure known tone, not a data burst; our pilot receivers already use ML / R&B FFT estimators.
#### Used in
-

### 7. C. A. C. Rodrigues, C. F. Dias, G. Fraidenraich, E. R. de Lima, "Study of a pilotless fine frequency estimator algorithm in burst-mode PSK transmissions", SBrT 2019
- Link: https://biblioteca.sbrt.org.br/articlefile/2063.pdf   - Type: paper   - Read depth: full (text reader)
#### What it does
L&R / Jiang-type fine frequency estimator with complex phase accumulation and vector projection for DVB-S2 without pilots;
21690-symbol window, coarse residual 4e-3; residual below the target at Es/N0 -2 dB; "close to the MCRB down to 0 dB";
Kay and Tretter degrade below ~9 dB.
#### What we took / could take
Not used: long frames, fine stage only.
#### Used in
-

### 8. A. O. Kislal, M. Rajiv, G. Durisi, E. G. Strom, U. Mitra, "Is synchronization a bottleneck for pilot-assisted URLLC links?", IEEE Trans. Wireless Commun. 23(12), 2024
- Link: https://arxiv.org/abs/2401.09089   - Type: paper   - Read depth: abstract
#### What it does
Finite-blocklength RCUs bound (saddlepoint) for pilot-assisted transmission over an imperfectly synchronised block-fading
waveform channel, joint delay and channel estimation from pilots, checked against the CRB. With independent delays per block,
synchronisation becomes the bottleneck. No numbers read.
#### What we took / could take
Context for the open item "timing unknown"; not a CFO competitor.
#### Used in
-

### 9. P. Walk, P. Jung, B. Hassibi, H. Jafarkhani, "MOCZ for blind short-packet communication: some practical aspects", arXiv 1902.02928, 2019
- Link: https://arxiv.org/abs/1902.02928   - Type: paper   - Read depth: abstract
#### What it does
Modulation on conjugate-reciprocal zeros for pilot-free short packets; a CFO is a common rotation of the zeros, fractional
rotations found by an oversampled zero-testing decoder, integer rotations absorbed by a cyclically permutable code. No numbers
in the abstract.
#### What we took / could take
Not used: a different modulation and code.
#### Used in
-

### 10. D. Bodet, M. Medard, M. Rangaswamy, K. Duffy, "The benefit of decoder-provided pilots in highly dynamic channels", arXiv 2605.00761, 2026
- Link: https://arxiv.org/abs/2605.00761   - Type: paper   - Read depth: abstract
#### What it does
Decoded codewords reused as pilots to update the channel estimate, non-iterative, code- and decoder-agnostic; information
limits on sensing while transmitting; fast fading. Qualitative results only in the abstract.
#### What we took / could take
Same idea as our `pns` code-aided phase tracking (already adopted); citation support.
#### Used in
-

### 11. M. Sy, R. Knopp, "Novel joint estimation and decoding metrics for short-blocklength transmission systems", arXiv 2404.09943 (IEEE CSCN 2023)
- Link: https://arxiv.org/abs/2404.09943   - Type: paper   - Read depth: abstract
#### What it does
BICM metrics for joint estimation and detection with low-density DMRS (power-boosted), BPSK / QPSK, polar and LDPC in a 5G
chain, up to 8 receive antennas; ~4-symbol windows "close to coherent".
#### What we took / could take
Not used: OFDM / 5G channel estimation, no CFO.
#### Used in
-

### 12. A. Serbes, "Fast and efficient sinusoidal frequency estimation by using the DFT coefficients", IEEE Trans. Commun. 67(3), pp. 2333-2342, 2019
- Link: https://www.bohrium.com/paper-details/fast-and-efficient-sinusoidal-frequency-estimation-by-using-the-dft-coefficients/812821168208740353-105711   - Type: paper   - Read depth: snippet
#### What it does
Iterative interpolation on shifted DFT coefficients for the frequency of a complex tone in noise. Numbers not read.
#### What we took / could take
Could replace the parabolic interpolation in the FFT pilot estimators (DVB-RCS2 ID 13, ML); expected gain tiny, since those
receivers already reach the genie after the energy charge. Not used.
#### Used in
-

### 13. H.-Y. Jung, D.-H. Paek, W.-J. Jung, S.-H. Kong, "Frequency estimation based on SNR-adaptive frequency estimator under wide SNR range", arXiv 2609.07034, 2026
- Link: https://arxiv.org/abs/2609.07034   - Type: paper   - Read depth: abstract
#### What it does
SAFE: a time-frequency image NN (TFINet) enhances weak tones, an SNR-based selector picks a robust or super-resolution
estimator; multi-tone, -10 ... 0 dB; FNR 13.00 % (13.04 % better than prior), NN-RMSE -56.67 %.
#### What we took / could take
Not used: multi-tone radar-style setting, no data modulation or decoding.
#### Used in
-

### 14. I. P. Vieira, G. V. Serra, R. A. Colares, D. A. A. Mello, "Spectral segmented linear regression for coarse carrier frequency offset estimation in optical LEO satellite communications", Opt. Express 34(17), 2026
- Link: https://arxiv.org/abs/2603.28262   - Type: paper   - Read depth: abstract
#### What it does
NDA coarse CFO from low-complexity operations on the received spectrum, cast as segmented linear regression; CFO up to about
half the symbol rate (per a search snippet); "low SNR" stress tests, no numbers in the abstract.
#### What we took / could take
Not used: optical continuous transmission.
#### Used in
-

### 15. M. Baldi et al., "State-of-the-art space mission telecommand receivers", IEEE Aerospace and Electronic Systems Magazine 32(6), pp. 4-15, 2017
- Link: https://iris.polito.it/bitstream/11583/2651421/3/29017%20j1%20nexcode%20journal_x.pdf   - Type: paper   - Read depth: full (text reader, OCR noise)
#### What it does
CCSDS telecommand receiver: ground carrier sweep + PLL, proposed FFT-aided acquisition and Costas loop; LDPC (128,64) and
(512,256); Es/N0 for CER 1e-5: (128,64) 0.55 dB (hybrid decoder) ... ~2.4 dB (MS), (512,256) 0.43 ... 1.85 dB. No sync-loss numbers.
#### What we took / could take
Not used: loop-based acquisition with long acquisition sequences; deployment context only.
#### Used in
-

### 16. J. Vila-Valls, M. Navarro, P. Closas, M. Bertinelli, "Synchronization challenges in deep space communications" (IEEE AES Magazine, ~2018-2019; year not stated in the text read)
- Link: https://zenodo.org/records/3471450/files/Synchronization%20Challenges%20in%20Deep%20Space.pdf   - Type: paper   - Read depth: full (text reader)
#### What it does
FFT carrier acquisition (replacing ground sweeping), Kalman / FLL-assisted PLLs, NC-DTTL; uncoded simulations, target Es/N0
2 dB; 8192-point FFT with 10 blocks: 0 / 50 misacquisitions at 10 dB vs 35-46 with one block. No code-aided method.
#### What we took / could take
Not used: deployment context only.
#### Used in
-

### 17. Q. Yue et al., "Code-aided CFOs and CPOs estimation in cooperative satellite communication", arXiv 2309.12828, 2023 (cross-reference; read in lit_blind_cfo.md, 2026-11-13)
- Link: https://arxiv.org/html/2309.12828   - Type: paper   - Read depth: full (survey 1)
#### What it does
Cross-entropy search over a 6-bit quantised CFO (120 candidates, 24 elites, 4-8 iterations) + EM with soft symbols from polar
BP LLRs; polar (1024, 512), BPSK, |f| <= 7.8e-3, Es/N0 ~ -3 dB, 2-4 satellites; 0.3-0.4 dB BER loss at 1e-4.
#### What we took / could take
Not used: sequential adaptive search, a quarter of our CFO range; noted as the closest polar code-aided CFO work.
#### Used in
-

### 18. Chen et al., "Deep learning-based frequency offset estimation", arXiv 2311.16155, 2023 (cross-reference; read in lit_blind_cfo.md)
- Link: https://ar5iv.labs.arxiv.org/html/2311.16155   - Type: paper   - Read depth: full (survey 1)
#### What it does
IQ-ResNet regression of CFO; BPSK / FSK / QAM, 512-2048 samples, |f| <= 0.2, -20 ... 30 dB; beats Kay; no CRB, no complexity.
#### What we took / could take
Not used: no BLER or CRB evidence; our CNN estimator covers the DL comparison.
#### Used in
-

### 19. P. Yuan, M. C. Coskun, G. Kramer, "Polar-coded non-coherent communication", IEEE Commun. Lett. 2021, arXiv 2102.10719 (cross-reference; read in lit_blind_cfo.md and lit_polar_sync.md)
- Link: https://ar5iv.arxiv.org/html/2102.10719   - Type: paper   - Read depth: full (surveys 1, 2)
#### What it does
Phase (no CFO) by max p(y | theta, u_F = 0) via SCL(L_e) up to bit beta, coarse-fine search, then SCL-8 + CRC; (128, 32) +
CRC-6, QPSK; within 0.3 dB of coherent, ~1.5 dB over 14-pilot PAT at FER 1e-4.
#### What we took / could take
Same structure as our Stage 2 / Stage 3 (phase only); list-marginalised metric is survey 2 finding F3.
#### Used in
-
