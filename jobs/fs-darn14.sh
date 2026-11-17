#!/bin/bash
# fs-darn14: as fs-dars but at the LOW end of DVB-RCS2's design CFO range, U(+-0.005)/symbol (TR 101 545-4 6.2.2: gateways accept 0.5 % .. 3 % of the symbol rate)
# N0 estimated, timing known. Variant strong (top-3 candidates until the CRC); the standard receiver (1 estimate, 1 decode)
# is its attempt 1 (standard_* fields, chunks.err_idx_att1). Grid = TR ref 1e-3 (1.49 dB) -0.4 .. +0.4 in 0.2, seed 14
# (= ideal fs-rcs2v14, paired); + the TR 1e-5 point (1.71 dB), 1e7 frames, seed 114 (= ideal fs-rcs2v14b). Decoder as run_rcs2. Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 14 --snrs 1.09 1.29 1.49 1.69 1.89 --frames 1000000 --max-err 300 --seed 14 --cfo-max 0.005 --variant strong --top-m 3 --workers 16 --part fs-darn14
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 14 --snrs 1.71 --frames 10000000 --max-err 100 --seed 114 --cfo-max 0.005 --variant strong --top-m 3 --workers 16 --part fs-darn14b
  echo "ALL DONE" ) > logs/run_fs-darn14.out 2>&1
