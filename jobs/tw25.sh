#!/bin/bash
# tw25: base25_qfix 2/5 at 0, 1.5, 2 dB and base2_qfix 1/2 at 1.5, 3, 3.5 dB (the SNRs the testing model never ran) (2026-11-15; testing model over the full SNR range, user request)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 2/5:0:16 2/5:1.5:64 2/5:2:32 --rx base25_qfix --seed 8205 --part t-tw25
  $R --points 1/2:1.5:16 1/2:3:32 1/2:3.5:32 --rx base2_qfix --seed 8206 --part t-tw2
  echo "ALL DONE" ) > logs/run_tw25.out 2>&1
