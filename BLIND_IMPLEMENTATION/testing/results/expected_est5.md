# est5: deployed preamble / pilot systems as competitors (pilots outside the packet, energy charged), predictions 2026-11-15
Goal (user, 2026-11-15): show that blind reaches the BLER of REAL preamble / pilot-based single-carrier systems without
sending any known symbols. Same framework and back-end as est4 (expected_est4.md): 1024 data symbols carry the whole
codeword, known symbols are extra burst symbols, SNR axis = burst energy per data symbol, same CA-SCL-8 + re-encoding
check + fair metric-ordered CRC search (incl. alias / lobe hypotheses), same packets / CFO / noise. Sources: the
lit_real_*.md surveys (2026-11-15). Already in est4: DVB-RCS2 ID 13 (C1a/b), 128 preamble ML / M&M (C3; Comtech, DOCSIS
class), 64+64 pre/post (C4; Hughes class), 16+16 4th power (C2).

| New competitor | Deployed origin | Layout scaled to 1024 data symbols | Nk (dB) | Estimator chain |
|---|---|---|---|---|
| C6 VDE-SAT | ITU-R M.2092-2 (VDES satellite) | 27-symbol syncword, then 1 pilot per 27 data symbols | 66 (0.27) | ML on the syncword + Rife-Boorstyn over all known symbols, CRC search over the +-1/27 alias lobes |
| C7 DVB-S2 style | ETSI EN 302 307 / TR 102 376 | 90-symbol PL header (SOF 26 + PLS 64) + one 36-symbol pilot block mid-burst | 126 (0.50) | M&M / L&R on the header, then joint ML header + pilot block with lobe search |
| C8 CCSDS style | CCSDS 131.2 / 130.11-G | 8 pilot blocks of 16 symbols spread over the burst (block period ~146) | 128 (0.51) | FFT (R-B) over all blocks + lobe search, per-block ML phase + linear interpolation |
| C9 ViaSat burst | US 7653150 + US 8243859 | 16-symbol midamble unique word | 16 (0.07) | 4th-power FFT over the burst, top-32 peaks each checked on the UW (pi/2 ambiguity), CRC search |
| C10 NB-IoT / LTE DMRS style | 3GPP 36.211 (NPUSCH) | 1 pilot per 7 symbols | 171 (0.67) | R-B over the pilots (range +-0.071, no aliases at 0.03), pilot phase + interpolation |
| C11 Sparse pilots 1/32 (400ZR-inspired) | OIF 400ZR | 1 pilot per 32 data symbols | 33 (0.14) | blind 4th-power coarse, R-B on the pilots, CRC search over the +-1/32 alias lobes |
| C12 Wi-Fi style | IEEE 802.11 (coarse/fine preamble) | 128-symbol preamble: 8 x 16 repeats (lag 16 coarse), lag 64 fine | 128 (0.51) | autocorrelation coarse + fine, CRC search over the +-4 fine lobes (1/64) |
| C13 MIL-110 HF | MIL-STD-188-110C App C serial tone (design CFO +-75 Hz at 2400 Bd = 0.031) | 184-symbol preamble + 4 x (256 data + 31-symbol probe) | 308 (1.14) | R-B over all known symbols, CRC search over the +-3 probe-period lobes (1/287); const phase (AWGN), track (Kalman over the probes) for phase noise |
| C14 hyb3 | Advantech US 7590199 (hybrid DA + NDA) | 16 + 16 pre/post (as C2) | 32 (0.13) | log DA spectrum + log 4th-power spectrum summed, 3 best peaks; metric-ordered CRC search over the 3 candidates + their lobes |

Nk (dB) checked against est4/common.py (Nk = len(known_idx), dB = 10 log10((1024 + Nk) / 1024)) on 2026-11-15: C6 66
(was ~65), C7 0.50 (was 0.52), C8 0.51 (was 0.52), C10 171 / 0.67 (was ~171 / 0.69), C11 33 / 0.14 (was 32 / 0.13);
<= 0.02 dB, the predictions below are unchanged (made with the old values). Airtime, where quoted (competitors.md) =
Nk / 1024 (extra symbols relative to the data); 08 section 8.3 uses the burst share Nk / (1024 + Nk).

## Predictions (no phase noise; at the plotted, energy-charged SNR; blind numbers from 8.2a)
- C6 VDE-SAT: the best new competitor at 2/5, 1/2: 0.15-0.2 dB better than DVB-RCS2 ID 13 (lower overhead), still
  0.3-0.4 dB behind blind; at 1/10, 0.15 equal to ID 13 within +-0.1 dB, alias errors (lobe 0.59 of the peak) below 1e-4.
- C7 DVB-S2 style, C8 CCSDS style: like 128 ML / ID 13 within +-0.1 dB (same energy); C8 may show alias errors at -5 dB.
- C9 ViaSat: fails below ~0 dB like C2 (4th power), but the top-32 + UW check makes it 1-2 dB better than C2 at 1/2 and
  2/5 0.5-1 dB; BLER ~1e-1 at 0.15 -3 dB.
