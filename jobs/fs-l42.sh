#!/bin/bash
# fs-l42: live check of the tuned F5 stop for ID 42 (q 0.9, t 0.75; tune_k42), fresh seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -4.0 --frames 20000 --seed 4290 --fzstop 0.9,0.75 --part fs-l42m40
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -3.8 --frames 40000 --seed 4291 --fzstop 0.9,0.75 --part fs-l42m38
  echo "ALL DONE" ) > logs/run_fs-l42.out 2>&1
