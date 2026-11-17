# Full-system comparison: blind receiver vs DVB-RCS2 and VDE-SAT

State: 2026-11-17. Everything below was checked against the code in this folder and the result files in
[results/](results/). Where a document and the code disagree, the code is described and the difference is noted.
Statements that could not be confirmed from code or result files are marked **(unverified)**.

## 1. Overview

**Goal.** Show that our blind receiver can carry the same payload as a real, deployed burst system with at most the
same Eb/N0, while sending no known symbols at all. Blind means:
- no pilots, preamble or unique word;
- CFO and carrier phase estimated blind;
- a polar code decoded by CRC-aided list decoding (CA-SCL, list 8), with a CRC-32 and a re-encoding check.

The competitors are complete standard systems: their FEC, burst layout, known symbols, CRC and a data-aided (DA)
synchroniser. Their known symbols cost energy, and that energy is charged to them.

**Reference systems.**
- **DVB-RCS2** (ETSI EN 301 545-2 V1.3.1, TC-LM return link) waveform IDs 3, 13, 14 and 42 ([rcs2.py](rcs2.py),
  [turbo_db.py](turbo_db.py)).
- **VDE-SAT Link 32** (ITU-R M.2092-2) ([vde.py](vde.py), [turbo_vde.py](turbo_vde.py)).

**Equal payload.** Blind carries the competitor's payload bits A plus its own CRC-32, rate-matched to the
competitor's number of coded data bits E. Blind therefore sends exactly the competitor's data symbols and drops the
known ones.

**Axes.** Every curve is shown on three axes:

