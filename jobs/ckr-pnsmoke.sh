#!/bin/bash
# ckr-pnsmoke: smoke of the pilots receiver with the prior NN shortlist per rate (blind_ber "NN per rate"): R = 2/5
# 0.5 dB and R = 1/2 2 dB, 1600 frames each, against the same receiver without it
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_ckr-pnsmoke.out
P="S pilots N3x8, checkpoints, pilot score"
$PY -u blind_ber.py --points 2/5:0.5:8 1/2:2:8 --max-frames 200 --min-errors 100 --rx "$P, rescue + CRC" "$P, NN per rate, rescue + CRC" --seed 5702 --part smoke-pn >> logs/run_ckr-pnsmoke.out 2>&1
echo "SMOKE DONE" >> logs/run_ckr-pnsmoke.out
