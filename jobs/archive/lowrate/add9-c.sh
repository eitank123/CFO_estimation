#!/bin/bash
# add9-c: R=1/4 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, first look (200000 frames or 300 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add9-c.out
PROG=logs/add9-c.progress
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 300 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add9-p1024r14-mmf-0p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 0.0 200000 9002 ) &
( run add9-p1024r14-mmf-0p5 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 0.5 200000 9007 ) &
( run add9-p1024r14-mmf-1p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 1.0 200000 9012 ) &
( run add9-p1024r14-mmf-1p5 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 1.5 200000 9017 ) &
( run add9-p1024r14-mmf-2p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 2.0 200000 9022 ) &
( run add9-p1024r14-mmf-2p5 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 2.5 200000 9027 ) &
( run add9-p1024r14-mmf-3p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 3.0 200000 9032 ) &
( run add9-p1024r14-mmf-4p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 4.0 200000 9037 ) &
( run add9-p1024r14-mmf-5p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 5.0 200000 9042 ) &
( run add9-p1024r14-mmf-6p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 6.0 200000 9047 ) &
( run add9-p1024r14-mmf-7p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 7.0 200000 9052 ) &
( run add9-p1024r14-mmf-8p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 8.0 200000 9057 ) &
( run add9-p1024r14-mmf-9p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 9.0 200000 9062 ) &
( run add9-p1024r14-mmf-10p0 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 10.0 200000 9067 ) &
( run add9-p1024r13-snnf-0p0 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 200000 9072 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
