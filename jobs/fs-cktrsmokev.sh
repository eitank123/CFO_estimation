#!/bin/bash
# fs-cktrsmokev: tiny ck_nn_fs.py run for vde32 (1 validation point, 2 epochs x 2 steps of 4 packets, smoke model name
# ck_nn_fs_smoke_vde32), then 40 packets of run_blind_fs --fmt vde32 --cknn fmt with it at -5.8 dB (the loading path, the
# 0.15 mapping c 3 without the coarse start), then the guard: a missing model name must exit before the pool
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results small_cfo/blind/models
S="--cfo-max 0.03 --val 10 --val-frames 2000 --val-time 0.5 --epochs 2 --steps 2 --mb 4 --budget 4"
B="--cfo-max 0.03 --workers 16 --frames 40 --batch 10 --max-err 40 --seed 9932 --cknn fmt"
( $PY -u fullsys/ck_nn_fs.py --fmt vde32 $S --val-snrs -5.8 --name ck_nn_fs_smoke_vde32 --part fs-cktrsmokev-v32
  $PY -u fullsys/run_blind_fs.py --fmt vde32 $B --dump --snrs -5.8 --cknn-name ck_nn_fs_smoke_vde32 --part fs-cktrsmokev-bl
  $PY -u fullsys/run_blind_fs.py --fmt vde32 $B --snrs -5.8 --cknn-name ck_nn_fs_smoke_missing --part fs-cktrsmokev-guard \
    && echo "GUARD FAILED: ran without the model" || echo "GUARD OK (exit $?)"
  echo "ALL DONE" ) > logs/run_fs-cktrsmokev.out 2>&1
