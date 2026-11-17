#!/bin/bash
# fs-vdesmoke: VDE (ITU-R M.2092-2) smoke test, ideal sync, high-PER points so the failure paths run: Link 32 (BPSK/CDMA SF 8,
# turbo 1/4) max-log + log-MAP, M.2435 88-bit QPSK 1/4 (no CRC), Link 11 (pi/4-QPSK 1/2, Kim settings), Link 33 (BPSK 1/3,
# k 4280), Link 34 (2 sub-blocks, pi/4-QPSK + pilots, no tail). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/selftest_vde.py
  $PY -u fullsys/run_vde.py --link 32 --snrs -6.0 --frames 100 --max-err 100 --seed 900 --workers 16 --algo maxlog --part fs-vdesmoke
  $PY -u fullsys/run_vde.py --link 32 --snrs -6.0 --frames 100 --max-err 100 --seed 900 --workers 16 --algo logmap --part fs-vdesmoke-b
  $PY -u fullsys/run_vde.py --link M2435 --snrs -3.0 --frames 100 --max-err 100 --seed 902 --workers 16 --algo logmap --part fs-vdesmoke-c
  $PY -u fullsys/run_vde.py --link 11 --snrs 1.0 --frames 100 --max-err 100 --seed 903 --workers 16 --algo logmap --iters 6 --part fs-vdesmoke-d
  $PY -u fullsys/run_vde.py --link 33 --snrs -4.0 --frames 20 --max-err 100 --batch 4 --seed 904 --workers 16 --part fs-vdesmoke-e
  $PY -u fullsys/run_vde.py --link 34 --snrs -1.5 --frames 20 --max-err 100 --batch 4 --seed 905 --workers 16 --part fs-vdesmoke-f
  echo "ALL DONE" ) > logs/run_fs-vdesmoke.out 2>&1
