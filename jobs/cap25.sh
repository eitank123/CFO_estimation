#!/bin/bash
# cap25: MAC cap 1 M per core vs uncapped, paired, 2/5 1.5 dB and 1/2 2.5 dB (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7763 --points 2/5:1.5:100 --rx base25_qfix base25_qfix_cap1 --part t-cap25
  $R --max-frames 4000 --seed 7764 --points 1/2:2.5:32 --rx base2_qfix base2_qfix_cap1 --part t-cap2
  echo "ALL DONE" ) > logs/run_cap25.out 2>&1
