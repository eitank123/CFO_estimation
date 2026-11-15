#!/bin/bash
# bm2-b: classic fine estimators + split pilots with the estimated phase, R = 2/5 0.5 / 1 dB, R = 1/2 2 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_bm2-b.out
PROG=logs/bm2-b.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=15
T0=$(date +%s)
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL lanes" > "$LOG"
finish() {
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag esn0 frames seed code min-errors
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "M&M + L&R, est. phase, pre-MF + CRC search (first pass)" "M&M + Fitz, est. phase, pre-MF + CRC search (first pass)" "Kay, est. phase, pre-MF + CRC search (first pass)" "Split pilots ML, est. phase, pre-MF + CRC search (first pass)" "Split pilots NN, est. phase, pre-MF + CRC search (first pass)" --shared-frames --tag $1 --extra-esn0 $2 --min-errors $6 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run bm2-R_2_5_C16-0p5 0.5 80000 18048 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-0p5-1 0.5 80000 68049 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-0p5-2 0.5 80000 68050 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-0p5-3 0.5 80000 68051 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-0p5-4 0.5 80000 68052 "R=2/5,C16" 25 ) &
( run bm2-R_2_5_C16-1 1 200000 18056 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-1-1 1 200000 68057 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-1-2 1 200000 68058 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-1-3 1 200000 68059 "R=2/5,C16" 25 ) &
( run add-bm2-R_2_5_C16-1-4 1 200000 68060 "R=2/5,C16" 25 ) &
( run bm2-R_1_2_C16-2 2 120000 18132 "R=1/2,C16" 25 ) &
( run add-bm2-R_1_2_C16-2-1 2 120000 68133 "R=1/2,C16" 25 ) &
( run add-bm2-R_1_2_C16-2-2 2 120000 68134 "R=1/2,C16" 25 ) &
( run add-bm2-R_1_2_C16-2-3 2 120000 68135 "R=1/2,C16" 25 ) &
( run add-bm2-R_1_2_C16-2-4 2 120000 68136 "R=1/2,C16" 25 ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
