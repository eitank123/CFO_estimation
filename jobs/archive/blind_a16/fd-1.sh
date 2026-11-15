#!/bin/bash
# fd-1 (smoke slot): classify the failures of the best blind / 24-pilot receivers at the hard points
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
( $PY -u blind/smoke/fail_diag.py --points 1/10:-5:64000 --rx "Pilots N3x8 + v3 eco7, default grid + CRC" "v3 eco7 + CRC" --out fail_diag_r10m5
  $PY -u blind/smoke/fail_diag.py --points 1/10:-4:48000 --rx "v3 eco7 + CRC" --out fail_diag_r10m4
  $PY -u blind/smoke/fail_diag.py --points 2/5:0.5:24000 2/5:1:160000 --rx "Pilots N3x8 + v3 eco6 + CRC" "v3 eco6 + CRC" --out fail_diag_r25
) > logs/run_fd-1.out 2>&1
