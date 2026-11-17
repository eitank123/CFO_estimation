"""
est4: fair pilot-aided competitors to the blind receiver (BLIND_IMPLEMENTATION/testing/results/expected_est4.md), common
parts. Differences from est3:

    pilots  OUTSIDE the packet: the 1024 data symbols carry the whole codeword (N = 2048, CRC-16, est3's interleaver,
            Gray QPSK, exactly as est3/run_bler); the Nk known symbols are EXTRA burst symbols (burst K = 1024 + Nk),
            every symbol with the same Es. Simulated at the per-symbol Es/N0; the energy charged per data symbol is
            energy_db(Nk) = 10 log10((1024 + Nk) / 1024) (plotted SNR = Es/N0 + energy_db)
    layouts (LAYOUTS, burst order):
              pre128     128 known, 1024 data                                         Nk = 128, K = 1152
              split64    64 known, 1024 data, 64 known                                Nk = 128, K = 1152
              rcs13      DVB-RCS2 burst ID 13 scaled (EN 301 545-2 Table A-1): 32 known, 53 x (19 data + 1 pilot),
                         17 data, 31 known; one UW pilot symbol repeated in all 53 pilot fields   Nk = 116, K = 1140
              prepost16  16 known, 1024 data, 16 known (IDs 5 / 15 style, pilotless)  Nk = 32, K = 1056
              none       1024 data (genie)                                            Nk = 0, K = 1024
            est5 (deployed systems, expected_est5.md; appended to LAYOUTS so the est4 noise streams are unchanged):
              vde27      VDE-SAT (ITU-R M.2092-2 A5-2.10): 27 syncword (0-26), 13 data, 1 pilot, 38 x (26 data +
                         1 pilot), 23 data: pilots at 40, 67, 94, ..., 1066 (period 27); one pilot symbol repeated in
                         all pilot fields ((1+j)/sqrt2 in the standard)               Nk = 66, K = 1090, alias 1/27
              dvbs2      DVB-S2 style: 90 PL header (SOF 26 + PLS 64), 512 data, 36 pilot block, 512 data
                                                                                      Nk = 126, K = 1150, lobes 1/575
              ccsds8     CCSDS style: 8 blocks of 16 known, one at each end, data gaps 146 146 147 146 147 146 146
                                                                                      Nk = 128, K = 1152, alias 1/162.3
              viasat16   ViaSat burst: 512 data, 16 midamble UW, 512 data                Nk = 16, K = 1040
              dmrs7      NB-IoT DMRS style: 170 x (3 data, 1 pilot, 3 data), 3 data, 1 pilot, 1 data (pilot mid-slot)
                                                                                      Nk = 171, K = 1195, alias 1/7
              zr32       sparse pilots 1/32 (400ZR-inspired): 33 x (1 pilot + 31 data), 1 data
                                                                                      Nk = 33, K = 1057, alias 1/32
              wifi128    Wi-Fi style: 128 preamble = one random 16-symbol sequence repeated 8 x, 1024 data
                                                                                      Nk = 128, K = 1152, fine lobes 1/64
              mil110     MIL-STD-188-110C App C scaled: 184 preamble, 4 x (256 data + 31 probe)
                                                                                      Nk = 308, K = 1332, alias 1/287
            faithful variants (expected_variants.md, lit_card_sat / space / terr.md; appended after est5, so the est4 /
            est5 noise streams and phase-noise paths are unchanged):
              pre48      Advantech US 7590199 / 7593490: 48 contiguous preamble, 1024 data     Nk = 48, K = 1072
              dvbh90     DVB-S2 PLHEADER only (SOF 26 + PLS 64, CCM), 1024 data (no pilot block: the first one is 1440
                         data symbols after the header)                              Nk = 90, K = 1114, CRC range scan
              sof26      DVB-S2 SOF only (ACM: the PLS is unknown before decoding)   Nk = 26, K = 1050, CRC range scan
              mil110f    MIL-STD-188-110C App C full: 287 preamble (184 + 72 + 31), 4 x (256 data + 31 probe)
                                                                                      Nk = 411, K = 1435, alias 1/287
              cc131      CCSDS 131.2 pilot density: 242 data, 16 pilots, 540 data, 16 pilots, 242 data
                                                                                      Nk = 32, K = 1056, alias 1/556
              asm32      CCSDS 131.0 (2048,1024) LDPC: the same 32-symbol ASM before and after the codeblock
                                                                                      Nk = 64, K = 1088, lobes 1/1056
              wifi320    Wi-Fi legacy: L-STF 10 x 16, L-LTF 32 guard (the last 32 of the 64) + 2 x 64, 1024 data
                                                                                      Nk = 320, K = 1344, fine lobes 1/64
            a FIELD is one contiguous run of known symbols (preamble, a pilot, postamble): the phase models work per field
            alias / lobe spacing 1 / lobe_D(layout) and the number of lobe hypotheses each side lobe_n (run_bler's CRC
            search); est5 layouts only search the lobes whose centre is inside |f| <= MAX_CFO + the window
    chain   est3.common.transmit (= blind_cfo.transmit_full) on the whole burst: Es measured over the burst, + Wiener
            phase noise as blind_cfo (BLIND_PN): per 8-SPS sample increment N(0, 2 pi pn / SPS), zero at the burst
            centre, only if pn > 0; bursts longer than the est4 KMAX (1152) take the est4 path extended outwards at
            both ends by extend_path (its own rng stream), so the est4 path and its RNG draws are unchanged; bursts
            longer than the est5 KMAX_ALL (1332: the variants mil110f, wifi320) continue that path once more
            (KMAX_V, a third stream), so the est5 path is unchanged too
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                                   # noqa: E402
from scipy.signal import fftconvolve                                 # noqa: E402

from est3 import common as C3                                        # noqa: E402  (sets CFO_MAX / POLAR_NSYM)
from txrx_chain import rrc                                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS, LOGS, PLOTS = (os.path.join(HERE, d) for d in ("results", "logs", "plots"))

N_SYM, N_BITS = C3.N_SYM, C3.N_BITS
SPS, SPAN, BETA, DELAY_SYM, MAX_CFO = C3.SPS, C3.SPAN, C3.BETA, C3.DELAY_SYM, C3.MAX_CFO
INTERLEAVER, CODES = C3.INTERLEAVER, C3.CODES
RCS_PRE, RCS_NP, RCS_DP, RCS_TAIL, RCS_POST = 32, 53, 19, 17, 31    # ID 13 scaled: pre, pilots, data per pilot, ...
VDE_SYNC, VDE_NP, VDE_DP, VDE_TAIL = 27, 39, 26, 23                 # VDE-SAT: syncword, pilots, data per pilot, tail
VDE_HEAD = 13                                                       # data between syncword and 1st pilot (pilot at 40)
DVB_HDR, DVB_PB = 90, 36                                            # DVB-S2: PL header, mid-burst pilot block
CC_BL, CC_GAPS = 16, (146, 146, 147, 146, 147, 146, 146)            # CCSDS: block length, data between the 8 blocks
UW_LEN = 16                                                         # ViaSat midamble unique word
DM_NS = 170                                                         # DMRS: full 7-symbol slots (3 data, pilot, 3 data)
ZR_P, ZR_NP = 32, 33                                                # sparse pilots 1/32: pilot period, pilots
WIFI_REP, WIFI_FINE = 16, 64                                        # Wi-Fi: repeat length (coarse lag), fine lag
MIL_PRE, MIL_PROBE, MIL_DATA, MIL_NP = 184, 31, 256, 4              # MIL-110C App C scaled: preamble, probe, data, probes
PRE48 = 48                                                          # Advantech (US 7590199): contiguous preamble
DVB_SOF = 26                                                        # DVB-S2 SOF (ACM: the PLS is unknown before decoding)
MILF_PRE = 287                                                      # MIL-110C App C full preamble (184 + 72 + 31 probe)
CC_P, CC_D = 16, 540                                                # CCSDS 131.2: pilot field, data per pilot field
ASM_LEN = 32                                                        # CCSDS 131.0: 64-bit ASM on QPSK
WIFI_STF, WIFI_GI = 160, 32                                         # Wi-Fi legacy: L-STF 10 x 16, L-LTF guard (+ 2 x 64)

# receiver: (layout, CFO estimator, phase model); the estimators and phase models are in est4/estimators.py
SOURCES = {
    "pre128 ML": ("pre128", "ml128", "const"),            # C3: est3 ML direct (FFT 512 + 2 Newton) on the preamble
    "pre128 M&M": ("pre128", "mm128", "const"),           # C3: est3's M&M baseline
    "split64 ML": ("split64", "ml", "const"),             # C4: joint ML over both blocks, lobe pick
    "split64 ML interp": ("split64", "ml", "interp2"),    # C4b: phase tracked over the 2 blocks (RTS / linear interp.)
    "RCS2-13": ("rcs13", "rb", "const"),                  # C1a: Rife-Boorstyn on all known symbols, constant phase
    "RCS2-13 track": ("rcs13", "rb", "track"),            # C1b: + pilot phase RTS smoother (or sliding window), interp.
    "RCS2 pre/post": ("prepost16", "nda4", "const"),      # C2: 4th-power NDA over the burst, refined on the 32 known
    "Genie": ("none", "genie", "genie"),                  # true f, true per-symbol phase (incl. phase noise), gain 1
    # est5: deployed preamble / pilot systems (expected_est5.md)
    "VDE-SAT": ("vde27", "vde", "const"),                 # C6: ML on the syncword, R-B over all known in its lobe
    "VDE-SAT track": ("vde27", "vde", "track"),           # C6 + Kalman / RTS phase over the 40 fields (pn runs)
    "DVB-S2 style": ("dvbs2", "mmml", "const"),           # C7: M&M on the PL header, joint ML header + pilot block
    "CCSDS style": ("ccsds8", "rb", "const"),             # C8: R-B over the 8 blocks
    "CCSDS style track": ("ccsds8", "rb", "track"),       # C8 + Kalman / RTS over the 8 block phases (pn runs)
    "CCSDS style blocks": ("ccsds8", "rb", "blocks"),     # C8 + per-block ML phase + linear interp. (CCSDS 130.11 5.6)
    "ViaSat UW": ("viasat16", "nda4uw", "const"),         # C9: 4th-power top-32 peaks, picked with the midamble UW
    "DMRS 1/7": ("dmrs7", "rb", "const"),                 # C10: R-B over the pilots (no alias inside +-0.03)
    "DMRS 1/7 track": ("dmrs7", "rb", "track"),           # C10 + Kalman / RTS over the 171 pilots (pn runs)
    "Sparse pilots 1/32": ("zr32", "nda4rb", "const"),    # C11 (400ZR-inspired): 4th-power coarse, R-B on the pilots
    "WiFi pre128": ("wifi128", "lag", "const"),           # C12: lag-16 coarse + lag-64 fine autocorrelation
    "MIL-110 HF": ("mil110", "rb", "const"),              # C13: R-B over preamble + probes
    "MIL-110 HF track": ("mil110", "rb", "track"),        # C13 + Kalman / RTS over the 5 fields (pn runs)
    "hyb3": ("prepost16", "hyb3", "const")}               # C14: US7590199, log DA + log 4th-power spectra, 3 candidates
EST5 = ("VDE-SAT", "VDE-SAT track", "DVB-S2 style", "CCSDS style", "CCSDS style track", "CCSDS style blocks",
        "ViaSat UW", "DMRS 1/7", "DMRS 1/7 track", "Sparse pilots 1/32", "WiFi pre128", "MIL-110 HF",
        "MIL-110 HF track", "hyb3")                       # run_bler: lobe range filter + per-packet hypotheses
# Griebel, Wasenmueller, Wehn, ARS 19 (2021) variants on the rcs13 layout (lit_ars2021.md section 6, expected_ars.md):
# the same burst as RCS2-13, so they pair packet for packet with it
SOURCES.update({
    "G4096": ("rcs13", "rb4096", "const"),                # rb with FFT 4096 + parabolic
    "G2048": ("rcs13", "rb2048", "const"),                # rb with FFT 2048 + parabolic
    "G2048N": ("rcs13", "rb2048n", "const"),              # rb with FFT 2048 + parabolic + 1 Newton step
    "Griebel faithful": ("rcs13", "rb2048f", "eq17"),     # FFT 2048, peak over the full band, Eq. 17 phase, 1 decode
    "RCS2-13 lobes": ("rcs13", "rb", "const")})           # RCS2-13 + the +-1/20 alias lobes in the CRC search
ARS = ("G4096", "G2048", "G2048N", "Griebel faithful", "RCS2-13 lobes")   # run_bler: the est5 search branch
NO_SEARCH = ("Griebel faithful",)                         # window 0: one decode at the estimate (the paper's chain)
SRC_LOBES = {"RCS2-13 lobes": (float(RCS_DP + 1), 1)}     # per-source (D_lobe, lobes each side): rcs13 itself keeps 0
# faithful variants of the est5 competitors (expected_variants.md, 2026-11-15): the deployed layouts / estimators of
# lit_card_sat / space / terr.md; the est5 search branch; McNemar-paired with PARENT when both are in a job
SOURCES.update({
    "hyb3-pre48": ("pre48", "hyb3", "const"),             # V1: US 7590199 / 7593490 layout, 48 contiguous preamble
    "ViaSat 7653150": ("viasat16", "nda4pk", "x4"),       # V2a: single 4th-power peak, 3-bin average, phase arg X4 / 4
    "ViaSat top32 X4phase": ("viasat16", "nda4uw", "x4"),  # V2b: ViaSat UW (US 8243859) with the 4th-power phase
    "DVB-S2 header90": ("dvbh90", "mmml", "const"),       # V3a: PLHEADER only (CCM): M&M + ML in its 1/90 lobe
    "DVB-S2 SOF26": ("sof26", "mmml", "const"),           # V3b: SOF only (ACM): M&M + ML in its 1/26 lobe
    "MIL-110 full": ("mil110f", "rb", "const"),           # V4: R-B over 287 preamble + 4 probes, +-3 lobes of 1/287
    "CCSDS 131.2 real": ("cc131", "rb", "const"),         # V5: R-B over the 2 pilot fields, +-17 lobes of 1/556
    "CCSDS 131.0 ASM": ("asm32", "ml", "const"),          # V6: joint ML over the 2 ASMs, +-12 lobes of 1/1056
    "WiFi real320": ("wifi320", "lag320", "const"),       # V7a: lag 16 on the L-STF, lag 64 on the L-LTF, no lobes
    "WiFi real320 lobes": ("wifi320", "lag320", "const"),     # V7b: V7a + the +-4 fine-lobe (1/64) CRC search
    "hyb3-pre48 wide": ("pre48", "hyb3", "const"),        # V1w: V1 with window max(4th-power, 48-symbol DA CRB)
    "split64 ML L4": ("split64", "ml", "const")})         # split64 ML with +-4 lobes (~4 sigma_env; reference for V6)
VARS = ("hyb3-pre48", "ViaSat 7653150", "ViaSat top32 X4phase", "DVB-S2 header90", "DVB-S2 SOF26", "MIL-110 full",
        "CCSDS 131.2 real", "CCSDS 131.0 ASM", "WiFi real320", "WiFi real320 lobes", "hyb3-pre48 wide")
                                                          # run_bler: the est5 branch ("split64 ML L4" keeps the est4
                                                          # branch of split64 ML: only its lobe count differs)
PARENT = {"hyb3-pre48": "hyb3", "ViaSat 7653150": "ViaSat UW", "ViaSat top32 X4phase": "ViaSat UW",
          "DVB-S2 header90": "DVB-S2 style", "DVB-S2 SOF26": "DVB-S2 style", "MIL-110 full": "MIL-110 HF",
          "CCSDS 131.2 real": "CCSDS style", "CCSDS 131.0 ASM": "split64 ML", "WiFi real320": "WiFi pre128",
          "WiFi real320 lobes": "WiFi pre128", "hyb3-pre48 wide": "hyb3-pre48",
          "split64 ML L4": "split64 ML"}                  # run_bler McNemar reference of a variant (if in the job)
SRC_LOBES["WiFi real320"] = (float(WIFI_FINE), 0)         # V7a: the chip trusts the coarse lobe pick (lobe_err kept)
SRC_LOBES["split64 ML L4"] = (float(N_SYM + 64), 4)       # D_lobe 1088 (as split64), 4 lobes each side
SCAN = ("DVB-S2 header90", "DVB-S2 SOF26")                # contiguous headers: no lobes, the CRC search scans k STEP over
for _s in SCAN:                                           # the whole +-MAX_CFO, filtered per hypothesis to |f_hat + off|
    SRC_LOBES[_s] = (0.0, 0)                              # <= MAX_CFO + STEP (run_bler; the 1/Nh lobe windows overlapped
                                                          # (SOF26) or left holes (header90): verifier 2026-11-15)
NDA4_WIN = ("hyb3-pre48",)                                # run_bler window from crb_nda4 (the 4th-power term sets the
                                                          # precision of the summed spectrum, not the 48 DA symbols)
WIN_MAX = ("hyb3-pre48 wide",)                            # run_bler window from max(crb_nda4, crb_known): at 1/10, 0.15 the
                                                          # 4th power is noise and f_hat has the 48-symbol DA precision
# fixed CFO search of two competitors (code review 2026-11-17); new sources, their parents unchanged (McNemar-paired:
# the same layouts, so the same bursts packet for packet)
SOURCES.update({
    "RCS2-13 wide": ("rcs13", "rb", "const"),             # F1: RCS2-13, CRC-search window >= +-WIN_HALF (the noise-free
                                                          # known-symbol spectrum has pre/post fringes at +-9.72e-4,
                                                          # +-1.84e-3, +-2.73e-3 (|X| 62.6 / 60.8 / 60.1 vs 116), 13 / 25
                                                          # / 36 steps away: M = 3 missed them); est4 branch as RCS2-13
                                                          # (metric-ordered, as pre128 ML with its M = 36), 1st decode f_hat
    "VDE-SAT fixed": ("vde27", "vdef", "const")})         # F2: VDE-SAT, R-B window f0 +- 1/54 not clipped to |nu| <= MAX_CFO
                                                          # (always one full alias period), +-2 alias lobes, alias window
                                                          # x ALIAS_WIN; est5 branch (range-filtered lobe centres)
FIX = ("RCS2-13 wide", "VDE-SAT fixed")
FIX5 = ("VDE-SAT fixed",)                                 # run_bler: the est5 search branch ("RCS2-13 wide" keeps the est4
                                                          # branch of RCS2-13: only its window differs)
PARENT.update({"RCS2-13 wide": "RCS2-13", "VDE-SAT fixed": "VDE-SAT"})
WIN_HALF = {"RCS2-13 wide": 1e-2}                         # run_bler window M >= ceil(half / STEP) (1e-2: M = 134; the pre/post fringes continue at ~60/116 height across the range, 2026-11-17)
SRC_LOBES["VDE-SAT fixed"] = (float(VDE_DP + 1), 2)       # syncword errors > 3/54 land on |m| = 2 (VDE-SAT keeps 1)
ALIAS_WIN = {"VDE-SAT fixed": 1.7}                        # run_bler window of the |m| > 0 hypotheses: the CRB window x 1.7
                                                          # (the alias peak is 0.59 of the true one: ~1.7 x the rms error)
SOURCES["VDE-SAT scan"] = ("vde27", "vdef", "const")      # F2b (2026-11-17): VDE-SAT with the full-range CRC scan of the DVB-S2
SCAN = SCAN + ("VDE-SAT scan",)                           # header (k STEP over +-MAX_CFO, no lobes): the smoke showed "VDE-SAT
SRC_LOBES["VDE-SAT scan"] = (0.0, 0)                      # fixed" still misses 0.2 % (in-search 0.9979 at 0.15 -3.5 dB)
FIX = FIX + ("VDE-SAT scan",)
FIX5 = FIX5 + ("VDE-SAT scan",)
PARENT["VDE-SAT scan"] = "VDE-SAT"


def _segments(name):
    """(kind, length) runs of the burst, 'k' = known, 'd' = data."""
    if name == "pre128":
        return [("k", 128), ("d", N_SYM)]
    if name == "split64":
        return [("k", 64), ("d", N_SYM), ("k", 64)]
    if name == "rcs13":
        assert RCS_PRE + RCS_NP * (RCS_DP + 1) + RCS_TAIL + RCS_POST == N_SYM + 116
        assert RCS_NP * RCS_DP + RCS_TAIL == N_SYM
        return [("k", RCS_PRE)] + [("d", RCS_DP), ("k", 1)] * RCS_NP + [("d", RCS_TAIL), ("k", RCS_POST)]
    if name == "prepost16":
        return [("k", 16), ("d", N_SYM), ("k", 16)]
    if name == "none":
        return [("d", N_SYM)]
    if name == "vde27":
        assert VDE_HEAD + (VDE_NP - 1) * VDE_DP + VDE_TAIL == N_SYM
        return ([("k", VDE_SYNC), ("d", VDE_HEAD), ("k", 1)] + [("d", VDE_DP), ("k", 1)] * (VDE_NP - 1)
                + [("d", VDE_TAIL)])
    if name == "dvbs2":
        return [("k", DVB_HDR), ("d", N_SYM // 2), ("k", DVB_PB), ("d", N_SYM // 2)]
    if name == "ccsds8":
        assert sum(CC_GAPS) == N_SYM
        return [("k", CC_BL)] + sum(([("d", g), ("k", CC_BL)] for g in CC_GAPS), [])
    if name == "viasat16":
        return [("d", N_SYM // 2), ("k", UW_LEN), ("d", N_SYM // 2)]
    if name == "dmrs7":
        assert 6 * DM_NS + 4 == N_SYM
        return [("d", 3), ("k", 1), ("d", 3)] * DM_NS + [("d", 3), ("k", 1), ("d", 1)]
    if name == "zr32":
        assert ZR_NP * (ZR_P - 1) + 1 == N_SYM
        return [("k", 1), ("d", ZR_P - 1)] * ZR_NP + [("d", 1)]
    if name == "wifi128":
        return [("k", 8 * WIFI_REP), ("d", N_SYM)]
    if name == "mil110":
        assert MIL_NP * MIL_DATA == N_SYM
        return [("k", MIL_PRE)] + [("d", MIL_DATA), ("k", MIL_PROBE)] * MIL_NP
    if name == "pre48":
        return [("k", PRE48), ("d", N_SYM)]
    if name == "dvbh90":
        return [("k", DVB_HDR), ("d", N_SYM)]
    if name == "sof26":
        return [("k", DVB_SOF), ("d", N_SYM)]
    if name == "mil110f":
        return [("k", MILF_PRE)] + [("d", MIL_DATA), ("k", MIL_PROBE)] * MIL_NP
    if name == "cc131":
        h = (N_SYM - CC_D) // 2                                       # the 540-data gap centred in the codeword
        return [("d", h), ("k", CC_P), ("d", CC_D), ("k", CC_P), ("d", N_SYM - CC_D - h)]
    if name == "asm32":
        return [("k", ASM_LEN), ("d", N_SYM), ("k", ASM_LEN)]
    if name == "wifi320":
        return [("k", WIFI_STF), ("k", WIFI_GI + 2 * WIFI_FINE), ("d", N_SYM)]   # fields: L-STF, L-LTF
    raise ValueError(name)


LAYOUTS4 = ("pre128", "split64", "rcs13", "prepost16", "none")
LAYOUTS5 = LAYOUTS4 + ("vde27", "dvbs2", "ccsds8", "viasat16", "dmrs7", "zr32", "wifi128", "mil110")   # est5 appended
VLAYOUTS = ("pre48", "dvbh90", "sof26", "mil110f", "cc131", "asm32", "wifi320")   # faithful variants, appended last
LAYOUTS = LAYOUTS5 + VLAYOUTS
LAYOUT_ID = {l: i for i, l in enumerate(LAYOUTS)}           # the layout's noise stream (run_bler)
LOBE_N = {"vde27": 1, "dvbs2": 3, "ccsds8": 5, "zr32": 1, "wifi128": 4, "mil110": 3}   # est5 lobe hypotheses each side
                                                            # (wifi128 4: the lag-16 coarse range 1/32 wraps by
                                                            # 1/16 = 4 fine lobes near |f| = 0.03)
LOBE_N.update({"dvbh90": 3, "sof26": 1, "mil110f": 3, "wifi320": 4,   # variants: header-only ceil(0.03 Nh) (unused:
               "cc131": int(np.ceil(MAX_CFO * (CC_D + CC_P))),   # C.SCAN); cc131 ceil(0.03 x 556) = 17 (= 4 sigma_env)
               "asm32": 12})                                # asm32 ceil(4 sigma_env D) at -5 dB: sigma_env = the per-block
                                                            # noncoherent CRB = 2.86 lobes (+-3 as split64 would miss the
                                                            # lobe for 17 % of packets at -4 dB, 2 % at 2/5 0.5 dB)
_LAY = {}


def layout(name):
    """Burst layout: K, data_idx (1024,), known_idx (Nk,) (burst indices, ascending), the fields (fstart: offsets of
    the fields in known order, fsize, centres: mean burst index of each field), the linear-interpolation weights of
    the data symbols between the field centres (ij, iw: phase(n) = (1 - w) phi[j] + w phi[j + 1], w clipped to [0, 1]),
    nk, energy_db."""
    if name in _LAY:
        return _LAY[name]
    kinds, n0, fst, fsz, cen, dat, kno = [], 0, [], [], [], [], []
    for kd, ln in _segments(name):
        idx = np.arange(n0, n0 + ln)
        if kd == "k":
            fst.append(len(kno))
            fsz.append(ln)
            cen.append(idx.mean())
            kno.extend(idx)
        else:
            dat.extend(idx)
        n0 += ln
    dat, kno = np.array(dat, int), np.array(kno, int)
    assert len(dat) == N_SYM and n0 == N_SYM + len(kno)
    cen = np.array(cen, float)
    if len(cen) >= 2:
        j = np.clip(np.searchsorted(cen, dat, side="right") - 1, 0, len(cen) - 2)
        w = np.clip((dat - cen[j]) / (cen[j + 1] - cen[j]), 0.0, 1.0)
    else:
        j, w = np.zeros(N_SYM, int), np.zeros(N_SYM)
    L = dict(name=name, K=n0, data_idx=dat, known_idx=kno, fstart=np.array(fst, int), fsize=np.array(fsz, int),
             centres=cen, ij=j, iw=w, nk=len(kno), energy_db=energy_db(len(kno)))
    _LAY[name] = L
    return L


def lobe_D(name):
    """Lobe spacing 1/D_lobe of a 2-field layout (split64: D_lobe = 1088, prepost16: 1040, dvbs2: 575), D_lobe = the
    distance of the two block centres; est5 periodic layouts: D_lobe = the known-symbol period (vde27 27, zr32 32,
    wifi128 64 = the fine lag, ccsds8 the mean block-centre spacing 162.3, mil110 the probe spacing 287); 0 for the
    other layouts (no lobe hypotheses in the CRC search; dmrs7: its 1/7 aliases are outside |f| <= 0.03). Variants:
    dvbh90 / sof26 D_lobe = Nh (lobes at the header's resolution 1 / Nh), wifi320 64, mil110f 287, cc131 556, asm32
    1056 (2 fields), pre48 0."""
    if name == "vde27":
        return float(VDE_DP + 1)
    if name == "zr32":
        return float(ZR_P)
    if name in ("wifi128", "wifi320"):
        return float(WIFI_FINE)
    if name in ("dvbh90", "sof26"):
        return float(layout(name)["nk"])
    c = layout(name)["centres"]
    if name == "ccsds8":
        return float((c[-1] - c[0]) / (len(c) - 1))
    if name in ("mil110", "mil110f"):
        return float(np.mean(np.diff(c[1:])))
    if name in ("viasat16", "dmrs7"):
        return 0.0
    return float(c[1] - c[0]) if len(c) == 2 else 0.0


def lobe_n(name, lobes):
    """Lobe hypotheses each side: est5 layouts their own LOBE_N (0 if run_bler --lobes 0), the est4 ones --lobes."""
    return (LOBE_N[name] if lobes else 0) if name in LOBE_N else lobes


def src_lobes(src, lobes):
    """(D_lobe, lobes each side) of a source: SRC_LOBES overrides (0 lobes if --lobes 0), else its layout's."""
    if src in SRC_LOBES:
        D, n = SRC_LOBES[src]
        return (D, n) if lobes else (0.0, 0)
    lay = SOURCES[src][0]
    return (lobe_D(lay) if lobes else 0.0), lobe_n(lay, lobes)


def var_lag(snr_db, lag=WIFI_FINE, n=WIFI_FINE):
    """Variance of the lag-autocorrelation CFO estimate over n products at lag `lag` (Gaussian approximation,
    lit_real_wlan.md): (2 rho + 1) / (2 n rho^2) / (2 pi lag)^2; the Wi-Fi fine stage: lag = n = 64."""
    rho = 10 ** (np.asarray(snr_db) / 10)
    return (2 * rho + 1) / (2 * n * rho ** 2) / (2 * np.pi * lag) ** 2


def energy_db(nk):
    """Energy charged per data symbol by Nk extra known symbols: 10 log10((1024 + Nk) / 1024)."""
    return 10 * np.log10((N_SYM + nk) / N_SYM)


KMAX = max(N_SYM + sum(l for k, l in _segments(n) if k == "k") for n in LAYOUTS4)  # est4 longest burst (1152): the
                                                                     # est4 phase-noise path length, unchanged
KMAX_ALL = max(N_SYM + sum(l for k, l in _segments(n) if k == "k") for n in LAYOUTS5)  # incl. est5 (mil110: 1332),
                                                                     # the est5 extended path, unchanged
KMAX_V = max(N_SYM + sum(l for k, l in _segments(n) if k == "k") for n in LAYOUTS)    # incl. variants (mil110f: 1435)


def crb_nda4(snr_db, K):
    """Bound of the 4th-power NDA estimate over a K-symbol QPSK burst: the known-symbol CRB of K contiguous symbols x the
    4th-power loss (16 rho^3 + 72 rho^2 + 96 rho + 24) / (16 rho^3), rho = Es/N0 (the noise of (s + n)^4 - s^4:
    16 rho^3 + 72 rho^2 + 96 rho + 24 in units of sigma^8, signal rho^4, var(f) = var(4 f) / 16)."""
    rho = 10 ** (np.asarray(snr_db) / 10)
    return crb_known(snr_db, np.arange(K)) * (16 * rho ** 3 + 72 * rho ** 2 + 96 * rho + 24) / (16 * rho ** 3)


def make_burst(name, data_sym, rng):
    """Burst symbols (B, K) with the data symbols data_sym (B, 1024) at data_idx and random QPSK known symbols drawn
    from rng (rcs13: preamble / postamble random, ONE pilot symbol per burst repeated in all pilot fields, as the
    DVB-RCS2 unique word holds one pilot block; vde27 the same for its single pilots; wifi128: the first 16 known
    symbols repeated 8 x; wifi320: L-STF = the first 16 repeated 10 x, L-LTF = a 64-symbol sequence (known 160 .. 223)
    as guard (its last 32) + 2 copies; asm32: the same 32-symbol marker before and after). Returns burst, data_idx,
    known_idx, known symbols (B, Nk)."""
    L = layout(name)
    B = len(data_sym)
    burst = np.empty((B, L["K"]), complex)
    burst[:, L["data_idx"]] = data_sym
    ks = C3.qpsk(rng, (B, L["nk"]))
    if name in ("rcs13", "vde27") and L["nk"]:
        pil = np.where(L["fsize"] == 1)[0]
        ks[:, L["fstart"][pil]] = ks[:, [L["fstart"][pil[0]]]]
    if name == "wifi128":
        ks = np.tile(ks[:, :WIFI_REP], (1, L["nk"] // WIFI_REP))
    if name == "wifi320":
        lt = ks[:, WIFI_STF:WIFI_STF + WIFI_FINE]
        ks = np.concatenate([np.tile(ks[:, :WIFI_REP], (1, WIFI_STF // WIFI_REP)), lt[:, WIFI_FINE - WIFI_GI:], lt, lt], 1)
    if name == "asm32":
        ks[:, ASM_LEN:] = ks[:, :ASM_LEN]
    burst[:, L["known_idx"]] = ks
    return burst, L["data_idx"], L["known_idx"], ks


# =====================================================================
# Chain: est3 / blind_cfo full 8-SPS RRC chain on the whole burst + Wiener phase noise
# =====================================================================

def n_samples(K):
    """8-SPS samples of a K-symbol burst after the transmit RRC (fftconvolve full length)."""
    return K * SPS + len(rrc(BETA)) - 1


def wiener(B, K, pn, rng):
    """Wiener phase path (B, n_samples(K)) as blind_cfo.transmit_full: cumsum of N(0, 2 pi pn / SPS) per sample, zero
    at the centre sample n_samples // 2."""
    inc = rng.standard_normal((B, n_samples(K))) * np.sqrt(2 * np.pi * pn / SPS)
    phi = np.cumsum(inc, axis=1)
    return phi - phi[:, [phi.shape[1] // 2]]


def extend_path(phi, K, pn, rng):
    """The Wiener path phi (B, n_samples(Kp)) continued outwards at both ends to n_samples(K) >= n_samples(Kp) with
    increments N(0, 2 pi pn / SPS) from rng (the same process; phi unchanged in the centre, so still zero there)."""
    B, a = len(phi), (n_samples(K) - phi.shape[1]) // 2
    assert a >= 0 and (n_samples(K) - phi.shape[1]) % 2 == 0
    inc = rng.standard_normal((B, 2 * a)) * np.sqrt(2 * np.pi * pn / SPS)
    left = phi[:, :1] - np.cumsum(inc[:, :a], axis=1)[:, ::-1]
    return np.concatenate([left, phi, phi[:, -1:] + np.cumsum(inc[:, a:], axis=1)], axis=1)


def slice_path(phi, K):
    """The centred piece of a longer path phi (B, n_samples(Kp)) for a K-symbol burst: the same phase-noise process
    at the same time from the burst centre for every layout, and still zero at the burst's own centre."""
    a = (phi.shape[1] - n_samples(K)) // 2
    assert (phi.shape[1] - n_samples(K)) % 2 == 0
    return phi[:, a:a + n_samples(K)]


def transmit(burst_sym, f, ph, snr_db, rng, pn=0.0, phi=None):
    """The full AWGN chain (identical to est3.common.transmit / blind_cfo.transmit_full) on the burst (B, K): Es
    measured over the whole burst, sigma^2 = Es / SNR per real dimension x 2. pn > 0: Wiener phase noise exactly as
    blind_cfo (the path phi if given, else drawn from rng before the noise, as blind_cfo); pn = 0: no extra draws.
    Returns the MF output r (B, K), the noisy 8-SPS samples rx (pre-MF correction) and the true phase-noise path at
    symbol rate phs (B, K) = phi at the symbol centre sample (n + DELAY_SYM) SPS (zeros if pn = 0)."""
    B, K = burst_sym.shape
    h = rrc(BETA)
    up = np.zeros((B, K * SPS), complex)
    up[:, ::SPS] = burst_sym
    tx = fftconvolve(up, h[None], axes=1)
    m = np.arange(tx.shape[1])
    rx = tx * np.exp(1j * (2 * np.pi * np.asarray(f, float).reshape(-1, 1) * m / SPS
                           + np.asarray(ph, float).reshape(-1, 1)))
    phs = np.zeros((B, K))
    if pn > 0:
        if phi is None:
            phi = wiener(B, K, pn, rng)
        assert phi.shape == rx.shape, (phi.shape, rx.shape)
        rx = rx * np.exp(1j * phi)
        phs = phi[:, (np.arange(K) * SPS + int(round(DELAY_SYM * SPS)))]
    es = np.sum(np.abs(tx) ** 2, axis=1, keepdims=True) / K          # main.apply_awgn, over the whole burst
    sigma = np.sqrt(es / (10 ** (np.asarray(snr_db, float).reshape(-1, 1) / 10)) / 2)
    rx = rx + sigma * (rng.standard_normal(rx.shape) + 1j * rng.standard_normal(rx.shape))
    D = SPAN * SPS
    return fftconvolve(rx, h[None], axes=1)[:, D:D + K * SPS:SPS], rx, phs


def premf(r, rx, fs):
    """blind_fast.premf for a burst of any length K = r.shape[1] (blind_fast's slices N_SYM = 1024 outputs):
    r'[n] = MF(rx e^{-j 2 pi fs m / SPS})[n] e^{j 2 pi fs (n + DELAY_SYM)}, n = 0 .. K-1."""
    K = r.shape[1]
    h = rrc(BETA)
    m = np.arange(rx.shape[1])
    rx2 = rx * np.exp(-2j * np.pi * fs[:, None] * m[None] / SPS)
    D = SPAN * SPS
    r2 = fftconvolve(rx2, h[None], axes=1)[:, D:D + K * SPS:SPS]
    return r2 * np.exp(2j * np.pi * fs[:, None] * (np.arange(K)[None] + DELAY_SYM))


# =====================================================================
# CRB and the LLR back-end
# =====================================================================

def crb_known(snr_db, pos):
    """CRB of f from known symbols at burst positions pos (unknown phase and amplitude):
    1 / (2 SNR (2 pi)^2 sum (n_k - mean n)^2) (cycles/symbol)^2; inf without known symbols."""
    n = np.asarray(pos, float)
    if len(n) < 2:
        return np.inf
    return 1.0 / (2 * 10 ** (np.asarray(snr_db) / 10) * (2 * np.pi) ** 2 * np.sum((n - n.mean()) ** 2))


def llrs(r, data_idx, f, g, sigma2c):
    """est3.common.llrs on the data symbols of a burst with a per-packet (B,) or per-symbol (B, 1024) complex gain g:
    sh = r[data] e^{-j 2 pi f (n + D)} / g_n, LLR = 2 sqrt2 Re/Im(sh) |g_n|^2 / sigma2c, de-interleaved."""
    g = np.asarray(g)
    g = g[:, None] if g.ndim == 1 else g
    sh = r[:, data_idx] * np.exp(-2j * np.pi * f[:, None] * (data_idx + DELAY_SYM)[None]) / g
    var = np.broadcast_to(sigma2c / np.abs(g) ** 2, sh.shape)
    llr = np.empty((len(r), N_BITS))
    llr[:, 0::2] = 2 * np.sqrt(2) * sh.real / var
    llr[:, 1::2] = 2 * np.sqrt(2) * sh.imag / var
    out = np.empty_like(llr)
    out[:, INTERLEAVER] = llr
    return out, sh


def path(kind, name):
    d = {"results": RESULTS, "logs": LOGS, "plots": PLOTS}[kind]
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)
