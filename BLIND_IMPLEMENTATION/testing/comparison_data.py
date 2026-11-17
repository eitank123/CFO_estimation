"""Full comparison data: blind vs EVERY receiver of the est4 / est5 / ARS harness, from EXISTING results only (no
simulation). Rerunnable: parts that have not landed (or whose job log has no ALL DONE) are reported as "not run yet";
the est5 smoke parts (800 packets) are shown separately and labelled SMOKE.
Writes results/comparison_full.md and results/comparison_full.json.

Data: plot_e4.e4 / plot_e4.blind (the loaders of the figures and of 08, 8.2a), applied part by part (plot_e4.load is
swapped for one call so that each part keeps its name; the receiver numbers are those of plot_e4.e4). Merge rule = the
plot_e4.e4(rate, e5=True, ars=True) rule (est5 parts without their Genie, ARS parts without their RCS2-13) with ONE
difference: a receiver that already comes from an est4 part (RCS2 pre/post in e5-pp*) is NOT merged with the est5
replicate; the replicate is shown as its own row "<src> [<part>]". plot_e4.e4 pools such replicates (plot_e4.pool), so
the merge check pools "<src>" + "<src> [<part>]" the same way and reports where plot_e4.e4 still differs.
Cards: section A "Real system" block from REAL / CARD_SYS (lit_card_sat / space / terr.md, lit_rates.md, 2026-11-15);
section E = spectral efficiency vs the real systems (lit_rates.md, curated constants below).
Required SNR / CI / MACs at the required SNR = plot_final.req / core_at (= plot_e4.gap_db + Clopper-Pearson bound
curves), on points >= -5 dB only (user rule 2026-11-15). 8.2a values that used a point below -5 dB are shown in the
reproduction check only.
usage: py comparison_data.py"""
import glob, json, os, re, sys
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plot_e4 as P4                    # noqa: E402  e4, blind, gap_db, load, STY / STY5 / STYA, MAIN / PP / MAIN5 / PP5 / ARSP
import plot_final as PF                 # noqa: E402  cp, req, core_at (the final_table.md method)

C, E4C = P4.C, P4.E4C
PROJ = P4.PROJ
OUT_MD = os.path.join(HERE, "results", "comparison_full.md")
OUT_JS = os.path.join(HERE, "results", "comparison_full.json")
RATES = ("1/10", "0.15", "2/5", "1/2")
TARGETS = [("1/10", 1e-4), ("0.15", 1e-3), ("0.15", 1e-4), ("2/5", 1e-3), ("1/2", 1e-3)]
XMIN = -5.0                                             # no point below -5 dB is used or shown (user, 2026-11-15)
SMOKE = ["e5-smoke-a", "e5-smoke-b", "e5-smoke-c"]
OTHER_SMOKE = ["e4-smoke-a", "e4-smoke-b", "e4-smoke2-a", "e4-smoke2-b", "ars-smoke-a", "ars-smoke-b"]
LABELS = P4.styles(True, True)                          # every receiver plot_e4 draws (STY + STY5 + STYA)
N_SYM = 1024
BLIND_82A = {("1/10", 1e-4): -4.90, ("0.15", 1e-3): -3.60, ("0.15", 1e-4): -2.98, ("2/5", 1e-3): 0.61,
             ("1/2", 1e-3): 1.79}                       # blind in 8.2a (the base of the gap predictions)

# ------------------------------------------------------------------ reference values that must reproduce (None = fails)
TK = [("1/10", 1e-4), ("0.15", 1e-3), ("0.15", 1e-4), ("2/5", 1e-3), ("1/2", 1e-3)]
REF = {  # 08_parameters_results.md 8.2a (pre128 M&M: final_table.md), expected_ars.md "Measured"
    "Blind": ("8.2a", [-4.90, -3.60, -2.98, 0.61, 1.79]),
    "Genie": ("8.2a", [-5.19, -3.91, -3.59, 0.64, 1.90]),
    "RCS2-13": ("8.2a", [-4.09, -3.45, -3.12, 1.10, 2.33]),
    "pre128 ML": ("8.2a", [-4.68, -3.44, -3.12, 1.16, 2.41]),
    "pre128 M&M": ("final_table.md", [-3.03, -3.40, -3.00, 1.16, 2.41]),
    "split64 ML": ("8.2a", [-2.87, -3.34, -2.71, 1.12, 2.38]),
    "RCS2 pre/post": ("8.2a", [None, None, None, None, 2.77]),
    "G4096": ("expected_ars.md", [-3.97, -3.45, -3.11, 1.10, 2.33]),
    "G2048": ("expected_ars.md", [-1.15, -2.88, -1.34, 1.10, 2.33]),
    "G2048N": ("expected_ars.md", [-1.15, -2.88, -1.34, 1.10, 2.33]),
    "Griebel faithful": ("expected_ars.md", [-1.08, -2.72, -1.26, 1.29, 2.55]),
    "RCS2-13 lobes": ("expected_ars.md", [-4.10, -3.45, -3.12, 1.10, 2.33])}

# ------------------------------------------------------------------ predictions written BEFORE the runs
# (lo, hi) required SNR [dB], "fails" or None (= no prediction). est5: expected_est5.md "Predicted comparison" table
# (= competitors.md); ARS: expected_ars.md "Predicted comparison" (gap to blind -> blind 8.2a + gap). est4: qualitative
# only (expected_est4.md), no numbers.
F = "fails"
PRED5 = {"VDE-SAT": [(-4.85, -4.6), (-3.6, -3.4), None, (0.9, 1.0), (2.15, 2.25)],
         "DVB-S2 style": [(-4.65, -4.5), (-3.4, -3.3), None, (1.15, 1.2), (2.4, 2.5)],
         "CCSDS style": [(-4.65, -4.3), (-3.4, -3.2), None, (1.15, 1.25), (2.4, 2.5)],
         "CCSDS style blocks": [(-4.65, -4.3), (-3.4, -3.2), None, (1.15, 1.25), (2.4, 2.5)],
         "ViaSat UW": [F, F, None, (1.5, 2.5), (2.2, 2.8)],
         "DMRS 1/7": [(-4.5, -4.5), (-3.2, -3.2), None, (1.33, 1.33), (2.6, 2.6)],
         "Sparse pilots 1/32": [(-4.4, -3.9), (-3.5, -3.0), None, (0.8, 1.0), (2.05, 2.2)],
         "WiFi pre128": [(-4.6, -4.3), (-3.4, -3.2), None, (1.2, 1.3), (2.45, 2.55)],
         "MIL-110 HF": [(-4.05, -4.05), (-2.8, -2.8), None, (1.8, 1.8), (3.0, 3.0)],
         "hyb3": [F, F, None, (1.2, 2.0), (2.2, 2.6)]}
GAPA = {"G4096": [(0.81, 0.86), (0.15, 0.2), (-0.14, -0.09), (0.49, 0.54), (0.54, 0.59)],
        "G2048": [(0.84, 1.0), (0.18, 0.35), (-0.11, 0.06), (0.52, 0.69), (0.57, 0.74)],
        "G2048N": [(0.81, 0.86), (0.15, 0.2), (-0.14, -0.09), (0.49, 0.54), (0.54, 0.59)],
        "Griebel faithful": [(0.9, 1.3), (0.25, 0.65), (-0.04, 0.36), (0.6, 1.0), (0.65, 1.05)],
        "RCS2-13 lobes": [(0.2, 0.35), (0.15, 0.15), (-0.14, -0.14), (0.49, 0.49), (0.54, 0.54)]}
PRED = dict(PRED5)
PRED.update({k: [(round(BLIND_82A[t] + a, 2), round(BLIND_82A[t] + b, 2)) for t, (a, b) in zip(TK, v)]
             for k, v in GAPA.items()})
PRED_MACS = {"VDE-SAT": "~0.04-0.06 M", "DVB-S2 style": "~0.05-0.1 M", "CCSDS style": "~0.05-0.1 M",
             "CCSDS style blocks": "~0.05-0.1 M", "ViaSat UW": "~0.04 M", "DMRS 1/7": "~0.035 M",
             "Sparse pilots 1/32": "~0.045 M", "WiFi pre128": "estimator < 1k MACs, many lobe decodes at -5 dB",
             "MIL-110 HF": "~0.035 M", "hyb3": "~0.04 M", "G4096": "RCS2-13 -9 ... -11 %",
             "G2048": "RCS2-13 -12 ... -17 %", "G2048N": "~ G2048", "Griebel faithful": "lowest (one decode)",
             "RCS2-13 lobes": "RCS2-13 + a few decodes at -5 dB"}
PRED_SRC = {**{k: "expected_est5.md / competitors.md" for k in PRED5}, **{k: "expected_ars.md" for k in GAPA}}

