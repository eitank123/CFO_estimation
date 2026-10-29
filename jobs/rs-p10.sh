#!/bin/bash
# rs-p10: small-CFO study, the receivers with the rescue stage (final_post / fine_last) at full statistics, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_rs-p10.out
$PY -u blind_ber.py --points 1/10:-6:8 1/10:-5.5:8 1/10:-5:8 1/10:-4.5:8 --max-frames 25000 --min-errors 100 --rx "S pilots N3x8, no checkpoints, MF per candidate, CA retry, rescue + CRC" "S pilots N3x8, checkpoints, rescue + CRC" "S pilots N3x8, checkpoints, pilot score, rescue + CRC" --seed 5701 --part rs-p100 >> logs/run_rs-p10.out 2>&1
