# Literature survey 3: methods to ADOPT that cut MACs (per core and total) at the same BLER (2026-11-15)

Scope (main-session request): methods from papers, patents and other fields (5G PDCCH blind detection, adaptive /
early-terminated SCL, Fast-SSC variants, sequential search and bandits, GNSS acquisition, FFT pruning) that reduce the
cost of our blind receiver: N = 2048 polar + CRC-16, 1024 QPSK symbols, R = 1/10, 0.15, 2/5, 1/2, |f| <= 0.03.

Read before searching (not repeated): `DEAD_ENDS.md`, `03_path_metric.md`, `04_search.md`, `05_decoding.md`,
`02_fast_path.md`, `07_complexity.md`, `lit_blind_cfo.md` (survey 1), `lit_polar_sync.md` (survey 2), the cost
accounting in `small_rx.py` (`_par`, `_dec_cost`, `dp8`, the retry block around line 1048, `score`, `refine_joint`) and
`blind_vp.MAC` / `metric_macs`.

Reading depth: "full" = full text (HTML); "abstract"; "snippet" = only search-result text or a patent page's first
part. **[derived]** = my own arithmetic from our cost model, not from a source. No simulation was run.

**Unit costs used below [read from the code].** m_met (one full list-1 Fast-SSC metric pass, `metric_macs`) is
about 20.3k MACs at R = 1/10 (2 m s = 14.6k at s = 0.36, report_cmp.md), about 22k at 0.15, about 27k at 2/5
(README). One cell de-rotation + phase = 4·1024 + 4 = 4.1k. One CA-SCL-8 decode on the critical path (`dp8`) =
180,224 / 8 + K·10 (bitonic sort of 16) = 24.7k (1/10, K = 221), 25.8k (0.15), about 30k (2/5) and 33k (1/2); total
186k per decode. Per-core baselines (testing receiver, scheduled model, 07, 7.5b): 0.206 M (1/10 -5 dB), 0.406 M
(0.15 -4 dB), 0.234 M (2/5 0.5 dB), 0.083 M (1/2 2 dB).

**Comparability caveat.** No source does a blind CFO search with a polar code; every complexity number below comes
from PDCCH blind detection (N <= 512, about 44 candidates), from single-codeword decoders (adaptive SCL, N = 1024 /
2048 at R = 1/2 ... 0.84) or from GNSS acquisition. Their percentages are latency or throughput, not MACs per core on
32 cores. The expected savings for us are [derived] from our own cost model and are upper bounds until measured.

---

## 1. Ranked adoption candidates (expected saving x confidence)

