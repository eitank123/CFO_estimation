#!/bin/bash
# add5-f: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-f.out
PROG=logs/add5-f.progress
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
( run add5-p512c16-sqf-m1-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5125; run add5-p512c16-sqfull-m0p5-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5168 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5126; run add5-p512c16-sqfull-m0p5-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5169 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5127; run add5-p512c16-sqfull-m0p5-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5170 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5128; run add5-p512c16-sqfull-m0p5-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5171 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5129; run add5-p512c16-sqfull-m0p5-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5172 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5130; run add5-p512c16-sqfull-m0p5-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5173 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5131; run add5-p512c16-sqfull-m0p5-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5174 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5132; run add5-p512c16-sqfull-m0p5-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5175 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5133; run add5-p512c16-sqfull-m0p5-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5176 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5134; run add5-p512c16-sqfull-m0p5-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5177 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5135; run add5-p512c16-sqfull-m0p5-13 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5178 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 3423500 5136; run add5-p512c16-sqfull-m0p5-14 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5179 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5137; run add5-p1024c16-v2full-m2p5-6 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5249 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5138; run add5-p1024c16-v2full-m2p5-7 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5250 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5139; run add5-p1024c16-v2full-m2p5-8 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5251 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5140; run add5-p1024c16-v2full-m2p5-9 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5252 ) &   # ~2.2 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
