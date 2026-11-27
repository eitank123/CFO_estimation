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
        testing_s11g (0.15 = the 1/10 settings), id2 -> base25_qfix_fzs (2/5), id5 / id5p -> the PROVISIONAL 2/3
        profile (PROF_RX: base2_qfix_fzs's 1/2 settings + PROF_SPS kstep 2), + the format hooks: nopi (shortened id14s: 4 pi/2 branches),
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
Early give-up: --sps '{"giveup": {"stat": "psn", "thr": 0.9, "after": "final"}}' (small_rx giveup; a list of tests
allowed): per point giveup / giveup_pts (per GU_PTS point); a given-up packet is out 2 like a capped one (so it is in
cap_frames / cap_idx too). --dump writes the giveup statistics per packet (GU_KEYS) whatever the setting: tune them
offline with fullsys/tune_giveup.py.
--charge-all (default off = the old count): small_rx ck_charge_all, the checkpoint NN's partial decodes of the cells
outside the current round (2/5 first_k 32, 0.15 batches of 32) charged when the NN runs (macs + crit_par); decisions and
BLER identical, only the MACs change (meta charge_all; st ck_extra_cells / macs_ck_extra). fullsys/recharge.py bounds
the correction of the runs without it.
--twin rep:<rule><t>[p]:<place> (2026-11-23, id13 / id3; 2026-11-24 + id14s / id5 shorten, id2): a repetition twin
(blind_fmt rep, sync_cfo/fs/rep_twin.py): the (E - t, K) code + t coded bits sent twice on diagonal symbols; tx = F.encode_rep, rx MRC in F.llrs (MAC llr + t),
re-encoding over the extended word; meta rep_twin; --selfcheck-rep checks the conventions and 3 packets at 30 dB.
--selfcheck --fmt <f> --twin <moved-bit design> (2026-11-24): only that format's base check and its twin (not TW_CHECK).
--twin pil:<n_p>:<place> (2026-11-24, equal-overhead pilot test, id13 / id3): the rep arm's budget t = 2 n_p as n_p known
pilot symbols (blind_fmt pil: the plain (E - t, K) code, pilots at rep_twin.place); tx = F.encode_pil, the decoder gets
no pilot LLRs; --pil-fe jt|pl = small_rx pl_fe (pilot line + 4th-power line / pilots alone), --sps pl_ph / pl_parab
(pilot_fe.py); meta pilots; --selfcheck-pil checks the conventions and 3 packets at 30 dB.
--chunks c1 c2 ... (2026-11-24, D4b replay; default None = chunks 0, 1, ...): only these chunk indices of each point (the
same packets as the full run's chunks: entropy keyed by the chunk index), in the given order; no early stop by max-err.
--genie (2026-11-24, D1 of sync_cfo/expected_fs.md; default off = the blind receiver): the same packets (tx_packets, paired bit for
bit with the blind run at the same --seed / --batch / point / chunk) decoded once at genie sync (genie_chunk): CRC-only,
CRC + rho table and oracle-rho counters, per packet gn_*.npz with --dump; D_acc from it is an upper bound.

Cost: blind_vp.MAC scaled to N / n_sym / E (blind_fmt), unit env BLIND_MAC_UNIT (ops default from 2026-11-19 = the
competitors' fullsys/costmodel ops; legacy = the earlier parts; meta mac_unit; decisions identical in both), per-point
st cc_* = small_rx's per-component counters (re-pricing: BLIND_IMPLEMENTATION/testing/reprice_ops.py); MACs per core = crit_par (32 cores, scheduled): the standard
model is crit_par_h_d4a at the 0.15 profile, crit_par_d4a at 2/5, 1/2 (BLIND_IMPLEMENTATION/07_complexity.md); both
are recorded per packet (histograms split right / wrong / failed) and per stage (stage_acc).

    BLIND_STUDY=small_cfo python fullsys/run_blind_fs.py --fmt id13 --snrs -0.6 -0.2 --frames 20000 --part fs-bl13
    BLIND_STUDY=small_cfo python fullsys/run_blind_fs.py --selfcheck       # 3 packets at 30 dB per format (no BLER)

Writes fullsys/results/blind_fs_<part>.json (rewritten after every point; refuses an existing part), .prog ("done total
elapsed_s"), and with --dump compact per-packet records + small_rx's decode / fz rows per chunk in
fullsys/results/blind_fs_<part>_dump/. --dump-lite (2026-11-25, default off): only pk_*.npz with the fields the joint
tuner reads (right, fe, the std per-core cost, GU_KEYS), no rows / decode dumps (~1/100 of --dump); decisions, MACs
and the JSON unchanged. --lite-ops (2026-11-25, H1; default off): --dump-lite + passed, stage, f, f0 and the four
per-packet cost columns (macs, cpar, c_d4a, c_hd4a). With --sps h1 (small_rx H1) the pk_*.npz of --dump / --dump-lite
also hold the h1_* fields (small_rx.H1_KEYS). Run on the cluster only.
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))  # (package) run/
ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "blind"), os.path.join(ROOT, "dvbrcs2")]

import run_polar_genie as pg                        # noqa: E402  (FMTS, modulate, the seed scheme)
import txrx_chain                                   # noqa: E402

RESULTS = os.path.join(HERE, "results")
CALIB_TAG = 500000                                  # --calib: seed tag offset (disjoint from every reported run)
# per format: rate profile (receiver settings / RHO_N key) and the adopted receiver (testing/run.py VARIANTS key)
BL = {"id13": ("2/5", "base25_qfix_fzs"), "id14s": ("1/2", "base2_qfix_fzs"), "id14p": ("1/2", "base2_qfix_fzs"),
      "id3": ("2/5", "base25_qfix_fzs"), "id42b": ("2/5", "base25_qfix_fzs"), "id42q": ("2/5", "base25_qfix_fzs"),
      "vde32": ("0.15", "testing_s11g"),
      "id2": ("2/5", "base25_qfix_fzs"), "id5": ("2/3", "base2_qfix_fzs"), "id5p": ("2/3", "base2_qfix_fzs"),
      "pc1024": ("2/5", "base25_qfix_fzs")}         # (2026-11-26) R 1/3 own format: the 2/5 profile, as id3
