#!/bin/bash
# fs-pgl16: rate-matched polar (PW design, CRC-32), CA-SCL-16 (--list 16), genie sync; id14s, id13, id3, vde32, id42b with the L = 8 jobs' grids and seeds (fs-pg14 / fs-pg13 / fs-pg3 / fs-pgvde / fs-pg42): same data and noise per packet
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id14s --list 16 --snrs 0.60 0.80 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 14 --workers 16 --part fs-pgl16-14s
  $PY -u fullsys/run_polar_genie.py --fmt id13 --list 16 --snrs -1.80 -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 13 --workers 16 --part fs-pgl16-13
  $PY -u fullsys/run_polar_genie.py --fmt id3 --list 16 --snrs -1.60 -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 0.00 0.20 0.40 0.60 0.80 1.00 1.20 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 3 --workers 16 --part fs-pgl16-3
  $PY -u fullsys/run_polar_genie.py --fmt vde32 --list 16 --snrs -5.00 -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 -2.40 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 32 --workers 16 --part fs-pgl16-vde
  $PY -u fullsys/run_polar_genie.py --fmt id42b --list 16 --snrs -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 42 --workers 16 --part fs-pgl16-42b
  echo "ALL DONE" ) > logs/run_fs-pgl16.out 2>&1
