#!/bin/bash
# fs-pgga: rate-matched polar with the GA info set (--design ga, design Es/N0 = DESIGN_SNR: id13 -0.5, id14s +1.8 dB), CRC-32, genie sync; id13 / id14s at L 8 then L 16, the fs-pg13 / fs-pg14 seeds (13 / 14) and grid points: same data and noise per packet as the PW runs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/selftest_polar_rm.py || echo "WARNING selftest_polar_rm FAILED (logged; the GA runs continue)"
  $PY -u fullsys/run_polar_genie.py --ga-check || { echo "FAILED ga-check"; exit 1; }
  $PY -u fullsys/run_polar_genie.py --fmt id13 --design ga --list 8 --snrs -1.00 -0.80 -0.60 -0.40 -0.20 0.00 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 13 --workers 16 --part fs-pgga-13
  $PY -u fullsys/run_polar_genie.py --fmt id14s --design ga --list 8 --snrs 1.20 1.40 1.60 1.80 2.00 2.20 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 14 --workers 16 --part fs-pgga-14s
  $PY -u fullsys/run_polar_genie.py --fmt id13 --design ga --list 16 --snrs -1.00 -0.80 -0.60 -0.40 -0.20 0.00 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 13 --workers 16 --part fs-pgga-l16-13
  $PY -u fullsys/run_polar_genie.py --fmt id14s --design ga --list 16 --snrs 1.20 1.40 1.60 1.80 2.00 2.20 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 14 --workers 16 --part fs-pgga-l16-14s
  echo "ALL DONE" ) > logs/run_fs-pgga.out 2>&1
