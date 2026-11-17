# Griebel, Wasenmüller, Wehn, Adv. Radio Sci. 19, 59-70 (2021): full analysis as a competitor / idea

Literature scout report, 2026-11-15. No simulations were run. Numbers marked **[fig]** were read by eye from the
paper's FER figures (the PNGs were fetched and viewed; reading accuracy about +-0.03 dB on the Es/N0 axis). Numbers
marked **[derived]** are my own arithmetic.

**Is this "Griebel et al. 2021"? Yes.** It is entry **C4** in `BLIND_IMPLEMENTATION/REFERENCES.md`, item 4 / section 2.1
of `lit_dvbrcs2.md`, #23 in `lit_blind_cfo.md`, and the source cited in `est4/estimators.py` for `rb` and `nda4`.
Two corrections to our existing entry: the authors are **Oliver** Griebel and **Uwe** Wasenmüller (REFERENCES.md has
"P." and "M."), and the real title is given below. The earlier reads said "tables 1-2 are images, not read"; this time
Tables 1-3 were read from the article XML and all FER figures (3-9) were viewed.

---

## 1. Reference and setting

- **Reference:** O. Griebel, U. Wasenmüller, N. Wehn, "Communication Performance vs. Implementation Trade-offs of
  Interpolation Techniques for FFT-Based Carrier Synchronization exemplified on DVB-RCS2", *Advances in Radio Science*
  19, 59-70, 2021 (published 17 Dec 2021), doi:10.5194/ars-19-59-2021, CC BY 4.0. TU Kaiserslautern, Microelectronic
  Systems Design group.
- **Links:** HTML https://ars.copernicus.org/articles/19/59/2021/ , PDF
  https://ars.copernicus.org/articles/19/59/2021/ars-19-59-2021.pdf , XML (tables)
  https://ars.copernicus.org/articles/19/59/2021/ars-19-59-2021.xml
- **Read depth:** full text (HTML + XML incl. MathML of Eqs. 1-20, Tables 1-3), Figures 2, 3-9, 10 viewed. The PDF
  itself could not be rendered here (no poppler); the XML is the same content.
- **Code:** "based on proprietary libraries, which are not publicly available"; the formulas are the method.

**System.** DVB-RCS2 return link, TC-LM (turbo-coded linear modulation) TDMA bursts, ETSI EN 301 545-2. 40 linear
burst types simulated (~3600 simulations), 7 shown. Symbol-rate model (Fig. 2: TC encoder -> mapper -> burst
construction -> e^{j(2 pi f0 l + phi)} -> + n(l) -> carrier sync -> demapper -> TC decoder; no pulse shaping, no
timing: "gain control, timing synchronization and frame detection ... carried out properly"). AWGN. Decoder: 16-state
duo-binary turbo, max-log-MAP, extrinsic scaling 0.75, 8 iterations, 6-bit LLRs; 8-bit I/Q input (bit-true vs float
"negligible difference").

**Burst types shown (Table 1, from the XML; all pilot blocks 1 symbol):**

| Burst type | Length (sym) | Map | Pre | Post | Pilots | Pilot period P | Known total [derived] | Known / burst [derived] | Pilot energy charge 10log10(L / data) [derived] |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 536 | QPSK (1/3) | 27 | 27 | 26 | 18 | 80 | 14.9 % | 0.70 dB |
| 4 | 536 | QPSK (1/2) | 22 | 22 | 20 | 24 | 64 | 11.9 % | 0.55 dB |
| 5 | 536 | QPSK (2/3) | 13 | 13 | - | - | 26 | 4.9 % | 0.22 dB |
| 8 | 536 | 8PSK | 10 | 9 | 57 | 9 | 76 | 14.2 % | 0.66 dB |
| 21 | 1616 | 16QAM | 10 | 9 | 159 (text: 157) | 10 | 178 | 11.0 % | 0.51 dB |
| 33 | 566 | QPSK (3/4) | 32 | - | - | - | 32 | 5.7 % | 0.25 dB |
| 42 | 3236 | BPSK | 52 | 51 | 125 | 25 | 228 | 7.0 % | 0.32 dB |

(Code rates in brackets from EN 301 545-2 Table A-1, not from the paper. Burst type 42 here has the parameters that
`lit_dvbrcs2.md` lists as V1.3.1 waveform ID 43 (52 / 51 / P 25 / 125); either the paper's numbering or our earlier
flattened-table reading of IDs 42 / 43 is off by one. IDs 3, 4, 5, 8, 13, 14, 21, 33 agree between the paper, EN 301
545-2 V1.1.1 and V1.3.1.)

