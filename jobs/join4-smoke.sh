#!/bin/bash
# join4-smoke: round 4 of the R = 1/10 MAC cuts: coarse start on every 3rd cell (+ one-sided join of the 2 cells between), tighter join (top 8); paired (same seeds) with join-smoke / join3-smoke
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_join4-smoke.out
C="S blind, checkpoints, coarse start, join top 16, phase hand-off"; H="S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off"
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$C, keep 2 phases, stride 3, rescue, tree cost + CRC" "$C, keep 2 phases, join top 8, rescue, tree cost + CRC" "$H, keep 2 phases, stride 3, rescue, tree cost + CRC" "$H, keep 2 phases, join top 8, rescue, tree cost + CRC" --seed 5701 --part smoke-join4 >> logs/run_join4-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_join4-smoke.out
