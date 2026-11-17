"""
Monte-Carlo BLER and MACs of the BLIND receiver (small_rx, the adopted testing receiver per rate profile) on the
full-system native formats: the rate-matched polar code of run_polar_genie (fullsys/polar_rm.py, CRC-32, CA-SCL-8) on
the competitors' (A, E), unknown CFO and carrier phase, no pilots / UW, timing known (scope: no burst sync).

    tx  data (B, A) drawn first (as run_polar_genie / run_rcs2) -> RMPolarCode.encode_rm -> [:, F.chan] (QPSK: OUR
        channel interleaver rng(12345).permutation(E), blind_fmt; --no-chan-intlv = the old map with the pi/2 tie
        floor; = run_polar_genie --chan-intlv) -> run_polar_genie.modulate
        (QPSK Gray / pi/2-BPSK / BPSK) -> txrx_chain._transmit (upsample, RRC --beta, CFO f, phase, AWGN Es/N0, MF,
        downsample; the pre-MF samples captured for the receiver's pre-MF correction)
        f ~ U[-cfo_max, cfo_max], phase ~ U[0, 2 pi) per packet from a SEPARATE stream SeedSequence(entropy + [1]), so
        the data AND the noise equal run_polar_genie's chunk at the same --seed / --batch / point (fully paired packets)
    rx  fullsys/blind_fmt.BlindFormat context (N, n_sym, E, MAC model, virtual QPSK for (pi/2-)BPSK, rate recovery),
        small_rx.small_receive with the adopted receiver of the format's rate profile (BLIND_IMPLEMENTATION/README.md):
        id13 / id3 / id42b / id42q -> base25_qfix_fzs (2/5), id14s / id14p -> base2_qfix_fzs (1/2), vde32 ->
        testing_s11g (0.15 = the 1/10 settings), + the format hooks: nopi (shortened id14s: 4 pi/2 branches),
        bpsk_sq (--bpsk-phase sq: (pi/2-)BPSK line / phases from r^2), ck_useful (--ck useful)
    acceptance  CRC-32 (PiCode's pi complement except under shortening) + the re-encoding check over the E sent bits
        (re-encode, rate-match, re-modulate) with a PROVISIONAL threshold table (--rho scaled: blind_fmt.rho_table)

Provisional, not calibrated for these formats (defaults conservative: stops off, checkpoints on the informative bits):
    --fzstop off (F5 off; 'adopted' = run.FZS_T at the profile key; 'q,t' explicit), --spec off (spec11 off at vde32;
    'adopted' keeps it), --rho scaled (RHO_N[rho_key] kept in right-pass std units for n_sym; 'table' as is, 'min' =
    rho_min only), --cknn keep (the checkpoint NN of 2/5, 1/2 trained on 1024-symbol packets; 'off' = z-test only;
    'fmt' = the format's own, trained by fullsys/ck_nn_fs.py: models ck_nn_fs_<fmt>_c<c>.npz, --cknn-name another prefix;
    at the profile's checkpoint, or CK_C at 0.15 (vde32: c 3 = 1/4; its base10 receiver then runs without the coarse
    start, the NN needs every cell up to its checkpoint), --ck-c another; the models are checked before the pool).
    Logged for the recalibration: rho_n of every CRC pass (right / wrong), psn_min at the FZ_Q checkpoints of every
    CA-SCL decode (right / CRC-wrong / failed; masked by blind_fmt fz_mask as the stop would see it), the spec / fz
    counters of small_rx. --calib: seeds disjoint from every reported run (tag + CALIB_TAG): calibrate on those only.

--design pw|ga, --design-snr (default DESIGN_SNR[fmt]): the info set as run_polar_genie (tx and rx share one code).
--cap-core M (default None = no cap): small_rx cap_core, a packet whose crit_par passes M MACs per core is stopped
there and counted as a failure (out 2); logged per point (cap_hit, cap_hit_right = right before the cap) and per
chunk (chunks[].cap_idx); max_<cost> = the largest per-packet cost. fullsys/cmp_cap.py pairs a cap run with a no-cap one.
--sps '<json>' (default None = unchanged): small_rx spec keys set last in rx_spec (lists -> tuples; a per-rate dict
merges into the profile's per-rate dict, anything else replaces), recorded in meta sps_override / sps. Live tuning of
settings that change which decodes happen (the z-test: tau, kmin, win, ck_keep, ck_min, phase_keep, final, ...) on
--calib packets, one part per setting at the same --seed / --batch / --frames (paired; fullsys/zt_compare.py).
--charge-all (default off = the old count): small_rx ck_charge_all, the checkpoint NN's partial decodes of the cells
outside the current round (2/5 first_k 32, 0.15 batches of 32) charged when the NN runs (macs + crit_par); decisions and
BLER identical, only the MACs change (meta charge_all; st ck_extra_cells / macs_ck_extra). fullsys/recharge.py bounds
the correction of the runs without it.

Cost: blind_vp.MAC scaled to N / n_sym / E (blind_fmt); MACs per core = crit_par (32 cores, scheduled): the standard
model is crit_par_h_d4a at the 0.15 profile, crit_par_d4a at 2/5, 1/2 (BLIND_IMPLEMENTATION/07_complexity.md); both
are recorded per packet (histograms split right / wrong / failed) and per stage (stage_acc).

    BLIND_STUDY=small_cfo python fullsys/run_blind_fs.py --fmt id13 --snrs -0.6 -0.2 --frames 20000 --part fs-bl13
    BLIND_STUDY=small_cfo python fullsys/run_blind_fs.py --selfcheck       # 3 packets at 30 dB per format (no BLER)

Writes fullsys/results/blind_fs_<part>.json (rewritten after every point; refuses an existing part), .prog ("done total
elapsed_s"), and with --dump compact per-packet records + small_rx's decode / fz rows per chunk in
fullsys/results/blind_fs_<part>_dump/. Run on the cluster only.
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import run_polar_genie as pg          # noqa: E402  (FMTS, modulate, the seed scheme)
import txrx_chain                                   # noqa: E402

RESULTS = os.path.join(ROOT, "fullsys", "results")
CALIB_TAG = 500000                                  # --calib: seed tag offset (disjoint from every reported run)
# per format: rate profile (receiver settings / RHO_N key) and the adopted receiver (testing/run.py VARIANTS key)
BL = {"id13": ("2/5", "base25_qfix_fzs"), "id14s": ("1/2", "base2_qfix_fzs"), "id14p": ("1/2", "base2_qfix_fzs"),
      "id3": ("2/5", "base25_qfix_fzs"), "id42b": ("2/5", "base25_qfix_fzs"), "id42q": ("2/5", "base25_qfix_fzs"),
      "vde32": ("0.15", "testing_s11g")}
STD_CORE = {"0.15": "c_hd4a", "2/5": "c_d4a", "1/2": "c_d4a"}   # the standard MACs per core of the profile
# --cknn fmt on a profile whose receiver has no checkpoint NN: its checkpoint CK_FR[c] (0.15: c 3 = 1/4, as 2/5;
# --ck-c overrides it on every profile); the 2/5, 1/2 profiles keep their own (c 3 = 1/4, c 2 = 3/16)
CK_C = {"0.15": 3}
RHO_BINS = pg.RHO_BINS                              # rho_n = rho / sqrt(s / (1 + s)), 0 .. 1.5 step 0.01
RTH_BINS = np.linspace(0.0, 3.0, 151)               # rho / threshold
PSN_BINS = np.linspace(0.0, 1.5, 301)               # psn_min at the FZ_Q checkpoints
CORE_B = (4.0, 20, 100)                             # MACs per core histogram: log10 from 1e4, 0.05-decade bins
LERR_B = np.linspace(-8.0, -1.0, 71)                # log10 |CFO error|
SERR_B = np.linspace(-5.0, 5.0, 201)                # CFO error / STEP of the right decodes
_F, _RX = {}, {}


def _init():
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[v] = "1"


def get_fmt(fmt, o):
    """BlindFormat of a format (cached per process)."""
    dsnr = (pg.DESIGN_SNR[fmt] if o["design_snr"] is None else o["design_snr"]) if o["design"] == "ga" else None
    key = (fmt, o["crc"], o["beta"], o["cfo_max"], o["extra_in_fz"], o["chan"], o["design"], dsnr)
    if key not in _F:
        from fullsys.blind_fmt import BlindFormat
        f = pg.FMTS[fmt]
        F = BlindFormat(fmt, f["A"], f["E"], f["mod"], mode=f["mode"] if f["force"] else None, crc=o["crc"],
                        L=pg.L_LIST, beta=o["beta"], cfo_max=o["cfo_max"], extra_in_fz=o["extra_in_fz"],
                        chan_intlv=o["chan"], design=o["design"], design_snr=dsnr)
        assert F.mode == f["mode"], (fmt, F.mode, f["mode"])
        _F[key] = F
    return _F[key]


def _testing_run():
    """BLIND_IMPLEMENTATION/testing/run.py as a module (its BASE / VARIANTS / FZS_T)."""
    if "m" not in _RX:
        p = os.path.join(ROOT, "BLIND_IMPLEMENTATION", "testing", "run.py")
        sp = importlib.util.spec_from_file_location("bl_testing_run", p)
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        _RX["m"] = m
    return _RX["m"]


def ck_index(sps, prof):
    """The checkpoint index c (CK_FR[c]) of an sps's checkpoint NN at the profile, as small_rx resolves it (None: off)."""
    import blind_cfo as bc
    c = sps.get("ck_nn")
    return c.get(bc.PROFILE.get(prof, prof)) if isinstance(c, dict) else c


