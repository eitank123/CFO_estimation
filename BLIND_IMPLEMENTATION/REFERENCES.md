# References: every source cited in the blind CFO project

One registry of every paper, standard, patent and application note cited in the project (built 2026-11-15 from
`testing/results/lit_blind_cfo.md` (survey 1), `lit_polar_sync.md` (survey 2), `lit_dvbrcs2.md`,
`lit_checks_results.md`, `expected_*.md`, `DEAD_ENDS.md`, `01`-`08`, `est3/README.md` and the root `README.md`). Merged 2026-11-15: the "Reference entries" of `lit_card_sat.md`, `lit_card_space.md`, `lit_card_terr.md`
and `lit_rates.md` (C1-C4, C13, C16, C17 updated; A16, C18-C83 added).
Merged 2026-11-17: the "Reference entries" of `lit_turbo_db.md`, `lit_vde_fec.md` and `lit_polar_ratematch.md` (A6, A7,
A16, C1, C16, C84, C86-C88 updated; A17-A22, C90-C94, C96, C97, C99, C100, C104-C106, C108-C110, C112 added; index rows for the
earlier C84-C88 added). Numbers
C89, C95, C98, C101-C103, C107, C111, C113, C114 are not used (the scouts' duplicates of existing entries, or polar
papers moved to section A); the lit files cite the registry numbers.
Each source has its own section below: full reference, link, type, read depth (as recorded in the lit file that cited
it), what it does, what we took / could take, and a dated "Used in" log.

**Rules.**
- Every new source gets a section here; every change in the project that comes from a source adds a dated line to its
  "Used in" section (file / run.py variant / expected_*.md and the measured result).
- Only the main session edits this file. Other agents put their entries in a "Reference entries" section of their own
  `lit_real_*.md` / `lit_adopt_*.md` files; the main session merges them here. Those surveys are in progress and will
  add more sources.
- Read depth: "full" = full text; "abstract"; "snippet" = only search-result text or an index page; "bib" = only the
  bibliographic record / abstract was checked when this registry was built (classic baselines cited in the code and
  READMEs that were never surveyed in a lit file). Numbers come from our lit files and results, not from new reading.

Status words: **adopted** (in a project receiver or the testing receiver), **passed / proposed** (passed its test,
adoption is the user's call), **in test**, **tested-dropped** (see DEAD_ENDS.md), **competitor** (implemented as a
benchmark receiver / estimator), **reference only**.

---

## Index (by topic)

| # | Reference | Type | What we took (one line) | Status |
|---|---|---|---|---|
| **A** | **Polar codes and decoders** | | | |
| A1 | Arikan 2009, Channel polarization | paper | the polar code, SC decoding | adopted (base) |
| A2 | Tal & Vardy 2015, List decoding of polar codes | paper | SCL / CA-SCL-8 decoder | adopted (base) |
| A3 | Balatsoukas-Stimming, Bastani Parizi, Burg 2015, LLR-based SCL | paper | LLR path metric = our CFO detector; hardware cycle model | adopted (metric); cycle model reference only |
| A4 | Sarkis, Giard, Vardy, Thibeault, Gross 2014, Fast polar decoders | paper | Fast-SSC node rules (rate-0 / rate-1 / REP / SPC) of the list-1 metric | adopted |
| A5 | Hashemi, Condo, Gross 2017, Fast and flexible SCL | paper | Fast-SSCL node splits (decoder, lit_checks FastSCL) | adopted |
| A6 | He et al. 2017, beta-expansion (polarization weight) | paper | PW reliability order, beta = 2^(1/4) | adopted (code construction) |
| A7 | 3GPP TS 38.212 (NR channel coding) | standard | CRC polynomials | adopted |
| A8 | Yuan & Parhi 2016, multi-bit SCL | paper | fixed-point word lengths (6-bit LLR) | reference only |
| A9 | Seah, Rubenacke, Gross 2026, speculative SC | paper | none (latency, not MACs) | reference only |
| A10 | Shen et al. 2025, SO Fast SCL (WCNC) | paper | none yet | reference only |
| A11 | Shen, Wu, Gao et al. 2026, node-based SO Fast SCL | paper | possible soft symbols for pns | reference only |
| A12 | Lulei et al. 2025, subcode ensemble decoding | paper | none | reference only |
| A13 | Aharoni, Huleihel, Pfister, Permuter 2023, neural polar codes | paper | SCT cost statement | reference only |
| A14 | Wang, Liu, Hou 2014, joint SC over ISI | paper | none (SC trellis too costly) | reference only |
| A15 | Fazeli, Mansour, Zhu, Jalloul 2026, partially polarized codes | paper | none (needs a code change) | reference only |
| A16 | Polyanskiy, Poor, Verdu 2010, finite blocklength | paper | normal-approximation bound for a 1024-symbol packet (section E) | reference only |
| A17 | Bioglio, Condo, Land 2021, Design of polar codes in 5G NR | paper | NR mother-length rule, 7/16 switch, pre-freezing (rate matching) | reference only (rate matching proposed) |
| A18 | Bioglio, Gabry, Land 2017, puncturing and shortening of polar codes | paper | N-agnostic bit-reversal puncture / shorten rule (n_max = 12) | reference only (rate matching proposed) |
| A19 | Niu et al. 2023, A golden decade of polar codes | paper | polar vs LTE turbo numbers (code-only gain) | reference only |
| A20 | Stitched polar codes 2025 (arXiv 2511.19249) | paper | rate-matching sub-optimality <= 0.3 dB (SC) | reference only |
| A21 | Niu, Chen, Lin 2013, rate-compatible punctured polar codes (ICC) | paper | QUP puncturing, "> 0.7 dB" vs turbo (snippet) | reference only |
| A22 | Miloslavskaya 2015, Shortened polar codes (T-IT) | paper | none (shortening-pattern search, snippet) | reference only |
| **B** | **Classic and NN CFO / phase estimators** | | | |
| B1 | Rife & Boorstyn 1974 | paper | periodogram ML = our 4th-power FFT core; DVB-RCS2 competitor CFO | adopted + competitor |
| B2 | Kay 1989 | paper | benchmark estimator (A.17.3) | competitor |
| B3 | Fitz 1994 | paper | M&M + Fitz fine stage (A.17.3) | competitor |
| B4 | Luise & Reggiannini 1995 | paper | M&M + L&R fine stage (A.17.3) | competitor |
| B5 | Mengali & Morelli 1997 | paper | the M&M baseline (exactly per paper) | competitor (main baseline) |
| B6 | Morelli & Mengali 1998, feedforward tutorial | paper | NDA threshold argument | reference only |
| B7 | Morelli & Mengali 1999, BLUE | paper | est3 periodic-preamble estimator | competitor |
| B8 | Morelli & Mengali 2000, selective channels | paper | est3 joint CFO / channel ML | competitor |
| B9 | Moose 1994 | paper | est3 periodic-preamble estimator | competitor |
| B10 | Schmidl & Cox 1997 | paper | est3 periodic-preamble estimator | competitor |
| B11 | Aboutanios & Mulgrew 2005 | paper | interpolation for the ML periodogram (A.17.3, est3) | competitor |
| B12 | Candan 2013 | paper | est3 Jacobsen-Candan estimator | competitor |
| B13 | Viterbi & Viterbi 1983 | paper | 4th-power phase (fast path phase4) | adopted |
| B14 | Casini, De Gaudenzi, Ginesi 2004, DVB-S2 modem | paper | est3 DVB-S2 block phase-difference estimator | competitor |
| B15 | Li Zhen et al. 2024, Clustering-NN CFO | paper | est3 NN competitor | competitor |
| B16 | Chen et al. 2023, DL frequency offset estimation | paper | none (NN regressor not better at low SNR) | reference only |
| **C** | **Standards, burst modems, pilot placement** | | | |
| C1 | ETSI EN 301 545-2 V1.3.1 / V1.5.1 (2026, current; DVB-RCS2 lower layers) | standard | ID 13 burst layout scaled to 1024 data (est4 RCS2-13; ID 13 unchanged in V1.5.1) | competitor |
| C2 | ETSI TR 101 545-4 V1.1.1 (DVB-RCS2 guidelines) | standard | CFO range 0.5-3 % of Rs; operating points; "no TC-LM sync algorithm" | reference only |
| C3 | ETSI TR 101 545-4 V1.2.1 (2026) | standard | ToC check; cl. 10.2.1 MODCOD thresholds (SE comparison) | reference only |
| C4 | Griebel, Wasenmuller et al. 2021, FFT interpolation for DVB-RCS2 | paper | DA-KS R&B + parabolic interpolation (est4 RCS2-13, RCS2 pre/post) | competitor |
| C5 | Ali, Wasenmuller, Wehn 2014 (CSNDSP), pilotless bursts | paper | none (not read) | reference only |
| C6 | Ali, Wasenmuller, Wehn 2014 (ICSPCS), pilot-assisted bursts | paper | none (not read) | reference only |
| C7 | MathWorks dvbrcs2WaveformGenerator | app note | field ranges | reference only |
| C8 | MathWorks DVB-RCS2 TC-LM link example | app note | a working pilot chain (cross-check) | reference only |
| C9 | ESA US7409024 (Ginesi et al.), pilot-aided phase sync | patent | PA-SWI idea behind the RCS2-13 track arm | competitor (idea) |
| C10 | Ying & Ghogho 2005, optimal pilot placement | paper | split pre/post placement (split64; fairness argument) | competitor (design rule) |
| C11 | Spalvieri et al. 2009, optimal filtering in pilot-aided recovery | paper | Wiener > linear interpolation | reference only |
| C12 | Barbieri & Colavolpe 2007, PSA sync for DVB-S2 | paper | decoder picks among frequency lobes (est4 lobe search); CBC smoother | competitor (idea) |
| C13 | DVB Project DVB-RCS2 page | app note | design intent quote | reference only |
| C14 | Lin et al. (Ericsson) 2021, Doppler in 5G NR NTN | paper | none (GNSS / reference signals) | reference only |
| C15 | Jung et al. 2024, LR-FHSS for DtS IoT | paper | none (Doppler candidates in the header) | reference only |
| C16 | ITU-R M.2092-2 (VDE-SAT), with IALA G1139 | standard | C6 `vde27` layout; design SNRs -2.4 / -0.6 dB; formats and SE | competitor |
| C17 | Ma, Shi, Meng, Li 2018 (IEEE ICCC), VDES CFO estimation | paper | the published VDES estimator (correlator bank + autocorrelation fine) | reference only |
| C18 | DVB BlueBook C107 (2023), RCS2 in GSO / NGSO | standard | NGSO context, no numbers | reference only |
| C19 | ESA / SatLabs DVB-RCS survey 2010 | press | deployment count (RCS card) | reference only |
| C20 | Via Satellite 2012, STM DVB-RCS2 SatLink | press | deployment (RCS card) | reference only |
| C21 | CSI Magazine 2011, RCS2 adoption | press | context | reference only |
| C22 | ESA ARTES joint turbo decoding and carrier sync (Advantech et al.) | app note | decoder-aided burst sync industrialised (C14 framing) | reference only |
| C23 | ETSI EN 302 307-1 V1.4.1 (DVB-S2) | standard | real pilot spacing (C7 correction); MODCOD thresholds, SE | competitor (C7) |
| C24 | ETSI EN 302 307-2 V1.1.1 / V1.3.1 / V1.4.1 (DVB-S2X) | standard | VL-SNR / short-frame thresholds, SE (section E) | reference only |
| C25 | MathWorks DVB-S2X VL-SNR end-to-end example | app note | multi-frame S2X acquisition ranges | reference only |
| C26 | DVB 2019, > 1.5 billion receivers | press | deployment (S2 card) | reference only |
| C27 | iDirect / Creonic DVB-S2X | datasheet | deployment (S2 card) | reference only |
| C28 | Thesling, Vanderaar (Viasat) US 7653150 B2 | patent | C9 burst + UW; phase from the 4th-power bins (correction) | competitor (C9) |
| C29 | Mo, Thesling (Viasat) US 8243859 B2 | patent | C9 top-32 + UW joint metric | competitor (C9) |
| C30 | Converge Digest 2005, ViaSat acquires ECC | press | deployment (ViaSat card) | reference only |
| C31 | ViaSat LinkWay S2 datasheet | datasheet | not read (404) | reference only |
| C32 | Alagha (Advantech) US 7590199 B2 | patent | C14 hyb3; real layout = 48-symbol preamble (correction) | competitor (C14) |
| C33 | Alagha, Erup (Advantech) US 7593490 B2 | patent | real C14 selector = mean \|LLR\| (ours CRC + rho) | reference only |
| C34 | Satnews 2010, Advantech DoD deliveries | press | deployment (hyb3 card) | reference only |
| C35 | CCSDS 131.0-B-5 (TM sync and coding) | standard | ASM-only (2048, 1024) LDPC layout | reference only |
| C36 | CCSDS 131.2-B-2 (SCCC) | standard | real pilot density for C8 (3.7x correction) | competitor (C8) |
| C37 | CCSDS 130.11-G-2 (SCCC reference receiver) | standard | C8 `blocks` phase model; FLL; sync loss 0.2-0.4 dB | competitor (C8) |
| C38 | CCSDS 130.1-G-3 (TM green book) | standard | turbo thresholds, SE (section E) | reference only |
| C39 | CCSDS 401.0-B-32 (RF and modulation) | standard | acquisition sweeps, CFO context | reference only |
| C40 | NASA DSN 810-005 Module 207 | standard | deep-space loops lock over minutes | reference only |
| C41 | Bertolucci, Cassettari, Fanucci 2021 (Sensors) | paper | CCSDS receiver FLL, ~0.2 CFO at 5 Mbaud (C8 correction) | reference only |
| C42 | MathWorks CCSDS FACM example | app note | multi-frame context | reference only |
| C43 | Creonic CCSDS AR4JA LDPC brief | datasheet | (2048, 1024) LDPC = our N, K: 2.20 dB @ 1e-5 | reference only |
| C44 | Safran Cortex CRT datasheet | datasheet | acquisition Es/N0 < -2 dB, < 0.5 dB loss | reference only |
| C45 | Safran Cortex HDR datasheet | datasheet | deployment | reference only |
| C46 | Kongsberg HRDFEP data sheet | datasheet | loss < 0.5 dB (snippet) | reference only |
| C47 | Andreotti et al. 2021/2023, VDE-SAT Link ID 20 over NorSat-2 | paper | real VDE-SAT receivers use DA R-B-type estimation | reference only |
| C48 | Nanna et al. 2023 (IET), VDE-SAT Link ID 20 | paper | none (not read) | reference only |
| C49 | ESA VDE-SAT downlink verification (NorSat-2) | app note | deployment (VDE-SAT card) | reference only |
| C50 | IALA ENAV16 Annex 4 (2016) | standard | origin of the +-160 Hz / +-4 kHz budget | reference only |
| C51 | Alen Space 2025, SATMAR launch | press | deployment (VDE-SAT card) | reference only |
| C52 | Chakrapani 2019/2020, NB-IoT uplink receiver (Qualcomm) | paper | deployed DMRS estimator, +-250 Hz window (C10 correction) | reference only |
| C53 | Wang et al., NB-IoT primer | paper | C10 1/7 DMRS density | competitor (C10) |
| C54 | MathWorks NB-IoT NPUSCH pages | app note | DMRS positions; repetition example | reference only |
| C55 | Ericsson US 8605799 B2, two-lag CFO resolution | patent | DMRS range +-1 kHz | reference only |
| C56 | 3GPP TS 36.521-1 6.5.1F (NB-IoT frequency error) | standard | terrestrial NB-IoT CFO budget | reference only |
| C57 | Liberg et al. 2020, NB-IoT NTN | paper | NTN Doppler context | reference only |
| C58 | Ericsson US 12136966 B2, NTN frequency offset | patent | Doppler rate (drift test) | reference only |
| C59 | 3GPP R1-2208176 / R4-2512550 (IoT-NTN pre-compensation) | standard | per-segment re-compensation | reference only |
| C60 | 3GPP R4-2216641 (NTN frequency error, draft) | standard | NTN residual budget | reference only |
| C61 | arXiv 2601.04882, 5G NR NTN road ahead | paper | release context | reference only |
| C62 | Sensors 2022, NB-IoT uplink in LEO NTN | paper | none (not verifiable) | reference only |
| C63 | Press on NB-IoT / NTN deployments | press | deployment (C10 card) | reference only |
| C64 | 3GPP TS 36.213 CQI table (secondary) | standard | LTE QPSK rates (indicative) | reference only |
| C65 | Ahmad, Kaleem, Chang, LTE DL BLER | paper | CQI SNRs at 10 % BLER (indicative) | reference only |
| C66 | MathWorks wlanCoarseCFOEstimate | app note | C12 coarse / fine stages | competitor (C12) |
| C67 | OpenOFDM frequency offset correction | app note | real Wi-Fi may run only the lag-16 stage | reference only |
| C68 | Keysight 89600 SymClkErr (802.11) | app note | Wi-Fi CFO budget | reference only |
| C69 | WARP 802.11 Rx characterization | app note | minimum operating SNR | reference only |
| C70 | Baruffa, Rugini 2023, 802.11ad SC | paper | 11ad SC layout (C12 correction) | reference only |
| C71 | Lomayev (Intel) US 10615930, 802.11ay GI | patent | none | reference only |
| C72 | Liu et al. TCSI 2015, 802.11ad / 15.3c sync | paper | 11ad CFO range; not modelled | reference only |
| C73 | Terragraph runbook; Qualcomm 11ay press | app note | 11ad SC deployment | reference only |
| C74 | Wikipedia WiGig (802.11ad MCS table) | app note | 11ad SC thresholds, SE (section E) | reference only |
| C75 | Keysight 802.11ad concepts | app note | LDPC 672 bits | reference only |
| C76 | MIL-STD-188-110C with CN1 | standard | C13 layout; real 411 known (correction) | competitor (C13) |
| C77 | ITU-R F.763-5 (STANAG 4539) | standard | App C frame and range | reference only |
| C78 | MIL-STD-188-110D (2017) listing | standard | 110C superseded | reference only |
| C79 | MathWorks MIL-STD-188-110A receiver | app note | HF tracking is equaliser-driven | reference only |
| C80 | L3Harris RF-7800H-MP datasheets | datasheet | deployment (C13 card) | reference only |
| C81 | Furman, Nieto 2012; Jorgenson et al. 2013 (110C App D) | paper | none (not read) | reference only |
| C82 | Wang et al. 2025 (Chinese Optics Letters), 400ZR pilot-only sync | paper | 400ZR coarse CFO uses training sequences (C11 note) | reference only |
| C83 | Comtech DMD1050TS datasheet | datasheet | real-modem thresholds (SE comparison) | reference only |
| C84 | ITU-R Report M.2435-0 (2018), VDES simulations | report | VDE-SAT turbo PER / BER validation target (-1.5 dB at PER 1e-2) | reference only |
| C85 | CEAS Space Journal, VDES satellite component | paper | E-SSA receiver, CRC + SIC (full-system VDE-SAT) | reference only |
| C86 | AFF3CT DVB-RCS2 duo-binary turbo source | code | P / Q table, circulation table, reference encoder / decoder for RCS2 turbo | reference only |
| C87 | MathWorks dvbrcs2TurboEncode / dvbrcs2TurboDecode | app note | bit-exact arbiter for the RCS2 turbo codec | reference only |
| C88 | Boxerman, Bensimon, Greenberg, Ben-Shimol 2023, RCS2 turbo interleaver | paper | second source for the RCS2 ARP interleaver formula | reference only |
| C90 | AFF3CT error_rate_references, TURBO_DB DVB-RCS2 | data | reference FER for the RCS2 turbo decoder | reference only |
| C91 | AFF3CT documentation (Turbo DB / RSC DB, turbo, interleaver) | app note | test-vector dump flags, decoder scaling options | reference only |
| C92 | Martina, Masera 2011, NoC turbo decoders | paper | max-log-MAP near log-MAP on duo-binary | reference only |
| C93 | IEEE 802.16 maint. contributions 05_149 / 05_151 (CTC interleaver) | standard | precedent for the interleaver-direction ambiguity | reference only |
| C94 | ETSI EN 302 583 V1.2.1 (DVB-SH), turbo code 5.3 | standard | confirms the VDE constituent code and tail | reference only |
| C96 | Kim 2025 (J. KICS), VDES turbo decoder on FPGA | paper | VDE turbo PER points and decoder settings | reference only |
| C97 | MathWorks comm.TurboEncoder / comm.TurboDecoder | app note | independent cross-check of the VDE codec (no MATLAB) | reference only |
| C99 | Robertson, Villebrun, Hoeher 1995, log-domain MAP | paper | log-MAP vs max-log-MAP choice for the VDE baseline | reference only |
| C100 | Iterative decoding algorithm for VDES signals (ICDSP 2020) | paper | none (not read) | reference only |
| C104 | NVIDIA Sionna Polar5GEncoder source | code | NR rate-matching P table, 9/8 rule, pre-freezing (off-by-one noted) | reference only (rate matching proposed) |
| C105 | MathWorks 5G NR polar coding example | app note | rate-recovery LLR conventions | reference only |
| C106 | MathWorks nrUCIEncode | app note | NR segmentation condition (not adopted) | reference only |
| C108 | Coskun et al. 2019, codes in the short blocklength regime | paper | polar CRC-16 L = 32 ~ turbo at (512, 256) | reference only |
| C109 | Liva, Gaudio, Ninacs, Jerkovits 2016, code design for short blocks | paper | 16-state turbo 0.4 dB from the RCB at (128, 64) | reference only |
| C110 | Shirvanimoghaddam et al. 2019, short codes for URLLC | paper | CA-polar 0.5 dB from the NA, turbo > 1 dB (N = 128) | reference only |
| C112 | Sybis et al. 2016, channel coding for URLLC in 5G | paper | none (snippet only) | reference only |
| **D** | **Blind / non-coherent polar, phase ambiguity, blind detection** | | | |
| D1 | Yuan, Coskun, Kramer 2021, polar-coded non-coherent | paper | list-marginalised metric (F3, `lmarg`) | in test (offline gate passed) |
| D2 | Geiselhart, Gauger, Krieg, Clausius, ten Brink 2023, phase-equivariant PCM | paper | `equiv` and the 2 rotation bits `eqrb` | passed / proposed at 2/5, 1/2; dropped at 1/10, 0.15 |
| D3 | Choi & Lee 2026, pilotless polar coded modulation | paper | confirms the eqrb construction | reference only (confirmation) |
| D4 | Hybrid polar encoding, non-coherent channels 2023 | paper | none | reference only |
| D5 | Giard, Balatsoukas-Stimming, Burg 2017, blind detection of polar codes | paper | frozen-only ranking metric | tested-dropped |
| D6 | Giard et al. 2018, accuracy vs complexity in blind detection | paper | frozen-only / no-SPC ranking | tested-dropped |
| D7 | Condo, Hashemi, Gross 2017, blind detection with polar codes | paper | two-phase SC -> SCL structure (= our Stage 2 -> 3) | reference only |
| D8 | Condo et al. 2018, blind detection hardware | paper | none | reference only |
| D9 | Jalali & Ding 2019, blind detection of polar PDCCH | paper | none (MIMO detector) | reference only |
| D10 | Feng, Liu et al. 2023, polar-assisted blind frame sync | paper | only if timing becomes unknown | reference only |
| D11 | Tu, Liu, Feng, Niu 2026, blind recognition of polar codes | paper | none | reference only |
| D12 | Chen et al. 2019, noncoherent detection with polar codes | paper | none (differential ~3 dB loss) | reference only |
| D13 | Li, Xu, Hu 2018, channel estimation with systematic polar codes | paper | pilots inside the codeword: pilot family only | reference only |
| D14 | Ghaddar, Kim, Milstein, Ma, Yi 2021, joint estimation over channels with memory | paper | supports list-chosen reliable symbols (pns) | reference only |
| **E** | **Code-aided synchronization and phase noise** | | | |
| E1 | Herzet, Noels, Lottici et al. 2007, code-aided turbo sync | paper | classic EM baseline (dd family) | reference only |
| E2 | Wymeersch & Moeneclaey 2005, code-aided ML phase + ambiguity | paper | pilot-free ambiguity resolution idea | reference only |
| E3 | Yue et al. 2023, code-aided CFO / CPO in cooperative satcom | paper | cross-entropy CFO search (not recommended) | reference only |
| E4 | Colavolpe, Barbieri, Caire 2005, strong phase noise | paper | code-aided phase smoothing retry `pns` | passed (candidate) |
| E5 | Isikman, Mehrpouyan, Graell i Amat 2012, phase noise estimation | paper | Kalman / EKS smoother variant of pns | reference only (idea used) |
| E6 | Mei & Qu 2026, log density spectrum decoding | paper | none yet (LDSR parked) | reference only |
| E7 | Shayovitz & Raphaeli 2012, multiple-hypothesis LDPC in phase noise | paper | none | reference only |
| E8 | BIT CN110519200B, polar-assisted carrier sync | patent | reason why EM / dd cannot replace the grid | reference only (dead-end reason) |
| E9 | Wu, Wang, Chen, Wang 2025, J. TT&C, PCAFOE | paper | same as E8 | reference only (dead-end reason) |
| E10 | Barbieri, Colavolpe, Caire 2007 (phase noise + frequency offset) | paper | not read | reference only |
| **F** | **Acceptance, undetected errors, false alarms** | | | |
| F1 | Coskun, Liva, Ostman, Durisi 2019, joint estimation and list decoding | paper | non-coherent re-scoring = our rho idea | adopted (idea, found independently) |
| F2 | Yuan, Duffy, Medard 2024, near-optimal generalized decoding | paper | Forney / codebook-probability test; list-1 ~ PM argument | reference only |
| F3 | Yuan, Duffy, Medard 2025, soft-output SCL (T-IT) | paper | possible soft output | reference only |
| F4 | Feng, Yuan, Duffy, Medard 2025, CA-polar SO + GRAND | paper | erase on SO; outer GRAND | reference only |
| F5 | Sauter, Kislal, Durisi, Liva, Matuz, Strom 2025, UEP in short blocklength | paper | keep CRC + rho under phase error; segmented rho `rhos` | in test (log-only) |
| F6 | King, Yao, Ryan, Wesel 2023, CRC-aided list decoding of short messages | paper | UER vs CRC length / list size | reference only |
| F7 | Learning to mitigate the FAR in polar blind detection 2019 (WCL) | paper | none (false-pass NN = dead end) | reference only |
| **G** | **Early termination, gates, search theory** | | | |
| G1 | Strodthoff et al. 2019, ML for early HARQ feedback | paper | logistic gate = as good as complex models | tested-dropped (our retry gate) |
| G2 | Sarkis, Jiang, Lin, Yang (Qualcomm) US10615825 B2 | patent | PM-spread in-decode abort | reference only (not tested) |
| G3 | Lin, Sarkis, Yang (Qualcomm) US10742238 B2 | patent | frozen-bit abort inside CA-SCL-8 (F5, `fz_diag`) | in test (diagnostic) |
| G4 | Yao & Ma 2024, low-complexity PSCL | paper | double-threshold pruning | reference only |
| G5 | Pillet, Bioglio, Condo 2020, list decoding of 5G-NR polar | paper | distributed-CRC early stop (needs a code change) | reference only |
| G6 | Karnin, Koren, Somekh 2013, sequential halving | paper | theory behind our checkpoints | reference only |
| G7 | arXiv 2306.07549 (variance-aware best-arm identification) | paper | hint: looser cut near the true cell | reference only |

