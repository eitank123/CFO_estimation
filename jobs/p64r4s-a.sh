#!/bin/bash
# p64r4s-a: 64-symbol preamble BLER (r4snn), lowrate study, 1024 symbols, est-len 64; one chunk per lane
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_p64r4s-a.out
PROG=logs/p64r4s-a.progress
TOTAL=64
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
run() {  # tag code source esn0 frames seed
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --est-len 64 --codes "$2" --sources "$3" --tag $1 --extra-esn0 $4 --min-errors 100 --max-frames $5 --seed $6 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run addp64r4s-snnf-10p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 10.0 300000 67000; run addp64r4s-snnf-5p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 5.0 300000 67016; run addp64r4s-snnf-1p5-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 300000 67032; run addp64r4s-snn-8p0-2 "R=1/4,C16" "Split pilots NN, quarter" 8.0 300000 67048 ) &
( run addp64r4s-snnf-10p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 10.0 300000 67001; run addp64r4s-snnf-5p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 5.0 300000 67017; run addp64r4s-snnf-1p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 300000 67033; run addp64r4s-snn-7p0-0 "R=1/4,C16" "Split pilots NN, quarter" 7.0 300000 67049 ) &
( run addp64r4s-snnf-10p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 10.0 300000 67002; run addp64r4s-snnf-4p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 300000 67018; run addp64r4s-snnf-1p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 300000 67034; run addp64r4s-snn-7p0-1 "R=1/4,C16" "Split pilots NN, quarter" 7.0 300000 67050 ) &
( run addp64r4s-snnf-9p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 9.0 300000 67003; run addp64r4s-snnf-4p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 300000 67019; run addp64r4s-snnf-1p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.0 300000 67035; run addp64r4s-snn-7p0-2 "R=1/4,C16" "Split pilots NN, quarter" 7.0 300000 67051 ) &
( run addp64r4s-snnf-9p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 9.0 300000 67004; run addp64r4s-snnf-4p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 300000 67020; run addp64r4s-snnf-0p5-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 300000 67036; run addp64r4s-snn-6p0-0 "R=1/4,C16" "Split pilots NN, quarter" 6.0 300000 67052 ) &
( run addp64r4s-snnf-9p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 9.0 300000 67005; run addp64r4s-snnf-3p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 300000 67021; run addp64r4s-snnf-0p5-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 300000 67037; run addp64r4s-snn-6p0-1 "R=1/4,C16" "Split pilots NN, quarter" 6.0 300000 67053 ) &
( run addp64r4s-snnf-8p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 8.0 300000 67006; run addp64r4s-snnf-3p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 300000 67022; run addp64r4s-snnf-0p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 300000 67038; run addp64r4s-snn-6p0-2 "R=1/4,C16" "Split pilots NN, quarter" 6.0 300000 67054 ) &
( run addp64r4s-snnf-8p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 8.0 300000 67007; run addp64r4s-snnf-3p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 3.0 300000 67023; run addp64r4s-snnf-0p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 300000 67039; run addp64r4s-snn-5p0-0 "R=1/4,C16" "Split pilots NN, quarter" 5.0 300000 67055 ) &
( run addp64r4s-snnf-8p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 8.0 300000 67008; run addp64r4s-snnf-2p5-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 300000 67024; run addp64r4s-snn-10p0-0 "R=1/4,C16" "Split pilots NN, quarter" 10.0 300000 67040; run addp64r4s-snn-4p0-0 "R=1/4,C16" "Split pilots NN, quarter" 4.0 300000 67056 ) &
( run addp64r4s-snnf-7p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 7.0 300000 67009; run addp64r4s-snnf-2p5-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 300000 67025; run addp64r4s-snn-10p0-1 "R=1/4,C16" "Split pilots NN, quarter" 10.0 300000 67041; run addp64r4s-snn-3p0-0 "R=1/4,C16" "Split pilots NN, quarter" 3.0 300000 67057 ) &
( run addp64r4s-snnf-7p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 7.0 300000 67010; run addp64r4s-snnf-2p5-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 300000 67026; run addp64r4s-snn-10p0-2 "R=1/4,C16" "Split pilots NN, quarter" 10.0 300000 67042; run addp64r4s-snn-2p5-0 "R=1/4,C16" "Split pilots NN, quarter" 2.5 300000 67058 ) &
( run addp64r4s-snnf-7p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 7.0 300000 67011; run addp64r4s-snnf-2p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 300000 67027; run addp64r4s-snn-9p0-0 "R=1/4,C16" "Split pilots NN, quarter" 9.0 300000 67043; run addp64r4s-snn-2p0-0 "R=1/4,C16" "Split pilots NN, quarter" 2.0 300000 67059 ) &
( run addp64r4s-snnf-6p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 6.0 300000 67012; run addp64r4s-snnf-2p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 300000 67028; run addp64r4s-snn-9p0-1 "R=1/4,C16" "Split pilots NN, quarter" 9.0 300000 67044; run addp64r4s-snn-1p5-0 "R=1/4,C16" "Split pilots NN, quarter" 1.5 300000 67060 ) &
( run addp64r4s-snnf-6p0-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 6.0 300000 67013; run addp64r4s-snnf-2p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.0 300000 67029; run addp64r4s-snn-9p0-2 "R=1/4,C16" "Split pilots NN, quarter" 9.0 300000 67045; run addp64r4s-snn-1p0-0 "R=1/4,C16" "Split pilots NN, quarter" 1.0 300000 67061 ) &
( run addp64r4s-snnf-6p0-2 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 6.0 300000 67014; run addp64r4s-snnf-1p5-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 300000 67030; run addp64r4s-snn-8p0-0 "R=1/4,C16" "Split pilots NN, quarter" 8.0 300000 67046; run addp64r4s-snn-0p5-0 "R=1/4,C16" "Split pilots NN, quarter" 0.5 300000 67062 ) &
( run addp64r4s-snnf-5p0-0 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 5.0 300000 67015; run addp64r4s-snnf-1p5-1 "R=1/4,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 300000 67031; run addp64r4s-snn-8p0-1 "R=1/4,C16" "Split pilots NN, quarter" 8.0 300000 67047; run addp64r4s-snn-0p0-0 "R=1/4,C16" "Split pilots NN, quarter" 0.0 300000 67063 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
