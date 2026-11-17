#!/bin/bash
# fs-qg42b: --charge-all rerun of fs-g42b (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 42: -3.4, -3.2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.4 --frames 150000 --seed 7042 --charge-all --part fs-g42m34ca
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.2 --frames 250000 --seed 7042 --charge-all --part fs-g42m32ca
  echo "ALL DONE" ) > logs/run_fs-qg42b.out 2>&1
