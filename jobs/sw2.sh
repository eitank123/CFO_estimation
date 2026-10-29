#!/bin/bash
# sw2: small-CFO study full SNR sweep, small_rx without (C) / with (D) checkpoints, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_sw2.out
$PY -u blind_ber.py --points 1/2:1.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8 --max-frames 50000 --min-errors 100 --rx "S blind, no checkpoints, MF per candidate, CA retry + CRC" "S blind, checkpoints + CRC" "Genie (known CFO, pre-MF correction)" "S pilots N3x8, no checkpoints, MF per candidate, CA retry + CRC" "S pilots N3x8, checkpoints + CRC" --seed 5703 --part sw20 >> logs/run_sw2.out 2>&1
