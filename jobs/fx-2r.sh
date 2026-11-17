#!/bin/bash
# fx-2r: R = 1/2, pn 0, fixed-search test (expected_fx.md), re-split of fx-25 / fx-2 (2026-11-17: the lowest, high-BLER point made
# RCS2-13 wide decode up to 268 hypotheses per failing packet, ETA 4-5 h): data Es/N0 2.0 2.5, 480k per point, seed 193
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/2 --snrs 2.0 2.5 --frames 480000 --min-err 100000 --chunks 120 --seed 193 --pn 0 --sources "RCS2-13 wide" --part fx-2r
  echo "ALL DONE" ) > logs/run_fx-2r.out 2>&1
