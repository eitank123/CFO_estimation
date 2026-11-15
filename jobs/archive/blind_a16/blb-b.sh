#!/bin/bash
# blb-b: blind receivers BLER (blind_ber.py), points rate:snr:chunks = 1/4:4:16 1/4:5:16 1/4:6:16 1/4:8:16 1/4:10:16
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/4:4:16 1/4:5:16 1/4:6:16 1/4:8:16 1/4:10:16 --max-frames 40000 --min-errors 100 --rx "4th power + CRC (phase mod pi)" "4th power + SC search + CRC" "4th power + syndrome search + CRC" "4th power + turbo (DD) + CRC" --part b > logs/run_blb-b.out 2>&1