- **Modulation:** BPSK, QPSK, 8PSK, 16QAM; the QPSK cases are the ones comparable to us.
- **CFO range:** "uniformly distributed frequency offset up to 1.5 % of the symbol rate" = **|f| <= 0.015
  cycles/symbol** [derived], half of our 0.03. The tolerable range quoted from TR 101 545-4 is 0.5-3 % = 0.005-0.03
  cycles/symbol; at 3 % the paper says DA-PL fails and NDA is needed (burst 42).
- **Phase:** "random phase offset", distribution not stated (constant per burst).
- **SNR axis:** **Es/N0 per burst symbol** (axis label "E_S/N_0 in [dB]" on Figs. 3-9); the pilot energy is NOT
  charged (the reference curve uses the same burst). Ranges shown: burst 42 (BPSK) -4.25 ... -3.0 dB; burst 3 (QPSK 1/3)
  -0.75 ... +0.5 dB; burst 4 (QPSK 1/2) 1.5 ... 2.75 dB; bursts 5, 33 (QPSK 2/3, 3/4) 3.25 ... 6.25 dB; burst 8 (8PSK)
  7.25 ... 8.5 dB; burst 21 (16QAM) 10.25 ... 11 dB.
- **Reference curve:** "exact estimation of phase and frequency offset by a magic genie" (= our genie). Consistency
  check [fig]: reference at FER 1e-3 is -0.23 dB (burst 3) and 1.97 dB (burst 4) vs the TR 101 545-4 ideal-sync values
  -0.27 and 1.92 dB (lit_dvbrcs2.md 1.3): agreement within 0.05 dB.
- **No RMSE, no CRB, no outlier / acquisition statistics** anywhere in the paper: only FER curves and FPGA numbers.
  There is no two-stage estimator and no refinement step: one FFT, one peak, one interpolation.

## 2. The algorithm, step by step (Eqs. 1-20 as in the article MathML)

Signal (Eq. 1): r(l) = s(l) e^{j(2 pi f_o l + phi)} + n(l), l = 0 ... L-1, symbol-rate, f_o in cycles/symbol.

**DA-KS: data-aided over all known symbols (pre + pilots + post)**
1. Eq. 2: z(l) = r(l) c*(l) at known positions, z(l) = 0 at data positions (length L, the whole burst).
2. Eq. 3: X(k) = sum_{n=0}^{N-1} x(n) e^{-j 2 pi k n / N}, x = z zero-padded to N.
3. Eq. 4: k_f = argmax_k |X(k)| over **all N bins** (no restriction to the expected CFO range).
4. Eq. 5: f = k_f / N if k_f < N/2, else (k_f - N)/N.
5. Eq. 6: phi = arg X(k_f) (phase referred to l = 0, the burst start).
6. Eq. 7: u(l) = r(l) e^{-j(2 pi f l + phi)} (constant phase over the burst; no tracking).

**DA-PL: pilots only** (sub-sequence of the L_P pilots, spacing P, S symbols before the first pilot)
- Eq. 8: z(l) = r_p(l) c_p*(l); Eq. 9: f = k_f / (N P) (or (k_f - N)/(N P)); Eq. 10: phi = arg X(k_f) - 2 pi f S.
  Unambiguous only for |f| < 1/(2P) [derived].

**NDA: non-data-aided, M-th "power"**
- Eq. 11: z(l) = |r(l)| e^{j M arg r(l)}, M = 4 for QPSK (magnitude kept at power 1: a Viterbi-and-Viterbi
  nonlinearity F(rho) = rho, NOT r^M); over the whole burst.
- Eq. 12: f = k_f / (M N) (or (k_f - N)/(M N)); Eq. 13: phi_NDA = arg X(k_f) / M, in (-pi/M, pi/M].
- Eq. 14: phi = phi_NDA + m 2 pi / M, 0 <= m < M (MathML prints "m pi/(M/2)" and "0 <= i < M": typos);
  m resolved by correcting with Eq. 7 and correlating with the known symbols.

**Interpolation (replaces a bigger FFT)**
- Magnitude (Eq. 15): Delta = 1/2 (|X(k_r)| - |X(k_l)|) / (2|X(k_f)| - |X(k_r)| - |X(k_l)|), -0.5 <= Delta <= 0.5;
  Eq. 16: k~ = k_f + Delta replaces k_f in Eqs. 5, 9, 12.
