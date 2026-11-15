#!/bin/bash
# fill-10p: best 3x8 (pilot score + rescue) at the missing SNRs, R = 1/10 -3..0 dB (plots)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fill-10p.out
$PY -u blind_ber.py --points 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 --rx "S pilots N3x8, checkpoints, pilot score, rescue + CRC" --seed 5701 --max-frames 25000 --min-errors 100 --part fill-10p >> logs/run_fill-10p.out 2>&1
