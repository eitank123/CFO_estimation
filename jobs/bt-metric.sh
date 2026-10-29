#!/bin/bash
# bt-metric: T2 decoder metrics vs CFO / phase error and ranking (3 rates), T3 sub-code capture (no interleaver)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_cfo.py metric --rate 1/10 --snrs -5 -3 -1 0 1 2 --frames 4000 --part a > logs/run_bt-metric-r10.out 2>&1
$PY -u blind_cfo.py metric --rate 1/4 --snrs -2 0 1 2 3 4 6 --frames 4000 --part a > logs/run_bt-metric-r4.out 2>&1
$PY -u blind_cfo.py metric --rate 1/2 --snrs 1 2 3 4 5 6 8 --frames 4000 --part a > logs/run_bt-metric-r2.out 2>&1
$PY -u blind_cfo.py subcode --rate 1/4 --snrs 0 2 4 6 --frames 4000 --part a > logs/run_bt-sub-r4.out 2>&1
$PY -u blind_cfo.py subcode --rate 1/2 --snrs 3 5 8 --frames 4000 --part a > logs/run_bt-sub-r2.out 2>&1
