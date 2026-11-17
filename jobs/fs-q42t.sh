#!/bin/bash
# fs-q42t: DVB-RCS2 ID 42 fast: ideal sync then own DA CFO estimate (strong) at +-0.03, seed 42, 3e5 frames / 100 errors
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 42 --snrs -4.41 -4.21 -4.01 -3.81 -3.61 -3.41 -3.21 --frames 300000 --max-err 100 --seed 42 --workers 16 --part fs-q42ti
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 42 --snrs -4.41 -4.21 -4.01 -3.81 -3.61 -3.41 --frames 300000 --max-err 100 --seed 42 --variant strong --top-m 3 --workers 16 --part fs-q42td
  echo "ALL DONE" ) > logs/run_fs-q42t.out 2>&1
