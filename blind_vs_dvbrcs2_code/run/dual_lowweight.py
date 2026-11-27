"""Low-weight DUAL checks of the transmitted code (task D3, 2026-11-24): a feasibility count for future soft-syndrome
scoring. Pure GF(2) design counting (no channel, no decoder); imports twin_design / rep_twin / fullsys / polar read-only.

    code     tx bit m = x[P[m]] XOR pn[m], x = u G_N (fullsys/blind_fmt conventions: twin P = pos0[chan], chan / pn of
             td.guess_build(fmt, spec, 'search', 'rd', crc 24); rep twin P = pe[chan], pe = [pos0, pos0[rep]], chan / pn
             of rep_twin.tx_map(fmt, 96, 'ea', rep), RepCode(fmt, 96, 'gr', crc 24, aware)); u[info_pos] = v:
               noCRC  v free (K = A + 24): G_tx = G_A[:, P] (G_A = the K info rows of G_N, the code's info_pos order)
               CRC    v = [p, crc24(p)] (A rows): G_tx = [I_A | crc_G] G_A[:, P]  (asserted vs PolarCode.encode / encode_rm)
             a check = a set S of tx bits with XOR_{m in S} col_m = 0, i.e. XOR_{m in S} tx_m = c, c = XOR_{m in S} pn_m
    twins    column classes of G_A[:, P]: equal columns = the twin relations (weight-2 checks; designed = the rd clean
             twins / the rep copies), zero columns = known bits. S is in the twin span iff every class holds an even
             number of its bits, so the checks BEYOND the twins are the REDUCED checks: sets of w distinct nonzero
             classes (D of them, one representative column each) summing to 0; each has prod |class| lifts of weight
             w (one bit per class). Rank beyond twins <= D - rank(G_tx) (= E - rank - twin rank - zero columns)
    exact    (on the CRC reduced columns, whose dual contains the noCRC dual; every check classified noCRC / CRC-only
             by the G_A columns) w1 / w2: zero / equal G_eff columns among the reduced classes; w3: pair XOR == a
             column; w4: pair-XOR collisions; w5: triple XOR == a pair XOR (bitmap prefilter); w6 (D <= W6_DMAX):
             triple-XOR collisions, partitioned by the top fingerprint bits. Linear 64-bit fingerprints fp = col^T R
             (R random): a true check always collides, every hit verified on the columns
    search   (time box BOX s; w5 / w6 lower bounds where not exhaustive) Lee-Brickell ISD p <= 2 on the reduced CRC code
             (random column order, Gauss-Jordan, h_I = M h_R, wt(h_R) <= 2), the mother-dual words h_f (+ h_g)
             (h_f[j] = [f subset-of j], f frozen, wt 2^(n - wt f) <= 16, support inside the sent positions) and XOR
             pairs of found lower-weight checks; ISD recall of the exhaustive lists and the per-word miss probability
             (1 - P_hit)^iters (P_hit = P(<= 2 of the w support bits off the information set), hypergeometric)
    parity   all-ones in the row space of G_tx -> every check has even weight (noCRC: u_{N-1} info, the PiCode
             condition); odd checks counted separately (under the pi branch every bit flips: c -> c + |S| mod 2)
    stats    per weight: reduced count (noCRC / CRC-only), lifts, cumulative rank of the reduced checks vs the bound,
             QPSK symbols touched (symbol m // 2: union, per-lift histogram of distinct symbols), within one symbol vs
             cross-symbol, lifts holding a full symbol (I and Q), the share of constants c = 1

    py sync_cfo/fs/dual_lowweight.py --codes id2:twc     # one code -> results/dual_lowweight_parts/<code>.json
    py sync_cfo/fs/dual_lowweight.py --char              # w4 forms + plain k0 baselines (exact w <= 4) -> parts/char.json
    py sync_cfo/fs/dual_lowweight.py --merge             # parts -> results/dual_lowweight.json + the md
    py sync_cfo/fs/dual_lowweight.py --export-w4 id13:k0 id3:k0 id2:k0   # (2026-11-26) plain k0 w4 lists (h2fe50k-k0)"""
import argparse
import itertools
import json
import os
import sys
import time

import numpy as np
from scipy.stats import hypergeom

HERE = os.path.dirname(os.path.abspath(__file__))  # (package) run/
sys.path[:0] = [os.path.join(os.path.dirname(HERE), "blind"), os.path.join(os.path.dirname(HERE), "dvbrcs2")]

import rep_twin as rt  # noqa: E402
import twin_design as td  # noqa: E402  (td.RES = run/data)
import polar_rm as rm  # noqa: E402
import run_polar_genie as rpg  # noqa: E402
from polar import PolarCode  # noqa: E402

PARTS = os.path.join(td.RES, "dual_lowweight_parts")
JSON = os.path.join(td.RES, "dual_lowweight.json")
MD = os.path.join(td.RES, "dual_lowweight.md")
CRC = 24
CODES = {"id2:twc": ("id2", "twin", "k12"), "id3:tz0": ("id3", "twin", "k18z0"), "id3:rpz": ("id3", "rep", "gr96"),
         "id13:twc": ("id13", "twin", "k18"), "id13:rpz": ("id13", "rep", "gr96"),
         "pc1024:twc": ("pc1024", "twin", "k18z0")}   # (2026-11-26) pc1024 twin code (k18z0: k18's 68 twins, lower UB)
PLAIN = {"vde32:plain": ("vde32", 32)}   # (2026-11-25, H1 VDE; --export-w4 only) the plain ADOPTED blind code of a format
                                         # (no twin), CRC length: as fullsys/blind_fmt.BlindFormat builds it (design pw)
K0 = {f"{f}:k0": f for f in ("id2", "id3", "id13", "pc1024")}   # (2026-11-26, h2fe50k-k0; --export-w4 only) plain k0
#                                        (k0_code: CRC-24, GA at DESIGN_SNR, rng(12345) interleaver, pn 0) = the
#                                        BlindFormat of h2_frontend_diag --code k0 (twin None) -> dual_w4_<fmt>_k0.json
BOX = 1200.0                                               # w5 / w6 search box (s) per code
HARD = 1420.0                                              # absolute cap from start (the runs use timeout 1500)
WMAX = 6
W6_DMAX = 1000                                             # exhaustive w6 (triple collisions) up to this D
TRI_PASS = 3_000_000                                       # w6: triples kept per partition pass
BMB = 28                                                   # w5 bitmap: 2^BMB bits over the top pair-XOR bits
LIFT_CAP = 200_000                                         # per weight: lifts enumerated for the symbol stats
COMBO_CAP = 20_000_000                                     # pair evaluations per combo step
RANK_CAP = 200_000                                         # per weight: reduced checks fed to the rank (random subset)
FP_SEED, ISD_SEED = 4610, 4611


