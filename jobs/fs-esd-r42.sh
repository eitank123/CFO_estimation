#!/bin/bash
# fs-esd-r42: DVB-RCS2 ID 42 final DA curve (fs-q42td: same seed / points / frames / max-err) re-run with CRC early stop (2026-11-19 standard)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 42 --snrs -4.41 -4.21 -4.01 -3.81 -3.61 -3.41 --frames 300000 --max-err 100 --seed 42 --variant strong --top-m 3 --early-stop --es-crc-start 1 --es-crc-cost --workers 16 --part fs-esd-q42td
  echo "ALL DONE" ) > logs/run_fs-esd-r42.out 2>&1
