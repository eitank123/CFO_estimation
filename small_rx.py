"""Receiver of the small-CFO study (|f| <= bc.MAX_CFO, BLIND_STUDY=small_cfo): no spectral, cyclic or autocorrelation
statistics. With |f| <= 0.03 the 4th-power line 4f stays inside its unambiguous +-1/2, so the 4th-power FFT alone gives
the CFO.

    1. fast path: 4th-power FFT peak inside |4f| <= 4 MAX_CFO (24 pilots: the top peaks graded by the pilots' coherent
       sum), parabolic refinement, pre-MF de-rotation at it, the pi/2 branch by the metric (blind) or the pilots, one
       CA-SCL decode
    2. search, for the packets the fast path does not deliver: every cell of the whole small grid x phases scored with
       the list-1 Fast-SSC path metric, optionally with checkpoints along the decode (spec "ck": fractions of the
       codeword): at each checkpoint the robust z of the cells still alive (median / MAD among them); cells with
       z <= tau are dropped (the best kmin always survive); "win": a cell with z > win at a checkpoint ends the CFO
       search: it is decoded at once, and on a CRC pass the other cells are never finished
    3. the survivors in z order (z > z0) refined (+-k/2 STEP x phase sub-offsets) and decoded, then the best-metric
       cells regardless of z (final)
    acceptance: CRC + the normalised re-encoding check rho_n (+ the pilot check for pilots)
MACs per packet are counted per block as it runs; a cell dropped at a checkpoint costs only the part decoded."""
import numpy as np

import blind_cfo as bc
import blind_fast as bf
import blind_vp as vp
import fastscl
from polar import polar_transform

DEFAULT = dict(s0_snr=-99.0, nph=None, z0=4.0, T=2, ncand=4, final=32, rho_n=None, pilots=None, pc_sigmas=5.0,
               fast_peaks=16, fast_ratio=0.7, ck=None, tau=0.0, kmin=16, win=None, rate=None,
               premf_dec=False, ca_retry=False, prior=(), pre_keep=None, sub3=False, coarse=False, pilot_score=0.0,
               final_post=0, fine_last=0, T_fine=6, nn=None, nn_keep=None, nn_min=48, nn_score=0.0, dump=None, dump_pm=None,
               ck_nn=None, ck_keep=1e-3, ck_min=8, ck_win=None, cost="linear", beam=None, keep_early=None,
               race_phase=None, first_k=None, blind_peaks=None, blind_ratio=0.85,
               join_side=False, join_nph=None, join_top=None,
               phase_keep=None, stride=2, top_k=None, batch=None, cores=None, joint=None,
               truth=None, kstep=None, reencode=True,
               snr_err=0.0, re_margin=0.0,
               truth_f=None, truth_th=None, s3dump=None, s3dump_top=6,   # (measurement) BLIND_IMPLEMENTATION/testing/: Stage 3 dump
               s3_dd=False,   # experiment R1: Stage 3 refinement by the re-encoded SC codeword (code_aided) instead of
                              # the CFO-offset x phase grid of list-1 metric passes (False = the baseline)
               win_spec=None,   # action 2: at a checkpoint where the win test does not fire, the best untried cell with
                                # z > win_spec is decoded speculatively once (T = 1, no CA retry; re-encoding guards)
               old_acct=False,  # (accounting) True: the pre-2026-11-13 count, a cell joining after a phase pruning
                                # (phase_keep / race_phase / beam) charged its pruned phases from 0; False: its
                                # pre-pruning phases up to the pruning checkpoint (decisions identical)
               q_fix=False,   # True: a candidate's phase th + qs[qb] pi/4 (the phase offset its metric was scored at);
                              # False (baseline): th + qb pi/4 (qb the index: with nph = 2, qs = [0, 2], index 1
                              # gives pi/4 instead of pi/2, on the rounding edge of the pi/2 branch)
               equiv=False,   # phase-equivariant receiver (needs BLIND_NOINT=1 and a bc.PiCode4 code): the pi/2
                              # branches have the same list-1 metric and PiCode4 decodes any of them, so the cell phases
                              # are kept mod pi/2 (nph 2 -> 1, 4 -> 2; phase_keep / beam counts halved), the fast path
                              # decodes th0 without scoring both branches, final_post only b = 0; each decode is charged
                              # the un-rotation check of its list paths (PiCode4.rot_macs; st macs_rot)
               eqrb=False,    # with equiv: the rotation-bit code (Geiselhart et al. 2023; needs BLIND_NOINT=1,
                              # BLIND_ROTBITS=1 and a bc.PiCodeRB code): each list path reads its rotation from
                              # (u_{N-2}, u_{N-1}), is un-rotated once and gets one CRC test (PiCodeRB.rot_macs)
               cap_core=None,  # hard cap on a packet's MACs per core (crit_par): a packet whose search needs more
                               # is stopped at the cap and declared "no packet" (an erasure; emulated after the run:
                               # the search stops at its first accept, so decisions before the cap are identical);
                               # every cost counter of a capped packet is scaled to end at the cap (None = no cap)
               spec_rho=None,  # speculative decodes (win_spec) accepted only if rho > spec_rho x the re-encoding
                               # threshold (None = the threshold itself, the baseline)
               spec_snr=None,  # win_spec only below this SNR (dB), a number or {code rate: dB}; a missing rate or
                               # None = win_spec at every SNR (the spec11 sweep: it saves MACs only in the waterfall)
               nn_b=None,     # retry gate (BLIND_IMPLEMENTATION/testing/nn_b_export.py): (gate json, frac): the CA
                              # retry of a failed main decode runs only when the logistic score of its decoder-list /
                              # LLR features >= the json's thr[frac] for the CODE rate (missing rate: no gate)
               pns=None,      # phase-noise tracking retry (testing/results/expected_pns.md; None = off, the baseline):
                              # dict(q=None, iters=1, soft=True, spec=False, max_calls=None, rho="corr") (PNS_DEF); a
                              # CA-SCL-8 decode (main, CA retry, joint) failing CRC or rho -> list-weighted re-encoded
                              # symbols xbar (softmax(-PM) over the paths; soft=False the best path), z = y xbar*, RTS
                              # smoother of the phase (random walk, q per symbol; q None = 2 pi pns_lw) -> y e^{-j phi}
                              # -> one more CA-SCL-8 decode per iteration, accepted by CRC + the re-encoding check (rho
                              # "corr": on the de-rotated samples, "raw": on the original); never after an accepted
                              # decode; spec: also after the speculative decodes; max_calls: per packet (None = all)
               pns_lw=None,   # the linewidth x Ts the pns smoother assumes (None: BLIND_PN if > 0, else 1e-4)
               rhos=None,     # segment re-encoding check: rho_s (rho_seg, segments of rhos symbols, e.g. 64) replaces
               rhos_k=1.0,    # rho, threshold rhos_k x the rho threshold (None = rho, the baseline); TODO calibrate
               rhos_log=None,  # (measurement) segment lengths (e.g. (32, 64, 128)): every CRC pass -> st["rhos_rows"]
                               # [rho, rho_s per length, threshold, right, tag, origin 0 main / 1 retry / 2 pns, snr]
               dec_dump=None, dec_acc=None, dec_id=None,   # (measurement) BLIND_IMPLEMENTATION/testing/ decode dump:
                                # dec_dump a directory (None = off): one row per decode attempt + one per packet
                                # (dec_save); dec_acc / dec_id (set by blind_ber.simulate): the chunk's accumulator
                                # and (chunk_seed, index of the batch's first packet in the chunk)
               ref_diag=None,  # (measurement) D0 of testing/results/expected_ref.md, a directory (None = off): every
                               # candidate cell refined in Stage 3 (refine2 / refine_joint) -> one row (truth residual,
                               # the grid's metrics / choices / outcome, the 4th-power Newton, checkpoint-PM / grid
                               # parabola and DD Newton estimates, their MACs) + one row per packet, in the chunk's
                               # dec_acc (groups r / q; rd_<chunk>.npz) and rd_* counters; decisions and MACs unchanged
               fz_diag=None,  # (measurement) F5 of testing/results/expected_f3f5.md, a directory (None = off): every
                              # CA-SCL decode the receiver runs (main, CA retry, joint, pns) -> one row with every list
                              # path's frozen-only metrics at FZ_Q of the frozen set (polar.PolarCode fz_q), the outcome
                              # (right / CRC-pass wrong / failed), the true-cell label and its decode round, in the
                              # chunk's dec_acc (groups f: CA-SCL-8, j: joint lists, g: packets; fz_<chunk>.npz);
                              # decisions, MACs and counters unchanged
               lmarg=None,    # F3 online (testing/results/expected_online_f3dd.md A; None = off, the baseline): L_e;
                              # the candidates after the last checkpoint (z > z0, then the best `final`) ordered by the
                              # list-marginalised metric -log sum_l exp(-PM_l) of a Fast-SSC list decode with L_e paths
                              # (fastscl.FastSCL) of every surviving (cell, phase) hypothesis up to lmarg_ck, z recomputed
                              # from it over the survivors, the cell's phase = its best by it; instead of the list-1 PM
                              # (non-joint receivers: R = 1/10, 0.15); rescue (final_post, fine_last) unchanged
               lmarg_ck=None,  # lmarg's codeword fraction (None = the last z-test checkpoint, 3/4 at R = 1/10, 0.15)
               lmarg_lazy=False,  # lmarg lazily: the first s2cand candidate in list-1 order is decoded first; only if it
                                  # fails (or no cell has z > z0) the survivors get the list decode, the rest of s2cand
                                  # (at most ncand - 1 more, by the lmarg z) and final32 use it (st lm_lazy_runs)
               ddref=False,   # TODO 3 online (expected_online_f3dd.md B; False = the baseline): a candidate cell's
                              # refinement (refine2 on the roffs grid, non-joint receivers) starts with the DD Newton of
                              # its list-1 SC codeword at the cell centre (bf.code_aided, 2 steps) -> f_dd x (theta_dd +
                              # sub) scored (list-1) and the best T decoded; the cells none of them accepted fall back
                              # to the grid refinement (st ddref_cells / ddref_hit / ddref_fallback / _fallback_hit,
                              # ddref_jump_<b>: |f_dd - f_cell| in 0.5-STEP bins); the centre pass is charged only when
                              # the search had not decoded that hypothesis to full length (its SC decisions: a by-product)
               ddref_tags=None,   # ddref only for decodes of these origins (e.g. ("win", "spec", "s2cand")); None = all
               ddref_T=None,      # ddref: DD hypotheses decoded per cell, min(T, ddref_T) (None = the call's T)
               fzstop=None,   # F5 online (expected_f3f5.md; None = off, the baseline): (q, t): every CA-SCL decode (main,
                              # CA retry, pns, joint list) is stopped at the first node boundary with >= ceil(q F) frozen
                              # leaves when min over its alive paths of psn > t (polar.PolarCode fz_stop) and treated as
                              # a CRC failure; charged the work up to there (fz_share: the fz_profile tree share), per
                              # core a 4-decode round shortens only when all its decodes stop (d4a); st fz_checks /
                              # fz_stops / fz_stops_right (truth, log only) / macs_fz_saved / fzs_pos_<leaf> / fzs_<kind>;
                              # or {code rate: (q, t)} (e.g. {"0.15": (0.9, 0.763)}; a missing rate = off). Not with
                              # pns, the retry gate (nn_b) or s3_dd (not modelled)
               nopi=False,    # (fullsys/blind_fmt.py, shortened codes: no all-ones codeword, a CA-SCL without PiCode's pi
                              # complement) the phase is needed mod 2 pi: the cells' offsets qs and qs + 4 (pi/4 units),
                              # 4 pi/2 branches in the fast path and the rescue (final_post), join hand-off mod 2 pi
               bpsk_sq=False,  # (blind_fmt, (pi/2-)BPSK as virtual QPSK b (1 + j) / sqrt2) the fast path's line and the
                               # cells' phases from r^2 (line at 2f, phase mod pi) instead of -r^4; the pi/2 branch (LLR 0
                               # for BPSK) dropped: offsets 2 qs[qs < 2] (nph 2 -> 1, 4 -> 2), no branch scoring in the
                               # fast path, final_post b = 0, phase_keep halved, refinement phases from the square
               ck_useful=False,  # (blind_fmt) checkpoint fractions (ck, ck_nn CK_FR) counted on the u positions not
                                 # pre-frozen by rate matching (bc.FMT.pre: the rm / extra block carries no CFO
                                 # information) instead of the codeword; the cost share follows the actual leaf ends
               ck_nn_name=None,  # (fullsys/ck_nn_fs.py) the checkpoint NN's model prefix: models f"{ck_nn_name}_c{c}"
                                 # (e.g. "ck_nn_fs_id13", trained on the format's own packets); None = the baseline
                                 # f"ck_nn_{mode}_c{c}" (mode blind / pilots)
               ck_charge_all=False,  # (accounting) the checkpoint NN's features (robust z over EVERY cell, softmax and
                                     # cumulative-mass shortlist over every cell) need every cell's partial metric up to
                                     # CK_FR[ck_nn]: True charges the cells not paid up to there (phase + de-rotation, the
                                     # metric of their phases) when the search reaches the NN, in the same stage as the
                                     # alive cells (macs, crit_par; later rounds do not re-charge them; st ck_extra_cells /
                                     # macs_ck_extra); False (baseline): only the round's alive cells (first_k, batch:
                                     # optimistic). Decisions identical (cap_core, applied after the run, sees the cost)
               stage_acc=None,  # (measurement) list: each call appends per-packet reach (B, 5) (stages entered: 1 fast,
                                # 2 grid search, 3 final, 4 final_post, 5 fine_last), cost (B, 6, 3) [macs, crit_par_d4a,
                                # crit_par_h_d4a] at the end of each stage reached (nan if not; 5 = the end, after
                                # cap_core), stage, passed, right, n_hyp (metric hypotheses started); decisions unchanged
               mac_acc=None,  # (measurement) per-packet MACs log (None = off; blind_ber.simulate sets a list unless
                              # BLIND_NO_MACLOG=1): each call appends one dict of per-packet arrays, the costs as the
                              # counters below sum them (c_hd4a = crit_par_h_d4a, c_d4a = crit_par_d4a, cpar = crit_par,
                              # macs; float32, after cap_core) + passed / right; decisions, MACs and counters unchanged
               fulllog=None)  # (measurement) full-search log for the offline joint tuner (fullsys/joint_tune_fs.py;
                              # None = off): True or dict(FL_DEF keys); needs truth / truth_f and dec_acc (chunk groups
                              # flp: per search packet the list-1 PMs of every cell x phase at the checkpoints cks + fr,
                              # the cost counters at its search start, the checkpoint NN's log P(cell), the spectral
                              # prior, the true cell; flh: one row per decode attempt of a (cell, phase offset, kind)
                              # hypothesis, the search's own (src 0) and, outside every counter, the refine2 of the
                              # cells within `near` of the true cell at each phase some checkpoint's best-phase choice
                              # gives (src 1; kind 1 the fine_last grid within `fine`); flb: every packet's result and
                              # costs; flc: the call's settings and cost constants, fl_save); decisions, MACs and
                              # counters unchanged. Non-joint receivers without coarse / beam / race_phase / lmarg /
                              # ddref / s3_dd / pns / pilots / win_spec / fzstop / cap_core / nn / pre_keep / top_k /
                              # equiv / rhos (asserted)
FZ_Q = (0.25, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)   # (measurement, fz_diag) checkpoints: fractions of the frozen set in
                                              # decoding order (denser in the information-bearing second half)
FZ_L = {"f": 8, "j": 16}       # (measurement, fz_diag) list paths per row, padded: CA-SCL-8 rows / joint-list rows
FL_DEF = dict(near=1, fine=0, fr=(0.25, 0.375, 0.5, 0.625, 0.75), retry_all=False, all_attempts=False)
# (measurement, fulllog) near: cells within near of the true cell get their standard refine2 logged (src 1); fine: the
# true cell +- fine its fine_last refine2 when no standard attempt of it accepted (None = off); fr: checkpoint fractions
# logged besides cks (phase_keep / ck variants); retry_all: the CA retry also after a main CRC pass, all_attempts: every
# attempt after an accept (both only for an exact fzstop replay of the side rows)
PER_RATE = ("ck", "tau", "kmin", "win", "win_spec", "pre_keep", "pilot_score", "coarse", "nn", "nn_keep", "nn_min", "nn_score", "ck_nn", "ck_keep", "ck_win", "beam", "keep_early", "race_phase", "first_k", "blind_peaks", "phase_keep", "top_k", "batch", "kstep")
SPLIT = 64                     # rate-0 nodes reported in 64-bit chunks (checkpoints inside a long frozen block)          # these may be given per rate ({"1/10": ..., ...})


def leaves(plan, lo, hi, out, split=None):
    if plan[0] == "R0" and split and hi - lo > split:
        out += [(c, c + split) for c in range(lo, hi, split)]
        return out
    if plan[0] != "N":
        out.append((lo, hi))
        return out
    mid = (lo + hi) // 2
    leaves(plan[1], lo, mid, out, split)
    leaves(plan[2], mid, hi, out, split)
    return out


