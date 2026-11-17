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

The table is the presentation receiver. The testing receiver (README, "Current state"; run.py `testing_s11g`) changes
four rows at R = 1/10, 0.15: fast path off at SNR <= 0 dB; R = 0.15 uses 4 phases below 0.5 dB and 2 from +1 dB;
speculative decode `spec11` below 1/10 −3.5 dB / 0.15 −2.5 dB; `q_fix` at every rate. The reasons are in 8.1a.

## 8.1a Why each threshold has its value (the measured evidence)
"Set by design" means no sweep of that value is stored in the repo; the value comes from an argument or an older
receiver. Packet counts are per arm; "paired" = the same packets in both arms.

| Threshold | Value | Evidence | Alternatives tried |
|---|---|---|---|
| Checkpoint z-test drop τ, kept cells k_min | τ = −0.5 (1/10), −1 (2/5, 1/2); k_min = 16 | Offline replay of stored partial path metrics (`blind/smoke/pm_traj_report.py`), sweep τ ∈ {−1, −0.5, 0, 0.5, 1} × k_min ∈ {8, 16, 32}, rule: true cell lost <= 0.1 % (`blind_ber.py`). Work with coarse start 0.515 → 0.417 (1/10), 0.290 → 0.246 (2/5), 0.234 → 0.177 (1/2). The printed sweep table is not stored | τ = +1, one checkpoint (1/10 −5 dB): BLER 6.7e-4 vs 3.9e-4 for τ = −0.5 with checkpoints ½ + ¾ (10.5 M vs 8.6 M MACs). τ = 0 with k_min = 8: loses the true cell |
| Early win | z > 6 | Replay: z > 6 is almost never a wrong cell (swept 6 … 20; numbers not stored) | z > 4 (64k paired): same BLER (9 vs 8 errors at 1/10 −5 dB, 273 vs 273 at 0.15 −4 dB), total −13 % but per core +6 % (1/10 −4 dB), +5 % (0.15 −3 dB): dropped (DEAD_ENDS) |
| Candidates after the last checkpoint | z > 4 (at most 4), then the 32 best by path metric | z0 = 4 by design: a wrong cell (about Gaussian z) passes with probability 3e-5, the true cell sits at z ≈ 10. 68-71 % of failures at 1/10 −5 dB had the true cell at z <= 4, which the best-32 stage recovers (BLER 2.0e-3 → 1.2e-3 in the earlier ±0.2 receiver). The cap of 4 is set by design | — |
| Batch block rejected | best z < 5 at the first checkpoint (1/10; pilots 3) | diag-b, 1/10 −5 dB, 40k: 47 / 47 / 47 / 47 errors with and without batches, z 3 / 5, blocks of 32 / 64; batches cut total MACs 30-45 % at no BLER cost. z 5 vs 3 is a BLER tie; no MAC comparison between them is stored | Hard top-K cut by the prior: true cell outside the top 64 in 63 % of packets, BLER 0.5 |
| Checkpoint NN cut | cumulative probability 1 − 10⁻³, at least 8 cells | 3000 packets per point: 2/5 0.5 dB keeps 69 cells, 0 true cells missed, work 0.379; 2/5 1 dB 14 cells, 0 missed; 1/2 2 dB 24 cells, 0 missed, work 0.237 | 1 − 10⁻²: 27.5 cells but misses 0.17 % (2/5), 0.07 % (1/2). 1 − 10⁻⁴: 133 cells, work 0.499. At least 16 instead of 8: work 0.388 / 0.249 for the same misses |
| 4th-power prior weight w₄ | 0.1 / ⅓ / 1 at −5 / −2 / +1 dB | Set by design (inherited from the ±0.2 study). Context: at 1/10 the 4th-power periodogram is almost uninformative (true cell mean rank ~90 of 201), at 2/5 rank 12-25 of 401, at 1/2 ~5 | — |
| Coarse start, phase pruning | stride 2; best 2 phases per cell from ½ | diag-c, 1/10 −5 dB, 40k: phase_keep 2 gives 10 vs 9 errors at 4.15 vs 5.99 M MACs (−31 %) | Stride 3: 148 errors in 3200 packets. Joining only the top 16 / 8 neighbours: 37 / 43 errors vs 9 (×5 at 200k) |
| Grid step (1/10) | 4 STEP at every SNR | Widening to 6 / 8 STEP above −2 dB gave BLER 1.9e-3 at 0 dB; 4 STEP: 0 errors in 100k per point | 6 or 3 STEP (testing): BLER ×5-70 and more MACs |
| Re-encoding check | max(0.12, ½·√(s/(1+s)), RHO_N·√(s/(1+s))) | 06, 6.2: RHO_N is midway between the lowest correct pass and the highest false pass, per rate and SNR (calibration table there) | ½·√(s/(1+s)) alone ("rho_min") is far too loose: false passes reached ρ = 0.65 vs a threshold of 0.37 (2/5 1 dB) |
| Fast path off (testing receiver) | SNR <= 0 dB at 1/10, 0.15 (`s0_snr = 0.5`); kept at 2/5, 1/2 | Paired, per core: 1/10 −30 / −37 / −38 / −37 / −30 % at −5 / −4 / −3 / −1 / 0 dB; 0.15 −15 / −35 / −35 / −26 % at −4 / −3 / −1 / 0 dB, but +6 % at +1 dB, so the switch sits between 0 and +1 dB. BLER the same (8 vs 8, 275 vs 273, 7 vs 7 errors) | Off at 2/5, 1/2 (32k paired): 0 fixed / 17 broken at 2/5 0.5 dB (p = 1.5e-5), per core +22 % (2/5), +278 … +316 % (1/2) |
| Phases at R = 0.15 (testing receiver) | 4 below 0.5 dB, 2 from +1 dB | Paired 400k: −1 dB 72 → 0 errors (72 fixed / 0 broken), per core −5 %; 0 dB 9 → 1, per core +1 %. +1 dB: 0 errors in 64k both ways, 4 phases cost +2.1 % per core, +10 % total | 2 phases from −1 dB (presentation receiver): the 143 / 880k error bump at −1 dB. 2 phases at 1/10: BLER ×20 |
| Speculative decode (testing receiver) | 4 < z <= 6, accepted at ρ > 1.1 × threshold | Plain spec at the normal threshold (1/10 −5 dB, 400k): its 2 undetected errors had ρ / threshold in [1.0, 1.1), where only 573 of 107,317 correct passes (0.5 %) lie. Confirmed on fresh packets: 400k 98 vs 98 errors, 0 discordant, undetected 1 = base, per core −14.4 %; 1e6: 209 vs 209, undetected 2 vs 2, −14.5 % | Plain spec (factor 1.0): 1 broken packet, 2 undetected |
| spec11 SNR gate | below −3.5 dB (1/10), −2.5 dB (0.15) | 64k paired sweep, per core: 1/10 −14.6 / −10.1 / −3.6 % at −5 / −4.5 / −4 dB, +3.7 % at −3 dB; 0.15 −7.0 / −8.1 / −4.1 % at −4 / −3.5 / −3 dB, +0.5 % at −2.5 dB, +2.8 … +3.6 % above. Gate = between the last gain and the first loss | — |
| Hard MAC cap (option) | 2 M per core (1/10, 0.15), 1 M (2/5, 1/2) | 07, 7.6 cap plots (0.5 … 10 M). Paired: 0.15 −2.5 dB 400k 2 → 4 errors; 2/5 1.5 dB 400k 0 → 3; 1/2 2.5 dB 128k 0 → 0; mean MACs within 0.1 %; noise-only packets stop at the cap instead of ~16.5 M | 1 M per core at 1/10 −5 dB: BLER 3.3e-4 → 1.1e-3; a cap on total MACs is much worse |
| SNR margin on the check (option) | `re_margin` 1 dB | SNR underestimated by 1 dB: 3-5 undetected in 3200-6400 packets; with the margin none, and the few correct packets rejected (0 at 1/10, 4 of 6400 at 2/5) were all recovered. Not used in the final runs (SNR known) | — |

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
- **A fairer pilot search (2026-11-13, `testing/results/expected_fair.md`).** The floor is mostly the search ORDER
  (neighbours tried in |k| order, so wrong passes come before the right CFO). With the order set by the list-1 SC
  metric ("PM+all": decode at the estimate, then every neighbour best-first), on the same 480k packets per SNR the
  waterfall BLER is unchanged, the floor falls 2–5× to 2–10·10⁻⁶ (undetected 3–5× fewer) and per core rises 8–36 %
  (0.04–0.09 M, still 2–6× below blind; totals −8 … +15 %). The `cmp_*` plots now use this search as the pilot
  reference. Blind still has 0 errors above the waterfall at the same packet counts, so its edge there shrinks to
  ~5·10⁻⁶ BLER plus the pilots' overhead (12.5 % of the packet in this inside-the-packet framing, 8.3); its MAC cost per core stays 2–6× higher.
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

