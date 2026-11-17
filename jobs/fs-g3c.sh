#!/bin/bash
# fs-g3c: FINAL blind ID 3 at +1.0 dB (1e-5 region)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs 1.0 --frames 400000 --seed 7003 --part fs-g3p10
  echo "ALL DONE" ) > logs/run_fs-g3c.out 2>&1
