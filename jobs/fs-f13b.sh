#!/bin/bash
# fs-f13b: blind ID 13 tuned at 0.0 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs 0.0 --frames 80000 --seed 1321 --fzstop 0.6,0.80 --part fs-f13p00
  echo "ALL DONE" ) > logs/run_fs-f13b.out 2>&1
