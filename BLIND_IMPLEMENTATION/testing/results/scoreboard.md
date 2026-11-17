# Blind vs every compared receiver: scoreboard (2026-11-17)

Generated from existing results only (est4 / est5 / ARS / variant parts via `plot_e4.e4(rate, e5, ars, var)`, blind = the
adopted testing receiver via `plot_e4.blind`; same interpolation as `plot_e4.gap_db`). Regenerated as jobs land.
Fair axis: SNR (Es/N0) [dB] = burst energy per data symbol, pilot energy charged. Gap = receiver - blind (+ = blind
needs less SNR). MACs per core = scheduled count at the crossing; 'blind / it' < 1 means blind is cheaper. 'fails' =
never reaches the target in the simulated range (>= -5 dB); 'below at lowest point' = already under the target at the
lowest simulated point (crossing not bracketed). Blind and the competitors are not packet-paired: gaps under ~0.1 dB
are ties. Phase-tracking ('track') and 'interp' duplicates are left out (same numbers at pn = 0). Receiver layouts and
sources: competitors.md (est5) and expected_variants.md (faithful variants). Jobs still running at generation:
DVB-S2 SOF26 (all rates), DVB-S2 header90 at 1/2 and the 1/10 -5.3 dB point (v-10hla/hlb).

## R = 1/10, BLER 1e-04: blind -4.78 dB, 0.194 M MACs per core

| # | Receiver | Required SNR [dB] | Gap to blind [dB] | MACs per core [M] | blind / it MACs |
|---|---|---|---|---|---|
| 1 | 128-symbol preamble, ML | -4.68 | +0.10 | 0.090 | 2.2x |
| 2 | CCSDS-inspired (8 x 16 blocks) | -4.65 | +0.13 | 0.065 | 3.0x |
| 3 | 5G-NR-like DMRS, 1 in 7 | -4.58 | +0.20 | 0.034 | 5.7x |
| 4 | MIL-STD-188-110 HF (current layout) | -4.10 | +0.68 | 0.034 | 5.7x |
| 5 | DVB-RCS2 ID 13 + lobe search | -4.10 | +0.68 | 0.034 | 5.7x |
| 6 | DVB-RCS2 ID 13 (116 known, Rife-Boorstyn) | -4.09 | +0.69 | 0.034 | 5.7x |
| 7 | Griebel 2021 FFT 4096 | -3.97 | +0.81 | 0.030 | 6.5x |
| 8 | CCSDS 131.0 ASM (64, +-12 lobes) | -3.89 | +0.89 | 0.167 | 1.2x |
| 9 | CCSDS-inspired, per-block phase | -3.38 | +1.41 | 0.065 | 3.0x |
| 10 | Wi-Fi-like 128-symbol preamble | -3.10 | +1.68 | 0.323 | 0.6x |
| 11 | 128-symbol preamble, Mengali-Morelli | -3.03 | +1.75 | 0.065 | 3.0x |
| 12 | 64 + 64 pre/post, joint ML (+-3 lobes) | -2.83 | +1.95 | 0.065 | 3.0x |
| 13 | Wi-Fi 802.11 real 320 + lobes | -2.46 | +2.32 | 0.343 | 0.6x |
| 14 | DVB-S2-inspired (header + pilot block, 126) | -2.32 | +2.46 | 0.041 | 4.7x |
| 15 | CCSDS 131.2 real pilot density (32) | -2.32 | +2.46 | 0.343 | 0.6x |
| 16 | Griebel 2021 FFT 2048 | -1.15 | +3.63 | 0.028 | 6.9x |
| 17 | Griebel 2021 FFT 2048 N | -1.15 | +3.63 | 0.028 | 6.9x |
| 18 | Griebel 2021 as published | -1.08 | +3.70 | 0.028 | 6.9x |
| 19 | DVB-RCS2 16 + 16 pre/post, 4th power | fails (min BLER 5.1e-01) | - | - | - |
| 20 | Sparse pilots, 1 in 32 | fails (min BLER 9.5e-02) | - | - | - |
| 21 | VDE-SAT (ITU-R M.2092, 66 known) | fails (min BLER 1.0e-04) | - | - | - |
| 22 | ViaSat burst (16-symbol UW) | fails (min BLER 8.3e-01) | - | - | - |
| 23 | Advantech hybrid DA + NDA | fails (min BLER 3.2e-01) | - | - | - |
| 24 | ViaSat US 7653150 (single peak) | fails (min BLER 9.1e-01) | - | - | - |
| 25 | ViaSat top-32 + 4th-power phase | fails (min BLER 8.3e-01) | - | - | - |
| 26 | Advantech 48 preamble | fails (min BLER 4.2e-01) | - | - | - |
| 27 | Advantech 48 preamble, wide DA window | fails (min BLER 2.3e-04) | - | - | - |
| 28 | MIL-STD-188-110, full 411 known | below target at lowest point -3.53 (BLER 1.9e-05) | - | - | - |
| 29 | 64 + 64 pre/post, joint ML (+-4 lobes) | below target at lowest point -4.49 (BLER 8.1e-05) | - | - | - |
| 30 | DVB-S2 PL header only (90, CFO scan) | below target at lowest point -4.63 (BLER 3.1e-05) | - | - | - |
| 31 | Wi-Fi 802.11 real 320 (STF + LTF) | fails (min BLER 1.9e-03) | - | - | - |

