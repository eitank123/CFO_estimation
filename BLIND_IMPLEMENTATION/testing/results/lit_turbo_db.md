# DVB-RCS2 TC-LM turbo code (16-state duo-binary, "Turbo-Phi"): bit-level mechanics for a Python encoder + decoder

Date: 2026-11-17. Scope: only the code mechanics (constituent encoder, circulation, interleaver, puncturing, bit
order, LLR conventions, max-log-MAP / log-MAP decoder, cost, test vectors). Burst formats, waveform IDs and reference
PER curves are in `lit_rcs2_fullsystem.md` (another agent), which also quotes EN 301 545-2 V1.3.1 text read through a
text reader. **I could not read the EN PDF myself**: every ETSI / DVB BlueBook PDF (EN 301 545-2 V1.1.1, V1.2.1,
A155-2r3) came back as compressed / encrypted binary through my fetch tool, and the local PDF reader is not installed.
So the normative items below are tagged:
- **[EN-x]**: EN text as extracted in `lit_rcs2_fullsystem.md` sec. 1.4-1.5 (not re-read by me);
- **[AFF]**: AFF3CT source code I read (via a summariser), C86;
- **[BOX]**: Boxerman et al. 2023, arXiv 2308.14128 (HTML read), C88;
- **[MW]**: MathWorks dvbrcs2TurboEncode / dvbrcs2TurboDecode pages, C87;
- **[derived]**: my own arithmetic / checks.

## 0. Bottom line for the implementer (ranked)

1. **Everything needed for a bit-level encoder is available and cross-checked by two sources**, except one item:
   polynomials, circulation table, P/Q table, ARP formula and puncturing patterns agree between AFF3CT and the EN text
   (as extracted), and I hand-checked the circulation table against the state update (sec. 1.3).
