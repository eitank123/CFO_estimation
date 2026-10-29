#!/bin/bash
# ec-r2c: re-decode / FFT phase variants; v3 eco (MAC-reduced v3) vs v3 fast, paired frames (same --seed in the a/b jobs of a rate), points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8  --max-frames 50000 --min-errors 100 --rx "v3 eco, re-decode in search + CRC" "v3 eco, re-decode + CRC" "v3 eco, FFT phase + CRC" "v3 eco2 + CRC" --seed 5703 --part ec-r2c > logs/run_ec-r2c.out 2>&1
