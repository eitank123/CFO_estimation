"""
Monte-Carlo BLER of our rate-matched polar code (fullsys/polar_rm.py, CA-SCL-8, CRC-32) at the competitors' native
(A, E), code only, genie sync: the blind side of the full-system comparison with DVB-RCS2 (run_rcs2.py) and VDE-SAT
(run_vde.py). Blind sends only the E coded bits (no UW / pilots / syncwords): n_sym = E / 2 (QPSK) or E (BPSK).

    tx  data (B, A) -> RMPolarCode.encode_rm (CRC-32 0x04C11DB7, init 0) -> e (B, E) -> map:
        qpsk    : Gray, I = (1 - 2 e_2k)/sqrt2, Q = (1 - 2 e_2k+1)/sqrt2            (= rcs2 Waveform.map)
        pi2bpsk : s(n) = (1 - 2 e_n) exp(j (pi n / 2 + pi / 4)), n = 0 .. E - 1   (EN 301 545-2 7.3.7.1.4.1)
        bpsk    : s(n) = 1 - 2 e_n                     (VDE-SAT Link 32; the SF 8 spreading is not simulated: in
                  genie AWGN despreading SF chips at Ec/N0 = Es/N0 - 10 log10 8 gives the same Es/N0 per symbol)
    ch  txrx_chain.transmit (upsample x SPS, RRC roll-off --beta (0.20, DVB-RCS2 cl. 7.3.7.1.1), AWGN Es/N0 per
        symbol, matched RRC, downsample), f = 0, phase 0
    rx  genie: true timing, zero CFO, true phase, known N0 = 1 / (Es/N0) (as rcs2.rx sync='ideal'); max-log =
        exact per-dimension LLRs: qpsk 2 sqrt2 Re / Im (y) / N0, (pi/2-)BPSK 4 Re(y [e^-j(pi n/2 + pi/4)]) / N0;
        rate recovery (punctured 0, shortened +LLR_BIG) -> CA-SCL-8 -> the CRC-passing path with the best metric

Frame error = CRC fail OR data mismatch; undetected = CRC pass AND mismatch (as run_rcs2). Acceptance = CRC only.
Measurement only (no gating): the project's re-encoding check (blind_fast.reencode_rho / rho_min with the per-rate
table blind_ber.RHO_N, normalised: thr = max(rho_min(s), RHO_N(s) sqrt(s / (1 + s))), rho = |sum y s^*| /
sqrt(n_sym sum |y|^2) of the re-encoded packet): reenc_* counters + rho_n histograms of the CRC passes. RHO_N was
calibrated on the 1024-symbol N = 2048 CRC-16 codes; the key per format is the nearest code rate (--rho-key).

Eb/N0 axis: ebn0_burst = Es/N0 + 10 log10(n_sym / A), A = payload bits = rcs2 k = K - 32 (Waveform.ebn0 with L =
n_sym, every transmitted symbol charged; no UW here). ops_per_frame = polar_rm.decode_macs total (no early stop).

Pairing: chunk c of point Es/N0 = x uses SeedSequence([--seed, tag, round(1000 x) + 100000, c]) with the data drawn
first, rng.integers(0, 2, (batch, A)).astype(int8): the run_rcs2 scheme with tag = the RCS2 waveform code (13, 14,
3, 42), so at the same --seed / --batch / point the payloads equal the rcs2 run's; id14s / id14p (and --crc 16 vs 32)
share data AND noise (same symbol count). vde32 tag 2032 (run_vde seeds differently). nb* (NB-IoT NPUSCH F1,
fullsys/nbiot.py) tags = nbiot.FORMATS tags: the payloads equal run_fullsys_da --sys nbiot's at the same --seed and
batch 200 (A = TBS, CRC-32 here vs CRC-24A there: equal payload). Run on the cluster only.

    python fullsys/run_polar_genie.py --fmt id13 --snrs -1.4 -1.2 --frames 1000000 --max-err 300 --seed 13 --part x
    python fullsys/run_polar_genie.py --selfcheck            # 3 frames at 30 dB per format (< 5 s, no BLER)
    --list L (default 8; 16 / 32): CA-SCL-L, ops_per_frame = decode_macs at L (the selfcheck too)
    --design pw|ga (default pw = the rate-matching-blind PW info set, unchanged): ga = Gaussian approximation over the
      rate-matched channel (fullsys/polar_design.py) at --design-snr Es/N0 (default DESIGN_SNR per format = the turbo
      PER-1e-3 Es/N0 + 0.3 dB), bps from the modulation (QPSK 2, BPSK / pi/2-BPSK 1); packets pair with the pw runs
    python fullsys/run_polar_genie.py --ga-check             # GA design checks + union bounds PW vs GA (no channel)
    --chan-intlv (default off: the old runs reproduce): QPSK formats send e[:, chan], chan = the blind receiver's
      channel interleaver (blind_fmt: rng(12345).permutation(E)), the demapped LLRs de-interleaved; same data / noise
      as without it (pairs exactly with run_blind_fs, whose default it is); in genie AWGN the BLER is unchanged

Writes fullsys/results/polar_genie_<part>.json (rewritten after every point; refuses an existing part) and
polar_genie_<part>.prog ("done total elapsed_s", job_progress.count_row format).
"""

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import polar_rm as rm                 # noqa: E402
import txrx_chain                                   # noqa: E402

