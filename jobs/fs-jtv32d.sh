#!/bin/bash
# fs-jtv32d: joint tuning, relative objective, 4 restarts with another seed (search robustness)
# fs-jtv32b pick (abs objective) cut -6.2 dB by 48 % but raised -4.6 dB by 18 % (live check fs-jv32t*)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46 --name v32jr2 --objective rel --restarts 4 --seed 2 --workers 8
  echo "ALL DONE" ) > logs/run_fs-jtv32d.out 2>&1
