#!/bin/bash
# race2-2: replay v2 (Fast-SSC cost per leaf, neighbour criterion, early lenient checkpoint, small beams) of PM pruning rules (phase racing, PM gap, beam vs the z-test) on 30000 search packets per point,
# R = 1/2 (small_race.py); a 32-packet run first so a crash shows at once
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_race2-2.out
$PY -u small_race.py --points 1/2:2 --packets 32 --workers 4 --part smoke-race2-2 >> logs/run_race2-2.out 2>&1 && $PY -u small_race.py --points 1/2:2 --packets 30000 --workers 16 --part race2-2 --seed 71 >> logs/run_race2-2.out 2>&1
