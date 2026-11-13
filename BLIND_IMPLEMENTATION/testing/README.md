# testing/: re-encoding correlation experiments on the blind receiver

Goal (user task "Optimize the Blind CFO Receiver Using Re-Encoding Correlation"): find out whether information the
receiver already computes (list-1 SC codewords, CA-SCL list paths, the re-encoding correlation) can
1. **cut complexity** (average total MACs and MACs per core on 32 cores) at the same BLER, undetected-error rate and
   false-alarm rate, and/or
2. **lower BLER** at little or no extra cost.

The final receivers are the baselines and stay unchanged (`S blind final v2` for R = 1/10 and 0.15,
`S blind final 2/5, 1/2, best-first 32` for R = 2/5, `S blind final 2/5, 1/2` for R = 1/2). Every experiment is a
separate small_rx flag that defaults to the baseline behaviour; variants are compared on **paired packets** (same
seed, points and therefore the same data, CFO, phase and noise).

## Method

**Step 1: instrument the baseline (measurement only).** `small_rx` flag `s3dump` (set by `BLIND_IMPLEMENTATION/testing/run.py --dump`)
records, for every Stage 3 refinement, the best `s3dump_top` = 6 hypotheses of each candidate by the list-1
metric, with
- the list-1 path metric M and its rank,
- the correlation rho_sc of the list-1 (SC) hard-decision codeword with r at the hypothesis CFO,
- the distance to the true CFO and phase (mod pi),
- the outcome of a CA-SCL-8 decode of that hypothesis: CRC pass, re-encoding pass, correct data, the true packet
  anywhere in the 8 surviving paths, number of CRC-passing paths, rho of the chosen path,
- the half-packet coherent sums |C1|, |C2| and their phase difference (experiment J),

plus one row per packet (decoded right?, fast path?, total MACs, MACs per core, fast-path MACs, decode MACs). These
side decodes are outside the receiver's MAC count and decisions.

**Step 2: evaluate policies offline on the dump** (`BLIND_IMPLEMENTATION/testing/analyze.py`). The search stops at the first accepted
decode, so for ranking / screening / adaptive-T policies (A, B, C) and list re-ranking (F) the outcome of each
policy follows exactly from the recorded per-hypothesis outcomes: number of CA-SCL decodes until the first
acceptance, and whether that acceptance is right. No new simulation per policy.

**Step 3: real runs** for changes that create new decodes (G multi-candidate retry, H larger list), behind flags,
with BLER confidence intervals on paired packets and noise-only false alarms when search or acceptance changes.

Statistics: BLER differences use paired packets (McNemar-type counts of packets fixed / broken); zero observed
errors are reported as a 95 % upper bound (3 / n).

## Files
| File | Content |
|---|---|
| `run.py` | runs baselines / variants through blind_ber on paired packets; `--dump` for Step 1 |
| `analyze.py` | Step 2: failure classification, MAC breakdown, policy evaluation, plots |
| `agg_variants.py` | sums `blind_ber_<part>.json` per (rate, SNR, receiver): BLER with 95 % interval, total MACs, MACs per core, scoring / fast-path / decode MACs, decodes per packet, stage shares, undetected (`py BLIND_IMPLEMENTATION/testing/agg_variants.py srch10 srch15 ...`) |
| `plot_variants.py` | BLER and MACs plots of the R experiments and of K -> `results/plots/srch_*`, `k_nph4_*` (`py BLIND_IMPLEMENTATION/testing/plot_variants.py`) |
| `results/` | dumps, tables, plots |

## Status
Dumps (2026-11-11/12): t-dump10 (R = 1/10: -5 dB 100k packets, 16 errors; -4.5 dB 50k, 0 errors), t-dump15a +
t-dump15b@-1 (R = 0.15: -4 dB 50k, 199 errors; -3 dB 60k, 6; -1 dB 100k, 11). Reports:
`results/report_t-dump10.md`, `results/report_t-dump15a.md`.