def rx_spec(fmt, F, o, rx_key=None):
    """small_rx spec of the format: the adopted receiver's sps flags + the format hooks + the provisional settings."""
    import blind_ber as bb
    tr = _testing_run()
    prof, key0 = BL[fmt]
    base, flags = tr.VARIANTS[rx_key or key0]
    sps = {**bb.RX[tr.BASE[base]]["sps"], **flags}
    assert sps.get("pns") is None and not sps.get("pilots"), "pns / pilots: not supported on the formats"
    sps["rate"] = prof
    rk = pg.FMTS[fmt]["rho_key"]
    sps["rho_n"] = (F.rho_table(rk) if o["rho"] == "scaled" else tuple(bb.RHO_N[rk]) if o["rho"] == "table" else None)
    if o["fzstop"] == "off":
        sps["fzstop"] = None
    elif o["fzstop"] != "adopted":
        sps["fzstop"] = tuple(float(x) for x in o["fzstop"].split(","))
    if o["spec"] == "off":
        sps["win_spec"] = None
    if o["cknn"] == "off":
        sps["ck_nn"] = None
    elif o["cknn"] == "fmt":                                          # the format's own checkpoint NN (ck_nn_fs.py):
        sps["ck_nn_name"] = o.get("cknn_name") or f"ck_nn_fs_{fmt}"   # same checkpoint, models <name>_c<c>.npz
        import blind_cfo as bc
        pk = bc.PROFILE.get(prof, prof)                               # small_rx resolves PER_RATE on this key (0.15: 1/10)
        if o.get("ck_c") is not None or ck_index(sps, prof) is None:  # (2/5, 1/2 without --ck-c: their ck_nn untouched)
            c = o.get("ck_c") if o.get("ck_c") is not None else CK_C.get(prof)
            if c is None:
                raise ValueError(f"--cknn fmt: no checkpoint NN mapping for profile {prof} (give --ck-c)")
            sps["ck_nn"] = {pk: int(c)}
        cs_ = sps.get("coarse")                                       # the NN needs every cell decoded up to its
        if (cs_.get(pk) if isinstance(cs_, dict) else cs_):           # checkpoint: no coarse start (0.15: base10 has
            sps["coarse"] = False                                     # it; 2/5, 1/2: never on, unchanged)
    sps["nopi"] = F.nopi
    sps["bpsk_sq"] = F.mod != "qpsk" and o["bpsk_phase"] == "sq"
    sps["ck_useful"] = o["ck"] == "useful"
    if o["cap_core"] is not None:                                     # hard MACs-per-core cap (small_rx cap_core: on
        sps["cap_core"] = float(o["cap_core"])                        # crit_par, absolute MACs, the format's MAC model)
    if o.get("charge_all"):                                           # (accounting) small_rx ck_charge_all: every cell the
        sps["ck_charge_all"] = True                                   # checkpoint NN sees is charged (decisions identical)
    for k_, v_ in (o.get("sps") or {}).items():                       # --sps (None = none): applied last, as given; a
        sps[k_] = ({**sps[k_], **v_} if isinstance(v_, dict) and isinstance(sps.get(k_), dict)   # per-rate dict onto
                   else v_)                                           # a per-rate dict merges, anything else replaces
    return sps, prof


