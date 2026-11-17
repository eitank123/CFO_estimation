#!/bin/bash
# fs-blbase: baseline identity of the blind format hooks: the current receiver without a format context == the git HEAD receiver (fullsys/_head, extracted locally with selftest_blind_fs.py --extract) bit for bit at 1/10 (testing_s11g, +1 / -3 dB) and 1/2 (base2_qfix_fzs, 3 / 1.5 dB), + a BlindFormat context entered / left restores everything
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs
( $PY -u fullsys/selftest_blind_fs.py
  echo "ALL DONE" ) > logs/run_fs-blbase.out 2>&1
