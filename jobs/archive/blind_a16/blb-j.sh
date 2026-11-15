#!/bin/bash
# blb-j: blind BLER + wall time, "Spectral grid 6 sigma + SC search + CRC", points 1/10:-5:4 1/10:-4:12
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-5:4 1/10:-4:12 --max-frames 6250 --min-errors 100 --rx "Spectral grid 6 sigma + SC search + CRC" --seed 4101 --part j > logs/run_blb-j.out 2>&1
