#!/bin/bash
# fs-dars3: DVB-RCS2 ID 3 with the DATA-AIDED synchroniser (fullsys/da_sync.py), CFO U(+-0.03)/symbol + uniform phase,
# N0 estimated, timing known. Variant strong (top-3 candidates until the CRC); the standard receiver (1 estimate, 1 decode)
# is its attempt 1 (standard_* fields, chunks.err_idx_att1). Grid = TR ref 1e-3 (-0.27 dB) -0.4 .. +0.4 in 0.2, seed 3
# (= ideal fs-rcs2v3, paired); + the TR 1e-5 point (0.22 dB), 1e7 frames, seed 103 (= ideal fs-rcs2v3b). Decoder as run_rcs2. Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 3 --snrs -0.67 -0.47 -0.27 -0.07 0.13 --frames 1000000 --max-err 300 --seed 3 --variant strong --top-m 3 --workers 16 --part fs-dars3
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --wf 3 --snrs 0.22 --frames 10000000 --max-err 100 --seed 103 --variant strong --top-m 3 --workers 16 --part fs-dars3b
  echo "ALL DONE" ) > logs/run_fs-dars3.out 2>&1
