# Decode-feedback NN, offline stage: results (2026-11-13)

## Source

- Script: `py BLIND_IMPLEMENTATION/testing/nn_offline.py`, which writes every number to `results/nn_offline.json`.
- Plots: `results/plots/original_study/nn_auc_headB.png` and `nn_pm_vs_rho.png` (heads A, C dropped: their plots removed; numbers below).
- Data: the decode dumps t-deca, t-decb25, t-decb2 and t-decbn.
- Train / test split by chunk: the last 2 of 8 chunks are the test set (8000 packets per point).
- No receiver simulation; this is fits on the logged rows only.

## P0: validation

- Rows match the JSON decode counts in every chunk. At 2/5 and 1/2 the joint-list decodes are not logged (254 and 31 per chunk).
- Packets: 32k per point.
- Noise-only: 5600 frames, 4.57 M decode rows, 201k kept (subsampled).

| Point | decodes / pk | retries | retry share of per-core MACs | errors |
|---|---|---|---|---|
| 1/10 -5 dB | 1.30 | 4815 | 2.5 % | 5 |
| 0.15 -4 dB | 7.90 | 110780 (562 succeed) | **28 %** | 138 |
| 0.15 -3 dB | 1.20 | 3274 | 2.2 % | 4 |
| 2/5 0.5 dB | 6.35 | 85773 (168 succeed) | **42 %** | 73 |
| 1/2 2 dB | 1.07 | 1064 | 2.5 % | 5 |

## P1: can the path metric (PM) replace the re-encoding check?

**No.** It cannot replace rho in acceptance.

- **Correlation.** PM and rho are strongly related: Pearson -0.81 ... -0.93, Spearman on CRC passes -0.86 ... -0.96.
- **0.15 -4 dB.** At the PM threshold that keeps every correct packet, PM still accepts 12 of 47 CRC-pass-wrong decodes (95 % CI 14-40 %). rho rejects all 47.
- **Noise-only.** PM would accept all 1046 noise CRC passes at the -4 dB threshold, and 90 at the -3 dB threshold. rho rejects every one (max 0.44).
- **Cost.** Saving the check would save only 625 MACs per core per check (20k total), so there is little to gain anyway.
- **Conclusion.** Acceptance stays CRC + rho, as the plan required.

## P3: AUC (best model per feature set, test chunks)

| Head | Point | F0 | F0+F1 | F0+F2 | F0+F1+F2 | F0..F3 | predicted (F0..F3) | hit |
|---|---|---|---|---|---|---|---|---|
| A local refine | 1/10 -5 | 0.906 | 0.899 | 0.925 | 0.915 | 0.878 | 0.97-0.99 | miss (only 36 positives) |
| A | 0.15 -4 | 0.971 | 0.980 | 0.973 | 0.978 | 0.976 | 0.90-0.95 | above |
| A | 2/5 0.5 | 0.925 | 0.939 | 0.940 | 0.938 | 0.970 | 0.95-0.98 | hit |
| A | 1/2 2 | 0.956 | 0.982 | 0.988 | 0.976 | 0.974 | 0.95-0.98 | hit |
| B retry gate | 1/10 -5 | 0.959 | 0.963 | 0.966 | 0.969 | 0.983 | 0.93-0.97 | above |
| B | 0.15 -4 | 0.995 | 0.998 | 0.996 | 0.997 | 0.998 | 0.88-0.94 | above |
| B | 2/5 0.5 | 0.910 | 0.966 | 0.938 | 0.965 | 0.966 | 0.92-0.96 | hit |
| B | 1/2 2 | 0.721 | 0.898 | 0.966 | 0.977 | 0.966 | 0.92-0.96 | hit |
| C grid stop | 1/10 -5 | 0.919 | 0.919 | 0.937 | 0.930 | 0.942 | 0.85-0.92 | above |
| C | 0.15 -4 | 0.904 | 0.921 | 0.905 | 0.897 | 0.901 | 0.80-0.88 | above |
| C | 2/5 0.5 | 0.761 | 0.771 | 0.758 | 0.740 | 0.964 | 0.85-0.92 | above |
| C | 1/2 2 | 0.953 | 0.969 | 0.986 | 0.972 | 0.962 | 0.85-0.92 | above |

