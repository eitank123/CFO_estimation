#!/bin/bash
# sm-s3: smoke of the coarse-start receiver (G): runs + MACs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --points 1/10:-5:8 2/5:0.5:8 1/2:2:8 --max-frames 150 --min-errors 100 --rx "S blind, checkpoints + CRC" "S blind, checkpoints, coarse start + CRC" "S pilots N3x8, checkpoints + CRC" "S pilots N3x8, checkpoints, coarse start + CRC" --seed 5701 --part smoke-s3 > logs/run_sm-s3.out 2>&1
