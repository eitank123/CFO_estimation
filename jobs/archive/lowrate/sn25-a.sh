#!/bin/bash
# sn25-a: R=2/5 CRC-16 (1024 symbols), 128-pilot split NN + CRC search (first pass) and the genie, 0.5 .. 4 dB; one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_sn25-a.out
PROG=logs/sn25-a.progress
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
( run add13-p1024r25-snnf-0p5-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 1000000 13000 ) &
( run add13-p1024r25-snnf-0p5-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 1000000 13008 ) &
( run add13-p1024r25-snnf-1p0-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 1000000 13016 ) &
( run add13-p1024r25-snnf-1p0-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 1000000 13024 ) &
( run add13-p1024r25-snnf-1p5-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 1000000 13032 ) &
( run add13-p1024r25-snnf-1p5-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 1000000 13040 ) &
( run add13-p1024r25-snnf-2p0-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 1000000 13048 ) &
( run add13-p1024r25-snnf-2p0-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 1000000 13056 ) &
( run add13-p1024r25-snnf-2p5-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 1000000 13064 ) &
( run add13-p1024r25-snnf-2p5-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 1000000 13072 ) &
( run add13-p1024r25-snnf-3p0-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 1000000 13080 ) &
( run add13-p1024r25-snnf-3p0-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 1000000 13088 ) &
( run add13-p1024r25-snnf-4p0-0 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 1000000 13096 ) &
( run add13-p1024r25-snnf-4p0-1 1024 "R=2/5,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 1000000 13104 ) &
( run add13-p1024r25-genie-0p5-0 1024 "R=2/5,C16" "Genie (known CFO)" 0.5 1000000 13112 ) &
( run add13-p1024r25-genie-1p0-0 1024 "R=2/5,C16" "Genie (known CFO)" 1.0 1000000 13120 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
