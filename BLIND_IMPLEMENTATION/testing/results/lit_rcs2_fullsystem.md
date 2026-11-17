# DVB-RCS2 TC-LM return-link burst system: an end-to-end spec you can implement (encoder, burst, receiver, decoder, CRC)

Literature scout report, 2026-11-17. No simulations were run and no code was executed. Builds on `lit_dvbrcs2.md`,
`lit_ars2021.md`, `lit_card_sat.md` and `lit_rates.md`; it does not repeat them, it fills in what they lacked.

Tags: **[EN]** = ETSI EN 301 545-2 V1.3.1 (2020-07), with the clause / table; **[TR]** = ETSI TR 101 545-4 V1.1.1
(2014), with the clause / table (cross-checked with V1.2.1 (2026) where stated); **[AFF3CT]** = the open-source AFF3CT
library (MIT), which implements the RCS2 code from EN 301 545-2 V1.3.1; **[MW]** = MathWorks Satellite Communications
Toolbox pages; **[Gr]** = Griebel et al. 2021; **[derived]** = my own arithmetic or consistency check.
How the sources were read: the ETSI PDFs through a public PDF-to-text reader (r.jina.ai, given only the public ETSI URL).
Tables come out flattened, so every row used here was **checked arithmetically** (burst = payload + pre + post + pilots;
N couples = 4 x payload bytes; payload symbols = 2N / (m R); UW hex length = (pre + 1 + post) m / 4 rounded up).
Figures (constellation drawings) are not in the extracted text.

---

## 0. Phase-1 priority: the native low-SNR waveforms to implement first

(After the user's update: phase 1 runs at RCS2's own operating points.) These are the waveforms I recommend. All are
from Annex A Table A-1 [EN], ideal-sync PER from TR cl. 10.2.1 [TR].

| Pick | ID | Map, rate | Payload (bytes / bits incl. CRC) | N couples | P, Q0, Q1, Q2, Q3 | Y punct. (period / pattern) | W punct. | Burst (sym) | Pre / post | Pilot period / sum | Es/N0 @ PER 1e-3 / 1e-5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1 (main)** | **13** | QPSK 1/3 | 123 / 984 | 492 | 31, 0, 3, 1, 0 | 1 / 1 | 1 / 1 | 1616 | 32 / 31 | 20 / 77 | **-0.80 / -0.51 dB** (T10.6) |
| **2** | **14** | QPSK 1/2 | 188 / 1504 | 752 | 37, 1, 3, 4, 2 | 1 / 1 | 1 / 0 | 1616 | 25 / 25 | 25 / 62 | **1.49 / 1.71 dB** (T10.6) |
| **3 (lowest SNR)** | **42** | pi/2-BPSK 1/3 | 123 / 984 | 492 | 31, 0, 3, 1, 0 | 1 / 1 | 1 / 1 | 3236 | 65 / 64 | 20 / 155 | **-3.81 / -3.52 dB** (T10.8) |
| **4 (short)** | **3** | QPSK 1/3 | 38 / 304 | 152 | 17, 9, 5, 14, 1 | 1 / 1 | 1 / 1 | 536 | 27 / 27 | 18 / 26 | **-0.27 / 0.22 dB** (T10.5) |
| optional | 4 | QPSK 1/2 | 59 / 472 | 236 | 23, 10, 2, 11, 1 | 1 / 1 | 1 / 0 | 536 | 22 / 22 | 24 / 20 | 1.92 / 2.34 dB (T10.5) |
| optional | 43 | pi/2-BPSK 1/2 | 188 / 1504 | 752 | 37, 1, 3, 4, 2 | 1 / 1 | 1 / 0 | 3236 | 52 / 51 | 25 / 125 | -1.53 / -1.30 dB (T10.8) |
| optional (control) | 41 | pi/2-BPSK 1/3 | 59 / 472 | 236 | 23, 10, 2, 11, 1 | 1 / 1 | 1 / 1 | 1612 | 57 / 56 | 18 / 83 | -3.38 dB @1e-3 (full row in 4.1) (T10.4, see caveat) |
| optional (control) | 2 | QPSK 1/3 | 14 / 112 | 56 | 9, 2, 2, 8, 0 | 1 / 1 | 1 / 1 | 262 | 41 / 41 | 15 / 12 | 0.50 dB @1e-3 (full row in 4.1) (T10.4) |

