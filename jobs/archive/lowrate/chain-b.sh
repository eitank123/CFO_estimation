#!/bin/bash
# chain-b: 7 simulations from the add2 / lr12 / nn2 queue specs, commands verbatim.
# Lanes run side by side; inside a lane the simulations run one after another. A failure is logged
# and the lane goes on. Progress: logs/chain-b.progress ('done total elapsed_s'), log: logs/run_chain-b.out
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_chain-b.out
PROG=logs/chain-b.progress
TOTAL=7
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

sim_add2_r01c16_nns_m2p5() {  # expected ~108 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m2p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m2p5 --extra-esn0 -2.5 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m2p5.out 2>&1; then finish add2-r01c16-nns-m2p5 DONE; else finish add2-r01c16-nns-m2p5 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m2p5.out)"; fi
}
sim_add2_r01c16_nns_m2() {  # expected ~84 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m2" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m2 --extra-esn0 -2 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m2.out 2>&1; then finish add2-r01c16-nns-m2 DONE; else finish add2-r01c16-nns-m2 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m2.out)"; fi
}
sim_add2_r01c16_nns_m3() {  # expected ~50 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m3" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m3 --extra-esn0 -3 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m3.out 2>&1; then finish add2-r01c16-nns-m3 DONE; else finish add2-r01c16-nns-m3 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m3.out)"; fi
}
sim_add2_r01c16_nns_m3p5() {  # expected ~35 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m3p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m3p5 --extra-esn0 -3.5 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m3p5.out 2>&1; then finish add2-r01c16-nns-m3p5 DONE; else finish add2-r01c16-nns-m3p5 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m3p5.out)"; fi
}
sim_add2_r01c16_nns_m4() {  # expected ~20 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m4" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m4 --extra-esn0 -4 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m4.out 2>&1; then finish add2-r01c16-nns-m4 DONE; else finish add2-r01c16-nns-m4 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m4.out)"; fi
}
sim_add2_r01c16_nns_m1p5_m1() {  # expected ~69 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m1p5-m1" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m1p5-m1 --extra-esn0 -1.5 -1 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m1p5-m1.out 2>&1; then finish add2-r01c16-nns-m1p5-m1 DONE; else finish add2-r01c16-nns-m1p5-m1 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m1p5-m1.out)"; fi
}
sim_add2_r01c16_nns_m0p5_0() {  # expected ~63 min
  echo "$(date "+%F %T") START add2-r01c16-nns-m0p5-0" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-r01c16-nns-m0p5-0 --extra-esn0 -0.5 0 --max-frames 3000000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-r01c16-nns-m0p5-0.out 2>&1; then finish add2-r01c16-nns-m0p5-0 DONE; else finish add2-r01c16-nns-m0p5-0 "FAILED (exit $?, see lowrate/logs/run_add2-r01c16-nns-m0p5-0.out)"; fi
}

( sim_add2_r01c16_nns_m2p5 ) &   # lane 1: ~108 min
( sim_add2_r01c16_nns_m2 ) &   # lane 2: ~84 min
( sim_add2_r01c16_nns_m3 ) &   # lane 3: ~50 min
( sim_add2_r01c16_nns_m3p5; sim_add2_r01c16_nns_m4 ) &   # lane 4: ~55 min
( sim_add2_r01c16_nns_m1p5_m1 ) &   # lane 5: ~69 min
( sim_add2_r01c16_nns_m0p5_0 ) &   # lane 6: ~63 min
wait
echo "EVAL DONE: all $TOTAL simulations finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
