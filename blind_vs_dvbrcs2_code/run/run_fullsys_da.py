"""
Monte-Carlo PER of the full-system competitors with a DATA-AIDED synchroniser (fullsys/da_sync.py): DVB-RCS2 TC-LM
bursts (rcs2.py) and VDE-SAT Link 32 (vde.py), full Tx/Rx chain (txrx_chain.transmit: upsample, RRC, CFO, AWGN,
matched RRC, downsample), timing known, CFO f ~ U(-cfo_max, cfo_max) cycles per SYMBOL and phase ~ U(0, 2 pi) per
packet (VDE Link 32: the chips get f / SF per chip, despread at chip level first: <= 0.0125 dB loss at 0.03, see
da_sync.despread_loss_db; then DA on the 192 syncword + 180 pilot symbols).

Variants (--variant)
    standard  one DA estimate (rank-1 periodogram peak, Newton-refined), one turbo decode + CRC (a deployed receiver)
    strong    the top-M candidates (--top-m, default 3) in Lambda order, decoded until the CRC passes (est4 CRC search)
    genie     CFO / phase applied and corrected with the TRUE f, phase, gain and N0 (sync loss = 0, chain effects in)
    ideal     f = 0, phase 0, genie N0: exactly run_rcs2.py / run_vde.py (same packets, same noise, same decisions)
--n0 est (default: N0 from the known-symbol residual, a real receiver) | genie (true N0 / |g_hat|^2).
Decoders as run_rcs2 (max-log, 8 it, ADAPTIVE sf, aff3ct interleaver) / run_vde (max-log x 0.75 or --algo logmap, 8 it,
CRC early stop). rcs2 early stop (2026-11-19, the user-approved standard, default ON from then on; the final parts
da_fs-q3td / q3deep / q13da / q14td / q42td ran --no-early-stop): a CRC-32 check after every full iteration from
--es-crc-start (1), stop at the first pass; --es-crc-cost (on) charges those checks (turbo_db.macs crc_ops: 1 op per
decoded bit per check, crit ceil(2 N / 32) + log2 2 N each) on top of the iterations actually run. Both recorded in
meta args (a missing key = the earlier behaviour: crc_start 2, CRC not charged).

Pairing: the payload + noise rng of a chunk is EXACTLY run_rcs2's / run_vde's (same --seed, point, chunk index, batch);
the CFO / phase come from a separate stream (the same entropy + [1]), so the noise samples equal the ideal run's and
the four variants at one --seed see the same packets (paired McNemar tests; do not pool equal seeds).
Calibration / tuning runs: --calib-seed-offset 1000000 (CALIB_SEED_OFFSET; rng seed = --seed + offset), disjoint from
the test runs. Scope: timing and burst position are KNOWN (no timing / frame detection); the known symbols serve only
the CFO and carrier-phase (+ N0) estimate. --cfo-max is free (draw range AND search window): 0.03 default, realistic
ranges e.g. DVB-RCS2 0.002, VDE the residual Doppler.
Frame error = CRC fail OR payload mismatch; undetected = CRC pass AND mismatch.
Output fullsys/results/da_<part>.json (rewritten after every point, refuses to overwrite), progress
fullsys/results/da_<part>.prog ("done total elapsed_s" in points), --dump: per-packet records da_<part>_p<i>.npz.
Run on the cluster only (Run:ai job). Locally only --selfcheck (noiseless, 2 packets per system, f = +-0.029).

    python fullsys/run_fullsys_da.py --sys rcs2 --wf 13 --snrs -1.2 -1.0 --variant strong --frames 1000000 --part x
    python fullsys/run_fullsys_da.py --sys vde --link 32 --snrs -4.5 --variant standard --algo logmap --part y
    python fullsys/run_fullsys_da.py --sys nbiot --nbfmt nb328 --snrs -1.0 --variant strong --cfo-max 0.035 --part z

--sys nbiot (NBSys, fullsys/nbiot.py): NB-IoT NPUSCH format 1, single tone 3.75 kHz, DA on the DM-RS comb (1 per
2 ms slot, true symbol times with the 3/11-symbol guard), LTE turbo + CRC-24A early stop (default on), batch 200 and
the run_polar_genie seed tag of the format: the payloads equal the polar genie run's at the same --seed.

Hooks (NOT applied here; the main session may wire them into rcs2.py / vde.py, 3 lines each):
    rcs2.synchronise, replacing the NotImplementedError line under `if sync == "da":`
        from fullsys import da_sync
        return da_sync.rcs2_hook(r, wf, n0, **kw)
    vde.VDELink.rx, replacing the NotImplementedError line under `if sync == "da":`
        from fullsys import da_sync
        y, N0 = da_sync.vde_hook(self, r, N0_el)
        return self.decode_llr(self.data_llr(y, N0), iters, algo, scale, early)
"""

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))                 # (package) run/
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "blind"), os.path.join(ROOT, "dvbrcs2")]

import txrx_chain                                                  # noqa: E402
import da_sync as DA                                               # noqa: E402
import rcs2, turbo_db as tdb                                       # noqa: E402
import costmodel                                                   # noqa: E402
from run_rcs2 import wf_code                                       # noqa: E402  (the rcs2 seed sequence)

RESULTS = os.path.join(HERE, "results")
DELAY = txrx_chain.SPAN / 2                    # MF output n carries 2 pi f (n + DELAY) + phase (elements)
FERR_FINE = np.linspace(-1.0, 1.0, 201)        # f error / (1 / 2L): inside the outlier threshold
FERR_COARSE = np.linspace(-0.1, 0.1, 401)      # f error (cycles / symbol): side peaks, aliases
PH_EDGES = np.linspace(-np.pi, np.pi, 181)     # phase error at the known-symbol centre (rad)
N0_EDGES = np.linspace(-3.0, 3.0, 121)         # 10 log10(N0_hat / N0_true) (clipped into the range)
KP = DA.KP
CALIB_SEED_OFFSET = 1000000                    # --calib-seed-offset for calibration runs (test runs: 0, seeds < 1e6)


