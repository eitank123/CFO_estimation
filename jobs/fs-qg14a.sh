#!/bin/bash
# fs-qg14a: --charge-all rerun of fs-g14a (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 14 (tuned F5 + retrained NN): 1.2 .. 1.8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 1.2 --frames 20000 --seed 7014 --charge-all --part fs-g14p12ca
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 1.4 --frames 20000 --seed 7014 --charge-all --part fs-g14p14ca
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 1.6 --frames 30000 --seed 7014 --charge-all --part fs-g14p16ca
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 1.8 --frames 100000 --seed 7014 --charge-all --part fs-g14p18ca
  echo "ALL DONE" ) > logs/run_fs-qg14a.out 2>&1