# ------------------------------------------------------------------ cards (text from the docs; numbers from the code)
CARDS = {
    "Blind": dict(
        system="ours: no preamble, no pilots (blind CFO + phase from the polar decoder metric)",
        link="BLIND_IMPLEMENTATION/08_parameters_results.md 8.1; testing/run.py",
        est="testing receiver: run.py testing_s11g at 1/10, 0.15 (nph + q_fix + spec11 below 1/10 -3.5, 0.15 -2.5 dB); "
            "2/5, 1/2: base25_qfix / base2_qfix where run, the presentation receiver (blind_ber.json) elsewhere",
        search="grid of CFO cells x phases ranked by the list-1 decoder metric, CA-SCL-8 + CRC-16 + RHO_N re-encoding check",
        cfo="designed for |f| <= 0.03 cycles/symbol (= our range)",
        changes="-"),
    "Genie": dict(
        system="none (lower bound): true CFO and true per-symbol phase", link="-",
        est="true f and phase, gain 1", search="one decode, no search", cfo="n/a", changes="-"),
    "RCS2-13": dict(
        system="DVB-RCS2 return-link burst, ID 13 layout (ETSI EN 301 545-2, current V1.5.1 2026-04; est4 built on "
               "V1.3.1, ID 13 unchanged; REFERENCES C1, C2, C4)",
        link="https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/en_30154502v010501p.pdf",
        est="Rife-Boorstyn FFT over all known symbols (zeros at the data) + 3-bin parabolic interpolation; constant phase",
        search="metric-ordered CRC search over the CRB window; no alias lobes (pilot spacing 20 -> resolves |f| < 0.025)",
        cfo="TR 101 545-4: 0.5-3 % of Rs = 0.005-0.03 cycles/symbol; our 0.03 is the top of that range",
        changes="ID 13 scaled to 1024 data symbols (pre 32, 53 x (19 d + 1 p), 17 d, post 31); turbo -> our polar; "
                "constant phase (no phase noise here)"),
    "RCS2-13 track": dict(
        system="as RCS2-13 + pilot phase tracking (ESA US7409024 PA-SWI idea, REFERENCES C9; ours: no DVB-RCS2 source "
               "tracks phase in TC-LM)", link="as RCS2-13",
        est="as RCS2-13 + per-pilot phase, smoothed (RTS / sliding window), linearly interpolated across the data",
        search="as RCS2-13", cfo="as RCS2-13",
        changes="as RCS2-13; in AWGN (pn 0) its packets are identical to RCS2-13 (same errors): tracking only matters "
                "under phase noise"),
    "pre128 ML": dict(
        system="128-symbol preamble, ML (DVB-RCS2 TR 101 545-4 preamble-only competitor; Comtech / DOCSIS class)",
        link="https://www.etsi.org/deliver/etsi_tr/101500_101599/10154504/01.01.01_60/tr_10154504v010101p.pdf",
        est="ML direct (FFT 512 + 2 Newton) on the preamble, one LS phase (constant)",
        search="metric-ordered CRC search over the CRB window", cfo="unambiguous over +-0.5 (single block); deployed "
        "modem ranges not documented here", changes="one 128-symbol block before the 1024 data symbols; our polar code"),
    "pre128 M&M": dict(
        system="as pre128 ML with the Mengali-Morelli 1997 estimator (REFERENCES B5; TR 101 545-4 Annex D fine stage)",
        link="Mengali & Morelli, IEEE Trans. Commun. 45(1), 1997", est="M&M (exactly per paper), constant phase",
        search="metric-ordered CRC search over the CRB window", cfo="as pre128 ML", changes="as pre128 ML"),
    "split64 ML": dict(
        system="64 preamble + 64 postamble (Hughes class; pilot placement Ying & Ghogho 2005, REFERENCES C10)",
        link="REFERENCES.md C10", est="joint ML over both blocks (FFT + Newton, lobe pick), constant phase",
        search="CRC search over the +-3 ML lobes (spacing 1/1088), metric order",
        cfo="lobe ambiguity 1/1088 inside +-0.03 (resolved by the CRC search)",
        changes="block split chosen by us (64 + 64)"),
    "split64 ML interp": dict(
        system="as split64 ML + linear interpolation of the two block phases (C4b)", link="as split64 ML",
        est="as split64 ML, phase interpolated", search="as split64 ML", cfo="as split64 ML",
        changes="in AWGN its packets are identical to split64 ML (same errors)"),
    "RCS2 pre/post": dict(
        system="DVB-RCS2 16 + 16 pre / postamble burst, NDA 4th-power (TR 101 545-4; Griebel 2021 NDA chain)",
        link="https://ars.copernicus.org/articles/19/59/2021/",
        est="4th-power FFT over the whole burst (NDA), refined on the 32 known symbols; pi/2 ambiguity from the known symbols",
        search="metric-ordered CRC search (+-3 lobes of 1/1040)", cfo="4th power unambiguous over +-1/8",
        changes="16 + 16 chosen as the shortest DVB-RCS2-like pre/post; our polar code"),
    "VDE-SAT": dict(
        system="C6 VDE-SAT (VHF Data Exchange via satellite, ITU-R M.2092-2 Annex 5 A5-2.10)",
        link="https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf",
        est="ML on the 27-symbol syncword, Rife-Boorstyn over all known symbols in its lobe",
        search="CRC search over the +-1/27 alias lobes (alias peak ~0.59 of the true one)",
        cfo="real: LEO Doppler up to ~+-4 kHz at 33.6 ksps = +-0.12 cycles/symbol (IEEE 8780774 estimator); ours +-0.03",
        changes="one 1090-symbol window of an 80371-symbol burst; turbo -> polar; no link ID (none on the downlink, "
                "M.2092-2 Table 10); pilot comb as A5-2.10 (fixed 2026-11-15, lit_vdesat_format.md)"),
    "VDE-SAT track": dict(
        system="C6 + Kalman / RTS phase over the 40 known fields (phase-noise arm)", link="as VDE-SAT",
        est="as VDE-SAT + phase tracking", search="as VDE-SAT", cfo="as VDE-SAT", changes="as VDE-SAT; smoke only (pn 1e-4)"),
    "DVB-S2 style": dict(
        system="C7 DVB-S2-inspired (EN 302 307 / TR 102 376-1: PL header + pilot block)",
        link="https://www.etsi.org/deliver/etsi_tr/102300_102399/10237601/01.02.01_60/tr_10237601v010201p.pdf",
        est="M&M on the 90-symbol PL header, then joint ML header + 36-symbol pilot block",
        search="CRC search over +-3 lobes of 1/575 (~30 % of packets start in the wrong lobe at -5 dB)",
        cfo="real: pilot FLL coarse acquisition over many frames (Ku DTH +-5 MHz at 25 Mbaud = 0.2) then fine; one-burst "
            "header acquisition range smaller than +-0.03 (lit_real_space.md)",
        changes="real: a pilot block every 16 slots (first one 1440 data symbols after the header: none in a "
                "1024-symbol window), pi/2-BPSK header (only the 26-symbol SOF known before PLS decoding in ACM), "
                "multi-frame loops; we give one burst, one block and all 90 header symbols as known"),
    "CCSDS style": dict(
        system="C8 CCSDS-inspired (CCSDS 131.2 SCCC: frame marker + 16-symbol pilot fields; 130.11-G-2)",
        link="https://public.ccsds.org/Pubs/130x11g2.pdf", est="Rife-Boorstyn FFT over the 8 x 16 pilot blocks",
        search="CRC search over +-5 lobes of 1/162.3 (block period 162.3, data gaps 146 / 147: dense aliases)",
        cfo="real: frame-level FLL over 133 760-symbol frames; 130.11 test case 0.01-0.02 (100 MBaud), ~0.2 at 5 Mbaud "
            "(Bertolucci 2021), acquired over many frames, not in one burst; ours +-0.03",
        changes="field spacing scaled to our burst (8 blocks, gaps 146 / 147): 3.7x the real 131.2 pilot density "
                "(16 per 540 data); +-5 lobe search added"),
    "CCSDS style blocks": dict(
        system="C8 + per-block ML phase + linear interpolation (CCSDS 130.11 5.6)", link="as CCSDS style",
        est="as CCSDS style, per-block phase", search="as CCSDS style", cfo="as CCSDS style", changes="as CCSDS style"),
    "CCSDS style track": dict(
        system="C8 + Kalman / RTS over the 8 block phases (phase-noise arm)", link="as CCSDS style",
        est="as CCSDS style + tracking", search="as CCSDS style", cfo="as CCSDS style",
        changes="as CCSDS style; smoke only (pn 1e-4)"),
    "ViaSat UW": dict(
        system="C9 ViaSat return-link burst demodulators (a merge of two patents: US 7653150 burst + single peak, "
               "US 8243859 top-N + UW joint metric)",
        link="https://patents.google.com/patent/US7653150B2/en",
        est="4th-power FFT over the burst, top-32 peaks (US 8243859) each tested on the 16-symbol midamble UW (pi/2 "
            "ambiguity); phase = LS gain on the 16 UW symbols (the patent: 4th-power bins / 4)",
        search="CRC search; window from the 4th-power bound over the burst (crb_nda4)",
        cfo="patent design statement: up to 10 % of Rs (0.1 cycles/symbol; no product spec found); ours +-0.03",
        changes="UW pick = |U|^2 / (Nk s2) + |X4|^2 / mean in-range |X4|^2 (weight 1, from the patent's joint metric); "
                "the 16-symbol UW barely ranks the 32 candidates (review 2026-11-15)"),
    "DMRS 1/7": dict(
        system="C10 LTE / NB-IoT uplink DMRS style (NPUSCH: 1 reference symbol per 7)",
        link="https://arxiv.org/pdf/1606.04171", est="Rife-Boorstyn over the pilots (range +-0.071, no alias inside +-0.03)",
        search="metric-ordered CRC search, no lobes", cfo="pilot comb unambiguous over +-0.071 (> our +-0.03)",
        changes="single-tone NPUSCH format 1 is structurally the same comb (1 DMRS per 7 single-carrier symbols); "
                "multi-tone NPUSCH / LTE PUSCH DMRS blocks are not modelled; window +-0.071 (deployed +-0.018)"),
    "DMRS 1/7 track": dict(
        system="C10 + Kalman / RTS over the 171 pilots (phase-noise arm)", link="as DMRS 1/7",
        est="as DMRS 1/7 + tracking", search="as DMRS 1/7", cfo="as DMRS 1/7", changes="as DMRS 1/7; smoke only (pn 1e-4)"),
    "Sparse pilots 1/32": dict(
        system="C11 generic sparse pilots 1/32 (400ZR-inspired; 400ZR cited for its +-0.03 CFO requirement only)",
        link="https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf",
        est="4th-power coarse, Rife-Boorstyn on the pilots", search="CRC search over the +-1/32 alias lobes",
        cfo="400ZR: +-1.8 GHz at 59.8 GBd = 0.030 (= ours)",
        changes="not 400ZR (dual-pol 16QAM optics, continuous carrier recovery, Es/N0 ~19 dB; its coarse stage uses "
                "training sequences per Wang 2025, unverified against OIF); only the pilot density"),
    "WiFi pre128": dict(
        system="C12 IEEE 802.11-inspired coarse / fine preamble estimation (legacy L-STF / L-LTF)",
        link="https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html",
        est="lag-16 autocorrelation coarse, lag-64 fine on an 8 x 16 repeated block",
        search="CRC search over the +-4 fine lobes (1/64; the lag-16 range 1/32 wraps)",
        cfo="802.11: +-20 ppm -> coarse range +-1/32 = 0.031 at lag 16 (lit_real_wlan.md)",
        changes="OFDM STF / LTF mapped to a single-carrier 8 x 16 repeated block"),
    "MIL-110 HF": dict(
        system="C13 MIL-STD-188-110C App. C serial-tone HF modem",
        link="https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf",
        est="Rife-Boorstyn over preamble + probes (all 308 known symbols), constant phase",
        search="CRC search over the +-3 probe-period lobes (1/287)", cfo="requirement +-75 Hz at 2400 Bd = 0.031 (= ours)",
        changes="184 preamble + 4 x (256 d + 31 probe) scaled to 1024 data (drops the 103-symbol rate / interleaver "
                "section: real 411 known, 1.47 dB); the real modem has an adaptive equaliser and interleaver frames"),
    "MIL-110 HF track": dict(
        system="C13 + Kalman / RTS over the 5 known fields (phase-noise arm)", link="as MIL-110 HF",
        est="as MIL-110 HF + tracking", search="as MIL-110 HF", cfo="as MIL-110 HF", changes="as MIL-110 HF; smoke only (pn 1e-4)"),
    "hyb3": dict(
        system="C14 Advantech satellite modems, hybrid DA + NDA (patent US 7590199)",
        link="https://patents.google.com/patent/US7590199",
        est="log DA spectrum (16 + 16 known) + log 4th-power spectrum summed, 3 best peaks",
        search="metric-ordered CRC search over the 3 candidates + their lobes", cfo="patent: +-3 % of Rs = 0.03 (= ours)",
        changes="16 + 16 pre / post instead of the patent's 48-symbol contiguous preamble + 440 payload (US 7590199); "
                "candidates chosen by CRC + rho instead of mean |LLR| after partial turbo decoding (US 7593490)"),
    "G4096": dict(
        system="C15 DVB-RCS2 ID 13, Griebel & Wasenmueller & Wehn, Adv. Radio Sci. 19, 59 (2021) (REFERENCES C4)",
        link="https://ars.copernicus.org/articles/19/59/2021/",
        est="the paper's DA-KS: zero-filled r c*, FFT 4096 + 3-bin parabolic interpolation", search="as RCS2-13",
        cfo="paper: |f| <= 1.5 % of Rs = 0.015 (half of ours); TR 101 545-4 range 0.5-3 %",
        changes="FPGA fixed-point word lengths not modelled; FFT 4096 = the paper's ~3.8x zero-padding for our ~1140-symbol burst"),
    "G2048": dict(
        system="as G4096 (C15)", link="https://ars.copernicus.org/articles/19/59/2021/",
        est="FFT 2048 + parabolic (the paper's size for 536 symbols; only 1.8x padding for our burst)",
        search="as RCS2-13", cfo="as G4096", changes="as G4096"),
    "G2048N": dict(
        system="as G4096 (C15)", link="https://ars.copernicus.org/articles/19/59/2021/",
        est="FFT 2048 + parabolic + 1 Newton step", search="as RCS2-13", cfo="as G4096", changes="Newton step is ours"),
    "Griebel faithful": dict(
        system="C15 Griebel et al. 2021 as published", link="https://ars.copernicus.org/articles/19/59/2021/",
        est="FFT 2048, peak over the full band (Eq. 4), Eq. 17 phase (sign-corrected)",
        search="none: ONE decode at the estimate (the paper's chain)", cfo="as G4096 (peak searched over +-0.5)",
        changes="our polar code instead of the 16-state turbo code; fixed point not modelled"),
    "RCS2-13 lobes": dict(
        system="C15 / RCS2-13 + the +-1/20 alias lobes in the CRC search (our addition, not from the paper)",
        link="expected_ars.md", est="as RCS2-13", search="as RCS2-13 + 1 alias lobe of 1/20 each side",
        cfo="as RCS2-13", changes="lobe search added by us"),
}

