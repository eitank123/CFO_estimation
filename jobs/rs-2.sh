#!/bin/bash
# rs-2: small-CFO study, the receivers with the rescue stage (final_post / fine_last) at full statistics, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_rs-2.out
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 --max-frames 50000 --min-errors 100 --rx "S blind, no checkpoints, MF per candidate, CA retry, rescue + CRC" "S blind, checkpoints, rescue + CRC" "S blind, checkpoints, coarse start, rescue + CRC" "S pilots N3x8, no checkpoints, MF per candidate, CA retry, rescue + CRC" "S pilots N3x8, checkpoints, rescue + CRC" "S pilots N3x8, checkpoints, pilot score, rescue + CRC" --seed 5703 --part rs-20 >> logs/run_rs-2.out 2>&1
