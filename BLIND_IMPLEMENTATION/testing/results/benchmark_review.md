# Benchmark review: blind CFO receiver vs real-world synchronization (2026-11-15)

Technical assessment of the proposed review points, before any further implementation. Every statement is tied to a
measured file where one exists; "[pred]" marks predictions, "[est]" estimates from analysis, unmarked = measured.
Implementation is paused (two in-progress code edits were stopped at a compilable state).

---

## 1. Scientific fairness of the comparison

| # | Question | Verdict | Assessment |
|---|---|---|---|
| 1.1 | Do the comparisons represent the cited methods? | **Modify** | They represent the *synchronization algorithm* of each system transplanted onto our link, not the system. Some layouts are faithful (DVB-RCS2 ID 13 from EN 301 545-2 Table A-1), some are composites we chose: "CCSDS style" (8 x 16 blocks — CCSDS 131.2 uses a long frame marker + 16-symbol pilot fields every 540 symbols), "DVB-S2 style" (one 36-symbol block in a 1024 burst; DVB-S2 places one per 1440 symbols, continuous mode), "400ZR style" (periodic pilots only, no 11-symbol training sequence, 16QAM at ~+19 dB in reality), "VDE-SAT" (a 27-pilot period chosen from three that exist: 17 / 27 / 33, see 2). These must be labelled "-inspired", with the deviations listed. |
| 1.2 | Does our common back-end (polar + CA-SCL-8 + re-encoding check + metric-ordered CRC search) bias the result? | **Agree it is the right control, but say which way it biases** | Using one code isolates synchronization from coding gain — correct for our question. The back-end **favours the competitors**, not us: deployed receivers decode once at the estimate; ours try up to all neighbouring CFO/lobe hypotheses in metric order (measured: the fair search cut the competitors' floor 2-5x, `expected_fair.md`) and accept with the re-encoding check no deployed system has (`lit_real_wlan.md`). Two exceptions to disclose: (a) the competitors lose their native code (turbo/LDPC) — neutral for sync, but their published thresholds are not comparable to ours; (b) DVB-S2 PL-signalling symbols are treated as known (advantage to the competitor). |
| 1.3 | Is pilot-energy normalization right for our objective? | **Agree** | The objective is "same BLER without sending known symbols". Pilots outside the packet cost energy and airtime; charging energy on the SNR axis answers exactly that. It must not be the only axis (1.4). |
| 1.4 | Show raw data-symbol Es/N0 too? | **Agree, mandatory** | Raw Es/N0 shows the synchronization loss itself: on that axis the good pilot receivers sit at the genie (2/5: 128 ML 1.16 - 0.51 = 0.65 vs genie 0.64 dB) and blind is ~0.3 dB WORSE than the genie at 1/10, 0.15 (`lit_adopt_performance.md` [est]). On the normalized axis blind wins by ~the pilot energy. Showing only the normalized axis would hide that, at 2/5 and 1/2, blind's entire lead equals the pilot energy, not better synchronization. |
| 1.5 | Can current assumptions mislead about deployed receivers? | **Yes — the main risk** | (a) **Timing and burst detection are assumed known.** In real systems the preamble does detection + timing + CFO + phase; we credit it only with CFO/phase. A reviewer will say the comparison removes the preamble's main job. (b) Known SNR. (c) Static CFO (no drift). (d) Uniform +-0.03 exceeds the design range of several systems (DVB-RCS2 guideline 0.5-3 %, Griebel 1.5 %, 802.11ad 0.14 %): at the edges we test them outside their design point. (e) Blind and the est4 competitors are NOT paired: different simulators / seeds, and blind's 1/10, 0.15 points have 64k-464k packets with 1-98 errors near the targets (+-0.1 dB). |
| 1.6 | Is the 12.5 % overhead claim consistent? | **Disagree with current text — fix it** | `08_parameters_results.md` 8.3 says "12.5 % throughput loss / blind delivers 12-14 % more data" — that is the OLD framing (est3: 128 pilots INSIDE the 1024 symbols). In the energy-charged framing (est4/est5) pilots are extra symbols: airtime ratio 1024/(1024+Nk) = 0.889 for 128 (11.1 %), 0.898 for 116 (10.2 %), 0.97 for 32. Energy is already charged on the SNR axis; airtime is a separate resource and may be reported separately, but never "12.5 %" together with the energy-charged curves. One framing per figure. |

**Recommended methodology** (section B below) adds: two SNR axes, paired runs of blind and competitors on the same packets, confidence intervals on required-SNR, a timing-offset sensitivity test, and explicit design-range disclosure.

---

## 2. Competitor shortlist

| Priority (proposed) | Verdict | Reasoning |
|---|---|---|
| 1. DVB-RCS2 / Griebel 2021 | **Agree — top** | Burst-mode, return-link, the only real standard whose operating point overlaps ours, published estimator with hardware results. We already have its DA-KS estimator (RCS2-13; ~0 dB estimation loss at 0.15, 2/5, 1/2 measured). Value now: (a) the paper's own FFT 2048/4096 variants = an implementation-realistic version, (b) "faithful" one-decode chain = the reproduction, (c) our alias-lobe search = the improved adaptation, reported separately. The NDA variant (|r| e^{j4 arg r}) is used in the paper only at Es/N0 >= 3.9 dB for QPSK — include for completeness, expect failure below 0 dB. Note the paper's CFO range is 1.5 % (half ours): report results also restricted to |f| <= 0.015, where it is in its design range. |
| 2. VDE-SAT | **Modify — verify before implementing** | Closest standard in SNR (thresholds Es/N0 -4.5 ... -0.6 dB). But M.2092-2 has several satellite link IDs with different pilot periods (17 / 27 / 33), 27- vs 48-symbol syncwords, and a downlink syncword repeated every 1004-4214 symbols. Our "27 + pilot every 27" was not tied to one link ID: the user's warning is valid. Action: pick one link ID (the low-SNR pi/4-QPSK uplink or downlink), copy its exact known-symbol pattern scaled to 1024 data symbols, and document it. Its pilot-only range is 1/54 = 0.0185 < 0.03: in the real system the residual Doppler after compensation would be smaller; disclose. |
| 3. CCSDS telemetry | **Modify** | Valuable as "distributed short pilot blocks" (alias ambiguity + inter-block phase tracking), not as a standard reproduction: CCSDS 131.2 receivers use multi-frame FLL/PLL; our single-burst receiver is our design. Frame it as "CCSDS-inspired distributed pilots", show the alias behaviour (lobes every ~0.006 need +-5 hypotheses) and its phase-noise tracking. Most informative under phase noise / drift, less so in AWGN. |
| 4. DVB-S2 / S2X | **Modify — lower priority** | Deployed DVB-S2 receivers are continuous-mode with multi-frame loops (~100 ms pull-in, `lit_real_space.md`); a single-burst PL-header estimator is not what they do. Our "DVB-S2 style" = a 90-symbol header + one pilot block with M&M — honest only as "PL-header-inspired". DVB-RCS2 (#1) is already the burst-mode member of the DVB family, so DVB-S2 adds little scientifically; keep as an appendix line. |
| 5. 400ZR | **Disagree as a named competitor** | Continuous coherent-optical 16QAM at ~+19 dB with 3.1 % pilots + training sequences, CFO handled by blind coarse + pilot fine over long streams. Transplanting only its pilot period and calling it "400ZR" misrepresents it. Keep a generic "sparse periodic pilots (1/32)" receiver as a low-overhead reference if wanted, without the 400ZR label (cite 400ZR only as evidence that +-0.03 CFO is a real requirement). |
| (not proposed) 128-preamble ML / M&M, 64+64 joint ML | **Keep** | Already measured; the generic burst-modem baseline (Comtech/DOCSIS/Hughes class, `lit_real_leo.md`, `lit_real_terrestrial.md`). |
| (not proposed) Dense pilots 1/7 (LTE/NB-IoT DMRS) | **Add as the phase-noise reference** | No aliases inside +-0.03 and the best pilot phase tracking: the competitor most likely to BEAT blind under phase noise / drift — exactly the limitation we should expose. |
| Wi-Fi style, ViaSat UW, hyb3, MIL-110 | **Appendix / drop** | Wi-Fi: CFO design range 22x smaller, our version needed two fairness fixes to not be a strawman. ViaSat / hyb3: 4th-power based, fail below 0 dB (already shown by C2). MIL-110: 1.14 dB of pilots, a predictable "heavy pilots" anchor; optional. |

---

## 3. Measured vs predicted; the prediction model

| Question | Verdict | Assessment |
|---|---|---|
| Reliability of SNR_req ~ genie + E + d | **Modify** | Calibrated in-sample on 3 measured points (128 ML, RCS2-13 at 2/5, 128 ML at 1/10) — not independently validated. It is reliable only where the CFO estimate is unambiguous and accurate (d ~ 0). |
| Does d capture lobe errors / false CRC acceptance? | **Disagree that it does** | Measured counter-examples: RCS2-13 at 1/10 -5 dB (d = 0.63 dB from 1/20 aliases), 64+64 joint ML at 1/10 (-2.87 vs genie+0.51 = -4.68: d = 1.8 dB from 1/1088 lobes), preamble receivers' undetected floor 2-6 per 480k. None was predicted by the rule. Floors and rare ambiguity errors need simulation. |
| Most likely to deviate | — | VDE-SAT (alias peak 0.59 of the true one), CCSDS-inspired (dense aliases), sparse 1/32 pilots (weak coarse stage), DVB-S2-inspired at -5 dB (90-symbol M&M), Griebel faithful (no search), ViaSat / hyb3 (4th-power threshold). Most credible: dense 1/7 pilots, MIL-110, Griebel FFT 4096 (= RCS2-13). |
| Avoid quantitative claims until simulated? | **Agree** | `competitors.md` mixes measured rows and [pred] rows in one table: split into "measured" and "predicted (planning only)"; plots never show predicted curves. |

---

## 4. Genie baseline

**Modify.** The single-decode genie conflates decoding diversity with synchronization: blind beats it at 2/5, 1/2
(measured 400k: blind 848 vs genie 1306 errors per 400k at 2/5 0.5 dB, `expected_eqrb.md`). Proposed set:
1. **Genie, CA-SCL-8, one decode** (keep: the classical bound, comparable with the literature).
2. **Oracle-cell blind** (instead of "genie with comparable budget"): the blind receiver with Stage 2 replaced by the
   true CFO cell and phase branch, everything else identical (refinement, retries, joint list, acceptance). This is the
   cleanest way to separate SEARCH loss from DECODING: blind - oracle-cell = what the CFO search costs. A "matched budget"
   genie is ill-defined (budget of what: decodes? MACs?) and would be argued about.
3. **Genie, CA-SCL-32** (agree): measures the decoder gap the literature scout estimated at 1.1-1.3 dB from the
   finite-length bound [est], and frames list escalation as a decoder improvement available to every receiver.
Also apply the same CRC-search/retry diversity to the pilot receivers' genie view: report each competitor against its
own "oracle-CFO" version (true CFO, its own phase estimate) to separate CFO from phase errors.

---

## 5. Pilotless code-aided comparison

**Agree with the two-question framing; modify the candidate list.** Feasibility from what we could read:
| Method | Detail available | Faithful reproduction possible? | Recommendation |
|---|---|---|---|
| Code-aided EM (Noels-Steendam-Moeneclaey 2005; Herzet 2007) | full text (EURASIP open access) | yes, as a FINE stage; pull-in ~1/N (EM is local) | Build the classical pilotless pipeline "NDA 4th-power coarse + code-aided EM fine" — the textbook pilotless receiver. Expect failure below the 4th-power threshold (~0 dB), i.e. at all low-rate points. |
| Syndrome / decoder-metric blind search (Imad-Houcke-Ghogho 2010) | full text | the cost function is LDPC-specific; for polar the analogue is the frozen-bit metric = our own exhaustive grid without checkpoints | Present as an **ablation**: exhaustive decoder-metric search over all cells, no checkpoints / no early decisions. This directly measures what our checkpoint machinery saves (MACs at equal BLER) — the algorithmic contribution. Call it "Imad-type exhaustive search (adaptation)". |
| Polar-code-aided CFO (Wu 2025) | full text (EM-based) | yes, but pull-in |f| <= 2e-4 | Only as a fine stage after our grid; compare fine RMSE vs MCRB, not acquisition. |
| Pilotless LDPC sync (Yang 2026, Xu 2024) | abstracts only (IEEE) | no | Do not claim a reproduction; cite. Full texts needed (DOIs in `lit_adopt_codeaided.md`). |
| Cross-entropy / Taylor (Yue 2026) | preprint full | partly (BP posteriors -> adapt to SCL soft output); needs a prior FFT acquisition to 7.8e-3 | Low priority; adaptation only. |

---

## 6. Complexity and performance presentation

**Agree**, with these changes:
- The Pareto plot (required normalized SNR at fixed BLER vs scheduled MACs per core, labelled with Nk) is the right
  headline. Add the **raw-Es/N0 variant** and **airtime** as a third annotation. Make one per rate (1/10 and 0.15 never
  in one figure).
- Label honestly: our MACs are **modelled operation counts** from the code paths (vp.MAC model), not instrumented
  hardware cycles; "scheduled MACs per core" is a **scheduling model** (32 cores, 4 decodes per round). Neither is a
  hardware measurement.
- Worst case: report p99 / p99.9 / max per packet (already in the summaries) and the effect of the hard MAC cap.
- Add required-SNR confidence intervals (bootstrap over chunks or Clopper-Pearson at the crossing points).
- CFO RMSE: report vs MCRB, separating "used for decoding" from the post-acceptance final estimate.
- Undetected errors and noise-only false alarms: per receiver, noise-only at >= 1e6 hypotheses for blind.

---

## 7. Robustness

| Test | Verdict | When |
|---|---|---|
| A. CFO drift (linear ramp over the burst) | **Agree — include now, small** | Cheap (one parameter), flagged independently by two surveys (HF 3.5 Hz/s, narrowband NTN). Two points (0.15 -3.5, 2/5 0.5 dB), drifts 0.003 / 0.01 / 0.03 total over the burst, blind vs RCS2-13 (track) vs dense pilots. Our cell grid assumes a constant CFO: this is where blind is most likely to lose. |
| B. Phase noise | **Agree — partly done, extend after AWGN** | Measured already: blind (+pns) vs C1-C4 at 1e-5 / 1e-4 / 3e-4 (`expected_est4.md`, `expected_pns.md`): DVB-RCS2 with Kalman tracking BEATS blind at 0.15 and 2/5 under 1e-4. That must be in the final story, not hidden. Add dense pilots + CCSDS-inspired tracking. |
| C. (added) Timing offset | **Add** | The most likely reviewer objection (1.5a). A fractional timing offset (+-0.5 symbol) with each receiver's own timing estimate — or at least blind's sensitivity to an uncorrected offset. |
| D. (added) SNR mismatch | **Add (cheap)** | Blind's thresholds use the SNR estimate; one +-1 dB mismatch point exists (re_margin); repeat in the final setup. |

---

## A. Ranked competitor shortlist
1. **DVB-RCS2 ID 13 family**: measured RCS2-13 (+ Kalman track), plus Griebel FFT-2048/4096 variants, the faithful one-decode chain, and the alias-search adaptation — reported as three distinct things (reproduction / realistic implementation / our improvement).
2. **128-symbol preamble, ML** (measured; generic burst modem) — the simplest reference everyone understands.
3. **VDE-SAT** — after fixing one link ID's exact pattern.
4. **Dense pilots 1/7 with tracking** — the strongest under phase noise and drift: the honest "where pilots win" case.
5. **CCSDS-inspired distributed blocks** — alias + tracking behaviour.
6. **Pilotless references**: NDA 4th-power + code-aided EM; exhaustive decoder-metric search (ablation).
Appendix: 64+64 joint ML, 16+16 4th power, DVB-S2-inspired, sparse 1/32 pilots, MIL-110; drop Wi-Fi, ViaSat, hyb3 from the main figures.

## B. Benchmark methodology a reviewer would accept
1. **One link model for all**: same packets (paired seeds) for blind AND every competitor — run blind inside the same harness or seed-align the simulators; McNemar per point for paired claims.
2. **Two SNR axes**: raw data-symbol Es/N0 (sync loss) and burst-energy-normalized (the objective); airtime reported separately; one framing per figure.
3. **Required SNR at BLER 1e-3 and 1e-4 with CIs**; >= 100 errors near each crossing (400k-2M packets at the low rates).
4. **Three references**: genie CA-SCL-8 (one decode), oracle-cell blind (same back-end), genie CA-SCL-32.
5. **Labels**: "reproduction" only for faithful chains (Griebel faithful, RCS2 ID 13 layout); everything else "-inspired adaptation", with a deviations table; design CFO range of each system next to its curve; optional results restricted to each system's design range.
6. **Complexity**: modelled total MACs, scheduled per-core model, p99 / max, Pareto plot; never mixed with hardware claims.
7. **Error types**: detected, undetected (wrong CRC pass), noise-only false alarms (>= 1e6 hypotheses).
8. **Robustness block**: CFO drift, phase noise, timing offset, SNR mismatch — reported even where blind loses.
9. **Measured vs predicted**: predictions only in planning documents, never on plots.

## C. Assessment of competitors.md predictions
- Credible (rule valid, unambiguous estimates): Griebel FFT 4096 (= RCS2-13), dense 1/7 pilots, MIL-110, DVB-S2-inspired at 2/5 and 1/2.
- Plausible but needs simulation: VDE-SAT (aliases), Griebel FFT 2048 (+0.03-0.2 dB), sparse 1/32 pilots.
- Unreliable (ambiguity / threshold dominated): CCSDS-inspired at -5 dB, Wi-Fi (before the fairness fixes), ViaSat, hyb3, Griebel faithful, DVB-S2-inspired at 1/10 -5 dB.
- The table's "vs blind" column compares predictions with blind numbers from UNPAIRED runs: move to "planning" status.

## D. Implementation roadmap (value / effort)
1. **Docs fixes** (hours): 08 8.3 overhead framing; split competitors.md into measured / predicted; deviations table; design ranges; state timing/SNR assumptions.
2. **Plots from existing data** (hours): raw-Es/N0 versions of the fair figures; Pareto plot for the 4 measured competitors; CIs.
3. **Oracle-cell blind + genie L32** (1-2 days incl. runs): isolates search loss vs decoding diversity — the most important missing control.
4. **Paired blind in the est4 harness** (1-2 days): makes every blind-vs-competitor statement a paired one.
5. **Griebel / RCS2 variants** (code ~done, paused; 1 day runs).
6. **CFO drift test** (1 day): blind vs RCS2-13 track vs dense pilots at 2 points.
7. **VDE-SAT** after link-ID verification (1-2 days).
8. **Dense pilots 1/7 + CCSDS-inspired** under AWGN and phase noise (code done, paused; 1-2 days runs).
9. **Pilotless references**: exhaustive-search ablation (cheap: a flag), NDA + EM (2-3 days).
10. **Timing-offset sensitivity** (2-3 days: needs a timing model in the chain).
11. Appendix competitors (DVB-S2-inspired, sparse pilots, MIL-110): only if time.

## E. Weaknesses in our current claims
1. Preamble functions other than CFO (detection, timing, SNR) are not credited; blind assumes them solved.
2. At 2/5 and 1/2 blind's lead equals the pilot energy: on raw Es/N0 blind = genie = good pilot receivers; the claim is "pilot-free at no sync loss", not "better synchronization".
3. At 1/10, 0.15 blind is ~0.3 dB from the genie (search loss) [est] and ties / slightly loses to the best pilot receivers at BLER 1e-4 (0.15: -2.98 vs -3.12 dB).
4. Under phase noise (1e-4) the DVB-RCS2 tracking receiver beats blind at 0.15 and 2/5 (measured); pns recovers only 10-23 %.
5. Complexity: 2-12x the MACs per core of pilot receivers; modelled, not hardware.
6. Unpaired blind-vs-competitor comparisons; low error counts on blind's low-rate points; pooled-floor smoothing in the presentation figures (disclosed in the legend, must also be in the text).
7. Uniform +-0.03 CFO is beyond several competitors' design ranges.
8. R = 0.15 runs settings tuned for 1/10; NN components trained on the same distribution as the test.
9. "Beats the genie" at 2/5, 1/2 is decoding diversity, not synchronization.
10. The 12.5 % overhead statement uses the old inside-the-packet framing.

## F. Preferred final presentation
1. **Problem slide**: CFO +-0.03 is real (MIL-STD-188-110, 400ZR, uncompensated LEO at 1-16 Msps, GEO 1 ppm at ~470 ksps).
2. **Headline: Pareto plots per rate** — required SNR (normalized, BLER 1e-3) vs scheduled MACs per core; points labelled with Nk; blind at Nk = 0.
3. **Two BLER figures per rate**: normalized (objective) and raw Es/N0 (sync loss), with blind, genie L8, oracle-cell blind, RCS2-13, 128 ML, VDE-SAT; CIs at the crossings.
4. **Decomposition bar**: blind's gap to the genie split into search loss (blind - oracle-cell) and decoder gap (genie L8 - L32 - bound).
5. **Robustness panel**: drift and phase noise — including where pilots win (DVB-RCS2 track, dense pilots), and what pns recovers.
6. **Complexity panel**: where the MACs go, what the checkpoints save vs the exhaustive search (ablation), worst case and the cap.
7. **Honest limitations slide**: timing/detection assumed, modelled complexity, adaptations not reproductions.
Message: "a pilot-free burst receiver that reaches the BLER of standard pilot-assisted receivers at equal energy, with 0 known symbols, at 2-12x their decoding complexity; pilots still win under strong phase noise / drift."
