# Competitor "cards": NB-IoT / LTE uplink, IEEE 802.11 (legacy + 802.11ad/ay SC), MIL-STD-188-110C App C/D, 400ZR sparse pilots (2026-11-15)

Literature scout report. No simulations were run, no code or REFERENCES.md edited. This fills gaps left by
`lit_real_terrestrial.md`, `lit_real_wlan.md`, `lit_real_military.md`, `competitors.md`, `expected_est5.md`; what is solid
there is not repeated, only referenced. Code rates / MCS are out of scope (see `lit_rates.md`).

Conventions. f = CFO / symbol (or sample / chip) rate, in cycles/symbol; our range is |f| <= 0.03. Every number is tagged
**[std]** (standard or 3GPP/IEEE/ITU document), **[paper]**, **[vendor]** (vendor doc, datasheet, app note, open
implementation), **[patent]**, or **[derived]** (my arithmetic from tagged numbers). "Not found" means searched and not
found; "not read" means the source exists but could not be opened (PDF parsing failed for several 3GPP / OIF / IEEE PDFs).

---

## 0. Short summary and contradictions with competitors.md

| System | One-line verdict |
|---|---|
| C10 NB-IoT / LTE DMRS 1/7 | **Single-tone NPUSCH format 1 is exactly "1 known symbol per 7 single-carrier symbols"** (pi/2-BPSK / pi/4-QPSK, DMRS in symbol 3 of 7 at 15 kHz, symbol 4 at 3.75 kHz), so C10 is a faithful model of single-tone NB-IoT, not only "the pilot density". The deployed eNB estimator (Qualcomm FSM, Chakrapani 2019) is an FFT over the DMRS phases with quadratic interpolation, **searched only over +-250 Hz = +-0.018 cycles/symbol at 15 kHz** [derived], i.e. narrower than our 0.03; its theoretical DMRS range is +-1 kHz = +-0.071. No decoder-aided step. Terrestrial CFO after DL lock is ~0.013 cycles/symbol; NTN without GNSS ~0.04 (15 kHz) to 0.17 (3.75 kHz) [derived]. |
| C12 Wi-Fi-inspired | Legacy L-STF/L-LTF = 160 + 160 samples (coarse lag 16, range 0.031 cycles/sample; fine lag 64, range 0.0078). Design CFO +-40 ppm relative = 0.0117 cycles/sample at 5.8 GHz [derived]. An open FPGA implementation (OpenOFDM) uses **only the lag-16 coarse stage over 64 samples and skips the fine stage**. 802.11ad SC is a different structure (Golay, lag 128, range 0.0039 cycles/chip; Ga64 guard interval every 512 chips = 12.5 % known). |
| C13 MIL-110-inspired | App C: 287-symbol preamble (184 sync/Doppler + 103 rate/interleaver incl. a 31-symbol mini-probe), then frames of 256 data + 31-symbol mini-probe, +72 known every 72 frames (steady state 11.1 % known) [std]. +-75 Hz at 2400 Bd = 0.031 [std/derived], tested only at 30 dB SNR; low-SNR acquisition "not yet standardized" [std]. App D (3 kHz) known fraction per WID: 50 % (WID 1-2), 25 % (3-4), 11.1 % (5-10, 13), 6.25 % (11-12) [std/derived]. Superseded by MIL-STD-188-110D (29 Dec 2017). Published tracking: probe/equaliser-driven loops (MathWorks 110A: cross-spectrum phase fit + PI loop + NCO), no one-shot estimator published for App C/D. |
| C11 400ZR sparse pilots | 1 QPSK pilot per 32 symbols, 11-symbol training sequence per 3712-symbol sub-frame, +-1.8 GHz at 59.84375 GBd = 0.0301 (datasheets +-3.6 GHz = 0.060) - already solid in lit_real_terrestrial.md. New: a 2025 paper states the OIF 400ZR frame uses the **training sequences for frame sync and initial frequency-offset locking** and the pilots for phase tracking; 800G LR moved the pilot interval from 32 to 64. |

**Contradictions / corrections to competitors.md (and its sources):**
1. **C12 "(also 802.11ad single carrier)" is misleading.** 802.11ad SC does not use the lag-16 / lag-64 pair: its STF is 16 x Ga128 + (-Ga128) (2176 chips) with a lag-128 autocorrelation (max tolerable CFO 114.58 ppm = +-1/256 = 0.0039 cycles/chip [paper / derived]), and its in-payload known symbols are a 64-chip Golay guard interval per 512-chip block. Our C12 models only legacy OFDM Wi-Fi (L-STF/L-LTF). Suggest dropping "(also 802.11ad SC)" or adding a separate note.
2. **C12 lobe count.** competitors.md says "CRC search over the +-1 fine lobes"; `expected_est5.md` (as implemented) uses LOBE_N = 4 lobes each side at 1/64 spacing. One of the two should be corrected.
3. **C12 known length.** Real legacy Wi-Fi spends 320 known samples (L-STF 160 + L-LTF 160 at 20 MS/s) [std via vendor]; our C12 uses 128 (0.51 dB). Charged the real way, the preamble would cost 10 log10(1344/1024) = 1.18 dB [derived]. Our C12 is therefore lighter in energy but has fewer known symbols for estimation and reuses the period-16 sequence for the lag-64 stage (the real LTF is a separate 64-periodic sequence).
4. **C10 "we keep only the pilot density".** For single-tone NPUSCH this understates the match: one single-carrier symbol per SC-FDMA symbol (plus CP), 1 DMRS in 7, pi/2-BPSK / pi/4-QPSK [paper]. For multi-tone NPUSCH and LTE PUSCH, however, the DMRS is a block of M known DFT-spread samples every 7 symbols (e.g. 12 known in 84 for 12 tones [derived]), which C10 does not model. Also: competitors.md gives 0.69 dB; the implemented layout (1195 symbols) is 0.67 dB [derived].
5. **C10 range.** The real deployed NB-IoT search window (+-250 Hz at 15 kHz = 0.018 cycles/symbol) does not cover our 0.03; C10's +-0.071 window is the theoretical DMRS range, i.e. a widened (stronger) version of the real receiver.
6. **C13 known-symbol count.** Real App C for 1024 data symbols carries 287 + 4 x 31 = 411 known symbols (1.47 dB charged) [derived from std], not 308 (1.14 dB): our 184-symbol preamble omits the 103-symbol rate/interleaver section (72 symbols, one of 30 D-value sets, + a 31-symbol mini-probe). This makes our C13 ~0.33 dB more favourable than the real waveform in AWGN. Also: in 110C, App C is called "Medium data rate" (3200-9600 bps, 12800 bps uncoded); the current revision is 110D (2017).
7. **C11 / lit_real_terrestrial "the coarse FOE in 400ZR must be blind".** Wang et al. 2025 (COL) state the 400ZR frame uses its training sequences for initial frequency-offset locking. The OIF IA text itself could not be read, so this is a paper statement, not verified against the IA; the C11 competitor (blind 4th-power coarse + pilots + lobe search) remains a reasonable "-inspired" design, but the deviation table should say the real coarse stage is likely TS-aided or vendor-specific, not necessarily blind. Also: competitors.md says 32 pilots (0.13 dB); the implemented zr32 layout has 33 pilots, 1057 symbols (0.14 dB).

---

## 1. Card C10: NB-IoT NPUSCH / LTE PUSCH DMRS, with NTN Rel-17/18

### 1.1 Standard, version, deployments
- 3GPP TS 36.211 clause 10.1 (NB-IoT uplink, NPUSCH, DMRS in 10.1.4; symbol positions in Table 10.1.4.2-1) [std; the
  itecspec mirror page was truncated, positions confirmed through MathWorks and Chakrapani]. Rel-13 onward; NTN in
  Rel-17 (IoT-NTN), enhancements in Rel-18 (HARQ-feedback disabling, GNSS operation in connected mode) [std drafts via search].
- UE frequency error: TS 36.101 clause 6.5.1F, cat NB1/NB2: +-0.1 ppm above 1 GHz, +-0.2 ppm at or below 1 GHz, relative to
  the received DL carrier, measured over one slot (0.5 ms at 15 kHz; 2 ms minus the 2304 Ts gap at 3.75 kHz); test limit
  +-(0.1 or 0.2 ppm + 15 Hz) [std, via TS 36.521-1 mirror snippet only]. LTE: +-0.1 ppm over one slot [std, quoted in a
  patent snippet].
