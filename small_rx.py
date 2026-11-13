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
               dec_dump=None, dec_acc=None, dec_id=None)   # (measurement) BLIND_IMPLEMENTATION/testing/ decode dump:
                                # dec_dump a directory (None = off): one row per decode attempt + one per packet
                                # (dec_save); dec_acc / dec_id (set by blind_ber.simulate): the chunk's accumulator
                                # and (chunk_seed, index of the batch's first packet in the chunk)
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


def ck_logp(mode, c, x):
    """The checkpoint NN's log P(cell) at CK_FR[c] (skip = the z-test feature)."""
    return nn_logp(mode, x, f"ck_nn_{mode}_c{c}", NF)


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


def dec_save(acc, path, **meta):
    """(measurement) the decode dump of one chunk (acc: small_receive's dec_acc): d_<field> one row per decode
    attempt, p_<field> one row per packet, + the scalars meta (rate, snr, rx, chunk_seed)."""
    import os
    if not acc.get("d") and not acc.get("p"):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = {f"{g}_{k}": np.concatenate([x[k] for x in acc[g]]) for g in ("d", "p") if acc.get(g) for k in acc[g][0]}
    np.savez_compressed(path, **out, **{k: np.asarray(v) for k, v in meta.items()})


def small_receive(r, rx, snr, code, sigma2, st, spec, sym=None):
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
    B = len(r)
    k = p["kstep"] or bf.grid_step(p["rate"], snr)          # kstep: a fixed grid step (STEP units) at every SNR
    g = bf.grid(k)["f"]
    nph = p["nph"] or (4 if snr < -1 else 2)
    qs = np.arange(nph) * (2 if nph == 2 else 1)              # phase offsets of a cell (pi/4 units)
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
    nl = [max(1, int((lv <= c * bc.N_BITS).sum())) for c in cks]
    frac = lv[np.array(nl) - 1] / bc.N_BITS
    # cost of the decode up to each checkpoint, as a share of a full metric pass: linear in the codeword fraction, or
    # the Fast-SSC tree cost of the leaves decoded so far ("tree": at R = 1/10 the mostly frozen first half is 36 %)
    sh = cost_share(fsn.plan, frac) if p["cost"] == "tree" else frac
    m_met, derot = vp.metric_macs(code.A), vp.MAC["cmul"] * bc.N_SYM
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
    dp8 = vp.MAC["decode"] / 8 * np.ceil(8 / Kc) + code.K * _lg8 * (_lg8 + 1) / 2   # a CA-SCL-8 decode's path part
    ctx = {"tag": "fast", "log": None}                        # (measurement) origin of the decodes / d4b loop records
    # (measurement) decode dump (dec_dump): one row per decode attempt; ctx "sc" the last score() call (fr, fh, th, M),
    # "H" (hypotheses, sub-offsets) per candidate of that call, "meta" the grid state per candidate (_gm), "jl" the
    # joint decode's list; nothing here enters macs / pmac / dmac / crit or a decision
    dd = p["dec_dump"] is not None and p["truth"] is not None and p["truth_f"] is not None
    ctx.update(sc=None, H=None, meta=None, jl=None)
    drows, natt = [], np.zeros(B, int)                        # decode rows (dicts of arrays per call), attempts so far

    def _cpar(fr_):                                           # (measurement) crit_par / total MACs of packets fr_ so far
        return (crit + dcritp + seqc + (macs - pmac - dmac - seqm) / KP)[fr_], macs[fr_].copy()

    def _lst(Lc):                                             # (measurement) every list path of the last decode (code's
        pm_ = code._pm.copy()                                 # traceback state): info bits (n, Ls, K), PMs, channel LLRs
        n_, Ls_ = pm_.shape
        info = np.empty((n_, Ls_, code.K), np.uint8)
        path = np.broadcast_to(np.arange(Ls_), (n_, Ls_))
        rows = np.arange(n_)[:, None]
        for k_ in range(code.K - 1, -1, -1):
            info[:, :, k_] = code._bits[k_][rows, path]
            path = code._parents[k_][rows, path]
        return info, pm_, Lc

    def _thr():                                               # the re-encoding threshold (as in decode)
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
        if isinstance(code, bc.PiCode):
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
                  + code.K * 2 * L * np.log2(2 * L))
        lg = np.log2(2 * L)                                   # bitonic sort of 2L metrics: lg (lg + 1) / 2 stages
        np.add.at(dcritp, fr, vp.MAC["decode"] / 8 * np.ceil(L / Kc) + vp.MAC["llr"] * H / KP
                  + code.K * lg * (lg + 1) / 2)

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

    def decode(fr, fh, th, pre=None):
        fr, fh, th = np.asarray(fr), np.asarray(fh, float), np.asarray(th, float)
        c0_ = _cpar(fr) if dd else None                       # (measurement) cost so far (joint: incl. its list decode)
        lm_ = rq_ = None
        if pre is not None:                                   # a joint decode's chosen path (decode_joint)
            rc, d, ok = pre
            lm_ = ctx["jl"]
        else:
            if p["premf_dec"]:                                # the MF de-rotated at the candidate's own CFO
                rc = bf.premf(r_mf[fr], rx[fr], fh)
                np.add.at(macs, fr, vp.PREMF_FAIR_MACS)
            else:
                rc = r[fr]
            Lm_ = bc.llrs(rc, fh, th, sigma2)
            d, ok, _ = code.decode(Lm_, return_info=True)
            if dd:
                lm_ = _lst(Lm_)
            st["decodes"] += len(fr)
            _dec_cost(fr, 8)
            u_, n_ = np.unique(fr, return_counts=True)        # (measurement) d4a: ceil(n / 4) decode rounds
            d4a[u_] += (np.ceil(n_ / 4) - n_) * dp8
        if dd:                                                # (measurement) the main decodes before the retry edits
            dm_, okm_, fhm_ = d.copy(), ok.copy(), fh.copy()  # d / ok / fh in place
        rtry = np.zeros(len(fr), bool)                        # (measurement) CRC failed -> the CA retry ran
        if p["ca_retry"] and not ok.all():                    # code-aided CFO / phase from the SC hard decisions
            j = np.where(~ok)[0]
            rtry[j] = True
            c1_ = _cpar(fr[j]) if dd else None                # (measurement) cost so far, before the retry
            u_, n_ = np.unique(fr[j], return_counts=True)     # (measurement) d4a: the retries' SC passes in
            d4a[u_] += (np.ceil(n_ / 4) - n_) * dp8 + (np.ceil(n_ / KP) - n_) * m_met   # parallel, 4 decodes at once
            _, cwh = fs_.metric_cw(bc.llrs(rc[j], fh[j], th[j], sigma2))
            fca, tca = bf.code_aided(rc[j], fh[j], cwh, 2)
            L2_ = bc.llrs(rc[j], fca, tca, sigma2)
            d2, ok2, _ = code.decode(L2_, return_info=True)
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
            ok_re[j] = rho > thr
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
        if pos is not None and ok.any():
            j = np.where(ok)[0]
            np.add.at(macs, fr[j], 2 * vp.MAC["cmul"] * len(pos))
            zpj = rc[j][:, pos] * np.conj(sym[fr[j]][:, pos])
            c = bf.pilot_coherent(code, rc[j], d[j], fh[j], zpj, pos)
            ok[j] = c > len(pos) - p["pc_sigmas"] * np.sqrt(len(pos) / (2 * s_lin))
        _truth(fr, d, ok_crc, ok if p["reencode"] else ok & ok_re)
        if p["truth"] is not None and ok.any():               # (measurement) accepted packets per origin, main
            ia_ = np.where(ok)[0]                             # decode / CA retry, right / wrong: once per packet
            u_, inv_, cnt_ = np.unique(fr[ia_], return_inverse=True, return_counts=True)   # per call, by the row
            dl_ = np.zeros(len(u_), int)                      # delivered (out[w] = d[ok]: the last accepted row)
            np.maximum.at(dl_, inv_, ia_)
            wr_ = (d[dl_] != p["truth"][fr[dl_]]).any(1)
            rt_ = rtry[dl_]
            for m_, nm_ in ((~rt_ & ~wr_, "main_right"), (~rt_ & wr_, "main_wrong"),
                            (rt_ & ~wr_, "retry_right"), (rt_ & wr_, "retry_wrong")):
                if m_.any():
                    st[f"acc_{ctx['tag']}_{nm_}"] = st.get(f"acc_{ctx['tag']}_{nm_}", 0) + int(m_.sum())
            if (cnt_ > 1).any():                              # calls accepting > 1 hypothesis of one packet
                st["acc_multi"] = st.get("acc_multi", 0) + int((cnt_ > 1).sum())
        if ctx["log"] is not None:                            # (measurement) d4b: (retried, accepted at the main
            ctx["log"] += list(zip(rtry.tolist(), (ok & ~rtry).tolist(), ok.tolist()))   # decode, accepted)
        if dd and lm_ is not None:                            # (measurement) decode dump rows
            _dlog(fr, fhm_, th, rc, lm_, dm_, okm_, rq_, ok, rtry, c0_)
        first = ~have[fr]
        out[fr[first]], have[fr[first]], f_fin[fr[first]] = d[first], True, fh[first]
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
        if dd:                                                # (measurement) the shared list, the chosen hypothesis'
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
        TH = bc.phase4(r[np.full(len(cands), i)], F)
        TH = TH + np.round((t_[:, None] - TH) / (np.pi / 2)) * (np.pi / 2)
        F = np.repeat(F, len(sub), 1)
        TH = (TH[:, :, None] + np.array(sub)[None, None]).reshape(len(cands), -1)
        M = score(np.full(F.size, i), F.ravel(), TH.ravel()).reshape(F.shape)
        o = np.argsort(M, 1)[:, :p["joint"][0]]
        decode_joint(i, np.take_along_axis(F, o, 1).ravel(), np.take_along_axis(TH, o, 1).ravel())

    def score(fr, fh, th):
        M = fs_.metric(bc.llrs(r[fr], fh, th, sigma2))
        st["metric_evals"] += len(fr)
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

    def refine2(*a):                                          # bf._refine2, with the BLIND_IMPLEMENTATION/testing/ Stage 3 dump
        if p["s3dump"] is not None and p["truth"] is not None:
            _s3dump(a[0], a[1], a[2])
        ctx["sc"], ctx["H"] = None, (len(a[1]) * len(a[2]), len(a[2]))   # (measurement) decode dump: score layout
        if p["s3_dd"] and a[1] is roffs:                     # (the fine_last rescue keeps its own fine grid)
            return refine_dd(a[0], a[3])
        return bf._refine2(*a)

    def _rec(l4):                                             # (measurement) d4b: the next candidate's records
        l4.append([])
        ctx["log"] = l4[-1]

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
    y4 = -(r ** 4)
    Y4c = np.fft.fft(y4, nf, axis=1)
    Y4 = np.abs(Y4c)
    nu_b = np.fft.fftfreq(nf)
    Y4m = np.where(np.abs(nu_b)[None] <= 4 * bc.MAX_CFO + 2.0 / nf, Y4, 0.0)
    macs += 2 * 4 * bc.N_SYM + vp.fft_macs(nf)
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
            if q == 0 or live[:, q].any():
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
    f0 = np.clip((nu_b[kb] + off / nf) / 4, -bc.MAX_CFO, bc.MAX_CFO)
    macs += 8
    r_mf = r
    r = bf.premf(r_mf, rx, f0)                                 # pre-MF de-rotation at the 4th-power estimate
    macs += vp.PREMF_FAIR_MACS
    y4 = -(r ** 4)
    Y4c = np.fft.fft(y4, nf, axis=1)                          # (the cells' phases; counted as the FFT above)
    macs += 2 * 4 * bc.N_SYM + vp.fft_macs(nf)
    if pos is not None:
        zp = r[:, pos] * np.conj(sym[:, pos])
    if snr >= p["s0_snr"]:
        th0 = bc.phase4(r, f0)
        macs += vp.MAC["phase4"]
        fr = np.arange(B)
        if pos is not None:                                   # the pi/2 branch by the pilots' phase
            zz = np.sum(zp * np.exp(-2j * np.pi * f0[:, None] * (pos - bc.CENTRE)[None]), 1)
            rel = ((np.angle(zz) - th0) / (np.pi / 2)) % 2
            br = (np.abs(rel - 1) < np.minimum(rel, 2 - rel)).astype(int)
            macs += vp.MAC["cmul"] * 3 * len(pos)
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
    stg = np.where(passed, 1, 0)                              # (measurement) the stage that accepted each packet:
    # 1 fast path, 2 the grid search's own decodes, 3 the final candidates, 4 rescue (final_post), 5 rescue (fine_last)
    # 2. search over the whole small grid, cell by cell for each remaining packet
    roffs = np.arange(-(k // 2), k // 2 + 1)
    sub = (-np.pi / 12, 0.0, np.pi / 12) if (nph == 4 or p["sub3"]) else (0.0,)   # phase sub-offsets of a candidate
    H_s = 1 if p["s3_dd"] else len(roffs) * len(sub)          # (measurement) d4b: hypotheses scored per candidate
    T_s = min(p["T"], 2) if p["s3_dd"] else p["T"]            # and decodes per candidate (refine_dd: <= 2)
    b4 = np.round(((4 * g) % 1.0) * nf).astype(int) % nf
    nus = 4 * g + ((b4 / nf - (4 * g) % 1.0 + 0.5) % 1.0 - 0.5)
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
        il = np.array([max(1, int((lv <= c * bc.N_BITS).sum())) for c in CK_FR]) - 1
        D = np.empty((len(rem), len(g), nph, len(CK_FR), 2), np.float32)
        for n, i in enumerate(rem):
            th = np.angle(Y4c[i, b4] * np.exp(2j * np.pi * nus * bc.CENTRE)) / 4
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
        il = np.array([max(1, int((lv <= c * bc.N_BITS).sum())) for c in CK_FR]) - 1
        jnn = cks.index(CK_FR[cnn])
        ck_mode = "pilots" if pos is not None else "blind"
    for i in rem:
        th = np.angle(Y4c[i, b4] * np.exp(2j * np.pi * nus * bc.CENTRE)) / 4     # the cells' 4th-power phases
        Pq = np.empty((nph, len(g), len(cks)), np.float32)
        ri = np.repeat(r[i:i + 1], len(g), 0)
        if cnn is not None:
            Dq = np.empty((len(g), nph, len(CK_FR), 2), np.float32)
        for jq, q in enumerate(qs):
            llr = bc.llrs(ri, g, th + q * np.pi / 4, sigma2)
            v = fsn.metric_nodes(llr)
            Pq[jq] = np.cumsum(v, 1)[:, np.array(nl) - 1]
            if cnn is not None:
                Dq[:, jq, :, 0] = np.cumsum(v, 1)[:, il]
                Dq[:, jq, :, 1] = np.cumsum(v * lr0, 1)[:, il]
        st["metric_evals"] += nph * len(g)
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
                nd = (alive & (paid < sh[j])).sum()           # cells extended in this stage
                passes[i] += np.ceil(nd / ncore) if ncore else (nd > 0)
                if new_acct and qcut:                         # cells paid below a pruning share: its pre-pruning phases
                    L_, C_ = _segs(qcut, qal, paid, alive, sh[j])
                    w_ = m_met * (L_ * C_).sum(1)
                    macs[i] += w_.sum()
                    _par(i, w_, hyp=(L_, C_))
                else:
                    macs[i] += m_met * (qal[alive].sum(1) * np.clip(sh[j] - paid[alive], 0, None)).sum()   # alive cells x
                    _par(i, m_met * qal[alive].sum(1) * np.clip(sh[j] - paid[alive], 0, None), qal[alive].sum(1))
                paid[alive] = np.maximum(paid[alive], sh[j])                                       # phases up to f_
                z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                if j == len(frac) - 1:
                    break
                if cnn is not None and j == jnn:              # the checkpoint NN instead of the z-test here: its
                    n_ = int(np.searchsorted(rem, i))         # shortlist (cumulative probability 1 - ck_keep,
                    lp = ck_logp(ck_mode, cnn, ck_features(XC[n_:n_ + 1], Dq[None], cnn))[0]   # >= ck_min cells)
                    macs[i] += ck_macs(len(g))
                    o = np.argsort(-lp)
                    o = o[alive[o]]
                    if p["ck_win"] is not None and np.exp(lp[o[0]]) > p["ck_win"] and o[0] not in tried:
                        c = int(o[0])                         # a confident NN winner is decoded at once
                        tried.add(c)
                        ctx["tag"] = "early_z"
                        if dd:                                        # (measurement) decode dump: grid state
                            ctx["meta"] = [_gm(c, qb[c, j], j, z, pm, alive, paid, len((tried | spec_tried) - {c}))]
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
                    qal &= np.argsort(np.argsort(sc_, 1), 1) < pk_[1]
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
                    if f_ >= bm[0]:                            # cell's other score terms) continue
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
                            d = np.abs((tp - (th[n_] + qs * np.pi / 4) + np.pi / 2) % np.pi - np.pi / 2)
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
            cs = [c for c in np.argsort(-zf)[:p["ncand"]] if zf[c] > p["z0"] and c not in tried]
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
            for c in cs:
                if dd:                                        # (measurement) decode dump: grid state
                    ctx["meta"] = [_gm(c, qb[c, -1], len(frac) - 1, zf, pm, alive, paid, len((tried | spec_tried) - {c}))]
                tried.add(c)
                _rec(l4)
                refine2([(i, g[c], th[c] + qph[qb[c, -1]] * np.pi / 4)], roffs, sub, p["T"], r, score, decode, passed)
                if passed[i]:
                    break
            if cs:
                _d4b(i, l4, len(cs), T_s, H_s, solo)
            if passed[i]:
                break
        if passed[i]:
            stg[i] = 2
            continue
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
            refine2([(i, g[c], th[c] + qph[qb[c, -1]] * np.pi / 4)], roffs, sub, p["T"], r, score, decode, passed)
            if passed[i]:
                break
        if cs:
            _d4b(i, l4, len(cs), T_s, H_s, solo)
        stg[i] = 3 if passed[i] else 0
        # rescue (as blind_fast's final_post / fine_last), only for packets still undecoded: the next best cells by z
        # on both pi/2 branches, 8 at a time; then the best-metric cells on a half-STEP grid over the cell and its
        # edges x pi/16 phases with more decodes
        if not passed[i] and p["final_post"]:
            cs = [c for c in np.argsort(-zf) if np.isfinite(zf[c]) and c not in tried][:p["final_post"]]
            if dd:                                            # (measurement) decode dump: grid state (q + 4 b)
                pmeta = [_gm(c, qb[c, -1] + 4 * b, len(frac) - 1, zf, pm, alive, paid,
                             len((tried | spec_tried) - {c})) for c in cs for b in (0, 1)]
            tried.update(cs)
            cand = [(i, g[c], th[c] + qph[qb[c, -1]] * np.pi / 4 + b * np.pi / 2) for c in cs for b in (0, 1)]
            ctx["tag"] = "post"
            for a in range(0, len(cand), 8):
                if dd:
                    ctx["meta"] = pmeta[a:a + 8]
                refine2(cand[a:a + 8], roffs, sub, p["T"], r, score, decode, passed)
                if passed[i]:
                    break
            stg[i] = 4 if passed[i] else 0
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
                refine2([(i, g[c], th[c] + qph[qb[c, -1]] * np.pi / 4)], fine, subf, p["T_fine"], r, score, decode,
                            passed)
                if passed[i]:
                    break
            if len(cs):
                _d4b(i, l4, len(cs), p["T_fine"], len(fine) * len(subf), solo)
            stg[i] = 5 if passed[i] else 0
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