| Axis | Definition |
|---|---|
| SNR | Es/N0 per transmitted symbol (VDE: per despread symbol, the chips run at Es/N0 - 10 log10 8) |
| Eb/N0, known symbols charged (main axis) | Eb/N0 = Es/N0 + 10 log10(L_burst / A), where L_burst = every symbol sent (data + known) and A = payload bits (CRC not counted) |
| Eb/N0, known symbols free | the same with L_burst replaced by the data symbols only (the competitor's pilots cost nothing) |

The offsets are in section 5.2.

**Channel (all systems).** Every simulation uses the full Tx/Rx chain of [../txrx_chain.py](../txrx_chain.py):
1. upsample by SPS = 8;
2. RRC transmit filter with a span of 10 symbols ([../config.py](../config.py));
3. CFO applied per sample;
4. AWGN;
5. matched RRC filter;
6. remove the filter delay and downsample.

| System | Roll-off used in the code |
|---|---|
| DVB-RCS2 | 0.20 (`rcs2.ROLLOFF`, EN cl. 7.3.7.1.1) |
| VDE-SAT reference | 0.25 (`LINKS[32]["beta"]`) |
| Blind, all formats | 0.20 (`run_polar_genie.ROLLOFF`, default `--beta`); the blind VDE runs did **not** pass `--beta 0.25` (see 9) |

- The CFO f is uniform in [-0.03, +0.03] cycles per symbol (normalised to the symbol rate) and the phase is uniform
  in [0, 2 pi), drawn per packet.
- Timing and burst position are **known** for every receiver. No timing or burst detection is simulated. The known
  symbols of the competitors serve only CFO, phase and N0 estimation. In a real system they would also give timing.

## 2. DVB-RCS2 (TC-LM return link)

### 2.1 Waveforms (EN 301 545-2 Annex A Table A-1, `rcs2.WAVEFORMS`)

All four IDs carry a CRC-32. The code asserts every burst length from its layout.

| ID | Mod. | Rate | Payload A + CRC | Turbo couples N | Coded bits | Data symbols | Preamble / pilots / postamble | Pilot period | Burst L | Known share |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | QPSK | 1/3 | 272 + 32 | 152 | 912 | 456 | 27 / 26 / 27 | 18 | 536 | 80 (15 %) |
| 13 | QPSK | 1/3 | 952 + 32 | 492 | 2952 | 1476 | 32 / 77 / 31 | 20 | 1616 | 140 (8.7 %) |
| 14 | QPSK | 1/2 | 1472 + 32 | 752 | 3008 | 1504 | 25 / 62 / 25 | 25 | 1616 | 112 (6.9 %) |
| 42 | pi/2-BPSK | 1/3 | 952 + 32 | 492 | 2952 | 2952 | 65 / 155 / 64 | 20 | 3236 | 284 (8.8 %) |

**Transmitter** (`rcs2.tx`):
1. Energy dispersal of the PDU: PRBS 1 + x^14 + x^15, init `100101010000000`, reset per burst.
2. CRC-32/MPEG-2 over the scrambled PDU (poly 0x04C11DB7, init all ones, no reflection).
3. Duo-binary turbo encoding.
4. Symbol stream: A0 B0 A1 B1 ... followed by the parity Z1_0 Z2_0 Z1_1 ...
5. Mapping: Gray QPSK, or pi/2-BPSK s(n) = (1 - 2b) e^{j(pi n/2 + pi/4)} with n counted from the first preamble symbol.

**Known symbols.**
- The unique word (UW) hex strings come from Table A-1.
- Pilots are single symbols. The first lies one pilot period after the last preamble symbol, at position
  Lpre - 1 + kP. Every pilot block repeats the same symbol.

### 2.2 Turbo code (`turbo_db.py`, EN cl. 7.3.5.1)

**Code.**
- 16-state duo-binary circular RSC ("Turbo-Phi"). Each trellis step takes one couple (A, B).
- Constituent taps are AFF3CT's `Encoder_RSC_DB`.
- Circular (tail-biting) termination: pre-encode from state 0, then restart from Sc = CIRC[N mod 15 - 1][S_N^0]. The
  self-test rebuilds the circulation table over GF(2).
- Interleaver:
  - level 1 swaps (A, B) on alternate couples;
  - level 2 is the ARP Pi(j) = (P j + Q(j mod 4) + 3) mod N, with (P, Q) = (17, (9,5,14,1)) for ID 3,
    (31, (0,3,1,0)) for IDs 13 and 42, and (37, (1,3,4,2)) for ID 14.
  - The default reading is `'aff3ct'` (the one behind AFF3CT's published curves). Two literal EN readings are kept as
    options.
- Puncturing: rate 1/3 keeps every Y and W; rate 1/2 (ID 14) keeps every Y and no W (`ypat "1"`, `wpat "0"`).

**Decoder.**
- Log-domain BCJR on 4-ary couple symbols, max-log-MAP, 8 iterations.
- Extrinsic scaling `'adaptive'` (AFF3CT ADAPTIVE): 0.5 in iteration 1, then 0.85.
- The circular trellis passes state metrics between iterations.
- **No early stop** in the competitor runs (`early_stop false` in every `da_fs-q*` part). The CRC is checked after
  every iteration for logging only. TR 101 545-4 cl. 6.3.2 uses 0.7 except in the last iteration; that setting is
  available as `--sf 0.7`.

### 2.3 DA synchroniser (`da_sync.py`, used by `run_fullsys_da.py`)

The standard leaves the estimator open (TR 101 545-4). We use the strongest reasonable DA ML estimator for |f| <= 0.03.

**Model.** At the known positions n_k:

$$z_k = r[n_k]\,s_k^* = g\,e^{j2\pi f n_k} + w_k,\qquad \hat f = \arg\max_f \Lambda(f),\quad \Lambda(f) = \Big|\sum_k z_k e^{-j2\pi f n_k}\Big|^2 .$$

**Steps.**
1. Place z on the burst span (zeros at the data). Take |FFT| of size nfft = the smallest power of 2 >= 4 x span:
   4096 for ID 3, 8192 for IDs 13 and 14, 16384 for ID 42.
2. Find local maxima inside |f| <= 0.03 + 2/span (+1 bin). Refine the 6 highest (`REFINE`): parabolic interpolation,
   then 3 Newton steps on the exact Lambda.
3. Rank the maxima by Lambda and merge duplicates closer than 0.5/span.
4. Complex gain g = sum z_k e^{-j2 pi f n_k} / Nk. N0 from the residual: sum |z - g e^{j2 pi f n}|^2 / (Nk - 1.5).
5. Correct: y = r e^{-j2 pi f n} / g. LLR noise N0 / |g|^2 (`--n0 est`, a real receiver).

**Variant used: `strong`.** The top 3 candidates (`TOP_M = 3`) are tried in Lambda order. Each costs a full turbo
decode, and the receiver stops at the first CRC pass. This is how the pilot layout's side lobes and aliases are caught.

Decision-directed refinement exists (`--dd-iters`) but is off: neither standard specifies it.

**MAC counting** (`costmodel.da_ops` / `da_crit`, same op unit as everything else):

| Part | Ops |
|---|---|
| FFT | 5 n log2 n |
| Strip | 2 Nk |
| Search | 5 per bin |
| Newton step | 22 Nk + 10 |
| Lambda | 14 Nk |
| Gain and N0 | 17 Nk + 20 |
| De-rotation | 12 per data symbol |

- The charged cost is the **lean** synchroniser: one maximum refined, nfft = power of 2 >= 2 x span. An extra
  candidate costs `per_cand` + `refine_one`. The bigger synchroniser that actually runs is logged as the upper bracket
  (`*_upper_*`).
- Example, ID 13: the lean first pass is 278,678 ops (8,845 per core). The upper bracket is 622,913 (20,096 per core).

### 2.4 Validation of our DVB-RCS2 implementation (ideal sync)

Targets: TR 101 545-4 Tables 10.5 / 10.6 / 10.8 (`rcs2.REF_PER`) and AFF3CT's DVB-RCS2 reference FER curves
(`rcs2.REF_AFF3CT`). Plot: [fullsys_refs.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/BLER/fullsys_refs.png).

| Check | Result (results/rcs2_*.json) | Reference |
|---|---|---|
| ID 13 (`fs-rcs2v13`, `v13b`) | 1.5e-3 at -0.80 dB, 6.3e-5 at -0.60, 1.2e-5 at -0.51 (8.2 M packets) | -0.80 / -0.51 dB at 1e-3 / 1e-5 |
| ID 14 (`fs-rcs2v14`) | 1.22e-3 at 1.49 dB, 2.4e-5 at 1.69 | 1.49 / 1.71 |
| ID 3 (`fs-q3ti`) | 1.7e-3 at -0.27, 2.7e-4 at -0.07, 2.7e-5 at 0.13 | -0.27 / 0.22 (ours ~0.05-0.1 dB worse at 1e-3) |
| ID 42 (`fs-q42ti`) | 1.6e-3 at -3.81, 5e-5 at -3.61 | -3.81 / -3.52 (ours ~0.05 dB worse at 1e-3) |
| AFF3CT N 3008 (the ID 14 code, early stop as AFF3CT, `fs-rcs2a3008`, `a3008b`) | 9.1e-4 at AFF3CT Eb/N0 1.6 dB, 1.7e-5 at 1.8 | 5.9e-4 / 9.2e-6 (ours ~0.03-0.05 dB right of it) |

All four IDs land within the +-0.2 dB pass rule of [expected_fullsys.md](../BLIND_IMPLEMENTATION/testing/results/expected_fullsys.md).
A bit-exact check of encoder, interleaver and CRC against AFF3CT test vectors is coded
([compare_aff3ct.py](compare_aff3ct.py), [aff3ct_tools/](aff3ct_tools/)), but no vectors are in
`results/aff3ct_vectors/` locally: **its result is (unverified) / not run**.

## 3. VDE-SAT Link 32 (ITU-R M.2092-2, `vde.LINKS[32]`, "SAT-MCS-0.50-2")

### 3.1 Burst

| Item | Value in the code |
|---|---|
| Payload | 280 bits + one CRC-32 per burst (poly 0x04C11DB7, init all ones, MSB first) -> k = 312 turbo input bits |
| FEC | turbo rate 1/4: puncturing pattern "2" (4 bits per data clock) + tail pattern "2e" (21 bits) -> 312 x 4 + 21 = 1269 channel bits |
| Scrambler | 1 + x^-14 + x^-15, seed `100101010000000`, per burst |
| Channel interleaver | Table 63 block, M 27 x N 47 (= 1269) |
| Modulation | BPSK (bit 1 -> +1) |
| Spreading | every burst bit x 8 Gold chips (Table 62 SS0, period 2047) |
| Burst | 1641 symbols = 1269 data + 4 syncwords x 48 = 192 (at 0, 531, 1062, 1593; the last ends the burst) + 3 x 60 = 180 single pilots (bit 1, every d_p = 8 symbols) |
| Known symbols | 372 = 23 % of the burst |
| Design point | Table 11: Es/N0 -4.5 dB per despread symbol (the PER is not stated in M.2092) |

Ramps and guard time are not transmitted (assumption A10). Every layout and table-reading assumption is listed in
`vde.ASSUMPTIONS` (A1-A13).

### 3.2 Turbo code and decoder (`turbo_vde.py`)

**Code.**
- 8-state, two-parity RSC: G(D) = [1, n0/d, n1/d] with d = 1 + D^2 + D^3, n0 = 1 + D + D^3, n1 = 1 + D + D^2 + D^3.
  This is the 3GPP2 / DVB-SH family.
- Terminated with 3 tail clocks per constituent.
- Interleaver: CCSDS law with k1 = 2, k2 = 156 and the Link 32 primes.

**Decoder.**
- **log-MAP, 8 iterations**, with a CRC early stop after every full iteration from iteration 1. This is what the
  competitor runs used (`--algo logmap`).
- `run_vde.py` and `run_fullsys_da.py` default to max-log x 0.75. log-MAP has to be given explicitly.

### 3.3 DA synchroniser and costs

**Synchroniser.**
- The CFO is f per symbol, i.e. f/8 per chip. The chips are despread first; the loss is <= 0.0125 dB at 0.03
  (`da_sync.despread_loss_db`).
- Then the estimator of 2.3 runs on the 372 known symbols (span 1641, nfft 8192, lean costing 4096). Variant
  `strong` with top 3.

**Costs.**
- Despreading: 2 ops per chip, once per burst (26,256 ops, 824 per core).
- LLR scaling: 1 op per channel bit per decode attempt.
- Turbo decode: `costmodel.turbo_ops` / `crit_turbo` (S = 8, log-MAP 177 ops per SISO step).
- Lean sync: 299,162 ops (9,483 per core).

### 3.4 Validation

| Check | Result | Reference |
|---|---|---|
| 88-bit QPSK rate 1/4 pseudo-link (`fs-vdev88`) | 9.5e-3 at -1.5 dB, 1.45e-3 at -1.0 (from expected_fullsys.md) | M.2435 Fig. 11: 1e-2 at -1.5 dB (ours 0.05-0.1 dB better) |
| Link 32, ideal sync, log-MAP (`fs-v32a`, `v32lo`) | 4.4e-3 at -5.0 dB, 1.6e-4 at -4.5, 6.7e-6 at -4.0 | design point -4.5 dB (PER unstated) |

M.2435 does not state its interleaver, so the 88-bit check uses the M.2092 CCSDS law. The check is approximate.

## 4. The blind counterpart per format

### 4.1 Formats (`run_polar_genie.FMTS`, [blind_fmt.py](blind_fmt.py), [polar_rm.py](polar_rm.py), [polar_design.py](polar_design.py))

| Format key | Competitor | A + CRC | E | Mother N | Rate matching | Design (final runs) | Modulation, symbols | Phase handling |
|---|---|---|---|---|---|---|---|---|
| `id3` | ID 3 | 272 + 32 | 912 | 1024 | puncture (U 112) | GA at 0.0 dB | QPSK, 456 | PiCode (pi), pi/2 branches by the interleaver |
| `id13` | ID 13 | 952 + 32 | 2952 | 4096 | puncture (U 1144) | GA at -0.5 dB | QPSK, 1476 | as ID 3 |
| `id14s` | ID 14 | 1472 + 32 | 3008 | 4096 | **shorten** (U 1088, K/E > 7/16) | GA at 1.8 dB | QPSK, 1504 | no PiCode (no all-ones codeword): 4 pi/2 branches (`nopi`) |
| `id42b` | ID 42 | 952 + 32 | 2952 | 4096 | puncture | GA at -3.5 dB | pi/2-BPSK, 2952 | de-rotated to virtual QPSK; line and phase mod pi from r^2 (`bpsk_sq`), PiCode for pi |
| `vde32` | VDE Link 32 | 280 + 32 | 1269 | 2048 | puncture (U 779) | **PW** (not GA, see 9) | BPSK, 1269, no spreading | `bpsk_sq` as ID 42 |

**Rate matching** (NR TS 38.212 style, `polar_rm.rm_plan`):
- Mother length: the 9/8 rule, n_max raised to 12 (N <= 4096), and a mother rate of at least 1/8.
- 32-sub-block interleaver J.
- Mode: puncture if K/E <= 7/16, else shorten.
- Puncturing pre-freezes the removed positions plus the low block u_0 ... u_{t-1} (38.212 rule).
- Rate recovery: punctured LLR = 0, shortened LLR = +1e4 (known zero).

**Construction.**
- `pw` = our PW order (beta = 2^(1/4)). It ignores the rate matching.
- `ga` = Gaussian approximation (Trifonov's two-piece phi) over the rate-matched channel at a design Es/N0. It knows
  which bits are punctured or shortened.
- GA gained 0.35-0.4 dB over PW at ID 13 (genie sync, [expected_fullsys.md](../BLIND_IMPLEMENTATION/testing/results/expected_fullsys.md)).

**Codes and interleaver.**
- CRC-32 0x04C11DB7 (init 0) and CA-SCL list 8 for every format.
- Channel interleaver: for QPSK, a fixed random permutation `rng(12345).permutation(E)` of the E sent bits. Without
  it, a pi/2 rotation maps codewords to codewords and about a third of the packets fail (README "The bit interleaver
  is essential"). BPSK and pi/2-BPSK use none.

**Re-encoding threshold.** The table is `--rho scaled`: the native RHO_N table of the rate profile, rescaled to
n_sym (`blind_fmt.rho_table`). The code calls it **provisional, not calibrated for these formats**.

### 4.2 Receiver profile and pipeline

[run_blind_fs.py](run_blind_fs.py) runs `small_rx.small_receive` inside a `BlindFormat` context. The context
rescales N, n_sym, E, the MAC model, the grid step (1.5e-4 x 512 / n_sym: the same phase drift per cell as the native
packet) and the FFT size. Every modulation is presented to the receiver as "virtual QPSK".

| Format | Rate profile | Adopted receiver (`BL`) | Standard MACs per core |
|---|---|---|---|
| ID 3, 13, 42 | 2/5 | `base25_qfix_fzs` | `c_d4a` |
| ID 14 | 1/2 | `base2_qfix_fzs` | `c_d4a` |
| VDE 32 | 0.15 (= the 1/10 settings) | `testing_s11g` | `c_hd4a` |

**Pipeline** (details in the blind docs, not repeated here):
1. **Coarse estimate**: power-law FFT. QPSK uses -r^4. (pi/2-)BPSK uses the square, -j r^2 (line at 2f, phase mod
   pi). See [02_fast_path.md](../BLIND_IMPLEMENTATION/02_fast_path.md).
2. **Fast path**: one decode at the coarse estimate. In `testing_s11g` it runs only above 0 dB (`s0_snr 0.5`), so it
   is off at every VDE operating point.
3. **Search over CFO grid x phase hypotheses** with partial list-1 path metrics to checkpoints and a robust z-test
   ([03_path_metric.md](../BLIND_IMPLEMENTATION/03_path_metric.md), [04_search.md](../BLIND_IMPLEMENTATION/04_search.md)).
   The **checkpoint NN** ranks every cell at its checkpoint and keeps a shortlist (cumulative probability 1 - ck_keep,
   at least ck_min cells).
4. **Final candidates**: refinement, CA-SCL-8 (joint list decoding at 2/5, 1/2), code-aided retry and rescue
   ([05_decoding.md](../BLIND_IMPLEMENTATION/05_decoding.md)). **F5** early stop: a CA-SCL decode stops when, after a
   share q of the frozen leaves, the frozen-only penalty per leaf of every list path exceeds t (05_decoding.md 5.8).
5. **Acceptance**: CRC-32 (with PiCode's pi complement, except under shortening) and the re-encoding correlation over
   the E sent bits ([06_acceptance.md](../BLIND_IMPLEMENTATION/06_acceptance.md)).

Parameters per rate: [08_parameters_results.md](../BLIND_IMPLEMENTATION/08_parameters_results.md).

### 4.3 Tuned settings in the final runs (read from the `fs-g*` / `fs-h*` / `fs-gv32*` part metadata)

| Format | F5 `--fzstop` (q, t) | Checkpoint NN | Other |
|---|---|---|---|
| ID 13 | 0.6, 0.80 | `--cknn fmt`: retrained on ID 13 packets (c 3 = 1/4) | |
| ID 42 | 0.9, 0.75 | own NN (c 3) | |
| ID 14 | 0.7, 0.78 | own NN (c 2 = 3/16) | |
| ID 3 | **off**: `base25_qfix_fzs` runs with its F5 disabled | own NN (c 3) | |
| VDE 32 | off (none in the profile) | own NN (c 3 = 1/4); `--cknn fmt` turns the coarse start off | **spec11 of `testing_s11g` is not active** |

All final runs use `--spec off`, `--rho scaled`, `--cfo-max 0.03` and `--beta 0.2`.

- The NNs are trained by [ck_nn_fs.py](ck_nn_fs.py) on the format's own search packets. The models are saved as
  `small_cfo/blind/models/ck_nn_fs_<fmt>_c<c>.npz`.
- **VDE final receiver = jointly tuned + one phase guess** (2026-11-18): `--cknn fmt --sps '{"batch": null, "cores": 32,
  "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}'`, F5 off. Parts `fs-gv32om*`
  (seeds 7032 / 7033); the jointly tuned receiver without the phase change: `fs-gv32km*`.
  - `batch: null` = all shortlisted cells scored in one round instead of blocks of 32 with a z > 5 gate;
    `cores: 32` keeps the cost on the study's 32-core model (**without it the code costs one core per grid cell,
    ~249 cores**: the first batch-null numbers, -41 ... -69 %, were that artefact; on 32 cores batch null + final 16
    gives -26 ... -36 %).
  - final 4 (was 32) candidates decoded in full; z-test window 4.0 (was 6.0); shortlist 1 - 0.003 cumulative NN
    probability, at least 4 cells (was 1 - 0.001, 8).
  - Chosen by the offline joint tuner (section 7), checked live on calibration packets (replay matches to 0.002 M,
    0 packets lost), on a held-out log and on fresh test packets (section 6).
  - Rejected on the way: the tuner's first pick (absolute-MAC objective: final 0, -48 % at -6.2 dB but +18 % at
    -4.6 dB); F5 early stop (tuned jointly, best pick saves ~2 % for pushing final / win further; live (0.9, 0.75):
    0-5 % for +6 ... +11 errors); CFO grid step 6 / 8 and coarse stride 3 (2-4x the errors); NN checkpoint 1/8 or
    3/16 (no saving); "NN only for rejected packets" (two-pass: cheaper only at high SNR).
- **DVB-RCS2 jointly tuned (live combinations on calibration packets, final reruns `fs-u*` running 2026-11-18)**:
  ID 13 `{"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8}`, ID 42 `{"final": 8, "win": 4.0, "ck_keep": 0.003,
  "ck_min": 8}`, ID 3 `{"final": 8, "win": 4.5}`, ID 14 `{"final": 8, "win": 4.0, "ck_keep": 0.01, "ck_min": 4}`.

## 5. Cost and Eb/N0 accounting

### 5.1 MACs per core

One unit for everything: every real add, compare-select, multiply or LUT read = 1 (`costmodel.py`; the polar MAC
model of [07_complexity.md](../BLIND_IMPLEMENTATION/07_complexity.md)). "MACs per core" is the critical path on
**32 cores**.

**Blind.** The scheduled standard of 07_complexity.md 7.5a:
- `c_d4a` at 2/5 and 1/2: 4 CA-SCL decodes at once.
- `c_hd4a` at 0.15: one core per (cell, phase) hypothesis, plus 4 decodes at once.
- Format MAC model (`blind_fmt`): decode 8 N log2 N, LLRs 4 n_sym + E, phase 4 n_sym, re-encoding N/2 log2 N + 4E.
  The VDE format charges no despreading (blind sends no chips).

**Honest NN accounting (`--charge-all`).** The checkpoint NN looks at every cell up to its checkpoint, but the old
count charged only the cells of the current round. `--charge-all` charges them all. Decisions and BLER are
identical; only the MACs change.

| Format | How the honest MACs were obtained | Effect |
|---|---|---|
| ID 13, 42, 3 | `<part>ca` reruns on the same seeds; `plot_fs_final.py` uses the `ca` MACs where they exist (filled markers) and the old count elsewhere (hollow) | ID 13 at -0.6 dB: +56 % (sum 1.03e10 -> 1.60e10) |
| ID 14 | no `ca` reruns needed | `ca` reruns at 1.2 and 1.6 dB give identical sums, so all ID 14 points are honest |
| VDE | `--charge-all` given directly | - |

**DVB-RCS2 turbo** (`turbo_db.macs`, 16-state duo-binary):
- Per couple per SISO pass: 252 add + 156 CS + 3 mul = 411 ops (branch metrics, alpha, beta with normalisation,
  APP, extrinsic and scaling).
- Per core (state-parallel on 32 cores): 2 x iters x N x (ceil(411/32) + 8), plus the decision and LLR scaling / 32.
- ID 13, 8 iterations: ~165.6 k per core. Adding the lean sync gives the measured 0.174 M per core at high SNR.

**VDE turbo** (`costmodel.siso_step_ops`, S = 8, binary): log-MAP 177 ops per SISO step. Per core:
2 x it x (k + 3) x (ceil(177/32) + 3 + 3), plus the APP and CRC per iteration with early stop.

**Competitor totals.** DA sync (lean) + per attempt (turbo + LLR scaling + `per_cand`), up to 3 attempts, plus the
despreading for VDE.

### 5.2 Eb/N0 offsets

Eb/N0 [dB] = Es/N0 + 10 log10(n_sym / A):
- n_sym = burst symbols for the competitor (known charged), or data symbols for blind;
- A = payload bits.

This is `rcs2.Waveform.ebn0`, `vde.VDELink.ebn0_db` and `run_blind_fs` `ebn0_offset`.

| Format | A | Competitor L (offset) | Blind n_sym (offset) | Symbol saving |
|---|---|---|---|---|
| ID 13 | 952 | 1616 (+2.298 dB) | 1476 (+1.904 dB) | 0.394 dB |
| ID 42 | 952 | 3236 (+5.314 dB; the plot uses 5.311) | 2952 (+4.915 dB) | 0.399 dB |
| ID 3 | 272 | 536 (+2.946 dB) | 456 (+2.244 dB) | 0.702 dB |
| ID 14 | 1472 | 1616 (+0.405 dB) | 1504 (+0.093 dB) | 0.312 dB |
| VDE 32 | 280 | 1641 (+7.680 dB) | 1269 (+6.563 dB) | 1.116 dB |

On the "known symbols free" axis both systems get the blind offset: the competitor's Es/N0 + 10 log10(data symbols / A),
the same data-symbol count for both.

## 6. Results (2026-11-17), BLER 1e-3, Eb/N0 per payload bit, known symbols charged

Gap = competitor - blind (**+ = blind better**). The crossings are log-linear interpolations between the two
bracketing points. The MACs per core are the mean near the crossing. Both are approximate: read the exact points
from the plots.

| Format | Blind [dB] | Competitor [dB] | Gap | Blind MACs/core | Competitor MACs/core |
|---|---|---|---|---|---|
| DVB-RCS2 ID 13 | 1.34 | 1.62 | **+0.28** | ~0.79 M | 0.175 M |
| DVB-RCS2 ID 42 | 1.28 | 1.58 | **+0.30** | ~0.12 M | 0.185 M |
| DVB-RCS2 ID 3 | 2.33 | 2.88 | **+0.55** | ~0.155 M | 0.055 M |
| DVB-RCS2 ID 14 | 1.77 | 2.01 | **+0.24** | ~0.17 M | 0.26 M |
| VDE-SAT Link 32 (jointly tuned, one phase guess) | 1.78 | 2.93 | **+1.15** | 0.21-0.23 M (was 0.42-0.46 M before tuning) | ~0.028 M |

- **Competitor settings.** DVB-RCS2: `strong` DA (top 3), max-log 8 iterations, no early stop. Parts
  `da_fs-q13da`, `q42td`, `q3td` + `q3deep`, `q14td`. VDE: `strong` DA, log-MAP 8 iterations, CRC early stop
  (`da_fs-vda32`, `vda32lo`).
- **Blind.** Final receiver on fresh seeds 70xx / 71xx; summary in `results/fs_final_summary.json`.
- **Statistics.** Blind points stop at 30 errors (`--max-err 30`), the competitor's at 100. Blind and the competitor
  run on different packets, so differences under ~0.1 dB are ties.
- **VDE (jointly tuned receiver, fresh test packets, paired with the receiver before tuning).** Same failing
  packets at every point (31 vs 32 at -6.2 dB, 30 vs 31 at -5.8 dB, otherwise identical), so the BLER curve and the
  +1.15 dB lead are unchanged. Mean MACs per core:

  | Es/N0 [dB] | -6.6 | -6.2 | -5.8 | -5.4 | -5.0 | -4.6 | -4.2 | -3.8 |
  |---|---|---|---|---|---|---|---|---|
  | before tuning [M] | 5.88 | 3.62 | 1.67 | 0.71 | 0.46 | 0.42 | 0.44 | 0.49 |
  | jointly tuned [M] | 2.20 | 1.44 | 0.74 | 0.41 | 0.33 | 0.31 | 0.31 | 0.31 |
  | **+ one phase guess (FINAL) [M]** | **2.05** | **1.31** | **0.62** | **0.32** | **0.23** | **0.21** | **0.21** | **0.21** |
  | change vs before tuning | -65 % | -64 % | -63 % | -55 % | -51 % | -50 % | -52 % | -57 % |

  Worst case per core 8.4 -> **2.9 M**. The blind crossing of BLER 1e-3 lies at about -4.78 dB Es/N0. VDE-SAT
  costs 0.025-0.03 M there, so blind is ~8x dearer (was ~16x before tuning).
  One phase guess (2026-11-18 01:00): for BPSK the squared signal fixes the phase mod pi, so the second phase hypothesis
  per CFO cell (offset pi/2) is dropped (`nph {"0.15": [2, 0.5]}`): half the grid hypotheses; paired over three fresh
  seeds 214 vs 215 errors at -5.0 dB and 59 vs 58 at -4.6 dB (within the 2 % rule), -31 ... -33 % MACs.
  - **MAC cap on the tuned receiver** ([fs_vde_tuned_capped.png](../BLIND_IMPLEMENTATION/testing/results/plots/VDE-SAT/MACs/fs_vde_tuned_capped.png),
    [fs_vde_tuned_macs_capped.png](../BLIND_IMPLEMENTATION/testing/results/plots/VDE-SAT/MACs/fs_vde_tuned_macs_capped.png)):
    2 M costs at most 4 extra errors per point (~free); 1 M about 0.05 dB at BLER 1e-3; 0.5 M about 0.1-0.15 dB.
    Above -5 dB the mean stays ~0.31 M under any cap (the per-packet floor); caps only cut the low-SNR tail.
  - VDE's own BLER target is 1e-2 (ARQ). The M.2092 design point (Es/N0 -4.5 dB) corresponds to 3.18 dB. Our VDE
    with DA sync reaches 1e-3 at 2.93 dB.
- **Cost ratio.** Blind is cheaper than DVB-RCS2 at ID 42 and ID 14. It is 2.8x dearer at ID 3 and 4.5x at ID 13,
  and 15x (current) or about 5x (candidate) at VDE.
- **MAC caps** (a packet that needs more than C MACs per core counts as an error) were evaluated and **not adopted**.
  No cap passed the 2 % rule at the operating points. Plots:
  [DVB-RCS2/MACs/](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/MACs/),
  [fs_final_capped.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/BLER/fs_final_capped.png) and
  [VDE-SAT/MACs/fs_vde_capped.png](../BLIND_IMPLEMENTATION/testing/results/plots/VDE-SAT/MACs/fs_vde_capped.png).
  For VDE, a cap of 1 M per core raises the BLER from 3e-4 to 2.9e-3 at -4.6 dB.

### 6.1 DVB-RCS2 jointly tuned (fresh test packets, paired with the receiver before tuning)

Settings per ID (live combinations on calibration packets, section 4.3 / tuning_fullsys.md). Numbers below are
generated by `py BLIND_IMPLEMENTATION/testing/plot_fs_tuned.py` then `py BLIND_IMPLEMENTATION/testing/dvb_tuned_table.py`.

| Waveform | DVB-RCS2 [dB] | Blind before [dB] | Blind tuned [dB] | Gap tuned (+ = blind better) | MACs/core before | MACs/core tuned | DVB-RCS2 MACs/core |
|---|---|---|---|---|---|---|---|
| ID 13 | 1.62 | 1.34 | 1.33 | **+0.29** | 0.789 M | 0.790 M | 0.175 M |
| ID 42 | 1.58 | 1.29 | 1.28 | **+0.29** | 0.121 M | 0.118 M | 0.185 M |
| ID 3 | 2.88 | 2.33 | 2.30 | **+0.58** | 0.155 M | 0.159 M | 0.055 M |
| ID 14 | 2.01 | 1.77 | 1.76 | **+0.24** | 0.175 M | 0.170 M | 0.263 M |

**ID 13**

| Es/N0 [dB] | errors before | errors tuned | MACs/core before [M] | MACs/core tuned [M] | change |
|---|---|---|---|---|---|
| -0.8 | 30/4600 | 30/4600 | 1.001 | 0.977 | -2 % |
| -0.6 | 83/64200 | 84/69000 | 0.808 | 0.804 | -0 % |
| -0.4 | 13/40000 | 13/40000 | 0.708 | 0.709 | +0 % |
| -0.2 | 2/80000 | 2/80000 | 0.616 | 0.617 | +0 % |
| +0.0 | 0/120000 | 1/120000 | 0.531 | 0.532 | +0 % |

**ID 42**

| Es/N0 [dB] | errors before | errors tuned | MACs/core before [M] | MACs/core tuned [M] | change |
|---|---|---|---|---|---|
| -4.2 | 38/600 | 38/600 | 0.952 | 0.820 | -14 % |
| -4.0 | 39/1600 | 39/1600 | 0.373 | 0.327 | -12 % |
| -3.8 | 90/19000 | 90/19200 | 0.178 | 0.165 | -7 % |
| -3.6 | 90/116600 | 90/118800 | 0.111 | 0.109 | -2 % |
| -3.4 | 20/150000 | 20/150000 | 0.099 | 0.099 | -0 % |
| -3.2 | 4/250000 | 4/250000 | 0.097 | 0.097 | -0 % |
| -3.0 | 2/400000 | 2/400000 | 0.096 | 0.096 | -0 % |

**ID 3**

| Es/N0 [dB] | errors before | errors tuned | MACs/core before [M] | MACs/core tuned [M] | change |
|---|---|---|---|---|---|
| -1.0 | 36/400 | 35/400 | 0.618 | 0.673 | +9 % |
| -0.8 | 34/800 | 32/800 | 0.404 | 0.434 | +7 % |
| -0.6 | 31/1600 | 30/1800 | 0.255 | 0.257 | +1 % |
| -0.4 | 31/3600 | 30/3600 | 0.206 | 0.212 | +3 % |
| -0.2 | 31/12800 | 31/12800 | 0.175 | 0.178 | +2 % |
| +0.0 | 30/20200 | 30/22400 | 0.161 | 0.162 | +1 % |
| +0.2 | 30/48000 | 30/59600 | 0.148 | 0.149 | +1 % |
| +0.4 | 30/93000 | 27/100000 | 0.140 | 0.141 | +0 % |
| +0.6 | 17/150000 | 16/150000 | 0.132 | 0.132 | +0 % |
| +0.8 | 19/300000 | 15/300000 | 0.123 | 0.124 | +0 % |
| +1.0 | 7/400000 | 6/400000 | 0.115 | 0.115 | +0 % |

**ID 14**

| Es/N0 [dB] | errors before | errors tuned | MACs/core before [M] | MACs/core tuned [M] | change |
|---|---|---|---|---|---|
| +1.0 | 42/200 | 40/200 | 5.505 | 2.982 | -46 % |
| +1.2 | 41/600 | 41/600 | 1.361 | 0.867 | -36 % |
| +1.4 | 32/2000 | 30/2200 | 0.427 | 0.328 | -23 % |
| +1.6 | 30/16400 | 31/16000 | 0.188 | 0.180 | -5 % |
| +1.8 | 84/223000 | 74/236000 | 0.153 | 0.152 | -1 % |
| +2.0 | 7/200000 | 8/200000 | 0.144 | 0.144 | +0 % |
| +2.2 | 2/300000 | 3/300000 | 0.142 | 0.142 | +0 % |

**Conclusions:**
- **BLER unchanged** by the joint tuning on all four IDs (same packets: differences of 0-2 errors per point, ID 3 a few
  fewer at +0.4 ... +1.0 dB). Gap to DVB-RCS2 at BLER 1e-3 (known symbols charged): ID 13 **+0.29 dB**, ID 42 **+0.29**,
  ID 3 **+0.58**, ID 14 **+0.24** (before tuning +0.28 / +0.29 / +0.55 / +0.24: within ~0.03 dB).
- **MACs: the gain is in the waterfall, not at the operating point.** ID 14 -46 / -36 / -23 % at +1.0 / +1.2 / +1.4 dB,
  ID 42 -14 / -12 / -7 % at -4.2 / -4.0 / -3.8 dB, about 0 % from BLER ~1e-3 on; ID 13 about 0 % everywhere (its
  receiver was already near its floor of decodes); ID 3 +1 ... +9 % (final 8 + win 4.5 bought the few BLER gains).
  The DVB receivers had far less slack than VDE: no batch scheduling to remove and F5 already tuned.
- **Versus DVB-RCS2 near BLER 1e-3:** blind is cheaper at ID 42 (0.12 vs 0.19 M) and ID 14 (0.17 vs 0.26 M), dearer at
  ID 3 (0.16 vs 0.055 M, ~2.9x) and ID 13 (0.79 vs 0.175 M, ~4.5x).
- **Worst case per packet** (footnotes of the plots) drops where the waterfall cost drops, e.g. ID 14 +1.0 dB 96 -> 77 M.

**Plots.**

| Format | Final (jointly tuned) | Before tuning |
|---|---|---|
| ID 13 | [fs_tuned_id13.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_tuned_id13.png) | [fs_final_id13.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_final_id13.png) |
| ID 42 | [fs_tuned_id42b.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_tuned_id42b.png) | [fs_final_id42b.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_final_id42b.png) |
| ID 3 | [fs_tuned_id3.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_tuned_id3.png) | [fs_final_id3.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_final_id3.png) |
| ID 14 | [fs_tuned_id14s.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_tuned_id14s.png) | [fs_final_id14s.png](../BLIND_IMPLEMENTATION/testing/results/plots/DVB-RCS2/overview/fs_final_id14s.png) |
| VDE 32 | [fs_vde32_final.png](../BLIND_IMPLEMENTATION/testing/results/plots/VDE-SAT/overview/fs_vde32_final.png) (both on one figure) | |

## 7. Tuning methodology (full record: [tuning_fullsys.md](../BLIND_IMPLEMENTATION/testing/results/tuning_fullsys.md))

**Seed ranges.** Every threshold was chosen on data kept apart from the reported curves:

| Purpose | Seeds |
|---|---|
| Calibration packets | `run_blind_fs --calib`: seed tag + 500000, disjoint from every test run |
| NN training and validation | tag + 900000 |
| DA calibration runs | `--calib-seed-offset 1000000` |
| Final curves | further fresh seeds 70xx / 71xx |

**Rule.** The cheapest setting (mean MACs per core) whose extra errors are <= floor(0.02 x no-stop errors) at every
calibration point. The choice is then replayed on the paired test packets ([tune_blind_fs.py](tune_blind_fs.py),
offline from `--dump` decode rows) and checked live on fresh seeds.

**Live z-test grid.** Shortlist and phase-keep settings, the final count and batch / first_k were tested live on
calibration packets ([zt_compare.py](zt_compare.py), output `results/zt_compare_2026-11-17.txt`).

**Two-pass replay.** [two_pass_replay.py](two_pass_replay.py) replays the VDE option "NN only for the packets the
cheap receiver rejects".

**Joint tuning (VDE, done 2026-11-18; DVB: live combinations).** All search settings are tuned TOGETHER, not one at
a time:
1. **Full-search log** (`run_blind_fs --fulllog`, small_rx `fulllog`): a normal run of the base receiver that also
   records, per packet, every hypothesis' path metrics at all checkpoints, the NN log-probabilities, every decode
   attempt (CRC, re-encoding check, right / wrong, cost) and extra decodes of the cells next to the true CFO.
2. **Offline joint tuner** [joint_tune_fs.py](joint_tune_fs.py) replays the search from the log for any setting of
   ck_keep, ck_min, tau, kmin, win, ncand, z0, final, final_post, fine_last, T, cores (exact while every decode lands
   on a logged hypothesis; an unlogged decode counts as a failure at full cost). Self-check first: replaying the
   logged setting must reproduce every packet (decisions and every cost counter). Then coordinate descent + random
   restarts minimising the **mean over the calibration points of cost / baseline cost** (each SNR counts equally),
   subject to the 2 % rule at every point.
3. The pick is checked **live on the same calibration packets** (replay vs reality), **replayed on a held-out log**
   (another calibration seed) and run as the **final curve on fresh test packets** paired with the previous final.

Not replayable, so tested live instead: the CFO grid step / coarse stride, the NN checkpoint position, batch
(32, z) vs null. F5 (`fzstop`) replays only approximately (pessimistic) and was tuned jointly and then checked live.
DVB-RCS2 cannot be replayed (joint list decodes couple the cells), so its combinations were tuned live on
calibration packets (`fs-zt<ID>k8`, `k9`, compared with `zt_compare.py`).

## 8. How to run

Cluster only. Never run simulations locally or on the login node. Jobs are bash scripts in `jobs/`, pushed and
submitted with [../multipath/cluster.py](../multipath/cluster.py) from the Bash tool, 16 cores:

```bash
py multipath/cluster.py run --job fs-g13a --cpu 16 --mem 24Gi \
   --push jobs/fs-g13a.sh fullsys/run_blind_fs.py --cmd @jobs/fs-g13a.sh --results fullsys/results
```

Each script sets `BLIND_STUDY=small_cfo` and the thread variables, then calls the env's python (see `jobs/fs-g13a.sh`).

**Blind (final ID 13 receiver):**
```bash
python fullsys/run_blind_fs.py --fmt id13 --design ga --cfo-max 0.03 --cknn fmt --fzstop 0.6,0.80 \
   --snrs -0.6 --frames 20000 --max-err 30 --seed 7013 --dump --charge-all --workers 16 --part fs-<new>
```

| Flag | Meaning |
|---|---|
| `--fmt` | `id3`, `id13`, `id14s` / `id14p`, `id42b` / `id42q`, `vde32` |
| `--design` | `pw` (default) or `ga`, with `--design-snr` |
| `--cknn` | `keep` (native NN), `off` or `fmt` (own NN) |
| `--fzstop` | `off` (default), `adopted` or `q,t` |
| `--spec` | `off` (default) or `adopted` |
| `--rho` | `scaled` (default), `table` or `min` |
| `--cap-core` | MAC cap per packet |
| `--charge-all` | honest NN accounting |
| `--sps '<json>'` | small_rx spec overrides |
| `--calib` | calibration seeds |
| `--dump` | per-packet records |
| `--beta` | roll-off |

`--selfcheck` sends 3 packets per format at 30 dB.

**DVB-RCS2 with its DA synchroniser:**
```bash
python fullsys/run_fullsys_da.py --sys rcs2 --wf 13 --snrs -0.8 -0.6 --frames 300000 --max-err 100 \
   --seed 13 --variant strong --top-m 3 --workers 16 --part fs-<new>
```
Variants: `standard` / `strong` / `genie` / `ideal`. Ideal-sync reference runs (validation):
`run_rcs2.py --wf 13 --snrs ...` or `--fmt aff3ct-N3008 --ebn0-aff3ct ...`.

**VDE-SAT reference:**
```bash
python fullsys/run_fullsys_da.py --sys vde --link 32 --snrs -5.0 -4.5 --frames 300000 --max-err 100 \
   --seed 1 --variant strong --top-m 3 --algo logmap --workers 16 --part fs-<new>
```
Ideal sync: `run_vde.py --link 32 --algo logmap --iters 8 --snrs ... --part ...`.

**Result files** (`fullsys/results/`):

| File | Content |
|---|---|
| `blind_fs_<part>.json` | meta incl. all args, the spec and the MAC model; per point: frames, errors, undetected, `sum_c_d4a` / `sum_c_hd4a`, max, histograms, per-chunk `fe_idx` for pairing |
| `blind_fs_<part>_dump/` | per-packet and per-decode npz (input to the tuners) |
| `da_<part>.json` | competitor with DA: `ops_mean`, `crit_mean` (MACs per core), sync cost breakdown, error records |
| `rcs2_<part>.json`, `vde_<part>.json` | ideal-sync references |
| `polar_genie_<part>.json` | code-only genie-sync polar runs |
| `ck_nn_fs_<part>.json` | NN training history |
| `tune_*.json`, `tuning_f5_sweep.json` | tuner output |
| `fs_final_summary.json` | the pooled final points |
| `.prog` | progress, `done total elapsed_s` |

Parts are never overwritten; a new run needs a new name.

**Plots** (local, from existing results only):

| Script | Output |
|---|---|
| `py BLIND_IMPLEMENTATION/testing/plot_fs_final.py` | `DVB-RCS2/overview/fs_final_<id>.png`, `DVB-RCS2/BLER/fs_final_capped.png`, `results/fs_final_summary.json` (pools `fs-g*` / `fs-h*`, uses the `ca` MACs) |
| `py BLIND_IMPLEMENTATION/testing/plot_vde_final.py` | `VDE-SAT/overview/fs_vde32_final.png` (its points are typed into the script) |
| `py BLIND_IMPLEMENTATION/testing/plot_tuning_f5.py` | `DVB-RCS2/tuning/fs_tuning_f5.png`, `results/tuning_f5_sweep.json` |
| `plot_fullsys_refs.py` | the published reference curves |

Plot folder `BLIND_IMPLEMENTATION/testing/results/plots/` ([README](../BLIND_IMPLEMENTATION/testing/results/plots/README.md)):
- `DVB-RCS2/{overview, BLER, MACs, tuning, superseded}`
- `VDE-SAT/{overview, MACs, tuning, superseded}`
- `original_study/`

## 9. Limitations and open items

**Scope.**
- **Timing and burst detection are out of scope**: known for everyone. In real DVB-RCS2 and VDE systems the unique
  word and syncwords also do this job. The result holds "given timing".
- **CFO range.** +-0.03 is the top of DVB-RCS2's design range (TR 101 545-4: 0.5-3 % of the symbol rate). DVB-RCS2
  runs at +-0.005 exist (`da_fs-n3/13/14/42`) but are not summarised here. VDE's real Doppler range is wider; we keep
  +-0.03 (user decision).

**Differences between the runs and the docs.**
- **Blind VDE vs VDE**: blind uses the PW construction (GA not run for VDE) and roll-off 0.20, and has no spreading.
  The roll-off and the spreading are immaterial in AWGN per symbol (`run_polar_genie` assumptions), but they differ
  from the standard's 0.25 and x8.
- **Re-encoding thresholds** are provisional (scaled from the native tables, not calibrated per format).
- **spec11** is off in every full-system run, including VDE.

**Open checks.**
- **AFF3CT bit-exact check**: `compare_aff3ct.py` is written, but no test vectors are present locally. Status
  (unverified). The statistical agreement with AFF3CT's curve (~0.03-0.05 dB) is measured.
- **List-32 reference**: genie-sync CA-SCL-32 GA runs (`polar_genie_fs-pg32-{3,13,14s,42b}`, finished per `.prog`)
  are not yet analysed or plotted here (unverified).

**Next steps.**
- **VDE batch null + final 16**: finish the -4.2 / -3.8 dB fresh check, then adopt if it stays identical.
- **Joint tuning**: tuning of all thresholds with NN retraining (VDE first), in progress.
- **Next systems**: NB-IoT NTN (3GPP NPUSCH format 1, LTE turbo + CRC-24A, DM-RS DA sync; [nbiot.py](nbiot.py)) is
  planned. Phase 2 (lower SNR and the rates 1/10, 0.15, where DVB-RCS2 has no native turbo mode) comes after phase 1.
