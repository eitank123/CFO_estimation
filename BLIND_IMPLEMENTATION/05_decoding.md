# 5. Stage 3: refinement and decoding

Code: `blind_fast._refine2`, `small_rx.decode`, `small_rx.refine_joint` / `decode_joint`, `blind_cfo.PiCode.decode_joint`.

## 5.1 Refinement of a candidate cell
For a candidate cell (f_c, θ_c):
1. **Offsets:** CFO offsets o ∈ {−⌊k/2⌋, …, ⌊k/2⌋}·STEP. At R = 1/10 (k = 4) that is 5 offsets of 7.5·10⁻⁵ each, so the residual is at most 3.75·10⁻⁵.
2. **Phase:** recomputed per offset as θ = phase4(r', f_c + o), then moved onto the cell's π/2 branch: θ ← θ + round((θ_c − θ)/(π/2))·π/2.
3. **Phase sub-offsets:** {−π/12, 0, +π/12} when 4 phases are in use (below −1 dB).
4. **Scoring and decoding:** all of these are scored with the full list-1 metric, and the best **T = 2** go to CA-SCL-8, best first.

## 5.2 CA-SCL-8 (`polar.PolarCode`, `PiCode`)
Successive-cancellation list decoding with L = 8 paths:
- each information bit doubles the list to 16 candidates;
- the 8 with the smallest path metric (3.1) survive;
- at the end, the best path that passes the CRC is chosen (PiCode: either CRC pattern, 06).

The decode runs on LLRs from the **pre-MF-corrected** samples. Each candidate's MF is re-matched at the candidate's own CFO (`premf_dec`).

## 5.3 Joint list decoding (R = 2/5, 1/2)
The candidates' best 2 refined hypotheses each, 4 cells at a time (8 hypotheses), go into **one** list decoder of **16** paths. Path h starts on hypothesis h's LLRs, and pruning is global over all of them:

$$\text{keep the 16 best of } \{(h,\text{path})\}\ \text{by } M_h(\text{path}) .$$

This is valid because all hypotheses come from the **same received samples**, so their path metrics are comparable. A wrong hypothesis's paths lose to the right hypothesis's paths and die. On 32 cores that is 4 candidates × 8 paths at once. The chosen path then goes through the retry and the checks below.

## 5.4 Code-aided retry (all rates)
If the CRC fails, the receiver uses the SC hard-decision codeword ĉ (from `metric_cw`), even though it is wrong in places, as decision-directed pilots:
1. it re-maps ĉ to symbols ŝ and forms z_n = r'_n ŝ_n*;
2. it runs 2 Newton steps on Λ(f) = |Σ z_n e^{−j2πf·n_c}|² from f̂, with the update f ← f − Λ′/Λ″;
3. it sets θ = arg Σ z_n e^{−j2πf·n_c};
4. it runs one more CA-SCL-8 decode at the new (f, θ).

## 5.5 Rescue (packets still undecoded)
1. **Next cells:** the next **256** cells by z, now on **both** π/2 branches, 8 at a time, each with the refinement of 5.1.
2. **Fine grid:** the 4 best cells by final path metric, on a **half-STEP** grid over ±k/2 STEP (offsets {−k, …, k}·½ STEP) and phases {0, ±π/16, ±π/8}, with T = 6 decodes each.

## 5.6 Delivered CFO
The delivered CFO is the accepted hypothesis's CFO. After a pass, a decision-directed refinement over all 1024 re-encoded symbols (`blind_cfo.dd_refine`: ±10⁻³ scan + Newton) gives the final estimate. Its error statistics are reported as "final" CFO RMSE.

## 5.7 Which stage delivers a packet
For the statistics, every right decode is tagged with the stage that accepted it (`small_rx`, counters
`stage_1` … `stage_5`):

| Tag | Stage |
|---|---|
| 1 | the fast path (02) |
| 2 | a decode inside the grid search: an early win (z > 6) or a candidate after the last checkpoint (04) |
| 3 | the final candidates (best 32 by path metric) |
| 4 | the rescue over the next 256 cells (5.5, step 1) |
| 5 | the fine-grid rescue (5.5, step 2) |

The share of packets still undecoded after each stage, vs SNR, is plotted per rate in `est3/plots/stages_R*.png`
(also in [presentation/](presentation/)).

## 5.8 F5: frozen-bit early stop inside every CA-SCL-8 decode (testing receiver, R = 2/5 and 1/2; adopted 2026-11-15)
Most CA-SCL-8 decodes the receiver runs are at a **wrong** (CFO, phase) hypothesis: they end in a CRC failure, but they
still cost a full decode. F5 stops such a decode early, from the frozen bits it has already seen.

**Metric.** While the list decoder walks the code tree, every frozen leaf adds a penalty to the path metric of each
list path when the path's LLR disagrees with the known 0. F5 keeps that frozen-only part apart:
psn = (sum of frozen-leaf penalties of the path so far) / (number of frozen leaves seen so far).
At the right hypothesis the frozen bits look like pilots that agree, so psn stays small; at a wrong one it grows.

**Rule (one check per decode).** At the first node boundary where at least ceil(q · F) of the F frozen leaves have been
decided, the decode is stopped if min over the alive list paths of psn > t. A stopped decode is treated exactly like
a CRC failure (the rest of the receiver flow is unchanged) and is charged the work done up to the stop.

| Rate | q (share of frozen leaves seen) | t (threshold on psn) | Receiver |
|---|---|---|---|
| 2/5 | 0.7 | 0.774 | `base25_qfix_fzs` (adopted) |
| 1/2 | 0.7 | 0.776 | `base2_qfix_fzs` (adopted) |
| 1/10 | 0.8 | 0.751 | available, not adopted (only -1.4 % MACs per core) |
| 0.15 | 0.9 | 0.763 | available, not adopted |

The thresholds come from an offline study on decode dumps (every list path's frozen metric at 1/4, 1/2, 3/4 of the
frozen set, right vs wrong decodes): t is the largest value that keeps the right decodes (0 lost in-sample, half-split
check). MACs per core: a round of 4 parallel decodes shortens only when all 4 of its decodes stop.

**Measured (paired packets, same seeds as the baseline).**

| Point | MACs per core | Lost right packets | Effect on the 1e-3 crossing |
|---|---|---|---|
| 2/5, 0.5 dB (403k packets) | 0.2308 -> 0.1965 M (**-14.9 %**) | 11 (2.7e-5) | <= 0.003 dB |
| 1/2, 1.5 dB (128k) | 0.2328 -> 0.1852 M (**-20.4 %**) | 18 (1.4e-4, +1.3 % of that point's errors) | ~0.001 dB |
| 2/5 0 dB / 1 dB | -21 % / -7.6 % | - | - |
| 1/2 2 dB and up, 1/10 -5 dB | -0 ... -2 % | 0 | - |

Code: `small_rx.py` flag `fzstop` (per code rate), `polar.PolarCode.fz_stop`; receivers in `testing/run.py`. Full study,
predictions and kill rules: [testing/results/expected_f3f5.md](testing/results/expected_f3f5.md).
