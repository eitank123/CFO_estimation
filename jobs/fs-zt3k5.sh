#!/bin/bash
# fs-zt3k5: z-test grid k5 = drop the first-round cell limit (first_k 32 / batch) now that round 0 pays for every cell up to the NN checkpoint (--charge-all); paired with k0
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.6 --frames 20000 --seed 8003 --sps '{"first_k": {"2/5": null}}' --part fs-zt3k5m06
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.2 --frames 100000 --seed 8003 --sps '{"first_k": {"2/5": null}}' --part fs-zt3k5m02
  echo "ALL DONE" ) > logs/run_fs-zt3k5.out 2>&1