# ------------------------------------------------------------------ real systems (curated, 2026-11-15)
# from lit_card_sat.md (DVB-RCS2, DVB-S2/S2X, ViaSat, Advantech), lit_card_space.md (CCSDS, VDE-SAT), lit_card_terr.md
# (NB-IoT/LTE, 802.11, MIL-110C, 400ZR), lit_rates.md (rates / MODCODs, net SE). Tags: [std] [paper] [patent] [vendor]
# [derived]. Ours (net SE, 8.2a): 1/10 0.185 @ -4.90, 0.15 0.284 @ -3.60, 2/5 0.784 @ 0.61, 1/2 0.984 @ 1.79 dB.
RF = ("std", "deploy", "layout", "est", "cfo", "loss", "rates", "verdict", "src")
RLAB = dict(std="Current standard / source", deploy="Real deployments", layout="Real known-symbol layout vs ours",
            est="Real estimator, acquisition / tracking", cfo="Design CFO range [cycles/symbol]",
            loss="Published sync loss", rates="Code rates / MODCODs in -5 ... +3 dB (required Es/N0, net SE)",
            verdict="Verdict", src="Sources")
REAL = {
    "rcs2": dict(
        std="ETSI EN 301 545-2 V1.5.1 (2026-04, current; NGSO, roll-off 0.20 / 0.10 / 0.05, S2X waveforms on the "
            "return link) [std]; Annex A ID 13 unchanged from V1.3.1 (used in est4) [std]; guidelines TR 101 545-4 "
            "V1.2.1 (2026) [std]",
        deploy="MF-TDMA return link (terminal -> hub); DVB-RCS gen 1: > 370 networks, > 180 000 terminals (2010) "
               "[vendor]; RCS2 in STM SatLink (2012), Gilat SkyEdge, Creonic hub IP [vendor]; a current RCS2 "
               "terminal count: not found",
        layout="ID 13: 1616 symbols, QPSK 1/3, pre 32 + post 31 + 77 one-symbol pilots (P = 20) = 140 known (8.7 %, "
               "0.39 dB) [std, derived]; ours: same pre / post / P scaled to 1024 data, 116 known (0.47 dB): "
               "equivalent",
        est="no TC-LM estimator in the standard or TR (TR: frequency from the preamble) [std]; the one documented "
            "implementation (Griebel 2021): DA-KS R-B FFT over all known symbols + 3-bin interpolation, constant "
            "phase, one decode [paper]; one shot per burst, the NCC closes a slow per-terminal frequency loop "
            "(10 Hz steps) [std]; no phase tracking in any RCS2 source",
        cfo="TR 101 545-4: 0.005-0.03 (0.5-3 % of Rs) [std]; Griebel simulates |f| <= 0.015 [paper]; ours 0.03 = "
            "the top of the range",
        loss="Griebel best DA-KS 0.12-0.15 dB vs genie at FER 1e-3 [paper]; TR bench, all impairments: ~0.5 dB "
             "(QPSK 1/3), ~0.6 dB (QPSK 1/2) at PER 1e-5 [std]; ours ~0 dB except 1/10 (0.63 dB, 1/20 alias)",
        rates="turbo, ideal-sync AWGN, PER 1e-3 (TR 101 545-4 10.2.1) [std], net SE [derived]: ID 42 BPSK 1/3 "
              "(3236 sym) -3.81 dB 0.304; ID 43 BPSK 1/2 -1.53 dB 0.465; ID 13 QPSK 1/3 (1616) -0.80 dB 0.609; "
              "ID 3 QPSK 1/3 (536) -0.27 dB 0.567; ID 2 (262) 0.50 dB 0.427; ID 14 QPSK 1/2 (1616) 1.49 dB 0.931; "
              "ID 4 QPSK 1/2 (536) 1.92 dB 0.881; at the same Es/N0 0.56-1.13x our SE (ID 42 0.95x with the bench loss)",
        verdict="our version is STRONGER than the real system because it gets a metric-ordered CRC search, an "
                "8192-point FFT, the exact LS phase and genie timing; the deployed chain would be 0.1-0.5 dB worse",
        src="[EN 301 545-2 V1.5.1](https://www.etsi.org/deliver/etsi_en/301500_301599/30154502/01.05.01_60/"
            "en_30154502v010501p.pdf), [TR 101 545-4 V1.2.1](https://www.etsi.org/deliver/etsi_tr/101500_101599/"
            "10154504/01.02.01_60/tr_10154504v010201p.pdf), [Griebel 2021](https://ars.copernicus.org/articles/19/59/"
            "2021/); lit_card_sat.md 1, lit_rates.md 4.3"),
    "rcs2pp": dict(
        std="as DVB-RCS2 (EN 301 545-2 V1.5.1) [std]", deploy="as DVB-RCS2",
        layout="the pilotless RCS2 format: ID 15, 1616 symbols, QPSK 2/3, pre / post 16 / 16, no pilots (2.0 % "
               "known) [std]; ours 16 + 16 around 1024 data (0.13 dB): equivalent",
        est="Griebel 2021: NDA |r| e^{j4 arg r} FFT for pilotless bursts, QPSK NDA used only at Es/N0 >= 3.9 dB "
            "[paper]; one shot, no decoder step",
        cfo="as DVB-RCS2 (0.005-0.03) [std]", loss="not published for the NDA chain",
        rates="the pilotless QPSK 2/3 IDs 5 / 15 need 3.90 / 3.46 dB (above our range) [std]; every RCS2 waveform "
              "in -5 ... +3 dB carries pilots (IDs 2-4, 13, 14, 42, 43: see RCS2-13)",
        verdict="our version is MIXED vs the real system: its CRC lobe search is stronger than the real NDA chain, "
                "but we run a pilotless 4th-power layout at -5 ... +3 dB, which RCS2 uses only above 3.4 dB",
        src="lit_card_sat.md 1.2-1.3, lit_rates.md 4.3"),
    "generic": dict(
        std="no single real system (pre128: TR 101 545-4 preamble-only assumption, Comtech / DOCSIS class; split64: "
            "Ying & Ghogho 2005 placement, Hughes class); not surveyed in the 2026-11-15 card reports",
        deploy="not covered", layout="generic layout chosen by us", est="not covered", cfo="not covered",
        loss="not covered",
        rates="nearest real modem table: Comtech DMD1050TS (SCPC continuous, BER 1e-5, guaranteed) [vendor]: BPSK "
              "TPC 5/16 -2.59 dB SE 0.31; BPSK turbo 1/2 -1.24 dB 0.497; BPSK LDPC 1/2 -1.01 dB 0.50; BPSK turbo "
              "2/3 0.77 dB 0.656; QPSK turbo 1/2 1.72 dB (1.32 typ.) 0.982; QPSK LDPC 1/2 2.0 dB 1.00: 0.73-1.02x "
              "our SE",
        verdict="not rated: a generic layout with no single real system to compare against",
        src="[Comtech DMD1050TS](https://comtech.com/wp-content/uploads/2022/04/ds-DMD1050TS.pdf); lit_rates.md 3"),
    "vde": dict(
        std="ITU-R M.2092-2 (02/2026) Annex 2 Tables 9-11 + Annex 5 [std]; IALA G1139 ed. 3 (2019) cross-check [std]",
        deploy="NorSat-2 (2017; ESA downlink verification, Kongsberg Seatex receivers, 103 passes) [agency]; "
               "Andreotti 2021/23 uplink Link ID 20 trial [paper]; SATMAR (Alen Space, 2025) [vendor]; still in "
               "trials",
        layout="SAT-MCS-1.50-1 (Link ID 26): 27-symbol syncword every 2268 + 1 pilot / 27 (first +14), no link ID "
               "on the downlink, ramp 14 + 14, 80 371-symbol burst, 4.8 % known (0.21 dB) [std, derived]; ours: the "
               "same pattern in a 1090-symbol window, 66 known (0.27 dB): faithful, 0.06 dB more energy",
        est="Ma 2018: correlator bank of Doppler-shifted known sequences, then an autocorrelation-argument fine "
            "stage, +-4 kHz [paper, abstract]; Andreotti: DA 'such as R-B' on preamble / pilots + pilot phase "
            "[snippet]; tracked over 35 syncwords / 2940 pilots per 2.4 s burst",
        cfo="LEO Doppler +-4 kHz + 1 ppm (160 Hz) at 33.6 ksym/s = up to +-0.124 (4.1x ours), drifting ~50 Hz/s "
            "[std, derived]; ours +-0.03 static",
        loss="not found (Ma 2018: 'approximate to the CRB' only; NorSat-2 page gives no numbers)",
        rates="turbo, AWGN, PER not stated (M.2092-2 T10-11) [std], net SE [derived]: SAT-MCS-0.50-2 (ID 32) "
              "BPSK/CDMA 1/4 -4.5 dB 0.19 (0.88x ours); 0.50-3 (ID 33) BPSK 1/3 -3.6 dB 0.325 (1.14x); 1.50-1 (ID 26, "
              "the C6 layout) pi/4-QPSK 1/4 -2.4 dB 0.475 (1.11x); 1.50-2 (ID 34) pi/4-QPSK 1/3 -0.6 dB 0.633 "
              "(0.99x); the 27 / 27 comb is designed for -2.4 and -0.6 dB only, -4.5 dB is BPSK/CDMA SF 8 with "
              "48-symbol syncwords and a pilot every 8 (22.7 % known)",
        verdict="our version is MIXED vs the real system: faithful layout and estimator family, stronger by the "
                "smaller CFO range and the CRC lobe search, weaker by one syncword (vs tracking 35) and 0.06 dB more "
                "energy; at 1/10 and 0.15 it runs 1-2.6 dB below the layout's -2.4 dB design point",
        src="[M.2092-2](https://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.2092-2-202602-I!!PDF-E.pdf), [Ma 2018]"
            "(https://ieeexplore.ieee.org/document/8780774/); lit_card_space.md 5, lit_rates.md 4.5"),
    "s2": dict(
        std="ETSI EN 302 307-1 V1.4.1 (DVB-S2) and EN 302 307-2 V1.4.1 (2024; V1.3.1 read, DVB-S2X) [std]; TR 102 "
            "376-1 / -2 [std]",
        deploy="forward / broadcast continuous TDM (DTH, VSAT outbound); > 1.5 billion DVB receivers (all DVB, 2019) "
               "[std body]; S2X modems Newtec, Hughes, iDirect, Creonic [vendor]; bursts only as S2X superframe / "
               "beam hopping and S2X-in-TDMA on the RCS2 V1.5.1 return link [std]",
        layout="PLHEADER 90 (SOF 26 + PLS 64, pi/2-BPSK) + optional 36-symbol pilot block every 16 slots (period "
               "1476); short QPSK frame 8370 symbols, 270 known (3.2 %) [std, derived]; a 1024-symbol window after "
               "the header holds NO pilot block, and in ACM / VCM only the 26-symbol SOF is known before PLS "
               "decoding; ours: 90 + one 36-block (126, 0.50 dB, period 602)",
        est="multi-frame: pilot FLL coarse + Luise-Reggiannini fine over ~1000 pilot blocks, per-block ML phase + "
            "interpolation (TR 102 376-1) [std]; MathWorks VL-SNR chain: FLL 20 % -> ~2 %, pilot fine 3.5 %, 9-25 "
            "acquisition frames [vendor]; no decoder-aided step (research only)",
        cfo="acquisition 0.2 (Ku LNB +-5 MHz at 25 Mbaud) over many frames; single frame / tracking 3.4e-4 ... 0.01 "
            "(VL-SNR detector designed for <= 1 % of Rs) [std]; ours 0.03 in one burst",
        loss="sync loss QPSK 1/2 ~0.1 dB, 8PSK 2/3 ~0.25 dB; L&R RMS 6e-5 at -2 dB with 1000 blocks [std]",
        rates="LDPC, ideal-sync AWGN [std], net SE with pilots [derived]: S2 (PER 1e-7, 64 800): QPSK 1/4 -2.35 dB "
              "0.479, 1/3 -1.24 0.641, 2/5 -0.30 0.771, 1/2 1.00 0.965, 3/5 2.23 1.160; S2X (FER 1e-5): BPSK 11/45 "
              "-5.50 0.230, BPSK 4/15 short -4.9 <= 0.244, BPSK 1/3 -4.00 0.317, QPSK 2/9 -2.85 0.425, 11/45 short "
              "-2.50 0.444, 13/45 -2.03 0.554, 14/45 short -1.46 0.573, 9/20 0.22 0.868, 7/15 short 0.60 0.874, "
              "8/15 short 1.45 1.003, 11/20 1.45 1.063: 1.06-1.32x our SE, mostly from 16k-65k-bit blocks",
        verdict="our version is STRONGER than a real 1024-symbol DVB-S2 segment because it adds a pilot block the "
                "window does not contain, treats all 90 header symbols as known (CCM) and has genie timing (the "
                "real multi-frame tracking chain does not apply to one burst)",
        src="[EN 302 307-1](https://www.etsi.org/deliver/etsi_en/302300_302399/30230701/01.04.01_60/"
            "en_30230701v010401p.pdf), [EN 302 307-2](https://www.etsi.org/deliver/etsi_en/302300_302399/30230702/"
            "01.03.01_60/en_30230702v010301p.pdf); lit_card_sat.md 2, lit_rates.md 4.1-4.2"),
    "ccsds": dict(
        std="CCSDS 131.2-B-2 (2023, SCCC) + 130.11-G-2 (2023, reference receiver) [std]; 131.0-B-5 (2023, "
            "ASM-only TM coding) [std]",
        deploy="high-rate EO downlink; HW validation Tesat EM transmitter + Kongsberg Spacetec receiver at 500 MBaud "
               "[std]; ground receivers Safran Cortex HDR (1000+ units), Kongsberg HRDFEP [vendor]; named 131.2 "
               "flight missions: not found",
        layout="131.2: 320-symbol header (256 FM + 64 FD) + 16 x 15 x (540 data + 16 pilots), 133 760 symbols, "
               "3.06 % known (0.14 dB) [std, derived]: a 1024-data window holds ~30 known, aliases 1/556; ours 8 x "
               "16 = 128 (0.51 dB), block period 162.3 (aliases 0.0062): 3.7x the real pilot density",
        est="frame-level 2nd-order FLL (1024-point FFT of the FM + Newton, k1 = 0.2), DA ML phase per 16-symbol "
            "field + linear interpolation, no DD or code-aided step; acquisition not simulated [std]; Bertolucci "
            "2021: M&M + Fitz Type II FLL [paper]",
        cfo="130.11 test case 0.01-0.02 (1 MHz + 1 MHz Doppler at 100 MBaud) [std]; ~0.2 at 5 Mbaud, 0.002 at 500 "
            "Mbaud (Bertolucci) [paper]; acquired by a multi-frame FLL, never in one burst",
        loss="sync chain 0.2-0.4 dB at CER 1e-4 (0.2-0.8 dB with a TWTA) [std]; vendor < 0.5 dB (Cortex CRT; "
             "HRDFEP snippet) [vendor]",
        rates="SCCC lowest ACM format (QPSK) -0.58 dB at CER 1e-4 [std]; 131.0 turbo k 8920, BER 1e-6 ~ FER 1e-4 "
              "[std, derived Es/N0]: 1/6 -4.87 dB 0.332 (1.78x ours), 1/4 -2.86 0.498 (1.34x), 1/3 -1.36 0.664 "
              "(1.21x), 1/2 1.10 0.996 (1.15x); AR4JA LDPC (2048, 1024) r 1/2 = our N, K: 2.20 dB at BLER 1e-5, "
              "0.985 (1.00x) [vendor]",
        verdict="our version is MIXED vs the real system: STRONGER in estimation (3.7x the pilot density, 3.4x wider "
                "alias spacing, CRC lobe search), WEAKER in energy (0.51 vs ~0.13 dB charged); the real receiver's "
                "CFO is already tracked by its multi-frame FLL",
        src="[131.2-B-2](https://public.ccsds.org/Pubs/131x2b2.pdf), [130.11-G-2](https://public.ccsds.org/Pubs/"
            "130x11g2.pdf), [130.1-G-3](https://public.ccsds.org/Pubs/130x1g3e1.pdf); lit_card_space.md 2-4, "
            "lit_rates.md 4.4"),
    "viasat": dict(
        std="patents US 7653150 B2 (2010, expired 2022; continuation of US 7200185) and US 8243859 B2 (2012, "
            "active) [patent]; no standard",
        deploy="GEO return link of a star MF-TDMA VSAT system (7653150); gateway or mesh terminal (8243859) "
               "[patent]; Viasat bought ECC in 2005 (IPSTAR modem chips) [vendor]; product running these "
               "algorithms: not found",
        layout="7653150: 512 QPSK symbols, no preamble, 16-symbol midamble UW inside the coded burst (26 dedicated "
               "TPC bits, 3.1 % known) [patent, my reading]; 8243859: UW length not stated; ours: 16 extra symbols "
               "(0.07 dB): ~equal cost",
        est="7653150: phase x 4 LUT, 1024-point FFT, single peak + 3-bin average, frequency AND phase from the "
            "4th-power bins / 4, UW only for the pi/2 ambiguity and +-8 symbol timing; 8243859: top-N peaks (32 of "
            "1024, N adapted to SNR) x UW positions, joint metric [patent]; one shot, no decoder step",
        cfo="7653150: up to 0.1 (10 % of Rs; a patent design statement, no product spec) [patent]; 4th-power range "
            "+-1/8 [derived]; ours 0.03",
        loss="~0.2 dB sync degradation; sync fails just below the FEC threshold [patent]; 8243859: burst error "
             "< 1e-5 at 2.5 dB, N = 32 [patent]",
        rates="TPC (32,26)^2 rate 0.66, BER 1e-5 at Eb/N0 1.4 dB = Es/N0 ~2.6 dB [patent, derived]; no public "
              "ViaSat burst-modem threshold table (LinkWay S2 datasheet 404); its return links use DVB-RCS / RCS2 "
              "waveforms (see RCS2-13)",
        verdict="our version is MIXED vs the real system: it merges the two patents and adds a CRC search and genie "
                "timing (stronger), but takes its phase from the 16 UW symbols instead of the 4th-power bins (std "
                "0.31 / 0.18 / 0.14 rad at -5 / 0 / +2 dB), so it is WEAKER at 2/5 and 1/2, the only rates where "
                "it works",
        src="[US 7653150](https://patents.google.com/patent/US7653150B2/en), [US 8243859](https://patents.google.com/"
            "patent/US8243859); lit_card_sat.md 3, lit_rates.md 4.9"),
    "nbiot": dict(
        std="3GPP TS 36.211 cl. 10.1 (NPUSCH, DMRS 10.1.4), Rel-13 on; IoT-NTN Rel-17 / 18 [std]",
        deploy="32 NB-IoT networks by early 2018 (GSMA) [vendor]; Qualcomm FSM small-cell eNB (Chakrapani 2019) "
               "[paper]; NTN: Skylo GEO Rel-17 (Soracom launch 07/2024), Sateliot LEO, Sony ALT1250 / u-blox / "
               "Quectel / Telit modules [vendor]",
        layout="single-tone NPUSCH format 1: 1 DMRS in 7 SC-FDMA symbols (symbol 3 at 15 kHz, 4 at 3.75 kHz), "
               "pi/2-BPSK / pi/4-QPSK [std, paper]: our 1/7 comb (171 in 1195, 0.67 dB) is structurally exact; "
               "multi-tone / LTE PUSCH use an M-sample DMRS block per 7 symbols (not modelled)",
        est="Qualcomm FSM: 256-point FFT over the DMRS phases per 32 ms (single-tone) block + quadratic "
            "interpolation, search +-250 Hz, not iterative, no decoder step [paper]; CFO mostly removed by the UE "
            "locking to the downlink",
        cfo="UE +-0.1 / 0.2 ppm vs the DL [std] = 0.013 at 900 MHz, 15 kHz [derived]; DMRS range +-1 kHz = "
            "+-0.071, deployed search +-250 Hz = +-0.018 [paper, derived]; NTN without GNSS ~0.043 [derived]; ours "
            "0.03 with the full +-0.071 window",
        loss="not reported vs ideal sync; NPUSCH F1 1 tone 1 rep: 3GPP -2.1 dB, Qualcomm sim -4.5, bench -4.2 (70 % "
             "throughput); fixed point < 0.5 dB [paper]",
        rates="no AWGN MCS thresholds in 3GPP; low SNR by repetition (up to 128) + HARQ at 10 % BLER; LTE CQI 1-6 "
              "(QPSK, code rate 78-602 / 1024) at ~-7 ... +3 dB, 10 % BLER, OFDM (indicative) [std, paper]: not "
              "comparable",
        verdict="our version is STRONGER than the deployed one because its window is the full DMRS range +-0.071 "
                "instead of the deployed +-0.018 and R-B uses all 171 pilots coherently: an upper bound for "
                "DMRS-style receivers",
        src="[Chakrapani 2019](https://arxiv.org/abs/1906.07096), [NB-IoT primer](https://arxiv.org/pdf/1606.04171); "
            "lit_card_terr.md 1, lit_rates.md 4.7"),
    "zr": dict(
        std="OIF-400ZR IA 02.0 (2020) / 03.0 (2024) (PDF not parseable, not read) [std]; IEEE 802.3ct contribution "
            "(Zhang 2019) [std]",
        deploy="400ZR DCI coherent pluggables (DP-16QAM, 59.84375 GBd), proprietary vendor DSPs [vendor]; 800G LR "
               "moved the pilot interval 32 -> 64 [paper]",
        layout="1 QPSK pilot / 32 symbols (3.1 %) + an 11-symbol training sequence per 3712-symbol sub-frame (0.3 %) "
               "[std, derived]; ours: the 1/32 grid (33 pilots, 0.14 dB), no training sequence",
        est="continuous: training sequences for frame sync and initial frequency-offset locking, pilots for carrier "
            "phase (Wang 2025, unverified against the OIF IA) [paper]; fallback FFT-FOE + blind phase search; no "
            "decoder step",
        cfo="Rx tolerance +-1.8 GHz at 59.84 GBd = 0.030 (datasheets +-3.6 GHz = 0.060) [std, vendor, derived]; = ours",
        loss="not found (proprietary)", rates="none in -5 ... +3 dB (DP-16QAM CFEC threshold Es/N0 ~19 dB) [derived]",
        verdict="our version is MIXED vs the real system: WEAKER in observation length (one 1024-symbol burst, no "
                "training sequence, vs continuous averaging over millions of symbols) but STRONGER in its "
                "decoder-checked lobe search; cited only for the +-0.03 requirement",
        src="[Zhang 2019](https://www.ieee802.org/3/ct/public/19_05/zhang_3ct_01a_0519.pdf), [Wang 2025]"
            "(https://www.researching.cn/ArticlePdf/m00005/2025/23/6/060602.pdf); lit_card_terr.md 4"),
    "wifi": dict(
        std="IEEE 802.11-2020 (OFDM PHY cl. 17; the legacy preamble also in HT / VHT / HE) [std, not read; via "
            "MathWorks / Keysight]",
        deploy="every Wi-Fi chip runs the legacy L-STF / L-LTF preamble [vendor]; OpenOFDM open FPGA receiver [vendor]",
        layout="L-STF 160 samples (10 x 16) + L-LTF 160 (32 GI + 2 x 64) = 320 known at 20 MS/s: 1.18 dB if charged "
               "like ours [std, derived]; ours 8 x 16 = 128 (0.51 dB), the lag-64 stage on the same 16-periodic "
               "block (the real LTF is a separate 64-periodic sequence)",
        est="lag-16 L-STF autocorrelation coarse (range +-0.031), lag-64 L-LTF fine (+-0.0078); the coarse picks the "
            "fine lobe, no retry; pilot subcarriers track phase [vendor]; OpenOFDM runs only the lag-16 coarse "
            "stage [vendor]; no decoder step",
        cfo="+-20 ppm per side -> +-40 ppm relative = 0.0117 cycles/sample at 5.8 GHz, 0.0062 at 2.4 GHz [derived]; "
            "ours 0.03 (2.6-4.8x larger)",
        loss="not found (no readable STF / LTF RMSE or implementation-loss source)",
        rates="none in -5 ... +3 dB: 6 Mb/s (BPSK 1/2) sensitivity -82 dBm at PER 10 % ~ +4 dB SNR [std, derived]; "
              "802.11ad SC (different structure, not modelled) MCS 2-4 at ~0.5-2.5 dB, SE 0.44-0.66 = 0.56-0.67x "
              "ours [std via Wikipedia, derived]",
        verdict="our version is MIXED vs the real system: fewer known samples (128 vs 320) and no phase tracking "
                "(weaker), but 0.51 instead of 1.18 dB energy and a CRC search over +-4 fine lobes the real chip "
                "does not have (stronger)",
        src="[wlanCoarseCFOEstimate](https://www.mathworks.com/help/wlan/ref/wlancoarsecfoestimate.html), [OpenOFDM]"
            "(https://openofdm.readthedocs.io/en/latest/freq_offset.html); lit_card_terr.md 2, lit_rates.md 4.6"),
    "mil": dict(
        std="MIL-STD-188-110C with CN1, App C (= STANAG 4539, ITU-R F.763-5 Annex 6); superseded by MIL-STD-188-110D "
            "(29 Dec 2017) [std]",
        deploy="L3Harris Falcon III RF-7800H-MP (110C App D in 2019, 110D in 2022; 50 000 Falcon III units by 2023) "
               "[vendor]",
        layout="App C: 287-symbol preamble (184 sync / Doppler + 103 rate / interleaver incl. a 31-symbol "
               "mini-probe), then 256 data + 31-symbol mini-probe frames, +72 known every 72 frames: 411 known per "
               "1024 data (1.47 dB) [std, derived]; ours 184 + 4 x 31 = 308 (1.14 dB) drops the 103-symbol section",
        est="preamble detection / Doppler removal, then probe- and equaliser-driven tracking (MathWorks 110A: "
            "cross-spectrum phase fit + PI loop + NCO, RLS DFE) [vendor]; no one-shot estimator published for App "
            "C / D; no decoder step",
        cfo="+-75 Hz at 2400 Bd = 0.031 (= ours), tested at 30 dB SNR; Doppler rate 3.5 Hz/s; low-SNR acquisition "
            "'not yet standardized' [std]",
        loss="not found",
        rates="none in -5 ... +3 dB with an AWGN requirement: 2400 bps serial 8PSK 1/2 Es/N0 ~11 dB; App C 3200 bps "
              "AWGN 9 dB SNR in 3 kHz (~10 dB Es/N0); App D WID 1-4 BPSK 1/8-2/3, SE 0.06-0.5 [std]",
        verdict="our version is STRONGER than the real App C because it charges ~0.33 dB less energy and adds an "
                "all-symbol R-B estimate and a CRC lobe search at SNRs the real modem does not specify (AWGN only)",
        src="[MIL-STD-188-110C](https://www.sigidwiki.com/images/c/c8/MIL-STD-188_110C_CHG_NOTICE-1.pdf), [F.763-5]"
            "(https://www.itu.int/dms_pubrec/itu-r/rec/f/R-REC-F.763-5-200501-P!!PDF-E.pdf); lit_card_terr.md 3, "
            "lit_rates.md 4.8"),
    "adv": dict(
        std="patents US 7590199 B2 (2009, hybrid estimator) + US 7593490 B2 (2009, joint synchroniser / decoder), "
            "Advantech; Alagha-Erup SPSC 2003 not found [patent]",
        deploy="DVB-RCS gen-1 MF-TDMA return link; Advantech DVB-RCS / S2 hubs and terminals to the US DoD (2010) "
               "[vendor]; whether products run the patented estimator: not found; ESA joint turbo decoding + "
               "carrier sync project (FPGA) [agency]",
        layout="48-symbol contiguous preamble + 440 payload = 488 symbols, QPSK, rate-1/2 turbo (9.8 % known) "
               "[patent]; ours 16 + 16 pre / post (0.13 dB): a 1/1040 fringe comb instead of one ~1/48 DA lobe "
               "that gates the 4th-power peaks",
        est="DA (r c*) and NDA (phase x 4) log spectra summed with weights, 3 candidates by peak removal + "
            "parabolic interpolation (7590199); per candidate: derotation, decision-aided phase tracking, partial "
            "turbo decoding (1-3 of ~10 iterations), pick the largest mean |LLR| (7593490) [patent]",
        cfo="Ka 1e-8 RMS x 6 = +-1800 Hz at 64 kBd = +-0.028 [patent, derived]; = ours",
        loss="no numbers published [patent]",
        rates="rate-1/2 turbo QPSK, threshold not published; DVB-RCS / RCS2 waveforms are the proxy (see RCS2-13)",
        verdict="our version is MIXED vs the real system: the candidate choice (CRC + rho over candidates and lobes) "
                "is STRONGER than mean |LLR|, but the 16 + 16 layout is WEAKER than the patent's 48-symbol preamble "
                "(no gating lobe) and the phase is constant instead of decision-aided tracking",
        src="[US 7590199](https://patents.google.com/patent/US7590199), [US 7593490](https://patents.google.com/"
            "patent/US7593490); lit_card_sat.md 4"),
}
CARD_SYS = {"RCS2-13": "rcs2", "RCS2-13 track": "rcs2", "G4096": "rcs2", "G2048": "rcs2", "G2048N": "rcs2",
            "Griebel faithful": "rcs2", "RCS2-13 lobes": "rcs2", "RCS2 pre/post": "rcs2pp",
            "pre128 ML": "generic", "pre128 M&M": "generic", "split64 ML": "generic", "split64 ML interp": "generic",
            "VDE-SAT": "vde", "VDE-SAT track": "vde", "DVB-S2 style": "s2", "CCSDS style": "ccsds",
            "CCSDS style blocks": "ccsds", "CCSDS style track": "ccsds", "ViaSat UW": "viasat", "DMRS 1/7": "nbiot",
            "DMRS 1/7 track": "nbiot", "Sparse pilots 1/32": "zr", "WiFi pre128": "wifi", "MIL-110 HF": "mil",
            "MIL-110 HF track": "mil", "hyb3": "adv"}
