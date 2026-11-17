# How the "CFO Estimation & Blind CFO Receiver" deck is maintained

Written 2026-11-17 by the cloud session that built the current version, on request of the local session.
Everything below is the state at commit time; the user also edits the deck by hand (deletes slides, moves boxes),
so always re-read the deck before editing it.

## 1. The deck
- Google Slides, presentation ID `1fF29ZDn7ZlKsJvW8bFxpMtD8-vc4T4yj4Obfrmd932c`
  (https://docs.google.com/presentation/d/1fF29ZDn7ZlKsJvW8bFxpMtD8-vc4T4yj4Obfrmd932c/edit). No other deck.
- Page 12192000 x 6858000 EMU (16:9). Slides are BLANK layout with hand-made elements (see section 4).
- Edited with the Google Slides MCP tools: `read_presentation` (use a field mask, e.g.
  `slides(objectId,pageElements(objectId,shape.text.textElements.textRun.content))`), `read_slide_page`,
  `read_slide_page_thumbnail` (render check: download the PNG and look at it) and `update_presentation` (batchUpdate).

## 2. Slide list (32 slides, in order)
| # | objectId | Title | Figure / images |
|---|---|---|---|
| 1 | p1 | CFO Estimation & Blind CFO Receiver | - |
| 2 | p2 | Outline | - |
| 3 | h53e440704b309bbf_0_0 | Offset correction pipeline | block diagram (shapes) |
| 4 | p3 | Carrier frequency offset and the pilot baseline | equation PNGs (render_eq.py) |
| 5 | h6b1ac0df4dc7c549_5_2 | Mengali & Morelli estimator (baseline) | equation PNGs |
| 6 | ml_slide | ML estimator on 128 pilots (BLER baseline) | ml1 ... ml5 |
| 7 | h544f61a385580e47_0_22 | CRC search around the estimate | - |
| 8 | h26f0fe4afcb54c7f_0_0 | Blind CFO estimation | model equation |
| 9 | h26f0fe4afcb54c7f_0_15 | Blind CFO receiver: proposed method | three stage cards (shapes) |
| 10 | flow_slide | Blind receiver: decision flow | flow chart (shapes) |
| 11 | fp_slide | Stage 1: the 4th power removes QPSK | model, s4, v4, nu |
| 12 | fft_slide | Stage 1: the FFT finds the CFO | fft_s, kb_s, f0_s |
| 13 | ph_slide | Stage 1: carrier phase and pre-MF correction | ph1 / theta0 / mod / premf |
| 14 | br_slide | Stage 1: scoring a hypothesis with the decoder | xh, lam, path-metric equations |
| 15 | ps_slide | Stage 2: the decoder as a CFO detector | path-metric equations |
| 16 | gr_slide | Stage 2: the grid of hypotheses and checkpoints | grid equations + checkpoint timeline (shapes) |
| 17 | zt_slide | Stage 2: the z-test finds the right cell | z-test equations |
| 18 | s3_slide | Stage 3: refine, decode and retry | refinement / code-aided equations |
| 19 | tr_slide | Testing receiver: switching the fast path off | fastpath_switch.png (tr_img6) |
| 20 | f5_slide | Stage 3: frozen-bit early stop (F5) | f5a.png (f5_eqa3), f5b.png (f5_eqb2), f5_thr.png (f5_img3) |
| 21 | re_slide | Re-encoding check | re-encoding equations |
| 22 | thr_slide | Why these thresholds: the measured evidence | thresholds.png (thr_img2) |
| 23 | par1s | Parallel decoding on 32 cores: what runs at once | crit_p, tdec_p equations |
| 24 | cmp_slide | The compared receivers: where they are used and why | table cmp_tab3 (no figure) |
| 25 | rcs_slide | DVB-RCS2 ID 13: how the pilot receiver works | rcs_alg.png (rcs_img2, pilot layout strip only), rcs1-3.png |
| 26 | vde_slide | VDE-SAT: how the pilot receiver works | vde_alg.png (vde_img2, layout strip only), vde1-2.png |
| 27 | h26f0fe4afcb54c7f_0_9 | BLER vs SNR: blind vs pilot-based receivers | fair_bler.png (res_img5) |
| 28 | eb_slide | BLER vs SNR without the pilot energy | raw_bler.png (eb_img2) |
| 29 | capb_slide | BLER with a hard cap on the MACs per core | cap_bler.png (capb_img4) |
| 30 | macs_slide | Complexity: MACs per core vs SNR | fair_macs.png (macs_img6) |
| 31 | capm_slide | MACs per core with a hard cap | cap_macs.png (capm_img5) |
| 32 | cc_slide | Conclusion & future directions | - |

Image object IDs change every time an image is replaced (img2 -> img3 ...): read the slide first.

## 3. How a figure gets into a slide
1. Generate the PNG with the script in `slides_eq/` (dpi 200; equations: `render_eq.py`, dpi 300, 26 pt).
2. Commit and push to branch `claude/festive-feynman-3o19mb` of eitank123/CFO_estimation.
3. Use the raw URL pinned to the commit SHA (not the branch name, which caches):
   `https://raw.githubusercontent.com/eitank123/CFO_estimation/<SHA>/slides_eq/<file>.png`.
   Check it returns 200 first (`curl -o /dev/null -w "%{http_code}"`); right after a push createImage can fail with
   "problem retrieving the image": wait a few seconds and retry.
4. Replace an existing figure: `deleteObject` the old image, then `createImage` with a new objectId on the same
   page, same size / position (keep aspect ratio: height = width x png_h / png_w). There is no in-place replace.
5. Standard placements (EMU):
   - full-width 4-panel figure: width 10900000, translate (646000, 1200000); text box below at x 758952, width
     10674000, from figure bottom + 20000 to y 6330000, Calibri 12-13 pt, dark text rgb(0.1216, 0.1608, 0.2157), bullets
     BULLET_DISC_CIRCLE_SQUARE.
   - 2/3-panel figure: width 10000000-10900000, translate x (12192000 - w) / 2, y 1250000.
6. New slide: `createSlide` (BLANK, insertionIndex) + rule rectangle (3000000 x 3000000 at scale 3.557 x 0.0091,
   translate 758952, 1124712, navy fill, no outline) + title text box (667512, 457200, 10972800 x 640200, Arial 28 pt
   bold navy rgb(0, 0.2, 0.4)) + page number box (11201400, 6400800, 777300 x 274200, Calibri 10 pt grey
   rgb(0.357, 0.396, 0.451), text "n/N"). After inserting / deleting slides renumber every "n/N" with replaceAllText
   scoped by pageObjectIds, and fix textual cross references ("slide 22").
7. Text edits: `replaceAllText` with `pageObjectIds` scoped to the slide (exact old text, matchCase).
8. Always render-check: `read_slide_page_thumbnail` LARGE, download the contentUrl, look at it (overlaps, wrapped
   titles, missing glyphs: Calibri lacks some sub/superscript Unicode, e.g. superscript l, so write plain text).

## 4. Visual style
- Colours: blind navy #003366 (solid, lw 2.8-3, marker o); DVB-RCS2 orange #E07B39 (s, dashed); VDE-SAT brown #8c564b
  (P, dashed); 128-symbol preamble ML grey #777777 (^, dashed). Savings bars green #2e8b3d, costs red #c8423b.
- Font DejaVu Sans 13-14 pt in plots; titles bold "R = 1/10" per panel; legend below the panels (fig.legend, frameon
  False); log y for BLER and MACs; MAC axes with plain ticks (0.05, 0.1, 0.2, ...), no minor ticks.
- SNR axis: "SNR [dB], pilot energy charged" = Es/N0 + 10 log10((1024 + Nk) / 1024) (pilots outside the packet).
  Slide 28 uses Es/N0 per transmitted symbol (pilot energy NOT charged).
- BLER curves: join runs of >= 2 adjacent SNRs with errors; 0-error and isolated points are not drawn.
- Legends: no "(+x dB)" pilot-energy tags, no "(measured)" / "(model estimate)" tags.
- Slide text: short bullets, numbers only from the data / READMEs, page numbers "n/N".

## 5. User instructions (most recent last; verbatim where possible)
- Don't invent results; follow the code over the docs; if data is missing, say so ("if you are missing any data just
  tell me, dont assume anything").
- "remove the (model estimate) and (measured MAC count) from the titles"
- "remove the CNN clasification from the comparison"
- "in the threshold slides make it plots and not tables"; then "z-test and rho threshold plots are great (leave the tru
  cell z=10 regon out of the plot), MAC threshold just give me BLER vs MAC cap"
