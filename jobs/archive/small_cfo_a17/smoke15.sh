#!/bin/bash
# smoke15: R = 0.15 runs end to end (blind receiver with the R = 1/10 profile, est3 back-end), tiny
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results est3/logs est3/results
( BLIND_STUDY=small_cfo $PY -u blind_ber.py --max-frames 200 --min-errors 100000 --points 0.15:-3:16 --rx "S blind final v2" --seed 7299 --part smoke-15
  $PY -u est3/run_bler.py --rate 0.15 --snrs -3 --sources 'Genie CFO' M\&M 'ML direct' --max-frames 1600 --chunks 16 --part smoke15
  echo "ALL DONE" ) > logs/run_smoke15.out 2>&1
