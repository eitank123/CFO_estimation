# Ideas that did not work (do not retry without a new reason)

One list of everything tried on the blind CFO receiver that was dropped, with the evidence. Before testing an idea,
check here. An item may be reopened only if the "would change if" condition holds; say so in the prediction file.

Rates: R = 1/10, 0.15, 2/5, 1/2; N = 2048, CRC-16. BLER statements are paired (same packets) unless noted.

## Search and refinement (testing cycle, 2026-11-11 ... 11-13)

| Idea | Result | Evidence | Would change if |
|---|---|---|---|
| Code-aided refinement in Stage 3 (`dd`, s3_dd): CFO / phase from the re-encoded SC codeword instead of the offset x phase scoring | No packet fixed at any of 7 points (with q_fix); 2/5 0.5 dB: 8 fixed / 51 broken, per core +11 %; 0.15 -4 dB without q_fix BLER x1.6 | `testing/results/report_qfix_ddq.md`, testing README "R experiments" | - |
| `dd` + early win at z > 4 (`dd_win4`) | As dd; per core +6 ... +9 % at 1/10, 0.15 | same | - |
| Coarser CFO grid (6 STEP at 1/10 / 0.15, 3 STEP at 2/5 / 1/2), with or without dd | BLER x5 ... x70 wherever errors occur, and MORE MACs (rescue / extra decodes) | testing README R2 | - |
| Early win at z > 4 alone (`win4`) | BLER unchanged, total -3 ... -13 %, but per core +5 ... +6 % at 1/10 -4 and 0.15 -3 dB | testing README R3 | per-core counting changes |
| Fast path off at R = 2/5 and 1/2 | Worse: per core +15 ... +300 %, 0 fixed / 24 broken | `expected_cnf.md` (Measured), `plots/thresholds/thr_fastpath_R2_5_R1_2.png` | - |
| Fast path on at R = 1/10, 0.15 below +0.5 dB | 15-38 % more MACs per core than off (the testing receiver turns it off at <= 0 dB) | `thr_fastpath_R1_10.png`, `thr_fastpath_R0.15.png` | - |
| 2 phase hypotheses per cell at R = 0.15 from -1 to 0 dB | Error bump: 143 / 880k at -1 dB (vs 0 / 400k with 4 phases); q_fix does not remove it | `expected_cnf.md`, `report_qfix_ddq.md` | - |
| Frozen-bit-only cell ranking (Giard et al.: rate-0 + REP nodes, or no SPC) | Same rank of the true cell as the full metric (P(rank <= 4) 0.9725 vs 0.9735 at 0.15 -4 dB) | `testing/results/lit_checks_results.md` | higher code rates (more rate-1 / SPC nodes) |
| Correlation ranking / screening of Stage 3 hypotheses (exp. A, B, D) | Never better than the path metric; thresholds <= 0.5 screen out nothing | testing README table | - |
| Adaptive 1 / 2 / more hypotheses in Stage 3 (exp. C) | T = 1 loses accepted candidates; T = 3 recovers <= 17 / 199 errors for +39 % decodes | testing README | - |
| Re-ranking the final CA-SCL list (exp. F) | 0 hypotheses with the true packet in the list but another path chosen | testing README | - |
| Half-packet consistency check (exp. J) | Right and wrong decodes overlap in every feature | testing README | - |
| spec11 (speculative decode at 4 < z <= 6, rho > 1.1 thr) above the waterfall (1/10 >= -3 dB, 0.15 >= -2 dB) | Per core +3 ... +4 %, BLER identical: the extra decode mostly duplicates the next round's win. Kept below 1/10 -3.5, 0.15 -2.5 dB (`testing_s11g`) | `testing/results/expected_s11.md` | - |
| Multi-candidate DD retry (G), adaptive list size (H) | Not run: upside <= the non-Stage-2 failures (2 of 16 at 1/10 -5 dB) | testing README | Stage-2 failures fixed first |

## Acceptance and false alarms

| Idea | Result | Evidence |
|---|---|---|
| Path metric (PM) instead of the re-encoding check | Accepts 12 / 47 wrong CRC passes at 0.15 -4 dB and 1046 / 1046 noise-only CRC passes; acceptance stays CRC + rho | `report_nn_offline.md` (P1), `plots/nn_pm_vs_rho.png` |
| Speculative decode accepted at the normal threshold (`nofast_spec`) | 1-2 undetected errors per 400k (wrong passes with rho / thr in 1.0-1.1); use spec_rho = 1.1 | `expected_spec.md`, `plots/thresholds/thr_spec_rho.png` |
| Pilot check at 3 sigma (24 pilots) | Rejects ~0.13 % of right decodes, misses the false passes; replaced by rho_n | README A.16.4 |
| "Verified" re-decode at the decision-directed CFO | Identical BLER: a wrong codeword re-converges to itself | README A.16.4 |
| Lag-1 residual phase, false-pass NN | Does not separate right and false passes; rho_n does | README A.16.4 |