VERDICT = {  # per-card verdicts where the card differs from its system's default
    "RCS2-13 track": "our version is STRONGER than the real system: as RCS2-13, plus a Kalman / RTS phase tracker that "
                     "no DVB-RCS2 source has",
    "Griebel faithful": "our version is MIXED vs the real system: the paper's one-decode chain (faithful) with genie "
                        "timing (stronger) and |f| <= 0.03 instead of the paper's 0.015 (harder)",
    "RCS2-13 lobes": "our version is STRONGER than the real system: as RCS2-13, plus a +-1/20 alias-lobe search no "
                     "RCS2 source has",
    "CCSDS style track": "our version is MIXED vs the real system: as CCSDS style, plus a Kalman / RTS tracker "
                         "stronger than the standard's linear interpolation"}
NO_REAL = {"Blind": "none: ours (no preamble, no pilots); spectral efficiency vs the real systems in section E",
           "Genie": "none: lower bound; spectral efficiency vs the real systems in section E"}
# section E: lit_rates.md section 6 (per operating point) and the recomputed normal-approximation bound
SE_POINTS = [("1/10", "1e-4", 0.403, 0.300), ("0.15", "1e-3", 0.520, 0.427), ("2/5", "1e-3", 1.065, 0.959),
             ("1/2", "1e-3", 1.251, 1.149)]            # (rate, BLER, QPSK capacity, max SE of a 1024-symbol packet)
