#!/bin/bash
# add10-d: R=1/4 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, top-up (500000 frames or 100 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add10-d.out
PROG=logs/add10-d.progress
TOTAL=16
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

( run add10-p1024r14-snnf-0p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 500000 10003 ) &
( run add10-p1024r14-snnf-0p5-5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 500000 10011 ) &
( run add10-p1024r14-snnf-1p5-1 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 500000 10019 ) &
( run add10-p1024r14-snnf-2p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 500000 10027 ) &
( run add10-p1024r14-snnf-2p5-5 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 500000 10035 ) &
( run add10-p1024r14-snnf-4p0-1 1024 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 500000 10043 ) &
( run add10-p1024r14-mmf-0p0-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 0.0 500000 10051 ) &
( run add10-p1024r14-mmf-1p0-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 1.0 500000 10059 ) &
( run add10-p1024r14-mmf-2p0-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 2.0 500000 10067 ) &
( run add10-p1024r14-mmf-3p0-3 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 3.0 500000 10075 ) &
( run add10-p1024r14-mmf-6p0-1 1024 "R=1/4,C16" "M&M + CRC search (first pass)" 6.0 500000 10083 ) &
( run add10-p1024r14-snn-7p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter" 7.0 500000 10091 ) &
( run add10-p1024r14-snn-9p0-3 1024 "R=1/4,C16" "Split pilots NN, quarter" 9.0 500000 10099 ) &
( run add10-p1024r14-mm-7p0-3 1024 "R=1/4,C16" "M&M" 7.0 500000 10107 ) &
( run add10-p1024r14-mm-9p0-3 1024 "R=1/4,C16" "M&M" 9.0 500000 10115 ) &
( run add10-p1024r14-genie-0p0-3 1024 "R=1/4,C16" "Genie (known CFO)" 0.0 500000 10123 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
