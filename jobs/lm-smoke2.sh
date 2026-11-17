#!/bin/bash
# lm-smoke2: the lm-smoke run again after FastSCL moved to fastscl.py (same --seed 9461 --n 50, part t-lm-smoke2): L = 2/4/8 ranks and gaps must equal lit_t-lm-smoke.json per packet; L = 1 may differ at near-ties (new FastSC REP tie rule), viol_full no worse (2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
L="$PY -u BLIND_IMPLEMENTATION/testing/lit_checks.py --check lmarg"
( $L --rate 0.15 --snr -4 --n 50 --seed 9461 --part t-lm-smoke2
  echo "ALL DONE" ) > logs/run_lm-smoke2.out 2>&1