| # | Experiment | Status |
|---|---|---|
| 1 | Baseline instrumentation: where MACs go, failure types | **done** (1/10, 0.15). MACs: search metrics / scoring ("rest") 44-66 %, CA-SCL decodes 15-25 %, fast path 11-32 %. Failures: Stage 2 (true CFO region never among the Stage 3 candidates) 14/16 at 1/10 -5 dB, 117/199 at 0.15 -4 dB, 6/6 at -3 dB, 10/11 at -1 dB; list 1 / 65 / 0 / 1; order/budget 1 / 17 / 0 / 0; selection 0 everywhere |
| A | Correlation ranking of Stage 3 hypotheses | **drop**: never better than the path metric (AUC 0.98-0.998 for both; equal or fewer right acceptances at T = 1-3) and costs a correlation per hypothesis |
| B | Correlation screening before CA-SCL | **drop**: thresholds t <= 0.5 screen out no hypothesis at all, so no decode is saved |
| C | Adaptive 1 / 2 / more hypotheses | **drop for now**: T = 1 saves 8 % of the decodes at 1/10 -5 dB (= ~1 % of MACs) and 39 % at 0.15 -4 dB (~10 % of MACs) but loses accepted candidates; T = 3 at 0.15 -4 dB could recover at most 17 of 199 errors for +39 % decodes |
| D | Cheap / progressive correlation | **drop**: moot, B screens nothing |
| E | Redundant work in the acceptance path | code audit, not done |
| F | Re-ranking the final CA-SCL list | **drop**: 0 hypotheses with the true packet in the list but another path chosen |
| G | Multi-candidate DD CFO retry | **not run**: works on Stage 3 candidates, but most failures never reach the true region (Stage 2), so its upside is <= the list + order failures (2 of 16 at 1/10 -5 dB) |
| H | Adaptive list size | **pending, low priority**: upside <= the "sync / list" failures (65 of 199 at 0.15 -4 dB, ~0-1 elsewhere) |
| I | Soft-decision refinement | not run (only if G shows gain) |
| J | Half-packet consistency check | **drop**: no wrong decode is accepted by the receiver; on side decodes wrong and right overlap (rho, |C1|, |C2|, phase) |
| K | R = 0.15: 4 phase hypotheses per cell at every SNR (`run.py` variant `nph4`, small_rx `nph` = 4) | **done, fixes the -1 dB bump** (nph15a -1 dB, nph15b 0 dB, 400k packets each, paired with b15c, seed 7203): -1 dB 72 -> 0 / 400k (72 fixed, 0 broken), 0 dB 9 -> 1 / 400k; per core -5 % at -1 dB, +1 % at 0 dB; total +1.5 % / +11 %. Noise-only false alarms not measured. See "Results vs predictions" |
| R1 | `dd`: code-aided CFO / phase in Stage 3 instead of the offset scoring | **done, 4 rates**: total MACs -5 to -10 % at 1/10 and 0.15, per core +1 to +9 %, BLER the same or worse (0.15 -4 dB: 428 vs 273 / 64k); at 2/5 and 1/2 BLER x1.75-2.6 and total MACs +3.5 % to x4.8 |
| R2 | `dd_k6` / `dd_k3`: R1 + coarser grid | **drop**: BLER x5-70 wherever errors occur (113 vs 0 / 64k at 1/10 -4 dB; 0 vs 0 only at 1/2 2.5 dB) and total MACs and MACs per core higher at every point |
| R3 | `win4`: early win at z > 4 | **done, 4 rates**: BLER unchanged (paired counts within +-1); total -13 % at 1/10 -5 dB, -8 % at 0.15 -4 dB, -3 to 0 % elsewhere; per core -2 to +6 % |
| R1+R3 | `dd_win4` | **done, 4 rates**: largest total saving at 1/10 and 0.15 (-12 to -21 %) but per core +0 to +9 % and BLER as R1; at 2/5, 1/2 the same as R1 |

R = 2/5 and 1/2 use the joint list decode (`refine_joint`), which the dump does not cover yet; they follow once
the R = 1/10 / 0.15 analysis shows which experiments are worth porting.

