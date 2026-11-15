# Literature survey 3: methods to ADOPT for lower BLER (waterfall, R = 1/10, 0.15) at reasonable cost (2026-11-15)

Scope (main-session request): what can be borrowed to lower BLER of the blind receiver at the four hard points
(1/10 -5 dB, 0.15 -4 dB, 2/5 0.5 dB, 1/2 2 dB): better ranking metrics and sync-friendly codes, stronger decoding at the
right CFO, phase-noise robustness without pilots, combining across hypotheses, and finite-blocklength headroom.
Read first (not repeated): `lit_blind_cfo.md` (survey 1), `lit_polar_sync.md` (survey 2, F1-F6), `DEAD_ENDS.md`,
`expected_f3f5.md`, `expected_pns.md` (pns measured), `expected_ref.md` (D0 smoke), `08_parameters_results.md`.

Reading depth per source: "full" / "abstract" / "snippet" (search-result text only). Numbers marked **[derived]** are my
own arithmetic, not from a source. No simulation was run. Several PDFs (Polyanskiy-Poor-Verdu 2010, Ostman 2019,
Ferro 2025, PolarBear) came back as unparseable binary or 403; they are marked "snippet".

**Comparability caveat.** No source does a blind CFO search of |f| <= 0.03 with a polar code. The list-size numbers
come from N = 512 ... 2048 polar codes in AWGN with known channel (they apply to our "decode at the right CFO" part,
not to the search). The phase-noise sources use LDPC / convolutional codes, BPSK / DPSK or block-constant phase.

---

## 0. Where the headroom is (finite-blocklength view) [derived]

