#!/bin/bash
# jt-10: the R = 1/10 MAC cuts at full statistics (paired with rs-p10 / rs-b10 / fill-10*): coarse start + join top 8 +
# phase hand-off + best 2 phases at 1/2, tree cost; blind and pilots (H + coarse start), -5 / -4.5 / -4 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_jt-10.out
C="S blind, checkpoints, coarse start, join top 16, phase hand-off, keep 2 phases"; H="S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off, keep 2 phases"
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4.5:8 1/10:-4:8 --max-frames 25000 --min-errors 100 --rx "$C, join top 8, rescue, tree cost + CRC" "$H, join top 8, rescue, tree cost + CRC" --seed 5701 --part jt-10 >> logs/run_jt-10.out 2>&1
