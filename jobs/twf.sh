#!/bin/bash
# twf: the adopted early-stop receivers (fzstop, adopted 2026-11-15) over the rest of the waterfall, so the 2/5 and 1/2
# blind curves and MAC counts come from base25_qfix_fzs / base2_qfix_fzs (fzs25a-d cover 2/5 0.5 dB, fzs-r 1/2 1.5, 2 dB).
# Predictions: testing/results/expected_f3f5.md "Adopted: full range" (2026-11-15).
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 2/5:0:16 2/5:1:32 2/5:1.5:32 2/5:2:16 --rx base25_qfix_fzs --seed 8231 --part t-twf25
  $R --points 1/2:2.5:32 1/2:3:16 1/2:3.5:16 --rx base2_qfix_fzs --seed 8232 --part t-twf2
  echo "ALL DONE" ) > logs/run_twf.out 2>&1
