#!/bin/bash
# nf-smoke: smoke: S experiments (nofast, nofast_spec, nph15, nofast_nph4, noise-only)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-5:1 --rx base10 nofast nofast_spec --max-frames 64 --seed 7899 --part nf-smoke-a
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-1:1 --rx base10 nph15 nofast_nph4 --max-frames 64 --seed 7899 --part nf-smoke-b
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-1:1 --rx base10 nph15 --max-frames 8 --noise-only --seed 7899 --part nf-smoke-c
  echo "ALL DONE" ) > logs/run_nf-smoke.out 2>&1
