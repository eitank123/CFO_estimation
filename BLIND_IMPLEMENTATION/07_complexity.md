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

## 7.3 MACs per core: the standard model (32 decoder cores)
"MACs per core" is the latency measure of this study: the MACs on the busiest core of a receiver with **K = 32**
cores, summed over the packet (`crit_par_macs` in `small_rx.small_receive`). The work is split as follows:

| Step | On the critical path |
|---|---|
| Search passes (cells of a pass, scored hypotheses) | dealt to the 32 cores, largest first; each pass costs its busiest core |
| 4th power, both 4096-point FFTs, pre-MF corrections, LLRs, phase sums, Newton sums of the code-aided retry, re-encoding correlation, priors, checkpoint NN | cost / 32 (sample-wise steps split over the cores) |
| One CA-SCL-8 decode | one list path per core: 8N log₂N / 8, plus the 2L → L path sort at each of the K information bits as a bitonic network, K · ½ log₂(2L)(log₂(2L) + 1) (10 stages for 2L = 16) |
| SC metric passes outside the parallel stages (code-aided retry, the fast path's π/2-branch choice) | sequential (one branch per core) |

For one pass of a parallel stage:

$$\text{crit}_{\text{stage}} = \sum_{p}\ \max_{\text{core}}\ \text{cost} \;=\; \sum_{i\ \equiv\ 0 \bmod K} \text{cost}_{(i)}\quad(\text{costs sorted descending}).$$

The final reduction of a sum over the cores (about log₂ 32 = 5 additions) is not counted, and one list path's own
f/g operations are not split further over the free cores (32 / 8 = 4 per path), so the model is slightly
conservative. (An earlier model kept every serial step on one core; it gave 2.5–6× higher per-core numbers and is
no longer used.)

## 7.4 Measured (final receivers, mean per packet, all runs merged, 2026-11-12)
| Rate | SNR | BLER (errors / packets) | Total MACs | **MACs per core** | per core: serial / decodes / search |
|---|---|---|---|---|---|
| 1/10 | −5 dB | 2.1·10⁻⁴ (88 / 424k) | 4.16 M | **0.31 M** | 0.04 / 0.08 / 0.19 M |
| 1/10 | −4.5 dB | 3.4·10⁻⁵ (19 / 560k) | 3.41 M | **0.28 M** | 0.03 / 0.08 / 0.17 M |
| 1/10 | −4 dB | 1.6·10⁻⁶ (1 / 624k) | 2.99 M | **0.26 M** | 0.03 / 0.08 / 0.15 M |
| 1/10 | −3 dB | 0 / 260k | 2.67 M | **0.24 M** | 0.03 / 0.08 / 0.14 M |
| 1/10 | −2 / −1 / 0 dB | 0 / 160k each | 2.53 / 1.94 / 1.44 M | **0.23 / 0.20 / 0.15 M** | |
| 0.15 | −4.5 dB | 3.1·10⁻² (11239 / 360k) | 22.1 M | **2.32 M** | |
| 0.15 | −4 dB | 4.2·10⁻³ (2175 / 524k) | 7.27 M | **0.64 M** | 0.12 / 0.25 / 0.26 M |
| 0.15 | −3.5 dB | 6.8·10⁻⁴ (230 / 340k) | 4.22 M | **0.35 M** | |
| 0.15 | −3 dB | 1.1·10⁻⁴ (93 / 844k) | 3.31 M | **0.28 M** | 0.04 / 0.08 / 0.17 M |
| 0.15 | −2.5 dB | 9.1·10⁻⁶ (6 / 660k) | 2.90 M | **0.26 M** | |
| 0.15 | −2 dB | 0 / 780k | 2.70 M | **0.25 M** | 0.03 / 0.08 / 0.14 M |
| 0.15 | −1 dB | 1.6·10⁻⁴ (143 / 880k) | 2.35 M | **0.24 M** | |
| 0.15 | 0 dB | 1.8·10⁻⁵ (14 / 780k) | 1.59 M | **0.17 M** | 0.03 / 0.06 / 0.08 M |
| 0.15 | +1 dB | 0 / 780k | 0.88 M | **0.099 M** | 0.02 / 0.04 / 0.05 M |
| 2/5 | 0.5 dB | 2.3·10⁻³ (1536 / 681k) | 3.72 M | **0.41 M** | 0.12 / 0.23 / 0.09 M |
| 2/5 | 1 dB | 5.9·10⁻⁵ (76 / 1.28M) | 1.26 M | **0.13 M** | 0.02 / 0.05 / 0.05 M |
| 2/5 | 1.5–3 dB | 0 / 0.60–0.72M each | 0.55–0.77 M | **0.072–0.089 M** | 0.01 / 0.03–0.04 / 0.03–0.04 M |
| 1/2 | 2 dB | 1.4·10⁻⁴ (159 / 1.15M) | 0.74 M | **0.085 M** | 0.01 / 0.04 / 0.04 M |
| 1/2 | 2.5 dB | 8.7·10⁻⁷ (1 / 1.15M) | 0.58 M | **0.075 M** | 0.01 / 0.03 / 0.03 M |
| 1/2 | 3–5 dB | 0 / 0.60–0.72M each | 0.55 M | **0.074 M** | 0.01 / 0.03 / 0.03 M |

(Total MACs over all packets; MACs per core averaged over the runs that record the critical path, 40k–544k
packets per point; the split columns come from the 20 000-packet `cpar` runs.) R = 0.15 runs the R = 1/10 settings;
its −1 dB point (1.6·10⁻⁴, while −2 dB has 0 errors in 780k packets and the genie has 0) shows they are not tuned for it: in those
failures the search never reaches the true CFO region (see 04, 4.1).

**Where the total MACs go** (per-packet breakdown from instrumented baseline runs):

| | 1/10 −5 dB | 1/10 −4.5 dB | 0.15 −4 dB | 0.15 −3 dB | 0.15 −1 dB |
|---|---|---|---|---|---|
| fast path | 19 % | 23 % | 11 % | 24 % | 32 % |
| CA-SCL decodes (+ retries) | 15 % | 17 % | 25 % | 18 % | 24 % |
| search metrics + refinement scoring | 66 % | 60 % | 64 % | 59 % | 44 % |

So the grid search over CFO × phase (04) and the scoring of the refinement offsets (05) are the cost to attack; the
full decodes are a minority.

## 7.5 Comparison with a 128-pilot receiver (same model)
The pilot receivers (est3, same back-end: pre-MF correction, CA-SCL-8, the same re-encoding check, CRC search over
neighbouring CFOs) are costed with the same model from their measured extra decodes (`est3/plots.pilot_macs`; an
estimate, not instrumented). Their CRC search runs **4 decodes at once** (32 cores / 8 list paths per decode): the
decode at the estimate first, then the neighbouring CFOs 4 at a time, so per core 1 + x/4 decode rounds for x extra
decodes. The last round of 4 may decode up to 3 hypotheses past the accepted one; the totals add min(x, 1.5)
decodes for that (an approximation: only the mean x is stored per point). For the ML estimator (FFT 512 + 2 Newton):

| Rate / SNR | extra decodes x | ML 128 pilots, 4 at once: total / per core | (one at a time: per core) | Blind: total / per core |
|---|---|---|---|---|
| 1/10 −5 dB | 6.5 | 1.75 M / 0.068 M | 0.19 M | 4.17 M / 0.31 M |
| 1/10 −4 dB | 4.8 | 1.44 M / 0.057 M | 0.15 M | 2.99 M / 0.26 M |
| 1/10 0 dB | 1.1 | 0.68 M / 0.034 M | 0.06 M | 1.45 M / 0.15 M |
| 0.15 −4 dB | 6.3 | 1.72 M / 0.069 M | 0.19 M | 7.28 M / 0.64 M |
| 0.15 −3 dB | 4.5 | 1.38 M / 0.057 M | 0.15 M | 3.30 M / 0.28 M |
| 0.15 0 dB | 1.5 | 0.82 M / 0.038 M | 0.07 M | 1.59 M / 0.17 M |
| 2/5 0.5 dB | 3.7 | 1.23 M / 0.062 M | 0.15 M | 3.68 M / 0.41 M |
| 2/5 2 dB | 2.0 | 0.90 M / 0.049 M | 0.09 M | 0.60 M / 0.08 M |
| 1/2 2 dB | 2.8 | 1.07 M / 0.059 M | 0.13 M | 0.74 M / 0.08 M |
| 1/2 4 dB | 1.2 | 0.71 M / 0.045 M | 0.08 M | 0.55 M / 0.07 M |

With the parallel CRC search the pilot receivers need 0.03–0.07 M MACs per core: blind costs 4.4–9× more per core
at R = 1/10 and 0.15 (every SNR), 6.6× at R = 2/5 0.5 dB, and about 1.6× above the waterfall at R = 2/5 and 1/2. Blind's own serial decodes (the fast path's decode + code-aided retry, the
candidate decodes at R = 1/10 and 0.15) are still counted one at a time; at R = 2/5 and 1/2 its joint decode already
runs 4 cells at once. The CNN estimator (classification + refinement) alone costs about 9 M MACs in total.

