#!/bin/bash
# add7-a: split-pilot NN (1024, conv + lobe classifier), with and without the CRC search ("add6" parts, own seeds); 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add7-a.out
PROG=logs/add7-a.progress
TOTAL=33
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
( run add7-p1024c16-snnf-m3p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -3.0 544750 7030 ) &   # ~0.50 h
( run add7-p1024c16-snnf-m3p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -3.0 544750 7029 ) &   # ~0.50 h
( run add7-p1024c16-snnf-m0p5-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -0.5 770250 7016 ) &   # ~0.50 h
( run add7-p1024c16-snnf-m0p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -0.5 770250 7015 ) &   # ~0.50 h
( run add7-p1024c16-snnf-m1p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.0 682000 7018 ) &   # ~0.47 h
( run add7-p1024c16-snnf-m1p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.0 682000 7017 ) &   # ~0.47 h
( run add7-p1024c16-snnf-m2p5-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.5 396167 7028; run add7-p1024c16-snn-m4p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -4.5 2000 7010; run add7-p1024c16-snn-m2p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -2.5 2000 7006; run add7-p1024c16-snn-m0p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -0.5 2000 7001 ) &   # ~0.34 h
( run add7-p1024c16-snnf-m2p5-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.5 396167 7027; run add7-p1024c16-snn-m4p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -4.0 2000 7009; run add7-p1024c16-snn-m2p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -2.0 2000 7005; run add7-p1024c16-snn-0p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter" 0.0 2000 7004 ) &   # ~0.34 h
( run add7-p1024c16-snnf-m2p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.5 396167 7026; run add7-p1024c16-snn-m3p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -3.5 2000 7008; run add7-p1024c16-snn-m1p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -1.5 2000 7003 ) &   # ~0.34 h
( run add7-p1024c16-snnf-0p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 543500 7014; run add7-p1024c16-snnf-m4p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -4.5 125500 7032 ) &   # ~0.49 h
( run add7-p1024c16-snnf-0p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 543500 7013; run add7-p1024c16-snnf-m5p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -5.0 17500 7025 ) &   # ~0.36 h
( run add7-p1024c16-snnf-0p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 543500 7012; run add7-p1024c16-snn-m5p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -5.0 2000 7011; run add7-p1024c16-snn-m3p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -3.0 2000 7007; run add7-p1024c16-snn-m1p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter" -1.0 2000 7002 ) &   # ~0.34 h
( run add7-p1024c16-snnf-m1p5-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.5 456334 7021; run add7-p1024c16-snnf-m2p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.0 425167 7022 ) &   # ~0.67 h
( run add7-p1024c16-snnf-m1p5-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.5 456334 7020; run add7-p1024c16-snnf-m3p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -3.5 300000 7031 ) &   # ~0.63 h
( run add7-p1024c16-snnf-m1p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.5 456334 7019; run add7-p1024c16-snnf-m4p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -4.0 240000 7033 ) &   # ~0.60 h
( run add7-p1024c16-snnf-m2p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.0 425167 7024; run add7-p1024c16-snnf-m2p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.0 425167 7023 ) &   # ~0.67 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
