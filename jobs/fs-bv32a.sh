#!/bin/bash
# fs-bv32a: blind on VDE-SAT Link 32 (vde32 format; adopted 0.15 receiver, provisional): smoke 100 at -4.6 (high BLER), then -4.2, -3.8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --snrs -4.6 --frames 100 --max-err 100 --seed 932 --part fs-bv32smoke
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -4.2 --frames 20000 --seed 32 --part fs-bv32m42
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -3.8 --frames 20000 --seed 32 --part fs-bv32m38
  echo "ALL DONE" ) > logs/run_fs-bv32a.out 2>&1