## R = 0.15, BLER 1e-03: blind -3.60 dB, 0.262 M MACs per core

| # | Receiver | Required SNR [dB] | Gap to blind [dB] | MACs per core [M] | blind / it MACs |
|---|---|---|---|---|---|
| 1 | Advantech 48 preamble, wide DA window | -3.63 | -0.03 | 0.363 | 0.7x |
| 2 | DVB-S2 PL header only (90, CFO scan) | -3.57 | +0.03 | 0.774 | 0.3x |
| 3 | DVB-RCS2 ID 13 (116 known, Rife-Boorstyn) | -3.45 | +0.15 | 0.035 | 7.5x |
| 4 | Griebel 2021 FFT 4096 | -3.45 | +0.16 | 0.031 | 8.5x |
| 5 | DVB-RCS2 ID 13 + lobe search | -3.45 | +0.15 | 0.035 | 7.5x |
| 6 | 128-symbol preamble, ML | -3.44 | +0.16 | 0.078 | 3.4x |
| 7 | CCSDS 131.0 ASM (64, +-12 lobes) | -3.44 | +0.16 | 0.172 | 1.5x |
| 8 | 64 + 64 pre/post, joint ML (+-4 lobes) | -3.41 | +0.19 | 0.074 | 3.5x |
| 9 | 128-symbol preamble, Mengali-Morelli | -3.40 | +0.20 | 0.079 | 3.3x |
| 10 | CCSDS-inspired (8 x 16 blocks) | -3.40 | +0.20 | 0.060 | 4.4x |
| 11 | Wi-Fi-like 128-symbol preamble | -3.39 | +0.21 | 0.435 | 0.6x |
| 12 | 64 + 64 pre/post, joint ML (+-3 lobes) | -3.34 | +0.26 | 0.071 | 3.7x |
| 13 | 5G-NR-like DMRS, 1 in 7 | -3.27 | +0.33 | 0.035 | 7.5x |
| 14 | DVB-S2-inspired (header + pilot block, 126) | -3.11 | +0.49 | 0.048 | 5.5x |
| 15 | VDE-SAT (ITU-R M.2092, 66 known) | -2.92 | +0.68 | 0.035 | 7.5x |
| 16 | CCSDS-inspired, per-block phase | -2.90 | +0.70 | 0.067 | 3.9x |
| 17 | Griebel 2021 FFT 2048 | -2.88 | +0.72 | 0.029 | 9.0x |
| 18 | Griebel 2021 FFT 2048 N | -2.88 | +0.72 | 0.029 | 9.0x |
| 19 | MIL-STD-188-110 HF (current layout) | -2.82 | +0.78 | 0.036 | 7.3x |
| 20 | CCSDS 131.2 real pilot density (32) | -2.73 | +0.87 | 0.387 | 0.7x |
| 21 | Griebel 2021 as published | -2.72 | +0.88 | 0.029 | 9.0x |
| 22 | Wi-Fi 802.11 real 320 + lobes | -2.72 | +0.88 | 0.442 | 0.6x |
| 23 | MIL-STD-188-110, full 411 known | -2.51 | +1.09 | 0.036 | 7.3x |
| 24 | Wi-Fi 802.11 real 320 (STF + LTF) | -0.05 | +3.55 | 0.080 | 3.3x |
| 25 | DVB-RCS2 16 + 16 pre/post, 4th power | fails (min BLER 1.9e-01) | - | - | - |
| 26 | Sparse pilots, 1 in 32 | fails (min BLER 8.3e-02) | - | - | - |
| 27 | ViaSat burst (16-symbol UW) | fails (min BLER 7.0e-01) | - | - | - |
| 28 | Advantech hybrid DA + NDA | fails (min BLER 2.0e-01) | - | - | - |
| 29 | ViaSat US 7653150 (single peak) | fails (min BLER 8.2e-01) | - | - | - |
| 30 | ViaSat top-32 + 4th-power phase | fails (min BLER 7.1e-01) | - | - | - |
| 31 | Advantech 48 preamble | fails (min BLER 3.4e-01) | - | - | - |

