#!/bin/bash
# stg10: packets accepted per stage vs SNR, final blind R = 1/10, seed 7601
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 2500 --min-errors 100000 --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 1/10:-3:16 1/10:-2:16 1/10:-1:16 1/10:0:16 --rx "S blind final v2" --seed 7601 --part stg10
  echo "ALL DONE" ) > logs/run_stg10.out 2>&1
