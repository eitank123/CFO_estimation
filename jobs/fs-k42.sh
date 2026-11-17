#!/bin/bash
# fs-k42: blind ID 42 calibration packets (disjoint seeds), early stops off
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --frames 4000 --max-err 4000 --calib --workers 16 --dump --fmt id42b --snrs -4.0 -3.8 --seed 42 --part fs-k42
  echo "ALL DONE" ) > logs/run_fs-k42.out 2>&1
