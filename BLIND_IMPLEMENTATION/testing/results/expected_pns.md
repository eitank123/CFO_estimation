# Blind phase tracking: code-aided phase-smoothing retry (`pns`) + phase-noise-tolerant re-encoding check (`rhos`)
Predictions 2026-11-15, before any code. Source: lit_polar_sync.md F1, F2 (Colavolpe-Barbieri-Caire 2005 Tikhonov
smoother; soft-decision-directed Kalman smoothers; Sauter et al. 2025). Reopens `dd` (DEAD_ENDS) for a NEW reason: a
time-varying phase that the constant-phase CFO grid cannot represent (in AWGN dd had nothing to fix).

## Method
- pns: after a CRC / rho failure of a CA-SCL-8 decode at a candidate (never on a passed decode), take the list's
  re-encoded QPSK symbols, list-weighted (weights exp(-PM_l), normalised), z_k = y_k conj(xbar_k); smooth the phase of z
  with a Kalman / RTS smoother (random walk, q = 2 pi linewidth x Ts, a receiver parameter `pn_q`; measurement variance
  from the SNR and |xbar_k|), de-rotate y by the smoothed phase, decode once more (1 iteration; 2 as a variant).
- rhos: the re-encoding correlation summed per segment of S symbols with a per-segment phase,
  rho_s = sum_seg |sum_k in seg y_k conj(c_k)| / norm, with its own threshold calibrated to the same false-accept level
  as rho on noise-only and wrong-CRC-pass data (S = 64 default). Measured first offline on existing dumps if possible.

## Predictions (64k paired, BLIND_PN = linewidth x Ts; the pn1-pn3 points; receivers: testing_s11g / base25_qfix / base2_qfix)
Residual phase rms now (line fit) 0.21 rad at 1e-4, 0.36 rad at 3e-4 (lit_polar_sync.md [derived]).
| Point | 1e-4: BLER now -> with pns | 3e-4: now -> with pns | per core |
|---|---|---|---|
| 2/5 0.5 dB | 8.3e-2 -> 5e-3 ... 2e-2 (x4-15 better) | 0.54 -> 0.1 ... 0.3 | +5 ... +30 % at 1e-4 (one extra decode per failing packet), less than now at 3e-4 |
| 1/10 -5 dB | 6.6e-4 -> 2.5e-4 ... 4.5e-4 | 2.7e-2 -> 3e-3 ... 1e-2 | +2 ... +10 % |
| 0.15 -3.5 dB | 2.25e-3 -> 8e-4 ... 1.5e-3 | 6.2e-2 -> 1e-2 ... 3e-2 | +2 ... +10 % |
| 1/2 2 dB | (not measured with pn yet) x? -> close to no-pn | - | - |
- AWGN (pn 0) at 2/5 0.5 dB and 0.15 -4 dB: BLER unchanged (0 ... 2 discordant), per core +0 ... +3 % (retry only on
  failing packets; fixes 0 in AWGN as dd did).
- rhos: at pn 1e-4 / 3e-4 recovers right decodes that rho rejects (rho drops 4 % / 12 %): BLER -5 ... -20 % on its own;
  in AWGN identical decisions within +-1 packet; undetected <= base + 1.
- Kill: AWGN BLER loss (paired p < 0.05) or undetected > base + 2 at any point.

## Code review (2026-11-15): GO with fixes
Flags off: bit-identical (safe for the queued eqrb jobs). Verified: xbar from one path = the sent symbols; smoother
0.60 -> 0.20 rad (3e-4, -3.5 dB, known symbols); rho_seg = 1 (noiseless right) and = rho at S = N; undetected risk of
rho="corr" low (an unrelated codeword barely moves the smoother). Fixes being applied: per-packet max_calls (the post
rescue could give 9 calls and overwrite an accepted packet), _truth on the pre-pns snapshot, counter pns_calls_incell.
Reading rules: use crit_par / d4a (not d4b) for pns MACs; se_coarse differs between arms (ignore); the smoother is
told the true linewidth (mismatch untested: a later arm). Cap: 2 pns calls per packet (run.py PNS).

## Smoke (pns-smoke, pn 1e-4, 400 packets per arm; 2026-11-15)
- Part a, 2/5 0 dB: base 148 errors -> pns 135 (13 fixed, 0 broken), undetected 0 / 0, per core -9.8 %, total -10.3 %
  (fixed packets stop searching). pns calls 567 (cap 2 per packet), fixes 28 of them, 0 wrong fixes, 0 wrong CRC passes.
  Only 12 of the 567 calls were "in-cell" (|f - f_true| <= 0.5 STEP and the right phase branch): under phase noise the
  best candidate is usually a neighbouring cell, and pns still fixes it. _rhosl arms identical to their base: OK.