STD_CORE = {"0.15": "c_hd4a", "2/5": "c_d4a", "1/2": "c_d4a", "2/3": "c_d4a"}   # the standard MACs per core of the profile
# (2026-11-23, id5 / id5p) a format profile without its own small_rx tuning: small_rx runs the settings of PROF_RX[prof]
# (sps rate = that key: every per-rate dict, FZS_T, ck_nn c, nph resolve there) + PROF_SPS[prof] (before --sps).
# PROVISIONAL 2/3: the 1/2 settings (c 2 = 3/16 checkpoint NN, z-test tau / kmin / win, final, phase rules) with the
# grid step fixed at 2 STEP (bf.grid_step('2/3') = 2 at every SNR; '1/2' gives 4 from 4 dB, too wide a basin at 2/3)
PROF_RX = {"2/3": "1/2"}
PROF_SPS = {"2/3": {"kstep": 2}}
# --rho fmt: per-format re-encoding tables (SNR dB, rho_n) for small_rx rho_n, calibrated on --calib parts
# (fullsys/rho_calib_fs.py); a (fmt, crc) without an entry is refused. Empty until the fs-r2cal / fs-r5cal parts are in
RHO_FS = {("id2", 16): ((-0.25, 0.87), (0.5, 0.858), (1.25, 0.82)),       # fs-r2cal-{l8,l16,min}-{m025,p050,p125}
          ("id5", 32): ((3.25, 0.863), (4.0, 0.863), (4.75, 0.863))}     # fs-r5cal-*: CRC-32, 0 wrong passes -> keep scaled
# (2026-11-24, PROVISIONAL, the twin arms at CRC-24) the CRC-16 / CRC-32 tables carried over, not recalibrated: rho_n of a
# right pass does not depend on the CRC; CRC-24 lets 2^-8 x the wrong passes of CRC-16 through (id2: the table stays
# conservative) and 2^8 x those of CRC-32 (id5: 0 wrong in 180k at CRC-32, rho_n of the logged wrong passes to be checked)
RHO_FS[("id2", 24)] = RHO_FS[("id2", 16)]
RHO_FS[("id5", 24)] = RHO_FS[("id5", 32)]
# (2026-11-23) id2 1.25 dB: 0.82 instead of the midway 0.851 (which rejects ~7e-4 right passes = a floor at the 1e-3
# target); 0.82 rejects ~1e-4 right and passes one 0.842 wrong outlier in 60k (1.7e-5 per frame). id5: no wrong pass
# in 180k frames, right min 0.954 -> the scaled table (no tightening; CRC-32 false accepts ~2^-32 per pass).
GU_PTS = ("fast", "grid", "s2", "final", "post")    # = small_rx.GU_PTS (giveup points; --sps '{"giveup": ...}')
GU_KEYS = ("gu_z", "gu_pnn", "gu_psn", "gu_rho", "gu_cost", "gu_pt")   # small_rx stage_acc giveup stats (--dump)
TW_KEYS = ("tw_llz", "tw_y2z", "tw_phz", "tw_dth", "tw_bt", "tw_bs", "tw_use")   # small_rx stage_acc twin stats (tw_fe)
# --cknn fmt on a profile whose receiver has no checkpoint NN: its checkpoint CK_FR[c] (0.15: c 3 = 1/4, as 2/5;
# --ck-c overrides it on every profile); the 2/5, 1/2 profiles keep their own (c 3 = 1/4, c 2 = 3/16)
CK_C = {"0.15": 3}
TW_CHECK = {"id13": "search:k12:rd", "id3": "search:k12:rd", "id14s": "search:k12:rd"}   # --selfcheck twin designs
REP_CHECK = {"id13": "rep:gr96:ea", "id3": "rep:gr128:ea"}   # --selfcheck-rep repetition twins (2026-11-23)
REP_FMTS = ("id13", "id3", "id14s", "id5", "id2")   # --twin rep:...: rep_twin.RX_FMTS (2026-11-24: + id14s / id5
#                                                     shorten, id2 puncture t <= 47)
REP_SPEC = r"^rep:(gr|pnc|rnd|wst)(\d+)(p?):(rd|us|ea|ex)$"   # rep:<rule><t>[p]:<place> (rep_twin RULES / PLACES)
# (2026-11-24 equal-overhead pilot test) --twin pil:<n_p>:<place>: n_p known pilot symbols on the plain (E - 2 n_p) code
PIL_SPEC = r"^pil:(\d+):(rd|us|ea|ex)$"
PIL_FMTS = ("id13", "id3")                          # (blind_fmt pil accepts rep_twin.RX_FMTS; run on these two)
PIL_CHECK = {"id13": "pil:48:ea", "id3": "pil:48:ea"}   # --selfcheck-pil designs
PL_KEYS = ("pl_llz", "pl_lz", "pl_phz", "pl_dth", "pl_br")   # small_rx stage_acc pilot stats (pl_fe / pl_ph)
# (2026-11-24, --sps '{"pk_log": true}') small_rx pk_log: the stage-1 candidate list of tw_fe jt (tw_*) / pl_fe (pl_*)
PK_KEYS = tuple(f"{a_}_{k_}" for a_, ks_ in (("tw", ("tw", "lc")), ("pl", ("pl",))) for k_ in (
    "pk_f", "pk_ll", "ll_true", "rank_true", "pk_y4", "y4_true",
    *(x_ for c_ in ks_ + ("lcq",) for x_ in (f"pk_{c_}", f"{c_}_true"))))
