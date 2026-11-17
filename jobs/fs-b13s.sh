#!/bin/bash
# fs-b13s: SMOKE of the channel-interleaver fix (blind_fmt chan) on ID 13: noiseless chan checks, the run_blind_fs selfcheck (3 packets at 30 dB per format), then blind id13 GA design, Es/N0 -0.2, 200 packets, CFO U(+-0.03), seed 13 batch 200 (same data / noise as fs-b13m02: 73 errors without chan), --dump; expected PER ~1e-3 .. 1e-2 (near genie)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/selftest_chan_fs.py
  $PY -u fullsys/run_blind_fs.py --selfcheck
  $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.2 --frames 200 --max-err 200 --seed 13 --cfo-max 0.03 --workers 16 --dump --part fs-b13s
  echo "ALL DONE" ) > logs/run_fs-b13s.out 2>&1