- Phase (Eq. 17, as printed): phi~ = phi_f + Delta (phi_l - phi_f) if Delta < 0, else phi_f + Delta (phi_f - phi_r).
  **Both branches have the sign opposite to a linear interpolation** (Delta < 0 should give phi_f + |Delta| (phi_l -
  phi_f)); Eq. 20 below has the consistent signs. Implement the linear interpolation phi_f + |Delta| wrap(phi_nb -
  phi_f) and note the printed typo. No unwrapping is mentioned; the phase step between bins is about 2 pi c / N with
  c the centre of the known symbols (for our rcs13 at N = 2048: 2 pi 570 / 2048 = 1.75 rad per bin [derived]), so a
  wrap is needed.
- Energy (Eqs. 18-19): E_k = |X(k)|^2, Delta = 1/2 (E_R - E_L) / (2 E_kf - E_R - E_L); Eq. 20: complex X(k~) = X(k_f) +
  Delta (X(k_f) - X(k_l)) if Delta < 0, else X(k_f) + Delta (X(k_r) - X(k_f)); its arg is the phase.

**Complexity.** One N-point FFT on the zero-filled burst (DA-KS), on the L_P pilots (DA-PL) or on the whole burst
(NDA), a peak search over N bins, 3-bin interpolation (one division, CORDIC magnitudes / phases), and the correction.
In our MAC convention [derived]: DA-KS = 4 Nk (z) + 2 N log2 N (FFT) + 2 N (|X|) + ~10 (interpolation).
FPGA (Xilinx Kintex, speed grade -2, ~350 MHz, max burst 4096, 8-bit I/Q; Table 2, post place and route):

| Configuration | FFT max | FF | LUT | BRAM | DSP |
|---|---|---|---|---|---|
| No interpolation | 4096 / 8192 / 16384 | 15 368 / 16 248 / 16 892 | 9 778 / 10 356 / 10 892 | 35 / 46.5 / 69 | 42 / 46 / 46 |
| Magnitude interp. | 4096 / 8192 / 16384 | 17 398 / 18 279 / 18 924 | 10 741 / 11 336 / 11 823 | 35.5 / 47 / 69.5 | 53 / 57 / 57 |
| Energy interp. | 4096 / 8192 / 16384 | 17 158 / 18 039 / 18 684 | 10 565 / 11 098 / 11 630 | 35.5 / 47 / 69.5 | 54 / 58 / 58 |

Throughput (Table 3, M symbols/s at 350 MHz): DA-KS burst 3: 22.9 (8192, no interp.) -> 90.9 (2048, interp.); NDA
burst 5: 89.6 (2048, no interp.) -> 175.5 (1024, interp.); DA-PL burst 8: the XML gives 346.8 for "2048 without" and
91.6 for "512 with", which contradicts the text (interpolation raises throughput): probably swapped in the extraction or
the table. Interpolation costs ~2000 FF, ~1000 LUT, 13 DSP (< 20 % more resources); throughput x2-4; efficiency +67 %
at least.

## 3. Reported results (all FER vs Es/N0, no pilot energy charged)

Text statements:
- Without interpolation the FFT must be 4-16x the burst length. Burst 3: about 16x (8192; the text says "8096", a typo)
  without interpolation; with either interpolation 2048 has no loss.
- Burst 4: 1024 points + magnitude interpolation (zero padding 1.9x) "tolerable"; doubling to 2048 gains ~0.1 dB at FER
  1e-3, ~0.2 dB at 1e-5. Energy interpolation at 1024 performs poorly.
- Burst 8: DA-PL + interpolation sufficient at 512 (2048 without); DA-KS + interpolation at 2048 ~0.2 dB better at 1e-4.
- Burst 21: 512 + energy interpolation 0.15 dB from reference at 1e-3, magnitude another 0.1 dB better.
- Burst 42: DA-PL + interpolation ~0.1 dB (1e-3) / ~0.2 dB (1e-5) from reference; at 3 % CFO NDA (4096) needed.
- Burst 5: NDA needs >= 1024; magnitude interpolation very close to reference, energy ~0.1 dB worse.
- Burst 33: NDA without interpolation at 1024 < 0.2 dB from reference at 1e-3; 2048 without = interpolated.
- Conclusion: interpolation halves (or better) the FFT for equal FER; magnitude better than energy only at very low
  zero padding.

