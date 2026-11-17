"""
Self-test of fullsys/nbiot.py + turbo_lte.py + the run_fullsys_da --sys nbiot adapter (no BLER simulation, < 5 s):
QPP permutations (all 188 sizes), encoder bit-exact vs Sionna's LTE turbo reference codewords, trellis termination,
CRC-24A check values, rate-matching structure, noiseless round trips of every format (max-log and log-MAP), erasure
decoding needs the extrinsic exchange, burst layout / timing / DM-RS properties, TBS choices, ops, and the DA adapter
on 2 noiseless packets per variant (guard + 40 ms gap, CFO +-0.029 / +-0.054).     py fullsys/selftest_nbiot.py
"""

import os
import sys
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from fullsys import costmodel as cm      # noqa: E402
from fullsys import nbiot as nb          # noqa: E402
from fullsys import turbo_lte as tl      # noqa: E402

T0 = time.time()
# Sionna test/codes/turbo/ref_k{K}_u.npy / ref_k{K}_x.npy, row 0 (TurboEncoder(rate 1/3, constraint_length 4,
# terminate True), output x_k z_k z'_k per k, then the 12 tail bits in the 36.212 d(0) d(1) d(2) order), as hex
SIONNA_REF = {
    40: ("0aebdabffb", "008ee0beaeb7b96ce8a7efbfff7c6db30"),
    112: ("ec7c14de02817d45acc1ede12667",
          "f3adda5adbc120f702b8eba20116a2ad00851bef845d974ceb1f09b1325ef73ddcfa10c502a1b97ba566007"),
    168: ("528c7805482ae864f6ba77e5ede4c26e7c7cf3bf1c",
          "1dd2e8a4bdda5ada5a64a106318c586ab8e2b79e923f1580f345e2cbe8705b41bfff07cf9a2f16b2854a9c823b5619e21f7fc2374902"
          "bbc02586f92f2469986f0"),
    432: ("a28732b525cbae650bcd83887cfd6622ef7e9d13fa9cd7ebc63bcb083e2e41ca94c62eadf034521b274cfec8320838c0f919106e21ad",
          "ee96a3ad13642ef0728265876e37d7d09af58ea9391a811745aaecfd2b45eca6f4ad1c195379d1becb877393e80b1232bfabfd1bffb98"
          "86fcc405477fb6e2aec5d58d847e5bbb826b1a3f84278f4b4282f6528d82bfbea02bd2a790696952ef8c9d713d19322430969870b1c9f"
          "40116ec1497864a34458a50e973f54a9c8d35b70f018c166f6212cb85b67fc51bd94d8ffee5e246a0440c60a372fa02f1047838b14b00"),
}


def ok(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg, flush=True)
    if not cond:
        ok.failed += 1


ok.failed = 0


def hexbits(h, n):
    return np.array([int(c) for x in h for c in format(int(x, 16), "04b")], np.int8)[:n]


