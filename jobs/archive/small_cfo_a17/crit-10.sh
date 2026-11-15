#!/bin/bash
# crit-10: R = 1/10 with the critical-path MAC count (serial MACs + per pass the busiest core): the best receivers all at once, on 64 / 32 cores in passes, and in batches of 64 / 32
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_crit-10.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S blind, checkpoints, coarse start, join top 16, phase hand-off, keep 2 phases, join top 8, rescue, tree cost + CRC" "S blind 1/10 best, 64 cores" "S blind 1/10 best, 32 cores" "S blind 1/10 best, batches of 64, z 5" "S blind 1/10 best, batches of 32, z 5" "S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off, keep 2 phases, join top 8, rescue, tree cost + CRC" "S pilots 1/10 best, 64 cores" "S pilots 1/10 best, 32 cores" "S pilots 1/10 best, batches of 64, z 3" "S pilots 1/10 best, batches of 32, z 3" --seed 5701 --part smoke-crit-10 >> logs/run_crit-10.out 2>&1
echo "SMOKE DONE" >> logs/run_crit-10.out
