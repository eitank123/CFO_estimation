#!/bin/bash
# add9-b: R=1/4 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, first look (200000 frames or 300 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add9-b.out
PROG=logs/add9-b.progress
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

( run add9-p1024r14-mm-0p0 1024 "R=1/4,C16" "M&M" 0.0 200000 9001 ) &
( run add9-p1024r14-mm-0p5 1024 "R=1/4,C16" "M&M" 0.5 200000 9006 ) &
( run add9-p1024r14-mm-1p0 1024 "R=1/4,C16" "M&M" 1.0 200000 9011 ) &
( run add9-p1024r14-mm-1p5 1024 "R=1/4,C16" "M&M" 1.5 200000 9016 ) &
( run add9-p1024r14-mm-2p0 1024 "R=1/4,C16" "M&M" 2.0 200000 9021 ) &
( run add9-p1024r14-mm-2p5 1024 "R=1/4,C16" "M&M" 2.5 200000 9026 ) &
( run add9-p1024r14-mm-3p0 1024 "R=1/4,C16" "M&M" 3.0 200000 9031 ) &
( run add9-p1024r14-mm-4p0 1024 "R=1/4,C16" "M&M" 4.0 200000 9036 ) &
( run add9-p1024r14-mm-5p0 1024 "R=1/4,C16" "M&M" 5.0 200000 9041 ) &
( run add9-p1024r14-mm-6p0 1024 "R=1/4,C16" "M&M" 6.0 200000 9046 ) &
( run add9-p1024r14-mm-7p0 1024 "R=1/4,C16" "M&M" 7.0 200000 9051 ) &
( run add9-p1024r14-mm-8p0 1024 "R=1/4,C16" "M&M" 8.0 200000 9056 ) &
( run add9-p1024r14-mm-9p0 1024 "R=1/4,C16" "M&M" 9.0 200000 9061 ) &
( run add9-p1024r14-mm-10p0 1024 "R=1/4,C16" "M&M" 10.0 200000 9066 ) &
( run add9-p1024r13-mmf-0p0 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 0.0 200000 9071 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
