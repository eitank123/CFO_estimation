#!/bin/bash
# fd-4 (smoke slot): is the coded QPSK packet closed under a pi/2 rotation; staircase test of the false passes
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
( $PY -u blind/smoke/rot_test.py
  $PY -u blind/smoke/fail_diag.py --points 2/5:1:240000 --rx "v3 eco6 + CRC" --out fail_diag_fp25c ) > logs/run_fd-4.out 2>&1
