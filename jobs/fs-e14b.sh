#!/bin/bash
# fs-e14b: blind ID 14 extra packets at 2.0 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 2.0 --frames 150000 --seed 1415 --part fs-e14p20
  echo "ALL DONE" ) > logs/run_fs-e14b.out 2>&1
