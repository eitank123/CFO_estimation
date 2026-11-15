#!/bin/bash
# fair-smoke: fair 128-pilot references: the fixed-order CRC search vs the path-metric-ordered one (PM_T = 3), same packets (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
S="Genie CFO" 
( $PY -u est3/run_bler.py --rate 0.15 --snrs -3 --sources 'Genie CFO' 'ML direct' 'ML direct PM' M\&M 'M&M PM' --max-frames 1600 --min-errors 100000 --chunks 16 --seed 31 --part fair-smoke
  echo "ALL DONE" ) > logs/run_fair-smoke.out 2>&1
