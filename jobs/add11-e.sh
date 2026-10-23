#!/bin/bash
# add11-e: R=1/3 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, top-up (500000 frames or 100 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add11-e.out
PROG=logs/add11-e.progress
TOTAL=15
T0=$(date +%s)
mkdir -p logs lowrate/logs
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL chunks" > "$LOG"
finish() {  # name status
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag packet code source esn0 frames seed
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 100 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add11-p1024r13-genie-1p5-2 1024 "R=1/3,C16" "Genie (known CFO)" 1.5 500000 11004 ) &
( run add11-p1024r13-genie-3p0-1 1024 "R=1/3,C16" "Genie (known CFO)" 3.0 500000 11012 ) &
( run add11-p1024r13-mm-3p0-0 1024 "R=1/3,C16" "M&M" 3.0 500000 11020 ) &
( run add11-p1024r13-mm-7p0-2 1024 "R=1/3,C16" "M&M" 7.0 500000 11028 ) &
( run add11-p1024r13-mm-10p0-1 1024 "R=1/3,C16" "M&M" 10.0 500000 11036 ) &
( run add11-p1024r13-snn-3p0-0 1024 "R=1/3,C16" "Split pilots NN, quarter" 3.0 500000 11044 ) &
( run add11-p1024r13-snn-7p0-2 1024 "R=1/3,C16" "Split pilots NN, quarter" 7.0 500000 11052 ) &
( run add11-p1024r13-snn-10p0-1 1024 "R=1/3,C16" "Split pilots NN, quarter" 10.0 500000 11060 ) &
( run add11-p1024r13-mmf-1p0-2 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 1.0 500000 11068 ) &
( run add11-p1024r13-mmf-2p0-2 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 2.0 500000 11076 ) &
( run add11-p1024r13-mmf-3p0-2 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 3.0 500000 11084 ) &
( run add11-p1024r13-mmf-6p0-0 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 6.0 500000 11092 ) &
( run add11-p1024r13-snnf-1p0-3 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 500000 11100 ) &
( run add11-p1024r13-snnf-2p0-3 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 500000 11108 ) &
( run add11-p1024r13-snnf-3p0-3 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 500000 11116 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
