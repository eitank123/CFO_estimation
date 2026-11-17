# tw: the testing blind receiver over the full SNR range (predictions 2026-11-15, before the runs)

**Why:** the user asked (2026-11-15) for the testing model on the entire SNR range so it can be compared with the new
competitors (est5, ARS). Until now the blind numbers mixed models: 1/10, 0.15 = testing (`testing_s11g`, 64k per point);
2/5 = testing only at 0.5, 1.0 dB; 1/2 = testing at 2.0, 2.5 dB and the presentation receiver at 1.5 dB. And the 1/10
1e-4 crossing rested on 10 and 1 errors (64k at -5 and -4.5 dB).

**Jobs** (single arm, no paired baseline; `--max-frames 4000` per chunk; seeds 8201-8206; new data pooled with the
existing testing-model runs of the same receiver):

| Job | Receiver | Points (packets) |
|---|---|---|
| tw10a | testing_s11g | 1/10 -5, -4.5 dB (480k each) |
| tw10b | testing_s11g | 1/10 -4 (480k), -3.5 (256k) |
| tw15a | testing_s11g | 0.15 -3 (480k) |
| tw15b | testing_s11g | 0.15 -2.5 (480k), -5, -4.5 (64k each, the missing low end) |
| tw25 | base25_qfix / base2_qfix | 2/5 0 (64k), 1.5 (256k), 2 (128k); 1/2 1.5 (64k), 3 (128k), 3.5 (128k) |

Runtime estimate: 0.14-0.19 s per packet per core at low SNR -> tw10a ~2.3 h, tw15a ~1.3 h, tw15b ~1.5 h, tw10b ~1.8 h,
tw25 < 0.5 h.

## Predicted BLER per point (from the existing runs)
| Rate, SNR | Existing | Predicted |
|---|---|---|
| 1/10 -5 | 10 / 64k = 1.6e-4 | 0.8 ... 2.5e-4 (40-120 errors in 480k) |
| 1/10 -4.5 | 1 / 64k | 0.5 ... 3e-5 (3-15 errors) |
| 1/10 -4, -3.5 | 1 / 64k, - | 0 ... 1e-5 |
| 0.15 -5 | - (onl-smoke: 0.13-0.21) | 0.15 ... 0.2 |
| 0.15 -4.5 | - | 1.5 ... 4e-2 |
| 0.15 -3 | 7 / 64k = 1.1e-4 | 0.6 ... 2e-4 (30-90 errors) |
| 0.15 -2.5 | 1 / 64k | 0.5 ... 4e-5 (3-20 errors) |
| 2/5 0 | presentation 115 / 1.9k = 6e-2 | 4 ... 8e-2 |
| 2/5 1.5, 2 | presentation 0 / 721k, 0 / 621k | 0 ... 2 errors |
| 1/2 1.5 | presentation 690 / 59.8k = 1.15e-2 | 0.9 ... 1.4e-2 (same receiver within noise) |
| 1/2 3, 3.5 | presentation 0 | 0 errors |

## Predicted required SNR and the comparison with the competitors
| Target | Now (8.2a) | Predicted (testing model only, pooled) | Effect on the vs-blind tables |
|---|---|---|---|
| 1/10 @1e-4 | -4.90 (10 / 1 errors) | -5.0 ... -4.75, CI ~ +-0.1 dB instead of [-, -4.56] | gaps change by <= 0.15 dB |
| 0.15 @1e-3 | -3.60 | -3.65 ... -3.55 (new -4.5 dB point brackets it) | <= 0.05 dB |
| 0.15 @1e-4 | -2.98, CI [-3.17, -2.57] | -3.05 ... -2.85, CI ~ +-0.1 dB | decides whether RCS2-13 / 128 ML (-3.12) really edge blind there |
| 2/5 @1e-3 | 0.61 | 0.58 ... 0.64 | none |
| 1/2 @1e-3 | 1.79 (mixed models) | 1.75 ... 1.85, all testing model; MACs interpolated instead of the 2 dB value | <= 0.05 dB |

Kill / flag rule: if a testing-model point disagrees with the presentation receiver at the same SNR beyond the 95 %
CIs, report it (the two models are assumed equal in BLER).

## Measured (2026-11-15 21:00)
tw10a2, tw10b, tw15a2 (19:40) and tw25 / tw2 (21:00): ALL DONE, no Traceback. tw15b still running.
| Rate, SNR | Predicted | Measured (pooled testing model) |
|---|---|---|
| 1/10 -5 | 0.8 ... 2.5e-4 | 2.2e-4 (118 / 544k) hit |
| 1/10 -4.5 | 0.5 ... 3e-5 | 3.7e-5 (20 / 544k) close miss (just above) |
| 1/10 -4, -3.5 | 0 ... 1e-5 | 5.5e-6 (3 / 544k), 0 / 256k hit |
| 0.15 -3 | 0.6 ... 2e-4 | 1.3e-4 (72 / 544k) hit |
| 2/5 0 | 4 ... 8e-2 | 5.9e-2 (3775 / 64k) hit; MACs per core 1.70 M there |
| 2/5 1.5, 2 | 0 ... 2 errors | 0 / 256k, 0 / 128k hit |
| 1/2 1.5 | 0.9 ... 1.4e-2 | 1.11e-2 (711 / 64k) hit (presentation 1.15e-2: same within noise, no flag) |
| 1/2 3, 3.5 | 0 | 0 / 128k each hit |

| Target | Predicted | Measured |
|---|---|---|
| 1/10 @1e-4 | -5.0 ... -4.75 | -4.78 [-4.86, -4.69] hit |
| 0.15 @1e-4 | -3.05 ... -2.85 | -2.93 [-3.00, -2.61] hit (-2.5 dB point still 64k until tw15b) |
| 2/5 @1e-3 | 0.58 ... 0.64 | 0.61 hit |
| 1/2 @1e-3 | 1.75 ... 1.85 | 1.79 hit, now all testing model |

### tw15b (2026-11-15 ~23:10, ALL DONE, no Traceback)
| Point | Predicted | Measured |
|---|---|---|
| 0.15 -2.5 | 0.5 ... 4e-5 | 2.0e-5 (11 / 544k) hit |
| 0.15 -5 | 0.15 ... 0.2 | 0.19 (12368 / 64k) hit |
| 0.15 -4.5 | 1.5 ... 4e-2 | 3.1e-2 (1967 / 64k) hit |
0.15 @1e-4: -2.93, CI now [-2.99, -2.83] (was [-3.00, -2.61]). RCS2-13 -3.12 [-3.16, -3.07], 128 ML -3.12, G4096
-3.11, CCSDS style -3.07 [-3.12, -3.02]: the CIs no longer overlap, so **blind really trails them by 0.15-0.20 dB at
0.15 @1e-4** (predicted "decides whether RCS2-13 / 128 ML really edge blind": they do). DMRS 1/7 ties (+0.01).
