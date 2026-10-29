"""
BLER of blind receivers (no pilots) on the 1024-symbol polar-coded packet (CRC-16, CA-SCL L = 8), full Tx/Rx chain.
Every receiver sees the same frames; the CFO is U[-0.2, 0.2] and the carrier phase uniform (both unknown).

Candidates: the 64 largest peaks of |FFT_4096(-r^4)| (or of the NN posterior, blind_nn.py), each refined by Newton,
its 1/4 ambiguity resolved by the spectral (band-edge) estimate; at a candidate CFO f the phase is phase4(r, f) + q pi/2,
q = 0..3. A hypothesis = (peak, grid offset k * STEP, q). The search runs in stages; in each stage every hypothesis of
the frames still undecoded is scored by a decoder metric (phase hypotheses q = 0, 1: a pi error is resolved by the
CRC, blind_cfo.PiCode), and CA-SCL + CRC-16 decodes the best T of them in order
(stop at the first CRC pass):

    S0  peak 1, offset 0                  x 4 phases   T = 1
    S1  peak 1, offsets +-1, +-2          x 4 phases   T = 2     (grid receivers)
    S2  peaks 2..8, offsets -1, 0, 1      x 4 phases   T = 3
    S3  peaks 9..64, offset 0             x 4 phases   T = 3

Receivers
    Genie                                  true CFO and phase, one decode (the bound)
    4th power + CRC (phase mod pi)         S0 only, T = 2 (both phase hypotheses, in metric order)
    4th power + SC search + CRC            S0..S3, ranking by the SC path metric (list 1)
    4th power + syndrome search + CRC      the same stages, ranking by the soft low-weight syndrome (w <= 16)
    NN peaks + SC search + CRC             S0..S3 on the NN-ranked peaks
    4th power + SC search, then spectral grid + CRC   S0..S2, then the grid stage (the combined receiver)
    Spectral grid + SC search + CRC        S0, then a grid of hypotheses every 4 steps over +-3 sigma of the spectral
                                           estimate, SC-scored; the best 3 refined (+-1, +-2 steps); CA-SCL on the best 3
    4th power + turbo (DD) + CRC           S0, then up to 3 decision-directed re-estimations + re-decodes of its best
                                           hypothesis; S2 (offset 0, 1 DD iteration each), S3 (no DD)
After a CRC pass every receiver re-estimates the CFO decision-directed over all 1024 symbols (rmse_dd).

    python blind_ber.py --rate 1/4 --snrs 2 3 --part a       # -> blind/results/blind_ber_<part>.json
    python blind_ber.py --points 1/4:4:16 1/2:6:16 --part b  # rate:snr:chunks (independent runs of a point)
    python blind_ber.py --merge                              # -> blind/results/blind_ber.json
"""
import argparse
import glob
import json
import multiprocessing as mp
import os
import time
import zlib

import numpy as np

import blind_cfo as bc
from polar import PolarCode

