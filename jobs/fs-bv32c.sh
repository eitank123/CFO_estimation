#!/bin/bash
# fs-bv32c: blind VDE Link 32 at -4.4 and -4.0 dB (low-BLER end)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -4.4 --frames 60000 --seed 32 --part fs-bv32m44
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -4.0 --frames 100000 --seed 32 --part fs-bv32m40
  echo "ALL DONE" ) > logs/run_fs-bv32c.out 2>&1
