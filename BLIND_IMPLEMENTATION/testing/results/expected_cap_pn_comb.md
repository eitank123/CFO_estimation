# MAC cap in the receiver, phase noise, gate + stricter speculative decode, more gate dumps: predictions, 2026-11-13, before any result

## 1. Hard MAC cap (small_rx cap_core; jobs cap15a/b, cap25, capn15, capn25)
A packet whose search needs more than the cap (MACs per core) is stopped there and declared "no packet". Caps: 2 M at
1/10 / 0.15, 1 M at 2/5 / 1/2 (from the cap plots). Paired with the uncapped receiver on the same packets.

| Point | BLER uncapped (from earlier runs) | predicted BLER capped | mean per core change | undetected |
|---|---|---|---|---|
| 0.15 -2.5 dB (400k) | ~1e-5 | ~1.3e-5 (+2.5e-6 from the cap histogram, i.e. +0 ... +3 packets) | -0 ... -2 % | unchanged (can only fall) |
| 2/5 1.5 dB (400k) | ~0 ... 1e-5 | +0 ... +2e-5 | -0 ... -3 % | unchanged |
| 1/2 2.5 dB (128k) | 0 / 128k | 0 ... 1 error | ~0 | unchanged |
| noise-only 0.15 / 2/5 (10k frames each) | false alarms 0 | 0 (< 3e-4) | per core per frame 34 M -> 2 M / ~1 M (x17 / x30 lower) | - |

Kill: measured extra errors exceed the histogram prediction by > 2 packets (a bug in the cap emulation).

## 2. Phase noise (BLIND_PN = linewidth x symbol time; jobs pn1, pn2, pn3)
Wiener phase noise on the 8-SPS signal, zero at the packet centre, through the full chain. Testing receivers (+ the genie
that knows CFO and centre phase) at 0.15 -3.5 dB, 1/10 -5 dB (64k) and 2/5 0.5 dB (64k). No-noise references: 0.15 -3.5
dB 6.3e-4, 1/10 -5 dB 2.2e-4, 2/5 0.5 dB ~2.3e-3.

| Linewidth x Ts | phase drift over half a packet (std) | predicted blind BLER vs no phase noise | genie |
|---|---|---|---|
| 1e-5 | ~0.18 rad | x1 ... x1.3 | x1 ... x1.2 |
| 1e-4 | ~0.57 rad | x2 ... x10 (the 1024-symbol coherent metric loses ~0.5-1 dB) | x2 ... x5 |
| 3e-4 | ~1.0 rad | x10 ... x100, near 1 at 1/10 -5 dB | x5 ... x50 |
Decision rule (strategist): blind degrading < 2x more than the genie at 1e-4 -> phase noise parked; > 2x -> a segmented
/ non-coherent metric becomes the top item. MACs per core rise with the BLER (more search for failing packets).

## 3. Retry gate + stricter speculative decode (jobs comb10, comb15)
vs nofast15_qfix, paired, 64k: per core 1/10 -5 dB -8 ... -14 % (spec dominates; gate <= 2 %), 0.15 -4 dB -15 ... -25 %,
0.15 -3 dB -2 ... -5 %; BLER within noise; undetected 0 ... 1.

## 4. Decode dumps at more SNRs (jobs dga, dgb25, dgb2)
Measurement only (decisions as the receiver). Then the gate is refit on all SNRs per rate and re-checked offline; the
1/2 smoke at 1.5 dB skipped every retry, so a refit should keep some retries at 1/2 below 2 dB.

## Measured (2026-11-13)
All logs checked: EVAL DONE / ALL DONE, no Traceback, no duplicated chunk (pn3b finished 2026-11-14: 2/5 0.5 dB at 3e-4, 64k).

### 1. Cap: cap15a (0.15 -2.5 dB, 200k paired)
0 errors in both arms, cap_hit 0, per core identical (0.167 M): no packet at -2.5 dB needs > 2 M per core. HIT (predicted
+0 ... +3 packets).