# (2026-11-24, D2) pk_log tw: the complex lines at the top peaks / the truth (small_rx pk_lines: Y4 all symbols, Y4 with
# the twins masked, Y2 of the twins)
PK_KEYS += tuple(f"tw_{x_}" for c_ in ("y4c", "y4nc", "y2c") for x_ in (f"pk_{c_}", f"{c_}_true"))
# (2026-11-24, D3) sps pk_w4: the weight-4 dual-check scores at the same peaks / the truth (small_rx w4_scores)
PK_KEYS += tuple(f"tw_{x_}" for c_ in ("w4s", "w4l", "w4b", "w4v") for x_ in (f"pk_{c_}", f"{c_}_true")) + ("tw_w4_npa",)
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
    tw = o.get("twin")                                  # (--twin) None = the baseline format
    L = o.get("L", pg.L_LIST)                           # (--list) CA-SCL list size; default 8 = the baseline
    key = (fmt, o["crc"], L, o["beta"], o["cfo_max"], o["extra_in_fz"], o["chan"], o["design"], dsnr) + \
        ((tw,) if tw is not None else ())
    if key not in _F:
        from blind_fmt import BlindFormat
        f = pg.FMTS[fmt]
        F = BlindFormat(fmt, f["A"], f["E"], f["mod"], mode=f["mode"] if f["force"] else None, crc=o["crc"],
                        L=L, beta=o["beta"], cfo_max=o["cfo_max"], extra_in_fz=o["extra_in_fz"],
                        chan_intlv=o["chan"], design=o["design"], design_snr=dsnr,
                        **({"twin": tw} if tw is not None else {}))
        assert F.mode == f["mode"], (fmt, F.mode, f["mode"])
        _F[key] = F
    return _F[key]


def _testing_run():
    """BLIND_IMPLEMENTATION/testing/run.py as a module (its BASE / VARIANTS / FZS_T)."""
    if "m" not in _RX:
        p = os.path.join(ROOT, "blind", "testing_run.py")
        sp = importlib.util.spec_from_file_location("bl_testing_run", p)
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        _RX["m"] = m
    return _RX["m"]


def ck_index(sps, prof):
    """The checkpoint index c (CK_FR[c]) of an sps's checkpoint NN at the profile, as small_rx resolves it (None: off)."""
    import blind_cfo as bc
    c = sps.get("ck_nn")
    rk = PROF_RX.get(prof, prof)                                      # (2/3: the 1/2 settings; else prof itself)
    return c.get(bc.PROFILE.get(rk, rk)) if isinstance(c, dict) else c


def rx_spec(fmt, F, o, rx_key=None):
    """small_rx spec of the format: the adopted receiver's sps flags + the format hooks + the provisional settings."""
    import blind_ber as bb
    tr = _testing_run()
    prof, key0 = BL[fmt]
    base, flags = tr.VARIANTS[rx_key or key0]
    sps = {**bb.RX[tr.BASE[base]]["sps"], **flags}
    assert sps.get("pns") is None and not sps.get("pilots"), "pns / pilots: not supported on the formats"
    sps["rate"] = PROF_RX.get(prof, prof)                             # (2/3: runs the 1/2 settings, PROF_RX)
    sps.update(PROF_SPS.get(prof, {}))
    rk = pg.FMTS[fmt]["rho_key"]
    if o["rho"] == "fmt":                                             # the format's calibrated table (RHO_FS)
        if (fmt, o["crc"]) not in RHO_FS:
            raise ValueError(f"--rho fmt: no RHO_FS table for ({fmt}, crc {o['crc']}) (calibrate: rho_calib_fs.py)")
        sps["rho_n"] = tuple(RHO_FS[(fmt, o["crc"])])
    else:
        sps["rho_n"] = (F.rho_table(rk) if o["rho"] == "scaled" else tuple(bb.RHO_N[rk]) if o["rho"] == "table"
                        else None)
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
        pk = bc.PROFILE.get(sps["rate"], sps["rate"])                 # small_rx resolves PER_RATE on this key (0.15: 1/10)
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
    if getattr(F, "pil", None) is not None:                           # (pil) [e1, pilot bits] -> the pilot frame
        e = F.encode_pil(d.astype(np.uint8))[:, F.chan]
    else:
        e = (F.rmc.encode_rm(d.astype(np.uint8)) if getattr(F, "rep", None) is None   # chan: the channel interleaver
             else F.encode_rep(d.astype(np.uint8)))[:, F.chan]       # (QPSK); (rep twin) the extended E bits
    s = pg.modulate(e if getattr(F, "tw_pn", None) is None else e ^ F.tw_pn[None], fmt)   # (--twin) scrambler
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


