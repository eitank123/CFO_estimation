#!/bin/bash
# blb-n: blind BLER + wall time, "4th power + SC search, then spectral grid 6 sigma + CRC", points 1/10:-5:2 1/10:-4:2 1/10:-3:4 1/10:-2:4 1/10:-1:2 1/10:0:2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-5:2 1/10:-4:2 1/10:-3:4 1/10:-2:4 1/10:-1:2 1/10:0:2 --max-frames 6250 --min-errors 100 --rx "4th power + SC search, then spectral grid 6 sigma + CRC" --seed 4105 --part n > logs/run_blb-n.out 2>&1
