#!/bin/bash
# est3 smoke test: validation checks, tiny training, tiny estimation sweep, tiny BLER (CPU)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results est3/models
{
echo "=== validate"; $PY -u est3/run_est.py validate
echo "=== train (tiny)"; $PY -u est3/nn.py train --what cluster cnn-cr cnn-reg --device cpu --epochs 1 --steps 30 --batch 256 --workers 4 --cluster-per-value 2 --cluster-epochs 2
echo "=== est (tiny)"; $PY -u est3/run_est.py run --channel awgn rician --snrs -5 5 --chunks 2 --part smoke --workers 8
echo "=== bler (tiny)"; $PY -u est3/run_bler.py --channel rician --rate 1/10 --snrs -3 --max-frames 400 --chunks 4 --workers 4 --part smoke1
$PY -u est3/run_bler.py --channel awgn --rate 1/2 --snrs 2 --max-frames 400 --chunks 4 --workers 4 --part smoke2
echo "=== done"
} > logs/run_est3-smoke.out 2>&1
