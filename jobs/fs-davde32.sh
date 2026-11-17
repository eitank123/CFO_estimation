#!/bin/bash
# fs-davde32: VDE-SAT Link 32 (BPSK/CDMA SF 8, turbo 1/4, 1641 symbols) with the DATA-AIDED synchroniser: chip-level
# despreading, then DA on the 192 syncword + 180 pilot symbols; CFO U(+-0.03)/symbol (+-0.00375/chip) + uniform phase,
# N0 estimated, timing known; log-MAP 8 it, CRC early stop (as run_vde). Variant strong (top-3); the standard receiver =
# its attempt 1 (standard_* fields). Seed 1 = the ideal run fs-vdev32 (paired), grid -5.0 .. -3.0 (M.2092 threshold
# -4.5 dB; nothing below -5 dB). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys vde --link 32 --snrs -5.0 -4.5 -4.0 -3.5 -3.0 --frames 1000000 --max-err 300 --seed 1 --variant strong --top-m 3 --algo logmap --workers 16 --part fs-davde32
  echo "ALL DONE" ) > logs/run_fs-davde32.out 2>&1