def genie_chunk(task):
    """(--genie, 2026-11-24 D1 arms 1 / 2 / 6 of sync_cfo/expected_fs.md) One chunk of the SAME packets as run_chunk (tx_packets:
    data, noise, CFO, phase bit for bit at the same --seed / --batch / point / chunk), decoded ONCE at genie sync: the
    receiver's pre-MF correction at the true f (bf.premf), bc.llrs at (true f, true centre phase th), the format's
    decoder F.code (CA-SCL-L, --list; no fzstop, no CA retry, no search). Per packet: the decoded word's CRC, right,
    rho of the decoded word and of the TRUE word (bf.reencode_rho at the true f on the premf symbols = decode()'s rho
    and normaliser), true word in the decoder list (as small_rx in_list). Online counters: CRC-only (arm 1), CRC + the
    run's rho_n table (arm 2: thr = decode()'s max(rho_min, RHO_N sqrt(s / (1 + s))), accept rho > thr), oracle rho
    (arm 6: the true word below thr); everything else is offline from the dump (gn_<tag>.npz). D_acc from arm 2 - arm 1
    is an UPPER BOUND (no fallback search after a rho rejection). No MACs (sums 0)."""
    fmt, esn0, entropy, batch, o, cidx = task
    import blind_cfo as bc
    import blind_fast as bf
    F = get_fmt(fmt, o)
    sps, _ = rx_spec(fmt, F, o, o.get("rx"))
    A = pg.FMTS[fmt]["A"]
    d, f, th, v, rx = tx_packets(fmt, F, esn0, entropy, batch, o)
    sigma2 = 1.0 / (2.0 * 10 ** (esn0 / 10))
    truth = d.astype(np.uint8)
    s_ = 10 ** (esn0 / 10)
    sq = np.sqrt(s_ / (1 + s_))
    thr = bf.rho_min(esn0)                                            # = small_rx decode()'s threshold (snr_chk None,
    if sps["rho_n"]:                                                  # re_margin 0)
        thr = max(thr, float(np.interp(esn0, *zip(*sps["rho_n"]))) * sq)
    dh, okc, inl = np.zeros((batch, A), np.uint8), np.zeros(batch, bool), np.zeros(batch, bool)
    rho_d, rho_t = np.zeros(batch), np.zeros(batch)
    t0 = time.time()
    with F:
        code = F.code
        code.fz_stop = None
        for a in range(0, batch, o["sub"]):
            sl = slice(a, min(a + o["sub"], batch))
            rc = bf.premf(v[sl], rx[sl], f[sl])                       # (the receiver decodes premf'd symbols)
            dh[sl], okc[sl], _ = code.decode(bc.llrs(rc, f[sl], th[sl], sigma2), return_info=True)
            n_, Ls_ = code._pm.shape                                  # the list (traceback as small_rx _lst)
            info = np.empty((n_, Ls_, code.K), np.uint8)
            path, rows = np.broadcast_to(np.arange(Ls_), (n_, Ls_)), np.arange(n_)[:, None]
            for k_ in range(code.K - 1, -1, -1):
                info[:, :, k_] = code._bits[k_][rows, path]
                path = code._parents[k_][rows, path]
            inl[sl] = (info[..., :A] == truth[sl][:, None]).all(2).any(1)
            rho_d[sl] = bf.reencode_rho(code, rc, dh[sl], f[sl])
            rho_t[sl] = bf.reencode_rho(code, rc, truth[sl], f[sl])
    right = okc & (dh == truth).all(1)
    wrong = okc & ~right
    acc2 = okc & (rho_d > thr)
    fe1, fe2 = ~right, ~(acc2 & right)                                # arm 1 CRC only, arm 2 CRC + rho
    res = dict(frames=batch, frame_err=int(fe2.sum()), undetected=int((acc2 & wrong).sum()),
               frame_err_crc=int(fe1.sum()), undetected_crc=int(wrong.sum()), crc_fail=int((~okc).sum()),
               right_rej=int((right & ~acc2).sum()), wrong_rej=int((wrong & ~acc2).sum()),
               true_rej=int((rho_t <= thr).sum()), true_rej_right=int((right & (rho_t <= thr)).sum()),
               in_list=int(inl.sum()), fail_in_list=int((~right & inl).sum()), time_rx_s=time.time() - t0,
               passed=int(acc2.sum()), right=int((acc2 & right).sum()), mac_frames=0, out_frames=batch,
               **{f"sum_{k}": 0.0 for k in ("c_hd4a", "c_d4a", "cpar", "macs")},
               **{f"max_{k}": 0.0 for k in ("c_hd4a", "c_d4a", "cpar", "macs")},
               rho_hist={"right": _hist(rho_d[right] / sq, RHO_BINS), "wrong": _hist(rho_d[wrong] / sq, RHO_BINS),
                         "true": _hist(rho_t / sq, RHO_BINS)},
               rho_n_min_right=float((rho_d[right] / sq).min()) if right.any() else None,
               rho_n_max_wrong=float((rho_d[wrong] / sq).max()) if wrong.any() else None,
               rho_n_min_true=float((rho_t / sq).min()), st={}, cap_frames=0, cap_idx=[],
               fe_idx=np.flatnonzero(fe2).tolist(), ud_idx=np.flatnonzero(acc2 & wrong).tolist())
    if o["dump"]:
        os.makedirs(o["dump"], exist_ok=True)
        np.savez_compressed(os.path.join(o["dump"], f"gn_{fmt}_{esn0:+.2f}_c{cidx:05d}.npz"),
                            pk=np.arange(batch, dtype=np.int32), f=f.astype(np.float32), th=th.astype(np.float32),
                            crc=okc, right=right, in_list=inl, rho_d=rho_d.astype(np.float32),
                            rho_t=rho_t.astype(np.float32), thr=thr, sq=sq, esn0=esn0, entropy=np.array(entropy))
    return res


def run_chunk(task):
    """One chunk (= run_polar_genie's chunk c: the same data and noise): blind receiver, counters, histograms."""
    if task[4].get("genie"):                                          # (--genie DEFAULT off) the genie decode instead
        return genie_chunk(task)
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
    S = {k: _cat(sacc, k) for k in ("reach", "cost", "stage", "n_hyp", *GU_KEYS)}
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
        # (measurement, 2026-11-23) CRC passes of the decode attempts: right / wrong, and what the re-encoding check did
        # with them (acc = accepted): crc_pass_wrong = the CRC false passes the rho check must hold (CRC-16 at id2)
        a_ = D["acc"].astype(bool)
        cw_, cr_ = c_ & ~D["right"].astype(bool), c_ & D["right"].astype(bool)
        res["crc_pass_right"], res["crc_pass_right_rej"] = int(cr_.sum()), int((cr_ & ~a_).sum())
        res["crc_pass_wrong"], res["crc_pass_wrong_acc"] = int(cw_.sum()), int((cw_ & a_).sum())
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
                            **{k: S[k] for k in GU_KEYS},                     # (small_rx giveup stats per GU_PTS)
                            **{k: _cat(sacc, k) for k in TW_KEYS if sacc and k in sacc[0]},   # (tw_fe: twin stats)
                            **{k: _cat(sacc, k) for k in PL_KEYS if sacc and k in sacc[0]},   # (pl_fe / pl_ph)
                            **{k: _cat(sacc, k) for k in PK_KEYS if sacc and k in sacc[0]},   # (sps pk_log)
                            **{k: _cat(sacc, k) for k in sr.H1_KEYS if sacc and k in sacc[0]},   # (sps h1)
                            **{k: v_.astype(np.float32) for k, v_ in M.items()}, esn0=esn0, entropy=np.array(entropy),
                            step=step)
        sr.dec_save(dacc, os.path.join(dd, f"rows_{tag}.npz"), fmt=fmt, snr=esn0, chunk=cidx)
        if o.get("fulllog") is not None:                              # (--fulllog) the joint tuner's full-search log
            sr.fl_save(dacc, os.path.join(dd, f"fl_{tag}.npz"), fmt=fmt, snr=esn0, chunk=cidx)
    elif o.get("dump_lite"):                                          # (--dump-lite, measurement) the tuner's fields only
        dd = o["dump_lite"]
        os.makedirs(dd, exist_ok=True)
        ops_ = dict(passed=ok, stage=stg, f=f.astype(np.float32), f0=f0.astype(np.float32),
                    **{k: v_.astype(np.float32) for k, v_ in M.items()}) if o.get("lite_ops") else {}   # (--lite-ops)
        np.savez_compressed(os.path.join(dd, f"pk_{fmt}_{esn0:+.2f}_c{cidx:05d}.npz"), right=right, fe=fe,
                            **{std: M[std].astype(np.float32)}, **{k: S[k] for k in GU_KEYS}, esn0=esn0,
                            **{k: v_ for k, v_ in ops_.items() if k != std},
                            **{k: _cat(sacc, k) for k in small_rx.H1_KEYS if sacc and k in sacc[0]})   # (sps h1)
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
    rp_ = getattr(args, "chunks", None)                              # (--chunks: a replay; other callers: None)
    cl = range(nch) if rp_ is None else list(rp_)
    tasks = ((fmt, esn0, [args.seed, tag, int(round(esn0 * 1000)) + 100000, c],
              min(args.batch, args.frames - c * args.batch), o, c) for c in cl)
    acc, chunks = {}, []
    t0 = tlast = time.time()
    with Pool(args.workers, initializer=_init) as pool:
        for c, res in zip(cl, pool.imap(run_chunk, tasks)):
            chunks.append(dict(c=c, frames=res["frames"], fe_idx=res["fe_idx"], ud_idx=res["ud_idx"],
                               cap_idx=res["cap_idx"]))
            _add(acc, res)
            if time.time() - tlast > 60:
                tlast = time.time()
                print(f"  progress fmt {fmt} Es/N0 {esn0:+.2f}: frames {acc['frames']} err {acc['frame_err']} "
                      f"({time.time() - t0:.0f} s)", flush=True)
                prog(max(acc["frames"] / args.frames, acc["frame_err"] / args.max_err) if rp_ is None
                     else len(chunks) / len(cl))
            if rp_ is None and (acc["frame_err"] >= args.max_err or acc["frames"] >= args.frames):
                break
        pool.terminate()
    acc["time_s"] = round(time.time() - t0, 1)
    acc["chunks"] = chunks
    return acc


