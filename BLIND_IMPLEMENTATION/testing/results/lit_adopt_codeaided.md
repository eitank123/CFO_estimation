# Literature survey 3: code-aided / pilotless synchronization methods to ADOPT (2026-11-15)

Scope (main-session request): deep-read Yang et al. 2026, Xu et al. 2024, Yue et al. 2026, Wu et al. 2025 and related
2023-2026 work on pilotless code-aided synchronization with a wide CFO range, and on using PARTIAL decoder metrics to
drive a frequency search or optimisation (gradient / Taylor / cross-entropy instead of a grid). For each: algorithm,
pull-in range in cycles/symbol, setting, numbers, which part of our pipeline it could replace, expected effect at our
points (1/10 -5 dB, 0.15 -4 dB, 2/5 0.5 dB, 1/2 2 dB), risks, DEAD_ENDS status.

Read before searching (not repeated): `DEAD_ENDS.md`, `lit_blind_cfo.md` (survey 1), `lit_polar_sync.md` (survey 2),
README "Current state", `07_complexity.md`, `04_search.md`, `05_decoding.md`, `expected_ref.md` (D0 refinement
diagnostic, measured today), `expected_online_f3dd.md` (ddref / lm2 in flight), `expected_pns.md` (pns measured today).

Reading depth: "full" = full text; "abstract" = abstract only (often via the OpenAlex / Crossref record, because the
IEEE Xplore pages could not be fetched); "metadata" = title / venue only. Numbers marked **[derived]** are my own
arithmetic. No simulations were run.

**What could NOT be read.** The full texts of Yang et al. 2026 (IEEE Access, open access, but the Xplore page and PDF
could not be fetched from here), Xu et al. 2024 (IEEE TVT) and the TVT 2026 version of Yue et al. are not read: for
these I have the abstracts only. For Yue et al. I read the full arXiv preprint (2309.12828v2), which has the same
cross-entropy stage but EM instead of the journal's "Taylor expansion" step. For Wu et al. 2025 only the abstract page
was readable this session (the PDF did not parse); the numbers below come from survey 2's full-text read of the same PDF.
**If the user has IEEE access, the full texts of Yang 2026 (doi 10.1109/ACCESS.2026.3653159) and Xu 2024
(doi 10.1109/TVT.2024.3383891) are the two worth downloading**: their pull-in ranges are not in the abstracts.

**Main comparability caveat.** Every paper here uses LDPC or polar codes with BP / sum-product decoding (soft outputs
for free), BPSK or QPSK, Eb/N0 >= 0-1 dB, and either a small residual CFO (EM family: |f| <= 2e-4 cycles/symbol) or an
upstream FFT acquisition that leaves at most one FFT bin. None searches |f| <= 0.03 cycles/symbol without pilots at
Es/N0 -5 dB with an SC-type decoder. dB figures are relative to each paper's own ideal-sync curve and are not
transferable.

---

## 1. Ranked adoption candidates (4)

### A1. Soft (posterior-weighted) symbols instead of hard re-encoded symbols in the code-aided estimators (`ddref`, `pns`, retry)
- **Literature consensus.** Every code-aided synchronizer read uses SOFT symbol estimates from the decoder, never the
  hard codeword: EM with posterior means (Noels et al. 2005, the framework paper); soft decision feedback in the
  carrier loop, within 0.3 dB of perfect sync (Valles et al. 2006); "squared sum of soft decision metrics" after a few
  LDPC iterations, within 0.1 dB (Bao et al. 2015; Yang et al. 2026); posterior expectations from BP LLRs with a
  piecewise-linear tanh (alpha = 1/3, threshold 3) in Yue et al. (arXiv full text); extrinsic LLRs widen the phase
  acquisition region from +-30 deg to +-40 deg at iteration 3 (APPA, 2009 abstract).
- **Our state.** The code-aided retry (05, 5.4), the `ddref` candidate (expected_online_f3dd.md B) and `pns`
  (expected_pns.md) all use the HARD SC / list codeword (pns: list-weighted with exp(-PM), which is close to hard because
  the 8 paths differ in few bits). The measured pns limit is exactly the one the literature avoids: "one smoothing pass
  from a FAILED decode's list symbols (decision errors corrupt the phase reference)", 4-7 % of calls fix the packet.
- **What to borrow.** x_bar_n = E[s_n | y] from per-code-bit posterior LLRs, Lpost = Lch + Lext:
  - (a) cheap: Lext_n = Lam * c_hat_n with a constant code reliability Lam (from the rate / SNR; one table entry),
    x_bar = tanh(Lpost/2) per I/Q bit; ~4 MACs per bit, ~8k MACs per call [derived];
  - (b) proper: Lext from one SCAN backward pass on the SC schedule (Fang 2019 uses SCAN soft outputs to refine an
    unknown channel state; SCANL in Pillet et al. 2020). Cost about 2 list-1 SC passes [derived: SCAN carries L and B
    messages per node], i.e. ~45-50k MACs [derived from 07: one list path of CA-SCL-8 = 8 N log2 N / 8 = 22.5k], small
    next to the grid refinement's 0.36-0.40 M per refined cell (expected_ref.md).