Figure readings **[fig]** (Es/N0 where FER crosses 1e-3; gap = estimation loss vs genie, pilot energy not included):

| Fig. / burst | Reference | Curves (Es/N0 @ 1e-3, gap) |
|---|---|---|
| 3 / QPSK 536, DA-KS | -0.23 dB | 2048 mag. or energy interp. -0.10 (0.13); 8192 no interp. -0.10 (0.13); 4096 no interp. -0.04 (0.19); 2048 no interp. +0.20 (0.43). At 1e-4: ref +0.02, best DA-KS +0.15 (0.13); at 1e-5: ref ~0.24, best ~0.42 (0.18) |
| 4 / QPSK 536, DA-KS | 1.97 dB | 2048 mag. 2.09 (0.12); 8192 no interp. 2.12 (0.15); 1024 mag. 2.26 (0.29); 1024 energy: FER 5e-3 at 2.75 dB (fails) |
| 5 / 8PSK 536 | 7.77 dB | DA-KS 2048 mag. 7.91 (0.14), energy ~7.95 (0.18); DA-PL 512 interp. 8.05 (0.28); DA-PL 2048 no interp. 8.09 (0.32) |
| 6 / 16QAM 1616, DA-PL | 10.56 dB | 512 mag. 10.60 (0.04); 512 energy 10.66 (0.10); 2048 no interp. ~10.9 (~0.35) |
| 7 / BPSK 3236 | -3.75 dB | NDA (M = 2) 4096 mag. -3.72 (0.03); NDA energy -3.54 (0.21); NDA no interp. -3.36 (0.39); DA-PL 512 interp. -3.61 (0.14); DA-PL 512 no interp. ~-3.18 (0.57) |
| 8 / QPSK 536 2/3, NDA | 3.90 dB | 1024 interp. 3.95 (0.05); 2048 no interp. 3.98 (0.08); 1024 no interp. 4.07 (0.17) |
| 9 / QPSK 566 3/4, NDA | 4.92 dB | 1024 mag. ~4.93 (~0.01); energy ~4.95 (0.03); no interp. 5.09 (0.17); all curves incl. reference show a turbo floor 1e-4 ... 1e-5 above 5.25 dB |

Key facts for us: (a) the best DVB-RCS2 DA-KS chain keeps **0.12-0.15 dB** of estimation loss for QPSK bursts with 64-80
known symbols; (b) QPSK NDA (4th power) is used only at **Es/N0 >= ~3.9 dB** (rates 2/3, 3/4); the only NDA case at
our SNRs is **BPSK** (squaring, 3236 symbols) at -3.75 dB; (c) magnitude interpolation is never worse than energy and
much better at <= 2x zero padding.

## 4. Deployment / standard

Targets DVB-RCS2 (ETSI EN 301 545-2) TC-LM return-link bursts: an FPGA IP core for a gateway burst demodulator
(TU Kaiserslautern; no product or partner named, no funding statement). TR 101 545-4 gives no TC-LM synchronizer
(lit_dvbrcs2.md 2), so this paper is the best documented DVB-RCS2 TC-LM carrier-sync chain we have; it is consistent
with the DA-KS / R&B practice in TR's CPM clause and the Ali et al. 2014 predecessors (same group, paywalled).

## 5. Comparison with our receivers

