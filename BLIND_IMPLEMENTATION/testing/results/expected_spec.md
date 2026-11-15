# Speculative decode with a stricter acceptance (jobs spec10a-d, spec15): predictions, written 2026-11-13 before any result

## What is tested
- `nofast15_qfix_spec`: the testing receiver + q_fix + win_spec = 4 (for 4 < z <= 6 at a checkpoint, one CA-SCL
  decode without the CA retry; the cell stays a later candidate).
- `nofast15_qfix_spec11`: the same, a speculative decode accepted only if rho > 1.1 x the re-encoding threshold.
- Baseline `nofast15_qfix`; all three on the same packets: 1/10 -5 dB 400k (4 jobs x 100k), 0.15 -4 / -3 dB 64k.

## Why
nofast_spec_t (1/10 -5 dB, 400k, t-cnf): per core -12 % vs nofast, but 2 undetected errors; both wrong speculative CRC
passes had rho / thr in [1.0, 1.1), against 573 of 107 317 right ones (0.5 %). The 1.1 margin was chosen on those
same 2 events, so it needs fresh packets.

## Predictions
| Point | spec vs base: per core | spec11 vs base: per core | total (both) | errors | undetected spec / spec11 |
|---|---|---|---|---|---|
| 1/10 -5 dB (400k) | -8 ... -12 % | -7 ... -12 % (0.5 % of spec accepts lost, retried later) | -12 ... -18 % | same within noise | 1 ... 4 / 0 ... 1 |
| 0.15 -4 dB (64k) | -3 ... -6 % | -3 ... -6 % | -6 ... -10 % | same within noise | 0 ... 2 / 0 ... 1 |
| 0.15 -3 dB (64k) | -0 ... -3 % | -0 ... -3 % | -4 ... -8 % | same | 0 / 0 |

Adoption rule: spec11 is adopted if per core falls >= 5 % at 1/10 -5 dB, the paired BLER change is not significant, and
undetected <= the baseline's + 1 at 400k.

## Measured: 1/10 -5 dB, 400k paired (t-spec10a-d, 2026-11-13)
All 4 logs EVAL DONE + ALL DONE, no Traceback, no duplicated chunk.
| arm | errors | undetected | per core | scheduled per core (h + d4a) | total | decodes / pk | spec decodes / passes / wrong passes |
|---|---|---|---|---|---|---|---|
| nofast15_qfix | 98 (2.45e-4) | 1 | 0.2894 M | 0.2420 M | 4.881 M | 1.40 | - |
| spec (1.0) | 99 (0 fixed / 1 broken) | 2 | -12.0 % | -14.6 % | -19.5 % | 1.56 | 171569 / 107225 / 1 |
| spec11 (1.1) | 98 (0 / 0) | 1 (same as base) | -11.8 % | -14.4 % | -19.4 % | 1.56 | 171582 / 106609 / 0 |
- Per core: hit (predicted -7 ... -12 %). Total: -19.4 % vs predicted -12 ... -18 % (slight miss, more saving).
- BLER: identical on the same packets (0 discordant). Undetected: spec11 adds none; plain spec added 1 (its wrong
  speculative pass, again in the 1.0-1.1 band).
- Adoption rule (per core >= 5 %, BLER not significant, undetected <= base + 1): spec11 PASSES at 1/10 -5 dB. Before final
  adoption (strategist): 0.15 (t-spec15, running), >= 1e6 packets for undetected errors, noise-only false alarms.

## Measured: 0.15, 64k paired (t-spec15, 2026-11-13)
EVAL DONE + ALL DONE, no Traceback. Per core = scheduled count.
| point | arm | errors (fixed / broken) | undetected | per core | (earlier count) | total |
|---|---|---|---|---|---|---|
| -4 dB | nofast15_qfix | 302 (4.72e-3) | 1 | 0.443 M | 0.639 M | 8.42 M |
| -4 dB | spec (1.0) | 302 (0 / 0) | 1 | -7.4 % | -5.2 % | -10.7 % |
| -4 dB | spec11 (1.1) | 302 (0 / 0) | 1 | -6.9 % | -4.9 % | -10.2 % |
| -3 dB | nofast15_qfix | 8 (1.25e-4) | 0 | 0.190 M | 0.238 M | 3.68 M |
| -3 dB | spec (1.0) | 8 (0 / 0) | 0 | -4.6 % | -3.8 % | -8.5 % |
| -3 dB | spec11 (1.1) | 8 (0 / 0) | 0 | -4.5 % | -3.4 % | -8.4 % |
- BLER identical on the same packets at both points; no extra undetected error.
- Saving smaller than at 1/10 (-5 dB: -14.4 %): at 0.15 more packets need the full search, where the speculative decode
  does not help. spec11 passes the adoption rule (per core >= 5 %) at -4 dB, just misses it at -3 dB (-4.5 %), BLER and
  undetected neutral everywhere.
- Still open before final adoption: >= 1e6 packets for undetected errors, noise-only false alarms.
