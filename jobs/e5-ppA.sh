#!/bin/bash
# e5-ppA: est5 4th-power receivers "ViaSat UW", "hyb3" + "RCS2 pre/post" (C2, paired with hyb3 on the same prepost16 bursts),
# R = 0.15 and 1/10, pn 0, same seeds as e5-15 / e5-10; --min-err 200 so the SNRs where the 4th power fails stop early (as e4-pp)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4.5 -4 -3.5 -3 -2.5 -2 -1 --frames 480000 --min-err 200 --chunks 120 --seed 63 --pn 0 --sources "ViaSat UW" "hyb3" "RCS2 pre/post" --part e5-pp15
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5 -4.5 -4 -3 -2 --frames 480000 --min-err 200 --chunks 120 --seed 62 --pn 0 --sources "ViaSat UW" "hyb3" "RCS2 pre/post" --part e5-pp10
  echo "ALL DONE" ) > logs/run_e5-ppA.out 2>&1
