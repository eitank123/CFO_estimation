#!/bin/bash
# fs-pgsmoke: smoke test, 100 frames per format at a high-BLER point (failure paths), one CRC-16 run, the --stop-per path, then smoke_polar_rm.py (shortening LLR arms) with 100 packets
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --selfcheck
  $PY -u fullsys/run_polar_genie.py --fmt id13 --snrs -1.4 -0.8 --frames 100 --max-err 100 --batch 50 --seed 900 --workers 16 --part fs-pgsmoke-13
  $PY -u fullsys/run_polar_genie.py --fmt id14s --snrs 1.0 --frames 100 --max-err 100 --batch 50 --seed 901 --workers 16 --part fs-pgsmoke-14s
  $PY -u fullsys/run_polar_genie.py --fmt id14p --snrs 1.0 --frames 100 --max-err 100 --batch 50 --seed 901 --workers 16 --part fs-pgsmoke-14p
  $PY -u fullsys/run_polar_genie.py --fmt id3 --snrs -1.0 --frames 100 --max-err 100 --batch 50 --seed 902 --workers 16 --part fs-pgsmoke-3
  $PY -u fullsys/run_polar_genie.py --fmt id3 --crc 16 --snrs -1.0 --frames 100 --max-err 100 --batch 50 --seed 902 --workers 16 --part fs-pgsmoke-3c16
  $PY -u fullsys/run_polar_genie.py --fmt id42b --snrs -4.4 --frames 100 --max-err 100 --batch 50 --seed 903 --workers 16 --part fs-pgsmoke-42b
  $PY -u fullsys/run_polar_genie.py --fmt id42q --snrs -1.4 --frames 100 --max-err 100 --batch 50 --seed 903 --workers 16 --part fs-pgsmoke-42q
  $PY -u fullsys/run_polar_genie.py --fmt vde32 --snrs -5.0 2.0 -4.0 --frames 100 --max-err 100 --batch 50 --stop-per 0.05 --seed 904 --workers 16 --part fs-pgsmoke-vde
  $PY -u fullsys/smoke_polar_rm.py --part fs-pgsmoke-prm --packets 100 --seed 905
  echo "ALL DONE" ) > logs/run_fs-pgsmoke.out 2>&1
