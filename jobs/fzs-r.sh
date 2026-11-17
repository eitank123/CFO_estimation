#!/bin/bash
# fzs-r: F5 early stop online at 1/2 (1.5, 2 dB, 128k paired) and 1/10 (-5, -4.5 dB, 64k paired) (2026-11-15, user request; predictions in BLIND_IMPLEMENTATION/testing/results/expected_f3f5.md "F5 online at 1/10 and 1/2")
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 8221 --points 1/2:1.5:32 1/2:2:32 --rx base2_qfix base2_qfix_fzs --part t-fzs-r2
  $R --max-frames 4000 --seed 8222 --points 1/10:-5:16 1/10:-4.5:16 --rx testing_s11g testing_s11g_fzs --part t-fzs-r10
  echo "ALL DONE" ) > logs/run_fzs-r.out 2>&1
