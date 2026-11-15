# Blind CFO research news

Newest first. One item per research result. Details in the linked files; sources in [REFERENCES.md](REFERENCES.md).

---

## 2026-11-15 12:10 — Your papers list (Yang 2026, Xu 2024, Yue 2026, Wu 2025): none can replace the grid; soft symbols can improve refinement / retry / pns
- **Found:** all four refine CFO/phase from the decoder's SOFT posteriors, starting from a small residual: Yang 2026
  (LDPC partial-metric gradient + Costas loop, within 0.1 dB of ideal sync at Eb/N0 1-2 dB), Yue 2026 (64-point FFT
  acquisition to |f| <= 7.8e-3, then cross-entropy search scored by BP posteriors + Taylor/EM; polar (1024,512) BPSK,
  0.3 / 0.4 dB loss), Xu 2024 (wide-range estimator + EM in LDPC; range not in the abstract), Wu 2025 (EM, |f| <= 2e-4:
  cannot acquire our 0.03). No 2023-2026 paper drives a wide-range search with partial decoder metrics.
- **Adopt (A1):** use soft symbols (tanh of the posterior LLRs, ~8k MACs; or a SCAN backward pass ~45-50k) instead of
  the hard re-encoded codeword in our DD refinement, retry and pns — exactly the measured pns limit (decision errors).
  Test offline on the refinement dumps first. (A2) 2-3 pns iterations with list-1 passes in between.
- **Do not adopt:** cross-entropy / gradient acquisition (our metric is a needle one cell wide: 120 samples hit the true
  cell with p = 0.45).
