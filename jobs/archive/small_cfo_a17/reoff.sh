#!/bin/bash
# reoff: the final blind / 3x8 receivers with the re-encoding check switched off (CRC-16 alone), paired with fin-* (same seeds, the first packets of each chunk)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_reoff.out
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4.5:4 1/10:-4:4 --max-frames 12500 --min-errors 100000 --rx "S blind final, CRC only" "S pilots final, CRC only" --seed 5701 --part reoff-10 >> logs/run_reoff.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:4 --max-frames 12500 --min-errors 100000 --rx "S blind final 2/5, 1/2, CRC only" "S pilots final 2/5, 1/2, CRC only" --seed 5702 --part reoff-25 >> logs/run_reoff.out 2>&1
$PY -u blind_ber.py --points 1/2:2:4 --max-frames 25000 --min-errors 100000 --rx "S blind final 2/5, 1/2, CRC only" "S pilots final 2/5, 1/2, CRC only" --seed 5703 --part reoff-2 >> logs/run_reoff.out 2>&1
echo "ALL DONE" >> logs/run_reoff.out
