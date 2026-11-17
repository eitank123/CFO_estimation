#!/bin/bash
# fs-pg42: rate-matched polar (A 952, E 2952, N 4096 puncture, CRC-32, CA-SCL-8), genie sync, vs RCS2 ID 42 (TR T10.8 -3.81 / -3.52 dB): pi/2-BPSK (2952 symbols) and QPSK (1476 symbols), same seed = same data
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id42b --snrs -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 42 --workers 16 --part fs-pg42b
  $PY -u fullsys/run_polar_genie.py --fmt id42q --snrs -1.80 -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 42 --workers 16 --part fs-pg42q
  echo "ALL DONE" ) > logs/run_fs-pg42.out 2>&1
