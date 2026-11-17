#!/bin/bash
# fs-nn13b: ID 13 NN off at -0.8 dB, paired with fs-c13m08n
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs -0.8 --frames 5800 --seed 13 --cknn off --part fs-nn13m08
  echo "ALL DONE" ) > logs/run_fs-nn13b.out 2>&1
