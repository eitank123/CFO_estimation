# Competitor "cards": DVB-RCS2, DVB-S2 / S2X, ViaSat burst patents, Advantech hybrid DA + NDA (2026-11-15)

Literature scout report. No simulations were run, no code or REFERENCES.md edited. Code rates / MODCOD thresholds are
NOT covered here (lit_rates.md). This file fills the gaps left by `competitors.md`, `expected_est5.md`,
`lit_ars2021.md`, `lit_dvbrcs2.md`, `lit_real_space.md`, `lit_real_leo.md`, `lit_real_military.md`; what is already
solid there is only referenced, not repeated.

**Labels on every number:** [std] = standard / official guideline text; [paper]; [patent]; [vendor] = datasheet,
press release, vendor web page or a vendor-written example (MathWorks); [derived] = my arithmetic from the cited
numbers; [prev: file] = read and reported by an earlier survey in this folder (not re-read today); [my reading] =
an interpretation of a source's wording. "Not found" means searched and not found.
f = CFO / Rs in cycles per symbol (ours: |f| <= 0.03).

**How sources were read today:** Google Patents pages (US 7653150, US 8243859, US 7590199, US 7593490), the ETSI PDFs
EN 301 545-2 V1.5.1, EN 302 307-1 V1.4.1, EN 302 307-2 V1.3.1 and DVB BlueBook C107 through a public PDF-to-text
reader (r.jina.ai, public URL only; tables come out flattened), ESA / trade-press / MathWorks pages directly.

---

## 0. Ranked actionable findings (at most 5)

1. **C14 "hyb3" is not the patent's layout, and the difference matters.** competitors.md says "pilot counts (16 + 16)
   chosen by us, not from the patent". The patent DOES give the layout: a **48-symbol contiguous preamble + 440
   payload symbols** (488 total, QPSK, rate-1/2 turbo, 64 kBd) [patent US 7590199, US 7593490]. A contiguous
   48-symbol DA spectrum is one smooth lobe ~1/48 wide that **gates** the 4th-power peaks; our 16 + 16 pre/post DA
   spectrum is a comb of near-equal fringes every 1/1040 under a 1/16-wide envelope, so the "3 candidates" become
   mostly neighbouring fringes (which the lobe search already covers) instead of 3 distinct 4th-power peaks.
   [derived] DA CRB std of a 48-symbol block: 2.1e-3 at Es/N0 -5 dB, 9.3e-4 at +2 dB; a +-3 sigma DA window holds
   ~54 (at -5 dB) / ~24 (at +2 dB) 4th-power resolution cells (1/(4 x 1072) = 2.3e-4 each) instead of ~260 over
   +-0.03, i.e. 5-11x fewer false peaks to beat. The real selector is also different: **mean |LLR| after 1-3 of
   ~10 turbo iterations** per candidate (US 7593490), not CRC.
   **Recommendation:** add "hyb3-pre48" (48-symbol preamble, Nk = 48, energy 10 log10(1072/1024) = 0.20 dB
   [derived]) next to the current hyb3; keep the CRC + rho acceptance (stronger than LLR). Expected: better than
   the current hyb3 at 2/5 and 1/2 (my estimate, not measured), probably still failing at 1/10 and 0.15. Test:
   e5-pp style job, 2/5 0 ... 1.5 dB, 1/2 1 ... 3 dB, 0.15 -3 dB sanity point.
2. **C9 "ViaSat UW" takes its phase from the 16-symbol UW; the patent takes it from the 4th-power spectrum.** In US
   7653150 the phase is theta' / 4 from the 3 FFT bins of the 4th-power spectrum over all 512 symbols; the UW only
   picks the quadrant (and the timing) [patent]. In est4, the `const` phase model on `viasat16` is the LS gain on
   the 16 UW symbols only: std 1/sqrt(2 x 16 x SNR) = **0.31 rad at -5 dB, 0.18 rad at 0 dB, 0.14 rad at +2 dB**
   [derived]; the CRC search is over CFO, not phase. So **our C9 is weaker in phase than the real chain** at 2/5 and
   1/2, where it is the only regime in which C9 works. **Recommendation:** a phase model "nda4ph" = arg X4(4 f_hat) /
   4 + the quadrant that maximises Re(UW correlation) (Griebel Eq. 13-14 is the same rule); cost ~0 MACs. Test on the
   e5-pp points at 2/5 and 1/2 only.
3. **C7 "DVB-S2-inspired" is stronger than a real DVB-S2 frame segment.** Real pilot blocks (36 symbols) come every
   16 slots = **1440 data symbols** after the 90-symbol PLHEADER (period 1476) [std EN 302 307-1 5.5.3]; a 1024-symbol
   window after the header therefore contains **no pilot block** [derived]. Our C7 puts one block at 512 (period
   602, 2.45x denser). Also, in ACM / VCM only the **26-symbol SOF** is known before the PLS code (7 bits, 64
   symbols) is decoded [std 5.5.2; derived]; our C7 treats all 90 as known (= CCM). The faithful single-burst
   version is lit_real_space's "V4 S2-header" (90 symbols, 0.37 dB, M&M). Keep C7 but **relabel** it "DVB-S2
   header + one pilot block (denser than the standard)" or add V4; do not call C7 the deployed DVB-S2 layout.
4. **DVB-RCS2 has moved on: EN 301 545-2 V1.5.1 (2026-04).** It adds NGSO support, roll-off 0.20 / 0.10 / 0.05, and
   DVB-S2X waveforms on the return link "within the TDMA grid or over a continuous carrier" (S2X bursts carrying a
   single S2X frame, payload 384-7274 bytes, cl. 9.9.5.6) [std]. **Reference waveform ID 13 is unchanged**
   (1616 symbols, QPSK 1/3, pre 32, post 31, P = 20, pilot block 1, pilot sum 77) [std V1.5.1 Annex A], so `rcs13`
   needs no change; competitors.md / REFERENCES.md C1 should cite V1.5.1 as the current version.
5. **The real DVB-RCS2 implementation loss is 0.5-0.6 dB, ours ~0 dB.** TR 101 545-4 bench: QPSK 1/3 at PER 1e-5
   needs 0.0 dB vs ideal -0.51 dB, QPSK 1/2 2.3 vs 1.71 dB (all impairments together) [prev: lit_dvbrcs2.md 1.3];
   Griebel's best DA-KS keeps 0.12-0.15 dB of estimation loss at FER 1e-3 [prev: lit_ars2021.md]; our RCS2-13 has
   d = -0.01 ... -0.04 dB at 0.15, 2/5, 1/2 [prev: lit_ars2021.md 5.2]. State in the plots that the est4 DVB-RCS2
   receiver is a **strengthened** one (CRC search, 8192-point FFT, exact LS phase, genie timing); the deployed
   chain would be 0.1-0.5 dB worse.

---

## 1. Card: DVB-RCS2 return link (TC-LM bursts), incl. Griebel & Wasenmüller 2021