---

## A. Polar codes and decoders

### A1. E. Arikan, "Channel polarization: A method for constructing capacity-achieving codes for symmetric binary-input memoryless channels", IEEE Trans. Inf. Theory 55(7), July 2009
- Link: https://arxiv.org/abs/0807.3917   - Type: paper   - Read depth: bib (abstract)
#### What it does
Defines polar codes (x = u F^{(x)n}) and SC decoding, O(N log N) encoding and decoding.
#### What we took / could take
The code itself (`polar.PolarCode`, natural order, no bit reversal) and the SC recursion behind the list-1 metric.
The facts our phase tricks rest on (last row of G_N all ones -> PiCode, 02 section 2.4) follow from this structure.
#### Used in
- (project base, before 2026-11) `polar.py`, every receiver.

### A2. I. Tal, A. Vardy, "List decoding of polar codes", IEEE Trans. Inf. Theory 61(5), 2213-2226, May 2015 (ISIT 2011)
- Link: https://arxiv.org/abs/1206.0050   - Type: paper   - Read depth: bib (abstract)
#### What it does
SC list decoding with L paths, O(L N log N); CRC-aided selection of the final path.
#### What we took / could take
CA-SCL-8 decoding of every candidate (05 section 5.2); the joint 16-path list over 8 hypotheses (05, 5.3) extends it.
#### Used in
- (project base) `polar.PolarCode`, `blind_cfo.PiCode.decode`, `small_rx.decode`.

### A3. A. Balatsoukas-Stimming, M. Bastani Parizi, A. Burg, "LLR-based successive cancellation list decoding of polar codes", IEEE Trans. Signal Process., 2015
- Link: https://ar5iv.arxiv.org/html/1401.3753   - Type: paper   - Read depth: full (survey 1, #20)
#### What it does
LLR-domain path metric PM += ln(1 + e^{-(1-2u)LLR}); hardware SCL: latency 2N + (N/P) log2(N/4P) + K cycles (2592 for
N = 1024, K = 512, P = 64), independent of L; L = 8: 637 MHz, 246 Mb/s, 3.6-3.9 mm^2 (90 nm).
#### What we took / could take
The path metric that the whole search uses as a CFO detector (03_path_metric.md section 3.1). Could take: the cycle
model, to state next to "MACs per core" that list decodes are relatively cheaper in hardware cycles (survey 1 section
4.4: ~4515 cycles at R = 0.15, 5232 at 1/2 for N = 2048 [derived]).
#### Used in
- (project base) `03_path_metric.md`, `blind_fast.fast_metric`, `polar.py`.
- 2026-11-13: survey 1 recommends a cycle-model note in `07_complexity.md` (not checked whether it was added).

### A4. G. Sarkis, P. Giard, A. Vardy, C. Thibeault, W. J. Gross, "Fast polar decoders: algorithm and implementation", IEEE JSAC 32(5), 946-957, 2014
- Link: https://arxiv.org/abs/1307.7154   - Type: paper   - Read depth: bib (abstract)
#### What it does
Fast-SSC: rate-0, rate-1, repetition and single-parity-check nodes decoded in closed form without recursion; 1 Gbps
FPGA decoder.
#### What we took / could take
The closed-form node penalties of our list-1 Fast-SSC metric and the Fast-SSC tree cost used in the MAC model
(03 section 3.2, 07, `blind_fast.fast_metric`, `blind_vp.py`).
#### Used in
- (project base) `blind_fast.py` Fast-SSC metric; cost model `metric_macs` (07_complexity.md).

### A5. S. A. Hashemi, C. Condo, W. J. Gross, "Fast and flexible successive-cancellation list decoders for polar codes", 2017
- Link: https://arxiv.org/abs/1703.08208   - Type: paper   - Read depth: abstract (survey 1, #21)
#### What it does
Fast-SSCL and Fast-SSCL-SPC list decoders; 1.86 Gb/s.
#### What we took / could take
The Fast-SSCL rate-0 shortcut in `polar.PolarCode` and the node splits of the `lit_checks.py` FastSCL list decoder.
#### Used in
- (project base) `polar.py` (rate-0 node shortcut).
- 2026-11-15: `testing/lit_checks.py` FastSCL (F3 `lmarg` harness) uses its node splits.

### A6. G. He, J.-C. Belfiore, I. Land, G. Yang, Y. Ge, R. Zhang, W. Tong, "beta-expansion: a theoretical framework for fast and recursive construction of polar codes", 2017
- Link: https://arxiv.org/abs/1704.05709   - Type: paper   - Read depth: bib (abstract; author list as on the arXiv PDF)
#### What it does
Polarization-weight (PW) construction; beta converges to ~2^(1/4) for AWGN; the basis of the 5G NR sequence.
#### What we took / could take
The frozen set: PW reliability order with beta = 2^(1/4) (`polar.py` header).
#### Used in
- (project base) `polar.py` construction for all rates; `eqrb` takes the K + 2 most reliable positions of the same order
  (expected_eqrb.md, 2026-11-15).
- 2026-11-17: `testing/results/lit_polar_ratematch.md`: PW kept for the N = 2048 / 4096 rate-matched codes (proposed).

### A7. 3GPP TS 38.212, "NR; Multiplexing and channel coding" (ETSI TS 138 212)
- Link: https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.11.00_60/ts_138212v171100p.pdf   - Type: standard
- Read depth: bib (version list only; the polynomial table was not re-read for this registry). 2026-11-17: V15.5.0
  (https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/15.05.00_60/ts_138212v150500p.pdf) clauses 5.3.1,
  5.4.1, 6.3.2.2 cited by `lit_polar_ratematch.md`: NOT read (binary PDF), the rules taken from A17 and C104.
#### What it does
5G NR CRC polynomials (clause 5.1), polar coding for control channels (5.3.1), rate matching (5.4.1: sub-block
interleaver, bit selection by puncturing / shortening / repetition, pre-freezing).
#### What we took / could take
CRC polynomials (`polar.CRC_POLYS`; CRC-16 in the blind study). Not taken: rate matching by shortening (PiCode would
need 4 phase branches, 08_parameters_results.md "PiCode's assumption"); distributed CRC (G5) would be a code change.
Could take (2026-11-17, proposed, not implemented): the 5.3.1 / 5.4.1 rate matching for the native competitor formats
(DVB-RCS2, VDE-SAT), with n_max lifted to 12 (lit_polar_ratematch.md 1.7).
#### Used in
- (project base) `polar.py` CRC_POLYS; CRC-16 in every blind / pilot receiver.
- 2026-11-17: `testing/results/lit_polar_ratematch.md`: rate-matching clauses proposed for the native formats (sections
  1.1-1.7; proposed, not implemented).

### A8. B. Yuan, K. K. Parhi, "LLR-based successive-cancellation list decoder for polar codes with multibit decision", 2016
- Link: https://arxiv.org/pdf/1603.07055   - Type: paper   - Read depth: snippet (survey 1, #22)
#### What it does
Fixed-point study at N = 1024, R = 1/2: 6-bit LLRs suffice; PMs need more bits; 7-bit sorting ~ no loss.
#### What we took / could take
A warning for any hardware claim: our z-test uses wrong-cell metrics of ~(N - K) ln 2 ~ 1200 nats, which a saturating
PM register would compress. Test before claiming hardware numbers (open item 4).
#### Used in
- none yet.

### A9. Seah, Rubenacke, Gross, "Speculative successive-cancellation decoding of polar codes", 2026
- Link: https://arxiv.org/abs/2608.02760   - Type: paper   - Read depth: abstract (survey 2, #15)
#### What it does
Speculative parallel execution in general nodes + verification; N = 4096; -69 % sequentially traversed nodes, same FER.
#### What we took / could take
Nothing: it cuts latency, not MACs (our cost model).
#### Used in
- none.

### A10. Shen et al., "Soft-output fast SCL decoder", WCNC 2025
- Link: https://arxiv.org/abs/2410.15071   - Type: paper   - Read depth: abstract (survey 1, #14)
#### What it does
SO-SCL with Fast-SSC nodes; "significant" latency cut, no numbers in the abstract.
#### What we took / could take
Only if soft outputs are needed (soft EM, Forney test).
#### Used in
- none.

### A11. Shen, Wu, Gao et al., "Node-based soft-output fast SCL decoding", IEEE Trans. Commun. 2026
- Link: https://arxiv.org/abs/2604.17482   - Type: paper   - Read depth: abstract (survey 2, #14)
#### What it does
SO-SCL with Fast-SSC nodes: vs SO-SCL time steps -81.8 %, additions -41.3 %, comparisons -46.4 %.
#### What we took / could take
Soft symbols for the pns smoother if the list-weighted average is not enough (survey 2 F1).
#### Used in
- none (pns uses the list-weighted re-encoded symbols, expected_pns.md).

### A12. Lulei et al., "Subcode ensemble decoding of polar codes", 2025
- Link: https://arxiv.org/abs/2504.17511   - Type: paper   - Read depth: abstract (survey 2, #24)
#### What it does
Ensemble decoding via pre-transformations.
#### What we took / could take
Nothing (relevance none).
#### Used in
- none.

### A13. Aharoni, Huleihel, Pfister, Permuter, "Data-driven neural polar codes for unknown channels with and without memory", 2023
- Link: https://arxiv.org/html/2309.03148   - Type: paper   - Read depth: intro / abstract (first 100k chars; survey 2, #16)
#### What it does
Neural SC (learned f / g / decision), cost O(k d N log N); states the SC-trellis cost O(|S|^3 N log N).
#### What we took / could take
The SCT cost figure used to reject phase-state trellis decoding (survey 2 F6: Q = 8 states = 512x an SC pass).
#### Used in
- 2026-11-15: survey 2 F6 rejection argument.

### A14. Wang, Liu, Hou, "Joint successive cancellation decoding of polar codes over intersymbol interference channels", 2014
- Link: https://arxiv.org/abs/1404.3001   - Type: paper   - Read depth: abstract (survey 2, #17)
#### What it does
SC trellis with channel states at the top of the SC tree; list extension.
#### What we took / could take
Nothing; too costly with quantised phase states (A13).
#### Used in
- 2026-11-15: survey 2 F6, "not applicable".

### A15. Fazeli, Mansour, Zhu, Jalloul, "Partially polarized polar codes for 6G control channels", ICC 2026
- Link: https://arxiv.org/abs/2601.15404   - Type: paper   - Read depth: abstract (survey 2, #13)
#### What it does
Prunes kernels so information bits arrive early -> earlier termination in blind decoding.
#### What we took / could take
Only together with a code change; not now.
#### Used in
- none.

### A16. Y. Polyanskiy, H. V. Poor, S. Verdu, "Channel Coding Rate in the Finite Blocklength Regime", IEEE Trans. Inf. Theory 56(5), 2307-2359, May 2010
- Link: https://www.math.chalmers.se/~hegarty/finite_block.pdf   - Type: paper   - Read depth: bib (formula confirmed through search results and course notes; the PDF did not decode, lit_rates.md)
#### What it does
Finite-blocklength bounds and the normal approximation log2 M ~ nC - sqrt(nV) Q^-1(eps) + 0.5 log2 n for the AWGN
channel.
#### What we took / could take
The bound on what any 1024-symbol packet can carry: recomputed for QPSK = 2 x BI-AWGN, n = 2048 real channel uses, C and
V by numerical integration (main session, lit_rates.md last section): max SE 0.300 / 0.427 / 0.959 / 1.149 bits/symbol
at our 1/10 / 0.15 / 2/5 / 1/2 points; ours reach 62 / 67 / 82 / 86 % of it. The long-frame standards' SE advantage at
the same Es/N0 is mostly block length, not pilots.
#### Used in
- 2026-11-15: lit_rates.md section 2 (hand estimate) and last section (recomputed); `comparison_full.md` section E.
- 2026-11-17: `testing/results/lit_polar_ratematch.md`: normal approximation at each native (K, E) recommended as the
  reference.

### A17. V. Bioglio, C. Condo, I. Land, "Design of polar codes in 5G New Radio", IEEE Commun. Surveys & Tutorials, 2021, arXiv 1804.04389
- Link: https://arxiv.org/abs/1804.04389   - Type: paper   - Read depth: full text (ar5iv; lit_polar_ratematch.md)
#### What it does
Tutorial of the 38.212 polar chain (NR control channels, SCL-8): mother-code length rule (0.17 term), sub-block
interleaver, puncture / shorten switch at 7/16, Q1 / Q2 / Q3 pre-freezing formulas; its Fig. 13 has no numbers in the
text.
#### What we took / could take
The mother-length rule, the 7/16 switch and the pre-freezing formulas for rate matching the native competitor formats
(proposed, not implemented).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` sections 1.2-1.4, 1.6 (proposed).

### A18. V. Bioglio, F. Gabry, I. Land, "Low-complexity puncturing and shortening of polar codes", IEEE WCNC Workshops 2017, arXiv 1701.06458
- Link: https://arxiv.org/abs/1701.06458   - Type: paper   - Read depth: full text (ar5iv; lit_polar_ratematch.md)
#### What it does
Bit-reversal puncture / shorten sets plus the reliability order, independent of N; matches the DE / GA sets on (320,160),
(160,120), (160,40) with CRC-24, L = 32, QPSK AWGN (qualitative only in the text).
#### What we took / could take
The N-agnostic puncture / shorten rule, which justifies lifting n_max to 12 (proposed).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` 1.2, 1.4 (proposed).

### A19. K. Niu et al., "A golden decade of polar codes: from basic principle to 5G applications", 2023, arXiv 2303.14614
- Link: https://arxiv.org/abs/2303.14614   - Type: paper   - Read depth: ~78 % of the html (first 100k of 128k chars)
#### What it does
Survey; polar vs LTE turbo at K = 400, N = 1024, L = 32, CRC-8: R 1/5-1/2 polar equal to turbo or better (0.5-1 dB at
1/5); N = 1024, R = 1/2: 0.5-1 dB at 1e-4.
#### What we took / could take
The polar vs turbo numbers for the code-only gain (section 3 of the lit file).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 3.

### A20. "Stitched polar codes", 2025, arXiv 2511.19249 (authors not captured)
- Link: https://arxiv.org/abs/2511.19249   - Type: paper   - Read depth: html, results section text only
#### What it does
New length-flexible construction, N = 256-8192, R = 1/3, 2/5, 1/2, SC and SCL-8 with CRC-11 at BLER 0.01: up to 0.3 dB
better than QUP / BRS rate matching (SC).
#### What we took / could take
The size of the rate-matching sub-optimality: <= 0.3 dB (SC).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 2.

### A21. K. Niu, K. Chen, J.-R. Lin, "Beyond turbo codes: rate-compatible punctured polar codes", IEEE ICC 2013, pp. 3423-3427
- Link: https://arxiv.org/abs/1612.01352 (journal follow-up)   - Type: paper   - Read depth: abstract snippet
#### What it does
QUP puncturing; M = 512, R = 0.5: "> 0.7 dB" gain at 1e-4 (snippet).
#### What we took / could take
Nothing (unverified number).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 3 (unverified).

