#!/bin/bash
# v-2: R = 1/2, pn 0, 480k per SNR in chunks of 4000 (as e5-2): MIL-110 full, CCSDS 131.0 ASM, CCSDS 131.2 real, split64 ML L4 + parents
# (faithful variants of the est5 competitors, expected_variants.md, 2026-11-15; each variant McNemar-paired with its parent)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/2 --snrs 1.5 2 2.5 3 --frames 480000 --min-err 100000 --chunks 120 --seed 121 --pn 0 --sources "MIL-110 HF" "MIL-110 full" "split64 ML" "split64 ML L4" "CCSDS 131.0 ASM" "CCSDS style" "CCSDS 131.2 real" --part v-2
  echo "ALL DONE" ) > logs/run_v-2.out 2>&1
