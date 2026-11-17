#!/bin/bash
# fs-d42a: blind ID 42 extra packets at -3.4 (1e-4 region), new seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -3.4 --frames 100000 --seed 4242 --part fs-d42m34
  echo "ALL DONE" ) > logs/run_fs-d42a.out 2>&1
