#!/bin/bash
# x-smoke: smoke: MAC cap, gate+spec11, phase noise, capped noise-only, new dump points (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 25 --seed 7900 --points 0.15:-3.5:4 --rx nofast15_qfix nofast15_qfix_cap2 nofast15_qfix_nnb1_spec11 --part t-x-smoke-a
  $R --max-frames 25 --seed 7901 --points 2/5:0.5:4 --rx base25_qfix base25_qfix_cap1 --part t-x-smoke-b
  $R --max-frames 25 --seed 7902 --points 1/2:1.5:4 --rx base2_qfix base2_qfix_cap1 --part t-x-smoke-c
  BLIND_PN=3e-4 $R --max-frames 25 --seed 7903 --points 0.15:-4:4 --rx nofast15_qfix --part t-x-smoke-d
  $R --max-frames 25 --seed 7904 --noise-only --points 0.15:-2.5:2 --rx nofast15_qfix_cap2 --part t-x-smoke-e
  $R --max-frames 25 --seed 7905 --points 2/5:1:2 --rx base25_qfix_dump --part t-x-smoke-f
  echo "ALL DONE" ) > logs/run_x-smoke.out 2>&1
