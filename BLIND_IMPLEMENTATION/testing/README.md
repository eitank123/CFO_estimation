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

> **Adopted testing receiver (2026-11-17):** `testing_s11g` at R = 1/10, 0.15; `base25_qfix_fzs` (2/5) and
> `base2_qfix_fzs` (1/2) = q_fix + early stop. Gain over the presentation receivers, BLER unchanged: MACs per core
> -39 % (1/10), -32 ... -37 % (0.15), -17 % (2/5), -20 % at 1.5 dB (1/2). Table and competitor scoreboard:
> [../README.md](../README.md#current-state-2026-11-17), [results/scoreboard.md](results/scoreboard.md).

> **Before testing an idea, check [../DEAD_ENDS.md](../DEAD_ENDS.md)**: every dropped idea (search, acceptance, NN,
> channel format) with its evidence and what would justify reopening it.

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
| `plot_variants.py` | (not run since 2026-11-13: its plots `srch_*`, `k_nph4_*` were removed; the numbers are in the tables below) |
| `plot_curves.py` | full BLER vs SNR and MACs per core vs SNR of blind and every compared receiver (figures `results/plots/curves_*`, table `results/curves.md`) |
| `results/scoreboard.md` | required SNR / gap / MACs per core at the target BLERs, every compared receiver |
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
(plots removed 2026-11-13: experiments dropped / superseded; numbers below). With 0-8 baseline errors at
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
Full tables: `results/report_S.md` (`agg_S.py`; the `s_*` plots were removed 2026-11-13, superseded by the `cmp_*` plots). 64 000 paired packets per
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

## 2026-11-13: the testing receiver, fixed accounting, q_fix, decode dump and the decode-feedback NN

### Where it stands
| Item | Status | Result | Report |
|---|---|---|---|
| Phase accounting fix | **done** | the old count undercharged cells joining after a phase pruning; `old_acct` reproduces it, decisions identical | `results/expected_cnf.md` |
| Testing receiver `nofast15` (fast path off at <= 0 dB, 4 phases at R = 0.15) vs presentation, fixed accounting | **done** (t-cnf*) | 1/10: per core -25 ... -37 %, total -9 ... -18 %, BLER same. 0.15: per core -13 % (-4 dB) ... -32 %, +8 % at +1 dB; total -5 ... -13 % below -1 dB, +10 % / +33 % / +20 % at -1 / 0 / +1 dB; the -1 dB bump removed (0 / 400k; paired 12 fixed / 0 broken). Fast path off at 2/5, 1/2 is worse: kept there | `results/expected_cnf.md` (Measured) |
| `q_fix` (a candidate's phase th + qs[qb] pi/4) | **done, ADOPTED (user, 2026-11-13)** | 2/5 0.5 dB per core -14 %, total -10 %, 21 fixed / 8 broken (p = 0.024); 1/10, 0.15 -1 ... -5 %; 1/2 ~0. Does not remove the 0.15 -1 dB bump (17 -> 17 / 128k): the 4 phases do | `results/report_qfix_ddq.md` |
| `dd`, `dd_win4` with q_fix | **done, dropped** | 0 packets fixed at 7 points; 2/5 0.5 dB 8 fixed / 51 broken, per core +11 % | `results/report_qfix_ddq.md`, `results/expected_ddq.md` |
| Decode dump (`<key>_dump`, small_rx `dec_dump`) | **done** (t-deca, t-decb25, t-decb2, t-decbn) | one row per decode attempt + one per packet, 32k packets per point, noise-only 5600 frames | `results/report_nn_offline.md` (P0) |
| NN offline stage (heads A refine, B retry gate, C grid stop, D noise) | **done** | B is the only large win; A 2-4 %; C loses packets (not built); the path metric cannot replace rho (accepts 12 / 47 wrong CRC passes and 1046 / 1046 noise passes); logistic = MLP | `results/report_nn_offline.md`, `nn_offline.py` |
| Deployable retry gate (13 decoder-list / LLR features, one logistic per code rate) | **offline done** | replay on the test chunks: 0.15 -4 dB -12 % (0.1 % point) / -21 % (1 % point) per core, 2/5 0.5 dB -14 % / -24 %, 0 lost of 8000 each; <= 2 % elsewhere; oracle -30 % / -42 % | `results/nn_b_export.json`, `plots/thresholds/thr_gate_*.png` |
| Retry gate online (small_rx `nn_b`) | **done, NOT adopted** | 64k paired at 1/10 -5, 0.15 -4 / -3, 2/5 0.5, 1/2 2 dB. On the standard (scheduled) count: 1 % setting -9 % per core at 0.15 -4 and 2/5 0.5 dB, <= 2 % elsewhere, 0 fixed / 8 broken pooled (p = 0.008): rejected; 0.1 % setting <= 4.5 % per core, 0 / 3 broken: not worth it next to spec11 | `results/expected_nnb.md` (Measured) |
| Stricter speculative decode `spec11` (accept at rho > 1.1 thr) | **ADOPTED in the waterfall** (1/10 below -3.5 dB, 0.15 below -2.5 dB: run.py `testing_s11g`) | Above those SNRs it costs +3 ... +4 % per core (64k sweep, `results/expected_s11.md`), so small_rx `spec_snr` turns it off there. 1/10 -5 dB 1e6 paired: 209 vs 209 errors, 0 discordant, undetected 2 vs 2, per core -14.5 %, total -19.4 %. 0.15 -4 / -3 dB 64k: per core -6.9 / -4.5 %, total -10 / -8 %, 0 discordant. Noise only: 0 false alarms in either arm | `results/expected_spec.md`, `results/expected_spec1m.md` |
| Retry gate + spec11 together (comb10, comb15) | **done** | savings add (0.15 -4 dB: -16.3 % per core), but the gate is rejected, so not adopted | `results/expected_cap_pn_comb.md` |
| Phase-equivariant receiver without the interleaver (`*_eq`, BLIND_NOINT=1) | **done** | 2/5, 1/2: same BLER, per core -30 ... -40 %. 1/10, 0.15: BLER x1.6-17, 4-11 undetected per 64k (the rho check cannot reject a wrong pi/2 rotation): dropped there | `results/expected_eq.md` |
| Hard MAC cap (`*_cap2`, `*_cap1`) | **done** | +2 / 400k (0.15 -2.5 dB), +3 / 400k (2/5 1.5 dB), 0 / 128k (1/2 2.5 dB); mean MACs unchanged; noise-only packets stop at the cap, 0 false alarms | `results/expected_cap_pn_comb.md` |
| Wiener phase noise (BLIND_PN) | **done** | 1e-5 harmless; 1e-4: x3-3.6 BLER at 1/10, 0.15, x36 at 2/5; 3e-4: x100-235. The genie (no tracking) is worse than blind: no bound | `results/expected_cap_pn_comb.md` |
| Fair pilot reference (est3 CRC search in path-metric order, `PM+all`) | **done** | same waterfall BLER as the fixed order, floor 2-5x lower, undetected 3-5x fewer, per core +8 ... +36 %; top-3 / PM+3 variants lose x2-4.7 in the waterfall | `results/expected_fair.md` |

### The retry gate (small_rx flag `nn_b`)
- `nn_b = (path to results/nn_b_gate.json, frac)`, frac = 0.01 or 0.001; keyed by CODE rate (missing rate: no gate).
- After a main decode fails the CRC, the CA retry runs only if the logistic score of 13 features of that failed
  decode >= thr[frac]: pm0, pm_gap, pm_spread, pm_meanex (sorted list PMs), syn_w, n_rem, n_agree, agree_bits (CRC
  syndromes / agreement of the list paths), l_sum, l_mean, l_lt1, pm_norm (LLR magnitudes), sgn_agree (LLR signs vs
  the best path's codeword). No grid state, no re-encoding.
- thr[frac]: at most frac of the TRAIN successful retries would be skipped (the "1 %" / "0.1 %" operating points). The
  "perfect gate" in the plot is the oracle (skips exactly the failing retries): the upper bound.
- Cost charged per gated decode (`small_rx.GATE_MACS`): L K (list CRCs) + 3 N + N/2 log2 N + 26, as parallel serial
  work (/ 32 in crit_par). Counters `gate_calls`, `gate_skip`.
- Weights: `py BLIND_IMPLEMENTATION/testing/nn_b_export.py` (train = first 6 of 8 chunks of the dumps); plot:
  `plot_nnb.py`.

### Open decisions / next (review 2026-11-15)
1. Decided: spec11 in the waterfall (`testing_s11g`); 4 phases at 0.15 below 0.5 dB; the retry gate and `nofast_spec` (threshold 1.0) dropped.
2. User decision: the phase-equivariant format at 2/5 and 1/2 (-30 ... -40 % per core; no interleaver, checkpoint NN retrain, 400k confirmation).
3. Phase tracking / a segmented non-coherent metric: needed if the oscillators reach linewidth x Ts ~ 1e-4 (2/5 collapses). Also run the pilot receivers under the same phase noise (not done: the comparison under phase noise is one-sided).
4. Fair comparison at equal throughput: the pilot receivers get their 128 pilots on top of the N = 2048 code (12.5 % overhead not charged, ~0.5-0.7 dB). A rate-matched pilot system and the 24-pilot hybrid (A.16) re-run with the current receiver and cost model.
5. Still open from A.17.7: timing / burst sync, multipath, fixed point, noise-only false alarms at 1e6.

## The plots (`results/plots/`, kept 2026-11-13; superseded plots removed, their numbers stay in the reports)
| Plots | What they show | Script |
|---|---|---|
| `curves_bler_R*.png`, `curves_macs_R*.png` | BLER and MACs per core vs SNR: blind (adopted testing receiver) vs every compared receiver, one panel per system family | `plot_curves.py` |
| (`cmp_*`, `e4_*`, `pres_bler_*`, `ars_*`, `arsf_*`: deleted 2026-11-17, superseded by `curves_*`; `plot_cmp.py`, `plot_e4.py`, `plot_ars.py` regenerate them) | | |
| `cap/cap_<C>_R*.png` | BLER vs SNR under a hard cap C = 0.5 / 1 / 2 / 5 / 10 M MACs per core, with and without the cap, vs the pilot receivers | `plot_cap_snr.py` |
| `thresholds/thr_gate_*.png` | retry gate: MAC saving and BLER vs the share of retries skipped, the chosen settings | `plot_thresholds.py` |
| `thresholds/thr_spec_rho.png` | speculative decode: why the acceptance factor is 1.1 | `plot_thresholds.py` |
| `thresholds/thr_fastpath_*.png` | fast-path switch: MACs per core with it off vs on, per SNR | `plot_thresholds.py` |
| `nn_auc_headB.png`, `nn_pm_vs_rho.png` | NN offline: the retry-gate AUC per feature set; why the path metric cannot replace the re-encoding check | `nn_offline.py` |

## MACs per core: the standard count (user decision, 2026-11-13)
MACs per core = the scheduled critical path on the 32 decoder cores:
- R = 1/10, 0.15: one core per (cell, phase) hypothesis in the grid + 4 CA-SCL-8 decodes at once (32 cores / 8 paths)
  (small_rx counter `crit_par_h_d4a_macs`);
- R = 2/5, 1/2 (their joint decode already runs 4 cells at once): 4 decodes at once only (`crit_par_d4a_macs`).
Decisions, BLER and total MACs are unchanged; the 128-pilot receivers were already costed with 4 decodes at once. The
earlier count (`crit_par_macs`: one core per cell, decodes one at a time) is still logged and shown dotted for one round.
Effect on the testing receiver: -16 ... -21 % at 1/10, -20 ... -31 % at 0.15 (-7 % at +1 dB), -36 % at 2/5 0.5 dB,
-2 % at 2/5 1 dB, 0 at 1/2. The hard-cap runs (cap_core) still cap the earlier count (conservative: the same cap on the
scheduled count would be looser).
