#!/bin/bash
# fs-esd-r14: DVB-RCS2 ID 14 final DA curve (fs-q14td: same seed / points / frames / max-err) re-run with CRC early stop (2026-11-19 standard)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 14 --snrs 1.09 1.29 1.49 1.69 1.89 --frames 300000 --max-err 100 --seed 14 --variant strong --top-m 3 --early-stop --es-crc-start 1 --es-crc-cost --workers 16 --part fs-esd-q14td
  echo "ALL DONE" ) > logs/run_fs-esd-r14.out 2>&1