GENIE = "Genie (known CFO and phase)"
STAGES = [([0], [0], 1), ([0], [-2, -1, 1, 2], 2), (list(range(1, 8)), [-1, 0, 1], 3), (list(range(8, 64)), [0], 3)]
# spectral-grid receiver: grid f_spec + j * GRID_STEP, |j| <= 3 sigma_spec(SNR) / GRID_STEP (inside the SC metric's
# basin, +-4..8 steps); the 3 best grid points are refined by +-1, +-2 steps; CA-SCL on the best 3
GRID_STEP = 4 * bc.STEP
SPEC_SIGMA = ((-5, 4.1e-2), (-2, 2.05e-2), (0, 1.4e-2), (2, 1.0e-2), (5, 7.3e-3), (10, 4.4e-3))   # measured RMSE
GRID_CAP = 0.06
RX = {
    "4th power + CRC (phase mod pi)": dict(metric="SC", peaks="fft", stages=[([0], [0], 2)]),
    "4th power + SC search + CRC": dict(metric="SC", peaks="fft"),
    "4th power + syndrome search + CRC": dict(metric="soft", peaks="fft"),
    "NN peaks + SC search + CRC": dict(metric="SC", peaks="nn"),
    "Spectral grid + SC search + CRC": dict(metric="SC", peaks="fft", stages=[([0], [0], 1), "grid"]),
    "4th power + SC search, then spectral grid + CRC": dict(metric="SC", peaks="fft", stages=STAGES[:3] + ["grid"]),
    # the +-3 sigma grid misses the heavy tail of the spectral error (4e-3 outside at 0 dB: the BLER floor at R = 1/10);
    # +-6 sigma, capped at the full CFO range
    "Spectral grid 6 sigma + SC search + CRC": dict(metric="SC", peaks="fft", stages=[([0], [0], 1), "grid"],
                                                    grid_k=6, grid_cap=0.2),
    "4th power + SC search, then spectral grid 6 sigma + CRC": dict(metric="SC", peaks="fft",
                                                                    stages=STAGES[:3] + ["grid"], grid_k=6, grid_cap=0.2),
    # round 2 (blind_fast.py): best-first search over the whole CFO range in the order of a coarse posterior, Fast-SSC
    # metric, a cell is refined + decoded when its metric stands out (robust z > z0); stop at the first CRC pass
    "Best-first search (spectral + 4th) + CRC": dict(kind="sps", sps=dict()),
    "Best-first search (spectral only) + CRC": dict(kind="sps", sps=dict(w4=0.0)),
    "Best-first search (spectral + cyclic + 4th) + CRC": dict(kind="sps", sps=dict(wc=1.0)),
    "Best-first search, z0 = 3 + CRC": dict(kind="sps", sps=dict(z0=3.0)),
    "Best-first search, z0 = 5 + CRC": dict(kind="sps", sps=dict(z0=5.0)),
    "Best-first search, exact box-plus + CRC": dict(kind="sps", sps=dict(exact=True)),
    # v2 (after E1 / E2): 4 phase hypotheses below -1 dB, grid step from the measured basin, cyclic posterior
    "Best-first search v2 + CRC": dict(kind="sps2", sps=dict()),
    "Best-first search v2, 2 phases + CRC": dict(kind="sps2", sps=dict(nph=2)),
    "Best-first search v2, no cyclic + CRC": dict(kind="sps2", sps=dict(wc=0.0)),
    "Best-first search v2, step 4 + CRC": dict(kind="sps2", sps=dict(step=4)),
    "Best-first search v2, weighted metric + CRC": dict(kind="sps2", sps=dict(weighted=True)),
    "Best-first search v2, exact box-plus + CRC": dict(kind="sps2", sps=dict(exact=True)),
    "Best-first search v2, weighted + exact box-plus + CRC": dict(kind="sps2", sps=dict(weighted=True, exact=True)),
    # v3: v2 + re-encoding check of every CRC pass (undetected errors) + pre-MF correction by the spectral estimate
    "Best-first search v3 + CRC": dict(kind="sps2", sps=dict(verify=True, premf=True)),
    "Best-first search v2 + re-encoding check + CRC": dict(kind="sps2", sps=dict(verify=True)),
    "Best-first search v2 + pre-MF correction + CRC": dict(kind="sps2", sps=dict(premf=True)),
    "Genie (known CFO, pre-MF correction)": dict(kind="genie_premf"),
    # v3, optimised implementation (same algorithm), and with the hard path metric
    "Best-first search v3 fast + CRC": dict(kind="sps3", sps=dict()),
    "Best-first search v3 fast, hard metric + CRC": dict(kind="sps3", sps=dict(hard=True)),
    # MAC-saving variants of v3 (MACs counted in the receiver: blind_vp MAC model)
    "v3 lite + CRC": dict(kind="sps3", sps=dict(lite=True)),
    "v3 lite, adaptive phases + CRC": dict(kind="sps3", sps=dict(lite=True, adaptive=True)),
    "v3 lite, early abort + CRC": dict(kind="sps3", sps=dict(lite=True, abort=True)),
    "v3 lite, adaptive + abort + CRC": dict(kind="sps3", sps=dict(lite=True, adaptive=True, abort=True)),
    "v3 NN posterior + CRC": dict(kind="sps3", sps=dict(posterior="nn")),
    "v3 NN posterior, adaptive + abort + CRC": dict(kind="sps3", sps=dict(posterior="nn", adaptive=True, abort=True)),
    # v3 eco: v3's decisions for fewer MACs (blind_fast.sps3_receive eco)
    "v3 eco + CRC": dict(kind="sps3", sps=dict(eco=True)),
    "v3 eco, 8-SPS statistics + CRC": dict(kind="sps3", sps=dict(eco=True, eco_feat="8sps")),
    "v3 eco, no adaptive / abort + CRC": dict(kind="sps3", sps=dict(eco=True, eco_gate=np.inf)),
    "v3 eco, grid step 6 + CRC": dict(kind="sps3", sps=dict(eco=True, step=6)),       # R = 1/10 only (basin E6)
    "v3 eco, re-decode + CRC": dict(kind="sps3", sps=dict(eco=True, redecode=True)),
    "v3 eco, re-decode in search + CRC": dict(kind="sps3", sps=dict(eco=True, redecode=True, rd_where="search")),
    "v3 eco, FFT phase + CRC": dict(kind="sps3", sps=dict(eco=True, phase_fft=True)),
    "v3 eco, fast path from -2 dB + CRC": dict(kind="sps3", sps=dict(eco=True, s0_snr=-2.0)),   # R = 1/10
    "v3 eco2 + CRC": dict(kind="sps3", sps=dict(eco=True, redecode=True, phase_fft=True)),
    # eco3: cheaper fast path (lag-4 autocorrelation coarse + pre-MF redone at the 4th-power estimate, 2 Newton steps,
    # left-half metric for the pi/2 branch); eco3+ = + code-aided retry + 8 posterior final cells
    **{f"{pre}v3 eco3{plus}{suf} + CRC": dict(kind="sps3", sps=dict(
        eco=True, coarse="acf", premf2=True, newton=2, pi2="left", **(dict(pilots="N3x8") if pre else {}),
        **(dict(ca_retry=True, final_post=8) if plus else {}), **extra))
       for pre in ("", "Pilots N3x8 + ") for plus in ("", "+")
       for suf, extra in (("", {}), (", fast path from 0 dB", dict(s0_snr=0.0)),
                          (", grid 6 from -3 dB", dict(step_from=(6, -3.0))),
                          (", fast path from 0 dB, 16 peaks", dict(s0_snr=0.0, fast_peaks=16)),
                          (", fast path from 0 dB, 4 peaks", dict(s0_snr=0.0, fast_peaks=4)),
                          *((f", fast path from 0 dB, 16 peaks >= {q}", dict(s0_snr=0.0, fast_peaks=16, fast_ratio=q))
                            for q in (0.5, 0.7, 0.85)),
                          *((f", fast path from 0 dB, 4 peaks >= {q}", dict(s0_snr=0.0, fast_peaks=4, fast_ratio=q))
                            for q in (0.7, 0.85)))},
    "v3 fast, both pi/2 branches + CRC": dict(kind="sps3", sps=dict(branch2=True)),
    "v3 eco, both pi/2 branches + CRC": dict(kind="sps3", sps=dict(eco=True, branch2=True)),
    "v3 eco, final 8 + CRC": dict(kind="sps3", sps=dict(eco=True, final=8)),
    "v3 eco, code-aided retry + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True)),
    "v3 eco, code-aided retry, final 8 + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True, final=8)),
    "v3 eco, code-aided retry, posterior final 8 + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True,
                                                                                     final_post=8)),
    # eco+ with the extra decodes' passes verified (re-decode at the decision-directed CFO / phase, kept if it fails)
    "v3 eco+ verified + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True, final_post=8, redecode=True,
                                                       rd_where="extra", rd_keep=True)),
    "v3 eco+ verified, all search passes + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True, final_post=8,
                                                                          redecode=True, rd_where="search", rd_keep=True)),
    # pilots + v3 eco+ (eco + code-aided retry + 8 posterior final cells)
    **{f"Pilots {pat} + v3 eco+ + CRC": dict(kind="sps3", sps=dict(pilots=pat, eco=True, ca_retry=True, final_post=8))
       for pat in ("N3x8", "N4x4", "C16")},
    # blind eco3+ with the extras (code-aided retry, posterior final cells) only on the waterfall: above it their extra
    # decodes add more CRC-16 false passes than they rescue (ep-r10, ep-r25)
    "v3 eco3+ gated, peak-picked fast path + CRC": dict(kind="sps3", sps=dict(
        eco=True, ca_retry=True, final_post=8, plus_below={"1/10": -4.5, "2/5": 1.25, "1/2": 2.25}, coarse="acf",
        premf2=True, newton=2, pi2="left", s0_snr={"2/5": 0.0, "1/2": 0.0}, fast_peaks=4, fast_ratio=0.85)),
    # eco4: + the pilots pick the fast path's pi/2 branch; above the waterfall (hi_snr) the 1024-point 4th-power FFT with
    # off-bin interpolation and no second pre-MF correction (smoke-6: -6..-8 % each there, worse on the waterfall)
    **{f"{nm} + CRC": dict(kind="sps3", sps=dict(
        eco=True, ca_retry=True, final_post=8, coarse="acf", premf2=True, newton=2, pi2="left", s0_snr={"2/5": 0.0, "1/2": 0.0},
        **extra)) for nm, extra in (
        ("Pilots N3x8 + v3 eco4", dict(pilots="N3x8", pilot_pi2=True, fast_peaks=16, fast_ratio=0.7,
                                       hi_snr={"2/5": 1.5, "1/2": 2.5})),
        ("Pilots N3x8 + v3 eco4, pilot pi/2 only", dict(pilots="N3x8", pilot_pi2=True, fast_peaks=16, fast_ratio=0.7)),
        ("v3 eco4", dict(fast_peaks=4, fast_ratio=0.85, plus_below={"1/10": -4.5, "2/5": 1.25, "1/2": 2.25},
                         hi_snr={"2/5": 1.5, "1/2": 2.5})))},
    "Pilots N3x8 + v3 eco+, pilot direct 1 + CRC": dict(kind="sps3", sps=dict(pilots="N3x8", eco=True, ca_retry=True,
                                                                              final_post=8, pilot_direct=1)),
    "Pilots N3x8 + v3 eco+, pilot direct 2 + CRC": dict(kind="sps3", sps=dict(pilots="N3x8", eco=True, ca_retry=True,
                                                                              final_post=8, pilot_direct=2)),
    # eco5 = the best of the cycle: eco3 fast path from 0 dB with the peak picked among the near-highest 4th-power
    # peaks, no code-aided retry in the fast path, the cheapest fast path only well above the waterfall (h9: lossy at
    # 1.5-2 dB at R = 2/5); blind: extras gated to the waterfall; pilots: their pi/2 branch in the fast path
    **{f"{nm} + CRC": dict(kind="sps3", sps=dict(
        eco=True, ca_retry=True, final_post=8, coarse="acf", premf2=True, newton=2, pi2="left", ca_fast=False,
        s0_snr={"2/5": 0.0, "1/2": 0.0}, hi_snr={"2/5": 2.5, "1/2": 3.0}, **extra)) for nm, extra in (
        ("Pilots N3x8 + v3 eco5", dict(pilots="N3x8", pilot_pi2=True, fast_peaks=16, fast_ratio=0.7)),
        ("Pilots N3x8 + v3 eco5, pilot phase", dict(pilots="N3x8", pilot_pi2=True, fast_peaks=16, fast_ratio=0.7,
                                                   pilot_phase=-4.5)),
        ("v3 eco5", dict(fast_peaks=4, fast_ratio=0.85, plus_below={"1/10": -4.5, "2/5": 1.25, "1/2": 2.25})))},
    # the pilots choose each search cell's phase branch (1 metric per cell at nph 2, 2 of the 4 at nph 4)
    "Pilots N3x8 + v3 eco+, pilot phase + CRC": dict(kind="sps3", sps=dict(pilots="N3x8", eco=True, ca_retry=True,
                                                                           final_post=8, pilot_phase=True)),
    "Pilots N3x8 + v3 eco3+, pilot-picked fast path + pilot phase + CRC": dict(kind="sps3", sps=dict(
        pilots="N3x8", eco=True, ca_retry=True, final_post=8, pilot_phase=True, coarse="acf", premf2=True, newton=2,
        pi2="left", s0_snr=0.0, fast_peaks=16, fast_ratio=0.7)),
    "v3 eco, code-aided retry, posterior final 16 + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True,
                                                                                      final_post=16)),
    "v3 eco, code-aided retry, final 8, posterior final 8 + CRC": dict(kind="sps3", sps=dict(eco=True, ca_retry=True,
                                                                                            final=8, final_post=8)),
    # pilots + v3: the pilot ruler in the posterior, the pilots as an extra check of every CRC pass
    **{f"Pilots {pat} + v3 + CRC": dict(kind="sps3", sps=dict(pilots=pat)) for pat in ("N3x8", "N4x6", "N4x4", "C16", "C24")},
    "Pilots N3x8 + v3, order only + CRC": dict(kind="sps3", sps=dict(pilots="N3x8", pilot_check=False)),
    "Pilots N3x8 + v3, check only + CRC": dict(kind="sps3", sps=dict(pilots="N3x8", pilot_order=False)),
    "Pilots N3x8 + v3 lite, adaptive + abort + CRC": dict(kind="sps3", sps=dict(pilots="N3x8", lite=True, adaptive=True,
                                                                               abort=True)),
    # few known symbols ("Vernier comb") + code-aided search (blind_vp.py); pilots in the 1024 symbols
    **{f"Pilots {pat} + code search": dict(kind="vp", vp=dict(pattern=pat))
       for pat in ("C16", "C24", "V2x8 D32", "V2x8 D64", "N3x5", "N4x4", "N3x8", "N4x6", "R3x8")},
    "Pilots N4x4 + blind terms + code search": dict(kind="vp", vp=dict(pattern="N4x4", blind_terms=True)),
    "Pilots C16 + blind terms + code search": dict(kind="vp", vp=dict(pattern="C16", blind_terms=True)),
    "Pilots N4x4 + code search, 4th-power phase": dict(kind="vp", vp=dict(pattern="N4x4", phase="pilot+4th")),
    "Pilots N3x8 + code search, 4th-power phase": dict(kind="vp", vp=dict(pattern="N3x8", phase="pilot+4th")),
    "4th power + turbo (DD) + CRC": dict(metric="SC", peaks="fft", turbo=True,
                                         stages=[([0], [0], 1, 3), (list(range(1, 8)), [0], 3, 1),
                                                 (list(range(8, 64)), [0], 3, 0)]),
}
# eco6 = eco5 + left-metric screening / adaptive phases at R = 1/10 from -4.5 dB with z_screen 1.5 below -2.5 dB
# (smoke-11: -49..-51 % blind at -4 / -3 dB, lossy at -5 dB) + the cells' phase from the 4th-power FFT (ec-r10c)
for _nm in ("v3 eco5", "Pilots N3x8 + v3 eco5"):
    RX[_nm.replace("eco5", "eco6") + " + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"], "z_screen_low": 1.5,
                                                                       "phase_fft": True, "eco_gate": {"1/10": -4.5}})
