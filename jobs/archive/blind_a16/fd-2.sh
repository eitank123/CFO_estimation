#!/bin/bash
# fd-2 (smoke slot): the false CRC passes: rho, stage, code-aided, at the points where they are frequent
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
( $PY -u blind/smoke/fail_diag.py --points 2/5:1:240000 --rx "Pilots N3x8 + v3 eco6 + CRC" "v3 eco6 + CRC" --out fail_diag_fp25
  $PY -u blind/smoke/fail_diag.py --points 1/10:-5:64000 --rx "v3 eco7 + CRC" --out fail_diag_fp10
) > logs/run_fd-2.out 2>&1
