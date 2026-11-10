#!/bin/bash
# est3 AWGN smoke test: validation checks (chain, layouts, noiseless estimators, references, CRBs), tiny sweeps
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
{
echo "=== validate"; $PY -u est3/run_est.py validate
echo "=== est (tiny)"; $PY -u est3/run_est.py run --snrs -5 5 --chunks 2 --part smoke3 --workers 8 --only M\&M "ML direct" "Joint ML" Candan Moose BLUE Distributed DVB-S2
echo "=== bler (tiny)"; $PY -u est3/run_bler.py --rate 1/10 --snrs -4 --max-frames 400 --chunks 4 --workers 4 --part smoke3 --sources "Genie CFO" M\&M "ML direct" "Joint ML Lh=3" Jacobsen-Candan "Schmidl-Cox / Moose" "BLUE MM99" "Distributed ML 2x64" "Distributed ML 4x32" "DVB-S2 blocks 4x32" "DVB-S2 blocks 8x16"
echo "=== done"
} > logs/run_est3-smoke2.out 2>&1
