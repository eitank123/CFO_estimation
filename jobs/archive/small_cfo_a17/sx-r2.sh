#!/bin/bash
# sx-r2: small-CFO study (|f| <= 0.03), small_rx variants without / with checkpoints, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 --max-frames 50000 --min-errors 100 --rx "S blind, no checkpoints, MF per candidate, CA retry + CRC" "S blind, checkpoints + CRC" "S blind, checkpoints, shortlist + CRC" "S pilots N3x8, no checkpoints, MF per candidate, CA retry + CRC" "S pilots N3x8, checkpoints + CRC" "S pilots N3x8, checkpoints, shortlist + CRC" "Genie (known CFO, pre-MF correction)" --seed 5703 --part sx-r2 > logs/run_sx-r2.out 2>&1
