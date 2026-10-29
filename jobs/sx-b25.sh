#!/bin/bash
# sx-b25: small-CFO study (|f| <= 0.03), small_rx variants without / with checkpoints, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "S blind, no checkpoints + CRC" "S blind, no checkpoints, MF per candidate + CRC" "S blind, no checkpoints, MF per candidate, CA retry + CRC" "S blind, checkpoints + CRC" "S blind, checkpoints, shortlist + CRC" "Genie (known CFO, pre-MF correction)" --seed 5702 --part sx-b25 > logs/run_sx-b25.out 2>&1
