"""BLIND_IMPLEMENTATION/testing/: measurement-only checks of two literature ideas (lit_blind_cfo.md). Cluster only.

    BLIND_STUDY=small_cfo python BLIND_IMPLEMENTATION/testing/lit_checks.py --check equiv --rate 0.15 --snr -3 --n 4000 --part t-lit-eq15
    BLIND_STUDY=small_cfo python BLIND_IMPLEMENTATION/testing/lit_checks.py --check rank  --rate 0.15 --snr -4 --n 2000 --part t-lit-rk15

equiv (Geiselhart et al. 2023, phase-equivariant polar-coded QPSK): with Gray QPSK, a pi/2 rotation maps the bit pair
(b0, b1) of a symbol to (not b1, b0). If the pair is (c_2k, c_2k+1) of the codeword in natural order (NO interleaver),
that is a translation of the code index (an automorphism of every polar / decreasing monomial code, and SC decoding
is equivariant under it) plus the codeword "ones at even positions" (row N-2, always an information row). So the list-1
SC metric at theta + q pi/2 should equal the one at theta, and CA-SCL at a wrong pi/2 branch should find the packet
after un-rotating its list paths (4 CRC checks per path instead of a second metric pass / decode). Measured per packet
at the true CFO: the metric at theta + q pi/2 (q = 0..3) with and without the interleaver, and CA-SCL-8 success at
theta + q pi/2 with the rotation-aware CRC check (no interleaver).

rank (Giard et al. 2017/18, frozen-bit metric): the list-1 Fast-SSC metric per leaf node at every grid cell (4 phases
q pi/4 at the cell's 4th-power phase), scored as (a) the total (our metric), (b) rate-0 + REP nodes only, (c) without
SPC nodes. Rank of the true cell (nearest grid cell to the true CFO) among all cells for each score; the receiver keeps
<= 4 candidates (32 at 2/5, 1/2), so P(rank <= 4) and P(rank <= 32) are the numbers to compare. Full-length metrics
(the receiver's last checkpoint).

Writes small_cfo/blind/results/lit_<part>.json (BLIND_STUDY=small_cfo).
"""
import argparse
import json
import multiprocessing as mp
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

import blind_cfo as bc  # noqa: E402
import blind_fast as bf  # noqa: E402
from polar import polar_transform  # noqa: E402


def rot_back(cw, q):
    """Undo q pi/2 rotations of Gray QPSK on natural-order codewords cw (..., N): one rotation maps (b0, b1) to
    (not b1, b0), so its inverse maps (b0', b1') to (b1', not b0')."""
    x = cw.copy()
    for _ in range(q % 4):
        b0, b1 = x[..., 0::2].copy(), x[..., 1::2].copy()
        x[..., 0::2], x[..., 1::2] = b1, 1 - b0
    return x


def equiv_chunk(args):
    rate, snr, n, seed = args
    rng = np.random.default_rng(seed)
    A = bc.CODES[rate]
    code = bc.PiCode(bc.N_BITS, A, 16, 8)
    fs_ = bf.fast_sc(A)
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    out = dict(n=0, dm_noint=[], dm_int=[], ok_std=0, ok_rot=[0, 0, 0, 0], ok_rot_any=0, right_rot=[0, 0, 0, 0],
               wrong_rot=[0, 0, 0, 0])
    for il in (False, True):
        data, cw, r, rx, f, th = bc.frames(n, code, snr, rng, interleave=il)
        M = np.stack([fs_.metric(bc.llrs(r, f, th + q * np.pi / 2, sigma2, interleave=il)) for q in range(4)], 1)
        out["dm_int" if il else "dm_noint"] = (M[:, 1:] - M[:, :1]).tolist()
        if il:
            continue
        out["n"] = n
        # CA-SCL-8 at each pi/2 branch; every list path un-rotated by q' = 0..3, kept if its frozen bits are 0 and
        # its CRC passes (PiCode: also the pi complement through the last CRC bit, as in the receiver)
        for q in range(4):
            L = bc.llrs(r, f, th + q * np.pi / 2, sigma2, interleave=False)
            d0, ok0, _ = code.decode(L, return_info=True)
            if q == 0:
                out["ok_std"] = int((ok0 & (d0 == data).all(1)).sum())
            info = np.empty((n, code.list_size, code.K), np.uint8)
            path = np.broadcast_to(np.arange(code.list_size), (n, code.list_size))
            rows = np.arange(n)[:, None]
            for k in range(code.K - 1, -1, -1):
                info[:, :, k] = code._bits[k][rows, path]
                path = code._parents[k][rows, path]
            fin = np.isfinite(code._pm)
            u = np.zeros((n, code.list_size, code.N), np.uint8)
            u[..., code.info_pos] = info
            cwp = polar_transform(u)
            got = np.zeros(n, bool)
            right = np.zeros(n, bool)
            for qq in range(4):
                uu = polar_transform(rot_back(cwp, qq))
                fz = ~uu[..., code.frozen].any(-1)
                d, c = uu[..., code.info_pos][..., :code.A], uu[..., code.info_pos][..., code.A:]
                calc = code.crc(d.reshape(-1, code.A)).reshape(n, code.list_size, code.C)
                flip = np.zeros(code.C, np.uint8)
                flip[-1] = 1
                ok = fz & fin & ((calc == c).all(-1) | (calc == c ^ flip).all(-1))
                score = np.where(ok, code._pm, np.inf)
                b = score.argmin(1)
                okp = ok.any(1)
                dsel = d[np.arange(n), b]
                newly = okp & ~got
                right |= newly & (dsel == data).all(1)
                got |= okp
            out["ok_rot"][q] = int(right.sum())
            out["wrong_rot"][q] = int((got & ~right).sum())
    return out


