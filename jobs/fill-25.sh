#!/bin/bash
# fill-25: best blind (checkpoint NN) and best 3x8 (prior NN) at the missing SNRs, R = 2/5 0, 1.5..3 dB (plots)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fill-25.out
$PY -u blind_ber.py --points 2/5:0:4 2/5:1.5:4 2/5:2:4 2/5:2.5:4 2/5:3:4 --rx "S blind, checkpoints, checkpoint NN, rescue + CRC" "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" --seed 5702 --max-frames 25000 --min-errors 100 --part fill-25 >> logs/run_fill-25.out 2>&1