- **Full texts not readable here (IEEE):** Yang [10.1109/ACCESS.2026.3653159](https://doi.org/10.1109/access.2026.3653159),
  Xu [10.1109/TVT.2024.3383891](https://doi.org/10.1109/tvt.2024.3383891) — worth downloading if you have access.
  Yue preprint [arXiv 2309.12828](https://arxiv.org/html/2309.12828). Full: `testing/results/lit_adopt_codeaided.md`.

## 2026-11-15 12:07 — Complexity ideas: reuse the SC codeword we already compute; one de-rotation per cell
- **A1 (top):** the code-aided retry recomputes a full SC pass the receiver has just done at the same hypothesis — cache
  it (-13...-19 % per core where retries dominate). And "SC first": check CRC + re-encoding on that SC codeword before the
  CA-SCL-8 decode, list only if it fails (Sarkis JSAC 2016, Li-Shen-Tse 2012, Condo PDCCH two-phase). Estimated per core
  -6...-17 %, -20 % at 1/2 2 dB, ~-20 % on fast-path-only points — if SC alone passes ~90 % of right hypotheses (to measure).
- **A2:** share one de-rotation per CFO cell across its phase hypotheses (pi/2 steps are swaps / sign flips): -10...-15 %
  per core at 1/10 -5, 0.15 -4 dB, no BLER risk (a recount from stored counters).
- **A3-A5:** Stage-2 metric on reliable frozen leaves only (-6...-12 % search, offline first); successive halving in the
  refinement scoring (-3...-7 % total); pruned FFT in the fast path (-1...-5 %).
- **Rejected:** dynamic list size (paths already parallel in our model), chirp-z de-rotation, multiplier-free 8-phase,
  SPRT with absolute thresholds.
- **Links:** [Sarkis JSAC 2016](https://ar5iv.labs.arxiv.org/html/1505.01466), [Condo two-phase PDCCH](https://ar5iv.labs.arxiv.org/html/1801.01820),
  [Qualcomm US10742238](https://patents.google.com/patent/US10742238B2/en). Full: `testing/results/lit_adopt_complexity.md`.

## 2026-11-15 12:07 — All sources now in one file: REFERENCES.md (93 sources)
- Every paper, standard and patent cited so far, each with link, what it does, what we took and a dated "Used in" log
  (eqrb <- Geiselhart 2023; pns <- Colavolpe 2005; F3 <- Yuan 2021; est4 competitors <- EN 301 545-2, Griebel 2021,
  Barbieri-Colavolpe 2007, ...). The new survey entries will be merged in next. `BLIND_IMPLEMENTATION/REFERENCES.md`.

## 2026-11-15 12:03 — Where the dB really are: the decoder is ~1.2 dB from the finite-length bound, the CFO search only ~0.2 dB
- **Found [derived from the normal approximation, Coskun et al. 2019]:** with the true CFO and phase, our CA-SCL-8 is
  ~1.3 dB from the finite-blocklength bound at 1/10 and ~1.1-1.2 dB at 0.15, 2/5, 1/2. Blind minus genie is ~0.3 dB at
  1/10, 0.15 and ~0 at 2/5, 1/2, of which ~0.06-0.1 dB is unavoidable. So a better search can win at most x7 BLER at
  1/10 -5 dB, x2 at 0.15 -4 dB and nothing at 2/5, 1/2; the decoder is where the rest is.
- **Top idea — list escalation (P1):** when a packet is about to be lost, decode its best 1-2 hypotheses again with
  list 32 (128 on the best). Literature: Li-Shen-Tse ((2048,1024)+CRC-24, 0.2 dB from the limit), Giard 2017 (+0.35 dB
  from L 8 -> 32 at R = 1/8). Predicted BLER x3-6 lower at 2/5 0.5 dB, x4-10 at 1/2 2 dB, x1.3-1.8 at 0.15 -4 dB, for
  < 0.5 % more total MACs (only would-be failures). Risk: more wrong CRC passes -> recalibrate the re-encoding check.
- **First, a zero-risk diagnostic (T1):** genie with lists 8 / 32 / 128 on 64k packets at the 4 points, and which
  checkpoint drops the true cell at 1/10 -5 dB.
- **Rejected:** PAC codes (gain only at short lengths), OSD / GRAND (too costly at our K), LLR combining across cells
  (~0.02-0.05 dB). Also: more pns passes (P2) for phase noise.
- **Links:** [Coskun et al. 2019](https://ar5iv.labs.arxiv.org/html/1812.08562), [Li-Shen-Tse 2012](https://arxiv.org/abs/1208.3091),
  [Giard 2017](https://ar5iv.labs.arxiv.org/html/1705.02111), [Pillet 2026 SCL-Flip](https://arxiv.org/abs/2605.08492).
  Full: `testing/results/lit_adopt_performance.md`.

## 2026-11-15 12:03 — Military HF: our +-0.03 CFO is exactly the MIL-STD-188-110 requirement (with lots of known symbols)
- **Found:** MIL-STD-188-110C App C / D (tactical HF modems) require sync at +-75 Hz at 2400 Bd = |f| 0.031 cycles/symbol,
  our range; but they carry 11-50 % known symbols (a 1440-symbol preamble alone) and are specified at ~3-4 dB Es/N0 and
  above (+-75 Hz tested at 30 dB). Deployed receivers use banks of frequency hypotheses (Harris US7315588, QinetiQ
  US7715499: 10 Hz bins lose > 2 dB between bins), the same idea as our CFO cells; underwater modems use the 4th-power
  DFT (our fast path). Blind SIGINT estimators reduce to the 4th-power family for QPSK.
- **New competitors (added to est5):** "MIL-110 HF" layout scaled to 1024 data symbols (~308 known, +1.14 dB): expected
  genie + 1.14 dB, i.e. ~0.5-1.2 dB behind blind; "hyb3" (Advantech US7590199: pilot + 4th-power log spectra, 3 CFO
  candidates decided by the decoder) on 16+16 known symbols (+0.13 dB).
- **Side finding:** HF Doppler rate (3.5 Hz/s) would leave ~0.25 rad of quadratic phase over our burst; we do not model a
  CFO ramp yet — a small ramp test is worth adding.
- **Links:** [MIL-STD-188-110C](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf),
  [Advantech US7590199](https://patents.google.com/patent/US7590199), [Hosseini-Perrins 2013](https://ar5iv.labs.arxiv.org/html/1310.0757),
  [ETSI EN 301 841-1 (VDL2)](https://www.etsi.org/deliver/etsi_EN/301800_301899/30184101/01.04.01_60/en_30184101v010401p.pdf).
  Full: `testing/results/lit_real_military.md`.

## 2026-11-15 12:01 — Space agencies and DVB: comparable designs are CCSDS pilot blocks and the ViaSat 4th-power + unique-word burst
- **Found:** official single-carrier standards keep the CFO small (DVB-RCS terminals locked to the network clock:
  1e-8), pull it in over many frames (DVB-S2 pilot FLL: +-0.2 -> 4e-3 in ~100 ms; CCSDS 131.2 SCCC: FFT FLL on a
  256-symbol marker + 16-symbol pilot blocks every 540 symbols, 0.2-0.4 dB loss, lowest mode Es/N0 -0.58 dB), or work
  at higher SNR. DVB-S2X very-low-SNR: 900-symbol unique word, only for CFO <= 1 % of Rs.
- **Most comparable for us:** (1) ViaSat US 7653150: 512-symbol QPSK burst, CFO up to 10 % of Rs, 4th-power FFT +
  16-symbol midamble for the pi/2 ambiguity, ~0.2 dB loss at Es/N0 ~2.6 dB = the industry version of our fast path and
  of our 16+16 competitor; (2) CCSDS / DVB-S2-style pilot blocks with the same 128 known symbols (8 x 16, FFT over all,
  per-block phase + interpolation) as a new competitor C5. Mengali-Morelli is the estimator chosen in a CCSDS study
  (1.2x CRB at -2 dB): already our M&M competitor.
- **GEO numbers:** NCR-locked terminal 140 Hz at 14 GHz; f = 0.03 needs Rs ~53-126 ksps with the RCS2 budget, or ~470
  ksps for a free-running 1 ppm terminal.
- **Links:** [CCSDS 130.11-G-2](https://public.ccsds.org/Pubs/130x11g2.pdf), [ETSI TR 102 376-1 (DVB-S2)](https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf),
  [TR 102 376-2 (S2X VL-SNR)](https://www.etsi.org/deliver/etsi_TR/102300_102399/10237602/01.01.01_60/tr_10237602v010101p.pdf),
  [ViaSat US7653150](https://patents.google.com/patent/US7653150B2/en), [Bertolucci et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/),
  [gr-dvbs2rx](https://github.com/igorauad/gr-dvbs2rx). Full: `testing/results/lit_real_space.md`.

## 2026-11-15 12:00 — Academic state of the art: nobody publishes a blind search at our CFO range and SNR
- **Found:** no single-carrier paper 2015-2026 does a blind CFO search over |f| <= 0.03 at Es/N0 <= -3 dB with BLER, so
  nothing beats us at a comparable point. Closest: Noels-Steendam-Moeneclaey 2005 (1001 QPSK symbols, turbo R = 1/2,
  |f| <= 0.1): code-aided EM reaches the bound only above ~2 dB and needs 128-256 preamble symbols to start;
  Imad-Houcke-Ghogho 2010: the only blind code-aided search as wide as ours (LDPC syndrome cost), ~6x the MCRB at
  Es/N0 ~-0.5 dB, no BLER. Deep-learning CFO papers: none at -5 dB / 1024 symbols with BLER; O'Shea 2017 finds the
  4th-power FFT beats the CNN beyond 1024 samples.
- **For us:** our final CFO RMSE is 2.3-3.8x the MCRB but costs only ~0.04 dB, so BLER is unaffected; worth an
  RMSE-vs-MCRB plot. Suggested competitor: a Noels-style code-aided EM on our pilot layouts (expected: same BLER as our
  pilot receivers, so blind keeps its +0.2 / 0 / +0.5 dB).
- **Links:** [Noels 2005](https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972),
  [Imad 2010](https://link.springer.com/article/10.1155/2010/293572), [Barbieri-Colavolpe-Caire 2007](https://www.tlc.unipr.it/colavolpe/papers/j31.pdf),
  [O'Shea 2017](https://ar5iv.labs.arxiv.org/html/1707.06260). Full: `testing/results/lit_real_academic.md`.

## 2026-11-15 12:00 — Optics, cable, cellular: 400ZR coherent optics uses exactly our CFO range, at +19 dB
- **Found:** 400ZR (coherent optical) specifies a frequency-offset tolerance of +-1.8 GHz at 59.8 GBd = |f| 0.030, our
  range, but at Es/N0 ~19 dB on a continuous stream, with a pilot every 32 symbols (resolves only +-0.016, so coarse CFO
  is blind 4th-power). Li-Zhao-Chen 2014 (1024 QPSK samples, blind): the 4th-power family breaks down at Es/N0
  2.5-5.5 dB, which independently confirms our "4th power fails below 0 dB". DOCSIS, coherent PON, GSM, LTE PRACH,
  microwave modems: all use known symbols at small CFO or 10-25 dB more SNR — covered by our 128-preamble competitor.
- **Optional competitor:** a 400ZR-style layout (32 pilots, 1 per 32 symbols, 0.13 dB, blind coarse + pilot fine + lobe
  search); expected >= 1 dB worse than DVB-RCS2 at 1/10, 0.15.
- **Links:** [IEEE 802.3ct Zhang 2019](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf),
  [Li et al. 2014](https://lightweb.ie.cuhk.edu.hk/wp-content/uploads/publication/1658737499249-Least-squares_carrier_frequency_offset_estimation_for_coherent_optical_QPSK_receivers.pdf),
  [DOCSIS burst patent US8755462](https://patents.google.com/patent/US8755462). Full: `testing/results/lit_real_terrestrial.md`.

## 2026-11-15 12:00 — Satellite (LEO / GEO / IoT): every deployed system pre-compensates or uses known symbols; VDE-SAT is the closest
- **Found:** no deployed system searches the CFO blind with the decoder. 3GPP NTN pre-compensates Doppler to +-0.1 ppm
  (residual 0.013-0.053 of a subcarrier). Closest real standard to our SNRs: **VDE-SAT** (ITU-R M.2092-2): pi/4-QPSK,
  turbo 1/4-1/2, a 27-symbol syncword + 1 pilot per 27 symbols, thresholds Es/N0 -4.5 / -3.6 / -0.6 dB.
  A Viasat patent (US8243859) does what our blind receiver does with a unique word in place of the decoder: 4th-power
  FFT, keep the top 32 peaks, test each. OneWeb downlink uses a 4th-power FFT + PLL (our Stage 1) at ~10 dB.
- **Proposed competitors:** VDE-SAT layout scaled to 1024 symbols (66 known, 0.27 dB; expected 0.15-0.2 dB better than
  DVB-RCS2 but 0.3-0.4 dB behind blind at 2/5, 1/2), and a fairer top-N version of our 16+16 4th-power receiver.
  Also suggested: a CFO-ramp robustness point (0.01 drift over the burst) for narrowband-NTN comparability.
- **Not comparable:** Iridium, AIS, Argos, ORBCOMM (|f| 0.4-1.9: far larger CFO, non-coherent).
- **Links:** [ITU-R M.2092-2](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf),
  [Viasat US8243859](https://patents.google.com/patent/US8243859), [OneWeb, Komodromos-Humphreys 2025](https://www.nature.com/articles/s44459-025-00013-y),
  [3GPP TS 38.101-5](https://itecspec.com/3gpp/38.101-5/s/6.4.1). Full: `testing/results/lit_real_leo.md`.

## 2026-11-15 11:59 — Wi-Fi and short-range radios: no tougher competitor than the ones we already simulate
- **Found:** real single-carrier Wi-Fi / short-range systems work with a much smaller CFO or much more SNR per symbol.
  802.11ad (60 GHz single carrier): +-20 ppm = |f| <= 1.4e-3 cycles/chip, 22x smaller than our 0.03, a 3300-chip
  preamble, and its lowest mode needs ~+3.5 dB per chip. LoRa, BLE Coded, 802.15.4 reach +9...+16 dB per symbol through
  spreading, with non-coherent detection.
- **What they use:** repeated-preamble autocorrelation, coarse then fine (802.11ad lag 128, OFDM Wi-Fi lag 16 / 64,
  802.11b Barker-to-Barker); a BLE long-range patent uses a bank of FFT frequency hypotheses, like our CFO grid.
  Nobody checks more than the CRC: our re-encoding check has no equivalent.
- **Optional extra competitor:** a Wi-Fi-style 128-symbol preamble (8 x 16 coarse + 2 x 64 fine): expected 1.9x the CRB
  and a 1e-3...5e-3 BLER floor near -5 dB from fine-window misses, i.e. worse than our 128-preamble ML.
- **Links:** [802.11ad PHY](https://www.rfwireless-world.com/tutorials/wlan-802-11ad-physical-layer),
  [MathWorks 802.11ad SC PER](https://www.mathworks.com/help/wlan/ug/802-11ad-packet-error-rate-single-carrier-phy-simulation-with-tgay-channel.html),
  [Liu et al. TCSI 2015](https://doi.org/10.1109/TCSI.2014.2361035), [BLE LR patent US 2018/0270091](https://ipiq.io/patents/5237399),
  [LoRa sync, Xhonneux](https://arxiv.org/abs/1912.11344). Full: `testing/results/lit_real_wlan.md`.

## 2026-11-15 11:56 — Averaging over a few list paths finds the true CFO cell far more often (F3)
- **Found:** the checkpoint metric averaged over the best 2-8 list paths ranks the true CFO cell in the top 4 in
  99.9 % of packets at R = 0.15, -4 dB, against 97.4 % for today's single-path metric: 46 packets fixed, 0 broken out of
  1875 (p = 3e-14). Two paths already give 40 of the 46. No change at 0.15 -3 dB (already 100 %), 1/10 -5 dB 99.84 -> 100 %.
- **Source:** Yuan, Coskun & Kramer 2021 (list-marginalised SC metric), via the literature scout's survey (F3).
- **Why it matters:** these "true cell not found" cases are the main error source at the hardest point.
- **Next:** build it into the receiver for the last-checkpoint survivors (2 paths first), 64k paired BLER test.
  `testing/results/expected_f3f5.md`. My prediction was a near-zero gain: wrong.

## 2026-11-15 11:56 — Refinement study: decision-directed Newton beats the grid, 4th-power Newton and the PM parabola fail
- **Found (8k packets per point):** the CFO from a Newton step on the single-path codeword at the cell centre is 2-3x more
  accurate than the current refinement grid (0.25-0.42 vs 0.55-0.79 STEP rms at 1/10, 0.15) at about 1/4 of its MACs.
  4th-power Newton is worse than no refinement at the low rates; the path-metric parabola lacks its neighbour cells in
  59-96 % of cases.
- **Also:** 37 % of the failures at 0.15 -4 dB and 65 % at 2/5 0.5 dB had the true cell refined and still failed:
  refinement can fix more than expected.
- **Next:** online test, decision-directed refinement replacing the grid at 1/10, 0.15, grid as fallback.
  `testing/results/expected_ref.md`.
