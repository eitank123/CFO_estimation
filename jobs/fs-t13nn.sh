#!/bin/bash
# fs-t13nn: ID 13 with its RETRAINED checkpoint NN (--cknn fmt), paired (seed 13) with the old-NN and NN-off runs at -0.8 / -0.6 / -0.4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs -0.8 --frames 5800 --seed 13 --cknn fmt --part fs-t13nnm08
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs -0.6 --frames 20000 --seed 13 --cknn fmt --part fs-t13nnm06
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id13 --snrs -0.4 --frames 20000 --seed 13 --cknn fmt --part fs-t13nnm04
  echo "ALL DONE" ) > logs/run_fs-t13nn.out 2>&1