# ---- system adapters: tx, channel, genie values, decode through the public rcs2 / vde functions -------------------
class RCS2Sys:
    name = "rcs2"

    def __init__(self, o):
        self.o, self.key = o, rcs2.wf_key(o["wf"])
        self.wf = wf = rcs2.Waveform(self.key, direction=o["itl"])
        self.lay = DA.rcs2_layout(wf, o["cfo_max"])
        self.gm = float(np.sum(txrx_chain.rrc(rcs2.ROLLOFF) ** 2))  # MF peak gain (= 1 up to the truncation)
        self.n_data, self.sf = wf.n_data, 1
        self.front, self.front_crit, self.llr, self.llr_crit = 0.0, 0.0, 0.0, 0.0   # LLR scaling is in tdb.macs
        assert o.get("nda", "off") == "off" or wf.mod == "qpsk", "--nda: the 4th-power line needs a QPSK burst"
        self.batch = o["batch"] or 200                              # run_rcs2 --batch default
        _costs(self, o)

    def rngs(self, seed, esn0, c):
        ent = [seed, wf_code(self.key), int(round(esn0 * 1000)) + 100000, c]      # = run_rcs2.run_point
        return (np.random.default_rng(np.random.SeedSequence(ent)),
                np.random.default_rng(np.random.SeedSequence(ent + [1])))

    def draw(self, rng, B):
        pdu = rng.integers(0, 2, (B, self.wf.k)).astype(np.int8)
        return pdu, rcs2.tx(pdu, self.wf)[0]

    def channel(self, s, f, ph, esn0, rng):
        return txrx_chain.transmit(s, f, ph, esn0, rng, beta=rcs2.ROLLOFF)

    def g_true(self, f, ph):
        return self.gm * np.exp(1j * (ph + 2 * np.pi * f * DELAY))

    def n0_true(self, esn0):
        return self.gm ** 2 * 10 ** (-esn0 / 10)

    def ideal(self, r, esn0):
        return r, 10 ** (-esn0 / 10)                                # exactly run_rcs2.run_chunk

    def decide(self, y):
        if self.wf.mod == "pi2bpsk":
            rot = np.exp(1j * (np.pi * np.arange(y.shape[1]) / 2 + np.pi / 4))[None]
            return np.where((y * np.conj(rot)).real >= 0, 1.0, -1.0) * rot
        return (np.where(y.real >= 0, 1.0, -1.0) + 1j * np.where(y.imag >= 0, 1.0, -1.0)) / np.sqrt(2)

    def decode(self, y, n0):
        """rcs2.rx at the given sync; ops = turbo_db.macs (NOT costmodel.turbo_ops: costmodel's SISO step is the
        binary 8-state trellis of turbo_vde / polar_rm, the RCS2 code is the duo-binary 16-state CRSC with 4 branches
        per state; turbo_db.macs counts that trellis in the same unit, every add / compare-select / multiply / LUT = 1
        op, crit = its 32-core state-parallel path, + the demapper LLR scaling)."""
        o, wf = self.o, self.wf
        n0 = n0 if np.ndim(n0) == 0 else np.asarray(n0)[:, None, None]
        out = rcs2.rx(y, wf, n0, sync="ideal", algo=o["algo"], iters=o["iters"], sf=o["sf"],
                      early_stop=o["early_stop"], exact_demap=o["exact_demap"], sf_low_iters=o["sf_low_iters"],
                      crc_start=o.get("es_crc_start", 2))                # (missing key: the runs before 2026-11-19)
        it = np.asarray(out["iters"])                                    # iterations actually run per burst
        m = tdb.macs(wf.code.N, it, o["algo"], o["early_stop"], n_sym=wf.n_data, bps=wf.m, crc=wf.crc,
                     crc_ops=o.get("es_crc_cost", False), crc_start=o.get("es_crc_start", 2))   # + the CRC checks run
        tot = np.broadcast_to(np.asarray(m["total"], float), it.shape)
        crit = np.broadcast_to(np.asarray(m["crit"], float), it.shape)
        return out["pdu"], out["crc"], it, np.asarray(out["first_pass"]), tot, crit


def _costs(S, o):
    """Synchroniser costs of S.lay: 'lean' (the competitor cost reported) and 'upper' (what runs: o['refine'] maxima,
    nfft >= 4 span), da_sync.cost -> costmodel.da_ops / da_crit."""
    if o.get("nda", "off") != "off":                                     # (--nda) the 4th-power NDA estimator
        dn = o["newton"] if o["nda"] == "pow4da" else 0
        S.cost_lean = DA.nda_cost(S.lay, S.n_data, "lean", o["newton"], dn, o["cfo_max"])
        S.cost_up = DA.nda_cost(S.lay, S.n_data, "upper", o["newton"], dn, o["cfo_max"])
        return
    S.cost_lean = DA.cost(S.lay, S.n_data, "lean", newton=o["newton"])
    S.cost_up = DA.cost(S.lay, S.n_data, "upper", refine=o["refine"], newton=o["newton"])


SYSTEMS = {"rcs2": RCS2Sys}
_S = {}


def _init(o):
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ[v] = "1"
    _S["sys"] = SYSTEMS[o["sys"]](o)


