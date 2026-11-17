#!/bin/bash
# fs-c13m08n: blind ID 13 at Es/N0 -0.8, NO MAC cap (rerun of fs-c13m08, whose 5 M cap clipped 32 packets' MACs), GA, chan intlv, seed 13, 30 errors, --dump
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.8 --frames 20000 --max-err 30 --seed 13 --cfo-max 0.03 --workers 16 --dump --part fs-c13m08n
  echo "ALL DONE" ) > logs/run_fs-c13m08n.out 2>&1
