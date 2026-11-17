# Blind CFO research news

Newest first. One item per research result. Details in the linked files; sources in [REFERENCES.md](REFERENCES.md).

---

## 2026-11-18 01:05 (full system, VDE-SAT) — One phase guess: the VDE MAC floor drops from 0.31 to 0.21 M per core
- The floor (~0.31 M per core at every SNR above -5 dB) was 58 % CFO-grid work: 513 frequency x phase hypotheses per
  packet, each partly decoded. For BPSK the squared signal already fixes the phase mod pi, so the second phase guess per
  cell was insurance; dropping it halves the grid.
- Paired over three fresh seeds (180k packets at -4.6 dB, 60k at -5.0): 58 vs 59 and 215 vs 214 errors (within the 2 %
  rule), mean MACs -31 ... -33 % at every SNR; vs the receiver before tuning -50 ... -65 %. Blind ~8x VDE-SAT's cost at
  the operating point (was ~16x), still 1.15 dB ahead in Eb/N0.
- Also tested: NN checkpoint 1/8 or 3/16 (no gain), CFO grid step 6 (fails). Retune around one phase guess (fs-jtv32n)
  found final 0 + other changes, not adopted without a live check.
- Plots updated: VDE-SAT/overview/fs_vde32_final.png, VDE-SAT/MACs/. Summary: testing/results/summary_fullsys_2026-11-18.md.

## 2026-11-18 00:40 (full system, DVB-RCS2) — Jointly tuned blind: same BLER, MACs down only in the waterfall
- Settings per ID (live combinations on calibration packets; the offline replay cannot model DVB's joint list
  decodes): ID 13 final 16 + win 4.5 + shortlist 99.7 %/8; ID 42 final 8 + win 4.0 + 99.7 %/8; ID 3 final 8 + win 4.5;
  ID 14 final 8 + win 4.0 + 99 %/4. F5 thresholds as before.
- Fresh test packets, paired with the receiver before tuning: BLER unchanged; gap to DVB-RCS2 at BLER 1e-3 +0.29 /
  +0.29 / +0.58 / +0.24 dB (ID 13 / 42 / 3 / 14). Mean MACs per core: ID 14 -46 ... -23 % and ID 42 -14 ... -7 % in the
  waterfall, ~0 % at the operating point; ID 13 ~0 %; ID 3 +1 ... +9 %. DVB had little slack left (no batch schedule,
  F5 already tuned), unlike VDE.
- Plots: [DVB-RCS2/overview/fs_tuned_*.png](testing/results/plots/DVB-RCS2/overview/). Tables:
  fullsys/results/dvb_tuned_tables.md. Record: testing/results/tuning_fullsys.md.

## 2026-11-18 00:30 (full system, VDE-SAT) — Jointly tuned blind: same BLER, 26-63 % fewer MACs, worst case 8.4 -> 3.0 M
- New tooling: a full-search log mode (`run_blind_fs --fulllog`) and an offline joint tuner (`fullsys/joint_tune_fs.py`)
  that replays the whole search for any combination of shortlist / z-test / final-list settings; its self-check
  reproduces all 50k logged packets exactly, and the live check of its pick matched the replay to 0.002 M per core.
- Adopted VDE receiver: VDE-trained checkpoint NN + batch null on 32 cores + final 4 + z-test window 4.0 + shortlist
  99.7 % / at least 4 cells; F5 tuned but left out (~2 % for extra risk).
- Fresh test packets, paired with the receiver before tuning: identical failing packets; mean MACs per core 2.20 / 0.74 /
  0.33 / 0.31 M at -6.6 / -5.8 / -5.0 / -4.6 dB (was 5.88 / 1.67 / 0.46 / 0.42). BLER 1e-3 still 1.15 dB below VDE-SAT
  (sync word + pilots charged); blind costs ~11x VDE-SAT's ~0.03 M at the operating point (was ~16x).
- Caught on the way: `batch: null` without `cores` costed the search on one core per grid cell (~249 cores); the first
  "-41 ... -69 %" numbers were that artefact (fair: -26 ... -36 % for batch null + final 16 alone).
- Plots: [fs_vde32_final.png](testing/results/plots/VDE-SAT/overview/fs_vde32_final.png),
  [fs_vde_tuned_macs_capped.png](testing/results/plots/VDE-SAT/MACs/fs_vde_tuned_macs_capped.png),
  [fs_vde_tuned_capped.png](testing/results/plots/VDE-SAT/MACs/fs_vde_tuned_capped.png). Record: testing/results/tuning_fullsys.md.

## 2026-11-17 14:00 (full system, ID 13) — Blind beats DVB-RCS2 by 0.34 dB at BLER 1e-3, at ~3-4x the MACs
- DVB-RCS2 ID 13 (rate 1/3, 952-bit payload, 140 known symbols) with its own data-aided CFO estimate at +-0.03 vs blind
  (no known symbols, same payload, same 2952 coded bits, rate-matched polar N 4096 with GA construction, CA-SCL-8).
- Eb/N0 per payload bit at BLER 1e-3, known symbols charged: blind 1.28 dB vs DVB-RCS2 1.62 (+0.34); at 1e-4 +0.13
  (few errors). Blind sends 9.5 % fewer symbols for the same payload.
- MACs per core: blind 0.39-0.80 M vs DVB-RCS2 0.175 M (early stops not yet tuned; tuning on separate calibration
  packets, validated by replay on the test packets).
- Two fixes were needed: a rate-matching-aware polar construction (GA, +0.35-0.4 dB) and a random channel interleaver
  (without it a pi/2 QPSK rotation maps codewords to codewords and 37 % of packets fail; see 01_signal_model.md).
- Plot: [fs_id13_blind.png](testing/results/plots/DVB-RCS2/superseded/fs_id13_blind.png). Next: ID 42, then ID 3.

## 2026-11-17 11:40 (full-system build) — DVB-RCS2 and polar rate matching coded; their published curves collected
- `fullsys/turbo_db.py` + `rcs2.py`: DVB-RCS2 TC-LM (IDs 3, 13, 14, 42), self-test 36/36; `fullsys/polar_rm.py`: NR-style
  polar rate matching up to N = 4096, self-test 43/43, verifier PASS WITH FIXES (fixes in progress). VDE-SAT being coded.
- Their published curves: [plots/DVB-RCS2/BLER/fullsys_refs.png](testing/results/plots/DVB-RCS2/BLER/fullsys_refs.png). AFF3CT's full K = 1504
  rate-1/2 curve hits the TR 101 545-4 ID 14 values (1e-3 at 1.47 vs 1.49 dB): two independent targets agree.
- User decisions: blind carries the same payload + CRC-32 (952 + 32 at ID 13); ID 14 run both shortened and punctured;
  ID 42 blind on pi/2-BPSK and on QPSK. Standards PDFs in [testing/results/standards/](testing/results/standards/).

## 2026-11-17 10:20 (fixed-search test done) — With a correct CFO search, DVB-RCS2 is 0.20 dB behind blind at 1/10 (was 0.69)
- Three code reviews found holes in several competitors' CFO searches (blind's lead overstated). Re-run of the three key
  ones, 9 jobs, all clean, done in ~25 min:
  - **DVB-RCS2 ID 13**, search widened to +-1e-2 (its split pre/postamble makes side peaks across the range): 1/10
    **-4.58 dB (+0.20)**, was -4.09 (+0.69); 0.15 and 2/5 unchanged. Predicted -4.80 ... -4.65: missed (some loss remains).
  - **128-symbol preamble ML** (control): reproduces its old numbers; pooled 1/10 now **-4.72 (+0.06): a tie with blind**.
  - **VDE-SAT** with the unclipped window: still misses 0.6-2 % of packets at 1/10, still fails 1e-4; the full-range scan
    is running (fx-s10, fx-s15).
- At 0.15 @1e-4 the pilot receivers still beat blind (DVB-RCS2 -0.16 ... -0.19, 128 ML -0.17); 2/5, 1/2 unchanged.
- Updated: scoreboard.md, curves_* and fx_R* figures, presentation bler_fair / macs_fair (fixed DVB-RCS2 solid, old dashed),
  READMEs. Details: testing/results/expected_fx.md.

## 2026-11-17 (DVB-S2 header runs done at 0.15 and 2/5) — The DVB-S2 90-symbol header beats blind by 0.30 dB at R = 0.15, BLER 1e-4
- Real DVB-S2 PL header (90 known symbols, CFO scanned over the whole range): R = 0.15 **-3.23 dB @1e-4 vs blind -2.93
  (-0.30)**, the largest loss for blind so far (DVB-RCS2 / 128 ML were -0.19 / -0.20). @1e-3 -3.57 vs -3.60: tie.
  At 2/5 1.03 (+0.45 behind blind). Predictions hit (0.15 @1e-3 at the edge, in its favour).
