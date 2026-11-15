# q_fix, and dd / dd_win4 with q_fix: measured results (2026-11-13)

## Source and method

- Script: `py BLIND_IMPLEMENTATION/testing/agg_qfix.py`.
- Parts: `blind_ber_t-qfx10`, `-qfx25`, `-qfx2`, `-ddq10`, `-ddq25`, `-ddq2` (the smoke parts are excluded).
- Packets are paired on (chunk_seed, fe_idx), and errors are compared with the exact McNemar test.
- MACs are the mean per packet; per core = crit_par.
- Changes are paired, with the delete-one-chunk jackknife SE.
- The qfx and ddq jobs used different seeds, so their packets are disjoint and can be pooled.

## Table 1: q_fix vs base (paired, same packets)

MACs are in millions per packet. "ch." is the paired change.

| R | SNR | n | err base -> qfix | fixed / broken (p) | per core [M] | core ch. | total [M] | total ch. | dec/pk |
|---|---|---|---|---|---|---|---|---|---|
| 1/10 | -1 | 64k | 0 -> 0 | 0/0 | 0.2015 -> 0.1980 | -1.7+-0.1 % | 1.945 -> 1.903 | -2.1 % | 2.76 -> 2.70 |
| 1/10 | 0 | 64k | 0 -> 0 | 0/0 | 0.1533 -> 0.1511 | -1.5+-0.1 % | 1.438 -> 1.413 | -1.8 % | 2.22 -> 2.18 |
| 0.15 | -1 | 128k | 17 -> 17 (1.33e-4) | 1/1 (p=1) | 0.2371 -> 0.2252 | -5.0+-0.4 % | 2.344 -> 2.237 | -4.5 % | 3.06 -> 2.83 |
| 0.15 | 0 | 64k | 0 -> 0 | 0/0 | 0.1686 -> 0.1645 | -2.4+-0.2 % | 1.586 -> 1.543 | -2.7 % | 2.26 -> 2.19 |
| 0.15 | +1 | 64k | 0 -> 0 | 0/0 | 0.0986 -> 0.0974 | -1.2+-0.1 % | 0.880 -> 0.868 | -1.5 % | 1.47 -> 1.45 |
| 2/5 | 0.5 | 64k | 163 -> 150 | **21/8 (p=0.024)** | 0.4315 -> 0.3712 | **-14.0+-1.7 %** | 3.784 -> 3.395 | **-10.3+-1.1 %** | 7.37 -> 6.12 |
| 2/5 | 1 | 64k | 5 -> 4 | 1/0 | 0.1272 -> 0.1240 | -2.5+-0.8 % | 1.267 -> 1.246 | -1.7 % | 1.65 -> 1.59 |
| 1/2 | 2 | 64k | 10 -> 12 | 1/3 (p=0.62) | 0.0840 -> 0.0833 | -0.8+-0.6 % | 0.739 -> 0.735 | -0.6 % | 1.08 -> 1.07 |
| 1/2 | 2.5 | 64k | 0 -> 0 | 0/0 | 0.0751 -> 0.0750 | 0 % | 0.577 -> 0.577 | 0 % | 1.007 -> 1.006 |

- **Undetected errors.** There is one in the whole set: 0.15 -1 dB, tag acc_fast_retry_wrong. It is the same packet in both arms.
- **Zero-error points.** These support only an upper bound: BLER < 4.7e-5 per 64k (95 %).

## Table 2: q_fix pooled vs nofast15 at R = 0.15 (unpaired)

| SNR | base10_qfix | nofast15 | p | per core qfix -> nofast15 | total qfix -> nofast15 |
|---|---|---|---|---|---|
| -1 | 21/192k = 1.09e-4 [6.8e-5, 1.7e-4] | 0/400k | 5e-11 | 0.2245 -> 0.180 (-20 %) | 2.234 -> 2.59 (+16 %) |
| 0 | 0/128k | 0/400k | 1 | 0.1646 -> 0.148 (-10 %) | 1.545 -> 2.13 (+38 %) |

## Table 3: dd_qfix and dd_win4_qfix vs their q_fix baseline (paired, 64k each)

| R | SNR | base err | dd err (fixed/broken) | dd_win4 err | base core [M] | dd core | win4 core | dd total | win4 total |
|---|---|---|---|---|---|---|---|---|---|
| 1/10 | -1 | 0 | 0 | 0 | 0.1982 | +2.1 % | +9.3 % | -1.0 % | +2.3 % |
| 0.15 | -1 | 4 | 4 (0/0) | 4 | 0.2230 | +1.5 % | +6.6 % | -1.3 % | -2.2 % |
| 0.15 | 0 | 0 | 0 | 0 | 0.1647 | +1.7 % | +6.3 % | -1.2 % | -0.6 % |
| 2/5 | 0.5 | 143 | **186 (8/51, p=9e-9)** | 186 | 0.3756 | +11.2 % | +10.3 % | +6.1 % | +4.4 % |
| 2/5 | 1 | 3 | 3 | 3 | 0.1225 | +0.7 % | +0.8 % | 0 % | -0.2 % |
| 1/2 | 2 | 9 | 9 | 9 | 0.0846 | +0.6 % | +0.4 % | +0.3 % | -0.1 % |
| 1/2 | 2.5 | 0 | 0 | 0 | 0.0750 | 0 % | 0 % | 0 % | 0 % |

## Conclusions

1. **q_fix is neutral or better.**
   - At 2/5 0.5 dB it fixes 21 packets and breaks 8 (p = 0.024).
   - Everywhere else the change is 0/0 or within noise.
2. **q_fix lowers MACs per core** by:
   - -1.2 ... -5 % at 1/10 and 0.15;
   - -14 % at 2/5 0.5 dB;
   - about 0 at 1/2.
3. **q_fix does not remove the 0.15 -1 dB bump.**
   - Paired: 17 -> 17 errors per 128k.
   - Pooled q_fix gives 1.09e-4, against 0/400k for nofast15.
   - So the bump is not the pi/4 index bug; the 4 phases (nph15) are what remove it.
4. **dd with q_fix gains nothing.**
   - It fixes 0 packets at all 7 points.
   - At 2/5 0.5 dB it is worse: 8 fixed / 51 broken, +11 % per core.
   - dd_win4 costs +6 ... +9 % per core at 1/10 and 0.15.
   - dd is not adopted.
5. **Too few errors for a BLER claim on q_fix** at 0.15 0 dB and at 1/2 2 dB.

## Open questions

- What causes the 2-phase bump at 0.15 -1 dB? The 16 shared error packets could be inspected in a dump.
- Why does dd break 51 packets at 2/5 0.5 dB?