- Part b, 0.15 -4 dB: CRASH (IndexError in decode: the pns settings variable P_ was shadowed by an array of the same
  name in the 4-phase search, used only at 0.15). Renamed to PNSC (pns path only; the flags-off path never reads it).
  Rerun as pns-smoke2 (part t-pns-smoke2-b).
- Smoke 2 (pns-smoke2, 0.15 -4 dB, pn 1e-4, 400 packets): EVAL DONE + ALL DONE, no Traceback. base 5 -> pns 4 errors (1
  fixed, 0 broken), undetected 0 / 0, per core -13.9 %, total -14.0 %; 8 fixes, 0 wrong; _rhosl identical. PASS ->
  full runs pns0, pns1a-e, pns3a-f submitted (queued as slots free).

## Measured: pns1a-e, pns0a (64k paired, same packets; 2026-11-15; EVAL DONE + ALL DONE, no Traceback)
| Point | pn | errors base -> pns (fixed / broken) | undetected | per core | pns calls / CRC-pass fixes / wrong |
|---|---|---|---|---|---|
| 1/10 -5 dB | 1e-4 | 35 -> 33 (2 / 0) | 0 / 0 | -1.0 % | 3211 / 134 / 0 |
| 0.15 -3.5 dB | 1e-4 | 172 -> 155 (17 / 0, p < 1e-3) | 0 / 0 | -4.6 % | 4128 / 251 / 0 |
| 2/5 0.5 dB | 1e-4 | 5358 -> 4400 (958 / 0) | 3 / 2 | -13.3 % | 59849 / 2624 / 0 |
| 1/2 2 dB | 1e-4 | 3788 -> 2933 (855 / 0) | 1 / 1 | -13.5 % | 30873 / 2060 / 0 |
| 0.15 -4 dB | 0 (AWGN) | 247 -> 241 (6 / 0, p = 0.03) | 0 / 0 | -2.4 % | 5493 / 262 / 0 |
- Never breaks a packet (0 broken in 1200+ discordant pairs), never a wrong fix; MACs per core go DOWN everywhere (fixed
  packets stop searching). AWGN: no loss, a small gain (kill gate passed).
- Size of the gain vs predictions: MISS. 2/5 1e-4 BLER 8.4e-2 -> 6.9e-2 (-18 %, predicted x4-15); 1/2 -23 %; 0.15 -10 %
  (predicted x1.5-3); 1/10 within noise. One smoothing pass from a FAILED decode's list symbols fixes ~4-7 % of the calls.
  The DVB-RCS2 tracking pilot receiver stays better under 1e-4 at 2/5 (1967 vs ~4400 per 64k, per-symbol SNR).
- rhos log-only arms identical to base.

## Measured: pns3a-f (pn 3e-4) and pns0b (AWGN 2/5); EVAL DONE + ALL DONE, no Traceback (2026-11-15)
| Point | pn | errors base -> pns (fixed / broken) | undetected | per core |
|---|---|---|---|---|
| 1/10 -5 dB (64k) | 3e-4 | 1627 -> 1266 (361 / 0) | 0 / 0 | -16.8 % |
| 0.15 -3.5 dB (64k) | 3e-4 | 3943 -> 3210 (733 / 0) | 5 / 3 | -18.4 % |
| 2/5 0.5 dB (16k) | 3e-4 | 8744 -> 7966 (778 / 0) | 5 / 4 | -8.6 % |
| 1/2 2 dB (16k) | 3e-4 | 8599 -> 7802 (797 / 0) | 3 / 2 | -7.5 % |
| 2/5 0.5 dB (64k) | 0 (AWGN) | 140 -> 136 (4 / 0) | 2 / 1 | +7.1 % |
- 3e-4: BLER -9 ... -22 % (predicted x2.5-9 lower): MISS. Still 0 broken, MACs down. 2/5, 1/2 stay at BLER ~0.5.
- AWGN 2/5: no loss (kill gate passed); +7 % per core (predicted +0 ... +3 %): the retry costs a decode on every
  failing packet and fixes few there.
- Verdict: pns is a safe, small win (keep as a candidate: never worse in BLER, cheaper under phase noise, +7 % per core
  in AWGN at 2/5). It does not close the gap to the DVB-RCS2 tracking receiver. Limit: one smoothing pass from a FAILED
  decode's list symbols (decision errors corrupt the phase reference); more passes (iters 2-3, more calls per packet) or
  a soft per-segment phase search before decoding are the next candidates.
