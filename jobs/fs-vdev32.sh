#!/bin/bash
# fs-vdev32: VDE-SAT Link 32 (SAT-MCS-0.50-2: 312 bits incl. CRC-32 = 280 payload, turbo 1/4, BPSK/CDMA SF 8, 1641 symbols),
# ideal sync, full Tx/Rx chain (RRC 0.25), PER vs Es/N0 per despread symbol around the M.2092 threshold -4.5 dB.
# log-MAP (strongest decoder) and max-log x 0.75 on the SAME packets (same seed: paired comparison, do not pool). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_vde.py --link 32 --snrs -7.0 -6.5 -6.0 -5.5 -5.0 -4.5 -4.0 -3.5 -3.0 --frames 1000000 --max-err 300 --seed 1 --workers 16 --algo logmap --iters 8 --part fs-vdev32
  $PY -u fullsys/run_vde.py --link 32 --snrs -7.0 -6.5 -6.0 -5.5 -5.0 -4.5 -4.0 -3.5 -3.0 --frames 1000000 --max-err 300 --seed 1 --workers 16 --algo maxlog --iters 8 --part fs-vdev32ml
  echo "ALL DONE" ) > logs/run_fs-vdev32.out 2>&1
