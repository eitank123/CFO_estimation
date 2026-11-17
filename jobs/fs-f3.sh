#!/bin/bash
# fs-f3: blind ID 3 (untuned) at +0.8 dB, 1e-5 region
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.8 --frames 300000 --seed 350 --part fs-f3p08
  echo "ALL DONE" ) > logs/run_fs-f3.out 2>&1
