# F3 (list-marginalised checkpoint metric) and F5 (frozen-bit abort inside CA-SCL-8): predictions 2026-11-15, before code
Source: `lit_polar_sync.md` F3, F5 (literature scout, 2026-11-15). Queued by the user 2026-11-15. Neither is in
DEAD_ENDS: the frozen-only cell ranking (dead) is a different metric from F3; the post-decode retry gate (dead) is a
different test from F5 (inside the decode, per path, absolute). No point below -5 dB.

## F3: list-marginalised metric for ranking the grid cells
Metric of a (cell, phase) hypothesis = -log sum_l exp(-PM_l) over the L_e surviving paths of an SC list decode
(L_e = 1 is today's list-1 path metric), full length (as the earlier rank check), and at the last checkpoint (c = 3/4).
Offline rank harness (`lit_checks.py --check rank`, 201 cells x 4 phases, 2000 packets per point, same packets for every
L_e): P(rank 1), P(rank <= 4) of the true cell, and the mean metric gap to the best wrong cell.
| Point | today (L_e = 1): P(rank <= 4) | prediction L_e = 2 / 4 / 8 |
|---|---|---|
| 0.15 -4 dB | 0.9725 | 0.974 / 0.976 / 0.977 (+0.002 ... +0.005) |
| 1/10 -5 dB | 0.998 | 0.998 ... 0.999 (ceiling) |
| 0.15 -3 dB | 1.0 | 1.0 |
- Why small: at these rates ~85-90 % of the leaves are rate-0 / REP (frozen), where every list path pays the same
  frozen-bit penalty; marginalising only helps on the ~200-300 information bits, and the misses are mostly packets where
  the right cell's metric is simply worse (noise), not a list artefact. Yuan et al.'s 3.5x is for N = 128 with few
  frozen bits per information bit.
- Cost if used: L_e x the remaining partial pass for the last-checkpoint survivors only (~32-64 hypotheses): +10 ... +40 %
  of the search MACs per core for L_e = 4.
- Go online (flag at the last checkpoint, 64k paired) only if P(rank <= 4) at 0.15 -4 dB rises by >= 0.005 (from the
  survey). Predicted: NO GO (below the gate).
- Gate made precise after review (2026-11-15): on the c = 3/4 checkpoint rank (`ck_L*`; full length only as context),
  paired per packet vs L_e = 1 (McNemar on "true cell in the top 4": fixed b vs broken c, p < 0.05 AND b - c >= 10 of
  2000), and the cost of L_e x the list decode of every surviving hypothesis at the checkpoint must be named next to it.
  L_e = 1 reproduces the old rank run per packet only within float rounding (+-1-2 near-tie packets): checked through
  `ranks_ref` (the old summation), not through the P value.

## F5: frozen-bit abort inside the CA-SCL-8 decodes
Per list path a frozen-only path metric (penalties at frozen positions only), normalised by the number of frozen bits
seen; a path is pruned when it exceeds a threshold, and the decode stops when all paths are pruned. Offline first:
a decode dump with every path's frozen-only metric at 1/4, 1/2, 3/4 of the frozen set, for right decodes (true cell,
CRC pass) and wrong-candidate decodes; ROC per checkpoint.
| Point | wrong-candidate decodes stoppable at <= 1e-4 loss of right decodes | saving |
|---|---|---|
| 0.15 -4 dB | 40-70 % of wrong decodes, stopped at ~1/2 of the frozen set | total -5 ... -10 %, per core -3 ... -8 % (decodes are ~25 % of total) |
| 2/5 0.5 dB | 30-60 % (fewer frozen bits per decode) | total -3 ... -8 % |
| 1/10 -5, 0.15 -3, 1/2 2 dB | few failing decodes | <= 2 % |
- Risk: right decodes at low SNR have large frozen penalties early (the retry gate lost 8 right packets); the threshold
  must keep >= 1 - 1e-4 of right decodes and is confirmed on 400k paired packets.
- Go online only if the offline saving at the 1e-4 point is >= 5 % total at 0.15 -4 or 2/5 0.5 dB.

