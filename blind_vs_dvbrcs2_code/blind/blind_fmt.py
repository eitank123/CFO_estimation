"""
Format context of the blind receiver (small_rx) on a full-system native format: a rate-matched polar code
(fullsys/polar_rm.RMPolarCode, N = 1024 / 2048 / 4096, CRC-32) on n_sym QPSK, pi/2-BPSK or BPSK symbols, instead of
the 1024-symbol N = 2048 CRC-16 packet (BLIND_IMPLEMENTATION/testing/results/lit_polar_ratematch.md sec. 4).

    with BlindFormat("id13", A=952, E=2952, mod="qpsk") as F:      # sets the module globals, restores them on exit
        small_rx.small_receive(F.virtual(r), rx, snr, F.code, sigma2, st, spec)

Nothing changes without the context (bc.FMT None = the baseline). Inside it:
    globals  bc.N_SYM = n_sym, bc.N_BITS = N, bc.CENTRE / NC, bc.STEP = 1.5e-4 512 / n_sym (the same phase drift per
             step over the packet), bc.NFFT4 = the power of 2 >= 4 n_sym, bc.MAX_CFO = cfo_max (the grid scales with it),
             bc.INTERLEAVER = the virtual-bit -> mother x position map; blind_vp.MAC / PREMF_FAIR_MACS scaled to N, n_sym,
             E; bf.premf's RRC at the format's roll-off; the metric-code / grid / sub-rotation / cost-share caches
             swapped for the format's own (kept in the object: the next context of the same format reuses them)
    virtual QPSK  every modulation is fed to the QPSK receiver as virtual QPSK symbols v: QPSK v = s (Gray, bits
             e_2k -> I, e_2k+1 -> Q); BPSK s = b: v = s e^{j pi/4} = b (1 + j) / sqrt2; pi/2-BPSK s(n) = b e^{j (pi n / 2 +
             pi / 4)}: v = s e^{-j pi n / 2} = b (1 + j) / sqrt2 (n from 0 at the first symbol; the rotation is known, so
             the CFO and the centre phase are those of the chain). A BPSK symbol = a QPSK symbol with both bits = e_k:
             INTERLEAVER repeats each sent bit's position twice, its LLR = LLR_I + LLR_Q = 2 Re(v e^{-j pi/4}) / sigma2
             (= 4 Re / N0), and the re-encoded virtual symbols are the exact BPSK symbols. -r^4 of the virtual
             symbols is e^{j 4 theta} as for QPSK; the pi/2 branch of a BPSK packet has LLR 0 (a dud), the pi branch is
             the complement (PiCode). small_rx bpsk_sq: the line and phase from -j r^2 (mod pi), the dud dropped
    hop      (Fable I1 keyed axis hopping, F.hopped(pn), off unless asked) BPSK formats sent as s_n = b_n j^{p_n}, p_n a
             known PN bit per symbol (run_polar_genie.hop_pn; id42b: instead of pi/2): derot = e^{j pi/4} j^{-p_n}, so
             v = s derot = b (1 + j) / sqrt2 and the receiver sees the plain-BPSK virtual QPSK (bpsk_sq, the same
             metric / LLR / re-encoding maps). Where the de-hop goes: the hop is a per-SYMBOL factor, rx the pre-MF
             samples at 8 SPS: rx[m] = sum_k s_k g(m - 8 k) e^{j (2 pi f m / 8 + phi)} + w, each symbol's pulse spans
             +-SPAN symbols, so no per-sample factor on rx removes it. bf.premf(r, rx, fs) de-rotates rx by fs, filters,
             samples at the symbol instants: u_n = sum_k s_k e^{j phi'} g_D(n - k) ~ s_n e^{j (2 pi D (n + DELAY) +
             phi)} (D = f - fs; g_D = the Nyquist pulse at residual D: g_0(k) = delta_k), then multiplies by
             bc.FMT.derot[n] and by e^{j 2 pi fs (n + DELAY)}; both are symbol-rate factors (they commute), so the
             de-hop on the MF output is exact at D = 0 and for D != 0 leaves only the small ISI of the residual, the
             same magnitude as for plain / pi/2-BPSK (the neighbours' terms carry j^{p_k - p_n}: rotated, not larger).
             Hence the hop needs no change in bf.premf / small_rx: derot carries it on r (virtual) and on every premf.
             QPSK formats (hop4, F.hopped on id3 / id13 / id14s): s_n = q_n e^{j pi p_n / 4}, derot = e^{-j pi p_n / 4},
             v = q (mod stays 'qpsk': the same llrs / re-encoding / phase4 maps; -v^4 = e^{j 4 theta} as plain). The
             pi/4 hop is no rotation of the constellation the receiver sees: a common phase e^{j phi} commutes with the
             per-symbol factor (v -> e^{j phi} v), so the phase ambiguities and the pi/2 GF(2) rank [G; rot G] are the
             plain format's (the de-hopped bit labels are identical)
    llrs    de-rotated y (B, n_sym) -> N mother LLRs: punctured x 0, shortened x +LLR_BIG (known zero), sent x the
             channel LLR (BPSK: the I + Q sum); QPSK sends e[:, chan] (the channel interleaver, pos = pos[chan]: llrs,
             INTERLEAVER and so every re-encoding code.encode(d)[:, bc.INTERLEAVER] follow it)
    codes    code = the decoder: bc.PiCode on the rate-matched info set (puncture / none: the all-ones mother codeword
             restricted to the sent bits is all ones, the pi trick holds), NoPiCode under shortening (no all-ones
             codeword: polar_rm's guard; small_rx nopi = 4 pi/2 branches); sc = the list-1 metric code (bf.fast_sc)
    fz_mask  code.fz_mask = frozen & ~rm (& ~extra unless extra_in_fz): the pre-frozen leaves leave the fz_stop / psn
             counts (polar.PolarCode fz_mask); pre = rm | extra (small_rx ck_useful)
    twin     (twin "<order>:<spec>:<gmap>", sync_cfo/PLAN_twin_receiver.md; None = off, the baseline bit for bit) a twin
             design of sync_cfo/fs/twin_design.guess_build on the ADOPTED code (same rate matching / J / pre; any crc:
             the design and its moved-bit search rebuilt for K = A + crc, CRC-32 = the adopted designs): the
             info set moved (frozen = ~info, as td.TwinCode), chan = the design's channel map (tx bit m = e[chan[m]] XOR
             pn[m], P = pos0[chan] = pos), and the known scrambler folded into derot: c_n = s0_n / sref_n (s0 the
             symbols of x = 0 under pn, sref with pn = 0), derot = conj(c) (x the old derot for (pi/2-)BPSK). QPSK
             pn on both bits: c = (-1)^q, exact; pn on I only (the rd / cl / sp diagonal symbols): c = j^q, exact iff
             I == Q in every codeword (asserted: the two columns of the info-row generator equal), so v = the
             unscrambled virtual QPSK and llrs / re-encoding / PiCode / fz_mask / NN run unchanged. derot = sign / I-Q
             swaps: not charged. tw = dict(diag (diagonal symbols: -j v^2 = e^{j 2 theta} there), pi, pj (adjacent
             pairs), meta): small_rx tw_fe reads it
    rep      (twin "rep:<rule><t>[p]:<place>", 2026-11-23, sync_cfo/fs/rep_twin.py; QPSK rep_twin.RX_FMTS: id13 / id3 / id2
             puncture, from 2026-11-24 also id14s / id5 shorten: pos = J[:E1], base +LLR_BIG on J[E1:] of the (E - t) code) a
             REPETITION twin instead of moved info bits: self.rmc = rep_twin.RepCode's (E - t, K) rate-matched code
             (GA-aware info set; p = plain), self.rep (t,) the repeated e1 indices; tx e = [e1, e1[:, rep]] (E bits,
             encode_rep), chan / pn = rep_twin.tx_map (copy on the Q bit of the diagonal symbol whose I bit is the
             original; pn on I only there: the same +-j fold of _twin_derot, F.tw diag = its s0, pi / pj empty).
             pos (sent bit -> mother x) holds every repeated position twice, so bc.INTERLEAVER re-encodes the copies
             (code.encode(d)[:, INTERLEAVER] = the extended word: rho over all E sent bits, as tx); llrs MRC: the
             copies' LLRs ADDED onto their originals before the (E - t) rate recovery, charged t adds per LLR build
             (MAC llr + t)
    pil      (twin "pil:<n_p>:<place>", 2026-11-24 equal-overhead pilot test; QPSK rep_twin.RX_FMTS, run on id13 / id3) the
             SAME budget as a rep twin of t = 2 n_p bits spent on n_p known pilot symbols: self.rmc = the plain (E - t, K)
             rate-matched code (rm_plan's own GA design at the adopted design SNR, = rep_twin's 'p' info set: the best
             info set of a code without repeated bits), its E - t bits on the n_sym - n_p data symbols (OUR interleaver
             rng(12345).permutation(E - t) over the data bit slots), n_p pilots p_k (QPSK of the bits
             rng([PIL_SEED, tag, n_p])) at rep_twin.place(fmt, n_p, place) (the rep twins' 'ea' / 'us' placement rule);
             same Es on every symbol (frame length unchanged: Eb/N0 offset = the rep arm's). Extended word = [e1, pilot
             bits] (E): chan places the pilot bits on their symbols' I / Q; derot = c0 conj(p_k) on the pilots (c0 =
             (1 + j) / sqrt2: a sign / I-Q swap), so the virtual pilots are c0 = bits 00; pos / INTERLEAVER map the pilot
             bits to index N and the code's encode (PilPiCode / PilNoPiCode) returns (B, N + 1) with column N = 0, the
             list-1 metric code's metric_cw likewise (_PadFastSC): every re-encoding / code-aided map re-modulates the
             pilots exactly (rho over all n_sym symbols, as tx). llrs: the data bits only (the decoder gets nothing from
             the pilots), MAC llr - t (no scaling of the pilot bits). F.pil = dict(pos, val, n, meta): small_rx pl_fe /
             pl_ph (pilot_fe.py) read it

Parallel workers: every Pool worker is its own process with its own module state; a context is entered and left inside
one task (no threads), and nesting is refused. MAC model = blind_vp.mac_table(n_sym, N, E) in blind_vp.MAC_UNIT (env
BLIND_MAC_UNIT; the polar_rm.decode_macs conventions): ops (default, the fullsys/costmodel unit): decode
8 (2 N log2 N + N) / L x 8, llr CMUL 6 n_sym (de-rotation) + E (scaling), phase4 8 n_sym, reencode N / 2 log2 N + 2 E,
cmul 6, FFT 5 n log2 n; legacy: decode 8 N log2 N, llr 4 n_sym + E, phase4 4 n_sym, reencode N / 2 log2 N + 4 E,
cmul 4, FFT 2 n log2 n.
"""

