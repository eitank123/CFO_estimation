# Checkpoint-based local CFO refinement (team-leader TODO, 2026-11-15): predictions before any code

## Task
Can a local CFO refinement at the Stage 2 -> Stage 3 transition (4th-power Newton, parabolic interpolation of the
checkpoint path metric, early decision-directed Newton, or an adaptive mix) replace part of the Stage 3 refinement grid
(05, 5.1: 5 CFO offsets x 1 or 3 phases, all scored with the full list-1 metric, best T = 2 decoded) and cut MACs at the
same BLER, or recover packets the grid loses? Baseline = the testing receiver (run.py `testing_s11g` at 1/10, 0.15;
`base25_qfix` / `base2_qfix` at 2/5, 1/2), kept unchanged and paired. No point below -5 dB (user, 2026-11-15).

## What we already know (DEAD_ENDS.md, measured)
- Refinement scoring (`macs_score`) is 8-19 % of the total MACs at 1/10, 0.15 below +1 dB and 7-11 % at 2/5, 1/2
  (testing receiver, 64k-128k per point: s11, qfx, ddq parts). The search grid is 60-80 % of the total, decodes 5-34 %.
  So replacing the WHOLE refinement could save at most ~8-19 % total; per core it is cheaper still (the offsets run
  in parallel on the 32 cores). Any method must pay for its own LLR recomputation at the new CFO.
- Most remaining errors at the hard points are Stage-2 failures (the true region never becomes a candidate); refinement
  changes cannot fix them. Upper bound on BLER gain = packets whose true cell IS a candidate but are lost in Stage 3.
- Decision-directed refinement in Stage 3 (`dd`, s3_dd) fixed 0 packets and broke 8-51; the code-aided retry already
  runs DD Newton x2 after a CRC failure. TODO 3 reopens dd only for a NEW reason: as a cheaper REPLACEMENT of the grid
  (complexity), not to fix packets.
- At 1/10 the 4th-power periodogram is nearly uninformative below 0 dB (true cell mean rank ~90 of 201).

## Plan
D0 (diagnostic, log-only, flags off = bit-identical): for every candidate cell that enters Stage 3, log the true residual
(f_true - f_cell, in STEP), the refinement grid's chosen offsets and their list-1 metrics, and what each method would
estimate: (1) 4th-power Newton, 1 and 2 iterations, from the cell centre, clamped to the cell; (2) parabola through the
checkpoint metrics of the cell and its two neighbour cells (free when stored) and through the grid's own 5 offsets;
(3) DD Newton from the list-1 SC codeword at the cell centre; plus whether the true cell was a candidate but the packet
was lost in Stage 3. Points: 1/10 -5 dB, 0.15 -4 / -3 dB, 2/5 0.5 dB, 1/2 2 dB; 8k packets each.
Then build only the methods that D0 shows can save >= 5 % total or fix packets, each with the grid as fallback, and run
64k paired (400k for any BLER claim) against the baseline.

## Predictions (D0)
| Method | CFO error after refinement (rms, in grid-offset units of 1 STEP) | Can replace grid offsets? |
|---|---|---|
| Baseline grid (5 offsets) | <= 0.5 STEP by construction when the true cell is the candidate | - |
| 4th-power Newton (TODO 1) | 1/10, 0.15 <= 0 dB: worse than the grid (noise-dominated, > 1 STEP, wrong local maxima often); 2/5, 1/2: ~0.3-0.6 STEP | no at 1/10, 0.15; maybe at 2/5, 1/2, where the fast path already decodes most packets |
| Checkpoint-PM parabola, neighbour cells (TODO 2) | 0.5-1 STEP (the metric is smooth over ~3 cells: lobe width ~ 1/(N c)), unbiased when the true cell is the best | partly: scoring 2 offsets around the parabola instead of 5 -> total -3 ... -8 %, per core <= 3 % |
| Parabola on the grid's own offsets (refine the refined) | 0.2-0.4 STEP | adds nothing to BLER (grid already within 0.5 STEP) |
| DD Newton from the list-1 codeword (TODO 3) | right when the SC codeword is mostly right (high z), useless otherwise; costs one pass + LLRs | no BLER gain (as dd); complexity only if it replaces >= 3 offsets |
- BLER upper bound: packets with the true cell among the candidates but lost in Stage 3: <= 15 % of errors at 1/10 -5,
  0.15 -4 dB (most failures are Stage 2), so any BLER gain is <= x0.85 there.
- Kill: a method whose rms is not below 1 STEP at the point, or whose saving after its own cost is < 3 % total, is
  dropped (added to DEAD_ENDS with the D0 numbers).

## Code review (2026-11-15): GO with fixes (applied)
ddb starts at the grid's best hypothesis; MAC costs: use_score = derot + m_met, use_dec = llr, +phase4 for m1/m2; m2a takes
the nearest phase and the latest checkpoint all 3 cells reached; hd = max(h, 1 - h); decode-argument copies; `nearest`
flag (|res| <= k/2: true cells overlap at k = 2). Analysis rules: split rows by tag (main: win 1, spec 2, s2cand 3,
final32 4, early_z 7; rescue: post 5, fine_last 6), dedupe repeated cells, savings over ALL refined rows.

