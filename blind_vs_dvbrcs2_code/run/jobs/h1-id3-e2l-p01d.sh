#!/bin/bash
# h1-id3-e2l-p01d (2026-11-25, user-approved): H2 (e2l) on tz0-id3 at 0.1 dB, seed 9903, chunks 750..999 of 200000 packets (part 4 of 4; merge locally)
# h1-id3-e2l-p01d (2026-11-25, H2 cell-FFT variant of the H1 / H2 step 1 screen ID 3, arm E2 + h1 "ls_L": "cell"): Es/N0 0.0 dB,
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
  run --seed 9903 --snrs 0.1 --frames 200000 --chunks 750 751 752 753 754 755 756 757 758 759 760 761 762 763 764 765 766 767 768 769 770 771 772 773 774 775 776 777 778 779 780 781 782 783 784 785 786 787 788 789 790 791 792 793 794 795 796 797 798 799 800 801 802 803 804 805 806 807 808 809 810 811 812 813 814 815 816 817 818 819 820 821 822 823 824 825 826 827 828 829 830 831 832 833 834 835 836 837 838 839 840 841 842 843 844 845 846 847 848 849 850 851 852 853 854 855 856 857 858 859 860 861 862 863 864 865 866 867 868 869 870 871 872 873 874 875 876 877 878 879 880 881 882 883 884 885 886 887 888 889 890 891 892 893 894 895 896 897 898 899 900 901 902 903 904 905 906 907 908 909 910 911 912 913 914 915 916 917 918 919 920 921 922 923 924 925 926 927 928 929 930 931 932 933 934 935 936 937 938 939 940 941 942 943 944 945 946 947 948 949 950 951 952 953 954 955 956 957 958 959 960 961 962 963 964 965 966 967 968 969 970 971 972 973 974 975 976 977 978 979 980 981 982 983 984 985 986 987 988 989 990 991 992 993 994 995 996 997 998 999 --dump-lite --lite-ops --sps "$S_X" --part h1-id3-e2l-p01d
  date
  echo "ALL DONE" ) > logs/run_h1-id3-e2l-p01d.out 2>&1
