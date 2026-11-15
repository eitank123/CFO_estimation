#!/bin/bash
# e3-r25a: eco3+ (cheap fast path) blind, paired with ep-r25 / ec-r25a
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco3+ + CRC" "v3 eco3+, fast path from 0 dB + CRC" --seed 5702 --part e3-r25a > logs/run_e3-r25a.out 2>&1
