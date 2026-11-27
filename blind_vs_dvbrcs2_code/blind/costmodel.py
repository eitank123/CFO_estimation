"""
ONE op-counting convention for the full-system competitors' decoders (turbo_vde, turbo_db, polar_rm) and their
receiver front ends. Ops = real add / subtract / compare-select / sign / LUT read / multiply, each 1 op.

    max* (algo)     : max-log = compare-select (1); log-MAP = compare-select + LUT + add = 1 + MAXSTAR_EXTRA
    SISO step       : one trellis step of one constituent decoder (S states, binary input, m soft inputs per step)
        branch      : 2^m - 2 adds (the 2^m branch labels from m LLRs, half by sign symmetry)
        alpha, beta : each S x (2 adds + 1 max*) + (S - 1) normalisation subtracts
        LLR         : 2S branches x 2 adds + 2 (S - 1) max* + 1 subtract + 2 extrinsic subtracts
        scaling     : + 1 multiply when the extrinsic is scaled (max-log x 0.75)
    Turbo / iter.   : 2 SISOs x N_steps (k info steps + tail steps per SISO)
    Early stop      : + per iteration and info bit: APP decision (2 adds + 1 sign) + CRC (1 op / bit, LFSR);
                      without early stop one final APP decision (3 ops / bit), no per-iteration CRC
    Front end       : de-rotation CMUL 6 / sample (legacy 4) at the processed rate (chip rate when spread), despreading 2 / chip
                      (sf > 1: +-1 x complex chip accumulate), LLR scaling 1 / coded bit
    Critical path   : 32 cores (CORES). Turbo default = state-parallel: every trellis step stays serial, the
                      ops of a step spread over the cores + a reduction tree:
                      crit = 2 iters N_steps (ceil(ops_step / cores) + ceil(log2 S) + 3) [+ early stop per iter
                      ceil(4 k / cores) + ceil(log2 k)]; option model='window': `cores` sliding windows of
                      ceil(N_steps / cores) steps + W warm-up, each serial on one core:
                      crit = 2 iters (ceil(N_steps / cores) + W) ops_step (not the default).

Max-log, S = 8, m = 3, scaled: 6 + 31 + 31 + 49 + 1 = 118 ops / step; log-MAP (unscaled): 6 + 47 + 47 + 77 = 177.
`iters` may be an array (iterations actually used per block) everywhere.
Unit switch (env BLIND_MAC_UNIT, shared with blind_vp): "ops" (default) prices the front-end de-rotation at CMUL;
"legacy" keeps the 4 / sample of the runs before 2026-11-19 (everything else here is the same in both).
"""

import os

import numpy as np

MAC_UNIT = os.environ.get("BLIND_MAC_UNIT", "ops")             # "ops" | "legacy" (as blind_vp.MAC_UNIT)
assert MAC_UNIT in ("ops", "legacy"), f"BLIND_MAC_UNIT={MAC_UNIT!r}: 'ops' or 'legacy'"

MAXSTAR_EXTRA = 2              # log-MAP max* = compare-select + LUT read + add (Jacobian correction)
CORES = 32                     # the project's latency model ("MACs per core" over 32 cores)
REDUCTION = 3                  # crit: + ceil(log2 S) + 3 per trellis step (max* tree over states + normalisation)
APP_OPS = 3                    # per info bit: Ls + Le1 + Le2 (2 adds) + sign
CRC_OPS = 1                    # per info bit per CRC check (bit-serial LFSR, 1 op / bit)
WINDOW = 32                    # warm-up of the windowed (sliding-window) model


def maxstar_ops(algo):
    """Ops of one max* (max-log: 1 compare-select; log-MAP: + LUT + add)."""
    return 1 + (MAXSTAR_EXTRA if algo == "logmap" else 0)


def siso_step_ops(algo="maxlog", n_states=8, n_soft=3, scaled=None):
    """Breakdown dict + 'total' of one SISO trellis step (see module doc). scaled: default True for max-log."""
    S, ms = n_states, maxstar_ops(algo)
    scaled = (algo == "maxlog") if scaled is None else scaled
    d = dict(branch=2 ** n_soft - 2,
             alpha=S * (2 + ms) + (S - 1),
             beta=S * (2 + ms) + (S - 1),
             llr=2 * S * 2 + 2 * (S - 1) * ms + 1 + 2,
             scale=1 if scaled else 0)
    d["total"] = sum(d.values())
    return d


