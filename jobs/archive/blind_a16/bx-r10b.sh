#!/bin/bash
# bx-r10b: blind R = 1/10 complexity on top of the rescue (adaptive phases / + screening), paired with fx-r10b5 / b4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue, adaptive from -5.5 dB + CRC" "v3 eco7, rescue, screen from -5.5 dB + CRC" --seed 5701 --part bx-r10b > logs/run_bx-r10b.out 2>&1
