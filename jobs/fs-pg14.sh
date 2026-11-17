#!/bin/bash
# fs-pg14: rate-matched polar (A 1472, E 3008, N 4096, CRC-32, CA-SCL-8), QPSK, genie sync, vs RCS2 ID 14 (TR T10.6 1.49 / 1.71 dB): shorten (standard rule) and forced puncture, same seed = same data and noise
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id14s --snrs 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 14 --workers 16 --part fs-pg14s
  $PY -u fullsys/run_polar_genie.py --fmt id14p --snrs 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 14 --workers 16 --part fs-pg14p
  echo "ALL DONE" ) > logs/run_fs-pg14.out 2>&1
