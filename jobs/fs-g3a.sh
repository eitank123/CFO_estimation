#!/bin/bash
# fs-g3a: FINAL blind ID 3 (retrained NN, no F5): -1.0 .. 0.0
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -1.0 --frames 20000 --seed 7003 --part fs-g3m10
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -0.6 --frames 20000 --seed 7003 --part fs-g3m06
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -0.2 --frames 30000 --seed 7003 --part fs-g3m02
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs 0.0 --frames 40000 --seed 7003 --part fs-g3p00
  echo "ALL DONE" ) > logs/run_fs-g3a.out 2>&1
