#!/bin/bash
# miss10b: per-packet MACs (per core and total) of the right decodes -> BLER vs MAC cap; final blind receiver R = 1/10, seed 7412
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 12500 --min-errors 100000 --points 1/10:-4:8 1/10:-3:8 --rx "S blind final v2" --seed 7412 --part miss-10b
  echo "ALL DONE" ) > logs/run_miss10b.out 2>&1
