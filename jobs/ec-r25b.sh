#!/bin/bash
# ec-r25b: v3 eco (MAC-reduced v3) vs v3 fast, paired frames (same --seed in the a/b jobs of a rate), points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8  --max-frames 50000 --min-errors 100 --rx "v3 eco, 8-SPS statistics + CRC" "v3 eco, no adaptive / abort + CRC" --seed 5702 --part ec-r25b > logs/run_ec-r25b.out 2>&1
