# Confirmation runs (cnf*, submitted 2026-11-13 02:16): expected values, written before any result

## Receivers

- **Presentation** = `S blind final v2`, the current blind receiver.
- **Testing** = `nofast15`: fast path off at SNR <= 0 dB, 4 phases at R = 0.15.
- **MACs** are mean M per packet on the standard 32-core model:
  - "per core" = crit_par;
  - "total" = all MACs.

## Where the numbers come from

**Presentation BLER.** Measured, from the merged `small_cfo/blind/results/blind_ber.json`.

**Presentation MACs, pre-fix.** Measured with the old phase-accounting.

**Presentation MACs, "expected fixed".** The pre-fix value plus the analyst's undercount bracket (`report_cmp.md` section 3):
- per core +17...+20 % at 1/10, +13...+20 % at 0.15;
- total about +20 %;
- 0 at the 2-phase points (1/10 -1 and 0 dB; 0.15 -1, 0 and +1 dB).

**Testing change.** The S paired results, re-based to the fixed accounting on both sides (`report_cmp.md`). The S runs
had no points at:
- 1/10 -4.5 / -2 dB: taken from the neighbouring points;
- 0.15 -3.5 / -2.5 / -2 dB: interpolated.

**Testing BLER.** Unchanged wherever the phase count is the same (1/10 everywhere, 0.15 <= -2 dB):
- S runs: 8 vs 8, 275 vs 273 and 7 vs 7 errors.
- At 0.15 -1 / 0 dB, nph15 removes the 2-phase bump: 72 -> 0 and 9 -> 1 errors per 400k (K test).

**Not yet in this table:** the 4-at-once counters (d4a / d4b). The expectation for d4a is about -25 % per core at 0.15 -4 dB and -1...-3 % elsewhere.

### R = 1/10

| SNR [dB] | BLER presentation (measured) | BLER testing (expected) | per core presentation pre-fix -> expected fixed [M] | per core testing expected [M] | change | total presentation expected fixed [M] | total testing expected [M] | change |
|---|---|---|---|---|---|---|---|---|
| -5 | 2.08e-04 (88/424k) | same as presentation | 0.314 -> 0.377 | 0.279 | -26 % | 5.00 | 4.40 | -12 % |
| -4.5 | 3.39e-05 (19/560k) | same as presentation | 0.276 -> 0.328 | 0.233 | -29 % | 4.10 | 3.48 | -15 % |
| -4 | 1.60e-06 (1/624k) | same as presentation | 0.258 -> 0.304 | 0.210 | -31 % | 3.59 | 2.98 | -17 % |
| -3 | 0 / 260k | same as presentation | 0.243 -> 0.284 | 0.193 | -32 % | 3.20 | 2.63 | -18 % |
| -2 | 0 / 160k | same as presentation | 0.232 -> 0.271 | 0.185 | -32 % | 3.03 | 2.49 | -18 % |
| -1 | 0 / 160k | same as presentation | 0.202 -> 0.202 | 0.127 | -37 % | 1.94 | 1.59 | -18 % |
| 0 | 0 / 160k | same as presentation | 0.154 -> 0.154 | 0.108 | -30 % | 1.44 | 1.31 | -9 % |

### R = 0.15

| SNR [dB] | BLER presentation (measured) | BLER testing (expected) | per core presentation pre-fix -> expected fixed [M] | per core testing expected [M] | change | total presentation expected fixed [M] | total testing expected [M] | change |
|---|---|---|---|---|---|---|---|---|
| -4 | 4.15e-03 (2175/524k) | same as presentation | 0.640 -> 0.726 | 0.639 | -12 % | 8.72 | 8.19 | -6 % |
| -3.5 | 6.76e-04 (230/340k) | same as presentation | 0.349 -> 0.405 | 0.316 | -22 % | 5.07 | 4.51 | -11 % |
| -3 | 1.10e-04 (93/844k) | same as presentation | 0.282 -> 0.337 | 0.239 | -29 % | 3.97 | 3.37 | -15 % |
| -2.5 | 9.09e-06 (6/660k) | same as presentation | 0.261 -> 0.311 | 0.221 | -29 % | 3.48 | 2.96 | -15 % |
| -2 | 0 / 780k | same as presentation | 0.250 -> 0.297 | 0.211 | -29 % | 3.24 | 2.76 | -15 % |
| -1 | 1.62e-04 (143/880k) | < 1e-5 (nph15 removes the 2-phase bump) | 0.236 -> 0.236 | 0.179 | -24 % | 2.35 | 2.61 | +11 % |
| 0 | 1.79e-05 (14/780k) | about 3e-6 | 0.169 -> 0.169 | 0.149 | -12 % | 1.59 | 2.13 | +34 % |
| 1 | 0 / 780k | < 1e-5 | 0.099 -> 0.099 | 0.108 | +9 % | 0.88 | 0.97 | +10 % |

