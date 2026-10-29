#!/bin/bash
# ckr-p10: checkpoint NN in the pilots search (H + rescue), R = 1/10 -5 / -4.5 dB, paired with rs-p10
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_ckr-p10.out
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4.5:8 --max-frames 25000 --min-errors 100 --rx "S pilots N3x8, checkpoints, pilot score, checkpoint NN, rescue + CRC" --seed 5701 --part ckr-p10 >> logs/run_ckr-p10.out 2>&1
