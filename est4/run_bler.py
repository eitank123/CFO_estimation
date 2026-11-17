"""
est4: BLER of the fair pilot-aided receivers (pilots OUTSIDE the 1024-symbol packet, energy charged; DVB-RCS2-style
layouts; Wiener phase noise) with est3's back-end, BLIND_IMPLEMENTATION/testing/results/expected_est4.md:

    f_hat from the receiver's own known symbols (est4/estimators.py), on its own burst (est4/common.py layouts)
    -> pre-MF correction at f_hat over the whole burst (est4.common.premf)
    -> per CFO hypothesis f_h: the receiver's phase model (const / interp2 / track / genie) on its known symbols at f_h,
       LLRs of the 1024 data symbols, CA-SCL-8 (N = 2048, CRC-16), CRC + re-encoding check (blind_fast.rho_min and the
       blind receivers' per-rate RHO_N table, at the simulated per-symbol Es/N0)
    -> est3's fair "PM+all" CRC search: decode at f_hat first; for the packets not accepted, score every neighbour
       hypothesis by the list-1 Fast-SSC metric (KP = 32 at a time: metric_rounds) and decode all of them in metric
       order, stopping at the first accepted pass. Neighbours: f_hat + k STEP (0 < |k| <= M), M = max(1, ceil(4 x 1.3
       sqrt(CRB_own) / STEP)) with the CRB of the receiver's own known positions in its burst (unknown phase); the
       genie has no search (M = 0). 2-field layouts (split64, prepost16; 2026-11-15 after e4-smoke: split64 491/800
       errors from lobe jumps of 1/1088): the union over lobes m = -LOBES .. LOBES of f_hat + m / D_lobe + k STEP,
       |k| <= M, without (0, 0), so the decoder chooses the lobe (Barbieri-Colavolpe 2007): (2 LOBES + 1)(2M + 1) - 1
       metric passes per failing packet (split64 at M = 3: 48 = 2 rounds (LOBES = 3) instead of 6 = 1 round)
    -> phase model of the receiver at each hypothesis: --track kalman (default; RTS smoother with q = 2 pi pn, est4/
       estimators.py) or sw (the first sliding-window version, --track-w)
    -> est5 sources (C.EST5, expected_est5.md; the est4 sources keep the code path above exactly): the lobes are the
       layout's alias / lobe spacing 1 / C.lobe_D with C.lobe_n of them each side (vde27, zr32 1; dvbs2, mil110 3;
       wifi128 4; ccsds8 5), and only the lobe hypotheses whose centre f_hat + m / D_lobe is inside |f| <= MAX_CFO + M STEP
       are scored and decoded (per packet; metric_evals / metric_rounds count only those). hyb3: its 2 extra CFO
       candidates c and their lobes join the search (c - f_hat + m / D_lobe + k STEP), hypotheses within STEP / 2 of
       an earlier in-range one dropped. ViaSat UW: the window M from crb_nda4 (the 4th-power bound over the whole burst: its
       CFO comes from the 4th-power FFT, the 16-symbol UW only picks the peak); WiFi pre128: M from C.var_lag (the
       lag-64 fine estimate's own variance, not the 128-symbol CRB)
    -> ARS 2021 sources (C.ARS, lit_ars2021.md section 6) on rcs13, also on the est5 branch: "RCS2-13 lobes" gets the
       +-1/20 alias lobes (C.SRC_LOBES, 1 each side, range-filtered); "Griebel faithful" (C.NO_SEARCH) has window 0:
       one decode at the estimate, no CRC search
    -> faithful variants (C.VARS, expected_variants.md) also on the est5 branch: their layouts' C.lobe_n lobes (WiFi
       real320: 0 via C.SRC_LOBES), range-filtered; window M from crb_nda4 for ViaSat 7653150 / X4phase and hyb3-pre48
       (C.NDA4_WIN), max(crb_nda4, crb_known) for hyb3-pre48 wide (C.WIN_MAX), from C.var_lag for the WiFi real320
       pair, else the CRB of the own known positions. DVB-S2 header90 / SOF26 (C.SCAN): no lobes, offsets k STEP,
       |k| <= SCAN_K (the whole +-MAX_CFO) around c = clip(f_hat, +-(MAX_CFO + STEP)) (= f_hat in range; the first
       decode stays at f_hat), valid if |c + k STEP| <= MAX_CFO + STEP (no holes, no duplicates); their
       in_search = some valid hypothesis within STEP / 2 of f. "split64 ML L4" stays on the est4 branch (split64 ML
       with C.SRC_LOBES 4 lobes)
Measurement only (no effect on decisions or MACs): in_window / in_search = packets with |f_hat - f| <= M STEP / with
some lobe hypothesis f_hat + m / D_lobe within M STEP of f; for 2-field layouts lobe_err (|f_hat - f| > 1 / (2 D_lobe)),
nc_lobe_err (the per-block noncoherent estimate off by more than half a lobe) and nc_pick_err (the lobe of the
joint-ML candidate set nearest the noncoherent estimate is wrong). McNemar pairing (all sources): n10 / n01 = packets
that the source gets wrong and the reference right / right and the reference wrong, reference mcnemar_ref(sources)
("RCS2-13" if in the job, else "RCS2 pre/post", else the first source; its own n10 = n01 = 0); a variant (C.PARENT)
is paired with its parent source instead when the parent is in the job (mcnemar_src).

Packets: IDENTICAL data, CFO, phase (and Wiener phase-noise process) for every receiver. The bursts of the different
layouts have different lengths, so each layout gets its own known symbols and noise from a dedicated rng stream (seeded
from (seed, rate, SNR, chunk, layout)): the noise differs BETWEEN layouts (it cannot be the same: the bursts differ),
the sources of one layout share one burst. The phase-noise path is drawn once per batch for the longest burst and each
layout takes its centred piece (the same process at the same time from the burst centre, zero at every burst centre).
pn is not in the seed: runs at different pn with the same seed have the same packets and the same (scaled) path.
Results are independent of which other sources run.

    python est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --chunks 2 --pn 1e-4 --part e4-smoke-b
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                                   # noqa: E402

from est4 import common as C                                         # noqa: E402
from est4 import estimators as E                                     # noqa: E402

SEARCH_STEP = 1.5e-4 * 512 / C.N_SYM                                 # = est3.run_bler.SEARCH_STEP (7.5e-5)
KP = E.KP
RATE_IDX = {"1/10": 0, "0.15": 1, "2/5": 1, "1/2": 2}               # est3.run_bler.RATE_IDX (0.15 and 2/5 share 1:
                                                                     # use different --seed per rate)
_FIELDS = ("frames", "frame_err", "undetected", "extra_decodes", "se_first", "se_final", "crc_pass", "crc_pass_wrong",
           "re_caught", "re_lost", "time_est", "metric_evals", "metric_rounds", "in_window", "in_search", "lobe_err",
           "nc_lobe_err", "nc_pick_err", "n10", "n01")
LOBES = 3                                                            # lobe hypotheses m = -LOBES .. LOBES (2-field)
SCAN_K = int(np.ceil(2 * C.MAX_CFO / SEARCH_STEP)) + 1               # C.SCAN offsets |k| <= SCAN_K: any f_hat in
                                                                     # +-MAX_CFO reaches any f in +-MAX_CFO (801)


def mcnemar_ref(sources):
    """McNemar reference of a job: "RCS2-13" if present, else "RCS2 pre/post" (e5-pp: hyb3 pairs), else the first."""
    return next((s for s in ("RCS2-13", "RCS2 pre/post") if s in sources), sources[0])


def mcnemar_src(src, sources):
    """McNemar reference of one source: a variant's parent (C.PARENT) if in the job, else mcnemar_ref(sources)."""
    p = C.PARENT.get(src)
    return p if p in sources else mcnemar_ref(sources)


