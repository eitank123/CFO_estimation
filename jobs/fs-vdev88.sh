#!/bin/bash
# fs-vdev88: validation vs ITU-R M.2435 4.3.1 (88 info bits, QPSK, turbo 1/4: Es/N0 -1.5 dB at PER 1e-2, -0.3 dB at BER 1e-5),
# pseudo-link M2435 (no CRC: genie frame errors, fixed 8 iterations), full Tx/Rx chain. log-MAP and max-log on the same packets,
# plus a random-interleaver log-MAP run (M.2435's interleaver is not stated). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_vde.py --link M2435 --snrs -4.0 -3.5 -3.0 -2.5 -2.0 -1.5 -1.0 -0.5 0.0 0.5 --frames 4000000 --max-err 500 --seed 11 --workers 16 --algo logmap --iters 8 --part fs-vdev88
  $PY -u fullsys/run_vde.py --link M2435 --snrs -4.0 -3.5 -3.0 -2.5 -2.0 -1.5 -1.0 -0.5 0.0 0.5 --frames 4000000 --max-err 500 --seed 11 --workers 16 --algo maxlog --iters 8 --part fs-vdev88ml
  $PY -u fullsys/run_vde.py --link M2435 --snrs -3.0 -2.5 -2.0 -1.5 -1.0 -0.5 --frames 4000000 --max-err 500 --seed 11 --workers 16 --algo logmap --iters 8 --interleaver random --part fs-vdev88rnd
  echo "ALL DONE" ) > logs/run_fs-vdev88.out 2>&1
