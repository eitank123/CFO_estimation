# Phase-equivariant receiver (equiv, BLIND_NOINT=1; jobs eq15, eq10, eq25, eq2): predictions, 2026-11-13, before any result

Paired, both arms without the bit interleaver: the receiver with half the phase hypotheses + rotation-aware CRC vs the
same receiver without (nofast15_qfix / base25_qfix / base2_qfix). 64k per point.
Basis: lit_checks_results.md (full-length metric equal at theta + q pi/2; CA-SCL rotation-aware 100 %). The un-rotation
check is charged conservatively (~11.6k MACs per list path, XORs as MACs; reported apart as macs_rot).

| Point | per core | total | BLER |
|---|---|---|---|
| 1/10 -5 / -4 dB (4 / 2 phases -> 2 / 1) | -15 ... -35 % | -25 ... -45 % | same within noise |
| 0.15 -4 / -3 dB (4 phases -> 2) | -15 ... -35 % | -25 ... -45 % | same within noise |
| 2/5 0.5 / 1 dB (2 phases -> 1, joint decode) | -5 ... -25 % | -10 ... -35 % | same within noise |
| 1/2 2 / 2.5 dB | -5 ... -20 % | -10 ... -30 % | same within noise |
Risk: if the partial metrics at the checkpoints are NOT rotation-equal, BLER rises (the search would prune on one
branch only). Kill: paired BLER loss p < 0.05 at any point. Note: the 2/5, 1/2 checkpoint NN was trained with the
interleaver; under BLIND_NOINT=1 both arms see the same mismatch (fair comparison, but a deployment needs a retrain).

## Notes from the code review (before the runs)
- Partial metrics at every checkpoint are equal too (leaf by leaf, same decoding order; the code is decreasing).
- The un-rotation check is charged as XORs on the decoded u (info bits at even indices + 2 + K CRC, ~0.3-1.5k per path),
  not the earlier N/2 log2 N (~11.6k, +50 % per decode).
- PiCode4 makes 4 CRC tests per path instead of 2: compare undetected errors and wrong CRC passes between the arms, not
  only BLER; report McNemar discordant counts.

## Smoke (t-eq-smoke-a/b/c, 400 packets per point) and a change of the comparison arm
Without the interleaver the OLD receiver breaks: its pi/2 hypothesis pairs have identical metrics and PiCode undoes only
pi, so it decodes at a wrong pi/2 branch half the time: 0.15 -4.5 dB 68 errors, 1/10 -5.5 dB 37 (4 undetected), 2/5 0 dB
167, 1/2 1.5 dB 167, vs the equivariant receiver 15 / 1 / 30 / 5 (interleaved receiver, other packets: 17 / 0 / 20 / 3).
So the comparison arm is the normal receiver WITH the interleaver, same seed (same data, CFO, phase, noise; only the
bit-to-symbol mapping differs): jobs eq15/eq10/eq25/eq2, parts t-eq*b (interleaved: `testing`, base25_qfix, base2_qfix)
and t-eq*e (BLIND_NOINT=1, *_eq). Smoke MACs (indicative, other packets): 0.15 -4.5 dB per core 1.56 vs 2.87 M, total
15.6 vs 27.7 M; 2/5 0 dB 3.64 vs 5.19 M; 1/2 1.5 dB 0.36 vs 0.38 M. Watch 2/5: 30 vs 20 errors in the smoke.

## Measured (eq15, eq10, eq25, eq2; 64k per point and arm, same seed, 2026-11-13)
All 4 logs: both parts EVAL DONE, ALL DONE, no Traceback, no duplicated chunk. Arms: interleaved receiver (t-eq*b:
`testing` / base25_qfix / base2_qfix) vs equivariant receiver without the interleaver (t-eq*e: *_eq). Same data, CFO,
phase and noise; only the bit mapping differs, so "paired" here is approximate (McNemar not meaningful).
Genie: same BLER in both formats (0.15 -4 dB 129 vs 112, 1/10 -5 dB 1 vs 1): the code / channel is not the cause.
| Point | errors interleaved -> eq (undetected) | per core (scheduled) | total |
|---|---|---|---|
| 0.15 -4 dB | 274 (0) -> 438 (4) | 0.437 -> 0.385 M (-12 %) | 8.34 -> 6.82 M (-18 %) |
| 0.15 -3 dB | 3 (0) -> 35 (0) | 0.189 -> 0.209 M (+11 %) | 3.66 -> 4.33 M (+18 %) |
| 1/10 -5 dB | 8 (0) -> 79 (7) | 0.241 -> 0.275 M (+14 %) | 4.87 -> 5.69 M (+17 %) |
| 1/10 -4 dB | 1 (0) -> 17 (11) | 0.171 -> 0.260 M (+52 %) | 3.23 -> 5.50 M (+70 %) |
| 2/5 0.5 dB | 128 (1) -> 111 (2) | 0.227 -> 0.159 M (-30 %) | 3.29 -> 2.28 M (-31 %) |
| 2/5 1.0 dB | 2 (0) -> 3 (0) | 0.118 -> 0.083 M (-30 %) | 1.21 -> 1.04 M (-14 %) |
| 1/2 2.0 dB | 8 (0) -> 10 (0) | 0.083 -> 0.052 M (-37 %) | 0.745 -> 0.634 M (-15 %) |
| 1/2 2.5 dB | 0 -> 0 | 0.075 -> 0.045 M (-40 %) | 0.575 -> 0.519 M (-10 %) |
Wrong CRC passes / caught by the re-encoding check (128k packets per arm, both SNRs): 1/10 6 / 6 -> 48 / 30;
0.15 101 / 101 -> 176 / 172; 2/5 77 / 76 -> 89 / 87.

vs predictions:
- 2/5, 1/2: HIT on BLER (within noise), per core -30 ... -40 % (predicted -5 ... -25 %: more saving), total -10 ... -31 %
  (predicted -10 ... -35 %).
- 1/10, 0.15: MISS. BLER x1.6 (0.15 -4) to x10-17 (0.15 -3, 1/10), undetected 4-11 per 64k, and MORE MACs except at
  0.15 -4 dB. Kill rule met: not adopted at 1/10, 0.15.
- Likely cause of the undetected errors (hypothesis, not yet tested): the re-encoding check |sum r c*| is
  phase-invariant, and a pi/2 rotation of the true codeword is again a codeword (that is the equivariance), so the check
  cannot reject a wrong rotation q that passes the CRC by chance. PiCode4 tests 4 rotations per path (PiCode: 2), so
  these chance passes double, and the check does not catch them (1/10: 18 of 48 wrong passes not caught; interleaved
  0 of 6). Possible fix: require exactly one rotation to pass the CRC (ambiguous -> no pass), for 2 more CRC tests per
  passing path. The detected-error excess (1/10 -5 dB: 72 vs 8) is a second problem (search side: half the phase
  hypotheses at the low rates prune the true branch more often), not explained yet.

### Decision (proposed)
- 1/10, 0.15: dropped (DEAD_ENDS), unless the uniqueness check fixes both the undetected and the detected excess.
- 2/5, 1/2: works, -30 ... -40 % per core at the same BLER. Adopting it removes the bit interleaver, a change of the
  channel format, and the 2/5, 1/2 checkpoint NN should be retrained without the interleaver: the user's call. Before
  adoption: 400k paired at 2/5 0.5 dB and 1/2 2 dB for undetected errors (2 vs 1 here).
