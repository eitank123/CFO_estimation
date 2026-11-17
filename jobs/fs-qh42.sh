#!/bin/bash
# fs-qh42: --charge-all rerun of fs-h42 (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 42, second seed at -3.8, -3.6 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.8 --frames 30000 --seed 7142 --charge-all --part fs-h42m38ca
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.6 --frames 120000 --seed 7142 --charge-all --part fs-h42m36ca
  echo "ALL DONE" ) > logs/run_fs-qh42.out 2>&1