- "update the slides with the most relevant competitors and use the new testing model that saves macs"
- "I dont want the plots to be for a certain required SNR but for them to be BLER vs SNR or MACs vs SNR"
- Competitors: first 4 (DVB-RCS2, VDE-SAT, CCSDS, DVB-S2), then final: "only compare this 3 with the new blind":
  DVB-RCS2 ID 13, VDE-SAT, 128-symbol preamble ML. "no genie".
- "remove the (+xdB) from the titles" (legend entries)
- "also update the stages to represent the new blind algorithm"; "dont make them notes, add a slide explaining the
  threshold and a plot showing how much it saves" (F5 and testing-receiver changes)
- "make slides 19,20, 21 clearer and their plots less complex"; "add 2 slides, one for each model we compare against
  explaining the algorithm"
- BLER vs Eb/N0 was added then rejected: "nevermind, delete the BLER vs Eb/N0, instead give BLER vs SNR where the SNR
  does not include the pilot overhead SNR degredation" (slide 28)
- Slide 19: first a saving histogram per SNR, then "make the histograms red and green (positive and negative), leave
  only R=1/10 and R=0.15", then replaced by the user's own fast-path switch histograms (values in
  plot_fastpath_switch.py; R = 2/5, 1/2 shown as costs).
- Slide 20: "make the paragraph explaining the equation (and the equation itself) clearer, remove the star from the
  plot just leave the vertical line where the threshold is"; "you can just type instead of the sum M(i)" (psi = mean of
  Delta M(i) over decided frozen bits).
