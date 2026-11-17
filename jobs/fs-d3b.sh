#!/bin/bash
# fs-d3b: blind ID 3 at +0.4 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(   $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.4 --frames 80000 --seed 3 --part fs-d3p04
  echo "ALL DONE" ) > logs/run_fs-d3b.out 2>&1
