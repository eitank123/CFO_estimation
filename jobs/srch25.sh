#!/bin/bash
# srch25: search experiments R1-R3 vs baseline, R = 2/5, paired packets (seed 7703)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 2/5:0.5:16 2/5:1:16 --rx base25 dd_25 win4_25 dd_win4_25 dd_k3_25 --max-frames 4000 --seed 7703 --part srch25
  echo "ALL DONE" ) > logs/run_srch25.out 2>&1