def sps_json(s):
    """--sps JSON -> dict of small_rx spec keys; lists -> tuples (small_rx tests tuples, e.g. nph (phases, snr_hi))."""
    def tup(v):
        return (tuple(tup(x) for x in v) if isinstance(v, list) else
                {k: tup(x) for k, x in v.items()} if isinstance(v, dict) else v)
    d = json.loads(s)
    if not isinstance(d, dict):
        raise ValueError("--sps: a JSON object {key: value}")
    return tup(d)


def transmit_rx(sym, f, ph, esn0, rng, beta):
    """txrx_chain._transmit (the chain itself) returning also the noisy pre-MF samples (its 2nd convolution input)."""
    import scipy.fft
    from scipy.signal import fftconvolve
    cap = []

    def fc(x, h, axes):
        cap.append(x)
        return fftconvolve(x, h, axes=axes)

    with scipy.fft.set_workers(1):
        r = txrx_chain._transmit(sym, f, ph, esn0, rng, beta, fc)
    return r, cap[1]


def tx_packets(fmt, F, esn0, entropy, batch, o):
    """The tx of a chunk (run_chunk; fullsys/ck_nn_fs.py training data): data (B, A) int8, CFO f, centre phase th,
    virtual QPSK symbols v (B, n_sym) and the pre-MF samples rx."""
    A = pg.FMTS[fmt]["A"]
    rng = np.random.default_rng(np.random.SeedSequence(entropy))
    d = rng.integers(0, 2, (batch, A)).astype(np.int8)                # drawn first, as run_polar_genie / run_rcs2
    rg2 = np.random.default_rng(np.random.SeedSequence(list(entropy) + [1]))   # CFO / phase: a separate stream
    f = rg2.uniform(-o["cfo_max"], o["cfo_max"], batch)
    ph = rg2.uniform(0, 2 * np.pi, batch)
    s = pg.modulate(F.rmc.encode_rm(d.astype(np.uint8))[:, F.chan], fmt)   # chan: the channel interleaver (QPSK)
    r, rx = transmit_rx(s, f, ph, esn0, rng, o["beta"])               # noise = run_polar_genie's at f = 0
    th = ph + 2 * np.pi * f * (F.centre + txrx_chain.DELAY_SYM)       # centre phase (= the virtual symbols' phase)
    return d, f, th, F.virtual(r), rx


