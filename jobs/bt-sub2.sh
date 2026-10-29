#!/bin/bash
# bt-sub2: T3 sub-code test again, now with the mean SC metric vs CFO offset (basin width) up to 128 grid steps
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs
$PY -u blind_cfo.py subcode --rate 1/4 --snrs 0 2 4 6 --frames 4000 --part b > logs/run_bt-sub2-r4.out 2>&1
$PY -u blind_cfo.py subcode --rate 1/2 --snrs 3 5 8 --frames 4000 --part b > logs/run_bt-sub2-r2.out 2>&1