def selfcheck(o, only=None):
    """3 packets at 30 dB per format through the whole receiver: all right; the virtual map == the re-encoding map.
    only (2026-11-24: --selfcheck --fmt with a moved-bit --twin): that format's base check and its --twin design (in
    place of TW_CHECK); the base check without the twin and the sps tw_* keys (the twin check adds tw_fe jt itself)."""
    t_all = time.time()
    tw_check = TW_CHECK
    if only is not None:
        tw_check = {only: o["twin"]}
        o = dict(o, twin=None, sps={k: v for k, v in (o.get("sps") or {}).items() if not k.startswith("tw_")} or None)
    for fmt in ([only] if only is not None else pg.FMTS):
        t0 = time.time()
        if fmt.startswith("nb"):                           # NB-IoT formats (nb208 / nb208b): no blind receiver profile
            print(f"  skip {fmt:6s}: NB-IoT, not a blind receiver format", flush=True)
            continue
        if fmt not in BL:                                  # id2 / id5 (2026-11-23): code-only genie formats, no profile yet
            print(f"  skip {fmt:6s}: no blind receiver profile (BL)", flush=True)
            continue
        try:
            F = get_fmt(fmt, o)
        except AssertionError as ex:                       # e.g. nb208: repetition (E > N), no blind format context
            if "repetition" not in str(ex):
                raise
            print(f"  skip {fmt:6s}: {ex}", flush=True)
            continue
        e = np.random.default_rng(0).integers(0, 2, (2, F.E))
        assert np.allclose(F.virtual(pg.modulate(e, fmt)), F.modulate_virtual(e)), fmt
        res = run_chunk((fmt, 30.0, [0, pg.FMTS[fmt]["tag"], 0], 3, o, 0))
        assert res["frame_err"] == 0 and res["right"] == 3, (fmt, {k: res[k] for k in ("frame_err", "right")})
        print(f"  ok  {fmt:6s}: N {F.N} {F.mode:8s} n_sym {F.n_sym} {F.mod} nopi {F.nopi} | MACs/frame "
              f"{res['sum_macs'] / 3:.4g}, per core (d4a) {res['sum_c_d4a'] / 3:.4g} | {time.time() - t0:.1f} s",
              flush=True)
    for fmt, tw in tw_check.items():                       # (--twin) one twin design per QPSK format, tw_fe jt
        t0 = time.time()
        o2 = dict(o, design="ga", design_snr=None, twin=tw, sps={**(o.get("sps") or {}), "tw_fe": "jt"})
        F = get_fmt(fmt, o2)
        d = np.random.default_rng(1).integers(0, 2, (4, F.A)).astype(np.uint8)
        e = F.rmc.encode_rm(d)[:, F.chan]                  # codewords: the +-j fold is exact only on them
        assert np.allclose(F.virtual(pg.modulate(e ^ F.tw_pn[None], fmt)), F.modulate_virtual(e)), (fmt, tw)
        res = run_chunk((fmt, 30.0, [0, pg.FMTS[fmt]["tag"], 0], 3, o2, 0))
        assert res["frame_err"] == 0 and res["right"] == 3, (fmt, tw, {k: res[k] for k in ("frame_err", "right")})
        m = F.tw["meta"]
        print(f"  ok  {fmt:6s} twin {tw}: n_diag {m['n_diag']} moved {m['n_moved']} rot rank {m['rot_rank']} "
              f"UB x{m['ub_ratio']:.2f} | MACs/frame {res['sum_macs'] / 3:.4g}, twin {res['st'].get('cc_t_twin', 0) / 3:.4g}"
              f" | {time.time() - t0:.1f} s", flush=True)
    print(f"SELFCHECK OK ({time.time() - t_all:.1f} s)")


