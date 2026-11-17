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
    llrs     de-rotated y (B, n_sym) -> N mother LLRs: punctured x 0, shortened x +LLR_BIG (known zero), sent x the
             channel LLR (BPSK: the I + Q sum); QPSK sends e[:, chan] (the channel interleaver, pos = pos[chan]: llrs,
             INTERLEAVER and so every re-encoding code.encode(d)[:, bc.INTERLEAVER] follow it)
    codes    code = the decoder: bc.PiCode on the rate-matched info set (puncture / none: the all-ones mother codeword
             restricted to the sent bits is all ones, the pi trick holds), NoPiCode under shortening (no all-ones
             codeword: polar_rm's guard; small_rx nopi = 4 pi/2 branches); sc = the list-1 metric code (bf.fast_sc)
    fz_mask  code.fz_mask = frozen & ~rm (& ~extra unless extra_in_fz): the pre-frozen leaves leave the fz_stop / psn
             counts (polar.PolarCode fz_mask); pre = rm | extra (small_rx ck_useful)

Parallel workers: every Pool worker is its own process with its own module state; a context is entered and left inside
one task (no threads), and nesting is refused. MAC model (blind_vp.MAC, the polar_rm.decode_macs conventions): decode
L N log2 N / L x 8, llr 4 n_sym (de-rotation) + E (scaling), phase4 4 n_sym, reencode N / 2 log2 N + 4 E, cmul 4.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import blind_cfo as bc                              # noqa: E402
import blind_fast as bf                             # noqa: E402
import blind_vp as vp                               # noqa: E402
import small_rx                                     # noqa: E402
from fullsys import polar_rm as rm                  # noqa: E402
from polar import PolarCode                         # noqa: E402

MODS = ("qpsk", "pi2bpsk", "bpsk")
N0_SYM = 1024                                       # the baseline packet the RHO_N tables were calibrated on


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


class BlindFormat:
    """A rate-matched format for small_rx (see the module docstring). A data bits, E coded bits, mod in MODS, mode
    None (38.212 rule) / 'puncture' / 'shorten', crc 32 (or 16), L list size, beta the chain's RRC roll-off,
    cfo_max the CFO range |f| <= cfo_max (the grid), extra_in_fz: the puncturing low block counts in fz_stop / psn,
    chan_intlv: QPSK channel interleaver chan = rng(12345).permutation(E) (tx sends e[:, chan]; pos = pos[chan]),
    design 'pw' / 'ga' at design_snr Es/N0 dB (polar_rm.rm_plan, bps from mod; tx and rx share self.rmc)."""

    def __init__(self, name, A, E, mod, mode=None, crc=32, L=8, beta=0.20, cfo_max=0.03, extra_in_fz=False,
                 chan_intlv=True, design="pw", design_snr=None):
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
        self.code = self.rmc.code                       # the decoder (N-length, rate-matched info set)
        self.N, self.mode, self.K = self.rmc.N, self.rmc.mode, self.rmc.K
        self.nopi = self.mode == "shorten"
        self.n_sym = E // 2 if mod == "qpsk" else E
        assert mod != "qpsk" or E % 2 == 0, "QPSK needs an even E"
        J, U = self.rmc.J, self.rmc.U
        self.pos = J[U:] if self.mode == "puncture" else (J[:E] if self.mode == "shorten" else J.copy())
        # channel interleaver of OUR system over the E sent bits (tx e[:, chan], as the native chain's bc.INTERLEAVER):
        # without it J keeps the mother pairs (x_2m, x_2m+1) on one QPSK symbol, the pi/2 rotation maps the
        # rate-matched code onto itself (i -> i xor 1 + a codeword) and the two pi/2 branches tie exactly
        # (chan_intlv False = the old map, a pi/2 ambiguity floor); BPSK: identity (no pi/2 branch)
        self.chan_intlv = bool(chan_intlv) and mod == "qpsk"
        self.chan = np.random.default_rng(12345).permutation(E) if self.chan_intlv else np.arange(E)
        self.pos = self.pos[self.chan]                  # sent bit k (after chan) -> mother x position
        self.inter = self.pos.copy() if mod == "qpsk" else np.repeat(self.pos, 2)   # virtual bit -> mother x
        self.base = np.zeros(self.N)                    # rate recovery: punctured 0, shortened +LLR_BIG
        if self.mode == "shorten":
            self.base[J[E:]] = rm.LLR_BIG
        fi = self.rmc.frozen_info()
        self.rm, self.extra, self.pre = fi["rm"], fi["extra"], fi["pre"]
        self.fz_mask = self.code.frozen & ~self.rm & (np.ones(self.N, bool) if extra_in_fz else ~self.extra)
        self.code.fz_mask = self.fz_mask
        n = np.arange(self.n_sym)
        self.derot = (None if mod == "qpsk" else np.exp(-1j * np.pi * n / 2) if mod == "pi2bpsk"
                      else np.full(self.n_sym, np.exp(1j * np.pi / 4)))
        self.sc = PolarCode(self.N, A, crc, list_size=1, info_pos=self.code.info_pos, crc_G=self.code.crc_G)
        self.step = 1.5e-4 * 512 / self.n_sym
        self.nfft4 = int(2 ** np.ceil(np.log2(4 * self.n_sym)))
        self.centre = (self.n_sym - 1) / 2
        self.nc = n - self.centre
        lg = int(np.log2(self.N))
        self.mac = dict(cmul=4, decode=8 * self.N * lg, llr=4 * self.n_sym + E, phase4=4 * self.n_sym,
                        reencode=self.N / 2 * lg + 4 * E)
        self._cache = dict(sc={(A, crc): self.sc, (A, 16): self.sc}, fast={}, fast_hard={}, G={}, SUB={}, E={},
                           SHARE={})
        self._saved = None

    # ------------------------------------------------------------------ receiver hooks
    def virtual(self, r):
        """Chain MF output r (B, n_sym) -> virtual QPSK symbols (the known (pi/2-)BPSK rotation off)."""
        return r if self.derot is None else r * self.derot[None]

    def llrs(self, y, sigma2):
        """De-rotated virtual symbols y (B, n_sym) -> mother LLRs (B, N) (bc.llrs with bc.FMT set)."""
        out = np.repeat(self.base[None], len(y), 0)
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
        """Summary (json-safe)."""
        return dict(name=self.name, A=self.A, E=self.E, K=self.K, N=self.N, mode=self.mode, mod=self.mod,
                    crc=self.crc, n_sym=self.n_sym, nopi=self.nopi, beta=self.beta, cfo_max=self.cfo_max,
                    chan_intlv=self.chan_intlv, design=self.design, design_snr=self.design_snr,
                    step=self.step, nfft4=self.nfft4, n_rm=int(self.rm.sum()), n_extra=int(self.extra.sum()),
                    n_pre=int(self.pre.sum()), n_fz_mask=int(self.fz_mask.sum()),
                    n_frozen=int(self.code.frozen.sum()), extra_in_fz=self.extra_in_fz,
                    mac={k: float(v) for k, v in self.mac.items()},
                    premf_fair=float(4 * (self.n_sym + 2 * bc.SPAN) * bc.SPS),
                    decode_macs=self.rmc.macs(self.n_sym))

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
                (vp, "MAC", dict(self.mac)), (vp, "PREMF_FAIR_MACS", 4 * (self.n_sym + 2 * bc.SPAN) * bc.SPS),
                (vp, "S4_MACS", 2 * 4 * self.n_sym + vp.fft_macs(self.nfft4)),
                (vp, "NEWTON_MACS", 4 * 3 * 4 * self.n_sym + 4 * 8 * self.n_sym),
                (vp, "PREMF_MACS", 4 * (self.n_sym + bc.SPAN) * bc.SPS + 2 * (bc.SPAN * bc.SPS + 1) * self.n_sym),
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
