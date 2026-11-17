#!/bin/bash
# fs-nbpg: our rate-matched polar (CA-SCL-8, CRC-32, A = the NB-IoT TBS, E = the NPUSCH coded bits G, genie sync) at the
# 4 main NB-IoT formats: nb208 (A 208, E 1152, N 1024 + repetition), nb328 (328, 1152, repetition), nb808 (808, 1536,
# N 2048 shortened), nb1000 (1000, 1536, shortened). Seed 50, batch 200: the payloads equal those of fs-nbv / fs-nbda.
# Blind sends E/2 QPSK symbols (no DM-RS). Grids are first guesses (polar expected at or below the turbo threshold).
# Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
P="$PY -u fullsys/run_polar_genie.py --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 50 --workers 16"
( $P --fmt nb208 --snrs -5.00 -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 -2.40 -2.20 -2.00 -1.80 -1.60 --part fs-nbpg-208
  $P --fmt nb328 --snrs -3.20 -3.00 -2.80 -2.60 -2.40 -2.20 -2.00 -1.80 -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 --part fs-nbpg-328
  $P --fmt nb808 --snrs -0.40 -0.20 0.00 0.20 0.40 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 3.00 --part fs-nbpg-808
  $P --fmt nb1000 --snrs 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 3.00 3.20 3.40 3.60 3.80 4.00 4.20 4.40 --part fs-nbpg-1000
  echo "ALL DONE" ) > logs/run_fs-nbpg.out 2>&1
