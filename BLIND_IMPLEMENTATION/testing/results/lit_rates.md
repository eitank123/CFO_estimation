# Code rates and modulations of the real pilot / preamble systems in our SNR region (literature scout, 2026-11-15)

Question (main session): which MODCODs do the real systems we compare against (competitors.md C1, C6-C15) actually run
between Es/N0 = -5 and +3 dB, what Es/N0 do their standards require, what is their net spectral efficiency (SE, info
bits per transmitted symbol with header / pilot / preamble overhead included), and would any of them deliver more
throughput than our blind receiver at the same Es/N0, even after paying for its pilots?

No simulations were run. Numbers marked **[derived]** are my arithmetic from the cited numbers. Each number is labelled
by origin: **[std]** = the standard or its official implementation guideline, **[vendor]** = a datasheet / product
brief, **[paper]** = a paper, **[prev]** = an earlier scout report in this folder (not re-read here).

---

## 0. Short verdict

**At the same Es/N0, the long-frame satellite standards run a higher SE than we do. The short-burst systems do not.**

- **Long frames: DVB-S2 / S2X (16 200 to 64 800-bit LDPC) and CCSDS turbo (k = 8920).** At each of our four points
  they deliver **5-20 % more info bits per symbol**, on their ideal-sync AWGN table values. The outliers are CCSDS
  turbo rate 1/4 (+34 % at -2.9 dB) and CCSDS turbo rate 1/6 (+78 % at -4.9 dB, our 1/10 point).
- **Short bursts: DVB-RCS2 (984-1504-bit turbo), VDE-SAT short formats, IEEE 802.11ad SC, MIL-STD-188-110C and
  real SCPC modems.** At the same Es/N0 they are **equal to or below our SE**. The one exception is VDE-SAT
  SAT-MCS-0.50-3 / DVB-RCS2 ID 42 at our 0.15 point, which are +13-14 % on paper (ideal sync, unstated or 1e-3 PER).
- **Most of the long-frame advantage is block length, not pilots.** Our packet is 1024 symbols carrying K = 205-1024
  bits; theirs carry 4 000-64 800 bits. The normal approximation (NA) bounds what any code can do at our length. At
  -4.9 dB and 1e-4, a 1024-symbol packet can carry at most about 0.30 bit/symbol **[derived]**. CCSDS turbo 1/6 (0.33)
  is above that, so no 1024-symbol scheme can match it.
- **We are still 1.1-1.6 dB from the NA at our own length, and most of that is at the low rates.** So part of the
  S2X advantage (+11-14 % at 2/5, 1/2) could in principle be recovered with a better short code or decoder. That
  needs no change to the blind synchroniser.

Comparability caveats (they apply to every row):
- Their thresholds are mostly **ideal-sync AWGN table values**. Ours are measured with blind CFO / phase recovery
  over +-0.03.
- The error-rate targets differ: S2 PER 1e-7, S2X FER 1e-5, RCS2 PER 1e-3, CCSDS BER 1e-6 ~ FER 1e-4, VDE-SAT
  unstated, ours 1e-3 / 1e-4.
- Real-implementation losses would shift the competitor thresholds right by 0.1-0.6 dB:
  - DVB-RCS2 bench: about 0.5-0.6 dB [std, via prev];
  - DVB-S2 QPSK 1/2: about 0.1 dB [std, via prev].

---

## 1. Ranked findings (at most 5)

1. **The DVB-S2X short-frame QPSK MODCODs are the strongest "same Es/N0" competitors at 2/5 and 1/2.**
   - QPSK 7/15 short: 0.60 dB, SE 0.874 with pilots. That is +12 % over our 2/5 (0.784 at 0.61 dB).
   - QPSK 8/15 short: 1.45 dB, SE 1.003. That is +8 % over our interpolated SE at 1.45 dB. It reaches our 1/2 SE
     (0.984) at 0.34 dB lower Es/N0.
   - Both are 16 200-bit LDPC frames, FER 1e-5, ideal sync.
   - Source: ETSI EN 302 307-2 Table 20c [std]
     ([PDF](https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.01.01_60/en_30230702v010101p.pdf)).
