#!/bin/bash
# e5-ppB: est5 4th-power receivers "ViaSat UW", "hyb3" + "RCS2 pre/post" (C2, paired with hyb3 on the same prepost16 bursts),
# R = 2/5 and 1/2, pn 0, same seeds as e5-25 / e5-2; --min-err 200 (a chunk stops at 2 errors per source,
# so the full 480k only where every source has BLER below about 5e-4)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 2/5 --snrs 0 0.5 1 1.5 2 --frames 480000 --min-err 200 --chunks 120 --seed 64 --pn 0 --sources "ViaSat UW" "hyb3" "RCS2 pre/post" --part e5-pp25
  $PY -u est4/run_bler.py --rate 1/2 --snrs 1.5 2 2.5 3 --frames 480000 --min-err 200 --chunks 120 --seed 65 --pn 0 --sources "ViaSat UW" "hyb3" "RCS2 pre/post" --part e5-pp2
  echo "ALL DONE" ) > logs/run_e5-ppB.out 2>&1
