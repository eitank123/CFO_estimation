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

## Measured (2026-11-13)

Source: `py BLIND_IMPLEMENTATION/testing/agg_qfix.py`. The full tables are in `report_qfix_ddq.md`. Parts t-ddq10 / t-ddq25 / t-ddq2:
- 64k paired packets per arm and point;
- all logs `EVAL DONE` + `ALL DONE`, no Traceback, no duplicated chunk;
- 0 undetected errors in every arm.

| Point | dd_qfix vs base_qfix: errors (fixed / broken) | dd_qfix per core | dd_win4_qfix per core | Verdict | hit / miss (errors, dd core, win4 core, verdict) |
|---|---|---|---|---|---|
| 2/5 0.5 dB | 143 -> 186, +30 % (8 / 51, p = 9e-9) | +11.2 % | +10.3 % (errors 186, same packets as dd) | dd not adopted | miss (worse than +25 %), miss (+11.2 vs <= +10), miss (+10.3 vs <= +5), hit |
| 2/5 1 dB | 3 -> 3 (0 / 0) | +0.7 % | +0.8 % | dd not adopted | hit, hit, hit, hit |
| 1/2 2 dB | 9 -> 9 (0 / 0) | +0.6 % | +0.4 % | no gain | hit, hit, miss (+0.4 +- 0.4 vs -10 ... 0, marginal), hit (no gain) |
| 1/2 2.5 dB | 0 -> 0 | +0.0 % | -0.0 % | no gain | hit, hit, hit, hit |
| 1/10 -1 dB | 0 -> 0 | +2.1 % | +9.3 % | no gain | hit, hit, miss (+9.3 vs <= +8), hit |
| 0.15 -1 dB | 4 -> 4 (0 / 0) | +1.5 % | +6.6 % | no gain | hit, hit, hit, hit |
| 0.15 0 dB | 0 -> 0 | +1.7 % | +6.3 % | no gain | hit, hit, hit, hit |

- **Score.** 23 of 28 marks hit. The overall prediction holds: with q_fix, dd fixes nothing at any point.
- **2/5 0.5 dB.** dd was worse than predicted: 51 packets broken, a significant BLER loss.
- **dd_win4 at 1/10 and 0.15.** Per core +6 ... +9 %, but total -2 ... +2 %. Decodes per packet are 3.14 vs 2.70 at 1/10 -1 dB.
- **dd at 1/10 and 0.15.** Per core +1.5 ... +2 %, total about -1 %.
- **Few errors.** All points except 2/5 0.5 dB have <= 9 errors per arm. There, only "no packet fixed or broken" is
  supported, not a BLER difference.
