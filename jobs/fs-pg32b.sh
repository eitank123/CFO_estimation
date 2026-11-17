#!/bin/bash
# fs-pg32b: polar GA CA-SCL-32 genie sync, ID 42
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_polar_genie.py --design ga --chan-intlv --list 32 --frames 300000 --max-err 100 --stop-per 1e-5 --workers 16 --fmt id42b --snrs -4.0 -3.8 -3.6 -3.4 -3.2 --seed 42 --part fs-pg32-42b
  echo "ALL DONE" ) > logs/run_fs-pg32b.out 2>&1
