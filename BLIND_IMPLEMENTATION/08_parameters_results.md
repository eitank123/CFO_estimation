# 8. Parameters per rate, and results

## 8.1 Final receivers (`blind_ber.py`)
| Parameter | R = 1/10 (`S blind final v2`) | R = 2/5 (`S blind final 2/5, 1/2, best-first 32`) | R = 1/2 (`S blind final 2/5, 1/2`) |
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

## 8.2 Results (AWGN, CFO uniform in ±0.03, full chain)
| Rate | SNR (Es/N0) | Blind BLER | Genie (known CFO and phase, 1 decode) | Best 128-pilot receiver (true phase given) |
|---|---|---|---|---|
| 1/10 | −5 dB | **1.75·10⁻⁴** | 3.0·10⁻⁵ | split NN 2.1·10⁻⁴; split ML + re-encoding check 2.5·10⁻⁵ |
| 1/10 | −4.5 dB | 3.5·10⁻⁵ | 0 | split NN 1.5·10⁻⁴ |
| 1/10 | −4 dB | 5·10⁻⁶ | 0 | split NN 1.2·10⁻⁴ |
| 1/10 | −3 … 0 dB | 0 / 10⁵ | 0 | 10⁻⁴ … 2·10⁻⁵ (undetected-error floor) |
| 2/5 | 0.5 dB | 2.1·10⁻³ | 3.2·10⁻³ | split NN 1.7·10⁻³ |
| 2/5 | 1.0 dB | 8·10⁻⁵ | 1.2·10⁻⁴ | split NN 5.3·10⁻⁵ |
| 1/2 | 2.0 dB | 1.4·10⁻⁴ | 4.7·10⁻⁴ | split NN 2.4·10⁻⁴ |
| 1/2 | ≥ 2.5 dB | 0 / 10⁵ | ≤ 10⁻⁵ | split NN 8·10⁻⁶ … 2·10⁻⁶ |

**Why blind can beat the genie at R = 2/5 and 1/2:** the genie makes one decode. Blind retries a failing packet on neighbouring hypotheses and in a 16-path joint list, which is extra decoding diversity.

**Undetected errors:** with the re-encoding check, blind had 0 undetected errors in 1.4 M packets, and 0 false alarms in 9,600 noise-only packets.

## 8.3 Throughput with the pilots inside the packet
The pilot receivers' 128 known symbols sit inside the 1024-symbol packet, so they carry no data. Information bits per packet:

$$T = A\,(1-\mathrm{BLER})\cdot\frac{1024 - n_{\text{pilots}}}{1024}.$$

- **The pilots' factor:** for 128 pilots it is 0.875, a **12.5 % throughput loss** at any BLER.
- **Blind's factor:** 1.
- **The BLER term:** at the operating points (BLER ≤ 10⁻³), (1 − BLER) changes T by at most 0.1 %.

So blind delivers about 12–14 % more data per packet than every 128-pilot receiver here. That includes the split ML + re-encoding check receiver, which has lower BLER at R = 1/10 −5 dB (2.5·10⁻⁵ vs 1.75·10⁻⁴).

The pilot receivers would beat blind on throughput only where blind's BLER is more than about 12 % higher in absolute terms, deep in the waterfall.

**Matching throughput instead:** a pilot system that keeps the same data bits needs a code rate 1024/896 times higher, which costs roughly 0.5–0.7 dB of SNR.

## 8.4 Limits of what was simulated
- **Ideal synchronisation:** timing and SNR are known. A 1 dB SNR error was tested, and a 1 dB threshold margin fixes it.
- **Static channel:** AWGN only, with a static CFO over the packet (no drift or phase noise).
- **Floating-point arithmetic.**
- **No worst-case MAC cap** on noise-only packets.
- **PiCode's assumption:** it requires u_{N−1} to be an information bit and no shortening. With 5G-NR-style rate matching by shortening, 4 phase branches would be needed in the final decodes.