## After the runs

When the runs finish, the final table adds measured columns next to these:
- presentation with the fixed accounting (64k packets, parts t-cnf10d / t-cnf15f, paired on the same packets);
- testing BLER and MACs (t-cnf10a/b/c, t-cnf15a/b/c/d/e).

Each measured value gets a hit / miss mark against this file.

## Measured (2026-11-13)

Source: `py BLIND_IMPLEMENTATION/testing/agg_cnf.py` (tables, side arms) and `agg_cnf_prefix.py` (pre-fix -> fixed on
the same packets). No simulation in either.

**Completeness.** All 7 logs have `EVAL DONE` for every run and `ALL DONE`, no `Traceback`. Every receiver / point has
the requested number of chunks (4000 packets each), no chunk seed is duplicated, and nothing is missing:
- 1/10: testing 400k at -5 / -4.5 / -4, 160k at -3 ... 0; presentation 64k at every point;
- 0.15: testing 64k at -4, 128k at -3.5, 400k at -3 ... 0, 64k at +1; presentation 64k at every point;
- 2/5, 1/2: 32k per arm.

**How to read the tables.**
- *BLER pres*: presentation with the fixed accounting, 64k packets (t-cnf10d / t-cnf15d / t-cnf15f).
- *BLER test*: `T nofast15`, all of its packets. In brackets, the paired 64k comparison: the 16 chunks that both arms
  ran, matched packet by packet (chunk_seed + fe_idx). It gives pres errors vs test errors, then the McNemar
  discordant counts "fixed / broken" (fixed = presentation error that testing gets right) and the exact p.
- *Per core / total*: mean M per packet. The test value uses all of its packets. *Change* is paired, on the common 64k
  (all packets vs the 64k subset differ by <= 0.004 M per core).
- *d4a / d4b*: testing, per core, with the change vs crit_par in brackets.
- *hit / miss*: 5 marks per row: BLER, per core pres, per core test, total pres, total test.
  - MACs: hit = within ±10 % of the expected value.
  - BLER "same as presentation": exact conditional binomial test vs the merged presentation count, p > 0.05.
  - BLER "< 1e-5" / "about 3e-6": the 95 % Clopper-Pearson interval reaches the expected value.

### R = 1/10 (measured)

| SNR [dB] | BLER pres | BLER test | per core pres fixed [M] | per core test [M] | change | total pres [M] | total test [M] | change | d4a test [M] | d4b test [M] | hit / miss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| -5 | 1.25e-04 (8/64k) | 2.20e-04 (88/400k) [paired 8 vs 8: 0 / 0] | 0.379 | 0.289 | -25 % | 5.33 | 4.88 | -9 % | 0.283 (-2 %) | 0.281 (-3 %) | 4/5: total test **miss** (+11 %) |
| -4.5 | 9.4e-05 (6/64k) | 2.50e-05 (10/400k) [6 vs 6: 0 / 0] | 0.334 | 0.238 | -28 % | 4.34 | 3.83 | -11 % | 0.237 (-0 %) | 0.237 (-0 %) | 4/5: total test **miss** (+10.1 %) |
| -4 | < 4.7e-05 (0/64k) | 2.5e-06 (1/400k) [0 vs 0] | 0.306 | 0.212 | -31 % | 3.73 | 3.23 | -13 % | 0.212 (-0 %) | 0.212 (-0 %) | 5/5 hit |
| -3 | < 4.7e-05 (0/64k) | < 1.9e-05 (0/160k) [0 vs 0] | 0.284 | 0.192 | -32 % | 3.28 | 2.80 | -15 % | 0.192 (0 %) | 0.192 (-0 %) | 5/5 hit |
| -2 | < 4.7e-05 (0/64k) | < 1.9e-05 (0/160k) [0 vs 0] | 0.270 | 0.184 | -32 % | 3.08 | 2.66 | -14 % | 0.184 (0 %) | 0.184 (-0 %) | 5/5 hit |
| -1 | < 4.7e-05 (0/64k) | < 1.9e-05 (0/160k) [0 vs 0] | 0.202 | 0.127 | -37 % | 1.95 | 1.59 | -18 % | 0.127 (0 %) | 0.127 (-0 %) | 5/5 hit |
| 0 | < 4.7e-05 (0/64k) | < 1.9e-05 (0/160k) [0 vs 0] | 0.153 | 0.108 | -30 % | 1.44 | 1.30 | -9 % | 0.108 (0 %) | 0.108 (-0 %) | 5/5 hit |

