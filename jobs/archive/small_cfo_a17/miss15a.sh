#!/bin/bash
# miss15a: per-packet MACs per core (standard critical path, crit_par) of the right decodes -> missed packets vs a per-core
# MAC cap; final blind receiver, seed 7401
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 12500 --min-errors 100000 --points 0.15:-4:8 0.15:-3:8 --rx "S blind final v2" --seed 7401 --part miss-15a
  echo "ALL DONE" ) > logs/run_miss15a.out 2>&1
