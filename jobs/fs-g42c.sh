#!/bin/bash
# fs-g42c: FINAL blind ID 42 at -3.0 dB (1e-5 region)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.0 --frames 400000 --seed 7042 --part fs-g42m30
  echo "ALL DONE" ) > logs/run_fs-g42c.out 2>&1
