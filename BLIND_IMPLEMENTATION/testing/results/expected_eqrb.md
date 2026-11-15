# Faithful phase-equivariant code: 2 rotation bits (Geiselhart et al. 2023), predictions 2026-11-15, before any code

## Why (expected_eq.md)
Our `equiv` receiver (no interleaver, PiCode4) left out the paper's 2 rotation bits: it tried the CRC at all 4 rotations of
every list path, so a wrong rotation could pass by chance (4 tests per path) and the phase-invariant re-encoding check
cannot reject it -> 4-11 undetected per 64k at 1/10, 0.15. Without the interleaver a pi/2 rotation is the translation
u_{2m+1} ^= u_{2m} plus the constant codeword "ones at even positions" = e_{N-2} in the u domain (to be verified in code);
a pi rotation adds e_{N-1}. So the rotation is visible in u_{N-2}, u_{N-1}.

## Construction (`eqrb`, env BLIND_ROTBITS=1, needs BLIND_NOINT=1)
- Information set = the K + 2 most reliable positions (they always include N-2 and N-1). Data + CRC-16 (K = A + 16 bits)
  go on the K positions other than N-2, N-1; u_{N-2} = u_{N-1} = 0 at the transmitter (2 bits of rate, as the paper).
- Decoder: the same CA-SCL-8 / metrics with N-2, N-1 decoded as free bits (keeps the equivariance); each list path reads
  q from (u_{N-2}, u_{N-1}), un-rotates once, and runs ONE CRC test (no PiCode / PiCode4 guessing). Half the phase
  hypotheses as in `equiv`.

## Predictions (paired with the interleaved standard receiver on the same seeds, as eq*; 64k per point)
| Point | BLER vs interleaved | undetected | per core |
|---|---|---|---|
| 2/5 0.5 / 1 dB | same within noise (2 fewer frozen bits: <= +0.05 dB) | <= base + 1 | -30 ... -40 % (as equiv) |
| 1/2 2 / 2.5 dB | same within noise | <= base + 1 | -35 ... -40 % |
| 1/10 -5 / -4 dB, 0.15 -4 / -3 dB | undetected fixed (0-1 per 64k), but the DETECTED excess of equiv (x1.6-10, half the phases lose the true branch) stays: x1.5-10 | 0 ... 1 | as equiv (+10 ... +50 % at 1/10) |
- Wrong CRC passes per 128k: about 1/4 of equiv's (one test per path instead of four), close to the interleaved base.
- Kill: at 2/5 or 1/2 paired BLER loss p < 0.05 or undetected > base + 2. If 2/5 and 1/2 pass: 400k confirmation at
  2/5 0.5 dB and 1/2 2 dB (undetected) before proposing adoption.
- Unit checks first (cluster smoke): equivariance with the new info set (metric(theta) = metric(theta + q pi/2)), the
  rotation read from (u_{N-2}, u_{N-1}) is right in 100 % of noiseless and high-SNR packets at q = 0..3.

## Unit check (eqrb-chk, 2026-11-15): PASS
At the true CFO, all 4 rotations: metric difference <= 1.2e-4 (float rounding; 0 at +5 dB); the delivered path's
rotation read right in 100 % (best-metric path 99.9-100 %); CRC passes at a wrong rotation 0; wrong decodes 0
(0.15 -3, 2/5 1, 1/10 -5, 1/2 2 dB and +5 dB at all rates; 2000-4000 packets each).

## Smoke (eqrb-smoke, 1600 packets per arm, same seeds; codewords differ so discordant counts are not McNemar-paired)
| Point | errors standard -> eqrb (undetected) | per core | total |
|---|---|---|---|
| 0.15 -4.5 dB | 64 (1) -> 56 (0) | -31.8 % | -42.4 % |
| 1/10 -5.5 dB | 2 (0) -> 6 (3) | +2.2 % | -3.1 % |
| 2/5 0 dB | 93 (1) -> 84 (0) | -41.0 % | -47.7 % |
| 1/2 1.5 dB | 11 (0) -> 13 (0) | -45.5 % | -51.9 % |
EVAL DONE + ALL DONE, no Traceback. 2/5, 1/2 and 0.15 as predicted or better; 1/10 -5.5 dB again shows undetected errors
(3 / 1600, not from wrong rotations: the unit check had 0): a 1/10-specific false-accept path to look into in the full
runs (eqrb10). Full paired runs submitted.

## Measured: eqrb25, eqrb2 (64k per point and arm, same seeds; logs EVAL DONE + ALL DONE, no Traceback)
| Point | errors standard -> eqrb (undetected) | genie standard / RB code | per core | total |
|---|---|---|---|---|
| 2/5 0.5 dB | 145 (1) -> 113 (1) | 237 / 246 | 0.231 -> 0.159 M (-31.3 %) | -32.0 % |
| 2/5 1.0 dB | 3 (0) -> 1 (0) | 6 / 8 | -29.7 % | -15.7 % |
| 1/2 2.0 dB | 12 (0) -> 5 (0) | 38 / 31 | 0.083 -> 0.051 M (-38.2 %) | -14.0 % |
| 1/2 2.5 dB | 1 (0) -> 1 (0) | 1 / 2 | -39.9 % | -9.7 % |
- vs predictions: BLER same or better (2/5 0.5 dB 145 -> 113, p = 0.053 in favour; the genie shows the code itself is equal):
  HIT. Undetected = base: HIT. Per core -30 ... -40 %: HIT. Kill gate passed -> 400k confirmations eqrb25c, eqrb2c queued.

## Measured: eqrb15, eqrb10 (64k per point and arm) and the 400k confirmations eqrb25c, eqrb2c (2026-11-15)
All logs EVAL DONE + ALL DONE, no Traceback. Codewords differ between arms: unpaired Poisson comparison.
| Point | errors standard -> eqrb (undetected) | genie standard / RB code | per core |
|---|---|---|---|
| 0.15 -4 dB | 274 (1) -> 450 (1) | 112 / 143 | 0.438 -> 0.390 M (-11 %) |
| 0.15 -3 dB | 11 (0) -> 50 (2) | 0 / 0 | 0.191 -> 0.211 M (+10 %) |
| 1/10 -5 dB | 18 (0) -> 65 (5) | 2 / 3 | 0.243 -> 0.273 M (+12 %) |
| 1/10 -4 dB | 0 (0) -> 12 (3) | 0 / 0 | 0.171 -> 0.260 M (+52 %) |
| 2/5 0.5 dB (400k) | 848 (2) -> 716 (2) | 1306 / 1424 | 0.230 -> 0.161 M (-30.0 %) |
| 1/2 2 dB (400k) | 47 (1) -> 58 (1) | 188 / 220 | 0.083 -> 0.051 M (-38.6 %) |
- 1/10, 0.15: KILL (undetected 2-5 > base + 2; detected x1.6-4.5 as predicted: half the phases lose the true branch,
  the 2 rotation bits do not give it back). Same verdict as `equiv` there.
- 2/5: PASS, better (848 -> 716, z = 3.3) at -30 % per core, undetected equal. The RB code alone is 9 % weaker (genie).
- 1/2: PASS within noise (47 -> 58, z = 1.1; the RB code alone is 17 % weaker: 2 fewer frozen bits at K = 1040), undetected
  equal, -39 % per core.
- Proposal (user's call, it drops the interleaver at those rates): adopt eqrb at 2/5 and 1/2 only.
