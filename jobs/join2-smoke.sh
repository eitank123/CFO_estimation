#!/bin/bash
# join2-smoke: "join top 16" (only the best 16 surviving coarse cells bring in neighbours), alone and with the phase hand-off, blind and pilots, R = 1/10
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_join2-smoke.out
C="S blind, checkpoints, coarse start"; H="S pilots N3x8, checkpoints, pilot score"
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$C, join top 16, rescue, tree cost + CRC" "$C, join top 16, phase hand-off, rescue, tree cost + CRC" --seed 5701 --part smoke-join2-b >> logs/run_join2-smoke.out 2>&1
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$H, coarse start, join top 16, rescue, tree cost + CRC" "$H, coarse start, join top 16, phase hand-off, rescue, tree cost + CRC" --seed 5701 --part smoke-join2-p >> logs/run_join2-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_join2-smoke.out
