# Deployed preamble / pilot competitors: which to implement, and predictions vs blind (2026-11-15)

**Purpose.** Show that the blind receiver (0 known symbols) reaches the BLER of real preamble / pilot-based
single-carrier systems. Every competitor is simulated in the est4 framework: the 1024 data symbols carry the whole
codeword (N = 2048, CRC-16), the known symbols are EXTRA symbols in the burst, and their energy is charged on the SNR
axis (SNR = Es/N0 + 10 log10((1024 + Nk) / 1024)). Same CFO (|f| <= 0.03), noise, decoder (CA-SCL-8), re-encoding check
and fair metric-ordered CRC search (incl. alias / lobe hypotheses) for all. Sources: the surveys
`lit_real_space.md`, `lit_real_leo.md`, `lit_real_terrestrial.md`, `lit_real_wlan.md`, `lit_real_military.md`,
`lit_real_academic.md` (2026-11-15). Test status: `expected_est5.md`.

## How the predictions are made
Required SNR at a target BLER ~= genie SNR (true CFO and phase, no pilots) + pilot energy E + estimation loss d.
Calibrated on our measured est4 results (8.2a): 128-preamble ML at 2/5: 0.64 + 0.51 = 1.15 predicted, 1.16 measured;
DVB-RCS2 ID 13 at 2/5: 0.64 + 0.47 = 1.11 vs 1.10; 128 ML at 1/10: -5.19 + 0.51 = -4.68 vs -4.68. d ~ 0 when the pilots
resolve the CFO; d > 0 when alias / window misses or a weak coarse stage remain (DVB-RCS2 at 1/10: d = 0.63).

Reference SNRs [dB] (measured, 8.2a; lower is better):
| | 1/10 @ 1e-4 | 0.15 @ 1e-3 | 0.15 @ 1e-4 | 2/5 @ 1e-3 | 1/2 @ 1e-3 |
|---|---|---|---|---|---|
| **Blind (0 known symbols)** | **-4.9** | **-3.60** | **-2.98** | **0.61** | **1.79** |
| Genie (lower bound, no pilots) | -5.19 | -3.91 | -3.59 | 0.64 | 1.90 |
| DVB-RCS2 ID 13 (measured) | -4.09 | -3.45 | -3.12 | 1.10 | 2.33 |
| 128 preamble ML (measured) | -4.68 | -3.44 | -3.12 | 1.16 | 2.41 |
| 64 + 64 joint ML (measured) | -2.87 | -3.34 | -2.71 | 1.12 | 2.38 |
| 16 + 16 4th power (measured) | fails | fails | fails | fails | 2.77 |
(Blind beats its own genie at 2/5, 1/2 because its retries and joint list add decoding attempts.)