- **BLER.** Testing is consistent with the merged presentation at every point (p = 0.71 / 0.46 / 1.00 at -5 / -4.5 / -4).
  On the paired 64k it never fixed or broke a packet. There are no undetected errors in either arm.
  From -3 dB up there are no errors at all, so these points support only upper bounds.
- **Per-core change.** It matches the expectation within 1 percentage point (-25 / -28 / -31 / -32 / -32 / -37 / -30 % vs
  -26 / -29 / -31 / -32 / -32 / -37 / -30 %).
- **Total change.** It is smaller than expected below -1 dB (-9 / -11 / -13 / -15 / -14 % vs -12 / -15 / -17 / -18 / -18 %).
  Both absolute totals are higher than expected, see the bracket check below.
- **Per-core tail (testing).** At -5 dB the 99 / 99.9 % / max are 0.56 / 1.12 / 39.8 M (presentation 0.71 / 1.00 / 35.5 M);
  from -4 dB the 99.9 % is <= 0.71 M.

### R = 0.15 (measured)

| SNR [dB] | BLER pres | BLER test | per core pres fixed [M] | per core test [M] | change | total pres [M] | total test [M] | change | d4a test [M] | d4b test [M] | hit / miss |
|---|---|---|---|---|---|---|---|---|---|---|---|
| -4 | 4.27e-03 (273/64k) | 4.30e-03 (275/64k) [273 vs 275: 0 / 2, p = 0.50] | 0.733 | 0.636 | -13 % | 8.86 | 8.40 | -5 % | 0.491 (-23 %) | 0.431 (-32 %) | 5/5 hit |
| -3.5 | 6.4e-04 (41/64k) | 6.25e-04 (80/128k) [41 vs 42: 0 / 1] | 0.411 | 0.312 | -24 % | 5.35 | 4.86 | -9 % | 0.293 (-6 %) | 0.285 (-8 %) | 5/5 hit |
| -3 | 1.09e-04 (7/64k) | 1.15e-04 (46/400k) [7 vs 7: 0 / 0] | 0.335 | 0.239 | -29 % | 4.14 | 3.69 | -11 % | 0.237 (-1 %) | 0.236 (-1 %) | 5/5 hit |
| -2.5 | < 4.7e-05 (0/64k) | 1.0e-05 (4/400k) [0 vs 0] | 0.307 | 0.212 | -31 % | 3.58 | 3.14 | -13 % | 0.212 (-0 %) | 0.211 (-0 %) | 5/5 hit |
| -2 | < 4.7e-05 (0/64k) | < 7.5e-06 (0/400k) [0 vs 0] | 0.292 | 0.199 | -32 % | 3.32 | 2.89 | -13 % | 0.199 (0 %) | 0.199 (-0 %) | 5/5 hit |
| -1 | 1.88e-04 (12/64k) | < 7.5e-06 (0/400k) [12 vs 0: **12 / 0**, p = 4.9e-4] | 0.239 | 0.180 | -25 % | 2.36 | 2.59 | +10 % | 0.180 (0 %) | 0.180 (-0 %) | 5/5 hit |
| 0 | 3.1e-05 (2/64k) | < 7.5e-06 (0/400k) [2 vs 0: 2 / 0, p = 0.50] | 0.171 | 0.148 | -13 % | 1.60 | 2.13 | +33 % | 0.148 (0 %) | 0.148 (-0 %) | 5/5 hit |
| 1 | < 4.7e-05 (0/64k) | < 4.7e-05 (0/64k) [0 vs 0] | 0.098 | 0.106 | +8 % | 0.88 | 1.05 | +20 % | 0.106 (0 %) | 0.106 (0 %) | 5/5 hit |

