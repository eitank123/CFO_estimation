#!/bin/bash
# h1-id3-e2l-p01c (2026-11-25, user-approved): H2 (e2l) on tz0-id3 at 0.1 dB, seed 9903, chunks 500..749 of 200000 packets (part 3 of 4; merge locally)
# h1-id3-e2l-p01c (2026-11-25, H2 cell-FFT variant of the H1 / H2 step 1 screen ID 3, arm E2 + h1 "ls_L": "cell"): Es/N0 0.0 dB,
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
  run --seed 9903 --snrs 0.1 --frames 200000 --chunks 500 501 502 503 504 505 506 507 508 509 510 511 512 513 514 515 516 517 518 519 520 521 522 523 524 525 526 527 528 529 530 531 532 533 534 535 536 537 538 539 540 541 542 543 544 545 546 547 548 549 550 551 552 553 554 555 556 557 558 559 560 561 562 563 564 565 566 567 568 569 570 571 572 573 574 575 576 577 578 579 580 581 582 583 584 585 586 587 588 589 590 591 592 593 594 595 596 597 598 599 600 601 602 603 604 605 606 607 608 609 610 611 612 613 614 615 616 617 618 619 620 621 622 623 624 625 626 627 628 629 630 631 632 633 634 635 636 637 638 639 640 641 642 643 644 645 646 647 648 649 650 651 652 653 654 655 656 657 658 659 660 661 662 663 664 665 666 667 668 669 670 671 672 673 674 675 676 677 678 679 680 681 682 683 684 685 686 687 688 689 690 691 692 693 694 695 696 697 698 699 700 701 702 703 704 705 706 707 708 709 710 711 712 713 714 715 716 717 718 719 720 721 722 723 724 725 726 727 728 729 730 731 732 733 734 735 736 737 738 739 740 741 742 743 744 745 746 747 748 749 --dump-lite --lite-ops --sps "$S_X" --part h1-id3-e2l-p01c
  date
  echo "ALL DONE" ) > logs/run_h1-id3-e2l-p01c.out 2>&1
