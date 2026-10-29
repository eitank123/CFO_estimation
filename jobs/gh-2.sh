#!/bin/bash
# gh-2: small-CFO study, coarse start (G) and pilots inside the cell score (H) at full statistics, paired with D
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_gh-2.out
$PY -u blind_ber.py --points 1/2:1.5:8 1/2:2:8 1/2:2.5:8 1/2:3:8 --max-frames 50000 --min-errors 100 --rx "S blind, checkpoints, coarse start + CRC" "S pilots N3x8, checkpoints, coarse start + CRC" "S pilots N3x8, checkpoints, pilot score + CRC" --seed 5703 --part gh-20 >> logs/run_gh-2.out 2>&1
