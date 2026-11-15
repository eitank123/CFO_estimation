#!/bin/bash
# join3-smoke: round 3 of the R = 1/10 MAC cuts: join top 16 + phase hand-off + each continuing cell keeps its best 2
# phases at 1/2 (blind, pilots); pilots with an early checkpoint at 1/8; paired with join-smoke (same seeds)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_join3-smoke.out
C="S blind, checkpoints, coarse start, join top 16, phase hand-off"; H="S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off"
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$C, keep 2 phases, rescue, tree cost + CRC" "$H, keep 2 phases, rescue, tree cost + CRC" "$H, early 1/8, rescue, tree cost + CRC" "$H, early 1/8, keep 2 phases, rescue, tree cost + CRC" --seed 5701 --part smoke-join3 >> logs/run_join3-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_join3-smoke.out