### A22. V. Miloslavskaya, "Shortened polar codes", IEEE Trans. Inf. Theory 61(9), 4852-4865, 2015
- Link: https://rune.une.edu.au/web/handle/1959.11/64594   - Type: paper   - Read depth: snippet
#### What it does
Shortening-pattern search for long codes; beats LDPC (snippet only).
#### What we took / could take
Nothing.
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` table 5 (reference only).

---

## B. Classic and NN CFO / phase estimators

### B1. D. C. Rife, R. R. Boorstyn, "Single tone parameter estimation from discrete-time observations", IEEE Trans. Inf. Theory 20(5), 591-598, Sept. 1974
- Link: https://doi.org/10.1109/TIT.1974.1055282   - Type: paper   - Read depth: bib (abstract)
#### What it does
CRB and ML estimation of a single complex tone; ML = DFT peak (periodogram); threshold analysis.
#### What we took / could take
(a) The 4th-power fast path is R&B on y = -r^4: zero-padded 4096-point FFT, peak, parabolic refinement (02 section 2.1).
(b) The DVB-RCS2 competitors use R&B over the known symbols (DA-KS) or on r^4 (NDA), after Griebel 2021 (C4).
(c) est3 "ML direct" (FFT 512 + 2 Newton) is the same estimator on a 128-symbol preamble.
#### Used in
- (project base) `small_rx.small_receive` fast path, `blind_cfo.phase4`.
- est3 (commit 2b636d2): ML direct and distributed ML estimators.
- 2026-11-15: est4 `RCS2-13` (R&B FFT over all known symbols + parabolic interpolation) and `RCS2 pre/post` (4th-power
  NDA) - expected_est4.md: RCS2-13 crosses BLER 1e-3 at 0.15 at -3.45 dB vs blind -3.60 dB; 1e-4 at 1/10 at -4.09 vs
  blind -4.9 dB (energy charged); pre/post 4th power fails at low SNR.

### B2. S. Kay, "A fast and accurate single frequency estimator", IEEE Trans. ASSP 37(12), 1987-1990, Dec. 1989
- Link: https://doi.org/10.1109/29.45547   - Type: paper   - Read depth: bib (abstract)
#### What it does
Weighted phase-difference estimator; ML-like accuracy at moderately high SNR, cheap.
#### What we took / could take
Benchmark estimator on 128 contiguous pilots (README A.17.3).
#### Used in
- README A.17.3 (`polar_ber_experiment.py` BENCH): BLER 0.91 / 0.73 / 0.45 at 1/10 -5 dB / 2/5 0.5 dB / 1/2 2 dB: below its
  SNR threshold. Not competitive.

### B3. M. P. Fitz, "Further results in the fast estimation of a single frequency", IEEE Trans. Commun. 42(2/3/4), 862-864, 1994
- Link: https://doi.org/10.1109/TCOMM.1994.580190   - Type: paper   - Read depth: bib
#### What it does
Autocorrelation-phase frequency estimator for burst modems.
#### What we took / could take
Fine stage after M&M in the benchmark (A.17.3); BIT / Wu 2025 (E8, E9) also compare against it.
#### Used in
- README A.17.3: M&M + Fitz BLER 2.7e-3 / 3.3e-3 / 9.1e-4 (1/10 -5, 2/5 0.5, 1/2 2 dB): helps ~2x only at 1/10.

### B4. M. Luise, R. Reggiannini, "Carrier frequency recovery in all-digital modems for burst-mode transmissions", IEEE Trans. Commun. 43, 1169-1178, 1995
- Link: https://doi.org/10.1109/26.380149   - Type: paper   - Read depth: bib
#### What it does
Open-loop feedforward frequency estimator for TDMA bursts (sum of autocorrelations).
#### What we took / could take
Fine stage after M&M in the benchmark (A.17.3).
#### Used in
- README A.17.3: M&M + L&R BLER 1.9e-3 / 3.4e-3 / 9.7e-4.

### B5. U. Mengali, M. Morelli, "Data-aided frequency estimation for burst digital transmission", IEEE Trans. Commun. 45(1), 23-25, Jan. 1997
- Link: https://doi.org/10.1109/26.554282   - Type: paper   - Read depth: equations used in the code (root README: "exactly as in the paper, eqs. (3), (8), (9)"); bib re-checked
#### What it does
Weighted sum of phase increments arg(R(m) R*(m-1)) of the lag correlations, m = 1..N (N = L0/2); range ~ +-20 % of
the symbol rate; near the CRB down to ~0 dB.
#### What we took / could take
The project's main preamble baseline ("M&M", 24,704 MACs at L = 128, N = 64); used in every pilot comparison.
#### Used in
- Root README (A.3, A.17.3): M&M breaks down below -3 dB (x109 the CRB at -5 dB); BLER 4.5e-3 / 2.9e-3 / 9.5e-4 at
  1/10 -5, 2/5 0.5, 1/2 2 dB with 128 pilots.
- est3: baseline `bench_estimate("mm")`.
- 2026-11-15: est4 `pre128 M&M` (C3) - expected_est4.md: 207 errors / 64k at 1/10 -5 dB (pn 0) vs blind 14; among the
  worst constant-phase receivers under phase noise. TR 101 545-4 Annex D also uses M&M as the fine estimator (lit_dvbrcs2).

### B6. M. Morelli, U. Mengali, "Feedforward frequency estimation for PSK: a tutorial review", Eur. Trans. Telecommun. (ETT), 1998
- Link: https://www.bohrium.com/paper-details/feedforward-frequency-estimation-for-psk-a-tutorial-review/811904108263899138-14477   - Type: paper   - Read depth: abstract (survey 1, #24)
#### What it does
DA vs NDA (M-th power) feedforward estimators: the NDA non-linearity raises the threshold; R&B best at low SNR.
#### What we took / could take
The reason the 4th-power fast path is off below 0 dB at 1/10, 0.15 (DEAD_ENDS: fast path on below +0.5 dB costs 15-38 %
more MACs per core).
#### Used in
- 2026-11-13: survey 1 verdict "coarse CFO: we already use the state of the art".

### B7. M. Morelli, U. Mengali, "An improved frequency offset estimator for OFDM applications", IEEE Commun. Lett. 3(3), 75-77, 1999
- Link: https://doi.org/10.1109/4234.752907   - Type: paper   - Read depth: bib
#### What it does
BLUE frequency estimator from a training symbol of L > 2 identical parts.
#### What we took / could take
est3 "BLUE (MM99)" on an 8 x 16 periodic preamble (U = 8, H = 4).
#### Used in
- est3 (commit 2b636d2): needs ~4 dB more SNR than ML before it is efficient; not competitive at our SNRs.

### B8. M. Morelli, U. Mengali, "Carrier-frequency estimation for transmissions over selective channels", IEEE Trans. Commun. 48(9), 1580-1589, 2000
- Link: https://doi.org/10.1109/26.870025   - Type: paper   - Read depth: bib
#### What it does
ML (and periodic-training variants) CFO estimation with an unknown multipath channel.
#### What we took / could take
est3 joint CFO / channel ML (profile likelihood with Lh taps).
#### Used in
- est3: Lh = 1 equals ML direct; on AWGN extra taps only cost accuracy (unknown-tap CRB 1.04x at Lh = 3, 1.08x at 8).

### B9. P. H. Moose, "A technique for orthogonal frequency division multiplexing frequency offset correction", IEEE Trans. Commun. 42(10), 2908-2914, 1994
- Link: https://doi.org/10.1109/26.328961   - Type: paper   - Read depth: bib
#### What it does
CFO from a repeated symbol (ML).
#### What we took / could take
est3 periodic-preamble estimator (Q = 16).
#### Used in
- est3: needs ~10 dB more SNR than ML before efficient; not competitive.

### B10. T. M. Schmidl, D. C. Cox, "Robust frequency and timing synchronization for OFDM", IEEE Trans. Commun. 45(12), 1613-1621, 1997
- Link: https://ieeexplore.ieee.org/document/650240   - Type: paper   - Read depth: bib
#### What it does
Timing and CFO from a two-half training symbol.
#### What we took / could take
est3 "Schmidl-Cox / Moose" estimator.
#### Used in
- est3 (as B9).

### B11. E. Aboutanios, B. Mulgrew, "Iterative frequency estimation by interpolation on Fourier coefficients", IEEE Trans. Signal Process. 53(4), 1237-1242, 2005
- Link: https://doi.org/10.1109/TSP.2005.843719   - Type: paper   - Read depth: bib (abstract)
#### What it does
Two-iteration interpolation on DFT coefficients; variance 1.0147x the asymptotic CRB.
#### What we took / could take
Refinement option of the ML periodogram (A.17.3, est3 ML direct variants).
#### Used in
- README A.17.3: ML periodogram + A&M BLER 8.6e-4 / 2.9e-3 / 9.7e-4 (best of the contiguous-preamble estimators at 1/10).

### B12. C. Candan, "Analysis and further improvement of fine resolution frequency estimation method from three DFT samples", IEEE Signal Process. Lett. 20(9), 913-916, 2013
- Link: https://users.metu.edu.tr/home103/ccandan/wwwhome/pub_dir/Fine_Doppler2_IEEE_SPL_Sept2013.pdf   - Type: paper   - Read depth: bib
#### What it does
Jacobsen three-bin interpolator with a bias correction.
#### What we took / could take
est3 "Jacobsen-Candan" (unpadded 128-point FFT).
#### Used in
- est3: constant ~1.5x the CRB; 2,472 MACs; residuals the CRC search does not always fix -> not competitive.

### B13. A. J. Viterbi, A. M. Viterbi, "Nonlinear estimation of PSK-modulated carrier phase with application to burst digital transmission", IEEE Trans. Inf. Theory 29(4), 543-551, 1983
- Link: https://ieeexplore.ieee.org/document/1056713   - Type: paper   - Read depth: bib (abstract)
#### What it does
M-th power feedforward phase estimation for PSK bursts.
#### What we took / could take
The fast path phase: theta_0 = (1/4) arg sum y_n e^{-j 2 pi 4 f0 n_c} (02 section 2.3), modulo pi/2. Survey 2 F6 rejects
NDA 4th-power sliding-window phase tracking (variance ~4.8 rad^2 per symbol at 0.5 dB, ~194 at -5 dB [derived]).
#### Used in
- (project base) `blind_cfo.phase4`; Geiselhart 2023 and Choi & Lee 2026 use the same V&V start.

### B14. A. Casini, R. De Gaudenzi, A. Ginesi, "DVB-S2 modem algorithms design and performance over typical satellite channels", Int. J. Satell. Commun. Netw. 22(3), 2004
- Link: https://www.bohrium.com/paper-details/dvb-s2-modem-algorithms-design-and-performance-over-typical-satellite-channels/812347569408573441-2825   - Type: paper   - Read depth: abstract snippet (lit_dvbrcs2 #13)
#### What it does
DVB-S2 modem: block-periodogram coarse frequency, block phase-difference fine frequency, pilot-aided phase.
#### What we took / could take
est3 "DVB-S2 block phase-difference" estimator on split / distributed layouts.
#### Used in
- est3: 37x CRB at low SNR (4 x 32), 1.06x at high SNR; not competitive at our SNRs.

### B15. Li Zhen, L. Cheng, Z. Chu, K. Yu, P. Xiao, M. Guizani, "Clustering-NN-based CFO estimation using random access preambles for 5G non-terrestrial networks", IEEE Wireless Commun. Lett. 13(3), 587-591, 2024
- Link: https://doi.org/10.1109/LWC.2023.3333810   - Type: paper   - Read depth: bib (abstract)
#### What it does
K-means integer clusters + small BPNN per cluster for the fractional CFO, on NR PRACH preambles.
#### What we took / could take
est3 NN competitor, adapted to a random QPSK preamble.
#### Used in
- est3: precision floor 19x the CRB at 16 dB; does not reach the CRB in our setting.

### B16. Chen et al., "Deep learning-based frequency offset estimation", 2023
- Link: https://ar5iv.labs.arxiv.org/html/2311.16155   - Type: paper   - Read depth: full (survey 1, #27)
#### What it does
IQ-ResNet CFO regression; BPSK / FSK / QAM, 512-2048 samples, |f| <= 0.2, -20 ... 30 dB; beats Kay; no CRB, no complexity.
#### What we took / could take
Nothing; NN regressors not shown to beat R&B at low SNR (our own NN results agree, root README A.3).
#### Used in
- none.

---

## C. Standards, burst modems, pilot placement

### C1. ETSI EN 301 545-2, DVB-RCS2 Part 2: Lower layers for satellite standard: V1.3.1 (2020-07, used in est4) and V1.5.1 (2026-04, current)
- Link: https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.03.01_60/en_30154502v010301p.pdf ; V1.5.1:
  https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/en_30154502v010501p.pdf   - Type: standard
- Read depth: V1.3.1 full text of cl. 6.4.6, 7.3.6-7.3.9 and Annex A Table A-1 (via a text reader; UW hex values not
  legible); V1.5.1 chars 0-100k and 200k-800k of 814k via a text reader, tables flattened (lit_card_sat.md, 2026-11-15)
#### What it does
TC-LM burst construction: preamble + 1-symbol pilots every P symbols + postamble; reference waveforms (ID 13: QPSK 1/3,
1616 symbols, pre 32, post 31, P = 20, 77 pilots); RRC roll-off 0.20; pilots on only for QPSK 1/3 and 1/2.
V1.5.1 (adopted 21 April 2026): NGSO support, roll-off 0.20 / 0.10 / 0.05, DVB-S2X waveforms on the return link (TDMA
bursts of one S2X frame, 384-7274 bytes, or continuous carrier), pilots always mandatory for VL-SNR return; carrier
accuracy 1e-8 RMS, burst start 0.5 symbol, symbol clock 20 ppm, NCC corrections in 10 Hz steps; **Annex A ID 13
unchanged**, so `rcs13` needs no change. Known symbols use the payload constellation.
#### What we took / could take
The main DVB-RCS2 competitor layout: ID 13 scaled to 1024 data symbols = preamble 32 | 53 x (19 data + 1 pilot) |
17 data | postamble 31, 116 known symbols (0.47 dB). Derived fact: 1-symbol pilots every 20 resolve only |f| < 0.025,
below our 0.03, so DA-KS over all known symbols is needed.
#### Used in
- 2026-11-15: `lit_dvbrcs2.md` competitors C1 (RCS2-PL), C2 (pre/post), C3 (preamble-only).
- 2026-11-15: est4 `RCS2-13` / `RCS2-13 track` (expected_est4.md, 480k per point): with energy charged blind is
  equal or better in BLER at all 4 rates (0.15 1e-3: blind -3.60 vs -3.45 dB; 2/5 1e-3: 0.61 vs 1.10 dB; 1/2: 1.79 vs
  2.33 dB) at 5-12x the MACs per core (RCS2-13 0.034-0.045 M); RCS2-13 has a window-miss floor (881 / 480k at 1/10
  -5 dB) from the 1/(2P) alias. Under Wiener phase noise 1e-4 the tracking arm beats blind at 0.15 and 2/5
  (94 vs 144, 1967 vs 5312 per 64k, pilot energy not charged). Also `08_parameters_results.md` 8.2a, `07` 7.5b,
  `presentation/bler_fair_R*.png`.
- 2026-11-15: `lit_card_sat.md` card 1 (V1.5.1 read; ID 13 unchanged): citation updated to V1.5.1 in
  `testing/comparison_data.py` / `comparison_full.md` (RCS2-13 card + "Real system" block) and `competitors.md` C1 / C15.
- 2026-11-17: `testing/results/lit_rcs2_fullsystem.md` (full TC-LM transmitter spec: scrambler, CRC16 / CRC32,
  turbo encoder, interleaver, puncturing, mapping, UW hex of IDs 2-4, 13, 14, 40-43; Table A-2 SS waveforms).
- 2026-11-17: `testing/results/lit_turbo_db.md`: PDF not legible to the scout's tool; EN items taken from the
  `lit_rcs2_fullsystem.md` extraction.

### C2. ETSI TR 101 545-4 V1.1.1 (2014), DVB-RCS2 Part 4: Guidelines for implementation and use of EN 301 545-2
- Link: https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.01.01_60/tr_10154504v010101p.pdf   - Type: standard
- Read depth: characters 0-620,000 of 705,000 (cl. 1-10, Annexes A-D)
#### What it does
No burst-detection, frequency or phase algorithm for TC-LM; assumes frequency estimated on the preamble; tolerable CFO
0.5-3 % of Rs (not specified by DVB-RCS2); ideal-sync PER points (ID 13 PER 1e-3 at -0.80 dB); implementation loss
~0.5-0.6 dB (QPSK); phase-noise mask (Table 10.1); M&M in Annex D, data-aided R&B for CPM.
#### What we took / could take
Our |f| <= 0.03 is the top of the DVB-RCS2 range; the preamble-only + ML competitor (C3 / pre128) is the TR's own
assumption, a fair classic baseline, not a modern one.
#### Used in
- 2026-11-15: `lit_dvbrcs2.md`; est4 `pre128 ML` / `pre128 M&M` design (expected_est4.md).
- 2026-11-15: `comparison_full.md` RCS2 "Real system" blocks (CFO range 0.5-3 %, bench loss 0.5-0.6 dB;
  lit_card_sat.md 1.3-1.4).
- 2026-11-17: `testing/results/lit_rcs2_fullsystem.md` (decoder: max-log-MAP, scaling 0.7, up to 8 iterations;
  complexity 267 add + 159 CS per stage per SISO; Table 10.4 full rows ID 2 and BPSK ID 41).

### C3. ETSI TR 101 545-4 V1.2.1 (2026)
- Link: https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf   - Type: standard
- Read depth: table of contents (lit_dvbrcs2.md); clause 10.2.1 Tables 10.4-10.8, characters 440 000-600 000
  (lit_rates.md, 2026-11-15)
#### What it does
Revision; same clause titles, no TC-LM synchronizer clause in the ToC. Clause 10.2.1: AWGN ideal-sync Es/N0 at PER 1e-3 /
1e-5 for IDs 2-22, 42-49, e.g. ID 13 (QPSK 1/3, 1616) -0.80 / -0.51 dB, ID 14 (QPSK 1/2) 1.49 / 1.71, ID 42 (BPSK
1/3, 3236) -3.81 / -3.52, ID 43 -1.53 / -1.30, ID 3 -0.27 / 0.22, ID 4 1.92 / 2.34, ID 2 0.50 / 1.29; pilotless QPSK
2/3 IDs 5 / 15 at 3.90 / 3.46 dB.
#### What we took / could take
Confirms C2's "no algorithm" finding (ToC only). The DVB-RCS2 MODCOD thresholds and net SE (0.304-0.931 b/sym
[derived]) of lit_rates.md: the fairest short-burst standard comparison (block length 112-1504 bits, like ours).
#### Used in
- 2026-11-15: lit_dvbrcs2.md.
- 2026-11-15: `lit_rates.md` 4.3; `comparison_full.md` RCS2 "Real system" blocks (rates) and section E.
- 2026-11-17: `testing/results/lit_rcs2_fullsystem.md` (confirms Tables 10.4 / 10.8; no SS-TC-LM PER table).

### C4. O. Griebel, U. Wasenmüller et al., "Communication Performance vs. Implementation Trade-offs of Interpolation Techniques for FFT-Based Carrier Synchronization exemplified on DVB-RCS2", Adv. Radio Sci. 19, 59-70, 2021, doi:10.5194/ars-19-59-2021 (author initials and title corrected 2026-11-15 from the full text; full analysis: testing/results/lit_ars2021.md)
- Link: https://ars.copernicus.org/articles/19/59/2021/   - Type: paper   - Read depth: full HTML (tables 1-2 are images, not read)
#### What it does
DA-KS (R&B over all known symbols, zeros at data), DA-PL (pilots only, |f| < 1/(2P)), NDA 4th power; parabolic /
energy interpolation cuts the FFT 8192 -> 2048 with no FER loss; constant phase per burst; CFO up to 1.5 % of Rs (3 %
needs NDA); FPGA: interpolation ~2000 FF, 1000 LUT, 13 DSP, throughput 22.9 -> 90.9 Msym/s.
#### What we took / could take
The faithful DVB-RCS2 estimator chain (Eqs. 2-7, 11-17) for est4 RCS2-13 and RCS2 pre/post. Confirms our 4th-power +
parabolic fast path is the deployed NDA baseline.
#### Used in
- 2026-11-15: est4 `RCS2-13` (DA-KS + parabolic) and `RCS2 pre/post` (NDA, 4-fold ambiguity from 32 known symbols) -
  expected_est4.md; RCS2 pre/post fails at low SNR (BLER 0.5-0.9 below 0 dB), crosses 1e-3 at 1/2 only at 2.77 dB.
- 2026-11-15: est4 ARS variants G4096 / G2048 / G2048N / Griebel faithful / RCS2-13 lobes (jobs ars-10/15/25/2,
  480k paired with RCS2-13; expected_ars.md "Measured"): G4096 = RCS2-13 within 0.12 dB at 10 % fewer MACs (the paper's
  claim holds at its zero-padding ratio ~3.6x); G2048 (1.8x on our 1140-symbol burst, coarser than the paper's 3.8x)
  floors at low SNR (+3.75 dB at 1/10 1e-4) from wrong-bin peak picks, equal at 2/5, 1/2; one-decode chain +0.2 dB at
  2/5, 1/2. Blind's gaps to the best DVB-RCS2 variant unchanged: +0.80 / +0.15 / -0.14 / +0.49 / +0.54 dB.
- 2026-11-15: `comparison_full.md` RCS2 "Real system" blocks (the one documented RCS2 implementation: loss 0.12-0.15 dB,
  |f| <= 0.015, constant phase; lit_card_sat.md 1); `competitors.md` fidelity table (C1, C15: ours stronger).
- 2026-11-17: `testing/results/lit_rcs2_fullsystem.md` (decoder settings 0.75 / 8 it / 6-bit, genie FER anchors).

### C5. A. Ali, M. Wasenmuller, N. Wehn, "Feedforward carrier synchronization for pilotless bursts of DVB-RCS2", CSNDSP 2014, 342-347
- Link: https://ieeexplore.ieee.org/document/6923851/   - Type: paper   - Read depth: abstract snippet only
#### What it does
Feedforward frequency + phase for pre/post-only bursts at very low SNR; four FPGA architectures.
#### What we took / could take
Nothing (full text not accessible).
#### Used in
- none.

### C6. A. Ali, M. Wasenmuller, N. Wehn, "Hardware implementation issues of carrier synchronization for pilot-symbol assisted bursts: a case study for DVB-RCS2", ICSPCS 2014
- Link: https://ieeexplore.ieee.org/document/7021078/   - Type: paper   - Read depth: abstract snippet only
#### What it does
Two methods for pilot-assisted bursts in one IP core (Virtex-6).
#### What we took / could take
Nothing (not read).
#### Used in
- none.

### C7. MathWorks, dvbrcs2WaveformGenerator System object (Satellite Communications Toolbox)
- Link: https://www.mathworks.com/help/satcom/ref/dvbrcs2waveformgenerator-system-object.html   - Type: app note   - Read depth: full page
#### What it does
DVB-RCS2 waveform generation; pilot period field 0 ... 4095.
#### What we took / could take
Field ranges (cross-check of C1).
#### Used in
- 2026-11-15: lit_dvbrcs2.md.
- 2026-11-17: `testing/results/lit_rcs2_fullsystem.md` (payload = Frame PDU + CRC; P in [9, 255], Q in [0, 15]; SF 2-16).

### C8. MathWorks, "End-to-end DVB-RCS2 simulation with RF impairments and corrections for TC-LM bursts"
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-dvb-rcs2-simulation-with-rf-impairments-and-corrections-for-tc-lm-bursts.html   - Type: app note   - Read depth: full page
#### What it does
Burst start by differential correlation, CFO by pilot-period differential correlation; 10 kHz at 1 Msym/s (1 %); ID 21
at 15.5 dB, PER 0 over 191 bursts.
#### What we took / could take
A working reference chain; not copied (MathWorks, not the standard).
#### Used in
- 2026-11-15: lit_dvbrcs2.md.

### C9. A. Ginesi, D. Fittipaldi, A. Bigi, R. De Gaudenzi (ESA), "Pilot aided phase synchronization", US 7409024 B2, 2008
- Link: https://patents.google.com/patent/US7409024   - Type: patent   - Read depth: 100k of 141k characters
#### What it does
Per-pilot-block ML phase, unwrapping, linear (PA-LI), Wiener (PA-WI) or Wiener-at-pilots + linear (PA-SWI)
interpolation; QPSK jitter target 6-8 deg; PA-LI fails at 2 % overhead; DD loops only for slots > ~1000 symbols.
#### What we took / could take
The idea of the phase-tracking pilot competitor (est4 C1b `RCS2-13 track`), implemented as a Kalman / RTS smoother
over the pilot phasors with the true linewidth (best-tuned competitor).
#### Used in
- 2026-11-15/16: est4 `RCS2-13 track` (expected_est4.md): rms phase error at -4 dB, pn 1e-4: 0.371 -> 0.249 rad
  (const -> Kalman); the strongest pilot receiver under phase noise.

### C10. Y. Ying, M. Ghogho, "Optimal pilot placement for frequency offset estimation and data detection in burst transmission systems", IEEE Commun. Lett. 9(6), 2005
- Link: https://eprints.whiterose.ac.uk/id/eprint/691/   - Type: paper   - Read depth: abstract
#### What it does
CRB analysis: half of the pilots at the start, half at the end is optimal for CFO and detection.
#### What we took / could take
The split pre/post placement (est4 `split64`, and earlier the project's split-pilot NN / ML) and the argument that a
128-symbol contiguous preamble is the worst placement (a classic, not modern, baseline).
#### Used in
- 2026-11-15: est4 `split64 ML` / `split64 interp` (expected_est4.md): lobe errors at low SNR (wrong lobe in 54-61 % of
  packets at -4 dB, fixed by a lobe CRC search); crosses 1e-4 at 1/10 at -2.87 dB (vs blind -4.9).

### C11. A. Spalvieri et al., "Optimal filtering in pilot-aided carrier recovery", J. Electr. Comput. Eng., 2009
- Link: https://onlinelibrary.wiley.com/doi/10.1155/2009/645615   - Type: paper   - Read depth: search snippet only (403)
#### What it does
Wiener vs suboptimal pilot filters; the gap grows with pilot spacing and SNR (~0.35 dB at 40 dB).
#### What we took / could take
Supports smoothing over linear interpolation for the tracking competitor.
#### Used in
- 2026-11-15: lit_dvbrcs2.md recommendation 4.3.

### C12. A. Barbieri, G. Colavolpe, "On pilot-symbol-assisted carrier synchronization for DVB-S2 systems", IEEE Trans. Broadcast. 53(3), 2007
- Link: https://www.tlc.unipr.it/colavolpe/papers/j36.pdf   - Type: paper   - Read depth: full text (via text reader)
#### What it does
Coarse DA M&M on the preamble, fine reduced M&M on distributed pilots, 3-7 frequency candidates chosen by the LDPC
syndrome; phase by a forward-backward Tikhonov (CBC) smoother; phase-noise loss < 0.1 dB (QPSK, 8PSK, 16APSK).
#### What we took / could take
"The decoder picks the lobe": est4 split64 / pre-post CRC search over lobes m = -3..3, metric-ordered. Also the same
idea as our split-pilot quarter layout + CRC lobe search (root README A.13), which is why that reference is already the
strongest kind of pilot-aided baseline.
#### Used in
- 2026-11-15: est4 fix after smoke 1 (expected_est4.md): lobe search m = -3..3 (+-3 lobes cover ~99 %); split64 errors
  at 0.15 -4 dB went 491 (smoke 1) -> 1 (smoke 2) per 800 packets.

### C13. DVB Project, "DVB-RCS2 lower layer satellite specification" page (accessed 2026-11-15)
- Link: https://dvb.org/?p=8033   - Type: app note   - Read depth: full (lit_card_sat.md; earlier snippet)
#### What it does
States the known-symbol balance ("balanced use of preamble, postamble and pilots") is chosen so that sync sensitivity
matches decoding sensitivity. Version history: V1.4.1 NGSO + superframe signalling; V1.5.1 published 2026-04-24,
replaces EN 301 790 (DVB-RCS gen 1).
#### What we took / could take
Context and version facts only.
#### Used in
- 2026-11-15: lit_dvbrcs2.md.
- 2026-11-15: lit_card_sat.md card 1 (version history).

### C14. Lin et al. (Ericsson), "Doppler shift estimation in 5G NR non-terrestrial networks", Globecom 2021
- Link: https://arxiv.org/abs/2108.07757   - Type: paper   - Read depth: abstract (survey 1, #29)
#### What it does
Doppler from reference signals at several frequencies; UL pre-compensation (GNSS).
#### What we took / could take
Nothing; not pilot-free.
#### Used in
- none.

### C15. Jung et al., "LR-FHSS transceiver for direct-to-satellite IoT", 2024
- Link: https://arxiv.org/abs/2403.14154   - Type: paper   - Read depth: abstract (+ snippet) (survey 1, #28)
#### What it does
Doppler-robust sync; candidate Doppler values tested in the header (snippet); ASIC + FPGA.
#### What we took / could take
Deployment context only (candidate search exists in practice).
#### Used in
- none.

### C16. ITU-R Recommendation M.2092-2 (02/2026), "Technical characteristics for VHF data exchange system in the maritime mobile service", Annex 2 Tables 9-11 and Annex 5 (VDE-SAT); with IALA G1139 ed. 3 (2019)
- Link: https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf ; IALA:
  https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf   - Type: standard
- Read depth: first pass search-engine text excerpts of A5-2.10 / A5-2.12 (worked example quoted directly; table
  totals inferred; also M.2092-1 and the ESA NAVISP ICING doc as cross-checks). 2026-11-15: Annex 5 A5-2 in full and
  Annex 2 Tables 9-11 (flattened, columns checked by arithmetic) via a text reader (lit_card_space.md, lit_rates.md);
  G1139 ed. 3 Tables 9-11 as a cross-check of the thresholds (lit_rates.md).
#### What it does
VDE-SAT downlink (SAT-MCS-1.50-1 = Link ID 26 / 3.50-1, 33.6 ksps): 27-symbol syncword (pi/4-QPSK, dibits 00/11) every
2268 symbols, one (1+j)/sqrt2 pilot every 27 symbols (odd positions offset by pi/4), first pilot 14 symbols after the
syncword (pilots at 40, 67, ...); 2.4 s burst of 80371 symbols (945 sync + 2940 pilots + 76 458 data + 14 / 14 ramp,
4.8 % known), turbo code; **no link ID on the downlink** (Table 10: size 0); the 16-symbol link ID exists only on the
33.6 ksym/s uplink formats. Data pi/4-QPSK (3.50-1: 8PSK). Satellite TX error < 1 ppm (+-160 Hz), LEO Doppler +-4 kHz
(up to 0.124 cycles/symbol [derived]). AWGN thresholds (PER not stated): SAT-MCS-1.50-1 -2.4 dB, Link 34 (pi/4-QPSK,
27 x 6 syncwords, pilot every 27) -0.6 dB, Link 33 (BPSK) -3.6 dB, Link 32 (BPSK/CDMA SF 8, 48-symbol syncwords, pilot
every 8, 22.7 % known) -4.5 dB; net SE 0.19 / 0.325 / 0.475 / 0.633 [derived]. Name of the Link 34 column ambiguous in
the extraction ("SAT-MCS-1.50-2").
#### What we took / could take
est5 competitor C6 layout `vde27`: in the 1090-symbol window [k27][d13][k1]([d26][k1])x38[d23], 66 known symbols
(0.27 dB), alias lobes at 1/27. Real system: 74x longer burst, turbo code, LEO Doppler up to ~0.12 cycles/symbol. The
27 / 27 comb is designed for -2.4 and -0.6 dB; C6 runs 1-2.6 dB below that at 1/10 and 0.15.
#### Used in
- 2026-11-15: `testing/results/lit_vdesat_format.md`; est4 `vde27` pilot offset corrected (first pilot 13 symbols
  earlier; Nk, K and lobes unchanged) before any C6 run; competitors.md C6 (deviations table).
- 2026-11-15: `lit_card_space.md` card 3 (resolves link ID 0, pi/4-QPSK, ramp 14), `lit_rates.md` 4.5;
  `competitors.md` C6 design-SNR correction (-2.4 / -0.6 dB; -4.5 dB is another format) and fidelity table;
  `comparison_full.md` VDE-SAT card (link-ID text fixed, "Real system" block) and section E.
- 2026-11-17: `testing/results/lit_vdesat_fullsystem.md`: Annex 2 FEC (Tables 4-6), CRC-32, scrambler, Tables 9-11,
  A5-2.5 spreading, A5-2.13 / Table 63 interleaver; phase-1 native formats Links 32, 33, 26, 34. G1139: cross-check of
  the turbo code; the syncword must work at -2 dB; its Table 65 is measured data, not AWGN.
- 2026-11-17: `testing/results/lit_vde_fec.md`: A2-1.2.4 to A2-1.2.6 turbo / CRC / scrambler, Table 4 re-aligned for
  all Link IDs with arithmetic checks, Tables 5-6, A3-8 full test vector (scrambler seed 100101010000000 and pi/4-QPSK
  map recovered from it), Table 63 re-read (Ac / Bc differ from lit_vdesat_fullsystem.md).
- 2026-11-17: `testing/results/lit_vde_fec.md` sections 1-3, G1139 ed. 3 Annex A A1.2.4 (turbo code; chars 0-100k via a
  reader): same turbo law, Table 4 rows (4, 8, 20, 34) and puncturing strings (IDs 2, 6, 7, 7a, 7b, 8) as M.2092-2,
  so a second source for the puncturing positions; its OCR transfer-function order [1, n1/d, n0/d] is contradicted by
  the M.2092-2 A3-8 example.

### C17. S. Ma, K. Shi, X. Meng, X. Li, "Frequency Offset Estimation Algorithm of VDES Signals Based on Cross-Correlation", IEEE ICCC 2018, pp. 1234-1238, doi:10.1109/CompComm.2018.8780774 (metadata corrected 2026-11-15 from Crossref; earlier "about 2019", authors unknown)
- Link: https://ieeexplore.ieee.org/abstract/document/8780774   - Type: paper
- Read depth: abstract excerpt + Crossref metadata (IEEE page empty to the fetcher; lit_card_space.md)
#### What it does
Coarse CFO by cross-correlating with a bank of Doppler-shifted copies of the VDES known sequence, compensation, then a
fine stage that is an **autocorrelation-argument estimator** (the coarse step removes its phase folding), not R-B;
claims +-4000 Hz range and accuracy "approximate to the CRB" (no numbers seen).
#### What we took / could take
Our C6 chain (ML on the syncword, Rife-Boorstyn over all known symbols with lobe hypotheses) is at least as accurate as
this published VDE-SAT estimator, so C6 is not a weakened competitor.
#### Used in
- 2026-11-15: `lit_vdesat_format.md`; competitors.md C6.
- 2026-11-15: `lit_card_space.md` (metadata fix); `comparison_full.md` VDE-SAT "Real system" block (estimator).

### C18. DVB BlueBook C107, "Commercial Requirements for the use of DVB-RCS2 in Geostationary and Non-Geostationary Systems", July 2023
- Link: https://dvb.org/wp-content/uploads/2023/07/C107_Commercial-Requirements-for-the-use-of-DVB-RCS2-in-Geostationary-and-Non-Geostationary-Systems.pdf   - Type: standard (requirements)   - Read depth: full via text reader (lit_card_sat.md)
#### What it does
RCS2 requirements for NGSO: higher Doppler (no number in Hz or ppm), operation without GNSS, return roll-off <= 5 %, up to
500 Msym/s, consumer terminals 128 ksps-2 Msps; market: VSAT shipments > 1 M per year (2022), ~2 M by 2026 (all VSAT).
#### What we took / could take
Context: RCS2 is being extended to LEO / MEO, where per-burst Doppler residuals larger than the GEO budget are expected;
no numbers to adopt.
#### Used in
- 2026-11-15: lit_card_sat.md card 1.1.

### C19. ESA news, "SatLabs survey: over 370 DVB-RCS networks, 180,000 terminals" (mid-2010)
- Link: https://resilience.esa.int/?p=9372   - Type: press (agency news)   - Read depth: full
#### What it does
Deployment scale of first-generation DVB-RCS (the predecessor RCS2 replaces): > 370 networks, > 180 000 terminals.
#### What we took / could take
Deployment line of the DVB-RCS2 card only.
#### Used in
- 2026-11-15: `comparison_full.md` RCS2 "Real system" block (deployments); lit_card_sat.md 1.1.

### C20. Via Satellite, "STM adds DVB-RCS2 capability to SatLink VSATs, hubs", 21 March 2012
- Link: https://www.satellitetoday.com/connectivity/2012/03/21/stm-adds-dvb-rcs2-capability-to-satlink-vsats-hubs-2/   - Type: press   - Read depth: full
#### What it does
First commercial RCS2 product claim; up to 50 Mbit/s TDMA shared by "many thousands of VSATs".
#### What we took / could take
Deployment line of the DVB-RCS2 card only.
#### Used in
- 2026-11-15: `comparison_full.md` RCS2 "Real system" block (deployments); lit_card_sat.md 1.1.

### C21. CSI Magazine, "The ultimate interactive satellite standard?", May-June 2011
- Link: https://csimagazine.com/csi/The-ultimate-interactive-satellite-standard.php   - Type: press   - Read depth: full
#### What it does
Operator / vendor views on RCS2 adoption (~30 organisations); gen-1 DVB-RCS strong in government / military networks.
#### What we took / could take
Card context only.
#### Used in
- 2026-11-15: lit_card_sat.md 1.1.

### C22. ESA ARTES project "Joint Turbo Decoding and Carrier Synchronisation" (Advantech Satellite Networks, TurboConcept, Eurecom)
- Link: https://resilience.esa.int/projects/joint-turbo-decoding-and-carrier-synchronisation   - Type: app note (agency project page)   - Read depth: full page
#### What it does
Joint synchronisation and decoding for DVB-RCS (QPSK, BPSK, 8PSK) and CBC with LDPC for DVB-S2, VHDL on FPGA; carrier
sync named "the dominant cause of receiver performance degradation"; no dB numbers.
#### What we took / could take
Evidence that decoder-aided burst sync was industrialised for DVB-RCS (supports the hyb3 / C14 framing).
#### Used in
- 2026-11-15: `comparison_full.md` hyb3 "Real system" block (deployments); lit_card_sat.md 1.6, 4.1.

### C23. ETSI EN 302 307-1 V1.4.1 (2014-11), "Digital Video Broadcasting (DVB); Second generation framing structure, channel coding and modulation systems ...; Part 1: DVB-S2"
- Link: https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf   - Type: standard
- Read depth: partial via a text reader: chars 50k-150k, cl. 5.5-6 (lit_card_sat.md); Table 13, Tables 5a / 5b (lit_rates.md)
#### What it does
PLFRAME: 90-symbol pi/2-BPSK PLHEADER (SOF 26 + PLS 64), 90-symbol slots, optional 36-symbol pilot blocks every 16 slots
(first one 1440 data symbols after the header, period 1476), scrambling after the header; QPSK short frame 90 slots
(8370 symbols with pilots, 3.2 % known [derived]); roll-off 0.35 / 0.25 / 0.20. Table 13 (PER 1e-7 QEF, AWGN, ideal
sync, 64 800 bits, 50 iterations): QPSK 1/4 -2.35, 1/3 -1.24, 2/5 -0.30, 1/2 1.00, 3/5 2.23 dB; short frames 0.2-0.3 dB
worse (note).
#### What we took / could take
The real pilot spacing behind the C7 correction: a 1024-symbol window after the header has no pilot block, and in ACM
only the 26-symbol SOF is known a priori, so C7 is denser than the standard. The QPSK MODCOD thresholds and net SE
(0.479-1.160 with pilots [derived]) for the SE comparison.
#### Used in
- 2026-11-15: lit_card_sat.md 2, lit_rates.md 4.1; `competitors.md` C7 deviation and fidelity table;
  `comparison_full.md` DVB-S2 style card (changes text, "Real system" block) and section E.

### C24. ETSI EN 302 307-2, "... Part 2: DVB-S2 Extensions (DVB-S2X)": V1.1.1 (2015-02), V1.3.1 (2021-07), V1.4.1 (2024-08, latest)
- Link: https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.03.01_60/en_30230702v010301p.pdf ;
  V1.1.1: https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.01.01_60/en_30230702v010101p.pdf ;
  V1.4.1: https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.04.01_60/en_30230702v010401p.pdf   - Type: standard
- Read depth: V1.3.1 chars 0-300k of 340k (lit_card_sat.md); V1.1.1 Tables 4-6, 20a-c, cl. 5.5.2 via a text reader,
  Tables 18a / 19a partly legible (lit_rates.md); V1.4.1 cover only (search result)
#### What it does
VL-SNR frames of 33 282 (set 1) / 16 686 (set 2) symbols with a 900-symbol VL-SNR header after the 90-symbol PLHEADER
plus 32 / 34 / 36-symbol pilots; Annex E superframes (612 540 symbols, SOSF 270 + SFFI 450, SF pilots; format 3: 48 /
1887; format 5 beam hopping). Ideal-sync thresholds at FER 1e-5: normal QPSK 2/9 -2.85, 13/45 -2.03, 9/20 0.22, 11/20
1.45 dB; medium BPSK 11/45 -5.50, 1/3 -4.00; short BPSK 4/15 -4.9, BPSK 1/3 -3.72, QPSK 11/45 -2.50, 4/15 -2.24, 14/45
-1.46, 7/15 0.60, 8/15 1.45 dB.
#### What we took / could take
The strongest "same Es/N0" competitors in lit_rates.md (QPSK 7/15 short +12 % over our 2/5; 8/15 short reaches our 1/2
SE 0.34 dB lower); card 2 structure facts. K after shortening for the short BPSK VL-SNR codes not resolved.
#### Used in
- 2026-11-15: lit_card_sat.md 2, lit_rates.md 4.2; `comparison_full.md` DVB-S2 style "Real system" block and section E.

### C25. MathWorks Satellite Communications Toolbox, "End-to-End DVB-S2X Simulation with RF Impairments and Corrections for VL-SNR Frames" (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-dvbs2x-simulation-with-rf-impairments-and-corrections-for-vlsnr-frames.html   - Type: app note (vendor reference example)   - Read depth: full
#### What it does
VL-SNR receiver: Gardner timing, BQ-FED FLL (20 % of Rs -> ~2 % residual), pilot fine estimator (3.5 % -> 0.03 %), pilot
phase (works to ~-8 dB), 9-25 acquisition frames; one run at Es/N0 5 dB, 3 MHz CFO, PER 0.
#### What we took / could take
The multi-frame acquisition / tracking ranges of a working S2X chain; not a single-burst competitor.
#### Used in
- 2026-11-15: `comparison_full.md` DVB-S2 style "Real system" block (estimator); lit_card_sat.md 2.3.

### C26. DVB announcement, May 2019 (as reported by radiotvlink.com): "over 1.5 billion DVB receivers deployed"
- Link: https://www.radiotvlink.com/en/delivery/866-dvb-worldwide   - Type: press (secondary)   - Read depth: full
#### What it does
Deployment scale of all DVB standards together; a DVB-S2-only count was not found.
#### What we took / could take
Deployment line of the DVB-S2 card only.
#### Used in
- 2026-11-15: `comparison_full.md` DVB-S2 style "Real system" block (deployments).

### C27. iDirect, "DVB-S2X standard" page; Creonic DVB-S2X demodulator product brief (via Aldec, 2023)
- Link: https://www.idirect.net/technology/dvb-s2x-standard/ ; https://www.aldec.com/files/ip_products/PB_Creonic_DVB_S2X_Demodulator.pdf   - Type: datasheet (vendor)   - Read depth: full
#### What it does
Vendor claims of VL-SNR support ("below -9 dB", SNR -9.6 ... 19.8 dB), demodulator up to 100 Msym/s; no sync numbers
or resources.
#### What we took / could take
Deployment line of the DVB-S2 card only.
#### Used in
- 2026-11-15: `comparison_full.md` DVB-S2 style "Real system" block (deployments).

### C28. W. H. Thesling, M. Vanderaar (Efficient Channel Coding, assigned to Viasat), "Star receiver burst processing", US 7653150 B2, 26 Jan 2010 (continuation of US 7200185; priority 21 Aug 2000; expired 2022)
- Link: https://patents.google.com/patent/US7653150B2/en   - Type: patent   - Read depth: full description
#### What it does
512-symbol QPSK return burst, no preamble, 16-symbol midamble UW (a (32,26) Hamming codeword, 26 dedicated TPC
information bits, inside the coded burst [lit_card_sat reading]); blind timing (5x oversampling), phase x 4 LUT,
1024-point FFT, single peak + 3-bin average, frequency / 4 and **phase / 4 from the 4th-power bins**, UW correlation over
+-8 symbols x 2 phases for the pi/2 ambiguity and arrival time; CFO up to 10 % of Rs (design statement); TPC (32,26)^2
BER 1e-5 at Eb/N0 1.4 dB (Es/N0 ~2.6 dB [derived]); ~0.2 dB sync degradation; sync fails just below the FEC threshold.
#### What we took / could take
Basis of est5 C9. Corrections: single peak (top-32 is C29), phase from the 4th-power bins (our `const` phase on the
16 UW symbols is weaker: 0.31 / 0.18 / 0.14 rad std at -5 / 0 / +2 dB [derived]). Possible phase model "nda4ph"
(arg X4 / 4 + UW quadrant, ~0 MACs) proposed by lit_card_sat.md finding 2; not run.
#### Used in
- 2026-11-15: est5 C9 `viasat16` / `nda4uw` (expected_est5.md); `competitors.md` C9 corrections (merge of two patents,
  phase, "10 %" = design statement) and fidelity table; `comparison_full.md` ViaSat UW card and "Real system" block.

### C29. F. Mo, W. H. Thesling (Viasat), "Joint frequency and unique word detection", US 8243859 B2, 14 Aug 2012
- Link: https://patents.google.com/patent/US8243859   - Type: patent   - Read depth: full (two parts)
#### What it does
N-theta FFT, top-N peaks (example 32 of 1024 bins), N trial derotations x M UW positions, joint alpha / beta metric
(LUT, adapted to SNR), optional 1-theta preamble FFT; N grows as SNR falls; gateway or mesh terminal; UW length not
stated; burst error < 1e-5 at 2.5 dB with N = 32.
#### What we took / could take
The top-32 + UW joint metric of est5 C9 (`nda4uw`); the "adapt N to SNR" idea matches our gated extras.
#### Used in
- 2026-11-15: est5 C9 `nda4uw`; `competitors.md` C9 (labelled a merge of C28 and C29); `comparison_full.md` ViaSat UW
  "Real system" block.

### C30. Converge Digest, "ViaSat acquires Efficient Channel Coding", 30 Nov 2005
- Link: https://convergedigest.com/viasat-acquires-efficient-channel-coding/   - Type: press   - Read depth: full
#### What it does
Acquisition facts (~US$16.5 M + 9 M earn-out); ECC supplied IPSTAR modem chips and DVB-S2 / ACM chips.
#### What we took / could take
Deployment line of the ViaSat card; no product tie to the patents found.
#### Used in
- 2026-11-15: `comparison_full.md` ViaSat UW "Real system" block (deployments).

### C31. ViaSat, LinkWay S2 datasheet
- Link: https://www.viasat.com/content/dam/us-site/government/documents/LinkWay_S2_Datasheet_018_web_1085053.pdf   - Type: datasheet   - Read depth: not read (404); search snippet only
#### What it does
Snippet: DVB-RCS turbo 1/3 ... 6/7 with BPSK / QPSK / 8PSK return bursts.
#### What we took / could take
Nothing (no threshold table available); ViaSat return links use DVB-RCS / RCS2 waveforms (C1, C3 as proxy).
#### Used in
- 2026-11-15: lit_rates.md 4.9 (not read).

### C32. N. S. Alagha (Advantech Advanced Microwave Technologies), "Hybrid frequency offset estimator", US 7590199 B2, 15 Sep 2009 (priority 12 Sep 2003)
- Link: https://patents.google.com/patent/US7590199   - Type: patent   - Read depth: full (three parts)
#### What it does
DVB-RCS burst (48-symbol contiguous preamble + 440 payload, QPSK, rate-1/2 turbo, 64 kBd, +-1800 Hz = +-2.8 % of Rs);
DA spectrum of the known symbols and NDA (phase x 4, magnitude 1 / rho / rho^2) spectrum, decimated to the same grid,
log |.|^2, weighted sum, 3 candidates by peak removal + parabolic interpolation; no performance numbers. Cites
Alagha-Erup SPSC 2003 (not found).
#### What we took / could take
Basis of est5 C14 hyb3. Correction: the patent gives the layout (48-symbol preamble), so "16 + 16 chosen by us, not from
the patent" was wrong; lit_card_sat.md proposes a "hyb3-pre48" variant (not run).
#### Used in
- 2026-11-15: est5 C14 `hyb3`; `competitors.md` C14 deviation correction and fidelity table; `comparison_full.md` hyb3
  card (changes text) and "Real system" block.

### C33. N. S. Alagha, L. Erup (Advantech), "Joint synchronizer and decoder", US 7593490 B2, 22 Sep 2009 (continuation US 8331497)
- Link: https://patents.google.com/patent/US7593490   - Type: patent   - Read depth: 200k of 216k characters
#### What it does
Per frequency candidate: derotation, phase initialisation, decision-aided phase tracking, partial turbo decoding (1-3 of
~10 iterations); pick the largest mean |LLR|; LLR-weighted decision-directed phase tracking with a ~50-symbol sliding
window. CRC use or a threshold not stated; no dB numbers.
#### What we took / could take
The real candidate selector of C14 (ours, CRC + rho, is stronger); "partial decode as candidate score" is what our
list-1 metric checkpoints already do.
#### Used in
- 2026-11-15: `competitors.md` C14 (selector correction, link added) and fidelity table; `comparison_full.md` hyb3
  card and "Real system" block.

### C34. Satnews, "Advantech / Agile Communications: DoD deliveries done", 8 Nov 2010
- Link: https://satnews.com/2010/11/08/advantech-agile-communications-dod-deliveries-done-milsatcom/   - Type: press   - Read depth: full
#### What it does
Advantech DVB-RCS / S2 hubs and terminals delivered to the US DoD (no quantities).
#### What we took / could take
Deployment line of the hyb3 card only.
#### Used in
- 2026-11-15: `comparison_full.md` hyb3 "Real system" block (deployments).

### C35. CCSDS 131.0-B-5, "TM Synchronization and Channel Coding", Blue Book, Issue 5, September 2023
- Link: https://public.ccsds.org/Pubs/131x0b5.pdf   - Type: standard   - Read depth: full text via a text reader (figures as text)
#### What it does
ASM before every codeblock: 32-bit 1ACFFC1D (uncoded / conv. / RS / LDPC 7/8), 64-bit 034776C7272895B0 (turbo 1/2,
LDPC 1/2, 2/3, 4/5), 96 / 128 / 192-bit (turbo 1/3, 1/4, 1/6); no pilots; ASM not randomized; LDPC k = 1024 r = 1/2 ->
n = 2048 transmitted (Table 7-5); phase ambiguities must be resolved before decoding (the CSM may help).
#### What we took / could take
(2048,1024) LDPC + 64-bit ASM = 32 QPSK known symbols per 1024-symbol codeblock: the CCSDS single-codeword layout
(lit_card_space.md finding 3; est4 16 + 16 / 64 + 64 bracket it; an `asm32` competitor is optional, not run).
#### Used in
- 2026-11-15: `comparison_full.md` CCSDS style "Real system" block (standard list).

### C36. CCSDS 131.2-B-2, "Flexible Advanced Coding and Modulation Scheme for High Rate Telemetry Applications", Blue Book, Issue 2, February 2023
- Link: https://public.ccsds.org/Pubs/131x2b2.pdf   - Type: standard   - Read depth: chars 0-100k of 160k via a text reader
#### What it does
PL frame: 256-symbol pi/2-BPSK Gold frame marker + 64-symbol frame descriptor, 16 codeword sections of 8100 symbols,
each with 15 x (540 data + 16 pilots) when pilots are on (b6); pilots (1+j)/sqrt2 then PL-scrambled; 133 760 symbols
per frame with pilots, 3.06 % known [derived]; 27 ACM formats QPSK ... 64APSK.
#### What we took / could take
The real pilot density for C8: about 30 known per 1024 data, aliases 1/556; our C8 has 3.7x more (lit_card_space.md).
An optional faithful-density `cc131` layout is proposed there (not run).
#### Used in
- 2026-11-15: `competitors.md` C8 deviation (density, alias typo 0.0068 -> 0.0062) and fidelity table;
  `comparison_full.md` CCSDS style card (search / changes text) and "Real system" block.

### C37. CCSDS 130.11-G-2, "SCCC - Summary of Definition and Performance", Green Book, Issue 2, May 2023
- Link: https://public.ccsds.org/Pubs/130x11g2.pdf   - Type: standard (informational)   - Read depth: full via a text reader
#### What it does
Reference receiver: frame-level FLL with a 1024-point FFT of the FM + Newton (k1 = 0.2, B_L < 186.9 Hz at 100 MBaud),
DA ML phase per 16-symbol field + linear interpolation, SNR / DAGC on the FM; timing and FM acquisition not simulated;
f_D 1 MHz, 50 kHz/s at 100 MBaud (f = 0.01-0.02 [derived]); phase noise 1.45 deg rms; sync loss 0.2-0.4 dB at CER
1e-4 (0.2-0.8 dB with TWTA); FD soft ML 1e-5 at -4 dB; lowest ModCod -0.58 dB; HW test Tesat EM TX + Kongsberg
Spacetec RX at 500 MBaud K-band.
#### What we took / could take
C8 `blocks` phase model = 130.11 5.6 (already the C8 card link); confirms there is no single-burst acquisition and no
code-aided step; the "acquisition range smaller" remark holds only for this 100 MBaud case.
#### Used in
- (before 2026-11-15) est5 C8 card link (competitors.md, expected_est5.md).
- 2026-11-15: `competitors.md` C8 deviation; `comparison_full.md` CCSDS style "Real system" block (estimator, loss).

### C38. CCSDS 130.1-G-3 (2020, Editorial Change 1 2024), "TM Synchronization and Channel Coding - Summary of Concept and Rationale", Green Book
- Link: https://public.ccsds.org/Pubs/130x1g3e1.pdf   - Type: standard (informational)   - Read depth: chars 100 000-200 000 via a text reader (lit_rates.md)
#### What it does
7.4.1: turbo threshold bit-SNRs ~-0.1, 0.15, 0.4, 1.1 dB for rates 1/6, 1/4, 1/3, 1/2 at BER 1e-6 (~ FER 1e-4); block
length not named (most likely k = 8920); assumes no synchronisation losses.
#### What we took / could take
CCSDS turbo QPSK Es/N0 -4.87 / -2.86 / -1.36 / +1.10 dB, net SE 0.332-0.996 [derived]: the largest same-Es/N0 SE
advantage over us (x1.78 at our 1/10 point), reachable only with long blocks.
#### Used in
- 2026-11-15: lit_rates.md 4.4; `comparison_full.md` CCSDS style "Real system" block (rates) and section E.

### C39. CCSDS 401.0-B-32, "Radio Frequency and Modulation Systems - Part 1: Earth Stations and Spacecraft", Blue Book, Issue 32, October 2021
- Link: https://public.ccsds.org/Pubs/401x0b32.pdf   - Type: standard   - Read depth: chars 0-100k of 517k (text to 2.3.4B; summary tables for the rest)
#### What it does
Earth-station acquisition sweeps +-150 kHz (2 GHz), +-600 kHz (8 GHz), +-1.8 MHz (26 GHz) Cat A; +-300 kHz / +-1 MHz /
+-4 MHz Cat B; sweep rates 100 Hz/s-200 kHz/s; Doppler rates up to 3 / 10 / 34 kHz/s; telemetry loop 2B_LO 30 Hz-2 kHz
(Cat A), 1 Hz-1 kHz (Cat B); suppressed-carrier rate limits 2 / 10 / 20 Msps.
#### What we took / could take
CFO-as-fraction-of-Rs context (0.075-0.3 [derived]), handled by sweeps and loops over seconds, not per block.
#### Used in
- 2026-11-15: lit_card_space.md card 1.

### C40. NASA JPL, DSN Telecommunications Link Design Handbook 810-005, Module 207 Rev. A, "34-m and 70-m Telemetry Reception", 2003
- Link: https://deepspace.jpl.nasa.gov/dsndocs/810-005/207/207A.pdf   - Type: standard (agency handbook)   - Read depth: chars 0-100k of 111k via a text reader
#### What it does
Receiver and Ranging Processor: Costas for suppressed carrier, a dedicated QPSK / OQPSK loop; BL <= min(200 Hz, Rs/20);
FFT acquisition (>= 512 points) when the uncertainty exceeds half the loop BL; lock time ~20/BL; typical acquisition
about one minute; loop SNR >= 23 dB (QPSK), 17 dB (BPSK Costas), 10 dB (residual); QPSK 40 ksps-26 Msps; system loss
>= 0.3 dB.
#### What we took / could take
Evidence that deep-space receivers lock loops over seconds to minutes; not a single-burst competitor.
#### Used in
- 2026-11-15: lit_card_space.md card 2b.

### C41. M. Bertolucci, R. Cassettari, L. Fanucci, "On the Frequency Carrier Offset and Symbol Timing Estimation for CCSDS 131.2-B-1 High Data-Rate Telemetry Receivers", Sensors 21(9):2915, 2021, doi:10.3390/s21092915
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/   - Type: paper   - Read depth: full via a text reader
#### What it does
LEO Ka 5-500 Mbaud, Doppler ~20 % of Rs at 5 Mbaud (0.2 % at 500 Mbaud), 50 kHz/s; compares D&M / Kay / Fitz / L&R /
M&M / O'Shea; chooses an M&M + Fitz multi-algorithm Type II FLL (N = 64, k1 = 1/8, k2 = 1/32), residual 239 Hz rms;
FPGA frequency block 1723 LUT, 32 DSP, 544 MHz, 25 196 cycles per estimate.
#### What we took / could take
The low-baud CFO range behind the C8 correction ("real acquisition range smaller" only at 100 MBaud); FPGA cost of a
deployed-class DA estimator. The "M&M 705 Hz at -2 dB" figure quoted in lit_real_space.md was not visible in this read.
Already cited in competitors.md "Not worth implementing" (L&R, Fitz, Kay, D&M).
#### Used in
- (before 2026-11-15) competitors.md "Not worth implementing" row.
- 2026-11-15: `competitors.md` C8 deviation; `comparison_full.md` CCSDS style card (cfo text) and "Real system" block.

### C42. MathWorks, "End-to-End CCSDS Flexible Advanced Coding and Modulation Simulation with RF Impairments and Corrections" (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/satcom/ug/end-to-end-ccsds-flexible-advanced-coding-and-modulation-simulation-with-rf-impairments-and-corrections.html   - Type: app note   - Read depth: full page
#### What it does
Gardner timing, FM frame sync, FFT-based FLL (K1 = 0.17), FM fine estimate, pilot phase; 1 MHz CFO + 1 MHz Doppler,
50 kHz/s at 100 MBaud, Es/N0 1 dB; 15 frames (~2e6 symbols) for acquisition, then 0 bit errors.
#### What we took / could take
Context only (multi-frame).
#### Used in
- 2026-11-15: lit_card_space.md card 2b.

### C43. Creonic GmbH, "CCSDS AR4JA LDPC Encoder and Decoder - Product Brief", 2023
- Link: https://www.aldec.com/files/ip_products/PB_Creonic_CCSDS_AR4JA_LDPC_FEC_IP.pdf   - Type: datasheet (vendor)   - Read depth: full (lit_rates.md)
#### What it does
Eb/N0 at BER 1e-6 / 1e-7 / BLER 1e-5 for k = 1024 / 4096 / 16384, r = 1/2, 2/3, 4/5 (31 iterations, 6-bit input);
k = 1024 r 1/2 (= (2048, 1024), the same N and K as our rate 1/2): 2.20 dB at BLER 1e-5.
#### What we took / could take
The same-length real code at our 1/2 point: SE 0.985 at Es/N0 2.20 dB @ 1e-5 vs ours 0.984 at 1.79 dB @ 1e-3 (equal or
behind us).
#### Used in
- 2026-11-15: lit_rates.md 4.4; `comparison_full.md` CCSDS style "Real system" block (rates) and section E.

### C44. Safran Data Systems, "Cortex CRT - Digital Modem for Satellite Housekeeping & Critical Communications", datasheet COL000010.4.0, 2022
- Link: https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20CRT%20-%20Datasheet.pdf   - Type: datasheet (vendor)   - Read depth: full
#### What it does
4000+ deployed TT&C modems; BPSK / (S)(O)QPSK / GMSK / AQPSK 1 kbps-40 Mbps, CCSDS Viterbi / LDPC / RS / turbo;
acquisition threshold Es/N0 < -2 dB; BER degradation < 0.5 dB typical; Doppler compensation, automatic ambiguity
resolution.
#### What we took / could take
The lowest vendor acquisition threshold found for CCSDS telemetry (continuous signal, ~3 dB above our lowest point).
#### Used in
- 2026-11-15: `comparison_full.md` CCSDS style "Real system" block (loss); lit_card_space.md card 2b.

### C45. Safran Data Systems, "Cortex HDR - High Data Rate Receiver for Space Science and Earth Observation", datasheet COL000016.4.0, 2022
- Link: https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20HDR%20-%20Datasheet.pdf   - Type: datasheet (vendor)   - Read depth: full
#### What it does
1000+ units; up to 6 channels, 10 Gbps; BPSK ... 64APSK; DVB-S2 / S2X / SCCC, LDPC 7/8 and AR4JA; no sync
specifications.
#### What we took / could take
Deployment evidence only.
#### Used in
- 2026-11-15: `comparison_full.md` CCSDS style "Real system" block (deployments).

### C46. Kongsberg (KSGS), "MEOS Capture HRDFEP" data sheet v1.1, 2025
- Link: https://www.kongsberg.com/globalassets/kongsberg-defence--aerospace/1.-what-we-do/1.4-space-and-surveillance/connecting-space--earth/space-ground-systems/wideband-receivers/2025/ksgs-qa-25072-hrdfep-data-sheet-v1.1.pdf   - Type: datasheet (vendor)   - Read depth: snippet only (HTTP 500)
#### What it does
CCSDS 131.2-B-2 compliant; "implementation loss typically less than 0.5 dB"; "Doppler on carrier 1500 kHz" (snippet).
#### What we took / could take
Context only (unverified).
#### Used in
- 2026-11-15: `comparison_full.md` CCSDS style "Real system" block (deployments, loss; marked snippet).

### C47. R. Andreotti, L. Nanna, M. Andrenacci, A. Isca, H.-C. Haugli, N. Alagha, "On-field test campaign performance of VDE-SAT Link ID 20 over Norsat-2 LEO satellite", Int. J. Satell. Commun. Netw. 41(2):195-215, 2023 (online 10 Nov 2021), doi:10.1002/sat.1437
- Link: https://onlinelibrary.wiley.com/doi/10.1002/sat.1437   - Type: paper   - Read depth: metadata and abstract snippets only (403)
#### What it does
Over-the-air uplink RA tests (Pisa ground platform emulating vessels -> NorSat-2), post-processed; demodulator with a
preamble searcher, DA CFO ("such as Rife and Boorstyn", snippet) and pilot phase; up to 22 overlapping RAC messages
demodulated.
#### What we took / could take
Real VDE-SAT receivers use DA R-B-type estimation on preamble + pilots: the same family as C6.
#### Used in
- 2026-11-15: `comparison_full.md` VDE-SAT "Real system" block (deployments, estimator).
- 2026-11-17: `testing/results/lit_vdesat_fullsystem.md` section 3 (VDE-SAT receiver).

### C48. L. Nanna, R. Andreotti, M. Andrenacci, N. Alagha, "VDE-SAT Link ID 20 performance assessment under different random access conditions", IET Conference Proceedings 2022(29):241-247, published 2023, doi:10.1049/icp.2023.1393
- Link: http://digital-library.theiet.org/doi/10.1049/icp.2023.1393   - Type: paper   - Read depth: metadata only
#### What it does
Not read.
#### What we took / could take
Nothing.
#### Used in
- none.

### C49. ESA, "VDE-SAT Downlink Verification" (NorSat-2) activity page, 2018
- Link: https://resilience.esa.int/?p=17839   - Type: app note (agency page)   - Read depth: full
#### What it does
NorSat-2 SDR payload (launched 14 July 2017) as an arbitrary waveform generator, 3 VDE-SAT test waveforms (150 kHz,
M.2092-0 / G1139) + a CW tone; Kongsberg Seatex ship receiver on KV Harstad, reference at Andoya; IQ recording + MATLAB
software demodulator (SER, offsets, Ec/N0); 103 passes in Nov 2017; no link numbers published.
#### What we took / could take
Deployment evidence for C6's real system; no sync numbers.
#### Used in
- 2026-11-15: `comparison_full.md` VDE-SAT "Real system" block (deployments).

### C50. IALA ENAV16 WG3, draft Annex 4 "satellite downlink" (VDE-SAT draft technical description), 2016
- Link: https://www.iala.int/content/uploads/2016/06/enav16_14_2_20_wg3_pdnr_annex_4_satellite_downlink.pdf   - Type: standard (draft)   - Read depth: full via a text reader
#### What it does
Superseded draft waveform (Barker-13 sync, CW pilot, QPSK 2.625 / 21 kbaud); TX error < 1 ppm (+-160 Hz), Doppler +-4 kHz;
C/(N0+I0) 41-47 dB-Hz.
#### What we took / could take
Origin of the +-160 Hz / +-4 kHz budget wording only.
#### Used in
- 2026-11-15: lit_card_space.md card 3.

### C51. Alen Space, "Alen Space places SATMAR satellite into orbit to boost the digitalization of maritime communications", 24 June 2025
- Link: https://alen.space/alen-space-places-satmar-satellite-into-orbit-to-boost-the-digitalization-of-maritime-communications/   - Type: press   - Read depth: full
#### What it does
VDES in-orbit validation satellite launched 23 June 2025 (Transporter-14); no waveform details.
#### What we took / could take
Deployment list only.
#### Used in
- 2026-11-15: `comparison_full.md` VDE-SAT "Real system" block (deployments).

### C52. A. Chakrapani, "NB-IoT Uplink Receiver Design and Performance Study", IEEE Internet of Things Journal, 2020 (arXiv 1906.07096)
- Link: https://arxiv.org/abs/1906.07096   - Type: paper   - Read depth: full text via a text reader
#### What it does
Qualcomm FSM small-cell NB-IoT uplink receiver. NPUSCH format 1: DMRS (symbol 3) averaged over tones, per block of 8 ms
(multi-tone) or 32 ms (single-tone); 256-point FFT of the DMRS phase sequence, peak + quadratic interpolation, search
+-250 Hz, resolution ~7.8 Hz; format 2 reuses it. Not iterative. Results vs TS 36.104: e.g. 1 tone 1 rep -2.1 (3GPP) /
-4.5 (sim) / -4.2 dB (test); fixed-point loss < 0.5 dB; NPRACH Pd >= 99 %, Pfa <= 0.1 %, max NPRACH offset ~+-357 Hz.
#### What we took / could take
Deployed NB-IoT CFO estimator and window (+-250 Hz = 0.018 cycles/symbol at 15 kHz [derived]) for the C10 card: C10 is
a widened (stronger) version. Not adopted into blind.
#### Used in
- 2026-11-15: `competitors.md` C10 deviation (window) and fidelity table; `comparison_full.md` DMRS 1/7 card (changes
  text) and "Real system" block.

### C53. Y.-P. E. Wang et al., "A Primer on 3GPP Narrowband Internet of Things (NB-IoT)", IEEE Commun. Mag., 2017 (arXiv 1606.04171)
- Link: https://arxiv.org/pdf/1606.04171   - Type: paper   - Read depth: full text via a text reader
#### What it does
NB-IoT structure: NPUSCH F1 7 symbols / slot, 1 DMRS (middle); F2 3 DMRS; single tone 15 / 3.75 kHz with pi/2-BPSK,
pi/4-QPSK; multi-tone 3 / 6 / 12; initial crystal offset up to 20 ppm; raster offset 2.5 / 7.5 kHz.
#### What we took / could take
Confirms the 1/7 DMRS density of C10 and that single-tone NPUSCH is structurally the same comb.
#### Used in
- (before 2026-11-15) competitors.md C10 link; est5 `dmrs7` (expected_est5.md).
- 2026-11-15: `comparison_full.md` DMRS 1/7 "Real system" block.

### C54. MathWorks, LTE Toolbox: `lteULFrameOffsetNPUSCH` and "NB-IoT NPUSCH Block Error Rate Simulation" (accessed 2026-11-15)
- Link: https://www.mathworks.com/help/lte/ug/nb-iot-npusch-block-error-rate-simulation.html ; https://www.mathworks.com/help/lte/ref/lteulframeoffsetnpusch.html   - Type: app note (vendor)   - Read depth: full (BLER page), snippet (DMRS position)
#### What it does
DMRS on symbol 4 (3.75 kHz) / 3 (15 kHz) for NPUSCH format 1; BLER example (A16-5 FRC, 12 tones, 15 kHz, TBS 136, QPSK,
repetitions 2 / 16 / 64, 5 TBs per SNR point) with timing from the DRS correlation, perfect or DRS-based channel
estimation, no CFO model.
#### What we took / could take
DMRS positions for the C10 card; NPUSCH runs at low SNR by repetition (not comparable to one burst).
#### Used in
- 2026-11-15: lit_card_terr.md 1.2, lit_rates.md 4.7.

### C55. Ericsson (G. Lu, O. Mauritz, F. Huss, H. Back), "Estimation of frequency offset between a base station and mobile terminal", US 8605799 B2, 2013
- Link: https://patents.google.com/patent/US8605799B2/en   - Type: patent   - Read depth: partial (description summary)
#### What it does
LTE PUSCH RS spacing 0.5 ms -> +-1000 Hz; PUCCH ~4/14 ms -> +-1750 Hz; combines both lags through a hypothesis table of
offset regions to resolve wrap-around (ideal limit 7 kHz). No SNR numbers.
#### What we took / could take
Deployed example of CFO hypothesis resolution with two lags; we already do a stronger version (decoder-scored grid).
The +-1 kHz DMRS range (0.071 cycles/symbol at 15 kHz [derived]) of the C10 card.
#### Used in
- 2026-11-15: `comparison_full.md` DMRS 1/7 "Real system" block (DMRS range).

### C56. 3GPP TS 36.521-1 clause 6.5.1F (NB-IoT frequency error, cat NB1 / NB2), via the itecspec mirror
- Link: https://itecspec.com/spec/3gpp-36-521-1-6-5-1f-frequency-error-for-category-nb1-and-nb2   - Type: standard   - Read depth: snippet only
#### What it does
Cat NB1 / NB2 UE frequency error +-0.1 ppm (> 1 GHz), +-0.2 ppm (<= 1 GHz) over one slot vs the received DL carrier;
test +15 Hz.
#### What we took / could take
Terrestrial NB-IoT CFO budget: 0.013 cycles/symbol at 900 MHz, 15 kHz single tone [derived].
#### Used in
- 2026-11-15: `comparison_full.md` DMRS 1/7 "Real system" block (design CFO).

### C57. O. Liberg et al., "Narrowband Internet of Things for Non-Terrestrial Networks", IEEE Communications Standards Magazine, 2020 (arXiv 2010.04906)
- Link: https://arxiv.org/pdf/2010.04906   - Type: paper   - Read depth: full text via a text reader
#### What it does
NB-IoT over GEO / LEO: GNSS + ephemeris based timing and Doppler pre-compensation; LEO 600 km Doppler capped at 24 ppm by
the 10 deg elevation limit; delay rate up to 24 us/s; link budgets. No residual-error numbers.
#### What we took / could take
NTN Doppler context for the C10 card.
#### Used in
- 2026-11-15: lit_card_terr.md 1.3.

### C58. Ericsson, "Frequency offset in non-terrestrial networks", US 12136966 B2, 2024
- Link: https://patents.google.com/patent/US12136966B2/en   - Type: patent   - Read depth: first 100k characters
#### What it does
LEO 600 km: max Doppler 43 kHz / 21 ppm at 2 GHz; Doppler rate up to 500 Hz/s; oscillator drift 0.01 ppm/s; two UEs'
UL frequency difference up to ~16 kHz.
#### What we took / could take
Doppler-rate value for the drift-test discussion (raw, before UE pre-compensation).
#### Used in
- 2026-11-15: lit_card_terr.md 1.3, 6.

### C59. 3GPP RAN1 #110 draft CR R1-2208176 to TS 36.213 (IoT-NTN UE pre-compensation); RAN4 LS reply on pre-compensation for IoT NTN TDD (R4-2512550)
- Link: https://3gpp.org/ftp/TSG_RAN/WG1_RL1/TSGR1_110/Inbox/drafts/8.14(LTE_NBIOT_eMTC_NTN)/CR%20to%2036.213-UE%20pre-compensation/DRAFT-R1-2208176-Moderator-CR%20to%2036.213-Maintenance%20on%20IoT-NTN.docx   - Type: standard (draft)   - Read depth: snippet
#### What it does
NB-IoT UE adjusts time and frequency pre-compensation per uplink segment (npusch-TxDuration), with uplink compensation
gaps; pre-compensation updated at the start of each segment. Segment duration values not found.
#### What we took / could take
How Rel-17 handles Doppler rate (re-compensation per segment). Not used.
#### Used in
- none.

### C60. 3GPP R4-2216641 (revised), "(R17 NTN) CR on NTN frequency error requirement", draft
- Link: https://3gpp.org/ftp/tsg_ran/WG4_Radio/TSGR4_104bis-e/Inbox/Drafts/%5B104-bis-e%5D%5B304%5D%20NTN_Solutions_RF_Maintenance/Rnd2/revised%20R4-2216641%20(R17%20NTN)%20%20CR%20on%20NTN%20Frequency%20error%20requirement.docx   - Type: standard (draft CR)   - Read depth: snippet
#### What it does
NR NTN UE frequency error +-0.1 ppm over 1 ms relative to the ideally pre-compensated carrier (draft wording).
#### What we took / could take
NTN residual budget with GNSS: ~0.014 cycles/symbol at 15 kHz [derived]. Not confirmed as final text.
#### Used in
- 2026-11-15: lit_card_terr.md 1.3.

### C61. "5G NR Non-Terrestrial Networks: From Early Results to the Road Ahead", arXiv 2601.04882, 2026
- Link: https://arxiv.org/html/2601.04882   - Type: paper   - Read depth: full HTML
#### What it does
Rel-17 GNSS-based TA / frequency pre-compensation (not usable indoors); Rel-18 PUSCH DMRS bundling for phase
continuity; Rel-20 to study GNSS-resilient operation. Qualitative only.
#### What we took / could take
Release context for the C10 card. Not used.
#### Used in
- none.

### C62. "Performance Analysis of NB-IoT Uplink in Low Earth Orbit Non-Terrestrial Networks", Sensors 22(18) 7097, 2022
- Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC9502177/   - Type: paper   - Read depth: snippet only (captcha)
#### What it does
LEO NB-IoT uplink: added DMRS improves BLER; residual compensation range ~950 Hz; beam-size reduction proposed.
#### What we took / could take
Not used: numbers not verifiable.
#### Used in
- none.

### C63. Press on NB-IoT and NB-IoT NTN deployments (RCR Wireless 2024: Soracom / Skylo launch, Sony ALT1250 certification; CNX Software 2023: Qualcomm 9205S / 212S; GSMA via RCR Wireless 2018)
- Link: https://rcrwireless.com/20240717/internet-of-things/soracom-offers-satellite-nb-iot-from-skylo-in-phased-commercial-launch ;
  https://www.rcrwireless.com/20240503/internet-of-things-4/skylo-certifies-nb-iot-chipset-from-sony-semiconductor-for-dual-mode-satellite-iot ;
  https://www.cnx-software.com/2023/06/23/qualcomm-212s-and-9205s-satellite-iot-modems-target-remote-monitoring-and-asset-tracking/ ;
  https://rcrwireless.com/20180518/internet-of-things/gsma-48-mobile-iot-networks-worldwide-tag23   - Type: press   - Read depth: snippet
#### What it does
Skylo GEO Rel-17 NB-IoT service; Soracom phased launch July 2024; certified chipsets (Sony ALT1250, u-blox UBX-S52,
Quectel, Telit); Sateliot LEO; 32 NB-IoT networks by early 2018 (GSMA).
#### What we took / could take
"Real deployments" line of the C10 card.
#### Used in
- 2026-11-15: `comparison_full.md` DMRS 1/7 "Real system" block (deployments).

### C64. 3GPP TS 36.213 Table 7.2.3-1 (4-bit CQI table), as reproduced in US patent 10079655 and on sqimway.com
- Link: https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10079655 ; https://sqimway.com/nr_pdsch.php   - Type: standard (secondary)   - Read depth: snippet (search-result text; the 3GPP document not opened)
#### What it does
QPSK CQI code rates 78, 120, 193, 308, 449, 602 / 1024 (efficiencies 0.1523 ... 1.1758 per RE).
#### What we took / could take
Indicative LTE rates only (10 % BLER, OFDM, HARQ: not comparable).
#### Used in
- 2026-11-15: lit_rates.md 4.7; `comparison_full.md` DMRS 1/7 "Real system" block (rates, marked not comparable).

### C65. I. Ahmad, Z. Kaleem, K. Chang, "Block Error Rate and UE Throughput Performance Evaluation using LLS and SLS in 3GPP LTE Downlink", arXiv:1810.01162
- Link: https://arxiv.org/pdf/1810.01162   - Type: paper   - Read depth: full (figure read for the CQI mapping)
#### What it does
LTE downlink AWGN link-level CQI mapping at 10 % BLER: CQI 1 at ~-7 dB, ~2 dB per CQI step.
#### What we took / could take
The indicative SNRs of the LTE CQI row in lit_rates.md (not comparable to our 1e-3 / 1e-4 targets).
#### Used in
- 2026-11-15: lit_rates.md 3, 4.7; `comparison_full.md` DMRS 1/7 "Real system" block (rates).

### C66. MathWorks, `wlanCoarseCFOEstimate` (WLAN Toolbox, accessed 2026-11-15)
- Link: https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html   - Type: app note (vendor)   - Read depth: full
#### What it does
L-STF autocorrelation coarse CFO; max 625 kHz (2 subcarrier spacings); `corrOffset` default 0.75 of a short symbol
skipped against delay spread; L-STF 8 us at 20 MHz; L-LTF fine max 156.25 kHz; refs Li 2001, Moose 1994 (B9), Perahia
& Stacey 2013.
#### What we took / could take
The C12 coarse / fine stages (lag 16 / lag 64).
#### Used in
- (before 2026-11-15) competitors.md C12 link; est5 `wifi128` (expected_est5.md).
- 2026-11-15: `comparison_full.md` WiFi pre128 "Real system" block.

### C67. OpenOFDM documentation, "Frequency Offset Correction" (open-source 802.11a/g FPGA receiver)
- Link: https://openofdm.readthedocs.io/en/latest/freq_offset.html   - Type: app note (open implementation)   - Read depth: full
#### What it does
Coarse CFO = angle(sum conj(S[i]) S[i+16]) / 16 with a 64-sample moving average; correction applied from the LTF on; the
fine LTF stage is omitted because of LUT phase-resolution limits; pilots used for SFO.
#### What we took / could take
Evidence that real Wi-Fi hardware may run only the lag-16 coarse stage; C12's two-stage + lobe search is stronger.
#### Used in
- 2026-11-15: `comparison_full.md` WiFi pre128 "Real system" block (estimator); `competitors.md` fidelity table (C12).

### C68. Keysight 89600 VSA help, "SymClkErr (802.11a/g/j/p OFDM)"
- Link: https://helpfiles.keysight.com/csg/89600B/Webhelp/Subsystems/wlan-ofdm/content/ofdm_symtblerrdata_symclkerr.htm   - Type: app note (vendor)   - Read depth: snippet
#### What it does
Symbol clock (and carrier, same oscillator) tolerance +-20 ppm (802.11a/j/p), +-25 ppm (802.11b/g).
#### What we took / could take
Wi-Fi CFO budget: 0.0117 cycles/sample at 5.8 GHz, 0.0062 at 2.4 GHz [derived].
#### Used in
- 2026-11-15: `comparison_full.md` WiFi pre128 "Real system" block (design CFO).

### C69. WARP project, "802.11 Reference Design Rx characterization" (wiki)
- Link: https://warpproject.org/trac/wiki/802.11/Benchmarks/Rx_Char?version=10   - Type: app note (open implementation)   - Read depth: snippet (403 on fetch)
#### What it does
802.11-2012 18.3.10.2 minimum sensitivity: 6 Mb/s -82 dBm at PER 10 %, 1000 octets; WARP measured -85 (later -88) dBm.
#### What we took / could take
Minimum operating SNR context (~+4 dB, derived with an assumed NF and margin).
#### Used in
- 2026-11-15: `comparison_full.md` WiFi pre128 "Real system" block (rates: none in our range).

### C70. G. Baruffa, L. Rugini, "Improved Channel Estimation and Equalization for Single-Carrier IEEE 802.11ad Receivers", Radioengineering 32(3), 2023
- Link: https://www.radioeng.cz/fulltexts/2023/23_03_0438_0450.pdf   - Type: paper   - Read depth: full via a text reader
#### What it does
802.11ad SC frame: STF 17 x 128, CEF 9 x 128, LDPC 672-bit codewords in 448-symbol blocks + Ga64 GI (512-symbol cyclic
blocks, GI reused as known data), pi/2 rotation, 1760 MS/s; assumes ideal sync; channel-estimation gains 0.5-0.95 dB.
#### What we took / could take
The 802.11ad SC known-symbol layout: shows C12 does not model 11ad (the "(also 802.11ad SC)" label was removed).
#### Used in
- 2026-11-15: `competitors.md` C12 correction.

### C71. A. Lomayev et al. (Intel), US 10615930, 802.11ay adaptive guard interval (claim)
- Link: https://patentimages.storage.googleapis.com/b4/7f/5f/550f3e1a0fcef2/US10615930.pdf   - Type: patent   - Read depth: snippet
#### What it does
EDMG SC GI types: short 32 (480 data), normal 64 (448), long 128 (384) chips.
#### What we took / could take
802.11ay known fractions 6.25 / 12.5 / 25 % [derived]. Not used.
#### Used in
- none.

### C72. W.-C. Liu, T.-C. Wei, Y.-S. Huang, C.-D. Chan, S.-J. Jou, "All-Digital Synchronization for SC/OFDM Mode of IEEE 802.15.3c and IEEE 802.11ad", IEEE TCSI 62(2), 545-553, 2015, doi:10.1109/TCSI.2014.2361035
- Link: https://ir.lib.nycu.edu.tw:443/handle/11536/124352   - Type: paper   - Read depth: abstract via search
#### What it does
Joint preamble detection, boundary detection, CFO estimation on the Golay preamble; 8x parallel feed-forward; tolerates
114.58 ppm (SC), 171.87 ppm (OFDM).
#### What we took / could take
11ad CFO range (0.0039 cycles/chip [derived]); a different structure from C12 (lag 128 Golay).
#### Used in
- (before 2026-11-15) competitors.md C12 link.
- 2026-11-15: `competitors.md` C12: moved from the C12 row to the deviations note "802.11ad SC is not modelled".

### C73. Terragraph documentation, "Runbook: Overview"; Qualcomm 802.11ay chipset press (Tom's Hardware, 2018)
- Link: https://terragraph.com/docs/runbook/Overview ; https://www.tomshardware.com/news/qualcomm-reveals-802-11ay-wi-fi-chipsets,37935.html   - Type: app note (vendor) + press   - Read depth: full (runbook), snippet (press)
#### What it does
Terragraph uses the 802.11ad single-carrier PHY (MCS 1-12, pi/2-BPSK / QPSK / 16QAM, 385-4620 Mb/s, 2.16 GHz channels),
GPS-synchronised nodes, on Qualcomm QCA6438 / QCA6428 (pre-802.11ay).
#### What we took / could take
Deployment line for 802.11ad SC (not a modelled competitor).
#### Used in
- 2026-11-15: lit_card_terr.md 2.1.

### C74. Wikipedia, "WiGig" (IEEE 802.11ad MCS and sensitivity table)
- Link: https://en.wikipedia.org/wiki/WiGig   - Type: app note (secondary)   - Read depth: full (the IEEE 802.11ad text not read)
#### What it does
MCS 0-12 modulation, rate, PHY rate, sensitivity (MCS 1-4: -68 / -66 / -65 / -64 dBm); assumptions 5 dB implementation
loss, 10 dB NF, PER < 1 % at 4 000 bytes (from a search snippet of a paper regenerating Table 21-3).
#### What we took / could take
802.11ad SC Es/N0 ~0.5-2.5 dB for MCS 2-4 and SE 0.44-0.66 [derived; noise bandwidth assumed 1.76 GHz]: far below our SE.
#### Used in
- 2026-11-15: lit_rates.md 4.6; `comparison_full.md` WiFi pre128 "Real system" block (rates).

### C75. Keysight, "802.11ad Concepts", N7637 help
- Link: https://helpfiles.keysight.com/csg/n7637/Content/Main/802.11ad%20Concepts.htm   - Type: app note (vendor)   - Read depth: partial
#### What it does
802.11ad LDPC codeword 672 bits.
#### What we took / could take
Block length of the 802.11ad row in lit_rates.md.
#### Used in
- 2026-11-15: lit_rates.md 4.6.

### C76. MIL-STD-188-110C with Change Notice 1, "Interoperability and Performance Standards for Data Modems" (2011 / 2012; superseded by 110D, C78)
- Link: https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf   - Type: standard   - Read depth: text reader, chars 200k-400k (lit_card_terr.md); Tables XV, XVI, C-XVII, D-XI / D-XII / D-XLI, Table D-LII not legible (lit_rates.md)
#### What it does
App C (3200-9600 bps, 12 800 uncoded; = STANAG 4539): 2400 Bd, 287-symbol preamble (184 sync / Doppler + 103 rate /
interleaver incl. a 31-symbol mini-probe), frames of 256 data + 31-symbol mini-probe, +72 known every 72 frames (11.1 %
known; 411 known per 1024 data, 1.47 dB [derived]); +-75 Hz at 2400 Bd = 0.031, tested at 30 dB SNR; Doppler sweep
3.5 Hz/s; acquisition "not yet standardized". App D (WBHF = STANAG 5069): known fraction per WID 50 / 25 / 11.1 /
6.25 %. AWGN requirements only at 2400 bps (SNR 10 dB / 3 kHz, BER 1e-5) and above.
#### What we took / could take
The C13 layout (184 + probes, our 308 known); correction: the real waveform carries 411 known per 1024 data, so our C13
is ~0.33 dB more favourable. No AWGN requirement in our Es/N0 range.
#### Used in
- (before 2026-11-15) competitors.md C13 link; est5 `mil110`.
- 2026-11-15: `competitors.md` C13 deviation (411 vs 308, 110D) and fidelity table; `comparison_full.md` MIL-110 HF card
  (changes text) and "Real system" block.

### C77. ITU-R Recommendation F.763-5 (2005), "Data transmission over HF circuits using PSK or QAM", Annex 6 (STANAG 4539)
- Link: https://www.itu.int/dms_pubrec/itu-r/rec/f/R-REC-F.763-5-200501-P!!PDF-E.pdf   - Type: standard   - Read depth: text reader (Annex 6)
#### What it does
287-symbol preamble (+0-7 x 184 AGC), 256 data + 31 mini-probe, 72-symbol reinsertion every 72 frames, 2400 Bd, +-75 Hz
tolerance; coded BER 1e-4 SNR (3 kHz): 3200 bps 9 dB AWGN / 14 dB poor, 9600 bps 21 / 30 dB.
#### What we took / could take
Confirms the App C frame and range for the C13 card.
#### Used in
- 2026-11-15: `comparison_full.md` MIL-110 HF "Real system" block (standard, rates).

### C78. MIL-STD-188-110D (29 Dec 2017), listing (EverySpec) and AFCEA comment
- Link: https://everyspec.com/MIL-STD/MIL-STD-0100-0299/MIL-STD-188-110D_55856/ ; https://www.afcea.org/comment/1627   - Type: standard (listing)   - Read depth: snippet
#### What it does
Current revision; Appendix D extended to contiguous bandwidths up to 48 kHz, up to 240 kb/s.
#### What we took / could take
Version note for the C13 card (110C is superseded).
#### Used in
- 2026-11-15: `competitors.md` C13 (superseded by 110D); `comparison_full.md` MIL-110 HF "Real system" block.

### C79. MathWorks, "US MIL-STD-188-110A Receiver" (Communications Toolbox example)
- Link: https://in.mathworks.com/help/comm/ug/defense-communications-us-mil-std-188-110a-receiver.html   - Type: app note (vendor)   - Read depth: full
#### What it does
Preamble correlator + 3-peak state machine; CFO removed by an NCO driven by a PI loop on the phase slope (LS fit) of the
equaliser input / output cross-spectrum; RLS DFE 20 + 20 taps; Watterson channel; no numbers.
#### What we took / could take
Shows deployed-style HF tracking is equaliser / decision-directed, not one-shot.
#### Used in
- 2026-11-15: `comparison_full.md` MIL-110 HF "Real system" block (estimator).

### C80. L3Harris, RF-7800H-MP wideband HF/VHF tactical radio datasheets (2019, 2022)
- Link: https://l3harris.com/sites/default/files/2020-07/cs_tc_datsheet_rf-7800h-mp-wideband-hf-vhf-tactical-radio-system.pdf   - Type: datasheet   - Read depth: snippet
#### What it does
Wideband waveforms MIL-STD-188-110C App D (2019 sheet), MIL-STD-188-110D (2022 sheet); 50 000 Falcon III units by 2023
(vendor press).
#### What we took / could take
Deployment line for the C13 card.
#### Used in
- 2026-11-15: `comparison_full.md` MIL-110 HF "Real system" block (deployments).

### C81. W. N. Furman, J. W. Nieto, "Latest on-air testing of U.S. MIL-STD-188-110C Appendix D wideband HF data waveforms", IET HF Radio Systems and Techniques, 2012; M. Jorgenson, R. Johnson, R. Nelson, "An extension of wideband HF capabilities", MILCOM 2013, doi:10.1109/MILCOM.2013.205
- Link: https://digital-library.theiet.org/content/conferences/10.1049/cp.2012.0386   - Type: paper   - Read depth: index only
#### What it does
On-air App D tests (160 km NVIS, 1700 km); App D extensions. Full texts not read.
#### What we took / could take
Nothing (not read).
#### Used in
- none.

### C82. C. Wang, Z. Li, Z. Dong et al., "Highly robust and hardware-efficient frame synchronization and carrier recovery via pilot-only approaches for short-reach optical interconnections", Chinese Optics Letters 23(6), 060602, 2025
- Link: https://www.researching.cn/ArticlePdf/m00005/2025/23/6/060602.pdf   - Type: paper   - Read depth: full via a text reader
#### What it does
States that OIF 400ZR frames use training sequences for frame sync and initial frequency-offset locking and pilots for
phase tracking; 800G LR pilot interval 32 -> 64; proposes pilot-only sync (60 GBd DP-16QAM, CFO range +-13 GHz vs +-7.5
GHz for FFT-FOE + BPS, 0.7 dB sensitivity gain).
#### What we took / could take
Correction to lit_real_terrestrial.md ("400ZR coarse FOE must be blind"): the real coarse stage is likely TS-aided
(paper statement; the OIF IA text could not be read). C11 unchanged.
#### Used in
- 2026-11-15: `competitors.md` C11 deviation; `comparison_full.md` Sparse pilots 1/32 card (changes text) and "Real
  system" block.

### C83. Comtech EF Data, "DMD1050TS L-Band Satellite Modem Board" datasheet, 11/2018
- Link: https://comtech.com/wp-content/uploads/2022/04/ds-DMD1050TS.pdf   - Type: datasheet (vendor)   - Read depth: full (lit_rates.md)
#### What it does
Guaranteed / typical Eb/N0 at BER 1e-5 for Viterbi, TPC, STANAG 4486 turbo and LDPC modes (SCPC, continuous): e.g. QPSK
turbo 1/2 Es/N0 1.72 dB guaranteed (1.32 typical) [derived], BPSK modes -2.6 ... +0.8 dB.
#### What we took / could take
The only real-modem threshold table read (implementation losses included): 0.73-1.02x our SE at the same Es/N0.
#### Used in
- 2026-11-15: lit_rates.md 3, 4.9; `comparison_full.md` pre128 / split64 "Real system" block (nearest real modem table)
  and section E (1/2 row).

---

### C84. ITU-R Report M.2435-0 (2018), VDES characteristics and simulations
- Link: https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-M.2435-2018-PDF-E.pdf   - Type: report
- Read depth: search snippet only (the PDF / DOCX are over 10 MB and could not be fetched by the agent).
#### What it does
ITU-R simulations of the VDES / VDE-SAT links; snippet: "QPSK turbo 1/4: -1.5 dB at PER 1e-2" (unverified).
#### What we took / could take
The only AWGN PER reference found for VDE-SAT formats; needs to be opened by hand to validate our VDE-SAT implementation.
#### Used in
- 2026-11-17: `testing/results/lit_vdesat_fullsystem.md` section 4 (-1.5 dB at PER 1e-2, unverified).
- 2026-11-17: `testing/results/lit_vde_fec.md` 0.4: 4.3.1 read in the local text: 88 info bits, QPSK turbo 1/4,
  -1.5 dB at PER 1e-2, -0.3 dB at BER 1e-5 (AWGN) as the validation target.

### C85. VDES satellite-component article, CEAS Space Journal, doi:10.1007/s12567-018-0214-8
- Link: https://doi.org/10.1007/s12567-018-0214-8   - Type: paper
- Read depth: full page.
#### What it does
Describes the VDE-SAT receiver side: E-SSA style detection, CRC check and successive interference cancellation.
#### What we took / could take
Receiver structure for the full-system VDE-SAT implementation (CRC-based acceptance).
#### Used in
- 2026-11-17: `testing/results/lit_vdesat_fullsystem.md` section 3 (E-SSA receiver, CRC + SIC).

### C86. AFF3CT (A Fast Forward Error Correction Toolbox), DVB-RCS2 duo-binary turbo: `Interleaver_core_ARP_DVB_RCS2.cpp`, `Encoder_RSC_DB.cpp` (MIT licence)
- Link: https://github.com/aff3ct/aff3ct (files under src/Tools/Interleaver/ARP/ and src/Module/Encoder/RSC_DB/)   -
  Type: open-source code   - Read depth: interleaver file full; encoder file: polynomial vectors, circ_states table,
  state-update logic (via a summariser)
#### What it does
Implements the EN 301 545-2 V1.3.1 16-state duo-binary RCS2 turbo code: P / Q0-Q3 for all 30 Table A-1 block sizes
(56-2396 couples), the ARP permutation (P j + Q(j mod 4) + 3) mod N, the 14 x 16 circulation-state table, encoder taps
A 1000, B 1101, Y 11101, W 10111, feedback 0011.
#### What we took / could take
The P / Q table and the circulation table (EN text garbled) for the RCS2 turbo implementation; a reference encoder to
check ours bit-exactly.
#### Used in
- 2026-11-17: lit_rcs2_fullsystem.md 1.4.
- 2026-11-17: `testing/results/lit_turbo_db.md`: encoder taps, circulation table (3 hand checks), ARP table, puncturing
  masks, **AFF3CT interleaves with lut_inv (inverse of the EN 'read' form)**, decoder metric passing, op count.

### C87. MathWorks, `dvbrcs2TurboDecode` / `dvbrcs2TurboEncode` (Satellite Communications Toolbox)
- Link: https://www.mathworks.com/help/satcom/ref/dvbrcs2turbodecode.html   - Type: app note / reference code   - Read
  depth: full page
#### What it does
Standard-compliant RCS2 duo-binary turbo decoder, default 8 iterations, rates 1/3-7/8; algorithm not named.
#### What we took / could take
A bit-exact cross-check of our encoder (level-1 / level-2 order, Z1 / Z2 order) if MATLAB is available.
#### Used in
- 2026-11-17: lit_rcs2_fullsystem.md 3.2, 6.
- 2026-11-17: `testing/results/lit_turbo_db.md`: named as the bit-exact arbiter for the interleaver direction; LLR sign
  positive = 1; 8 iterations default.

### C88. O. Boxerman, M. Bensimon, S. Greenberg, Y. Ben-Shimol, "A novel reconfigurable vector-processed interleaving algorithm for a DVB-RCS2 turbo encoder", arXiv:2308.14128, 2023
- Link: https://arxiv.org/abs/2308.14128 (HTML: https://arxiv.org/html/2308.14128, v2)   - Type: paper   - Read depth:
  abstract; 2026-11-17 HTML full text via a summariser (lit_turbo_db.md)
#### What it does
Parallel DSP interleaving for the RCS2 turbo encoder; speed-up up to 3.4x total cycles vs serial. Vectorised DSP
(CEVA-XC4500) version of the two-level interleaver; quotes eq. 1 (swap if j mod 2 = 1), eq. 2-3 (Pi(j) = (P j + Q + 3)
mod N, Q = 0 / 4Q1 / 4Q0P + 4Q2 / 4Q0P + 4Q3); 11 block sizes 56-2396.
#### What we took / could take
Nothing for the hardware side (encoder only). Second source for the ARP formula; its "j odd" swap equals AFF3CT's
"natural even" by the odd/even rule [derived] (lit_turbo_db.md).
#### Used in
- 2026-11-17: lit_rcs2_fullsystem.md source table (low relevance).
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 2.1-2.2 (second copy of the interleaver equations; the scout's
  entry C89 merged here).

### C90. AFF3CT error_rate_references, TURBO_DB DVB-RCS2 curves
- Link: https://github.com/aff3ct/error_rate_references (TURBO_DB/AWGN/BPSK/RSC_DB_RSC_DB/BCJR/)   - Type: data
- Read depth: 4 files (N1880 / N2256 / N3008 ref + fnc / N4512, K = 1504)
#### What it does
Reference BER / FER of the RCS2 code with the exact AFF3CT command line (QPSK AWGN, max-log, adaptive SF, 8 it).
#### What we took / could take
FER validation targets for our Python decoder (e.g. rate 1/2 FER 1.22e-2 at Eb/N0 1.4 dB).
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 5.

### C91. AFF3CT documentation: v4.5.0 Turbo DB / RSC DB codec parameters and simulation debug; turbo encoder and interleaver parameters (latest)
- Link: https://aff3ct.readthedocs.io/en/v4.5.0/user/simulation/parameters/codec/turbo_db/decoder.html ;
  https://aff3ct.readthedocs.io/en/latest/user/simulation/parameters/interleaver/interleaver.html   - Type: docs
- Read depth: 4 doc pages (lit_turbo_db.md); turbo / interleaver pages (lit_vde_fec.md)
#### What it does
Flags: `--enc-sub-std DVB-RCS2`, `--dec-max MAX|MAXL|MAXS`, `--dec-sf-type ADAPTIVE (0.5, then 0.85) | LTE (0.75) |
CST | ARRAY`, `--dec-crc-start`, `--sim-dbg` (prints every task's frames, hex option). The binary turbo codec has LTE /
CCSDS presets and a USER interleaver read from a file; one-parity RSC.
#### What we took / could take
Recipe to dump bit-exact test vectors and the scaling options for the RCS2 competitor decoder. For VDE only a partial
cross-check (Y0-only puncturing).
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 4.1, 5.
- 2026-11-17: `testing/results/lit_vde_fec.md` section 5 (the scout's AFF3CT-docs entry merged here).

### C92. M. Martina, G. Masera, "Improving Network-on-Chip-based turbo decoder architectures", arXiv 1105.1014 (2011)
- Link: https://ar5iv.labs.arxiv.org/html/1105.1014   - Type: paper
- Read depth: HTML (via a summariser)
#### What it does
NoC turbo decoders incl. WiMAX duo-binary (8-state, N = 1920, 8 iterations, max-log-MAP).
#### What we took / could take
Support for max-log-MAP being near log-MAP on duo-binary codes (no 16-state number).
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 4.1.

### C93. IEEE 802.16 maintenance contributions C80216maint-05_149 and C80216maint-05_151 (CTC interleaver clarification)
- Link: https://grouper.ieee.org/groups/802/16/maint/contrib/C80216maint-05_149.pdf ,
  https://grouper.ieee.org/groups/802/16/maint/contrib/C80216maint-05_151.pdf   - Type: standards contribution
- Read depth: search snippets only (PDF text not legible)
#### What it does
Reports that the 802.16 CTC text was ambiguous about the order of the couple swap and the permutation and about the
address meaning of P(j).
#### What we took / could take
Precedent for our interleaver-direction ambiguity #1.
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 2.3.

### C94. ETSI EN 302 583 V1.2.1, "DVB-SH: Framing structure, channel coding and modulation for satellite services to handheld devices below 3 GHz", section 5.3 (turbo code)
- Link: https://www.etsi.org/deliver/etsi_EN/302500_302599/302583/01.02.01_60/en_302583v010201p.pdf   - Type: standard
- Read depth: section 5.3 via a text reader
#### What it does
3GPP2 (cdma2000) turbo code: 8-state RSC, d = 1+D^2+D^3, n0 = 1+D+D^3, n1 = 1+D+D^2+D^3, rates 1/5-2/3 by puncturing,
6-clock tail (RSC1 then RSC2), own bit-reversal interleaver (L = 1146 / 12282).
#### What we took / could take
Confirms the VDE constituent code and termination; its interleaver is not used by VDE.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` sections 1, 3.