# eco7 = eco6 with the screening only from -3.5 dB (j6-r10a/b: lossy at -4 dB, x5-7 BLER) + grid step 6 at R = 1/10 from
# -3 dB (e3-r10: -21 % blind at -3 dB, BLER no worse)
for _nm in ("v3 eco6", "Pilots N3x8 + v3 eco6"):
    RX[_nm.replace("eco6", "eco7") + " + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"],
                                                                       "eco_gate": {"1/10": -3.5},
                                                                       "step_from": {"1/10": (6, -3.0)}})
NPEAK = 64
CHUNK_H = 4096                     # hypotheses per metric call (memory)
# 24 pilots: eco7 without the coarser grid (k7-r10b: grid 6 at -3 dB triples the BLER for the pilot receiver, whose
# search is already short, and saves nothing)
RX["Pilots N3x8 + v3 eco7, default grid + CRC"] = dict(kind="sps3", sps={**RX["Pilots N3x8 + v3 eco7 + CRC"]["sps"],
                                                                        "step_from": None})
# eco8 candidates (on eco7): left-metric screening from the first search round (screen_rnd 0); at R = 1/10 the
# screening also at -4 dB with z 1.0; 24 pilots: the re-encoded packet shared by the rho and pilot checks, and the
# fast path at R = 1/10 from -1 dB (pilot-picked peaks)
for _nm in ("v3 eco7", "Pilots N3x8 + v3 eco7"):
    _b = RX[_nm + " + CRC"]["sps"]
    _sh = {"share_reencode": True} if "Pilots" in _nm else {}
    RX[_nm + ", screen from round 1 + CRC"] = dict(kind="sps3", sps={**_b, **_sh, "screen_rnd": 0})
    RX[_nm + ", screen -4 dB z 1.0 + CRC"] = dict(kind="sps3", sps={**_b, **_sh, "eco_gate": {"1/10": -4.5},
                                                                     "z_screen_vlow": 1.0})
# the fast-path peak chosen by the small peak-grader NN (blind_peak_nn), optionally skipping the fast-path decode
# when the NN says no peak is right (P(none) > 0.8)
for _nm in ("v3 eco7", "Pilots N3x8 + v3 eco7"):
    RX[_nm + ", NN peak + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"], "fast_nn": True})
    RX[_nm + ", NN peak, skip 0.8 + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"], "fast_nn": True,
                                                                    "fast_skip": 0.8})
# the fast-path tone refined by a parabolic fit through the 3 largest points of the zero-padded FFT / off-bin grid
# (spacing 1/4 bin) instead of 2 Newton steps (-61k MACs a fast-path packet)
RX["v3 eco7, parabolic + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7 + CRC"]["sps"], "parab": True})
RX["Pilots N3x8 + v3 eco7, NN peak, parabolic + CRC"] = dict(kind="sps3", sps={
    **RX["Pilots N3x8 + v3 eco7 + CRC"]["sps"], "fast_nn": True, "parab": True})
# the top 512 cells of the search order re-scored by the per-cell ranking NN (blind_rank_nn, ~83k MACs)
RX["v3 eco7, rank NN + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7 + CRC"]["sps"], "rank_nn": 512})
RX["Pilots N3x8 + v3 eco7, rank NN + CRC"] = dict(kind="sps3", sps={**RX["Pilots N3x8 + v3 eco7 + CRC"]["sps"],
                                                                    "rank_nn": 512})
# the last stage, reached only by the packets still undecoded after the whole search (fail_diag: the true cell is
# usually there with a low z, or decoded slightly off): more best-metric cells (final), more top-posterior cells
# (final_post), and the best cells again on a finer CFO / phase grid with more decodes (fine_last)
for _nm, _b, _post in (("v3 eco7", "v3 eco7, parabolic", 256), ("Pilots N3x8 + v3 eco7", "Pilots N3x8 + v3 eco7, NN peak, parabolic", 64)):
    _s = {**RX[_b + " + CRC"]["sps"], "step_from": None}     # grid 6 from -3 dB costs BLER (k7-r10a, m9-r10)
    RX[_nm + ", final 32 + CRC"] = dict(kind="sps3", sps={**_s, "final": 32})
    RX[_nm + ", rescue + CRC"] = dict(kind="sps3", sps={**_s, "final": 32, "final_post": _post, "fine_last": 4,
                                                         "plus_below": {"2/5": 1.25, "1/2": 2.25} if "plus_below" in _s
                                                         else None})
RX["v3 eco7, rank NN, default grid + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7, rank NN + CRC"]["sps"],
                                                                    "step_from": None})
# the pilot check at 3 sigma (5: a "staircase" codeword of a wrong CFO, ~half coherent at the pilots, passes)
RX["Pilots N3x8 + v3 eco7, rescue, pc 3 + CRC"] = dict(kind="sps3", sps={**RX["Pilots N3x8 + v3 eco7, rescue + CRC"]["sps"],
                                                                         "pc_sigmas": 3.0})
RX["Pilots N3x8 + v3 eco7, rescue+, pc 3 + CRC"] = dict(kind="sps3", sps={
    **RX["Pilots N3x8 + v3 eco7, rescue + CRC"]["sps"], "pc_sigmas": 3.0, "final": 64, "final_post": 128,
    "fine_last": 8})
# the 24-pilot fast path at R = 1/10 (the peak NN picks among the top 16 4th-power peaks), now with the 3 sigma pilot
# check that rejects the staircase false passes, + rescue
for _s0 in (-1.0, 0.0, -2.0):
    RX[f"Pilots N3x8 + v3 eco7, rescue, pc 3, fast R=1/10 from {_s0:g} dB + CRC"] = dict(kind="sps3", sps={
        **RX["Pilots N3x8 + v3 eco7, rescue, pc 3 + CRC"]["sps"], "s0_snr": {"1/10": _s0, "2/5": 0.0, "1/2": 0.0}})
# blind R = 1/10 complexity on top of the rescue: adaptive phases (2 of 4 first) alone, or with the left-metric
# screening, down to -5.5 dB (lossy without the rescue at -4 dB, eco6)
RX["v3 eco7, rescue, adaptive from -5.5 dB + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7, rescue + CRC"]["sps"],
                                                                           "adapt_gate": {"1/10": -5.5}})
RX["v3 eco7, rescue, screen from -5.5 dB + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7, rescue + CRC"]["sps"],
                                                                         "eco_gate": {"1/10": -5.5}, "screen_from": -5.5})
# the normalised re-encoding check (fp_check.py: midway between the right passes' 0.1 % quantile and the false
# passes' maximum of rho / sqrt(s / (1 + s)), per rate): removes the staircase false passes at no MAC cost
RHO_N = {"1/10": ((-5.0, 0.775), (-4.0, 0.72), (-3.0, 0.66), (-2.0, 0.625), (-1.0, 0.59), (0.0, 0.553)),
         "2/5": ((0.5, 0.928), (1.0, 0.91), (1.5, 0.894), (2.0, 0.883)),
         "1/2": ((2.0, 0.934), (3.0, 0.903))}
for _nm in ("v3 eco7, rescue", "Pilots N3x8 + v3 eco7, rescue"):
    RX[_nm + ", rho_n + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"], "rho_n": RHO_N})
# the 24-pilot fast path at R = 1/10 with the rho_n check instead of the 3 sigma pilot check (which loses right decodes)
RX["Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB + CRC"] = dict(kind="sps3", sps={
    **RX["Pilots N3x8 + v3 eco7, rescue, rho_n + CRC"]["sps"], "s0_snr": {"1/10": -2.0, "2/5": 0.0, "1/2": 0.0}})
# blind rescue with a smaller last stage (the false passes it produced are now rejected by rho_n)
RX["v3 eco7, rescue lite, rho_n + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7, rescue, rho_n + CRC"]["sps"],
                                                                  "final_post": 64})
for _s0 in (-3.0, -4.0):
    RX[f"Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from {_s0:g} dB + CRC"] = dict(kind="sps3", sps={
        **RX["Pilots N3x8 + v3 eco7, rescue, rho_n + CRC"]["sps"], "s0_snr": {"1/10": _s0, "2/5": 0.0, "1/2": 0.0}})
RX["v3 eco7, rescue mid, rho_n + CRC"] = dict(kind="sps3", sps={**RX["v3 eco7, rescue, rho_n + CRC"]["sps"],
                                                                 "final_post": 128})
