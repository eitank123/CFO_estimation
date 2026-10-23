#!/bin/bash
# add5-h: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-h.out
PROG=logs/add5-h.progress
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
( run add5-p512c16-sqf-m0p5-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5157; run add5-p1024c16-v2full-m1-5 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5282 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5158; run add5-p1024c16-v2full-m1-6 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5283 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5159; run add5-p1024c16-v2full-m2p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5243 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5160; run add5-p1024c16-v2full-m2p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5244 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5161; run add5-p1024c16-v2full-m2p5-2 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5245 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5162; run add5-p1024c16-v2full-m2p5-3 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5246 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5163; run add5-p1024c16-v2full-m2p5-4 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5247 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5164; run add5-p1024c16-v2full-m2p5-5 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5248 ) &   # ~2.2 h
( run add5-p1024c16-sqfull-0-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 476500 5297; run add5-p512c16-sqf-0-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5190 ) &   # ~2.2 h
( run add5-p1024c16-sqfull-0-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 476500 5298; run add5-p512c16-sqf-0-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5191 ) &   # ~2.2 h
( run add5-p1024c16-sqfull-0-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 476500 5299; run add5-p512c16-sqf-0-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5192 ) &   # ~2.2 h
( run add5-p512c16-sqf-0-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5180; run add5-p512c16-sqf-0-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5185 ) &   # ~2.2 h
( run add5-p512c16-sqf-0-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5181; run add5-p512c16-sqf-0-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5186 ) &   # ~2.2 h
( run add5-p512c16-sqf-0-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5182; run add5-p512c16-sqf-0-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5187 ) &   # ~2.2 h
( run add5-p512c16-sqf-0-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5183; run add5-p512c16-sqf-0-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5188 ) &   # ~2.2 h
( run add5-p512c16-sqf-0-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5184; run add5-p512c16-sqf-0-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 3423500 5189 ) &   # ~2.2 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
