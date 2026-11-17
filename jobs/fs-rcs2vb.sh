#!/bin/bash
# fs-rcs2vb: paired decoder / interleaver variants: N3008 at AFF3CT Eb/N0 1.4, 1.6 (seed 31 = fs-rcs2a3008 packets): 'en', 'en-natswap', log-MAP, sf 0.7 (TR), no early stop; ID 13 at -0.80, -0.60 (seed 13 = fs-rcs2v13): 'en', sf 0.7
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.4 1.6 --itl en --frames 1000000 --max-err 300 --seed 31 --workers 16 --part fs-rcs2vb-en
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.4 1.6 --itl en-natswap --frames 1000000 --max-err 300 --seed 31 --workers 16 --part fs-rcs2vb-ens
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.4 1.6 --algo logmap --sf 1.0 --frames 1000000 --max-err 300 --seed 31 --workers 16 --part fs-rcs2vb-lm
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.4 1.6 --sf 0.7 --frames 1000000 --max-err 300 --seed 31 --workers 16 --part fs-rcs2vb-sf07
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.4 1.6 --no-early-stop --frames 1000000 --max-err 300 --seed 31 --workers 16 --part fs-rcs2vb-noes
  $PY -u fullsys/run_rcs2.py --wf 13 --snrs -0.80 -0.60 --itl en --frames 1000000 --max-err 300 --seed 13 --workers 16 --part fs-rcs2vb13-en
  $PY -u fullsys/run_rcs2.py --wf 13 --snrs -0.80 -0.60 --sf 0.7 --frames 1000000 --max-err 300 --seed 13 --workers 16 --part fs-rcs2vb13-sf07
  echo "ALL DONE" ) > logs/run_fs-rcs2vb.out 2>&1
