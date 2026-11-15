#!/bin/bash
# nf10b: S1 R = 1/10 -3, -1, 0 dB: base10 vs nofast (seed 7701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-3:16 1/10:-1:16 1/10:0:16 --rx base10 nofast --max-frames 4000 --seed 7701 --part nf10b
  echo "ALL DONE" ) > logs/run_nf10b.out 2>&1
