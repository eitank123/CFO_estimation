# Literature survey 2: code-aided synchronization, blind detection and phase-noise robustness WITH POLAR CODES (2026-11-15)

Scope (main-session request): methods that use the polar code itself (frozen bits, decoder metrics, list, CRC) to
estimate CFO / phase, to detect / acquire a packet, or to track phase noise, that we have NOT yet considered, or better
versions of what we do. Aims: (a) fewer MACs per core at the same BLER, (b) close the BLER gap at the lowest SNRs
(Stage 2 misses), (c) pilot-free phase tracking under Wiener phase noise.

Read before searching (not repeated here): `lit_blind_cfo.md` (survey 1, 30 sources), `lit_dvbrcs2.md`,
`DEAD_ENDS.md`, the README "Current state", `lit_checks_results.md`, `expected_cap_pn_comb.md` (phase-noise
results), `expected_eqrb.md` (rotation-bit test in flight), `expected_est4.md`. Sources already in survey 1
(Giard 2017/18, Condo 2017, Geiselhart 2023, Yuan-Coskun-Kramer 2021, Yuan-Duffy-Medard 2024, Qualcomm US10615825,
...) appear below only when a NEW point was read from them.

Reading depth: "full" = full text read (HTML or text extraction); "abstract"; "snippet" = search-result text only.
Numbers marked **[derived]** are my own arithmetic, not from a source. No simulations were run.

**Main comparability caveat.** Still no paper does a blind CFO search over |f| <= 0.03 cycles/symbol with a polar code.
Every code-aided CFO paper found works with |f| <= 2e-4 at N = 2048 (EM pull-in range), i.e. 150x smaller than ours.
The phase-noise papers use BPSK, LDPC or N <= 512 and give few numbers in the text. Treat all dB values as indicative.

---

## 1. Ranked actionable findings (6)

