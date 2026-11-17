#!/bin/bash
# fs-bl13: blind (adopted 2/5 receiver base25_qfix_fzs + format hooks; F5 / spec off, rho scaled: provisional) on RCS2 ID 13 (A 952, E 2952, N 4096 puncture, CRC-32), QPSK, |f| <= 0.03; data + noise paired with fs-pg13 (seed 13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 0.40 0.60 --frames 100000 --max-err 200 --stop-per 2e-4 --seed 13 --workers 16 --part fs-bl13
  echo "ALL DONE" ) > logs/run_fs-bl13.out 2>&1
