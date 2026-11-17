#!/bin/bash
# fs-blcal: CALIBRATION packets (--calib: seed tag + 500000, disjoint from every reported fs-bl* run; seeds 7xxx) for the per-format thresholds (rho_n table, F5 q / t, spec11, checkpoints): every format at 2 waterfall points, F5 / spec measured-only off, --dump (per-packet records + decode / fz rows); tune on these, report on fs-bl13 ... fs-blvde
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
C="--frames 4000 --max-err 4000 --calib --dump --workers 16"
( $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -0.8 -0.2 $C --seed 7013 --part fs-blcal-13
  $PY -u fullsys/run_blind_fs.py --fmt id14s --snrs 1.4 2.0 $C --seed 7014 --part fs-blcal-14s
  $PY -u fullsys/run_blind_fs.py --fmt id14p --snrs 1.4 2.0 $C --seed 7014 --part fs-blcal-14p
  $PY -u fullsys/run_blind_fs.py --fmt id3 --snrs -0.4 0.4 $C --seed 7003 --part fs-blcal-3
  $PY -u fullsys/run_blind_fs.py --fmt id42b --snrs -3.8 -3.2 $C --seed 7042 --part fs-blcal-42b
  $PY -u fullsys/run_blind_fs.py --fmt id42q --snrs -0.8 -0.2 $C --seed 7042 --part fs-blcal-42q
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --snrs -4.0 -3.2 $C --seed 7032 --part fs-blcal-vde
  echo "ALL DONE" ) > logs/run_fs-blcal.out 2>&1