RESULTS = os.path.join(ROOT, "fullsys", "results")
ROLLOFF = 0.20                                      # DVB-RCS2 cl. 7.3.7.1.1 (VDE-SAT uses 0.25: --beta)
L_LIST = 8
RHO_BINS = np.linspace(0.0, 1.5, 151)               # rho_n = rho / sqrt(s / (1 + s)) histogram edges
# --fmt: A payload bits, E coded bits, modulation, rate-matching mode (forced if `force`, else the 38.212 rule, checked),
# seed tag, RHO_N key (nearest code rate K / E among blind_ber.RHO_N: 1/3 -> 2/5, 1/2 -> 1/2, 0.246 -> 0.15), reference
FMTS = {
    "id13": dict(A=952, E=2952, mod="qpsk", mode="puncture", force=False, tag=13, rho_key="2/5",
                 ref="RCS2 ID 13 (QPSK 1/3, 123 B) TR 101 545-4 T10.6: PER 1e-3 -0.80, 1e-5 -0.51 dB"),
    "id14s": dict(A=1472, E=3008, mod="qpsk", mode="shorten", force=False, tag=14, rho_key="1/2",
                  ref="RCS2 ID 14 (QPSK 1/2, 188 B) T10.6: PER 1e-3 1.49, 1e-5 1.71 dB"),
    "id14p": dict(A=1472, E=3008, mod="qpsk", mode="puncture", force=True, tag=14, rho_key="1/2",
                  ref="RCS2 ID 14 (QPSK 1/2, 188 B) T10.6: PER 1e-3 1.49, 1e-5 1.71 dB"),
    "id3": dict(A=272, E=912, mod="qpsk", mode="puncture", force=False, tag=3, rho_key="2/5",
                ref="RCS2 ID 3 (QPSK 1/3, 38 B) T10.5: PER 1e-3 -0.27, 1e-5 0.22 dB"),
    "id42b": dict(A=952, E=2952, mod="pi2bpsk", mode="puncture", force=False, tag=42, rho_key="2/5",
                  ref="RCS2 ID 42 (pi/2-BPSK 1/3, 123 B) T10.8: PER 1e-3 -3.81, 1e-5 -3.52 dB"),
    "id42q": dict(A=952, E=2952, mod="qpsk", mode="puncture", force=False, tag=42, rho_key="2/5",
                  ref="RCS2 ID 42 payload on QPSK (the id13 code and map; independent packets, tag 42)"),
    "vde32": dict(A=280, E=1269, mod="bpsk", mode="puncture", force=False, tag=2032, rho_key="0.15",
                  ref="VDE-SAT Link 32 SAT-MCS-0.50-2 (BPSK SF 8, 280 b) M.2092 threshold -4.5 dB (PER unstated)"),
    # NB-IoT NPUSCH F1 single tone 3.75 kHz (fullsys/nbiot.FORMATS, same tag = same payloads at equal --seed / --batch):
    # A = TBS, E = G = 96 N_RU Q_m; mode by the 38.212 rule (N 1024 + repetition at E 1152)
    "nb208": dict(A=208, E=1152, mod="qpsk", mode="repeat", force=False, tag=5208, rho_key="0.15",
                  ref="NB-IoT NPUSCH F1 TBS 208 (I_MCS 2, I_RU 5: 6 RUs, pi/4-QPSK, LTE turbo + CRC-24A), 672 symbols"),
    "nb208b": dict(A=208, E=768, mod="pi2bpsk", mode="puncture", force=False, tag=5209, rho_key="2/5",
                   ref="NB-IoT NPUSCH F1 TBS 208 (I_MCS 0, I_RU 6: 8 RUs, pi/2-BPSK), 896 symbols"),
    "nb296": dict(A=296, E=384, mod="qpsk", mode="shorten", force=False, tag=5296, rho_key="1/2",
                  ref="NB-IoT NPUSCH F1 TBS 296 (I_MCS 9, I_RU 1: 2 RUs, pi/4-QPSK), 224 symbols"),
    "nb328": dict(A=328, E=1152, mod="qpsk", mode="repeat", force=False, tag=5328, rho_key="2/5",
                  ref="NB-IoT NPUSCH F1 TBS 328 (I_MCS 3, I_RU 5: 6 RUs, pi/4-QPSK), 672 symbols"),
    "nb808": dict(A=808, E=1536, mod="qpsk", mode="shorten", force=False, tag=5808, rho_key="1/2",
                  ref="NB-IoT NPUSCH F1 TBS 808 (I_MCS 6, I_RU 6: 8 RUs, pi/4-QPSK), 896 symbols"),
    "nb1000": dict(A=1000, E=1536, mod="qpsk", mode="shorten", force=False, tag=6000, rho_key="1/2",
                   ref="NB-IoT NPUSCH F1 TBS 1000 (I_MCS 7, I_RU 6: 8 RUs, pi/4-QPSK), 896 symbols"),
    "nb1000r10": dict(A=1000, E=1920, mod="qpsk", mode="shorten", force=False, tag=6010, rho_key="1/2",
                      ref="NB-IoT NPUSCH F1 TBS 1000 (I_MCS 6, I_RU 7: 10 RUs, pi/4-QPSK), 1120 symbols"),
}
ASSUMPTIONS = [
    "Code only, genie sync (true timing, f = 0, true phase, known N0 = 1 / (Es/N0)); blind sends no UW / pilots.",
    "Polar: polar_rm.RMPolarCode (NR-style rate matching on an N <= 4096 PW mother code, our PW order, not the NR "
    "sequence), CA-SCL-8, CRC-32 0x04C11DB7 init 0 (or --crc 16), full L N log2 N decode charged.",
    "QPSK Gray map = rcs2 (I = (1 - 2 b0)/sqrt2, Q = (1 - 2 b1)/sqrt2), coded bits in order e_0 e_1 | e_2 e_3 ...",
    "pi/2-BPSK s(n) = (1 - 2 b) exp(j (pi n / 2 + pi / 4)), n from 0 at the first coded symbol.",
    "vde32: plain BPSK, the SF 8 Gold spreading not simulated (identical Es/N0 per despread symbol in genie AWGN); "
    "roll-off --beta (default 0.20 for every format, VDE-SAT specifies 0.25; immaterial in AWGN up to filter ISI).",
    "Eb/N0 = Es/N0 + 10 log10(n_sym / A), A = payload bits (rcs2 k = K - 32, VDE kpay), n_sym = E / bits per symbol.",
    "Re-encoding check recorded, not gated: RHO_N calibrated on 1024-symbol CRC-16 packets (key = nearest rate).",
]
DESIGN_SNR = {"id13": -0.5, "id42q": -0.5, "id14s": 1.8, "id14p": 1.8, "id3": 0.0, "id42b": -3.5, "vde32": -4.2}
DESIGN_SNR.update({"nb208": -2.1, "nb208b": -3.2, "nb296": 6.5, "nb328": -0.2, "nb808": 2.7, "nb1000": 4.1,
                   "nb1000r10": 2.7})   # nb*: PLACEHOLDER guesses (no NB-IoT turbo run yet): set from fs-nbv (--design ga)
