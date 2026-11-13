#!/bin/bash
# t-dump15a: testing/ Stage 3 dump of the baseline (paired seed 8101): 0.15:-4:20 0.15:-3:24
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results testing/results
( $PY -u testing/run.py --points 0.15:-4:20 0.15:-3:24 --rx base10 --dump --max-frames 2500 --seed 8101 --part t-dump15a
  echo "ALL DONE" ) > logs/run_t-dump15a.out 2>&1