## R experiments: the re-encoded codeword inside the search (2026-11-12)
Paired runs (`run.py --rx base10 dd win4 dd_win4 dd_k6`): jobs `srch10` (R = 1/10, -5 and -4 dB, 64k packets per
receiver and point, seed 7701) and `srch15` (R = 0.15, -4 and -3 dB, 64k, seed 7702). New small_rx flag `s3_dd`
(default off) and the measurement counter `macs_score` (Stage 3 scoring MACs).

| # | Variant | What changes |
|---|---|---|
| R1 | `dd` | Stage 3 refinement: instead of scoring 5 CFO offsets x 3 phase sub-offsets (15 list-1 metric passes per candidate below -1 dB, 5 above), ONE list-1 SC pass at the cell hypothesis, its codeword re-modulated, z = r s*, 2 Newton steps (bf.code_aided) -> CFO and phase; CA-SCL on that hypothesis, then on the cell hypothesis (T = 2) |
| R2 | `dd_k6` | R1 + a coarser grid, 6 STEP instead of 4 (201 -> 134 cells): R1's wider capture should finish what the coarser grid leaves |
| R3 | `win4` | early win at z > 4 instead of 6 at the first checkpoint: the best cell is decoded at once; CRC + re-encoding check keep wrong accepts out, so a wrong early decode only costs MACs |
| R1+R3 | `dd_win4` | both |

**Predictions, written before the runs** (baseline at 1/10 -5 dB: 4.16 M total, 0.313 M per core; scoring is
~15 x 24.3k = 365k MACs per Stage 3 candidate, ~2-3 candidates per packet):
- **R1 dd**: total MACs -14 to -20 % at 1/10 -5 dB and 0.15 -4 dB (288k saved per candidate), less at -4 / -3 dB
  (fewer candidates); MACs per core about unchanged (+-3 %: the 15 scores ran in one parallel pass, the SC pass
  is also one pass). BLER unchanged within noise (+-20 %); at 0.15 -4 dB possibly a few % better ("list" failures
  from a better CFO / phase); risk: the true cell's SC codeword too poor for the DD estimate (then BLER up).
- **R2 dd_k6**: total MACs -30 % vs baseline, per core -10 to -15 %; BLER x2-4 worse at 1/10 -5 and 0.15 -4 dB,
  because the right cell now sits up to 2.25e-4 off (0.72 rad of drift at the packet edges) and stands out less
  at the checkpoints: more Stage 2 failures, which R1 cannot repair (it needs the cell among the candidates).
- **R3 win4**: total MACs -5 to +5 % (saved continuations vs. wasted early decodes of noise cells, noise maxima
  reach z ~ 3-4 among ~100 cells), per core -0 to -10 %; BLER unchanged (acceptance unchanged), a small risk that
  an early failed decode of the true cell at a poorer phase removes it from the later candidates.
- **R1 + R3**: roughly the sum: total -15 to -25 %, per core -0 to -10 %, BLER unchanged.

**R = 2/5 and 1/2** (added 2026-11-12, jobs `srch25`: 2/5 at 0.5 and 1 dB, 64k; `srch2`: 1/2 at 2 and 2.5 dB, 128k;
variants `dd_25 win4_25 dd_win4_25 dd_k3_25` / `..._2`). These rates refine 4 cells at once in one joint CA-SCL-16
decode (`refine_joint`), after scoring only 3 CFO offsets per cell (72k MACs per cell); R1 replaces that by 1 SC
pass + the code-aided sums (77k). R2 = grid 3 STEP instead of 2 (the checkpoint NN was trained on 2 STEP).
Predictions, written before the runs:
- **R1 dd**: no saving: total MACs +0 to +3 %, per core +0 to +3 %; BLER the same or slightly better (the
  code-aided CFO / phase is more precise than the best of 3 offsets).
- **R3 win4**: total and per core -0 to -10 % at 0.5 / 2 dB (lowest SNRs, most cells reach the later
  checkpoints), ~0 at 1 / 2.5 dB (most packets end in the fast path); BLER unchanged.
