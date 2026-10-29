#!/bin/bash
# blb-e: blind spectral-grid receiver BLER (blind_ber.py), points rate:snr:chunks = 1/10:-5:4 1/10:-4:4 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 1/2:2:2 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 1/2:6:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-5:4 1/10:-4:4 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 1/2:2:2 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 1/2:6:4 --max-frames 20000 --min-errors 100 --rx "Spectral grid + SC search + CRC" --seed 3030 --part e > logs/run_blb-e.out 2>&1
