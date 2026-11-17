#!/bin/bash
# fs-bv32e: blind VDE Link 32 at -3.8 dB (1e-5 region)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -3.8 --frames 200000 --seed 3232 --part fs-bv32m38b
  echo "ALL DONE" ) > logs/run_fs-bv32e.out 2>&1