def turbo_ops(k, iters, algo="maxlog", n_states=8, n_soft=3, tail_steps=3, early=False, scaled=None):
    """Total ops of a turbo decode of one block (k info bits, tail_steps per SISO; 0 = unterminated)."""
    it = np.asarray(iters)
    step = siso_step_ops(algo, n_states, n_soft, scaled)["total"]
    dec = it * 2 * (k + tail_steps) * step
    if early:
        return dec + it * k * (APP_OPS + CRC_OPS)
    return dec + k * APP_OPS


def crit_turbo(k, iters, algo="maxlog", n_states=8, n_soft=3, tail_steps=3, early=False, scaled=None,
               cores=CORES, model="state", window=WINDOW):
    """32-core critical path (serial op steps) of one turbo decode; model 'state' (default) or 'window'."""
    it = np.asarray(iters)
    step = siso_step_ops(algo, n_states, n_soft, scaled)["total"]
    N = k + tail_steps
    if model == "state":
        dec = 2 * it * N * (int(np.ceil(step / cores)) + int(np.ceil(np.log2(n_states))) + REDUCTION)
    elif model == "window":
        dec = 2 * it * (int(np.ceil(N / cores)) + window) * step
    else:
        raise ValueError(model)
    per_dec = int(np.ceil(k * (APP_OPS + CRC_OPS) / cores)) + int(np.ceil(np.log2(max(k, 2))))   # + CRC/OR tree
    if early:
        return dec + it * per_dec
    return dec + int(np.ceil(k * APP_OPS / cores))


FFT_OPS = 5                    # complex radix-2 FFT: ~5 n log2 n real ops (n/2 log2 n butterflies x 10)
CMUL, CMAC = 6, 8              # complex multiply (4 mul + 2 add); complex multiply-accumulate
DEROT = CMUL if MAC_UNIT == "ops" else 4                       # front-end de-rotation per sample (legacy 4)


def frontend_ops(n_sym, sf=1, E=0, mod="bpsk", derot=True):
    """
    Receiver front end per burst: de-rotation DEROT (CMUL 6; legacy 4) per processed sample (n_sym sf samples; derot
    False: none, the DA correction de-rotates), despreading 2 per chip if sf > 1, LLR scaling 1 per coded bit (E channel
    bits). mod is accepted for the API (BPSK / QPSK / pi/4-QPSK all cost 1 op per LLR; the pi/4 de-rotation of odd
    symbols rides on the de-rotation multiply).
    """
    if mod not in ("bpsk", "qpsk", "pi4qpsk"):
        raise ValueError(f"frontend_ops: no LLR cost defined for {mod}")
    samples = n_sym * sf
    return (DEROT * samples if derot else 0) + (2 * samples if sf > 1 else 0) + E


def frontend_crit(n_sym, sf=1, E=0, mod="bpsk", cores=CORES, derot=True):
    """Critical path of the front end: element-wise work over the cores + a log2(sf) despreading adder tree."""
    par = int(np.ceil(frontend_ops(n_sym, sf, E, mod, derot) / cores))
    return par + (int(np.ceil(np.log2(sf))) if sf > 1 else 0)


# ---- data-aided CFO / phase synchroniser (fullsys/da_sync.py), the same op units --------------------------------


def pow2_at_least(n):
    """Smallest power of 2 >= n."""
    return 1 << int(np.ceil(np.log2(max(n, 1))))


def da_ops(Nk, n_data, nfft, n_win, refine=1, newton=3):
    """
    Ops of the DA CFO / phase / N0 estimator per burst (Nk known symbols, n_data symbols corrected, FFT nfft, n_win
    bins searched, `refine` periodogram maxima refined with `newton` Newton steps each). Phasors e^{-j 2 pi f n} by
    recursion (1 complex multiply per sample; the per-core seeds are negligible), no exp.
        strip    2 Nk        z = r conj(s), s a constellation point: sign changes / I-Q swaps + adds
        fft      FFT_OPS nfft log2 nfft
        search   5 n_win     |X|^2 (2 mul + 1 add) + local-maximum / argmax compares (2)
        refine   per maximum: parabolic 10 + newton x (22 Nk + 10) + Lambda 14 Nk
                 (Newton per symbol: phasor 6, z e 6, A += 2, A' += t(.) 4, A'' += t(.) 4; Lambda: phasor 6 + CMAC 8)
        gain_n0  17 Nk + 20  residual z - g e (phasor 6, g e 6, subtract 2, |.|^2 3); g from Lambda's sum
        correct  12 n_data   y = r e^{-j 2 pi f n} / g (phasor recursion seeded with 1/g: 6 + 6)
    Returns dict(first = strip + fft + search + refine + gain_n0 + correct, per_cand = gain_n0 + correct (each
    further candidate tried), refine_one (refining one more maximum), breakdown)."""
    one = 10 + newton * (22 * Nk + 10) + 14 * Nk
    b = dict(strip=2 * Nk, fft=FFT_OPS * nfft * int(np.log2(nfft)), search=5 * n_win + refine * refine,
             refine=refine * one, gain_n0=17 * Nk + 20, correct=12 * n_data)
    return dict(first=float(sum(b.values())), per_cand=float(b["gain_n0"] + b["correct"]), refine_one=float(one),
                breakdown={k: float(v) for k, v in b.items()})