- Deployments: GSMA counted 32 NB-IoT networks launched by early 2018 [vendor/press, RCR Wireless / GSMA]; chipsets
  Qualcomm 9205 / 212S (satellite-capable) [vendor, CNX]; NTN: Skylo GEO NB-IoT service at Rel-17 level, Sony ALT1250
  certified, Soracom phased commercial launch July 2024; Sateliot LEO constellation on Rel-17 NB-IoT NTN; u-blox UBX-S52,
  Telit Cinterion, Quectel Rel-17 NTN modules [press, RCR Wireless, Counterpoint, everythingrf]. eNB: Qualcomm FSM small
  cell (Chakrapani 2019) [paper].

### 1.2 Frame / pilot structure
| Item | Value | Tag |
|---|---|---|
| NPUSCH format 1 (data) | 7 SC-FDMA symbols per slot, **1 DMRS symbol per slot** (middle symbol) | [paper: Wang primer; Chakrapani] |
| DMRS position, format 1 | symbol 3 (15 kHz), symbol 4 (3.75 kHz) | [vendor: MathWorks, quoting TS 36.211] |
| NPUSCH format 2 (HARQ-ACK) | 3 DMRS per slot: symbols 2, 3, 4 (15 kHz); 0, 1, 2 (3.75 kHz) | [paper: Chakrapani; std fragment via itecspec snippet] |
| Single tone | 15 kHz (0.5 ms slot) or 3.75 kHz (2 ms slot); pi/2-BPSK or pi/4-QPSK with phase continuity | [paper: primer] |
| Multi-tone | 3, 6, 12 tones at 15 kHz (format 1 only) | [paper: primer] |
| Known fraction | format 1: 1/7 = 14.3 % of the SC-FDMA symbols; format 2: 3/7 | [derived] |
| Single-tone symbol rate | 15 kHz: 7 symbols / 0.5 ms = 14.0 ksym/s (71.4 us incl. CP); 3.75 kHz: (2000 - 75 us) / 7 = 275 us -> 3.64 ksym/s | [derived] |
| LTE PUSCH | same slot structure as NPUSCH format 1 (1 DMRS SC-FDMA symbol per 0.5 ms slot, 2 per subframe), DMRS spans all M allocated subcarriers | [paper: primer; patent US8605799] |
| DMRS sequence | definition in TS 36.211 10.1.4.1 | **not read** (mirror truncated) |

**What carries over to our single carrier:** single-tone NPUSCH is a single-carrier stream of one complex symbol per
SC-FDMA symbol, so C10's "1 pilot per 7 symbols" is structurally exact (apart from the CP). **What does not:** for
multi-tone NPUSCH / LTE PUSCH, the DMRS is a contiguous block of M known samples (after DFT spreading) every 7 SC-FDMA
symbols; the single-carrier analogue would be a block-pilot layout (block period about 7M samples, alias spacing about
1/(7M) cycles/sample, e.g. 1/84 for 12 tones [derived]) close to our CCSDS / DVB-S2 block competitors, not C10.

### 1.3 Synchronization in practice
- **What the DMRS is used for:** channel estimation and frequency-offset estimation (and timing refinement in MathWorks)
  [paper: Chakrapani; vendor: MathWorks NPUSCH BLER example]. Initial timing comes from NPRACH; CFO is mostly removed by
  the UE locking to the downlink (+-0.1/0.2 ppm), see above.
- **Deployed estimator (Qualcomm FSM, Chakrapani 2019) [paper]:** pilot-only (DMRS symbol 3), averaged over tones; per block
  of B = 8 ms (multi-tone) or 32 ms (single-tone); 256-point FFT on the DMRS phase sequence (pilots every 0.5 ms), squared
  magnitude summed over Rx antennas, peak + quadratic interpolation; resolution ~7.8 Hz; **search limited to
  [-250, +250] Hz**. Format 2 reuses the format-1 estimate. Not iterative, not decoder-aided.
- **Range:** DMRS spacing 0.5 ms -> unambiguous +-1 kHz [patent: US8605799 (Ericsson), USPTO 12040918 snippet].
  Normalised, single tone 15 kHz: +-1 kHz -> **+-0.071 cycles/symbol**; Qualcomm search +-250 Hz -> **+-0.018**;
  3.75 kHz: DMRS every 2 ms -> +-250 Hz -> +-0.069 cycles/symbol [derived]. LTE PUSCH: +-1 kHz = 0.067 of the 15 kHz SCS;
  high-speed train needs +-1.7 kHz; Ericsson resolves wrap-around by combining PUSCH (0.5 ms) and PUCCH (~4/14 ms)
  reference-symbol lags via a hypothesis table (ideal limit 7 kHz) [patent US8605799].
- **Design CFO (terrestrial):** +-0.2 ppm at 900 MHz = +-180 Hz -> 0.013 cycles/symbol (15 kHz) or 0.049 (3.75 kHz) [derived
  from std]. Compare our 0.03: terrestrial NB-IoT at 15 kHz is ~2.3x smaller, 3.75 kHz ~1.6x larger relative to the symbol
  rate (but the 3.75 kHz DMRS range 0.069 still covers it).
