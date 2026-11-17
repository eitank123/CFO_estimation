# Deployed preamble / pilot competitors: which to implement, and predictions vs blind (2026-11-15)

**Purpose.** Show that the blind receiver (0 known symbols) reaches the BLER of real preamble / pilot-based
single-carrier systems. Every competitor is simulated in the est4 framework: the 1024 data symbols carry the whole
codeword (N = 2048, CRC-16), the known symbols are EXTRA symbols in the burst, and their energy is charged on the SNR
axis (SNR = Es/N0 + 10 log10((1024 + Nk) / 1024)). Same CFO (|f| <= 0.03), noise, decoder (CA-SCL-8), re-encoding check
and fair metric-ordered CRC search (incl. alias / lobe hypotheses) for all. Sources: the surveys
`lit_real_space.md`, `lit_real_leo.md`, `lit_real_terrestrial.md`, `lit_real_wlan.md`, `lit_real_military.md`,
`lit_real_academic.md` (2026-11-15); real-system cards `lit_card_sat.md`, `lit_card_space.md`, `lit_card_terr.md` and
rates `lit_rates.md` (2026-11-15; corrections below, predictions unchanged). Test status: `expected_est5.md`.

## Is the comparison fair? (yes, under the assumptions below; this is what "fair" means here)
The question each comparison answers: **does blind keep the same BLER while sending no preamble / pilots?**
- **Same data, same code:** every receiver decodes the same 1024 data symbols carrying the same codeword (N = 2048,
  CRC-16, interleaver), with the same CA-SCL-8 decoder, the same re-encoding check (RHO_N) and the same fair CRC search
  (metric order, incl. alias / lobe hypotheses). Same CFO (uniform +-0.03), noise, phase noise, packets (paired seeds).
- **Pilots are OUTSIDE the packet:** the competitor sends 1024 + Nk symbols; its known symbols do not steal data space.
- **Pilot energy is charged:** the SNR axis is the burst energy per DATA symbol, Es/N0 + 10 log10((1024 + Nk) / 1024).
  So a competitor with 128 pilots is plotted 0.51 dB to the right: it paid that energy (and 12.5 % airtime) for its pilots.
- **Each competitor gets its own best estimator and search window** (its own CRB), not a crippled one.
- **What is NOT equal (reported, not hidden):** complexity — blind needs 2-12x the MACs per core; airtime — the
  competitors need 1024 + Nk symbols (1.6-30 % more), blind 1024.
- **Airtime in this file = Nk / 1024** (extra symbols relative to the 1024 data symbols: 128 known = 12.5 %, 116 =
  11.3 %); 08 §8.3 quotes the share of the burst, Nk / (1024 + Nk) (128 = 11.1 %, 116 = 10.2 %). Nk and dB checked
  against est4/common.py (Nk = len(known_idx), dB = 10 log10((1024 + Nk) / 1024)) on 2026-11-15: zr32 33 (0.14 dB),
  dmrs7 171 (0.67), dvbs2 126 (0.50), ccsds8 128 (0.51), vde27 66 (0.27); earlier text had 32 / 0.13, 0.69, 0.52, 0.52,
  ~65. The changes are <= 0.02 dB; the predictions below are unchanged.
- So "blind at the same plotted SNR has the same or lower BLER" = blind matches the system WITHOUT its preamble.

## Assumptions (state them with every plot)
- **Timing and burst detection are assumed known** for every receiver, blind included (out of scope for now, user
  2026-11-15). In a real system the preamble also does detection and timing, so this assumption favours blind: the
  comparison is CFO/phase + decoding only.
- **CFO uniform in +-0.03 cycles/symbol for everyone.** Several real systems are designed for a smaller range
  (DVB-S2 header acquisition, CCSDS, Wi-Fi fine stage); we widen them with their own lobe / alias CRC search rather
  than reject them. Static CFO (a drift test is planned, see the end).
- **Same FEC for all** (our polar N = 2048 + CRC-16, CA-SCL-8); real systems use turbo / LDPC / BCH.
- **Blind is NOT packet-paired with the est4 competitors** (different harness and seeds); est4 competitors are paired
  with each other. Differences below ~0.1 dB between blind and a competitor are inside this unpaired noise.
