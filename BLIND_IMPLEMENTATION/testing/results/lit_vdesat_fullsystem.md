# VDE-SAT complete system spec for a Python implementation (literature scout, 2026-11-17)

Goal: an end-to-end VDE-SAT reference (CRC, turbo FEC, puncturing, scrambler, block channel interleaver, mapping,
spreading, syncword / pilots) at VDE-SAT's **own operating points** (phase 1), then at our payloads (phase 2).
Builds on `lit_vdesat_format.md`, `lit_card_space.md` card 3 and `lit_rates.md` 4.5; what is there is not repeated
(syncword bit pattern, pilot rule, Doppler budget, deployments).

**How it was read.** ITU-R M.2092-2 (02/2026) PDF through the public text reader r.jina.ai, chars 0-295k (the whole
document): Annex 2 A2-1.2.3 - A2-1.2.9, Tables 1-11, Annex 3 A3-7 / A3-8, Annex 5 A5-2 (incl. A5-2.5, A5-2.10, A5-2.13,
Table 63). The reader's model gives **values, not verbatim text** (it refuses long quotes), and tables come out
flattened; column mapping was re-checked by arithmetic (every check is shown, tag [chk]). IALA G1139 ed. 3 (2019) read
the same way as a cross-check. Tags: [M2092 A2-x] = clause of M.2092-2; [G1139]; [derived] = my arithmetic;
[snippet] = search-engine text only; [chk] = closes arithmetically; [prev: file] = from an earlier survey here.

---

## 0. Short answer (phase 1: native low-SNR formats)

| Rank | Format (Link ID) | Why for phase 1 | Info bits k (incl. CRC) | Payload [derived] | Mod / rate | Es/N0 AWGN | Eb/N0 per payload bit, all overhead [derived] |
|---|---|---|---|---|---|---|---|
| 1 | **SAT-MCS-0.50-2 (32)**, DL, 15 slots | lowest SNR, short block (closest to our 307) | 312 | 280 (CRC-32) | BPSK / DS-CDMA SF 8, turbo 1/4 | **-4.5 dB** | -4.5 + 10log10(1641/280) = **3.18 dB** |
| 2 | **SAT-MCS-0.50-3 (33)**, DL, 15 slots | plain BPSK, no spreading, no pilots | 4280 | 4248 | BPSK, turbo 1/3 | **-3.6 dB** | -3.6 + 10log10(13143/4248) = **1.31 dB** |
| 3 | **SAT-MCS-1.50-1 (26)**, DL, 90 slots | the pilot format our C6 copies | 7 x 5456 | 7 x 5424 = 37968 (if one CRC per block) | pi/4-QPSK, turbo 1/4 | **-2.4 dB** | -2.4 + 10log10(80343/37968) = **0.86 dB** |
| 4 | **SAT-MCS-1.50-2 (34)**, DL, 15 slots | pi/4-QPSK with pilots, 15-slot burst | 2 x 4160 | 2 x 4128 = 8256 | pi/4-QPSK, turbo 1/3, no tail | **-0.6 dB** | -0.6 + 10log10(13122/8256) = **1.41 dB** |
| (5) | SAT-MCS-0.50-1 (25), DL bulletin board | | 4776 | 4744 | BPSK / DS-CDMA SF 8, turbo 1/2 | -2.0 dB | -2.0 + 10log10(10042/4744) = 1.26 dB |
| (6) | SAT-MCS-1.50-2 (20), **uplink** RA (NorSat-2 trial) | very short | 96 | 80 (CRC-16) | QPSK, CPM-like spreading SF 16, turbo 1/4 | -0.9 dB | -0.9 + 10log10(261/80) = 4.24 dB |

- **k includes the CRC** [chk]: the A3-8 worked example is 256 payload + 32 CRC = 288 = Table 4 k of Link 5. So
  Link 32 carries 280 payload bits, near our 307-bit (R = 0.15) payload.
- **Es/N0 is per (despread) data-modulation symbol** [chk]: Link 32: C/(N0+I0) 31.6 dB-Hz - 10log10(4200) = -4.63 dB;
  Link 26: 42.9 - 45.26 = -2.36 dB; Link 25: 34.2 - 36.23 = -2.03 dB.
