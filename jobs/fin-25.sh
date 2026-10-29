#!/bin/bash
# fin-25: final receivers, full statistics, R = 2/5 0 .. 3 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fin-25.out
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 25 --rx "S blind final 2/5, 1/2" "S blind final 2/5, 1/2, best-first 32" "S pilots final 2/5, 1/2" --seed 5702 --part fin-25a >> logs/run_fin-25.out 2>&1
$PY -u blind_ber.py --points 2/5:0:4 2/5:1.5:4 2/5:2:4 2/5:2.5:4 2/5:3:4 --max-frames 25000 --min-errors 25 --rx "S blind final 2/5, 1/2" "S blind final 2/5, 1/2, best-first 32" "S pilots final 2/5, 1/2" --seed 5702 --part fin-25b >> logs/run_fin-25.out 2>&1
echo "ALL DONE" >> logs/run_fin-25.out