- **R2 dd_k3**: grid -33 %: total MACs -15 to -25 %, per core -10 to -20 %; BLER clearly worse (x2-5) at
  0.5 / 2 dB: a coarser grid plus a checkpoint NN outside its training grid.

### Results vs predictions (srch10 / srch15 / srch25 / srch2, nph15a / nph15b; 2026-11-12)
Errors / packets on paired packets (64k per point at 1/10, 0.15, 2/5; 128k at 1/2); MACs as mean total / mean per
core (32 cores, crit_par), in M. Tables: `py BLIND_IMPLEMENTATION/testing/agg_variants.py srch10 srch15 srch25 srch2`;
plots: `results/plots/srch_bler_R*.png`, `srch_macs_R*.png`, `k_nph4_*.png`. With 0-8 baseline errors at
1/10 -5 / -4 dB, 0.15 -3 dB, 2/5 1 dB and 1/2 2 / 2.5 dB, BLER differences of a few errors there are noise; the
part files hold counts only, so fixed / broken packets cannot be separated for the R runs.

| Rate, SNR | baseline | R1 dd | R3 win4 | R1+R3 dd_win4 | R2 dd + coarse grid |
|---|---|---|---|---|---|
| 1/10, -5 dB | 8; 4.131 / 0.3102 | 13; 3.838 (-7.1 %) / 0.3131 | 9; 3.585 (-13 %) / 0.3075 | 13; 3.254 (-21 %) / 0.3115 | 457; 4.647 / 0.447 |
| 1/10, -4 dB | 0; 2.987 / 0.2577 | 0; 2.708 / 0.2605 | 0; 2.955 / 0.2734 (+6 %) | 0; 2.638 / 0.2770 | 113; 3.190 / 0.303 |
| 0.15, -4 dB | 273; 7.368 / 0.6497 | 428; 6.960 / 0.7105 (+9 %) | 273; 6.813 / 0.6466 | 426; 6.384 / 0.7095 | 1961; 10.13 / 1.232 |
| 0.15, -3 dB | 7; 3.295 / 0.2817 | 7; 2.975 / 0.2834 | 7; 3.198 / 0.2950 | 7; 2.837 / 0.2971 | 513; 4.443 / 0.463 |
| 2/5, 0.5 dB | 116; 3.582 / 0.3976 | 302; 17.11 / 2.487 | 117; 3.504 / 0.3913 | 302; 17.10 / 2.491 | 676; 19.19 / 2.921 |
| 2/5, 1 dB | 5; 1.285 / 0.1299 | 10; 3.642 / 0.389 | 5; 1.285 / 0.1305 | 10; 3.651 / 0.392 | 54; 3.945 / 0.480 |
| 1/2, 2 dB | 12; 0.742 / 0.0849 | 21; 0.992 / 0.1228 | 13; 0.740 / 0.0848 | 22; 0.992 / 0.1231 | 58; 1.065 / 0.1424 |
| 1/2, 2.5 dB | 0; 0.577 / 0.0751 | 0; 0.597 / 0.0776 | 0; 0.577 / 0.0751 | 0; 0.597 / 0.0776 | 0; 0.591 / 0.0776 |

R2 is `dd_k6` (6 STEP) at 1/10, 0.15 and `dd_k3` (3 STEP) at 2/5, 1/2. Zero errors mean < 3 / 64k = 4.7e-5
(< 2.3e-5 at 128k), 95 %. Undetected errors: 0 for every baseline; 1 each for dd, dd_win4, dd_k6 at 0.15 -4 dB,
win4 and dd_k6 at 1/10 -5 dB, dd and dd_win4 at 2/5 0.5 dB.

