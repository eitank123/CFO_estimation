#!/bin/bash
# ec-r10b: v3 eco (MAC-reduced v3) vs v3 fast, paired frames (same --seed in the a/b jobs of a rate), points 1/10:-5:8 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8  --max-frames 50000 --min-errors 100 --rx "v3 eco, 8-SPS statistics + CRC" "v3 eco, grid step 6 + CRC" --seed 5701 --part ec-r10b > logs/run_ec-r10b.out 2>&1
