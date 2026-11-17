#!/bin/bash
# fs-nbda: NB-IoT NPUSCH F1 (single tone 3.75 kHz) with the DATA-AIDED synchroniser on its DM-RS (1 per 2 ms slot;
# da_sync on the DM-RS comb, true symbol times incl. the 3/11-symbol guard), CFO U(+-0.035)/symbol (the 36.108 SAN
# test offset 128 Hz = 0.0352 per 275 us symbol) + uniform phase, N0 estimated, timing known. Variant strong (top-3
# candidates until the CRC-24A); the standard receiver (1 estimate, 1 decode) is its attempt 1 (standard_* fields,
# chunks.err_idx_att1). Seed 50 = ideal fs-nbv (paired packets: same payload + noise). Decoder max-log x 0.75, 8 it,
# CRC-24A early stop. Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --sys nbiot --variant strong --top-m 3 --cfo-max 0.035 --frames 1000000 --max-err 300 --seed 50 --workers 16"
( $R --nbfmt nb208 --snrs -4.50 -4.25 -4.00 -3.75 -3.50 -3.25 -3.00 -2.75 -2.50 -2.25 -2.00 -1.75 -1.50 -1.25 -1.00 --part fs-nbda-208
  $R --nbfmt nb328 --snrs -2.50 -2.25 -2.00 -1.75 -1.50 -1.25 -1.00 -0.75 -0.50 -0.25 0.00 0.25 0.50 0.75 1.00 --part fs-nbda-328
  $R --nbfmt nb808 --snrs 0.25 0.50 0.75 1.00 1.25 1.50 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 --part fs-nbda-808
  $R --nbfmt nb1000 --snrs 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 4.00 4.25 4.50 4.75 5.00 5.25 --part fs-nbda-1000
  echo "ALL DONE" ) > logs/run_fs-nbda.out 2>&1
