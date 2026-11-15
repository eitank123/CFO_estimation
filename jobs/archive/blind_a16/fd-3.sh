#!/bin/bash
# fd-3 (smoke slot): what are the false CRC passes (relation of the decoded packet to the transmitted one)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
$PY -u blind/smoke/fail_diag.py --points 2/5:1:240000 --rx "v3 eco6 + CRC" "Pilots N3x8 + v3 eco6 + CRC" --out fail_diag_fp25b > logs/run_fd-3.out 2>&1