### C96. J. H. Kim, "SIMULINK Modeling and FPGA Implementation of Turbo Decoder for VDES Receiver", J. KICS 50(3), 489-, March 2025, doi:10.7840/kics.2025.50.3.489
- Link: https://d2j16w31g89z0j.cloudfront.net/journal/jkics/fullText/1387/jkics-2503-12.pdf   - Type: paper
- Read depth: text via a reader (figures not readable)
#### What it does
VDES turbo decoder: log-MAP (128-entry max* LUT), sliding window 32, 6 iterations, on-the-fly interleaver, max input
6032 bits, Xilinx ZCU104 at 43.008 MHz, < 10 ms per block. PER 1 % at Es/N0 2.1 dB (Link 11, 432 bits, 1/2,
pi/4-QPSK), 1.5 dB (Link 17, 1872), 13 dB (Link 19, 5616, 3/4, 16QAM).
#### What we took / could take
Reference PER points and decoder settings for the VDE turbo baseline.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` sections 4, 6.

### C97. MathWorks, comm.TurboEncoder / comm.TurboDecoder System objects
- Link: https://www.mathworks.com/help/comm/ref/comm.turboencoder-system-object.html   - Type: vendor documentation
- Read depth: page
#### What it does
Turbo encoder with any rate-1/N RSC trellis (e.g. `poly2trellis(4,[13 15 17],13)` = the VDE RSC), any interleaver
permutation, custom output indices, per-encoder tails at the end.
#### What we took / could take
Independent cross-check of our Python codec (not run: no MATLAB).
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` section 5.

