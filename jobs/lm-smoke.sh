#!/bin/bash
# lm-smoke: list-marginalised SC metric (lit_polar_sync.md F3, expected_f3f5.md): rank of the true cell for L_e = 1, 2, 4, 8
# at full length and at c = 3/4 (smoke, 64 packets; lit_checks.py --check lmarg); measurement only (2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
L="$PY -u BLIND_IMPLEMENTATION/testing/lit_checks.py --check lmarg"
( $L --rate 0.15 --snr -4 --n 50 --seed 9461 --part t-lm-smoke
  echo "ALL DONE" ) > logs/run_lm-smoke.out 2>&1
