"""
Self-test of the DVB-RCS2 TC-LM implementation (no BLER simulation; runs in a few seconds):
CRC check values, scrambler start, circulation table (GF(2) rebuild + end state = start state), interleaver
permutations (both directions), burst lengths / pilots, Eb/N0 conversions (lit_rcs2_fullsystem.md 0,
lit_turbo_db.md 5), noiseless round trip through the RRC chain for every waveform.

    py fullsys/selftest_rcs2.py
"""

import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import rcs2, turbo_db as tdb          # noqa: E402

T0 = time.time()
N_FAIL = 0


def check(name, ok, detail=""):
    global N_FAIL
    N_FAIL += not ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


# CRC (cl. 7.3.4): catalogue check values of "123456789"
b = rcs2.bytes_to_bits(b"123456789")
c32 = rcs2.bits_to_int(rcs2.crc_bits_serial(b, 32)[0])
c16 = rcs2.bits_to_int(rcs2.crc_bits_serial(b, 16)[0])
check("CRC-32/MPEG-2 check = 0x0376E6E7", c32 == 0x0376E6E7, f"0x{c32:08X}")
check("CRC-16 (0x8005, init 0) check = 0xFEE8 (CRC-16/UMTS)", c16 == 0xFEE8, f"0x{c16:04X}")
rng = np.random.default_rng(1)
x = rng.integers(0, 2, (5, 952)).astype(np.int8)
check("CRC linear form = serial CRC", np.array_equal(rcs2.crc_bits(x, 32), rcs2.crc_bits_serial(x, 32)))

# energy dispersal (cl. 7.3.3): init 100101010000000 -> DVB-S randomiser start 0x03F6 [derived]
p = rcs2.prbs(16)
check("PRBS first 16 bits = 0x03F6", rcs2.bits_to_int(p) == 0x03F6, "".join(map(str, p)))

# circulation (cl. 7.3.5.1.2)
check("circulation table = GF(2) rebuild (14 x 16)", np.array_equal(tdb.circ_table_gf2(), tdb.CIRC))
ok = True
for N in (56, 152, 236, 492, 752, 1056, 2396):
    u = rng.integers(0, 4, (20, N))
    Y, W, sc = tdb.rsc_encode_circular(u)                         # asserts end == start internally
    _, _, s_end = tdb.rsc_encode(u, sc)
    ok &= bool(np.array_equal(s_end, sc))
check("circular encoder ends in its start state (random inputs, 7 sizes)", ok)

# interleaver (cl. 7.3.5.1.1)
for d in tdb.INTERLEAVER_DIRS:
    ok = True
    for key, w in rcs2.WAVEFORMS.items():
        src, sw = tdb.interleaver(w["N"], w["P"], w["Q"], d)
        ok &= bool(np.array_equal(np.sort(src), np.arange(w["N"])))
        ok &= bool(np.all(src[0::2] % 2 == 1) and np.all(src[1::2] % 2 == 0))   # odd/even rule
        ok &= int(sw.sum()) == w["N"] // 2
    check(f"interleaver '{d}' is a permutation for every waveform (odd/even rule, N/2 swaps)", ok)
w = rcs2.WAVEFORMS[13]
I = {d: tdb.interleaver(w["N"], w["P"], w["Q"], d) for d in tdb.INTERLEAVER_DIRS}
pi = tdb.arp(w["N"], w["P"], w["Q"])
check("'aff3ct' = inverse of Pi, swaps natural even couples (interleaved odd j)",
      np.array_equal(I["aff3ct"][0][pi], np.arange(w["N"])) and np.array_equal(I["aff3ct"][1], np.arange(w["N"]) % 2 == 1))
check("'en' = EN Eq. 7-4 read form, swaps interleaved even j (natural odd); 'en-natswap' swaps natural even",
      np.array_equal(I["en"][0], pi) and np.array_equal(I["en"][1], np.arange(w["N"]) % 2 == 0)
      and np.array_equal(I["en-natswap"][1], pi % 2 == 0))