### 1b. Cap: cap15b, cap25, cap2, capn15, capn25
| Point | packets | errors uncapped / capped | cap_hit | per core change | undetected |
|---|---|---|---|---|---|
| 0.15 -2.5 dB (cap15a + cap15b) | 400k | 2 / 4 (0 fixed / 2 broken) | 4 | -0.1 % | 0 / 0 |
| 2/5 1.5 dB (cap25) | 400k | 0 / 3 (0 / 3) | 3 | 0.0 % | 0 / 0 |
| 1/2 2.5 dB (cap2) | 128k | 0 / 0 | 0 | 0.0 % | 0 / 0 |
| noise only 0.15 -2.5 dB (capn15) | 11.2k | 0 false alarms | 11 200 | crit stops at 2.000 M; scheduled 0.94 M (uncapped ~16.5 M) | - |
| noise only 2/5 1.5 dB (capn25) | 11.2k | 0 false alarms | 11 200 | crit stops at 1.000 M; scheduled 0.33 M | - |
- vs predictions: 0.15 +2 packets on 400k (predicted +0 ... +3): HIT. 2/5 +3 on 400k = +7.5e-6 (predicted +0 ... +2e-5): HIT.
  1/2 0 ... 1: HIT. Noise only: 0 false alarms, the cap stops every noise packet at the cap (predicted 34 M -> 2 M / ~1 M):
  HIT. The cap is the only difference between the arms, so the broken packets are cap-stopped ones that the uncapped search decodes late (0.15: cap_hit 4 = the 2 packets lost anyway + 2 broken; 2/5: cap_hit 3 = 3 broken).
- Decision: a 2 M (1/10, 0.15) / 1 M (2/5, 1/2) cap costs ~1e-5 BLER at the waterfall foot and nothing in mean MACs,
  and bounds the worst case (noise / missed packets) at ~17x / ~30x below the uncapped search. Recommended for a real
  receiver; kept as a variant (`*_cap2`, `*_cap1`), the plots stay uncapped (cap plots show the effect per SNR).

### 2. Phase noise (64k per point; BLER, x = vs the no-noise reference above)
| Linewidth x Ts | 1/10 -5 dB | 0.15 -3.5 dB | 2/5 0.5 dB | per core vs no noise |
|---|---|---|---|---|
| 1e-5 | 1.25e-4 (x0.6, noise) | 7.3e-4 (x1.2) | 2.9e-3 (x1.3) | 1/10 0 %, 0.15 ~0 %, 2/5 +19 % |
| 1e-4 | 6.6e-4 (x3.0) | 2.25e-3 (x3.6) | 8.3e-2 (x36) | +17 %, +39 %, x10 (2.26 M) |
| 3e-4 | 2.7e-2 (x120) | 6.2e-2 (x98) | 0.54 (x235; genie 0.92) | x3.7, x6.9, x50 (11.7 M) |
- vs predictions: 1e-5 HIT (x1 ... x1.3). 1e-4 HIT at 1/10, 0.15 (x2 ... x10), MISS at 2/5 (x36). 3e-4 HIT (x10 ... x100).
- The "genie" (known CFO and centre phase, no tracking) is FAR worse than blind under phase noise (1e-4: 1/10 -5 dB 7.2e-2
  vs blind 6.6e-4; 2/5 0.5 dB 0.56): the blind receiver's CFO / phase estimate absorbs part of the drift, the genie does
  not. So the decision rule "blind degrades < 2x more than the genie" is met but says nothing; the genie is no bound here.
- Decision: phase noise is NOT parked. At 1e-4 (0.57 rad drift over half a packet) R = 2/5 collapses (x36 BLER, x10 MACs
  per core); 1/10 and 0.15 lose ~0.5 dB. A segmented / non-coherent metric (or a phase-tracking stage after the CFO
  search) becomes the top real-world item for 2/5 and 1/2 if the target oscillators reach linewidth x Ts ~ 1e-4.

### 3. Gate + spec11 combined (comb10, comb15, 64k paired)
| Point | base errors | nnb1 | nnb1 + spec11 | per core nnb1 / nnb1 + spec11 | total |
|---|---|---|---|---|---|
| 1/10 -5 dB | 20 | 20 (0 / 0) | 21 (0 / 1) | -1.2 % / -15.7 % | -0.7 % / -20.1 % |
| 0.15 -4 dB | 253 | 255 (0 / 2) | 254 (1 / 2) | -9.3 % / -16.3 % | -6.5 % / -16.8 % |
| 0.15 -3 dB | 15 | 15 | 15 | 0 % / -4.1 % | 0 % / -7.9 % |
- vs predictions: HIT (1/10 -8 ... -14 % -> -15.7 %, slightly more; 0.15 -4 dB -15 ... -25 % -> -16.3 %; -3 dB -2 ... -5 % -> -4.1 %).
- The savings add up (0.15 -4 dB: spec11 -6.9 % + gate -9.3 % -> -16.3 %), but the 1 % gate is rejected (expected_nnb.md:
  pooled 0 fixed / 8 broken), so this combination is not adopted; spec11 alone is the candidate.
