#!/bin/bash
# blb-o: blind BLER + wall time, "Spectral grid 6 sigma + SC search + CRC" "4th power + SC search, then spectral grid 6 sigma + CRC", points 1/4:0:4 1/4:0.5:2 1/4:1:4 1/4:1.5:2 1/4:2:4 1/4:3:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/4:0:4 1/4:0.5:2 1/4:1:4 1/4:1.5:2 1/4:2:4 1/4:3:4 --max-frames 6250 --min-errors 100 --rx "Spectral grid 6 sigma + SC search + CRC" "4th power + SC search, then spectral grid 6 sigma + CRC" --seed 4106 --part o > logs/run_blb-o.out 2>&1
