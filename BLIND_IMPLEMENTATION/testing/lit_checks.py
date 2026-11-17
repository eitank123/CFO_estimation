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

eqrb (2026-11-15, expected_eqrb.md; BLIND_NOINT=1 BLIND_ROTBITS=1): the rotation-bit code (bc.RBCode / bc.PiCodeRB): metric
at theta + q pi/2 vs theta, the rotation read from the decoded (u_{N-2}, u_{N-1}) per q, CRC passes at a wrong rotation.

    BLIND_STUDY=small_cfo BLIND_NOINT=1 BLIND_ROTBITS=1 python BLIND_IMPLEMENTATION/testing/lit_checks.py --check eqrb --rate 0.15 --snr -3 --n 4000 --part t-eqrb-chk15

lmarg (2026-11-15, expected_f3f5.md F3; Yuan, Coskun, Kramer 2021): the rank harness with the list-marginalised SC
metric -log sum_l exp(-PM_l) over the L_e surviving paths of a Fast-SSC list decode (FastSCL, no CRC), L_e = 1, 2, 4, 8,
at full length and at the last checkpoint c = 3/4; L_e = 1 is checked against today's metric (bf.FastSC).

    BLIND_STUDY=small_cfo python BLIND_IMPLEMENTATION/testing/lit_checks.py --check lmarg --rate 0.15 --snr -4 --n 2000 --part t-lm15a

Writes small_cfo/blind/results/lit_<part>.json (BLIND_STUDY=small_cfo).
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

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


def eqrb_chunk(args):
    """(eqrb, BLIND_NOINT=1 BLIND_ROTBITS=1) packets of the rotation-bit code at the true CFO: (a) the list-1 metric at
    theta + q pi/2 vs theta, (b) bc.PiCodeRB's rotation read from (u_{N-2}, u_{N-1}) at theta + q pi/2 (the symbols
    de-rotated by -q pi/2: the decoded codeword is rot^{-q}(cw), expected read (-q) mod 4), (c) CRC passes at a wrong
    rotation read (0 by construction) and wrong data."""
    rate, snr, n, seed = args
    assert bc.NOINT and bc.ROTBITS, "eqrb needs BLIND_NOINT=1 BLIND_ROTBITS=1"
    rng = np.random.default_rng(seed)
    A = bc.CODES[rate]
    tx = bc.RBCode(bc.N_BITS, A, 16, 8)
    code = bc.PiCodeRB(bc.N_BITS, A, 16, 8)
    fs_ = bf.fast_sc(A)
    assert np.array_equal(fs_.frozen, code.frozen)           # the metric decodes the same K + 2 positions
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    data, cw, r, rx, f, th = bc.frames(n, tx, snr, rng)
    assert not polar_transform(cw)[:, -2:].any()             # u_{N-2} = u_{N-1} = 0 sent
    M = np.stack([fs_.metric(bc.llrs(r, f, th + q * np.pi / 2, sigma2)) for q in range(4)], 1)
    out = dict(n=n, dm=(M[:, 1:] - M[:, :1]).tolist(), read_best=[0] * 4, read_chosen=[0] * 4, ok=[0] * 4,
               ok_right=[0] * 4, ok_wrong=[0] * 4, ok_wrong_rot=[0] * 4, paths_pass=[0] * 4, paths_pass_wrong_rot=[0] * 4)
    ar = np.arange(n)
    for q in range(4):
        qe = (-q) % 4
        d, ok, _ = code.decode(bc.llrs(r, f, th + q * np.pi / 2, sigma2), return_info=True)
        lq, (_, okl, pm) = code.last_q, code.last_list
        okl = okl & np.isfinite(pm)
        right = (d == data).all(1)
        out["read_best"][q] = int((lq[ar, pm.argmin(1)] == qe).sum())             # the best-PM path's rotation read
        out["read_chosen"][q] = int((ok & (code.last_rot == qe)).sum())          # the delivered path (CRC pass)
        out["ok"][q] = int(ok.sum())
        out["ok_right"][q] = int((ok & right).sum())
        out["ok_wrong"][q] = int((ok & ~right).sum())
        out["ok_wrong_rot"][q] = int((ok & (code.last_rot != qe)).sum())          # packets: delivered at a wrong read
        out["paths_pass"][q] = int(okl.sum())
        out["paths_pass_wrong_rot"][q] = int((okl & (lq != qe)).sum())            # list paths: CRC pass, wrong read
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