### C99. P. Robertson, E. Villebrun, P. Hoeher, "A comparison of optimal and sub-optimal MAP decoding algorithms operating in the log domain", Proc. IEEE ICC 1995, 1009-1013
- Link: https://ieeexplore.ieee.org/document/524253   - Type: paper   - Read depth: abstract (search result)
#### What it does
Log-MAP = MAP; SOVA ~0.7 dB worse at BER 1e-4; max-log-MAP in between; complexity in the same order.
#### What we took / could take
Log-MAP vs max-log-MAP choice for the VDE baseline; the op counts are the scout's own derivation.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` section 4.

### C100. "Iterative Decoding Algorithm for VDES Signals", Proc. ICDSP 2020 (ACM), doi:10.1145/3408127.3408158
- Link: https://dl.acm.org/doi/10.1145/3408127.3408158   - Type: paper   - Read depth: search snippet only (ACM 403)
#### What it does
BCJR / factor-graph iterative decoding for VDES (QPSK, 8PSK, 16QAM, 16APSK); results not read.
#### What we took / could take
Nothing yet.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` section 6 (unread).

### C104. NVIDIA Sionna, `Polar5GEncoder` source
- Link: https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/polar/encoding.py   - Type: code
- Read depth: code read
#### What it does
38.212 polar encoding with rate matching in Python; K <= 1013, E <= 1088, no segmentation.
#### What we took / could take
The 32-entry sub-block interleaver P table and the 9/8 rule; its extra (pre-)freezing is off by one vs A17 (noted).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` 1.3-1.4 (proposed).

