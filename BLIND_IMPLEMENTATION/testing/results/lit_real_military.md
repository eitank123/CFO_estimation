# Deployed single-carrier CFO estimation: military / tactical HF, SATCOM, aviation, maritime, underwater (2026-11-15)

Literature scout report. No simulations were run. Scope: real deployed (or standard-mandated) CFO / Doppler handling in
single-carrier PSK burst systems, compared with our blind receiver (1024 QPSK symbols, polar N = 2048 + CRC-16, rates
1/10, 0.15, 2/5, 1/2, Es/N0 -5 ... +3 dB, |f| <= 0.03 cycles/symbol, no pilots). New material only: the DVB-RCS2 chain,
polar code-aided sync and the general blind-CFO literature are in `lit_dvbrcs2.md`, `lit_polar_sync.md`,
`lit_blind_cfo.md` and are not repeated.

Conventions. f = df / Rs in cycles/symbol. Values marked **[derived]** are my arithmetic, not from the source.
HF standards quote SNR in a 3 kHz noise bandwidth; at 2400 Bd, Es/N0 = SNR_3kHz + 10 log10(3000/2400) =
SNR_3kHz + 0.97 dB **[derived]**. PDFs that the fetch tool could not parse were read through a public PDF-to-text
reader (r.jina.ai, given only the public URL); read depth is stated per source.

**Main comparability caveat.** Every deployed system found is data-aided (preamble, unique word, probes) and its
published low-SNR requirements are for fading HF channels with equalisers, not AWGN. None acquires a burst without known
symbols. Their numbers bound "what the field does", not what a blind decoder-search receiver can do.

---

## 1. Ranked takeaways

### T1. Our CFO range is exactly the tactical HF requirement; the field meets it with 11-50 % known symbols, tested at 30 dB
- MIL-STD-188-110C Appendix C (the 3.2-12.8 kbps serial waveforms of the STANAG 4539 class) and Appendix D (WBHF):
  acquire and keep sync with a **75 Hz offset, then -75 Hz** (C.6.3, D.6.4), and a **3.5 Hz/s sweep between -75 and
  +75 Hz** for 1 hour at BER <= 1e-5 (C.6.4, D.6.5). Symbol rate 2400 Bd (C.5.1). So **|f| <= 75 / 2400 = 0.03125
  cycles/symbol [derived]**: essentially our +-0.03. The STANAG 4285 receiver studied by QinetiQ (US7715499) also
  designs for +-75 Hz at 2.4 kBd.
- But: the +-75 Hz test is run at **30 dB average SNR** (C.6.3, D.6.4) and the Doppler-rate test at 24 dB; acquisition
  at low SNR is "not yet standardized" (C.6.2, D.6.3).
- Known-symbol budgets **[derived from the cited structures]**: 110C serial (5.3): 0.6 s preamble (3 x 200 ms segments
  = **1440 symbols**, longer than our whole burst) plus 16 known per 32 data at 2400 bps or 20 per 20 at 150-1200 bps
  (33-50 % known); 75 bps has no probes. 110C App C: 287-symbol preamble, then 31-symbol mini-probes after every 256
  data symbols (~11 %). App D WID 1/2 at 3 kHz: 48 data + 48 known per frame (50 %). STANAG 4285: 80-symbol preamble +
  3 x 16 probes per 256-symbol frame, i.e. 128 / 256 = 50 % known.
- Lowest low-SNR requirements: 110C serial 75 bps BER 1e-5 at SNR 2 dB (Es/N0 ~ 3.0 dB [derived]) in 2-path Rayleigh,
  5 Hz fading (Table XVI); App D WID 1 BER 1e-5 at about 3 dB in AWGN (Table D-LII, garbled extraction; Es/N0 ~ 4 dB
  [derived]) with 50 % known symbols. **Our operating points (-5 ... +3 dB Es/N0, 0 % known) are below every tactical
  HF requirement read.**
