#!/bin/bash
# sm-s4: smoke of the pilot-score receiver (H) and the chunked checkpoints: runs + MACs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --points 1/10:-6:8 1/10:-5:8 2/5:0.5:8 1/2:2:8 --max-frames 150 --min-errors 100 --rx "S pilots N3x8, checkpoints + CRC" "S pilots N3x8, checkpoints, pilot score + CRC" --seed 5701 --part smoke-s4 > logs/run_sm-s4.out 2>&1
