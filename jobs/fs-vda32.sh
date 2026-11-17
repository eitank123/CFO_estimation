#!/bin/bash
# fs-vda32: VDE-SAT Link 32 with its own DA CFO estimate (syncword + pilots, strong top-3), log-MAP 8 it., -5.0..-3.0 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_fullsys_da.py --sys vde --link 32 --snrs -5.0 -4.5 -4.0 -3.5 -3.0 --frames 300000 --max-err 100 --seed 1 --variant strong --top-m 3 --algo logmap --workers 16 --part fs-vda32
  echo "ALL DONE" ) > logs/run_fs-vda32.out 2>&1
