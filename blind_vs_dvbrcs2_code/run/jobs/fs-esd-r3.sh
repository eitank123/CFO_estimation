#!/bin/bash
# fs-esd-r3: DVB-RCS2 ID 3 final DA curve (fs-q3td + fs-q3deep: same seeds / points / frames / max-err) re-run with CRC early stop (2026-11-19 standard)
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
( $PY -u run_fullsys_da.py --sys rcs2 --wf 3 --snrs -1.07 -0.87 -0.67 -0.47 -0.27 -0.07 0.13 --frames 300000 --max-err 100 --seed 3 --variant strong --top-m 3 --early-stop --es-crc-start 1 --es-crc-cost --workers 16 --part fs-esd-q3td
  $PY -u run_fullsys_da.py --sys rcs2 --wf 3 --snrs 0.33 0.53 --frames 600000 --max-err 100 --seed 303 --variant strong --top-m 3 --early-stop --es-crc-start 1 --es-crc-cost --workers 16 --part fs-esd-q3deep
  echo "ALL DONE" ) > logs/run_fs-esd-r3.out 2>&1