### 5.1 What of it est4 already implements
| Paper element | est4 | Status |
|---|---|---|
| DA-KS Eqs. 2-5: zero-filled r c* on all known symbols, FFT, peak | `estimators.rife_boorstyn` on layout `rcs13` (source `RCS2-13`, C1a) | **implemented** |
| Magnitude parabolic interpolation Eqs. 15-16 | `_fft_peak` (parabolic on \|X\|, den < 0 guard, clip +-0.5) | **implemented** (same formula) |
| FFT size | `nfft_for(K)` = power of 2 >= 4K: **8192 for K = 1140 (7.2x)** | **larger than the paper's** (it would use 2048-4096 with interpolation) |
| Peak search range | \|nu\| <= 0.03 + 1 bin | **better than the paper** (Eq. 4 searches all N bins, i.e. +-0.5; it would add the +-1/20 aliases outside +-0.03 as outlier candidates) |
| Phase Eq. 6 / 17 (FFT-bin phase, interpolated) | `gain_const`: LS gain sum y_k / sum \|ks\|^2 at f = exact X(f) evaluated at the estimate | **ours is exact**; Eq. 17 is an approximation of it (and printed with a sign typo). No BLER difference expected |
| Constant phase over the burst | `const` | **implemented**; `RCS2-13 track` (Kalman / RTS, C1b) goes beyond the paper |
| NDA Eq. 11-14 | `nda4` on `prepost16` (C2) | **partly**: we use **r^4** (F = rho^4), the paper **\|r\| e^{j4 arg r}** (F = rho); we refine on the 32 known symbols (grid 17 + 2 Newton), the paper does not; the pi/2 ambiguity is absorbed by our LS gain (equivalent to Eq. 14's correlation) |
| Energy interpolation Eqs. 18-20 | - | **not implemented** (the paper shows it is never better; not worth it) |
| DA-PL Eqs. 8-10 | - | **not implemented; not applicable**: our pilot period 20 gives \|f\| < 0.025 < 0.03, and it discards the pre/postamble |
| Paper's own burst layouts (IDs 3, 4: 536 symbols) | rcs13 = ID 13 scaled to 1024 data (116 known, 0.47 dB) | different layout by design (ours carries our 1024-symbol codeword) |
| CFO 1.5 %, Es/N0 -0.75 ... +2.75 dB for QPSK | \|f\| <= 3 %, -5 ... +3 dB | ours is a harder setting |
| Single decode, no decoder in the loop | est4: fair metric-ordered CRC search around the estimate + re-encoding check | **ours is stronger** than the deployed chain |
| CRB comparison | `common.crb_known`, `crb_nda4` | the paper has none |

### 5.2 Why our RCS2-13 already beats the paper's DA-KS
Measured (8.2a, expected_est4.md): RCS2-13 estimation loss d = required - (genie + 0.47 dB) = -3.45 - (-3.91 + 0.47) =
**-0.01 dB** at 0.15 1e-3, 1.10 - 1.11 = **-0.01 dB** at 2/5, 2.33 - 2.37 = **-0.04 dB** at 1/2 [derived]. The paper's
DA-KS keeps 0.12-0.15 dB [fig]. The difference comes from our 116 vs 64-80 known symbols spread over a longer burst,
the 8192 FFT, the exact LS phase and, most of all, the CRC search around the estimate. So `RCS2-13` is a
**strengthened** DVB-RCS2 receiver; a "faithful Griebel" version can only be equal or worse in BLER (but cheaper).
The one place where RCS2-13 loses is 1/10: d = -4.09 - (-5.19 + 0.47) = **0.63 dB**, caused by alias picks at f +- 1/20
(881 / 480k packets at -5 dB; 25 / 64k in the pn runs). Neither the paper nor DVB-RCS2 addresses this (their CFO is
<= 1.5 %, where with a +-0.015 window no alias falls inside).

### 5.3 Predicted performance of the candidate variants at our points
Rule (competitors.md): required SNR ~ genie + pilot energy E + estimation loss d. Per-symbol points and plotted SNR
(+0.47 dB): 1/10 -5 (-4.53), 0.15 -4 (-3.53) / -3.5 (-3.03), 2/5 0.5 (0.97), 1/2 2 (2.47).

| Variant | What changes | 1/10 @1e-4 | 0.15 @1e-3 | 2/5 @1e-3 | 1/2 @1e-3 | Errors at the per-symbol points vs RCS2-13 (pn runs: 25 / 4 / 155 per 64k at 1/10 -5, 0.15 -3.5, 2/5 0.5) | MACs per core vs RCS2-13 |
|---|---|---|---|---|---|---|---|
| RCS2-13 (measured) | - | -4.09 | -3.45 | 1.10 | 2.33 | 25 / 4 / 155 | 0.034-0.045 M (estimator 7.2 k) |
| **G4096**: FFT 4096 (3.6x, like the paper's lossless 2048 / 536 = 3.8x) | nfft only | -4.09 ... -4.05 | -3.45 ... -3.42 | 1.10 ... 1.13 | 2.33 ... 2.36 | x1.0-1.1 | -3.8 k (estimator 3.3 k): -9 ... -11 % |
| **G2048**: FFT 2048 (1.8x, like the paper's lossy 1024 / 536 = 1.9x) | nfft only | -4.05 ... -3.9 | -3.42 ... -3.3 | 1.13 ... 1.3 | 2.36 ... 2.5 | x1.1-2 (more at 1/2, where bias > CRB) | -5.6 k (estimator 1.55 k): -12 ... -17 % |
| **G2048N**: 2048 + 1 Newton step (RB_NEWTON = 1) | removes the parabolic bias | as G4096 | as G4096 | as G4096 | as G4096 | x1.0-1.1 | -5.6 k + 2.3 k / 32 = -5.5 k |
| **Faithful-1dec**: G2048 + Eq. 17 phase + one decode (no CRC search) | the deployed chain | -3.9 ... -3.6 | -3.35 ... -3.25 | 1.2 ... 1.3 | 2.45 ... 2.5 | x2-5 | lower (no search decodes) |
| **RCS2-13 lobes** (not from this paper: alias hypotheses f +- 1/20 in the CRC search, as est5 VDE-SAT / Barbieri-Colavolpe) | removes the alias floor at 1/10 | **-4.70 ... -4.55** | -3.45 | 1.10 | 2.33 | 1/10: 25 -> ~2-6; others unchanged | + rare search decodes (failing packets with \|f\| > 0.02 only) |
| NDA-VV: Eq. 11 (\|r\| e^{j4 arg r}) instead of r^4 in RCS2 pre/post | nonlinearity | fails | fails | fails | 2.6 ... 2.9 (r^4: 2.77) | unknown sign | equal (+~2 per symbol) |

Reasoning: G4096 / G2048 from the paper's Fig. 3-4 ratios (2048 / 536 lossless vs 8192; 1024 / 536 0.17 dB worse at
1e-3) [fig]; our estimate of the parabolic bias at 1.8x is ~0.05-0.1 bin = 2.5-5e-5 cycles/symbol vs the CRB std
~4e-5 at -5 dB and ~1.8e-5 at +2 dB for the 116 rcs13 positions [derived], so the bias matters most at 1/2. The
"lobes" prediction is genie -5.19 + 0.47 + d ~0.05-0.15 (the 128-preamble ML reached d = 0 at 1/10). NDA-VV: the
paper only uses QPSK NDA above 3.9 dB, and our r^4 version already fails below 0 dB, so neither nonlinearity rescues
pre/post at our SNRs; which nonlinearity is better at -5 ... +2 dB was not found in a source I could read (Wang,
Serpedin, Ciblat 2002/2003 optimise the nonlinearity per SNR; only abstracts seen).

**vs blind:** none of these variants changes the 8.2a picture at 0.15, 2/5, 1/2 (blind -3.60 / 0.61 / 1.79). With
"RCS2-13 lobes" the 1/10 gap shrinks from 0.8 dB to about 0.2-0.35 dB (blind -4.9); with G2048 the MAC ratio
blind / RCS2-13 grows from x2-12 to about x2.3-14 [derived].

### 5.4 Ideas for blind from this paper
- Magnitude (not energy) parabolic interpolation on the 4th-power spectrum: **we already use it** (`blind_fast`
  `parab` / `s4_interp` on \|FFT(r^4)\|, plus Newton).
- Smaller FFT + interpolation: **already used** (`nfft4 = 1024, s4_interp = 4` above the waterfall).
- F(rho) = rho (Eq. 11) instead of r^4 in the fast path: **untested** (not in DEAD_ENDS.md). Cost +~4 MACs per symbol.
  Worth only a measurement-only check (fast-path in-window rate, 10k bursts at 0.15 -3.5 dB and 2/5 0.5 dB) before
  any BLER run; low priority, no source supports a gain at our SNRs.
- Nothing else in the paper is new for blind (no search, no code-aided step, no acceptance rule).

## 6. Implementation spec for est4 (for the code editor)

All on the existing **`rcs13` layout** (same LAYOUT_ID -> same noise / data / CFO draws as `RCS2-13`, so McNemar
pairing against RCS2-13 is valid). Do not change the existing sources or `LOBE_N` entries for `rcs13` (that would
change `RCS2-13` itself).

1. **Estimator `rbN` (N = 2048 / 4096), `rbNn` (with Newton):** reuse `rife_boorstyn(r, ks, kidx, nfft=N,
   iters=0 or 1)`. Steps: z = r[kidx] conj(ks) (116 cmul); x = zeros(1140), x[kidx] = z; X = FFT_N(x) (N >= K, no
   folding needed); peak of \|X\| over \|nu\| <= MAX_CFO + 1/N; parabolic Eq. 15 on \|X\| (bins k-1, k, k+1, den < 0
   guard, clip +-0.5); f = nu[k] + Delta / N; optional 1 Newton step on z at the exact positions (`E3.newton`).
   Add `"rb2048"`, `"rb4096"`, `"rb2048n"` to `estimate()` and `est_macs()`.
2. **Phase model:** `const` (LS gain at f). This equals arg X(f) evaluated exactly, i.e. Eq. 6 / 17 without the
   interpolation error. Optional faithful flag `eq17`: phi = phi_f + \|Delta\| wrap(phi_nb - phi_f) (nb = k-1 if
   Delta < 0 else k+1), phi_* = arg X at those bins (reference l = 0), converted to our reference by phi - 2 pi f
   DELAY_SYM; amplitude \|X(k~)\| / sum \|ks\|^2 with X(k~) from Eq. 20. Charge 40 MACs (3 CORDIC angles).
3. **Sources** (common.SOURCES): `"RCS2-13 G4096": ("rcs13", "rb4096", "const")`, `"RCS2-13 G2048": ("rcs13",
   "rb2048", "const")`, `"RCS2-13 G2048N": ("rcs13", "rb2048n", "const")`. Optional: `"RCS2-13 faithful"`
   (rb2048 + eq17 + `--no-search`, one decode) and `"RCS2-13 lobes"` (rb, const, lobe_D = 20 = RCS_DP + 1,
   1 lobe each side, only lobe centres inside \|f\| <= MAX_CFO + window, as the EST5 filter), implemented as a
   per-source override so `RCS2-13` keeps lobe_n = --lobes.
4. **Alias / lobe search:** G-variants: none (same as RCS2-13). Lobes variant: hypotheses f +- 0.05 in the
   metric-ordered CRC search.
5. **MACs** (est_macs, est3 conventions; per core = /32):
   - rb (now, 8192): 4·116 + 2·8192·13 + 2·8192 + 10 = **229 850** (7 183 per core)
   - rb4096: 464 + 98 304 + 8 192 + 10 = **106 970** (3 343 per core)
   - rb2048: 464 + 45 056 + 4 096 + 10 = **49 626** (1 551 per core)
   - rb2048n: 49 626 + 20·116 = **51 946** (1 623 per core)
   - eq17 phase: +40 per hypothesis (instead of const's 4·116; both negligible).
6. **Test plan:** smoke at a high-BLER point (2/5 per-symbol 0 dB or 1/2 1.5 dB, 800 packets: EVAL DONE, no
   Traceback, BLER within x2 of RCS2-13). Full: 1/10 -5.5 / -5 / -4.5, 0.15 -4 / -3.5 / -3, 2/5 0 / 0.5 / 1, 1/2 1.5 / 2 /
   2.5 dB per-symbol, 480k packets per point (as est4), one job per rate, part files merged. Report: crossing SNRs
   (plotted, +0.47 dB), McNemar vs RCS2-13 per point, RMSE vs `crb_known` per point, estimator MACs apart (expected_est4
   reading rule c). Write `expected_ars.md` with these predictions before the run.

## 7. Reference [4] of the article (anchor #bib1.bibx4)

The article's reference list is alphabetical; bib1.bibx4 is the 4th entry: **JTC (Joint Technical Committee
Broadcast of EBU, CENELEC, ETSI): ETSI EN 301 545-2 V1.1.1 (2012-01), "Digital Video Broadcasting (DVB); Second
Generation DVB Interactive Satellite System (DVB-RCS2); Part 2: Lower Layers for Satellite standard"** (approved
August 2011, published January 2012). Link:
https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.01.01_60/en_30154502v010101p.pdf

- **Where cited:** only in the Introduction, for "A Joint Technical Committee (JTC) specified this as part of an open
  standard initially in 2011 and recently revised it" (with V1.3.1 = JTC 2020a). The technical content of the paper
  (burst types, the 0.5-3 % range) cites V1.3.1 (2020a), TS 101 545-1 (2020b) and TR 101 545-4 (2014).
- **Read:** title page / history and Annex A Table A-1 rows (via a PDF-to-text reader, flattened table, positions
  matched by column order): IDs 3, 4, 5, 8, 13, 14, 21, 33 have the same burst length, payload, pre, post, pilot
  period and pilot sum as V1.3.1 (ID 13: 1616, QPSK 1/3, 32 / 31, P = 20, 77 pilots). Rows 42 / 43 fell between two
  text chunks and were not read.
- **Does it matter?** **Low.** It is the first edition of the standard we already use in V1.3.1; for the rows we
  depend on (ID 13 for `rcs13`, IDs 5 / 15 for `prepost16`) the parameters are unchanged, so no est4 layout changes.
  It contains no synchronization algorithm.

## Reference entries

### C4 (update). O. Griebel, U. Wasenmüller, N. Wehn, "Communication Performance vs. Implementation Trade-offs of Interpolation Techniques for FFT-Based Carrier Synchronization exemplified on DVB-RCS2", Adv. Radio Sci. 19, 59-70, 2021, doi:10.5194/ars-19-59-2021
- Link: https://ars.copernicus.org/articles/19/59/2021/   - Type: paper   - Read depth: full text (HTML + XML incl.
  MathML and Tables 1-3; FER Figs. 3-9 viewed and read by eye)
