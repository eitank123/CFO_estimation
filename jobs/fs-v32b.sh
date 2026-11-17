#!/bin/bash
# fs-v32b: VDE-SAT Link 32 ideal sync, log-MAP 8 it., -3.5, -3.0 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_vde.py --link 32 --snrs -3.5 -3.0 --frames 300000 --max-err 100 --seed 1 --workers 16 --algo logmap --iters 8 --part fs-v32b
  echo "ALL DONE" ) > logs/run_fs-v32b.out 2>&1
