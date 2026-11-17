# Competitor cards: CCSDS telemetry (131.0, 131.2, 130.11, 401, ground receivers) and VDE-SAT (ITU-R M.2092-2)

Literature scout, 2026-11-15. No simulations were run, and no code or REFERENCES.md was edited. Code rates and MODCOD
thresholds belong to `lit_rates.md`. They appear here only where a sync statement needs them.

**How the sources were read.** CCSDS, ITU and JPL PDFs were read through the public text reader r.jina.ai, given only
the public URL. Tables come out flattened, so every table value below carries a confidence note. Vendor datasheets
were read in full as PDFs. IEEE Xplore, Wiley, ResearchGate, MDPI and EBSCO returned 403 or empty pages, so for those
papers only metadata (from Crossref) and search-engine abstract excerpts were seen. One fetch of an IET PDF crawler URL
was refused by the permission system and was not retried.

**Labels.** [std] = standard or agency handbook; [paper]; [vendor]; [snippet] = a search-engine excerpt, not the
document itself; [derived] = my arithmetic from the cited numbers. f = CFO / Rs in cycles per symbol (ours: |f| <= 0.03).

---

## 0. Summary per system

- **CCSDS 131.0 (TM sync and channel coding, continuous telemetry).** The only known symbols are the Attached Sync
  Marker (ASM) before every codeblock. There are no pilots. The (2048,1024) rate-1/2 AR4JA LDPC block uses a 64-bit
  ASM (`034776C7272895B0`), which is 32 QPSK symbols per 1024 code symbols (3.0 % known, 0.13 dB). That is exactly our
  N = 2048 block. Carrier sync is left to a continuous Costas or PLL receiver: DSN loop BL <= min(200 Hz, Rs/20),
  acquisition after an FFT search and predicts, "often about one minute or less" [std]. There is no single-burst
  estimator and no code-aided step. The CSM / ASM may resolve the phase ambiguity [std].
- **CCSDS 131.2 SCCC (and the 130.11-G-2 reference receiver).** Frame = 320-symbol pi/2-BPSK header (256-symbol frame
  marker + 64-symbol descriptor) + 16 codeword sections, each with 15 x (540 data + 16 pilots). Total 133 760 symbols,
  3.06 % known [std + derived]. The reference receiver uses a frame-level FLL (1024-point FFT of the frame marker +
  Newton interpolation, k1 = 0.2), DA ML phase per 16-symbol field with linear interpolation, and no code-aided step.
  Sync loss vs ideal is 0.2-0.4 dB at CER 1e-4. The lowest ModCod is at Es/N0 -0.58 dB [std]. Acquisition was not
  simulated [std]. **Our C8 has 3.7x the real pilot density.** A 1024-data window of the real stream holds only about
  2 pilot fields (about 30 known symbols, aliases every 1/556 = 0.0018).
- **CCSDS 401.0-B-32 (RF and modulation).** Earth-station acquisition sweeps of +-150 kHz (2 GHz) to +-1.8 MHz (26 GHz)
  for near-Earth links, carrier-loop 2B_LO of 30 Hz-2 kHz [std]. The CFO is handled by sweeps and PLL / Costas loops
  over seconds, never in one burst.
- **Ground receivers.** NASA DSN Receiver and Ranging Processor: Costas or QPSK loops, loop SNR >= 23 dB for QPSK, lock
  time ~20/BL, typical acquisition about 1 min [std]. ESA TTCP: suppressed-carrier BPSK / QPSK / OQPSK / GMSK; its
  acquisition parameters were not found. Safran Cortex CRT (4000+ units): acquisition threshold Es/N0 < -2 dB, BER
  degradation < 0.5 dB typical, Doppler compensation [vendor]. Cortex HDR (1000+ units, SCCC / DVB-S2 / AR4JA LDPC):
  no sync numbers [vendor]. Kongsberg HRDFEP (131.2-B-2): implementation loss < 0.5 dB, Doppler 1500 kHz [snippet
  only].
- **VDE-SAT (ITU-R M.2092-2, 02/2026).** The downlink format SAT-MCS-1.50-1 (Link ID 26, 50 kHz channel) is
  confirmed. It is pi/4-QPSK at 33.6 ksym/s with a 27-symbol syncword every 2268 symbols and one pilot every 27 symbols
  (first pilot 14 symbols after the syncword). There is **no link ID** on the downlink, the **ramp is 14 + 14 symbols**,
  and a burst is 80 371 symbols (2392 ms). Known symbols are 4.8 % (0.21 dB) [std + derived]. Its AWGN design point
  is **Es/N0 -2.4 dB** [std, column alignment checked through C/(N0+I0) = 42.9 dB-Hz]. The -4.5 dB format is a
  different layout: BPSK/CDMA SF 8, 48-symbol syncwords, a pilot every 8 symbols, 22.7 % known. Doppler is up to
  +-4 kHz plus a 1 ppm (160 Hz) satellite error, i.e. **f up to 0.124** [std + derived]. The only VDES CFO paper is
  Ma, Shi, Meng, Li (IEEE ICCC **2018**): a bank of Doppler-shifted correlators, then an autocorrelation-argument fine
  stage, +-4000 Hz, "approximate to the CRB" [snippet of the abstract]. The field trials are the NorSat-2 ESA downlink
  verification (2017-18, Kongsberg Seatex receivers, 103 passes, MATLAB software demodulator; no numbers published on
  the page) and Andreotti et al. 2021/2023 (uplink Link ID 20 RA bursts, up to 22 overlapping messages demodulated;
  estimator "e.g. Rife-Boorstyn" on preamble / pilots [snippet]).

### Contradictions with competitors.md and lit_vdesat_format.md

1. **competitors.md C6 "its own thresholds Es/N0 -4.5 ... -0.6 dB" overstates the 27/27 layout.** The 27-syncword +
   27-pilot formats are designed for Es/N0 -2.4 dB (SAT-MCS-1.50-1, Table 10) and -0.6 dB (Table 11, Link 34). The
   -4.5 dB format (Table 11, Link 32) uses BPSK/CDMA SF 8, 48-symbol syncwords and a pilot every 8 symbols (372 known
   of 1641, 1.12 dB). So at our 1/10 -5 dB and 0.15 -3.5 dB points, C6 runs its comb 1-2.6 dB below the standard's
   design SNR for it. That is fair to state, but "designed for our SNRs" should name the format. (Rates and thresholds
   are for `lit_rates.md` to confirm; the alignment checks are in card 3.)
2. **competitors.md C8 "8 blocks x 16, 128 (0.52 dB)" is described as the 131.2 layout, but real 131.2 has 16 pilots
   per 540 data symbols.** That is about 30 known per 1024 data, 0.13 dB, aliases at 1/556, plus a 256-symbol frame
   marker only once per 133 760 symbols. Our C8 has 3.7x more pilot energy than the standard and a 3.4x wider alias
   spacing (1/162 vs 1/556). It is "CCSDS-style blocks", not the 131.2 density. Say so in the deviations table.
3. **competitors.md C8 "block period ~146: aliases every ~0.0068":** 146 is the data gap. The block period is 162.3
   (as in expected_est5.md and est4/common.py), so the aliases are every 1/162.3 = 0.0062 [derived]. Small typo.
4. **competitors.md C8 deviation "real acquisition range smaller":** this holds only for the 130.11-G-2 test case
   (f = 0.01-0.02 at 100 MBaud). Bertolucci et al. 2021 design the same 131.2 receiver for Doppler of about 20 % of Rs
   at 5 Mbaud. The real range is larger than ours at low baud, but it is acquired by a multi-frame FLL, not in one
   burst.
5. **lit_vdesat_format.md open items, now resolved (medium-high confidence):** (a) the link ID size for SAT-MCS-1.50-1
   is 0 / N/A (Table 10: "Link ID size 0 (N/A)" for the downlink formats); (b) the data modulation is pi/4-QPSK
   (channel bits 152 915 = 2 x 76 458 net symbols); 3.50-1 is 8PSK (229 368 = 3 x 76 456); (c) the ramp is 14 / 14
   symbols = 0.41 ms each at 33.6 ksym/s. The 30/30 and 47/47 values belong to the 72 / 112.8 kchip/s formats, and the
   totals close: 945 + 2940 + 76 458 + 28 = 80 371. Burst duration 2392.0 ms + 8 ms guard = 90 slots. All of these
   agree with lit_vdesat_format.md's inferences.
