#!/bin/bash
# fs-rcs2smoke: smoke test, 100 frames per point at high-PER points (failure paths) and every code path (BPSK, rate 1/2 / 2/3, --fmt, log-MAP, sf 0.7, early stop, en / en-natswap interleavers)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 13 3 --snrs -1.4 -0.8 --frames 100 --max-err 100 --batch 50 --seed 900 --workers 16 --part fs-rcs2smoke
  $PY -u fullsys/run_rcs2.py --wf 3 --snrs -0.27 --sf 0.7 --frames 100 --max-err 100 --batch 50 --seed 901 --workers 16 --part fs-rcs2smoke-b
  $PY -u fullsys/run_rcs2.py --wf 42 --snrs -4.4 --itl en --frames 100 --max-err 100 --batch 50 --seed 902 --workers 16 --part fs-rcs2smoke-c
  $PY -u fullsys/run_rcs2.py --wf 14 --snrs 0.9 --algo logmap --sf 1.0 --early-stop --frames 100 --max-err 100 --batch 50 --seed 903 --workers 16 --part fs-rcs2smoke-d
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.0 --itl en-natswap --frames 100 --max-err 100 --batch 50 --seed 904 --workers 16 --part fs-rcs2smoke-e
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N2256 --ebn0-aff3ct 2.0 --frames 100 --max-err 100 --batch 50 --seed 905 --workers 16 --part fs-rcs2smoke-f
  echo "ALL DONE" ) > logs/run_fs-rcs2smoke.out 2>&1
