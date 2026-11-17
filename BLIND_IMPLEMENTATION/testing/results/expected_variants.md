# Faithful variants of the est5 competitors: data cards and predictions (written 2026-11-15, BEFORE any run)

Approved by the user on 2026-11-15. Sources: `lit_card_sat.md`, `lit_card_space.md`, `lit_card_terr.md`, `lit_rates.md`,
`competitors.md`, `expected_est5.md`. Code: est4/common.py, est4/estimators.py, est4/run_bler.py (est4 harness: pilots
outside the packet, energy charged, the same CA-SCL-8 + CRC-16 + RHO_N re-encoding check, metric-ordered CRC search).
**No variant has been simulated yet. Every number in the prediction table is a prediction (genie + pilot energy +
estimated loss), for planning only. Do not plot or quote it as a result.**

Every existing source stays bit-identical:
- the new layouts are appended to `C.LAYOUTS`, so the noise streams keep their IDs;
- `KMAX_ALL` (the est5 extended phase-noise path) is unchanged; the longer variants (mil110f, wifi320) extend it once
  more from a separate stream `[44] + key`;
- est4 / est5 McNemar references are unchanged (`mcnemar_src` = `mcnemar_ref` except for a variant whose parent is in
  the job).

Labels: [std] standard, [patent], [vendor], [paper], [derived] = arithmetic, **[inferred]** = not stated by a source.

## 1. Data cards

Common to all: single carrier, QPSK data, 1024 data symbols carrying the whole polar codeword, Nk known symbols outside
the packet (energy charged: 10 log10((1024 + Nk) / 1024)), genie timing, uniform CFO |f| <= 0.03, AWGN (pn 0).
"Overhead %" = Nk / 1024. MACs per core = the standard scheduled model (`E.pilot_macs`, par) at the predicted required
SNR, from the hypothesis counts of the code (`hyp_matrix`) and an assumed first-decode failure rate p_f. These MACs are
estimates.