#### What it does
FFT (Rife-Boorstyn) carrier sync for DVB-RCS2 TC-LM bursts: DA-KS over all known symbols, DA-PL over pilots, NDA
\|r\| e^{jM arg r}; magnitude or energy 3-bin interpolation lets a 2-4x smaller FFT reach the same FER (8192 -> 2048
for a 536-symbol burst); constant phase; CFO <= 1.5 % of Rs, AWGN, symbol rate, genie timing. Best DA-KS QPSK
estimation loss 0.12-0.15 dB at FER 1e-3; QPSK NDA only at Es/N0 >= 3.9 dB; BPSK NDA works at -3.75 dB. FPGA: +2000 FF,
+1000 LUT, +13 DSP for interpolation, throughput x2-4. No RMSE / CRB.
#### What we took / could take
Took: the DA-KS chain + magnitude parabolic interpolation (est4 `rb`, `RCS2-13`) and the NDA chain (`nda4`, with r^4
instead of Eq. 11's \|r\| e^{j4 arg r}). Could take: the smaller FFT (2048 / 4096, -9 ... -17 % MACs per core for
RCS2-13), Eq. 11's nonlinearity (untested), Eq. 17 phase (no gain over our exact LS phase).
#### Used in
- 2026-11-15: est4 `RCS2-13`, `RCS2 pre/post` (expected_est4.md).
- 2026-11-15: lit_ars2021.md (full analysis; G4096 / G2048 / G2048N / faithful / lobes variants specified).