- C10 dense DMRS: 0.1-0.2 dB worse than ID 13 in AWGN (more overhead), the best under phase noise with tracking.
- C11 400ZR: >= 1 dB worse than ID 13 at 1/10, 0.15 (pilot energy too low for the coarse step), close at 2/5, 1/2.
- C12 Wi-Fi: worse than 128 ML; a BLER floor ~1e-3 near -5 dB from fine-lobe misses unless the CRC lobe search catches them.
- C13 MIL-110 HF: genie + 1.14 dB in AWGN: about -4.05 / -2.8 / 1.8 / 3.0 dB at the 8.2a targets (1/10 1e-4, 0.15 1e-3,
  2/5 1e-3, 1/2 1e-3) vs blind -4.9 / -3.60 / 0.61 / 1.79.
- C14 hyb3: better than the 16 + 16 4th-power receiver (C2) at 2/5, 1/2; still failing at 1/10, 0.15.
- Overall: blind matches or beats every one of them in BLER (best case for them: tie at 0.15), with 0 known symbols.

## Predicted comparison with blind (written before the runs, 2026-11-15)
Required SNR [dB] at the 8.2a targets on the fair axis (pilot energy charged). **Gap = competitor - blind: positive =
blind needs less SNR (blind better), negative = the competitor is better.** Blind is measured (8.2a / final_table.md);
competitor numbers are predictions (genie + pilot energy + estimated loss, method in competitors.md). MACs per core:
blind measured at its required SNR (0.200 / 0.262 / 0.209 / 0.083 M); competitors predicted.

| Competitor | 1/10 @1e-4 (blind -4.90) | 0.15 @1e-3 (blind -3.60) | 2/5 @1e-3 (blind 0.61) | 1/2 @1e-3 (blind 1.79) | Predicted verdict vs blind | MACs per core (blind / competitor) |
|---|---|---|---|---|---|---|
| C6 VDE-SAT | -4.85 ... -4.6 (gap +0.05 ... +0.3) | -3.6 ... -3.4 (0 ... +0.2) | 0.9 ... 1.0 (+0.3 ... +0.4) | 2.15 ... 2.25 (+0.35 ... +0.45) | tie at 1/10, 0.15; blind better by ~0.4 dB at 2/5, 1/2 (its lead = the 0.27 dB pilot energy + small loss) | ~0.04-0.06 M: blind 2-6x more |
| C7 DVB-S2-inspired | -4.65 ... -4.5 (+0.25 ... +0.4) | -3.4 ... -3.3 (+0.2 ... +0.3) | 1.15 ... 1.2 (+0.55 ... +0.6) | 2.4 ... 2.5 (+0.6 ... +0.7) | blind better everywhere, 0.2-0.7 dB | ~0.05-0.1 M (many lobe decodes at -5 dB): blind 2-4x more |
| C8 CCSDS-inspired (const and blocks) | -4.65 ... -4.3 (+0.25 ... +0.6) | -3.4 ... -3.2 (+0.2 ... +0.4) | 1.15 ... 1.25 (+0.55 ... +0.65) | 2.4 ... 2.5 (+0.6 ... +0.7) | blind better everywhere; "blocks" ~= const in AWGN (it matters only under phase noise) | ~0.05-0.1 M: blind 2-4x more |
| C9 ViaSat burst | fails (BLER > 0.1) | fails | 1.5 ... 2.5 (+0.9 ... +1.9) | 2.2 ... 2.8 (+0.4 ... +1.0) | blind far better; works only at high SNR | ~0.04 M: blind 2-5x more |
| C10 DMRS 1/7 | -4.5 (+0.4) | -3.2 (+0.4) | 1.33 (+0.7) | 2.6 (+0.8) | blind better by 0.4-0.8 dB in AWGN (highest overhead); its strength is phase noise, not tested here | ~0.035 M: blind 2-7x more |
| C11 Sparse pilots 1/32 | -4.4 ... -3.9 (+0.5 ... +1.0) | -3.5 ... -3.0 (+0.1 ... +0.6) | 0.8 ... 1.0 (+0.2 ... +0.4) | 2.05 ... 2.2 (+0.25 ... +0.4) | closest competitor at 2/5, 1/2 (lowest overhead); uncertain at low SNR (see note) | ~0.045 M: blind 2-6x more |
| C12 Wi-Fi-inspired | -4.6 ... -4.3 (+0.3 ... +0.6) | -3.4 ... -3.2 (+0.2 ... +0.4) | 1.2 ... 1.3 (+0.6 ... +0.7) | 2.45 ... 2.55 (+0.65 ... +0.75) | blind better 0.2-0.75 dB; possible floor near -5 dB | estimator < 1k MACs, but ~560 decodes per failed packet at -5 dB: the ratio may shrink there |
| C13 MIL-110-inspired | -4.05 (+0.85) | -2.8 (+0.8) | 1.8 (+1.2) | 3.0 (+1.2) | blind better by ~1 dB (1.14 dB of pilots) | ~0.035 M: blind 2-7x more |
| C14 hyb3 | fails | fails | 1.2 ... 2.0 (+0.6 ... +1.4) | 2.2 ... 2.6 (+0.4 ... +0.8) | blind better; fails at low SNR (4th power) | ~0.04 M: blind 2-5x more |