RX["Pilots N3x8 + v3 eco7, fast path R=1/10 from -1 dB + CRC"] = dict(kind="sps3", sps={
    **RX["Pilots N3x8 + v3 eco7 + CRC"]["sps"], "share_reencode": True,
    "s0_snr": {"1/10": -1.0, "2/5": 0.0, "1/2": 0.0}})
# in-cell CFO grid for the z-test (the true cell's off-centre CFO lowers its z: the main R = 1/10 failure): every
# cell scored at +-1/4 cell instead of its centre ("sub-grid 2"), or only the near misses of a round (1.5 < z <= z0,
# best 4) scored again at +-1/3 cell ("in-cell retry"); at every SNR (run on the full sweeps to see where it helps)
_SUBW = None
for _nm in ("v3 eco7, rescue, rho_n", "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB"):
    RX[_nm + ", sub-grid 2 + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"], "sub_all": (-0.25, 0.25),
                                                             "sub_below": _SUBW})
    RX[_nm + ", in-cell retry + CRC"] = dict(kind="sps3", sps={**RX[_nm + " + CRC"]["sps"],
                                                                "sub_z": (1.5, 4, (-1 / 3, 1 / 3)), "sub_below": _SUBW})


# small-CFO study (BLIND_STUDY=small_cfo, |f| <= 0.03, small_rx.py): no spectral / cyclic / autocorrelation statistics;
# 4th-power fast path, then the whole small grid scored with the code metric, without or with checkpoints (pruning of
# the cells along the decode, early stop of the CFO search)
# checkpoint rules from the replay of the partial path metrics (pm_traj_report.py, true cell lost <= 0.1 %): drop
# the cells with z <= tau among the alive ones at the checkpoints (the best 16 always survive), early stop at z > 6
CK_S = {"1/10": (0.5,), "2/5": (0.25, 0.375, 0.5, 0.75), "1/2": (0.125, 0.25, 0.5)}
TAU_S = {"1/10": 1.0, "2/5": -1.0, "1/2": -1.0}
for _nm, _pl in (("S blind", None), ("S pilots N3x8", "N3x8")):
    _b = {"rho_n": RHO_N, "pilots": _pl}
    RX[_nm + ", no checkpoints + CRC"] = dict(kind="small", sps=_b)
    RX[_nm + ", no checkpoints, MF per candidate + CRC"] = dict(kind="small", sps={**_b, "premf_dec": True})
    _c = {**_b, "premf_dec": True, "ca_retry": True}
    RX[_nm + ", no checkpoints, MF per candidate, CA retry + CRC"] = dict(kind="small", sps=_c)
    _d = {**_c, "ck": CK_S, "tau": TAU_S, "kmin": 16, "win": 6.0}
    RX[_nm + ", checkpoints + CRC"] = dict(kind="small", sps=_d)
    # + phase sub-offsets (+-pi/12) for the candidates at every SNR (scl_traj: at R = 2/5, 0.5 dB half the search
    # packets without a right hypothesis had a hypothesis within 3e-5 of the CFO but only 2 phases, no sub-offsets)
    RX[_nm + ", checkpoints, phase sub-offsets + CRC"] = dict(kind="small", sps={**_d, "sub3": True})
    # + coarse start (pm_traj_report.replay2 on pmt-b, true cell lost <= 0.1 %): up to the first checkpoint only every
    # other cell; the neighbours of the survivors join there. Work vs no checkpoints 0.515 -> 0.417 (R = 1/10, with a
    # checkpoint at 3/4 and tau -0.5), 0.290 -> 0.246 (2/5), 0.234 -> 0.177 (1/2, first checkpoint at 1/4)
    RX[_nm + ", checkpoints, coarse start + CRC"] = dict(kind="small", sps={
        **_d, "coarse": True, "ck": {"1/10": (0.5, 0.75), "2/5": (0.25, 0.375, 0.5, 0.75), "1/2": (0.25, 0.5)},
        "tau": {"1/10": -0.5, "2/5": -1.0, "1/2": -1.0}})
    # + a shortlist of the cells by the prior (4th power + pre-MF autocorrelation [+ pilots]) before any metric;
    # blind R = 1/10 keeps every cell (that prior is flat at -5 dB)
    RX[_nm + ", checkpoints, shortlist + CRC"] = dict(kind="small", sps={
        **_d, "prior": ("s4", "acf") + (("pilots",) if _pl else ()),
        "pre_keep": {"2/5": 128, "1/2": 128} if _pl else {"2/5": 192, "1/2": 192}})   # R = 1/10: lossy (smoke-s2)
# 24 pilots: + the pilots' log-likelihood inside the cell score (path metric - w x log-likelihood, both in nats), which
# also makes early checkpoints useful (pm_traj c replay, true cell lost <= 0.1 %; work vs no checkpoints:
# R = 1/10 -5 / -6 dB 0.42 / 0.51, R = 2/5 0.10, R = 1/2 0.10)
RX["S pilots N3x8, checkpoints, pilot score + CRC"] = dict(kind="small", sps={
    **RX["S pilots N3x8, checkpoints + CRC"]["sps"], "pilot_score": {"1/10": 1.0, "2/5": 2.0, "1/2": 1.0},
    "ck": {"1/10": (1 / 16, 1 / 8, 0.5, 0.75), "2/5": (0.125, 0.25, 0.375, 0.5, 0.75), "1/2": (0.125, 0.25, 0.5, 0.75)},
    "tau": {"1/10": -1.0, "2/5": 1.0, "1/2": 1.0}, "coarse": {"1/10": False, "2/5": True, "1/2": True}})
# + the rescue of the +-0.2 receivers (final_post / fine_last): on the small range the old receivers were 5-40x
# better in BLER (sx-ref), mostly from decoding many more CFO / phase hypotheses of the failing packets
for _nm, _post in (("S blind", 256), ("S pilots N3x8", 64)):
    for _v in ("no checkpoints, MF per candidate, CA retry", "checkpoints", "checkpoints, coarse start") + (
            ("checkpoints, pilot score",) if "pilots" in _nm else ()):
        RX[f"{_nm}, {_v}, rescue + CRC"] = dict(kind="small", sps={**RX[f"{_nm}, {_v} + CRC"]["sps"],
                                                                   "final_post": _post, "fine_last": 4})
# + the SNR-aware cell-prior NN (small_prior_nn.py) instead of a spectral prior: best-first, first the NN's shortlist
# (cumulative probability 1 - nn_keep, >= 48 cells), the whole grid only if nothing passes there; "NN score" also adds
# its log-probability to the cell score (as the pilot score)
for _nm, _mode, _v in (("S blind", "blind", "no checkpoints, MF per candidate, CA retry"),
                       ("S blind", "blind", "checkpoints, coarse start"),
                       ("S pilots N3x8", "pilots", "checkpoints, pilot score")):
    _r = RX[f"{_nm}, {_v}, rescue + CRC"]["sps"]
    RX[f"{_nm}, {_v}, NN shortlist, rescue + CRC"] = dict(kind="small", sps={**_r, "nn": _mode, "nn_keep": 1e-3})
    RX[f"{_nm}, {_v}, NN shortlist + score, rescue + CRC"] = dict(kind="small", sps={
        **_r, "nn": _mode, "nn_keep": 1e-3, "nn_score": 1.0})
# + the checkpoint NN (small_ck_nn.py) instead of the z-test at one checkpoint: every cell decoded up to CK_FR[c], then
# only the NN's shortlist (cumulative probability 1 - 1e-3, >= 8 cells) continues; the z-test checkpoints after it as
# before. Offline (ck-blind / ck-pilots, 3000 search packets per point, true cell never missed / <= 0.2 %): pilots
# R = 1/10 at 1/8 (c = 1) -> 71-94 of 201 cells; blind R = 2/5 at 1/4 (c = 3) -> 14-69 of 401, R = 1/2 at 3/16 (c = 2)
# -> 24 of 401. Blind R = 1/10 gains nothing (no information before 1/2). "NN early stop": a cell with NN probability
# > 0.9 is decoded at once
for _nm, _v, _c in (("S pilots N3x8", "checkpoints, pilot score", {"1/10": 1}),
                    ("S blind", "checkpoints", {"2/5": 3, "1/2": 2})):
    _r = RX[f"{_nm}, {_v}, rescue + CRC"]["sps"]
    RX[f"{_nm}, {_v}, checkpoint NN, rescue + CRC"] = dict(kind="small", sps={**_r, "ck_nn": _c})
    RX[f"{_nm}, {_v}, checkpoint NN + early stop, rescue + CRC"] = dict(kind="small", sps={
        **_r, "ck_nn": _c, "ck_win": 0.9})