SE_KCRC = {"1/10": 205, "0.15": 307, "2/5": 819, "1/2": 1024}   # K incl. CRC-16; net SE = (K - 16) / 1024
SE_BEST = [
    ("1/10, -4.9 dB, 0.185", "CCSDS turbo 1/6, k 8920: 0.332 (x1.78). S2X BPSK 4/15 short: <= 0.244 (x1.32). S2X "
     "BPSK 11/45: 0.230 at 0.6 dB lower. VDE-SAT 0.50-2: 0.19 at +0.4 dB (x0.88). No DVB-RCS2 mode.",
     "Behind the long-block standards; only part is closable at 1024 symbols (the bound allows 0.300); the largest "
     "code gap of our four rates"),
    ("0.15, -3.6 dB, 0.284", "VDE-SAT 0.50-3: 0.325 (x1.14). RCS2 ID 42: 0.304 (x1.13 ideal, x0.95 with the bench "
     "loss). S2X BPSK 1/3 medium: 0.317 at -4.0 dB (x1.25).",
     "Slightly behind on paper (10-25 %); about a tie with the short-burst ID 42 once its real loss is counted"),
    ("(gap) -2.9 ... -1 dB", "CCSDS turbo 1/4 (0.498 at -2.86), VDE-SAT 1.50-1 (0.475 at -2.4), S2 QPSK 1/4 (0.48 "
     "at -2.35), S2X 13/45 (0.55 at -2.03)", "We have no rate here (a rate ~1/4, SE ~0.48, would fill it; not tested)"),
    ("2/5, 0.61 dB, 0.784", "S2X QPSK 7/15 short: 0.874 (x1.12). S2 QPSK 2/5 normal: 0.77-0.79 at 0.9 dB lower. "
     "RCS2 ID 13 / VDE-SAT 1.50-2: ~0.6 (x0.8 at 0.61).", "Behind S2X by ~12 % at 16 200-bit frames; ahead of the "
     "short-burst standards"),
    ("1/2, 1.79 dB, 0.984", "S2X QPSK 11/20 normal: 1.06 at 1.45 dB; 8/15 short: 1.00 at 1.45 dB; S2 QPSK 1/2: 0.97 "
     "at 1.00 dB; CCSDS turbo 1/2: 1.00 at 1.10 dB; RCS2 ID 14: 0.931 at 1.49 dB; CCSDS LDPC (2048, 1024): 0.985 at "
     "2.20 dB @ 1e-5; Comtech QPSK turbo 1/2: 0.982 at 1.72 dB guaranteed", "Equal SE; the long-block standards need "
     "0.3-0.8 dB less Es/N0; the same-length LDPC (2048, 1024) is equal or behind")]


# ============================================================================================== helpers
def fnum(v, d=2):
    return "-" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{d}f}"


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        o = o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


def ksn(k, n):
    return f"{k}/{n // 1000}k" if n % 1000 == 0 else f"{k}/{n}"


def bler_ci(k, n):
    lo, hi = PF.cp(k, n)
    return k / n, lo, hi


def fmt_bler(k, n):
    if k == 0:
        return f"0 (< {3 / n:.1e}, 95 %)"
    b, lo, hi = bler_ci(k, n)
    return f"{b:.2e} [{lo:.1e}, {hi:.1e}]"


def compress(segs):
    """run-length string of a layout's (kind, length) runs, periods 1-3"""
    out, i = [], 0
    while i < len(segs):
        best = (1, 1)
        for p in (1, 2, 3):
            r = 1
            while segs[i + r * p:i + (r + 1) * p] == segs[i:i + p] and i + (r + 1) * p <= len(segs):
                r += 1
            if r > 1 and r * p > best[0] * best[1]:
                best = (r, p)
        r, p = best
        s = " ".join(f"[{k} {l}]" for k, l in segs[i:i + p])
        out.append(f"({s}) x {r}" if r > 1 else s)
        i += r * p
    t = " ".join(out)
    if len(t) > 160:
        ks = [l for k, l in segs if k == "k"]
        ds = [l for k, l in segs if k == "d"]
        t = (f"{len(ks)} known fields (sizes {sorted(set(ks))}), {len(ds)} data runs (lengths {sorted(set(ds))}); "
             f"starts {t[:90]} ...")
    return t


# ============================================================================================== jobs and validation
def jobs():
    """{part: dict(job, log, frames, min_err, seed, snrs, sources)} parsed from jobs/*.sh (est4 run_bler lines)"""
    out = {}
    for sh in sorted(glob.glob(os.path.join(PROJ, "jobs", "*.sh"))):
        txt = open(sh, encoding="utf-8", errors="replace").read()
        m = re.search(r">\s*(logs/\S+\.out)", txt)
        log = os.path.join(PROJ, m.group(1)) if m else None
        for line in txt.splitlines():
            if "est4/run_bler.py" not in line or "--part" not in line:
                continue
            g = lambda k: (re.search(rf"--{k} (\S+)", line) or [None, None])[1]
            snrs = re.search(r"--snrs ((?:-?[\d.]+ ?)+)", line)
            srcs = re.search(r"--sources (.*?) --part", line)
            out[g("part")] = dict(job=os.path.basename(sh)[:-3], log=log, frames=int(g("frames")),
                                  min_err=int(g("min-err")), seed=int(g("seed")), rate=g("rate"),
                                  snrs=[float(x) for x in snrs.group(1).split()] if snrs else [],
                                  sources=re.findall(r'"([^"]+)"|(\S+)', srcs.group(1)) if srcs else [])
    for v in out.values():
        v["sources"] = [a or b for a, b in v["sources"]]
    return out