### C4a. JTC (EBU / CENELEC / ETSI), ETSI EN 301 545-2 V1.1.1 (2012-01), DVB-RCS2 Part 2: Lower Layers for Satellite standard
- Link: https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.01.01_60/en_30154502v010101p.pdf   - Type:
  standard   - Read depth: title / history and Annex A Table A-1 rows 1-39 (text reader, flattened table)
#### What it does
First edition of the DVB-RCS2 lower-layer standard (burst formats, reference waveforms, coding, modulation). Reference
[4] of Griebel 2021, cited only for the standard's history.
#### What we took / could take
Nothing new: the rows we use (ID 13 for rcs13, IDs 5 / 15 for prepost16) are identical to V1.3.1 (C1 / lit_dvbrcs2.md).
#### Used in
- 2026-11-15: lit_ars2021.md (check of the burst parameters only).

## Sources
- Griebel et al. 2021, HTML: https://ars.copernicus.org/articles/19/59/2021/ ; XML:
  https://ars.copernicus.org/articles/19/59/2021/ars-19-59-2021.xml ; figures
  https://ars.copernicus.org/articles/19/59/2021/ars-19-59-2021-f03-web.png ... -f10-web.png
- ETSI EN 301 545-2 V1.1.1: https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.01.01_60/en_30154502v010101p.pdf
- Wang, Serpedin, Ciblat, "Optimal blind carrier synchronization for M-PSK burst transmissions", ICASSP 2002 (abstract
  only): https://researchportal.ip-paris.fr/en/publications/optimal-blind-carrier-synchronization-for-m-psk-burst-transmissio/
- Wang, Serpedin, Ciblat, general QAM version (abstract only):
  https://researchportal.ip-paris.fr/en/publications/optimal-blind-nonlinear-least-squares-carrier-phase-and-frequency-2/
- Project files: est4/estimators.py, est4/common.py, BLIND_IMPLEMENTATION/08_parameters_results.md 8.2a,
  testing/results/expected_est4.md, competitors.md, lit_dvbrcs2.md, BLIND_IMPLEMENTATION/REFERENCES.md (C4).
