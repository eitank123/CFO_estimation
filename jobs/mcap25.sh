#!/bin/bash
# cap-25: MAC histogram of the right decodes (cost of a hard MAC cap), final blind receiver R = 2/5, seed 7105
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --max-frames 12500 --min-errors 100000 --points 2/5:0.5:8 2/5:1:16 --rx "S blind final 2/5, 1/2, best-first 32" --seed 7105 --part cap-25 > logs/run_cap-25.out 2>&1
echo "ALL DONE" >> logs/run_cap-25.out
