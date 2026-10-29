#!/bin/bash
# ec-r10c: re-decode / FFT phase variants; v3 eco (MAC-reduced v3) vs v3 fast, paired frames (same --seed in the a/b jobs of a rate), points 1/10:-5:8 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8  --max-frames 50000 --min-errors 100 --rx "v3 eco, re-decode in search + CRC" "v3 eco, re-decode + CRC" "v3 eco, FFT phase + CRC" "v3 eco2 + CRC" --seed 5701 --part ec-r10c > logs/run_ec-r10c.out 2>&1
