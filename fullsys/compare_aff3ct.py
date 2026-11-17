"""
Bit-exact check of fullsys/turbo_db.py (and the rcs2 CRC-32) against AFF3CT test vectors (job fs-aff3ct).

    inputs   fullsys/results/aff3ct_vectors/cli_K<K>_N<N>.txt   AFF3CT CLI --sim-dbg trace (Source, CRC, Encoder_turbo_DB,
                                                                Puncturer_turbo_DB per frame)
             fullsys/results/aff3ct_vectors/lib_K<K>_N<N>.txt   aff3ct_vec (fullsys/aff3ct_tools): lut, lut_inv, info_f,
                                                                crc_f, enc_f (3K), pct_f (N) per frame f
    checks   interleaver: AFF3CT lut = tdb.arp(N, P, Q); tdb 'aff3ct' src = lut_inv
             encoder: for every INTERLEAVER_DIRS reading, our 3K mother codeword and our punctured codeword
                      (rcs2.tx order) vs AFF3CT enc / pct, plus per-stream counts (Y1 W1 natural, Y2 W2 interleaved)
             CRC: AFF3CT '32-GZIP' (poly 0x04C11DB7 division of info | 0^32, init 0, no reflection, no final XOR)
                  vs a zero-init register CRC and vs rcs2's CRC-32/MPEG-2 (init 0xFFFFFFFF); the MPEG-2 - GZIP
                  difference must be the constant crc_MPEG2(0^k) (affine map, same polynomial)
Coded-bit order. AFF3CT Encoder_turbo_DB X_N (3K) = [A0 B0 A1 B1 ... | Y1_0 Y2_0 Y1_1 Y2_1 ... | W1_0 W2_0 ...]
(1 = natural, 2 = interleaved constituent, couple index of each constituent); Puncturer_turbo_DB keeps the first 2K
at R = 1/2 (all Y, no W) and all 3K at R = 1/3. rcs2.tx: u | Z1_0 Z2_0 Z1_1 Z2_1 ..., Z_i = kept Y_i then kept W_i,
which is the same sequence whenever the Y pattern keeps every couple (R = 1/3, 1/2; also checked here).

    py fullsys/compare_aff3ct.py [--dir fullsys/results/aff3ct_vectors]
"""

import argparse
import glob
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fullsys import rcs2, turbo_db as tdb          # noqa: E402

T0 = time.time()
ANSI = re.compile(r"\x1b\[[0-9;]*m")
NUM = re.compile(r"-?\d+(?:\.\d+)?")
HEAD = re.compile(r"^# (\w+)::(\w+)\(")
SOCK = re.compile(r"^# \{(IN|OUT|IN_OUT|FWD)\}\s+(\w+)\s*=\s*\[(.*)\]\s*$")
PUNCT = {"1/3": ("1", "1"), "1/2": ("1", "0"), "2/3": ("10", "0")}   # AFF3CT Puncturer_turbo_DB patterns (Y, W)
N_FAIL = 0


def check(name, ok, detail=""):
    global N_FAIL
    N_FAIL += not ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


def rate_key(K, N):
    for k, (a, b) in {"1/3": (1, 3), "1/2": (1, 2), "2/3": (2, 3)}.items():
        if K * b == N * a:
            return k
    return None


def code_params(n_couples):
    """(P, Q) of the Table A-1 code with this many couples (rcs2.WAVEFORMS)."""
    for w in rcs2.WAVEFORMS.values():
        if w["N"] == n_couples:
            return w["P"], w["Q"]
    raise KeyError(f"no WAVEFORMS entry with N = {n_couples} couples")


# ---- parsers -----------------------------------------------------------------------------------------------------
def parse_lib(path):
    """aff3ct_vec file -> dict name -> int8/int64 array."""
    out = {}
    with open(path) as f:
        for line in f:
            if line.startswith("#") or ":" not in line:
                continue
            k, v = line.split(":", 1)
            out[k.strip()] = np.array(v.split(), np.int64)
    return out


def parse_cli(path):
    """AFF3CT --sim-dbg trace -> list of (module, task, {socket: array}, truncated)."""
    calls, cur = [], None
    with open(path, errors="replace") as f:
        for raw in f:
            line = ANSI.sub("", raw.rstrip("\n"))
            m = HEAD.match(line)
            if m:
                cur = (m.group(1), m.group(2), {}, [False])
                calls.append(cur)
                continue
            s = SOCK.match(line)
            if s and cur is not None:
                body = s.group(3)
                cur[3][0] |= "..." in body
                cur[2][(s.group(1), s.group(2))] = np.array([float(x) for x in NUM.findall(body)])
    return [(a, b, c, d[0]) for a, b, c, d in calls]