### F1. Code-aided phase SMOOTHING retry for phase noise (time-varying phase from the list's re-encoded symbols) - top item for (c)
- Sources: Colavolpe, Barbieri, Caire, JSAC 2005 ([j26.pdf](https://www.tlc.unipr.it/colavolpe/papers/j26.pdf), full via
  text reader): Tikhonov forward-backward phase smoother ("a nonlinear Kalman smoother"), within 0.1 dB of coherent on
  DVB-S2 phase-noise models, but it needs pilots to bootstrap (EXIT: stuck at zero extrinsic without pilots).
  Barbieri-Colavolpe 2007 CBC smoother (in `lit_dvbrcs2.md`). Isikman, Mehrpouyan, Graell i Amat 2012
  ([1210.6267](https://arxiv.org/abs/1210.6267), abstract): soft-decision-directed EKF smoother inside EM, close to
  perfect phase knowledge at low-medium SNR (LDPC). Mei & Qu 2026 ([2610.16363](https://arxiv.org/html/2610.16363), full):
  the pilot-free soft-decision-directed Kalman smoother (SDD-EKS) used as their polar baseline has error floors under
  STRONG phase noise, but is better than their method under weak phase noise.
- Why it fits us: our Stage 2 search IS the bootstrap the Tikhonov / Kalman methods lack (it gives CFO, phase and a
  near-right list). After a failed CA-SCL-8 decode at a good candidate, form z_k = y_k conj(xbar_k) with xbar the
  re-encoded QPSK symbols of the best path (better: the list-weighted average over the 8 paths, weights exp(-PM_l)),
  smooth arg z with a two-sided window (or a Wiener / Tikhonov recursion), de-rotate, decode again (1-2 iterations).
- Expected gain [derived]. With Wiener increment variance s2 = 2 pi (linewidth x Ts) per symbol and packet length
  T = 1024, the blind receiver's CFO + phase fit is a straight-line fit of the phase path; the mean-square residual of a
  Brownian path after a least-squares line is s2 T / 15 (after a constant only: s2 T / 6; around the centre phase, the
  "genie": s2 T / 4). So the residual RMS phase of today's receiver is:

  | linewidth x Ts | blind now (line fit) | genie (true CFO, centre phase) | code-aided smoother, right decisions, 2/5 at 0.5 dB | same, 1/10 at -5 dB | same, 0.15 at -3.5 dB |
  |---|---|---|---|---|---|
  | 1e-4 | 0.207 rad | 0.40 rad | 0.098 rad (W ~ 92 symbols) | 0.135 rad (W ~ 170) | 0.124 rad |
  | 3e-4 | 0.36 rad | 0.70 rad | 0.129 rad (W ~ 53) | 0.178 rad (W ~ 100) | 0.16 rad |

  Smoother error from var = 1/(2 rho W) + s2 W / 12, optimum W = sqrt(6/(rho s2)), minimum var = sqrt(s2/(6 rho)),
  rho = Es/N0 linear. The 2:1 genie-vs-blind ratio explains the measured "genie far worse than blind under phase noise"
  (expected_cap_pn_comb.md). A 0.21 rad residual is a coherent-power loss of about 0.2 dB plus a similar amount of
  quadrature interference, i.e. ~0.3-0.4 dB, which is the right size for the measured x36 BLER at 2/5 0.5 dB, 1e-4.
  Halving the residual should remove most of that loss at 2/5 and 1/2, and most of the x3 at 1/10, 0.15. Not measured.
- Cost: per smoothing iteration ~1024 complex MACs for z + a running sum or recursion (a few thousand MACs) + one
  CA-SCL-8 decode (dominant). Applied only after a CRC / rho failure at the top candidate, so in AWGN it touches only
  failing packets.
- Risks: (1) DEAD_ENDS lists `dd` (code-aided CFO / phase refinement, AWGN: no packet fixed) and the "verified re-decode"
  (a wrong codeword re-converges to itself). The NEW reason is a time-varying phase that the constant-phase grid cannot
  represent; in AWGN there was nothing to fix. (2) Self-confirmation: run it only on CRC-failed decodes, never to
  "verify" a passed one; the list-weighted soft symbols reduce lock-in to one wrong path. (3) In AWGN the window adds
  phase noise of its own (1/(2 rho W) ~ 0.005 rad^2 at W = 100, 0.5 dB): harmless on a retry, but measure it.
- Test: flag e.g. `pn_smooth` (window W from the rate's operating SNR, or a Tikhonov recursion with s2 as a parameter).
  64k paired with BLIND_PN = 1e-4 and 3e-4 at 2/5 0.5 dB, 1/2 2 dB, 0.15 -3.5 dB, 1/10 -5 dB (the pn1-pn3 points), plus
  AWGN at 2/5 0.5 dB and 0.15 -4 dB to show no loss and the MAC cost. Report BLER, undetected, MACs per core. A first
  offline check is possible on the pn dumps if they hold the received packet and the failed list: the RMS of
  (true phase path - smoothed estimate) vs the 0.21 / 0.36 rad of the line fit.

### F2. Make the re-encoding check (rho) phase-noise tolerant, and keep CRC (not a likelihood threshold) as the gate under mismatch
- Sources: Sauter, Kislal, Durisi, Liva, Matuz, Strom, IEEE T-COM 2025 ([2503.02782](https://arxiv.org/html/2503.02782),
  full): CA-polar, SCL L = 8, n = 64-256; on a phase channel with a 10-pilot ML phase estimate (mismatched decoding) the
  CRC-based detection "largely outperforms" Forney's threshold test, which wins only at n = 64; on biAWGN the threshold
  test wins (0.5-0.95 dB). Coskun, Liva, Ostman, Durisi 2019 (survey 1 #10): final list choice by a non-coherent metric.
- Why it matters: rho is a coherent sum over 1024 symbols. Under phase noise a RIGHT decode keeps only
  |mean e^{j phi}|^2 ~ e^{-phi_rms^2} of its correlation power: ~0.96 at 1e-4, ~0.88 at 3e-4 [derived from the F1
  residuals], so right packets near RHO_N are rejected; the wrong-pass side is unchanged. A segmented rho
  (sum over S segments of |sum_seg y conj(xhat)|^2, non-coherent across segments, S = 4-8) loses little in AWGN and
  is insensitive to the drift. It also says: survey 1's finding 5 (Forney / SO-SCL threshold for acceptance) should be
  deprioritised, since it is the variant that degrades under mismatch.
- Gain: unknown (how many pn failures are "right codeword, rho rejected"?). Cost: ~0 MACs.
- Test: offline first on the pn1-pn3 dumps: rho / RHO_N of right decodes vs pn level; count right CRC passes rejected
  by rho. If > 5 % of the pn errors, add `rho_seg = S`, recalibrate RHO_N on noise-only frames (as for the other rates)
  and rerun the pn points 64k paired.

### F3. List-marginalised metric (L_e = 2-8) at the last checkpoint - still untested, now with numbers - for (b)
- Source: Yuan, Coskun, Kramer 2021 ([ar5iv 2102.10719](https://ar5iv.arxiv.org/html/2102.10719), full, re-read):
  (128, 32) + CRC-6, QPSK, phase-only; the estimator stops at bit beta: beta = 113 with L_e = 8 gives FER 1.0e-4 and
  8807 visited nodes, beta = 113 with L_e = 1 gives 3.5e-4 and 2439 nodes (3.5x lower FER for 3.6x the estimator
  work); beta = 61, L_e = 8: 3.2e-3; beta = 47, L_e = 1: 3.4e-2. For B = 2 phase blocks the joint search grows
  exponentially in B.
- Our state: P(rank of true cell <= 4) is 0.9725 at 0.15 -4 dB even with the FULL-length list-1 metric
  (`lit_checks_results.md`), so part of the Stage 2 misses is the metric itself, not the checkpoints. The frozen-only
  metric did not help (dead end); the list-marginalised metric is a different metric and is NOT in DEAD_ENDS.
- Not a cheap substitute: the SC "codebook probability" of Yuan, Duffy, Medard ([2402.05004](https://arxiv.org/html/2402.05004),
  full) adds, at every untaken information branch, 2^{-|F(i:N)|} Q(a^i | y). With ~1700-1800 frozen bits at our low
  rates the weight is negligible except for the last information bits [derived], so the list-1 version equals our PM.
  Real marginalisation needs L_e > 1 paths.
- Cost: L_e x the remaining partial pass, only for the survivors of the last checkpoint (~32-64 cell x phase pairs).
- Test: offline in the `lit_checks.py` rank harness (201 cells x 4 phases, 2000 packets): P(rank 1), P(rank <= 4) for
  L_e = 1, 2, 4, 8 (log-sum-exp of the L_e PMs) at 0.15 -4 dB and 1/10 -5 dB. Go online (flag at the last checkpoint,
  64k paired) only if P(rank <= 4) rises by >= 0.005 at 0.15 -4 dB.

### F4. The rotation-bit construction (`eqrb`) is the published one - confirmation, no new action
- Source: Choi & Lee 2026 ([2602.17979](https://arxiv.org/html/2602.17979v1), full): QPSK segment, positions N-2 and N-1
  frozen at the transmitter and decoded as free bits, rotation read from them ([1,0] = pi/2, [0,1] = pi, [1,1] = 3pi/2),
  then the re-encoded symbols are implicit pilots. Gains up to 1.5 dB over PAT (16-QAM, B = 3), ~1 dB (B = 1, 16-QAM),
  PAT equal or slightly better at R = 0.25 with K = 60. Rate matching breaks the symmetry only with shortening /
  puncturing on that segment; our N = 2048 fills 1024 QPSK symbols exactly.
- Meaning for us: `expected_eqrb.md` already implements this; the paper's weaker result at low rate matches our
  equiv finding at 1/10, 0.15. No change to the test plan.

### F5. In-decode frozen-bit abort inside the main CA-SCL-8 decodes (frozen-only per-path metric, stop when all paths fail)
- Source: Lin, Sarkis, Yang (Qualcomm), US 10742238 B2, 2020 ([Google Patents](https://patents.google.com/patent/US10742238B2/en),
  first 100k of 289k characters): per path a frozen-bit-only path metric (normalised by a scalar array, by the summed
  LLR magnitudes or by the number of frozen bits seen), prune a path when it exceeds a threshold, terminate the decode
  when every path is pruned; only reliable frozen positions may be used. No BLER / FAR numbers.
- Difference from what we have: our checkpoints do this for the list-1 Stage 2 metric across cells; survey 1's
  finding 4 (PM-spread abort) is about the list spread. This is an absolute per-path test inside the CA-SCL-8 decode of
  a wrong candidate. The post-decode retry gate failed (0 fixed / 8 broken), so the abort threshold must be set for
  <= 1e-4 loss of right decodes and checked on >= 400k packets.
- Gain [rough]: CA-SCL decodes are ~25 % of MACs at 0.15 -4 dB; if wrong-candidate decodes stop at half length, at
  most ~10 % of the total. Cost: none. Test: decode dump with the frozen-only PM of every path at 1/4, 1/2, 3/4 of the
  frozen set, offline ROC (right vs wrong candidates), then a flag at 0.15 -4 dB, 2/5 0.5 dB, 400k paired.

### F6. What NOT to do (read and rejected, with reasons)
- **EM code-aided CFO / phase with polar BP** (BIT patent [CN110519200B](https://patents.google.com/patent/CN110519200B/en);
  Wu et al. 2025, J. TT&C, [PDF](https://castjournals.cast.org.cn/joweb/ycyk/EN/PDF/10.12347/j.ycyk.20250628001)):
  (2048, 1024) BPSK, reliable range +-1.5e-4 (+-2e-4) cycles/symbol, "closer to the MCRB than Fitz". Our grid already
  covers that; it confirms that EM alone has no pull-in at our CFO range (and `dd` is a dead end).
- **SC trellis decoding with quantised phase states** (SCT; Wang, Liu, Hou 2014 [1404.3001](https://arxiv.org/abs/1404.3001);
  cost O(|S|^3 N log N) as stated in Aharoni et al. 2023 [2309.03148](https://arxiv.org/html/2309.03148)): Q = 8 phase
  states = 512x an SC pass. Not applicable.
- **Per-segment phase hypotheses inside the SC tree**: [derived] in the polar transform a node at depth d combines code
  bits spaced N/2^d apart, so every node mixes all time positions (and the interleaver permutes them further); no
  node sees only one time segment, so per-segment phases cannot be pruned locally. A B-segment phase search is
  exponential in B (Yuan et al. 2021). Not applicable.
- **Log-density spectrum recursion (LDSR)** (Mei & Qu 2026): SC on phase densities, N(56 log2 N - 54) + 54 real mults
  per decode = ~1.15 M at N = 2048 [derived from their formula], BPSK only, no list version, no numbers in the text,
  "inferior to Kalman under weak phase noise". Park; revisit only if F1 fails at 3e-4.
- **NDA (4th-power, V&V) sliding-window phase tracking**: [derived] per-symbol variance of the 4th-power phase is
  ~4.8 rad^2 at 0.5 dB (from E|s+n|^8) and ~194 rad^2 at -5 dB; the optimum window is ~300 symbols at 0.5 dB, 1e-4,
  residual 0.18 rad vs 0.207 rad from today's line fit (no gain), and longer than the packet at -5 dB. Cycle slips at
  low SNR on top. Not worth a test.
- **Quadratic (chirp) phase hypotheses** to absorb more of the Wiener path: [derived] residual mean square
  s2 T / 15 -> 3 s2 T / 70 (RMS x0.8) for a 2-D grid. Not worth it.
- **Code-aided pilots inside the codeword** (systematic polar pilot selection, Li, Xu, Hu 2018
  [1801.02860](https://arxiv.org/abs/1801.02860); Ghaddar et al. T-COM 2021, snippet): known coded symbols cost rate like
  pilots; they belong to the pilot reference family (est4), not to the blind receiver.

---

## 2. Per-source table (new sources of this survey)

| # | Title (authors), year | Link | Read | Relevance | Method | Setting | Numbers | How we would test it |
|---|---|---|---|---|---|---|---|---|
| 1 | Log Density Spectrum Based Decoding of Polar Codes for Channels with Strong Phase Noise (Mei, Qu), 2026 | [2610.16363](https://arxiv.org/html/2610.16363) | full (text + refs) | medium: the only polar decoder for Wiener phase noise | SC recursion on 2-D Fourier spectra of log-densities over phase; 4 approximations, 7-13 spectral terms | BPSK, AWGN + Wiener (sigma_phi 1.9 deg, 7.5 deg, 30 deg per symbol) and linear drift; N = 128, 512, R = 1/4, 1/2; no pilots; baselines SC and SDD-EKS (Shehata & El-Tanany 2009) | no numbers in text; removes SC / SDD-EKS error floors under strong noise, worse under weak noise; cost N(56 log2 N - 54) + 54 real mults | not now (F6); our 1e-4 = 0.025 rad per symbol is their "weak" regime |
| 2 | Learning While Transmitting: Pilotless Polar Coded Modulation (Choi, Lee), 2026 | [2602.17979v1](https://arxiv.org/html/2602.17979v1) | full | medium-high: same rotation-bit trick as eqrb | QPSK coded-pilot segment: 4th-power VVPE phase, rotation from u_{N-2}, u_{N-1}, re-encoded symbols as pilots for QAM | B = 1, 3 block fading; M = 240-720 coded bits; CRC-11; SC / SCL-8; BLER 1e-3 | up to 1.5 dB over PAT (16-QAM, B = 3); ~1 dB (B = 1); PAT equal at R = 0.25 | F4: already in eqrb |
| 3 | Polar-Coded Non-Coherent Communication (Yuan, Coskun, Kramer), 2021 (re-read) | [ar5iv 2102.10719](https://ar5iv.arxiv.org/html/2102.10719) | full | high: list-marginalised metric | p(y \| theta, u_F = 0) by SCL(L_e) up to bit beta; B phase blocks searched jointly | (128, 32) + CRC-6, QPSK, B = 1, 2 | L_e = 8 vs 1 at beta = 113: FER 1.0e-4 vs 3.5e-4, 8807 vs 2439 nodes; B = 2 search exponential in B | F3 rank harness |
| 4 | Near-Optimal Generalized Decoding of Polar-like Codes (Yuan, Duffy, Medard), 2024 (re-read) | [2402.05004](https://arxiv.org/html/2402.05004) | full | medium: shows the list-1 codebook probability ~ PM at low rate | Q* = visited leaves + sum over untaken branches 2^{-\|F(i:N)\|} Q(a^i \| y) | dRM, 5G polar, N = 32-128 | MDR <= eps (0.1, 0.005); uniform-subtree approximation breaks with late static frozen bits | none (argument in F3) |
| 5 | Undetected Error Probability in the Short Blocklength Regime (Sauter, Kislal, Durisi, Liva, Matuz, Strom), T-COM 2025 | [2503.02782](https://arxiv.org/html/2503.02782) | full | high for acceptance under phase error | CRC-based vs Forney-threshold detection on CA-SCL; finite-blocklength bounds | n = 64-256, R = 1/2, L = 8; biAWGN and a phase channel with 10-pilot ML estimate | biAWGN: threshold better (0.5-0.95 dB); mismatched phase: CRC "largely outperforms" threshold, threshold better only at n = 64 | F2 (keep CRC + rho; segmented rho) |
| 6 | Algorithms for iterative decoding in the presence of strong phase noise (Colavolpe, Barbieri, Caire), JSAC 2005 | [j26.pdf](https://www.tlc.unipr.it/colavolpe/papers/j26.pdf) | full (text reader; tables garbled) | high: the smoother to borrow | sum-product with canonical phase pdfs: Fourier and Tikhonov; Tikhonov = forward-backward "nonlinear Kalman smoother" | (3,6) LDPC n = 4000 BPSK; DVB-S2 64800; 1 pilot per 20 symbols; Wiener and ESA models | Tikhonov < 0.1 dB from coherent (DVB-S2, ESA mask); needs pilots to bootstrap (EXIT) | F1 (our search = bootstrap) |
| 7 | Phase Noise Estimation for Uncoded/Coded SISO and MIMO Systems (Isikman, Mehrpouyan, Graell i Amat), 2012 | [1210.6267](https://arxiv.org/abs/1210.6267) | abstract | medium | EM code-aided turbo sync with soft-decision EKF / Kalman smoother (KS-MLA, EKS) | LDPC, SISO / MIMO, BICM | "close to perfect phase knowledge at low-medium SNR"; no numbers in abstract | F1 variant (Kalman instead of window) |
| 8 | CN110519200B: polar-code-assisted carrier synchronization at low SNR (Beijing Inst. Tech.), 2019/2020 | [Google Patents](https://patents.google.com/patent/CN110519200B/en) | full description | low: tiny pull-in | EM loop: compensate -> BP decode -> soft symbols (simplified tanh) -> arg-based f, phase | (2048, 1024), (1024, 512), (512, 256) BPSK AWGN | reliable f range +-1.5e-4, phase +-0.4 pi (N = 2048); uncorrected 1.2e-4 costs 0.5 dB; closer to MCRB than Fitz, V&V | none (F6) |
| 9 | Carrier synchronization frequency offset estimation for aerospace TT&C (Wu, Wang, Chen, Wang), J. TT&C 46(6) 2025 | [PDF](https://castjournals.cast.org.cn/joweb/ycyk/EN/PDF/10.12347/j.ycyk.20250628001) | full (text reader) | low | PCAFOE: EM-style ML with BP posteriors | (2048, 1024) BPSK, Eb/N0 0-5 dB, \|f\| <= 2e-4 | closer to MCRB than Fitz (plots only); no complexity | none |
| 10 | Frozen bits based pruning and early termination for polar decoding (Lin, Sarkis, Yang, Qualcomm), US 10742238 B2, 2020 | [Google Patents](https://patents.google.com/patent/US10742238B2/en) | first 100k of 289k chars | medium | frozen-only per-path metric, normalised; prune > threshold; stop when all paths fail | 5G control, L = 4 example | no BLER / FAR numbers | F5 |
| 11 | Polar-Coding-Assisted Blind Frame Synchronization Based on Soft Information of Frozen Bits (Feng, Liu, et al.), IEEE CL 27(10) 2023 | [dblp](https://dblp.dagstuhl.de/rec/journals/icl/FengLZXJ23.html) | snippet only | medium-low: frame timing from frozen-bit soft info | metric ~ P(frozen sequence right), low-complexity approximation merged with SCL; ROC / CDF analysis | not read | not read | only relevant if timing becomes unknown (open item) |
| 12 | Blind Recognition of Polar Codes Using SCL Decoding (Tu, Liu, Feng, Niu), 2026 | [2605.13331](https://arxiv.org/abs/2605.13331) | abstract | low: non-cooperative code recognition | per-position frozen / info hypotheses in an SCL across many frames | (32,16) ... (128,64), L = 64 | >= 2.5 dB over prior method | none |
| 13 | Partially Polarized Polar Codes for 6G Control Channels (Fazeli, Mansour, Zhu, Jalloul), ICC 2026 | [2601.15404](https://arxiv.org/abs/2601.15404) | abstract | low-medium | prune kernels so information bits arrive early -> earlier termination in blind decoding | PDCCH | no numbers in abstract | only with a code change; not now |
| 14 | Node-Based Soft-Output Fast SCL Decoding (Shen, Wu, Gao, et al.), T-COM 2026 | [2604.17482](https://arxiv.org/abs/2604.17482) | abstract | medium: soft outputs for F1 | SO-SCL with Fast-SSC nodes | polar | vs SO-SCL: time steps -81.8 %, additions -41.3 %, comparisons -46.4 % | F1 soft symbols (if the list-weighted average is not enough) |
| 15 | Speculative SC Decoding of Polar Codes (Seah, Rubenacke, Gross), 2026 | [2608.02760](https://arxiv.org/abs/2608.02760) | abstract | low: latency, not MACs | speculative parallel execution in general nodes + verification | N = 4096 | -69 % sequentially traversed nodes, same FER | none (our cost model counts MACs) |
| 16 | Data-Driven Neural Polar Codes for Unknown Channels With and Without Memory (Aharoni, Huleihel, Pfister, Permuter), 2023 | [2309.03148](https://arxiv.org/html/2309.03148) | intro / abstract (first 100k chars) | low-medium | neural SC replaces f / g / decision; cost O(k d N log N) | finite-state channels | states the SCT cost O(\|S\|^3 N log N) | none (F6); NN metrics already a dead end for us |
| 17 | Joint SC Decoding of Polar Codes over ISI Channels (Wang, Liu, Hou), 2014 | [1404.3001](https://arxiv.org/abs/1404.3001) | abstract | low | SC trellis (channel states at the top of the SC tree), list extension | ISI channels | no numbers in abstract | none |
| 18 | Multiple Hypotheses Iterative Decoding of LDPC in Strong Phase Noise (Shayovitz, Raphaeli), 2012 | [1210.5198](https://arxiv.org/abs/1210.5198) | abstract | low | phase-hypothesis mixtures in BP with mixture reduction | LDPC | none in abstract | none |
| 19 | A New Algorithm for Improved Blind Detection of Polar Coded PDCCH (Jalali, Ding), 2019 / TWC 2020 | [1902.10280](https://arxiv.org/abs/1902.10280) | abstract | low | LP relaxation of polar constraints in MIMO detection; a metric that removes most wrong candidates before decoding | 5G PDCCH, MIMO | none in abstract | none (MIMO detector) |
| 20 | Channel Estimation with Systematic Polar Codes (Li, Xu, Hu), 2018 | [1801.02860](https://arxiv.org/abs/1801.02860) | abstract | low: pilots inside the codeword | pilots chosen among systematic coded symbols (EPS / UEPS) | fading, Doppler 50 Hz | EPS better than pilot insertion (no numbers in abstract) | pilot family (est4) only |
| 21 | Joint Channel Estimation and Coding Over Channels With Memory Using Polar Codes (Ghaddar, Kim, Milstein, Ma, Yi), T-COM 2021 | [search record](https://www.bohrium.com/paper-details/joint-channel-estimation-and-coding-over-channels-with-memory-using-polar-codes/812018367450841088-2495) | snippet (page blocked; arXiv number in the index was wrong) | medium-low | list decoding marks reliably-decoded bits, iterative estimation-decoding; pilots embedded in the codeword | finite-state Markov, Gauss-Markov, flat fading | not read | supports F1's "use the list to pick reliable symbols" |
| 22 | Noncoherent Detection With Polar Codes (Chen et al.), IEEE Access 2019 | [BIT record](https://pure.bit.edu.cn/en/publications/noncoherent-detection-with-polar-codes/) | snippet | low | BDPSK + SC; MSDSD + BP iterative | - | ~3 dB from coherent | none (differential costs ~3 dB) |
| 23 | Learning to Mitigate the FAR in Polar Code Blind Detection, IEEE WCL 2019 | [unpaywall DOI](https://unpaywall.org/10.1109%2FLWC.2019.2937299) | snippet | low | NN classifier after a CRC pass | PDCCH, short CRC | not read | our false-pass NN is a dead end |
| 24 | Subcode Ensemble Decoding of Polar Codes (Lulei et al.), 2025 | [2504.17511](https://arxiv.org/abs/2504.17511) | abstract | none | ensemble decoding via pre-transformations | - | - | none |

Not found or not readable: any paper with a polar CFO search wider than 2e-4 cycles/symbol; any polar SCL decoder
with per-path phase tracking (searched several phrasings; nothing); the full text of Feng et al. 2023 (frame sync),
Ghaddar et al. 2021, Barbieri-Colavolpe-Caire 2007 (phase noise + frequency offset, j31.pdf not parseable), the
Petry et al. 2024 pilot-less DL synchronization PDF (binary only), PDCCH early-termination papers with FAR numbers.

---

## 3. What this means for phase-noise robustness without pilots

1. **Where the loss is.** The blind receiver already absorbs the linear part of the Wiener path (CFO cell + refinement
   = a line fit). [derived] Residual RMS 0.21 rad at 1e-4 and 0.36 rad at 3e-4 over 1024 symbols, against 0.40 / 0.70
   rad for the "genie" (true CFO, centre phase): this explains why the genie lost more than blind. The Stage 2 metric
   loses only ~e^{-0.043} of its coherent power at 1e-4 (about 0.2 dB), so the search mostly survives; the loss is in
   the decode (and maybe rho). At 3e-4 (~0.56 dB metric loss) Stage 2 misses grow too.
2. **What the literature does.** Pilot-free phase tracking is either (a) a code-aided forward-backward smoother
   (Tikhonov / Kalman) fed by decoder soft symbols, which needs a bootstrap and is near-coherent once started
   (Colavolpe et al. 2005, Isikman 2012), or (b) a decoder that carries phase densities through the code (LDSR 2026,
   SC trellis), which is far costlier and BPSK-only so far. Our grid search is the bootstrap that (a) lacks: F1.
3. **What cannot work inside SC.** Per-segment phases cannot be handled at the nodes, because every polar node mixes all
   time positions [derived]; joint per-block phase search is exponential in the number of blocks (Yuan et al. 2021).
   So tracking must sit outside the decoder, between decodes (F1), not inside the Stage 2 metric.
4. **Expected size [derived, not measured].** A code-aided smoother with mostly-right decisions leaves ~0.10-0.13 rad
   at 2/5 0.5 dB and ~0.13-0.18 rad at 1/10 -5 dB, for 1e-4 and 3e-4: about half of today's residual, enough to remove
   most of the ~0.3-0.4 dB loss at 1e-4. It cannot fix packets whose first decode is far from right (Stage 2 misses).
   NDA 4th-power tracking gives no gain at our SNRs.
5. **Acceptance.** Make rho segment-wise non-coherent (F2) before trusting any phase-noise BLER; keep CRC + rho, not a
   likelihood threshold, as the acceptance under phase error (Sauter et al. 2025).
6. **Pilot competitor context.** est4's C1b (DVB-RCS2 pilots + smoothing) is the published way to do the same with
   pilots; `lit_dvbrcs2.md` estimated 16-21 deg (0.29-0.37 rad) residual for pilot-only tracking at -5 dB. The
   code-aided figures above (0.13-0.18 rad at -5 dB) are lower because the decoder supplies ~1024 "pilots" instead of 53,
   if its decisions are right.

---

## 4. Sources
- https://arxiv.org/html/2610.16363 and https://arxiv.org/abs/2610.16363
- https://arxiv.org/html/2602.17979v1
- https://ar5iv.arxiv.org/html/2102.10719
- https://arxiv.org/html/2402.05004
- https://arxiv.org/html/2503.02782 and https://arxiv.org/abs/2503.02782
- https://www.tlc.unipr.it/colavolpe/papers/j26.pdf (read via https://r.jina.ai/)
- https://arxiv.org/abs/1210.6267
- https://patents.google.com/patent/CN110519200B/en
- https://castjournals.cast.org.cn/joweb/ycyk/EN/PDF/10.12347/j.ycyk.20250628001 (read via https://r.jina.ai/)
- https://patents.google.com/patent/US10742238B2/en
- https://dblp.dagstuhl.de/rec/journals/icl/FengLZXJ23.html
- https://arxiv.org/abs/2605.13331
- https://arxiv.org/abs/2601.15404
- https://arxiv.org/abs/2604.17482
- https://arxiv.org/abs/2608.02760
- https://arxiv.org/html/2309.03148
- https://arxiv.org/abs/1404.3001
- https://arxiv.org/abs/1210.5198
- https://arxiv.org/abs/1902.10280
- https://arxiv.org/abs/1801.02860
- https://www.bohrium.com/paper-details/joint-channel-estimation-and-coding-over-channels-with-memory-using-polar-codes/812018367450841088-2495
- https://pure.bit.edu.cn/en/publications/noncoherent-detection-with-polar-codes/
- https://unpaywall.org/10.1109%2FLWC.2019.2937299
- https://arxiv.org/abs/2504.17511