### C105. MathWorks, "5G New Radio polar coding" example
- Link: https://www.mathworks.com/help/5g/gs/polar-coding.html   - Type: vendor doc   - Read depth: page
#### What it does
NR polar chain with rate recovery, K = 54, E = 124, L = 8; no BLER numbers.
#### What we took / could take
Rate-recovery LLR conventions: punctured LLR 0, shortened LLR large.
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` 1.4.

### C106. MathWorks, `nrUCIEncode`
- Link: https://www.mathworks.com/help/5g/ref/nruciencode.html   - Type: vendor doc   - Read depth: search snippet
#### What it does
NR UCI encoding with code-block segmentation when A >= 1013, or A >= 360 and E >= 1088.
#### What we took / could take
The NR segmentation condition (not adopted: we lift n_max instead).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` 1.2.

### C108. B. Coskun et al., "Efficient error-correcting codes in the short blocklength regime", Physical Communication 2019, arXiv 1812.08562
- Link: https://arxiv.org/abs/1812.08562   - Type: paper   - Read depth: ~93 % of the html
#### What it does
Survey with simulations at (128,64) and (512,256): polar with CRC-16, L = 32 ~ turbo at (512,256); LTE turbo -0.4 dB vs
the 16-state turbo at (128,64).
#### What we took / could take
The closest published polar vs turbo comparison to our K (code-only gain).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 3.