def log_status(log):
    if not log or not os.path.exists(log):
        return dict(exists=False, all_done=False, eval_done=0, traceback=False)
    t = open(log, encoding="utf-8", errors="replace").read()
    return dict(exists=True, all_done="ALL DONE" in t, eval_done=t.count("EVAL DONE"), traceback="Traceback" in t)


def validate(J):
    """per part: file, log, requested vs present points / packets / sources; returns {part: dict}"""
    parts = []
    for d in (P4.MAIN, P4.PP, P4.MAIN5, P4.PP5, P4.ARSP):
        parts += [d[r] for r in RATES]
    parts += [q for r in RATES for q in P4.EXT5.get(r, [])]
    V = {}
    for p in parts + SMOKE + OTHER_SMOKE:
        j = J.get(p)
        path = os.path.join(P4.RES, f"bler_{p}.json")
        rows = P4.load(p)
        ls = log_status(j["log"] if j else None)
        same_job = [q for q, v in J.items() if j and v["job"] == j["job"]]
        idx = same_job.index(p) + 1 if j else 0
        issues = []
        if rows and j:
            if not ls["all_done"]:
                issues.append("log has no ALL DONE (job still running or failed)")
            if ls["traceback"]:
                issues.append("Traceback in log")
            if ls["eval_done"] < idx:
                issues.append(f"EVAL DONE {ls['eval_done']} < {idx} expected")
            have = {(r["src"], round(r["snr"], 3)) for r in rows}
            want = {(s, round(x, 3)) for s in j["sources"] for x in j["snrs"]}
            if want - have:
                issues.append(f"missing (src, snr): {sorted(want - have)}")
            for r in rows:
                if r["frames"] > j["frames"]:
                    issues.append(f"{r['src']} @{r['snr']}: {r['frames']} > requested {j['frames']}")
                elif r["frames"] < j["frames"] and j["min_err"] >= j["frames"]:
                    issues.append(f"{r['src']} @{r['snr']}: {r['frames']} < requested {j['frames']} without min-err stop")
                if r.get("seed") != j["seed"]:
                    issues.append(f"{r['src']} @{r['snr']}: seed {r.get('seed')} != job seed {j['seed']}")
            cnt = defaultdict(int)
            for r in rows:
                cnt[(r["rate"], r["src"], r["pn"], round(r["snr"], 3))] += 1
            issues += [f"duplicated row {k}" for k, c in cnt.items() if c > 1]
        early = sorted({(r["src"], r["snr"], r["frames"]) for r in rows if j and r["frames"] < j["frames"]})
        if not rows:
            status = "not run yet" + (" (job log present, running)" if ls["exists"] and not ls["all_done"] else
                                      "" if ls["exists"] else " (no part file, no log)")
        elif p in SMOKE or p in OTHER_SMOKE:
            status = "SMOKE"
        else:
            status = "ok" if not issues else "ISSUES"
        V[p] = dict(file=os.path.exists(path), n_rows=len(rows), job=j["job"] if j else None,
                    log=os.path.relpath(j["log"], PROJ).replace(os.sep, "/") if j and j["log"] else None, **ls, status=status,
                    issues=issues, early_stop=[list(e) for e in early],
                    requested=dict(frames=j["frames"], min_err=j["min_err"], seed=j["seed"]) if j else None)
    return V


# ============================================================================================== data
def part_data(rate, part):
    """plot_e4.e4(rate) restricted to ONE part: plot_e4.load answers the est4 main name with this part's rows"""
    orig = P4.load
    P4.load = lambda p: orig(part) if p == P4.MAIN[rate] else []
    try:
        return P4.e4(rate)
    finally:
        P4.load = orig


def nk_of(src):
    return 0 if src in ("Blind", "Genie") else E4C.layout(E4C.SOURCES[src][0])["nk"]


def collect(rate, V):
    """{receiver: dict(pts={snr_plot: point}, part, kind)}; merge rule in the module docstring"""
    R, notes = {}, []
    order = [(P4.MAIN[rate], "est4"), (P4.PP[rate], "est4"), (P4.MAIN5[rate], "est5"), (P4.PP5[rate], "est5"),
             (P4.ARSP[rate], "ars")] + [(q, "est5x") for q in P4.EXT5.get(rate, [])]
    for part, kind in order:
        if V[part]["status"] not in ("ok", "ISSUES") or not V[part]["all_done"]:
            continue
        for src, pts in part_data(rate, part).items():
            if kind == "est5" and src == "Genie":
                continue                                   # plot_e4 rule: est4's genie stays the reference
            if kind == "ars" and src == "RCS2-13":
                continue                                   # plot_e4 rule: the e4 packets again (regression-checked)
            if kind == "est5x" and src in R:              # low-SNR extension of an est5 row: other SNRs, merged
                for sx, v in pts.items():
                    if sx in R[src]["pts"]:
                        notes.append(f"{src} {sx:g} dB in both {R[src]['part']} and {part}: kept the first")
                        continue
                    R[src]["pts"][sx] = dict(v, below=sx < XMIN)
                R[src]["part"] += f" + {part}"
                continue
            name = src if src not in R else f"{src} [{part}]"
            if name != src:
                notes.append(f"{src} also in {part}: shown as its own row '{name}' (plot_e4.e4(e5=True) pools it "
                             f"with the est4 points at the same plotted SNR; here kept separate)")
            R[name] = dict(src=src, part=part, kind=kind, pts={})
            for s, v in pts.items():
                R[name]["pts"][s] = dict(v, below=s < XMIN)
    B = P4.blind(rate)
    ext = C.adopted(rate) if rate in C.S11_SNR else C.testing_hi(rate)
    bp = {}
    for s, v in B.items():
        e = ext.get(s)
        same = e is not None and e["err"] == v["err"] and e["n"] == v["n"]
        bp[s] = dict(v, snr=s, below=s < XMIN, x=e["dec"] if same else None, tot=e["macs"] if same else None,
                     p99=e["p99"] if same else None, p999=e["p999"] if same else None, pmax=e["pmax"] if same else None,
                     model=("testing (" + "+".join(e["parts"]) + ")") if same else
                     "presentation receiver (blind_ber.json, EP.BLIND_RX), MACs not counted")
    R = {"Blind": dict(src="Blind", part="agg_cmp", kind="blind", pts=bp), **R}
    return R, notes


def check_vs_plot_e4(rate, R):
    """differences between our merge and plot_e4.e4(rate, e5=True, ars=True) (what the figures draw); plot_e4 pools
    replicates (plot_e4.pool), so the rows of one src ("<src>" + "<src> [<part>]") are pooled here before comparing"""
    P = P4.e4(rate, True, True)
    mine = defaultdict(dict)                               # {src: {snr: (err, n)}} pooled over our rows of that src
    for d in R.values():
        if d["kind"] == "blind":
            continue
        for s, v in d["pts"].items():
            a = mine[d["src"]].get(s, (0, 0))
            mine[d["src"]][s] = (a[0] + v["err"], a[1] + v["n"])
    out = []
    for src, pts in P.items():
        for s, v in pts.items():
            m = mine.get(src, {}).get(s)
            if m != (v["err"], v["n"]):
                here = "-" if m is None else f"{m[0]}/{m[1]}"
                out.append(f"{src} @{s:g}: plot_e4.e4(e5, ars) {v['err']}/{v['n']} vs here (pooled) {here}")
    for src, pts in mine.items():                          # rows here that plot_e4 does not draw at all
        out += [f"{src} @{s:g}: here (pooled) {m[0]}/{m[1]} vs plot_e4.e4(e5, ars) -"
                for s, m in pts.items() if s not in P.get(src, {})]
    return out


def regression_ars(rate):
    """ARS part's RCS2-13 vs e4 RCS2-13: identical (err, n) at every point?"""
    a = {round(r["snr_plot"], 3): (r["frame_err"], r["frames"]) for r in P4.load(P4.ARSP[rate]) if r["src"] == "RCS2-13"}
    e = {round(r["snr_plot"], 3): (r["frame_err"], r["frames"]) for r in P4.load(P4.MAIN[rate]) if r["src"] == "RCS2-13"}
    if not a:
        return None
    return dict(points=len(a), same=sum(a[s] == e.get(s) for s in a))


def dup_check(R):
    seen, out = {}, []
    for name, d in R.items():
        if d["kind"] == "blind":
            continue
        for r in P4.load(d["part"]):
            k = (r["rate"], r["src"], round(r["snr"], 3), r.get("seed"), r["pn"])
            if r["src"] != d["src"]:
                continue
            if k in seen and seen[k] != d["part"]:
                out.append(f"{k} in {seen[k]} and {d['part']}")
            seen.setdefault(k, d["part"])
    return out


# ============================================================================================== required SNR
def use(pts, raw=False):
    """points >= -5 dB on the plotted axis (raw=True: re-keyed by the raw Es/N0, >= -5 dB on that axis)"""
    if raw:
        return {v["snr"]: v for v in pts.values() if v["snr"] >= XMIN}
    return {s: v for s, v in pts.items() if s >= XMIN}


def status(pts, t):
    """(value or None, text) of the required SNR at target t"""
    if not pts:
        return None, "not run"
    g = P4.gap_db(pts, t)
    if g is not None:
        return g, f"{g:.2f}"
    xs = sorted(pts)
    y = [pts[s]["err"] / pts[s]["n"] for s in xs]
    if y[0] < t:
        return None, f"< {xs[0]:g} (BLER {y[0]:.1e} at the lowest point >= -5 dB)"
    for a, b, ya, yb in zip(xs, xs[1:], y, y[1:]):
        if ya >= t and yb == 0:
            return None, f"in ({a:g}, {b:g}] (0 errors at {b:g}: not interpolated)"
    return None, f"fails (BLER >= {t:g} up to {xs[-1]:g} dB)"


def bracket(pts, g):
    xs = sorted(pts)
    a = max([s for s in xs if s <= g], default=None)
    b = min([s for s in xs if s > g], default=None)
    pres = lambda s: " (presentation rx)" if "presentation" in pts[s].get("model", "") else ""
    return " -> ".join(f"{ksn(pts[s]['err'], pts[s]['n'])} @{s:g}{pres(s)}" for s in (a, b) if s is not None)


def score(pred, val, txt):
    if pred is None:
        return "no numeric prediction"
    if pred == F:
        return "hit (fails)" if val is None and txt.startswith("fails") else f"miss (predicted fails, measured {txt})"
    lo, hi = pred
    ps = f"{lo:g}" if lo == hi else f"{lo:g} ... {hi:g}"
    if val is None:
        return f"{ps}: miss (measured {txt})"
    if lo - 0.005 <= val <= hi + 0.005:
        return f"{ps}: hit"
    d = val - hi if val > hi else val - lo
    return f"{ps}: miss by {d:+.2f} dB"


def summary(rate, t, R):
    rows = []
    Bp = use(R["Blind"]["pts"])
    gb, lob, hib = PF.req(Bp, t)
    cb, _ = PF.core_at(Bp, gb)
    for name, d in R.items():
        pts = use(d["pts"])
        g, txt = status(pts, t)
        lo = hi = None
        if g is not None:
            _, lo, hi = PF.req(pts, t)
        c, cnote = PF.core_at(pts, g) if g is not None else (None, "")
        gr, rtxt = status(use(d["pts"], raw=True), t) if d["kind"] != "blind" else (g, txt)
        nk = nk_of(d["src"])
        k = TK.index((rate, t))
        p = PRED.get(d["src"])
        rows.append(dict(receiver=name, src=d["src"], part=d["part"], req=g, req_txt=txt, ci=[lo, hi],
                         bracket=bracket(pts, g) if g is not None else "", raw_req=gr, raw_txt=rtxt,
                         gap=None if g is None or gb is None else g - gb, core=c, core_note=cnote,
                         ratio=None if c is None or cb is None or name == "Blind" else cb / c, nk=nk,
                         energy_db=10 * np.log10((N_SYM + nk) / N_SYM), airtime=100 * nk / N_SYM,
                         pred=(None if p is None else p[k]), pred_src=PRED_SRC.get(d["src"], "-"),
                         pred_macs=PRED_MACS.get(d["src"], "-"),
                         score=score(None if p is None else p[k], g, txt) if d["src"] in PRED else "-"))
    have = {d["src"] for d in R.values()}
    k = TK.index((rate, t))
    for src, p in PRED.items():                            # predicted receivers without data: "not measured yet"
        if src in have:
            continue
        nk = nk_of(src)
        pk = p[k]
        ps = "no numeric prediction" if pk is None else pk if pk == F else (
            f"{pk[0]:g}" if pk[0] == pk[1] else f"{pk[0]:g} ... {pk[1]:g}")
        rows.append(dict(receiver=src, src=src, part=None, req=None, req_txt="not measured yet", ci=[None, None],
                         bracket="", raw_req=None, raw_txt="-", gap=None, core=None, core_note="", ratio=None, nk=nk,
                         energy_db=10 * np.log10((N_SYM + nk) / N_SYM), airtime=100 * nk / N_SYM, pred=pk,
                         pred_src=PRED_SRC[src], pred_macs=PRED_MACS.get(src, "-"), score=f"{ps}: not measured yet"))
    return rows


