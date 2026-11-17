#!/bin/bash
# fs-vdev88b: bracket the unknown interleaver of ITU-R M.2435 4.3.1 (88 info bits, QPSK, turbo 1/4, -1.5 dB at PER 1e-2):
# log-MAP 8 it., same grid and seed as fs-vdev88 (paired packets): S-random (S = 6 = floor(sqrt(88/2))), LTE QPP K 88
# (f1 5 f2 22 = TS 36.212 Table 5.1.3-3 as recalled; f1 21 f2 44 as given by the coordinator; both valid QPPs), and
# uniform random interleavers with seeds 1 2 3 (fs-vdev88rnd used seed 0). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
S="-4.0 -3.5 -3.0 -2.5 -2.0 -1.5 -1.0 -0.5 0.0 0.5"
C="--link M2435 --frames 4000000 --max-err 500 --seed 11 --workers 16 --algo logmap --iters 8"
( $PY -u fullsys/run_vde.py --snrs $S $C --interleaver srandom --perm-seed 0 --part fs-vdev88b-srnd
  $PY -u fullsys/run_vde.py --snrs $S $C --interleaver qpp --qpp 5 22 --part fs-vdev88b-qpp
  $PY -u fullsys/run_vde.py --snrs $S $C --interleaver qpp --qpp 21 44 --part fs-vdev88b-qpp2144
  $PY -u fullsys/run_vde.py --snrs $S $C --interleaver random --perm-seed 1 --part fs-vdev88b-rnd1
  $PY -u fullsys/run_vde.py --snrs $S $C --interleaver random --perm-seed 2 --part fs-vdev88b-rnd2
  $PY -u fullsys/run_vde.py --snrs $S $C --interleaver random --perm-seed 3 --part fs-vdev88b-rnd3
  echo "ALL DONE" ) > logs/run_fs-vdev88b.out 2>&1