_C = {}


def _init():
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[v] = "1"


def get_code(fmt, crc, L=L_LIST, design="pw", dsnr=None):
    """RMPolarCode of a format at list size L, info set design 'pw' / 'ga' at Es/N0 dsnr (default DESIGN_SNR) (cached
    per process); asserts the expected rate-matching mode."""
    if design == "ga" and dsnr is None:
        dsnr = DESIGN_SNR[fmt]
    if (fmt, crc, L, design, dsnr) not in _C:
        f = FMTS[fmt]
        kw = dict(design="ga", design_snr_db=dsnr, bps=bps(fmt)) if design == "ga" else {}   # pw: the old call
        c = rm.RMPolarCode(f["A"], f["E"], crc_len=crc, list_size=L, mode=f["mode"] if f["force"] else None, **kw)
        assert c.mode == f["mode"], (fmt, c.mode, f["mode"])
        _C[(fmt, crc, L, design, dsnr)] = c
    return _C[(fmt, crc, L, design, dsnr)]


def n_sym(fmt):
    f = FMTS[fmt]
    return f["E"] // 2 if f["mod"] == "qpsk" else f["E"]


def bps(fmt):
    """Coded bits per symbol: QPSK 2, BPSK / pi/2-BPSK 1."""
    return 2 if FMTS[fmt]["mod"] == "qpsk" else 1


