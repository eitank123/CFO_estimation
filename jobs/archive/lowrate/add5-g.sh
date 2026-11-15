#!/bin/bash
# add5-g: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-g.out
PROG=logs/add5-g.progress
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
( run add5-p512c16-sqfull-m1-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5141; run add5-p1024c16-v2full-m2p5-10 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 169000 5253 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5142; run add5-p1024c16-v2full-m3p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5220 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5143; run add5-p1024c16-v2full-m3p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5221 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5144; run add5-p1024c16-v2full-m3p5-2 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5222 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5145; run add5-p1024c16-v2full-m3p5-3 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5223 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5146; run add5-p1024c16-v2full-m3p5-4 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5224 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5147; run add5-p1024c16-v2full-m3p5-5 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5225 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5148; run add5-p1024c16-v2full-m3p5-6 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5226 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5149; run add5-p1024c16-v2full-m3p5-7 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 106000 5227 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-13 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5150; run add5-p512c16-sqfull-m0p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5165 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1-14 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 3200000 5151; run add5-p512c16-sqfull-m0p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -0.5 3200000 5166 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5152; run add5-p1024c16-v2full-m1-0 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5277 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5153; run add5-p1024c16-v2full-m1-1 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5278 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5154; run add5-p1024c16-v2full-m1-2 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5279 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5155; run add5-p1024c16-v2full-m1-3 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5280 ) &   # ~2.2 h
( run add5-p512c16-sqf-m0p5-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 3423500 5156; run add5-p1024c16-v2full-m1-4 1024 "R=0.1,C16" "NN v2 + CRC search" -1 366000 5281 ) &   # ~2.2 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
