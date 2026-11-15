# DVB-RCS2 return-link burst synchronization: what the standard and the literature say, and which competitors to build

Literature scout report, 2026-11-15. No simulations were run. Every number below has a source and section. Numbers
marked **[derived]** are my own arithmetic from the cited numbers, not from a source.

How the sources were read: the ETSI PDFs could not be parsed by the normal fetch tool, so their text was read through a
public PDF-to-text reader (r.jina.ai, given only the public ETSI URL). Tables came out as flat text; the Table A-1 rows
below were rebuilt from it and **checked arithmetically**: burst length = payload symbols + preamble + postamble +
pilot sum, for every row used. The IEEE papers by Ali et al. are paywalled; only their abstracts / snippets were seen.

---

## Summary: recommended competitors (details in item 4)

| Name | Known symbols for 1024 data | Chain | Faithful source |
|---|---|---|---|
| **RCS2-PL** (ID 13 style, the main one) | preamble 32 + 53 single-symbol pilots (period 20) + postamble 31 = **116** (total 1140, 0.47 dB energy cost) | DA-KS: zero-filled r·conj(a) on all known symbols -> zero-padded FFT -> peak -> parabolic interpolation -> f, phase. Constant phase (faithful) **or** + pilot phase smoothing and linear interpolation (PA-SWI) | EN 301 545-2 Table A-1 ID 13; Griebel et al. 2021 Eqs. 2-7, 15-17; ESA patent US7409024 |
| **RCS2-PP** (ID 15 / 5 style, pilotless) | preamble 16 + postamble 16 = **32** (0.13 dB) | NDA 4th-power FFT over the whole burst + interpolation; 4-fold phase ambiguity from the 32 known symbols | Table A-1 IDs 5, 15; Griebel et al. Eqs. 11-14 |
| **Preamble-only + ML** (TR 6.2.2.1 assumption) | 128 contiguous (0.51 dB) | R&B / ML FFT on the preamble, constant phase | TR 101 545-4 cl. 6.2.2.1; Table A-1 IDs 32-39 (32-symbol preamble) |

---

## 1. DVB-RCS2 linear-modulation (TC-LM) burst structure

### 1.1 Rules (ETSI EN 301 545-2 V1.3.1, 2020-07)

- **Burst construction (cl. 7.3.6.1):** pilot blocks are evenly distributed with evenly sized payload sections between
  them. Pilot blocks are inserted until the pilot sum is reached, as long as enough payload symbols remain to sustain
  the pilot period; zero or more payload symbols may follow the last pilot block.
- **Pilot period (cl. 6.4.6.1 / 6.4.6.4, burst format fields):** `pilot_period` (12 bits) is the distance in symbols
  from the first symbol of one pilot block to the first symbol of the next; the first pilot block starts one pilot
  period after the last preamble symbol; 0 = no pilots. `pilot_block_len` = symbols per block; `pilot_sum` = total
  pilot symbols (pilot_sum = pilot_block_len means one midamble).
  - **[derived]** With block length 1, every Table A-1 row satisfies pilot_sum = floor(N_payload / (P - 1)), i.e.
    P - 1 data symbols, then 1 pilot, repeated; 0 ... P - 2 data symbols are left after the last pilot (ID 2 has 0).
- **Known-symbol content (cl. 7.3.7.1.2, 7.3.7.1.3):** preamble, pilot block and postamble together form one unique
  word (UW). Its bits are given per waveform in Annex A (column "UW (hex)") or signalled by the NCC (cl. 6.4.6.1);
  the UW length in symbols is preamble_len + pilot_block_len + postamble_len, m bits per symbol (2 for QPSK).
  Known symbols are mapped **with the same constellation as the payload** (QPSK for QPSK bursts). So the single
  pilot symbol of each pilot block is the **same symbol in every pilot block** (the UW holds one pilot block).
  The hex UW values themselves were not legible in the text extraction; they are in Annex A, Table A-1.
- **Pulse shaping (cl. 7.3.7.1.1):** root-raised-cosine, roll-off fixed at **0.20** in the text read (our chain uses
  0.25; not a problem for a comparison of synchronizers).
