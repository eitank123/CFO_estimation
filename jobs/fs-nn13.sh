#!/bin/bash
# fs-nn13: ID 13 with the checkpoint NN off: paired with fs-c13m06 / fs-c13m04
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs -0.6 --frames 20000 --seed 13 --cknn off --part fs-nn13m06
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs -0.4 --frames 20000 --seed 13 --cknn off --part fs-nn13m04
  echo "ALL DONE" ) > logs/run_fs-nn13.out 2>&1
