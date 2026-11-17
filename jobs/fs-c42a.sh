#!/bin/bash
# fs-c42a: blind ID 42 (pi/2-BPSK): smoke 100 packets at -3.6, then points -4.2, -4.0; GA, no cap, early stops off, seed 42
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id42b --design ga --cfo-max 0.03 --snrs -3.6 --frames 100 --max-err 100 --seed 942 --workers 16 --dump --part fs-c42smoke
  $PY -u fullsys/run_blind_fs.py --fmt id42b --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -4.2 --seed 42 --part fs-c42m42
  $PY -u fullsys/run_blind_fs.py --fmt id42b --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -4.0 --seed 42 --part fs-c42m40
  echo "ALL DONE" ) > logs/run_fs-c42a.out 2>&1
