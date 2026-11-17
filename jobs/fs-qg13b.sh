#!/bin/bash
# fs-qg13b: --charge-all rerun of fs-g13b (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 13: -0.2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id13 --fzstop 0.6,0.80 --snrs -0.2 --frames 80000 --seed 7013 --charge-all --part fs-g13m02ca
  echo "ALL DONE" ) > logs/run_fs-qg13b.out 2>&1
