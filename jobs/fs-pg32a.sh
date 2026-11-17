#!/bin/bash
# fs-pg32a: polar GA CA-SCL-32 genie sync, ID 13 (list-32 reference for the blind curve)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_polar_genie.py --design ga --chan-intlv --list 32 --frames 300000 --max-err 100 --stop-per 1e-5 --workers 16 --fmt id13 --snrs -0.8 -0.6 -0.4 -0.2 0.0 --seed 13 --part fs-pg32-13
  echo "ALL DONE" ) > logs/run_fs-pg32a.out 2>&1
