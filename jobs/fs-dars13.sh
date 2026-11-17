#!/bin/bash
# fs-dars13: DVB-RCS2 ID 13 with the DATA-AIDED synchroniser (fullsys/da_sync.py), CFO U(+-0.03)/symbol + uniform phase,
# N0 estimated, timing known. Variant strong (top-3 candidates until the CRC); the standard receiver (1 estimate, 1 decode)
# is its attempt 1 (standard_* fields, chunks.err_idx_att1). Grid = TR ref 1e-3 (-0.80 dB) -0.4 .. +0.4 in 0.2, seed 13
# (= ideal fs-rcs2v13, paired); + the TR 1e-5 point (-0.51 dB), 1e7 frames, seed 113 (= ideal fs-rcs2v13b). Decoder as run_rcs2. Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 13 --snrs -1.20 -1.00 -0.80 -0.60 -0.40 --frames 1000000 --max-err 300 --seed 13 --variant strong --top-m 3 --workers 16 --part fs-dars13
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 13 --snrs -0.51 --frames 10000000 --max-err 100 --seed 113 --variant strong --top-m 3 --workers 16 --part fs-dars13b
  echo "ALL DONE" ) > logs/run_fs-dars13.out 2>&1