def words(B):
    """(R, bits) bool -> (R, W) uint64 (zero padded)."""
    pk = np.packbits(np.asarray(B, bool), axis=1)
    pad = (-pk.shape[1]) % 8
    pk = np.concatenate([pk, np.zeros((pk.shape[0], pad), np.uint8)], 1)
    return np.ascontiguousarray(pk).view(np.uint64)


def gf2_rank_rows(R, basis=None):
    """Rank of the packed rows R (n, W) uint64 [+ a previous echelon basis]; returns (rank, echelon basis)."""
    M = R.copy() if basis is None else np.concatenate([basis, R])
    if not M.shape[0]:
        return 0, M
    W = M.shape[1]
    r = 0
    for col in range(64 * W):
        if r == M.shape[0]:
            break
        w, b = col >> 6, np.uint64(1) << np.uint64(col & 63)
        nz = np.flatnonzero(M[r:, w] & b)
        if not nz.size:
            continue
        pr = r + nz[0]
        if pr != r:
            M[[r, pr]] = M[[pr, r]]
        sel = r + 1 + np.flatnonzero(M[r + 1:, w] & b)
        if sel.size:
            M[sel] ^= M[r]
        r += 1
    return r, M[:r].copy()


def build(code):
    """The transmitted code: P, pn, info (code order), G_A (K x N), G_eff (A x N), designed twin pairs (tx indices)."""
    if code in PLAIN:
        return plain_code(code)
    if code in K0:                                         # (2026-11-26, --export-w4 only) the plain k0 code
        return k0_code(K0[code])
    fmt, kind, spec = CODES[code]
    f = rpg.FMTS[fmt]
    A, E = f["A"], f["E"]
    crcG = rm.crc_matrix(A, CRC)
    pay = np.random.default_rng(7).integers(0, 2, (16, A)).astype(np.uint8)
    if kind == "twin":
        B = td.guess_build(fmt, spec, "search", "rd", crc=CRC)
        N, P, pn = int(B["N"]), np.asarray(B["P"], int), np.asarray(B["pn"], np.uint8)
        pos0 = td._pos0(B["plan"])
        assert np.array_equal(pos0[np.asarray(B["chan"], int)], P), "P != pos0[chan]"
        enc = PolarCode(N, A, CRC, 1, info_pos=np.asarray(B["info"]), crc_G=crcG)
        info = np.asarray(enc.info_pos)
        gs = B["gs"]
        tpos = np.full(N, -1, int)
        tpos[P] = np.arange(E)
        ks = gs["ks"][gs["level"] == 0]
        designed = np.array([(tpos[k], tpos[k + N // 2]) for k in ks], int).reshape(-1, 2)
        x = enc.encode(pay)
        tx_ref = x[:, P] ^ pn
        meta = dict(twin=f"search:{spec}:rd", n_diag=int(len(B["s0"])))
    else:
        t = int(spec[2:])
        rc = rt.RepCode(fmt, t, "gr", CRC, L=1, aware=True)
        X = rt.tx_map(fmt, t, "ea", rc.rep)
        chan, pn = np.asarray(X["chan"], int), np.asarray(X["pn"], np.uint8)
        pos0 = td._pos0(rc.rmc.plan)
        pe = np.concatenate([pos0, pos0[rc.rep]])
        P = pe[chan]
        N = int(rc.N)
        info = np.asarray(rc.code.info_pos)
        tinv = np.empty(E, int)
        tinv[chan] = np.arange(E)
        designed = np.stack([tinv[rc.rep], tinv[rc.E1 + np.arange(t)]], 1)
        tx_ref = rc.encode_rm(pay)[:, chan] ^ pn
        x = rc.code.encode(pay)
        meta = dict(twin=f"rep:{spec}:ea", E1=int(rc.E1), n_diag=int(len(X["s0"])))
    j = np.arange(N)
    G_A = (j[None, :] & ~info[:, None]) == 0              # K x N, row r = info_pos[r] (data first A, CRC last C)
    G_eff = (G_A[:A].astype(np.uint8) ^ ((crcG.astype(np.int32) @ G_A[A:].astype(np.int32)) % 2).astype(np.uint8)).astype(bool)
    xe = (pay.astype(np.int32) @ G_eff.astype(np.int32)) % 2
    assert np.array_equal(x, xe), f"{code}: x != p G_eff"
    assert np.array_equal(tx_ref, xe[:, P] ^ pn), f"{code}: tx != x[P] ^ pn"
    return dict(code=code, fmt=fmt, kind=kind, spec=spec, N=N, A=A, K=int(info.size), E=E, P=P, pn=pn, info=info,
                G_A=G_A, G_eff=G_eff, designed=designed, meta=meta, mode=f["mode"])


class Dual:
    """Reduced classes, fingerprints, exhaustive w <= 4 (+ w5 / w6), searches, stats."""

    def __init__(self, C, t0):
        self.C, self.t0 = C, t0
        P = C["P"]
        GA, GC = C["G_A"][:, P], C["G_eff"][:, P]           # K x E, A x E
        self.E = P.size
        pk = np.packbits(GA.T, axis=1)
        _, inv, cnt = np.unique(pk, axis=0, return_inverse=True, return_counts=True)
        inv = np.asarray(inv).ravel()
        z = ~pk.any(1)
        zid = int(inv[np.flatnonzero(z)[0]]) if z.any() else -1
        self.zero = np.flatnonzero(z)
        ids = [i for i in range(cnt.size) if i != zid]
        remap = np.full(cnt.size, -1, int)
        remap[ids] = np.arange(len(ids))
        self.cls = remap[inv]                              # tx bit -> reduced class (-1 = zero column)
        self.D = D = len(ids)
        self.members = [[] for _ in range(D)]
        for m, c in enumerate(self.cls):
            if c >= 0:
                self.members[c].append(m)
        self.size = np.array([len(v) for v in self.members], int)
        self.rep = np.array([v[0] for v in self.members], int)
        self.CA, self.CC = GA[:, self.rep], GC[:, self.rep]  # K x D, A x D
        self.PA, self.PC = words(self.CA.T), words(self.CC.T)  # D x w
        self.rank_A, self.rank_C = int(td.gf2_rank(GA)), int(td.gf2_rank(GC))
        one = np.ones((1, self.E), bool)
        self.ones_A = int(td.gf2_rank(np.concatenate([GA, one]))) == self.rank_A
        self.ones_C = int(td.gf2_rank(np.concatenate([GC, one]))) == self.rank_C
        R = np.random.default_rng(FP_SEED).integers(0, 2, (C["A"], 64)).astype(np.float32)
        bits = (self.CC.T.astype(np.float32) @ R) % 2      # D x 64 (exact: sums <= A)
        self.fp = np.packbits(bits.astype(bool), axis=1, bitorder="little").view(np.uint64).ravel()
        self.found = {w: set() for w in range(1, WMAX + 1)}   # reduced checks (sorted class tuples)
        self.exact = {}                                    # w -> True if exhaustive
        self.src = {w: {} for w in range(1, WMAX + 1)}     # w -> {source: n new}
        self.times = {}

    def el(self):
        return time.time() - self.t0

    def verify(self, T):
        """T (n, w) class indices -> (valid CRC check, noCRC check) bool masks."""
        T = np.asarray(T, int)
        if not T.size:
            return np.zeros(0, bool), np.zeros(0, bool)
        vc = ~np.bitwise_xor.reduce(self.PC[T], axis=1).any(1)
        va = ~np.bitwise_xor.reduce(self.PA[T], axis=1).any(1)
        return vc, va

    def add(self, w, tuples, source):
        if not len(tuples):
            return 0
        T = np.unique(np.sort(np.asarray(list(tuples), int).reshape(-1, w), 1), axis=0)
        T = T[np.all(np.diff(T, axis=1) > 0, 1)] if w > 1 else T
        vc, _ = self.verify(T)
        n0 = len(self.found[w])
        self.found[w].update(map(tuple, T[vc].tolist()))
        k = len(self.found[w]) - n0
        self.src[w][source] = self.src[w].get(source, 0) + k
        return k

    # ---------------------------------------------------------------- exhaustive
    def low(self):
        t = time.time()
        D = self.D
        self.add(1, [(i,) for i in np.flatnonzero(~self.PC.any(1))], "exact")
        _, inv, cnt = np.unique(self.PC, axis=0, return_inverse=True, return_counts=True)
        inv = np.asarray(inv).ravel()
        w2 = [p for g in np.flatnonzero(cnt > 1) for p in itertools.combinations(np.flatnonzero(inv == g), 2)]
        self.add(2, w2, "exact")
        self.exact[1] = self.exact[2] = True
        o = np.argsort(self.fp, kind="stable")
        fs = self.fp[o]
        w3 = []
        for i in range(D - 1):
            x = self.fp[i] ^ self.fp[i + 1:]
            p = np.minimum(np.searchsorted(fs, x), D - 1)
            for q in np.flatnonzero(fs[p] == x):
                k = int(o[p[q]])
                jj = i + 1 + int(q)
                if k != i and k != jj:
                    w3.append((i, jj, k))
        self.add(3, w3, "exact")
        self.exact[3] = True
        I, J = np.triu_indices(D, 1)
        self.I, self.J = I.astype(np.int32), J.astype(np.int32)
        del I, J
        self.S = self.fp[self.I] ^ self.fp[self.J]
        self.o = np.argsort(self.S, kind="stable")
        self.Ss = self.S[self.o]
        self.st = np.searchsorted(self.I, np.arange(D + 1)).astype(np.int64)
        eq = np.flatnonzero(self.Ss[1:] == self.Ss[:-1])
        w4 = []
        if eq.size:
            starts = eq[np.r_[True, np.diff(eq) > 1]]
            for s0 in starts:
                e = s0 + 1
                while e + 1 < self.Ss.size and self.Ss[e + 1] == self.Ss[s0]:
                    e += 1
                qs = self.o[s0:e + 1]
                for a, b in itertools.combinations(qs, 2):
                    u = {int(self.I[a]), int(self.J[a]), int(self.I[b]), int(self.J[b])}
                    if len(u) == 4:
                        w4.append(tuple(sorted(u)))
        self.add(4, w4, "exact")
        self.exact[4] = True
        self.times["w1_4"] = round(time.time() - t, 1)
        print(f"  {self.C['code']}: D {D} | exact w1 {len(self.found[1])} w2 {len(self.found[2])} w3 "
              f"{len(self.found[3])} w4 {len(self.found[4])} ({self.times['w1_4']} s, {self.el():.0f} s)", flush=True)

    def w5(self, deadline):
        """Exhaustive w5: fp_a ^ fp_b ^ fp_c (a < b < c) in the pair-XOR set, bitmap prefilter, disjoint, verified."""
        t = time.time()
        D, S, Ss, o, I, J, st = self.D, self.S, self.Ss, self.o, self.I, self.J, self.st
        sh = np.uint64(64 - BMB)
        bm = np.zeros(1 << (BMB - 3), np.uint8)
        idx = S >> sh
        np.bitwise_or.at(bm, (idx >> np.uint64(3)).astype(np.int64), (np.uint8(1) << (idx & np.uint64(7)).astype(np.uint8)))
        del idx
        out, done = [], True
        n_s = Ss.size
        for a in range(D - 2):
            if time.time() > deadline:
                done = False
                break
            lo = st[a + 1]
            X = S[lo:] ^ self.fp[a]
            ix = X >> sh
            hit = (bm[(ix >> np.uint64(3)).astype(np.int64)] >> (ix & np.uint64(7)).astype(np.uint8)) & 1
            c = np.flatnonzero(hit)
            if not c.size:
                continue
            Xc = X[c]
            p = np.searchsorted(Ss, Xc)
            ok = (p < n_s) & (Ss[np.minimum(p, n_s - 1)] == Xc)
            for ii in np.flatnonzero(ok):
                q, xv, k = int(c[ii]), Xc[ii], int(p[ii])
                tri = (a, int(I[lo + q]), int(J[lo + q]))
                while k < n_s and Ss[k] == xv:
                    d, e = int(I[o[k]]), int(J[o[k]])
                    if d not in tri and e not in tri:
                        out.append(tuple(sorted(tri + (d, e))))
                    k += 1
        del bm
        self.add(5, out, "exact" if done else "w5_partial")
        self.exact[5] = done
        self.times["w5"] = round(time.time() - t, 1)
        print(f"  w5 {'exhaustive' if done else 'PARTIAL'}: {len(self.found[5])} ({self.times['w5']} s)", flush=True)

    def w6(self, deadline):
        """Exhaustive w6 (D <= W6_DMAX): equal triple XORs, disjoint triples, partitioned by the top bits."""
        t = time.time()
        D, S, I, J, st = self.D, self.S, self.I, self.J, self.st
        ntri = D * (D - 1) * (D - 2) // 6
        lb = max(0, int(np.ceil(np.log2(max(ntri / TRI_PASS, 1)))))
        npass = 1 << lb
        out, done = [], True
        for ps in range(npass):
            if time.time() > deadline:
                done = False
                break
            V, AA, QQ = [], [], []
            for a in range(D - 2):
                lo = st[a + 1]
                X = S[lo:] ^ self.fp[a]
                sel = np.flatnonzero((X >> np.uint64(64 - lb)) == ps) if lb else np.arange(X.size)
                V.append(X[sel])
                AA.append(np.full(sel.size, a, np.int32))
                QQ.append((lo + sel).astype(np.int64))
            V, AA, QQ = np.concatenate(V), np.concatenate(AA), np.concatenate(QQ)
            od = np.argsort(V, kind="stable")
            V, AA, QQ = V[od], AA[od], QQ[od]
            eq = np.flatnonzero(V[1:] == V[:-1])
            if eq.size:
                starts = eq[np.r_[True, np.diff(eq) > 1]]
                for s0 in starts:
                    e = s0 + 1
                    while e + 1 < V.size and V[e + 1] == V[s0]:
                        e += 1
                    tris = [(int(AA[k]), int(I[QQ[k]]), int(J[QQ[k]])) for k in range(s0, e + 1)]
                    for x, y in itertools.combinations(tris, 2):
                        u = set(x) | set(y)
                        if len(u) == 6:
                            out.append(tuple(sorted(u)))
            del V, AA, QQ
        self.add(6, out, "exact" if done else "w6_partial")
        self.exact[6] = done
        self.times["w6"] = round(time.time() - t, 1)
        print(f"  w6 {'exhaustive' if done else 'PARTIAL'} ({npass} passes): {len(self.found[6])} "
              f"({self.times['w6']} s)", flush=True)

    # ---------------------------------------------------------------- searches
    def structured(self):
        """Mother-dual words h_f (+ h_g), f frozen, wt(h_f) <= 16, support inside the sent positions -> reduced."""
        t = time.time()
        C = self.C
        N = C["N"]
        n = int(np.log2(N))
        mcls = np.full(N, -1, int)                         # mother position -> reduced class (-2 zero col, -1 not sent)
        for m in range(self.E):
            mcls[C["P"][m]] = self.cls[m] if self.cls[m] >= 0 else -2
        fz = np.setdiff1d(np.arange(N), C["info"])
        pc = np.array([bin(int(v)).count("1") for v in fz])
        F = fz[pc >= n - 4]
        sup = []
        for f in F:
            free = [b for b in range(n) if not (f >> b) & 1]
            s = [int(f) | sum(1 << free[i] for i in range(len(free)) if (k >> i) & 1) for k in range(1 << len(free))]
            sup.append(frozenset(s))

        def red(s):
            c = mcls[np.fromiter(s, int)]
            if (c == -1).any():
                return None
            c = c[c >= 0]
            u, k = np.unique(c, return_counts=True)
            return tuple(u[k % 2 == 1].tolist())

        got = {w: [] for w in range(1, WMAX + 1)}
        for s in sup:
            r = red(s)
            if r and len(r) <= WMAX:
                got[len(r)].append(r)
        npair = 0
        for a in range(len(sup)):
            for b in range(a + 1, len(sup)):
                s = sup[a] ^ sup[b]
                if not s or len(s) > 4 * WMAX:
                    continue
                npair += 1
                r = red(s)
                if r and len(r) <= WMAX:
                    got[len(r)].append(r)
        new = {w: self.add(w, v, "mother") for w, v in got.items() if v}
        self.times["structured"] = round(time.time() - t, 1)
        self.n_frozen_hi = int(F.size)
        print(f"  structured: {F.size} frozen f with wt(h_f) <= 16, {npair} pairs, new {new} "
              f"({self.times['structured']} s)", flush=True)

    def combos(self):
        """XOR pairs of found checks: w3 + w3 disjoint, w3 + w4 / w4 + w4 sharing one class -> w5 / w6."""
        t = time.time()
        vec = {}
        for w in (3, 4, 5):
            L = sorted(self.found[w])
            if L:
                M = np.zeros((len(L), self.D), bool)
                for i, c in enumerate(L):
                    M[i, list(c)] = True
                vec[w] = words(M)
        for a, b in ((3, 3), (3, 4), (4, 4), (3, 5)):
            if a not in vec or b not in vec or vec[a].shape[0] * vec[b].shape[0] > COMBO_CAP:
                continue
            Va, Vb = vec[a], vec[b]
            out = {w: [] for w in (5, 6)}
            for i in range(Va.shape[0]):
                X = Va[i] ^ Vb
                wt = np.bitwise_count(X).sum(1)
                for w in (5, 6):
                    for k in np.flatnonzero(wt == w):
                        bits = np.unpackbits(X[k:k + 1].view(np.uint8), bitorder="big")[:self.D]
                        out[w].append(tuple(np.flatnonzero(bits).tolist()))
            for w in (5, 6):
                self.add(w, out[w], "combo")
        self.times["combos"] = round(time.time() - t, 1)

    def isd(self, deadline, seed=ISD_SEED):
        """Lee-Brickell p <= 2 on the reduced CRC code until the deadline: every check of weight <= WMAX found."""
        t = time.time()
        rng = np.random.default_rng(seed)
        A, D = self.CC.shape
        it = 0
        while time.time() < deadline:
            perm = rng.permutation(D)
            M = np.packbits(self.CC[:, perm], axis=1)
            r, piv = 0, []
            for col in range(D):
                if r == A:
                    break
                by, bt = col >> 3, np.uint8(1 << (7 - (col & 7)))
                nz = np.flatnonzero(M[r:, by] & bt)
                if not nz.size:
                    continue
                pr = r + nz[0]
                if pr != r:
                    M[[r, pr]] = M[[pr, r]]
                sel = np.flatnonzero(M[:, by] & bt)
                sel = sel[sel != r]
                if sel.size:
                    M[sel] ^= M[r]
                piv.append(col)
                r += 1
            assert r == A, f"ISD: rank {r} < A {A}"
            piv = np.array(piv, int)
            Bm = np.unpackbits(M, axis=1)[:, :D].astype(bool)
            npv = np.setdiff1d(np.arange(D), piv)
            Mc = Bm[:, npv]                                # A x nR, row r <-> pivot column piv[r]
            Wc = words(Mc.T)
            wt1 = np.bitwise_count(Wc).sum(1)
            got = {w: [] for w in range(1, WMAX + 1)}
            for jj in np.flatnonzero(wt1 + 1 <= WMAX):
                s = np.concatenate([[npv[jj]], piv[Mc[:, jj]]])
                got[s.size].append(tuple(np.sort(perm[s]).tolist()))
            for jj in range(npv.size - 1):
                x = Wc[jj] ^ Wc[jj + 1:]
                wt = np.bitwise_count(x).sum(1)
                for g in np.flatnonzero(wt + 2 <= WMAX):
                    ll = jj + 1 + int(g)
                    s = np.concatenate([[npv[jj], npv[ll]], piv[Mc[:, jj] ^ Mc[:, ll]]])
                    got[s.size].append(tuple(np.sort(perm[s]).tolist()))
            for w, v in got.items():
                if v:
                    self.isd_hits[w].update(v)
                    self.add(w, v, "isd")
            it += 1
        self.isd_iters += it
        self.times["isd"] = round(self.times.get("isd", 0) + time.time() - t, 1)
        nR = D - A
        self.isd_phit = {w: float(hypergeom(D, nR, w).cdf(2)) for w in range(1, WMAX + 1)}
        print(f"  ISD: {it} iterations ({self.times['isd']} s), hits per weight "
              f"{ {w: len(v) for w, v in self.isd_hits.items()} }", flush=True)

    # ---------------------------------------------------------------- stats
    def stats(self, w):
        L = sorted(self.found[w])
        T = np.asarray(L, int).reshape(-1, w)
        _, va = self.verify(T)
        n_a = int(va.sum())
        lifts = int(np.prod(self.size[T], axis=1).sum()) if T.size else 0
        cls_used = np.unique(T) if T.size else np.zeros(0, int)
        sym_union = sorted({m // 2 for c in cls_used for m in self.members[c]})
        rng = np.random.default_rng(5)
        order = rng.permutation(len(L)) if lifts > LIFT_CAP else np.arange(len(L))
        hist, within, full, c1, nl, n_sampled = {}, 0, 0, 0, 0, 0
        for i in order:
            if nl >= LIFT_CAP:
                break
            n_sampled += 1
            for lift in itertools.product(*[self.members[c] for c in L[i]]):
                s = [m // 2 for m in lift]
                k = len(set(s))
                hist[k] = hist.get(k, 0) + 1
                within += k == 1
                full += k < len(s)
                c1 += int(np.bitwise_xor.reduce(self.C["pn"][list(lift)]))
                nl += 1
        return dict(w=w, count=len(L), noCRC=n_a, crc_only=len(L) - n_a, odd=w % 2 == 1, lifts=lifts,
                    exact=bool(self.exact.get(w, False)), sources=self.src[w], sym_union=len(sym_union),
                    lift_sym_hist={int(k): int(v) for k, v in sorted(hist.items())}, lifts_seen=nl,
                    checks_seen=n_sampled, within_one_symbol=int(within), cross_symbol=int(nl - within),
                    with_full_symbol=int(full), const1=int(c1),
                    isd_hits=len(self.isd_hits.get(w, ())),
                    isd_recall=(len(self.isd_hits[w] & self.found[w]) / len(self.found[w])
                                if self.found[w] and self.exact.get(w) else None),
                    isd_phit=self.isd_phit.get(w), isd_miss=((1 - self.isd_phit[w]) ** self.isd_iters
                                                             if w in self.isd_phit else None),
                    sample=[[int(self.rep[c]) for c in t] for t in L[:20]]), T, va

    def ranks(self, rows):
        """Cumulative rank of the reduced checks (noCRC subset / all) per weight."""
        out = {}
        bA, bC = None, None
        rA, rC = 0, 0
        for w in range(1, WMAX + 1):
            T, va = rows[w]
            if T.shape[0] > RANK_CAP:                      # (rank <= D - rank G: a subset saturates it)
                k = np.random.default_rng(6).choice(T.shape[0], RANK_CAP, replace=False)
                T, va = T[k], va[k]
            if T.size:
                M = np.zeros((T.shape[0], self.D), bool)
                np.put_along_axis(M, T, True, axis=1)
                V = words(M)
                for s in range(0, V.shape[0], 20000):
                    rC, bC = gf2_rank_rows(V[s:s + 20000], bC)
                if va.any():
                    Va = V[va]
                    for s in range(0, Va.shape[0], 20000):
                        rA, bA = gf2_rank_rows(Va[s:s + 20000], bA)
            out[w] = dict(rank_noCRC=int(rA), rank_CRC=int(rC))
        return out


def run(code, box=BOX):
    t0 = time.time()
    C = build(code)
    Dl = Dual(C, t0)
    Dl.isd_hits = {w: set() for w in range(1, WMAX + 1)}
    Dl.isd_iters, Dl.isd_phit = 0, {}
    tb = time.time() - t0
    print(f"{code}: {C['meta']['twin']} N {C['N']} E {C['E']} K {C['K']} A {C['A']} | classes D {Dl.D} zero "
          f"{Dl.zero.size} sizes {dict(zip(*np.unique(Dl.size, return_counts=True)))} | rank noCRC {Dl.rank_A} CRC "
          f"{Dl.rank_C} | all-ones in code noCRC {Dl.ones_A} CRC {Dl.ones_C} ({tb:.0f} s)", flush=True)
    Dl.low()
    ts = time.time()
    deadline = min(ts + box, t0 + HARD)
    Dl.w5(deadline)
    if Dl.D <= W6_DMAX:
        Dl.w6(deadline)
    Dl.structured()
    Dl.combos()
    Dl.isd(deadline)
    box_used = round(time.time() - ts, 1)
    # twin relations (weight 2 on the full code)
    sz = Dl.size
    des = C["designed"]
    des_eq = [Dl.cls[a] == Dl.cls[b] and Dl.cls[a] >= 0 for a, b in des]
    twin_pairs = [(m1, m2) for v in Dl.members for m1, m2 in itertools.combinations(v, 2)]
    des_set = {tuple(sorted(map(int, p))) for p in des}
    tw = dict(classes_ge2=int((sz >= 2).sum()), sizes={int(k): int(v) for k, v in zip(*np.unique(sz, return_counts=True))},
              weight2_checks=len(twin_pairs), twin_rank=int((sz - 1).sum()), designed=int(len(des)),
              designed_equal=int(np.sum(des_eq)), extra_pairs=int(len({tuple(sorted(p)) for p in twin_pairs} - des_set)),
              designed_within_symbol=int(np.sum(des[:, 0] // 2 == des[:, 1] // 2)) if len(des) else 0,
              pairs_within_symbol=int(sum(a // 2 == b // 2 for a, b in twin_pairs)),
              designed_const1=int(np.sum(C["pn"][des[:, 0]] ^ C["pn"][des[:, 1]])) if len(des) else 0,
              zero_cols=int(Dl.zero.size))
    rows, W = {}, {}
    for w in range(1, WMAX + 1):
        W[w], T, va = Dl.stats(w)
        rows[w] = (T, va)
    rk = Dl.ranks(rows)
    for w in W:
        W[w].update(rk[w])
    res = dict(code=code, fmt=C["fmt"], kind=C["kind"], spec=C["spec"], meta=C["meta"], mode=C["mode"], N=C["N"],
               E=C["E"], K=C["K"], A=C["A"], crc=CRC, D=Dl.D, rank_noCRC=Dl.rank_A, rank_CRC=Dl.rank_C,
               ub_new_noCRC=Dl.D - Dl.rank_A, ub_new_CRC=Dl.D - Dl.rank_C, allones_noCRC=Dl.ones_A,
               allones_CRC=Dl.ones_C, twins=tw, weights={str(w): v for w, v in W.items()}, isd_iters=Dl.isd_iters,
               n_frozen_hi=Dl.n_frozen_hi, times=dict(Dl.times, build=round(tb, 1), box_used=box_used,
                                                      total=round(time.time() - t0, 1)), box=box)
    print(f"{code}: " + " | ".join(f"w{w} {v['count']}{'' if v['exact'] else '+'} (noCRC {v['noCRC']}, rank "
                                   f"{v['rank_noCRC']}/{v['rank_CRC']})" for w, v in W.items())
          + f" | {res['times']['total']} s", flush=True)
    return res


def k0_code(fmt):
    """The plain adopted code (k0, crc 24) on OUR channel interleaver rng(12345) (blind_fmt chan_intlv), pn = 0."""
    p = td.base_plan(fmt, CRC)
    f = rpg.FMTS[fmt]
    A, E, N = f["A"], f["E"], p["N"]
    crcG = rm.crc_matrix(A, CRC)
    info = np.asarray(PolarCode(N, A, CRC, 1, info_pos=p["info_pos"], crc_G=crcG).info_pos)
    j = np.arange(N)
    G_A = (j[None, :] & ~info[:, None]) == 0
    G_eff = (G_A[:A].astype(np.uint8) ^ ((crcG.astype(np.int32) @ G_A[A:].astype(np.int32)) % 2).astype(np.uint8)).astype(bool)
    P = td._pos0(p)[np.random.default_rng(12345).permutation(E)]
    return dict(code=f"{fmt}:k0", fmt=fmt, N=N, A=A, K=int(info.size), E=E, P=P, pn=np.zeros(E, np.uint8), info=info,
                G_A=G_A, G_eff=G_eff, designed=np.zeros((0, 2), int), meta=dict(twin="k0"), mode=p["mode"])


def plain_code(code):
    """(2026-11-25, H1 VDE) the plain adopted blind code of PLAIN[code] exactly as fullsys/blind_fmt.BlindFormat builds
    it (no twin, design pw): RMPolarCode(A, E, crc), sent bit m = x[P[m]], P = J[U:] (puncture) / J[:E] (shorten) / J,
    then chan = rng(12345).permutation(E) for QPSK, identity for (pi/2-)BPSK (blind_fmt chan_intlv); pn = 0. mod kept:
    export_w4 writes BPSK checks in virtual-bit indices 2m (blind_fmt inter = repeat(pos, 2): symbol m, I bit)."""
    fmt, crc = PLAIN[code]
    f = rpg.FMTS[fmt]
    A, E = f["A"], f["E"]
    rmc = rm.RMPolarCode(A, E, crc_len=crc, list_size=1, mode=f["mode"] if f["force"] else None)
    N, J, U = rmc.N, rmc.J, rmc.U
    P = J[U:] if rmc.mode == "puncture" else (J[:E] if rmc.mode == "shorten" else J.copy())
    chan = np.random.default_rng(12345).permutation(E) if f["mod"] == "qpsk" else np.arange(E)
    P = np.asarray(P, int)[chan]
    info = np.asarray(rmc.code.info_pos)
    crcG = rm.crc_matrix(A, crc)
    j = np.arange(N)
    G_A = (j[None, :] & ~info[:, None]) == 0              # K x N, row r = info_pos[r] (data first A, CRC last C)
    G_eff = (G_A[:A].astype(np.uint8) ^ ((crcG.astype(np.int32) @ G_A[A:].astype(np.int32)) % 2).astype(np.uint8)).astype(bool)
    pay = np.random.default_rng(7).integers(0, 2, (16, A)).astype(np.uint8)
    xe = (pay.astype(np.int32) @ G_eff.astype(np.int32)) % 2
    assert np.array_equal(rmc.encode(pay), xe), f"{code}: x != p G_eff"
    assert np.array_equal(rmc.encode_rm(pay)[:, chan], xe[:, P]), f"{code}: tx != x[P]"
    return dict(code=code, fmt=fmt, kind="plain", spec=f"crc{crc}", N=N, A=A, K=int(info.size), E=E, P=P,
                pn=np.zeros(E, np.uint8), info=info, G_A=G_A, G_eff=G_eff, designed=np.zeros((0, 2), int),
                meta=dict(twin="plain", crc=crc), mode=rmc.mode, mod=f["mod"])


def char_w4(C):
    """Exact w <= 4 of a code + the form of its w4 checks: a 2-dim subcube {f, f|a, f|b, f|a|b} of mother positions
    (some lift; x_f + x_{f|a} + x_{f|b} + x_{f|a|b} = XOR_{i superset-of f, a, b not in i} u_i: clean iff all those u_i
    frozen; the twin is the 1-dim case) keyed by wt(f), else 'other'."""
    D = Dual(C, time.time())
    D.isd_hits, D.isd_iters, D.isd_phit = {}, 0, {}
    D.low()
    kinds = {}
    for t in sorted(D.found[4]):
        mem = [sorted({int(C["P"][m]) for m in D.members[c]}) for c in t]
        k = "other"
        for pick in itertools.product(*mem):
            a, o = int(np.bitwise_and.reduce(pick)), int(np.bitwise_or.reduce(pick))
            if len(set(pick)) == 4 and bin(o ^ a).count("1") == 2:
                k = f"subcube wt(f) {bin(a).count('1')}"
                break
        kinds[k] = kinds.get(k, 0) + 1
    return dict(code=C["code"], D=D.D, w={w: len(D.found[w]) for w in range(1, 5)},
                w4_forms=dict(sorted(kinds.items())))


def char_all():
    out = {}
    for code in CODES:
        out[code] = char_w4(build(code))
    for fmt in ("id2", "id3", "id13"):
        out[f"{fmt}:k0"] = char_w4(k0_code(fmt))
    for k, v in out.items():
        print(f"{k}: D {v['D']} w1-4 {v['w']} w4 forms {v['w4_forms']}", flush=True)
    return out


def _js(o):
    if isinstance(o, dict):
        return {str(k): _js(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_js(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def merge():
    doc = {}
    for code in CODES:
        fn = os.path.join(PARTS, code.replace(":", "_") + ".json")
        if os.path.exists(fn):
            with open(fn) as fh:
                doc[code] = json.load(fh)
    fn = os.path.join(PARTS, "char.json")
    char = json.load(open(fn)) if os.path.exists(fn) else {}
    with open(JSON, "w") as fh:
        json.dump(dict(codes=doc, w4_char=char), fh, indent=1)
    write_md(doc, char)
    return doc


def write_md(doc, char=None):
    L = ["# Low-weight dual checks of the transmitted code (task D3, 2026-11-24)", "",
         "Pure GF(2) count (`sync_cfo/fs/dual_lowweight.py` -> `sync_cfo/fs/results/dual_lowweight.json`): feasibility "
         "of soft-syndrome scoring. G_tx = the payload -> transmitted-bit map of the blind receiver (fullsys/blind_fmt "
         "P = pos0[chan] / [pos0, pos0[rep]][chan], scrambler pn kept as the known constant c = XOR pn over the "
         "check), noCRC = the K = A + 24 info bits free, CRC = the A payload bits through CRC-24. Asserted against "
         "PolarCode.encode / RepCode.encode_rm. Checks counted BEYOND the twin relations = reduced checks: w distinct "
         "nonzero equal-column classes of G_A[:, P] (D of them) summing to 0 (a check is in the twin span iff every "
         "class holds an even number of its bits); each reduced check has prod |class| full-code lifts of weight w. "
         "The CRC dual contains the noCRC dual, so every search runs on the CRC columns and classifies "
         "noCRC / CRC-only. Exact: w1-w4 everywhere, w5 exhaustive (triple vs pair XOR), w6 exhaustive for D <= "
         f"{W6_DMAX} (id2, id3); id13 w6 = lower bound (Lee-Brickell ISD p <= 2 + mother-dual h_f sums + combos "
         "of found checks, box 20 min) with the per-word miss probability (1 - P_hit)^iters.", "",
         "## Codes", "",
         "| code | design | N / E | K / A | classes D | twin classes (sizes) | twin rank | designed twins (equal / "
         "within symbol) | extra equal pairs | zero cols | rank noCRC / CRC | rank bound beyond twins D - rank noCRC / "
         "CRC | all-ones in code noCRC / CRC | time s (box used) | ISD iters |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for code, r in doc.items():
        t = r["twins"]
        L.append(f"| {code} | {r['meta']['twin']} | {r['N']} / {r['E']} | {r['K']} / {r['A']} | {r['D']} | "
                 f"{t['classes_ge2']} ({t['sizes']}) | {t['twin_rank']} | {t['designed']} ({t['designed_equal']} / "
                 f"{t['designed_within_symbol']}) | {t['extra_pairs']} | {t['zero_cols']} | {r['rank_noCRC']} / "
                 f"{r['rank_CRC']} | {r['ub_new_noCRC']} / {r['ub_new_CRC']} | {r['allones_noCRC']} / "
                 f"{r['allones_CRC']} | {r['times']['total']} ({r['times']['box_used']}) | {r['isd_iters']} |")
    L += ["", "## Reduced checks per weight (beyond the twin span)", "",
          "count = reduced checks found with CRC-24 (exact unless marked '>='); noCRC = those that are also checks "
          "without the CRC; rank = cumulative GF(2) rank of the reduced checks of weight <= w (noCRC / CRC) vs the "
          "bound above; symbols = distinct QPSK symbols touched (union over all lifts); hist = lifts by number of "
          "distinct symbols; within = lifts on one symbol; full = lifts holding both bits of a symbol; c=1 = lifts "
          "with constant 1; ISD = Lee-Brickell hits / recall of the exact list / per-word miss probability.", "",
          "| code | w | count | noCRC / CRC-only | odd | lifts | rank noCRC / CRC | symbols | hist (n_sym: lifts) | "
          "within / cross | full | c=1 | ISD hits / recall / miss |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for code, r in doc.items():
        for w, v in r["weights"].items():
            rec = "-" if v["isd_recall"] is None else f"{v['isd_recall']:.3f}"
            miss = "-" if v["isd_miss"] is None else f"{v['isd_miss']:.1e}"
            cnt = f"{v['count']}" if v["exact"] else f">= {v['count']}"
            L.append(f"| {code} | {w} | {cnt} | {v['noCRC']} / {v['crc_only']} | {'yes' if v['odd'] else 'no'} | "
                     f"{v['lifts']} | {v['rank_noCRC']} / {v['rank_CRC']} | {v['sym_union']} | {v['lift_sym_hist']} | "
                     f"{v['within_one_symbol']} / {v['cross_symbol']} | {v['with_full_symbol']} | {v['const1']} | "
                     f"{v['isd_hits']} / {rec} / {miss} |")
    L += ["", "## Twin relations (weight 2 on the full code)", "",
          "| code | weight-2 checks | designed | within one symbol (all / designed) | designed with c = 1 |",
          "|---|---|---|---|---|"]
    for code, r in doc.items():
        t = r["twins"]
        L.append(f"| {code} | {t['weight2_checks']} | {t['designed']} | {t['pairs_within_symbol']} / "
                 f"{t['designed_within_symbol']} | {t['designed_const1']} |")
    L += ["", "## Times (s)", "", "| code | build | w1-4 | w5 | w6 | structured | combos | ISD | total |",
          "|---|---|---|---|---|---|---|---|---|"]
    for code, r in doc.items():
        t = r["times"]
        L.append(f"| {code} | {t['build']} | {t['w1_4']} | {t.get('w5', '-')} | {t.get('w6', '-')} | "
                 f"{t['structured']} | {t['combos']} | {t['isd']} | {t['total']} |")
    if char:
        L += ["", "## Form of the weight-4 checks, and the plain k0 codes (`--char`)", "",
              "subcube wt(f) = the 4 bits sit (in some lift) on a 2-dim subcube {f, f|a, f|b, f|a|b} of mother "
              "positions: x_f + x_{f|a} + x_{f|b} + x_{f|a|b} = XOR of u_i over i superset-of f with bits a, b clear, so "
              "it is a check iff all those u_i are frozen (the twin x_k + x_{k|b} is the 1-dim case). k0 = the adopted "
              "code with CRC-24 on OUR interleaver rng(12345) (no twin design).", "",
              "| code | D | w1 / w2 / w3 / w4 (exact) | w4 forms |", "|---|---|---|---|"]
        for k, v in char.items():
            w = v["w"]
            L.append(f"| {k} | {v['D']} | {w['1']} / {w['2']} / {w['3']} / {w['4']} | {v['w4_forms']} |")
    L += ["", "## Verdict (2026-11-24 run)", "",
          "- Predictions hold: weight-2 beyond the twins = 0 in every code, with and without CRC (the equal-column "
          "classes are exactly the designed twins / rep copies: 96 / 100 / 96 / 73 / 96, all on one diagonal symbol), "
          "and the CRC-24 adds NO check of weight <= 6 (CRC-only = 0 at every weight; with the CRC the all-ones word "
          "leaves the code, so odd checks become possible, but there is none of weight 1, 3 or 5).",
          "- Without the CRC all checks are even (u_{N-1} is information, the PiCode condition: all-ones is a "
          "codeword), so w1 / w3 / w5 = 0 is structural; with the CRC-24 they are 0 by the exhaustive count.",
          "- Beyond the twins the first low-weight checks are at weight 4: 2-dim subcube relations of the polar "
          "transform (the twin's next order), cross-symbol (4 distinct QPSK symbols per check under the random "
          "interleaver, 1 check in id3 rpz / id13 twc holds a full symbol): id2 twc 0, id3 tz0 108, id3 rpz 48, id13 "
          "twc 445 (rank 374; 58 of them not a subcube: twin-reduced), id13 rpz 384, i.e. at most ~1/4 of the rank bound (D - rank: 144 / 540 / 544 / 1927 / "
          "1904 with CRC). The plain k0 codes already have them (id2 32, id3 144, id13 392): they are no product of "
          "the twin designs (id2 k12 removes all 32, id3 tz0 / rpz cut 144 to 108 / 48).",
          "- Weight 5 = 0 everywhere (exhaustive); weight 6 = 0 for id2 / id3 (exhaustive) and id13 rpz (ISD, per-word "
          "miss probability ~1e-30), id13 twc >= 576 (ISD + mother-dual; only 4 new dimensions beyond its weight-4 "
          "checks, on 79 symbols).",
          "- Soft-syndrome scoring would therefore have, per packet, the twins (weight 2) plus 48-445 cross-symbol "
          "weight-4 checks (each covering 4 symbols, half of them with constant c = 1); a weight-4 parity is far "
          "noisier than a twin at low SNR (tanh product of 4 LLRs), so their use is a separate question.", ""]
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    with open(MD, "w", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")


def export_w4(code):
    """(2026-11-24, D3 step 2; --export-w4) the exact weight-4 reduced checks of a code (Dual.low on the CRC columns) as
    an explicit list for small_rx pk_w4: per check its 4 classes (sent-bit indices m; a class = equal G columns = one
    mother bit, e.g. a rep copy pair), their mother positions P[m] (small_rx asserts them against blind_fmt pos), the
    constant c = XOR pn over one lift (sent-bit domain: XOR tx = c; on the unscrambled virtual bits XOR = 0), the symbol
    span / lags of the representatives. Verified on 64 random payloads (G_eff): every lift's sent-bit XOR = c and every
    class's members carry one bit. -> results/dual_w4_<code>.json"""
    C = build(code)
    D = Dual(C, time.time())
    D.low()
    P, pn = C["P"], C["pn"].astype(np.uint8)
    pay = np.random.default_rng(8).integers(0, 2, (64, C["A"])).astype(np.uint8)
    x = ((pay.astype(np.int32) @ C["G_eff"].astype(np.int32)) % 2).astype(np.uint8)
    tx = x[:, P] ^ pn[None]
    bp = C.get("mod", "qpsk") != "qpsk"                   # (PLAIN BPSK) sent bit m = symbol m -> virtual bit 2m
    checks, pos, cst, lag = [], [], [], []
    for t in sorted(D.found[4]):
        mem = [sorted(int(m) for m in D.members[c]) for c in t]
        for cl in mem:                                     # one mother bit per class (virtual bits equal)
            assert all(np.array_equal(x[:, P[cl[0]]], x[:, P[m]]) for m in cl), (code, t, "class bits differ")
        lift = [cl[0] for cl in mem]
        c = int(np.bitwise_xor.reduce(pn[lift]))
        for lf in itertools.product(*mem):
            assert (np.bitwise_xor.reduce(tx[:, list(lf)], axis=1) == int(np.bitwise_xor.reduce(pn[list(lf)]))).all(), \
                (code, t, lf, "sent-bit XOR != c")
        checks.append([[2 * m for m in cl] for cl in mem] if bp else mem)
        pos.append([[int(P[m]) for m in cl] for cl in mem])
        cst.append(c)
        sy = sorted(m if bp else m // 2 for m in lift)
        lag.append([sy[0], sy[-1] - sy[0]])
    out = dict(code=code, written="2026-11-24", E=int(C["E"]), n_sym=int(C["E"] if bp else C["E"] // 2), H=len(checks),
               checks=checks, pos=pos, c=cst, span=lag, D=int(D.D), note="classes of sent-bit indices (blind_fmt / "
               "small_rx virtual bit index m: symbol m // 2, I / Q = m % 2); XOR over any lift of the sent bits = c; of "
               "the virtual bits = 0")
    if bp:                                                 # (PLAIN BPSK) the index convention, for w4_load / ls_quads
        out.update(written="2026-11-25", mod=C["mod"], note="BPSK: checks = VIRTUAL bit indices 2m (sent bit m = "
                   "symbol m, its I bit; blind_fmt inter = repeat(pos, 2), so inter[2m] = pos[m] = the json pos); "
                   "small_rx w4_load / ls_quads need pos = bc.FMT.inter for it (bc.FMT.pos is per sent bit); "
                   "XOR over any lift = 0 (pn = 0)")
    if code in K0:                                         # (k0) the plain code of h2_frontend_diag --code k0
        out.update(written="2026-11-26", twin="k0 (no moved bits, pn 0, CRC-24, GA at DESIGN_SNR, rng(12345) interleaver)")
    p = os.path.join(td.RES, f"dual_w4_{code.replace(':', '_')}.json")
    with open(p + ".tmp", "w") as fh:
        json.dump(_js(out), fh)
    os.replace(p + ".tmp", p)
    print(f"export-w4 {code}: {len(checks)} weight-4 checks (D {D.D}), verified on 64 payloads -> {p}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export-w4", nargs="*", default=[], help="(D3 step 2) codes -> results/dual_w4_<code>.json "
                    "(the explicit weight-4 check list for small_rx pk_w4)")
    ap.add_argument("--codes", nargs="*", default=[], help=f"codes of {list(CODES)}")
    ap.add_argument("--box", type=float, default=BOX, help="w5 / w6 search box per code (s)")
    ap.add_argument("--merge", action="store_true", help="merge the parts -> json + md")
    ap.add_argument("--char", action="store_true", help="w4 forms + the k0 baselines -> parts/char.json (exact w <= 4)")
    a = ap.parse_args()
    os.makedirs(PARTS, exist_ok=True)
    if a.char:
        with open(os.path.join(PARTS, "char.json"), "w") as fh:
            json.dump(_js(char_all()), fh, indent=1)
    for code in a.codes:
        r = _js(run(code, a.box))
        with open(os.path.join(PARTS, code.replace(":", "_") + ".json"), "w") as fh:
            json.dump(r, fh, indent=1)
    if a.merge:
        merge()
    for code in a.export_w4:
        export_w4(code)


if __name__ == "__main__":
    main()