- Price: its scan costs ~0.7-0.8 M MACs per core, so blind is 2.9-4.5x CHEAPER than this competitor.
- 1/2 still running. The extra 1/10 point at -5.3 dB (your request) is first in the queue: v-10hla / v-10hlb, 960k packets,
  prediction -4.92 ... -4.80 dB @1e-4 (tie or slightly better than blind's -4.78). Starts when a slot frees (7 active).

## 2026-11-17 (v-2w done) — Real Wi-Fi preamble at R = 1/2: +1.38 dB behind blind
- @1e-3 (blind 1.73): real 320-symbol 802.11 preamble 3.11 with or without lobes (+1.38; both predictions hit); the
  128-symbol Wi-Fi receiver 2.42 (+0.69). Wi-Fi is now closed at every rate. Scoreboard unchanged.

## 2026-11-17 — Summary: READMEs updated with the adopted receiver and all 31 competitors
- **Adopted testing receiver vs the presentation receiver** (same BLER within the CIs): MACs per core -39 % at 1/10
  (0.317 -> 0.194 M), -32 % / -37 % at 0.15 (1e-3 / 1e-4), -17 % at 2/5 (0.221 -> 0.183 M), -20 % at 1/2 1.5 dB.
- **Scoreboard** (testing/results/scoreboard.md, generated from the result files): 31 receivers of 12 deployed
  systems. Blind is best or tied at 1/10, 0.15 @1e-3, 2/5 and 1/2; it loses only at 0.15 @1e-4 (DVB-RCS2 -0.19, 128 ML
  -0.20, Griebel 4096 -0.18, 64 + 64 L4 -0.17, CCSDS-inspired -0.14 dB). Open: DVB-S2 90-symbol header at 1/10 (below
  1e-4 already at -4.63 dB; measured 0.63 M MACs per core, blind 3.2x cheaper).
- v-10hb (DVB-S2 at 1/10, -4 ... -2 dB) done: header90 flat at ~6e-6 (2-4 errors per 480k); DVB-S2 style -2.32 (+2.46).
- **Correction:** the R = 1/2 CCSDS 131.2 real crossing is 2.35 dB (+0.63), not 2.00 (+0.27) as first sent; the
  closest competitor at 1/2 is the Advantech wide preamble (+0.38).
- READMEs touched: BLIND_IMPLEMENTATION/README.md (new "Current state"), presentation/README.md, testing/README.md,
  top-level README.md (pointer), 08 §8.2a and competitors.md (blind row).

## 2026-11-16 (v-15w2 done) — Wi-Fi at R = 0.15 closed: 128-symbol preamble ties blind at 1e-4
- @1e-4 (blind -2.93): 128-symbol Wi-Fi receiver -2.91 (+0.02, tie); real 320-symbol preamble with lobes -2.26 (+0.67);
  without lobes it never reaches 1e-4 and needs ~-0.05 dB for 1e-3 (+3.55, CFO wrap).

## 2026-11-16 (v-10wb done) — Real Wi-Fi preamble at R = 1/10: +2.3 dB behind blind at 1e-4
- @1e-4 (blind -4.78): 320-symbol 802.11 preamble with lobes **-2.46 (+2.32)**, predicted -4.01 ... -3.96: big miss,
  worse (coarse CFO misses outside the lobes set the tail). Without lobes it never reaches 1e-4 (~2e-3 at -0.8 dB).
  The 128-symbol Wi-Fi receiver: -3.13 (+1.65).

## 2026-11-16 (v-25w done) — Real Wi-Fi preamble at R = 2/5: +1.26 dB behind blind
- @1e-3 (blind 0.58): real 320-symbol 802.11 preamble with lobes 1.84 (+1.26, predicted 1.82 ... 1.87: hit); without
  lobes 1.88 (+1.30; predicted 2.35 ... 2.5: miss in its favour, the CFO wrap only bites below 1e-4 at this rate).
  The 128-symbol Wi-Fi receiver: 1.17 (+0.59).

## 2026-11-16 (v-10ha done) — DVB-S2 90-symbol header at R = 1/10 may tie or beat blind at 1e-4
- Real DVB-S2 PL header (90 known symbols, scanned over the CFO range): **3.1e-5 (15 / 480k) at fair-axis -4.63 dB**,
  already below 1e-4 at the lowest point we ran. Blind needs -4.78. Predicted -4.82 ... -4.72 (+0.08 ... +0.18).
- The crossing is not bracketed: somewhere in about -4.95 ... -4.65, i.e. between 0.17 dB better and 0.13 dB worse
  than blind. A point at data Es/N0 -5.3 dB (plots at -4.93, inside the -5 dB limit) would settle it; not run yet.
- Cost: it was predicted at ~0.70 M MACs per core (scan) vs blind's 0.20 M, so blind stays ~3.5x cheaper.
- The current "DVB-S2 style" receiver floors at ~1e-2 (search misses), as before. More points in v-10hb.

## 2026-11-16 (v-15w done) — Real Wi-Fi preamble at R = 0.15: +0.88 dB behind blind; wraps without lobes
- @1e-3 (blind -3.60): real 320-symbol 802.11 preamble with lobes **-2.72 (+0.88)**, predicted -2.73 ... -2.68: hit.
  Its result is the 128-symbol Wi-Fi receiver (-3.39, +0.21) shifted by its 0.67 dB extra energy.
- Without lobes it floors near 5e-3 (CFO wrap of the lag-16 coarse step): fails, as predicted.
- @1e-4: the 128-symbol receiver is at 1.2e-4 at -2.99, so about a tie with blind (-2.93); final with v-15w2.

## 2026-11-16 (v-2mb done) — R = 1/2 closed for the real CCSDS / MIL / 64+64 layouts
- Upper points show no floors (all <= 1.9e-4 at 2.5 dB raw, CCSDS 131.2 the slowest), so the v-2ma numbers @1e-3 are
  final: ASM +0.46, CCSDS 131.2 real +0.63 (corrected, was +0.27), split L4 +0.64, CCSDS style +0.66, MIL-110 HF +1.27, full +1.62 dB.

## 2026-11-16 (v-25mb done) — R = 2/5 final for the real CCSDS / MIL / 64+64 layouts: all 0.37+ dB behind blind
- @1e-3 (blind 0.58): CCSDS 131.0 ASM 0.95 (+0.37), 64+64 split L4 1.12 (+0.54), CCSDS style 1.14 (+0.56), CCSDS 131.2
  real 1.15 (+0.57), MIL-110 HF 1.74 (+1.16), MIL-110 full 2.10 (+1.52). Three of four predictions hit; 131.2 a close
  miss (0.03 dB worse). Closest competitor at 2/5 is still the Advantech wide preamble (+0.33).

## 2026-11-16 (v-15mc done) — R = 0.15 closed for the real CCSDS / MIL / 64+64 layouts
- Real CCSDS 131.2 pilots (32 pilots): **-2.74 dB @1e-3 (+0.86 behind blind), -1.95 @1e-4 (+0.98)**; predicted -3.53 ...
  -3.18 @1e-3: miss, much worse. Every other source is at <= 1 error above -2.5 dB raw, so the v-15mb crossings are final:
  @1e-4 split L4 (-0.16) and CCSDS style (-0.13) beat blind, ASM ties (-0.05).

## 2026-11-16 ~08:00 (v-10mb, v-15mb, v-25ma done) — Real CCSDS layouts lose clearly at 1/10; 0.15 @1e-4 pilots still win
- **R = 1/10 @1e-4 (final):** real CCSDS 131.0 ASM **-3.89 dB (+0.89 behind blind)**, real CCSDS 131.2 pilots **-2.32
  (+2.46)**; both predicted near blind: big misses, worse. Cause: shallow curves from residual CFO-search misses.
  64+64 split L4 ~-4.60 (+0.18, crossing not bracketed). MIL-110 full is below 1e-4 at its lowest point.
- **R = 0.15:** @1e-3 blind leads everyone (ASM +0.16, split L4 +0.19, CCSDS style +0.20, MIL +0.77 ... +1.09).
  @1e-4 the old picture holds: **split L4 -3.09 and CCSDS style -3.06 beat blind (-2.93) by 0.16 / 0.13 dB**, ASM ties
  (-0.05). All predictions hit except CCSDS 131.2 (much worse).
- **R = 2/5 (provisional, 2 points):** ASM ~1.00 (+0.42), split L4 / CCSDS style ~1.15 (+0.57), 131.2 ~1.23 (+0.65),
  MIL full ~2.12 (+1.54).
- Open idea (not run): one raw -5.5 dB point at 1/10 (fair axis about -4.0, on the plotted axis) to bracket the L4 and
  MIL-110 full crossings. Details: expected_variants.md §9.

## 2026-11-16 (v-2ma done) — R = 1/2: real CCSDS / MIL / 64+64 layouts all 0.46+ dB behind blind (CORRECTED 2026-11-17)
- Crossings @1e-3, blind 1.73 [1.69, 1.76]: CCSDS 131.0 ASM 2.19 (+0.46), CCSDS 131.2 real **2.35 (+0.63)**, 64+64
  split L4 2.37 (+0.64), CCSDS style 2.39 (+0.66), MIL-110 HF 3.00 (+1.27), MIL-110 full 3.34 (+1.62). All four
  predictions hit.
- **Correction:** this item first said CCSDS 131.2 real 2.00 (+0.27) and "closest competitor at 1/2". That was an
  arithmetic slip in my hand interpolation (1e-3 lies between 2.13 and 2.63 dB, not below 2.13); the scripted
  scoreboard gives 2.35. The closest competitor at 1/2 stays the Advantech wide preamble (+0.38).

## 2026-11-16 (v-15p2 done) — Advantech wide preamble cannot reach BLER 1e-4 at R = 0.15
- Floor 2.0e-4 ... 3.8e-4 from -2.8 to -0.8 dB (fair axis), rising slightly with SNR: ~3e-4 of packets have the true
  CFO outside its search (coarse 4th-power misses). Blind reaches 1e-4 at -2.93 dB, so blind wins this target outright.
- So this receiver ties blind at 1e-3 but fails 1e-4, at both 1/10 and 0.15. ViaSat x3, hyb3 and the narrow 48 fail.
- Details: expected_variants.md §9.

## 2026-11-16 (v-15ma done) — R = 0.15, BLER 1e-3: real CCSDS / MIL / 64+64 layouts all 0.2+ dB behind blind
- Provisional crossings (extrapolated from -4.5 / -4 dB raw; v-15mb adds the points that bracket 1e-3). Blind -3.60:
  CCSDS 131.0 ASM ~-3.40 (+0.20), 64+64 split with 4 lobes ~-3.39 (+0.21), CCSDS style ~-3.37 (+0.23),
  MIL-110 HF ~-2.82 (+0.78), MIL-110 full ~-2.50 (+1.10). All four predictions hit.
- Miss: real CCSDS 131.2 pilot density (32 pilots) ~-2.6 (+1.0), predicted -3.53 ... -3.18: its CFO estimate is too weak
  at 0.15 (0.2 % of packets outside the search), so its curve is shallow.
- Details: expected_variants.md §9.

## 2026-11-16 (v-10wa done) — Real Wi-Fi preamble at R = 1/10: wrap floor ~1e-2; with lobes ~5e-4 floor
- Real 802.11 320-symbol preamble (STF lag-16 coarse + LTF fine): **floor ~1e-2** (1.5e-2 at -3.82, 1.05e-2 at -3.32 dB):
  the lag-16 coarse range is +-0.03125, so CFOs near +-0.03 wrap. Predicted, hit.
- Same with the +-4 fine lobes: 1.0e-3 at -3.82, 5.2e-4 at -3.32 dB. Predicted 1e-4 at about -4.0: **likely miss
  (worse)**; BLER tracks the packets outside the search (~5e-4). Upper points in v-10wb.
- Blind needs -4.78 dB for 1e-4 at 1/10, so both are well behind. Details: expected_variants.md §9.

## 2026-11-16 (v-10ma, v-10p2 done) — R = 1/10: Advantech preamble floors over the whole range; 64+64 split near blind
- **Advantech 48 wide (v-10p2):** flat floor ~2.5e-4 from -3.8 to -1.8 dB (102-128 errors per ~420k): it never
  reaches 1e-4 at 1/10. Cause: ~3e-4 of packets have the true CFO outside its search (coarse 4th-power miss). Loss
  for the competitor. ViaSat x3, the narrow 48 and hyb3 fail as predicted.
- **v-10ma (lowest two points, provisional until v-10mb):** 64+64 split with 4 lobes 8.1e-5 at -4.49 dB, so ~-4.6 @1e-4
  (blind -4.78: blind ~0.2 dB better; prediction hit). Real CCSDS ASM (8.7e-4 at -4.74) and real CCSDS 131.2 pilots
  (1.3e-2 at -4.87) look worse than predicted; MIL-110 full 1.9e-5 at -3.53 dB, consistent.
- Details: testing/results/expected_variants.md §9.

## 2026-11-16 (v-15pb done) — Real Advantech preamble ties blind at R = 0.15, BLER 1e-3
- Advantech 48-symbol preamble with the wide window: **-3.63 dB @1e-3 vs blind -3.60** (gap -0.03, inside blind's CI
  [-3.67, -3.52]): a tie. Predicted 0.04-0.24 dB behind blind: close miss in its favour.
- Unlike the other pilot receivers it is not cheap: ~0.36 M MACs per core at its crossing vs blind's 0.26 M (its wide
  DA search runs ~130 hypotheses), so blind is the cheaper of the two here.
