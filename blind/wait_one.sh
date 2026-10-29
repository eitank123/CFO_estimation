#!/bin/bash
# Exit as soon as one job not yet listed in blind/handled.txt has finished (EVAL DONE) or failed.
cd "$(dirname "$0")/.."
touch blind/handled.txt
while true; do
  for f in logs/run_b25-*.out logs/run_pv-*.out logs/run_pe-*.out logs/run_ec-*.out logs/run_ep-*.out logs/run_ev-*.out logs/run_e3-*.out logs/run_f7-*.out logs/run_g8-*.out logs/run_h9-*.out logs/run_i5-*.out logs/run_j6-*.out logs/run_k7-*.out logs/run_l8-*.out logs/run_nn-*.out logs/run_m9-*.out logs/run_pb-*.out logs/run_rk-*.out logs/run_rn-*.out logs/run_fx-*.out logs/run_rn2-*.out logs/run_fx2-*.out logs/run_fx3-*.out logs/run_pf-*.out logs/run_bx-*.out logs/run_rh-*.out logs/run_pf2-*.out logs/run_rl-*.out logs/run_pf3-*.out logs/run_rm-*.out; do
    [ -f "$f" ] || continue
    j=$(basename "$f" .out); j=${j#run_}
    grep -qx "$j" blind/handled.txt && continue
    if grep -q 'EVAL DONE' "$f" || grep -qE 'Traceback|FAILED' "$f"; then
      echo "$j" >> blind/handled.txt
      echo "finished: $j"; grep -cE 'Traceback|FAILED' "$f" | sed 's/^/failures: /'; exit 0
    fi
  done
  sleep 60
done
