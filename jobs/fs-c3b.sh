#!/bin/bash
# fs-c3b: blind ID 3 points -0.6, -0.4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id3 --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -0.6 --seed 3 --part fs-c3m06
  $PY -u fullsys/run_blind_fs.py --fmt id3 --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -0.4 --seed 3 --part fs-c3m04
  echo "ALL DONE" ) > logs/run_fs-c3b.out 2>&1