- Row sources: Table A-1 raw rows (P, Q, puncture columns read from the row text, e.g. ID 13 "... 31 0 3 1 0 1 1 1 1
  3F00C3...") [EN]. The P / Q values agree **exactly** with AFF3CT's `Interleaver_core_ARP_DVB_RCS2.cpp` for every row
  (152, 56, 236, 492, 752) [AFF3CT]. Pilot sums of IDs 42 / 43 (155 / 125) are now read from the row text, which settles
  the "[derived]" values in `lit_dvbrcs2.md`.
- **Why these four:** ID 13 is the nearest native QPSK burst to our N = 2048 (984 coded-input bits, 1476 data
  symbols) and the lowest-SNR QPSK long burst; ID 14 is its rate-1/2 twin (same burst length); ID 42 is the lowest-SNR
  native waveform in the whole TC-LM table (Es/N0 -3.81 dB, within our -5 ... +3 dB range) and uses **the same turbo
  code as ID 13** on BPSK; ID 3 is the short-burst 1/3 point (304 bits, close to our 307-bit payload).
- **Consistency check [derived]:** ID 42 = ID 13's code on BPSK, so it should need 10 log10(2) = 3.01 dB less Es/N0:
  -0.80 - 3.01 = -3.81 (table: -3.81). ID 43 vs ID 14: 1.49 - 3.01 = -1.52 (table -1.53). So Es/N0 in the TR tables
  is **per transmitted symbol**, and the tables are self-consistent to 0.01 dB.
- **Equivalent Eb/N0 per information bit, all overhead charged [derived]:** Eb/N0 = Es/N0 + 10 log10(L_burst / k),
  k = payload bits minus the CRC (CRC32 for traffic, CRC16 for control, see 1.4), all burst symbols (pre, pilots,
  post) charged, guard time not charged.

| ID | L_burst | k (traffic, CRC32) | 10 log10(L/k) | Eb/N0 @ 1e-3 | Eb/N0 @ 1e-5 | k if control (CRC16) | Eb/N0 @ 1e-3 (control) |
|---|---|---|---|---|---|---|---|
| 13 | 1616 | 952 | 2.30 dB | **1.50 dB** | 1.79 dB | 968 | 1.43 dB |
| 14 | 1616 | 1472 | 0.41 dB | **1.90 dB** | 2.12 dB | 1488 | 1.86 dB |
| 42 | 3236 | 952 | 5.31 dB | **1.50 dB** | 1.79 dB | 968 | 1.43 dB |
| 3 | 536 | 272 | 2.95 dB | **2.68 dB** | 3.17 dB | 288 | 2.43 dB |
| 4 | 536 | 440 | 0.86 dB | 2.78 dB | 3.20 dB | 456 | 2.71 dB |
| 43 | 3236 | 1472 | 3.42 dB | 1.89 dB | 2.12 dB | 1488 | 1.85 dB |
| 41 (control) | 1612 | - | - | - | - | 456 | 2.10 dB (5.48 dB term) |
| 2 (control) | 262 | - | - | - | - | 96 | 4.86 dB (4.36 dB term) |

- Blind configured "to the same payload and rate" means a polar code with K = k + 16 (CRC-16) [derived]: e.g. ID 13
  traffic: 952 information bits; ID 14: 1472 bits; ID 3: 272 bits. Note the RCS2 code length differs from our N = 2048
  (ID 13 is a (2952, 984) turbo code); the comparison on the Eb/N0-per-information-bit axis absorbs this.

---

## 1. The transmitter, step by step (TC-LM, non-spread)

Order of operations (cl. 7.3.2) [EN]: (1) energy dispersal of the Frame PDU, (2) CRC addition, (3) turbo coding,
(4) insertion of the unique word (preamble / pilots / postamble), (5) linear modulation (RRC).

### 1.1 Payload and Frame PDU
- Table A-1 "payload length" (bytes) = **Frame PDU + CRC**, i.e. the turbo-encoder input K = 8 x payload bytes.
  Evidence: N couples = 4 x payload bytes for every row (ID 13: 123 B -> 492) [EN Table A-1 + AFF3CT]; cl. 7.2.6.3.4
  says the resources are "occupied by Frame PDU and frame CRC" [EN]; MathWorks: "FramePDULength = payload length in
  bits minus the CRC length", 10-byte traffic payload -> 48 PDU bits (CRC32), 10-byte control payload -> 64 (CRC16) [MW
  generator page].
- Higher-layer headers (RLE / frame PDU headers) inside the Frame PDU are not modelled here (they are user data to the
  physical layer). This is a simplification: real traffic bursts carry a few header bytes, which this spec counts as
  payload.

### 1.2 Energy dispersal (cl. 7.3.3) [EN]
- PRBS 1 + x^14 + x^15 (Eq. 7-1), 15-cell LFSR, initial state SR1 ... SR15 = **100101010000000** (Table 7-11).
- XOR applied to **every Frame PDU bit**; the first PRBS bit goes on the first payload bit (the first bit after the
  preamble); reset to the initial state for every burst.
- Not scrambled: the CRC (it is computed after scrambling, over the scrambled bits) and the UW.
- Bit order: fields MSB first (cl. 7.3.3 field-ordering rules).
- [derived] This is the DVB-S randomiser polynomial and init (output = SR14 XOR SR15, fed back to SR1). For an AWGN
  link test it changes nothing in BLER; implement it for fidelity only (or skip with a note).

### 1.3 CRC (cl. 7.3.4, Table 7-12) [EN]

| Content type | CRC | Polynomial | Init | Bit order / output |
|---|---|---|---|---|
| Logon, control | CRC16 | x^16 + x^15 + x^2 + 1 | all 0 | PDU fed MSB first; register sent "from the bit at the end of the register"; no final XOR stated |
| Traffic (and traffic/control) | CRC32 | x^32 + x^26 + x^23 + x^22 + x^16 + x^12 + x^11 + x^10 + x^8 + x^7 + x^5 + x^4 + x^2 + x + 1 (ISO/IEC 13818-1 Annex B) | 0xFFFFFFFF | per ISO 13818-1 Annex B |

- Table 7-12 has one row, "transparent star, any access method": CRC16 / CRC16 / CRC32 [EN]. **No CRC-less option** in
  the text read.
- [derived] Catalogue names: CRC16 = poly 0x8005, init 0, no reflection, no XOR-out (= "CRC-16/UMTS" / BUYPASS);
  CRC32 = 0x04C11DB7, init 0xFFFFFFFF, no reflection, no XOR-out (= "CRC-32/MPEG-2"). Verify with the standard test
  vector "123456789": CRC-16/UMTS = 0xFEE8, CRC-32/MPEG-2 = 0x0376E6E7 (catalogue values, from memory: check them
  against a CRC catalogue before relying on them).
- **Undetected-error rate [derived]:** CRC32 ~2^-32 = 2.3e-10 per wrong decode; CRC16 ~1.5e-5. RCS2 has no extra
  re-encoding check.

### 1.4 Turbo encoder: 16-state duo-binary CRSC, "Turbo-Phi" (cl. 7.3.5.1) [EN], [TR 6.3.1]
- **Input:** K = 2N bits as N couples (A_j, B_j), j = 0 ... N-1; the MSB of the first byte is A_0, the next bit B_0,
  and so on (cl. 7.3.5.1.0). Constraints: **N multiple of 4** and **N not a multiple of 15** (the LFSR period) [TR 6.3.1].
  With N = 4 x bytes, the second rule means **payload bytes must not be a multiple of 15** [derived].
- **Constituent encoder** (cl. 7.3.5.1.0) [EN], polynomial vectors [AFF3CT `Encoder_RSC_DB.cpp`]:
  - state S = 8 S1 + 4 S2 + 2 S3 + S4 (S1 = MSB), 16 states;
  - feedback 1 + x^3 + x^4; parity Y: 1 + x + x^2 + x^4; parity W: 1 + x^2 + x^3 + x^4;
  - A enters at tap 1 only; B enters at tap 1, after S1 and after S3.
  - One step (state S1..S4, input A, B) -> new state S1'..S4' and outputs [derived, written out from the AFF3CT vectors
    A = 1000, B = 1101, Y = 11101, W = 10111, feedback = 0011]:
    ```
    f   = S3 ^ S4 ^ A ^ B          # new S1 (feedback + inputs)
    S1' = f
    S2' = S1 ^ B
    S3' = S2
    S4' = S3 ^ B
    Y   = f ^ S1 ^ S2 ^ S4         # 1 + x + x^2 + x^4
    W   = f ^ S2 ^ S3 ^ S4         # 1 + x^2 + x^3 + x^4
    ```
  - **Check against the circulation table [derived, by hand]:** with zero input the state map G gives G(14) = 15,
    G(3) = 1, G^3(8) = 9, and the table entries below satisfy Sc XOR G^n(Sc) = S_N^0 for n = N mod 15 = 1 (14 -> 1,
    3 -> 2) and n = 3 (8 -> 1). So the update rule above and the table below match.
