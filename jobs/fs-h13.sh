#!/bin/bash
# fs-h13: FINAL blind ID 13, second seed at -0.6 dB (more errors)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id13 --fzstop 0.6,0.80 --snrs -0.6 --frames 50000 --seed 7113 --part fs-h13m06
  echo "ALL DONE" ) > logs/run_fs-h13.out 2>&1
