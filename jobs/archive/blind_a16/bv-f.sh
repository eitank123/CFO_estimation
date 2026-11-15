#!/bin/bash
# bv-f: v3 optimised implementation + hard path metric, BLER + wall time
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:2 1/10:-4:2 1/10:-3:2 1/10:-2:2 1/10:-1:2 1/10:0:2 1/4:0:2 1/4:1:2 1/4:2:2 1/2:3:2 --max-frames 25000 --min-errors 100 --rx "Best-first search v3 fast + CRC" "Best-first search v3 fast, hard metric + CRC" --seed 5306 --part bv-f > logs/run_bv-f.out 2>&1
