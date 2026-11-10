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

DEFAULT = dict(s0_snr=-99.0, nph=None, z0=4.0, T=2, ncand=4, final=32, rho_n=None, pilots=None, pc_sigmas=5.0,
               fast_peaks=16, fast_ratio=0.7, ck=None, tau=0.0, kmin=16, win=None, rate=None,
               premf_dec=False, ca_retry=False, prior=(), pre_keep=None, sub3=False, coarse=False, pilot_score=0.0,
               final_post=0, fine_last=0, T_fine=6, nn=None, nn_keep=None, nn_min=48, nn_score=0.0, dump=None, dump_pm=None,
               ck_nn=None, ck_keep=1e-3, ck_min=8, ck_win=None, cost="linear", beam=None, keep_early=None,
               race_phase=None, first_k=None, blind_peaks=None, blind_ratio=0.85,
               join_side=False, join_nph=None, join_top=None,
               phase_keep=None, stride=2, top_k=None, batch=None, cores=None, joint=None,
               truth=None, kstep=None, reencode=True,
               snr_err=0.0, re_margin=0.0)
PER_RATE = ("ck", "tau", "kmin", "win", "pre_keep", "pilot_score", "coarse", "nn", "nn_keep", "nn_min", "nn_score", "ck_nn", "ck_keep", "ck_win", "beam", "keep_early", "race_phase", "first_k", "blind_peaks", "phase_keep", "top_k", "batch", "kstep")
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
    B = len(r)
    k = p["kstep"] or bf.grid_step(p["rate"], snr)          # kstep: a fixed grid step (STEP units) at every SNR
    g = bf.grid(k)["f"]
    nph = p["nph"] or (4 if snr < -1 else 2)
    qs = np.arange(nph) * (2 if nph == 2 else 1)              # phase offsets of a cell (pi/4 units)
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
    crc_seen = np.zeros(B, bool)                              # (measurement) a CRC pass seen / the first was wrong
    crc_wrong = np.zeros(B, bool)
    pmac = np.zeros(B)                                        # MACs of the parallel work (grid stages, hypothesis
    crit = np.zeros(B)                                        # scoring) and its critical path: per pass the busiest
    crit_g = np.zeros(B)                                      # (its grid-search part)
                                                              # core; everything else (decodes, FFT, ...) is serial

    def _par(i, cost):                                        # one stage: per-core costs, dealt K at a time in
        cost = cost[cost > 0]                                 # decreasing order -> each pass costs its largest
        if len(cost):
            pmac[i] += cost.sum()
            crit[i] += np.sort(cost)[::-1][::Kc].sum()
            crit_g[i] += np.sort(cost)[::-1][::Kc].sum()
    out = np.zeros((B, code.A), np.uint8)
    passed = np.zeros(B, bool)
    have = np.zeros(B, bool)
    f_fin = np.full(B, np.nan)
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
        if pre is not None:                                   # a joint decode's chosen path (decode_joint)
            rc, d, ok = pre
        else:
            if p["premf_dec"]:                                # the MF de-rotated at the candidate's own CFO
                rc = bf.premf(r_mf[fr], rx[fr], fh)
                np.add.at(macs, fr, vp.PREMF_FAIR_MACS)
            else:
                rc = r[fr]
            d, ok, _ = code.decode(bc.llrs(rc, fh, th, sigma2), return_info=True)
            st["decodes"] += len(fr)
            _dec_cost(fr, 8)
        if p["ca_retry"] and not ok.all():                    # code-aided CFO / phase from the SC hard decisions
            j = np.where(~ok)[0]
            _, cwh = fs_.metric_cw(bc.llrs(rc[j], fh[j], th[j], sigma2))
            fca, tca = bf.code_aided(rc[j], fh[j], cwh, 2)
            d2, ok2, _ = code.decode(bc.llrs(rc[j], fca, tca, sigma2), return_info=True)
            st["decodes"] += len(j)
            np.add.at(macs, fr[j], m_met + vp.MAC["llr"] + bf.CA_MACS(2))
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
        d, ok, _, h = code.decode_joint(bc.llrs(rc, fh, th, sigma2), Lj)
        st["decodes"] += Lj / 8                               # in CA-SCL-8 decode equivalents
        st["joint_decodes"] = st.get("joint_decodes", 0) + 1
        _dec_cost(fr[:1], Lj, H)
        return decode(fr[:1], fh[h:h + 1], th[h:h + 1], pre=(rc[h:h + 1], d[None].copy(), np.array([ok])))

    def refine_joint(i, cands):
        """As bf._refine2 for up to joint[2] candidate cells (CFO, phase) of packet i at once: every offset x phase
        sub-offset scored (in parallel), the best joint[0] hypotheses of each cell decoded jointly (decode_joint)."""
        f_ = np.array([c[0] for c in cands])
        t_ = np.array([c[1] for c in cands])
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
        np.add.at(macs, fr, m_met + derot)
        u, n_ = np.unique(fr, return_counts=True)             # independent hypotheses: in parallel on the cores
        pmac[u] += n_ * (m_met + derot)
        crit[u] += np.ceil(n_ / Kc) * (m_met + derot)
        return M

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

    # 2. search over the whole small grid, cell by cell for each remaining packet
    roffs = np.arange(-(k // 2), k // 2 + 1)
    sub = (-np.pi / 12, 0.0, np.pi / 12) if (nph == 4 or p["sub3"]) else (0.0,)   # phase sub-offsets of a candidate
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
            _par(i, np.full((alive & ~joined).sum(), vp.MAC["cmul"] + derot))
            joined |= alive
            for j, f_ in enumerate(frac):
                nd = (alive & (paid < sh[j])).sum()           # cells extended in this stage
                passes[i] += np.ceil(nd / ncore) if ncore else (nd > 0)
                macs[i] += m_met * (qal[alive].sum(1) * np.clip(sh[j] - paid[alive], 0, None)).sum()   # alive cells x
                _par(i, m_met * qal[alive].sum(1) * np.clip(sh[j] - paid[alive], 0, None))
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
                        bf._refine2([(i, g[c], th[c] + qb[c, j] * np.pi / 4)], roffs, sub, p["T"], r, score, decode,
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
                    qal &= np.argsort(np.argsort(sc_, 1), 1) < pk_[1]
                    P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                    pm, qb = P_.min(0) + adj, P_.argmin(0)
                    z = np.where(alive, _rz(np.where(alive, pm[:, j], np.nan)), -np.inf)
                rp = p["race_phase"]
                if rp is not None and f_ == rp[0]:
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
                        qal &= kp.reshape(qal.shape)
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
                        macs[i] += (new & ~joined).sum() * (vp.MAC["cmul"] + derot)
                        macs[i] += nph * m_met * np.clip(sh[j] - paid[new], 0, None).sum()
                        _par(i, (vp.MAC["cmul"] + derot) * (~joined[new]) + nph * m_met * np.clip(
                            sh[j] - paid[new], 0, None))
                        paid[new] = np.maximum(paid[new], sh[j])
                        joined |= new
                        alive |= new
                        P_ = np.where(qal.T[:, :, None], Pq, np.inf)
                        pm, qb = P_.min(0) + adj, P_.argmin(0)
                    continue
                if p["win"] is not None:                      # early stop: a clear winner ends the CFO search
                    zt = z.copy()
                    zt[list(tried)] = -np.inf
                    c = int(zt.argmax())
                    if zt[c] > p["win"]:
                        tried.add(c)
                        bf._refine2([(i, g[c], th[c] + qb[c, j] * np.pi / 4)], roffs, sub, p["T"], r, score, decode,
                                    passed)
                        if passed[i]:
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
                            tp = th[c] + qb[c, j] * np.pi / 4  # nearest to its parent's best one (mod pi)
                            d = np.abs((tp - (th[n_] + qs * np.pi / 4) + np.pi / 2) % np.pi - np.pi / 2)
                            qal[n_] = False
                            qal[n_, np.argsort(d)[:p["join_nph"]]] = True
                    macs[i] += (new & ~joined).sum() * (vp.MAC["cmul"] + derot)
                    nd = (new & (paid < sh[j])).sum()
                    passes[i] += np.ceil(nd / ncore) if ncore else (nd > 0)
                    macs[i] += m_met * (qal[new].sum(1) * np.clip(sh[j] - paid[new], 0, None)).sum()
                    _par(i, (vp.MAC["cmul"] + derot) * (~joined[new]) + m_met * qal[new].sum(1) * np.clip(
                        sh[j] - paid[new], 0, None))
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
            if p["joint"] is not None:                        # the candidates decoded jointly, joint[2] at a time
                for a in range(0, len(cs), p["joint"][2]):
                    tried.update(cs[a:a + p["joint"][2]])
                    refine_joint(i, [(g[c], th[c] + qb[c, -1] * np.pi / 4) for c in cs[a:a + p["joint"][2]]])
                    if passed[i]:
                        break
                cs = []
            for c in cs:
                tried.add(c)
                bf._refine2([(i, g[c], th[c] + qb[c, -1] * np.pi / 4)], roffs, sub, p["T"], r, score, decode, passed)
                if passed[i]:
                    break
            if passed[i]:
                break
        if passed[i]:
            continue
        cs = [c for c in np.argsort(np.where(alive, pm[:, -1], np.inf))[:p["final"]] if c not in tried]
        if p["joint"] is not None:
            for a in range(0, len(cs), p["joint"][2]):
                tried.update(cs[a:a + p["joint"][2]])
                refine_joint(i, [(g[c], th[c] + qb[c, -1] * np.pi / 4) for c in cs[a:a + p["joint"][2]]])
                if passed[i]:
                    break
            cs = []
        for c in cs:
            tried.add(c)
            bf._refine2([(i, g[c], th[c] + qb[c, -1] * np.pi / 4)], roffs, sub, p["T"], r, score, decode, passed)
            if passed[i]:
                break
        # rescue (as blind_fast's final_post / fine_last), only for packets still undecoded: the next best cells by z
        # on both pi/2 branches, 8 at a time; then the best-metric cells on a half-STEP grid over the cell and its
        # edges x pi/16 phases with more decodes
        if not passed[i] and p["final_post"]:
            cs = [c for c in np.argsort(-zf) if np.isfinite(zf[c]) and c not in tried][:p["final_post"]]
            tried.update(cs)
            cand = [(i, g[c], th[c] + qb[c, -1] * np.pi / 4 + b * np.pi / 2) for c in cs for b in (0, 1)]
            for a in range(0, len(cand), 8):
                bf._refine2(cand[a:a + 8], roffs, sub, p["T"], r, score, decode, passed)
                if passed[i]:
                    break
        if not passed[i] and p["fine_last"]:
            cs = np.argsort(np.where(alive, pm[:, -1], np.inf))[:p["fine_last"]]
            fine = np.arange(-k, k + 1) * 0.5
            subf = tuple(np.arange(-2, 3) * np.pi / 16)
            for c in cs:
                bf._refine2([(i, g[c], th[c] + qb[c, -1] * np.pi / 4)], fine, subf, p["T_fine"], r, score, decode,
                            passed)
                if passed[i]:
                    break
    st["macs"] = st.get("macs", 0.0) + float(macs.sum())
    st["core_macs"] = st.get("core_macs", 0.0) + float((macs / cores).sum())
    st["cores"] = st.get("cores", 0.0) + float(cores.sum())
    st["passes"] = st.get("passes", 0.0) + float(passes.sum())
    st["crit_macs"] = st.get("crit_macs", 0.0) + float((macs - pmac + crit).sum())   # MACs on the critical path
    st["crit_lp_macs"] = st.get("crit_lp_macs", 0.0) + float((macs - pmac + crit - dmac + dcrit).sum())   # with the
    hist = [("mh", macs), ("ch", macs - pmac + crit - dmac + dcrit)]
    if p["truth"] is not None:          # (measurement) the same for the RIGHT decodes only: the search stops at the first
        good = passed & (out == p["truth"]).all(1)    # accepted pass, so a MAC cap C turns exactly the right decodes
        hist += [("mg", macs[good]), ("cg", (macs - pmac + crit - dmac + dcrit)[good])]   # above C into errors
    for tag, v in hist:                                       # per-packet histograms, 0.1-decade bins
        bins = np.clip(np.floor((np.log10(np.maximum(v, 1.0)) - 5.0) * 10), 0, 39).astype(int)   # from 1e5 (tails)
        for b_, n_ in zip(*np.unique(bins, return_counts=True)):
            st[f"{tag}_{b_:02d}"] = st.get(f"{tag}_{b_:02d}", 0) + int(n_)
    st["crc_undetected"] = st.get("crc_undetected", 0) + int(crc_wrong.sum())   # list paths of a decode in parallel
    st["crit_grid"] = st.get("crit_grid", 0.0) + float(crit_g.sum())    # breakdown of crit_lp: grid passes, the
    st["crit_score"] = st.get("crit_score", 0.0) + float((crit - crit_g).sum())   # hypothesis scoring, the decodes;
    st["crit_dec"] = st.get("crit_dec", 0.0) + float(dcrit.sum())       # the rest is serial (FFT, retry, checks)
    return out, passed, f_fin, f0