def rot(fmt):
    """pi/2-BPSK rotation exp(j (pi n / 2 + pi / 4)) (n_sym,), else None."""
    return np.exp(1j * (np.pi * np.arange(n_sym(fmt)) / 2 + np.pi / 4)) if FMTS[fmt]["mod"] == "pi2bpsk" else None


def modulate(e, fmt):
    """Coded bits e (B, E) -> unit-energy symbols (B, n_sym)."""
    mod, b = FMTS[fmt]["mod"], 1 - 2.0 * e
    if mod == "qpsk":
        return (b[:, 0::2] + 1j * b[:, 1::2]) / np.sqrt(2)
    return b * rot(fmt)[None] if mod == "pi2bpsk" else b + 0j


def demap(y, fmt, n0):
    """MF output y (B, n_sym) -> bit LLRs (B, E), L = ln P(0)/P(1) (max-log = exact for these maps)."""
    mod = FMTS[fmt]["mod"]
    if mod == "qpsk":
        L = np.empty((y.shape[0], 2 * y.shape[1]))
        L[:, 0::2], L[:, 1::2] = 2 * np.sqrt(2) * y.real / n0, 2 * np.sqrt(2) * y.imag / n0
        return L
    if mod == "pi2bpsk":
        y = y * np.conj(rot(fmt))[None]
    return 4 * y.real / n0


def reenc_thr(esn0, key):
    """The re-encoding acceptance threshold (small_rx _thr, re_margin 0): max(rho_min(s), RHO_N(s) sqrt(s/(1+s)))."""
    from blind_ber import RHO_N
    from blind_fast import rho_min
    s = 10 ** (esn0 / 10)
    thr = rho_min(esn0)
    tab = RHO_N.get(key) if key else None
    if tab:
        thr = max(thr, float(np.interp(esn0, *zip(*tab))) * np.sqrt(s / (1 + s)))
    return float(thr)


def chan_perm(fmt, on):
    """The channel interleaver of the blind system (blind_fmt.BlindFormat chan): QPSK + on -> rng(12345).permutation(E),
    else None (identity)."""
    return np.random.default_rng(12345).permutation(FMTS[fmt]["E"]) if on and FMTS[fmt]["mod"] == "qpsk" else None