### V1 "hyb3-pre48": Advantech hybrid DA + NDA (parent: hyb3)
- **Real system.** US 7590199 B2, "Hybrid frequency offset estimator" (Alagha; Advantech Advanced Microwave
  Technologies) [patent](https://patents.google.com/patent/US7590199), with US 7593490 B2, "Joint synchronizer and
  decoder" (Alagha, Erup) [patent](https://patents.google.com/patent/US7593490). Link: DVB-RCS (gen 1) MF-TDMA return,
  Ku / Ka.
- **Who uses it.** Advantech is the patent assignee. Neither patent names a product. Advantech DVB-RCS / S2 hubs and
  terminals were delivered to the US DoD (2010, trade press). That those products run this estimator is **[inferred],
  not found** in any source.
- **Real layout and estimator vs ours.**
  - Real: a 48-symbol contiguous preamble + 440 payload symbols (488, QPSK, rate-1/2 turbo, 64 kBd, +-2.8 % of Rs)
    [patent].
  - Ours: `pre48` = 48 contiguous known symbols + 1024 data.
  - Real estimator: a DA spectrum of the 48 known symbols and an NDA (phase x 4) spectrum, log |.|^2, weighted and
    summed, then 3 candidates by peak removal + parabolic interpolation.
  - Ours: `hyb3` unchanged (log |FFT(z)| + log |FFT(r^4)|(4 nu), 3 local maxima in +-0.03, parabolic), on the new
    layout. Window M from `crb_nda4` over the burst (`C.NDA4_WIN`): the 4th-power term sets the curvature of the
    summed spectrum. No lobes (one field).
  - **Real selector: the largest mean |LLR| after 1-3 of ~10 turbo iterations per candidate**, plus decision-aided
    phase tracking (50-symbol window) [patent US 7593490]. Ours: the metric-ordered CRC search + rho over the 3
    candidates, i.e. full CA-SCL decodes, CRC-16 and re-encoding. **Ours is stronger.**
- **Nk = 48, 0.20 dB, 4.7 %.**
- **MACs per core.** ~0.052 M (2/5) / 0.054 M (1/2) at the required SNR. The estimator alone is 476 k total = 0.015 M
  per core (two 8192-point FFTs).
- **Fidelity: STRONGER** (CRC + rho selector instead of mean |LLR|, 8192 FFT, genie timing; constant LS phase instead
  of DD tracking is equal in AWGN).
- **V1w "hyb3-pre48 wide"** (added 2026-11-15 after the verifier review; parent hyb3-pre48).
  - The same estimator and candidates, with window M = max(crb_nda4 window, crb_known(pre48) window) (`C.WIN_MAX`).
  - At 1/10 and 0.15 the 4th-power term is mostly noise (peak SNR -4.4 dB at -4 dB), so f_hat has about the
    48-symbol DA precision (std ~1.9e-3). V1's 4th-power window (M = 11) then misses it, and V1w's DA window
    (M = 145 / 129 / 77 / 65 at -5 / -4 / 0.5 / 2 dB) covers it.
  - It shares f_hat and the pre-MF correction with V1 (fcache).
  - The cost is ~260-520 in-range hypotheses per failing packet (3 candidates with near-duplicates dropped).
  - MACs per core ~0.49 / 0.45 / 0.14 / 0.15 M. Fidelity STRONGER (a search the patent does not have).

### V2a "ViaSat 7653150" and V2b "ViaSat top32 X4phase" (parent: ViaSat UW)
- **Real system.**
  - US 7653150 B2, "Star receiver burst processing" (Thesling, Vanderaar; Efficient Channel Coding, assigned to
    Viasat; expired) [patent](https://patents.google.com/patent/US7653150B2/en).
  - US 8243859 B2, "Joint frequency and unique word detection" (Mo, Thesling; Viasat)
    [patent](https://patents.google.com/patent/US8243859).
  - Link: GEO star return-link MF-TDMA bursts; 8243859 also covers a user terminal in a mesh network (claims).
- **Who uses it.** ECC / Viasat: ECC supplied modem chips for the IPSTAR system (trade press, ECC acquisition 2005).
  US 8243859 covers gateways and mesh terminals. That the IPSTAR chips or any named Viasat product run these two
  algorithms is **[inferred], not found** (no product named in either patent).
- **Real layout.** 512 QPSK symbols, no preamble, a 16-symbol midamble UW [patent]. Ours: `viasat16` (512 data + 16 UW
  + 512 data), unchanged.
- **Real estimator.**
  - US 7653150: 4th power over the burst (LUT), 2x zero padding (512 -> 1024-point FFT), the **single** largest bin s,
    frequency = the weighted average of bins s-1, s, s+1, / 4.
  - **Phase theta' / 4 from the 4th-power bins; the UW only resolves the pi/2 quadrant** (and the timing, +-8
    symbols).
- **Ours.**
  - V2a, `nda4pk`: FFT of r^4 with the patent's 2x padding (4096 for K = 1040), single peak in |4f| <= 0.12 + 1 bin,
    |X|-weighted 3-bin mean, / 4.
  - Phase model `x4` (both V2a and V2b): theta = arg(-sum_n (r[n] e^{-j 2 pi fh (n + D)})^4) / 4, i.e. the 4th-power
    bin at 4 fh referred to our time origin (QPSK s^4 = -1). The quadrant is the one maximising Re(UW correlation),
    the amplitude is the UW projection.
  - V2b: the existing top-32 + UW joint pick (`nda4uw`, US 8243859) with the same `x4` phase. It shares f_hat and the
    pre-MF correction with ViaSat UW (fcache), so the two differ only in phase.
  - Window M from `crb_nda4` (as ViaSat UW); no lobes.
  - The `x4` phase is charged 12 K + 4 Nk + 44 MACs per hypothesis, as computed. The patent reads it off its 3 FFT bins
    at ~0 MACs.
  - Verifier note: the charge is ~2 % pessimistic in MACs per core (8 K would do: r^4 already exists, so a twiddle +
    complex multiply on it, vs the 12 K charged). Kept as computed.
- **Nk = 16, 0.07 dB, 1.6 %.**
- **MACs per core.** V2a ~0.039 / 0.041 M, V2b ~0.043 / 0.045 M (2/5 / 1/2).
- **Fidelity.**
  - V2a **STRONGER**: the CRC search around the single peak, genie timing, 3 % instead of 10 % CFO range.
  - V2b **STRONGER**: a merge of both patents plus the CRC search.
  - Both are now equal to the real chain in phase (the parent ViaSat UW was WEAKER in phase: UW-only LS phase, std
    0.31 / 0.18 / 0.14 rad at -5 / 0 / +2 dB).

### V3a "DVB-S2 header90" and V3b "DVB-S2 SOF26" (parent: DVB-S2 style)
- **Real system.** ETSI EN 302 307-1 V1.4.1 (DVB-S2) cl. 5.5
  [std](https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf). Guidelines
  TR 102 376-1.
- **Who uses it.** Every DVB-S2 forward-link receiver (DTH, contribution, VSAT outbound). "Over 1.5 billion DVB
  receivers" is a count for all DVB standards together; a DVB-S2-only count was not found.
- **Real layout.**
  - PLHEADER = 90 symbols (SOF 26 + PLS code 64), pi/2-BPSK.
  - The first 36-symbol pilot block comes 16 slots = **1440 data symbols** after the header, so a 1024-symbol window
    after the header has **no pilot block** [std + derived].
  - In CCM all 90 header symbols are known (V3a). In ACM / VCM only the 26-symbol SOF is known before the PLS is
    decoded (V3b).
- **Ours.** `dvbh90` = 90 known + 1024 data; `sof26` = 26 known + 1024 data. Random QPSK instead of pi/2-BPSK (same
  energy; neutral for DA estimation).
- **Real estimator.** A multi-frame FLL + Luise-Reggiannini over ~1000 pilot blocks; gr-dvbs2rx uses M&M-type on the
  header, averaged over frames. There is no single-burst chain.
- **Ours (`mmml`, the parent's chain without the pilot block).**
  - M&M on the header (M = N/2), then ML (FFT of the zero-filled header) restricted to f_c +- 1/(2 Nh), then 2 Newton
    steps.
  - **CRC search: a range scan** (`C.SCAN`, fixed 2026-11-15 after the verifier review).
    - Offsets k STEP, |k| <= SCAN_K = 801, i.e. the whole +-0.03 from any f_hat.
    - A hypothesis is valid if |f_hat + off| <= 0.03 + STEP, so there are no holes and no duplicates. That gives 801-802
      valid hypotheses per packet at every SNR (n_hyp 1602 before the filter).
    - The search is metric-ordered as usual and charged through metric_evals / metric_rounds / extra_decodes.
    - The window M from the header CRB (51 / 324 steps at -4 dB) is kept for in_window and the json only.
  - **The first grid was wrong (an artefact of the 1/Nh lobe search).**
    - SOF26 at -4 / -5 dB: adjacent lobe windows overlapped (M 324 > 1/26 = 513 steps / 2) and ran past +-0.03.
      That gave 1637 / 1906 hypotheses, only ~803 distinct and in range.
    - Coverage of the range: SOF26 at 2/5 0.5 dB only 77 %; header90 61 % at -4 dB and 36 % at 0.5 dB.
  - The first decode almost always fails (CRB std > 1e-4), so every packet pays its metric search.
- **Nk.** V3a 90, 0.37 dB, 8.8 %; V3b 26, 0.11 dB, 2.5 %.
- **MACs per core** (scan grid). V3a ~0.70 / 0.75 / 0.88 / 0.89 M; V3b ~0.71 / 0.77 / 0.89 / 0.90 M (1/10, 0.15, 2/5,
  1/2). The old grid gave V3a 0.52 / 0.50 / 0.37 / 0.34 and V3b 1.57 / 1.35 / 0.90 / 0.78: duplicates inflated SOF26
  and holes deflated header90.
  - Both remain **above blind** (0.200 / 0.262 / 0.209 / 0.083), so the claim is unchanged: the CRC search is what
    pays for the missing pilot block.
- **Fidelity.**
  - **MIXED.** The layout is the real one (weaker than our C7, which adds a pilot block the standard does not have
    there), and the CFO range is harsher than the single-frame range.
  - The real receiver is locked by a multi-frame FLL before this frame (much stronger). Against a cold single frame,
    our M&M + ML + exhaustive CRC search is stronger than anything in the standard.

### V4 "MIL-110 full": MIL-STD-188-110C Appendix C (parent: MIL-110 HF)
- **Real system.**
  - MIL-STD-188-110C with Change Notice 1, Appendix C = STANAG 4539
    [std](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf);
    ITU-R F.763-5 Annex 6 [std](https://www.itu.int/dms_pubrec/itu-r/rec/f/R-REC-F.763-5-200501-P!!PDF-E.pdf).
  - Superseded by MIL-STD-188-110D (29 Dec 2017)
    [listing](https://everyspec.com/MIL-STD/MIL-STD-0100-0299/MIL-STD-188-110D_55856/).
- **Who uses it.**
  - L3Harris Falcon III RF-7800H-MP: 110C App D in the 2019 datasheet, 110D in 2022
    [vendor](https://l3harris.com/sites/default/files/2020-07/cs_tc_datsheet_rf-7800h-mp-wideband-hf-vhf-tactical-radio-system.pdf);
    50 000 Falcon III units by 2023.
  - Harris / Rockwell Collins App D modems shown interoperable.
  - That these radios run **App C** (STANAG 4539) is **[inferred]**: the datasheets cited name App D / 110D.
- **Real layout.** 287-symbol preamble (184 sync / Doppler + 103 = 72 rate / interleaver symbols + a 31-symbol
  mini-probe), then frames of 256 data + 31-symbol mini-probe. For 1024 data that is 287 + 4 x 31 = 411 known [std +
  derived]. Ours: `mil110f`, exactly that (the 287 as one field). The parent `mil110` omitted the 103.
- **Real estimator.** Preamble estimate at high SNR (tested at 30 dB), then probe / equaliser-driven tracking; no
  one-shot estimator published. Design CFO +-75 Hz at 2400 Bd = 0.031.
- **Ours.** `rb` = R-B over all 411 known (FFT 8192, parabolic) + CRC search over +-3 probe-period lobes (1/287),
  constant LS phase. Lobe misses are negligible: the 287-symbol block alone resolves the lobe.
- **Nk = 411, 1.47 dB, 40.1 %.**
- **MACs per core.** ~0.036 / 0.038 / 0.043 / 0.045 M.
- **Fidelity: STRONGER** (all-symbol R-B + CRC lobe search at low SNR, where the real chain is not specified) but now
  energy-faithful (parent: 0.33 dB lighter than the real waveform).

### V5 "CCSDS 131.2 real" (parent: CCSDS style)
- **Real system.**
  - CCSDS 131.2-B-2 (SCCC, Feb 2023) [std](https://public.ccsds.org/Pubs/131x2b2.pdf).
  - Reference receiver CCSDS 130.11-G-2 [std](https://public.ccsds.org/Pubs/130x11g2.pdf).
  - Link: high-rate Earth-observation payload downlink.
- **Who uses it.**
  - Ground: Safran Cortex HDR (SCCC decoding listed)
    [vendor](https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20HDR%20-%20Datasheet.pdf);
    Kongsberg HRDFEP (131.2-B-2; search snippet only).
  - Hardware validation: Tesat transmitter + Kongsberg Spacetec receiver. DSN / ESA stations as CCSDS operators.
  - Named 131.2 flight missions: not found.
- **Real layout.** 16 pilot symbols after every 540 data symbols, plus a 320-symbol header once per 133 760-symbol
  frame [std]. A 1024-data window holds 1.9 pilot fields (~30 known) and normally no frame marker [derived].
- **Ours.** `cc131` = 242 data, 16 pilots, 540 data, 16 pilots, 242 data: 2 fields 556 apart (one 540 + 16
  subsection), Nk = 32.
- **Real estimator.** A frame-rate 2nd-order FLL on the FFT of the 256-symbol frame marker (locked over many frames),
  per-field DA ML phase + linear interpolation, no decoder aid.
- **Ours.** `rb` = R-B over the 2 pilot fields + CRC search over +-17 lobes of 1/556 (`C.LOBE_N` = ceil(0.03 x 556) =
  17), range-filtered, constant LS phase.
  - 17 lobes = 4 sigma_env at -5 dB. sigma_env = the per-block noncoherent CRB of the lobe pick (two 16-symbol
    blocks) = 4.3 lobes at -5 dB and 3.8 at -4 dB.
  - So lobe misses beyond +-17 are <= 4e-5 at -5 dB and 4e-6 at -4 dB [derived]. The lobe pick itself is wrong in
    ~85 % of packets, and the search finds the lobe.
  - The cost: ~440-500 in-range hypotheses at the low points.
- **Nk = 32, 0.13 dB, 3.1 %.**
- **MACs per core.** ~0.41 / 0.39 / 0.32 / 0.29 M (**above blind**).
- **Fidelity: WEAKER in CFO** (the real FLL is locked before the data; one-shot acquisition over +-0.03 is our
  addition), **stronger in search** (CRC over 35 lobes, genie timing). Net: WEAKER than the deployed receiver, but the
  faithful single-burst information content of the 131.2 pilot density. The per-field phase + interpolation is not
  used (AWGN: constant phase).

### V6 "CCSDS 131.0 ASM" (parent: split64 ML)
- **Real system.** CCSDS 131.0-B-5 (TM sync and channel coding, Sept 2023) cl. 7.2.1.2, 9.3.4, Table 7-5
  [std](https://public.ccsds.org/Pubs/131x0b5.pdf); RF per CCSDS 401.0-B-32.
- **Who uses it.**
  - Essentially all CCSDS agency telemetry uses 131.0.
  - Ground: NASA DSN (810-005 Module 207 [std](https://deepspace.jpl.nasa.gov/dsndocs/810-005/207/207A.pdf)), ESA
    ESTRACK, Safran Cortex CRT (CCSDS LDPC / turbo; acquisition below Es/N0 -2 dB)
    [vendor](https://www.safran-group.com/sites/default/files/2022-10/Safran%20Data%20Systems%20-%20Base-bands%20units%20Cortex%20CRT%20-%20Datasheet.pdf).
  - Missions using the (2048,1024) AR4JA code specifically: not found.
- **Real layout.** The (2048,1024) rate-1/2 AR4JA LDPC block (exactly our N = 2048) with the 64-bit ASM
  034776C7272895B0 = 32 QPSK symbols before each codeblock. In a stream, the next block's ASM follows, so 32 + 32 known
  sit 1056 apart. No pilots.
- **Ours.** `asm32` = the same random 32-symbol marker before and after the 1024 data. Nk = 64 is charged (isolated
  burst). In a continuous stream an ASM is shared by two blocks, so 32 would be charged (0.13 dB).
- **Real estimator.** The ASM is for frame sync and phase-ambiguity resolution only. The carrier comes from a
  continuous Costas / QPSK loop, acquired over ~1 min with Doppler predicts. There is no per-block estimator.
- **Ours.** `ml` (the split64 chain: zero-filled FFT on the span, 3 candidates + 2 Newton each) + CRC search over
  **+-12** lobes of 1/1056 (range-filtered):
  - **Deviation from "like split64": its +-3 lobes are too few for 32 + 32.** sigma_env (per-block noncoherent CRB of
    the lobe pick) is 2.9 lobes at -5 dB, 2.6 at -4 dB and 1.5 at 0.5 dB [derived].
  - With +-3 lobes the true lobe would lie outside the search for **17 % of packets at -4 dB, 2 % at 2/5 0.5 dB and
    0.2 % even at 3 dB**: a pure lobe-count floor.
  - 12 = ceil(4 sigma_env) at -5 dB (the same rule gives cc131's 17). The same rule explains split64's 1/10 floor:
    with +-3 it misses 7.8e-4 at -5 dB; measured 1.5e-3 BLER at -5 dB.
  - One edit in `C.LOBE_N` reverts it to 3 if the "like split64" reading is preferred.
  - **So V6's gap to split64 ML (+-3) partly measures the lobe count, not the layout.**
- **Reference "split64 ML L4"** (added 2026-11-15; parent split64 ML).
  - split64 ML with +-4 lobes (`C.SRC_LOBES`, D_lobe 1088) on the est4 branch, otherwise identical (shares f_hat).
  - 4 lobes ~ 4 sigma_env at -5 dB: P(miss) 1.5e-5 instead of 7.8e-4.
  - V6 vs L4 compares the two layouts with both lobe searches sized to ~4 sigma.
  - n_hyp 62 / 62 / 44 / 44 at -5 / -4 / 0.5 / 2 dB; MACs per core ~0.06-0.07 M.
- **Nk = 64, 0.26 dB, 6.2 %.**
- **MACs per core.** ~0.19 / 0.16 / 0.14 / 0.15 M.
- **Fidelity: WEAKER** than the deployed chain (the real loop is locked for seconds before the block). It is the
  faithful single-codeword information content of the ASMs, and the CRC lobe search is our addition.

### V7a "WiFi real320" and V7b "WiFi real320 lobes" (parent: WiFi pre128)
- **Real system.**
  - IEEE 802.11-2020 OFDM PHY (cl. 17): the legacy preamble, also sent in HT / VHT / HE frames (text paywalled, read via
    MathWorks / Keysight).
  - MathWorks `wlanCoarseCFOEstimate` [vendor](https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html);
    OpenOFDM [open implementation](https://openofdm.readthedocs.io/en/latest/freq_offset.html).
- **Who uses it.** Every 802.11a/g/n/ac/ax chip runs the legacy L-STF / L-LTF. The exact estimator in commercial
  chips is not published. The lag-16 / lag-64 pair is the reference implementation (MathWorks). OpenOFDM uses only the
  coarse stage.
- **Real layout.**
  - L-STF: 10 x 16 samples (160).
  - L-LTF: a 32-sample guard + 2 x 64 (160).
  - 320 known samples at 20 MS/s.
- **Ours.** `wifi320`:
  - STF = one random 16-symbol sequence x 10;
  - LTF = a random 64-symbol sequence, its last 32 as the guard, then 2 copies;
  - single carrier, 320 known.
  - (The STF's 16-periodicity comes from occupying every 4th subcarrier; the time-domain estimators carry over
    unchanged.)
- **Real estimator.**
  - Coarse: arg(sum r[n + 16] r*[n]) / (2 pi 16) on the L-STF (range +-1/32 = 0.031).
  - Fine: lag 64 on the L-LTF (range +-1/128).
  - The coarse value picks the fine lobe. There is no retry.
  - Design CFO +-40 ppm = 0.0117 cycles / sample at 5.8 GHz.
- **Ours (`lag320`).**
  - Coarse over the 160-symbol STF (144 products), fine over the 2 x 64 LTF symbols after the guard (64 products),
    f = f_f + round((f_c - f_f) 64) / 64.
  - Window M from the fine-stage variance (`C.var_lag`, as the parent).
  - V7a: lobe count 0 (`C.SRC_LOBES`), so only the in-lobe window, which the chip also does not have.
  - V7b: + the +-4 fine lobes (1/64).
  - Phase: the LS gain on all 320 known.
- **Nk = 320, 1.18 dB, 31.2 %.**
- **MACs per core.** V7a ~0.11 M; V7b ~0.49 / 0.42 / 0.27 / 0.24 M (**above blind**).
- **Fidelity.**
  - V7a **MIXED**: the faithful chip estimator; our in-lobe CRC window and genie timing are stronger. Our +-0.03 range
    is 2.6x the 5 GHz design CFO, so the coarse stage wraps near |f| = 0.031, and the real chip never sees that.
  - V7b **STRONGER** (adds the lobe search no chip has).

## 2. Predicted comparison with blind (written before the runs, 2026-11-15)

**How to read the table.**
- Required SNR [dB] at the 8.2a targets on the fair axis (pilot energy charged).
- **Gap to blind = variant - blind**: positive = blind needs less SNR (blind better). **Gap to parent = variant -
  parent**: negative = the variant is better.
- Blind and the genie are measured (8.2a). Parents: measured where est4 measured them (split64 ML: -2.87 / -3.34 /
  1.12 / 2.38), else the est5 prediction or the re-derivation below. Variants: predictions.
- MACs per core: blind as measured at its required SNR (0.200 / 0.262 / 0.209 / 0.083 M); variants predicted.

**Method** (as competitors.md "How the predictions are made"): required SNR ~= genie (-5.19 / -3.91 / 0.64 / 1.90) + E
+ d. The estimated loss d comes from these mechanisms:

- **4th-power failure (V1, V2).** P_fail of a single 4th-power peak is taken from the measured 16 + 16 4th-power
  receiver (e4-pp25 / pp2) at per-symbol 0.5 / 1 / 1.5 / 2 / 2.5 / 3 dB: 0.33 / 0.17 / 0.07 / 0.016 / ~0.002 / ~1.2e-4.
  - e5-smoke-b: ViaSat UW 33.5 % and hyb3 5.4 % at 2/5 0.5 dB.
  - V1's 48-symbol DA lobe gates ~30 instead of ~260 4th-power cells (x 1/8), and the 3 candidates catch more, so P_fail
    is taken as ~1/15-1/30 of the single peak.
  - The 4th-power peak SNR at -4 dB is K rho_4 = 1072 x 3.4e-4 = 0.36 (-4.4 dB) [derived], so V1 / V2 fail at
    1/10, 0.15.
- **Constant LS phase from few known symbols (V3b, V5, V6).** The phase std is 1 / sqrt(2 Nk rho): 26 symbols 0.22 rad,
  32 symbols 0.20 rad, 64 symbols 0.14 rad at -4 dB.
  - Packets with |eps| above ~0.45 rad fail at 0.15 -4 dB. This is calibrated on the e4-smoke sliding window (rms 0.37
    rad -> 14 % BLER vs 0.1 %). The threshold rises to ~0.6-0.8 rad 0.5-1 dB above the genie point.
  - This is the dominant loss for Nk <= 32 at 1/10 and 0.15 (the deep 1e-4 target is hurt most). It is rough
    (+-0.2 dB).
- **CRC search (V3, V5, V6, V7b).** The windows / lobes cover the CRB, and lobe misses are <= 4e-5 (cc131) / 1e-5
  (asm32 at +-12) at -5 dB, so the search costs MACs, not BLER (d ~ 0, as 128 ML / split64 / WiFi pre128 measured:
  d = -0.04 ... +0.06).
- **Coarse wrap (V7a).** The lag-16 range is +-1/32 = 0.03125, so for f near +-0.03 the noise wraps the coarse estimate
  by 1/16 = 4 fine lobes. P_wrap = (2 sigma_c / 0.06)[phi(a) - a Q(a)], a = 0.00125 / sigma_c, sigma_c^2 =
  var_lag(lag 16, 144 products).
  - That is 1.0e-2 at 0.15 -4 dB, 3.0e-3 at -1 dB, 8.9e-4 at +1.24 dB and 5.5e-4 at +1.9 dB per-symbol [derived].
  - It reaches 1e-4 only at ~+4.3 dB.

| Variant (parent) | Nk (dB) | 1/10 @1e-4 (blind -4.90) | 0.15 @1e-3 (blind -3.60) | 2/5 @1e-3 (blind 0.61) | 1/2 @1e-3 (blind 1.79) | Gap to parent | MACs per core, blind / variant (M) |
|---|---|---|---|---|---|---|---|
| V1 hyb3-pre48 (hyb3) | 48 (0.20) | fails (BLER > 0.1 at -5 dB) | fails (BLER ~0.3-0.5 at -4 dB) | 1.6 ... 2.2 (+1.0 ... +1.6) | 2.15 ... 2.5 (+0.35 ... +0.7) | 2/5 -0.2 ... -0.5, 1/2 0 ... -0.3; both fail at 1/10, 0.15 | 2/5 0.209 / 0.052 (4x); 1/2 0.083 / 0.054 (1.5x) |
| V1w hyb3-pre48 wide (hyb3-pre48) | 48 (0.20) | -4.79 ... -4.49 (+0.11 ... +0.41) | -3.56 ... -3.36 (+0.04 ... +0.24) | 0.89 ... 0.99 (+0.28 ... +0.38) | 2.15 ... 2.25 (+0.36 ... +0.46) | 1/10, 0.15: works where V1 fails; 2/5 -0.7 ... -1.2; 1/2 -0.1 ... -0.3 (the DA window catches the 4th-power misses) | 0.200 / 0.49; 0.262 / 0.45; 0.209 / 0.14 (1.5x); 0.083 / 0.15 (variant 1.7-2.4x MORE except 2/5) |
| V2a ViaSat 7653150 (ViaSat UW) | 16 (0.07) | fails | fails | 2.45 ... 2.8 (+1.85 ... +2.2) | 2.55 ... 2.9 (+0.75 ... +1.1) | -0.15 ... +0.1 (single peak ~= the parent's barely-ranked top-32; better phase) | 0.209 / 0.039 (5x); 0.083 / 0.041 (2x) |
| V2b ViaSat top32 X4phase (ViaSat UW) | 16 (0.07) | fails | fails | 2.4 ... 2.75 (+1.8 ... +2.15) | 2.5 ... 2.85 (+0.7 ... +1.05) | -0.1 ... 0 (UW-phase loss is gone at its ~2.5 dB crossing) | 0.209 / 0.043 (5x); 0.083 / 0.045 (1.8x) |
| V3a DVB-S2 header90 (DVB-S2 style) | 90 (0.37) | -4.82 ... -4.72 (+0.08 ... +0.18) | -3.54 ... -3.44 (+0.06 ... +0.16) | 1.01 ... 1.11 (+0.40 ... +0.50) | 2.27 ... 2.37 (+0.48 ... +0.58) | -0.13 ... -0.03 (less energy, same estimate quality) | 0.200 / 0.70; 0.262 / 0.75; 0.209 / 0.88; 0.083 / 0.89 (variant 3-11x MORE; scan grid) |
| V3b DVB-S2 SOF26 (DVB-S2 style) | 26 (0.11) | -4.78 ... -4.38 (+0.12 ... +0.52) | -3.50 ... -3.10 (+0.10 ... +0.50) | 0.90 ... 1.15 (+0.29 ... +0.54) | 2.16 ... 2.41 (+0.37 ... +0.62) | -0.2 ... +0.3 (0.39 dB less energy vs the 26-symbol phase loss) | 0.200 / 0.71; 0.262 / 0.77; 0.209 / 0.89; 0.083 / 0.90 (variant 3-11x MORE; scan grid) |
| V4 MIL-110 full (MIL-110 HF) | 411 (1.47) | -3.76 ... -3.67 (+1.14 ... +1.23) | -2.48 ... -2.39 (+1.12 ... +1.21) | 2.07 ... 2.16 (+1.46 ... +1.55) | 3.33 ... 3.42 (+1.54 ... +1.63) | +0.33 (the 103 extra symbols) | 0.200 / 0.036 (5.6x); 0.262 / 0.038 (6.9x); 0.209 / 0.043 (4.9x); 0.083 / 0.045 (1.8x) |
| V5 CCSDS 131.2 real (CCSDS style) | 32 (0.13) | -4.56 ... -3.96 (+0.34 ... +0.94) | -3.53 ... -3.18 (+0.07 ... +0.42) | 0.87 ... 1.12 (+0.26 ... +0.51) | 2.13 ... 2.38 (+0.34 ... +0.59) | 1/10 +0.1 ... +0.6; 0.15 -0.2 ... +0.1; 2/5, 1/2 -0.3 ... -0.05 | 0.200 / 0.41; 0.262 / 0.39; 0.209 / 0.32; 0.083 / 0.29 (variant 1.5-3.5x MORE) |
| V6 CCSDS 131.0 ASM (split64 ML, measured) | 64 (0.26) | -4.78 ... -4.53 (+0.12 ... +0.37) | -3.55 ... -3.35 (+0.05 ... +0.25) | 0.95 ... 1.10 (+0.34 ... +0.49) | 2.21 ... 2.36 (+0.42 ... +0.57) | 1/10 -1.9 ... -1.65 (its +-12 lobes vs split64's +-3); 0.15, 2/5, 1/2 -0.2 ... 0 | 0.200 / 0.19 (1.05x); 0.262 / 0.16 (1.6x); 0.209 / 0.14 (1.5x); 0.083 / 0.15 (variant 1.8x MORE) |
| split64 ML L4 (split64 ML, measured) | 128 (0.51) | -4.68 ... -4.58 (+0.22 ... +0.32) | -3.40 ... -3.30 (+0.20 ... +0.30) | 1.12 ... 1.17 (+0.51 ... +0.56) | 2.38 ... 2.43 (+0.59 ... +0.64) | 1/10 -1.8 ... -1.7 (the +-3 lobe floor removed); else -0.05 ... +0.05 | 0.200 / 0.063 (3.2x); 0.262 / 0.061 (4.3x); 0.209 / 0.067 (3.1x); 0.083 / 0.066 (1.3x) |
| V7a WiFi real320 (WiFi pre128) | 320 (1.18) | fails (wrap floor ~1e-2 at -4 dB; 1e-4 needs ~+4.3 dB) | fails (floor 3e-3 at -1 dB) | 2.35 ... 2.5 (+1.74 ... +1.89) | 3.1 ... 3.3 (+1.31 ... +1.51) | 2/5 +1.1 ... +1.3; 1/2 +0.6 ... +0.85 | 0.209 / 0.105 (2x); 0.083 / 0.108 (variant 1.3x MORE) |
| V7b WiFi real320 lobes (WiFi pre128) | 320 (1.18) | -4.01 ... -3.96 (+0.89 ... +0.94) | -2.73 ... -2.68 (+0.87 ... +0.92) | 1.82 ... 1.87 (+1.21 ... +1.26) | 3.08 ... 3.13 (+1.29 ... +1.34) | +0.6 ... +0.7 (its 0.67 dB more energy; better coarse / phase do not pay it back) | 0.200 / 0.49; 0.262 / 0.42; 0.209 / 0.27; 0.083 / 0.24 (variant 1.3-2.9x MORE) |

V6 vs split64 ML L4 (the lobe-matched comparison): -0.1 ... +0.05 at 1/10 and -0.2 ... 0 at 0.15, 2/5 and 1/2. V6's
0.25 dB lower energy is partly lost to its 64-symbol phase.

V1w method: the DA window covers the 48-symbol estimate (5 sigma), so V1w ~= genie + 0.20 + the 48-symbol LS phase
loss (0.16 rad at -4 dB): d = 0.2 ... 0.5 at 1/10, 0.15 ... 0.35 at 0.15, 0.05 ... 0.15 at 2/5 and 1/2.

Parent references used for "gap to parent":
- hyb3, re-derived from the 4th-power curve: 2/5 ~2.4, 1/2 ~2.5. The est5 table said 1.2 ... 2.0 / 2.2 ... 2.6.
- ViaSat UW: 2/5 2.5 ... 2.8, 1/2 2.6 ... 2.9 (= the 16 + 16 4th-power curve + 0.07 dB).
- DVB-S2 style: genie + 0.50 + (0 ... 0.1).
- MIL-110 HF: genie + 1.14.
- CCSDS style: est5 -4.65 ... -4.3 / -3.4 ... -3.2 / 1.15 ... 1.25 / 2.4 ... 2.5.
- WiFi pre128: genie + 0.51 + (0 ... 0.1). e5-smoke d ~ 0: 2/800 vs the genie's 1-3/800.

**Summary prediction.**
- No variant beats blind at any target.
- The closest are V3a header90 (+0.06 ... +0.18 at 1/10, 0.15), V6 ASM and V3b SOF26 / V5 cc131 at 0.15 (+0.05 ...
  +0.5).
- Faithful layouts are **cheaper in pilot energy but pay in either BLER (4th power, wrap, few-symbol phase) or MACs
  (exhaustive CRC searches)**. V3a, V3b, V5 and V7b are predicted to need **more MACs per core than blind** at every
  rate (V3a / V3b re-derived on the scan grid; the claim survived the grid fix), and V1w at 1/10, 0.15 and 1/2. V1,
  V2 and V4 stay 1.5-7x cheaper than blind but are 0.35-2.2 dB behind.
- V1w (the DA-sized window) turns V1's failure at 1/10 and 0.15 into a near-blind result (+0.04 ... +0.41), at
  ~2x blind's MACs.
- Against their parents: V1, V3a, V6 and (at 2/5, 1/2) V5 improve. V4, V7a and V7b get worse, because the real
  layouts carry more energy (V4, V7) or no lobe search (V7a).

## 3. As implemented (code-editor, 2026-11-15; py_compile + a pure layout / MACs check only, nothing simulated)

- **est4/common.py.**
  - Constants PRE48, DVB_SOF, MILF_PRE, CC_P / CC_D, ASM_LEN, WIFI_STF / WIFI_GI.
  - `SOURCES` + the 10 variants, `VARS`, `PARENT`, `SRC_LOBES["WiFi real320"] = (64, 0)`, `NDA4_WIN`.
  - `_segments` for pre48, dvbh90, sof26, mil110f, cc131, asm32, wifi320. `LAYOUTS5` (old LAYOUTS) + `VLAYOUTS` =
    `LAYOUTS`, so the old `LAYOUT_ID`s are unchanged.
  - `LOBE_N`: dvbh90 3, sof26 1, mil110f 3, cc131 17, asm32 12, wifi320 4.
  - `lobe_D`: dvbh90 90, sof26 26, wifi320 64, mil110f 287 (mean probe spacing); cc131 556 and asm32 1056 by the
    2-field rule; pre48 0.
  - `KMAX_ALL` over LAYOUTS5 (still 1332), new `KMAX_V` = 1435.
  - `make_burst`: wifi320 STF / LTF structure; asm32 the same marker twice.
- **est4/estimators.py.** `nda4pk`, `lag320` (+ est_macs), phase model `x4` (`gain_x4`, phase_macs 12 K + 4 Nk + 44).
- **est4/run_bler.py.**
  - The variants take the est5 search branch.
  - `window`: crb_nda4 for nda4pk and NDA4_WIN, var_lag for lag320.
  - Phase-noise path: `phv` = the est5 path extended to KMAX_V from rng `[44] + key`. It is only drawn when a layout is
    longer than 1332 and pn > 0.
  - `mcnemar_src`: per-source McNemar reference = the parent if in the job. The json field `mcnemar_ref` is now per
    row, identical to before for every non-variant source.
  - The per-packet MACs log is unchanged (mac_coef works for the new est / model names; checked by the layout script).
- **Layout check (pure, 1.3 s).** Nk / K / dB:
  - pre48 48 / 1072 / 0.199;
  - dvbh90 90 / 1114 / 0.366;
  - sof26 26 / 1050 / 0.109;
  - mil110f 411 / 1435 / 1.466 (fields 287 + 4 x 31, centres 143 / 558 / 845 / 1132 / 1419);
  - cc131 32 / 1056 / 0.134 (centres 249.5 / 805.5);
  - asm32 64 / 1088 / 0.263 (centres 15.5 / 1071.5);
  - wifi320 320 / 1344 / 1.181.
  - The STF / LTF periodicity and the asm32 repeat were asserted.
  - Windows M at -5 / -4 / 0.5 / 2 dB:
    - hyb3-pre48 and both ViaSat 16 / 11 / 3 / 2;
    - header90 57 / 51 / 30 / 26;
    - SOF26 363 / 324 / 193 / 163;
    - MIL full 2 / 2 / 1 / 1;
    - cc131 9 / 8 / 5 / 4;
    - ASM 4 / 3 / 2 / 2;
    - WiFi 62 / 52 / 25 / 20.
- **Plots.** `plot_e4.py --e5 --var` loads the v-* parts (labels in STY5); the parent rows are other seeds and pool
  with the e4 / e5 rows.
- **Verifier fixes (2026-11-15, second pass).**
  - common: + "hyb3-pre48 wide" (VARS, PARENT hyb3-pre48, `WIN_MAX`) and "split64 ML L4" (est4 branch, `SRC_LOBES`
    (1088, 4), PARENT split64 ML). `SCAN` = header90, SOF26 with `SRC_LOBES` (0, 0).
  - run_bler:
    - `SCAN_K` = 801.
    - `_hyp` scans |k| <= SCAN_K for C.SCAN.
    - `hyp_matrix`: per-hypothesis validity |f_hat + off| <= MAX_CFO + STEP for C.SCAN. The hyb3 duplicate filter is
      done in row blocks of 4 when B (H + 1)^2 > 2^24 (V1w: ~776 hypotheses), the same result as the one-shot form
      (checked on a synthetic case).
    - `window`: max(crb_nda4, crb_known) for WIN_MAX.
    - in_search for C.SCAN = a valid hypothesis within STEP / 2 of f.
    - The est4-branch in_search uses `C.src_lobes(src, lobes)[1]` (= `lobes` for every est4 source).
  - Pure checks (2.1 s):
    - every old source reproduces n_hyp and window of bler_e5-smoke-a/b, e4-10/15/25 and ars-15 exactly (0
      mismatches);
    - scan: n_hyp 1602, 801-802 valid at -5 / -4 / 0.5 / 2 dB for both, full coverage of +-0.03, grid steps <= STEP,
      no duplicates;
    - V1w M 145 / 129 / 77 / 65, n_hyp (without candidates) 290 / 258 / 154 / 130;
    - L4 n_hyp 62 / 62 / 44 / 44.
  - Untested path: no v-* job runs pn > 0, so `phv` / the third `extend_path` (mil110f, wifi320 longer than 1332) has
    never executed. It needs its own smoke before any phase-noise run of those two layouts.

## 4. Jobs (none submitted)

Seeds are new and unique (est4 used 50-57, 61-66, 81 before). All jobs run pn 0, per-packet MACs logging on (default),
nothing below -5 dB, LF only (0 CR bytes checked). Each parent is in the same job as its variants.

Runtime is from a cost model fitted to e5-smoke-a + e5-10: t_decode 1.9 ms and t_metric 0.15 ms per packet (x1.6 at
2/5, 1/2), first-decode failure and BLER assumed per source. It is +-50 %.

Groups:
- m = MIL-110 HF, MIL-110 full, split64 ML, split64 ML L4, CCSDS 131.0 ASM, CCSDS style, CCSDS 131.2 real
- h = DVB-S2 style, DVB-S2 header90
- p = ViaSat UW, ViaSat 7653150, ViaSat top32 X4phase, hyb3, hyb3-pre48, hyb3-pre48 wide (--min-err 200)
- w = WiFi pre128, WiFi real320, WiFi real320 lobes
- s = DVB-S2 style, DVB-S2 SOF26

All jobs run 480k packets per SNR in chunks of 4000 on the e5 grids, split by SNR where a job would exceed ~9 h by the
model. Estimates are base case; the pessimistic value assumes SOF26 BLER 3 % at the hard point, and "no stop" means
the --min-err 200 early stop does not fire.

| Job (seed) | Rate, SNRs | Group | Estimate |
|---|---|---|---|
| v-10 (92) | 1/10, -5 -4.5 -4 -3 -2 | m | 6.4 h |
| v-10h (93) | same | h | 6.7 h |
| v-10p (94) | 1/10, -5 -4.5 | p | 1.4 h (9.0 h no stop) |
| v-10p2 (97) | 1/10, -4 -3 -2 | p | 1.2 h (1.9 h no stop) |
| v-10w (95) | 1/10, -5 ... -2 | w | 7.2 h |
| v-10s (96) | 1/10, -5 ... -2 | s | 5.9 h (9.7 h pessimistic) |
| v-15 (101) | 0.15, -4.5 -4 -3.5 -3 -2.5 -2 -1 | m | 7.8 h |
| v-15h (102) | 0.15, -4.5 -4 -3.5 | h | 4.6 h |
| v-15h2 (107) | 0.15, -3 -2.5 -2 -1 | h | 4.2 h |
| v-15p (103) | 0.15, -4.5 -4 -3.5 | p | 1.4 h (9.1 h no stop) |
| v-15p2 (109) | 0.15, -3 -2.5 -2 -1 | p | 2.1 h |
| v-15w (104) | 0.15, -4.5 -4 -3.5 | w | 4.7 h |
| v-15w2 (105) | 0.15, -3 -2.5 -2 -1 | w | 3.9 h |
| v-15s (106) | 0.15, -4.5 -4 -3.5 | s | 3.7 h (7.5 h pessimistic) |
| v-15s2 (108) | 0.15, -3 -2.5 -2 -1 | s | 4.3 h |
| v-25 (111) | 2/5, 0 0.5 1 1.5 2 | m | 6.9 h |
| v-25h (112) | 2/5, 0 0.5 1 | h | 7.3 h |
| v-25h2 (116) | 2/5, 1.5 2 | h | 3.3 h |
| v-25p (113) | 2/5, 0 ... 2 | p | 2.5 h (9.1 h no stop) |
| v-25w (114) | 2/5, 0 ... 2 | w | 5.8 h |
| v-25s (115) | 2/5, 0 0.5 | s | 4.2 h (10.2 h pessimistic) |
| v-25s2 (117) | 2/5, 1 1.5 2 | s | 5.2 h |
| v-2 (121) | 1/2, 1.5 2 2.5 3 | m | 5.6 h |
| v-2h (122) | 1/2, 1.5 2 | h | 5.6 h |
| v-2h2 (126) | 1/2, 2.5 3 | h | 3.3 h |
| v-2p (123) | 1/2, 1.5 ... 3 | p | 1.7 h (7.5 h no stop) |
| v-2w (124) | 1/2, 1.5 ... 3 | w | 4.1 h |
| v-2s (125) | 1/2, 1.5 2 | s | 4.2 h (10.2 h pessimistic) |
| v-2s2 (127) | 1/2, 2.5 3 | s | 3.4 h |
| v-smoke (61, 131-135) | v-smoke-id = e5-smoke-a repeated; 0.15 -4 and 2/5 0.5 dB, 800 each, 10 parts v-smoke-{m,h,p,w,s}{15,25} | e5-smoke-a sources; each group + Genie in m | ~6 min |

**Grid changes after the verifier's review.** With the scan, SOF26 costs ~801 metric passes per packet at every SNR,
not 1000-2200. So the s jobs are back on the full e5 grids at 480k (the first version had dropped end points and run
240k / 360k). The h and s jobs at 0.15, 2/5 and 1/2 and the p jobs at 1/10 and 0.15 are split by SNR (V1w is predicted
to work at low SNR, so their early stop may not fire). Each split pair has separate seeds and parts.

## 5. Smoke pass criteria (v-smoke; seeds differ from e5-smoke, so the parents match only within noise)

1. **Completion.** `logs/run_v-smoke.out` has 11 x "EVAL DONE" + "ALL DONE", no "Traceback" and no "WARNING maclog".
   There are 11 `est4/results/bler_v-smoke-*.json`, and 8 `macs_*.npz` per part in `est4/dumps/v-smoke-*/` with
   finite coef and contig True.
2. **Identity (v-smoke-id).** For every source, frame_err, undetected, extra_decodes, metric_evals and se_first equal
   `bler_e5-smoke-a.json` exactly.
   - Any difference means an existing est5 source changed: stop and diff the code before using any v-* result.
   - Caveat: this assumes no est5 source changed between the e5-smoke-a run and the variant edits (e.g. the vde27
     layout fix of 2026-11-15). If only VDE-SAT differs, check git for that fix first.
3. **Bookkeeping.**
   - Each variant row has mcnemar_ref = its parent (hyb3-pre48 wide -> hyb3-pre48, split64 ML L4 -> split64 ML), and
     the parent row has the job's first source (Genie in m, DVB-S2 style in h / s, ViaSat UW in p, WiFi pre128 in w).
   - nk / energy_db as in section 3.
   - lobes: 0 / 0 / 3 / 17 / 12 / 4 / 0 / 4 for header90 / SOF26 / MIL full / cc131 / ASM / split64 ML L4 / WiFi
     real320 / its lobes variant; 0 for pre48, pre48 wide and both ViaSat.
   - n_hyp at -4 dB: header90 1602, SOF26 1602, MIL full 34, cc131 594, ASM 174, L4 62, WiFi real320 104 and its lobes
     variant 944, hyb3-pre48 22, pre48 wide 258, ViaSat 22.
   - At 0.5 dB: header90 / SOF26 1602 (801-802 valid per packet at both SNRs).
4. **Parents reproduce e5-smoke within noise.**
   - 0.15 -4 dB: DVB-S2 style <= 15/800, CCSDS style <= 5, MIL-110 HF <= 6, WiFi pre128 <= 8, ViaSat UW >= 600,
     hyb3 200-500, split64 ML <= 10 (e4: 955/480k).
   - 2/5 0.5 dB: ViaSat UW 180-350, hyb3 20-80, the rest <= 10/800.
5. **Variants are sane (a failure here means a bug, not a result).**
   - **undetected <= 2/800** for every large-search source: CCSDS 131.2 real, DVB-S2 header90, DVB-S2 SOF26, WiFi
     real320 lobes, CCSDS 131.0 ASM (and hyb3-pre48 wide).
   - MIL-110 full <= 8/800 at both points, lobe_err 0, in_search 1.0.
   - CCSDS 131.0 ASM: in_search >= 0.995, **lobe_err 50-95 %** of packets, BLER <= 20/800 (0.15) and <= 10/800 (2/5).
   - split64 ML L4: BLER <= split64 ML + 3 at both points; extra decodes / metric passes up to ~1.4x split64 ML.
   - CCSDS 131.2 real: in_search >= 0.995, lobe_err >= 50 %, BLER <= 40/800 (0.15; predicted ~1-3 %) and <= 15/800
     (2/5).
   - DVB-S2 header90 and SOF26: in_search >= 0.999 (the scan covers the range); metric_evals / frame ~700-800 at both
     points (0.95-1.0 x 801; the first decode almost always fails); metric_rounds / frame ~25-26.
     - header90 BLER <= 10/800 (0.15) and <= 8/800 (2/5).
     - SOF26 BLER 2-40/800 (0.15) and <= 20/800 (2/5).
   - Both ViaSat variants >= 550/800 at 0.15 -4 dB; at 2/5 0.5 dB within +-100 of ViaSat UW (X4phase n01 >= n10).
   - **ViaSat 7653150 vs ViaSat UW at 2/5 0.5 dB:** rmse_first within a factor 1.5 and frac_in_window within +-0.1 of
     the parent. Both start from a 4th-power peak; a large mismatch means a /4 or bin-scaling bug in nda4pk.
   - hyb3-pre48 at 2/5 0.5 dB below hyb3 (predicted 1-4 % vs ~5 %); at 0.15 -4 dB 100-500/800.
   - hyb3-pre48 wide <= hyb3-pre48 at both points (n10 small), and at 0.15 -4 dB well below it: predicted <= 20/800
     vs 100-500.
   - WiFi real320 at 0.15 -4 dB 3-25/800 (wrap floor ~1 %, lobe_err ~ its excess errors); WiFi real320 lobes <= 8/800
     with lobe_err > 0 and in_search >= 0.995.
6. **Timing gate** (the part time on the "saved ... Ns" line).
   - Model at 0.15: m 12, h 14, p 30, w 16, s 14-18 s. Model at 2/5: m 14, h 22, p 25, w 14, s 21-28 s.
   - A part slower than 1.6x its model needs its full jobs re-split before submission.
   - If SOF26 is above 8/800 at 0.15 -4 dB, use the pessimistic runtimes: v-10s, v-25s and v-2s run ~10 h, still
     inside 12 h.
7. **Phase noise not covered.** No v-* job (smoke included) uses pn > 0, so the `phv` path (mil110f, wifi320) is
   untested. A separate pn smoke is needed before any phase-noise run of those layouts.

## 8. Runtime after the smoke (2026-11-15)

**Measured part times** (`logs/run_v-smoke.out`, "saved ... Ns"; the identity part took 42 s vs 41 s in e5-smoke-a, so
the hardware is the same; fixed overhead <= 5 s, kept in the ratios, so they are pessimistic):

| Group | 0.15: measured / model | ratio | 2/5: measured / model | ratio |
|---|---|---|---|---|
| m | 27 / 12 | 2.25 | 28 / 14 | 2.00 |
| h | 28 / 14 | 2.00 | 43 / 22 | 1.95 |
| p | 43 / 30 | 1.43 | 23 / 25 | 0.92 (1.0 used) |
| w | 32 / 16 | 2.00 | 24 / 14 | 1.71 |
| s | 27 / 18 (pess.) or 14 | 1.50 or 1.93 | 47 / 28 (pess.) or 21 | 1.68 or 2.24 |

**Method.**
- New estimate = the section-4 estimate x the ratio. The pessimistic value is used where section 4 gives one ("no
  stop" for p, "pessimistic" for s).
- The 1/10 jobs use the 0.15 ratio of their group, and the 1/2 jobs the 2/5 ratio.
- s jobs: max(pessimistic x the pessimistic-model ratio, base x the base-model ratio).
- Smoke SOF26 BLER: 3/800 at 0.15 -4 dB and 4/800 at 2/5 0.5 dB, so the pessimistic SOF26 case did not occur. It is
  kept as the sizing case anyway.
- The cost is split equally over the SNRs of a job. Exception: for v-25s and v-2s, the pessimistic excess is also
  placed on the hard point (0 / 1.5 dB = 13.6 h alone). That point is split by packets into 2 x 240k with separate
  seeds.
- Smoke parts ran 8 chunks on 16 workers, so a part time = its slowest chunk. The full jobs (120 chunks) average over
  chunks, which is another pessimistic margin.

**Jobs over ~10 h, re-split** (old scripts kept, **do not submit**: v-10, v-10h, v-10p, v-10w, v-10s, v-15, v-15p,
v-15s, v-25, v-25h, v-25s, v-25s2, v-2, v-2h, v-2s):
- v-10 14.4, v-10h 13.4, v-10p 12.9, v-10w 14.4, v-10s 14.6 h;
- v-15 17.6, v-15p 13.0, v-15s 11.3 h;
- v-25 13.8, v-25h 14.2, v-25s 17.1, v-25s2 11.6 h;
- v-2 11.2, v-2h 10.9, v-2s 17.1 h.

**Jobs to submit (48).** Every (source, SNR) keeps 480k packets. New seeds are 141-177, unused in jobs/ (incl.
archive). Parts = job names, registered in job_progress.py and in plot_e4.py `VARP`.

| Job (seed) | Rate, SNRs | Group | Estimate |
|---|---|---|---|
| v-10ma (141) | 1/10, -5 -4.5 | m | 5.8 h |
| v-10mb (142) | 1/10, -4 -3 -2 | m | 8.6 h |
| v-10ha (143) | 1/10, -5 -4.5 | h | 5.4 h |
| v-10hb (144) | 1/10, -4 -3 -2 | h | 8.0 h |
| v-10pa (145) | 1/10, -5 | p | 6.4 h (no stop) |
| v-10pb (146) | 1/10, -4.5 | p | 6.4 h (no stop) |
| v-10p2 (97) | 1/10, -4 -3 -2 | p | 2.7 h (no stop) |
| v-10wa (147) | 1/10, -5 -4.5 | w | 5.8 h |
| v-10wb (148) | 1/10, -4 -3 -2 | w | 8.6 h |
| v-10sa (149) | 1/10, -5 -4.5 | s | 5.8 h (10.3 h if the whole SOF26 excess falls here) |
| v-10sb (150) | 1/10, -4 -3 -2 | s | 8.7 h |
| v-15ma (151) | 0.15, -4.5 -4 | m | 5.0 h |
| v-15mb (152) | 0.15, -3.5 -3 | m | 5.0 h |
| v-15mc (153) | 0.15, -2.5 -2 -1 | m | 7.5 h |
| v-15h (102) | 0.15, -4.5 -4 -3.5 | h | 9.2 h |
| v-15h2 (107) | 0.15, -3 -2.5 -2 -1 | h | 8.4 h |
| v-15pa (154) | 0.15, -4.5 | p | 4.3 h (no stop) |
| v-15pb (155) | 0.15, -4 -3.5 | p | 8.7 h (no stop) |
| v-15p2 (109) | 0.15, -3 -2.5 -2 -1 | p | 3.0 h |
| v-15w (104) | 0.15, -4.5 -4 -3.5 | w | 9.4 h |
| v-15w2 (105) | 0.15, -3 -2.5 -2 -1 | w | 7.8 h |
| v-15sa (156) | 0.15, -4.5 | s | 3.8 h (8.1 h if the whole excess falls here) |
| v-15sb (157) | 0.15, -4 -3.5 | s | 7.5 h |
| v-15s2 (108) | 0.15, -3 -2.5 -2 -1 | s | 8.3 h |
| v-25ma (161) | 2/5, 0 0.5 | m | 5.5 h |
| v-25mb (162) | 2/5, 1 1.5 2 | m | 8.3 h |
| v-25ha (163) | 2/5, 0 | h | 4.7 h |
| v-25hb (164) | 2/5, 0.5 | h | 4.7 h |
| v-25hc (165) | 2/5, 1 | h | 4.7 h |
| v-25h2 (116) | 2/5, 1.5 2 | h | 6.4 h |
| v-25p (113) | 2/5, 0 ... 2 | p | 9.1 h (no stop) |
| v-25w (114) | 2/5, 0 ... 2 | w | 9.9 h (7.9 h without the 5 s overhead; borderline, not split) |
| v-25sa (166) | 2/5, 0, 240k | s | 4.3 h (6.8 h with the excess at 0 dB) |
| v-25sb (167) | 2/5, 0, 240k | s | 4.3 h (6.8 h) |
| v-25sc (168) | 2/5, 0.5 | s | 8.6 h |
| v-25s2a (169) | 2/5, 1 | s | 3.9 h |
| v-25s2b (170) | 2/5, 1.5 2 | s | 7.7 h |
| v-2ma (171) | 1/2, 1.5 2 | m | 5.6 h |
| v-2mb (172) | 1/2, 2.5 3 | m | 5.6 h |
| v-2ha (173) | 1/2, 1.5 | h | 5.5 h |
| v-2hb (174) | 1/2, 2 | h | 5.5 h |
| v-2h2 (126) | 1/2, 2.5 3 | h | 6.4 h |
| v-2p (123) | 1/2, 1.5 ... 3 | p | 7.5 h (no stop) |
| v-2w (124) | 1/2, 1.5 ... 3 | w | 7.0 h |
| v-2sa (175) | 1/2, 1.5, 240k | s | 4.3 h (6.8 h with the excess at 1.5 dB) |
| v-2sb (176) | 1/2, 1.5, 240k | s | 4.3 h (6.8 h) |
| v-2sc (177) | 1/2, 2 | s | 8.6 h |
| v-2s2 (127) | 1/2, 2.5 3 | s | 7.6 h |

Total ~310 job-hours at these estimates.
- The re-split jobs have new seeds, so their packets are not those of the unsubmitted originals.
- Never submit an original together with its split: plot_e4 would pool both.

## 9. Measured (filled in as the v-* jobs land)
### v-2p, R = 1/2 (2026-11-15, ALL DONE, no Traceback; blind 1.79 dB @1e-3)
| Variant (parent) | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|
| ViaSat UW (parent) | 2.2 ... 2.8 | fails (> 3.07 dB) | - | parent worse than predicted |
| V2a ViaSat 7653150 | 2.55 ... 2.9 | 2.74 | +0.95 | hit; 0.33+ dB better than the parent |
| V2b ViaSat top32 X4phase | 2.5 ... 2.85 | 2.61 | +0.82 | hit; the UW phase was the parent's weak point |
| hyb3 (parent) | 2.2 ... 2.6 | 2.34 | +0.55 | hit |
| V1 hyb3-pre48 | 2.15 ... 2.5 | 2.18 | +0.39 | hit |
| V1w hyb3-pre48 wide | 2.15 ... 2.25 | 2.11 | +0.32 | close miss (-0.04, in its favour) |

### v-25p, R = 2/5 (2026-11-15 ~22:50, ALL DONE, no Traceback; blind 0.61 dB @1e-3)
| Variant (parent) | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|
| V2a ViaSat 7653150 | 2.45 ... 2.8 | > 2.07 (2.0e-2 at the top point) | > +1.46 | consistent (range ends below the prediction) |
| V2b ViaSat top32 X4phase | 2.4 ... 2.75 | > 2.07 (1.0e-2 at the top point) | > +1.46 | consistent |
| hyb3 (parent, pooled with e5-ppB) | 1.2 ... 2 | 1.79 | +1.18 | hit |
| V1 hyb3-pre48 | 1.6 ... 2.2 | 2.02 | +1.41 | hit |
| V1w hyb3-pre48 wide | 0.89 ... 0.99 | 0.91 | +0.30 | hit |

### v-10pa / v-10pb, R = 1/10 (2026-11-16 early, ALL DONE, no Traceback; blind -4.78 dB @1e-4)
| Variant | Predicted @1e-4 | Measured (fair axis) | Verdict |
|---|---|---|---|
| V1w hyb3-pre48 wide | -4.79 ... -4.49 (+0.11 ... +0.41) | 5.7e-4 at -4.80, 3.7e-4 at -4.30: **floor ~4e-4, fails 1e-4** | miss: worse than predicted |
| V1 hyb3-pre48, hyb3, ViaSat x3 | fails | 0.42-0.95 | hit |
- The floor equals the packets whose true CFO is outside the search (in-search 0.9995 / 0.9996 -> 5e-4 / 4e-4): the
  4th-power coarse estimate sometimes lands on a noise peak further than the +-137-step DA window. Real result of the
  layout (48 known symbols cannot fix a gross 4th-power miss at -5 dB), not a bug. -4 dB and above: v-10p2 (running).

### v-15pa / v-15pb, R = 0.15 (2026-11-16, ALL DONE, no Traceback; blind -3.60 @1e-3, -2.93 @1e-4)
| Variant | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|
| V1w hyb3-pre48 wide | -3.56 ... -3.36 (+0.04 ... +0.24) | **-3.63** (1.96e-3 at -3.80, 2.8e-4 at -3.30) | **-0.03 (tie, inside blind's CI [-3.67, -3.52])** | close miss, in its favour |
| V1 hyb3-pre48, hyb3, ViaSat x3 | fails | 0.42-0.96 | - | hit |
- @1e-4: open until v-15p2 (-3 dB and up); in-search 0.9998 at -3.8 / -3.3 dB means a search-miss floor near 2e-4, so
  it likely fails 1e-4 like at 1/10.

### v-10p2, R = 1/10, data Es/N0 -4 -3 -2 dB (2026-11-16, ALL DONE, no Traceback; blind -4.78 dB @1e-4)
| Variant | BLER at the fair-axis points | Verdict @1e-4 |
|---|---|---|
| V1w hyb3-pre48 wide | 2.3e-4 (102 / 439k) at -3.80, 2.4e-4 (102 / 434k) at -2.80, 3.2e-4 (128 / 406k) at -1.80 | **fails over the whole range: flat floor ~2.5e-4** (confirms the v-10pa/pb miss) |
| V1 hyb3-pre48 | 0.46-0.52 | fails (hit) |
| hyb3 (parent) | 0.32-0.43 | fails (hit) |
| ViaSat UW / 7653150 / top32 X4phase | 0.83-0.95 | fail (hit) |
- The floor does not fall with SNR: in-search stays 0.9996-0.9997, i.e. ~3e-4 of the packets have the true CFO outside
  the DA window. The 4th-power coarse step over the 3 % range still picks a noise peak at 1/10 (K rho_4 is small at
  these SNRs), and 48 known symbols cannot recover it. V1w is a 1/10 loss for the competitor, not a near-tie.

### v-10ma, R = 1/10, data Es/N0 -5 -4.5 dB (2026-11-16, ALL DONE, no Traceback; PROVISIONAL until v-10mb lands)
| Variant | BLER (fair axis) | Predicted @1e-4 | Early read |
|---|---|---|---|
| split64 ML L4 | 8.1e-5 at -4.49, 3.1e-5 at -3.99 | -4.68 ... -4.58 | ~-4.6 by extrapolation (blind ~+0.18): likely hit; shallow slope |
| split64 ML (L3, reference) | 1.5e-3 at -4.49, 8.1e-4 at -3.99 | - | the 4th lobe removes its floor |
| V6 CCSDS 131.0 ASM | 8.7e-4 at -4.74, 2.2e-4 at -4.24 | -4.78 ... -4.53 | likely miss, worse than predicted |
| V5 CCSDS 131.2 real | 1.3e-2 at -4.87, 5.2e-3 at -4.37 | -4.56 ... -3.96 | likely miss, worse than predicted |
| V4 MIL-110 full | 1.9e-5 at -3.53, 0 at -3.03 | -3.76 ... -3.67 | crossing below -3.53: consistent so far |
| CCSDS style, MIL-110 HF (parents) | 4.2e-5 at -4.49 / 2.1e-5 at -3.86 | - | as in e5-10 |

### v-10wa, R = 1/10, data Es/N0 -5 -4.5 dB (2026-11-16, ALL DONE, no Traceback; PROVISIONAL until v-10wb lands)
| Variant | BLER (fair axis) | in-search | Predicted @1e-4 | Early read |
|---|---|---|---|---|
| WiFi pre128 (parent) | 9.9e-4 at -4.49, 4.9e-4 at -3.99 | 0.9989, 0.9994 | - | search-miss floor ~5e-4 forming |
| V7a WiFi real320 | 1.5e-2 at -3.82, 1.05e-2 at -3.32 | 0.985, 0.990 | fails (wrap floor ~1e-2) | hit: lag-16 wrap floor ~1e-2 |
| V7b WiFi real320 lobes | 1.0e-3 at -3.82, 5.2e-4 at -3.32 | 0.9989, 0.9994 | -4.01 ... -3.96 | **likely miss, worse**: already above the predicted crossing and falling only x2 per 0.5 dB; BLER ~ 1 - in-search, so a search-miss floor near 5e-4 |
- The lobes fix V7a's wrap floor (x15 at -3.82) but not the coarse misses outside the +-4 lobes. Both Wi-Fi forms are
  well behind blind (-4.78) at 1/10 either way.

### v-15ma, R = 0.15, data Es/N0 -4.5 -4 dB (2026-11-16, ALL DONE, no Traceback; PROVISIONAL until v-15mb lands)
Blind -3.60 dB @1e-3. Crossing = log-linear extrapolation from the two points (all are still above 1e-3 at -4 dB raw).
| Variant | BLER (fair axis) | Predicted @1e-3 | Extrapolated @1e-3 (gap to blind) | Early read |
|---|---|---|---|---|
| split64 ML L4 | 2.6e-2 at -3.99, 1.7e-3 at -3.49 | -3.40 ... -3.30 | ~-3.39 (+0.21) | hit |
| split64 ML (L3) | 2.6e-2 at -3.99, 2.1e-3 at -3.49 | - | ~-3.35 (+0.25) | L4 ~0.04 dB better |
| V6 CCSDS 131.0 ASM | 4.3e-2 at -4.24, 4.5e-3 at -3.74 | -3.55 ... -3.35 | ~-3.40 (+0.20) | hit |
| CCSDS style (parent) | 2.7e-2 at -3.99, 1.9e-3 at -3.49 | - | ~-3.37 (+0.23) | as est5 (+0.19) |
| V5 CCSDS 131.2 real | 1.0e-1 at -4.37, 2.7e-2 at -3.87 | -3.53 ... -3.18 | ~-2.6 (+1.0), shallow slope, in-search 0.997-0.9985 | **miss, much worse** |
| MIL-110 HF (parent) | 2.1e-2 at -3.36, 1.25e-3 at -2.86 | - | ~-2.82 (+0.78) | - |
| V4 MIL-110 full | 2.2e-2 at -3.03, 1.2e-3 at -2.53 | -2.48 ... -2.39 | ~-2.50 (+1.10) | hit |
- V5 is the only miss: 32 pilots spread over the burst give a weak, partly ambiguous CFO estimate at 0.15 (in-search
  < 0.9985), so its curve is shallow. Same pattern as at 1/10 (v-10ma).

### v-15p2, R = 0.15, data Es/N0 -3 -2.5 -2 -1 dB (2026-11-16, ALL DONE, no Traceback; blind -2.93 dB @1e-4)
| Variant | BLER (fair axis) | Verdict @1e-4 |
|---|---|---|
| V1w hyb3-pre48 wide | 2.0e-4 at -2.80, 2.5e-4 at -2.30, 2.9e-4 at -1.80, 3.8e-4 at -0.80 (87-152 errors) | **fails: floor 2-4e-4, rising slightly with SNR** (predicted at v-15pb: likely floor ~2e-4) |
| V1 hyb3-pre48, hyb3 | 0.20-0.54 | fail |
| ViaSat UW / 7653150 / top32 X4phase | 0.70-0.95 | fail |
- As at 1/10: BLER ~= 1 - in-search (0.9997 ... 0.9995), i.e. coarse 4th-power misses outside the DA window. At 0.15
  V1w ties blind @1e-3 (-3.63 vs -3.60) but cannot reach 1e-4 at all.

### v-2ma, R = 1/2, data Es/N0 1.5 2 dB (2026-11-16, ALL DONE, no Traceback; blind 1.73 dB [1.69, 1.76] @1e-3)
The two points bracket 1e-3 for every source, so these are interpolated crossings (log-linear), not extrapolations.
| Variant | BLER (fair axis) | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|---|
| V5 CCSDS 131.2 real | 5.4e-2 at 1.63, 3.65e-3 at 2.13 (1.9e-4 at 2.63, v-2mb) | 2.13 ... 2.38 | **2.35** | **+0.63** | hit (CORRECTED 2026-11-17: first written as 2.00 / +0.27, an arithmetic slip; 1e-3 lies between 2.13 and 2.63) |
| V6 CCSDS 131.0 ASM | 2.6e-2 at 1.76, 5.9e-4 at 2.26 | 2.21 ... 2.36 | 2.19 | +0.46 | hit (edge) |
| split64 ML L4 | 1.84e-2 at 2.01, 3.0e-4 at 2.51 | 2.38 ... 2.43 | 2.36 | +0.63 | hit (edge); identical to L3 packet for packet (no lobe errors at 1/2) |
| CCSDS style (parent) | 1.9e-2 at 2.01, 3.6e-4 at 2.51 | - | 2.38 | +0.65 | - |
| MIL-110 HF (parent) | 1.9e-2 at 2.64, 3.2e-4 at 3.14 | - | 3.00 | +1.27 | - |
| V4 MIL-110 full | 2.1e-2 at 2.97, 3.65e-4 at 3.47 | 3.33 ... 3.42 | 3.35 | +1.62 | hit |
- (Corrected 2026-11-17) V5 is NOT the closest competitor at 1/2: its waterfall is the shallowest of these layouts, so
  1e-3 is only reached between 2.13 and 2.63 dB. Closest at 1/2 stays the Advantech wide preamble (+0.38).
- MACs not yet compared here; V5 was predicted at ~0.29 M per core vs blind 0.139 M (blind ~2x cheaper).

### v-10mb, R = 1/10, data Es/N0 -4 -3 -2 dB (2026-11-16, ALL DONE, no Traceback) - final with v-10ma
Crossings @1e-4 interpolated (log-linear) over the pooled v-10ma + v-10mb points. Blind -4.78 [-4.86, -4.69].
| Variant | BLER (fair axis), new points | Predicted @1e-4 | Measured @1e-4 | Gap to blind | Verdict |
|---|---|---|---|---|---|
| split64 ML L4 | 6.3e-6 at -3.49, 0 at -2.49 | -4.68 ... -4.58 | below -4.49 (8.1e-5 there); ~-4.60 by extrapolation | ~+0.18 | hit (crossing not bracketed) |
| split64 ML (L3) | 3.4e-4 at -3.49, 5.8e-5 at -2.49 | - | -2.80 | +1.98 | lobe floor (as e5) |
| V6 CCSDS 131.0 ASM | 7.1e-5 at -3.74, 4.2e-6 at -2.74 | -4.78 ... -4.53 | **-3.89** | **+0.89** | **miss, much worse** |
| V5 CCSDS 131.2 real | 2.1e-3 at -3.87, 3.3e-4 at -2.87, 3.8e-5 at -1.87 | -4.56 ... -3.96 | **-2.32** | **+2.46** | **miss, much worse** |
| V4 MIL-110 full | 0 at -2.53 and up | -3.76 ... -3.67 | below -3.53 (1.9e-5 there) | > +1.0 ... +1.25 | consistent (not bracketed) |
| CCSDS style, MIL-110 HF (parents) | 0 errors | - | -4.66 / -4.11 (e5-10lo) | +0.12 / +0.67 | - |
- V6 / V5 at 1/10: shallow curves (x3-x10 per dB), in-search 0.998-0.9999 at the low points: residual CFO-search
  misses dominate the 1e-4 tail. The +-12 ASM lobes do not cover all of them; 131.2's 32 pilots are too few at 1/10.
- Open: L4 and MIL full are below 1e-4 at their lowest point. A raw -5.5 dB point (fair axis -4.0 / -4.03, i.e. on the
  plotted axis) would bracket them; not run.

### v-15mb, R = 0.15, data Es/N0 -3.5 -3 dB (2026-11-16, ALL DONE, no Traceback) - with v-15ma; v-15mc running
Blind -3.60 [-3.67, -3.52] @1e-3, -2.93 [-2.99, -2.83] @1e-4. Interpolated over the pooled points.
| Variant | Predicted @1e-3 | Measured @1e-3 (gap) | Measured @1e-4 (gap) | Verdict |
|---|---|---|---|---|
| V6 CCSDS 131.0 ASM | -3.55 ... -3.35 | -3.44 (+0.16) | -2.98 (**-0.05**, tie) | hit |
| split64 ML L4 | -3.40 ... -3.30 | -3.41 (+0.19) | -3.09 (**-0.16**, beats blind) | hit |
| split64 ML (L3) | - | -3.34 (+0.26) | -2.74 (+0.19) | L4 gains 0.35 dB @1e-4 |
| CCSDS style (parent) | - | -3.40 (+0.20) | -3.06 (**-0.13**, beats blind) | as est5 |
| MIL-110 HF (parent) | - | -2.83 (+0.77) | -2.49 (+0.44) | - |
| V4 MIL-110 full | -2.48 ... -2.39 | -2.51 (+1.09) | -2.15 (+0.78) | hit |
| V5 CCSDS 131.2 real | -3.53 ... -3.18 | above -2.87 (1.5e-3 there): > +0.73 | open (v-15mc) | miss, much worse |
- Confirms the 0.15 @1e-4 picture: dense-preamble layouts with lobes (split64 L4, CCSDS style) beat blind by 0.13-0.16
  dB there, while blind leads by 0.16-0.26 dB @1e-3.

### v-25ma, R = 2/5, data Es/N0 0 0.5 dB (2026-11-16, ALL DONE, no Traceback; PROVISIONAL until v-25mb lands)
Blind 0.58 [0.55, 0.61] @1e-3. All sources still above 1e-3 at 0.5 dB raw: crossings extrapolated.
| Variant | BLER (fair axis) | Predicted @1e-3 | Extrapolated @1e-3 (gap) | Early read |
|---|---|---|---|---|
| V6 CCSDS 131.0 ASM | 8.9e-2 at 0.26, 4.2e-3 at 0.76 | 0.95 ... 1.10 | ~1.00 (+0.42) | hit |
| split64 ML L4 (= L3 packet for packet) | 7.0e-2 at 0.51, 2.5e-3 at 1.01 | 1.12 ... 1.17 | ~1.15 (+0.57) | hit |
| CCSDS style (parent) | 7.1e-2 at 0.51, 2.6e-3 at 1.01 | - | ~1.15 (+0.57) | - |
| V5 CCSDS 131.2 real | 1.4e-1 at 0.13, 1.5e-2 at 0.63 | 0.87 ... 1.12 | ~1.23 (+0.65) | likely miss, worse |
| MIL-110 HF (parent) | 6.9e-2 at 1.14, 2.3e-3 at 1.64 | - | ~1.76 (+1.18) | - |
| V4 MIL-110 full | 7.4e-2 at 1.47, 2.7e-3 at 1.97 | 2.07 ... 2.16 | ~2.12 (+1.54) | hit |

### v-15mc, R = 0.15, data Es/N0 -2.5 -2 -1 dB (2026-11-16, ALL DONE, no Traceback) - closes v-15m*
| Variant | New points (fair axis) | Measured @1e-3 (gap) | Measured @1e-4 (gap) | Verdict |
|---|---|---|---|---|
| V5 CCSDS 131.2 real | 3.5e-4 at -2.37, 7.9e-5 at -1.87, 6.3e-6 at -0.87 | **-2.74 (+0.86)** | **-1.95 (+0.98)** | miss, much worse (predicted -3.53 ... -3.18 @1e-3) |
| split64 ML (L3) | 3.1e-5 at -1.99, 8.3e-6 at -1.49 | -3.34 (+0.26) | -2.74 (+0.19) | unchanged (lobe-floor tail) |
| others | <= 1 error | as v-15mb | as v-15mb | unchanged |

### v-25mb, R = 2/5, data Es/N0 1 1.5 2 dB (2026-11-16, ALL DONE, no Traceback) - final with v-25ma
Blind 0.58 [0.55, 0.61] @1e-3. Crossings interpolated over the pooled points (1e-3 now bracketed for every source).
| Variant | New points (fair axis) | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|---|
| V6 CCSDS 131.0 ASM | 9.6e-5 at 1.26, 0 at 1.76 | 0.95 ... 1.10 | 0.95 | +0.37 | hit (edge) |
| split64 ML L4 (= L3) | 4.0e-5 at 1.51, 0 at 2.01 | 1.12 ... 1.17 | 1.12 | +0.54 | hit (edge) |
| CCSDS style (parent) | 5.8e-5 at 1.51, 0 at 2.01 | - | 1.14 | +0.56 | - |
| V5 CCSDS 131.2 real | 1.1e-3 at 1.13, 9.2e-5 at 1.63 | 0.87 ... 1.12 | 1.15 | +0.57 | close miss, worse (0.03 dB) |
| MIL-110 HF (parent) | 3.8e-5 at 2.14, 4.2e-6 at 2.64 | - | 1.74 | +1.16 | - |
| V4 MIL-110 full | 5.6e-5 at 2.47, 4.2e-6 at 2.97 | 2.07 ... 2.16 | 2.10 | +1.52 | hit |
- At 2/5 the closest of these is ASM (+0.37); the overall closest at 2/5 stays the Advantech wide preamble (+0.33).

### v-2mb, R = 1/2, data Es/N0 2.5 3 dB (2026-11-16, ALL DONE, no Traceback) - closes v-2m*
Every source <= 8.3e-6 at 2.5 dB raw except CCSDS 131.2 real (1.9e-4 at 2.63, 8.3e-6 at 3.13): no floors, the waterfalls
continue below 1e-4. The v-2ma crossings @1e-3 are final: 131.2 real 2.35 (+0.63; corrected, was 2.00), ASM 2.19 (+0.46), split L4 2.36
(+0.63), CCSDS style 2.38 (+0.65), MIL-110 HF 3.00 (+1.27), MIL-110 full 3.35 (+1.62).

### v-15w, R = 0.15, data Es/N0 -4.5 -4 -3.5 dB (2026-11-16, ALL DONE, no Traceback; @1e-4 open until v-15w2)
Blind -3.60 @1e-3, -2.93 @1e-4. Interpolated where bracketed.
| Variant | BLER (fair axis) | Predicted @1e-3 | Measured @1e-3 (gap) | @1e-4 (gap) | Verdict |
|---|---|---|---|---|---|
| WiFi pre128 (parent) | 2.5e-2 at -3.99, 1.7e-3 at -3.49, 1.2e-4 at -2.99 | - | -3.39 (+0.21) | ~-2.96 extrapolated (~-0.03, tie) | as est5 (+0.22) |
| V7b WiFi real320 lobes | 2.5e-2 at -3.32, 1.7e-3 at -2.82, 1.2e-4 at -2.32 | -2.73 ... -2.68 | -2.72 (+0.88) | ~-2.29 extrapolated (+0.64) | hit |
| V7a WiFi real320 | 3.5e-2 at -3.32, 8.8e-3 at -2.82, 5.3e-3 at -2.32 | fails (wrap floor) | fails in range (floor ~5e-3) | fails | hit |
- V7b = the parent shifted by its 0.67 dB extra preamble energy, packet counts almost identical (804 vs 807, 55 vs 56):
  the 320-symbol estimator plus lobes buys nothing over the 128-symbol one, as predicted.

### v-10ha, R = 1/10, data Es/N0 -5 -4.5 dB (2026-11-16, ALL DONE, no Traceback; v-10hb has -4 -3 -2)
Blind -4.78 [-4.86, -4.69] @1e-4.
| Variant | BLER (fair axis) | in-search | Predicted @1e-4 | Read |
|---|---|---|---|---|
| V3a DVB-S2 header90 | **3.1e-5 (15 / 480k) at -4.63**, 8.3e-6 (4) at -4.13 | 1.0000 | -4.82 ... -4.72 (+0.08 ... +0.18) | **already below 1e-4 at its lowest point: crossing < -4.63, may tie or beat blind** |
| DVB-S2 style (parent) | 1.27e-2 at -4.50, 5.6e-3 at -4.00 | 0.987, 0.994 | - | search-miss floor (as est5) |
- V3a's crossing is not bracketed. Its curve between the two points is shallow (x3.8 per 0.5 dB, 15 vs 4 errors), so
  a two-point extrapolation (~-5.1) is not trustworthy; the true crossing is somewhere in about -4.95 ... -4.65,
  i.e. from 0.17 dB better than blind to 0.13 dB worse. Bracketing it needs data Es/N0 -5.3 dB (fair axis -4.93, still
  on the plotted axis); -5.5 would plot at -5.13 and is not allowed. Not run.
- MACs: V3a was predicted at ~0.70 M per core at 1/10 (frame-sync scan) vs blind 0.200 M, so even a tie leaves blind
  ~3.5x cheaper.

### v-25w, R = 2/5, data Es/N0 0 ... 2 dB (2026-11-16, ALL DONE, no Traceback) - final
Blind 0.58 [0.55, 0.61] @1e-3. Interpolated (bracketed).
| Variant | BLER (fair axis) | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|---|
| WiFi pre128 (parent) | 3.2e-3 at 1.01, 7.9e-5 at 1.51 | - | 1.17 | +0.59 | - |
| V7b WiFi real320 lobes | 3.6e-3 at 1.68, 5.8e-5 at 2.18 | 1.82 ... 1.87 | 1.84 | +1.26 | hit |
| V7a WiFi real320 | 3.8e-3 at 1.68, 1.3e-4 at 2.18, 1.5e-5 at 3.18 | 2.35 ... 2.5 | **1.88** | +1.30 | **miss, in its favour (~0.5 dB)** |
- V7a: the wrap floor is ~1e-5 at 2/5 (in-search 0.9997-1.0), far below the 1e-3 target, so it only costs 0.04 dB
  there; the prediction assumed a larger wrap penalty. It does show at 1e-4 (1.3e-4 at 2.18 vs 5.8e-5 with lobes).

### v-10wb, R = 1/10, data Es/N0 -4 -3 -2 dB (2026-11-16, ALL DONE, no Traceback) - final with v-10wa
Blind -4.78 [-4.86, -4.69] @1e-4. Interpolated over the pooled points.
| Variant | New points (fair axis) | Predicted @1e-4 | Measured @1e-4 | Gap to blind | Verdict |
|---|---|---|---|---|---|
| WiFi pre128 (parent) | 1.9e-4 at -3.49, 3.3e-5 at -2.49 | - | -3.13 | +1.65 | search-miss tail |
| V7b WiFi real320 lobes | 2.2e-4 at -2.82, 2.5e-5 at -1.82 | -4.01 ... -3.96 | **-2.46** | **+2.32** | **miss, much worse** |
| V7a WiFi real320 | 7.2e-3 at -2.82, 4.0e-3 at -1.82, 1.9e-3 at -0.82 | fails | fails (wrap floor, ~2e-3 at -0.82) | - | hit |
- V7b's 1/10 tail is set by the coarse misses outside the +-4 lobes (in-search 0.9989 ... 0.9997 below -2.8 dB),
  not by the fine estimate: the prediction priced only energy and fine-estimate quality.

### v-15w2, R = 0.15, data Es/N0 -3 ... -1 dB (2026-11-16, ALL DONE, no Traceback) - final with v-15w
Blind -3.60 @1e-3, -2.93 [-2.99, -2.83] @1e-4. Interpolated.
| Variant | New points (fair axis) | Measured @1e-3 (gap) | Measured @1e-4 (gap) | Verdict |
|---|---|---|---|---|
| WiFi pre128 (parent) | 4.2e-5 at -2.49, 1.9e-5 at -1.99 | -3.39 (+0.21) | **-2.91 (+0.02, tie)** | - |
| V7b WiFi real320 lobes | 3.5e-5 at -1.82, 1.25e-5 at -1.32 | -2.72 (+0.88) | -2.26 (+0.67) | hit @1e-3 (-2.73 ... -2.68) |
| V7a WiFi real320 | 3.8e-3 at -1.82 ... 8.2e-4 at 0.18 | ~-0.05 (+3.55) | fails | hit (wrap floor; predicted ~3e-3 at -1 dB) |
- pre128 and V7b flatten below 1e-4 (x2-3 per 0.5 dB): a slow tail of coarse misses. Not a hard floor.

### v-10hb, R = 1/10, data Es/N0 -4 -3 -2 dB (2026-11-16, ALL DONE, no Traceback)
| Variant | New points (fair axis) | Read |
|---|---|---|
| V3a DVB-S2 header90 | 4.2e-6 (2) at -3.63, 8.3e-6 (4) at -2.63, 6.3e-6 (3) at -1.63 | flat ~6e-6 tail (2-4 errors per 480k), far below 1e-4; the 1e-4 crossing stays below -4.63 (not bracketed) |
| DVB-S2 style (parent) | 2.0e-3 at -3.50, 1.8e-4 at -2.50, 6.3e-6 at -1.50 | @1e-4: -2.32 (+2.46, pooled with e5-10); search misses |

- (2026-11-17) V3a measured MACs per core at 1/10: 0.63 M at -4.63, 0.51-0.60 M above (the CFO scan); blind 0.194 M at
  its crossing, so blind is ~3.2x cheaper per core even if V3a ties.

### v-2w, R = 1/2, data Es/N0 1.5 ... 3 dB (2026-11-17, ALL DONE, no Traceback) - final
Blind 1.73 [1.69, 1.76] @1e-3. Interpolated (bracketed).
| Variant | BLER (fair axis) | Predicted @1e-3 | Measured @1e-3 | Gap to blind | Verdict |
|---|---|---|---|---|---|
| WiFi pre128 (parent) | 2.7e-2 at 2.01, 4.6e-4 at 2.51 | - | 2.42 | +0.69 | - |
| V7b WiFi real320 lobes | 3.3e-2 at 2.68, 5.6e-4 at 3.18 | 3.08 ... 3.13 | 3.11 | +1.38 | hit |
| V7a WiFi real320 | 3.3e-2 at 2.68, 5.7e-4 at 3.18 | 3.1 ... 3.3 | 3.11 | +1.39 | hit (no wrap at 1/2: in-search 1.0000) |

## 10. Extra low point for V3a DVB-S2 header90 at R = 1/10 (predictions 2026-11-17, before the run)
**Why (user request 2026-11-17):** V3a is already below 1e-4 at its lowest point (3.1e-5, 15 / 480k at fair -4.63), so
its crossing is not bracketed and the comparison with blind (-4.78 [-4.86, -4.69]) is open (-4.95 ... -4.65).
Jobs v-10hla / v-10hlb (seeds 179 / 180, 480k each, pooled = 960k): header90 only, data Es/N0 -5.3 dB = fair axis
-4.93 dB (overhead 0.37 dB), inside the -5 dB limit. No code change. Runtime: v-10ha ran 2 SNRs x 2 sources in 5.4 h,
header90 (801-hypothesis scan) dominant, so ~2-3 h per job.

**Predicted BLER at -4.93:** the curve has a slow tail of ~6e-6 (2-4 errors per 480k from -4.1 up) plus a waterfall
part of ~2.5e-5 at -4.63. With the waterfall slope of the other dense layouts at 1/10 (x6 ... x27 per 0.5 dB, e5-10lo)
the 0.3 dB step gives x2.9 ... x7.2: BLER **0.8 ... 1.9e-4** (75-180 errors in 960k).

| Receiver | Predicted required SNR @1e-4 [dB] | Gap to blind [dB] | Verdict | MACs ratio blind / it |
|---|---|---|---|---|
| V3a DVB-S2 header90 | -4.92 ... -4.80 | -0.14 ... -0.02 | tie, possibly slightly better than blind (inside blind's CI) | 0.31x (it 0.63 M vs blind 0.194 M: blind 3.2x cheaper) |

Kill / flag rule: BLER < 1e-4 at -4.93 means V3a beats blind at 1/10 by more than 0.15 dB (outside blind's CI): report
it as a loss for blind (no point below -5 dB on the plotted axis, so the crossing would stay a bound).

### v-15h, v-15h2 (R = 0.15), v-25ha/hb/hc/h2 (R = 2/5), v-2ha (R = 1/2): DVB-S2 header90 and parent (2026-11-17, ALL DONE, no Traceback)
Interpolated (bracketed). MACs per core of V3a interpolated at its crossing (the 801-hypothesis CFO scan dominates).
| Rate, BLER | Blind | V3a DVB-S2 header90: predicted | measured (gap) | V3a MACs per core (blind / it) | DVB-S2 style (parent) | Verdict |
|---|---|---|---|---|---|---|
| 0.15, 1e-3 | -3.60 | -3.54 ... -3.44 | **-3.57 (+0.03, tie)** | ~0.77 M (0.34x: blind 2.9x cheaper) | -3.09 (+0.51) | hit at the edge, in its favour |
| 0.15, 1e-4 | -2.93 | - | **-3.23 (-0.30: beats blind)** | ~0.69 M (blind 3.8x cheaper) | -2.25 (+0.68) | the largest loss for blind so far (others -0.14 ... -0.20) |
| 2/5, 1e-3 | 0.58 | 1.01 ... 1.11 | 1.03 (+0.45) | ~0.83 M (blind 4.5x cheaper) | 1.12 (+0.54) | hit |
| 1/2, 1e-3 | 1.73 | 2.27 ... 2.37 | open (v-2hb / v-2h2 running): 2.7e-2 at 1.87 | 1.23 M at 1.87 | - | - |
- V3a beats its parent by 0.5-0.9 dB at 0.15: the dedicated 90-symbol header with a full-range scan has no search
  misses (in-search 1.0000 at every point), while the parent's M&M coarse stage leaves 0.1-0.5 % outside the window.
- Its tail flattens to 2-4 errors per 480k (~6e-6) above the waterfall at 0.15 and 1/10, like the 128-preamble floor.
