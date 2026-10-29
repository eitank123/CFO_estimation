#!/bin/bash
# sx-f: small-CFO study, checkpoints + phase sub-offsets at every SNR (F) on the waterfall, paired with sx-b25 / sx-p25 / sx-r2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_sx-f.out
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "S blind, checkpoints, phase sub-offsets + CRC" "S pilots N3x8, checkpoints, phase sub-offsets + CRC" --seed 5702 --part sx-f1 >> logs/run_sx-f.out 2>&1
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 --max-frames 50000 --min-errors 100 --rx "S blind, checkpoints, phase sub-offsets + CRC" "S pilots N3x8, checkpoints, phase sub-offsets + CRC" --seed 5703 --part sx-f2 >> logs/run_sx-f.out 2>&1
