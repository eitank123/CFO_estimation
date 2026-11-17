#!/bin/bash
# fs-blsmoke: smoke test of run_blind_fs (blind on the rate-matched formats): --selfcheck (3 packets at 30 dB per format), then 100 packets per format at a high-BLER point (search, rescue, CRC-32 failures) with every code path: nopi (14s), bpsk_sq and the 4th-power BPSK arm (42b, vde), F5 on with the fz_mask (13, 14s), spec11 on (vde), checkpoint NN off (3), codeword checkpoints (42q), rho table / min arms, --calib seeds, cfo-max 0.005, --dump
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
S="--frames 100 --max-err 100 --batch 10 --sub 10 --workers 16"
( $PY -u fullsys/run_blind_fs.py --selfcheck
  $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -1.2 $S --seed 990 --dump --part fs-blsmoke-13
  $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -1.2 $S --seed 990 --fzstop adopted --part fs-blsmoke-13fz
  $PY -u fullsys/run_blind_fs.py --fmt id14s --snrs 1.2 $S --seed 991 --fzstop adopted --dump --part fs-blsmoke-14s
  $PY -u fullsys/run_blind_fs.py --fmt id14p --snrs 1.2 $S --seed 991 --rho table --part fs-blsmoke-14p
  $PY -u fullsys/run_blind_fs.py --fmt id3 --snrs -0.8 $S --seed 992 --cknn off --rho min --part fs-blsmoke-3
  $PY -u fullsys/run_blind_fs.py --fmt id42b --snrs -4.2 $S --seed 993 --dump --part fs-blsmoke-42b
  $PY -u fullsys/run_blind_fs.py --fmt id42b --snrs -4.2 $S --seed 993 --bpsk-phase 4th --part fs-blsmoke-42b4
  $PY -u fullsys/run_blind_fs.py --fmt id42q --snrs -1.2 $S --seed 993 --ck codeword --calib --part fs-blsmoke-42q
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --snrs -4.4 $S --seed 994 --spec adopted --dump --part fs-blsmoke-vde
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --snrs -4.4 $S --seed 994 --bpsk-phase 4th --part fs-blsmoke-vde4
  $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -1.2 $S --seed 995 --cfo-max 0.005 --part fs-blsmoke-13n
  echo "ALL DONE" ) > logs/run_fs-blsmoke.out 2>&1
