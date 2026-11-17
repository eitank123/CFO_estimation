#!/bin/bash
# fs-kv32: blind VDE Link 32 calibration packets (disjoint seeds), early stops off: -5.6, -5.0, -4.4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --calib --frames 4000 --max-err 4000 --snrs -5.6 -5.0 -4.4 --seed 32 --part fs-kv32
  echo "ALL DONE" ) > logs/run_fs-kv32.out 2>&1