- **BLER, -4 ... -2.5 dB.** Testing is consistent with the merged presentation (p = 0.58 / 0.57 / 0.86 / 1.00). The paired
  64k shows 0 fixed and 3 broken over -4 / -3.5 dB (2 + 1, not significant).
- **BLER, -1 dB.** nph15 removes the 2-phase bump: 0/400k vs 143/880k merged. On the paired 64k it fixed 12 packets and
  broke none.
- **BLER, 0 dB.** 0/400k (95 % upper bound 9.2e-6) is consistent with "about 3e-6", but it does not resolve it.
  The K test had 1/400k.
- **BLER, +1 dB.** Testing has only 64k packets: no BLER claim below 4.7e-5.
- **Undetected error.** One in testing at -3 dB (origin acc_win_main_wrong, chunk 64, outside the paired chunks): 1/400k,
  CI [6e-8, 1.4e-5]. The presentation 64k arms have 0 undetected errors.
- **d4a at -4 dB.** -23 % per core (expected about -25 %): hit. Elsewhere -0 ... -1 %, -6 % at -3.5 dB (expected -1 ... -3 %).
- **MAC changes.** Per core within 2 percentage points of the expectation. Total also within 2 points, except +1 dB:
  +20 % vs +10 % expected (the test total 1.05 is still a hit against 0.97).
- **Per-core tail (testing).** At -4 dB the 99 / 99.9 % / max are 8.9 / 39.8 / 39.8 M (presentation 8.9 / 39.8 / 44.7 M).
  At -3.5 dB the 99.9 % is 17.8 M (presentation 20.0 M). From -3 dB the 99.9 % is <= 0.79 M. Single packets near 40 M
  still occur at -3 and -2.5 dB.

### Was the undercount bracket right?

Two comparisons. The first is the bracket in this file vs the 64k fixed run (different packets from the pre-fix
numbers). The second is exact: the same receiver on the same packets, old S parts nf10a / nf15a / nf15b vs the cnf parts,
chunks matched by the packet-only signature (16 of 16 matched at each point). Errors and decode counts are identical in
the second comparison, so only the accounting differs.

| R | SNR | bracket (per core) | fixed / pre-fix (64k vs file) | same packets: per core | same packets: total (bracket "about +20 %") |
|---|---|---|---|---|---|
| 1/10 | -5 | +17 ... +20 % | +21 % | 0.3102 -> 0.3787, **+22.1 %** (above) | 4.13 -> 5.33, **+28.9 %** |
| 1/10 | -4.5 | +17 ... +20 % | +21 % | - | - |
| 1/10 | -4 | +17 ... +20 % | +19 % | 0.2577 -> 0.3059, +18.7 % | 2.99 -> 3.73, **+24.8 %** |
| 1/10 | -3 / -2 | +17 ... +20 % | +17 / +16 % | - | - |
| 1/10 | -1 / 0 | 0 | -0 / -1 % | - | - |
| 0.15 | -4 | +13 ... +20 % | +15 % | 0.6497 -> 0.7333, +12.9 % (at the edge) | 7.37 -> 8.86, +20.3 % |
| 0.15 | -3.5 / -3 / -2.5 / -2 | +13 ... +20 % | +18 / +19 / +17 / +17 % | (-3 dB) 0.2817 -> 0.3352, +19.0 % | (-3 dB) 3.30 -> 4.14, **+25.6 %** |
| 0.15 | -1 / 0 / +1 | 0 | +1 / +1 / -1 % | - | - |

- **Per core.** The bracket held, except at 1/10 -5 dB: there the undercount was +22 %, about 2 points above the bracket,
  and the 64k run also reads +21 % at -4.5 dB.
