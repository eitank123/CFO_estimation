#!/bin/bash
# sw25b: small-CFO study full SNR sweep, small_rx without (C) / with (D) checkpoints, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_sw25b.out
$PY -u blind_ber.py --points 2/5:0:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 --max-frames 50000 --min-errors 100 --rx "S blind, no checkpoints, MF per candidate, CA retry + CRC" "S blind, checkpoints + CRC" "Genie (known CFO, pre-MF correction)" --seed 5702 --part sw25b0 >> logs/run_sw25b.out 2>&1
