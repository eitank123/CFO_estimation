#!/bin/bash
# eqrb15: rotation-bit code (eqrb, BLIND_NOINT=1 BLIND_ROTBITS=1, expected_eqrb.md) vs the interleaved receiver, same seed:
# same data / CFO / phase / noise, only the code construction / bit mapping differs (2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7953 --points 0.15:-4:16 0.15:-3:16 --rx testing --part t-eqrb15b
  BLIND_NOINT=1 BLIND_ROTBITS=1 $R --max-frames 4000 --seed 7953 --points 0.15:-4:16 0.15:-3:16 --rx nofast15_qfix_eqrb --part t-eqrb15r
  echo "ALL DONE" ) > logs/run_eqrb15.out 2>&1
