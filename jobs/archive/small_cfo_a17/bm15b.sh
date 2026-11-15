#!/bin/bash
# bm15b: more packets, final blind receiver R = 0.15, seed 7502
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 20000 --min-errors 100000 --points 0.15:-1:16 0.15:0:16 0.15:1:16 --rx "S blind final v2" --seed 7502 --part bm15b
  echo "ALL DONE" ) > logs/run_bm15b.out 2>&1