2. **Open ambiguity #1 (affects bit-exactness, not the code family): the interleaver direction.** The EN text (as
   extracted) says interleaved couple j = natural (swapped) couple i = Pi(j) ("read" form). **AFF3CT does the inverse**:
   `Encoder_turbo_DB.cpp` gathers with `lut_inv`, i.e. natural couple k is *written* to interleaved position Pi(k)
   (I checked that AFF3CT's `lut_inv[lut[i]] = i` and that `lut` = the ARP formula). So a Python encoder that follows
   the EN reading will **not** match AFF3CT test vectors, and AFF3CT's published FER curves are for the inverse
   permutation. Implement both behind a flag (`itl_dir = "read" | "write"`); the arbiter is MATLAB
   `dvbrcs2TurboEncode` (or a human reading cl. 7.3.5.1.1 of the PDF). [AFF], [EN-x], [derived]
3. **Strongest realistic decoder:** log-MAP (exact max*) or max-log-MAP with extrinsic scaling, 8 iterations, circular
   trellis handled by passing the state metrics across iterations (free), CRC-aided early stop for cost only. Run
   both log-MAP and max-log + scaling once at one rate and keep the better FER as the competitor; flip-and-check (FNC)
   adds nothing (AFF3CT curves, sec. 5).
4. **Validation target (FER, not bit-exact):** AFF3CT reference curves for K = 1504 bits (752 couples), QPSK AWGN,
   max-log + adaptive SF, 8 iterations: rate 1/2 FER 1.22e-2 at Eb/N0 1.4 dB and 5.91e-4 at 1.6 dB; rate 1/3 FER
   6.49e-3 at 0.8 dB; rate 2/3 FER 2.17e-2 at 2.2 dB (sec. 5). Our implementation should land within about 0.05 dB of
   these when run with AFF3CT's interleaver direction.
5. **Decoder cost [derived]:** about 460 add/compare operations per couple per SISO pass (half-iteration) for
   max-log-MAP, about 930 per couple per iteration; 8 iterations at N = 152 couples (304 bits) = 1.13 M ops, at
   N = 752 couples = 5.6 M ops. Log-MAP adds about 156 correction-term evaluations per couple per half-iteration
   (about +50-100 % depending on the LUT cost).

## 1. Constituent encoder (16-state duo-binary CRSC)

### 1.1 Connections [AFF] (polynomial vectors), [EN-x] (structure)
AFF3CT `Encoder_RSC_DB.cpp`, DVB-RCS2 branch (n_ff = 4): A = {1,0,0,0}, B = {1,1,0,1}, Y = {1,1,1,0,1},
W = {1,0,1,1,1}, feedback = {0,0,1,1}. AFF3CT semantics (read in the code): register s[0..3] (s[0] = S1 = MSB of the
state integer), feedback = XOR of F[r] s[r] over the OLD state; new s'[0] = fb ^ A[0]a ^ B[0]b;
s'[r] = s[r-1] ^ A[r]a ^ B[r]b; parity uses the NEW s'[0] and the OLD s[r]: Y = Y[0]s'[0] ^ XOR_r Y[r+1]s[r].
Written out (S = 8 S1 + 4 S2 + 2 S3 + S4) [derived]:

```
f   = S3 ^ S4 ^ A ^ B      # new S1
S1' = f
S2' = S1 ^ B
S3' = S2
S4' = S3 ^ B
Y   = f ^ S1 ^ S2 ^ S4     # 1 + D + D^2 + D^4
W   = f ^ S2 ^ S3 ^ S4     # 1 + D^2 + D^3 + D^4
```

- Feedback 1 + D^3 + D^4 (period 15, primitive) -> the "N mod 15" rule and the 14-row circulation table [derived].
- A enters tap 1 only; B enters taps 1, 2 and 4. Input couple order: A = first bit, B = second bit of each couple
  (AFF3CT `U[2c]`, `U[2c+1]`); EN: MSB of the first byte = A_0, next bit B_0 [EN-x].
- Symbol index used by AFF3CT tables: d = 2A + B (00, 01, 10, 11).

### 1.2 Difference to the 8-state DVB-RCS1 / IEEE 802.16 (WiMAX) CTC [AFF]
| | DVB-RCS1 / WiMAX CTC | DVB-RCS2 TC-LM |
|---|---|---|
| States | 8 (3 flip-flops) | 16 (4 flip-flops) |
| Feedback | 1 + D + D^3 (AFF3CT {1,0,1}) | 1 + D^3 + D^4 ({0,0,1,1}) |
| Y parity | 1 + D^2 + D^3 ({1,0,1,1}) | 1 + D + D^2 + D^4 ({1,1,1,0,1}) |
| W parity | 1 + D^3 ({1,0,0,1}) | 1 + D^2 + D^3 + D^4 ({1,0,1,1,1}) |
| B injection | taps 1, 2, 3 | taps 1, 2, 4 |
| Period / table | 7 / 6 rows x 8 | 15 / 14 rows x 16 |
| Interleaver | i = (P0 j + P + 1) mod N, P in {0, N/2+P1, P2, N/2+P3} | i = (P j + Q + 3) mod N (sec. 2) |
| Rates | 1/3, 2/5, 1/2, 2/3, 3/4, 4/5, 6/7 | 1/3, 1/2, 2/3, 3/4, 4/5, 5/6, 6/7, 7/8 [MW] |

AFF3CT RCS1 P0..P3 rows (header file, listed without sizes; sizes 48, 64, 212, 220, 228, 424, 432, 440, 752, 848,
856, 864 are listed in the .cpp; I assume the same order, **not verified**): (11,24,0,24), (7,34,32,2),
(13,106,108,2), (23,112,4,116), (17,116,72,188), (11,6,8,2), (13,0,4,8), (13,10,4,2), (19,2,16,6), (19,428,224,652),
(19,2,16,6), (19,376,224,600). Comparison only; not needed for RCS2.

### 1.3 Circulation (tail-biting) state [AFF], [EN-x]
Procedure (both encoders, independently: C1 natural, C2 interleaved): (1) encode the N couples from S = 0, final state
S_N^0; (2) Sc = T[(N mod 15) - 1][S_N^0] (AFF3CT row index; N mod 15 = 0 is forbidden); (3) encode again from Sc;
the end state equals Sc (AFF3CT throws if not). The 14 x 16 table (AFF3CT `circ_states`, identical to the one
reproduced in `lit_rcs2_fullsystem.md` sec. 1.4):

```
N%15= 1: 0 14  3 13  7  9  4 10 15  1 12  2  8  6 11  5
N%15= 2: 0 11 13  6 10  1  7 12  5 14  8  3 15  4  2  9
N%15= 3: 0  8  9  1  2 10 11  3  4 12 13  5  6 14 15  7
N%15= 4: 0  3  4  7  8 11 12 15  1  2  5  6  9 10 13 14
N%15= 5: 0 12  5  9 11  7 14  2  6 10  3 15 13  1  8  4
N%15= 6: 0  4 12  8  9 13  5  1  2  6 14 10 11 15  7  3
N%15= 7: 0  6 10 12  5  3 15  9 11 13  1  7 14  8  4  2
N%15= 8: 0  7  8 15  1  6  9 14  3  4 11 12  2  5 10 13
N%15= 9: 0  5 14 11 13  8  3  6 10 15  4  1  7  2  9 12
N%15=10: 0 13  7 10 15  2  8  5 14  3  9  4  1 12  6 11
N%15=11: 0  2  6  4 12 14 10  8  9 11 15 13  5  7  3  1
N%15=12: 0  9 11  2  6 15 13  4 12  5  7 14 10  3  1  8
N%15=13: 0 10 15  5 14  4  1 11 13  7  2  8  3  9 12  6
N%15=14: 0 15  1 14  3 12  2 13  7  8  6  9  4 11  5 10
```

Hand checks [derived], using the zero-input map G (S1' = S3^S4, S2' = S1, S3' = S2, S4' = S3) and the condition
Sc ^ G^n(Sc) = S_N^0 with n = N mod 15:
- n = 1, S_N^0 = 1: Sc = 14 = 1110 -> G = 1111 -> 1111 ^ 1110 = 0001 = 1 (ok).
- n = 1, S_N^0 = 2: Sc = 3 = 0011 -> G = 0001 -> 0001 ^ 0011 = 0010 = 2 (ok).
- n = 2, S_N^0 = 1: Sc = 11 = 1011 -> G = 0101 -> G^2 = 1010 -> 1010 ^ 1011 = 0001 (ok).
These also confirm the bit order of the state integer (S1 = MSB). Unit test to write: build T by solving
(I + G^n) Sc = S_N^0 over GF(2) for n = 1..14 and assert it equals the table above, then for random data and every
N used assert end state == Sc.

## 2. Interleaver (two levels, N couples)

### 2.1 Formula [AFF] (`Interleaver_core_ARP_DVB_RCS2.cpp`), [BOX] eq. 1-3, [EN-x]
- Level 2: i = Pi(j) = (P j + Q(j) + 3) mod N with Q = 0 (j mod 4 = 0), 4 Q1 (= 1), 4 Q0 P + 4 Q2 (= 2),
  4 Q0 P + 4 Q3 (= 3). Identical in AFF3CT, BOX and EN-x.
- Parameter ranges for custom sizes [MW]: P in [9, 255], Q0..Q3 in [0, 15], P coprime to N.
- [derived] With N a multiple of 4 and P odd, every Q is a multiple of 4, so i = j + 3 + (P-1) j + Q = j + 1 (mod 2):
  **Pi maps even j to odd i and odd j to even i** (the RCS "odd/even rule").

### 2.2 Level 1 (intra-couple swap): three statements, one reading [derived]
- EN-x: "for j even, (A_j, B_j) -> (B_j, A_j)", applied to the natural sequence, then level 2.
- AFF3CT: swaps natural couples 0, 2, 4, ... (even natural index) before the permutation.
- BOX eq. 1: "if j mod 2 = 1, (A_j, B_j) -> (B_j, A_j)".
- These agree if BOX's j indexes the interleaved sequence: by the odd/even rule, interleaved position j odd <=>
  natural index i = Pi(j) even. So **swap = natural even couples**; I consider this settled.

### 2.3 Direction (open ambiguity #1)
- EN-x: "the j-th couple of the interleaved sequence is the i-th couple of the (level-1-swapped) natural sequence":
  `V[j] = S[Pi(j)]` ("read").
- AFF3CT encoder: `V[c] = S[lut_inv[c]]` with `lut = Pi`, i.e. `V[Pi(k)] = S[k]` ("write"); the decoder uses the same
  convention (natural -> interleaved via `lut_inv`, back via `lut`). Checked: `Interleaver_core.hxx` sets
  `pi_inv[pi[i]] = i` and `gen_lut` writes `pi`.
- So AFF3CT = EN-x with Pi replaced by Pi^-1. Same ARP family and same spread (the spread is symmetric under
  inversion), so the FER should be practically the same, but this is **not proven** (the level-1 swap then lands on
  the other parity class, so the two codes are not trivially equivalent) [derived]. The IEEE 802.16 CTC had the same
  read/write and swap-order ambiguity, raised in maintenance contributions C80216maint-05_149 / 05_151 (titles and
  search snippets only; the PDFs were not legible to my tool).

### 2.4 Parameter table
All 30 V1.3.1 Table A-1 sizes (56 ... 2396 couples) are in `lit_rcs2_fullsystem.md` sec. 1.4; I re-read AFF3CT's
table and it matches entry for entry (e.g. 152: 17, 9, 5, 14, 1; 492: 31, 0, 3, 1, 0; 752: 37, 1, 3, 4, 2;
2396: 81, 1, 2, 5, 2). AFF3CT also has six "old waveforms (source unknown)" sizes (64? / 228, 440, 652, 864, 1504);
do not use them. [derived] Spot checks: no Table A-1 N is a multiple of 15 (e.g. 152 mod 15 = 2, 492 mod 15 = 12,
752 mod 15 = 2, 1332 mod 15 = 12), and P is coprime to N for the ones I checked (576/31, 700/37, 1332/49, 2156/65,
2396/81).

## 3. Puncturing and coded-bit order

### 3.1 Patterns (same pattern for the natural Y1/W1 and interleaved Y2/W2 encoders; 1 = keep, per couple)
| Rate | Y pattern (period in couples) | W pattern | Source |
|---|---|---|---|
| 1/3 | 1 (1) | 1 | EN-x, AFF |
| 1/2 | 1 (1) | 0 | EN-x, AFF |
| 2/3 | 10 (2) | 0 | EN-x, AFF |
| 3/4 | 101000 (6) | 0 | EN-x, AFF (AFF: bits {0,1,4,5} of a 12-bit Y-block period) |
| 4/5 | 1000 (4) | 0 | AFF only |
| 5/6 | 10001000100010000000 (20) | 0 | EN-x, AFF (AFF: bit offsets {0,1,8,9,16,17,24,25} of 40) |
| 6/7 | 100010000000 (12) | 0 | AFF only |
| 7/8 | 1000100000001000000010000000 (28) | 0 | AFF only |
| 2/5 | 1 | 10 (2) | AFF only; an RCS1 rate, not in the RCS2 rate list [MW] |

The AFF3CT masks are per bit of its Y block, which holds (Y1_c, Y2_c) pairs, so one couple-pattern "1" keeps both
Y1_c and Y2_c [AFF], [derived].

### 3.2 Order of the coded bits [AFF], [EN-x], [derived]
- EN-x: Z1 = surviving Y1 (j = 0..N-1) then surviving W1; Z2 the same for the interleaved encoder; QPSK symbol k < N
  carries (A_k, B_k), symbol N + k carries (Z1_k, Z2_k).
- AFF3CT codeword: [U (A_0 B_0 A_1 B_1 ...) | kept bits of (Y1_0 Y2_0 Y1_1 Y2_1 ...) | kept bits of
  (W1_0 W2_0 ...)].
- [derived] Read in pairs these give exactly the EN QPSK order at every rate (at 1/3 the Y pairs come first, then the
  W pairs, which is Z1 = Y1 then W1). So AFF3CT's bit order can be used as is for QPSK.

### 3.3 LLR conventions
- AFF3CT: L = ln P(b=0)/P(b=1), BPSK 0 -> +1. The decoder halves each LLR and builds the systematic symbol metrics
  L(00) = (La + Lb)/2, L(01) = (La - Lb)/2, L(10) = (-La + Lb)/2, L(11) = (-La - Lb)/2 [AFF `_load`]; parity metrics
  the same way.
- MATLAB `dvbrcs2TurboDecode`: positive soft bit = 1; its examples pass `-1*demodLLR` [MW]. Flip the sign when feeding
  MATLAB.

## 4. Decoder: max-log-MAP / log-MAP for the duo-binary trellis

### 4.1 Structure (AFF3CT `Decoder_turbo_DB.cpp`, `Decoder_RSC_DB_BCJR.cpp`) [AFF]
- Each couple carries 4 symbol metrics (AFF3CT stores all 4; 3 values relative to 00 are enough).
- One iteration = SISO on the natural order, then on the interleaved order. Extrinsic natural -> interleaved: swap
  the 01 and 10 metrics of even natural couples, then permute couples; back: inverse permutation, swap again.
- A posteriori decision: A = 1 if max(L10, L11) > max(L00, L01); B = 1 if max(L01, L11) > max(L00, L10).
- Circular trellis: alpha_0 and beta_N start at zero (uniform) in the first iteration and are then initialised from
  the previous iteration's alpha_N / beta_0 ("metric passing"; reset per frame). No prologue, no extra cost.
- max* options in AFF3CT: `MAX` (max-log), `MAXL` (linear approximation), `MAXS` (exact log-MAP) (`--dec-max`).
- Extrinsic scaling (`--dec-sf-type`, applied after each half-iteration): `ADAPTIVE` = 0.5 in iterations 1-2, then
  0.85; `LTE` = constant 0.75; `CST x`; `ARRAY` = 0.15, 0.25, 0.30, 0.40, 0.70, 0.80, 0.90, 0.95 for iterations
  1-8. AFF3CT's DVB-RCS2 reference curves use `ADAPTIVE` with `MAX`.
- Iterations: MATLAB default 8 [MW]; AFF3CT default 6, its RCS2 reference curves use 8; CRC-aided stop from
  iteration 2 (`--dec-crc-start 2`) in AFF3CT.
- Max-log loss on duo-binary codes is small: "the correction term ... can be omitted for double-binary turbo codes
  with minor error rate performance degradation" (Martina and Masera, C92, 8-state WiMAX, N = 1920, 8 iterations).
  I found **no published number for the 16-state RCS2 code** and no primary source for 0.75 as the duo-binary
  optimum (0.75 is AFF3CT's "LTE" constant; the classic binary result is Vogt and Finger 2000, about 0.2-0.4 dB gain
  from scaling, which I could not open, IET returned 403).

### 4.2 Recommended "strongest realistic" competitor decoder
max-log-MAP with scaling (ADAPTIVE or 0.75), 8 iterations, metric passing, CRC early stop; plus one run of log-MAP
(MAXS) at one rate and SNR to measure the gap. If log-MAP is better by more than about 0.05 dB, use it as the
competitor and charge its cost. FNC (flip-and-check) is not worth it: identical FER in AFF3CT's curves (sec. 5).

### 4.3 Operation count per couple [derived]
16 states x 4 inputs = 64 branches per couple per trellis step. Max-log-MAP, one SISO pass (half-iteration):

| Step | Operations per couple |
|---|---|
| Branch metrics: 4 symbol terms (a priori + systematic) x 4 parity terms (Y, W) = 16 values | ~15 adds |
| Forward alpha: 64 adds + 16 x 3 compares + 15 normalisation subtractions | ~127 |
| Backward beta: same | ~127 |
| Extrinsic: 64 x 2 adds (alpha + gamma_par + beta), 4 x 15 compares, 3 subtractions (relative to 00, minus a priori and systematic), 3 scaling multiplies | ~194 |
| **Total per half-iteration** | **~463** |
| **Per full iteration (2 SISOs)** | **~926** |

Examples (8 iterations, no early stop): N = 152 couples (304 bits): 926 x 152 x 8 = 1.13 M ops; N = 492: 3.64 M;
N = 752: 5.57 M. Log-MAP: each of the 48 + 48 + 60 = 156 max operations per half-iteration also needs a correction
term (subtract, abs, LUT, add), about +470 ops, so about 2x max-log in software. Counting convention: each add, compare
or multiply = 1 operation; mapping this to the project's "MACs per core" is the main session's call. Parallel
schedule: forward and backward can run on 2 cores, and windowed / sub-block decoding with metric passing splits the
N couples over P cores (critical path about total / P plus window warm-up); not quantified here.

## 5. Reference implementations, test vectors and reference FER

| What | Where | Bit-exact use | FER use |
|---|---|---|---|
| AFF3CT encoder / interleaver / decoder / puncturer (C86) | github.com/aff3ct/aff3ct: `src/Module/Encoder/RSC_DB/Encoder_RSC_DB.cpp`, `src/Module/Encoder/Turbo_DB/Encoder_turbo_DB.cpp`, `src/Tools/Interleaver/ARP/Interleaver_core_ARP_DVB_RCS2.cpp`, `src/Module/Puncturer/Turbo_DB/Puncturer_turbo_DB.cpp`, `src/Module/Decoder/Turbo_DB/Decoder_turbo_DB.cpp`, `src/Module/Decoder/RSC_DB/BCJR/Decoder_RSC_DB_BCJR.cpp` | yes, against AFF3CT's convention ("write" interleaver): `aff3ct --sim-type BFER -C TURBO_DB -K 1504 -N 3008 --enc-sub-std DVB-RCS2 -i 8 --dec-sf-type ADAPTIVE -m 3 -M 3 --sim-dbg --sim-dbg-fra 2` prints source U_K, encoder X_N, puncturer output and decoder in/out per frame (`--sim-dbg-hex` for exact floats) | yes |
| AFF3CT error-rate references (C90) | github.com/aff3ct/error_rate_references, `TURBO_DB/AWGN/BPSK/RSC_DB_RSC_DB/BCJR/Turbo_DB_N{1880,2256,3008,4512}_K1504_BCJR_i8_{ref,fnc}_DVB-RCS2.txt` (and `N3008 ... DVB-RCS1`) | no | yes; each file starts with the exact command line |
| MathWorks `dvbrcs2TurboEncode` / `dvbrcs2TurboDecode` (C87) | Satellite Communications Toolbox, closed source | yes, against MathWorks' reading of EN cl. 7.3.5.1: e.g. `dvbrcs2TurboEncode(msg, "1/2", [37 1 3 4 2])` with 1504 bits; this is the arbiter for ambiguity #1 | yes (decoder algorithm not documented; 8 iterations default) |
| technoas123/turbo_encdoer (GitHub) | HDL encoder for RCS2, no formulas / vectors / licence shown | unknown, not checked | no |
| OpenAirInterface, GNU Radio | no 16-state duo-binary RCS2 turbo found | - | - |

AFF3CT reference FER (QPSK, AWGN, K = 1504 incl. a CRC-32, 8 iterations, max-log `MAX`, `ADAPTIVE` SF; Eb/N0 counts
the 1472 information bits; Es/N0 = Eb/N0 + 10 log10(2 x 1472/N) dB, shown when given):

| Rate (N coded bits) | Eb/N0 (dB) : FER |
|---|---|
| 1/3 (4512) | 0.6 (Es/N0 -1.25): 8.01e-2; 0.8 (-1.05): 6.49e-3; 1.0 (-0.85): 2.37e-4; 1.2 (-0.65): 2.64e-6 |
| 1/2 (3008) | 1.2 (1.11): 1.07e-1; 1.4 (1.31): 1.22e-2; 1.6 (1.51): 5.91e-4; 1.8 (1.71): 9.22e-6 |
| 1/2 (3008), with FNC | 1.4: 1.22e-2; 1.6: 5.87e-4; 1.8: 9.30e-6 (no gain) |
| 2/3 (2256) | 2.0 (3.16): 1.44e-1; 2.2 (3.36): 2.17e-2; 2.4 (3.56): 1.31e-3; 2.6 (3.76): 4.86e-5 |

Comparability: these are for 752 couples, AFF3CT's interleaver direction, symbol-rate AWGN with no synchronisation;
our shorter blocks (e.g. 152 / 492 couples) will need about 0.5-1 dB more [rough expectation, not a cited number].

## 6. Remaining ambiguities (explicit list)
1. **Interleaver direction** (read Pi vs write Pi = AFF3CT): open; settle with MATLAB or the PDF text (sec. 2.3).
2. Level-1 swap parity: settled as "natural even couples" [derived, sec. 2.2]; recheck with the same test vector.
3. Puncturing for 4/5, 6/7, 7/8: AFF3CT only (not in the EN-x extract); 1/3, 1/2, 2/3, 3/4, 5/6 confirmed by both.
4. Whether Y2 / W2 use exactly the same pattern positions as Y1 / W1 (indexed by the interleaved couple index): both
   sources say yes; the odd/even rule is designed for it.
5. Coded-bit order for 8PSK / 16QAM (bit-to-label mapping): out of my scope; for QPSK AFF3CT's order = EN-x order.
6. AFF3CT "legacy" sizes (source unknown): do not use.
7. The circulation table rests on AFF3CT plus my 3 hand checks plus the other agent's 3 (the EN table text was
   garbled); the GF(2) unit test in sec. 1.3 removes this risk.