## 8.2a Fair comparison: pilots outside the packet, energy charged (est4, 2026-11-15)
The presentation figures `presentation/bler_fair_R*.png` (`testing/plot_pres.py`; numbers in
`testing/results/expected_est4.md`). The tables above put 128 pilots INSIDE the packet and do not charge their energy.
Here the pilot receivers keep the whole 1024-symbol packet for data (N = 2048, CRC-16, as blind) and send their known
symbols as EXTRA symbols, all at the same Es; the SNR axis is the burst energy per data symbol,
SNR = Es/N0 + 10 log10((1024 + Nk) / 1024): +0.47 dB for 116 known symbols, +0.51 dB for 128, +0.13 dB for 32.
Same back-end for all (pre-MF correction, CA-SCL-8, the re-encoding check, the fair metric-ordered CRC search), the same
data / CFO / noise; 480k packets per SNR for the pilot receivers.

Receivers:
| Receiver | Known symbols | CFO estimate |
|---|---|---|
| Blind | none | 08, 8.1 (testing receiver) |
| DVB-RCS2 ID 13 (EN 301 545-2, scaled) | preamble 32, 53 × (19 data + 1 pilot), postamble 31: 116 | Rife-Boorstyn FFT over all known symbols + parabolic interpolation |
| 128 preamble, ML / Mengali-Morelli | 128 | ML direct (FFT 512 + 2 Newton) / M&M |
| 64 + 64 pre / post, joint ML | 128 | joint ML over both blocks, CRC search over the ±3 ML lobes |
| DVB-RCS2 16 + 16 pre / post | 32 | 4th-power FFT over the burst (non-data-aided), π/2 ambiguity from the known symbols |
| Genie | none | true CFO and phase, one decode (lower bound) |