# ---- one batch of packets -----------------------------------------------------------------------------------------
def simulate(S, o, esn0, rng, rngc, B, f_set=None, ph_set=None):
    """B packets through tx -> channel -> sync variant -> decode attempts. Returns per-packet records."""
    lay, var = S.lay, o["variant"]
    f = rngc.uniform(-o["cfo_max"], o["cfo_max"], B)
    ph = rngc.uniform(0, 2 * np.pi, B)
    if f_set is not None:
        f, ph = np.asarray(f_set, float), np.asarray(ph_set, float)
    pay, s = S.draw(rng, B)
    if var == "ideal":
        f, ph = np.zeros(B), np.zeros(B)
    r = S.channel(s, f, ph, esn0, rng)
    n0t = S.n0_true(esn0)
    gt = S.g_true(f, ph)
    M = o["top_m"] if var == "strong" else 1
    da = var in ("standard", "strong")
    cl, cu = S.cost_lean, S.cost_up
    if da:
        if o.get("nda", "off") != "off":                                # (--nda) 4th-power NDA f, UW phase / N0
            assert M == 1 and not hasattr(S, "estimate"), "--nda: variant standard, rcs2 only"
            e = DA.nda4_estimate(r, lay, o["cfo_max"], iters=o["newton"],
                                 da_newton=o["newton"] if o["nda"] == "pow4da" else 0)
        elif hasattr(S, "estimate"):                                    # system hook (nbiot: DA on the DM-RS comb)
            e = S.estimate(r, n_cand=M, refine=o["refine"], iters=o["newton"])
        else:
            e = DA.estimate(r, lay, n_cand=M, refine=o["refine"], iters=o["newton"])
        F, G, N0h, valid = e["f"], e["g"], e["n0"], e["valid"]
        valid[:, 0] = True
        st0, cr0 = S.front + cl["ops"]["first"], S.front_crit + cl["crit"]["first"]
        up0, upc0 = cu["ops"]["first"] - cl["ops"]["first"], cu["crit"]["first"] - cl["crit"]["first"]
    else:                                                               # genie / ideal: the true values, no sync cost
        F, G = f[:, None], gt[:, None]
        N0h, valid = np.full((B, 1), n0t), np.ones((B, 1), bool)
        st0, cr0, up0, upc0 = S.front, S.front_crit, 0.0, 0.0
    pay_hat = np.zeros_like(pay)
    crc = np.zeros(B, bool)
    chosen = np.zeros(B, np.int64)                                      # rank (1..M) of the CRC-passing candidate
    iters = np.full((B, M), -1, np.int64)
    first = np.full((B, M), -1, np.int64)
    st_ops = np.zeros((B, M + 1))
    st_crit = np.zeros((B, M + 1))
    st_ops[:, 0], st_crit[:, 0] = st0, cr0
    up_ops, up_crit = np.full(B, up0), np.full(B, upc0)                # upper bracket - lean, per packet
    crc1, mism1 = np.zeros(B, bool), np.zeros(B, bool)                  # attempt 1 = the 'standard' receiver
    fsel = F[:, 0].copy()
    for m in range(M):
        act = np.flatnonzero(~crc & valid[:, m])
        if len(act) == 0:
            break
        if var == "ideal":
            y, n0 = S.ideal(r, esn0)
        else:
            fm, gm = F[act, m], G[act, m]
            if var != "genie" and o["dd_iters"] > 0:
                fm, gm = DA.dd_refine(r[act], fm, gm, S.decide, lay, o["dd_iters"])
            y = (S.correct if hasattr(S, "correct") else DA.correct)(r[act], fm, gm)   # nbiot: true symbol times
            n0 = (n0t if (o["n0"] == "genie" or var == "genie") else N0h[act, m]) / np.abs(gm) ** 2
        pa, ok, it, fp, tot, cr = S.decode(y, n0)
        if da and m > 0:
            tot, cr = tot + DA.attempt_cost(cl, m), cr + DA.attempt_cost(cl, m, "crit")
            up_ops[act] += DA.attempt_cost(cu, m) - DA.attempt_cost(cl, m)
            up_crit[act] += DA.attempt_cost(cu, m, "crit") - DA.attempt_cost(cl, m, "crit")
        if m == 0:
            crc1[act], mism1[act] = ok, np.any(pa != pay[act], 1)
        st_ops[act, m + 1], st_crit[act, m + 1] = tot, cr
        iters[act, m], first[act, m] = it, fp
        upd = act[ok] if m > 0 else act                                 # attempt 1 is the fallback decision
        pay_hat[upd] = pa[ok] if m > 0 else pa
        fsel[act[ok]] = F[act[ok], m]
        crc[act[ok]] = True
        chosen[act[ok]] = m + 1
    nbe = np.sum(pay_hat != pay, 1)
    thr = lay.outlier_thr()
    hit = np.abs(F - f[:, None]) <= thr
    hit &= valid
    true_rank = np.where(hit.any(1), hit.argmax(1) + 1, 0)
    nc = lay.pos.mean()
    return dict(f=f, ph=ph, f1=F[:, 0], fsel=fsel, ph_err1=DA.phase_err(F[:, 0], G[:, 0], f, gt, nc),
                n0_ratio1=N0h[:, 0] / n0t, crc=crc, mism=nbe > 0, nbe=nbe, chosen=chosen, true_rank=true_rank,
                iters=iters, first=first, st_ops=st_ops, st_crit=st_crit, M=M, crc1=crc1, mism1=mism1,
                up_ops=up_ops, up_crit=up_crit, peaks=(e["peaks"] if da else np.ones(B, np.int64)))