- @1e-4 still open (v-15p2 running); its search covers the true CFO in 99.98 % of packets, so a ~2e-4 floor is likely,
  as at 1/10 (where it fails 1e-4). ViaSat x3 and the narrow 48 fail at 0.15 as predicted.

## 2026-11-16 00:45 (twf done) — Adopted early-stop receiver now drives the 2/5 and 1/2 numbers
- twf ran the adopted receiver over the rest of the waterfall: all BLER and MAC predictions hit (2/5 0 dB -21 % per
  core, 1 dB -7.6 %, above the waterfall ~0 ... -4 %).
- Blind now: **2/5 @1e-3 = 0.58 dB [0.55, 0.61]** (was 0.61), MACs per core at the crossing 0.183 M (was 0.209);
  **1/2 @1e-3 = 1.73 dB [1.69, 1.76]** (was 1.79), 0.139 M (was 0.149).
- The 0.03-0.06 dB move is NOT an early-stop gain (paired, early stop is slightly worse): the adopted curve uses its
  own, larger packet sets, and the old 1/2 2 dB base point (21 / 128k) was on the unlucky side. Both inside the CIs.
- Gaps grow accordingly: at 2/5 closest are the Advantech wide preamble +0.33, VDE-SAT +0.34, RCS2-13 +0.52; at 1/2
  Advantech wide +0.38, VDE-SAT +0.44, RCS2-13 +0.61. MACs ratio blind / RCS2-13: 2/5 5.2x -> 4.5x; 1/2 now 3.3x.
- Faithful variants also landed at 1/10: the Advantech wide preamble floors at ~4e-4 (search misses), so it fails
  1e-4 (predicted -4.79 ... -4.49: miss); ViaSat x3 and the narrow 48 fail as predicted.

## 2026-11-15 23:10 (tw15b done) — Confirmed: at R = 0.15, BLER 1e-4, four pilot receivers beat blind by 0.15-0.20 dB
- Blind 0.15 @1e-4 = **-2.93 dB, CI [-2.99, -2.83]** (544k packets at -3 and -2.5 dB; was CI [-3.00, -2.61]).
- RCS2-13 -3.12, 128 ML preamble -3.12, G4096 -3.11, CCSDS style -3.07: their CIs no longer overlap blind's, so the
  0.15-0.20 dB deficit is real. DMRS 1/7 ties (-2.92). Blind still wins at 0.15 @1e-3 (-3.60, all +0.15 or more).
- Why: blind's waterfall at 0.15 is shallower below 1e-3 (x6 per 0.5 dB at -3 -> -2.5 vs x30 for RCS2-13), most
  likely a tail of CFO-search misses (not yet checked with a decode dump). Blind loses the low-BLER end at this rate.
- All three tw15b predictions hit. Plots and tables regenerated.

## 2026-11-15 22:50 (v-25p done) — Faithful ViaSat / Advantech at R = 2/5: blind wins, closest +0.30 dB
- Advantech 48-preamble wide window **0.91 dB (blind 0.61, +0.30)**, the narrow one 2.02 (+1.41), hyb3 1.79 (+1.18).
- Both real ViaSat receivers stay above 1e-3 up to 2.07 dB (top of the run; predicted 2.4-2.8), so > +1.46 dB.
- All five predictions hit or consistent.

