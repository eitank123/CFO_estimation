#!/bin/bash
# fs-t42nn: ID 42 RETRAINED NN, paired (seed 42) with old-NN / NN-off runs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --snrs -4.0 --frames 20000 --seed 42 --part fs-t42nnm40
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --snrs -3.8 --frames 20000 --seed 42 --part fs-t42nnm38
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --snrs -3.6 --frames 20000 --seed 42 --part fs-t42nnm36
  echo "ALL DONE" ) > logs/run_fs-t42nn.out 2>&1
