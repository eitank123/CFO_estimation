#!/bin/bash
# cpar: MACs on the critical path with the serial steps split over the 32 cores (small_rx crit_par_macs), final blind
# receivers at R = 0.15, 2/5, 1/2; 20000 packets per point, seed 7301
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 2500 --min-errors 100000 --points 0.15:-4.5:8 0.15:-4:8 0.15:-3:8 0.15:-2:8 0.15:-1:8 0.15:0:8 0.15:1:8 --rx "S blind final v2" --seed 7301 --part cpar-15
  $PY -u blind_ber.py --max-frames 2500 --min-errors 100000 --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:3:8 --rx "S blind final 2/5, 1/2, best-first 32" --seed 7301 --part cpar-25
  $PY -u blind_ber.py --max-frames 2500 --min-errors 100000 --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:4:8 --rx "S blind final 2/5, 1/2" --seed 7301 --part cpar-2
  echo "ALL DONE" ) > logs/run_cpar.out 2>&1