## Worth implementing (in est5 now)
| # | Competitor | Real system using it | Link | Known symbols (E) | Estimator chain | Predicted SNR: 1/10 @1e-4 / 0.15 @1e-3 / 2/5 @1e-3 / 1/2 @1e-3 | vs blind | Why include |
|---|---|---|---|---|---|---|---|---|
| C6 | **VDE-SAT** | VHF Data Exchange via satellite (maritime, ITU-R M.2092-2) | [ITU-R M.2092-2](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf) | 27-symbol syncword + 1 pilot / 27 symbols, ~65 (0.27 dB) | ML on syncword, Rife-Boorstyn on all known symbols, CRC search over +-1/27 alias lobes (alias peak ~0.59 of the true one) | -4.85 ... -4.6 / -3.6 ... -3.4 / 0.9 ... 1.0 / 2.15 ... 2.25 | tie at 1/10, 0.15; blind 0.3-0.4 dB better at 2/5, 1/2 | the real standard closest to our SNRs (its own thresholds Es/N0 -4.5 ... -0.6 dB) |
| C7 | **DVB-S2 style** | DVB-S2 / S2X broadcast and VSAT (PL header + pilot blocks) | [ETSI TR 102 376-1](https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf) | 90-symbol header + one 36-symbol pilot block, 126 (0.52 dB) | M&M on the header, then joint ML header + block with lobe search | -4.65 ... -4.5 / -3.4 ... -3.3 / 1.15 ... 1.2 / 2.4 ... 2.5 | blind better by 0.25 / 0.2 / 0.55 / 0.65 dB | the most widely deployed satellite standard |
| C8 | **CCSDS style** | NASA / ESA telemetry (CCSDS 131.2 SCCC: frame marker + 16-symbol pilot fields) | [CCSDS 130.11-G-2](https://public.ccsds.org/Pubs/130x11g2.pdf) | 8 blocks x 16, 128 (0.52 dB) | Rife-Boorstyn over all blocks + lobe search (block period ~146: aliases every ~0.0068), per-block phase + interpolation | -4.65 ... -4.3 / -3.4 ... -3.2 / 1.15 ... 1.25 / 2.4 ... 2.5 | blind better by 0.25-0.6 dB everywhere | space-agency practice; tests distributed short blocks with dense aliases |
| C9 | **ViaSat burst** | ViaSat return-link burst demodulators (patents) | [US 7653150](https://patents.google.com/patent/US7653150B2/en), [US 8243859](https://patents.google.com/patent/US8243859) | 16-symbol midamble unique word (0.07 dB) | 4th-power FFT over the burst, top-32 peaks each tested on the UW (pi/2 ambiguity), CRC search | fails / fails / 1.5 ... 2.5 / 2.2 ... 2.8 | blind far better (it works where 4th power fails) | the industry version of our own fast path; shows what "almost no pilots" costs without a decoder search |
| C10 | **DMRS 1/7** | LTE / NB-IoT uplink (NPUSCH: 1 reference symbol per 7) | [3GPP NB-IoT primer, arXiv 1606.04171](https://arxiv.org/pdf/1606.04171) | 1 pilot / 7 symbols, ~171 (0.69 dB) | Rife-Boorstyn over the pilots (range +-0.071, no aliases), pilot phase + interpolation / Kalman | -4.5 / -3.2 / 1.33 / 2.6 | blind better by 0.4-0.8 dB in AWGN; likely the best competitor under phase noise | dense-pilot cellular practice; the phase-noise reference |
| C11 | **400ZR style** | Coherent optics 400ZR (pilot every 32 symbols; tolerance +-1.8 GHz at 59.8 GBd = our 0.03) | [IEEE 802.3ct, Zhang 2019](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf) | 1 pilot / 32 symbols, 32 (0.13 dB) | 4th-power coarse, Rife-Boorstyn on the pilots, CRC search over +-1/32 alias lobes | -4.4 ... -3.9 / -3.5 ... -3.0 / 0.8 ... 1.0 / 2.05 ... 2.2 | the closest competitor at 2/5, 1/2 (lowest overhead); blind still 0.2-0.4 dB better | the only real system specified for exactly our CFO range |
| C12 | **Wi-Fi style** | IEEE 802.11 coarse/fine preamble estimation (also 802.11ad single carrier) | [MathWorks wlanCoarseCFOEstimate](https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html), [Liu et al. TCSI 2015](https://doi.org/10.1109/TCSI.2014.2361035) | 128-symbol preamble: 8 x 16 repeats (0.51 dB) | lag-16 autocorrelation coarse, lag-64 fine, CRC search over the +-1 fine lobes | -4.6 ... -4.3 / -3.4 ... -3.2 / 1.2 ... 1.3 / 2.45 ... 2.55 | blind better by 0.3-0.7 dB | the estimator every Wi-Fi chip runs (simpler than ML) |
| C13 | **MIL-110 HF** | Tactical HF modems, MIL-STD-188-110C (requirement +-75 Hz at 2400 Bd = 0.031, our range) | [MIL-STD-188-110C](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf) | preamble + known probe blocks scaled, ~308 (1.14 dB) | ML / R-B over all known symbols, per-probe phase + interpolation | -4.05 / -2.8 / 1.8 / 3.0 | blind better by 0.85-1.2 dB | heavy-pilot military practice for our exact CFO range |
| C14 | **hyb3** | Advantech satellite modems (patent; designed for +-3 % of Rs) | [US 7590199](https://patents.google.com/patent/US7590199) | 16 + 16 (0.13 dB) | sum of pilot and 4th-power log spectra, 3 CFO candidates decided by the decoder | fails / fails / 1.2 ... 2.0 / 2.2 ... 2.6 | blind better by >= 0.6 dB | a deployed "few pilots + decoder picks among candidates" hybrid |

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