- **Circular (tail-biting) state** (cl. 7.3.5.1.2) [EN]: (1) start at S = 0, encode the N couples in natural order,
  final state S_N^0; (2) C1 = Table 7-13[N mod 15][S_N^0]; (3) same in interleaved order for C2; (4) encode again from
  C1 (natural) and C2 (interleaved): the encoder ends in the state it started in. The table in the EN text is garbled;
  the values below are AFF3CT's `circ_states` (row = (N mod 15) - 1, column = S_N^0), checked as above:

| N mod 15 | Sc for S_N^0 = 0 ... 15 |
|---|---|
| 1 | 0 14 3 13 7 9 4 10 15 1 12 2 8 6 11 5 |
| 2 | 0 11 13 6 10 1 7 12 5 14 8 3 15 4 2 9 |
| 3 | 0 8 9 1 2 10 11 3 4 12 13 5 6 14 15 7 |
| 4 | 0 3 4 7 8 11 12 15 1 2 5 6 9 10 13 14 |
| 5 | 0 12 5 9 11 7 14 2 6 10 3 15 13 1 8 4 |
| 6 | 0 4 12 8 9 13 5 1 2 6 14 10 11 15 7 3 |
| 7 | 0 6 10 12 5 3 15 9 11 13 1 7 14 8 4 2 |
| 8 | 0 7 8 15 1 6 9 14 3 4 11 12 2 5 10 13 |
| 9 | 0 5 14 11 13 8 3 6 10 15 4 1 7 2 9 12 |
| 10 | 0 13 7 10 15 2 8 5 14 3 9 4 1 12 6 11 |
| 11 | 0 2 6 4 12 14 10 8 9 11 15 13 5 7 3 1 |
| 12 | 0 9 11 2 6 15 13 4 12 5 7 14 10 3 1 8 |
| 13 | 0 10 15 5 14 4 1 11 13 7 2 8 3 9 12 6 |
| 14 | 0 15 1 14 3 12 2 13 7 8 6 9 4 11 5 10 |

  Unit test to add: for random data and every N used, encode from Sc and assert end state == Sc (AFF3CT does this). A
  more robust alternative that needs no table: solve Sc = (I + G^N)^(-1) S_N^0 over GF(2) [derived].
  N mod 15 for the native sizes: 56 -> 11, 152 -> 2, 236 -> 11, 492 -> 12, 752 -> 2 [derived].
- **Interleaver** (cl. 7.3.5.1.1) [EN], identical formula in AFF3CT `gen_lut`:
  - Level 1 (inside the couple): for j even (j mod 2 = 0), swap: (A_j, B_j) -> (B_j, A_j).
  - Level 2: for j = 0 ... N-1: Q(j) = 0 (j mod 4 = 0), 4 Q1 (= 1), 4 Q0 P + 4 Q2 (= 2), 4 Q0 P + 4 Q3 (= 3);
    i = Pi(j) = (P j + Q(j) + 3) mod N; the j-th couple of the interleaved sequence is the i-th couple of the
    (level-1-swapped) natural sequence.
  - Allowed signalling ranges for custom formats: **P in [9, 255], Q0 ... Q3 in [0, 15], gcd(P, 4 x bytes) = 1** [MW
    generator page]. [derived] P odd and coprime to N with all Q(j) multiples of 4 makes Pi a bijection when 4 | N
    (add an assert in code).
  - Order of the level-1 swap relative to level 2: the swap is applied to the natural-order couple index j before the
    permutation (as in DVB-RCS1 / AFF3CT); the extracted EN text does not spell out the order beyond "level 1, then
    level 2". **Ambiguity to test:** compare our encoder output with MATLAB `dvbrcs2TurboEncode` or AFF3CT for one block.
- **Full table of permutation parameters available (all Table A-1 sizes)** [EN Table A-1, AFF3CT, identical]:

| N couples | Payload bytes | P | Q0 | Q1 | Q2 | Q3 | Used by waveform IDs |
|---|---|---|---|---|---|---|---|
| 56 | 14 | 9 | 2 | 2 | 8 | 0 | 2 |
| 152 | 38 | 17 | 9 | 5 | 14 | 1 | 1, 3 |
| 204 | 51 | 23 | 10 | 5 | 0 | 0 | 44 |
| 220 | 55 | 23 | 6 | 10 | 4 | 0 | 45 |
| 236 | 59 | 23 | 10 | 2 | 11 | 1 | 4, 40, 41 |
| 248 | 62 | 23 | 6 | 8 | 1 | 1 | 46 |
| 276 | 69 | 25 | 1 | 1 | 2 | 0 | 47 |
| 336 | 84 | 23 | 8 | 1 | 4 | 1 | 48 |
| 340 | 85 | 23 | 6 | 13 | 10 | 0 | 5 |
| 372 | 93 | 25 | 1 | 7 | 2 | 1 | 49 |
| 384 | 96 | 25 | 1 | 2 | 0 | 1 | 6 |
| 400 | 100 | 23 | 10 | 8 | 2 | 1 | 32, 33 (and SS IDs 1, 2, 7, 8, 13, 14) |
| 432 | 108 | 29 | 1 | 4 | 1 | 1 | 7 |
| 460 | 115 | 29 | 6 | 5 | 0 | 0 | 8 |
| 492 | 123 | 31 | 0 | 3 | 1 | 0 | 13, 42 |
| 520 | 130 | 31 | 0 | 1 | 2 | 0 | 9 |
| 576 | 144 | 31 | 0 | 0 | 0 | 0 | 10 |
| 680 | 170 | 33 | 9 | 15 | 3 | 1 | 34, 35, 36 (and SS 3, 4, 9, 10, 15, 16) |
| 700 | 175 | 37 | 0 | 2 | 0 | 2 | 11 |
| 752 | 188 | 37 | 1 | 3 | 4 | 2 | 14, 43 |
| 776 | 194 | 39 | 7 | 0 | 0 | 0 | 12 |
| 1056 | 264 | 43 | 0 | 0 | 6 | 2 | 15 |
| 1192 | 298 | 49 | 0 | 3 | 5 | 0 | 16 |
| 1332 | 333 | 49 | 0 | 5 | 0 | 5 | 17 |
| 1420 | 355 | 53 | 1 | 4 | 6 | 2 | 18 |
| 1600 | 400 | 53 | 1 | 10 | 7 | 1 | 19 |
| 1752 | 438 | 59 | 1 | 1 | 2 | 1 | 37, 38, 39 (and SS 5, 6, 11, 12, 17, 18) |
| 1776 | 444 | 59 | 3 | 8 | 5 | 1 | 20 |
| 2156 | 539 | 65 | 0 | 3 | 7 | 0 | 21 |
| 2396 | 599 | 81 | 1 | 2 | 5 | 2 | 22 |

  AFF3CT also carries six "old waveforms (source unknown)" sizes 64, 228, 440, 652, 864, 1504 (e.g. 1504: P = 53,
  Q = 2, 1, 2, 2); not in V1.3.1 Table A-1, do not use them as "standard".
