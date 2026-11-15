#!/bin/bash
# add10-h: R=1/4 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, top-up (500000 frames or 100 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add10-h.out
PROG=logs/add10-h.progress
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

( run add10-p1024r14-snnf-0p5-1 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 500000 10007 ) &
( run add10-p1024r14-snnf-1p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 500000 10015 ) &
( run add10-p1024r14-snnf-1p5-5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 500000 10023 ) &
( run add10-p1024r14-snnf-2p5-1 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 500000 10031 ) &
( run add10-p1024r14-snnf-3p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 500000 10039 ) &
( run add10-p1024r14-snnf-4p0-5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 500000 10047 ) &
( run add10-p1024r14-mmf-0p5-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 0.5 500000 10055 ) &
( run add10-p1024r14-mmf-1p5-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 1.5 500000 10063 ) &
( run add10-p1024r14-mmf-2p5-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 2.5 500000 10071 ) &
( run add10-p1024r14-mmf-4p0-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 4.0 500000 10079 ) &
( run add10-p1024r14-snn-6p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter" 6.0 500000 10087 ) &
( run add10-p1024r14-snn-8p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter" 8.0 500000 10095 ) &
( run add10-p1024r14-snn-10p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter" 10.0 500000 10103 ) &
( run add10-p1024r14-mm-8p0-3 1024 "R=1/4,C16" "M&M" 8.0 500000 10111 ) &
( run add10-p1024r14-mm-10p0-3 1024 "R=1/4,C16" "M&M" 10.0 500000 10119 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
