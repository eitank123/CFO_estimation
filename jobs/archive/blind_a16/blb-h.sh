#!/bin/bash
# blb-h: turbo (DD) receiver again with the fixed decision-directed step (scan + Newton); T4 decision-directed test
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_cfo.py dd --snrs -5 -3 -2 0 2 4 6 8 10 --frames 4000 --part a > logs/run_bt-dd.out 2>&1
$PY -u blind_ber.py --points 1/10:-2:2 1/10:0:2 1/10:2:4 1/4:0:2 1/4:1:2 1/4:2:4 1/4:3:8 1/4:4:8 1/2:2:2 1/2:3:4 1/2:4:4 1/2:5:8 --max-frames 30000 --min-errors 100 --rx "4th power + turbo (DD) + CRC" --seed 5050 --part h > logs/run_blb-h.out 2>&1