def mac_coef(rate, src, track, pn):
    """(measurement) per-packet MACs log: plot_e4's MACs per core (E.pilot_macs, par) is linear in a packet's extra
    decodes x, metric passes e and metric rounds m: core = c0 + cx x + ce e + cm m. Returns (c0, cx, ce, cm), so the
    mean of the per-packet values = pilot_macs of the json's per-frame means. (cx = the decode round's per-core cost /
    E.PAR_DEC: x extra decodes charged x / PAR_DEC rounds; cap_post's "ceil" variant charges ceil(x / PAR_DEC).)"""
    f = lambda x, e, m: E.pilot_macs(rate, src, x, par=True, m_evals=e, m_rounds=m, mode=track, pn=pn)[1]
    try:                                                   # (a cost-model error must never stop the run: nan
        c0 = f(0.0, 0.0, None)                             # coefficients, flagged by cap_post / maclog_check)
        return c0, f(1.0, 0.0, None) - c0, f(0.0, 1.0, 0.0) - c0, f(0.0, 1.0, 1.0) - f(0.0, 1.0, 0.0)
    except Exception as e_:
        print(f"WARNING maclog: mac_coef({rate!r}, {src!r}) failed: {e_!r}; per-packet MACs = nan", flush=True)
        return (np.nan,) * 4


