#!/bin/bash
# join-smoke: cheaper neighbour join of the coarse start (one-sided join / phase hand-off / both), blind (coarse-start
# receiver) and pilots (H + coarse start), tree cost, R = 1/10 -5 / -4.5 / -4 dB, paired against the plain coarse start
# and the current best pilots receiver
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_join-smoke.out
C="S blind, checkpoints, coarse start"; H="S pilots N3x8, checkpoints, pilot score"
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$C, rescue, tree cost + CRC" "$C, one-sided join, rescue, tree cost + CRC" "$C, phase hand-off, rescue, tree cost + CRC" "$C, one-sided join, phase hand-off, rescue, tree cost + CRC" --seed 5701 --part smoke-join-b >> logs/run_join-smoke.out 2>&1
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$H, rescue, tree cost + CRC" "$H, coarse start, rescue, tree cost + CRC" "$H, coarse start, one-sided join, rescue, tree cost + CRC" "$H, coarse start, phase hand-off, rescue, tree cost + CRC" "$H, coarse start, one-sided join, phase hand-off, rescue, tree cost + CRC" --seed 5701 --part smoke-join-p >> logs/run_join-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_join-smoke.out
