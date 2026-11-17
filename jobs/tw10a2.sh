#!/bin/bash
# tw10a2: rerun of tw10a with per-packet MACs logging (tw10a cancelled 2026-11-15 at the user's request); testing_s11g, 1/10 -5 and -4.5 dB, 480k each (the 1e-4 crossing had only 10 / 1 errors at 64k) (2026-11-15; testing model over the full SNR range, user request)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-5:120 1/10:-4.5:120 --rx testing_s11g --seed 8211 --part t-tw10a2
  echo "ALL DONE" ) > logs/run_tw10a2.out 2>&1
