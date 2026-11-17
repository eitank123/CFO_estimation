#!/bin/bash
# fs-bl42q: blind (base25_qfix_fzs) on the ID 42 payload on QPSK (the id13 code, tag 42 packets); paired with fs-pg42q (seed 42)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id42q --snrs -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 0.40 0.60 --frames 100000 --max-err 200 --stop-per 2e-4 --seed 42 --workers 16 --part fs-bl42q
  echo "ALL DONE" ) > logs/run_fs-bl42q.out 2>&1
