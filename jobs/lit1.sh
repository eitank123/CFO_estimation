#!/bin/bash
# lit1: literature checks (lit_blind_cfo.md): phase equivariance without the interleaver (Geiselhart 2023) and the
# frozen-bit ranking of grid cells (Giard 2017/18); measurement only (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
L="$PY -u BLIND_IMPLEMENTATION/testing/lit_checks.py"
( $L --check equiv --rate 0.15 --snr -3 --n 4000 --seed 9101 --part t-lit-eq15
  $L --check equiv --rate 2/5 --snr 1 --n 2000 --seed 9102 --part t-lit-eq25
  $L --check equiv --rate 1/10 --snr -5 --n 2000 --seed 9103 --part t-lit-eq10
  $L --check rank --rate 0.15 --snr -4 --n 2000 --seed 9111 --part t-lit-rk15a
  $L --check rank --rate 0.15 --snr -3 --n 2000 --seed 9112 --part t-lit-rk15b
  $L --check rank --rate 1/10 --snr -5 --n 2000 --seed 9113 --part t-lit-rk10
  echo "ALL DONE" ) > logs/run_lit1.out 2>&1