### C109. G. Liva, L. Gaudio, T. Ninacs, T. Jerkovits, "Code design for short blocks: a survey", 2016, arXiv 1610.00873
- Link: https://arxiv.org/abs/1610.00873   - Type: paper   - Read depth: html
#### What it does
Survey at (128,64) only: the 16-state turbo is 0.4 dB from the RCB at 1e-4.
#### What we took / could take
Nothing (k = 64 only).
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 3 (reference only).

### C110. M. Shirvanimoghaddam et al., "Short block-length codes for ultra-reliable low latency communications", IEEE Commun. Mag. 2019, arXiv 1802.09166
- Link: https://arxiv.org/abs/1802.09166   - Type: paper   - Read depth: html
#### What it does
Survey, N = 128; K = 40 and 1000 curves: CA-polar 0.5 dB from the normal approximation, turbo > 1 dB.
#### What we took / could take
Nothing.
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 3 (reference only).

### C112. M. Sybis, K. Wesolowski, K. Jayasinghe, V. Venkatasubramanian, V. Vukadinovic, "Channel coding for ultra-reliable low-latency communication in 5G systems", IEEE VTC-Fall 2016
- Link: https://nokia.com/bell-labs/publications-and-media/publications/channel-coding-for-ultra-reliable-low-latency-communication-in-5g-systems
- Type: paper   - Read depth: search snippet only (HTTP 403)
#### What it does
Comparison of 5G candidate codes at 40 / 200 bits (not read).
#### What we took / could take
Nothing.
#### Used in
- 2026-11-17: `testing/results/lit_polar_ratematch.md` section 3 (unverified).

## D. Blind / non-coherent polar, phase ambiguity, blind detection

### D1. P. Yuan, M. C. Coskun, G. Kramer, "Polar-coded non-coherent communication", 2021
- Link: https://ar5iv.arxiv.org/html/2102.10719   - Type: paper   - Read depth: full (survey 1 #1; re-read survey 2 #3)
#### What it does
Unknown phase by maximising p(y | theta, u_F = 0), the sum over information bits approximated by an SCL(L_e) pass up to
bit beta; coarse-fine theta search; SCL-8 + CRC second stage; pi ambiguity by flipping u_N. (128, 32) + CRC-6, QPSK, no
pilots, no CFO: within 0.3 dB of coherent, ~1.5 dB over 14-pilot PAT at FER 1e-4. beta = 113: L_e = 8 FER 1.0e-4 with
8807 visited nodes vs L_e = 1 3.5e-4 with 2439; beta = 47 worse than PAT; B phase blocks: search exponential in B.
#### What we took / could take
(a) Same Stage 2 + Stage 3 structure as ours (found independently). (b) The pi trick by flipping the last bit = our
PiCode. (c) F3: the list-marginalised metric -log sum_l exp(-PM_l) over L_e paths to rank grid cells.
#### Used in
- 2026-11-13: survey 1 finding 3.
- 2026-11-15: survey 2 F3; `expected_f3f5.md` predictions (predicted +0.002 ... +0.005, NO GO).
- 2026-11-15: `testing/lit_checks.py --check lmarg` (rank harness, 201 cells x 4 phases, 2000 packets per point),
  measured at the c = 3/4 checkpoint: 0.15 -4 dB P(true cell in top 4) 0.9744 -> 0.9989 with L_e = 8 (46 fixed / 0
  broken of 1875, p = 3e-14; L_e = 2: 40 / 2); 0.15 -3 dB no change (1.0); 1/10 -5 dB 0.9984 -> 1.0 (3 / 0). Gate passed
  (the prediction was too low); online flag and its MAC cost still to be tested.

### D2. M. Geiselhart, M. Gauger, F. Krieg, J. Clausius, S. ten Brink, "Phase-equivariant polar coded modulation", 2023
- Link: https://arxiv.org/html/2305.01972   - Type: paper   - Read depth: full (survey 1, #2)
#### What it does
With Gray QPSK a pi/2 rotation = a polar automorphism + a bit flip; 2 frozen "rotation bits" make the SC decoder
equivariant (metric(theta) = metric(theta + pi/2)); rotation read from 2 decoded bits; V&V phase first; list paths
start on different phases. K = 64 ... 192, N ~ 128 ... 256: +0.8 dB (QPSK), up to +2 dB (16-QAM) over PAT; cost 2 bits.
#### What we took / could take
Half the phase hypotheses per cell; one fast-path branch. First `equiv` (no interleaver, PiCode4: CRC at 4 rotations),
then the faithful `eqrb` (2 rotation bits u_{N-2}, u_{N-1}, one CRC test per path).
#### Used in
- 2026-11-13: `lit_checks.py equiv` (lit_checks_results.md): CONFIRMED, metric difference <= 1.2e-4 (float rounding)
  without the interleaver; 174-295 mean abs diff with it.
- 2026-11-13: run.py `*_eq` (`equiv`, BLIND_NOINT=1), expected_eq.md (64k): 2/5, 1/2 same BLER at -30 ... -40 % per
  core; 1/10, 0.15 BLER x1.6-17 and 4-11 undetected per 64k -> dropped there (DEAD_ENDS "Channel format").
