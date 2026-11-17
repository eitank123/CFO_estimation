#!/bin/bash
# fs-nn42: ID 42 with the checkpoint NN off, paired with fs-c42m40 / fs-c42m38 (seed 42)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -4.0 --frames 20000 --seed 42 --cknn off --part fs-nn42m40
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id42b --snrs -3.8 --frames 20000 --seed 42 --cknn off --part fs-nn42m38
  echo "ALL DONE" ) > logs/run_fs-nn42.out 2>&1
