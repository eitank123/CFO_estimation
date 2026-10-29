#!/bin/bash
# ckr-pn25: pilots, prior NN shortlist (>= 16 cells) in H + rescue, R = 2/5 0.5 / 1 dB, paired with rs-25
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_ckr-pn25.out
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" --seed 5702 --part ckr-pn25 >> logs/run_ckr-pn25.out 2>&1
