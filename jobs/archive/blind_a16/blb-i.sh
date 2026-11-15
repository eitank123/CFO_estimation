#!/bin/bash
# blb-i: the combined blind receiver (4th-power SC search S0..S2, then the spectral grid)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-5:2 1/10:-4:2 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 1/4:0:4 1/4:1:4 1/4:2:4 1/4:3:4 1/4:4:4 1/2:2:2 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 --max-frames 20000 --min-errors 100 --rx "4th power + SC search, then spectral grid + CRC" --seed 6060 --part i > logs/run_blb-i.out 2>&1
