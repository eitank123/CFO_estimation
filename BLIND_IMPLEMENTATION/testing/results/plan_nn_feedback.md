# NN on decode feedback: versions, combinations and predictions (written 2026-11-13, before any data)

## Data

The data comes from the decode dump (`dec_dump`): one row per decode attempt and one row per packet.

| Logging point | Packets |
|---|---|
| R = 1/10, -5 dB | 32k |
| R = 0.15, -4 dB | 32k |
| R = 0.15, -3 dB | 32k |
| R = 2/5, 0.5 dB | 32k |
| R = 1/2, 2 dB | 32k |
| R = 0.15, -1 dB, noise-only | 11k |

Train and test sets are split by packet: test = the last 25 % of the chunks.

## Features

| Group | Features |
|---|---|
| F0, grid only (the baseline) | cell z, z gap to the second-best cell, rank, checkpoint, alive / tried counts, distance to f0 |
| F1, decoder | the sorted list PMs (best PM, spread, gap 1-2), CRC syndrome weight, number of distinct CRC remainders, path agreement |
| F2, re-encoding | rho of the best path (CRC failed or not), sign agreement |
| F3, channel and packet | sum and mean of abs(L), share of abs(L) < 1, SNR estimate (M2M4 and the receiver's), 4th-power peak ratio and coherence |

The feature sets are tested in this order: F0; F0+F1; F0+F2; F0+F1+F2; F0+F1+F2+F3. The model gets no truth inputs.

## Models

The order is cheapest first:
- logistic regression (about 50 MACs);
- MLP 1 x 32 (about 1k MACs);
- MLP 2 x 32 (about 2k MACs);
- MLP 2 x 64 (about 6k MACs).

One model per rate, as with the split-pilot NN. A pooled model with the rate as an input is also tested. Training runs on the cluster (torch, up to 2 GPUs when free).

## Uses (heads)

| Head | Question it answers | What it changes in the receiver |
|---|---|---|
| A, local refine | Is this failed decode at the right cell (abs(f_err) <= 0.5 STEP)? | If yes: refine locally (sub-offsets, a code-aided step, the other pi/2 branch) instead of moving on to the next candidate. |
| B, retry gate | Will the code-aided retry succeed? | If no: skip the retry (its SC pass and decode). |
| C, grid stop | Is the right cell already among the decoded or top-z cells? | If yes: stop extending the grid and go to refinement. |
| D, no packet | Is this a noise-only packet? | If yes: stop the search (idle-channel cost only). |

## Offline stage (before any receiver change)

For each head, feature set and model, measure:
- AUC;
- the operating point that loses at most 1 % (and at most 0.1 %) of the decodes that would have succeeded;
- the MACs a gate at that operating point would have saved on the logged packets (an approximation that replays each packet's trajectory);
- the MACs a perfect (oracle) gate would save.

### Predictions (AUC, best model, F0+F1+F2+F3)

| Head | 1/10 -5 dB | 0.15 -4 dB | 2/5 0.5 dB | 1/2 2 dB |
|---|---|---|---|---|
| A | 0.97-0.99 | 0.90-0.95 | 0.95-0.98 | 0.95-0.98 |
| B | 0.93-0.97 | 0.88-0.94 | 0.92-0.96 | 0.92-0.96 |
| C | 0.85-0.92 | 0.80-0.88 | 0.85-0.92 | 0.85-0.92 |

- **Head D:** AUC > 0.99. It does not count towards the MACs-per-packet goal.

**Expected order of the feature sets:**
- F0 alone is the weakest: about 0.10 lower AUC on head A.
- Adding F2 (rho of the failed path) gives the biggest single gain; F1 is the next biggest.
- F3 adds at most 0.01.

**Expected model size:**
- logistic regression is within 0.02 AUC of MLP 2 x 32 on heads A and B;
- the MLP is needed only for head C.

## Online versions (simulated, paired with the testing receiver nofast15)

The top versions are chosen from the offline stage. Each version runs 64k paired packets at 1/10 -5 dB, 0.15 -4 dB, 0.15 -3 dB, 2/5 0.5 dB and 1/2 2 dB. Each gets a smoke test first, at a high-BLER point.

**Predicted per-core MACs change (BLER within noise unless noted):**

| Version | 1/10 -5 | 0.15 -4 | 0.15 -3 | 2/5 0.5 | 1/2 2 | Risk |
|---|---|---|---|---|---|---|
| NN-A (logistic) | -3...-6 % | -10...-20 % | -3...-6 % | -5...-15 % | -3...-8 % | low |
| NN-A (MLP) | -3...-7 % | -12...-22 % | -3...-7 % | -5...-15 % | -3...-8 % | low |
| NN-B | -2...-5 % | -5...-15 % | -2...-4 % | -5...-10 % | -2...-5 % | low-medium (lost retries) |
| NN-C | -10...-25 % | -5...-15 % | -10...-20 % | -5...-15 % | -5...-10 % | **high** (search cut: BLER) |
| A+B | -5...-10 % | -15...-30 % | -5...-10 % | -10...-20 % | -5...-12 % | low-medium |
| A+C | -12...-28 % | -15...-30 % | -12...-25 % | -10...-25 % | -8...-15 % | high |
| B+C | -12...-28 % | -10...-25 % | -12...-22 % | -10...-22 % | -7...-14 % | high |
| A+B+C | -15...-32 % | -20...-35 % | -15...-28 % | -12...-28 % | -10...-18 % | high |
| A+B+q_fix | the A+B values plus the q_fix gain at the 2-phase points (2/5, 1/2) | | | | | low-medium |

## Pass / fail rules

- **NN in the acceptance decision:** never. Acceptance stays CRC + rho, so the undetected-error rate cannot get worse because of the NN. This is checked with the origin tags, which must show 0 extra undetected errors.
- **BLER:** a version is kept only if its errors are no more than +5 % above the paired baseline at 0.15 -4 dB (significant in the paired test) and do not increase at the other points.
- **Head C** additionally needs a 400k confirmation at 1/10 -5 dB and 0.15 -3 dB before it can be adopted.
- **NN cost:** the NN's own MACs (at most a few k per call) are charged on the critical path. The gain must survive that.

## Later combinations

- The best version on top of nofast_spec, if spec passes its undetected-error check.
- The PM-based acceptance (P1), if it passes the noise-only false-alarm check.