def cli_frames(calls):
    """Per frame: info (Source out), crc (CRC build out), enc (Encoder_turbo_DB out), pct (Puncturer out)."""
    def outs(pred):
        r = []
        for mod, task, socks, trunc in calls:
            if pred(mod, task):
                o = [v for (d, _), v in socks.items() if d == "OUT"]
                i = [v for (d, _), v in socks.items() if d == "IN"]
                r.append((i[0] if i else None, o[0] if o else None, trunc))
        return r
    enc = outs(lambda m, t: m.startswith("Encoder_turbo_DB") and t == "encode")
    pct = outs(lambda m, t: m.startswith("Puncturer") and t == "puncture")
    crc = outs(lambda m, t: m.startswith("CRC") and t == "build")
    src = outs(lambda m, t: m.startswith("Source") and t == "generate")
    fr = []
    for f, (u, x, tr) in enumerate(enc):
        d = {"crc": u.astype(np.int64), "enc": x.astype(np.int64), "trunc": tr}
        if f < len(pct):
            d["pct"] = pct[f][1].astype(np.int64)
            d["trunc"] |= pct[f][2]
        if f < len(crc):
            d["info"] = crc[f][0].astype(np.int64)
        elif f < len(src):
            d["info"] = src[f][1].astype(np.int64)
        fr.append(d)
    return fr


# ---- our side ----------------------------------------------------------------------------------------------------
def ours(u, K, N, direction):
    """u (B, K) encoder input -> (mother 3K in AFF3CT X_N order, punctured N in rcs2.tx order, streams)."""
    nc = K // 2
    P, Q = code_params(nc)
    full = tdb.TurboDB(nc, P, Q, "1", "1", direction)
    Z1, Z2 = full.encode(u)                                  # [Y | W] per constituent, every couple kept
    Y1, W1, Y2, W2 = Z1[:, :nc], Z1[:, nc:], Z2[:, :nc], Z2[:, nc:]
    B = u.shape[0]
    mother = np.empty((B, 3 * K), np.int64)
    mother[:, :K] = u
    mother[:, K:2 * K:2], mother[:, K + 1:2 * K:2] = Y1, Y2
    mother[:, 2 * K::2], mother[:, 2 * K + 1::2] = W1, W2
    yp, wp = PUNCT[rate_key(K, N)]
    code = tdb.TurboDB(nc, P, Q, yp, wp, direction)
    z1, z2 = code.encode(u)
    par = np.empty((B, 2 * code.M), np.int64)
    par[:, 0::2], par[:, 1::2] = z1, z2                      # rcs2.tx interleaving of Z1 / Z2
    return mother, np.concatenate([u, par], axis=1), (Y1, W1, Y2, W2)


def crc_zero_init(bits, r=32):
    """Register CRC, MSB first, init 0, no final XOR (= AFF3CT polynomial division of bits | 0^r)."""
    poly = np.array([(rcs2.CRC_POLY[r] >> (r - 1 - i)) & 1 for i in range(r)], np.int8)
    reg = np.zeros((bits.shape[0], r), np.int8)
    for k in range(bits.shape[1]):
        fb = reg[:, 0] ^ bits[:, k]
        reg = np.concatenate([reg[:, 1:], np.zeros((bits.shape[0], 1), np.int8)], axis=1)
        reg ^= fb[:, None] * poly[None]
    return reg


