# spec11 final checks (jobs spec1m-a/b/c, spnoise): predictions, written 2026-11-13 before any result

Arms: `nofast15_qfix` (= the testing receiver below +0.5 dB) vs `nofast15_qfix_spec11` (speculative decode accepted only
at rho > 1.1 x thr). Same packets in both arms.

## 1. Undetected errors, 1/10 -5 dB, 600k more packets (spec1m-a/b/c, 200k each, new seeds)
Together with t-spec10a-d (400k): 1e6 paired packets.
- Errors: base ~150 (2.45e-4 x 600k), spec11 within +-3 of base, discordant pairs <= 3.
- Undetected: base 0 ... 3 on the 600k; spec11 - base in {-1, 0, +1}. Over 1e6: spec11 <= base + 1.
- Per core (scheduled) -13 ... -16 %, total -18 ... -21 % (as on the 400k).
- Adoption rule: spec11 undetected <= base + 1 over 1e6 AND the noise check below passes.

## 2. Noise-only false alarms (spnoise: 1/10 -5 dB and 0.15 -4 dB, 1600 noise packets per arm and point)
A noise packet "passes" if the receiver accepts any codeword (CRC + re-encoding check).
- Base: 0 accepted (the rho check rejected 1046 / 1046 noise CRC passes before).
- spec11: 0 accepted (its threshold is stricter than the base one); CRC passes per noise packet the same order as base.
- Fail if spec11 accepts more noise packets than base.

The smoke (spnoise-smoke, 25 noise packets x 4 chunks) only checks that --noise-only runs through testing/run.py.

## Smoke (t-spnoise-smoke, 1/10 -5 dB, 400 noise packets per arm, 2026-11-13)
EVAL DONE + ALL DONE, no Traceback. Both arms: 0 noise packets accepted; 73 CRC passes each (the same ones), all 73
rejected by the re-encoding check; ~814 decodes per noise packet (the whole search runs), ~4 CPU-s per packet.

## Measured (2026-11-13; all logs EVAL DONE + ALL DONE, no Traceback)
### 1. 1/10 -5 dB, paired
| Packets | base errors | spec11 errors | discordant (fixed / broken) | undetected base / spec11 | per core (scheduled) | total |
|---|---|---|---|---|---|---|
| spec1m-a/b/c (600k) | 111 | 111 | 0 / 0 | 1 / 1 | 0.241 -> 0.206 M (-14.6 %) | 4.87 -> 3.92 M (-19.5 %) |
| + t-spec10a-d (1e6) | 209 | 209 | 0 / 0 | 2 / 2 | 0.242 -> 0.207 M (-14.5 %) | 4.87 -> 3.93 M (-19.4 %) |
- vs predictions: errors ~150 predicted on 600k, measured 111 (BLER 1.85e-4 vs 2.45e-4: a little better, within the
  earlier interval); spec11 = base packet for packet: HIT. Undetected 1 / 1 (predicted base 0 ... 3, difference 0): HIT.
  Per core -14.6 % (predicted -13 ... -16 %), total -19.5 % (-18 ... -21 %): HIT.

### 2. Noise only (spnoise, 1600 noise packets per arm and point)
| Point | accepted base / spec11 | per core base / spec11 | total base / spec11 |
|---|---|---|---|
| 1/10 -5 dB | 0 / 0 | 15.63 / 15.65 M | 283.2 / 283.4 M |
| 0.15 -4 dB | 0 / 0 | 16.48 / 16.50 M | 290.2 / 290.4 M |
- HIT: no false alarm in either arm; the CRC passes are the same packets and all are rejected by the re-encoding check.
  (The full search runs on a noise packet: ~16 M per core, ~290 M total, i.e. ~65x / ~60x a normal packet; the hard cap
  in expected_cap_pn_comb.md stops this at 2 M.)

### Decision
Both adoption conditions hold (undetected spec11 = base over 1e6; 0 noise false alarms). **spec11 is adopted**: the
testing receiver at 1/10 and 0.15 is now `nofast15_qfix_spec11` (speculative decode accepted at rho > 1.1 thr). BLER is
unchanged (0 discordant packets in 1e6 + 128k); per core -14.5 % at 1/10 -5 dB, -6.9 / -4.5 % at 0.15 -4 / -3 dB.
2/5 and 1/2 are unchanged (spec11 not tested there).
