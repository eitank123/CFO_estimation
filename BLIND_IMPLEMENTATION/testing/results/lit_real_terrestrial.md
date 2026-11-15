# Deployed single-carrier CFO estimation outside space: coherent optics, cable / PON bursts, cellular, microwave

Literature scout report, 2026-11-15. No simulations were run. Numbers marked **[derived]** are my own arithmetic from
the cited numbers, not from a source. f = CFO / symbol rate (cycles/symbol). Our setting: 1024 QPSK data symbols,
|f| <= 0.03, Es/N0 -5 ... +3 dB, single burst, no pilots (blind) vs 128 / 116 / 32-known-symbol competitors (08, 8.2a).
This report only adds material not in `lit_dvbrcs2.md`, `lit_polar_sync.md`, `lit_blind_cfo.md`.

SNR conversion used for optics: Es/N0 = OSNR + 10 log10(12.5 GHz / Rs) (0.1 nm reference bandwidth, per polarisation).

---

## 1. Ranked takeaways

1. **Our CFO range matches the deployed 400ZR value exactly.** 400ZR: laser frequency accuracy ±1.8 GHz, Rx frequency
   offset tolerance ±1.8 GHz (IEEE 802.3ct baseline from the OIF IA; several module datasheets quote ±3.6 GHz,
   Tx + LO), at 59.84375 GBd -> **|f| = 0.0301 (±1.8 GHz) or 0.060 (±3.6 GHz) [derived]**. So |f| <= 0.03 is a
   realistic, cited operating range, not a stress case. But 400ZR works at **Es/N0 about 19 dB** (OSNR tolerance 26 dB
   [derived]) on a continuous stream, where the FOE averages over far more than 1024 symbols. Its frame has a
   **pilot every 32 symbols (3.1 %)** and an 11-symbol training sequence per 3712-symbol DSP sub-frame; the pilots are
   for "carrier phase recovery and absolute phase detection" (Inphi/Cisco 2018 slides). Pilot-only range 1/64 = 0.0156
   < 0.0301 [derived], so the coarse FOE in 400ZR must be blind (vendor DSPs, algorithm not in the IA as far as could
   be read). ([IEEE 802.3ct, Zhang 2019](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf),
   [Lyubomirsky 2018](https://grouper.ieee.org/groups/802/3/B10K/public/18_09/lyubomirsky_b10k_01a_0918.pdf))
2. **The deployed blind (4th-power) FOE family has a threshold at Es/N0 about 2.5 ... 5.5 dB for N = 1024 symbols,
   i.e. above our whole SNR range.** Li, Zhao, Chen 2014 (28 GBd QPSK, 1024 samples, ±3 GHz = |f| <= 0.107 [derived]):
   the multi-lag least-squares 4th-power estimator reaches about 8.2 x MCRB at OSNR 11.5 dB (Es/N0 8.0 dB [derived]),
   but its variance "drops dramatically" only when OSNR rises from 6 to 9 dB (Es/N0 2.5 ... 5.5 dB [derived]); the
   classic lag-1 (Leven 2007) estimator is 2.7e5 x MCRB at 11.5 dB OSNR. This is the same sample count as our burst and
   independently confirms our 8.2a finding that the 4th-power receiver "fails" below 0 dB. No deployed optical
   estimator is designed for one-shot acquisition at -5 dB. ([Li 2014 PDF](https://lightweb.ie.cuhk.edu.hk/wp-content/uploads/publication/1658737499249-Least-squares_carrier_frequency_offset_estimation_for_coherent_optical_QPSK_receivers.pdf))
3. **Every deployed burst system (DOCSIS upstream, coherent PON upstream, GSM, LTE / NR PRACH, NB-IoT NPRACH) uses
   known symbols with a data-aided estimator** (differential / Mengali-Morelli / least squares / correlation peak),
   and either a small CFO range or a high SNR:
   DOCSIS |f| < 0.015 at SNR > 25 dB with a periodic preamble of <= 37 ... 75 symbols, variance about 0.5 dB above the
   CRB; coherent PON |f| <= 0.25 (±3.5 GHz at 15 GBd) at SNR 18 dB with a 272-symbol CAZAC preamble; GSM a 26-symbol
   midamble with LS + averaging over bursts at |f| of order 1e-3 ... 6e-3 [derived]. Our 128-preamble ML / M&M
   competitor already represents this class; **no new estimator from these systems would beat it at our SNRs.**
4. **One new competitor is worth considering: a "400ZR-style" distributed-pilot receiver** (pilot every 32 symbols,
   K = 32 extra pilots for 1024 data, energy cost 0.13 dB [derived]) with blind 4th-power coarse + pilot DA
   Rife-Boorstyn fine + CRC lobe search (pilot alias spacing 1/32 = 0.03125, so 2-3 lobes inside ±0.03). It is the
   deployed optical frame structure, and it isolates "few, spread pilots + blind coarse" from our "many pilots" (116 /
   128) competitors. Expected (rough, [derived], must be simulated): the pilot fine estimate is accurate (CRB std
   1.2e-4 cycles/symbol at -5 dB), but the pilot peak SNR is only 32 x 0.316 = 10 dB at -5 dB vs 15.6 dB for DVB-RCS2
   ID 13, so lobe / outlier errors should dominate at R = 1/10 and 0.15; at 2/5 and 1/2 (0.5 ... 2 dB) it should come
   close to DVB-RCS2 ID 13 at a third of the pilot energy. Cost: one 4th-power FFT + a 32-point pilot correlation per
   lobe + up to 3 CA-SCL decodes - far below blind.
5. **NB-IoT / PRACH show the 3GPP false-alarm practice and the first NN detectors**: NPRACH requirement Pd >= 99 %,
   Pfa <= 0.1 % (TS 36.104 via Chougrani 2021), CFO removed by DL sync (residual ±600 Hz on 3.75 kHz tones in NTN,
   0.16 subcarrier); the detector is CFO-insensitive (|DFT| of differential symbol-group products). An NN receiver
   (NVIDIA 2022) gains up to 8 dB in false-negative rate over that baseline. Our acceptance targets are far stricter
   (wrong-accept < 1e-5); nothing to borrow for the CFO stage, the NN result only supports ML-assisted gates in general.

---

## 2. Per-source table

| # | Source | Year | Link | Read | Relevance | Algorithm | Designed CFO range -> \|f\| | SNR (Es/N0) | Numbers | Comparability vs us |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Zhang, Lyubomirsky, Maj (Inphi), "Proposal for 400GBASE-ZR DWDM optical specs baseline", IEEE P802.3ct | 2019 | [PDF](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf) | full (11 slides) | **high**: deployed CFO range | (spec, no algorithm) | Rx FO tolerance ±1.8 GHz, laser accuracy ±1.8 GHz, 59.84375 GBd -> 0.0301 [derived] | OSNR tol. 26 dB -> 19.2 dB [derived] | linewidth <= 500 kHz -> 8.4e-6 per laser x Ts [derived]; CFEC | same \|f\|; SNR 20+ dB higher; continuous stream |
| 2 | Lyubomirsky et al. (Inphi, Cisco), "400G FEC and framing for 80 km" | 2018 | [PDF](https://grouper.ieee.org/groups/802/3/B10K/public/18_09/lyubomirsky_b10k_01a_0918.pdf) | full (11 slides) | **high**: deployed pilot structure | DSP frame 3712 symbols, 49 per super-frame; 11-symbol TS; QPSK pilot every 32 symbols (PRBS10) for phase recovery and absolute phase | pilot-only range 1/64 = 0.0156 [derived] | - | pilot overhead 1/32 = 3.1 %; CFEC NCG 10.8 dB, OH 14.8 % | frame layout usable as a competitor template |
| 3 | OIF, letter to IEEE 802.3 on 400ZR | 2017 | [PDF](https://www.ieee802.org/3/minutes/nov17/incoming/OIF_to_IEEE_802d3_Nov_2017.pdf) | full (3 pages) | medium | super-frame 181 888 symbols, pilot after every 31 data symbols, 3712-symbol sub-frame | line clock ±20 ppm (this is the symbol clock, not the carrier) | - | DP-16QAM 59.84375 GBd | confirms #2 |
| 4 | OIF-400ZR-02.0 Implementation Agreement | 2020+ | [PDF](https://www.oiforum.com/wp-content/uploads/OIF-400ZR-02.0.pdf) | **not read** (PDF not parseable here) | high | - | - | - | - | numbers taken from #1, #2 instead |
| 5 | Module datasheets (400ZR QSFP-DD / OSFP) | - | [Skylane](https://www.skylaneoptics.com/app/uploads/2023/11/OBDTUSEN0101000_Datasheets_EN.pdf), [ProLabs](https://prolabs.com/Datasheets/OSFP-400GB-DCO-ZR-C_datasheets_EN.pdf) | search snippet only | medium | - | Rx offset tolerance ±3.6 GHz -> 0.060 [derived] | - | - | worst case Tx + LO |
| 6 | Li, Zhao, Chen, "Least-squares CFO estimation for coherent optical QPSK receivers", CSNDSP | 2014 | [PDF](https://lightweb.ie.cuhk.edu.hk/wp-content/uploads/publication/1658737499249-Least-squares_carrier_frequency_offset_estimation_for_coherent_optical_QPSK_receivers.pdf) | full | **high**: NDA threshold at N = 1024 | 4th power, phase differences at lags 1..M, unwrap, LS slope | ±3 GHz at 28 GBd -> 0.107 [derived] | OSNR 5-25 dB -> 1.5 ... 21.5 dB [derived] | N = 1024: LS-64 var < 8.2 x MCRB at Es/N0 8 dB; lag-1 (Leven) > 2.7e5 x MCRB; threshold OSNR 6-9 dB (2.5-5.5 dB Es/N0); 512 samples, M = 16: std < 3 MHz = 1.1e-4 [derived]; linewidth 100 kHz +25 % std | same N, blind, QPSK, AWGN + Wiener: **directly comparable**; shows NDA is dead below ~3 dB |
| 7 | Leven, Kaneda, Koc, Chen, "Frequency estimation in intradyne reception", IEEE PTL 19(6) | 2007 | [Nokia Bell Labs](https://www.nokia.com/bell-labs/publications-and-media/publications/frequency-estimation-in-intradyne-reception/) | abstract / index only | medium (classic baseline) | 4th-power lag-1 differential phase, feed-forward | range ±Rs/8 = 0.125 (per #6, #9) | - | see #6 (2.7e5 x MCRB at 8 dB) | classic optical NDA |
| 8 | Selmi, Jaouen, Ciblat et al., "Accurate digital FO estimator for coherent PolMux QAM", ECOC | 2009 | [IP Paris](https://researchportal.ip-paris.fr/en/publications/accurate-digital-frequency-offset-estimator-for-coherent-polmux-q/) | abstract | low-medium | blind spectral (periodogram) FOE for QAM | not given | - | "accuracy of a few kHz" at 100 Gb/s | high SNR, long blocks |
| 9 | NEC Labs, US 8 463 121, "Ultra wide-range FOE for digital coherent optical receivers" | 2013 | [Google Patents](https://patents.google.com/patent/US8463121) | description | medium: why NDA range limits matter | coarse: Gardner timing-error MPE + LUT; fine: FFT M-th power | M-th power limit ±Rs/(2M) = 0.125; cascaded ±0.9 Rs; commercial lasers ±2.5 GHz -> offsets up to ±5 GHz; ±5.4 GHz at 10.75 GBd = 0.50 [derived] | OSNR 9 dB at 10.75 GBd -> 9.7 dB [derived] | coarse accuracy about ±1 GHz | high SNR, long streams |
| 10 | Sun, Jiang, ..., Zhuge, "Preamble design for joint frame sync, FOE and channel estimation in upstream burst-mode coherent PON" | 2024 | [arXiv 2409.14400](https://www.arxiv.org/pdf/2409.14400) | full | **high**: modern optical **burst** receiver | 272-symbol CAZAC preamble (2 units x 2 x (64 + 4 GI)); FOE = M&M-type average of arg R(m+2) - arg R(m) over lags (Eq. 28), range ±Rs/4; pilot 1 in 32 for CPR | ±3.5 GHz at 15 GBd -> 0.233 [derived] | SNR 18 dB (sim.), 14-18 dB (exp.) | mean abs FOE error about 1 MHz (6.7e-5) at L = 2, block 64; < 3 MHz over ±3.5 GHz; exp. error < 0.4 MHz over ±1.5 GHz; earlier preambles 1792 / 416 / 496 symbols | preamble 272 of 32 768 payload (0.83 %); SNR 15-23 dB above ours; same class as our 128-preamble M&M |
| 11 | Berscheid, Salt, Nguyen (Vecima), US 8 755 462, "Frequency offset estimator for upstream cable signals" | 2014 | [Google Patents](https://patents.google.com/patent/US8755462) | description | **high** for DOCSIS | periodic preamble 3 x M symbols; average of N - M elementary differential estimators (lag 1 or lag M); unbiased under micro-reflection ISI | "almost certain" < 1.5 % of Rs -> 0.015; tolerable 3/(8M) cycles/symbol | SNR > 25 dB "typical" | var = 1/(M^2 (N - M) SNR); best 27/(4 N^3 SNR), about 0.5 dB above CRB; N <= 37 (75); micro-reflections up to -10 dBc, 7 symbols | short preamble, high SNR, small range; estimator = M&M class |
| 12 | Berscheid, Salt, Nguyen, "An economical, ISI-immune frequency offset estimator for DOCSIS upstream channels", IEEE T-BC | 2012 | [dblp](https://dblp.dagstuhl.de/rec/bibtex/journals/tbc/BerscheidSN12), DOI 10.1109/TBC.2012.2190192 | abstract (via search) | medium | same as #11 | - | high SNR | "approaches the CRB at high SNR" | as #11 |
| 13 | Chougrani, Kisseleff, Martins, Chatzinotas, "NB-IoT random access for NTN: preamble detection and uplink sync" | 2021 | [arXiv 2101.08079](https://arxiv.org/pdf/2101.08079) | full | medium: 3GPP detection practice | NPRACH single-tone hopping, 3.75 kHz SCS; detection = |DFT| of differential symbol-group products (CFO-insensitive); CFO pre-compensated from DL sync | terrestrial: CFO "negligible"; NTN residual ±600 Hz = 0.16 of 3.75 kHz SCS | per-3.75 kHz SNR: Pmd 1e-2 at 2.6 ... 15.5 dB (32 / 64 reps) | 3GPP: Pd >= 99 %, Pfa <= 0.1 % | OFDM-style tones, long repeated preambles, CFO removed beforehand: not comparable |
| 14 | Authors not recorded (code at github.com/NVlabs/nprach_synch), "Deep learning-based synchronization for uplink NB-IoT" | 2022 | [arXiv 2205.10805](https://arxiv.org/html/2205.10805v2) | full HTML (text) | low-medium | residual CNN for detection + ToA + CFO on NPRACH | trained on ±25 ppm at 3.4 GHz (as stated) | figures only | up to 8 dB FNR gain at 1e-3 vs #13's baseline; FPR lower | NN replaces a DA detector; no CRB, no complexity numbers |
| 15 | US 10 582 545, "Restricted set of cyclic shifts for LTE PRACH" | - | [Google Patents](https://patents.google.com/patent/US10582545) | first 100k of 138k chars | medium | LTE high-speed restricted set: ZC cyclic shifts excluding Doppler aliases; PDPs of 5 windows combined | designed up to 1 PRACH SCS = 1.25 kHz; new set ±2.5 kHz; 430 km/h at 2.6 GHz -> 2.07 kHz. Per ZC sample (839 x 1.25 kHz) 1.25 kHz -> 1.2e-3 [derived]; per PRACH subcarrier 1.0 | - | - | preamble detection, not data-burst CFO; CFO mostly removed by DL sync |
| 16 | US 7 570 719, "Receiver and a receiving method" (GSM BTS, high-speed train) | 2009 | [Google Patents](https://patents.google.com/patent/US7570719) | description summary | medium | LS frequency estimate on 26-symbol training sequence (+ tails after pre-filter), adaptive averaging over bursts (step 0.008), LMMSE per-burst residual | 180 Hz, 470 Hz test offsets; 130 / 500 km/h at 1800 MHz (Doppler 833 Hz at 500 km/h [derived]); at 270.833 kbaud: 470 Hz -> 1.7e-3, 2 x 833 Hz -> 6.2e-3 [derived] | raw BER target 1.6-3.2 % (RXQUAL 4) | mean error -> 0 after about 600 bursts | multi-burst tracking; one-shot 26-symbol estimate useless at -5 dB (see 4.2) |
| 17 | 3GPP TS 45.010 cl. 5, 6 (via itecspec index) | - | [itecspec](https://itecspec.com/spec/3gpp-45-010-6-ms-requirements-for-synchronization) | search snippet only (page 404 on fetch) | low-medium | - | MS 0.1 ppm (GSM 400: 0.2 ppm) relative to BTS; BTS 0.05 ppm. 0.1 ppm at 900 MHz = 90 Hz -> 3.3e-4 [derived] | - | - | spec numbers not read in full |
| 18 | Comtech EF Data MM200 high-speed microwave modem manual, p. 30 | - | [manualsdir](https://www.manualsdir.com/manuals/761315/comtech-ef-data-mm200.html?page=30) | page text | medium: microwave acquisition | user-set acquisition sweep window; shrinks with QAM order and noise | QPSK "over ±1 MHz", 256-QAM "as low as ±50 kHz"; 3.5-28 Msps -> QPSK 0.036 ... 0.29, 256-QAM 0.0018 ... 0.014 [derived] | high (QAM) | - | continuous link, sweep acquisition, high SNR |
| 19 | Xie, Raybon, "Digital PLL based FO compensation and CPE for 16-QAM coherent optical systems", ECOC | 2012 | [Nokia Bell Labs](https://www.nokia.com/bell-labs/publications-and-media/publications/digital-pll-based-frequency-offset-compensation-and-carrier-phase-estimation-for-16-qam-coherent-optical-communication-systems/) | catalog abstract via search (page 403) | low-medium | 2nd-order digital PLL + FO compensation + pilot-aided cycle-slip recovery | up to 10 % of Rs -> 0.1 | - | earlier methods "only about 100 MHz at 28 GBaud" (0.0036) | tracking loop, high SNR |
| 20 | Thomsen, Maher, Millar, Savory, "Burst mode receiver for 112 Gb/s DP-QPSK with parallel DSP", Opt. Express 19(26) | 2011 | [index](https://www.bohrium.com/paper-details/burst-mode-receiver-for-112-gb-s-dp-qpsk-with-parallel-dsp/813350038351642625-513) | abstract snippet | medium | blind burst recovery with commercial tunable laser; 4th-power periodogram FOE (per #6 ref. [5]) | not read | - | switching < 150 ns (companion paper) | high SNR |
| 21 | Pittala et al., CAZAC training-aided FOE / frame sync (TUM) | 2013-14 | [TUM portal](https://portal.fis.tum.de/en/publications/training-aided-frequency-offset-estimation-in-16-qam-nyquist-tran/) | search snippet only (PDF blocked) | low | CAZAC training-aided feed-forward FOE | ±3.6 GHz (Rs not read) | - | - | same class as #10 |
| 22 | PS-QAM blind FOE (IEEE Photonics J. 2022; Opt. Express 2022) | 2022 | [DOAJ](https://doaj.org/article/7a26dcdc264f42c793cd4396c8773f4f) | search snippet only | low | QPSK-partition / radius-directed 4th power for shaped QAM | not given | - | 71 % lower complexity than RD 4th-power FFT at equal MI | shaping not relevant to QPSK |

**Searched, not found or not readable:** the OIF 400ZR / 800ZR IA text (PDFs not parseable; 800ZR pilot density and
FO tolerance therefore not confirmed); the DOCSIS 3.0 PHY spec text (CM frequency accuracy, preamble tables);
3GPP TS 36.211 / 38.211 PRACH text; LTE / NR PUSCH DMRS-based CFO estimators beyond patent snippets (±1 kHz ... ±1.7
kHz ranges, 15 kHz SCS: 0.07 ... 0.11 of a subcarrier [derived], snippet only); TETRA / P25 / DMR frequency tolerances
and burst-sync CFO estimators (no source found); PON burst mode for IM/DD (no CFO problem, skipped); DSL (OFDM, skipped).

---

## 3. Per-component verdict (deployed terrestrial practice vs our receiver)

| Component | Deployed practice (sources) | Verdict |
|---|---|---|
| Coarse CFO | optics: blind 4th-power periodogram / multi-lag LS (#6, #7, #9, #20), designed at Es/N0 >= 8 ... 19 dB; bursts: preamble DA (#10, #11, #16) | **we already use it** (4th-power FFT fast path, lag-4 autocorrelation). Multi-lag LS (#6) = Fitz / L&R family; at our SNRs it is below threshold like ours. No switch. |
| Fine CFO / phase | optics: pilot every 32 symbols + phase recovery, PLL with pilot cycle-slip recovery (#2, #19); PON: pilot 1/32 + ML CPR (#10); GSM: LS on midamble + tails, multi-burst averaging (#16) | **not applicable** to a pilot-free burst; the pilot-based variants are competitor material (finding 4). Our code-aided refinement has no deployed terrestrial analogue. |
| Hypothesis search | LTE PRACH restricted sets (search over ZC shifts with Doppler aliases, #15); microwave sweep acquisition (#18) | **we already go further** (CFO x phase grid scored by the decoder). Deployed searches are over timing / sequence, not CFO with a decoder metric. |
| Acceptance / false alarm | 3GPP NPRACH Pd >= 99 %, Pfa <= 0.1 % (#13); CRC on data | **we already use stricter checks** (CRC-16 + rho, wrong-accept < 1e-5 targets). |
| Complexity | 400ZR CFEC 420 mW at 7 nm (#2); FOE cost minimised by lag-difference estimators instead of FFT (#6) | **not comparable**: optical DSP amortises FOE over a continuous stream; no per-burst MAC numbers found. |
| ML gates | NN NPRACH detector, up to 8 dB FNR gain (#14) | **we already use** NN / logistic gates; consistent. |

---

## 4. Competitor recommendation

### 4.1 Worth adding: C4 "400ZR-style" distributed pilots (optional, cheap to build from existing code)
- Layout: 1024 data + 32 extra QPSK pilots, one after every 31 data symbols (pilot period 32; the last 0-1 data
  symbols after the last pilot), PRBS-type random QPSK pilot values; energy cost 10 log10(1056/1024) = 0.13 dB.
- Chain (as 400ZR modules would do it, the algorithm is vendor-specific, so this is my reconstruction):
  (a) blind 4th-power FFT coarse over the whole burst (our fast-path code); (b) pilot DA Rife-Boorstyn on the 32 pilots
  (zero-filled periodogram, the DVB-RCS2 DA-PL code with P = 32) to refine; the pilot alias spacing 1/32 = 0.03125 means
  the coarse estimate selects the lobe; (c) if the coarse estimate is unreliable, CRC search over the 2-3 pilot lobes
  inside ±0.03 (same back-end as the 64+64 joint ML CRC search); (d) phase from the pilots (constant, or pilot phase
  smoothing as C1b in `lit_dvbrcs2.md`). CA-SCL-8, rho check, energy charged as in 8.2a.
- Expected (rough, [derived]): pilot CRB std = sqrt(6 / (4 pi^2 P^2 K (K^2 - 1) SNR)) = 1.2e-4 cycles/symbol at
  -5 dB (P = 32, K = 32), fine enough; but coherent pilot energy K x SNR = 10 dB at -5 dB (vs 15.6 dB for DVB-RCS2
  ID 13's 116 known symbols), so lobe picks and outliers should cost about 1 dB or more at R = 1/10 and 0.15; at R = 2/5
  and 1/2 (0.5 ... 2 dB, K x SNR 15.6 ... 17 dB) it should be within a few tenths of a dB of DVB-RCS2 ID 13 with 0.34 dB
  less pilot energy. Without step (c) it inherits the 4th-power failure below about 0 dB (8.2a row "16 + 16, 4th
  power: fails").
- Test: rates 1/10, 0.15, 2/5, 1/2 at the 8.2a SNR grid, 480k packets per point like the other pilot receivers.

### 4.2 Not worth adding
- **GSM-style midamble (26 symbols)**: one-shot CRB at -5 dB, N = 26: std = sqrt(6 / (4 pi^2 N (N^2 - 1) SNR)) =
  5.2e-3 cycles/symbol, i.e. 2 pi x 5.2e-3 x 512 = 17 rad of phase drift at the burst edge [derived]: useless without
  multi-burst averaging, which our single-packet setting does not allow.
- **DOCSIS periodic preamble / coherent-PON CAZAC preamble**: estimators are M&M-class, about 0.5 dB above the CRB
  (#11), i.e. what our 128-preamble ML / M&M receiver already does; DOCSIS range 0.015 is half of ours.
- **Multi-lag LS 4th-power (#6)** as a separate NDA competitor: same threshold as our 4th-power fast path (fails below
  about 3 dB at N = 1024); it would only reproduce the "fails" row. Could be cited instead of simulated.
- **PRACH / NPRACH**: preamble detection on OFDM tones with CFO pre-removed by DL sync; different problem.

### 4.3 How to phrase the comparison in the report
"Deployed single-carrier systems with a CFO range like ours (400ZR: ±1.8 GHz at 59.84 GBd, |f| = 0.030) operate
20+ dB above our SNR and estimate the CFO blind over continuous streams with a pilot every 32 symbols for phase;
deployed burst systems (DOCSIS, coherent PON, GSM) use preambles or midambles with M&M / LS estimators at SNR >= 14 dB.
None acquires |f| <= 0.03 in a single 1024-symbol burst at Es/N0 <= 3 dB; the closest published blind estimator
(multi-lag 4th-power LS, N = 1024) has its threshold at about 2.5 ... 5.5 dB Es/N0."

---

## Reference entries

# Zhang, B., Lyubomirsky, I., Maj, T., "Proposal for 400GBASE-ZR DWDM optical specs baseline", IEEE P802.3ct interim, Salt Lake City, May 2019
- Link: https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf   - Type: standard contribution   - Read depth: full
## What it does
Rx / Tx spec tables taken from OIF 400ZR: Rx frequency offset tolerance ±1.8 GHz (Tx offset from ITU grid), laser
frequency accuracy ±1.8 GHz, linewidth <= 500 kHz, OSNR tolerance 26 dB (CFEC threshold), DP-16QAM 59.84375 GBd
±20 ppm. |f| = 0.0301 [derived]; Es/N0 about 19.2 dB [derived]; linewidth x Ts = 8.4e-6 per laser [derived].
## What we took / could take
Citation that our |f| <= 0.03 equals a deployed CFO tolerance; also gives a realistic phase-noise point (about 1.7e-5
for two lasers [derived]) at the low end of our Wiener range.
## Used in
-

# Lyubomirsky, I., Smith, B., Riani, J., Bhoja, S., Nicholl, G., Nowell, M., Villarruel, F., "400G FEC and framing for 80km", IEEE 802.3 B10K, Sept. 2018
- Link: https://grouper.ieee.org/groups/802/3/B10K/public/18_09/lyubomirsky_b10k_01a_0918.pdf   - Type: standard contribution   - Read depth: full
## What it does
OIF 400ZR DSP frame: 3712-symbol frames, 49 per super-frame, 11-symbol training sequence, QPSK pilot every 32 symbols
(PRBS10, different X / Y seeds) for carrier phase recovery and absolute phase detection; CFEC (staircase 255/239 +
Hamming 128/119), NCG 10.8 dB, 14.8 % OH. Pilot-only CFO range 1/64 = 0.0156 [derived].
## What we took / could take
Template for the optional C4 "400ZR-style" pilot competitor (pilot period 32, 32 pilots per 1024 data, 0.13 dB).
## Used in
-

# OIF Technical Committee (Otto, K.-H.), letter to IEEE 802.3 "400ZR Interop Project", Nov. 2017
- Link: https://www.ieee802.org/3/minutes/nov17/incoming/OIF_to_IEEE_802d3_Nov_2017.pdf   - Type: standard (liaison)   - Read depth: full
## What it does
Super-frame 181 888 symbols over 5 SC-FEC blocks, pilot after every 31 data symbols, 3712-symbol sub-frames, DP-16QAM
59.84375 GBd, line clock ±20 ppm (symbol clock tolerance, not carrier).
## What we took / could take
Confirms the pilot density of the Lyubomirsky 2018 entry. Not used otherwise.
## Used in
-

# OIF, "Implementation Agreement 400ZR" OIF-400ZR-02.0
- Link: https://www.oiforum.com/wp-content/uploads/OIF-400ZR-02.0.pdf   - Type: standard   - Read depth: not read (PDF not parseable)
## What it does
The normative 400ZR IA; its numbers were taken from the IEEE contributions above.
## What we took / could take
Not used directly: should be checked in a PDF viewer before quoting clause numbers.
## Used in
-

# 400ZR module datasheets (Skylane OBDTUSEN0101000; ProLabs OSFP-400GB-DCO-ZR-C)
- Link: https://www.skylaneoptics.com/app/uploads/2023/11/OBDTUSEN0101000_Datasheets_EN.pdf   - Type: app note / datasheet   - Read depth: snippet
## What it does
Rx frequency offset between carrier and LO -3.6 ... +3.6 GHz; LO has the same ±1.8 GHz accuracy as the Tx. |f| = 0.060 [derived].
## What we took / could take
Upper bound of deployed optical CFO (2x our range). Not used otherwise.
## Used in
-

# Li, M., Zhao, J., Chen, L.-K., "Least-squares carrier frequency offset estimation for coherent optical QPSK receivers", CSNDSP 2014, pp. 40-43
- Link: https://lightweb.ie.cuhk.edu.hk/wp-content/uploads/publication/1658737499249-Least-squares_carrier_frequency_offset_estimation_for_coherent_optical_QPSK_receivers.pdf   - Type: paper   - Read depth: full
## What it does
Blind 4th-power CFO from phase differences at lags 1..M, unwrapped, least-squares slope. 28 GBd QPSK, Wiener phase,
range ±3 GHz (|f| <= 0.107 [derived]). N = 1024: LS-64 variance < 8.2 x MCRB at OSNR 11.5 dB (Es/N0 8.0 dB
[derived]); lag-1 (Leven 2007) > 2.7e5 x MCRB; threshold between OSNR 6 and 9 dB (Es/N0 2.5 ... 5.5 dB [derived]).
512 samples, M = 16: std < 3 MHz (1.1e-4 cycles/symbol [derived]); 100 kHz linewidth +25 % std.
## What we took / could take
Independent evidence, at our exact burst length, that NDA 4th-power estimation breaks down above our SNR range
(supports the 8.2a "4th power fails" row and the need for decoder-aided search). Could be cited instead of simulating
another NDA competitor.
## Used in
-

# Leven, A., Kaneda, N., Koc, U.-V., Chen, Y.-K., "Frequency estimation in intradyne reception", IEEE Photon. Technol. Lett. 19(6), 366-368, 2007
- Link: https://www.nokia.com/bell-labs/publications-and-media/publications/frequency-estimation-in-intradyne-reception/   - Type: paper   - Read depth: abstract / index
## What it does
Classic optical feed-forward 4th-power differential (lag-1) frequency estimator, range ±Rs/8.
## What we took / could take
Classic baseline only; our lag-4 autocorrelation is a variant. Not used.
## Used in
-

# Selmi, M., Jaouen, Y., Ciblat, P., et al., "Accurate digital frequency offset estimator for coherent PolMux QAM transmission systems", ECOC 2009
- Link: https://researchportal.ip-paris.fr/en/publications/accurate-digital-frequency-offset-estimator-for-coherent-polmux-q/   - Type: paper   - Read depth: abstract
## What it does
Blind spectral (periodogram) FOE adapted to QAM; accuracy of a few kHz at 100 Gb/s.
## What we took / could take
Not used: high SNR, long blocks.
## Used in
-

# NEC Laboratories America, US 8 463 121 B2, "Ultra wide-range frequency offset estimation for digital coherent optical receivers", 2013
- Link: https://patents.google.com/patent/US8463121   - Type: patent   - Read depth: description
## What it does
States the M-th power range limit ±Rs/(2M) (±Rs/8 for QPSK); commercial lasers ±2.5 GHz -> up to ±5 GHz offsets;
coarse stage from Gardner timing-error maximum phase error + LUT (about ±1 GHz accuracy), fine FFT M-th power;
cascaded range about ±0.9 Rs in simulation (OSNR 9 dB, 10.75 GBd).
## What we took / could take
Context: deployed optics needs |f| up to 0.1-0.5 at 10 GBd class. Not used.
## Used in
-

# Sun, Y., Jiang, H., Xu, Y., Fu, M., Zhu, Y., Yi, L., Hu, W., Zhuge, Q., "Preamble design for joint frame synchronization, frequency offset estimation, and channel estimation in upstream burst-mode detection of coherent PONs", arXiv 2409.14400, 2024
- Link: https://www.arxiv.org/pdf/2409.14400   - Type: paper   - Read depth: full
## What it does
272-symbol CAZAC preamble shared by frame sync, FOE and channel estimation; FOE = averaged lag-2 phase increments of
the preamble autocorrelation (M&M type), range ±Rs/4 (±3.5 GHz at 15 GBd, |f| <= 0.233 [derived]); payload pilot
1 in 32 for CPR. SNR 18 dB: mean abs FOE error about 1 MHz (6.7e-5 [derived]), < 3 MHz over the full range;
experiment < 0.4 MHz over ±1.5 GHz vs a 4th-power reference. Prior burst preambles: 1792, 416, 496 symbols.
## What we took / could take
Shows modern optical burst receivers use a DA preamble + M&M, i.e. our 128-preamble M&M competitor class. Not used otherwise.
## Used in
-

# Berscheid, B., Salt, J. E., Nguyen, H. H. (Vecima Networks), US 8 755 462 B2, "Frequency offset estimator for upstream cable signals", 2014
- Link: https://patents.google.com/patent/US8755462   - Type: patent   - Read depth: description
## What it does
DOCSIS 3.0 upstream: CFO "almost certain" < 1.5 % of Rs (|f| < 0.015); SNR typically > 25 dB; periodic preamble of
3M symbols (N <= 37, extended to 75), composite of differential elementary estimators, unbiased under micro-reflection
ISI (up to -10 dBc, 7 symbols); variance 27/(4 N^3 SNR), about 0.5 dB above the CRB.
## What we took / could take
Cable burst practice = short DA preamble + M&M-class estimator at high SNR and half our CFO range; covered by our
128-preamble competitor. Not used otherwise.
## Used in
-

# Berscheid, B., Salt, J. E., Nguyen, H. H., "An economical, ISI-immune frequency offset estimator for DOCSIS upstream channels", IEEE Trans. Broadcasting, 2012, DOI 10.1109/TBC.2012.2190192
- Link: https://dblp.dagstuhl.de/rec/bibtex/journals/tbc/BerscheidSN12   - Type: paper   - Read depth: abstract
## What it does
Journal version of the Vecima estimator; approaches the CRB at high SNR; preamble condition for unbiased estimation under ISI.
## What we took / could take
Not used (see the patent entry).
## Used in
-

# Chougrani, H., Kisseleff, S., Martins, W. A., Chatzinotas, S., "NB-IoT random access for non-terrestrial networks: preamble detection and uplink synchronization", arXiv 2101.08079, 2021
- Link: https://arxiv.org/pdf/2101.08079   - Type: paper   - Read depth: full
## What it does
NPRACH (3.75 kHz single-tone hopping, format 1, 32 / 64 repetitions) detection by |DFT| of differential symbol-group
products, insensitive to CFO; CFO pre-compensated from DL sync (residual ±600 Hz = 0.16 SCS in NTN, negligible
terrestrially). 3GPP targets Pd >= 99 %, Pfa <= 0.1 %; Pmd 1e-2 at per-tone SNR 2.6 ... 15.5 dB.
## What we took / could take
Shows how 3GPP sets detection / false-alarm targets; not applicable to our CFO stage.
## Used in
-

# Authors not recorded (code at github.com/NVlabs/nprach_synch), "Deep learning-based synchronization for uplink NB-IoT", arXiv 2205.10805, 2022
- Link: https://arxiv.org/html/2205.10805v2   - Type: paper   - Read depth: full HTML text (figures not read)
## What it does
Residual-CNN detector + ToA + CFO estimator for NPRACH; up to 8 dB FNR gain at 1e-3 over the Chougrani baseline;
trained with CFO uniform in ±25 ppm at 3.4 GHz (as stated); no complexity numbers.
## What we took / could take
Supports NN-assisted detection gates in general; nothing concrete to borrow.
## Used in
-

# US 10 582 545, "System and method for controlling network traffic by restricting a set of cyclic shifts for LTE PRACH preambles"
- Link: https://patents.google.com/patent/US10582545   - Type: patent   - Read depth: first 100k of 138k characters
## What it does
LTE high-speed restricted set designed for CFO up to one PRACH SCS (1.25 kHz); proposed second set up to ±2.5 kHz;
430 km/h at 2.6 GHz gives 2.07 kHz; receiver combines power-delay profiles of 5 detection windows.
## What we took / could take
Not applicable: preamble detection over ZC shifts, CFO mostly removed by DL sync.
## Used in
-

# US 7 570 719 B2, "Receiver and a receiving method" (GSM BTS frequency offset estimation for high-speed trains)
- Link: https://patents.google.com/patent/US7570719   - Type: patent   - Read depth: description summary
## What it does
LS frequency estimate from the 26-symbol training sequence (+ tails after a pre-filter), adaptive average over
bursts (step 0.008, converges in about 600 bursts), LMMSE per-burst residual; tested at 180 / 470 Hz and 130 / 500
km/h at 1800 MHz (|f| about 1.7e-3 ... 6.2e-3 at 270.833 kbaud [derived]).
## What we took / could take
Shows GSM relies on multi-burst averaging; a one-shot 26-symbol estimate at -5 dB is useless (CRB std 5.2e-3
[derived]). Not used.
## Used in
-

# 3GPP TS 45.010, "Radio subsystem synchronization", clauses 5-6 (via itecspec index)
- Link: https://itecspec.com/spec/3gpp-45-010-6-ms-requirements-for-synchronization   - Type: standard   - Read depth: snippet (fetch returned 404)
## What it does
MS carrier within 0.1 ppm (GSM 400: 0.2 ppm) of the received BTS signal; BTS source 0.05 ppm (pico 0.1 ppm).
## What we took / could take
Shows cellular CFO is tiny relative to Rs (about 3e-4 [derived]) because the MS locks to the downlink. Not used.
## Used in
-

# Comtech EF Data, "MM200 High-Speed Microwave Modem, Installation and Operation Manual", TM086 Rev. 4.1, p. 30
- Link: https://www.manualsdir.com/manuals/761315/comtech-ef-data-mm200.html?page=30   - Type: app note / manual   - Read depth: page text
## What it does
User-set demodulator acquisition window: QPSK over ±1 MHz, 256-QAM as low as ±50 kHz; 3.5-28 Msps
(QPSK |f| about 0.036 ... 0.29, 256-QAM 0.0018 ... 0.014 [derived]); noise shrinks the window.
## What we took / could take
Microwave modems acquire by sweeping on continuous, high-SNR links. Not used.
## Used in
-

# Xie, C., Raybon, G., "Digital PLL based frequency offset compensation and carrier phase estimation for 16-QAM coherent optical communication systems", ECOC 2012
- Link: https://www.nokia.com/bell-labs/publications-and-media/publications/digital-pll-based-frequency-offset-compensation-and-carrier-phase-estimation-for-16-qam-coherent-optical-communication-systems/   - Type: paper   - Read depth: abstract via search (page 403)
## What it does
Second-order digital PLL with FO compensation and pilot-aided cycle-slip recovery; tolerates FO up to 10 % of Rs.
## What we took / could take
Not used: tracking loop on continuous streams.
## Used in
-

# Thomsen, B. C., Maher, R., Millar, D. S., Savory, S. J., "Burst mode receiver for 112 Gb/s DP-QPSK with parallel DSP", Opt. Express 19(26), B770, 2011
- Link: https://www.bohrium.com/paper-details/burst-mode-receiver-for-112-gb-s-dp-qpsk-with-parallel-dsp/813350038351642625-513   - Type: paper   - Read depth: abstract snippet
## What it does
Blind burst-mode coherent reception with a commercial tunable laser and parallel DSP; equalizer initialisation to
avoid CMA singularity; 4th-power periodogram FOE (per Li 2014 ref. [5]).
## What we took / could take
Not used (high SNR); cited as the first blind optical burst receiver.
## Used in
-

# Pittala, F. et al., "Training-aided frequency offset estimation in 16-QAM Nyquist transmission" (TUM)
- Link: https://portal.fis.tum.de/en/publications/training-aided-frequency-offset-estimation-in-16-qam-nyquist-tran/   - Type: paper   - Read depth: snippet
## What it does
CAZAC training-aided feed-forward FOE, evaluated for offsets up to ±3.6 GHz.
## What we took / could take
Not used (same class as Sun 2024).
## Used in
-

# Blind FOE for probabilistically shaped QAM (IEEE Photonics Journal 2022, DOAJ record)
- Link: https://doaj.org/article/7a26dcdc264f42c793cd4396c8773f4f   - Type: paper   - Read depth: snippet
## What it does
Multi-stage FOE for PS-QAM where the 4th-power peak is submerged; 71 % lower complexity than radius-directed
4th-power FFT at equal MI.
## What we took / could take
Not used: QPSK only in our study.
## Used in
-
