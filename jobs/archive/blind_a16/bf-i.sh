#!/bin/bash
# bf-i: blind best-first search v2 (blind_fast.py), BLER + wall time, points 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 1/2:6:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 1/2:6:4 --max-frames 50000 --min-errors 100 --rx "Best-first search v2 + CRC" --seed 5204 --part bf-i > logs/run_bf-i.out 2>&1