def window(src, snr):
    """CRC-search half-width M (steps) of a source: from the CRB of its own known positions, at least 1; genie 0."""
    lay, est, _ = C.SOURCES[src]
    if lay == "none" or src in C.NO_SEARCH:
        return 0
    if src in C.WIN_MAX:                                   # hyb3-pre48 wide: the wider of the 4th-power / DA bounds
        crb = max(C.crb_nda4(snr, C.layout(lay)["K"]), C.crb_known(snr, C.layout(lay)["known_idx"]))
    elif est in ("nda4uw", "nda4pk") or src in C.NDA4_WIN:   # ViaSat, hyb3-pre48: the 4th-power bound over the burst
        crb = C.crb_nda4(snr, C.layout(lay)["K"])
    elif est in ("lag", "lag320"):                         # Wi-Fi: the fine lag-64 estimate's own variance
        crb = C.var_lag(snr)
    else:
        crb = C.crb_known(snr, C.layout(lay)["known_idx"])
    return max(1, int(np.ceil(4.0 * 1.3 * np.sqrt(crb) / SEARCH_STEP)))


def _hyp(src, snr, lobes):
    M = window(src, snr)
    D, nl = C.src_lobes(src, lobes)
    ms = range(-nl, nl + 1) if D else (0,)
    K = SCAN_K if src in C.SCAN else M                     # C.SCAN: k STEP over the whole range (M = the CRB window,
                                                           # kept for in_window and the json, measurement only)
    hyp = sorted([(m, k) for m in ms for k in range(-K, K + 1) if (m, k) != (0, 0)],
                 key=lambda t: (abs(t[0]), t[0], abs(t[1]), t[1]))
    return hyp, M, D


def hypotheses(src, snr, lobes):
    """CFO offsets from f_hat of the search (without 0), in (|m|, m, |k|, k) order (the metric decides the order of
    the decodes; this order only breaks ties): k STEP, |k| <= M, and for lobe layouts m / D_lobe + k STEP,
    0 < |m| <= lobes (est5 layouts: C.lobe_n). Returns (offsets, M, D_lobe)."""
    hyp, M, D = _hyp(src, snr, lobes)
    return np.array([(m / D if m else 0.0) + k * SEARCH_STEP for m, k in hyp]), M, D