def run_chunk(task):
    fmt, crc, esn0, entropy, batch, beta, thr, L, design, dsnr = task[:10]
    ch = chan_perm(fmt, task[10] if len(task) > 10 else False)       # --chan-intlv (default off)
    code = get_code(fmt, crc, L, design, dsnr)
    A = FMTS[fmt]["A"]
    rng = np.random.default_rng(np.random.SeedSequence(entropy))
    d = rng.integers(0, 2, (batch, A)).astype(np.int8)                # drawn first, as run_rcs2's pdu
    e = code.encode_rm(d.astype(np.uint8))
    s = modulate(e if ch is None else e[:, ch], fmt)
    z = np.zeros(batch)
    y = txrx_chain.transmit(s, z, z, esn0, rng, beta=beta)            # f = 0, phase = 0: genie sync
    n0 = 10 ** (-esn0 / 10)
    le = demap(y, fmt, n0)
    if ch is not None:                                                # de-interleave: sent bit k = e_{ch[k]}
        le_, le = le, np.empty_like(le)
        le[:, ch] = le_
    dh, ok, _ = code.decode(le, return_info=True)
    nbe = np.sum(dh != d, axis=1)
    mism = nbe > 0
    # (measurement) re-encoding check of the CRC passes: not gated, decisions unchanged
    rho = np.zeros(batch)
    j = np.flatnonzero(ok)
    if len(j):
        eh = code.encode_rm(dh[j].astype(np.uint8))
        sh = modulate(eh if ch is None else eh[:, ch], fmt)
        rho[j] = np.abs(np.sum(y[j] * np.conj(sh), 1)) / np.sqrt(n_sym(fmt) * np.sum(np.abs(y[j]) ** 2, 1))
    sq = np.sqrt(10 ** (esn0 / 10) / (1 + 10 ** (esn0 / 10)))
    acc = ok & (rho > thr)
    right, wrong = ok & ~mism, ok & mism
    return dict(frames=batch, frame_err=int(np.sum(~ok | mism)), crc_fail=int(np.sum(~ok)),
                undetected=int(np.sum(wrong)), mismatch=int(mism.sum()), bit_err=int(nbe.sum()),
                reenc_pass=int(acc.sum()), reenc_reject_right=int(np.sum(right & ~acc)),
                reenc_reject_wrong=int(np.sum(wrong & ~acc)), frame_err_reenc=int(np.sum(~acc | mism)),
                rho_hist_right=np.histogram(np.clip(rho[right] / sq, 0, 1.4999), RHO_BINS)[0].tolist(),
                rho_hist_wrong=np.histogram(np.clip(rho[wrong] / sq, 0, 1.4999), RHO_BINS)[0].tolist(),
                rho_min_right=float(rho[right].min() / sq) if right.any() else None,
                rho_max_wrong=float(rho[wrong].max() / sq) if wrong.any() else None)


def _add(acc, res):
    for k, v in res.items():
        if k.startswith("rho_hist"):
            acc[k] = [a + b for a, b in zip(acc[k], v)]
        elif k == "rho_min_right":
            acc[k] = v if acc[k] is None else (acc[k] if v is None else min(acc[k], v))
        elif k == "rho_max_wrong":
            acc[k] = v if acc[k] is None else (acc[k] if v is None else max(acc[k], v))
        else:
            acc[k] += v


