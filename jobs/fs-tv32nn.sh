#!/bin/bash
# fs-tv32nn: VDE Link 32 with its OWN checkpoint NN (ck_nn_fs_vde32, c 3 = 1/4, no coarse start), paired (seed 32, [--charge-all: the NN's uncharged cells charged (small_rx ck_charge_all)]
# batch 200) with the no-NN runs fs-bv32m54 / fs-bv32m50 / fs-bv32m46
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.4 --frames 1000 --seed 32 --charge-all --part fs-tv32nnm54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.0 --frames 4400 --seed 32 --charge-all --part fs-tv32nnm50
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -4.6 --frames 40000 --seed 32 --charge-all --part fs-tv32nnm46
  echo "ALL DONE" ) > logs/run_fs-tv32nn.out 2>&1
