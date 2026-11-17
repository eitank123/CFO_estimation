#!/bin/bash
# fs-c42c: blind ID 42 points -3.4, -3.2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id42b --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -3.4 --seed 42 --part fs-c42m34
  $PY -u fullsys/run_blind_fs.py --fmt id42b --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -3.2 --seed 42 --part fs-c42m32
  echo "ALL DONE" ) > logs/run_fs-c42c.out 2>&1
