#!/bin/bash
# eq-smoke: smoke of the phase-equivariant receiver (equiv) vs the same receiver without it (2026-11-13; BLIND_NOINT=1: no bit interleaver in every arm)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_NOINT=1
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 25 --seed 7910 --points 0.15:-4.5:4 1/10:-5.5:4 --rx nofast15_qfix nofast15_qfix_eq --part t-eq-smoke-a
  $R --max-frames 25 --seed 7911 --points 2/5:0:4 --rx base25_qfix base25_qfix_eq --part t-eq-smoke-b
  $R --max-frames 25 --seed 7912 --points 1/2:1.5:4 --rx base2_qfix base2_qfix_eq --part t-eq-smoke-c
  echo "ALL DONE" ) > logs/run_eq-smoke.out 2>&1
