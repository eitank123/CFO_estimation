#!/bin/bash
# more-hi: more statistics for the final blind receivers at R = 2/5 and 1/2 (est3 comparison), seed 7104
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_more-hi.out
$PY -u blind_ber.py --max-frames 25000 --min-errors 100000 --points 2/5:0.5:8 2/5:1:16 2/5:1.5:16 2/5:2:16 2/5:2.5:16 2/5:3:16 --rx "S blind final 2/5, 1/2, best-first 32" --seed 7104 --part more-25 >> logs/run_more-hi.out 2>&1
$PY -u blind_ber.py --max-frames 25000 --min-errors 100000 --points 1/2:1.5:2 1/2:2:16 1/2:2.5:16 1/2:3:16 1/2:3.5:16 1/2:4:16 1/2:5:16 --rx "S blind final 2/5, 1/2" --seed 7104 --part more-2 >> logs/run_more-hi.out 2>&1
echo "ALL DONE" >> logs/run_more-hi.out
