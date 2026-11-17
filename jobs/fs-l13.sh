#!/bin/bash
# fs-l13: live confirmation of the offline-tuned F5 stop (q 0.6, t 0.80; tune_k13 + replay) on fresh seeds, ID 13
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.6 --frames 20000 --max-err 30 --seed 1306 --cfo-max 0.03 --workers 16 --dump --fzstop 0.6,0.80 --part fs-l13m06
  $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.4 --frames 20000 --max-err 30 --seed 1304 --cfo-max 0.03 --workers 16 --dump --fzstop 0.6,0.80 --part fs-l13m04
  echo "ALL DONE" ) > logs/run_fs-l13.out 2>&1
