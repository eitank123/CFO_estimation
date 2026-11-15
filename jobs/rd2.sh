#!/bin/bash
# rd2: Stage 3 refinement diagnostic (ref_diag, log-only; base + _rd on the same packets), R = 2/5 0.5 dB, 1/2 2 dB, 8k packets per point (2026-11-15, expected_ref.md D0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 500 --seed 8013 --points 2/5:0.5:16 --rx base25_qfix base25_qfix_rd --part t-rd2a
  $R --max-frames 500 --seed 8013 --points 1/2:2:16 --rx base2_qfix base2_qfix_rd --part t-rd2b
  echo "ALL DONE" ) > logs/run_rd2.out 2>&1
