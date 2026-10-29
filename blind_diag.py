"""
Why does v3 lose packets at the waterfall that the pre-MF genie decodes? For every v3 failure (wrong or no CRC pass),
re-decode with one piece of the truth substituted at a time:

    genie        pre-MF at the true CFO f, decode at (f, true phase)                  -> the code itself fails?
    premf_fs     v3's pre-MF (spectral fs), decode at (f, true phase)                 -> pre-MF centre error
    phase4       v3's pre-MF, decode at f, 4th-power phase (best of the 4 q pi/4 offsets by the metric)
    grid         v3's pre-MF, CFO = the grid cell nearest f, its 4th-power phase, best q -> grid quantisation
    grid_refine  as grid, then v3's refine offsets (+-k/2 STEP), best metric          -> refine
and the rank of the true cell in v3's posterior order, the robust z of the true cell, and whether v3 delivered a CRC
pass (false) or none.

    python blind_diag.py --rate 2/5 --snr 0.5 --frames 4000
"""
import argparse
import json

import numpy as np

import blind_cfo as bc
import blind_fast as bf


def main(a):
    code = bc.PiCode(bc.N_BITS, bc.CODES[a.rate], 16, 8)
    sigma2 = 1.0 / (2.0 * 10 ** (a.snr / 10))
    k = bf.grid_step(a.rate, a.snr)
    g = bf.grid(k)["f"]
    metric = bf.fast_sc(code.A).metric
    rng = np.random.default_rng(a.seed)
    rows, n = [], 0
    while n < a.frames:
        data, cw, r, rx, f, th = bc.frames(a.batch, code, a.snr, rng)
        st = dict(decodes=0, metric_evals=0)
        spec = {"sps": {"rate": a.rate}}
        dec, ok, ff, ftop = bf.sps3_receive(r, rx, a.snr, code, sigma2, st, spec)
        n += len(f)
        bad = np.where((dec != data).any(1))[0]
        if not len(bad):
            continue
        fs = bc.spectral(rx[bad])
        rv = bf.premf(r[bad], rx[bad], fs)                       # v3's pre-MF
        rg = bf.premf(r[bad], rx[bad], f[bad])                   # genie pre-MF

        def dec_ok(rr, fh, t):
            d, okk, _ = code.decode(bc.llrs(rr, fh, t, sigma2), return_info=True)
            return okk & ~(d != data[bad]).any(1)

        def best_q(rr, fh):
            t4 = bc.phase4(rr, fh)
            M = np.stack([metric(bc.llrs(rr, fh, t4 + q * np.pi / 4, sigma2)) for q in range(4)])
            return t4 + M.argmin(0) * np.pi / 4, M.min(0)

        res = {"genie": dec_ok(rg, f[bad], th[bad]), "premf_fs": dec_ok(rv, f[bad], th[bad])}
        t4, _ = best_q(rv, f[bad])
        res["phase4"] = dec_ok(rv, f[bad], t4)
        fc = g[np.abs(g[None] - f[bad][:, None]).argmin(1)]
        tc, _ = best_q(rv, fc)
        res["grid"] = dec_ok(rv, fc, tc)
        offs = np.arange(-(k // 2), k // 2 + 1) * bc.STEP
        cand = [best_q(rv, fc + o) + (fc + o,) for o in offs]
        j = np.argmin(np.stack([c[1] for c in cand]), 0)
        fr_ = np.array([cand[jj][2][i] for i, jj in enumerate(j)])
        tr_ = np.array([cand[jj][0][i] for i, jj in enumerate(j)])
        res["grid_refine"] = dec_ok(rv, fr_, tr_)
        fsc = bf.fast_sc(code.A)

        def ca(rr, fh, t, newton):
            _, cwh = fsc.metric_cw(bc.llrs(rr, fh, t, sigma2))
            return bf.code_aided(rr, fh, cwh, newton)
        f1, t1 = ca(rv, f[bad], t4, 0)
        res["ca_phase_truef"] = dec_ok(rv, f1, t1)
        f2, t2 = ca(rv, fc, tc, 2)
        res["ca_grid"] = dec_ok(rv, f2, t2)
        f3, t3 = ca(rv, f2, t2, 2)                                # a second code-aided pass
        res["ca_grid_x2"] = dec_ok(rv, f3, t3)
        f4, t4b = ca(rv, fr_, tr_, 2)
        res["ca_grid_refine"] = dec_ok(rv, f4, t4b)
        for i, b in enumerate(bad):
            rows.append({"snr": a.snr, "f": float(f[b]), "fs_err": float(fs[i] - f[b]), "v3_crc_pass": bool(ok[b]),
                         "v3_f_err": float(ff[b] - f[b]) if np.isfinite(ff[b]) else None,
                         **{kk: bool(v[i]) for kk, v in res.items()}})
        print(f"{n} frames, {len(rows)} v3 failures", flush=True)
    keys = ("genie", "premf_fs", "phase4", "grid", "grid_refine", "ca_phase_truef", "ca_grid", "ca_grid_x2",
            "ca_grid_refine")
    summ = {kk: int(sum(r_[kk] for r_ in rows)) for kk in keys}
    print(f"rate {a.rate} {a.snr} dB: {n} frames, v3 failures {len(rows)} "
          f"(false CRC pass {sum(r_['v3_crc_pass'] for r_ in rows)}); decodable with: {summ}", flush=True)
    json.dump({"rate": a.rate, "snr": a.snr, "frames": n, "rows": rows, "summary": summ},
              open(bc.path("results", f"diag_{a.rate.replace('/', '_')}_{a.snr}.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", default="2/5")
    ap.add_argument("--snr", type=float, default=0.5)
    ap.add_argument("--frames", type=int, default=4000)
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--seed", type=int, default=31)
    main(ap.parse_args())