def run_point(fmt, esn0, args, thr, prog):
    nch = -(-args.frames // args.batch)
    tasks = ((fmt, args.crc, esn0, [args.seed, FMTS[fmt]["tag"], int(round(esn0 * 1000)) + 100000, c],
              min(args.batch, args.frames - c * args.batch), args.beta, thr, args.list, args.design, args.design_snr,
              args.chan_intlv) for c in range(nch))
    acc = dict(frames=0, frame_err=0, crc_fail=0, undetected=0, mismatch=0, bit_err=0, reenc_pass=0,
               reenc_reject_right=0, reenc_reject_wrong=0, frame_err_reenc=0, rho_hist_right=[0] * (len(RHO_BINS) - 1),
               rho_hist_wrong=[0] * (len(RHO_BINS) - 1), rho_min_right=None, rho_max_wrong=None)
    t0 = tlast = time.time()
    with Pool(args.workers, initializer=_init) as pool:
        for res in pool.imap(run_chunk, tasks):
            _add(acc, res)
            if time.time() - tlast > 60:
                tlast = time.time()
                print(f"  progress fmt {fmt} Es/N0 {esn0:+.2f}: frames {acc['frames']} err {acc['frame_err']} "
                      f"({time.time() - t0:.0f} s)", flush=True)
                prog(max(acc["frames"] / args.frames, acc["frame_err"] / args.max_err))
            if acc["frame_err"] >= args.max_err or acc["frames"] >= args.frames:
                break
        pool.terminate()
    acc["time_s"] = round(time.time() - t0, 1)
    return acc


def selfcheck(L=L_LIST):
    """3 frames at 30 dB per format (CRC-32 and one CRC-16), list size L: correct decode, CRC pass, re-encoding accept; the
    demapper equals rcs2.demap (max-log) on the same symbols."""
    import types
    t_all = time.time()
    rng = np.random.default_rng(0)
    for fmt in FMTS:
        for crc in ((32, 16) if fmt == "id3" else (32,)):
            t0 = time.time()
            c = get_code(fmt, crc, L)
            res = run_chunk((fmt, crc, 30.0, [0, FMTS[fmt]["tag"], 0], 3, ROLLOFF, reenc_thr(30.0, FMTS[fmt]["rho_key"]),
                             L, "pw", None))
            assert res["frame_err"] == 0 and res["crc_fail"] == 0 and res["reenc_pass"] == 3, (fmt, crc, res)
            print(f"  ok  {fmt:6s} crc {crc} L {L}: A {c.A} K {c.K} E {c.E} N {c.N} {c.mode:8s} n_sym {n_sym(fmt)} "
                  f"Eb/N0 = Es/N0 {10 * np.log10(n_sym(fmt) / c.A):+.3f} dB  MACs {c.macs(n_sym(fmt))['total']:.4g} "
                  f"| 3 frames {time.time() - t0:.2f} s", flush=True)
    try:                                                # demapper == rcs2.demap (if rcs2 imports; another editor)
        from fullsys import rcs2
        for fmt in ("id13", "id42b"):
            mod = FMTS[fmt]["mod"]
            m = 2 if mod == "qpsk" else 1
            y = rng.standard_normal((2, n_sym(fmt))) + 1j * rng.standard_normal((2, n_sym(fmt)))
            wf = types.SimpleNamespace(mod=mod, m=m, data_idx=np.arange(n_sym(fmt)),
                                       map=lambda b, n: ((1 - 2 * b[..., 0]) + 1j * (1 - 2 * b[..., 1])) / np.sqrt(2))
            e = rng.integers(0, 2, (2, FMTS[fmt]["E"]))
            if mod == "qpsk":
                assert np.allclose(modulate(e, fmt), wf.map(e.reshape(2, -1, 2), None))
            assert np.allclose(demap(y, fmt, 0.7), rcs2.demap(y, wf, 0.7)), fmt
            print(f"  ok  demap {fmt} == rcs2.demap ({mod})")
    except ImportError as ex:
        print(f"  skip rcs2.demap comparison ({ex})")
    print(f"SELFCHECK OK ({time.time() - t_all:.1f} s)")


def ga_check():
    """GA design checks (no channel, < 5 s): per format noiseless round trip of the GA code (CA-SCL-8, 2 frames),
    top-K overlap PW vs GA, no zero-mean (punctured-incapable) info position, union bound sum Q(sqrt(m / 2)) of the PW
    and GA info sets under the GA means at the design SNR; GA at E = N (N = 2048, K = 1040) vs PW, overlap > 90 %."""
    from fullsys import polar_design as pd
    t_all, fails = time.time(), []
    rng = np.random.default_rng(0)
    for fmt in FMTS:
        f, t0 = FMTS[fmt], time.time()
        cp, cg = get_code(fmt, 32), get_code(fmt, 32, design="ga")
        ga, ip, ig = cg.plan["ga"], cp.plan["info_pos"], cg.plan["info_pos"]
        d = rng.integers(0, 2, (2, f["A"]), dtype=np.uint8)
        dh, ok, _ = cg.decode(20.0 * (1 - 2 * cg.encode_rm(d).astype(np.float64)), return_info=True)
        rt = bool(ok.all() and np.array_equal(dh, d) and int(cg.code.frozen.sum()) == cg.N - cg.K
                  and not (cg.plan["pre"] & ~cg.code.frozen).any())
        zero = int(np.sum(ga["m_u"][ig] <= 0))
        ov = len(np.intersect1d(ip, ig)) / cg.K
        ub = (pd.union_bound(ga["m_u"], ip), pd.union_bound(ga["m_u"], ig))
        print(f"  {'ok  ' if rt and not zero else 'FAIL'} {fmt:6s} {cg.mode:8s} N {cg.N} K {cg.K} E {cg.E} bps "
              f"{bps(fmt)} design {DESIGN_SNR[fmt]:+.1f} dB: round trip {rt}, zero-mean info {zero} (zero-mean u "
              f"outside pre {int(np.sum((ga['m_u'] <= 0) & ~cg.plan['pre']))}), overlap PW/GA {ov:.4f} "
              f"({cg.K - len(np.intersect1d(ip, ig))} differ), union bound PW {ub[0]:.2e} GA {ub[1]:.2e} | "
              f"{time.time() - t0:.2f} s", flush=True)
        if not rt or zero:
            fails.append(fmt)
    for dsnr in (1.0, 2.0):                                     # no rate matching: GA vs PW at N = 2048, K = 1040
        pp = rm.rm_plan(1040, 2048)
        pg = rm.rm_plan(1040, 2048, design="ga", design_snr_db=dsnr, bps=2)
        ov = len(np.intersect1d(pp["info_pos"], pg["info_pos"])) / 1040
        print(f"  {'ok  ' if pg['mode'] == 'none' and ov > 0.9 else 'FAIL'} E = N = 2048, K = 1040, GA @ {dsnr:+.1f} "
              f"dB vs PW: overlap {ov:.4f}, union bound PW {pd.union_bound(pg['ga']['m_u'], pp['info_pos']):.2e} GA "
              f"{pd.union_bound(pg['ga']['m_u'], pg['info_pos']):.2e}")
        if not (pg["mode"] == "none" and ov > 0.9):
            fails.append(f"E=N {dsnr}")
    for fmt in ("id13", "id14s"):                               # the expected gain around the design SNR
        cp, cg, E = get_code(fmt, 32), get_code(fmt, 32, design="ga"), FMTS[fmt]["E"]
        row = []
        for x in DESIGN_SNR[fmt] + np.array([-0.4, -0.2, 0.0, 0.2, 0.4]):
            m_u = pd.ga_design(cg.N, E, cg.mode, cg.J, x, bps(fmt))["m_u"]
            row.append(f"{x:+.1f}: {pd.union_bound(m_u, cp.plan['info_pos']):.2e} / "
                       f"{pd.union_bound(m_u, cg.plan['info_pos']):.2e}")
        print(f"  union bound PW / GA(design {DESIGN_SNR[fmt]:+.1f} dB) {fmt}: " + "; ".join(row))
    print(f"GA CHECK {'OK' if not fails else 'FAILED ' + str(fails)} ({time.time() - t_all:.1f} s)")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fmt", choices=list(FMTS))
    ap.add_argument("--snrs", nargs="+", type=float, help="Es/N0 per transmitted symbol (dB)")
    ap.add_argument("--crc", type=int, default=32, choices=[32, 16], help="CRC length (payload A unchanged)")
    ap.add_argument("--frames", type=int, default=100000, help="max frames per point")
    ap.add_argument("--max-err", type=int, default=200, help="stop a point at this many frame errors")
    ap.add_argument("--stop-per", type=float, default=0.0, help="end the sweep after a point with PER below this "
                    "(0 = run every point)")
    ap.add_argument("--batch", type=int, default=200, help="frames per chunk (one task; = run_rcs2 for pairing)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--beta", type=float, default=ROLLOFF, help="RRC roll-off")
    ap.add_argument("--rho-key", default=None, help="blind_ber.RHO_N key for the re-encoding counter "
                    "(default per format; 'none' = rho_min only)")
    ap.add_argument("--part", help="results file fullsys/results/polar_genie_<part>.json")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--list", type=int, default=L_LIST, choices=[1, 2, 4, 8, 16, 32], help="CA-SCL list size L "
                    "(ops = decode_macs at this L)")
    ap.add_argument("--selfcheck", action="store_true", help="3 frames at 30 dB per format, assert correct decode")
    ap.add_argument("--design", default="pw", choices=["pw", "ga"], help="info set: pw (default, the PW order) or ga "
                    "(Gaussian approximation over the rate-matched channel, fullsys/polar_design.py)")
    ap.add_argument("--design-snr", type=float, default=None, help="GA design Es/N0 (dB); default DESIGN_SNR per "
                    "format (turbo PER-1e-3 Es/N0 + 0.3 dB)")
    ap.add_argument("--ga-check", action="store_true", help="GA design checks + union bounds (no channel, < 5 s)")
    ap.add_argument("--chan-intlv", action="store_true", help="QPSK: the blind system's channel interleaver "
                    "(blind_fmt chan) in modulate / demap (default off = the existing runs)")
    args = ap.parse_args()
    if args.selfcheck:
        return selfcheck(args.list)
    if args.ga_check:
        return ga_check()
    if args.design == "pw" and args.design_snr is not None:
        ap.error("--design-snr needs --design ga")
    if args.design == "ga" and args.design_snr is None and args.fmt:
        args.design_snr = DESIGN_SNR[args.fmt]
    if not (args.fmt and args.snrs and args.part):
        ap.error("give --fmt, --snrs and --part (or --selfcheck)")
    fmt, f = args.fmt, FMTS[args.fmt]
    key = f["rho_key"] if args.rho_key is None else (None if args.rho_key == "none" else args.rho_key)
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, f"polar_genie_{args.part}.json")
    prog_path = os.path.join(RESULTS, f"polar_genie_{args.part}.prog")
    if os.path.exists(path):
        sys.exit(f"{path} exists: use a new --part")
    code = get_code(fmt, args.crc, args.list, args.design, args.design_snr)
    ns = n_sym(fmt)
    ops = code.macs(ns)
    doc = dict(meta=dict(args=vars(args), fmt=fmt, spec={k: v for k, v in f.items()}, A=code.A, K=code.K, E=code.E,
                         N=code.N, mode=code.mode, crc=args.crc, L=args.list, design=args.design,
                         chan_intlv=chan_perm(fmt, args.chan_intlv) is not None,
                         design_snr_db=args.design_snr, bps=bps(fmt), n_sym=ns, rolloff=args.beta,
                         ebn0_offset=float(10 * np.log10(ns / code.A)), rho_key=key, rho_bins=RHO_BINS.tolist(),
                         frozen={k: v for k, v in code.frozen_info().items() if k.startswith("n_")},
                         chain="txrx_chain.transmit (SPS %d, span %d)" % (txrx_chain.SPS, txrx_chain.SPAN),
                         assumptions=ASSUMPTIONS + [f"List size L = {args.list} (CA-SCL-{args.list}; decode_macs at this L)."]),
               points=[])
    print(f"run_polar_genie {vars(args)} | A {code.A} K {code.K} E {code.E} N {code.N} {code.mode} n_sym {ns} L {args.list} "
          f"design {args.design}{'' if args.design_snr is None else f' @ {args.design_snr:+.2f} dB'}",
          flush=True)
    t_run, npt = time.time(), len(args.snrs)

    def prog(done):
        with open(prog_path, "w") as fh:
            fh.write(f"{done:.4f} {npt} {time.time() - t_run:.0f}\n")

    for pi, esn0 in enumerate(args.snrs):
        thr = reenc_thr(esn0, key)
        acc = run_point(fmt, esn0, args, thr, lambda x: prog(pi + min(x, 1.0)))
        n = acc["frames"]
        p = dict(fmt=fmt, esn0=esn0, ebn0_burst=round(float(esn0 + 10 * np.log10(ns / code.A)), 4), n_sym=ns,
                 k=code.A, K=code.K, E=code.E, N=code.N, mode=code.mode, crc=args.crc, L=args.list,
                 design=args.design, design_snr_db=args.design_snr, **acc,
                 per=acc["frame_err"] / n, per_reenc=acc["frame_err_reenc"] / n, reenc_thr=thr,
                 ops_per_frame=ops["total"], ops=ops, ref=f["ref"])
        doc["points"].append(p)
        with open(path + ".tmp", "w") as fh:
            json.dump(doc, fh, indent=1)
        os.replace(path + ".tmp", path)
        prog(pi + 1)
        print(f"SNR {esn0:+.2f} dB | fmt {fmt} crc {args.crc} L {args.list} | Eb/N0 burst {p['ebn0_burst']:+.2f} | frames {n} | "
              f"err {acc['frame_err']} (undetected {acc['undetected']}) | PER {p['per']:.3e} | reenc: PER "
              f"{p['per_reenc']:.3e}, rejected right {acc['reenc_reject_right']} wrong {acc['reenc_reject_wrong']} | "
              f"ops {ops['total'] / 1e6:.2f} M | {acc['time_s']:.0f} s", flush=True)
        if args.stop_per and p["per"] < args.stop_per:
            print(f"  PER {p['per']:.2e} < --stop-per {args.stop_per:g}: sweep ends", flush=True)
            prog(npt)
            break
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