Normal approximation (Gaussian input, complex AWGN; form and accuracy discussion in Coskun et al. 2019, #1):
log2 M ~ n C - sqrt(n V) Q^-1(eps) + 0.5 log2 n, C = log2(1+s), V = s(s+2)/(1+s)^2 (log2 e)^2, n = 1024 symbols,
log2 M = A (data bits). QPSK-constrained capacity is within ~0.02 b/symbol of Gaussian below 0 dB (adds ~0.05-0.1 dB at
2/5, 1/2). Measured blind / genie SNRs from `08_parameters_results.md` 8.2a.

| Point | Target BLER | NA (approx.) | Genie = CA-SCL-8 at true CFO / phase | Blind | Genie - NA | Blind - genie |
|---|---|---|---|---|---|---|
| 1/10 (A = 205) | 1e-4 | ~ -6.5 dB | -5.19 dB | -4.9 dB | **~1.3 dB** | 0.29 dB |
| 0.15 (A = 307) | 1e-3 | ~ -5.1 dB | -3.91 dB | -3.60 dB | **~1.2 dB** | 0.31 dB |
| 2/5 (A = 819) | 1e-3 | ~ -0.45 dB | 0.64 dB | 0.61 dB | **~1.1 dB** | -0.03 dB |
| 1/2 (A = 1024) | 1e-3 | ~ 0.8 dB | 1.90 dB | 1.79 dB | **~1.1 dB** | -0.11 dB |

- **Cost of not knowing CFO / phase** [derived, union-bound style]: the receiver effectively tests M_h ~ 61 resolvable
  frequencies (0.06 x 1024) x a few phases ~ 2^8 ... 2^10 hypotheses: 8-10 bits / 1024 symbols = 0.008-0.010 b/symbol,
  i.e. ~0.1 dB at 1/10, 0.15 and ~0.06 dB at 2/5, 1/2. No source with an exact unknown-CFO finite-length bound was
  found (Liva 2017 #12, Ostman 2019 #13, Lancho 2021 #14 treat unknown gain / block fading / packet detection).
- So the measured blind-vs-genie gap at the low rates (~0.3 dB) is ~0.2 dB above the fundamental cost: that is the
  search's share (Stage-2 misses). At 2/5, 1/2 the search costs nothing (blind already beats the one-decode genie).
- **The decoder (CA-SCL-8 with this code) is ~1.1-1.3 dB from the NA at every rate.** That is 4-6x more than the
  search gap. Sources agree it is the list size, not the code family: at n = 512 polar codes need L ~ 1024 to approach
  the bounds (#1); (2048, 1024) + CRC-24 with a very large adaptive list reaches FER 1e-3 at Eb/N0 1.1 dB, "about
  0.2 dB from the limit" (#2) - our genie at 1/2 is at 1.9 dB for the same FER (Eb/N0 = Es/N0 there), i.e. ~0.8 dB of
  list headroom on the same length and rate [derived].
- **BLER share that each fix can reach** [derived from 8.2]: genie / blind BLER = 2.9e-5 / 2.1e-4 = 14 % at 1/10 -5 dB;
  2.0e-3 / 4.2e-3 = 48 % at 0.15 -4 dB; 3.2e-3 / 2.3e-3 > 100 % at 2/5 0.5 dB; 4.7e-4 / 1.4e-4 > 100 % at 1/2 2 dB.
  A stronger decoder attacks the decoder-limited part (most at 0.15, 2/5, 1/2); a better search can at most bring blind
  to the genie (x7 at 1/10 -5, x2.1 at 0.15 -4, nothing at 2/5, 1/2).

---

## 1. Ranked adoption candidates (gain x confidence)

### P1. List escalation on the final candidate(s): adaptive CA-SCL, L = 8 -> 32 (-> 128) only when everything else failed
- Sources: Li, Shen, Tse 2012 (#2, abstract: increase L until a path passes the CRC; (2048, 1024) + CRC-24, FER 1e-3 at
  1.1 dB, ~0.2 dB from the limit, average complexity "essentially does not increase with the list size"); Giard et al.
  2017 (#3, full: (512, 80) incl. CRC-16, effective R = 1/8 - our regime - SC -> CA-SCL-8 gains 1.0 dB, -> CA-SCL-32
  1.35 dB at FER 1e-4, i.e. **+0.35 dB for L 8 -> 32**); PolarBear (#4, snippet: (1024, 869) + CRC-8, L 4 -> 32 +0.31 dB);
  Coskun et al. 2019 (#1: L = 1024 needed at n = 512 to reach the bounds).
- Idea: after the normal Stage 3 decodes, retry and rescue have all failed (the packet is about to be declared lost),
  decode the best 1-2 refined hypotheses (by full list-1 metric; at 2/5, 1/2 the joint-list survivors) once more with
  L = 32; if that fails, optionally L = 128 on the best one. Accept with CRC + rho as now.
- Expected BLER [derived; list gain 0.2-0.35 dB taken from #3 / #4 at shorter N, applied to the decoder-limited share,
  waterfall slopes from 8.2]: 2/5 0.5 dB (x39 per 0.5 dB): **x3-6 lower**; 1/2 2 dB (x150 per 0.5 dB): **x4-10 lower**;
  0.15 -4 dB (x6 per 0.5 dB, ~50 % decoder-limited): **x1.3-1.8 lower**; 1/10 -5 dB (14 % decoder-limited): <= x1.15.
  Confidence medium: the list gain at N = 2048 and low rate was not found for exactly our code; the 0.35 dB is for
  N = 512, R = 1/8.
- Cost [derived from the 07 model]: one CA-SCL-32 decode = 4 x 186k = ~0.75 M MACs total; on 32 cores with one path per
  core the critical path is ~23k MACs + the 64 -> 32 bitonic sort (21 stages x K: 4.6k at 1/10, 6.8k at 0.15, 21.8k at
  1/2) - about the same per core as one CA-SCL-8 decode. Triggered only on would-be failures: at 0.15 -4 dB the search
  is ~7 M per packet, so +0.75 M on ~1-3 % of packets is < +0.5 % total; per core ~ +1 decode round on those packets.
  L = 128 = 16x an L = 8 decode in total MACs, 4 paths per core: use only on the single best hypothesis.
- Risks: more wrong CRC passes per escalated decode (32 paths x 2 PiCode patterns x 2^-16 ~ 1e-3; King et al. 2023,
  #5: undetected errors grow once L approaches 2^m); rho must hold them; RHO_N calibration for L = 32 needed.
  Escalating at a WRONG cell (Stage-2 miss) only adds false-pass chances: escalate only the best-metric hypothesis.
- DEAD_ENDS: "adaptive list size (H) - not run: upside <= the non-Stage-2 failures (2 of 16 at 1/10 -5 dB)". New reason:
  that estimate is for 1/10 only; at 0.15 -4 dB ~50 % and at 2/5, 1/2 ~100 % of the errors are decoder-limited
  (genie BLER >= blind BLER x 0.48). Reopen for 0.15, 2/5, 1/2, keep 1/10 as control.
- Test: first the zero-risk ceiling (T1 below). Then flag e.g. `lesc = (32, 2)` (L, number of hypotheses) and
  `lesc128`; 64k paired at 2/5 0.5 dB, 1/2 2 dB, 0.15 -4 dB, 1/10 -5 dB; go to 400k + 30k noise-only if >= 10 fixed and
  undetected <= base + 1. Report BLER, undetected, total and per-core MACs.

### T1 (diagnostic for P1 and for any search work). Genie list ladder + Stage-2 / genie overlap
- Genie decode at the true CFO / phase with L = 8, 32, 128 (and the joint 16 -> 64-path list at 2/5, 1/2) on 64k
  packets at the four points: measures the real list gain at our N, rate, CRC-16 and rho. Cheap (one decode per arm).
- On the same seeds as existing blind runs: for each blind error, does the L = 8 genie also fail? A Stage-2 miss whose
  genie also fails is an undecodable packet, not a search failure. This tells how much of the 117 / 199 "true region not
  among candidates" (t-dump15a) is truly recoverable by search changes (F3 etc.) [derived: ~half at 0.15 -4 dB].
- At 1/10 -5 dB the full-length metric ranks the true cell <= 4 in 99.8 % (lit_checks), yet blind is 7x the genie: log at
  which checkpoint (coarse start at 1/2, z-cut at 3/4, batch rejection z < 5) the true cell is dropped. The tau / k_min
  sweep allowed 0.1 % true-cell loss, which is 5x the 1/10 -5 dB BLER: a looser rule ONLY at <= -4.5 dB (tau = -1 or
  k_min = 32) is not in DEAD_ENDS ("harder z cut" is) and may be the cheapest fix at 1/10.

### P2. More than one code-aided phase-smoothing pass (`pns` iterations), reliability-weighted symbols - phase noise only
- Sources: Colavolpe, Barbieri, Caire 2005 (survey 2) and the turbo-synchronization line (Herzet et al. 2007, survey 1):
  phase estimation improves over decoder iterations; Ferro, Schiavone, Liva, Magarini, ISTC 2025 (#6, snippet):
  pilot-free blockwise-noncoherent decoder in three steps (blind decode -> code-aided phase estimate -> re-decode),
  "within a few tenths of a dB" of finite-length achievability bounds, ~0.5 dB better than pilot-aided; Ninacs et al.
  2019 (#7, abstract): joint factor-graph phase-noise detection + short NB-LDPC within 1.2 dB of finite-length bounds.
- Our measured pns (one pass from a failed decode's list): BLER -18 % (2/5), -23 % (1/2), -10 % (0.15) at 1e-4; fixes
  4-7 % of calls, never breaks a packet, MACs per core go down. The literature's gain comes from iterating (each re-decode
  gives better symbols). Two cheap changes: (a) 2-3 passes (smooth -> decode -> smooth), (b) weight z_k by the symbol
  reliability (|tanh(LLR/2)| of the two code bits after decoding, or 0 for symbols whose list paths disagree) so wrong
  decisions do not drag the phase.
- Expected [derived, low confidence]: under 1e-4 at 2/5, 1/2: -30 ... -50 % BLER instead of -18 ... -23 %; at 0.15,
  1/10: -15 ... -25 %. In AWGN: no change (as pns).
- Cost: one decode per extra pass on failing packets only (pns is already cheaper than base under phase noise; at 2/5
  AWGN pns is +7 % per core: keep the pass count adaptive, stop when rho rises by < x%).
- DEAD_ENDS: dd is dead in AWGN; pns is the reopened version for phase noise (measured safe). Not a repeat.
- Test: flags `pns_it = 2, 3`, `pns_w = rel`; pn 1e-4 and 3e-4 at the pns1 / pns3 points (64k paired against pns
  with 1 pass), AWGN 2/5 0.5 dB as the kill check. Combined arm: pns + P1 (L = 32 after the last pns pass).

### P3. List-marginalised ranking metric (F3) - already queued; expect little
- Source: Yuan, Coskun, Kramer 2021 (survey 1 / 2). Being tested in `expected_f3f5.md`; predicted P(rank <= 4) +0.002 ...
  +0.005 at 0.15 -4 dB (below the 0.005 gate). By section 0, search fixes can win at most x2.1 at 0.15 -4 dB, and T1
  will say how much of that is reachable. Nothing new to add from this survey; keep the gate.

### P4. SCL-Flip on the final candidate as a cheaper alternative to P1 (only if P1's per-core cost is a problem)
- Sources: Pillet, Sagitov, Giard 2026 (#8, abstract): partitioned SCL-Flip with L = 2, 3 flips per trial, T_max = 300,
  within 0.05 dB of SCL-64, up to 0.1 dB better than SCLF, -77 % complexity vs SCLF at FER 1e-2; Lv et al. (#9, full:
  PC(512, 256+16), adaptive SCL-Flip, T_max = 78, -80.85 % complexity vs SCL-Flip L = 32 at FER 1e-3).
- Why ranked below P1: flips are serial trials (up to 78-300 decodes on a failing packet) - at our waterfall points
  the failing packets are exactly the ones that would use all trials; L = 32 has the same per-core critical path as
  L = 8 on 32 cores and needs no flip-metric tuning. Use only if T1 shows that L = 32 helps but costs too much.
- Test: only after P1; flag `sclf = (L, T)` on the same points.

### Not recommended (read and rejected for this receiver)
- **PAC codes / new frozen-set design** (Rowshan, Burg, Viterbo 2021, #10; Gu, Rowshan, Yuan 2025, #11): PAC gains are at
  short lengths; at longer lengths PAC under list decoding no longer beats CRC-aided polar (search snippet of #10;
  #11 gains 0.12 dB at "medium length" with CRC-masked frozen bits). A code change also needs the pilot references and
  NN rerun. No "sync-friendly" frozen-set design for CFO metric separation was found in any search. Not at N = 2048.
- **OSD / GRAND**: OSD cost ~ sum_{i<=t} C(K, i) re-encodings plus Gaussian elimination O(n min(K, n-K)^2)
  (#15, snippet); with K = 221 ... 1040 order 2 is 2.4e4 ... 5.4e5 re-encodings [derived], and low-rate codes need high
  orders (#15). GRAND is for high-rate codes (small n - K; #16 snippet); ours has n - K >= 1000. Not applicable.
- **Soft combining of LLRs across neighbouring CFO hypotheses**: after refinement the residual is 0.57-0.78 STEP rms at
  the low rates (expected_ref D0) = 4-6e-5 cycles/symbol, an edge drift of ~0.15-0.2 rad: coherent loss
  -20 log10(sin a / a) ~ 0.02-0.05 dB [derived]. Combining hypotheses can gain at most that, and averaging LLRs of an
  incoherent neighbour lowers their reliability. Our joint list over hypotheses (2/5, 1/2) already does the useful part.
- **Phase-error-aware soft metrics** (Krishnan et al. 2013, #17, abstract): at our SNRs with a residual phase of
  0.1-0.3 rad the optimal QPSK metric is, to first order, the Euclidean one scaled by e^{-sigma^2/2} plus a small
  extra noise term (<= 0.09 Es vs N0 = 1.1-3.2 Es) [derived]; Fast-SSC min-sum decoding is invariant to an LLR scale.
  No gain expected.
- **Larger CRC**: CRC-24 would cut wrong passes under large lists (#5) but costs 8 bits of rate (~0.04-0.15 dB at our
  A [derived]); rho already does that job. Only if P1's undetected count is a problem.

---

## 2. Per-source table (new sources of this survey; survey 1 / 2 sources only when a new point was read)

| # | Title (authors), year | Link | Read | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|
| 1 | Efficient Error-Correcting Codes in the Short Blocklength Regime (Coskun, Durisi, Jerkovits, Liva, Ryan, Stein, Steiner), PhyCom 2019 | [ar5iv 1812.08562](https://ar5iv.labs.arxiv.org/html/1812.08562) | full (first 100k of 104k chars) | high: decoder headroom, NA | survey of short codes vs NA / RCU / MC bounds | n = 128 (k = 64), n = 512, 1024; rate 1/2; AWGN | polar + CRC-7, L = 32 close to RCU at (128, 71); (512, 256) + CRC-16 at L = 32 only marginally better than LDPC / turbo, L = 1024 needed to approach bounds; NA loses accuracy at small rate / error |
| 2 | An Adaptive SC List Decoder for Polar Codes with CRC (Li, Shen, Tse), IEEE CL 2012 | [1208.3091](https://arxiv.org/abs/1208.3091) | abstract | high: P1 | list size doubled until a CRC pass | (2048, 1024) + CRC-24 | FER 1e-3 at Eb/N0 1.1 dB, ~0.2 dB from the limit; average complexity ~ not growing with L_max |
| 3 | Blind Detection of Polar Codes (Giard, Balatsoukas-Stimming, Burg), SiPS 2017 (re-read) | [ar5iv 1705.02111](https://ar5iv.labs.arxiv.org/html/1705.02111) | full | high: list gain at our rate | SC vs CA-SCL-8 vs CA-SCL-32 | (512, 80) incl. CRC-16, effective R = 1/8, BPSK AWGN | at FER 1e-4: SC -> L = 8: 1.0 dB, SC -> L = 32: 1.35 dB |
| 4 | PolarBear: a 28-nm FD-SOI ASIC for decoding of polar codes (Giard et al.), JETCAS 2017 | [1708.09603](https://arxiv.org/abs/1708.09603) | abstract + snippet | medium | SC / SCF / SCL ASIC | (1024, 869) + CRC-8 (snippet) | L 4 -> 32: +0.31 dB to FER ~1e-3 (snippet only); 306.8 Mb/s at 721 MHz (abstract) |
| 5 | Design, Performance, and Complexity of CRC-Aided List Decoding ... Short Messages (King, Yao, Ryan, Wesel), 2023 (survey 1) | [2302.07513](https://ar5iv.labs.arxiv.org/html/2302.07513) | full (survey 1) | medium: undetected risk of P1 | CRC-polar / TBCC list decoding | (512, 43), CRC-11 / 24, L <= 1024 | CRC-24: 0 undetected up to L = 1024; CRC-11: > 80 % of failures undetected at high SNR; L ~ 2^m |
| 6 | A Decoding Algorithm for Terminated Convolutional Codes over the Blockwise Noncoherent Channel (Ferro, Schiavone, Liva, Magarini), ISTC 2025 | [Polito record](https://iris.polito.it/handle/11583/3002166) | snippet (PDF 403) | medium: supports P2 | 3-step Viterbi: blind decode, code-aided phase estimate, re-decode; outer CRC | zero-tail CC, BPSK / QPSK, random constant phase, no pilots | ~0.5 dB over pilot-aided; within a few tenths of a dB of finite-length achievability bounds |
| 7 | Short Non-Binary LDPC Codes for Phase Noise Channels (Ninacs, Matuz, Liva, Colavolpe), T-COM 2019 | [1908.02816](https://arxiv.org/abs/1908.02816) | abstract | medium: phase-noise benchmark | joint factor graph: non-coherent multi-symbol detection + NB-LDPC | m-ary DPSK, AWGN + Wiener | within 1.2 dB of finite-length bounds down to CER 1e-3 |
| 8 | On Reducing Decoding Complexity of SCL-Flip Decoding of Polar Codes (Pillet, Sagitov, Giard), JSPS 2026 | [2605.08492](https://arxiv.org/abs/2605.08492) | abstract | medium: P4 | partitioned SCL-Flip, dynamic flip metric, multiple flips | L = 2, 3 flips per trial, T_max = 300 | ~0.05 dB from SCL-64; up to 0.1 dB over SCLF; -77 % complexity vs SCLF at FER 1e-2 |
| 9 | Adaptive List Decoder with Flip Operations for Polar Codes (Lv, Yin, Yang, Wang, Dai, Huan) | [ar5iv 2112.04713](https://ar5iv.labs.arxiv.org/html/2112.04713) | full (via reader) | low-medium | adaptive SCL + flips | PC(512, 256+16), CRC-16, L_max 4 / 32, T_max = 78 | -80.85 % complexity vs SCL-Flip L = 32 at FER 1e-3; FER curves overlap |
| 10 | PAC Codes: Sequential Decoding vs List Decoding (Rowshan, Burg, Viterbo), IEEE TVT 2021 | [2002.06805](https://arxiv.org/abs/2002.06805) | abstract + snippet | low | PAC list vs Fano / stack decoding | short PAC codes | sequential: -50 ... -80 % time for 0.05-0.3 dB loss at FER 1e-3; snippet: PAC list "cannot compete" with CA-polar as length grows |
| 11 | PAC Codes Meet CRC-Polar Codes (Gu, Rowshan, Yuan), 2025 | [2501.18080](https://arxiv.org/abs/2501.18080) | abstract + snippet | low | shifted rate profile PAC; CRC parity in frozen positions | short and medium lengths (snippet: N = 64-512) | up to 0.5 dB (short PS-PAC); 0.12 dB at medium length |
| 12 | Short Codes with Mismatched Channel State Information: A Case Study (Liva, Durisi, Chiani, Ullah, Liew), SPAWC 2017 | [1705.05528](https://arxiv.org/abs/1705.05528) | abstract | low-medium: theory frame | mismatched-decoding bounds, preamble vs redundancy | AWGN, unknown constant gain, short LDPC | bounds predict the optimal preamble length; no numbers in abstract |
| 13 | Short Packets over Block-Memoryless Fading Channels: Pilot-Assisted or Noncoherent Transmission? (Ostman, Durisi, Strom, Coskun, Liva), T-COM 2019 | [Chalmers record](https://research.chalmers.se/publication/508866) | snippet (PDF binary) | low-medium | noncoherent vs PAT finite-length bounds | Rician / Rayleigh block fading | Rayleigh, n = 168, rate 0.48, block 8: PAT needs +1.2 dB at 1e-3 vs noncoherent |
| 14 | On Joint Detection and Decoding in Short-Packet Communications (Lancho, Ostman, Durisi), Globecom 2021 | [2109.13669](https://arxiv.org/abs/2109.13669) | abstract | low-medium: detection-limited regime | bounds with false-alarm + misdetection + error | bi-AWGN | identifies blocklengths where detection is the bottleneck (no numbers in abstract) |
| 15 | Pre-configured Error Pattern OSD for CRC-Polar Codes, 2023 (+ OSD complexity statements) | [2309.11836](https://arxiv.org/pdf/2309.11836) | snippet | none for us (rejects OSD) | OSD variants | high-rate CRC-polar | Gaussian elimination O(n min(k, n-k)^2); OSD cost sum C(k, i); low-rate codes need high order |
| 16 | Ordered Reliability Bits GRAND (Duffy, An, Medard), 2022 | [2202.13951](https://arxiv.org/pdf/2202.13951) | snippet | none for us | noise-guessing ML decoder | short, high-rate codes | better than CA-SCL for short high-rate CA-polar (snippet) |
| 17 | Soft Metrics and their Performance Analysis for Optimal Data Detection in the Presence of Strong Oscillator Phase Noise (Krishnan, Khanzadi, Eriksson, Svensson), T-COM 2013 | [1310.1638](https://arxiv.org/abs/1310.1638) | abstract | low | ML detector after a tracker, Tikhonov / Gaussian phase-error pdf | arbitrary constellations, strong phase noise | no numbers in abstract |
| 18 | An Information-Theoretic Perspective on SCL Decoding and Polar Code Design (Coskun, Pfister), 2021 / 2022 | [2103.16680](https://arxiv.org/abs/2103.16680) | abstract + snippet | low | list size needed for ML; RM-polar designs | N = 128, 512, L 8-1024 | snippet: within 0.75 dB of RCU to BLER 1e-6 at L = 32, ~0.2 dB over 5G + CRC-11 |

Not found or not readable: a finite-blocklength bound with an unknown carrier FREQUENCY offset (only gain / phase / block
fading / delay); list-size curves for N = 2048 at R ~ 0.1-0.15 with CRC-16 (closest: #3 at N = 512, R = 1/8); any
"sync-friendly" polar frozen-set construction; the full texts of Polyanskiy-Poor-Verdu 2010 (PDF binary; the normal
approximation is taken as stated in #1), Ostman 2019, Ferro 2025, PolarBear.

---

## 3. Per-component verdict (BLER only)

| Component | Ours | State of the art found | Verdict |
|---|---|---|---|
| Hypothesis ranking (Stage 2) | list-1 Fast-SSC metric, robust z, checkpoints | same family; list-marginalised metric (F3) | **use**; F3 queued. Headroom bounded by blind - genie (x7 at 1/10 -5, x2.1 at 0.15 -4, none at 2/5, 1/2). Diagnose where 1/10 loses the cell (T1) |
| Decoding at the right CFO | CA-SCL-8, joint 16-path list (2/5, 1/2), code-aided retry | adaptive / large-list CA-SCL (L 32-1024), SCL-Flip | **behind**: P1 (largest headroom: ~1.1-1.3 dB to NA, 0.2-0.35 dB practical with L = 32) |
| Fine CFO / phase | refinement grid, DD retry | code-aided EM | **use**; residual costs ~0.02-0.05 dB [derived]; no BLER lever |
| Phase noise | pns (1 pass) | iterative code-aided smoothing, factor-graph detection | **slightly behind**: P2 (iterate, weight by reliability) |
| Combining across hypotheses | joint list (2/5, 1/2) | list paths over phase hypotheses (Geiselhart 2023) | **use**; LLR soft combining not useful [derived] |
| Code | CRC-polar N = 2048, CRC-16, interleaver | PAC, RM-polar, AED-designed polar | **not applicable** now (gains at short N or need a code change) |
| Strong ML decoders | - | OSD, GRAND | **not applicable** (K 221-1040, n - K >= 1000) |

---

## Reference entries

### Coskun, M. C., Durisi, G., Jerkovits, T., Liva, G., Ryan, W., Stein, B., Steiner, F., "Efficient error-correcting codes in the short blocklength regime," Physical Communication, 2019 (arXiv 1812.08562)
- Link: https://ar5iv.labs.arxiv.org/html/1812.08562   - Type: paper   - Read depth: full (first 100k of 104k characters)
## What it does
Survey of short codes against the normal approximation, RCU and meta-converse bounds (n = 128, 512, 1024, rate 1/2,
AWGN). Polar + CRC with L = 32 is close to RCU at n = 128; at n = 512 with CRC-16, L = 32 is only marginally better than
LDPC / turbo and L = 1024 is needed to approach the bounds. Notes that the NA loses accuracy at small rate / error.
## What we took / could take
Basis for the headroom table (section 0) and for P1 (the gap is the list size, not the search).
## Used in
-

### Li, B., Shen, H., Tse, D., "An adaptive successive cancellation list decoder for polar codes with cyclic redundancy check," IEEE Communications Letters, 2012 (arXiv 1208.3091)
- Link: https://arxiv.org/abs/1208.3091   - Type: paper   - Read depth: abstract
## What it does
Doubles the list size until a path passes the CRC; (2048, 1024) + CRC-24 reaches FER 1e-3 at Eb/N0 1.1 dB, about 0.2 dB
from the limit, with average complexity that hardly grows with the maximum list size.
## What we took / could take
P1: list escalation (L = 8 -> 32 -> 128) only on the final candidate of a packet that would otherwise be lost.
## Used in
-

### Giard, P., Balatsoukas-Stimming, A., Burg, A., "Blind detection of polar codes," IEEE SiPS 2017 (arXiv 1705.02111)
- Link: https://ar5iv.labs.arxiv.org/html/1705.02111   - Type: paper   - Read depth: full
## What it does
Frozen-bit detection metric for blind detection (survey 1). New point read here: for (512, 80) incl. CRC-16 (effective
R = 1/8), at FER 1e-4 SC -> CA-SCL-8 gains 1.0 dB and SC -> CA-SCL-32 gains 1.35 dB.
## What we took / could take
The +0.35 dB (L 8 -> 32) at a rate like ours is the main input to the P1 BLER prediction. (Frozen-only ranking: dead end.)
## Used in
-

### Giard, P., et al., "PolarBear: A 28-nm FD-SOI ASIC for decoding of polar codes," IEEE JETCAS 7, 2017 (arXiv 1708.09603)
- Link: https://arxiv.org/abs/1708.09603   - Type: paper   - Read depth: abstract + search snippet
## What it does
Silicon SC / SC-Flip / SCL decoders (306.8 Mb/s at 721 MHz). Snippet: (1024, 869) + CRC-8, L = 32 gains 0.31 dB over
L = 4 down to FER ~1e-3.
## What we took / could take
Second data point for the list-size gain in P1 (snippet only; not verified in the text).
## Used in
-

### King, J., Yao, H., Ryan, W., Wesel, R., "Design, performance, and complexity of CRC-aided list decoding of convolutional and polar codes for short messages," 2023 (arXiv 2302.07513)
- Link: https://ar5iv.labs.arxiv.org/html/2302.07513   - Type: paper   - Read depth: full (in survey 1)
## What it does
Undetected errors vs list size and CRC length: CRC-24 no undetected errors up to L = 1024; CRC-11 > 80 % of failures
undetected at high SNR; list size ~ 2^m as a design rule.
## What we took / could take
Risk bound for P1: with CRC-16 and L = 32 the CRC alone is not enough; keep rho and recalibrate RHO_N for L = 32.
## Used in
-

### Ferro, Schiavone, Liva, Magarini, "A decoding algorithm for terminated convolutional codes over the blockwise noncoherent channel," ISTC 2025
- Link: https://iris.polito.it/handle/11583/3002166   - Type: paper   - Read depth: snippet (PDF 403)
## What it does
Pilot-free decoder for a random constant phase: blind Viterbi decode, code-aided phase estimate, re-decode (3 steps),
outer CRC; ~0.5 dB better than pilot-aided, within a few tenths of a dB of finite-length achievability bounds (BPSK, QPSK).
## What we took / could take
Supports P2 (iterate decode <-> phase estimate) and our blind-vs-pilot result; same structure as pns.
## Used in
-

### Ninacs, T., Matuz, B., Liva, G., Colavolpe, G., "Short non-binary low-density parity-check codes for phase noise channels," IEEE Trans. Commun., 2019 (arXiv 1908.02816)
- Link: https://arxiv.org/abs/1908.02816   - Type: paper   - Read depth: abstract
## What it does
m-ary DPSK + NB-LDPC over AWGN with Wiener phase noise, non-coherent multi-symbol detection on a joint factor graph;
within 1.2 dB of finite-length bounds down to CER 1e-3.
## What we took / could take
Benchmark size for pilot-free phase-noise receivers (P2). Not used directly: different code and modulation.
## Used in
-

### Pillet, C., Sagitov, I., Giard, P., "On reducing decoding complexity of successive-cancellation list flip decoding of polar codes," J. Signal Processing Systems, 2026 (arXiv 2605.08492)
- Link: https://arxiv.org/abs/2605.08492   - Type: paper   - Read depth: abstract
## What it does
Partitioned SCL-Flip with early termination / restarts, dynamic flip metric, multiple flips: L = 2, 3 flips per trial,
T_max = 300; ~0.05 dB from SCL-64, up to 0.1 dB over SCLF, -77 % complexity vs SCLF at FER 1e-2.
## What we took / could take
P4: fallback to P1 if list escalation is too costly per core. Serial trials make it a poor fit for our critical path.
## Used in
-

### Lv, Y., Yin, H., Yang, Z., Wang, Y., Dai, J., Huan, J., "Adaptive list decoder with flip operations for polar codes" (arXiv 2112.04713)
- Link: https://ar5iv.labs.arxiv.org/html/2112.04713   - Type: paper   - Read depth: full (via reader)
## What it does
Adaptive SCL with flips; PC(512, 256+16), CRC-16; T_max = 78; -80.85 % complexity vs SCL-Flip (L = 32) at FER 1e-3 with
overlapping FER curves.
## What we took / could take
P4 context only.
## Used in
-

### Rowshan, M., Burg, A., Viterbo, E., "Polarization-adjusted convolutional (PAC) codes: sequential decoding vs list decoding," IEEE Trans. Veh. Technol. 70(2), 2021 (arXiv 2002.06805)
- Link: https://arxiv.org/abs/2002.06805   - Type: paper   - Read depth: abstract + snippet
## What it does
List and Fano / stack decoding for PAC codes; sequential complexity -50 ... -80 % for 0.05-0.3 dB loss at FER 1e-3.
Snippet: as length grows, PAC under list decoding cannot compete with CRC-aided polar.
## What we took / could take
Not used: PAC's advantage is at short lengths; at N = 2048 a larger CA-SCL list is the better lever.
## Used in
-

### Gu, X., Rowshan, M., Yuan, J., "PAC codes meet CRC-polar codes," 2025 (arXiv 2501.18080)
- Link: https://arxiv.org/abs/2501.18080   - Type: paper   - Read depth: abstract + snippet
## What it does
Shifted rate-profile PAC and CRC-derived parity in frozen positions; up to 0.5 dB at short length, 0.12 dB at medium
length.
## What we took / could take
Not used: needs a code change for ~0.1 dB at our length.
## Used in
-

### Liva, G., Durisi, G., Chiani, M., Ullah, S. S., Liew, S. C., "Short codes with mismatched channel state information: a case study," SPAWC 2017 (arXiv 1705.05528)
- Link: https://arxiv.org/abs/1705.05528   - Type: paper   - Read depth: abstract
## What it does
AWGN with an unknown constant gain; mismatched-decoding achievability / converse bounds for preamble + code; predicts the
optimal preamble length vs redundancy (short LDPC).
## What we took / could take
Frame for the "cost of the unknown parameter" estimate in section 0; no CFO version exists.
## Used in
-

### Ostman, J., Durisi, G., Strom, E. G., Coskun, M. C., Liva, G., "Short packets over block-memoryless fading channels: pilot-assisted or noncoherent transmission?" IEEE Trans. Commun., 2019
- Link: https://research.chalmers.se/publication/508866   - Type: paper   - Read depth: snippet (PDF not parseable)
## What it does
Finite-length bounds, noncoherent vs pilot-assisted; Rayleigh, n = 168, rate 0.48, block 8: PAT needs +1.2 dB at 1e-3.
## What we took / could take
Supports the blind-vs-pilot comparison (8.2a); not used numerically (fading, different n).
## Used in
-

### Lancho, A., Ostman, J., Durisi, G., "On joint detection and decoding in short-packet communications," Globecom 2021 (arXiv 2109.13669)
- Link: https://arxiv.org/abs/2109.13669   - Type: paper   - Read depth: abstract
## What it does
Bounds on the coding rate with false-alarm, misdetection and error probabilities; joint detection-decoding vs preamble;
bi-AWGN.
## What we took / could take
Frame for the open item "noise-only false alarms / packet detection"; not used for BLER.
## Used in
-

### "Pre-configured error pattern ordered statistics decoding for CRC-polar codes," 2023 (arXiv 2309.11836), and OSD complexity statements in the same search
- Link: https://arxiv.org/pdf/2309.11836   - Type: paper   - Read depth: snippet
## What it does
OSD variant for high-rate CRC-polar; preprocessing O(n min(k, n-k)^2); OSD cost ~ sum C(k, i); low-rate codes need high
orders.
## What we took / could take
Not used: K = 221-1040 makes OSD far too costly.
## Used in
-

### Duffy, K. R., An, W., Medard, M., "Ordered reliability bits guessing random additive noise decoding," 2022 (arXiv 2202.13951)
- Link: https://arxiv.org/pdf/2202.13951   - Type: paper   - Read depth: snippet
## What it does
Soft GRAND for short high-rate codes (BCH, CA-polar, RLC), better than CA-SCL there.
## What we took / could take
Not used: our codes have n - K >= 1000.
## Used in
-

### Krishnan, R., Khanzadi, M. R., Eriksson, T., Svensson, T., "Soft metrics and their performance analysis for optimal data detection in the presence of strong oscillator phase noise," IEEE Trans. Commun. 61(6), 2013 (arXiv 1310.1638)
- Link: https://arxiv.org/abs/1310.1638   - Type: paper   - Read depth: abstract
## What it does
ML detection after a phase tracker using the residual phase-error pdf (Gaussian / Tikhonov), "soft metrics".
## What we took / could take
Not used: at our SNRs and 0.1-0.3 rad residual it reduces to an LLR scale, which min-sum Fast-SSC ignores [derived].
## Used in
-

### Coskun, M. C., Pfister, H. D., "An information-theoretic perspective on successive cancellation list decoding and polar code design," 2021 / 2022 (arXiv 2103.16680)
- Link: https://arxiv.org/abs/2103.16680   - Type: paper   - Read depth: abstract + snippet
## What it does
Links the list size needed for ML-like SCL to information-theoretic quantities; RM-polar designs for N = 128, 512, L 8-1024
(snippet: within 0.75 dB of RCU to 1e-6 at L = 32, ~0.2 dB better than 5G + CRC-11).
## What we took / could take
Supports "list size is the lever"; code redesign not pursued.
## Used in
-

## Sources
- https://ar5iv.labs.arxiv.org/html/1812.08562
- https://arxiv.org/abs/1208.3091
- https://ar5iv.labs.arxiv.org/html/1705.02111
- https://arxiv.org/abs/1708.09603
- https://ar5iv.labs.arxiv.org/html/2302.07513
- https://iris.polito.it/handle/11583/3002166
- https://arxiv.org/abs/1908.02816
- https://arxiv.org/abs/2605.08492
- https://ar5iv.labs.arxiv.org/html/2112.04713
- https://arxiv.org/abs/2002.06805
- https://arxiv.org/abs/2501.18080
- https://arxiv.org/abs/1705.05528
- https://research.chalmers.se/publication/508866
- https://arxiv.org/abs/2109.13669
- https://arxiv.org/pdf/2309.11836
- https://arxiv.org/pdf/2202.13951
- https://arxiv.org/abs/1310.1638
- https://arxiv.org/abs/2103.16680