def _hist(v, edges):
    return np.histogram(np.clip(v, edges[0], np.nextafter(edges[-1], -np.inf)), edges)[0].tolist()


def _lhist(v, b=CORE_B):
    i = np.clip(np.floor((np.log10(np.maximum(v, 1.0)) - b[0]) * b[1]), 0, b[2] - 1).astype(int)
    return np.bincount(i, minlength=b[2]).tolist()


def _cnt(v, top=400):
    return np.bincount(np.clip(np.asarray(v, int), 0, top), minlength=top + 1).tolist()


def _cat(rows, k):
    return np.concatenate([x[k] for x in rows]) if rows else np.zeros(0)


def run_chunk(task):
    """One chunk (= run_polar_genie's chunk c: the same data and noise): blind receiver, counters, histograms."""
    fmt, esn0, entropy, batch, o, cidx = task
    import blind_cfo as bc
    import small_rx
    F = get_fmt(fmt, o)
    sps, prof = rx_spec(fmt, F, o, o.get("rx"))
    A = pg.FMTS[fmt]["A"]
    d, f, th, v, rx = tx_packets(fmt, F, esn0, entropy, batch, o)
    sigma2 = 1.0 / (2.0 * 10 ** (esn0 / 10))
    truth = d.astype(np.uint8)
    st = dict(decodes=0, metric_evals=0)
    dacc, macc, sacc = {}, [], []
    out = np.zeros((batch, A), np.uint8)
    ok = np.zeros(batch, bool)
    ffin, f0 = np.full(batch, np.nan), np.full(batch, np.nan)
    t0 = time.time()
    with F:
        for a in range(0, batch, o["sub"]):
            sl = slice(a, min(a + o["sub"], batch))
            spec = {"sps": {**sps, "truth": truth[sl], "truth_f": f[sl], "truth_th": th[sl], "dec_dump": "(acc)",
                            "fz_diag": "(acc)", "dec_acc": dacc, "dec_id": (cidx, a), "mac_acc": macc,
                            "stage_acc": sacc, **({"fulllog": o["fulllog"]} if o.get("fulllog") is not None else {})}}
            out[sl], ok[sl], ffin[sl], f0[sl] = small_rx.small_receive(v[sl], rx[sl], esn0, F.code, sigma2, st, spec)
        step = bc.STEP
    t_rx = time.time() - t0
    err = (out != truth)
    fe, nbe = err.any(1), err.sum(1)
    right, wrong = ok & ~fe, ok & fe
    M = {k: _cat(macc, k) for k in ("c_hd4a", "c_d4a", "cpar", "macs")}
    S = {k: _cat(sacc, k) for k in ("reach", "cost", "stage", "n_hyp")}
    res = dict(frames=batch, frame_err=int(fe.sum()), undetected=int(wrong.sum()), bit_err=int(nbe.sum()),
               passed=int(ok.sum()), right=int(right.sum()), time_rx_s=t_rx, mac_frames=batch, out_frames=batch,
               **{f"sum_{k}": float(v_.sum()) for k, v_ in M.items()},
               **{f"sum_{k}_right": float(v_[right].sum()) for k, v_ in M.items()},
               **{f"max_{k}": float(v_.max()) if len(v_) else 0.0 for k, v_ in M.items()})
    capped = (out == 2).any(1)                                        # (measurement) stopped at the cap (small_rx: out 2)
    res["cap_frames"], res["cap_idx"] = int(capped.sum()), np.flatnonzero(capped).tolist()
    std = STD_CORE[prof]
    res["core_hist"] = {nm: {k: _lhist(M[k][m]) for k in ("c_hd4a", "c_d4a")}
                        for nm, m in (("right", right), ("wrong", wrong), ("failed", ~ok))}
    res["core_std"] = std
    # per stage (1 fast, 2 grid, 3 final, 4 final_post, 5 fine_last): reached / right / wrong / failed, MACs total and
    # per core (d4a, h_d4a) spent IN the stage by the packets reaching it
    stg, reach, cost = S["stage"], S["reach"], S["cost"]
    tab = []
    prev = np.zeros((batch, 3))
    for s_ in range(5):
        rc_ = reach[:, s_]
        here = stg == s_ + 1
        c_ = np.where(np.isfinite(cost[:, s_]), cost[:, s_], prev)
        inc = np.where(rc_[:, None], c_ - prev, 0.0)
        prev = np.where(rc_[:, None], c_, prev)
        tab.append(dict(stage=s_ + 1, reached=int(rc_.sum()), right=int((here & right).sum()),
                        wrong=int((here & wrong).sum()), failed=int((rc_ & ~here).sum()),
                        macs=float(inc[:, 0].sum()), c_d4a=float(inc[:, 1].sum()), c_hd4a=float(inc[:, 2].sum())))
    tail = cost[:, 5] - prev                                          # after the last stage (cap_core scaling, checks)
    tab.append(dict(stage="tail", macs=float(tail[:, 0].sum()), c_d4a=float(tail[:, 1].sum()),
                    c_hd4a=float(tail[:, 2].sum())))
    res["stages"] = tab
    # hypotheses / decodes per packet
    nd_ = np.zeros(batch, int)                                        # CA-SCL calls (main, retry, joint) per packet
    for g in ("f", "j"):
        for x in dacc.get(g, []):
            np.add.at(nd_, x["pk"], 1)
    natt = np.zeros(batch, int)                                       # decode attempts (dec dump rows) per packet
    for x in dacc.get("d", []):
        np.add.at(natt, x["pk"], 1)
    res["n_dec_hist"] = _cnt(nd_)
    res["n_att_hist"] = _cnt(natt)
    res["n_hyp_hist"] = _lhist(S["n_hyp"], (0.0, 10, 60))             # log10 hypotheses, 0.1-decade bins
    res["sum_n_dec"], res["sum_n_hyp"] = int(nd_.sum()), int(S["n_hyp"].sum())
    # CFO estimate errors
    ef, e0 = ffin - f, f0 - f
    res["cfo_fin_lhist"] = {nm: _hist(np.log10(np.abs(ef[m & np.isfinite(ef)]) + 1e-12), LERR_B)
                            for nm, m in (("right", right), ("wrong", wrong))}
    res["cfo_fin_shist_right"] = _hist(ef[right & np.isfinite(ef)] / step, SERR_B)
    res["cfo_fast_lhist"] = _hist(np.log10(np.abs(e0[np.isfinite(e0)]) + 1e-12), LERR_B)
    # rho_n of every CRC pass (main decodes and CA retries of the decode dump), right / wrong
    sq = np.sqrt(10 ** (esn0 / 10) / (1 + 10 ** (esn0 / 10)))
    D = {k: _cat(dacc.get("d", []), k) for k in ("crc", "rho_crc", "right", "rho_min", "acc", "tag")}
    res["rho_hist"], res["rth_hist"] = {}, {}
    if len(D["crc"]):
        c_ = D["crc"].astype(bool) & np.isfinite(D["rho_crc"].astype(float))
        rr = D["rho_crc"].astype(float)
        for nm, m in (("right", c_ & D["right"].astype(bool)), ("wrong", c_ & ~D["right"].astype(bool))):
            res["rho_hist"][nm] = _hist(rr[m] / sq, RHO_BINS)
            res["rth_hist"][nm] = _hist(rr[m] / D["rho_min"].astype(float)[m], RTH_BINS)
            res[f"rho_n_min_{nm}"] = float((rr[m] / sq).min()) if m.any() else None
            res[f"rho_n_max_{nm}"] = float((rr[m] / sq).max()) if m.any() else None
    # psn_min at the FZ_Q checkpoints of every CA-SCL decode: 0 right, 1 CRC pass wrong, 2 failed
    res["psn_hist"] = {}
    for g in ("f", "j"):
        P = _cat(dacc.get(g, []), "psn_min")
        if not len(P):
            continue
        O = _cat(dacc.get(g, []), "out")
        res["psn_hist"][g] = {str(c): {str(k): _hist(P[(O == k) & np.isfinite(P[:, c]), c], PSN_BINS) for k in (0, 1, 2)}
                              for c in range(P.shape[1])}
    res["fe_idx"], res["ud_idx"] = np.flatnonzero(fe).tolist(), np.flatnonzero(wrong).tolist()
    res["st"] = {k: (int(v_) if isinstance(v_, (int, np.integer)) else float(v_)) for k, v_ in st.items()
                 if isinstance(v_, (int, float, np.integer, np.floating)) and not isinstance(v_, (bool, np.bool_))}
    if o["dump"]:
        import small_rx as sr
        dd = o["dump"]
        os.makedirs(dd, exist_ok=True)
        tag = f"{fmt}_{esn0:+.2f}_c{cidx:05d}"
        np.savez_compressed(os.path.join(dd, f"pk_{tag}.npz"), pk=np.arange(batch, dtype=np.int32), right=right,
                            passed=ok, fe=fe, stage=stg, f=f.astype(np.float32), f0=f0.astype(np.float32),
                            f_fin=ffin.astype(np.float32), th=th.astype(np.float32), n_hyp=S["n_hyp"],
                            n_dec=nd_.astype(np.int16), n_att=natt.astype(np.int16), reach=reach, cost=cost,
                            **{k: v_.astype(np.float32) for k, v_ in M.items()}, esn0=esn0, entropy=np.array(entropy),
                            step=step)
        sr.dec_save(dacc, os.path.join(dd, f"rows_{tag}.npz"), fmt=fmt, snr=esn0, chunk=cidx)
        if o.get("fulllog") is not None:                              # (--fulllog) the joint tuner's full-search log
            sr.fl_save(dacc, os.path.join(dd, f"fl_{tag}.npz"), fmt=fmt, snr=esn0, chunk=cidx)
    return res