6. **New detail not in lit_vdesat_format.md:** with pi/4-QPSK, "single pilots at odd positions are offset by pi/4"
   (A5-2.10). So the pilot value alternates between two points. This does not matter for DA estimation (known
   symbols), and our `make_burst` repeating one random QPSK symbol is equivalent.
7. **lit_vdesat_format.md says the link ID exists "in other formats" (16 symbols).** The arithmetic of uplink Table 9
   confirms it for the 33.6 ksym/s uplink formats: 27 + 16 + 556 + 28 = 627 and 27 + 16 + 71 + 2277 + 28 = 2419
   symbols per burst [derived from flattened cells]. It is absent on every downlink format.
8. **REFERENCES.md C17 metadata:** the paper is from Dec 2018, not "about 2019". It is S. Ma, K. Shi, X. Meng, X. Li,
   2018 IEEE 4th Int. Conf. on Computer and Communications (ICCC), pp. 1234-1238, doi:10.1109/CompComm.2018.8780774
   (Crossref). Its fine stage is an autocorrelation-argument estimator after coarse correlation-bank compensation, not
   R-B. Our C6 (ML syncword + R-B on all known symbols) is at least as accurate, so the claim "C6 is not a weakened
   competitor" stands.
9. **Naming ambiguity in M.2092-2 (flag, not resolved):** the extraction shows "SAT-MCS-1.50-2" both as uplink Link 20
   (Table 9, CDMA SF 16) and as a Table 11 downlink column (Link 34, pi/4-QPSK, 27/27). The Table 11 parameters close
   arithmetically (162 + 480 + 12 480 + 28 = 13 150), but the format name of that column needs a PDF viewer.

---

## 1. Ranked actionable findings (the main session decides)

1. **Relabel C6 and give its design SNR** (competitors.md C6 row and the deviations table): "SAT-MCS-1.50-1 comb (27
   syncword + 1 pilot / 27), designed for Es/N0 -2.4 dB; the standard's -4.5 dB format uses 23 % known symbols". There
   is no simulation cost. Source: [M.2092-2](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf),
   Tables 10-11.
