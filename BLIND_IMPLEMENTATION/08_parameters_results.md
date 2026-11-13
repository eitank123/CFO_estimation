# 8. Parameters per rate, and results

## 8.1 Final receivers (`blind_ber.py`)
R = 0.15 uses the R = 1/10 column (`blind_cfo.PROFILE = {"0.15": "1/10"}`), with its own RHO_N table (06); it is not
tuned for its code yet.

| Parameter | R = 1/10 and 0.15 (`S blind final v2`) | R = 2/5 (`S blind final 2/5, 1/2, best-first 32`) | R = 1/2 (`S blind final 2/5, 1/2`) |
|---|---|---|---|
| Fast path | always | always | always |
| Grid step k (cells) | 4 STEP (201) | 2 STEP (401) | 2 STEP (401), 4 STEP from 4 dB |
| Phases per cell | 4 below −1 dB, else 2 | 2 | 2 |
| Cell prior | 4th-power periodogram (s4) | s4 (best-first 32) | — |
| First stage | coarse start (every 2nd cell) to ½, neighbours join | checkpoint NN at ¼ | checkpoint NN at 3/16 |
| z-test checkpoints | ½, ¾ (τ = −0.5) | ⅜, ½, ¾ (τ = −1) | ¼, ½ (τ = −1) |
| k_min / early win | 16 / z > 6 | 16 / z > 6 | 16 / z > 6 |
| Phase pruning | best 2 phases per cell from ½ | — | — |
| Cores | batches of 32 cells, block rejected if z < 5 | 32 cores in passes | 32 cores in passes |
| Candidates | z > 4 (≤ 4), then best 32 by PM | same | same |
| Refinement | ±2 STEP × (±π/12 below −1 dB), best T = 2 | ±1 STEP, T = 2 | same |
| Decoding | CA-SCL-8 per hypothesis | joint list of 16 paths over 4 cells × 2 hypotheses | same |
| Code-aided retry | yes (Newton ×2) | yes | yes |
| Rescue | 256 cells, then half-STEP × π/16 on the best 4 | same | same |
| Acceptance | PiCode CRC-16 + re-encoding check (RHO_N) | same | same |
| MF | pre-MF correction at f₀ and per candidate | same | same |
| Cost model | Fast-SSC tree cost | same | same |

## 8.2 Results (AWGN, CFO uniform in ±0.03, full chain; all runs merged, 2026-11-12)
Errors / packets. "Genie" knows the CFO and phase and decodes once. The 128-pilot receivers (est3) use the same
back-end as blind (pre-MF correction, CA-SCL-8, CRC search over neighbouring CFOs, the same re-encoding check); "ML"
is the ML estimator (FFT 512 + 2 Newton), "CRB" an ideal estimator whose CFO error is drawn at the Cramér-Rao bound.

**R = 1/10**

| SNR | Blind | Genie | ML, 128 pilots | joint CFO / channel ML | CRB, 128 pilots |
|---|---|---|---|---|---|
| −5 dB | **2.1·10⁻⁴** (88 / 424k) | 2.9·10⁻⁵ (83 / 2.8M) | 6.5·10⁻⁵ (66 / 1.0M) | 6.8·10⁻⁵ (69 / 1.0M) | 6.6·10⁻⁵ (63 / 960k) |
| −4.5 dB | 3.4·10⁻⁵ (19 / 560k) | 8·10⁻⁷ | 4.1·10⁻⁵ | 2.7·10⁻⁵ | 3.9·10⁻⁵ |
| −4 dB | 1.6·10⁻⁶ (1 / 624k) | 0 / 2.8M | 3.0·10⁻⁵ | 4.0·10⁻⁵ | 2.1·10⁻⁵ |
| −3 dB | 0 / 260k | 0 | 3.1·10⁻⁵ | 3.6·10⁻⁵ | 3.4·10⁻⁵ |
| −2 … 0 dB | 0 / 160k each | 0 | 1–2·10⁻⁵ | 2·10⁻⁵ | 2·10⁻⁵ |

**R = 0.15**

| SNR | Blind | Genie | ML, 128 pilots | joint ML | CRB, 128 pilots |
|---|---|---|---|---|---|
| −4.5 dB | 3.1·10⁻² (11239 / 360k) | 2.8·10⁻² | 2.1·10⁻² | 2.1·10⁻² | 2.1·10⁻² |
| −4 dB | 4.2·10⁻³ (2175 / 524k) | 2.0·10⁻³ | 1.3·10⁻³ | 1.3·10⁻³ | 1.3·10⁻³ |
| −3.5 dB | 6.8·10⁻⁴ (230 / 340k) | 5.9·10⁻⁵ | 7.2·10⁻⁵ | 7.2·10⁻⁵ | 6.5·10⁻⁵ |
| −3 dB | 1.1·10⁻⁴ (93 / 844k) | 0 / 944k | 3.1·10⁻⁵ | 4.0·10⁻⁵ | 3.3·10⁻⁵ |
| −2.5 dB | 9.1·10⁻⁶ (6 / 660k) | 0 | 2.3·10⁻⁵ | 1.7·10⁻⁵ | 2.4·10⁻⁵ |
| −2 dB | **0 / 780k** | 0 | 2.2·10⁻⁵ | 2.9·10⁻⁵ | 2.3·10⁻⁵ |
| −1 dB | **1.6·10⁻⁴** (143 / 880k) | 0 | 2.4·10⁻⁵ | 2.3·10⁻⁵ | 2.3·10⁻⁵ |
| 0 dB | 1.8·10⁻⁵ (14 / 780k) | 0 | 1.1·10⁻⁵ | 1.0·10⁻⁵ | 6.3·10⁻⁶ |
| +1 dB | 0 / 780k | 0 | 1.4·10⁻⁵ | 5.2·10⁻⁶ | 6.3·10⁻⁶ |

