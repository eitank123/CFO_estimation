#!/bin/bash
# sm-s5: smoke of the rescue versions: runs + MACs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --points 1/10:-5:8 2/5:0.5:8 --max-frames 150 --min-errors 100 --rx "S blind, no checkpoints, MF per candidate, CA retry, rescue + CRC" "S blind, checkpoints, rescue + CRC" "S blind, checkpoints, coarse start, rescue + CRC" "S pilots N3x8, no checkpoints, MF per candidate, CA retry, rescue + CRC" "S pilots N3x8, checkpoints, rescue + CRC" "S pilots N3x8, checkpoints, pilot score, rescue + CRC" --seed 5701 --part smoke-s5 > logs/run_sm-s5.out 2>&1