### 1.1 Standard, link, deployments
- **Documents.** ETSI EN 301 545-2 (lower layers): V1.1.1 (2012-01), V1.3.1 (2020-07, used in est4), V1.4.1
  (2024-01), **V1.5.1 (2026-04, adopted 21 April 2026; current)** [std, cover page read;
  https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/en_30154502v010501p.pdf]. DVB page: V1.4.1
  added signalling for non-GSO satellites and S2X Annex E superframes; V1.5.1 "replaces ETSI EN 301 790" (DVB-RCS
  first generation) [vendor/std body, https://dvb.org/?p=8033]. Guidelines: TR 101 545-4 V1.1.1 (2014), V1.2.1 (2026)
  [prev: lit_dvbrcs2.md]. System part TS 101 545-1 V1.4.1 (2026-01) [std, search result only].
- **Link:** return (terminal -> hub), MF-TDMA **burst** mode; TC-LM (turbo, QPSK / 8PSK / 16QAM, plus pi/2-BPSK
  waveforms) and CPM waveforms; S2X continuous-carrier and S2X-in-TDMA as options in V1.5.1 [std].
- **V1.5.1 changes** [std V1.5.1 Introduction, cl. 6.4.6.5 Table 6-28b, 7.3.7.1.1, 9.9.5.6]: NGSO constellations;
  extended return-link bandwidth; **roll-off 0.20, 0.10 or 0.05** (V1.3.1: 0.20 only); DVB-S2X waveforms in the
  TDMA grid (a burst carries a single S2X frame, payload 384-7274 bytes) or as continuous carrier (the old
  continuous waveform deprecated). For VL-SNR on the return link "pilots are always mandatory" (cl. 6.4.9).
- **Requirements document:** DVB BlueBook C107 (July 2023), "Commercial requirements for the use of DVB-RCS2 in GSO
  and NGSO systems": "higher Doppler shifts generated in lower orbits" (req. 100), operation without GNSS (req. 107),
  return roll-off 5 % or better (req. 113), symbol rates up to 500 Msym/s (req. 111), consumer terminal instantaneous
  rate 128 ksps-2 Msps. **No Doppler / CFO number in Hz or ppm** [std body]. Market context in C107: VSAT terminal
  shipments > 1 million per year in 2022, ~2 million by 2026 (Euroconsult, all VSAT, not RCS2 only) [vendor/market].
- **Deployments.** First-generation DVB-RCS: > 370 networks and > 180 000 terminals by mid-2010 (SatLabs survey)
  [vendor/industry, https://resilience.esa.int/?p=9372]; mainly governmental / military networks (CSI 2011)
  [trade press]. DVB-RCS2: STM claims to be first, RCS2 in SatLink VSATs and hubs, commercial 20 March 2012, "many
  thousands of VSATs" sharing up to 50 Mbit/s TDMA [vendor, trade press]; Gilat SkyEdge listed with RCS2 support
  [vendor profile, snippet]; commercial RCS2 hub receiver Creonic 200 ksym/s-12.5 Msym/s per carrier [prev:
  lit_real_space.md #18]; NATO standards incorporate DVB-S2X / RCS2 terminals (C107) [std body]. **A current count
  of RCS2 terminals or named RCS2 operators: not found.** (Newtec Dialog deployments use the proprietary Mx-DMA
  return, not RCS2 [vendor].)

### 1.2 Burst structure (closest to our ~1000 symbols)
- Rules [std V1.5.1 cl. 6.4.6.1, 7.3.6.1, 7.3.7.1.2-3]: "A preamble is typically present in every burst"; pilot
  blocks "evenly distributed with evenly sized payload sections in between"; pilot_period (12 bit) in symbols;
  preamble + pilot block + postamble form one unique word; **known symbols use the payload constellation** (QPSK for
  QPSK bursts). Burst start accuracy 0.5 symbol (7.3.9.1); symbol clock 20 ppm (7.3.9.2); carrier accuracy **better
  than 1e-8 RMS** (7.3.9.3); NCR on the forward link 5 ppm or better (7.3.9.0); frequency corrections from the NCC in
  10 Hz steps (6.4.17.1) [std].
- Closest reference waveforms [std Annex A Table A-1; V1.3.1 table in lit_dvbrcs2.md 1.2; ID 13 re-checked today in
  V1.5.1]: **ID 13**: 1616 symbols, QPSK 1/3, 1476 payload symbols, pre 32, post 31, pilot period 20, 1-symbol
  blocks, 77 pilots: **140 known = 8.7 %** [derived], energy 10 log10(1616/1476) = 0.39 dB [derived]. ID 14: 1616,
  QPSK 1/2, 25 / 25, P = 25, 62 pilots, 112 known (6.9 %). IDs 3 / 4: 536 symbols, 80 / 64 known (14.9 / 11.9 %).
  ID 15: 1616, QPSK 2/3, pre / post 16 / 16, no pilots (2.0 %). Guard time: not in the parts read.
- Our `rcs13`: 32 + 53 x (19 d + 1 p) + 17 d + 31 = 1140 symbols, 116 known (10.2 %), 0.47 dB [prev: lit_dvbrcs2.md].

### 1.3 Synchronisation in practice
- **Known symbols used for:** burst (UW) detection, frequency, phase; timing is assumed done (Griebel: "gain control,
  timing synchronization and frame detection ... carried out properly") [paper]. No TC-LM detector or estimator is
  given in TR 101 545-4; it assumes "frequency is estimated on the preamble" (cl. 6.2.2.1) [prev: lit_dvbrcs2.md 2].
- **Estimator in the one documented implementation (Griebel, Wasenmüller, Wehn 2021):** DA-KS Rife-Boorstyn FFT over
  all known symbols (zeros at data), 3-bin magnitude interpolation, phase = arg of the interpolated bin, constant
  phase over the burst; DA-PL (pilots only) for 8PSK / 16QAM; NDA |r| e^{j4 arg r} for pilotless bursts (QPSK NDA
  only used at Es/N0 >= 3.9 dB) [paper; prev: lit_ars2021.md 2-3].
- **Range:** standard does not specify the tolerable burst CFO; TR 101 545-4 assumes **0.5-3 % of Rs** [std/prev];
  Griebel simulates uniform **|f| <= 0.015** [paper]; frequency budget Ku 1590 Hz / Ka 3784 Hz total [std/prev] ->
  f = 0.03 only at Rs ~53 ksps (Ku) / 126 ksps (Ka) [prev: lit_real_space.md, derived]. Acquisition vs tracking: no
  tracking in TC-LM sources (one-shot per burst); the NCC closes a slow frequency-correction loop per terminal
  (CMD2 corrections) [std]. Our 0.03 = the top corner of the guideline range, 2x Griebel's.
- **Phase noise:** RCST transmit mask in TR 101 545-4 Table 10.1 (e.g. -64 / -70 dBc/Hz at 1 kHz) [prev:
  lit_dvbrcs2.md]; no TC-LM phase tracking published; Griebel uses constant phase [paper].

### 1.4 Published performance
- Griebel 2021 (AWGN, CFO <= 1.5 %, pilot energy not charged): best DA-KS loss vs genie **0.12-0.15 dB** at FER 1e-3
  for QPSK 536-symbol bursts; 0.13 / 0.18 dB at 1e-4 / 1e-5 (burst 3); no RMSE, no CRB, no acquisition / false-alarm
  statistics [paper; prev: lit_ars2021.md 3].
- TR 101 545-4 bench prototype: total implementation loss **~0.5 dB (QPSK 1/3), ~0.6 dB (QPSK 1/2), ~0.96 dB
  (16QAM 5/6)** at PER 1e-5, not split into sync / phase noise / quantisation [std; prev: lit_dvbrcs2.md 1.3].
- Minimum operating Es/N0 (ideal sync): ID 13 -0.80 dB at PER 1e-3 [std; prev]. (Rates: see lit_rates.md.)
- UW detection probability / false alarm: **not found** in any DVB-RCS2 document.

### 1.5 Complexity
- Griebel FPGA IP (Kintex, ~350 MHz, max burst 4096, 8-bit I/Q): 15-19 k FF, 9.8-11.8 k LUT, 35-70 BRAM, 42-58 DSP
  depending on FFT size (4096-16384) and interpolation; interpolation +~2000 FF, +~1000 LUT, +13 DSP, throughput x2-4
  [paper; prev: lit_ars2021.md 2]. Ali et al. 2014 (Virtex-6, pilot-assisted bursts): numbers not seen (abstract
  only) [paper].

### 1.6 Decoder-aided step
- None in the standard, the TR or Griebel. Research: the ESA project "Joint turbo decoding and carrier
  synchronisation" (Advantech Satellite Networks, TurboConcept, Eurecom) found carrier sync "the dominant cause of
  receiver performance degradation" and implemented joint sync + decoding for a DVB-RCS demodulator on FPGA; **no dB
  numbers published** on the page [vendor/agency, https://resilience.esa.int/projects/joint-turbo-decoding-and-carrier-synchronisation].
  The Advantech patents of section 4 are the published version of that line.

### 1.7 Our version vs the real one (est4 C1a / C1b, est5 C15)
| Aspect | Real | Ours | Effect on our competitor |
|---|---|---|---|
| Layout | ID 13: 140 known in 1616 (8.7 %) | 116 in 1140 (10.2 %), same pre / post / P = 20 | equivalent (scaled) |
| CFO | 0.5-3 % (TR), 1.5 % (Griebel) | 3 % | harder for ours (alias at 1/20 enters the range) |
| FFT / search | 2048-4096 + interpolation, peak over all bins, one decode | 8192 + parabolic, window +-0.03, metric-ordered CRC search | **stronger** |
| Phase | arg X(k~), constant | exact LS gain (const) or Kalman (track) | **stronger** (track goes beyond any RCS2 source) |
| Timing / detection | UW detection needed | genie | **stronger** |
| Loss vs genie | 0.12-0.15 dB (paper), 0.5-0.6 dB all-in (bench) | ~0 dB except 1/10 (0.63 dB, alias) | **stronger** except the 1/10 alias floor |
| Code | duo-binary turbo | polar CA-SCL-8 | same for all receivers |

---

## 2. Card: DVB-S2 / DVB-S2X (incl. VL-SNR, superframe, S2X bursts)

### 2.1 Standard, link, deployments
- **Documents.** EN 302 307-1 V1.4.1 (DVB-S2) [std]; EN 302 307-2 V1.3.1 (2021-07, read today) and **V1.4.1
  (2024-08)** (exists, cover only seen in search) [std]; guidelines TR 102 376-1 V1.2.1 (S2) and TR 102 376-2 V1.1.1
  (S2X) [prev: lit_real_space.md].
- **Link:** forward / broadcast, **continuous** TDM (DTH, contribution, VSAT outbound). Burst use exists only as (a)
  DVB-S2X superframe / beam-hopping bursts on the forward link (Annex E formats 5-7), (b) DVB-S2X waveforms on the
  DVB-RCS2 return link (V1.5.1: a burst = one S2X frame, 384-7274 bytes) [std].
- **Deployments.** "Over 1.5 billion DVB receivers deployed" and DVB-S / S2 "used in virtually every country"
  (DVB, May 2019; all DVB standards together) [vendor/std body]; a DVB-S2-only count: not found. S2X products:
  Newtec MDM5000 (first S2X VSAT modem, 2016), Hughes JUPITER (S2X since 2016), iDirect (VL-SNR "for mobile
  applications"), Creonic IP (VL-SNR "below -9 dB") [vendor]. Field use of VL-SNR: not found beyond vendor claims.

### 2.2 Frame structure
- **PLFRAME** [std EN 302 307-1 cl. 5.5]: slot = 90 symbols; PLHEADER = 1 slot = SOF 26 + PLS code 64, **pi/2-BPSK**,
  SOF = 18D2E82 hex; pilots optional (TYPE bit): a **36-symbol block, (1+j)/sqrt2 before scrambling, after every 16
  slots** (first block 16 slots after the PLHEADER; skipped if it would hit the next SOF); everything after the
  PLHEADER is scrambled. Frame lengths QPSK: normal 360 slots (32 400 data symbols), short **90 slots (8 100)**.
  [derived] Short QPSK with pilots: 90 + 8100 + 5 x 36 = **8370 symbols, 270 known = 3.2 %**; without pilots 8190,
  90 known = 1.1 %; pilot period 1476. Dummy PLFRAME: header + 36 slots (3330 symbols) [std].
- **No DVB-S2 / S2X frame is near 1000 symbols.** The shortest is 8190 symbols [derived]; a 1024-symbol segment after a
  PLHEADER contains **no pilot block** (first pilot at data symbol 1441) [derived].
- **S2X VL-SNR** [std EN 302 307-2 V1.3.1 cl. 5.5.2]: XFECFRAME sets of **33 282** (set 1) and **16 686** (set 2)
  symbols incl. header and pilots; PLHEADER 90 + **VL-SNR header 900 symbols** (pi/2-BPSK, not scrambled); extra
  pilots of 32, 34 or 36 symbols in fixed groups; pi/2-BPSK and BPSK-S (spreading factor 2) MODCODs. [derived] Known
  before the data: 990 symbols = 3.0 % of set 1 / 5.9 % of set 2, plus pilots. MathWorks describes the header as an
  896-symbol Walsh-Hadamard sequence + padding [vendor].
- **Superframe (Annex E)** [std]: 612 540 symbols (formats 0-4); SOSF 270 (256-bit Walsh-Hadamard + 14 padding) +
  SFFI 450; SF-pilots type A 36 symbols every 16 CUs (1440); format 2: 36-symbol pilots every 956 (overhead 4.79 %);
  format 3 (bundled short frames): **48-symbol pilots every 1887**, 4.79 %; format 4 (VL-SNR): 0.24 % / 2.67 % with
  SF-pilots, special 90-symbol VL-SNR pilots every 15 slots; format 5 (beam hopping): SF pilots always on, dwell ends
  with a postamble.
- **S2X burst in DVB-RCS2 V1.5.1:** preamble / guard of an S2X burst: **not found** in the parts read (cl. 9.9.4 only
  says the S2X header carries the MODCOD).

### 2.3 Synchronisation in practice
- **Known symbols used for:** SOF / PLHEADER frame sync (differential correlator), coarse CFO (pilot FLL or header
  autocorrelation), fine CFO (pilot blocks), phase (per-pilot-block ML + interpolation); VL-SNR header for frame
  sync at very low SNR [std TR; prev: lit_real_space.md #1-2, #5-6].
- **Estimators:** TR 102 376-1: pilot FLL coarse + Luise-Reggiannini fine on pilot blocks over ~1000 blocks; gr-dvbs2rx:
  M&M-type on the 90-symbol PLHEADER, averaged over frames [prev]. MathWorks VL-SNR example: first-order FLL with a
  balanced quadricorrelator (**up to 20 % of Rs**, residual ~2 %), pilot-aided fine (**up to 3.5 %**, residual
  ~0.03 %), pilot phase estimation (needs residual < 0.05 %, works to ~-8 dB Es/N0); acquisition 9 frames default, 25
  at low Es/N0 [vendor, read today]. Code-aided research: Barbieri-Colavolpe 2007 (3-7 frequency candidates chosen
  by the LDPC syndrome, CBC phase smoother) [prev: lit_dvbrcs2.md].
- **Ranges:** Ku DTH LNB +-5 MHz at 25 Mbaud = **0.2** (multi-frame pull-in ~100 ms); fine range 1/(2 x 1476) =
  **3.4e-4**; DSNG transmit uncertainty < 0.5 % of Rs [prev: lit_real_space.md #1]. VL-SNR burst detector designed
  for **<= 1 %** of Rs; above that a quadricorrelator loop over "several hundred thousand symbols" [prev: #2]. So the
  acquisition range (0.2) is far above ours but only over many frames; the single-frame / tracking range (3.4e-4 to
  1 %) is below ours.
- **Phase noise:** DVB-S2 phase-noise masks and pilot-block ML + interpolation; 16 / 32APSK add an NDA DPLL [prev].

### 2.4 Published performance
- L&R fine estimator RMS **6e-5 at Es/N0 -2 dB, 5.2e-5 at 1 dB** with 1000 pilot blocks; frame acquisition mean 20 ms
  / 99 % in 130 ms at -2 dB; sync losses QPSK 1/2 ~0.1 dB, 8PSK 2/3 ~0.25 dB [std TR; prev: lit_real_space.md #1].
- VL-SNR: detection "reliable at Es/N0 near -10 dB" for <= 1 % CFO (figure values not in text); quadricorrelator at
  -10 dB residual 1e-4 mean / 1e-4 std of Rs in ~50 ms; superframe lock 0.9914 within 5 SOSFs [std TR; prev #2].
- Minimum operating Es/N0: QPSK 1/4 normal frame -2.35 dB (QEF) [std EN 302 307-1 Table 13]; S2X VL-SNR down to
  about -10 dB [prev]; Creonic decoder SNR range -9.6 ... 19.8 dB [vendor]. (MODCOD thresholds: lit_rates.md.)
- Single-frame acquisition probability / false alarm at our SNRs: not found.

### 2.5 Complexity
- No published FPGA resource numbers for a DVB-S2 / S2X synchroniser were found (Creonic briefs give throughput
  only: demodulator up to 100 Msym/s, modulator 250 Msym/s [vendor]). gr-dvbs2rx states that "PL sync algorithms are
  the current performance bottleneck" [prev]. FFT sizes: none prescribed (loop-based chain).

### 2.6 Decoder-aided step
- Not in the standard or guidelines; research only (Barbieri-Colavolpe 2007; ESA / Advantech CBC with LDPC on FPGA,
  no numbers) [prev; agency].

### 2.7 Our version vs the real one (est5 C7)
| Aspect | Real DVB-S2 | Our C7 | Effect |
|---|---|---|---|
| Known symbols in a 1024-data window | 90-symbol header (26 SOF known a priori in ACM / VCM, 90 in CCM); **no pilot block** | 90 header + one 36-symbol block at 512 (126, 0.50 dB) | **stronger** (an extra block, 575-symbol baseline; 90 known as CCM) |
| Header modulation | pi/2-BPSK | treated as known symbols (same energy) | neutral |
| Estimator | multi-frame FLL + L&R over ~1000 blocks | M&M on the header + joint ML in-lobe + CRC lobe search | real chain not applicable to one burst; ours is the best single-burst version |
| CFO | 0.2 over 1e5-1e6 symbols; single frame <= 3.4e-4 ... 1 % | 3 % in one burst | harder for ours |
| Timing / frame sync | SOF correlator | genie | stronger |
Verdict: C7 is a strengthened "DVB-S2 header + one block" receiver, not the deployed DVB-S2 layout. The faithful
single-burst analogue is V4 "S2-header" (lit_real_space.md section 0, rank 5).

---

## 3. Card: ViaSat return-link burst processing (US 7653150, US 8243859)

### 3.1 Documents, link, deployments
- **US 7653150 B2** "Star receiver burst processing", W. H. Thesling, M. Vanderaar; filed 2007-03-02 as a continuation
  of US 09/934,299 (2001; granted as **US 7200185**), priority 2000-08-21; granted 2010-01-26; original assignee
  Efficient Channel Coding (ECC), assigned to Viasat; **expired** (adjusted 2022-10-06) [patent].
- **US 8243859 B2** "Joint frequency and unique word detection", F. Mo, W. H. Thesling, Viasat; filed / priority
  2009-12-04; granted 2012-08-14; active (to ~2031) [patent].
- **Link:** GEO **return** link of a hub-and-spoke (star) MF-TDMA VSAT system (7653150); US 8243859 covers any burst
  receiver: gateway, or a **user terminal in a mesh network** (the claims include terminal-to-terminal) [patent].
- **Deployments:** Viasat bought ECC (closed 1 Dec 2005, ~US$16.5 M + 9 M earn-out); ECC supplied **modem chips for the
  IPSTAR** spot-beam system and DVB-S2 / ACM chips for Viasat's LinkStar roadmap [trade press]. **Which product runs
  the 7653150 / 8243859 algorithms: not found** (no product named in either patent). The "real modems handle 10 %"
  wording in competitors.md is a patent design statement, not a product spec.

### 3.2 Burst structure
- **US 7653150** [patent]: **512 QPSK symbols per burst, no preamble**; optional 8 extra symbols before and after (528);
  a **16-symbol (32-bit) unique word in the middle (midamble)**, the bits being a (32,26) extended-Hamming codeword;
  "twenty-six information bits are dedicated to the UW ... 26 of 26^2 bits, or approximately 3.8 %". FEC: one
  (32,26)^2 turbo product code per burst (1024 coded bits = 512 QPSK symbols). [my reading] The UW is a row of the TPC
  array, i.e. **inside** the 512-symbol coded burst (a 3.8 % rate cost, not extra symbols); the patent does not say
  this explicitly. Known fraction 16 / 512 = **3.1 %** [derived].
- **US 8243859** [patent]: burst = UW symbols + signalling header + payload (e.g. an XFEC frame "under DVB-S2"); UW as
  a preamble (Fig. 2B) or spread through the frame ("spread-amble", Fig. 2C); UW length "relatively short", **not
  stated**.

### 3.3 Synchronisation in practice
- **US 7653150 chain** [patent]: 5x oversampling (2560 samples); timing from five |r|^2 sums and a 5-point sinusoidal
  correlation (blind); energy normalisation; modulation removal by **multiplying the phase by 4** with a lookup
  table (256K x 32 bit; amplitude handling not stated); zero-pad 512 -> **1024-point FFT**; **single** maximum bin s,
  frequency = weighted average over bins s-1, s, s+1, then /4; **phase theta' / 4 from the three bins**; derotation;
  UW correlation at **+-8 symbols x 2 phases = 34 correlations**, the sign / phase of the largest resolves the 90 deg
  ambiguity and gives the time of arrival. Constant phase over the burst.
- **US 8243859 chain** [patent]: N-theta (M-th power) FFT over the burst, **top N peaks (example N = 32 of 1024 bins)**,
  N trial derotations, UW correlation over M timing hypotheses (M x N correlations), joint metric alpha x |freq peak|
  + beta x |UW peak| (alpha, beta found by simulation, stored in LUTs, adapted to SNR), optional "1-theta" preamble
  FFT as a third term; **N increases as SNR decreases** (LUT by link condition).
- **Range:** carrier offset **up to 10 % of Rs** (7653150; = 168.75 kHz at the example 1.6875 Msps [derived]); timing
  +-8 symbols [patent]. 4th-power FFT range +-1/8 of Rs [derived]. 8243859: range not stated.
- **Phase noise:** listed only as a design parameter (7653150) [patent].

### 3.4 Published performance
- 7653150: TPC BER 1e-5 at **Eb/N0 1.4 dB** (-> Es/N0 ~2.6 dB with rate 676/1024 [derived]); "approximately 0.2 dB of
  degradation associated with the disclosed burst-processing algorithm" (simulation); "As the SNR decreases, the
  synchronization techniques fail just below the point where the forward error correcting code fails" [patent].
  Detection / false-alarm rates: not given.
- 8243859: "burst recover error rate below 0.001 %" at **2.5 dB SNR** with N = 32 in a 1024-bin FFT (SNR definition
  not stated) [patent]. Nothing else.

### 3.5 Complexity
- 7653150: 1024-point FFT, 256K x 32-bit LUT, polyphase channeliser up to 16 channels, 34 UW correlations of 16 symbols;
  FPGA / DSP; no gate counts or latency [patent]. 8243859: M x N UW correlations (e.g. N = 32), "UW correlation speed
  may limit M and N"; ASIC / FPGA, no numbers [patent].

### 3.6 Decoder-aided step
- None in either patent: the UW (plus the frequency-peak magnitude) is the hypothesis test, not the decoder.

### 3.7 Our version vs the real one (est5 C9 "ViaSat UW")
| Aspect | Real | Ours (`viasat16`, `nda4uw`, `const`) | Effect |
|---|---|---|---|
| UW | 16 symbols mid-burst, inside the coded 512-symbol burst [my reading] | 16 extra symbols (0.07 dB charged) | ~equal cost |
| Peak selection | 7653150: single peak; 8243859: top-32 + UW joint metric | top-32 (8243859) in +-0.03 + UW joint metric, weight 1 | a merge of the two patents (label it so); top-32 only helps where the UW can rank them, which a 16-symbol UW barely can (expected_est5.md review) |
| Frequency | 1024 FFT, 3-bin weighted average | 8192 FFT, parabolic | slightly stronger |
| **Phase** | **arg of the 4th-power bins / 4 (all 512 symbols), UW only for the quadrant** | **LS gain on the 16 UW symbols** (0.31 / 0.18 / 0.14 rad std at -5 / 0 / +2 dB [derived]) | **weaker than real** above the 4th-power threshold (finding 2) |
| Timing | blind (+-8 symbols) | genie | stronger |
| CFO range | 10 % | 3 % | easier for ours (fewer false peaks) |
| Search | none (UW decides) | metric-ordered CRC search around the pick | stronger |
| Operating point | Es/N0 ~2.6 dB (code rate 0.66) | -5 ... +3 dB | ours far below its design point |

---

## 4. Card: Advantech hybrid DA + NDA estimator (US 7590199) with its joint synchroniser / decoder (US 7593490)

### 4.1 Documents, link, deployments
- **US 7590199 B2** "Hybrid frequency offset estimator", N. S. Alagha; priority 2003-09-12, filed 2004-09-10, granted
  2009-09-15; Advantech Advanced Microwave Technologies (originally via EMS Satellite Networks / EMS Technologies
  Canada); active (to ~2027) [patent]. Cites Rife-Boorstyn 1974, Mengali-Morelli 1997, Cowley 1996 and **N. Alagha,
  L. Erup, "A hybrid data-aided and non-data-aided carrier frequency estimator for short PSK-modulated bursts", 8th
  Int. Workshop on Signal Processing for Space Communications (SPSC), 2003** (full text not found) [patent].
- **US 7593490 B2** "Joint synchronizer and decoder", N. S. Alagha, L. Erup; same priority; granted 2009-09-22
  (continuation US 8331497) [patent].
- **Link:** DVB-RCS (first generation, EN 301 790) **return** link, MF-TDMA bursts, Ku / Ka [patent].
- **Deployments:** Advantech DVB-RCS / S2 hub and remote terminals delivered to the US DoD for in-theatre use via Agile
  Communications (Nov 2010; quantities not given) [trade press]; Advantech "Millennium" hub with DVB-RCS MF-TDMA
  return, QPSK / 8PSK, 128 kbps-12 Mbps bursts [vendor, search snippet only]. Whether these products run the
  patented estimator: **not found**. ESA project with Advantech, TurboConcept, Eurecom on joint turbo decoding and
  carrier sync for DVB-RCS / DVB-S2, VHDL on FPGA (section 1.6) [agency].

### 4.2 Burst structure
- **48 known preamble symbols + 440 unknown payload symbols = 488**, QPSK, rate-1/2 turbo (440 information bits),
  example 64 kBd [patent]. Known fraction 48 / 488 = **9.8 %** [derived]. "Known symbols need not be located with a
  data packet preamble, but may be located anywhere" [patent].

### 4.3 Synchronisation in practice
- **Estimator** [patent US 7590199]: DA branch r c* on the known symbols; NDA branch on "the unknown data symbols (or
  all of the data symbols)": phase x modulation index (4 for QPSK), magnitude transform constant / linear / squared;
  zero padding, low-pass filtering and decimation with D = E x mi (aligns the two spectra); FFT, |.|^2, **log**;
  weights alpha (DA), beta (NDA), summed (alpha or beta = 0 gives pure NDA / DA); iterative peak picking (remove the
  peak and 1-2 neighbours each side, repeat), parabolic interpolation; **3 candidates**. FFT length and weight values:
  **not given**.
- **Candidate choice** [patent US 7593490]: one branch per candidate: frequency correction, phase initialisation,
  decision-aided phase tracking, **partial turbo decoding (1-3 of ~10 iterations; "one or two ... adequate")**; pick
  the branch with the **largest mean |LLR|**; the winner continues with decision-aided phase tracking (systematic
  bits: LLR-weighted hard decisions, sliding average over ~50 symbols; parity bits: conventional DD tracker). CRC use
  or a threshold: not stated.
- **Range:** Ka (30 GHz), 1e-8 RMS x 6 -> **+-1800 Hz = about +-3 % of Rs at 64 kBd** (exactly 2.8 % [derived]) [patent].
  Single-shot per burst; no acquisition / tracking split besides the DD phase tracker.
- **Phase noise:** handled by the decision-aided tracker (50-symbol window) [patent].

### 4.4 Published performance
- **No numbers** in either patent (no RMSE, Eb/N0, PER or loss); only the DVB-RCS packet-loss targets 1e-5 and 1e-7 and
  "operates at a lower SNR than a conventional receiver" [patent]. The SPSC 2003 paper: not found.

### 4.5 Complexity
- Two FFTs + candidate peak search + 3 partial turbo decodes (1-3 iterations each) + full decode of the winner; "system
  complexity grows with" the number of candidates; no operation counts [patent].

### 4.6 Decoder-aided step
- **Yes**: the decoder (mean |LLR| after partial decoding) selects among 3 frequency candidates, and decoder LLRs drive
  the phase tracker [patent US 7593490]. Closest deployed-class design to our blind decoder-in-the-loop idea.

### 4.7 Our version vs the real one (est5 C14 "hyb3")
| Aspect | Real | Ours (`prepost16`, `hyb3`, `const`) | Effect |
|---|---|---|---|
| Known symbols | **48 contiguous preamble** (9.8 %) | 16 + 16 pre / post (32, 0.13 dB) | **different DA spectrum**: one ~1/48 lobe (gates the 4th-power peaks) vs a 1/1040 fringe comb (no gating); finding 1 |
| NDA | payload (or all), magnitude transform 1 / rho / rho^2, decimated | r^4 on the whole burst, log |.| | similar |
| Combining | alpha log|.|^2 + beta log|.|^2 | log|.| + 1.0 log|.| | weights equivalent up to scale; the patent tunes them |
| Candidates | 3, by peak removal | 3 local maxima in +-0.03 | same |
| Choice | mean |LLR| after 1-3 turbo iterations | metric-ordered CRC search + rho over candidates and their lobes | **stronger** (CRC + rho, full decodes, lobes) |
| Phase | DA init + decision-aided tracking (50-symbol window) | constant LS gain on 32 known | weaker under phase noise; ~equal in AWGN |
| CFO | +-2.8 % | +-3 % | ~equal (the patent's design range = ours) |

---

## 5. Contradictions with / corrections to competitors.md

| competitors.md says | Source says | Correction |
|---|---|---|
| C14: "pilot counts (16 + 16) chosen by us, not from the patent" | US 7590199 / 7593490: 48-symbol preamble + 440 payload | the patent gives the layout; our 16 + 16 changes the DA branch qualitatively (finding 1) |
| C14: "3 CFO candidates decided by the decoder" | decided by **mean |LLR| after 1-3 turbo iterations** (US 7593490) | ours decides by CRC + rho: stronger than real; say so |
| C9: "4th-power FFT over the burst, top-32 peaks each tested on the UW" from "US 7653150, US 8243859" | 7653150 = **single peak**, UW for the pi/2 ambiguity and +-8 symbol timing; top-32 is 8243859 (later, different burst format) | label C9 a merge of the two patents |
| C9 "16-symbol midamble unique word (0.07 dB)", "extra" | 7653150: UW = 26 dedicated information bits of the (32,26)^2 TPC, within the 512-symbol burst [my reading] | cost equivalent; note it |
| C9 phase (implicit: `const` on the UW) | phase from the 4th-power spectrum, UW only for the quadrant | ours weaker in phase (finding 2) |
| C9 pros: "handles 10 % CFO in real modems" | a design statement of the patent; no product named; product use not found | write "designed for 10 % of Rs (patent)" |
| C7 deviation: "pilot block every 16 slots ... we give one burst and one block" | first pilot block 1440 data symbols after the header: none in a 1024-symbol window; in ACM only the 26-symbol SOF is known a priori | C7 is denser / stronger than the standard (finding 3) |
| C7: "the most widely deployed satellite standard" | true for the forward broadcast link; DVB-S2 is continuous, not a burst return link; S2X bursts exist only in RCS2 V1.4.1+/V1.5.1 and superframe / beam hopping | add "(forward link)" |
| C1 / C15 cite EN 301 545-2 V1.3.1 | current version V1.5.1 (2026-04); ID 13 unchanged; roll-off 0.20 / 0.10 / 0.05 | update the citation only |
| C1 pros: "phase tracking under phase noise (Kalman)" | no DVB-RCS2 source tracks phase in TC-LM; Griebel uses constant phase | the Kalman is ours, beyond the real system (already noted in lit_ars2021.md) |
| "Not worth": S2X VL-SNR UW "limited to CFO <= 1 % of Rs" | the 1 % is the TR's single-frame burst detector design; the standard chain (FLL) pulls in 20 % over many frames (MathWorks: FLL 20 %, fine 3.5 %) | keep the decision; reword to "single-frame detection designed for <= 1 %" |
| S2X VL-SNR "900 known symbols" | 90 PLHEADER + 900 VL-SNR header = 990 known before the data, in a 16 686 or 33 282-symbol frame | minor |

No contradiction found for the DVB-RCS2 ID 13 layout, the 0.5-3 % range, the Griebel chain, or the ViaSat 10 % / Advantech
3 % design ranges.

---

## 6. Per-source table

| # | Source | Year | Link | Read | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|---|
| 1 | ETSI EN 301 545-2 V1.5.1 (DVB-RCS2 lower layers) | 2026 | [etsi.org](https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/en_30154502v010501p.pdf) | chars 0-100k, 200k-800k of 814k (text reader) | high: current version of the est4 layout source | burst rules, UW, roll-off, S2X return | MF-TDMA return, GEO + NGSO | ID 13 unchanged; roll-off 0.20/0.10/0.05; carrier 1e-8 RMS; S2X bursts 384-7274 bytes |
| 2 | DVB page, DVB-RCS2 lower layer | 2026 | [dvb.org](https://dvb.org/?p=8033) | full | medium | version history | - | V1.4.1 NGSO + superframe signalling; V1.5.1 replaces EN 301 790 |
| 3 | DVB BlueBook C107, RCS2 commercial requirements GSO / NGSO | 2023 | [dvb.org PDF](https://dvb.org/wp-content/uploads/2023/07/C107_Commercial-Requirements-for-the-use-of-DVB-RCS2-in-Geostationary-and-Non-Geostationary-Systems.pdf) | full (text reader) | medium: NGSO requirements, market | requirements list | GSO / NGSO return | no Doppler numbers; roll-off <= 5 %; 128 ksps-2 Msps consumer; VSAT shipments > 1 M/yr (2022) |
| 4 | ESA / SatLabs DVB-RCS market survey news | 2010 | [esa.int](https://resilience.esa.int/?p=9372) | full | low: deployment count | - | DVB-RCS gen 1 | > 370 networks, > 180 000 terminals (mid-2010) |
| 5 | STM adds DVB-RCS2 to SatLink (Via Satellite) | 2012 | [satellitetoday.com](https://www.satellitetoday.com/connectivity/2012/03/21/stm-adds-dvb-rcs2-capability-to-satlink-vsats-hubs-2/) | full | low | - | RCS2 product | first RCS2 vendor claim; 50 Mbit/s TDMA, thousands of VSATs |
| 6 | CSI magazine, "The ultimate interactive satellite standard?" | 2011 | [csimagazine.com](https://csimagazine.com/csi/The-ultimate-interactive-satellite-standard.php) | full | low | - | RCS2 adoption | ~30 organisations; gen-1 strong in gov / mil |
| 7 | ESA project "Joint turbo decoding and carrier synchronisation" (Advantech, TurboConcept, Eurecom) | ~2006-2011 | [esa.int](https://resilience.esa.int/projects/joint-turbo-decoding-and-carrier-synchronisation) | full page | medium: code-aided sync in DVB-RCS practice | joint sync + decoding, CBC | DVB-RCS / S2, FPGA | no numbers |
| 8 | Griebel, Wasenmüller, Wehn, Adv. Radio Sci. 19, 59 | 2021 | [ars.copernicus.org](https://ars.copernicus.org/articles/19/59/2021/) | [prev: lit_ars2021.md, full] | high | DA-KS / DA-PL / NDA FFT + interpolation | RCS2 TC-LM, CFO <= 1.5 % | loss 0.12-0.15 dB; FPGA table |
| 9 | Ali, Wasenmüller, Wehn, CSNDSP / ICSPCS 2014 | 2014 | [dblp](https://dblp.org/rec/html/conf/csndsp/AliWW14) | bibliographic record / abstract snippet | low (not readable) | FPGA carrier sync for RCS2 bursts | Virtex-6 | not seen |
| 10 | ETSI EN 302 307-1 V1.4.1 (DVB-S2) | 2014 | [etsi.org](https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf) | chars 50k-150k (cl. 5.5-6) | high: real pilot layout | PLFRAME | continuous forward | 90-symbol header; 36 pilots / 16 slots; short QPSK 90 slots; QPSK 1/4 -2.35 dB |
| 11 | ETSI EN 302 307-2 V1.3.1 (DVB-S2X) | 2021 | [etsi.org](https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.03.01_60/en_30230702v010301p.pdf) | chars 0-300k of 340k | high: VL-SNR, superframe | framing | continuous / superframe | VL-SNR frames 33 282 / 16 686; header 900; SF 612 540; format 3 pilots 48 / 1887 |
| 12 | ETSI EN 302 307-2 V1.4.1 | 2024 | [etsi.org](https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.04.01_60/en_30230702v010401p.pdf) | search result (cover) only | low | - | - | existence only |
| 13 | MathWorks, DVB-S2X VL-SNR end-to-end example | - | [mathworks.com](https://www.mathworks.com/help/satcom/ug/end-to-end-dvbs2x-simulation-with-rf-impairments-and-corrections-for-vlsnr-frames.html) | full | medium: a working VL-SNR chain | FLL (BQ-FED) + pilot fine + pilot phase | Es/N0 5 dB example, 3 MHz at 26.7 Msym/s | FLL 20 %, fine 3.5 %, phase to ~-8 dB; 9-25 acquisition frames |
| 14 | TR 102 376-1 / -2, gr-dvbs2rx, MathWorks S2 | 2015 | see lit_real_space.md | [prev] | high | S2 / S2X sync guidelines | continuous | L&R 6e-5 at -2 dB; VL-SNR <= 1 % |
| 15 | DVB announcement (via radiotvlink) | 2019 | [radiotvlink.com](https://www.radiotvlink.com/en/delivery/866-dvb-worldwide) | full | low | - | - | > 1.5 billion DVB receivers |
| 16 | iDirect DVB-S2X page; Creonic S2X brief (Aldec) | 2023-2026 | [idirect.net](https://www.idirect.net/technology/dvb-s2x-standard/), [aldec.com](https://www.aldec.com/files/ip_products/PB_Creonic_DVB_S2X_Demodulator.pdf) | full | low | vendor claims | - | VL-SNR "below -9 dB"; SNR -9.6 ... 19.8 dB; no resources |
| 17 | US 7653150 B2 (Thesling, Vanderaar; Viasat) | 2010 | [Google Patents](https://patents.google.com/patent/US7653150B2/en) | full description (one page, not truncated) | high | 4th-power FFT + midamble UW | 512-symbol QPSK burst, 10 % CFO | Eb/N0 1.4 dB @ BER 1e-5; ~0.2 dB loss |
| 18 | US 8243859 B2 (Mo, Thesling; Viasat) | 2012 | [Google Patents](https://patents.google.com/patent/US8243859) | full (two parts) | high | top-N N-theta peaks + UW joint metric, adaptive N | gateway or mesh terminal | < 1e-5 burst error at 2.5 dB, N = 32 / 1024 |
| 19 | ConvergeDigest, Viasat acquires ECC | 2005 | [convergedigest.com](https://convergedigest.com/viasat-acquires-efficient-channel-coding/) | full | low | - | - | ~US$16.5 M; IPSTAR modem chips |
| 20 | US 7590199 B2 (Alagha; Advantech) | 2009 | [Google Patents](https://patents.google.com/patent/US7590199) | full (220k chars, three parts) | high | hybrid DA + NDA log spectra, 3 candidates | DVB-RCS 48 + 440, 64 kBd, +-1800 Hz | no performance numbers |
| 21 | US 7593490 B2 (Alagha, Erup; Advantech) | 2009 | [Google Patents](https://patents.google.com/patent/US7593490) | 200k of 216k chars | high | partial turbo decoding per candidate, mean |LLR| pick, DD phase tracking | same burst | 1-3 of ~10 iterations; 50-symbol phase window; no dB numbers |
| 22 | Satnews, Advantech DVB-RCS/S2 hub to US DoD | 2010 | [satnews.com](https://satnews.com/2010/11/08/advantech-agile-communications-dod-deliveries-done-milsatcom/) | full | low | - | - | delivery, no quantities |
| 23 | Alagha, Erup, SPSC 2003 (hybrid DA / NDA estimator) | 2003 | cited in US 7590199 | **not found** | (would be high) | - | - | - |

---

## 7. Per-component state of the art (these four systems only)

| Our component | What these systems do | Verdict |
|---|---|---|
| Coarse CFO (4th-power FFT fast path) | ViaSat: 4th-power FFT, 2x zero padding, 3-bin interpolation (7653150); top-N peaks with adaptive N (8243859); Advantech: 4th-power + DA log spectra summed; RCS2 NDA bursts: |r| e^{j4 arg r} FFT | **we already use it** (blind_fast 4th-power FFT + parabolic; peak-picked candidates); adaptive N by SNR is close to our gated extras |
| Fine CFO / phase | RCS2: DA-KS FFT + interpolation, constant phase; S2: multi-frame L&R + pilot-block ML; ViaSat: phase = arg(4th-power bin) / 4 | **we already use** refinement + code-aided steps; multi-frame **not applicable** |
| Hypothesis search | ViaSat: N frequency x M timing x 2 phases scored by UW + peak magnitude; Advantech: 3 frequency candidates scored by partial decoding | **we already use it** (CFO x phase grid scored by the SC metric with early stop); Advantech's partial-decode scoring = our list-1 metric checkpoints in spirit |
| Acceptance / false alarm | UW correlation (ViaSat), mean |LLR| (Advantech), CRC in payload; no published false-alarm numbers | **we already use** CRC-16 + rho, stricter than all four |
| Complexity reduction | interpolation instead of bigger FFTs (Griebel); adapt N to SNR (8243859); 1-3 partial turbo iterations per candidate (7593490) | **already used** (s4_interp, early-stop checkpoints) |
| ML gates | none | not applicable |

---

## 8. Comparability

All four systems differ from our setting: turbo / TPC / LDPC codes, 488-8370-symbol frames (none at 1024 with our
code), roll-off 0.05-0.35 (ours 0.25), and operating points of Es/N0 -0.8 dB (RCS2 QPSK 1/3) to +2.6 dB (ViaSat TPC),
or multi-frame acquisition (DVB-S2 / S2X). Their dB losses (0.1-0.6 dB) describe their setting and must not be quoted as
what their layout would lose at our -5 ... +3 dB with |f| <= 0.03. None of them publishes a single-burst acquisition
probability or false-alarm rate at our SNRs.

---

## Reference entries

### EN 301 545-2 V1.5.1. ETSI EN 301 545-2 V1.5.1 (2026-04), Digital Video Broadcasting (DVB); Second Generation DVB Interactive Satellite System (DVB-RCS2); Part 2: Lower Layers for Satellite standard
- Link: https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/en_30154502v010501p.pdf   - Type: standard   - Read depth: partial (chars 0-100k and 200k-800k of 814k via text reader; tables flattened)
#### What it does
Current RCS2 lower layers: TC-LM burst rules (preamble typical, evenly spread pilot blocks, UW = pre + pilot block + post, known symbols in the payload constellation), roll-off 0.20 / 0.10 / 0.05, carrier accuracy 1e-8 RMS, burst start 0.5 symbol, symbol clock 20 ppm; NGSO support; DVB-S2X waveforms on the return link (TDMA bursts of one S2X frame, 384-7274 bytes, or continuous). Annex A ID 13 unchanged (1616, QPSK 1/3, 32 / 31, P = 20, 77 pilots).
#### What we take
Citation update for est4 `rcs13` (no layout change); the S2X-in-TDMA option as the only real "DVB-S2X burst".

### DVB C107. DVB BlueBook C107, "Commercial Requirements for the use of DVB-RCS2 in Geostationary and Non-Geostationary Systems", July 2023
- Link: https://dvb.org/wp-content/uploads/2023/07/C107_Commercial-Requirements-for-the-use-of-DVB-RCS2-in-Geostationary-and-Non-Geostationary-Systems.pdf   - Type: standard (requirements)   - Read depth: full via text reader
#### What it does
RCS2 requirements for NGSO: higher Doppler (no number), operation without GNSS, roll-off <= 5 %, up to 500 Msym/s; market: VSAT shipments > 1 M per year (2022).
#### What we take
Context: RCS2 is being extended to LEO / MEO, where per-burst Doppler residuals larger than the GEO budget are expected; no numbers to adopt.

### DVB-RCS2 page. DVB Project, "DVB-RCS2 lower layer satellite specification" web page, accessed 2026-11-15
- Link: https://dvb.org/?p=8033   - Type: standard body web page   - Read depth: full
#### What it does
Version history (V1.4.1 NGSO + superframe signalling, V1.5.1 published 2026-04-24) and "balanced use of preamble, postamble and pilots" so that sync sensitivity matches decoding sensitivity.
#### What we take
Version facts only.

### SatLabs 2010. ESA news, "SatLabs survey: over 370 DVB-RCS networks, 180,000 terminals" (mid-2010)
- Link: https://resilience.esa.int/?p=9372   - Type: agency news   - Read depth: full
#### What it does / what we take
Deployment scale of first-generation DVB-RCS (the predecessor RCS2 replaces). Card 1.1 only.

### STM 2012. Via Satellite, "STM adds DVB-RCS2 capability to SatLink VSATs, hubs", 21 March 2012
- Link: https://www.satellitetoday.com/connectivity/2012/03/21/stm-adds-dvb-rcs2-capability-to-satlink-vsats-hubs-2/   - Type: trade press   - Read depth: full
#### What it does / what we take
First commercial RCS2 product claim. Card 1.1 only.

### CSI 2011. CSI Magazine, "The ultimate interactive satellite standard?", May-June 2011
- Link: https://csimagazine.com/csi/The-ultimate-interactive-satellite-standard.php   - Type: trade press   - Read depth: full
#### What it does / what we take
Operator / vendor views on RCS2 adoption; gen-1 strength in government / military. Card 1.1 only.

### ESA JTDCS. ESA ARTES project "Joint Turbo Decoding and Carrier Synchronisation" (Advantech Satellite Networks, TurboConcept, Eurecom)
- Link: https://resilience.esa.int/projects/joint-turbo-decoding-and-carrier-synchronisation   - Type: agency project page   - Read depth: full page
#### What it does
Joint synchronisation and decoding for DVB-RCS (QPSK, BPSK, 8PSK) and CBC with LDPC for DVB-S2, VHDL on FPGA; carrier sync named the dominant degradation; no dB numbers.
#### What we take
Evidence that decoder-aided burst sync was industrialised for DVB-RCS (supports the hyb3 / C14 framing).

### EN 302 307-1. ETSI EN 302 307-1 V1.4.1 (2014-11), DVB-S2 Part 1
- Link: https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf   - Type: standard   - Read depth: partial (chars 50k-150k: cl. 5.5-6)
#### What it does
PLFRAME: 90-symbol pi/2-BPSK PLHEADER (SOF 26 + PLS 64), 90-symbol slots, optional 36-symbol pilot blocks every 16 slots, scrambling after the header; QPSK short frame 90 slots; roll-off 0.35 / 0.25 / 0.20; QPSK 1/4 -2.35 dB at QEF.
#### What we take
The real pilot spacing (1476) behind finding 3: a 1024-symbol window after the header has no pilot block; C7 is denser than the standard.

### EN 302 307-2 V1.3.1. ETSI EN 302 307-2 V1.3.1 (2021-07), DVB-S2X Part 2
- Link: https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.03.01_60/en_30230702v010301p.pdf   - Type: standard   - Read depth: partial (chars 0-300k of 340k)
#### What it does
VL-SNR frames (33 282 / 16 686 symbols, 900-symbol VL-SNR header, extra 32 / 34 / 36-symbol pilots), Annex E superframes (612 540 symbols, SOSF 270 + SFFI 450, SF-pilots 36 / 1440; format 2: 36 / 956; format 3: 48 / 1887; format 4 VL-SNR; format 5 beam hopping).
#### What we take
Card 2 structure facts; no change to C7 beyond the relabelling.

### EN 302 307-2 V1.4.1. ETSI EN 302 307-2 V1.4.1 (2024-08), DVB-S2X
- Link: https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.04.01_60/en_30230702v010401p.pdf   - Type: standard   - Read depth: search result (cover) only
#### What it does / what we take
Latest S2X edition; content not read. Version fact only.

### MathWorks VL-SNR. MathWorks Satellite Communications Toolbox, "End-to-End DVB-S2X Simulation with RF Impairments and Corrections for VL-SNR Frames", accessed 2026-11-15
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-dvbs2x-simulation-with-rf-impairments-and-corrections-for-vlsnr-frames.html   - Type: vendor reference example   - Read depth: full
#### What it does
VL-SNR receiver: Gardner timing, BQ-FED FLL (20 % of Rs -> ~2 %), pilot fine estimator (3.5 % -> 0.03 %), pilot phase (to ~-8 dB), 9-25 acquisition frames; one run at Es/N0 5 dB, 3 MHz CFO, PER 0.
#### What we take
The multi-frame acquisition / tracking ranges of a working S2X chain (card 2.3); not a single-burst competitor.

### DVB 2019. DVB announcement, May 2019 (as reported by radiotvlink.com): "over 1.5 billion DVB receivers deployed"
- Link: https://www.radiotvlink.com/en/delivery/866-dvb-worldwide   - Type: standard body announcement (secondary)   - Read depth: full
#### What it does / what we take
Deployment scale (all DVB standards). Card 2.1 only.

### iDirect S2X / Creonic. iDirect "DVB-S2X standard" page; Creonic DVB-S2X transmitter / receiver product brief (2023)
- Link: https://www.idirect.net/technology/dvb-s2x-standard/ ; https://www.aldec.com/files/ip_products/PB_Creonic_DVB_S2X_Demodulator.pdf   - Type: vendor   - Read depth: full
#### What it does / what we take
Vendor claims of VL-SNR support ("below -9 dB", SNR -9.6 ... 19.8 dB), no sync numbers or resources. Card 2.1 / 2.4 only.

### Thesling 2010. W. H. Thesling, M. Vanderaar (Efficient Channel Coding, assigned to Viasat), "Star receiver burst processing", US 7653150 B2, 26 Jan 2010 (continuation of US 7200185; priority 21 Aug 2000; expired)
- Link: https://patents.google.com/patent/US7653150B2/en   - Type: patent   - Read depth: full description
#### What it does
512-symbol QPSK return burst, no preamble, 16-symbol midamble UW (a (32,26) Hamming codeword, 26 dedicated TPC information bits), blind timing (5x oversampling), phase x 4 LUT, 1024-point FFT, single peak + 3-bin average, frequency / 4 and phase / 4 from the bins, UW correlation over +-8 symbols x 2 phases; CFO up to 10 % of Rs; TPC (32,26)^2 at Eb/N0 1.4 dB (BER 1e-5); ~0.2 dB sync degradation; sync fails just below the FEC threshold.
#### What we take
Basis of est5 C9; corrections: single peak (top-32 is US 8243859), phase from the 4th-power bins (finding 2), UW inside the coded burst [my reading].

### Mo 2012. F. Mo, W. H. Thesling (Viasat), "Joint frequency and unique word detection", US 8243859 B2, 14 Aug 2012
- Link: https://patents.google.com/patent/US8243859   - Type: patent   - Read depth: full (two parts)
#### What it does
N-theta FFT, top-N peaks (32 of 1024), N trial derotations x M UW positions, joint alpha / beta metric, optional 1-theta preamble FFT, N adapted to SNR by LUT; gateway or mesh terminal; burst error < 1e-5 at 2.5 dB.
#### What we take
The top-32 + UW joint metric of est5 C9 (`nda4uw`); the "adapt N to SNR" idea matches our gated extras.

### ECC 2005. Converge Digest, "ViaSat acquires Efficient Channel Coding", 30 Nov 2005
- Link: https://convergedigest.com/viasat-acquires-efficient-channel-coding/   - Type: trade press   - Read depth: full
#### What it does / what we take
Acquisition facts (US$16.5 M + 9 M; IPSTAR modem chips). Card 3.1 only; no product tie to the patents found.

### Alagha 2009a. N. S. Alagha (Advantech Advanced Microwave Technologies), "Hybrid frequency offset estimator", US 7590199 B2, 15 Sep 2009 (priority 12 Sep 2003)
- Link: https://patents.google.com/patent/US7590199   - Type: patent   - Read depth: full (three parts)
#### What it does
DVB-RCS burst (48-symbol preamble + 440 payload, QPSK, rate-1/2 turbo, 64 kBd, +-1800 Hz = +-2.8 % of Rs); DA spectrum of the known symbols and NDA (phase x 4, magnitude 1 / rho / rho^2) spectrum, decimated to the same grid, log |.|^2, weighted sum, 3 candidates by peak removal + parabolic interpolation; no performance numbers. Cites Alagha-Erup SPSC 2003 (not found).
#### What we take
Basis of est5 C14 hyb3; correction: the patent's layout is a 48-symbol preamble (finding 1; proposed "hyb3-pre48").

### Alagha 2009b. N. S. Alagha, L. Erup (Advantech), "Joint synchronizer and decoder", US 7593490 B2, 22 Sep 2009 (continuation US 8331497)
- Link: https://patents.google.com/patent/US7593490   - Type: patent   - Read depth: 200k of 216k characters
#### What it does
Per frequency candidate: derotation, phase initialisation, decision-aided phase tracking, partial turbo decoding (1-3 of ~10 iterations); pick the largest mean |LLR|; LLR-weighted decision-directed phase tracking with a ~50-symbol sliding window. No dB numbers.
#### What we take
The real candidate selector of C14 (ours, CRC + rho, is stronger); the "partial decode as candidate score" idea is what our list-1 metric checkpoints already do.

### Advantech DoD 2010. Satnews, "Advantech / Agile Communications: DoD deliveries done", 8 Nov 2010
- Link: https://satnews.com/2010/11/08/advantech-agile-communications-dod-deliveries-done-milsatcom/   - Type: trade press   - Read depth: full
#### What it does / what we take
Deployment evidence for Advantech DVB-RCS / S2 hubs and terminals (no quantities). Card 4.1 only.

## Sources
- https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/en_30154502v010501p.pdf (read via https://r.jina.ai/ + the URL)
- https://dvb.org/?p=8033
- https://dvb.org/wp-content/uploads/2023/07/C107_Commercial-Requirements-for-the-use-of-DVB-RCS2-in-Geostationary-and-Non-Geostationary-Systems.pdf
- https://resilience.esa.int/?p=9372
- https://www.satellitetoday.com/connectivity/2012/03/21/stm-adds-dvb-rcs2-capability-to-satlink-vsats-hubs-2/
- https://csimagazine.com/csi/The-ultimate-interactive-satellite-standard.php
- https://resilience.esa.int/projects/joint-turbo-decoding-and-carrier-synchronisation
- https://dblp.org/rec/html/conf/csndsp/AliWW14
- https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf
- https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.03.01_60/en_30230702v010301p.pdf
- https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.04.01_60/en_30230702v010401p.pdf
- https://www.mathworks.com/help/satcom/ug/end-to-end-dvbs2x-simulation-with-rf-impairments-and-corrections-for-vlsnr-frames.html
- https://www.radiotvlink.com/en/delivery/866-dvb-worldwide
- https://www.idirect.net/technology/dvb-s2x-standard/
- https://www.aldec.com/files/ip_products/PB_Creonic_DVB_S2X_Demodulator.pdf
- https://patents.google.com/patent/US7653150B2/en
- https://patents.google.com/patent/US8243859
- https://convergedigest.com/viasat-acquires-efficient-channel-coding/
- https://patents.google.com/patent/US7590199
- https://patents.google.com/patent/US7593490
- https://satnews.com/2010/11/08/advantech-agile-communications-dod-deliveries-done-milsatcom/
- Project files: competitors.md, expected_est5.md, lit_ars2021.md, lit_dvbrcs2.md, lit_real_space.md, lit_real_leo.md,
  lit_real_military.md, est4/estimators.py (nda4uw, hyb3, mmml), est4/common.py, est4/run_bler.py.