def hyp_matrix(src, snr, lobes, fh, cand):
    """est5 per-packet search: offsets (B, H), lobe / candidate centres (B, H) and the valid mask (B, H) (centre inside
    |f| <= MAX_CFO + M STEP or the f_hat lobe itself; hyb3: no hypothesis within STEP / 2 of an earlier valid one, f_hat
    included). cand (B, n) extra CFO candidates or None."""
    hyp, M, D = _hyp(src, snr, lobes)
    off = np.array([(m / D if m else 0.0) + k * SEARCH_STEP for m, k in hyp])
    cen = np.array([m / D if m else 0.0 for m, k in hyp])
    B = len(fh)
    O, Cn = np.broadcast_to(off, (B, len(off))), np.broadcast_to(cen, (B, len(off)))
    if cand is not None:
        d = cand - fh[:, None]                                              # (B, n)
        O = np.concatenate([O] + [np.concatenate([d[:, [c]], d[:, [c]] + off[None]], 1) for c in range(d.shape[1])], 1)
        Cn = np.concatenate([Cn] + [np.concatenate([d[:, [c]], d[:, [c]] + cen[None]], 1) for c in range(d.shape[1])], 1)
    val = (np.abs(fh[:, None] + Cn) <= C.MAX_CFO + M * SEARCH_STEP + 1e-12) | (Cn == 0)
    if src in C.SCAN:                                                           # range scan: filter per hypothesis
        c = np.clip(fh, -C.MAX_CFO - SEARCH_STEP, C.MAX_CFO + SEARCH_STEP)      # grid centre c + k STEP (= fh if in
        O = (c - fh)[:, None] + off[None]                                       # range; mmml can return |fh| > MAX_CFO).
        val = np.abs(c[:, None] + off[None]) <= C.MAX_CFO + SEARCH_STEP + 1e-12  # Clip at MAX + STEP, not MAX: the
                                                                                # skipped k = 0 point c is then outside
    if cand is not None:
        Fa = np.concatenate([np.zeros((B, 1)), O], 1)
        vf = np.concatenate([np.ones((B, 1), bool), val], 1)
        if B * Fa.shape[1] ** 2 <= 1 << 24:                                    # (the original one-shot form)
            close = np.abs(Fa[:, :, None] - Fa[:, None, :]) < SEARCH_STEP / 2   # (B, H + 1, H + 1)
            close &= vf[:, None, :]                                            # only valid earlier ones count
            val &= ~np.tril(close, -1).any(2)[:, 1:]                           # an earlier hypothesis within STEP / 2
        else:                                                                  # large searches (hyb3-pre48 wide): the
            dup = np.zeros(Fa.shape, bool)                                     # same test in row blocks (memory)
            for a in range(0, B, 4):
                cl = (np.abs(Fa[a:a + 4, :, None] - Fa[a:a + 4, None, :]) < SEARCH_STEP / 2) & vf[a:a + 4, None, :]
                dup[a:a + 4] = np.tril(cl, -1).any(2)
            val &= ~dup[:, 1:]
    return np.array(O), np.array(Cn), val, M, D


