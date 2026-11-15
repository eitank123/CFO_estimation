#!/bin/bash
# srch-smoke2: smoke: search experiments R1-R3 at R = 2/5 and 1/2 (joint list decode), paired
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 2/5:0.5:1 --rx base25 dd_25 win4_25 dd_win4_25 dd_k3_25 --max-frames 64 --seed 7798 --part srch-smoke2a
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/2:2:1 --rx base2 dd_2 win4_2 dd_win4_2 dd_k3_2 --max-frames 64 --seed 7798 --part srch-smoke2b
  echo "ALL DONE" ) > logs/run_srch-smoke2.out 2>&1