- **Puncturing** (cl. 7.3.5.1.3; patterns in Table A-1 columns "Y puncture" / "W puncture" as period + pattern) [EN]:
  applied identically to the natural (Y1, W1) and interleaved (Y2, W2) encoders; depends on the rate only.

| Rate | Y period / pattern | W period / pattern | Seen in rows | Check [derived] |
|---|---|---|---|---|
| 1/3 | 1 / 1 | 1 / 1 | 1, 2, 3, 13, 40-42 | 2 systematic + Y1 Y2 W1 W2 per couple = 1/3 |
| 1/2 | 1 / 1 | 1 / 0 | 4, 14, 43, SS 1, 3, 5 | 2 + Y1 Y2 = 1/2 |
| 2/3 | 2 / 10 | 1 / 0 | 45, SS 2 | 4 sys + 2 parity per 2 couples |
| 3/4 | 6 / 101000 | 1 / 0 | 46, 48 | 12 + 4 per 6 couples |
| 5/6 | 20 / 10001000100010000000 | 1 / 0 | 44, 47, 49 | 40 + 8 per 20 couples |

  (The 5/6 pattern was printed in pieces "100010 001000 100000 00"; read as one 20-bit string. MATLAB also supports
  4/5, 6/7, 7/8 [MW `dvbrcs2TurboDecode`]; not needed here.) [TR 6.3.1]: W is used only for rates below 1/2.
- **Encoder output streams:** Z1 = surviving Y1 bits (j = 0 ... N-1) followed by surviving W1 bits; Z2 the same from
  the interleaved encoder (cl. 7.3.5.1.0 / 7.3.5.1.3) [EN, as extracted; verify against MATLAB / AFF3CT]. Length M of
  each Z: 2N at rate 1/3, N at rate 1/2.
- **Channel interleaver:** **none for TC-LM** (the bit interleaver of cl. 7.3.5.2.3 is for CPM only) [EN].

### 1.5 Bit-to-symbol mapping (cl. 7.3.7.1.4, Tables 7-16, 7-17) [EN]
- **QPSK (Table 7-17):** symbols 0 ... N-1 carry the systematic couples, (u0, u1) = (A_k, B_k); then symbols
  N ... N+M-1 carry the parity, (u0, u1) = (Z1_k, Z2_k). So the burst payload = all systematic first, then parity.
  ID 13: 492 + 984 = 1476 symbols [derived] (matches Table A-1).
- **pi/2-BPSK (Table 7-16):** symbol order A_0, B_0, A_1, B_1, ..., then Z1_0, Z2_0, Z1_1, Z2_1, ...; bit 0 -> +1,
  bit 1 -> -1, then rotation by an n-dependent phase pi n / 2 plus pi/4, i.e. **s(n) = (1 - 2b) e^{j(pi n/2 + pi/4)}**
  (the equation itself is garbled in the extraction; this is the reading of "pi n / 2 + pi/4" in the text) [EN,
  reconstructed]. Whether n counts from the first burst symbol (preamble) or the first payload symbol is not legible;
  for AWGN with known timing this only changes a known phase reference. ID 42: 6 x 492 = 2952 symbols [derived] ✓.
- **QPSK constellation labels:** in Figure 7-20, which is a drawing and not in the extracted text. Assume DVB-S2
  style Gray mapping I = (1 - 2 u0)/sqrt2, Q = (1 - 2 u1)/sqrt2 **[assumption]**; any Gray labelling gives the same AWGN
  performance, so this does not affect validation.
- If the coded bit count is not a multiple of m, zeros are appended (cl. 7.3.7.1.4) [EN]; never happens for QPSK /
  BPSK at 1/3, 1/2 [derived].

### 1.6 Burst construction and unique word (cl. 7.3.6.1, 7.3.7.1.2-3, Annex A) [EN]
- Layout: preamble | payload sections separated by single-symbol pilot blocks | postamble. First pilot one pilot period
  after the last preamble symbol, i.e. P-1 data symbols, pilot, P-1 data, pilot, ...; pilots are inserted until the pilot
  sum is reached, then the remaining data, then the postamble (details in `lit_dvbrcs2.md` 1.1).
  Index form [derived], burst symbol index l = 0 ... L-1: preamble l < Lpre; pilots at l = Lpre - 1 + k P,
  k = 1 ... pilot_sum; postamble the last Lpost symbols. ID 13: pilots at 51, 71, ..., 1571; 13 data symbols after the
  last pilot; postamble 1585 ... 1615.
- **UW content:** one hex string per waveform = preamble bits | one pilot block bits | postamble bits, m bits per symbol,
  mapped like payload bits [EN 7.3.7.1.2-3; MW "UniqueWord covers the preamble, one pilot block and the postamble"].
  Every pilot block repeats the same pilot symbol(s).
- **UW hex strings from Table A-1** [EN] (spaces removed; the length check is [derived] = ceil((pre + 1 + post) m / 4)):

