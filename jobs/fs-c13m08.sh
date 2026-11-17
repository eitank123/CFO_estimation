#!/bin/bash
# fs-c13m08: blind ID 13 ONE point (Es/N0 -0.8), GA design, channel interleaver on (the pi/2 tie fix),, CFO U(+-0.03), provisional thresholds (early stops off), seed 13 batch 200 (paired with fs-b13m* / fs-q13pg), 30 errors, per-packet dump; submit only after fs-b13cap shows no BLER loss from the cap
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.8 --frames 20000 --max-err 30 --seed 13 --cfo-max 0.03 --workers 16 --dump --part fs-c13m08
  echo "ALL DONE" ) > logs/run_fs-c13m08.out 2>&1