- **Head D (noise-only).** AUC 1.00, but with scale-free features it drops to 0.92 (logistic). It does not count towards the MACs goal.
- **Feature-set prediction (F2 the biggest gain): not borne out.** F0 alone is already within 0.01-0.03 for heads A and B at most points. F1 and F2 matter only at 1/2 for head B (0.72 -> 0.97).
- **Model size.** Logistic regression is within 0.01-0.02 of the MLPs. The MLP gates lost more packets on the operating-point test (for example B at 1/10 -5 dB: 19-22 lost vs 0).

## P2 / P3: per-core MAC saving of a gate (logistic, test packets, approximate replay)

"lost" = packets that were right in the log and are lost by the gate, out of 8000. The baseline errors per 8000 packets are given for scale.

| Point (errors / 8k) | B at 1 % | B at 0.1 % | A at 1 % | C at 1 % | A+B at 1 % | A+B+C at 1 % | oracle B | oracle A+B |
|---|---|---|---|---|---|---|---|---|
| 1/10 -5 (1) | -0.5 %, 0 lost | -0.2 %, 0 | 0 | 0 %, 3 lost | -0.5 %, 0 | -0.5 %, 3 | -0.8 % | -0.8 % |
| **0.15 -4 (34)** | **-19.3 %, 0 lost** | **-9.2 %, 0** | -2.2 %, 0 | -5.3 %, 6 lost | **-20.4 %, 0** | -22.2 %, 6 | -29.8 % | -31.5 % |
| 0.15 -3 (1) | -0.6 %, 0 | -0.6 %, 0 | 0 | 0 %, 3 lost | -0.5 %, 0 | -0.6 %, 3 | -0.8 % | -0.8 % |
| **2/5 0.5 (18)** | **-15.5 %, 2 lost** | -13.7 %, 2 | -4.3 %, 0 | -13.5 %, **36 lost** | -17.5 %, 1 | -21.6 %, 36 | -42.3 % | -44.4 % |
| 1/2 2 (1) | -1.8 %, 1 | ... | -0.1 %, 0 | -0.7 %, 3 | -1.9 %, 1 | ... | -1.9 % | ... |

## Findings

1. **The retry gate (head B) is the only large win.**
   - At the two hard points almost every code-aided retry fails: 562 of 110780 succeed at 0.15 -4 dB, and 168 of 85773 at 2/5 0.5 dB. Yet retries are 28 % and 42 % of the per-core MACs there.
   - A logistic gate (about 50 MACs) skips most of them:
     - 0.15 -4 dB: -19 % per core with 0 lost.
     - 2/5 0.5 dB: -15.5 % with 2 lost (+11 % errors on 18, not resolved by 8k test packets).
   - The oracle gate bounds the saving at -30 % and -42 %.
   - At the easy points there are few retries, so the saving is <= 2 %.
2. **Head A (local refine) saves only 2-4 %**, and even that assumes optimistically that every refine succeeds. The oracle A is 4-6 %.
3. **Head C (grid stop) loses packets at every point**: 3-6 lost, and 36 at 2/5 0.5 dB at the 1 % point. Its savings appear only where it is unsafe. As the plan required, it is not built until a much stronger confirmation.
4. **PM cannot replace re-encoding** (P1): it accepts wrong CRC passes and noise. Acceptance stays CRC + rho.
5. **Logistic regression is enough.** The MLPs gain no AUC and lose more packets at the chosen operating points.

## Ranking for online tests (predicted per-core change vs the testing receiver)

1. **NN-B (logistic retry gate) at the 0.1 % point**: 0.15 -4 dB -9...-19 %, 2/5 0.5 dB -13...-15 %, others -0.2...-2 %. Low risk.
2. **A+B**: +1...+2 points over B at the hard points; low risk.
3. **A+B+q_fix**: as A+B at 1/10 and 0.15 (q_fix there is identity under nph15); at 2/5 the q_fix -14 % stacks on top.
4. **Variants that include C (C, A+C, B+C, A+B+C): not built**, because C loses packets.
5. **A alone: not worth an online run** (<= 4 %).

## Caveats

- **The replay is approximate.** A skipped successful retry is counted as lost (conservative). A refine is assumed to succeed (optimistic). Only an online paired run settles the BLER.
- **Head-B model inputs.** Retries are triggered by a failed main decode, so the gate uses the parent decode's features.
