#!/bin/bash
# fs-pgl32: rate-matched polar (PW design, CRC-32), CA-SCL-32 (--list 32), genie sync; id14s, id13, id3, vde32, id42b with the L = 8 jobs' grids and seeds (fs-pg14 / fs-pg13 / fs-pg3 / fs-pgvde / fs-pg42): same data and noise per packet (VDE part removed 2026-11-17: DVB-RCS2 first)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id14s --list 32 --snrs 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 14 --workers 16 --part fs-pgl32-14s
  $PY -u fullsys/run_polar_genie.py --fmt id13 --list 32 --snrs -1.80 -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 13 --workers 16 --part fs-pgl32-13
  $PY -u fullsys/run_polar_genie.py --fmt id3 --list 32 --snrs -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 0.40 0.60 0.80 1.00 1.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 3 --workers 16 --part fs-pgl32-3
  $PY -u fullsys/run_polar_genie.py --fmt id42b --list 32 --snrs -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 42 --workers 16 --part fs-pgl32-42b
  echo "ALL DONE" ) > logs/run_fs-pgl32.out 2>&1
