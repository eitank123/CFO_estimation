#!/bin/bash
# fin-10b: final receivers, full statistics, R = 1/10 -4 .. 0 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fin-10b.out
$PY -u blind_ber.py --points 1/10:-4:8 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 --max-frames 25000 --min-errors 25 --rx "S blind final" "S pilots final" --seed 5701 --part fin-10b >> logs/run_fin-10b.out 2>&1
echo "ALL DONE" >> logs/run_fin-10b.out