## 2026-11-15 (v-2p done) — First faithful variants, R = 1/2: real ViaSat and Advantech are better than our stand-ins, blind still wins
- **ViaSat:** our UW stand-in never reaches 1e-3, but the patent's own receivers do: 7653150 at 2.74 dB (blind +0.95),
  top-32 + 4th-power phase at 2.61 dB (blind +0.82). The UW-based phase was what crippled the stand-in.
- **Advantech:** the 48-symbol preamble beats our 16+16 hyb3: 2.18 dB (blind +0.39), wide window 2.11 dB (blind +0.32;
  hyb3 2.34, +0.55). So the closest real burst modem at 1/2 is 0.32 dB behind blind.
- 5 of 6 predictions hit; the wide pre48 came out 0.04 dB better than predicted.

## 2026-11-15 (e5-15 done) — Deployed competitors at R = 0.15: blind wins at 1e-3, three edge it at 1e-4
- **@1e-3** (blind -3.60): every competitor needs more SNR. Closest: CCSDS style +0.19, Wi-Fi +0.22, DMRS 1/7 +0.33,
  DVB-S2 style +0.48, VDE-SAT +0.68, CCSDS blocks +0.70, MIL-110 +0.78 dB; Sparse 1/32, ViaSat UW and hyb3 fail.
- **@1e-4** (blind -2.93, CI [-3.00, -2.61]): **CCSDS style -0.14**, RCS2-13 -0.18 and 128 ML preamble -0.19 are
  ahead of blind; DMRS 1/7 ties (+0.02); the rest trail by 0.11-1.17 dB.
- Blind's 1e-4 CI is wide because its -2.5 dB point has only 64k packets; tw15b (480k there) is still running and
  decides how real the 0.14-0.19 dB deficit is. Blind uses 3-7x their MACs per core.
- Predictions: CCSDS style, Wi-Fi, MIL-110 hit within 0.02; DVB-S2 style +0.18 and VDE-SAT +0.48 dB worse than predicted.

## 2026-11-15 21:30 — ViaSat UW and hyb3 at 2/5 and 1/2: blind wins
- e5-ppB: **hyb3** needs 1.82 dB at 2/5 (blind 0.61, **+1.21**) and 2.34 dB at 1/2 (blind 1.79, **+0.55**). Both
  predictions hit. Blind spends 2.8-4.1x its MACs per core.
- **ViaSat UW** never reaches 1e-3 (up to 2.1 dB at 2/5, 3.1 dB at 1/2). I had predicted 1.5-2.5 / 2.2-2.8 dB: miss,
  it is worse than predicted.
- With this every same-system competitor is measured at 2/5 and 1/2; blind is best at every rate except 0.15 @1e-4
  (RCS2-13 / 128 ML preamble ahead by 0.18-0.19 dB).

## 2026-11-15 21:25 — ViaSat UW and Advantech hyb3 at 1/10 and 0.15: both fail, as predicted
- e5-ppA (stopped at 200 errors, 12k packets per point): ViaSat UW BLER 0.69-0.92 and hyb3 0.21-0.50 over the whole
  1/10 and 0.15 range (to -1 dB). Neither reaches 1e-3 or 1e-4 anywhere; predicted "fails". Their 16-32 known symbols
  cannot pin a +-0.03 CFO at these SNRs.
- Same-system plots (same_bler_R10 / R15) are now complete apart from DMRS 1/7 at 0.15 (e5-15 still running).

## 2026-11-15 21:20 — Early stop at 2/5 confirmed on 400k: -15 % MACs per core, 11 packets lost
- fzs25a-d pooled, 2/5 0.5 dB, 403.2k paired: errors 794 -> 805 (0 fixed, 11 lost, p = 0.001), undetected 4 = 4.
  Per core 0.231 -> 0.197 M (**-14.9 %**), total -12.7 %. Prediction hit (-11 ... -14 %, up to ~25 lost).
- The +40-packet rule passes; the "p < 0.05" clause trips. Loss = 2.7e-5, moves the crossing ~0.003 dB.
- **Decision needed (2/5 and 1/2 together):** adopt early stop (-15 % / -20 % MACs per core below the waterfall,
  ~0.001-0.003 dB BLER cost) or keep it off. At 1/10 / 0.15 it saves only 1-5 %.

## 2026-11-15 21:00 — Testing blind now covers the whole range at 2/5 and 1/2 too (tw25)
- 2/5 0 dB 5.9e-2, 1/2 1.5 dB 1.11e-2: both inside the predictions, and the 1/2 point agrees with the presentation
  receiver (1.15e-2), so no model mismatch.
- Required SNR unchanged: 2/5 @1e-3 **0.61 dB**, 1/2 @1e-3 **1.79 dB**, now all from the testing model with its own
  MAC counts. Every tw prediction hit except 1/10 -4.5 dB (3.7e-5 vs <= 3e-5).
- Plots and comparison tables regenerated. Only tw15b (0.15 -2.5 dB at 480k) is left.

## 2026-11-15 20:55 — Early stop (F5) at 1/10 and 1/2: -20 % MACs at 1/2 1.5 dB, but it trips the loss rule there
- fzs-r, paired: **1/2 1.5 dB** (128k) per core -20.4 %, total -20.7 %; errors 1363 -> 1381 (1 fixed, 19 lost,
  p = 4e-5). Pre-set kill rule was > 13 extra errors, so it is **tripped (+18)**, though the 1e-3 crossing moves
  only ~0.001 dB. **1/2 2 dB:** -1.7 %, 0 lost. **1/10 -5 / -4.5 dB:** -1.4 / -1.3 %, 0 lost (predictions hit).
- Your call for 1/2: accept (crossing unchanged, big saving below the waterfall) or retest a stricter threshold.
  2/5 confirmations (fzs25b/c/d) still queued.

## 2026-11-15 20:40 — Online list re-ranking (F3): no BLER gain, but 6 % fewer MACs per core at 0.15 -4 dB
- onl15a / onl15b: testing_s11g vs lm2 / lm2z / lm4 on the same 64k packets per point.
- **0.15 -4 dB:** errors 245 -> 241 (11 fixed, 7 broken, p = 0.48: not significant). Predicted 2.5-3.5e-3, measured
  3.8e-3. **-3.5 dB:** 48 -> 50-51, no gain.
- **Unexpected:** per core 0.391 -> 0.365 M (**-6.6 %**, lm2z) at -4 dB; I had predicted a cost increase. The better
  order finds the right candidate sooner. Only -1 % at -3.5 dB.
- Dropped as a BLER idea (DEAD_ENDS.md). **Update 20:55, onl10 (1/10 -5 dB):** BLER identical (18 = 18), per core
  only -0.7 %. So the trim is ~2 % at the operating points; not adopted.

## 2026-11-15 20:30 — R = 1/10 settled: blind beats the last three deployed competitors too
- e5-10lo (lower Es/N0, all points >= -5 dB on the fair axis) brackets the 1e-4 crossings that were below range.
- Required SNR @1e-4 (fair axis): blind **-4.78**; CCSDS style -4.66 (**+0.12**, CIs just touch), NB-IoT DMRS 1/7
  -4.58 (**+0.20**), MIL-110 -4.11 (**+0.67**). Blind uses 3-5.7x their MACs per core.
- I had predicted a tie for CCSDS and DMRS: their genie-level -5 dB points hid very steep waterfalls (x27 per 0.5 dB).
  All three misses were in the competitors' favour.
- So at 1/10 blind now beats every deployed competitor; the closest are the 128-symbol ML preamble (+0.10) and
  CCSDS style (+0.12). MIL-110 has 48 undetected errors in 480k at -4.96 dB.

## 2026-11-15 20:20 — Deployed competitors at R = 2/5 (e5-25): blind wins all of them
- Required SNR at BLER 1e-3 (fair axis), blind **0.61 dB** [0.58, 0.65]. Gaps (+ = blind better): VDE-SAT +0.31,
  DVB-S2 style +0.51, CCSDS style +0.52, Wi-Fi +0.56, DMRS 1/7 +0.67, CCSDS blocks +0.75, MIL-110 +1.14 dB;
  Sparse pilots 1/32 fails 1e-3 up to 2.1 dB. (RCS2-13 +0.49, unchanged.)
- Predictions held: most within 0.05 dB (VDE-SAT hit, CCSDS blocks off by 0.11).
- MACs per core: blind 0.209 M = 4-5x theirs (Wi-Fi 0.9x).
- 0.15 (e5-15) still running, ~4 h left.

