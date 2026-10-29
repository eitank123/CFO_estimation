#!/bin/bash
# sx-p25: small-CFO study (|f| <= 0.03), small_rx variants without / with checkpoints, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "S pilots N3x8, no checkpoints + CRC" "S pilots N3x8, no checkpoints, MF per candidate + CRC" "S pilots N3x8, no checkpoints, MF per candidate, CA retry + CRC" "S pilots N3x8, checkpoints + CRC" "S pilots N3x8, checkpoints, shortlist + CRC" --seed 5702 --part sx-p25 > logs/run_sx-p25.out 2>&1
