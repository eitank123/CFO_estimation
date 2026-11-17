#!/bin/bash
# v-10hlb: R = 1/10, pn 0, DVB-S2 header90 only, data Es/N0 -5.3 dB (fair axis -4.93, inside the -5 dB plot limit), 480k packets,
# seed 180 (2026-11-17, user request: bracket the 1e-4 crossing of V3a; v-10hla + v-10hlb = 960k, pooled; expected_variants.md §10)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/10 --snrs -5.3 --frames 480000 --min-err 100000 --chunks 120 --seed 180 --pn 0 --sources "DVB-S2 header90" --part v-10hlb
  echo "ALL DONE" ) > logs/run_v-10hlb.out 2>&1
