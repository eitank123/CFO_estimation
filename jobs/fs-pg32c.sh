#!/bin/bash
# fs-pg32c: polar GA CA-SCL-32 genie sync, ID 3 and ID 14
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_polar_genie.py --design ga --chan-intlv --list 32 --frames 300000 --max-err 100 --stop-per 1e-5 --workers 16 --fmt id3 --snrs -0.4 -0.2 0.0 0.2 0.4 0.6 --seed 3 --part fs-pg32-3
  $PY -u fullsys/run_polar_genie.py --design ga --chan-intlv --list 32 --frames 300000 --max-err 100 --stop-per 1e-5 --workers 16 --fmt id14s --snrs 1.4 1.6 1.8 2.0 --seed 14 --part fs-pg32-14s
  echo "ALL DONE" ) > logs/run_fs-pg32c.out 2>&1
