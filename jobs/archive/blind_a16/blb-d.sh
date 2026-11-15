#!/bin/bash
# blb-d: blind receivers BLER (blind_ber.py), points rate:snr:chunks = 1/2:6:16 1/2:7:16 1/2:8:16 1/2:10:16
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/2:6:16 1/2:7:16 1/2:8:16 1/2:10:16 --max-frames 40000 --min-errors 100 --rx "4th power + CRC (phase mod pi)" "4th power + SC search + CRC" "4th power + syndrome search + CRC" "4th power + turbo (DD) + CRC" --part d > logs/run_blb-d.out 2>&1
