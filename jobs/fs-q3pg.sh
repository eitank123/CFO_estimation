#!/bin/bash
# fs-q3pg: polar genie GA id3 L 8 then L 16, seed 3
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id3 --design ga --snrs -1.6 -1.4 -1.2 -1.0 -0.8 -0.6 -0.4 -0.2 0.0 0.2 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 3 --workers 16 --part fs-q3pg8
  $PY -u fullsys/run_polar_genie.py --fmt id3 --design ga --list 16 --snrs -1.6 -1.4 -1.2 -1.0 -0.8 -0.6 -0.4 -0.2 0.0 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 3 --workers 16 --part fs-q3pg16
  echo "ALL DONE" ) > logs/run_fs-q3pg.out 2>&1