- **Total.** The "about +20 %" was too low at 1/10 and at 0.15 -3 dB (+25 ... +29 %), but right at 0.15 -4 dB.
  This explains why the measured totals (both arms) come out 5 ... 11 % above the expected column at 1/10. It also
  explains the two "total test" misses.

### (a) nofast_spec_t vs nofast15, 1/10 -5 dB (t-cnf10a, the same 400k packets)

| receiver | errors | undetected (origin) | per core [M] | total [M] | d4a [M] | dec / pk | per core 99 / 99.9 % / max [M] |
|---|---|---|---|---|---|---|---|
| nofast15 | 88/400k | 0 | 0.289 | 4.88 | 0.283 | 1.395 | 0.56 / 1.12 / 39.8 |
| nofast_spec_t | 90/400k | 2 (acc_spec_main_wrong = 2; spec_pass_wrong = 2) | 0.254 (-12 %) | 3.92 (-20 %) | 0.249 | 1.552 | 0.63 / 1.12 / 39.8 |

- **Paired.** 0 fixed / 2 broken (p = 0.50). The 2 broken packets are exactly the 2 undetected errors, both wrong
  decodes accepted by the speculative path. Undetected rate: 2/400k = 5e-6, CI [6e-7, 1.8e-5].
- **Speculative path.** 171 595 speculative decodes, of which 107 319 passed.

### (b) 0.15 +1 dB: nofast15 vs nofast_nph4 vs base10 (t-cnf15e and t-cnf15f, the same 64k packets)

| receiver | errors | per core [M] | total [M] | dec / pk | per core 99 / 99.9 % / max [M] |
|---|---|---|---|---|---|
| base10 (presentation, fixed) | 0/64k | 0.098 | 0.88 | 1.461 | 0.32 / 0.56 / 0.71 |
| nofast15 (fast path on, 4 phases) | 0/64k | 0.106 (+8 %) | 1.05 (+20 %) | 1.445 | 0.40 / 0.56 / 0.89 |
| nofast_nph4 (fast path off, 4 phases) | 0/64k | 0.113 (+15 %; +6 % vs nofast15) | 1.62 (+84 %; +54 % vs nofast15) | 1.011 | 0.28 / 0.50 / 0.79 |

- **Errors.** There are none in any arm (< 4.7e-5 each), so this point compares MACs only.

### (c) 2/5 and 1/2: base vs fast path off (t-cnf25, t-cnf2; 32k paired packets per point)

| R | SNR | base errors | nofast errors | fixed / broken (p) | per core base -> nofast [M] | total base -> nofast [M] |
|---|---|---|---|---|---|---|
| 2/5 | 0.5 | 48 | 65 | 0 / **17** (1.5e-5) | 0.382 -> 0.466 (+22 %) | 3.49 -> 4.85 (+39 %) |
| 2/5 | 1 | 3 | 5 | 0 / 2 (0.50) | 0.130 -> 0.150 (+15 %) | 1.29 -> 2.37 (+83 %) |
| 1/2 | 2 | 1 | 6 | 0 / 5 (0.06) | 0.085 -> 0.322 (+278 %) | 0.745 -> 7.71 (x 10.3) |
| 1/2 | 2.5 | 0 | 0 | 0 / 0 | 0.075 -> 0.313 (+316 %) | 0.580 -> 7.63 (x 13.2) |

- **Effect of turning the fast path off.** At these rates it never fixed a packet: 0 fixed, 24 broken over the 4 points,
  and it raises per core and total MACs at every point. Base is the presentation receiver ("S blind final 2/5, 1/2,
  best-first 32" at 2/5, "S blind final 2/5, 1/2" at 1/2).
  - The 2/5 0.5 dB loss is significant. The 1/2 2 dB loss is borderline (5 vs 0).
  - At 1/2, nofast costs about 7.6 M total and 0.31 M per core whatever the SNR, with only 1.1 ... 1.3 decodes per packet.
- **Not explained.** It is not known why the search without the fast path loses packets that the fast path decodes
  right at 2/5. At 1/10 and 0.15 below 0 dB, nofast broke 0 ... 2 packets.