def _add(acc, res):
    for k, v in res.items():
        if k in ("fe_idx", "ud_idx", "core_std", "cap_idx"):
            continue
        if k not in acc:
            acc[k] = json.loads(json.dumps(v))
        elif isinstance(v, dict):
            _add(acc[k], v)
        elif isinstance(v, list):
            if k == "stages":
                for a_, b_ in zip(acc[k], v):
                    for q in b_:
                        if q != "stage":
                            a_[q] = a_.get(q, 0) + b_[q]
            else:
                acc[k] = [a + b for a, b in zip(acc[k], v)]
        elif k.startswith("rho_n_min"):
            acc[k] = v if acc[k] is None else (acc[k] if v is None else min(acc[k], v))
        elif k.startswith("max_"):
            acc[k] = max(acc[k], v)
        elif k.startswith("rho_n_max"):
            acc[k] = v if acc[k] is None else (acc[k] if v is None else max(acc[k], v))
        elif v is not None:
            acc[k] = (acc[k] or 0) + v


def run_point(fmt, esn0, args, o, prog):
    nch = -(-args.frames // args.batch)
    tag = pg.FMTS[fmt]["tag"] + (CALIB_TAG if args.calib else 0)
    tasks = ((fmt, esn0, [args.seed, tag, int(round(esn0 * 1000)) + 100000, c],
              min(args.batch, args.frames - c * args.batch), o, c) for c in range(nch))
    acc, chunks = {}, []
    t0 = tlast = time.time()
    with Pool(args.workers, initializer=_init) as pool:
        for c, res in enumerate(pool.imap(run_chunk, tasks)):
            chunks.append(dict(c=c, frames=res["frames"], fe_idx=res["fe_idx"], ud_idx=res["ud_idx"],
                               cap_idx=res["cap_idx"]))
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
    acc["chunks"] = chunks
    return acc


def selfcheck(o):
    """3 packets at 30 dB per format through the whole receiver: all right; the virtual map == the re-encoding map."""
    t_all = time.time()
    for fmt in pg.FMTS:
        t0 = time.time()
        F = get_fmt(fmt, o)
        e = np.random.default_rng(0).integers(0, 2, (2, F.E))
        assert np.allclose(F.virtual(pg.modulate(e, fmt)), F.modulate_virtual(e)), fmt
        res = run_chunk((fmt, 30.0, [0, pg.FMTS[fmt]["tag"], 0], 3, o, 0))
        assert res["frame_err"] == 0 and res["right"] == 3, (fmt, {k: res[k] for k in ("frame_err", "right")})
        print(f"  ok  {fmt:6s}: N {F.N} {F.mode:8s} n_sym {F.n_sym} {F.mod} nopi {F.nopi} | MACs/frame "
              f"{res['sum_macs'] / 3:.4g}, per core (d4a) {res['sum_c_d4a'] / 3:.4g} | {time.time() - t0:.1f} s",
              flush=True)
    print(f"SELFCHECK OK ({time.time() - t_all:.1f} s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fmt", choices=list(pg.FMTS))
    ap.add_argument("--snrs", nargs="+", type=float, help="Es/N0 per transmitted symbol (dB)")
    ap.add_argument("--crc", type=int, default=32, choices=[32, 16])
    ap.add_argument("--frames", type=int, default=20000, help="max frames per point")
    ap.add_argument("--max-err", type=int, default=200)
    ap.add_argument("--stop-per", type=float, default=0.0, help="end the sweep after a point with PER below this")
    ap.add_argument("--batch", type=int, default=200, help="frames per chunk (= run_polar_genie's, for pairing)")
    ap.add_argument("--sub", type=int, default=50, help="packets per small_receive call inside a chunk")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--calib", action="store_true", help="calibration packets: seed tag + CALIB_TAG (disjoint from "
                    "every reported run); thresholds are tuned on these only")
    ap.add_argument("--beta", type=float, default=pg.ROLLOFF, help="RRC roll-off")
    ap.add_argument("--cfo-max", type=float, default=0.03, help="|f| <= cfo_max (the search grid scales with it)")
    ap.add_argument("--rx", default=None, help="testing/run.py VARIANTS key (default: the adopted one per profile)")
    ap.add_argument("--rho", default="scaled", choices=["scaled", "table", "min"])
    ap.add_argument("--fzstop", default="off", help="off | adopted | q,t")
    ap.add_argument("--spec", default="off", choices=["off", "adopted"])
    ap.add_argument("--cknn", default="keep", choices=["keep", "off", "fmt"], help="keep: the 2/5, 1/2 checkpoint NN "
                    "of the 1024-symbol packets; off: z-test only; fmt: the format's own (fullsys/ck_nn_fs.py)")
    ap.add_argument("--cknn-name", default=None, help="--cknn fmt: model prefix (default ck_nn_fs_<fmt>)")
    ap.add_argument("--ck-c", type=int, default=None, choices=list(range(1, 7)), help="--cknn fmt: the NN's checkpoint "
                    "CK_FR[c] (default: the profile's, 2/5 c 3, 1/2 c 2; CK_C for 0.15: c 3 = 1/4; no coarse start "
                    "with the NN)")
    ap.add_argument("--ck", default="useful", choices=["useful", "codeword"])
    ap.add_argument("--bpsk-phase", default="sq", choices=["sq", "4th"])
    ap.add_argument("--extra-in-fz", action="store_true", help="the puncturing low block counts in fz_stop / psn")
    ap.add_argument("--dump", action="store_true", help="per-packet records + decode / fz rows per chunk (npz)")
    ap.add_argument("--no-chan-intlv", action="store_true", help="QPSK without the channel interleaver (the old map: "
                    "pi/2 rotation = a code automorphism, the two pi/2 branches tie; only to reproduce old runs)")
    ap.add_argument("--design", default="pw", choices=["pw", "ga"], help="info set (as run_polar_genie): pw (default) "
                    "or ga (Gaussian approximation over the rate-matched channel); tx and rx use the same code")
    ap.add_argument("--design-snr", type=float, default=None, help="GA design Es/N0 (dB); default "
                    "run_polar_genie.DESIGN_SNR[fmt]")
    ap.add_argument("--cap-core", type=float, default=None, help="hard cap on a packet's MACs per core (small_rx "
                    "cap_core on crit_par; a capped packet = no packet, a failure; default None = no cap)")
    ap.add_argument("--charge-all", action="store_true", help="small_rx ck_charge_all: the checkpoint NN's partial "
                    "decodes of the cells outside the round (first_k, batch) are charged (MACs only; decisions, BLER "
                    "identical to the run without it at the same --seed / --batch / points)")
    ap.add_argument("--sps", default=None, help="JSON object of small_rx spec keys set after the profile / format / "
                    "provisional settings (e.g. '{\"win\": 4.5, \"tau\": {\"2/5\": 0.0}}'; a per-rate dict merges into "
                    "a per-rate one); live z-test tuning on --calib packets; default None = unchanged")
    ap.add_argument("--fulllog", nargs="?", const="{}", default=None, help="small_rx fulllog (implies --dump): the "
                    "full-search log fl_<fmt>_<snr>_c<chunk>.npz per chunk for fullsys/joint_tune_fs.py; optional JSON "
                    "of small_rx.FL_DEF keys (near, fine, fr, retry_all, all_attempts); decisions / MACs unchanged")
    ap.add_argument("--part")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()
    import blind_cfo as bc
    assert bc.STUDY == "small_cfo", "run with BLIND_STUDY=small_cfo (the small-CFO receiver's models and settings)"
    assert 0 < args.cfo_max <= 0.1, "--cfo-max: the 4th-power line must stay inside +-1/2 (and the tuning is for 0.03)"
    if args.design == "pw" and args.design_snr is not None:
        ap.error("--design-snr needs --design ga")
    if args.design == "ga" and args.design_snr is None and args.fmt:
        args.design_snr = pg.DESIGN_SNR[args.fmt]
    assert args.cap_core is None or args.cap_core > 0, "--cap-core: MACs per core > 0"
    o = dict(crc=args.crc, beta=args.beta, cfo_max=args.cfo_max, extra_in_fz=args.extra_in_fz, rho=args.rho,
             fzstop=args.fzstop, spec=args.spec, cknn=args.cknn, ck=args.ck, bpsk_phase=args.bpsk_phase,
             sub=args.sub, rx=args.rx, dump=None, chan=not args.no_chan_intlv, design=args.design,
             design_snr=args.design_snr, cap_core=args.cap_core, cknn_name=args.cknn_name, ck_c=args.ck_c, sps=None,
             charge_all=args.charge_all, fulllog=None)
    if args.fulllog is not None:                                      # --fulllog: options checked before the pool
        import small_rx
        try:
            o["fulllog"] = sps_json(args.fulllog)
        except ValueError as e:
            ap.error(f"--fulllog: {e}")
        bad = sorted(set(o["fulllog"]) - set(small_rx.FL_DEF))
        if bad:
            ap.error(f"--fulllog: not small_rx.FL_DEF keys: {bad}")
        args.dump = True
    if args.ck_c is not None and args.cknn != "fmt":
        ap.error("--ck-c needs --cknn fmt")
    if args.sps is not None:                                          # --sps: parsed and checked before the pool
        import small_rx
        try:
            o["sps"] = sps_json(args.sps)
        except ValueError as e:
            ap.error(str(e))
        bad = sorted(set(o["sps"]) - set(small_rx.DEFAULT))
        if bad:
            ap.error(f"--sps: not small_rx spec keys: {bad}")
    if args.selfcheck:
        return selfcheck(o)
    if not (args.fmt and args.snrs and args.part):
        ap.error("give --fmt, --snrs and --part (or --selfcheck)")
    fmt = args.fmt
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, f"blind_fs_{args.part}.json")
    prog_path = os.path.join(RESULTS, f"blind_fs_{args.part}.prog")
    if os.path.exists(path):
        sys.exit(f"{path} exists: use a new --part")
    if args.dump:
        o["dump"] = os.path.join(RESULTS, f"blind_fs_{args.part}_dump")
    F = get_fmt(fmt, o)
    try:
        sps, prof = rx_spec(fmt, F, o, args.rx)
    except ValueError as e:                                           # (--cknn fmt on a profile without a mapping)
        sys.exit(str(e))
    if args.cknn == "fmt":                                            # the format's models must exist before the pool
        c_ = ck_index(sps, prof)
        if c_ is None:
            sys.exit(f"--cknn fmt: no checkpoint NN at profile {prof} for {fmt}")
        mp_ = bc.path("models", f"{sps['ck_nn_name']}_c{c_}.npz")
        if not os.path.exists(mp_):
            sys.exit(f"--cknn fmt: model {mp_} missing (train it with fullsys/ck_nn_fs.py --fmt {fmt})")
        print(f"--cknn fmt: checkpoint NN {mp_} at CK_FR[{c_}] (coarse start {sps.get('coarse')})", flush=True)
    A = F.A
    doc = dict(meta=dict(args=vars(args), fmt=fmt, spec=dict(pg.FMTS[fmt]), format=F.info(), profile=prof,
                         rx=args.rx or BL[fmt][1], std_core=STD_CORE[prof], calib=args.calib,
                         chan_intlv=F.chan_intlv, design=args.design, design_snr_db=args.design_snr,
                         cap_core=args.cap_core, sps_override=o["sps"], charge_all=args.charge_all,
                         fulllog=o["fulllog"],
                         seed_tag=pg.FMTS[fmt]["tag"] + (CALIB_TAG if args.calib else 0),
                         sps={k: (repr(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                              for k, v in sps.items()},
                         ebn0_offset=float(10 * np.log10(F.n_sym / A)), rho_bins=RHO_BINS.tolist(),
                         rth_bins=RTH_BINS.tolist(), psn_bins=PSN_BINS.tolist(), core_bins=list(CORE_B),
                         lerr_bins=LERR_B.tolist(), serr_bins=SERR_B.tolist(),
                         provisional=dict(rho=args.rho, fzstop=args.fzstop, spec=args.spec, cknn=args.cknn,
                                          cknn_name=sps.get("ck_nn_name"), ck_c=ck_index(sps, prof),
                                          ck=args.ck, bpsk_phase=args.bpsk_phase),
                         chain="txrx_chain._transmit (SPS %d, span %d), f ~ U[-cfo_max, cfo_max], phase ~ U[0, 2 pi)"
                               % (txrx_chain.SPS, txrx_chain.SPAN)), points=[])
    print(f"run_blind_fs {vars(args)} | {F.info()}", flush=True)
    t_run, npt = time.time(), len(args.snrs)

    def prog(done):
        with open(prog_path, "w") as fh:
            fh.write(f"{done:.4f} {npt} {time.time() - t_run:.0f}\n")

    for pi_, esn0 in enumerate(args.snrs):
        acc = run_point(fmt, esn0, args, o, lambda x: prog(pi_ + min(x, 1.0)))
        n = acc["frames"]
        p = dict(fmt=fmt, esn0=esn0, ebn0_burst=round(float(esn0 + 10 * np.log10(F.n_sym / A)), 4), **acc,
                 per=acc["frame_err"] / n, macs_per_frame=acc["sum_macs"] / n,
                 crit_par_d4a_per_frame=acc["sum_c_d4a"] / n, crit_par_h_d4a_per_frame=acc["sum_c_hd4a"] / n,
                 macs_per_core_std=acc["sum_" + STD_CORE[prof]] / n, max_macs_per_core_std=acc["max_" + STD_CORE[prof]],
                 cap_hit=acc["st"].get("cap_hit", 0), cap_hit_right=acc["st"].get("cap_hit_right", 0),
                 reenc_thr=float(max(__import__("blind_fast").rho_min(esn0), np.interp(esn0, *zip(*sps["rho_n"]))
                                     * np.sqrt(10 ** (esn0 / 10) / (1 + 10 ** (esn0 / 10))))
                                 if sps["rho_n"] else __import__("blind_fast").rho_min(esn0)))
        doc["points"].append(p)
        with open(path + ".tmp", "w") as fh:
            json.dump(doc, fh, indent=1)
        os.replace(path + ".tmp", path)
        prog(pi_ + 1)
        print(f"SNR {esn0:+.2f} dB | fmt {fmt} | Eb/N0 burst {p['ebn0_burst']:+.2f} | frames {n} | err "
              f"{acc['frame_err']} (undetected {acc['undetected']}) | PER {p['per']:.3e} | MACs/frame "
              f"{p['macs_per_frame'] / 1e6:.3f} M, per core ({STD_CORE[prof]}) {p['macs_per_core_std'] / 1e6:.3f} M "
              f"(max {p['max_macs_per_core_std'] / 1e6:.3f} M) | cap hits {p['cap_hit']} (right before the cap "
              f"{p['cap_hit_right']}) | {acc['time_s']:.0f} s", flush=True)
        if args.stop_per and p["per"] < args.stop_per:
            print(f"  PER {p['per']:.2e} < --stop-per {args.stop_per:g}: sweep ends", flush=True)
            prog(npt)
            break
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
