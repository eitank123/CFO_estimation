#!/bin/bash
# srch10: search experiments R1-R3 vs baseline, R = 1/10, paired packets (seed 7701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-5:16 1/10:-4:16 --rx base10 dd win4 dd_win4 dd_k6 --max-frames 4000 --seed 7701 --part srch10
  echo "ALL DONE" ) > logs/run_srch10.out 2>&1