import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [_p for _p in (os.path.join(ROOT, "blind"), os.path.join(ROOT, "dvbrcs2")) if _p not in sys.path]   # (package)

import blind_cfo as bc                              # noqa: E402
import blind_fast as bf                             # noqa: E402
import blind_vp as vp                               # noqa: E402
import small_rx                                     # noqa: E402
import polar_rm as rm                               # noqa: E402
from polar import PolarCode                         # noqa: E402

MODS = ("qpsk", "pi2bpsk", "bpsk")
N0_SYM = 1024                                       # the baseline packet the RHO_N tables were calibrated on
PIL_SEED = 4540                                     # (pil) the pilot bits: rng([PIL_SEED, tag, n_p])
C0 = (1 + 1j) / np.sqrt(2)                          # (pil) virtual QPSK of bits 00: the folded pilot symbol


class NoPiCode(PolarCode):
    """CA-SCL without the pi complement (shortened codes: no all-ones codeword): PolarCode.decode, and bc.PiCode's
    joint list decode (decode_joint) with the plain CRC test. last_list as bc.PiCode (measurement)."""

    def decode(self, llr, return_info=False):
        out = super().decode(llr, return_info=return_info)
        return out

    def decode_joint(self, llr_h, Ls):
        """One packet's H hypotheses (H, N) in ONE list decode of Ls >= H paths (as bc.PiCode.decode_joint)."""
        H = len(llr_h)
        assert H <= Ls
        L0, self.list_size = self.list_size, Ls
        try:
            self._pm = np.full((1, Ls), np.inf, dtype=np.float32)
            self._pm[0, :H] = 0.0
            self._bits, self._parents = [], []
            alpha = np.repeat(llr_h[:1, None, :].astype(np.float32), Ls, axis=1)
            alpha[0, :H] = llr_h
            self._rec(alpha, 0, self.N)
            info = np.empty((1, Ls, self.K), dtype=np.uint8)
            path = np.arange(Ls)[None]
            for k in range(self.K - 1, -1, -1):
                info[:, :, k] = self._bits[k][0, path]
                path = self._parents[k][0, path]
            data, crc = info[0, :, :self.A], info[0, :, self.A:]
            ok = np.all(self.crc(data) == crc, axis=1)
            self.last_list = (data[None], ok[None], self._pm)
            pm = self._pm[0]
            best = np.where(ok, pm, np.inf).argmin() if ok.any() else pm.argmin()
            return data[best], bool(ok.any()), pm[best], int(path[0, best])
        finally:
            self.list_size = L0


