#!/bin/bash
# fs-q42pg: polar genie GA id42b (pi/2-BPSK) L 8 then L 16, seed 42, 3e5 / 100
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id42b --design ga --snrs -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 42 --workers 16 --part fs-q42pg8
  $PY -u fullsys/run_polar_genie.py --fmt id42b --design ga --list 16 --snrs -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 42 --workers 16 --part fs-q42pg16
  echo "ALL DONE" ) > logs/run_fs-q42pg.out 2>&1