## R = 0.15, BLER 1e-04: blind -2.93 dB, 0.180 M MACs per core

| # | Receiver | Required SNR [dB] | Gap to blind [dB] | MACs per core [M] | blind / it MACs |
|---|---|---|---|---|---|
| 1 | DVB-S2 PL header only (90, CFO scan) | -3.23 | -0.31 | 0.690 | 0.3x |
| 2 | DVB-RCS2 ID 13 (116 known, Rife-Boorstyn) | -3.12 | -0.19 | 0.035 | 5.1x |
| 3 | 128-symbol preamble, ML | -3.12 | -0.20 | 0.076 | 2.4x |
| 4 | DVB-RCS2 ID 13 + lobe search | -3.12 | -0.20 | 0.035 | 5.1x |
| 5 | Griebel 2021 FFT 4096 | -3.11 | -0.18 | 0.031 | 5.8x |
| 6 | 64 + 64 pre/post, joint ML (+-4 lobes) | -3.09 | -0.17 | 0.071 | 2.5x |
| 7 | CCSDS-inspired (8 x 16 blocks) | -3.06 | -0.14 | 0.058 | 3.1x |
| 8 | 128-symbol preamble, Mengali-Morelli | -3.00 | -0.07 | 0.075 | 2.4x |
| 9 | CCSDS 131.0 ASM (64, +-12 lobes) | -2.98 | -0.05 | 0.167 | 1.1x |
| 10 | 5G-NR-like DMRS, 1 in 7 | -2.92 | +0.01 | 0.035 | 5.1x |
| 11 | Wi-Fi-like 128-symbol preamble | -2.86 | +0.07 | 0.341 | 0.5x |
| 12 | 64 + 64 pre/post, joint ML (+-3 lobes) | -2.72 | +0.20 | 0.068 | 2.6x |
| 13 | MIL-STD-188-110 HF (current layout) | -2.47 | +0.45 | 0.035 | 5.1x |
| 14 | CCSDS-inspired, per-block phase | -2.44 | +0.49 | 0.064 | 2.8x |
| 15 | DVB-S2-inspired (header + pilot block, 126) | -2.26 | +0.66 | 0.042 | 4.3x |
| 16 | Wi-Fi 802.11 real 320 + lobes | -2.26 | +0.66 | 0.359 | 0.5x |
| 17 | MIL-STD-188-110, full 411 known | -2.15 | +0.77 | 0.035 | 5.1x |
| 18 | CCSDS 131.2 real pilot density (32) | -1.94 | +0.98 | 0.348 | 0.5x |
| 19 | VDE-SAT (ITU-R M.2092, 66 known) | -1.77 | +1.16 | 0.035 | 5.1x |
| 20 | Griebel 2021 FFT 2048 | -1.34 | +1.59 | 0.029 | 6.2x |
| 21 | Griebel 2021 FFT 2048 N | -1.34 | +1.59 | 0.029 | 6.2x |
| 22 | Griebel 2021 as published | -1.26 | +1.67 | 0.029 | 6.2x |
| 23 | DVB-RCS2 16 + 16 pre/post, 4th power | fails (min BLER 1.9e-01) | - | - | - |
| 24 | Sparse pilots, 1 in 32 | fails (min BLER 8.3e-02) | - | - | - |
| 25 | ViaSat burst (16-symbol UW) | fails (min BLER 7.0e-01) | - | - | - |
| 26 | Advantech hybrid DA + NDA | fails (min BLER 2.0e-01) | - | - | - |
| 27 | ViaSat US 7653150 (single peak) | fails (min BLER 8.2e-01) | - | - | - |
| 28 | ViaSat top-32 + 4th-power phase | fails (min BLER 7.1e-01) | - | - | - |
| 29 | Advantech 48 preamble | fails (min BLER 3.4e-01) | - | - | - |
| 30 | Advantech 48 preamble, wide DA window | fails (min BLER 2.0e-04) | - | - | - |
| 31 | Wi-Fi 802.11 real 320 (STF + LTF) | fails (min BLER 8.2e-04) | - | - | - |