def _hist_dict(v, mask):
    u, c = np.unique(np.round(v[mask]).astype(np.int64), return_counts=True)
    return {str(a): int(b) for a, b in zip(u, c)}


ERR_FIELDS = ("chunk", "idx", "f", "ph", "f1-f", "fsel-f", "ph_err1", "n0_ratio1", "nbe", "chosen", "true_rank",
              "iters")                                                 # per-error-packet rows (iters: per attempt, -1 = not run)


def summarise(rec, S, o, c=0):
    """Per-packet records of chunk c -> mergeable counters / histograms + the frame-error rows (ERR_FIELDS)."""
    M, it_n = rec["M"], o["iters"] + 1
    fe = ~rec["crc"] | rec["mism"]
    fe1 = ~rec["crc1"] | rec["mism1"]                                  # attempt 1 alone: the standard receiver
    ops1, crit1 = rec["st_ops"][:, :2].sum(1), rec["st_crit"][:, :2].sum(1)
    da = o["variant"] in ("standard", "strong")                        # upper - lean of attempt 1: the first-stage gap
    up1 = S.cost_up["ops"]["first"] - S.cost_lean["ops"]["first"] if da else 0.0
    up1c = S.cost_up["crit"]["first"] - S.cost_lean["crit"]["first"] if da else 0.0
    eidx = np.flatnonzero(fe)
    rows = [[int(c), int(i), float(rec["f"][i]), float(rec["ph"][i]), float(rec["f1"][i] - rec["f"][i]),
             float(rec["fsel"][i] - rec["f"][i]), float(rec["ph_err1"][i]), float(rec["n0_ratio1"][i]),
             int(rec["nbe"][i]), int(rec["chosen"][i]), int(rec["true_rank"][i]), rec["iters"][i].tolist()]
            for i in eidx]
    thr = S.lay.outlier_thr()
    e1, es = rec["f1"] - rec["f"], rec["fsel"] - rec["f"]
    inl = np.abs(e1) <= thr
    ops, crit = rec["st_ops"].sum(1), rec["st_crit"].sum(1)
    st = dict(reach=[len(fe)] + [0] * M, crc_pass=[0] * (M + 1), correct=[0] * (M + 1), undetected=[0] * (M + 1),
              crc_fail=[0] * (M + 1), ops=rec["st_ops"].sum(0).tolist(), crit=rec["st_crit"].sum(0).tolist(),
              iters_hist=[[0] * it_n for _ in range(M + 1)], first_hist=[[0] * it_n for _ in range(M + 1)])
    for m in range(M):
        a = rec["iters"][:, m] >= 0
        pas = a & (rec["chosen"] == m + 1)
        st["reach"][m + 1] = int(a.sum())
        st["crc_pass"][m + 1] = int(pas.sum())
        st["correct"][m + 1] = int((pas & ~rec["mism"]).sum())
        st["undetected"][m + 1] = int((pas & rec["mism"]).sum())
        st["crc_fail"][m + 1] = int((a & ~pas).sum())
        st["iters_hist"][m + 1] = np.bincount(rec["iters"][a, m], minlength=it_n)[:it_n].tolist()
        st["first_hist"][m + 1] = np.bincount(rec["first"][a, m], minlength=it_n)[:it_n].tolist()
    n0db = np.clip(10 * np.log10(np.maximum(rec["n0_ratio1"], 1e-30)), N0_EDGES[0], N0_EDGES[-1])
    return dict(
        frames=len(fe), frame_err=int(fe.sum()), err_idx=eidx.tolist(), err_idx_att1=np.flatnonzero(fe1).tolist(),
        err_rows=rows,
        standard_frame_err=int(fe1.sum()), standard_crc_fail=int((~rec["crc1"]).sum()),
        standard_undetected=int((rec["crc1"] & rec["mism1"]).sum()), standard_mismatch=int(rec["mism1"].sum()),
        standard_ops_sum=float(ops1.sum()), standard_crit_sum=float(crit1.sum()),
        standard_ops_upper_sum=float((ops1 + up1).sum()), standard_crit_upper_sum=float((crit1 + up1c).sum()),
        standard_ops_hist_right=_hist_dict(ops1, ~fe1), standard_ops_hist_wrong=_hist_dict(ops1, fe1),
        standard_crit_hist_right=_hist_dict(crit1, ~fe1), standard_crit_hist_wrong=_hist_dict(crit1, fe1),
        ops_upper_sum=float((ops + rec["up_ops"]).sum()), crit_upper_sum=float((crit + rec["up_crit"]).sum()),
        crc_fail=int((~rec["crc"]).sum()), undetected=int((rec["crc"] & rec["mism"]).sum()),
        mismatch=int(rec["mism"].sum()), bit_err=int(rec["nbe"].sum()),
        ops_sum=float(ops.sum()), crit_sum=float(crit.sum()), stages=st,
        rank_ok=np.bincount(rec["chosen"], minlength=M + 1).tolist(),
        true_rank=np.bincount(rec["true_rank"], minlength=M + 1).tolist(),
        ops_hist_right=_hist_dict(ops, ~fe), ops_hist_wrong=_hist_dict(ops, fe),
        crit_hist_right=_hist_dict(crit, ~fe), crit_hist_wrong=_hist_dict(crit, fe),
        outliers_rank1=int((~inl).sum()), outliers_final=int((np.abs(es) > thr).sum()),
        outliers_rank1_err=int((~inl & fe).sum()),
        ferr_sum=float(e1[inl].sum()), ferr_sq=float((e1[inl] ** 2).sum()), ferr_n=int(inl.sum()),
        ferr_absmax=float(np.abs(e1).max()),
        ferr_hist_fine=np.histogram(e1 / thr, FERR_FINE)[0].tolist(),
        ferr_hist_coarse=np.histogram(e1, FERR_COARSE)[0].tolist(),
        pherr_sq=float((rec["ph_err1"][inl] ** 2).sum()),
        pherr_hist=np.histogram(rec["ph_err1"], PH_EDGES)[0].tolist(),
        n0db_sum=float(n0db.sum()), n0db_hist=np.histogram(n0db, N0_EDGES)[0].tolist(),
        peaks_sum=int(rec["peaks"].sum()))


