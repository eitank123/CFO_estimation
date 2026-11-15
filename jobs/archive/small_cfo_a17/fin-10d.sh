#!/bin/bash
# fin-10d: blind R = 1/10 final v2 (full neighbour join + keep 2 phases, batches of 32, grid step 4), full statistics, paired with fin-10a/b
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fin-10d.out
$PY -u blind_ber.py --points 1/10:-4:8 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 --max-frames 25000 --min-errors 25 --rx "S blind final v2" --seed 5701 --part fin-10d >> logs/run_fin-10d.out 2>&1
echo "ALL DONE" >> logs/run_fin-10d.out
