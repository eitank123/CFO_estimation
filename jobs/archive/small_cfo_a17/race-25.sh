#!/bin/bash
# race-25: replay of PM pruning rules (phase racing, PM gap, beam vs the z-test) on 30000 search packets per point,
# R = 2/5 (small_race.py); a 32-packet run first so a crash shows at once
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_race-25.out
$PY -u small_race.py --points 2/5:0.5 --packets 32 --workers 4 --part smoke-race-25 >> logs/run_race-25.out 2>&1 && $PY -u small_race.py --points 2/5:0.5 2/5:1 --packets 30000 --workers 16 --part race-25 >> logs/run_race-25.out 2>&1