- **Complexity is modelled** (MACs per core, scheduled count), not measured on hardware.

## How the predictions are made
Required SNR at a target BLER ~= genie SNR (true CFO and phase, no pilots) + pilot energy E + estimation loss d.
Calibrated on our measured est4 results (8.2a): 128-preamble ML at 2/5: 0.64 + 0.51 = 1.15 predicted, 1.16 measured;
DVB-RCS2 ID 13 at 2/5: 0.64 + 0.47 = 1.11 vs 1.10; 128 ML at 1/10: -5.19 + 0.51 = -4.68 vs -4.68. d ~ 0 when the pilots
resolve the CFO; d > 0 when alias / window misses or a weak coarse stage remain (DVB-RCS2 at 1/10: d = 0.63).

## Measured reference SNRs (est4, 8.2a; the only numbers for plots)
Every est5 competitor and faithful variant, measured: [scoreboard.md](scoreboard.md) (2026-11-17).
Required SNR [dB], lower is better:
| | 1/10 @ 1e-4 | 0.15 @ 1e-3 | 0.15 @ 1e-4 | 2/5 @ 1e-3 | 1/2 @ 1e-3 |
|---|---|---|---|---|---|
| **Blind (0 known symbols; adopted testing receiver, updated 2026-11-17)** | **-4.78** | **-3.60** | **-2.93** | **0.58** | **1.73** |
| Genie (lower bound, no pilots) | -5.19 | -3.91 | -3.59 | 0.64 | 1.90 |
| DVB-RCS2 ID 13 (measured) | -4.09 | -3.45 | -3.12 | 1.10 | 2.33 |
| 128 preamble ML (measured) | -4.68 | -3.44 | -3.12 | 1.16 | 2.41 |
| 64 + 64 joint ML (measured) | -2.87 | -3.34 | -2.71 | 1.12 | 2.38 |
| 16 + 16 4th power (measured) | fails | fails | fails | fails | 2.77 |
(Blind beats its own genie at 2/5, 1/2 because its retries and joint list add decoding attempts.)

## Predicted: worth implementing (est5; PLANNING ONLY, not measured, never plot these numbers)
The "Predicted SNR" column is genie + pilot energy + an estimated loss (method above). It decides what to run, not
what we claim. "-inspired" = an adaptation of the system's known-symbol layout and estimator to our 1024-symbol burst,
not a standard-compliant implementation (deviations in the next table).

