#!/bin/bash
# est3-y15b: more packets for bler_more R = 0.15: ML, M&M, CRB, seed 2 (seed 1 = m15 / crb15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
( $PY -u est3/run_bler.py --rate 0.15 --snrs -4 -3.5 -3 -2.5 -2 -1 0 1 --sources 'ML direct' 'M&M' 'CRB 128 pilots' --max-frames 480000 --min-errors 2000 --seed 2 --part y15b
  echo "ALL DONE" ) > logs/run_est3-y15b.out 2>&1
