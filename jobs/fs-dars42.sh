#!/bin/bash
# fs-dars42: DVB-RCS2 ID 42 with the DATA-AIDED synchroniser (fullsys/da_sync.py), CFO U(+-0.03)/symbol + uniform phase,
# N0 estimated, timing known. Variant strong (top-3 candidates until the CRC); the standard receiver (1 estimate, 1 decode)
# is its attempt 1 (standard_* fields, chunks.err_idx_att1). Grid = TR ref 1e-3 (-3.81 dB) -0.4 .. +0.4 in 0.2, seed 42
# (= ideal fs-rcs2v42, paired); + the TR 1e-5 point (-3.52 dB), 1e7 frames, seed 142 (= ideal fs-rcs2v42b). Decoder as run_rcs2. Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 42 --snrs -4.21 -4.01 -3.81 -3.61 -3.41 --frames 1000000 --max-err 300 --seed 42 --variant strong --top-m 3 --workers 16 --part fs-dars42
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 42 --snrs -3.52 --frames 10000000 --max-err 100 --seed 142 --variant strong --top-m 3 --workers 16 --part fs-dars42b
  echo "ALL DONE" ) > logs/run_fs-dars42.out 2>&1
