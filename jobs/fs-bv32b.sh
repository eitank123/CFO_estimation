#!/bin/bash
# fs-bv32b: blind VDE Link 32 at -5.0 and -4.8 dB (lowest allowed SNR)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -5.0 --frames 20000 --seed 32 --part fs-bv32m50
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -4.8 --frames 20000 --seed 32 --part fs-bv32m48
  echo "ALL DONE" ) > logs/run_fs-bv32b.out 2>&1
