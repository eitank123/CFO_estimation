#!/bin/bash
# fairb25: 128-pilot references, decode at f_hat first then metric-ordered neighbours (PM+3, PM+all) vs fixed order (expected_fair.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
( $PY -u est3/run_bler.py --rate 2/5 --snrs 0.5 1 1.5 2 --sources 'Genie CFO' 'ML direct' 'ML direct PM+3' 'ML direct PM+all' M\&M 'M&M PM+3' 'M&M PM+all' --max-frames 480000 --min-errors 100000 --chunks 16 --seed 39 --part fairb25
  echo "ALL DONE" ) > logs/run_fairb25.out 2>&1
