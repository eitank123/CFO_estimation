#!/bin/bash
# fs-nn42b: ID 42 NN off at -3.6 dB, paired with fs-c42m36
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -3.6 --frames 20000 --seed 42 --cknn off --part fs-nn42m36
  echo "ALL DONE" ) > logs/run_fs-nn42b.out 2>&1
