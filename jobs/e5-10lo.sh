#!/bin/bash
# e5-10lo: est5 competitors that sat at genie level at the lowest e5-10 point (CCSDS style, DMRS 1/7, MIL-110 HF), R = 1/10,
# extended down in data Es/N0 so the 1e-4 crossing on the fair axis is bracketed, every point >= -5 dB on the plotted axis
# (fair = raw + 0.51 / 0.67 / 1.14 dB). Predictions: testing/results/expected_e5lo.md (2026-11-15). Own part + seed per source.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/10 --snrs -5.5 --frames 480000 --min-err 100000 --chunks 120 --seed 71 --pn 0 --sources "CCSDS style" --part e5-10lo-a
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5.65 --frames 480000 --min-err 100000 --chunks 120 --seed 72 --pn 0 --sources "DMRS 1/7" --part e5-10lo-b
  $PY -u est4/run_bler.py --rate 1/10 --snrs -6.1 -5.5 --frames 480000 --min-err 100000 --chunks 120 --seed 73 --pn 0 --sources "MIL-110 HF" --part e5-10lo-c
  echo "ALL DONE" ) > logs/run_e5-10lo.out 2>&1
