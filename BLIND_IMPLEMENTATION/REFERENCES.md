# References: every source cited in the blind CFO project

One registry of every paper, standard, patent and application note cited in the project (built 2026-11-16 from
`testing/results/lit_blind_cfo.md` (survey 1), `lit_polar_sync.md` (survey 2), `lit_dvbrcs2.md`,
`lit_checks_results.md`, `expected_*.md`, `DEAD_ENDS.md`, `01`-`08`, `est3/README.md` and the root `README.md`).
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
| C1 | ETSI EN 301 545-2 V1.3.1 (DVB-RCS2 lower layers) | standard | ID 13 burst layout scaled to 1024 data (est4 RCS2-13) | competitor |
| C2 | ETSI TR 101 545-4 V1.1.1 (DVB-RCS2 guidelines) | standard | CFO range 0.5-3 % of Rs; operating points; "no TC-LM sync algorithm" | reference only |
| C3 | ETSI TR 101 545-4 V1.2.1 (2026) | standard | ToC check only | reference only |
| C4 | Griebel, Wasenmuller, Wehn 2021, FFT interpolation for DVB-RCS2 | paper | DA-KS R&B + parabolic interpolation (est4 RCS2-13, RCS2 pre/post) | competitor |
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
- 2026-11-16: `testing/lit_checks.py` FastSCL (F3 `lmarg` harness) uses its node splits.

### A6. G. He, J.-C. Belfiore, I. Land, G. Yang, Y. Ge, R. Zhang, W. Tong, "beta-expansion: a theoretical framework for fast and recursive construction of polar codes", 2017
- Link: https://arxiv.org/abs/1704.05709   - Type: paper   - Read depth: bib (abstract; author list as on the arXiv PDF)
#### What it does
Polarization-weight (PW) construction; beta converges to ~2^(1/4) for AWGN; the basis of the 5G NR sequence.
#### What we took / could take
The frozen set: PW reliability order with beta = 2^(1/4) (`polar.py` header).
#### Used in
- (project base) `polar.py` construction for all rates; `eqrb` takes the K + 2 most reliable positions of the same order
  (expected_eqrb.md, 2026-11-15).