**R1 dd at 1/10, 0.15.** Predicted: total -14 to -20 % at 1/10 -5 / 0.15 -4 dB, per core +-3 %, BLER unchanged
(risk: SC codeword too poor -> BLER up). Measured: total -7.1 % / -9.3 % at 1/10 -5 / -4 dB and -5.5 % / -9.7 % at
0.15 -4 / -3 dB; per core +1 % except +9 % at 0.15 -4 dB; BLER 13 vs 8 (not significant) at 1/10 -5 dB, 428 vs 273
at 0.15 -4 dB (95 % intervals [6.1e-3, 7.4e-3] vs [3.8e-3, 4.8e-3], disjoint), equal at -3 / -4 dB. Mechanism: the
saving is smaller because Stage 3 scoring is only 10.5 % (1/10 -5 dB: 0.434 of 4.131 M, ~1.2 candidates per packet
at 365k, not 2-3) to 16 % (0.15 -4 dB: 1.154 M) of the total; dd removes ~70 % of it (0.434 -> 0.132 M), 70 % of
10.5 % = 7.3 %, matching the measured 7.1 %. At 0.15 -4 dB the decodes grow (10.14 -> 11.85 per packet, decode MACs
1.89 -> 2.21 M), so per core rises 9 %: extra serial decodes replace scores that ran in one parallel pass. The CFO
estimate is better (RMSE 7.1e-5 -> 4.9e-5 at 1/10 -5 dB, 5.9e-5 -> 5.2e-5 at 0.15 -4 dB), so the BLER loss at
0.15 -4 dB is the predicted risk (a poor SC codeword misleads the code-aided estimate) rather than CFO precision;
this mechanism is inferred from the 2/5 counters below, not measured separately at 0.15.

**R1 dd at 2/5, 1/2.** Predicted: no saving (+0 to +3 %), BLER the same or slightly better. Measured: BLER x2.6 at
2/5 0.5 dB (302 vs 116), x2 at 1 dB (10 vs 5), x1.75 at 1/2 2 dB (21 vs 12); total x4.8 / x2.8 at 2/5 0.5 / 1 dB,
+34 % at 1/2 2 dB, +3.5 % at 2.5 dB; per core x6.3 at 2/5 0.5 dB (2.487 vs 0.398 M). At 2/5 0.5 dB the decodes go
from 6.65 to 49.5 per packet, Stage 2 acceptances fall from 39.4 % to 20.8 % of the packets and the rescue (stage 5)
rises from 0.2 % to 17.8 %; wrong CRC passes rise from 71 to 712 (711 caught by the re-encoding check) and 5 right
decodes are rejected by the check. Mechanism: the SC pass runs at the raw cell hypothesis, up to ~1 STEP off, with
the cell phase not re-estimated (phase4); near threshold its codeword is poor, the code-aided estimate fails, and
the packet falls through to the rescue. The CFO RMSE of the accepted packets still improves slightly (4.3e-5 ->
3.9e-5 at 2/5 0.5 dB).

**R2 coarser grid.** Predicted: total -30 % (1/10, 0.15) / -15 to -25 % (2/5, 1/2), per core -10 to -20 %, BLER
x2-5. Measured: BLER x57 at 1/10 -5 dB (457 vs 8), 113 vs 0 at -4 dB, x7.2 / x73 at 0.15 -4 / -3 dB, x5.8 / x11 at
2/5 0.5 / 1 dB, x4.8 at 1/2 2 dB, 0 vs 0 at 1/2 2.5 dB; MACs higher at every point (total +2 % to x5.4, per core
+3 % to x7.3). Mechanism: the true cell is lost in Stage 2 more often (1/10 -5 dB: Stage 3 share 0.5 % vs 0.1 %,
decodes 6.9 vs 3.3 per packet), and the extra decodes / rescue outweigh the 33 % grid saving. The MAC prediction
had the wrong sign and the BLER loss is far larger than predicted.

