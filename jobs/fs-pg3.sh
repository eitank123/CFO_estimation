#!/bin/bash
# fs-pg3: rate-matched polar (A 272, E 912, N 1024 puncture, CRC-32, CA-SCL-8), QPSK, genie sync, vs RCS2 ID 3 (TR T10.5 -0.27 / 0.22 dB); payloads paired with fs-rcs2v3 (seed 3)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id3 --snrs -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 0.40 0.60 0.80 1.00 1.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 3 --workers 16 --part fs-pg3
  echo "ALL DONE" ) > logs/run_fs-pg3.out 2>&1
