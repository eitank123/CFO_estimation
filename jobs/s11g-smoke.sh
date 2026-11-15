#!/bin/bash
# s11g-smoke: SNR-gated spec11 (testing_s11g) must equal testing_spec11 below the switch and testing above (expected_s11.md, 2026-11-14)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 400 --points 1/10:-5:2 1/10:-3:2 0.15:-3:2 0.15:-2:2 --seed 7940 --rx testing testing_spec11 testing_s11g --part t-s11g-smoke
  echo "ALL DONE" ) > logs/run_s11g-smoke.out 2>&1
