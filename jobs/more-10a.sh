#!/bin/bash
# more-10a: more statistics for the final blind receiver (est3 comparison), seed 7101
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_more-10a.out
$PY -u blind_ber.py --max-frames 25000 --min-errors 100000 --points 1/10:-5:16 1/10:-4.5:16 --rx "S blind final v2" --seed 7101 --part more-10a >> logs/run_more-10a.out 2>&1
echo "ALL DONE" >> logs/run_more-10a.out