LM_LIST = (1, 2, 4, 8)          # lmarg: list sizes L_e
LM_CK = 0.75                    # lmarg: the last checkpoint (codeword fraction), as small_rx's ck schedule
LM_SPLIT = 64                   # rate-0 nodes in 64-bit chunks for the checkpoint (small_rx.SPLIT)


# FastSCL, lse_metric, leaf_ends: moved to fastscl.py at the project root (2026-11-15; small_rx lmarg uses them too)
from fastscl import FastSCL, leaf_ends, lse_metric  # noqa: E402,F401


def lmarg_chunk(args):
    """(lmarg, lit_polar_sync.md F3) rank of the true cell under the list-marginalised SC metric
    -log sum_l exp(-PM_l), L_e in LM_LIST, at full length and at c = LM_CK; the packets, grid and phases of rank_chunk.
    L_e = 1 is checked against bf.FastSC (exact full metric; checkpoint vs the 64-bit-chunked metric_nodes), and
    ranks_ref = rank_chunk's "total" rank on the same packet (pairing with the old rank runs: same seed, n, workers).
    Per-packet progress "<done> <total>" in logs/lit_<part>.c<chunk>.progress (overwritten)."""
    rate, snr, n, seed, chunk, part = args
    rng = np.random.default_rng(seed)
    A = bc.CODES[rate]
    code = bc.PiCode(bc.N_BITS, A, 16, 8)
    fs_ = bf.fast_sc(A)
    fsn = bf.FastSC(fs_.frozen)                                       # the same metric, rate-0 nodes in chunks
    fsn.split = LM_SPLIT
    cut = int(LM_CK * bc.N_BITS)
    nl = max(1, int((np.array(leaf_ends(fsn.plan, 0, bc.N_BITS, [], LM_SPLIT)) <= cut).sum()))
    dec = {L: FastSCL(fs_, L) for L in LM_LIST}
    sigma2 = 1.0 / (2.0 * 10 ** (snr / 10))
    k = bf.grid_step(bc.PROFILE.get(rate, rate), snr)
    g = bf.grid(k)["f"]
    nq = 4
    data, cw, r, rx, f, th = bc.frames(n, code, snr, rng)
    out = {f"{ln}_L{L}": dict(rank=[], gap=[]) for ln in ("full", "ck") for L in LM_LIST}
    out.update(chunk=chunk, seed=seed, ranks_ref=[])
    chk = dict(full_vs_metric=0.0, full_vs_nodes=0.0, ck_vs_nodes=0.0, rel_full=0.0, rel_ck=0.0, rows=0,
               viol_full=0, viol_ck=0)                                # viol: rows with |a - b| > 1e-4 |b| + 1e-3
    prog = bc.path("logs", f"lit_{part}.c{chunk}.progress")
    for i in range(n):
        th_c = bc.phase4(np.repeat(r[i:i + 1], 1, 0), g[None])[0]           # 4th-power phase per cell
        F = np.repeat(g, nq)
        TH = (th_c[:, None] + np.arange(nq)[None] * np.pi / 4).ravel()
        llr = bc.llrs(np.repeat(r[i:i + 1], len(F), 0), F, TH, sigma2)
        tc = int(np.abs(g - f[i]).argmin())
        for L in LM_LIST:
            pm, pmc = dec[L].decode(llr, cut)
            for ln, P in (("full", pm), ("ck", pmc)):
                s = lse_metric(P).reshape(len(g), nq).min(1)                  # best phase per cell
                out[f"{ln}_L{L}"]["rank"].append(int((s < s[tc]).sum()) + 1)
                out[f"{ln}_L{L}"]["gap"].append(float(np.delete(s, tc).min() - s[tc]))
            if L == 1:                                                         # L_e = 1 == today's metric
                s = fs_.metric_nodes(llr).reshape(len(g), nq, -1).sum(-1).min(1)   # rank_chunk's "total"
                out["ranks_ref"].append(int((s < s[tc]).sum()) + 1)
                Pn = fsn.metric_nodes(llr).astype(np.float64)
                tot, ck = Pn.sum(-1), Pn[:, :nl].sum(-1)
                dd = [np.abs(pm[:, 0] - tot), np.abs(pmc[:, 0] - ck)]
                if i == 0:                                                     # bf.FastSC.metric: same sums
                    chk["full_vs_metric"] = float(np.abs(pm[:, 0] - fs_.metric(llr)).max() / np.abs(tot).max())
                                                                               # (logged; soft check after the loop)
                chk["full_vs_nodes"] = max(chk["full_vs_nodes"], float(dd[0].max()))
                chk["ck_vs_nodes"] = max(chk["ck_vs_nodes"], float(dd[1].max()))
                chk["rel_full"] = max(chk["rel_full"], float(dd[0].max() / np.abs(tot).max()))
                chk["rel_ck"] = max(chk["rel_ck"], float(dd[1].max() / np.abs(ck).max()))
                chk["rows"] += len(tot)
                chk["viol_full"] += int((dd[0] > 1e-4 * np.abs(tot) + 1e-3).sum())
                chk["viol_ck"] += int((dd[1] > 1e-4 * np.abs(ck) + 1e-3).sum())
        with open(prog, "w") as fh:                                            # per-packet progress of this chunk
            fh.write(f"{i + 1} {n}\n")
    assert chk["viol_full"] <= 0.01 * chk["rows"], chk                         # soft check: FastSCL(1) != FastSC on
    out["l1_check"] = chk                                                      # > 1 % of the rows (full length)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", choices=["equiv", "rank", "eqrb", "lmarg"], required=True)
    ap.add_argument("--rate", required=True)
    ap.add_argument("--snr", type=float, required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=9100)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--part", required=True)
    a = ap.parse_args()
    per = int(np.ceil(a.n / a.workers))
    jobs = [(a.rate, a.snr, per, a.seed + w) + ((w, a.part) if a.check == "lmarg" else ()) for w in range(a.workers)]
    fn = {"equiv": equiv_chunk, "rank": rank_chunk, "eqrb": eqrb_chunk, "lmarg": lmarg_chunk}[a.check]
    t0, res, err = time.time(), [], []
    with mp.Pool(a.workers) as pool:                          # (ordered, as pool.map) + a progress file "i n seconds"
        it = pool.imap(fn, jobs)                             # as blind_ber's (job_progress.py "count")
        for i in range(1, len(jobs) + 1):
            try:
                res.append(it.next())
            except Exception as e:                           # a failed chunk: keep the others, re-raise after the JSON
                err.append((i - 1, repr(e)))
                print("CHUNK FAILED", i - 1, repr(e), flush=True)
            with open(bc.path("logs", f"lit_{a.part}.progress"), "a") as fh:
                fh.write(f"{i} {len(jobs)} {time.time() - t0:.0f}\n")
    if not res:
        raise RuntimeError(f"all chunks failed: {err}")
    if a.check == "eqrb":
        dm = np.abs(np.concatenate([np.array(x["dm"]) for x in res]))
        n = sum(x["n"] for x in res)
        R = dict(check="eqrb", rate=a.rate, snr=a.snr, n=n,
                 metric_diff_q123=dict(max_abs=dm.max(0).tolist(), mean_abs=dm.mean(0).tolist()),
                 **{k: [sum(x[k][q] for x in res) for q in range(4)] for k in (
                     "read_best", "read_chosen", "ok", "ok_right", "ok_wrong", "ok_wrong_rot", "paths_pass",
                     "paths_pass_wrong_rot")})
        R["read_best_acc"] = [v / n for v in R["read_best"]]
        R["read_chosen_acc"] = [v / max(o, 1) for v, o in zip(R["read_chosen"], R["ok"])]
    elif a.check == "equiv":
        dn = np.concatenate([np.array(x["dm_noint"]) for x in res])
        di = np.concatenate([np.array(x["dm_int"]) for x in res])
        R = dict(check="equiv", rate=a.rate, snr=a.snr, n=sum(x["n"] for x in res),
                 metric_diff_no_interleaver=dict(max_abs=float(np.abs(dn).max()), mean_abs=float(np.abs(dn).mean())),
                 metric_diff_interleaver=dict(max_abs=float(np.abs(di).max()), mean_abs=float(np.abs(di).mean()),
                                              median_abs=float(np.median(np.abs(di)))),
                 ok_standard_branch0=sum(x["ok_std"] for x in res),
                 ok_rotation_aware=[sum(x["ok_rot"][q] for x in res) for q in range(4)],
                 wrong_rotation_aware=[sum(x["wrong_rot"][q] for x in res) for q in range(4)])
    elif a.check == "lmarg":
        sm = ("rows", "viol_full", "viol_ck")                  # summed over the chunks, the rest: max
        R = dict(check="lmarg", rate=a.rate, snr=a.snr, n=per * len(res), cells=len(bf.grid(
            bf.grid_step(bc.PROFILE.get(a.rate, a.rate), a.snr))["f"]), phases=4, L_e=list(LM_LIST), ck=LM_CK,
            chunks=[x["chunk"] for x in res], seeds=[x["seed"] for x in res],    # packet order: chunk by chunk
            l1_check={k: (sum if k in sm else max)(x["l1_check"][k] for x in res) for k in res[0]["l1_check"]},
            ranks_ref=sum((x["ranks_ref"] for x in res), []))
        for ln in ("full", "ck"):
            for L in LM_LIST:
                nm = f"{ln}_L{L}"
                rk = np.concatenate([x[nm]["rank"] for x in res])
                gp = np.concatenate([x[nm]["gap"] for x in res])          # best wrong cell - true cell (> 0: right)
                R[nm] = dict(p_rank1=float((rk == 1).mean()), p_le4=float((rk <= 4).mean()),
                             p_le8=float((rk <= 8).mean()), p_le32=float((rk <= 32).mean()),
                             median=float(np.median(rk)), gap_mean=float(gp.mean()),
                             gap_p10=float(np.percentile(gp, 10)), ranks=rk.tolist(), gaps=gp.tolist())
    else:
        R = dict(check="rank", rate=a.rate, snr=a.snr, n=per * a.workers, cells=len(bf.grid(
            bf.grid_step(bc.PROFILE.get(a.rate, a.rate), a.snr))["f"]))
        for nm in ("total", "frozen", "no_spc"):
            rk = np.concatenate([x[nm] for x in res])
            R[nm] = dict(p_rank1=float((rk == 1).mean()), p_le4=float((rk <= 4).mean()),
                         p_le8=float((rk <= 8).mean()), p_le32=float((rk <= 32).mean()),
                         median=float(np.median(rk)), ranks=rk.tolist())
    if err:
        R["failed_chunks"] = err
    out = bc.path("results", f"lit_{a.part}.json")
    json.dump(R, open(out, "w"), indent=1)
    big = [k for k, v in R.items() if isinstance(v, dict) and "ranks" in v]
    print(json.dumps({k: v for k, v in R.items() if k not in big}, indent=1))
    for nm in big:
        print(nm, {k: v for k, v in R[nm].items() if k not in ("ranks", "gaps")})
    if err:
        raise RuntimeError(f"failed chunks (JSON of the others written): {err}")
    print("LIT DONE", flush=True)


if __name__ == "__main__":
    main()
