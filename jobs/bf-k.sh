#!/bin/bash
# bf-k: blind best-first search v2 (blind_fast.py), BLER + wall time, points 1/10:-5:2 1/10:-3:2 1/10:-1:2 1/10:0:2 1/4:0:2 1/4:1:2 1/4:2:2 1/2:3:2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:2 1/10:-3:2 1/10:-1:2 1/10:0:2 1/4:0:2 1/4:1:2 1/4:2:2 1/2:3:2 --max-frames 15000 --min-errors 100 --rx "Best-first search v2 + CRC" "Best-first search v2, weighted metric + CRC" "Best-first search v2, weighted + exact box-plus + CRC" --seed 5206 --part bf-k > logs/run_bf-k.out 2>&1