def leaf_types(plan, out):
    if plan[0] == "N":
        leaf_types(plan[1], out)
        leaf_types(plan[2], out)
    else:
        out.append(plan[0])
    return out


def rank_chunk(args):
    rate, snr, n, seed = args
    rng = np.random.default_rng(seed)
    A = bc.CODES[rate]
    code = bc.PiCode(bc.N_BITS, A, 16, 8)
    fs_ = bf.fast_sc(A)
    types = np.array(leaf_types(fs_.plan, []))
    m_frz = np.isin(types, ["R0", "REP"])
    m_nospc = types != "SPC"
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    k = bf.grid_step(bc.PROFILE.get(rate, rate), snr)
    g = bf.grid(k)["f"]
    nq = 4
    data, cw, r, rx, f, th = bc.frames(n, code, snr, rng)
    ranks = {"total": [], "frozen": [], "no_spc": []}
    for i in range(n):
        th_c = bc.phase4(np.repeat(r[i:i + 1], 1, 0), g[None])[0]           # 4th-power phase per cell
        F = np.repeat(g, nq)
        TH = (th_c[:, None] + np.arange(nq)[None] * np.pi / 4).ravel()
        P = fs_.metric_nodes(bc.llrs(np.repeat(r[i:i + 1], len(F), 0), F, TH, sigma2)).reshape(len(g), nq, -1)
        tc = int(np.abs(g - f[i]).argmin())
        for nm, m in (("total", np.ones(len(types), bool)), ("frozen", m_frz), ("no_spc", m_nospc)):
            s = P[..., m].sum(-1).min(1)                                       # best phase per cell
            ranks[nm].append(int((s < s[tc]).sum()) + 1)
    return ranks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", choices=["equiv", "rank"], required=True)
    ap.add_argument("--rate", required=True)
    ap.add_argument("--snr", type=float, required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=9100)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--part", required=True)
    a = ap.parse_args()
    per = int(np.ceil(a.n / a.workers))
    jobs = [(a.rate, a.snr, per, a.seed + w) for w in range(a.workers)]
    fn = equiv_chunk if a.check == "equiv" else rank_chunk
    with mp.Pool(a.workers) as pool:
        res = pool.map(fn, jobs)
    if a.check == "equiv":
        dn = np.concatenate([np.array(x["dm_noint"]) for x in res])
        di = np.concatenate([np.array(x["dm_int"]) for x in res])
        R = dict(check="equiv", rate=a.rate, snr=a.snr, n=sum(x["n"] for x in res),
                 metric_diff_no_interleaver=dict(max_abs=float(np.abs(dn).max()), mean_abs=float(np.abs(dn).mean())),
                 metric_diff_interleaver=dict(max_abs=float(np.abs(di).max()), mean_abs=float(np.abs(di).mean()),
                                              median_abs=float(np.median(np.abs(di)))),
                 ok_standard_branch0=sum(x["ok_std"] for x in res),
                 ok_rotation_aware=[sum(x["ok_rot"][q] for x in res) for q in range(4)],
                 wrong_rotation_aware=[sum(x["wrong_rot"][q] for x in res) for q in range(4)])
    else:
        R = dict(check="rank", rate=a.rate, snr=a.snr, n=per * a.workers, cells=len(bf.grid(
            bf.grid_step(bc.PROFILE.get(a.rate, a.rate), a.snr))["f"]))
        for nm in ("total", "frozen", "no_spc"):
            rk = np.concatenate([x[nm] for x in res])
            R[nm] = dict(p_rank1=float((rk == 1).mean()), p_le4=float((rk <= 4).mean()),
                         p_le8=float((rk <= 8).mean()), p_le32=float((rk <= 32).mean()),
                         median=float(np.median(rk)), ranks=rk.tolist())
    out = bc.path("results", f"lit_{a.part}.json")
    json.dump(R, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ("total", "frozen", "no_spc")}, indent=1))
    for nm in ("total", "frozen", "no_spc"):
        if nm in R:
            print(nm, {k: v for k, v in R[nm].items() if k != "ranks"})
    print("LIT DONE", flush=True)


if __name__ == "__main__":
    main()