# bursts (Table A-1)
for key, L in ((3, 536), (13, 1616), (14, 1616), (42, 3236), ("A12", 1504), ("A13", 2256), ("A23", 1128)):
    wf = rcs2.Waveform(key)
    pil = "-" if wf.pilot_bits is None else "".join(map(str, wf.pilot_bits))
    check(f"ID {key}: burst {wf.L} = {L}, data {wf.n_data}, known {len(wf.known_idx)}, pilot bits {pil}",
          wf.L == L and (wf.pilot_bits is None or not wf.pilot_bits.any()))

# Eb/N0 per information bit, all burst symbols charged (lit_rcs2_fullsystem.md 0)
for key, e3, e5 in ((13, 1.50, 1.79), (14, 1.90, 2.12), (42, 1.50, 1.79), (3, 2.68, 3.17)):
    wf = rcs2.Waveform(key)
    a, b5 = wf.ebn0(rcs2.REF_PER[key][1e-3]), wf.ebn0(rcs2.REF_PER[key][1e-5])
    check(f"ID {key}: Eb/N0 @1e-3 {a:.2f} dB, @1e-5 {b5:.2f} dB", round(a, 2) == e3 and round(b5, 2) == e5,
          f"table {e3:.2f} / {e5:.2f}")
for rate, es in (("1/2", 1.31), ("1/3", -1.05), ("2/3", 3.36)):
    ref = rcs2.REF_AFF3CT[rate]
    eb = {"1/2": 1.4, "1/3": 0.8, "2/3": 2.2}[rate]
    wf = rcs2.Waveform(ref["wf"])
    v = wf.esn0_from_aff3ct(eb)
    check(f"AFF3CT rate {rate}: Eb/N0 {eb} -> Es/N0 {v:.2f} dB (n_coded {wf.n_coded})",
          round(v, 2) == es and wf.n_coded == ref["n_coded"], f"lit {es:.2f}")

# noiseless round trip through the full chain (upsample, RRC 0.20, AWGN at 60 dB, MF, downsample)
import txrx_chain                                   # noqa: E402

for key, d, algo in ((3, "aff3ct", "maxlog"), (13, "aff3ct", "maxlog"), (14, "aff3ct", "maxlog"),
                     (42, "aff3ct", "maxlog"), ("A12", "aff3ct", "maxlog"), ("A13", "aff3ct", "maxlog"), ("A23", "aff3ct", "maxlog"),
                     (13, "en", "maxlog"), (13, "en-natswap", "maxlog"), (3, "aff3ct", "logmap")):
    wf = rcs2.Waveform(key, direction=d)
    B, snr = 3, 60.0
    pdu = rng.integers(0, 2, (B, wf.k)).astype(np.int8)
    s, u = rcs2.tx(pdu, wf)
    r = txrx_chain.transmit(s, np.zeros(B), np.zeros(B), snr, rng, beta=rcs2.ROLLOFF)
    out = rcs2.rx(r, wf, 10 ** (-snr / 10), algo=algo, iters=2, early_stop=True)
    check(f"round trip ID {key} ({d}, {algo}): CRC pass, PDU equal, iters {out['iters'].tolist()}",
          bool(out["crc"].all() and np.array_equal(out["pdu"], pdu) and np.array_equal(out["u"], u)))
# decoder uses the parity of both constituents: erase the systematic LLRs of 20 % of the couples and flip 2 % of the
# remaining systematic bits (noiseless parity); systematic-only decisions would fail, the turbo decoder must not
for key, d, algo, sfk in ((13, "aff3ct", "maxlog", {}), (13, "en", "maxlog", {}), (13, "en-natswap", "maxlog", {}),
                          (14, "aff3ct", "maxlog", {}), (3, "aff3ct", "logmap", {}), (13, "aff3ct", "maxlog", {"sf": 0.7}),
                          (13, "aff3ct", "maxlog", {"sf_low_iters": 2})):
    wf = rcs2.Waveform(key, direction=d)
    B = 2
    u = rng.integers(0, 2, (B, wf.K)).astype(np.int8)
    Z1, Z2 = wf.code.encode(u)
    Ls = 4.0 * (1 - 2 * u)
    er = np.repeat(rng.random((B, wf.code.N)) < 0.2, 2, axis=1)
    fl = (rng.random((B, wf.K)) < 0.02) & ~er
    Ls[er] = 0.0
    Ls[fl] *= -1
    hard_ok = np.array_equal((Ls < 0) & ~er, u.astype(bool))
    bh, info = wf.code.decode(Ls, 4.0 * (1 - 2 * Z1), 4.0 * (1 - 2 * Z2), iters=6, algo=algo, **sfk)
    check(f"erasure + flip recovery ID {key} ({d}, {algo}, {sfk or 'adaptive'}): {er[:, ::2].sum()} couples erased, "
          f"{fl.sum()} flips",
          np.array_equal(bh, u) and not hard_ok)