## 2026-11-15 20:10 — Faithful competitor variants: smoke passed after one scan fix, 48 full jobs queued
- **v-smoke:** identity part bit-exact with the old e5 smoke (existing competitors unchanged); hypothesis counts,
  lobes, Nk as designed; 0 undetected errors everywhere; parents reproduce.
- **Bug found and fixed:** the DVB-S2 SOF-only / header-only range scan left part of the +-0.03 range unsearched when
  the first estimate fell outside it (3/800 misses, a ~4e-3 floor). Scan now centred on the clipped estimate;
  re-smoke: SOF26 in-search 1.000, errors 3 -> 0 on the same packets, every other source bit-exact.
- **Real results, not bugs:** ViaSat 7653150 (pure 4th-power) misses land uniformly in the range, so its rmse is
  3.4x the UW re-ranked parent at a similar BLER; the narrow Advantech 48-preamble is worse than hyb3 at 2/5 (60 of
  its 62 errors are outside its 6-hypothesis search). The wide 48-preamble fixes it: 1/800 at 0.15 -4 dB vs 424.
- **Runtime:** parts ran 1.4-2.3x the model, so the set was re-split to 48 jobs, each <= 9.9 h, ~310 job-hours
  (~45 h on 7 slots). Queued behind e5-10lo and the 6 earlier jobs.

## 2026-11-15 20:00 — Testing blind over the full range at 1/10 and 0.15; deployed competitors at 1/10 and 1/2
- **Blind, testing model (tw10a2, tw10b, tw15a2 pooled, 544k packets per low-SNR point):** 1/10 @1e-4 = **-4.78 dB**
  (CI [-4.86, -4.69]; was -4.90 on 10 / 1 errors), 0.15 @1e-4 = **-2.93 dB** (CI [-3.00, -2.61]). Both inside the
  predictions (-5.0 ... -4.75, -3.05 ... -2.85).
- **What changes:** at 0.15 @1e-4 RCS2-13 and the 128 ML preamble now beat blind by 0.18-0.19 dB with blind's CI
  clear of theirs on the low side. At 1/10 blind still leads RCS2-13 by 0.69 dB and pre128 ML by 0.10 dB. The 0.15
  -2.5 dB point is still 64k (tw15b running).
- **Deployed competitors, R = 1/2 (e5-2):** blind wins every one at 1e-3: VDE-SAT +0.38, DVB-S2 style +0.60, CCSDS
  +0.61, Sparse 1/32 +0.67, DMRS 1/7 +0.75, MIL-110 +1.21 dB. Blind spends 1.6-2x their MACs per core (Wi-Fi: 0.4x).
- **R = 1/10 (e5-10):** blind wins against VDE-SAT, Sparse 1/32 (both fail 1e-4 up to -1.7 dB), DVB-S2 style +2.45,
  CCSDS blocks +1.41, Wi-Fi +1.71 dB. **Open:** CCSDS style, DMRS 1/7 and MIL-110 were at genie level at the lowest
  point, so their crossing is below the simulated range. Follow-up e5-10lo queued (raw -5.5 ... -6.1 dB, all >= -5 dB
  on the fair axis): predicted CCSDS style and DMRS 1/7 **tie** blind, MIL-110 +0.5 dB (expected_e5lo.md).
- Plots regenerated (e4_*, bler_raw / bler_norm / pareto, arsf_*, same_*, capf_*); comparison_full.md updated.

## 2026-11-15 15:27 — Real-system cards: most of our competitors are STRONGER than the deployed systems
- 3 agents read the standards, patents and vendor data for all 11 systems (lit_card_sat / space / terr.md).
- **Stronger than real:** DVB-RCS2 (real sync loses 0.12-0.6 dB, ours ~0), DVB-S2 (a real 1024-symbol window has
  no pilot block), CCSDS (3.7x the real pilot density), NB-IoT DMRS (wider window than deployed), MIL-110 (drops 103
  of the real 411 known symbols, ~0.33 dB in its favour), hyb3 (CRC selector vs real |LLR|).
- **Weaker than real:** ViaSat (real phase from the 4th-power spectrum, ours from the 16-symbol UW).
- **Mixed:** Wi-Fi (real uses 320 known samples, no lobe search). **Harsher conditions:** VDE-SAT (designed for
  -2.4 dB, we test it down to -5 dB).
- Confirmed: DVB-RCS2 ID 13 unchanged in V1.5.1 (2026); VDE-SAT downlink format closed (no link ID, pi/4-QPSK).
- Optional faithful variants proposed (your call): Advantech 48-symbol preamble, ViaSat 4th-power phase, DVB-S2
  header-only. Merging into the cards, competitors.md and REFERENCES.md now.

## 2026-11-15 15:20 — Code rates of the real systems: long-frame standards carry 5-78 % more bits/symbol at our SNRs
- **Same-length competitors tie:** DVB-RCS2 (984-1504-bit bursts), VDE-SAT short formats, CCSDS LDPC (2048,1024) and
  real SCPC modems are at 0.8-1.0x our spectral efficiency at the same Es/N0.
- **Long-frame standards are ahead:** DVB-S2/S2X +12-20 % at 2/5 and 1/2; at 1/10 CCSDS turbo 1/6 (k = 8920) +78 %,
  S2X VL-SNR +25-32 %. Their pilots cost only 2-10 %: the gap is code length, not synchronisation.
- **Bound (recomputed):** the best any 1024-symbol packet can do at our points is 0.30 / 0.43 / 0.96 / 1.15 bits/symbol;
  we reach 62 / 67 / 82 / 86 % of it. The headroom is in the code and decoder, mostly at 1/10 and 0.15.
- **Rate gap:** between 0.15 and 2/5 (-2.9 ... -1 dB) we have no rate; standards run ~1/4 there.
- Caveats: their thresholds are ideal-sync table values at different error targets (S2 PER 1e-7, CCSDS BER 1e-6);
  real implementations lose 0.1-0.6 dB more. Details: `testing/results/lit_rates.md`.

## 2026-11-15 15:07 — Early stop (F5) holds at 2/5 full scale and below its fitted SNR; blind's -5 dB cost exposed
- **fzs25a (2/5 0.5 dB, 100.8k paired):** 204 -> 205 errors (1 lost, 0 gained; kill rule +10), MACs per core -15.1 %,
  total -13.0 %. Three more 100k parts queued.
- **fzs-lo (below the fitted SNR):** 2/5 0 dB 377 -> 378 (1 lost / 6.4k), MACs per core **-21 %**; 0.15 -5 dB identical
  errors, saving ~0 (the stop almost never fires there).
- **New on blind (0.15 -5 dB, first testing-model run there):** 4.7 M MACs per core on average (18x its cost at the
  BLER target) and 53 / 4800 undetected errors (1.1 %; the genie has none). Goes into the comparison as a caveat.
- In progress: per-packet MACs logging (caps in post-processing), competitor card research (3 agents), code rates.

## 2026-11-15 14:37 — Griebel / DVB-RCS2 study done (480k packets): blind's lead over DVB-RCS2 unchanged
- **Paper's claim holds at its own setting:** FFT 4096 (zero-padding ~3.6x, like the paper) = RCS2-13 within 0.1 dB
  with 10 % fewer MACs. FFT 2048 is only 1.8x padding on our longer burst: at -5 ... -2 dB the peak lands in the wrong
  bin, a BLER floor (+3.75 dB at 1/10); fine at 2/5, 1/2. A Newton step does not rescue a wrong bin.
- **The paper's one-decode chain** (no CRC search): +0.2 dB at 2/5, 1/2, much worse at low SNR.
- **Our alias-lobe search adds nothing:** predicted to close blind's 1/10 lead, it did not. RCS2-13's 1/10 losses are
  CFO accuracy at -5 dB, not aliasing (prediction missed, recorded).
