#!/bin/bash
# fs-t14nn: ID 14 RETRAINED NN, paired (seed 14) with old-NN / NN-off runs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --snrs 1.4 --frames 20000 --seed 14 --part fs-t14nnp14
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --snrs 1.6 --frames 20000 --seed 14 --part fs-t14nnp16
  echo "ALL DONE" ) > logs/run_fs-t14nn.out 2>&1
