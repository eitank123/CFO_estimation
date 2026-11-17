# Polar rate matching for native competitor formats (DVB-RCS2, VDE-SAT)

Literature scout, 2026-11-17. Scope: how to make our CA-SCL-8 / CRC-16 polar code carry exactly the payload of a
competitor burst in exactly its number of coded bits (arbitrary K, E), what it costs in dB, what part of a gain vs
DVB-RCS2 / VDE-SAT comes from the code alone, and what rate matching does to the blind search.
Marks: [std] standard text, [paper], [code] reference implementation, [derived] my arithmetic, [unverified] not
read in a primary source.

**Read-depth warning.** The TS 38.212 PDF (ETSI V15.5.0) downloaded only as binary and could not be read here. The
5G rules below are taken from two sources that copy the standard: the Bioglio-Condo-Land tutorial (full text read)
and NVIDIA Sionna's `Polar5GEncoder` source (code read). They agree on every rule I checked except one off-by-one
noted in 1.4. Before you freeze the code, check the 3GPP text once (clauses 5.3.1.2, 5.4.1.1, 5.4.1.2).

---

## 0. Ranked findings (actionable)

1. **Use the 5G NR rate-matching rules, but raise n_max from 10 to 12.** Do not pad to the next power of two and do
   not use our current N = 2048 for every format. The mother code is N = 2^n with n = max(min(n1, n2, n_max), 5).
   n1 = ceil(log2 E), lowered by one when E <= (9/8) 2^(ceil(log2 E) - 1) and K/E < 9/16. n2 = ceil(log2 8K).
   Use puncturing when K/E <= 7/16 and shortening otherwise. Freeze the pre-frozen set first, then fill the K
   information positions from the reliability order. For the five target formats this gives N = 4096 for DVB-RCS2
   IDs 13, 14 and 42, N = 1024 for ID 3 and N = 2048 for VDE-SAT Link 32 (table 1.6).
   ([Bioglio-Condo-Land](https://arxiv.org/abs/1804.04389), [Sionna](https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/polar/encoding.py))
2. **Shortening always removes the all-ones codeword, so PiCode breaks at DVB-RCS2 ID 14 (K/E = 0.505 > 7/16).**
   [derived] With x = u G_N in natural order, x_j is the XOR of all u_i whose index bits contain j's. Index N-1
   contains every j, so making any x_j a known zero forces u_{N-1} = 0. 08_parameters_results.md already states
   PiCode's assumption. There are three options: (a) use puncturing at ID 14 too, which breaks the 5G rule (the
   main session decides; the BLER cost must be measured); (b) keep shortening and run 4 phase branches in the
   final decodes; (c) keep shortening and accept the pi ambiguity, which raises the false-alarm count. Puncturing
   keeps the all-ones word, so IDs 13, 42, 3 and VDE are unaffected.
3. **Code alone: expect roughly 0 +- 0.5 dB vs a 16-state turbo code at K ~ 300-1500, so any large gain vs
   DVB-RCS2 must come from sync and pilot energy.** Coskun et al.: at (512, 256), CRC-16 polar with list 32 is "only
   marginally better" than binary LDPC / turbo, and list 1024 is needed to close the gap to the bounds. Niu et al.:
   at K = 400, L = 32, CRC-8, punctured polar "match or slightly beat" LTE turbo at R = 1/5-1/2, and gain 0.5-1 dB
   at N = 1024, R = 1/2, BLER 1e-4. DVB-RCS2 uses a 16-state turbo code, which is better than LTE's 8-state
   (~0.4 dB at (128, 64) per Coskun / Liva), and we use L = 8, not 32. **Measure it**: genie-sync CA-SCL-8 BLER at
   the exact (K, E) of ID 13 / 14 / 3 vs the TR 101 545-4 ideal-sync PER-1e-3 points already in the project
   (ID 13 -0.80 dB, ID 14 1.49 dB, ID 3 -0.27 dB, ID 4 1.92 dB Es/N0).
4. **N = 4096 costs ~2.2x per SC decode [derived]**: (N/2) log2 N = 24 576 vs 11 264 butterflies for N = 2048.
   This is a real MACs-per-core cost at IDs 13 / 14 / 42. The cheaper alternative (N = 2048 + 904 repeated bits at
   ID 13) goes against the 5G rule (E/2048 = 1.44 > 9/8). I found no published dB figure for it. If MACs matter,
   A/B it under genie sync (finding 3's experiment, same flagged code).
5. **Recalibrate the frozen-bit early stop (fz_stop / q_fix checkpoints) for rate-matched codes, and exclude
   pre-frozen leaves from its counts.** Punctured-induced frozen u's have ~0 LLR, which gives a constant ln 2
   penalty under every hypothesis. Shortened ones have LLR = +inf, which gives a 0 penalty under every hypothesis.
   Neither carries CFO information, but both enter the per-leaf average psn and shift the thresholds (section 4).

---

## 1. 5G NR polar rate matching (TS 38.212 5.3.1, 5.4.1), as needed here

### 1.1 Encoder convention: compatible with polar.py
NR encodes d = u G_N, G_N = F^{(x)n}, F = [[1,0],[1,1]], with no bit reversal [paper: Bioglio 2020 sec. II]. That is
exactly `polar.PolarCode.encode` (natural order, no bit reversal). So the NR interleaver and pre-freezing index
formulas apply to our u / x indices without any translation.

### 1.2 Mother code size [paper, code]
- n1 = ceil(log2 E) - 1 if E <= (9/8) 2^(ceil(log2 E) - 1) and K/E < 9/16, else ceil(log2 E). Sionna codes it this
  way. Bioglio states the same test as "fractional part of log2 E < 0.17", and log2(9/8) = 0.170 [derived].
- n2 = ceil(log2(8K)), which keeps the mother rate >= 1/8.
- n = max(min(n1, n2, n_max), n_min), n_min = 5, n_max = 9 (DL) / 10 (UL).
- **Our extension:** n_max = 12. NR stops at N = 1024 and instead segments UCI into two code blocks when A >= 1013,
  or A >= 360 and E >= 1088 ([MathWorks nrUCIEncode](https://www.mathworks.com/help/5g/ref/nruciencode.html),
  search snippet only). Segmenting ID 13 into 2 x (500 + CRC, E = 1476) is "NR-faithful". I do not recommend it:
  the codes are shorter, there are two CRCs, and every packet needs two successful decodes. The selection rules
  themselves do not depend on N ([Bioglio-Gabry-Land 2017](https://arxiv.org/abs/1701.06458)).

### 1.3 Sub-block interleaver (5.4.1.1) [paper, code]
Split the N coded bits d into 32 sub-blocks of B = N/32 bits. Output y_n = d_{J(n)}, with
J(n) = P(floor(32 n / N)) * B + (n mod B) and
P = [0, 1, 2, 4, 3, 5, 6, 7, 8, 16, 9, 17, 10, 18, 11, 19, 12, 20, 13, 21, 14, 22, 15, 23, 24, 25, 26, 28, 27, 29, 30, 31]
(Sionna, Table 5.4.1.1-1). This is a coarse (32-block) bit-reversal-like order. Bioglio-Gabry-Land use the exact
bit-reversal permutation for the same purpose.

### 1.4 Bit selection (5.4.1.2) and pre-freezing (5.3.1.2) [paper, code]
U = N - E.

| Case | Condition | Sent bits e_k (k = 0..E-1) | Pre-frozen u indices | Rx LLR of removed bits |
|---|---|---|---|---|
| Puncturing | E < N, K/E <= 7/16 | y_{k+U} (drop the first U) | J(0..U-1), plus u_0..u_T (below) | 0 |
| Shortening | E < N, K/E > 7/16 | y_k (drop the last U) | J(E..N-1) | +inf (bit = 0; our LLR = log P0/P1) |
| Repetition | E > N | y_{k mod N} | none | add the LLRs of all copies (MRC) [derived: optimal]; the MathWorks page says it "selects" the first N |

Extra freezing for puncturing: T + 1 = ceil(3N/4 - E/2) bits if E >= 3N/4, otherwise ceil(9N/16 - E/4) bits,
indices 0..T (Bioglio: Q2 = {0..T}, T = ceil(.) - 1). **Off-by-one:** Sionna's loop `for i in range(t)` freezes
only 0..T-1, one bit fewer than Bioglio's set. That bit is almost always frozen by reliability anyway, but follow
the standard text.
K is then filled with the K most reliable positions left after the pre-frozen set (Q3 in Bioglio). K includes the
CRC; NR also counts its 3 PC bits, which we do not use.
Puncturing vs shortening, why: punctured positions make low-index u's "incapable", so they must be frozen.
Shortened positions are known zeros, which forces the high-index u's to be frozen. Puncturing wins at low rate and
shortening at high rate. Bioglio-Gabry-Land Figs. 5-6 show only qualitatively that the wrong choice gives an error
floor at high rate (puncturing) or a loss at low rate (shortening). [Niu et al. 2023](https://arxiv.org/html/2303.14614v1)
state the same split: QUP for R <= 7/16, RQUS above.
The uplink triangular coded-bit interleaver (5.4.1.3, I_BIL) only matters for higher-order or non-Gray mappings.
Skip it for QPSK / BPSK in AWGN [derived].

### 1.5 Reliability sequence vs polar.py
polar.py builds the frozen set from the PW order, beta = 2^(1/4), for any power-of-two N
(`pw_reliability`). NR uses a fixed table of length 1024 (Q_0^{1023}, nested). Bioglio cites beta-expansion as one
of its origins, not as identical. Sionna ships the table (`generate_5g_ranking`). Recommendation:
- N = 1024 (ID 3): the NR table can be used for faithfulness. The difference to PW is a re-ordering of a few
  mid-reliability indices; I found no published dB figure for PW vs NR at L = 8.
- N = 2048 / 4096: there is no NR table, so keep PW, which is the same family. Optional check: a GA-at-design-SNR
  construction at N = 4096, under genie sync, at one SNR. I found no published PW-vs-GA comparison at N = 4096.
- In every case the pre-frozen set (1.4) must be removed before taking the top K. polar.py today takes
  `pw_reliability(N)[-K:]` with no exclusions, so this is the main code change.

### 1.6 The target (K, E) pairs [derived]
K = payload incl. the format's own CRC + our CRC-16. Alternative: use their CRC-32 as the CA-SCL check and drop
ours (K 16 bits smaller, 10 log10(K/(K-16)) = 0.07 dB at K = 1000 and 0.21 dB at K = 328 [derived]).

| Format | A (bits) | K = A + 16 | E (coded bits) | K/E | Mode | N | U = N - E | Extra frozen u_0..u_T | Mother K/N | E - K |
|---|---|---|---|---|---|---|---|---|---|---|
| RCS2 ID 13 (QPSK 1/3, 1476 sym) | 984 | 1000 | 2952 | 0.339 | puncture | 4096 | 1144 | 1566 (0..1565) | 0.244 | 1952 |
| RCS2 ID 42 (pi/2-BPSK 1/3, 2952 sym) | 984 | 1000 | 2952 | 0.339 | puncture | 4096 | 1144 | 1566 | 0.244 | 1952 |
| RCS2 ID 14 (QPSK 1/2, 1504 sym) | 1504 | 1520 | 3008 | 0.505 | **shorten** | 4096 | 1088 | none | 0.371 | 1488 |
| RCS2 ID 3 (QPSK 1/3, 456 sym) | 304 | 320 | 912 | 0.351 | puncture | 1024 | 112 | 312 (0..311) | 0.313 | 592 |
| VDE-SAT Link 32 (BPSK, SF 8) | 312 | 328 | 1269 | 0.258 | puncture | 2048 | 779 | 835 (0..834) | 0.160 | 941 |
| (ours now, 0.15) | 307 | 323 | 2048 | 0.158 | none | 2048 | 0 | - | 0.158 | 1725 |
| (ours now, 1/2) | 1024 | 1040 | 2048 | 0.508 | none | 2048 | 0 | - | 0.508 | 1008 |

Working: ID 13: 2952 > (9/8) 2048 = 2304, so n1 = 12; n2 = ceil(log2 8000) = 13; N = 4096. E < 3N/4 = 3072, so
ceil(2304 - 738) = 1566. ID 3: 912 > 576, so N = 1024; E >= 768, so ceil(768 - 456) = 312. VDE: 1269 > 1152, so
N = 2048; E < 1536, so ceil(1152 - 317.25) = 835. ID 14: 3008 > 2304, so N = 4096; K/E > 7/16, so shorten.
VDE E = 1269 is the turbo output including its 21 tail bits (M.2092 Table 4, as recorded in
`lit_vdesat_fullsystem.md`). A polar code needs no tail, so E = 1269 gives the same channel bits. E = 1248 would
match the code rate rather than the airtime. Use 1269.
ID 14 note: K/E = 0.505 is only 0.07 above the 7/16 = 0.4375 switch. Puncturing it instead (finding 2a) is
therefore a modest departure. Its BLER cost is unknown and must be measured.

### 1.7 Implementation checklist (for polar.py; the main session implements)
1. `PolarCode(N=None, A, crc_len, E)`: compute N (1.2, n_max = 12), J (1.3), the mode and pre-frozen set (1.4),
   then the info set = the top K of PW order excluding the pre-frozen set.
2. Tx: x = polar_transform(u); y = x[J]; e = y[U:] (puncture) / y[:E] (shorten) / y[k mod N] (repeat), then to
   QPSK / BPSK in order.
3. Rx: LLR_y = zeros(N) (puncture) / +BIG at y[E:] (shorten); place the received E LLRs; for repetition, sum;
   LLR_x[J] = LLR_y; decode as now.
4. Unit checks (cluster smoke slot, no local runs): (i) under shortening, x[J[E:]] == 0 for random data;
   (ii) noiseless round trip for every row of 1.6; (iii) N = 2048, E = 2048 must reproduce today's code
   bit-exactly (regression).
5. Rate-0 / Fast-SSC shortcuts still apply. The extra-frozen block u_0..u_T is contiguous and low-index, so it
   forms large rate-0 sub-trees, which makes the first part of an N = 4096 decode cheap [derived].

---

## 2. Expected loss of rate-matched polar codes vs the next power of two

- **No published dB number found for "rate-matched at E vs power-of-two at 2^n" under CA-SCL-8 at our sizes.**
  What exists:
  - [Stitched polar codes (arXiv 2511.19249, 2025)](https://arxiv.org/html/2511.19249v1): rate-matched (QUP / BRS)
    polar codes show a rise in the SNR needed at a fixed BLER just past each power of two, even at long lengths.
    Their stitched construction beats QUP / BRS "by up to 0.3 dB" (SC, R = 1/3 and 2/5, BLER 0.01). For SCL-8 +
    CRC-11 (N = 256-8192, R = 1/3, 2/5, 1/2) they give only qualitative statements. Reading: the sub-optimality
    of standard rate matching is at most ~0.3 dB (SC). [derived reading]
  - [Bioglio-Gabry-Land 2017](https://arxiv.org/abs/1701.06458): (320, 160), (160, 120), (160, 40), CRC-24, L = 32,
    QPSK AWGN. Bit-reversal puncturing / shortening match DE/GA-optimised sets. The figures carry the numbers; the
    text gives no dB values.
  - [Niu et al. 2023 survey](https://arxiv.org/html/2303.14614v1), Fig. 15: K = 400, mother N = 1024, QUP / RQUS,
    CA-SCL L = 32, CRC-8. No loss-vs-mother figure in the text.
- **The inherent cost vs a full power-of-two code is the rate / length difference, not the puncturing.** Example:
  ID 13 at E = 2952 is a rate-0.339 length-2952 code. That is better per info bit than our rate-0.15 length-2048
  code is per its own rate, and the right reference is a finite-length bound at (K, E). [derived] Recommend the
  main session plot the normal approximation (A16, Polyanskiy-Poor-Verdu) at each (K, E) next to the genie
  CA-SCL-8 curve. With well-designed rate matching, expect a gap of a few tenths of a dB more than at the power
  of two [unverified: only the 0.3 dB stitched result supports the size].

## 3. Polar CA-SCL vs turbo at short blocks (code-only gain)

| Source | Setting | Result |
|---|---|---|
| [Coskun et al. 2019, arXiv 1812.08562](https://arxiv.org/html/1812.08562v2) | (512, 256) R = 1/2, polar + CRC-16, bi-AWGN | L = 32 "only marginally better" than binary LDPC / turbo; L = 1024 needed to approach the bounds (text, no dB) |
| same | (128, 64) | LTE turbo ~0.4 dB worse than the best 16-state turbo at CER 1e-4; the 16-state turbo is ~0.4 dB from the RCB |
| [Niu et al. 2023](https://arxiv.org/html/2303.14614v1) | K = 400, N = 1024 mother, L = 32, CRC-8, vs LTE turbo (8-state, Log-MAP, 8 it.) | R = 1/5-1/2: polar matches or slightly beats turbo (0.5-1 dB at R = 1/5); R = 8/9: +1-1.2 dB |
| same, sec. 6.1 | N = 1024, R = 1/2, BLER 1e-4 | CRC-polar gains 0.5-1 dB over turbo / LDPC (list size not restated; L = 32 in their examples) |
| [Shirvanimoghaddam et al. 2019, arXiv 1802.09166](https://ar5iv.labs.arxiv.org/html/1802.09166) | N = 128, R = 1/2 | CA-polar SCL 0.5 dB from the normal approximation at 1e-4; LTE turbo "more than 1 dB" from the bound at short / moderate lengths |
| [Liva et al. 2016, arXiv 1610.00873](https://arxiv.org/abs/1610.00873) | (128, 64) | CA-polar L = 32 best of the iterative competitors down to 1e-6 |
| Sybis et al., VTC-Fall 2016 ([listing](https://nokia.com/bell-labs/publications-and-media/publications/channel-coding-for-ultra-reliable-low-latency-communication-in-5g-systems), 403 here) | URLLC, 40 and 200 bits | from search snippets only: polar / LDPC beat turbo at 40 bits, turbo better at 200 bits [unverified] |
| Niu, Chen, Lin, ICC 2013 (RCPP, QUP) | M = 512, R = 0.5, CA-SCL / SCS | "over 0.7 dB" gain at BLER 1e-4 (abstract snippet; versus what, not confirmed) [unverified] |

**Verdict [derived].** At K ~ 1000, R = 1/3, against DVB-RCS2's 16-state duo-binary turbo, CA-SCL-8 + CRC-16 is
probably within +-0.3 dB, and may be slightly worse at R = 1/3 because the 16-state turbo is strong there. The
evidence: published polar gains are vs LTE 8-state turbo and use L = 32, while ours uses L = 8. Against VDE-SAT's
LTE-like 8-state turbo at K = 312, R = 1/4, polar can be ~0.3-0.7 dB better. None of these comparisons uses our
exact (K, E), list size or CRC. Use them only to set expectations, then measure (finding 3).

## 4. What rate matching does to the blind receiver

- **Implicit pilot budget.** Only frozen bits that touch transmitted bits carry CFO information. The useful count
  is about E - K (1.6, last column). ID 13: 1952 of 2952 coded bits (0.66). Ours at 0.15: 1725 / 2048 (0.84).
  ID 14: 1488 / 3008 (0.49), vs ours at 1/2: 1008 / 2048 (0.49). ID 3: 592 / 912. VDE: 941 / 1269. [derived] So
  the per-bit frozen density at the native formats is similar to our current rates at the matching code rate.
  The total grows with E. The 4th-power fast path gains directly from the extra symbols (1476 vs 1024 at ID 13).
- **Pre-frozen bits carry nothing.** Punctured-induced (incapable) u's add ~ln 2 to every hypothesis's metric.
  Shortened ones (LLR = +inf) add 0. Both are hypothesis-independent. Exclude them from the fz_stop / fz_q leaf
  counts and from `psn`, or the per-leaf averages are diluted and the q_fix / spec11 thresholds move. Recalibrate
  the early-stop thresholds per format in any case: N, the frozen pattern and the decoding order all change.
- **Early checkpoints see the extra-frozen block first.** Under puncturing, u_0..u_T (1566 of 4096 at ID 13) are
  decoded first and are the weakest channels. The earliest checkpoint will discriminate less than at N = 2048
  [derived]. Move the first checkpoint later (as a fraction of the useful frozen bits) and test.
- **PiCode / phase.** Shortening breaks the all-ones codeword (finding 2). Puncturing keeps it (row N-1 restricted
  to the sent positions is still all ones), so PiCode and the 2-branch phase logic stay valid at IDs 13, 42, 3 and
  VDE.
- **Re-encoding check (RHO_N).** Correlate only over the E transmitted bits. Re-encode and then rate-match the
  same way; never correlate over punctured or shortened positions.
- **Cost.** N = 4096 gives ~2.18x MACs per SC decode [derived]. ID 3 (N = 1024) gives 0.45x, and VDE (N = 2048)
  1.0x.

---

## 5. Per-source table

| # | Title | Year | Link | Relevance | Method | Setting | Numbers |
|---|---|---|---|---|---|---|---|
| 1 | 3GPP TS 38.212 (ETSI TS 138 212 V15.5.0) | 2019 | [ETSI](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/15.05.00_60/ts_138212v150500p.pdf) | high: the rules themselves | NR polar coding and rate matching | N <= 1024, CRC-6/11/24 | **not readable here (binary PDF)**; rules taken from #2 and #4 |
| 2 | Bioglio, Condo, Land, Design of polar codes in 5G New Radio (IEEE COMST) | 2018/2021 | [arXiv 1804.04389](https://arxiv.org/abs/1804.04389) | high: full NR chain | tutorial of 38.212 | NR control channels, SCL-8 | n rule (0.17), 7/16, Q1/Q2/Q3 formulas; Fig. 13 has no numbers in the text |
| 3 | Bioglio, Gabry, Land, Low-complexity puncturing and shortening of polar codes | 2017 | [arXiv 1701.06458](https://arxiv.org/abs/1701.06458) | high: N-agnostic rule | bit-reversal puncture / shorten sets + reliability order | (320,160), (160,120), (160,40), CRC-24, L = 32, QPSK AWGN | matches DE/GA sets; qualitative only in the text |
| 4 | NVIDIA Sionna Polar5GEncoder (code) | current | [GitHub](https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/polar/encoding.py) | high: reference implementation | 38.212 in Python | K <= 1013, E <= 1088, no segmentation | P table, 9/8 rule, pre-freezing (off-by-one vs #2) |
| 5 | MathWorks, 5G NR polar coding example | current | [page](https://www.mathworks.com/help/5g/gs/polar-coding.html) | medium: Rx conventions | rate recovery | K = 54, E = 124, L = 8 | punctured LLR 0, shortened large; no BLER numbers |
| 6 | MathWorks nrUCIEncode | current | [page](https://www.mathworks.com/help/5g/ref/nruciencode.html) | low | UCI segmentation | - | A >= 1013, or A >= 360 and E >= 1088 (search snippet only) |
| 7 | Niu et al., A golden decade of polar codes | 2023 | [arXiv 2303.14614](https://arxiv.org/html/2303.14614v1) | medium: polar vs LTE turbo | survey | K = 400, N = 1024, L = 32, CRC-8 | R 1/5-1/2 ~ turbo or better (0.5-1 dB at 1/5); N = 1024 R = 1/2: 0.5-1 dB at 1e-4; first 100k of 128k chars read |
| 8 | Coskun et al., Efficient error-correcting codes in the short blocklength regime | 2019 | [arXiv 1812.08562](https://arxiv.org/html/1812.08562v2) | high: closest to our K | survey with simulations | (128,64), (512,256) | polar CRC-16 L = 32 ~ turbo at (512,256); LTE turbo -0.4 dB vs 16-state at (128,64) |
| 9 | Liva, Gaudio, Ninacs, Jerkovits, Code design for short blocks | 2016 | [arXiv 1610.00873](https://arxiv.org/abs/1610.00873) | low: k = 64 only | survey | (128,64) | 16-state turbo 0.4 dB from the RCB at 1e-4 |
| 10 | Shirvanimoghaddam et al., Short block-length codes for URLLC | 2019 | [arXiv 1802.09166](https://ar5iv.labs.arxiv.org/html/1802.09166) | low-medium | survey | N = 128; K = 40, 1000 curves | CA-polar 0.5 dB from the NA; turbo > 1 dB |
| 11 | Stitched polar codes | 2025 | [arXiv 2511.19249](https://arxiv.org/html/2511.19249v1) | medium: size of the rate-matching loss | new length-flexible construction | N = 256-8192, R = 1/3, 2/5, 1/2, SC and SCL-8 CRC-11, BLER 0.01 | up to 0.3 dB better than QUP / BRS (SC); authors not captured |
| 12 | Sybis et al., Channel coding for URLLC in 5G | 2016 | [listing](https://nokia.com/bell-labs/publications-and-media/publications/channel-coding-for-ultra-reliable-low-latency-communication-in-5g-systems) | low | comparison | 40 / 200 bits | snippet only (HTTP 403) |
| 13 | Niu, Chen, Lin, Beyond turbo codes: rate-compatible punctured polar codes (ICC) | 2013 | [journal version arXiv 1612.01352](https://arxiv.org/abs/1612.01352) | low-medium | QUP puncturing | M = 512, R = 0.5 | "> 0.7 dB" at 1e-4 (snippet) |
| 14 | Miloslavskaya, Shortened polar codes (IEEE T-IT 61(9)) | 2015 | [record](https://rune.une.edu.au/web/handle/1959.11/64594) | low | shortening-pattern search | long codes | beats LDPC (snippet only) |

## 6. Per-component verdict

| Component | Status |
|---|---|
| Encoder order (natural, no bit reversal) | **we already use it** (`polar.polar_transform`), NR-compatible |
| Reliability order | **we already use it** (PW, beta = 2^(1/4)); the NR table is optional at N = 1024 |
| Rate matching (sub-block interleaver, puncture / shorten / repeat, pre-freezing) | **we are behind**: none exists; implement 1.7. Cost: 1-2 days of code, no runtime cost beyond the N change |
| Mother code length | **behind**: fixed N = 2048; use the 1.2 rule with n_max = 12 (IDs 13 / 14 / 42 need N = 4096, ~2.2x MACs per decode) |
| Segmentation (NR UCI) | **not applicable**: we lift n_max instead |
| Coded-bit interleaver I_BIL | **not applicable** (BPSK / QPSK, AWGN) |
| PiCode under shortening | **behind / decision needed** (finding 2) |
| Early stop / fz_stop under rate matching | **must be recalibrated**; exclude pre-frozen leaves (section 4) |

## Reference entries (for the coordinator to merge; I did NOT edit REFERENCES.md)

Merged into REFERENCES.md 2026-11-17 and renumbered (scout's C95-C108 -> C101-C114 in order; polar-code papers moved
to section A as A17-A22; TS 38.212 merged into the existing A7; unused: C101, C102, C103, C107, C111, C113, C114).
Citations below use the registry numbers.

- **A7 (merged into the existing A7). 3GPP TS 38.212, NR multiplexing and channel coding, clauses 5.3.1, 5.4.1,
  6.3.2.2** (ETSI TS 138 212 V15.5.0). Link:
  https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/15.05.00_60/ts_138212v150500p.pdf -
  Type: standard - Read depth: NOT read (binary PDF); content via A17 / C104. Note: A7 held the CRC use only before. Used in: 2026-11-17 lit_polar_ratematch.md, rate-matching rules for the native formats (proposed,
  not implemented).
- **A17 (polar). V. Bioglio, C. Condo, I. Land, "Design of polar codes in 5G New Radio", IEEE Commun. Surveys &
  Tutorials 2021, arXiv 1804.04389.** Link: https://arxiv.org/abs/1804.04389 - Type: paper - Read depth: full text
  (ar5iv). Took: the mother-length rule, 7/16 switch and pre-freezing formulas. Used in: 2026-11-17
  lit_polar_ratematch.md sections 1.2-1.4, 1.6 (proposed).
- **A18 (polar). V. Bioglio, F. Gabry, I. Land, "Low-complexity puncturing and shortening of polar codes", IEEE
  WCNC Workshops 2017, arXiv 1701.06458.** Link: https://arxiv.org/abs/1701.06458 - Type: paper - Read depth: full
  text (ar5iv). Took: N-agnostic bit-reversal puncture / shorten rule (justifies n_max = 12). Used in: 2026-11-17
  lit_polar_ratematch.md 1.2, 1.4 (proposed).
- **C104. NVIDIA Sionna, `Polar5GEncoder` source.** Link:
  https://raw.githubusercontent.com/NVlabs/sionna/main/src/sionna/phy/fec/polar/encoding.py - Type: code - Read
  depth: code read. Took: the 32-entry P table, 9/8 rule; off-by-one in the extra freezing noted. Used in:
  2026-11-17 lit_polar_ratematch.md 1.3-1.4 (proposed).
- **C105. MathWorks, "5G New Radio polar coding" example.** Link: https://www.mathworks.com/help/5g/gs/polar-coding.html
  - Type: vendor doc - Read depth: page. Took: rate-recovery LLR conventions. Used in: 2026-11-17
  lit_polar_ratematch.md 1.4.
- **C106. MathWorks, nrUCIEncode.** Link: https://www.mathworks.com/help/5g/ref/nruciencode.html - Type: vendor doc
  - Read depth: search snippet. Took: the NR segmentation condition (not adopted). Used in: 2026-11-17
  lit_polar_ratematch.md 1.2.
- **A19 (polar). K. Niu et al., "A golden decade of polar codes: from basic principle to 5G applications", 2023,
  arXiv 2303.14614.** Link: https://arxiv.org/abs/2303.14614 - Type: paper - Read depth: ~78 % of html. Took:
  polar vs LTE turbo numbers (section 3). Used in: 2026-11-17 lit_polar_ratematch.md 3.
- **C108 (polar). B. Coskun et al., "Efficient error-correcting codes in the short blocklength regime", Physical
  Communication 2019, arXiv 1812.08562.** Link: https://arxiv.org/abs/1812.08562 - Type: paper - Read depth: ~93 %
  of html. Took: (512,256) CRC-16 L = 32 ~ turbo; LTE vs 16-state turbo 0.4 dB. Used in: 2026-11-17
  lit_polar_ratematch.md 3.
- **C109 (polar). G. Liva, L. Gaudio, T. Ninacs, T. Jerkovits, "Code design for short blocks: a survey", 2016,
  arXiv 1610.00873.** Link: https://arxiv.org/abs/1610.00873 - Type: paper - Read depth: html. Used in:
  2026-11-17 lit_polar_ratematch.md 3 (reference only).
- **C110 (polar). M. Shirvanimoghaddam et al., "Short block-length codes for ultra-reliable low latency
  communications", IEEE Commun. Mag. 2019, arXiv 1802.09166.** Link: https://arxiv.org/abs/1802.09166 - Type: paper
  - Read depth: html. Used in: 2026-11-17 lit_polar_ratematch.md 3 (reference only).
- **A20 (polar). "Stitched polar codes", 2025, arXiv 2511.19249** (authors not captured). Link:
  https://arxiv.org/abs/2511.19249 - Type: paper - Read depth: html, results section text only. Took: <= 0.3 dB
  rate-matching sub-optimality (SC). Used in: 2026-11-17 lit_polar_ratematch.md 2.
- **C112. M. Sybis, K. Wesolowski, K. Jayasinghe, V. Venkatasubramanian, V. Vukadinovic, "Channel coding for
  ultra-reliable low-latency communication in 5G systems", IEEE VTC-Fall 2016.** Link:
  https://nokia.com/bell-labs/publications-and-media/publications/channel-coding-for-ultra-reliable-low-latency-communication-in-5g-systems
  - Type: paper - Read depth: search snippet only (HTTP 403). Used in: 2026-11-17 lit_polar_ratematch.md 3
  (unverified).
- **A21 (polar). K. Niu, K. Chen, J.-R. Lin, "Beyond turbo codes: rate-compatible punctured polar codes", IEEE ICC
  2013, pp. 3423-3427.** Link: https://arxiv.org/abs/1612.01352 (journal follow-up) - Type: paper - Read depth:
  abstract snippet. Used in: 2026-11-17 lit_polar_ratematch.md 3 (unverified).
- **A22 (polar). V. Miloslavskaya, "Shortened polar codes", IEEE T-IT 61(9), 4852-4865, 2015.** Link:
  https://rune.une.edu.au/web/handle/1959.11/64594 - Type: paper - Read depth: snippet. Used in: 2026-11-17
  lit_polar_ratematch.md table 5 (reference only).
- Existing entries to extend: **A6** (PW): "2026-11-17 lit_polar_ratematch.md: PW kept for N = 2048 / 4096 rate-matched
  codes (proposed)". **A7** (TS 38.212): "2026-11-17 lit_polar_ratematch.md: rate-matching clauses proposed (see the
  A7 entry above)". **A16** (PPV): "2026-11-17 lit_polar_ratematch.md: normal approximation at each native (K, E) recommended
  as reference".
