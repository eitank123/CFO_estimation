#!/bin/bash
# fs-g13c: FINAL blind ID 13 (tuned F5 + retrained NN) at 0.0 dB, 1e-5 region
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id13 --fzstop 0.6,0.80 --snrs 0.0 --frames 120000 --seed 7013 --part fs-g13p00
  echo "ALL DONE" ) > logs/run_fs-g13c.out 2>&1
