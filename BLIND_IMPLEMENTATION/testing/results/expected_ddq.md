# The R experiments with q_fix (jobs ddq25, ddq10): predictions, written 2026-11-13 before any result

## What is tested

- `dd` = code-aided refinement (s3_dd).
- `dd_win4` = dd plus the early win at z > 4.
- Both have q_fix on, and each is paired with its own q_fix baseline on the same packets:
  - base25_qfix at 2/5, 0.5 / 1 dB;
  - base2_qfix at 1/2, 2 / 2.5 dB;
  - base10_qfix at 1/10 -1 dB and at 0.15 -1 / 0 dB.
- Each point runs 64k packets.

## Why it is re-run

- The phase-index bug put 2-phase candidates at pi/4 instead of pi/2. That biased the earlier dd results at exactly these points.
- The earlier dd verdict there is therefore not trusted.

## Smoke signal (400 packets, 2/5 0 dB)

- dd_qfix_25: 28 errors.
- base25_qfix: 21 errors.
- That is too few packets to judge, but it points against dd.

## Predictions

| Point | dd_qfix vs base_qfix: errors | dd_qfix per core | dd_win4_qfix per core | Verdict expected |
|---|---|---|---|---|
| 2/5 0.5 dB | +0...+25 % | +0...+10 % | -5...+5 % | dd not adopted |
| 2/5 1 dB | +0...+30 % (few errors) | +0...+10 % | -5...+5 % | dd not adopted |
| 1/2 2 dB | within noise | -5...+5 % | -10...+0 % | small gain at most |
| 1/2 2.5 dB | within noise | -5...+5 % | -10...+0 % | small gain at most |
| 1/10 -1 dB | 0 vs 0 | +0...+5 % | +0...+8 % (the smoke had more decodes) | no gain |
| 0.15 -1 dB | within noise of base10_qfix | +0...+5 % | +0...+8 % | no gain |
| 0.15 0 dB | within noise | +0...+5 % | +0...+8 % | no gain |

**Overall prediction.** With q_fix, the refinement already lands on the right pi/2 branch. So dd's code-aided step has little left to fix:
- the earlier dd conclusion ("no gain") stays;
- dd is not adopted.