- **Blind vs best DVB-RCS2 (fair axis):** +0.80 (1/10), +0.15 (0.15 @1e-3), -0.14 (0.15 @1e-4, tie inside blind's CI),
  +0.49 (2/5), +0.54 dB (1/2); blind at 2-8x the MACs per core. Details: `testing/results/expected_ars.md`.
- Also: regression check passed (RCS2-13 bit-identical to the earlier run). Next: testing-model blind over the full SNR
  range (tw jobs, the 1/10 and 0.15 @1e-4 crossings get 480k packets) and the est5 pilot competitors.

## 2026-11-15 13:53 — All 5 smoke tests pass; early stop saves 15 % at 2/5 with no loss; full runs started
- **Early stop (fzstop, F5) online:** 2/5 0.5 dB: MACs per core -15.0 % (offline predicted -15 %), 0.15 -4 dB: -6.3 %
  (predicted -3.8 %); identical errors (1 vs 1, 2 vs 2 on the same 400 packets); no packet's data lost to a stop.
- **Griebel / ARS smoke:** the paper's one-decode chain has 7-9 errors / 800 vs 0-1 for RCS2-13; FFT 2048 has a 4.6x
  larger CFO error at -4 dB. As predicted: the paper's shortcuts make DVB-RCS2 cheaper but worse.
- **Pilot competitors smoke (800 packets, 0.15 -4 dB):** VDE-SAT 6, DVB-S2-inspired 6, CCSDS 0, Wi-Fi 2, MIL-110 2
  errors; ViaSat 734 and hyb3 352 (4th power fails, as predicted). Surprise: **sparse pilots 1/32 has 108 errors**
  (BLER 0.135), much worse than the competitors.md prediction; the earlier ">= 1 dB behind" estimate looks right.
- lm-smoke2 reproduces lm-smoke exactly (L = 1/2/4/8); the new list-1 tie rule matches the reference decoder.
- Running: ARS full runs (4); queued: est5 (6), early stop incl. the lower-SNR check fzs-lo (6), online F3/DD (3).

## 2026-11-15 13:09 — Reviews passed; VDE-SAT format confirmed (pilots were 13 symbols late, fixed before any run)
- **VDE-SAT (ITU-R M.2092-2):** 27-symbol syncword, 1 pilot every 27, first pilot 14 symbols after the syncword.
  Our layout had the right count (66 known, 0.27 dB) but pilots 13 symbols late; fixed now, ~0 dB effect expected.
  The only published VDES CFO estimator (IEEE 8780774: correlate with Doppler-shifted copies, then refine) is the
  same family as our C6 chain, so C6 is a full-strength competitor. Details: `testing/results/lit_vdesat_format.md`.
- **Competitor code review (est5 + Griebel):** pass. Fixes in progress: per-packet paired counts (needed for the
  "not worse than DVB-RCS2" test), a rare dropped candidate in hyb3, CCSDS blocks added to the full runs.
  Watch: Wi-Fi-inspired needs ~560 decodes per failed packet at -5 dB; DVB-S2-inspired starts in the wrong lobe ~30 %.
- **Receiver code review (lmarg / ddref / fzstop):** pass; baseline bit-identical. Fixes in progress: progress
  entries, rate-keyed early-stop thresholds, a softer FastSCL check, a new lower-SNR arm `fzs-lo`.
  F5 prediction corrected: up to ~25 lost packets per 400k at 2/5 (kill rule stays at +40).
- Next: smoke jobs as soon as the fixes are verified (VPN needed).

## 2026-11-15 13:04 — Final comparison figures: blind's lead is exactly the pilot energy at 2/5, 1/2
- New `testing/plot_final.py` (existing data only) -> `results/final_table.md` + plots `bler_raw_R*`, `bler_norm_R*`
  (95 % error bars), `pareto_R*` (required SNR vs MACs per core). All 23 required-SNR values reproduce §8.2a.
- **Raw axis (pilot energy NOT charged):** at 2/5 blind, genie, DVB-RCS2 ID 13 and 128 ML lie on one curve. So blind
  loses nothing to its CFO search, and its 0.5 dB lead in the fair plot is the pilot energy the others pay.
- **0.15 @ 1e-4:** blind -2.98 [-3.17, -2.57] vs RCS2-13 / 128 ML -3.12: a tie within the CI (64k packets per point).
- **Cost:** blind sits at 0.18-0.27 M MACs per core vs 0.034-0.08 M for the pilot receivers (Pareto plots).
- Doc fix: §8.2a now says its blind numbers are the adopted runs (pooled curves differ by <= 0.07 dB).

## 2026-11-15 12:22 — F5 early stop of failing list decodes: -13 % total, -15 % per core at R = 2/5, 0 right packets lost (offline)
- **Found (32k packets per point, offline replay):** stop a CA-SCL-8 decode when every alive path's normalised frozen-bit
  penalty (the decoder's own, free) exceeds t ~ 0.77 at 70 % of the frozen set. At 2/5 0.5 dB this stops 98.8 % of the
  wrong-candidate decodes and saves 13.0 % of total MACs and 14.8 % per core, with 0 of 31,587 right packets lost
  (half-split check: 2 lost). 0.15 -4 dB: only -3.8 % total / -5 % per core (the first information bits come late
  there); 1/10, 1/2: <= 2 %.
- **Why it works where "frozen-only ranking" failed:** the separation comes from frozen bits AFTER each path's own
  decisions, inside one decode (AUC 0.995-0.9999 from 60 % of the frozen set on), not from ranking cells.
- **Prediction check:** 2/5 MISS high (predicted -3...-8 %), 0.15 MISS low (predicted -5...-10 %).
- **Next:** online flag at 2/5 (and 0.15 at 90 %), 400k paired to confirm a <= 1e-4 loss. Source: Qualcomm US10742238
  (literature scout F5). `testing/results/expected_f3f5.md`, plots `fz_roc.png`, `fz_saving_vs_loss.png`.

## 2026-11-15 12:21 — Your ARS 2021 article = Griebel & Wasenmüller, the DVB-RCS2 estimator our competitor already uses
- **What it is:** O. Griebel, U. Wasenmüller et al., Adv. Radio Sci. 19, 59 (2021): FFT-based CFO estimation for DVB-RCS2
  return-link bursts (zero-filled r c* over all known symbols, FFT, peak + 3-bin parabolic interpolation, phase from the
  peak). Claim: interpolation lets the FFT shrink 4x (8192 -> 2048) for ~0.1-0.2 dB, 2-4x FPGA throughput. Setting: CFO
  up to 1.5 % of Rs (half our range), turbo codes, FER only (no RMSE / CRB); best QPSK estimation loss 0.12-0.15 dB.
  Its reference [4] is EN 301 545-2 V1.1.1 (the DVB-RCS2 standard; history only).
- **Vs ours:** our "RCS2-13" competitor = its DA-KS method + restricted search + exact LS phase + CRC search: ~0 dB
  estimation loss at 0.15, 2/5, 1/2. Its weakness at our range: 1/20 alias picks at 1/10 -5 dB (0.63 dB).
- **Testing next (`expected_ars.md`):** FFT 4096 / 2048 / 2048 + Newton, the faithful one-decode chain, and "RCS2-13
  lobes" (+-1/20 alias search: predicted to close the 1/10 gap to blind to 0.2-0.35 dB), all paired with RCS2-13.
- **Fixed:** our reference entry had wrong author initials and title.
- **Links:** [article](https://ars.copernicus.org/articles/19/59/2021/). Full: `testing/results/lit_ars2021.md`.

## 2026-11-15 12:10 — Your papers list (Yang 2026, Xu 2024, Yue 2026, Wu 2025): none can replace the grid; soft symbols can improve refinement / retry / pns
- **Found:** all four refine CFO/phase from the decoder's SOFT posteriors, starting from a small residual: Yang 2026
  (LDPC partial-metric gradient + Costas loop, within 0.1 dB of ideal sync at Eb/N0 1-2 dB), Yue 2026 (64-point FFT
  acquisition to |f| <= 7.8e-3, then cross-entropy search scored by BP posteriors + Taylor/EM; polar (1024,512) BPSK,
  0.3 / 0.4 dB loss), Xu 2024 (wide-range estimator + EM in LDPC; range not in the abstract), Wu 2025 (EM, |f| <= 2e-4:
  cannot acquire our 0.03). No 2023-2026 paper drives a wide-range search with partial decoder metrics.
- **Adopt (A1):** use soft symbols (tanh of the posterior LLRs, ~8k MACs; or a SCAN backward pass ~45-50k) instead of
  the hard re-encoded codeword in our DD refinement, retry and pns — exactly the measured pns limit (decision errors).
  Test offline on the refinement dumps first. (A2) 2-3 pns iterations with list-1 passes in between.
- **Do not adopt:** cross-entropy / gradient acquisition (our metric is a needle one cell wide: 120 samples hit the true
  cell with p = 0.45).
- **Full texts not readable here (IEEE):** Yang [10.1109/ACCESS.2026.3653159](https://doi.org/10.1109/access.2026.3653159),
  Xu [10.1109/TVT.2024.3383891](https://doi.org/10.1109/tvt.2024.3383891) — worth downloading if you have access.
  Yue preprint [arXiv 2309.12828](https://arxiv.org/html/2309.12828). Full: `testing/results/lit_adopt_codeaided.md`.

## 2026-11-15 12:07 — Complexity ideas: reuse the SC codeword we already compute; one de-rotation per cell
- **A1 (top):** the code-aided retry recomputes a full SC pass the receiver has just done at the same hypothesis — cache
  it (-13...-19 % per core where retries dominate). And "SC first": check CRC + re-encoding on that SC codeword before the
  CA-SCL-8 decode, list only if it fails (Sarkis JSAC 2016, Li-Shen-Tse 2012, Condo PDCCH two-phase). Estimated per core
  -6...-17 %, -20 % at 1/2 2 dB, ~-20 % on fast-path-only points — if SC alone passes ~90 % of right hypotheses (to measure).
- **A2:** share one de-rotation per CFO cell across its phase hypotheses (pi/2 steps are swaps / sign flips): -10...-15 %
  per core at 1/10 -5, 0.15 -4 dB, no BLER risk (a recount from stored counters).
- **A3-A5:** Stage-2 metric on reliable frozen leaves only (-6...-12 % search, offline first); successive halving in the
  refinement scoring (-3...-7 % total); pruned FFT in the fast path (-1...-5 %).
- **Rejected:** dynamic list size (paths already parallel in our model), chirp-z de-rotation, multiplier-free 8-phase,
  SPRT with absolute thresholds.
- **Links:** [Sarkis JSAC 2016](https://ar5iv.labs.arxiv.org/html/1505.01466), [Condo two-phase PDCCH](https://ar5iv.labs.arxiv.org/html/1801.01820),
  [Qualcomm US10742238](https://patents.google.com/patent/US10742238B2/en). Full: `testing/results/lit_adopt_complexity.md`.

## 2026-11-15 12:07 — All sources now in one file: REFERENCES.md (93 sources)
- Every paper, standard and patent cited so far, each with link, what it does, what we took and a dated "Used in" log
  (eqrb <- Geiselhart 2023; pns <- Colavolpe 2005; F3 <- Yuan 2021; est4 competitors <- EN 301 545-2, Griebel 2021,
  Barbieri-Colavolpe 2007, ...). The new survey entries will be merged in next. `BLIND_IMPLEMENTATION/REFERENCES.md`.

## 2026-11-15 12:03 — Where the dB really are: the decoder is ~1.2 dB from the finite-length bound, the CFO search only ~0.2 dB
- **Found [derived from the normal approximation, Coskun et al. 2019]:** with the true CFO and phase, our CA-SCL-8 is
  ~1.3 dB from the finite-blocklength bound at 1/10 and ~1.1-1.2 dB at 0.15, 2/5, 1/2. Blind minus genie is ~0.3 dB at
  1/10, 0.15 and ~0 at 2/5, 1/2, of which ~0.06-0.1 dB is unavoidable. So a better search can win at most x7 BLER at
  1/10 -5 dB, x2 at 0.15 -4 dB and nothing at 2/5, 1/2; the decoder is where the rest is.
- **Top idea — list escalation (P1):** when a packet is about to be lost, decode its best 1-2 hypotheses again with
  list 32 (128 on the best). Literature: Li-Shen-Tse ((2048,1024)+CRC-24, 0.2 dB from the limit), Giard 2017 (+0.35 dB
  from L 8 -> 32 at R = 1/8). Predicted BLER x3-6 lower at 2/5 0.5 dB, x4-10 at 1/2 2 dB, x1.3-1.8 at 0.15 -4 dB, for
  < 0.5 % more total MACs (only would-be failures). Risk: more wrong CRC passes -> recalibrate the re-encoding check.
- **First, a zero-risk diagnostic (T1):** genie with lists 8 / 32 / 128 on 64k packets at the 4 points, and which
  checkpoint drops the true cell at 1/10 -5 dB.
- **Rejected:** PAC codes (gain only at short lengths), OSD / GRAND (too costly at our K), LLR combining across cells
  (~0.02-0.05 dB). Also: more pns passes (P2) for phase noise.
- **Links:** [Coskun et al. 2019](https://ar5iv.labs.arxiv.org/html/1812.08562), [Li-Shen-Tse 2012](https://arxiv.org/abs/1208.3091),
  [Giard 2017](https://ar5iv.labs.arxiv.org/html/1705.02111), [Pillet 2026 SCL-Flip](https://arxiv.org/abs/2605.08492).
  Full: `testing/results/lit_adopt_performance.md`.

## 2026-11-15 12:03 — Military HF: our +-0.03 CFO is exactly the MIL-STD-188-110 requirement (with lots of known symbols)
- **Found:** MIL-STD-188-110C App C / D (tactical HF modems) require sync at +-75 Hz at 2400 Bd = |f| 0.031 cycles/symbol,
  our range; but they carry 11-50 % known symbols (a 1440-symbol preamble alone) and are specified at ~3-4 dB Es/N0 and
  above (+-75 Hz tested at 30 dB). Deployed receivers use banks of frequency hypotheses (Harris US7315588, QinetiQ
  US7715499: 10 Hz bins lose > 2 dB between bins), the same idea as our CFO cells; underwater modems use the 4th-power
  DFT (our fast path). Blind SIGINT estimators reduce to the 4th-power family for QPSK.
- **New competitors (added to est5):** "MIL-110 HF" layout scaled to 1024 data symbols (~308 known, +1.14 dB): expected
  genie + 1.14 dB, i.e. ~0.5-1.2 dB behind blind; "hyb3" (Advantech US7590199: pilot + 4th-power log spectra, 3 CFO
  candidates decided by the decoder) on 16+16 known symbols (+0.13 dB).
- **Side finding:** HF Doppler rate (3.5 Hz/s) would leave ~0.25 rad of quadratic phase over our burst; we do not model a
  CFO ramp yet — a small ramp test is worth adding.
- **Links:** [MIL-STD-188-110C](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf),
  [Advantech US7590199](https://patents.google.com/patent/US7590199), [Hosseini-Perrins 2013](https://ar5iv.labs.arxiv.org/html/1310.0757),
  [ETSI EN 301 841-1 (VDL2)](https://www.etsi.org/deliver/etsi_EN/301800_301899/30184101/01.04.01_60/en_30184101v010401p.pdf).
  Full: `testing/results/lit_real_military.md`.

## 2026-11-15 12:01 — Space agencies and DVB: comparable designs are CCSDS pilot blocks and the ViaSat 4th-power + unique-word burst
- **Found:** official single-carrier standards keep the CFO small (DVB-RCS terminals locked to the network clock:
  1e-8), pull it in over many frames (DVB-S2 pilot FLL: +-0.2 -> 4e-3 in ~100 ms; CCSDS 131.2 SCCC: FFT FLL on a
  256-symbol marker + 16-symbol pilot blocks every 540 symbols, 0.2-0.4 dB loss, lowest mode Es/N0 -0.58 dB), or work
  at higher SNR. DVB-S2X very-low-SNR: 900-symbol unique word, only for CFO <= 1 % of Rs.
- **Most comparable for us:** (1) ViaSat US 7653150: 512-symbol QPSK burst, CFO up to 10 % of Rs, 4th-power FFT +
  16-symbol midamble for the pi/2 ambiguity, ~0.2 dB loss at Es/N0 ~2.6 dB = the industry version of our fast path and
  of our 16+16 competitor; (2) CCSDS / DVB-S2-style pilot blocks with the same 128 known symbols (8 x 16, FFT over all,
  per-block phase + interpolation) as a new competitor C5. Mengali-Morelli is the estimator chosen in a CCSDS study
  (1.2x CRB at -2 dB): already our M&M competitor.
- **GEO numbers:** NCR-locked terminal 140 Hz at 14 GHz; f = 0.03 needs Rs ~53-126 ksps with the RCS2 budget, or ~470
  ksps for a free-running 1 ppm terminal.
- **Links:** [CCSDS 130.11-G-2](https://public.ccsds.org/Pubs/130x11g2.pdf), [ETSI TR 102 376-1 (DVB-S2)](https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf),
  [TR 102 376-2 (S2X VL-SNR)](https://www.etsi.org/deliver/etsi_TR/102300_102399/10237602/01.01.01_60/tr_10237602v010101p.pdf),
  [ViaSat US7653150](https://patents.google.com/patent/US7653150B2/en), [Bertolucci et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8122673/),
  [gr-dvbs2rx](https://github.com/igorauad/gr-dvbs2rx). Full: `testing/results/lit_real_space.md`.

## 2026-11-15 12:00 — Academic state of the art: nobody publishes a blind search at our CFO range and SNR
- **Found:** no single-carrier paper 2015-2026 does a blind CFO search over |f| <= 0.03 at Es/N0 <= -3 dB with BLER, so
  nothing beats us at a comparable point. Closest: Noels-Steendam-Moeneclaey 2005 (1001 QPSK symbols, turbo R = 1/2,
  |f| <= 0.1): code-aided EM reaches the bound only above ~2 dB and needs 128-256 preamble symbols to start;
  Imad-Houcke-Ghogho 2010: the only blind code-aided search as wide as ours (LDPC syndrome cost), ~6x the MCRB at
  Es/N0 ~-0.5 dB, no BLER. Deep-learning CFO papers: none at -5 dB / 1024 symbols with BLER; O'Shea 2017 finds the
  4th-power FFT beats the CNN beyond 1024 samples.
- **For us:** our final CFO RMSE is 2.3-3.8x the MCRB but costs only ~0.04 dB, so BLER is unaffected; worth an
  RMSE-vs-MCRB plot. Suggested competitor: a Noels-style code-aided EM on our pilot layouts (expected: same BLER as our
  pilot receivers, so blind keeps its +0.2 / 0 / +0.5 dB).
- **Links:** [Noels 2005](https://asp-eurasipjournals.springeropen.com/articles/10.1155/ASP.2005.972),
  [Imad 2010](https://link.springer.com/article/10.1155/2010/293572), [Barbieri-Colavolpe-Caire 2007](https://www.tlc.unipr.it/colavolpe/papers/j31.pdf),
  [O'Shea 2017](https://ar5iv.labs.arxiv.org/html/1707.06260). Full: `testing/results/lit_real_academic.md`.

## 2026-11-15 12:00 — Optics, cable, cellular: 400ZR coherent optics uses exactly our CFO range, at +19 dB
- **Found:** 400ZR (coherent optical) specifies a frequency-offset tolerance of +-1.8 GHz at 59.8 GBd = |f| 0.030, our
  range, but at Es/N0 ~19 dB on a continuous stream, with a pilot every 32 symbols (resolves only +-0.016, so coarse CFO
  is blind 4th-power). Li-Zhao-Chen 2014 (1024 QPSK samples, blind): the 4th-power family breaks down at Es/N0
  2.5-5.5 dB, which independently confirms our "4th power fails below 0 dB". DOCSIS, coherent PON, GSM, LTE PRACH,
  microwave modems: all use known symbols at small CFO or 10-25 dB more SNR — covered by our 128-preamble competitor.
- **Optional competitor:** a 400ZR-style layout (32 pilots, 1 per 32 symbols, 0.13 dB, blind coarse + pilot fine + lobe
  search); expected >= 1 dB worse than DVB-RCS2 at 1/10, 0.15.
- **Links:** [IEEE 802.3ct Zhang 2019](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf),
  [Li et al. 2014](https://lightweb.ie.cuhk.edu.hk/wp-content/uploads/publication/1658737499249-Least-squares_carrier_frequency_offset_estimation_for_coherent_optical_QPSK_receivers.pdf),
  [DOCSIS burst patent US8755462](https://patents.google.com/patent/US8755462). Full: `testing/results/lit_real_terrestrial.md`.

## 2026-11-15 12:00 — Satellite (LEO / GEO / IoT): every deployed system pre-compensates or uses known symbols; VDE-SAT is the closest
- **Found:** no deployed system searches the CFO blind with the decoder. 3GPP NTN pre-compensates Doppler to +-0.1 ppm
  (residual 0.013-0.053 of a subcarrier). Closest real standard to our SNRs: **VDE-SAT** (ITU-R M.2092-2): pi/4-QPSK,
  turbo 1/4-1/2, a 27-symbol syncword + 1 pilot per 27 symbols, thresholds Es/N0 -4.5 / -3.6 / -0.6 dB.
  A Viasat patent (US8243859) does what our blind receiver does with a unique word in place of the decoder: 4th-power
  FFT, keep the top 32 peaks, test each. OneWeb downlink uses a 4th-power FFT + PLL (our Stage 1) at ~10 dB.
- **Proposed competitors:** VDE-SAT layout scaled to 1024 symbols (66 known, 0.27 dB; expected 0.15-0.2 dB better than
  DVB-RCS2 but 0.3-0.4 dB behind blind at 2/5, 1/2), and a fairer top-N version of our 16+16 4th-power receiver.
  Also suggested: a CFO-ramp robustness point (0.01 drift over the burst) for narrowband-NTN comparability.
- **Not comparable:** Iridium, AIS, Argos, ORBCOMM (|f| 0.4-1.9: far larger CFO, non-coherent).
- **Links:** [ITU-R M.2092-2](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf),
  [Viasat US8243859](https://patents.google.com/patent/US8243859), [OneWeb, Komodromos-Humphreys 2025](https://www.nature.com/articles/s44459-025-00013-y),
  [3GPP TS 38.101-5](https://itecspec.com/3gpp/38.101-5/s/6.4.1). Full: `testing/results/lit_real_leo.md`.

## 2026-11-15 11:59 — Wi-Fi and short-range radios: no tougher competitor than the ones we already simulate
- **Found:** real single-carrier Wi-Fi / short-range systems work with a much smaller CFO or much more SNR per symbol.
  802.11ad (60 GHz single carrier): +-20 ppm = |f| <= 1.4e-3 cycles/chip, 22x smaller than our 0.03, a 3300-chip
  preamble, and its lowest mode needs ~+3.5 dB per chip. LoRa, BLE Coded, 802.15.4 reach +9...+16 dB per symbol through
  spreading, with non-coherent detection.
- **What they use:** repeated-preamble autocorrelation, coarse then fine (802.11ad lag 128, OFDM Wi-Fi lag 16 / 64,
  802.11b Barker-to-Barker); a BLE long-range patent uses a bank of FFT frequency hypotheses, like our CFO grid.
  Nobody checks more than the CRC: our re-encoding check has no equivalent.
- **Optional extra competitor:** a Wi-Fi-style 128-symbol preamble (8 x 16 coarse + 2 x 64 fine): expected 1.9x the CRB
  and a 1e-3...5e-3 BLER floor near -5 dB from fine-window misses, i.e. worse than our 128-preamble ML.
- **Links:** [802.11ad PHY](https://www.rfwireless-world.com/tutorials/wlan-802-11ad-physical-layer),
  [MathWorks 802.11ad SC PER](https://www.mathworks.com/help/wlan/ug/802-11ad-packet-error-rate-single-carrier-phy-simulation-with-tgay-channel.html),
  [Liu et al. TCSI 2015](https://doi.org/10.1109/TCSI.2014.2361035), [BLE LR patent US 2018/0270091](https://ipiq.io/patents/5237399),
  [LoRa sync, Xhonneux](https://arxiv.org/abs/1912.11344). Full: `testing/results/lit_real_wlan.md`.

## 2026-11-15 11:56 — Averaging over a few list paths finds the true CFO cell far more often (F3)
- **Found:** the checkpoint metric averaged over the best 2-8 list paths ranks the true CFO cell in the top 4 in
  99.9 % of packets at R = 0.15, -4 dB, against 97.4 % for today's single-path metric: 46 packets fixed, 0 broken out of
  1875 (p = 3e-14). Two paths already give 40 of the 46. No change at 0.15 -3 dB (already 100 %), 1/10 -5 dB 99.84 -> 100 %.
- **Source:** Yuan, Coskun & Kramer 2021 (list-marginalised SC metric), via the literature scout's survey (F3).
- **Why it matters:** these "true cell not found" cases are the main error source at the hardest point.
- **Next:** build it into the receiver for the last-checkpoint survivors (2 paths first), 64k paired BLER test.
  `testing/results/expected_f3f5.md`. My prediction was a near-zero gain: wrong.

## 2026-11-15 11:56 — Refinement study: decision-directed Newton beats the grid, 4th-power Newton and the PM parabola fail
- **Found (8k packets per point):** the CFO from a Newton step on the single-path codeword at the cell centre is 2-3x more
  accurate than the current refinement grid (0.25-0.42 vs 0.55-0.79 STEP rms at 1/10, 0.15) at about 1/4 of its MACs.
  4th-power Newton is worse than no refinement at the low rates; the path-metric parabola lacks its neighbour cells in
  59-96 % of cases.
- **Also:** 37 % of the failures at 0.15 -4 dB and 65 % at 2/5 0.5 dB had the true cell refined and still failed:
  refinement can fix more than expected.
- **Next:** online test, decision-directed refinement replacing the grid at 1/10, 0.15, grid as fallback.
  `testing/results/expected_ref.md`.
