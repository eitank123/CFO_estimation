#!/bin/bash
# srch2: search experiments R1-R3 vs baseline, R = 1/2, paired packets (seed 7704)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/2:2:16 1/2:2.5:16 --rx base2 dd_2 win4_2 dd_win4_2 dd_k3_2 --max-frames 8000 --seed 7704 --part srch2
  echo "ALL DONE" ) > logs/run_srch2.out 2>&1
