#!/bin/bash
# fs-n3: DVB-RCS2 ID 3 own DA CFO estimate at its recommended low CFO range +-0.005
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --frames 300000 --max-err 100 --variant strong --top-m 3 --workers 16 --cfo-max 0.005 --wf 3 --snrs -0.87 -0.67 -0.47 -0.27 -0.07 0.13 --seed 3 --part fs-n3
  echo "ALL DONE" ) > logs/run_fs-n3.out 2>&1
