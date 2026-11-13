# Testing model vs presentation model vs 128-pilot receivers

Analysis only. Tables: `agg_cmp.py` (run with `BLIND_STUDY=small_cfo`). Plots: `plot_cmp.py` ->
`results/plots/cmp_{bler,macs,macs_total}_R{1_10,0.15,2_5,1_2}.png`. Full table output: `cmp_out.md` (scratchpad
copy, see the session).

**All blind MAC numbers here use the pre-fix accounting.** The phase_keep undercount (section 3) was fixed in
small_rx.py on 2026-11-13 (`old_acct` flag); re-measured plots follow.

## Models

- **Testing model**:
  - R = 1/10: fast path off at SNR <= 0 dB (`T nofast`: nf10a, nf10b).
  - R = 0.15: `T nofast` at -4 and -3 dB, `T nofast_nph4` at -1 and 0 dB, `T nph15` at +1 dB (fast path on there).
- **Presentation model**:
  - the current blind receiver `S blind final v2`;
  - BLER from the merged `small_cfo/blind/results/blind_ber.json` (2026-11-12 19:40);
  - MACs from all parts except the nf baseline arms (duplicate packets).
- **Pilot receivers (128 pilots)**: ML direct, joint ML (Lh = 3) and CNN class. + refinement (the 3 best by pooled
  BLER relative to ML direct), plus M&M.
  - BLER relative to ML direct:

    | Receiver | 1/10 | 0.15 |
    |---|---|---|
    | joint ML | 1.04 | 0.99 |
    | CNN-cr | 1.01 | 1.00 |
    | M&M | 15.5 | 1.15 |

  - MACs from `est3/plots.pilot_macs` (4 decodes at once).
  - ML direct is the cheapest pilot receiver per core at every point.

## 1. MACs per packet (M, pre-fix), testing vs presentation

The paired change (in brackets) is measured on the same 64k packets.

| R | SNR | per core T / P | change | crit_par_h T | total T / P | change | T / ML direct per core |
|---|---|---|---|---|---|---|---|
| 1/10 | -5 | 0.216 / 0.314 | -31.4 % (-30.5) | 0.180 | 3.631 / 4.167 | -12.9 % (-12.1) | 3.19 |
| 1/10 | -4 | 0.163 / 0.258 | -36.5 % (-36.6) | 0.131 | 2.485 / 2.986 | -16.8 % | 2.86 |
| 1/10 | -3 | 0.150 / 0.243 | -38.0 % | 0.119 | 2.187 / 2.668 | -18.0 % | 3.07 |
| 1/10 | -1 | 0.127 / 0.202 | -37.1 % | 0.104 | 1.592 / 1.945 | -18.2 % | 3.36 |
| 1/10 | 0 | 0.108 / 0.154 | -30.0 % (-29.7) | 0.091 | 1.302 / 1.442 | -9.7 % | 3.15 |
| 0.15 | -4 | 0.551 / 0.640 | -13.9 % (-15.2) | 0.509 | 6.888 / 7.283 | -5.4 % (-6.5) | 7.96 |
| 0.15 | -3 | 0.183 / 0.282 | -35.1 % (-34.9) | 0.148 | 2.812 / 3.304 | -14.9 % | 3.19 |
| 0.15 | -1 | 0.145 / 0.236 | -38.7 % (-35.2 vs nph4) | 0.116 | 2.084 / 2.344 | -11.1 % | 3.38 |
| 0.15 | 0 | 0.127 / 0.169 | -24.9 % (-26.0 vs nph4) | 0.104 | 1.821 / 1.589 | **+14.6 %** (+3.1 vs nph4) | 3.33 |
| 0.15 | +1 | 0.101 / 0.099 | **+2.5 %** | 0.095 | 0.973 / 0.881 | **+10.5 %** | 2.92 |

**With the undercount bracket added to both models (per core):**

| R | SNR | change, testing vs presentation |
|---|---|---|
| 1/10 | -5 | -24 to -28 % |
| 1/10 | -4 | -30 to -32 % |
| 1/10 | -3 | -32 % |
| 0.15 | -4 | -11 to -14 % |
| 0.15 | -3 | -29 % |
| 0.15 | -1 | -24 % |
| 0.15 | 0 | -12 % |
| 0.15 | +1 | +8.6 % |