# pilots, per rate the better NN (ck-pilots / spn-pilots evaluations): R = 1/10 the checkpoint NN at 1/8; R = 2/5 and
# 1/2 the prior NN before any decoding with a 16-cell minimum (true cell outside its top 16 in <= 0.4 % / 0.01 %; the
# checkpoint NN would cost 1/8 of every cell's decode, more than the whole pilot-score search there)
# PM racing (small_race.py replays race2-*, 30000 search packets per point, Fast-SSC cost per leaf): R = 1/10 a beam
# of the best 128 (cell, phase) hypotheses from 1/2 (half as many at 3/4) instead of the z-test there (work 0.474 ->
# 0.435, true cell or neighbour lost 5.3e-4 -> 1.3e-4 at -5 dB); R = 2/5, 1/2 phase racing at 1/2 (each cell keeps
# its phases within 20 nats of its best, then the z-test; -6 %). "tree cost": the list-1 decode up to a checkpoint is
# charged its Fast-SSC cost (at R = 1/10 the mostly frozen first half is 36 % of a pass, not 50 %); the baselines are
# re-counted the same way under their own names
_RACE = {"beam": {"1/10": (0.5, 128)}, "race_phase": {"2/5": (0.5, 20.0), "1/2": (0.5, 20.0)}}
for _nm, _v in (("S blind", "checkpoints"), ("S pilots N3x8", "checkpoints, pilot score")):
    _r = RX[f"{_nm}, {_v}, rescue + CRC"]["sps"]
    RX[f"{_nm}, {_v}, rescue, tree cost + CRC"] = dict(kind="small", sps={**_r, "cost": "tree"})
    RX[f"{_nm}, {_v}, PM racing, rescue, tree cost + CRC"] = dict(kind="small", sps={**_r, "cost": "tree", **_RACE})
# blind MAC cuts with the existing methods (user 2026-10-29: blind MACs down to the pilots' level at R = 2/5, 1/10),
# all with the tree cost: R = 2/5, 1/2 on the checkpoint-NN receiver: best-first (the 4th-power periodogram's best 32
# cells first, the whole grid only if nothing passes there; the periodogram ranks the true cell ~20th of 401 at R = 2/5)
# and / or the 4-peak fast path (peaks within 0.85 of the highest, graded by the left-half metric of both pi/2
# branches, as blind_fast eco3); R = 1/10 on the coarse-start receiver: the PM beam from 1/2 (128, then 64)
_CN = RX["S blind, checkpoints, checkpoint NN, rescue + CRC"]["sps"]
for _v, _x in (("", {}), (", best-first 32", {"prior": ("s4",), "first_k": 32}), (", 4-peak fast path", {"blind_peaks": 4}),
               (", best-first 32, 4-peak fast path", {"prior": ("s4",), "first_k": 32, "blind_peaks": 4}),
               (", best-first 16", {"prior": ("s4",), "first_k": 16})):
    RX[f"S blind, checkpoints, checkpoint NN{_v}, rescue, tree cost + CRC"] = dict(kind="small", sps={
        **_CN, "cost": "tree", **_x})
_CS = RX["S blind, checkpoints, coarse start, rescue + CRC"]["sps"]
RX["S blind, checkpoints, coarse start, rescue, tree cost + CRC"] = dict(kind="small", sps={**_CS, "cost": "tree"})
RX["S blind, checkpoints, coarse start, beam, rescue, tree cost + CRC"] = dict(kind="small", sps={
    **_CS, "cost": "tree", "beam": {"1/10": (0.5, 128)}})
# blind R = 1/10 trading BLER margin for MACs (user 2026-10-29: BLER is great, complexity too high; at -4.5 dB and up
# blind is 4-10x below the split NN): 2 phase hypotheses per cell instead of 4 (+ the +-pi/12 sub-offsets of the
# candidates), and / or a harder cut at 1/2 (z > 0 instead of -0.5, the best 8 cells instead of 16)
for _v, _x in ((", 2 phases", {"nph": 2, "sub3": True}), (", hard cut", {"tau": {"1/10": 0.0, "2/5": -1.0, "1/2": -1.0}, "kmin": 8}),
               (", 2 phases, hard cut", {"nph": 2, "sub3": True, "tau": {"1/10": 0.0, "2/5": -1.0, "1/2": -1.0}, "kmin": 8})):
    RX[f"S blind, checkpoints, coarse start{_v}, rescue, tree cost + CRC"] = dict(kind="small", sps={
        **_CS, "cost": "tree", **_x})
# coarse start, cheaper neighbour join (user 2026-10-29: >= 50 % fewer MACs at low SNR, same BLER): with the coarse
# start every surviving coarse cell brought in BOTH neighbours with all 4 phases, re-buying most of the grid up to 1/2.
# "one-sided join": only the neighbour on the side of the better adjacent coarse cell; "phase hand-off": the carrier
# phase (referenced to the packet centre) is common to adjacent CFO hypotheses, so a joining cell decodes only the 2
# phases nearest its parent's best one. Pilots: H with the coarse start at R = 1/10 (checkpoints 1/2, 3/4, tau -0.5)
_HC = {**RX["S pilots N3x8, checkpoints, pilot score, rescue + CRC"]["sps"], "coarse": True,
       "ck": {"1/10": (0.5, 0.75), "2/5": (0.125, 0.25, 0.375, 0.5, 0.75), "1/2": (0.125, 0.25, 0.5, 0.75)},
       "tau": {"1/10": -0.5, "2/5": 1.0, "1/2": 1.0}}
RX["S pilots N3x8, checkpoints, pilot score, coarse start, rescue, tree cost + CRC"] = dict(kind="small", sps={
    **_HC, "cost": "tree"})
for _v, _x in ((", one-sided join", {"join_side": True}), (", phase hand-off", {"join_nph": 2}),
               (", one-sided join, phase hand-off", {"join_side": True, "join_nph": 2})):
    RX[f"S blind, checkpoints, coarse start{_v}, rescue, tree cost + CRC"] = dict(kind="small", sps={
        **_CS, "cost": "tree", **_x})
    RX[f"S pilots N3x8, checkpoints, pilot score, coarse start{_v}, rescue, tree cost + CRC"] = dict(
        kind="small", sps={**_HC, "cost": "tree", **_x})
# "join top 16": only the 16 best surviving coarse cells bring in neighbours (all survivors continue)
for _v, _x in ((", join top 16", {"join_top": 16}), (", join top 16, phase hand-off", {"join_top": 16, "join_nph": 2})):
    RX[f"S blind, checkpoints, coarse start{_v}, rescue, tree cost + CRC"] = dict(kind="small", sps={
        **_CS, "cost": "tree", **_x})
    RX[f"S pilots N3x8, checkpoints, pilot score, coarse start{_v}, rescue, tree cost + CRC"] = dict(
        kind="small", sps={**_HC, "cost": "tree", **_x})
# round 3: + each continuing cell keeps its best 2 phases at 1/2; pilots also with an early checkpoint at 1/8 (the pilot
# score is informative there: the coarse cells are pruned before most of the decode)
_J = {"join_top": 16, "join_nph": 2}
RX["S blind, checkpoints, coarse start, join top 16, phase hand-off, keep 2 phases, rescue, tree cost + CRC"] = dict(
    kind="small", sps={**_CS, "cost": "tree", **_J, "phase_keep": {"1/10": (0.5, 2)}})
_HE = {**_HC, "ck": {**_HC["ck"], "1/10": (0.125, 0.5, 0.75)}}
for _v, _x in ((", early 1/8", {}), (", early 1/8, keep 2 phases", {"phase_keep": {"1/10": (0.5, 2)}})):
    RX[f"S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off{_v}, rescue, tree cost + "
       f"CRC"] = dict(kind="small", sps={**_HE, "cost": "tree", **_J, **_x})
RX["S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off, keep 2 phases, rescue, "
   "tree cost + CRC"] = dict(kind="small", sps={**_HC, "cost": "tree", **_J, "phase_keep": {"1/10": (0.5, 2)}})
# round 4: coarse start on every 3rd cell (the two cells between on the better side join), and a tighter join (top 8)
_K2 = {"phase_keep": {"1/10": (0.5, 2)}}
for _v, _x in ((", stride 3", {"stride": 3, "join_side": True}), (", join top 8", {"join_top": 8})):
    RX[f"S blind, checkpoints, coarse start, join top 16, phase hand-off, keep 2 phases{_v}, rescue, tree cost + CRC"] =         dict(kind="small", sps={**_CS, "cost": "tree", **_J, **_K2, **_x})
    RX[f"S pilots N3x8, checkpoints, pilot score, coarse start, join top 16, phase hand-off, keep 2 phases{_v}, rescue, "
       f"tree cost + CRC"] = dict(kind="small", sps={**_HC, "cost": "tree", **_J, **_K2, **_x})
RX["S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC"] = dict(kind="small", sps={
    **RX["S pilots N3x8, checkpoints, pilot score, rescue + CRC"]["sps"], "ck_nn": {"1/10": 1},
    "nn": {"2/5": "pilots", "1/2": "pilots"}, "nn_keep": 1e-3, "nn_min": 16})


