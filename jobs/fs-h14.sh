#!/bin/bash
# fs-h14: FINAL blind ID 14, second seed at 1.8 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 1.8 --frames 150000 --seed 7114 --part fs-h14p18
  echo "ALL DONE" ) > logs/run_fs-h14.out 2>&1