Summary prediction: **no competitor beats blind at any of the 4 targets**; the closest are C6 VDE-SAT (tie at 1/10, 0.15)
and C11 (0.2-0.4 dB behind at 2/5, 1/2). Blind pays 2-7x the MACs per core. Where blind's lead is <= 0.1 dB it is inside
the unpaired noise (blind and est5 run on different packets). The measured 0.15 @1e-4 point (blind -2.98 vs ID 13 / 128 ML
-3.12, a tie within blind's CI) says a competitor CAN edge blind at the 1e-4 target of 0.15; expect the same there for C6.

Notes on consistency (2026-11-15): the per-competitor bullets above were the first estimates; the table uses the later,
more careful values from competitors.md. Two differ: C6 at 1/10 (bullet: "equal to ID 13" = -4.1; table: -4.85 ... -4.6,
because unlike ID 13 its alias lobes are searched) and C11 at 1/10, 0.15 (bullet: ">= 1 dB worse than ID 13", i.e. gap
>= +1.8 / +1.15; table: +0.5 ... +1.0 / +0.1 ... +0.6, because the +-1/32 lobe search covers the range even when the
4th-power coarse step fails). The smoke and full runs decide; both versions are kept so the miss can be scored.

## As implemented (code-editor, 2026-11-15; est4/common.py, est4/estimators.py, est4/run_bler.py; not run yet)
Layouts (Nk, K, energy dB, alias / lobe spacing, lobe hypotheses each side): vde27 27 sync + 13 d + 1 p + 38 x (26 d + 1 p)
+ 23 d (pilots at 40, 67, ..., 1066 as M.2092-2 A5-2.10; fixed 2026-11-15 from 39 x (26 d + 1 p) + 10 d, which put every
pilot 13 symbols late; lit_vdesat_format.md): 66, 1090, 0.27, 1/27, 1; dvbs2 90 + 512 d + 36 + 512 d: 126, 1150, 0.50, 1/575, 3; ccsds8 8 x 16, gaps 146/147: 128,
1152, 0.51, 1/162.3, 5 (all in range); viasat16 512 d + 16 UW + 512 d: 16, 1040, 0.07, -; dmrs7 171 x (3 d, p, 3 d)
(last slot 1 d after the pilot): 171, 1195, 0.67, 1/7 (outside +-0.03, no lobes); zr32 33 x (p + 31 d) + 1 d: 33, 1057,
0.14, 1/32, 1; wifi128 16-symbol sequence x 8: 128, 1152, 0.51, 1/64 (fine lag), 4; mil110 184 + 4 x (256 d + 31): 308,
1332, 1.14, 1/287, 3; hyb3 on prepost16 (32, 1056, 0.13, 1/1040, 3) + 2 extra candidates with their lobes.
- est5 CRC search: lobe hypotheses only with the lobe centre inside |f| <= 0.03 + M STEP (per packet; metric passes counted
  only for those). ViaSat UW: window M from the 4th-power bound over the burst (crb_nda4), not the 16-symbol UW CRB
  (which would give M ~ 600). ViaSat UW pick: |U|^2 / (Nk s2) + |X4|^2 / mean in-range |X4|^2 (patent: weighted joint
  frequency + UW metric, weight 1).
- C9 ViaSat UW (review 2026-11-15): the 16-symbol UW barely ranks the 32 candidates (its frequency resolution is about
  1/16), so the pick is effectively the 4th-power peak; the top-32 + UW gain over C2 predicted above may not appear.
- C7 DVB-S2 style (review 2026-11-15): about 30 % of packets start in the wrong 1/575 lobe at -5 dB (M&M on the 90-symbol
  header), so expect large extra_decodes there (the lobe search fixes them at a decode cost).
- C12 Wi-Fi: LOBE_N = 4 fine lobes each side (the lag-16 coarse range 1/32 wraps) raises its search cost: about 560 valid
  offsets at -5 dB, all metric-scored and decoded for a packet that never passes.
- Jobs: e5-10 / 15 / 25 / 2 (seeds 62-65; Genie + C6, C7, C8, C8 blocks ("CCSDS style blocks", added 2026-11-15), C10,
  C11, C12, C13; pn 0 only, no phase-noise arm), e5-pp (C9, C14 + C2, --min-err 200 over 120 chunks = 2 errors per
  source per chunk, so the full 480k only where every source has BLER below about 5e-4; same seeds), e5-smoke (seed 61;
  a, b pn 0 all new sources + Genie + CCSDS blocks; c pn 1e-4 the track variants).
- McNemar pairing (all est4 / est5 parts): n10 / n01 per source against mcnemar_ref (RCS2-13 if in the job, else RCS2
  pre/post, else the first source, i.e. Genie in e5-10 / 15 / 25 / 2).
