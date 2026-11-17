#!/bin/bash
# fs-nbvx (optional): the NB-IoT format variants, ideal sync + polar genie, to justify the format choice: nb208b
# (TBS 208 pi/2-BPSK, 8 RUs), nb296 (closest TBS to 307, 2 RUs, rate 0.83), nb1000r10 (TBS 1000, 10 RUs + the 40 ms
# uplink gap). Seed 50 (polar payloads = the NB-IoT payloads, batch 200). Grids are first guesses (see fs-nbsmoke).
# Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --sys nbiot --variant ideal --frames 1000000 --max-err 300 --workers 16 --seed 50"
P="$PY -u fullsys/run_polar_genie.py --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 50 --workers 16"
( $R --nbfmt nb208b --snrs -5.00 -4.75 -4.50 -4.25 -4.00 -3.75 -3.50 -3.25 -3.00 -2.75 -2.50 -2.25 -2.00 --part fs-nbvx-208b
  $R --nbfmt nb296 --snrs 4.00 4.50 5.00 5.50 6.00 6.50 7.00 7.50 8.00 --part fs-nbvx-296
  $R --nbfmt nb1000r10 --snrs 0.25 0.50 0.75 1.00 1.25 1.50 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 --part fs-nbvx-1000r
  $P --fmt nb208b --snrs -5.00 -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 -2.40 -2.20 -2.00 --part fs-nbvx-pg208b
  $P --fmt nb296 --snrs 3.50 4.00 4.50 5.00 5.50 6.00 6.50 7.00 7.50 8.00 --part fs-nbvx-pg296
  $P --fmt nb1000r10 --snrs -0.25 0.00 0.25 0.50 0.75 1.00 1.25 1.50 1.75 2.00 2.25 2.50 2.75 3.00 3.25 --part fs-nbvx-pg1000r
  echo "ALL DONE" ) > logs/run_fs-nbvx.out 2>&1