# a bounded number of parallel decoders (user 2026-10-29: 201 / 401 parallel decodes are not realistic; try 64 and 32):
# "top K": the grader (blind: the 4th-power spectrum, pilots: the cell-prior NN) keeps only its best K cells, nothing
# else is ever decoded; "batches of K": contiguous blocks of <= K cells in the grader's order, decoded one block at a
# time to the first checkpoint, a block without a cell at z >= z_rej is dropped there and the next block starts; the
# rounds are cumulative (the last one sees every cell, paid cells are not re-charged), so no cell is lost for good
_B10 = {**_CS, "cost": "tree", **_J, **_K2, "join_top": 8}
_P10 = {**_HC, "cost": "tree", **_J, **_K2, "join_top": 8}
_BZ = {**RX["S blind, checkpoints, rescue + CRC"]["sps"], "cost": "tree"}
_PN = RX["S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC"]["sps"]
for _K in (64, 32):
    RX[f"S blind 1/10 best, top {_K}"] = dict(kind="small", sps={**_B10, "prior": ("s4",), "top_k": _K})
    RX[f"S pilots 1/10 best, top {_K}"] = dict(kind="small", sps={**_P10, "nn": "pilots", "top_k": _K})
    RX[f"S blind z-test, top {_K}"] = dict(kind="small", sps={**_BZ, "prior": ("s4",), "top_k": _K})
    RX[f"S pilots NN per rate, top {_K}"] = dict(kind="small", sps={**_PN, "nn": "pilots", "top_k": _K})
    for _z in (3.0, 5.0):
        RX[f"S blind 1/10 best, batches of {_K}, z {_z:g}"] = dict(kind="small", sps={
            **_B10, "prior": ("s4",), "batch": (_K, _z)})
        RX[f"S pilots 1/10 best, batches of {_K}, z {_z:g}"] = dict(kind="small", sps={
            **_P10, "nn": "pilots", "batch": (_K, _z)})
        RX[f"S blind z-test, batches of {_K}, z {_z:g}"] = dict(kind="small", sps={
            **_BZ, "prior": ("s4",), "batch": (_K, _z)})

# time-multiplexed cores (user 2026-10-29: run the 32 cores 4 times / the 64 cores twice; the stored path metrics of
# every pass are compared jointly, nothing is decoded again): the same receivers on a fixed number of cores (same MACs,
# more passes), and the grader's top 128 cells on 32 / 64 cores
_CN25 = {**_CN, "cost": "tree"}
for _K in (64, 32):
    RX[f"S blind 1/10 best, {_K} cores"] = dict(kind="small", sps={**_B10, "cores": _K})
    RX[f"S pilots 1/10 best, {_K} cores"] = dict(kind="small", sps={**_P10, "cores": _K})
    RX[f"S blind checkpoint NN, {_K} cores"] = dict(kind="small", sps={**_CN25, "cores": _K})
    RX[f"S pilots NN per rate, {_K} cores"] = dict(kind="small", sps={**_PN, "cores": _K})
    RX[f"S blind 1/10 best, top 128, {_K} cores"] = dict(kind="small", sps={**_B10, "prior": ("s4",), "top_k": 128, "cores": _K})
    RX[f"S pilots 1/10 best, top 128, {_K} cores"] = dict(kind="small", sps={**_P10, "nn": "pilots", "top_k": 128, "cores": _K})
    RX[f"S blind z-test, top 128, {_K} cores"] = dict(kind="small", sps={**_BZ, "prior": ("s4",), "top_k": 128, "cores": _K})
    RX[f"S pilots NN per rate, top 128, {_K} cores"] = dict(kind="small", sps={**_PN, "nn": "pilots", "top_k": 128, "cores": _K})

# joint CA-SCL of the candidates (user 2026-10-29: on 32 cores 4 candidates x 8 list paths at once, with a global
# path metric that cuts the unwanted paths): each candidate cell's best 2 refined (CFO, phase) hypotheses, 4 cells per
# decode (8 hypotheses), one list of 32 / 16 / 8 paths pruned over all of them (PiCode.decode_joint)
for _b in ("S blind 1/10 best, batches of 32, z 5", "S pilots 1/10 best, batches of 32, z 3", "S pilots 1/10 best, 32 cores",
           "S blind checkpoint NN, 32 cores", "S pilots NN per rate, 32 cores"):
    for _L in (32, 16, 8):
        RX[f"{_b}, joint L{_L}"] = dict(kind="small", sps={**RX[_b]["sps"], "joint": (2, _L, 4)})

# blind R = 1/10 BLER rising above -3 dB (2.4e-4 at -2, 1.9e-3 at 0 dB, none undetected): diagnosis with 4 phase
# hypotheses per cell at every SNR (from -1 dB up the receiver tries 2)
RX["S blind 1/10 best, 4 phases"] = dict(kind="small", sps={**_B10, "nph": 4})
# and the grid step: blind_fast.grid_step widens it at R = 1/10 to 6 STEP from -2 dB and 8 from 0 dB (tuned on the
# +-0.2 receivers that decoded every cell in full); with the coarse start and the checkpoint at 1/2 the cell basin is
# about one cell of 4 STEP. "grid 4": 4 STEP at every SNR
RX["S blind 1/10 best, grid 4"] = dict(kind="small", sps={**_B10, "kstep": {"1/10": 4}})
RX["S blind 1/10 best, grid 4, 4 phases"] = dict(kind="small", sps={**_B10, "kstep": {"1/10": 4}, "nph": 4})
RX["S blind, checkpoints, coarse start, rescue, grid 4 + CRC"] = dict(kind="small", sps={
    **RX["S blind, checkpoints, coarse start, rescue + CRC"]["sps"], "kstep": {"1/10": 4}})
RX["S pilots 1/10 best, grid 4"] = dict(kind="small", sps={**_P10, "kstep": {"1/10": 4}})

# the final receivers on 32 decoder cores (user 2026-10-29): R = 1/10 the coarse-start / join receivers with the grid
# step fixed at 4 STEP, in batches of 32 cells (blind z 5, pilots z 3); R = 2/5, 1/2 the checkpoint NN (blind) / the
# prior NN (pilots) on 32 cores in passes with the joint CA-SCL (16 paths over 4 candidates x 2 hypotheses); blind R = 2/5
# also with the best-first 32 cells
RX["S blind final"] = dict(kind="small", sps={**_B10, "kstep": {"1/10": 4}, "prior": ("s4",), "batch": {"1/10": (32, 5.0)}})
RX["S pilots final"] = dict(kind="small", sps={**_P10, "kstep": {"1/10": 4}, "nn": "pilots", "batch": {"1/10": (32, 3.0)}})
RX["S blind final 2/5, 1/2"] = dict(kind="small", sps={**_CN25, "cores": 32, "joint": (2, 16, 4)})
RX["S blind final 2/5, 1/2, best-first 32"] = dict(kind="small", sps={
    **_CN25, "cores": 32, "joint": (2, 16, 4), "prior": ("s4",), "first_k": {"2/5": 32}})
RX["S pilots final 2/5, 1/2"] = dict(kind="small", sps={**_PN, "cores": 32, "joint": (2, 16, 4)})
# blind final at R = 1/10: 1.0e-3 at -5 dB at full statistics (old receiver 1.8e-4): batches vs the join steps
# jt-10 (no batches) = the same 1.0e-3: the cheaper neighbour join loses packets blind, not the batches. The old coarse
# start (both neighbours, every phase) in batches of 32, and each join step added back alone
_CSB = {**_CS, "cost": "tree", "kstep": {"1/10": 4}, "prior": ("s4",), "batch": {"1/10": (32, 5.0)}}
for _v, _x in (("", {}), (", join top 16 + hand-off", _J), (", keep 2 phases", _K2), (", join top 8", {"join_top": 8})):
    RX[f"S blind C, batches of 32{_v}"] = dict(kind="small", sps={**_CSB, **_x})
# diag-c (40000 packets, -5 dB): join top 16 / 8 lose the right cell without pilots (37 / 43 errors vs 9), keeping the
# best 2 phases at 1/2 is free (10 errors, -31 % MACs). The blind R = 1/10 final receiver (v2): the full neighbour join
RX["S blind final v2"] = dict(kind="small", sps={**_CSB, **_K2})
for _K, _z in ((32, 3.0), (64, 5.0)):
    RX[f"S blind final, batches of {_K}, z {_z:g}"] = dict(kind="small", sps={
        **_B10, "kstep": {"1/10": 4}, "prior": ("s4",), "batch": {"1/10": (_K, _z)}})
# the same final receivers with the re-encoding check switched off (CRC-16 alone accepts; the check is still computed
# and counted, not applied): the BLER / undetected cost of dropping it
for _k in ("S blind final", "S blind final 2/5, 1/2", "S pilots final", "S pilots final 2/5, 1/2"):
    RX[_k + ", CRC only"] = dict(kind="small", sps={**RX[_k]["sps"], "reencode": False})
    for _d in (-1.0, -0.5, 0.5, 1.0):                         # robustness: the receiver told the SNR off by _d dB
        RX[f"{_k}, SNR error {_d:+g} dB"] = dict(kind="small", sps={**RX[_k]["sps"], "snr_err": _d})
    # an SNR underestimated by 1 dB lowered the re-encoding threshold (undetected errors): the threshold computed at
    # the SNR estimate + 1 dB
    RX[_k + ", check margin 1 dB"] = dict(kind="small", sps={**RX[_k]["sps"], "re_margin": 1.0})
    RX[_k + ", check margin 1 dB, SNR error -1 dB"] = dict(kind="small", sps={**RX[_k]["sps"], "re_margin": 1.0, "snr_err": -1.0})


