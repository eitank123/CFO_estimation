# Full-system competitors: predictions and measurements (started 2026-11-17)

Goal: prove the whole blind system (no pilots, blind CFO/phase, polar CA-SCL-8 + CRC-32) beats the REAL deployed
systems: their FEC, frame, pilots, synchroniser, decoder and error check, implemented as accurately as possible.
Axis: Eb/N0 per payload bit (k = info bits - 32 CRC bits), every known symbol and parity bit charged.
Channel: CFO +-0.03, AWGN, timing known. Equal payload: blind carries the same k + CRC-32 (user, 2026-11-17).
Scope (user, 2026-11-17): no timing / burst synchronisation for anyone; the competitors' known symbols are used for
CFO (and decode phase) estimation only. Their unique words also serve timing in the real systems: the result holds
"given timing". Planned extra runs: each system also at its realistic CFO range (DVB-RCS2 also at +-0.005, the low end of
its design range: TR 101 545-4 6.2.2 says gateways accept burst CFO of 0.5 % .. 3 % of the symbol rate, so +-0.03 is
the TOP of DVB-RCS2's own design range (corrected 2026-11-17; an earlier note wrongly said +-0.002); VDE residual Doppler), BLER vs MACs at several list sizes / iteration
counts, and blind thresholds calibrated on seeds disjoint from the test seeds.
Reporting (user, 2026-11-17): every curve on BOTH axes: (a) Eb/N0 per payload bit with all known symbols charged,
(b) the same without the known-symbol energy (Es/N0 per data symbol, i.e. the pilots free). Realistic-CFO runs
queued after the +-0.03 ones: fs-darn3/13/14/42 (DVB-RCS2 at +-0.005). Blind thresholds re-tuned per format on
calibration seeds (seed + 1e6). A modern wide-CFO system closest to ours is being researched
(lit_widecfo_competitor.md).
Specs: [lit_rcs2_fullsystem.md](lit_rcs2_fullsystem.md), [lit_turbo_db.md](lit_turbo_db.md),
[lit_vdesat_fullsystem.md](lit_vdesat_fullsystem.md), [lit_vde_fec.md](lit_vde_fec.md),
[lit_polar_ratematch.md](lit_polar_ratematch.md). Code: `fullsys/`. Published targets:
[plots/DVB-RCS2/BLER/fullsys_refs.png](plots/DVB-RCS2/BLER/fullsys_refs.png).

Sign convention for every gap: **+ = blind better** (needs less Eb/N0).

Axis conversions used below (Es/N0 per transmitted symbol):

| Format | k | RCS2 burst symbols | RCS2 Eb/N0 = Es/N0 + | Blind symbols (data only) | Blind Eb/N0 = Es/N0 + |
|---|---|---|---|---|---|
| ID 3 (QPSK 1/3) | 272 | 536 | 2.95 dB | 456 | 2.24 dB |
| ID 13 (QPSK 1/3) | 952 | 1616 | 2.30 dB | 1476 | 1.90 dB |
| ID 14 (QPSK 1/2) | 1472 | 1616 | 0.41 dB | 1504 | 0.09 dB |
| ID 42 (pi/2-BPSK 1/3) | 952 | 3236 | 5.31 dB | 2952 (BPSK) / 1476 (QPSK) | 4.92 / 1.90 dB |

The symbol overhead alone is worth 0.70 / 0.39 / 0.31 / 0.40 dB to blind at ID 3 / 13 / 14 / 42.

## Step 1: validation of our competitor implementations (ideal sync)

### 1a. DVB-RCS2 vs TR 101 545-4 (jobs fs-rcs2v3 / v13 / v14 / v42) and AFF3CT (fs-rcs2a3008 / a4512 / va)
Decoder: max-log-MAP, ADAPTIVE scaling (0.5 then 0.85), 8 iterations; TR runs also at sf 0.7 (fs-rcs2vb).
Pass = within +-0.2 dB of the reference at PER 1e-3 and 1e-5. AFF3CT runs are the same code and decoder as AFF3CT,
so they must match within +-0.1 dB (only our RRC chain and float64 differ).

| Run | Reference Es/N0 @1e-3 / @1e-5 | Predicted ours | Verdict rule |
|---|---|---|---|
| ID 3 | -0.27 / 0.22 | -0.27 / 0.22 (+-0.15) | miss > 0.2 dB: fix before step 3 |
| ID 13 | -0.80 / -0.51 | -0.80 / -0.51 (+-0.15) | same |
| ID 14 | 1.49 / 1.71 | 1.48 / 1.72 (+-0.1) | same |
| ID 42 | -3.81 / -3.52 | -3.81 / -3.52 (+-0.15) | same |
| AFF3CT N3008 (ID 14 code) | FER 1.22e-2 at Es/N0 1.31, 5.9e-4 at 1.51 | same +-0.05 dB | must match: same code and decoder |
| AFF3CT N4512 (rate 1/3) | 6.5e-3 at -1.05, 2.4e-4 at -0.85 | same +-0.05 dB | must match |
| Interleaver reading 'en' / 'en-natswap' vs 'aff3ct' (fs-rcs2vb) | - | within +-0.05 dB of each other | if one is > 0.1 dB worse, use the best (strongest competitor) |
| log-MAP vs max-log ADAPTIVE | - | log-MAP 0.05-0.15 dB better | strongest variant goes into step 3 |
| sf 0.7 vs ADAPTIVE | - | within 0.05 dB | |

### 1b. VDE-SAT vs ITU-R M.2435 Fig. 11 (88 info bits, QPSK, turbo 1/4) and Kim 2025 (fs-vdev88 / fs-vdev32)
| Run | Reference | Predicted ours |
|---|---|---|
| 88 bits QPSK 1/4 (DVB-SH interleaver option) | PER 1e-2 at Es/N0 -1.5 dB, 1e-3 at -0.8 | -1.5 / -0.8 (+-0.2) |
| 88 bits with the M.2092-2 CCSDS-law interleaver | (no reference) | within 0.1 dB of the above |
| Link 32 (312 bits incl. CRC-32, BPSK SF 8, turbo 1/4) | design point Es/N0 -4.5 dB (per chip-rate convention of lit_vdesat_fullsystem.md) | PER 1e-2 at about -4.6 +- 0.3 |

### 1c. Rate-matching smoke (fs-rmsmoke): ID 14 shorten, shortened LLR +BIG / 0 / -BIG on the same packets
Predicted: BLER(+BIG) < BLER(0) << BLER(-BIG) = ~1; +BIG vs 0 differ by 0.2-0.4 dB-equivalent (McNemar p < 0.01 at
the 1.0 dB point). Any other order = a rate-recovery bug.

## Step 2: code-only gain, genie sync on both (fs-pg13 / pg14 / pg3 / pg42 / pgvde vs the step-1 runs)
Polar CA-SCL-8 + CRC-32, NR-style rate matching (N <= 4096), vs DVB-RCS2 turbo (16-state duo-binary, 8 it.).
Same (K, E), same QPSK map, paired seeds where the chain allows. Literature: polar L = 8 within +-0.5 dB of turbo at
K = 300-1500; the 16-state duo-binary code is ~0.3 dB stronger than the LTE turbo most polar papers beat; CRC-32 in
the list costs the polar side ~0.1-0.2 dB vs CRC-16 at L = 8 (more false-path protection, fewer list hits).

Es/N0 at BLER 1e-3 (1e-5 in brackets); gap = turbo - polar (+ = polar better):

| Format | Turbo (TR, ideal) | Polar genie predicted | Gap predicted | Verdict expected |
|---|---|---|---|---|
| ID 3: K 304, E 912, N 1024 punct. | -0.27 (0.22) | -0.30 (0.10) | +0.03 (+0.12) | tie; polar steeper, wins at 1e-5 |
| ID 13: K 984, E 2952, N 4096 punct. | -0.80 (-0.51) | -0.60 (-0.40) | -0.20 (-0.11) | turbo better by 0.1-0.2 |
| ID 14 shorten: K 1504, E 3008, N 4096 | 1.49 (1.71) | 1.62 (1.80) | -0.13 (-0.09) | turbo better by ~0.1 |
| ID 14 forced puncture | 1.49 (1.71) | 1.80 (1.98) | -0.31 (-0.27) | worse than shorten by ~0.2 |
| ID 42 pi/2-BPSK | -3.81 (-3.52) | -3.61 (-3.41) | -0.20 (-0.11) | as ID 13 (BPSK = QPSK per bit) |
| ID 42 code on QPSK | - | -0.60 (-0.40) on 1476 QPSK symbols | - | same Eb/N0 as BPSK |

So the code alone is predicted to lose 0.1-0.2 dB at K >= 1000 and tie at K = 304: the system win must come from
the symbol overhead and synchronisation.

## Step 3 (phase 1): full systems with real sync, native formats, CFO +-0.03
- DVB-RCS2 receiver: DA CFO + phase from its UW / pilots (the standard leaves the estimator open; we use the best
  published DA ML estimator with a search wide enough for +-0.03, then turbo with the true-SNR LLRs). Predicted
  synchronisation loss vs ideal: 0.15-0.4 dB, largest at ID 3 (80 known symbols) and ID 42 (low Es/N0 per symbol),
  with a CFO-outlier floor possible at |f| > 0.025 (its single-symbol pilot spacing aliases, seen in est4).
- Blind: the adopted receiver, rate-matched; predicted sync loss vs genie 0.1 dB (IDs 13, 14, 42: >= 1476 symbols)
  and 0.25 dB at ID 3 (456 symbols). ID 14 shorten: 4 phase hypotheses (no PiCode), +~0.02 dB from extra false paths.

Eb/N0 per payload bit at PER 1e-3 (1e-5 in brackets):

| Format | RCS2 ideal sync (TR) | RCS2 real DA sync, predicted | Blind predicted | Gap vs RCS2 real (+ = blind better) | Gap vs RCS2 ideal | Verdict expected |
|---|---|---|---|---|---|---|
| ID 3 | 2.68 (3.17) | 3.0-3.1 (3.5) | 2.19 (2.59) | +0.85 (+0.9) | +0.49 | blind clearly better |
| ID 13 | 1.50 (1.79) | 1.75 (2.05) | 1.40 (1.60) | +0.35 (+0.45) | +0.10 | blind better |
| ID 14 (shorten) | 1.90 (2.12) | 2.05 (2.27) | 1.81 (1.99) | +0.24 (+0.28) | +0.09 | blind better |
| ID 14 (puncture) | 1.90 (2.12) | 2.05 (2.27) | 1.99 (2.17) | +0.06 (+0.10) | -0.09 | tie |
| ID 42 pi/2-BPSK | 1.50 (1.79) | 1.80 (2.10) | 1.41 (1.61) | +0.39 (+0.49) | +0.09 | blind better |
| ID 42 code, blind on QPSK | 1.50 (1.79) | 1.80 (2.10) | 1.40 (1.60) | +0.40 (+0.50) | +0.10 | blind better |

VDE-SAT Link 32 (payload 280 + CRC-32, rate 1/4, 1641 symbols of which 372 known, BPSK x8 spreading; blind: polar
K 312, E 1269 BPSK symbols, no spreading). Eb/N0 per payload bit at PER 1e-2 (VDE's design target; 1e-3 in brackets):

| System | Eb/N0 @1e-2 (1e-3) | Gap (+ = blind better) |
|---|---|---|
| VDE design point (M.2092-2, Es/N0 -4.5) | 3.18 | - |
| VDE ideal sync, our implementation (predicted) | 2.6 (3.1) | - |
| VDE real DA sync (predicted, syncwords + 180 pilots, +0.2 dB) | 2.8 (3.3) | - |
| Blind (predicted: genie 2.0 (2.4), + 0.25 sync) | 2.25 (2.65) | **+0.55 (+0.65) vs VDE real; +0.9 vs the design point** |

Blind runs at Es/N0 = Eb/N0 - 6.56 dB = -4.3 dB per BPSK symbol at 1e-2 (inside our -5 dB limit).

Uncertainty: +-0.15 dB on each blind number (rate matching at N = 4096 and the early-stop retune are new).

MACs (predicted; turbo counted with the same op rules, per-core by window-parallel decoding over 32 cores):

| Format | RCS2 decode ops (8 it., max-log) | RCS2 + DA sync, per core | Blind per core (grid + decodes + check) | Ratio blind / RCS2 |
|---|---|---|---|---|
| ID 3 | 1.00 M | ~0.04 M | ~0.10 M | ~2.5x |
| ID 13 | 3.24 M | ~0.11 M | ~0.30 M | ~2.7x |
| ID 14 | 4.95 M | ~0.16 M | ~0.35 M (4 phases) | ~2.2x |
| ID 42 | 3.24 M | ~0.12 M | ~0.40 M (2952 symbols in the grid) | ~3.3x |

The turbo decoder is 8-12x costlier per packet than one polar decode, so the cost gap shrinks from 3-7x (est4, polar
on both sides) to ~2-3x. With early stop on the turbo side (CRC, from iteration 2) its cost drops ~40 % near the
1e-3 point: ratio ~3.5-4x then.

## Step 4 (phase 2): lower SNR / our rates (1/10, 0.15)
Not predicted yet: DVB-RCS2 has no native rate below 1/3 (spread-spectrum only); written after phase 1.

## Measured (partial, 2026-11-17 ~13:00)
Validation (step 1), all PASS:
- RCS2 ID 13 ideal: PER 1e-3 at Es/N0 ~-0.77 (TR -0.80); 6.3e-5 at -0.60.
- RCS2 ID 14 ideal: 1.22e-3 at 1.49 (TR 1e-3 at 1.49): within 0.02 dB.
- AFF3CT N3008 (ID 14 code): ours ~0.03 dB right of AFF3CT's curve at every point (9.1e-4 vs 5.9e-4 at Eb/N0 1.6).
- VDE 88-bit (M.2435 Fig. 11): 9.5e-3 at -1.5, 1.45e-3 at -1.0, 1.9e-4 at -0.5, 2.7e-5 at 0.0: 0.05-0.1 dB better
  than the figure.
Step 2, code only (genie both), ID 14: polar CA-SCL-8, CRC-32, PW construction, shortened N 4096: BLER 1e-3 at
Es/N0 ~1.97, 1e-5 at ~2.37 (5.3e-5 at 2.2, 7e-6 at 2.4); punctured is worse (2.9e-2 at 1.8 vs 4.2e-3 shortened).
Turbo 1.51 / ~1.72. **Code gap -0.46 dB at 1e-3, -0.66 at 1e-5 (predicted -0.13 / -0.09: MISSED).** On the system
axis (Eb/N0 per payload bit, known symbols charged) blind with genie sync is 2.06 vs RCS2 ideal 1.92 at 1e-3
(**-0.14**) and 2.46 vs 2.12 at 1e-5 (**-0.34**): the 0.31 dB overhead saving does not cover the code gap.
Suspected cause: PW construction ignores the rate matching (shortened bits are known); a GA construction over the
rate-matched channel and L = 16/32 are being added (fs-pgga, fs-pgl32).

## Measured, ID 13 (2026-11-17 ~13:10), Eb/N0 per payload bit, known symbols charged (+ = polar better than RCS2 DA)
| BLER | RCS2 ideal | RCS2 own DA CFO (+-0.03) | polar PW L8 | polar PW L16 | polar GA L8 | polar GA L16 |
|---|---|---|---|---|---|---|
| 1e-2 | 1.35 | 1.43 | 1.54 (-0.11) | 1.43 (0.00) | 1.19 (+0.24) | 1.04 (+0.39) |
| 1e-3 | 1.53 | 1.62 | ~1.91 (-0.29) | ~1.75 (-0.13) | 1.49 (+0.13) | 1.34 (+0.28) |
| 1e-4 | 1.67 | 1.76 | - | - | 1.77 (-0.01) | 1.59 (+0.17) |
Polar curves are genie sync (code only). GA construction (rate-matching-aware) gains 0.35-0.4 dB over PW: the PW
construction was the handicap. Pilots free: GA L16 still beats RCS2 ideal at 1e-2 (1.04 vs 0.96 +.. see plot) only
with pilots charged; code-vs-code (pilots free) GA L16 is -0.07 (1e-2) / -0.21 (1e-3) vs RCS2 ideal.
Blind (PW, provisional): PER floor ~0.37 at -1.2 and -0.2 dB: a bug, under investigation; cost 26.8 M/core at -1.2 dB
was the failing packets exhausting the post rescue.

## Predictions: blind ID 13 after the interleaver fix (written 2026-11-17 13:40, before the runs)
Setup: blind adopted 2/5 receiver + format hooks, rate-matched polar N 4096 -> E 2952, GA construction, CA-SCL-8,
CRC-32, random channel interleaver over E (fix), CFO U(+-0.03), timing known, early stops off (provisional), per-core
cap 5 M (if the cap smoke passes). Reference = genie GA L8 on the same code (fs-pgga-13); blind's sync loss assumed
~0.1 dB (as at the native 2/5 format).

| Es/N0 | genie GA L8 (measured) | blind predicted | 
|---|---|---|
| -0.8 | 1.80e-2 | 2.5e-2 |
| -0.6 | 4.31e-3 | 7e-3 |
| -0.4 | 8.80e-4 | 1.5e-3 |
| -0.2 | 1.87e-4 | 3.5e-4 |
| 0.0 | 2.67e-5 | 6e-5 |

Eb/N0 per payload bit at BLER 1e-3 (known symbols charged): blind predicted **1.59 dB** vs RCS2 with its own CFO
estimate 1.62 (**+0.03, tie**) and RCS2 ideal 1.53 (-0.06). At 1e-2: blind ~1.29 vs 1.43 (**+0.14**).
With list 16 (next): blind ~1.44 at 1e-3 (**+0.18** vs RCS2 DA).
MACs per core (mean): 0.5-2 M at -0.4 ... 0 dB (fast path dominant), 3-6 M at -0.8; RCS2 0.175 M (8 it.) /
~0.07-0.1 M (CRC early stop): blind ~5-20x more. Wrong-branch decodes vanish, so the cost per right packet drops
roughly 2x from the broken smoke (median 3.5 M).
Cap smoke (fs-b13cap, 300 paired packets at -0.6 and -0.2): predicted 0 packets lost by the 5 M cap at -0.2,
0-2 at -0.6 (if > 0 the cap is not adopted as is).

## Measured: BLIND vs DVB-RCS2, ID 13 (2026-11-17 ~14:00) — plot testing/results/plots/DVB-RCS2/superseded/fs_id13_blind.png
Blind = fixed receiver (channel interleaver, GA CA-SCL-8, CRC-32, CFO +-0.03, early stops off). No-cap errors =
err - right-before-cap (the 5 M cap was applied after the receive, so this is exact).
| Es/N0 | Eb/N0 (blind axis) | blind errors / packets | blind BLER | blind MACs/core (mean) |
|---|---|---|---|---|
| -0.8 | 1.10 | 16 / 2800 | 5.7e-3 | 0.80 M (calib, no cap) |
| -0.6 | 1.30 | 14 / 17000 | 8.2e-4 | 0.58 M (calib) |
| -0.4 | 1.50 | 7 / 20000 | 3.5e-4 | 0.48 M (calib) |
| -0.2 | 1.70 | 1 / 20000 | 5e-5 | 0.39 M |
| 0.0 | 1.90 | 0 / 20000 | < 5e-5 | 0.34 M |
Eb/N0 per payload bit, known symbols charged, at BLER 1e-3: **blind 1.28** vs RCS2 own DA 1.62 (**+0.34 dB**), vs RCS2
ideal 1.53 (+0.25). At 1e-4: blind ~1.63 (7 and 1 errors: wide CI) vs 1.76 (+0.13). Predicted +0.03 at 1e-3: blind
did better than predicted because it also beats its own genie L8 curve (the search's extra decodes act like extra
list paths). MACs per core: blind 0.39-0.80 M vs RCS2 0.175 M (8 it.): 2.2-4.6x (early stops not yet tuned).
Pilots free (code vs code): blind is about equal to RCS2 own-DA at 1e-2..1e-3 and worse below (turbo steeper).
