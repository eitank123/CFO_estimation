# VDE channel coding (FEC) mechanics: what is needed for a bit-exact Python implementation

Literature scout, 2026-11-17. Scope: ONLY the VDE (ITU-R M.2092) FEC chain: turbo code, interleaver law and parameters,
puncturing, tail, CRC, scrambler, channel interleaver, mapping, decoder cost, test vectors, reference FER curves.
Burst formats / syncwords / pilots (incl. Link 32 layout) are in `lit_vdesat_fullsystem.md`; this file adds the full
Table 4 for every VDE block size with arithmetic checks, the A3-8 test vector, scrambler seed, pi/4-QPSK map, a
re-read of Table 63, the code's relation to LTE / 3GPP2 / MATLAB, the decoder and its op count, and the published
PER numbers at VDE block sizes.

Primary source: the full local text `testing/results/standards/ITU-R_M.2092-2_2026.txt` (pdftotext of ITU-R
M.2092-2, 02/2026) [M2092], cross-checked with an earlier web reading of the same PDF; `ITU-R_M.2435_2018.txt`
[M2435]. Figures are images and are NOT in the text; the Read tool cannot render the PDFs on this machine
(pdftoppm missing), so M.2092 Figs 7-13 and M.2435 Figs 11-12 were **not seen**. Secondary: IALA G1139 ed. 3 (2019)
[G1139], ETSI EN 302 583 V1.2.1 (DVB-SH) [SH], Kim 2025 VDES turbo decoder [Kim]. Tags: [chk] = closes by arithmetic
against another table / the worked example; [derived] = my arithmetic; **AMBIGUITY** = still open.

## 1. Answer in short

1. **Not the LTE (36.212, QPP) or UMTS (25.212) turbo code.** It is the **3GPP2 / cdma2000 / DVB-SH 8-state turbo
   code with two parities per RSC (rate-1/5 mother)**: "The overall structure follows ... ETSI EN 302 583"
   [M2092 A2-1.2.4.1]; [SH 5.3]: "The Turbo Code as standardized by the 3GPP2 organization shall be used". The
   **interleaver is the CCSDS 131.0-B-2 law with VDE-specific k1, k2 and primes per Link ID** [M2092 A2-1.2.4.3]
   (not the DVB-SH bit-reversal interleaver).