## R = 2/5, BLER 1e-03: blind 0.58 dB, 0.183 M MACs per core

| # | Receiver | Required SNR [dB] | Gap to blind [dB] | MACs per core [M] | blind / it MACs |
|---|---|---|---|---|---|
| 1 | Advantech 48 preamble, wide DA window | 0.91 | +0.33 | 0.101 | 1.8x |
| 2 | VDE-SAT (ITU-R M.2092, 66 known) | 0.92 | +0.34 | 0.041 | 4.5x |
| 3 | CCSDS 131.0 ASM (64, +-12 lobes) | 0.95 | +0.38 | 0.142 | 1.3x |
| 4 | DVB-S2 PL header only (90, CFO scan) | 1.02 | +0.44 | 0.833 | 0.2x |
| 5 | DVB-RCS2 ID 13 (116 known, Rife-Boorstyn) | 1.10 | +0.52 | 0.040 | 4.6x |
| 6 | Griebel 2021 FFT 2048 | 1.10 | +0.52 | 0.035 | 5.2x |
| 7 | Griebel 2021 FFT 2048 N | 1.10 | +0.52 | 0.035 | 5.2x |
| 8 | Griebel 2021 FFT 4096 | 1.10 | +0.52 | 0.036 | 5.1x |
| 9 | DVB-RCS2 ID 13 + lobe search | 1.10 | +0.52 | 0.040 | 4.6x |
| 10 | 64 + 64 pre/post, joint ML (+-3 lobes) | 1.12 | +0.54 | 0.066 | 2.8x |
| 11 | DVB-S2-inspired (header + pilot block, 126) | 1.12 | +0.55 | 0.042 | 4.4x |
| 12 | 64 + 64 pre/post, joint ML (+-4 lobes) | 1.12 | +0.55 | 0.067 | 2.7x |
| 13 | CCSDS-inspired (8 x 16 blocks) | 1.13 | +0.55 | 0.052 | 3.5x |
| 14 | CCSDS 131.2 real pilot density (32) | 1.15 | +0.58 | 0.300 | 0.6x |
| 15 | 128-symbol preamble, Mengali-Morelli | 1.16 | +0.58 | 0.086 | 2.1x |
| 16 | 128-symbol preamble, ML | 1.16 | +0.59 | 0.085 | 2.2x |
| 17 | Wi-Fi-like 128-symbol preamble | 1.17 | +0.59 | 0.228 | 0.8x |
| 18 | 5G-NR-like DMRS, 1 in 7 | 1.28 | +0.70 | 0.040 | 4.6x |
| 19 | Griebel 2021 as published | 1.29 | +0.71 | 0.034 | 5.4x |
| 20 | CCSDS-inspired, per-block phase | 1.36 | +0.78 | 0.056 | 3.3x |
| 21 | MIL-STD-188-110 HF (current layout) | 1.75 | +1.17 | 0.041 | 4.5x |
| 22 | Advantech hybrid DA + NDA | 1.79 | +1.22 | 0.051 | 3.6x |
| 23 | Wi-Fi 802.11 real 320 + lobes | 1.84 | +1.26 | 0.238 | 0.8x |
| 24 | Wi-Fi 802.11 real 320 (STF + LTF) | 1.88 | +1.30 | 0.097 | 1.9x |
| 25 | Advantech 48 preamble | 2.02 | +1.45 | 0.048 | 3.8x |
| 26 | MIL-STD-188-110, full 411 known | 2.09 | +1.51 | 0.041 | 4.5x |
| 27 | DVB-RCS2 16 + 16 pre/post, 4th power | fails (min BLER 1.6e-02) | - | - | - |
| 28 | Sparse pilots, 1 in 32 | fails (min BLER 1.8e-03) | - | - | - |
| 29 | ViaSat burst (16-symbol UW) | fails (min BLER 1.1e-02) | - | - | - |
| 30 | ViaSat US 7653150 (single peak) | fails (min BLER 2.0e-02) | - | - | - |
| 31 | ViaSat top-32 + 4th-power phase | fails (min BLER 1.0e-02) | - | - | - |