- **The PER behind these thresholds is not stated** in M.2092-2. M.2435 4.3.1 (now read locally, lines 1134-1188 of
  `standards/ITU-R_M.2435_2018.txt`; figures read from PDF pp. 25-26, 2026-11-17): AWGN, a packet of **88 information
  bits**, QPSK, turbo rate 1/4 "according to ETSI EN 302 583 (V1.2.1)" (the DVB-SH FEC), **Es/N0 after
  de-spreading** -1.5 dB at PER 1e-2 (Fig. 11) and -0.3 dB at BER 1e-5 (Fig. 12), called "a conservative design
  point". The interleaver, decoder algorithm and number of iterations are **not stated**. Fig. 11 read by eye: PER
  0.5 at -3.29 dB, 0.11 at -2.29, 1.2e-2 at -1.54, 1.05e-3 at -0.79, 1.8e-4 at -0.29 (about 0.75 dB per decade).
  Validation rule in `fullsys/vde.py` REF: log-MAP within -1.5 +- 0.3 dB at PER 1e-2, slope about one decade per
  0.9 dB.
- Consistency check [derived]: coded Eb/N0 (no overhead) is 1.17 dB for Link 33 (k 4280, BPSK 1/3) and 1.16 dB for
  Link 34 (k 4160, pi/4-QPSK 1/3). These are the same, so the thresholds look like one PER target plus one margin.
  They sit about 0.5 dB above what a 4k-bit rate-1/3 turbo code typically needs at PER 1e-3 (my estimate, not
  sourced). **Do not treat these thresholds as ideal-sync curves to match within 0.1 dB.**

---

## 1. FEC chain (Annex 2 A2-1.2.3 - A2-1.2.6; Annex 5 A5-2.11 says "see Annex 2")

### 1.1 Order of operations
Downlink [M2092 A2-1.2.3.5 Fig. 6; A5-2.13; A5-2.5.2]: payload (zero-padded) -> **CRC** appended MSB first -> **turbo
encode** (the "interleaving" step listed before encoding in Fig. 6 is the turbo-internal interleaver) -> **puncture**
(Tables 5 / 6) -> **bit scrambler** -> **block channel interleaver** (A5-2.13, downlink only) -> burst stuffing bits ->
bit-to-symbol mapping -> **DS spreading** (Links 25, 32: Gold, 8 chips; 28, 29: "0010", 2 chips) -> insert syncwords
and pilots (A5-2.10) -> ramps / guard -> RRC 0.25. The reader flagged the ordering of Fig. 6 as "check the figure".

### 1.2 CRC [M2092 A2-1.2.5]
| | CRC-32 (all formats except Link 20) | CRC-16 (Link 20 only) |
|---|---|---|
| Generator | x^32+x^26+x^23+x^22+x^16+x^12+x^11+x^10+x^8+x^7+x^5+x^4+x^2+x+1 (0x04C11DB7) | x^16+x^15+x^2+1 (0x8005) |
| Initial register | 0xFFFFFFFF | 0x0000 |
| Coverage / order | all payload bits incl. zero padding; MSB of each byte first; CRC appended MSB first | same |
| Final XOR | **not stated** (the text describes a plain remainder: register over data + CRC = 0) | not stated |

### 1.3 Turbo code [M2092 A2-1.2.4; G1139 A1.2.4; "follows ETSI EN 302 583" (DVB-SH, = 3GPP2 family)]
- Two identical RSC encoders, parallel. G(D) = [1, n0(D)/d(D), n1(D)/d(D)], **n0 = 1+D+D^3, n1 = 1+D+D^2+D^3,
  d = 1+D^2+D^3** (8 states; octal feedforward 15 / 17 with feedback 13). Outputs per clock X, Y0, Y1 (RSC1), X',
  Y0', Y1' (RSC2 on the interleaved input).
