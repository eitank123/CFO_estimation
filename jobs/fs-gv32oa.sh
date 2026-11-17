#!/bin/bash
# fs-gv32oa: FINAL blind VDE Link 32 (its own checkpoint NN, --cknn fmt), fresh seed 7032: -6.6 .. -5.0. Small chunks [--charge-all: the NN's uncharged cells charged (small_rx ck_charge_all)] + jointly tuned + ONE phase hypothesis (nph 2): floor cut candidate
# (--batch 20 / 50) at the costly low-SNR points so 30 errors arrive in the first wave of the 16 workers (no pairing
# with the batch-200 runs at those points)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -6.6 --frames 2000 --batch 20 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}' --part fs-gv32om66
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -6.2 --frames 4000 --batch 20 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}' --part fs-gv32om62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.8 --frames 8000 --batch 20 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}' --part fs-gv32om58
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.4 --frames 20000 --batch 50 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}' --part fs-gv32om54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.0 --frames 20000 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}' --part fs-gv32om50
  echo "ALL DONE" ) > logs/run_fs-gv32oa.out 2>&1
