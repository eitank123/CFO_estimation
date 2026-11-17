"""
Self-test of fullsys/polar_rm.py (no channel noise, no BLER; ~5 s):  py fullsys/selftest_polar_rm.py

    1 baseline: polar.PolarCode default == the git HEAD polar.py (info set, encode) at N = 2048, A = 205 / 307 / 819 /
      1024, CRC-16; == an explicit info_pos + crc_matrix; == RMPolarCode(crc_len=16) at E = N (mode none); CRC-16 /
      CRC-32 check values; crc_matrix == polar's row-by-row CRC matrix
    2 targets (CRC-32, user 2026-11-17): mode, N, len(e) = E, N - K frozen, rm / extra u frozen, exact rate-recovery
      inverse, noiseless round trip (CRC pass, data equal), shortened x positions always 0, negative control
      (shortened LLRs -LLR_BIG -> no correct accept)
    3 repetition, PiCode guards, N = 4096 decoder bookkeeping (fz_stop / fz_q)
"""

import os
import subprocess
import sys
import time
import types

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
from fullsys import polar_rm as rm  # noqa: E402
from polar import PolarCode, crc_remainder  # noqa: E402

TARGETS = [  # (name, K incl. CRC-32, E, mode override, expected mode, N)
    ("RCS2 ID 13/42", 984, 2952, None, "puncture", 4096),
    ("RCS2 ID 14", 1504, 3008, None, "shorten", 4096),
    ("RCS2 ID 14 forced", 1504, 3008, "puncture", "puncture", 4096),
    ("RCS2 ID 3", 304, 912, None, "puncture", 1024),
    ("VDE-SAT L32", 312, 1269, None, "puncture", 2048),
]
N_SYM = {"RCS2 ID 13/42": 1476, "RCS2 ID 14": 1504, "RCS2 ID 14 forced": 1504, "RCS2 ID 3": 456,
         "VDE-SAT L32": 1269}                                   # QPSK E / 2 (ID 42 pi/2-BPSK: 2952), VDE BPSK E
FAILS = []


