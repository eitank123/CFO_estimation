#!/bin/bash
# da-f2-std (2026-11-23, queue_sync42): FULL DVB-RCS2 ID 2 (--variant standard; standard = UW + pilot DA sync), turbo + CRC-16 early
# stop, energy over the 262-symbol burst, seed 2 (= the blind fs-f2 payloads / CFO), 7 points, 1M frames, max-err 100
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results models
( $PY -u run_fullsys_da.py --sys rcs2 --batch 0 --cfo-max 0.03 --workers 16 --dump --wf 2 --variant standard --seed 2 --max-err 100 --snrs -0.25 0.00 0.25 0.50 0.75 1.00 1.25 --frames 1000000 --part da-f2-std
  echo "ALL DONE" ) > logs/run_da-f2-std.out 2>&1
