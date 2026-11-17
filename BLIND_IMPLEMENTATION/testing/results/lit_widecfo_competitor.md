# Which modern full system has a CFO regime like ours? (literature scout, 2026-11-17)

**Question (user):** DVB-RCS2 has a residual CFO of about +-0.002 per symbol and was never designed for +-0.03. Which
MODERN deployed or standardised system (or published receiver) is closest to ours: short bursts, Es/N0 -5 ... +3 dB,
a CFO of 0.01 cycles/symbol or more estimated per burst without closed-loop correction, ideally polar / LDPC / turbo,
few or no pilots?

**Short answer.** The closest modern standard is **3GPP IoT-NTN (Rel-17+) NB-IoT NPUSCH format 1, single tone at
3.75 kHz**. Its satellite-access-node (SAN) conformance test applies a **128 Hz frequency offset = 0.034 cycles/symbol**,
which is our +-0.03 range. It is single-carrier pi/4-QPSK (or pi/2-BPSK), short transport blocks (up to 1000 bits),
turbo + CRC, about 1000 symbols per transmission, and it runs at SNR around -2 dB (1 Rx, fading, 4 repetitions). The
terrestrial NB-IoT test has no frequency offset at all, so the CFO is there because of the satellite. It is
deployed (Skylo GEO, Sateliot LEO; C63). The UE requirement (+-0.1 ppm after pre-compensation, TS 36.102) gives
0.045-0.055 cycles/symbol in the L/S NTN bands. That is even larger than our range.
The second candidate, if a **same-code** standard is wanted, is **NR NTN PUCCH format 3** (polar-coded UCI, CRC-6/11,
like ours). Its residual CFO is about 0.014 cycles per OFDM symbol, but it is OFDM / DFT-s-OFDM with 14-29 % DM-RS.
**VDE-SAT is not "Doppler pre-compensated":** M.2092-2 does not ask the ship to pre-compensate frequency. The receiver
sees up to +-4 kHz (+-0.12 cycles/symbol at 33.6 ksym/s), 4x our range. Our `fullsys_datacard.md` section 3 row
"Designed CFO range: small (Doppler pre-compensated)" is **wrong** and should be corrected.

Read-depth tags: [full] = whole page or section read; [summ] = page read through the fetch summariser (tables can be
flattened); [abs] = abstract only; [snip] = search snippet only; [local] = local text file; [derived] = my
arithmetic; [mem] = from memory, not verified in this session (flagged, do not rely on it).

---

## 1. Ranked actionable findings (at most 5)

