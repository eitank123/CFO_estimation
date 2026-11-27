#!/bin/bash
# h1-id3-e2l-p01a (2026-11-25, user-approved): H2 (e2l) on tz0-id3 at 0.1 dB, seed 9903, chunks 0..249 of 200000 packets (part 1 of 4; merge locally)
# h1-id3-e2l-p01a (2026-11-25, H2 cell-FFT variant of the H1 / H2 step 1 screen ID 3, arm E2 + h1 "ls_L": "cell"): Es/N0 0.0 dB,
# 150000 packets, the SAME packets as h1-id3-e2-p00 (HELD-OUT seed 9903, batch 200, same chunk entropy / packet index; paired for
# the coverage check). "ls_L": "cell" = the receiver-cell LS FFT (ID 3 default L = 4 nf = 8192; "cell" = the smallest power of 2
# with a bin <= the search cell k STEP), |D| folded mod L, linearly interpolated for the peak pick, cells re-scored by the exact
# LS DTFT (ls_rs, H1_DEF default true). --dump-lite --lite-ops. est. wall ~3-5 min (the E2 arm took 84 s); disk ~15 MB
# Baseline A = the exact tz0-id3 args (18 moved bits --twin search:k18z0:rd, z0 arrangement, CRC-24, L 16, twin phase tw_ph iv,
# --twin-fe jt, ck NN ck_nn_fs_id3_c3 via --cknn fmt, --rho scaled, fzstop off, design-snr 0.0, sps final 8 / win 4.5 / vv_p 2),
# no early stop (max-err 1e9). NO repeated twins. H line = the H1 ID 3 screen (K 8, M 1, union off, w (1, 1, 1)).
#   C2 : h1 all (H2: no fast path), ends        E2 : C2 + the fallback
# LS = data/dual_w4_id3_tz0.json (push it with the code, or run jobs/h1-id3-prep.sh first).
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
LS=data/dual_w4_id3_tz0.json
C="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho scaled --spec off --cknn fmt --ck useful --bpsk-phase sq --design ga --charge-all --workers 16"
AF="--list 16 --fmt id3 --design-snr 0.0 --fzstop off --max-err 1000000000 --twin search:k18z0:rd --twin-fe jt"
B='"final": 8, "win": 4.5, "vv_p": 2, "tw_ph": "iv"'
H='"K": 8, "M": 1, "union": false, "w": [1.0, 1.0, 1.0]'
S_X="{$B, \"h1\": {$H, \"fb\": true, \"all\": true, \"ls\": \"$LS\", \"ls_L\": \"cell\"}}"
run() { $PY -u run_blind_fs.py $C $AF "$@" || echo "FAILED: run_blind_fs $*"; }
( date
  test -s $LS || { echo "FAILED: $LS missing (push it, or run jobs/h1-id3-prep.sh)"; exit 2; }
  run --seed 9903 --snrs 0.1 --frames 200000 --chunks 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 --dump-lite --lite-ops --sps "$S_X" --part h1-id3-e2l-p01a
  date
  echo "ALL DONE" ) > logs/run_h1-id3-e2l-p01a.out 2>&1
