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
Decoders as run_rcs2 (max-log, 8 it, ADAPTIVE sf, no early stop, aff3ct interleaver) / run_vde (max-log x 0.75 or
--algo logmap, 8 it, CRC early stop).

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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import txrx_chain                                                  # noqa: E402
from fullsys import da_sync as DA                                  # noqa: E402
from fullsys import rcs2, turbo_db as tdb                          # noqa: E402
from fullsys import costmodel                                      # noqa: E402
from fullsys.run_rcs2 import wf_code                               # noqa: E402  (the rcs2 seed sequence)
from fullsys.vde import VDELink                                    # noqa: E402

RESULTS = os.path.join(ROOT, "fullsys", "results")
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
                      early_stop=o["early_stop"], exact_demap=o["exact_demap"], sf_low_iters=o["sf_low_iters"])
        it = np.asarray(out["iters"])
        m = tdb.macs(wf.code.N, it, o["algo"], o["early_stop"], n_sym=wf.n_data, bps=wf.m, crc=wf.crc)
        tot = np.broadcast_to(np.asarray(m["total"], float), it.shape)
        crit = np.broadcast_to(np.asarray(m["crit"], float), it.shape)
        return out["pdu"], out["crc"], it, np.asarray(out["first_pass"]), tot, crit


class VDESys:
    name = "vde"

    def __init__(self, o):
        self.o = o
        lid = int(o["link"]) if str(o["link"]).isdigit() else o["link"]
        self.L = L = VDELink(lid)
        self.lay = DA.vde_layout(L, o["cfo_max"])
        self.g = float(np.sum(txrx_chain.rrc(L.beta) ** 2))         # run_vde._init normalisation
        self.n_data, self.sf = len(L.data_pos), L.sf
        # costmodel.frontend_ops without its chip-rate de-rotation (4 / chip: the DA correction de-rotates at the
        # symbol rate, in da_ops): despreading 2 / chip, once per burst; LLR scaling 1 / channel bit per decode attempt
        self.front = float(costmodel.frontend_ops(L.n_sym, L.sf, 0, L.mod) - 4 * L.n_el)
        self.front_crit = float(costmodel.frontend_crit(L.n_sym, L.sf, 0, L.mod) - np.ceil(4 * L.n_el / KP))
        self.llr, self.llr_crit = float(L.n_chan), float(np.ceil(L.n_chan / KP))
        self.batch = o["batch"] or int(np.clip(4e5 // L.n_el, 1, 64))      # run_vde auto batch
        _costs(self, o)

    def rngs(self, seed, esn0, c):
        ent = [seed, int(round(100 * (esn0 + 50))), c]                   # = run_vde._chunk
        return np.random.default_rng(ent), np.random.default_rng(ent + [1])

    def draw(self, rng, B):
        pay = rng.integers(0, 2, (B, self.L.kpay), dtype=np.int8)
        return pay, self.L.tx(pay)[0]

    def snr_el(self, esn0):
        return esn0 - 10 * np.log10(self.sf)

    def channel(self, x, f, ph, esn0, rng):
        r = txrx_chain.transmit(x, f / self.sf, ph, self.snr_el(esn0), rng, beta=self.L.beta) / self.g
        return self.L.despread(r)                                        # chip-level despreading first

    def g_true(self, f, ph):
        fc = f / self.sf
        D = np.exp(2j * np.pi * fc[:, None] * np.arange(self.sf)[None]).mean(1)   # despreading gain / phase
        return np.exp(1j * (ph + 2 * np.pi * fc * DELAY)) * D

    def n0_true(self, esn0):
        return 10 ** (-self.snr_el(esn0) / 10) / self.sf

    def ideal(self, y, esn0):
        return y, self.n0_true(esn0)                                     # exactly run_vde (N0_el / sf)

    def decide(self, y):
        return np.where(y.real >= 0, 1.0, -1.0).astype(complex)

    def decode(self, y, n0):
        o, L = self.o, self.L
        n0 = n0 if np.ndim(n0) == 0 else np.asarray(n0)[:, None]
        out = L.decode_llr(L.data_llr(y, n0), o["iters"], o["algo"], o["scale"], o["early_stop"])
        it = out["iters"].max(1)
        first = np.where(out["crc_ok"], it, 0)                          # early stop from iteration 1: first pass
        return (out["payload"], out["crc_ok"], it, first, np.asarray(out["ops"], float) + self.llr,
                np.asarray(out["ops_crit"], float) + self.llr_crit)       # costmodel.turbo_ops / crit_turbo


def _costs(S, o):
    """Synchroniser costs of S.lay: 'lean' (the competitor cost reported) and 'upper' (what runs: o['refine'] maxima,
    nfft >= 4 span), da_sync.cost -> costmodel.da_ops / da_crit."""
    S.cost_lean = DA.cost(S.lay, S.n_data, "lean", newton=o["newton"])
    S.cost_up = DA.cost(S.lay, S.n_data, "upper", refine=o["refine"], newton=o["newton"])


class NBLayout:
    """DA layout facade of an NB-IoT burst for simulate / summarise / point_doc: pos = TRUE DM-RS times (symbol
    durations, guard + gaps included; pos.mean() = the phase-error centre), FFT / search values of the comb lay_v."""

    def __init__(self, t, ks, L, T, lay_v, P, name):
        self.pos, self.ks = np.asarray(t, float), np.asarray(ks, complex)
        self.L, self.Nk, self.name, self.T = int(L), len(self.pos), name, float(T)
        self.span = float(self.pos.max() - self.pos.min() + 1)
        self.nfft, self.n_win, self.fwin = lay_v.nfft, lay_v.n_win, lay_v.fwin / P

    def crb(self, snr_db):
        return DA.C4.crb_known(snr_db, self.pos)                       # true times (float positions)

    def outlier_thr(self):
        return 0.5 / self.T                                            # 1 / (2 burst duration)


class NBSys:
    """3GPP IoT-NTN NB-IoT NPUSCH format 1, single tone 3.75 kHz (fullsys/nbiot.py), --nbfmt. The DA estimator runs on
    the DM-RS comb index s' (uniform in time: period P = 80/11 symbols, the 40 ms gap = 20 empty comb slots) through
    da_sync.estimate on a comb Layout with cfo_max P, then f = f_comb / P, g = g_comb e^{-j 2 pi f t0}; the correction
    de-rotates at the true symbol times t_n (S.correct). Channel: exp(j 2 pi f (t_n - n)) applied to the symbols, then
    txrx_chain.transmit (RRC nbiot.ROLLOFF) / MF gain. Decoder: LTE turbo (turbo_lte, max-log x --scale (0.75) or
    log-MAP, CRC-24A early stop), ops costmodel.turbo_ops / crit_turbo + LLR scaling (+ repetition sums)."""
    name = "nbiot"

    def __init__(self, o):
        from fullsys import nbiot
        self.o, self.nb = o, nbiot
        self.fmt = o.get("nbfmt") or "nb328"
        self.L = L = nbiot.NPUSCH(self.fmt)
        assert o.get("dd_iters", 0) == 0, "nbiot: decision-directed refinement not implemented (--dd-iters 0)"
        self.g = float(np.sum(txrx_chain.rrc(nbiot.ROLLOFF) ** 2))      # MF peak gain (unit-gain normalisation)
        self.n_data, self.sf = L.n_data, 1
        self.front, self.front_crit = 0.0, 0.0                          # de-rotation is in da_ops 'correct'
        self.llr, self.llr_crit = L.llr_ops(), float(np.ceil(L.llr_ops() / KP))
        self.batch = o["batch"] or 200                                  # = run_polar_genie --batch (payload pairing)
        self.dt = L.t - np.arange(L.n_sym)                              # guard / gap delay of symbol n
        T = L.t[-1] + 1
        if L.code_only:                                                 # bookkeeping layout only (no DM-RS)
            assert o["variant"] in ("ideal", "genie"), f"{self.fmt} is code-only: variant ideal / genie"
            pos, ks, self.P, self.t0 = np.array([0, L.n_sym - 1]), np.ones(2, complex), 1.0, 0.0
        else:
            self.P, self.t0 = nbiot.SLOT_T, float(L.t[L.dmrs_pos[0]])
            pos = np.round((L.t[L.dmrs_pos] - self.t0) / self.P).astype(np.int64)   # comb index s'
            ks = L.dmrs
        self.lay_v = DA.Layout(pos, ks, int(pos.max()) + 1, cfo_max=o["cfo_max"] * self.P, name=f"nbiot-{self.fmt}-comb")
        tk = self.t0 + self.P * pos
        self.lay = NBLayout(tk, ks, L.n_sym, T, self.lay_v, self.P, f"nbiot-{self.fmt}")
        self.cost_lean = DA.cost(self.lay_v, self.n_data, "lean", newton=o["newton"])
        self.cost_up = DA.cost(self.lay_v, self.n_data, "upper", refine=o["refine"], newton=o["newton"])

    def rngs(self, seed, esn0, c):
        ent = [seed, self.nb.FORMATS[self.fmt]["tag"], int(round(esn0 * 1000)) + 100000, c]   # = run_polar_genie
        return (np.random.default_rng(np.random.SeedSequence(ent)),
                np.random.default_rng(np.random.SeedSequence(ent + [1])))

    def draw(self, rng, B):
        pay = rng.integers(0, 2, (B, self.L.A)).astype(np.int8)        # drawn first, as run_polar_genie's data
        return pay, self.L.tx(pay)[0]

    def channel(self, s, f, ph, esn0, rng):
        x = s * np.exp(2j * np.pi * np.asarray(f, float)[:, None] * self.dt[None])
        return txrx_chain.transmit(x, f, ph, esn0, rng, beta=self.nb.ROLLOFF) / self.g

    def g_true(self, f, ph):
        return np.exp(1j * (ph + 2 * np.pi * f * DELAY))               # r_n = g e^{j 2 pi f t_n} s_n

    def n0_true(self, esn0):
        return 10 ** (-esn0 / 10)

    def ideal(self, r, esn0):
        return r, self.n0_true(esn0)

    def estimate(self, r, n_cand=1, refine=DA.REFINE, iters=DA.NEWTON):
        """da_sync.estimate on the DM-RS comb -> the same dict, f per symbol, g at t = 0."""
        lv = self.lay_v
        rv = np.zeros((len(r), lv.L), complex)
        rv[:, lv.pos] = r[:, self.L.dmrs_pos]
        e = DA.estimate(rv, lv, n_cand=n_cand, refine=refine, iters=iters)
        f = e["f"] / self.P
        return dict(e, f=f, g=e["g"] * np.exp(-2j * np.pi * f * self.t0))

    def correct(self, r, f, g):
        """y_n = r_n e^{-j 2 pi f t_n} / g at the true symbol times."""
        return r * np.exp(-2j * np.pi * np.asarray(f)[:, None] * self.L.t[None]) / np.asarray(g)[:, None]

    def decode(self, y, n0):
        o, L = self.o, self.L
        n0 = n0 if np.ndim(n0) == 0 else np.asarray(n0)[:, None]
        out = L.rx(y, n0, o["iters"], o["algo"], o["scale"], o["early_stop"])
        return (out["payload"], out["crc_ok"], out["iters"], out["first"], out["ops"] + self.llr,
                out["ops_crit"] + self.llr_crit)

    def point_extra(self, esn0):
        L = self.L
        eb = float(L.ebn0_db(esn0))
        return dict(ebn0_payload=eb, ebn0_payload_cp=float(L.ebn0_db(esn0, cp=True)),
                    ebn0_data=float(L.ebn0_db(esn0, charge="data")), L_burst=L.n_sym, k=L.A, K=L.K, E=L.E,
                    nbfmt=self.fmt, ref_aff3ct_fer=self.nb.REF_AFF3CT.get(round(eb, 2)) if L.code_only else None)

    def meta(self):
        lv = self.lay_v
        return dict(nbiot=self.L.summary(), assumptions=self.nb.ASSUMPTIONS, rolloff=self.nb.ROLLOFF,
                    comb=dict(P=self.P, t0=self.t0, Nk=lv.Nk, span=lv.span, L=lv.L, nfft=lv.nfft, fwin=lv.fwin,
                              n_win=lv.n_win, alias_per_symbol=1.0 / (2 * self.P)),
                    ref_aff3ct=({str(k): v for k, v in self.nb.REF_AFF3CT.items()} if self.L.code_only else None))


SYSTEMS = {"rcs2": RCS2Sys, "vde": VDESys, "nbiot": NBSys}
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
        if hasattr(S, "estimate"):                                      # system hook (nbiot: DA on the DM-RS comb)
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
        p.update(ebn0_burst=round(float(S.wf.ebn0(esn0)), 4), L_burst=S.wf.L, k=S.wf.k,
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
             da=dict(MARGIN=DA.MARGIN, DEDUP=DA.DEDUP, KP=KP),
             edges=dict(ferr_fine_over_thr=FERR_FINE.tolist(), ferr_coarse=FERR_COARSE.tolist(),
                        pherr=PH_EDGES.tolist(), n0db=N0_EDGES.tolist()),
             stages="index 0 = estimation (+ despreading for VDE), m = decode attempt m (candidate rank m)",
             cost="ops / crit (MACs per core) = the LEAN synchroniser (costmodel.da_ops / da_crit: 1 maximum refined, "
                  "nfft >= 2 span; + refine_one + per_cand per further candidate) + front end + decoder; *_upper = "
                  "the synchroniser that runs (refine maxima, nfft >= 4 span). Decoder: rcs2 turbo_db.macs (duo-binary "
                  "16-state, not in costmodel's binary SISO), vde decode_llr ops / ops_crit (costmodel.turbo_ops / "
                  "crit_turbo) + LLR scaling; vde front end costmodel.frontend_ops / crit minus the chip-rate "
                  "de-rotation (despreading). dd_iters > 0 is not costed.",
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
    cases = [("rcs2", dict(wf="13")), ("rcs2", dict(wf="42")), ("vde", dict(link="32")),
             ("nbiot", dict(nbfmt="nb328")), ("nbiot", dict(nbfmt="nb1000r10"))]
    ok_all = True
    for name, extra in cases:
        S = None
        for var, m in (("standard", 1), ("strong", DA.TOP_M), ("genie", 1), ("ideal", 1)):
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
                             ("rcs2", dict(wf="14"), 1.49), ("rcs2", dict(wf="42"), -3.81),
                             ("vde", dict(link="32"), -4.5)]:
        lay = (DA.rcs2_layout(rcs2.Waveform(rcs2.wf_key(extra["wf"]))) if name == "rcs2"
               else DA.vde_layout(VDELink(32)))
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
    ap.add_argument("--wf", default="13", help="rcs2 waveform ID: 3 13 14 42")
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
                    help="CRC early stop (default: off for rcs2 as run_rcs2, on for vde as run_vde)")
    ap.add_argument("--no-early-stop", dest="early_stop", action="store_const", const=False)
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
    if a.early_stop is None:
        a.early_stop = a.sys in ("vde", "nbiot")
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
