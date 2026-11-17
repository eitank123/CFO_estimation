#!/bin/bash
# fs-cktrsmoke: tiny ck_nn_fs.py run per format (1 validation point, 2 epochs x 2 steps of 4 packets, smoke model names
# ck_nn_fs_smoke_<fmt>), then 40 packets of run_blind_fs --cknn fmt with those models (the loading path)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results small_cfo/blind/models
S="--design ga --cfo-max 0.03 --val 10 --val-frames 2000 --val-time 0.5 --epochs 2 --steps 2 --mb 4 --budget 4"
B="--design ga --cfo-max 0.03 --workers 16 --frames 40 --batch 10 --max-err 40 --seed 9901 --cknn fmt"
( $PY -u fullsys/ck_nn_fs.py --fmt id3 $S --val-snrs -1.0 --name ck_nn_fs_smoke_id3 --part fs-cktrsmoke-3
  $PY -u fullsys/ck_nn_fs.py --fmt id13 $S --val-snrs -0.8 --name ck_nn_fs_smoke_id13 --part fs-cktrsmoke-13
  $PY -u fullsys/ck_nn_fs.py --fmt id14s $S --val-snrs 1.3 --name ck_nn_fs_smoke_id14s --part fs-cktrsmoke-14s
  $PY -u fullsys/ck_nn_fs.py --fmt id42b $S --val-snrs -4.3 --name ck_nn_fs_smoke_id42b --part fs-cktrsmoke-42b
  $PY -u fullsys/run_blind_fs.py --fmt id3 $B --snrs -1.0 --cknn-name ck_nn_fs_smoke_id3 --part fs-cktrsmoke-bl3
  $PY -u fullsys/run_blind_fs.py --fmt id13 $B --snrs -0.8 --cknn-name ck_nn_fs_smoke_id13 --part fs-cktrsmoke-bl13
  $PY -u fullsys/run_blind_fs.py --fmt id14s $B --snrs 1.2 --cknn-name ck_nn_fs_smoke_id14s --part fs-cktrsmoke-bl14s
  $PY -u fullsys/run_blind_fs.py --fmt id42b $B --snrs -4.4 --cknn-name ck_nn_fs_smoke_id42b --part fs-cktrsmoke-bl42b
  echo "ALL DONE" ) > logs/run_fs-cktrsmoke.out 2>&1
