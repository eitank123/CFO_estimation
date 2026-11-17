#!/bin/bash
# fs-q13da: FAST ID 13 first plot: DVB-RCS2 with its DA CFO estimate (strong; standard derived), CFO U(+-0.03), seed 13, 3e5 frames / 100 errors
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 13 --snrs -1.20 -1.00 -0.80 -0.60 -0.40 --frames 300000 --max-err 100 --seed 13 --variant strong --top-m 3 --workers 16 --part fs-q13da
  echo "ALL DONE" ) > logs/run_fs-q13da.out 2>&1
