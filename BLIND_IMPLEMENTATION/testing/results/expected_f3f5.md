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
