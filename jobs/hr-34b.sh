#!/bin/bash
# hr-34b: high-rate blind BLER (throughput study), paired frames with its a/b twin (same --seed), points 3/4:4.5:8 3/4:5:8 3/4:5.5:8 3/4:6:8 3/4:6.5:8 3/4:7:8 3/4:7.5:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 3/4:4.5:8 3/4:5:8 3/4:5.5:8 3/4:6:8 3/4:6.5:8 3/4:7:8 3/4:7.5:8  --max-frames 50000 --min-errors 100 --rx "v3 eco, re-decode in search + CRC" "v3 eco2 + CRC" --seed 5803 --part hr-34b > logs/run_hr-34b.out 2>&1
