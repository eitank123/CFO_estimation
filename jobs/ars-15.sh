#!/bin/bash
# ars-15: Griebel et al. ARS 2021 variants on the rcs13 layout + RCS2-13, R = 0.15, pn 0, 480k packets per SNR in chunks of 4000
# (expected_ars.md, 2026-11-15); SAME seed, chunks and SNRs as e4-15 (minus SNRs < -5 dB): RCS2-13 here must equal e4-15 bit-exactly
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4.5 -4 -3.5 -3 -2.5 -2 -1 0 1 --frames 480000 --min-err 100000 --chunks 120 --seed 51 --pn 0 --sources "RCS2-13" "G4096" "G2048" "G2048N" "Griebel faithful" "RCS2-13 lobes" --part ars-15
  echo "ALL DONE" ) > logs/run_ars-15.out 2>&1
