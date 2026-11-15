#!/bin/bash
# eqrb-smoke: smoke of the rotation-bit code (eqrb, expected_eqrb.md) at high-BLER points, 400 packets per point: the
# interleaved receiver (part ...-i) and the eqrb receiver with BLIND_NOINT=1 BLIND_ROTBITS=1 (part ...-r), same seed (2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
RB="env BLIND_NOINT=1 BLIND_ROTBITS=1 $R"
( $R --max-frames 25 --seed 7950 --points 0.15:-4.5:16 1/10:-5.5:16 --rx nofast15_qfix --part t-eqrb-smoke-a-i
  $RB --max-frames 25 --seed 7950 --points 0.15:-4.5:16 1/10:-5.5:16 --rx nofast15_qfix_eqrb --part t-eqrb-smoke-a-r
  $R --max-frames 25 --seed 7951 --points 2/5:0:16 --rx base25_qfix --part t-eqrb-smoke-b-i
  $RB --max-frames 25 --seed 7951 --points 2/5:0:16 --rx base25_qfix_eqrb --part t-eqrb-smoke-b-r
  $R --max-frames 25 --seed 7952 --points 1/2:1.5:16 --rx base2_qfix --part t-eqrb-smoke-c-i
  $RB --max-frames 25 --seed 7952 --points 1/2:1.5:16 --rx base2_qfix_eqrb --part t-eqrb-smoke-c-r
  echo "ALL DONE" ) > logs/run_eqrb-smoke.out 2>&1