def _merge(acc, res):
    for k, v in res.items():
        if k not in acc:
            acc[k] = v
        elif isinstance(v, dict) and k == "stages":
            for kk, vv in v.items():
                acc[k][kk] = _merge_val(acc[k][kk], vv)
        else:
            acc[k] = _merge_val(acc[k], v)
    return acc


def _merge_val(a, b):
    if isinstance(b, dict):
        for k, v in b.items():
            a[k] = a.get(k, 0) + v
        return a
    if isinstance(b, list):
        return [_merge_val(x, y) for x, y in zip(a, b)]
    return a + b


DUMP_KEYS = ("f", "ph", "f1", "fsel", "ph_err1", "n0_ratio1", "crc", "mism", "chosen", "true_rank", "iters", "first",
             "st_ops", "st_crit", "crc1", "mism1", "up_ops", "up_crit")
PER_CHUNK = ("err_idx", "err_idx_att1", "err_rows", "ferr_absmax")    # not summed: run_point keeps them per chunk


def run_chunk(task):
    esn0, c, B, o = task
    S = _S["sys"]
    rng, rngc = S.rngs(o["seed"], esn0, c)
    rec = simulate(S, o, esn0, rng, rngc, B)
    res = summarise(rec, S, o, c)
    dump = None
    if o["dump"]:
        dump = {k: (rec[k].astype(np.float32) if rec[k].dtype == float else rec[k]) for k in DUMP_KEYS}
        dump["chunk"] = np.full(B, c, np.int32)
        dump["idx"] = np.arange(B, dtype=np.int32)
    return c, res, dump


