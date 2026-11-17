"""
Self-test of fullsys/vde.py + turbo_vde.py (no channel simulation): M.2092-2 A3-8 worked example bit-exact (CRC,
turbo encoder Link 5, scrambler, pi/4-QPSK symbols incl. syncword and Link ID; strings loaded from the standard's
.txt), Gold tables vs the .txt + linear complexity 22, interleaver permutations, tail termination, noiseless round
trip of every link, burst lengths and the Link 32 Eb/N0 bookkeeping.   py fullsys/selftest_vde.py
"""

import os
import re
import sys
import time
from math import gcd

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from fullsys import turbo_vde as tv  # noqa: E402
from fullsys import costmodel as cm  # noqa: E402
from fullsys import vde  # noqa: E402

TXT = os.path.join(_ROOT, "BLIND_IMPLEMENTATION", "testing", "results", "standards", "ITU-R_M.2092-2_2026.txt")
T0 = time.time()


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg, flush=True)
    if not cond:
        ok.failed += 1


ok.failed = 0


def load_a38(lines):
    """(b)..(e) bit strings and the (f) symbol list of A3-8, parsed from the .txt."""
    a = next(i for i, l in enumerate(lines) if l.startswith("A3-8 Example") and i > 3000)
    out, key = {}, None
    for l in lines[a:]:
        s = l.strip()
        m = re.match(r"^\(([b-f])\)", s)
        if m:
            key = m.group(1)
            if key == "f":
                break
            out[key] = ""
        elif key and re.fullmatch(r"[01]+", s):
            out[key] += s
    f0 = next(i for i in range(a, len(lines)) if "-- Syncword symbols" in lines[i])
    f1 = next(i for i in range(f0, len(lines)) if lines[i].strip() == "Annex 4")
    blob = re.sub(r"\s+", "", "".join(lines[f0:f1]))
    sym = [complex(float(x), float(y)) for x, y in re.findall(r"\(([+-]\d\.\d),([+-]\d\.\d)\)", blob)]
    return out, np.array(sym)


def load_gold(lines):
    a = next(i for i, l in enumerate(lines) if "Gold spreading sequences" in l and i > 5000)
    groups, cur = [], []
    for l in lines[a + 1:a + 40]:
        s = l.replace("SS0", "").replace("SS1", "").strip()
        if re.fullmatch(r"([0-9A-F]{2}-)*[0-9A-F]{2}-?", s):
            cur.append(s)
        elif not s and cur:
            groups.append(cur)
            cur = []
        if "direct spreading sequence" in l:
            break
    if cur:
        groups.append(cur)
    return ["".join(g).replace("-", "") for g in groups[:2]]


def lin_complexity(s):
    """Berlekamp-Massey over GF(2)."""
    s = np.asarray(s, np.int64)
    n = len(s)
    c, b = np.zeros(n + 1, np.int64), np.zeros(n + 1, np.int64)
    c[0] = b[0] = 1
    L, m = 0, -1
    for N in range(n):
        d = (s[N] + int(np.dot(c[1:L + 1], s[N - L:N][::-1]))) & 1
        if d:
            t = c.copy()
            c[N - m:] ^= b[:n + 1 - (N - m)]
            if L <= N // 2:
                L, m, b = N + 1 - L, N, t
    return L


