#!/bin/bash
# fs-n14: DVB-RCS2 ID 14 own DA CFO estimate at its recommended low CFO range +-0.005
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --frames 300000 --max-err 100 --variant strong --top-m 3 --workers 16 --cfo-max 0.005 --wf 14 --snrs 1.29 1.49 1.69 1.89 --seed 14 --part fs-n14
  echo "ALL DONE" ) > logs/run_fs-n14.out 2>&1
