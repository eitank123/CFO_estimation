#!/bin/bash
# fs-bv32la: blind VDE Link 32 waterfall: -6.6, -6.2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -6.6 --frames 2000 --seed 32 --part fs-bv32m66
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --snrs -6.2 --frames 4000 --seed 32 --part fs-bv32m62
  echo "ALL DONE" ) > logs/run_fs-bv32la.out 2>&1