SNR [dB] where the BLER crosses a target (log-linear interpolation; blind = the adopted testing-receiver runs,
`plot_e4.blind`, 64k-1.4M packets per SNR, about ±0.1 dB at 1/10 and 0.15; the presentation BLER curves pool all runs of
the same receiver, which moves blind by <= 0.07 dB: 1/10 -4.83, 0.15 -3.62 / -2.97, 1/2 1.78; genie at 1/10 interpolates
with its -5.5 dB point, which is not plotted; CIs and the raw / charged-axis / Pareto figures: `testing/results/final_table.md`):
(Blind column updated 2026-11-17 to the adopted testing receiver: `testing_s11g` at 1/10, 0.15; q_fix + early stop at
2/5, 1/2. All 31 deployed-system competitors: [testing/results/scoreboard.md](testing/results/scoreboard.md).)
| Rate, BLER | Blind | DVB-RCS2 ID 13 | 128 preamble, ML | 64 + 64, joint ML | 16 + 16, 4th power | Genie |
|---|---|---|---|---|---|---|
| 1/10, 10⁻⁴ | **−4.78** | −4.09 | −4.68 | −2.87 | fails | −5.19 |
| 0.15, 10⁻³ | **−3.60** | −3.45 | −3.44 | −3.34 | fails | −3.91 |
| 0.15, 10⁻⁴ | −2.93 | **−3.12** | **−3.12** | −2.71 | fails | −3.59 |
| 2/5, 10⁻³ | **0.58** | 1.10 | 1.16 | 1.12 | fails | 0.64 |
| 1/2, 10⁻³ | **1.73** | 2.33 | 2.41 | 2.38 | 2.77 | 1.90 |

**Reading it**
- With the pilot energy charged, the waterfall gap of 8.2 ("blind loses at the lowest SNRs") is gone: blind is the best
  receiver at R = 1/10 (0.10 dB ahead of the 128-preamble ML at 10⁻⁴), ties at R = 0.15 (0.15 dB ahead at 10⁻³,
  0.19 dB behind at 10⁻⁴: the pilot waterfalls are steeper) and is 0.5-0.6 dB better at R = 2/5 and 1/2 (2026-11-17).