class _PilEnc:
    """(pil) encode -> (B, N + 1): the mother codeword + a constant 0 column (index N = the pilot bits of pos /
    bc.INTERLEAVER, so code.encode(d)[:, INTERLEAVER] re-modulates the virtual pilots c0 exactly)."""

    def encode(self, data):
        x = super().encode(data)
        return np.concatenate([x, np.zeros((len(x), 1), x.dtype)], 1)


class PilPiCode(_PilEnc, bc.PiCode):
    """(pil) bc.PiCode with the zero pilot column (_PilEnc)."""


class PilNoPiCode(_PilEnc, NoPiCode):
    """(pil) NoPiCode with the zero pilot column (_PilEnc)."""


class _PadFastSC(bf.FastSC):
    """(pil) the list-1 metric code with metric_cw's codeword (H, N + 1) padded by the zero pilot column (the CA
    retry's code_aided re-modulates cw[:, INTERLEAVER]); metric / metric_left unchanged."""

    def metric_cw(self, llr):
        pm, cw = super().metric_cw(llr)
        return pm, np.concatenate([cw, np.zeros((len(cw), 1), cw.dtype)], 1)


class BlindFormat:
    """A rate-matched format for small_rx (see the module docstring). A data bits, E coded bits, mod in MODS, mode
    None (38.212 rule) / 'puncture' / 'shorten', crc 32 (or 16), L list size, beta the chain's RRC roll-off,
    cfo_max the CFO range |f| <= cfo_max (the grid), extra_in_fz: the puncturing low block counts in fz_stop / psn,
    chan_intlv: QPSK channel interleaver chan = rng(12345).permutation(E) (tx sends e[:, chan]; pos = pos[chan]),
    design 'pw' / 'ga' at design_snr Es/N0 dB (polar_rm.rm_plan, bps from mod; tx and rx share self.rmc), chan_map
    'block2' (QPSK, Fable I3): chan = the 2-row block map, symbol n = (e_n, e_{n_sym + n}) instead (None = chan_intlv),
    twin '<order>:<spec>:<gmap>' a twin design (module docstring; None = off; name = the run_polar_genie format key);
    'rep:<rule><t>[p]:<place>' a repetition twin (module docstring rep); 'pil:<n_p>:<place>' the same budget as n_p
    known pilot symbols (module docstring pil)."""

    def __init__(self, name, A, E, mod, mode=None, crc=32, L=8, beta=0.20, cfo_max=0.03, extra_in_fz=False,
                 chan_intlv=True, design="pw", design_snr=None, chan_map=None, twin=None):
        assert mod in MODS, mod
        self.name, self.A, self.E, self.mod, self.crc, self.beta = name, A, E, mod, crc, beta
        self.cfo_max, self.extra_in_fz = float(cfo_max), bool(extra_in_fz)
        bps = 2 if mod == "qpsk" else 1
        kw = dict(design="ga", design_snr_db=design_snr, bps=bps) if design == "ga" else {}   # pw: the old call
        self.design, self.design_snr = design, (design_snr if design == "ga" else None)
        plan = rm.rm_plan(A + crc, E, mode=mode, **kw)
        assert plan["mode"] != "repeat", f"{name}: repetition (E > N) not supported by the blind format context"
        cls = NoPiCode if plan["mode"] == "shorten" else bc.PiCode
        self.rmc = rm.RMPolarCode(A, E, crc_len=crc, list_size=L, code_cls=cls, mode=mode, **kw)
        self.twin, self.tw, self.tw_pn = twin, None, None   # (tw_pn: the twin scrambler; pn = the hop PN)
        self.rep, self.rep_t = None, 0                  # (rep twin) the repeated e1 indices; None = off
        self.pil = None                                 # (pil) dict(pos, val, bits, n, meta); None = off
        if twin is not None and twin.split(":")[0] == "rep":
            tB = self._rep_code(name, twin, A, crc, L, cls)   # (rep twin) the (E - t) code + t repeated bits
        elif twin is not None and twin.split(":")[0] == "pil":
            tB = self._pil_code(name, twin, A, crc, L, cls)   # (pil) the plain (E - t) code + n_p known pilots
        else:
            tB = self._twin_code(name, twin, A, crc, L, cls) if twin is not None else None   # (twin) info set moved
        self.code = self.rmc.code                       # the decoder (N-length, rate-matched info set)
        self.N, self.mode, self.K = self.rmc.N, self.rmc.mode, self.rmc.K
        self.nopi = self.mode == "shorten"
        self.n_sym = E // 2 if mod == "qpsk" else E
        assert mod != "qpsk" or E % 2 == 0, "QPSK needs an even E"
        J, U = self.rmc.J, self.rmc.U                   # (shorten: rmc.E = E; rep twin: the (E - t) code's own E1)
        self.pos = J[U:] if self.mode == "puncture" else (J[:self.rmc.E] if self.mode == "shorten" else J.copy())
        if self.rep is not None or self.pil is not None:   # (rep twin) extended e index -> mother x (copies: pos0[rep];
            assert np.array_equal(self.pos, self._pe[:self.rmc.E]), "rep / pil: pos0 != the (E - t) plan's J[U:]"
            self.pos = self._pe.copy()                  # pil: the pilot bits -> N, the zero column)
        # channel interleaver of OUR system over the E sent bits (tx e[:, chan], as the native chain's bc.INTERLEAVER):
        # without it J keeps the mother pairs (x_2m, x_2m+1) on one QPSK symbol, the pi/2 rotation maps the
        # rate-matched code onto itself (i -> i xor 1 + a codeword) and the two pi/2 branches tie exactly
        # (chan_intlv False = the old map, a pi/2 ambiguity floor); BPSK: identity (no pi/2 branch)
        self.chan_intlv = bool(chan_intlv) and mod == "qpsk"
        self.chan = np.random.default_rng(12345).permutation(E) if self.chan_intlv else np.arange(E)
        # chan_map 'block2' (Fable I3, sync_cfo/IDEAS_fable.md; None = the rule above): QPSK symbol n = (e_n, e_{n_sym + n})
        # (a 2-row block interleaver: I = the first half of the rate-matched bits, Q = the second half). A symbol shift
        # is then a shift by 1 of both halves in natural (sub-block) order, so the SC node arrays of consecutive starts
        # are shifts of each other (small_rx i3), and the pi/2 rotation (I <-> Q) is no polar automorphism (GF(2) rank
        # [G; rot G] 592 / 1958 / 2623 for id3 / id13 / id14s vs K 304 / 984 / 1504). Zero energy, AWGN BLER unchanged
        assert chan_map in (None, "block2"), chan_map
        self.chan_map = chan_map
        if chan_map == "block2":
            assert mod == "qpsk" and E % 2 == 0, "chan_map block2: QPSK formats"
            self.chan = np.arange(E).reshape(2, E // 2).T.ravel()   # sent 2n = e_n (I), 2n + 1 = e_{n_sym + n} (Q)
        if tB is not None:                              # (twin) the design's channel map replaces OUR interleaver
            assert chan_map is None and (self.chan_intlv or mod != "qpsk"), "twin: refused with --no-chan-intlv / block2"
            self.chan = np.asarray(tB["chan"], int)
            assert np.array_equal(np.sort(self.chan), np.arange(E)), "twin: chan not a permutation"
        self.pos = self.pos[self.chan]                  # sent bit k (after chan) -> mother x position
        if tB is not None:
            assert np.array_equal(self.pos, tB["P"]), "twin: P != pos0[chan] (the twin_design tx map conventions)"
        if self.rep is not None:                        # (rep twin) sent bit m is a copy iff chan[m] >= E - t
            self._cp = self.chan >= self.rmc.E
            assert int(self._cp.sum()) == self.rep_t and np.unique(self.pos[~self._cp]).size == self.rmc.E
            assert np.array_equal(np.sort(self.pos[self._cp]), np.sort(self._pe[self.rmc.E:])), "rep: copy positions"
        if self.pil is not None:                        # (pil) sent bit m is a data bit iff chan[m] < E - t; the pilot
            self._dm = self.chan < self.rmc.E           # bits are both bits of the pilot symbols, mapped to index N
            ps_ = self.pil["pos"]
            assert np.array_equal(np.flatnonzero(~self._dm), np.sort(np.concatenate([2 * ps_, 2 * ps_ + 1]))), \
                "pil: a data bit on a pilot slot"
            assert (self.pos[~self._dm] == self.N).all() and np.unique(self.pos[self._dm]).size == self.rmc.E
        self.inter = self.pos.copy() if mod == "qpsk" else np.repeat(self.pos, 2)   # virtual bit -> mother x
        self.base = np.zeros(self.N)                    # rate recovery: punctured 0, shortened +LLR_BIG
        if self.mode == "shorten":                      # (rep twin: J[E1:], the (E - t) code's shortened set)
            self.base[J[self.rmc.E:]] = rm.LLR_BIG
        fi = self.rmc.frozen_info()
        self.rm, self.extra, self.pre = fi["rm"], fi["extra"], fi["pre"]
        self.fz_mask = self.code.frozen & ~self.rm & (np.ones(self.N, bool) if extra_in_fz else ~self.extra)
        self.code.fz_mask = self.fz_mask
        n = np.arange(self.n_sym)
        self.derot = (None if mod == "qpsk" else np.exp(-1j * np.pi * n / 2) if mod == "pi2bpsk"
                      else np.full(self.n_sym, np.exp(1j * np.pi / 4)))
        if self.pil is not None:                        # (pil) c0 conj(p_k) on the pilots: virtual pilots = c0
            self.derot = np.ones(self.n_sym, complex)
            self.derot[self.pil["pos"]] = C0 * np.conj(self.pil["val"])
        elif tB is not None:
            self._twin_derot(name, tB)                  # (twin) the scrambler folded into derot, F.tw
        self.sc =PolarCode(self.N, A, crc, list_size=1, info_pos=self.code.info_pos, crc_G=self.code.crc_G)
        self.step = 1.5e-4 * 512 / self.n_sym
        self.nfft4 = int(2 ** np.ceil(np.log2(4 * self.n_sym)))
        self.centre = (self.n_sym - 1) / 2
        self.nc = n - self.centre
        self.mtab = vp.mac_table(self.n_sym, self.N, E)   # cost constants in blind_vp.MAC_UNIT (module docstring);
        #                                                   decode = the CA-SCL-8 price for every L (small_rx charges
        #                                                   code.list_size / 8 of it, ceil(L / cores) paths per core)
        self.mac = dict(self.mtab["MAC"])
        if self.rep is not None:                        # (rep twin) the MRC: t LLR adds per LLR build
            self.mac["llr"] += self.rep_t
        if self.pil is not None:                        # (pil) no LLR scaling of the 2 n_p pilot bits
            self.mac["llr"] -= 2 * self.pil["n"]
        self._cache = dict(sc={(A, crc): self.sc, (A, 16): self.sc}, fast={}, fast_hard={}, G={}, SUB={}, E={},
                           SHARE={})
        if self.pil is not None:                        # (pil) the metric code with the padded metric_cw (bf.fast_sc)
            self._cache["fast"][(A, False)] = _PadFastSC(self.sc.frozen)
        self._saved = None

    def _twin_code(self, name, twin, A, crc, L, cls):
        """(twin) Validate the design against the adopted code and move the info set into self.rmc (as td.TwinCode);
        returns td.guess_build's record."""
        here = os.path.join(ROOT, "blind")
        if here not in sys.path:
            sys.path.insert(0, here)
        import twin_design as td                        # (import only, never edited here)
        order, spec, gmap = twin.split(":")
        assert name in td.ADOPTED, f"twin: {name} has no adopted design"
        d_, s_ = td.ADOPTED[name]
        assert self.design == d_ and (d_ != "ga" or float(self.design_snr) == float(s_)), \
            f"twin: the format must use the ADOPTED design {td.ADOPTED[name]} (got {self.design} {self.design_snr})"
        # (--crc) the design is rebuilt in-process for K = A + crc: base plan, moved-bit search, guess space, tx map all
        # take crc (twin_design caches keyed by it); crc = td.CRC (32) = the adopted designs bit for bit
        p0 = self.rmc.plan
        assert p0["mode"] == td.base_plan(name, crc)["mode"], "twin: rate-matching mode != twin_design's"
        assert np.array_equal(td.design_info(name, "k0", order, crc)[0], p0["info_pos"]), "twin: k0 info != base info_pos"
        B = td.guess_build(name, spec, order, gmap, crc=crc)
        info = np.asarray(B["info"])
        N = self.rmc.N
        fz = np.ones(N, bool)
        fz[info] = False
        assert not (p0["pre"] & ~fz).any(), "twin: an info bit on a pre-frozen position"
        assert cls is not bc.PiCode or (N - 1) in set(info.tolist()), "twin: PiCode needs u_{N-1} information"
        self.rmc.plan = dict(p0, info_pos=info, frozen=fz, rel=fz & ~p0["pre"])
        self.rmc.code = cls(N, A, crc, L, info_pos=info, crc_G=rm.crc_matrix(A, crc))
        assert np.array_equal(self.rmc.code.frozen, fz)
        if self.mod == "qpsk":
            rk = td.rotation_rank(B["G"], B["P"])
            assert rk > self.rmc.K, f"twin: pi/2 rotation rank {rk} <= K {self.rmc.K} (rotated code = the code)"
        else:
            rk = None
        p = td.base_plan(name, crc)
        ub = float(td.pd.union_bound(p["m_u"], info) / td.pd.union_bound(p["m_u"], p["info_pos"]))
        dm = td.design_info(name, spec, order, crc)[1]
        self._tw_meta = dict(spec=spec, order=order, gmap=gmap, moved=int(dm.get("m", 0)) if "m" in dm else None,
                             n_moved=int((~np.isin(info, p0["info_pos"])).sum()), rot_rank=rk, ub_ratio=ub,
                             geo={k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in (B["geo"] or {}).items()})
        return B

    def _rep_code(self, name, twin, A, crc, L, cls):
        """(rep twin, module docstring rep) The (E - t, K) code of rep_twin.RepCode into self.rmc, self.rep / rep_t,
        self._pe (E,) extended e index -> mother x; returns a guess_build-like record (chan, pn, s0, P, G, pi, pj) for
        the shared chan / P checks and _twin_derot."""
        here = os.path.join(ROOT, "blind")
        if here not in sys.path:
            sys.path.insert(0, here)
        import rep_twin as rt                           # (import only, never edited here)
        import twin_design as td
        _, spec, place = twin.split(":")
        m = re.match(r"^(gr|pnc|rnd|wst)(\d+)(p?)$", spec)
        assert m and place in rt.PLACES, f"rep: rep:<rule><t>[p]:<place in {rt.PLACES}> (got {twin})"
        assert name in rt.RX_FMTS and self.mod == "qpsk", f"rep: QPSK formats {rt.RX_FMTS} only (got {name})"
        d_, s_ = td.ADOPTED[name]
        assert self.design == d_ and float(self.design_snr) == float(s_), \
            f"rep: the format must use the ADOPTED design {td.ADOPTED[name]} (got {self.design} {self.design_snr})"
        rule, t, aw = m.group(1), int(m.group(2)), not m.group(3)
        rc = rt.RepCode(name, t, rule, crc, L, aware=aw, code_cls=cls)   # design rebuilt for K = A + crc (cached)
        assert rc.mode == self.rmc.mode in ("puncture", "shorten") and rc.N == self.rmc.N and rc.E == self.E, \
            "rep: a puncture / shorten format, the same mode and N (rate recovery: base on the E1 code's J)"
        info = np.asarray(rc.code.info_pos)
        assert cls is not bc.PiCode or (rc.N - 1) in set(info.tolist()), "rep: PiCode needs u_{N-1} information"
        self.rmc, self.rep, self.rep_t = rc.rmc, np.asarray(rc.rep, int), t
        D = rt.design(name, t, rule, crc)
        X = rt.tx_map(name, t, place, self.rep)
        pos0 = np.asarray(td._pos0(self.rmc.plan))     # e1 index -> mother x (= the rate match x[J][U':])
        assert np.array_equal(pos0, D["pos0"]), "rep: pos0 != rep_twin's"
        self._pe = np.concatenate([pos0, pos0[self.rep]])   # copy E - t + k -> pos0[rep[k]] (the same mother bit)
        G = td.gen_info(rc.N, info)
        P = self._pe[np.asarray(X["chan"], int)]
        rk = td.rotation_rank(G, P)
        assert rk > rc.K, f"rep: pi/2 rotation rank {rk} <= K {rc.K} (rotated code = the code)"
        s0, b = td.GA_REF[name], td.base_plan(name, crc)
        ub = float(rt.ub_at(name, s0, D["plan"], D["E1"], D["rep_x"], info) / rt.ub_at(name, s0, b, self.E, [],
                                                                                         b["info_pos"]))
        self._tw_meta = dict(kind="rep", spec=spec, order="rep", gmap=place, rule=rule, t=t, aware=aw, place=place,
                             E1=int(rc.E1), moved=None, n_moved=int(np.setdiff1d(info, D["info_plain"]).size),
                             rot_rank=rk, ub_ratio=ub, mrc_llr_adds=t,
                             geo={k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in X["geo"].items()})
        return dict(chan=X["chan"], pn=X["pn"], s0=X["s0"], P=P, G=G, pi=np.zeros(0, int), pj=np.zeros(0, int))

    def _pil_code(self, name, twin, A, crc, L, cls):
        """(pil, module docstring pil) The plain (E - t, K) code (t = 2 n_p) into self.rmc (Pil* code class: the zero
        pilot column), self._pe (E,) extended index -> mother x (pilot bits -> N), self.pil; returns dict(chan, P) for
        the shared chan / P checks."""
        here = os.path.join(ROOT, "blind")
        if here not in sys.path:
            sys.path.insert(0, here)
        import rep_twin as rt                           # (import only, never edited here)
        import twin_design as td
        _, ns, place = twin.split(":")
        assert re.match(r"^\d+$", ns) and place in rt.PLACES, f"pil: pil:<n_p>:<place in {rt.PLACES}> (got {twin})"
        assert name in rt.RX_FMTS and self.mod == "qpsk", f"pil: QPSK formats {rt.RX_FMTS} only (got {name})"
        d_, s_ = td.ADOPTED[name]
        assert self.design == d_ and float(self.design_snr) == float(s_), \
            f"pil: the format must use the ADOPTED design {td.ADOPTED[name]} (got {self.design} {self.design_snr})"
        n_p = int(ns)
        t, E, n = 2 * n_p, self.E, self.E // 2
        E1 = E - t
        assert 0 < n_p < n, f"pil: 0 < n_p < n_sym {n}"
        pcls = PilNoPiCode if cls is NoPiCode else PilPiCode
        r = rm.RMPolarCode(A, E1, crc_len=crc, list_size=L, code_cls=pcls, **td.plan_kw(name))   # rm_plan's GA design
        assert r.mode == self.rmc.mode in ("puncture", "shorten") and r.N == self.rmc.N, \
            "pil: a puncture / shorten format, the same mode and N (rate recovery: base on the E1 code's J)"
        info = np.asarray(r.code.info_pos)
        assert pcls is not PilPiCode or (r.N - 1) in set(info.tolist()), "pil: PiCode needs u_{N-1} information"
        self.rmc = r
        pos0 = np.asarray(td._pos0(r.plan))            # e1 index -> mother x (= the rate match x[J][U':])
        assert pos0.size == E1
        self._pe = np.concatenate([pos0, np.full(t, r.N)])   # pilot bit E1 + 2k (+1) -> N (the zero column)
        ps = rt.place(name, n_p, place)                 # pilot symbols (sorted; the rep twins' placement rule)
        q = np.random.default_rng([PIL_SEED, rt.rpg.FMTS[name]["tag"], n_p]).integers(0, 2, t).astype(np.uint8)
        isp = np.zeros(n, bool)
        isp[ps] = True
        sb = np.flatnonzero(np.repeat(~isp, 2))         # the sent-bit slots of the data symbols (E1 of them)
        chan = np.empty(E, int)
        chan[sb] = np.random.default_rng(12345).permutation(E1)   # OUR interleaver over the data bits
        chan[2 * ps], chan[2 * ps + 1] = E1 + 2 * np.arange(n_p), E1 + 2 * np.arange(n_p) + 1
        P = self._pe[chan]
        G = td.gen_info(r.N, info)
        rk = td.rotation_rank(G, P[sb])                 # (data bits only; the pilots break the pi/2 tie besides)
        assert rk > r.K, f"pil: pi/2 rotation rank {rk} <= K {r.K} (rotated code = the code)"
        b, s0 = td.base_plan(name, crc), td.GA_REF[name]
        ub = float(rt.ub_at(name, s0, r.plan, E1, [], info) / rt.ub_at(name, s0, b, E, [], b["info_pos"]))
        val = ((1 - 2.0 * q[0::2]) + 1j * (1 - 2.0 * q[1::2])) / np.sqrt(2)   # Gray QPSK (= run_polar_genie.modulate)
        self.pil = dict(pos=ps, val=val, bits=q, n=n_p,
                        meta=dict(kind="pil", twin=twin, n_p=n_p, t=t, place=place, E1=int(E1), rot_rank=int(rk),
                                  ub_ratio=ub, a=rt.PLACE_A.get(place), seed=[PIL_SEED, int(rt.rpg.FMTS[name]["tag"]),
                                                                              n_p],
                                  derot="c0 conj(p_k): sign / I-Q swap, not charged",
                                  pos_span=int(ps.max() - ps.min()), pos_rms=float(np.std(ps - (n - 1) / 2))))
        return dict(chan=chan, P=P)

    def encode_pil(self, data):
        """(pil) data (B, A) -> the extended E bits [e1, pilot bits] (before chan: tx sends [:, self.chan])."""
        e1 = self.rmc.encode_rm(data)
        return np.concatenate([e1, np.repeat(self.pil["bits"][None], len(e1), 0)], 1)

    def encode_rep(self, data):
        """(rep twin) data (B, A) -> the extended E bits [e1, e1[:, rep]] (before chan: tx sends [:, self.chan])."""
        e1 = self.rmc.encode_rm(data)
        return np.concatenate([e1, e1[:, self.rep]], 1)

    def _twin_derot(self, name, B):
        """(twin) Fold the scrambler pn into derot (module docstring; asserted exact on codewords) and build self.tw."""
        pn = np.asarray(B["pn"]).astype(np.uint8)
        assert pn.shape == (self.E,), "twin: pn (E,)"
        import run_polar_genie as pg
        s0 = pg.modulate(pn[None], name)[0]
        sref = pg.modulate(np.zeros((1, self.E), np.uint8), name)[0]
        c = s0 / sref
        near = lambda z: np.abs(c - z) < 1e-9          # noqa: E731
        assert (near(1) | near(-1) | near(1j) | near(-1j)).all(), "twin: c not in {+-1, +-j}"
        q = ~(near(1) | near(-1))                       # symbols where the fold needs I == Q
        if q.any():
            assert self.mod == "qpsk", "twin: a +-j fold on a BPSK format"
            G, P = B["G"], self.pos
            n_ = np.flatnonzero(q)
            assert np.array_equal(G[:, P[2 * n_]], G[:, P[2 * n_ + 1]]), "twin: a +-j symbol that is no clean twin"
        self.derot = (np.ones(self.n_sym, complex) if self.derot is None else self.derot) * np.conj(c)
        self.tw_pn = pn
        dg = np.asarray(B["s0"], int)
        if self.mod == "qpsk" and dg.size:              # diagonal symbols are clean twins (I == Q): -j v^2 = e^{j 2 th}
            assert np.array_equal(B["G"][:, self.pos[2 * dg]], B["G"][:, self.pos[2 * dg + 1]]), "twin: diag not clean"
        self.tw = dict(diag=dg, pi=np.asarray(B["pi"], int), pj=np.asarray(B["pj"], int),
                       lags=np.asarray(B["pj"], int) - np.asarray(B["pi"], int),
                       meta=dict(self._tw_meta, n_diag=int(dg.size), n_pairs=int(len(B["pi"])), n_pm_j=int(q.sum()),
                                 derot="free (sign / I-Q swap), not charged"))

    def hopped(self, pn):
        """(hop, module docstring) The same format sent with keyed axis hopping s_n = b_n j^{p_n} (BPSK formats; id42b:
        replaces pi/2-BPSK): a shallow copy sharing the code, maps and caches (only the per-symbol rotation differs),
        mod 'hop' (mod0 = the format's own), pn (n_sym,) the PN bits, derot = e^{j pi/4} j^{-p_n}, hop_pw 2.
        QPSK formats (hop4, s_n = q_n e^{j pi p_n / 4}, q_n the Gray QPSK): mod stays 'qpsk' (every QPSK path of the
        receiver: llrs, modulate_virtual, phase4 / the 4th-power fast path), derot = e^{-j pi p_n / 4} (v = s derot =
        q: the virtual QPSK convention v = s of the plain format), hop_pw 4."""
        import copy
        assert self._saved is None, "hop: outside a context"
        assert self.tw is None and self.pil is None, "hop: not with a twin design / pilots (derot carries them)"
        pn = np.asarray(pn).astype(int)
        assert pn.shape == (self.n_sym,) and np.isin(pn, (0, 1)).all(), "hop: n_sym PN bits"
        G = copy.copy(self)
        G.mod0, G.pn = self.mod, pn
        if self.mod == "qpsk":                          # (hop4) a known per-symbol pi/4 rotation: the bit labels of
            G.derot, G.hop_pw = np.exp(-1j * np.pi / 4 * pn), 4   # v are the plain format's (same pi/2 rank)
        else:
            G.mod, G.hop_pw = "hop", 2
            G.derot = np.where(pn == 1, -1j, 1.0) * np.exp(1j * np.pi / 4)
        return G

    # ------------------------------------------------------------------ receiver hooks
    def virtual(self, r):
        """Chain MF output r (B, n_sym) -> virtual QPSK symbols (the known (pi/2-)BPSK rotation off)."""
        return r if self.derot is None else r * self.derot[None]

    def llrs(self, y, sigma2):
        """De-rotated virtual symbols y (B, n_sym) -> mother LLRs (B, N) (bc.llrs with bc.FMT set)."""
        out = np.repeat(self.base[None], len(y), 0)
        if self.rep is not None:                        # (rep twin) MRC: the copies' LLRs added onto the originals
            le = np.empty((len(y), self.E))
            le[:, 0::2] = np.sqrt(2) * y.real / sigma2
            le[:, 1::2] = np.sqrt(2) * y.imag / sigma2
            out[:, self.pos[~self._cp]] = le[:, ~self._cp]
            out[:, self.pos[self._cp]] += le[:, self._cp]
            return out
        if self.pil is not None:                        # (pil) the data bits only: nothing from the pilots
            le = np.empty((len(y), self.E))
            le[:, 0::2] = np.sqrt(2) * y.real / sigma2
            le[:, 1::2] = np.sqrt(2) * y.imag / sigma2
            out[:, self.pos[self._dm]] = le[:, self._dm]
            return out
        if self.mod == "qpsk":
            out[:, self.pos[0::2]] = np.sqrt(2) * y.real / sigma2
            out[:, self.pos[1::2]] = np.sqrt(2) * y.imag / sigma2
        else:
            out[:, self.pos] = np.sqrt(2) * (y.real + y.imag) / sigma2
        return out

    def modulate_virtual(self, e):
        """Sent bits e (B, E) (after chan) -> virtual QPSK symbols (B, n_sym) (= the receiver's re-encoding map)."""
        v = e if self.mod == "qpsk" else np.repeat(e, 2, axis=1)
        return ((1 - 2.0 * v[:, 0::2]) + 1j * (1 - 2.0 * v[:, 1::2])) / np.sqrt(2)

    def rho_table(self, key, snrs=None):
        """Provisional re-encoding threshold table (SNR dB, rho_n) for small_rx rho_n, from blind_ber.RHO_N[key]
        (1024-symbol CRC-16 packets): the table's margin below 1 in right-pass std units, kappa = (1 - t) sqrt(2 1024)
        / sigma (sigma^2 = 1 / s at the table SNR clamped to its range), kept for n_sym: t' = 1 - kappa sigma(s') /
        sqrt(2 n_sym), s' = min(s, the table's top SNR) (rho_n of a right packet ~ 1 + N(0, sigma^2 / (2 n_sym)); above
        the table the margin stays, as the clamped table does, else t' -> 1 at high SNR). Not calibrated: recalibrate
        from the logged rho_n of the right / wrong CRC passes (run_blind_fs rho_hist)."""
        from blind_ber import RHO_N
        tab = RHO_N[key]
        s_t, t_t = (np.array(v, float) for v in zip(*tab))
        snrs = np.arange(-8.0, 8.01, 0.25) if snrs is None else np.asarray(snrs, float)
        out = []
        for s in snrs:
            sc = float(np.clip(s, s_t.min(), s_t.max()))
            kap = (1 - float(np.interp(sc, s_t, t_t))) * np.sqrt(2 * N0_SYM) / np.sqrt(10 ** (-sc / 10))
            sg = np.sqrt(10 ** (-min(float(s), float(s_t.max())) / 10))
            out.append((float(s), float(max(1 - kap * sg / np.sqrt(2 * self.n_sym), 0.0))))
        return tuple(out)

    def info(self):
        """Summary (json-safe); 'twin' only with a twin design."""
        out = dict(name=self.name, A=self.A, E=self.E, K=self.K, N=self.N, mode=self.mode, mod=self.mod,
                    crc=self.crc, n_sym=self.n_sym, nopi=self.nopi, beta=self.beta, cfo_max=self.cfo_max,
                    chan_intlv=self.chan_intlv, chan_map=self.chan_map, design=self.design, design_snr=self.design_snr,
                    step=self.step, nfft4=self.nfft4, n_rm=int(self.rm.sum()), n_extra=int(self.extra.sum()),
                    n_pre=int(self.pre.sum()), n_fz_mask=int(self.fz_mask.sum()),
                    n_frozen=int(self.code.frozen.sum()), extra_in_fz=self.extra_in_fz,
                    mac={k: float(v) for k, v in self.mac.items()},
                    premf_fair=float(self.mtab["PREMF_FAIR_MACS"]), mac_unit=vp.unit_info(),
                    decode_macs=self.rmc.macs(self.n_sym))
        if self.tw is not None:                         # design_hash (2026-11-24, measurement): sha1 of the sorted info
            import hashlib                              # indices + the rep e1 indices (none: moved bits), first 12 hex
            hb = np.concatenate([np.sort(np.asarray(self.code.info_pos, np.int64)), [-1],
                                 np.asarray(self.rep if self.rep is not None else [], np.int64)]).astype(np.int64)
            out["twin"] = dict(self.tw["meta"], twin=self.twin, design_hash=hashlib.sha1(hb.tobytes()).hexdigest()[:12])
        if self.pil is not None:                        # (pil) the same hash over the info set + the pilot symbols
            import hashlib
            hb = np.concatenate([np.sort(np.asarray(self.code.info_pos, np.int64)), [-1],
                                 np.asarray(self.pil["pos"], np.int64)]).astype(np.int64)
            out["pilots"] = dict(self.pil["meta"], design_hash=hashlib.sha1(hb.tobytes()).hexdigest()[:12])
        return out

    # ------------------------------------------------------------------ context manager
    def _targets(self):
        from txrx_chain import rrc
        G = 4 * self.step
        c = self._cache
        return [(bc, "FMT", self), (bc, "N_SYM", self.n_sym), (bc, "N_BITS", self.N), (bc, "CENTRE", self.centre),
                (bc, "NC", self.nc), (bc, "STEP", self.step), (bc, "NFFT4", self.nfft4),
                (bc, "INTERLEAVER", self.inter), (bc, "MAX_CFO", self.cfo_max), (bc, "_sc", c["sc"]),
                (bf, "_fast", c["fast"]), (bf, "_fast_hard", c["fast_hard"]), (bf, "_G", c["G"]),
                (bf, "_SUB", c["SUB"]), (bf, "_E", c["E"]), (bf, "_h", rrc(self.beta)), (bf, "GSTEP", G),
                (bf, "GRID", np.arange(-self.cfo_max, self.cfo_max + G / 2, G)),
                (vp, "MAC", dict(self.mac)), (vp, "PREMF_FAIR_MACS", self.mtab["PREMF_FAIR_MACS"]),
                (vp, "S4_MACS", vp.pow_macs(self.n_sym) + vp.fft_macs(self.nfft4)),
                (vp, "NEWTON_MACS", self.mtab["NEWTON_MACS"]),
                (vp, "PREMF_MACS", self.mtab["PREMF_MACS"]),
                (small_rx, "_SHARE", c["SHARE"])]

    def __enter__(self):
        assert bc.FMT is None and self._saved is None, "blind_fmt: contexts do not nest"
        tg = self._targets()
        self._saved = [(m, a, getattr(m, a)) for m, a, _ in tg]
        for m, a, v in tg:
            setattr(m, a, v)
        return self

    def __exit__(self, *exc):
        for m, a, v in self._saved:
            setattr(m, a, v)
        self._saved = None
        return False