## Order
F3 offline harness now (separate file, `lit_checks.py`); F5 dump after the refinement diagnostic (expected_ref.md D0)
has finished its edits of the decoder files.

## F3 measured (lm15a, lm15b, lm10; 2026-11-15)
Logs ALL DONE; lm15a and lm10 each lost 1 of 16 chunks to the fail-fast check (FastSCL L_e = 1 vs fs_.metric relative
difference 2.7e-3 / 4.3e-3 on one packet: a rare FastSCL edge case to find; the other 15 chunks = 1875 packets are valid).
Validity: `ranks_ref` equals the old rank run (t-lit-rk*) in 5750 / 5750 packets and full L_e = 1 equals it too.
P(true cell in the top 4), paired per packet vs L_e = 1 (McNemar on rank <= 4):
| Point | c = 3/4 checkpoint: L_e 1 -> 2 / 4 / 8 | fixed / broken (L_e 8) | full length: L_e 1 -> 8 |
|---|---|---|---|
| 0.15 -4 dB (1875) | 0.9744 -> 0.9947 / 0.9979 / 0.9989 | 46 / 0 (p = 3e-14); L_e 2: 40 / 2 | 0.9717 -> 0.9989 (51 / 0) |
| 0.15 -3 dB (2000) | 1.0 -> 1.0 | 0 / 0 | 1.0 |
| 1/10 -5 dB (1875) | 0.9984 -> 1.0 | 3 / 0 (p = 0.25) | 0.9984 -> 1.0 |
P(rank 1) at 0.15 -4 dB (checkpoint): 0.860 -> 0.878 / 0.882 / 0.882.
- vs prediction (+0.002 ... +0.005, NO GO): MISS — the gain is +0.020 (L_e 2) ... +0.025 (L_e 8), 5x the gate, highly
  significant. GO for the online test: re-rank the survivors of the last checkpoint by the list-marginalised metric
  (L_e = 2 first: most of the gain at the lowest cost; L_e = 4 as a variant), 64k paired at 0.15 -4 / -3.5 dB and
  1/10 -5 dB, then 400k. The rank gain does not map 1:1 to BLER (the receiver also tries the best 32 and rescues):
  expected BLER effect at 0.15 -4 dB: -20 ... -50 % of the Stage-2 failures [to be measured]. Cost: L_e x the list
  decode of the surviving (cell, phase) pairs up to c = 3/4 — to be counted in MACs per core.

## F5 measured (fz1a/b, fz2a/b, fz3; 2026-11-15)
Validation: 6 parts (t-fz1a, 1b, 2a, 2b, 3a, 3b), logs EVAL DONE + ALL DONE, no Traceback; 16 chunks each, unique
chunk seeds (no duplicates across parts), smoke parts excluded; dump packets = JSON frames, dump rows per packet =
g_n_rows everywhere. BLER (T receiver): 0.15 -4 dB 157/32000 = 4.9e-3, 2/5 0.5 dB 65/32000 = 2.0e-3, 1/10 -5 dB
1/8000, 1/2 2 dB 1/8000; 0 undetected; no pns rows, retry gate off. Scripts: `testing/fz_load.py`, `testing/fz_analyze.py`
(-> `results/fz_f5.json`), `testing/plot_fz.py`.
Method: rule "stop the decode at checkpoint c when min over alive paths of the metric > t". Right = the DELIVERED
decode(s) of a right packet (its out-0 rows of the latest call with an out-0 row); a packet is lost when all of them
stop. A stopped decode = a CRC failure, so the rest of the flow is unchanged (CA retry CFO comes from the SC pass).
t = the (k+1)-th largest delivered score, k = 0 / floor(1e-4 n) = 3 / floor(1e-3 n) = 31 lost (in-sample), plus a
half-split check (t from part a applied to part b and back, pooled). MACs: fz_profile.saved at the checkpoint (pn / pl
rounded UP to the end of the rate-0 node they sit in) per stopped non-delivered decode; per core: a d4a round
(4 decodes) shortens by the min of its rows' crit savings (only if every row of the round stops). Denominators:
standard per core (crit_par_h_d4a at 0.15, 1/10; crit_par_d4a at 2/5, 1/2). CA-SCL decodes are 19.9 % (0.15 -4),
32.0 % (2/5 0.5), 6.8 % (1/10 -5), 26.2 % (1/2 2) of total MACs.

