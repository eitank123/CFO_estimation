#!/bin/bash
# f7-r2: fast path with the peak chosen among the near-highest 4th-power peaks (24 pilots / blind metric), paired with e3-* / ep-* / pe-*
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco3+, fast path from 0 dB, 16 peaks >= 0.7 + CRC" "v3 eco3+, fast path from 0 dB, 4 peaks >= 0.85 + CRC" --seed 5703 --part f7-r2 > logs/run_f7-r2.out 2>&1
