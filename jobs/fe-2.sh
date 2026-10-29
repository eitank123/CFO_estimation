#!/bin/bash
# fe-2: E2, metric separation / basin / time per evaluation (blind_fast.py metric)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
: > logs/run_fe-2.out
$PY -u blind_fast.py metric --rates 1/10 --snrs -5 -4 -3 -2 -1 0 --frames 500 --chunks 4 --part r10 >> logs/run_fe-2.out 2>&1
$PY -u blind_fast.py metric --rates 1/4 --snrs 0 1 2 3 --frames 500 --chunks 4 --part r4 >> logs/run_fe-2.out 2>&1
$PY -u blind_fast.py metric --rates 1/2 --snrs 2 3 4 --frames 500 --chunks 4 --part r2 >> logs/run_fe-2.out 2>&1