- The user deleted slide 21 (F5 saving) and the testing-vs-presentation table slide themselves: don't re-add.
- Slides 25-26: "remove the amplitude vs freq plot and leave only how the pilot distribution plot".
- Slide 31: "remove from the plot the blind with no cap and add the other algorithms macs"; "add a number in the
  y-axis of the flat region of the other algorithms"; "remove the 2M or 1M grey line in the MACs capped plots".
- Latest (2026-11-17, open): corrected DVB-RCS2 search at R = 1/10. Slide 27 text updated (blind -4.78 ties 128 ML
  -4.72; 0.20 dB ahead of DVB-RCS2 -4.58 with the correct search; old +0.69 was a search defect; other competitors with
  known search holes not re-run). The PLOT still shows the old DVB-RCS2 curve: the corrected data
  (expected_fx.md, est4 results, or bler_fair_R1_10.png) is not pushed yet. To do when it lands: R = 1/10 panel with
  DVB-RCS2 corrected solid and old dashed; minimal change. Slides 28, 29, 32 still quote the old 1/10 numbers (asked the
  user whether to fix them). VDE-SAT stays "fails 1e-4 at 1/10".

## 6. Data and regeneration
Data are snapshots in `slides_eq/data/` (from a checkout of full-chain-cfo; the scratch checkout is not in the repo):
| File | From | Used by |
|---|---|---|
| curves_17b16ea.json | full-chain-cfo 17b16ea, `BLIND_IMPLEMENTATION/testing/plot_curves.data(rate)` (blind = adopted testing receiver, competitors = `plot_e4.e4(e5, ars, var)`) | plot_fair.py (fair_bler, fair_macs, raw_bler), plot_cap_testing.py |
| cap_testing_17b16ea.json | 17b16ea, the packet pool of `testing/plot_cap_fair.py` (pg_ / ph_ histograms) | plot_cap_testing.py (cap_bler, cap_macs) |
| fz_f5_17b16ea.json | 17b16ea `testing/results/fz_f5.json` | plot_testing_changes.py (f5_thr) |
| f5_paired_17b16ea.json | 17b16ea `agg_cmp.FZS` parts | plot_testing_changes.py (f5_save, not in the deck now) |
| testing_vs_pres_17b16ea.json | 17b16ea `agg_cmp.pres_fix_macs` vs `adopted` / `testing_hi` | plot_saving_hist.py (not in the deck now) |
| layouts_est4.json | 17b16ea `est4.common.layout('rcs13' / 'vde27')` | plot_competitor_algos.py |
| results_c90c5b7.json | c90c5b7 (older presentation receiver) | plot_results.py, plot_thresholds.py |
| scoreboard_2026-11-17.md | user upload | reference numbers |

Regenerate (from the repo root): `python slides_eq/plot_fair.py`, `python slides_eq/plot_cap_testing.py`,
`python slides_eq/plot_testing_changes.py`, `python slides_eq/plot_fastpath_switch.py`,
`python slides_eq/plot_competitor_algos.py`, `python slides_eq/plot_thresholds.py`,
`python slides_eq/render_eq.py [names...]` (equations; no names = all). To refresh a JSON snapshot, check out the new
full-chain-cfo commit and run the matching loader with `BLIND_STUDY=small_cfo` (e.g. `plot_curves.data`, keep only the
receivers the deck uses).
