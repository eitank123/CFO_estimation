#!/bin/bash
# add9-e: R=1/4 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, first look (200000 frames or 300 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add9-e.out
PROG=logs/add9-e.progress
TOTAL=14
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 300 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add9-p1024r14-snnf-0p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 200000 9004 ) &
( run add9-p1024r14-snnf-0p5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 200000 9009 ) &
( run add9-p1024r14-snnf-1p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 200000 9014 ) &
( run add9-p1024r14-snnf-1p5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 200000 9019 ) &
( run add9-p1024r14-snnf-2p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 200000 9024 ) &
( run add9-p1024r14-snnf-2p5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 200000 9029 ) &
( run add9-p1024r14-snnf-3p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 200000 9034 ) &
( run add9-p1024r14-snnf-4p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 200000 9039 ) &
( run add9-p1024r14-snnf-5p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 5.0 200000 9044 ) &
( run add9-p1024r14-snnf-6p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 6.0 200000 9049 ) &
( run add9-p1024r14-snnf-7p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 7.0 200000 9054 ) &
( run add9-p1024r14-snnf-8p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 8.0 200000 9059 ) &
( run add9-p1024r14-snnf-9p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 9.0 200000 9064 ) &
( run add9-p1024r14-snnf-10p0 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 10.0 200000 9069 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