- The cost is complexity, not BLER: blind needs 2-12× the MACs per core of the pilot receivers (07, 7.5b).
- DVB-RCS2 ID 13 is the strongest and cheapest pilot receiver. Its single-symbol pilots every 20 symbols resolve only
  |f| < 0.025, so at R = 1/10 −5 dB 0.2 % of packets fall outside its CFO window (881 errors per 480k).
- The 128-preamble receivers keep a floor of wrong CRC passes: 2-6 per 480k at every SNR above the waterfall
  (pooled: about 3-7·10⁻⁶); DVB-RCS2 ID 13 and 64 + 64 have none. In the figures that floor is pooled over the flat
  region (the legend gives the count) instead of drawn point by point.
- The 4th-power estimator with 32 known symbols fails at low SNR: BLER 0.5-0.9 below 0 dB at every rate.
- The 64 + 64 joint ML picks a wrong lobe (spacing 1/1088) in about 55-60 % of packets below −4 dB; the CRC search over
  ±3 lobes recovers most of it, but it is the weakest ML layout at R = 1/10.
- Phase noise (Wiener, linewidth × Ts, per-symbol SNR, pilot energy not charged; 64k per point): at 10⁻⁴ the DVB-RCS2
  receiver with Kalman phase tracking is the best pilot receiver and beats blind at 0.15 and 2/5 (94 vs 144 and 1967 vs
  5312 errors) but loses at 1/10 (168 vs 42); every pilot receiver with a constant phase is worse than blind. Blind's
  code-aided phase tracking (`pns`) cuts its BLER 10-23 % at 10⁻⁴ and 9-22 % at 3·10⁻⁴, never breaks a packet and lowers
  MACs per core (`testing/results/expected_pns.md`).

## 8.3 Throughput: two framings, do not mix them
**Which framing applies to which result.** The 8.2 tables (est3) put the 128 pilots INSIDE the 1024-symbol packet: the
pilot receivers carry fewer data bits and the SNR axis is the same for all. The 8.2a comparison (est4, the presentation
figures) puts the pilots OUTSIDE the packet: every receiver carries the same data, the pilot energy is charged on the
SNR axis, and the remaining cost is airtime. The "12.5 %" below belongs ONLY to the inside-the-packet framing; with the
8.2a curves the airtime cost is 11.1 % for 128 known symbols (10.2 % for 116), reported separately from the energy.

**Inside the packet (8.2, est3):**
The pilot receivers' 128 known symbols sit inside the 1024-symbol packet, so they carry no data. Information bits per packet:

$$T = A\,(1-\mathrm{BLER})\cdot\frac{1024 - n_{\text{pilots}}}{1024}.$$

- **The pilots' factor:** for 128 pilots it is 0.875, a **12.5 % throughput loss** at any BLER.
- **Blind's factor:** 1.
- **The BLER term:** at the operating points (BLER ≤ 10⁻³), (1 − BLER) changes T by at most 0.1 %.

So blind delivers about 12–14 % more data per packet than every 128-pilot receiver here. That includes the ML + re-encoding check receiver, which has lower BLER at R = 1/10 −5 dB (6.5·10⁻⁵ vs 2.1·10⁻⁴).

The pilot receivers would beat blind on throughput only where blind's BLER is more than about 12 % higher in absolute terms, deep in the waterfall.

**Matching throughput instead:** a pilot system that keeps the same data bits needs a code rate 1024/896 times higher, which costs roughly 0.5–0.7 dB of SNR.

**Outside the packet (8.2a, est4; the framing of the presentation figures):** the pilot system keeps every data bit but sends 1024 + Nk symbols, so its
airtime throughput is 1024 / (1024 + Nk) of blind's: 0.898 for 116 known symbols, 0.889 for 128, 0.970 for 32; the extra
energy is charged on the SNR axis of 8.2a.

## 8.4 Limits of what was simulated
- **Ideal synchronisation:** timing and SNR are known. A 1 dB SNR error was tested, and a 1 dB threshold margin fixes it.
- **Static channel:** AWGN only, with a static CFO over the packet in 8.2 and 8.2a. Wiener phase noise was tested
  separately (8.2a, last point; `testing/results/expected_est4.md`, `expected_pns.md`); CFO drift was not.
- **Floating-point arithmetic.**
- **No worst-case MAC cap** in the receiver (7.6 gives the BLER cost of one).
- **PiCode's assumption:** it requires u_{N−1} to be an information bit and no shortening. With 5G-NR-style rate matching by shortening, 4 phase branches would be needed in the final decodes.
