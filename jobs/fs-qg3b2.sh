#!/bin/bash
# fs-qg3b2: --charge-all rerun of fs-g3b (part 2 of 2: +0.8; same seeds, points, frames: decisions and BLER identical, only MACs)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs 0.8 --frames 300000 --seed 7003 --charge-all --part fs-g3p08ca
  echo "ALL DONE" ) > logs/run_fs-qg3b2.out 2>&1
