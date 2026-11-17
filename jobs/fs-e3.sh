#!/bin/bash
# fs-e3: blind ID 3 at +0.6 dB (1e-4 region)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.6 --frames 100000 --seed 3 --part fs-e3p06
  echo "ALL DONE" ) > logs/run_fs-e3.out 2>&1
