#!/bin/bash
# fs-rmsmoke: polar rate-matching smoke (verifier item 3c): ID 14 shorten, shortened LLR +BIG / 0 / -BIG, paired, McNemar
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/smoke_polar_rm.py --part fs-rmsmoke --packets 300 --seed 1 --snr 0.5 1.0 1.5
  echo "ALL DONE" ) > logs/run_fs-rmsmoke.out 2>&1
