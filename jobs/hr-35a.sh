#!/bin/bash
# hr-35a: high-rate blind BLER (throughput study), paired frames with its a/b twin (same --seed), points 3/5:3:8 3/5:3.5:8 3/5:4:8 3/5:4.5:8 3/5:5:8 3/5:5.5:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 3/5:3:8 3/5:3.5:8 3/5:4:8 3/5:4.5:8 3/5:5:8 3/5:5.5:8  --max-frames 50000 --min-errors 100 --rx "Best-first search v3 fast + CRC" "v3 eco + CRC" "Genie (known CFO, pre-MF correction)" --seed 5801 --part hr-35a > logs/run_hr-35a.out 2>&1
