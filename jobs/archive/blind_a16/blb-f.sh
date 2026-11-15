#!/bin/bash
# blb-f: blind spectral-grid receiver BLER (blind_ber.py), points rate:snr:chunks = 1/4:0:4 1/4:0.5:4 1/4:1:4 1/4:1.5:4 1/4:2:4 1/4:3:4 1/4:4:4 1/4:5:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/4:0:4 1/4:0.5:4 1/4:1:4 1/4:1.5:4 1/4:2:4 1/4:3:4 1/4:4:4 1/4:5:4 --max-frames 20000 --min-errors 100 --rx "Spectral grid + SC search + CRC" --seed 3030 --part f > logs/run_blb-f.out 2>&1