At 2-phase points (1/10 at -1 and 0 dB) there is no undercount.

**Testing vs ML direct per core, with the bracket:**
- 1/10: 3.2-4.2x.
- 0.15: 9.2x at -4 dB, about 4x at -3 to 0 dB, 3.1x at +1 dB.

**R = 2/5 and 1/2** (the testing model equals the presentation model there):
- blind costs 1.4-1.8x ML direct per core from 2/5 1.5 dB and 1/2 2 dB up;
- 2.2x at 2/5 1 dB;
- 6.7x at 2/5 0.5 dB.

## 2. Where it improved

**R = 1/10, -5 to 0 dB: improved everywhere measured.**
- Per core -30 to -38 % (bracketed -24 to -33 %), total -10 to -18 %.
- Errors unchanged: 8 vs 8 at -5 dB, 0 vs 0 elsewhere.

**R = 0.15:**
- **-4 dB:** small gain, per core -14 % and total -6 %. 2 % of packets carry 56 % of the mean cost.
- **-3 dB:** improved, -35 % per core and -15 % total.
- **-1 dB:** per core improved, but the total is probably worse once the 4-phase undercount is charged.
- **0 dB:** per core better, total worse (+15 % vs presentation).
- **+1 dB:** worse, +2.5 % per core and +10.5 % total. Only nph15 differs there.

**Not measured:** 1/10 above 0 dB and the half-dB points.

**BLER:**
- testing 8/64k vs presentation 88/424k at 1/10 -5 dB;
- 275/64k vs 2175/524k at 0.15 -4 dB;
- 0/64k vs 143/880k at 0.15 -1 dB (the 2-phase bump).

Testing zero-error points only show BLER < 4.7e-5.

## 3. Phase-accounting undercount (bracket from stored counters)

**Mechanism.** After the 1/2 checkpoint, cells decoded from 0 to 1/2 were charged 2 phases instead of 4.
- That is 2 m s per cell = 14.6k MACs at 1/10 and 16.0k at 0.15.
- There is nothing missing at 2 phases.

**Bracket.** It comes from solving `passes` and `crit_grid` for the number of undercharged passes. At the 2-phase
points the same equations give consistent values (model check).

**Per-core undercount:**

| R | SNR | presentation | testing |
|---|---|---|---|
| 1/10 | -5 | +19-22 % | +27-32 % |
| 1/10 | -4 | +18-19 % | +28-30 % |
| 1/10 | -3 | +17 % | +27-28 % |
| 0.15 | -4 | +13-14 % | +15-17 % |
| 0.15 | -3 | +19-20 % | +30-31 % |
| 0.15 | -1 | 0 | +24 % |
| 0.15 | 0 | 0 | +17 % |
| 0.15 | +1 | 0 | +6 % |

The total-MAC undercount is only loosely bounded (+1.6 to +47 % at 1/10 -5 dB; nominal +17 to +29 %).

## 4. Step-0 numbers

**Packets >= 1 M per core.**
- At 0.15 -4 dB, testing: 1309/64000 packets carry 56 % of the mean (29 % right-decoded, 27 % failed).
- At 1/10 -5 dB: 46 packets carry 4 %.

**Blind decodes 4 at once.** This uses the pilot rule (first decode alone, the rest 4 at a time).

| Point | Per core | Total MACs |
|---|---|---|
| 0.15 -4 dB | about -25 % (upper bound -29 %, with rounding at least -22 %) | +4 % |
| 1/10 -5 dB | -2.5 % | |
| Other nofast points | <= -2 % | |
| 0.15 +1 dB (fast path on) | -9 % | |

**Undetected errors at 1/10 -5 dB.** The win4 error (srch10) and the nofast_spec error (nf10a) fall in the same
4000-packet chunk.
- Chance of that for two independent events: 1/16.
- The packet cannot be identified; per-packet indices are added from now on.

## Caveats

- Pre-fix accounting everywhere; the bracket is model-based.
- Testing points have 64k packets each.
- At 0.15 -1 / 0 dB the testing model (4 phases) is compared with the presentation model (2 phases).
- The blind-packet genie at 0.15 -4 dB (1.95e-3) is worse than the est3 genie (1.2e-3); unexplained.
