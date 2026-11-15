#!/bin/bash
# e4-pp: est4 "RCS2 pre/post" (16 + 16 known, 4th-power NDA) alone, pn 0, same seeds as e4-15/10/25/2 (same data, CFO,
# phase); --min-err 200 so the SNRs where its NDA fails (~90 % BLER at -4 dB, ~68 decodes / packet) stop early
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4.5 -4 -3.5 -3 -2.5 -2 -1 0 1 --frames 480000 --min-err 200 --chunks 120 --seed 51 --pn 0 --sources "RCS2 pre/post" --part e4-pp15
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5.5 -5 -4.5 -4 -3 -2 -1 0 --frames 480000 --min-err 200 --chunks 120 --seed 52 --pn 0 --sources "RCS2 pre/post" --part e4-pp10
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0 0.5 1 1.5 2 --frames 480000 --min-err 200 --chunks 120 --seed 53 --pn 0 --sources "RCS2 pre/post" --part e4-pp25
  $PY -u est4/run_bler.py --rate 1/2 --snrs 1.5 2 2.5 3 --frames 480000 --min-err 200 --chunks 120 --seed 54 --pn 0 --sources "RCS2 pre/post" --part e4-pp2
  echo "ALL DONE" ) > logs/run_e4-pp.out 2>&1