def work(task):
    rate, snr, chunk, frames, min_err, sources, seed, pn, track_w, track, lobes = task[:11]
    part = task[11] if len(task) > 11 else None            # (measurement) per-packet MACs log: its dumps/<part> (None: off)
    q = 2 * np.pi * pn                                    # Wiener phase variance per symbol (kalman: true linewidth)
    from blind_fast import fast_sc, rho_min
    from blind_ber import RHO_N                            # the blind receivers' per-rate threshold (same check)
    from polar import PolarCode
    key = [seed, RATE_IDX[rate], int(round(10 * snr)) + 1000, chunk]
    rng = np.random.default_rng([40] + key)                # data, CFO, phase
    rpn = np.random.default_rng([41] + key)                # the phase-noise path (drawn only if pn > 0)
    lays = [l for l in C.LAYOUTS if any(C.SOURCES[s][0] == l for s in sources)]
    rlay = {l: np.random.default_rng([42] + key + [C.LAYOUT_ID[l]]) for l in lays}   # known symbols + noise
    rext = np.random.default_rng([43] + key)               # est5: the path continued beyond the est4 KMAX
    rvar = np.random.default_rng([44] + key)               # variants: continued again beyond the est5 KMAX_ALL
    longer = any(C.layout(l)["K"] > C.KMAX for l in lays)
    longest = any(C.layout(l)["K"] > C.KMAX_ALL for l in lays)
    A = C.CODES[rate]
    code = PolarCode(C.N_BITS, A, 16, 8)
    fsc = fast_sc(A)
    s2 = 10 ** (-snr / 10)                                 # complex noise variance at the MF output
    sl = 10 ** (snr / 10)
    thr = max(rho_min(snr), float(np.interp(snr, *zip(*RHO_N[rate]))) * np.sqrt(sl / (1 + sl)))
    st = {s: {k: (0.0 if k in ("se_first", "se_final", "time_est") else 0) for k in _FIELDS} for s in sources}
    mlog = {s: [] for s in sources} if part else None      # (measurement) per-packet MACs log rows per source
    mcf = {s: mac_coef(rate, s, track, pn) for s in sources} if part else None
    B = 100
    while st[sources[0]]["frames"] < frames and min(v["frame_err"] for v in st.values()) < min_err:
        data = rng.integers(0, 2, (B, A), dtype=np.uint8)
        cw = code.encode(data)[:, C.INTERLEAVER]
        sym = ((1 - 2.0 * cw[:, 0::2]) + 1j * (1 - 2.0 * cw[:, 1::2])) / np.sqrt(2)
        f = rng.uniform(-C.MAX_CFO, C.MAX_CFO, B)
        ph = rng.uniform(0, 2 * np.pi, B)
        phi = C.wiener(B, C.KMAX, pn, rpn) if pn > 0 else None
        phx = C.extend_path(phi, C.KMAX_ALL, pn, rext) if phi is not None and longer else None
        phv = C.extend_path(phx, C.KMAX_V, pn, rvar) if phx is not None and longest else None
        bur = {}
        for l in lays:
            bs, _, _, ks = C.make_burst(l, sym, rlay[l])
            pth = phi if phi is None or bs.shape[1] <= C.KMAX else phx if bs.shape[1] <= C.KMAX_ALL else phv
            r, rx, phs = C.transmit(bs, f, ph, snr, rlay[l], pn, None if pth is None else C.slice_path(pth, bs.shape[1]))
            bur[l] = (r, rx, phs, ks)
        fcache = {}
        ebat = {}                                          # per-packet errors of this batch (McNemar, measurement only)
        for src in sources:
            S = st[src]
            lay, est, model = C.SOURCES[src]
            L = C.layout(lay)
            didx = L["data_idx"]
            r, rx, phs, ks = bur[lay]
            if (lay, est) not in fcache:                   # sources of one layout and estimator share f_hat, premf
                t0 = time.perf_counter()
                fh_, cd_ = E.candidates(est, r, ks, L, snr, f)
                dt = time.perf_counter() - t0
                fcache[(lay, est)] = (fh_, dt, C.premf(r, rx, fh_), cd_)
            fh, dt, rp, cand = fcache[(lay, est)]
            S["time_est"] += dt
            off, M, D = hypotheses(src, snr, lobes)
            tol = M * SEARCH_STEP + 1e-12                  # measurement only from here to attempt()
            S["in_window"] += int(np.sum(np.abs(fh - f) <= tol))
            e5 = src in C.EST5 or src in C.ARS or src in C.VARS
            if e5:                                         # est5: per-packet hypotheses (range-filtered lobes, hyb3)
                O5, C5, V5, _, _ = hyp_matrix(src, snr, lobes, fh, cand)
                sc = src in C.SCAN                         # range scan: a hypothesis within STEP / 2 of f
                cc = np.concatenate([np.zeros((B, 1)), np.where(V5, O5 if sc else C5, np.inf)], 1)
                S["in_search"] += int(np.sum(np.min(np.abs(fh[:, None] + cc - f[:, None]), 1)
                                             <= (SEARCH_STEP / 2 + 1e-12 if sc else tol)))
                if D:
                    S["lobe_err"] += int(np.sum(np.abs(fh - f) > 0.5 / D))
            else:
                nl_ = C.src_lobes(src, lobes)[1]           # (= lobes for the est4 sources; split64 ML L4: 4)
                ms = np.arange(-nl_, nl_ + 1) / D if D else np.zeros(1)
                S["in_search"] += int(np.sum(np.min(np.abs(fh[:, None] + ms[None] - f[:, None]), 1) <= tol))
            if C.lobe_D(lay) and not e5:
                D_ = C.lobe_D(lay)
                fnc = E.noncoherent(r, ks, L)
                S["lobe_err"] += int(np.sum(np.abs(fh - f) > 0.5 / D_))
                S["nc_lobe_err"] += int(np.sum(np.abs(fnc - f) > 0.5 / D_))
                fpk = fh + np.round((fnc - fh) * D_) / D_
                S["nc_pick_err"] += int(np.sum(np.abs(fpk - f) > 0.5 / D_))

            def attempt(idx, fhyp):
                g = E.gain(model, rp[idx], ks[idx], L, fhyp, ph[idx], phs[idx], track_w, track, q, s2)
                llr, sh = C.llrs(rp[idx], didx, fhyp, g, s2)
                d, ok, _ = code.decode(llr, return_info=True)
                j = np.where(ok)[0]
                if len(j):                                 # re-encoding check on the de-rotated, gain-corrected symbols
                    c_ = code.encode(d[j])[:, C.INTERLEAVER]
                    sr = ((1 - 2.0 * c_[:, 0::2]) + 1j * (1 - 2.0 * c_[:, 1::2])) / np.sqrt(2)
                    rho = np.abs(np.sum(sh[j] * np.conj(sr), 1)) / np.sqrt(C.N_SYM * np.sum(np.abs(sh[j]) ** 2, 1))
                    acc = rho > thr
                    wrong = (d[j] != data[idx[j]]).any(1)
                    S["crc_pass"] += len(j)
                    S["crc_pass_wrong"] += int(wrong.sum())
                    S["re_caught"] += int((wrong & ~acc).sum())
                    S["re_lost"] += int((~wrong & ~acc).sum())
                    ok = ok.copy()
                    ok[j] = acc
                return d, ok

            dec, ok = attempt(np.arange(B), fh)
            ffin = fh.copy()
            bad = np.where(~ok)[0]
            xd, me, mr = np.zeros(B, int), np.zeros(B, int), np.zeros(B, int)   # (measurement) per packet: extra
                                                           # decodes, metric passes, metric rounds (MACs log)
            if e5 and O5.shape[1] and len(bad):            # est5 PM+all: only the valid hypotheses of each packet
                Ob, Vb = O5[bad], V5[bad]
                nv = Vb.sum(1)
                me[bad], mr[bad] = nv, np.ceil(nv / KP)
                Mt = np.full(Ob.shape, np.inf)
                for i_ in range(Ob.shape[1]):
                    rw = np.where(Vb[:, i_])[0]
                    if not len(rw):
                        continue
                    sel = bad[rw]
                    fq = fh[sel] + Ob[rw, i_]
                    g = E.gain(model, rp[sel], ks[sel], L, fq, ph[sel], phs[sel], track_w, track, q, s2)
                    llr, _ = C.llrs(rp[sel], didx, fq, g, s2)
                    Mt[rw, i_] = fsc.metric(llr)
                S["metric_evals"] += int(nv.sum())
                S["metric_rounds"] += int(np.sum(np.ceil(nv / KP)))
                order = np.argsort(Mt, 1, kind="stable")   # invalid (inf) last
                for t in range(order.shape[1]):
                    sub = np.where(~ok[bad] & (t < nv))[0]
                    if not len(sub):
                        break
                    idx = bad[sub]
                    fk = fh[idx] + Ob[sub, order[sub, t]]
                    d, okk = attempt(idx, fk)
                    S["extra_decodes"] += len(idx)
                    xd[idx] += 1
                    w = idx[okk]
                    dec[w], ok[w], ffin[w] = d[okk], True, fk[okk]
            elif not e5 and len(off) and len(bad):         # PM+all: metric-ordered neighbours after the decode at f_hat
                Mt = np.empty((len(bad), len(off)))
                for i_, o in enumerate(off):
                    fq = fh[bad] + o
                    g = E.gain(model, rp[bad], ks[bad], L, fq, ph[bad], phs[bad], track_w, track, q, s2)
                    llr, _ = C.llrs(rp[bad], didx, fq, g, s2)
                    Mt[:, i_] = fsc.metric(llr)
                S["metric_evals"] += len(bad) * len(off)
                S["metric_rounds"] += len(bad) * int(np.ceil(len(off) / KP))
                me[bad], mr[bad] = len(off), int(np.ceil(len(off) / KP))
                order = np.argsort(Mt, 1, kind="stable")
                for t in range(order.shape[1]):
                    sub = np.where(~ok[bad])[0]
                    if not len(sub):
                        break
                    idx = bad[sub]
                    fk = fh[idx] + off[order[sub, t]]
                    d, okk = attempt(idx, fk)
                    S["extra_decodes"] += len(idx)
                    xd[idx] += 1
                    w = idx[okk]
                    dec[w], ok[w], ffin[w] = d[okk], True, fk[okk]
            errs = (dec != data).any(1)
            if mlog is not None:                           # (measurement) per-packet MACs log row of this batch
                mlog[src].append(dict(pkt0=S["frames"], x_dec=xd.copy(), m_evals=me.copy(), m_rounds=mr.copy(),
                                      passed=ok.copy(), right=ok & ~errs, fe=errs.copy(), ud=errs & ok))
            S["frames"] += B
            S["frame_err"] += int(errs.sum())
            S["undetected"] += int((errs & ok).sum())
            S["se_first"] += float(np.sum((fh - f) ** 2))
            S["se_final"] += float(np.sum((ffin - f) ** 2))
            ebat[src] = errs
        for src, e_ in ebat.items():                       # n10: src wrong, ref right; n01: src right, ref wrong
            eref = ebat[mcnemar_src(src, sources)]         # (= mcnemar_ref(sources) except variants with a parent)
            st[src]["n10"] += int(np.sum(e_ & ~eref))
            st[src]["n01"] += int(np.sum(~e_ & eref))
    if mlog is not None:                                   # (measurement) one file per (part, chunk), every source:
        import re                                          # est4/dumps/<part>/macs_R<rate>_<snr>_c<chunk>.npz
        slug = lambda x: re.sub(r"[^0-9A-Za-z.+-]+", "_", str(x)).strip("_")
        dir_ = os.path.join(C.HERE, "dumps", part)
        os.makedirs(dir_, exist_ok=True)
        out, srcs = {}, [s for s in sources if mlog[s]]
        n_, p0_, ok_, ovf_ = [], [], [], []
        for i, src in enumerate(srcs):                     # source i: packets pkt0 .. pkt0 + n - 1 of the chunk (the
            rows = mlog[src]                               # batches in order); core = coef . (1, x, e, m), not stored
            cat = lambda q: np.concatenate([x[q] for x in rows])
            p0 = np.array([x["pkt0"] for x in rows])
            ok_.append(bool(np.all(p0 == p0[0] + B * np.arange(len(rows)))))   # contiguous batches
            x_, e_, m_ = cat("x_dec"), cat("m_evals"), cat("m_rounds")
            ovf_.append(int((x_ > 32767).sum() + (e_ > 32767).sum() + (m_ > 255).sum()))   # clipped (flagged)
            out.update({f"x_dec_{i}": np.minimum(x_, 32767).astype(np.int16),
                        f"m_evals_{i}": np.minimum(e_, 32767).astype(np.int16),
                        f"m_rounds_{i}": np.minimum(m_, 255).astype(np.uint8),
                        **{f"{q}_{i}": np.packbits(cat(q)) for q in ("passed", "right", "fe", "ud")}})
            n_.append(len(x_))
            p0_.append(int(p0[0]))
        np.savez_compressed(os.path.join(dir_, f"macs_R{slug(rate)}_{snr:+.1f}_c{chunk}.npz"), **out,
                            src=np.array(srcs), n=np.array(n_, np.int64), pkt0=np.array(p0_, np.int64),
                            contig=np.array(ok_), ovf=np.array(ovf_, np.int64),
                            coef=np.array([mcf[s] for s in srcs], np.float64).reshape(-1, 4), par_dec=E.PAR_DEC,
                            rate=rate, snr=snr, chunk=chunk, seed=seed, rng_key=np.array(key), pn=pn, track=track)
    return rate, snr, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", required=True, choices=list(C.CODES))
    ap.add_argument("--snrs", type=float, nargs="+", required=True, help="per-symbol Es/N0 (dB)")
    ap.add_argument("--sources", nargs="+", default=list(C.SOURCES))
    ap.add_argument("--frames", "--max-frames", dest="frames", type=int, default=60_000, help="packets per SNR")
    ap.add_argument("--min-err", "--min-errors", dest="min_err", type=int, default=150)
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--part", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--pn", type=float, default=0.0, help="Wiener phase noise, linewidth x symbol time")
    ap.add_argument("--track", choices=("kalman", "sw"), default=E.TRACK_MODE,
                    help="interp2 / track phase model: RTS smoother (q = 2 pi pn) or the sliding window (--track-w)")
    ap.add_argument("--track-w", type=int, default=E.TRACK_W, help="--track sw: sliding window in fields (odd)")
    ap.add_argument("--lobes", type=int, default=LOBES, help="2-field layouts: lobe hypotheses m = -L .. L (0: none)")
    a = ap.parse_args()
    assert all(s in C.SOURCES for s in a.sources), a.sources
    assert a.track_w % 2 == 1, a.track_w
    tasks = [(a.rate, s, c, a.frames // a.chunks, -(-a.min_err // a.chunks), a.sources, a.seed, a.pn, a.track_w,
              a.track, a.lobes, None if os.environ.get("EST4_NO_MACLOG", "0") == "1" else a.part)
             for s in a.snrs for c in range(a.chunks)]   # (+ the per-packet MACs log's part, EST4_NO_MACLOG=1: off)
    acc = {}
    t0 = time.time()
    prog = C.path("logs", f"bler_{a.part}.progress")
    with mp.Pool(a.workers) as pool:
        for i, (rt, snr, st) in enumerate(pool.imap_unordered(work, tasks)):
            for src, v in st.items():
                w = acc.setdefault((snr, src), {k: 0 for k in v})
                for k, x in v.items():
                    w[k] += x
            with open(prog, "w") as fp:
                fp.write(f"{i + 1} {len(tasks)} {time.time() - t0:.0f}\n")    # job_progress.py: done total seconds
            print(f"{i + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
    res = []
    for (snr, src), v in sorted(acc.items()):
        lay = C.SOURCES[src][0]
        L = C.layout(lay)
        res.append(dict(rate=a.rate, snr=snr, src=src, layout=lay, pn=a.pn, nk=L["nk"], energy_db=L["energy_db"],
                        snr_plot=snr + L["energy_db"], window=window(src, snr), track=a.track, track_w=a.track_w,
                        lobes=(C.src_lobes(src, a.lobes)[1] if src in C.SRC_LOBES else
                               C.lobe_n(lay, a.lobes) if C.lobe_D(lay) else 0), n_hyp=len(hypotheses(src, snr, a.lobes)[0]),
                        seed=a.seed, mcnemar_ref=mcnemar_src(src, a.sources), bler=v["frame_err"] / v["frames"], undetected_bler=v["undetected"] / v["frames"],
                        frac_in_window=v["in_window"] / v["frames"], frac_in_search=v["in_search"] / v["frames"],
                        rmse_first=float(np.sqrt(v["se_first"] / v["frames"])),
                        rmse_final=float(np.sqrt(v["se_final"] / v["frames"])),
                        extra_decodes_per_frame=v["extra_decodes"] / v["frames"],
                        us_est_per_frame=1e6 * v["time_est"] / v["frames"], **v))
    json.dump(dict(results=res), open(C.path("results", f"bler_{a.part}.json"), "w"))
    for r_ in res:
        print(f"{r_['snr']:5.1f} ({r_['snr_plot']:5.2f}) {r_['src']:18s} BLER {r_['bler']:.2e} "
              f"({r_['frame_err']}/{r_['frames']}) und {r_['undetected']} extra {r_['extra_decodes_per_frame']:.2f} "
              f"M {r_['window']} hyp {r_['n_hyp']} in-win {r_['frac_in_window']:.4f} in-search "
              f"{r_['frac_in_search']:.4f} lobe-err {r_['lobe_err']} (nc {r_['nc_lobe_err']}, nc-pick {r_['nc_pick_err']}) "
              f"rmse {r_['rmse_first']:.2e} -> {r_['rmse_final']:.2e}")
    print("saved", C.path("results", f"bler_{a.part}.json"), f"{time.time() - t0:.0f}s")
    print("EVAL DONE")


if __name__ == "__main__":
    main()
