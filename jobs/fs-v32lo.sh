#!/bin/bash
# fs-v32lo: VDE Link 32 ideal sync, waterfall below -5 dB (user exception for VDE)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_vde.py --link 32 --snrs -7.0 -6.5 -6.0 -5.5 --frames 100000 --max-err 100 --seed 1 --workers 16 --algo logmap --iters 8 --part fs-v32lo
  echo "ALL DONE" ) > logs/run_fs-v32lo.out 2>&1
