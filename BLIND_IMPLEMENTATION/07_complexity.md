# 7. Complexity: MACs and the critical path on 32 cores

Code: MAC counters in `small_rx.small_receive` (`macs`, `pmac`, `crit`, `dmac`, `dcrit`) and the constants in `blind_vp.MAC`.

## 7.1 Unit costs (real multiply-accumulates)
| Operation | MACs |
|---|---|
| Complex multiply | 4 |
| FFT of n points | ≈ 2n·log₂n (4096 points: 98,304) |
| 4th power of 1024 symbols | 8·1024 |
| Phase from the 4th power (phase4) | 4,096 |
| De-rotation + LLRs of one hypothesis | 4·1024 + 6,144 |
| One full list-1 Fast-SSC metric pass | `metric_macs(A)` from the node plan (2n per f/g, n per rate-0/1 leaf, 2n per REP/SPC) |
| Partial metric up to fraction c | metric cost × tree-cost share (R = 1/10: the first half is 36 %) |
| One CA-SCL-8 decode | 8·N·log₂N = 180,224, plus 6,144 for the LLRs |
| Pre-MF correction (de-rotation; its MF replaces the chain's) | 4·(1024 + 20)·8 |
| Re-encoding check | 20,000 |
| Code-aided retry | metric + LLRs + 4·1024 + 2·20·1024 + 8·1024, plus one decode |

## 7.2 Total MACs per packet
The sum of everything the receiver did for that packet:
- the fast-path FFTs;
- every partial metric up to the checkpoint where the cell stopped (a cell dropped at c = ½ costs only its first half);
- the refinement scoring;
- the decodes, retries and checks.

## 7.3 Critical path (latency) on 32 cores
Every **parallel stage** (the cells of a pass, the scored hypotheses) is dealt out to the K = 32 cores, largest jobs first. Each pass costs its busiest core:

$$\text{crit}_{\text{stage}} = \sum_{p}\ \max_{\text{core}}\ \text{cost} \;=\; \sum_{i\ \equiv\ 0 \bmod K} \text{cost}_{(i)}\quad(\text{costs sorted descending}).$$

Serial work (the FFT, pre-MF, retries, checks) counts in full. A CA-SCL-8 decode with its **list paths on their own cores** counts as one path, decode/8, plus the path-metric sort at every information bit:

$$\text{crit}_{\text{decode}} = \frac{8 N\log_2 N}{8}\Big\lceil\frac{L}{K}\Big\rceil + 6144\Big\lceil\frac{H}{K}\Big\rceil + K_{\text{info}}\cdot 2L\log_2(2L).$$

The reported "MACs per core" is the critical path with list paths in parallel (`crit_lp_macs`).

## 7.4 Measured (final receivers, mean per packet)
| Rate | SNR | BLER | Total MACs | MACs per core (critical path) |
|---|---|---|---|---|
| 1/10 | −5 dB | 1.75·10⁻⁴ | 4.16 M | 0.77 M |
| 1/10 | −4 dB | 5·10⁻⁶ | 2.99 M | 0.70 M |
| 1/10 | 0 dB | 0 / 10⁵ | 1.44 M | 0.54 M |
| 2/5 | 0.5 dB | 2.1·10⁻³ | 3.65 M | 1.72 M |
| 2/5 | 1.0 dB | 8·10⁻⁵ | 1.26 M | 0.73 M |
| 1/2 | 2.0 dB | 1.4·10⁻⁴ | 0.74 M | 0.47 M |
| 1/2 | ≥ 2.5 dB | 0 / 10⁵ | 0.55 M | 0.43 M |

**Reference:** a 128-pilot receiver (split NN + one CA-SCL-8 + CRC search) costs about 0.4–0.8 M MACs in total.

**Worst case:** noise-only packets or failures that exhaust the search cost up to about 400 M MACs (R = 2/5, 1/2). A real modem needs a cap with a "no packet" decision there (not implemented).
