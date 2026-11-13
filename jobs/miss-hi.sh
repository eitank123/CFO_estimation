#!/bin/bash
# miss-hi: per-packet MACs per core (standard critical path) of the right decodes -> missed packets vs a per-core MAC
# cap; final blind receivers at R = 2/5 and 1/2, seed 7403
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 12500 --min-errors 100000 --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 --rx "S blind final 2/5, 1/2, best-first 32" --seed 7403 --part miss-25
  $PY -u blind_ber.py --max-frames 12500 --min-errors 100000 --points 1/2:2:8 1/2:2.5:8 1/2:3:8 --rx "S blind final 2/5, 1/2" --seed 7403 --part miss-2
  echo "ALL DONE" ) > logs/run_miss-hi.out 2>&1