Free metric psn (decoder's own frozen PM increment / frozen bits seen), CA-SCL-8 rows, 0 right packets lost in-sample
(95 % UB 9.4e-5 at 0.15, 9.5e-5 at 2/5, 3.7e-4 at 1/10, 1/2), W = wrong decodes stopped, nb = info bits decided:
| Point (rows: right / wrong) | best checkpoint (nb) | AUC | W | total MACs | per core | half-split: lost, total / core |
|---|---|---|---|---|---|---|
| 0.15 -4 dB (32166 / 235901) | 0.9 (76) | 0.9989 | 0.810 | -3.75 % | -5.00 % | 1 / 31843, -3.90 / -5.36 % |
| 0.15 -4 dB | 0.8 (35) | 0.9983 | 0.471 | -3.26 % | -3.02 % | 3 / 31843, -3.61 / -3.51 % |
| 0.15 -4 dB, union of 7 checkpoints | - | - | 0.988 | -5.39 % | -6.70 % | 9 / 31843 (2.8e-4, UB 4.9e-4), -5.71 / -7.18 % |
| 2/5 0.5 dB (31589 / 167839) | 0.7 (184) | 0.9974 | 0.988 | -12.98 % | -14.83 % | 2 / 31587 (6.3e-5, UB 2.0e-4), -12.95 / -14.83 % |
| 2/5 0.5 dB | 0.6 (48) | 0.9969 | 0.609 | -11.26 % | -8.66 % | 2 / 31587, -12.98 / -10.74 % |
| 2/5 0.5 dB, union | - | - | 0.991 | -16.32 % | -17.15 % | 8 / 31587 (2.5e-4, UB 4.6e-4), -16.83 / -17.69 % |
| 1/10 -5 dB (8009 / 3723) | 0.8 (15) | 0.9986 | 0.673 | -0.57 % | -1.11 % | (one part) union -0.76 / -1.56 % |
| 1/2 2 dB (7986 / 677) | 0.6 (50) | 0.9983 | 0.935 | -1.39 % | -1.83 % | (one part) union -1.46 / -1.91 % |
At the 1e-4 setting (3 lost / ~31.7k, UB 2.4e-4 - not certifiable at 1e-4 with 32k): 0.15 q 0.9 -4.11 % / -5.88 %,
2/5 q 0.6 -15.70 % / -14.28 %. At 1e-3 (31 lost, UB 1.3e-3): 0.15 q 0.8 -6.34 % / -8.74 %, 2/5 q 0.6 -17.91 % / -18.88 %.
0-loss thresholds t (psn): 0.763 (0.15, q 0.9), 0.774 (2/5, q 0.7), 0.751 (1/10, q 0.8), 0.776 (1/2, q 0.7).
- AUC P(wrong > right) per checkpoint q = 0.25 / 0.5 / 0.6 / 0.7 / 0.8 / 0.9 / 1.0, psn: 0.15 -4: 0.81 / 0.92 / 0.995 /
  0.995 / 0.998 / 0.999 / 0.9995 (nb 0 / 1 / 29 / 29 / 35 / 76 / 228); 2/5 0.5: 0.80 / 0.992 / 0.997 / 0.997 / 0.998 /
  0.998 / 0.999 (nb 0 / 19 / 48 / 184 / 189 / 233 / 588). Wrong-cell decodes alone: up to 0.9999 (2/5, q >= 0.7).
  The stopped wrong decodes are wrong-cell decodes (2/5 q 0.7: 99.6 % of wrong-cell, 3.3 % of failed true-cell decodes).
- Costed metrics pn (hard penalty / frozen bits) and pl (/ sum |LLR|) are never better than the free psn at 0 loss:
  2/5 q 0.7 pn -12.19 %, pl -12.90 % total (psn -12.98 %); 0.15 q 0.9 pn -2.36 %, pl -1.50 % (psn -3.75 %); unions
  0.15 pn -3.35 %, pl -2.46 %. They also need the leaf LLRs inside rate-0 nodes (extra cost, not counted here).
- Joint-list rows (16 paths) separately: 2/5 0.5 dB 2682 rows (348 right, all delivered; 0.9 % of total MACs): psn q 0.7
  W 0.930, -0.34 % total / -0.59 % per core, union W 0.977, -0.45 % / -0.75 %, 0 / 348 lost (UB 8.6e-3); 1/2 2 dB 38 rows
  (13 right): <= -0.12 %. Negligible.
- Difference from the frozen-only cell ranking dead end: before the first information bits are decided (0.15: q <= 0.5,
  nb <= 1; 2/5: q 0.25, nb 0) the frozen metric is a function of the channel LLRs alone, i.e. what the list-1 checkpoint
  metric of Stage 2 already used to pick these candidates: AUC only 0.80-0.92 and ~0 % of wrong decodes stoppable at
  0 loss. The separation comes from the frozen bits AFTER information bits are on the paths (checks of each path's own
  decisions): AUC 0.995-0.9999. The dead end was a relative ranking of cells (frozen-only = full metric there); F5 is
  an absolute test inside a decode, which is why it works here.
- vs prediction: 0.15 -4 dB MISS (low): ~0 % of wrong decodes stoppable at 1/2 of the frozen set (predicted 40-70 %),
  -3.75 % total / -5.0 % per core at 0 loss (predicted -5 ... -10 % / -3 ... -8 %); 2/5 0.5 dB MISS (high): 98.8 % of
  wrong decodes at q 0.7, -13.0 % total / -14.8 % per core (predicted 30-60 %, -3 ... -8 %); 1/10, 1/2: HIT (<= 2 %).
- **GATE: GO** (on 2/5 0.5 dB): -12.98 % total (gate 5 %), -14.83 % per core, single checkpoint q 0.7 with the free
  metric, 0 / 31587 lost (UB 9.5e-5), half-split 2 / 31587 lost at the same saving. 0.15 -4 dB alone would be NO GO:
  -3.75 % total at 0 loss with one checkpoint; only the 7-checkpoint union reaches -5.4 % and it loses 9 / 31843 out of
  sample (2.8e-4 > 1e-4).
- Open: (1) thresholds are in-sample; a max-of-n threshold has an expected out-of-sample loss ~1 / (n + 1) = 3e-5 per
  checkpoint at n = 32k (the half-split matches: 1-3 lost per checkpoint), a union of c checkpoints ~c / (n + 1); 1e-4
  needs the planned 400k confirmation. (2) SNR dependence of t untested: right-decode psn rises at lower SNR (one point
  per rate measured); the 0-loss t is nearly rate-independent (0.75-0.78). (3) Per-core saving assumes the d4a
  4-at-once rounds; a stopped decode only shortens its round when all 4 stop.
- Plots: `results/plots/original_study/fz_roc.png` (wrong decodes stopped vs right packets lost per checkpoint, psn, 0.15 and 2/5),
  `results/plots/original_study/fz_saving_vs_loss.png` (total MACs saved vs right-packet loss 95 % UB, best checkpoints of each metric,
  union in-sample and half-split).

## F5 online (`fzstop`), predictions 2026-11-15, before code
Thresholds from the offline 0-loss points (fz_f5.json): 2/5 q = 0.7, t = 0.774; 0.15 q = 0.9, t = 0.763.
| Point | packets | BLER | total MACs | per core |
|---|---|---|---|---|
| 2/5 0.5 dB | 400k paired | kill rule <= +1e-4 x 400k = +40 packets (paired McNemar); expected loss 0 ... ~25 packets (offline half-split 2 / 31587 = 6.3e-5 projects to ~25 at 400k as an upper estimate; online retries can rescue some; review 2026-11-15) | -11 ... -14 % | -12 ... -15 % |
| 0.15 -4 dB | 64k paired | same (+0 ... 2) | -3 ... -4 % | -4 ... -5 % |
- Kill: paired BLER loss p < 0.05 or > +1e-4, or undetected > base + 2.

Review note (2026-11-15): thresholds were fitted at 2/5 0.5 dB and 0.15 -4 dB only; right-decode psn rises at lower SNR, so the extra arm `fzs-lo` (2/5 0 dB, 0.15 -5 dB) must pass before adoption. Thresholds are now keyed by rate in run.py (1/10 0.8/0.751, 0.15 0.9/0.763, 2/5 0.7/0.774, 1/2 0.7/0.776).

## F5 online at 1/10 and 1/2 (predictions 2026-11-15, before the runs; jobs fzs-r-smoke, fzs-r)
Offline (8k packets each): 1/10 -5 dB -1.1 % per core / -0.6 % total; 1/2 2 dB -1.8 % / -1.4 %; 0 lost. At 1/10 the
search dominates (decodes 6.8 % of all MACs); at 1/2 2 dB few decodes fail. 1/2 1.5 dB (below the waterfall) was not
analysed: more failing decodes there, closer to 2/5.
| Point (paired) | Predicted MACs per core | Predicted total | Lost packets | Kill rule |
|---|---|---|---|---|
| 1/2 1.5 dB (128k) | -5 ... -10 % | -4 ... -8 % | 0 ... 3 | > +1e-4 x 128k = 13 extra errors (McNemar) |
| 1/2 2 dB (128k) | -1 ... -3 % | -1 ... -2 % | 0 ... 1 | as above |
| 1/10 -5 dB (64k) | -0.5 ... -1.5 % | -0.3 ... -1 % | 0 ... 1 | > +6 extra errors |
| 1/10 -4.5 dB (64k) | -0.5 ... -1.5 % | -0.3 ... -1 % | 0 | as above |
vs blind baseline: same BLER within the kill rule; the comparison with the pilot competitors is unchanged (<= 0.1 %
of MACs at 1/10, <= 10 % at 1/2, where blind is already 2x DVB-RCS2's MACs per core).


### Measured: fzs-r (2026-11-15 20:53, ALL DONE, no Traceback), paired
| Point | packets | errors base -> fzs | fixed / lost | undetected | per core | total | Prediction |
|---|---|---|---|---|---|---|---|
| 1/2 1.5 dB | 128k | 1363 -> 1381 | 1 / 19 (p = 4e-5) | 9 -> 8 | 0.2328 -> 0.1852 M (**-20.4 %**) | 3.27 -> 2.59 M (-20.7 %) | -5 ... -10 %, 0-3 lost: saving x2 better, losses x6 worse; **kill rule (> 13 extra) tripped: +18** |
| 1/2 2 dB | 128k | 7 -> 7 | 0 / 0 | 0 | 0.0829 -> 0.0815 M (-1.7 %) | -1.1 % | hit |
| 1/10 -5 dB | 64k | 19 -> 19 | 0 / 0 | 0 | 0.2070 -> 0.2042 M (-1.4 %) | -0.8 % | hit |
| 1/10 -4.5 dB | 64k | 3 -> 3 | 0 / 0 | 0 | 0.1773 -> 0.1750 M (-1.3 %) | -0.5 % | hit |
- The 18 extra errors at 1/2 1.5 dB are +1.3 % of that point's errors: they shift the 1e-3 crossing by ~0.001 dB.
  Still, by the pre-set rule the 1/2 thresholds (0.7, 0.776) fail at 1.5 dB. Not adopted at 1/2 until decided (user):
  accept (crossing unaffected, -20 % MACs below the waterfall) or retest a stricter 1/2 threshold. 1/10: adopt-able,
  but the gain is only ~1.4 %.

### Measured: fzs25a-d pooled, 2/5 0.5 dB, 403.2k paired (2026-11-15 21:20, all ALL DONE, no Traceback)
| Arm | errors | fixed / lost | undetected | per core | total |
|---|---|---|---|---|---|
| base25_qfix | 794 (1.97e-3) | - | 4 | 0.2308 M | 3.364 M |
| base25_qfix_fzs | 805 (2.00e-3) | 0 / 11 (McNemar p = 0.001) | 4 | 0.1965 M (**-14.9 %**) | 2.937 M (-12.7 %) |
- Predicted -11 ... -14 % per core, -12 ... -15 % total, 0 ... ~25 lost: **hit** (11 lost).
- Kill rules disagree: the +40-packet (+1e-4) rule passes (+11 = 2.7e-5), the "paired loss p < 0.05" clause trips.
  The loss shifts the 2/5 1e-3 crossing by ~0.003 dB. Same situation as 1/2 1.5 dB (+18 / 128k, -20 %): user decision.

## Adopted: full range (user, 2026-11-15) — job twf, predictions before the run
Early stop adopted at 2/5 and 1/2 (base25_qfix_fzs / base2_qfix_fzs). twf runs the rest of the waterfall with them
(single arm, seeds 8231 / 8232): 2/5 0 (64k), 1 (128k), 1.5 (128k), 2 (64k); 1/2 2.5 (128k), 3 (64k), 3.5 (64k).
| Point | BLER (base25 / base2 measured) | Predicted BLER | Predicted per core vs base |
|---|---|---|---|
| 2/5 0 dB | 5.9e-2 | 5.5 ... 6.5e-2 | -20 ... -30 % (most decodes fail there) |
| 2/5 1 dB | 5.5e-5 (7 / 128k) | 0 ... 15 errors | -5 ... -10 % |
| 2/5 1.5, 2 dB | 0 | 0 ... 2 errors | -1 ... -3 % |
| 1/2 2.5, 3, 3.5 dB | 0 | 0 ... 2 errors | -0.5 ... -2 % |
Required SNR: 2/5 @1e-3 0.61 -> 0.61 ... 0.62; 1/2 @1e-3 1.79 -> 1.79 ... 1.80 dB. Gaps to the competitors change by
<= 0.01 dB; blind's MACs per core at the 2/5 / 1/2 crossings drop ~10-15 %, so the MACs ratios vs the pilot
receivers shrink accordingly (2/5 ~5x -> ~4.3x vs RCS2-13). Runtime ~1 h (tw25 took ~1 h for similar points).

### Measured: twf (2026-11-16 ~00:45, ALL DONE, no Traceback) — the adopted receivers over the waterfall
| Point | Predicted BLER | Measured (adopted, pooled early-stop parts) | Predicted per core | Measured per core vs base |
|---|---|---|---|---|
| 2/5 0 dB | 5.5 ... 6.5e-2 | 5.8e-2 (4079 / 70.4k, twf25 + fzs-lo-a) | -20 ... -30 % | 1.70 -> 1.34 M (-21 %) hit |
| 2/5 1 dB | 0 ... 15 errors | 3 / 128k | -5 ... -10 % | -7.6 % hit |
| 2/5 1.5, 2 dB | 0 ... 2 | 0, 0 | -1 ... -3 % | -3.6 %, -0.9 % |
| 1/2 2.5, 3, 3.5 dB | 0 ... 2 | 0, 0, 0 | -0.5 ... -2 % | -0.3 ... 0 % (slightly less) |
| Required SNR 2/5 @1e-3 | 0.61 ... 0.62 | **0.58 [0.55, 0.61]** | MACs at the crossing | 0.209 -> 0.183 M (-12 %) |
| Required SNR 1/2 @1e-3 | 1.79 ... 1.80 | **1.73 [1.69, 1.76]** | | 0.149 -> 0.139 M (-7 %) |
- The crossings moved 0.03 / 0.06 dB LEFT although early stop is slightly worse when paired (+11 / 403k, +18 / 128k):
  the shift is the packet sets, not the receiver. The adopted curve now rests on its own packets (403k at 2/5 0.5 dB;
  1/2 2 dB: 7 / 128k with seeds 8221, where the paired base arm also had 7; the older base runs had 21 / 128k with
  other seeds, CIs [1.0, 2.5]e-4 vs [0.2, 1.1]e-4, borderline). Both predictions of the crossing missed for that reason.
- Wired in: agg_cmp.testing_hi (FZS parts) is the blind curve at 2/5, 1/2 in plot_e4.blind and comparison_data.
  plot_cap_fair still uses the base q_fix receiver (its pg_ histograms; not re-derived for early stop).
