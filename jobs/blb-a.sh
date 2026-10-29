#!/bin/bash
# blb-a: blind receivers BLER (blind_ber.py), points rate:snr:chunks = 1/4:0:2 1/4:1:2 1/4:2:4 1/4:3:8 1/10:-2:2 1/10:0:2 1/10:2:4 1/10:4:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/4:0:2 1/4:1:2 1/4:2:4 1/4:3:8 1/10:-2:2 1/10:0:2 1/10:2:4 1/10:4:8 --max-frames 40000 --min-errors 100 --rx "4th power + CRC (phase mod pi)" "4th power + SC search + CRC" "4th power + syndrome search + CRC" "4th power + turbo (DD) + CRC" --part a > logs/run_blb-a.out 2>&1