# ============================================================================================== smoke
def smoke():
    out = []
    for part in SMOKE:
        rows = P4.load(part)
        if not rows:
            continue
        for rate in RATES:
            mac = part_data(rate, part)
            for r in rows:
                if r["rate"] != rate:
                    continue
                m = mac.get(r["src"], {}).get(round(r["snr_plot"], 3)) if r["pn"] == 0 else None
                out.append(dict(part=part, rate=rate, src=r["src"], pn=r["pn"], snr=r["snr"], snr_plot=r["snr_plot"],
                                err=r["frame_err"], n=r["frames"], und=r["undetected"],
                                x=r["extra_decodes_per_frame"], core=m["core"] if m else None))
    return out


# ============================================================================================== markdown
def md_cards(R_all):
    L = ["## A. Receiver cards", "",
         "Nk = known symbols sent in addition to the 1024 data symbols; pilot energy = 10 log10((1024 + Nk) / 1024) dB "
         "(charged on the SNR axis); airtime overhead = Nk / 1024 (08 8.3 quotes Nk / (1024 + Nk): 10.2 % for 116, 11.1 % for 128). window / lobes / n_hyp = the run_bler settings "
         "found in the part files (window = CRC-search half-width M in steps from the receiver's own CRB at that SNR, "
         "so it varies with SNR; lobes = lobe hypotheses each side; n_hyp = hypotheses per packet), as min-max over "
         "all points of the full and smoke parts.",
         "Our CFO range for every receiver: uniform |f| <= 0.03 cycles/symbol, static over the burst.", ""]
    runs = defaultdict(set)
    for p in [*P4.MAIN.values(), *P4.PP.values(), *P4.MAIN5.values(), *P4.PP5.values(), *P4.ARSP.values(), *SMOKE]:
        for r in P4.load(p):
            runs[r["src"]].add((r.get("window"), r.get("lobes"), r.get("n_hyp"), p))
    for src, c in CARDS.items():
        if src in ("Blind", "Genie"):
            nk, lay = 0, "none (1024 data symbols only)"
        else:
            ln = E4C.SOURCES[src][0]
            L_ = E4C.layout(ln)
            nk, lay = L_["nk"], f"`{ln}`, K = {L_['K']}: {compress(E4C._segments(ln))}"
        rr = runs[src]
        rg = lambda i: (lambda v: "-" if not v else (f"{min(v)}" if min(v) == max(v) else f"{min(v)}-{max(v)}"))(
            [x[i] for x in rr if x[i] is not None])
        st = f"window {rg(0)}, lobes {rg(1)}, n_hyp {rg(2)}" if rr else "-"
        where = sorted({p for *_, p in runs[src]})
        inlab = "yes" if src in LABELS or src == "Blind" else "**NO: plot_e4 never draws it**"
        L += [f"### {src}", "",
              f"- Real system / standard: {c['system']}",
              f"- Link: {c['link']}",
              f"- Known-symbol layout: {lay}",
              f"- Nk = {nk}; pilot energy {10 * np.log10((N_SYM + nk) / N_SYM):.2f} dB; airtime +{100 * nk / N_SYM:.1f} %",
              f"- Estimator chain: {c['est']}",
              f"- CRC / lobe search: {c['search']}" + (f" (part files: {st})" if st != "-" else ""),
              f"- Design CFO range of the real system vs our +-0.03: {c['cfo']}",
              f"- What we changed vs the real system: {c['changes']}",
              f"- Data: {', '.join(where) if where else ('agg_cmp (blind parts)' if src == 'Blind' else 'none yet')}; "
              f"label in plot_e4 STY / STY5 / STYA: {inlab}"] + md_real(src) + [""]
    return L


def real_block(src):
    """the card's REAL entry (with its per-card verdict) or None for Blind / Genie"""
    if src not in CARD_SYS:
        return None
    return dict(REAL[CARD_SYS[src]], system=CARD_SYS[src], verdict=VERDICT.get(src, REAL[CARD_SYS[src]]["verdict"]))


def md_real(src):
    r = real_block(src)
    if r is None:
        return [f"- Real system: {NO_REAL.get(src, 'not covered')}"]
    return ["- Real system (lit_card_sat / space / terr.md, lit_rates.md, 2026-11-15):"] + \
           [f"  - {RLAB[k]}: {r[k]}" for k in RF]


def md_se():
    """section E: lit_rates.md section 6 at our points + the recomputed finite-length bound"""
    L = ["## E. Spectral efficiency vs the real systems (lit_rates.md, 2026-11-15)", "",
         "Net SE = information bits per transmitted symbol, header / preamble / pilots / syncwords included; ours = "
         "(K - 16) / 1024 (CRC-16 not counted, no other overhead). Competitor thresholds are mostly ideal-sync AWGN "
         "table values at their own targets (S2 PER 1e-7, S2X FER 1e-5, RCS2 PER 1e-3, CCSDS BER 1e-6 ~ FER 1e-4, "
         "VDE-SAT unstated); ours are measured with blind CFO / phase recovery over +-0.03 (8.2a). Real implementation "
         "losses would move theirs 0.1-0.6 dB right. Per-system MODCOD lists: the Real system blocks of section A; "
         "full table: lit_rates.md section 3.", "",
         "### Best real SE at our operating points (lit_rates.md section 6)", "",
         "| Our point (rate, Es/N0, net SE) | Best competitor SE at the same Es/N0 (x = ratio to ours) | Verdict |",
         "|---|---|---|"]
    L += [f"| {a} | {b} | {c} |" for a, b, c in SE_BEST]
    L += ["", "Pilot / header overhead of these standards is 2-10 % SE (S2 normal 2.4 %, S2X short 2-3 %, VL-SNR "
          "7.5-10 %, RCS2 ID 13 / 14 7-9 %, VDE-SAT 2-5 %); the +5-20 % SE differences come mainly from block length "
          "(4-60x ours) and code / decoder quality.", "",
          "### Finite-length bound for a 1024-symbol packet (recomputed, lit_rates.md last section)", "",
          "Normal approximation (Polyanskiy-Poor-Verdu) for QPSK = 2 x BI-AWGN, n = 2048 real channel uses, log2 M ~ "
          "nC - sqrt(nV) Q^-1(eps) + 0.5 log2 n, C and V by numerical integration (QPSK capacity at 0 dB = 0.972 "
          "bits/symbol). Replaces the hand estimate of lit_rates.md section 2.", "",
          "| Our point | Es/N0 [dB] (blind, 8.2a) | BLER | QPSK capacity [bits/sym] | max SE of any 1024-symbol "
          "packet | ours (net SE) | ours / max |", "|---|---|---|---|---|---|---|"]
    for rate, t, cap, mx in SE_POINTS:
        se = (SE_KCRC[rate] - 16) / N_SYM
        L.append(f"| {rate} | {BLIND_82A[(rate, float(t))]:.2f} | {t} | {cap:.3f} | {mx:.3f} | {se:.3f} | "
                 f"{100 * se / mx:.0f} % |")
    return L + ["", "0.15 @ 1e-4 (-2.98 dB) is not in the bound table.", ""]


def md_data(rate, R, notes):
    L = [f"### R = {rate}", "",
         "| Receiver | part | SNR plotted [dB] | raw Es/N0 [dB] | errors / packets | BLER [95 % CI] | undetected | "
         "M MACs per core | extra decodes / frame |", "|---|---|---|---|---|---|---|---|---|"]
    excl = []
    for name, d in R.items():
        for s in sorted(d["pts"]):
            v = d["pts"][s]
            if v["below"]:
                excl.append(f"{name} @{s:g} ({ksn(v['err'], v['n'])})")
                continue
            pk = "" if v["n"] == 480000 or d["kind"] == "blind" else " *"
            x = v.get("x")
            xs = "-" if x is None else (f"{x:.3f}" if d["kind"] != "blind" else f"{x:.3f} (total)")
            und = "-" if v.get("und") is None else v["und"]
            mod = f" ({v['model']})" if d["kind"] == "blind" and "presentation" in v.get("model", "") else ""
            L.append(f"| {name}{mod} | {d['part']} | {s:g} | {v['snr']:.3f} | {ksn(v['err'], v['n'])}{pk} | "
                     f"{fmt_bler(v['err'], v['n'])} | {und} | {fnum(None if v.get('core') is None else v['core'] / 1e6, 3)} | {xs} |")
    L += ["", "`*` = fewer than 480k packets (pp parts: --min-err 200 early stop by design). Blind: packets per point as "
          "listed (testing model 64k-128k; presentation receiver up to 721k); its extra-decode column is the TOTAL "
          "CA-SCL-8 decodes per packet (agg_S `dec`).",
          f"Not shown (below -5 dB, rule): {', '.join(excl) if excl else 'none'}.", ""]
    L += [f"Note: {n}" for n in notes] + ([""] if notes else [])
    return L


def md_blind_tail(rate, R):
    L = [f"Blind MAC tails, R = {rate} (per-core histogram `ph_` of small_rx = the unscheduled crit_par count, upper bin "
         "edge; mean per core = scheduled count; mean total):", "",
         "| SNR | packets | mean total [M] | mean per core, scheduled [M] | 99 % [M] | 99.9 % [M] | max [M] | model |",
         "|---|---|---|---|---|---|---|---|"]
    for s, v in sorted(R["Blind"]["pts"].items()):
        if v["below"]:
            continue
        g = lambda k: fnum(None if v.get(k) is None else v[k] / 1e6, 3)
        L.append(f"| {s:g} | {v['n']} | {g('tot')} | {g('core')} | {g('p99')} | {g('p999')} | {g('pmax')} | {v['model']} |")
    return L + [""]


