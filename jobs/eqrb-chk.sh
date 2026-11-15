#!/bin/bash
# eqrb-chk: unit checks of the rotation-bit code (expected_eqrb.md; BLIND_NOINT=1 BLIND_ROTBITS=1): metric(theta) ==
# metric(theta + q pi/2), the rotation read from (u_{N-2}, u_{N-1}) per q at the low SNRs and at +5 dB, CRC passes at a
# wrong rotation (lit_checks.py --check eqrb); measurement only (2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_NOINT=1 BLIND_ROTBITS=1
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
L="$PY -u BLIND_IMPLEMENTATION/testing/lit_checks.py --check eqrb"
( $L --rate 0.15 --snr -3 --n 4000 --seed 9201 --part t-eqrb-chk15
  $L --rate 2/5 --snr 1 --n 2000 --seed 9221 --part t-eqrb-chk25
  $L --rate 1/10 --snr -5 --n 2000 --seed 9241 --part t-eqrb-chk10
  $L --rate 1/2 --snr 2 --n 2000 --seed 9261 --part t-eqrb-chk2
  $L --rate 0.15 --snr 5 --n 2000 --seed 9281 --part t-eqrb-chk15h
  $L --rate 2/5 --snr 5 --n 2000 --seed 9301 --part t-eqrb-chk25h
  $L --rate 1/2 --snr 5 --n 2000 --seed 9321 --part t-eqrb-chk2h
  $L --rate 1/10 --snr 5 --n 2000 --seed 9341 --part t-eqrb-chk10h
  echo "ALL DONE" ) > logs/run_eqrb-chk.out 2>&1
