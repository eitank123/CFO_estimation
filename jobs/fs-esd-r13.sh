#!/bin/bash
# fs-esd-r13: DVB-RCS2 ID 13 final DA curve (fs-q13da: same seed / points / frames / max-err) re-run with CRC early stop (2026-11-19 standard)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 13 --snrs -1.20 -1.00 -0.80 -0.60 -0.40 --frames 300000 --max-err 100 --seed 13 --variant strong --top-m 3 --early-stop --es-crc-start 1 --es-crc-cost --workers 16 --part fs-esd-q13da
  echo "ALL DONE" ) > logs/run_fs-esd-r13.out 2>&1
