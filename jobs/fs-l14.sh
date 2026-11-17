#!/bin/bash
# fs-l14: live check of the tuned F5 stop for ID 14 (q 0.7, t 0.78; tune_k14), fresh seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.4 --frames 20000 --seed 1490 --fzstop 0.7,0.78 --part fs-l14p14
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.6 --frames 40000 --seed 1491 --fzstop 0.7,0.78 --part fs-l14p16
  echo "ALL DONE" ) > logs/run_fs-l14.out 2>&1