| # | Competitor | Real system using it | Link | Known symbols (E) | Estimator chain | Predicted SNR: 1/10 @1e-4 / 0.15 @1e-3 / 2/5 @1e-3 / 1/2 @1e-3 | vs blind | Why include |
|---|---|---|---|---|---|---|---|---|
| C6 | **VDE-SAT** | VHF Data Exchange via satellite (maritime, ITU-R M.2092-2) | [ITU-R M.2092-2](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf) | 27-symbol syncword + 1 pilot / 27 symbols, 66 (0.27 dB; format confirmed against M.2092-2) | ML on syncword, Rife-Boorstyn on all known symbols, CRC search over +-1/27 alias lobes (alias peak ~0.59 of the true one) | -4.85 ... -4.6 / -3.6 ... -3.4 / 0.9 ... 1.0 / 2.15 ... 2.25 | tie at 1/10, 0.15; blind 0.3-0.4 dB better at 2/5, 1/2 | the real standard closest to our SNRs; this 27 / 27 layout is designed for Es/N0 -2.4 dB (SAT-MCS-1.50-1) and -0.6 dB (the -4.5 dB VDE-SAT format is a different BPSK/CDMA layout: 48-symbol syncwords, a pilot every 8) |
| C7 | **DVB-S2-inspired** | DVB-S2 / S2X broadcast and VSAT (PL header + pilot blocks) | [ETSI TR 102 376-1](https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf) | 90-symbol header + one 36-symbol pilot block, 126 (0.50 dB) | M&M on the header, then joint ML header + block with lobe search | -4.65 ... -4.5 / -3.4 ... -3.3 / 1.15 ... 1.2 / 2.4 ... 2.5 | blind better by 0.25 / 0.2 / 0.55 / 0.65 dB | the most widely deployed satellite standard (forward link) |
| C8 | **CCSDS-inspired** | NASA / ESA telemetry (CCSDS 131.2 SCCC: frame marker + 16-symbol pilot fields) | [CCSDS 130.11-G-2](https://public.ccsds.org/Pubs/130x11g2.pdf) | 8 blocks x 16, 128 (0.51 dB) | Rife-Boorstyn over all blocks + lobe search (block period 162.3: aliases every 1/162.3 = 0.0062), per-block phase + interpolation | -4.65 ... -4.3 / -3.4 ... -3.2 / 1.15 ... 1.25 / 2.4 ... 2.5 | blind better by 0.25-0.6 dB everywhere | space-agency practice; tests distributed short blocks with dense aliases |
| C9 | **ViaSat burst** | ViaSat return-link burst demodulators (a merge of two patents: US 7653150 burst + single peak, US 8243859 top-N + UW joint metric) | [US 7653150](https://patents.google.com/patent/US7653150B2/en), [US 8243859](https://patents.google.com/patent/US8243859) | 16-symbol midamble unique word (0.07 dB) | 4th-power FFT over the burst, top-32 peaks each tested on the UW (pi/2 ambiguity), phase from the 16 UW symbols (the patent: from the 4th-power bins), CRC search | fails / fails / 1.5 ... 2.5 / 2.2 ... 2.8 | blind far better (it works where 4th power fails) | the industry version of our own fast path; shows what "almost no pilots" costs without a decoder search |
| C10 | **DMRS 1/7** | LTE / NB-IoT uplink (NPUSCH: 1 reference symbol per 7) | [3GPP NB-IoT primer, arXiv 1606.04171](https://arxiv.org/pdf/1606.04171) | 1 pilot / 7 symbols, 171 (0.67 dB) | Rife-Boorstyn over the pilots (range +-0.071, no aliases), pilot phase + interpolation / Kalman | -4.5 / -3.2 / 1.33 / 2.6 | blind better by 0.4-0.8 dB in AWGN; likely the best competitor under phase noise | dense-pilot cellular practice; the phase-noise reference |
| C11 | **Sparse periodic pilots (1/32)** | Generic sparse-pilot layout; 400ZR coherent optics (pilot every 32 symbols, CFO tolerance +-1.8 GHz at 59.8 GBd = our 0.03) cited only as evidence that +-0.03 is a real requirement | [IEEE 802.3ct, Zhang 2019](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf) | 1 pilot / 32 symbols, 33 (0.14 dB) | 4th-power coarse, Rife-Boorstyn on the pilots, CRC search over +-1/32 alias lobes | -4.4 ... -3.9 / -3.5 ... -3.0 / 0.8 ... 1.0 / 2.05 ... 2.2 | the closest competitor at 2/5, 1/2 (lowest overhead); blind still 0.2-0.4 dB better | the lowest-overhead pilot layout; +-0.03 is a real (optical) requirement |
| C12 | **Wi-Fi-inspired** | IEEE 802.11 legacy L-STF / L-LTF coarse/fine preamble estimation | [MathWorks wlanCoarseCFOEstimate](https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html) | 128-symbol preamble: 8 x 16 repeats (0.51 dB) | lag-16 autocorrelation coarse, lag-64 fine, CRC search over the +-4 fine lobes (1/64) | -4.6 ... -4.3 / -3.4 ... -3.2 / 1.2 ... 1.3 / 2.45 ... 2.55 | blind better by 0.3-0.7 dB | the estimator every Wi-Fi chip runs (simpler than ML) |
| C13 | **MIL-110-inspired HF** | Tactical HF modems, MIL-STD-188-110C App C (superseded by 110D, 2017; requirement +-75 Hz at 2400 Bd = 0.031, our range) | [MIL-STD-188-110C](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf) | preamble + known probe blocks scaled, ~308 (1.14 dB) | ML / R-B over all known symbols, per-probe phase + interpolation | -4.05 / -2.8 / 1.8 / 3.0 | blind better by 0.85-1.2 dB | heavy-pilot military practice for our exact CFO range |
| C14 | **hyb3 (patent-inspired)** | Advantech satellite modems (patents; designed for +-3 % of Rs) | [US 7590199](https://patents.google.com/patent/US7590199), [US 7593490](https://patents.google.com/patent/US7593490) | 16 + 16 (0.13 dB; the patent: a 48-symbol preamble) | sum of pilot and 4th-power log spectra, 3 CFO candidates decided by CRC + rho (the patent: mean \|LLR\| after 1-3 partial turbo iterations) | fails / fails / 1.2 ... 2.0 / 2.2 ... 2.6 | blind better by >= 0.6 dB | a deployed "few pilots + decoder picks among candidates" hybrid |
| C15 | **Griebel / ARS 2021 variants** | DVB-RCS2 return-link burst demodulators (FPGA; EN 301 545-2 current V1.5.1, 2026, ID 13 unchanged) | [Griebel & Wasenmüller, Adv. Radio Sci. 19, 59 (2021)](https://ars.copernicus.org/articles/19/59/2021/) | DVB-RCS2 ID 13, 116 (0.47 dB) | the paper's chain: zero-filled r c*, FFT 2048 / 4096, 3-bin parabolic interpolation, phase from the peak; plus "RCS2-13 lobes" (+-1/20 alias search, ours) | G4096: = RCS2-13; G2048: +0.03 ... +0.2 dB; faithful one-decode chain: +0.1 ... +0.5 dB; RCS2-13 lobes at 1/10: -4.7 ... -4.55 | lobes variant closes the 1/10 gap to 0.2-0.35 dB; blind's lead at 0.15, 2/5, 1/2 unchanged | the user's article; the real implementation trade-off (FFT size vs loss) of the DVB-RCS2 estimator (`expected_ars.md`, `lit_ars2021.md`) |

## Deviations from the real systems (what "-inspired" changes)
Common to all: one burst of 1024 data symbols + Nk known symbols outside it, QPSK data, our polar code and CRC search,
timing known, +-0.03 CFO window.

| # | Real system | What we keep | What we change |
|---|---|---|---|
| C6 | VDE-SAT (ITU-R M.2092-2, A5-2.10) | the exact known-symbol pattern: 27-symbol syncword, first pilot 14 after it, then 1 pilot / 27 (66 known in our 1090-symbol window); ML + R-B, the same family as the published VDES estimator (IEEE 8780774) | one 1090-symbol window of a 80371-symbol burst; turbo code -> polar; LEO Doppler up to ~0.12 cycles/symbol -> our +-0.03; no link ID (none on the downlink, M.2092-2 Table 10); used down to -5 dB, 1-2.6 dB below this layout's -2.4 dB design point at 1/10 and 0.15 (`lit_vdesat_format.md`, `lit_card_space.md`) |
| C7 | DVB-S2 / S2X (forward link) | 90-symbol PL header + one 36-symbol pilot block | real: pilot block every 16 slots in a long continuous frame, pi/2-BPSK header, multi-frame loops; we give one burst and one block. A real 1024-symbol window after the PLHEADER holds NO pilot block (the first comes 1440 data symbols after it), and in ACM only the 26-symbol SOF is known before PLS decoding (we treat all 90 as known): ours is stronger than the standard (`lit_card_sat.md` 2) |
| C8 | CCSDS 131.2 SCCC | distributed 16-symbol pilot fields | field spacing scaled to our burst (8 blocks). Real 131.2 has 16 pilots per 540 data symbols, about 30 known per 1024 data (0.13 dB, aliases 1/556): ours has 3.7x the density (128, 0.51 dB, aliases 1/162.3). The real acquisition range is smaller than ours only in the 130.11-G-2 100 MBaud case (0.01-0.02; ~0.2 at 5 Mbaud, Bertolucci 2021), and it is acquired by a multi-frame FLL; we add a +-5 lobe search (`lit_card_space.md` 3) |
| C9 | ViaSat US 7653150 + US 8243859 | 4th-power FFT, 16-symbol midamble UW, UW + peak joint metric | merges the two patents (US 7653150: single peak, UW only for the pi/2 ambiguity and timing; top-32 + joint metric is US 8243859); phase from the 16 UW symbols instead of the 4th-power bins (std 0.31 / 0.18 / 0.14 rad at -5 / 0 / +2 dB): weaker than the real chain at 2/5, 1/2; CRC search and genie timing added (`lit_card_sat.md` 3) |
| C10 | LTE / NB-IoT NPUSCH | 1 reference symbol per 7 (0.67 dB) | single-tone NPUSCH format 1 is structurally exact (1 DMRS per 7 single-carrier symbols); multi-tone NPUSCH / LTE PUSCH DMRS blocks are not modelled. Our window +-0.071 (the full DMRS range) is wider than the deployed one (+-250 Hz = 0.018 at 15 kHz, Chakrapani 2019): a stronger-than-deployed upper bound (`lit_card_terr.md` 1) |
| C11 | (generic sparse pilots) | 1 pilot / 32 symbols (33 pilots, 0.14 dB), alias search | not 400ZR: 400ZR is dual-pol 16QAM optics with continuous carrier recovery; its coarse CFO uses training sequences (Wang 2025; not verified against the OIF IA), ours is blind 4th power (`lit_card_terr.md` 4) |
| C12 | IEEE 802.11 (legacy L-STF / L-LTF) | repeated short block, lag-16 coarse + lag-64 fine autocorrelation | OFDM STF/LTF mapped to a single-carrier 8 x 16 repeated block; real Wi-Fi spends 320 known samples (L-STF 160 + L-LTF 160, 1.18 dB if charged), ours 128 (0.51 dB); CRC search over +-4 fine lobes (1/64), not +-1. 802.11ad SC (Golay STF, lag 128, [Liu et al. TCSI 2015](https://doi.org/10.1109/TCSI.2014.2361035)) is a different structure and is not modelled (`lit_card_terr.md` 2) |
| C13 | MIL-STD-188-110C App C (superseded by 110D, 2017) | preamble + known probe blocks, per-probe phase | probe/data pattern scaled to 1024 symbols (~308 known); real modem has adaptive equaliser and interleaver frames. Real App C carries 287 + 4 x 31 = 411 known per 1024 data (1.47 dB); our 308 drops the 103-symbol rate / interleaver section, so it is about 0.33 dB more favourable (`lit_card_terr.md` 3) |
| C14 | Advantech patents US 7590199 + US 7593490 | pilot + 4th-power spectra, decoder picks among 3 candidates | the real layout is a 48-symbol contiguous preamble + 440 payload (US 7590199); we use 16 + 16 pre / post (a fringe-comb DA spectrum without the gating lobe). The real candidate selector is mean \|LLR\| after partial turbo decoding (US 7593490); ours, CRC + rho, is stronger (`lit_card_sat.md` 4) |
| C15 | DVB-RCS2 ID 13 (Griebel 2021; EN 301 545-2 V1.5.1 current, ID 13 unchanged) | the paper's FFT + interpolation chain | the paper's FPGA fixed-point word lengths not modelled |

## Real-system fidelity (our competitor vs the deployed system, 2026-11-15)
From `lit_card_sat.md`, `lit_card_space.md`, `lit_card_terr.md` (and `comparison_full.md` section A, "Real system").
"Stronger" = our version is easier on itself than the real system would be (so blind's lead over it is conservative).

| Competitor | vs the real system | Why |
|---|---|---|
| C1 DVB-RCS2 ID 13 (RCS2-13, track) | stronger | CRC-checked search, 8192-point FFT, exact LS phase, genie timing; the Kalman tracker is ours (no RCS2 source tracks phase); real chain 0.1-0.5 dB worse (bench 0.5-0.6 dB all-in) |
| C2 16 + 16, 4th power (RCS2 pre/post) | mixed | CRC lobe search stronger than the real NDA chain, but RCS2 uses pilotless bursts only above ~3.4 dB (QPSK NDA from 3.9 dB): we run it outside its design region |
| C3 / C4 pre128, split64 | not rated | generic layouts (TR 101 545-4 preamble-only assumption, Ying & Ghogho placement), no single real system |
| C6 VDE-SAT | mixed | faithful layout and estimator family; smaller CFO range (0.03 vs 0.124) and CRC lobe search help; one syncword (vs tracking 35) and +0.06 dB energy hurt; run 1-2.6 dB below its design SNR at 1/10, 0.15 |
| C7 DVB-S2-inspired | stronger | a pilot block the real 1024-symbol window does not contain, all 90 header symbols known (CCM; ACM: 26), genie timing |
| C8 CCSDS-inspired | mixed | 3.7x the real pilot density and 3.4x wider alias spacing (stronger estimation), 0.51 vs ~0.13 dB energy (weaker); the real FLL tracks over frames |
| C9 ViaSat burst | mixed (weaker at 2/5, 1/2) | merges two patents, adds a CRC search and genie timing; phase from 16 UW symbols instead of the 4th-power bins (0.31 / 0.18 / 0.14 rad at -5 / 0 / +2 dB) |
| C10 DMRS 1/7 | stronger | structurally exact single-tone NPUSCH comb, but a +-0.071 window vs the deployed +-0.018 and all 171 pilots coherent: an upper bound |
| C11 sparse pilots 1/32 | mixed | one burst and no training sequence vs continuous averaging (weaker); decoder-checked lobe search (stronger) |
| C12 Wi-Fi-inspired | mixed | 128 vs 320 known samples and no pilot-subcarrier tracking (weaker); 0.51 vs 1.18 dB energy and a +-4 lobe CRC search (stronger) |
| C13 MIL-110-inspired | stronger | 308 vs 411 known (~0.33 dB less energy), all-symbol R-B + CRC lobe search at SNRs the real modem does not specify; AWGN only |
| C14 hyb3 | mixed | CRC + rho stronger than mean \|LLR\|; 16 + 16 weaker than the patent's 48-symbol preamble (no gating lobe), constant phase vs decision-aided tracking |
| C15 Griebel / ARS variants | stronger (faithful chain: mixed) | as C1; "Griebel faithful" keeps the paper's one-decode chain but gets genie timing and twice the paper's CFO range |

## Pros and cons of each competitor (as a system, vs blind)
| Competitor | Pros (why a real system chose it) | Cons (vs blind, at our setting) |
|---|---|---|
| DVB-RCS2 ID 13 (C1, measured; EN 301 545-2 V1.5.1 current, ID 13 unchanged) | cheapest pilot receiver (0.034-0.045 M per core); pilots spread over the burst -> excellent CFO accuracy and phase tracking under phase noise (the Kalman tracker is ours, not from an RCS2 source) | 116 known symbols = +0.47 dB and 11 % airtime; 1-symbol pilots every 20 alias at 1/20 -> 0.63 dB loss at 1/10 -5 dB; tied or 0.15-0.5 dB behind blind |
| 128 preamble ML / M&M (C3, measured) | simplest structure (one block, standard estimators); detection and sync in one place | +0.51 dB; constant phase only (collapses under phase noise: x9-140 at 1e-4); wrong-CRC floor 2-6 per 480k |
| 64 + 64 joint ML (C4, measured) | 2x longer baseline than a preamble -> 4x lower CRB | lobe ambiguity 1/1088: wrong lobe in 55-60 % below -4 dB, worst at 1/10 (-2.87 dB) |
| 16 + 16, 4th power (C2, measured) | tiny overhead (0.13 dB) | 4th power fails below ~0 dB: BLER 0.5-0.9 at 1/10, 0.15, 2/5 |
| C6 VDE-SAT | designed near our SNRs (this layout: Es/N0 -2.4 and -0.6 dB; -4.5 dB is a different BPSK/CDMA format); low overhead (0.27 dB); syncword + pilots = both acquisition and tracking | alias lobes at 1/27 need a CRC search; turbo-coded in reality (we give it our polar code) |
| C7 DVB-S2-inspired | the most deployed satellite standard (forward link); header doubles as signalling | 0.50 dB; header-only M&M is weak at -5 dB; built for continuous streams (we give it one burst) |
| C8 CCSDS-inspired | space-agency practice; distributed blocks give phase tracking | 0.51 dB; dense aliases (every ~0.006) need +-5 lobe hypotheses -> more decodes, alias errors at -5 dB |
| C9 ViaSat burst | almost no overhead (0.07 dB); designed for 10 % of Rs (a patent design statement; no product spec found) | the 4th power fails below ~0 dB (works only at 2/5, 1/2 high SNR) |
| C10 DMRS 1/7 | no aliases inside +-0.03; best phase tracking (dense pilots) | highest overhead after MIL (0.67 dB, 17 % airtime) |
| C11 sparse pilots 1/32 | very low overhead (0.14 dB); +-0.03 is a real 400ZR requirement | only 33 pilots: weak coarse stage at low SNR (needs 4th power + alias search) |
| C12 Wi-Fi-inspired | the cheapest estimator (autocorrelation, < 1k MACs) | coarser than ML (~1.9x CRB); fine-lobe misses -> floor near -5 dB |
| C13 MIL-110-inspired | built for our CFO range with heavy pilots; very robust | 1.14 dB and 30 % airtime: the most expensive in energy |
| C14 hyb3 | few pilots (0.13 dB) + decoder picks among 3 candidates (closest in spirit to blind) | still relies on the 4th power: fails at 1/10, 0.15 |
| Blind (ours) | 0 known symbols: no energy or airtime overhead; matches or beats every pilot receiver in BLER; no wrong-CRC floor | 2-12x the MACs per core; needs the decoder in the loop; phase noise needs code-aided tracking (pns, partial gain) |

MACs per core (predicted): every pilot competitor 0.03-0.13 M (DVB-RCS2 0.034-0.045, preamble ML 0.05-0.12 measured);
the ones with a 4th-power FFT (C9, C11, C14) +~0.01 M; lobe / alias searches add decodes at low SNR. Blind 0.08-0.41 M.
So the expected picture: equal or better BLER for blind with 0 known symbols, at 2-12x the MACs per core.

## Not worth implementing (with the reason)
| Algorithm / system | Link | Why not |
|---|---|---|
| Code-aided EM sync (Noels-Steendam-Moeneclaey 2005) on a pilot layout | [EURASIP 2005](https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972) | improves the CFO RMSE, not the BLER: our pilot receivers already sit at genie + pilot energy; needs 128-256 pilots and >= 2 dB to start |
| Blind syndrome-cost CFO search (Imad-Houcke-Ghogho 2010) | [EURASIP 2010](https://link.springer.com/article/10.1155/2010/293572) | not a preamble system; equals our frozen-bit ranking, which we tested and found equal to our metric (dead end) |
| DVB-S2X very-low-SNR unique word | [TR 102 376-2](https://www.etsi.org/deliver/etsi_TR/102300_102399/10237602/01.01.01_60/tr_10237602v010101p.pdf) | 900 known symbols (88 % overhead) and limited to CFO <= 1 % of Rs |
| Multi-frame FLL / PLL (DVB-S2 continuous mode, CCSDS FLL, NASA DSN) | TR 102 376-1, CCSDS 130.11-G | needs many frames; we receive one burst |
| Luise-Reggiannini, Fitz, Kay, D&M estimators | [Bertolucci et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/) | dominated by ML / M&M on the same known symbols (already simulated); Kay biased below ~8 dB |
| GSM 26-symbol midamble | [US7570719](https://patents.google.com/patent/US7570719) | one-shot estimate too poor at -5 dB (CRB 5e-3 = ~17 rad drift over the burst) |
| DOCSIS / PON preambles | [US8755462](https://patents.google.com/patent/US8755462), [arXiv 2409.14400](https://www.arxiv.org/pdf/2409.14400) | same class as our 128-preamble ML/M&M (already simulated) |
| LoRa, BLE, 802.15.4, Sigfox, Iridium, AIS, Argos, ORBCOMM | lit_real_wlan.md, lit_real_leo.md | not coherent PSK (CSS / GFSK / DSSS) or CFO 0.4-40 cycles/symbol |
| Starlink, 5G NR, Wi-Fi OFDM | lit_real_leo.md, lit_real_wlan.md | OFDM, not single carrier |

## Also recommended (not a competitor): robustness points
- A linear CFO ramp over the burst (e.g. 0.01 total drift; HF 3.5 Hz/s, narrowband NTN Doppler rate) at 2/5 0.5 dB and
  0.15 -3.5 dB, blind vs the best competitors: our simulations assume a static CFO.
- Phase noise (1e-4) for C6, C8, C10 with Kalman tracking next to DVB-RCS2 track and blind + pns.
