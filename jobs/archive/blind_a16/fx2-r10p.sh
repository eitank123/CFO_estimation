#!/bin/bash
# fx2-r10p: rescue + the pilot check at 3 sigma (false passes of staircase codewords)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, pc 3 + CRC" "Pilots N3x8 + v3 eco7, rescue+, pc 3 + CRC" --seed 5701 --part fx2-r10p > logs/run_fx2-r10p.out 2>&1