8. LLR sign: AFF3CT positive = 0, MATLAB positive = 1.
9. MATLAB's decoder algorithm (log-MAP vs max-log, scaling) is undocumented, so MATLAB FER is not a clean max-log
   reference.

## 7. Per-source table
| # | Source | Year | Link | Relevance | What I read | Numbers / content used |
|---|---|---|---|---|---|---|
| C86 | AFF3CT source (RCS2 interleaver, RSC_DB encoder, turbo_DB encoder / decoder, BCJR, puncturer, Interleaver_core) | current master | https://github.com/aff3ct/aff3ct | high: the only open, complete RCS2 codec | source files via summariser | polynomials, 14x16 circulation table, P/Q table, ARP formula, lut_inv gather, puncturing masks, metric passing, LLR packing |
| C87 | MathWorks dvbrcs2TurboEncode / dvbrcs2TurboDecode | current | https://www.mathworks.com/help/satcom/ref/dvbrcs2turboencode.html , https://www.mathworks.com/help/satcom/ref/dvbrcs2turbodecode.html | high: independent bit-exact arbiter (needs licence) | doc pages | rates 1/3-7/8, P in [9,255], Q in [0,15], 8 iterations default, positive soft bit = 1 |
| C88 | Boxerman, Bensimon, Greenberg, Ben-Shimol, "A Novel Reconfigurable Vector-Processed Interleaving Algorithm for a DVB-RCS2 Turbo Encoder" | 2023 | https://arxiv.org/html/2308.14128 | medium: second copy of the interleaver equations | HTML full text | eq. 1-3 (swap j odd, Pi = P j + Q + 3), 11 sizes 56-2396, CEVA-XC4500 speed-up up to 3.4x |
| C90 | AFF3CT error_rate_references, TURBO_DB | current | https://github.com/aff3ct/error_rate_references | high: reference FER with command lines | 4 RCS2 files | table in sec. 5 |
| C91 | AFF3CT documentation (Turbo DB encoder / decoder, RSC DB decoder, simulation debug options) | v4.5.0 | https://aff3ct.readthedocs.io/en/v4.5.0/user/simulation/parameters/codec/turbo_db/decoder.html | medium: flags for test vectors | doc pages | SF types and values, `--enc-sub-std DVB-RCS2`, `--dec-max MAX/MAXL/MAXS`, `--sim-dbg` |
| C92 | Martina, Masera, "Improving Network-on-Chip-based turbo decoder architectures" | 2011 | https://ar5iv.labs.arxiv.org/html/1105.1014 | low-medium: max-log is enough for duo-binary | HTML | 8-state WiMAX, N = 1920, 8 iterations; max* correction can be dropped with minor loss |
| C93 | IEEE 802.16 maintenance contributions C80216maint-05_149, 05_151 (CTC interleaver wording) | 2005 | https://grouper.ieee.org/groups/802/16/maint/contrib/C80216maint-05_151.pdf | low: shows the same ambiguity existed for WiMAX CTC | search snippets only; PDFs not legible | swap order and P(j) address meaning were ambiguous in 802.16 |
| - | ETSI EN 301 545-2 (V1.1.1, V1.2.1), DVB A155-2r3 | 2012-2023 | (C1 in REFERENCES.md) | high | **not legible to my tool** | relied on `lit_rcs2_fullsystem.md` extraction |
| - | Vogt and Finger, "Improving the max-log-MAP turbo decoder", Electron. Lett. | 2000 | https://doi.org/10.1049/el:20001357 | medium | **not read** (403); claim only from a search snippet | 0.2-0.4 dB from scaling (binary 3GPP) |
| - | technoas123/turbo_encdoer | 2025? | https://github.com/technoas123/turbo_encdoer | low | README only | HDL encoder, no vectors seen |