def run_point(o, esn0, pi, npts, t0, prog):
    S = _S["sys"]
    batch = S.batch
    nch = -(-o["frames"] // batch)
    tasks = ((esn0, c, min(batch, o["frames"] - c * batch), o) for c in range(nch))
    acc, absmax = {}, 0.0
    chunks = dict(batch=batch, index=[], frame_err=[], err_idx=[], err_idx_att1=[])   # per chunk c: pairing
    err_rows, dumps = [], []
    tp = tlast = time.time()
    with Pool(o["workers"], initializer=_init, initargs=(o,)) as pool:
        for c, res, dump in pool.imap(run_chunk, tasks):
            chunks["index"].append(c)
            chunks["err_idx"].append(res.pop("err_idx"))
            chunks["err_idx_att1"].append(res.pop("err_idx_att1"))   # attempt 1 = the standard receiver's errors
            chunks["frame_err"].append(res["frame_err"])
            err_rows += res.pop("err_rows")
            absmax = max(absmax, res.pop("ferr_absmax"))
            _merge(acc, res)
            if dump is not None:
                dumps.append(dump)
            if time.time() - tlast > 60:
                tlast = time.time()
                print(f"  progress {S.name} Es/N0 {esn0:+.2f}: frames {acc['frames']} err {acc['frame_err']} "
                      f"({time.time() - tp:.0f} s)", flush=True)
                with open(prog, "w") as fh:
                    fh.write(f"{pi + min(acc['frames'] / o['frames'], 1.0):.4f} {npts} {time.time() - t0:.0f}\n")
            if acc["frame_err"] >= o["max_err"] or acc["frames"] >= o["frames"]:
                break
        pool.terminate()
    acc["ferr_absmax"] = absmax
    acc["time_s"] = round(time.time() - tp, 1)
    acc["chunks"] = chunks
    acc["err_rows"] = err_rows
    return acc, dumps


def point_doc(S, o, esn0, acc):
    n = acc["frames"]
    lay = S.lay
    st = acc["stages"]
    crb = float(lay.crb(esn0))
    p = dict(sys=S.name, esn0=esn0, variant=o["variant"], frames=n, per=acc["frame_err"] / n,
             crb_f=crb, sqrt_crb_f=float(np.sqrt(crb)), outlier_thr=lay.outlier_thr(),
             rms_ferr_inliers=float(np.sqrt(acc["ferr_sq"] / max(acc["ferr_n"], 1))),
             mean_ferr_inliers=acc["ferr_sum"] / max(acc["ferr_n"], 1),
             rms_pherr_inliers=float(np.sqrt(acc["pherr_sq"] / max(acc["ferr_n"], 1))),
             mse_over_crb=float(acc["ferr_sq"] / max(acc["ferr_n"], 1) / crb) if crb > 0 else None,
             outlier_rate_rank1=acc["outliers_rank1"] / n, outlier_rate_final=acc["outliers_final"] / n,
             n0db_mean=acc["n0db_sum"] / n, peaks_mean=acc["peaks_sum"] / n,
             ops_mean=acc["ops_sum"] / n, crit_mean=acc["crit_sum"] / n,
             stage_ops_mean=[v / n for v in st["ops"]], stage_crit_mean=[v / n for v in st["crit"]],
             attempts_mean=sum(st["reach"][1:]) / n,
             ops_upper_mean=acc["ops_upper_sum"] / n, crit_upper_mean=acc["crit_upper_sum"] / n,
             # the standard receiver (one estimate, one decode) = attempt 1 of these packets (stage counters 0 + 1,
             # chunks.err_idx_att1): exact, since rank 1 does not depend on top_m
             standard_frames=n, standard_per=acc["standard_frame_err"] / n,
             standard_ops_mean=acc["standard_ops_sum"] / n, standard_crit_mean=acc["standard_crit_sum"] / n,
             standard_ops_upper_mean=acc["standard_ops_upper_sum"] / n,
             standard_crit_upper_mean=acc["standard_crit_upper_sum"] / n,
             standard_iters_hist=st["iters_hist"][1], standard_first_hist=st["first_hist"][1])
    if S.name == "rcs2":
        p.update(ebn0_burst=round(float(S.wf.ebn0(esn0)), 4), L_burst=S.wf.L, k=S.wf.k, pay=S.wf.pay,
                 ref_tr=rcs2.REF_PER.get(S.key) and {str(k): v for k, v in rcs2.REF_PER[S.key].items()})
    elif S.name == "nbiot":
        p.update(S.point_extra(esn0))
    else:
        p.update(ebn0_payload=float(S.L.ebn0_db(esn0)), L_burst=S.L.n_sym, k=S.L.kpay)
    p.update(acc)
    return p


def meta_doc(S, o):
    lay = S.lay
    m = dict(args=o, sys=S.name, layout=dict(name=lay.name, Nk=lay.Nk, span=lay.span, L=lay.L, nfft=lay.nfft,
                                             fwin=lay.fwin, n_win=lay.n_win, outlier_thr=lay.outlier_thr()),
             sync_cost=dict(lean=S.cost_lean, upper=S.cost_up, front_ops=S.front, front_crit=S.front_crit,
                            llr_per_attempt=S.llr, llr_crit_per_attempt=S.llr_crit),
             err_fields=list(ERR_FIELDS),
             da=dict(MARGIN=DA.MARGIN, DEDUP=DA.DEDUP, KP=KP), nda=o.get("nda", "off"),
             edges=dict(ferr_fine_over_thr=FERR_FINE.tolist(), ferr_coarse=FERR_COARSE.tolist(),
                        pherr=PH_EDGES.tolist(), n0db=N0_EDGES.tolist()),
             stages="index 0 = estimation (+ despreading for VDE), m = decode attempt m (candidate rank m)",
             cost="ops / crit (MACs per core) = the LEAN synchroniser (costmodel.da_ops / da_crit: 1 maximum refined, "
                  "nfft >= 2 span; + refine_one + per_cand per further candidate) + front end + decoder; *_upper = "
                  "the synchroniser that runs (refine maxima, nfft >= 4 span). Decoder: rcs2 turbo_db.macs (duo-binary "
                  "16-state, not in costmodel's binary SISO), vde decode_llr ops / ops_crit (costmodel.turbo_ops / "
                  "crit_turbo) + LLR scaling; vde front end costmodel.frontend_ops / crit minus the chip-rate "
                  "de-rotation (despreading). dd_iters > 0 is not costed.",
             mac_unit=dict(unit=costmodel.MAC_UNIT, derot=costmodel.DEROT, cmul=costmodel.CMUL, fft_c=costmodel.FFT_OPS),
             chain="txrx_chain.transmit (SPS %d, span %d)" % (txrx_chain.SPS, txrx_chain.SPAN))
    if S.name == "vde":
        m.update(despread_loss_db_at_cfo_max=DA.despread_loss_db(o["cfo_max"], S.sf), sf=S.sf)
    if S.name == "nbiot":
        m.update(S.meta())
    return m


# ---- self-check (local, < 5 s): noiseless, f = +-0.029 -------------------------------------------------------------
def selfcheck():
    t0 = time.time()
    base = dict(cfo_max=DA.CFO_MAX, variant="standard", top_m=1, refine=DA.REFINE, newton=DA.NEWTON,
                dd_iters=0, n0="est", batch=0, iters=8, itl=tdb.INTERLEAVER_DIR, algo="maxlog", sf=tdb.SF_DEFAULT,
                early_stop=True, exact_demap=False, sf_low_iters=None, scale=None)
    cases = [("rcs2", dict(wf="13")), ("rcs2", dict(wf="42")),
             ("rcs2", dict(wf="2")), ("rcs2", dict(wf="5")), ("rcs2", dict(wf="5", nda="pow4")),
             ("rcs2", dict(wf="5", nda="pow4da"))]
    ok_all = True
    for name, extra in cases:
        S = None
        for var, m in (("standard", 1), ("strong", DA.TOP_M), ("genie", 1), ("ideal", 1)):
            if extra.get("nda") and var == "strong":                     # (--nda: one estimate, standard only)
                continue
            o = dict(base, sys=name, variant=var, top_m=m, **extra)
            S = S or SYSTEMS[name](o)
            S.o = o
            rng = np.random.default_rng(5)
            rec = simulate(S, o, 60.0, rng, rng, 2, f_set=[0.029, -0.029], ph_set=[1.0, -2.5])
            acc = {}
            for c in (0, 1):                                            # the chunk-merge path
                res = summarise(rec, S, o, c)
                for k in PER_CHUNK:
                    res.pop(k)
                _merge(acc, res)
            json.dumps(dict(meta=meta_doc(S, o), points=[point_doc(S, o, 60.0, dict(acc, time_s=0.0, chunks={},
                                                                                   err_rows=[], ferr_absmax=0.0))]))
            ferr = rec["f1"] - rec["f"]
            good = bool(np.all(np.abs(ferr) < 1e-4) and rec["crc"].all() and not rec["mism"].any()
                        and acc["frames"] == 4 and acc["stages"]["reach"][1] == 4)
            ok_all &= good
            print(f"selfcheck {name} {extra} {var:<8}: f_err {ferr[0]:+.2e} {ferr[1]:+.2e} | phase err "
                  f"{rec['ph_err1'][0]:+.2e} {rec['ph_err1'][1]:+.2e} rad | crc {rec['crc'].tolist()} mismatch "
                  f"{rec['mism'].tolist()} | rank_ok {acc['rank_ok']} | ops/pkt {acc['ops_sum'] / 4:.3g} crit "
                  f"{acc['crit_sum'] / 4:.3g} | {'OK' if good else 'FAIL'}", flush=True)
    print("CRB per layout (sqrt, cycles/symbol) at the reference Es/N0 (TR PER 1e-3 / M.2092 threshold):")
    for name, extra, ref in [("rcs2", dict(wf="3"), -0.27), ("rcs2", dict(wf="13"), -0.80),
                             ("rcs2", dict(wf="14"), 1.49), ("rcs2", dict(wf="42"), -3.81)]:
        lay = DA.rcs2_layout(rcs2.Waveform(rcs2.wf_key(extra["wf"])))
        print(f"  {lay.name:<9} Nk {lay.Nk:4d} span {lay.span:5d} nfft {lay.nfft:6d} | Es/N0 {ref:+.2f} dB: "
              f"sqrt CRB {np.sqrt(lay.crb(ref)):.2e} | outlier thr 1/(2L) {lay.outlier_thr():.2e}")
        cl, cu = DA.cost(lay, lay.L - lay.Nk, "lean"), DA.cost(lay, lay.L - lay.Nk, "upper")
        print(f"            sync ops lean {cl['ops']['first']:.0f} (crit {cl['crit']['first']:.0f}, nfft {cl['nfft']}) "
              f"| upper {cu['ops']['first']:.0f} (crit {cu['crit']['first']:.0f}, nfft {cu['nfft']}) | per further "
              f"candidate lean {cl['ops']['per_cand'] + cl['ops']['refine_one']:.0f} upper {cu['ops']['per_cand']:.0f}")
    print(f"despreading loss at |f| = 0.03 / symbol, SF 8: {DA.despread_loss_db(0.03, 8):.4f} dB")
    print(f"selfcheck {'PASSED' if ok_all else 'FAILED'} in {time.time() - t0:.1f} s", flush=True)
    return ok_all


def _err_sets(path):
    """Per point (esn0, frames, {(chunk, idx)} of frame errors) of a da_ / rcs2_ / vde_ results file."""
    with open(path) as fh:
        doc = json.load(fh)
    out = []
    for p in doc["points"]:
        if "chunk_err" in p:                                            # run_vde: [[chunk, frames, [idx]], ...]
            e = {(c, i) for c, _, idx in p["chunk_err"] for i in idx}
        elif "chunks" not in p:
            print(f"check: {os.path.basename(path)} Es/N0 {p['esn0']:+.2f} has no per-chunk errors", flush=True)
            e = None
        else:                                                           # run_rcs2 / run_fullsys_da chunks
            ch = p["chunks"]
            e = {(c, i) for c, idx in zip(ch.get("index", range(len(ch["err_idx"]))), ch["err_idx"]) for i in idx}
        out.append((p["esn0"], p["frames"], e))
    return out


def check(a, b):
    """Smoke assertion: the two runs have the same frames and the same frame-error packets at every point."""
    A, B = _err_sets(a), _err_sets(b)
    ok = len(A) == len(B)
    for (ea, na, sa), (eb, nb, sb) in zip(A, B):
        if sa is None or sb is None:
            ok = False
            continue
        same = ea == eb and na == nb and sa == sb
        ok &= same
        print(f"check Es/N0 {ea:+.2f}/{eb:+.2f}: frames {na}/{nb} errors {len(sa)}/{len(sb)} common {len(sa & sb)} "
              f"-> {'MATCH' if same else 'MISMATCH'}", flush=True)
    print(f"CHECK {'PASSED' if ok else 'FAILED'}: {os.path.basename(a)} vs {os.path.basename(b)}", flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sys", choices=sorted(SYSTEMS))
    ap.add_argument("--wf", default="13", help="rcs2 waveform ID: 2 3 5 13 14 42; custom C44 (pc1024 competitor) or "
                    "C44p<P>q<Q0>-<Q1>-<Q2>-<Q3> (rcs2.wf_spec)")
    ap.add_argument("--link", default="32", help="vde LINKS key (32)")
    ap.add_argument("--nbfmt", default="nb328", help="nbiot format (fullsys/nbiot.FORMATS): nb208 nb208b nb296 nb328 "
                    "nb808 nb1000 nb1000r10 aff3ct-K2048 (code-only, ideal / genie)")
    ap.add_argument("--snrs", nargs="+", type=float, help="Es/N0 per (despread) data symbol, dB")
    ap.add_argument("--frames", type=int, default=100000)
    ap.add_argument("--max-err", type=int, default=200)
    ap.add_argument("--batch", type=int, default=0, help="0 = the ideal runner's default (pairing)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--calib-seed-offset", type=int, default=0,
                    help="added to --seed (rng seed = seed + offset); calibration / tuning runs use CALIB_SEED_OFFSET "
                         f"= {CALIB_SEED_OFFSET} so their packets are disjoint from the test runs (offset 0)")
    ap.add_argument("--part")
    ap.add_argument("--variant", default="standard", choices=["standard", "strong", "genie", "ideal"])
    ap.add_argument("--top-m", type=int, default=DA.TOP_M, help="strong: candidates tried")
    ap.add_argument("--refine", type=int, default=DA.REFINE, help="local maxima refined before the ranking")
    ap.add_argument("--newton", type=int, default=DA.NEWTON, help="Newton steps per refined maximum")
    ap.add_argument("--dd-iters", type=int, default=DA.DD_ITERS, help="decision-directed Newton steps (0 = off)")
    ap.add_argument("--nda", default="off", choices=["off", "pow4", "pow4da"], help="(rcs2 QPSK, variant standard) "
                    "4th-power NDA CFO over the whole burst (da_sync.nda4_estimate): pow4 = its f, the UW for phase / "
                    "gain / N0; pow4da = + --newton Newton steps on the UW's DA Lambda from it (the NDA f picks the DA "
                    "lobe); costed by da_sync.nda_cost; off (default) = the DA periodogram, unchanged")
    ap.add_argument("--n0", default="est", choices=["est", "genie"])
    ap.add_argument("--cfo-max", type=float, default=DA.CFO_MAX)
    ap.add_argument("--algo", default="maxlog", choices=["maxlog", "logmap"])
    ap.add_argument("--iters", type=int, default=8)
    ap.add_argument("--sf", default=None, help="rcs2 extrinsic scaling (default 'adaptive', as run_rcs2)")
    ap.add_argument("--sf-low-iters", type=int, default=None)
    ap.add_argument("--itl", default=tdb.INTERLEAVER_DIR, choices=list(tdb.INTERLEAVER_DIRS))
    ap.add_argument("--exact-demap", action="store_true")
    ap.add_argument("--scale", type=float, default=None, help="vde extrinsic scale (default 0.75 max-log)")
    ap.add_argument("--early-stop", dest="early_stop", action="store_const", const=True, default=None,
                    help="CRC early stop (default on for every system; rcs2 from 2026-11-19, the final rcs2 parts "
                         "before ran --no-early-stop as run_rcs2)")
    ap.add_argument("--no-early-stop", dest="early_stop", action="store_const", const=False)
    ap.add_argument("--es-crc-start", type=int, default=1,
                    help="rcs2 early stop: first iteration with a CRC check (1 = after every iteration, the standard "
                         "from 2026-11-19; 2 = AFF3CT --dec-crc-start, the rcs2.rx default)")
    ap.add_argument("--es-crc-cost", action=argparse.BooleanOptionalAction, default=True,
                    help="rcs2 early stop: charge the per-iteration CRC checks (turbo_db.macs crc_ops)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--dump", action="store_true", help="per-packet records da_<part>_p<i>.npz")
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--check", nargs=2, metavar=("A.json", "B.json"),
                    help="smoke: assert equal frames + frame-error packets (da_ / rcs2_ / vde_ results files)")
    a = ap.parse_args()
    if a.selfcheck:
        sys.exit(0 if selfcheck() else 1)
    if a.check:
        sys.exit(0 if check(*a.check) else 1)
    if not (a.sys and a.snrs and a.part):
        ap.error("give --sys, --snrs and --part (or --selfcheck)")
    if a.nda != "off" and (a.sys != "rcs2" or a.variant not in ("standard", "genie", "ideal")):
        ap.error("--nda: --sys rcs2 with --variant standard (genie / ideal ignore it)")
    if a.early_stop is None:
        a.early_stop = True                                             # rcs2 too from 2026-11-19 (was vde, nbiot)
    sf = tdb.SF_DEFAULT if a.sf is None else (a.sf if a.sf == "adaptive" else float(a.sf))
    o = dict(vars(a), sf=sf, seed=a.seed + a.calib_seed_offset, seed_arg=a.seed)   # rng seed = seed + offset
    o.pop("selfcheck")
    o.pop("check")
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, f"da_{a.part}.json")
    prog = os.path.join(RESULTS, f"da_{a.part}.prog")
    if os.path.exists(path):
        sys.exit(f"{path} exists: use a new --part")
    _init(o)
    S = _S["sys"]
    doc = dict(meta=meta_doc(S, o), points=[])
    print(f"run_fullsys_da {o}", flush=True)
    t0 = time.time()
    for pi, esn0 in enumerate(a.snrs):
        acc, dumps = run_point(o, esn0, pi, len(a.snrs), t0, prog)
        p = point_doc(S, o, esn0, acc)
        doc["points"].append(p)
        with open(path + ".tmp", "w") as fh:
            json.dump(doc, fh, indent=1)
        os.replace(path + ".tmp", path)
        if dumps:
            dp = os.path.join(RESULTS, f"da_{a.part}_p{pi}.npz")
            if not os.path.exists(dp):
                np.savez_compressed(dp, esn0=esn0, **{k: np.concatenate([d[k] for d in dumps]) for k in dumps[0]})
        with open(prog, "w") as fh:
            fh.write(f"{pi + 1} {len(a.snrs)} {time.time() - t0:.0f}\n")
        st = p["stages"]
        sid = {"rcs2": a.wf, "nbiot": a.nbfmt}.get(a.sys, a.link)
        print(f"SNR {esn0:+.2f} dB | {S.name} {sid} {a.variant} | frames {p['frames']}"
              f" | err {p['frame_err']} (und {p['undetected']}) | PER {p['per']:.3e} | outl1 "
              f"{p['outlier_rate_rank1']:.2e} | rms f_err {p['rms_ferr_inliers']:.2e} (sqrt CRB {p['sqrt_crb_f']:.2e})"
              f" | N0 {p['n0db_mean']:+.2f} dB | rank_ok {p['rank_ok']} | reach {st['reach']} | ops "
              f"{p['ops_mean'] / 1e6:.3f} M crit {p['crit_mean'] / 1e3:.1f} k | {p['time_s']:.0f} s", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
