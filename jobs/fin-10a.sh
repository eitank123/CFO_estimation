#!/bin/bash
# fin-10a: final receivers, full statistics, R = 1/10 -5 / -4.5 dB (paired with rs / jt seeds)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fin-10a.out
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4.5:8 --max-frames 25000 --min-errors 25 --rx "S blind final" "S pilots final" --seed 5701 --part fin-10a >> logs/run_fin-10a.out 2>&1
echo "ALL DONE" >> logs/run_fin-10a.out
