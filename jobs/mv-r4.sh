#!/bin/bash
# mv-r4: v3 MAC-saving variants (2-SPS features, adaptive phases, early abort)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/4:0:4 1/4:0.5:4 1/4:1:4 1/4:1.5:4 1/4:2:4 1/4:3:4 --max-frames 25000 --min-errors 100 --rx "v3 lite + CRC" "v3 lite, adaptive phases + CRC" "v3 lite, early abort + CRC" "v3 lite, adaptive + abort + CRC" "Best-first search v3 fast + CRC" --seed 5432 --part mv-r4 > logs/run_mv-r4.out 2>&1