**R = 2/5 and 1/2**

| Rate / SNR | Blind | Genie | ML, 128 pilots | CRB, 128 pilots |
|---|---|---|---|---|
| 2/5, 0.5 dB | 2.3·10⁻³ (1536 / 681k) | 3.2·10⁻³ | 2.6·10⁻³ | 2.5·10⁻³ |
| 2/5, 1 dB | 5.9·10⁻⁵ (76 / 1.28M) | 1.1·10⁻⁴ | 6.6·10⁻⁵ | 5.6·10⁻⁵ |
| 2/5, 1.5–3 dB | 0 / 0.6–0.72M each | ≤ 3.5·10⁻⁶ | 4·10⁻⁶ … 4·10⁻⁵ | 4·10⁻⁶ … 2·10⁻⁵ |
| 1/2, 2 dB | 1.4·10⁻⁴ (159 / 1.15M) | 4.7·10⁻⁴ | 3.6·10⁻⁴ | 3.4·10⁻⁴ |
| 1/2, 2.5 dB | 9·10⁻⁷ (1 / 1.15M) | 1.1·10⁻⁵ | 3.0·10⁻⁵ | 2.3·10⁻⁵ |
| 1/2, 3–5 dB | 0 / 0.6–0.72M each | 0 | 6·10⁻⁶ … 1.5·10⁻⁵ | 1–2·10⁻⁵ |

**Reading the tables**
- **The pilot receivers' floor (1–4·10⁻⁵).** It is the same for every estimator, including the ideal CRB one, and the
  genie has 0 errors there. The errors are all *undetected*: the CFO error left by 128 pilots makes the back-end
  try 1–6 extra decodes at neighbouring CFOs; each can pass CRC-16 with wrong data, the re-encoding check stops
  ~93 % of those, the rest form the floor. Blind has no such floor at R = 1/10, 2/5, 1/2 (0 errors in 160k–1M
  packets above the waterfall).
- **Blind vs pilots in the waterfall.** At the lowest SNRs blind loses to the pilot receivers: R = 1/10 −5 dB
  (2.1·10⁻⁴ vs 6.5·10⁻⁵) and R = 0.15 −4 … −3 dB (3–9×); at R = 2/5 and 1/2 blind is equal or better, because its
  retries and joint list decoding add decoding diversity (it even beats the one-decode genie).
- **R = 0.15 is not tuned.** Blind beats every pilot receiver from −2.5 dB up except at −1 and 0 dB, where the
  4 → 2 phase switch of the R = 1/10 settings loses the CFO (04, 4.1).
- **Why blind can beat the genie at R = 2/5 and 1/2:** the genie makes one decode. Blind retries a failing packet
  on neighbouring hypotheses and in a 16-path joint list, which is extra decoding diversity.

**Undetected errors (blind):** 1 in 2.35 M packets at R = 1/10 (at −5 dB); 30 in 5.9 M at R = 0.15 (22 at −4.5 dB,
5 at −4 dB, 1 at −1 dB, 2 at 0 dB); 4 in 4.5 M at R = 2/5 (3 at 0.5 dB, 1 at 1 dB); 2 in 4.9 M at R = 1/2 (1.5 dB). They sit
almost all deep in the waterfall, where many hypotheses are decoded per packet. Noise-only packets: 0 false alarms
in 9,600 (earlier final receivers).

## 8.3 Throughput with the pilots inside the packet
The pilot receivers' 128 known symbols sit inside the 1024-symbol packet, so they carry no data. Information bits per packet:

$$T = A\,(1-\mathrm{BLER})\cdot\frac{1024 - n_{\text{pilots}}}{1024}.$$

- **The pilots' factor:** for 128 pilots it is 0.875, a **12.5 % throughput loss** at any BLER.
- **Blind's factor:** 1.
- **The BLER term:** at the operating points (BLER ≤ 10⁻³), (1 − BLER) changes T by at most 0.1 %.

So blind delivers about 12–14 % more data per packet than every 128-pilot receiver here. That includes the ML + re-encoding check receiver, which has lower BLER at R = 1/10 −5 dB (6.5·10⁻⁵ vs 2.1·10⁻⁴).

The pilot receivers would beat blind on throughput only where blind's BLER is more than about 12 % higher in absolute terms, deep in the waterfall.

**Matching throughput instead:** a pilot system that keeps the same data bits needs a code rate 1024/896 times higher, which costs roughly 0.5–0.7 dB of SNR.

## 8.4 Limits of what was simulated
- **Ideal synchronisation:** timing and SNR are known. A 1 dB SNR error was tested, and a 1 dB threshold margin fixes it.
- **Static channel:** AWGN only, with a static CFO over the packet (no drift or phase noise).
- **Floating-point arithmetic.**
- **No worst-case MAC cap** in the receiver (7.6 gives the BLER cost of one).
- **PiCode's assumption:** it requires u_{N−1} to be an information bit and no shortening. With 5G-NR-style rate matching by shortening, 4 phase branches would be needed in the final decodes.