- **Transmitter accuracy (cl. 7.3.9):** carrier frequency better than 1e-8 RMS of nominal (7.3.9.3); symbol clock within
  20 ppm, time error within 1/20 symbol over a burst (7.3.9.2); burst start within 0.5 symbol (7.3.9.1).

### 1.2 Reference waveforms (EN 301 545-2 V1.3.1, Annex A, Table A-1), QPSK and BPSK rows

All pilot blocks are 1 symbol long. Overhead columns are **[derived]**.

| ID | Map | Rate | Burst (sym) | Payload (bytes / sym) | Pre | Post | Pilot period P | Pilot sum | Known total | Known / burst | Known / payload |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | QPSK | 1/3 | 664 | 38 / 456 | 155 | 27 | 18 | 26 | 208 | 31.3 % | 45.6 % |
| 2 | QPSK | 1/3 | 262 | 14 / 168 | 41 | 41 | 15 | 12 | 94 | 35.9 % | 56.0 % |
| **3** | QPSK | 1/3 | 536 | 38 / 456 | 27 | 27 | 18 | 26 | 80 | 14.9 % | 17.5 % |
| **4** | QPSK | 1/2 | 536 | 59 / 472 | 22 | 22 | 24 | 20 | 64 | 11.9 % | 13.6 % |
| 5 | QPSK | 2/3 | 536 | 85 / 510 | 13 | 13 | 0 | 0 | 26 | 4.9 % | 5.1 % |
| 6 | QPSK | 3/4 | 536 | 96 / 512 | 12 | 12 | 0 | 0 | 24 | 4.5 % | 4.7 % |
| 7 | QPSK | 5/6 | 536 | 108 / 519 | 9 | 8 | 0 | 0 | 17 | 3.2 % | 3.3 % |
| **13** | QPSK | 1/3 | 1616 | 123 / 1476 | 32 | 31 | 20 | 77 | 140 | 8.7 % | 9.5 % |
| **14** | QPSK | 1/2 | 1616 | 188 / 1504 | 25 | 25 | 25 | 62 | 112 | 6.9 % | 7.4 % |
| 15 | QPSK | 2/3 | 1616 | 264 / 1584 | 16 | 16 | 0 | 0 | 32 | 2.0 % | 2.0 % |
| 16 | QPSK | 3/4 | 1616 | 298 / 1590 | 13 | 13 | 0 | 0 | 26 | 1.6 % | 1.6 % |
| 17 | QPSK | 5/6 | 1616 | 333 / 1599 | 9 | 8 | 0 | 0 | 17 | 1.1 % | 1.1 % |
| 32 | QPSK | 1/2 | 832 | 100 / 800 | 32 | 0 | 0 | 0 | 32 | 3.8 % | 4.0 % |
| 33 | QPSK | 3/4 | 566 | 100 / 534 | 32 | 0 | 0 | 0 | 32 | 5.7 % | 6.0 % |
| 34 | QPSK | 1/2 | 1392 | 170 / 1360 | 32 | 0 | 0 | 0 | 32 | 2.3 % | 2.4 % |
| 35-39 | QPSK | 3/4 ... 6/7 | 810 ... 2660 | | 32 | 0 | 0 | 0 | 32 | 1.2-4.0 % | |
| 40 | BPSK | 1/3 | 1868 | 59 / 1416 | 313 | 56 | 18 | 83 | 452 | 24.2 % | 31.9 % |
| 41 | BPSK | 1/3 | 1612 | 59 / 1416 | 57 | 56 | 18 | 83 | 196 | 12.2 % | 13.8 % |
| 42 | BPSK | 1/3 | 3236 | 123 / 2952 | 65 | 64 | 20 | (155 [derived]) | ~284 | ~8.8 % | |
| 43 | BPSK | 1/2 | 3236 | 188 / 3008 | 52 | 51 | 25 | (125 [derived]) | ~228 | ~7.0 % | |

(The pilot sums of IDs 42 / 43 were illegible; the values in brackets are burst - payload - pre - post.)

