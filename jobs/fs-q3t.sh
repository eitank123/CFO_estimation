#!/bin/bash
# fs-q3t: DVB-RCS2 ID 3 fast: ideal then own DA (strong) +-0.03, seed 3
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 3 --snrs -1.27 -1.07 -0.87 -0.67 -0.47 -0.27 -0.07 0.13 --frames 300000 --max-err 100 --seed 3 --workers 16 --part fs-q3ti
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 3 --snrs -1.07 -0.87 -0.67 -0.47 -0.27 -0.07 0.13 --frames 300000 --max-err 100 --seed 3 --variant strong --top-m 3 --workers 16 --part fs-q3td
  echo "ALL DONE" ) > logs/run_fs-q3t.out 2>&1
