#!/bin/bash
# bm15a: more packets, final blind receiver R = 0.15, seed 7501
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 20000 --min-errors 100000 --points 0.15:-3:16 0.15:-2.5:16 0.15:-2:16 --rx "S blind final v2" --seed 7501 --part bm15a
  echo "ALL DONE" ) > logs/run_bm15a.out 2>&1