- 2026-11-15: unit check `eqrb-chk` PASS (rotation read right in 100 %, 0 CRC passes at a wrong rotation).
- 2026-11-15: run.py `*_eqrb` (BLIND_NOINT=1 BLIND_ROTBITS=1, `bc.PiCodeRB`), expected_eqrb.md: 2/5 0.5 dB (400k) 848 ->
  716 errors (z = 3.3), per core 0.230 -> 0.161 M (-30 %); 1/2 2 dB (400k) 47 -> 58 (z = 1.1, within noise), -38.6 % per
  core; undetected equal. PASS at 2/5, 1/2 (adoption = user's call: drops the interleaver at those rates). 1/10, 0.15:
  KILL (undetected 2-5 per 64k, detected x1.6-4.5; e.g. 1/10 -5 dB 18 -> 65).

### D3. Choi, Lee, "Learning while transmitting: pilotless polar coded modulation", 2026
- Link: https://arxiv.org/html/2602.17979v1   - Type: paper   - Read depth: full (survey 2 #2; survey 1 #25 abstract + snippet)
#### What it does
QPSK coded-pilot segment: 4th-power VVPE phase, rotation from u_{N-2}, u_{N-1} ([1,0] = pi/2, [0,1] = pi, [1,1] =
3pi/2), re-encoded symbols as implicit pilots for a QAM segment; up to 1.5 dB over PAT (16-QAM, B = 3), ~1 dB (B = 1);
PAT equal or slightly better at R = 0.25 (K = 60); symmetry breaks under shortening / puncturing.
#### What we took / could take
Confirmation that `eqrb` is the published construction, and that its weaker result at low rate matches our 1/10, 0.15
failure. Our N = 2048 fills 1024 QPSK symbols exactly (no rate matching), so the fragility does not apply.
#### Used in
- 2026-11-15: survey 2 F4 (no change to the eqrb test plan); expected_eqrb.md results 2026-11-15 consistent.

### D4. "Hybrid polar encoding with applications in non-coherent channels", 2023
- Link: https://arxiv.org/pdf/2308.08201   - Type: paper   - Read depth: snippet (survey 1, #26)
#### What it does
Joint estimation + decoding, L = 16, CRC-16, block fading; approaches perfect CSI at high SNR.
#### What we took / could take
Nothing. Authors not recorded in survey 1 (snippet only).
#### Used in
- none.

### D5. P. Giard, A. Balatsoukas-Stimming, A. Burg, "Blind detection of polar codes", SiPS 2017
- Link: https://ar5iv.arxiv.org/html/1705.02111   - Type: paper   - Read depth: full (ar5iv; survey 1, #3)
#### What it does
Detection metric from rate-0 / REP / SPC nodes, rate-1 ignored; (512, 80) incl. CRC-16, BPSK: P_miss 1e-5 at P_fa 1e-3
(3 dB, SC); CA-SCL-8 ROC worse than SC (list decoding makes non-codewords decodable).
#### What we took / could take
(a) Frozen-only cell ranking (tested, no gain). (b) The explanation why the raw PM cannot replace rho (our 1046 / 1046
noise-only passes accepted by PM agree with "SCL ROC worse than SC").
#### Used in
- 2026-11-13: `lit_checks.py rank` (lit_checks_results.md): P(rank <= 4) at 0.15 -4 dB 0.9725 (total) / 0.9735
  (frozen-only) / 0.973 (no SPC); same at 0.15 -3 and 1/10 -5 dB -> dropped (DEAD_ENDS "Frozen-bit-only cell ranking";
  would change at higher code rates).

### D6. P. Giard, A. Balatsoukas-Stimming, A. Burg (same group), "On the tradeoff between accuracy and complexity in blind detection of polar codes", ISTC 2018
- Link: https://ar5iv.arxiv.org/html/1807.00655   - Type: paper   - Read depth: full (survey 1, #4); author list as "same group" in survey 1
#### What it does
Fast-SSC detection metric after t nodes; prune M = 44 candidates to B for SCL; N = 256, K = 24 + CRC-16: 40 / 44
dismissed at MDR 1e-2 without SPC updates; SPC updates hurt at high BLER.
#### What we took / could take
The "no SPC" ranking variant (tested with D5); partial-decode pruning = our checkpoints.
#### Used in
- 2026-11-13: as D5 (no-SPC column), dropped.

### D7. C. Condo, S. A. Hashemi, W. J. Gross, "Blind detection with polar codes", 2017
- Link: https://ar5iv.arxiv.org/html/1705.01864   - Type: paper   - Read depth: full (survey 1, #5)
#### What it does
PDCCH: 44 SC decodes ranked by PM, best C2 (plus low-PM ones) to SCL; RNTI in frozen bits; early stop when all paths
mismatch; FAR < 1e-3 (sequential RNTIs), ~1e-4 bound (random, 1e6 trials); 4 us budget with 22 SC + C2 SCL decoders at
800 MHz.
#### What we took / could take
Confirms our two-phase Stage 2 -> Stage 3 structure; the 1e6-trial noise-only FAR practice (our open item 4).
#### Used in
- 2026-11-13: survey 1 verdicts (hypothesis search, acceptance).

### D8. C. Condo et al., "Design and implementation of a polar codes blind detection scheme", 2018
- Link: https://arxiv.org/abs/1801.01820   - Type: paper   - Read depth: abstract (survey 1, #6)
#### What it does
Hardware (65 nm) for D7; "substantial" latency gain, no numbers in the abstract.
#### What we took / could take
Nothing.
#### Used in
- none.

### D9. Jalali, Ding, "A new algorithm for improved blind detection of polar coded PDCCH", 2019 / IEEE TWC 2020
- Link: https://arxiv.org/abs/1902.10280   - Type: paper   - Read depth: abstract (survey 2, #19)
#### What it does
LP relaxation of polar constraints in MIMO detection to remove wrong candidates before decoding.
#### What we took / could take
Nothing (MIMO detector).
#### Used in
- none.

### D10. Feng, Liu et al., "Polar-coding-assisted blind frame synchronization based on soft information of frozen bits", IEEE Commun. Lett. 27(10), 2023
- Link: https://dblp.dagstuhl.de/rec/journals/icl/FengLZXJ23.html   - Type: paper   - Read depth: snippet only (survey 2, #11)
#### What it does
Frame-timing metric ~ P(frozen sequence right), approximated and merged with SCL.
#### What we took / could take
Only if timing becomes unknown (open item).
#### Used in
- none.

### D11. Tu, Liu, Feng, Niu, "Blind recognition of polar codes using SCL decoding", 2026
- Link: https://arxiv.org/abs/2605.13331   - Type: paper   - Read depth: abstract (survey 2, #12)
#### What it does
Non-cooperative code recognition: per-position frozen / info hypotheses in an SCL; (32,16) ... (128,64), L = 64.
#### What we took / could take
Nothing.
#### Used in
- none.

### D12. Chen et al., "Noncoherent detection with polar codes", IEEE Access 2019
- Link: https://pure.bit.edu.cn/en/publications/noncoherent-detection-with-polar-codes/   - Type: paper   - Read depth: snippet (survey 2, #22)
#### What it does
BDPSK + SC; MSDSD + BP iterative; ~3 dB from coherent.
#### What we took / could take
Nothing (differential costs ~3 dB).
#### Used in
- none.

### D13. Li, Xu, Hu, "Channel estimation with systematic polar codes", 2018
- Link: https://arxiv.org/abs/1801.02860   - Type: paper   - Read depth: abstract (survey 2, #20)
#### What it does
Pilots chosen among systematic coded symbols (EPS / UEPS).
#### What we took / could take
Pilot family only (costs rate like pilots); not for the blind receiver.
#### Used in
- none.

### D14. Ghaddar, Kim, Milstein, Ma, Yi, "Joint channel estimation and coding over channels with memory using polar codes", IEEE Trans. Commun. 2021
- Link: https://www.bohrium.com/paper-details/joint-channel-estimation-and-coding-over-channels-with-memory-using-polar-codes/812018367450841088-2495   - Type: paper   - Read depth: snippet (page blocked)
#### What it does
List decoding marks reliably decoded bits; iterative estimation-decoding; pilots embedded in the codeword.
#### What we took / could take
Supports "use the list to pick reliable symbols" in pns.
#### Used in
- none directly.

---

## E. Code-aided synchronization and phase noise

### E1. C. Herzet, N. Noels, V. Lottici, et al., "Code-aided turbo synchronization", Proc. IEEE, 2007
- Link: https://www.researchgate.net/profile/Nele-Noels/publication/2998277_Code-Aided_Turbo_Synchronization/links/09e415077d6120c438000000/Code-Aided-Turbo-Synchronization.pdf   - Type: paper   - Read depth: snippet only (403)
#### What it does
EM / gradient / sum-product code-aided synchronization; turbo / LDPC, long frames.
#### What we took / could take
The classic baseline of the code-aided family; our `dd` (decision-directed CFO / phase from the re-encoded codeword) and
the "code-aided EM" bench are of this family.
#### Used in
- Root README A.17.3: "M&M + Newton + code-aided EM + search" BLER 4.4e-3 / 2.9e-3 / 1.2e-3: EM adds nothing to the
  CRC search.
- 2026-11-13: `dd` / `dd_win4` dropped (DEAD_ENDS: no packet fixed at 7 points; 2/5 0.5 dB 8 fixed / 51 broken).

### E2. H. Wymeersch, M. Moeneclaey, "Iterative code-aided ML phase estimation and phase ambiguity resolution", EURASIP J. Appl. Signal Process., 2005
- Link: https://portal.mardi4nfdi.de/wiki/Item:Q2570528   - Type: paper   - Read depth: abstract
#### What it does
EM with MAP-decoder soft information; ambiguity resolved without pilots (turbo codes).
#### What we took / could take
Pilot-free ambiguity resolution (we do it by PiCode / rotation bits instead).
#### Used in
- none.

### E3. Yue et al., "Code-aided CFOs and CPOs estimation in cooperative satellite communication", 2023
- Link: https://arxiv.org/html/2309.12828   - Type: paper   - Read depth: full (survey 1, #9)
#### What it does
Cross-entropy search over a 6-bit quantised CFO (120 candidates, 24 elites, 4-8 iterations) + EM with soft symbols from
BP LLRs; polar (1024, 512), BPSK, |f| <= 7.8e-3, Es/N0 ~ -3 dB, 2-4 satellites; 0.3-0.4 dB BER loss at 1e-4.
#### What we took / could take
Nothing; cross-entropy needs several full scoring rounds and lost 4 dB with 5-bit quantisation (survey 1: not
recommended for a 32-core MAC budget).
#### Used in
- none.

### E4. G. Colavolpe, A. Barbieri, G. Caire, "Algorithms for iterative decoding in the presence of strong phase noise", IEEE JSAC, 2005
- Link: https://www.tlc.unipr.it/colavolpe/papers/j26.pdf   - Type: paper   - Read depth: full (text reader; tables garbled)
#### What it does
Sum-product with canonical phase pdfs (Fourier, Tikhonov); Tikhonov = forward-backward "nonlinear Kalman smoother";
< 0.1 dB from coherent on DVB-S2 phase-noise models with 1 pilot per 20 symbols; needs pilots to bootstrap (EXIT).
#### What we took / could take
F1: our Stage 2 search is the bootstrap; after a failed CA-SCL-8 decode, smooth the phase of y conj(xbar) with the
list-weighted re-encoded symbols (Kalman / RTS, q = 2 pi linewidth x Ts), de-rotate, decode once more (`pns`).
#### Used in
- 2026-11-15: survey 2 F1; expected_pns.md predictions; run.py `*_pns` (PNS = iters 1, soft, max_calls 2).
- 2026-11-15: pns1a-e, pns3a-f, pns0a/b (expected_pns.md): never breaks a packet (0 broken in 1200+ discordant pairs),
  0 wrong fixes. pn 1e-4: 2/5 0.5 dB 5358 -> 4400 (-18 %), 1/2 2 dB 3788 -> 2933 (-23 %), 0.15 -3.5 dB 172 -> 155
  (-10 %), 1/10 -5 dB 35 -> 33; pn 3e-4: -9 ... -22 %; MACs per core down 1-18 % under phase noise; AWGN 0.15 -4 dB 247 ->
  241, AWGN 2/5 0.5 dB 140 -> 136 at +7.1 % per core. Prediction (x4-15 at 2/5) MISS on size. Status: safe small win,
  candidate; does not close the gap to the DVB-RCS2 tracking receiver.

### E5. Isikman, Mehrpouyan, Graell i Amat, "Phase noise estimation for uncoded / coded SISO and MIMO systems", 2012
- Link: https://arxiv.org/abs/1210.6267   - Type: paper   - Read depth: abstract (survey 2, #7)
#### What it does
EM code-aided sync with a soft-decision EKF / Kalman smoother; close to perfect phase knowledge at low-medium SNR (LDPC).
#### What we took / could take
The Kalman / RTS form of the pns smoother (instead of a window).
#### Used in
- 2026-11-15: pns design (expected_pns.md method: Kalman / RTS smoother).

### E6. Mei, Qu, "Log density spectrum based decoding of polar codes for channels with strong phase noise", 2026
- Link: https://arxiv.org/html/2610.16363   - Type: paper   - Read depth: full (text + refs; survey 2, #1)
#### What it does
SC recursion on 2-D Fourier spectra of log-densities over phase (LDSR); BPSK, Wiener sigma_phi 1.9 / 7.5 / 30 deg per
symbol, N = 128, 512; removes SC / SDD-EKS error floors under strong noise, worse under weak noise; cost
N(56 log2 N - 54) + 54 real mults (~1.15 M at N = 2048 [derived]); no numbers in the text.
#### What we took / could take
Its SDD-EKS baseline (pilot-free Kalman smoother) supports pns. LDSR parked; revisit only if pns fails at 3e-4.
#### Used in
- 2026-11-15: survey 2 F1 / F6.

### E7. Shayovitz, Raphaeli, "Multiple hypotheses iterative decoding of LDPC in the presence of strong phase noise", 2012
- Link: https://arxiv.org/abs/1210.5198   - Type: paper   - Read depth: abstract (survey 2, #18)
#### What it does
Phase-hypothesis mixtures in BP with mixture reduction.
#### What we took / could take
Nothing.
#### Used in
- none.

### E8. Beijing Institute of Technology, "Polar-code-assisted carrier synchronization method at low SNR", CN 110519200 B (2019/2020)
- Link: https://patents.google.com/patent/CN110519200B/en   - Type: patent   - Read depth: full description (title as paraphrased in survey 2)
#### What it does
EM loop: compensate -> BP decode -> soft symbols -> arg-based f and phase; (2048, 1024) BPSK AWGN: reliable f range
+-1.5e-4 cycles/symbol, phase +-0.4 pi; uncorrected 1.2e-4 costs 0.5 dB; closer to the MCRB than Fitz and V&V.
#### What we took / could take
The reason code-aided EM cannot replace the grid: pull-in 150x smaller than our |f| <= 0.03; our grid already covers it.
#### Used in
- 2026-11-15: survey 2 F6; consistent with the `dd` dead end (DEAD_ENDS).

### E9. Wu, Wang, Chen, Wang, "Carrier synchronization frequency offset estimation for aerospace TT&C" (PCAFOE), J. Telemetry, Tracking and Command 46(6), 2025
- Link: https://castjournals.cast.org.cn/joweb/ycyk/EN/PDF/10.12347/j.ycyk.20250628001   - Type: paper   - Read depth: full (text reader)
#### What it does
EM-style ML with BP posteriors; (2048, 1024) BPSK, Eb/N0 0-5 dB, |f| <= 2e-4; closer to the MCRB than Fitz (plots only).
#### What we took / could take
As E8: dead-end reason for EM / dd at our CFO range.
#### Used in
- 2026-11-15: survey 2 F6.

### E10. A. Barbieri, G. Colavolpe, G. Caire, 2007 (phase noise + frequency offset; unipr "j31.pdf")
- Link: not recorded (survey 2: "j31.pdf not parseable"; presumably https://www.tlc.unipr.it/colavolpe/papers/j31.pdf, not verified)   - Type: paper   - Read depth: not read
#### What it does
Not read. Title not recorded in our lit files.
#### What we took / could take
Nothing.
#### Used in
- none.

---

## F. Acceptance, undetected errors, false alarms

### F1. M. C. Coskun, G. Liva, J. Ostman, G. Durisi, "Low-complexity joint channel estimation and list decoding of short codes", 2019
- Link: https://arxiv.org/abs/1901.05409   - Type: paper   - Read depth: abstract (survey 1, #10)
#### What it does
A few pilots for a first estimate, OSD list, final choice by a non-coherent metric; up to 1.2 dB over PAT (block fading).
#### What we took / could take
Same idea as our rho re-encoding check (found independently before the survey).
#### Used in
- (project, root README A.16-A.17.4) rho re-encoding check `blind_fast.reencode_rho`, RHO_N: removes 100 % of wrong CRC
  passes (68 / 68 at 1/10 -5 dB), 0 right packets rejected.

### F2. P. Yuan, K. R. Duffy, M. Medard, "Near-optimal generalized decoding of polar-like codes", 2024
- Link: https://arxiv.org/html/2402.05004   - Type: paper   - Read depth: full (survey 1 #11; re-read survey 2 #4)
#### What it does
Accept only if P(c | y) / sum over the codebook >= 2^{NT}/(1 + 2^{NT}) (Forney); codebook sum from the list plus
2^{-|F(i:N)|} Q(a^i | y) per untaken branch; MDR <= eps (0.1, 0.005), (64, 42) dRM vs 5G polar + CRC-6/11, L = 4/8.
#### What we took / could take
(a) Survey 1 finding 5 (P_list / Forney score next to rho) - later deprioritised because of F5 (Sauter 2025). (b) The
argument that at our low rates the list-1 codebook probability equals our PM, so F3 needs L_e > 1.
#### Used in
- 2026-11-15: survey 2 F3 argument.

### F3. P. Yuan, K. R. Duffy, M. Medard, "Soft-output successive cancellation list decoding", IEEE Trans. Inf. Theory, 2025
- Link: https://arxiv.org/abs/2412.03623   - Type: paper   - Read depth: abstract (survey 1, #12)
#### What it does
Codebook-probability estimate for SC-type decoders; blockwise / bitwise soft output.
#### What we took / could take
Soft output for EM / Forney, if ever needed.
#### Used in
- none.

### F4. Feng, P. Yuan, K. R. Duffy, M. Medard, "Improving the decoding performance of CA-polar codes", 2025
- Link: https://arxiv.org/html/2512.10223v1   - Type: paper   - Read depth: full (survey 1, #13)
#### What it does
SO for CA-polar; erase when SO < 1 - eps; outer GRAND / GCD on CA-SCL failure; +0.2 dB (non-systematic), +0.2-1 dB
(systematic); UER below the target line.
#### What we took / could take
Nothing yet.
#### Used in
- none.

### F5. Sauter, Kislal, Durisi, Liva, Matuz, Strom, "Undetected error probability in the short blocklength regime", IEEE Trans. Commun. 2025
- Link: https://arxiv.org/html/2503.02782   - Type: paper   - Read depth: full (survey 2, #5)
#### What it does
CA-polar, SCL L = 8, n = 64-256, R = 1/2: on biAWGN Forney's threshold test beats CRC detection (0.5-0.95 dB); on a
phase channel with a 10-pilot ML estimate (mismatched) CRC-based detection "largely outperforms" the threshold test
(threshold better only at n = 64).
#### What we took / could take
Keep CRC + rho (not a likelihood threshold) under phase error; F2: a segment-wise non-coherent rho (`rhos`, S = 32 / 64
/ 128) insensitive to phase drift.
#### Used in
- 2026-11-15: survey 2 F2; expected_pns.md (rhos part); run.py `*_rhosl` (RHOS_LOG, log-only, decisions unchanged).
- 2026-11-15: rhos log-only arms identical to base in every pns run (expected_pns.md); the offline calibration of
  `rhos_k` and the `*_rhos` receivers are still a TODO in run.py.

### F6. King, Yao, Ryan, Wesel, "Design, performance, and complexity of CRC-aided list decoding of convolutional and polar codes for short messages", 2023
- Link: https://ar5iv.labs.arxiv.org/html/2302.07513   - Type: paper   - Read depth: full (survey 1, #19)
#### What it does
(512, 43), CRC-11 / CRC-24, L up to 1024: CRC-24 0 undetected errors up to L = 1024; CRC-11 > 80 % of failures undetected
at high SNR; L ~ 2^m conjecture.
#### What we took / could take
Why CRC-16 alone is not enough for a search with many decodes (budget ~ decodes x 8 paths x 2 patterns x 2^-16), hence
rho; supports the 1e6-trial noise-only test (open item).
#### Used in
- 2026-11-13: survey 1 section 4.3.

### F7. "Learning to mitigate the false alarm rate in polar code blind detection", IEEE Wireless Commun. Lett., 2019
- Link: https://unpaywall.org/10.1109%2FLWC.2019.2937299   - Type: paper   - Read depth: snippet (survey 2, #23)
#### What it does
NN classifier after a CRC pass (PDCCH, short CRC).
#### What we took / could take
Nothing; our false-pass NN is a dead end (DEAD_ENDS "Lag-1 residual phase, false-pass NN"). Authors not recorded.
#### Used in
- none.

---

## G. Early termination, gates, search theory

### G1. Strodthoff et al., "Enhanced machine learning techniques for early HARQ feedback prediction in 5G", IEEE JSAC 2019
- Link: https://ar5iv.arxiv.org/html/1807.10495   - Type: paper   - Read depth: full (survey 1, #15)
#### What it does
Failure prediction from decoder reliability (VNR of LDPC iterations 0-5), LR / RF / isolation forest / SAE, threshold
moving; LDPC BG2 R = 1/5, 360 bits, TDL-C: AUC-PR 0.902 (threshold) vs 0.905 (LR) vs 0.908 (SAE) at 4 dB.
#### What we took / could take
Confirms our "logistic = MLP" finding and the feature family of our retry gate (13 failed-decode features).
#### Used in
- 2026-11-13: retry gate (logistic, expected_nnb.md): "1 %" setting 0 fixed / 8 broken pooled (p = 0.008), "0.1 %"
  0 / 3 broken, per core only -4.5 ... -9 % at the hardest points -> dropped (DEAD_ENDS "NN ideas").

### G2. G. Sarkis, J. Jiang, J. Lin, Y. Yang (Qualcomm), "Early-termination techniques for polar list decoders", US 10615825 B2, 2020
- Link: https://patents.google.com/patent/US10615825B2/en   - Type: patent   - Read depth: description (first 100k chars)
#### What it does
Stop a polar list decode when the normalised spread of the list PMs (max - min, or std / percentiles) falls below a
threshold after a minimum number of bits (PDCCH blind decoding); example spread 1.75 vs threshold 2.0; no BLER numbers.
#### What we took / could take
Survey 1 finding 4: an in-decode PM-spread abort of failing main CA-SCL-8 decodes (decodes ~25 % of MACs at 0.15
-4 dB). Not tested; F5 (G3) was chosen instead.
#### Used in
- none.

### G3. J. Lin, G. Sarkis, Y. Yang (Qualcomm), "Frozen bits based pruning and early termination for polar decoding", US 10742238 B2, 2020
- Link: https://patents.google.com/patent/US10742238B2/en   - Type: patent   - Read depth: first 100k of 289k characters
#### What it does
Per-path frozen-bit-only path metric, normalised (scalar array, summed LLR magnitudes, or number of frozen bits seen);
prune a path above a threshold; terminate when all paths are pruned; only reliable frozen positions; no BLER / FAR
numbers.
#### What we took / could take
F5: frozen-bit abort inside the CA-SCL-8 decodes; offline ROC first (right vs wrong-candidate decodes at 1/4, 1/2, 3/4 of
the frozen set), go online only if >= 5 % total saving at the 1e-4 right-decode-loss point.
#### Used in
- 2026-11-15: expected_f3f5.md predictions (0.15 -4 dB total -5 ... -10 %); run.py `fz_diag` log-only diagnostic
  (`fz_*.npz`, decisions and MACs unchanged), `testing/fz_profile.py`; diagnostic running, no result yet.

### G4. Yao, Ma, "Low-complexity PSCL decoding of polar codes", 2024
- Link: https://arxiv.org/abs/2405.13255   - Type: paper   - Read depth: abstract (survey 1, #17)
#### What it does
Two SNR-dependent thresholds (path reliability; probability that the correct path is in the list); savings grow with SNR.
#### What we took / could take
Nothing yet.
#### Used in
- none.

### G5. Pillet, Bioglio, Condo, "On list decoding of 5G-NR polar codes", WCNC 2020
- Link: https://arxiv.org/abs/1907.00784   - Type: paper   - Read depth: abstract (survey 1, #18)
#### What it does
Path pruning and early termination with a distributed CRC (5G DCI); trade-off curves only.
#### What we took / could take
Not applicable without changing the CRC placement (a code change).
#### Used in
- none.

### G6. Z. Karnin, T. Koren, O. Somekh, "Almost optimal exploration in multi-armed bandits", ICML 2013
- Link: https://labs.yahoo.com/mobstor/publication_attachments/Almost%20Optimal%20Exploration%20in%20Multi-Armed%20Bandits.pdf   - Type: paper   - Read depth: snippet (via citing papers)
#### What it does
Sequential halving: fixed-budget best-arm identification, near-optimal for equal variances.
#### What we took / could take
Theory behind our checkpoint scheme (cut the cell population at checkpoints along the code).
#### Used in
- 2026-11-13: survey 1 section 4.1 (supports the existing checkpoints; nothing new to borrow).

### G7. arXiv 2306.07549 (variance-aware best-arm identification; title not recorded in survey 1)
- Link: https://arxiv.org/pdf/2306.07549   - Type: paper   - Read depth: snippet (cited for G6's optimality and the variance-aware variants)
#### What it does
Variance-aware variants of sequential halving.
#### What we took / could take
Hint that cells near the true CFO (partially coherent, larger metric variance) deserve a looser cut; the R = 1/10
"neighbours join" rule already does something similar.
#### Used in
- none.
