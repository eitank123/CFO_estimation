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