1. **Implement NB-IoT IoT-NTN NPUSCH format 1, 3.75 kHz single tone, as the "modern full system closest to ours".**
   The SAN test uses a 128 Hz offset at 3.75 kHz SCS. That is 0.034 of the SCS, or 0.035 per 275 us symbol with CP
   [derived; the 275 us symbol is [mem]]. That is our +-0.03. The terrestrial test (TS 36.104) has no offset column.
   Sources: [TS 36.108 cl. 8.5.1.1.1](https://itecspec.com/spec/3gpp-36-108-8-5-1-1-1-minimum-requirements) [summ],
   [TS 36.104 cl. 8.5.1.1.1](https://itecspec.com/spec/3gpp-36-104-8-5-1-1-1-minimum-requirements) [summ],
   [TS 36.102 cl. 6.4B.1](https://itecspec.com/spec/3gpp-36-102-6-4b-1-frequency-error-for-ue-category-nb1-and-nb2) [summ].
   - **What it is.** A deployed open-loop residual after GNSS + ephemeris pre-compensation, estimated per
     transmission from DM-RS (1 per 7 symbols).
   - **Test.** Blind vs the full NPUSCH (DM-RS + LTE turbo + CRC) at the same payload in AWGN, with a static CFO of
     128 Hz and 200 Hz (S-band +-0.1 ppm), Eb/N0 per payload bit.
2. **Correct the VDE-SAT CFO claim.** In M.2092-2, A5-2.1.2 gives a satellite carrier error below 1 ppm (+-160 Hz) and
   a LEO Doppler of up to +-4 kHz. No clause asks the ship or the satellite to pre-compensate frequency. The only
   pre-compensation clause, A5-2.1.1, is for delay (timing). The VDE-SAT syncwords are chosen for "best autocorrelation for
   differential detection" (Table 1), i.e. for a receiver that handles a large CFO. So the residual is
   +-4.16 kHz [derived]. That is +-0.124 cycles/symbol at 33.6 ksym/s, and +-0.99 cycles/symbol (0.124 per chip) on
   Link 32 at 4.2 ksym/s with spreading x8 (Table 11). Source: local `standards/ITU-R_M.2092-2_2026.txt`, lines
   535-552 and 5142-5169 [local].
   - **Action.** Fix `fullsys_datacard.md` §3, and state in every VDE-SAT plot that it is tested inside +-0.03, 4x
     narrower than its design.
3. **NR NTN residual CFO (the user's 3GPP question):** +-0.1 ppm relative to the ideally pre-compensated carrier, over
   1 ms. In cycles per OFDM symbol (15 kHz SCS, S-band) that is **0.014**. Per DFT-s-OFDM data symbol it is about
   **0.001** (1 PRB). Details in section 4. Sources:
   [TS 38.101-5 cl. 6.4.1](https://itecspec.com/spec/3gpp-38-101-5-6-4-1-frequency-error) [summ] and
   [TS 38.300 cl. 16.14.2.2](https://itecspec.com/spec/3gpp-38-300-16-14-2-2-timing-advance-and-frequency-pre-compensation)
   [summ]. The NR SAN conformance tests (TS 38.108 PUSCH / PUCCH) have **no frequency-offset column**: they test fading
   only. So NR NTN is a weaker CFO match than IoT-NTN.
4. **If a same-code standard is wanted, use NR PUCCH format 3 (polar UCI).** For A >= 12 bits: CRC-6 below 20 bits,
   CRC-11 from 20 bits, N <= 1024. It uses 2 DM-RS symbols of 14 (4 with additional DM-RS) and DFT-s-OFDM. The 38.108
   test is 16 UCI bits, 1 PRB, 14 symbols, 1 % BLER at 6.6 / 6.4 dB SNR (1 Rx, NTN-TDLA100-200).
   - **Cost.** An OFDM chain (CP, FFT), which our RRC single-carrier harness does not have.
   - **Use.** It is a "same decoder, modern standard" point, not a CFO match.
   - Sources: [ShareTechnote PUCCH](https://www.sharetechnote.com/html/5G/5G_PUCCH.html) [summ],
     [TS 38.108 cl. 8.3.5.1](https://itecspec.com/spec/3gpp-38-108-8-3-5-1-general) and
     [8.3.5.2](https://itecspec.com/spec/3gpp-38-108-8-3-5-2-minimum-requirements) [summ].
5. **Closest published receiver: Yue et al. 2023.** It uses FFT acquisition, then a code-aided cross-entropy + EM
   CFO / phase search on a polar (1024, 512) BP-decoded short burst with no training sequence, at Es/N0 about -3 dB.
   - **Same architecture class as ours.** It confirms the approach, but its residual CFO after acquisition is only
     +-0.0078 per symbol.
   - **Nothing to adopt.** It is cooperative multi-satellite with a BP decoder and has no complexity numbers.
   - Source: [arXiv 2309.12828](https://arxiv.org/html/2309.12828) [summ, full HTML].

---

## 2. Candidate systems, ranked

Normalisation: CFO in cycles per (data) symbol = f_offset x T_symbol [derived unless stated].

### Rank 1: NB-IoT IoT-NTN NPUSCH format 1, single tone (3GPP Rel-17+; TS 36.211/212/213, 36.102, 36.108). Resemblance **4 / 5**
- **What and deployed.** The NB-IoT uplink data channel over GEO / LEO satellites. Commercial: Skylo GEO Rel-17
  service, Soracom launch 2024, certified chipsets (Sony ALT1250, u-blox, Quectel), Sateliot LEO (already C63 [snip]).
- **Burst format.**
  - Single tone at 3.75 kHz (or 15 kHz), pi/2-BPSK or pi/4-QPSK with phase continuity
    ([Keysight NPUSCH help](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/nbiot/content/nbiot_dlg_fmt_npuschformatparameters.htm), [snip]).
  - Slot of 2 ms = 7 symbols; resource unit 32 ms at 3.75 kHz ([snip], NB-IoT primer
    [arXiv 1606.04171](https://arxiv.org/abs/1606.04171); the PDF could not be parsed this session; C53).
  - 1 DM-RS symbol per 7 (14 % pilots; C53, C10 card).
  - LTE turbo code ([snip]); max TBS 1000 bits ([snip]; 2536 bits for Rel-14 feNB-IoT is only in a patent claim,
    unverified). CRC-24 [mem, unverified].
  - The 36.108 test uses Tx duration 256 (ms per the table [summ]). That is about 930 symbols per transmission
    [derived], close to our 1024.
- **CFO per burst, with sources.**
  - UE error: +-0.1 ppm (>1 GHz) or +-0.2 ppm (<=1 GHz), relative to the "ideally pre-compensated" carrier from SIB
    ephemeris + UE position (TS 36.102 6.4B.1 [summ]).
  - NTN bands: n255 UL 1626.5-1660.5 MHz, n256 UL 1980-2010 MHz
    ([band table](https://www.doc.surf/wiki/5g-nr-frequency-bands) [snip]). So +-163 ... +-201 Hz [derived] =
    **0.045-0.055 cycles/symbol at 3.75 kHz** and 0.011-0.014 at 15 kHz [derived].
  - SAN test: **128 Hz static offset** at 3.75 kHz (0.034-0.035 per symbol) and at 15 kHz single tone (0.009). It is
    only 8 Hz / 2 Hz for 15 kHz multi-tone (TS 36.108 Tables 8.5.1.1.1-1 ... -5 [summ]).
  - Terrestrial NB-IoT (TS 36.104) has no offset column [summ].
  - Earlier project notes: the NPRACH residual after DL sync is +-600 Hz (Chougrani 2021, C57 / lit_real_leo #5).
    The deployed terrestrial DM-RS window is +-250 Hz (Chakrapani, C52).
- **Es/N0 range and published curves.** 36.108 FDD single tone 3.75 kHz: SNR -2.0 dB (TDLA100-1) / -3.6 dB (TDLC5-1)
  at 1 Rx, 4 repetitions, 70 % of max throughput, HARQ 4 tx [summ]. Terrestrial 3.75 kHz: -1.9 / -9.2 / -12.2 dB for
  1 / 16 / 64 repetitions (2 Rx, ETU 1 Hz) [summ]. No AWGN PER curve was found. The FRC A7-1 payload (TBS) could not be
  read (itecspec 404).
- **Synchroniser.** DM-RS based CFO / phase (implementation-specific; Chakrapani C52). Its 1-in-7 comb resolves
  |f| < 1/14 = 0.071 [derived], so there are no aliases at 0.055.
- **Implementation difficulty: medium, all public.**
  - Specs: 3GPP TS 36.211 / 212 / 213 (free).
  - Turbo: Sionna `TurboEncoder(interleaver_type="3GPP")` + `Turbo3GPPInterleaver` (LTE interleaver, length up to
    6144; [Sionna docs](https://nvlabs.github.io/sionna/phy/api/fec/turbo/sionna.phy.fec.turbo.TurboEncoder.html)
    [snip]) or AFF3CT (C86).
  - References: MATLAB LTE Toolbox NB-IoT NPUSCH BLER example (C54, terrestrial); MATLAB NB-IoT NTN NPDSCH example
    (downlink only; [MathWorks](https://www.mathworks.com/help/lte/ug/nb-iot-ntn-npdsch-throughput.html) [snip]).
  - Our C10 "DMRS 1/7" competitor is already the pilot comb, so the new work is the turbo + CRC + TBS / rate matching
    and the 3.75 kHz slot (guard period).
- **Why it resembles ours.**
  - Same: CFO size, single carrier, QPSK-class, short blocks, low SNR, open-loop per-transmission estimation.
  - Different: turbo (not polar), 14 % pilots, repetitions / HARQ in the real system, fading conformance tests.

### Rank 2: VDE-SAT with its real Doppler (ITU-R M.2092-2, Annex 5). Resemblance **3 / 5** (already implemented)
- **What it is.** Maritime VHF data exchange via LEO, in trials (C16, C85).
- **Burst format.** Already in `fullsys_datacard.md` §2.
- **CFO.** +-4 kHz Doppler + 1 ppm (+-160 Hz) satellite carrier error, no frequency pre-compensation clause [local,
  A5-2.1.2; searched "compensat", "Doppler", "ephemeris" in the whole text]. That is +-0.124 per symbol at 33.6 ksym/s
  and +-0.99 per symbol on Link 32 (4.2 ksym/s) [derived]. The ship's own error is 1.5 / 3 ppm (normal / extreme)
  [local, line 1540].
- **SNR.** Es/N0 -4.5 ... -0.6 dB on AWGN (Table 11). There is no public PER curve (lit_vdesat_fullsystem §4).
- **Synchroniser.** A Doppler-shifted syncword correlation bank over +-4 kHz (Ma et al. 2018, abstract, earlier
  survey) plus pilot tracking.
- **Why rank 2.**
  - For: real, low SNR, short Link 32 packets, large open-loop CFO.
  - Against: its CFO is 4-30x ours, so at +-0.03 we test it outside its design. Turbo code, 23 % known symbols.

### Rank 3: NR NTN PUCCH format 3 / format 2 (polar UCI) and PUSCH (3GPP Rel-17+). Resemblance **3 / 5**
- **What and deployed.** The 5G NR satellite uplink. Rel-17 NR NTN; open source: OAI gNB with GEO and LEO NTN features
  ([OAI RAN](https://openairinterface.org/ran/),
  [2025 newsletter](https://openairinterface.org/wp-content/uploads/2025/10/OAI-2025-Summer-Newsletter.pdf), [snip]).
  srsRAN has NTN only in research UE forks [snip].
- **Burst format.**
  - PF3: 4-14 symbols, 1-16 PRBs, DFT-s-OFDM, QPSK or pi/2-BPSK, 2 DM-RS symbols per 14 (4 with additional DM-RS).
  - PF2: 1-2 symbols, CP-OFDM, DM-RS on 4 of 12 subcarriers.
  - UCI: polar for A >= 12 bits, CRC-6 (12-19 bits) or CRC-11 (>= 20 bits), N <= 1024 (ShareTechnote [summ]).
  - PUSCH: LDPC.
- **CFO.** UE +-0.1 ppm vs ideal pre-compensation (TS 38.101-5 6.4.1). Feeder-link Doppler is left to the network
  (TS 38.300 16.14.2.2). See section 4 for the per-symbol numbers.
- **SNR / curves.** 38.108 PF3, 16 bits, 1 PRB, 14 symbols, 1 % BLER: 6.6 dB (1 Rx, no additional DM-RS) and 6.4 dB
  (with) at 15 kHz; 9.2 / 8.6 dB at 30 kHz; about 0-1.6 dB with 2 Rx (column layout unclear) [summ]. PUSCH (DFT-s-OFDM)
  at 70 % throughput: 3.7 dB (TDLA, 1 Rx) ... -1.2 dB (TDLC, 2 Rx) [summ]. No frequency-offset column in either.
- **Synchroniser.** DM-RS. MATLAB NR NTN PUSCH example: a ±50 kHz / 1 kHz-step joint time-frequency search
  on DM-RS, differential correlation, CP / DM-RS residual correction
  ([MathWorks](https://www.mathworks.com/help/5g/ug/nr-ntn-pusch-throughput.html) [summ]).
- **Difficulty.** Medium-high: an OFDM chain is needed; MATLAB 5G Toolbox and OAI exist; Sionna has the 5G polar
  UCI encoder (C104).
- **Why it resembles ours.** It is the same code family as ours. But its CFO is small per data symbol (OFDM), and the
  UCI payloads in the tests are small (16 bits).

### Rank 4: NB-IoT NTN NPUSCH at 15 kHz single tone, or LTE-M NTN. Resemblance 2.5 / 5
- **NB-IoT at 15 kHz single tone.** A 128 Hz test offset gives 0.009/symbol, and 0.1 ppm gives 0.011-0.014 [derived].
  It is the lower edge of our range and is covered by Rank 1 as a variant (one flag).
- **LTE-M.** Wideband SC-FDMA, so the CFO per data symbol is small (as for NR PUSCH). Not pursued.

### Not chosen (with reasons)
| System | Why not | Source / read depth |
|---|---|---|
| DVB-RCS2 (incl. V1.5.1 NGSO, S2X return bursts) | carrier accuracy 1e-8 RMS + NCC corrections: residual about 0.002 per symbol | C1 (earlier read) |
| DVB-S2X VL-SNR / Annex E superframe | continuous forward link; VL-SNR header limited to about 1 % of Rs; multi-frame loops | C24 / C25, competitors.md |
| S-MIM / E-SSA (ETSI TS 102 721-3) | **could not be read**: the ETSI PDF is AES-encrypted and the text could not be extracted. Only abstracts of the E-SSA field trials were found ([Fraunhofer](https://publica.fraunhofer.de/entities/publication/b1691489-7479-4c62-9f7d-afd6d4f4e3b5), [Semantic Scholar](https://www.semanticscholar.org/paper/Enhanced-Spread-Spectrum-Aloha-(E-SSA),-an-emerging-Reichman/88c36cc2f0b8335fc7073652b0cb56ced1c73c6c)) [snip]. GEO S-band mobile, spread spectrum, CRC + SIC; no CFO numbers found. A 2024 E-SSA paper with CA-polar codes ([arXiv 2402.12101](https://arxiv.org/html/2402.12101) [summ]) models no CFO | [ETSI TS 102 721-3 V1.2.1](https://etsi.org/deliver/etsi_TS/102700_102799/10272103/01.02.01_60/ts_10272103v010201p.pdf) (not readable) |
| LoRa / LR-FHSS, Sigfox, Argos-4 / Kinéis, ORBCOMM, AIS, Iridium | CSS / FSK / differential, or a CFO of 0.4-40 cycles/symbol | lit_real_leo.md, lit_real_wlan.md |
| Myriota, Astrocast, Swarm | no public physical layer or CFO numbers found (this search and lit_real_leo.md) | [snip] |
| MIL-STD-188-181 / 165, Link 16 | numeric tolerances not public; Link 16 is MSK / CCSK | lit_real_military.md |
| CCSDS 131.2, Proximity-1 | continuous or idle-sequence acquisition; small CFO | lit_real_space.md |

---

## 3. Per-source table (new this session)

| # | Title | Year | Link | Read | Rel. | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|---|
| C115 | 3GPP TS 38.101-5 cl. 6.4.1, NR NTN UE frequency error (Rel-19, itecspec mirror) | 2025-26 | [itecspec](https://itecspec.com/spec/3gpp-38-101-5-6-4-1-frequency-error) | summ | high | requirement | NR NTN UE, FR1 | +-0.1 ppm, 1 ms, vs the ideally pre-compensated UL carrier |
| C116 | 3GPP TS 36.102 cl. 6.4B.1, NB-IoT NTN UE frequency error | 2025-26 | [itecspec](https://itecspec.com/spec/3gpp-36-102-6-4b-1-frequency-error-for-ue-category-nb1-and-nb2) | summ | high | requirement | NB1 / NB2 NTN | +-0.2 ppm <= 1 GHz, +-0.1 ppm > 1 GHz; 1 slot averaged over 72 / L_tone slots; reference includes ephemeris Doppler |
| C117 | 3GPP TS 36.108 cl. 8.5.1.1 / 8.5.1.1.1, IoT-NTN SAN NPUSCH F1 requirements | 2025-26 | [itecspec](https://itecspec.com/spec/3gpp-36-108-8-5-1-1-1-minimum-requirements) | summ | **high** | conformance test | 3.75 / 15 kHz, 1 Tx, 1-2 Rx, NTN-TDL, HARQ 4 | **offset 128 Hz** (single tone), 8 / 2 Hz (multi-tone); SNR -2.0 / -3.6 dB (1 Rx), -5.4 / -6.5 dB (2 Rx) at 70 % throughput |
| C118 | 3GPP TS 36.104 cl. 8.5.1.1.1, terrestrial NB-IoT NPUSCH F1 | current | [itecspec](https://itecspec.com/spec/3gpp-36-104-8-5-1-1-1-minimum-requirements) | summ | medium | conformance test | ETU 1 Hz, 2 Rx | no offset column; 3.75 kHz: -1.9 / -9.2 / -12.2 dB for 1 / 16 / 64 reps |
| C119 | 3GPP TS 38.108 cl. 8.3.5.1, 8.3.5.2, 8.2.2.2, NR NTN SAN PUCCH F3 / PUSCH | 2025-26 | [8.3.5.2](https://itecspec.com/spec/3gpp-38-108-8-3-5-2-minimum-requirements), [8.3.5.1](https://itecspec.com/spec/3gpp-38-108-8-3-5-1-general), [8.2.2.2](https://itecspec.com/spec/3gpp-38-108-8-2-2-2-minimum-requirements) | summ | medium | conformance test | NTN-TDLA100-200 / TDLC5-200, 15 / 30 kHz | PF3 16 bits, 1 PRB, 14 symbols: 6.6 / 6.4 dB at 1 % BLER (1 Rx); no offset column |
| C120 | 3GPP TS 38.300 cl. 16.14.2.2, TA and frequency pre-compensation | current | [itecspec](https://itecspec.com/spec/3gpp-38-300-16-14-2-2-timing-advance-and-frequency-pre-compensation) | summ | medium | architecture | NR NTN | UE pre-compensates the service-link Doppler; feeder-link Doppler is left to the network |
| C121 | ShareTechnote, 5G NR PUCCH | n/a | [link](https://www.sharetechnote.com/html/5G/5G_PUCCH.html) | summ (2 passes) | medium | tutorial | PF2 / 3 / 4 | polar for A >= 12, CRC-6 / 11, N <= 1024; PF3 2 or 4 DM-RS symbols (10-14 symbols) |
| C122 | MathWorks, NR NTN PUSCH throughput example | R2026a | [link](https://www.mathworks.com/help/5g/ug/nr-ntn-pusch-throughput.html) | summ | medium | reference sim | 2 GHz, 15 kHz, 25 RB, 600 km LEO | +-50 kHz / 1 kHz DM-RS search, differential correlation; no residual value given |
| C123 | MathWorks, NB-IoT NTN NPDSCH throughput example | current | [link](https://www.mathworks.com/help/lte/ug/nb-iot-ntn-npdsch-throughput.html) | snip | low | reference sim (downlink) | ETSI Rician, P.681 LMS | none |
| C124 | Yue, Li, Li, Zhang, Wang, An, "Multiple Satellites Collaboration for Joint Code-aided CFOs and CPOs Estimation" | 2023 | [arXiv 2309.12828](https://arxiv.org/html/2309.12828) | summ (full HTML) | medium-high | FFT acquisition (I = 64), then cross-entropy CFO quantisation (D = 6 bits, 120 candidates), then code-aided EM, polar BP | polar (1024, 512), BPSK-DSSS, 1 ksym/s, no training sequence, Es/N0 about -3 dB | residual after acquisition +-0.0078 per symbol; BER 0.3-0.4 dB from ideal at 1e-4 (2-4 satellites); no complexity numbers |
| C125 | "Edge-Side Residual Timing and Frequency Control for Software-Defined Ground Stations in 5G NTN Uplinks" | 2026 | [arXiv 2604.13984](https://arxiv.org/abs/2604.13984) | abs | low-medium | closed-loop edge control | 5G NTN UL, 4 ground stations | residual CFO P95 76-77 Hz after control |
| C126 | OpenAirInterface NTN (RAN page; 2025 summer newsletter) | 2025 | [RAN](https://openairinterface.org/ran/), [newsletter](https://openairinterface.org/wp-content/uploads/2025/10/OAI-2025-Summer-Newsletter.pdf) | snip | low | open source | Rel-17 GEO + LEO | none |
| C127 | NVIDIA Sionna TurboEncoder / Turbo3GPPInterleaver docs | current | [docs](https://nvlabs.github.io/sionna/phy/api/fec/turbo/sionna.phy.fec.turbo.TurboEncoder.html) | snip | medium (implementation) | LTE turbo | rate 1/3 (1/2 punctured), 3GPP interleaver up to 6144 | none |
| C128 | Keysight 89600 help, NPUSCH format parameters; NB-IoT primer snippets | n/a | [Keysight](https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/nbiot/content/nbiot_dlg_fmt_npuschformatparameters.htm) | snip | medium | reference | NPUSCH F1 | LTE turbo; max TBS 1000; single tone 3.75 kHz pi/2-BPSK / pi/4-QPSK; RU 32 ms |
| C129 | 5G NR frequency bands table (doc.surf wiki, from Rel-19) | n/a | [link](https://www.doc.surf/wiki/5g-nr-frequency-bands) | snip | low | band list | NTN | n256 UL 1980-2010 MHz, n255 UL 1626.5-1660.5 MHz, n512 UL 27.5-30 GHz (secondary source) |
| C130 | ETSI TS 102 721-3 V1.2.1, S-MIM return link asynchronous access (E-SSA) | 2013 | [ETSI](https://etsi.org/deliver/etsi_TS/102700_102799/10272103/01.02.01_60/ts_10272103v010201p.pdf) | **not readable** (encrypted PDF) | unknown | - | - | none extracted |
| C131 | E-SSA field-trial papers (Fraunhofer; Reichman) | ~2012-13 | [Fraunhofer](https://publica.fraunhofer.de/entities/publication/b1691489-7479-4c62-9f7d-afd6d4f4e3b5), [S2](https://www.semanticscholar.org/paper/Enhanced-Spread-Spectrum-Aloha-(E-SSA),-an-emerging-Reichman/88c36cc2f0b8335fc7073652b0cb56ced1c73c6c) | snip | low | E-SSA demodulator + CRC + SIC | EUTELSAT 10A trials | none |
| (C16) | ITU-R M.2092-2, A5-2.1.1 / A5-2.1.2, Table 1, Table 11 | 2026 | local `standards/ITU-R_M.2092-2_2026.txt` | local (clauses) | high | standard | VDE-SAT | +-4 kHz Doppler, < 1 ppm satellite carrier, ship 1.5 / 3 ppm; no frequency pre-compensation clause |

Not found: an NR or NB-IoT NTN paper that publishes an AWGN PER curve with a stated residual CFO; the IoT-NTN FRC A7-1
TBS; any "pilot-free" polar or LDPC short-packet receiver with a CFO of 0.01 per symbol or more beyond those already in
REFERENCES.md (2102.10719, 2305.01972, 2602.17979 are phase / fading only). IEEE 9148234 ("Iterative joint CFO
estimation and channel decoding for satellite NB-IoT") did not load (empty page): not read, not cited for content.

---

## 4. The 3GPP NR NTN residual CFO, per symbol (the user's question)

- **Requirement (normative).** The NTN UE carrier "shall be accurate to within +-0.1 PPM observed over a period of
  1 ms ... compared to ideally pre-compensated reference uplink carrier frequency". The reference = signalled UL
  carrier + the UE's pre-compensated Doppler (TS 38.101-5 6.4.1 [summ]; first proposed in R4-2216641, C60).
- **Who handles what.** The UE pre-compensates the service-link Doppler from GNSS + ephemeris. The feeder-link Doppler
  and the transponder error are "left to the network implementation" (TS 38.300 16.14.2.2 [summ]).
- **What the gNB / SAN must handle.** No explicit receiver CFO requirement was found. The SAN conformance (38.108)
  PUSCH / PUCCH tables carry no frequency offset [summ]. In practice the gNB sees the UE's +-0.1 ppm, plus any
  GNSS / ephemeris error (not part of the 0.1 ppm; measured P95 76-77 Hz in one 2026 testbed, C125 [abs]), plus
  network-side residuals.
- **Per symbol [derived].** +-0.1 ppm at n256 UL (1980-2010 MHz) = +-198 ... +-201 Hz; at n255 UL
  (1626.5-1660.5 MHz) = +-163 ... +-166 Hz.

| Waveform | Symbol | CFO / symbol (S-band) | CFO / symbol (L-band) |
|---|---|---|---|
| CP-OFDM / DFT-s-OFDM, 15 kHz, per OFDM symbol (71.4 us incl. CP) | 1 OFDM symbol | **0.014** (0.013 of SCS) | 0.012 |
| same, 30 kHz (35.7 us) | 1 OFDM symbol | 0.007 | 0.006 |
| DFT-s-OFDM PUSCH / PUCCH F3, 1 PRB (180 ksym/s), per modulation symbol | 1 data symbol | 0.0011 | 0.0009 |
| NB-IoT single tone 3.75 kHz (275 us incl. CP [mem]) | 1 data symbol | **0.055** | 0.045 |
| NB-IoT single tone 15 kHz (71.4 us) | 1 data symbol | 0.014 | 0.012 |
| IoT-NTN SAN test, 128 Hz at 3.75 kHz | 1 data symbol | **0.035** | - |
| FR2-NTN Ka n512 (27.5-30 GHz), 120 kHz SCS, if +-0.1 ppm applies (not verified) | 1 OFDM symbol | 0.025-0.027 | - |

- **Reading.** For NR the residual is about +-0.013 of the SCS. That is a small CFO per OFDM symbol, and tiny per
  DFT-s-OFDM data symbol. Only the single-tone NB-IoT uplink turns the same ppm budget into a per-symbol CFO the size
  of ours (or larger).

---

## 5. Per-component state-of-the-art verdict (from these candidates)

| Component | Ours | What the closest systems do | Verdict |
|---|---|---|---|
| Coarse CFO | 4th-power FFT fast path | NB-IoT / NR NTN: GNSS + ephemeris pre-compensation, then DM-RS; VDE-SAT: Doppler-shifted syncword bank; Yue 2023: FFT acquisition | **we already use it** (blind analogue). Pre-compensation is **not applicable** (we model the residual) |
| Fine CFO / phase | grid x phase list-1 SC metric, Stage 3, code-aided retry | DM-RS 1/7 (NB-IoT), 2-4 DM-RS symbols / slot (NR PF3), code-aided EM (Yue 2023) | **we already use it** (code-aided); nothing to borrow for AWGN |
| Hypothesis search | CFO cells x phases, early-stop checkpoints | Yue 2023: cross-entropy sampling of quantised CFO candidates (120 candidates, Ne elites) | **not behind**: CE sampling is a possible alternative ordering, but no complexity numbers to justify a test |
| Acceptance / false alarm | CRC-16 + rho | CRC-24 (NB-IoT TB [mem]), CRC-6 / 11 (NR UCI), CRC-32 (VDE) | **we already use it** (stricter with rho) |
| Drift | static CFO | NB-IoT NTN re-pre-compensates per segment (C59); Doppler rate matters for 256 ms transmissions | **behind / untested** (already on the list: drift robustness point) |

## 6. Comparability (plainly)
- **3GPP numbers.** All are fading (NTN-TDL), with HARQ, 70 % throughput or 1 % UCI BLER, often with 2 Rx. None is an
  AWGN PER curve, so none can be plotted next to ours. We must simulate the system ourselves in AWGN.
- **NB-IoT uses repetitions.** A faithful AWGN comparison at Es/N0 -5 ... +3 dB uses 1-4 repetitions; above that
  the system works far below our SNR range.
- **NR PUCCH is OFDM.** Our single-carrier RRC chain would need a CP-OFDM / DFT-s-OFDM front end. The "per symbol"
  CFO is not the same quantity.
- **VDE-SAT.** Its design CFO is 4x (Links 26 / 34) to about 30x (Link 32) ours. At +-0.03 it is tested on an
  easier problem than it was built for.

## 7. Recommendation
1. **Implement next: NB-IoT IoT-NTN NPUSCH format 1, single tone 3.75 kHz, faithful** (Rel-17 36.211 / 212 / 213 +
   36.108 FRC A7-1).
   - **Chain.** pi/4-QPSK (and pi/2-BPSK), 7-symbol 2 ms slots with 1 DM-RS, LTE turbo rate 1/3 + rate matching +
     TB CRC, native TBS near our payloads (e.g. 208 / 328 / 1000 bits).
   - **CFO.** Static 128 Hz (= 0.034 per symbol, the 3GPP test) and +-200 Hz (0.055, the S-band ppm budget).
   - **Axis and receiver.** Eb/N0 per payload bit with DM-RS energy charged; a DM-RS R&B / ML receiver (window
     +-0.071, no alias search needed).
   - **Why.** It is the only modern, deployed, standardised system found whose own conformance test puts the CFO in
     our range, on a single-carrier QPSK short-block uplink at our SNRs.
   - **Cost.** Medium: Sionna 3GPP turbo or AFF3CT; C10 already has the comb. MATLAB's NB-IoT NPUSCH example can
     validate bit-exactness (C54).
2. **Optional second: NR NTN PUCCH format 3 with polar UCI** (CRC-11, N <= 1024, 2 or 4 DM-RS of 14 symbols). It is
   the "same code, modern 5G satellite standard" point. Its CFO match is weaker (0.014 per OFDM symbol) and it needs an
   OFDM front end, so do it only if the reviewers want a polar-coded standard competitor.
3. **Keep VDE-SAT, but fix its description** (no Doppler pre-compensation; design residual +-0.12 per symbol). Report
   it as "tested inside its design range". Retire DVB-RCS2 as the "large-CFO" competitor: keep it only as the
   "deployed return-link burst" reference with its true +-0.002 residual.

---

## New reference entries (for REFERENCES.md; not edited here)

### C115. 3GPP TS 38.101-5, NR UE radio transmission and reception, Part 5: Satellite access, clause 6.4.1 Frequency error (Rel-19, itecspec mirror)
- Link: https://itecspec.com/spec/3gpp-38-101-5-6-4-1-frequency-error   - Type: standard   - Read depth: summ (section page)
- What: NTN UE carrier within +-0.1 ppm over 1 ms of 1-slot measurements, relative to the ideally pre-compensated UL carrier.
- Took: residual CFO budget for NR NTN, 0.014 cycles per 15 kHz OFDM symbol at S-band [derived] (supersedes the draft-only C60 wording).

### C116. 3GPP TS 36.102 (IoT NTN UE radio), clause 6.4B.1 Frequency error for UE category NB1 and NB2
- Link: https://itecspec.com/spec/3gpp-36-102-6-4b-1-frequency-error-for-ue-category-nb1-and-nb2   - Type: standard   - Read depth: summ
- What: +-0.2 ppm (<= 1 GHz), +-0.1 ppm (> 1 GHz), 1 slot averaged over 72 / L_tone slots, reference includes the ephemeris-based Doppler.
- Took: 0.045-0.055 cycles/symbol at 3.75 kHz single tone in n255 / n256 [derived].

### C117. 3GPP TS 36.108 (IoT-NTN SAN), clauses 8.5.1.1 and 8.5.1.1.1, NPUSCH format 1 requirements
- Link: https://itecspec.com/spec/3gpp-36-108-8-5-1-1-1-minimum-requirements ; https://itecspec.com/spec/3gpp-36-108-8-5-1-1-requirements   - Type: standard   - Read depth: summ (tables flattened)
- What: test frequency offset 128 Hz (single tone 3.75 / 15 kHz), 8 Hz / 2 Hz (15 kHz multi-tone); 3.75 kHz FRC A7-1, Tx duration 256, 4 reps: SNR -2.0 / -3.6 dB (1 Rx), -5.4 / -6.5 dB (2 Rx) at 70 % throughput; HARQ 4 tx, RV0 / RV2.
- Took: the CFO operating point (0.034 per symbol) for the proposed NB-IoT NTN competitor.

### C118. 3GPP TS 36.104 clause 8.5.1.1.1, terrestrial NB-IoT NPUSCH format 1 requirements
- Link: https://itecspec.com/spec/3gpp-36-104-8-5-1-1-1-minimum-requirements   - Type: standard   - Read depth: summ
- What: no frequency offset; 3.75 kHz FRC A16-1: -1.9 / -9.2 / -12.2 dB for 1 / 16 / 64 reps (2 Rx, ETU 1 Hz).
- Took: evidence that the 128 Hz offset in C117 is NTN-specific.

### C119. 3GPP TS 38.108 (NR NTN SAN), clauses 8.3.5.1, 8.3.5.2 (PUCCH F3), 8.2.2.2 (PUSCH, transform precoding)
- Link: https://itecspec.com/spec/3gpp-38-108-8-3-5-2-minimum-requirements ; https://itecspec.com/spec/3gpp-38-108-8-3-5-1-general ; https://itecspec.com/spec/3gpp-38-108-8-2-2-2-minimum-requirements   - Type: standard   - Read depth: summ
- What: PF3 16 UCI bits, 1 PRB, 14 symbols, hopping, QPSK, 1 % BLER: 6.6 / 6.4 dB (15 kHz, 1 Rx), 9.2 / 8.6 dB (30 kHz); PUSCH 3.7 ... -1.2 dB at 70 %; no frequency-offset parameter.
- Took: reference only (fading tests, not comparable to AWGN).

### C120. 3GPP TS 38.300 clause 16.14.2.2, Timing advance and frequency pre-compensation
- Link: https://itecspec.com/spec/3gpp-38-300-16-14-2-2-timing-advance-and-frequency-pre-compensation   - Type: standard   - Read depth: summ
- What: UE pre-compensates the service-link Doppler; feeder-link Doppler is left to the network.
- Took: who owns which residual.

### C121. ShareTechnote, "5G NR PUCCH"
- Link: https://www.sharetechnote.com/html/5G/5G_PUCCH.html   - Type: tutorial   - Read depth: summ (both halves)
- What: PF2 / 3 / 4 structure; UCI coding (RM for 3-11 bits, polar for >= 12, CRC-6 / CRC-11, N <= 1024); PF3 DM-RS 2 or 4 symbols for lengths 10-14.
- Took: PUCCH F3 card (Rank 3).

### C122. MathWorks 5G Toolbox, "NR NTN PUSCH Throughput" example (R2026a)
- Link: https://www.mathworks.com/help/5g/ug/nr-ntn-pusch-throughput.html   - Type: app note   - Read depth: summ
- What: UE Doppler pre-compensation from ephemeris; receiver +-50 kHz / 1 kHz joint time-frequency DM-RS search, differential correlation; 2 GHz, 15 kHz, 25 RB, 600 km.
- Took: reference receiver for an NR NTN competitor.

### C123. MathWorks LTE Toolbox, "NB-IoT NTN NPDSCH Throughput" example
- Link: https://www.mathworks.com/help/lte/ug/nb-iot-ntn-npdsch-throughput.html   - Type: app note   - Read depth: snip
- What: downlink NB-IoT NTN with Doppler pre-compensation and receiver compensation.
- Took: reference only (no uplink NPUSCH NTN example found).

### C124. P. Yue, Y. Li, Y. Li, R. Zhang, S. Wang, J. An, "Multiple Satellites Collaboration for Joint Code-aided CFOs and CPOs Estimation", arXiv 2309.12828, 2023
- Link: https://arxiv.org/html/2309.12828   - Type: paper   - Read depth: summ (full HTML)
- What: FFT acquisition (64 points), cross-entropy CFO quantisation (6 bits, 120 candidates), code-aided EM with polar (1024, 512) BP; BPSK-DSSS, no training sequence; residual +-0.0078 per symbol; 0.3-0.4 dB from ideal BER at 1e-4 (2-4 satellites).
- Took: reference only (confirms the coarse-FFT + code-aided search architecture; smaller CFO range, no complexity).

### C125. "Edge-Side Residual Timing and Frequency Control for Software-Defined Ground Stations in 5G NTN Uplinks", arXiv 2604.13984, 2026
- Link: https://arxiv.org/abs/2604.13984   - Type: paper   - Read depth: abs
- What: closed-loop residual control; residual CFO P95 76-77 Hz, TA P95 0.49 us.
- Took: reference only (a measured real-world residual).

### C126. OpenAirInterface NTN support (RAN page; OAI 2025 Summer Newsletter)
- Link: https://openairinterface.org/ran/ ; https://openairinterface.org/wp-content/uploads/2025/10/OAI-2025-Summer-Newsletter.pdf   - Type: open source   - Read depth: snip
- What: Rel-17 NTN, GEO and LEO features (Fraunhofer IIS-led).
- Took: open-source availability for an NR NTN competitor.

### C127. NVIDIA Sionna, TurboEncoder and Turbo3GPPInterleaver documentation
- Link: https://nvlabs.github.io/sionna/phy/api/fec/turbo/sionna.phy.fec.turbo.TurboEncoder.html ; https://nvlabs.github.io/sionna/phy/api/fec/sionna.phy.fec.interleaving.Turbo3GPPInterleaver.html   - Type: code docs   - Read depth: snip
- What: rate-1/3 turbo, 3GPP LTE interleaver (up to 6144), termination, puncturing to 1/2.
- Took: implementation path for the NB-IoT NTN turbo code.

### C128. Keysight 89600 VSA help, "NPUSCH Format Parameters (NB-IoT)"; NB-IoT primer search snippets
- Link: https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/nbiot/content/nbiot_dlg_fmt_npuschformatparameters.htm   - Type: vendor help   - Read depth: snip
- What: NPUSCH F1 uses the LTE turbo code, max TBS 1000 bits, single tone 3.75 kHz with pi/2-BPSK / pi/4-QPSK, RU 32 ms.
- Took: burst format for the NB-IoT NTN card.

### C129. 5G NR frequency bands table (doc.surf wiki, based on Rel-19)
- Link: https://www.doc.surf/wiki/5g-nr-frequency-bands   - Type: secondary   - Read depth: snip
- What: n256 UL 1980-2010 MHz, n255 UL 1626.5-1660.5 MHz, n512 UL 27.5-30 GHz.
- Took: carrier frequencies for the ppm-to-Hz conversion.

### C130. ETSI TS 102 721-3 V1.2.1 (2013-08), S-MIM Part 3: Physical layer, return link asynchronous access (E-SSA)
- Link: https://etsi.org/deliver/etsi_TS/102700_102799/10272103/01.02.01_60/ts_10272103v010201p.pdf   - Type: standard   - Read depth: none (encrypted PDF, text not extractable)
- What: not read.
- Took: nothing; listed so it is not re-searched blindly (needs a local PDF text extraction).

### C131. E-SSA field-trial papers: Fraunhofer, "E-SSA satellite messaging return channel: performance analysis and field trials results"; Reichman, "Enhanced Spread Spectrum Aloha (E-SSA), an emerging satellite return link messaging scheme"
- Link: https://publica.fraunhofer.de/entities/publication/b1691489-7479-4c62-9f7d-afd6d4f4e3b5 ; https://www.semanticscholar.org/paper/Enhanced-Spread-Spectrum-Aloha-(E-SSA),-an-emerging-Reichman/88c36cc2f0b8335fc7073652b0cb56ced1c73c6c   - Type: paper   - Read depth: snip
- What: E-SSA demodulator with CRC + SIC, EUTELSAT 10A trials; no CFO numbers in what was read.
- Took: reference only.
