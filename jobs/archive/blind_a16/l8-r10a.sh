#!/bin/bash
# l8-r10a: eco8 candidates, blind R = 1/10: screening from round 1 / at -4 dB with z 1.0 (paired with i5/j6/k7-r10)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, screen from round 1 + CRC" "v3 eco7, screen -4 dB z 1.0 + CRC" --seed 5701 --part l8-r10a > logs/run_l8-r10a.out 2>&1