for de, dd in (("en", "aff3ct"), ("en-natswap", "en")):          # negative control: wrong interleaver must fail
    we, wd = rcs2.Waveform(13, de), rcs2.Waveform(13, dd)
    u = rng.integers(0, 2, (2, 984)).astype(np.int8)
    Z1, Z2 = we.code.encode(u)
    Ls = 4.0 * (1 - 2 * u)
    Ls[np.repeat(rng.random((2, 492)) < 0.2, 2, axis=1)] = 0.0
    bh, _ = wd.code.decode(Ls, 4.0 * (1 - 2 * Z1), 4.0 * (1 - 2 * Z2), iters=6)
    check(f"negative control: '{de}' codeword decoded with the '{dd}' interleaver fails", not np.array_equal(bh, u))

u13 = rng.integers(0, 2, (2, 984)).astype(np.int8)
Z2s = {d: rcs2.Waveform(13, d).code.encode(u13)[1] for d in tdb.INTERLEAVER_DIRS}
check("the three interleaver readings give pairwise different Z2 (ID 13)",
      all(not np.array_equal(Z2s[a], Z2s[b]) for a in Z2s for b in Z2s if a < b))
check("--fmt map: aff3ct-N3008 -> A12 (ID 14 code), N4512 -> A13, N2256 -> A23",
      rcs2.FMT == {"aff3ct-N3008": "A12", "aff3ct-N4512": "A13", "aff3ct-N2256": "A23"}
      and rcs2.Waveform("A12").code.src.tolist() == rcs2.Waveform(14).code.src.tolist())

m = tdb.macs(492, 8, n_sym=1476, bps=2)
check("macs ID 13: 411 ops/couple, crit = 2*8*492*(13+8) + 6*492/32 + 4*1476/32, per bit over k = 952",
      m["ops_couple"] == 411 and abs(m["crit"] - (2 * 8 * 492 * 21 + 6 * 492 / 32 + 4 * 1476 / 32)) < 1e-9
      and abs(m["per_info_bit"] - m["total"] / 952) < 1e-9 and m["llr"] == 5904, f"crit {m['crit']:.1f}")
from fullsys.run_rcs2 import iters_es_equiv             # noqa: E402
v = iters_es_equiv([1, 2, 1, 0, 0, 0, 0, 0, 1], 8)      # never, 2 x it 1 (-> 2), 1 x it 2, 1 x it 8
check("iters_es_equiv = mean(max(first pass, 2), 8 if never)", abs(v - (8 + 2 * 2 + 2 + 8) / 5) < 1e-12, f"{v:.2f}")

for key in (3, 13, 14, 42):
    wf = rcs2.Waveform(key)
    mk = dict(n_sym=wf.n_data, bps=wf.m)
    m, t = tdb.macs(wf.code.N, 8, **mk), tdb.macs(wf.code.N, 8, model="tr", **mk)
    ml = tdb.macs(wf.code.N, 8, algo="logmap", **mk)
    print(f"ops/decode ID {key} (N = {wf.code.N}, 8 it): max-log {m['total'] / 1e6:.2f} M "
          f"({m['per_info_bit']:.0f}/info bit, crit {m['crit'] / 1e3:.1f} k/core), TR model {t['total'] / 1e6:.2f} M, "
          f"log-MAP {ml['total'] / 1e6:.2f} M (crit {ml['crit'] / 1e3:.1f} k)")

dt = time.time() - T0
print(f"{N_FAIL} failures, {dt:.1f} s")
sys.exit(1 if N_FAIL else 0)
