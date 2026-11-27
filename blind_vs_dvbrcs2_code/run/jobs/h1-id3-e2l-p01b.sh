#!/bin/bash
# h1-id3-e2l-p01b (2026-11-25, user-approved): H2 (e2l) on tz0-id3 at 0.1 dB, seed 9903, chunks 250..499 of 200000 packets (part 2 of 4; merge locally)
# h1-id3-e2l-p01b (2026-11-25, H2 cell-FFT variant of the H1 / H2 step 1 screen ID 3, arm E2 + h1 "ls_L": "cell"): Es/N0 0.0 dB,
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
  run --seed 9903 --snrs 0.1 --frames 200000 --chunks 250 251 252 253 254 255 256 257 258 259 260 261 262 263 264 265 266 267 268 269 270 271 272 273 274 275 276 277 278 279 280 281 282 283 284 285 286 287 288 289 290 291 292 293 294 295 296 297 298 299 300 301 302 303 304 305 306 307 308 309 310 311 312 313 314 315 316 317 318 319 320 321 322 323 324 325 326 327 328 329 330 331 332 333 334 335 336 337 338 339 340 341 342 343 344 345 346 347 348 349 350 351 352 353 354 355 356 357 358 359 360 361 362 363 364 365 366 367 368 369 370 371 372 373 374 375 376 377 378 379 380 381 382 383 384 385 386 387 388 389 390 391 392 393 394 395 396 397 398 399 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 419 420 421 422 423 424 425 426 427 428 429 430 431 432 433 434 435 436 437 438 439 440 441 442 443 444 445 446 447 448 449 450 451 452 453 454 455 456 457 458 459 460 461 462 463 464 465 466 467 468 469 470 471 472 473 474 475 476 477 478 479 480 481 482 483 484 485 486 487 488 489 490 491 492 493 494 495 496 497 498 499 --dump-lite --lite-ops --sps "$S_X" --part h1-id3-e2l-p01b
  date
  echo "ALL DONE" ) > logs/run_h1-id3-e2l-p01b.out 2>&1
