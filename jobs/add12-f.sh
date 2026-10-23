#!/bin/bash
# add12-f: R=1/2 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 2 .. 10 dB, top-up (500000 frames or 100 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add12-f.out
PROG=logs/add12-f.progress
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 100 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add12-p1024r12-genie-3p5-0 1024 "R=1/2,C16" "Genie (known CFO)" 3.5 500000 12005 ) &
( run add12-p1024r12-mm-3p0-0 1024 "R=1/2,C16" "M&M" 3.0 500000 12013 ) &
( run add12-p1024r12-mm-7p0-2 1024 "R=1/2,C16" "M&M" 7.0 500000 12021 ) &
( run add12-p1024r12-mm-10p0-1 1024 "R=1/2,C16" "M&M" 10.0 500000 12029 ) &
( run add12-p1024r12-snn-5p0-0 1024 "R=1/2,C16" "Split pilots NN, quarter" 5.0 500000 12037 ) &
( run add12-p1024r12-snn-9p0-0 1024 "R=1/2,C16" "Split pilots NN, quarter" 9.0 500000 12045 ) &
( run add12-p1024r12-mmf-2p5-2 1024 "R=1/2,C16" "M&M + CRC search (first pass)" 2.5 500000 12053 ) &
( run add12-p1024r12-mmf-3p5-2 1024 "R=1/2,C16" "M&M + CRC search (first pass)" 3.5 500000 12061 ) &
( run add12-p1024r12-mmf-4p5-2 1024 "R=1/2,C16" "M&M + CRC search (first pass)" 4.5 500000 12069 ) &
( run add12-p1024r12-mmf-6p0-2 1024 "R=1/2,C16" "M&M + CRC search (first pass)" 6.0 500000 12077 ) &
( run add12-p1024r12-snnf-2p5-3 1024 "R=1/2,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 500000 12085 ) &
( run add12-p1024r12-snnf-3p5-3 1024 "R=1/2,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.5 500000 12093 ) &
( run add12-p1024r12-snnf-4p5-3 1024 "R=1/2,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.5 500000 12101 ) &
( run add12-p1024r12-snnf-6p0-3 1024 "R=1/2,C16" "Split pilots NN, quarter + CRC search (first pass)" 6.0 500000 12109 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
