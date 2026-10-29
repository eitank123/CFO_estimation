#!/bin/bash
# pm-hr: R=3/5, 2/3, 3/4. 128-pilot split NN + CRC search with and without the pre-MF correction, and the pre-MF genie, on the
# same frames (--shared-frames); study CFO_STUDY=premf_split (results in premf_split/), one lane per (SNR, seed).
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=premf_split
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_pm-hr.out
PROG=logs/pm-hr.progress
TOTAL=16
T0=$(date +%s)
mkdir -p logs premf_split/logs
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL chunks" > "$LOG"
finish() {  # name status
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag esn0 frames seed code
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "Split pilots NN, quarter + CRC search (first pass)" "Split pilots NN, quarter, pre-MF correction + CRC search (first pass)" "Genie (known CFO), pre-MF correction" --shared-frames --tag $1 --extra-esn0 $2 --min-errors 100 --max-frames $3 --seed $4 --workers 1 > premf_split/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add-pm-hr-3_5-3p5 3.5 1000000 17600 "R=3/5,C16" ) &
( run add-pm-hr-3_5-4 4 1000000 17608 "R=3/5,C16" ) &
( run add-pm-hr-3_5-4p5 4.5 1000000 17616 "R=3/5,C16" ) &
( run add-pm-hr-3_5-5 5 1000000 17624 "R=3/5,C16" ) &
( run add-pm-hr-3_5-5p5 5.5 1000000 17632 "R=3/5,C16" ) &
( run add-pm-hr-2_3-4 4 1000000 17640 "R=2/3,C16" ) &
( run add-pm-hr-2_3-4p5 4.5 1000000 17648 "R=2/3,C16" ) &
( run add-pm-hr-2_3-5 5 1000000 17656 "R=2/3,C16" ) &
( run add-pm-hr-2_3-5p5 5.5 1000000 17664 "R=2/3,C16" ) &
( run add-pm-hr-2_3-6 6 1000000 17672 "R=2/3,C16" ) &
( run add-pm-hr-3_4-5 5 1000000 17680 "R=3/4,C16" ) &
( run add-pm-hr-3_4-5p5 5.5 1000000 17688 "R=3/4,C16" ) &
( run add-pm-hr-3_4-6 6 1000000 17696 "R=3/4,C16" ) &
( run add-pm-hr-3_4-6p5 6.5 1000000 17704 "R=3/4,C16" ) &
( run add-pm-hr-3_4-7 7 1000000 17712 "R=3/4,C16" ) &
( run add-pm-hr-3_4-7p5 7.5 1000000 17720 "R=3/4,C16" ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