| ID | UW (hex) | hex digits (needed) |
|---|---|---|
| 2 | 3CF0003F0F30CCCFCFFC03CF0003F0F30CCCFCFFC0 | 42 (42) |
| 3 | F030F330CFFF00F030F330CFFF00 | 28 (28) |
| 4 | C300FCC33FC30C03F30CFF0 | 23 (23) |
| 13 | 3F00C30F3F3FCCC03CC0F03F3F00333C | 32 (32) |
| 14 | FC033FCC3030CFC033FCC30303 | 26 (26) |
| 41 | 37108FD095972F1BA7E7274340AB0 | 29 (29) |
| 42 | C7B6676A0A09D0B7B17D422B7B8E48E44 | 33 (33) |
| 43 | DFCCD0A1758493B4728DC5828F | 26 (26) |
| 40 | BB8874877B4BB447778B8848747B8844444784774B4B788474487BB778448788 + the ID 41 string | 93 (93) |

  (ID 1's 92-digit string is in the source rows; not needed here.) The QPSK UWs use only hex digits 0, 3, C, F, so every
  known QPSK symbol is (0,0) or (1,1): the known symbols lie on one diagonal (BPSK-like) [derived].
- **Bit order and padding [derived, not stated in the text read]:** read the hex MSB first, drop the **trailing** pad
  bits. Evidence: with this reading the pilot symbol is (0,0) in IDs 3, 4, 13, 14 and bit 0 in ID 42, matching
  Table 9-2's "solitary pilot symbol (0,0) for QPSK"; dropping leading bits instead gives (1,1) pilots. ID 3 and ID 4
  then have preamble = postamble (the ID 3 string is one 14-digit block repeated twice).
- Roll-off: RRC **0.20** only in V1.3.1 (cl. 7.3.7.1.1) [EN]; V1.5.1 adds 0.10 / 0.05 (`lit_card_sat.md`).

### 1.7 Lower-rate options: spread-spectrum TC-LM (SS-TC-LM) [EN cl. 7.3.7.1.5, Table A-2, Table 9-4]
- **The lowest native code rate is 1/3**: QPSK 1/3 (0.667 information bits per symbol before overhead) and pi/2-BPSK 1/3
  (0.333). Nothing near 1/10-0.15 exists in Table A-1.
- Below that, RCS2 uses **direct-sequence spreading** of pi/2-BPSK bursts: every symbol is repeated SF times and the whole
  burst (UW included) is multiplied chip by chip by a +-1 sequence (default: polynomial 1 + x + x^6 + x^10 + x^14 =
  0x2221, init 0x1F79, restarted every burst) [EN 7.3.7.1.5]. SF 1 ... 8 for traffic, up to 16 for logon [EN Table
  9-4]; MATLAB allows 2-16 for custom SS formats [MW].
- Table A-2 reference SS waveforms (19 rows, all pi/2-BPSK) [EN; read as a parsed table, the cells for even IDs' puncture
  columns and ID 19 are uncertain]: SF 2 (IDs 1-6), 4 (7-12), 8 (13-18), 16 (19); payload 100 / 170 / 438 B (N = 400 /
  680 / 1752 couples, the same P / Q as in the table above); **rate 1/2 (odd IDs) or 2/3 (even IDs)**; e.g. SS ID 1:
  100 B, 1600 payload symbols, burst 1792 symbols = 3584 chips, preamble 6 chips, pilot block 6 chips every 56 chips,
  pilot sum 378 chips (check: 3200 + 6 + 378 = 3584 chips ✓ [derived]).
- [derived] Information bits per chip: SS 1/2 SF 2 = 0.25, SF 4 = 0.125, SF 8 = 0.0625. Repetition gives no coding gain:
  on the Eb/N0 axis an SS burst performs like its un-spread code (plus the larger pilot overhead).
- **No PER table for SS-TC-LM** was found in TR 101 545-4 V1.1.1 or V1.2.1 (cl. 10.2.1 has none).
- What a faithful RCS2 operator would do at Es/N0 = -5 dB (per transmitted symbol / chip) [derived]: pi/2-BPSK 1/3
  needs at least -3.81 dB (ID 42) at PER 1e-3 even with ideal sync, so -5 dB is out of reach for any un-spread TC-LM
  waveform; the operator would assign an **SS-TC-LM burst with SF 2** (rate 1/2: per-symbol Es/N0 = chip Es/N0 +
  3.01 dB = -2.0 dB, above the ~ -1.5 dB the BPSK 1/2 code needs, e.g. ID 43 -1.53 dB) or a lower symbol rate. A rough
  estimate, not a published number.

---

## 2. Our payloads mapped to RCS2 burst formats (secondary now)

Frame PDU = our information bits rounded up to bytes (zero padding) + CRC; payload bytes must not be a multiple of 15
[derived from TR 6.3.1].

| Info bits | Data bytes (pad bits) | + CRC32 (traffic, faithful) -> N | + CRC16 (control-style) -> N | Nearest Table-A-1 N with ready P/Q (waste vs CRC32 custom) |
|---|---|---|---|---|
| 205 | 26 (3) | 30 B -> N = 120 **invalid** (120 mod 15 = 0) -> 31 B, **N = 124** | 28 B, N = 112 | 152 (38 B): +0.89 dB |
| 307 | 39 (1) | 43 B, **N = 172** | 41 B, N = 164 | 204 (51 B): +0.74 dB |
| 819 | 103 (5) | 107 B, **N = 428** | 105 B invalid -> 106 B, N = 424 | 432 (108 B, P/Q of ID 7): +0.04 dB; 492 (ID 13): +0.61 dB |
| 1024 | 128 (0) | 132 B, **N = 528** | 130 B, **N = 520** (P/Q of ID 9 ready) | 576 (144 B): +0.38 dB |

(waste = 10 log10(N_table / N_custom) [derived].)

Recommended RCS2 configuration per payload / our rate [derived; NCC-defined custom formats, cl. 6.4.6.1]:

| Our rate | Payload | RCS2 format | Payload symbols | Layout (ID template) |
|---|---|---|---|---|
| 1/10 | 205 b | pi/2-BPSK 1/3, N = 124 (or SS SF 2 for the -5 dB end) | 744 | ID 41/42 style: pre ~57-65, P = 18-20, post ~56-64 |
| 0.15 | 307 b | pi/2-BPSK 1/3, N = 172 | 1032 | ID 42 style: pre 65, P = 20 (54 pilots), post 64 |
| 2/5 | 819 b | QPSK 1/3, N = 428 (or 432 with ID 7's P/Q) | 1284 | ID 13 style: pre 32, P = 20 (67 pilots), post 31 |
| 1/2 | 1024 b | QPSK 1/2, N = 528 (or 520 with ID 9's P/Q, CRC16) | 1056 | ID 14 style: pre 25, P = 25 (44 pilots), post 25 |

For N = 124, 172, 428, 528 there are **no standard P / Q values**: the NCC chooses them. Neither the EN nor the TR gives a
design rule (TR 6.3.1 only says the laws are "tuned per block size" against an error floor above BER 1e-9). Practical
option: search P in [9, 255] (coprime to N), Q in [0, 15], maximising the minimum spread / simulating a few candidates at
PER 1e-3; or use the "N from the table" columns above where the padding waste is <= 0.1 dB (819 -> 432, 1024 -> 520).

---

## 3. Receiver as specified / recommended

### 3.1 Synchronisation
- EN 301 545-2 specifies no receiver; TR 101 545-4 gives **no TC-LM frequency / phase / UW algorithm**
  (`lit_dvbrcs2.md` 2). The documented chain is Griebel 2021: DA-KS (Rife-Boorstyn FFT over all known symbols +
  magnitude parabolic interpolation, constant phase) for pilot bursts, NDA M-th power for pre/post-only bursts, genie
  timing (`lit_ars2021.md` 2). For pi/2-BPSK, derotate by e^{-j(pi n/2 + pi/4)} first, then BPSK squaring (M = 2) NDA
  or DA-KS; Griebel used NDA M = 2 on burst 42 at -3.75 dB [Gr Fig. 7].
- CFO: the TR assumes 0.5-3 % of Rs; Griebel uses <= 1.5 % [TR 6.2.2, Gr].

### 3.2 Decoder
- **TR (cl. 6.3.2.1, 10.2.1):** BCJR in the log domain, **max-log-MAP** (min-sum form), **extrinsic scaling 0.7** in every
  iteration except the last (where it is not scaled), no noise-variance estimate needed; reference results "up to
  **8 iterations**, BCJR, normalized max-log-MAP", ideal synchronisation, AWGN [TR]. The stopping rule behind "up to"
  is not stated.
- **Griebel 2021:** max-log-MAP, extrinsic scaling **0.75**, **8 iterations**, 6-bit LLRs, 8-bit I/Q [Gr].
- **MATLAB `dvbrcs2TurboDecode`:** default 8 iterations; algorithm not named [MW].
- Duo-binary specifics (standard practice, not in the EN / TR text read): work on **symbol** (couple) metrics with three
  log-ratios per couple, L(01), L(10), L(11) vs 00; branch metric per transition = a-priori symbol metric + channel
  metrics of A, B, Y, W (Y, W punctured -> 0); the **level-1 swap** must be applied to the symbol extrinsics when moving
  between the two SISOs (00 and 11 unchanged, 01 <-> 10 for even j); **tail-biting**: initialise alpha_0 / beta_N of
  iteration i with alpha_N / beta_0 of iteration i-1 (uniform at the first iteration). Final bit LLRs from the symbol
  APPs: L(A) = max(01... ) form: L(A) = max(L10, L11) - max(L00, L01), L(B) = max(L01, L11) - max(L00, L10).
- **Burst declared correct:** by the **CRC** (CRC16 for logon / control, CRC32 for traffic) after descrambling order:
  CRC is checked on the decoded scrambled bits, then the PDU is descrambled [EN 7.3.4 order]. How the TR's PER was
  counted (CRC or genie comparison) is **not stated** [TR]. Recommended for our validation: genie PER (any bit error)
  for the reference curves, CRC-based acceptance for the receiver chain, and report both (with CRC32 they differ by
  < 1e-9 [derived]).

### 3.3 Fair "real-loss" anchor
- TR bench prototype: about 0.5 dB (QPSK 1/3) and 0.6 dB (QPSK 1/2) implementation loss at PER 1e-5 (`lit_dvbrcs2.md`
  1.3). Griebel DA-KS estimation loss 0.12-0.15 dB at FER 1e-3 (`lit_ars2021.md` 3).

---

## 4. Reference performance for validation (ideal sync, AWGN)

### 4.1 TR 101 545-4 cl. 10.2.1 [TR V1.1.1; same values in V1.2.1]
Es/N0 per transmitted symbol (pilots / UW not charged, see the 3.01 dB check in section 0).

| ID | Burst | Mod, rate | 1e-1 | 1e-2 | 1e-3 | 1e-4 | 1e-5 | Table |
|---|---|---|---|---|---|---|---|---|
| 2 | 262 | QPSK 1/3 | -0.53 | 0.06 | 0.50 | 0.87 | 1.29 | 10.4 (control bursts) |
| 41 (see caveat) | 1612 ("3 236" printed) | BPSK 1/3 | -4.00 | -3.65 | -3.38 | -3.17 | -2.98 | 10.4 |
| 3 | 536 | QPSK 1/3 | - | - | -0.27 | - | 0.22 | 10.5 |
| 4 | 536 | QPSK 1/2 | - | - | 1.92 | - | 2.34 | 10.5 |
| 13 | 1616 | QPSK 1/3 | - | - | -0.80 | - | -0.51 | 10.6 |
| 14 | 1616 | QPSK 1/2 | - | - | 1.49 | - | 1.71 | 10.6 |
| 42 | 3236 | BPSK 1/3 | - | - | -3.81 | - | -3.52 | 10.8 |
| 43 | 3236 | BPSK 1/2 | - | - | -1.53 | - | -1.30 | 10.8 |
| 5 / 15 | 536 / 1616 | QPSK 2/3 | - | - | 3.90 / 3.46 | - | 4.29 / 3.69 | 10.5 / 10.6 |

- **Caveat, the BPSK row of Table 10.4:** both TR versions print "41 | 3 236 | BPSK 1/3". ID 41 is 1612 symbols in
  Table A-1; 3236 is ID 42's length. The values cannot be ID 42 (ID 42 is -3.81 dB at 1e-3 in Table 10.8, this row
  -3.38). [derived] They fit ID 41's 236-couple code: its QPSK equivalent -3.38 + 3.01 = -0.37 dB lies between ID 3
  (152 couples, -0.27) and ID 13 (492 couples, -0.80). So the row is ID 41 with a misprinted burst length. Medium
  confidence.
- Griebel's genie reference curves (read by eye, +-0.03 dB) agree: ID 3 -0.23 dB, ID 4 1.97 dB, burst "42" -3.75 dB at FER
  1e-3 (`lit_ars2021.md` 3), i.e. within 0.05 dB of the TR with max-log-MAP, scaling 0.75, 8 iterations, 6-bit LLRs.
- **Validation target:** float max-log-MAP, scaling 0.7 (or 0.75), 8 iterations, genie sync; ID 13 at PER 1e-3 within
  0.1-0.2 dB of -0.80 dB and ID 42 of -3.81 dB. Packets needed [derived]: 1e-3 with +-20 % at 95 % needs ~100 errors =
  1e5 bursts per point; the 1e-5 column needs 1e7 per point (skip it or use fewer errors).
- Only 1e-3 and 1e-5 points exist for IDs 3, 4, 13, 14, 42, 43. No full PER curves with more points were found in an
  open source (AFF3CT has BER/FER curves for RCS1 / RCS2 turbo in its comparator database, not read).

---

## 5. Decoder complexity (MAC model inputs)

- **TR cl. 6.3.2.2-6.3.2.3 [TR]:** max-log-MAP cost "for the process of a trellis stage, or equivalently of an
  information symbol": **DVB-RCS2 16-state code (m = 2, n = 4): 267 additions and 159 compare-select operations**;
  DVB-RCS (8-state): 171 additions, 79 compare-selects. Multiplications by 2 are counted as free shifts. Table 6.7 has
  the per-step breakdown (branch metrics, forward / backward recursion, APP, extrinsic); it is garbled in the extraction.
  No iteration count, no memory figure.
- **Is it per SISO? [derived] yes.** 16 states x 4 branches = 64 transitions per stage: forward 64 adds + 16 x 3 = 48
  CS, backward the same, APP ~128 adds + 4 x 15 = 60 CS, plus branch metrics -> about 267 adds and 156-159 CS, which
  matches the TR totals. So one full iteration (2 SISOs) costs 534 adds + 318 CS per couple.
- **Per burst [derived]** (count add = 1 op, compare-select = 1 op; scaling of the extrinsic, 3 per couple, ignored):
  - per information bit per iteration: (534 + 318) / 2 = **426 ops**;
  - 8 iterations: **3 408 ops per encoder-input bit**;
  - ID 13 / 42 (N = 492): 852 x 492 x 8 = **3.35 M ops per burst**; ID 14 / 43 (N = 752): **5.13 M**; ID 3 (152):
    **1.04 M**; ID 4 (236): **1.61 M**.
  - Mapping to our MAC convention: these are add / compare operations, not multiplies. If our polar MAC count also
    counts f / g / sign-min operations as 1 MAC each, the numbers are directly comparable; otherwise state the
    convention. Early stopping (CRC every iteration) would cut the average at high SNR; the TR gives no number.
- **Parallelism:** a turbo decoder is usually parallelised by splitting the trellis into windows / sub-blocks (critical
  path ~ N / (number of windows) stages per half-iteration). No RCS2-specific window / core numbers were found.
  For our "MACs per core" model, a 32-way sub-block split of ID 13 gives ~15-16 stages per window plus the warm-up
  [derived, assumption about the architecture].

---

## 6. Ambiguities and what could not be obtained

| Item | Status | What I tried |
|---|---|---|
| Table 7-13 circulation states | EN text garbled; **AFF3CT values used and hand-checked** against the encoder (3 entries) | EN V1.3.1 text reader; AFF3CT source |
| Exact order level-1 swap vs level-2 | inferred (swap on natural index, then permute), as AFF3CT / RCS1 | EN text; verify against MATLAB `dvbrcs2TurboEncode` |
| Z1 / Z2 stream order (all Y then all W) | from the extracted text; verify | EN 7.3.5.1 |
| QPSK constellation labels (Fig. 7-20) | figure not extractable; assume Gray I = 1-2u0, Q = 1-2u1 | EN text |
| pi/2-BPSK equation and the index origin of n | garbled; reconstructed s(n) = (1-2b) e^{j(pi n/2 + pi/4)} | EN 7.3.7.1.4.1 |
| UW hex bit order / padding | not stated; trailing-pad, MSB-first inferred from the pilot = (0,0) check | EN 7.3.7.1.2-3, Table 9-2 |
| CRC16 final XOR / reflection | text: init 0, MSB first, no XOR mentioned | EN 7.3.4 |
| Which bursts carry CRC16 vs CRC32 in practice | Table 7-12: logon / control CRC16, traffic CRC32; Table A-1 does not say which IDs are control | EN |
| Table 10.4 BPSK row ID / length | misprint; assigned to ID 41 by consistency | TR V1.1.1 and V1.2.1 |
| PER definition / stopping rule of the TR results | not stated | TR 10.2.1 both versions |
| SS-TC-LM PER tables | none found | TR V1.1.1, V1.2.1 cl. 10.2.1 |
| P / Q design rule for custom N | none in EN / TR; MATLAB ranges only | EN, TR 6.3.1, MW |
| Turbo decoder parallel / hardware latency numbers for RCS2 | not found | - |

---

## 7. Per-component verdict vs our blind polar receiver (for the comparison, not for adoption)

| Part | RCS2 | Ours | Verdict |
|---|---|---|---|
| Code | 16-state duo-binary turbo, rate >= 1/3, N 56-2396 couples | polar N = 2048, CA-SCL-8, rates 1/10-1/2 | different families; compare on Eb/N0 per information bit |
| Error check | CRC32 traffic (2.3e-10 undetected), CRC16 control | CRC-16 + re-encoding rho | RCS2 traffic has 16 more CRC bits (0.1-0.3 dB rate cost at our sizes [derived]) but no second check |
| Known symbols | 5-24 % of the burst (IDs 13, 42: 8.7-8.8 %) | none | blind saves their energy; charge it on the Eb/N0 axis |
| Sync | not specified; DA-KS / NDA one-shot FFT (Griebel) | 4th-power fast path + grid + code-aided | already compared in est4 (`lit_ars2021.md` 5) |
| Decoder cost | ~3.4 k add/CS ops per bit at 8 iterations | our MACs per packet | use section 5 for the RCS2 MAC model |

---

## 8. Source table

| # | Source | Year | Link | Read | Relevance |
|---|---|---|---|---|---|
| 1 | ETSI EN 301 545-2 V1.3.1, DVB-RCS2 Lower layers | 2020 | [PDF](https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.03.01_60/en_30154502v010301p.pdf) | cl. 7.3.1-7.3.7.1.5, Table 9-2 / 9-4 summaries, Annex A Tables A-1, A-2 (text reader, chars 400k-700k) | high: the whole transmitter |
| 2 | ETSI TR 101 545-4 V1.1.1, Guidelines | 2014 | [PDF](https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.01.01_60/tr_10154504v010101p.pdf) | cl. 6.3.1-6.3.2.3 (decoder, complexity), 10.2.1 Tables 10.4-10.8 | high: decoder, complexity, PER |
| 3 | ETSI TR 101 545-4 V1.2.1 | 2026 | [PDF](https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.02.01_60/tr_10154504v010201p.pdf) | cl. 10 (chars 460k-560k): same Tables 10.4, 10.8; no SS table | medium: confirmation |
| 4 | AFF3CT, `Interleaver_core_ARP_DVB_RCS2.cpp` | current master | [GitHub raw](https://raw.githubusercontent.com/aff3ct/aff3ct/master/src/Tools/Interleaver/ARP/Interleaver_core_ARP_DVB_RCS2.cpp) | full file | high: P / Q table + permutation code |
| 5 | AFF3CT, `Encoder_RSC_DB.cpp` | current master | [GitHub raw](https://raw.githubusercontent.com/aff3ct/aff3ct/master/src/Module/Encoder/RSC_DB/Encoder_RSC_DB.cpp) | polynomial vectors, circ_states table, state-update logic (via a summariser) | high: encoder + circulation table |
| 6 | AFF3CT docs, turbo_DB encoder / interleaver parameters | - | [docs](https://aff3ct.readthedocs.io/en/latest/user/simulation/parameters/interleaver/interleaver.html) | search snippet | low: confirms RCS2 option exists |
| 7 | MathWorks `dvbrcs2WaveformGenerator` | - | [page](https://www.mathworks.com/help/satcom/ref/dvbrcs2waveformgenerator-system-object.html) | full page | medium: CRC inside payload, P / Q ranges, SF 2-16 |
| 8 | MathWorks `dvbrcs2TurboDecode` | - | [page](https://www.mathworks.com/help/satcom/ref/dvbrcs2turbodecode.html) | full page | medium: 8 iterations default, rates 1/3-7/8; reference implementation to check against |
| 9 | Griebel, Wasenmüller, Wehn, Adv. Radio Sci. 19 | 2021 | [ars](https://ars.copernicus.org/articles/19/59/2021/) | from `lit_ars2021.md` | high: decoder settings, genie FER |
| 10 | Boxerman, Bensimon, Greenberg, Ben-Shimol, "A novel reconfigurable vector-processed interleaving algorithm for a DVB-RCS2 turbo encoder", arXiv:2308.14128 | 2023 | [arXiv](https://arxiv.org/abs/2308.14128) | abstract | low: encoder interleaver speed-up 3.4x cycles; no P / Q table on the abstract page |

Comparability: RCS2 numbers are ideal-sync, Es/N0 per symbol with pilots not charged, roll-off 0.20, turbo codes of
112-1504 bits; our chain uses roll-off 0.25, polar N = 2048 and charges all overhead on Eb/N0. The 0.1-0.2 dB validation
target applies to the turbo code alone (genie sync).

---

## Reference entries (for the main session to merge into REFERENCES.md)

I had no edit tool for in-place changes to `BLIND_IMPLEMENTATION/REFERENCES.md` (only full-file overwrite, too risky for a
~2000-line file), so these lines follow the registry rule "other agents put their entries in a Reference entries
section of their own lit file".

**Used-in lines for existing entries:**
- C1 (EN 301 545-2): `- 2026-11-17: lit_rcs2_fullsystem.md (full TC-LM transmitter spec: scrambler, CRC16 / CRC32,
  turbo encoder, interleaver, puncturing, mapping, UW hex of IDs 2-4, 13, 14, 40-43; Table A-2 SS waveforms).`
- C2 (TR 101 545-4 V1.1.1): `- 2026-11-17: lit_rcs2_fullsystem.md (decoder: max-log-MAP, scaling 0.7, up to 8 iterations;
  complexity 267 add + 159 CS per stage per SISO; Table 10.4 full rows ID 2 and BPSK ID 41).`
- C3 (TR V1.2.1): `- 2026-11-17: lit_rcs2_fullsystem.md (confirms Tables 10.4 / 10.8; no SS-TC-LM PER table).`
- C4 (Griebel 2021): `- 2026-11-17: lit_rcs2_fullsystem.md (decoder settings 0.75 / 8 it / 6-bit, genie FER anchors).`
- C7 (MathWorks generator): `- 2026-11-17: lit_rcs2_fullsystem.md (payload = Frame PDU + CRC; P in [9, 255], Q in
  [0, 15]; SF 2-16).`

**New entries:**

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

### C87. MathWorks, `dvbrcs2TurboDecode` / `dvbrcs2TurboEncode` (Satellite Communications Toolbox)
- Link: https://www.mathworks.com/help/satcom/ref/dvbrcs2turbodecode.html   - Type: app note / reference code   - Read
  depth: full page
#### What it does
Standard-compliant RCS2 duo-binary turbo decoder, default 8 iterations, rates 1/3-7/8; algorithm not named.
#### What we took / could take
A bit-exact cross-check of our encoder (level-1 / level-2 order, Z1 / Z2 order) if MATLAB is available.
#### Used in
- 2026-11-17: lit_rcs2_fullsystem.md 3.2, 6.

### C88. O. Boxerman, M. Bensimon, S. Greenberg, Y. Ben-Shimol, "A novel reconfigurable vector-processed interleaving algorithm for a DVB-RCS2 turbo encoder", arXiv:2308.14128, 2023
- Link: https://arxiv.org/abs/2308.14128   - Type: paper   - Read depth: abstract
#### What it does
Parallel DSP interleaving for the RCS2 turbo encoder; speed-up up to 3.4x total cycles vs serial.
#### What we took / could take
Nothing (encoder-side hardware only).
#### Used in
- 2026-11-17: lit_rcs2_fullsystem.md source table (low relevance).
