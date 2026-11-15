#!/bin/bash
# mv-r3: v3 MAC-saving variants, R = 1/3
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:0.5:4 1/3:1:4 1/3:1.5:4 1/3:2:4 1/3:2.5:4 1/3:3:4 1/3:4:4 --max-frames 25000 --min-errors 100 --rx "v3 lite + CRC" "v3 lite, adaptive phases + CRC" "v3 lite, early abort + CRC" "v3 lite, adaptive + abort + CRC" "Best-first search v3 fast + CRC" --seed 5464 --part mv-r3 > logs/run_mv-r3.out 2>&1