## R = 1/2, BLER 1e-03: blind 1.73 dB, 0.139 M MACs per core

| # | Receiver | Required SNR [dB] | Gap to blind [dB] | MACs per core [M] | blind / it MACs |
|---|---|---|---|---|---|
| 1 | Advantech 48 preamble, wide DA window | 2.11 | +0.38 | 0.070 | 2.0x |
| 2 | VDE-SAT (ITU-R M.2092, 66 known) | 2.16 | +0.44 | 0.043 | 3.2x |
| 3 | Advantech 48 preamble | 2.18 | +0.45 | 0.051 | 2.7x |
| 4 | CCSDS 131.0 ASM (64, +-12 lobes) | 2.19 | +0.47 | 0.144 | 1.0x |
| 5 | DVB-RCS2 ID 13 (116 known, Rife-Boorstyn) | 2.33 | +0.61 | 0.043 | 3.2x |
| 6 | Griebel 2021 FFT 2048 | 2.33 | +0.61 | 0.037 | 3.8x |
| 7 | Griebel 2021 FFT 2048 N | 2.33 | +0.61 | 0.037 | 3.8x |
| 8 | Griebel 2021 FFT 4096 | 2.33 | +0.61 | 0.039 | 3.6x |
| 9 | DVB-RCS2 ID 13 + lobe search | 2.33 | +0.61 | 0.043 | 3.2x |
| 10 | Advantech hybrid DA + NDA | 2.34 | +0.61 | 0.053 | 2.6x |
| 11 | CCSDS 131.2 real pilot density (32) | 2.35 | +0.63 | 0.258 | 0.5x |
| 12 | 64 + 64 pre/post, joint ML (+-3 lobes) | 2.37 | +0.65 | 0.065 | 2.1x |
| 13 | 64 + 64 pre/post, joint ML (+-4 lobes) | 2.37 | +0.64 | 0.067 | 2.1x |
| 14 | CCSDS-inspired (8 x 16 blocks) | 2.39 | +0.66 | 0.053 | 2.6x |
| 15 | DVB-S2-inspired (header + pilot block, 126) | 2.39 | +0.66 | 0.044 | 3.2x |
| 16 | 128-symbol preamble, Mengali-Morelli | 2.41 | +0.69 | 0.068 | 2.0x |
| 17 | 128-symbol preamble, ML | 2.41 | +0.69 | 0.068 | 2.0x |
| 18 | Wi-Fi-like 128-symbol preamble | 2.42 | +0.69 | 0.209 | 0.7x |
| 19 | Sparse pilots, 1 in 32 | 2.46 | +0.73 | 0.050 | 2.8x |
| 20 | 5G-NR-like DMRS, 1 in 7 | 2.53 | +0.81 | 0.043 | 3.2x |
| 21 | Griebel 2021 as published | 2.55 | +0.82 | 0.036 | 3.9x |
| 22 | CCSDS-inspired, per-block phase | 2.58 | +0.86 | 0.054 | 2.6x |
| 23 | ViaSat top-32 + 4th-power phase | 2.61 | +0.89 | 0.043 | 3.2x |
| 24 | ViaSat US 7653150 (single peak) | 2.74 | +1.01 | 0.039 | 3.6x |
| 25 | DVB-RCS2 16 + 16 pre/post, 4th power | 2.77 | +1.04 | 0.043 | 3.2x |
| 26 | MIL-STD-188-110 HF (current layout) | 3.00 | +1.27 | 0.044 | 3.2x |
| 27 | Wi-Fi 802.11 real 320 (STF + LTF) | 3.11 | +1.39 | 0.099 | 1.4x |
| 28 | Wi-Fi 802.11 real 320 + lobes | 3.11 | +1.38 | 0.218 | 0.6x |
| 29 | MIL-STD-188-110, full 411 known | 3.34 | +1.62 | 0.044 | 3.2x |
| 30 | ViaSat burst (16-symbol UW) | fails (min BLER 1.2e-03) | - | - | - |
| 31 | DVB-S2 PL header only (90, CFO scan) | fails (min BLER 2.7e-02) | - | - | - |
