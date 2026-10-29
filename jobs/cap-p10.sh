#!/bin/bash
# cap-p10: bounded parallel decoders, pilots R = 1/10: baseline, top 64 / 32, batches of 64 / 32 z 3 / 5
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_cap-p10.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off, keep 2 phases, join top 8, rescue, tree cost + CRC" "S pilots 1/10 best, top 64" "S pilots 1/10 best, top 32" "S pilots 1/10 best, batches of 64, z 3" "S pilots 1/10 best, batches of 64, z 5" "S pilots 1/10 best, batches of 32, z 3" "S pilots 1/10 best, batches of 32, z 5" --seed 5701 --part smoke-cap-p10 >> logs/run_cap-p10.out 2>&1
echo "SMOKE DONE" >> logs/run_cap-p10.out
