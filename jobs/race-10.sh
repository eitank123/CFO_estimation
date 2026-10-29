#!/bin/bash
# race-10: replay of PM pruning rules (phase racing, PM gap, beam vs the z-test) on 30000 search packets per point,
# R = 1/10 (small_race.py); a 32-packet run first so a crash shows at once
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_race-10.out
$PY -u small_race.py --points 1/10:-5 --packets 32 --workers 4 --part smoke-race-10 >> logs/run_race-10.out 2>&1 && $PY -u small_race.py --points 1/10:-5 1/10:-4.5 1/10:-4 --packets 30000 --workers 16 --part race-10 >> logs/run_race-10.out 2>&1