class Peaks:
    """Candidate CFOs of a batch: top-NPEAK bins (periodogram or NN), refined lazily per peak index."""

    def __init__(self, r, rx, snr, source):
        self.r, self.snr = r, snr
        self.fs = bc.spectral(rx)
        if source == "nn":
            import blind_nn
            self.bins = blind_nn.peak_bins(blind_nn.load(), r, snr, NPEAK)
        else:
            self.bins = bc.top_peaks(np.abs(np.fft.fft(-(r ** 4), bc.NFFT4)), NPEAK, radius=bc.NFFT4 // bc.N_SYM * 2)
        self.f = np.full(self.bins.shape, np.nan)

    def get(self, idx, p):
        """Refined, 1/4-resolved CFO (len(idx), len(p)) of peaks p of frames idx (periodogram order kept)."""
        need = np.isnan(self.f[np.ix_(idx, p)])
        if need.any():
            rows = idx[need.any(1)]
            y = -(self.r[rows] ** 4)
            nu, _ = bc._newton_tone(y, np.fft.fftfreq(bc.NFFT4)[self.bins[np.ix_(rows, p)]])
            self.f[np.ix_(rows, p)] = bc.resolve((nu + 0.5) % 1.0 - 0.5, self.fs[rows])
        return self.f[np.ix_(idx, p)]


def _metric(name, llr, code):
    if name == "SC":
        return bc.sc_metric(llr, bc.sc_code(code.A))
    return bc.syndrome_soft(llr, code.frozen, 16)


def run_receiver(spec, r, peaks, code, sigma2, st):
    """One blind receiver on a batch. Returns decoded data (B, A), passed (B,), final CFO (B,)."""
    B = len(r)
    out = np.zeros((B, code.A), np.uint8)
    have = np.zeros(B, bool)                       # a first decode exists (delivered if nothing passes)
    passed = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
    th_fin = np.zeros(B)
    stages = spec.get("stages", STAGES)
    for stage in stages:
        if stage == "grid":
            _grid_stage(r, peaks, code, sigma2, st, spec, out, have, passed, f_fin, th_fin)
            continue
        pk, offs, T = stage[:3]
        n_dd = stage[3] if len(stage) > 3 else 0
        idx = np.where(~passed)[0]
        if not len(idx):
            break
        fp = peaks.get(idx, pk)                                                  # (n, P)
        F = (fp[:, :, None] + np.array(offs, float)[None, None, :] * bc.STEP).reshape(len(idx), -1)
        TH = bc.phase4(r[idx], F)
        nq = spec.get("phases", 2)                 # 2: the phase mod pi (PiCode resolves pi); 4: mod 2 pi
        F = np.repeat(F, nq, axis=1)
        TH = (TH[:, :, None] + np.arange(nq)[None, None, :] * np.pi / 2).reshape(len(idx), -1)
        H = F.shape[1]
        rows = idx[np.repeat(np.arange(len(idx)), H)]
        fl, tl = F.ravel(), TH.ravel()
        M = np.empty(len(fl))
        for a in range(0, len(fl), CHUNK_H):
            sl = slice(a, a + CHUNK_H)
            M[sl] = _metric(spec["metric"], bc.llrs(r[rows[sl]], fl[sl], tl[sl], sigma2), code)
        st["metric_evals"] += len(fl)
        order = np.argsort(M.reshape(len(idx), H), 1)
        act = np.ones(len(idx), bool)
        for t in range(min(T, H)):
            j = np.where(act)[0]
            if not len(j):
                break
            fh = F[j, order[j, t]]
            th = TH[j, order[j, t]]
            fr = idx[j]
            d, ok, _ = code.decode(bc.llrs(r[fr], fh, th, sigma2), return_info=True)
            st["decodes"] += len(j)
            for it in range(n_dd):                     # turbo: decision-directed re-estimation, re-decode
                bad = np.where(~ok)[0]
                if not len(bad):
                    break
                f2, t2 = bc.dd_refine(r[fr[bad]], d[bad], code, fh[bad])
                d2, ok2, _ = code.decode(bc.llrs(r[fr[bad]], f2, t2, sigma2), return_info=True)
                st["decodes"] += len(bad)
                d[bad], ok[bad], fh[bad], th[bad] = d2, ok2, f2, t2
            first = ~have[fr]
            out[fr[first]], have[fr[first]] = d[first], True
            f_fin[fr[first]], th_fin[fr[first]] = fh[first], th[first]
            w = fr[ok]
            out[w], passed[w], f_fin[w], th_fin[w] = d[ok], True, fh[ok], th[ok]
            act[j[ok]] = False
    return out, passed, f_fin


def _phase4_blocks(r, F, blk=8):
    """phase4 over frames in blocks (the (B, H, N) exponent of a large grid does not fit in memory at once)."""
    return np.concatenate([bc.phase4(r[a:a + blk], F[a:a + blk]) for a in range(0, len(r), blk)])


def _score(spec, r, rows, F, TH, code, sigma2, st):
    fl, tl = F.ravel(), TH.ravel()
    M = np.empty(len(fl))
    for a in range(0, len(fl), CHUNK_H):
        sl = slice(a, a + CHUNK_H)
        M[sl] = _metric(spec["metric"], bc.llrs(r[rows[sl]], fl[sl], tl[sl], sigma2), code)
    st["metric_evals"] += len(fl)
    return M.reshape(F.shape)


def _grid_stage(r, peaks, code, sigma2, st, spec, out, have, passed, f_fin, th_fin, keep=3, T=3):
    idx = np.where(~passed)[0]
    if not len(idx):
        return
    sig = float(np.interp(peaks.snr, *zip(*SPEC_SIGMA)))
    J = int(np.ceil(min(spec.get("grid_k", 3) * sig, spec.get("grid_cap", GRID_CAP)) / GRID_STEP))
    G = peaks.fs[idx, None] + np.arange(-J, J + 1)[None, :] * GRID_STEP                  # (n, 2J+1)
    TH = _phase4_blocks(r[idx], G)
    Fh, Th = np.repeat(G, 2, 1), (TH[:, :, None] + np.array([0, np.pi / 2])).reshape(len(idx), -1)
    M = _score(spec, r, idx[np.repeat(np.arange(len(idx)), Fh.shape[1])], Fh, Th, code, sigma2, st)
    best_j = np.argsort(M.reshape(len(idx), -1, 2).min(2), 1)[:, :keep]                  # best grid points
    base = np.take_along_axis(G, best_j, 1)                                                # (n, keep)
    F = (base[:, :, None] + np.array([-2, -1, 0, 1, 2])[None, None, :] * bc.STEP).reshape(len(idx), -1)
    TH = _phase4_blocks(r[idx], F)
    F, TH = np.repeat(F, 2, 1), (TH[:, :, None] + np.array([0, np.pi / 2])).reshape(len(idx), -1)
    M = _score(spec, r, idx[np.repeat(np.arange(len(idx)), F.shape[1])], F, TH, code, sigma2, st)
    order = np.argsort(M, 1)
    act = np.ones(len(idx), bool)
    for t in range(T):
        j = np.where(act)[0]
        if not len(j):
            break
        fh, th, fr = F[j, order[j, t]], TH[j, order[j, t]], idx[j]
        d, ok, _ = code.decode(bc.llrs(r[fr], fh, th, sigma2), return_info=True)
        st["decodes"] += len(j)
        w = fr[ok]
        out[w], passed[w], f_fin[w], th_fin[w] = d[ok], True, fh[ok], th[ok]
        act[j[ok]] = False


def simulate(task):
    rate, snr, seed, max_frames, min_errors, rx_names, noise = task
    rng = np.random.default_rng(seed)
    code = PolarCode(bc.N_BITS, bc.CODES[rate], 16, 8)
    pi_code = bc.PiCode(bc.N_BITS, bc.CODES[rate], 16, 8)      # the blind receivers (phase known only mod pi)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    names = [GENIE] + list(rx_names)
    st = {k: dict(frames=0, frame_err=0, bit_err=0, undetected=0, decodes=0, metric_evals=0, se_coarse=0.0,
                  se_final=0.0, se_dd=0.0, n_dd=0, time=0.0, timed_frames=0) for k in names}
    running = lambda k: st[k]["frame_err"] < min_errors and st[k]["frames"] < max_frames
    B = 100
    while any(running(k) for k in names):
        data, cw, r, rx, f, th = bc.frames(B, code, snr, rng, noise_only=noise)
        cache = {}
        for k in names:
            if not running(k):
                continue
            s = st[k]
            t0 = time.perf_counter()                 # receiver wall time per packet (chain excluded, 1 thread)
            m0 = s.get("macs", 0.0)
            if k == GENIE:
                dec, ok, _ = code.decode(bc.llrs(r, f, th, sigma2), return_info=True)
                s["decodes"] += B
                s["macs"] = s.get("macs", 0.0) + B * (8 * bc.N_BITS * 11 + 6144)
                ff = f.copy()
                fc = f
            elif RX[k].get("kind") == "vp":
                import blind_vp
                sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
                spec = {**RX[k], "vp": {**RX[k]["vp"], "rate": rate}}
                dec, ok, ff, f_top = blind_vp.vp_receive(r, rx, snr, code, sigma2, s, spec, sym)
                s["se_coarse"] += float(np.sum((f_top - f) ** 2))
                fc = f_top
            elif RX[k].get("kind") == "genie_premf":           # the MF matched to the true CFO (bound of premf)
                import blind_fast
                rc = blind_fast.premf(r, rx, f)
                dec, ok, _ = code.decode(bc.llrs(rc, f, th, sigma2), return_info=True)
                s["decodes"] += B
                ff = f.copy()
                fc = f
            elif RX[k].get("kind") in ("sps", "sps2", "sps3", "small"):
                import blind_fast
                import small_rx
                spec = {**RX[k], "sps": {**RX[k]["sps"], "rate": rate}}
                if RX[k]["kind"] == "small":                 # the true data, only to count the CRC-only undetected
                    spec["sps"]["truth"] = data              # errors and the checks' catches (small_rx._truth)
                fn = {"sps": blind_fast.sps_receive, "sps2": blind_fast.sps2_receive,
                      "sps3": blind_fast.sps3_receive, "small": small_rx.small_receive}[RX[k]["kind"]]
                sym = (((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
                       if spec["sps"].get("pilots") else None)
                dec, ok, ff, f_top = (fn(r, rx, snr, pi_code, sigma2, s, spec, sym) if sym is not None
                                      else fn(r, rx, snr, pi_code, sigma2, s, spec))
                s["se_coarse"] += float(np.sum((f_top - f) ** 2))
                fc = f_top
            else:
                spec = RX[k]
                if spec["peaks"] not in cache:
                    cache[spec["peaks"]] = (Peaks(r, rx, snr, spec["peaks"]), time.perf_counter() - t0)
                else:
                    t0 -= cache[spec["peaks"]][1]      # a shared candidate list counts for every receiver
                pk = cache[spec["peaks"]][0]
                dec, ok, ff = run_receiver(spec, r, pk, code if spec.get("phases", 2) == 4 else pi_code, sigma2, s)
                fc = pk.get(np.arange(B), [0])[:, 0]
                s["se_coarse"] += float(np.sum((fc - f) ** 2))
            s["time"] += time.perf_counter() - t0
            s["timed_frames"] += B
            if s.get("macs", 0.0) != m0:                     # the receiver counted its MACs for this batch
                s["mac_frames"] = s.get("mac_frames", 0) + B
            # CFO outage (|error| > TOL = 1e-4, the decoder's tolerance) of the coarse stage (first candidate) and of the
            # delivered CFO after the code-aided search (no decode at all counts as an outage)
            s["out_coarse"] = s.get("out_coarse", 0) + int(np.sum(~(np.abs(fc - f) <= bc.TOL)))
            s["out_coarse_1e3"] = s.get("out_coarse_1e3", 0) + int(np.sum(~(np.abs(fc - f) <= 1e-3)))
            s["out_frames"] = s.get("out_frames", 0) + B
            errs = dec != data
            s["frames"] += B
            s["frame_err"] += int(errs.any(1).sum())
            s["bit_err"] += int(errs.sum())
            s["undetected"] += int((errs.any(1) & ok).sum())
            good = ok & ~errs.any(1) & np.isfinite(ff)           # correctly decoded frames
            # the receiver's final CFO: decision-directed over the 1024 symbols after a CRC pass (the delivered
            # hypothesis otherwise); a final outage = |error| > TOL or no CRC pass
            f_out = np.where(np.isfinite(ff), ff, fc)
            if good.any():
                s["se_final"] += float(np.sum((ff[good] - f[good]) ** 2))
                fd, _ = bc.dd_refine(r[good], dec[good], code, ff[good])
                s["se_dd"] += float(np.sum((fd - f[good]) ** 2))
                s["n_dd"] += int(good.sum())
                f_out[good] = fd
            s["out_final"] = s.get("out_final", 0) + int(np.sum(~ok | ~(np.abs(f_out - f) <= bc.TOL)))
            s["se_final_all"] = s.get("se_final_all", 0.0) + float(np.sum((f_out - f) ** 2))
    return [{"rate": rate, "snr": snr, "rx": k + (" [noise only]" if noise else ""), **v} for k, v in st.items()]


def run(a):
    tasks = []
    points = [(p.split(":")[0], float(p.split(":")[1]), int(p.split(":")[2])) for p in a.points] if a.points         else [(a.rate, s, a.chunks) for s in a.snrs]
    for rate, s, chunks in points:
        for i in range(chunks):
            seed = zlib.crc32(repr((rate, s, a.seed, i)).encode())
            tasks.append((rate, s, seed, a.max_frames, a.min_errors, a.rx or list(RX), a.noise_only))
    tasks.sort(key=lambda t: -t[1])                 # the long, high-SNR chunks first
    t0, res = time.time(), []
    with mp.Pool(a.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(simulate, tasks), 1):
            res += r
            with open(bc.path("logs", f"blind_ber_{a.part}.progress"), "a") as fh:
                fh.write(f"{i} {len(tasks)} {time.time() - t0:.0f}\n")
    json.dump(res, open(bc.path("results", f"blind_ber_{a.part}.json"), "w"), indent=1)
    for r in sorted(res, key=lambda r: (r["snr"], r["rx"])):
        print(f"{r['rate']} {r['snr']:5.1f} {r['rx']:36s} BLER {r['frame_err'] / r['frames']:.2e} "
              f"({r['frame_err']}/{r['frames']}) decodes {r['decodes'] / r['frames']:.2f}", flush=True)
    print("EVAL DONE", flush=True)


OLD_DD_PARTS = ("a", "b", "c", "d")       # turbo runs made with the Newton-only dd_refine (capture +-2e-4)


def merge():
    tot = {}
    for p in sorted(glob.glob(bc.path("results", "blind_ber_*.json"))):
        if p.endswith("blind_ber.json"):
            continue
        part = os.path.basename(p)[len("blind_ber_"):-len(".json")]
        if "smoke" in part:              # smoke tests reuse the paired seeds: their packets would be counted twice
            continue
        for r in json.load(open(p)):
            if r["rx"] == "4th power + turbo (DD) + CRC" and part in OLD_DD_PARTS:
                r = {**r, "rx": r["rx"] + " [Newton-only DD]"}   # run before the DD scan fix (dd_refine), kept apart
            k = (r["rate"], r["snr"], r["rx"])
            if k not in tot:
                tot[k] = dict(r)
            else:
                for f in r:
                    if f not in ("rate", "snr", "rx"):
                        tot[k][f] = tot[k].get(f, 0) + r[f]
    out = []
    for r in tot.values():
        n = r["frames"]
        r.update(bler=r["frame_err"] / n, ber=r["bit_err"] / (n * bc.CODES[r["rate"]]), undetected_bler=r["undetected"] / n,
                 decodes_per_frame=r["decodes"] / n,
                 time_per_frame=r["time"] / r["timed_frames"] if r.get("timed_frames") else None,
                 macs_per_frame=r["macs"] / r["mac_frames"] if r.get("mac_frames") else None,
                 macs_per_core=r["core_macs"] / r["mac_frames"] if r.get("core_macs") else None,
                 cores_per_frame=r["cores"] / r["mac_frames"] if r.get("cores") else None,
                 passes_per_frame=r["passes"] / r["mac_frames"] if r.get("passes") else None,
                 crit_macs_per_frame=r["crit_macs"] / r["mac_frames"] if r.get("crit_macs") else None,
                 crit_lp_macs_per_frame=r["crit_lp_macs"] / r["mac_frames"] if r.get("crit_lp_macs") else None,
                 crc_undetected_bler=r["crc_undetected"] / n if "crc_undetected" in r else None,
                 outage_coarse=r["out_coarse"] / r["out_frames"] if r.get("out_frames") else None,
                 outage_coarse_1e3=r["out_coarse_1e3"] / r["out_frames"] if r.get("out_frames") else None,
                 outage_final=r["out_final"] / r["out_frames"] if r.get("out_frames") else None,
                 rmse_final_all=float(np.sqrt(r["se_final_all"] / r["out_frames"])) if r.get("out_frames") else None, metric_evals_per_frame=r["metric_evals"] / n,
                 rmse_coarse=float(np.sqrt(r["se_coarse"] / n)),
                 rmse_final=float(np.sqrt(r["se_final"] / max(r["n_dd"], 1))),
                 rmse_dd=float(np.sqrt(r["se_dd"] / max(r["n_dd"], 1))))
        out.append(r)
    json.dump(sorted(out, key=lambda r: (r["rate"], r["snr"], r["rx"])), open(bc.path("results", "blind_ber.json"), "w"),
              indent=1)
    print(f"merged {len(out)} points")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", default="1/4", choices=list(bc.CODES))
    ap.add_argument("--snrs", type=float, nargs="+", default=[2.0])
    ap.add_argument("--rx", nargs="+", choices=list(RX), default=None)
    ap.add_argument("--chunks", type=int, default=1, help="independent runs per SNR (one per worker)")
    ap.add_argument("--points", nargs="+", default=None, help='"rate:snr:chunks" items (overrides --rate/--snrs)')
    ap.add_argument("--max-frames", type=int, default=100000, help="per chunk")
    ap.add_argument("--min-errors", type=int, default=100, help="per chunk")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--part", default="a")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--noise-only", action="store_true", help="packets without signal (false alarms)")
    a = ap.parse_args()
    merge() if a.merge else run(a)