- Use: a presentation framing ("same Doppler range as MIL-STD-188-110C App C/D, zero overhead, several dB lower
  Es/N0"), and a reason not to expect a better military estimator to borrow: their advantage is overhead and SNR.

### T2. Competitor worth one cheap run: hybrid DA + NDA spectrum with a short candidate list chosen by the decoder (US7590199)
- Source: Alagha (Advantech), "Hybrid frequency offset estimator", US7590199B2, 2009
  ([Google Patents](https://patents.google.com/patent/US7590199)). DVB-RCS burst (48 known + 440 data), Ka-band
  uncertainty +-1800 Hz at 64 kBd = **+-3 % of Rs** (the patent's own number; = our 0.03).
- Method: DA branch r * conj(c) on the known symbols, NDA branch 4th power (QPSK) on the payload; both FFT'd, converted
  to log magnitude, weighted and **summed**; several local maxima are refined by parabolic interpolation and output
  as **3 CFO candidates; the decoder picks one**. No dB numbers in the part read (100k of 220k characters).
- Why: our 16 + 16 pre/post 4th-power receiver "fails" (BLER 0.5-0.9 below 0 dB; 2.77 dB at R = 1/2, 1e-3 vs blind
  1.79 dB, `08_parameters_results.md` 8.2a). The hybrid is the deployed fix for exactly that failure, and it costs
  2 FFTs + up to 3 CA-SCL-8 decodes, far below blind's MACs per core. It is the natural cheap pilot receiver between
  the 16 + 16 4th-power receiver and the 116-symbol DVB-RCS2 ID 13.
- Expected (my estimate, not a source number): helps at 2/5 and 1/2 (0 ... +3 dB) where the 4th-power peak is often in
  the top 3; should still fail at 1/10 and 0.15 (-5 ... -3 dB) where the 4th-power peak is buried. If it reaches
  ~2.2-2.4 dB at 1/2 it would sit between the 16 + 16 receiver and blind.
- How to test: a new est4 receiver `hyb3` on the 16 + 16 layout (K = 32, +0.13 dB charged): log|FFT_DA| + w log|FFT_NDA|
  over +-0.03, top-3 peaks + parabolic interpolation, pi/2 ambiguity from the 32 known symbols, CA-SCL-8 + re-encoding
  check per candidate in peak order (stop at first accept). Rates 2/5 (0 ... 1.5 dB) and 1/2 (1 ... 3 dB), plus 0.15
  at -3 dB as a sanity point; w in {0.5, 1} tuned on a small run.

### T3. "Military HF layout" competitor: predictable, so only for the presentation
- Scaling of 110C App C to 1024 data symbols **[derived]**: 184-symbol sync preamble + 4 mini-probes of 31 (after every
  256 data) = 308 known, energy charge 10 log10(1332/1024) = **+1.14 dB**. The DA-KS estimator (Rife-Boorstyn over all
  known symbols, already in est4) is far from threshold: CRB std of f with 308 known symbols spread over 1332 at
  Es/N0 = -5 dB is about 3e-5 cycles/symbol, edge phase error ~0.12 rad [derived, var = 1/(8 pi^2 SNR sum (t - tbar)^2)];
  each 31-symbol probe has ~10 dB block SNR. So its BLER ~ genie shifted by +1.14 dB: 1/10 at 1e-4 ~ -4.05 dB
  (blind -4.9), 0.15 at 1e-3 ~ -2.8 dB (blind -3.60), 2/5 at 1e-3 ~ 1.8 dB (blind 0.61), 1/2 at 1e-3 ~ 3.0 dB
  (blind 1.79) **[derived from the 8.2a genie numbers]**. A STANAG 4285 / WID 1 style 50 % layout would be ~+1.8 dB
  from genie.
- Verdict: blind wins by ~0.8-1.2 dB against the military HF overhead in AWGN. A run is optional (one est4 layout).
  In fading HF the known symbols also train the equaliser, so this comparison is AWGN-only and must be labelled so.

### T4. Deployed hypothesis banks and their straddle loss confirm our cell design; nothing to switch to
- Harris HPW acquisition (US7315588) runs **parallel branches mixed by fixed +- offsets (~800 Hz)** because a single
  estimator fails above ~800 Hz; QinetiQ (US7715499) reports that a conventional **10 Hz bin search over an 80-symbol
  STANAG 4285 preamble loses more than 2 dB between bins** (10 Hz / 2400 Bd = 0.0042 cycles/symbol [derived]; phase
  drift over 80 symbols at half a bin = 2 pi x 0.0021 x 80 = 1.05 rad [derived]) and replaces bins by basis-function
  combining. Our CFO grid x phase search with an edge drift of 0.48 rad per cell (04, 4.1) and Stage 3 refinement is
  the same idea with a tighter cell. Harris DAMA (US8054920) refines the FFT estimate by iterated half-block conjugate
  correlation (N = 3), analogous to our refinement step.
- Underwater single carrier (Perrine et al. 2010) uses a **windowed 4th-power DFT** for QPSK bulk + piecewise Doppler
  (pilot filter +-1 % of 62.5 kHz at 15.625 kBd = +-0.04 cycles/symbol [derived]); this is our fast path. Li et al.
  2008 search residual CFO on a grid by the energy of **known-zero (null) subcarriers**: the OFDM analogue of scoring a
  CFO grid by frozen-bit consistency. Neither works near our SNR.

### T5. False-alarm practice in deployed sync: fixed normalised thresholds checked on noise, PFA ~1e-6 per test
- Aeronautical-telemetry burst CPM (Hosseini & Perrins 2013): DA GLRT frame sync with 64 known symbols at Es/N0 = 1 dB:
  PD ~ 1 - 5e-7, **PFA ~ 4.9e-6**; with 32 known symbols, false locks dominate the BER loss at low SNR. Open HF modem
  (kg7hf): 9 x 32-chip block correlation normalised to 1, floor 0.35, max in 10 s of white noise 0.264. Harris DAMA
  (US8054920) adds a quad correlator to cut false start-of-message detections.
- Our CRC-16 + rho (RHO_N per rate) and the 0 / 9600 noise-only result are in line; the deployed habit to copy is to
  report PFA **per hypothesis tested and per packet**, at >= 1e6 noise trials (already our open item; no new test).

### Side finding: Doppler RATE is the one deployed requirement we do not model
- 110C C.6.4 / D.6.5: 3.5 Hz/s at 2400 Bd = k = 6.1e-7 cycles/symbol^2 [derived]. Over 1024 symbols (0.43 s) the CFO
  moves 1.5 Hz = 6.2e-4 cycles/symbol (2 % of our range), and the quadratic phase left after the best linear (CFO) fit
  peaks at about pi k N^2 / 8 = 0.25 rad [derived], half of our 0.48 rad cell-edge budget. A small check (linear CFO
  ramp, one rate at its waterfall) could go next to the phase-noise runs. Not simulated here.

Not applicable / not found: Link 16 (MSK chips + CCSK, frequency hopping; the one paper read uses +-20 kHz with a
32-pilot MSK block, no BLER); MIL-STD-188-181/182/183 UHF DAMA tolerance numbers (not found in open text, only Harris
patents); VDES / ITU-R M.2092 and Inmarsat aero burst specs (not found); ADS-B 1090ES and UAT (not searched this round);
underwater Doppler **scale** estimation (time compression a ~ 1e-3 in water; at RF the scale is negligible).

---

## 2. Per-source table

| # | Source, year | Link | Read | Relevance | Algorithm, overhead | Designed CFO -> \|f\| | SNR regime | Numbers | Comparability |
|---|---|---|---|---|---|---|---|---|---|
| 1 | MIL-STD-188-110C w/ Change 1 (US DoD) | [sigidwiki PDF](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf) | text reader, 400k of 437k chars | **high** | DA: preambles 1440 (serial), 287 (App C); probes 16/32, 20/20, 31/256, 48/48 | +-75 Hz @ 2400 Bd -> **0.031** [derived] (C.6.3, D.6.4); 3.5 Hz/s | tests at 30 / 24 dB; data reqs 2-11 dB SNR_3kHz | 75 bps 1e-5 @ 2 dB (fading); App C AWGN 9-27 dB; WID 1 AWGN ~3 dB; App B: +-20 Hz, sync in 2.5 s | same range; 11-50 % overhead; higher Es/N0 |
| 2 | Nieto, Furman (Harris), preamble performance slides, 2011 | [hfindustry PDF](https://hfindustry.com/_files/ugd/cbfc9b_d4e853dd64704b0fa83f8591add9e923.pdf) | search snippet only (404) | medium | 110A/110B preamble acquisition tests | random +-75 Hz -> 0.031 | | acquisition "several dB" below data SNR except 75 bps | numbers not read |
| 3 | kg7hf, "Acquisition: finding the burst" (open 110A modem) | [dev.to](https://dev.to/kg7hf/acquisition-finding-the-burst-i1l) | full | medium | DA lag-1 differential estimate over 288 preamble chips; 9-block normalised correlation; segment voting | estimate wraps at +-1200 Hz (0.5); gate +-120 Hz -> 0.05 | 4-10 dB examples | 37 Hz true -> 35.2-37.6 Hz at 10 dB; noise max 0.264 vs floor 0.35 | Kay-type DA; long preamble |
| 4 | Harris, US8054920B2, DAMA acquisition, 2011 | [Google Patents](https://patents.google.com/patent/US8054920) | 100k of 141k | medium | FFT on 64-symbol repeated BPSK preamble, then 3 iterations of half-block conjugate correlation | 0 and 100 Hz tested | Eb/N0 2 dB | qualitative only | DA |
| 5 | Harris (Hessel), US7315588B2, HPW acquisition, 2008 | [Google Patents](https://patents.google.com/patent/US7315588) | summary of full text | medium | 3 FM MLS x 31 + pure carrier, 23.7 ms; parallel branches at +- fixed offsets | single branch fails above ~800 Hz | not given | no PD/PFA | hypothesis bank (DA) |
| 6 | QinetiQ (Warner), US7715499B2, frequency-compensated reception, 2010 | [Google Patents](https://patents.google.com/patent/US7715499) | 100k of 136k | medium | basis-function (7) adaptive combining on 80-symbol STANAG 4285 preamble; bisection 10/5/1/0.1 Hz | +-75 Hz @ 2.4 kBd -> 0.031 | 3 dB sim (6 antennas), ~-10 dB SINR off-air (8 antennas) | 10 Hz bins lose > 2 dB between peaks; 62.6k vs 154k ops | DA, arrays + jammer |
| 7 | Wavecom, STANAG 4285 decoder help | [wavecom.ch](https://www.wavecom.ch/content/ext/DecoderOnlineHelp/worddocuments/stanag42851.htm) | full | medium | 80 preamble + 4 x 32 data / 3 x 16 probes per 256 | decoder centre adjustable +-400 Hz | | 50 % known [derived] | DA |
| 8 | sigidwiki, STANAG 4285 | [sigidwiki](https://sigidwiki.com/wiki/STANAG_4285) | full | low | rates 75-3600 bps, BPSK/QPSK/8PSK, FEC 1/16 ... 2/3 | not given | | 2400 Bd | |
| 9 | STANAG 4529 test plan (Scribd) | [scribd](https://www.scribd.com/document/461258872/STANAG-4529-4-02-04-v3) | search snippet only | low | | +-37.5 Hz incl. Doppler; 3.5 Hz/s | | symbol rate not read | |
| 10 | ETSI EN 301 841-1 V1.4.1, VDL Mode 2 ground equipment, 2015 | [etsi.org PDF](https://www.etsi.org/deliver/etsi_EN/301800_301899/30184101/01.04.01_60/en_30184101v010401p.pdf) | text reader, 100k of 125k | medium | D8PSK; training 5 ramp + 16-symbol UW + header | +-826 Hz (685 Tx + 141 Doppler) @ 10.5 kBd -> **0.079** [derived] | uncoded BER 1e-3 at -98 dBm | | high SNR, differential detection |
| 11 | TRW (Myers), EP1128621A2, D8PSK carrier/symbol sync, 2001 | [EPO PDF](https://data.epo.org/publication-server/rest/v1.2/patents/EP1128621NWA2/document.pdf) | front pages only | low | Doppler from stored preamble samples (DA) | not stated in read part | | none | |
| 12 | Jamal, Matolak, "Advanced PHY technologies in VDL", 2020 | [arXiv 2005.11456](https://arxiv.org/abs/2005.11456) | abstract | low | VDL 2/3 D8PSK vs LDPC / DFT-s-OFDM | | | none on sync | |
| 13 | Meng et al., S-AIS frequency offset in IF, Optoelectron. Lett. 2018 | [PDF](https://www.researching.cn/ArticlePdf/m00050/2018/14/4/2018-04-0301.pdf) | text reader, full | medium | DA (32-bit training + flag removes GMSK phase), interpolated FFT | +-3.8 kHz @ 9.6 kbps -> **0.40** [derived] | quoted 0 ... -20 dB; works below 3 dB | MSE ~1.7 dB above MCRB above 3 dB | GMSK, huge range |
| 14 | Doppler shift estimation for space-based AIS (Southampton), IEEE Access 2019 | [eprints](https://eprints.soton.ac.uk/431482/) | search snippet only (403) | low | Doppler estimator, Rician + non-Gaussian noise | ~ +-4 kHz (650 km LEO) | | not read | |
| 15 | Hosseini, Perrins, "Timing, carrier, frame sync of burst-mode CPM", IEEE TCOM 2013 | [ar5iv 1310.0757](https://ar5iv.labs.arxiv.org/html/1310.0757) | full | medium | DA joint ML (2 zero-padded FFTs + interpolation) on 64-symbol preamble; GLRT frame sync | ~ +-Rs (2 samples/symbol) | Es/N0 >= 0 dB | within 0.5 dB of CRB; PD 1 - 5e-7, PFA 4.9e-6 at 1 dB; 0.1 dB from ideal BER (L0 = 64) | aero telemetry, CPM |
| 16 | Ning et al., Link-16 joint frequency offset estimation, JEIT 2023 | [jeit.ac.cn](https://jeit.ac.cn/cn/article/doi/10.11999/JEIT220967) | abstract | low | autocorrelation + FFT peak + correction, then improved L&R | +-20 kHz; 32-symbol MSK pilot | "low SNR" | accuracy ~1e-5, near CRLB | MSK / hopping |
| 17 | Alagha, US7590199B2, hybrid frequency offset estimator, 2009 | [Google Patents](https://patents.google.com/patent/US7590199) | 100k of 220k | **high** | DA + 4th-power NDA log-spectra summed; 3 candidates; decoder chooses | +-1800 Hz @ 64 kBd -> **0.03** | below the QPSK NDA threshold | none in read part | closest deployed design to our fast path + candidates |
| 18 | Wang et al., iterative Doppler estimation in low-SNR satcom (GP + MLE + turbo), IWCMC 2020 | [PolyU](https://research.polyu.edu.hk/en/publications/iterative-doppler-frequency-offset-estimation-in-low-snr-satellit/) | abstract | medium | NDA coarse search by Gaussian-process optimisation + code-aided ML with turbo iterations | "large" | "low" | within 0.1 dB of ideal BER | code-aided NDA; no burst length given |
| 19 | Ciblat, Loubaton, Serpedin, Giannakis, IEEE TSP 2002 | [index](https://researchportal.ip-paris.fr/en/publications/blind-cyclostationary-statistics-based-carrier-frequency-offset-a/) | search snippets | low | conjugate cyclic frequency at 2 df (non-circular only) | | asymptotic | closed-form variance | QPSK is circular at order 2: reduces to 4th power |
| 20 | Yu, Shi, Su (NJIT / US Army CERDEC), MILCOM 2004 | [NJIT](https://digitalcommons.njit.edu/fac_pubs/20091) | abstract | low | blind autocorrelation-phase carrier estimate for AMR | | | none | SIGINT, no symbol knowledge |
| 21 | Vieira et al., NDA coarse CFO by spectral segmented regression, arXiv 2026 | [arXiv 2603.28262](https://arxiv.org/html/2603.28262) | 100k of 111k | low | PSD breakpoints, then 4th-power fine (range Rs/8) | up to GHz at 4-32 GBd | SNRb > 1 dB | worst errors 56 MHz - 1.69 GHz; ~2^18 symbols | optical, long observation |
| 22 | Perrine et al., Doppler estimation for shallow underwater comms, Asilomar 2010 | [UT PDF](https://users.ece.utexas.edu/~bevans/papers/2010/Doppler/UnderwaterAcousticCommDopplerAsil2010Draft.pdf) | text reader, full | medium | LFM + 4 x Barker-13 (Moose); windowed 4th-power DFT; pilot tone; spline resampling | pilot filter +-1 % of 62.5 kHz @ 15.625 kBd -> 0.04 [derived] | lake trials | 10-15 dB SNR gain with finer windows; 4096 symbols | NDA 4th power deployed; high SNR |
| 23 | Li, Zhou, Stojanovic, Freitag, Willett, IEEE JOE 2008 | [MIT PDF](https://web.mit.edu/people/millitsa/resources/pdfs/shengli-joe.pdf) | text reader, full | medium | scale from pre/postamble duration; residual CFO grid + refine on null-subcarrier energy | 77 Hz @ 27 kHz (8.3 kn); scale ~2.9e-3 [derived] | low (ISI-limited) | 6 / 21 packets with errors (1 element) | OFDM; idea analogous to frozen-bit scoring |
| 24 | Sharif et al., computationally efficient Doppler compensation, IEEE JOE 2000 | [Newcastle](https://eprints.ncl.ac.uk/62643) | search snippet only (403) | low | Doppler estimate + sample-rate conversion before DFE | +-2.6 m/s | | 16 kbit/s at sea | scale problem, not RF |

---

## 3. Competitor recommendation

| Name | Known symbols / energy | Estimator | Expected at our points | Priority |
|---|---|---|---|---|
| **hyb3** (US7590199 style) | 16 + 16 pre/post = 32 / +0.13 dB | log\|FFT_DA\| + w log\|FFT_4th\| over +-0.03, top-3 peaks, parabolic interpolation, decoder + rho picks | helps 2/5, 1/2 vs plain 4th power; still fails at 1/10, 0.15 (my estimate) | **run** (cheap; new information: is a 3-candidate list enough at high rate?) |
| **mil110C** (App C scaled) | 184 pre + 4 x 31 probes = 308 / +1.14 dB | DA-KS R&B over all known symbols (existing code) | ~genie + 1.14 dB: -4.05 / -2.8 / 1.8 / 3.0 dB at the 8.2a targets [derived] | optional (outcome predictable; presentation only) |
| **4285-style 50 %** | 512 known / +1.76 dB | DA-KS | ~genie + 1.76 dB [derived] | do not run (predictable) |

No deployed blind (pilot-free) estimator was found that works below the 4th-power threshold; the blind estimators in
military / SIGINT use (cyclostationary, autocorrelation phase, 4th power) are all variants of the NDA family that our
receiver already beats. The strongest pilot competitors remain DVB-RCS2 ID 13 and the 128-preamble ML of 8.2a.

---

## 4. Per-component verdict (vs the deployed systems of this survey)

| Component | Ours | Deployed practice | Verdict |
|---|---|---|---|
| Coarse CFO | 4th-power FFT fast path | 4th-power windowed DFT (underwater), DA FFT on preambles (HF, DAMA, AIS), hybrid DA + NDA (US7590199) | **use it** (NDA); the hybrid needs known symbols, so it is a competitor, not a change |
| Hypothesis search | CFO grid x phase, list-1 SC metric, checkpoints | parallel offset branches (HPW), 10 Hz bins (STANAG 4285, > 2 dB straddle loss), segment voting (110A) | **use it**, with a finer cell than the deployed bins |
| Fine CFO / phase | Stage 3 refinement, DD Newton | iterated half-block correlation (DAMA), probes + equaliser tracking (HF) | **use it**; probe tracking not applicable (no pilots) |
| Acceptance / false alarm | CRC-16 + rho | normalised correlation thresholds, GLRT PFA ~5e-6, quad correlators | **use it**; report PFA per hypothesis at 1e6 noise trials (open item) |
| Doppler rate | not modelled (static CFO) | 3.5 Hz/s over +-75 Hz (110C) | **not tested**: ~0.25 rad residual quadratic phase over the burst [derived]; small check suggested |
| Doppler scale | none | resampling (underwater) | **not applicable** at RF |

---

## 5. Not found / not read
- Low-SNR acquisition curves of 110C App C/D (the standard says "not yet standardized"; the Harris slides return 404;
  MILCOM papers paywalled). MIL-STD-188-181/182/183 numeric tolerances (only patents). VDES / M.2092 and Inmarsat aero
  R/T-channel specs. Ali / Koski / Nieto MILCOM full texts.

---

## Reference entries

### US DoD, MIL-STD-188-110C with Change Notice 1, "Interoperability and performance standards for data modems"
- Link: https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf   - Type: standard   - Read depth: full text via text reader, characters 0-400k of 437k
#### What it does
HF modem standard. Serial tone (5.3): 2400 Bd, 0.6 s / 4.8 s preamble (1440 / 11520 symbols [derived]), probes 16 per 32 data (2400 bps) or 20 per 20 (150-1200 bps); 75 bps BER 1e-5 at SNR_3kHz 2 dB in 2-path Rayleigh. App C: 287-symbol preamble, 31-symbol mini-probes per 256 data; App C/D require sync at +-75 Hz (|f| = 0.031 [derived]) tested at 30 dB SNR, and a 3.5 Hz/s sweep at 24 dB; acquisition at low SNR "not yet standardized". App D WID 1: 48 data + 48 known; ~3 dB AWGN for 1e-5 (garbled table).
#### What we took / could take
Framing of our +-0.03 range as the tactical HF requirement; "mil110C" layout for an optional competitor (T3); Doppler-rate value for a drift check.
#### Used in
-

### Nieto, J. W., Furman, W. N. (Harris), HF preamble performance presentation, 2011
- Link: https://hfindustry.com/_files/ugd/cbfc9b_d4e853dd64704b0fa83f8591add9e923.pdf   - Type: app note (slides)   - Read depth: snippet (URL returns 404)
#### What it does
Acquisition tests of 110A / 110B preambles with a random +-75 Hz offset; acquisition works several dB below the data SNR except at 75 bps (snippet).
#### What we took / could take
Not used: no numbers readable.
#### Used in
-

### kg7hf, "Acquisition: finding the burst" (open-source MIL-STD-188-110A modem, modem-core)
- Link: https://dev.to/kg7hf/acquisition-finding-the-burst-i1l   - Type: app note (blog + code)   - Read depth: full
#### What it does
DA lag-1 differential CFO estimate over the 288 known preamble chips (wraps at +-1200 Hz), gate +-120 Hz, 9 x 32-chip block correlation normalised to 1, floor 0.35, segment voting; 10 s white noise max 0.264.
#### What we took / could take
Example of deployed false-alarm practice (normalised threshold checked on noise, T5). The estimator is the Kay / M&M class already simulated.
#### Used in
-

### Harris Corp., US8054920B2, "Communications device and related method with improved acquisition estimates of frequency offset and phase error", 2011
- Link: https://patents.google.com/patent/US8054920   - Type: patent   - Read depth: 100k of 141k characters
#### What it does
UHF DAMA (MIL-STD-188-181B) BPSK: FFT over a 64-symbol repeated preamble, then 3 iterations of conjugate correlation between block halves to refine CFO; quad correlator against false start-of-message detection; tested at 0 and 100 Hz, Eb/N0 2 dB; qualitative gains only.
#### What we took / could take
Confirms iterative refinement after the FFT (our Stage 3). Not used otherwise (DA).
#### Used in
-

### Hessel, C. (Harris), US7315588B2, "System and method for enhanced acquisition for large frequency offsets and poor signal to noise ratio", 2008
- Link: https://patents.google.com/patent/US7315588   - Type: patent   - Read depth: full summary
#### What it does
HPW preamble (3 FM MLS x 31 + pure carrier, 23.7 ms); parallel receiver branches mixed by fixed +- offsets because one estimator fails above ~800 Hz; no SNR / PD numbers.
#### What we took / could take
Deployed example of a CFO hypothesis bank (T4); no change.
#### Used in
-

### Warner, E. S. (QinetiQ), US7715499B2, "Frequency compensated communications reception", 2010
- Link: https://patents.google.com/patent/US7715499   - Type: patent   - Read depth: 100k of 136k characters
#### What it does
Adaptive basis-function combining (7 functions) on the 80-symbol STANAG 4285 preamble, designed for +-75 Hz at 2.4 kBd (0.031 [derived]); a conventional 10 Hz bin search loses > 2 dB between bins; off-air detection at ~-10 dB SINR with 8 antennas.
#### What we took / could take
Straddle-loss evidence supporting our fine CFO cells (T4). Not used otherwise (DA, arrays).
#### Used in
-

### Wavecom, STANAG 4285 decoder online help
- Link: https://www.wavecom.ch/content/ext/DecoderOnlineHelp/worddocuments/stanag42851.htm   - Type: app note   - Read depth: full
#### What it does
STANAG 4285 frame: 80-symbol preamble + 4 x 32 data + 3 x 16 probes (256 symbols, 2400 Bd); 50 % known [derived]; decoder centre adjustable +-400 Hz.
#### What we took / could take
Overhead figure for the "4285-style" layout (not recommended to run).
#### Used in
-

### Signal Identification Wiki, "STANAG 4285"
- Link: https://sigidwiki.com/wiki/STANAG_4285   - Type: app note (wiki)   - Read depth: full
#### What it does
Rates 75-3600 bps, BPSK / QPSK / 8PSK at 2400 Bd, FEC 1/16 ... 2/3.
#### What we took / could take
Not used: background only.
#### Used in
-

### STANAG 4529 test plan (document on Scribd)
- Link: https://www.scribd.com/document/461258872/STANAG-4529-4-02-04-v3   - Type: standard (test plan)   - Read depth: snippet
#### What it does
Tolerate +-37.5 Hz frequency error including Doppler; 3.5 Hz/s rate (snippet).
#### What we took / could take
Not used: symbol rate not read, so not normalised.
#### Used in
-

### ETSI EN 301 841-1 V1.4.1 (2015), VHF air-ground Digital Link (VDL) Mode 2, Part 1: physical layer requirements
- Link: https://www.etsi.org/deliver/etsi_EN/301800_301899/30184101/01.04.01_60/en_30184101v010401p.pdf   - Type: standard   - Read depth: text reader, 100k of 125k characters
#### What it does
D8PSK at 10 500 symbols/s; training 5 ramp + 16-symbol UW + length + header FEC; receiver must meet uncoded BER 1e-3 at +-826 Hz offset (685 Hz Tx + 141 Hz Doppler) -> |f| = 0.079 [derived]; sensitivity -98 dBm.
#### What we took / could take
Not used: high-SNR differential detection; only a range reference.
#### Used in
-

### Myers, M. H. (TRW), EP1128621A2, "Carrier and symbol synchronisation for 8-DPSK signals", 2001
- Link: https://data.epo.org/publication-server/rest/v1.2/patents/EP1128621NWA2/document.pdf   - Type: patent   - Read depth: front pages / claims
#### What it does
VDL Mode 2 Doppler estimate from stored preamble samples (DA); no numbers in the read part.
#### What we took / could take
Not used.
#### Used in
-

### Jamal, H., Matolak, D. W., "Advanced physical-layer technologies in VHF data link communications", IEEE DASC 2020
- Link: https://arxiv.org/abs/2005.11456   - Type: paper   - Read depth: abstract
#### What it does
Compares VDL 2/3 (D8PSK) with LDPC / APSK / DFT-s-OFDM variants; no sync numbers in the abstract.
#### What we took / could take
Not used.
#### Used in
-

### Meng, X., Ma, S., Liu, C., Teng, J., "Frequency offset estimation in the intermediate frequency for satellite-based AIS signals", Optoelectronics Letters 14(4), 2018
- Link: https://www.researching.cn/ArticlePdf/m00050/2018/14/4/2018-04-0301.pdf   - Type: paper   - Read depth: full via text reader
#### What it does
DA: 32-bit training + start flag remove the GMSK phase, interpolated FFT; range > symbol rate (S-AIS Doppler +-3.8 kHz at 9.6 kbps -> 0.40 [derived]); MSE ~1.7 dB above MCRB above 3 dB SNR.
#### What we took / could take
Not used: GMSK, DA, much wider range and higher SNR.
#### Used in
-

### "Doppler shift estimation for space-based AIS signals over satellite-to-ship links", IEEE Access 2019 (University of Southampton)
- Link: https://eprints.soton.ac.uk/431482/   - Type: paper   - Read depth: snippet (403)
#### What it does
Doppler estimator for S-AIS under Rician fading and non-Gaussian noise; +-4 kHz range at 650 km LEO (snippet).
#### What we took / could take
Not used.
#### Used in
-

### Hosseini, E., Perrins, E., "Timing, carrier, and frame synchronization of burst-mode CPM", IEEE Trans. Commun. 61(12), 2013
- Link: https://ar5iv.labs.arxiv.org/html/1310.0757   - Type: paper   - Read depth: full
#### What it does
Aeronautical telemetry / TDMA burst CPM: DA joint ML on a 64-symbol optimised preamble (two zero-padded FFTs + interpolation), within 0.5 dB of the CRB down to ~0 dB Es/N0; GLRT frame sync PD ~1 - 5e-7, PFA ~4.9e-6 at Es/N0 = 1 dB; L0 = 32 suffers false locks.
#### What we took / could take
Deployed-style PFA target and per-test reporting (T5); the DA preamble competitor is already covered by our 128-preamble ML.
#### Used in
-

### Ning, X., Luo, H., Sun, Z., Diao, M., "Joint frequency offset estimation for Link-16 system in low signal-noise ratio scene", Journal of Electronics & Information Technology 45(10), 2023
- Link: https://jeit.ac.cn/cn/article/doi/10.11999/JEIT220967   - Type: paper   - Read depth: abstract
#### What it does
Coarse autocorrelation + FFT peak search, fine improved L&R; +-20 kHz, 32-symbol MSK pilot; accuracy ~1e-5, close to the CRLB.
#### What we took / could take
Not used: MSK / frequency hopping, DA.
#### Used in
-

### Alagha, N. S. (Advantech), US7590199B2, "Hybrid frequency offset estimator", 2009
- Link: https://patents.google.com/patent/US7590199   - Type: patent   - Read depth: 100k of 220k characters
#### What it does
DVB-RCS burst (48 known + 440 data); DA (r conj(c)) and 4th-power NDA spectra in the log domain, weighted and summed; several peaks + parabolic interpolation -> 3 CFO candidates, the decoder selects; designed for +-1800 Hz at 64 kBd = +-3 % of Rs (= our 0.03); no dB numbers in the read part.
#### What we took / could take
Proposed competitor "hyb3" on the 16 + 16 layout (T2): a cheap candidate-list pilot receiver between the 16 + 16 4th-power receiver and DVB-RCS2 ID 13.
#### Used in
-

### Wang, J., Jiang, C., Kuang, L., Guo, S., "Iterative Doppler frequency offset estimation in low SNR satellite communications", IWCMC 2020
- Link: https://research.polyu.edu.hk/en/publications/iterative-doppler-frequency-offset-estimation-in-low-snr-satellit/   - Type: paper   - Read depth: abstract
#### What it does
NDA coarse search by Gaussian-process optimisation of an objective + fine ML with turbo iterations; within 0.1 dB of ideal-sync BER, lower complexity than multi-step search.
#### What we took / could take
Not used: no burst length / range / SNR numbers; adaptive search was judged not a win for a 32-core MAC budget in lit_blind_cfo.md (cross-entropy item).
#### Used in
-

### Ciblat, P., Loubaton, P., Serpedin, E., Giannakis, G. B., blind cyclostationary-statistics-based CFO estimation for noncircular transmissions through frequency-selective channels (exact title truncated in the index read), IEEE Trans. Signal Process. 50(1), pp. 130-140, 2002
- Link: https://researchportal.ip-paris.fr/en/publications/blind-cyclostationary-statistics-based-carrier-frequency-offset-a/   - Type: paper   - Read depth: snippet
#### What it does
Blind CFO from the conjugate cyclic frequency at 2 df of non-circular (e.g. BPSK) signals over unknown channels; closed-form asymptotic variance.
#### What we took / could take
Not applicable: QPSK is circular at order 2; the QPSK analogue is the 4th-power estimator we already use.
#### Used in
-

### Yu, Z., Shi, Y. Q., Su, W., "A blind carrier frequency estimation algorithm for digitally modulated signals", IEEE MILCOM 2004, vol. 1, pp. 48-54
- Link: https://digitalcommons.njit.edu/fac_pubs/20091   - Type: paper   - Read depth: abstract
#### What it does
Blind carrier estimate from autocorrelation phases, iterative refinement, for automatic modulation recognition (no knowledge of symbol rate or constellation); no numbers in the abstract.
#### What we took / could take
Not used: SIGINT setting, coarse accuracy.
#### Used in
-

### Vieira, I. P., Serra, G. V., Colares, R. A., Mello, D. A. A., "Spectral segmented linear regression for coarse carrier frequency offset estimation in optical LEO satellite communications", arXiv 2603.28262, 2026
- Link: https://arxiv.org/html/2603.28262   - Type: paper   - Read depth: full (first 100k of 111k characters)
#### What it does
NDA coarse CFO from PSD breakpoints, then 4th-power fine (range Rs/8); works for SNRb > 1 dB; uses ~2^18 symbols; ~60N operations after the FFT.
#### What we took / could take
Not applicable: needs very long observations.
#### Used in
-

### Perrine, K. A., Nieman, K. F., Henderson, T. L., Lent, K. H., Brudner, T. J., Evans, B. L., "Doppler estimation and correction for shallow underwater acoustic communications", Asilomar 2010
- Link: https://users.ece.utexas.edu/~bevans/papers/2010/Doppler/UnderwaterAcousticCommDopplerAsil2010Draft.pdf   - Type: paper   - Read depth: full via text reader
#### What it does
Single-carrier QPSK, 15.625 kBd, 4096 symbols, 62.5 kHz carrier: LFM + 4 x Barker-13 (Moose) bulk estimate, windowed 4th-power DFT (1-8 windows), pilot tone (+-1 % filter -> +-0.04 cycles/symbol [derived]), spline resampling; up to 10-15 dB SNR gain with finer windows.
#### What we took / could take
Confirms the 4th-power NDA fast path as deployed practice (T4); not used otherwise.
#### Used in
-

### Li, B., Zhou, S., Stojanovic, M., Freitag, L., Willett, P., "Multicarrier communication over underwater acoustic channels with nonuniform Doppler shifts", IEEE J. Oceanic Eng. 33(2), 2008
- Link: https://web.mit.edu/people/millitsa/resources/pdfs/shengli-joe.pdf   - Type: paper   - Read depth: full via text reader
#### What it does
Doppler scale from preamble / postamble duration, resampling, then residual CFO by a coarse grid + refinement on the energy of null subcarriers; 27 kHz carrier, up to 8.3 kn (77 Hz); 6 / 21 packets with errors (single element).
#### What we took / could take
Conceptual analogue of scoring a CFO grid by known-zero (frozen) structure; not applicable directly (OFDM, scale problem).
#### Used in
-

### Sharif, B. S., Neasham, J., Hinton, O. R., et al. (author list to be checked against DOI 10.1109/48.820736), "A computationally efficient Doppler compensation system for underwater acoustic communications", IEEE J. Oceanic Eng. 25(1), pp. 52-61, 2000
- Link: https://eprints.ncl.ac.uk/62643   - Type: paper   - Read depth: snippet (403)
#### What it does
Doppler estimation + sample-rate conversion as a pre-processor to adaptive single-carrier receivers; 16 kbit/s at up to +-2.6 m/s in North Sea trials.
#### What we took / could take
Not applicable: Doppler scale (time compression) problem, negligible at RF.
#### Used in
-