## NN ideas

| Idea | Result | Evidence |
|---|---|---|
| NN grid stop (head C: stop the search when the true cell has been seen) | Loses packets at every point (36 / 8000 at 2/5 0.5 dB) | `report_nn_offline.md` |
| NN local refine trigger (head A) | <= 4 % per core even assuming every refine succeeds (oracle 4-6 %) | `report_nn_offline.md` |
| MLPs instead of logistic regression for the gates | Same AUC, more packets lost at the operating points | `report_nn_offline.md` |
| Retry gate (logistic, 13 list / LLR features), "1 %" setting | All 4 rates, 64k paired: 0 fixed / 8 broken pooled (p = 0.008); per core (scheduled) only -9 % at 0.15 -4 and 2/5 0.5 dB, <= 2 % elsewhere | `expected_nnb.md` |
| Retry gate, "0.1 %" setting | Per core (scheduled) -4.5 % at the two hardest points, <= 1 % elsewhere; 0 fixed / 3 broken pooled. Not worth it next to spec11. Would change if: the per-core count goes back to one decode at a time | `expected_nnb.md` |
| Cell grader NN replacing the z-test, posterior NN, blind peak NN, rank NN in the receivers | Same as the analytic rule or worse (peak NN blind: +3 ... +14 % MACs, 1.2-1.7x errors) | README A.16.4 |
| Checkpoint NN at R = 1/10, cut-size NN | No gain or lost BLER | README A.17.6 |

## Cheaper search variants (earlier cycles)

| Idea | Result | Evidence |
|---|---|---|
| Hard cap on the cells (decode only a prior's top 32 / 64 / 128) | True cell outside the top 64 in 63 % of packets at 1/10 -5 dB | README A.17.6 |
| Cheaper neighbour join for blind | ~5x BLER at 1/10 -5 dB; a 3200-packet smoke missed it | README A.17.6 |
| PM beam / gap / phase racing, harder z cut, stride 3, early checkpoint at 1/8 | No gain or lost BLER | README A.17.6 |
| Screening from round 1, screening at -4 dB with z 1.0, adaptive phases at -5 dB | MACs x2-8 or BLER x3-7 | README A.16.4 |
| Smaller first search round, smaller 4th-power FFT / fewer Newton steps on the waterfall | More MACs (z-test needs a population; fast path fails more) | README A.16.4 |
| Fast path at R = 1/10 (earlier receivers), pilot-chosen search phases at 1/10 | <= 7 % right peaks; BLER x2-2.7 | README A.16.4 |
| In-cell retry of near misses (z 1.5-4) | No BLER gain, +5 ... +20 % MACs | memory note, A.16 |
| Rescue lite (64 instead of 256 cells) at 2/5 | -33 % MACs for +30 % BLER: a trade-off, not a gain | README A.16.4 |

## Channel format

| Idea | Result | Evidence |
|---|---|---|
| The OLD receiver without the bit interleaver | Breaks: the pi/2 pairs have identical metrics and PiCode only undoes pi (smoke: 68-167 errors per 400 packets, 4 undetected at 1/10). Without the interleaver use the phase-equivariant receiver (`equiv`, PiCode4) | `testing/results/expected_eq.md` |
| Phase-equivariant receiver (`equiv`, no interleaver, half the phases, PiCode4) at R = 1/10, 0.15 | BLER x1.6-17 and 4-11 undetected per 64k (the phase-invariant re-encoding check cannot reject a wrong pi/2 rotation that passes the CRC), more MACs except 0.15 -4 dB. Works at 2/5, 1/2 (-30 ... -40 % per core, same BLER; see expected_eq.md). Would change if: a rotation-uniqueness check fixes the undetected AND the detected excess | `testing/results/expected_eq.md` |

## Pilot reference receivers (est3)

| Idea | Result | Evidence |
|---|---|---|
| Pilot reference CRC search by the list-1 metric only (" PM": decode the top 3 of all 2M+1 CFO candidates) | Removes the undetected floor but waterfall BLER x3-4.5, per core +20 ... +130 % | `testing/results/expected_fair.md` |
| Pilot reference " PM+3" (decode at f_hat, then at most 3 neighbours in metric order) | Waterfall BLER x2.2-2.9 (0.15 -4, 1/2 2 dB, 480k): the true neighbour is often ranked 4th or lower. " PM+all" (all neighbours in metric order) keeps the BLER and is the fair reference | `testing/results/expected_fair.md` |

## Lessons that apply to every new idea
- A smoke test (100-4000 packets) never proves BLER below ~1e-3: twice a clean smoke hid x5-7 BLER (neighbour join,
  screening). Only paired runs of >= 64k (better 400k) decide.
- Per-core and total MACs can move in opposite directions (win4, 4 phases at 0.15); report both.
- Most remaining errors at the hard points are Stage 2 (the true CFO region never becomes a candidate): changes after
  Stage 2 (lists, acceptance, refinement) cannot fix them.
