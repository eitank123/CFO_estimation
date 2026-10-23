#!/bin/bash
# add5-e: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-e.out
PROG=logs/add5-e.progress
TOTAL=32
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 1000000 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run add5-p512c16-sqfull-m1p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5104; run add5-p512c16-v2full-m1p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2824000 5119 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5105; run add5-p512c16-v2full-m1p5-1 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2824000 5120 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5106; run add5-p512c16-v2full-m1p5-2 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2824000 5121 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5107; run add5-p512c16-v2full-m1p5-3 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2824000 5122 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5108; run add5-p512c16-v2full-m1p5-4 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2824000 5123 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5109; run add5-p512c11-v2full-m1-0 512 "R=0.1" "NN v2 + CRC search" -1 3098500 5012 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5110; run add5-p1024c16-sqfull-m0p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 306500 5285 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5111; run add5-p1024c16-sqfull-m0p5-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 306500 5286 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5112; run add5-p1024c16-sqfull-m0p5-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 306500 5287 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5113; run add5-p1024c16-sqfull-m0p5-3 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 306500 5288 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5114; run add5-p1024c16-sqfull-m0p5-4 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 306500 5289 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5115; run add5-p1024c16-sqfull-m0p5-5 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 306500 5290 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-13 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5116; run add5-p1024c16-v2full-m1p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 257000 5269 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-14 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5117; run add5-p1024c16-v2full-m1p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 257000 5270 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-15 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5118; run add5-p1024c16-v2full-m1p5-2 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 257000 5271 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5124; run add5-p512c16-sqfull-m0p5-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5167 ) &   # ~2.2 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
