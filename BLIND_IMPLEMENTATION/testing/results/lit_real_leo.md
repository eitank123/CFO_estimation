# Real, deployed LEO / NTN / satellite-IoT systems: how they handle CFO, and what it means for our blind receiver

Literature scout report, 2026-11-15. No simulations were run. Scope: commercial LEO, NTN and satellite-IoT systems,
**single-carrier waveforms first** (user's clarification); OFDM systems get one line of context. Material already in
`lit_blind_cfo.md`, `lit_polar_sync.md` and `lit_dvbrcs2.md` (DVB-RCS2 EN 301 545-2 / TR 101 545-4, Griebel 2021,
ESA US7409024, LR-FHSS ASIC paper 2403.14154, Ericsson 2108.07757) is not repeated.

Conventions. f = df / Rs in cycles per symbol. Numbers marked **[derived]** are my arithmetic, not from a source.
LEO Doppler is taken as about +-2.3e-5 x fc (user's figure; Humphreys et al. bound |beta| < 2.5e-5). "Static over the
burst" is judged with the quadratic-phase deviation pi x (Doppler rate) x T^2 / 4 of a 1024-symbol burst
(T = 1024 / Rs) against 0.1 rad **[derived criterion]**.

Reading depth: "full" = text read (some PDFs via the r.jina.ai text reader, public URL only); "abstract"; "snippet" =
search-result text only. Several PDFs (ICAO Iridium manual, the npj OneWeb PDF directly, IMDEA NTN receiver, UPC
OJCOMS 2026, AIS papers, MDPI DVB-RCS2-over-LEO) could not be parsed or were blocked (403/404); this is marked.

---

## 1. Ranked takeaways (5)

### T1. No deployed system does what we do; all of them use known symbols, pre-compensation, or both
Every system read either (a) pre-compensates Doppler with GNSS position + ephemeris (3GPP NR / NB-IoT NTN: UE must be
within **+-0.1 ppm** of the ideally pre-compensated frequency, TS 38.101-5 cl. 6.4.1; OneWeb / Starlink receivers use
TLE-predicted Doppler with "at most a few Hz" error), or (b) acquires with known symbols (VDE-SAT 27-symbol syncword +
1 pilot every 27 symbols; Iridium 12-symbol BPSK unique word; Comtech 64-symbol QPSK preamble; Viasat / Hughes unique
words; NB-IoT DMRS 1 symbol per 7), or both. None acquires |f| up to 0.03 at Es/N0 = -5 dB with zero known symbols.
**Consequence for the comparison:** our blind receiver is beyond deployed practice in the "no known symbols"
dimension, and our +-0.03 static CFO corresponds in the real world to either (i) **uncompensated** LEO Doppler on
wideband single-carrier bursts (Rs about 1.2 / 1.7 / 9 / 16 Msym/s at L / S / Ku / Ka), or (ii) the **residual** after
GNSS pre-compensation on narrowband links (NB-IoT-NTN single tone at 3.75 kHz: 200 Hz / 3750 = **0.053** [derived]).
Case (ii) is not static over 1024 symbols (T6 below).

### T2. Add a VDE-SAT-style competitor: 27-symbol syncword + 1 pilot every 27 symbols (66 known symbols, 0.27 dB)
ITU-R M.2092-2 (02/2026), VDE-SAT links: pi/4-QPSK at 33.6 ksym/s, roll-off 0.25, turbo rates 1/4-1/2, CRC-16/32;
pilots are single symbols (1+j)/sqrt2, pilot distance **27**, syncword **27 symbols**; AWGN Es/N0 thresholds as low as
**-4.5 / -3.6 / -0.6 dB** (Table 11), -0.9 dB on the uplink (Table 9). Doppler +-4 kHz at VHF, satellite carrier
< 1 ppm. This is the only real, current, low-SNR single-carrier PSK standard found whose operating Es/N0 is at our
points, and its known-symbol budget (about 6 %) sits between our RCS2 ID 13 (116 known) and 16 + 16 (32 known).
- Layout for us [derived]: syncword 27 | 1024 data with 1 pilot after every 26 data symbols (39 pilots) | = 66 known
  symbols, burst 1090, energy cost 10 log10(1090/1024) = **0.27 dB**.
- Estimator: Rife-Boorstyn FFT over all known symbols (DA-KS, as our RCS2 receiver) + CRC search over the alias lobes.
  The pilot-only range is |f| < 1/54 = 0.0185 [derived], below our 0.03, so the alias lobes at +-1/27 = +-0.037 from the
  true peak are inside the search window. The 27-symbol syncword has an exact null at offset 1/27, so the alias lobe
  carries the 39 pilots but none of the syncword: height about 39/66 = **0.59** of the true peak [derived]. Expect wrong
  lobes at -5 dB in a few to ~10 % of packets [rough], so reuse the 64 + 64 receiver's CRC lobe search (3 lobes).
- Expected performance [rough estimate from 8.2a, not simulated]: where estimation is good (2/5, 1/2) the loss vs genie
  is about the energy cost, as for RCS2 ID 13 (2/5: 1.10 = genie 0.64 + 0.46 dB). So VDES-27 should land about
  genie + 0.3 dB: **~0.9-1.0 dB at 2/5 10^-3** and **~2.2 dB at 1/2 10^-3**, i.e. 0.15-0.2 dB better than ID 13 and still
  ~0.3-0.4 dB behind blind (0.61, 1.79). At 1/10 -5 dB the lobe ambiguity decides; with the CRC lobe search it should
  be between ML-128 (-4.68) and genie + 0.27 (-4.92) at 10^-4. Test: est4 variant `vdes27`, 480k packets at the 8.2a
  SNRs, all four rates.

### T3. The Viasat "joint frequency and unique word detection" patent is the deployed form of our Stage 1 -> Stage 2 idea
US 8,243,859 (Viasat, Mo & Thesling, 2012): N-theta (M-th power) FFT over the burst, keep the **N strongest peaks**
(example: 32 of 1024 bins), frequency-correct at each, UW-correlate over M timing hypotheses, combine frequency and UW
magnitudes with weights, pick the best; reported **burst recovery error < 1e-5 at 2.5 dB SNR** (SNR definition,
symbol rate and CFO range not given). This is NDA coarse search + a short candidate list + a known-symbol verifier.
- For the blind receiver: we already do the same with the decoder as verifier (peak-picked priors, Stage 2 metric,
  CRC + rho). **We already use it.** Nothing to switch to.
- For the competitors: our **16 + 16 4th-power receiver fails (BLER 0.5-0.9 below 0 dB) because it takes only the top
  peak.** A Viasat-faithful version keeps the top N = 8-32 4th-power peaks and picks by the 32-known-symbol correlation
  (and the 4 phase branches), optionally confirmed by CRC. This is a fairer "deployed" pilotless-burst competitor than
  the single-peak one. Expected: much better than "fails", but at -5 dB the 32 known symbols give a coherent
  correlation SNR of only 32 x 0.316 = 10 (10 dB) [derived], so wrong-candidate picks will remain; with a CRC check over
  the N candidates it becomes a cheap cousin of our blind receiver. Test: est4 variant `pp_topN` with N = 8, 32 at
  1/10 -5, 0.15 -3.5, 2/5 0.5, 1/2 2 dB, 480k packets, report BLER and MACs per core.

### T4. OneWeb (deployed, single-carrier QPSK) uses exactly our coarse stage: 4th-power periodogram, then a PLL
Komodromos & Humphreys 2025 (npj Wireless Technology): OneWeb Ku downlink is **single-carrier MF-TDMA, QPSK, 230.4
Msym/s, RRC roll-off 0.1**, 10 ms frames of 10 x 1 ms slots, a ~400-symbol sync sequence once per 1 ms slot
(400 / 230 400 = 0.17 % [derived]). Their receiver: TLE-predicted Doppler ("at most a few Hertz" error), **4th-power FFT
periodogram for the residual CFO, then a second-order PLL**. Ku Doppler +-280 kHz is only 1.2e-3 cycles/symbol at
230.4 Msym/s [derived] before compensation; the operating SNR is ~10 dB. Confirms our Stage 1 is the deployed
NDA baseline; nothing to borrow at -5 dB. The OneWeb **return link** waveform was not found in any source.

### T5. Static CFO over 1024 symbols holds for wideband bursts, not for narrowband IoT at our normalised CFO
Doppler rates: up to **594 Hz/s at 2 GHz, 600 km** (Chougrani et al. 2021). [derived] The quadratic phase over a
1024-symbol burst stays below 0.1 rad only if Rs > about 70 ksym/s at 2 GHz (594 Hz/s); scaling the rate with fc,
roughly Rs > 170 ksym/s at Ku and > 220 ksym/s at Ka. So:
- Systems that land near |f| = 0.03 with a **static** CFO: wideband single-carrier bursts without fine pre-compensation
  at Rs of about 1-16 Msym/s (DVB-RCS2-type MF-TDMA return links on LEO; the 0.5-3 % tolerance of TR 101 545-4 is the
  same regime), and narrowband links with Rs >= ~100 ksym/s after coarse pre-compensation.
- NB-IoT NTN single tone (3.75 kHz, residual +-200 Hz -> 0.053) and VDE-SAT (33.6 ksym/s, uncompensated +-4 kHz ->
  0.12; ship crystal 3 ppm = 480 Hz -> 0.014) have the right **size** of normalised CFO but drift within the packet
  (NB-IoT 3.75 kHz: 594 Hz/s x 0.273 s = 162 Hz = 0.043 cycles/symbol of drift over the burst [derived]).
- Recommendation (main session decides): one robustness point with a linear CFO ramp (Doppler rate) would make the
  claim "comparable to narrowband NTN" honest; e.g. drift 1e-5 cycles/symbol^2 x 1024 symbols = 0.01 total at 2/5 0.5 dB
  and 0.15 -3.5 dB, blind vs RCS2 ID 13 vs VDES-27. Not run.

---

## 2. Per-source table

Normalisation columns are **[derived]** unless the source states them.

| # | System / source | Band, Rs, waveform | Doppler handling | |f| before -> after compensation | Algorithm (known symbols) | Reported numbers | Comparable to our +-0.03 static, 1024 sym, -5..+3 dB? | Rel. |
|---|---|---|---|---|---|---|---|---|
| 1 | VDES / VDE-SAT, ITU-R M.2092-2 (2026) | VHF ~160 MHz; 2.1, 33.6 ksym/s (UL), 4.2-56.4 ksym/s (DL); pi/4-QPSK, 8PSK, 16QAM, BPSK/CDMA; turbo 1/4-5/6; RRC 0.25 | not specified; satellite carrier < 1 ppm; ship 1.5 / 3 ppm | +-4 kHz / 33.6 k = **0.12** -> crystal-only 3 ppm: **0.014** | 27-symbol syncword (pi/4-QPSK) or 48 (CDMA); pilots every 17, 27 or 33 symbols; DL syncword repeated every 1004-4214 symbols | AWGN thresholds Es/N0 -4.5, -3.6, -0.6 dB (Table 11), -0.9 ... 12.2 dB (UL Table 9); no CFO-estimator numbers | **Closest standard**: same SNR, QPSK, turbo low rate; CFO size right, but pilots present and drift at 33.6 ksym/s (594 Hz/s scaled to 160 MHz ~ 48 Hz/s: quadratic phase 0.004 rad, static OK [derived]) | high |
| 2 | OneWeb Ku downlink, Komodromos & Humphreys 2025 | 10.7-12.7 GHz, 230.4 Msym/s, single-carrier QPSK, RRC 0.1, MF-TDMA | TLE ephemeris prediction | 280 kHz / 230.4 M = **1.2e-3** -> few Hz (~1e-8) | ~400-symbol sync sequence per 1 ms slot; CFO by 4th-power FFT periodogram, 2nd-order PLL | SNR ~10.35 dB capture; no CFO accuracy figures | No: 25x smaller CFO, ~15 dB higher SNR. Confirms our Stage 1 | medium |
| 3 | Starlink Ku downlink, Humphreys et al. 2023 | 240 MHz OFDM, 1024 subcarriers, 234.375 kHz SCS, 302 symbols per 1/750 s frame | ephemeris prior + joint search over start index and Doppler beta (constellation-tightness metric) | +-300 kHz = 1.28 SCS | PSS (8 x 128-sample m-sequence repetition), SSS (4QAM OFDM symbol) | |beta| < 2.5e-5 bound | No (OFDM; one line of context). Uplink: OFDMA per an unverified SDR blog | low |
| 4 | 3GPP TS 38.101-5 cl. 6.4.1 (NR NTN UE) | S-band ~2 GHz; NR UL DFT-s-OFDM, SCS 15 kHz+ | GNSS + ephemeris pre-compensation by the UE | +-48 kHz / 15 k = 3.2 SCS -> **+-0.1 ppm = 200 Hz = 0.013 SCS** | DMRS-based (not specified) | requirement only | Residual per SCS is below ours; multicarrier; not comparable per symbol | medium |
| 5 | NB-IoT NTN random access, Chougrani et al. 2021 | 2 GHz, 600 km; NPRACH 3.75 kHz single-tone hopping | satellite + UE DL-based pre-compensation | +-41 kHz -> residual +-600 Hz (sim.) = **0.16 SCS** | differential processing of symbol groups cancels CFO; 256-pt DFT ToA, 62-pt DTFT Doppler-rate search; Doppler rate -101 ... -594 Hz/s | SNR for 1e-2 miss: 2.6-15.5 dB (32-64 reps); targets Pd 99 %, Pfa 0.1 %; Doppler-rate error 7.8-31 Hz/s at 99 % | No: preamble detection, not data decoding; CFO non-static | medium |
| 6 | NB-IoT NPUSCH F1 (primer 1606.04171; RF wireless world; Keysight help) | single tone 3.75 / 15 kHz, pi/2-BPSK, pi/4-QPSK | as #4 | residual 200 Hz: **0.053** (3.75 kHz), 0.013 (15 kHz) | 1 DMRS symbol per 7-symbol slot (14 % pilots) | none | CFO size near ours; pilots dense (14 %), drift large at 3.75 kHz (0.043 over 1024 symbols) | medium |
| 7 | Viasat US 8,243,859, Mo & Thesling 2012 | satellite bursts (rate, band not stated) | none stated | not stated | N-theta FFT -> top N peaks (32 of 1024) -> UW correlation over M timings -> weighted joint metric | burst recovery error < 1e-5 at 2.5 dB SNR | Concept yes (NDA FFT + candidate list + verifier); numbers not normalisable | high |
| 8 | Comtech US 8,451,947, Eymann & Reum 2013 | TDMA bursts < 2500 symbols, QPSK / 8PSK, short-block LDPC | DDS removes known systematic offset | transmit offsets ~6.25 % of Rs (= 0.0625) before removal | 64-symbol QPSK (128 8PSK) preamble = UW; feed-forward split-sum phase-difference estimator; split 8PSK preamble 2 x 64 separated by 192 symbols | first estimate within +-0.3 % of the offset; split preamble ~3x better at low SNR | Yes in CFO size; it is our 128-preamble / 64+64 competitor family | high |
| 9 | Hughes US 6,373,858 (1997/2002) | TDMA random access (cellular / satellite) | none | "wide range" | CW segment split half at start, half at end; DFT filter bank + CFAR; interpolation; hypothesis test on strongest peak + 2 neighbours; MMSE phase | only qualitative ("much smaller" RMS error for split); 10 dB between adjacent hypotheses | Same as our 64 + 64 + CRC lobe search; confirms it is the deployed design | medium-high |
| 10 | Hughes US 10,104,631, Lee, Chen, Liau 2018 | QPSK bursts, 2 samples/symbol | not read | not read | n parallel UW correlators, threshold, timing from peak and neighbour, phase from correlation | none in the part read (100k of 174k chars) | Partly | low-medium |
| 11 | Juniper US 7,187,731, Popper 2007 (DOCSIS ranging) | cable, QPSK, ~200-symbol bursts | none | not stated | 26-symbol preamble coarse + decision-directed on data with outlier rejection | target 1e-4 in df Ts; one decision error ~1e-3 | No (cable, high SNR) | low |
| 12 | Iridium (sigidwiki; gr-iridium README; snippets of an Iridium simplex patent) | L-band 1616-1626.5 MHz, 25 ksym/s DE-QPSK, 41.667 kHz channels, 8.28 ms bursts (~207 symbols) in 90 ms frames | subscriber unit pre-correction from position / downlink (Motorola US 5,119,504, snippet) | +-37 kHz / 25 k = **1.5** -> residual not published | 12-symbol BPSK unique word (preamble + UW + burst type 92 bits in BPSK at 25 ksym/s on simplex) | gr-iridium detection threshold 16-18 dB above noise | No: short differential bursts, high SNR, huge uncompensated CFO | low-medium |
| 13 | LR-FHSS sat-IoT (Lacuna / EchoStar class), Jung et al. 2023 | 900 MHz, GMSK BT 0.3, 488 Hz hops, 162 / 325 bit/s | none (channelizer + search) | +-20.7 kHz / 488 = ~42 | header: FFT channelizer + sync-word correlation, coarse + fine CFO (976/128 Hz res.), CRC-8 rejects false headers | header PER 1e-3 at ~6 dB SNR (perfect sync); Doppler rate 0-400 costs ~1.5 dB in miss detection | No (FSK-type, huge relative CFO) | low |
| 14 | AIS satellite (IEEE Access 2019 / Opt. Lett. 2018, snippets) | 162 MHz, GMSK 9600 bit/s | none | +-3.8-4 kHz / 9600 = **0.42**; ship 3 ppm 486 Hz = 0.05 | interpolated FFT on a GMSK-phase-removing auxiliary function; differential Viterbi | BER < 1e-3 (2-bit differential Viterbi); FFT estimator poor at low SNR with short FFT | No (GMSK, non-coherent) | low |
| 15 | Argos-4 (ARTIC R2 datasheet, snippet) | 401.65 MHz; HD 4800 / MD 1200 bit/s GMSK, VLD 200 bit/s BPSK | none (Doppler is the positioning observable) | +-9.2 kHz / 4800 = 1.9 (HD) | not read | none | No | low |
| 16 | ORBCOMM (patents US 7,289,533 and similar, snippets) | 148-150 MHz, SDPSK 2400 bit/s UL | none | +-3.4 kHz / 2400 = 1.4 | differential detection | none | No | low |
| 17 | ADS-B from space (Aireon patents, snippets; Ma et al. 2024 abstract) | 1090 MHz, PPM 1 Mbit/s | none | +-25 kHz / 1 M = **0.025** (lands on ours) | non-coherent / coherent matched filter on the 8 us preamble + first bits, CFAR | 96 % detection at "extremely low SNR" (abstract, value not given) | CFO size matches, but PPM energy detection: CFO barely matters; not comparable | low |
| 18 | Direct-to-cell (Rohde & Schwarz DTC page) | LTE / NR bands, unmodified phones | satellite pre-compensates DL and post-compensates UL relative to a fixed point per beam | residual grows off beam centre; not quantified | standard LTE / NR reference signals | none | No (OFDM / SC-FDMA, network-side compensation) | low |
| 19 | Ericsson CR R4-2216641 (2022, snippet) | NR NTN | source of the +-0.1 ppm / 1 ms rule in #4 | - | - | - | context for #4 | low |

**Not found / not readable:** any SpaceX patent on burst frequency acquisition (searches returned only SpaceX OFDM
uplink/downlink patents' titles, not read); the Amazon Kuiper, Globalstar, AST SpaceMobile, Lynk, Myriota,
Astrocast, Sateliot or Swarm physical layers with CFO-estimator numbers (no public technical documents found in the
searches made); the OneWeb return link; the Iridium air-interface specification and the ICAO AMS(R)S manual (404);
any NR PBCH / PDCCH paper that uses the polar code itself to estimate CFO (only DMRS / PSS-based papers, e.g. the IMDEA
blind NTN initial-access receiver, whose PDF could not be parsed); VDE-SAT receiver algorithm papers with CFO numbers.

---

## 3. What to add to our comparison (concrete competitors)

All follow the 8.2a rules (extra known symbols, energy charged, same back-end, CRC-16, CA-SCL-8, rho check).

| Name | Known symbols for 1024 data | Energy cost | Estimator | Source | Expected (rough, not simulated) |
|---|---|---|---|---|---|
| **VDES-27** | syncword 27 + 39 single pilots every 27 = 66 | 0.27 dB | R&B FFT over all known + parabolic interp. + CRC search over the 3 alias lobes (+-1/27) | ITU-R M.2092-2 | 2/5 1e-3 ~0.9-1.0 dB; 1/2 1e-3 ~2.2 dB; 1/10 1e-4 between -4.7 and -4.9 dB if the lobe search works |
| **PP-topN (Viasat style)** | pre 16 + post 16 = 32 | 0.13 dB | 4th-power FFT, top N = 8 / 32 peaks x 4 phases, pick by known-symbol correlation (joint weighted metric), optional CRC over the N | US 8,243,859 + our 16+16 | from "fails" to a usable curve at 2/5, 1/2; still weak at 1/10 -5 dB (known-symbol correlation SNR 10 dB) |
| **NB-IoT-DMRS-7** (optional) | 1 pilot per 7 symbols: 171 (data 6 of 7) | 0.69 dB | pilot-only R&B FFT, unambiguous to |f| < 1/14 = 0.071 > 0.03 | NPUSCH format 1 structure | no lobe or window losses (fixes ID 13's 0.2 % window misses at 1/10 -5 dB); ~genie + 0.7 dB everywhere: 1/10 1e-4 ~ -4.5 dB, 2/5 1e-3 ~1.35 dB |

The 128-preamble ML and 64 + 64 receivers already represent the Comtech / Hughes deployed preamble designs (#8, #9);
no change needed, but cite them as the deployed practice.

---

## 4. Per-component verdict against deployed practice

| Component | Ours | Deployed practice | Verdict |
|---|---|---|---|
| Coarse CFO | 4th-power FFT 4096 + parabolic | OneWeb: 4th-power periodogram (+ ephemeris); Viasat: N-theta FFT + top-N peaks | **we already use it** (fast path + peak-picked priors) |
| Fine CFO / phase | grid x list-1 metric, Stage 3, code-aided retry | PLL (OneWeb), known-symbol interpolation (Hughes, Comtech, VDES pilots) | ours is code-aided, beyond deployed; **nothing to borrow** for AWGN |
| Hypothesis search / verification | CFO cells x phases scored by SC metric, CRC + rho | Viasat: top-N frequency candidates verified by UW correlation; Hughes: 3-hypothesis test; NB-IoT: Doppler-rate DTFT search + threshold | **we already use it** (decoder as verifier instead of a UW) |
| Doppler pre-compensation | none (blind over +-0.03) | GNSS + ephemeris everywhere in 3GPP NTN (+-0.1 ppm); TLE in OneWeb / Starlink receivers | **not applicable** to the study (we model the residual); the residual itself is our CFO range |
| Doppler rate (CFO drift) | static CFO only | NB-IoT NTN explicitly estimates rate (62-pt DTFT); LR-FHSS tests 0-400 | **behind / untested**: one drift robustness point (T5) |
| Acceptance / false alarm | CRC-16 + rho | CRC-8 header (LR-FHSS), Pd 99 % / Pfa 0.1 % (NPRACH), UW threshold / CFAR (Hughes, Aireon) | ours is stricter; **we already use it** |

Comparability, plainly: none of the deployed systems publishes BLER for a polar code, a 1024-symbol burst or a static
CFO of +-0.03 at Es/N0 = -5 dB. VDE-SAT is the closest in SNR and modulation (turbo, not polar; pilots). All
"expected" numbers in sections 1 and 3 are my estimates from our measured 8.2a curves and have to be simulated.

---

## 5. Sources
- https://r.jina.ai/https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf (text of https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf)
- https://www.nature.com/articles/s44459-025-00013-y (read via r.jina.ai); https://radionavlab.ae.utexas.edu/wp-content/uploads/komodromos_oneweb_parameter_estimation.pdf
- https://arxiv.org/abs/2210.11578 (full text via r.jina.ai of https://arxiv.org/pdf/2210.11578v3)
- https://sdr-x.github.io/starlink4/
- https://itecspec.com/3gpp/38.101-5/s/6.4.1
- https://3gpp.org/ftp/tsg_ran/WG4_Radio/TSGR4_104bis-e/Inbox/Drafts/%5B104-bis-e%5D%5B304%5D%20NTN_Solutions_RF_Maintenance/Rnd2/revised%20R4-2216641%20(R17%20NTN)%20%20CR%20on%20NTN%20Frequency%20error%20requirement.docx
- https://ar5iv.labs.arxiv.org/html/2101.08079 and https://arxiv.org/abs/2101.08079
- https://arxiv.org/pdf/1606.04171 ; https://www.rfwireless-world.com/Terminology/LTE-NB-IoT-NPUSCH.html
- https://patents.google.com/patent/US8243859
- https://patents.google.com/patent/US8451947
- https://patents.google.com/patent/US6373858
- https://patents.google.com/patent/US10104631
- https://patents.google.com/patent/US7187731
- https://sigidwiki.com/wiki/Iridium ; https://github.com/muccc/gr-iridium ; https://patents.google.com/patent/US5119504
- https://ar5iv.labs.arxiv.org/html/2305.13779 and https://arxiv.org/abs/2305.13779
- https://www.researching.cn/ArticlePdf/m00050/2018/14/4/2018-04-0301.pdf (snippet); https://typeset.io/pdf/doppler-shift-estimation-for-space-based-ais-signals-over-4hg8qp05j8.pdf (snippet)
- https://learn.sparkfun.com/tutorials/argos-artic-r2-satellite-communication-guide/argos-message-formats (snippet); https://cdn.sparkfun.com/assets/c/0/8/d/4/ENA303_ARTIC_R2_User_Datasheet_1v10.pdf (snippet)
- https://patents.google.com/patent/US7289533 (snippet)
- https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9992011 (snippet); https://doaj.org/article/8e7ca9593699431490e67519889992f6 (snippet)
- https://www.rohde-schwarz.com/ca/_258609.html (snippet)

---

## Reference entries

### ITU-R Recommendation M.2092-2, "Technical characteristics for a VHF data exchange system in the VHF maritime mobile band", 02/2026
- Link: https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf   - Type: standard   - Read depth: full for Annex 2 Tables 9-11 and Annex 5 §A5-2 (text reader; some tables garbled)
#### What it does
VDE-SAT links: pi/4-QPSK / 8PSK / 16QAM / BPSK-CDMA, 2.1-56.4 ksym/s, RRC 0.25, turbo 1/4-5/6, CRC-16/32. Known symbols: 27-symbol (pi/4-QPSK) or 48-symbol (CDMA) syncwords, single pilots (1+j)/sqrt2 every 17, 27 or 33 symbols, DL syncword repeated every 1004-4214 symbols. AWGN Es/N0 thresholds -4.5, -3.6, -0.6 dB (Table 11). Doppler +-4 kHz at VHF, satellite carrier < 1 ppm. [derived] |f| = 0.12 at 33.6 ksym/s uncompensated; pilot-only range 1/54 = 0.0185.
#### What we took / could take
Basis of the proposed VDES-27 competitor (66 known symbols, 0.27 dB) in section 3.
#### Used in
-

### Z. M. Komodromos, T. E. Humphreys, "Signal parameter estimation and demodulation of the OneWeb Ku-band downlink", npj Wireless Technology, 2025, doi:10.1038/s44459-025-00013-y
- Link: https://www.nature.com/articles/s44459-025-00013-y   - Type: paper   - Read depth: full (text reader)
#### What it does
Shows OneWeb's downlink is single-carrier MF-TDMA QPSK, 230.4 Msym/s, RRC 0.1, 10 ms frames, ~400-symbol sync sequence per 1 ms slot. Doppler from TLE ("at most a few Hz" error), residual CFO by 4th-power FFT periodogram, then a 2nd-order PLL. SNR ~10 dB. [derived] |f| = 1.2e-3 before compensation.
#### What we took / could take
Confirms our Stage 1 (4th-power FFT) is the deployed coarse estimator; nothing new for low SNR.
#### Used in
-

### T. E. Humphreys, P. A. Iannucci, Z. M. Komodromos, A. M. Graff, "Signal Structure of the Starlink Ku-Band Downlink", IEEE Trans. Aerosp. Electron. Syst. 59(5), 2023 (arXiv 2210.11578)
- Link: https://arxiv.org/abs/2210.11578   - Type: paper   - Read depth: full (text reader)
#### What it does
Starlink Ku downlink is OFDM: 240 MHz, 1024 subcarriers, 234.375 kHz spacing, 302 symbols per 1/750 s frame; PSS = 8 repetitions of a 128-sample DPSK m-sequence, SSS = a 4QAM OFDM symbol. Doppler |beta| < 2.5e-5 handled by an ephemeris prior plus a joint start-index x Doppler search scored by constellation tightness.
#### What we took / could take
Not used: OFDM, high SNR. Context only (the joint search scored by a demodulation-quality metric is the same idea as our CFO grid scored by the SC metric).
#### Used in
-

### SDR-X blog, "Starlink uplink signal analysis (4): OFDMA and RU allocation"
- Link: https://sdr-x.github.io/starlink4/   - Type: app note (hobbyist analysis, unverified)   - Read depth: snippet
#### What it does
Reports the Starlink terminal uplink as OFDMA with resource units in multiples of 63 subcarriers, 8 channels of 62.5 MHz in 14.0-14.5 GHz (author's hypotheses).
#### What we took / could take
Not used: OFDMA uplink, so not a single-carrier comparison.
#### Used in
-

### 3GPP TS 38.101-5 (Rel-17), clause 6.4.1 "Frequency error" (NTN UE)
- Link: https://itecspec.com/3gpp/38.101-5/s/6.4.1   - Type: standard   - Read depth: full (clause)
#### What it does
NTN UE carrier must be within +-0.1 ppm of the ideally pre-compensated UL frequency (signalled UL carrier + UE's pre-compensated Doppler), averaged over 1 ms of UL slots. [derived] 200 Hz at 2 GHz: 0.013 of 15 kHz SCS, 0.053 of a 3.75 kHz NB-IoT single tone.
#### What we took / could take
Defines the residual CFO of real NTN uplinks; frames our +-0.03 as a post-pre-compensation residual for narrowband links.
#### Used in
-

### Ericsson, R4-2216641, "CR on NTN frequency error requirement" (3GPP RAN4 #104bis-e), 2022
- Link: https://3gpp.org/ftp/tsg_ran/WG4_Radio/TSGR4_104bis-e/Inbox/Drafts/%5B104-bis-e%5D%5B304%5D%20NTN_Solutions_RF_Maintenance/Rnd2/revised%20R4-2216641%20(R17%20NTN)%20%20CR%20on%20NTN%20Frequency%20error%20requirement.docx   - Type: standard (change request)   - Read depth: snippet
#### What it does
Proposed the +-0.1 ppm / 1 ms rule now in TS 38.101-5 cl. 6.4.1.
#### What we took / could take
Context only.
#### Used in
-

### H. Chougrani, S. Kisseleff, W. A. Martins, S. Chatzinotas, "NB-IoT Random Access for Non-Terrestrial Networks: Preamble Detection and Uplink Synchronization", arXiv 2101.08079, 2021
- Link: https://ar5iv.labs.arxiv.org/html/2101.08079   - Type: paper   - Read depth: full
#### What it does
2 GHz, 600 km LEO, NPRACH format 1 (3.75 kHz). Doppler up to +-41 kHz, Doppler rate -101 to -594 Hz/s; residual after pre-compensation +-600 Hz (simulated uniform). Differential symbol-group processing cancels CFO; 256-point DFT for ToA, 62-point DTFT Doppler-rate search, non-coherent combining over repetitions. SNR for 1e-2 miss: 2.6-15.5 dB (32 / 64 repetitions); targets Pd 99 %, Pfa 0.1 %; Doppler-rate error 7.8-31 Hz/s at 99 %. No CFO RMSE reported.
#### What we took / could take
The Doppler rate figure is the basis of the drift / static-CFO criterion (T5) and the suggested drift robustness test.
#### Used in
-

### Authors not verified (listed by the agent as Y.-P. E. Wang et al.), "A Primer on 3GPP Narrowband Internet of Things (NB-IoT)", arXiv 1606.04171, 2016 (with RF Wireless World NPUSCH page)
- Link: https://arxiv.org/pdf/1606.04171   - Type: paper / app note   - Read depth: snippet
#### What it does
NPUSCH format 1 single tone (3.75 / 15 kHz), pi/2-BPSK / pi/4-QPSK; one DMRS symbol (the middle one) per 7-symbol slot.
#### What we took / could take
Basis of the optional NB-IoT-DMRS-7 competitor (171 pilots, 0.69 dB, unambiguous to 0.071).
#### Used in
-

### F. Mo, W. H. Thesling (Viasat), "Joint frequency and unique word detection", US 8,243,859 B2, 2012
- Link: https://patents.google.com/patent/US8243859   - Type: patent   - Read depth: full (151k characters, in two parts)
#### What it does
N-theta FFT over the burst, top N peaks (example 32 of 1024 bins), frequency-correct each, UW correlation over M timing hypotheses, weighted joint frequency + UW metric, optional second preamble FFT; N adapted to link conditions. Burst recovery error < 1e-5 at 2.5 dB SNR. UW length, symbol rate and CFO range not stated.
#### What we took / could take
Blind receiver: same architecture as ours (we already use it). Competitor: PP-topN (16 + 16 known, top-N 4th-power peaks).
#### Used in
-

### S. Eymann, P. Reum (Comtech EF Data), "Burst demodulator", US 8,451,947 B2, 2013
- Link: https://patents.google.com/patent/US8451947   - Type: patent   - Read depth: full (description)
#### What it does
Feed-forward TDMA burst demodulator (bursts < 2500 symbols, short LDPC): 64-symbol QPSK (128 8PSK) preamble doubling as UW, data-aided split-sum phase-difference frequency estimator; transmit offsets about 6.25 % of Rs removed by DDS first; first estimate within +-0.3 % of the offset; splitting the 8PSK preamble into 2 x 64 separated by 192 symbols gives ~3x better frequency estimates at low SNR.
#### What we took / could take
Shows our 128-preamble and 64 + 64 competitors are the deployed preamble designs; supports split placement.
#### Used in
-

### Hughes Electronics, "Burst format and method for improving frequency and timing estimation on random access channels", US 6,373,858 B1, 2002 (priority 1997)
- Link: https://patents.google.com/patent/US6373858   - Type: patent   - Read depth: full (description)
#### What it does
CW segment split half at the start and half at the end of a random-access burst; DFT filter bank + CFAR detection, interpolated fine frequency, multiple-hypothesis test on the strongest peak and its two neighbours, MMSE phase. Qualitative gain only.
#### What we took / could take
Same as our 64 + 64 joint ML + CRC lobe search; cite as deployed practice.
#### Used in
-

### L.-N. Lee, L. Chen, V. Liau (Hughes Network Systems), "Unique word (UW) based multiple access signal acquisition technique", US 10,104,631 B2, 2018
- Link: https://patents.google.com/patent/US10104631   - Type: patent   - Read depth: 100k of 174k characters
#### What it does
QPSK bursts with a UW; n parallel UW correlators at 2 samples/symbol over a timing window, threshold detection, timing from the peak and its neighbour, phase and power from the correlator. No frequency-range or SNR numbers in the part read.
#### What we took / could take
Not used: no CFO numbers; context for UW-based acquisition.
#### Used in
-

### A. Popper (Juniper Networks), "Precise frequency estimation of short data bursts", US 7,187,731 B2, 2007
- Link: https://patents.google.com/patent/US7187731   - Type: patent   - Read depth: full (description)
#### What it does
DOCSIS CMTS ranging bursts (~200 QPSK symbols, 26-symbol preamble): preamble coarse estimate, then decision-directed refinement on data with outlier rejection; target 1e-4 in df Ts.
#### What we took / could take
Not used: cable, high SNR.
#### Used in
-

### Signal Identification Wiki, "Iridium"
- Link: https://sigidwiki.com/wiki/Iridium   - Type: app note (community wiki)   - Read depth: full
#### What it does
Iridium: DE-QPSK, 25 ksym/s, 41.667 kHz channels, 1616-1626.5 MHz, 8.28 ms bursts in 90 ms TDMA frames. [derived] Doppler +-37 kHz = 1.5 cycles/symbol uncompensated.
#### What we took / could take
Not used: short differential bursts, CFO pre-corrected by the subscriber unit.
#### Used in
-

### muccc, gr-iridium (GNU Radio Iridium burst detector / demodulator), README
- Link: https://github.com/muccc/gr-iridium   - Type: app note (open-source software)   - Read depth: full (README only)
#### What it does
Overlapping polyphase channelizer "to account for Doppler shift"; timing on the 12-symbol BPSK sync word; detection threshold 16-18 dB above noise.
#### What we took / could take
Not used: high-SNR passive receiver.
#### Used in
-

### Motorola, "Position aided subscriber unit for a satellite cellular system", US 5,119,504, 1992
- Link: https://patents.google.com/patent/US5119504   - Type: patent   - Read depth: snippet
#### What it does
Subscriber unit uses its own position to pre-correct Doppler and reference-frequency error for Iridium-type LEO acquisition.
#### What we took / could take
Context: deployed LEO systems pre-correct rather than search blindly.
#### Used in
-

### S. Jung, S. Jeong, J. Kang, J. G. Ryu, J. Kang, "Transceiver Design and Performance Analysis for LR-FHSS-based Direct-to-Satellite IoT", arXiv 2305.13779, 2023
- Link: https://ar5iv.labs.arxiv.org/html/2305.13779   - Type: paper   - Read depth: full
#### What it does
900 MHz LR-FHSS, GMSK BT 0.3 (and QPSK), 488 Hz hops; header detection by FFT channelizer + sync-word 0x2C0F7995 correlation, coarse/fine CFO, CRC-8 rejects false headers. Header PER 1e-3 at ~6 dB SNR (perfect sync); Doppler rate 0-400 costs ~1.5 dB in miss detection.
#### What we took / could take
Not used: FSK-type, relative CFO ~40 cycles/symbol.
#### Used in
-

### Satellite AIS frequency-offset papers (Optoelectronics Letters 14(4), 2018; IEEE Access 2019, per search index)
- Link: https://www.researching.cn/ArticlePdf/m00050/2018/14/4/2018-04-0301.pdf   - Type: paper   - Read depth: snippet
#### What it does
Space-based AIS (162 MHz, GMSK 9600 bit/s): LEO Doppler +-3.8-4 kHz beyond the 3 ppm (486 Hz) receiver tolerance; interpolated-FFT estimators and differential Viterbi detection (BER < 1e-3). [derived] |f| = 0.42 cycles/bit.
#### What we took / could take
Not used: GMSK, non-coherent.
#### Used in
-

### ARTIC R2 Argos chipset datasheet (ENA303) and SparkFun Argos guide
- Link: https://cdn.sparkfun.com/assets/c/0/8/d/4/ENA303_ARTIC_R2_User_Datasheet_1v10.pdf   - Type: app note   - Read depth: snippet
#### What it does
Argos-4 uplinks: HD 4800 bit/s and MD 1200 bit/s GMSK, VLD 200 bit/s BPSK, 401.65 MHz. [derived] Doppler +-9.2 kHz = 1.9 cycles/bit at HD.
#### What we took / could take
Not used.
#### Used in
-

### ORBCOMM subscriber communicator patents (e.g. US 7,289,533)
- Link: https://patents.google.com/patent/US7289533   - Type: patent   - Read depth: snippet
#### What it does
ORBCOMM uplink SDPSK 2400 bit/s at 148-150 MHz. [derived] Doppler +-3.4 kHz = 1.4 cycles/symbol.
#### What we took / could take
Not used: differential, narrowband.
#### Used in
-

### Aireon, "Receiver with coherent matched filter", US 9,992,011 (family), and Ma et al., Int. J. Aerospace Eng. 2024 (two-stage satellite ADS-B preamble synchronization)
- Link: https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9992011 ; https://doaj.org/article/8e7ca9593699431490e67519889992f6   - Type: patent / paper   - Read depth: snippet / abstract snippet
#### What it does
Space-based ADS-B (1090 MHz, PPM 1 Mbit/s): matched filter on the preamble + first data bits, CFAR; 96 % detection at very low SNR (value not given in the snippet). [derived] Doppler +-25 kHz = 0.025 cycles/bit, but PPM energy detection is CFO-insensitive.
#### What we took / could take
Not used: not coherent PSK.
#### Used in
-

### Rohde & Schwarz, "Direct-to-cell technology" (web page)
- Link: https://www.rohde-schwarz.com/ca/_258609.html   - Type: app note   - Read depth: snippet
#### What it does
Direct-to-cell LEO: satellite pre-compensates DL and post-compensates UL Doppler (carrier and sampling) relative to a fixed point per narrow beam; residual grows off the beam centre (not quantified).
#### What we took / could take
Not used: OFDM / SC-FDMA, network-side compensation.
#### Used in
-
