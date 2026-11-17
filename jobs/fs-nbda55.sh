#!/bin/bash
# fs-nbda55: as fs-nbda with CFO U(+-0.055)/symbol (the S-band +-0.1 ppm UE budget of TS 36.102 6.4B.1, about +-200 Hz),
# search window +-0.055 (comb aliases at +-0.069). Seed 50: the same payload + noise as fs-nbv / fs-nbda (paired; the
# CFO draws are the same uniforms scaled, do not pool with fs-nbda). Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --sys nbiot --variant strong --top-m 3 --cfo-max 0.055 --frames 1000000 --max-err 300 --seed 50 --workers 16"
( $R --nbfmt nb208 --snrs -4.50 -4.25 -4.00 -3.75 -3.50 -3.25 -3.00 -2.75 -2.50 -2.25 -2.00 -1.75 -1.50 -1.25 -1.00 --part fs-nbda55-208
  $R --nbfmt nb328 --snrs -2.50 -2.25 -2.00 -1.75 -1.50 -1.25 -1.00 -0.75 -0.50 -0.25 0.00 0.25 0.50 0.75 1.00 --part fs-nbda55-328
  $R --nbfmt nb808 --snrs 0.25 0.50 0.75 1.00 1.25 1.50 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 --part fs-nbda55-808
  $R --nbfmt nb1000 --snrs 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 4.00 4.25 4.50 4.75 5.00 5.25 --part fs-nbda55-1000
  echo "ALL DONE" ) > logs/run_fs-nbda55.out 2>&1
