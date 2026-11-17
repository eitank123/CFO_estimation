# VDE-SAT (ITU-R M.2092-2) burst format and published CFO estimators (literature scout, 2026-11-15)

Question: what is the real VDE-SAT burst (syncword, link ID, pilots, modulation, length), is our est4 layout `vde27`
(27 known + 39 x (26 data + 1 pilot) + 10 data, Nk = 66, K = 1090) right, and is there a published CFO estimator for it.

**How this was read (be aware):** the ITU-R M.2092-2 PDF (7 MB) could be downloaded, but neither the fetch tool nor
the local reader could decode its compressed text, and IEEE / ResearchGate / Academia returned 403 / 418. All numbers
below come from text excerpts of M.2092-2, M.2092-1, IALA G1139 ed. 3 and the ESA NAVISP ICING document that the search
engine returned. The rules quoted in the worked example (positions 26, 40, 67, 2254, 2268) are direct quotes and are
reliable. Table cells (burst totals, link ID size per format) came out of garbled table extractions, so their column
mapping is my inference, checked by arithmetic (it adds up, see section 2). Someone should open Annex 5, sections
A5-2.10 (pilots and syncword) and A5-2.12 (link configuration formats), in a PDF viewer and confirm three items: the
link ID size for SAT-MCS-1.50-1, the data modulation, and the ramp length.

## 1. Short answer

