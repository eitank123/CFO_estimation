#!/bin/bash
# stg2: packets accepted per stage vs SNR, final blind R = 1/2, seed 7604
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 6250 --min-errors 100000 --points 1/2:2:16 1/2:2.5:16 1/2:3:16 1/2:3.5:16 1/2:4:16 1/2:5:16 --rx "S blind final 2/5, 1/2" --seed 7604 --part stg2
  echo "ALL DONE" ) > logs/run_stg2.out 2>&1
