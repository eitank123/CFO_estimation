#!/bin/bash
# bv-e: blind best-first search v3 (blind_fast.py), BLER + wall time, points 1/10:-5:2 1/10:-3:2 1/10:-1:2 1/10:0:2 1/4:0:2 1/4:1:2 1/4:2:2 1/2:3:2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:2 1/10:-3:2 1/10:-1:2 1/10:0:2 1/4:0:2 1/4:1:2 1/4:2:2 1/2:3:2 --max-frames 25000 --min-errors 100 --rx "Best-first search v2 + re-encoding check + CRC" "Best-first search v2 + pre-MF correction + CRC" --seed 5305 --part bv-e > logs/run_bv-e.out 2>&1