- **NTN (Rel-17/18):** UE pre-compensates timing and Doppler from its GNSS position and the satellite ephemeris
  [paper: Liberg et al. 2020; arXiv 2601.04882]; pre-compensation is updated per uplink segment (RRC
  npusch-TxDuration-r17), with uplink compensation gaps [std: RAN1 #110 draft CR, RAN4 LS on TDD pre-compensation]; NR
  NTN draft requirement: +-0.1 ppm over 1 ms relative to the ideally pre-compensated carrier [std draft R4-2216641, not
  confirmed final]. Raw LEO 600 km Doppler: up to 24 ppm with the 10 deg elevation limit [paper: Liberg 2020] or 43 kHz /
  21 ppm at 2 GHz [patent: Ericsson US12136966]; Doppler rate up to ~500 Hz/s [patent US12136966]; delay rate 24 us/s
  [paper: Liberg]. Residual at NPRACH without GNSS: about +-600 Hz (99 %) [paper: Chougrani 2021] -> 0.043 (15 kHz) /
  0.165 (3.75 kHz, beyond the DMRS range) cycles/symbol [derived]. With GNSS (+-0.1 ppm at 2 GHz = 200 Hz): 0.014 / 0.055
  [derived]. A 1024-symbol single-tone burst lasts 73 ms (15 kHz) or 282 ms (3.75 kHz); 500 Hz/s of uncompensated Doppler
  rate would move the CFO by 37 Hz (0.0026 cycles/symbol) or 141 Hz (0.039) over it [derived] - this is why Rel-17
  re-pre-compensates per segment. Rel-18 NR NTN added PUSCH DMRS bundling (phase continuity for joint channel
  estimation) [paper: arXiv 2601.04882]; **no NB-IoT DMRS change for NTN was found.**
- **Phase noise / time variation:** channel estimate averaged over the block assuming slow fading (1 Hz Doppler, coherence
  ~423 ms) [paper: Chakrapani]; format 2 averages its 3 pilots per slot.

### 1.4 Published sync performance
- NPUSCH format 1, 15 kHz, 70 % throughput (TS 36.104 requirement vs Qualcomm sim / test bench) [paper: Chakrapani]:
  1 tone, 1 rep: 3GPP -2.1 dB, sim -4.5, test -4.2; 1 tone, 16 reps: -8.8 / -11.2 / -11.0; 12 tones, 2 reps: -0.7 / -7.0 /
  -3.5. Test bench 0.2-4 dB worse than simulation; fixed-point loss < 0.5 dB. No loss vs ideal sync is reported.
- NPUSCH format 2: 1 rep 6.3 / 3.2 / 4.4 dB; 64 reps -9.5 / -11.8 / -10.6 dB (ACK miss <= 1 %, DTX-to-ACK <= 1 %).
- NPRACH: 3GPP Pd >= 99 %, Pfa <= 0.1 % [paper, quoting std]; max estimable NPRACH offset ~+-357 Hz.
- MathWorks NPUSCH BLER example: no CFO modelled, perfect channel estimation by default [vendor].
- **CFO RMSE vs SNR for NPUSCH DMRS: not found.** NB-IoT LEO uplink with added DMRS (Sensors 2022, PMC9502177): BLER
  improves with denser DMRS, residual compensation range ~950 Hz [paper, search snippet only; page blocked].

### 1.5 Complexity
- One 256-point FFT per 8 / 32 ms block + quadratic interpolation [paper]; no gate / cycle numbers. Shared wideband FFT
  with LTE; fixed point < 0.5 dB loss [paper].

### 1.6 Decoder-aided step
- None in the published eNB receiver (Chakrapani: "not iterative"); turbo decoding per repetition group + CRC. Format 2 uses
  a one-shot pilot + data hypothesis test [paper].

### 1.7 Our C10 vs the real system
| Aspect | Real (single-tone NPUSCH format 1) | Our C10 (dmrs7) | Effect |
|---|---|---|---|
| Layout | 1 DMRS in 7 symbols, CP, pi/2-BPSK / pi/4-QPSK | 1 pilot in 7, 171 pilots in 1195 symbols, QPSK data | equal density, structurally exact |
| CFO window | +-250 Hz searched (0.018 cycles/symbol at 15 kHz) | full +-0.071 (no aliases inside +-0.03) | ours stronger (needed for 0.03) |
| Estimator | FFT over DMRS phases per 32 ms block (64 DMRS) + quadratic interpolation | R-B over all 171 pilots + phase interpolation / Kalman | same family; ours uses 2.7x more pilots coherently |
| Code / repetition | turbo, up to 128 repetitions, HARQ | polar N = 2048 + CRC-16, one burst | not comparable in coding |
| CFO budget | 0.013 (terrestrial), 0.014-0.043 (NTN, 15 kHz) | uniform +-0.03 | ours harsher than terrestrial, similar to NTN residuals |
| Overall | - | - | **C10 is a stronger-than-deployed version** (wider window, more pilots per estimate); fair as an upper bound for DMRS-style receivers. |

---

## 2. Card C12: IEEE 802.11 legacy STF/LTF, plus 802.11ad / ay single carrier

### 2.1 Standard, version, deployments
- IEEE 802.11-2020 (OFDM PHY, clause 17; legacy preamble also in HT/VHT/HE); 802.11ad-2012 (DMG, now in 802.11-2020
  clause 20); 802.11ay-2021 (EDMG). Standard texts paywalled, **not read**; numbers from MathWorks / Keysight / papers.
- Deployments: every Wi-Fi chip runs the legacy preamble; 60 GHz: Facebook/Meta **Terragraph** uses the 802.11ad single-
  carrier PHY (MCS 1-12, pi/2-BPSK/QPSK/16QAM, 385-4620 Mb/s, 2.16 GHz channels) on Qualcomm QCA6438 / QCA6428 (pre-11ay)
  chipsets [vendor: Terragraph docs; press: RCR Wireless, Tom's Hardware].
- Frequency tolerance: +-20 ppm (802.11a/j/p, 5 GHz), +-25 ppm (802.11b/g, 2.4 GHz); carrier and symbol clock from one
  oscillator [vendor: Keysight 89600 help]. 802.11ad: +-20 ppm [vendor: rfwireless-world, in lit_real_wlan.md].

### 2.2 Frame / training structure
| Item | Legacy OFDM (20 MHz) | 802.11ad SC | Tag |
|---|---|---|---|
| Coarse field | L-STF 8 us = 10 x 16 samples (160) | STF 16 x Ga128 + (-Ga128) = 2176 chips | [vendor: MathWorks]; [paper: Baruffa 2023, 17 blocks of 128] |
| Fine / channel field | L-LTF 8 us = 32 GI + 2 x 64 (160 samples) | CEF 9 x 128 = 1152 chips (Gu512, Gv512, -Gb128) | [vendor]; [paper: Baruffa] |
| In-payload known | 4 pilot subcarriers of 52 per OFDM symbol | Ga64 guard interval per 512-chip block (448 data), i.e. 12.5 % known; 11ay GI 32 / 64 / 128 (480 / 448 / 384 data) | [paper: Baruffa]; [patent: Lomayev claim] |
| Modulation of known symbols | BPSK on subcarriers (STF every 4th subcarrier) | pi/2-rotated binary Golay | [vendor]; [paper] |
| Sample / chip rate | 20 MS/s | 1.76 Gchip/s | [vendor]; [paper] |
| Known fraction of a 1024-symbol burst | 320 known -> 1.18 dB if charged like ours | preamble 3328 chips (more than our burst) + 64 per 448 data | [derived] |

**What carries over to single carrier:** the L-STF / L-LTF autocorrelation estimators are time-domain operations on a
periodic known waveform; they work unchanged on any repeated single-carrier block (our C12 does this). **What does not:**
the OFDM pilot-subcarrier phase tracking during data, and the fact that the STF period (16 samples) results from
occupying every 4th subcarrier. 802.11ad SC is natively single carrier; its GI-every-512 is a block-pilot layout.

### 2.3 Synchronization in practice
- **Legacy coarse:** autocorrelation of L-STF at lag 16, alpha = angle(sum conj(s[i]) s[i+16]) / 16; MathWorks
  `wlanCoarseCFOEstimate` max 625 kHz = 2 subcarrier spacings; default `corrOffset` 0.75 of a short symbol skipped
  because of delay spread [vendor]. **OpenOFDM (open FPGA receiver) uses N = 64 samples and only the coarse estimate; the
  fine L-LTF stage is omitted** "due to the limited resolution of phase estimation and rotation in the look up table";
  pilots used for SFO [vendor/open implementation].
- **Legacy fine:** L-LTF lag 64, max 156.25 kHz = half a subcarrier spacing [vendor: MathWorks]; references Moose 1994,
  Li 2001 [vendor].
- **Ranges normalised [derived]:** coarse +-0.03125 cycles/sample (= our 0.03), fine +-0.0078. Design CFO +-40 ppm relative
  at 5.825 GHz = +-233 kHz = **0.0117 cycles/sample** (0.75 subcarrier); 2.4 GHz +-50 ppm = 124 kHz = 0.0062. So real Wi-Fi
  needs the coarse stage to pick the fine lobe, exactly as our C12 does, but its CFO is 2.6x (5 GHz) to 4.8x (2.4 GHz)
  smaller than ours relative to the sample rate.
- **802.11ad SC:** one-shot STF estimate (`dmgCFOEstimate` in MathWorks examples) [vendor, lit_real_wlan.md]; lag-128
  Golay autocorrelation; max tolerable 114.58 ppm (SC) = +-1/256 = 0.0039 cycles/chip [paper: Liu TCSI 2015 / derived];
  design +-40 ppm relative = 2.42 MHz = 1.4e-3 cycles/chip [derived]. GI-based residual phase tracking: plausible (the GI
  is "reused as known data for the next block" [paper: Baruffa]) but **not confirmed in a readable source**.
- **Phase noise / Doppler:** OFDM: pilot subcarriers track common phase error; packets are short (CFO drift negligible).
  802.11ad: not found.

### 2.4 Published sync performance
- **CFO RMSE vs SNR for L-STF/L-LTF in a readable source: not found** (Sourour et al. VTC 2004 and the NYCU CRB paper not
  readable). Our closed-form estimate (lit_real_wlan.md): fine std ~1.9x the 128-symbol CRB.
- Minimum operating point: 6 Mb/s sensitivity -82 dBm at PER 10 %, 1000 octets [std, via WARP page snippet]; WARP
  reference design measured -85 ... -88 dBm [vendor snippet]. With kTB(20 MHz) = -101 dBm, NF 10 dB, 5 dB implementation
  margin this implies ~+4 dB SNR [derived; NF and margin are assumptions, not read from the standard].
- 802.11ad SC (MathWorks, MCS 9): PER 0.09 at 7.5 dB, 0.03 at 8.5 dB with 20 ppm CFO estimated on the STF [vendor,
  lit_real_wlan.md]; MCS1 sensitivity -68 dBm ~ +3.5 dB per chip [derived, lit_real_wlan.md].
- Implementation loss vs ideal sync: **not found** for either.

### 2.5 Complexity
- OpenOFDM: one complex multiply + 64-sample moving average per sample for the coarse stage, no fine stage [vendor].
- Liu et al. TCSI 2015: 8x-parallel feed-forward joint detection / boundary / CFO for 802.11ad / 802.15.3c [paper,
  abstract via search]; the predecessor 802.15.3c sync design: 189k gates, 60.16 mW, 65 nm [paper, search snippet;
  different paper, do not attribute to Liu 2015].

### 2.6 Decoder-aided step
- None in any published Wi-Fi sync chain read (MathWorks, OpenOFDM). Pilot-subcarrier tracking is data-aided, not
  decoder-aided.

### 2.7 Our C12 vs the real system
| Aspect | Real legacy Wi-Fi | Our C12 (wifi128) | Effect |
|---|---|---|---|
| Known samples | 160 (STF) + 160 (LTF) | 128 (8 x 16) | ours fewer known samples (weaker estimate) but 0.51 dB instead of 1.18 dB energy |
| Fine stage | separate 64-periodic LTF, lag 64 | lag 64 on the same 16-periodic block (64 products) | similar |
| Lobe handling | coarse picks the fine lobe, no retry | CRC search over +-4 fine lobes (1/64) | ours stronger (catches coarse misses) |
| Phase tracking | pilot subcarriers | constant phase | ours weaker under phase noise (not tested in AWGN) |
| CFO range | 0.0117 (5 GHz), coarse range 0.031 | uniform +-0.03 | ours harsher |
| Overall | - | - | **mixed**: fewer known symbols and no tracking (weaker), plus a lobe search the real chip does not have (stronger). As an AWGN reference it is a fair "Wi-Fi-style" line. |

---

## 3. Card C13: MIL-STD-188-110C Appendix C and D (serial tone)

### 3.1 Standard, version, deployments
- MIL-STD-188-110C with Change Notice 1 [std, read via text reader]; superseded by **MIL-STD-188-110D (29 Dec 2017)**, whose
  Appendix D extends WBHF to 48 kHz / 240 kb/s [std listing: EverySpec, standards.ie; press: AFCEA]. App C = STANAG
  4539 (ITU-R F.763-5 Annex 6), App D = STANAG 5069 [std].
- Deployments: L3Harris Falcon III RF-7800H-MP (110C App D in the 2019 datasheet, 110D in the 2022 datasheet), Harris /
  Rockwell Collins App D modems shown interoperable [vendor: L3Harris datasheets via search; HFIA 2013 briefing via search].
  50 000 Falcon III units produced by 2023 [vendor press].

### 3.2 Frame structure
| Item | Appendix C (3200-9600 bps, 12800 uncoded) | Appendix D (3 kHz case) | Tag |
|---|---|---|---|
| Symbol rate | 2400 Bd, +-0.024 Bd (10 ppm); subcarrier 1800 Hz | 2400 Bd at 3 kHz ... 19200 Bd at 24 kHz | [std] / [derived from fn] |
| Preamble | 0-7 AGC blocks of 184 8PSK symbols, then 287 symbols: 184 for sync and Doppler removal + 103 (= reinserted preamble: 72 rate/interleaver symbols from 30 D-value sets x 13-chip Barker, + 31-symbol mini-probe) | TLC N blocks (N 0-255) + M superframes of Walsh-coded 32-symbol channel symbols: fixed 1 or 9 + count 4 + WID 5 -> 320 or 576 symbols per superframe [derived]; programmable 0.12 s to > 9.6 s [Harris slides, snippet] | [std] |
| Data / known | frames of 256 data + 31-symbol mini-probe (repeated 16-symbol Frank-Heimiller; text also says 32 in one place); every 72 frames +72 known | U data + K mini-probe per WID: 48/48 (WID 1-2), 96/32 (3-4), 256/32 (5-10, 13), 360/24 (11-12); WID 0 Walsh, no probes | [std] |
| Known fraction | steady state (72 x 31 + 72) / (72 x 287 + 72) = 11.1 %; 1024 data -> 287 + 4 x 31 = 411 known (1.47 dB) | 50 / 25 / 11.1 / 6.25 % | [derived] |
| Known-symbol modulation | 8PSK (Table C-I), unscrambled | PSK | [std] |

### 3.3 Synchronization in practice
- **Use of known symbols:** preamble = detection, timing, Doppler removal, rate signalling; mini-probes = channel
  estimation for the equaliser and Doppler / phase tracking; App C reinserted preamble for late entry [std].
- **Range:** +-75 Hz at 2400 Bd = **0.03125 cycles/symbol** [std/derived], i.e. our range. Test: +75 Hz then -75 Hz, >= 5
  min sync at 9600 bps, 30 dB SNR, 2 ms / 1 Hz channel, no BER test; Doppler sweep 3.5 Hz/s between +-75 Hz for 1 h at
  BER <= 1e-5 and 24 dB SNR (C.6.3/C.6.4, D.6.4/D.6.5) [std]. ITU-R F.763-5 restates +-75 Hz tolerance [std].
  Acquisition requirement C.6.2: "not yet standardized" [std].
- **Doppler rate:** 3.5 Hz/s = 6.1e-7 cycles/symbol^2 [derived], tracked through the probes / equaliser.
- **Published estimators:** for App C / D themselves, **not found** (MILCOM papers by Jorgenson / Furman / Nieto paywalled;
  Harris HFIA slides return 404). Nearest published implementations: MathWorks MIL-STD-188-110A receiver - preamble
  correlator + 3-peak state machine, CFO removed by an NCO driven by a PI loop on the phase slope of the equaliser
  input/output cross-spectrum (decision/equaliser-directed tracking), RLS DFE 20 + 20 taps [vendor]; kg7hf open 110A modem:
  lag-1 differential DA estimate over the 288-chip preamble (lit_real_military.md); QinetiQ STANAG 4285 basis-function
  combining, > 2 dB loss between 10 Hz bins (lit_real_military.md).

### 3.4 Published performance
- STANAG 4539 / App C, coded BER 1e-4, 72-frame interleaver, SNR in 3 kHz: 3200 bps (QPSK) AWGN 9 dB, poor channel 14 dB;
  9600 bps AWGN 21 dB [std: ITU-R F.763-5]. 3200 bps AWGN -> Es/N0 ~ 10 dB [derived, + 0.97 dB].
- App D WID 1-3 ~3 dB SNR for BER 1e-5 in AWGN (garbled table) [std].
- Acquisition Pd / Pfa vs SNR: **not found**. 110A/B acquisition "several dB" below the data SNR except 75 bps [Harris slides, snippet].

### 3.5 Complexity
- Not found for App C/D; QinetiQ 62.6k vs 154k operations for its 4285 acquisition (lit_real_military.md) [patent].

### 3.6 Decoder-aided step
- None published; tracking is probe-aided and equaliser/decision-directed (MathWorks 110A) [vendor].

### 3.7 Our C13 vs the real system
| Aspect | Real App C | Our C13 (mil110) | Effect |
|---|---|---|---|
| Known symbols for 1024 data | 411 (184 + 72 + 31 + 4 x 31) | 308 (184 + 4 x 31) | ours lighter: 1.14 vs 1.47 dB, so ~0.33 dB more favourable in AWGN |
| Acquisition | preamble estimate at high SNR, then probe tracking with DFE | R-B over all known + CRC search over +-3 probe-period lobes (1/287) | ours stronger at low SNR (CRC lobe search, all-symbol estimate) |
| Phase / Doppler rate | probe + equaliser tracking, 3.5 Hz/s | constant phase (AWGN) or Kalman over probes (pn arm) | comparable in the pn arm; static CFO only |
| Channel | HF fading, equaliser | AWGN | not comparable; known symbols also train the equaliser in reality |
| Overall | - | - | **C13 is a favourable (lighter, smarter-search) version** of App C; the real waveform would sit ~0.3 dB further right in AWGN. |

---

## 4. Card C11: sparse periodic pilots as in OIF 400ZR (layout and CFO range only)

Solid in `lit_real_terrestrial.md` (not repeated): 59.84375 GBd DP-16QAM, QPSK pilot every 32 symbols (PRBS10, X/Y
different seeds) for carrier phase recovery and absolute phase, 11-symbol training sequence per 3712-symbol DSP sub-frame,
49 sub-frames per super-frame, Rx frequency-offset tolerance +-1.8 GHz = 0.0301 (datasheets +-3.6 GHz = 0.060), Es/N0
~19 dB at the CFEC threshold [std contributions / vendor; derived].

New items:
- Pilot overhead 1/32 = 3.1 %, TS overhead 11/3712 = 0.30 % [derived]. Pilot-only alias range +-1/64 = 0.0156 [derived];
  TS spacing 3712 symbols.
- Wang et al., Chinese Optics Letters 23(6) 060602 (2025): the OIF 400ZR frame "employs training sequences for frame
  synchronization and initial frequency offset locking" and pilots for phase tracking; conventional fallback without TS is
  FFT-FOE + blind phase search; 800G LR pilot interval increased from 32 to 64 [paper]. (The OIF IA PDFs 02.0 / 03.0 could
  not be parsed here, so this is not verified against the IA.)
- Decoder-aided step: none found. Published sync performance for 400ZR modules: not found (vendor DSPs proprietary).
- **Our C11 vs real:** keeps the 1/32 pilot grid (33 pilots, 0.14 dB); changes: one 1024-symbol burst instead of a
  continuous stream, no TS, blind 4th-power coarse + R-B on pilots + CRC lobe search. Weaker than the real system in
  observation length (the real one averages over millions of symbols at 19 dB), stronger in its decoder-checked lobe
  search. As stated in competitors.md, cite 400ZR only as evidence that +-0.03 is a deployed requirement.

---

## 5. Per-source table

| # | Source | Year | Link | Read | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|---|
| 1 | Chakrapani, "NB-IoT uplink receiver design and performance study" (Qualcomm), IEEE IoT-J | 2019/2020 | [arXiv 1906.07096](https://arxiv.org/abs/1906.07096) | full text via reader | **high** | DMRS-only FFT (256 pt) + quadratic interpolation, per 8 / 32 ms block, search +-250 Hz | NB-IoT NPUSCH F1/F2, NPRACH, ETU/EPA | F1 1 tone 1 rep: 3GPP -2.1, sim -4.5, test -4.2 dB; fixed point < 0.5 dB; no iteration |
| 2 | Wang et al., "A primer on 3GPP NB-IoT" | 2016 | [arXiv 1606.04171](https://arxiv.org/pdf/1606.04171) | full text via reader | high | structure only | NB-IoT Rel-13 | F1: 1 DMRS / 7 symbols; F2: 3 / 7; pi/2-BPSK, pi/4-QPSK; 20 ppm initial crystal offset |
| 3 | MathWorks, `lteULFrameOffsetNPUSCH` / NB-IoT uplink pages (quoted in search) | current | [link](https://www.mathworks.com/help/lte/ref/lteulframeoffsetnpusch.html) | snippet | medium | - | NB-IoT | DMRS symbol 4 (3.75 kHz), 3 (15 kHz) |
| 4 | MathWorks, "NB-IoT NPUSCH block error rate simulation" | current | [link](https://www.mathworks.com/help/lte/ug/nb-iot-npusch-block-error-rate-simulation.html) | full | low | timing from DRS correlation; no CFO | A16-5 FRC, 12 tones, 15 kHz | perfect channel estimation default |
| 5 | Ericsson (Lu, Mauritz, Huss, Back), US 8 605 799 B2 | 2013 | [Google Patents](https://patents.google.com/patent/US8605799B2/en) | partial | medium | PUSCH (0.5 ms) + PUCCH (~4/14 ms) RS lags combined by hypothesis table | LTE eNB | PUSCH +-1 kHz, PUCCH +-1.75 kHz, ideal 7 kHz |
| 6 | TS 36.521-1 6.5.1F mirror (itecspec) | - | [link](https://itecspec.com/spec/3gpp-36-521-1-6-5-1f-frequency-error-for-category-nb1-and-nb2) | search snippet only | medium | - | NB-IoT UE | +-0.1 ppm (> 1 GHz), +-0.2 ppm (<= 1 GHz), + 15 Hz test |
| 7 | Liberg et al., "NB-IoT for non-terrestrial networks", IEEE Comm. Std. Mag. | 2020 | [arXiv 2010.04906](https://arxiv.org/pdf/2010.04906) | full via reader | medium | GNSS + ephemeris pre-compensation | NB-IoT NTN GEO / LEO | 24 ppm cap (LEO 600 km), delay rate 24 us/s; no residual numbers |
| 8 | Ericsson, US 12 136 966 B2, "Frequency offset in NTN" | 2024 | [Google Patents](https://patents.google.com/patent/US12136966B2/en) | first 100k chars | medium | - | NTN LEO | 43 kHz / 21 ppm at 2 GHz; rate up to 500 Hz/s; UE-to-UE UL difference ~16 kHz |
| 9 | 3GPP RAN1 #110 draft CR to 36.213 (IoT-NTN pre-compensation); RAN4 LS on TDD pre-comp. | 2022/2025 | [R1-2208176](https://3gpp.org/ftp/TSG_RAN/WG1_RL1/TSGR1_110/Inbox/drafts/8.14(LTE_NBIOT_eMTC_NTN)/CR%20to%2036.213-UE%20pre-compensation/DRAFT-R1-2208176-Moderator-CR%20to%2036.213-Maintenance%20on%20IoT-NTN.docx) | search snippet | medium | per-segment time/frequency pre-compensation, uplink compensation gaps | IoT-NTN Rel-17 | segment duration values not found |
| 10 | 3GPP R4-2216641 draft CR, NTN frequency error | 2022 | [docx](https://3gpp.org/ftp/tsg_ran/WG4_Radio/TSGR4_104bis-e/Inbox/Drafts/%5B104-bis-e%5D%5B304%5D%20NTN_Solutions_RF_Maintenance/Rnd2/revised%20R4-2216641%20(R17%20NTN)%20%20CR%20on%20NTN%20Frequency%20error%20requirement.docx) | search snippet | medium | - | NR NTN UE | +-0.1 ppm over 1 ms vs ideally pre-compensated carrier (draft) |
| 11 | "5G NR NTN: from early results to the road ahead" | 2026 | [arXiv 2601.04882](https://arxiv.org/html/2601.04882) | full HTML | low-medium | Rel-17 GNSS pre-comp.; Rel-18 PUSCH DMRS bundling | NR NTN | qualitative only |
| 12 | Chougrani et al., NB-IoT RA for NTN (already in lit_real_terrestrial.md) | 2021 | [arXiv 2101.08079](https://arxiv.org/pdf/2101.08079) | (prior) | medium | - | NPRACH NTN | residual +-600 Hz (99 %) |
| 13 | NB-IoT uplink in LEO NTN, Sensors 22(18) 7097 | 2022 | [PMC9502177](https://pmc.ncbi.nlm.nih.gov/articles/PMC9502177/) | search snippet only (captcha) | low-medium | added DMRS | NB-IoT LEO | residual compensation ~950 Hz; denser DMRS helps BLER |
| 14 | RCR Wireless / Counterpoint / CNX press on Skylo, Sateliot, Sony ALT1250, Qualcomm 9205S | 2023-25 | [RCR](https://rcrwireless.com/20240717/internet-of-things/soracom-offers-satellite-nb-iot-from-skylo-in-phased-commercial-launch), [RCR Sony](https://www.rcrwireless.com/20240503/internet-of-things-4/skylo-certifies-nb-iot-chipset-from-sony-semiconductor-for-dual-mode-satellite-iot), [CNX](https://www.cnx-software.com/2023/06/23/qualcomm-212s-and-9205s-satellite-iot-modems-target-remote-monitoring-and-asset-tracking/) | snippets | low | - | deployments | Skylo GEO Rel-17; Soracom launch 07/2024 |
| 15 | GSMA via RCR Wireless, "48 mobile IoT networks" | 2018 | [RCR](https://rcrwireless.com/20180518/internet-of-things/gsma-48-mobile-iot-networks-worldwide-tag23) | snippet | low | - | deployments | 32 NB-IoT networks (early 2018) |
| 16 | MathWorks `wlanCoarseCFOEstimate` | current | [link](https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html) | full | medium | L-STF autocorrelation, corrOffset 0.75 default | 802.11 OFDM | max 625 kHz; refs Moose 1994, Li 2001 |
| 17 | OpenOFDM, "Frequency offset correction" | current | [link](https://openofdm.readthedocs.io/en/latest/freq_offset.html) | full | **high** (real implementation) | lag-16 over N = 64 samples; fine stage omitted | 802.11a/g FPGA | - |
| 18 | Keysight 89600, "SymClkErr (802.11a/g/j/p OFDM)" | current | [link](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/wlan-ofdm/content/ofdm_symtblerrdata_symclkerr.htm) | snippet | medium | - | 802.11 | +-20 ppm (a/j/p), +-25 ppm (b/g); same oscillator |
| 19 | WARP 802.11 Rx characterization | - | [link](https://warpproject.org/trac/wiki/802.11/Benchmarks/Rx_Char?version=10) | snippet (403) | low | - | 802.11 | 6 Mb/s min -82 dBm, PER 10 %, 1000 octets; measured -85 ... -88 dBm |
| 20 | Baruffa, Rugini, "Improved channel estimation and equalization for SC IEEE 802.11ad receivers", Radioengineering 32(3) | 2023 | [PDF](https://www.radioeng.cz/fulltexts/2023/23_03_0438_0450.pdf) | full via reader | medium | (assumes ideal sync) | 802.11ad SC | STF 17 x 128, CEF 9 x 128, 448 + Ga64, 1.76 GS/s |
| 21 | Lomayev et al. (Intel), 802.11ay GI claim | - | [patent PDF](https://patentimages.storage.googleapis.com/b4/7f/5f/550f3e1a0fcef2/US10615930.pdf) | search snippet | low | - | 802.11ay SC | GI 32 / 64 / 128 with 480 / 448 / 384 data |
| 22 | Liu et al., "All-digital synchronization for SC/OFDM mode of 802.15.3c and 802.11ad", IEEE TCSI 62 | 2015 | [NYCU record](https://ir.lib.nycu.edu.tw:443/handle/11536/124352) | abstract via search | medium | joint detection / boundary / CFO, 8x parallel | 60 GHz | 114.58 ppm (SC), 171.87 ppm (OFDM) |
| 23 | Terragraph runbook overview | current | [link](https://terragraph.com/docs/runbook/Overview) | full | medium (deployment) | - | 802.11ad SC mesh | MCS 1-12, 385-4620 Mb/s, GPS-synchronised nodes |
| 24 | Qualcomm 802.11ay chipsets press | 2018 | [Tom's Hardware](https://www.tomshardware.com/news/qualcomm-reveals-802-11ay-wi-fi-chipsets,37935.html) | snippet | low | - | 60 GHz | QCA6438 / QCA6428 for Terragraph |
| 25 | MIL-STD-188-110C w/ CN1 (App C, D) | 2011/2012 | [sigidwiki PDF](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf) | text reader, 200k-400k | **high** | - | HF serial tone | see card 3 |
| 26 | ITU-R F.763-5 (Annex 6 = STANAG 4539) | 2005 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/f/R-REC-F.763-5-200501-P!!PDF-E.pdf) | text reader | high | - | HF | +-75 Hz; 3200 bps AWGN 9 dB / poor 14 dB at BER 1e-4 |
| 27 | MIL-STD-188-110D listing (EverySpec); AFCEA comment | 2017 | [EverySpec](https://everyspec.com/MIL-STD/MIL-STD-0100-0299/MIL-STD-188-110D_55856/), [AFCEA](https://www.afcea.org/comment/1627) | snippet | medium | - | HF | dated 29 Dec 2017; WBHF to 48 kHz, 240 kb/s |
| 28 | MathWorks, "US MIL-STD-188-110A receiver" | current | [link](https://in.mathworks.com/help/comm/ug/defense-communications-us-mil-std-188-110a-receiver.html) | full | medium | preamble 3-peak detection; CFO via cross-spectrum phase LS fit + PI loop + NCO; RLS DFE 20 + 20 | 110A, Watterson channel | no numbers |
| 29 | L3Harris RF-7800H-MP datasheets | 2019/2022 | [2020 PDF](https://l3harris.com/sites/default/files/2020-07/cs_tc_datsheet_rf-7800h-mp-wideband-hf-vhf-tactical-radio-system.pdf) | search snippet | low (deployment) | - | WBHF radio | 110C App D (2019), 110D (2022) |
| 30 | Furman, Nieto, "Latest on-air testing of 110C App D", IET HF conf. | 2012 | [IET](https://digital-library.theiet.org/content/conferences/10.1049/cp.2012.0386) | index only | medium | - | 160 km NVIS, 1700 km | not read |
| 31 | Jorgenson, Johnson, Nelson, "An extension of wideband HF capabilities", MILCOM | 2013 | DOI 10.1109/MILCOM.2013.205 ([index](https://manuscript.isc.ac/Inventory/49/680940.htm)) | index only | medium | - | App D extensions | not read |
| 32 | Wang C. et al., Chinese Optics Letters 23(6) 060602 | 2025 | [PDF](https://www.researching.cn/ArticlePdf/m00005/2025/23/6/060602.pdf) | full via reader | medium | pilot-only frame sync + carrier recovery | 60 GBd DP-16QAM, 800G LR style | 400ZR TS for initial FO locking; pilot interval 32 -> 64; +-13 GHz range vs +-7.5 GHz FFT-FOE |
| 33 | OIF-400ZR-02.0 / 03.0 IA | 2020/2024 | [03.0 PDF](https://oiforum.com/wp-content/uploads/OIF-400ZR-03.0.pdf) | **not read** (PDF not parseable) | high | - | 400ZR | - |

Searched, not found or not readable: TS 36.211 DMRS sequence text; TS 36.102 IoT-NTN frequency-error clause and the
npusch-TxDuration value list; NPUSCH CFO RMSE vs SNR; 802.11 STF/LTF RMSE curves (Sourour 2004, NYCU CRB paper);
802.11ad GI phase tracking; App C/D acquisition Pd/Pfa curves; any App C/D sync complexity; the OIF IA text.

---

## 6. Per-component verdict (these four systems vs our blind receiver)

| Component | Deployed practice (this report) | Verdict |
|---|---|---|
| Coarse CFO | DA: FFT over DMRS phases (NB-IoT), lag-16 autocorrelation (Wi-Fi), lag-128 Golay (11ad), preamble (MIL), TS (400ZR) | **not applicable** to a pilot-free burst; our 4th-power fast path is the blind counterpart (already used) |
| Fine CFO / phase | DMRS block averaging, LTF lag 64, probe + equaliser tracking, pilot CPR | **we already use** code-aided refinement (Stage 3) as the blind counterpart; pilot tracking not applicable |
| Range extension | Ericsson PUSCH + PUCCH lag combination by hypothesis table (US8605799) | **we already use** a stronger form (CFO-cell grid scored by the decoder); nothing to borrow |
| Doppler rate | NTN per-segment re-pre-compensation; MIL 3.5 Hz/s probe tracking | **not tested**: static CFO only; the drift test planned in competitors.md covers it (NTN 3.75 kHz raw rate would move the CFO by 0.039 cycles/symbol over 1024 symbols [derived], so use GNSS-compensated residuals, e.g. 0.001-0.01 total) |
| Acceptance | CRC only; NPRACH Pd >= 99 %, Pfa <= 0.1 % | **we already use** stricter CRC-16 + rho |
| Decoder-aided sync | none in any of the four systems | blind is the only decoder-in-the-loop receiver here; no deployed analogue |

---

## Reference entries

### Chakrapani, A., "NB-IoT Uplink Receiver Design and Performance Study", IEEE Internet of Things Journal, 2020 (arXiv 1906.07096)
- Link: https://arxiv.org/abs/1906.07096   - Type: paper   - Read depth: full text via PDF-to-text reader
#### What it does
Qualcomm FSM small-cell NB-IoT uplink receiver. NPUSCH format 1: DMRS (symbol 3) averaged over tones, per block of 8 ms
(multi-tone) or 32 ms (single-tone); 256-point FFT of the DMRS phase sequence, peak + quadratic interpolation, search
+-250 Hz, resolution ~7.8 Hz; format 2 reuses it. Not iterative. Results vs TS 36.104: e.g. 1 tone 1 rep -2.1 (3GPP) /
-4.5 (sim) / -4.2 dB (test); fixed-point loss < 0.5 dB; NPRACH Pd >= 99 %, Pfa <= 0.1 %, max NPRACH offset ~+-357 Hz.
#### What we took / could take
Deployed NB-IoT CFO estimator and window (+-250 Hz = 0.018 cycles/symbol at 15 kHz [derived]) for the C10 card: C10
is a widened (stronger) version. Not adopted into blind.
#### Used in
-

### Wang, Y.-P. E., et al., "A Primer on 3GPP Narrowband Internet of Things (NB-IoT)", IEEE Commun. Mag., 2017 (arXiv 1606.04171)
- Link: https://arxiv.org/pdf/1606.04171   - Type: paper   - Read depth: full text via reader
#### What it does
NB-IoT structure: NPUSCH F1 7 symbols / slot, 1 DMRS (middle); F2 3 DMRS; single tone 15 / 3.75 kHz with pi/2-BPSK,
pi/4-QPSK; multi-tone 3/6/12; initial crystal offset up to 20 ppm; raster offset 2.5 / 7.5 kHz.
#### What we took / could take
Confirms the 1/7 DMRS density of C10 (already cited in competitors.md).
#### Used in
competitors.md C10 (link)

### MathWorks, LTE Toolbox, `lteULFrameOffsetNPUSCH` and "NB-IoT NPUSCH Block Error Rate Simulation" (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/lte/ug/nb-iot-npusch-block-error-rate-simulation.html   - Type: app note (vendor)   - Read depth: full (BLER page), snippet (DMRS position)
#### What it does
DMRS on symbol 4 (3.75 kHz) / 3 (15 kHz) for NPUSCH format 1; BLER example (A16-5 FRC, 12 tones, 15 kHz) with timing from
the DRS correlation, perfect or DRS-based channel estimation, no CFO model.
#### What we took / could take
DMRS positions for the C10 card. Nothing else.
#### Used in
-

### Ericsson (Lu, G., Mauritz, O., Huss, F., Back, H.), US 8 605 799 B2, "Estimation of frequency offset between a base station and mobile terminal", 2013
- Link: https://patents.google.com/patent/US8605799B2/en   - Type: patent   - Read depth: partial (description summary)
#### What it does
LTE PUSCH RS spacing 0.5 ms -> +-1000 Hz; PUCCH ~4/14 ms -> +-1750 Hz; combines both lags through a hypothesis table of
offset regions to resolve wrap-around (ideal limit 7 kHz). No SNR numbers.
#### What we took / could take
Deployed example of CFO hypothesis resolution with two lags; we already do a stronger version (decoder-scored grid).
#### Used in
-

### 3GPP TS 36.521-1 clause 6.5.1F (NB-IoT frequency error), via itecspec mirror
- Link: https://itecspec.com/spec/3gpp-36-521-1-6-5-1f-frequency-error-for-category-nb1-and-nb2   - Type: standard   - Read depth: search snippet only
#### What it does
Cat NB1/NB2 UE frequency error +-0.1 ppm (> 1 GHz), +-0.2 ppm (<= 1 GHz) over one slot; test +15 Hz.
#### What we took / could take
Terrestrial NB-IoT CFO budget: 0.013 cycles/symbol at 15 kHz single tone [derived].
#### Used in
-

### Liberg, O., et al., "Narrowband Internet of Things for Non-Terrestrial Networks", IEEE Communications Standards Magazine, 2020 (arXiv 2010.04906)
- Link: https://arxiv.org/pdf/2010.04906   - Type: paper   - Read depth: full text via reader
#### What it does
NB-IoT over GEO / LEO: GNSS + ephemeris based timing and Doppler pre-compensation; LEO 600 km Doppler capped at 24 ppm by
the 10 deg elevation limit; delay rate up to 24 us/s; link budgets. No residual-error numbers.
#### What we took / could take
NTN Doppler context for the C10 card.
#### Used in
-

### Ericsson, US 12 136 966 B2, "Frequency offset in non-terrestrial networks", 2024
- Link: https://patents.google.com/patent/US12136966B2/en   - Type: patent   - Read depth: first 100k characters
#### What it does
LEO 600 km: max Doppler 43 kHz / 21 ppm at 2 GHz; Doppler rate up to 500 Hz/s; oscillator drift 0.01 ppm/s; two UEs'
UL frequency difference up to ~16 kHz.
#### What we took / could take
Doppler-rate value for the drift test discussion (raw, before UE pre-compensation).
#### Used in
-

### 3GPP RAN1 #110 draft CR R1-2208176 to TS 36.213 (IoT-NTN UE pre-compensation); RAN4 LS reply on pre-compensation for IoT NTN TDD (R4-2512550)
- Link: https://3gpp.org/ftp/TSG_RAN/WG1_RL1/TSGR1_110/Inbox/drafts/8.14(LTE_NBIOT_eMTC_NTN)/CR%20to%2036.213-UE%20pre-compensation/DRAFT-R1-2208176-Moderator-CR%20to%2036.213-Maintenance%20on%20IoT-NTN.docx   - Type: standard (draft)   - Read depth: search snippet
#### What it does
NB-IoT UE adjusts time and frequency pre-compensation per uplink segment (npusch-TxDuration), uplink compensation gaps;
pre-compensation updated at the start of each segment.
#### What we took / could take
How Rel-17 handles Doppler rate (re-compensation per segment). Not used.
#### Used in
-

### 3GPP R4-2216641 (revised), "(R17 NTN) CR on NTN frequency error requirement", draft
- Link: https://3gpp.org/ftp/tsg_ran/WG4_Radio/TSGR4_104bis-e/Inbox/Drafts/%5B104-bis-e%5D%5B304%5D%20NTN_Solutions_RF_Maintenance/Rnd2/revised%20R4-2216641%20(R17%20NTN)%20%20CR%20on%20NTN%20Frequency%20error%20requirement.docx   - Type: standard (draft CR)   - Read depth: search snippet
#### What it does
NR NTN UE frequency error +-0.1 ppm over 1 ms relative to the ideally pre-compensated carrier (draft wording).
#### What we took / could take
NTN residual budget with GNSS: ~0.014 cycles/symbol at 15 kHz [derived]. Not confirmed as final text.
#### Used in
-

### "5G NR Non-Terrestrial Networks: From Early Results to the Road Ahead", arXiv 2601.04882, 2026
- Link: https://arxiv.org/html/2601.04882   - Type: paper   - Read depth: full HTML
#### What it does
Rel-17 GNSS-based TA / frequency pre-compensation (not usable indoors); Rel-18 PUSCH DMRS bundling for phase continuity;
Rel-20 to study GNSS-resilient operation. Qualitative only.
#### What we took / could take
Release context for the C10 card. Not used.
#### Used in
-

### "Performance Analysis of NB-IoT Uplink in Low Earth Orbit Non-Terrestrial Networks", Sensors 22(18) 7097, 2022
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC9502177/   - Type: paper   - Read depth: search snippet only (captcha)
#### What it does
LEO NB-IoT uplink: added DMRS improves BLER; residual compensation range ~950 Hz; beam-size reduction proposed.
#### What we took / could take
Not used: numbers not verifiable.
#### Used in
-

### Press on NB-IoT NTN deployments (RCR Wireless 2024: Soracom / Skylo launch, Sony ALT1250 certification; CNX Software 2023: Qualcomm 9205S / 212S; GSMA via RCR 2018)
- Link: https://rcrwireless.com/20240717/internet-of-things/soracom-offers-satellite-nb-iot-from-skylo-in-phased-commercial-launch   - Type: press   - Read depth: snippet
#### What it does
Skylo GEO Rel-17 NB-IoT service; Soracom phased launch July 2024; certified chipsets (Sony ALT1250, u-blox UBX-S52,
Quectel, Telit); Sateliot LEO; 32 NB-IoT networks by early 2018 (GSMA).
#### What we took / could take
"Real deployments" line of the C10 card.
#### Used in
-

### MathWorks, `wlanCoarseCFOEstimate` (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html   - Type: app note (vendor)   - Read depth: full
#### What it does
L-STF autocorrelation coarse CFO; max 625 kHz (2 subcarrier spacings); `corrOffset` default 0.75 of a short symbol
skipped against delay spread; L-STF 8 us at 20 MHz; refs Li 2001, Moose 1994, Perahia & Stacey 2013.
#### What we took / could take
Confirms the C12 coarse stage (already cited).
#### Used in
competitors.md C12 (link)

### OpenOFDM documentation, "Frequency Offset Correction" (open-source 802.11a/g FPGA receiver)
- Link: https://openofdm.readthedocs.io/en/latest/freq_offset.html   - Type: app note (open implementation)   - Read depth: full
#### What it does
Coarse CFO = angle(sum conj(S[i]) S[i+16]) / 16 with a 64-sample moving average; correction applied from the LTF on;
the fine LTF stage is omitted because of LUT phase-resolution limits; pilots used for SFO.
#### What we took / could take
Evidence that real Wi-Fi hardware may run only the lag-16 coarse stage; C12's two-stage + lobe search is stronger.
#### Used in
-

### Keysight 89600 VSA help, "SymClkErr (802.11a/g/j/p OFDM)"
- Link: https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/wlan-ofdm/content/ofdm_symtblerrdata_symclkerr.htm   - Type: app note (vendor)   - Read depth: snippet
#### What it does
Symbol clock (and carrier, same oscillator) tolerance +-20 ppm (802.11a/j/p), +-25 ppm (802.11b/g).
#### What we took / could take
Wi-Fi CFO budget: 0.0117 cycles/sample at 5.8 GHz, 0.0062 at 2.4 GHz [derived].
#### Used in
-

### WARP project, "802.11 Reference Design Rx characterization" (wiki)
- Link: https://warpproject.org/trac/wiki/802.11/Benchmarks/Rx_Char?version=10   - Type: app note (open implementation)   - Read depth: snippet (403 on fetch)
#### What it does
802.11-2012 18.3.10.2 minimum sensitivity: 6 Mb/s -82 dBm at PER 10 %, 1000 octets; WARP measured -85 (later -88) dBm.
#### What we took / could take
Minimum operating SNR context (~+4 dB, derived with assumed NF and margin). Not used.
#### Used in
-

### Baruffa, G., Rugini, L., "Improved Channel Estimation and Equalization for Single-Carrier IEEE 802.11ad Receivers", Radioengineering 32(3), 2023
- Link: https://www.radioeng.cz/fulltexts/2023/23_03_0438_0450.pdf   - Type: paper   - Read depth: full via reader
#### What it does
802.11ad SC frame: STF 17 x 128, CEF 9 x 128, LDPC 672-bit codewords in 448-symbol blocks + Ga64 GI (512-symbol cyclic
blocks, GI reused as known data), pi/2 rotation, 1760 MS/s; assumes ideal sync; channel-estimation gains 0.5-0.95 dB.
#### What we took / could take
802.11ad SC known-symbol layout for the C12 card (shows C12 does not model 11ad). Not used otherwise.
#### Used in
-

### Lomayev, A., et al. (Intel), US 10 615 930, 802.11ay adaptive GI (claim)
- Link: https://patentimages.storage.googleapis.com/b4/7f/5f/550f3e1a0fcef2/US10615930.pdf   - Type: patent   - Read depth: search snippet
#### What it does
EDMG SC GI types: short 32 (480 data), normal 64 (448), long 128 (384) chips.
#### What we took / could take
802.11ay known fractions 6.25 / 12.5 / 25 % [derived]. Not used.
#### Used in
-

### Liu, W.-C., Wei, T.-C., Huang, Y.-S., Chan, C.-D., Jou, S.-J., "All-Digital Synchronization for SC/OFDM Mode of IEEE 802.15.3c and IEEE 802.11ad", IEEE TCSI 62(2), 545-553, 2015
- Link: https://ir.lib.nycu.edu.tw:443/handle/11536/124352   - Type: paper   - Read depth: abstract via search
#### What it does
Joint preamble detection, boundary detection, CFO estimation on the Golay preamble; 8x parallel feed-forward; tolerates
114.58 ppm (SC), 171.87 ppm (OFDM).
#### What we took / could take
11ad CFO range (0.0039 cycles/chip [derived]); already cited in competitors.md C12.
#### Used in
competitors.md C12 (link)

### Terragraph documentation, "Runbook: Overview"; Qualcomm 802.11ay chipset press (Tom's Hardware 2018)
- Link: https://terragraph.com/docs/runbook/Overview   - Type: app note (vendor)   - Read depth: full (runbook), snippet (press)
#### What it does
Terragraph uses the 802.11ad single-carrier PHY (MCS 1-12, pi/2-BPSK/QPSK/16QAM, 385-4620 Mb/s, 2.16 GHz channels),
GPS-synchronised nodes, on Qualcomm QCA6438 / QCA6428 (pre-802.11ay).
#### What we took / could take
Deployment line for the 802.11ad SC card.
#### Used in
-

### ITU-R Recommendation F.763-5 (2005), "Data transmission over HF circuits using PSK or QAM", Annex 6 (STANAG 4539)
- Link: https://www.itu.int/dms_pubrec/itu-r/rec/f/R-REC-F.763-5-200501-P!!PDF-E.pdf   - Type: standard   - Read depth: text reader (Annex 6)
#### What it does
287-symbol preamble (+0-7 x 184 AGC), 256 data + 31 mini-probe, 72-symbol reinsertion every 72 frames, 2400 Bd, +-75 Hz
tolerance; coded BER 1e-4 SNR (3 kHz): 3200 bps 9 dB AWGN / 14 dB poor, 9600 bps 21 / 30 dB.
#### What we took / could take
Confirms the App C frame and range for the C13 card.
#### Used in
-

### MIL-STD-188-110D (29 Dec 2017), listing (EverySpec) and AFCEA comment
- Link: https://everyspec.com/MIL-STD/MIL-STD-0100-0299/MIL-STD-188-110D_55856/   - Type: standard (listing)   - Read depth: snippet
#### What it does
Current revision; Appendix D extended to contiguous bandwidths up to 48 kHz, up to 240 kb/s.
#### What we took / could take
Version note for the C13 card (110C is superseded).
#### Used in
-

### MathWorks, "US MIL-STD-188-110A Receiver" (Communications Toolbox example)
- Link: https://in.mathworks.com/help/comm/ug/defense-communications-us-mil-std-188-110a-receiver.html   - Type: app note (vendor)   - Read depth: full
#### What it does
Preamble correlator + 3-peak state machine; CFO removed by an NCO driven by a PI loop on the phase slope (LS fit) of the
equaliser input/output cross-spectrum; RLS DFE 20 + 20 taps; Watterson channel; no numbers.
#### What we took / could take
Shows deployed-style HF tracking is equaliser/decision-directed, not one-shot. Not used.
#### Used in
-

### L3Harris, RF-7800H-MP wideband HF/VHF tactical radio datasheets (2019, 2022)
- Link: https://l3harris.com/sites/default/files/2020-07/cs_tc_datsheet_rf-7800h-mp-wideband-hf-vhf-tactical-radio-system.pdf   - Type: datasheet   - Read depth: search snippet
#### What it does
Wideband waveforms MIL-STD-188-110C App D (2019 sheet), MIL-STD-188-110D (2022 sheet).
#### What we took / could take
Deployment line for the C13 card.
#### Used in
-

### Furman, W. N., Nieto, J. W., "Latest on-air testing of U.S. MIL-STD-188-110C Appendix D wideband HF data waveforms", IET HF Radio Systems and Techniques, 2012; Jorgenson, M., Johnson, R., Nelson, R., "An extension of wideband HF capabilities", MILCOM 2013
- Link: https://digital-library.theiet.org/content/conferences/10.1049/cp.2012.0386   - Type: paper   - Read depth: index only
#### What it does
On-air App D tests (160 km NVIS, 1700 km); App D extensions. Full texts not read.
#### What we took / could take
Nothing (not read).
#### Used in
-

### Wang, C., Li, Z., Dong, Z., et al., "Highly robust and hardware-efficient frame synchronization and carrier recovery via pilot-only approaches for short-reach optical interconnections", Chinese Optics Letters 23(6), 060602, 2025
- Link: https://www.researching.cn/ArticlePdf/m00005/2025/23/6/060602.pdf   - Type: paper   - Read depth: full via reader
#### What it does
States that OIF 400ZR frames use training sequences for frame sync and initial frequency-offset locking and pilots for
phase tracking; 800G LR pilot interval 32 -> 64; proposes pilot-only sync (60 GBd DP-16QAM, CFO range +-13 GHz vs +-7.5
GHz for FFT-FOE + BPS, 0.7 dB sensitivity gain).
#### What we took / could take
Correction to lit_real_terrestrial.md ("400ZR coarse FOE must be blind"): the real coarse stage is likely TS-aided. C11
unchanged.
#### Used in
-