def check(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond:
        FAILS.append(msg)


def head_polar():
    """polar.py as committed at git HEAD (the behaviour before the info_pos / crc_G hooks), or None."""
    try:
        src = subprocess.run(["git", "-C", _ROOT, "show", "HEAD:polar.py"], capture_output=True, text=True,
                             check=True).stdout
    except Exception:
        return None
    mod = types.ModuleType("polar_head")
    exec(compile(src, "polar_head", "exec"), mod.__dict__)
    return mod


def bits_of(s):
    return np.unpackbits(np.frombuffer(s, np.uint8))           # MSB first per byte


def to_int(b):
    return int("".join(map(str, b)), 2)


def main():
    t0 = time.time()
    rng = np.random.default_rng(1)
    print("1 baseline (N = 2048, CRC-16)")
    old = head_polar()
    if old is None:
        print("  (git HEAD polar.py not readable: HEAD comparison skipped)")
    for A in (205, 307, 819, 1024):
        new = PolarCode(2048, A, 16, 8)
        d = rng.integers(0, 2, (8, A), dtype=np.uint8)
        if old is not None:
            ref = old.PolarCode(2048, A, 16, 8)
            check(np.array_equal(new.info_pos, ref.info_pos) and np.array_equal(new.frozen, ref.frozen)
                  and np.array_equal(new.crc_G, ref.crc_G) and np.array_equal(new.encode(d), ref.encode(d)),
                  f"A = {A}: info set + CRC matrix + encode == git HEAD polar.py")
        check(np.array_equal(rm.crc_matrix(A, 16), new.crc_G), f"A = {A}: crc_matrix == polar CRC-16 matrix")
        exp = PolarCode(2048, A, 16, 8, info_pos=new.info_pos[::-1], crc_G=rm.crc_matrix(A, 16))
        check(np.array_equal(exp.info_pos, new.info_pos) and np.array_equal(exp.encode(d), new.encode(d)),
              f"A = {A}: explicit info_pos + crc_G == default")
        r = rm.RMPolarCode(A, 2048, crc_len=16)
        check(r.mode == "none" and r.N == 2048 and np.array_equal(r.code.info_pos, new.info_pos)
              and np.array_equal(r.encode(d), new.encode(d)) and np.array_equal(r.encode_rm(d)[:, r.J.argsort()],
                                                                                 new.encode(d)),
              f"A = {A}: RMPolarCode(E = 2048, CRC-16) mode none, same code, e = x interleaved by J")
    c9 = bits_of(b"123456789")
    check(to_int(crc_remainder(c9, 16)) == 0x31C3, "CRC-16 0x1021 init 0 check '123456789' = 0x31C3 (XMODEM)")
    check(to_int(crc_remainder(c9, 32)) == 0x89A1897F,
          "CRC-32 0x04C11DB7 init 0 check '123456789' = 0x89A1897F (= CKSUM 0x765E7680 without its final XOR)")
    G32 = np.stack([crc_remainder(np.eye(272, dtype=np.uint8)[i], 32) for i in range(272)])
    check(np.array_equal(rm.crc_matrix(272, 32), G32), "A = 272: crc_matrix == polar row-by-row CRC-32 matrix")

    print("2 targets (CRC-32)")
    codes = {}
    for name, K, E, force, mode, N in TARGETS:
        A = K - 32
        r = codes[name] = rm.RMPolarCode(A, E, mode=force)
        fi = r.frozen_info()
        sio = rm.rm_plan(K, E, extra_std=False, mode=force)
        print(f" {name}: K = {K}, E = {E}, K/E = {K / E:.3f} -> {r.mode}, N = {r.N}, U = {r.U}; frozen rm "
              f"{fi['n_rm']} + extra {fi['n_extra']} (low block {rm.extra_count(E, r.N) if r.mode == 'puncture' else 0},"
              f" Sionna {int((sio['rm'] | sio['extra']).sum())} pre) + reliability {fi['n_rel']}")
        check(r.mode == mode and r.N == N, f"mode {mode}, N {N}")
        check(int(r.code.frozen.sum()) == N - K and fi["n_pre"] + fi["n_rel"] == N - K
              and not (fi["rm"] & fi["extra"]).any() and np.array_equal(fi["rm"] | fi["extra"], fi["pre"]),
              "frozen count N - K; rm, extra disjoint, rm | extra = pre")
        gone = r.J[:r.U] if r.mode == "puncture" else r.J[E:]
        low = np.arange(rm.extra_count(E, r.N)) if r.mode == "puncture" else np.arange(0)
        check(r.code.frozen[gone].all() and r.code.frozen[low].all() and fi["rm"][gone].all(),
              "removed-position u (rm) and the whole low block frozen")
        v = rng.standard_normal((1, r.N))                     # exact inverse of the selection, deterministic values
        w = r.rate_recover(r.rate_match(v))
        sent = r.plan["sent_x"]
        fill = 0.0 if r.mode == "puncture" else rm.LLR_BIG
        check(np.array_equal(w[:, sent], v[:, sent]) and (w[:, ~sent] == fill).all() and (~sent).sum() == r.U,
              f"rate_recover(rate_match(v)): v at the {E} sent, {fill:g} at the {r.U} removed positions")
        d = rng.integers(0, 2, (64, A), dtype=np.uint8)
        x = r.encode(d)
        e = r.rate_match(x)
        check(e.shape == (64, E), f"len(e) = {E}")
        if r.mode == "shorten":
            check(not x[:, r.J[E:]].any(), "shortened x positions all 0 (64 frames)")
        llr = 20.0 * (1 - 2 * e[:2].astype(np.float64))          # noiseless BPSK, big LLR
        dh, ok, _ = r.decode(llr, return_info=True)
        check(ok.all() and np.array_equal(dh, d[:2]), "noiseless round trip, 2 frames, CRC pass")
        if r.mode == "shorten":                                  # negative control: the known zeros told as ones
            lx = r.rate_recover(llr)
            lx[:, r.J[E:]] = -rm.LLR_BIG
            dn, okn, _ = r.code.decode(lx, return_info=True)
            check(not (okn & np.all(dn == d[:2], axis=1)).any(),
                  f"negative control: shortened LLR -LLR_BIG -> no correct accept (CRC pass {[bool(o) for o in okn]})")
        m = r.macs(N_SYM[name], sf=8 if name.startswith("VDE") else 1)
        print(f"  MACs (CA-SCL-8, n_sym {N_SYM[name]}{', SF 8' if name.startswith('VDE') else ''}): decode total "
              f"{m['total']:,.0f}, per core {m['crit']:,.0f}; re-encode {m['reencode']:,.0f} "
              f"(per core {m['reencode_crit']:,.0f})")

    print("3 repetition, guards, N = 4096 bookkeeping")
    r = rm.RMPolarCode(24, 600, crc_len=16)                     # K = 40: n2 = 9, N = 512 < E
    v = rng.standard_normal((1, 512))
    exp = v.copy()
    exp[:, r.J[:600 - 512]] += v[:, r.J[:600 - 512]]
    check(np.allclose(r.rate_recover(r.rate_match(v)), exp), "repeat: rate_recover = sum of the copies")
    d = rng.integers(0, 2, (4, 24), dtype=np.uint8)
    dh, ok, _ = r.decode(4.0 * (1 - 2 * r.encode_rm(d).astype(np.float64)), return_info=True)
    check(r.mode == "repeat" and r.N == 512 and ok.all() and np.array_equal(dh, d), "repeat K = 40, E = 600, N 512")
    PiCode = type("PiCode", (PolarCode,), {})                   # stand-ins with blind_cfo's class names
    PiCode4 = type("PiCode4", (PiCode,), {})
    RBCode = type("RBCode", (PolarCode,), {})
    for cls, kw, want in ((PiCode, {}, False), (PiCode, dict(mode="puncture"), True), (PiCode4, dict(mode="puncture"),
                                                                                      False), (RBCode, {}, False)):
        try:
            rm.RMPolarCode(1472, 3008, crc_len=32, code_cls=cls, **kw)
            got = True
        except AssertionError:
            got = False
        check(got == want, f"guard {cls.__name__} {kw or 'standard rule'}: {'accepted' if want else 'rejected'}")
    r = codes["RCS2 ID 13/42"]
    d = rng.integers(0, 2, (1, r.A), dtype=np.uint8)
    llr = 20.0 * (1 - 2 * r.encode_rm(d).astype(np.float64))
    r.code.fz_stop, r.code.fz_q = (0.5, 1e9), (0.25, 0.5, 1.0)
    try:
        dh, ok, _ = r.decode(llr, return_info=True)
        F = int(r.code.frozen.sum())
        check(ok.all() and np.array_equal(dh, d) and not r.code.fzs_stop.any() and r.code.fzs_pos > 0
              and (r.code.fz_rec["cnt"] == np.ceil(np.array([0.25, 0.5, 1.0]) * F - 1e-9)).all(),
              f"N = 4096 fz_stop / fz_q run (fzs_pos {r.code.fzs_pos}, fz_q cnt {[int(c) for c in r.code.fz_rec['cnt']]})")
    finally:
        r.code.fz_stop = r.code.fz_q = None
    print(f"{'PASS' if not FAILS else 'FAILED (' + str(len(FAILS)) + ')'} in {time.time() - t0:.1f} s")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
