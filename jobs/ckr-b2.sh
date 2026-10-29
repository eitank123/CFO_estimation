#!/bin/bash
# ckr-b2: checkpoint NN in the blind search (checkpoints + rescue), R = 1/2 2 / 2.5 dB, paired with rs-2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_ckr-b2.out
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 --max-frames 50000 --min-errors 100 --rx "S blind, checkpoints, checkpoint NN, rescue + CRC" --seed 5703 --part ckr-b2 >> logs/run_ckr-b2.out 2>&1
