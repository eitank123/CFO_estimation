#!/bin/bash
# fairb15: 128-pilot references, decode at f_hat first then metric-ordered neighbours (PM+3, PM+all) vs fixed order (expected_fair.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
( $PY -u est3/run_bler.py --rate 0.15 --snrs -4 -3 -2 -1 0 1 --sources 'Genie CFO' 'ML direct' 'ML direct PM+3' 'ML direct PM+all' M\&M 'M&M PM+3' 'M&M PM+all' --max-frames 480000 --min-errors 100000 --chunks 16 --seed 37 --part fairb15
  echo "ALL DONE" ) > logs/run_fairb15.out 2>&1
