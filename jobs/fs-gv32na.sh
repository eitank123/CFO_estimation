#!/bin/bash
# fs-gv32na: FINAL blind VDE Link 32 (its own checkpoint NN, --cknn fmt), fresh seed 7032: -6.6 .. -5.0. Small chunks [--charge-all: the NN's uncharged cells charged (small_rx ck_charge_all)] + batch null + final 16 (z-test k5 + k4: identical decisions on calibration, -41..-69 % MACs)
# (--batch 20 / 50) at the costly low-SNR points so 30 errors arrive in the first wave of the 16 workers (no pairing
# with the batch-200 runs at those points)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -6.6 --frames 2000 --batch 20 --seed 7032 --charge-all --sps '{"batch": null, "final": 16}' --part fs-gv32nm66
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -6.2 --frames 4000 --batch 20 --seed 7032 --charge-all --sps '{"batch": null, "final": 16}' --part fs-gv32nm62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.8 --frames 8000 --batch 20 --seed 7032 --charge-all --sps '{"batch": null, "final": 16}' --part fs-gv32nm58
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.4 --frames 20000 --batch 50 --seed 7032 --charge-all --sps '{"batch": null, "final": 16}' --part fs-gv32nm54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -5.0 --frames 20000 --seed 7032 --charge-all --sps '{"batch": null, "final": 16}' --part fs-gv32nm50
  echo "ALL DONE" ) > logs/run_fs-gv32na.out 2>&1
