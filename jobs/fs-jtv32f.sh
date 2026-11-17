#!/bin/bash
# fs-jtv32f: VDE joint tuning WITH the F5 early stop in the grid (relative objective), around the current pick
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46 --name v32jf5 --objective rel --restarts 2 --workers 8 --grid '{"fzstop": [null, [1.0, 0.75], [1.0, 0.8], [0.9, 0.75], [0.9, 0.8], [0.8, 0.8], [0.8, 0.75]], "final": [16, 8, 4, 2], "win": [6.0, 5.0, 4.5, 4.0, 3.5], "ck_keep": [0.001, 0.003, 0.01], "ck_min": [8, 6, 4], "fine_last": [4, 2], "kmin": [16, 8]}'
  echo "ALL DONE" ) > logs/run_fs-jtv32f.out 2>&1
