#!/bin/bash
# fs-pg13: rate-matched polar (A 952, E 2952, N 4096 puncture, CRC-32, CA-SCL-8), QPSK, genie sync, vs RCS2 ID 13 (TR T10.6 -0.80 / -0.51 dB); payloads paired with fs-rcs2v13 (seed 13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id13 --snrs -1.80 -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 13 --workers 16 --part fs-pg13
  echo "ALL DONE" ) > logs/run_fs-pg13.out 2>&1
