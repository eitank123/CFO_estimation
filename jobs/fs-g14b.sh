#!/bin/bash
# fs-g14b: FINAL blind ID 14: 2.0, 2.2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 2.0 --frames 200000 --seed 7014 --part fs-g14p20
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 2.2 --frames 300000 --seed 7014 --part fs-g14p22
  echo "ALL DONE" ) > logs/run_fs-g14b.out 2>&1
