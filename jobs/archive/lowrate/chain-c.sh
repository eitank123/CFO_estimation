#!/bin/bash
# chain-c: 3 simulations from the add2 / lr12 / nn2 queue specs, commands verbatim.
# Lanes run side by side; inside a lane the simulations run one after another. A failure is logged
# and the lane goes on. Progress: logs/chain-c.progress ('done total elapsed_s'), log: logs/run_chain-c.out
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_chain-c.out
PROG=logs/chain-c.progress
TOTAL=3
T0=$(date +%s)
mkdir -p logs lowrate/logs
: > "$PROG"
echo "$(date "+%F %T") chain start, $TOTAL simulations" > "$LOG"
finish() {  # name status
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done   # portable lock: lanes finish independently
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}

sim_nn2_light64() {  # expected ~40 min
  echo "$(date "+%F %T") START nn2-light64" >> "$LOG"
  if $PY -u train_cfo_v2.py --name light64 --arch light --hidden 64 32 > logs/run_nn2-light64.out 2>&1; then finish nn2-light64 DONE; else finish nn2-light64 "FAILED (exit $?, see logs/run_nn2-light64.out)"; fi
}
sim_nn2_light32() {  # expected ~40 min
  echo "$(date "+%F %T") START nn2-light32" >> "$LOG"
  if $PY -u train_cfo_v2.py --name light32 --arch light --hidden 32 16 > logs/run_nn2-light32.out 2>&1; then finish nn2-light32 DONE; else finish nn2-light32 "FAILED (exit $?, see logs/run_nn2-light32.out)"; fi
}
sim_nn2_light16() {  # expected ~40 min
  echo "$(date "+%F %T") START nn2-light16" >> "$LOG"
  if $PY -u train_cfo_v2.py --name light16 --arch light --hidden 16 > logs/run_nn2-light16.out 2>&1; then finish nn2-light16 DONE; else finish nn2-light16 "FAILED (exit $?, see logs/run_nn2-light16.out)"; fi
}

( sim_nn2_light64; sim_nn2_light32; sim_nn2_light16 ) &   # lane 1: ~120 min
wait
echo "EVAL DONE: all $TOTAL simulations finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