2. **Relabel C8 as "CCSDS-style blocks (3.7x the 131.2 pilot density)"** and fix the 0.0068 typo. Optional test of
   the faithful density: a layout `cc131` = 1024 data with 16-symbol pilot fields every 540 data symbols (2 fields,
   32 known, 0.13 dB, alias 1/556), R-B + lobe search, at 2/5 0.5 dB and 1/2 2 dB, 480k packets. Prediction [rough]:
   lobe errors like or worse than split64 (55-60 % wrong lobe below -4 dB). It works at 2/5 and 1/2 only if the lobe
   search covers +-0.03 / 0.0018 = +-17 lobes, which is expensive. This shows why the real receiver needs a multi-frame
   FLL. Source: [CCSDS 131.2-B-2](https://public.ccsds.org/Pubs/131x2b2.pdf) 5.3.4.
3. **A CCSDS 131.0 "ASM-only" competitor is the most faithful CCSDS single-codeword layout**: (2048,1024) AR4JA LDPC +
   64-bit ASM = 32 QPSK symbols before each 1024-symbol codeblock. In a stream, the next block's ASM follows, so a
   block sees 32 + 32 known symbols at a distance of 1056 (charged 32 known = 0.13 dB, since ASMs are shared, or 64 =
   0.27 dB as an isolated burst). est4 already has the neighbours `16 + 16` (4th power, fails below 0 dB) and `64 + 64`
   joint ML (-2.87 dB at 1/10 1e-4 from lobe errors). A `asm32` (32 + 32 ML + lobe search) would sit between them
   [rough], so at most relabel C2 / C4 as "CCSDS 131.0 ASM-like". A run is optional: 2/5 0.5 dB, 1/2 2 dB and 0.15
   -3.5 dB, 480k packets. Source: [CCSDS 131.0-B-5](https://public.ccsds.org/Pubs/131x0b5.pdf) 7.2.1.2, 9.3.4, Table 7-5.
4. **Do not add a VDE-SAT low-SNR (pilot every 8) variant.** At 1024 data symbols it would be about 146 pilots + 2 x 48
   syncword symbols, about 242 known (0.92 dB) [derived]. That is C10 (DMRS 1/7, 0.67 dB) plus 0.25 dB more energy, so
   it would land just behind C10 [rough]. Instead, cite C10 as also representing VDE-SAT Link 32's dense-pilot design.
   Source: M.2092-2 Table 11.
5. **Fix REFERENCES.md C17** (2018 ICCC, authors, DOI; fine stage = autocorrelation argument), and add the Cortex CRT
   datasheet as the vendor evidence for "space TT&C modems acquire down to Es/N0 -2 dB with < 0.5 dB loss" (the only
   vendor low-SNR acquisition number found). Sources: [Crossref record](https://api.crossref.org/works?query.bibliographic=Frequency+Offset+Estimation+Algorithm+of+VDES+Signals+Based+on+Cross-Correlation&rows=3),
   [Cortex CRT](https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20CRT%20-%20Datasheet.pdf).

---

## 2. Card 1: CCSDS 131.0 TM synchronization and channel coding (+ 401 RF, 130.1 rationale)

**1. Standard and deployments.**
- CCSDS 131.0-B-5, *TM Synchronization and Channel Coding*, Blue Book Issue 5, Sept 2023
  ([PDF](https://public.ccsds.org/Pubs/131x0b5.pdf)) [std]. RF / modulation through CCSDS 401.0-B-32 (Oct 2021)
  ([PDF](https://public.ccsds.org/Pubs/401x0b32.pdf)) [std]. Rationale in CCSDS 130.1-G-3 (2020, EC1 2024), which
  assumes no sync losses (read by lit_real_space.md; not re-read here).
- Link: spacecraft-to-ground telemetry, near-Earth (Category A, < 2e6 km) and deep space (Category B), continuous
  stream of codeblocks.
- Deployments: essentially all CCSDS agency missions use 131.0 telemetry (convolutional, RS, turbo or LDPC). Named
  missions using the (2048,1024) AR4JA code specifically: **not found**. Vendors sell AR4JA IP for "real-time telemetry"
  (IPrium, Creonic; [snippet]). Ground: NASA DSN, ESA ESTRACK, commercial stations with Safran Cortex / Kongsberg
  receivers (card 2b).

**2. Frame structure (known symbols).**
| Coding | ASM | ASM in symbols | Block (code symbols) | Known fraction | Source |
|---|---|---|---|---|---|
| uncoded / conv. / RS / LDPC 7/8 | 32 bit `1ACFFC1D` | 16 (QPSK) / 32 (BPSK) | e.g. LDPC (8160,7136) | 0.4 % | 131.0 9.3.1 [std] |
| turbo r 1/2 | 64 bit `034776C7272895B0` | 32 / 64 | 3576 (k = 1784) ... | 1.8 % | 6.3, 9.3.4 [std] |
| turbo r 1/3, 1/4, 1/6 | 96 / 128 / 192 bit | 48-96 (QPSK) | 32/r ASM | | 9.3.2 [std] |
| **LDPC k = 1024, r = 1/2** | **64 bit** `034776C7272895B0` | **32 QPSK** | **2048** | **32 / 1056 = 3.0 %, 0.13 dB** [derived] | 7.2.1.2, Table 7-5 [std] |
| LDPC k = 1024, r 2/3, 4/5 | 64 bit | 32 QPSK | 1536, 1280 | 4.0 %, 4.8 % [derived] | Table 7-5 [std] |
- No pilots anywhere in 131.0 (none in the text read). The ASM is not randomized (10.3.4 note); the data are randomized
  (131 071-bit long randomizer, default required).
- Modulation: BPSK / QPSK / OQPSK / GMSK / 8PSK per 401; LDPC needs >= 2 code symbols per modulation symbol (13.3.1).
  The ASM bits are mapped like data (BPSK or QPSK), so on QPSK they are 32 known QPSK symbols.
- **Closest to our burst:** the (2048,1024) LDPC codeblock, 1024 QPSK symbols + a 32-symbol ASM. In a stream, each
  codeblock sits between two ASMs, 1056 symbols apart.

**3. Synchronization in practice.**
- The known symbols (ASM) are for frame / codeblock sync and phase-ambiguity resolution ("phase ambiguities have to be
  detected and resolved before decoding"; the CSM "can be used to resolve phase ambiguities", 8.2.2) [std]. They are
  not intended for carrier estimation.
- Carrier: continuous suppressed-carrier Costas / QPSK loops (DSN, card 2b). Acquisition by a ground sweep and FFT
  against Doppler predicts [std 401, DSN 207].
- 401 acquisition requirements [std]: Earth-station receiver sweep of at least +-150 kHz at 2 GHz, +-600 kHz at 8 GHz,
  +-1800 kHz at 26 GHz (Cat A, 2.3.3A); +-300 kHz / +-1 MHz / +-4 MHz at 2 / 8 / 32 GHz (Cat B). Sweep rates 100 Hz/s
  to >= 200 kHz/s (Cat A). Doppler rates up to 3 / 10 / 34 kHz/s one-way (2 / 8 / 26 GHz). Telemetry receiver loop
  2B_LO 30 Hz-2 kHz (Cat A), 1 Hz-1 kHz (Cat B). Suppressed-carrier symbol-rate limits 2 Msps (2 and 8 GHz),
  10 Msps (26 GHz), 20 Msps (32 GHz).
- As a fraction of Rs [derived]: +-150 kHz at 2 Msps = 0.075; +-600 kHz at 2 Msps = 0.3; +-1.8 MHz at 10 Msps = 0.18.
  These are above our 0.03, but they are swept and tracked over seconds with Doppler predicts, not estimated per block.
- Phase noise: 401 phase-noise rules were not visible in the read part. DSN models sigma_phi^2 = 1/rho_L + sigma_U^2 +
  sigma_T^2 (transmitter and solar terms) [std, DSN 207].

**4. Published sync performance.** 131.0 itself: none ("assume no synchronization losses", 130.1-G-3 via
lit_real_space.md). For receiver numbers see card 2b. Frame-sync performance: not given in 131.0-B-5.

**5. Complexity.** Not in the standard. The ASM correlation is 32 complex MACs per lag [derived].

**6. Code-aided step.** None in the standard. 13.2.2 note 2: a low-rate turbo code near threshold "may need" a narrow
symbol loop and external Doppler compensation [std].

**7. Our version.** We do not simulate a "CCSDS 131.0" competitor by name. The nearest est4 receivers are `16 + 16`
(C2, 4th power) and `64 + 64` (C4, joint ML), which bracket a 32 + 32 ASM layout. A real 131.0 receiver is much stronger
than any single-burst version, because its carrier loop has been locked for seconds before the codeblock arrives. The
single-burst comparison is therefore a model of the ASM's information content only (finding 3).

---

## 3. Card 2: CCSDS 131.2 SCCC with pilots (+ 130.11-G-2 reference receiver)

**1. Standard and deployments.**
- CCSDS 131.2-B-2, *Flexible Advanced Coding and Modulation Scheme for High Rate Telemetry Applications*, Blue Book
  Issue 2, Feb 2023 ([PDF](https://public.ccsds.org/Pubs/131x2b2.pdf)) [std]. ISO 17854 = 131.2-B-1 (2012).
- CCSDS 130.11-G-2, *SCCC Summary of Definition and Performance*, Green Book Issue 2, May 2023
  ([PDF](https://public.ccsds.org/Pubs/130x11g2.pdf)) [std].
- Link: high-rate Earth-observation payload downlink (X / K-band, up to 500 MBaud), 27 ACM formats QPSK ... 64APSK.
- Deployments: the hardware validation used a Tesat Spacecomm EM transmitter and a Kongsberg Spacetec receiver at
  500 MBaud, K-band 26.25 GHz (130.11-G-2 sec. 7) [std]. ESA SCCC IP cores exist (ESA pages, [snippet]). Commercial
  ground receivers: Safran Cortex HDR (SCCC decoding listed) [vendor], Kongsberg HRDFEP (131.2-B-2) [snippet]. Named
  flight missions: **not found** (130.11-G-2 names none).

**2. Frame structure.**
| Element | Length (symbols) | Modulation | Position | Source |
|---|---|---|---|---|
| Frame marker (FM) | 256 | pi/2-BPSK, Gold sequence | frame start | 131.2 5.3.1-5.3.2 [std] |
| Frame descriptor (FD) | 64 | pi/2-BPSK, 7 bits -> (32,6) biorthogonal + repetition (the text has two descriptions) | after the FM | 5.3.3 [std] |
| Codeword sections | 16 x 8100 data symbols | QPSK ... 64APSK | after the header | 5.3.4 [std] |
| Pilot fields (if b6 = on) | 16 every 540 data symbols (15 per section, 240 per section) | unmodulated (1+j)/sqrt2, then PL-scrambled (known pseudo-random QPSK after scrambling) | after each 540 data | 5.3.4.2-3, 5.5 [std] |
| Frame total | 133 760 with pilots, 129 920 without | | | [derived from std] |
- Known fraction: (256 + 3840) / 133 760 = 3.06 % (3.11 % with the FD), energy 10 log10(133 760 / 129 600) = 0.14 dB
  [derived]. 130.11-G-2 quotes "about 0.15 dB" of header + pilot overhead [std].
- **Closest to our burst:** one 540 + 16 subsection is 556 symbols. A 1024-data window holds 1.9 pilot fields (about
  30 known, 0.13 dB) and no frame marker, except in 1 window in about 130.
- Pilot-comb alias spacing 1/556 = 1.8e-3; FM-to-FM spacing 1/133 760 = 7.5e-6 [derived].

**3. Synchronization in practice (130.11-G-2 sec. 5).**
- Known symbols: the FM for frame sync, SNR estimation / DAGC and the frequency detector; FM + pilots for phase.
- Frequency: a 2nd-order digital FLL at frame rate. The detector is a 1024-point FFT of the modulation-removed 256 FM
  symbols, argmax + Newton interpolation. B_L ~ R_FM (k1 + k2)/4, R_FM = Rs/133 760. First-order k1 = 0.2 is enough
  for f_D = 1 MHz and 50 kHz/s at 100 MBaud. B_L < 186.9 Hz, SNR_FLL > 29.5 dB [std]. The FFT range is about +-Rs/2
  (bin Rs/1024) [derived by the reader, not stated].
- Phase: DA ML per 16-symbol block (FM) and per pilot field, linear interpolation between fields 540 apart. No
  decision-directed step. The report calls it suboptimal and suggests a DA / DD PLL as an improvement [std].
- Acquisition vs tracking: timing (Gardner suggested) and FM acquisition were **not simulated** [std]. MathWorks'
  reference chain discards the first 15 frames (~2e6 symbols [derived]) as acquisition, with FLL K1 = 0.17 at 100 MBaud
  and Es/N0 1 dB, and says the FLL converges at 0 dB [vendor reference example].
- Design CFO: 1 MHz CFO + 1 MHz sinusoidal Doppler, 50 kHz/s at 100 MBaud: f = 0.01-0.02 [std + derived] (K-band pass
  example 600 kHz, 7 kHz/s). Bertolucci et al. 2021 (131.2 receiver design): Doppler ~20 % of Rs at 5 Mbaud, 0.2 % at
  500 Mbaud, 50 kHz/s worst rate [paper].
- Phase noise: mask sigma = 1.45 deg rms over [100 Hz, Rs/2] (the standard's recommendation above 1 MBaud). Hardware
  modulator < 1 deg rms over 10 kHz-250 MHz [std].

**4. Published sync performance.**
- Sync-chain loss vs ideal: 0.2-0.4 dB at CER 1e-4 (no nonlinearity); end-to-end with a TWTA 0.2-0.8 dB [std].
- FD decoding: hard ML 1e-5 at Es/N0 -2 dB, soft ML 1e-5 at -4 dB [std].
- SNR estimation on one FM is reliable below ~8 dB [std]. DAGC converges within one frame [std].
- Lowest ModCod (ACM 1, QPSK) Es/N0 -0.58 dB at CER 1e-4; FLL simulated at -0.9 dB [std].
- Bertolucci 2021: Type II FLL, k1 = 1/8, k2 = 1/32, residual 239 Hz rms (triangular Doppler, 5 Mbaud) = 4.8e-5
  cycles/symbol [paper + derived]. Fitz raw sigma ~718 Hz and M&M ~930 Hz at N = 64 (SNR of those two not stated in
  my read). Chosen: an M&M + Fitz multi-algorithm loop, N = 64. **Note:** lit_real_space.md quotes "M&M (N = 128)
  705 Hz at -2 dB" from the same paper. My read (r.jina text) did not show that number; treat it as unconfirmed.
- Acquisition probability / time: **not found** (not simulated in 130.11-G-2).

**5. Complexity.**
- Bertolucci 2021 (Zynq UltraScale+ XCZU28DR): frequency recovery 1723 LUT, 1511 FF, 2.5 BRAM, 32 DSP at 544 MHz,
  25 196 clock cycles per estimate; timing recovery 5202 LUT, 21 DSP, 536 MHz [paper].
- 130.11-G-2 reference: one 1024-point FFT per frame (133 760 symbols) = about 5120 complex multiplies per frame
  [derived], i.e. about 0.04 per symbol. 16-symbol phase sums per field.

**6. Code-aided step.** None. A DD PLL is suggested as future work [std].

**7. Our C8 "CCSDS style" vs the real system.**
| Aspect | Real 131.2 | Our C8 (`ccsds8`) | Effect on C8 |
|---|---|---|---|
| Known symbols per 1024 data | ~30 (pilots) + FM once per frame | 128 (8 x 16) | **stronger estimation**, 0.51 dB charged instead of ~0.13 dB: **weaker in energy** |
| Field spacing | 540 data | 146-147 data | aliases 1/162 instead of 1/556: easier lobe search |
| Known-symbol modulation | pi/2-BPSK FM; scrambled QPSK pilots | random QPSK | neutral for DA estimation |
| Frequency | multi-frame FLL on the FM FFT (locked before the data) | single-shot R-B over the 8 blocks + 5 lobes each side | real system much stronger: its CFO is already tracked |
| Phase | per-field ML + linear interpolation | `blocks` variant = the same; `const` and `track` (Kalman / RTS) also run | `blocks` is faithful; `track` is stronger than the standard |
| Code | SCCC, ACM | polar N = 2048 + CRC-16, CA-SCL-8, rho | same for all competitors |
| CFO | 0.01-0.02 (100 MBaud test) up to ~0.2 (5 Mbaud) | +-0.03 uniform | comparable size, but one-burst acquisition is our addition |
Verdict: C8 is a fair "CCSDS-style distributed blocks" single-packet receiver. It is not the 131.2 density, and it is
probably *stronger* in estimation than a faithful-density single burst would be (finding 2).

---

## 4. Card 2b: Receivers that implement CCSDS telemetry

| Receiver | What was read | Sync method | CFO / Doppler | Thresholds and losses | Source type |
|---|---|---|---|---|---|
| **NASA DSN Receiver and Ranging Processor** (ex Block V), 34-m / 70-m, 810-005 Module 207 Rev. A | full text via reader | carrier, subcarrier, symbol sync, Doppler compensation; suppressed carrier by Costas; QPSK / OQPSK with a dedicated loop; 4-fold ambiguity resolved downstream | FFT acquisition only when the uncertainty exceeds half the loop BL; FFT >= 512 points at 2 kHz-2 MHz sampling; BL <= min(200 Hz, Rs/20) for suppressed carrier, often < 1 Hz feasible | loop SNR >= 23 dB for QPSK (17 dB BPSK Costas, 10 dB residual); symbol loop >= 15 dB; lock time ~20/BL; typical acquisition "about one minute or less"; system loss capped at 0.93 (>= 0.3 dB); QPSK 40 ksps-26 Msps | [std] |
| **ESA TTCP** (ESTRACK) | search snippet only | suppressed carrier BPSK / QPSK / OQPSK / GMSK, residual carrier, ranging | acquisition parameters **not found** | not found | [snippet] |
| **Safran Cortex CRT** (TT&C modem, 4000+ units) | full datasheet | BPSK / (S)(O)QPSK / GMSK / AQPSK 1 kbps-40 Mbps; CCSDS Viterbi / LDPC / RS / turbo; "Doppler compensation, automatic ambiguity resolution" | range not stated | **acquisition threshold Es/N0 < -2 dB; BER degradation < 0.5 dB typical** | [vendor] |
| **Safran Cortex HDR** (1000+ units) | full datasheet | BPSK ... 64APSK, DVB-S2 / S2X / SCCC, LDPC 7/8 and AR4JA, ambiguity resolution | not stated | not stated | [vendor] |
| **Kongsberg HRDFEP** | search snippet (the PDF returned HTTP 500) | CCSDS 131.2-B-2 | "Doppler on carrier 1500 kHz" | "implementation loss typically less than 0.5 dB" | [snippet] |
| **MathWorks CCSDS FACM reference** | full page | Gardner, FM frame sync, FFT FLL (K1 = 0.17), FM fine estimate, pilot phase | 1 MHz CFO + 1 MHz Doppler, 50 kHz/s at 100 MBaud | 0 errors at Es/N0 1 dB after 15 acquisition frames | [vendor reference] |

Comparability: all of these are continuous-mode receivers that lock a loop over many frames (seconds to a minute in the
DSN case). None acquires a CFO in one 1024-symbol block. The best low-SNR acquisition number found is Cortex CRT's
Es/N0 < -2 dB, which is about 3 dB above our lowest point and is for a continuous signal.

---

## 5. Card 3: VDE-SAT (ITU-R M.2092-2 Annex 2 Tables 9-11 + Annex 5)

**1. Standard and deployments.**
- ITU-R M.2092-2 (02/2026), *Technical characteristics for VHF data exchange system in the maritime mobile service*,
  Annex 2 (Tables 9-11: uplink and downlink identification parameters), Annex 5 (VDE-SAT physical layer)
  ([PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf)) [std]. Read: all of
  Annex 5 A5-2 and the Annex 2 tables (flattened) via the text reader.
- Companion: the IALA ENAV16 draft Annex 4 "satellite downlink" (2016) uses an older, different waveform (13-bit Barker
  sync, CW pilot, QPSK at 2.625 / 21 kbaud); superseded, used only for the Doppler budget wording
  ([PDF](https://www.iala.int/content/uploads/2016/06/enav16_14_2_20_wg3_pdnr_annex_4_satellite_downlink.pdf)).
- Link: LEO satellite <-> ships, VHF ~157-162 MHz, 50-150 kHz channels.
- Deployments: **NorSat-2** (launched 14 July 2017, 600 km LEO; Space Norway, Kongsberg Seatex SDR payload and ship
  receivers, FFI analysis, ESA; 103 passes recorded on KV Harstad in Nov 2017; test waveforms from M.2092-0 / IALA
  G1139) ([ESA](https://resilience.esa.int/?p=17839)) [std/agency page]. **NorSat-TD** (Space Norway / Statsat, VDES
  payload; launch date not verified here) ([search result](https://spacenorway.no/en/vellykket-oppskyting-av-norsat-td/),
  redirected, not read). **SATMAR** (Alén Space, launched 23 June 2025 on Transporter-14, VDES in-orbit validation over
  the Bay of Algeciras; no waveform detail) ([Alén Space](https://alen.space/alen-space-places-satmar-satellite-into-orbit-to-boost-the-digitalization-of-maritime-communications/)).

**2. Burst structure.**
Downlink SAT-MCS-1.50-1 (Link ID 26, 50 kHz channel; the format our C6 copies):
| Item | Value | Source / confidence |
|---|---|---|
| Symbol rate, modulation | 33.6 ksym/s, pi/4-QPSK, RRC 0.25 | Table 10 [std]; modulation confirmed by channel bits = 2 x net |
| Ramp up / down | 14 / 14 symbols (0.41 ms each) | Table 10 + totals close [std + derived] |
| Syncword | 27 symbols, pi/4-QPSK with dibits 00 / 11 only, = the Table 1 training sequence; repeated every d_s = 2268 symbols; 35 per burst (945 symbols) | A5-2.10, Table 10 [std] |
| Pilots | single unit-power symbol, first at (1 + d_p)/2 = 14 after the syncword end, then every d_p = 27 (positions 40, 67, ..., 2254); odd-position pilots offset by pi/4; 2940 per burst | A5-2.10 [std] |
| Link ID | **0 / N/A** on all downlink formats | Table 10 [std], medium-high |
| Burst | 80 371 symbols incl. ramps = 945 + 2940 + 76 458 net + 28; 2392.0 ms + 8 ms guard = 90 slots; "the last syncword is followed by 3204 symbols" | Table 10, A5-2.10 [std + derived] |
| Known fraction | 3885 / 80 343 = 4.8 %, 0.21 dB | [derived] |
| AWGN design point | Es/N0 -2.4 dB (C/(N0+I0) 42.9 dB-Hz - 10 log10 33 600 = -2.36 dB, consistent) | Table 10 [std + derived]; rates: lit_rates.md |

Other formats (flattened tables; per-column values checked by arithmetic where stated):
| Format (Table) | Rate, modulation | Syncword | Pilots | Burst / net symbols | Known | Es/N0 AWGN | Check |
|---|---|---|---|---|---|---|---|
| Link 32 (T11, "SAT-MCS-0.50-2") | 4.2 ksym/s, BPSK/CDMA SF 8 (33.6 kchip/s) | 48 x 4, d_s 531 | every 8, 180 | 1645 / 1269 | 372 / 1641 = 22.7 % (1.12 dB) | **-4.5 dB** | 192 + 180 + 1269 + ~4 ramp = 1645 [derived] |
| Link 33 (T11, "SAT-MCS-0.50-3") | 33.6 ksym/s, BPSK | 48 x 6, d_s 2619 | none | 13 171 / 12 855 | 2.2 % | -3.6 dB | 288 + 12 855 + 28 = 13 171 |
| Link 34 (T11, header says "SAT-MCS-1.50-2"; name ambiguous) | 33.6 ksym/s, pi/4-QPSK | 27 x 6, d_s 2619 | every 27, 480 | 13 150 / 12 480 | 4.9 % (0.22 dB) | -0.6 dB | 162 + 480 + 12 480 + 28 = 13 150 |
| SAT-MCS-0.50-1 (T10) | 4.2 ksym/s BPSK/CDMA | 48 x 10, d_s 1004 | none | 10 046 / 9562 | | -2.0 dB | lit_vdesat_format.md |
| Uplink Link 20 (T9, RA, the NorSat-2 trial) | 2.1 ksym/s, QPSK/CDMA SF 16 | 48 | every 17, 12 | 263 / 201 | 23 % | -0.9 dB | [std], medium |
| Uplink 33.6 ksym/s formats (T9) | pi/4-QPSK / 8PSK / 16QAM | 27 + 16-symbol link ID | none or every 33 (71) | 627 / 556; 2419 / 2348 or 2277 | 7-9 % | 3.9-12.2 dB | 27 + 16 + 556 + 28 = 627; 27 + 16 + 71 + 2277 + 28 = 2419 [derived] |
**Closest to our ~1000-symbol burst:** by length, the uplink 627-symbol (556 net) and the 15-slot downlink Link 32
(1645 symbols). By pattern and modulation, a 1090-symbol window of SAT-MCS-1.50-1 (our C6). By SNR, Link 32 (-4.5 dB),
but with 23 % known symbols and CDMA spreading.

**3. Synchronization in practice.**
- What the known symbols are for: "uniformly repeated syncwords are utilised for synchronisation purpose" (A5-2.10);
  pilots for phase / frequency tracking [std]. Andreotti et al. (uplink): residual CFO "estimated exploiting the
  preamble and/or pilot symbols", with a DA estimator "such as the Rife and Boorstyn algorithm", then phase corrected
  with the pilots [snippet of the ResearchGate page, not the paper].
- Published estimator: Ma, Shi, Meng, Li 2018 (IEEE ICCC, doc 8780774). Local copies of the known sequence at a set of
  Doppler offsets are cross-correlated with the signal (coarse). The coarse value compensates the signal, and a fine
  estimate based on the autocorrelation argument follows, the coarse step removing its phase folding. Range
  -4000 ... +4000 Hz, accuracy "approximate to the CRB" [snippet of the abstract; SNR, lengths and numbers not seen].
- Acquisition vs tracking: not specified by the standard. The receiver has 35 syncwords and 2940 pilots per 2.4 s
  burst to track the Doppler drift.
- Design CFO: satellite transmit error < 1 ppm = +-160 Hz; LEO Doppler up to +-4 kHz at VHF (A5-2.1.2) [std]. At
  33.6 ksym/s, +-4.16 kHz = **f up to +-0.124** (4.1x our 0.03); the satellite error alone is 0.005. At 4.2 ksym/s
  (CDMA formats) it is +-0.99 per symbol (+-0.124 per chip) [derived]. The pilot-only unambiguous range is +-1/54 =
  +-0.0185 = +-622 Hz [derived], so the syncword (or a coarse search) must resolve the rest. Ship transmitters 1.5 / 3
  ppm (Table 13, ship side) [std].
- Doppler rate [derived]: about f_c v^2 / (c h) = 160 MHz x (7.56 km/s)^2 / (3e8 m/s x 600 km) ~ 50 Hz/s at zenith. That
  is 1.6 Hz (5e-5 cycles/symbol) over our 1090-symbol window (static is fine) but ~120 Hz (0.0036) over a 2.392 s
  burst (tracking needed).
- Phase noise: **not specified** in the parts read.
- Delay: the provider pre-compensates the absolute delay (transmits 2 ms before the UTC epoch) (A5-2.1.1) [std].
  Doppler pre-compensation: not specified.

**4. Published sync performance.** CFO RMSE in numbers: **not found** (Ma 2018: "approximate to the CRB" only).
Acquisition probability / time: not found. Implementation loss vs ideal sync: not found. NorSat-2 downlink
verification: SER, offsets, Ec/N0 were measured by the software demodulator, but the ESA page gives no numbers.
Fading ~20 dB peak-to-peak with a 4.2 dB std from sea reflections (IET 2018 paper, [snippet]). Andreotti: "detecting
and demodulating up to 22 overlapping RAC messages" (abstract via Crossref / EBSCO listing). Minimum operating SNR:
the format thresholds above (-4.5 dB is the lowest).

**5. Complexity.** Not published (Ma 2018 not readable). A correlation bank over +-4 kHz with 27 known symbols: if the
bins are spaced 1/(2 x 27) of Rs (~620 Hz), about 14 hypotheses x 27 complex MACs = ~380 MACs per timing hypothesis
[derived, illustrative].

**6. Code-aided step.** None found.

**7. Our C6 "VDE-SAT" vs the real system.**
| Aspect | Real SAT-MCS-1.50-1 | Our C6 (`vde27`) | Effect |
|---|---|---|---|
| Known-symbol pattern | 27 syncword, first pilot +14, then 1 / 27 | identical in a 1090-symbol window (pilots at 40, 67, ..., 1066) | faithful |
| Known symbols per data | 35 syncwords + 2940 pilots per 76 458 data (4.8 %) | 1 syncword + 39 pilots per 1024 data (6.1 %, 0.27 dB) | C6 pays slightly more energy (0.27 vs 0.21 dB): marginally weaker |
| Syncword / pilot values | fixed 00/11 pattern; (1+j)/sqrt2 with pi/4 offset at odd positions | random QPSK syncword; one random QPSK pilot repeated | neutral for DA estimation |
| Data modulation | pi/4-QPSK | QPSK | equivalent for coherent detection |
| Code | turbo over 76k symbols (+ block interleaver A5-2.13) | polar N = 2048 + CRC-16, CA-SCL-8, rho | same for all competitors |
| CFO range | up to +-0.124, drifting ~50 Hz/s | +-0.03 static | C6 has an easier range than the real one (stronger) |
| Estimation | correlation bank + autocorrelation fine (Ma 2018) or R-B (Andreotti, snippet), tracked over 35 syncwords | ML on one syncword + R-B on 66 known + CRC over +-1/27 lobes | single shot is weaker than tracking 35 syncwords, but the CRC lobe search is stronger than any published VDES receiver |
| Design SNR | -2.4 dB for this format | used down to -5 dB | C6 is tested below its design point at 1/10 and 0.15 |
| Link ID | none on the downlink | none | faithful |
Verdict: C6 is faithful in layout and estimator family. Relative to the real receiver it is helped by the smaller CFO
range and the CRC lobe search, and hurt by the single syncword and the 0.06 dB higher energy charge. The net effect is
probably close to neutral at 2/5 and 1/2. At 1/10 -5 dB it is operating 2.6 dB below the standard's design point for
this layout.

---

## 6. Per-source table

| # | Title | Year | Link | Read | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|---|
| 1 | CCSDS 131.0-B-5 TM Synchronization and Channel Coding | 2023 | [PDF](https://public.ccsds.org/Pubs/131x0b5.pdf) | full via reader (two passes) | high: the ASM-only layout of a 2048-symbol LDPC block | ASM frame sync, CSM, randomizer | continuous TM | ASM 32 / 64 / 96 / 128 / 192 bits; LDPC k = 1024: n = 2048 / 1536 / 1280 with a 64-bit ASM |
| 2 | CCSDS 131.2-B-2 SCCC FACM | 2023 | [PDF](https://public.ccsds.org/Pubs/131x2b2.pdf) | chars 0-100k of 160k | high | FM 256 + FD 64 header, pilots 16 / 540 | high-rate EO downlink | 133 760 symbols / frame, 3.06 % known [derived] |
| 3 | CCSDS 130.11-G-2 SCCC Summary | 2023 | [PDF](https://public.ccsds.org/Pubs/130x11g2.pdf) | full via reader | high: the reference receiver | FFT-FM FLL + Newton, DA ML phase + interpolation | 100 MBaud, f_D 1 MHz, 50 kHz/s | loss 0.2-0.4 dB; FD 1e-5 at -4 dB (soft); min Es/N0 -0.58 dB; B_L < 186.9 Hz |
| 4 | CCSDS 401.0-B-32 RF and Modulation | 2021 | [PDF](https://public.ccsds.org/Pubs/401x0b32.pdf) | chars 0-100k of 517k (summary tables for 2.4-2.6) | medium: CFO budgets | sweeps and loops | Cat A / B | sweeps +-150 kHz-+-4 MHz; 2B_LO 30 Hz-2 kHz (Cat A) |
| 5 | DSN 810-005 Module 207 Rev. A, 34-m and 70-m Telemetry Reception | 2003 (module) | [PDF](https://deepspace.jpl.nasa.gov/dsndocs/810-005/207/207A.pdf) | 100k of 111k via reader | medium: the deployed deep-space receiver | Costas / QPSK loops, FFT acquisition | 40 ksps-26 Msps QPSK | BL <= min(200 Hz, Rs/20); loop SNR >= 23 dB (QPSK); lock ~20/BL; acquisition ~1 min |
| 6 | Bertolucci, Cassettari, Fanucci, Sensors 21(9) 2915 | 2021 | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/) | full via reader | high: 131.2 receiver estimators + FPGA | D&M, Kay, Fitz, L&R, M&M, O'Shea; Type II FLL | 5-500 Mbaud, Doppler ~20 % Rs at 5 Mbaud | residual 239 Hz rms; freq. block 1723 LUT / 32 DSP / 25 196 cycles |
| 7 | MathWorks CCSDS FACM end-to-end example | current | [page](https://www.mathworks.com/help/satcom/ug/end-to-end-ccsds-flexible-advanced-coding-and-modulation-simulation-with-rf-impairments-and-corrections.html) | full | medium | FFT FLL K1 = 0.17, FM fine, pilot phase | 100 MBaud, Es/N0 1 dB | 15 acquisition frames; BER 0 |
| 8 | Safran Cortex CRT datasheet | 2022 | [PDF](https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20CRT%20-%20Datasheet.pdf) | full | medium: the only vendor acquisition threshold | not stated | TT&C, 1 kbps-40 Mbps | acquisition Es/N0 < -2 dB; < 0.5 dB loss |
| 9 | Safran Cortex HDR datasheet | 2022 | [PDF](https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20HDR%20-%20Datasheet.pdf) | full | low | not stated | SCCC / DVB-S2 / AR4JA | 1000+ units; no sync numbers |
| 10 | Kongsberg HRDFEP data sheet | 2025 | [PDF](https://www.kongsberg.com/globalassets/kongsberg-defence--aerospace/1.-what-we-do/1.4-space-and-surveillance/connecting-space--earth/space-ground-systems/wideband-receivers/2025/ksgs-qa-25072-hrdfep-data-sheet-v1.1.pdf) | snippet only (HTTP 500) | low | n/a | 131.2-B-2 | loss < 0.5 dB; Doppler 1500 kHz [snippet] |
| 11 | ITU-R M.2092-2 | 2026 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf) | Annex 2 Tables 9-11 (flattened) + Annex 5 A5-2 via reader | high: the C6 layout | syncword + pilots | VDE-SAT, 2.1-56.4 ksym/s | see card 3 |
| 12 | Ma, Shi, Meng, Li, "Frequency Offset Estimation Algorithm of VDES Signals Based on Cross-Correlation", IEEE ICCC 2018, pp. 1234-1238 | 2018 | [IEEE](https://ieeexplore.ieee.org/document/8780774/), doi:10.1109/CompComm.2018.8780774 | metadata (Crossref) + abstract snippet | medium: the only VDES CFO estimator | correlation bank + autocorrelation fine | VDES, +-4 kHz | "approximate to the CRB"; no numbers seen |
| 13 | Andreotti, Nanna, Andrenacci, Isca, Haugli, Alagha, IJSCN 41(2):195-215 | online 2021, issue 2023 | [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/sat.1437), doi:10.1002/sat.1437 | metadata + abstract snippets (403) | medium: the real VDE-SAT trial (uplink RA) | preamble searcher, DA CFO ("such as R-B", snippet), pilot phase | Link ID 20 over NorSat-2, Pisa ground platform | up to 22 overlapping RAC messages demodulated |
| 14 | Nanna, Andreotti, Andrenacci, Alagha, "VDE-SAT Link ID 20 performance assessment under different random access conditions", IET Conf. Proc. 2022(29):241-247 | 2023 | [IET](http://digital-library.theiet.org/doi/10.1049/icp.2023.1393) | metadata only | low-medium | n/a | Link ID 20 | not read |
| 15 | ESA "VDE-SAT Downlink Verification" (NorSat-2) | 2018 | [ESA](https://resilience.esa.int/?p=17839) | full page | medium: the downlink field trial | Kongsberg MATLAB software demodulator | 3 test waveforms, 150 kHz, M.2092-0 / G1139 | 103 passes; no link numbers |
| 16 | IALA ENAV16 draft Annex 4, satellite downlink | 2016 | [PDF](https://www.iala.int/content/uploads/2016/06/enav16_14_2_20_wg3_pdnr_annex_4_satellite_downlink.pdf) | full via reader | low: superseded waveform | Barker-13 sync, CW pilot | QPSK 2.625 / 21 kbaud | +-160 Hz + +-4 kHz; C/(N0+I0) 41-47 dB-Hz |
| 17 | Alén Space SATMAR launch | 2025 | [page](https://alen.space/alen-space-places-satmar-satellite-into-orbit-to-boost-the-digitalization-of-maritime-communications/) | full | low: deployment only | n/a | VDES IOD | launched 23 June 2025 |
| 18 | Crossref records for #12-#14 | n/a | [query](https://api.crossref.org/works?query.bibliographic=Frequency+Offset+Estimation+Algorithm+of+VDES+Signals+Based+on+Cross-Correlation&rows=3) | full | metadata | n/a | n/a | authors, DOIs, pages |

Not found or not readable: the current CCSDS 401 text beyond 2.3.4B (only summary tables); DSN Module 207 last 10 %;
ESA TTCP acquisition specifications; NASA Near Space Network user guide sync specs; any CCSDS receiver paper with
single-block CFO acquisition below Es/N0 -2 dB; Ma 2018 full text; Andreotti 2021/23 full text; any VDE-SAT CFO RMSE,
acquisition probability or implementation loss in numbers; named missions flying 131.2 or the (2048,1024) AR4JA code;
the NorSat-TD launch date (not verified).

---

## 7. Per-component verdict (these systems only)

| Component | CCSDS / VDE-SAT practice | Verdict for the competitor set |
|---|---|---|
| Coarse CFO | sweeps + FFT acquisition against predicts (DSN, 401); FM-FFT FLL over frames (131.2); correlation bank on the syncword (VDES) | **we already use it** in C6 (syncword ML) and C8 (R-B FFT). The multi-frame FLL is **not applicable** to one packet |
| Fine CFO / phase | 16-symbol DA ML per field + linear interpolation (130.11); pilots every 27 (VDES); Costas / QPSK loops (DSN) | **we already use it** (C8 `blocks`, C6 / C8 `track`) |
| Hypothesis search | none published beyond the correlation bank (VDES) | our CRC lobe search is **beyond** the published practice |
| Acceptance | ASM / FM correlation thresholds; FD ML decoding; CRC in the frames | our CRC + rho is stricter |
| Complexity | 1723 LUT / 32 DSP / 25 196 cycles per estimate (Bertolucci); ~0.04 complex mult per symbol for the FM FFT [derived] | not comparable to MACs per core; the pilot competitors' estimator cost is negligible in both cases |
| Code-aided | none (130.11 suggests a DD PLL) | **not applicable**: no deployed CCSDS / VDES code-aided sync found |

Comparability, plainly: CCSDS receivers run continuous loops over seconds to minutes on 1e5-1e7 symbols. VDE-SAT
bursts are 2.4 s / 80k symbols with a CFO up to 0.124 that drifts. None publishes single-1024-symbol acquisition
results. Our "-inspired" competitors are single-packet models of their known-symbol layouts, not of the receivers.

---

## Reference entries

### CCSDS 131.0-B-5
# CCSDS 131.0-B-5, TM Synchronization and Channel Coding, Recommended Standard (Blue Book), Issue 5, September 2023
- Link: https://public.ccsds.org/Pubs/131x0b5.pdf   - Type: standard   - Read depth: full text via r.jina.ai (figures as text)
#### What it does
ASM before every codeblock: 32-bit 1ACFFC1D (uncoded / conv. / RS / LDPC 7/8), 64-bit 034776C7272895B0 (turbo 1/2,
LDPC 1/2, 2/3, 4/5), 96 / 128 / 192-bit (turbo 1/3, 1/4, 1/6); no pilots; ASM not randomized; LDPC k = 1024 r = 1/2 ->
n = 2048 transmitted (Table 7-5); phase ambiguities must be resolved before decoding (CSM may help).
#### What we took / could take
(2048,1024) LDPC + 64-bit ASM = 32 QPSK known symbols per 1024-symbol codeblock: the CCSDS single-codeword layout
(lit_card_space.md finding 3); est4 16 + 16 / 64 + 64 bracket it.
#### Used in
-

### CCSDS 131.2-B-2
# CCSDS 131.2-B-2, Flexible Advanced Coding and Modulation Scheme for High Rate Telemetry Applications, Blue Book, Issue 2, February 2023
- Link: https://public.ccsds.org/Pubs/131x2b2.pdf   - Type: standard   - Read depth: chars 0-100k of 160k via r.jina.ai
#### What it does
PL frame: 256-symbol pi/2-BPSK Gold frame marker + 64-symbol frame descriptor, 16 codeword sections of 8100 symbols,
each with 15 x (540 data + 16 pilots) when pilots are on (b6); pilots (1+j)/sqrt2 then PL-scrambled; 133 760 symbols
per frame with pilots [derived], 3.06 % known [derived]; 27 ACM formats QPSK ... 64APSK.
#### What we took / could take
Real pilot density for C8 (about 30 known per 1024 data, aliases 1/556): our C8 has 3.7x more (lit_card_space.md).
#### Used in
-

### CCSDS 130.11-G-2 (card read)
# CCSDS 130.11-G-2, SCCC - Summary of Definition and Performance, Green Book, Issue 2, May 2023
- Link: https://public.ccsds.org/Pubs/130x11g2.pdf   - Type: standard (informational)   - Read depth: full via r.jina.ai
#### What it does
Reference receiver: frame-level FLL with a 1024-point FFT of the FM + Newton (k1 = 0.2, B_L < 186.9 Hz at 100 MBaud),
DA ML phase per 16-symbol field + linear interpolation, SNR / DAGC on the FM; timing and FM acquisition not simulated;
f_D 1 MHz, 50 kHz/s at 100 MBaud; phase noise 1.45 deg rms; sync loss 0.2-0.4 dB at CER 1e-4 (0.2-0.8 dB with
TWTA); FD soft ML 1e-5 at -4 dB; lowest ModCod -0.58 dB; HW test Tesat EM TX + Kongsberg Spacetec RX at 500 MBaud
K-band.
#### What we took / could take
C8 `blocks` phase model = 130.11 5.6; confirms there is no single-burst acquisition and no code-aided step.
#### Used in
-

### CCSDS 401.0-B-32
# CCSDS 401.0-B-32, Radio Frequency and Modulation Systems - Part 1: Earth Stations and Spacecraft, Blue Book, Issue 32, October 2021
- Link: https://public.ccsds.org/Pubs/401x0b32.pdf   - Type: standard   - Read depth: chars 0-100k of 517k (text to 2.3.4B; summary tables for the rest)
#### What it does
Earth-station acquisition sweeps +-150 kHz (2 GHz), +-600 kHz (8 GHz), +-1.8 MHz (26 GHz) Cat A; +-300 kHz / +-1 MHz /
+-4 MHz Cat B; sweep rates 100 Hz/s-200 kHz/s; Doppler rates up to 3 / 10 / 34 kHz/s; telemetry loop 2B_LO 30 Hz-2 kHz
(Cat A), 1 Hz-1 kHz (Cat B); suppressed-carrier rate limits 2 / 10 / 20 Msps.
#### What we took / could take
CFO-as-fraction-of-Rs context (0.075-0.3 [derived]), handled by sweeps and loops, not per block.
#### Used in
-

### DSN 810-005 Module 207
# NASA JPL, DSN Telecommunications Link Design Handbook 810-005, Module 207 Rev. A, 34-m and 70-m Telemetry Reception, 2003
- Link: https://deepspace.jpl.nasa.gov/dsndocs/810-005/207/207A.pdf   - Type: standard (agency handbook)   - Read depth: chars 0-100k of 111k via r.jina.ai
#### What it does
Receiver and Ranging Processor: Costas for suppressed carrier, a dedicated QPSK / OQPSK loop; BL <= min(200 Hz, Rs/20);
FFT acquisition (>= 512 points) when the uncertainty exceeds half the loop BL; lock time ~20/BL; typical acquisition
about one minute; loop SNR >= 23 dB (QPSK), 17 dB (BPSK Costas), 10 dB (residual); QPSK 40 ksps-26 Msps; system loss
>= 0.3 dB.
#### What we took / could take
Evidence that deep-space receivers lock loops over seconds to minutes; not a single-burst competitor.
#### Used in
-

### Bertolucci 2021 (card read)
# M. Bertolucci, R. Cassettari, L. Fanucci, "On the Frequency Carrier Offset and Symbol Timing Estimation for CCSDS 131.2-B-1 High Data-Rate Telemetry Receivers", Sensors 21(9):2915, 2021, doi:10.3390/s21092915
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/   - Type: paper   - Read depth: full via r.jina.ai
#### What it does
LEO Ka 5-500 Mbaud, Doppler ~20 % of Rs at 5 Mbaud, 50 kHz/s; compares D&M / Kay / Fitz / L&R / M&M / O'Shea; chooses an
M&M + Fitz multi-algorithm Type II FLL (N = 64, k1 = 1/8, k2 = 1/32), residual 239 Hz rms; FPGA frequency block 1723
LUT, 32 DSP, 544 MHz, 25 196 cycles per estimate.
#### What we took / could take
FPGA cost of a deployed-class DA estimator; the "705 Hz at -2 dB" figure in lit_real_space.md was not visible in this read.
#### Used in
-

### MathWorks CCSDS FACM example (card read)
# MathWorks, "End-to-End CCSDS Flexible Advanced Coding and Modulation Simulation with RF Impairments and Corrections", accessed 2026-11-15
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-ccsds-flexible-advanced-coding-and-modulation-simulation-with-rf-impairments-and-corrections.html   - Type: app note   - Read depth: full page
#### What it does
Gardner timing, FM frame sync, FFT-based FLL (K1 = 0.17), FM fine estimate, pilot phase; 1 MHz CFO + 1 MHz Doppler,
50 kHz/s at 100 MBaud, Es/N0 1 dB; 15 frames for acquisition, then 0 bit errors.
#### What we took / could take
Context only (multi-frame).
#### Used in
-

### Safran Cortex CRT
# Safran Data Systems, Cortex CRT - Digital Modem for Satellite Housekeeping & Critical Communications, datasheet COL000010.4.0, 2022
- Link: https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20CRT%20-%20Datasheet.pdf   - Type: vendor datasheet   - Read depth: full
#### What it does
4000+ deployed TT&C modems; BPSK / (S)(O)QPSK / GMSK / AQPSK 1 kbps-40 Mbps, CCSDS Viterbi / LDPC / RS / turbo;
acquisition threshold Es/N0 < -2 dB; BER degradation < 0.5 dB typical; Doppler compensation, automatic ambiguity
resolution.
#### What we took / could take
The lowest vendor acquisition threshold found for CCSDS telemetry (continuous signal).
#### Used in
-

### Safran Cortex HDR
# Safran Data Systems, Cortex HDR - High Data Rate Receiver for Space Science and Earth Observation, datasheet COL000016.4.0, 2022
- Link: https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20HDR%20-%20Datasheet.pdf   - Type: vendor datasheet   - Read depth: full
#### What it does
1000+ units; up to 6 channels, 10 Gbps; BPSK ... 64APSK; DVB-S2 / S2X / SCCC, LDPC 7/8 and AR4JA; no sync specifications.
#### What we took / could take
Deployment evidence only.
#### Used in
-

### Kongsberg HRDFEP
# Kongsberg (KSGS), MEOS Capture HRDFEP data sheet v1.1, 2025
- Link: https://www.kongsberg.com/globalassets/kongsberg-defence--aerospace/1.-what-we-do/1.4-space-and-surveillance/connecting-space--earth/space-ground-systems/wideband-receivers/2025/ksgs-qa-25072-hrdfep-data-sheet-v1.1.pdf   - Type: vendor datasheet   - Read depth: search snippet only (HTTP 500)
#### What it does
CCSDS 131.2-B-2 compliant; "implementation loss typically less than 0.5 dB"; "Doppler on carrier 1500 kHz" (snippet).
#### What we took / could take
Context only (unverified).
#### Used in
-

### M.2092-2 (card read)
# ITU-R Recommendation M.2092-2 (02/2026), Technical characteristics for VHF data exchange system in the maritime mobile service, Annex 2 Tables 9-11 and Annex 5
- Link: https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf   - Type: standard   - Read depth: Annex 5 A5-2 full and Annex 2 Tables 9-11 (flattened) via r.jina.ai
#### What it does
SAT-MCS-1.50-1: pi/4-QPSK 33.6 ksym/s, ramp 14/14, 27-symbol syncword every 2268, pilot every 27 (first +14; odd
positions offset pi/4), no link ID on the downlink, 80 371 symbols per 2392 ms burst, Es/N0 -2.4 dB. The -4.5 dB
format (Link 32) is BPSK/CDMA SF 8, 48-symbol syncwords, pilot every 8. Satellite TX error < 1 ppm (+-160 Hz), Doppler
+-4 kHz; delay pre-compensated by the provider.
#### What we took / could take
Resolves lit_vdesat_format.md's open items (link ID 0, pi/4-QPSK, ramp 14); C6 design-SNR label (finding 1).
#### Used in
-

### Ma 2018 (VDES CFO)
# S. Ma, K. Shi, X. Meng, X. Li, "Frequency Offset Estimation Algorithm of VDES Signals Based on Cross-Correlation", 2018 IEEE 4th International Conference on Computer and Communications (ICCC), pp. 1234-1238, Dec 2018, doi:10.1109/CompComm.2018.8780774
- Link: https://ieeexplore.ieee.org/document/8780774/   - Type: paper   - Read depth: Crossref metadata + abstract search snippet (IEEE page empty to the fetcher)
#### What it does
Coarse: cross-correlation with local copies of the known sequence at a set of Doppler offsets; compensation; fine:
autocorrelation-argument estimator without phase folding; range +-4000 Hz, accuracy "approximate to the CRB".
#### What we took / could take
Corrects REFERENCES.md C17 metadata (2018, authors, DOI); C6's ML + R-B is at least as accurate as this chain.
#### Used in
-

### Andreotti 2021/2023
# R. Andreotti, L. Nanna, M. Andrenacci, A. Isca, H.-C. Haugli, N. Alagha, "On-field test campaign performance of VDE-SAT Link ID 20 over Norsat-2 LEO satellite", Int. J. Satell. Commun. Netw. 41(2):195-215, 2023 (online 10 Nov 2021), doi:10.1002/sat.1437
- Link: https://onlinelibrary.wiley.com/doi/10.1002/sat.1437   - Type: paper   - Read depth: metadata and abstract snippets only (403)
#### What it does
Over-the-air uplink RA tests (Pisa ground platform emulating vessels -> NorSat-2), post-processed; demodulator with a
preamble searcher, DA CFO ("such as Rife and Boorstyn", snippet) and pilot phase; up to 22 overlapping RAC messages
demodulated.
#### What we took / could take
Real VDE-SAT receivers use DA R-B-type estimation on preamble + pilots: the same family as C6.
#### Used in
-

### Nanna 2023 (IET)
# L. Nanna, R. Andreotti, M. Andrenacci, N. Alagha, "VDE-SAT Link ID 20 performance assessment under different random access conditions", IET Conference Proceedings 2022(29):241-247, published 2023, doi:10.1049/icp.2023.1393
- Link: http://digital-library.theiet.org/doi/10.1049/icp.2023.1393   - Type: paper   - Read depth: metadata only
#### What it does
Not read.
#### What we took / could take
Nothing.
#### Used in
-

### ESA VDE-SAT downlink verification
# ESA, "VDE-SAT Downlink Verification" (NorSat-2) activity page, 2018
- Link: https://resilience.esa.int/?p=17839   - Type: agency page   - Read depth: full
#### What it does
NorSat-2 SDR payload as an arbitrary waveform generator, 3 VDE-SAT test waveforms (150 kHz, M.2092-0 / G1139) + a CW
tone in a Doppler guard band; Kongsberg Seatex ship receiver on KV Harstad, reference at Andøya; IQ recording + MATLAB
software demodulator (SER, offsets, Ec/N0); 103 passes in Nov 2017; final review June 2018.
#### What we took / could take
Deployment evidence for C6's real system; no sync numbers.
#### Used in
-

### IALA ENAV16 Annex 4 (2016)
# IALA ENAV16 WG3, draft annex 4 "satellite downlink" (VDE-SAT draft technical description), 2016
- Link: https://www.iala.int/content/uploads/2016/06/enav16_14_2_20_wg3_pdnr_annex_4_satellite_downlink.pdf   - Type: standard (draft)   - Read depth: full via r.jina.ai
#### What it does
Superseded draft waveform (Barker-13 sync, CW pilot, QPSK 2.625 / 21 kbaud); TX error < 1 ppm (+-160 Hz), Doppler +-4 kHz;
C/(N0+I0) 41-47 dB-Hz.
#### What we took / could take
Origin of the +-160 Hz / +-4 kHz budget only.
#### Used in
-

### SATMAR (Alén Space)
# Alén Space, "Alén Space places SATMAR satellite into orbit to boost the digitalization of maritime communications", 24 June 2025
- Link: https://alen.space/alen-space-places-satmar-satellite-into-orbit-to-boost-the-digitalization-of-maritime-communications/   - Type: press release   - Read depth: full
#### What it does
VDES in-orbit validation satellite launched 23 June 2025 (Transporter-14); no waveform details.
#### What we took / could take
Deployment list only.
#### Used in
-