def main():
    lines = open(TXT, encoding="latin-1").read().splitlines()
    rng = np.random.default_rng(1)

    # ---- A3-8 worked example (Link 5) ----
    ex, sym = load_a38(lines)
    B_, C_, D_, E_ = (vde.bits_of(ex[c]) for c in "bcde")
    ok([len(B_), len(C_), len(D_), len(E_)] == [256, 288, 394, 394], f"A3-8 lengths {len(B_)}/{len(C_)}/{len(D_)}/{len(E_)}")
    crc = vde.crc_register(B_)
    ok(crc == 0x5AF2947C and np.array_equal(C_[:256], B_) and int("".join(map(str, C_[256:])), 2) == crc,
       f"CRC-32 of the example = 0x{crc:08X} (expected 0x5AF2947C), appended MSB first")
    ok(vde.crc_register(C_) == 0, "CRC register over data + CRC = 0")
    ok(np.array_equal(vde.CRC(256).register(B_[None])[0], C_[256:]), "vectorised CRC = LFSR CRC")
    p5 = vde.LINKS[5]
    code5 = tv.TurboVDE(288, p5["k1"], p5["k2"], p5["primes"], p5["punct"], p5["tail"])
    d = code5.encode(C_[None])[0]
    ok(code5.n == 394 and np.array_equal(d, D_), f"turbo encoder Link 5 (ID 8 / 8b) = A3-8 (d), {(d != D_).sum()} bit diffs")
    scr = vde.scrambler_seq(394)
    ok(int("".join(map(str, scr[:32])), 2) == 0x03F60834, f"scrambler first 32 bits 0x{int(''.join(map(str, scr[:32])), 2):08X}")
    ok(np.array_equal(D_ ^ scr, E_), "scrambled = A3-8 (e)")
    L5 = vde.VDELink(5)
    st = L5.encode_bits(B_[None, :256 - 0][:, :L5.kpay])
    ok(np.array_equal(st["chan"][0], E_), "VDELink(5).encode_bits = A3-8 (e)")
    x, _ = L5.tx(B_[None])
    ok(len(sym) == 240 and np.allclose(np.round(x[0].real, 1), sym.real) and np.allclose(np.round(x[0].imag, 1), sym.imag),
       f"A3-8 (f) {len(sym)} symbols: syncword TER27 + Link ID 5 (RM, D0 = MSB) + 197 pi/4-QPSK data symbols")

    # ---- Gold sequences ----
    g = load_gold(lines)
    ok(g == [vde.GOLD_HEX["SS0"], vde.GOLD_HEX["SS1"]], "Gold SS0 / SS1 hex = Table 62 in the .txt (256 bytes each)")
    lc = [lin_complexity(vde.gold_chips(n)) for n in ("SS0", "SS1")]
    ok(lc == [22, 22], f"Gold 2047-chip linear complexity {lc} (2 x degree 11)")
    ok(vde.gold_chips("SS0")[:16].tolist() == [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1], "SS0 starts 00000100 01100001")

    # ---- interleavers ----
    for lid, p in vde.LINKS.items():
        pi = tv.ccsds_interleaver(p["k1"], p["k2"], p["primes"])
        ok(np.array_equal(np.sort(pi), np.arange(p["k"])), f"turbo interleaver Link {lid} ({p['k1']} x {p['k2']}) is a permutation")
        if p["ileave"]:
            M, N, Ar, Br, Ac, Bc, IB = p["ileave"]
            ci = vde.chan_interleaver(M, N, Ar, Br, Ac, Bc)
            ok(np.array_equal(np.sort(ci), np.arange(M * N)) and gcd(Ar, M) == 1 and gcd(Ac, N) == 1,
               f"channel interleaver Link {lid} M {M} N {N} (Ar {Ar} Br {Br} Ac {Ac} Bc {Bc}) is a permutation")
    pi32 = tv.ccsds_interleaver(2, 156, vde.LINKS[32]["primes"])
    j = np.arange(156)
    ok(np.array_equal(pi32[0::2], 2 * ((37 * j) % 156) + 1) and np.array_equal(pi32[1::2], 2 * ((37 * j + 21) % 156)),
       "Link 32 interleaver = 2 (37 j + 21 m mod 156) + 2 - m (k1 = 2: only p1 used)")

    # ---- tail termination: the plain recursion fed with u + tail X ends in state 0 (both RSCs) ----
    for lid in (5, 32, 33):
        p = vde.LINKS[lid]
        c = tv.TurboVDE(p["k"], p["k1"], p["k2"], p["primes"], p["punct"], p["tail"])
        u = rng.integers(0, 2, (3, p["k"]), dtype=np.int8)
        s = c.streams(u)
        for name, uin, tx in (("RSC1", u, s[:, p["k"]:p["k"] + 3, 0]), ("RSC2", u[:, c.pi], s[:, p["k"] + 3:, 3])):
            a1 = a2 = a3 = np.zeros(3, np.int8)
            for t in range(p["k"] + 3):
                b = uin[:, t] if t < p["k"] else tx[:, t - p["k"]]
                a = b ^ a2 ^ a3
                a1, a2, a3 = a, a1, a2
            ok(not (a1 | a2 | a3).any(), f"Link {lid} {name} ends in state 0 after the 3 tail clocks")
        ok(c.n == c.n_data + {"8b": 10, "2e": 21, "4a": 15}[p["tail"]], f"Link {lid} tail {p['tail']} bits")

    # ---- burst lengths and layout ----
    want = {5: 240, 11: 480, 17: 1920, 26: 80343, 32: 1641, 33: 13143, 34: 13122, "M2435": 188}
    pil = {26: 2940, 32: 180, 34: 480}
    links = {}
    for lid in want:
        L = vde.VDELink(lid)
        links[lid] = L
        ok(L.n_sym == want[lid] and len(L.data_pos) == L.n_data_sym, f"Link {lid}: burst {L.n_sym} symbols, "
           f"{L.n_data_sym} data, {L.n_chan} channel bits, {len(L.pilot_pos)} pilots, {len(L.sync_pos)} sync symbols")
        if lid in pil:
            ok(len(L.pilot_pos) == pil[lid], f"Link {lid}: {pil[lid]} pilots (Tables 10-11)")
    L32 = links[32]
    ok(L32.n_chan == 1269 and L32.code.n == 1269 and L32.n_el == 1641 * 8 and L32.kpay == 280,
       "Link 32: 312 -> 1248 + 21 tail = 1269 channel bits, 1641 x 8 chips, 280 payload bits")
    ok(L32.sync_pos.tolist()[::48] == [0, 531, 1062, 1593] and L32.pilot_pos[:3].tolist() == [51, 59, 67]
       and L32.pilot_pos[59] == 523, "Link 32 syncwords at 0 531 1062 1593, pilots 51 59 67 ... 523")
    p26 = links[26].pilot_pos
    ok(p26[:2].tolist() == [40, 67] and 2254 in p26 and 2268 not in p26 and links[26].n_sym - 1 - p26[-1] == 31,
       "Link 26 pilots 40 67 ... 2254, 31 symbols after the last pilot (A5-2.10 example)")
    e = L32.ebn0_db(-4.5)
    ok(abs(e - 3.18) < 0.005, f"Link 32 Eb/N0 at Es/N0 -4.5 dB = {e:.3f} dB per payload bit "
       f"({L32.ebn0_db(-4.5, info='k'):.3f} dB per k = 312)")

    # ---- noiseless round trip (elements -> despread -> LLR -> decode -> CRC) ----
    for lid, L in links.items():
        for algo in (("maxlog", "logmap") if lid in (32, "M2435") else ("maxlog",)):
            pay = rng.integers(0, 2, (2 if L.n_sym < 20000 else 1, L.kpay), dtype=np.int8)
            x, _ = L.tx(pay)
            out = L.rx(x, 0.5, iters=2, algo=algo)
            ok(np.array_equal(out["payload"], pay) and out["crc_ok"].all(),
               f"round trip Link {lid} {algo}: payload {L.kpay} bits ok, iters {out['iters'].max()}, ops/burst {out['ops'][0]:.3g}")
    L34b = vde.VDELink(34, crc_mode="block")
    pay = rng.integers(0, 2, (1, L34b.kpay), dtype=np.int8)
    out = L34b.rx(L34b.tx(pay)[0], 0.5, iters=2)
    ok(np.array_equal(out["payload"], pay) and out["crc_ok"].all(), "round trip Link 34 crc_mode='block'")
    pay = rng.integers(0, 2, (2, L32.kpay), dtype=np.int8)
    x, _ = L32.tx(pay)
    x[1, :8 * 300] *= -1                                       # corrupt frame 1 heavily: CRC must flag it
    out = L32.rx(x, 0.5, iters=3)
    ok(out["crc_ok"][0] and not out["crc_ok"][1] and out["iters"][1, 0] == 3, "Link 32 corrupted burst: CRC fails, no early stop")
    c32 = L32.code                                             # erasure channel (no noise): 60 % of the coded bits
    u = rng.integers(0, 2, (4, 312), dtype=np.int8)             # erased -> rate 0.61 on the rest: needs the extrinsic
    llr = 8.0 * (1 - 2 * c32.encode(u).astype(float))           # exchange (one RSC alone has too few bits)
    llr[rng.random(llr.shape) < 0.6] = 0.0
    for algo in ("maxlog", "logmap"):
        b, used, _ = c32.decode(llr, iters=8, algo=algo, stop=lambda bb, rr, uu=u: (bb == uu[rr]).all(1))
        b1, _, _ = c32.decode(llr, iters=1, algo=algo)
        ok(np.array_equal(b, u) and used.max() > 1 and not np.array_equal(b1, u),
           f"Link 32 turbo, 60 % erasures, {algo}: 1 iteration fails, decoded after {used.tolist()} iterations")
    # ---- cost model (fullsys/costmodel.py) ----
    sm, sl = cm.siso_step_ops("maxlog")["total"], cm.siso_step_ops("logmap")["total"]
    ok(sm == 118 and sl == 177 and tv.OPS_PER_STEP == {"maxlog": 118, "logmap": 177},
       f"SISO step ops max-log {sm} (scaled) / log-MAP {sl} (max* = 1 + {cm.MAXSTAR_EXTRA}, normalisation S - 1)")
    m1 = tv.macs(312, 1, "maxlog")
    ok(m1 == 2 * 315 * 118 + 312 * 3 and tv.macs(312, 2, "maxlog", early=True) == 2 * (2 * 315 * 118 + 312 * 4),
       f"turbo ops k 312, 1 iteration: {m1 / 312:.1f} / info bit max-log, {tv.macs(312, 1, 'logmap') / 312:.1f} log-MAP; "
       f"early stop adds APP + CRC per iteration")
    c8 = tv.crit(312, 8, "logmap", early=True)
    ok(c8 == 2 * 8 * 315 * (6 + 3 + 3) + 8 * (39 + 9) and tv.crit(312, 8, "logmap", model="window") > c8,
       f"crit path k 312 log-MAP 8 it. early: state-parallel {c8}, windowed {tv.crit(312, 8, 'logmap', model='window')}")
    fo = L32.frontend_ops()
    ok(fo == 4 * 13128 + 2 * 13128 + 1269 and L32.despread_ops() == 2 * 13128,
       f"Link 32 front end {fo} ops (de-rotation 4 / chip, despread 2 / chip, LLR 1 / bit), crit {L32.frontend_crit()}")

    # ---- bracketing interleavers (M2435) ----
    for f1, f2 in ((5, 22), (21, 44)):
        q = tv.qpp_interleaver(88, f1, f2)
        ok(np.array_equal(np.sort(q), np.arange(88)), f"QPP K 88 f1 {f1} f2 {f2} is a permutation")
    for sd in (0, 1, 2):
        sr = tv.srandom_interleaver(88, None, sd)
        spread = min(abs(int(sr[i]) - int(sr[j])) for i in range(88) for j in range(max(0, i - 6), i))
        ok(np.array_equal(np.sort(sr), np.arange(88)) and spread > 6, f"S-random k 88 S 6 seed {sd}: min spread {spread}")
    for il in ("srandom", "qpp", "random"):
        Lm = vde.VDELink("M2435", interleaver=il, perm_seed=1)
        pay = rng.integers(0, 2, (2, 88), dtype=np.int8)
        out = Lm.rx(Lm.tx(pay)[0], 0.5, iters=2, algo="logmap")
        ok(np.array_equal(out["payload"], pay), f"round trip M2435 interleaver {il}")
    print(f"{'ALL PASS' if ok.failed == 0 else f'{ok.failed} FAILED'} ({time.time() - T0:.1f} s)", flush=True)
    return ok.failed


if __name__ == "__main__":
    sys.exit(main())