**R3 win4.** Predicted: total -5 to +5 % (1/10, 0.15), -0 to -10 % (2/5 0.5, 1/2 2 dB), per core -0 to -10 %, BLER
unchanged. Measured: BLER unchanged (9 vs 8, 273 = 273, 7 = 7, 117 vs 116, 5 = 5, 13 vs 12, 0 = 0); total -13 % at
1/10 -5 dB (more than predicted), -1 % at -4 dB, -7.5 % / -2.9 % at 0.15 -4 / -3 dB, -2.2 % at 2/5 0.5 dB, ~0 at
2/5 1 dB and 1/2; per core -2 to -0.1 % at the lowest SNRs but +6 % at 1/10 -4 dB and +5 % at 0.15 -3 dB.
Mechanism: early decodes save search continuations (1/10 -5 dB: the MACs outside scoring, fast path and decodes
fall 2.31 -> 1.58 M) but add decodes (3.27 -> 3.91 per packet at -5 dB, 3.04 -> 3.62 at -4 dB); on the critical path
the extra early decodes are serial, so per core rises where few continuations are left to save.

**R1 + R3.** Predicted: total -15 to -25 %, per core -0 to -10 %, BLER unchanged. Measured: total -21 % / -12 % at
1/10 -5 / -4 dB, -13 % / -14 % at 0.15 -4 / -3 dB; per core +0.4 % to +9 %; BLER as R1 (13, 0, 426, 7). At 2/5 and
1/2 it equals R1 (same BLER and MACs within 1 %). The savings add roughly as predicted; the per-core cost and the
0.15 -4 dB BLER loss come from R1 / R3 as above.

**K nph4 (R = 0.15, 4 phase hypotheses at every SNR; 400k packets per point, paired with b15c, seed 7203).**
Hypothesis: the -1 dB errors come from the 4 -> 2 phase switch at snr >= -1. Smoke: +3 % total, same per core.
Measured: -1 dB 72 -> 0 / 400k (< 7.5e-6, 95 %; 72 fixed, 0 broken), 0 dB 9 -> 1 / 400k (8 or 9 fixed, 0 or 1
broken: per-packet outcomes are not stored). Total MACs 2.373 M at -1 dB (+1.5 % vs 2.338 M of bm15b, +0.5 % vs
2.362 M of the paired b15c), 1.764 M at 0 dB (+11 %); per core 0.2236 vs 0.2357 M (-5 %) at -1 dB, 0.1711 vs 0.1690
M (+1 %) at 0 dB; decodes per packet 2.71 vs 3.03 (bm15b; 3.12 in b15c) at -1 dB. Per-core baseline from bm15b
(320k packets; b15c has no crit_par_macs). Undetected 0 / 1 (nph4) vs 1 / 2 (b15c) at -1 / 0 dB. Mechanism (consistent
with, not proven by, the counters): with only 2 phases a noisy 4th-power phase leaves the true cell's hypotheses
too far off in phase, so it misses the Stage 3 candidates (10 of 11 analysed -1 dB failures were Stage 2 failures);
the baseline's merged stage counters show 1.2e-3 of the packets still undecoded after Stage 2 at -1 dB vs 3.4e-4 at
-3 dB (`est3/plots/stages_R0.15.png`), while nph4 ends every -1 dB packet in Stage 1 or 2 (17.1 % / 82.9 %). With
fewer decodes per packet, per core falls at -1 dB despite the extra phases. Not measured: noise-only false alarms with nph4.

## S experiments: the fast path, core scheduling and a cheaper early decode (2026-11-12)
Variants in `run.py`: `nofast` (fast-path decode + retry skipped: `s0_snr = 99`; its FFTs stay), `nofast_spec`
(+ `win_spec = 4`: for 4 < z <= 6 at a checkpoint, one speculative CA-SCL decode without the code-aided retry; the
cell stays eligible as a later candidate), `nofast_nph4`, `nph15` (4 phases for code rate 0.15 only, keyed by code
rate). New measurement-only counter `crit_par_h_macs`: MACs per core if the grid gives every (cell, phase)
hypothesis its own core (each with its own de-rotation) instead of one core per cell; decisions identical.
Paired with the R runs (seeds 7701 / 7702, same chunking): the baseline arm must reproduce 8 / 0 errors at 1/10
-5 / -4 dB and 273 / 7 at 0.15 -4 / -3 dB.

