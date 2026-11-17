#!/bin/bash
# fs-n13: DVB-RCS2 ID 13 own DA CFO estimate at its recommended low CFO range +-0.005
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --frames 300000 --max-err 100 --variant strong --top-m 3 --workers 16 --cfo-max 0.005 --wf 13 --snrs -1.0 -0.8 -0.6 -0.4 --seed 13 --part fs-n13
  echo "ALL DONE" ) > logs/run_fs-n13.out 2>&1