## Smoke (rd-smoke, 400 packets per point, baseline and _rd arms on the same packets): PASS
EVAL DONE x3 + ALL DONE, no Traceback. Baseline vs _rd: 0 differences in any counter (errors, decodes, metric evals,
every MAC / crit field) over 20 chunk pairs: the diagnostic is log-only. First look (main tags, nearest true cell,
right branch; rms residual in STEP, share within 0.5 STEP; 140-262 rows per point, screening only):
| Point | cell centre | grid best | 4th-power Newton 1 / 2 | PM parabola (cells) | parabola (grid) | DD Newton (centre cw) | DD Newton (best cw) |
|---|---|---|---|---|---|---|---|
| 1/10 -5 dB | 1.12 (0.24) | 0.78 (0.57) | 1.35 / 1.24 | 0.67, 88 % missing | 0.73 (0.64) | 0.32 (0.89) | 0.29 (0.91) |
| 0.15 -4 dB | 1.05 (0.24) | 0.71 (0.61) | 1.20 / 1.14 | 0.79, 70 % missing | 0.64 (0.71) | 0.42 (0.83) | 0.32 (0.92) |
| 0.15 -3 dB | 1.14 (0.24) | 0.57 (0.72) | 1.36 / 1.27 | 0.77, 96 % missing | 0.56 (0.83) | 0.25 (0.95) | 0.22 (0.96) |
| 2/5 0.5 dB | 0.55 (0.53) | 0.42 (0.79) | 0.64 / 0.61 | 0.37, 31 % missing | 0.31 (0.91) | 0.18 (0.99) | 0.17 (0.99) |
MACs per refined cell: grid 0.36-0.40 M (1/10, 0.15), 0.09 M (2/5); DD from the centre codeword 0.08 M; 4th-power Newton
0.025 M; parabola ~0. Early reading: 4th-power Newton is WORSE than the cell centre at the low rates (as predicted);
the checkpoint-PM parabola mostly lacks stored neighbours (coarse start / pruning); DD Newton from the list-1 codeword
at the cell centre is 2-3x more accurate than the grid's pick at 1/5 of its cost on true cells — the candidate to test
online as a grid replacement (decode at the DD estimate, grid as fallback). Full D0 (rd1, rd2: 8k per point) next.

## D0 measured (rd1, rd2: 8k packets per point; 2026-11-15; EVAL DONE + ALL DONE, no Traceback)
rms residual in STEP on main-tag rows of the nearest true cell, right branch (share within 0.5 STEP):
| Point | rows | cell centre | grid best | 4th-power Newton 1 / 2 | PM parabola (cells; missing) | parabola (grid) | DD Newton centre cw / best cw |
|---|---|---|---|---|---|---|---|
| 1/10 -5 dB | 4870 | 1.10 (0.28) | 0.79 (0.57) | 1.35 / 1.25 | 0.67 (86 % missing) | 0.75 | 0.33 (0.89) / 0.31 (0.92) |
| 0.15 -4 dB | 5575 | 1.07 (0.29) | 0.73 (0.59) | 1.34 / 1.24 | 0.81 (59 %) | 0.68 | 0.42 (0.83) / 0.35 (0.92) |
| 0.15 -3 dB | 4385 | 1.13 (0.27) | 0.55 (0.70) | 1.32 / 1.25 | 0.64 (96 %) | 0.49 | 0.25 (0.96) / 0.28 (0.97) |
| 2/5 0.5 dB | 2805 | 0.53 (0.57) | 0.45 (0.73) | 0.57 / 0.53 | 0.38 (32 %) | 0.33 | 0.18 (0.98) / 0.18 (0.99) |
| 1/2 2 dB | 152 | 0.55 (0.51) | 0.37 (0.80) | 0.46 / 0.42 | 0.35 (0 %) | 0.24 | 0.14 (1.0) / 0.13 (1.0) |
MACs per refined cell: grid 0.36-0.40 M (1/10, 0.15), 0.09 M (2/5, 1/2); DD from the centre codeword 0.08 M (+ 0.026 M to
score / 6k to decode at the estimate); 4th-power Newton 0.025 M; parabolas ~0.
Packets lost in Stage 3 (a true-cell candidate was refined but the packet failed or was wrong): 1/10 -5: 0 of 0 fails;
0.15 -4: 11 of 30 fails; 0.15 -3: 0 of 1; 2/5 0.5: 13 of 20; 1/2 2: 3 of 3 (8k each).
- TODO 1 (4th-power Newton): KILL — worse than not refining at all at 1/10, 0.15 (1.24-1.35 vs 1.07-1.13 STEP), no
  better than the grid at 2/5, 1/2. (Prediction: HIT.)
- TODO 2 (checkpoint-PM parabola): KILL in this form — the neighbour cells' metrics are missing for 59-96 % of the
  candidates at 1/10, 0.15 (coarse start, phase pruning, the z-test drops them); where present, 0.64-0.81 STEP, not
  better than the grid's pick. The grid parabola refines the grid's pick slightly (0.49-0.75) but saves nothing.
- TODO 3 (DD Newton from the list-1 codeword at the cell centre): 2-3x more accurate than the grid's pick (0.25-0.42 vs
  0.55-0.79 STEP at 1/10, 0.15; 0.14-0.18 vs 0.37-0.45 at 2/5, 1/2) at ~1/4 of the grid's MACs at 1/10, 0.15 (equal at
  2/5, 1/2). Prediction MISS (expected no use): unlike `dd` (which re-decoded at the DD estimate AFTER the grid), here it
  REPLACES the grid. GO for an online test at 1/10, 0.15: decode at the DD estimate (+ its 2 best phase offsets), fall
  back to the grid when the CRC / re-encoding check fails. Expected total MACs -5 ... -14 % (refinement scoring is 8-19 %
  of the total), per core unclear (the grid's offsets run in parallel on the cores; DD is one SC pass + Newton in
  series): must be measured. BLER risk: the decode at the DD estimate must not miss packets the grid's T = 2 decodes
  catch (fallback covers it, at a cost).
- Stage-3 losses are larger than predicted (<= 15 %): 37 % of failures at 0.15 -4 dB and 65 % at 2/5 0.5 dB had a true-cell
  candidate refined. A better refinement (DD) could also fix some of those: measured online.