def selfcheck_rep(o):
    """(--selfcheck-rep) Per REP_CHECK design (or --fmt with its --twin rep:...): the conventions on codewords (diagonal
    I == Q, the re-encoding map = the tx bits copies included, virtual == modulate_virtual under the +-j fold, noiseless
    MRC LLRs = 2 on the repeated mother bits, 1 elsewhere, signs right) and 3 packets at 30 dB through the whole
    receiver (tw_fe jt): all right."""
    t_all = time.time()
    chk = {o["fmt"]: o["twin"]} if o.get("fmt") and str(o.get("twin", "")).startswith("rep:") else REP_CHECK
    for fmt, tw in chk.items():
        t0 = time.time()
        o2 = dict(o, design="ga", design_snr=None, twin=tw, sps={**(o.get("sps") or {}), "tw_fe": "jt"})
        F = get_fmt(fmt, o2)
        assert F.rep is not None and F.tw["diag"].size == F.rep_t, (fmt, tw)
        d = np.random.default_rng(1).integers(0, 2, (4, F.A)).astype(np.uint8)
        e = F.encode_rep(d)[:, F.chan]
        x = F.rmc.encode(d)
        dg = F.tw["diag"]
        assert np.array_equal(e[:, 2 * dg], e[:, 2 * dg + 1]), (fmt, tw, "diagonal I != Q")
        assert np.array_equal(e, x[:, F.inter]), (fmt, tw, "re-encoding map != tx bits")
        v = F.virtual(pg.modulate(e ^ F.tw_pn[None], fmt))
        assert np.allclose(v, F.modulate_virtual(e)), (fmt, tw, "virtual != modulate_virtual")
        Lm = F.llrs(v, 1.0)
        rx_ = np.unique(F.pos[F._cp])
        one = np.setdiff1d(np.unique(F.pos), rx_)
        assert np.allclose(np.abs(Lm[:, rx_]), 2.0) and np.allclose(np.abs(Lm[:, one]), 1.0), (fmt, tw, "MRC |LLR|")
        assert np.array_equal(Lm[:, F.pos] < 0, x[:, F.pos] == 1), (fmt, tw, "LLR signs")
        res = run_chunk((fmt, 30.0, [0, pg.FMTS[fmt]["tag"], 0], 3, o2, 0))
        assert res["frame_err"] == 0 and res["right"] == 3, (fmt, tw, {k: res[k] for k in ("frame_err", "right")})
        m = F.tw["meta"]
        print(f"  ok  {fmt:6s} rep {tw}: t {m['t']} E1 {m['E1']} n_diag {m['n_diag']} info moved {m['n_moved']} rot "
              f"rank {m['rot_rank']} UB x{m['ub_ratio']:.2f} | MAC llr {F.mac['llr']:.0f} | MACs/frame "
              f"{res['sum_macs'] / 3:.4g}, twin {res['st'].get('cc_t_twin', 0) / 3:.4g} | {time.time() - t0:.1f} s",
              flush=True)
    print(f"REP SELFCHECK OK ({time.time() - t_all:.1f} s)", flush=True)


