#!/bin/bash
# nf10a: S1/S2 R = 1/10 -5, -4 dB: base10 vs nofast vs nofast_spec, paired with srch10 (seed 7701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-5:16 1/10:-4:16 --rx base10 nofast nofast_spec --max-frames 4000 --seed 7701 --part nf10a
  echo "ALL DONE" ) > logs/run_nf10a.out 2>&1