**Answers to the specific questions:**
- **Closest to us (1024 QPSK data symbols, low rate):** ID 13 (QPSK 1/3, 1476 payload symbols) and ID 14 (QPSK 1/2);
  at 536 symbols, IDs 3 and 4. For our lowest SNR (-5 dB), the BPSK 1/3 bursts IDs 41 / 42 are the closest operating
  points (see 1.3).
- **Are pilots on by default for QPSK?** Only for the low rates: **on for QPSK 1/3 and 1/2 (IDs 1-4, 13, 14)**, off for
  QPSK 2/3 and higher (IDs 5-7, 15-17) and off for the preamble-only family IDs 32-39. There is no "default" beyond
  the reference table; the NCC can signal any burst format (cl. 6.4.6.1).
- **Pilot period options:** in the reference waveforms **15, 18, 20, 24, 25** symbols (QPSK/BPSK); in the format
  signalling any 12-bit value 0 ... 4095 (cl. 6.4.6.1; the MathWorks generator exposes the same range).
- **Pilot field length:** always **1 symbol** in Table A-1.
- **Pattern of the design:** low-rate bursts spread their known symbols (pre + post + distributed pilots, 7-18 % of
  the burst); high-rate bursts keep only a short pre + post (1-5 %); IDs 32-39 use a 32-symbol preamble only. The DVB
  project describes the balance as chosen so that synchronisation sensitivity matches decoding sensitivity
  ([dvb.org](https://dvb.org/?p=8033), snippet).

### 1.3 Operating points (TR 101 545-4 V1.1.1, cl. 10.2.1 and 10.4.3.2)

- AWGN, **ideal synchronization**, normalized max-log-MAP turbo, up to 8 iterations (cl. 10.2.1):

| ID | Burst | Es/N0 at PER 1e-3 | Es/N0 at PER 1e-5 | Table |
|---|---|---|---|---|
| 3 | 536, QPSK 1/3 | -0.27 dB | 0.22 dB | 10.5 |
| 4 | 536, QPSK 1/2 | 1.92 dB | 2.34 dB | 10.5 |
| 13 | 1616, QPSK 1/3 | -0.80 dB | -0.51 dB | 10.6 |
| 14 | 1616, QPSK 1/2 | 1.49 dB | 1.71 dB | 10.6 |

  The BPSK 1/3 control-burst row of Table 10.4 runs from -4.00 to -2.98 dB over PER 1e-1 ... 1e-5 (ID not legible).
- **Real implementation loss** (bench prototype, Table 10.16, cl. 10.4.3.2): QPSK 1/3 at PER 1e-5 needs 0.0 dB instead
  of -0.51 dB (**about 0.5 dB**), QPSK 1/2 2.3 vs 1.71 dB (**about 0.6 dB**), 16QAM 5/6 about 0.96 dB. The loss
  includes everything (sync, phase noise, quantization); it is not broken down.
- **Comparability:** our R = 1/10 at -5 dB Es/N0 is **about 4 dB below the lowest QPSK DVB-RCS2 operating point**
  (-0.8 dB) and near the BPSK 1/3 points. DVB-RCS2 known-symbol designs were never tuned for -5 dB QPSK.

---

## 2. Receiver algorithms in TR 101 545-4

**The main finding: TR 101 545-4 V1.1.1 does not recommend any burst-detection, frequency or phase algorithm for the
linear-modulation (TC-LM) bursts.** Clause 6 covers synchronization only at system level (Doppler, frequency budget);
clause 6.3.1-6.3.2 cover the turbo decoder; the only demodulator description in the clause-6 range is for **CPM**
(cl. 6.3.3.2). I read characters 0-620 000 of 705 000 (the unread tail is the last annexes and the bibliography).
The 2026 revision V1.2.1 has the same clause titles in its table of contents (6.1, 6.2, 10.1.1, 10.1.2, 10.2.1) and
no TC-LM synchronizer clause (only its table of contents was read).

What the TR does give:

- **(a) Burst / UW detection.** TC-LM: nothing. CPM receiver (cl. 6.3.3.2, Fig. 6.8): "burst detector (UW detector)",
  correlation of the received signal with the preamble and midamble pilot fields. Annex D (time-slot-sharing echo
  canceller, cl. D.3-D.4): a matched filter **split into sections whose outputs are combined over frequency-error
  hypotheses**, largest correlation in the timing window, parabolic interpolation of the delay, Farrow interpolator.
  No thresholds or false-alarm numbers are given anywhere. (The MathWorks DVB-RCS2 example uses differential
  correlation averaged over a burst interval for burst start; that is MathWorks, not the TR.)
- **(b) Frequency estimation.**
  - TC-LM: none. Cl. 6.2.2.1 **assumes "frequency is estimated on the preamble"** and derives the burst length for a
    worst-case in-burst phase rotation of **4 degrees** caused by frequency drift (Tables 6.5 / 6.6, e.g. Ku vehicular
    6.8 ms). It adds that estimating frequency over the whole burst, or tracking the phase, relaxes this a lot.
  - CPM (cl. 6.3.3.2): **data-aided Rife-Boorstyn**: FFT of the preamble correlation and of the midamble correlation,
    zero-padded to a common length, the two spectra combined, peak = frequency, with an R&B pruning factor.
  - Annex D: **Mengali-Morelli** fine frequency estimator after the sectioned-MF coarse search. Annex C (SC-FDMA):
    frequency from pilot tones, assumes the error is below one bin.
  - **Acquisition range:** the TR says the tolerable burst frequency offset is **not specified by DVB-RCS2**; the
    analysis assumes **0.5 % to 3 % of the symbol rate** (cl. 6.2.2; Tables 6.3 / 6.4 give the minimum symbol rate per
    terminal class: fixed Ku terminal 1590 Hz total error -> 53 ksym/s at 3 %, 318 ksym/s at 0.5 %). Our |f| <= 0.03
    is the top of this range.
  - Frequency budget (cl. 10.1.2, Table 10.2): terminal 6e-8 worst case (870 Hz Ku), gateway 1e-8, satellite 1e-7,
    Doppler 1e-8; total **1590 Hz (Ku), 3784 Hz (Ka)**.
- **(c) Phase estimation / tracking.** TC-LM: none. CPM: Bayesian phase tracking inside the BCJR, phase quantized to R
  levels; a simplified version costs about 1 dB at PER 1e-3 (cl. 6.3.3.2). CRDSA annex (B.3.1): phase re-estimated per
  burst by correlation with the already-demodulated replica. No pilot interpolation is described anywhere.
- **(d) NDA stage.** None in the TR.
- **Phase noise mask** (cl. 10.1.1, Table 10.1, RCST transmit, SSB dBc/Hz): 10 Hz: -16 / -30, 100 Hz: -54 / -60, 1 kHz:
  -64 / -70, 10 kHz: -74, 100 kHz: -89, >= 1 MHz: -106 (two columns for higher and lower symbol rates; the column
  boundary, about 128 kBaud, was garbled in the extraction: check in the PDF before quoting). Other link sources are
  assumed at least 10 dB lower. **Not checked:** how this mask maps to our Wiener linewidth x Ts = 1e-5 ... 3e-4; it
  depends on the symbol rate, which our setup does not fix.

### 2.1 The algorithms actually used for DVB-RCS2 TC-LM bursts (Griebel, Wasenmuller, Wehn, Adv. Radio Sci. 2021)

Since the TR gives no TC-LM algorithm, the best documented DVB-RCS2 TC-LM chain is this paper (full text read; its
burst-type numbers are the Table A-1 waveform IDs: "burst 3" has 80 known symbols, 26 pilots, 536 symbols = ID 3).
All formulas below are from its Eqs. 1-20 (normalized frequency in cycles/symbol, r(l) the symbol-rate MF output):

- **DA-KS (all known symbols):** z(l) = r(l) c*(l) at the known positions (preamble, pilots, postamble), 0 at data
  positions (Eq. 2); X(k) = FFT_N of the zero-padded z (Eq. 3); k_f = argmax |X(k)| (Eq. 4);
  f = k_f / N (or (k_f - N)/N) (Eq. 5); phase = arg X(k_f) (Eq. 6); correction r(l) exp(-j(2 pi f l + phase)) (Eq. 7).
  This is the Rife-Boorstyn (periodogram ML) estimator over the known symbols.
- **DA-PL (pilots only):** the same on the pilot sub-sequence, f = k_f / (N P) (Eq. 9), phase = arg X(k_f) - 2 pi f S
  with S the index of the first pilot (Eq. 10). Unambiguous only for **|f| < 1/(2P)** [derived from Eq. 9].
- **NDA (4th power):** z(l) = |r(l)| exp(j M arg r(l)), M = 4 (Eq. 11); f = k_f / (M N) (Eq. 12); phase =
  arg X(k_f) / M (Eq. 13) with the M-fold ambiguity phase + m 2 pi / M resolved by correlation with the known
  symbols (Eq. 14; the extracted equation was garbled, this reading follows the text). Range |f| < 1/8 [derived].
- **Interpolation** (to shrink the FFT): parabolic on magnitudes, delta = 0.5 (|X_r| - |X_l|) / (2|X_kf| - |X_r| -
  |X_l|) (Eq. 15), k = k_f + delta (Eq. 16); phase linearly interpolated between the peak and the neighbour on the
  delta side (Eq. 17). Energy version: same on |X|^2 (Eqs. 18-19) and a linearly interpolated complex X (Eq. 20).
- **No phase tracking:** frequency and phase are assumed constant over the burst; one phase estimate per burst.
- **Which method per burst:** ID 3, 4: DA-KS (NDA too poor at that SNR, too few pilots for DA-PL); ID 5, 33
  (no pilots): NDA; ID 8, 21, 42: DA-PL; ID 42 at 3 % CFO: **NDA needed** (DA-PL range too small).
- **CFO range used:** uniform up to 1.5 % of Rs; tolerable range quoted as 0.5-3 % (from the TR).
- **Numbers:** for ID 3 (DA-KS) without interpolation the FFT must be about 16x the burst length (8192 points);
  with either interpolation 2048 points have no loss. ID 4: 1024 points + magnitude interpolation (zero-padding
  factor about 1.9); doubling the FFT gains 0.1 dB at FER 1e-3, 0.2 dB at 1e-5. ID 42 DA-PL + interpolation: about
  0.1 dB (FER 1e-3) / 0.2 dB (1e-5) from the reference; ID 5 NDA: >= 1024 points, magnitude interpolation very close
  to reference. FPGA (Kintex-7, 350 MHz, max burst 4096): interpolation costs about 2000 FF, 1000 LUT, 13 DSP and
  raises throughput from 22.9 to 90.9 Msym/s for ID 3. SNR values are not given in the text (figures only).

**Important for our CFO range [derived]:** DVB-RCS2 pilot periods 18, 20, 24, 25 give pilot-only ranges 1/(2P) =
0.0278, 0.025, 0.0208, 0.020 cycles/symbol, **all below our 0.03**. With DA-KS the pre/postamble break the 1/P alias,
so DA-KS (or NDA) must be used, not DA-PL, and the FFT must search the full +-0.03. For the C1 layout below the
alias lobe at f +- 1/20 keeps the 53 pilots coherent but only a small part of the 63 pre/post symbols (32-symbol
block response at 0.05 offset about 0.19), so its height is roughly 0.56 of the true peak [derived, rough].

---

## 3. Published DVB-RCS2 burst-receiver and pilot-aided phase papers

| Paper | Algorithm chain | CFO range | Reported losses / numbers | What I read |
|---|---|---|---|---|
| Griebel, Wasenmuller, Wehn, "Interpolation techniques for FFT-based carrier synchronization ... DVB-RCS2", Adv. Radio Sci. 19, 2021 | DA-KS / DA-PL / NDA R&B FFT + parabolic interpolation; constant phase | up to 1.5 % (3 % needs NDA) | 0.1-0.2 dB from reference; FFT 4x smaller with interpolation | full text (tables are images, not read) |
| Ali, Wasenmuller, Wehn, "Feedforward carrier synchronization for pilotless bursts of DVB-RCS2", CSNDSP 2014, pp. 342-347 | feedforward frequency + phase for pre/post-only bursts at very low SNR; four FPGA architectures compared | not seen | not seen | abstract snippet only |
| Ali, Wasenmuller, Wehn, "Hardware implementation issues of carrier synchronization for pilot-symbol assisted bursts: a case study for DVB-RCS2", ICSPCS 2014 | two methods for pilot-assisted bursts, one IP core, Virtex-6 | not seen | not seen | abstract snippet only |
| MathWorks, "DVB-RCS2 link simulation with RF impairments ... TC-LM" | burst start by differential correlation; CFO by pilot-period differential correlation over the pilots | standard: 3 %; their sync: 10 kHz at 1 Msym/s (1 %) | ID 21, 15.5 dB, PER = 0 over 191 bursts | full page |
| Barbieri, Colavolpe, "On pilot-symbol-assisted carrier synchronization for DVB-S2 systems", IEEE T-BC 2007 (DVB-S2, not RCS2) | coarse DA M&M on the preamble; fine reduced M&M on distributed pilots; **3-7 frequency candidates chosen by the LDPC syndrome**; phase by forward-backward Tikhonov (CBC) smoother over the frame | pilot-spacing limited | CBC phase-noise loss < 0.1 dB (QPSK, 8PSK, 16APSK); poor at 1 Mbaud with the standard pilots | full text |
| ESA patent US7409024 (Ginesi, Fittipaldi, Bigi, De Gaudenzi), pilot-aided phase synchronization (DVB-S2) | per-pilot-block ML phase arg sum r c*; unwrapping; linear (PA-LI), Wiener (PA-WI) or Wiener-at-pilots + linear (PA-SWI) interpolation | cycle slip if f >= 1/(2 L_s) | QPSK jitter target 6-8 deg; PA-LI fails at 2 % overhead; DD loops only for slots > ~1000 symbols | 100 000 of 141 000 characters |
| Ying, Ghogho, "Optimal pilot placement for frequency offset estimation and data detection in burst transmission systems", IEEE Comm. Lett. 2005 | CRB analysis | quasi-static flat fading | **half of the pilots at the start, half at the end is optimal** for CFO and detection | abstract |
| Spalvieri et al., "Optimal filtering in pilot-aided carrier recovery", 2009 | Wiener vs suboptimal pilot filters | | gap grows with pilot spacing and SNR; ~0.35 dB at 40 dB SNR | search snippet only (403) |
| Casini, De Gaudenzi, Ginesi, "DVB-S2 modem algorithms design and performance over typical satellite channels", IJSCN 2004 | DVB-S2 modem incl. pilot-aided phase (linear interpolation according to secondary sources) | | not seen | abstract snippet only |

**Not found:** any paper that studies DVB-RCS2 TC-LM pilot-aided phase interpolation under phase noise, or any
DVB-RCS2 burst-sync result at QPSK Es/N0 below about -1 dB. The Ali et al. 2014 full texts were not accessible.

---

## 4. Recommendation

### 4.1 Competitors (all pilots are extra symbols; energy charged as 10 log10((1024 + K)/1024))

Timing and burst position: assume known (genie), as Griebel et al. do; the TR gives no TC-LM detector to copy.

**C1. RCS2-PL: ID 13 layout scaled to 1024 data symbols (the main DVB-RCS2 competitor).**
- Layout: preamble 32 | then 53 x (19 data + 1 pilot) | 17 data | postamble 31. Pilot sum = floor(1024/19) = 53.
  K = 116 known symbols, burst 1140, **0.47 dB** energy cost. All pilot symbols equal (one UW pilot symbol); preamble
  and postamble a fixed random QPSK sequence (the real UW hex was not legible).
- Variant with the same 128-symbol budget as our split NN: preamble 32 | 64 x (16 data + 1 pilot), i.e. P = 17,
  0 data left after the last pilot (allowed, as in ID 2) | postamble 32: K = 128, 0.51 dB. Pilot-only range
  1/34 = 0.0294 < 0.03, so DA-KS over all known symbols is still needed.
- Low-SNR variant (ID 42 BPSK proportions, closer to -5 dB): preamble 65, P = 20 (53 pilots), postamble 64: K = 182,
  0.71 dB.
- Frequency + phase (faithful, Griebel Eqs. 2-7, 15-17): z = r c* on all known symbols, zeros elsewhere; FFT N >= 2 x
  1140 -> 4096 points; magnitude-parabolic interpolation; search the full +-0.03; phase = interpolated arg X.
  **C1a = constant phase over the burst (faithful to the paper).**
- **C1b = C1a + pilot phase tracking (ESA PA-SWI style):** after the CFO is removed, smooth the known-symbol phasors
  z(l) e^{-j 2 pi f l} with a window of K_w pilots (or a Wiener filter), take arg, unwrap, then linear interpolation
  to the data symbols. [derived] For a Wiener phase with sigma^2 = 2 pi (linewidth x Ts) per symbol and Es/N0 = SNR,
  the window error variance is about 1/(2 K_w SNR) + sigma^2 K_w P / 12, minimized at K_w = sqrt(6 / (SNR sigma^2 P)).
  At -5 dB, P = 20: linewidth x Ts 1e-5 -> K_w = 123 (use all 53, residual small); 1e-4 -> K_w = 39 pilots,
  std about 0.29 rad (16 deg); 3e-4 -> K_w = 22, about 0.37 rad (21 deg). Both exceed the ~6-8 deg QPSK jitter target
  of the ESA patent, so **pilot-only DVB-RCS2 layouts are expected to fail at -5 dB with linewidth >= 1e-4** unless
  a decision-directed or code-aided stage is added (not in any DVB-RCS2 source). This is a back-of-envelope estimate;
  the simulation must confirm it.

**C2. RCS2-PP: pilotless pre/post (ID 15 / ID 5 style).**
- Layout: preamble 16 | 1024 data | postamble 16; K = 32, 0.13 dB.
- Chain (Griebel Eqs. 11-14): 4th-power NDA FFT over all 1056 symbols, interpolation, phase / 4 and the 4-fold
  ambiguity resolved with the 32 known symbols. Constant phase. This is close to our own fast path, so it isolates
  what our grid search + code-aided stages add.

**C3. Preamble-only + ML (the TR 6.2.2.1 assumption).**
- 128 contiguous preamble symbols (0.51 dB); R&B FFT (= ML) frequency + phase on the preamble; constant phase.
  DVB-RCS2's own preamble-only family (IDs 32-39) uses only 32 symbols and is meant for rates >= 1/2.

### 4.2 Is "128-symbol contiguous preamble + ML" a fair modern competitor?

It is a **fair classic baseline, not a modern one**. It is exactly what TR 101 545-4 cl. 6.2.2.1 assumes ("frequency
estimated on the preamble"), and the CRB argument and Ying-Ghogho 2005 show it is the **worst** placement of a fixed
pilot budget for CFO: the CRB scales with the spread of the known positions, and half at each end is optimal. It also
has no way to follow phase noise across 1024 data symbols. Keep it as the lower anchor; do not present it as the
state of the art.

### 4.3 Strongest pilot-aided baseline in the literature for short bursts at very low SNR

No source found studies QPSK at Es/N0 about -5 dB with DVB-RCS2-style bursts. Combining what was read:
1. **Spread known symbols + joint ML (DA-KS / R&B over all of them):** optimal placement is split (Ying-Ghogho);
   DVB-RCS2 low-rate bursts use pre + post + pilots and DA-KS (Griebel).
2. **Code-aided resolution of the remaining ambiguity:** Barbieri-Colavolpe pick among 3-7 frequency candidates with
   the decoder (LDPC syndrome) and smooth the phase with a forward-backward (CBC) recursion. This is the same idea as
   our split-pilot "quarter" layout + CRC lobe search (README A.13), which is therefore already the strongest kind of
   pilot-aided baseline; the DVB-RCS2 competitors C1-C3 are weaker by design (no decoder in the loop).
3. For phase noise, Wiener / forward-backward smoothing over pilots beats linear interpolation (ESA patent, Spalvieri),
   and PLL / DD loops are poor for slots < ~1000 symbols (ESA patent).

---

## 5. Source table

| # | Source | Year | Link | Read | Relevance |
|---|---|---|---|---|---|
| 1 | ETSI EN 301 545-2 V1.3.1, DVB-RCS2 Part 2 Lower layers | 2020 | [etsi.org PDF](https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.03.01_60/en_30154502v010301p.pdf) | full text of cl. 6.4.6, 7.3.6-7.3.9 and Annex A Table A-1 (via text reader) | high: burst layout |
| 2 | ETSI TR 101 545-4 V1.1.1, Guidelines | 2014 | [etsi.org PDF](https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.01.01_60/tr_10154504v010101p.pdf) | characters 0-620 000 of 705 000 (cl. 1-10, Annexes A-D) | high: no TC-LM sync algorithm; CFO 0.5-3 %; losses |
| 3 | ETSI TR 101 545-4 V1.2.1 | 2026 | [etsi.org PDF](https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf) | table of contents only | medium |
| 4 | Griebel, Wasenmuller, Wehn, Adv. Radio Sci. 19, 59-70 | 2021 | [ars.copernicus.org](https://ars.copernicus.org/articles/19/59/2021/) | full HTML text; tables 1-2 are images, not read | high: the DVB-RCS2 TC-LM chain |
| 5 | Ali, Wasenmuller, Wehn, CSNDSP 2014 | 2014 | [IEEE 6923851](https://ieeexplore.ieee.org/document/6923851/), [dblp](https://dblp.org/rec/html/conf/csndsp/AliWW14) | search-result abstract snippet | medium (pilotless bursts) |
| 6 | Ali, Wasenmuller, Wehn, ICSPCS 2014 | 2014 | [IEEE 7021078](https://ieeexplore.ieee.org/document/7021078/) | search-result abstract snippet | medium |
| 7 | MathWorks dvbrcs2WaveformGenerator | - | [mathworks.com](https://www.mathworks.com/help/satcom/ref/dvbrcs2waveformgenerator-system-object.html) | full page | medium: field ranges |
| 8 | MathWorks DVB-RCS2 TC-LM link example | - | [mathworks.com](https://www.mathworks.com/help/satcom/ug/end-to-end-dvb-rcs2-simulation-with-rf-impairments-and-corrections-for-tc-lm-bursts.html) | full page | medium: a working pilot-based chain |
| 9 | Barbieri, Colavolpe, IEEE T-Broadcasting 53(3) | 2007 | [unipr PDF](https://www.tlc.unipr.it/colavolpe/papers/j36.pdf) | full text (via text reader) | high: code-aided candidate choice + phase smoother |
| 10 | US7409024B2, ESA pilot-aided phase synchronization | 2008 | [Google Patents](https://patents.google.com/patent/US7409024) | 100k of 141k characters | high: PA-LI / PA-WI / PA-SWI |
| 11 | Ying, Ghogho, IEEE Comm. Lett. 9(6) | 2005 | [White Rose](https://eprints.whiterose.ac.uk/id/eprint/691/) | abstract | high: split placement optimal |
| 12 | Spalvieri et al., J. Elec. Comp. Eng. | 2009 | [Wiley](https://onlinelibrary.wiley.com/doi/10.1155/2009/645615) | search snippet only (403) | medium |
| 13 | Casini, De Gaudenzi, Ginesi, IJSCN 22(3) | 2004 | [bohrium index](https://www.bohrium.com/paper-details/dvb-s2-modem-algorithms-design-and-performance-over-typical-satellite-channels/812347569408573441-2825) | abstract snippet only | low-medium |
| 14 | DVB project page on DVB-RCS2 | - | [dvb.org](https://dvb.org/?p=8033) | snippet | low |

Comparability: DVB-RCS2 uses turbo codes, roll-off 0.2, CFO budgets in Hz tied to symbol rates of 53 ksym/s and up,
a phase-noise mask (not a Wiener process), and operates at Es/N0 >= about -1 dB for QPSK. Our polar CA-SCL-8 at
-5 dB, Wiener phase noise and 0.25 roll-off make all their dB losses indicative only.