### A7. 3GPP TS 38.212, "NR; Multiplexing and channel coding" (ETSI TS 138 212)
- Link: https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.11.00_60/ts_138212v171100p.pdf   - Type: standard
- Read depth: bib (version list only; the polynomial table was not re-read for this registry)
#### What it does
5G NR CRC polynomials (clause 5.1), polar coding for control channels (5.3.1), rate matching.
#### What we took / could take
CRC polynomials (`polar.CRC_POLYS`; CRC-16 in the blind study). Not taken: rate matching by shortening (PiCode would
need 4 phase branches, 08_parameters_results.md "PiCode's assumption"); distributed CRC (G5) would be a code change.
#### Used in
- (project base) `polar.py` CRC_POLYS; CRC-16 in every blind / pilot receiver.

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
- 2026-11-16: est4 `RCS2-13` (R&B FFT over all known symbols + parabolic interpolation) and `RCS2 pre/post` (4th-power
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
- 2026-11-16: est4 `pre128 M&M` (C3) - expected_est4.md: 207 errors / 64k at 1/10 -5 dB (pn 0) vs blind 14; among the
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

### C1. ETSI EN 301 545-2 V1.3.1 (2020-07), DVB-RCS2 Part 2: Lower layers for satellite standard
- Link: https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.03.01_60/en_30154502v010301p.pdf   - Type: standard
- Read depth: full text of cl. 6.4.6, 7.3.6-7.3.9 and Annex A Table A-1 (via a text reader; UW hex values not legible)
#### What it does
TC-LM burst construction: preamble + 1-symbol pilots every P symbols + postamble; reference waveforms (ID 13: QPSK 1/3,
1616 symbols, pre 32, post 31, P = 20, 77 pilots); RRC roll-off 0.20; pilots on only for QPSK 1/3 and 1/2.
#### What we took / could take
The main DVB-RCS2 competitor layout: ID 13 scaled to 1024 data symbols = preamble 32 | 53 x (19 data + 1 pilot) |
17 data | postamble 31, 116 known symbols (0.47 dB). Derived fact: 1-symbol pilots every 20 resolve only |f| < 0.025,
below our 0.03, so DA-KS over all known symbols is needed.
#### Used in
- 2026-11-15: `lit_dvbrcs2.md` competitors C1 (RCS2-PL), C2 (pre/post), C3 (preamble-only).
- 2026-11-16: est4 `RCS2-13` / `RCS2-13 track` (expected_est4.md, 480k per point): with energy charged blind is
  equal or better in BLER at all 4 rates (0.15 1e-3: blind -3.60 vs -3.45 dB; 2/5 1e-3: 0.61 vs 1.10 dB; 1/2: 1.79 vs
  2.33 dB) at 5-12x the MACs per core (RCS2-13 0.034-0.045 M); RCS2-13 has a window-miss floor (881 / 480k at 1/10
  -5 dB) from the 1/(2P) alias. Under Wiener phase noise 1e-4 the tracking arm beats blind at 0.15 and 2/5
  (94 vs 144, 1967 vs 5312 per 64k, pilot energy not charged). Also `08_parameters_results.md` 8.2a, `07` 7.5b,
  `presentation/bler_fair_R*.png`.

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

### C3. ETSI TR 101 545-4 V1.2.1 (2026)
- Link: https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf   - Type: standard   - Read depth: table of contents only
#### What it does
Revision; same clause titles, no TC-LM synchronizer clause in the ToC.
#### What we took / could take
Confirms C2's "no algorithm" finding (ToC only).
#### Used in
- 2026-11-15: lit_dvbrcs2.md.

### C4. P. Griebel, M. Wasenmuller, N. Wehn, "Interpolation techniques for FFT-based carrier synchronization in DVB-RCS2", Adv. Radio Sci. 19, 59-70, 2021
- Link: https://ars.copernicus.org/articles/19/59/2021/   - Type: paper   - Read depth: full HTML (tables 1-2 are images, not read)
#### What it does
DA-KS (R&B over all known symbols, zeros at data), DA-PL (pilots only, |f| < 1/(2P)), NDA 4th power; parabolic /
energy interpolation cuts the FFT 8192 -> 2048 with no FER loss; constant phase per burst; CFO up to 1.5 % of Rs (3 %
needs NDA); FPGA: interpolation ~2000 FF, 1000 LUT, 13 DSP, throughput 22.9 -> 90.9 Msym/s.
#### What we took / could take
The faithful DVB-RCS2 estimator chain (Eqs. 2-7, 11-17) for est4 RCS2-13 and RCS2 pre/post. Confirms our 4th-power +
parabolic fast path is the deployed NDA baseline.
#### Used in
- 2026-11-16: est4 `RCS2-13` (DA-KS + parabolic) and `RCS2 pre/post` (NDA, 4-fold ambiguity from 32 known symbols) -
  expected_est4.md; RCS2 pre/post fails at low SNR (BLER 0.5-0.9 below 0 dB), crosses 1e-3 at 1/2 only at 2.77 dB.

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
- 2026-11-16: est4 `split64 ML` / `split64 interp` (expected_est4.md): lobe errors at low SNR (wrong lobe in 54-61 % of
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

### C13. DVB Project, DVB-RCS2 page
- Link: https://dvb.org/?p=8033   - Type: app note   - Read depth: snippet
#### What it does
States the known-symbol balance is chosen so that sync sensitivity matches decoding sensitivity.
#### What we took / could take
Context only.
#### Used in
- 2026-11-15: lit_dvbrcs2.md.

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

---

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
- 2026-11-16: `testing/lit_checks.py --check lmarg` (rank harness, 201 cells x 4 phases, 2000 packets per point),
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
- 2026-11-16: run.py `*_eqrb` (BLIND_NOINT=1 BLIND_ROTBITS=1, `bc.PiCodeRB`), expected_eqrb.md: 2/5 0.5 dB (400k) 848 ->
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
- 2026-11-15: survey 2 F4 (no change to the eqrb test plan); expected_eqrb.md results 2026-11-16 consistent.

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
- 2026-11-16: pns1a-e, pns3a-f, pns0a/b (expected_pns.md): never breaks a packet (0 broken in 1200+ discordant pairs),
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
- 2026-11-16: rhos log-only arms identical to base in every pns run (expected_pns.md); the offline calibration of
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
- 2026-11-16: expected_f3f5.md predictions (0.15 -4 dB total -5 ... -10 %); run.py `fz_diag` log-only diagnostic
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
