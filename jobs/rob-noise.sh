#!/bin/bash
# rob-noise: robustness: noise-only packets (false alarms) at the operating points' noise power: final blind / 3x8 receivers with and without the re-encoding check
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_rob-noise.out
$PY -u blind_ber.py --noise-only --points 1/10:-5:16 --max-frames 100 --min-errors 100000 --rx "S blind final" "S blind final, CRC only" "S pilots final" "S pilots final, CRC only" --seed 5711 --part noise-10 >> logs/run_rob-noise.out 2>&1
$PY -u blind_ber.py --noise-only --points 2/5:0.5:16 1/2:2:16 --max-frames 100 --min-errors 100000 --rx "S blind final 2/5, 1/2" "S blind final 2/5, 1/2, CRC only" "S pilots final 2/5, 1/2" "S pilots final 2/5, 1/2, CRC only" --seed 5712 --part noise-25 >> logs/run_rob-noise.out 2>&1
echo "ALL DONE" >> logs/run_rob-noise.out
