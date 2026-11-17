#!/bin/bash
# fs-nbv: NB-IoT NPUSCH F1 ideal-sync validation (run_fullsys_da --sys nbiot --variant ideal: f = 0, genie N0; LTE turbo
# max-log x 0.75, 8 it, CRC-24A early stop). (1) the code-only AFF3CT configuration aff3ct-K2048 = Turbo_N4096_K2048_
# BCJR_i8_ref_LTE (K 2048 incl. CRC-24A, puncturing 11,10,01, BPSK, crc_start 2) at AFF3CT Eb/N0 0.8 .. 1.7 dB
# (Es/N0 = Eb/N0 - 3.074), seed 51: pass = within about 0.1 dB of the reference FER (ref_aff3ct_fer per point).
# (2) the 4 main formats (nb208, nb328, nb808, nb1000), seed 50 = fs-nbda / fs-nbda55 (paired packets) and = the
# fs-nbpg payloads. Grids are first guesses around the expected PER 1e-2 point (check fs-nbsmoke first). Memory: 16Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --sys nbiot --variant ideal --frames 1000000 --max-err 300 --workers 16"
( $R --nbfmt aff3ct-K2048 --snrs -2.27 -2.17 -2.07 -1.97 -1.87 -1.77 -1.67 -1.57 -1.47 -1.37 --seed 51 --part fs-nbv-aff
  $R --nbfmt nb208 --snrs -4.50 -4.25 -4.00 -3.75 -3.50 -3.25 -3.00 -2.75 -2.50 -2.25 -2.00 -1.75 -1.50 -1.25 -1.00 --seed 50 --part fs-nbv-208
  $R --nbfmt nb328 --snrs -2.50 -2.25 -2.00 -1.75 -1.50 -1.25 -1.00 -0.75 -0.50 -0.25 0.00 0.25 0.50 0.75 1.00 --seed 50 --part fs-nbv-328
  $R --nbfmt nb808 --snrs 0.25 0.50 0.75 1.00 1.25 1.50 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 --seed 50 --part fs-nbv-808
  $R --nbfmt nb1000 --snrs 1.75 2.00 2.25 2.50 2.75 3.00 3.25 3.50 3.75 4.00 4.25 4.50 4.75 5.00 5.25 --seed 50 --part fs-nbv-1000
  echo "ALL DONE" ) > logs/run_fs-nbv.out 2>&1