- **Termination:** 6 extra clocks with the switch in position (b) (feedback bit fed in, so the register goes to 0):
  clocks 1-3 output RSC1 only (X, Y0, Y1), clocks 4-6 output RSC2 only (X', Y0', Y1'). The tail is then punctured /
  repeated with Table 6. The switch wiring is in Fig. 8 (not extractable). Use the standard 3GPP2 / DVB-SH rule:
  the tail input = the feedback value.
- **Interleaver** (CCSDS 131.0-B-2 law, own k1, k2, primes per Link ID): for s = 1..k, k = k1 k2:
  m = (s-1) mod 2; i = floor((s-1)/(2 k2)); j = floor((s-1)/2) - i k2; t = (19 i + 1) mod (k1/2); q = t mod 8 + 1;
  c = (p_q j + 21 m) mod k2; **pi(s) = 2 (t + c k1/2 + 1) - m**; output bit s = input bit pi(s).
- **Table 4 (low-SNR satellite rows)** [M2092 Table 4; puncturing / tail ID pairs split by me, e.g. "22e" = 2 / 2e,
  each confirmed by the tail length in Tables 9-11]:

| Link | Rate | k | k1 | k2 | p1..p8 | Punct / tail | Tail bits [chk] |
|---|---|---|---|---|---|---|---|
| 20 (UL) | 1/4 | 96 | 2 | 48 | 37, 83, 211, 61, 107, 101, 149, 167 | 2 / 2a | 18: 96 x 4 + 18 = 402 = 201 QPSK |
| 25 | 1/2 | 4776 | 12 | 398 | default 31, 37, 43, 47, 53, 59, 61, 67 | 6 / 6a | 10: 9552 + 10 = 9562 |
| 26 | 1/4 | 5456 (x7) | 16 | 341 | 37, 41, 43, 47, 53, 59, 61, 67 | 2 / 2a | 18 (+3 pad) per block: 7 x 21845 = 152915 |
| 27 | 1/2 | 6032 (x19) | 16 | 377 | default | 6 / 6b | 8 |
| 28 | 1/4 | 5280 (x4) | 16 | 330 | default | 2 / 2b | 16 |
| 29 | 1/4 | 5552 (x6) | 16 | 347 | default | 2 / 2c | 12 |
| 32 | 1/4 | 312 | 2 | 156 | 37, 79, 29, 139, 151, 97, 181, 157 | 2 / 2e | 21: 1248 + 21 = 1269 |
| 33 | 1/3 | 4280 | 8 | 535 | 59, 37, 157, 167, 239, 83, 163, 29 | 4 / 4a | 15: 12840 + 15 = 12855 |
| 34 | 1/3 | 4160 (x2) | 16 | 260 | 163, 157, 149, 137, 197, 47, 241, 251 | 4 / none ("no tail bits") | 0: 2 x 12480 = 24960 |

  Other rows (ASM / TER, rates 1/2 and 3/4, k 192-5616) are in Table 4 as well. Examples: Link 5 3/4 k 288, Link 7
  3/4 k 1056, Link 9 1/2 k 448, Link 10 1/2 k 704, Link 11 1/2 k 432, Link 14 1/2 k 896, Link 17 1/2 k 1872. These
  are the 1/2 and 3/4 rates the task asked about, but **none is a satellite format**.
- **Table 5, data puncturing** (one 6-digit column per period, order X Y0 Y1 X' Y0' Y1'; 1 = send, 0 = delete;
  read period by period). Each pattern was checked: number of ones = Lp / r [chk]. Patterns 0, 2, 4, 6 equal the
  cdma2000 / DVB-SH patterns.

| ID | Rate | Lp | Periods |
|---|---|---|---|
| 0 | 1/5 | 1 | 111011 |
| 2 | 1/4 | 2 | 111001, 110011 |
| 4 | 1/3 | 1 | 110010 |
| 5 | 2/5 | 12 | 100000, 101001, 001001, 101001, 101001, 001001, 101001, 101001, 001001, 101001, 101001, 001001 |
| 6 | 1/2 | 2 | 110000, 100010 |
| 7 / 7a / 7b | 2/3 | 4 | 100000,100000,100000,101001 / 100000,100000,100000,110010 / 100000,110000,100000,100010 |
| 8 | 3/4 | 6 | 101000, 100000, 100000, 100000, 100000, 100001 |
| 9 | 5/6 | 10 | 100000, 110000, 100010, then 7 x 100000 |
| 1, 3 | 2/9, 2/7 | 4 | 101011,111011,111001,111011 / 101001,101011,101001,111001 |

  Caveat: the pattern-5 string starts with "100000", which gives 30 ones in 12 periods = 2/5 [chk], but it is
  unusual. Re-check it in the PDF if rate 2/5 is ever used.
- **Table 6, tail patterns** (one 6-digit group per tail clock 1..6, digits = copies of X Y0 Y1 X' Y0' Y1';
  0 = delete, 1 = send, 2 / 3 = repeat). Rows needed here:
  2a = 111000 x3, 000111 x3 (18 bits); 2e = 211000, 211000, 210000, 000211, 000211, 000200 (21); 4a = 210000, 210000,
  200000, 000210, 000210, 000010 (15); 6a = 110000, 110000, 100000, 000110, 000110, 000100 (10); 8b = 101000, 101000,
  100000, 000101, 000101, 000100 (10, Link 5). All 22 rows are in the reader output; in the 3GPP2 base rows (0, 2, 4,
  6, 8, 9) each tail clock produces 1/r bits.
- **Output length:** N = floor(K/Lp) Lp/r + (ones of the first K mod Lp periods) + tail [M2092 A2-1.2.4].
- **Decoder:** **not specified** by M.2092-2 / G1139 (no algorithm, no iteration count). Implementation choice:
  log-MAP or max-log-MAP BCJR, about 8 iterations (common turbo practice, not sourced here), early stop on CRC.

### 1.4 Bit scrambler [M2092 A2-1.2.6, Fig. 9]
F(x) = 1 + x^-14 + x^-15 (15 stages), re-initialised every packet, MSB = first output bit, applied to the coded bits.
**The seed is in Fig. 9 and could not be read.** It can be recovered from the A3-8 worked example, which lists the
394 bits before and after scrambling (bit strings exist in the PDF; the reader would not copy them). For AWGN BLER
the scrambler has no effect.

### 1.5 Downlink block channel interleaver [M2092 A5-2.13, Table 63]
The scrambled bits of length L are written by rows into an M x N matrix. A row permutation, then a column permutation
is applied, and the matrix is read out by columns.
pr(m) = 1 + ((Ar m + Cr(n)) mod M), Cr(n) = (Br n - 1) mod M; pc(n) = 1 + ((Ac n + Cc(m)) mod N),
Cc(m) = (Bc m - 1) mod N; "the bit in row pr(m) moves to row m, the bit in column pc(n) moves to column n". IB
interleaver blocks per burst (L x IB = channel bits).

| LCID | 25 | 26 | 27 | 28 | 29 | 32 | 33 | 34 |
|---|---|---|---|---|---|---|---|---|
| M x N | 14 x 683 | 257 x 119 | 503 x 114 | 16 x 1321 | 132 x 202 | 27 x 47 | 857 x 15 | 128 x 195 |
| L [chk M N] | 9562 | 30583 | 57342 | 21136 | 26664 | 1269 | 12855 | 24960 |
| IB [chk L IB = channel bits] | 1 | 5 | 4 | 4 | 5 | 1 | 1 | 1 |
| Ar (my split of "5127 251 761 13 421 51") | 5 | 127 | 251 | 7 | 61 | 13 | 421 | 51 |
| Br | 3 | 107 | 223 | 13 | 31 | 17 | 367 | 89 |
| Ac | 3 | 37 | 59 | 53 | 659 | 97 | 23 | 797 |
| Bc | 7 | 1 | 41 | 11 | 59 | 59 | 13 | 319 |

The Ar / Br / Ac / Bc token strings were run together in the extraction. My split gives 8 values per row, and every
Ar is coprime to its M. Still, it is **medium confidence**: confirm it in the PDF. G1139 ed. 3 (D 2.14) describes
an older version: bit-reversal column permutation, number of columns a power of 2. Use M.2092-2. In AWGN the
interleaver does not change BLER, so it is needed only for bit-exact fidelity.

### 1.6 Mapping and spreading [M2092 A2-1.2.3.3, A2-1.2.9, A5-2.4, A5-2.5]
- **QPSK (Gray):** quadrant index q for bits 11 -> 0, 01 -> 1, 00 -> 2, 10 -> 3 (A5-2.4), i.e. symbol
  e^{j(pi/4 + q pi/2)}: bit 1 -> +, first bit -> I, second -> Q [my reading]. **pi/4-QPSK:** the same map, with odd
  symbols rotated by 45 deg (A5-2.4); the constellations alternate {(+-1 +- j)/sqrt2} and {1, j, -1, -j}. The
  training / syncword maps bit 1 -> dibit 11, bit 0 -> 00. It is **not differential** (no pi/4-DQPSK wording found).
  Figs 10-13 (the BPSK, pi/4-QPSK, 8PSK and 16QAM maps) could not be read, so the BPSK sign convention and the 8PSK
  Gray table are open.
- **Bit packing:** the first scrambler output bit goes to the MSB of the first symbol.
- **DS spreading (downlink):** Links 25 and 32: each bit is XORed with 8 chips of the Gold sequence SS0 / SS1 (length
  2047, about 256 bytes listed; SS0 starts 0x04 = 00000100, which spreads the first syncword bit), then BPSK; the
  syncword and pilots are spread too (pilot bit "1" before spreading). Links 28, 29: "0010" (2 chips per bit). The
  Gold byte tables were not copied. **In AWGN with one user, a known +-1 spreading sequence is transparent**: despread,
  and Es/N0 per symbol = SF x Ec/N0. It matters only for the CFO definition: +-0.03 cycles per chip is +-0.24 cycles
  per symbol at SF 8 [derived].
- **Uplink Link 20:** constant-envelope CPM-like spreading, SF 16, NS 16, BL 261 symbols, 66 816 samples per burst,
  defined by two phase tables (`cpa_/cpe_SF16_NS16_BL261_r1.txt`) that are not in the text. Correlation loss
  < 0.25 dB [M2092 A5-2.5.1]. **Not implementable bit-exact** without those tables.
- **Link ID field:** (32,6) first-order Reed-Muller, XOR 11000010111000101000111001001111, pi/4-QPSK, 16 symbols. **Not
  used on the satellite downlink** (size 0 in Tables 10 / 11).

---

## 2. Formats (phase-1 candidates, full parameter sets) [M2092 Tables 9-11, A5-2.10]

| | Link 32 SAT-MCS-0.50-2 | Link 33 SAT-MCS-0.50-3 | Link 26 SAT-MCS-1.50-1 | Link 34 SAT-MCS-1.50-2 (DL) | Link 20 SAT-MCS-1.50-2 (UL) |
|---|---|---|---|---|---|
| Burst | 15 slots, 392 ms, guard 8.238 ms | 15 slots, guard 8 ms | 90 slots, 2392 ms, guard 8 ms | 15 slots, guard 8.625 ms | 5 slots, 125.3 ms |
| Symbol / chip rate | 4.2 ksym/s / 33.6 kchip/s | 33.6 ksym/s | 33.6 ksym/s | 33.6 ksym/s | 2.1 ksym/s, SF 16 |
| Symbols per burst (excl. ramps) | 1641 = 192 + 180 + 1269 [chk] | 13143 = 288 + 12855 [chk] | 80343 = 945 + 2940 + 76458 [chk] | 13122 = 162 + 480 + 12480 [chk] | 261 = 48 + 12 + 201 [chk] |
| Ramps | 14 / 14 chips | 14 / 14 | 14 / 14 | 14 / 14 | 14 / 14 chips |
| Syncword | 48 (Table 1 48-bit sequence) x 4, d_s 531, BPSK/CDMA | 48 x 6, d_s 2619, BPSK | 27 x 35, d_s 2268, pi/4-QPSK 00/11 | 27 x 6, d_s 2619, pi/4-QPSK 00/11 | 48, QPSK/CDMA 00/11 |
| Pilots | single, every 8 (180) | none | single, every 27 (2940) | single, every 27 (480) | single, every 17 (12) |
| First pilot after syncword end | floor((1+8)/2) = 4 [derived from rule] | - | 14 | 14 | 9 [derived] |
| Data modulation | BPSK | BPSK | pi/4-QPSK | pi/4-QPSK | QPSK |
| Coded bits (incl. tail) | 1269 | 12855 | 152915 + 1 stuffing | 24960 | 402 |
| FEC blocks x k | 1 x 312 | 1 x 4280 | 7 x 5456 | 2 x 4160 | 1 x 96 |
| CRC | 32 | 32 | 32 | 32 | 16 |
| Es/N0 / C/(N0+I0) | -4.5 dB / 31.6 dB-Hz | -3.6 / 41.7 | -2.4 / 42.9 | -0.6 / 44.7 | -0.9 / 32.3 |

48-bit syncword (Table 1): `000100011110011011000001010111011010110111101000`; 27-bit: see lit_vdesat_format.md.
Pilot value (1+j)/sqrt2 (pi/4 rotated at odd positions). With DSSS, the pilot is bit "1" spread.

**Phase-2 mapping to our payloads (secondary):** 205 / 307 bits -> Link 32 structure (k 312, rate 1/4, BPSK, pilots
every 8) is the only native low-SNR short block; 819 / 1024 bits -> no native satellite format. The closest is the
turbo law itself with an own k (k must factor as k1 k2 with k1 even; e.g. 1024 + 32 = 1056 = Link 7 k, 4 x 264;
819 + 32 = 851 is odd, so pad to 852 = 4 x 213 [derived]) at rate 1/2 or 1/4 and the Link 26 / 34 pilot comb.

---

## 3. Receiver (what is published)
- **Standard:** no receiver algorithm, no decoder, no PER target. Only "uniformly repeated syncwords are utilised
  for synchronisation" and pilots for tracking [M2092 A5-2.10]. G1139: the VDE-SAT syncword "needs to work at Es/N0
  of -2 dB" [G1139 Table 2].
- **Sync:** correlation bank of Doppler-shifted syncword copies + autocorrelation fine stage, +-4 kHz (Ma et al.
  2018, abstract only) [prev: lit_card_space.md]; DA "Rife-Boorstyn" on preamble / pilots + pilot phase (Andreotti
  et al., Link 20, snippet) [prev].
- **Burst declared correct:** CRC check (zero remainder), per FEC block [M2092 A2-1.2.5]; in the E-SSA uplink
  receiver, CRC-validated packets are cancelled (SIC) [CEAS Space J. VDES article, doi:10.1007/s12567-018-0214-8]. No
  extra undetected-error control was found: CRC-32 alone, so the UER is about 2^-32 per block, far below our CRC-16 +
  rho.

## 4. Reference performance curves
**No public AWGN PER / FER curve for any VDE-SAT format was found.** Tried: M.2092-2 (thresholds only, no PER);
G1139 ed. 3 Table 65 (PER vs C/(N0+I0), 50 % at 44 dB-Hz ... 0.01 % at 28 dB-Hz). Table 65 is **measured NorSat-2
pass statistics** (fading, format not stated), not an AWGN curve. ITU-R Report M.2435-0 (2018) holds the VDE-SAT
simulations (snippet: QPSK turbo 1/4, Es/N0 -1.5 dB at PER 1e-2, "conservative", plus about -0.3 dB at BER 1e-5),
but its 10.9 MB PDF and DOCX exceeded the fetch limit and the text reader returned nothing. Andreotti 2021/23 and
Nanna 2023: paywalled (403). **Validation plan instead:** (a) bit-exact check against the A3-8 example (Link 5: 288
-> 394 coded -> scrambled -> 197 QPSK symbols; needs the bit strings from the PDF); (b) the AWGN PER of our turbo
implementation at k = 312 / 4280 rate 1/4, 1/3 should reach PER about 1e-2 ... 1e-3 at or a little below the Table 11
Es/N0 (-4.5 / -3.6 dB). Since the PER target is unknown, this check is only accurate to about 0.5 dB, not 0.1 dB.
(c) Cross-check the generic codec against published 3GPP2 / DVB-SH turbo curves (same constituent code), which were
not collected here.

## 5. Complexity
None published for VDE-SAT. [derived, standard BCJR count, illustrative] Max-log-MAP 8-state, 2 SISO per iteration:
about 3 recursions x 8 states x 2 branches = about 50 add-compare per info bit per SISO, so about 100 per bit per
iteration and 800 per bit for 8 iterations. For k = 312: about 2.5e5 operations per block (not MACs in our model,
not sourced).

## 6. Could not be obtained (and what was tried)
| Item | Tried | Status |
|---|---|---|
| Scrambler seed (Fig. 9) | M.2092-2 reader, G1139 ed. 3 | not in text; recover from A3-8 bit strings |
| BPSK / pi/4-QPSK / 8PSK / 16QAM maps (Figs 10-13) | same | only the QPSK quadrant rule (A5-2.4) |
| Turbo switch wiring (Fig. 8) | same | assume the 3GPP2 / DVB-SH rule |
| Table 63 Ar row | reader (garbled "5127 251 761 13 421 51") | split inferred, medium confidence |
| Gold SS0 / SS1 byte tables, Link 20 CPM tables | reader would not copy; CPM tables are external .txt files | not obtained |
| PER target of the thresholds; AWGN PER curves | M.2092-2, G1139, M.2435 (too large: PDF and DOCX > 10 MB; reader empty), Wiley / IET (403), searches | not found |
| Decoder algorithm / iterations; complexity | all of the above | not specified anywhere read |
| CRC final XOR | M.2092-2 | not stated (assume none) |
| Link 26: one CRC per FEC block or per burst | Tables 9-11 | unclear; "FEC output bits" = k per block suggests per block |
| A3-8 test-vector bit strings | reader | present in the PDF, not copied (open the PDF in a viewer) |

## 7. Per-source table
| Source | Year | Link | Read | Relevance | What it gave |
|---|---|---|---|---|---|
| ITU-R M.2092-2 | 2026 | [PDF](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf) | whole text via reader, values not verbatim | high | sections 1-2 above |
| IALA G1139 ed. 3 | 2019 | [PDF](https://www.e-navigation.nl/sites/default/files/1139-ed.3-the-technical-specification-of-vdes_june-2019.pdf) | chars 0-100k, 150-290k via reader | medium | turbo / tail cross-check; syncword -2 dB requirement; Table 65 (measured); older interleaver |
| ITU-R Report M.2435-0 | 2018 | [ITU page](https://www.itu.int/pub/R-REP-M.2435-2018), [PDF](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-M.2435-2018-PDF-E.pdf) | local text 4.3.1 (lines 1134-1188) + Figs 11-12 (PDF pp. 25-26), 2026-11-17 | high | 88 info bits, QPSK, DVB-SH turbo 1/4, AWGN, Es/N0 after de-spreading: -1.5 dB at PER 1e-2 ("conservative design point"), -0.3 dB at BER 1e-5; interleaver / decoder / iterations not stated |
| "VHF Data Exchange System (VDES): an enabling technology for maritime communications", CEAS Space J., doi:10.1007/s12567-018-0214-8 (authors not shown on the page read) | ~2019 | [Springer](https://link.springer.com/article/10.1007/s12567-018-0214-8) | full page via reader | low-medium | E-SSA receiver with CRC + SIC; no numbers |
| Ma, Shi, Meng, Li, IEEE ICCC 2018 | 2018 | [IEEE](https://ieeexplore.ieee.org/document/8780774/) | [prev] abstract | medium | sync (see lit_card_space.md) |
| Andreotti et al., IJSCN 41(2) | 2023 | [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/sat.1437) | [prev] snippets | medium | Link 20 trial; no curves readable |
| SciTePress 2018 VDES evaluation | 2018 | [PDF](https://www.scitepress.org/papers/2018/68502/68502.pdf) | [prev] | low | generic MCS labels |
