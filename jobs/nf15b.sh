#!/bin/bash
# nf15b: S1/S2 R = 0.15 -3 dB (base10, nofast, nofast_spec) and -1 / 0 dB (nph4 vs nofast_nph4), seed 7702
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-3:16 --rx base10 nofast nofast_spec --max-frames 4000 --seed 7702 --part nf15b
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-1:16 0.15:0:16 --rx nph4 nofast_nph4 --max-frames 4000 --seed 7702 --part nf15c
  echo "ALL DONE" ) > logs/run_nf15b.out 2>&1
