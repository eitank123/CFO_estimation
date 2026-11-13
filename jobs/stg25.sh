#!/bin/bash
# stg25: packets accepted per stage vs SNR, final blind R = 2/5, seed 7603
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 6250 --min-errors 100000 --points 2/5:0.5:16 2/5:1:16 2/5:1.5:16 2/5:2:16 2/5:2.5:16 2/5:3:16 --rx "S blind final 2/5, 1/2, best-first 32" --seed 7603 --part stg25
  echo "ALL DONE" ) > logs/run_stg25.out 2>&1
