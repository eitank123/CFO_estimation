#!/bin/bash
# rob-margin: the re-encoding threshold at the SNR estimate + 1 dB (an SNR underestimated by 1 dB let wrong packets through): with / without the margin, true SNR and -1 dB error
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_rob-margin.out
$PY -u blind_ber.py --points 1/10:-5:16 --max-frames 400 --min-errors 100000 --rx "S blind final" "S blind final, SNR error -1 dB" "S blind final, check margin 1 dB" "S blind final, check margin 1 dB, SNR error -1 dB" "S pilots final" "S pilots final, SNR error -1 dB" "S pilots final, check margin 1 dB" "S pilots final, check margin 1 dB, SNR error -1 dB" --seed 5701 --part smoke-rob-margin10 >> logs/run_rob-margin.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 400 --min-errors 100000 --rx "S blind final 2/5, 1/2" "S blind final 2/5, 1/2, SNR error -1 dB" "S blind final 2/5, 1/2, check margin 1 dB" "S blind final 2/5, 1/2, check margin 1 dB, SNR error -1 dB" --seed 5702 --part smoke-rob-margin25 >> logs/run_rob-margin.out 2>&1
echo "ALL DONE" >> logs/run_rob-margin.out
