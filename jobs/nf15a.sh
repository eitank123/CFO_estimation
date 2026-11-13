#!/bin/bash
# nf15a: S1/S2 R = 0.15 -4 dB: base10 vs nofast vs nofast_spec, paired with srch15 (seed 7702)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-4:16 --rx base10 nofast nofast_spec --max-frames 4000 --seed 7702 --part nf15a
  echo "ALL DONE" ) > logs/run_nf15a.out 2>&1
