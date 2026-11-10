#!/bin/bash
# more-10b: more statistics for the final blind receiver (est3 comparison), seed 7102
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_more-10b.out
$PY -u blind_ber.py --max-frames 25000 --min-errors 100000 --points 1/10:-4:16 1/10:-3:16 --rx "S blind final v2" --seed 7102 --part more-10b >> logs/run_more-10b.out 2>&1
echo "ALL DONE" >> logs/run_more-10b.out