## 7.6 A hard cap on the MACs of a packet
The search stops at its first accepted decode, so a cap C on the MACs of a packet turns exactly the right decodes
that needed more than C into errors (histograms of the right decodes, `pg_` per core and `mg_` total in
`small_rx`). BLER without and with a cap:

| Rate / SNR | no cap | per core ≤ 0.5 M | ≤ 1 M | ≤ 3 M | total ≤ 3 M | ≤ 10 M | ≤ 30 M |
|---|---|---|---|---|---|---|---|
| 1/10 −5 dB | 3.3·10⁻⁴ | 3.1·10⁻² | 1.1·10⁻³ | 7.9·10⁻⁴ | 0.72 | 1.8·10⁻³ | 8.3·10⁻⁴ |
| 1/10 −4 dB | 0 | 1.5·10⁻² | 3.3·10⁻⁶ | 0 | 0.60 | 6.0·10⁻⁵ | 0 |
| 0.15 −3 dB | 9.5·10⁻⁵ | 8.4·10⁻² | 2.9·10⁻⁴ | 2.2·10⁻⁴ | 0.71 | 5.0·10⁻⁴ | 2.2·10⁻⁴ |
| 0.15 −2 dB | 0 | 1.7·10⁻² | 9.5·10⁻⁶ | 0 | 0.62 | 8.1·10⁻⁵ | 0 |
| 2/5 1 dB | 4.5·10⁻⁵ | 2.9·10⁻² | 3.9·10⁻⁴ | 2.3·10⁻⁴ | 0.22 | 2.4·10⁻² | 2.8·10⁻⁴ |
| 2/5 1.5 dB | 0 | 6.3·10⁻³ | 5·10⁻⁶ | 5·10⁻⁶ | 8.6·10⁻² | 4.7·10⁻³ | 5·10⁻⁶ |
| 1/2 2 dB | 1.5·10⁻⁴ | 3.7·10⁻³ | 3.2·10⁻⁴ | 2.0·10⁻⁴ | 2.3·10⁻² | 9.6·10⁻⁴ | 2.1·10⁻⁴ |
| 1/2 2.5 dB | 5·10⁻⁶ | 2.2·10⁻⁴ | 5·10⁻⁶ | 5·10⁻⁶ | 2.8·10⁻³ | 5·10⁻⁶ | 5·10⁻⁶ |

(100k–420k packets per point; the cap runs are separate from 7.4, so their uncapped BLER differs within noise.)
- One SNR step above the waterfall, a cap of **1 M MACs per core** costs at most ~10⁻⁵; in the waterfall the
  slow tail (rescue) matters and even 3 M per core triples the BLER.
- A cap on the **total** MACs is much worse at the same budget per packet: the search spreads its work over
  the cores, so the total grows ~10× faster than the per-core cost.
- Figures: `est3/plots/bler_vs_cap_R*.png` (also in [presentation/](presentation/)).

## 7.7 Worst case
Noise-only packets, and failures that exhaust the search, cost up to about 400 M MACs in total (R = 2/5, 1/2). A
real modem needs a cap with a "no packet" decision there (7.6 gives its BLER cost; not implemented in the receiver).