2. RSC: G(D) = [1, n0(D)/d(D), n1(D)/d(D)], d = 1 + D^2 + D^3, n0 = 1 + D + D^3, n1 = 1 + D + D^2 + D^3, 3 memory
   cells, start state 0 [M2092 A2-1.2.4.2 lines 678-688; SH 5.3.1 identical]. RSC1 outputs X, Y0 (= n0), Y1 (= n1);
   RSC2 (on the interleaved input u') outputs X', Y'0, Y'1.
   - Recursion [derived]: a_k = u_k + a_{k-2} + a_{k-3}; y0_k = a_k + a_{k-1} + a_{k-3}; y1_k = a_k + a_{k-1} +
     a_{k-2} + a_{k-3} (mod 2).
   - Y0 = n0 confirmed by the A3-8 example (section 0.2); the G1139 OCR order [1, n1/d, n0/d] is wrong.
   - d and n0 are the LTE pair, so for puncturing IDs that use only Y0 / Y'0 (4, 6, 7a, 7b, 9) the data part equals an
     LTE-constituent turbo code with another interleaver and tail [derived]. IDs 2 (1/4) and 8 (3/4) use Y1 / Y'1.
   - MATLAB `poly2trellis(4,[13 15 17],13)` (MATLAB octal, leftmost = D^0) is exactly this RSC [derived].
3. Termination: 6 clocks after the k data clocks. Clocks 1-3: RSC1 with the switch in position (b) (input = feedback,
   register flushes to 0), output X, Y0, Y1; clocks 4-6: RSC2 likewise, X', Y'0, Y'1. "with X output first"; then
   puncturing / repetition by Table 6 [M2092 lines 690-695]. Link 34 has no tail. **AMBIGUITY (small)**: Fig. 8
   (switch wiring) not seen; the text plus the 3GPP2 / DVB-SH rule are unambiguous, and the A3-8 test vector checks it.
4. Output order per data period: X, Y0, Y1, X', Y'0, Y'1 masked by Table 5 ("read first from left to right and then
   from top to bottom"); then the 6 tail periods by Table 6.
5. CRC (appended to the last segment of the datagram, one per datagram): CRC-32 x^32+x^26+x^23+x^22+x^16+x^12+x^11+
   x^10+x^8+x^7+x^5+x^4+x^2+x+1 (0x04C11DB7), init 0xFFFFFFFF; CRC-16 x^16+x^15+x^2+1 (0x8005), init 0x0000, Link 20
   only; MSB of each byte first, appended MSB first, over payload + zero padding; check = all-zero register after
   data + padding + CRC [M2092 A2-1.2.5]. No reflection and no final XOR are stated ("equivalent to ITU-T H.222.0" =
   CRC-32/MPEG-2) [derived]. **k of Table 4 includes the CRC** (A3-8: 256 + 32 = 288 = k of Link 5).
   **AMBIGUITY**: for multi-block bursts (Links 24, 26-31, 34) the text says the CRC is computed "over all fragments
   of the datagram" and appended to the last segment, but Table 4 gives every sub-block the same k. Whether every
   FEC sub-block carries its own CRC-32 or only the last one was not resolved (lit_vdesat_fullsystem.md assumed one
   per block). For our single-block comparisons it does not matter.
6. Scrambler: F(x) = 1 + x^-14 + x^-15, re-initialised every packet, MSB first, after FEC and before mapping
   [M2092 A2-1.2.6]. **Seed: 100101010000000 (the DVB PRBS), recovered from A3-8** (section 0.2) - Fig. 9 not seen.
7. Channel interleaver: VDE-SAT downlink only (A5-2.13), after the scrambler, before burst stuffing bits; parameters
   re-read in section 0.3. None on VDE-TER / uplink (none found in Annex 2 / 4). No effect on AWGN BLER.
8. Mapping: pi/4-QPSK map recovered from A3-8 (section 0.2). BPSK, 8PSK, 16QAM maps (Figs 10, 12, 13): **not
   obtained** (images).

## 0. Update from the local full text: test vector, seed, map, Table 63, M.2435

### 0.1 A3-8 worked example, full bit strings
Link 5: k = 288, k1 x k2 = 2 x 144, primes 47 17 233 127 239 139 199 163, puncturing ID 8, tail ID 8b. Copied from
lines 3303-3338 of `ITU-R_M.2092-2_2026.txt` (57 bits per printed line; lengths 256 / 288 / 394 / 394 by line count
[chk]). The main session should load these from the .txt by code (my copy is a visual transcription) and assert
bit equality for CRC, encoder and scrambler:

    (b) bit-packed payload, 256 bits (103 message bits + 153 zero padding)
    010100011100000000111010110111100110100010101001110101101
    111001101000101100010000000000000000000110010000000000000
    000000000000000000000000000000000000000000000000000000000
    000000000000000000000000000000000000000000000000000000000
    0000000000000000000000000000
    (c) turbo input = payload + CRC-32, 288 bits
    010100011100000000111010110111100110100010101001110101101
    111001101000101100010000000000000000000110010000000000000
    000000000000000000000000000000000000000000000000000000000
    000000000000000000000000000000000000000000000000000000000
    000000000000000000000000000001011010111100101001010001111
    100
    (d) turbo coded with flushing, 394 bits (288 x 4/3 = 384 + 10 tail)
    001010000011100000000001111101011110111110001100110001011
    001001011101011110111100001101100001011100001000100000100
    000001000000001010010100000000000000000000000100000001000
    000010000000100000001000000010000000000000000000000010000
    000000000001000000010000000000000000000000010000000000000
    000000000010000000100000001000000010000000100000001000000
    1101110100111110011101001001100010101110011111010001
    (e) scrambled, 394 bits
    001010111100111000001001110000011101111100110100011001100
    000000100100010101101101010110001111000001101110110100010
    101011111101010101101100111100000001001000100100011010001
    100010101101110100000110111101100010011000000100110111000
    001101011110000010101100001000111000100011011001001100101
    011011010111111101001111111000110100000010101011011000110
    1010101000101011010001101110011000000011011110101111

Then (f): 27 syncword + 16 Link ID + 197 data pi/4-QPSK symbols, printed as (+0.7,+0.7), (+1.0,+0.0), ... (lines
3340-3383), a symbol-level test vector for the mapper.

### 0.2 What the example settles (hand checks; code must confirm over all bits)
- CRC-32 of the example = last 32 bits of (c) = 01011010 11110010 10010100 01111100 = **0x5AF2947C** [derived from
  the printed string].
- **Puncturing ID 8 positions**: per 6 info bits, 8 coded bits [X1, P, X2, X3, X4, X5, X6, P'] - info 010100 ->
  0010100?, 011100 -> 0011100?, 000000 -> 0000000?, 111010 -> 11110101 [chk, first 4 groups].
- **Parity P of ID 8 is the n1 = 1+D+D^2+D^3 output (Y1)**: the RSC run by hand over u = 0101000 gives at bit 7
  y0 = 1, y1 = 0; the printed coded bit is 0 [chk, one discriminating bit]. This also supports the feedback
  polynomial and wiring. P' (RSC2 parity) depends on the interleaver: not checked by hand.
- **Scrambler seed**: (d) XOR (e), first 32 bits = 00000011 11110110 00001000 00110100 = 0x03 F6 08 34 = the first
  output of the DVB energy-dispersal PRBS 1 + x^14 + x^15 with init **100101010000000** [chk on 32 bits; the same
  PRBS as DVB-S / DVB-S2 / DVB-SH].
- **pi/4-QPSK map (absolute, not differential)** [chk on the syncword (bit 1 -> dibit 11, 0 -> 00) and the first 8
  data symbols]: even symbol index (set A): dibit b0 b1 -> ((2b0 - 1) + j(2b1 - 1))/sqrt2, i.e. 11 -> (+,+),
  10 -> (+,-), 00 -> (-,-), 01 -> (-,+); odd index (set B): the same point rotated by -45 deg: 11 -> 1, 01 -> j,
  00 -> -1, 10 -> -j. The index runs continuously from the first syncword symbol through Link ID and data (data
  start at index 43, odd: first data dibit 00 -> (-1, 0) as printed). First scrambler bit -> MSB (b0).
- Table 6 in the .txt is **shifted by one row** (first pattern line unlabelled; the line labelled "0 1/5" holds the
  2/9 pattern, ..., "8b" holds pattern 9). Re-aligned it equals section 3, and every tail count then matches Tables
  7-11 [chk]. Table 4 in the .txt is also broken across columns; section 2 is the re-aligned version. Do not parse
  either table from the .txt naively.

### 0.3 Table 63 (VDE-SAT downlink channel interleaver), re-read from the .txt
Row labels are shifted one line (label "M" sits on the LCID row) and the cells of LCID 26 and 27 sit one line lower
than the others (they hold the IB values 5 and 4 on the "Ar" line). Re-aligned:

| LCID | 25 | 26 | 27 | 28 | 29 | 32 | 33 | 34 |
|---|---|---|---|---|---|---|---|---|
| M | 14 | 257 | 503 | 16 | 132 | 27 | 857 | 128 |
| N | 683 | 119 | 114 | 1321 | 202 | 47 | 15 | 195 |
| L = M N | 9562 | 30583 | 57342 | 21136 | 26664 | 1269 | 12855 | 24960 |
| IB | 1 | 5 | 4 | 4 | 5 | 1 | 1 | 1 |
| Ar | 5 | 127 | 251 | 7 | 61 | 13 | 421 | 51 |
| Br | 3 | 107 | 223 | 13 | 31 | 17 | 367 | 89 |
| Ac | 337 | 59 | 53 | 659 | 97 | 23 | 7 | 97 |
| Bc | 71 | 41 | 11 | 59 | 59 | 13 | 3 | 19 |

Law [M2092 A5-2.13]: written by rows into M x N, read by columns after the permutations
pr(m) = 1 + (Ar m + Cr(n)) mod M, Cr(n) = (Br n - 1) mod M; pc(n) = 1 + (Ac n + Cc(m)) mod N, Cc(m) = (Bc m - 1) mod N;
"relocating the bit appearing at row pr(m) to row m, and ... column pc(n) ... to column n".
Checks [chk]: L x IB = channel bits of Tables 10-11 for all eight; gcd(Ar, M) = 1 and gcd(Ac, N) = 1 for all eight.
**AMBIGUITY**: Ar and Br agree with lit_vdesat_fullsystem.md 1.5, but **Ac and Bc do not** (that file: Ac = 3 37 59
53 659 97 23 797, Bc = 7 1 41 11 59 59 13 319, from a garbled web reading). My reading comes from the clean local
column structure (confidence medium-high); the other one is also coprime, so arithmetic cannot decide. Confirm on the
PDF page (Rec. p. 122) before a bit-exact competitor run. Also open: whether pr depends on n (Cr(n)) means the row
permutation differs per column - the formula says so; implement literally. AWGN BLER does not depend on this table.

### 0.4 M.2435 4.3.1 (validation target)
QPSK, turbo rate 1/4 "according to ETSI EN 302 583 (V1.2.1)", **88 information bits** per packet, AWGN: Es/N0
**-1.5 dB at PER 1e-2** (Fig. 11), **-0.3 dB at BER 1e-5** (Fig. 12); "a conservative design point" [M2435 lines
1134-1188]. Eb/N0 per info bit = Es/N0 + 3.0 dB -> +1.5 dB at PER 1e-2 [derived]. Cross-reference given there: CCSDS
130.1-G-2 Fig. 7-6, k = 1784, rate 1/4: Eb/N0 0.55 dB at BER 1e-5 (-2.45 dB Es/N0) - a different (16-state CCSDS)
code. Caveats: decoder, iterations, interleaver and CRC are not stated; it cites M.2092-0 / DVB-SH (so possibly the
DVB-SH interleaver, not the current Table 4 law); 88 bits is not a Table 4 size (closest: Link 20, k = 96 incl.
CRC-16). Other points of Figs 11-12: **not readable** (plots lost in pdftotext, page rendering unavailable here).

## 2. Turbo interleaver (all VDE block sizes)

Law [M2092 A2-1.2.4.3, CCSDS 131.0-B-2 form; the .txt lost the symbols, the web reading and G1139 give them],
k = k1 * k2, k1 even, s = 1..k:

    m = (s-1) mod 2
    i = floor((s-1) / (2*k2))
    j = floor((s-1)/2) - i*k2
    t = (19*i + 1) mod (k1/2)
    q = (t mod 8) + 1
    c = (p_q * j + 21*m) mod k2
    pi(s) = 2*(t + c*k1/2 + 1) - m      # "the s-th bit read out after interleaving is the pi(s)-th bit of the input"

**AMBIGUITY (small)**: the operator in "p_q j" is not rendered in any text read (CCSDS original: product). Unit test:
pi must be a permutation of 1..k for every row; the A3-8 vector (P' bits) then confirms. In CCSDS k1 = 8; VDE uses
k1 = 2..16, so for k1/2 < 8 only some primes are used [derived].

"Default" primes = 31 37 43 47 53 59 61 67 (the CCSDS set). Table 4 re-aligned (last column: channel bits of Tables
7-11 = blocks x (coded data + tail + padding) [chk, all rows checked except 30, 31]):

| Link | Use | Rate | k (incl. CRC) x blocks | k1 x k2 | p1..p8 | Punct / tail | Check [chk] |
|---|---|---|---|---|---|---|---|
| 4 | ASM SAT | 3/4 | 952 | 4 x 238 | 113 31 59 163 29 181 101 11 | 8 / 8a | 952 = 158x6+4 -> 158x8+5 = 1269, +11 = 1280 |
| 5 | ASM | 3/4 | 288 | 2 x 144 | 47 17 233 127 239 139 199 163 | 8 / 8b | 384 + 10 = 394 (= A3-8) |
| 6 | ASM | 3/4 | 672 | 2 x 336 | 37 101 191 149 79 131 229 31 | 8 / 8b | 896 + 10 = 906 |
| 7 | ASM | 3/4 | 1056 | 4 x 264 | 23 31 167 223 59 113 47 211 | 8 / 8b | 1408 + 10 = 1418 |
| 8, 9, 10 | (1) | 1/2 | 192 / 448 / 704 | 2 x 96 / 2 x 224 / 2 x 352 | default | 6 / 6 | "default suggested, no simulations" |
| 11 | TER 25 kHz pi/4-QPSK | 1/2 | 432 | 2 x 216 | 127 191 241 5 83 109 107 179 | 6 / 6a | 864 + 10 = 874 |
| 12 | TER 25 kHz 8PSK | 3/4 | 972 | 2 x 486 | default | 8 / 8 | 1296 + 12 = 1308 (+3 pad = 1311) |
| 13 | TER 25 kHz 16QAM | 3/4 | 1296 | 2 x 648 | default | 8 / 8 | 1728 + 12 = 1740 (+8 = 1748) |
| 14 | TER 50 kHz pi/4-QPSK | 1/2 | 896 | 2 x 448 | default | 6 / 6 | 1792 + 12 = 1804 (+30 = 1834) |
| 15 | TER 50 kHz 8PSK | 3/4 | 2016 | 4 x 504 | default | 8 / 8 | 2688 + 12 = 2700 (+51 = 2751) |
| 16 | TER 50 kHz 16QAM | 3/4 | 2688 | 4 x 672 | default | 8 / 8 | 3584 + 12 = 3596 (+72 = 3668) |
| 17 | TER 100 kHz pi/4-QPSK | 1/2 | 1872 | 6 x 312 | 211 61 227 239 181 79 73 193 | 6 / 6a | 3744 + 10 = 3754 |
| 18 | TER 100 kHz 8PSK | 3/4 | 4032 | 4 x 1008 | default | 8 / 8 | 5376 + 12 = 5388 (+243 = 5631) |
| 19 | TER 100 kHz 16QAM | 3/4 | 5616 | 16 x 351 | 137 101 223 41 67 131 61 47 | 8 / 8 | 7488 + 12 = 7500 (+8 = 7508) |
| 20 | SAT UL RA | 1/4 | 96 (CRC-16) | 2 x 48 | 37 83 211 61 107 101 149 167 | 2 / 2a | 384 + 18 = 402 |
| 21 | SAT UL pi/4-QPSK | 2/3 | 736 | 2 x 368 | 139 17 241 47 109 11 29 163 | 7a / 7a | 1104 + 8 = 1112 |
| 22 | SAT UL 8PSK | 2/3 | 3120 | 16 x 195 | 89 47 239 17 127 59 43 31 | 7a / 7b | 4680 + 12 + 4 pad = 4696 |
| 23 | SAT UL 16QAM | 2/3 | 4544 | 4 x 1136 | default | 7b / 7b | 6816 + 12 + 3 = 6831 |
| 24 | SAT UL 16QAM | 5/6 | 3788 x 2 | 4 x 947 | 127 251 227 173 139 149 101 7 | 9 / 9 | 378x12+10 = 4546, +8 = 4554, x2 = 9108 |
| 25 | SAT DL bulletin, BPSK/CDMA | 1/2 | 4776 | 12 x 398 | default | 6 / 6a | 9552 + 10 = 9562 |
| 26 | SAT DL pi/4-QPSK (1.50-1) | 1/4 | 5456 x 7 | 16 x 341 | 37 41 43 47 53 59 61 67 | 2 / 2a | 7 x (21824 + 18 + 3 pad) = 152915 |
| 27 | SAT DL 8PSK | 1/2 | 6032 x 19 | 16 x 377 | default | 6 / 6b | 19 x (12064 + 8) = 229368 |
| 28 | SAT DL BPSK/CDMA | 1/4 | 5280 x 4 | 16 x 330 | default | 2 / 2b | 4 x (21120 + 16) = 84544 |
| 29 | SAT DL | 1/4 | 5552 x 6 | 16 x 347 | default | 2 / 2c | 6 x (22208 + 12) = 133320 |
| 30 | (optional) | 1/4 | 5320 x 13 | 14 x 380 | default | 2 / 2c | not checked |
| 31 | (optional) | 1/4 | 5328 x 22 | 16 x 333 | 31 41 43 47 53 59 61 67 | 2 / 2d | not checked |
| 32 | SAT DL BPSK/CDMA SF 8 | 1/4 | 312 | 2 x 156 | 37 79 29 139 151 97 181 157 | 2 / 2e | 1248 + 21 = 1269 |
| 33 | SAT DL BPSK | 1/3 | 4280 | 8 x 535 | 59 37 157 167 239 83 163 29 | 4 / 4a | 12840 + 15 = 12855 |
| 34 | SAT DL pi/4-QPSK (1.50-2) | 1/3 | 4160 x 2 | 16 x 260 | 163 157 149 137 197 47 241 251 | 4 / none | 2 x 12480 = 24960 |

TER padding values in parentheses are [derived] (channel bits minus coded + tail). Link 26 primes 37 41 ... and the
Link 31 set 31 41 ... are as printed (both readings agree). **AMBIGUITY**: the .txt places the Link 26 / 27 prime
lists on separate lines (26 = 37|41|..., 27 = default); both readings agree, but check on the page.

## 3. Puncturing (Table 5, data) and tail (Table 6)

One 6-digit group per input bit period, order X Y0 Y1 X' Y'0 Y'1 (1 send, 0 delete, 2 / 3 = copies). Lp = number of
groups. Rate = Lp / (number of ones) checked for all [chk]. IDs 0-4, 6 equal the 3GPP2 / DVB-SH patterns; ID 8
positions confirmed by A3-8 (section 0.2); the local .txt Table 5 is aligned and matches this table exactly.

| ID | Rate | Lp | Pattern (period 1 / period 2 / ...) |
|---|---|---|---|
| 0 | 1/5 | 1 | 111011 |
| 1 | 2/9 | 4 | 101011 / 111011 / 111001 / 111011 |
| 2 | 1/4 | 2 | 111001 / 110011 |
| 3 | 2/7 | 4 | 101001 / 101011 / 101001 / 111001 |
| 4 | 1/3 | 1 | 110010 |
| 5 | 2/5 | 12 | 100000 / 101001 / 001001 / 101001 / 101001 / 001001 / 101001 / 101001 / 001001 / 101001 / 101001 / 001001 (as printed; not used by any Link) |
| 6 | 1/2 | 2 | 110000 / 100010 |
| 7 | 2/3 | 4 | 100000 / 100000 / 100000 / 101001 |
| 7a | 2/3 | 4 | 100000 / 100000 / 100000 / 110010 |
| 7b | 2/3 | 4 | 100000 / 110000 / 100000 / 100010 |
| 8 | 3/4 | 6 | 101000 / 100000 / 100000 / 100000 / 100000 / 100001 |
| 9 | 5/6 | 10 | 100000 / 110000 / 100010 / 100000 x 7 |

Tail (6 groups = tail clocks 1..6), re-aligned (see 0.2):

| ID | Groups | Tail bits [chk] |
|---|---|---|
| 2a | 111000 x3 / 000111 x3 | 18 |
| 2b | 111000 / 111000 / 110000 / 000111 / 000111 / 000110 | 16 |
| 2c | 110000 x3 / 000110 x3 | 12 |
| 2d | 110000 / 100000 / 100000 / 000110 / 000100 / 000100 | 8 |
| 2e | 211000 / 211000 / 210000 / 000211 / 000211 / 000200 | 21 |
| 4a | 210000 / 210000 / 200000 / 000210 / 000210 / 000010 | 15 |
| 6 | 110000 x3 / 000110 x3 | 12 |
| 6a | 110000 / 110000 / 100000 / 000110 / 000110 / 000100 | 10 |
| 6b | 110000 / 100000 / 100000 / 000110 / 000100 / 000100 | 8 |
| 7a | 110000 / 100000 / 100000 / 000110 / 000100 / 000100 | 8 |
| 7b | 110000 x3 / 000110 x3 | 12 |
| 8 | 101000 x3 / 000101 x3 | 12 |
| 8a | 101000 x3 / 000101 / 000101 / 000100 | 11 |
| 8b | 101000 / 101000 / 100000 / 000101 / 000101 / 000100 | 10 |
| 9 | 110000 / 100000 / 100000 / 000110 / 000100 / 000100 | 8 |

(IDs 0, 1, 2, 3, 4, 5, 7 also exist; unused by any Link.) A tail "2" means the symbol is sent twice: the decoder
adds the two LLRs. Number of coded data bits when k mod Lp = R != 0 [M2092 A2-1.2.4.5]: floor(k/Lp) x (ones per
period) + ones in the first R groups (used for Links 4, 24).

## 4. Decoder (M.2092 specifies none; receiver choice)

- Standard: iterative BCJR, log-MAP or max-log-MAP (extrinsic scaling ~0.7 for max-log), 6-8 iterations, early stop
  on CRC. [Kim]: log-MAP with max* by a 128-entry LUT for |x - y| < 4, sliding window 32, 6 iterations; max-log-MAP
  "noticeable degradation at low SNR" (no dB number in the text read). [Robertson 1995, abstract]: SOVA ~0.7 dB
  worse than log-MAP at BER 1e-4, max-log-MAP in between.
- Punctured symbols -> LLR 0; repeated tail symbols -> LLR sum.
- **Ops per info bit per full iteration [derived]** (8 states, 2 branches, 3 soft inputs per step; add and
  compare-select = 1 op):

  | Step (one SISO, one trellis step) | max-log-MAP ops |
  |---|---|
  | branch metrics (8 values from 3 LLRs, sign symmetry) | 6 |
  | forward alpha: 8 x (2 add + 1 max) + 8 normalisation | 32 |
  | backward beta: same | 32 |
  | LLR: 16 x 2 add + 2 x 7 max + 1 sub + 2 extrinsic sub | 49 |
  | **per SISO** | **~119** |
  | **per iteration (2 SISOs)** | **~240 per info bit** |

  Log-MAP: + LUT and add on each of 30 max ops -> ~360 per info bit per iteration. Sliding-window warm-up (W = 32)
  adds ~32 per SISO. Examples [derived]: k = 5456 (Link 26 block), max-log, 8 iterations: 10.5 M ops per block,
  73 M per 7-block burst; k = 312 (Link 32), 8 iterations: 0.60 M ops; k = 323 (our 0.15 packet incl. CRC-16):
  0.62 M ops. These are add / compare ops, not multiplies; state the convention when putting them beside our polar
  "MACs".
- Parallelism: P windows with P SISOs; critical path ~ (k/P + warm-up) x 2 x iterations trellis steps [derived;
  general practice].

## 5. Test vectors and implementations to verify a Python codec

| What | Use | Status |
|---|---|---|
| **M.2092-2 A3-8** (section 0.1) | bit-exact test of CRC-32, interleaver (Link 5), RSC wiring, ID 8 / 8b puncturing, tail, scrambler seed, pi/4-QPSK map (symbol list) | **full strings available** in the local .txt |
| MATLAB `comm.TurboEncoder` with `poly2trellis(4,[13 15 17],13)`, `InterleaverIndices` = pi, custom `OutputIndices` | independent reference | per-encoder tails appended at the end in the VDE order; repetitions done outside; not run (no MATLAB) |
| MATLAB `lteTurboEncode` | not usable (QPP interleaver, LTE tail, no Y1) | - |
| AFF3CT (`--itl-type USER` from a file; RSC {013,015}) | partial: Y0-only patterns | tail differs |
| Sionna `TurboEncoder` | 3GPP interleaver only (as documented) | not suitable unmodified |
| VDES-specific open source codec | none found | - |

## 6. Published PER / FER at VDE block sizes (AWGN)

| Source | Block / rate / mod | Number |
|---|---|---|
| [M2435 4.3.1] simulation, decoder unknown | 88 info bits, 1/4, QPSK | **Es/N0 -1.5 dB at PER 1e-2; -0.3 dB at BER 1e-5** |
| [M2092 Table 8] VDE-TER threshold (PER not in the table; Table 34 sensitivities are at PER 1 %) | 432 / 896 / 1872, 1/2, pi/4-QPSK | 1.0 dB; 8PSK 3/4: 7.9 dB; 16QAM 3/4: 10.2 dB |
| [M2092 Tables 9-11] VDE-SAT thresholds (PER 1e-2 per M.2435 Table 13 for the uplink) | Link 20: -0.9 dB; 26: -2.4 dB; 32: -4.5 dB; 33: -3.6 dB; 34: -0.6 dB; 25: -2.0 dB; 27: 5.0 dB | CDMA formats: check whether per chip or per symbol |
| [Kim 2025] log-MAP, 6 it., PER 1 % | Link 11 (432, 1/2, pi/4-QPSK) | Es/N0 2.1 dB |
| same | Link 17 (1872, 1/2) | 1.5 dB |
| same | Link 19 (5616, 3/4, 16QAM) | 13 dB (looks high vs 10.2 dB; not explained) |

Note [derived]: Kim's 2.1 dB at 432 bits is ~1 dB above M.2092's 1.0 dB TER threshold; M.2435's -1.5 dB at 88 bits
rate 1/4 is "conservative". No full FER curve of this exact code at VDE sizes was read. Comparability with our
N = 2048 polar packets: similar sizes are Link 32 (312, 1/4), 11 (432, 1/2), 21 (736, 2/3), 4 / 12 (952 / 972, 3/4),
7 (1056, 3/4). Our own sizes (e.g. 307 + 16 = 323, odd -> needs padding to an even k1 x k2) have no ITU parameters:
any non-tabled k is our design and must be labelled so.

## 7. Remaining ambiguities / not obtained (explicit list)

1. Table 63 Ac and Bc: two readings disagree (section 0.3) - confirm on the PDF page.
2. CRC per FEC sub-block vs per burst for multi-block links (section 1 item 5).
3. Interleaver operator "p_q j" (product assumed) and Fig. 8 wiring - both settled by passing the A3-8 test vector.
4. 8PSK, 16QAM and BPSK maps (Figs 10, 12, 13): not obtained.
5. M.2435 Figs 11-12 other points; their interleaver / decoder.
6. Kim Figs 5-6 numbers; ICDSP 2020 paper (ACM 403); Robertson 1997 ETT complexity table.
7. The .txt Tables 4 and 6 are mis-aligned by pdftotext (handled in sections 2-3).

## Sources

| Source | Year | Link | Read depth | Relevance |
|---|---|---|---|---|
| ITU-R M.2092-2 | 2026 | https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf | full local text + web reader; figures not seen | high: defines everything |
| ITU-R M.2435-0 | 2018 | https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-M.2435-2018-PDF-E.pdf | local text 4.3.1; figures not seen | high: only PER / BER numbers for the code |
| IALA G1139 ed. 3 | 2019 | https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf | chars 0-100k via reader | medium: cross-check |
| ETSI EN 302 583 V1.2.1 (DVB-SH) | 2011 | https://www.etsi.org/deliver/etsi_EN/302500_302599/302583/01.02.01_60/en_302583v010201p.pdf | 5.3 via reader | high: 3GPP2 code, polynomials, termination |
| J. H. Kim, J. KICS 50(3), 2025, doi:10.7840/kics.2025.50.3.489 | 2025 | https://d2j16w31g89z0j.cloudfront.net/journal/jkics/fullText/1387/jkics-2503-12.pdf | text via reader | high: VDES decoder, PER numbers |
| "Iterative decoding algorithm for VDES signals", ICDSP 2020, doi:10.1145/3408127.3408158 | 2020 | https://dl.acm.org/doi/10.1145/3408127.3408158 | snippet only (403) | low-medium |
| MathWorks comm.TurboEncoder | current | https://www.mathworks.com/help/comm/ref/comm.turboencoder-system-object.html | page | medium |
| AFF3CT docs (turbo encoder, interleaver) | current | https://aff3ct.readthedocs.io/en/latest/user/simulation/parameters/interleaver/interleaver.html | pages | low-medium |
| Robertson, Villebrun, Hoeher, ICC 1995 | 1995 | https://ieeexplore.ieee.org/document/524253 | abstract (search) | medium |

## Reference entries (for the coordinator to merge into REFERENCES.md; not edited by me)

Existing entries to extend:
- C16 (ITU-R M.2092-2), "Used in": 2026-11-17: `testing/results/lit_vde_fec.md` - A2-1.2.4 to A2-1.2.6 turbo / CRC /
  scrambler, Table 4 re-aligned for all Link IDs with arithmetic checks, Tables 5-6, A3-8 full test vector (scrambler
  seed 100101010000000 and pi/4-QPSK map recovered from it), Table 63 re-read (Ac / Bc differ from
  lit_vdesat_fullsystem.md).
- C84 (ITU-R M.2435), "Used in": 2026-11-17: `lit_vde_fec.md` 0.4 - 4.3.1 read in the local text: 88 info bits, QPSK
  turbo 1/4, -1.5 dB at PER 1e-2, -0.3 dB at BER 1e-5 (AWGN) as the validation target.

New entries (merged into REFERENCES.md 2026-11-17, renumbered: scout's C92-C98 -> C94-C100; the G1139 entry (C95)
duplicates C16 and the AFF3CT documentation entry (C98) duplicates C91, so both were merged there and C95, C98 are
not used; citations below use the registry numbers):

### C94. ETSI EN 302 583 V1.2.1, "DVB-SH: Framing structure, channel coding and modulation for satellite services to handheld devices below 3 GHz", section 5.3 (turbo code)
- Link: https://www.etsi.org/deliver/etsi_EN/302500_302599/302583/01.02.01_60/en_302583v010201p.pdf   - Type: standard   - Read depth: section 5.3 via text reader
#### What it does
3GPP2 (cdma2000) turbo code: 8-state RSC, d = 1+D^2+D^3, n0 = 1+D+D^3, n1 = 1+D+D^2+D^3, rates 1/5-2/3 by puncturing,
6-clock tail (RSC1 then RSC2), own bit-reversal interleaver (L = 1146 / 12282).
#### What we took / could take
Confirms the VDE constituent code and termination; its interleaver is not used by VDE.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` sections 1, 3.

### C16. IALA G1139 ed. 3, "The technical specification of VDES", June 2019, Annex A A1.2.4 (turbo code)
- (Merged into C16, where G1139 is filed.) Link: https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf   - Type: guideline   - Read depth: chars 0-100k via reader
#### What it does
Same turbo law, Table 4 rows (4, 8, 20, 34) and puncturing strings (IDs 2, 6, 7, 7a, 7b, 8) as M.2092-2; its OCR
transfer-function order [1, n1/d, n0/d] is contradicted by the M.2092-2 A3-8 example.
#### What we took / could take
Second source for the puncturing positions.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` sections 1-3.

### C96. J. H. Kim, "SIMULINK Modeling and FPGA Implementation of Turbo Decoder for VDES Receiver", J. KICS 50(3), 489-, March 2025, doi:10.7840/kics.2025.50.3.489
- Link: https://d2j16w31g89z0j.cloudfront.net/journal/jkics/fullText/1387/jkics-2503-12.pdf   - Type: paper   - Read depth: text via reader (figures not readable)
#### What it does
VDES turbo decoder: log-MAP (128-entry max* LUT), sliding window 32, 6 iterations, on-the-fly interleaver, max input
6032 bits, Xilinx ZCU104 at 43.008 MHz, < 10 ms per block. PER 1 % at Es/N0 2.1 dB (Link 11, 432 bits, 1/2,
pi/4-QPSK), 1.5 dB (Link 17, 1872), 13 dB (Link 19, 5616, 3/4, 16QAM).
#### What we took / could take
Reference PER points and decoder settings for the VDE turbo baseline.
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` sections 4, 6.

### C97. MathWorks, comm.TurboEncoder / comm.TurboDecoder System objects
- Link: https://www.mathworks.com/help/comm/ref/comm.turboencoder-system-object.html   - Type: vendor documentation   - Read depth: page
#### What it does
Turbo encoder with any rate-1/N RSC trellis (e.g. `poly2trellis(4,[13 15 17],13)` = the VDE RSC), any interleaver
permutation, custom output indices, per-encoder tails at the end.
#### What we took / could take
Independent cross-check of our Python codec (not run: no MATLAB).
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` section 5.

### C91. AFF3CT documentation, turbo encoder and interleaver parameters (merged into C91)
- Link: https://aff3ct.readthedocs.io/en/latest/user/simulation/parameters/interleaver/interleaver.html   - Type: software documentation   - Read depth: pages
#### What it does
Turbo codec with LTE / CCSDS presets and a USER interleaver from a file; one-parity RSC.
#### What we took / could take
Partial cross-check only (Y0-only puncturing).
#### Used in
- 2026-11-17: `testing/results/lit_vde_fec.md` section 5.

### C99. P. Robertson, E. Villebrun, P. Hoeher, "A comparison of optimal and sub-optimal MAP decoding algorithms operating in the log domain", Proc. IEEE ICC 1995, 1009-1013
- Link: https://ieeexplore.ieee.org/document/524253   - Type: paper   - Read depth: abstract (search result)
#### What it does
Log-MAP = MAP; SOVA ~0.7 dB worse at BER 1e-4; max-log-MAP in between; complexity in the same order.
#### What we took / could take
Log-MAP vs max-log-MAP choice for the VDE baseline; op counts are my own derivation.
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
