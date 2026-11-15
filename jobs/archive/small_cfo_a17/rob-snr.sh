#!/bin/bash
# rob-snr: robustness: the final R = 1/10 receivers told the SNR off by -1 .. +1 dB (+ the per-packet MAC histograms at 0 error)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_rob-snr.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S blind final" "S blind final, SNR error -1 dB" "S blind final, SNR error -0.5 dB" "S blind final, SNR error +0.5 dB" "S blind final, SNR error +1 dB" "S pilots final" "S pilots final, SNR error -1 dB" "S pilots final, SNR error -0.5 dB" "S pilots final, SNR error +0.5 dB" "S pilots final, SNR error +1 dB" --seed 5701 --part smoke-rob-snr10 >> logs/run_rob-snr.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 200 --min-errors 100000 --rx "S blind final 2/5, 1/2" "S blind final 2/5, 1/2, SNR error -1 dB" "S blind final 2/5, 1/2, SNR error +1 dB" "S pilots final 2/5, 1/2" "S pilots final 2/5, 1/2, SNR error -1 dB" "S pilots final 2/5, 1/2, SNR error +1 dB" --seed 5702 --part smoke-rob-snr25 >> logs/run_rob-snr.out 2>&1
$PY -u blind_ber.py --points 1/2:2:16 --max-frames 200 --min-errors 100000 --rx "S blind final 2/5, 1/2" "S blind final 2/5, 1/2, SNR error -1 dB" "S blind final 2/5, 1/2, SNR error +1 dB" "S pilots final 2/5, 1/2" "S pilots final 2/5, 1/2, SNR error -1 dB" "S pilots final 2/5, 1/2, SNR error +1 dB" --seed 5703 --part smoke-rob-snr2 >> logs/run_rob-snr.out 2>&1
echo "ALL DONE" >> logs/run_rob-snr.out
