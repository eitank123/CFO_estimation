#!/bin/bash
# fs-c14a: blind ID 14 (id14s): smoke 100 at 1.4 (high BLER), then 1.4, 1.6
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(   $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.4 --frames 100 --max-err 100 --seed 914 --part fs-c14smoke
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.4 --frames 20000 --seed 14 --part fs-c14p14
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.6 --frames 20000 --seed 14 --part fs-c14p16
  echo "ALL DONE" ) > logs/run_fs-c14a.out 2>&1
