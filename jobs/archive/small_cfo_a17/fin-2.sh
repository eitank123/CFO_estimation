#!/bin/bash
# fin-2: final receivers, full statistics, R = 1/2 1.5 .. 5 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fin-2.out
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 --max-frames 50000 --min-errors 25 --rx "S blind final 2/5, 1/2" "S pilots final 2/5, 1/2" --seed 5703 --part fin-2a >> logs/run_fin-2.out 2>&1
$PY -u blind_ber.py --points 1/2:1.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 --max-frames 25000 --min-errors 25 --rx "S blind final 2/5, 1/2" "S pilots final 2/5, 1/2" --seed 5703 --part fin-2b >> logs/run_fin-2.out 2>&1
echo "ALL DONE" >> logs/run_fin-2.out
