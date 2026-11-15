#!/bin/bash
# e4-pna: est4 under Wiener phase noise, R = 1/10 -5 dB (pn 1e-5, 1e-4, 3e-4) and 0.15 -3.5 dB (pn 1e-5), 64k packets each; seed 55 for every pn (packets paired across pn)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/10 --snrs -5 --frames 64000 --min-err 100000 --chunks 16 --seed 55 --pn 1e-5 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-pn10-1e5
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5 --frames 64000 --min-err 100000 --chunks 16 --seed 55 --pn 1e-4 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-pn10-1e4
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5 --frames 64000 --min-err 100000 --chunks 16 --seed 55 --pn 3e-4 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-pn10-3e4
  $PY -u est4/run_bler.py --rate 0.15 --snrs -3.5 --frames 64000 --min-err 100000 --chunks 16 --seed 55 --pn 1e-5 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-pn15-1e5
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5 --frames 64000 --min-err 100000 --chunks 16 --seed 55 --pn 0 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-pn10-0
  $PY -u est4/run_bler.py --rate 0.15 --snrs -3.5 --frames 64000 --min-err 100000 --chunks 16 --seed 55 --pn 0 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-pn15-0
  echo "ALL DONE" ) > logs/run_e4-pna.out 2>&1
