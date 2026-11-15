#!/bin/bash
# p64r4-b: 64-symbol preamble BLER (r4), lowrate study, 1024 symbols, est-len 64; one chunk per lane
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_p64r4-b.out
PROG=logs/p64r4-b.progress
TOTAL=55
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

( run addp64r4-mmf-10p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 10.0 300000 65001; run addp64r4-nnf-5p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 5.0 300000 65033; run addp64r4-nnf-1p5-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 1.5 300000 65065; run addp64r4-mm-3p0-0 "R=1/4,C16" "M&M" 3.0 300000 65097 ) &
( run addp64r4-nnf-10p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 10.0 300000 65003; run addp64r4-nnf-5p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 5.0 300000 65035; run addp64r4-mmf-1p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 1.0 300000 65067; run addp64r4-mm-2p0-0 "R=1/4,C16" "M&M" 2.0 300000 65099 ) &
( run addp64r4-nnf-10p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 10.0 300000 65005; run addp64r4-mmf-4p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 4.0 300000 65037; run addp64r4-nnf-1p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 1.0 300000 65069; run addp64r4-genie-1p0-0 "R=1/4,C16" "Genie (known CFO)" 1.0 300000 65101 ) &
( run addp64r4-mmf-9p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 9.0 300000 65007; run addp64r4-nnf-4p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 4.0 300000 65039; run addp64r4-nnf-1p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 1.0 300000 65071; run addp64r4-mm-1p0-0 "R=1/4,C16" "M&M" 1.0 300000 65103 ) &
( run addp64r4-nnf-9p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 9.0 300000 65009; run addp64r4-nnf-4p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 4.0 300000 65041; run addp64r4-mmf-0p5-1 "R=1/4,C16" "M&M + CRC search (first pass)" 0.5 300000 65073; run addp64r4-genie-0p5-1 "R=1/4,C16" "Genie (known CFO)" 0.5 300000 65105 ) &
( run addp64r4-nnf-9p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 9.0 300000 65011; run addp64r4-mmf-3p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 3.0 300000 65043; run addp64r4-nnf-0p5-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 0.5 300000 65075; run addp64r4-genie-0p0-0 "R=1/4,C16" "Genie (known CFO)" 0.0 300000 65107 ) &
( run addp64r4-mmf-8p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 8.0 300000 65013; run addp64r4-nnf-3p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 3.0 300000 65045; run addp64r4-mmf-0p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 0.0 300000 65077; run addp64r4-mm-0p0-0 "R=1/4,C16" "M&M" 0.0 300000 65109 ) &
( run addp64r4-nnf-8p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 8.0 300000 65015; run addp64r4-nnf-3p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 3.0 300000 65047; run addp64r4-nnf-0p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 0.0 300000 65079 ) &
( run addp64r4-nnf-8p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 8.0 300000 65017; run addp64r4-mmf-2p5-1 "R=1/4,C16" "M&M + CRC search (first pass)" 2.5 300000 65049; run addp64r4-mm-10p0-1 "R=1/4,C16" "M&M" 10.0 300000 65081 ) &
( run addp64r4-mmf-7p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 7.0 300000 65019; run addp64r4-nnf-2p5-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 2.5 300000 65051; run addp64r4-mm-9p0-0 "R=1/4,C16" "M&M" 9.0 300000 65083 ) &
( run addp64r4-nnf-7p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 7.0 300000 65021; run addp64r4-nnf-2p5-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 2.5 300000 65053; run addp64r4-mm-9p0-2 "R=1/4,C16" "M&M" 9.0 300000 65085 ) &
( run addp64r4-nnf-7p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 7.0 300000 65023; run addp64r4-mmf-2p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 2.0 300000 65055; run addp64r4-mm-8p0-1 "R=1/4,C16" "M&M" 8.0 300000 65087 ) &
( run addp64r4-mmf-6p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 6.0 300000 65025; run addp64r4-nnf-2p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 2.0 300000 65057; run addp64r4-mm-7p0-0 "R=1/4,C16" "M&M" 7.0 300000 65089 ) &
( run addp64r4-nnf-6p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 6.0 300000 65027; run addp64r4-nnf-2p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 2.0 300000 65059; run addp64r4-mm-7p0-2 "R=1/4,C16" "M&M" 7.0 300000 65091 ) &
( run addp64r4-nnf-6p0-2 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 6.0 300000 65029; run addp64r4-mmf-1p5-1 "R=1/4,C16" "M&M + CRC search (first pass)" 1.5 300000 65061; run addp64r4-mm-6p0-1 "R=1/4,C16" "M&M" 6.0 300000 65093 ) &
( run addp64r4-mmf-5p0-1 "R=1/4,C16" "M&M + CRC search (first pass)" 5.0 300000 65031; run addp64r4-nnf-1p5-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 1.5 300000 65063; run addp64r4-mm-5p0-0 "R=1/4,C16" "M&M" 5.0 300000 65095 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
