#!/bin/bash
# diag-k: R = 1/10 above -3 dB with the grid step fixed at 4 STEP (blind_fast.grid_step widens it to 6 / 8): blind new best (+ 4 phases), blind old, pilots new best
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_diag-k.out
$PY -u blind_ber.py --points 1/10:0:16 1/10:-1:16 1/10:-2:16 --max-frames 700 --min-errors 100000 --rx "S blind 1/10 best, grid 4" "S blind 1/10 best, grid 4, 4 phases" "S blind, checkpoints, coarse start, rescue, grid 4 + CRC" "S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off, keep 2 phases, join top 8, rescue, tree cost + CRC" "S pilots 1/10 best, grid 4" --seed 5701 --part smoke-diag-k >> logs/run_diag-k.out 2>&1
echo "SMOKE DONE" >> logs/run_diag-k.out