- **The 27 is right.** The VDE-SAT downlink formats SAT-MCS-1.50-1 and SAT-MCS-3.50-1 (the 33.6 ksps formats with
  pilots) have a **27-symbol syncword**, a **pilot distance of 27 symbols** and a **syncword distance of 2268 symbols**
  (M.2092-2, A5-2.10). The syncword bit pattern is `010001010010010000000110011` ("best autocorrelation for
  differential detection"). Each bit is sent as a pi/4-QPSK symbol restricted to the dibits 00 / 11.
- **Pilot = one fixed symbol**, unity power, at (1+j)/sqrt2, and it is the same in every pilot field. Our
  `make_burst` already repeats one pilot symbol, so this matches.
- **What is slightly wrong in `vde27`: the pilot phase relative to the syncword.** The standard puts the first pilot
  **(1 + d_p)/2 = 14 symbols after the last syncword symbol**. Worked example in M.2092-2: last syncword symbol at
  position 26, first pilot at 40, next pilot at 67. So there are **13 data symbols** between the syncword and the
  first pilot, then 26 data symbols between pilots. Our layout puts 26 data symbols before the first pilot (first
  pilot at 53).
- **Corrected layout for one 1024-data packet window:**
  `[k 27] [d 13] [k 1] ([d 26] [k 1]) x 38 [d 23]`, which gives 13 + 38 x 26 + 23 = 1024 data, 27 + 39 = 66 known, and
  K = 1090. **Nk = 66, K = 1090 and the 1/27 alias lobes are unchanged.** Only the pilot comb shifts by 13 symbols
  (half a pilot period), so the known-symbol centroid moves by about 13 x 39/66 = about 8 symbols. I expect the effect
  on CFO and phase RMSE or BLER to be negligible (< 0.02 dB, an estimate, not run). It is still worth fixing so that the
  layout is literally the standard's.
  - A possible code change (main session decides): in `est4/common.py` add `VDE_HEAD = 13` and return
    `[("k",27), ("d",13), ("k",1)] + [("d",26), ("k",1)]*38 + [("d",23)]`. **Caution:** changing a layout changes the
    est5 random streams and invalidates the finished `VDE-SAT` runs, so treat it as a new layout name (for example
    `vde27s`) or accept a rerun.
- **The link ID is not a known field.** M.2092-2 tables list a "Link ID size" row: 16 symbols, a (32,6) biorthogonal
  code, pi/4-QPSK for most PL formats, and 0 symbols for others. The excerpt says 0 for SAT-MCS-1.50-2 (Link ID 20,
  uplink). For SAT-MCS-1.50-1 the burst-total arithmetic (section 2) closes without a link ID field, so it is probably
  0 for that format too (unconfirmed). Even where it exists, the link ID is one of 64 codewords, not a pilot. It would
  count as non-payload overhead (energy charged), not as extra known symbols. **Leave it out of `vde27`.**
- **A real VDE-SAT downlink burst is about 74 x longer than our packet.** It is a 90-slot burst (2.4 s at 33.6 ksps,
  about 80.4k symbols) with the syncword repeated every 2268 symbols (35 syncwords) and a pilot every 27 symbols
  (2940 pilots). Our 1090-symbol `vde27` is "the first 1090 symbols of a VDE-SAT burst", which is the fair
  single-packet analogue: one syncword plus 39 pilots. Overhead is 66 / 1090 = 6.1 % (0.27 dB). The real burst's
  overhead is (945 + 2940) / 80343 = 4.8 % (0.21 dB), a little lower because the syncword is amortised over 2268 symbols
  instead of 1090. Our competitors.md figure of about 65 known and 0.27 dB stands.
- **Published CFO estimator for VDE-SAT:** I found only one VDE-SAT-specific paper, and I could not read it:
  IEEE Xplore document 8780774, "Frequency Offset Estimation Algorithm of VDES Signals Based on Cross-Correlation"
  (about 2019; authors and venue could not be read, IEEE blocked the fetch). From its abstract excerpt it builds local
  copies of the known sequence at a set of Doppler offsets, cross-correlates them with the received signal for a coarse
  estimate, compensates, then refines. It reports a range of +-4000 Hz and accuracy "approximate to the CRB". That is
  a correlation-bank coarse search plus a data-aided fine stage: the same family as our C6 chain (ML on the syncword,
  then Rife-Boorstyn over all known symbols). Its +-4 kHz at 33.6 ksps is +-0.119 cycles/symbol, about 4 x our |f| <=
  0.03. The NorSat-2 Link ID 20 field-test paper (Andreotti et al., IJSCN 2023, uplink) says only that the residual CFO
  "is estimated exploiting the preamble and/or pilot symbols". No algorithm or numbers were visible. The other VDES CFO
  papers found are for VDE-TER (double Barker training sequence, phase difference between the two halves) or a
  multicarrier FMT VDES variant, so they are not the satellite downlink.

## 2. The VDE-SAT downlink burst, as far as it could be read

| Item | SAT-MCS-1.50-1 / SAT-MCS-3.50-1 (downlink, 33.6 ksps) | Source / confidence |
|---|---|---|
| Syncword | 27 symbols, bits `010001010010010000000110011`, pi/4-QPSK with dibits 00 / 11 only, same pattern as the Table 1 preamble training sequence | M.2092-2 A5-2.10, quoted; high |
| Syncword distance d_s | 2268 symbols, first symbol to first symbol | quoted; high |
| Number of syncwords per burst | 35, 945 syncword symbols in total | table excerpt; 35 x 27 = 945 checks |
| Pilot | single symbol, unity power, (1+j)/sqrt2, the same every time | quoted (the sqrt sign was lost in extraction); high |
| Pilot distance d_p | 27 symbols, pilot to pilot (26 data between) | quoted; high |
| First pilot | (1 + d_p)/2 = 14 symbols after the last symbol of the preceding syncword: syncword 0-26, pilot 40, 67, ..., last pilot before the next syncword 2254, next syncword 2268 | quoted worked example; high |
| Pilots per syncword period | (2254 - 40)/27 + 1 = 83 (the comb is a global 27-grid; the grid point at offset 13 falls inside the syncword) | derived |
| Total pilots per burst | 2940 | table excerpt; consistent (34 x 83 + 118 in the last, longer segment) |
| Net (data) symbols per burst | 76458 | table excerpt |
| Symbols per burst | 80371 = 76458 + 945 + 2940 + 28 (28 = ramp 14 + 14, the G1139 value for these SAT-MCS formats) | table excerpt + arithmetic; medium |
| Burst / slot | 90 slots x 26.67 ms = 2.4 s = 80640 symbols; 80640 - 80371 = 269 symbols, about 8 ms guard | derived; consistent with the "8 ms guard" row |
| Link ID field | probably 0 for 1.50-1 (the totals close without it); 16 symbols, (32,6) biorthogonal, pi/4-QPSK in other formats | garbled table; low-medium |
| Data modulation | 1.50-1: QPSK-class (pi/4-QPSK or QPSK); 3.50-1: 8PSK. The 2018 SciTePress paper gives MCS-1 = QPSK rate 1/2, MCS-3 = 8PSK rate 3/4 | low-medium (exact table cell not read) |
| FEC | turbo code, rate 1/2 or lower, other rates by puncturing (IALA draft 2016); M.2092 Annex 5 also has a block channel interleaver (A5-2.13) | medium |
| Receiver thresholds | in competitors.md we quote Es/N0 thresholds of -4.5 ... -0.6 dB (A5-2.2.2, not re-read here) | not re-verified |

Other VDE-SAT formats seen in the same tables (column mapping uncertain): SAT-MCS-0.50-1 with a 48-symbol syncword,
10 syncwords (480 symbols), no pilots, 10046 symbols per burst and 9562 net. Link ID 20 / SAT-MCS-1.50-2 (uplink
random access, CDMA spread x16, about 2.1 ksps): 48-symbol QPSK syncword, 12 pilots at distance 17 (the field-test
paper says "every 16 data symbols", which is the same thing), 201 net symbols. Other syncword distances listed across
editions and formats: 531, 1004, 2619, 2690, 4214, 8697, 14705. **Editions differ:** G1139 ed. 3 (2019) lists 2619
where M.2092-2 has 2268. Use M.2092-2.

## 3. Is our `vde27` the right competitor layout?

- Known-symbol count: **yes.** In a 1090-symbol window that starts at a syncword, the standard gives exactly
  27 + 39 = 66 known symbols (pilots at 40, 67, ..., 40 + 38 x 27 = 1066 < 1090; the next one, at 1093, falls outside).
- Pilot positions: **off by 13 symbols** (see section 1). The corrected layout is
  `[k27][d13][k1]([d26][k1])x38[d23]`.
- Lobe spacing: `lobe_D = 27` and `LOBE_N = 1` stay right. The pilot comb has period 27, so the aliases sit at
  +-1/27 = +-0.037 cycles/symbol. For |f| <= 0.03 only the first lobe on each side can fall into range, and the
  contiguous syncword breaks the ambiguity (alias peak about 0.59 of the true peak, as in competitors.md).
- Syncword symbols: we draw random QPSK. The standard's syncword is a fixed +-1 pattern on pi/4-QPSK points. For
  data-aided CFO and phase estimation with known constant-modulus symbols this makes no difference to the CRB or to
  the R-B / ML estimators. It would matter only for detection and timing autocorrelation, which are out of scope.
  Using the real sequence is optional.
- Energy accounting: 66 known symbols, no link ID field. If the main session wants to be strict for formats that do
  carry a link ID, add 16 non-payload symbols (overhead 82 / 1106, 0.34 dB). For SAT-MCS-1.50-1 this is probably not
  needed (unconfirmed).
- Comparability caveats: real VDE-SAT uses a turbo code over about 76k data symbols in a LEO Doppler channel (Doppler
  up to about +-4 kHz, i.e. +-0.12 cycles/symbol, plus Doppler rate). Our C6 uses our polar N = 2048 code on 1024
  symbols in AWGN with |f| <= 0.03. C6 is "the VDE-SAT known-symbol pattern" and not the VDE-SAT system.

## 4. Per-source table

| Title | Year | Link | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|
| ITU-R M.2092-2, Technical characteristics for VHF data exchange system in the maritime mobile service, Annex 5 (VDE-SAT) | 2026 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf), [TOC](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!TOC-HTM-E.htm), [e-pub](https://www.itu.int/epublications/publication/recommendation-itu-r-m-2092-2-02-2026-technical-characteristics-for-vhf-data-exchange-system-in-the-maritime-mobile-service) | high: the normative burst format | standard: syncword, pilot and link-ID placement (A5-2.10, A5-2.12) | VDE-SAT down and uplink, 33.6 ksps, 25-150 kHz channels | 27-symbol syncword, d_p = 27, d_s = 2268, first pilot at +14, pilot (1+j)/sqrt2; 35 syncwords, 2940 pilots, 76458 net, 80371 symbols/burst (table excerpt) |
| ITU-R M.2092-1 | 2022 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-1-202202-I!!PDF-E.pdf) | medium: earlier edition | same | same | "Syncword size 27, syncword modulation pi/4-QPSK (00/11 only)" excerpt |
| ITU-R M.2092-0 | 2015 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-0-201510-I!!PDF-E.pdf) | low: superseded | same | same | pilot distance 8 in some formats; not used |
| IALA G1139 ed. 3, The technical specification of VDES | 2019 | [PDF](https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf) | medium: readable companion, older numbers | specification guideline | VDES incl. VDE-SAT | ramp 14 / 14 symbols for the SAT-MCS 15-slot formats, 8 ms guard; Link ID = 6 bits, biorthogonal (32,6); d_s 2619 (differs from M.2092-2) |
| ESA NAVISP ICING document | about 2021 | [PDF](https://navisp.esa.int/document/NAVISP%20EL3_010-ICING-Independent%20Critical%20Navigation.pdf) | low-medium | VDE-SAT format summary based on M.2092-1 | VDE-SAT | syncword modulation BPSK / CDMA / pi/4-QPSK (00/11) per format; burst durations 1641 / 13143 / 13122 symbols (15-slot formats) |
| Frequency Offset Estimation Algorithm of VDES Signals Based on Cross-Correlation (IEEE Xplore 8780774) | about 2019 | [IEEE](https://ieeexplore.ieee.org/abstract/document/8780774) | medium: the only VDE-SAT-specific CFO estimator found; **not read, only the abstract excerpt** (IEEE blocked the fetch) | bank of Doppler-shifted local known sequences, cross-correlation coarse estimate, compensation, fine estimate | VDE-SAT downlink, LEO Doppler | range +-4000 Hz (+-0.119 cycles/symbol at 33.6 ksps), accuracy "approximate to the CRB"; SNR and lengths not visible |
| Andreotti, Nanna, Andrenacci, Isca, Haugli, Alagha, On-field test campaign performance of VDE-SAT Link ID 20 over NorSat-2 LEO satellite, Int. J. Satell. Commun. Netw. 41(2):195-215 | 2023 | [ResearchGate](https://www.researchgate.net/publication/356135026_On-field_test_campaign_performance_of_VDE-SAT_Link_ID_20_over_Norsat-2_LEO_satellite), [dblp](https://dblp1.uni-trier.de/rec/journals/ijscn/AndreottiNAIHA23.html) | medium: real VDE-SAT receiver, but the uplink RA burst | preamble searcher, residual CFO from the preamble and / or pilots, E-SSA-like demodulator | Link ID 20: 48-symbol QPSK syncword, 12 pilots every 16 data symbols, CDMA x16, NorSat-2 at 600 km | estimator details and numbers not visible (403) |
| VDES Performance Evaluation for Future e-navigation Services (SciTePress) | 2018 | [PDF](https://www.scitepress.org/papers/2018/68502/68502.pdf) | low | link-level evaluation | VDE-SAT MCS | MCS-1 QPSK r 1/2, MCS-3 8PSK r 3/4, MCS-5 16QAM (generic labels) |
| IALA VDE draft annex 3 (ENAV16) | 2016 | [PDF](https://www.iala.int/content/uploads/2016/06/enav16_14_2_19_wg3_pdnr_annex_3_wd_v0_2.pdf) | low | FEC description | VDES | "turbo code with code rate 1/2 or lower", puncturing for other rates |
| US12184458B2, Carrier frequency offset synchronization method for the VDE-TER system | about 2024 | [Google Patents](https://patents.google.com/patent/US12184458) | low: terrestrial, not satellite | CFO from the phase difference between the two halves of a double-Barker training sequence | VDE-TER | not read in full |
| Central frequency offset estimation based on multicarrier VDES system (ICEIEC) | 2019 | [BIT pure](https://pure.bit.edu.cn/en/publications/central-frequency-offset-estimation-based-on-multicarrier-vdes-sy/) | none: multicarrier FMT variant | joint multi-carrier estimator | FMT VDES | no numbers |
| On the Interference from VDE-SAT Downlink to the Incumbent Land Mobile System | 2018 | [arXiv](https://arxiv.org/pdf/1810.01081) | none: interference study | n/a | n/a | n/a |

## 5. Verdict for the C6 "VDE-SAT" competitor

- Syncword length 27, pilot comb 27, one repeated pilot (1+j)/sqrt2, Nk = 66 in 1090: **we already use it**
  (`vde27`, `make_burst`).
- Pilot offset: **we are slightly behind the standard.** Fix it to first pilot 14 after the syncword end:
  `[k27][d13][k1]([d26][k1])x38[d23]`. Expected gain: about 0 dB (fidelity only). Cost: a new layout name or a rerun of
  the C6 points. Test: one C6 run at 0.15 at -3.0 dB and 1/2 at 2.0 dB, compared with the present `vde27`. The BLER
  should agree within its confidence interval.
- Link ID: **not applicable** to the known-symbol count. At most it is 16 symbols of non-payload overhead, and probably
  absent in SAT-MCS-1.50-1.
- Estimator: **we already use the same family** as the only published VDE-SAT CFO method (coarse correlation or ML on
  the syncword, then data-aided fine estimation over all known symbols, with lobe hypotheses). Nothing published beats
  it for this pattern as far as I could find. Real systems handle a +-4 kHz LEO Doppler that is out of our |f| <= 0.03
  range.

## Reference entries

1. ITU-R, Recommendation ITU-R M.2092-2 (02/2026), "Technical characteristics for VHF data exchange system in the
   maritime mobile service", Annex 5 (VDE-SAT), sections A5-2.10 "Pilots and syncword symbol location and modulation"
   and A5-2.12 "VHF data exchange-satellite link configuration formats".
   https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf ;
   TOC https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!TOC-HTM-E.htm .
   Taken: 27-symbol syncword and its bit pattern, d_p = 27, d_s = 2268, first pilot (1+d_p)/2 after the syncword, pilot
   (1+j)/sqrt2, burst totals. (Read through search-engine text excerpts; the PDF text could not be decoded here.)
2. ITU-R, Recommendation ITU-R M.2092-1 (02/2022), same title.
   https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-1-202202-I!!PDF-E.pdf . Taken: syncword modulation
   pi/4-QPSK (00/11 only).
3. ITU-R, Recommendation ITU-R M.2092-0 (10/2015). https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-0-201510-I!!PDF-E.pdf .
   Superseded; nothing taken.
4. IALA, Guideline G1139 "The Technical Specification of VDES", Edition 3, June 2019.
   https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf .
   Taken: ramp 14 / 14 symbols, 8 ms guard, (32,6) biorthogonal link ID.
5. ESA NAVISP, "ICING - Independent Critical Navigation" (NAVISP-EL3-010) document.
   https://navisp.esa.int/document/NAVISP%20EL3_010-ICING-Independent%20Critical%20Navigation.pdf . Cross-check of
   the syncword modulation per format.
6. "Frequency Offset Estimation Algorithm of VDES Signals Based on Cross-Correlation", IEEE conference paper, about 2019,
   IEEE Xplore document 8780774. https://ieeexplore.ieee.org/abstract/document/8780774 . Authors and venue not readable
   (IEEE blocked the fetch); abstract excerpt only.
7. A. Andreotti, F. Nanna, S. Andrenacci, A. Isca, H.-C. Haugli, N. Alagha, "On-field test campaign performance of
   VDE-SAT Link ID 20 over Norsat-2 LEO satellite", International Journal of Satellite Communications and Networking,
   vol. 41, no. 2, pp. 195-215, 2023.
   https://www.researchgate.net/publication/356135026_On-field_test_campaign_performance_of_VDE-SAT_Link_ID_20_over_Norsat-2_LEO_satellite ;
   https://dblp1.uni-trier.de/rec/journals/ijscn/AndreottiNAIHA23.html .
8. "VDES Performance Evaluation for Future e-navigation Services", SciTePress, 2018.
   https://www.scitepress.org/papers/2018/68502/68502.pdf .
9. IALA ENAV16 WG3 draft Annex 3 (VDE technical description, 2016).
   https://www.iala.int/content/uploads/2016/06/enav16_14_2_19_wg3_pdnr_annex_3_wd_v0_2.pdf .
10. US 12184458 B2, "Carrier frequency offset synchronization method for the VDE-TER system".
    https://patents.google.com/patent/US12184458 .
11. "Central frequency offset estimation based on multicarrier VDES system", ICEIEC 2019.
    https://pure.bit.edu.cn/en/publications/central-frequency-offset-estimation-based-on-multicarrier-vdes-sy/ .
