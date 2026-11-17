#!/bin/bash
# fs-f14: blind ID 14 tuned (F5 0.7,0.78) at 2.2 dB, 1e-5 region
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 2.2 --frames 500000 --seed 1450 --fzstop 0.7,0.78 --part fs-f14p22
  echo "ALL DONE" ) > logs/run_fs-f14.out 2>&1