def md_summary(S):
    L = ["## C. Summary per target", "",
         "Required SNR on the plotted axis (pilot energy charged), points >= -5 dB only; CI = plot_final.req "
         "(Clopper-Pearson bound curves of the bracketing points; '-' = that bound does not cross). Gap = receiver - "
         "blind (+ = blind better). Raw axis = the same crossing vs the data symbols' Es/N0 (pilot energy NOT "
         "charged; secondary). MACs per core = scheduled count at the required SNR (plot_final.core_at). Ratio = "
         "blind / receiver MACs per core. Bracket = the two points the interpolation uses (errors / packets). "
         "Predictions: written before the runs; '-' = no numeric prediction.", ""]
    for (rate, t), rows in S.items():
        L += [f"### R = {rate} @ BLER {t:.0e}", "",
              "| Receiver | required [dB] | 95 % CI | bracket | raw-axis required | gap to blind | M MACs/core | "
              "blind / it | Nk (energy, airtime) | predicted (source): score | predicted MACs |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            ci = f"[{fnum(r['ci'][0])}, {fnum(r['ci'][1])}]" if r["req"] is not None else "-"
            core = "-" if r["core"] is None else f"{r['core'] / 1e6:.3f}{r['core_note']}"
            ratio = "-" if r["ratio"] is None else f"{r['ratio']:.1f}x"
            L.append(f"| {r['receiver']} | {r['req_txt']} | {ci} | {r['bracket']} | {r['raw_txt']} | "
                     f"{fnum(r['gap'])} | {core} | {ratio} | {r['nk']} ({r['energy_db']:.2f} dB, {r['airtime']:.1f} %) | "
                     f"{r['score']}{'' if r['score'] == '-' else ' (' + r['pred_src'] + ')'} | {r['pred_macs']} |")
        L.append("")
    return L


def md_smoke(SM):
    L = ["## SMOKE (800 packets per point; est5 e5-smoke-a/b/c, seed 61): NOT for claims", "",
         "| part | rate | receiver | pn | raw Es/N0 | SNR plotted | errors / packets | BLER [95 % CI] | undetected | "
         "extra decodes / frame | M MACs/core |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in SM:
        L.append(f"| {r['part']} | {r['rate']} | {r['src']} | {r['pn']:g} | {r['snr']:g} | {r['snr_plot']:.3f} | "
                 f"{r['err']}/{r['n']} | {fmt_bler(r['err'], r['n'])} | {r['und']} | {r['x']:.3f} | "
                 f"{fnum(None if r['core'] is None else r['core'] / 1e6, 3)} |")
    return L + ["", "pn 1e-4 rows (e5-smoke-c): MACs not computed (plot_e4.e4 keeps pn 0 only).", ""]


def md_validation(V, extra):
    L = ["## Validation", "",
         "| part | job | log | ALL DONE | EVAL DONE | Traceback | rows | status | issues / early stops |",
         "|---|---|---|---|---|---|---|---|---|"]
    for p, v in V.items():
        iss = "; ".join(v["issues"][:6]) + (f" (+{len(v['issues']) - 6})" if len(v["issues"]) > 6 else "")
        es = f"{len(v['early_stop'])} points < requested (min-err {v['requested']['min_err']})" if v["early_stop"] else ""
        L.append(f"| {p} | {v['job'] or '-'} | {v['log'] or '-'} | {'yes' if v['all_done'] else 'no'} | "
                 f"{v['eval_done']} | {'YES' if v['traceback'] else 'no'} | {v['n_rows']} | {v['status']} | "
                 f"{'; '.join(x for x in (iss, es) if x) or '-'} |")
    return L + [""] + [f"- {x}" for x in extra] + [""]


def md_repro(RP):
    L = ["## Reproduction check (8.2a, final_table.md, expected_ars.md 'Measured')", "",
         "Computed with the 8.2a method (plot_e4.gap_db on ALL points, as 8.2a did) and with the -5 dB rule used in "
         "this file. ok = equal after rounding to 0.01 dB.", "",
         "| Receiver | source | target | reference | 8.2a method | this file (>= -5 dB) | check |", "|---|---|---|---|---|---|---|"]
    for r in RP:
        L.append(f"| {r['src']} | {r['ref_src']} | {r['rate']} @{r['t']:.0e} | {fnum(r['ref']) if r['ref'] is not None else 'fails'} | "
                 f"{r['all_txt']} | {r['rule_txt']} | {r['check']} |")
    return L + [""]


def caveats(tw, seeds):
    return ["## D. Fairness and caveats (from competitors.md, 'Assumptions' and 'Is the comparison fair?')", "",
            "- \"Timing and burst detection are assumed known for every receiver, blind included (out of scope for now, "
            "user 2026-11-15). In a real system the preamble also does detection and timing, so this assumption favours "
            "blind: the comparison is CFO/phase + decoding only.\"",
            "- \"Same FEC for all (our polar N = 2048 + CRC-16, CA-SCL-8); real systems use turbo / LDPC / BCH.\" Same "
            "re-encoding check (RHO_N) and metric-ordered CRC search (incl. alias / lobe hypotheses) for all.",
            "- \"Blind is NOT packet-paired with the est4 competitors (different harness and seeds); est4 competitors are "
            "paired with each other. Differences below ~0.1 dB between blind and a competitor are inside this unpaired "
            "noise.\" Seeds in the included parts: " + seeds + "; the ARS variants are paired with RCS2-13 (same seeds and "
            "bursts); est5 jobs use seeds 62-65, so est5 will not be packet-paired with est4 either.",
            "- \"Complexity is modelled (MACs per core, scheduled count), not measured on hardware.\"",
            "- \"CFO uniform in +-0.03 cycles/symbol for everyone. Several real systems are designed for a smaller range "
            "(DVB-S2 header acquisition, CCSDS, Wi-Fi fine stage); we widen them with their own lobe / alias CRC search "
            "rather than reject them. Static CFO.\"",
            "- \"Pilots are OUTSIDE the packet ... Pilot energy is charged\" (SNR = Es/N0 + 10 log10((1024 + Nk) / 1024)); "
            "the airtime cost (Nk / 1024) is reported, not charged. The raw-axis required SNR in section C is the "
            "secondary view where the pilot energy is NOT charged.",
            "- Blind = the testing model (plot_e4.blind): 1/10, 0.15 = run.py testing_s11g, 64k packets per SNR; 2/5 = "
            "testing at 0.5, 1.0 dB only; 1/2 = testing at 2.0, 2.5 dB, and the **1/2 1.5 dB point is still the "
            "presentation receiver (mixed model)** until the running tw25 job lands. The other points without MACs are "
            "presentation-receiver points too.",
            f"- tw parts (testing model over the full range, expected_tw.md): {tw}. plot_e4.blind (agg_cmp.adopted / "
            "qfix) pools every landed tw part (agg_cmp TW_PARTS / TW_QFX) per SNR, so they enter sections B-D here "
            "as soon as they land.",
            "- Genie at 1/10: 8.2a's -5.19 dB interpolates with its -5.5 dB point; under the -5 dB rule it is only "
            "'< -5.0' here. RCS2-13 at 1/10 -5.03 dB plotted (raw -5.5, 881 / 480k) and the RCS2 pre/post -5.37 dB "
            "point are likewise not shown.", ""]


# ============================================================================================== main
def main():
    J = jobs()
    V = validate(J)
    data, notes, diffs, regr, dups = {}, {}, {}, {}, []
    for rate in RATES:
        data[rate], notes[rate] = collect(rate, V)
        diffs[rate] = check_vs_plot_e4(rate, data[rate])
        regr[rate] = regression_ars(rate)
        dups += dup_check(data[rate])
    S = {(r, t): summary(r, t, data[r]) for r, t in TARGETS}
    # reproduction
    RP = []
    for src, (rs, vals) in REF.items():
        for (rate, t), ref in zip(TK, vals):
            d = data[rate].get(src)
            if d is None:
                RP.append(dict(src=src, ref_src=rs, rate=rate, t=t, ref=ref, all_txt="not loaded", rule_txt="-",
                               check="MISSING"))
                continue
            ga, ta = status(d["pts"], t)
            gr, tr = status(use(d["pts"]), t)
            ok = (ref is None and ga is None and ta.startswith("fails")) or \
                 (ref is not None and ga is not None and round(ga, 2) == round(ref, 2))
            RP.append(dict(src=src, ref_src=rs, rate=rate, t=t, ref=ref, all_txt=ta, rule_txt=tr,
                           check="ok" if ok else "DIFFERS"))
    # sources
    seen = {s for r in RATES for d in data[r].values() for s in [d["src"]]}
    in_parts = {r["src"] for p in V for r in P4.load(p)}
    unlab = sorted(s for s in in_parts if s not in LABELS)
    never = sorted(s for s in E4C.SOURCES if s not in in_parts)
    no_full = sorted(s for s in E4C.SOURCES if s not in seen)
    tw = sorted(os.path.basename(p) for p in glob.glob(os.path.join(C.EP.BLIND_DIR, "blind_ber_t-tw*.json")))
    tw_txt = ("landed: " + ", ".join(tw)) if tw else "none landed yet (t-tw10a/b, t-tw15a/b, t-tw25, t-tw2)"
    missing = {r: sorted(s for s in E4C.SOURCES if s not in {d["src"] for d in data[r].values()}) for r in RATES}
    extra = [f"Sources in some part file but NOT in plot_e4 STY / STY5 / STYA (never drawn by plot_e4): {unlab}",
             f"E4C.SOURCES never found in any part file: {never or 'none'}",
             f"E4C.SOURCES without full (non-smoke) data at any rate: {no_full}",
             f"Merge differences vs plot_e4.e4(rate, e5=True, ars=True) (replicate rows '<src> [<part>]' pooled "
             f"with '<src>', as plot_e4.pool does): "
             + ("; ".join(f"{r}: {x}" for r in RATES for x in diffs[r]) or "none"),
             "ARS regression (ars RCS2-13 rows = e4 RCS2-13 rows, errors and packets): "
             + ", ".join(f"{r} {v['same']}/{v['points']}" if v else f"{r} n/a" for r, v in regr.items()),
             f"Duplicated packets (same rate, src, SNR, seed, pn in two included parts): {dups or 'none'}",
             f"Blind tw parts: {tw_txt}"]
    SM = smoke()
    # ---------------------------------------------------------------- markdown
    L = ["# Blind vs every compared receiver: full data (regenerable)", "",
         "Generated by `BLIND_IMPLEMENTATION/testing/comparison_data.py` from existing results only (est4 "
         "`est4/results/bler_{e4,e5,ars}-*.json` via `plot_e4.e4`, blind via `plot_e4.blind`); rerun it when the est5 "
         "parts land. SNR axis: SNR (Es/N0) [dB] = burst energy per data symbol (pilot energy charged) unless "
         "marked raw. No point below -5 dB is used. 0-error points never enter an interpolation (plot_e4.gap_db). "
         "Counts: errors / packets; BLER with Clopper-Pearson 95 %; 0 errors = '< 3/n (95 %)'.", "",
         "R = 1/10 is the reference rate; main rates 0.15, 2/5, 1/2. 1/10 and 0.15 are separate sections everywhere.", "",
         "Status of the est5 full runs: " + ", ".join(f"{p} {V[p]['status']}" for p in
                                                     [*P4.MAIN5.values(), *P4.PP5.values()]), ""]
    L += md_validation(V, extra)
    L += md_repro(RP)
    L += md_cards(data)
    L += ["## B. Full data per rate", ""]
    for rate in RATES:
        L += md_data(rate, data[rate], notes[rate])
        L.append(f"Not run yet at R = {rate} (no validated full part): {', '.join(missing[rate]) or 'none'}.")
        L.append("")
        L += md_blind_tail(rate, data[rate])
    L += md_smoke(SM)
    L += md_summary(S)
    sd = defaultdict(set)
    for r in RATES:
        for d in data[r].values():
            if d["kind"] != "blind":
                sd[d["part"]] |= {x.get("seed") for x in P4.load(d["part"])}
    L += caveats(tw_txt, ", ".join(f"{p} {sorted(v)}" for p, v in sorted(sd.items())))
    L += md_se()
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    # ---------------------------------------------------------------- json
    J_ = dict(generated_by="BLIND_IMPLEMENTATION/testing/comparison_data.py", x_min_db=XMIN,
              validation=V, checks=extra, reproduction=RP,
              cards={k: dict(v, nk=nk_of(k), energy_db=10 * np.log10((N_SYM + nk_of(k)) / N_SYM),
                             airtime_pct=100 * nk_of(k) / N_SYM, real=real_block(k) or NO_REAL.get(k))
                     for k, v in CARDS.items()},
              spectral_efficiency=dict(best=[dict(point=a, best=b, verdict=c) for a, b, c in SE_BEST],
                                       bound=[dict(rate=r, bler=t, qpsk_capacity=c, max_se=m,
                                                   ours=(SE_KCRC[r] - 16) / N_SYM) for r, t, c, m in SE_POINTS]),
              data={r: {n: dict(src=d["src"], part=d["part"], kind=d["kind"],
                                points=[dict(snr_plot=s, **{k: v for k, v in p.items()},
                                             bler=p["err"] / p["n"], ci=list(PF.cp(p["err"], p["n"])))
                                        for s, p in sorted(d["pts"].items()) if not p["below"]])
                        for n, d in data[r].items()} for r in RATES},
              not_run_yet=missing, smoke=SM,
              summary={f"{r} @{t:.0e}": rows for (r, t), rows in S.items()})
    json.dump(jsonable(J_), open(OUT_JS, "w", encoding="utf-8", newline="\n"), indent=1)
    print(OUT_MD)
    print(OUT_JS)
    for x in extra:
        print("CHECK:", x)
    for r in RP:
        if r["check"] != "ok":
            print("REPRO:", r)
    for p, v in V.items():
        if v["issues"]:
            print("VALID:", p, v["status"], v["issues"][:4])


if __name__ == "__main__":
    main()
