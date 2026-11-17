#!/bin/bash
# ars-smoke: Griebel et al. ARS 2021 variants on the rcs13 layout + RCS2-13 for pairing (expected_ars.md, 2026-11-15),
# 800 packets: a = R 0.15 per-symbol -4 dB, b = R 2/5 0.5 dB, pn 0
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 66 --pn 0 --sources "RCS2-13" "G4096" "G2048" "G2048N" "Griebel faithful" "RCS2-13 lobes" --part ars-smoke-a
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 66 --pn 0 --sources "RCS2-13" "G4096" "G2048" "G2048N" "Griebel faithful" "RCS2-13 lobes" --part ars-smoke-b
  echo "ALL DONE" ) > logs/run_ars-smoke.out 2>&1