def nda4_ops(L, Nk, n_data, nfft, n_win, newton=3, da_newton=0):
    """
    (2026-11-23, run_fullsys_da --nda) Ops of the 4th-power NDA CFO estimator of a QPSK burst (da_sync.nda4_estimate)
    + the DA phase / gain / N0 on the Nk known symbols at its f, per burst of L symbols:
        pow      2 CMUL L      w = r^4 (two complex squarings, as blind_vp.pow_macs)
        fft      FFT_OPS nfft log2 nfft
        search   5 n_win       |X|^2 + argmax compares
        refine   10 + newton (22 L + 10)        parabolic + Newton on |sum w e^{-j 2 pi nu n}|^2 (as da_ops, over L)
        strip    2 Nk
        da_newton  da_newton (22 Nk + 10)       (pow4da) Newton on the DA Lambda from the NDA f
        gain_n0  14 Nk + 17 Nk + 20             Lambda sum -> g, residual N0 (as da_ops refine's Lambda + gain_n0)
        correct  12 n_data
    Returns da_ops' dict (per_cand / refine_one as da_ops: a further candidate is not defined, 0 refine_one)."""
    b = dict(pow=2 * CMUL * L, fft=FFT_OPS * nfft * int(np.log2(nfft)), search=5 * n_win,
             refine=10 + newton * (22 * L + 10), strip=2 * Nk, da_newton=da_newton * (22 * Nk + 10),
             gain_n0=31 * Nk + 20, correct=12 * n_data)
    return dict(first=float(sum(b.values())), per_cand=float(b["gain_n0"] + b["correct"]), refine_one=0.0,
                breakdown={k: float(v) for k, v in b.items()})


def nda4_crit(L, Nk, n_data, nfft, n_win, newton=3, da_newton=0, cores=CORES):
    """32-core critical path of nda4_ops (the da_crit conventions: element-wise work over the cores, + ceil(log2
    cores) per reduction, + log2 nfft FFT stage syncs)."""
    red = int(np.ceil(np.log2(cores)))
    c = lambda x: int(np.ceil(x / cores))
    b = dict(pow=c(2 * CMUL * L), fft=c(FFT_OPS * nfft * int(np.log2(nfft))) + int(np.log2(nfft)),
             search=c(5 * n_win) + red, refine=10 + newton * (c(22 * L) + 3 * red + 10), strip=c(2 * Nk),
             da_newton=da_newton * (c(22 * Nk) + 3 * red + 10), gain_n0=c(31 * Nk) + 2 * red + 20,
             correct=c(12 * n_data))
    return dict(first=float(sum(b.values())), per_cand=float(b["gain_n0"] + b["correct"]), refine_one=0.0,
                breakdown={k: float(v) for k, v in b.items()})


def da_crit(Nk, n_data, nfft, n_win, refine=1, newton=3, cores=CORES):
    """32-core critical path of da_ops: element-wise work split over the cores, + ceil(log2 cores) per reduction
    (sums, argmax), + log2 nfft FFT stage syncs; the refined maxima one after another (as da_ops' keys)."""
    red = int(np.ceil(np.log2(cores)))
    c = lambda x: int(np.ceil(x / cores))
    one = 10 + newton * (c(22 * Nk) + 3 * red + 10) + c(14 * Nk) + red
    b = dict(strip=c(2 * Nk), fft=c(FFT_OPS * nfft * int(np.log2(nfft))) + int(np.log2(nfft)),
             search=c(5 * n_win) + red + refine * refine, refine=refine * one, gain_n0=c(17 * Nk) + red + 20,
             correct=c(12 * n_data))
    return dict(first=float(sum(b.values())), per_cand=float(b["gain_n0"] + b["correct"]), refine_one=float(one),
                breakdown={k: float(v) for k, v in b.items()})