### A1. Re-use the SC codeword that the receiver has already computed: (a) in the code-aided retry, (b) as an "SC-first" decode before CA-SCL-8 (adaptive SCL with the L = 1 stage already paid)
- **Sources.** Li, Shen, Tse (Huawei), adaptive CA-SCL, IEEE CL 2012 ([1208.3091](https://arxiv.org/abs/1208.3091),
  abstract): grow the list only while no path passes the CRC. Sarkis, Giard, Vardy, Thibeault, Gross, "Fast List
  Decoders for Polar Codes", JSAC 2016 ([ar5iv 1505.01466](https://ar5iv.labs.arxiv.org/html/1505.01466), section V
  read): Fast-SSC first, list decoder only when the CRC fails; (2048, 1723) + CRC-32, L = 32: 8.6 / 33 / 196 Mb/s at
  Eb/N0 3.5 / 4.0 / 4.5 dB vs about 4 Mb/s for the list decoder alone. Condo, Hashemi, Gross, PDCCH two-phase blind
  detection ([ar5iv 1801.01820](https://ar5iv.labs.arxiv.org/html/1801.01820), full): a cheap first phase (L1 = 2) on
  44 candidates, only 5 reach SCL-8. Ericsson US 11777533 and Sequans US 10868571 (dynamic list size; below).
- **What we do now [read from small_rx.py].** (a) The code-aided retry (05, 5.4) recomputes the SC hard codeword with
  a FULL list-1 metric pass at the failed hypothesis (`fs_.metric_cw`, line 1053), charged as sequential (`seqm`,
  `seqc`), although that hypothesis was just scored with the same full metric in Stage 3 (`score`, `fs_.metric`) or,
  on the fast path, with its left half. (b) Every candidate goes to CA-SCL-8 even when the SC decisions of its own
  scoring pass already form a CRC-valid codeword; those decisions are computed anyway (they are the partial sums of
  Fast-SSC) and are simply not kept.
- **Change.** (a) `sc_cache`: keep the SC codeword of the scored hypotheses (2048 bits each; memory only) and give it
  to `bf.code_aided` instead of a new pass. (b) `sc_first`: before CA-SCL-8 at a hypothesis whose full SC pass exists,
  run the PiCode CRC (and, if it passes, rho) on the SC codeword; accept and skip the CA-SCL-8 decode if both pass.
  On the fast path (2/5, 1/2, and 1/10, 0.15 above 0 dB) finish the chosen branch's metric from c = 1/2 to 1 on one
  core *while* CA-SCL-8 runs on 8 others (speculative, 32 cores leave room), and stop the list decode if the SC
  codeword is accepted.
- **Which cost centre.** (a) code-aided retries, 28-42 % of per-core MACs at the hardest points; (b) CA-SCL decodes,
  5-34 % of the total.
- **Expected saving [derived].**
  - (a) A retry costs per core about m_met (sequential) + dp8 = 20.3k + 24.7k at 1/10 (22k + 25.8k at 0.15, 27k + 30k
    at 2/5): the SC pass is about 45 % of it. At the points where retries are 28-42 % of per core, **-13 ... -19 % per
    core**; elsewhere proportionally less (retries are rare above the waterfall). Total MACs: -m_met per retry,
    a few %. On the fast path only the left half exists, so the saving there is 36 % of m_met.
  - (b) The pass probability of the SC codeword at the right hypothesis, P_SC, is NOT known for our points. The usual
    SC-to-CA-SCL-8 gap at N = 2048 is about 0.5-1 dB, so where CA-SCL-8 is at BLER 1e-4 ... 2e-3, SC should be at
    roughly 1e-2 ... 1e-1, i.e. P_SC ~ 0.9-0.99 [rough guess, must be measured]. With P_SC = 0.9 the accepted decode is
    skipped in 90 % of the packets: per core -dp8 per packet, total -186k per packet:

    | Point | per core now | per-core saving | total now | total saving |
    |---|---|---|---|---|
    | 1/10 -5 dB | 0.206 M | -22k (-11 %) | 4.16 M | -0.17 M (-4 %) |
    | 0.15 -4 dB | 0.406 M | -23k (-6 %) | 7.27 M | -0.17 M (-2 %, more if several candidates pass on SC) |
    | 2/5 0.5 dB | 0.234 M | -15 ... -25k (-6 ... -11 %; joint decode, P_SC lower near the waterfall) | 3.72 M | -4 % |
    | 1/2 2 dB | 0.083 M | -14k (-17 %: 0.9·33k minus the 17k SC completion, run in parallel) | 0.74 M | -0.15 M (-20 %) |
    | 2/5 >= 1.5 dB, 1/2 >= 3 dB (fast path only) | 0.072-0.074 M | -15k (-20 %) | 0.55 M | -25 ... -30 % |

  - (a) and (b) add: when SC fails, its codeword is exactly the retry input of (a).
- **BLER risk.** (a) Small: the cached codeword comes from the scoring LLRs (`score` uses `r`, the retry uses the
  pre-MF-corrected `rc`), so the Newton start differs slightly; paired test needed. (b) Very small for missed
  packets: acceptance stays CRC + rho, and a CRC-valid SC codeword is almost always the CA-SCL-8 output too. False
  passes: each SC check is ONE path with 2 CRC patterns (2·2^-16), fewer CRC trials than an 8-path list (16·2^-16);
  only check hypotheses that would be decoded anyway (the best T of a candidate, the fast-path branch).
- **DEAD_ENDS?** No. "Adaptive list size (H)" there was about larger lists to fix errors; the "verified re-decode" and
  `dd` are about new CFO / phase estimates. Neither re-uses existing SC work.
- **Test.** Step 1 (measurement only, no decision change, 20k packets per point): count, at every decoded hypothesis,
  whether its SC codeword passes PiCode CRC, passes rho, and is right; and the retry's metric_cw vs the scoring
  codeword (Hamming distance, and whether the retry outcome would differ). Points 1/10 -5, 0.15 -4, 2/5 0.5, 1/2 2,
  plus 2/5 2 dB and 1/2 4 dB. Step 2: flags `sc_cache`, `sc_first`, paired 400k at the same points; report BLER,
  undetected, total and scheduled per core. Fairness: the pilot reference receivers could adopt SC-first too; rerun
  them with it if blind adopts it.

### A2. One de-rotation per cell, shared by its phase hypotheses (as GNSS shares one carrier wipe-off per Doppler bin)
- **Sources.** GNSS parallel code-phase acquisition: carrier wipe-off once per Doppler bin, then every code-phase
  hypothesis from the same wiped-off block; Doppler shifts by whole FFT bins are applied by shifting the spectrum
  ([EPFL, modified PCS architecture](https://infoscience.epfl.ch/record/188391/files/Acquisition%20of%20modern%20GNSS%20signals%20using%20a%20modified%20parallel%20code-phase%20search%20architecture%20-%20Accepted%20version.pdf),
  snippet; [EURASIP JASP 2014 acquisition paper](https://link.springer.com/doi/10.1186/1687-6180-2014-143), snippet).
- **What we do now [read from small_rx.py `_par`, comment at line 746].** In the scheduled per-hypothesis model
  (`crit_gh`), every (cell, phase) hypothesis core pays the cell's full "join cost (phase + de-rotation)", 4.1k MACs,
  on top of its partial metric (7.3k at c = 1/2 at 1/10). So about 36 % of a first-round hypothesis's critical cost
  is de-rotation, and the cell's 4 phases each pay it.
- **Change.** De-rotate the cell once by e^{-j(2 pi f_c n + theta_c)} (1024 complex multiplies, split over the cell's
  2-4 cores: 1024-2048 MACs each, plus a short exchange); the hypotheses theta_c + q pi/2 are then a swap / sign
  change of I and Q (0 MACs) and theta_c + pi/4 + q pi/2 are (I -/+ Q) (2 adds per symbol; the 1/sqrt 2 folds into the
  LLR scale). Exact, not an approximation: same LLRs, same decisions.
- **Expected saving [derived].** About 2-3k MACs off each first-round hypothesis (of 11.4k) at R = 1/10, 0.15 with 4
  phases: about -18 ... -27 % of the first-round search passes, about **-10 ... -15 % per core** at 1/10 -5 dB and
  0.15 -4 dB (search is about 60 % of per core there), about -5 % with 2 phases (above -1 dB). Total MACs: unchanged
  if the total already charges one de-rotation per cell (it does, line 1746). 2/5, 1/2: 2 phases, the search is a
  smaller share: -2 ... -4 % per core.
- **BLER risk.** None (bit-exact).
- **DEAD_ENDS?** No; it is an accounting / scheduling change, so the main session must decide whether the standard
  cost model (parallel-cost-model note) allows sharing work between cores of the same cell. If the model already
  intends one de-rotation per cell, A2 is only a fix of the `crit_gh` accounting.
- **Test.** No BLER run needed: recompute `crit_gh` from the stored counters with the join cost split over the
  cell's phases (`join / nh` + 2·1024 for odd q) on existing part files of 1/10 -5, 0.15 -4, 0.15 -1, 2/5 0.5 dB.

### A3. Stage 2 metric on reliable frozen nodes only: skip the subtrees of unreliable frozen bits (cost AND noise)
- **Sources.** Lin, Sarkis, Yang (Qualcomm) US 10742238 B2 (frozen-bit path metric "only for reliable frozen
  positions", prune / terminate; survey 2, F5); Coherent Logix US 10536305 B2
  ([Google Patents](https://patents.google.com/patent/US10536305B2/en), first 100k chars): "later frozen bits are more
  reliable but decoded later", position chosen to balance reliability and latency, PM growth threshold match vs
  mismatch; Giard et al. 2018 ([1807.00655](https://ar5iv.arxiv.org/html/1807.00655), survey 1): a partial Fast-SSC
  detection metric after t visited nodes dismisses 40 / 44 candidates.
- **Idea for us.** The first frozen bits of the polar tree sit on the worst synthetic channels. At the right CFO their
  LLRs are almost as zero-mean as at a wrong CFO, so their penalties add the same noise to every cell and carry almost
  no CFO information [derived from polarization, to be checked]. If the left child of a node is rate-0, its partial
  sums are 0 and the right child's LLRs are g = x + y without decoding the left child at all. So the penalty of an
  unreliable rate-0 leaf can be dropped together with the f operations that feed it, saving about 3n MACs for a
  rate-0 leaf of size n under our 2n-per-node count [derived], e.g. 768 MACs for n = 256.
- **Different from the dead end.** The "frozen-only ranking" (Giard metric) dropped rate-1 / SPC penalties and kept
  all frozen ones: no cost change, same rank. A3 drops the LOW-reliability frozen leaves, saves their tree work, and
  lowers the metric variance of every cell. "Early checkpoint at 1/8" failed because the first 1/8 alone does not
  rank well; that is consistent with A3 (that part is weak), not a contradiction.
- **Expected saving [derived, unknown until counted].** If the first quarter of the tree at R = 1/10 / 0.15 is
  (nearly) all frozen and uninformative, skipping it removes about 10-20 % of the c = 1/2 partial cost, i.e. -6 ...
  -12 % of search MACs (per core and total) at 1/10, 0.15; less at 2/5, 1/2 (fewer frozen leaves). It may also lift
  P(rank <= 4) (fewer Stage 2 misses), which no cost-only change can do.
- **BLER risk.** Ranking loss if the skipped leaves do carry CFO information at -5 dB. Offline first.
- **Test.** Offline in the `lit_checks.py` rank harness (201 cells x 4 phases, 2000 packets; `metric_nodes` already
  returns per-leaf penalties in decoding order): for a reliability cut on the leaves (Bhattacharyya / DE order of the
  code at the operating SNR, or simply "skip leaves before index i0" for i0 = 64, 128, 256, 512), report P(rank 1),
  P(rank <= 4), the robust-z of the true cell at c = 1/2, and the MAC share of the kept tree. A per-leaf linear
  weight (LDA on right vs wrong cells) is the upper bound. Go online (flag, 64k paired at 1/10 -5, 0.15 -4) only if
  P(rank <= 4) does not drop by more than 0.002 and the cost share falls by >= 10 %.

### A4. Successive halving inside Stage 3 scoring (checkpoint the 15 refinement hypotheses at c = 1/2)
- **Sources.** Successive halving / best-arm identification (Karnin, Koren, Somekh 2013, survey 1 #30); GNSS
  multi-dwell / SPRT verification: a sequential test needs a shorter mean dwell than a fixed dwell (O'Mahony,
  O'Driscoll, Murphy, ICC 2009, [UCC record](https://research.ucc.ie/en/publications/performance-of-sequential-probability-ratio-test-for-gps-acquisit/),
  abstract); PDCCH two-phase pruning (Condo 2018, Giard 2018).
- **Idea.** Below -1 dB a candidate is refined with 5 CFO offsets x 3 phase sub-offsets = 15 FULL list-1 passes
  (24.3k each, 365k per candidate). Score all 15 to c = 1/2 (36 % of m_met), keep the best 4, finish those to c = 1,
  then take the best T = 2 as now.
- **Expected saving [derived].** Scoring per candidate 15 x 24.3k = 365k -> 15 x (4.1k + 7.3k) + 4 x 13k = 223k:
  -39 % of refinement scoring = **-3 ... -7 % total** at 1/10 -5 dB and 0.15 -4 dB (refinement 7-19 % of total);
  per core about 0 (the 15 scores already run in one parallel pass). Only worth it if the total matters.
- **BLER risk.** A wrong top-2 choice. **DEAD_ENDS?** Not the same as "adaptive 1/2/more hypotheses (exp. C)" or the
  correlation screening (A, B, D): those changed T or the score, A4 keeps the full metric for the finalists.
- **Test.** Offline on the `ref_diag` / decode dumps if they keep per-hypothesis partial metrics: how often is the
  final top-2 inside the c = 1/2 top-4. Online flag only if >= 99.9 %.

### A5. Pruned FFT for the fast path (input zero-padding x4, output only |nu| <= 0.12)
- **Source.** Sorensen & Burrus, "Efficient computation of the DFT with only a subset of input or output points",
  IEEE TSP 41(3) 1993 ([record](https://dblp1.uni-trier.de/rec/journals/tsp/SorensenB93.html), abstract).
- **Saving [derived].** 1024 nonzero inputs of 4096: the first two radix-2 stages are trivial (input pruning) and
  only about 1000 of 4096 bins are needed (output pruning): roughly 4096·10 instead of 4096·12 butterflies-MACs, or
  less with transform decomposition: -17 ... -30 % of each 98k FFT = -17 ... -30k per FFT, about **-1 ... -3 % total**
  at the low-SNR points and -3 ... -5 % at the fast-path-only points; per core about 0 (FFTs are split / 32). No BLER
  risk (exact). Not the "smaller 4th-power FFT" dead end (that changed the resolution). Low priority.

---

## 2. Read and NOT recommended (with reasons)

| Idea | Source | Why not for us |
|---|---|---|
| Dynamic list size inside SCL (expand / shrink on PM spread) | Ericsson US 11777533 ([Google Patents](https://patents.google.com/patent/US11777533B2/en)); Sequans US 10868571 ([Google Patents](https://patents.google.com/patent/US10868571B2/en)): about -40 % latency vs Enhanced-Fast-SSCL L = 32 at BLER 0.1 | In our per-core model the 8 list paths already run on 8 cores, so a shorter list saves only the sort (K·10 = 2-10k) per decode; total saving is real but A1 (SC-first) captures most of it with no new thresholds |
| PM-spread / frozen-PM in-decode termination of CA-SCL-8 | Qualcomm US 10615825, US 10742238 | Still open from surveys 1 and 2 (F4 / F5); A1 removes most accepted decodes first; the abort then only matters for decodes of wrong candidates. Keep the earlier test plan |
| Sharing tree computations between CFO / phase hypotheses ("SC of many hypotheses sharing LLR prefixes") | none found (searched); [derived] | Each hypothesis has its own channel LLRs; every polar node mixes all time positions (survey 2, F6). The only exact sharing is the pi rotation (f(-x,-y) = f(x,y)), which PiCode already exploits. Nothing published |
| Chirp-z / zoom FFT / polyphase de-rotation for many CFO cells | GNSS PCS (A2 sources) | The SC metric needs the de-rotated TIME samples; going back from the spectrum costs an IFFT (about 20k MACs) per cell, more than the 4.1k direct de-rotation. Only the shared per-cell rotation (A2) applies |
| Multiplier-free 8-phase quantized de-rotation (2-3 bit carrier replica, as in GNSS) | GNSS carrier replicas, 1-5 bit (search snippets) | [derived] uniform phase error +-pi/8 costs (sin(pi/8)/(pi/8))^2 = 0.95, -0.22 dB coherent loss on the search metric (16 phases: -0.06 dB but needs multiplies); on top of the 0.48 rad edge drift of a cell at 1/10. At 0.15 -4 dB, where BLER changes x6 per 0.5 dB and Stage 2 misses dominate, not worth the risk |
| SPRT / Tong detector per cell with absolute thresholds | O'Mahony et al. 2009 | Our robust-z checkpoints are already a multi-dwell sequential test; SPRT needs the H1 distribution (SNR- and drift-dependent) and is "sensitive to signal attenuation relative to its design point" (their abstract). "Smaller first round" and "early checkpoint at 1/8" are dead ends |
| Bandit / successive halving for the grid | Karnin et al. 2013 (survey 1) | We already use it (stride 2, z cuts at 1/2, 3/4); beam / gap racing is a dead end. Only A4 (inside Stage 3) is new |
| Generalized Fast-SSC nodes (G-REP, G-PC, sequence nodes) | Condo, Bioglio, Land 2018 ([1804.09508](https://arxiv.org/pdf/1804.09508), snippet): up to 23.6 % / 29.2 % latency vs Fast-SSC / Fast-SSCL, no loss | Latency (time steps), not operations; in our MAC count the f / g work above the nodes stays. Possible few % of m_met; count it with `metric_macs` on the new plan before any run |
| Distributed-CRC early termination | Pillet, Bioglio, Condo 2020 ([1907.00784](https://arxiv.org/abs/1907.00784), snippet) | Needs a code / CRC change (CRC bits interleaved among the information bits) and a new reference; not now |
| Two-staged adaptive SCL hardware | TA-SCL, 2019, authors not recorded ([1905.09120](https://arxiv.org/abs/1905.09120), abstract): 3.00 Gb/s (L = 8), 2.35 Gb/s (L = 32), about 3x throughput, 90 nm | Same principle as A1; no new MAC idea |
| Segmented adaptive SCL (SAD-SCL) | Entropy 2020 ([PMC7515421](https://pmc.ncbi.nlm.nih.gov/articles/PMC7515421/), full): N = 1024, R = 1/2, L 1 ... 16; average PM computations 17,277 (0.5 dB) to 28 (2.5 dB) | Re-decoding from a restart index needs segmented CRCs; for us A1 is the simple version |

---

## 3. Per-component state of the art (complexity only)

| Component | Ours | State of the art for cost | Verdict |
|---|---|---|---|
| Coarse CFO (fast path) | 4th-power FFT 4096 + parabolic | R&B FFT + interpolation (DVB-RCS2); pruned FFT | **use it**; A5 small exact gain |
| Hypothesis scoring | list-1 Fast-SSC partial metric, checkpoints | PDCCH: partial Fast-SSC metric, two-phase (Giard 2018, Condo 2018) | **use it**; A3 (reliable frozen subset) and A2 (shared de-rotation) are behind |
| Hypothesis search | stride, z-cuts, prior batches, early win, NN at 2/5, 1/2 | successive halving, multi-dwell / SPRT (GNSS) | **use it** (ahead of PDCCH practice in scale); A4 inside Stage 3 |
| Decoding | CA-SCL-8 per candidate, joint list at 2/5, 1/2 | adaptive SCL / Fast-SSC first (Li-Shen-Tse 2012, Sarkis 2016), dynamic list (Ericsson, Sequans) | **behind**: A1 |
| Code-aided retry | new SC pass + 2 Newton + decode | re-use of decoder state is standard in iterative receivers | **behind**: A1(a) (cache) |
| Early termination of wrong decodes | none inside the decode | PM-spread / frozen-PM abort (Qualcomm patents) | **behind**, still the open survey 1/2 item |
| Acceptance | CRC-16 (PiCode) + rho | unchanged by this survey | **use it** |

---

## 4. Not found / not readable
- No paper or patent on sharing SC / SCL computations across channel hypotheses (CFO, phase, timing).
- No public number for the fraction of PDCCH candidates killed early by any PM threshold (patents give no numbers).
- No number for SC vs CA-SCL-8 BLER at our exact points; P_SC in A1 must be measured.
- Huawei / MediaTek / Nokia / Samsung blind-decoding patents: none surfaced in two searches (only Qualcomm,
  Coherent Logix, Ericsson, Sequans).
- PDFs not parseable here: 1801.01820 PDF (read via ar5iv instead), Sorensen-Burrus full text, GNSS PCS papers.

---

## Reference entries

### Condo, Hashemi, Ebrahimi, Gross, "Design and Implementation of a Polar Codes Blind Detection Scheme", IEEE TCAS-II 2019 / arXiv 1801.01820 (2018)
- Link: https://ar5iv.labs.arxiv.org/html/1801.01820   - Type: paper   - Read depth: full (ar5iv)
## What it does
Two-phase PDCCH blind detection: C1 = 44 candidates decoded by SCL with L1 = 2, C2 = 5 selected (UE-ID match, PM) for
SCL-8; in phase 2 paths whose decoded ID bit mismatches are deactivated, decoding stops when all are. N = 256, 512,
K = 8 ... 57, BPSK AWGN. About 61-67 % of bits estimated on average when the UE's packet is present; FAR < 1e-4. 65 nm,
1 GHz: 1 SCL decoder 1.555 mm^2, worst / average latency 14.7 / 11.8 us; 4 decoders 6.117 mm^2, 4.7 / 3.7 us.
## What we took / could take
Confirms the two-phase cheap-screen-then-list structure we use; supports A1 (cheap first stage, list only when
needed). No new metric.
## Used in
-

### Li, Shen, Tse, "An Adaptive Successive Cancellation List Decoder for Polar Codes with Cyclic Redundancy Check", IEEE Commun. Lett. 16(12) 2012
- Link: https://arxiv.org/abs/1208.3091   - Type: paper   - Read depth: abstract
## What it does
CA-SCL whose list grows (1, 2, 4, ...) until a path passes the CRC; "significant complexity reduction";
(2048, 1024) + CRC-24 with a very large list reaches FER 1e-3 at Eb/N0 = 1.1 dB.
## What we took / could take
A1(b): our SC stage (L = 1) is already computed by the scoring pass, so the first adaptive step is free.
## Used in
-

### Sarkis, Giard, Vardy, Thibeault, Gross, "Fast List Decoders for Polar Codes", IEEE JSAC 34(2) 2016
- Link: https://ar5iv.labs.arxiv.org/html/1505.01466   - Type: paper   - Read depth: full (section V-VII)
## What it does
Unrolled Fast-SSC list decoders; adaptive decoder = Fast-SSC first, list (L = 8 / 32) only on CRC failure.
(2048, 1723) + CRC-32: adaptive L = 32 gives 8.6 / 33 / 196 Mb/s at 3.5 / 4.0 / 4.5 dB vs about 4 Mb/s list-only;
L = 8 adaptive 32.8 / 92.1 / 196 Mb/s.
## What we took / could take
A1(b) SC-first acceptance with CRC + rho, A1(a) cached SC codeword for the retry.
## Used in
-

### Lin, Sarkis, Yang (Qualcomm), "Frozen bits based pruning and early termination for polar decoding", US 10742238 B2, 2020
- Link: https://patents.google.com/patent/US10742238B2/en   - Type: patent   - Read depth: snippet (first 100k chars, survey 2)
## What it does
Per-path frozen-bit-only metric on reliable frozen positions, normalised; prune paths above a threshold, terminate
when all are pruned. No BLER / FAR numbers.
## What we took / could take
A3: use only reliable frozen leaves in the Stage 2 metric and skip the tree work of the unreliable ones; the in-decode
abort remains the open item of surveys 1 / 2.
## Used in
-

### Coherent Logix (now HyperX), "Scrambling sequence design for multi-mode block discrimination on DCI blind detection", US 10536305 B2, 2020
- Link: https://patents.google.com/patent/US10536305B2/en   - Type: patent   - Read depth: snippet (first 100k of 318k chars)
## What it does
UE-specific pseudo-random sequence in frozen bits enables early termination of wrong PDCCH candidates; "a threshold
may be applied to discriminate PM growth in the match case from the mismatch case"; later frozen bits are more
reliable but decoded later. No numbers in the part read.
## What we took / could take
Supports A3 (which frozen bits discriminate) and the per-candidate PM-growth view of our checkpoints. A PRBS in the
frozen bits would be a code change (not proposed).
## Used in
-

### Sarkis, Jiang, Lin, Yang (Qualcomm), "Early-termination techniques for polar list decoders", US 10615825 B2, 2020
- Link: https://patents.google.com/patent/US10615825B2/en   - Type: patent   - Read depth: snippet (survey 1)
## What it does
Stop an SCL decode when the normalised spread of the list PMs falls below a threshold after a minimum number of bits;
aimed at PDCCH / PUCCH blind decoding. No BLER numbers.
## What we took / could take
Not used now: in-decode abort stays the open item; A1 comes first.
## Used in
-

### Feng, Xie, Zhang (Ericsson), "Method for polar decoding with dynamic successive cancellation list size and polar decoder", US 11777533 B2, 2023
- Link: https://patents.google.com/patent/US11777533B2/en   - Type: patent   - Read depth: snippet (first part)
## What it does
At each information bit: double L if the PM spread of the 2L candidates is below Th1, shrink to M if the top-(M+1)
spread exceeds Th2; Lmax = 8; AWGN Th1 = 10, Th2 = 15; N = 64-256, R = 1/2; BEC running time < 1/3 of SCL.
## What we took / could take
Not used: in our per-core model list paths are parallel, so only the sort shrinks; A1 is simpler.
## Used in
-

### Sequans Communications, "Adaptive-SCL polar decoder", US 10868571 B2, 2020
- Link: https://patents.google.com/patent/US10868571B2/en   - Type: patent   - Read depth: snippet
## What it does
Halve / double the list on the median-to-min PM gap with a threshold scaled to the LLR spread and inversely to the
rate; about -40 % latency vs Enhanced-Fast-SSCL at L = 32, BLER 0.1; BLER about unchanged.
## What we took / could take
Not used (same reason as Ericsson US 11777533).
## Used in
-

### Two-staged adaptive SCL decoding for polar codes (TA-SCL), arXiv 1905.09120, 2019
- Link: https://arxiv.org/abs/1905.09120   - Type: paper   - Read depth: abstract (authors not recorded)
## What it does
Two-stage adaptive SCL with constant latency, Markov-chain parameter design; UMC 90 nm, 3.00 Gb/s (L = 8), 2.35 Gb/s
(L = 32), about 3x the throughput of SCL architectures, negligible loss.
## What we took / could take
Supports A1; nothing new.
## Used in
-

### Simplified segmented adaptive SCL (SAD-SCL), Entropy 2020 (PMC7515421)
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC7515421/   - Type: paper   - Read depth: full (authors not recorded)
## What it does
Adaptive SCL restarting from the least reliable positions with segmented CRC-8s; N = 1024, R = 1/2, L = 1 ... 16;
average PM computations 17,277 / 7,132 / 1,580 / 228 / 28 at Eb/N0 0.5 / 1 / 1.5 / 2 / 2.5 dB; "almost the same" FER as
CA-SCL-16.
## What we took / could take
Not used (needs segmented CRC); shows the steep fall of adaptive cost with SNR that A1 relies on.
## Used in
-

### Condo, Bioglio, Land, "Generalized Fast Decoding of Polar Codes", Globecom 2018 / arXiv 1804.09508
- Link: https://arxiv.org/pdf/1804.09508   - Type: paper   - Read depth: snippet
## What it does
G-REP and G-PC nodes; up to 23.6 % / 29.2 % decoding latency gain vs Fast-SSC / Fast-SSCL with no loss, up to
63.6 % / 49.8 % with some loss.
## What we took / could take
Not used: latency, not MAC count; count `metric_macs` with the new node plan before any test.
## Used in
-

### Pillet, Bioglio, Condo, "On List Decoding of 5G-NR Polar Codes", WCNC 2020 / arXiv 1907.00784
- Link: https://arxiv.org/abs/1907.00784   - Type: paper   - Read depth: snippet
## What it does
CA-SCL early termination when no surviving path satisfies the distributed CRC bits (PDCCH: 7 distributed CRC bits).
## What we took / could take
Not used: needs a distributed CRC (code change).
## Used in
-

### O'Mahony, O'Driscoll, Murphy, "Performance of Sequential Probability Ratio Test for GPS Acquisition", IEEE ICC 2009
- Link: https://research.ucc.ie/en/publications/performance-of-sequential-probability-ratio-test-for-gps-acquisit/   - Type: paper   - Read depth: abstract
## What it does
SPRT (sequential multi-dwell) vs fixed single-dwell verification for GPS L1 C/A: SPRT gives a shorter mean
acquisition time at typical SNRs but is sensitive to attenuation relative to its design point. No numbers in the
abstract.
## What we took / could take
Supports the sequential (checkpoint) principle and A4; argues against absolute-threshold SPRT for our SNR spread.
## Used in
-

### Modified parallel code-phase search architecture for modern GNSS signals (EPFL, accepted version) and EURASIP JASP 2014 acquisition paper
- Link: https://infoscience.epfl.ch/record/188391/files/Acquisition%20of%20modern%20GNSS%20signals%20using%20a%20modified%20parallel%20code-phase%20search%20architecture%20-%20Accepted%20version.pdf ; https://link.springer.com/doi/10.1186/1687-6180-2014-143   - Type: paper   - Read depth: snippet
## What it does
FFT-based parallel code-phase search: one carrier wipe-off per Doppler bin shared by all code phases; whole-bin
Doppler shifts by spectrum shifts, finer Doppler needs a partial removal before the FFT.
## What we took / could take
A2: one de-rotation per CFO cell shared by its phase hypotheses.
## Used in
-

### Sorensen, Burrus, "Efficient computation of the DFT with only a subset of input or output points", IEEE TSP 41(3):1184-1200, 1993
- Link: https://dblp1.uni-trier.de/rec/journals/tsp/SorensenB93.html   - Type: paper   - Read depth: abstract
## What it does
Input / output pruned DFTs and "transform decomposition" (FFT + Horner / Goertzel), fewer operations than pruning.
## What we took / could take
A5: pruned 4096-point FFT in the fast path (zero-padded input, |nu| <= 0.12 output).
## Used in
-

### Karnin, Koren, Somekh, "Almost Optimal Exploration in Multi-Armed Bandits", ICML 2013
- Link: https://labs.yahoo.com/mobstor/publication_attachments/Almost%20Optimal%20Exploration%20in%20Multi-Armed%20Bandits.pdf   - Type: paper   - Read depth: snippet (survey 1)
## What it does
Sequential halving, fixed-budget best-arm identification, near-optimal for equal variances.
## What we took / could take
Theory behind our checkpoints (already used) and A4.
## Used in
-

### Giard, Balatsoukas-Stimming, Burg, "On the Tradeoff Between Accuracy and Complexity in Blind Detection of Polar Codes", ISTC 2018 / arXiv 1807.00655
- Link: https://ar5iv.arxiv.org/html/1807.00655   - Type: paper   - Read depth: full (survey 1)
## What it does
Partial Fast-SSC detection metric after t visited nodes prunes PDCCH candidates: 40 of 44 dismissed at MDR 1e-2
(N = 256, K = 24 + CRC-16); SPC updates hurt at high BLER.
## What we took / could take
Supports A3 (which part of the tree discriminates, and partial metrics as a cheap screen).
## Used in
-
