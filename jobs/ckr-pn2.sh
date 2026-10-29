#!/bin/bash
# ckr-pn2: pilots, prior NN shortlist (>= 16 cells) in H + rescue, R = 1/2 2 / 2.5 dB, paired with rs-2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_ckr-pn2.out
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 --max-frames 50000 --min-errors 100 --rx "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" --seed 5703 --part ckr-pn2 >> logs/run_ckr-pn2.out 2>&1