**Predictions, written before the runs** (strategist):
- **S1 nofast**: per core -25 to -35 % and total -8 to -15 % at 1/10 -5 ... -1 dB; at 1/10 0 dB per core -15 to
  -30 %, total -5 to +8 % (the fast path delivers 42 % there); 0.15 -4 dB per core -12 to -16 %, total ~-5 %;
  0.15 -3 / -1 dB per core -25 to -35 %, total -10 to -14 %. BLER unchanged within noise.
- **S1b per-hypothesis cores** (`crit_par_h` vs `crit_par`): crit_grid -20 to -40 %, crit_par -8 to -18 % at
  1/10 -5 dB, less elsewhere; BLER and total MACs identical by construction (a scheduling change, reported apart).
- **S2 nofast_spec vs nofast**: total -12 to -16 % at 1/10 -5 dB, -6 to -9 % at 0.15 -4 dB, 0 to -3 % at 1/10 -4 /
  0.15 -3 dB; per core -1 to -4 % / -1 to -3 % / 0 to +2 % (win4 was +5-6 %); decodes per packet +0.1 to +0.3;
  BLER unchanged.
- **S3 nph15 (R = 0.15 setting)**: noise-only false alarms 0 / 10k in both arms at -1 and 0 dB; at +1 dB total +5 to
  +12 %, per core within +-3 %, 0 errors in both.

### S results vs predictions (analysis 2026-11-12)
Full tables: `results/report_S.md` (`agg_S.py`, `plot_S.py`; plots `results/plots/s_*.png`). 64 000 paired packets per
point and receiver; the baseline arm reproduces the R runs chunk by chunk (8 / 0 at 1/10 -5 / -4 dB, 273 / 7 at 0.15
-4 / -3 dB, identical MACs). `frame_err` equals the count of packets without an accepted and right decode at every
point, so the different "first decode" delivery rule under nofast changed nothing.
- **S1 nofast: hit at 1/10 -5 dB and at 0.15, under-predicted elsewhere.** Per core -30.5 / -36.6 / -38.0 / -37.1 /
  -29.7 % at 1/10 -5 / -4 / -3 / -1 / 0 dB (predicted -25 to -35 %, 0 dB -15 to -30 %); total -12.1 / -16.8 / -18.1 /
  -18.2 / -9.4 % (predicted -8 to -15 %, 0 dB -5 to +8 %). 0.15: -15.2 % / -6.5 % at -4 dB, -34.9 % / -14.7 % at
  -3 dB; nofast_nph4 vs nph4 -35.2 % / -12.2 % at -1 dB and -26.0 % / +3.1 % at 0 dB. Errors 8 vs 8, 275 vs 273,
  7 vs 7, 0 elsewhere.
- **S1b crit_par_h: hit at 1/10 -5 dB** (-11.4 % for the baseline, grid part -24.6 %; -16.5 % under nofast); "less
  elsewhere" only partly (-12.5 % at 1/10 -4 / -3 dB, -6.4 % at 0.15 -4 dB, -8.7 % at 1/10 0 dB).
- **S2 nofast_spec vs nofast: miss on the size (more saving), decodes hit.** Total -18.0 % / per core -10.0 % at 1/10
  -5 dB (predicted -12 to -16 % / -1 to -4 %), -9.3 % / -4.0 % at 0.15 -4 dB, -5.8 % / -1.2 % at 1/10 -4 dB, -7.0 % /
  -2.1 % at 0.15 -3 dB; +0.11 to +0.16 decodes per packet. 9 vs 8 errors at 1/10 -5 dB; the extra one is an
  undetected error (1 / 64 000), the only one in the S runs.
- **S3 nph15: hit.** Noise only 0 / 11 200 accepted in both arms at -1 and 0 dB (< 2.7e-4 each, 95 %; chunks of 625
  run to 700 packets); +1 dB total +10.1 %, per core +2.1 %, 0 / 64 000 errors in both. A noise-only packet costs
  237 M / 33.9 M per core (baseline) vs 288 M / 35.1 M (nph15).