def leaf_cost(plan, n, lo, acc, out, split=None):
    """Fast-SSC cost in decoding order (as blind_vp.metric_macs: 2n per f / g at a node, n per rate-0 / rate-1 leaf,
    2n per REP / SPC): appends (leaf end, cumulative cost) for each leaf (rate-0 nodes in split-bit chunks)."""
    if plan[0] == "N":
        acc[0] += n
        leaf_cost(plan[1], n // 2, lo, acc, out, split)
        acc[0] += n
        leaf_cost(plan[2], n // 2, lo + n // 2, acc, out, split)
        return out
    c = 2 * n if plan[0] in ("REP", "SPC") else n
    if plan[0] == "R0" and split and n > split:
        for e in range(lo + split, lo + n + 1, split):
            acc[0] += c * split / n
            out.append((e, acc[0]))
        return out
    acc[0] += c
    out.append((lo + n, acc[0]))
    return out


_SHARE = {}


def cost_share(plan, fr):
    """Share of a full Fast-SSC metric pass spent once the leaves up to fraction fr (array) of the codeword are
    decoded (at R = 1/10 the first half, mostly frozen, is 36 % of the cost, not 50 %)."""
    key = id(plan)
    if key not in _SHARE:
        lc = np.array(leaf_cost(plan, bc.N_BITS, 0, [0.0], [], SPLIT))
        _SHARE[key] = (lc[:, 0], lc[:, 1] / lc[-1, 1])
    e, s = _SHARE[key]
    i = np.searchsorted(e, np.asarray(fr) * bc.N_BITS, side="right") - 1
    return np.where(i >= 0, s[np.maximum(i, 0)], 0.0)


_FZP = {}


def fz_share(frozen, pos):
    """(fzstop) share of a CA-SCL decode's work done once the leaves [0, pos) are decided (pos at a leaf / rate-0 node
    end, else the last one before it), the decoder's own order (polar.PolarCode, Fast-SSCL rate-0 nodes): per path f
    and g n/2 each at an internal node, n at a rate-0 node, 1 at a frozen leaf, 2 at an information leaf (as
    BLIND_IMPLEMENTATION/testing/fz_profile.py profile / share)."""
    key = np.asarray(frozen, bool).tobytes()
    if key not in _FZP:
        fz, out, acc = np.asarray(frozen, bool), [], [0.0]

        def walk(lo, hi):
            n = hi - lo
            if n == 1 or fz[lo:hi].all():
                acc[0] += n if fz[lo:hi].all() else 2
                out.append((hi, acc[0]))
                return
            acc[0] += n / 2
            walk(lo, lo + n // 2)
            acc[0] += n / 2
            walk(lo + n // 2, hi)

        walk(0, len(fz))
        a = np.array(out, float)
        _FZP[key] = (np.r_[0, a[:, 0]].astype(int), np.r_[0, a[:, 1] / a[-1, 1]])
    P, T = _FZP[key]
    return T[np.searchsorted(P, np.asarray(pos), side="right") - 1]


NF, NH, KS = 10, 12, 3          # cell-prior NN (small_prior_nn.py): features per cell, hidden channels, conv width


def nn_features(r, rx, f0, g, k, snr, pl=None):
    """Per-cell features (B, G, NF) for the cell-prior NN, from what the receiver has before the search:
    the normalised 4th-power periodogram (max over the cell's bins) of the whole packet and of each half, the phase
    agreement of the halves' 4th-power line at the cell, the periodogram's peak-to-mean, the distance to the fast-path
    estimate, the pre-MF lag-4 autocorrelation estimate, the pilots' log-likelihood (0 blind), SNR, grid step.
    Returns the features and their MACs per packet (beyond the receiver's own 4th-power FFT)."""
    B, nf = len(r), bc.NFFT4
    y4 = -(r ** 4)
    step = k * bc.STEP
    nu = (4 * g) % 1.0
    w = int(np.ceil(4 * step * nf)) + 1
    b0 = np.floor((nu - 2 * step) * nf).astype(int)
    bins = (b0[:, None] + np.arange(w)[None]) % nf
    bc_ = np.round(nu * nf).astype(int) % nf

    def per(y):
        Yc = np.fft.fft(y, nf, axis=1)
        Y = np.abs(Yc) ** 2
        Y /= Y.mean(1, keepdims=True)
        return Y[:, bins].max(2), Yc[:, bc_]

    h = bc.N_SYM // 2
    S, _ = per(y4)
    Sa, Ya = per(np.concatenate([y4[:, :h], np.zeros_like(y4[:, h:])], 1))
    Sb, Yb = per(np.concatenate([np.zeros_like(y4[:, :h]), y4[:, h:]], 1))
    fa = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
    x = np.empty((B, len(g), NF), np.float32)
    x[..., 0] = np.clip(S, 0, 50) / 10
    x[..., 1] = np.clip(Sa, 0, 50) / 10
    x[..., 2] = np.clip(Sb, 0, 50) / 10
    x[..., 3] = (Ya * np.conj(Yb)).real / (np.abs(Ya) * np.abs(Yb) + 1e-12)
    x[..., 4] = np.log(S.max(1, keepdims=True)) / 5
    x[..., 5] = np.clip((g[None] - f0[:, None]) / step / 20, -3, 3)
    x[..., 6] = np.clip((g[None] - fa[:, None]) / bc.MAX_CFO, -3, 3)
    x[..., 7] = 0.0 if pl is None else np.clip(pl - pl.max(1, keepdims=True), -50, 0) / 10
    x[..., 8] = snr / 10.0
    x[..., 9] = k / 4.0
    m = 2 * (2 * 4 * bc.N_SYM + vp.fft_macs(nf)) + vp.MAC["cmul"] * rx.shape[1] + 12 * len(g)
    return x, m


def nn_macs(G):
    return G * (KS * NF * NH + KS * NH * NH + NH)


_NN = {}


def nn_logp(mode, x, name=None, skip=0):
    """log P(cell) (B, G): conv(KS) -> FiLM(SNR) -> ReLU -> conv(KS) -> FiLM(SNR) -> ReLU -> 1x1, plus
    (w0 + w1 SNR) x feature skip (the periodogram); log-softmax over cells. FiLM: each hidden channel x (1 + a SNR)
    + b SNR."""
    name = name or f"prior_nn_{mode}"
    if name not in _NN:
        z = np.load(bc.path("models", name + ".npz"))
        _NN[name] = {q: z[q] for q in z.files}
    W = _NN[name]

    def conv(h, w, b):                                        # w (KS, C_in, C_out), 'same' padding
        G = h.shape[1]
        hp = np.pad(h, ((0, 0), (KS // 2, KS // 2), (0, 0)))
        return sum(hp[:, j:j + G] @ w[j] for j in range(KS)) + b

    s = x[:, :1, 8:9]                                        # SNR / 10 (B, 1, 1)
    h = np.maximum(conv(x, W["c1"], W["b1"]) * (1 + W["a1"] * s) + W["f1"] * s, 0)
    h = np.maximum(conv(h, W["c2"], W["b2"]) * (1 + W["a2"] * s) + W["f2"] * s, 0)
    lg = (h @ W["c3"])[..., 0] + W["b3"][0] + (W["w0"][0] + W["w1"][0] * s[..., 0]) * x[..., skip]
    lg = lg - lg.max(1, keepdims=True)
    return lg - np.log(np.exp(lg).sum(1, keepdims=True))


CK_FR = (1 / 16, 1 / 8, 3 / 16, 1 / 4, 5 / 16, 3 / 8, 1 / 2, 3 / 4, 1.0)   # checkpoint NN (small_ck_nn.py): fractions of the codeword
NF_CK = NF + 1 + 2 * len(CK_FR) + 1


def ck_macs(G):
    return G * (KS * NF_CK * NH + KS * NH * NH + NH)


def ck_logp(mode, c, x, name=None):
    """The checkpoint NN's log P(cell) at CK_FR[c] (skip = the z-test feature); name: the model prefix (None =
    ck_nn_<mode>)."""
    return nn_logp(mode, x, f"{name or 'ck_nn_' + mode}_c{c}", NF)


def _rzb(x, axis=1):
    """Robust z along the cells (higher = better metric), batched."""
    med = np.median(x, axis, keepdims=True)
    return (med - x) / (1.4826 * np.median(np.abs(x - med), axis, keepdims=True) + 1e-6)


def ck_features(x, pm, c):
    """Per-cell features (B, G, NF_CK) of the checkpoint NN at checkpoint CK_FR[c], from the cell-prior features x
    (B, G, NF) and the partial path metrics pm (B, G, phases, len(CK_FR), 2) [total, rate-0 nodes only]: the cells'
    robust z at CK_FR[c] (the z-test; also the skip input), the z trajectories of the total and of the rate-0 part up
    to CK_FR[c] for the cell's best phase there (0 beyond), the phase contrast (mean - best phase) at CK_FR[c]."""
    tot = pm[..., 0]
    q = tot[..., c].argmin(2)[..., None, None]
    T = np.take_along_axis(tot, q, 2)[:, :, 0]
    R = np.take_along_axis(pm[..., 1], q, 2)[:, :, 0]
    zT, zR = np.clip(_rzb(T), -10, 30) / 5, np.clip(_rzb(R), -10, 30) / 5
    zT[..., c + 1:] = 0
    zR[..., c + 1:] = 0
    con = np.clip(_rzb(-(tot[..., c].mean(2) - tot[..., c].min(2))), -10, 30) / 5
    return np.concatenate([x, zT[..., c:c + 1], zT, zR, con[..., None]], 2).astype(np.float32)


def _rz(x):
    med = np.nanmedian(x)
    return (med - x) / (1.4826 * np.nanmedian(np.abs(x - med)) + 1e-6)


DEC_TAGS = {"fast": 0, "win": 1, "spec": 2, "s2cand": 3, "final32": 4, "post": 5, "fine_last": 6, "early_z": 7}
DEC_LMAX = 16                  # (measurement) list PMs padded to 16 (joint decodes: 16 paths, CA-SCL-8: 8 + inf)
_GATES = {}


def gate_load(path, frac, rate):
    """The retry gate of code rate `rate` from nn_b_export.py's json (cached): (mu, sd, w, b, thr) or None."""
    if path not in _GATES:
        import json
        _GATES[path] = json.load(open(path))
    g = _GATES[path].get(rate)
    if g is None:
        return None
    assert g["features"] == list(GATE_F), g["features"]
    return (np.array(g["mu"]), np.array(g["sd"]), np.array(g["w"]), float(g["b"]), float(g["thr"][str(frac)]))


GATE_F = ("pm0", "pm_gap", "pm_spread", "pm_meanex", "syn_w", "n_rem", "n_agree", "agree_bits",
          "l_sum", "l_mean", "l_lt1", "pm_norm", "sgn_agree")



def GATE_MACS(code, L):
    """Retry gate cost per failed decode (total MACs): CRC of L list paths (K bits each), 3 N for the LLR sums and the
    sign agreement, N / 2 log2 N for the best path's polar transform, 2 x 13 for the logistic score."""
    return L * code.K + 3 * code.N + code.N / 2 * np.log2(code.N) + 2 * len(GATE_F)

def gate_feats(code, info, pmL, Lc):
    """The retry gate's features of n failed decodes (as the decode dump's _stats + nn_offline.prep): info (n, L, K)
    the list paths' bits, pmL (n, L) their path metrics, Lc (n, N) the channel LLRs. Returns (n, 13)."""
    n_, Ls_ = pmL.shape
    A_, ar = code.A, np.arange(n_)
    dl = info[..., :A_]
    syn = (code.crc(dl.reshape(-1, A_)).reshape(n_, Ls_, code.C) ^ info[..., A_:]).astype(np.uint8)
    if isinstance(code, bc.PiCode) and not isinstance(code, bc.PiCodeRB):
        syn[..., -1] = 0
    fin = np.isfinite(pmL)
    ib = pmL.argmin(1)
    db = dl[ar, ib]
    pms = np.sort(pmL, 1)
    pm0 = pms[:, 0]
    pmf = np.where(np.isfinite(pms), pms, np.nan)
    u = np.zeros((n_, code.N), np.uint8)
    u[:, code.info_pos] = info[ar, ib]
    cwb = polar_transform(u)
    aL = np.abs(Lc)
    l_sum = aL.sum(1).astype(np.float32)                     # dtypes as the dump (_stats) stores them
    F = dict(pm0=pm0, pm_gap=np.where(np.isfinite(pms[:, 1]), pms[:, 1] - pm0, 0.0) if Ls_ > 1 else np.zeros(n_),
             pm_spread=np.nanmax(pmf, 1) - pm0, pm_meanex=np.nanmean(pmf, 1) - pm0,
             syn_w=syn[ar, ib].sum(1), n_agree=(dl == db[:, None]).all(2).sum(1),
             agree_bits=(((info == info[ar, ib][:, None]).mean(2).sum(1) - 1) / max(Ls_ - 1, 1)).astype(np.float16),
             n_rem=np.array([len(np.unique(syn[q][fin[q]], axis=0)) for q in range(n_)]),
             l_sum=l_sum, l_mean=aL.mean(1).astype(np.float16), l_lt1=(aL < 1).mean(1).astype(np.float16),
             pm_norm=pm0 / l_sum,
             sgn_agree=((Lc < 0) == cwb).mean(1).astype(np.float16))
    X = np.stack([np.asarray(F[k], np.float64) for k in GATE_F], 1)
    X[~np.isfinite(X)] = np.nan                              # as the training (nn_b_export.X_of): nan -> 0 after scaling
    return X


def dec_save(acc, path, **meta):
    """(measurement) the decode dump of one chunk (acc: small_receive's dec_acc): d_<field> one row per decode
    attempt, p_<field> one row per packet, + the scalars meta (rate, snr, rx, chunk_seed); ref_diag: r_<field> one row
    per refined candidate cell, q_<field> one row per packet; fz_diag: f_<field> one row per CA-SCL-8 decode, j_<field>
    one per joint-list decode, g_<field> one per packet."""
    import os
    G_ = ("d", "p", "r", "q", "f", "j", "g")
    if not any(acc.get(g) for g in G_):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = {f"{g}_{k}": np.concatenate([x[k] for x in acc[g]]) for g in G_ if acc.get(g) for k in acc[g][0]}
    np.savez_compressed(path, **out, **{k: np.asarray(v) for k, v in meta.items()})


def fl_save(acc, path, **meta):
    """(measurement, fulllog) the full-search log of one chunk (acc: small_receive's dec_acc): flp_<field> one row per
    search packet, flh_<field> one per decode attempt, flb_<field> one per packet, flc_js one JSON per call."""
    import os
    G_ = ("flp", "flh", "flb", "flc")
    if not any(acc.get(g) for g in G_):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = {f"{g}_{k}": np.concatenate([x[k] for x in acc[g]]) for g in G_ if acc.get(g) for k in acc[g][0]}
    np.savez_compressed(path, **out, **{k: np.asarray(v) for k, v in meta.items()})


RD_HMAX = 96                  # (measurement) ref_diag: scored hypotheses per candidate row, padded (fine_last 9 x 5 = 45)


def rd_newton4(y, nu0, iters, half):
    """(measurement, ref_diag) Newton steps on Lambda4(nu) = |sum_n y[n] e^{-j 2 pi nu nc}|^2 (y = -r^4, nu = 4f) from
    nu0 (n,), as bc._newton_tone, but clamped to |nu - nu0| <= half and no step where the curvature is >= 0 (flagged).
    Returns nu after each step (iters, n), the not-concave flags (iters, n) and the clamped flags (iters, n)."""
    w = -2j * np.pi * bc.NC
    nu = np.asarray(nu0, float).copy()
    out, fnc, fcl = [], [], []
    for _ in range(iters):
        e = np.exp(-2j * np.pi * nu[:, None] * bc.NC[None])
        A, A1, A2 = (y * e).sum(1), (y * w * e).sum(1), (y * w ** 2 * e).sum(1)
        gr = 2 * (A1 * A.conj()).real
        h = 2 * ((A2 * A.conj()).real + np.abs(A1) ** 2)
        bad = ~(h < 0)
        nx = nu + np.where(bad, 0.0, -gr / np.where(bad, -1.0, h))
        nn = np.clip(nx, nu0 - half, nu0 + half)
        fnc.append(bad)
        fcl.append(nn != nx)
        nu = nn
        out.append(nu.copy())
    return np.array(out), np.array(fnc), np.array(fcl)


def rd_parab(Jm, J0, Jp, d):
    """(measurement, ref_diag) vertex of the parabola through costs J at -d, 0, +d: x = (d/2) (J- - J+) / (J- - 2 J0 + J+),
    clamped to +-d; not convex (denominator <= 0, or nan): x = 0. Returns x, the not-convex and the clamped flags."""
    den = Jm - 2 * J0 + Jp
    cvx = den > 0
    x = np.where(cvx, 0.5 * d * (Jm - Jp) / np.where(cvx, den, 1.0), 0.0)
    return np.clip(x, -d, d), ~cvx, np.abs(x) > d


PNS_DEF = dict(q=None, iters=1, soft=True, spec=False, max_calls=None, rho="corr")   # pns defaults (DEFAULT pns)
PNS_SYM = 4 + 12 + 8                                          # pns MACs per symbol: z 4, smoother ~12, de-rotation 8
PNS_KF = 12                                                   # (its smoother part: a serial recursion, sequential)


def pns_re_macs(nl):
    """pns re-encoding of nl list paths: polar transform N/2 log2 N each, the weighted symbol sums 2 N_SYM per path,
    the softmax weights 4 per path."""
    return nl * (bc.N_BITS / 2 * np.log2(bc.N_BITS) + 2 * bc.N_SYM + 4)


def rts(u, R, q):
    """Kalman filter + Rauch-Tung-Striebel smoother of a per-symbol random walk theta_{k+1} = theta_k + w_k, var w = q,
    from u_k = theta_k + v_k, var v_k = R_k (u, R: (B, N)); diffuse prior (est4.estimators.rts with dc = 1)."""
    B, F = u.shape
    if B <= 4:                                                # a few rows (the usual pns call): Python floats, ~5x faster
        return np.array([_rts1(u[b].tolist(), R[b].tolist(), q) for b in range(B)]).reshape(B, F)
    xp, Pp, xf, Pf = (np.empty((B, F)) for _ in range(4))
    x, P = np.zeros(B), np.full(B, 1e12)
    for j in range(F):
        if j:
            P = P + q
        xp[:, j], Pp[:, j] = x, P
        K = P / (P + R[:, j])
        x, P = x + K * (u[:, j] - x), K * R[:, j]
        xf[:, j], Pf[:, j] = x, P
    xs = xf.copy()
    for j in range(F - 2, -1, -1):
        xs[:, j] = xf[:, j] + Pf[:, j] / Pp[:, j + 1] * (xs[:, j + 1] - xp[:, j + 1])
    return xs


def _rts1(u, R, q):
    """rts of one row (lists u, R), scalar arithmetic."""
    F = len(u)
    xs, xf, Pf, Pp = [0.0] * F, [0.0] * F, [0.0] * F, [0.0] * F
    x, P = 0.0, 1e12
    for j in range(F):
        if j:
            P += q
        Pp[j] = P
        K = P / (P + R[j])
        x, P = x + K * (u[j] - x), K * R[j]
        xf[j], Pf[j] = x, P
    xs[F - 1] = xf[F - 1]
    for j in range(F - 2, -1, -1):
        xs[j] = xf[j] + Pf[j] / Pp[j + 1] * (xs[j + 1] - xf[j])   # xp_{j+1} = xf_j (random walk)
    return xs


def pns_symbols(code, info, pm, soft=True):
    """xbar (n, N_SYM): Gray QPSK symbols of the list paths' codewords (info (n, L, K) as decoded, pm (n, L)), weighted
    by softmax(-PM) over the finite paths (soft) or the best path alone. Returns xbar and the paths used per row."""
    n_, Ls_ = pm.shape
    fin = np.isfinite(pm)
    if soft:
        w = np.where(fin, np.exp(-(pm - np.where(fin, pm, np.inf).min(1, keepdims=True))), 0.0)
    else:
        w = np.zeros((n_, Ls_))
        w[np.arange(n_), pm.argmin(1)] = 1.0
    w /= np.maximum(w.sum(1, keepdims=True), 1e-300)
    u = np.zeros((n_ * Ls_, code.N), np.uint8)
    u[:, code.info_pos] = info.reshape(n_ * Ls_, -1)
    cw = polar_transform(u)[:, bc.INTERLEAVER].reshape(n_, Ls_, code.N)
    s = ((1 - 2.0 * cw[..., 0::2]) + 1j * (1 - 2.0 * cw[..., 1::2])) / np.sqrt(2)
    return np.einsum("nl,nlk->nk", w, s), (w > 0).sum(1)


def _padl(info, pm, L):
    """(pns) a list padded to L paths (zero bits, inf PMs: weight 0)."""
    n_, l_ = pm.shape
    if l_ == L:
        return info, pm
    return (np.concatenate([info, np.zeros((n_, L - l_, info.shape[2]), np.uint8)], 1),
            np.concatenate([pm, np.full((n_, L - l_), np.inf)], 1))


def pns_phase(y, xbar, sigma2, q):
    """Smoothed phase phi (n, N_SYM) of y (de-rotated MF output) against xbar: z = y xbar*, linearised about
    phi0 = arg sum z (as est4 gain_kalman 'im'): u_k = Im(z_k e^{-j phi0}) / (a0 |xbar_k|^2), variance
    sigma2 / (a0^2 |xbar_k|^2) (sigma2 per real dimension = s2 / 2), a0 = |sum z| / sum |xbar|^2; phi = phi0 + RTS."""
    z = y * np.conj(xbar)
    e = np.maximum(np.abs(xbar) ** 2, 1e-9)
    S = z.sum(1)
    phi0 = np.angle(S)
    a0 = np.maximum(np.abs(S) / e.sum(1), 1e-9)[:, None]
    u = (z * np.exp(-1j * phi0)[:, None]).imag / (a0 * e)
    return phi0[:, None] + rts(u, sigma2 / (a0 ** 2 * e), q)


def rho_seg(code, r, data, fh, Ss):
    """Segment re-encoding correlation (n, len(Ss)): rho_s = sum_seg |sum_{k in seg} r_k s_k* e^{-j 2 pi fh nc}| /
    sqrt(N sum |r|^2), segments of S symbols (each its own phase); 1 for a noise-free right decode, = rho at S = N."""
    cw = code.encode(data)[:, bc.INTERLEAVER]
    s = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
    z = r * np.conj(s) * np.exp(-2j * np.pi * fh[:, None] * bc.NC[None])
    en = np.sqrt(bc.N_SYM * np.sum(np.abs(r) ** 2, 1))
    return np.stack([np.abs(z.reshape(len(z), bc.N_SYM // S, S).sum(2)).sum(1) / en for S in Ss], 1)


def _refine2_sq(cand, roffs, sub, T, r, score, decode, passed):
    """(bpsk_sq) bf._refine2 with the square's phase: bc.phase2 at each offset, kept on the cell's branch mod pi."""
    fr = np.array([c[0] for c in cand])
    f = np.array([c[1] for c in cand])
    th = np.array([c[2] for c in cand])
    F = f[:, None] + roffs[None] * bc.STEP
    TH = bc.phase2(r[fr], F)
    TH = TH + np.round((th[:, None] - TH) / np.pi) * np.pi
    F = np.repeat(F, len(sub), 1)
    TH = (TH[:, :, None] + np.array(sub)[None, None]).reshape(len(fr), -1)
    H = F.shape[1]
    M = score(np.repeat(fr, H), F.ravel(), TH.ravel()).reshape(len(fr), H)
    o = np.argsort(M, 1)
    act = np.ones(len(fr), bool)
    for t in range(T):
        j = np.where(act & ~passed[fr])[0]
        if not len(j):
            break
        ok = decode(fr[j], F[j, o[j, t]], TH[j, o[j, t]])
        act[j[ok]] = False


def small_receive(r, rx, snr, code, sigma2, st, spec, sym=None):
    """The small receiver (_small_receive); fzstop: code.fz_stop (shared code object) cleared on every exit, also when
    the receiver raises (the normal path clears it already: no change there)."""
    try:
        return _small_receive(r, rx, snr, code, sigma2, st, spec, sym)
    finally:
        code.fz_stop = None


def _small_receive(r, rx, snr, code, sigma2, st, spec, sym=None):
    p = {**DEFAULT, **spec.get("sps", {})}
    if p["snr_err"]:                                          # an SNR estimate off by snr_err dB: every SNR-dependent
        snr = snr + p["snr_err"]                              # setting and the LLR scaling see it
        sigma2 = sigma2 * 10 ** (-p["snr_err"] / 10)
    p["code_rate"] = p["rate"]                                # RHO_N per code; every other setting per profile
    p["rate"] = bc.PROFILE.get(p["rate"], p["rate"])
    for key in PER_RATE:
        if isinstance(p[key], dict):
            p[key] = p[key].get(p["rate"])
    if isinstance(p["nph"], dict):                            # nph per CODE rate ({"0.15": 4}); missing -> the SNR rule
        p["nph"] = p["nph"].get(p["code_rate"])
        if isinstance(p["nph"], tuple):                       # (phases, snr_hi): that many phases below snr_hi dB,
            p["nph"] = p["nph"][0] if snr < p["nph"][1] else None   # the default SNR rule (2 phases) from there on
    if p["spec_snr"] is not None and p["win_spec"] is not None:
        th = p["spec_snr"].get(p["code_rate"]) if isinstance(p["spec_snr"], dict) else p["spec_snr"]
        if th is not None and snr >= th:
            p["win_spec"] = None                              # = the receiver without the speculative decode
    gate = gate_load(p["nn_b"][0], p["nn_b"][1], p["code_rate"]) if p["nn_b"] else None
    B = len(r)
    pns_on = p["pns"] is not None                             # phase-tracking retry (DEFAULT pns)
    if pns_on:
        assert not p["equiv"] and not p["pilots"], "pns: the interleaved blind (PiCode) receivers only"
        PNSC = {**PNS_DEF, **p["pns"]}
        lw_ = p["pns_lw"] if p["pns_lw"] is not None else (bc.PHASE_NOISE if bc.PHASE_NOISE > 0 else 1e-4)
        q_pn = PNSC["q"] if PNSC["q"] is not None else 2 * np.pi * lw_
        pns_n = np.zeros(B, int)                              # pns calls per packet (max_calls)
        for k_ in ("pns_calls", "pns_decodes", "pns_fixed"):
            st[k_] = st.get(k_, 0)
    if p["rhos"]:
        assert bc.N_SYM % p["rhos"] == 0, "rhos: segment length must divide N_SYM"
    rs_S = tuple(p["rhos_log"]) if p["rhos_log"] else ()     # (measurement) rhos_log segment lengths
    if rs_S:
        assert all(bc.N_SYM % S == 0 for S in rs_S), "rhos_log: segment lengths must divide N_SYM"
        st.setdefault("rhos_rows", [])                        # (every chunk of the receiver has the key: merge sums)
    k = p["kstep"] or bf.grid_step(p["rate"], snr)          # kstep: a fixed grid step (STEP units) at every SNR
    g = bf.grid(k)["f"]
    nph = p["nph"] or (4 if snr < -1 else 2)
    qs = np.arange(nph) * (2 if nph == 2 else 1)              # phase offsets of a cell (pi/4 units)
    nph0 = nph                                                # (the candidates' sub-offsets follow the unhalved count)
    if p["equiv"]:                                            # phase-equivariant: offsets mod pi/2 only (q pi/4 < pi/2)
        assert bc.NOINT and isinstance(code, bc.PiCode4), "equiv needs BLIND_NOINT=1 and a bc.PiCode4 code"
        assert not p["nn_b"], "equiv: the retry gate's features assume the interleaved PiCode list"
        qs = qs[qs < 2]
        nph = len(qs)
    if p["nopi"] or p["bpsk_sq"]:                             # (blind_fmt) phase sets of the rate-matched formats
        assert p["q_fix"] and not (p["nopi"] and p["bpsk_sq"]) and not p["equiv"] and not p["pilots"] \
            and not p["blind_peaks"] and p["beam"] is None and p["race_phase"] is None and not p["s3_dd"] \
            and not p["ddref"] and p["ref_diag"] is None and p["s3dump"] is None and p["lmarg"] is None, \
            "nopi / bpsk_sq: q_fix receivers without equiv, pilots, blind_peaks, beam, race_phase, s3_dd, ddref, lmarg"
        if p["nopi"]:                                         # phase mod 2 pi: both pi halves
            qs = np.concatenate([qs, qs + 4])
        else:                                                 # squared phase mod pi: the pi/2 branch is a dud
            assert bc.FMT is not None and bc.FMT.mod != "qpsk", "bpsk_sq needs a BPSK blind_fmt context"
            qs = 2 * qs[qs < 2]
        nph = len(qs)
    if p["eqrb"] or bc.ROTBITS:                               # rotation-bit code: only all together
        assert p["eqrb"] and p["equiv"] and bc.ROTBITS and isinstance(code, bc.PiCodeRB), \
            "eqrb needs equiv, BLIND_NOINT=1, BLIND_ROTBITS=1 and a bc.PiCodeRB code"
    qph = qs if p["q_fix"] else np.arange(nph)                # phase of a cell's best index qb (pi/4 units): q_fix the
                                                              # scored offset qs[qb]; False (baseline) qb itself
    fs_ = bf.fast_sc(code.A)
    fsn = bf.FastSC(fs_.frozen)                               # the same metric, rate-0 nodes in chunks (checkpoints)
    fsn.split = SPLIT
    lv = np.array([h for _, h in leaves(fsn.plan, 0, bc.N_BITS, [], SPLIT)])
    cks = [1.0] if not p["ck"] else sorted(set(p["ck"]) | {1.0})
    cnn = p["ck_nn"]
    if cnn is not None:                                       # checkpoint NN at CK_FR[cnn] (small_ck_nn.py): every
        assert not p["coarse"], "the checkpoint NN needs every cell up to its checkpoint"   # cell is decoded up to
        cks = sorted({c for c in cks if c > CK_FR[cnn]} | {CK_FR[cnn], 1.0})                # it, z-test after it
    if p["beam"] is not None:                                 # beam over the (cell, phase) hypotheses: from beam[0] on
        assert not p["coarse"] or p["beam"][0] == min(cks)    # the best beam[1] by path metric, half as many at each
        cks = sorted(set(cks) | {p["beam"][0], 0.75})          # later checkpoint (>= 4); no z-test from there on
        if p["keep_early"] is not None:                       # + a lenient checkpoint before: the best keep_early[1]
            cks = sorted(set(cks) | {p["keep_early"][0]})     # share of the hypotheses continue
    if p["phase_keep"] is not None:                           # at phase_keep[0] each cell keeps its best
        cks = sorted(set(cks) | {p["phase_keep"][0]})         # phase_keep[1] phases
    if p["race_phase"] is not None:                           # phase racing: at race_phase[0] each cell keeps only
        cks = sorted(set(cks) | {p["race_phase"][0], 1.0})    # its phases within race_phase[1] nats of its best one
    if p["ck_useful"]:                                        # (blind_fmt) fractions of the not pre-frozen u positions
        assert bc.FMT is not None, "ck_useful needs a blind_fmt context"
        ul_ = np.cumsum(~bc.FMT.pre)[lv - 1]                  # useful positions before each leaf end
        _nlf = lambda c: max(1, int((ul_ <= c * ul_[-1] + 1e-9).sum()))
        nl = [_nlf(c) for c in cks]
        fr_act = lv[np.array(nl) - 1] / bc.N_BITS             # the actual leaf ends (cost); frac stays nominal (the
        frac = np.array(cks, float)                           # phase_keep / beam / race_phase comparisons)
        sh = cost_share(fsn.plan, fr_act) if p["cost"] == "tree" else fr_act
    else:
        nl = [max(1, int((lv <= c * bc.N_BITS).sum())) for c in cks]
        frac = lv[np.array(nl) - 1] / bc.N_BITS
        # cost of the decode up to each checkpoint, as a share of a full metric pass: linear in the codeword fraction,
        # or the Fast-SSC tree cost of the leaves decoded so far ("tree": at R = 1/10 the mostly frozen first half is 36 %)
        sh = cost_share(fsn.plan, frac) if p["cost"] == "tree" else frac
    m_met, derot = vp.metric_macs(code.A), vp.MAC["cmul"] * bc.N_SYM
    lmo = p["lmarg"] is not None and p["joint"] is None       # lmarg (DEFAULT): the list-marginalised candidate order
    if lmo:
        L_e = int(p["lmarg"])
        c_lm = (cks[-2] if len(cks) > 1 else 1.0) if p["lmarg_ck"] is None else float(p["lmarg_ck"])
        fr_lm = lv[max(1, int((lv <= c_lm * bc.N_BITS).sum())) - 1] / bc.N_BITS   # the last leaf end <= c_lm N
        sh_lm = float(cost_share(fsn.plan, fr_lm)) if p["cost"] == "tree" else float(fr_lm)
        cut_lm = int(round(fr_lm * bc.N_BITS))
        lg_lm = np.log2(2 * L_e)
        # MACs of one hypothesis (on one core): its LLRs (de-rotation), L_e x the Fast-SSC work up to fr_lm (the
        # metric_macs model x the tree-cost share), the 2 L_e -> L_e path sort (bitonic, L_e lg (lg + 1) / 2
        # comparators) at each information bit up to fr_lm (L_e > 1)
        c_lmh = derot + L_e * m_met * sh_lm + ((~fs_.frozen[:cut_lm]).sum() * L_e * lg_lm * (lg_lm + 1) / 2
                                               if L_e > 1 else 0.0)
        dec_lm = fastscl.FastSCL(fs_, L_e)
        for k_ in ("lm_calls", "lm_hyp", "lm_first_diff", "macs_lm") + (("lm_lazy_runs",) if p["lmarg_lazy"] else ()):
            st[k_] = st.get(k_, 0)
    ddo = bool(p["ddref"]) and p["joint"] is None             # ddref (DEFAULT): DD-Newton refinement, grid fallback
    if ddo:
        assert not p["s3_dd"], "ddref replaces s3_dd's refinement: not both"
        for k_ in ("ddref_cells", "ddref_hit", "ddref_fallback", "ddref_fallback_hit", "macs_ddref", "ddref_paid"):
            st[k_] = st.get(k_, 0)
    if isinstance(p["fzstop"], dict):                         # fzstop per CODE rate ({"0.15": (q, t)}); missing -> off
        p["fzstop"] = p["fzstop"].get(p["code_rate"])
    fzs_on = p["fzstop"] is not None                          # fzstop (DEFAULT): the decoder's frozen-metric stop
    assert not (fzs_on and (pns_on or gate is not None or p["s3_dd"])), \
        "fzstop with pns / the retry gate (nn_b) / s3_dd: not modelled by fzstop (stop accounting, CRC-failure rows)"
    code.fz_stop = tuple(p["fzstop"]) if fzs_on else None     # (the code object is shared by the receivers of a run;
                                                              # small_receive clears it on every exit)
    if fzs_on:
        for k_ in ("fz_checks", "fz_stops", "fz_stops_right", "macs_fz_saved"):
            st[k_] = st.get(k_, 0)
    sto = p["stage_acc"] is not None                          # (measurement) stage_acc (DEFAULT)
    n_hyp = np.zeros(B, int)                                  # (measurement) metric hypotheses started per packet
    macs = np.zeros(B)
    cores = np.ones(B)                                        # the most cells decoded at once per packet
    passes = np.ones(B)                                       # sequential passes of the cores (latency)
    ncore = p["cores"] or (p["batch"][0] if p["batch"] else None)   # a fixed number of decoder cores (one cell each):
                                                              # each stage takes ceil(cells / ncore) passes, the path
                                                              # metrics of every pass are stored and compared jointly
    Kc = ncore or len(g)                                      # cores (unbounded receivers: one per grid cell)
    dmac = np.zeros(B)                                        # MACs of the CA-SCL decodes and their critical path
    dcrit = np.zeros(B)                                       # with the list paths on their own cores
    KP = p["cores"] or 32                                     # (measurement) the "parallel" critical path: every
    dcritp = np.zeros(B)                                      # sample-wise serial step (4th power, FFT, MF corrections,
    seqm = np.zeros(B)                                        # LLRs, Newton sums, re-encoding correlation) split over
    seqc = np.zeros(B)                                        # KP cores, the 2L -> L path sort as a bitonic network;
                                                              # the SC metric passes outside the stages stay sequential
                                                              # (seqm their MACs, seqc their critical path)
    crc_seen = np.zeros(B, bool)                              # (measurement) a CRC pass seen / the first was wrong
    crc_wrong = np.zeros(B, bool)
    pmac = np.zeros(B)                                        # MACs of the parallel work (grid stages, hypothesis
    crit = np.zeros(B)                                        # scoring) and its critical path: per pass the busiest
    crit_g = np.zeros(B)                                      # (its grid-search part)
                                                              # core; everything else (decodes, FFT, ...) is serial
    crit_gh = np.zeros(B)                                     # (measurement) crit_g with one core per (cell, phase)
    # (measurement) 4 decodes at once (KP = 32 cores / 8 list paths, as est3/plots.py pilot_macs): d4a the change of
    # the critical path when a decode() call's n hypotheses of a packet take ceil(n / 4) decode rounds (its CA retries:
    # the SC passes in parallel, ceil(n_fail / 4) decodes); d4b the further change when the serial candidate loops
    # (stage-2 candidates, final, fine_last) run 2 candidates x 2 hypotheses per round; d4w bounds d4b's extra MACs
    d4a, d4b, d4w = np.zeros(B), np.zeros(B), np.zeros(B)
    _lg8 = np.log2(2 * 8)
    n_dec = getattr(code, "n_dec", code.K)                    # information bits the list sorts at (PiCodeRB: K + 2)
    dp8 = vp.MAC["decode"] / 8 * np.ceil(8 / Kc) + n_dec * _lg8 * (_lg8 + 1) / 2   # a CA-SCL-8 decode's path part
    ctx = {"tag": "fast", "log": None}                        # (measurement) origin of the decodes / d4b loop records
    # (measurement) decode dump (dec_dump): one row per decode attempt; ctx "sc" the last score() call (fr, fh, th, M),
    # "H" (hypotheses, sub-offsets) per candidate of that call, "meta" the grid state per candidate (_gm), "jl" the
    # joint decode's list; nothing here enters macs / pmac / dmac / crit or a decision
    dd = p["dec_dump"] is not None and p["truth"] is not None and p["truth_f"] is not None
    ctx.update(sc=None, H=None, meta=None, jl=None)
    drows, natt = [], np.zeros(B, int)                        # decode rows (dicts of arrays per call), attempts so far
    # (measurement) ref_diag (DEFAULT): rows of the refined candidate cells; ctx "rdg" the grid state of the packet in the
    # search (packet, Pq, qal, paid, cell phases: the checkpoint PMs a receiver has stored), "rd_h" the joint decode's
    # chosen hypothesis; nothing here enters macs / pmac / dmac / crit or a decision
    rdo = p["ref_diag"] is not None and p["truth"] is not None and p["truth_f"] is not None
    rdrows = []
    if rdo:
        ctx.update(rdg=None, rd_h=None)
    # (measurement) fz_diag (DEFAULT): one row per CA-SCL decode (_fzlog after each code.decode / decode_joint call);
    # the decoder only records (polar.PolarCode fz_q); nothing here enters macs / pmac / dmac / crit or a decision
    fzo = p["fz_diag"] is not None and p["truth"] is not None and p["truth_f"] is not None
    code.fz_q = FZ_Q if fzo else None                         # (the code object is shared by the receivers of a run)
    fzrows = []
    fzc, fzr = np.zeros(B, int), np.zeros(B, int)            # (fz_diag) CA-SCL calls / decode rounds per packet so far
    fzn = [0]                                                 # (fz_diag) CA-SCL calls of this small_receive call
    # (measurement) fulllog (DEFAULT): the joint tuner's full-search log; nothing here enters macs / pmac / dmac / crit
    # or a decision (the side refine2 calls run after the search on local passed flags, outside every counter)
    flo = p["fulllog"] is not None and p["fulllog"] is not False
    if flo:
        FLO = {**FL_DEF, **(p["fulllog"] if isinstance(p["fulllog"], dict) else {})}
        assert p["truth"] is not None and p["truth_f"] is not None and p["dec_acc"] is not None, \
            "fulllog needs truth, truth_f and a dec_acc (run_blind_fs --fulllog)"
        assert (p["joint"] is None and not p["coarse"] and p["beam"] is None and p["race_phase"] is None
                and p["keep_early"] is None and p["lmarg"] is None and not p["ddref"] and not p["s3_dd"] and not pns_on
                and not p["pilots"] and p["win_spec"] is None and not fzs_on and not p["cap_core"] and not p["nn"]
                and not p["nn_keep"] and not p["pre_keep"] and not p["top_k"] and not p["equiv"] and not p["rhos"]
                and gate is None and not p["pilot_score"] and not p["nn_score"] and p["dump"] is None
                and p["dump_pm"] is None and p["reencode"] and "pilots" not in p["prior"]), \
            "fulllog: a receiver feature the joint replay does not model"
        FLF = sorted(set(cks) | {float(x) for x in FLO["fr"]})   # logged checkpoint fractions (nominal), their leaf
        if p["ck_useful"]:                                    # ends, comparison fractions and cost shares as cks's
            nlL = np.array([_nlf(c) for c in FLF])
            frL = np.array(FLF, float)
            shL = cost_share(fsn.plan, lv[nlL - 1] / bc.N_BITS) if p["cost"] == "tree" else lv[nlL - 1] / bc.N_BITS
        else:
            nlL = np.array([max(1, int((lv <= c * bc.N_BITS).sum())) for c in FLF])
            frL = lv[nlL - 1] / bc.N_BITS
            shL = cost_share(fsn.plan, frL) if p["cost"] == "tree" else frL
        jL = [FLF.index(c) for c in cks]                      # the receiver's checkpoints among the logged ones
        assert np.array_equal(np.asarray(frL)[jL], frac) and np.array_equal(np.asarray(shL)[jL], sh), "fulllog: cks"
        flp, flh = [], []                                     # packet rows (dicts), decode-attempt rows (dicts of arrays)
        ctx.update(fl=None, fl_t=0)

    def _cpar(fr_):                                           # (measurement) crit_par / total MACs of packets fr_ so far
        return (crit + dcritp + seqc + (macs - pmac - dmac - seqm) / KP)[fr_], macs[fr_].copy()

    def _lst(Lc):                                             # (measurement) every list path of the last decode (code's
        pm_ = code._pm.copy()                                 # traceback state): info bits (n, Ls, K), PMs, channel LLRs
        if p["equiv"]:                                        # PiCode4: each path un-rotated by its accepted rotation
            return code.last_info.copy(), pm_, Lc
        n_, Ls_ = pm_.shape
        info = np.empty((n_, Ls_, code.K), np.uint8)
        path = np.broadcast_to(np.arange(Ls_), (n_, Ls_))
        rows = np.arange(n_)[:, None]
        for k_ in range(code.K - 1, -1, -1):
            info[:, :, k_] = code._bits[k_][rows, path]
            path = code._parents[k_][rows, path]
        return info, pm_, Lc

    def _plist(h=None):                                       # (pns) the last decode's list: info bits (n, Ls, K) as
        pm_ = code._pm.astype(float)                          # decoded, PMs (n, Ls); h (a joint decode): only the
        n_, Ls_ = pm_.shape                                   # paths that started on hypothesis h (others inf)
        info = np.empty((n_, Ls_, code.K), np.uint8)
        path = np.broadcast_to(np.arange(Ls_), (n_, Ls_))
        rows = np.arange(n_)[:, None]
        for k_ in range(code.K - 1, -1, -1):
            info[:, :, k_] = code._bits[k_][rows, path]
            path = code._parents[k_][rows, path]
        if h is not None:
            pm_[path != h] = np.inf
        return info, pm_

    def _thr():                                             # the re-encoding threshold (as in decode)
        s_re = snr + p["re_margin"]
        s_rl = 10 ** (s_re / 10)
        thr = bf.rho_min(s_re)
        if tab:
            thr = max(thr, float(np.interp(s_re, *zip(*tab))) * np.sqrt(s_rl / (1 + s_rl)))
        return thr

    def _stats(fr_, fh_, th_, rc_, lst_, d_, okc_):
        """(measurement) decoder / channel / truth stats of n decode rows: lst_ = _lst (info, PMs, LLRs), d_ the
        delivered path (CRC-passing one if any), okc_ its CRC pass. PiCode: a syndrome equal to the last-bit flip
        counts as 0 (the pi complement), so the syndrome is taken with its last bit cleared."""
        info, pmL, Lc = lst_
        n_, Ls_ = pmL.shape
        A_, ar = code.A, np.arange(n_)
        dl = info[..., :A_]
        syn = (code.crc(dl.reshape(-1, A_)).reshape(n_, Ls_, code.C) ^ info[..., A_:]).astype(np.uint8)
        if isinstance(code, bc.PiCode) and not isinstance(code, bc.PiCodeRB):   # (PiCodeRB: no last-bit rule)
            syn[..., -1] = 0
        okl = ~syn.any(2) & np.isfinite(pmL)
        ib = pmL.argmin(1)                                    # the best-PM path
        db = dl[ar, ib]
        pms = np.full((n_, DEC_LMAX), np.inf, np.float32)
        pms[:, :Ls_] = np.sort(pmL, 1)
        u = np.zeros((n_, code.N), np.uint8)
        u[:, code.info_pos] = info[ar, ib]
        cwb = polar_transform(u)                              # the best path's own codeword (its CRC bits as decoded)
        aL = np.abs(Lc)
        tru = p["truth"][fr_]
        rho_c = np.full(n_, np.nan)
        if okc_.any():
            rho_c[okc_] = bf.reencode_rho(code, rc_[okc_], d_[okc_], fh_[okc_])
        dF = (fh_ - p["truth_f"][fr_]) / bc.STEP
        dT = th_ - p["truth_th"][fr_] if p["truth_th"] is not None else np.full(n_, np.nan)
        return dict(
            f_hyp=fh_.astype(np.float32), th_hyp=th_.astype(np.float32), f_err=dF.astype(np.float32),
            th_err4=((dT + np.pi / 4) % (np.pi / 2) - np.pi / 4).astype(np.float16),     # mod pi/2
            th_err2=((dT + np.pi / 2) % np.pi - np.pi / 2).astype(np.float16),           # mod pi (PiCode)
            pm_list=pms, pm_crc=np.where(okl.any(1), np.where(okl, pmL, np.inf).min(1), np.nan).astype(np.float32),
            crc=okc_.copy(), syn_w=syn[ar, ib].sum(1).astype(np.int8),
            n_agree=(dl == db[:, None]).all(2).sum(1).astype(np.int8),
            agree_bits=(((info == info[ar, ib][:, None]).mean(2).sum(1) - 1) / max(Ls_ - 1, 1)).astype(np.float16),
            n_rem=np.array([len(np.unique(syn[q][np.isfinite(pmL[q])], axis=0)) for q in range(n_)], np.int8),
            l_sum=aL.sum(1).astype(np.float32), l_mean=aL.mean(1).astype(np.float16),
            l_lt1=(aL < 1).mean(1).astype(np.float16), sgn_agree=((Lc < 0) == cwb).mean(1).astype(np.float16),
            rho_best=bf.reencode_rho(code, rc_, db, fh_).astype(np.float16), rho_crc=rho_c.astype(np.float16),
            right=(d_ == tru).all(1), best_right=(db == tru).all(1), in_list=(dl == tru[:, None]).all(2).any(1),
            in_cell=np.abs(dF) <= 0.5)

    def _gm(c, q, j_, z_, pm_, alive_, paid_, ntr):         # (measurement) grid state of cell c at its decode
        za = np.sort(z_[alive_ & np.isfinite(z_)])[::-1]
        return (int(c), int(q), float(pm_[c, j_]), float(z_[c]), int((za > z_[c]).sum()),
                za[0] if len(za) else np.nan, za[1] if len(za) > 1 else np.nan, int(j_), float(paid_[c]),
                int(alive_.sum()), int(ntr))

    def _dlog(fr, fh, th, rc, lm_, d_m, ok_m, rt_, ok, rtry, c0):
        """(measurement) the rows of one decode() call: the main decodes (n) and their CA retries, linked by parent."""
        n_ = len(fr)
        S = _stats(fr, fh, th, rc, lm_, d_m, ok_m)
        G = np.full((n_, 11), np.nan)                         # _gm fields
        G[:, [0, 1, 4, 7, 9, 10]] = -1
        hy = np.full((n_, 4), -1.0)                           # offset index, sub-offset index, rank by metric, metric
        hy[:, 3] = np.nan
        sc, H = ctx["sc"], ctx["H"]
        mt = ctx["meta"]
        for q in range(n_ if H is not None or sc is not None else 0):
            m = np.where((sc[0] == fr[q]) & (sc[1] == fh[q]) & (sc[2] == th[q]))[0] if sc is not None else []
            ci = 0 if (mt is not None and len(mt) == 1) else -1   # no scored match (s3_dd): a lone candidate's cell
            if len(m):
                m = int(m[0])
                if H is None:                                 # the fast path: score(both pi/2 branches) at f0
                    hy[q, 1], hy[q, 3] = m // max(len(sc[0]) // 2, 1), sc[3][m]
                    continue
                ci, h = divmod(m, H[0])
                blk = sc[3][ci * H[0]:(ci + 1) * H[0]]
                hy[q] = (h // H[1], h % H[1], int((blk < sc[3][m]).sum()), sc[3][m])
            if H is not None and mt is not None and 0 <= ci < len(mt):
                G[q] = mt[ci]
        def _att(fr_):                                        # attempt indices (a packet may repeat in one call)
            a_ = np.empty(len(fr_), int)
            for q_, i_ in enumerate(fr_):
                a_[q_] = natt[i_]
                natt[i_] += 1
            return a_

        att = _att(fr)
        tag = DEC_TAGS.get(ctx["tag"], -1)
        acc_ = ok & ~rtry

        def row(fr_, S_, at_, par_, G_, hy_, acc__, c_, dfca):
            m_ = len(fr_)
            return dict(pk=fr_.astype(np.int32), att=at_.astype(np.int16), tag=np.full(m_, tag, np.int8),
                        retry=np.full(m_, par_ is not None),
                        parent=(np.full(m_, -1) if par_ is None else par_).astype(np.int16),
                        cell=G_[:, 0].astype(np.int16), q=G_[:, 1].astype(np.int8), off=hy_[:, 0].astype(np.int8),
                        sub=hy_[:, 1].astype(np.int8), hrank=hy_[:, 2].astype(np.int8),
                        m_hyp=hy_[:, 3].astype(np.float32), pm_cell=G_[:, 2].astype(np.float32),
                        z=G_[:, 3].astype(np.float16), zrank=G_[:, 4].astype(np.int16), z1=G_[:, 5].astype(np.float16),
                        z2=G_[:, 6].astype(np.float16), ck=G_[:, 7].astype(np.int8), paid=G_[:, 8].astype(np.float16),
                        n_alive=G_[:, 9].astype(np.int16), n_tried=G_[:, 10].astype(np.int16),
                        cpar0=c_[0].astype(np.float32), macs0=c_[1].astype(np.float32),
                        rho_min=np.full(m_, _thr(), np.float16), acc=acc__.copy(), dfca=dfca.astype(np.float32), **S_)

        drows.append(row(fr, S, att, None, G, hy, acc_, c0, np.full(n_, np.nan)))
        if rt_ is not None:                                   # the CA retries of the failed main decodes
            j, fca, tca, lst2, d2, ok2, c1 = rt_
            S2 = _stats(fr[j], fca, tca, rc[j], lst2, d2, ok2)
            at2 = _att(fr[j])
            hy2 = np.full((len(j), 4), -1.0)
            hy2[:, 3] = np.nan
            drows.append(row(fr[j], S2, at2, att[j], G[j], hy2, ok[j] & rtry[j], c1, (fca - fh[j]) / bc.STEP))

    RHO_B = 30                                               # rho / threshold histogram: 30 bins of 0.1 over [0, 3)
                                                              # (bin 10 starts at the threshold; >= 3 in the last)

    def _par(i, cost, nh=None, join=None, hyp=None):          # one stage: per-core costs, dealt K at a time in
        keep_ = cost > 0                                      # decreasing order -> each pass costs its largest
        cost = cost[keep_]
        if len(cost):
            pmac[i] += cost.sum()
            crit[i] += np.sort(cost)[::-1][::Kc].sum()
            crit_g[i] += np.sort(cost)[::-1][::Kc].sum()
            # (measurement) per hypothesis: a cell's metric cost split over its nh phases, its join cost (phase +
            # de-rotation) paid by every hypothesis; the same LPT over Kc cores
            j_ = np.zeros(len(cost)) if join is None else np.broadcast_to(join, keep_.shape)[keep_]
            if hyp is None:
                h_ = np.ones(len(cost), int) if nh is None else np.maximum(np.broadcast_to(nh, keep_.shape)[keep_], 1)
                hc = np.repeat((cost - j_) / h_ + j_, h_)
            else:                                             # hyp = (L, C) of _segs: hypothesis h of a cell pays
                L_, C_ = hyp[0][keep_], hyp[1][keep_]         # m_met x the pieces where the cell decodes > h phases
                n_h = np.maximum((C_ * (L_ > 0)).max(1), 1)
                hc = np.concatenate([(m_met * (L_ * (C_ > h)).sum(1) + j_)[n_h > h] for h in range(int(n_h.max()))])
            crit_gh[i] += np.sort(hc)[::-1][::Kc].sum()

    def _segs(qcut, qal, paid, c, hi):
        """(accounting) the metric work of the cells c from paid[c] up to the share hi, piecewise: lengths L (n, P)
        and phases decoded C (n, P) per piece; below a pruning share (qcut: share -> phases per cell before the first
        pruning there) the phases before it (a receiver computes all of them up to the pruning checkpoint), beyond the
        last one the cell's current phases. Work = m_met (L C).sum(1)."""
        S = sorted(qcut)
        e = [0.0] + S + [np.inf]
        L = np.stack([np.clip(np.minimum(hi, e[k + 1]) - np.maximum(paid[c], e[k]), 0, None) for k in range(len(S) + 1)], 1)
        C = np.stack([qcut[s][c] for s in S] + [qal[c].sum(1)], 1)
        return L, C

    out = np.zeros((B, code.A), np.uint8)
    passed = np.zeros(B, bool)
    have = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
    s3rows = []                                               # (measurement) BLIND_IMPLEMENTATION/testing/ Stage 3 dump rows
    uid = np.random.default_rng().integers(1 << 40) * 1000 + np.arange(B)   # packet ids of this call
    pos = zp = None
    if p["pilots"]:
        pos = np.array(vp.PATTERNS[p["pilots"]])
    s_lin = 10 ** (snr / 10)
    tab = p["rho_n"].get(p["code_rate"]) if isinstance(p["rho_n"], dict) else p["rho_n"]

    def _dec_cost(fr, L, H=1):                                # one CA-SCL-L decode of H hypotheses per frame: total
        tot = L / 8 * vp.MAC["decode"] + H * vp.MAC["llr"]  # MACs, and its critical path with every list path on
        np.add.at(macs, fr, tot)                              # its own core (+ the path-metric sort, 2L -> L, at
        np.add.at(dmac, fr, tot)                              # each information bit)
        np.add.at(dcrit, fr, vp.MAC["decode"] / 8 * np.ceil(L / Kc) + vp.MAC["llr"] * np.ceil(H / Kc)
                  + n_dec * 2 * L * np.log2(2 * L))
        lg = np.log2(2 * L)                                   # bitonic sort of 2L metrics: lg (lg + 1) / 2 stages
        np.add.at(dcritp, fr, vp.MAC["decode"] / 8 * np.ceil(L / Kc) + vp.MAC["llr"] * H / KP
                  + n_dec * lg * (lg + 1) / 2)
        if p["equiv"]:                                        # PiCode4: the un-rotation check of every list path, each
            rm = code.rot_macs()                              # path on its own core
            np.add.at(macs, fr, L * rm)
            np.add.at(dmac, fr, L * rm)
            np.add.at(dcrit, fr, rm * np.ceil(L / Kc))
            np.add.at(dcritp, fr, rm * np.ceil(L / Kc))
            st["macs_rot"] = st.get("macs_rot", 0.0) + float(L * rm * len(fr))

    def _fzs(fr_, d_, ok_, L_, kind, rounds=True):
        """fzstop (DEFAULT): after a CA-SCL call of rows fr_ (d_ (n, A), ok_ (n,), edited in place): the rows the decoder
        stopped (code.fzs_stop) become CRC failures (data 2: never the packet) and get the work after the stop back:
        total (1 - share) L/8 MAC decode (fz_share at code.fzs_pos), per core (dcritp; dcrit in its own model) the
        share of the path part + the 2L -> L sorts of the information bits not decided; rounds (code.decode calls, as
        decode's d4a): per packet the call's 4-decode rounds (rows in call order) keep their length unless every row
        of the round stops (then the round ends at the stop). Returns the stopped mask."""
        fr_ = np.asarray(fr_)
        s_ = np.asarray(code.fzs_stop, bool).copy()
        st["fz_checks"] += len(fr_)
        if not s_.any():
            return s_
        tr_ = float(fz_share(code.frozen, code.fzs_pos))
        lg = np.log2(2 * L_)
        tot = (1 - tr_) * L_ / 8 * vp.MAC["decode"]
        cr = (1 - tr_) * vp.MAC["decode"] / 8 * np.ceil(L_ / Kc) + (n_dec - code.fzs_nb) * lg * (lg + 1) / 2
        crd = (1 - tr_) * vp.MAC["decode"] / 8 * np.ceil(L_ / Kc) + (n_dec - code.fzs_nb) * 2 * L_ * lg
        w = np.where(s_)[0]
        np.add.at(macs, fr_[w], -tot)
        np.add.at(dmac, fr_[w], -tot)
        np.add.at(dcritp, fr_[w], -cr)
        np.add.at(dcrit, fr_[w], -crd)
        if rounds:                                            # d4a: the rounds not all stopped keep their full length
            rk = np.zeros(len(fr_), int)
            cnt_ = {}
            for q_, f_ in enumerate(fr_.tolist()):
                rk[q_] = cnt_.get(f_, 0)
                cnt_[f_] = rk[q_] + 1
            for u_ in np.unique(fr_[w]):
                m_ = fr_ == u_
                rr_, ss_ = rk[m_] // 4, s_[m_]
                n_all = sum(bool(ss_[rr_ == v_].all()) for v_ in np.unique(rr_))
                d4a[u_] += (ss_.sum() - n_all) * cr
        if p["truth"] is not None:                            # (measurement) right CRC passes the stop lost
            st["fz_stops_right"] += int((np.asarray(ok_, bool)[w] & (d_[w] == p["truth"][fr_[w]]).all(1)).sum())
        st["fz_stops"] += len(w)
        st["macs_fz_saved"] += float(len(w) * tot)
        st[f"fzs_{kind}"] = st.get(f"fzs_{kind}", 0) + len(w)
        st[f"fzs_pos_{code.fzs_pos:04d}"] = st.get(f"fzs_pos_{code.fzs_pos:04d}", 0) + len(w)
        d_[w] = 2
        ok_[w] = False
        return s_

    def _rotst(q_):                                           # (measurement) equiv: CRC passes per accepted rotation
        for v_, n_ in zip(*np.unique(q_, return_counts=True)):
            st[f"rot_{v_}"] = st.get(f"rot_{v_}", 0) + int(n_)

    def _truth(fr, d, ok_crc, ok):                            # (measurement only) CRC passes with wrong data: the
        if p["truth"] is None:                                # first CRC pass of a packet is what a CRC-only receiver
            return                                            # would deliver; the checks' catches and false rejects
        wrong = (d != p["truth"][fr]).any(1)
        st["crc_pass"] = st.get("crc_pass", 0) + int(ok_crc.sum())
        st["crc_pass_wrong"] = st.get("crc_pass_wrong", 0) + int((ok_crc & wrong).sum())
        st["check_caught"] = st.get("check_caught", 0) + int((ok_crc & wrong & ~ok).sum())
        st["check_lost"] = st.get("check_lost", 0) + int((ok_crc & ~wrong & ~ok).sum())
        for n_ in np.where(ok_crc)[0]:
            if not crc_seen[fr[n_]]:
                crc_seen[fr[n_]] = True
                crc_wrong[fr[n_]] = wrong[n_]

    def _fzlog(fr_, fh_, th_, d_, okc_, kind, h_=None):
        """(measurement, fz_diag) the rows of the last CA-SCL call: n frames of code.decode (fh_, th_, d_, okc_ (n,)) or
        ONE decode_joint (fr_ = [i], fh_, th_ its H hypotheses, d_ (1, A), h_ the chosen one). Per row and checkpoint c
        (FZ_Q) every path's frozen-only metric pen / (frozen bits seen) and pen / sum |LLR| (pen = sum |LLR| [LLR < 0]
        over the frozen leaves seen), the path's starting hypothesis and whether its information-bit prefix is the
        transmitted one (traceback through the list; -1 / False with equiv); outcome 0 right (CRC pass, data = truth),
        1 CRC pass wrong, 2 CRC failed; true cell as ref_diag (|res| <= k/2 + 0.5 STEP, phase error mod pi < pi/4)."""
        R = code.fz_rec
        n_, Ls_, C_ = R["pen"].shape
        grp = "j" if kind == 2 else "f"
        LW = FZ_L[grp]
        assert Ls_ <= LW, "fz_diag: lists up to FZ_L paths"
        fr_ = np.asarray(fr_)
        tru = np.asarray(p["truth"])[fr_]
        nb = R["nb"]
        nbx = np.append(nb, len(code._bits))                  # + the final list (in_list: its data bits = truth)
        cmx = np.append(nb, code.A)                           # bits compared per block
        root = np.broadcast_to(np.arange(Ls_), (n_, C_ + 1, Ls_)).copy()   # traceback of every checkpoint's paths
        tm = np.ones((n_, C_ + 1, Ls_), bool)
        if not p["equiv"]:
            ut = np.concatenate([tru, code.crc(tru)], 1).astype(np.uint8)   # transmitted info bits, decoding order
            rows = np.arange(n_)[:, None, None]
            for k_ in range(int(nbx.max()) - 1, -1, -1):
                a_ = (k_ < nbx)[None, :, None]
                c_ = (k_ < cmx)[None, :, None]
                tm &= ~c_ | (code._bits[k_][rows, root] == ut[:, k_][:, None, None])
                root = np.where(a_, code._parents[k_][rows, root], root)
        else:
            tm[:] = False
        in_l = (tm[:, -1] & np.isfinite(code._pm)).any(1)
        root, tm = root[:, :-1], tm[:, :-1]
        al = np.transpose(R["alive"], (0, 2, 1))              # (n, C, Ls)
        tm &= al
        with np.errstate(divide="ignore", invalid="ignore"):
            pn = np.where(al, np.transpose(R["pen"], (0, 2, 1)) / R["cnt"][None, :, None], np.nan)
            pl = np.where(al, np.transpose(R["pen"] / R["mag"], (0, 2, 1)), np.nan)
            ps = np.where(al, np.transpose(R["ps"], (0, 2, 1)), np.nan)   # (the same node: alive_s = alive)
            psn = ps / R["cnt_s"][None, :, None]
        rk = np.zeros(n_, int)                                # rank of the row among its packet's rows in this call
        cnt_ = {}
        for q_, f_ in enumerate(fr_.tolist()):
            rk[q_] = cnt_.get(f_, 0)
            cnt_[f_] = rk[q_] + 1
        rnd, seq = fzr[fr_] + rk // 4, fzc[fr_].copy()       # decode round in the packet (4 decodes at once, as d4a)
        u_, nu_ = np.unique(fr_, return_counts=True)
        fzr[u_] += -(-nu_ // 4)
        fzc[u_] += 1
        fzn[0] += 1

        def pad(x, v):
            y = np.full(x.shape[:-1] + (LW,), v, x.dtype)
            y[..., :x.shape[-1]] = x
            return y

        fh_, th_ = np.asarray(fh_, float), np.asarray(th_, float)
        tf, tt = np.asarray(p["truth_f"])[fr_], np.asarray(p["truth_th"])[fr_] if p["truth_th"] is not None else None
        hr = ((tf[:, None] - fh_.reshape(len(fr_), -1)) / bc.STEP)    # (n, H) residual per hypothesis (STEP)
        he = (((th_.reshape(len(fr_), -1) - tt[:, None]) + np.pi / 2) % np.pi - np.pi / 2 if tt is not None
              else np.full(hr.shape, np.nan))                 # phase error mod pi (PiCode)
        htc = (np.abs(hr) <= k / 2 + 0.5) & (np.abs(he) < np.pi / 4)
        hc = np.zeros(len(fr_), int) if h_ is None else np.full(len(fr_), int(h_))   # the decoded / chosen hypothesis
        ar_ = np.arange(len(fr_))
        rt = np.asarray(okc_, bool) & (np.asarray(d_) == tru).all(1)
        f16 = lambda x: pad(x.astype(np.float16), np.nan)    # per-path metrics: float16 (dump size)
        fzrows.append((grp, dict(
            pk=fr_.astype(np.int32), tag=np.full(n_, DEC_TAGS.get(ctx["tag"], -1), np.int8),
            call=np.full(n_, fzn[0] - 1, np.int16), seq=seq.astype(np.int16), slot=rk.astype(np.int8),
            rnd=rnd.astype(np.int16),
            kind=np.full(n_, kind, np.int8), L=np.full(n_, Ls_, np.int8), H=np.full(n_, hr.shape[1], np.int8),
            hsel=hc.astype(np.int8), out=np.where(rt, 0, np.where(okc_, 1, 2)).astype(np.int8),
            right=rt, crc=np.asarray(okc_, bool).copy(), in_list=in_l,
            res=hr[ar_, hc].astype(np.float32), th_err=he[ar_, hc].astype(np.float16), true_cell=htc[ar_, hc],
            hyp_res=pad(hr.astype(np.float32), np.nan), hyp_tc=pad(htc, False), kstep=np.full(n_, k, np.int8),
            pn=f16(pn), pl=f16(pl), ps=f16(ps), psn=f16(psn),
            pn_min=np.nanmin(pn, 2).astype(np.float32), pn_max=np.nanmax(pn, 2).astype(np.float32),
            pl_min=np.nanmin(pl, 2).astype(np.float32), pl_max=np.nanmax(pl, 2).astype(np.float32),
            psn_min=np.nanmin(psn, 2).astype(np.float32), psn_max=np.nanmax(psn, 2).astype(np.float32),
            alive=pad(al, False), root=pad(root.astype(np.int8), -1), tm=pad(tm, False),
            **{f"{q}{x}": np.tile(R[q + x].astype(np.int16), (n_, 1)) for q in ("cnt", "pos", "nb") for x in ("", "_s")},
            snr_rx=np.full(n_, snr, np.float32))))

    def _rslog(fr_, rc_, d_, fh_, rho_, thr_, src_):           # (measurement) rhos_log rows of n CRC passes
        if not rs_S or p["truth"] is None or not len(fr_):
            return
        rs_ = rho_seg(code, rc_, d_, fh_, rs_S)
        rt_ = (d_ == p["truth"][fr_]).all(1)
        tg_ = DEC_TAGS.get(ctx["tag"], -1)
        st["rhos_rows"].extend([round(float(rho_[n]), 4)] + [round(float(v), 4) for v in rs_[n]]
                               + [round(float(thr_), 4), int(rt_[n]), tg_, int(src_[n]), float(snr)]
                               for n in range(len(fr_)))

    def _flpsn(n_):                                           # (fulllog) psn_min (n, FZ_Q) of the last CA-SCL call: min
        if not fzo:                                           # over the alive paths of the frozen PM increment / frozen
            return np.full((n_, len(FZ_Q)), np.nan, np.float32)   # leaves at the fz_stop rule's node (nan: not reached)
        R_ = code.fz_rec
        import warnings
        with warnings.catch_warnings(), np.errstate(divide="ignore", invalid="ignore"):
            warnings.simplefilter("ignore", RuntimeWarning)
            return np.nanmin(np.where(R_["alive_s"], R_["ps"], np.nan) / R_["cnt_s"][None, None, :], 1).astype(np.float32)

    def _flrow(fr_, kind_, hy_, t_, src_, okm_, okr_, am_, rm_, ar_, rr_, psm_, psr_):
        """(fulllog) n decode-attempt rows: hypothesis (cell, phase offset po in pi/4 units, kind 0 standard / 1
        fine_last), attempt t; main CRC, retry CRC (-1 not run), the main's and the retry's own acceptance (CRC +
        re-encoding check) and right data (valid where its CRC passed), psn_min of both (nan: not run / not reached)."""
        n_ = len(fr_)
        flh.append(dict(pk=np.asarray(fr_, np.int32), cell=np.array([h[0] for h in hy_], np.int16),
                        po=np.array([h[1] for h in hy_], np.int8), kind=np.full(n_, kind_, np.int8),
                        t=np.full(n_, t_, np.int8), src=np.full(n_, src_, np.int8), crc_m=np.asarray(okm_, bool),
                        crc_r=np.asarray(okr_, np.int8), acc_m=np.asarray(am_, bool), right_m=np.asarray(rm_, bool),
                        acc_r=np.asarray(ar_, bool), right_r=np.asarray(rr_, bool), psn_m=np.asarray(psm_, np.float32),
                        psn_r=np.asarray(psr_, np.float32)))

    def _flcap(fr_, okm_, okr_, psm_, psr_, ok_, d_):
        """(fulllog) the search's own decode() call of the hypotheses ctx fl (rows in candidate order: a refine2 round
        decodes every candidate of its call, none accepted before): one row each (src 0)."""
        kind_, hy_ = ctx["fl"]
        n_ = len(fr_)
        if len(hy_) != n_:                                    # (never in the modelled receivers: rows unmatched)
            hy_ = [(-1, -1)] * n_
        okr_ = np.full(n_, -1, np.int8) if okr_ is None else okr_
        psr_ = np.full((n_, len(FZ_Q)), np.nan, np.float32) if psr_ is None else psr_
        rt_ = np.asarray(ok_, bool) & (d_ == p["truth"][fr_]).all(1)
        okm_ = np.asarray(okm_, bool)
        _flrow(fr_, kind_, hy_, ctx["fl_t"], 0, okm_, okr_, ok_ & okm_, rt_ & okm_, ok_ & ~okm_, rt_ & ~okm_,
               psm_, psr_)
        ctx["fl_t"] += 1

    def _pns(fr, fh, th, rc, d, ok, ok_crc, ok_re, lp_, lr_):
        """pns (DEFAULT) on the rows of one decode() call that end failed (~ok: CRC or re-encoding check): the list of
        each row's last decode (lp_ the main / joint list, lr_ = (rows, CFO, phase, list) of the CA retries) ->
        list-weighted symbols -> smoothed phase -> one CA-SCL-8 decode per iteration; an accepted row overwrites d, ok,
        ok_crc, ok_re, fh in place. Returns the rows it fixed."""
        pf = np.zeros(len(fr), bool)
        a = np.where(~ok)[0]
        a = a[~np.isin(fr[a], fr[ok])]                        # never on a packet another row of this call accepted
        if PNSC["max_calls"] is not None and len(a):            # per packet: its first rows in decode order (highest z)
            rk = np.zeros(len(a), int)                        # rank of the row among its packet's rows here
            cnt_ = {}
            for n_, f_ in enumerate(fr[a].tolist()):
                rk[n_] = cnt_.get(f_, 0)
                cnt_[f_] = rk[n_] + 1
            a = a[pns_n[fr[a]] + rk < PNSC["max_calls"]]
        if not len(a) or lp_ is None:
            return pf
        np.add.at(pns_n, fr[a], 1)
        st["pns_calls"] += len(a)
        info, pm = lp_[0][a], lp_[1][a]
        fl, tl = fh[a].copy(), th[a].copy()
        if lr_ is not None:                                   # rows whose last decode was the CA retry: its list and
            jr, fca, tca, (ir, pr) = lr_                      # its hypothesis (fca, tca)
            mp_ = np.full(len(fr), -1)
            mp_[jr] = np.arange(len(jr))
            m_ = mp_[a]
            s_ = m_ >= 0
            if s_.any():
                L_ = max(pm.shape[1], pr.shape[1])
                info, pm = _padl(info, pm, L_)
                ir, pr = _padl(ir, pr, L_)
                info[s_], pm[s_] = ir[m_[s_]], pr[m_[s_]]
                fl[s_], tl[s_] = fca[m_[s_]], tca[m_[s_]]
        inc = np.zeros(len(a), bool)                          # (measurement) the row's hypothesis in the true cell
        if p["truth_f"] is not None:                          # (|f - f_true| <= STEP / 2) and on the right phase branch
            inc = np.abs(fl - p["truth_f"][fr[a]]) <= 0.5 * bc.STEP   # (error mod pi within pi/4, PiCode) if known
            if p["truth_th"] is not None:
                inc &= np.abs((tl - p["truth_th"][fr[a]] + np.pi / 2) % np.pi - np.pi / 2) < np.pi / 4
            st["pns_calls_incell"] = st.get("pns_calls_incell", 0) + int(inc.sum())
        rca = rc[a]
        y = rca * np.exp(-1j * (2 * np.pi * fl[:, None] * bc.NC[None] + tl[:, None]))   # (from the LLRs' de-rotation)
        phi = np.zeros(y.shape)
        act = np.arange(len(a))                               # rows of a still not accepted
        thr = _thr() * (p["spec_rho"] if p["spec_rho"] and ctx["tag"] == "spec" else 1.0)
        for t in range(PNSC["iters"]):
            fa_ = fr[a[act]]
            xb, nl = pns_symbols(code, info, pm, PNSC["soft"])
            phi[act] += pns_phase(y[act] * np.exp(-1j * phi[act]), xb, sigma2, q_pn)
            rcp = rca[act] * np.exp(-1j * phi[act])
            dp, okp, _ = code.decode(bc.llrs(rcp, fl[act], tl[act], sigma2), return_info=True)
            if fzo:                                           # (measurement) fz_diag rows
                _fzlog(fa_, fl[act], tl[act], dp, okp, 3)
            if fzs_on:                                        # fzstop: stopped decodes = CRC failures
                _fzs(fa_, dp, okp, 8, "pns")
            nxt = _plist() if t + 1 < PNSC["iters"] else None   # this decode's list (the next iteration)
            st["decodes"] += len(act)
            st["pns_decodes"] += len(act)
            np.add.at(macs, fa_, pns_re_macs(nl) + PNS_SYM * bc.N_SYM)   # re-encoding, z, smoother, de-rotation:
            np.add.at(seqm, fa_, PNS_KF * bc.N_SYM)          # sample-wise (/ KP) except the smoother's recursion
            np.add.at(seqc, fa_, PNS_KF * bc.N_SYM)          # (sequential)
            _dec_cost(fa_, 8)                                 # the decode, scheduled as the CA retry's
            u_, n_ = np.unique(fa_, return_counts=True)
            d4a[u_] += (np.ceil(n_ / 4) - n_) * dp8
            acc = okp.copy()
            ver = np.zeros(len(act), bool)
            jo = np.where(okp)[0]
            if len(jo):
                rr_ = rcp[jo] if PNSC["rho"] == "corr" else rca[act[jo]]
                rho = bf.reencode_rho(code, rr_, dp[jo], fl[act[jo]])
                ver[jo] = rho > thr
                if p["rhos"]:
                    ver[jo] = rho_seg(code, rr_, dp[jo], fl[act[jo]], (p["rhos"],))[:, 0] > p["rhos_k"] * thr
                    np.add.at(macs, fa_[jo], 8 * bc.N_SYM // p["rhos"])   # |.| and sum per segment (as decode)
                if p["reencode"]:
                    np.add.at(macs, fa_[jo], vp.MAC["reencode"])
                    acc = okp & ver
                _rslog(fa_[jo], rr_, dp[jo], fl[act[jo]], rho, thr, np.full(len(jo), 2))
                if p["truth"] is not None:                    # (measurement) the pns CRC passes and the check
                    wr_ = (dp[jo] != p["truth"][fa_[jo]]).any(1)
                    for k_, v_ in (("pns_crc_pass", len(jo)), ("pns_crc_wrong", wr_.sum()),
                                   ("pns_caught", (wr_ & ~ver[jo]).sum()), ("pns_lost", (~wr_ & ~ver[jo]).sum())):
                        st[k_] = st.get(k_, 0) + int(v_)
            g_ = a[act[acc]]
            if len(g_):
                d[g_], ok[g_], ok_crc[g_], ok_re[g_], fh[g_], pf[g_] = dp[acc], True, True, ver[acc], fl[act[acc]], True
                st["pns_fixed"] += len(g_)
                if p["truth_f"] is not None:                  # (measurement) fixes from an in-cell row
                    st["pns_fixed_incell"] = st.get("pns_fixed_incell", 0) + int(inc[act[acc]].sum())
                if p["truth"] is not None:
                    st["pns_fixed_wrong"] = st.get("pns_fixed_wrong", 0) + int((dp[acc] != p["truth"][fa_[acc]]).any(1).sum())
            kp_ = ~acc & ~np.isin(fa_, fa_[acc])              # next iteration: not on a packet accepted now
            if nxt is not None:
                info, pm = nxt[0][kp_], nxt[1][kp_]
            act = act[kp_]
            if not len(act):
                break
        return pf

    def decode(fr, fh, th, pre=None):
        fr, fh, th = np.asarray(fr), np.asarray(fh, float), np.asarray(th, float)
        c0_ = _cpar(fr) if dd else None                       # (measurement) cost so far (joint: incl. its list decode)
        lm_ = rq_ = None
        lp_ = lr_ = None                                      # (pns) the main / joint list, the CA retries' lists
        hd_ = None                                            # (fzstop, BER only) the stopped rows' own decoder output
        flm_ = flpm_ = flr_ = flpr_ = None                    # (fulllog) main CRC / psn, retry CRC / psn per row
        if pre is not None:                                   # a joint decode's chosen path (decode_joint)
            rc, d, ok = pre
            hd_ = ctx.pop("fz_hd", None)
            lm_ = ctx["jl"]
            if pns_on:
                lp_ = ctx["pns_l"]
        else:
            if p["premf_dec"]:                                # the MF de-rotated at the candidate's own CFO
                rc = bf.premf(r_mf[fr], rx[fr], fh)
                np.add.at(macs, fr, vp.PREMF_FAIR_MACS)
            else:
                rc = r[fr]
            Lm_ = bc.llrs(rc, fh, th, sigma2)
            d, ok, _ = code.decode(Lm_, return_info=True)
            if flo:                                           # (fulllog) the main decodes' CRC and psn_min
                flm_, flpm_ = ok.copy(), _flpsn(len(fr))
            if fzo:                                           # (measurement) fz_diag rows
                _fzlog(fr, fh, th, d, ok, 0)
            if fzs_on:                                        # fzstop: stopped decodes = CRC failures
                hd_ = (d.copy(), ~ok)                         # (BER only) the output before the stop, CRC failed
                _fzs(fr, d, ok, 8, "main")
            if pns_on:
                lp_ = _plist()
            if p["equiv"]:                                    # (measurement) PiCode4's accepted rotations (CRC passes)
                _rotst(code.last_rot[ok])
            if dd:
                lm_ = _lst(Lm_)
            st["decodes"] += len(fr)
            _dec_cost(fr, 8)
            u_, n_ = np.unique(fr, return_counts=True)        # (measurement) d4a: ceil(n / 4) decode rounds
            d4a[u_] += (np.ceil(n_ / 4) - n_) * dp8
        if dd:                                                # (measurement) the main decodes before the retry edits
            dm_, okm_, fhm_ = d.copy(), ok.copy(), fh.copy()  # d / ok / fh in place
        rtry = np.zeros(len(fr), bool)                        # (measurement) CRC failed -> the CA retry ran
        j = np.where(~ok)[0] if p["ca_retry"] else np.zeros(0, int)
        if gate is not None and len(j):                       # retry gate: features of the failed main decodes
            lg_ = lm_ if lm_ is not None else (ctx["jl"] if pre is not None else _lst(Lm_))
            mu_, sd_, w_, b_, t_ = gate
            Xg = np.clip(np.nan_to_num((gate_feats(code, lg_[0][j], lg_[1][j], lg_[2][j]) - mu_) / sd_, nan=0.0),
                         -20, 20)
            sg = Xg @ w_ + b_
            # cost: the list paths' CRCs, the LLR sums, the best path's re-encoding (N/2 log2 N XORs), the score;
            # the parallel serial steps (crit_par: / KP)
            np.add.at(macs, fr[j], GATE_MACS(code, lg_[1].shape[1]))
            st["gate_calls"] = st.get("gate_calls", 0) + len(j)
            st["gate_skip"] = st.get("gate_skip", 0) + int((sg < t_).sum())
            j = j[sg >= t_]
        if len(j):                                            # code-aided CFO / phase from the SC hard decisions
            rtry[j] = True
            c1_ = _cpar(fr[j]) if dd else None                # (measurement) cost so far, before the retry
            u_, n_ = np.unique(fr[j], return_counts=True)     # (measurement) d4a: the retries' SC passes in
            d4a[u_] += (np.ceil(n_ / 4) - n_) * dp8 + (np.ceil(n_ / KP) - n_) * m_met   # parallel, 4 decodes at once
            _, cwh = fs_.metric_cw(bc.llrs(rc[j], fh[j], th[j], sigma2))
            fca, tca = bf.code_aided(rc[j], fh[j], cwh, 2)
            L2_ = bc.llrs(rc[j], fca, tca, sigma2)
            d2, ok2, _ = code.decode(L2_, return_info=True)
            if flo:                                           # (fulllog) the retries' CRC and psn_min
                flr_ = np.full(len(fr), -1, np.int8)
                flr_[j] = ok2
                flpr_ = np.full((len(fr), len(FZ_Q)), np.nan, np.float32)
                flpr_[j] = _flpsn(len(j))
            if fzo:                                           # (measurement) fz_diag rows
                _fzlog(fr[j], fca, tca, d2, ok2, 1)
            if fzs_on:                                        # fzstop: stopped decodes = CRC failures
                _fzs(fr[j], d2, ok2, 8, "retry")
            if pns_on:
                lr_ = (j.copy(), fca, tca, _plist())
            if dd:
                rq_ = (j, fca, tca, _lst(L2_), d2.copy(), ok2.copy(), c1_)
            st["decodes"] += len(j)
            np.add.at(macs, fr[j], m_met + vp.MAC["llr"] + bf.CA_MACS(2))
            np.add.at(seqm, fr[j], m_met)                     # the SC metric of the retry: sequential
            np.add.at(seqc, fr[j], m_met)
            _dec_cost(fr[j], 8)
            d[j[ok2]], ok[j[ok2]], fh[j[ok2]] = d2[ok2], True, fca[ok2]
        ok_crc = ok.copy()
        ok_re = ok.copy()                                     # the re-encoding check's verdict; reencode=False:
        if ok.any():                                          # computed (counted by _truth) but not applied
            j = np.where(ok)[0]
            rho = bf.reencode_rho(code, rc[j], d[j], fh[j])
            s_re = snr + p["re_margin"]                       # re_margin: the threshold at the SNR estimate + a
            s_rl = 10 ** (s_re / 10)                          # margin (an underestimated SNR must not lower it)
            thr = bf.rho_min(s_re)
            if tab:
                thr = max(thr, float(np.interp(s_re, *zip(*tab))) * np.sqrt(s_rl / (1 + s_rl)))
            ok_re[j] = rho > (thr * p["spec_rho"] if p["spec_rho"] and ctx["tag"] == "spec" else thr)
            if p["rhos"]:                                     # segment check instead (DEFAULT rhos)
                ok_re[j] = rho_seg(code, rc[j], d[j], fh[j], (p["rhos"],))[:, 0] > p["rhos_k"] * (
                    thr * p["spec_rho"] if p["spec_rho"] and ctx["tag"] == "spec" else thr)
                np.add.at(macs, fr[j], 8 * bc.N_SYM // p["rhos"])   # |.| and sum per segment
            if rs_S:                                          # (measurement) rhos_log
                _rslog(fr[j], rc[j], d[j], fh[j], rho, thr * p["spec_rho"] if p["spec_rho"] and ctx["tag"] == "spec"
                       else thr, rtry[j].astype(int))       # (the threshold applied: spec_rho on spec rows)
            if p["truth"] is not None and ctx["tag"] in ("spec", "win"):   # (measurement) rho / threshold of the
                wr_ = (d[j] != p["truth"][fr[j]]).any(1)                     # right / wrong CRC passes
                b_ = np.clip(np.floor(rho / thr / (3.0 / RHO_B)), 0, RHO_B - 1).astype(int)
                for w_, nm_ in ((False, "right"), (True, "wrong")):
                    for bb_, nn_ in zip(*np.unique(b_[wr_ == w_], return_counts=True)):
                        key_ = f"rho_{ctx['tag']}_{nm_}_{bb_:02d}"
                        st[key_] = st.get(key_, 0) + int(nn_)
            if p["reencode"]:
                np.add.at(macs, fr[j], vp.MAC["reencode"])
                ok = ok_re.copy()
        pfix = np.zeros(len(fr), bool)                        # (pns) rows accepted by the phase-tracking retry
        tr_ = None                                            # (pns) _truth on the verdicts before it (no pilots)
        if pns_on and (PNSC["spec"] or ctx["tag"] != "spec"):   # every row still failed here (CRC or re-encoding
            tr_ = (d.copy(), ok_crc.copy(), (ok if p["reencode"] else ok & ok_re).copy())   # check, main or CA retry)
            pfix = _pns(fr, fh, th, rc, d, ok, ok_crc, ok_re, lp_, lr_)   # is a failed decode
        if pos is not None and ok.any():
            j = np.where(ok)[0]
            np.add.at(macs, fr[j], 2 * vp.MAC["cmul"] * len(pos))
            zpj = rc[j][:, pos] * np.conj(sym[fr[j]][:, pos])
            c = bf.pilot_coherent(code, rc[j], d[j], fh[j], zpj, pos)
            ok[j] = c > len(pos) - p["pc_sigmas"] * np.sqrt(len(pos) / (2 * s_lin))
        if tr_ is not None:                                   # (pns passes: their own pns_crc_* counters)
            _truth(fr, *tr_)
        else:
            _truth(fr, d, ok_crc, ok if p["reencode"] else ok & ok_re)
        if p["truth"] is not None and ok.any():               # (measurement) accepted packets per origin, main
            ia_ = np.where(ok)[0]                             # decode / CA retry, right / wrong: once per packet
            u_, inv_, cnt_ = np.unique(fr[ia_], return_inverse=True, return_counts=True)   # per call, by the row
            dl_ = np.zeros(len(u_), int)                      # delivered (out[w] = d[ok]: the last accepted row)
            np.maximum.at(dl_, inv_, ia_)
            wr_ = (d[dl_] != p["truth"][fr[dl_]]).any(1)
            rt_, pf_ = rtry[dl_] & ~pfix[dl_], pfix[dl_]   # (pns: its own origin; pfix all False without it)
            for m_, nm_ in ((~rt_ & ~pf_ & ~wr_, "main_right"), (~rt_ & ~pf_ & wr_, "main_wrong"),
                            (rt_ & ~wr_, "retry_right"), (rt_ & wr_, "retry_wrong"),
                            (pf_ & ~wr_, "pns_right"), (pf_ & wr_, "pns_wrong")):
                if m_.any():
                    st[f"acc_{ctx['tag']}_{nm_}"] = st.get(f"acc_{ctx['tag']}_{nm_}", 0) + int(m_.sum())
            if (cnt_ > 1).any():                              # calls accepting > 1 hypothesis of one packet
                st["acc_multi"] = st.get("acc_multi", 0) + int((cnt_ > 1).sum())
        if ctx["log"] is not None:                            # (measurement) d4b: (retried, accepted at the main
            ctx["log"] += list(zip((rtry | pfix).tolist(), (ok & ~rtry & ~pfix).tolist(), ok.tolist()))   # decode,
                                                              # accepted; a pns fix counts as retried)
        if dd and lm_ is not None:                            # (measurement) decode dump rows
            _dlog(fr, fhm_, th, rc, lm_, dm_, okm_, rq_, ok, rtry, c0_)
        if flo and pre is None and ctx["fl"] is not None:     # (fulllog) the search's decodes of its hypotheses
            _flcap(fr, flm_, flr_, flpm_, flpr_, ok, d)
        first = ~have[fr]
        do_ = d                                               # (fzstop) a stopped row delivers 2s (conservative: a real
        if hd_ is not None and p["truth"] is not None:        # stopped decoder never computes the rest; verifier B4)
            s_ = (d == 2).all(1) & hd_[1]                     # (measurement only, upper bound) stopped CRC-failed rows
            if s_.any():                                      # whose full decode had right data bits
                st["fzs_hd_right"] = st.get("fzs_hd_right", 0) + int(
                    (first & s_ & (hd_[0] == p["truth"][fr]).all(1)).sum())
        out[fr[first]], have[fr[first]], f_fin[fr[first]] = do_[first], True, fh[first]
        w = fr[ok]
        out[w], passed[w], f_fin[w] = d[ok], True, fh[ok]
        return ok

    def decode_joint(i, fh, th):
        """Packet i: H hypotheses (CFO fh, phase th) in ONE CA-SCL decode with a shared list of joint[1] paths,
        pruned over all of them (on the cores: 4 hypotheses x 8 paths = 32); the chosen path then gets the usual
        code-aided retry / re-encoding / pilot checks."""
        H, Lj = len(fh), p["joint"][1]
        fr = np.full(H, i)
        if p["premf_dec"]:
            rc = bf.premf(r_mf[fr], rx[fr], fh)
            macs[i] += H * vp.PREMF_FAIR_MACS
        else:
            rc = r[fr]
        Lj_ = bc.llrs(rc, fh, th, sigma2)
        d, ok, _, h = code.decode_joint(Lj_, Lj)
        if fzo:                                               # (measurement) fz_diag: one row, the shared list
            _fzlog(fr[:1], fh, th, d[None], np.array([ok]), 2, h)
        if fzs_on:                                            # fzstop: the shared list stopped = a CRC failure (one
            d_, ok_ = d[None].copy(), np.array([ok])          # decode, no 4-decode rounds)
            ctx["fz_hd"] = (d[None].copy(), ~ok_)             # (BER only) the output before the stop (decode's out)
            _fzs(fr[:1], d_, ok_, Lj, "joint", rounds=False)
            d, ok = d_[0], bool(ok_[0])
        if rdo:                                               # (measurement) ref_diag: the chosen hypothesis
            ctx["rd_h"] = int(h)
        if pns_on:                                            # (pns) the shared list's paths of hypothesis h
            ctx["pns_l"] = _plist(h)
        if p["equiv"] and ok:                                # (measurement) PiCode4's accepted rotation
            _rotst(code.last_rot)
        if dd or gate is not None:                            # the shared list, the chosen hypothesis' LLRs (decode
            ctx["jl"] = _lst(Lj_[h:h + 1])                    # LLRs (decode dump)
        st["decodes"] += Lj / 8                               # in CA-SCL-8 decode equivalents
        st["joint_decodes"] = st.get("joint_decodes", 0) + 1
        _dec_cost(fr[:1], Lj, H)
        return decode(fr[:1], fh[h:h + 1], th[h:h + 1], pre=(rc[h:h + 1], d[None].copy(), np.array([ok])))

    def refine_joint(i, cands):
        """As bf._refine2 for up to joint[2] candidate cells (CFO, phase) of packet i at once: every offset x phase
        sub-offset scored (in parallel), the best joint[0] hypotheses of each cell decoded jointly (decode_joint)."""
        f_ = np.array([c[0] for c in cands])
        t_ = np.array([c[1] for c in cands])
        ctx["sc"], ctx["H"] = None, (len(roffs) * len(sub), len(sub))   # (measurement) decode dump: score layout
        if p["s3_dd"]:                                        # experiment R1: each cell's 2 hypotheses are the
            fr = np.full(len(cands), i)                       # code-aided one (re-encoded SC codeword) and the cell
            _, cw = fs_.metric_cw(bc.llrs(r[fr], f_, t_, sigma2))   # itself, instead of the best 2 of the scored
            c1 = m_met + derot                                # offsets
            st["metric_evals"] += len(fr)
            st["macs_score"] = st.get("macs_score", 0.0) + len(fr) * (c1 + bf.CA_MACS(2))
            macs[i] += len(fr) * (c1 + bf.CA_MACS(2))
            pmac[i] += len(fr) * c1
            crit[i] += np.ceil(len(fr) / Kc) * c1
            fca, tca = bf.code_aided(r[fr], f_, cw, 2)
            fca = np.clip(fca, -bc.MAX_CFO, bc.MAX_CFO)
            F = np.stack([fca, f_], 1)[:, :p["joint"][0]]
            TH = np.stack([tca, t_], 1)[:, :p["joint"][0]]
            decode_joint(i, F.ravel(), TH.ravel())
            return
        F = f_[:, None] + roffs[None] * bc.STEP
        if p["bpsk_sq"]:                                      # (blind_fmt) the square's phase, on the cell's branch mod pi
            TH = bc.phase2(r[np.full(len(cands), i)], F)
            TH = TH + np.round((t_[:, None] - TH) / np.pi) * np.pi
        else:
            TH = bc.phase4(r[np.full(len(cands), i)], F)
            TH = TH + np.round((t_[:, None] - TH) / (np.pi / 2)) * (np.pi / 2)
        F = np.repeat(F, len(sub), 1)
        TH = (TH[:, :, None] + np.array(sub)[None, None]).reshape(len(cands), -1)
        M = score(np.full(F.size, i), F.ravel(), TH.ravel()).reshape(F.shape)
        o = np.argsort(M, 1)[:, :p["joint"][0]]
        okj = decode_joint(i, np.take_along_axis(F, o, 1).ravel(), np.take_along_axis(TH, o, 1).ravel())
        if rdo:                                               # (measurement) ref_diag: every cell's best joint[0]
            J_ = p["joint"][0]                                # entered the list; the accepted one = the chosen h
            act_ = np.full(len(cands), -1)
            if bool(np.asarray(okj).any()) and ctx["rd_h"] is not None:
                act_[ctx["rd_h"] // J_] = ctx["rd_h"] % J_
            _rdlog(np.full(len(cands), i), f_, t_, roffs, sub, F, TH, M, np.full(len(cands), J_), act_)

    def score(fr, fh, th):
        M = fs_.metric(bc.llrs(r[fr], fh, th, sigma2))
        st["metric_evals"] += len(fr)
        np.add.at(n_hyp, fr, 1)                               # (measurement) stage_acc
        st["macs_score"] = st.get("macs_score", 0.0) + len(fr) * (m_met + derot)   # (measurement) Stage 3 scoring
        np.add.at(macs, fr, m_met + derot)
        u, n_ = np.unique(fr, return_counts=True)             # independent hypotheses: in parallel on the cores
        pmac[u] += n_ * (m_met + derot)
        crit[u] += np.ceil(n_ / Kc) * (m_met + derot)
        if dd:                                                # (measurement) decode dump: the scored hypotheses
            ctx["sc"] = (np.asarray(fr), np.asarray(fh, float), np.asarray(th, float), M)
        return M

    def _s3dump(cand, roffs_, sub_):
        """(measurement, BLIND_IMPLEMENTATION/testing/) the hypotheses bf._refine2 is about to rank: for the best s3dump_top of each
        candidate by the list-1 metric, the SC codeword's correlation with r, the distance to the true CFO / phase and
        the outcome of a CA-SCL-8 decode of every one of them (all 8 list paths), outside the receiver's MAC count and
        decisions."""
        fr = np.array([c[0] for c in cand])
        f = np.array([c[1] for c in cand])
        th = np.array([c[2] for c in cand])
        F = f[:, None] + roffs_[None] * bc.STEP
        TH = bc.phase4(r[fr], F)
        TH = TH + np.round((th[:, None] - TH) / (np.pi / 2)) * (np.pi / 2)
        F = np.repeat(F, len(sub_), 1)
        TH = (TH[:, :, None] + np.array(sub_)[None, None]).reshape(len(fr), -1)
        H = F.shape[1]
        frr = np.repeat(fr, H)
        M, cw = fs_.metric_cw(bc.llrs(r[frr], F.ravel(), TH.ravel(), sigma2))
        b = cw[:, bc.INTERLEAVER]
        s_sc = ((1 - 2.0 * b[:, 0::2]) + 1j * (1 - 2.0 * b[:, 1::2])) / np.sqrt(2)
        en = np.sqrt(bc.N_SYM * np.sum(np.abs(r[frr]) ** 2, 1))
        zr = r[frr] * np.conj(s_sc) * np.exp(-2j * np.pi * F.ravel()[:, None] * bc.NC[None])
        rho_sc = np.abs(zr.sum(1)) / en
        M, rho_sc = M.reshape(len(fr), H), rho_sc.reshape(len(fr), H)
        o = np.argsort(M, 1)
        s_re = snr + p["re_margin"]
        s_rl = 10 ** (s_re / 10)
        thr = bf.rho_min(s_re)
        if tab:
            thr = max(thr, float(np.interp(s_re, *zip(*tab))) * np.sqrt(s_rl / (1 + s_rl)))
        for ci in range(len(fr)):
            i = fr[ci]
            hs = o[ci, :p["s3dump_top"]]
            fh, thh = F[ci, hs], TH[ci, hs]
            frs = np.full(len(hs), i)
            rc = bf.premf(r_mf[frs], rx[frs], fh) if p["premf_dec"] else r[frs]
            d, ok, pm = code.decode(bc.llrs(rc, fh, thh, sigma2), return_info=True)
            ld, lok, lpm = code.last_list                     # (H, L, A), (H, L), (H, L)
            tru = p["truth"][i]
            corr_sel = (d == tru).all(1)
            in_list = (ld == tru[None, None]).all(2).any(1)
            rho = bf.reencode_rho(code, rc, d, fh)
            c_ = code.encode(d)[:, bc.INTERLEAVER]
            s_ = ((1 - 2.0 * c_[:, 0::2]) + 1j * (1 - 2.0 * c_[:, 1::2])) / np.sqrt(2)
            z = rc * np.conj(s_) * np.exp(-2j * np.pi * fh[:, None] * bc.NC[None])
            c1, c2 = z[:, :bc.N_SYM // 2].sum(1), z[:, bc.N_SYM // 2:].sum(1)
            dF = fh - p["truth_f"][i] if p["truth_f"] is not None else np.full(len(hs), np.nan)
            dT = (((thh - p["truth_th"][i]) + np.pi / 2) % np.pi - np.pi / 2 if p["truth_th"] is not None
                  else np.full(len(hs), np.nan))              # phase error mod pi (PiCode)
            for j, h in enumerate(hs):
                s3rows.append((uid[i], len(s3rows), j, M[ci, h], M[ci, o[ci, 0]], rho_sc[ci, h], dF[j], dT[j],
                               ok[j], ok[j] and rho[j] > thr, corr_sel[j], in_list[j], int(lok[j].sum()), rho[j],
                               np.abs(c1[j]) / en[0], np.abs(c2[j]) / en[0], np.angle(c1[j] * np.conj(c2[j])),
                               thr, snr))

    def refine_dd(cand, T):
        """Experiment R1 (s3_dd): each candidate (frame, cell CFO, phase) gets ONE list-1 SC pass with hard decisions
        at the cell hypothesis; its codeword, re-modulated, strips the data off r (z = r s*), and 2 Newton steps on
        |sum z e^{-j 2 pi f nc}| give the CFO and the phase (bf.code_aided, as the CA retry). CA-SCL then decodes that
        hypothesis first and the cell hypothesis itself second (T = 2), stopping at an accepted decode. Replaces the
        roffs x sub grid of list-1 metric passes (15 below -1 dB, 5 above) by 1 pass + the code-aided sums."""
        fr = np.array([c[0] for c in cand])
        f = np.array([c[1] for c in cand], float)
        th = np.array([c[2] for c in cand], float)
        _, cw = fs_.metric_cw(bc.llrs(r[fr], f, th, sigma2))
        st["metric_evals"] += len(fr)
        c1 = m_met + derot                                    # the SC passes: in parallel on the cores (as score)
        st["macs_score"] = st.get("macs_score", 0.0) + len(fr) * (c1 + bf.CA_MACS(2))
        np.add.at(macs, fr, c1 + bf.CA_MACS(2))               # + the code-aided sums: sample-wise, serial (/KP)
        u, n_ = np.unique(fr, return_counts=True)
        pmac[u] += n_ * c1
        crit[u] += np.ceil(n_ / Kc) * c1
        fca, tca = bf.code_aided(r[fr], f, cw, 2)
        fca = np.clip(fca, -bc.MAX_CFO, bc.MAX_CFO)
        hyp = [(fca, tca), (f, th)]
        act = np.ones(len(fr), bool)
        for t in range(min(T, len(hyp))):
            j = np.where(act & ~passed[fr])[0]
            if not len(j):
                break
            ok = decode(fr[j], hyp[t][0][j], hyp[t][1][j])
            act[j[ok]] = False

    def refine_ddr(cand, sub_, T, pd_=None):
        """ddref (DEFAULT): each candidate (frame, cell CFO, phase) gets ONE list-1 SC pass at the cell centre; its
        hard-decision codeword strips the data off r (z = r s*) and 2 Newton steps on |sum z e^{-j 2 pi f nc}| give
        (f_dd, theta_dd) (bf.code_aided, as the CA retry); the hypotheses f_dd x (theta_dd + sub_) are scored with the
        list-1 metric (when more than one) and the best min(T, ddref_T) decoded, stopping at an accepted decode (as
        bf._refine2). pd_ (n,) bool: the centre hypothesis was decoded to full length by the search (its SC hard
        decisions are a by-product: the pass is not charged again; None = none). Returns the candidates none of whose
        DD hypotheses was accepted (packet not passed): the grid's fallback."""
        fr = np.array([c[0] for c in cand])
        f = np.array([c[1] for c in cand], float)
        th = np.array([c[2] for c in cand], float)
        n_ = len(fr)
        _, cw = fs_.metric_cw(bc.llrs(r[fr], f, th, sigma2))
        pd_ = np.zeros(n_, bool) if pd_ is None else np.asarray(pd_, bool)
        st["metric_evals"] += int((~pd_).sum())
        c1 = m_met + derot                                    # the SC passes at the cell centres not paid by the
        cc = np.where(pd_, 0.0, c1)                           # search: in parallel on the cores (as score); the
        np.add.at(macs, fr, cc + bf.CA_MACS(2))               # Newton sums sample-wise (/ KP)
        u, nu_ = np.unique(fr[~pd_], return_counts=True)
        pmac[u] += nu_ * c1
        crit[u] += np.ceil(nu_ / Kc) * c1
        st["macs_ddref"] += float(cc.sum() + n_ * bf.CA_MACS(2))
        st["ddref_paid"] += int(pd_.sum())
        fdd, tdd = bf.code_aided(r[fr], f, cw, 2)
        fdd = np.clip(fdd, -bc.MAX_CFO, bc.MAX_CFO)
        for b_ in np.minimum((np.abs(fdd - f) / bc.STEP / 0.5).astype(int), 20):   # (measurement) the DD jump
            st[f"ddref_jump_{b_:02d}"] = st.get(f"ddref_jump_{b_:02d}", 0) + 1     # (0.5-STEP bins, >= 10 STEP: 20)
        if p["ddref_T"] is not None:
            T = min(T, int(p["ddref_T"]))
        F = np.repeat(fdd[:, None], len(sub_), 1)
        TH = tdd[:, None] + np.array(sub_, float)[None]
        H = F.shape[1]
        o = (np.argsort(score(np.repeat(fr, H), F.ravel(), TH.ravel()).reshape(n_, H), 1) if H > 1
             else np.zeros((n_, 1), int))                     # (one hypothesis: nothing to rank)
        act = np.ones(n_, bool)
        for t in range(min(T, H)):
            j = np.where(act & ~passed[fr])[0]
            if not len(j):
                break
            ok = decode(fr[j], F[j, o[j, t]], TH[j, o[j, t]])
            act[j[ok]] = False
        left = [cand[q] for q in range(n_) if act[q] and not passed[fr[q]]]
        st["ddref_cells"] += n_
        st["ddref_hit"] += int((~act).sum())
        st["ddref_fallback"] += len(left)
        return left

    def lm_rank(i, alive_, qal_, th_, adj_, cache):
        """lmarg (DEFAULT): the list-marginalised metric -log sum_l exp(-PM_l) (fastscl, L_e paths, up to fr_lm) of every
        surviving (cell, phase) hypothesis of packet i (alive_ cells x their phases qal_, cell phases th_ + qs pi/4);
        hypotheses not in cache ((cell, phase index) -> metric, per packet) are decoded and charged: macs, and as a
        grid stage (_par: one core per hypothesis in crit_gh, per cell in crit). Returns the cells' best metric + adj_
        (inf for the dead cells) and its phase index (into qs)."""
        Hs = [(int(c), int(q)) for c, q in np.argwhere(alive_[:, None] & qal_)]
        nw = [h for h in Hs if h not in cache]
        st["lm_calls"] += 1
        if nw:
            nw_ = np.array(nw)
            Ln_ = bc.llrs(np.repeat(r[i:i + 1], len(nw_), 0), g[nw_[:, 0]], th_[nw_[:, 0]] + qs[nw_[:, 1]] * np.pi / 4,
                          sigma2)
            _, pmc_ = dec_lm.decode(Ln_, cut_lm, stop=True)
            for h, v in zip(nw, fastscl.lse_metric(pmc_)):
                cache[h] = float(v)
            _, nh_ = np.unique(nw_[:, 0], return_counts=True)
            macs[i] += len(nw_) * c_lmh
            _par(i, nh_ * c_lmh, nh_)                         # (the cell's cost split over its nh_ hypotheses)
            st["lm_hyp"] += len(nw_)
            st["macs_lm"] += float(len(nw_) * c_lmh)
        Mc, qc = np.full(len(g), np.inf), np.zeros(len(g), int)
        for c, q in Hs:
            v = cache[(c, q)] + adj_[c]
            if v < Mc[c]:
                Mc[c], qc[c] = v, q
        return Mc, qc

    def _rdlog(frs, fc, tc, roffs_, sub_, F, TH, M, ndec, acct):
        """(measurement, ref_diag) rows of the n candidate cells (frames frs, cell CFO fc, phase tc) of one Stage 3
        refinement: its hypotheses F, TH and list-1 metrics M (n, H = offsets x sub-offsets), ndec the hypotheses
        decoded (refine2) / entered in the joint list (refine_joint), acct the accepted one's metric rank (-1 none).
        Per cell, besides the grid: (1) Newton on Lambda4 from 4 fc (y4 = -r^4 of the fast path: free), 1 and 2 steps,
        clamped to the cell (+-k/2 STEP); (2a) the parabola through the stored checkpoint PMs of the cell and its 2
        neighbour cells (the last checkpoint all 3 reached, each cell's decoded phase nearest tc mod pi); (2b) the
        parabola through the grid's 3 offsets around its best (best sub-offset each); (3) bf.code_aided (2 Newton
        steps) on the list-1 SC codeword at the cell centre, from fc (ddc) / at the grid's best hypothesis, from it (ddb).
        Residuals (f_true - f_est) / STEP; MACs per method (vp.MAC model), outside the receiver's counters."""
        n_, H_ = M.shape
        ar = np.arange(n_)
        ro = np.asarray(roffs_, float)
        no, ns = len(ro), len(sub_)
        nan = np.full(n_, np.nan)
        tf = np.asarray(p["truth_f"])[frs]
        res = (tf - fc) / bc.STEP                             # truth residual of the cell (STEP)
        dT = ((tc - np.asarray(p["truth_th"])[frs] + np.pi / 2) % np.pi - np.pi / 2 if p["truth_th"] is not None
              else nan)                                       # phase error mod pi (PiCode)
        inc, bro = np.abs(res) <= k / 2 + 0.5, np.abs(dT) < np.pi / 4
        tru = inc & bro                                       # the true cell, on the right pi/2 branch
        nea = np.abs(res) <= k / 2                            # the cell nearest the truth (inc overlaps at k = 2)
        o = np.argsort(M, 1)
        rb0 = (tf - F[ar, o[:, 0]]) / bc.STEP                 # grid: the best / 2nd best scored hypothesis
        rb1 = (tf - F[ar, o[:, 1]]) / bc.STEP if H_ > 1 else nan
        Mo = M.reshape(n_, no, ns).min(2)                     # (2b) best sub-offset per offset
        ob = Mo.argmin(1)
        r2b, n2b, c2b, e2b = nan.copy(), np.zeros(n_, bool), np.zeros(n_, bool), np.zeros(n_, bool)
        if no >= 3:
            cen = np.clip(ob, 1, no - 2)                      # (best offset at the grid edge: the edge triple)
            dl_ = (ro[1] - ro[0]) * bc.STEP
            x_, n2b, c2b = rd_parab(Mo[ar, cen - 1], Mo[ar, cen], Mo[ar, cen + 1], dl_)
            r2b, e2b = (tf - (fc + ro[cen] * bc.STEP + x_)) / bc.STEP, cen != ob
        nu_, n1, c1 = rd_newton4(y4[frs], 4 * fc, 2, 4 * (k / 2) * bc.STEP)   # (1) 4th-power Newton
        r1 = (tf[None] - nu_ / 4) / bc.STEP
        r2a, m2a, n2a, c2a, j2a = nan.copy(), np.full(n_, 3), np.zeros(n_, bool), np.zeros(n_, bool), np.full(n_, -1)
        q2a = np.full((n_, 3), -1)                            # phase index (into qs) used per cell c-1, c, c+1
        G_ = ctx["rdg"]                                       # (2a) the stored checkpoint PMs of the packet's grid
        for q in range(n_):
            if G_ is None or G_[0] != frs[q]:
                continue
            _, Pq_, qal_, paid_, th_ = G_
            c = int(np.abs(g - fc[q]).argmin())
            if abs(g[c] - fc[q]) > 1e-3 * bc.STEP:            # (not a grid cell)
                continue
            nb = [n for n in (c - 1, c, c + 1) if 0 <= n < len(g)]
            jj = np.where(paid_[nb].min() >= sh - 1e-9)[0] if len(nb) == 3 else []   # the last checkpoint all 3
            if not len(jj):                                   # cells reached; none: the cells missing at the cell's
                jc_ = np.where(paid_[c] >= sh - 1e-9)[0]      # own last one counted
                m2a[q] = 3 if not len(jc_) else (3 - len(nb)) + sum(paid_[n] < sh[jc_[-1]] - 1e-9 for n in nb)
                continue
            j = int(jj[-1])
            J = []
            for u, n in enumerate((c - 1, c, c + 1)):         # each cell's decoded phase nearest tc (mod pi)
                v = np.nan
                dph = np.abs((th_[n] + qs * np.pi / 4 - tc[q] + np.pi / 2) % np.pi - np.pi / 2)
                dph = np.where(qal_[n], dph, np.inf)
                if np.isfinite(dph).any():
                    q2a[q, u] = int(dph.argmin())
                    v = float(Pq_[q2a[q, u], n, j])
                J.append(v)
            m2a[q], j2a[q] = int(np.isnan(J).sum()), j
            if not m2a[q]:
                x_, nc_, cl_ = rd_parab(*(np.array([v]) for v in J), k * bc.STEP)
                r2a[q], n2a[q], c2a[q] = (tf[q] - fc[q] - x_[0]) / bc.STEP, nc_[0], cl_[0]
        hb = o[:, 0]                                          # (3) DD Newton (log-only SC passes here)
        _, cw_ = fs_.metric_cw(np.concatenate([bc.llrs(r[frs], fc, tc, sigma2),
                                               bc.llrs(r[frs], F[ar, hb], TH[ar, hb], sigma2)]))
        ctr = code.encode(np.asarray(p["truth"])[frs]).astype(bool)
        fdc, _ = bf.code_aided(r[frs], fc, cw_[:n_], 2)
        fdb, _ = bf.code_aided(r[frs], F[ar, hb], cw_[n_:], 2)   # (from the hypothesis its codeword was decoded at)
        rdc, rdb = (tf - fdc) / bc.STEP, (tf - fdb) / bc.STEP
        hc, hbk = (cw_[:n_] == ctr).mean(1), (cw_[n_:] == ctr).mean(1)   # raw; max(h, 1 - h): the pi ambiguity
        # MACs per cell (vp.MAC model): the grid as counted by score; Newton 20 N per step (3 sums + exponentials, as
        # CA_MACS), y4 free (the fast path's); parabolas ~8 (2a: the neighbours' PMs stored); ddc one SC pass at the
        # cell + code_aided(2); ddb code_aided(2) only (the best hypothesis' codeword kept from its scoring pass);
        # m1 / m2 give no phase: + phase4 at the proposed f (dd gives it); use_score: scoring a proposed f (de-rotation
        # + list-1 metric), use_dec: decoding at it (llr: its de-rotation included)
        ph4 = vp.MAC["phase4"]
        cst = dict(grid=H_ * (m_met + derot), m1a=20 * bc.N_SYM + ph4, m1b=40 * bc.N_SYM + ph4, m2a=8.0 + ph4,
                   m2b=8.0 + ph4, ddc=m_met + derot + bf.CA_MACS(2), ddb=bf.CA_MACS(2), use_score=derot + m_met,
                   use_dec=vp.MAC["llr"])
        Mp = np.full((n_, RD_HMAX), np.nan, np.float32)
        Mp[:, :min(H_, RD_HMAX)] = M[:, :RD_HMAX]
        rdrows.append(dict(
            pk=np.asarray(frs, np.int32), tag=np.full(n_, DEC_TAGS.get(ctx["tag"], -1), np.int8),
            ci=ar.astype(np.int8), n_c=np.full(n_, n_, np.int8), kstep=np.full(n_, k, np.int8),
            n_off=np.full(n_, no, np.int8), n_sub=np.full(n_, ns, np.int8), off0=np.full(n_, ro[0], np.float32),
            doff=np.full(n_, ro[1] - ro[0] if no > 1 else 0.0, np.float32),
            f_c=fc.astype(np.float32), res=res.astype(np.float32), th_err=dT.astype(np.float16),
            in_cell=inc, branch_ok=bro, true_cell=tru, nearest=nea, m_grid=Mp, m_off=Mo.min(1).astype(np.float32),
            o0=o[:, 0].astype(np.int8), o1=(o[:, 1] if H_ > 1 else np.full(n_, -1)).astype(np.int8),
            res_b0=rb0.astype(np.float32), res_b1=rb1.astype(np.float32),
            n_dec=np.asarray(ndec, np.int8), acc_t=np.asarray(acct, np.int8),
            res_m1a=r1[0].astype(np.float32), res_m1b=r1[1].astype(np.float32),
            m1_flat=n1.T.astype(bool), m1_clamp=c1.T.astype(bool),
            res_m2a=r2a.astype(np.float32), m2a_miss=m2a.astype(np.int8), m2a_ck=j2a.astype(np.int8),
            m2a_q=q2a.astype(np.int8),
            m2a_ncvx=n2a, m2a_clamp=c2a,
            res_m2b=r2b.astype(np.float32), m2b_ncvx=np.asarray(n2b, bool), m2b_clamp=np.asarray(c2b, bool),
            m2b_edge=np.asarray(e2b, bool),
            res_ddc=rdc.astype(np.float32), res_ddb=rdb.astype(np.float32),
            hd_ddc=np.maximum(hc, 1 - hc).astype(np.float32), hd_ddb=np.maximum(hbk, 1 - hbk).astype(np.float32),
            hd_ddc_raw=hc.astype(np.float32), hd_ddb_raw=hbk.astype(np.float32),
            **{f"mac_{q}": np.full(n_, v, np.float32) for q, v in cst.items()}))
        st["rd_rows"] = st.get("rd_rows", 0) + n_             # counters: rms / within 0.5 STEP on the true-cell rows
        st["rd_rows_true"] = st.get("rd_rows_true", 0) + int(tru.sum())
        st["rd_rows_acc"] = st.get("rd_rows_acc", 0) + int((np.asarray(acct) >= 0).sum())
        st["rd_rows_true_acc"] = st.get("rd_rows_true_acc", 0) + int((tru & (np.asarray(acct) >= 0)).sum())
        for nm, e in (("cell", res), ("grid", rb0), ("m1a", r1[0]), ("m1b", r1[1]), ("m2a", r2a), ("m2b", r2b),
                      ("ddc", rdc), ("ddb", rdb)):
            v = e[tru & np.isfinite(e)]
            st[f"rd_n_{nm}"] = st.get(f"rd_n_{nm}", 0) + int(len(v))
            st[f"rd_se_{nm}"] = st.get(f"rd_se_{nm}", 0.0) + float((v ** 2).sum())
            st[f"rd_in05_{nm}"] = st.get(f"rd_in05_{nm}", 0) + int((np.abs(v) <= 0.5).sum())
        for nm, v in (("m1_flat1", n1[0]), ("m1_flat2", n1[1]), ("m1_clamp2", c1[1]), ("m2a_missing", m2a > 0),
                      ("m2a_ncvx", n2a), ("m2b_ncvx", n2b), ("m2b_edge", e2b)):
            st[f"rd_{nm}"] = st.get(f"rd_{nm}", 0) + int(np.sum(v))
        st["rd_m2a_miss_n"] = st.get("rd_m2a_miss_n", 0) + int(m2a.sum())   # missing PMs (of 3 per row)
        for q, v in cst.items():
            st[f"rd_mac_{q}"] = st.get(f"rd_mac_{q}", 0.0) + float(n_ * v)

    def refine2(*a):                                          # bf._refine2, with the BLIND_IMPLEMENTATION/testing/ Stage 3 dump
        if p["s3dump"] is not None and p["truth"] is not None:
            _s3dump(a[0], a[1], a[2])
        ctx["sc"], ctx["H"] = None, (len(a[1]) * len(a[2]), len(a[2]))   # (measurement) decode dump: score layout
        if p["s3_dd"] and a[1] is roffs:                     # (the fine_last rescue keeps its own fine grid)
            return refine_dd(a[0], a[3])
        pd_ = ctx.pop("ddp", None)                            # (ddref) the caller's paid flags of these candidates
        if (ddo and a[1] is roffs and not ctx.get("ddfb")    # ddref: the DD hypotheses first; the candidates they do
                and (p["ddref_tags"] is None or ctx["tag"] in p["ddref_tags"])):   # not deliver get this grid
            left = refine_ddr(a[0], a[2], a[3], pd_)          # refinement (fallback)
            if left:
                ctx["ddfb"] = True
                try:
                    refine2(left, *a[1:])
                finally:
                    ctx["ddfb"] = False
                st["ddref_fallback_hit"] += len({c[0] for c in left if passed[c[0]]})
            return
        if not rdo:
            return (_refine2_sq if p["bpsk_sq"] else bf._refine2)(*a)   # (bpsk_sq: the square's phases)
        cap_, calls_ = [], []                                 # (measurement) ref_diag: the same call, its score and

        def sc_(*x):                                          # decode passed through and recorded
            M_ = a[5](*x)
            cap_.append((np.asarray(x[1], float).copy(), np.asarray(x[2], float).copy(), np.asarray(M_).copy()))
            return M_

        def de_(*x):                                          # (arguments copied before decode edits them)
            xc = (np.array(x[0]), np.array(x[1], float), np.array(x[2], float))
            ok_ = a[6](*x)
            calls_.append(xc + (np.asarray(ok_, bool).copy(),))
            return ok_

        bf._refine2(*a[:5], sc_, de_, *a[7:])
        fr_ = np.array([c[0] for c in a[0]])
        n_ = len(fr_)
        fh_, th_, M_ = (v.reshape(n_, -1) for v in cap_[0])
        o_ = np.argsort(M_, 1)
        nd_, ac_ = np.zeros(n_, int), np.full(n_, -1)
        for t_, (fc_, fhc, thc, okc) in enumerate(calls_):     # decode round t: match each row to its candidate
            for q_ in range(len(fc_)):
                m_ = np.where((fr_ == fc_[q_]) & (fh_[np.arange(n_), o_[:, t_]] == fhc[q_])
                              & (th_[np.arange(n_), o_[:, t_]] == thc[q_]) & (nd_ == t_))[0]
                if len(m_):
                    nd_[m_[0]] = t_ + 1
                    if okc[q_]:
                        ac_[m_[0]] = t_
        _rdlog(fr_, np.array([c[1] for c in a[0]], float), np.array([c[2] for c in a[0]], float), a[1], a[2],
               fh_, th_, M_, nd_, ac_)

    def _rec(l4):                                             # (measurement) d4b: the next candidate's records
        l4.append([])
        ctx["log"] = l4[-1]

    def _flset(kind_, hy_):                                   # (fulllog) the (cell, phase offset in pi/4 units mod 8)
        if flo:                                               # hypotheses of the next refine2 call, in its order
            ctx["fl"], ctx["fl_t"] = (kind_, [(int(c_), int(q_) % 8) for c_, q_ in hy_]), 0

    def _d4b(i, l4, n_c, T_, H_, solo):
        """(measurement) crit_par_d4b of a serial candidate loop of packet i (l4: per candidate reached, the
        (retried, accepted at the main decode, accepted) of each decode; n_c candidates, T_ decodes each, H_ scored
        hypotheses each) run 2 candidates x 2 decodes per round: the rounds in order up to the first with an accept
        (assumed to deliver the same packet), each one decode round + one retry round (SC passes in parallel) unless
        a main decode accepts there (a speculative decode is assumed to need its retry); the candidates first needed
        in a round scored in one stage. If a pair's scoring does not fit one stage (2 H_ > Kc, e.g. fine_last) the
        candidates stay serial (one candidate x 2 decodes per round, scored when first decoded). solo: the packet's
        first decode (no decode before the loop) runs alone. d4w: the speculative decodes (+ retry, re-encoding) and
        the scoring of the unreached candidates, an upper bound.
        Reordering: a round takes hypotheses t, t + 1 of both candidates of a pair, so with T_ > 2 (fine_last,
        T_fine = 6) the partner's first hypotheses run before the candidate's later ones; the serial order of the
        accepts is not modelled (a grouped receiver could accept a different hypothesis)."""
        ctx["log"] = None
        G_ = 2 if 2 * H_ <= Kc else 1                         # candidates per round
        key = lambda c, t: (-1, 0) if (solo and c == 0 and t == 0) else (c // G_, t // 2)
        slots = {}                                            # round -> [decode slots, records, candidates]
        for c in range(n_c):
            for t in range(T_):
                s_ = slots.setdefault(key(c, t), [0, [], set()])
                s_[0] += 1
                s_[2].add(c)
        for c, rc_ in enumerate(l4):
            for t, x in enumerate(rc_):
                s_ = slots.setdefault(key(c, t), [0, [], set()])
                s_[1].append(x)
                s_[2].add(c)
        ser = sum(dp8 + x[0] * (m_met + dp8) for rc_ in l4 for x in rc_)   # as counted (one hypothesis per call)
        c1 = m_met + derot
        ser += len(l4) * np.ceil(H_ / Kc) * c1                # each reached candidate's scoring, one stage each
        w1 = (vp.MAC["decode"] + vp.MAC["llr"] + vp.MAC["reencode"] + (vp.PREMF_FAIR_MACS if p["premf_dec"] else 0)
              + (m_met + vp.MAC["llr"] + bf.CA_MACS(2) + vp.MAC["decode"] + vp.MAC["llr"] if p["ca_retry"] else 0))
        grp, scored = 0.0, set()
        for k_ in sorted(slots):
            n_s, xs, cs_ = slots[k_]
            if not xs:
                break
            new_ = cs_ - scored                               # candidates first needed in this round: scored together
            if new_:
                grp += np.ceil(len(new_) * H_ / Kc) * c1
                d4w[i] += sum(c >= len(l4) for c in new_) * H_ * c1
                scored |= new_
            grp += dp8
            if p["ca_retry"] and not any(x[1] for x in xs) and (any(x[0] for x in xs) or n_s > len(xs)):
                grp += m_met + dp8
            d4w[i] += max(0, n_s - len(xs)) * w1
            if any(x[2] for x in xs):
                break
        d4b[i] += grp - ser

    fa = None
    if "acf" in p["prior"]:                                   # lag-4 autocorrelation of the 8-SPS samples (pre-MF)
        fa = np.angle(np.einsum("bn,bn->b", rx[:, 4:], np.conj(rx[:, :-4]))) / (2 * np.pi * 4) * bc.SPS
        macs += vp.MAC["cmul"] * rx.shape[1]
    # 1. fast path: the 4th-power line inside the small range (no coarse estimate needed)
    nf = bc.NFFT4
    pw = 2 if p["bpsk_sq"] else 4                             # line power: 4 (QPSK), 2 (bpsk_sq: -j r^2 = e^{j 2 theta})
    y4 = -(r ** 4) if pw == 4 else -1j * r ** 2
    Y4c = np.fft.fft(y4, nf, axis=1)
    Y4 = np.abs(Y4c)
    nu_b = np.fft.fftfreq(nf)
    Y4m = np.where(np.abs(nu_b)[None] <= pw * bc.MAX_CFO + 2.0 / nf, Y4, 0.0)
    macs += (2 * 4 * bc.N_SYM if pw == 4 else 4 * bc.N_SYM) + vp.fft_macs(nf)
    if pos is not None:
        zp = r[:, pos] * np.conj(sym[:, pos])
        P = p["fast_peaks"]
        pk = bc.top_peaks(Y4m, P, 2)
        hp = np.take_along_axis(Y4m, pk, 1)
        fc = nu_b[pk] / 4
        live = hp >= p["fast_ratio"] * hp[:, :1]
        spl = np.abs(np.einsum("bk,bpk->bp", zp, np.exp(-2j * np.pi * fc[:, :, None] * (pos - bc.CENTRE)[None, None])))
        kb = pk[np.arange(B), np.where(live, spl, -1).argmax(1)]
        macs += live.sum(1) * (vp.MAC["cmul"] * len(pos) + 8 * len(pos))
    elif p["blind_peaks"] and p["blind_peaks"] > 1:           # blind: the top 4th-power peaks within blind_ratio of
        P = p["blind_peaks"]                                  # the highest, graded by the left-half metric of both
        pk = bc.top_peaks(Y4m, P, 2)                          # pi/2 branches at their parabolic estimates (MF output)
        hp = np.take_along_axis(Y4m, pk, 1)
        live = hp >= p["blind_ratio"] * hp[:, :1]
        Vp = Y4[np.arange(B)[:, None, None], (pk[:, :, None] + np.array([-1, 0, 1])[None, None]) % nf]
        dp = Vp[..., 0] - 2 * Vp[..., 1] + Vp[..., 2]
        op = np.clip(np.where(dp < 0, 0.5 * (Vp[..., 0] - Vp[..., 2]) / np.where(dp < 0, dp, -1.0), 0.0), -0.5, 0.5)
        fp = np.clip((nu_b[pk] + op / nf) / 4, -bc.MAX_CFO, bc.MAX_CFO)
        fsl = bf.fast_sc(code.A)
        Ml = np.full((B, P), np.inf)
        for q in range(P):
            rows = np.where(live[:, q])[0] if q else np.arange(B)
            if not len(rows):
                continue
            if (q == 0 or live[:, q].any()) and p["equiv"]:   # equiv: one branch (both have the same metric)
                thq = bc.phase4(r[rows], fp[rows, q])
                Ml[rows, q] = fsl.metric_left(bc.llrs(r[rows], fp[rows, q], thq, sigma2))
                macs[rows] += vp.MAC["phase4"] + bf._left_macs(code.A) + vp.MAC["cmul"] * bc.N_SYM
                seqm[rows] += bf._left_macs(code.A)
                seqc[rows] += bf._left_macs(code.A)
            elif q == 0 or live[:, q].any():
                thq = bc.phase4(r[rows], fp[rows, q])
                L = np.concatenate([bc.llrs(r[rows], fp[rows, q], thq, sigma2),
                                    bc.llrs(r[rows], fp[rows, q], thq + np.pi / 2, sigma2)])
                Ml[rows, q] = fsl.metric_left(L).reshape(2, len(rows)).min(0)
                macs[rows] += vp.MAC["phase4"] + 2 * (bf._left_macs(code.A) + vp.MAC["cmul"] * bc.N_SYM)
                seqm[rows] += 2 * bf._left_macs(code.A)       # both branches' left metrics, one core each
                seqc[rows] += bf._left_macs(code.A)
        kb = pk[np.arange(B), Ml.argmin(1)]
    else:
        kb = Y4m.argmax(1)
    V = Y4[np.arange(B)[:, None], (kb[:, None] + np.array([-1, 0, 1])[None]) % nf]
    den = V[:, 0] - 2 * V[:, 1] + V[:, 2]
    off = np.clip(np.where(den < 0, 0.5 * (V[:, 0] - V[:, 2]) / np.where(den < 0, den, -1.0), 0.0), -0.5, 0.5)
    f0 = np.clip((nu_b[kb] + off / nf) / pw, -bc.MAX_CFO, bc.MAX_CFO)
    macs += 8
    r_mf = r
    r = bf.premf(r_mf, rx, f0)                                 # pre-MF de-rotation at the 4th-power estimate
    macs += vp.PREMF_FAIR_MACS
    y4 = -(r ** 4) if pw == 4 else -1j * r ** 2
    Y4c = np.fft.fft(y4, nf, axis=1)                          # (the cells' phases; counted as the FFT above)
    macs += (2 * 4 * bc.N_SYM if pw == 4 else 4 * bc.N_SYM) + vp.fft_macs(nf)
    if pos is not None:
        zp = r[:, pos] * np.conj(sym[:, pos])
    if snr >= p["s0_snr"]:
        th0 = bc.phase4(r, f0) if pw == 4 else bc.phase2(r, f0)
        macs += vp.MAC["phase4"]
        fr = np.arange(B)
        if pos is not None:                                   # the pi/2 branch by the pilots' phase
            zz = np.sum(zp * np.exp(-2j * np.pi * f0[:, None] * (pos - bc.CENTRE)[None]), 1)
            rel = ((np.angle(zz) - th0) / (np.pi / 2)) % 2
            br = (np.abs(rel - 1) < np.minimum(rel, 2 - rel)).astype(int)
            macs += vp.MAC["cmul"] * 3 * len(pos)
        elif p["equiv"] or p["bpsk_sq"]:                      # equiv: both branches have the same metric and PiCode4
            br = np.zeros(B, int)                             # decodes either: th0 directly, no metric pass (bpsk_sq:
                                                              # th0 mod pi already)
        elif p["nopi"]:                                       # (blind_fmt) no pi complement: the 4 pi/2 branches
            M2 = score(np.tile(fr, 4), np.tile(f0, 4), np.concatenate([th0 + b * np.pi / 2 for b in range(4)])
                       ).reshape(4, B)
            br = M2.argmin(0)
        else:                                                 # by the full metric of both branches
            M2 = score(np.tile(fr, 2), np.tile(f0, 2), np.concatenate([th0, th0 + np.pi / 2])).reshape(2, B)
            br = M2.argmin(0)
        decode(fr, f0, th0 + br * np.pi / 2)
    if dd:                                                    # (measurement) decode dump, per packet: the 4th-power
        ar_ = np.arange(B)                                    # line (top / next peak, its coherence), both pi/2
        pk2 = bc.top_peaks(Y4m, 2, 2)                         # branches' list-1 metric at f0, M2M4 SNR estimate
        th0_ = bc.phase4(r, f0)
        M2_ = fs_.metric(np.concatenate([bc.llrs(r, f0, th0_, sigma2), bc.llrs(r, f0, th0_ + np.pi / 2, sigma2)]))
        m2_, m4_ = np.mean(np.abs(r_mf) ** 2, 1), np.mean(np.abs(r_mf) ** 4, 1)
        sq_ = np.sqrt(np.maximum(2 * m2_ ** 2 - m4_, 0.0))
        dT0 = th0_ - p["truth_th"] if p["truth_th"] is not None else np.full(B, np.nan)
        pk_row = dict(f0_err=((f0 - p["truth_f"]) / bc.STEP).astype(np.float32),
                      y4_ratio=(Y4m[ar_, pk2[:, 0]] / np.maximum(Y4m[ar_, pk2[:, 1]], 1e-30)).astype(np.float16),
                      y4_coh=(Y4m[ar_, pk2[:, 0]] / (m4_ * bc.N_SYM)).astype(np.float16),
                      th0_err4=((dT0 + np.pi / 4) % (np.pi / 2) - np.pi / 4).astype(np.float16),
                      m_br0=M2_[:B].astype(np.float32), m_br1=M2_[B:].astype(np.float32),
                      p_r=m2_.astype(np.float32),
                      snr_m2m4=(10 * np.log10(np.maximum(sq_, 1e-12) / np.maximum(m2_ - sq_, 1e-12))).astype(np.float16))

    m_fast = macs.copy()                                     # (measurement) MACs spent by the fast path
    pass_fast = passed.copy()

    def _snp(ix):                                             # (measurement, stage_acc) [macs, crit_par_d4a,
        cp_ = crit + dcritp + seqc + (macs - pmac - dmac - seqm) / KP   # crit_par_h_d4a] of packets ix so far
        return np.stack([macs[ix], (cp_ + d4a)[ix], (cp_ - crit_g + crit_gh + d4a)[ix]], -1)

    if sto:
        s_reach = np.zeros((B, 5), bool)
        s_reach[:, 0] = True
        s_cost = np.full((B, 6, 3), np.nan)
        s_cost[:, 0] = _snp(slice(None))
    stg = np.where(passed, 1, 0)                              # (measurement) the stage that accepted each packet:
    # 1 fast path, 2 the grid search's own decodes, 3 the final candidates, 4 rescue (final_post), 5 rescue (fine_last)
    # 2. search over the whole small grid, cell by cell for each remaining packet
    roffs = np.arange(-(k // 2), k // 2 + 1)
    sub = (-np.pi / 12, 0.0, np.pi / 12) if (nph0 == 4 or p["sub3"]) else (0.0,)   # phase sub-offsets of a candidate
    H_s = 1 if p["s3_dd"] else len(roffs) * len(sub)          # (measurement) d4b: hypotheses scored per candidate
    T_s = min(p["T"], 2) if p["s3_dd"] else p["T"]            # and decodes per candidate (refine_dd: <= 2)
    b4 = np.round(((pw * g) % 1.0) * nf).astype(int) % nf    # (bpsk_sq: pw = 2, the square's line at 2g)
    nus = pw * g + ((b4 / nf - (pw * g) % 1.0 + 0.5) % 1.0 - 0.5)
    rem = np.where(~passed)[0]
    LP = np.zeros((B, len(g)))                                # prior over the cells (only to shortlist them)
    if len(rem) and (p["pre_keep"] or p["first_k"] or p["top_k"] or p["batch"]):
        if "s4" in p["prior"]:                                # the 4th-power periodogram (its FFT is already there)
            LP[rem] += bf.w4_of(snr) * vp.s4_grid(r[rem], k)
        if fa is not None:
            sa = float(np.interp(snr, *zip(*bf.ACF_SIGMA)))
            LP[rem] += -0.5 * ((g[None] - fa[rem, None]) / sa) ** 2
        if "pilots" in p["prior"] and pos is not None:      # the pilots' non-coherent likelihood
            LP[rem] += vp.pilot_loglik(vp.pilot_A(zp[rem], pos, g), snr)
            macs[rem] += vp.MAC["cmul"] * len(pos) * len(g)
    LPf = LP                                                  # (fulllog) the spectral prior of the replay's batch /
    if flo and len(rem) and not (p["pre_keep"] or p["first_k"] or p["top_k"] or p["batch"]):   # first_k order (as LP;
        LPf = np.zeros((B, len(g)))                           # no MACs: the 4th-power FFT is already there)
        if "s4" in p["prior"]:
            LPf[rem] += bf.w4_of(snr) * vp.s4_grid(r[rem], k)
        if fa is not None:
            LPf[rem] += -0.5 * ((g[None] - fa[rem, None]) / float(np.interp(snr, *zip(*bf.ACF_SIGMA)))) ** 2
    LPp = None
    if len(rem) and p["pilot_score"] and pos is not None:     # the pilots' log-likelihood of every cell
        LPp = np.zeros((B, len(g)))
        LPp[rem] = vp.pilot_loglik(vp.pilot_A(zp[rem], pos, g), snr)
        macs[rem] += vp.MAC["cmul"] * len(pos) * len(g)
    LN = None
    if len(rem) and (p["nn"] or p["dump"] is not None):     # the cell-prior NN on the packets left for the search
        pl = None
        if pos is not None:
            pl = LPp[rem] if LPp is not None else vp.pilot_loglik(vp.pilot_A(zp[rem], pos, g), snr)
            if LPp is None:
                macs[rem] += vp.MAC["cmul"] * len(pos) * len(g)
        X, mx = nn_features(r[rem], rx[rem], f0[rem], g, k, snr, pl)
        if p["dump"] is not None:                             # training data (small_prior_nn.py): stop here
            p["dump"].update(x=X, rem=rem, f0=f0[rem], g=g, k=k)
            return out, passed, f_fin, f0
        LN = np.zeros((B, len(g)))
        LN[rem] = nn_logp(p["nn"], X)
        macs[rem] += mx + nn_macs(len(g))
    if len(rem) and p["dump_pm"] is not None:                # training data of the checkpoint NN (small_ck_nn.py):
        pl = None                                             # the partial path metrics of every cell x phase
        if pos is not None:
            pl = vp.pilot_loglik(vp.pilot_A(zp[rem], pos, g), snr)
        X, _ = nn_features(r[rem], rx[rem], f0[rem], g, k, snr, pl)
        lr0 = np.array([fsn.frozen[lo:hi].all() for lo, hi in leaves(fsn.plan, 0, bc.N_BITS, [], SPLIT)])
        if p["ck_useful"]:                                    # (blind_fmt) CK_FR on the not pre-frozen positions, as
            il = np.array([_nlf(c) for c in CK_FR]) - 1       # the search below (fullsys/ck_nn_fs.py training data)
        else:
            il = np.array([max(1, int((lv <= c * bc.N_BITS).sum())) for c in CK_FR]) - 1
        D = np.empty((len(rem), len(g), nph, len(CK_FR), 2), np.float32)
        for n, i in enumerate(rem):
            th = np.angle(Y4c[i, b4] * np.exp(2j * np.pi * nus * bc.CENTRE)) / pw   # (pw 4; bpsk_sq 2, as the search)
            ri = np.repeat(r[i:i + 1], len(g), 0)
            for jq, q in enumerate(qs):
                v = fsn.metric_nodes(bc.llrs(ri, g, th + q * np.pi / 4, sigma2))
                D[n, :, jq, :, 0] = np.cumsum(v, 1)[:, il]
                D[n, :, jq, :, 1] = np.cumsum(v * lr0, 1)[:, il]
        p["dump_pm"].update(x=X, pm=D, rem=rem, g=g, k=k)
        return out, passed, f_fin, f0
    if len(rem) and cnn is not None:                          # the checkpoint NN's per-cell prior features
        pl = None
        if pos is not None:
            pl = LPp[rem] if LPp is not None else vp.pilot_loglik(vp.pilot_A(zp[rem], pos, g), snr)
            if LPp is None:
                macs[rem] += vp.MAC["cmul"] * len(pos) * len(g)
        XC, mx = nn_features(r[rem], rx[rem], f0[rem], g, k, snr, pl)
        macs[rem] += mx
        lr0 = np.array([fsn.frozen[lo:hi].all() for lo, hi in leaves(fsn.plan, 0, bc.N_BITS, [], SPLIT)])
        if p["ck_useful"]:                                    # (blind_fmt) CK_FR on the not pre-frozen positions
            il = np.array([_nlf(c) for c in CK_FR]) - 1
        else:
            il = np.array([max(1, int((lv <= c * bc.N_BITS).sum())) for c in CK_FR]) - 1
        jnn = cks.index(CK_FR[cnn])
        ck_mode = "pilots" if pos is not None else "blind"
    def _lmz():                                               # lmarg: the survivors' z and phases by the lmarg metric
        Mlm_, qlm_ = lm_rank(i, alive, qal, th, adj[:, -1], lmc)   # (packet i's current grid state)
        ok_ = alive & np.isfinite(Mlm_)
        zc_ = np.where(ok_, _rz(np.where(ok_, Mlm_, np.nan)), -np.inf)
        st["lm_first_diff"] += int(np.argmax(zc_) != np.argmax(zf))   # (measurement) the top cell changed
        if p["lmarg_lazy"] and not lmon[0]:
            st["lm_lazy_runs"] += 1
        lmon[0] = True
        return zc_, np.where(np.isfinite(Mlm_), qlm_, qb[:, -1])   # (cells without a metric: their list-1 phase)

    def _pdc(c, q):                                           # (ddref) cell c's centre hypothesis at phase index q
        return bool(paid[c] >= sh[-1] - 1e-9 and qal[c, q] and qph[q] == qs[q])   # decoded to full by the search

    for i in rem:
        th = np.angle(Y4c[i, b4] * np.exp(2j * np.pi * nus * bc.CENTRE)) / pw    # the cells' 4th-power phases
        if sto:
            s_reach[i, 1] = True
        Pq = np.empty((nph, len(g), len(cks)), np.float32)
        ri = np.repeat(r[i:i + 1], len(g), 0)
        if cnn is not None:
            Dq = np.empty((len(g), nph, len(CK_FR), 2), np.float32)
        PL = np.empty((nph, len(g), len(FLF)), np.float32) if flo else None   # (fulllog) every logged checkpoint
        for jq, q in enumerate(qs):
            llr = bc.llrs(ri, g, th + q * np.pi / 4, sigma2)
            v = fsn.metric_nodes(llr)
            Pq[jq] = np.cumsum(v, 1)[:, np.array(nl) - 1]
            if cnn is not None:
                Dq[:, jq, :, 0] = np.cumsum(v, 1)[:, il]
                Dq[:, jq, :, 1] = np.cumsum(v * lr0, 1)[:, il]
            if flo:
                PL[jq] = np.cumsum(v, 1)[:, nlL - 1]
        if flo:                                               # (fulllog) packet i at its search start: PMs, NN log P
            assert np.array_equal(PL[:, :, jL], Pq), "fulllog: logged PMs differ from the search's"   # (as in the
            nfl_ = int(np.searchsorted(rem, i))               # loop below), prior, true cell, cost counters so far
            flp.append(dict(pk=i, pq=PL, lp=(ck_logp(ck_mode, cnn, ck_features(XC[nfl_:nfl_ + 1], Dq[None], cnn),
                                                     p["ck_nn_name"])[0] if cnn is not None else np.zeros(len(g))),
                            lpr=np.array(LPf[i], float), ct=int(np.abs(g - p["truth_f"][i]).argmin()),
                            snap=np.array([macs[i], pmac[i], dmac[i], seqm[i], crit[i], crit_g[i], crit_gh[i],
                                           dcritp[i], seqc[i], d4a[i]], float)))
        st["metric_evals"] += nph * len(g)
        n_hyp[i] += nph * len(g)                              # (measurement) stage_acc
        pm = Pq.min(0)                                        # (cells, checkpoints): the cell's best phase
        qb = Pq.argmin(0)
        pm0 = pm
        if p["pilot_score"] and pos is not None:              # the pilots inside the cell score: path metric minus
            pm = pm - p["pilot_score"] * LPp[i][:, None]       # their log-likelihood (both in nats)
        if LN is not None and p["nn_score"]:                 # the NN's log-probability inside the cell score
            pm = pm - p["nn_score"] * LN[i][:, None]
        base = np.ones(len(g), bool)
        if p["pre_keep"]:                                     # only the best pre_keep cells of the prior are scored
            base[:] = False
            base[np.argsort(-LP[i])[:p["pre_keep"]]] = True
        rounds = [base]
        if LN is not None and p["nn_keep"]:                   # best-first: the NN's shortlist (cumulative probability
            o = np.argsort(-LN[i])                            # 1 - nn_keep, >= nn_min cells), then the whole grid
            n = max(p["nn_min"], int(np.searchsorted(np.cumsum(np.exp(LN[i][o])), 1 - p["nn_keep"])) + 1)
            short = np.zeros(len(g), bool)
            short[o[:n]] = True
            rounds = [short & base, base]
        if p["first_k"]:                                      # best-first: the prior's best first_k cells, then the
            short = np.zeros(len(g), bool)                    # whole grid only if nothing passes among them
            short[np.argsort(-LP[i])[:p["first_k"]]] = True
            rounds = [short & base, base]
        sc_ = LN[i] if LN is not None else LP[i]              # the grader (the NN prior, else the spectral prior)
        if p["top_k"]:                                        # hard cap: only the grader's best top_k cells are ever
            cap = np.zeros(len(g), bool)                      # decoded, no fallback
            cap[np.argsort(-sc_)[:p["top_k"]]] = True
            rounds = [rd & cap for rd in rounds]
        if p["batch"]:                                        # at most batch[0] cells decoded at a time: contiguous
            blk = np.array_split(np.arange(len(g)), -(-len(g) // p["batch"][0]))   # blocks of the grid in the
            blk.sort(key=lambda b_: -np.logaddexp.reduce(sc_[b_]))                 # grader's order (log-sum-exp of
            acc = np.zeros(len(g), bool)                                           # the block); cumulative rounds,
            rounds = []                                                            # paid cells are not re-charged
            for b_ in blk:
                acc = acc.copy()
                acc[b_] = True
                rounds.append(acc & base)
        seen = np.zeros(len(g), bool)
        adj = pm - pm0                                        # the score terms beyond the path metric (per cell)
        qal = np.ones((len(g), nph), bool)                    # phases still decoded per cell (beam)
        paid = np.zeros(len(g))                               # share of a metric pass decoded per cell so far
        joined = np.zeros(len(g), bool)
        tried = set()
        spec_tried = set()                                    # cells decoded speculatively (win_spec)
        lmc = {}                                              # lmarg: (cell, phase index) -> list-marginalised metric
        lmon = [False]                                        # lmarg: the survivors' list decode has run (lazy)
        if rdo:                                               # (measurement) ref_diag: this packet's grid state (qal,
            ctx["rdg"] = (i, Pq, qal, paid, th)               # paid updated in place)
        qcut = {}                                             # (accounting) phase pruning shares -> phases per cell
        new_acct = not p["old_acct"]                          # before the first pruning there (_segs)
        for rnd, alive0 in enumerate(rounds):
            if rnd and not (alive0 & ~rounds[rnd - 1]).any():
                break
            alive = alive0.copy()
            cores[i] = max(cores[i], (alive0 & ~seen).sum()) if ncore is None else ncore
            seen |= alive0
            skip = False
            if p["coarse"]:                                   # coarse start: every other cell up to the 1st checkpoint
                alive[np.arange(len(g)) % p["stride"] != 0] = False   # (stride: every 2nd / 3rd)
            macs[i] += (alive & ~joined).sum() * (vp.MAC["cmul"] + derot)   # the cells' phase and de-rotation
            jn_ = alive & ~joined                             # (a cell joining after a pruning: its phases before it)
            _par(i, np.full(jn_.sum(), vp.MAC["cmul"] + derot),
                 _segs(qcut, qal, paid, jn_, 0.0)[1][:, 0] if (new_acct and qcut) else qal[jn_].sum(1),
                 vp.MAC["cmul"] + derot)
            joined |= alive
            for j, f_ in enumerate(frac):
                chg = alive                                   # the cells charged up to this checkpoint
                if p["ck_charge_all"] and cnn is not None and j == jnn:   # (accounting) the checkpoint NN sees every
                    chg = alive | (paid < sh[j])              # cell: those not paid up to here are charged with the
                    ux_ = chg & ~alive                        # alive ones (their phase + de-rotation first)
                    jx_ = ux_ & ~joined
                    if new_acct and qcut:
                        L_, C_ = _segs(qcut, qal, paid, ux_, sh[j])
                        wx_ = m_met * (L_ * C_).sum()
                    else:
                        wx_ = m_met * (qal[ux_].sum(1) * np.clip(sh[j] - paid[ux_], 0, None)).sum()
                    st["ck_extra_cells"] = st.get("ck_extra_cells", 0) + int(ux_.sum())   # (measurement) the extra
                    st["macs_ck_extra"] = st.get("macs_ck_extra", 0.0) + float(jx_.sum() * (vp.MAC["cmul"] + derot) + wx_)
                    if jx_.any():
                        macs[i] += jx_.sum() * (vp.MAC["cmul"] + derot)
                        _par(i, np.full(jx_.sum(), vp.MAC["cmul"] + derot),
                             _segs(qcut, qal, paid, jx_, 0.0)[1][:, 0] if (new_acct and qcut) else qal[jx_].sum(1),
                             vp.MAC["cmul"] + derot)
                        joined |= jx_
                nd = (chg & (paid < sh[j])).sum()             # cells extended in this stage
                passes[i] += np.ceil(nd / ncore) if ncore else (nd > 0)
                if new_acct and qcut:                         # cells paid below a pruning share: its pre-pruning phases
                    L_, C_ = _segs(qcut, qal, paid, chg, sh[j])
                    w_ = m_met * (L_ * C_).sum(1)
                    macs[i] += w_.sum()
                    _par(i, w_, hyp=(L_, C_))
                else:
                    macs[i] += m_met * (qal[chg].sum(1) * np.clip(sh[j] - paid[chg], 0, None)).sum()   # alive cells x
                    _par(i, m_met * qal[chg].sum(1) * np.clip(sh[j] - paid[chg], 0, None), qal[chg].sum(1))
                paid[chg] = np.maximum(paid[chg], sh[j])                                           # phases up to f_
                z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                if j == len(frac) - 1:
                    break
                if cnn is not None and j == jnn:              # the checkpoint NN instead of the z-test here: its
                    n_ = int(np.searchsorted(rem, i))         # shortlist (cumulative probability 1 - ck_keep,
                    lp = ck_logp(ck_mode, cnn, ck_features(XC[n_:n_ + 1], Dq[None], cnn),   # >= ck_min cells)
                                 p["ck_nn_name"])[0]
                    macs[i] += ck_macs(len(g))
                    o = np.argsort(-lp)
                    o = o[alive[o]]
                    if p["ck_win"] is not None and np.exp(lp[o[0]]) > p["ck_win"] and o[0] not in tried:
                        c = int(o[0])                         # a confident NN winner is decoded at once
                        tried.add(c)
                        ctx["tag"] = "early_z"
                        if dd:                                        # (measurement) decode dump: grid state
                            ctx["meta"] = [_gm(c, qb[c, j], j, z, pm, alive, paid, len((tried | spec_tried) - {c}))]
                        _flset(0, [(c, qph[qb[c, j]])])
                        refine2([(i, g[c], th[c] + qph[qb[c, j]] * np.pi / 4)], roffs, sub, p["T"], r, score, decode,
                                    passed)
                        if passed[i]:
                            break
                    n_ = max(p["ck_min"], int(np.searchsorted(np.cumsum(np.exp(lp[o])), 1 - p["ck_keep"])) + 1)
                    keep = np.zeros(len(g), bool)
                    keep[o[:n_]] = True
                    alive &= keep
                    continue
                pk_ = p["phase_keep"]
                if pk_ is not None and f_ == pk_[0]:
                    sc_ = np.where(qal, Pq[:, :, j].T, np.inf)
                    if new_acct:                              # (accounting) every cell's phases up to here
                        qcut.setdefault(sh[j], qal.sum(1))
                    nk_ = (max(1, pk_[1] // 2) if (p["equiv"] or p["bpsk_sq"])   # equiv: halved (pi/2 twins = one
                           else 2 * pk_[1] if p["nopi"] else pk_[1])             # phase; bpsk_sq: no pi/2 branch;
                                                                                 # nopi: both pi halves)
                    qal &= np.argsort(np.argsort(sc_, 1), 1) < nk_
                    P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                    pm, qb = P_.min(0) + adj, P_.argmin(0)
                    z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                rp = p["race_phase"]
                if rp is not None and f_ == rp[0]:
                    if new_acct:
                        qcut.setdefault(sh[j], qal.sum(1))
                    qal &= Pq[:, :, j].T <= Pq[:, :, j].min(0)[:, None] + rp[1]
                    P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                    pm, qb = P_.min(0) + adj, P_.argmin(0)
                    z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                bm = p["beam"]
                if bm is not None and (f_ >= bm[0] or (p["keep_early"] and f_ == p["keep_early"][0])):
                    H = alive[:, None] & qal                  # beam: the best hypotheses by path metric (+ the
                    if f_ >= bm[0] and p["equiv"]:             # cell's other score terms) continue; equiv: half
                        K = max(2, (bm[1] // 2) >> int(np.sum((frac >= bm[0]) & (frac < f_))))   # as many (no
                    elif f_ >= bm[0]:                          # pi/2 twins)
                        K = max(4, bm[1] >> int(np.sum((frac >= bm[0]) & (frac < f_))))
                    else:
                        K = int(np.ceil(p["keep_early"][1] * H.sum()))
                    if H.sum() > K:
                        sc = np.where(H, Pq[:, :, j].T + adj[:, j:j + 1], np.inf).ravel()
                        kp = np.zeros(sc.size, bool)
                        kp[np.argpartition(sc, K)[:K]] = True
                        if new_acct:
                            qcut.setdefault(sh[j], qal.sum(1))
                        qal &= kp.reshape(qal.shape)
                        for s_ in qcut:                       # (accounting) a cell left without hypotheses decodes
                            qcut[s_][~qal.any(1)] = 0         # nothing more (it never pays below a share later)
                        alive &= qal.any(1)
                        P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                        pm, qb = P_.min(0) + adj, P_.argmin(0)
                    if p["coarse"] and j == 0:                # coarse start: the neighbours of the surviving cells
                        new = np.zeros_like(alive)            # join (every phase), decoded up to here now
                        new[1:] |= alive[:-1]
                        new[:-1] |= alive[1:]
                        new &= ~alive & alive0
                        new[0::2] = False
                        qal[new] = True
                        for s_ in qcut:                       # (accounting) every phase, charged as such below
                            qcut[s_][new] = nph
                        macs[i] += (new & ~joined).sum() * (vp.MAC["cmul"] + derot)
                        macs[i] += nph * m_met * np.clip(sh[j] - paid[new], 0, None).sum()
                        _par(i, (vp.MAC["cmul"] + derot) * (~joined[new]) + nph * m_met * np.clip(
                            sh[j] - paid[new], 0, None), nph, (vp.MAC["cmul"] + derot) * (~joined[new]))
                        paid[new] = np.maximum(paid[new], sh[j])
                        joined |= new
                        alive |= new
                        P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                        pm, qb = P_.min(0) + adj, P_.argmin(0)
                    continue
                if p["win"] is not None or p["win_spec"] is not None:   # early stop: a clear winner ends the search
                    zt = z.copy()
                    zt[list(tried)] = -np.inf
                    c = int(zt.argmax())
                    if p["win"] is not None and zt[c] > p["win"]:
                        tried.add(c)
                        ctx["tag"] = "win"
                        if dd:                                        # (measurement) decode dump: grid state
                            ctx["meta"] = [_gm(c, qb[c, j], j, z, pm, alive, paid, len((tried | spec_tried) - {c}))]
                        _flset(0, [(c, qph[qb[c, j]])])
                        refine2([(i, g[c], th[c] + qph[qb[c, j]] * np.pi / 4)], roffs, sub, p["T"], r, score, decode,
                                    passed)
                        if passed[i]:
                            break
                    elif p["win_spec"] is not None and zt[c] > p["win_spec"] and c not in spec_tried:
                        spec_tried.add(c)                     # speculative: T = 1, no CA retry; not in tried (it can
                        st["spec_decodes"] = st.get("spec_decodes", 0) + 1   # still be a candidate later)
                        ca_ = p["ca_retry"]
                        p["ca_retry"] = False
                        ctx["tag"] = "spec"
                        if dd:                                        # (measurement) decode dump: grid state
                            ctx["meta"] = [_gm(c, qb[c, j], j, z, pm, alive, paid, len((tried | spec_tried) - {c}))]
                        try:
                            refine2([(i, g[c], th[c] + qph[qb[c, j]] * np.pi / 4)], roffs, sub, 1, r, score, decode,
                                    passed)
                        finally:
                            p["ca_retry"] = ca_
                        if passed[i]:
                            st["spec_pass"] = st.get("spec_pass", 0) + 1
                            if p["truth"] is not None and (out[i] != p["truth"][i]).any():   # (measurement)
                                st["spec_pass_wrong"] = st.get("spec_pass_wrong", 0) + 1
                            break
                if p["batch"] and rnd < len(rounds) - 1 and z.max() < p["batch"][1]:
                    skip = True                               # batch rejected: no cell stands out, the next block
                    break                                     # (its cells come back in the later, joint rounds)
                keep = z > p["tau"]
                keep[np.argsort(-z)[:p["kmin"]]] = True
                alive &= keep
                if p["coarse"] and j == 0:                    # the neighbours of the surviving coarse cells join;
                    new = np.zeros_like(alive)                # their decode up to this checkpoint is paid now
                    par = np.full(len(g), -1)
                    src = np.where(alive)[0]                  # join_top: only the best join_top coarse cells
                    if p["join_top"]:                         # bring in neighbours
                        src = src[np.argsort(pm[src, j])[:p["join_top"]]]
                    for c in src:                             # join_side: only the neighbour on the side of the
                        S_ = p["stride"]                      # better adjacent coarse cell (the CFO lies there)
                        sides = [c + d * m for d in (-1, 1) for m in range(1, S_)]
                        if p["join_side"]:
                            pl = pm[c - S_, j] if c >= S_ else np.inf
                            pr = pm[c + S_, j] if c + S_ < len(g) else np.inf
                            d = 1 if pr < pl else -1
                            sides = [c + d * m for m in range(1, S_)]
                        for n_ in sides:
                            if 0 <= n_ < len(g) and alive0[n_] and not alive[n_] and n_ % S_:
                                if par[n_] < 0 or pm[c, j] < pm[par[n_], j]:
                                    par[n_] = c
                                new[n_] = True
                    if p["join_nph"]:                         # phase hand-off: the carrier phase (at the packet
                        for n_ in np.where(new)[0]:           # centre) is common to adjacent CFO hypotheses: a
                            c = par[n_]                       # joining cell decodes only its join_nph phases
                            tp = th[c] + qph[qb[c, j]] * np.pi / 4  # nearest to its parent's best one (mod pi)
                            md_ = np.pi / 2 if p["equiv"] else (2 * np.pi if p["nopi"] else np.pi)   # (equiv: mod
                                                                                              # pi/2; nopi: mod 2 pi)
                            d = np.abs((tp - (th[n_] + qs * np.pi / 4) + md_ / 2) % md_ - md_ / 2)
                            qal[n_] = False
                            qal[n_, np.argsort(d)[:p["join_nph"]]] = True
                            for s_ in qcut:                   # (accounting) its phases chosen before it is paid:
                                qcut[s_][n_] = qal[n_].sum()  # those from 0 (legitimate)
                    macs[i] += (new & ~joined).sum() * (vp.MAC["cmul"] + derot)
                    nd = (new & (paid < sh[j])).sum()
                    passes[i] += np.ceil(nd / ncore) if ncore else (nd > 0)
                    if new_acct and qcut:                     # (accounting) a neighbour joining after a pruning:
                        L_, C_ = _segs(qcut, qal, paid, new, sh[j])   # its pre-pruning phases up to the pruning share
                        w_ = m_met * (L_ * C_).sum(1)
                        jc_ = (vp.MAC["cmul"] + derot) * (~joined[new])
                        macs[i] += w_.sum()
                        _par(i, jc_ + w_, None, jc_, hyp=(L_, C_))
                    else:
                        macs[i] += m_met * (qal[new].sum(1) * np.clip(sh[j] - paid[new], 0, None)).sum()
                        _par(i, (vp.MAC["cmul"] + derot) * (~joined[new]) + m_met * qal[new].sum(1) * np.clip(
                            sh[j] - paid[new], 0, None), qal[new].sum(1), (vp.MAC["cmul"] + derot) * (~joined[new]))
                    paid[new] = np.maximum(paid[new], sh[j])
                    joined |= new
                    alive |= new
                    if p["join_nph"]:
                        P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                        pm, qb = P_.min(0) + adj, P_.argmin(0)
            if passed[i]:
                break
            zf = z
            if skip:
                continue
            zc, qc_ = zf, qb[:, -1]                           # the candidates' order and phase index (list-1 PM)
            lz = lmo and p["lmarg_lazy"] and not lmon[0]      # lazy lmarg: the list-1 order's first candidate first
            if lmo and not lz:                                # lmarg: by the list-marginalised metric of the survivors
                zc, qc_ = _lmz()
            cs = [c for c in np.argsort(-zc)[:p["ncand"]] if zc[c] > p["z0"] and c not in tried]
            if lz and not cs:                                 # (lazy, no cell with z > z0: the list decode at once)
                lz = False
                zc, qc_ = _lmz()
                cs = [c for c in np.argsort(-zc)[:p["ncand"]] if zc[c] > p["z0"] and c not in tried]
            ctx["tag"] = "s2cand"
            if p["joint"] is not None:                        # the candidates decoded jointly, joint[2] at a time
                for a in range(0, len(cs), p["joint"][2]):
                    if dd:                                    # (measurement) decode dump: grid state
                        ctx["meta"] = [_gm(c, qb[c, -1], len(frac) - 1, zf, pm, alive, paid, len((tried | spec_tried) - {c}))
                                       for c in cs[a:a + p["joint"][2]]]
                    tried.update(cs[a:a + p["joint"][2]])
                    refine_joint(i, [(g[c], th[c] + qph[qb[c, -1]] * np.pi / 4) for c in cs[a:a + p["joint"][2]]])
                    if passed[i]:
                        break
                cs = []
            l4, solo = [], not have[i]
            n_cs, q_ = len(cs), list(cs)
            while q_:
                c = q_.pop(0)
                if dd:                                        # (measurement) decode dump: grid state
                    ctx["meta"] = [_gm(c, qb[c, -1], len(frac) - 1, zf, pm, alive, paid, len((tried | spec_tried) - {c}))]
                tried.add(c)
                _rec(l4)
                if ddo:                                       # (ddref) its centre hypothesis paid by the search?
                    ctx["ddp"] = [_pdc(c, qc_[c])]
                _flset(0, [(c, qph[qc_[c]])])
                refine2([(i, g[c], th[c] + qph[qc_[c]] * np.pi / 4)], roffs, sub, p["T"], r, score, decode, passed)
                if passed[i]:
                    break
                if lz:                                        # lazy lmarg: the first candidate failed -> the list
                    lz = False                                # decode; the rest (<= ncand - 1) by the lmarg z
                    zc, qc_ = _lmz()
                    q_ = [c for c in np.argsort(-zc)[:p["ncand"]] if zc[c] > p["z0"] and c not in tried][:p["ncand"] - 1]
                    n_cs = 1 + len(q_)
            if n_cs:
                _d4b(i, l4, n_cs, T_s, H_s, solo)
            if passed[i]:
                break
        if sto:                                               # (measurement) stage_acc: end of the grid search
            s_cost[i, 1] = _snp(i)
        if passed[i]:
            stg[i] = 2
            continue
        if sto:
            s_reach[i, 2] = True
        qf_ = qb[:, -1]                                       # the final candidates' phase index (list-1 PM)
        if lmo:                                               # lmarg: the best `final` by the list-marginalised metric
            Mlm, qlm = lm_rank(i, alive, qal, th, adj[:, -1], lmc)
            if p["lmarg_lazy"] and not lmon[0]:
                st["lm_lazy_runs"] += 1
            lmon[0] = True
            qf_ = np.where(np.isfinite(Mlm), qlm, qb[:, -1])   # (the dead cells padding the list: as the baseline)
            cs = [c for c in np.argsort(np.where(alive, Mlm, np.inf), kind="stable")[:p["final"]] if c not in tried]
        else:
            cs = [c for c in np.argsort(np.where(alive, pm[:, -1], np.inf))[:p["final"]] if c not in tried]
        ctx["tag"] = "final32"
        if p["joint"] is not None:
            for a in range(0, len(cs), p["joint"][2]):
                if dd:                                        # (measurement) decode dump: grid state
                    ctx["meta"] = [_gm(c, qb[c, -1], len(frac) - 1, zf, pm, alive, paid, len((tried | spec_tried) - {c}))
                                   for c in cs[a:a + p["joint"][2]]]
                tried.update(cs[a:a + p["joint"][2]])
                refine_joint(i, [(g[c], th[c] + qph[qb[c, -1]] * np.pi / 4) for c in cs[a:a + p["joint"][2]]])
                if passed[i]:
                    break
            cs = []
        l4, solo = [], not have[i]
        for c in cs:
            if dd:                                            # (measurement) decode dump: grid state
                ctx["meta"] = [_gm(c, qb[c, -1], len(frac) - 1, zf, pm, alive, paid, len((tried | spec_tried) - {c}))]
            tried.add(c)
            _rec(l4)
            if ddo:                                           # (ddref) its centre hypothesis paid by the search?
                ctx["ddp"] = [_pdc(c, qf_[c])]
            _flset(0, [(c, qph[qf_[c]])])
            refine2([(i, g[c], th[c] + qph[qf_[c]] * np.pi / 4)], roffs, sub, p["T"], r, score, decode, passed)
            if passed[i]:
                break
        if cs:
            _d4b(i, l4, len(cs), T_s, H_s, solo)
        stg[i] = 3 if passed[i] else 0
        if sto:                                               # (measurement) stage_acc: end of the final candidates
            s_cost[i, 2] = _snp(i)
            s_reach[i, 3] = not passed[i] and bool(p["final_post"])
        # rescue (as blind_fast's final_post / fine_last), only for packets still undecoded: the next best cells by z
        # on both pi/2 branches, 8 at a time; then the best-metric cells on a half-STEP grid over the cell and its
        # edges x pi/16 phases with more decodes
        if not passed[i] and p["final_post"]:
            cs = [c for c in np.argsort(-zf) if np.isfinite(zf[c]) and c not in tried][:p["final_post"]]
            bs_ = ((0,) if (p["equiv"] or p["bpsk_sq"]) else   # equiv: one pi/2 branch (PiCode4 decodes both);
                   (0, 1, 2, 3) if p["nopi"] else (0, 1))     # bpsk_sq: pi/2 a dud; nopi: all 4 branches
            if dd:                                            # (measurement) decode dump: grid state (q + 4 b)
                pmeta = [_gm(c, qb[c, -1] + 4 * b, len(frac) - 1, zf, pm, alive, paid,
                             len((tried | spec_tried) - {c})) for c in cs for b in bs_]
            tried.update(cs)
            cand = [(i, g[c], th[c] + qph[qb[c, -1]] * np.pi / 4 + b * np.pi / 2) for c in cs for b in bs_]
            ctx["tag"] = "post"
            for a in range(0, len(cand), 8):
                if dd:
                    ctx["meta"] = pmeta[a:a + 8]
                if ddo:                                       # (ddref) branch b = 0 of a cell decoded to full length
                    ctx["ddp"] = [b == 0 and _pdc(c, qb[c, -1]) for c in cs for b in bs_][a:a + 8]
                if flo:                                       # (fulllog) b pi/2 = 2 b in pi/4 units
                    _flset(0, [(c, qph[qb[c, -1]] + 2 * b) for c in cs for b in bs_][a:a + 8])
                refine2(cand[a:a + 8], roffs, sub, p["T"], r, score, decode, passed)
                if passed[i]:
                    break
            stg[i] = 4 if passed[i] else 0
            if sto:                                           # (measurement) stage_acc: end of final_post
                s_cost[i, 3] = _snp(i)
        if sto:
            s_reach[i, 4] = not passed[i] and bool(p["fine_last"])
        if not passed[i] and p["fine_last"]:
            cs = np.argsort(np.where(alive, pm[:, -1], np.inf))[:p["fine_last"]]
            fine = np.arange(-k, k + 1) * 0.5
            subf = tuple(np.arange(-2, 3) * np.pi / 16)
            ctx["tag"] = "fine_last"
            l4, solo = [], not have[i]
            for c in cs:
                if dd:                                        # (measurement) decode dump: grid state
                    ctx["meta"] = [_gm(c, qb[c, -1], len(frac) - 1, zf, pm, alive, paid, len((tried | spec_tried) - {c}))]
                _rec(l4)
                _flset(1, [(c, qph[qb[c, -1]])])
                refine2([(i, g[c], th[c] + qph[qb[c, -1]] * np.pi / 4)], fine, subf, p["T_fine"], r, score, decode,
                            passed)
                if passed[i]:
                    break
            if len(cs):
                _d4b(i, l4, len(cs), p["T_fine"], len(fine) * len(subf), solo)
            stg[i] = 5 if passed[i] else 0
            if sto:                                           # (measurement) stage_acc: end of fine_last
                s_cost[i, 4] = _snp(i)
    code.fz_stop = None                                       # (fzstop: off for whatever uses the shared code next)
    if flo and flp:                                           # (fulllog) side refine2 calls of the near hypotheses the
        thr_fl = _thr()                                       # search's own rows leave incomplete, outside every
        pas_fl = np.zeros(B, bool)                            # counter (local passed flags, fz_stop off): rows src 1
        cmp_fl = {}                                           # (packet, cell, po, kind) -> [attempts logged, accepted]
        for x in flh:
            for q_ in range(len(x["pk"])):
                a_ = cmp_fl.setdefault((int(x["pk"][q_]), int(x["cell"][q_]), int(x["po"][q_]), int(x["kind"][q_])),
                                       [0, False])
                a_[0] = max(a_[0], int(x["t"][q_]) + 1)
                a_[1] |= bool(x["acc_m"][q_] or x["acc_r"][q_])
        ref_fl = _refine2_sq if p["bpsk_sq"] else bf._refine2
        fine_fl, subf_fl = np.arange(-k, k + 1) * 0.5, tuple(np.arange(-2, 3) * np.pi / 16)   # (as fine_last)
        cur_fl = {}

        def _flsc(fr_, fh_, th_):                             # score() without its counters
            return fs_.metric(bc.llrs(r[fr_], fh_, th_, sigma2))

        def _fldec(fr_, fh_, th_):                            # decode() of one refine2 round without its counters
            fr_, fh_, th_ = np.asarray(fr_), np.array(fh_, float), np.asarray(th_, float)
            n_ = len(fr_)
            rc_ = bf.premf(r_mf[fr_], rx[fr_], fh_) if p["premf_dec"] else r[fr_]
            d_, okm_, _ = code.decode(bc.llrs(rc_, fh_, th_, sigma2), return_info=True)
            psm_ = _flpsn(n_)
            okr_ = np.full(n_, -1, np.int8)
            psr_ = np.full((n_, len(FZ_Q)), np.nan, np.float32)
            ar_, rr_, am_, rm_ = (np.zeros(n_, bool) for _ in range(4))
            jr = np.where(~okm_ | bool(FLO["retry_all"]))[0] if p["ca_retry"] else np.zeros(0, int)
            if len(jr):                                       # the CA retry (as decode: on the main's rc, fh, th)
                _, cwh = fs_.metric_cw(bc.llrs(rc_[jr], fh_[jr], th_[jr], sigma2))
                fca, tca = bf.code_aided(rc_[jr], fh_[jr], cwh, 2)
                d2, ok2, _ = code.decode(bc.llrs(rc_[jr], fca, tca, sigma2), return_info=True)
                okr_[jr], psr_[jr] = ok2, _flpsn(len(jr))
                if ok2.any():                                 # its re-encoding check at its own CFO (decode's fh edit)
                    w_ = jr[ok2]
                    ar_[w_] = bf.reencode_rho(code, rc_[w_], d2[ok2], fca[ok2]) > thr_fl
                    rr_[w_] = ar_[w_] & (d2[ok2] == p["truth"][fr_[w_]]).all(1)
            if okm_.any():
                am_[okm_] = bf.reencode_rho(code, rc_[okm_], d_[okm_], fh_[okm_]) > thr_fl
                rm_ = am_ & (d_ == p["truth"][fr_]).all(1)
            kind_, hy_, t_, key_ = cur_fl["c"]
            _flrow(fr_, kind_, hy_, t_, 1, okm_, okr_, am_, rm_, ar_, rr_, psm_, psr_)
            acc_ = np.where(okm_, am_, ar_ & (okr_ == 1))
            a_ = cmp_fl.setdefault(key_, [0, False])
            a_[0], a_[1] = max(a_[0], t_ + 1), a_[1] or bool(acc_.any())
            cur_fl["c"] = (kind_, hy_, t_ + 1, key_)
            return np.zeros(n_, bool) if FLO["all_attempts"] else acc_

        for x in flp:
            i_fl = x["pk"]
            th_fl = np.angle(Y4c[i_fl, b4] * np.exp(2j * np.pi * nus * bc.CENTRE)) / pw    # (as the search)
            qa_ = x["pq"].argmin(0)                           # (cells, logged checkpoints): each one's best phase
            for kind_, R_ in ((0, FLO["near"]), (1, FLO["fine"])):
                if R_ is None:
                    continue
                Tk = p["T"] if kind_ == 0 else p["T_fine"]
                for c_fl in range(max(0, x["ct"] - int(R_)), min(len(g), x["ct"] + int(R_) + 1)):
                    for q_fl in sorted(set(qa_[c_fl].tolist())):
                        po_ = int(qph[q_fl]) % 8
                        a_ = cmp_fl.get((i_fl, c_fl, po_, kind_), [0, False])
                        if a_[0] >= Tk or (a_[1] and not FLO["all_attempts"]):
                            continue                          # complete in the rows already
                        if kind_ == 1 and cmp_fl.get((i_fl, c_fl, po_, 0), [0, False])[1]:
                            continue                          # fine_last: only after the standard refine2 failed
                        cur_fl["c"] = (kind_, [(c_fl, po_)], 0, (i_fl, c_fl, po_, kind_))
                        ref_fl([(i_fl, g[c_fl], th_fl[c_fl] + qph[q_fl] * np.pi / 4)], roffs if kind_ == 0 else fine_fl,
                               sub if kind_ == 0 else subf_fl, Tk, r, _flsc, _fldec, pas_fl)
    if p["cap_core"]:                                         # hard MAC cap per core (see DEFAULT)
        cp_ = crit + dcritp + seqc + (macs - pmac - dmac - seqm) / KP
        over = cp_ > p["cap_core"]
        st["cap_hit"] = st.get("cap_hit", 0) + int(over.sum())
        st["cap_hit_passed"] = st.get("cap_hit_passed", 0) + int((over & passed).sum())
        if p["truth"] is not None:
            st["cap_hit_right"] = st.get("cap_hit_right", 0) + int((over & passed & (out == p["truth"]).all(1)).sum())
        sc_ = np.where(over, p["cap_core"] / np.maximum(cp_, 1.0), 1.0)
        for v_ in (macs, pmac, crit, crit_g, crit_gh, dmac, dcrit, dcritp, seqc, seqm, d4a, d4b, m_fast):
            v_ *= sc_
        passed[over] = False                                  # no packet: never equal to the data (2 is not a bit)
        out[over] = 2
        f_fin[over] = np.nan
    st["macs"] = st.get("macs", 0.0) + float(macs.sum())
    if p["truth"] is not None:                                # (measurement) right decodes per accepting stage
        okr = passed & (out == p["truth"]).all(1)
        for s_ in range(1, 6):
            st[f"stage_{s_}"] = st.get(f"stage_{s_}", 0) + int((okr & (stg == s_)).sum())
        st["stage_frames"] = st.get("stage_frames", 0) + B
    st["core_macs"] = st.get("core_macs", 0.0) + float((macs / cores).sum())
    st["cores"] = st.get("cores", 0.0) + float(cores.sum())
    st["passes"] = st.get("passes", 0.0) + float(passes.sum())
    st["crit_macs"] = st.get("crit_macs", 0.0) + float((macs - pmac + crit).sum())   # MACs on the critical path
    st["crit_lp_macs"] = st.get("crit_lp_macs", 0.0) + float((macs - pmac + crit - dmac + dcrit).sum())   # with the
    cpar = crit + dcritp + seqc + (macs - pmac - dmac - seqm) / KP    # the serial steps split over KP cores too
    st["crit_par_macs"] = st.get("crit_par_macs", 0.0) + float(cpar.sum())
    st["crit_par_h_macs"] = st.get("crit_par_h_macs", 0.0) + float((cpar - crit_g + crit_gh).sum())   # (measurement)
                                                              # the same with the grid scheduled per hypothesis
    st["d4b_clamped"] = st.get("d4b_clamped", 0) + int((d4b > 1.0).sum())   # (safety: grouping never costs more
    d4b = np.minimum(d4b, 0.0)                                # than d4a; the packets where the clamp fired, > 1 MAC)
    st["crit_par_d4a_macs"] = st.get("crit_par_d4a_macs", 0.0) + float((cpar + d4a).sum())   # (measurement) 4
    st["crit_par_d4b_macs"] = st.get("crit_par_d4b_macs", 0.0) + float((cpar + d4a + d4b).sum())   # decodes at once
    st["crit_par_h_d4a_macs"] = st.get("crit_par_h_d4a_macs", 0.0) + float((cpar - crit_g + crit_gh + d4a).sum())
    st["crit_par_h_d4b_macs"] = st.get("crit_par_h_d4b_macs", 0.0) + float((cpar - crit_g + crit_gh + d4a + d4b).sum())
    if p["mac_acc"] is not None:                              # (measurement) per-packet MACs log (DEFAULT mac_acc): the
        p["mac_acc"].append(dict(                             # search stops at its first accepted call, so a right
            c_hd4a=(cpar - crit_g + crit_gh + d4a).astype(np.float32),   # decode's cost = its cost up to acceptance
            c_d4a=(cpar + d4a).astype(np.float32), cpar=cpar.astype(np.float32), macs=macs.astype(np.float32),
            passed=passed.copy(), right=(passed & (out == p["truth"]).all(1)) if p["truth"] is not None
            else np.zeros(B, bool)))
    if flo:                                                   # (fulllog) this call's groups (fl_save): flp / flh rows,
        import json                                           # flb every packet's result and costs, flc the constants
        cid, i0 = p["dec_id"] if p["dec_id"] is not None else (int(uid[0] // 1000), 0)
        acc = p["dec_acc"]
        if flp:
            acc.setdefault("flp", []).append(dict(
                pk=(i0 + np.array([x["pk"] for x in flp])).astype(np.int32), pq=np.stack([x["pq"] for x in flp]),
                lp=np.stack([x["lp"] for x in flp]), lpr=np.stack([x["lpr"] for x in flp]),
                ct=np.array([x["ct"] for x in flp], np.int16), snap=np.stack([x["snap"] for x in flp])))
        if flh:
            Hfl_ = {q: np.concatenate([x[q] for x in flh]) for q in flh[0]}
            Hfl_["pk"] = (i0 + Hfl_["pk"]).astype(np.int32)   # packet index in the chunk
            acc.setdefault("flh", []).append(Hfl_)
        acc.setdefault("flb", []).append(dict(
            pk=(i0 + np.arange(B)).astype(np.int32), search=np.isin(np.arange(B), rem), passed=passed.copy(),
            right=passed & (out == p["truth"]).all(1), stage=stg.astype(np.int8), c_hd4a=cpar - crit_g + crit_gh + d4a,
            c_d4a=cpar + d4a, cpar=cpar.copy(), macs=macs.copy()))
        fzr_fl = getattr(code, "fz_rec", None) if fzo else None   # the F5 stop's node per FZ_Q (every decode's)
        Pfl_ = {q: (p[q] if not isinstance(p[q], np.ndarray) else p[q].tolist()) for q in (
            "ck", "ck_keep", "ck_min", "ck_win", "tau", "kmin", "win", "final", "batch", "first_k", "phase_keep",
            "ncand", "z0", "T", "T_fine", "final_post", "fine_last", "cores", "ck_charge_all", "old_acct", "ca_retry",
            "premf_dec", "reencode", "bpsk_sq", "nopi", "equiv", "q_fix", "cost", "ck_useful", "rate", "code_rate")}
        fm_ = dict(v=1, snr=float(snr), numpy=np.__version__, G=int(len(g)), k=int(k), nph=int(nph),
                   qs=[int(x) for x in qs], qph=[int(x) for x in qph], cks=[float(x) for x in cks], FLF=FLF,
                   frL=[float(x) for x in frL], shL=[float(x) for x in shL], cnn=cnn,
                   bs=[0] if (p["equiv"] or p["bpsk_sq"]) else [0, 1, 2, 3] if p["nopi"] else [0, 1],
                   H_std=int(len(roffs) * len(sub)), H_fine=int((2 * k + 1) * 5), Kc=int(Kc), KP=int(KP),
                   ncore=None if ncore is None else int(ncore), rx=Pfl_, fl=FLO, fz_q=list(FZ_Q),
                   fz_tr=None if fzr_fl is None else [float(x) for x in fz_share(code.frozen, fzr_fl["pos_s"])],
                   fz_nb=None if fzr_fl is None else [int(x) for x in fzr_fl["nb_s"]],
                   mac=dict(m_met=float(m_met), derot=float(derot), cmul=float(vp.MAC["cmul"]),
                            dec=float(vp.MAC["decode"]), llr=float(vp.MAC["llr"]), reenc=float(vp.MAC["reencode"]),
                            premf=float(vp.PREMF_FAIR_MACS), ca2=float(bf.CA_MACS(2)), ckm=float(ck_macs(len(g))),
                            n_dec=int(n_dec)))
        acc.setdefault("flc", []).append(dict(js=np.array([json.dumps(
            fm_, default=lambda o: o.item() if hasattr(o, "item") else list(o))])))
    if sto:                                                   # (measurement) stage_acc (DEFAULT): this call's packets
        s_cost[:, 5] = np.stack([macs, cpar + d4a, cpar - crit_g + crit_gh + d4a], -1)
        p["stage_acc"].append(dict(reach=s_reach, cost=s_cost.astype(np.float32), stage=stg.astype(np.int8),
                                   passed=passed.copy(), right=(passed & (out == p["truth"]).all(1))
                                   if p["truth"] is not None else np.zeros(B, bool), n_hyp=n_hyp.astype(np.int32)))
    st["d4b_waste"] = st.get("d4b_waste", 0.0) + float(d4w.sum())   # (upper bound on d4b's extra total MACs)
    st["crit_par_serial"] = st.get("crit_par_serial", 0.0) + float((seqc + (macs - pmac - dmac - seqm) / KP).sum())
    st["crit_par_dec"] = st.get("crit_par_dec", 0.0) + float(dcritp.sum())
    hist = [("mh", macs), ("ch", macs - pmac + crit - dmac + dcrit)]
    if p["truth"] is not None:          # (measurement) the same for the RIGHT decodes only: the search stops at the first
        good = passed & (out == p["truth"]).all(1)    # accepted pass, so a MAC cap C turns exactly the right decodes
        hist += [("mg", macs[good]), ("cg", (macs - pmac + crit - dmac + dcrit)[good])]   # above C into errors
    for tag, v in hist:                                       # per-packet histograms, 0.1-decade bins
        bins = np.clip(np.floor((np.log10(np.maximum(v, 1.0)) - 5.0) * 10), 0, 39).astype(int)   # from 1e5 (tails)
        for b_, n_ in zip(*np.unique(bins, return_counts=True)):
            st[f"{tag}_{b_:02d}"] = st.get(f"{tag}_{b_:02d}", 0) + int(n_)
    phist = [("ph", cpar)] + ([("pg", cpar[good])] if p["truth"] is not None else [])
    for tag, v in phist:                                      # MACs per core (the standard critical path), all / right
        bins = np.clip(np.floor((np.log10(np.maximum(v, 1.0)) - 4.0) * 20), 0, 99).astype(int)   # decodes: 0.05-decade
        for b_, n_ in zip(*np.unique(bins, return_counts=True)):                                  # bins from 1e4
            st[f"{tag}_{b_:02d}"] = st.get(f"{tag}_{b_:02d}", 0) + int(n_)
    st["macs_fast"] = st.get("macs_fast", 0.0) + float(m_fast.sum())    # MAC breakdown: fast path, parallel
    st["macs_par"] = st.get("macs_par", 0.0) + float(pmac.sum())         # search / scoring, CA-SCL decodes (the
    st["macs_dec"] = st.get("macs_dec", 0.0) + float(dmac.sum())         # rest: serial steps after the fast path)
    if rdo:                                                   # (measurement) ref_diag: per packet, a true-cell candidate
        R_ = {q: np.concatenate([x[q] for x in rdrows]) for q in rdrows[0]} if rdrows else None   # refined and lost
        nrw, ntr = np.zeros(B, int), np.zeros(B, int)
        if R_ is not None:
            np.add.at(nrw, R_["pk"], 1)
            np.add.at(ntr, R_["pk"], R_["true_cell"].astype(int))
        okr_ = passed & (out == p["truth"]).all(1)
        for nm, v in (("pk", np.ones(B, bool)), ("pk_refined", nrw > 0), ("pk_true", ntr > 0), ("pk_right", okr_),
                      ("pk_fail", ~okr_), ("pk_fail_refined", ~okr_ & (nrw > 0)), ("pk_lost", ~okr_ & (ntr > 0))):
            st[f"rd_{nm}"] = st.get(f"rd_{nm}", 0) + int(v.sum())
        cid, i0 = p["dec_id"] if p["dec_id"] is not None else (int(uid[0] // 1000), 0)
        q_row = dict(pkt=(i0 + np.arange(B)).astype(np.int32), n_rows=nrw.astype(np.int16),
                     n_true=ntr.astype(np.int16), any_true=ntr > 0, passed=passed.copy(), right=okr_,
                     lost=~okr_ & (ntr > 0), stage=stg.astype(np.int8), kstep=np.full(B, k, np.int8),
                     truth_f=np.asarray(p["truth_f"], np.float32),
                     f_fin_err=((f_fin - p["truth_f"]) / bc.STEP).astype(np.float32),
                     cpar=cpar.astype(np.float32), macs=macs.astype(np.float32), snr_rx=np.full(B, snr, np.float32))
        acc = p["dec_acc"] if p["dec_acc"] is not None else {}
        if R_ is not None:
            R_["pk"] = (i0 + R_["pk"]).astype(np.int32)       # packet index in the chunk (uid = chunk_seed, pk)
            acc.setdefault("r", []).append(R_)
        acc.setdefault("q", []).append(q_row)
        if p["dec_acc"] is None:                              # no chunk accumulator (a direct call): one file per call
            import os
            dec_save(acc, os.path.join(p["ref_diag"], f"rd_{cid}.npz"), snr=snr, chunk_seed=cid)
    if fzo:                                                   # (measurement) fz_diag: this call's decode rows + packets
        code.fz_q = None
        cid, i0 = p["dec_id"] if p["dec_id"] is not None else (int(uid[0] // 1000), 0)
        acc = p["dec_acc"] if p["dec_acc"] is not None else {}
        nfz = np.zeros(B, int)
        for gq in ("f", "j"):                                 # CA-SCL-8 rows / joint-list rows
            xs = [x for g_, x in fzrows if g_ == gq]
            if xs:
                F_ = {q: np.concatenate([x[q] for x in xs]) for q in xs[0]}
                np.add.at(nfz, F_["pk"], 1)
                F_["pk"] = (i0 + F_["pk"]).astype(np.int32)   # packet index in the chunk (uid = chunk_seed, pk)
                acc.setdefault(gq, []).append(F_)
        okr_ = passed & (out == p["truth"]).all(1)
        acc.setdefault("g", []).append(dict(
            pkt=(i0 + np.arange(B)).astype(np.int32), n_rows=nfz.astype(np.int16), n_rnd=fzr.astype(np.int16),
            passed=passed.copy(), right=okr_, stage=stg.astype(np.int8), kstep=np.full(B, k, np.int8),
            truth_f=np.asarray(p["truth_f"], np.float32), cpar=cpar.astype(np.float32), macs=macs.astype(np.float32),
            dmac=dmac.astype(np.float32), dcritp=dcritp.astype(np.float32), d4a=d4a.astype(np.float32),
            snr_rx=np.full(B, snr, np.float32)))
        if p["dec_acc"] is None:                              # no chunk accumulator (a direct call): one file per call
            import os
            dec_save(acc, os.path.join(p["fz_diag"], f"fz_{cid}.npz"), snr=snr, chunk_seed=cid)
    if p["s3dump"] is not None and p["truth"] is not None:  # (measurement) BLIND_IMPLEMENTATION/testing/ dump: Stage 3 rows + packets
        import os
        os.makedirs(p["s3dump"], exist_ok=True)
        good = passed & (out == p["truth"]).all(1)
        np.savez_compressed(os.path.join(p["s3dump"], f"s3_{uid[0]}.npz"),
                            rows=np.array(s3rows, float).reshape(-1, 19), uid=uid, passed=passed, good=good,
                            fast=pass_fast, macs=macs, cpar=cpar, m_fast=m_fast, dmac=dmac, snr=snr,
                            truth_f=p["truth_f"] if p["truth_f"] is not None else np.full(B, np.nan))
    if dd:                                                    # (measurement) decode dump: this call's rows + packets
        cid, i0 = p["dec_id"] if p["dec_id"] is not None else (int(uid[0] // 1000), 0)
        D = {q: np.concatenate([x[q] for x in drows]) for q in drows[0]} if drows else None
        fc_ = np.full(B, -1)                                  # the first attempt within +-0.5 STEP of the true CFO
        if D is not None and D["in_cell"].any():
            a_ = np.full(B, 1 << 30)
            np.minimum.at(a_, D["pk"][D["in_cell"]], D["att"][D["in_cell"]].astype(int))
            fc_ = np.where(a_ < 1 << 30, a_, -1)
        okr_ = passed & (out == p["truth"]).all(1)
        pk_row.update(pkt=(i0 + np.arange(B)).astype(np.int32), truth_f=np.asarray(p["truth_f"], np.float32),
                      truth_th=(np.asarray(p["truth_th"], np.float32) if p["truth_th"] is not None
                                else np.full(B, np.nan, np.float32)),
                      true_cell=np.abs(g[None] - np.asarray(p["truth_f"])[:, None]).argmin(1).astype(np.int16),
                      kstep=np.full(B, k, np.int8), n_cells=np.full(B, len(g), np.int16), stage=stg.astype(np.int8),
                      nph=np.full(B, nph, np.int8), q_fix=np.full(B, bool(p["q_fix"])),   # d_q: index into qs
                      passed=passed.copy(), right=okr_, n_dec=natt.astype(np.int16), first_cell=fc_.astype(np.int16),
                      cpar=cpar.astype(np.float32), macs=macs.astype(np.float32), m_fast=m_fast.astype(np.float32),
                      f_fin_err=((f_fin - p["truth_f"]) / bc.STEP).astype(np.float32),
                      snr_rx=np.full(B, snr, np.float32))
        acc = p["dec_acc"] if p["dec_acc"] is not None else {}
        if D is not None:
            D["pk"] = (i0 + D["pk"]).astype(np.int32)         # packet index in the chunk (uid = chunk_seed, pk)
            acc.setdefault("d", []).append(D)
        acc.setdefault("p", []).append(pk_row)
        if p["dec_acc"] is None:                              # no chunk accumulator (a direct call): one file per call
            import os
            dec_save(acc, os.path.join(p["dec_dump"], f"dec_{cid}.npz"), snr=snr, chunk_seed=cid)
    st["crc_undetected"] = st.get("crc_undetected", 0) + int(crc_wrong.sum())   # list paths of a decode in parallel
    st["crit_grid"] = st.get("crit_grid", 0.0) + float(crit_g.sum())    # breakdown of crit_lp: grid passes, the
    st["crit_score"] = st.get("crit_score", 0.0) + float((crit - crit_g).sum())   # hypothesis scoring, the decodes;
    st["crit_dec"] = st.get("crit_dec", 0.0) + float(dcrit.sum())       # the rest is serial (FFT, retry, checks)
    return out, passed, f_fin, f0
