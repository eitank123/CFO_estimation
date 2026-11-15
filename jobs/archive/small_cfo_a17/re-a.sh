#!/bin/bash
# re-a: the 128-pilot benchmarks (split ML, periodogram, M&M) with the blind receivers' re-encoding check; counts the CRC passes, the wrong ones and the ones the check removes (base lanes on the bm-a/b/c seeds, add lanes pooled)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_re-a.out
PROG=logs/re-a.progress
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
run() {  # tag esn0 frames seed code
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "Split pilots ML, est. phase, pre-MF + CRC search (first pass) + re-encode check" "ML periodogram (FFT + AM), est. phase, pre-MF + CRC search (first pass) + re-encode check" "M&M, est. phase, pre-MF + CRC search (first pass) + re-encode check" --shared-frames --tag $1 --extra-esn0 $2 --min-errors 1000 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run re-R_0p1_C16-m5 -5 25000 18000 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m5-1 -5 25000 88001 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m5-2 -5 25000 88002 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m5-3 -5 25000 88003 "R=0.1,C16" ) &
( run re-R_0p1_C16-m4p5 -4.5 25000 18216 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m4p5-1 -4.5 25000 88217 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m4p5-2 -4.5 25000 88218 "R=0.1,C16" ) &
( run re-R_0p1_C16-m4 -4 25000 18008 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m4-1 -4 25000 88009 "R=0.1,C16" ) &
( run add-re-R_0p1_C16-m4-2 -4 25000 88010 "R=0.1,C16" ) &
( run re-R_2_5_C16-0p5 0.5 25000 18048 "R=2/5,C16" ) &
( run add-re-R_2_5_C16-0p5-1 0.5 25000 88049 "R=2/5,C16" ) &
( run add-re-R_2_5_C16-0p5-2 0.5 25000 88050 "R=2/5,C16" ) &
( run re-R_1_2_C16-2 2 25000 18132 "R=1/2,C16" ) &
( run add-re-R_1_2_C16-2-1 2 25000 88133 "R=1/2,C16" ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