2. **At our 1/10 point (-4.9 dB) the only real systems are DVB-S2X VL-SNR and CCSDS turbo 1/6.** Both are long-block.
   - BPSK 4/15 short: -4.9 dB, SE about 0.24 (an upper value: the shortening is not resolved).
   - BPSK 11/45 medium: -5.5 dB, SE 0.230. Both are +25-32 % over our 0.185.
   - CCSDS turbo 1/6 at k = 8920: Eb/N0 -0.1 dB at BER 1e-6 ~ FER 1e-4 = Es/N0 -4.87 dB, SE 0.332. That is +78 %, and
     only reachable with long blocks (NA for 1024 symbols: 0.30).
   - DVB-RCS2 and VDE-SAT have no QPSK/BPSK mode at -4.9 dB with SE above ours. VDE-SAT SAT-MCS-0.50-2: -4.5 dB,
     SE 0.19.
   - Sources: EN 302 307-2 Tables 20b/20c [std]; CCSDS 130.1-G-3 section 7.4.1 [std]
     ([PDF](https://public.ccsds.org/Pubs/130x1g3e1.pdf)).
3. **The short-burst standards closest to our packet do not beat us at the same Es/N0, apart from ID 42 at ideal
   sync.**
   - DVB-RCS2 ID 13 (QPSK 1/3, 984 bits): -0.80 dB @ PER 1e-3, SE 0.609. That is 0.99x our interpolated SE.
   - DVB-RCS2 ID 14 (QPSK 1/2, 1504 bits): 1.49 dB, SE 0.931, 1.00x.
   - DVB-RCS2 ID 42 (BPSK 1/3, 984 bits): -3.81 dB, SE 0.304, 1.13x at ideal sync. With the measured ~0.5 dB
     implementation loss it drops to 0.95x.
   - Our measured est4 comparison already shows the ID 13 layout 0.15-0.8 dB behind blind on our code.
   - Source: ETSI TR 101 545-4 V1.2.1 clause 10.2.1 [std]
     ([PDF](https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf)).
4. **VDE-SAT, the standard closest to our SNR range, has formats at -4.5 / -3.6 / -2.4 / -0.6 dB** (Annex 2 Tables
   10-11 [std], [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf)).
   - Net SE 0.19 / 0.325 / 0.475 / 0.633, i.e. 0.88x / 1.14x / 1.11x / 0.99x our interpolated SE.
   - The two formats above 1.0x carry 4 280-38 192 bits per burst. The PER behind the thresholds is not stated.
   - SAT-MCS-1.50-1 (pi/4-QPSK, turbo 1/4, 80 371-symbol burst, the format our C6 layout is taken from) runs at
     -2.4 dB. That sits **between our 0.15 and 2/5 rates, where we have no rate.**
5. **Real SCPC modem guarantees (implementation losses included) are at or below our SE everywhere.**
   - Comtech DMD1050TS (STANAG 4486 turbo, LDPC, TPC) at BER 1e-5: QPSK turbo 1/2 needs Es/N0 1.72 dB guaranteed
     (1.32 dB typical) for SE 0.982, i.e. 1.01x (1.09x typical) of ours.
   - The BPSK modes at -2.6 ... +0.8 dB are 0.73-0.88x of ours.
   - Source: [Comtech datasheet](https://comtech.com/wp-content/uploads/2022/04/ds-DMD1050TS.pdf) [vendor].
   - IEEE 802.11ad SC and MIL-STD-188-110C are far below us (0.56-0.58x, and outside our SNR range respectively).

---

## 2. Our own operating points (checked)

K = round(2048 R) including the CRC-16 (1/10 -> 205, 0.15 -> 307 as in the memory notes, 2/5 -> 819, 1/2 -> 1024).
Net SE = (K - 16) / 1024, because the packet is exactly 1024 QPSK symbols with no other overhead. Gross SE = K / 1024
(CRC counted as payload, as the standards do with their own CRCs).

| Rate | K (with CRC) | Net SE [b/sym] | Gross SE | Required Es/N0 (measured, blind) | Eb/N0 net = Es/N0 - 10 log10(SE) [derived] | NA max SE at that Es/N0, n = 1024 complex symbols [derived] | Gap to NA (gross rate) [derived] |
|---|---|---|---|---|---|---|---|
| 1/10 | 205 | **0.1846** | 0.2002 | -4.9 dB @ BLER 1e-4 | 2.44 dB | 0.30 | ~1.6 dB (NA needs -6.5 dB) |
| 0.15 | 307 | **0.2842** | 0.2998 | -3.60 dB @ 1e-3 (-2.98 @ 1e-4) | 1.86 dB (2.48 @ 1e-4) | 0.43 | ~1.45 dB (NA -5.15 dB) |
| 2/5 | 819 | **0.7842** | 0.7998 | 0.61 dB @ 1e-3 | 1.67 dB | 0.99 | ~1.15 dB (NA -0.55 dB) |
| 1/2 | 1024 | **0.9844** | 1.0000 | 1.79 dB @ 1e-3 | 1.86 dB | 1.20 | ~1.1 dB (NA +0.7 dB) |

The main session's values (0.184, 0.284, 0.784, 0.984) are correct.

NA = Polyanskiy-Poor-Verdu normal approximation for the complex AWGN channel with Gaussian input:
R ~ C - sqrt(V/n) Q^-1(eps) + log2(n)/(2n), with C = log2(1 + P), V = P(P + 2)/(P + 1)^2 (log2 e)^2 per complex symbol,
n = 1024, P = Es/N0. The QPSK constraint lowers the NA by a few % at 2/5 and 1/2, so those gaps are about 0.2 dB
smaller for a QPSK system. These NA numbers are my hand arithmetic, not from a source; recompute before quoting.

To compare at an Es/N0 between our points, "our interpolated SE" is a straight line in (Es/N0 dB, SE) between our
measured points:
- slope 0.0766 / dB from 1/10 to 0.15 (mixed BLER targets);
- slope 0.1188 / dB from 0.15 to 2/5;
- slope 0.1697 / dB from 2/5 to 1/2;
- capped at 0.984 above 1.79 dB, our highest rate.

This assumes we would add intermediate rates. Real capacity is concave in dB at low SNR, so the straight line slightly
under-states what intermediate polar rates would reach.

---

## 3. Comparison table: every MODCOD in -5 ... +3 dB Es/N0

Columns:
- **Es/N0 req** is the standard's stated threshold.
- **Net SE** = info bits / all transmitted symbols of the frame or burst (header, preamble, pilots, syncwords, ASM
  included; guard time excluded).
- **Ratio** = competitor SE / our interpolated SE at the competitor's Es/N0. A ratio > 1 means more throughput than
  us at the same Es/N0.
- **Nearest** = the nearest of our four rates by SE.

Long-block rows are marked (L). Short-burst rows (block <= ~1 600 bits, like ours) are marked (S).

| System | MODCOD (mod, rate, FEC, info block) | Es/N0 req [dB] (target; conditions) | Origin | Net SE [b/sym] (overhead) | Eb/N0 net [dB] [derived] | Ours at that Es/N0 | Ratio | Nearest |
|---|---|---|---|---|---|---|---|---|
| DVB-S2X VL-SNR | BPSK 11/45, LDPC medium 30 780, K 7740 (L) | **-5.50** (FER 1e-5; AWGN, ideal sync, 75 it.) | [std] T20b | 0.230 (frame 33 282 incl. 90 PLH + 900 VL-SNR hdr + pilots) [derived] | 0.88 | below our range | - | 1/10 |
| DVB-S2X VL-SNR | BPSK 4/15 short, n 14 976, K <= 4152 (L) | **-4.9** (FER 1e-5; ideal) | [std] T20c | <= 0.244 (frame 16 686) [derived; K after shortening not read] | <= 1.23 | 0.185 | <= 1.32 | 1/10 |
| CCSDS 131.0 turbo | QPSK, turbo 1/6, k 8920 (L) | **-4.87** = Eb/N0 -0.1 dB at BER 1e-6 ~ FER 1e-4 [derived conversion] | [std] 130.1-G-3 7.4.1 | 0.332 (ASM 192 bits [not verified]) [derived] | -0.08 | 0.187 | **1.78** | 0.15 |
| VDE-SAT | SAT-MCS-0.50-2 (ID 32), BPSK/CDMA, turbo 1/4, 312 bits (S) | **-4.5** (PER not stated; AWGN) | [std] M.2092-2 T11 | 0.190 per despread symbol (1645 symbols incl. 192 sync + 180 pilots) [derived] | 2.71 | 0.215 | 0.88 | 1/10 |
| DVB-S2X VL-SNR | BPSK 1/3, LDPC medium 30 780, K 10 620 (L) | **-4.00** (FER 1e-5) | [std] T20b | 0.317 (frame 33 282) [derived] | 0.99 | 0.254 | 1.25 | 0.15 |
| DVB-RCS2 | ID 42, BPSK 1/3 turbo, 984 bits, 3236-symbol burst (S) | **-3.81** (PER 1e-3; AWGN, ideal sync) | [std] TR 101 545-4 10.2.1 | 0.304 (pre 65 + post 64 + pilots ~155 inside the burst) [derived] | 1.36 | 0.268 | 1.13 (0.95 with the 0.5 dB bench loss) | 0.15 |
| DVB-S2X VL-SNR | BPSK 1/3 short, n 14 976 or 16 200 (L) | **-3.72** (FER 1e-5) | [std] T20c | 0.235-0.309 (K 4008-5232; shortening not read) [derived] | 1.4-2.6 | 0.275 | 0.85-1.12 | 0.15 |
| VDE-SAT | SAT-MCS-0.50-3 (ID 33), BPSK, turbo 1/3, 4280 bits (L) | **-3.6** (PER not stated) | [std] M.2092-2 T11 | 0.325 (13 171 symbols incl. 288 sync) [derived] | 1.28 | 0.284 | **1.14** | 0.15 |
| DVB-S2X | QPSK 2/9, LDPC normal 61 560, K 14 208 (L) | **-2.85** (FER 1e-5) | [std] T20a | 0.4348 (no S2 pilots) / 0.4245 (frame 33 282) | 0.87 | 0.373 | 1.14-1.16 | 0.15 |
| CCSDS 131.0 turbo | QPSK, turbo 1/4, k 8920 (L) | **-2.86** (Eb/N0 0.15 at BER 1e-6 ~ FER 1e-4) | [std] | 0.498 [derived] | 0.17 | 0.372 (and our 0.15 @1e-4 is 0.284 at -2.98) | **1.34** | 2/5 |
| Comtech SCPC modem | BPSK TPC 5/16 (L, continuous) | -2.59 guaranteed (-2.79 typical); BER 1e-5, real modem | [vendor] | 0.31 | 2.5 | 0.404 | 0.77 | 0.15 |
| DVB-S2X | QPSK 11/45 short, K 3792 (L) | **-2.50** (FER 1e-5) | [std] T20c | 0.453 / 0.444 (90 PLH + 5 x 36 pilots) [derived] | 1.03 | 0.415 | 1.07-1.09 | 0.15 / 2/5 |
| VDE-SAT | SAT-MCS-1.50-1 (ID 26), pi/4-QPSK, turbo 1/4, 7 x 5456 bits (L) | **-2.4** (PER not stated) | [std] M.2092-2 T10 | 0.475 (80 371 symbols incl. 945 sync + 2940 pilots) [derived] | 0.83 | 0.427 | 1.11 | 2/5 |
| DVB-S2 | QPSK 1/4, LDPC normal 64 800, K 16 008 (L) | **-2.35** (PER 1e-7 QEF; ideal; 50 it.) | [std] EN 302 307-1 T13 | 0.4902 (no pilots) / 0.4786 (pilots) | 0.85 | 0.433 | 1.11-1.13 | 2/5 |
| DVB-S2X | QPSK 4/15 short, K 4152 (L) | **-2.24** | [std] T20c | 0.497 / 0.487 [derived] | 0.89 | 0.446 | 1.09-1.12 | 2/5 |
| DVB-S2X | QPSK 13/45 normal, K 18 528 (L) | **-2.03** | [std] T20a | 0.568 / 0.554 | 0.53 | 0.471 | 1.18-1.21 | 2/5 |
| DVB-S2X | QPSK 14/45 short, K 4872 (L) | **-1.46** | [std] T20c | 0.585 / 0.573 [derived] | 0.96 | 0.538 | 1.06-1.09 | 2/5 |
| CCSDS 131.0 turbo | QPSK, turbo 1/3, k 8920 (L) | **-1.36** (Eb/N0 0.4) | [std] | 0.664 [derived] | 0.42 | 0.550 | 1.21 | 2/5 |
| DVB-S2 | QPSK 1/3, normal, K 21 408 (L) | **-1.24** | [std] T13 | 0.6564 / 0.6408 | 0.69 | 0.565 | 1.14-1.16 | 2/5 |
| Comtech SCPC modem | BPSK STANAG 4486 turbo 1/2 (L) | -1.24 guaranteed (-1.64 typ.); BER 1e-5 | [vendor] | 0.497 | 1.8 | 0.565 | 0.88 | 2/5 |
| Comtech SCPC modem | BPSK LDPC 1/2 (L) | -1.01 guaranteed (-1.31 typ.) | [vendor] | 0.50 | 2.0 | 0.592 | 0.84 | 2/5 |
| DVB-RCS2 | ID 13, QPSK 1/3 turbo, 984 bits, 1616 symbols (S) | **-0.80** (PER 1e-3; ideal) | [std] TR 101 545-4 | 0.609 (pre 32 + post 31 + 77 pilots inside) [derived] | 1.35 | 0.617 | 0.99 | 2/5 |
| VDE-SAT | SAT-MCS-1.50-2 (ID 34), pi/4-QPSK, turbo 1/3, 2 x 4160 bits (L) | **-0.6** (PER not stated) | [std] M.2092-2 T11 | 0.633 (13 150 symbols incl. 162 sync + 480 pilots) [derived] | 1.39 | 0.641 | 0.99 | 2/5 |
| Comtech SCPC modem | BPSK TPC 21/44 (L) | -0.49 guaranteed | [vendor] | 0.48 | 2.7 | 0.654 | 0.73 | 2/5 |
| DVB-S2 | QPSK 2/5, normal, K 25 728 (L) | **-0.30** | [std] T13 | 0.7894 / 0.7706 | 0.83 | 0.689 | 1.12-1.15 | 2/5 |
| DVB-RCS2 | ID 3, QPSK 1/3, 304 bits, 536 symbols (S) | **-0.27** (PER 1e-3) | [std] | 0.567 [derived] | 2.19 | 0.693 | 0.82 | 2/5 |
| DVB-S2 | QPSK 2/5 short, K 6312 (L) | about -0.05 (normal value + 0.2...0.3 dB short-frame penalty stated by T13 note) | [std] + [derived] | 0.761 / 0.745 [derived] | ~1.2 | 0.722 | 1.03-1.05 | 2/5 |
| DVB-S2X | QPSK 9/20 normal, K 28 968 (L) | **0.22** | [std] T20a | 0.889 / 0.868 | 0.84 | 0.738 | 1.18-1.20 | 1/2 |
| DVB-RCS2 | ID 2, QPSK 1/3, 112 bits, 262 symbols (S, control burst) | **0.50** (PER 1e-3) | [std] T10.4 | 0.427 [derived] | 4.19 | 0.766 | 0.56 | 0.15/2/5 |
| IEEE 802.11ad SC | MCS 2, pi/2-BPSK 1/2, LDPC 672 (S codeword) | ~0.5 (sensitivity -66 dBm minus 5 dB impl. loss; PER 1 % at 4096 bytes) [derived, noise BW 1.76 GHz assumed] | [std via Wikipedia] | 0.4375 (GI 64 / 512 block; preamble not counted) [derived] | ~4.1 | 0.776 | 0.56 | 0.15/2/5 |
| DVB-S2X | QPSK 7/15 short, K 7392 (L) | **0.60** (FER 1e-5) | [std] T20c | 0.893 / 0.874 [derived] | 1.19 | **0.783 (our 2/5 at 0.61)** | **1.12-1.14** | 1/2 |
| Comtech SCPC modem | BPSK STANAG 4486 turbo 2/3 (L) | 0.77 guaranteed | [vendor] | 0.656 | 2.6 | 0.811 | 0.81 | 2/5 |
| DVB-S2 | QPSK 1/2, normal, K 32 208 (L) | **1.00** | [std] T13 | 0.9889 / 0.9653 | 1.15 | 0.850 | 1.14-1.16 | 1/2 |
| CCSDS 131.0 turbo | QPSK, turbo 1/2, k 8920 (L) | **1.10** (Eb/N0 1.1) | [std] | 0.996 [derived] | 1.12 | 0.867 | 1.15 | 1/2 |
| DVB-S2 | QPSK 1/2 short (effective rate 4/9), K 7032 (L) | about 1.25 (1.00 + 0.2...0.3) | [std] + [derived] | 0.849 / 0.831 [derived] | ~1.9 | 0.893 | 0.93-0.95 | 2/5 |
| Comtech SCPC modem | QPSK STANAG 4486 turbo 1/2 (L) | 1.72 guaranteed / 1.32 typical (BER 1e-5) | [vendor] | 0.982 | 1.8 (1.4) | 0.973 / 0.905 | 1.01 / 1.09 | 1/2 |
| DVB-S2X | QPSK 8/15 short, K 8472 (L) | **1.45** | [std] T20c | 1.025 / 1.003 [derived] | 1.44 | 0.927 | 1.08-1.11 | 1/2 |
| DVB-S2X | QPSK 11/20 normal, K 35 448 (L) | **1.45** | [std] T20a | 1.089 / 1.063 | 1.19 | 0.927 | 1.15-1.17 | 1/2 |
| DVB-RCS2 | ID 14, QPSK 1/2 turbo, 1504 bits, 1616 symbols (S) | **1.49** (PER 1e-3; ideal) | [std] | 0.931 [derived] | 1.80 | 0.934 | 1.00 | 1/2 |
| IEEE 802.11ad SC | MCS 3, pi/2-BPSK 5/8 | ~1.5 (sens. -65 dBm, same derivation) | [std via Wikipedia] | 0.547 | ~4.2 | 0.942 | 0.58 | 2/5 |
| Comtech SCPC modem | QPSK LDPC 1/2 (L) | 2.0 guaranteed / 1.7 typical | [vendor] | 1.00 | 2.0 | 0.984 (cap) | 1.02 | 1/2 |
| DVB-RCS2 | ID 4, QPSK 1/2, 472 bits, 536 symbols (S) | **1.92** (PER 1e-3) | [std] | 0.881 [derived] | 2.47 | 0.984 (cap) | 0.90 | 1/2 |
| CCSDS 131.0 LDPC | QPSK, AR4JA (2048, 1024), r 1/2: **same N and K as our 1/2** (S) | 2.20 at BLER 1e-5 (Eb/N0 = Es/N0 for r 1/2; 31 it., 6-bit) | [vendor] Creonic | 0.985 (32-bit ASM) [derived] | 2.27 | 0.984 (cap; ours at 1e-3) | 1.00 | 1/2 |
| DVB-S2 | QPSK 3/5, normal (L) | **2.23** | [std] T13 | 1.188 / 1.160 | 1.59 | above our highest rate | (1.18-1.21 vs our cap; we have no rate there) | - |
| IEEE 802.11ad SC | MCS 4, pi/2-BPSK 3/4 | ~2.5 | [std via Wikipedia] | 0.656 | ~4.4 | 0.984 | 0.67 | 2/5 |
| LTE (indicative only) | CQI 1-6, QPSK, turbo, code rate 78-602 / 1024 | about -7, -5, -3, -1, +1, +3 dB at **BLER 10 %** (CQI 1 ~ -7 dB, ~2 dB per step; OFDM downlink AWGN) | [std] efficiencies (TS 36.213 Table 7.2.3-1); [paper] SNRs read from a figure | 0.152, 0.234, 0.377, 0.602, 0.877, 1.176 per RE, before ~20 % DMRS + CP overhead | - | - | not comparable (10 % BLER, OFDM, HARQ) | - |
| MIL-STD-188-110C serial | 2400 bps = 8PSK r 1/2 with 32 data + 16 probe | SNR 10 dB in 3 kHz = Es/N0 10.97 dB (AWGN, BER 1e-5) | [std] Table XVI | 1.0 | 11.0 | out of range | - | - |
| MIL-STD-188-110C App D (WBHF, 3 kHz) | WID 1-4: BPSK 1/8, 1/4, 1/3, 2/3 (150-1200 bps) | AWGN table D-LII not legible; earlier scout read WID 1 ~ 3 dB SNR (Es/N0 ~4 dB) | [std, garbled] / [prev] | 0.0625, 0.125, 0.25, 0.5 (48 data + 48 probe, or 96 + 32) [derived] | - | - | far below ours | - |

How the [derived] SE values were computed:
- **DVB-S2 normal QPSK:** (K_bch - 80 BBHEADER) / 32 490 symbols without pilots (32 400 + 90 PLHEADER), or / 33 282
  with 22 pilot blocks of 36. This reproduces the standard's own SE column (QPSK 1/4: 15 928 / 32 490 = 0.4902).
- **Short QPSK:** / 8 190 symbols without pilots, / 8 370 with 5 pilot blocks.
- **S2X VL-SNR:** set 1 frame = 33 282 symbols, set 2 frame = 16 686 symbols (both totals from EN 302 307-2). The
  S2X Table 20a SE for QPSK 2/9 is 0.434841 = 14 128 / 32 490, so the stated SE excludes only the regular S2 pilots.
- **DVB-RCS2:** payload bytes x 8 / burst symbols (Table A-1 via `lit_dvbrcs2.md`). Payload CRCs not subtracted.
- **VDE-SAT:** information bits (its "FEC output bits" row, which equals channel bits x code rate) / symbols per
  burst. The ramp is included, the guard is excluded.
- **CCSDS turbo:** n = (k + 4)/r; QPSK Es/N0 = Eb/N0 + 10 log10(2 k / n).

---

## 4. Per-system details

### 4.1 DVB-S2 (ETSI EN 302 307-1 V1.4.1) [std, read]
- **MODCODs in -5 ... +3 dB:** QPSK 1/4, 1/3, 2/5, 1/2, 3/5 (2/3 is at 3.10 dB).
  - Ideal Es/N0 at PER 1e-7 (QEF), AWGN, perfect carrier and sync, no phase noise, 50 fixed-point LDPC iterations,
    64 800-bit frames (Table 13).
  - The Table 13 notes say short frames (16 200) are **0.2-0.3 dB worse**. There is no separate short-frame table in
    -1.
  - Short QPSK 1/4 is really rate 1/5 (K_bch 3072) and short 1/2 is rate 4/9 (K_bch 7032) (Table 5b). The +0.2-0.3 dB
    rule is therefore only a rough guide for those two.
- **Overhead:**
  - PLHEADER 90 symbols per frame (26 SOF + 64 PLS code), plus BBHEADER 80 bits.
  - Optional pilots: 36 symbols every 16 slots of 90.
  - QPSK normal: 99.72 % framing efficiency without pilots, 2.4 % pilot overhead.
- **Most used at these SNRs:** no source read gives deployment statistics. The ACM design picks the highest MODCOD
  that closes, which is the logic of our table.
- **Block length:** 16 008-38 688 info bits (normal), 3 072-9 552 (short); 15-190 x our K.

### 4.2 DVB-S2X (ETSI EN 302 307-2 V1.1.1) [std, read]
- **Normal frames (Table 20a, 50 iterations, FER 1e-5 QEF, AWGN, ideal):** QPSK 2/9 -2.85 dB (VL-SNR, 61 560 bits),
  13/45 -2.03, 9/20 0.22, 11/20 1.45.
- **Medium VL-SNR frames (Table 20b, 75 iterations):** BPSK 1/5 -6.85, 11/45 -5.50, 1/3 -4.00.
- **Short frames (Table 20c):**
  - BPSK-S 1/5 -9.9, BPSK-S 11/45 -8.3, BPSK 1/5 -6.1 (all below our range);
  - BPSK 4/15 -4.9, BPSK 1/3 -3.72;
  - QPSK 11/45 -2.50, 4/15 -2.24, 14/45 -1.46, 7/15 0.60, 8/15 1.45, 32/45 3.66.
- **VL-SNR frame overhead:**
  - a 900-symbol VL-SNR header after the 90-symbol PLHEADER, plus extra pilots;
  - set 1 = 30 780 payload symbols in 33 282 total (7.5 % overhead);
  - set 2 = 14 976 payload symbols in 16 686 total (10.2 %).
- **Not resolved:**
  - K after shortening for the short BPSK 4/15 / 1/3 VL-SNR codes (Table 19a gives Xs only for a few codes);
  - the exact frame-to-set mapping of BPSK 1/3 short;
  - the S2X implementation guideline TR 102 376-2 (not re-read here; [prev] says the VL-SNR detector is specified
    for CFO <= 1 % of Rs).
- **Most used:** not found.

### 4.3 DVB-RCS2 return link (EN 301 545-2 Table A-1, TR 101 545-4 V1.2.1 clause 10.2.1) [std, read]
- **Waveforms in range (AWGN, ideal sync, turbo, Es/N0 at PER 1e-3 / 1e-5):**

  | ID | Burst | Mod, rate | Payload | Es/N0 @ 1e-3 / 1e-5 [dB] |
  |---|---|---|---|---|
  | 2 | 262 | QPSK 1/3 | 14 B | 0.50 / 1.29 |
  | 3 | 536 | QPSK 1/3 | 38 B | -0.27 / 0.22 |
  | 4 | 536 | QPSK 1/2 | 59 B | 1.92 / 2.34 |
  | 13 | 1616 | QPSK 1/3 | 123 B | -0.80 / -0.51 |
  | 14 | 1616 | QPSK 1/2 | 188 B | 1.49 / 1.71 |
  | 42 | 3236 | BPSK 1/3 | 123 B | -3.81 / -3.52 |
  | 43 | 3236 | BPSK 1/2 | 188 B | -1.53 / -1.30 |

  - A BPSK 1/3 control burst in Table 10.4 gives -4.00 / -3.65 / -3.38 / -3.17 / -2.98 dB at PER 1e-1 ... 1e-5. Its
    ID and length are garbled ("236"); probably ID 40 / 41.
  - IDs 5 / 15 (QPSK 2/3) need 3.90 / 3.46 dB, outside our range.
- **Overhead:**
  - known symbols inside the burst: ID 13: 140 (8.7 %); ID 14: 112 (6.9 %); ID 3: 80; ID 4: 64; ID 42: ~284;
  - plus guard symbols (Table 10.9 assumes 4).
- **Net SE:**
  - 0.609 (ID 13), 0.931 (ID 14), 0.567 (ID 3), 0.881 (ID 4);
  - 0.304 / 0.465 (ID 42 / 43, BPSK);
  - ID 43: -1.53 dB, SE 0.465, ratio 0.465 / 0.540 = 0.86.
- **Implementation loss:** about 0.5-0.6 dB measured on a bench prototype at PER 1e-5 (TR 10.4.3.2, via
  `lit_dvbrcs2.md` [prev]).
- **Block length:** 112-1 504 bits, the same class as ours (189-1 008). **This is the fairest standard comparison.**
- **Most used:** not found. The TR calls IDs 1-22 the reference waveforms. The NCC can signal any format.

### 4.4 CCSDS telemetry (CCSDS 131.0-B turbo / AR4JA LDPC; green book 130.1-G-3) [std, partly read]
- **Turbo codes:** k = 1784, 3568, 7136, 8920, rates 1/2, 1/3, 1/4, 1/6.
  - Green book 7.4.1: "threshold bit-SNRs of approximately -0.1 dB, 0.15 dB, 0.4 dB, and 1.1 dB are required by the
    Turbo codes of rates 1/6, 1/4, 1/3 and 1/2" at BER 1e-6, "approximately the same ... achieve a WER or FER of
    1e-4".
  - The paragraph does not name the block length. It is most likely k = 8920; the shorter k = 1784 is worse, by an
    amount not read.
  - QPSK Es/N0: -4.87, -2.86, -1.36, +1.10 dB [derived].
- **AR4JA LDPC:** k = 1024 / 4096 / 16384, rates 1/2, 2/3, 4/5.
  - The green book gives figures only; numbers are from Creonic [vendor]: k = 1024 r 1/2 needs Eb/N0 2.20 dB at
    BLER 1e-5 (= Es/N0 2.20 dB in QPSK). That is (2048, 1024), **the same N and K as our rate 1/2**.
  - k = 1024 r 2/3 needs 3.00 dB = Es/N0 4.25 dB [derived], outside our range.
- **Overhead:** attached sync marker (32 bits for LDPC / RS; for turbo 32/r bits, i.e. 192 bits at r 1/6, from
  memory and **not verified**), below 1 %. CCSDS 131.2 SCCC adds pilots (~3 %) [prev].
- **Most used:** not found.

### 4.5 VDE-SAT (ITU-R M.2092-2 Annex 2 Tables 9-11; IALA G1139 ed. 3 Tables 9-11) [std, read via text extraction, tables partly garbled]

| Format | Mod, FEC | Info bits | Symbols | Es/N0 (AWGN) |
|---|---|---|---|---|
| Downlink 0.50-2 (ID 32) | BPSK/CDMA, turbo 1/4 | 312 | 1645 | -4.5 dB |
| Downlink 0.50-3 (ID 33) | BPSK, turbo 1/3 | 4280 | 13 171 | -3.6 dB |
| Downlink 1.50-2 (ID 34) | pi/4-QPSK, turbo 1/3 | 8320 | 13 150 | -0.6 dB |
| Downlink 1.50-1 (ID 26) | pi/4-QPSK, turbo 1/4 | 38 192 | 80 371 | -2.4 dB |
| Downlink 0.50-1 | BPSK/CDMA, 1/2 | - | - | -2.0 dB |
| Downlink 0.100 | BPSK/CDMA, 1/4 | - | - | -2.0 dB |
| Uplink 1.50-2 (ID 20) | QPSK/CDMA, 1/4 | 96 | - | -0.9 dB |

- Information bits are checked against channel bits x code rate.
- The code rates of IDs 26 and 27 are checked the same way: 76 458 x 2 x 1/4 = 38 229 ~ 38 192.
- The symbol rate is confirmed by C/N0 - Es/N0 = 45.3 dB-Hz -> 33.9 ksym/s [derived].
- The PER behind the thresholds is **not stated** in the tables.
- Most used: not found (VDE-SAT is still in trials). SAT-MCS-1.50-1 is the 33.6 ksym/s pilot format our C6 layout copies.

### 4.6 IEEE 802.11ad SC (DMG) [std via Wikipedia, MCS table and sensitivities; not read in the IEEE text]
- MCS 1-4 (pi/2-BPSK 1/2 with x2 repetition, 1/2, 5/8, 3/4): sensitivities -68 / -66 / -65 / -64 dBm. MCS 6 is
  pi/2-QPSK 1/2 at -63 dBm.
- Assumptions: 5 dB implementation loss, 10 dB noise figure, PER < 1 % at a 4 000-byte payload (confirmed by a search
  snippet).
- LDPC codeword 672 bits (Keysight page).
- Es/N0 = sensitivity + 174 - 10 log10(1.76e9) - 10 (NF) [derived]. With a 2.16 GHz noise bandwidth all values shift
  by +0.9 dB; I could not confirm which bandwidth the standard uses. The table subtracts the 5 dB implementation loss.
- SC blocks of 512 chips with a 64-chip guard interval (448 data). The rates confirm it: MCS 2 = 1760 x 448/512 x 0.5
  = 770 Mb/s.
- Far below our SE. It is not designed for low SNR.

### 4.7 LTE / NB-IoT uplink [std efficiencies; SNRs from papers / MathWorks, indicative only]
- The LTE CQI table gives QPSK code rates 78, 120, 193, 308, 449, 602 / 1024 (efficiencies 0.1523 ... 1.1758) (TS
  36.213 Table 7.2.3-1, via a patent text and sqimway).
- 3GPP gives no AWGN thresholds. The link-level paper read has CQI 1 at about -7 dB and ~2 dB between CQIs at **10 %
  BLER** (OFDM downlink).
- NB-IoT NPUSCH runs at low SNR **by repetition** (MathWorks example: TBS 136, 12 tones, QPSK, repetitions 2/16/64,
  only 5 TBs per SNR point).
- Not comparable: OFDM / SC-FDMA, HARQ, 10 % BLER operation. Our C10 uses only its pilot density.

### 4.8 MIL-STD-188-110C [std, read]
- Serial waveform AWGN requirements exist only at 2400 bps (SNR 10 dB / 3 kHz = Es/N0 10.97 dB, BER 1e-5) and
  4800 bps (17 dB, BER 1e-3).
- The low rates (75-1200 bps) are specified only in fading.
- App C (3200-12 800 bps) AWGN SNR runs from 9 dB (3200 bps) to 27 dB (12 800 bps).
- App D WBHF 3 kHz WID 1-6: BPSK 1/8, 1/4, 1/3, 2/3, 3/4, QPSK 3/4. Known symbols are 48/96 (WID 1-2), 32/128 (WID
  3-4) and 32/288 (WID 5-6).
- **Nothing in our Es/N0 range with an AWGN requirement.** The SE at 2400 Bd is 0.06-0.5 b/sym.

### 4.9 ViaSat / Advantech burst modems [vendor / patent]
- Not found: a public ViaSat or Advantech burst-modem datasheet with Es/N0 thresholds.
  - The ViaSat LinkWay S2 datasheet returned 404.
  - A search snippet (not read) lists DVB-RCS turbo 1/3 ... 6/7 with BPSK / QPSK / 8PSK return bursts.
- These return links use DVB-RCS / RCS2 waveforms, so section 4.3 is their best proxy.
- The Comtech DMD1050TS SCPC datasheet is the only vendor table read with guaranteed Eb/N0 at BER 1e-5 (continuous
  mode, long blocks). It is in the comparison table as the "real implementation" reference.

---

## 5. Per-source table

| Title | Year | Link | Relevance | Content used | Setting | Numbers |
|---|---|---|---|---|---|---|
| ETSI EN 302 307-1 V1.4.1 (DVB-S2) | 2014 | [PDF](https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf) | high | Table 13, Tables 5a / 5b, framing | LDPC + BCH 64 800 / 16 200, AWGN ideal, PER 1e-7 | QPSK 1/4 ... 3/5: -2.35, -1.24, -0.30, 1.00, 2.23 dB; SE 0.490-1.188; short +0.2-0.3 dB |
| ETSI EN 302 307-2 V1.1.1 (DVB-S2X) | 2015 | [PDF](https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.01.01_60/en_30230702v010101p.pdf) | high | Tables 4-6, 20a-c, VL-SNR frame (5.5.2) | FER 1e-5, AWGN ideal | see 4.2 |
| ETSI TR 101 545-4 V1.2.1 (DVB-RCS2 guidelines) | 2026 | [PDF](https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf) | high | clause 10.2.1 Tables 10.4-10.8 | turbo bursts 262-3236 symbols, AWGN ideal | see 4.3 |
| ETSI EN 301 545-2 V1.3.1 Table A-1 (via `lit_dvbrcs2.md`) | 2020 | [PDF](https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.03.01_60/en_30154502v010301p.pdf) | high | burst lengths, payload bytes, known symbols | | [prev], not re-read |
| ITU-R M.2092-2, Annex 2 Tables 9-11 | 2026 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf) | high | VDE-SAT formats, Es/N0 thresholds | turbo, 33.6 ksym/s, AWGN, PER not stated | -4.5 / -3.6 / -0.6 / -2.4 dB etc. |
| IALA G1139 ed. 3 | 2019 | [PDF](https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf) | medium | cross-check of the same tables | | same thresholds |
| CCSDS 130.1-G-3 (TM synchronization and channel coding, green book) | 2020 / 2024 | [PDF](https://public.ccsds.org/Pubs/130x1g3e1.pdf) | high | 7.4.1 turbo thresholds | turbo k 1784-8920, BER 1e-6 ~ FER 1e-4 | Eb/N0 -0.1 / 0.15 / 0.4 / 1.1 dB |
| Creonic CCSDS AR4JA LDPC product brief | 2023 | [PDF](https://www.aldec.com/files/ip_products/PB_Creonic_CCSDS_AR4JA_LDPC_FEC_IP.pdf) | high (same N, K as our 1/2) | BER / BLER table | 31 iterations, 6-bit | k 1024 r 1/2: 2.20 dB @ BLER 1e-5 |
| Comtech DMD1050TS datasheet | 2018 | [PDF](https://comtech.com/wp-content/uploads/2022/04/ds-DMD1050TS.pdf) | medium (real modem, SCPC) | Eb/N0 guaranteed / typical | BER 1e-5, continuous | see table |
| Wikipedia, WiGig (802.11ad MCS / sensitivity table) | - | [link](https://en.wikipedia.org/wiki/WiGig) | low | MCS 0-12 sensitivities | PER 1 %, 4 kB, 5 dB IL, NF 10 dB | -68 ... -53 dBm |
| Keysight 802.11ad concepts | - | [link](https://helpfiles.keysight.com/csg/n7637/Content/Main/802.11ad%20Concepts.htm) | low | LDPC 672 | | |
| MIL-STD-188-110C w/ Change 1 | 2011 / 2018 | [PDF](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf) | low | Tables XV, XVI, C-XVII, D-XI / D-XII / D-XLI | HF, SNR in 3 kHz | 2400 bps AWGN 10 dB |
| Ahmad, Kaleem, Chang, "BLER and UE throughput ... LTE downlink" | ~2013 | [arXiv 1810.01162](https://arxiv.org/pdf/1810.01162) | low | 10 % BLER CQI mapping (figure) | LTE DL OFDM AWGN | CQI 1 ~ -7 dB, ~2 dB / CQI |
| MathWorks NB-IoT NPUSCH BLER example | - | [link](https://www.mathworks.com/help/lte/ug/nb-iot-npusch-block-error-rate-simulation.html) | low | NPUSCH config | 12 tones, TBS 136, reps 2/16/64 | coarse (5 TBs) |
| Polyanskiy, Poor, Verdu, "Channel coding rate in the finite blocklength regime", IEEE T-IT 56(5) | 2010 | [PDF](https://www.math.chalmers.se/~hegarty/finite_block.pdf) | high (bounds our packet length) | normal approximation | AWGN | used for the NA column (formula via search / secondary text; the PDF did not decode here) |
| ViaSat LinkWay S2 datasheet | - | [link (404)](https://www.viasat.com/content/dam/us-site/government/documents/LinkWay_S2_Datasheet_018_web_1085053.pdf) | low | **not read** (search snippet only) | | |

---

## 6. Verdict per operating point (use / behind / not applicable)

| Our point | Best competitor SE at the same Es/N0 | Verdict |
|---|---|---|
| **1/10, -4.9 dB, 0.185** | CCSDS turbo 1/6, k 8920: 0.332 (x1.78). S2X BPSK 4/15 short: <= 0.244 (x1.32). S2X BPSK 11/45: 0.230 at 0.6 dB lower. VDE-SAT 0.50-2: 0.19 at +0.4 dB (x0.88). No DVB-RCS2 mode. | **Behind the long-block standards.** Only part of this is closable at 1024 symbols: the NA allows 0.30. The largest code gap of our four rates is here (~1.6 dB to the NA). Test idea, if wanted: one rate ~0.12-0.13 at -4.9 dB, or report Eb/N0 net (ours 2.44 dB vs 0.9-1.2 dB for S2X VL-SNR). |
| **0.15, -3.6 dB, 0.284** | VDE-SAT 0.50-3: 0.325 (x1.14). RCS2 ID 42: 0.304 (x1.13 ideal, x0.95 real). S2X BPSK 1/3 medium: 0.317 at -4.0 dB (x1.25). | **Slightly behind on paper (10-25 %).** Roughly a tie against the short-burst ID 42 once its real loss is counted. |
| **(gap) -2.9 ... -1 dB** | CCSDS turbo 1/4 (0.498 at -2.86), VDE-SAT 1.50-1 (0.475 at -2.4), S2 QPSK 1/4 (0.48 at -2.35), S2X 13/45 (0.55 at -2.03) | **We have no rate here.** Our 0.15 @ 1e-4 at -2.98 dB carries 0.284, against CCSDS 0.498 at -2.86 dB. A rate around 1/4 (SE ~0.48) would fill this gap. Not tested (main session decides). |
| **2/5, 0.61 dB, 0.784** | S2X QPSK 7/15 short: 0.874 (x1.12). S2 QPSK 2/5 normal: 0.77-0.79 at 0.9 dB lower. RCS2 ID 13 / VDE-SAT 1.50-2: ~0.6 (x0.8 at 0.61). | **Behind S2X by ~12 % at 16 200-bit frames.** Ahead of the short-burst standards. |
| **1/2, 1.79 dB, 0.984** | S2X QPSK 11/20 normal: 1.06 at 1.45 dB; 8/15 short: 1.00 at 1.45 dB; S2 QPSK 1/2: 0.97 at 1.00 dB; CCSDS turbo 1/2: 1.00 at 1.10 dB; RCS2 ID 14: 0.931 at 1.49 dB; CCSDS LDPC (2048, 1024): 0.985 at 2.20 dB @ 1e-5; Comtech QPSK turbo 1/2: 0.982 at 1.72 dB guaranteed | **Equal SE; the long-block standards need 0.3-0.8 dB less Es/N0.** Same-length LDPC (2048, 1024) is equal or behind (its 1e-5 vs our 1e-3). |

How much of this is pilots? Little. The pilot / header overhead of these standards costs:
- DVB-S2 normal with pilots: 2.4 % SE;
- S2X short: 2-3 %;
- VL-SNR: 7.5-10 %;
- RCS2 ID 13 / 14: 7-9 %;
- VDE-SAT: 2-5 %.

The SE differences in the table (+5-20 %) come mainly from block length (4-60x ours) and from code / decoder quality.
Our zero-overhead advantage is worth 2-10 % SE at the same code. In the est4 comparison on our code it shows up as
0.13-1.14 dB.

---

## Reference entries

1. ETSI EN 302 307-1 V1.4.1 (2014-11), "Digital Video Broadcasting (DVB); Second generation framing structure, channel
   coding and modulation systems for Broadcasting, Interactive Services, News Gathering and other broadband satellite
   applications; Part 1: DVB-S2".
   https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/en_30230701v010401p.pdf
   Taken: Table 13 (ideal Es/N0, SE), Tables 5a / 5b (K_bch), the PLHEADER / pilot / BBHEADER structure, the
   short-frame +0.2-0.3 dB note. Read through the r.jina.ai text reader.
2. ETSI EN 302 307-2 V1.1.1 (2015-02), "... Part 2: DVB-S2 Extensions (DVB-S2X)".
   https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/01.01.01_60/en_30230702v010101p.pdf
   Taken: Tables 4-6 (K_bch), Tables 20a / 20b / 20c (ideal Es/N0 at FER 1e-5), the VL-SNR frame sets (33 282 /
   16 686 symbols), the 900-symbol VL-SNR header. Read through r.jina.ai; Table 18a / 19a only partly legible.
3. ETSI TR 101 545-4 V1.2.1 (2026), "Digital Video Broadcasting (DVB); Second Generation DVB Interactive Satellite
   System (DVB-RCS2); Part 4: Guidelines for Implementation and Use of EN 301 545-2".
   https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf
   Taken: clause 10.2.1 AWGN ideal-sync Es/N0 at PER 1e-3 / 1e-5 for IDs 2-22, 42-49. Characters 440 000-600 000 read.
4. ETSI EN 301 545-2 V1.3.1 (2020), DVB-RCS2 Part 2: Lower Layers for Satellite standard, Annex A Table A-1.
   https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.03.01_60/en_30154502v010301p.pdf
   Taken (via `lit_dvbrcs2.md`, not re-read): burst lengths, payload bytes, known symbols.
5. ITU-R Recommendation M.2092-2 (02/2026), "Technical characteristics for a VHF data exchange system in the VHF
   maritime mobile band", Annex 2 Tables 9-11.
   https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf
   Taken: VDE-SAT link IDs 20-34, modulation, FEC rate, symbols, information bits, AWGN Es/N0, C/(N0+I0). Read through
   r.jina.ai; column mapping partly garbled, cross-checked by arithmetic.
6. IALA Guideline G1139, "The Technical Specification of VDES", Edition 3, June 2019.
   https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf
   Taken: a cross-check of the Tables 9-11 thresholds (-4.5 / -3.6 / -0.6 dB; FEC 1/4, 1/3, 1/3).
7. CCSDS 130.1-G-3 (2020, Editorial Change 1 2024), "TM Synchronization and Channel Coding - Summary of Concept and
   Rationale" (Green Book). https://public.ccsds.org/Pubs/130x1g3e1.pdf
   Taken: 7.4.1 turbo threshold bit-SNRs (-0.1, 0.15, 0.4, 1.1 dB for rates 1/6, 1/4, 1/3, 1/2 at BER 1e-6 ~ FER
   1e-4). Read through r.jina.ai, characters 100 000-200 000.
8. Creonic GmbH, "CCSDS AR4JA LDPC Encoder and Decoder - Product Brief", 2023.
   https://www.aldec.com/files/ip_products/PB_Creonic_CCSDS_AR4JA_LDPC_FEC_IP.pdf
   Taken: Eb/N0 at BER 1e-6 / 1e-7 / BLER 1e-5 for k = 1024 / 4096 / 16384, r = 1/2, 2/3, 4/5 (31 iterations,
   6-bit input).
9. Comtech EF Data, "DMD1050TS L-Band Satellite Modem Board" datasheet, 11/2018.
   https://comtech.com/wp-content/uploads/2022/04/ds-DMD1050TS.pdf
   Taken: guaranteed / typical Eb/N0 at BER 1e-5 for Viterbi, TPC, STANAG 4486 turbo and LDPC modes, with bandwidth
   efficiency.
10. Wikipedia, "WiGig" (IEEE 802.11ad MCS and sensitivity table). https://en.wikipedia.org/wiki/WiGig
    Taken: MCS 0-12 modulation, rate, PHY rate, sensitivity. Secondary source; the IEEE 802.11ad text was not read.
    Assumptions (5 dB implementation loss, 10 dB NF, PER < 1 % at 4 000 bytes) are from a search snippet of a paper
    that regenerates Table 21-3 (core.ac.uk 194621121, 403, not read).
11. Keysight, "802.11ad Concepts", N7637 help. https://helpfiles.keysight.com/csg/n7637/Content/Main/802.11ad%20Concepts.htm
    Taken: LDPC codeword 672 bits.
12. MIL-STD-188-110C with Change Notice 1, "Interoperability and Performance Standards for Data Modems".
    https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf
    Taken: Tables XV, XVI (serial waveform structure and performance), C-XVII (App C AWGN SNR), D-XI / D-XII / D-XLI
    (WBHF 3 kHz data / probe symbols and code rates). Read through r.jina.ai; Table D-LII not legible.
13. I. Ahmad, Z. Kaleem, K. Chang, "Block Error Rate and UE Throughput Performance Evaluation using LLS and SLS in
    3GPP LTE Downlink", arXiv:1810.01162. https://arxiv.org/pdf/1810.01162
    Taken: CQI mapping at 10 % BLER, AWGN (figure only), ~2 dB spacing (text).
14. 3GPP TS 36.213, Table 7.2.3-1 (4-bit CQI table), as reproduced in US patent 10079655 and on sqimway.com.
    https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10079655 ; https://sqimway.com/nr_pdsch.php
    Taken: QPSK code rates x 1024 and efficiencies (search-result text; the 3GPP document itself was not opened).
15. MathWorks, "NB-IoT NPUSCH Block Error Rate Simulation".
    https://www.mathworks.com/help/lte/ug/nb-iot-npusch-block-error-rate-simulation.html
    Taken: example NPUSCH configuration only.
16. Y. Polyanskiy, H. V. Poor, S. Verdu, "Channel Coding Rate in the Finite Blocklength Regime", IEEE Trans. Inf.
    Theory, vol. 56, no. 5, pp. 2307-2359, May 2010. https://www.math.chalmers.se/~hegarty/finite_block.pdf
    Taken: the normal approximation (formula confirmed through search results and course notes; the PDF did not decode
    here).
17. ViaSat, LinkWay S2 datasheet.
    https://www.viasat.com/content/dam/us-site/government/documents/LinkWay_S2_Datasheet_018_web_1085053.pdf
    **Not read** (404); a search snippet mentions DVB-RCS turbo 1/3 ... 6/7 return bursts. Nothing taken.

## Recomputed finite-length bound (main session, 2026-11-15)
Normal approximation (Polyanskiy-Poor-Verdu) for QPSK = 2 x BI-AWGN, n = 2048 real channel uses (1024 QPSK symbols),
log2 M ~ nC - sqrt(nV) Q^-1(eps) + 0.5 log2 n, C and V by numerical integration (check: QPSK capacity at Es/N0 0 dB
= 0.972 bits/symbol). Replaces the hand estimate above.

| Our point | QPSK capacity [bits/sym] | Max SE of any 1024-symbol packet | Ours | Ours / max |
|---|---|---|---|---|
| 1/10, -4.9 dB, 1e-4 | 0.403 | 0.300 | 0.185 | 0.62 |
| 0.15, -3.6 dB, 1e-3 | 0.520 | 0.427 | 0.284 | 0.67 |
| 2/5, 0.61 dB, 1e-3 | 1.065 | 0.959 | 0.784 | 0.82 |
| 1/2, 1.79 dB, 1e-3 | 1.251 | 1.149 | 0.984 | 0.86 |
