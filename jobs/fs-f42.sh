#!/bin/bash
# fs-f42: blind ID 42 tuned (F5 0.9,0.75) at -3.0 dB, 1e-5 region
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -3.0 --frames 400000 --seed 4250 --fzstop 0.9,0.75 --part fs-f42m30
  echo "ALL DONE" ) > logs/run_fs-f42.out 2>&1