def main():
    rng = np.random.default_rng(3)

    # ---- QPP, sub-block pattern ----
    bad = [K for K, f1, f2 in tl.QPP_TABLE if not np.array_equal(np.sort(tl.qpp_interleaver(K, f1, f2)), np.arange(K))]
    ok(len(tl.QPP_TABLE) == 188 and not bad and tl.QPP_TABLE[0] == (40, 3, 10) and tl.QPP_TABLE[-1] == (6144, 263, 480),
       f"QPP Table 5.1.3-3: 188 sizes 40..6144, every (f1, f2) a permutation (bad {bad})")
    rev = np.array([int(format(i, "05b")[::-1], 2) for i in range(32)])
    ok(np.array_equal(tl.SUBBLOCK_P, rev), "sub-block column pattern Table 5.1.4-1 = 5-bit bit reversal")
    tbs = sorted({v for row in nb.TBS_TABLE for v in row})
    ok(all(t + 24 in tl.QPP for t in tbs), f"every NPUSCH TBS + 24 is a QPP size ({len(tbs)} TBS values 16..2536): "
       "one code block, no filler")

    # ---- encoder bit-exact vs Sionna reference codewords ----
    for K, (uh, xh) in SIONNA_REF.items():
        u = hexbits(uh, K)
        x = hexbits(xh, 3 * K + 12)
        d = tl.TurboLTE(K).encode(u[None])[0]
        mine = d.T.ravel()                                       # d(0)_k d(1)_k d(2)_k for k = 0 .. K + 3
        ok(np.array_equal(mine, x), f"turbo encoder K {K} (f1 {tl.QPP[K][0]} f2 {tl.QPP[K][1]}) = Sionna reference "
           f"codeword ({int((mine != x).sum())} bit diffs of {3 * K + 12})")

    # ---- termination: the plain RSC recursion fed with c + tail x ends in state 0 ----
    for K in (232, 1024):
        code = tl.TurboLTE(K)
        c = rng.integers(0, 2, (3, K), dtype=np.int8)
        d = code.encode(c)
        T = np.empty((3, 12), np.int8)
        T[:, tl.tail_map().ravel()] = d[:, :, K:].reshape(3, 12)
        for name, uin, tx in (("RSC1", c, T[:, [0, 2, 4]]), ("RSC2", c[:, code.pi], T[:, [6, 8, 10]])):
            a1 = a2 = a3 = np.zeros(3, np.int8)
            for t in range(K + 3):
                b = uin[:, t] if t < K else tx[:, t - K]
                a = b ^ a2 ^ a3
                a1, a2, a3 = a, a1, a2
            ok(not (a1 | a2 | a3).any(), f"K {K} {name} ends in state 0 after the 3 tail clocks")

    # ---- CRC-24A ----
    c0, cp = nb.crc24a_check(), nb.crc24a_check(init=0xB704CE)
    ok(c0 == 0xCDE703, f"CRC-24A (0x864CFB, init 0) of '123456789' = 0x{c0:06X} (CRC-24/LTE-A check 0xCDE703)")
    ok(cp == 0x21CF02, f"same polynomial, init 0xB704CE (CRC-24/OpenPGP) = 0x{cp:06X} (check 0x21CF02)")
    L328 = nb.NPUSCH("nb328")
    pay = rng.integers(0, 2, (4, 328), dtype=np.int8)
    st = L328.encode_bits(pay)
    ser = [nb.crc_register(p, 24, 0x864CFB, 0) for p in pay]
    vec = [int("".join(map(str, r)), 2) for r in st["c"][:, 328:]]
    ok(ser == vec and not L328.crc_chk.register(st["c"]).any(), "vectorised CRC-24A = LFSR, residue 0 over TB | CRC")

    # ---- rate matching ----
    for K in (232, 352, 832, 1024):
        rm = tl.rm_index(K, 3 * K + 12)
        flat = np.sort(rm["idx"])
        ok(np.array_equal(flat, np.arange(3 * (K + 4))) and rm["k0"] == 2 * rm["R"] and rm["n_valid"] == 3 * K + 12
           and rm["K_w"] == 3 * 32 * rm["R"] and (rm["w"] == tl.NULL).sum() == rm["K_w"] - 3 * K - 12,
           f"RM K {K}: R {rm['R']} K_w {rm['K_w']} k0 {rm['k0']}; E = 3K + 12 at RV 0 = a permutation of the mother "
           f"codeword, {(rm['w'] == tl.NULL).sum()} NULLs never sent")
        r2 = tl.rm_index(K, 3 * K + 12, rv=2)
        ok(r2["k0"] == r2["R"] * (2 * int(np.ceil(r2["N_cb"] / (8 * r2["R"]))) * 2 + 2), f"RM K {K} RV 2 k0 {r2['k0']}")
    rm = tl.rm_index(352, 1152)
    ok(len(np.unique(rm["idx"])) == 1068 and len(rm["idx"]) == 1152, "nb328: E 1152 > 1068 coded bits -> 84 repeated "
       "(circular buffer wrap)")
    rm = tl.rm_index(1024, 1536)
    w = rm["w"][rm["w"] != tl.NULL]
    ok(len(np.unique(rm["idx"])) == 1536 and np.array_equal(rm["idx"][:10], np.roll(rm["w"], -rm["k0"])[
        np.roll(rm["w"], -rm["k0"]) != tl.NULL][:10]) and len(w) == 3084, "nb1000: E 1536 < 3084, read from k0")

    # ---- formats, burst layout, timing, DM-RS ----
    print("format      I_MCS I_TBS I_RU N_RU Qm  TBS    K     E  rate  symbols DM-RS  ms   Eb/N0 = Es/N0 + (burst, +CP, data)")
    links = {}
    for f in nb.FORMATS:
        L = nb.NPUSCH(f)
        links[f] = L
        s = L.summary()
        if L.code_only:
            ok(L.E == 4108 and L.A == 2024 and L.n_sym == 4108, f"{f}: (4108, 2048) AFF3CT frame, K_info 2024")
            continue
        print(f"  {f:10s} {s['i_mcs']:5d} {s['i_tbs']:5d} {s['i_ru']:4d} {s['n_ru']:4d} {s['qm']:2d} {L.A:5d} {L.K:5d} "
              f"{L.E:5d} {s['rate']:.3f} {L.n_sym:7d} {s['n_dmrs']:5d} {s['duration_ms']:4.0f}  "
              f"{s['ebn0_offset_burst']:+.2f} {s['ebn0_offset_burst_cp']:+.2f} {s['ebn0_offset_data']:+.2f}")
        ok(L.E == 96 * s["n_ru"] * L.qm and L.n_sym == 112 * s["n_ru"] and len(L.dmrs_pos) == 16 * s["n_ru"]
           and np.array_equal(L.dmrs_pos % 7, np.full(len(L.dmrs_pos), 4)), f"{f}: E = 96 N_RU Q_m, DM-RS at slot symbol 4")
    want = {"nb208": 208, "nb208b": 208, "nb296": 296, "nb328": 328, "nb808": 808, "nb1000": 1000, "nb1000r10": 1000}
    ok(all(links[f].A == a for f, a in want.items()), "TBS from Table 16.5.1.2-2: " + ", ".join(
        f"{f} {links[f].A}" for f in want))
    for tgt in (205, 307, 819, 1000):                           # closest NB1 TBS values (any single-tone I_RU)
        c = sorted({v for row in nb.TBS_TABLE[:11] for v in row if v <= nb.TBS_MAX_NB1}, key=lambda v: abs(v - tgt))[0]
        print(f"  target {tgt}: closest single-tone NB1 TBS {c}", flush=True)
    ok(links["nb328"].duration_ms == 192 and links["nb1000"].duration_ms == 256
       and links["nb1000r10"].duration_ms == 360, "durations 192 / 256 ms, 10 RUs 320 + 40 ms gap = 360 ms")
    t = links["nb328"].t
    ok(abs(t[7] - 80 / 11) < 1e-12 and abs(t[6] - 6) < 1e-12 and abs(t[1] - 1) < 1e-12,
       "timing: symbols 275 us apart inside a slot, next slot at 80/11 symbols (2304 T_s = 3/11 guard)")
    tr = links["nb1000r10"].t[links["nb1000r10"].dmrs_pos]
    dt = np.diff(tr)
    ok(np.allclose(dt[:127], 80 / 11) and abs(dt[127] - 21 * 80 / 11) < 1e-9 and np.allclose(dt[128:], 80 / 11),
       f"nb1000r10 DM-RS comb: period 80/11, one 40 ms gap (20 slots) after slot 127")
    L = links["nb328"]
    der = L.dmrs * np.conj(L.rot[L.dmrs_pos])
    c35 = nb.gold(35, L.n_slots)
    ok(np.allclose(np.abs(L.dmrs), 1) and np.allclose(der, (1 + 1j) / np.sqrt(2) * (1 - 2 * c35)),
       f"DM-RS: unit modulus, (1+j)/sqrt2 (1 - 2 c_35(n)) w_0 (all-ones row) after the rotation; "
       f"{int(c35.sum())} of {L.n_slots} c = 1")
    H = np.array([nb.hadamard_row(u) for u in range(16)])
    ok(np.array_equal(H @ H.T, 16 * np.eye(16)) and H[1].tolist() == [1, -1] * 8 and H[2][:4].tolist() == [1, 1, -1, -1],
       "Table 10.1.4.1.1-1 rows = Sylvester Hadamard (orthogonal, row 1 = +-+-, row 2 = ++--)")
    g = nb.gold(0x4000, 20000)
    ok(abs(g.mean() - 0.5) < 0.02 and not np.array_equal(g[:64], nb.gold(0x4001, 64)), f"Gold c(n): balance "
       f"{g.mean():.4f}, c_init sensitive")
    x, _ = L.tx(pay[:2])
    ang = np.angle(x[:, L.data_pos] * np.conj(L.rot[L.data_pos])[None])
    ok(np.allclose(np.abs(x), 1) and np.allclose(np.mod(ang - np.pi / 4, np.pi / 2), 0, atol=1e-9)
       and np.allclose(L.rot[1::2], np.exp(1j * np.pi / 4)), "pi/4-QPSK: odd symbols rotated by pi/4, unit energy")
    xb, _ = links["nb208b"].tx(rng.integers(0, 2, (2, 208), dtype=np.int8))
    Lb = links["nb208b"]
    ok(np.allclose(Lb.rot[1::2], 1j) and np.allclose(np.abs(np.real(xb[:, Lb.data_pos] * np.conj(Lb.rot[Lb.data_pos])
                                                                    * (1 - 1j) / np.sqrt(2))), 1),
       "pi/2-BPSK: odd symbols rotated by pi/2, (1+j)/sqrt2 (1 - 2 b)")

    # ---- noiseless round trips (ideal sync: unit gain, LLR scale from n0 = 0.5) ----
    for f, L in links.items():
        algos = ("maxlog", "logmap") if f in ("nb328", "nb208b") else ("maxlog",)
        for algo in algos:
            p = rng.integers(0, 2, (2, L.A), dtype=np.int8)
            x, _ = L.tx(p)
            out = L.rx(x, 0.5, iters=8, algo=algo)
            ok(np.array_equal(out["payload"], p) and out["crc_ok"].all() and (out["iters"] == L.crc_start).all(),
               f"round trip {f} {algo}: {L.A} bits ok, early stop at iteration {out['iters'].tolist()}, "
               f"ops/burst {out['ops'][0]:.4g} (crit {out['ops_crit'][0]:.4g})")
    p = rng.integers(0, 2, (2, 328), dtype=np.int8)
    x, _ = L328.tx(p)
    x[1, L328.data_pos[:300]] *= -1
    out = L328.rx(x, 0.5, iters=3)
    ok(out["crc_ok"][0] and not out["crc_ok"][1] and out["iters"][1] == 3 and out["first"][1] == 0,
       "corrupted burst: CRC fails, no early stop, first pass 0")
    code = L328.code                                             # erasures: the extrinsic exchange is needed
    c = rng.integers(0, 2, (4, code.K), dtype=np.int8)
    llr = 8.0 * (1 - 2 * code.encode(c).astype(float))
    llr[rng.random(llr.shape) < 0.55] = 0.0
    for algo in ("maxlog", "logmap"):
        b, used, first, _ = code.decode(llr, 8, algo, stop=lambda bb, rr: (bb == c[rr]).all(1))
        b1, _, _, _ = code.decode(llr, 1, algo)
        ok(np.array_equal(b, c) and used.max() > 1 and not np.array_equal(b1, c),
           f"K 352 turbo, 55 % erasures, {algo}: 1 iteration fails, decoded after {used.tolist()} iterations")

    # ---- ops (costmodel, 2 soft inputs per step) ----
    sm, sl = cm.siso_step_ops("maxlog", 8, 2)["total"], cm.siso_step_ops("logmap", 8, 2)["total"]
    m1 = tl.macs(352, 1, "maxlog", early=False)
    ok(sm == 114 and sl == 173 and m1 == 2 * 355 * 114 + 352 * 3, f"SISO step ops max-log {sm} / log-MAP {sl}; "
       f"K 352 one iteration {m1} ops ({m1 / 328:.0f} per payload bit)")
    print(f"  ops nb328 8 it max-log early: {tl.macs(352, 8):.4g}, crit {tl.crit(352, 8):.4g}; nb1000: "
          f"{tl.macs(1024, 8):.4g}, crit {tl.crit(1024, 8):.4g}", flush=True)

    # ---- the run_fullsys_da adapter: 2 noiseless packets per variant ----
    from fullsys import run_fullsys_da as R
    from fullsys import da_sync as DA
    for fmt, cfo in (("nb328", 0.035), ("nb1000r10", 0.035), ("nb208", 0.055)):
        S = None
        for var, m in (("standard", 1), ("strong", 3), ("genie", 1), ("ideal", 1)):
            o = dict(sys="nbiot", nbfmt=fmt, cfo_max=cfo, variant=var, top_m=m, refine=DA.REFINE, newton=DA.NEWTON,
                     dd_iters=0, n0="est", batch=0, iters=8, algo="maxlog", scale=None, early_stop=True)
            S = S or R.NBSys(o)
            S.o = o
            fs = 0.029 if cfo < 0.05 else 0.054
            rr = np.random.default_rng(5)
            rec = R.simulate(S, o, 60.0, rr, rr, 2, f_set=[fs, -fs], ph_set=[1.0, -2.5])
            res = R.summarise(rec, S, o, 0)
            ferr = rec["f1"] - rec["f"]
            good = bool(np.all(np.abs(ferr) < 1e-4) and rec["crc"].all() and not rec["mism"].any()
                        and np.all(np.abs(rec["ph_err1"]) < 0.05) and res["frames"] == 2)   # chain ISI at large f
            ok(good, f"adapter {fmt} +-{cfo} {var:8s}: f_err {ferr[0]:+.1e} {ferr[1]:+.1e} | phase err "
               f"{rec['ph_err1'][0]:+.1e} | crc {rec['crc'].tolist()} | ops/pkt {res['ops_sum'] / 2:.4g} "
               f"crit {res['crit_sum'] / 2:.4g}")
        lay = S.lay
        print(f"  {fmt}: comb Nk {S.lay_v.Nk} span {S.lay_v.span} nfft {S.lay_v.nfft} n_win {S.lay_v.n_win}, "
              f"window +-{lay.fwin:.4f}/symbol (alias +-{1 / (2 * S.P):.4f}); sync lean {S.cost_lean['ops']['first']:.0f} "
              f"ops (crit {S.cost_lean['crit']['first']:.0f}); sqrt CRB at 0 dB {np.sqrt(lay.crb(0.0)):.2e}, "
              f"outlier thr {lay.outlier_thr():.2e}", flush=True)
    o = dict(sys="nbiot", nbfmt="aff3ct-K2048", cfo_max=0.0, variant="ideal", top_m=1, refine=DA.REFINE,
             newton=DA.NEWTON, dd_iters=0, n0="est", batch=0, iters=8, algo="maxlog", scale=None, early_stop=True)
    S = R.NBSys(o)
    rr = np.random.default_rng(6)
    rec = R.simulate(S, o, 60.0, rr, rr, 2)
    pe = S.point_extra(-1.97)
    ok(rec["crc"].all() and not rec["mism"].any() and abs(pe["ebn0_payload"] - 1.10) < 0.01,
       f"aff3ct-K2048 ideal: round trip, AFF3CT Eb/N0 at Es/N0 -1.97 = {pe['ebn0_payload']:.3f} dB "
       f"(AFF3CT table -1.97 -> 1.10), ref FER {pe['ref_aff3ct_fer']}")
    print(f"{'ALL PASS' if ok.failed == 0 else f'{ok.failed} FAILED'} ({time.time() - T0:.1f} s)", flush=True)
    return ok.failed


if __name__ == "__main__":
    sys.exit(main())