- **Not a dead end.** DEAD_ENDS `dd` / `dd_win4` are HARD-codeword DD after the grid (AWGN, no packet fixed); the soft
  version is a different estimator, and the reason to reopen is the measured pns limit (decision errors), plus ddref
  being reopened as a grid replacement (D0: DD Newton 2-3x more accurate than the grid's pick on true cells).
- **Expected effect (reasoned, not measured).**
  - pns under phase noise (2/5 0.5 dB, 1/2 2 dB, 0.15 -3.5 dB at 1e-4): the fix rate per call should rise because
    wrong bits get weight ~0 instead of -1. Upper bound: the DVB-RCS2 tracking receiver at 2/5 1e-4 (1967 vs ~4400
    errors per 64k for pns now). MACs per core: pns already lowers them (-5 ... -14 %) because fixed packets stop
    searching; variant (a) adds ~0.
  - ddref in AWGN (1/10 -5 dB, 0.15 -4 dB): D0 rms 0.33 / 0.42 STEP (hard, centre codeword). Soft weighting should help
    most where the SC codeword is worst (low z), i.e. it should cut the fallbacks to the grid; MACs: part of the
    -5 ... -14 % total that ddref targets. BLER upper bound from refinement: 37 % of 0.15 -4 dB failures and 65 % at
    2/5 0.5 dB had a refined true-cell candidate (D0), 0 at 1/10 -5 dB; so no BLER gain at 1/10 -5 dB is possible.
- **Risks.** Lam mis-set (too large = hard DD again; too small = NDA, which fails at -5 dB); the SCAN pass costs one
  more serial pass on the critical path; the soft symbols must still be re-mapped through the bit interleaver.
- **Test.** Offline first on the D0 dumps (expected_ref.md rows, if they keep the received packet and the list-1
  codeword + channel LLRs): rms CFO residual of DD Newton with (hard, soft-a for Lam in {1, 2, 4}, soft-b) at 1/10 -5,
  0.15 -4 / -3, 2/5 0.5 dB. Go online only if soft beats hard by >= 20 % rms or raises the share within 0.5 STEP by
  >= 0.03. Online: flag on top of `ddref` (`dd_soft = a|b`) and of `pns` (`pns_soft`), 64k paired at the pns points
  (1e-4) and AWGN 0.15 -4 dB / 2/5 0.5 dB; kill rules as in expected_pns.md.

### A2. Iterate estimate -> decode 2-3 times with CHEAP intermediate passes (Yang / Bao "few decoding iterations", Costas + decoder feedback)
- **Source.** Yang et al. 2026 (abstract): joint phase + frequency by maximising the squared sum of partial decision
  metrics of "just a few LDPC decoding iterations" with an approximate stochastic gradient, then Costas tracking with
  decoder feedback to cut residual offsets; within 0.1 dB of ideal, rate-1/2 LDPC QPSK at Eb/N0 1-2 dB. The 2015 WCSP
  paper of the same group has the same structure and the same 0.1 dB claim. Valles et al. 2006: within 0.3 dB.
- **Our state.** pns = 1 smoothing pass + 1 CA-SCL-8 decode, at most 2 calls per packet; expected_pns.md already lists
  "more passes (iters 2-3)" as the next step. The literature point to add is: **do not pay a full CA-SCL-8 decode per
  iteration**. The LDPC papers update the synchronizer after a few BP iterations, i.e. on partial decoder output. Our
  analogue: intermediate iterations use a list-1 SC pass (22.5k MACs) [+ SCAN if A1-b] to produce new soft symbols,
  only the final iteration runs CA-SCL-8 (180k total, ~26k per core with the sort [derived from 07]).
- **Expected effect.** Under phase noise: more of the "right region, wrong phase path" packets fixed; MACs per core per
  extra iteration ~ +23k on the serial path [derived], only on failing packets. In AWGN: ~0 BLER change (the dd lesson),
  cost only on failures (+7 % per core at 2/5 0.5 dB AWGN was the measured cost of pns with full decodes; list-1
  intermediates should be cheaper).
- **Risks.** Self-confirmation of a wrong codeword over iterations (as the "verified re-decode" dead end): keep it only
  on CRC / rho failures and keep CRC + rho as the only acceptance. Cycle slips across pi/2 at low SNR (the rotation must
  stay on the decoded branch).
- **Test.** `pns_it = 2, 3` with list-1 intermediates, with and without A1, at 2/5 0.5 dB and 0.15 -3.5 dB, pn 1e-4 and
  3e-4, 64k paired against current pns; AWGN 2/5 0.5 dB for the cost.

### A3. Keep the grid; do NOT switch to cross-entropy or gradient search for acquisition (negative recommendation, with numbers)
- **Source.** Yue et al. (TVT 2026; arXiv 2309.12828 full): a 64-point FFT acquisition leaves |f| <= 1/128 = 7.8e-3
  cycles/symbol; the cross-entropy (CE) stage samples quantised CFO / CPO bit vectors (D = 6 CFO bits + 1 phase bit,
  N_c = 120 samples, N_e = 24 elites, 4-8 iterations), each sample scored by a combined-SNR objective built from BP
  posterior LLRs; then EM (arXiv) or a Taylor expansion of the objective (journal). Polar (1024, 512), BPSK-DSSS, BP.
  Losses at BER 1e-4: 0.3 / 0.4 dB (2 / 4 satellites; the arXiv body text has them swapped). Quantisation: 5 bits ->
  4.2 dB loss, 7 bits -> 0.5 dB. No complexity numbers.
- **Why not for us [derived].** (1) Their CE grid step is 2 x 7.8e-3 / 128 = 1.2e-4 cycles/symbol, the same as our
  cells (1.5-3e-4), but over a range 3.8x narrower; covering 0.06 at that step needs ~490 levels (~9 bits). (2) Our
  metric landscape is a needle: the basin is about one cell (D0: cell centre rms 1.1 STEP). With 120 samples on 201
  cells, P(at least one sample in the true cell) = 1 - (200/201)^120 = 0.45 per CE round; otherwise the elites are
  noise and CE converges to a wrong cell. The exhaustive grid hits it with probability 1. (3) 480-960 objective
  evaluations, each a FULL decode, vs our 201 x 4 = 804 PARTIAL passes most of which stop at the first checkpoint.
  (4) Their 5-bit result (4 dB loss) is the same lesson as our "coarser CFO grid" dead end.
- **Taylor / gradient = Newton.** The journal's "Taylor expansion of the objective" is a local second-order step, the
  same thing as our retry's 2 Newton steps on |sum z e^{-j2 pi f n}|^2 and ddref: **we already use it**.
- **Pull-in of gradient methods.** Yang 2026 / Bao 2015 / Qiu 2021 give "large" offsets without numbers in the
  abstracts; Qiu 2021 (timing, same group) needs a coarse-to-fine capture stage first. A gradient on a decoder
  metric needs a start inside the basin; at 1/10 below 0 dB the 4th-power periodogram puts the true cell at mean rank
  ~90 of 201 (expected_ref.md) and the fast path finds the right peak in <= 7 % of packets (DEAD_ENDS), and even inside
  the true cell the 4th-power Newton is worse than the cell centre (1.24-1.35 vs 1.07-1.13 STEP, D0). So no gradient
  method can replace Stage 2 at our low-SNR points.

### A4. Consider re-using the squared-soft-metric objective only as a Stage 3 SCORE, not as a search (low priority)
- **Source.** Bao 2015 / Yang 2026 maximise S = sum_n (soft decision of bit n)^2 after a few decoder iterations; Man et
  al. 2013 maximise the mean |soft output| over a frequency grid then interpolate (8-PSK, (1944, 972) LDPC, "negligible"
  loss).
- **Our state.** Stage 3 scores offsets with the full list-1 PM (the ML-type metric). D0 (expected_ref.md) already
  killed the interpolation part (neighbour metrics missing for 59-96 % of candidates). Giard's frozen-only metric
  (another "confidence" metric) gave the same ranking as the PM (dead end).
- **Verdict.** S is a weaker, BP-specific proxy for the likelihood; for SC the PM is already the log-likelihood of the
  path. Not worth a test unless A1-b (SCAN) is built, in which case S is free and can be logged next to the PM for an
  offline rank comparison.

(Nothing else read gives a concrete MAC or BLER win at our points: see the per-component verdict.)

---

## 2. Answers to the five questions

1. **Yang et al. 2026 (IEEE Access).** Algorithm (abstract): pilotless iterative carrier synchronization (ICS) for QPSK;
   maximise the squared sum of LDPC partial decision metrics (PDMs) from a few decoding iterations by an approximate
   stochastic gradient, jointly in phase and frequency; a two-stage hybrid ICS for the phase ambiguity; Costas loop
   tracking united with decoder feedback. Rate-1/2 LDPC QPSK, Eb/N0 1-2 dB, "within 0.1 dB of perfect" at "rather
   large" phase offsets, "moderate" complexity increase. Block length, CFO pull-in range, iteration counts: **not in the
   abstract, full text not read**. Same structure and claim as Bao et al. 2015 (WCSP). Maps to: refinement / retry /
   pns (A1, A2), not to the grid. Not in DEAD_ENDS as such (the hard `dd` is).
2. **Xu et al. 2024 (IEEE TVT 73(7), 10451-10463; title "Carrier Frequency Synchronization of LDPC Coded
   Transmissions in High Dynamic Environments").** Abstract: a new frequency estimator, moderate complexity, wider
   estimation range and variance near the CRB; an EM-based iterative synchronizer embedded in the LDPC decoder; a general
   framework for joint acquisition and fine synchronization. Whether the estimator is NDA or data-aided, its range in
   cycles/symbol, the code length and SNRs: **not in the abstract, full text not read**. If it is NDA, it competes with
   our fast path (4th-power FFT + Newton), which only matters at 2/5, 1/2 (the fast path is off at 1/10, 0.15 below
   0 dB); NDA estimators have a threshold (survey 1, Morelli-Mengali) that no estimator design removes at -5 dB.
   Cited 6 times (OpenAlex), one of them Yang 2026.
3. **Yue et al. 2026 (IEEE TVT 75(2), 2500-2515; arXiv 2309.12828).** See A3. Pull-in: 7.8e-3 cycles/symbol for the CE
   stage, after a 64-point FFT acquisition (DSSS, Rs = 1000 sps). Not for our grid; the Taylor step is our Newton.
4. **Wu et al. 2025 (J. TT&C 46(6), 39-44, "PCAFOE").** Confirmed: (2048, 1024) polar, BPSK, BP-based EM-type ML,
   Eb/N0 0-5 dB, |f| <= 2e-4 cycles/symbol, "closer to the MCRB than Fitz", no complexity (survey 2, full text; this
   session: abstract page only, which has no numbers). It is a journal version of Wu, Chen, Bu, ITNEC 2020 (same
   first author, same PCAFOE name). Normalised to our packet [derived]: 2e-4 over 2048 BPSK symbols is an edge phase of
   2 pi x 2e-4 x 1024 = 1.29 rad; for 1024 QPSK symbols with half the phase tolerance that is again ~+-2e-4, i.e. about
   our half-cell at 1/10 (1.5e-4) and above it at 2/5 (0.75e-4). So: EM-limited, no acquisition at |f| <= 0.03,
   usable only inside a cell, which is exactly where D0 found DD Newton good (our judgement stands; slightly
   corrected: the range is ~1 half-cell, not less).
5. **Related 2023-2026.** No 2023-2026 paper found that drives a WIDE-range frequency search with partial decoder
   metrics, for polar or LDPC; the partial-metric idea appears only as (a) Yang 2026 / Bao 2015 (few BP iterations per
   gradient step, small residual range assumed), (b) Qiu 2021 (timing, steepest descent on summed squared LDPC soft
   metrics, coarse-to-fine capture then Mueller-Mueller tracking, within 0.1 dB of ideal), (c) older: Valles 2006
   (check-node feedback for frequency / timing, carrier phase from soft LDPC info, within 0.3 dB), Man 2013 (grid on
   mean |soft output| + interpolation, then DD). Cross-entropy in sync: only Yue et al. Early stopping of iterative
   carrier sync: PIMRC 2010 (stop on LLR conditions, "little loss"), and a 2012 Acta Aeronautica paper (iterations
   -50 % at BER 1e-5, < 0.15 dB with phase noise) - we already stop at the first accepted decode.

---

## 3. Per-source table

| # | Title (authors), year | Link | Read | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|
| 1 | Pilotless Iterative Carrier Synchronization With LDPC Partial Decision Metrics in Satellite Communications at Low SNRs (Yang, Cai, Cai, Li, Jin, Bao), IEEE Access 2026 | [doi 10.1109/ACCESS.2026.3653159](https://doi.org/10.1109/access.2026.3653159), [OpenAlex record](https://api.openalex.org/works/doi:10.1109/access.2026.3653159) | abstract | medium-high: soft-metric + few-iteration loop (A1, A2) | max squared sum of PDMs of a few LDPC iterations, approx. stochastic gradient over phase + frequency; 2-stage hybrid for ambiguity; Costas + decoder feedback | rate-1/2 LDPC, QPSK, satellite, Eb/N0 1-2 dB; length / CFO range not in abstract | within 0.1 dB of perfect sync; "moderate" complexity increment |
| 2 | Iterative carrier recovery in an LDPC coded QPSK system at low SNRs (Bao et al.), WCSP 2015 | [doi 10.1109/WCSP.2015.7340999](https://doi.org/10.1109/wcsp.2015.7340999) | abstract | medium: precursor of #1 | max sum of squared soft decision metrics, gradient update of phase + CFO; Costas tracking; ambiguity solution | rate-1/2 LDPC QPSK, Eb/N0 ~1-2 dB | within 0.1 dB of ideal, "large" phase and frequency offsets |
| 3 | Efficient Iterative Timing Recovery of LDPC Decoding Metrics Using the Steepest Descent Algorithm ... (Qiu, Liu, Bao, Jiang, Shang), Electronics 2021 | [doi 10.3390/electronics10243055](https://doi.org/10.3390/electronics10243055) | abstract (MDPI page 403) | low-medium: same objective, for timing | steepest descent on summed squared LDPC soft metrics, Gaussian-approx. analysis, coarse-to-fine capture + M&M tracking | coded BPSK, low SNR | within 0.1 dB of ideal code |
| 4 | Carrier Frequency Synchronization of LDPC Coded Transmissions in High Dynamic Environments (Xu, Xiong, Yang, Zhou), IEEE TVT 73(7) 2024 | [doi 10.1109/TVT.2024.3383891](https://doi.org/10.1109/tvt.2024.3383891), [Crossref](https://api.crossref.org/works/10.1109/tvt.2024.3383891) | abstract (via OpenAlex) | medium, unverified: wide-range estimator + EM | new frequency estimator (wide range, near-CRB) + EM sync embedded in LDPC decoding; joint acquisition + fine framework | LDPC, low SNR, high dynamics; details not read | none in abstract |
| 5 | Code-Aided CFOs and CPOs Estimation in Cooperative Satellite Communication (Yue, Li, Li, Zhang, Wang, An), IEEE TVT 75(2) 2026 | [doi 10.1109/TVT.2025.3600028](https://doi.org/10.1109/TVT.2025.3600028), [BIT record](https://pure.bit.edu.cn/zh/publications/code-aided-cfos-and-cpos-estimation-in-cooperative-satellite-comm/) | abstract | medium: CE + Taylor (A3) | ICE (cross-entropy) + cooperative Taylor expansion of the objective | LEO multi-satellite, short bursts, no training | 0.3 dB (2 sats), 0.4 dB (4 sats) from BER bounds |
| 6 | Multiple Satellites Collaboration for Joint Code-aided CFOs and CPOs Estimation (same authors), arXiv 2309.12828v2, 2023 | [arXiv html](https://arxiv.org/html/2309.12828) | full | medium: the readable version of #5 | ICE: N_c = 120, N_e = 24, D = 6+1 bits, 4-8 iterations, objective from BP posteriors (tanh approx alpha 1/3, T_h 3); CEM fine stage | polar (1024, 512), BP, BPSK-DSSS, Rs 1000 sps, 64-pt FFT, \|f\| <= 7.8e-3, Es/N0 -3 dB | 0.3-0.4 dB at BER 1e-4; 5 bits: 4.2 dB loss, 7 bits: 0.5 dB; N_e 4: 1.3 dB, N_e 32: 0.4 dB; NFO 1e-4 costs ~1 dB uncompensated |
| 7 | Research on Carrier Synchronization Frequency Offset Estimation Algorithms for Aerospace TT&C (Wu, Wang, Chen, Wang), J. TT&C 46(6) 2025 | [abstract page](https://castjournals.cast.org.cn/joweb/ycyk/EN/10.12347/j.ycyk.20250628001) | abstract (full text in survey 2) | low: EM-limited | PCAFOE: polar-code-aided ML / EM with BP posteriors | (2048, 1024) BPSK, Eb/N0 0-5 dB, \|f\| <= 2e-4 (survey 2) | closer to MCRB than Fitz (plots only); no complexity |
| 8 | Polar Code-Aided Frequency Offset Estimation Algorithm in Satellite Covert Communication Carrier Synchronization (Wu, Chen, Bu), ITNEC 2020 | [BIT record](https://pure.bit.edu.cn/en/publications/polar-code-aided-frequency-offset-estimation-algorithm-in-satelli) | abstract | low: earlier version of #7 | PCAFOE | short polar codes, satellite | RMSE better than traditional (no numbers) |
| 9 | A Novel Code-Aided Carrier Recovery Algorithm for Coded Systems (Man, Xi, Gao, Zhang), IEEE CL 2013 | [doi 10.1109/LCOMM.2012.121912.122278](https://doi.org/10.1109/lcomm.2012.121912.122278) | abstract | medium: grid on a decoder metric + interpolation = our Stage 2 + parabola | coarse: max mean \|LDPC soft output\| + interpolation; fine: decoder decisions | 8-PSK, (1944, 972) LDPC, low SNR, "large" CFO | "negligible" loss vs ideal |
| 10 | Carrier and Timing Synchronization of BPSK via LDPC Code Feedback (Valles, Wesel, Villasenor, ...), Asilomar 2006 | [doi 10.1109/ACSSC.2006.355154](https://doi.org/10.1109/acssc.2006.355154) | abstract | medium: soft decoder feedback (A1) | check-node feedback for CFO / timing; soft LDPC info for carrier phase | BPSK, pilotless | within 0.3 dB of perfect phase + timing |
| 11 | A Theoretical Framework for Soft-Information-Based Synchronization in Iterative (Turbo) Receivers (Noels et al.), EURASIP JWCN 2005 | [doi 10.1155/WCN.2005.117](https://doi.org/10.1155/wcn.2005.117) | abstract | medium: classic baseline | turbo sync = EM with soft posteriors; phase, CFO, timing, amplitude | turbo-coded 16-QAM | no numbers in abstract |
| 12 | Iterative Code-Aided ML Phase Estimation and Phase Ambiguity Resolution (Wymeersch, Moeneclaey), EURASIP JASP 2005 | [doi 10.1155/ASP.2005.981](https://doi.org/10.1155/asp.2005.981) | abstract | low-medium | iterative ML phase + ambiguity from MAP soft info; convergence / initialisation | turbo codes | lower MSE and BER loss; ambiguity resolved without pilots |
| 13 | Iterative Carrier Phase Recovery Suited to Turbo-Coded Systems, IEEE TWC 2004 (authors not read) | [doi 10.1109/TWC.2004.837407](https://doi.org/10.1109/twc.2004.837407) | abstract | low-medium | APPA: extrinsic LLRs feed an iterative ML phase estimator | turbo BPSK / QPSK, AWGN | variance near CRB at very low SNR |
| 14 | Novel iterative APPA carrier phase recovery and detection for turbo-coded systems, ICCOMTA 2009 | [doi 10.1109/ICCOMTA.2009.5349142](https://doi.org/10.1109/iccomta.2009.5349142) | abstract | low | APPA with parity + information LLRs | turbo | acquisition +-30 deg -> +-40 deg at iteration 3 |
| 15 | Early stopping scheme for iterative carrier synchronization of LDPC codes, PIMRC 2010 | [doi 10.1109/PIMRC.2010.5671809](https://doi.org/10.1109/pimrc.2010.5671809) | abstract | low: we already stop at the first accepted decode | stop the sync-decode loop on LLR conditions | LDPC | "little" loss, negligible extra cost |
| 16 | Code-aided Carrier Synchronization via Soft Decision Feedback Based on Early Stopping Criterion, Acta Aeronautica et Astronautica Sinica 2012 | [abstract page](https://hkxb.buaa.edu.cn/EN/abstract/article/1000-6893/14674) | abstract (via OpenAlex search) | low | early stop when the estimated SNR passes a criterion | rate-1/2 LDPC | iterations -50 % at BER 1e-5; < 0.15 dB with phase noise |
| 17 | Decoding Polar Codes via Weighted-Window Soft Cancellation for Slowly-Varying Channel (Fang), arXiv 2019 | [1911.08763](https://arxiv.org/abs/1911.08763) | abstract | medium: SCAN soft output refines an unknown channel state (A1-b) | W2SCAN: coarse state, then per SCAN iteration a QP refinement | slowly varying unknown channel | no numbers in abstract |
| 18 | SCAN List Decoding of Polar Codes (Pillet, Condo, Bioglio), ICC 2020 | [2001.11283](https://arxiv.org/abs/2001.11283) | abstract | low-medium: soft-output polar decoder option | L SCAN decoders on permuted graphs, early termination | polar | ~BPL performance at lower complexity; no numbers in abstract |
| 19 | Enhanced BICM Receivers for URLLC Short Packet Communications (Sy, Knopp), arXiv 2024-25 | [2408.08660](https://arxiv.org/abs/2408.08660) | abstract | low: pilot-based, no CFO | joint estimation-detection metrics over ~4-symbol windows | 5G polar / LDPC, QPSK, sparse pilots | close to perfect-CSI receivers |

Not found / not readable: full texts of #1, #4, #5 (IEEE); a 2023-2026 paper with a polar code-aided CFO search wider
than ~2e-4 cycles/symbol (none, as in surveys 1-2); the PDFs of Godtmann et al. 2007 (RWTH link 404; it is
data-aided anyway) and Valles 2010 (PDF not parseable).

---

## 4. Per-component state of the art

| Component | Ours | Literature (this survey) | Verdict |
|---|---|---|---|
| Coarse CFO (fast path) | 4th-power FFT + Newton, off at 1/10, 0.15 below 0 dB | FFT acquisition before code-aided stages (Yue: 64-pt FFT); Xu 2024 "wide-range near-CRB" estimator (unread) | **we already use it**; Xu 2024 unverified (need full text) |
| Wide-range search | 201-401 cells x 2-4 phases, partial list-1 PM, checkpoints | CE sampling over 7-bit CFO (Yue); grid on mean \|soft output\| + interpolation (Man 2013) | **we already use it** (grid); CE **not applicable** (needle landscape, A3); interpolation killed by D0 |
| Fine CFO / phase | grid offsets (5 x phases), ddref (DD Newton) in test | EM / Taylor / gradient on SOFT posteriors (Noels, Yue, Yang, Wu) | **behind on soft symbols** (A1); Taylor / Newton **already used** |
| Iterative sync-decode | retry: 2 Newton steps + 1 decode; pns: 1 smoothing + 1 decode, <= 2 calls | 2-4+ loop iterations on partial decoder output, Costas + decoder feedback (Yang, Bao, Valles) | **behind** (A2) |
| Phase ambiguity | PiCode + pi/2 phase hypotheses; eqrb in test | two-stage hybrid ICS (Yang); ML ambiguity (Wymeersch) | **we already use it** (hypotheses); nothing better found |
| Stopping / early termination | stop at first accepted decode; early win z > 6; spec11 | early-stop on LLR / SNR conditions (PIMRC 2010, 2012) | **we already use it** |
| Acceptance | CRC-16 + rho | none of these papers addresses false acceptance (all assume known frames, BER curves) | **not applicable** (no new input) |

---

## 5. Sources
- https://doi.org/10.1109/access.2026.3653159 ; https://api.openalex.org/works/doi:10.1109/access.2026.3653159 ; https://api.crossref.org/works?query.bibliographic=Pilotless+Iterative+Carrier+Synchronization+LDPC+Partial+Decision+Metrics+Satellite&rows=5
- https://doi.org/10.1109/wcsp.2015.7340999
- https://doi.org/10.3390/electronics10243055
- https://doi.org/10.1109/tvt.2024.3383891 ; https://api.crossref.org/works/10.1109/tvt.2024.3383891 ; https://api.openalex.org/works/doi:10.1109/tvt.2024.3383891
- https://doi.org/10.1109/TVT.2025.3600028 ; https://pure.bit.edu.cn/zh/publications/code-aided-cfos-and-cpos-estimation-in-cooperative-satellite-comm/
- https://arxiv.org/html/2309.12828 ; https://arxiv.org/abs/2309.12828v2
- https://castjournals.cast.org.cn/joweb/ycyk/EN/10.12347/j.ycyk.20250628001
- https://pure.bit.edu.cn/en/publications/polar-code-aided-frequency-offset-estimation-algorithm-in-satelli
- https://doi.org/10.1109/lcomm.2012.121912.122278
- https://doi.org/10.1109/acssc.2006.355154
- https://doi.org/10.1155/wcn.2005.117
- https://doi.org/10.1155/asp.2005.981
- https://doi.org/10.1109/twc.2004.837407
- https://doi.org/10.1109/iccomta.2009.5349142
- https://doi.org/10.1109/pimrc.2010.5671809
- https://hkxb.buaa.edu.cn/EN/abstract/article/1000-6893/14674
- https://arxiv.org/abs/1911.08763
- https://arxiv.org/abs/2001.11283
- https://arxiv.org/abs/2408.08660

---

## Reference entries

### Yang, Cai, Cai, Li, Jin, Bao, "Pilotless Iterative Carrier Synchronization With LDPC Partial Decision Metrics in Satellite Communications at Low SNRs", IEEE Access, 2026, doi 10.1109/ACCESS.2026.3653159
- Link: https://doi.org/10.1109/access.2026.3653159   - Type: paper   - Read depth: abstract
#### What it does
Pilotless QPSK carrier sync: maximise the squared sum of LDPC partial decision metrics from a few decoding iterations by
an approximate stochastic gradient (phase + frequency jointly); two-stage hybrid scheme for the phase ambiguity; Costas
loop united with decoder feedback. Rate-1/2 LDPC, Eb/N0 1-2 dB, within 0.1 dB of perfect sync. Block length and CFO
pull-in range not in the abstract (full text not read).
#### What we took / could take
Soft symbols instead of hard codewords in ddref / pns (A1) and 2-3 cheap loop iterations (A2). Not a grid replacement.
#### Used in
-

### Bao et al., "Iterative carrier recovery in an LDPC coded QPSK system at low SNRs", WCSP 2015, doi 10.1109/WCSP.2015.7340999
- Link: https://doi.org/10.1109/wcsp.2015.7340999   - Type: paper   - Read depth: abstract
#### What it does
Precursor of Yang 2026: gradient maximisation of the sum of squared LDPC soft decision metrics for phase and CFO,
Costas tracking with decoder feedback, ambiguity resolution; rate-1/2 LDPC QPSK at Eb/N0 ~1-2 dB, within 0.1 dB.
#### What we took / could take
Supports A1 / A2. Not used otherwise.
#### Used in
-

### Qiu, Liu, Bao, Jiang, Shang, "Efficient Iterative Timing Recovery of Low-Density Parity-Check Decoding Metrics Using the Steepest Descent Algorithm for Satellite Communications at Low SNRs", Electronics 10(24) 3055, 2021
- Link: https://doi.org/10.3390/electronics10243055   - Type: paper   - Read depth: abstract
#### What it does
Timing (not carrier) recovery by steepest descent on the summed squared LDPC soft metrics, coarse-to-fine capture then
Mueller-Mueller tracking; coded BPSK; within 0.1 dB of the ideal code.
#### What we took / could take
Not used: timing is known in our study. Shows that gradient methods on decoder metrics need a capture stage first.
#### Used in
-

### Xu, Xiong, Yang, Zhou, "Carrier Frequency Synchronization of LDPC Coded Transmissions in High Dynamic Environments", IEEE Trans. Veh. Technol. 73(7), 10451-10463, 2024, doi 10.1109/TVT.2024.3383891
- Link: https://doi.org/10.1109/tvt.2024.3383891   - Type: paper   - Read depth: abstract
#### What it does
New frequency estimator (moderate complexity, wider range, variance near the CRB), an EM synchronizer embedded in LDPC
decoding, and a framework for joint acquisition and fine sync at low SNR. Range, pilots, code length, SNR not in the
abstract.
#### What we took / could take
Nothing yet; full text needed to judge whether the estimator could improve the fast path at 2/5, 1/2.
#### Used in
-

### Yue, Li, Li, Zhang, Wang, An, "Code-Aided CFOs and CPOs Estimation in Cooperative Satellite Communication", IEEE Trans. Veh. Technol. 75(2), 2500-2515, 2026, doi 10.1109/TVT.2025.3600028 (preprint: arXiv 2309.12828, 2023)
- Link: https://arxiv.org/html/2309.12828   - Type: paper   - Read depth: full (arXiv) / abstract (journal)
#### What it does
64-point FFT acquisition, then iterative cross-entropy over quantised CFO / CPO (D = 6 + 1 bits, 120 samples, 24
elites, 4-8 iterations; objective from BP posteriors), then EM (arXiv) or Taylor expansion (journal). Polar (1024, 512)
BP, BPSK-DSSS, |f| <= 7.8e-3 cycles/symbol, Es/N0 -3 dB; 0.3-0.4 dB from the BER bound at 1e-4; 5 bits: 4.2 dB loss.
#### What we took / could take
Not used: CE hits the true cell of a 201-cell needle landscape with p = 0.45 per round [derived] and needs full
decodes per sample; the Taylor step = our Newton step (retry, ddref).
#### Used in
-

### Wu, Wang, Chen, Wang, "Research on Carrier Synchronization Frequency Offset Estimation Algorithms for Aerospace TT&C Communications", J. Telemetry, Tracking and Command 46(6), 39-44, 2025, doi 10.12347/j.ycyk.20250628001
- Link: https://castjournals.cast.org.cn/joweb/ycyk/EN/10.12347/j.ycyk.20250628001   - Type: paper   - Read depth: abstract (full text read in survey 2)
#### What it does
PCAFOE: polar-code-aided EM-type ML frequency estimation with BP posteriors; (2048, 1024) BPSK, Eb/N0 0-5 dB,
|f| <= 2e-4 cycles/symbol (~ our half-cell at 1/10 [derived]); closer to the MCRB than Fitz. Journal version of Wu,
Chen, Bu, ITNEC 2020.
#### What we took / could take
Confirms that code-aided EM works only inside a cell (as our D0 DD Newton); no acquisition at |f| <= 0.03.
#### Used in
-

### Wu, Chen, Bu, "Polar Code-Aided Frequency Offset Estimation Algorithm in Satellite Covert Communication Carrier Synchronization", IEEE ITNEC 2020, 1340-1344, doi 10.1109/ITNEC48623.2020.9085165
- Link: https://pure.bit.edu.cn/en/publications/polar-code-aided-frequency-offset-estimation-algorithm-in-satelli   - Type: paper   - Read depth: abstract
#### What it does
First PCAFOE paper: polar-code-aided frequency estimation for short polar codes, RMSE better than traditional
algorithms (no numbers in the abstract).
#### What we took / could take
Not used (as Wu 2025).
#### Used in
-

### Man, Xi, Gao, Zhang, "A Novel Code-Aided Carrier Recovery Algorithm for Coded Systems", IEEE Commun. Lett., 2013, doi 10.1109/LCOMM.2012.121912.122278
- Link: https://doi.org/10.1109/lcomm.2012.121912.122278   - Type: paper   - Read depth: abstract
#### What it does
Coarse: maximise the mean |LDPC soft output| over the frequency, then interpolate; fine: decoder decisions. 8-PSK,
(1944, 972) LDPC, large CFO and phase at low SNR, "negligible" loss.
#### What we took / could take
Same structure as our Stage 2 + Stage 3; the interpolation part was tested and killed in D0 (expected_ref.md).
#### Used in
-

### Valles, Wesel, Villasenor, et al., "Carrier and Timing Synchronization of BPSK via LDPC Code Feedback", Asilomar 2006, doi 10.1109/ACSSC.2006.355154
- Link: https://doi.org/10.1109/acssc.2006.355154   - Type: paper   - Read depth: abstract
#### What it does
Pilotless: constraint-node feedback estimates frequency and timing; soft LDPC information recovers the carrier phase;
within 0.3 dB of perfect phase and timing.
#### What we took / could take
Supports soft feedback (A1) and loop iterations (A2).
#### Used in
-

### Noels et al., "A Theoretical Framework for Soft-Information-Based Synchronization in Iterative (Turbo) Receivers", EURASIP J. Wireless Commun. Netw. 2005, doi 10.1155/WCN.2005.117
- Link: https://doi.org/10.1155/wcn.2005.117   - Type: paper   - Read depth: abstract
#### What it does
Shows turbo synchronization is an instance of EM with soft posteriors; derives phase, CFO, timing and amplitude
estimators; turbo-coded 16-QAM.
#### What we took / could take
Theoretical basis for A1 (soft instead of hard symbols in DD / pns).
#### Used in
-

### Wymeersch, Moeneclaey, "Iterative Code-Aided ML Phase Estimation and Phase Ambiguity Resolution", EURASIP J. Adv. Signal Process. 2005, doi 10.1155/ASP.2005.981
- Link: https://doi.org/10.1155/asp.2005.981   - Type: paper   - Read depth: abstract
#### What it does
Iterative ML phase estimation and ambiguity resolution from MAP soft information, with convergence and
initialisation analysis; turbo codes; ambiguity resolved without pilots.
#### What we took / could take
Not used: our phase hypotheses + PiCode already resolve the ambiguity.
#### Used in
-

### "Iterative Carrier Phase Recovery Suited to Turbo-Coded Systems", IEEE Trans. Wireless Commun., 2004, doi 10.1109/TWC.2004.837407 (authors not read)
- Link: https://doi.org/10.1109/twc.2004.837407   - Type: paper   - Read depth: abstract
#### What it does
A-priori-probability-aided (APPA) ML phase estimation from turbo extrinsic LLRs, inside the decoding loop; variance near
the CRB at very low SNR; turbo BPSK / QPSK, AWGN.
#### What we took / could take
Supports A1 (extrinsic soft information as the reference).
#### Used in
-

### "Novel iterative APPA carrier phase recovery and detection for turbo-coded systems", ICCOMTA 2009, doi 10.1109/ICCOMTA.2009.5349142
- Link: https://doi.org/10.1109/iccomta.2009.5349142   - Type: paper   - Read depth: abstract
#### What it does
APPA with LLRs of parity and information bits; acquisition region +-30 deg -> +-40 deg at iteration 3.
#### What we took / could take
Supports A1 (more soft information widens the pull-in).
#### Used in
-

### "Early stopping scheme for iterative carrier synchronization of LDPC codes", PIMRC 2010, doi 10.1109/PIMRC.2010.5671809
- Link: https://doi.org/10.1109/pimrc.2010.5671809   - Type: paper   - Read depth: abstract
#### What it does
Stops the sync-decode iterations when the decoder output LLRs satisfy conditions; little loss, negligible extra cost.
#### What we took / could take
Already in use in spirit (stop at the first accepted decode).
#### Used in
-

### "Code-aided Carrier Synchronization via Soft Decision Feedback Based on Early Stopping Criterion", Acta Aeronautica et Astronautica Sinica, 2012
- Link: https://hkxb.buaa.edu.cn/EN/abstract/article/1000-6893/14674   - Type: paper   - Read depth: abstract
#### What it does
Soft decision feedback carrier sync with an SNR-based early stop; rate-1/2 LDPC; iterations -50 % at BER 1e-5,
< 0.15 dB loss with phase noise.
#### What we took / could take
Already in use in spirit; a stop rule for A2's loop if it is built.
#### Used in
-

### Fang, "Decoding Polar Codes via Weighted-Window Soft Cancellation for Slowly-Varying Channel", arXiv 1911.08763, 2019
- Link: https://arxiv.org/abs/1911.08763   - Type: paper   - Read depth: abstract
#### What it does
W2SCAN: SCAN decoding with a coarse channel-state estimate refined after each SCAN iteration (quadratic programming);
also a CRC-free verification of SCAN decoding. No numbers in the abstract.
#### What we took / could take
Precedent for using SCAN soft outputs to re-estimate a channel parameter: A1-b.
#### Used in
-

### Pillet, Condo, Bioglio, "SCAN List Decoding of Polar Codes", ICC 2020, arXiv 2001.11283
- Link: https://arxiv.org/abs/2001.11283   - Type: paper   - Read depth: abstract
#### What it does
L SCAN decoders on permuted factor graphs with a selection metric and early termination; about BPL performance at
lower complexity.
#### What we took / could take
Option for soft outputs if A1-b needs a list version; not needed for a first test.
#### Used in
-

### Sy, Knopp, "Enhanced BICM Receivers for Ultra-Reliable Low-Latency Short Packet Communications", arXiv 2408.08660, 2024-2025
- Link: https://arxiv.org/abs/2408.08660   - Type: paper   - Read depth: abstract
#### What it does
Joint estimation-detection metrics over ~4-symbol windows with sparse interleaved pilots; 5G polar / LDPC, QPSK; close
to perfect-CSI receivers.
#### What we took / could take
Not used: pilot-based, no CFO.
#### Used in
-
