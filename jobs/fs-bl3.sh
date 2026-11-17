#!/bin/bash
# fs-bl3: blind (base25_qfix_fzs) on RCS2 ID 3 (A 272, E 912, N 1024 puncture, 456 QPSK symbols); paired with fs-pg3 (seed 3)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id3 --snrs -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 0.40 0.60 0.80 1.00 1.20 1.40 1.60 --frames 100000 --max-err 200 --stop-per 2e-4 --seed 3 --workers 16 --part fs-bl3
  echo "ALL DONE" ) > logs/run_fs-bl3.out 2>&1
