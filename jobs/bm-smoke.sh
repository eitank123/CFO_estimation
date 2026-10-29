#!/bin/bash
# bm-smoke: smoke of the literature CFO benchmarks (polar_ber_experiment BENCH), 4000 frames per point
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_bm-smoke.out
PROG=logs/bm-smoke.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=3
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "M&M, est. phase, pre-MF + CRC search (first pass)" "M&M + ML Newton, est. phase, pre-MF + CRC search (first pass)" "ML periodogram (FFT + AM), est. phase, pre-MF + CRC search (first pass)" "M&M + ML Newton, est. phase, pre-MF + code-aided EM" "M&M + ML Newton, est. phase, pre-MF + code-aided EM + CRC search (first pass)" --shared-frames --tag $1 --extra-esn0 $2 --min-errors $6 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
# tag "aaa-..." sorts before the real parts, so a --merge lets the full runs override these points
( run aaa-bmsmoke-R_0p1_C16 -5 4000 18000 "R=0.1,C16" 100000000 ) &
( run aaa-bmsmoke-R_2_5_C16 0.5 4000 18048 "R=2/5,C16" 100000000 ) &
( run aaa-bmsmoke-R_1_2_C16 2 4000 18132 "R=1/2,C16" 100000000 ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
