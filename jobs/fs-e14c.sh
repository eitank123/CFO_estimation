#!/bin/bash
# fs-e14c: blind ID 14 top of the curve: 1.0, 1.2 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.0 --frames 2000 --seed 14 --part fs-e14p10
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id14s --snrs 1.2 --frames 4000 --seed 14 --part fs-e14p12
  echo "ALL DONE" ) > logs/run_fs-e14c.out 2>&1
