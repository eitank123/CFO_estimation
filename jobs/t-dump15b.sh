#!/bin/bash
# t-dump15b: testing/ Stage 3 dump of the baseline (paired seed 8101): 0.15:-3:16 0.15:-1:40
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results testing/results
( $PY -u testing/run.py --points 0.15:-3:16 0.15:-1:40 --rx base10 --dump --max-frames 2500 --seed 8101 --part t-dump15b
  echo "ALL DONE" ) > logs/run_t-dump15b.out 2>&1