def selfcheck_pil(o):
    """(--selfcheck-pil) pilot_fe's synthetic check, then per PIL_CHECK design (or --fmt with its --twin pil:...): the
    pilot positions / values round-trip (tx symbols at F.pil pos = F.pil val, n_p distinct symbols, the rep placement
    rule), no data bit on a pilot slot (chan), the re-encoding map = the tx data bits with the pilots as bits 00 (the
    zero column N of encode and of the padded metric_cw), virtual == modulate_virtual (virtual pilots c0), noiseless
    LLRs |1| on the E - t data mother bits only (signs right, the pilots nowhere), and 3 packets at 30 dB through the
    whole receiver (pl_fe jt, pl_ph iv unless the given --sps sets them): all right."""
    import blind_cfo as bc
    import pilot_fe
    import blind_fmt as bfm
    pilot_fe.selfcheck()
    t_all = time.time()
    chk = {o["fmt"]: o["twin"]} if o.get("fmt") and str(o.get("twin", "")).startswith("pil:") else PIL_CHECK
    for fmt, tw in chk.items():
        t0 = time.time()
        o2 = dict(o, design="ga", design_snr=None, twin=tw, sps={"pl_fe": "jt", "pl_ph": "iv", **(o.get("sps") or {})})
        F = get_fmt(fmt, o2)
        n_p, ps = F.pil["n"], F.pil["pos"]
        assert ps.size == n_p == np.unique(ps).size and F.rmc.E == F.E - 2 * n_p, (fmt, tw, "pilot count / E1")
        d = np.random.default_rng(1).integers(0, 2, (4, F.A)).astype(np.uint8)
        e = F.encode_pil(d)[:, F.chan]
        s = pg.modulate(e, fmt)
        assert np.allclose(s[:, ps], F.pil["val"][None]), (fmt, tw, "pilot values round trip")
        assert (F.chan[np.concatenate([2 * ps, 2 * ps + 1])] >= F.rmc.E).all() and (F.chan[F._dm] < F.rmc.E).all(), \
            (fmt, tw, "a data bit on a pilot slot")
        x = F.code.encode(d)
        assert x.shape[1] == F.N + 1 and not x[:, F.N].any(), (fmt, tw, "zero pilot column")
        ev = x[:, F.inter]
        assert np.array_equal(ev[:, F._dm], e[:, F._dm]) and not ev[:, ~F._dm].any(), (fmt, tw, "re-encoding map")
        v = F.virtual(s)
        assert np.allclose(v, F.modulate_virtual(ev)), (fmt, tw, "virtual != modulate_virtual")
        assert np.allclose(v[:, ps], bfm.C0), (fmt, tw, "virtual pilots != c0")
        Lm = F.llrs(v, 1.0)
        dpos = F.pos[F._dm]
        assert np.allclose(np.abs(Lm[:, dpos]), 1.0) and np.count_nonzero(Lm, 1).max() <= F.rmc.E, (fmt, tw, "|LLR|")
        assert np.array_equal(Lm[:, dpos] < 0, x[:, dpos] == 1), (fmt, tw, "LLR signs")
        with F:                                                       # the padded metric code inside the context
            _, cw = __import__("blind_fast").fast_sc(F.A).metric_cw(bc.llrs(v, np.zeros(4), np.zeros(4), 1.0))
            assert cw.shape[1] == F.N + 1 and not cw[:, F.N].any(), (fmt, tw, "metric_cw zero column")
        res = run_chunk((fmt, 30.0, [0, pg.FMTS[fmt]["tag"], 0], 3, o2, 0))
        assert res["frame_err"] == 0 and res["right"] == 3, (fmt, tw, {k: res[k] for k in ("frame_err", "right")})
        m = F.pil["meta"]
        print(f"  ok  {fmt:6s} pil {tw}: n_p {n_p} E1 {m['E1']} pos {ps[:4].tolist()}..{ps[-2:].tolist()} span "
              f"{m['pos_span']} rms {m['pos_rms']:.0f} rot rank {m['rot_rank']} UB x{m['ub_ratio']:.2f} | MAC llr "
              f"{F.mac['llr']:.0f} | MACs/frame {res['sum_macs'] / 3:.4g}, pilots {res['st'].get('cc_t_pil', 0) / 3:.4g}"
              f" | {time.time() - t0:.1f} s", flush=True)
    print(f"PIL SELFCHECK OK ({time.time() - t_all:.1f} s)", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fmt", choices=list(pg.FMTS))
    ap.add_argument("--snrs", nargs="+", type=float, help="Es/N0 per transmitted symbol (dB)")
    ap.add_argument("--crc", type=int, default=32, choices=[32, 24, 16], help="CRC length (24: CRC24C of polar.py)")
    ap.add_argument("--list", type=int, default=pg.L_LIST, choices=[8, 16, 32], help="CA-SCL list size L of the "
                    "format's decoder (default run_polar_genie.L_LIST = 8 = the baseline; small_rx charges L / 8 "
                    "CA-SCL-8 path parts per decode and 32 // L decodes per d4a round)")
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
    ap.add_argument("--rho", default="scaled", choices=["scaled", "table", "min", "fmt"], help="re-encoding table: "
                    "scaled (default), table, min (rho_min only), fmt (RHO_FS[(fmt, crc)], the format's calibrated one)")
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
    ap.add_argument("--dump-lite", action="store_true", help="(2026-11-25) compact pk_*.npz only: right, fe, the std "
                    "per-core cost, GU_KEYS (what analyze_joint_nn / the id3t tuner read); no rows; default off")
    ap.add_argument("--lite-ops", action="store_true", help="(2026-11-25, H1) with --dump-lite: + passed, stage, f, f0 "
                    "and the per-packet cost columns (macs, cpar, c_d4a, c_hd4a); default off")
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
    ap.add_argument("--twin", default=None, help="twin design <order>:<spec>:<gmap> (sync_cfo/fs/twin_design."
                    "guess_build, e.g. search:k12:rd; blind_fmt twin; needs --design ga at the adopted design SNR; "
                    "default None = the baseline format); rep:<rule><t>[p]:<place> a repetition twin (sync_cfo/fs/"
                    "rep_twin.py, e.g. rep:gr96:ea; REP_FMTS, --design ga at the adopted design SNR)")
    ap.add_argument("--twin-fe", default="off", choices=["off", "jt"], help="jt: small_rx tw_fe jt (the twin-aided "
                    "stage-1 bin, = --sps {\"tw_fe\": \"jt\"}; needs --twin); off (default) = the 4th-power argmax")
    ap.add_argument("--pil-fe", default="off", choices=["off", "jt", "pl"], help="(--twin pil:...) small_rx pl_fe: jt "
                    "the pilot line + the 4th-power line, pl the pilot line alone (= --sps {\"pl_fe\": ...}); the phase "
                    "from the pilots: --sps {\"pl_ph\": \"iv\"}; off (default) = the 4th-power argmax")
    ap.add_argument("--genie", action="store_true", help="(2026-11-24, D1 of sync_cfo/expected_fs.md) the SAME packets "
                    "decoded once at genie sync (true f premf + true centre phase, CA-SCL-L, no search / retry / fzstop; "
                    "genie_chunk): CRC-only, CRC + the rho table and oracle-rho counters, per packet gn_*.npz with --dump; "
                    "default off = the blind receiver")
    ap.add_argument("--chunks", nargs="+", type=int, default=None, help="(2026-11-24, D4b replay) only these chunk indices "
                    "of each point (the full run's packets, entropy by chunk index), no max-err stop; default None = all")
    ap.add_argument("--part")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--selfcheck-rep", action="store_true", help="(rep twin) conventions + 3 packets at 30 dB per "
                    "REP_CHECK design (or --fmt with its --twin rep:...), at the given --crc / --list / --sps")
    ap.add_argument("--selfcheck-pil", action="store_true", help="(pilots) conventions + 3 packets at 30 dB per "
                    "PIL_CHECK design (or --fmt with its --twin pil:...), at the given --crc / --list / --sps")
    args = ap.parse_args()
    import blind_cfo as bc
    assert bc.STUDY == "small_cfo", "run with BLIND_STUDY=small_cfo (the small-CFO receiver's models and settings)"
    assert 0 < args.cfo_max <= 0.1, "--cfo-max: the 4th-power line must stay inside +-1/2 (and the tuning is for 0.03)"
    if args.design == "pw" and args.design_snr is not None:
        ap.error("--design-snr needs --design ga")
    if args.design == "ga" and args.design_snr is None and args.fmt:
        args.design_snr = pg.DESIGN_SNR[args.fmt]
    assert args.cap_core is None or args.cap_core > 0, "--cap-core: MACs per core > 0"
    o = dict(crc=args.crc, L=args.list, beta=args.beta, cfo_max=args.cfo_max, extra_in_fz=args.extra_in_fz, rho=args.rho,
             fzstop=args.fzstop, spec=args.spec, cknn=args.cknn, ck=args.ck, bpsk_phase=args.bpsk_phase,
             sub=args.sub, rx=args.rx, dump=None, chan=not args.no_chan_intlv, design=args.design,
             design_snr=args.design_snr, cap_core=args.cap_core, cknn_name=args.cknn_name, ck_c=args.ck_c, sps=None,
             charge_all=args.charge_all, fulllog=None, genie=args.genie)
    if args.chunks is not None and (min(args.chunks) < 0 or max(args.chunks) * args.batch >= args.frames
                                    or len(set(args.chunks)) != len(args.chunks)):
        ap.error("--chunks: distinct indices with chunk x batch < --frames")
    if args.genie and (args.fulllog is not None or args.selfcheck or args.selfcheck_rep or args.selfcheck_pil):
        ap.error("--genie: not with --fulllog / the selfchecks")
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
    rep_tw = args.twin is not None and args.twin.startswith("rep:")  # (rep twin) rep:<rule><t>[p]:<place>
    if rep_tw:
        import re
        if not re.match(REP_SPEC, args.twin):
            ap.error(f"--twin rep: rep:<gr|pnc|rnd|wst><t>[p]:<rd|us|ea|ex> (got {args.twin})")
        if args.fmt is not None and args.fmt not in REP_FMTS:
            ap.error(f"--twin rep: formats {REP_FMTS} only")
        if args.design != "ga" or args.no_chan_intlv:
            ap.error("--twin rep: --design ga (the adopted design), with the channel interleaver")
        if args.fmt is not None and float(args.design_snr) != float(pg.DESIGN_SNR[args.fmt]):
            ap.error(f"--twin rep: --design-snr must be the adopted {pg.DESIGN_SNR[args.fmt]}")
    pil_tw = args.twin is not None and args.twin.startswith("pil:")  # (pilots) pil:<n_p>:<place>
    if pil_tw:
        import re
        if not re.match(PIL_SPEC, args.twin):
            ap.error(f"--twin pil: pil:<n_p>:<rd|us|ea|ex> (got {args.twin})")
        if args.fmt is not None and args.fmt not in PIL_FMTS:
            ap.error(f"--twin pil: formats {PIL_FMTS} only")
        if args.design != "ga" or args.no_chan_intlv:
            ap.error("--twin pil: --design ga (the adopted design), with the channel interleaver")
        if args.fmt is not None and float(args.design_snr) != float(pg.DESIGN_SNR[args.fmt]):
            ap.error(f"--twin pil: --design-snr must be the adopted {pg.DESIGN_SNR[args.fmt]}")
        if args.twin_fe != "off" or any(k.startswith("tw_") for k in (o["sps"] or {})):
            ap.error("--twin pil: no twin front end (--twin-fe / tw_* sps keys): use --pil-fe / pl_ph / pl_parab")
    if args.pil_fe != "off":
        if not pil_tw:
            ap.error("--pil-fe needs --twin pil:...")
        o["sps"] = {**(o["sps"] or {}), "pl_fe": args.pil_fe}
    if args.twin is not None:                                         # (--twin) a twin design of the format
        if len(args.twin.split(":")) != 3:
            ap.error("--twin: <order>:<spec>:<gmap>")
        if args.design != "ga" and args.fmt != "vde32":
            ap.error("--twin: the adopted design (--design ga)")
        o["twin"] = args.twin
    if args.twin_fe != "off":
        if args.twin is None:
            ap.error("--twin-fe jt needs --twin")
        o["sps"] = {**(o["sps"] or {}), "tw_fe": args.twin_fe}
    if args.selfcheck:                                                # (--fmt + a moved-bit --twin: that format only)
        if pil_tw:
            ap.error("--selfcheck with --twin pil: use --selfcheck-pil")
        return selfcheck(o, args.fmt if args.fmt and args.twin is not None and not rep_tw else None)
    if args.selfcheck_rep:                                            # (rep twin) its own selfcheck only
        return selfcheck_rep(dict(o, fmt=args.fmt))
    if args.selfcheck_pil:                                            # (pilots) its own selfcheck only
        return selfcheck_pil(dict(o, fmt=args.fmt))
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
    elif args.dump_lite:                                              # (--dump-lite) same folder name, pk_*.npz only
        o["dump_lite"] = os.path.join(RESULTS, f"blind_fs_{args.part}_dump")
        if args.lite_ops:                                             # (--lite-ops, H1) + the per-packet ops / outcome
            o["lite_ops"] = True
    elif args.lite_ops:
        sys.exit("--lite-ops needs --dump-lite")
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
                         crc=args.crc, list_size=args.list,         # (--crc / --list; also in format and args)
                         chan_intlv=F.chan_intlv, design=args.design, design_snr_db=args.design_snr,
                         cap_core=args.cap_core, sps_override=o["sps"], charge_all=args.charge_all,
                         mac_unit=__import__("blind_vp").unit_info(),   # cost unit (BLIND_MAC_UNIT); st cc_* = its
                         #                                                per-component counters (small_rx cco)
                         fulllog=o["fulllog"], genie=args.genie,   # (--genie: genie_chunk, no MACs)
                         seed_tag=pg.FMTS[fmt]["tag"] + (CALIB_TAG if args.calib else 0),
                         sps={k: (repr(v) if not isinstance(v, (int, float, str, bool, type(None))) else v)
                              for k, v in sps.items()},
                         **({"rep_twin": dict(F.tw["meta"], twin=args.twin)} if rep_tw else {}),   # (rep twin)
                         **({"pilots": dict(F.pil["meta"])} if pil_tw else {}),                  # (pilots)
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
                 giveup=acc["st"].get("giveup", 0), giveup_pts={q: acc["st"].get(f"giveup_{q}", 0) for q in GU_PTS},
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
              f"{p['cap_hit_right']}) | CRC passes wrong {acc.get('crc_pass_wrong', 0)} (accepted "
              f"{acc.get('crc_pass_wrong_acc', 0)}), right rejected {acc.get('crc_pass_right_rej', 0)} | "
              f"{acc['time_s']:.0f} s", flush=True)
        if args.genie:                                                # (--genie) arms 1 / 2 / 6 of D1
            print(f"  genie: PER CRC-only {acc['frame_err_crc'] / n:.3e} (undetected {acc['undetected_crc']}) | CRC + "
                  f"rho {p['per']:.3e} (right rejected {acc['right_rej']}, wrong rejected {acc['wrong_rej']}) | oracle "
                  f"true-word rho <= thr {acc['true_rej']} | fails with the truth in the list {acc['fail_in_list']}",
                  flush=True)
        if args.stop_per and p["per"] < args.stop_per:
            print(f"  PER {p['per']:.2e} < --stop-per {args.stop_per:g}: sweep ends", flush=True)
            prog(npt)
            break
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
