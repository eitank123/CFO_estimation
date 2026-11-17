#!/bin/bash
# fs-c3a: blind ID 3: smoke 100 at -0.6, then -1.0, -0.8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id3 --design ga --cfo-max 0.03 --snrs -0.6 --frames 100 --max-err 100 --seed 903 --workers 16 --dump --part fs-c3smoke
  $PY -u fullsys/run_blind_fs.py --fmt id3 --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -1.0 --seed 3 --part fs-c3m10
  $PY -u fullsys/run_blind_fs.py --fmt id3 --design ga --cfo-max 0.03 --frames 20000 --max-err 30 --workers 16 --dump --snrs -0.8 --seed 3 --part fs-c3m08
  echo "ALL DONE" ) > logs/run_fs-c3a.out 2>&1
