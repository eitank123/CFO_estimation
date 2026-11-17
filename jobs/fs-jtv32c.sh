#!/bin/bash
# fs-jtv32c: VDE-SAT 32 JOINT TUNING rerun with the RELATIVE objective (each SNR counts by cost / baseline cost); the
# fs-jtv32b pick (abs objective) cut -6.2 dB by 48 % but raised -4.6 dB by 18 % (live check fs-jv32t*)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46 --name v32jr --objective rel --restarts 2 --workers 8
  echo "ALL DONE" ) > logs/run_fs-jtv32c.out 2>&1
