# Retry gate online (jobs nnb10, nnb15, nnb25, nnb2): predictions, written 2026-11-13 before any result

## What is tested
- `<base>_nnb1` / `<base>_nnb01`: the q_fix baseline + the retry gate (small_rx `nn_b`) at the 1 % / 0.1 % operating
  point (thr keeps all but 1 % / 0.1 % of the train successful retries). Weights `results/nn_b_gate.json`
  (`nn_b_export.py`, one logistic per code rate, 13 features of the failed main decode).
- Paired against the q_fix baseline on the same packets (64k per point and arm):
  - 1/10 -5 dB and 0.15 -4 / -3 dB: nofast15_qfix (the testing receiver with q_fix);
  - 2/5 0.5 dB: base25_qfix; 1/2 2 dB: base2_qfix.
- New seeds (7741-7744): packets independent of the dumps the gate was trained on.

## Offline basis (replay on the dump test chunks, 8000 packets per point)
0.15 -4 dB -12.2 % / -20.7 % per core (0.1 % / 1 %), 2/5 0.5 dB -13.9 % / -24.1 %, others <= 2 %, 0 lost.
The replay counts a skipped successful retry as a lost packet; online the search can still find the packet later
(fewer losses) but the skipped retry's packet may also cost extra search (less saving).

## Predictions
| Point | arm | per core vs base | total vs base | errors vs base (paired) | gate skips / gated decodes |
|---|---|---|---|---|---|
| 0.15 -4 dB | nnb1 | -12 ... -22 % | -8 ... -20 % | +0 ... +5 %, broken - fixed <= 5 | >= 90 % |
| 0.15 -4 dB | nnb01 | -6 ... -14 % | -4 ... -12 % | within +-3 % | 60 ... 90 % |
| 0.15 -3 dB | both | -0 ... -3 % | -0 ... -3 % | same (few errors) | >= 80 % |
| 1/10 -5 dB | both | -0 ... -2 % | -0 ... -3 % | same | >= 80 % |
| 2/5 0.5 dB | nnb1 | -12 ... -25 % | -8 ... -20 % | +0 ... +8 % | >= 90 % |
| 2/5 0.5 dB | nnb01 | -8 ... -16 % | -5 ... -12 % | within +-5 % | 60 ... 90 % |
| 1/2 2 dB | both | -0 ... -3 % | -0 ... -3 % | same | >= 50 % |

- Undetected errors: unchanged (acceptance untouched): 0 ... 1 per arm.
- Gate cost (GATE_MACS, ~20k total per gated decode) < 0.5 % of per core everywhere.
- Adoption rule: nnb1 adopted if the paired BLER change is not significant (McNemar p > 0.05) and per core falls;
  else nnb01 under the same rule; else neither.

## Notes from the code review (before the runs)
- At 1/2 the gate had only 11 successful train retries: thr[0.01] = thr[0.001], so only `base2_qfix_nnb1` runs; about
  1 in 12 successful retries may be skipped there.
- The "0.1 %" point at 1/10 and 2/5 is in effect "0 train losses" (101 / 123 positives): expected loss ~1 %, and the "1 %"
  point ~2 % of the successful retries. Predictions above are from the replay, not from frac.
- GATE_MACS counts the list CRCs again (the decoder already computed them): conservative.
- The 1/2 gate was fit on base2 dumps without q_fix and is applied on base2_qfix (minor shift).

## Measured: 2/5 0.5 dB (t-nnb25, 64k paired, 2026-11-13)
| arm | errors (fixed / broken, p) | per core | total | decodes / pk | retries skipped |
|---|---|---|---|---|---|
| base25_qfix | 128 (2.00e-3) | 0.355 M | 3.30 M | 5.78 | - |
| nnb1 | 134 (0 / 6, p = 0.031) | -23.4 % | -9.7 % | 4.39 | 96404 / 154394 (62 %) |
| nnb01 | 130 (0 / 2, p = 0.5) | -14.8 % | -5.6 % | 4.88 | 60316 / 152202 (40 %) |
- Per core: hit for both (predicted -12 ... -25 % / -8 ... -16 %). Errors: nnb1 +4.7 % (hit on size, +0 ... +8 %), but the
  paired loss is significant (6 broken, 0 fixed): nnb1 FAILS the adoption rule at 2/5; nnb01 passes (adopt at 2/5).
- Undetected 0 in every arm. Genie 220 / 64k (blind is below the genie here: the genie has no rescue).

### 2/5 0.5 dB under the standard (scheduled) per-core count
Re-counted with the scheduled count adopted on 2026-11-13 (crit_par_d4a): base 0.228 M; nnb1 -9.1 %, nnb01 -4.4 %
(the -23.4 / -14.8 % above were the earlier crit_par count). Retries already overlap other decodes in the scheduled
model, so skipping them shortens the critical path much less.

## Measured: 0.15, 1/10, 1/2 (t-nnb15, t-nnb10, t-nnb2, 64k paired each, 2026-11-13)
All 3 logs EVAL DONE + ALL DONE, no Traceback. Per core = scheduled count; "earlier" = crit_par.
| point | arm | errors (fixed / broken, p) | undetected | per core | (earlier count) | total | retries skipped |
|---|---|---|---|---|---|---|---|
| 0.15 -4 dB | nofast15_qfix | 266 (4.16e-3) | 1 | 0.427 M | 0.607 M | 8.16 M | - |
| 0.15 -4 dB | nnb1 | 268 (0 / 2, p = 0.5) | 1 | -9.2 % | -18.0 % | -6.4 % | 145238 / 212049 (68 %) |
| 0.15 -4 dB | nnb01 | 267 (0 / 1, p = 1) | 1 | -4.5 % | -10.4 % | -3.4 % | 84144 / 210856 (40 %) |
| 0.15 -3 dB | nnb1 / nnb01 | 4 / 4 (0 / 0) | 0 | 0.0 % | 0 % | 0 % | 205 / 32 of 4995 |
| 1/10 -5 dB | nnb1 | 16 (0 / 0) | 0 | -1.3 % | -2.4 % | -0.7 % | 9470 / 13588 |
| 1/10 -5 dB | nnb01 | 16 (0 / 0) | 0 | -0.6 % | -1.4 % | -0.3 % | 5031 / 13340 |
| 1/2 2 dB | nnb1 | 7 (0 / 0) | 0 | -2.1 % | -2.4 % | -1.2 % | 2350 / 2473 |
- Predictions (0.15 -4 dB, written on the earlier count): per core -12 ... -22 % / -6 ... -14 % -> hit on the earlier
  count (-18.0 / -10.4 %), but on the standard count only -9.2 / -4.5 %. Errors: hit (+0.8 / +0.4 %).
- At 1/10, 1/2 and 0.15 -3 dB the main decode rarely fails, so there is almost nothing to gate (<= 2 %).
- Pooled over all points the gate never fixed a packet: nnb1 0 fixed / 8 broken (McNemar p = 0.008), nnb01 0 / 3
  (p = 0.25).

### Decision
- nnb1 (1 % setting): REJECTED everywhere (pooled 8 broken / 0 fixed is significant). -> DEAD_ENDS.
- nnb01 (0.1 % setting): passes the per-point rule, but the gain on the standard count is <= 4.5 % per core and
  <= 5.6 % total, only at the two hardest points, with 3 broken / 0 fixed pooled. NOT adopted: spec11 gives more
  (-7 ... -14 % per core, 0 discordant) at no BLER cost. Kept as a flag (`nn_b`) for the combined runs (comb10, comb15).
