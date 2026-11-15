#!/bin/bash
# pm-r2: R=1/2, 2 .. 5 dB. 128-pilot split NN + CRC search with and without the pre-MF correction, and the pre-MF genie, on the
# same frames (--shared-frames); study CFO_STUDY=premf_split (results in premf_split/), one lane per (SNR, seed).
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=premf_split
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_pm-r2.out
PROG=logs/pm-r2.progress
TOTAL=16
T0=$(date +%s)
mkdir -p logs premf_split/logs
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL chunks" > "$LOG"
finish() {  # name status
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag esn0 frames seed
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "R=1/2,C16" --sources "Split pilots NN, quarter + CRC search (first pass)" "Split pilots NN, quarter, pre-MF correction + CRC search (first pass)" "Genie (known CFO), pre-MF correction" --shared-frames --tag $1 --extra-esn0 $2 --min-errors 100 --max-frames $3 --seed $4 --workers 1 > premf_split/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add-pm-r2-2-1 2 1000000 17400 ) &
( run add-pm-r2-2p5-0 2.5 1000000 17408 ) &
( run add-pm-r2-2p5-1 2.5 1000000 17416 ) &
( run add-pm-r2-3-0 3 1000000 17424 ) &
( run add-pm-r2-3-1 3 1000000 17432 ) &
( run add-pm-r2-3p5-0 3.5 1000000 17440 ) &
( run add-pm-r2-3p5-1 3.5 1000000 17448 ) &
( run add-pm-r2-4-0 4 1000000 17456 ) &
( run add-pm-r2-4-1 4 1000000 17464 ) &
( run add-pm-r2-5-0 5 1000000 17472 ) &
( run add-pm-r2-5-1 5 1000000 17480 ) &
( run add-pm-r2-3-2 3 1000000 17488 ) &
( run add-pm-r2-3p5-2 3.5 1000000 17496 ) &
( run add-pm-r2-4-2 4 1000000 17504 ) &
( run add-pm-r2-5-2 5 1000000 17512 ) &
( run add-pm-r2-2-0 2 1000000 17520 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