## Reference entries (for the coordinator to merge into REFERENCES.md; I did not edit it)
Numbers used: C86 and C87 reused (assigned by the coordinator); new entries C89-C93.
Merged into REFERENCES.md 2026-11-17: the Boxerman entry (scout's C89) duplicates the existing C88 and was merged
there (citations in this file now say C88; C89 is not used); C90-C93 added as numbered; C91 also absorbs the AFF3CT
documentation entry of `lit_vde_fec.md`.

### C88 (merged into the existing C88). Boxerman, Bensimon, Greenberg, Ben-Shimol, "A Novel Reconfigurable Vector-Processed Interleaving Algorithm for a DVB-RCS2 Turbo Encoder", arXiv 2308.14128v2 (2023)
- Link: https://arxiv.org/html/2308.14128   - Type: preprint
- Read depth: HTML full text (via a summariser)
#### What it does
Vectorised DSP (CEVA-XC4500) version of the RCS2 two-level interleaver; quotes eq. 1 (swap if j mod 2 = 1),
eq. 2-3 (Pi(j) = (P j + Q + 3) mod N, Q = 0 / 4Q1 / 4Q0P + 4Q2 / 4Q0P + 4Q3); up to 3.4x fewer cycles.
#### What we took / could take
Second source for the ARP formula; its "j odd" swap equals AFF3CT's "natural even" by the odd/even rule [derived].
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 2.1-2.2.

### C90. AFF3CT error_rate_references, TURBO_DB DVB-RCS2 curves
- Link: https://github.com/aff3ct/error_rate_references (TURBO_DB/AWGN/BPSK/RSC_DB_RSC_DB/BCJR/)   - Type: data
- Read depth: 4 files (N1880 / N2256 / N3008 ref + fnc / N4512, K = 1504)
#### What it does
Reference BER / FER of the RCS2 code with the exact AFF3CT command line (QPSK AWGN, max-log, adaptive SF, 8 it).
#### What we took / could take
FER validation targets for our Python decoder (e.g. rate 1/2 FER 1.22e-2 at Eb/N0 1.4 dB).
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 5.

### C91. AFF3CT documentation v4.5.0 (Turbo DB / RSC DB codec parameters, simulation debug)
- Link: https://aff3ct.readthedocs.io/en/v4.5.0/user/simulation/parameters/codec/turbo_db/decoder.html   - Type: docs
- Read depth: 4 doc pages
#### What it does
Flags: `--enc-sub-std DVB-RCS2`, `--dec-max MAX|MAXL|MAXS`, `--dec-sf-type ADAPTIVE (0.5, then 0.85) | LTE (0.75) |
CST | ARRAY`, `--dec-crc-start`, `--sim-dbg` (prints every task's frames, hex option).
#### What we took / could take
Recipe to dump bit-exact test vectors and the scaling options for the competitor decoder.
#### Used in
- 2026-11-17: `testing/results/lit_turbo_db.md` sec. 4.1, 5.

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

Used-in lines to append to existing entries:
- C86 (AFF3CT RCS2 turbo files): "2026-11-17: `lit_turbo_db.md`: encoder taps, circulation table (3 hand checks),
  ARP table, puncturing masks, **AFF3CT interleaves with lut_inv (inverse of the EN 'read' form)**, decoder metric
  passing, op count."
- C87 (MathWorks): "2026-11-17: `lit_turbo_db.md`: named as bit-exact arbiter for the interleaver direction; LLR
  sign positive = 1; 8 iterations default."
- C1 (EN 301 545-2): "2026-11-17: `lit_turbo_db.md`: PDF not legible to the scout's tool; EN items taken from the
  `lit_rcs2_fullsystem.md` extraction."
