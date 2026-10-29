#!/bin/bash
# pm-r10: R=1/10, -5 .. 0 dB. 128-pilot split NN + CRC search with and without the pre-MF correction, and the pre-MF genie, on the
# same frames (--shared-frames); study CFO_STUDY=premf_split (results in premf_split/), one lane per (SNR, seed).
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=premf_split
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_pm-r10.out
PROG=logs/pm-r10.progress
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "R=0.1,C16" --sources "Split pilots NN, quarter + CRC search (first pass)" "Split pilots NN, quarter, pre-MF correction + CRC search (first pass)" "Genie (known CFO), pre-MF correction" --shared-frames --tag $1 --extra-esn0 $2 --min-errors 100 --max-frames $3 --seed $4 --workers 1 > premf_split/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add-pm-r10-m5-0 -5 1000000 17000 ) &
( run add-pm-r10-m4p5-0 -4.5 1000000 17008 ) &
( run add-pm-r10-m4-0 -4 1000000 17016 ) &
( run add-pm-r10-m4-1 -4 1000000 17024 ) &
( run add-pm-r10-m3p5-0 -3.5 1000000 17032 ) &
( run add-pm-r10-m3-0 -3 1000000 17040 ) &
( run add-pm-r10-m3-1 -3 1000000 17048 ) &
( run add-pm-r10-m2p5-0 -2.5 1000000 17056 ) &
( run add-pm-r10-m2-0 -2 1000000 17064 ) &
( run add-pm-r10-m2-1 -2 1000000 17072 ) &
( run add-pm-r10-m1p5-0 -1.5 1000000 17080 ) &
( run add-pm-r10-m1-0 -1 1000000 17088 ) &
( run add-pm-r10-m1-1 -1 1000000 17096 ) &
( run add-pm-r10-m0p5-0 -0.5 1000000 17104 ) &
( run add-pm-r10-0-0 0 1000000 17112 ) &
( run add-pm-r10-0-1 0 1000000 17120 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
