#!/bin/bash
# blb-l: blind BLER + wall time, "Spectral grid 6 sigma + SC search + CRC", points 1/10:-2:16
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-2:16 --max-frames 6250 --min-errors 100 --rx "Spectral grid 6 sigma + SC search + CRC" --seed 4103 --part l > logs/run_blb-l.out 2>&1
