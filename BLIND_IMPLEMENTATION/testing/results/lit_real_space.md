# Real, deployed and official single-carrier CFO / phase synchronization: CCSDS, ESA / NASA, DVB-S2 / S2X / RCS, vendors

Literature scout report, 2026-11-15 (revised the same day: comparability ranking added as section 0). No simulations
were run. Scope: single-carrier (PSK / APSK, burst or continuous) frequency and phase acquisition in official standards,
their implementation guidelines, space-agency receivers, open reference implementations and vendor products. OFDM is out
of scope (one line of context: 5G NR NTN and LTE-M / NB-IoT NTN pre-compensate Doppler from GNSS and use reference
signals, see `lit_blind_cfo.md` #29; not pilot-free).

Goal of the comparison (user, 2026-11-15): find receivers that do the SAME task (single-carrier coded burst, CFO
acquisition near |f| <= 0.03, low SNR) to simulate side by side as competitors; they may perform worse than ours.

Read before this survey and not repeated here: `lit_blind_cfo.md` (DVB-RCS2 deployment, Griebel 2021),
`lit_dvbrcs2.md` (EN 301 545-2 Table A-1, TR 101 545-4: CFO 0.5-3 % of Rs, Ku 1590 Hz / Ka 3784 Hz budget,
Barbieri-Colavolpe 2007, ESA pilot-phase patent), `lit_polar_sync.md`, and `expected_est4.md` (the pilot competitors
C1a / C1b / C2 / C3 / C4 already built and measured).

Conventions. f = df / Rs in cycles per symbol (our range |f| <= 0.03). SNR = Es/N0 per QPSK symbol where possible.
**[derived]** = my arithmetic from the cited numbers, not a number from the source. Reading depth per source is given in
the table; ETSI / CCSDS / ECSS PDFs were read through a public PDF-to-text reader (r.jina.ai, given only the public URL),
so tables and figures came out as flat text or not at all (figure values are never quoted).

---

## 0. Comparability ranking and what to implement

Criterion: same task = single-carrier coded QPSK burst, one packet, CFO acquisition near |f| <= 0.03, low Es/N0.
Measured est4 anchors (from `expected_est4.md`; plotted SNR with pilot energy charged; SNR in dB where BLER crosses the
target; order blind / RCS2-13 / pre128 ML / split64 ML / pre-post 4th power):
1/10 @1e-4: -4.9 / -4.09 / -4.68 / -2.87 / fails; 0.15 @1e-3: -3.60 / -3.45 / -3.44 / -3.34 / fails;
2/5 @1e-3: 0.61 / 1.10 / 1.16 / 1.12 / fails; 1/2 @1e-3: 1.79 / 2.33 / 2.41 / 2.38 / 2.77.
All "expected" numbers for NEW competitors are my predictions from these anchors and the CRB, not measurements.

| Rank | Source family | Why comparable / not | Status | What we would implement (known symbols, overhead, chain) | Expected at our points |
|---|---|---|---|---|---|
| 1 | **DVB-RCS2 TC-LM** (EN 301 545-2, TR 101 545-4; `lit_dvbrcs2.md`) | GEO MF-TDMA coded bursts; guideline CFO 0.5-3 % of Rs (0.03 = its top corner); QPSK down to ~-0.8 dB | **already implemented** (est4 C1a / C1b / C2 / C3) | - | measured (anchors above) |
| 2 | **ViaSat US 7653150** (GEO return-link burst receiver) | one coded QPSK burst, CFO up to 10 % (covers 0.03), NDA, almost pilot-free; but designed for Es/N0 ~2.6 dB [derived] | **new variant of C2** (cheap: known-symbol layout change only) | **V1 "ViaSat-UW"**: 1024 data + one 16-symbol QPSK unique word in the middle (e.g. symbols 504-519), K = 16, **0.07 dB** [derived]. Chain: 4th power of all 1040 symbols (amplitude kept, as in the patent), zero-pad to 4096, FFT, peak + 2-neighbour interpolation, f = k / (4 N); phase = arg(peak) / 4; pi/2 ambiguity by correlating the de-rotated UW with its 4 rotations (timing is known in our chain, so the patent's ±8-symbol search is dropped); constant phase; then CA-SCL-8 + CRC-16 + rho as in every est4 receiver | like C2 (pre/post 4th power, 0.13 dB): fails (BLER 0.5-0.9) at all 1/10 and 0.15 points and at 2/5, because of the 4th-power threshold, not the UW; 1/2 @1e-3 ~2.7 dB (C2 2.77 dB, 0.06 dB less overhead) [rough]. UW rotation-error probability [derived, 16 symbols, nearest-neighbour bound]: ~2.4e-2 at -5 dB, ~2.4e-5 at 0.5 dB, < 1e-6 at 2 dB. Value: names C2 as the deployed industry baseline |
| 3 | **CCSDS 131.2 SCCC reference receiver** (CCSDS 130.11-G-2; Bertolucci 2021) | low SNR (lowest mode Es/N0 -0.58 dB), CFO 0.01 (100 MBaud) to 0.3 (5 Mbaud); but the standard runs a frame-level FLL over 133 760-symbol frames, so only its single-shot core is comparable | **new (C5)**, optional | **C5 "CCSDS block pilots"**, K = 128 = **0.51 dB**: C5a 8 blocks x 16 symbols (one at each end, 6 evenly spaced, 146 data symbols between), or C5b (closer to CCSDS: frame-marker-like 64-symbol preamble + 4 x 16-symbol pilot blocks spread over the data). Chain: DA FFT over all known symbols (zeros at data), 4096 points, Newton / parabolic interpolation (CCSDS 130.11 5.7), full ±0.03 search + the est4 code-aided window; phase: per-block ML over 16 symbols + unwrap + linear interpolation (CCSDS 130.11 5.6) | AWGN: within the RCS2-13 / split64 range at 0.15, 2/5, 1/2 (frequency CRB set by the spread: std ~3-4e-5 at -5 dB [derived]). At 1/10 -5 dB a **risk of lobe errors like split64 (-2.87 dB)**: block period 162 -> aliases every 0.0062 (C5a), 272 -> 0.0037 (C5b); a 64-symbol preamble alone has std 1.4e-3 at -5 dB, 0.37 of the C5b alias spacing [derived]. Phase noise: per-block phase std 0.31 rad at -5 dB, 0.21 rad at -2 dB [derived]; 8 or 5 anchors, so between split64-interp and RCS2-13 track (e.g. 0.15 -3.5 dB, 1e-4: between 4044 and 94 errors per 64k) [rough] |
| 4 | **DVB-S2X VL-SNR burst mode** (TR 102 376-2 B.3-B.4) | the only official very-low-SNR burst detector (Es/N0 ~-10 dB); but designed for CFO <= 1 % and 900 known symbols | new, low priority | **V3 "VL-SNR-scaled"**, 0.51 dB: 128-symbol UW as 8 segments x 16 symbols; frequency-bin step search (B.4) with segment-coherent, cross-segment non-coherent energy sum_s \|sum_seg r c*\|^2 per bin (bin width ~1/(4 x 16) cycles/symbol), then ML refinement on all 128 symbols; constant phase | a 16-symbol segment rotates 0.48 cycles at f = 0.03 (coherent loss ~3.6 dB without the bin grid [derived]); with the grid, frequency accuracy at best equal to C3's. Expected equal to or slightly worse than pre128 ML. Value: "the official lowest-SNR burst detector, scaled", nothing more |
| 5 | **DVB-S2 PLHEADER + M&M** (gr-dvbs2rx; TR 102 376-1) | single-shot core of the DVB-S2 coarse estimator; the standard runs it in continuous mode | new, low priority | **V4 "S2-header"**: 90 known symbols as a preamble (0.37 dB), M&M (lags 1..89, gr-dvbs2rx weights), constant phase, est4 window search | = est4 `pre128 M&M` with 90 symbols: CRB std 1.7x larger [derived]; expect BLER at or above pre128 M&M (207 errors per 64k at 1/10 -5 dB vs 4 for pre128 ML) |
| 6 | Vendor burst modems (ComBlock COM-1802: ±20 % Rs, 50 + 32-symbol preamble, FFT acquisition) | burst, large CFO, but no low-SNR numbers | covered by C3 | - | - |
| - | Not comparable | DSN / ECSS / NASA relay (continuous PLLs, Doppler predicts or transmitter pre-compensation); deep-space residual carrier (a pilot tone); DVB-S2 / CCSDS multi-frame FLLs (1e5-1e7 symbols); Proximity-1 (idle acquisition sequence); CCSDS 130.1 (assumes sync) | - | - | - |

Recommended side-by-side set: keep est4 (rank 1); add **V1 ViaSat-UW** (rank 2: trivial, names the industry blind-burst
baseline) and **C5b** (rank 3: the space-agency layout). V3 / V4 only if the main session wants the full standards list;
their expected curves are dominated by C3. Test plan for new ones: est4 harness, same seeds, 1/10 -5 ... -3 dB,
0.15 -4 ... -2 dB, 2/5 0 ... 1.5 dB, 1/2 1.5 ... 3 dB, AWGN 480k per point as est4, plus pn 1e-4 at the three pn points.

---

## 1. Ranked takeaways for the comparison

1. **No official single-carrier system acquires a 3 % CFO in one short burst at Es/N0 <= -2 dB without help.**
   Every standard either (a) keeps the per-burst CFO far below 0.03 by locking the terminal to a network clock
   (DVB-RCS / RCS2: terminal carrier better than 1e-8 RMS, EN 301 790 cl. 6.1.2), or (b) acquires the large offset
   over many frames with a loop (DVB-S2: pilot FLL from ±5 MHz = 0.2 Rs to 4e-3 in ~100 ms, TR 102 376-1 C.4;
   DVB-S2X VL-SNR: quadricorrelator from ~3 % needs "several hundred thousand symbols" at -9.6 dB, TR 102 376-2 B.3;
   CCSDS 131.2 SCCC: frame-level FLL on a 256-symbol frame marker, CCSDS 130.11-G-2 5.7), or (c) uses a large
   known header at high SNR (vendor burst modems: ±20 % Rs with a 50 + 32-symbol preamble, ComBlock COM-1802; no
   threshold SNR given). The one deployed single-burst blind scheme found (ViaSat patent US 7653150: ±10 % Rs,
   512-symbol QPSK burst, 4th-power FFT, 16-symbol midamble UW for the pi/2 ambiguity, 0.2 dB loss) works at about
   Es/N0 2.6 dB [derived]. **Our receiver's operating region (|f| <= 0.03 in ONE 1024-symbol burst at -5 ... +3 dB,
   no pilots) is outside every standard's design envelope**; state this, it is not a weakness.
2. **The closest official burst-mode design is DVB-S2X VL-SNR burst reception**: 900-symbol unique word (16 segments x
   56 symbols, Walsh-Hadamard polarity), segment-coherent combining, reliable frame detection at Es/N0 near -10 dB but
   only for **frequency uncertainty within 1 % of Rs** (TR 102 376-2 B.3). Above 1 % they prescribe a quadricorrelator
   loop first, or a step search over frequency bins dwelling several frames (B.4). At our 3 % a 56-symbol segment
   spans 1.68 cycles [derived], so segment-coherent combining collapses; this is why the standard stops at 1 %.
   Known-symbol cost: 900 symbols per frame (88 % of our 1024 [derived]).
3. **What deployed estimators are, in one line each** (all data-aided except the ViaSat burst and the DVB-S2 NDA PLL):
   DVB-S2 guideline: pilot-only FLL (coarse) + Luise-Reggiannini on the 36-symbol pilot blocks (fine, L = 1000
   blocks, N = 18), RMS 6e-5 at -2 dB, 5.2e-5 at 1 dB; phase: per-pilot-block ML + linear interpolation, cycle-slip
   bound 1/(2 x 1476) = 3.4e-4. gr-dvbs2rx (open): Mengali-Morelli-type autocorrelation-phase-difference estimator
   on the 90-symbol PLHEADER, averaged over frames (range ±0.5), fine range 3.39e-4. CCSDS 131.2 SCCC: 1024-point
   FFT of the 256-symbol frame marker + Newton interpolation inside an FLL; phase: 16-symbol pilot fields every 540
   data symbols (about 3 % overhead), linear interpolation, sync loss 0.2-0.4 dB at CER 1e-4. Bertolucci et al.
   2021 (CCSDS 131.2 hardware): M&M chosen, 705 Hz RMS at 5 Mbaud, Es/N0 -2 dB = 1.41e-4 cycles/symbol, about
   1.2x the DA CRB std of a 256-symbol block [derived]. **All of these are in the families est4 already
   covers** (R&B / ML FFT = C3 / C4, M&M = C3 M&M, pilot blocks + interpolation = C1b, 4th-power + UW = C2).
4. **GEO burst return links.** NCR-locked DVB-RCS / RCS2 terminals: terminal error 1e-8 RMS = 140 Hz at 14 GHz
   [derived]; total budget in TR 101 545-4 is 1590 Hz (Ku) / 3784 Hz (Ka) incl. satellite LO and Doppler, i.e.
   **f = 0.03 only at Rs = 53 ksps (Ku) / 126 ksps (Ka)** [derived]; at 200 ksps (the lowest rate of the one
   commercial RCS2 hub receiver seen, Creonic, snippet) f = 0.008 (Ku) / 0.019 (Ka) [derived]; at 1 Msps 0.0016 /
   0.0038. Non-locked terminal (free-running 1 ppm TCXO): 14 kHz at 14 GHz = 0.03 at 467 ksps, 0.07 at 200 ksps
   [derived]. The RCS2 guideline assumes 0.5-3 % (0.03 is its top corner); the ViaSat return-link patent assumes 10 %.
   **So 0.03 = low-rate (<= ~130 ksps) NCR-locked RCS2 bursts, or a few-hundred-ksps non-locked terminal.**
5. **What to add to the comparison**: see section 0 (V1 ViaSat-UW, C5b CCSDS block pilots) and the standards map in
   3.1. No new estimator is needed beyond those: deployed estimators (M&M, L&R, Fitz, R&B FFT) are near the CRB above
   threshold, and est4 already has ML and M&M.

---

## 2. Per-source table (ordered as read; comparability rank from section 0 in the Relevance column)

Physical scenario columns: band, Rs, uncertainty -> |f| [derived], and "vs 0.03" = above / near / below our range.

| # | Source | Link | Read | Relevance | Algorithm (DA / NDA, known-symbol amount) | Physical scenario -> \|f\| | vs 0.03 | SNR | Reported numbers | Comparability |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ETSI TR 102 376-1 V1.2.1 (2015), DVB-S2 implementation guidelines, Annex B / C | [etsi.org PDF](https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf) | chars 100k-300k of 337k (Annexes B, C; cl. 4.4, 7.2) | **high** (official DVB-S2 sync chain with numbers); comparability rank 5 | frame: differential correlator on 26-sym SOF + 64-sym PLSCODE (90-sym PLHEADER); coarse: pilot-only 2nd-order FLL (FED on pilots, frozen on data), BL 1e-4; fine: **L&R on pilots** (N = 18, L = 1000 pilot fields of 36 symbols); phase: per-pilot ML (Lp = 36) + linear interpolation; 16/32APSK add a Q-th power NDA DPLL; pilots 36 per 1440 data (2.4 %) | Ku DTH LNB ±5 MHz at 25 Mbaud -> **0.2**; after coarse ±100 kHz -> 4e-3; 30 kHz/s ramp; DSNG transmit uncertainty < 0.5 % Rs (cl. 7.2.4) | coarse range **above** (but multi-frame), fine range **far below** (3.5e-4) | design down to Es/N0 -2 dB | coarse 5 MHz -> 100 kHz in ~100 ms; L&R RMS 6e-5 (-2 dB), 5.2e-5 (1 dB), 2.72e-5 (6.6 dB), 1.82e-5 (10 dB), target 5.3e-5, ~60 ms; at -2 dB needs L ~ 2500; alternative [i.12]: 25 % Rs -> 1e-4 in < 20 frames; frame acq. mean 20 ms / 99 % 130 ms at -2 dB; losses QPSK 1/2 ~0.1 dB, 8PSK 2/3 ~0.25 dB | continuous broadcast, 64800-bit LDPC frames; acquisition over 1e5-1e6 symbols |
| 2 | ETSI TR 102 376-2 V1.1.1 (2015), DVB-S2X guidelines (VL-SNR, superframe) | [etsi.org PDF](https://www.etsi.org/deliver/etsi_TR/102300_102399/10237602/01.01.01_60/tr_10237602v010101p.pdf) | chars 0-397k (full text; figures not read) | **high** (lowest-SNR official burst-mode detector); rank 4 | VL-SNR: **900-sym UW**, 16 x 56-sym segments, segment-coherent combining, DA; > 1 % CFO: quadricorrelator FLL first, or step search over frequency bins (B.4); superframe: 270-sym SOSF + SFFI (differential, 15-sym sub-blocks, 495 effective symbols); coarse (C.5.2.4.2.1): quadricorrelator BLT 2.7e-8 | burst-mode detector designed for **1 % of Rs**; quadricorrelator from ~3 %; forward LNB ±5 MHz (DTH), ±3 MHz VSAT; aero Doppler example 22.2 kHz at 20.2 GHz | detector **below** (1 %), FLL near (3 %, multi-frame) | Es/N0 down to -10 dB (BPSK-S 1/5 at -9.9 dB, FER 1e-5) | detection "reliable at Es/N0 near -10 dB" for <= 1 % (Fig. B.5, values not in text); quadricorrelator at -10 dB: residual mean 1e-4, std 1e-4 of Rs in ~50 ms (at 500 Mbaud ~2.5e7 symbols [derived]); SF lock 0.9914 within 5 SOSFs at Pr(miss) = 0.1; PLH WER threshold ~ -3.5 dB C/N at 1e-7 | 900 known symbols per frame; burst-mode UW is the closest analogue to a single packet |
| 3 | CCSDS 130.11-G-2 (2023), SCCC Summary of Definition and Performance (for CCSDS 131.2-B-2) | [ccsds.org PDF](https://public.ccsds.org/Pubs/130x11g2.pdf) | chars 0-100k of 126k (sec. 1-6.3) | **high** (official space reference receiver); rank 3 | FM 256 sym (pi/2-BPSK) + FD 64 sym per 133 760-sym frame; pilots 16 sym every 540 data (~3 %); freq: **1024-point FFT on the de-modulated FM + Newton interpolation**, inside a frame-level FLL (k1 = 0.2, or 0.32 / 0.16); phase: DA ML on FM (16-sym blocks) and pilot fields + linear interpolation | LEO Ka: test Doppler 1 MHz, 50 kHz/s at 100 MBaud -> **0.01** (zenith 27 GHz pass: 600 kHz, 7 kHz/s) | **below** | lowest ModCod Es/N0 -0.58 dB (QPSK, CER 1e-4) | FLL BL < 186.9 Hz at 100 MBaud, SNR_FLL > 29.5 dB; sync chain loss 0.2-0.4 dB at CER 1e-4; end-to-end with nonlinearity 0.2-0.8 dB; FD soft ML 1e-5 at -4 dB | very long frames; FLL over frames; acquisition not simulated |
| 4 | Bertolucci, Cassettari, Fanucci, Sensors 21(9) 2915, 2021 (CCSDS 131.2 frequency / timing estimation) | [PMC8122673](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/) | full | **high** (classic DA estimators on an official header at low SNR, with FPGA cost); rank 3 | DA on the 256-sym FM: D&M, Kay, Fitz, L&R, **M&M (chosen)**, O'Shea; FLL with M&M + Fitz; timing Gardner / Lee / O&M | LEO Ka 40 GHz, 5-500 Mbaud: worst Doppler ~1.5 MHz at 5 Mbaud -> **0.3**; 50 kHz/s | **above** (but tracked over frames) | Es/N0 -2 dB worst case | at -2 dB, 5 Mbaud: RMS D&M 2.5 MHz, Fitz (N=2) 1.67 MHz, L&R (N=2) 239 kHz, **M&M (N=128) 705 Hz = 1.41e-4 cyc/sym** (DA CRB std for 256 symbols at -2 dB 1.2e-4 -> ~1.2x CRB [derived]); loop 239 Hz RMS; Kay biased below ~8 dB; FPGA (RFSoC) freq block 1723 LUT, 32 DSP, 544 MHz; 25 196 cycles per estimate | single-block DA numbers transfer to our known-block competitors (C3 / C4 / C5) |
| 5 | gr-dvbs2rx (open GNU Radio DVB-S2 receiver): support page + `lib/pl_freq_sync.{h,cc}` | [docs](https://igorauad.github.io/gr-dvbs2rx/docs/support.html), [source](https://github.com/igorauad/gr-dvbs2rx/tree/master/lib) | support page + two source files | medium (open deployed code); rank 5 | coarse: DA on SOF (26) or full PLHEADER (90), autocorrelation lags 1..L (L = 89), weighted mean of successive lag-phase differences (**M&M-type** [my reading; the file cites no reference]), averaged over `period` frames, range ±0.5; fine: phase difference between consecutive pilot blocks, range 1/(2 x 1476) = 3.39e-4 | example: 100 kHz offset (Rs not stated) | coarse **above**, fine **far below** | QPSK down to ~2 dB in pilot mode | "PL sync algorithms are the current performance bottleneck"; live: QPSK 3/5, 1 Mbaud | research implementation, continuous mode |
| 6 | MathWorks, "End-to-end DVB-S2 simulation with RF impairments and corrections" | [mathworks.com](https://www.mathworks.com/help/satcom/ug/end-to-end-dvbs2-simulation-with-rf-impairments-and-corrections.html) | full page | medium (reference chain); not comparable (multi-frame) | coarse: pilot FLL (BL 1e-3), up to 20 % Rs; fine: angle(R) / (pi (N + 1)), N = 18 (**L&R form**) over pilot blocks, up to 4 %; phase from pilots needs residual < 0.02 % Rs | example 3 MHz at 26.67 Msym/s -> 0.1125 [derived] | coarse **above** (multi-frame) | example Es/N0 9.1 dB | PER 0 over 50 frames, decoding from frame 32 | high SNR, continuous |
| 7 | MathWorks, "End-to-end CCSDS flexible advanced coding and modulation simulation" (CCSDS 131.2) | [mathworks.com](https://www.mathworks.com/help/satcom/ug/end-to-end-ccsds-flexible-advanced-coding-and-modulation-simulation-with-rf-impairments-and-corrections.html) | full page | medium; not comparable (multi-frame) | FM-aided FLL (FFT + peak interpolation, k1 = 0.17), FM fine estimate, pilot-field phase recovery | 1 MHz CFO + 1 MHz sinusoidal Doppler (50 kHz/s) at 100 MBaud -> 0.01-0.02 [derived] | **below** | Es/N0 1 dB (FLL converges at 0 dB) | BER 0; first 15 frames (~2.0e6 symbols [derived]) excluded as acquisition | continuous |
| 8 | ECSS-E-ST-50-05C Rev. 2 (2011), Radio frequency and modulation (ESA TT&C) | [ecss.nl PDF](https://ecss.nl/wp-content/uploads/standards/ecss-e/ECSS-E-ST-50-05C_Rev24October2011.pdf) | chars 0-100k of 130k | medium (agency CFO budgets); not comparable | ground: Doppler predicts + triangular sweep for the on-board 2nd-order PLL (2BL = 800 Hz); suppressed-carrier QPSK / OQPSK / GMSK telemetry >= 2 Msps; no estimator specified | spacecraft TX stability ±2e-5: at X-band 8.45 GHz ±169 kHz -> **0.17 at 1 Msps, 0.017 at 10 Msps** [derived]; uplink sweeps ±150 kHz (S), ±0.5-1 MHz (X), Doppler predict error <= 5 kHz | 1 Msps above, 10 Msps below | not given | sweep rates 1 Hz/s-50 kHz/s; phase noise 2-10 deg RMS | continuous links, loops after Doppler predicts |
| 9 | NASA DSN 810-005, Module 206E (Telemetry general information) | [JPL PDF](https://deepspace.jpl.nasa.gov/dsndocs/810-005/206/206E.pdf) | full module (via reader) | low-medium; not comparable | closed-loop carrier tracking, residual or suppressed carrier (Costas), loop BL 0.2-100 Hz (0.1 % of Rs at K-band high rate) | Doppler removed by predicts; residual after lock ~0 | **below** | not given here (in Module 207, not found online) | QPSK / OQPSK 40 ks/s-26 Ms/s; turbo FER floor ~1e-6; LDPC per CCSDS 131.0-B | continuous, long passes |
| 10 | CCSDS 130.1-G-3 (2020, EC1 2024), TM synchronization and channel coding, summary | [ccsds.org PDF](https://public.ccsds.org/Pubs/130x1g3e1.pdf) | chars 0-100k of 272k | low; not comparable | ASM for frame sync and BPSK sense; coded performance "assume no synchronization losses" (sec. 3.3.3) | carrier sync assumed | n/a | n/a | none on carrier sync | carrier sync left to the (loop) receiver |
| 11 | Vilà-Valls, Navarro, Closas, Bertinelli, "Synchronization challenges in deep space communications", IEEE (year not stated in the file; refs to 2017) | [Zenodo PDF](https://zenodo.org/records/3471450/files/Synchronization%20Challenges%20in%20Deep%20Space.pdf) | full (via reader) | low; not comparable (residual-carrier telecommand) | ground sweep + 2nd-order PLL baseline; FFT Doppler acquisition; FLL-assisted PLL; adaptive Kalman | X-band uplink, Doppler ±400 kHz, ±2 kHz after compensation, 30 Hz/s; Rs 7.8-4000 sps | residual carrier tone, normalisation meaningless | Es/N0 target 2 dB at WER 1e-5 | baseline fails below 500 sps; FFT acquisition 22-24 Hz RMSE (8192-pt, 10 blocks), 0 misacq. at >= 4 dB, 3 / 50 at 2 dB | PCM/PSK/PM with residual carrier = a pilot tone |
| 12 | Gannon, Downey, Koch (NASA GRC), onboard Doppler pre-compensation for low-rate relay links, 2022 | [NTRS PDF](https://ntrs.nasa.gov/api/citations/20220013336/downloads/gannon2022_kaconf_doppler_wcopyright.pdf) | full (via reader) | medium (what commercial DVB-S2 modems tolerate); not comparable | transmitter pre-compensation from an orbit propagator (piecewise linear, 1 s steps); receiver = commercial DVB-S2 modems, QPSK 1/2, pilots on | Ka relay (LEO -> GEO / MEO), peak Doppler 699-826 kHz (25 ppm): uncompensated **3.3 at 250 kbaud** [derived]; residual after pre-comp 1.35-2.16 kHz -> **0.0054-0.0086** [derived] | uncompensated far above; compensated below | 3 dB above DVB-S2 QEF | without compensation the modems need >= ~1-5 Mbaud; with it, 0 frame errors, lock 10-42 s | commercial receivers do not acquire large CFO at low Rs: the transmitter removes it |
| 13 | EN 301 790 V1.5.1 (2009), DVB-RCS (first generation) | [etsi.org PDF](https://www.etsi.org/deliver/etsi_EN/301700_301799/301790/01.05.01_60/en_301790v010501p.pdf) | chars 0-100k of 456k (cl. 6) | **high** for the GEO mapping; rank 1 family | RCST locked to NCR (27 MHz from the forward link, NCC clock 5 ppm); burst preambles set by the TCT | carrier accuracy < 1e-8 RMS: 140 Hz at 14 GHz -> 1.1e-3 at 128 ksps, 2.6e-3 at 53 ksps [derived] | **below** (terminal part alone) | n/a | burst timing within 0.5 symbol; symbol clock 20 ppm | terminal error only; satellite LO / Doppler add (TR 101 545-4 budget, `lit_dvbrcs2.md`) |
| 14 | Thesling, Vanderaar (Efficient Channel Coding / ViaSat), "Star receiver burst processing", US 7653150 B2, 2010 | [Google Patents](https://patents.google.com/patent/US7653150B2/en) | description (Google Patents page) | **high** (deployed-class single-burst blind CFO); **rank 2** | **NDA 4th-power, 512 symbols zero-padded to 1024-pt FFT, peak + 2 neighbours interpolation, /4**; phase from the bins /4; pi/2 ambiguity and timing (±8 symbols) by a 16-symbol midamble UW; TPC (32,26)^2 | GEO return link, burst CFO **up to 10 % of Rs** | **above** | Eb/N0 1.4 dB at BER 1e-5 -> Es/N0 ~2.6 dB [derived, rate 0.66] | ~0.2 dB loss vs ideal timing and carrier; "sync fails only just below the FEC" | same structure as our fast path / est4 C2, at ~7.6 dB higher Es/N0 than our -5 dB point |
| 15 | ComBlock COM-1802 PSK burst modem datasheet | [comblock.com PDF](https://www.comblock.com/download/com1802.pdf) | full | medium (vendor burst modem); rank 6 | FFT frequency acquisition + FFT presence detection on a 50-symbol toggling preamble + 32-symbol sync word; coherent BPSK / QPSK, conv. K = 9 r 1/2 | **±20 % of Rs** "no a priori knowledge" (marked TBC), up to 40 Msym/s | **above** | thresholds "TBD" | none | preamble-based; no low-SNR numbers |
| 16 | ComBlock COM-1852 (CCSDS Proximity-1 receiver) datasheet / CCSDS 211.1-B | [comblock.com PDF](https://www.comblock.com/download/com1852soft.pdf) | search snippet only (PDF not parseable) | low-medium; not comparable | Prox-1 physical layer; acquisition method not read | two-sided acquisition window 160 kHz (Doppler + synthesizer drift), Doppler rate 200 Hz/s; at 2 Msps 0.04, at 256 ksps 0.31 [derived; the rate list was not read] | depends on rate | not read | idle sequence >= 3200 bits for 1 % symbol-rate offset | continuous sessions with idle acquisition sequence |
| 17 | Safran LYNKS TDMA DMX datasheet | [safran-group.com PDF](https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20LYNKS%20TDMA%20DMX%20-%20Datasheet_0.pdf) | full | low; not comparable | MF-TDMA monitoring, blind burst analysis | from 128 kBaud per carrier; CFO is an output, no range given | n/a | SNR > 6 dB | none | monitoring product, high SNR |
| 18 | Creonic DVB-RCS2 multi-carrier receiver brief | [Intel marketplace](https://marketplace.intel.com/file-asset/a5Y3b0000008GiaEAE_a5b3b0000004ex9AAA) | search snippet only | low-medium (GEO mapping) | not read | 200 ksym/s-12.5 Msym/s per carrier: with the TR Ku / Ka budget -> 0.008 / 0.019 at 200 ksps [derived] | **below** at its lowest rate | not read | not read | lowest commercial RCS2 hub rate seen |

Not found or not readable: CCSDS 131.3-B (DVB-S2 for space) text (the ccsds.org links returned 404); CCSDS 401.0-B
current text (mirror host unreachable; only a search snippet: Earth-station acquisition sweeps ±150 kHz at 2 GHz,
±600 kHz at 8 GHz); DSN 810-005 Module 207 (carrier-loop recommendations; not online under the guessed name); NASA
Near Space Network User's Guide 457-GUIDE-0001 (only its cover / table of contents were indexed); DVB-SH (not pursued
after the single-carrier clarification; its TDM mode is DVB-S2-like); any CCSDS / NASA / ESA document with a
single-burst CFO estimator at Es/N0 below about -2 dB; the Proximity-1 standard text.

---

## 3. Comparison support

### 3.1 A "standards map" for the est4 competitors (text only, no new runs)

| est4 / new receiver | Deployed / official counterpart | Where it sits vs ours |
|---|---|---|
| C3 `pre128 ML` / `pre128 M&M` | DVB-RCS2 TR 101 545-4 6.2.2.1 assumption ("frequency estimated on the preamble"); M&M as in Bertolucci 2021 (CCSDS 131.2 HW) and gr-dvbs2rx coarse; R&B FFT + Newton as in CCSDS 130.11-G-2 5.7 | single-shot version of the FLL front ends; deployed systems then refine over frames, which a single packet cannot |
| C4 `split64` | Ying-Ghogho optimal split (`lit_dvbrcs2.md`); RCS2 pre + post | - |
| C1a / C1b `RCS2-13` | DVB-RCS2 EN 301 545-2 ID 13; C1b ~ ESA PA-SWI, DVB-S2 TR C.6.1 linear interpolation | pilots as single symbols (RCS2) |
| C2 `RCS2 pre/post` (+ new V1) | RCS2 IDs 5 / 15 (Griebel NDA) and **ViaSat US 7653150** (4th-power FFT + 16-symbol UW, ±10 % Rs) | deployed at Es/N0 ~2.6 dB; fails below 0 dB in est4 |
| new C5 | CCSDS 131.2 / DVB-S2 pilot blocks | space-agency layout |
| blind (ours) | none; closest official: DVB-S2X VL-SNR burst UW (<= 1 % CFO, 900 known symbols) | only design with 3 % in one burst and 0 known symbols |

Physical scenario sentence for the README [derived]: |f| <= 0.03 corresponds to a GEO MF-TDMA return-link burst at
Rs ~ 50-130 ksps with an NCR-locked terminal (TR 101 545-4 budget 1590 Hz Ku / 3784 Hz Ka), or to a free-running
1 ppm terminal at ~470 ksps (Ku 14 GHz), or to a LEO Ka link of ~33 Msps with Doppler not pre-compensated (CCSDS
130.11 test Doppler 1 MHz). Standards with larger CFO (DVB-S2 20 %, ViaSat 10 %, vendors 20 %) handle it with
multi-frame loops or at Es/N0 >= ~2 dB.

### 3.2 What NOT to add

- A multi-frame FLL (DVB-S2 / CCSDS / VL-SNR quadricorrelator): needs 1e5-1e7 symbols; not applicable to one packet.
- L&R, Fitz, Kay, D&M as separate competitors: L&R / Fitz ranges are 1/(N+1) / 1/(2N) in the autocorrelation lag N,
  so for |f| <= 0.03 they need N <= 32 / 16, i.e. far from the CRB with 128 known symbols; Kay is biased below ~8 dB
  (Bertolucci 2021). M&M (in est4) represents the autocorrelation family and R&B FFT (in est4) is ML.
- The full VL-SNR 900-symbol UW: 88 % overhead for 1024 data symbols and limited to 1 % CFO (the scaled V3 is the
  most that makes sense).

---

## 4. Per-component verdict (this survey only)

| Component | Deployed / official state | Verdict |
|---|---|---|
| Coarse CFO | DA FFT on a known header (CCSDS 131.2) or DA autocorrelation (M&M / L&R) + multi-frame FLL; NDA 4th-power FFT in one GEO burst product (ViaSat) | **we already use it** (4th-power FFT fast path); our grid search goes beyond, since no standard acquires 3 % in one burst below ~2 dB |
| Fine CFO / phase | L&R over many pilot blocks; per-pilot-block ML phase + linear interpolation; NDA DPLL for APSK | **we already use** the single-packet equivalent (refinement + code-aided); multi-frame averaging **not applicable** |
| Hypothesis search | VL-SNR: step search over frequency bins dwelling several frames (B.4); ViaSat: UW correlation over ±8 timing x 4 rotations | **we already use it** (CFO x phase grid with decoder metric) |
| Acceptance / false alarm | UW / SOSF detection with thresholds (DVB-S2 FSM thresholds Table C.1; VL-SNR miss / false curves); PLSCODE / FD block codes; CRC in the payload | **we already use** CRC + rho; the standards give no per-packet false-alarm bound beyond UW detection |
| Complexity | FPGA numbers: M&M + Fitz freq block 1723 LUT / 32 DSP (Bertolucci); FFT interpolation (Griebel) | not comparable to MACs per core; no deployed number for a decoder-in-the-loop search |
| ML gates | none in any standard or agency document read | not applicable |

Comparability, plainly: every official system above uses long or continuous frames, multi-frame loops, or a higher
Es/N0 than our -5 dB; most use LDPC / turbo / SCCC, not polar; roll-offs 0.05-0.35 (ours 0.25). Their dB losses
(0.1-0.4 dB) are for that setting and must not be quoted as what a pilot receiver would lose at our points.

---

## Reference entries

### TR 102 376-1
# ETSI TR 102 376-1 V1.2.1 (2015-11), Digital Video Broadcasting (DVB); Implementation guidelines for the second generation system for broadcasting, interactive services, news gathering and other broadband satellite applications; Part 1: DVB-S2
- Link: https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf   - Type: standard (technical report)   - Read depth: partial (chars 100k-300k of 337k, Annexes B-C)
## What it does
DVB-S2 reference demodulator: SOF / PLHEADER differential-correlator frame sync, pilot-only FLL coarse (Ku DTH ±5 MHz at 25 Mbaud = 0.2 cycles/symbol [derived] -> 4e-3 in ~100 ms), Luise-Reggiannini fine on 36-symbol pilot blocks (RMS 6e-5 at Es/N0 -2 dB with 1000 blocks), per-pilot ML phase + linear interpolation (cycle slip if f >= 1/(2 x 1476)), losses 0.1-0.25 dB (QPSK 1/2, 8PSK 2/3). Design down to Es/N0 -2 dB; 64800-bit LDPC frames.
## What we took / could take
Comparability rank 5: single-shot core = V4 "S2-header" (90-symbol header + M&M); labels est4 C1b / C3 M&M with the DVB-S2 counterpart.
## Used in

### TR 102 376-2
# ETSI TR 102 376-2 V1.1.1 (2015-11), DVB implementation guidelines, Part 2: S2 Extensions (DVB-S2X)
- Link: https://www.etsi.org/deliver/etsi_TR/102300_102399/10237602/01.01.01_60/tr_10237602v010101p.pdf   - Type: standard (technical report)   - Read depth: full text (figures not read)
## What it does
VL-SNR burst reception: 900-symbol UW (16 x 56 segments), segment-coherent combining, reliable detection near Es/N0 -10 dB for CFO <= 1 % of Rs; above 1 % a quadricorrelator FLL (acquires from ~3 % after several hundred thousand symbols at -9.6 dB) or a frequency-bin step search. Superframe SOSF / SFFI sync; quadricorrelator residual 1e-4 mean / 1e-4 std of Rs at -10 dB in ~50 ms. Forward LNB ±5 MHz (DTH), ±3 MHz (VSAT).
## What we took / could take
Comparability rank 4: V3 "VL-SNR-scaled" (128-symbol segmented UW + bin search); shows the 1 % single-burst design limit vs our 3 %.
## Used in

### CCSDS 130.11-G-2
# CCSDS 130.11-G-2, SCCC - Summary of Definition and Performance, Informational Report (Green Book), Issue 2, May 2023
- Link: https://public.ccsds.org/Pubs/130x11g2.pdf   - Type: standard (informational report)   - Read depth: partial (chars 0-100k of 126k)
## What it does
Reference receiver for CCSDS 131.2-B: 256-symbol frame marker + 64-symbol descriptor per 133 760-symbol frame, 16-symbol pilot fields every 540 data symbols (~3 %); 1024-point FFT on the FM + Newton interpolation inside a frame-level FLL; DA ML phase on FM / pilots + linear interpolation. Test Doppler 1 MHz, 50 kHz/s at 100 MBaud (0.01 cycles/symbol [derived]). Lowest ModCod Es/N0 -0.58 dB at CER 1e-4; sync loss 0.2-0.4 dB.
## What we took / could take
Comparability rank 3: basis of competitor C5 (block pilots, section 0); confirms R&B FFT + interpolation (est4 C3 / C4) is the agency's estimator.
## Used in

### Bertolucci 2021
# M. Bertolucci, R. Cassettari, L. Fanucci, "On the Frequency Carrier Offset and Symbol Timing Estimation for CCSDS 131.2-B-1 High Data-Rate Telemetry Receivers", Sensors 21(9):2915, 2021, doi:10.3390/s21092915
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/   - Type: paper   - Read depth: full
## What it does
Compares D&M, Kay, Fitz, L&R, M&M, O'Shea on the 256-symbol CCSDS FM at Es/N0 -2 dB, 5-500 Mbaud, LEO Ka Doppler up to ~0.3 cycles/symbol at 5 Mbaud [derived]; M&M chosen: 705 Hz RMS at 5 Mbaud = 1.41e-4 cycles/symbol, ~1.2x the 256-symbol DA CRB std [derived]; Kay biased below ~8 dB; FPGA freq block 1723 LUT / 32 DSP at 544 MHz.
## What we took / could take
Supports keeping M&M (est4 C3 M&M) as the autocorrelation-family representative and not adding L&R / Fitz / Kay separately.
## Used in

### gr-dvbs2rx
# gr-dvbs2rx: open-source DVB-S2 receiver for GNU Radio (GitHub igorauad/gr-dvbs2rx), documentation and lib/pl_freq_sync.{h,cc}, accessed 2026-11-15
- Link: https://github.com/igorauad/gr-dvbs2rx   - Type: open-source implementation   - Read depth: support page + two source files
## What it does
Coarse CFO: DA on the 90-symbol PLHEADER, lag-1..89 autocorrelation, weighted mean of successive lag-phase differences (M&M-type, my reading), averaged over frames, range ±0.5; fine: pilot-block phase differences, range 3.39e-4; QPSK down to ~2 dB SNR in pilot mode; PL sync is the stated bottleneck.
## What we took / could take
Chain for V4 "S2-header" (rank 5); otherwise nothing new to borrow.
## Used in

### MathWorks DVB-S2 example
# MathWorks, Satellite Communications Toolbox example "End-to-End DVB-S2 Simulation with RF Impairments and Corrections", accessed 2026-11-15
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-dvbs2-simulation-with-rf-impairments-and-corrections.html   - Type: app note / reference example   - Read depth: full page
## What it does
Pilot FLL coarse (up to 20 % of Rs), L&R-form fine (angle(R)/(pi(N+1)), N = 18, up to 4 %), pilot phase (needs residual < 0.02 %); example 3 MHz at 26.67 Msym/s (0.11 [derived]), Es/N0 9.1 dB, PER 0 after ~32 frames.
## What we took / could take
Not used: multi-frame, high SNR (context only).
## Used in

### MathWorks CCSDS FACM example
# MathWorks, "End-to-End CCSDS Flexible Advanced Coding and Modulation Simulation with RF Impairments and Corrections", accessed 2026-11-15
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-ccsds-flexible-advanced-coding-and-modulation-simulation-with-rf-impairments-and-corrections.html   - Type: app note / reference example   - Read depth: full page
## What it does
CCSDS 131.2 chain: FM-aided FFT FLL, FM fine estimate, pilot-field phase; 1 MHz CFO + 1 MHz Doppler at 100 MBaud (0.01-0.02 [derived]), Es/N0 1 dB, BER 0 after 15 acquisition frames.
## What we took / could take
Not used: multi-frame (context only).
## Used in

### ECSS-E-ST-50-05C
# ECSS-E-ST-50-05C Rev. 2, Space engineering - Radio frequency and modulation, ESA-ESTEC, 4 October 2011
- Link: https://ecss.nl/wp-content/uploads/standards/ecss-e/ECSS-E-ST-50-05C_Rev24October2011.pdf   - Type: standard   - Read depth: partial (chars 0-100k of 130k)
## What it does
ESA TT&C RF rules: spacecraft TX stability ±2e-5 (X-band ±169 kHz: 0.17 cycles/symbol at 1 Msps, 0.017 at 10 Msps [derived]); Doppler predicts within 5 kHz; uplink sweeps ±150 kHz (S) to ±1 MHz (X) for an on-board 2nd-order PLL (2BL 800 Hz); suppressed-carrier QPSK / OQPSK / GMSK for >= 2 Msps; phase noise 2-10 deg RMS. No estimator specified.
## What we took / could take
Physical-scenario mapping only (agency CFO budgets); not a competitor.
## Used in

### DSN 810-005 Module 206
# NASA JPL, DSN Telecommunications Link Design Handbook 810-005, Module 206, Rev. E, Telemetry General Information
- Link: https://deepspace.jpl.nasa.gov/dsndocs/810-005/206/206E.pdf   - Type: standard (agency handbook)   - Read depth: full module via text reader
## What it does
DSN closed-loop carrier tracking (residual or suppressed carrier / Costas), loop BL 0.2-100 Hz, QPSK / OQPSK 40 ks/s-26 Ms/s, CCSDS turbo / LDPC; loop recommendations and losses are in Module 207 (not found).
## What we took / could take
Not used: continuous-mode PLL receivers with Doppler predicts; no single-burst acquisition.
## Used in

### CCSDS 130.1-G-3
# CCSDS 130.1-G-3, TM Synchronization and Channel Coding - Summary of Concept and Rationale, Green Book, June 2020 (EC1 October 2024)
- Link: https://public.ccsds.org/Pubs/130x1g3e1.pdf   - Type: standard (informational report)   - Read depth: partial (chars 0-100k of 272k)
## What it does
ASM frame sync and BPSK sense resolution; coded performance "assume no synchronization losses"; carrier sync left to the receiver.
## What we took / could take
Not used: no carrier-sync content.
## Used in

### Vila-Valls deep space sync
# J. Vilà-Valls, M. Navarro, P. Closas, M. Bertinelli, "Synchronization Challenges in Deep Space Communications", IEEE (year and venue not stated in the file; references to 2017)
- Link: https://zenodo.org/records/3471450/files/Synchronization%20Challenges%20in%20Deep%20Space.pdf   - Type: paper   - Read depth: full via text reader
## What it does
X-band residual-carrier telecommand (PCM/PSK/PM), Doppler ±400 kHz (±2 kHz after compensation), 7.8-4000 sps; sweep + PLL fails below 500 sps; FFT acquisition 22-24 Hz RMSE (8192-point, 10 blocks); Kalman tracking best; target Es/N0 2 dB.
## What we took / could take
Not used: residual-carrier (tone) systems are not comparable to suppressed-carrier blind QPSK.
## Used in

### Gannon 2022
# A. Gannon, J. Downey, M. Koch (NASA Glenn), onboard Doppler pre-compensation for low-rate Ka-band relay links, 2022 (conference paper, venue not stated in the text)
- Link: https://ntrs.nasa.gov/api/citations/20220013336/downloads/gannon2022_kaconf_doppler_wcopyright.pdf   - Type: paper   - Read depth: full via text reader
## What it does
Commercial DVB-S2 modems (QPSK 1/2, pilots) on LEO -> GEO / MEO Ka relays: Doppler 699-826 kHz (3.3 cycles/symbol at 250 kbaud [derived]) is not acquired below ~1-5 Mbaud; transmitter pre-compensation leaves 1.35-2.16 kHz (0.005-0.009 [derived]), then 0 frame errors, lock 10-42 s.
## What we took / could take
Supports the "outside the design envelope" statement; not a competitor.
## Used in

### EN 301 790
# ETSI EN 301 790 V1.5.1 (2009-05), Digital Video Broadcasting (DVB); Interaction channel for satellite distribution systems (DVB-RCS)
- Link: https://www.etsi.org/deliver/etsi_EN/301700_301799/301790/01.05.01_60/en_301790v010501p.pdf   - Type: standard   - Read depth: partial (chars 0-100k of 456k)
## What it does
RCST carrier frequency accuracy < 1e-8 RMS (cl. 6.1.2), NCR-derived 27 MHz reference (NCC clock 5 ppm), burst timing within 0.5 symbol, symbol clock 20 ppm; burst preambles set by the TCT. 1e-8 at 14 GHz = 140 Hz = 1.1e-3 cycles/symbol at 128 ksps [derived].
## What we took / could take
GEO return-link mapping of |f| <= 0.03 (section 1 item 4, 3.1).
## Used in

### Thesling 2010 (ViaSat)
# W. H. Thesling, M. Vanderaar (Efficient Channel Coding, assigned to ViaSat), "Star receiver burst processing", US 7653150 B2, granted 26 Jan 2010
- Link: https://patents.google.com/patent/US7653150B2/en   - Type: patent   - Read depth: description on Google Patents
## What it does
GEO return-link bursts with CFO up to 10 % of Rs: 512-symbol QPSK burst, NDA 4th-power, 1024-point FFT, peak + neighbour interpolation, /4; 16-symbol midamble UW for ±8-symbol timing and pi/2 rotation; TPC (32,26)^2 at Eb/N0 1.4 dB (BER 1e-5; Es/N0 ~2.6 dB [derived]); ~0.2 dB sync loss.
## What we took / could take
Comparability rank 2: competitor V1 "ViaSat-UW" (16-symbol midamble, 0.07 dB, 4th-power FFT chain); the deployed counterpart of est4 C2 and of our 4th-power fast path.
## Used in

### ComBlock COM-1802
# ComBlock (MSS), COM-1802 PSK burst modem 40 Msymbols/s, datasheet
- Link: https://www.comblock.com/download/com1802.pdf   - Type: app note / datasheet   - Read depth: full
## What it does
BPSK / QPSK burst modem, 50-symbol preamble + 32-symbol sync, FFT frequency acquisition ±20 % of Rs without a priori knowledge (marked TBC); Es/N0 thresholds TBD.
## What we took / could take
Comparability rank 6: covered by est4 C3 (FFT on a preamble); vendor data point for the CFO range.
## Used in

### ComBlock COM-1852 / Proximity-1
# ComBlock, COM-1852 CCSDS Proximity-1 receiver datasheet (CCSDS 211.1-B physical layer)
- Link: https://www.comblock.com/download/com1852soft.pdf   - Type: app note / datasheet   - Read depth: search snippet only (PDF not parseable)
## What it does
Two-sided acquisition window 160 kHz (Doppler + synthesizer drift), Doppler rate 200 Hz/s; symbol-rate offset < 1 % only with >= 3200-bit idle sequence.
## What we took / could take
Not used (snippet only; continuous sessions with an idle acquisition sequence).
## Used in

### Safran LYNKS TDMA DMX
# Safran Data Systems, LYNKS TDMA DMX datasheet, 2022
- Link: https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20LYNKS%20TDMA%20DMX%20-%20Datasheet_0.pdf   - Type: app note / datasheet   - Read depth: full
## What it does
MF-TDMA monitoring / blind burst analysis from 128 kBaud per carrier, SNR > 6 dB; CFO is an output, no acquisition range.
## What we took / could take
Not used (no numbers on CFO range or low SNR).
## Used in

### Creonic DVB-RCS2 receiver
# Creonic, DVB-RCS2 multi-carrier receiver IP product brief
- Link: https://marketplace.intel.com/file-asset/a5Y3b0000008GiaEAE_a5b3b0000004ex9AAA   - Type: app note / product brief   - Read depth: search snippet only
## What it does
200 ksym/s-12.5 Msym/s per carrier at 200 MS/s input.
## What we took / could take
Lowest commercial RCS2 hub symbol rate seen; with the TR 101 545-4 budget gives f = 0.008 (Ku) / 0.019 (Ka) [derived].
## Used in