# ---- per case ----------------------------------------------------------------------------------------------------
def compare_case(tag, K, N, frames, lut=None, lut_inv=None):
    print(f"\n=== {tag}: K = {K}, N = {N}, R = {rate_key(K, N)}, {K // 2} couples, {len(frames)} frames")
    nc = K // 2
    P, Q = code_params(nc)
    if lut is not None:
        check(f"{tag} lut = arp(N={nc}, P={P}, Q={Q})", np.array_equal(lut, tdb.arp(nc, P, Q)))
        src_a, sw_a = tdb.interleaver(nc, P, Q, "aff3ct")
        check(f"{tag} lut_inv = tdb 'aff3ct' src (interleaved couple j <- natural lut_inv[j], natural even swapped)",
              np.array_equal(lut_inv, src_a) and np.array_equal(sw_a, lut_inv % 2 == 0))
    if not frames:
        print("  no frames")
        return
    if any(f.get("trunc") for f in frames):
        check(f"{tag} trace not truncated (--sim-dbg-limit)", False)
        return
    u = np.stack([f["crc"] for f in frames]).astype(np.int8)
    enc = np.stack([f["enc"] for f in frames])
    check(f"{tag} sizes crc {u.shape[1]} = K, enc {enc.shape[1]} = 3K", u.shape[1] == K and enc.shape[1] == 3 * K)
    check(f"{tag} systematic part of X_N = encoder input", np.array_equal(enc[:, :K], u))
    # CRC
    if all("info" in f for f in frames):
        info = np.stack([f["info"] for f in frames]).astype(np.int8)
        k = info.shape[1]
        a_crc = u[:, k:]
        check(f"{tag} crc input = info bits", np.array_equal(u[:, :k], info))
        check(f"{tag} AFF3CT 32-GZIP = zero-init CRC-32 (poly 0x04C11DB7, MSB first)",
              np.array_equal(a_crc, crc_zero_init(info)))
        mp = rcs2.crc_bits_serial(info, 32)
        same = np.array_equal(a_crc, mp)
        c0 = rcs2.crc_bits_serial(np.zeros((1, k), np.int8), 32)[0]
        aff = np.array_equal(mp ^ a_crc, np.broadcast_to(c0, mp.shape))
        print(f"  rcs2 CRC-32/MPEG-2 == AFF3CT 32-GZIP: {same}; MPEG-2 ^ GZIP == crc_MPEG2(0^{k}) = "
              f"0x{rcs2.bits_to_int(c0):08X} for every frame: {aff}")
        check(f"{tag} MPEG-2 and GZIP differ by the init constant only", aff)
    # encoder, every reading
    res = {}
    for d in tdb.INTERLEAVER_DIRS:
        mother, punct, (Y1, W1, Y2, W2) = ours(u, K, N, d)
        ok_m = np.array_equal(mother, enc)
        ok_p = "pct" in frames[0] and np.array_equal(punct, np.stack([f["pct"] for f in frames]))
        A = enc[:, K:]
        nY = [int((A[:, 0:K:2] != Y1).sum()), int((A[:, 1:K:2] != Y2).sum())]
        nW = [int((A[:, K::2] != W1).sum()), int((A[:, K + 1::2] != W2).sum())]
        res[d] = ok_m and ok_p
        print(f"  reading {d:11s} mother 3K {'MATCH' if ok_m else 'differ'}, punctured {'MATCH' if ok_p else 'differ'}"
              f"  | bit errors Y1 {nY[0]} W1 {nW[0]} Y2 {nY[1]} W2 {nW[1]}")
    check(f"{tag} default INTERLEAVER_DIR '{tdb.INTERLEAVER_DIR}' bit-exact", res[tdb.INTERLEAVER_DIR])
    print(f"  bit-exact readings: {[d for d, v in res.items() if v] or 'NONE'}")
    if "pct" in frames[0]:
        pc = np.stack([f["pct"] for f in frames])
        check(f"{tag} AFF3CT punctured = first {N} bits of its X_N", np.array_equal(pc, enc[:, :N]))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(ROOT, "fullsys", "results", "aff3ct_vectors"))
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.dir, "cli_K*_N*.txt")) + glob.glob(os.path.join(a.dir, "lib_K*_N*.txt")))
    if not files:
        sys.exit(f"no cli_K*_N*.txt / lib_K*_N*.txt in {a.dir} (run job fs-aff3ct first)")
    summary = {}
    for p in files:
        name = os.path.basename(p)
        K, N = map(int, re.match(r"\w+_K(\d+)_N(\d+)\.txt", name).groups())
        if name.startswith("lib_"):
            d = parse_lib(p)
            fr = [{"info": d[f"info_{i}"], "crc": d[f"crc_{i}"], "enc": d[f"enc_{i}"], "pct": d[f"pct_{i}"]}
                  for i in range(10) if f"enc_{i}" in d]
            r = compare_case(name, K, N, fr, d.get("lut"), d.get("lut_inv"))
        else:
            r = compare_case(name, K, N, cli_frames(parse_cli(p)))
        summary[name] = r
    print("\nsummary (bit-exact readings per file):")
    for k, r in summary.items():
        print(f"  {k:24s} {[d for d, v in (r or {}).items() if v] or 'NONE / no frames'}")
    print(f"\n{N_FAIL} failure(s), {time.time() - T0:.1f} s")
    return 1 if N_FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
