#!/bin/bash
# fair25: fair 128-pilot references: the fixed-order CRC search vs the path-metric-ordered one (PM_T = 3), same packets (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
S="Genie CFO" 
( $PY -u est3/run_bler.py --rate 2/5 --snrs 0.5 1 1.5 2 --sources 'Genie CFO' 'ML direct' 'ML direct PM' M\&M 'M&M PM' --max-frames 480000 --min-errors 100000 --chunks 16 --seed 34 --part fair25
  echo "ALL DONE" ) > logs/run_fair25.out 2>&1
